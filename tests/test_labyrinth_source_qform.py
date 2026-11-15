"""Original qform-only sources must retain signs, sample order and offsets."""
import struct
import pytest
np=pytest.importorskip('numpy');pytest.importorskip('nibabel');pytest.importorskip('scipy')
from tools.anatomy_sources.review_labyrinth_T01_source import read


def source():
    header=bytearray(352);struct.pack_into('<i',header,0,348);struct.pack_into('<8h',header,40,3,2,3,4,0,0,0,0)
    struct.pack_into('<2h',header,70,4,16);struct.pack_into('<8f',header,76,-1,.15,.15,.2,0,0,0,0)
    struct.pack_into('<f',header,108,352);struct.pack_into('<2h',header,252,1,0)
    struct.pack_into('<3f',header,268,10,-20,-30);header[344:348]=b'n+1\0'
    return header+struct.pack('<24h',*range(-12,12))


def test_original_qform_reflection_origin_and_fortran_sample_order():
    values,affine,proof=read(source())
    assert values.shape==(2,3,4) and values[0,0,0]==-12 and values[1,0,0]==-11 and values[0,0,1]==-6
    assert affine[2,2]<0 and affine[:3,3].tolist()==[10,-20,-30]
    assert proof['independent_scalar_samples_checked']==24 and proof['sform_code']==0


@pytest.mark.parametrize('change',['fractional_offset','missing_qform','unexpected_sform','truncated'])
def test_invalid_source_geometry_or_payload_is_not_guessed(change):
    raw=source()
    if change=='fractional_offset':struct.pack_into('<f',raw,108,352.5)
    if change=='missing_qform':struct.pack_into('<h',raw,252,0)
    if change=='unexpected_sform':struct.pack_into('<h',raw,254,1)
    if change=='truncated':raw=raw[:-2]
    with pytest.raises(ValueError):read(raw)
