"""Native echo planes must never be flattened into a fictitious denser stack."""
from copy import deepcopy
import pytest

pytest.importorskip('numpy')
from tools.anatomy_sources.review_liver_mri_sequences import partition_echoes, pair_echo_planes


def plane(z, echo=1, te=2.38):
    return {'echo_number': echo, 'echo_time_ms': te, 'orientation_lps': [1, 0, 0, 0, 1, 0],
            'position_lps_mm': [0, 0, z], 'pixel_spacing_mm': [1.125, 1.125], 'rows': 260, 'columns': 320,
            'frame_of_reference_uid': 'source-frame', 'slice_thickness_mm': 7}


def test_repeated_positions_across_echoes_are_separate_gapped_stacks():
    rows = [plane(z, e, te) for z in (0, 8.75, 17.5) for e, te in ((1, 2.38), (2, 4.87))]
    a, b = partition_echoes(list(reversed(rows)))
    assert len(a['records']) == len(b['records']) == 3
    assert a['source_interplane_spacings_mm'] == [8.75, 8.75]
    assert a['source_slice_thicknesses_mm'] == [7]
    assert len(pair_echo_planes(a, b)) == 3


def test_repeated_plane_within_echo_is_rejected():
    with pytest.raises(ValueError, match='Repeated source plane'):
        partition_echoes([plane(0), plane(0)])


@pytest.mark.parametrize('field,value', [('position_lps_mm', [0, 0, .1]), ('frame_of_reference_uid', 'different-frame'),
                                        ('orientation_lps', [0, 1, 0, 1, 0, 0]), ('pixel_spacing_mm', [1, 1])])
def test_echo_pairing_rejects_geometry_or_frame_mismatch(field, value):
    a = partition_echoes([plane(0)])[0]
    b = deepcopy(a); b['records'][0][field] = value
    with pytest.raises(ValueError, match='Echo plane'):
        pair_echo_planes(a, b)


def test_irregular_spacing_is_preserved_instead_of_fitted():
    result = partition_echoes([plane(0), plane(8.75), plane(18)])[0]
    assert result['source_interplane_spacings_mm'] == [8.75, 9.25]
    assert not result['uniform_interplane_spacing']


def test_thick_slab_never_becomes_volume():
    p = plane(0); p['slice_thickness_mm'] = 50
    result = partition_echoes([p])[0]
    assert result['source_interplane_spacings_mm'] == []
    assert not result['single_thick_slab_is_volume']
