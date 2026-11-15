"""Historical evidence is restored only through the exact reviewed integration."""
import copy
from pathlib import Path
import pytest
from tools import algebra_openear_runtime_compatibility as bridge
from tools.coordinate_plane_runtime_compatibility import before_coordinate_plane_bytes
ROOT=Path(__file__).resolve().parents[1]

@pytest.mark.parametrize('path',sorted(bridge.PATHS))
def test_exact_current_delta_and_foreign_drift(path):
    raw=(ROOT/path).read_bytes();row=bridge.reviewed()['files'][path]
    assert bridge.sha(before_coordinate_plane_bytes(path,raw))==row['after_sha256']
    before=bridge.before_algebra_openear_bytes(path,raw)
    assert bridge.sha(before)==row['before_sha256']
    assert bridge.before_algebra_openear_bytes(path,before)==before
    with pytest.raises(ValueError,match='Unreviewed'):bridge.before_algebra_openear_bytes(path,raw+b'\nforeign\n')
    assert bridge.before_algebra_openear_bytes('unrelated',b'exact')==b'exact'

@pytest.mark.parametrize('identifier',['ra.ct-temporal-bone','ra.tinnitus'])
def test_inspector_removal_keeps_other_evidence(identifier):
    item=bridge.reviewed()['added_inspector'];fields={'source_native_inspectors':[{'id':'other'},item],'observation':'retained'}
    assert bridge.before_algebra_openear_reference_fields(identifier,fields)=={'source_native_inspectors':[{'id':'other'}],'observation':'retained'}
    assert len(fields['source_native_inspectors'])==2
    assert bridge.before_algebra_openear_reference_fields(identifier,{'source_native_inspectors':[item]})=={}
    altered=copy.deepcopy(fields);altered['source_native_inspectors'][1]['clinical_approval']=True
    with pytest.raises(ValueError,match='Unreviewed'):bridge.before_algebra_openear_reference_fields(identifier,altered)
    with pytest.raises(ValueError,match='Unreviewed'):bridge.before_algebra_openear_reference_fields('ra.brain-anatomy',fields)

@pytest.mark.parametrize('identifier',['rad.5.temporal-bone','rad.5.tinnitus'])
def test_exact_lesson_wrapper_only(identifier):
    item=bridge.reviewed()['lessons'][identifier]['added_media'];fields={'lesson_media':[{'id':'unrelated'},item],'quiz':['unchanged']}
    assert bridge.before_algebra_openear_lesson_fields(identifier,fields)=={'lesson_media':[{'id':'unrelated'}],'quiz':['unchanged']}
    changed=copy.deepcopy(fields);changed['lesson_media'][1]['instructions']='incorrectly upgraded approval'
    with pytest.raises(ValueError,match='Unreviewed'):bridge.before_algebra_openear_lesson_fields(identifier,changed)
