"""Independent model contacts preserve every native strip identity and clinical limits."""
from collections import Counter
import gzip
import hashlib
import itertools
import json
from pathlib import Path
import zipfile
import pytest

ROOT=Path(__file__).resolve().parents[1];REVIEW=ROOT/'docs/spl-wall-source-review'


def test_all_models_candidates_and_contacts_are_losslessly_accounted():
    summary=json.loads((REVIEW/'independent-wall-contact-summary.json').read_text())
    packed=(REVIEW/summary['file']).read_bytes();raw=gzip.decompress(packed);e=json.loads(raw)
    assert hashlib.sha256(packed).hexdigest()==summary['compressed_sha256']
    assert hashlib.sha256(raw).hexdigest()==summary['uncompressed_sha256']
    assert summary['all_five_original_models_compared'] and len(summary['source_models'])==5
    assert summary['source_triangles']==224612
    assert summary['contact_count']==19748 and summary['within_model_contacts']==24 and summary['between_model_contacts']==19724
    assert summary['candidate_pairs']==1617564
    assert {m['label_value']:m['contact_count'] for m in summary['within_models']}=={'135':6,'136':3,'235':12,'236':0,'32':3}
    assert summary['testable_triangles']+summary['invalid_triangles']==224612
    assert summary['candidate_pairs']==summary['explicitly_tested_pairs']+summary['analytically_resolved_shared_edge_pairs']
    assert summary['contact_count']==len(e['contacts'])==summary['within_model_contacts']+summary['between_model_contacts']
    assert sum(r['contact_count'] for r in summary['within_models'])==summary['within_model_contacts']
    assert len(summary['pairs'])==10 and sum(r['contact_count'] for r in summary['pairs'])==summary['between_model_contacts']
    models={m['source_part'] for m in summary['source_models']}
    assert {tuple(r['label_values']) for r in summary['pairs']}==set(itertools.combinations(sorted(models),2))
    assert e['source_review_sha256']==hashlib.sha256((REVIEW/'independent-wall-source-review.json').read_bytes()).hexdigest()
    for c in e['contacts']:
        assert c['contact_points_ras_mm']
        assert c['within_original_model']==(c['original_source_faces'][0]['source_part']==c['original_source_faces'][1]['source_part'])
        assert not c['anatomical_tissue_or_pathology_classified']
    assert not e['source_geometry_changed'] and not e['clinical_approval'] and not e['runtime_promoted']


def test_retained_contacts_map_to_every_original_native_strip_triangle():
    np=pytest.importorskip('numpy')
    from tools.anatomy_sources.review_spl_wall_source import vtk
    archive=ROOT/'.research/wall-independent-sources/spl-abdomen-2016-09.zip'
    if not archive.exists():pytest.skip('Independent source archive is retained in ignored staging')
    summary=json.loads((REVIEW/'independent-wall-contact-summary.json').read_text());e=json.loads(gzip.decompress((REVIEW/summary['file']).read_bytes()))
    native=json.loads((REVIEW/'independent-wall-source-review.json').read_text());mapping={}
    with zipfile.ZipFile(archive) as z:
        for row in native['records']:
            raw=z.read(row['source_member']);assert hashlib.sha256(raw).hexdigest()==row['source_vtk_sha256']
            v,n,f,strips,*_=vtk(raw);indices=[(s,i) for s,strip in enumerate(strips) for i in range(len(strip)-2)]
            assert len(indices)==len(f)==row['analysis_triangles'];mapping[str(row['label_value'])]=indices
    for c in e['contacts']:
        for face in c['original_source_faces']:
            assert mapping[face['source_part']][face['source_face_index']]==(face['native_strip_index'],face['triangle_index_within_strip'])


def test_location_sheet_retains_every_contact_point_and_original_context():
    summary=json.loads((REVIEW/'independent-wall-contact-summary.json').read_text())
    e=json.loads(gzip.decompress((REVIEW/summary['file']).read_bytes()))
    locations=json.loads((REVIEW/'independent-wall-contact-location-review.json').read_text())
    assert locations['complete_contact_evidence_sha256']==summary['uncompressed_sha256']
    assert hashlib.sha256((REVIEW/locations['file']).read_bytes()).hexdigest()==locations['sha256']
    assert locations['panels'][0]['contact_pairs']==19748
    assert locations['panels'][0]['all_contact_points_displayed']==sum(len(c['contact_points_ras_mm']) for c in e['contacts'])
    assert locations['panels'][1]['contact_pairs']==24 and locations['panels'][2]['contact_pairs']==19724
    assert all(p['all_original_context_triangles']==224612 for p in locations['panels'])
    assert not locations['source_geometry_changed'] and not locations['clinical_approval']
