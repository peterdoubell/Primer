"""Independently verify every linked contact anchor in unchanged source arrays."""
from pathlib import Path
import gzip
import hashlib
import json
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'web/anatomy/spl-nac-limbic'
ASSETS = ROOT / 'web/anatomy/spl-source-contacts'
OUT = ROOT / 'docs/cortical-native-mri-review-20261101'
sha = lambda raw: hashlib.sha256(raw).hexdigest()

def main():
    manifest = json.loads((SOURCE / 'manifest.json').read_bytes())
    config = json.loads((ASSETS / 'mri-source.json').read_bytes())
    contact = json.loads((ASSETS / 'manifest.json').read_bytes())
    assert config['volumes'] == manifest['volumes'] and config['labelVolume'] == manifest['labelVolume']
    identities = {}
    def array(row):
        packed = (SOURCE / row['file']).read_bytes()
        assert sha(packed) == row['gzipSHA256']
        raw = gzip.decompress(packed)
        assert len(raw) == row['byteLength'] and sha(raw) == row['decodedSHA256']
        identities['web/anatomy/spl-nac-limbic/' + row['file']] = sha(packed)
        return np.frombuffer(raw, dtype=row['dtype']).reshape(row['shape'], order='F')
    labels = array(manifest['labelVolume'])
    scans = {name: array(row) for name, row in manifest['volumes'].items()}
    label_affine = np.asarray(manifest['labelVolume']['voxelToRAS'])
    assert len(config['pairs']) == len(contact['groups']) == 77
    checks = []
    for pair, group in zip(config['pairs'], contact['groups']):
        assert (pair['whiteCode'], pair['corticalCode']) == (group['whiteCode'], group['corticalCode'])
        white = np.asarray(pair['anchors']['white']['sourceLabelIJK'])
        cortical = np.asarray(pair['anchors']['cortical']['sourceLabelIJK'])
        axis, sign = pair['sourceFaceAxis'], pair['sourceFaceSign']
        assert axis in [0, 1, 2] and sign in [-1, 1]
        step = np.zeros(3, int); step[axis] = sign
        assert np.array_equal(cortical - white, step)
        for side, voxel, expected in [('white', white, pair['whiteCode']), ('cortical', cortical, pair['corticalCode'])]:
            assert np.issubdtype(voxel.dtype, np.integer) and np.all((voxel >= 0) & (voxel < labels.shape))
            anchor = pair['anchors'][side]
            assert int(labels[tuple(voxel)]) == anchor['sourceLabelCode'] == expected
            world = label_affine @ np.array([*voxel, 1])
            for name, scan in scans.items():
                row = manifest['volumes'][name]; affine = np.asarray(row['voxelToRAS'])
                point = np.floor((np.linalg.inv(affine) @ world)[:3] + .5).astype(int)
                assert np.all((point >= 0) & (point < scan.shape))
                sample_world = affine @ np.array([*point, 1])
                label_point = np.floor((np.linalg.inv(label_affine) @ sample_world)[:3] + .5).astype(int)
                assert np.all((label_point >= 0) & (label_point < labels.shape))
                native = anchor['nativeMRI'][name]
                assert native['sourceIJK'] == point.tolist()
                assert native['sourceRASmm'] == sample_world[:3].tolist()
                assert native['sourceSample'] == float(scan[tuple(point)])
                assert native['nearestSourceLabelCode'] == int(labels[tuple(label_point)]) == expected
                checks.append({'pair': str(pair['whiteCode']) + ':' + str(pair['corticalCode']), 'side': side,
                               'contrast': name, 'nativeMRIIndex': point.tolist(), 'sourceLabelCode': expected})
    for file in ['web/anatomy/spl-nac-limbic/manifest.json', 'web/anatomy/spl-source-contacts/manifest.json',
                 'web/anatomy/spl-source-contacts/mri-source.json', 'tools/check_cortical_mri_anchors.py']:
        identities[file] = sha((ROOT / file).read_bytes())
    proof = {'allPassed': True, 'sourcePairs': 77, 'sourceAdjacencies': 77, 'originalMRISamplesVerified': len(checks),
             'allSamplesAndLabelsExact': True, 'sourceResampled': False, 'clinicalApproval': False,
             'anatomicalVisibilityVerified': False, 'checks': checks, 'sourceSHA256': identities}
    OUT.mkdir(exist_ok=True); (OUT / 'anchor-proof.json').write_text(json.dumps(proof, indent=2) + '\n')
    print(json.dumps({k: proof[k] for k in ['allPassed', 'sourcePairs', 'sourceAdjacencies', 'originalMRISamplesVerified']}))

if __name__ == '__main__':
    main()
