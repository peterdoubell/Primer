"""N5 decode must preserve endian order and original axis positions without interpreting clinical HU."""
import struct
import pytest
np=pytest.importorskip('numpy')
pytest.importorskip('numcodecs')
from numcodecs import Blosc
from tools.anatomy_sources.acquire_hipct_lung_chunks import decode_n5

def encode(values,shape=(2,3,4)):
    return struct.pack('>HHIII',0,3,*shape)+Blosc().encode(struct.pack('>'+str(len(values))+'H',*values))
def test_every_source_scalar_and_xyz_position_preserved():
    values=list(range(1,25));a,p=decode_n5(encode(values))
    assert a.shape==(4,3,2) and a[0,0,0]==1 and a[0,0,1]==2 and a[0,1,0]==3 and a[1,0,0]==7 and a[3,2,1]==24
    assert p['every_scalar_sample_independently_verified']==24
@pytest.mark.parametrize('header',[b'\0'*15,struct.pack('>HHIII',1,3,2,3,4),struct.pack('>HHIII',0,2,2,3,4),struct.pack('>HHIII',0,3,0,3,4),struct.pack('>HHIII',0,3,129,3,4)])
def test_truncated_variable_rank_or_unsupported_dimensions_rejected(header):
    with pytest.raises(ValueError):decode_n5(header)
def test_source_sample_length_must_match_declared_dimensions():
    with pytest.raises(ValueError):decode_n5(encode(list(range(23))))
