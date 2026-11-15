"""The AAA reference must expose original schematic panels without borrowing its module's AAS overview."""
import copy
import pytest
from primer.curriculum import Curriculum
from primer import radiology_catalog as catalog

IDENT='ra.aortic-aneurysm-rupture'
PREFIX='open-aortic-rupture-pmc4035490-fig'


def reference():return catalog.detail(Curriculum(),catalog.resolve(IDENT))['radiology_reference']


def test_original_schematic_panels_are_visible_to_the_diagram_selector():
    rows=[r for r in reference()['structure_atlas'] if r['id'].startswith(PREFIX)]
    assert len(rows)==13
    assert {r['figure_number'] for r in rows if r['contains_schematic_panels']}=={2,3,4,5,6,11}
    for r in rows:
        assert r['contains_schematic_panels']==r['source_context']['contains_schematic_panels']
        if r['contains_schematic_panels']:
            assert r['source_context']['panel_types']['a']=='Schematic'
            assert 'a' not in r['clinical_panels'] and r['schematic_structures_visible']


def test_aaa_overview_uses_registered_source_artwork_and_qualifies_generic_model():
    ref=reference();start=ref['walkthrough']['start']
    assert start['module_illustrations'] is False and start['images']==[PREFIX+'11',PREFIX+'3']
    assert all(i in {r['id'] for r in ref['structure_atlas']} for i in start['images'])
    for model in (ref['spatial_model'],ref['walkthrough']['spatial_model']):
        assert model['family']=='aorta'
        assert 'general orientation only' in model['reporting_aim']
        assert 'every branch' in model['reporting_aim'] and 'independent validation' in model['reporting_aim']


@pytest.mark.parametrize('bad',[{'images':['unregistered-figure']},
                               {'images':[PREFIX+'11',PREFIX+'11']},
                               {'images':PREFIX+'11'},
                               {'module_illustrations':'false'},[]])
def test_invalid_introduction_configuration_is_rejected(monkeypatch,bad):
    item=catalog.resolve(IDENT);ref=reference();authored=copy.deepcopy(catalog._steps()['investigations'][IDENT])
    authored['start']=bad
    monkeypatch.setattr(catalog,'_steps',lambda:{'investigations':{IDENT:authored},'reviewed_at':{IDENT:'2026-10-06'}})
    with pytest.raises(ValueError,match='introduction'):catalog._walkthrough(item,ref)


def test_other_investigations_keep_their_existing_module_illustration_default():
    ref=catalog.detail(Curriculum(),catalog.resolve('ra.mri-anal-cancer'))['radiology_reference']
    assert 'module_illustrations' not in ref['walkthrough']['start']
