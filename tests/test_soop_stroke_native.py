"""SOOP originals, native storage/scaling, complete boundaries and source scope."""
from pathlib import Path
import gzip
import hashlib
import json
import struct
import subprocess
import pytest

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'web/anatomy/soop-stroke-sub342'
REVIEW = ROOT / 'docs/soop-stroke-native-source-review-20261011'
PIN = 'a9913b4a7b56152ea53e79afaeb5baacb47c1d8eeee954832b1159792d943767'


def sha(b):
    return hashlib.sha256(b).hexdigest()


def manifest():
    return json.loads((OUT / 'manifest.json').read_text())


def test_originals_match_pinned_public_repository_and_annex_content_identifiers():
    receipt_bytes = (REVIEW / 'source/sub-342-acquisition.json').read_bytes()
    assert sha(receipt_bytes) == PIN
    receipt = json.loads(receipt_bytes)
    assert receipt['pinned_root_tree'] == 'a62344db73f18f384a95b452f4a1a423087e059b'
    assert len(receipt['files']) == 11 and receipt['total_bytes'] == 52676049
    assert json.loads((REVIEW / 'source/dataset_description.json').read_text())['License'] == 'CC0'
    for row in receipt['files']:
        name = Path(row['path']).name
        raw = (OUT / name).read_bytes()
        assert len(raw) == row['bytes'] and sha(raw) == row['sha256']
        if row['git_blob_mode'] == '120000':
            pointer = (REVIEW / 'source' / (name + '.annex-pointer')).read_bytes()
            assert sha(pointer) == row['annex_pointer_sha256']
            assert f'SHA256E-s{len(raw)}--{sha(raw)}'.encode() in pointer
            blob = pointer
        else:
            blob = raw
        assert hashlib.sha1(f'blob {len(blob)}\0'.encode() + blob).hexdigest() == row['git_blob']


def test_every_original_storage_value_scaling_and_complete_dimension_is_retained():
    nib = pytest.importorskip('nibabel')
    np = pytest.importorskip('numpy')
    m = manifest()
    total = 0
    for role, row in m['arrays'].items():
        source = nib.load(OUT / Path(row['source_file']).name)
        stored = source.dataobj.get_unscaled()
        compressed = (OUT / Path(row['file']).name).read_bytes()
        raw = gzip.decompress(compressed)
        assert len(compressed) == row['bytes'] and sha(compressed) == row['sha256']
        assert len(raw) == row['decoded_bytes'] and sha(raw) == row['decoded_sha256']
        assert raw == stored.astype(row['dtype']).tobytes(order='F')
        assert stored.dtype == np.dtype(row['dtype'])
        assert list(stored.shape) == row['shape']
        assert row['spatial_shape'] == row['shape'][:3]
        assert np.array_equal(source.affine, row['affine'])
        assert source.dataobj.slope == row['slope'] and source.dataobj.inter == row['intercept']
        q, qcode = source.header.get_qform(coded=True)
        s, scode = source.header.get_sform(coded=True)
        assert int(qcode) == row['qform_code'] and int(scode) == row['sform_code']
        assert (q is None and row['qform'] is None) or np.array_equal(q, row['qform'])
        assert (s is None and row['sform'] is None) or np.array_equal(s, row['sform'])
        total += stored.size
    assert total == 160204800
    assert m['arrays']['trace']['shape'] == m['arrays']['adc']['shape'] == [288, 288, 26, 1]
    assert m['arrays']['trace']['all_dimension_spacing'][3] == 0
    assert m['arrays']['adc']['slope'] == 0.5792486667633057
    assert m['arrays']['adc']['intercept'] == 18980.8203125
    assert m['arrays']['t1']['shape'] == [370, 512, 512]
    assert m['arrays']['flair']['shape'] == [200, 512, 512]


@pytest.mark.parametrize('role', ['acute', 'chronic', 'combined'])
def test_each_mask_mesh_is_exactly_its_original_exposed_cells_with_no_component_removed(role):
    nib = pytest.importorskip('nibabel')
    np = pytest.importorskip('numpy')
    ndimage = pytest.importorskip('scipy.ndimage')
    m = manifest()
    row = m['meshes'][role]
    a = nib.load(OUT / Path(m['arrays'][role]['source_file']).name)
    mask = a.dataobj.get_unscaled() == 1
    compressed = (OUT / Path(row['file']).name).read_bytes()
    raw = gzip.decompress(compressed)
    assert sha(compressed) == row['sha256'] and sha(raw) == row['decoded_sha256']
    assert raw[:4] == b'SPV1'
    n, t = struct.unpack_from('<II', raw, 4)
    positions = np.frombuffer(raw, '<f8', n * 3, 12).reshape(-1, 3)
    triangles = np.frombuffer(raw, '<u4', t * 3, 12 + n * 24).reshape(-1, 3)
    assert (n, t) == (row['vertices'], row['triangles'])
    assert len(raw) == 12 + n * 24 + t * 12
    assert sha(positions.tobytes()) == row['world_positions_sha256']
    assert sha(triangles.tobytes()) == row['triangle_indices_sha256']
    assert np.isfinite(positions).all() and triangles.max() < n
    inverse = np.linalg.inv(a.affine)
    vox = np.column_stack([inverse[r, 3] + sum(inverse[r, c] * positions[:, c] for c in range(3)) for r in range(3)])
    assert np.max(np.abs(vox * 2 - np.rint(vox * 2))) < 1e-9
    vox = np.rint(vox * 2) / 2

    def selected(p):
        return all(0 <= p[i] < mask.shape[i] for i in range(3)) and bool(mask[tuple(p)])

    observed = set()
    for k in range(0, t, 2):
        indices = list(dict.fromkeys([*map(int, triangles[k]), *map(int, triangles[k + 1])]))
        assert len(indices) == 4
        corners = vox[indices]
        constant = np.flatnonzero(np.ptp(corners, axis=0) == 0)
        assert len(constant) == 1
        axis = int(constant[0])
        mid = corners.mean(axis=0)
        lo = np.rint(mid).astype(int)
        lo[axis] = int(mid[axis] - .5)
        hi = lo.copy()
        hi[axis] += 1
        assert selected(lo) != selected(hi)
        cell = lo if selected(lo) else hi
        sign = 1 if selected(lo) else -1
        for j in range(3):
            if j != axis:
                assert np.ptp(corners[:, j]) == 1
        item = (*map(int, cell), axis, sign)
        assert item not in observed
        observed.add(item)
    expected = set()
    for p in np.argwhere(mask):
        for axis in range(3):
            for sign in (-1, 1):
                neighbor = p.copy()
                neighbor[axis] += sign
                if not selected(neighbor):
                    expected.add((*map(int, p), axis, sign))
    assert observed == expected
    assert len(observed) == row['exposed_original_cell_faces']
    a0, b, c = (positions[triangles[:, i]] for i in range(3))
    signed = np.sum(np.einsum('ij,ij->i', a0, np.cross(b, c))) / 6
    volume = mask.sum() * abs(np.linalg.det(a.affine[:3, :3]))
    assert signed == pytest.approx(volume, rel=2e-12)
    assert row['label_volume_ml'] == pytest.approx(volume / 1000)
    for connectivity, label in [(1, '6'), (3, '26')]:
        components, count = ndimage.label(mask, ndimage.generate_binary_structure(3, connectivity))
        expected_counts = sorted(map(int, np.bincount(components.ravel())[1:]), reverse=True)
        assert row['connectivity'][label] == dict(components=int(count), voxel_counts_descending=expected_counts)
    assert mask.sum() == {'acute': 2760, 'chronic': 11780, 'combined': 14540}[role]
    assert row['connectivity']['6']['components'] == {'acute': 13, 'chronic': 1, 'combined': 14}[role]


def test_javascript_native_read_scaling_oblique_mapping_and_negative_indices():
    code = """const a=require('./web/anatomy/soop-stroke-sub342/reference.js'),f=require('fs'),z=require('zlib'),c=require('crypto'),m=JSON.parse(f.readFileSync('./web/anatomy/soop-stroke-sub342/manifest.json'));let samples=0;for(const [role,row] of Object.entries(m.arrays)){const raw=new Uint8Array(z.gunzipSync(f.readFileSync('./web/'+row.file.slice(5)))),v=new DataView(raw.buffer,raw.byteOffset,raw.byteLength);if(c.createHash('sha256').update(raw).digest('hex')!==row.decoded_sha256)throw Error('buffer');for(let k=0;k<1001;k++){const p=row.spatial_shape.map((n,i)=>(k*(31+i*24)+i*17)%n),index=p[0]+row.shape[0]*(p[1]+row.shape[1]*p[2]),expected=row.dtype==='<i2'?v.getInt16(index*2,true):v.getUint8(index),value=a.readValue(raw,p,row);if(value!==expected||a.calibratedValue(value,row)!==expected*row.slope+row.intercept)throw Error('raw/scaled');for(let axis=0;axis<3;axis++){const [u,w]=a.axes[axis],q=a.pixelToSource(p[u],row.shape[w]-1-p[w],axis,p[axis],row.shape);if(q.some((x,i)=>x!==p[i]))throw Error('inverse');}samples++;}for(const p of [[-1,0,0],[.5,0,0],[row.shape[0],0,0],[NaN,0,0],[Infinity,0,0],[0,0]]){let rejected=false;try{a.readValue(raw,p,row);}catch(e){rejected=true;}if(!rejected)throw Error('invalid index accepted');}}for(const [role,row]of Object.entries(m.meshes)){const bytes=new Uint8Array(z.gunzipSync(f.readFileSync('./web/'+row.file.slice(5))));a.decodeMesh(bytes,row);for(const bad of [bytes.slice(0,-1),new Uint8Array(12)]){let ok=false;try{a.decodeMesh(bad,row);}catch(e){ok=true;}if(!ok)throw Error('bad geometry');}}for(const angle of [-180,-90,-20,0,25,90,180]){const p=[2,-3,5],q=a.camera(p,angle,angle);if(Math.abs(Math.hypot(...p)-Math.hypot(...q))>1e-12)throw Error('camera');}console.log(JSON.stringify({samples}));"""
    result = subprocess.run(['node', '-e', code], cwd=ROOT, text=True, capture_output=True, check=True)
    assert json.loads(result.stdout)['samples'] == 7007


def test_scope_never_grants_registration_clinical_units_timing_or_named_anatomical_coverage():
    m = manifest()
    for flag in ['clinical_approval', 'fine_anatomical_approval', 'structure_coverage_granted',
                 'current_patient_registration', 'T1_registered_to_diffusion', 'FLAIR_registered_to_diffusion',
                 'T1_registered_to_FLAIR', 'ADC_physical_units_verified', 'timing_or_pretreatment_state_known',
                 'source_resampling', 'source_sample_changes', 'source_mask_union_performed']:
        assert m[flag] is False
    for row in m['meshes'].values():
        assert row['label_volume_is_pretreatment_core_or_irreversible_tissue'] is False
        assert row['clinical_or_named_anatomical_boundary_approval'] is False
    source = (OUT / 'reference.js').read_text()
    assert sha((OUT / 'manifest.json').read_bytes()) in source
    assert 'await digest(manifestBody)!==MANIFEST_SHA256' in source
    html = (OUT / 'reference.html').read_text()
    assert 'ISLES' not in html and 'CC0' in html
    assert 'article\'s artwork terms' in html
    assert 'No masks are unioned' in html
    assert not (REVIEW / 'source/publication.xml').exists()


def test_finite_extreme_windows_do_not_overflow_or_invent_black_centre_values():
    code = "const a=require('./web/anatomy/soop-stroke-sub342/reference.js');if(a.windowGray(0,-1e308,1e308)!==128||a.windowGray(-1e308,-1e308,1e308)!==0||a.windowGray(1e308,-1e308,1e308)!==255||a.windowGray(5,0,10)!==128)throw Error('finite scaling');for(const args of [[0,NaN,1],[0,0,Infinity],[0,1,1],[0,2,1],[Infinity,0,1]]){let rejected=false;try{a.windowGray(...args);}catch(e){rejected=true;}if(!rejected)throw Error('invalid window');}console.log('passed');"
    result = subprocess.run(['node', '-e', code], cwd=ROOT, text=True, capture_output=True, check=True)
    assert result.stdout.strip() == 'passed'
