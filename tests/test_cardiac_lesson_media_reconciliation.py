"""Independent lesson images replace remote media without rewriting report-slot/patient identity."""
import hashlib,json
from pathlib import Path
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail,resolve
from tools.msk_runtime_rights import license_issues
ROOT=Path(__file__).resolve().parents[1];MODULE='rad.5.cardiac-masses-devices'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def test_lesson_slot_identity_and_original_source_pixels_are_preserved():
    n=Curriculum().node(MODULE);ref=n['radiology_reference'];authored=json.loads((ROOT/'data/radiology/module-guides.json').read_text())[MODULE]['key_images'];images=ref['key_images'];assert len(images)==3
    assert [(r['id'],r['label'],r['description']) for r in images]==[(r['id'],r['label'],r['description']) for r in authored]
    proof=json.loads((ROOT/'docs/cardiac-lesson-media-review/original-slot-reconciliation.json').read_text());assert all(r['previous_asset']['src'].startswith('https://radiologyassistant.nl/') for r in proof['slots'])
    assert not proof['patient_findings_prefilled'] and not proof['cases_registered_together'] and not proof['full_curriculum_scope_reconciled']
    catalog=json.loads((ROOT/'data/radiology/radiology-open-images.json').read_text());sources={r['id']:r for rows in catalog.values() for r in rows};registry=json.loads((ROOT/'data/radiology/local-source-figures.json').read_text())
    for image,record in zip(images,proof['slots']):
        source=sources[record['source_figure_id']];path=ROOT/'web'/image['src'].removeprefix('/app/')
        assert path.read_bytes()==(ROOT/'web'/source['src'].removeprefix('/app/')).read_bytes()
        assert sha(path.read_bytes())==record['sha256']==image['sha256']==registry[image['src']]['sha256']
        assert image['clinical_panels']==source['clinical_panels'] and image['source_context']==source['source_context']
        assert 'does not supply findings' in image['caption'] and 'No registration between' in image['caption']
def test_lesson_rights_and_sources_do_not_grant_whole_module_approval():
    a=json.loads((ROOT/'data/radiology/radiology-asset-evidence.json').read_text())['assets'];assets=[r for r in a if r['id'].startswith('cardiac-lesson-slot-')];assert len(assets)==3
    for asset in assets:
        assert not license_issues(asset,ROOT) and not asset['structure_ids'] and not asset['requirement_coverage'] and asset['anatomical_review']['status']=='pending'
    ref=Curriculum().node(MODULE)['radiology_reference'];urls={r['url'] for r in ref['additional_sources']}
    assert {'https://pmc.ncbi.nlm.nih.gov/articles/PMC10818366/','https://pmc.ncbi.nlm.nih.gov/articles/PMC10350447/'}.issubset(urls)
    assert json.loads((ROOT/'docs/cardiac-lesson-media-review/original-slot-reconciliation.json').read_text())['clinical_approval'] is False
def test_investigation_scopes_and_archived_legacy_replacement_are_preserved():
    c=Curriculum()
    for id,count in [('ra.cardiac-masses',38),('ra.cardiovascular-devices',43)]:
        ref=detail(c,resolve(id))['radiology_reference'];assert ref['key_images']==[] and len(ref['structure_atlas'])==count
    pack=json.loads((ROOT/'docs/cardiac-mimic-published-source-review/packaged-source-images.json').read_text())
    assert len(pack['replaced_unverified_investigation_images'])==3 and all(r['src'].startswith('https://radiologyassistant.nl/') for r in pack['replaced_unverified_investigation_images'])
