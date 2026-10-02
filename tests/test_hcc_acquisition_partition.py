from types import SimpleNamespace
import pytest
from tools.anatomy_sources.audit_hcc_source_acquisitions import acquisition_groups


def image(acquisition,z,sop):
    return SimpleNamespace(AcquisitionNumber=acquisition,ImagePositionPatient=[0,0,z],SOPInstanceUID=sop)


def test_same_positions_from_different_acquisitions_remain_separate():
    rows=[image(1,2,'a2'),image(2,0,'b0'),image(1,0,'a0'),image(2,2,'b2')]
    result=acquisition_groups(rows)
    assert set(result)=={'1','2'}
    assert [x.SOPInstanceUID for x in result['1']]==['a0','a2']
    assert [x.SOPInstanceUID for x in result['2']]==['b0','b2']


def test_repeated_positions_within_acquisition_do_not_get_collapsed():
    with pytest.raises(ValueError,match='Repeated positions'):
        acquisition_groups([image(1,0,'a'),image(1,0,'b')])


def test_missing_acquisition_metadata_is_not_guessed_from_source_order():
    with pytest.raises(ValueError,match='Missing acquisition'):
        acquisition_groups([SimpleNamespace(ImagePositionPatient=[0,0,0],SOPInstanceUID='a')])
