"""Review localization must expose diagonal connectivity and retain disconnected label differences."""
import pytest
np = pytest.importorskip('numpy')
pytest.importorskip('scipy')
from tools.anatomy_sources.localize_liver_mri_rater_boundaries import adjacency_locations, outside_components


def test_diagonal_foreground_is_localized_without_repair():
    mask = np.zeros((9, 9, 9), bool); mask[3, 3, 3] = True; mask[4, 4, 4] = True
    original = mask.copy(); origins, codes, _ = adjacency_locations(mask)
    match = np.flatnonzero(np.all(origins == [3, 3, 3], axis=1))
    assert len(match) == 1 and codes[match[0]] == 129
    assert np.array_equal(mask, original)


def test_diagonal_background_is_also_localized():
    mask = np.zeros((9, 9, 9), bool); mask[2:7, 2:7, 2:7] = True
    mask[3, 3, 3] = False; mask[4, 4, 4] = False
    origins, codes, _ = adjacency_locations(mask)
    index = np.flatnonzero(np.all(origins == [3, 3, 3], axis=1))[0]
    assert codes[index] == 126


def test_source_boundary_is_not_artificially_padded():
    mask = np.zeros((6, 6, 6), bool); mask[0, 3, 3] = True
    with pytest.raises(ValueError, match='touches boundary'):
        adjacency_locations(mask)


def test_label_disagreement_preserves_components_and_slice_counts():
    liver = np.zeros((9, 9, 9), bool); liver[2:5, 2:5, 2:5] = True
    tumour = np.zeros_like(liver); tumour[3, 3, 3] = True; tumour[5, 5, 5] = True; tumour[7, 7, 7] = True
    outside, review = outside_components(liver, tumour)
    assert review['total_outside_tumour_voxels'] == 2
    assert review['components_26'] == review['components_6'] == 2
    assert sum(sum(p['voxels'] for p in c['native_z_planes']) for c in review['components']) == 2
    assert not outside[3, 3, 3] and tumour[3, 3, 3]


def test_matching_masks_need_no_manufactured_disagreement():
    mask = np.zeros((8, 8, 8), bool); mask[2:5, 2:5, 2:5] = True
    _, review = outside_components(mask, mask)
    assert review['components'] == [] and review['total_outside_tumour_voxels'] == 0
