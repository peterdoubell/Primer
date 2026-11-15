import pytest
from tools.anatomy_sources.review_cptac_pancreatic_geometry import time_seconds


def test_recorded_time_difference_does_not_need_or_invent_injection_timing():
    delta=time_seconds('114147.324919')-time_seconds('114104.584535')
    assert delta==pytest.approx(42.740384)


@pytest.mark.parametrize('value',['1141','246000','116000','114160','badtime'])
def test_incomplete_or_invalid_dicom_time_is_not_silently_filled(value):
    with pytest.raises(ValueError):time_seconds(value)
