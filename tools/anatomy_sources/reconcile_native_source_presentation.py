#!/usr/bin/env python3
"""Check pinned native source presentation without rewriting approval ledgers."""
import argparse
import base64
import gzip
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess
import sys
import zlib
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
try:
    from tools.anatomy_sources.ui_refresh import advance as ui_refreshed
except ImportError:  # run as a script from its own directory
    from ui_refresh import advance as ui_refreshed
REVIEW = ROOT / 'docs/native-source-presentation-review-20261011'
NATIVE_CACHE = ROOT / '.research/native-source-presentation-20261011'
VERSE_MASTER = NATIVE_CACHE / 'verse-master'
VERSE_CANDIDATES = NATIVE_CACHE / 'verse-candidates'
SOURCE_IDS = ['liu-sub03-cord-contour-envelope', 'liu-sub03-dura-contour-envelope'] + [
    'verse521-' + level for level in [*[f't{i}' for i in range(1, 13)], *[f'l{i}' for i in range(1, 6)]]
] + ['verse521-native-ct-planes']
OLD = {'web/app.js': '911d86e91bb415ee6713c436c28f554e894d9416778dd2397571299b9bac83cb',
       'data/radiology/source-anatomy-references.json': '8861959d78acaf857aa2197dfb9c861cf540726036105e9c1c1f3f1b243c0577'}

def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def acquire_verse(destination):
    """Fetch only pinned case members, checking archive identity and ZIP CRC."""
    from tools.anatomy_sources.remote_zip_source import RemoteZipSource
    manifest = json.loads((ROOT / 'docs/msk-verse-source-review/case-acquisition.json').read_text())
    url = manifest['archive_url']
    assert url == 'https://s3.bonescreen.de/public/VerSe-complete/dataset-verse20training.zip'
    with urlopen(Request(url, method='HEAD'), timeout=60) as response:
        size = int(response.headers['Content-Length'])
        assert response.headers['ETag'] == manifest['etag']
    archive = RemoteZipSource(url, size)
    assert archive.etag == manifest['etag']
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    records = []
    for entry in manifest['files']:
        # Original CT, original whole-label NIfTI and original author preview.
        path = destination / Path(entry['member']).name
        if path.exists():
            raw = path.read_bytes()
        else:
            raw = archive.member(entry['member'])
            assert len(raw) == entry['size'] and sha(raw) == entry['sha256']
            path.write_bytes(raw)
        assert sha(raw) == entry['sha256'] and len(raw) == entry['size']
        assert zlib.crc32(raw) & 0xffffffff == entry['crc32']
        records.append({'file': str(path), 'source_member': entry['member'], 'sha256': sha(raw), 'bytes': len(raw), 'crc32': entry['crc32']})
        print(path.name, 'native SHA and CRC verified', flush=True)
    proof = {'archive_url': url, 'archive_bytes': size, 'etag': archive.etag, 'files': records,
             'clinical_approval': False, 'fine_3d_approval': False}
    (destination / 'acquisition-proof.json').write_text(json.dumps(proof, indent=2) + '\n')
    return proof


def mesh(path):
    import numpy as np
    encoded = path.read_bytes()
    raw = gzip.decompress(encoded)
    magic, n, k = struct.unpack('<4sII', raw[:12])
    assert magic == b'BP3D' and k % 3 == 0 and len(raw) == 12 + n * 24 + k * 4
    vertices = np.frombuffer(raw, '<f4', n * 3, 12).reshape(n, 3)
    normals = np.frombuffer(raw, '<f4', n * 3, 12 + n * 12).reshape(n, 3)
    faces = np.frombuffer(raw, '<u4', k, 12 + n * 24).reshape(k // 3, 3)
    assert np.isfinite(vertices).all() and np.isfinite(normals).all() and faces.max() < n
    return vertices, normals, faces, sha(encoded), sha(raw)


def embedded_verse_dataset():
    html = (ROOT / 'web/anatomy/verse521/ct-reference.html').read_text()
    match = re.search(r'<script id="dataset" type="application/json">(.*?)</script>', html, re.S)
    assert match
    return json.loads(match.group(1))


def verify_verse(source, candidates):
    """Independent affine/voxel/sample checks; no geometry generation or repair."""
    import nibabel as nib
    import numpy as np
    from scipy.ndimage import map_coordinates
    source, candidates = Path(source), Path(candidates)
    manifest = json.loads((ROOT / 'web/anatomy/verse521/manifest.json').read_text())
    chain = json.loads((ROOT / 'docs/msk-verse-source-review/chain-surface-audit.json').read_text())
    acquisition = json.loads((ROOT / 'docs/msk-verse-source-review/case-acquisition.json').read_text())
    for row in acquisition['files']:
        assert sha((source / Path(row['member']).name).read_bytes()) == row['sha256']
    ct = nib.load(source / 'sub-verse521_dir-ax_ct.nii.gz')
    segmentation = nib.load(source / 'sub-verse521_dir-ax_seg-vert_msk.nii.gz')
    assert ct.shape == segmentation.shape == (512, 512, 487)
    assert np.array_equal(ct.affine, segmentation.affine)
    assert ct.header.get_xyzt_units()[0] == 'mm'
    assert tuple(nib.aff2axcodes(ct.affine)) == ('L', 'A', 'S')
    dataset = embedded_verse_dataset()
    assert np.array_equal(ct.affine, dataset['affine'])
    assert tuple(dataset['axes']) == ('L', 'A', 'S')
    assert np.array_equal(ct.header.get_zooms(), dataset['spacing'])
    values = np.asanyarray(ct.dataobj)
    labels = np.asanyarray(segmentation.dataobj)
    assert np.isfinite(values).all()
    # The model's native RAS to display matrix preserves distances/handedness.
    display = np.array([[-1, 0, 0], [0, 0, 1], [0, 1, 0]])
    assert np.array_equal(display.T @ display, np.eye(3)) and np.linalg.det(display) == 1
    records = []
    for item in dataset['levels']:
        level, label = item['level'], item['label']
        expected_label = int(level[1:]) + (7 if level.startswith('T') else 19)
        assert label == expected_label
        part = manifest['parts']['verse521-' + level.lower()]
        v, n, f, encoded_hash, decoded_hash = mesh(ROOT / 'web' / part['file'].removeprefix('/app/'))
        assert encoded_hash == part['sha256'] and decoded_hash == part['decoded_sha256']
        saved = next(r for r in chain['levels'] if r['level'] == level)
        candidate = candidates / (level.lower() + '.npz')
        assert sha(candidate.read_bytes()) == saved['sha256'] == part['source_surface_sha256']
        with np.load(candidate) as original:
            assert np.array_equal(v.astype('f8'), original['vertices_world_mm'])
            assert np.array_equal(f, original['faces'])
            assert np.array_equal(original['affine'], ct.affine)
            voxel = np.linalg.solve(ct.affine[:3, :3], (v.astype('f8') - ct.affine[:3, 3]).T).T
            roundtrip_error = float(np.max(np.abs(voxel - original['vertices_voxel'])))
            assert roundtrip_error < 1e-7
        start, stop = np.array(item['start']), np.array(item['stop'])
        crop = tuple(slice(int(a), int(b)) for a, b in zip(start, stop))
        embedded_ct = np.frombuffer(gzip.decompress(base64.b64decode(item['ct'])), '<f4').reshape(item['shape'])
        embedded_label = np.frombuffer(gzip.decompress(base64.b64decode(item['mask'])), 'u1').reshape(item['shape'])
        assert np.array_equal(embedded_ct, values[crop])
        assert np.array_equal(embedded_label, labels[crop] == label)
        assert int(embedded_label.sum()) == item['foreground_voxels'] == saved['source_voxels']
        assert sha(embedded_ct.tobytes()) == item['ct_sha256']
        assert sha(embedded_label.tobytes()) == item['label_sha256']
        field_start = np.array(saved['crop_start'])
        field_stop = np.array(saved['crop_stop'])
        field = (labels[tuple(slice(int(a), int(b)) for a, b in zip(field_start, field_stop))] == label).astype(float)
        sampled = map_coordinates(field, (voxel - field_start).T, order=1, mode='constant', cval=0)
        fractions = voxel - np.floor(voxel)
        half = np.isclose(fractions, .5, rtol=0, atol=1e-7)
        helpers = half.sum(axis=1) == 3
        edge = half.sum(axis=1) == 1
        assert np.all(helpers | edge)
        assert np.max(np.abs(sampled[edge] - .5)) < 1e-7
        assert int(helpers.sum()) == saved['cell_center_helper_vertices']
        residual = float(np.max(np.abs(sampled - .5)))
        assert abs(residual - saved['maximum_saved_vertex_isovalue_residual']) < 1e-7
        triangles = v.astype('f8')[f]
        area = np.cross(triangles[:, 1] - triangles[:, 0], triangles[:, 2] - triangles[:, 0])
        assert np.all(np.linalg.norm(area, axis=1) > 0)
        normal_error = float(np.max(np.abs(np.linalg.norm(n.astype('f8'), axis=1) - 1)))
        assert normal_error < 1e-6
        witnesses = []
        for axis in range(3):
            for slice_number in [0, item['shape'][axis] // 2, item['shape'][axis] - 1]:
                point = np.array(item['shape']) // 2
                point[axis] = slice_number
                native = point + start
                world = ct.affine[:3, :3] @ native + ct.affine[:3, 3]
                witnesses.append({'axis': axis, 'slice': slice_number, 'native_voxel': native.tolist(),
                                  'RAS_mm': world.tolist(), 'scaled_ct_value': float(values[tuple(native)]),
                                  'target_membership': int(labels[tuple(native)] == label), 'source_label': label})
        records.append({'id': part['id'], 'level': level, 'source_label': label, 'source_mesh_sha256': encoded_hash,
                        'decoded_mesh_sha256': decoded_hash, 'vertices': len(v), 'triangles': len(f),
                        'candidate_vertices_and_faces_exact': True, 'affine_voxel_roundtrip_max_voxels': roundtrip_error,
                        'original_crop_ct_and_binary_membership_exact': True, 'ct_crop_sha256': item['ct_sha256'],
                        'membership_crop_sha256': item['label_sha256'], 'source_foreground_voxels': int(embedded_label.sum()),
                        'edge_vertices_isovalue_exact': True, 'retained_helper_vertices': int(helpers.sum()),
                        'helper_or_edge_max_field_residual': residual, 'unit_normal_max_error': normal_error,
                        'plane_witnesses': witnesses, 'anatomical_review': 'pending', 'clinical_approval': False})
        print(level, 'all source positions/faces/crop voxels verified', flush=True)
    assert len(records) == 17 and sum(r['triangles'] for r in records) == 798442
    return {'case': 'sub-verse521', 'source_files': manifest['source_files'], 'affine': ct.affine.tolist(),
            'source_shape': list(ct.shape), 'spacing_mm': list(map(float, ct.header.get_zooms())), 'axis_codes': list(nib.aff2axcodes(ct.affine)),
            'source_acquisition_slice_thickness_mm': manifest['source_acquisition']['slice_thickness_mm'],
            'source_data_scaling': {'slope': float(ct.dataobj.slope), 'intercept': float(ct.dataobj.inter)},
            'display_transform': display.tolist(), 'parts': records, 'total_triangles': 798442,
            'clinical_approval': False, 'fine_3d_approval': False,
            'limits': ['Whole-vertebra source labels do not certify separate cortical/trabecular/endplate/pedicle/facet boundaries.',
                       'Lewiner cell-centre helper approximations, T7 diagonal connectivity and T12 enclosed background are retained.',
                       'CT acquisition thickness 1.5 mm differs from stored slice spacing 1.0 mm; source pathology/calibration remain unverified.',
                       'No discs, ligament/root/cord geometry or cross-case Liu registration is supplied.']}


def validate_reader_oracles(browser, oracles):
    """Check the portable observations against independently computed native oracles."""
    assert browser['passed'] and not browser['errors'] and not browser['localHttpFailures']
    assert {'web/app.js', 'web/styles.css', 'web/anatomy/verse521/ct-reference.js'} <= set(browser['served'])
    assert [row['width'] for row in browser['rows']] == [1440, 390]
    assert len(oracles['levels']) == 17 and len(oracles['meshes']) == 19
    for row in browser['rows']:
        assert row['lifecycle']['pendingDecodeCleared'] and row['lifecycle']['pendingOutsideCleared']
        assert row['lifecycle']['errorCleared'] and row['lifecycle']['errorOutsideCleared']
        assert row['lifecycle']['failedDecodeControlled']
        assert len(row['meshSelections']) == len(row['ct']) == 17 and len(row['liu']) == 2
        assert sum(len(p['slices']) for level in row['ct'] for p in level['planes']) == 153
        assert sum(len(p['pointers']) for level in row['ct'] for p in level['planes']) == 102
        hashes = {buffer['sha256'] for buffer in row['gpu']['buffers']}
        for mesh in oracles['meshes'].values():
            assert {mesh['positions'], mesh['normals'], mesh['gpu_indices']} <= hashes
        for actual, expected in zip(row['ct'], oracles['levels'], strict=True):
            assert (actual['level'], actual['label']) == (expected['level'], expected['label'])
            for plane, oracle in zip(actual['planes'], expected['planes'], strict=True):
                assert plane['axis'] == oracle['axis'] and plane['outside']
                for frame, native in zip(plane['slices'], oracle['slices'], strict=True):
                    assert frame['rgba'] == native['rgba_sha256'], 'Reader native pixel oracle mismatch'
                    assert frame['canvas'] == native['canvas'] and frame['ct'] == native['ct_center']
                    assert frame['slice'] == native['native_center'][plane['axis']]
                    assert frame['directions'] == oracle['directions']
                    assert abs(frame['aspect'] - oracle['physical_aspect']) < .001
                    assert not frame['overflow']
                for pointer, native in zip(plane['pointers'], oracle['pointers'], strict=True):
                    assert pointer['membership'] == native['membership']
                    assert pointer['text'] == native['expected'], 'Reader native pointer oracle mismatch'


def portable_evidence(path):
    path = Path(path).resolve()
    relative = path.relative_to(ROOT)
    assert str(relative).startswith('docs/native-source-presentation-review-20261011/')
    return {'path': relative.as_posix(), 'sha256': sha(path.read_bytes())}


def proposed_contract(liu_proof, reader_proof):
    """Produce exact proposed changes only; root owns application to ledgers."""
    initial = json.loads((REVIEW / 'initial-dependency-issues.json').read_text())
    verse_path = REVIEW / 'verse-native-coordinate-proof.json'
    verse = json.loads(verse_path.read_text())
    liu_path, reader_path = Path(liu_proof), Path(reader_proof)
    liu, browser = json.loads(liu_path.read_text()), json.loads(reader_path.read_text())
    oracle_path = REVIEW / 'reader-native-oracles.json'
    validate_reader_oracles(browser, json.loads(oracle_path.read_text()))
    assert initial['issue_count'] == 40 and initial['asset_count'] == 20
    assert set(r['id'] for r in initial['original_issues']) == set(SOURCE_IDS)
    assert verse['clinical_approval'] is False and len(verse['parts']) == 17
    assert liu['clinical_approval'] is False and liu['anatomical_approval'] is False
    assert liu['source_original_curve_settings_recovered'] is False
    assert browser['passed'] and not browser['errors'] and not browser['localHttpFailures']
    assert [row['width'] for row in browser['rows']] == [1440, 390]
    for row in browser['rows']:
        assert len(row['meshSelections']) == len(row['ct']) == 17 and len(row['liu']) == 2
        assert sum(len(p['slices']) for level in row['ct'] for p in level['planes']) == 153
        assert sum(len(p['pointers']) for level in row['ct'] for p in level['planes']) == 102
        assert all(p['outside'] for level in row['ct'] for p in level['planes'])
    # app.js and styles.css may have moved on through a recorded UI-only
    # refresh (data/radiology/ui-presentation-refreshes.json); every native
    # file must still be byte-identical to what the proof served.
    for name, expected in browser['served'].items():
        assert sha((ROOT / name).read_bytes()) == ui_refreshed(name, expected), 'Reader proof is stale: ' + name
    evidence = json.loads((ROOT / 'data/radiology/msk-asset-evidence.json').read_text())
    by_id = {a['id']: a for a in evidence['assets']}
    amendments = []
    for ident in SOURCE_IDS:
        asset = by_id[ident]
        assert asset['anatomical_review']['status'] == 'pending' and not asset['structure_ids']
        assert not asset.get('requirement_coverage')
        assert sha((ROOT / asset['local_path']).read_bytes()) == asset['sha256']
        dependencies = {name: sha((ROOT / name).read_bytes()) for name in asset['presentation_dependencies']}
        changes = {name: {'before': old, 'after': dependencies[name]} for name, old in asset['presentation_dependencies'].items() if old != dependencies[name]}
        expected_issues = [r for r in initial['original_issues'] if r['id'] == ident]
        assert len(expected_issues) == 2 and all(asset['presentation_dependencies'][r['path']] == r['expected'] for r in expected_issues)
        amendment = {'id': ident, 'source_local_path': asset['local_path'], 'unchanged_source_sha256': asset['sha256'],
            'original_issue_count': 2, 'original_issues': expected_issues, 'proposed_dependency_changes': changes,
            'proposed_presentation_dependencies': dependencies,
            'proposed_presentation_reconciliation_review': {
                'reviewed_at': '2026-10-11', 'scope': 'Original source bytes, native coordinates and bounded current reader presentation only',
                'native_source_proof': 'Liu direct CISS/146 controls and exact saved open-loft candidates' if ident.startswith('liu-') else 'Fresh VerSe NIfTI CT/mask; every surface position/face and embedded source voxel checked',
                'reader_proof': 'Actual source references, selections, layers, camera labels, native WebGL buffer bytes, CT pixel/world/direction oracles, pointer membership and outside states at 1440/390',
                'review_path': 'docs/native-source-presentation-review-20261011/README.md',
                'original_dependency_issues_preserved': True, 'source_bytes_changed': False,
                'anatomical_approval_or_requirement_coverage_changed': False,
                'author_specific_curve_settings_recovered': False if ident.startswith('liu-') else None,
            },
            'preserve_fields_exactly': ['sha256', 'structure_ids', 'requirement_coverage', 'anatomical_review', 'fidelity', 'source'],
            'anatomical_review_status_after': 'pending', 'clinical_approval': False, 'fine_3d_approval': False,
            'requirement_coverage_after': {}, 'apply_status': 'proposed_pending_root_independent_review'}
        if ident.startswith('liu-'):
            amendment['proposed_geometry_coordinate_metadata'] = {'basis': 'LPS', 'units': 'millimetres', 'unit_meters': .001,
                'display_mapping': '[L,P,S] → [L,S,−P]', 'source_coordinate_provenance': 'Original Markups LPS controls and native CISS support; source-specific interpolation settings were not recorded.'}
            amendment['proposed_source_unknowns_append'] = ['The primary publication reports a healthy adult volunteer cohort for the released data; independent normality, boundary accuracy and diagnosis of this individual case remain unestablished.']
        amendments.append(amendment)
    assert len(amendments) == 20 and sum(a['original_issue_count'] for a in amendments) == 40
    scope_path = ROOT / 'data/radiology/source-anatomy-references.json'
    refs = json.loads(scope_path.read_text())['ra.thoracolumbar-fractures']
    return {'schema_version': 1, 'initial_commit': initial['initial_commit'], 'original_issue_count': 40, 'asset_count': 20,
        'original_issues': initial['original_issues'], 'all_original_issues_recorded': True,
        'actual_defect_fixed': {'helper': 'web/anatomy/verse521/ct-reference.js', 'sha256': sha((ROOT / 'web/anatomy/verse521/ct-reference.js').read_bytes()),
            'before': 'Binary membership0/1 called target label, conflating it with original source IDs8–24; outside coordinates clamped to a voxel. Prior-level sample could remain during pending or failed decode.',
            'after': 'Selected T/L level and original source label shown separately from membership present/absent; invalid/outside/leave yields no sampled voxel. Loading/error clears the prior sample and source scope; superseded decode errors cannot overwrite a newer load.',
            'source_voxels_or_geometry_changed': False},
        'source_reference_registry_sha256': sha(scope_path.read_bytes()), 'thoracolumbar_source_references': refs,
        'amendments': amendments,
        'evidence': [portable_evidence(p) for p in [
            verse_path, liu_path, reader_path, oracle_path,
            REVIEW / 'verse-native-acquisition-proof.json', REVIEW / 'liu-native-acquisition-proof.json',
            REVIEW / 'screenshots.json']],
        'evidence_path_policy': 'Repository-relative evidence paths and SHA-256 values are authoritative; private reproduction locations in source proofs are supplemental only. Native MRI/CT volumes and contour/candidate arrays remain ignored.',
        'original_provenance_limits_retained': True, 'unrelated_holds_or_approvals_cleared': False,
        'source_presentation_verified': True, 'clinical_approval': False, 'fine_anatomical_approval': False,
        'remaining_fine_boundary_gaps': [
            'VerSe whole-vertebra labels do not independently identify/validate cortical thickness, endplate layers, pedicles, facets or trabecular boundaries.',
            'No disc, ligament, epidural/CSF/root/cord or fracture/compression geometry is supplied by this VerSe package.',
            'Liu finite open lofts do not supply complete conus tips, rootlets/cauda equina, grey/white matter, dura wall thickness or a closed CSF volume.',
            'Author curve settings, continuous spline/surface nonintersection, case pathology and anatomical boundary accuracy remain unverified.',
            'Two source cases remain independent; no MRI-to-CT, current-patient or cross-atlas registration is created.',
        ], 'outcomes_not_established': ['Fine tissue/anatomical accuracy', 'Complete clinical reporting coverage', 'Case diagnosis/pathology', 'MRI/CT cross-case registration'],
        'apply_status': 'proposed_pending_root_independent_review'}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--acquire-verse', action='store_true',
                        help='Acquire the pinned case into the fixed ignored native cache')
    parser.add_argument('--verify-verse', action='store_true',
                        help='Compare the fixed native cache with the fixed candidate cache')
    parser.add_argument('--write-verse-proof', action='store_true')
    parser.add_argument('--make-proposed-contract', action='store_true')
    args = parser.parse_args(argv)
    if args.acquire_verse:
        acquire_verse(VERSE_MASTER)
    if args.verify_verse:
        result = verify_verse(VERSE_MASTER, VERSE_CANDIDATES)
        if args.write_verse_proof:
            REVIEW.mkdir(parents=True, exist_ok=True)
            (REVIEW / 'verse-native-coordinate-proof.json').write_text(json.dumps(result, indent=2) + '\n')
        print('17 native VerSe levels and all embedded source crops verified; no anatomical approval')
    if args.make_proposed_contract:
        result = proposed_contract(REVIEW / 'liu-native-coordinate-proof.json',
                                   REVIEW / 'reader-presentation-proof.json')
        REVIEW.mkdir(parents=True, exist_ok=True)
        (REVIEW / 'proposed-presentation-amendments.json').write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
        print('Proposed 20 source-presentation amendments; all 40 original issues retained; no approval or ledger edits')


if __name__ == '__main__':
    sys.path.insert(0, str(ROOT))
    main()
