"""Original reconstructed samples may interpolate, but never clamp/extrapolate missing anatomy."""
import pytest
np=pytest.importorskip('numpy');pytest.importorskip('scipy')
from tools.anatomy_sources.prepare_openear_ZETA_colour_samples import sample


def test_trilinear_RGB_uses_source_channels_and_preserves_missing_domain():
    volume=np.zeros((2,2,2,3),dtype=np.uint8)
    volume[:,:,:,0]=np.array([0,100])[None,None,:]
    volume[:,:,:,1]=np.array([20,60])[None,:,None]
    volume[:,:,:,2]=np.array([40,80])[:,None,None]
    vertices=np.array([[.5,.5,.5],[-.01,0,0],[1,1,1],[1.01,1,1]])
    colors,valid=sample(volume,vertices,np.eye(4))
    assert colors.tolist()==[[50,40,60],[128,128,128],[100,60,80],[128,128,128]]
    assert valid.tolist()==[True,False,True,False]


def test_unknown_non_RGB_volume_is_not_interpreted_as_photographic_colour():
    with pytest.raises(ValueError):sample(np.zeros((2,2,2),dtype=np.uint8),np.zeros((1,3)),np.eye(4))


def test_faces_crossing_missing_colour_bounds_require_whole_face_neutral_display():
    volume=np.zeros((2,2,2,3),dtype=np.uint8);vertices=np.array([[0,0,0],[1,0,0],[0,1,0],[-.01,0,0]])
    colors,valid=sample(volume,vertices,np.eye(4));faces=np.array([[0,1,2],[0,2,3]])
    assert valid[faces].all(axis=1).tolist()==[True,False]
