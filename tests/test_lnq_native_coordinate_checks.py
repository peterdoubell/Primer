import pytest

from tools.anatomy_sources.review_lnq_native_case import coordinate_roundtrip_check


def test_exact_source_position_is_not_fitted():
    pytest.importorskip('numpy')
    result = coordinate_roundtrip_check([-229.4, -186.2, -234.5], [-229.4, -186.2, -234.5])
    assert result == {'mode': 'exact_decimal_position', 'max_difference_mm': 0.0}


def test_serialized_float32_position_is_recorded_with_its_actual_error():
    pytest.importorskip('numpy')
    result = coordinate_roundtrip_check([-229.4, -186.2, -234.5], [-229.399994, -186.199997, -234.5])
    assert result['mode'] == 'consistent_with_float32_six_decimal_roundtrip'
    assert result['max_difference_mm'] == pytest.approx(0.000006)
    assert result['quantization_consistency_is_not_proof_of_author_conversion']


@pytest.mark.parametrize('target', [
    [-229.399, -186.2, -234.5],
    [-229.399995, -186.199997, -234.5],
    [-229.399994, -186.199997, -232],
    [float('nan'), -186.2, -234.5],
])
def test_offset_wrong_plane_and_unmatched_roundtrip_are_rejected(target):
    pytest.importorskip('numpy')
    with pytest.raises(ValueError):
        coordinate_roundtrip_check([-229.4, -186.2, -234.5], target)
