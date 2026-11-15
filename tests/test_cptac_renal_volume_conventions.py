import pytest
np=pytest.importorskip('numpy')
from tools.anatomy_sources.review_cptac_renal_end_extent import volume_candidates


def test_constant_area_has_distinct_explicit_endpoint_conventions():
    rows=volume_candidates([0,1,2],[10,10,10],[10,10,10],.02)
    assert rows[0]['volume_mm3']==20
    assert rows[1]['volume_mm3']==rows[2]['volume_mm3']==30
    assert rows[0]['difference_from_recorded_cm3']==0
    assert rows[1]['relative_difference_percent']==pytest.approx(50)
    assert all(not r['is_original_author_volume_method'] and not r['is_clinical_volume_validation'] for r in rows)


def test_raster_area_change_remains_separate_from_continuous_polygon_area():
    rows=volume_candidates([0,.625,1.25],[10,20,10],[9,18,9],.02)
    assert rows[0]['volume_mm3']==18.75
    assert rows[1]['volume_mm3']==25
    assert rows[2]['volume_mm3']==22.5


@pytest.mark.parametrize('z',[[0,0,1],[0,1,2.5],[2,1,0]])
def test_source_spacing_cannot_be_fitted_to_a_desired_volume(z):
    with pytest.raises(ValueError,match='Nonuniform or repeated'):
        volume_candidates(z,[10,10,10],[10,10,10],.02)
