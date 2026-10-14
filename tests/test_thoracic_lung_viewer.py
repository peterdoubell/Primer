"""Browser transports preserve every original surface vertex and face association."""
import gzip,hashlib,json
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
REVIEW=ROOT/'docs/thoracic-lung-source-review-s0028'


def test_centered_transport_preserves_source_positions_faces_and_declared_error():
    data=json.loads((REVIEW/'viewer-manifest.json').read_text());source=json.loads((REVIEW/'source-review.json').read_text());origin=np.asarray(data['mesh_origin_source_mm']);assert len(data['parts'])==5
    for part,row in zip(data['parts'],source['records'][1:]):
        encoded=(REVIEW/part['buffer_file']).read_bytes();assert hashlib.sha256(encoded).hexdigest()==part['buffer_sha256'];body=gzip.decompress(encoded);assert hashlib.sha256(body).hexdigest()==part['buffer_decoded_sha256'];n=part['vertices'];assert len(body)==n*24+part['triangles']*12
        positions=np.frombuffer(body,dtype='<f4',count=n*3).reshape(-1,3);normals=np.frombuffer(body,dtype='<f4',count=n*3,offset=n*12).reshape(-1,3);faces=np.frombuffer(body,dtype='<u4',offset=n*24).reshape(-1,3)
        original=np.frombuffer(gzip.decompress((REVIEW/row['surfaces']['positions.f64.gz']['file']).read_bytes()),dtype='<f8').reshape(-1,3);original_faces=np.frombuffer(gzip.decompress((REVIEW/row['surfaces']['triangles.u32.gz']['file']).read_bytes()),dtype='<u4').reshape(-1,3)
        assert np.array_equal(faces,original_faces);error=float(np.abs(positions.astype(float)+origin-original).max());assert error==part['max_centered_float32_position_error_source_mm']==0
        assert np.isfinite(normals).all();assert part['mask_payload_sha256']==row['source_header']['raw_voxel_sha256']
    assert not data['clinical_approval'] and not data['runtime_promoted']


def test_browser_proof_retains_original_arrays_and_covers_all_plane_boundaries():
    proof=json.loads((REVIEW/'viewer-browser-proof.json').read_text());assert len(proof['rows'])==90;assert not proof['errors'];assert proof['original_array_hashes_exact'] and proof['plane_world_corners_exact']
    for width in [1440,390]:
        for label in range(5):
            for axis in range(3):assert len([r for r in proof['rows'] if (r['width'],r['label'],r['axis'])==(width,label,axis)])==3
    for field in ['failed_volume_hides_previous_images_and_geometry','failed_volume_retry_recovers','failed_surface_hides_previous_geometry','failed_surface_retry_recovers']:assert proof[field]
    for name,value in proof['implementation_file_sha256'].items():assert hashlib.sha256((REVIEW/name).read_bytes()).hexdigest()==value


def test_gpu_proof_binds_all_surface_uploads_and_draw_counts():
    proof=json.loads((REVIEW/'viewer-gpu-proof.json').read_text());data=json.loads((REVIEW/'viewer-manifest.json').read_text());parts={p['id']:p for p in data['parts']};assert len(proof['rows'])==10
    for row in proof['rows']:
        assert row['all_uploaded_buffers_exact'];assert row['drawn_source_triangles']==parts[row['id']]['triangles']
    assert {(r['width'],r['id']) for r in proof['rows']}=={(w,i) for w in [1440,390] for i in parts}
