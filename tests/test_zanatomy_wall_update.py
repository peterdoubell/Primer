"""Fresh source dates and names cannot silently clear unchanged geometric defects."""
import gzip
import hashlib
import json
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[1]
REVIEW=ROOT/'docs/zanatomy-wall-update-review'


def test_pinned_current_archive_reader_and_blocked_script_are_explicit():
    r=json.loads((REVIEW/'current-wall-comparison.json').read_text())
    assert r['source_license_sha256']==hashlib.sha256((REVIEW/'License.txt').read_bytes()).hexdigest()
    assert r['observed_head']=='ded1a55381328f3f242426f0e8e711c5fca62c14'
    assert r['archive_bytes']==86734957 and r['archive_git_blob_sha1']=='f43cabc6f366b2a6058dd2ed4a2b3c7b9b2492cb'
    assert r['archive_sha256']=='e029688545627bd0214b269e1063143abb580aad72b2c2445d6d8a9a0d9da736'
    assert r['scene_header']=='BLENDER-v305' and r['scene_bytes']==306838281
    assert r['scene_sha256']=='9f08a17ea0115fed80b2a73ecdf0a1bc2ab2f6956f37c593ce23d513ea35afcd'
    assert r['archive_crc_verified'] and r['scene_bytes_match_original_archive']
    assert r['runtime_checksum_verified'] and r['reader_version']=='4.2.23 LTS'
    assert r['runtime_dmg_sha256']=='8b6bc5fafd4773e94bb863ca19ba1c9a54d096eecbbc4375eae7dbc3b49fab40'
    assert r['file_autoexec_failure'] and "Text 'z-anatomy.py'" in r['file_autoexec_failure_message']
    assert r['inspection_script_sha256']==hashlib.sha256((ROOT/'tools/anatomy_sources/inspect_zanatomy_wall_blend.py').read_bytes()).hexdigest()


def test_all_original_wall_mesh_values_and_evaluated_outputs_match_older_source():
    r=json.loads((REVIEW/'current-wall-comparison.json').read_text())
    old=json.loads((ROOT/'docs/zanatomy-wall-source-review/native-wall-review.json').read_text())
    assert r['previous_native_review_sha256']==hashlib.sha256((ROOT/'docs/zanatomy-wall-source-review/native-wall-review.json').read_bytes()).hexdigest()
    assert r['all_sixteen_original_wall_objects_compared'] and len(r['records'])==16
    assert {i['object_name'] for i in r['records']}=={i['name'] for i in old['instances']}
    for i in r['records']:
        assert i['local_positions_exactly_equal'] and i['polygon_corner_order_exactly_equal']
        assert i['previous_positions_float64_sha256']==i['current_positions_float64_sha256']
        assert i['original_and_evaluated_meshes_exactly_equal'] and not i['modifiers']
        assert abs(i['matrix_determinant'])>1e-12
        assert i['unchanged_geometry_cannot_remove_existing_interior_crossings']
    assert sum(i['material_assignments_exactly_equal'] for i in r['records'])==8
    assert sum(i['material_slot_names_exactly_equal'] for i in r['records'])==5
    assert sum(i['resolved_per_face_material_names_equal'] for i in r['records'])==13
    assert not r['existing_model_quality_holds_resolved']
    assert not r['source_mesh_changed_or_saved'] and not r['clinical_approval'] and not r['runtime_promoted']
    assert not r['named_object_queries']['rectus sheath'] and not r['named_object_queries']['scarpa'] and not r['named_object_queries']['camper']
    assert all('abdom' not in i['name'].lower() for i in r['named_object_queries']['semilunar']+r['named_object_queries']['aponeurosis'])


def test_locally_retained_capture_values_match_comparison_hashes():
    directory=ROOT/'.research/zanatomy-wall-update/native-wall'
    if not directory.exists():pytest.skip('Original full source/captures are retained in ignored staging')
    np=pytest.importorskip('numpy')
    report=json.loads((REVIEW/'current-wall-comparison.json').read_text())
    inv=json.loads((directory/'original-blend-wall-inventory.json').read_text())
    for i in report['records']:
        original=next(r for r in inv['records'] if r['object_name']==i['object_name'])
        packed=(directory/original['file']).read_bytes();raw=gzip.decompress(packed)
        assert hashlib.sha256(packed).hexdigest()==i['capture_compressed_sha256']
        assert hashlib.sha256(raw).hexdigest()==i['capture_uncompressed_sha256']
        source=json.loads(raw);points=np.asarray(source['original_mesh']['positions'])
        assert hashlib.sha256(points.astype('<f8').tobytes()).hexdigest()==i['current_positions_float64_sha256']
        assert source['original_mesh']==source['evaluated_mesh']
