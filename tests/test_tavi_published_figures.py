"""Original annotated snapshots and historical caption cutoffs cannot become patient simulations."""
import hashlib
import json
from pathlib import Path
from PIL import Image
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail,resolve

ROOT=Path(__file__).resolve().parents[1]
FOLDER=ROOT/'docs/tavi-published-source-review'
PREFIX='open-tavi-pmc9743261-fig'

def sha(raw):return hashlib.sha256(raw).hexdigest()

def test_eight_complete_original_jpegs_preserve_all_pixels_and_annotations():
    p=json.loads((FOLDER/'original-source-review.json').read_text());package=json.loads((FOLDER/'packaged-source-images.json').read_text())
    assert p['original_license']=='CC BY 4.0' and len(p['figures'])==len(package['figures'])==8
    for source,row in zip(p['figures'],package['figures']):
        path=ROOT/row['local_path'];assert sha(path.read_bytes())==source['sha256']==row['sha256']
        with Image.open(path) as im:
            assert im.size==(source['width'],source['height']) and im.mode==source['pixel_mode']
            assert sha(im.tobytes())==source['decoded_pixel_sha256']
        assert source['publisher_md5_verified'] and not source['source_pixels_changed']
    assert not package['clinical_approval'] and not package['structure_coverage_granted'] and not package['model_promoted']

def test_chart_CT_panels_and_source_cutoff_limits_are_distinct():
    ref=detail(Curriculum(),resolve('ra.ct-tavi'))['radiology_reference'];rows={r['figure_number']:r for r in ref['structure_atlas'] if r['id'].startswith(PREFIX)}
    assert len(rows)==8 and rows[1]['kind']=='schematic' and rows[1]['modality']=='Schematic' and not rows[1]['clinical_panels']
    assert rows[3]['clinical_panels']==['A','B'] and 'separate bicuspid/tricuspid' in rows[3]['limits']
    assert rows[4]['source_context']['laterality']=='right' and 'not a universal' in rows[4]['limits']
    assert 'maximum sinus-to-sinus surveillance' in rows[5]['limits'] and 'not a universal' in rows[5]['limits']
    assert ref['walkthrough']['start']['images']==[PREFIX+'1'] and ref['walkthrough']['start']['module_illustrations'] is False
    assert not any(i.startswith(PREFIX) for i in ref['walkthrough']['steps'][4]['images'])
    for row in rows.values():
        for key in ['cross_figure_patient_identity_verified','full_acquired_series_included','independent_calibrated_measurements_verified',
                    'complete_device_simulation_or_suitability_verified','independent_anatomical_review_verified']:
            assert row['source_context'][key] is False

def test_licensed_source_rights_preserve_unapproved_anatomy_and_device_scope():
    assets=json.loads((ROOT/'data/radiology/radiology-asset-evidence.json').read_text())['assets'];rows=[r for r in assets if r['id'].startswith(PREFIX)]
    assert len(rows)==8
    for row in rows:
        licence=row['source']['license'];assert licence['commercial_use'] and licence['redistribution'] and licence['review_status']=='verified'
        assert sha((ROOT/licence['evidence_path']).read_bytes())==licence['evidence_sha256']
        assert row['anatomical_review']['status']=='pending' and not row['structure_ids'] and not row['requirement_coverage']
