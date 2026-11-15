"""Independent native SPL canvas oracles from exactly reconstructed original NRRDs."""
from pathlib import Path
import argparse, gzip, hashlib, json
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'web/anatomy/spl-nac-limbic'
OUTPUT = ROOT / 'docs/spl-limbic-source-review-20261016/viewer'
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--write-proof', action='store_true')
args = parser.parse_args()
if not __debug__: raise RuntimeError('Assertions must remain enabled.')
sha = lambda b: hashlib.sha256(b).hexdigest()
manifest = json.loads((ASSETS / 'manifest.json').read_text())
sources = {}


def original(row):
    # The archived header includes its original blank terminator; compressed
    # transport body is unchanged. Verify full NRRD identity before parsing.
    header = (ASSETS / row['sourceHeaderFile']).read_bytes()
    body = (ASSETS / row['file']).read_bytes()
    nrrd = header + body
    assert sha(nrrd) == row['source']['sha256']
    assert hashlib.sha1(b'blob ' + str(len(nrrd)).encode() + b'\0' + nrrd).hexdigest() == row['source']['gitBlobSHA1']
    fields = dict(line.split(':', 1) for line in header.decode().splitlines() if ':' in line and not line.startswith('#'))
    assert fields['space'].strip() == 'left-posterior-superior'
    assert fields['encoding'].strip() == 'gzip' and fields['endian'].strip() == 'little'
    shape = tuple(map(int, fields['sizes'].split()))
    dtype = {'float': '<f4', 'short': '<i2'}[fields['type'].strip()]
    decoded = gzip.decompress(body)
    assert sha(decoded) == row['decodedSHA256']
    sources[row['name']] = {'originalNRRDSHA256': sha(nrrd), 'decodedSHA256': sha(decoded), 'dtype': dtype, 'shape': shape, 'header': fields}
    return np.frombuffer(decoded, dtype=dtype).reshape(shape, order='F')


labels = original(manifest['labelVolume'])
assert labels.shape == (256, 256, 256) and labels.dtype == np.dtype('<i2')
assert sources['labels']['header']['space directions'].strip() == '(0,1,0) (0,0,-1) (1,0,0)'
assert sources['labels']['header']['space origin'].strip() == '(-128,-128,128)'
focus = {}
assert labels[167, 132, 130] == 3007  # Original isolated source voxel at RAS(-2,-39,-4), not a biological claim.
for label in manifest['labels']:
    ids = np.flatnonzero(labels.ravel(order='F') == label['code'])
    points = np.column_stack((ids % 256, ids // 256 % 256, ids // 65536))
    assert len(ids) == label['voxelCount']
    center = points.mean(axis=0)
    p = points[np.argmin(np.sum((points - center) ** 2, axis=1))]
    ras = np.array([128 - p[2], 128 - p[0], 128 - p[1]])
    native = np.floor(np.array([(107.625-ras[1])/.75, (119.625-ras[2])/.75, (77.625-ras[0])/.75]) + .5).astype(int)
    focus[label['code']] = {'labelVoxel': p.tolist(), 'ras': ras.tolist(), 'nativeVoxel': native.tolist(), 'count': len(ids)}
fixtures = []
for contrast in ['T1', 'T2']:
    row = manifest['volumes'][contrast]
    volume = original(row)
    assert volume.shape == (288, 320, 208) and volume.dtype == np.dtype('<f4')
    assert sources[contrast]['header']['space directions'].strip() == '(0,0.75,0) (0,0,-0.75) (0.75,0,0)'
    assert sources[contrast]['header']['space origin'].strip() == '(-77.625,-107.625,119.625)'
    default_width = row['defaultWindow'][1] - row['defaultWindow'][0]
    default_center = sum(row['defaultWindow']) / 2
    for plane, fixed, height, width in [('axial', 1, 288, 208), ('coronal', 0, 320, 208), ('sagittal', 2, 320, 288)]:
        configurations = [{'name': 'focus', 'label': label['code'], 'slice': focus[label['code']]['nativeVoxel'][fixed], 'overlay': 'selected'} for label in manifest['labels']]
        configurations.append({'name': 'fornix-source-outlier', 'label': 3007, 'slice': [196,165,106][fixed], 'overlay': 'selected'})
        for s in [0, volume.shape[fixed] // 2, volume.shape[fixed]-1]:
            configurations.append({'name': 'edge-or-middle', 'slice': s, 'overlay': 'all', 'label': 17})
        for name, center, window in [('zero-centered', 0, 1), ('all-black', 1e6, 1), ('all-white', -1e6, 1), ('MRI-only', default_center, default_width)]:
            configurations.append({'name': name, 'slice': focus[17]['nativeVoxel'][fixed], 'overlay': 'off', 'label': 17, 'center': center, 'width': window})
        native = [height//2, focus[17]['nativeVoxel'][fixed], width//2] if plane == 'axial' else [focus[17]['nativeVoxel'][fixed],height//2,width//2] if plane == 'coronal' else [width//2,height//2,focus[17]['nativeVoxel'][fixed]]
        anchor = float(volume[tuple(native)])
        for name, center in [('window-low-exact', anchor+.5), ('window-high-exact', anchor-.5)]:
            configurations.append({'name': name, 'slice': focus[17]['nativeVoxel'][fixed], 'overlay': 'off', 'label': 17, 'center': center, 'width': 1})
        for config in configurations:
            s = config['slice']; xx, yy = np.meshgrid(np.arange(width), np.arange(height))
            # Direct original-axis permutations, independently of coordinates.js.
            if plane == 'axial': ii, jj, kk = yy, np.full_like(xx, s), xx
            elif plane == 'coronal': ii, jj, kk = np.full_like(xx, s), yy, xx
            else: ii, jj, kk = xx, yy, np.full_like(xx, s)
            scalar = volume[ii, jj, kk].astype(np.float64)
            li = np.floor(20.375 + .75 * ii + .5).astype(int)
            lj = np.floor(8.375 + .75 * jj + .5).astype(int)
            lk = np.floor(50.375 + .75 * kk + .5).astype(int)
            categorical = labels[li, lj, lk]
            center = config.get('center', default_center); window = config.get('width', default_width)
            grey = np.clip(np.floor(255 * (scalar - (center-window/2)) / window), 0, 255)
            rgba = np.empty((height, width, 4), dtype=np.uint8)
            rgba[:, :, :3] = grey[:, :, None]; rgba[:, :, 3] = 255
            for label in manifest['labels']:
                if config['overlay'] == 'off' or config['overlay'] == 'selected' and label['code'] != config['label']: continue
                mask = categorical == label['code']
                rgba[mask, :3] = np.floor(.55 * grey[mask, None] + .45 * np.asarray(label['color']) + .5).astype(np.uint8)
            probes = []
            locations = [(0, 0), (width-1, height-1), (width//2, height//2), (width//3, height//3)]
            if config['name'] == 'fornix-source-outlier': locations.append({'axial':(106,196),'coronal':(106,165),'sagittal':(196,165)}[plane])
            for x, y in locations:
                i, j, k = int(ii[y,x]), int(jj[y,x]), int(kk[y,x])
                probes.append({'pixel': [x,y], 'voxel': [i,j,k], 'value': float(scalar[y,x]), 'ras': [77.625-.75*k,107.625-.75*i,119.625-.75*j], 'labelVoxel': [int(li[y,x]),int(lj[y,x]),int(lk[y,x])], 'label': int(categorical[y,x])})
            fixtures.append({**config, 'contrast': contrast, 'plane': plane, 'center': center, 'width': window, 'pixelWidth': width, 'pixelHeight': height, 'spacing': [.75,.75], 'rgbaSHA256': sha(rgba.tobytes()), 'scalarSHA256': sha(scalar.astype('<f4').tobytes()), 'labelSHA256': sha(categorical.astype('<i2').tobytes()), 'probes': probes})
oracle = {'manifestSHA256': sha((ASSETS/'manifest.json').read_bytes()), 'sourceIdentity': sources, 'focus': focus, 'fixtures': fixtures, 'method': 'Exact original NRRD reconstruction and original-axis permutations; direct LPS-to-RAS coordinates and original-grid nearest-label equations in NumPy. No product coordinate functions imported.', 'clinicalApproval': False}
encoded = json.dumps(oracle, indent=2) + '\n'
if args.write_proof:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT/'pixel-oracles.json').write_text(encoded)
else:
    assert (OUTPUT/'pixel-oracles.json').read_text() == encoded, 'Committed source-derived oracle differs; inspect before regeneration.'
print(json.dumps({'allPassed': True, 'fixtures': len(fixtures), 'pixels': sum(f['pixelWidth']*f['pixelHeight'] for f in fixtures), 'manifestSHA256': oracle['manifestSHA256'], 'oracleSHA256': sha(encoded.encode())}))
