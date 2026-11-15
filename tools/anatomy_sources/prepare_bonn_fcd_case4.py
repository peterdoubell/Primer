"""Preserve native stored samples in independently decodable gzip plane packs."""
from pathlib import Path
import gzip
import hashlib
import json
import nibabel as nib
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / '.research/fcd-source-20261028'
OUT = SOURCE / 'native-package'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    receipt = (SOURCE / 'sub-00004-acquisition.json').read_bytes()
    assert digest(receipt) == 'b8d9916742bc35986cab9776760ede2d909a513e9f9d2b42f5d59e188fe5578e'
    OUT.mkdir(exist_ok=True)
    volumes = {}
    for entry in json.loads(receipt)['files']:
        path = SOURCE / entry['file']
        assert digest(path.read_bytes()) == entry['sha256']
        if not path.name.endswith('.nii.gz'):
            continue
        role = 'roi' if '_roi' in path.name else 'flair' if 'FLAIR' in path.name else 't1'
        image = nib.load(path)
        raw = np.asarray(image.dataobj.get_unscaled())
        dtype = raw.dtype.newbyteorder('<')
        planes = {}
        for axis in range(3):
            filename = f'{role}-axis-{axis}.pack'
            rows = []
            with (OUT / filename).open('wb') as stream:
                for index in range(raw.shape[axis]):
                    plane = np.ascontiguousarray(np.take(raw, index, axis=axis), dtype=dtype)
                    decoded = plane.tobytes()
                    encoded = gzip.compress(decoded, mtime=0)
                    rows.append(dict(index=index, offset=stream.tell(), gzipBytes=len(encoded),
                                     decodedBytes=len(decoded), shape=list(plane.shape),
                                     decodedSHA256=digest(decoded), gzipSHA256=digest(encoded)))
                    stream.write(encoded)
            pack = (OUT / filename).read_bytes()
            planes[str(axis)] = dict(file=filename, bytes=len(pack), sha256=digest(pack), planes=rows)
        volumes[role] = dict(sourceFile=entry['file'], sourceSHA256=entry['sha256'],
                             shape=list(raw.shape), dtype=dtype.str, affine=image.affine.tolist(),
                             slope=float(image.dataobj.slope), intercept=float(image.dataobj.inter),
                             axisCodes=list(nib.aff2axcodes(image.affine)), planes=planes)
    assert set(volumes) == {'roi', 'flair', 't1'}
    manifest = dict(source='OpenNeuro ds004199 v1.0.6 sub-00004', volumes=volumes,
                    sourceReceiptSHA256=digest(receipt), resampling=False,
                    roiReference='flair', t1RegistrationVerified=False,
                    clinicalApproval=False, independentPlaneVerificationPending=True)
    (OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps({'volumes': list(volumes), 'planes': sum(len(p['planes']) for v in volumes.values() for p in v['planes'].values())}))


if __name__ == '__main__':
    main()
