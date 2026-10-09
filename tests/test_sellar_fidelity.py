"""Sellar reporting needs fine interfaces; selected clinical stills do not close its anatomy."""
import copy
import hashlib
import json
from pathlib import Path

from PIL import Image
import pytest

from primer.curriculum import Curriculum
from primer.radiology_catalog import detail, resolve, _validate_source_panel_roles
from primer.module_media import radiology_source_bindings
from tools.check_msk_fidelity import requirements_for, audit, validate_reporting_snapshots
from tools.check_radiology_fidelity import digest

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / 'docs/sellar-published-source-review'


def selected():
    return {r['id']:r for r in detail(Curriculum(),resolve('ra.mri-sella'))['radiology_reference']['structure_atlas'] if r['id'].startswith('open-sella-')}


def test_every_new_sellar_component_retains_report_modality_and_unapproved_coverage():
    data = json.loads((ROOT/'data/radiology/non-msk-structure-requirements.json').read_text())
    row = next(r for r in data['investigations'] if r['investigation_id']=='ra.mri-sella')
    ref = detail(Curriculum(),resolve('ra.mri-sella'))['radiology_reference']
    validate_reporting_snapshots({**data,'investigations':[row]},{'ra.mri-sella':ref['reporting']})
    assert row['source_contract_sha256']==digest({k:ref.get(k) for k in ['reporting','report_templates','walkthrough','reading']})
    leaves={r['id']:r for r in requirements_for(row)}
    assert len(leaves)>700 and len(row['structures'])>100
    assert {r['checklist_index'] for s in row['structures'] for r in s['report_refs']}==set(range(5))
    for key in ['sella.adenohypophysis.posterior_lobe_interface','sella.neurohypophysis.source_precontrast_T1_bright_spot',
                'sella.optic_chiasm.nerve_and_tract_junctions','sella.right.cavernous.medial_wall.unresolved_thin_wall_or_compartment_extent',
                'sella.left.neural.VI_abducens.unresolved_fascicles_and_unacquired_extent',
                'sella.right.artery.encountered_superior_hypophyseal_branches.source_origin_endpoints_bends',
                'sella.skull_base.left_sellar_wall.cortex_marrow_air_mucosa_or_other_actual_components',
                'sella.treatment.actual_graft_flap_or_packing.source_internal_external_interfaces']:
        assert key in leaves
    result=audit({**data,'investigations':[row],'scope':{'catalog_investigation_ids':['ra.mri-sella']}},
        {'assets':[{'id':'whole-pituitary','kind':'model','structure_ids':['sella.gland'],'investigation_ids':['ra.mri-sella']}]},expected_catalog_ids={'ra.mri-sella'})
    assert result['counts']['missing']==len(leaves)*3


def test_twenty_complete_source_masters_reach_reader_and_lesson_with_exact_samples():
    figures=selected();proof=json.loads((REVIEW/'original-source-review.json').read_text())
    assert len(figures)==len(proof['figures'])==20
    assert 'ra.mri-sella' in radiology_source_bindings()['rad.5.sella']
    for source in proof['figures']:
        row=figures['open-sella-'+source['pmcid'].lower()+'-fig'+str(source['figure_number'])]
        raw=(ROOT/'web'/row['src'].removeprefix('/app/')).read_bytes()
        assert hashlib.sha256(raw).hexdigest()==source['sha256']==row['sha256']
        with Image.open(ROOT/'web'/row['src'].removeprefix('/app/')) as image:
            image.load();assert image.mode=='L' and image.size==(source['width'],source['height'])
            assert hashlib.sha256(image.tobytes()).hexdigest()==source['decoded_pixel_sha256']
        assert source['original_DCT_stream_independent_Poppler_byte_exact'] and source['all_panels_preserved']
        assert not source['source_pixels_changed']
        assert row['license']=='CC BY 4.0'
        _validate_source_panel_roles(row)


def test_source_case_sequence_age_comparison_and_ct_roles_remain_separate():
    figures=selected();p1=lambda n:figures['open-sella-pmc10366012-fig'+str(n)];p2=lambda n:figures['open-sella-pmc10366287-fig'+str(n)]
    assert p1(3)['source_context']['source_dynamic_time_seconds']==90
    assert p1(3)['source_context']['population']['life_stage']=='child'
    assert p1(7)['ancillary_panels'][0]['panels']==['a']
    for n,panels in {1:['e'],2:['d'],3:['d'],4:['f'],5:['a'],6:['a'],13:['a']}.items():
        assert p2(n)['ancillary_panels'][0]['kind']=='CT' and p2(n)['ancillary_panels'][0]['panels']==panels
        assert not set(panels).intersection(p2(n)['clinical_panels'])
    assert p1(5)['source_context']['source_caption_correction']=='10.1007/s11604-023-01414-1'
    assert 'hyperintensity anteriorly and mildly hypointensity posteriorly' in p1(5)['source_caption_full']
    assert 'unresolved wording is not adopted as procedural advice' in p1(6)['caption']
    for row,months in [(p1(9),24),(p2(9),3),(p2(10),120)]:
        assert row['source_context']['source_followup_months']==months
        assert not row['source_context']['independent_timepoint_registration_verified']
    assert 'attained age not separately stated' in p2(10)['source_context']['panel_population_context']['c']
    assert 'MRA' in p2(13)['source_context']['panel_processing']['e']
    wrong=copy.deepcopy(p1(7));wrong['source_context']['panel_types']['a']='MRI'
    with pytest.raises(ValueError,match='ancillary panel roles'):_validate_source_panel_roles(wrong)
    for row in figures.values():
        assert not row['source_context']['different_figures_assumed_same_patient']
        assert not row['source_context']['source_panels_independently_registered']


def test_original_images_do_not_grant_anatomical_or_three_dimensional_approval():
    proof=json.loads((REVIEW/'original-source-review.json').read_text())
    assert proof['separate_credit_holds']=={'PMC10366012':[1,2,10]}
    assert not proof['clinical_approval'] and not proof['every_sellar_structure_approved']
    assert not proof['native_3D_model_created']
    assets=json.loads((ROOT/'data/radiology/radiology-asset-evidence.json').read_text())['assets']
    rows=[a for a in assets if a['id'].startswith('open-sella-')];assert len(rows)==20
    for row in rows:
        assert row['structure_ids']==[] and row['requirement_coverage']=={} and row['anatomical_review']['status']=='pending'
        license=row['source']['license'];assert license['commercial_use'] and license['redistribution']
        assert hashlib.sha256((ROOT/license['evidence_path']).read_bytes()).hexdigest()==license['evidence_sha256']


def test_reporting_starts_cannot_assert_unassessed_normality_and_every_source_is_bound():
    ref=detail(Curriculum(),resolve('ra.mri-sella'))['radiology_reference'];steps=ref['walkthrough']['steps']
    assert len(steps)==5
    forbidden=['Normal pituitary gland; no focal lesion','Stalk midline and normal in thickness',
        'posterior pituitary bright spot present','Optic chiasm clear','No cavernous sinus invasion',
        'sellar floor intact; no vascular lesion']
    for step in steps:
        normal=step.get('normal',{})
        text=' '.join(normal.values()) if isinstance(normal,dict) else str(normal)
        assert not any(claim in text for claim in forbidden)
        if text:
            assert '[__]' in text
            assert any(term in text.lower() for term in ['adequacy','coverage','unassessed','unresolved'])
    all_bindings={ident for step in steps for ident in step['images'] if ident.startswith('open-sella-')}
    assert all_bindings==set(selected())
    assert 'does not delineate' in steps[0]['anatomy_note']
    assert 'single timed publication panel cannot reconstruct enhancement kinetics' in steps[0]['look']
    assert 'T1 brightness alone does not prove haemorrhage' in steps[1]['tip']
    assert 'visual function remain distinct' in steps[3]['tip']
    assert 'Knosp imaging extent does not prove microscopic' in steps[4]['tip']
    assert 'flow void alone neither confirms nor excludes an aneurysm' in steps[4]['tip']


def test_uncleared_legacy_thumbnails_are_held_with_complete_original_source_records():
    held=json.loads((REVIEW/'legacy-key-images-held.json').read_text())
    identifiers={f'sella-image-{n}' for n in [1,2,3]}
    assert set(held['source_records'])==identifiers
    # These identities were independently matched to the immutable pre-change
    # source pool/guide. They must remain stable after the current branch merges.
    assert digest(held['source_records'])=='2622c2aab988a206f75d87db00281fbdf690a955cb4c8f4d78f445caac3b25c8'
    assert digest(held['source_slot_metadata'])=='73ef174bfb1dc8f0d14efcbb85371125f5748ab3760d7f38dd69532008b58449'
    assert held['display_status']=='held_not_delivered' and not held['clinical_or_anatomical_approval']
    current_pool=json.loads((ROOT/'data/radiology/key-images-neuro-msk.json').read_text())
    current_guide=json.loads((ROOT/'data/radiology/module-guides.json').read_text())
    assert not identifiers.intersection(current_pool)
    assert current_guide['rad.5.sella']['key_images']==[]
    ref=detail(Curriculum(),resolve('ra.mri-sella'))['radiology_reference']
    assert ref['key_images']==[]
    assert not identifiers.intersection(i for step in ref['walkthrough']['steps'] for i in step['images'])
    assert set(held['replacement_figure_ids'])==set(selected())
