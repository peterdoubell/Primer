"""All original thoracic source coordinates, normals and face order remain inspectable."""
import gzip
import hashlib
import json
from pathlib import Path
import struct
import numpy as np
from tools.anatomy_sources.review_bodyparts_pancreatic_geometry import read_obj
from tools.anatomy_sources.package_thoracic_original_sources import EXPECTED

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / 'docs/thoracic-native-anatomy-review-20261013'


def test_every_original_face_and_authored_normal_survives_transport():
    manifest = json.loads((REVIEW / 'manifest.json').read_text())
    acquisition = json.loads((REVIEW / 'evidence/upstream-acquisition.json').read_text())
    records = {row['id']: row for row in acquisition['objects']}
    assert set(records) == set(EXPECTED) == {part['id'] for part in manifest['parts']}
    assert manifest['total_faces'] == 649480
    assert not manifest['clinical_approval'] and not manifest['current_patient_registration']
    assert not manifest['source_acquisition_resolution_verified'] and not manifest['runtime_integrated']
    for part in manifest['parts']:
        raw = gzip.decompress((REVIEW / part['source_obj']).read_bytes())
        assert hashlib.sha256(raw).hexdigest() == part['source_sha256'] == records[part['id']]['sha256']
        vertices, normals, faces, normal_faces = read_obj(raw.decode())
        assert np.array_equal(faces, normal_faces)
        compressed = (REVIEW / part['file']).read_bytes()
        assert hashlib.sha256(compressed).hexdigest() == part['transport_sha256']
        body = gzip.decompress(compressed)
        assert hashlib.sha256(body).hexdigest() == part['decoded_sha256']
        signature, nv, ni = struct.unpack_from('<4sII', body)
        assert signature == b'BP3D' and nv == len(vertices) and ni == faces.size
        assert len(body) == 12 + nv * 24 + ni * 4
        position = np.frombuffer(body, dtype='<f4', count=nv*3, offset=12).reshape(-1, 3)
        normal = np.frombuffer(body, dtype='<f4', count=nv*3, offset=12+nv*12).reshape(-1, 3)
        index = np.frombuffer(body, dtype='<u4', count=ni, offset=12+nv*24).reshape(-1, 3)
        assert np.array_equal(position, vertices.astype('<f4'))
        assert np.array_equal(normal, normals.astype('<f4'))
        assert np.array_equal(index, faces)
        error = float(np.abs(position.astype(float)-vertices).max())
        assert error == part['max_position_conversion_error_source_mm'] and error < .00006
        assert not part['geometry_altered_beyond_measured_float32_transport']
        original_cross = np.cross(vertices[faces[:,1]]-vertices[faces[:,0]], vertices[faces[:,2]]-vertices[faces[:,0]])
        transported = position.astype(float)
        transport_cross = np.cross(transported[faces[:,1]]-transported[faces[:,0]], transported[faces[:,2]]-transported[faces[:,0]])
        assert np.all(np.linalg.norm(transport_cross, axis=1) > 0)
        assert np.all(np.sum(original_cross * transport_cross, axis=1) > 0)


def test_original_license_and_mapping_evidence_are_retained():
    acquisition = json.loads((REVIEW / 'evidence/upstream-acquisition.json').read_text())
    for name, digest in acquisition['source_metadata_sha256'].items():
        path = REVIEW / 'evidence' / name
        raw = path.read_bytes() if path.exists() else gzip.decompress(path.with_name(path.name+'.gz').read_bytes())
        assert hashlib.sha256(raw).hexdigest() == digest
    assert b'creativecommons.org/licenses/by-sa/2.1/jp/' in (REVIEW/'evidence/upstream-license.html').read_bytes()
    assert acquisition['archive_40_cc_by_40_grant_reused_for_upstream_meshes'] is False


def test_diaphragm_source_events_remain_in_the_actual_original_faces():
    proof = json.loads((REVIEW / 'evidence/topology-events.json').read_text())
    raw = gzip.decompress((REVIEW / 'originals/FJ3131.obj.gz').read_bytes())
    vertices, _, faces, _ = read_obj(raw.decode())
    points, remap = np.unique(vertices, axis=0, return_inverse=True)
    mapped = remap[faces]
    edges = np.sort(np.concatenate([mapped[:, [0, 1]], mapped[:, [1, 2]], mapped[:, [2, 0]]]), axis=1)
    unique, counts = np.unique(edges, axis=0, return_counts=True)
    actual = unique[counts > 2]
    assert len(actual) == len(proof['events']) == 4
    assert proof['geometry_repaired'] is False
    for edge, event in zip(actual, proof['events']):
        assert event['source_id'] == 'FJ3131'
        assert event['edge_coordinates_source_mm'] == points[edge].tolist()
        incident = np.flatnonzero(np.sum(np.isin(mapped, edge), axis=1) == 2)
        assert event['incident_face_indices_zero_based'] == incident.tolist()
        assert event['incident_original_vertex_indices_zero_based'] == faces[incident].tolist()
        assert len(incident) == 4 and .0019 < event['length_source_mm'] < .0031


def test_browser_proof_covers_every_original_and_common_coordinate_assembly():
    proof = json.loads((REVIEW / 'evidence/browser-proof.json').read_text())
    selections = set(EXPECTED) | {'all', 'intercostals', 'valves'}
    assert {(r['width'], r['selection']) for r in proof['rows']} == {(w,s) for w in [1440,390] for s in selections}
    assert len(proof['rows']) == 30 and not proof['errors']
    for row in proof['rows']:
        assert row['all_drawn_GPU_buffers_match_preserved_source'] and row['camera_checks'] == 10
        if row['selection'] == 'all':
            assert set(row['parts']) == set(EXPECTED) and row['source_faces'] == 649480
    assert proof['clinical_approval'] is False and proof['runtime_integrated'] is False
    for name, digest in proof['implementation_file_sha256'].items():
        assert hashlib.sha256((REVIEW / name).read_bytes()).hexdigest() == digest
