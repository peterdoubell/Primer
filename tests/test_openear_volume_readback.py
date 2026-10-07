"""Retain original vector/list axes and reconcile declared frames without changing samples."""
import gzip
import pytest
np=pytest.importorskip('numpy')
from tools.anatomy_sources.decode_openear_ZETA_volumes import decode


def test_three_channel_vector_bytes_and_RAS_equivalent_mapping(tmp_path):
    source=tmp_path/'source.nrrd';raw=bytes(range(24))
    head=b'NRRD0004\ntype: unsigned char\ndimension: 4\nspace: left-posterior-superior\nsizes: 3 2 2 2\nspace directions: none (-0.05,0,0) (0,-0.05,0) (0,0,0.15)\nkinds: vector domain domain domain\nencoding: gzip\nspace origin: (0,0,0)\n\n'
    source.write_bytes(head+gzip.compress(raw,mtime=0));array,proof,fields=decode(source,tmp_path/'decoded.raw')
    assert array.shape==(2,2,2,3) and array[0,0,0].tolist()==[0,1,2] and array[0,0,1].tolist()==[3,4,5]
    assert proof['equivalent_RAS_affine'][0][0]==.05 and proof['equivalent_RAS_affine'][1][1]==.05
    assert (tmp_path/'decoded.raw').read_bytes()==raw and proof['all_decoded_bytes_match_independent_stream_and_written_readback']


def test_short_scalar_payload_not_accepted_as_complete_volume(tmp_path):
    source=tmp_path/'source.nrrd'
    head=b'NRRD0004\ntype: short\ndimension: 3\nspace: right-anterior-superior\nsizes: 2 2 2\nspace directions: (1,0,0) (0,1,0) (0,0,1)\nkinds: domain domain domain\nendian: little\nencoding: gzip\nspace origin: (0,0,0)\n\n'
    source.write_bytes(head+gzip.compress(b'\0'*14,mtime=0))
    with pytest.raises(ValueError,match='count'):decode(source,tmp_path/'decoded.raw')


def test_colour_support_preserves_outside_and_nonfinite_points_without_clamping():
    from tools.anatomy_sources.review_openear_colour_support import support
    points=np.array([[0,0,0],[1,1,1],[-.01,0,0],[1.01,0,0],[np.nan,0,0]])
    assert support(points,np.eye(4),[2,2,2]).tolist()==[True,True,False,False,False]
