"""Original source CT stills cannot supply unperformed expiration, whole native anatomy or independent PPF."""
import hashlib,json
from pathlib import Path
from PIL import Image
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail,resolve
from tools.check_msk_fidelity import requirements_for
from tools.anatomy_sources.expand_hrct_fibrosis_requirements import build
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/hrct-fibrosis-published-source-review';PREFIX='open-hrct-fibrosis-pmc11914337-fig'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def test_original_publisher_bytes_and_pixels_keep_exact_original_grant():
    p=json.loads((OUT/'original-source-review.json').read_text());package=json.loads((OUT/'packaged-source-images.json').read_text());original={r['figure_number']:r for r in p['figures']}
    assert set(original)=={1,3,4,5,6,7} and p['original_license']=='CC BY 4.0'
    for r in package['figures']:
        source=original[int(r['id'].removeprefix(PREFIX))];path=ROOT/r['local_path'];assert sha(path.read_bytes())==r['sha256']==source['sha256']
        with Image.open(path) as im:assert (im.width,im.height,im.mode)==(source['width'],source['height'],source['pixel_mode']) and sha(im.tobytes())==source['decoded_pixel_sha256']
    assert not p['clinical_approval'] and not p['structure_coverage_granted'] and not p['model_promoted']
def test_actual_case_patterns_and_chronology_are_not_merged_or_qualified_as_new_tests():
    ref=detail(Curriculum(),resolve('ra.hrct-lung'))['radiology_reference'];rows={r['figure_number']:r for r in ref['structure_atlas'] if r['id'].startswith(PREFIX)}
    assert len(rows)==6 and rows[1]['clinical_panels']==list('abc') and rows[7]['clinical_panels']==list('abcdefghi')
    assert rows[3]['source_context']['source_pattern_groups']=={'UIP':list('ab'),'probable_UIP':list('cd'),'fibrotic_NSIP':list('ef')}
    assert rows[4]['source_context']['source_case_groups']=={'fibrotic_sarcoidosis':list('abc'),'fibrotic_HP':list('def')}
    assert rows[5]['source_context']['source_follow_up_months']==13 and rows[6]['source_context']['source_follow_up_months']==15
    assert rows[7]['source_context']['source_time_groups']['40_days_after_acute_phase']==list('ghi')
    for row in rows.values():assert row['source_context']['actual_expiratory_acquisition_verified'] is False and row['source_context']['quantified_fibrosis_or_physiology_independently_verified'] is False
    assert not ref['key_images'] and all(not s['normal'] for s in ref['walkthrough']['steps'])
    assert 'unperformed expiration' in ref['walkthrough']['steps'][3]['tip']
    assert 'within one year' in ref['walkthrough']['steps'][4]['tip']
def test_rights_and_source_integrity_do_not_approve_structure_bindings():
    rows=[r for r in json.loads((ROOT/'data/radiology/radiology-asset-evidence.json').read_text())['assets'] if r['id'].startswith(PREFIX)];assert len(rows)==6
    for row in rows:
        l=row['source']['license'];assert l['name']=='CC BY 4.0' and l['commercial_use'] and sha((ROOT/l['evidence_path']).read_bytes())==l['evidence_sha256']
        assert row['anatomical_review']['status']=='pending' and not row['structure_ids'] and not row['requirement_coverage']
def test_inventory_covers_lobular_patterns_and_full_actual_site_instantiation():
    item=build();stored=next(i for i in json.loads((ROOT/'data/radiology/non-msk-structure-requirements.json').read_text())['investigations'] if i['investigation_id']=='ra.hrct-lung');assert item==stored
    assert len(item['structures'])==81 and len(requirements_for(item))==609
    ids={s['id'] for s in item['structures']}
    for key in ['right_secondary_lobule','left_secondary_lobule','right_bronchiolocentric_pattern','left_mosaic','right_traction_airway','left_additional_region','oesophagus','cardiovascular_context','acquisition','comparison']:assert 'hrct_lung.'+key in ids
    assert all(s['requires_site_instantiation'] and s['report_refs'] for s in item['structures'])
    ref=detail(Curriculum(),resolve('ra.hrct-lung'))['radiology_reference'];assert ref['reporting']['classification'] is None and 'Partial thoracic orientation' in ref['spatial_model']['reporting_aim']
