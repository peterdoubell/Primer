"""Original object projections and source CT retain pixels, license versions and unresolved interpretation."""
import hashlib,json
from pathlib import Path
from PIL import Image
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail,resolve

ROOT=Path(__file__).resolve().parents[1]
REVIEW=ROOT/'docs/gi-foreign-body-published-source-review'


def test_all_eight_original_pdf_jpeg_streams_keep_pixels_and_actual_license_versions():
    proof=json.loads((REVIEW/'original-source-review.json').read_text());package=json.loads((REVIEW/'packaged-source-images.json').read_text())
    assert len(proof['figures'])==len(package['figures'])==8
    licenses={a['pmcid']:a['license'] for a in proof['articles']}
    assert licenses=={'PMC7273454':'CC BY 3.0','PMC10880048':'CC BY 4.0','PMC12380921':'CC BY 4.0','PMC10205967':'CC BY 3.0','PMC10250127':'CC BY 3.0'}
    assert all(a['publisher_xml_pdf_md5_verified'] for a in proof['articles'])
    assert all(not r['runtime_promoted'] for r in proof['rights_holds'])
    for row in package['figures']:
        original=next(r for r in proof['figures'] if (r['pmcid'],r['figure_number'])==(row['pmcid'],row['figure_number']))
        path=ROOT/row['local_path'];assert hashlib.sha256(path.read_bytes()).hexdigest()==row['sha256']==original['sha256']
        assert original['acquisition']=='original_pdf_dct_stream_byte_identical'
        with Image.open(path) as image:
            assert image.size==(original['width'],original['height']) and hashlib.sha256(image.tobytes()).hexdigest()==original['decoded_pixel_sha256']
        assert original['publisher_media_md5_verified'] and not original['source_pixels_changed']


def test_radiography_is_primary_only_for_the_original_projection_figures():
    ref=detail(Curriculum(),resolve('ra.gi-foreign-bodies'))['radiology_reference'];rows={r['id']:r for r in ref['structure_atlas']}
    assert len(rows)==8
    radiographs=[r for r in rows.values() if r['modality']=='Radiography'];assert len(radiographs)==3
    assert all(r['clinical_panels']==['A','B'] for r in radiographs)
    assert all(r['source_context']['panel_types']=={'A':'Radiography','B':'Radiography'} for r in radiographs)
    assert sum(r['modality']=='CT' for r in rows.values())==5
    linked={i for s in ref['walkthrough']['steps'] for i in s['images'] if i.startswith('open-gi-foreign-body-')}
    assert linked==set(rows)


def test_source_plane_conflict_processed_insets_and_case_relationships_remain_explicit():
    ref=detail(Curriculum(),resolve('ra.gi-foreign-bodies'))['radiology_reference'];rows={r['id']:r for r in ref['structure_atlas']}
    conflict=rows['open-gi-foreign-body-pmc12380921-fig1']
    assert conflict['source_context']['source_plane_claims_unresolved']
    assert 'visible presentation suggests a plane discrepancy' in conflict['caption']
    processed=rows['open-gi-foreign-body-pmc10250127-fig1']
    assert processed['source_context']['source_processed_insets_retained']
    assert 'not unprocessed acquired masters' in processed['caption']
    gastric=[rows['open-gi-foreign-body-pmc7273454-fig'+str(n)] for n in [1,2,3]]
    assert len({r['source_context']['reported_case_group'] for r in gastric})==1
    assert rows['open-gi-foreign-body-pmc10205967-fig1']['source_context']['reported_case_group']!=rows['open-gi-foreign-body-pmc10205967-fig3']['source_context']['reported_case_group']
    assert 'article title names pyloric' in rows['open-gi-foreign-body-pmc10880048-fig1']['caption']


def test_cleared_figures_do_not_grant_calibrated_object_ct_injury_or_model_coverage():
    rows=[r for r in json.loads((ROOT/'data/radiology/radiology-asset-evidence.json').read_text())['assets'] if r['id'].startswith('open-gi-foreign-body-')]
    assert len(rows)==8
    for row in rows:
        assert row['structure_ids']==[] and row['requirement_coverage']=={} and row['anatomical_review']['status']=='pending'
        rights=row['source']['license'];assert rights['commercial_use'] and rights['redistribution']
        assert hashlib.sha256((ROOT/rights['evidence_path']).read_bytes()).hexdigest()==rights['evidence_sha256']
        assert not row['pixel_provenance']['highest_resolution_acquired_master_verified']
