"""Exact published templates are interpretable data, not complete clinical anatomy."""
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

import pytest

from tools.anatomy_sources.review_west_bohemia_pelvic_source import inspect_arrays, ORIGINAL_ARCHIVE_SHA256

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / 'docs/west-bohemia-pelvic-source-review'


@pytest.mark.parametrize('change', ['nonfinite', 'missing_axis', 'fractional_index', 'negative_index',
                                  'absent_vertex', 'quad', 'truncated_cell'])
def test_invalid_source_faces_or_scalars_cannot_be_silently_repaired(change):
    value = [[[0, 0, 0], [1, 0, 0], [0, 1, 0]], [3, 0, 1, 2]]
    if change == 'nonfinite': value[0][0][0] = float('inf')
    elif change == 'missing_axis': value[0][0].pop()
    elif change == 'fractional_index': value[1][-1] = 1.5
    elif change == 'negative_index': value[1][-1] = -1
    elif change == 'absent_vertex': value[1][-1] = 3
    elif change == 'quad': value[1][0] = 4
    else: value[1].pop()
    with pytest.raises(ValueError): inspect_arrays(value)


def test_reference_triangle_keeps_order_and_does_not_gain_volume_or_clinical_credit():
    np = pytest.importorskip('numpy')
    value = [[[0, 0, 0], [1, 0, 0], [0, 1, 0]], [3, 0, 1, 2]]
    proof = inspect_arrays(value)
    assert proof['positions'] == 3 and proof['triangles'] == 1
    assert proof['boundary_edges'] == 3 and proof['nonmanifold_edges'] == 0
    assert proof['positions_float64_le_sha256'] == hashlib.sha256(np.asarray(value[0], dtype='<f8').tobytes()).hexdigest()
    assert not proof['topology_findings_are_anatomical_accuracy_metrics']


def test_all_original_JSON_bytes_and_both_complete_object_inventories_are_retained():
    proof = json.loads((REVIEW / 'review.json').read_text())
    assert proof['source_archive_MD5_verified'] and proof['doi'] == '10.5281/zenodo.17423100'
    assert proof['source_archive_sha256'] == ORIGINAL_ARCHIVE_SHA256
    assert proof['software_license']['id'] == 'mit-license'
    assert hashlib.sha256((REVIEW / 'original-License.txt').read_bytes()).hexdigest() == proof['license_sha256']
    for model, count, positions, triangles in zip(proof['models'], [22, 43], [130146, 133874], [271775, 271771]):
        raw = (REVIEW / model['retained_file']).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == model['retained_file_sha256']
        original = gzip.decompress(raw)
        assert hashlib.sha256(original).hexdigest() == model['source_JSON_sha256']
        data = json.loads(original)
        assert list(data) == [o['source_label'] for o in model['objects']]
        assert len(data) == model['object_count'] == count
        assert model['positions'] == positions and model['triangles'] == triangles
        assert all(o['unreferenced_points'] == 0 and o['zero_area_triangles'] == 0 for o in model['objects'])
        assert model['independent_complete_scalar_and_index_readback_verified']
    for key in ['source_geometry_changed', 'MRI_subject_demographics_or_acquisition_verified',
                'physical_coordinate_units_or_clinical_axes_verified', 'template_registered_to_CVH5_or_current_MRI',
                'fine_reported_layer_boundaries_verified', 'clinical_approval', 'runtime_promoted', 'structure_coverage_granted']:
        assert not proof[key]
    assert proof['identical_shared_organ_arrays'] == ['Bladder', 'Urethra', 'Uterus', 'Vagina', 'Rectum & intestinum']


@pytest.mark.skipif(shutil.which('node') is None, reason='Independent V8 parser needs Node.js')
def test_every_source_coordinate_and_face_matches_both_independent_interpreters(tmp_path):
    pytest.importorskip('numpy')
    proof = json.loads((REVIEW / 'review.json').read_text())
    keys = ['positions', 'triangles', 'positions_float64_le_sha256',
            'original_VTK_cells_uint32_le_sha256', 'ordered_triangle_indices_uint32_le_sha256']
    for model in proof['models']:
        source = tmp_path / model['source_filename']
        source.write_bytes(gzip.decompress((REVIEW / model['retained_file']).read_bytes()))
        data = json.loads(source.read_bytes())
        result = subprocess.run(['node', str(ROOT / 'tools/anatomy_sources/read_pelvic_source_arrays.cjs')],
                                input=source.read_text(), text=True, capture_output=True, check=True)
        independent = json.loads(result.stdout)
        for obj in model['objects']:
            actual = inspect_arrays(data[obj['source_label']])
            assert {k: actual[k] for k in keys} == {k: obj[k] for k in keys} == independent[obj['source_label']]


def test_a_working_control_cube_does_not_clear_the_held_CVH_decoder():
    folder = ROOT / 'docs/cvh5-independent-decoder-review'
    proof = json.loads((folder / 'review.json').read_text())
    original = json.loads((ROOT / 'docs/cvh5-pelvic-source-review/original-model-inventory.json').read_text())
    assert proof['original_u3d_sha256'] == original['u3d_sha256']
    assert proof['expected_original_model_nodes'] == proof['expected_RHAdobe_mesh_resources'] == 47
    assert proof['control_cube']['control_points'] == 8 and proof['control_cube']['polygons'] == 12
    actual = proof['original_source_import']
    assert actual['exception'] == 'com.aspose.threed.TrialException'
    assert actual['retained_model_children'] == 5 and actual['meshes_returned'] == 0
    assert not actual['full_geometry_or_bootstrap_verified']
    assert not actual['geometry_absence_proves_source_defect'] and not actual['geometry_absence_proves_RHAdobe_unsupported']
    for name, expected in proof['logs'].items():
        assert hashlib.sha256((folder / name).read_bytes()).hexdigest() == expected
    assert not proof['trial_limits_bypassed'] and not proof['SDK_redistributed_or_added_to_runtime']
    assert not proof['clinical_approval'] and not proof['runtime_promoted']
