"""Independent rater export must preserve components and detect omitted source regions."""
import pytest
np = pytest.importorskip('numpy')
pytest.importorskip('nibabel')
pytest.importorskip('skimage')
from tools.anatomy_sources.massp_probability_mesh import mesh_mask
from tools.anatomy_sources.build_liver_mri_rater_surfaces import audit_voxel_centres


def two_components():
    mask = np.zeros((18, 16, 14), bool)
    mask[3:7, 4:9, 3:6] = True
    mask[11:14, 10:12, 8:11] = True
    affine = np.diag([1.40625, 1.40625, 2.5, 1.])
    affine[:3, 3] = [-200.86978149414062, -144.84375, -68.4110107421875]
    return mask, affine


def test_anisotropic_rater_export_keeps_both_source_components():
    mask, affine = two_components()
    vertices, faces, stats = mesh_mask(mask, affine)
    audit = audit_voxel_centres(mask, affine, vertices, faces)
    assert stats['source_components_6_connected'] == 2
    assert audit['complete_source_positive_voxels'] == 78
    assert audit['exact_voxel_centre_match']


def test_omitting_small_source_component_is_detected():
    mask, affine = two_components()
    incomplete = mask.copy(); incomplete[11:14, 10:12, 8:11] = False
    vertices, faces, _ = mesh_mask(incomplete, affine)
    with pytest.raises(ValueError, match='Full source annotation extent'):
        audit_voxel_centres(mask, affine, vertices, faces)


def test_shifted_mesh_cannot_claim_voxel_fidelity():
    mask, affine = two_components()
    vertices, faces, _ = mesh_mask(mask, affine)
    vertices[:, 0] += 1.40625
    audit = audit_voxel_centres(mask, affine, vertices, faces)
    assert audit['false_positive'] > 0
    assert audit['false_negative'] > 0
    assert not audit['exact_voxel_centre_match']
