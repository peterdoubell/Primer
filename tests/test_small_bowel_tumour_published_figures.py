"""Complete native tumour composites retain source pixels, ICC interpretation and modality boundaries."""
import hashlib,json
from pathlib import Path
from PIL import Image
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail,resolve

ROOT=Path(__file__).resolve().parents[1]
REVIEW=ROOT/'docs/small-bowel-tumour-published-source-review'
SELECTED={2,3,4,5,6,7,9,10,11,12,14,15,16,18,19,20}


def test_all_sixteen_source_figures_preserve_native_component_samples_profiles_and_repository_bytes():
    proof=json.loads((REVIEW/'original-source-review.json').read_text());package=json.loads((REVIEW/'packaged-source-images.json').read_text())
    assert {r['figure_number'] for r in proof['figures']}==SELECTED and len(package['figures'])==16
    assert proof['articles'][0]['license']=='CC BY 4.0'
    assert all('Trovato' not in a for a in proof['articles'][0]['authors'])
    assert proof['rights_holds'][0]['pmcid']=='PMC9935952' and not proof['rights_holds'][0]['runtime_promoted']
    for row in package['figures']:
        source=next(r for r in proof['figures'] if r['figure_number']==row['figure_number']);path=ROOT/row['local_path']
        assert hashlib.sha256(path.read_bytes()).hexdigest()==source['sha256']==row['sha256']
        with Image.open(path) as image:
            assert image.mode=='RGB' and image.size==(source['width'],source['height'])
            assert hashlib.sha256(image.tobytes()).hexdigest()==source['decoded_pixel_sha256']
            if source['pdf_components']:
                assert hashlib.sha256(image.info['icc_profile']).hexdigest()==source['pdf_components'][0]['icc_profile_sha256']
                offset=0
                for component in source['pdf_components']:
                    samples=image.crop((0,offset,component['width'],offset+component['height'])).tobytes()
                    assert hashlib.sha256(samples).hexdigest()==component['native_rgb_sample_sha256'];offset+=component['height']
                assert offset==image.height
            else:
                assert source['acquisition']=='original_repository_encoded_jpeg_byte_identical'
                assert source['sha256']==source['repository_media_sha256']
        assert source['publisher_media_md5_verified'] and not source['source_pixels_changed']


def test_original_native_rows_and_visually_checked_shifted_pdf_identities_remain_exact():
    rows={r['figure_number']:r for r in json.loads((REVIEW/'original-source-review.json').read_text())['figures']}
    assert [r['pdf_object_id'] for r in rows[12]['pdf_components']]==[414,415]
    assert (rows[12]['width'],rows[12]['height'])==(1483,750)
    a,b=(r['original_pdf_placements'][0]['matrix_points'] for r in rows[12]['pdf_components'])
    assert abs(a[4]-b[4])<1e-8 and abs(a[5]-(b[5]+b[3]))<1e-6
    assert rows[14]['pdf_page']==15 and rows[14]['pdf_object_id']==480
    assert rows[15]['pdf_page']==16 and rows[15]['pdf_object_id']==509
    assert rows[16]['pdf_page']==17 and rows[16]['pdf_object_id']==538
    assert rows[14]['source_panel_types']=={'A':'CT','B':'CT','C':'Clinical photograph'}
    assert rows[15]['source_panel_types']=={'A':'CT','B':'CT',**dict.fromkeys('CDEF','MRI')}
    assert rows[16]['source_panel_types']==dict.fromkeys('ABC','CT')


def test_mixed_evidence_and_reported_case_relationships_are_not_borrowed_into_ct():
    ref=detail(Curriculum(),resolve('ra.ct-small-bowel-tumours'))['radiology_reference'];rows={r['figure_number']:r for r in ref['structure_atlas']}
    assert len(rows)==16
    for n,kind,panels in [(12,'Clinical photograph',['D']),(14,'Clinical photograph',['C']),(15,'MRI',list('CDEF')),(19,'MRI',list('CDEF')),(20,'PET-CT',['C'])]:
        ancillary=rows[n]['ancillary_panels'];assert ancillary[0]['kind']==kind and ancillary[0]['panels']==panels
        assert not set(panels).intersection(rows[n]['clinical_panels'])
    assert rows[4]['source_context']['reported_case_group']==rows[7]['source_context']['reported_case_group']==rows[10]['source_context']['reported_case_group']==rows[14]['source_context']['reported_case_group']
    assert rows[2]['source_context']['reported_case_group']==rows[6]['source_context']['reported_case_group']
    assert rows[5]['source_context']['reported_case_group']!=rows[9]['source_context']['reported_case_group']
    assert rows[11]['source_context']['reported_case_group']!=rows[12]['source_context']['reported_case_group']
    assert 'unreported tracer subtype' in rows[20]['caption']
    assert all(not r['source_context']['independent_patient_identity_verified'] for r in rows.values())
    used={i for step in ref['walkthrough']['steps'] for i in step['images'] if i.startswith('open-small-bowel-tumour-')}
    assert used=={r['id'] for r in rows.values()}


def test_source_rights_and_exact_pixels_do_not_approve_tumour_or_interface_coverage():
    assets=json.loads((ROOT/'data/radiology/radiology-asset-evidence.json').read_text())['assets'];rows=[r for r in assets if r['id'].startswith('open-small-bowel-tumour-')]
    assert len(rows)==16
    for row in rows:
        assert row['structure_ids']==[] and row['requirement_coverage']=={} and row['anatomical_review']['status']=='pending'
        rights=row['source']['license'];assert rights['commercial_use'] and rights['redistribution']
        assert hashlib.sha256((ROOT/rights['evidence_path']).read_bytes()).hexdigest()==rights['evidence_sha256']
        assert not row['pixel_provenance']['highest_resolution_acquired_master_verified']
