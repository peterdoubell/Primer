"""Preserve source-panel, modality, injury and completeness distinctions."""
from pathlib import Path
import copy,hashlib,json
from tools.check_msk_fidelity import inspect_binding,inspect_requirement_coverage,requirements_for
ROOT=Path(__file__).resolve().parents[1]
def records():
    evidence=json.loads((ROOT/'data/radiology/msk-asset-evidence.json').read_text())
    requirements=json.loads((ROOT/'data/radiology/msk-structure-requirements.json').read_text())
    investigation=next(i for i in requirements['investigations'] if i['investigation_id']=='ra.mri-knee')
    return {a['id']:a for a in evidence['assets']},{r['id']:r for r in requirements_for(investigation)}
def test_original_streams_and_uppercase_source_panels_are_preserved():
    from primer import radiology_catalog as catalog
    images=catalog._structure_atlases()['ra.mri-knee']
    for identifier,filename in [('open-knee-semimembranosus-expansions-picasso-s1','supplement-figure-1.jpg'),('open-knee-posterior-oblique-arms-picasso-s4','supplement-figure-4.jpg'),('open-knee-all-meniscotibial-mri-picasso-fig4','article-figure-4.jpg')]:
        image=next(i for i in images if i['id']==identifier);raw=(ROOT/'web'/image['src'].removeprefix('/app/')).read_bytes()
        assert raw==(ROOT/'docs/msk-picasso-knee-source-review'/filename).read_bytes()
        assert hashlib.sha256(raw).hexdigest()==image['sha256']
        assert image['license']=='CC BY 4.0'
    s1=next(i for i in images if i.get('figure_number')=='S1' and 'picasso' in i['id'])
    assert s1['ancillary_panels'][0]['panels']==['B','C']
def test_schematic_candidates_do_not_establish_full_extent_or_mri():
    assets,requirements=records()
    for identifier in ['open-knee-semimembranosus-expansions-picasso-s1','open-knee-posterior-oblique-arms-picasso-s4-schematic-a']:
        asset=assets[identifier];assert asset['kind']=='schematic' and asset['source_context']['selected_panels']==['A']
        assert asset['anatomical_review']['status']=='pending'
        for target in asset['structure_ids']:
            assert not inspect_binding(asset,requirements[target])
            assert inspect_requirement_coverage(asset,requirements[target])==['requirement_coverage_partial']
        changed=copy.deepcopy(asset);changed['kind']='clinical_image';changed['modality']='MRI'
        assert 'source_context_selected_panel_not_clinical_image' in inspect_binding(changed,requirements['knee.posterior_oblique_ligament.course'])
def test_ultrasound_and_dissection_cannot_replace_mri_requirements():
    assets,requirements=records();asset=assets['open-knee-posterior-oblique-arms-picasso-s4']
    assert asset['structure_ids']==[] and asset['modality']=='Ultrasound'
    assert asset['source_context']['selected_panels']==['C','D']
    assert 'clinical_image_modality_not_in_requirement_scope' in inspect_binding(asset,requirements['knee.posterior_oblique_ligament.course'])
    changed=copy.deepcopy(asset);changed['source_context']['selected_panels']=['B'];changed['representation_selection']['panels']=['B']
    assert 'source_context_selected_panel_not_clinical_image' in inspect_binding(changed,requirements['knee.posterior_oblique_ligament.course'])
def test_normal_contralateral_ultrasound_is_not_a_normal_mri_exam():
    assets,_=records();asset=assets['open-knee-all-meniscotibial-mri-picasso-fig4']
    assert asset['structure_ids']==[] and asset['modality']=='MRI'
    assert asset['source_context']['selected_panels']==['B']
    assert asset['source_context']['population']['age_years']==31
    assert asset['source_context']['depicted_state']!='normal_anatomy'
    assert asset['source_context']['panel_types']['C']=='Ultrasound'
    assert 'meniscotibial' in asset['limitations'].lower() and 'not' in asset['limitations'].lower()
