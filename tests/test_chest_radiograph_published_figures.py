"""Original projections and CT comparisons cannot become normality, disease or3D-route proof."""
import copy,hashlib,json
from pathlib import Path
from PIL import Image
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail,resolve
from tools.check_msk_fidelity import inspect_binding
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/chest-radiograph-published-source-review';PREFIX='open-cxr-original-'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def test_all_original_selected_pixels_and_actual_grants_survive_packaging():
    p=json.loads((OUT/'original-source-review.json').read_text());package=json.loads((OUT/'packaged-source-images.json').read_text());original={PREFIX+s['pmcid'].lower()+'-fig'+str(r['figure_number']):r for s in p['sources'] for r in s['figures']}
    assert len(original)==11 and all(s['license']=='CC BY 4.0' for s in p['sources'])
    for row in package['figures']:
        o=original[row['id']];path=ROOT/row['local_path'];assert sha(path.read_bytes())==row['sha256']==o['sha256']
        with Image.open(path) as im:assert (im.width,im.height,im.mode)==(o['width'],o['height'],o['pixel_mode']) and sha(im.tobytes())==o['decoded_pixel_sha256']
    assert len(package['replaced_investigation_images'])==2 and not p['structure_coverage_granted']
def test_roles_and_normal_looking_frontal_views_cannot_claim_missing_anatomy():
    ref=detail(Curriculum(),resolve('ra.chest-radiography'))['radiology_reference'];rows={r['id']:r for r in ref['structure_atlas'] if r['id'].startswith(PREFIX)}
    assert len(rows)==11 and all(r['modality']=='Radiography' for r in rows.values())
    r=rows[PREFIX+'pmc5621990-fig2'];assert r['clinical_panels']==['a','c'] and r['ancillary_panels'][0]['panels']==['b','d']
    assert rows[PREFIX+'pmc5621990-fig6']['source_context']['panel_states']['c']=='normal_appearing_projection'
    assert rows[PREFIX+'pmc5621990-fig9']['source_context']['actual_CT_planes_vs_caption_mismatch']=={'c':'actual_sagittal_caption_axial','d':'actual_axial_caption_sagittal'}
    assert rows[PREFIX+'pmc12679500-fig15']['clinical_panels']==['A'] and not ref['key_images']
    assert all(not s['normal'] for s in ref['walkthrough']['steps'])
def test_normal_appearing_projection_does_not_prove_visible_pathology_or_new_modality():
    rows=[r for r in json.loads((ROOT/'data/radiology/radiology-asset-evidence.json').read_text())['assets'] if r['id'].startswith(PREFIX)];assert len(rows)==11
    for r in rows:
        l=r['source']['license'];assert sha((ROOT/l['evidence_path']).read_bytes())==l['evidence_sha256']
        assert not r['structure_ids'] and not r['requirement_coverage'] and r['anatomical_review']['status']=='pending'
    r=copy.deepcopy(next(r for r in rows if r['id']==PREFIX+'pmc5621990-fig6'));r['source_context']['selected_panels']=['c']
    assert 'source_context_selected_panel_state_mismatch' in inspect_binding(r,{'modality_scope':['Radiography'],'context_requirements':{'purpose':'pathology_example'}})
    assert 'clinical_image_modality_not_in_requirement_scope' in inspect_binding(r,{'modality_scope':['CT']})
def test_unresolved_device_figures_are_retained_as_holds_not_displayed():
    p=json.loads((OUT/'original-source-review.json').read_text());source=next(s for s in p['sources'] if s['pmcid']=='PMC12679500');assert {r['number'] for r in source['held_figures']}=={1,16}
    displayed={r['id'] for r in json.loads((OUT/'packaged-source-images.json').read_text())['figures']}
    assert PREFIX+'pmc12679500-fig1' not in displayed and PREFIX+'pmc12679500-fig16' not in displayed
