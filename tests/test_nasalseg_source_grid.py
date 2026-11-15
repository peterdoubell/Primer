"""Original NRRD byte order/grid declarations must survive; copied geometry does not approve anatomy."""
import gzip,struct
import pytest
np=pytest.importorskip('numpy');pytest.importorskip('scipy')
from tools.anatomy_sources.review_nasalseg_case import parse
HEADER=b'NRRD0005\ntype: int16\ndimension: 3\nspace: left-posterior-superior\nsizes: 2 3 4\nspace directions: (0.5,0,0) (0,0.5,0) (0,0,1.5)\nendian: little\nencoding: gzip\nspace origin: (-10,-20,-30)\n\n'
def test_original_axis_order_endian_and_LPS_geometry():
    raw=HEADER+gzip.compress(struct.pack('<24h',*range(-12,12)),mtime=0);a,p=parse(raw)
    assert a.shape==(4,3,2) and a[0,0,0]==-12 and a[0,0,1]==-11 and a[1,0,0]==-6
    assert p['source_pitch_mm']==[.5,.5,1.5] and p['declared_LPS_affine'][2]==[0,0,1.5,-30]
    assert p['independently_checked_scalar_samples']==24
@pytest.mark.parametrize('change',[('type: int16','type: float'),('endian: little','endian: big'),('space: left-posterior-superior','space: right-anterior-superior')])
def test_different_source_interpretation_is_not_guessed(change):
    header=HEADER.replace(change[0].encode(),change[1].encode())
    with pytest.raises(ValueError):parse(header+gzip.compress(struct.pack('<24h',*range(24))))
def test_truncated_original_samples_rejected():
    with pytest.raises(ValueError):parse(HEADER+gzip.compress(struct.pack('<23h',*range(23))))
