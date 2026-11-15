"""Published snapshots do not become whole tumour volumes, registered response or prognostic proof."""
import hashlib
import json
from pathlib import Path
from PIL import Image
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail,resolve

ROOT=Path(__file__).resolve().parents[1]
REVIEW=ROOT/'docs/anal-mri-published-source-review'
IDENT='open-anal-mri-pmc10784345-fig2'


def test_original_published_samples_and_profile_are_preserved():
    proof=json.loads((REVIEW/'original-source-review.json').read_text());source=proof['figures'][0]
    assert len(proof['figures'])==1 and proof['articles'][0]['license']=='CC BY 4.0'
    assert (source['figure_number'],source['pdf_page'],source['pdf_object_id'])==(2,6,65)
    row=json.loads((REVIEW/'packaged-source-images.json').read_text())['figures'][0]
    p=ROOT/row['local_path'];assert hashlib.sha256(p.read_bytes()).hexdigest()==row['sha256']==source['sha256']
    with Image.open(p) as im:
        assert im.size==(1016,875) and im.mode=='RGB'
        assert hashlib.sha256(im.tobytes()).hexdigest()==source['decoded_pixel_sha256']
        assert hashlib.sha256(im.info['icc_profile']).hexdigest()==source['source_icc_profile_sha256']
    assert source['original_encoded_stream_or_decoded_pixel_readback_verified'] and not source['source_pixels_changed']


def test_runtime_figure_preserves_separate_patients_timepoints_and_scope():
    ref=detail(Curriculum(),resolve('ra.mri-anal-cancer'))['radiology_reference']
    row=next(r for r in ref['structure_atlas'] if r['id']==IDENT);c=row['source_context']
    assert row['modality']=='MRI' and row['clinical_panels']==list('abcd')
    assert c['panel_types']==dict.fromkeys('abcd','MRI') and c['panel_sequences']==dict.fromkeys('abcd','axial T2')
    assert c['separate_patient_pairs']==[['a','b'],['c','d']]
    assert c['panel_timepoints']=={'a':'baseline','b':'week_2','c':'baseline','d':'week_2'}
    for key in ['independent_timepoint_registration_verified','full_volumetric_series_or_masks_included',
                'response_or_recurrence_prediction_verified','full_sphincter_or_organ_invasion_map_verified','spatial_3d_tumour_derived']:
        assert not c[key]
    assert IDENT in ref['walkthrough']['steps'][0]['images']
    assert all(IDENT not in s['images'] for s in ref['walkthrough']['steps'][1:])


def test_figure_rights_do_not_grant_complete_anatomical_or_model_coverage():
    rows=json.loads((ROOT/'data/radiology/radiology-asset-evidence.json').read_text())['assets']
    row=next(r for r in rows if r['id']==IDENT);rights=row['source']['license']
    assert rights['commercial_use'] and rights['redistribution'] and rights['review_status']=='verified'
    assert hashlib.sha256((ROOT/rights['evidence_path']).read_bytes()).hexdigest()==rights['evidence_sha256']
    assert row['anatomical_review']['status']=='pending' and not row['structure_ids'] and not row['requirement_coverage']
    assert not row['pixel_provenance']['highest_resolution_acquired_master_verified']
