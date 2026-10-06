"""Original artwork, independent readback and mixed panel roles cannot imply whole CT/model coverage."""
import hashlib
import json
from pathlib import Path
import shutil
import pytest
from PIL import Image
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail,resolve
from tools.anatomy_sources.acquire_aortic_rupture_figures import SELECTION
from tools.anatomy_sources.acquire_hernia_valsalva_figures import acquire,verify_flate_readback

ROOT=Path(__file__).resolve().parents[1]
FOLDER=ROOT/'docs/aortic-rupture-published-source-review'
PREFIX='open-aortic-rupture-pmc4035490-fig'


def sha(raw):return hashlib.sha256(raw).hexdigest()


def test_all_original_samples_profiles_and_object_placements_are_preserved():
    proof=json.loads((FOLDER/'original-source-review.json').read_text())
    packaged=json.loads((FOLDER/'packaged-source-images.json').read_text())
    assert proof['articles'][0]['license']=='CC BY 4.0' and len(proof['figures'])==len(packaged['figures'])==13
    for source,row in zip(proof['figures'],packaged['figures']):
        assert (source['pdf_page'],source['pdf_image_index'],source['pdf_object_id'])==SELECTION[source['figure_number']]
        raw=(ROOT/row['local_path']).read_bytes();assert sha(raw)==row['sha256']==source['sha256']
        with Image.open(ROOT/row['local_path']) as image:
            assert image.size==(source['width'],source['height']) and image.mode==source['pixel_mode']
            assert sha(image.tobytes())==source['decoded_pixel_sha256']
            assert (sha(image.info['icc_profile']) if image.info.get('icc_profile') else None)==source['source_icc_profile_sha256']
        assert source['original_encoded_stream_or_decoded_pixel_readback_verified'] and not source['source_pixels_changed']
        if source['pixel_mode']=='L':assert source['independent_gray_expansion_verified']
    assert sum(s['original_dct_stream_sha256'] is None for s in proof['figures'])==7
    assert not packaged['clinical_approval'] and not packaged['model_promoted'] and not packaged['structure_coverage_granted']


def test_clinical_panels_do_not_borrow_schematics_fluoroscopy_or_flat_renderings():
    ref=detail(Curriculum(),resolve('ra.aortic-aneurysm-rupture'))['radiology_reference']
    rows={r['figure_number']:r for r in ref['structure_atlas'] if r['id'].startswith(PREFIX)}
    assert len(rows)==13
    for n,row in rows.items():
        c=row['source_context'];assert c['selected_panels']==row['clinical_panels']
        assert all(c['panel_types'][p]=='CT' for p in row['clinical_panels'])
        assert not set(row['clinical_panels'])&set(c['source_ct_volume_rendering_panels'])
        for field in ('flat_renderings_are_spatial_geometry','full_acquired_series_included',
                      'independent_anatomical_validation_verified','independent_timepoint_registration_verified',
                      'independent_calibrated_measurements_verified','clinical_suitability_or_outcome_verified'):
            assert c[field] is False
    assert rows[1]['clinical_panels']==list('ac') and rows[1]['source_context']['source_ct_volume_rendering_panels']==list('bd')
    assert rows[13]['clinical_panels']==list('ac') and rows[13]['source_context']['panel_types']['b']=='Radiography'
    assert rows[13]['ancillary_structures_visible'][0]['panels']==['b']
    for n in (2,3,4,5,6,11):
        assert rows[n]['source_context']['source_schematic_panels']==['a'] and rows[n]['schematic_structures_visible']
    assert not ref['walkthrough']['steps'][3]['images']  # The article does not provide complete branch coverage.


def test_patient_timepoint_and_phase_identity_are_explicit_and_not_inferred():
    rows={r['figure_number']:r['source_context'] for r in json.loads((ROOT/'data/radiology/radiology-open-images.json').read_text())['ra.aortic-aneurysm-rupture']}
    assert rows[6]['panel_patient_ids']['b']!=rows[6]['panel_patient_ids']['c']
    assert rows[5]['panel_patient_ids']['b']==rows[13]['panel_patient_ids']['a']
    assert rows[1]['panel_timepoints']['c']=='one_year_later' and rows[2]['panel_timepoints']['c']=='four_years_later_lumbar_pain'
    assert rows[7]['panel_contrast_phases']=={'a':'arterial','b':'enhanced_phase_not_named'}
    assert rows[9]['panel_contrast_phases']==dict.fromkeys('ab','enhanced_phase_not_named')
    assert rows[12]['panel_contrast_phases']['a']=='unenhanced' and 'post_open_repair' in rows[12]['panel_timepoints']['c']


def test_rights_and_pixel_proof_cannot_grant_complete_anatomical_coverage():
    rows=[r for r in json.loads((ROOT/'data/radiology/radiology-asset-evidence.json').read_text())['assets'] if r['id'].startswith(PREFIX)]
    assert len(rows)==13
    for row in rows:
        rights=row['source']['license'];assert rights['review_status']=='verified' and rights['commercial_use'] and rights['redistribution']
        assert sha((ROOT/rights['evidence_path']).read_bytes())==rights['evidence_sha256']
        assert row['anatomical_review']['status']=='pending' and row['structure_ids']==[] and row['requirement_coverage']=={}
        assert not row['pixel_provenance']['highest_resolution_acquired_master_verified']


@pytest.mark.parametrize('change',['one_channel','dimensions','samples','mode'])
def test_independent_flate_readback_rejects_changed_samples_or_interpretation(tmp_path,change):
    samples=bytes([0,70,140,255]);image=Image.frombytes('L',(2,2),samples).convert('RGB')
    assert image.getpixel((0,1))==(140,140,140)
    if change=='one_channel':image.putpixel((0,1),(140,141,140))
    elif change=='dimensions':image=image.resize((4,1))
    elif change=='mode':image=image.convert('P')
    path=tmp_path/'independent.png';image.save(path)
    with pytest.raises(ValueError):verify_flate_readback(path,samples[:-1] if change=='samples' else samples,'L',(2,2))


def test_independent_gray_expansion_requires_all_channels_and_preserves_original_mode(tmp_path):
    samples=bytes([0,70,140,255]);path=tmp_path/'independent.ppm'
    Image.frombytes('L',(2,2),samples).convert('RGB').save(path)
    assert verify_flate_readback(path,samples,'L',(2,2))
    Image.frombytes('L',(2,2),samples).save(path)
    assert verify_flate_readback(path,samples,'L',(2,2)) is False


def test_flate_extraction_remains_opt_in_for_other_source_acquisitions(tmp_path):
    pytest.importorskip('pypdf');root=ROOT/'.research/aortic-rupture-source-review'
    if not (root/'PMC4035490.1.pdf').exists():pytest.skip('Original research PDF is not installed in this environment')
    source=tmp_path/'source';source.mkdir()
    for name in ('PMC4035490.1.json','PMC4035490.1.xml','PMC4035490.1.pdf','13244_2014_327_Fig1_HTML.jpg'):
        shutil.copyfile(root/name,source/name)
    with pytest.raises(ValueError,match='Unreviewed source filter'):
        acquire(source,tmp_path/'review',{1:SELECTION[1]},{1:dict.fromkeys('abcd','CT')},
                pmcid='PMC4035490',extraction_prefix='original',allow_icc_without_alternate=True)
