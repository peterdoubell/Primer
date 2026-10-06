"""Original gated/non-gated CT, flat renderings and conceptual chart retain distinct provenance."""
import hashlib
import json
from pathlib import Path
from PIL import Image
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail,resolve
from tools.anatomy_sources.acquire_acute_aortic_figures import SELECTION

ROOT=Path(__file__).resolve().parents[1]
FOLDER=ROOT/'docs/acute-aortic-published-source-review'
PREFIX='open-acute-aortic-pmc3505562-fig'

def sha(raw):return hashlib.sha256(raw).hexdigest()

def test_all_original_samples_and_profiles_with_ct_and_schematic_roles_are_preserved():
    main=json.loads((FOLDER/'original-source-review.json').read_text())
    diagram=json.loads((FOLDER/'conceptual-diagram/original-source-review.json').read_text())
    sources={r['figure_number']:r for r in main['figures']+diagram['figures']}
    package=json.loads((FOLDER/'packaged-source-images.json').read_text())
    assert len(main['figures'])==9 and len(diagram['figures'])==1 and len(package['figures'])==10
    assert diagram['figures'][0]['source_modality']=='Schematic'
    assert main['articles'][0]['license']==diagram['articles'][0]['license']=='CC BY 4.0'
    for row in package['figures']:
        source=sources[row['figure_number']];path=ROOT/row['local_path']
        assert sha(path.read_bytes())==row['sha256']==source['sha256']
        if row['figure_number'] in SELECTION:assert (source['pdf_page'],source['pdf_image_index'],source['pdf_object_id'])==SELECTION[row['figure_number']]
        with Image.open(path) as image:
            assert image.mode==source['pixel_mode'] and image.size==(source['width'],source['height'])
            assert sha(image.tobytes())==source['decoded_pixel_sha256']
            assert (sha(image.info['icc_profile']) if image.info.get('icc_profile') else None)==source['source_icc_profile_sha256']
        assert source['original_encoded_stream_or_decoded_pixel_readback_verified'] and not source['source_pixels_changed']
        if source['pixel_mode']=='L':assert sha(path.read_bytes())==source['original_dct_stream_sha256']
    assert not package['clinical_approval'] and not package['model_promoted'] and not package['structure_coverage_granted']

def test_context_retains_acquisition_timing_conflicts_and_flat_rendering_exclusions():
    ref=detail(Curriculum(),resolve('ra.ct-acute-aortic-syndrome'))['radiology_reference']
    rows={r['figure_number']:r for r in ref['structure_atlas'] if r['id'].startswith(PREFIX)}
    assert len(rows)==10 and rows[2]['kind']=='schematic' and rows[2]['modality']=='Schematic'
    assert not rows[2]['clinical_panels'] and rows[2]['source_context']['source_patient_id'] is None
    assert rows[1]['source_context']['panel_gating']=={'a':'non_gated','b':'non_gated','c':'ECG_gated','d':'ECG_gated'}
    assert rows[1]['source_context']['panel_timepoints']['c']=='one_day_later'
    assert rows[5]['source_context']['panel_timepoints']['a']=='visible_artwork_day_2'
    assert rows[5]['source_context']['panel_timepoints']['c']=='visible_artwork_day_7'
    assert 'caption describes 7-day follow-up' in rows[5]['limits']
    assert rows[6]['clinical_panels']==list('abc') and rows[6]['source_context']['source_ct_volume_rendering_panels']==['d']
    assert rows[7]['clinical_panels']==list('ab') and rows[7]['source_context']['source_ct_volume_rendering_panels']==['c']
    assert 'proximal ascending' in rows[7]['limits']
    for row in rows.values():
        for key in ['flat_renderings_are_spatial_geometry','full_acquired_series_included','independent_timepoint_registration_verified',
                    'independent_calibrated_measurements_verified','independent_anatomical_validation_verified','functional_or_outcome_confirmation_verified']:
            assert row['source_context'][key] is False
    assert ref['walkthrough']['start']['images']==[PREFIX+'2']
    assert ref['walkthrough']['start']['module_illustrations'] is False
    assert all(PREFIX+'2' not in s['images'] for s in ref['walkthrough']['steps'])

def test_rights_clearance_keeps_every_anatomical_and_model_requirement_unapproved():
    assets=json.loads((ROOT/'data/radiology/radiology-asset-evidence.json').read_text())['assets']
    rows=[a for a in assets if a['id'].startswith(PREFIX)];assert len(rows)==10
    assert len([a for a in assets if a['id'].startswith('open-aortic-rupture-pmc4035490-fig')])==13
    for row in rows:
        license=row['source']['license'];assert license['commercial_use'] and license['redistribution'] and license['review_status']=='verified'
        assert sha((ROOT/license['evidence_path']).read_bytes())==license['evidence_sha256']
        assert row['anatomical_review']['status']=='pending' and not row['structure_ids'] and not row['requirement_coverage']
