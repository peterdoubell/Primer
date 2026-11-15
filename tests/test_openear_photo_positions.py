"""Nearest source slots cannot silently discard collisions or invent photographic planes."""
import pytest
np=pytest.importorskip('numpy')
from tools.anatomy_sources.review_openear_ZETA_photographs import nearest_source_slots


def test_both_original_photos_in_same_nearest_slot_are_retained():
    positions=np.array([0,.149,.151,.45])
    slots=nearest_source_slots(positions,.15,4)
    assert slots.tolist()==[0,1,1,3] and len(slots)==len(positions)
    assert 2 not in slots


@pytest.mark.parametrize('positions',[[0,-.15],[0,float('nan')],[0,1.5]])
def test_invalid_unordered_or_outside_positions_are_not_clamped(positions):
    with pytest.raises(ValueError):nearest_source_slots(positions,.15,4)
