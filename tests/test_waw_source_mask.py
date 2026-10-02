import gzip
import pytest
from tools.anatomy_sources.review_waw_tace_mask import decode_mask


def source():
    np=pytest.importorskip('numpy')
    values=np.zeros((3,2,4),dtype='<i2');values[2,1,3]=1
    text='NRRD0004\ntype: short\ndimension: 3\nspace: left-posterior-superior\nsizes: 3 2 4\nspace directions: (0.7,0,0) (0,-0.7,0) (0,0,2.5)\nendian: little\nencoding: gzip\nspace origin: (-10,20,-30)\n\n'
    return text.encode()+gzip.compress(values.tobytes(order='F')),values


def test_nrrd_fast_axis_order_and_declared_directions_are_preserved():
    np=pytest.importorskip('numpy');data,expected=source()
    values,affine,fields=decode_mask(data)
    np.testing.assert_array_equal(values,expected)
    np.testing.assert_allclose(affine[:3,:3],np.diag([.7,-.7,2.5]))
    np.testing.assert_array_equal(affine[:3,3],[-10,20,-30])


@pytest.mark.parametrize('change',['byte_count','unsupported_space','repeated_header'])
def test_incomplete_or_unsupported_source_data_is_rejected(change):
    data,_=source();head,payload=data.split(b'\n\n',1)
    if change=='byte_count':payload=gzip.compress(b'\0\0')
    elif change=='unsupported_space':head=head.replace(b'left-posterior-superior',b'unknown-space')
    else:head+=b'\ntype: short'
    with pytest.raises(ValueError):decode_mask(head+b'\n\n'+payload)
