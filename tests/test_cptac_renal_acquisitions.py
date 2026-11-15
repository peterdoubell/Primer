from types import SimpleNamespace
import pytest
np=pytest.importorskip('numpy')
from tools.anatomy_sources.review_cptac_renal_geometry import partition_acquisitions


def image(acquisition,z):
    return SimpleNamespace(AcquisitionNumber=acquisition,AcquisitionTime='time'+str(acquisition),ImagePositionPatient=[0,0,z])


def test_overlapping_acquisitions_are_not_deduplicated_or_interleaved():
    ct=[image(a,z) for z in [1.25,0,.625] for a in [1,2]]
    groups=partition_acquisitions(ct,np.array([0,0,1]))
    assert [r['images'] for r in groups]==[3,3]
    assert all(r['observed_interplane_step_mm_min_max']==[.625,.625] for r in groups)
    assert all(not r['phase_identity_verified'] for r in groups)


def test_duplicate_plane_within_acquisition_remains_rejected():
    with pytest.raises(ValueError,match='Repeated plane'):
        partition_acquisitions([image(1,0),image(1,0)],np.array([0,0,1]))


def test_single_acquired_plane_does_not_manufacture_spacing():
    result=partition_acquisitions([image(1,0)],np.array([0,0,1]))[0]
    assert result['observed_interplane_step_mm_min_max'] is None
    assert not result['uniform_interplane_step']
