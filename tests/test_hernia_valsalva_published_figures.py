"""Original hernia comparisons preserve months/protocols and cannot establish dynamics or enhancement."""
import hashlib,json
from pathlib import Path
from PIL import Image
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail,resolve

ROOT=Path(__file__).resolve().parents[1];REVIEW=ROOT/'docs/hernia-valsalva-published-source-review'


def rows():
    return {r['figure_number']:r for r in detail(Curriculum(),resolve('ra.abdominal-wall-hernias'))['radiology_reference']['structure_atlas'] if r['id'].startswith('open-hernia-valsalva-')}


def test_three_original_gray_jpegs_retain_streams_pixels_actual_lowercase_panels_and_grant():
    proof=json.loads((REVIEW/'original-source-review.json').read_text());package=json.loads((REVIEW/'packaged-source-images.json').read_text())
    assert len(proof['figures'])==len(package['figures'])==3 and proof['articles'][0]['license']=='CC BY 4.0'
    for r in package['figures']:
        original=next(a for a in proof['figures'] if a['figure_number']==r['figure_number']);path=ROOT/r['local_path'];raw=path.read_bytes()
        assert hashlib.sha256(raw).hexdigest()==r['sha256']==original['sha256']==original['original_dct_stream_sha256']
        with Image.open(path) as image:
            assert image.mode=='L' and image.size==(original['width'],original['height'])
            assert hashlib.sha256(image.tobytes()).hexdigest()==original['decoded_pixel_sha256']
        assert original['acquisition']=='original_pdf_dct_stream_byte_identical'
        assert original['source_panel_types']==dict.fromkeys('abcd','CT')
        assert original['publisher_media_md5_verified'] and not original['source_pixels_changed']
    assert proof['articles'][0]['publisher_xml_pdf_md5_verified']


def test_month_separated_noncontrast_valsalva_and_magnifications_do_not_supply_unacquired_features():
    data=rows()
    assert {n:r['source_context']['source_nonValsalva_relative_date'] for n,r in data.items()}=={2:'one month after Valsalva',3:'three months before Valsalva',4:'two months before Valsalva'}
    for r in data.values():
        c=r['source_context'];assert c['source_noncontrast_Valsalva_panels']==['a','b'] and c['source_nonValsalva_panels']==['c','d']
        assert c['source_magnified_view_pairs']=={'b':'a','d':'c'} and c['magnifications_are_not_independent_acquisitions']
        assert not c['same_session_comparison'] and not c['enhancement_or_viability_evidence_granted']
        assert not c['reducibility_or_pressure_causality_verified']
        assert 'months apart' in r['limits'] and 'noncontrast' in r['limits']


def test_diastasis_does_not_become_true_defect_or_calibrated_volume_geometry():
    r=rows()[4];c=r['source_context']
    assert c['depicted_state']==r['image_state']=='source_diastasis_recti'
    assert c['source_reported_interrectus_distances_mm']=={'Valsalva':64,'nonValsalva':36}
    assert not c['independent_caliper_calibration_verified'] and not c['true_fascial_defect_geometry_granted']
    assert 'not independently calibrated geometry' in r['caption']
    assert 'does not automatically supply a true fascial hernia defect' in r['caption']
    ref=detail(Curriculum(),resolve('ra.abdominal-wall-hernias'))['radiology_reference']
    assert {i for s in ref['walkthrough']['steps'] for i in s['images'] if i.startswith('open-hernia-valsalva-')}=={r['id'] for r in ref['structure_atlas'] if r['id'].startswith('open-hernia-valsalva-')}
    assets=[r for r in json.loads((ROOT/'data/radiology/radiology-asset-evidence.json').read_text())['assets'] if r['id'].startswith('open-hernia-valsalva-')]
    assert len(assets)==3
    for a in assets:
        assert a['structure_ids']==[] and a['requirement_coverage']=={} and a['anatomical_review']['status']=='pending'
        rights=a['source']['license'];assert rights['commercial_use'] and rights['redistribution']
        assert hashlib.sha256((ROOT/rights['evidence_path']).read_bytes()).hexdigest()==rights['evidence_sha256']
