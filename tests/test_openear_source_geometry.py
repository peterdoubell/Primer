"""Source binary topology and Slicer layered declarations must not be guessed or repaired."""
import io,struct
import pytest
np=pytest.importorskip('numpy')
from tools.anatomy_sources.review_openear_ZETA_geometry import ply,header
HEAD=b'ply\nformat binary_little_endian 1.0\nelement vertex 3\nproperty float x\nproperty float y\nproperty float z\nelement face 1\nproperty list uchar int vertex_indices\nend_header\n'


def test_binary_positions_and_face_order_retained_including_degenerate_source():
    raw=HEAD+struct.pack('<9f',0,0,0,1,0,0,2,0,0)+struct.pack('<B3i',3,0,1,2)
    vertices,faces,proof=ply(raw)
    assert vertices.tolist()==[[0,0,0],[1,0,0],[2,0,0]] and faces.tolist()==[[0,1,2]]
    assert proof['zero_area_triangles']==1 and proof['new_smoothing_repair_decimation_or_component_deletion'] is False


@pytest.mark.parametrize('face',[(4,0,1,2),(3,-1,1,2),(3,0,1,3)])
def test_nontriangular_or_out_of_bounds_original_faces_rejected(face):
    raw=HEAD+struct.pack('<9f',*range(9))+struct.pack('<B3i',*face)
    with pytest.raises(ValueError):ply(raw)


def test_slicer_metadata_delimiter_and_original_list_axis_preserved():
    raw=b'NRRD0005\ntype: unsigned char\ndimension: 4\nsizes: 13 641 579 475\nkinds: list domain domain domain\nSegment0_Name:=Scala Tympani\nSegment0_Layer:=0\nSegment0_LabelValue:=1\n\npayload'
    original,fields=header(io.BytesIO(raw))
    assert fields['Segment0_Name']=='Scala Tympani' and fields['Segment0_Layer']=='0'
    assert fields['sizes']=='13 641 579 475' and 'Segment0_Name:=Scala Tympani' in original
