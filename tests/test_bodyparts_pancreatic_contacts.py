"""Native millimetres and separate parenchymal contexts must retain all source contacts."""
from collections import Counter,defaultdict
import gzip
import hashlib
import json
from pathlib import Path
import pytest
from tools.anatomy_sources.audit_bodyparts_pancreatic_contacts import contexts
from tools.anatomy_sources.audit_hra_renal_contacts import contact_arrays

ROOT=Path(__file__).resolve().parents[1]
REVIEW=ROOT/'docs/bodyparts-pancreatic-upstream-review'


def test_original_millimetres_are_not_mistaken_for_gltf_metres():
    np=pytest.importorskip('numpy')
    source=np.array([[20.,1000.,3.],[21.,1000.,3.],[20.,1001.,3.]])
    p={'id':'duct','vertices':source,'faces':np.array([[0,1,2]])}
    original=source.copy();v,f,ids,proof=contact_arrays([p],source_units='millimetres')
    assert np.array_equal(v[f[0]],source) and np.array_equal(source,original)
    assert ids==[{'source_part':'duct','source_face_index':0}]
    assert proof['source_positions_changed'] is False
    with pytest.raises(ValueError,match='coordinate units'):contact_arrays([p],source_units='unknown')


def test_alternative_source_parenchyma_is_not_counted_as_two_organs():
    selected=contexts(['FJ1895','FJ2629','FJ1896','FJ3647'])
    assert selected=={'FJ1895':['FJ1895','FJ1896','FJ3647'],'FJ2629':['FJ1896','FJ2629','FJ3647']}
    with pytest.raises(ValueError,match='Missing'):contexts(['FJ1895','FJ1896'])


def test_complete_evidence_counts_and_original_faces_are_preserved():
    inventory_path=REVIEW/'original-obj-geometry-review.json';inventory=json.loads(inventory_path.read_text())
    counts={r['id']:r['triangles'] for r in inventory['records']}
    summary=json.loads((REVIEW/'complete-contact-summary.json').read_text())
    assert [(r['parenchymal_context'],r['source_triangle_count'],r['contact_count']) for r in summary['records']]==[('FJ1895',22216,2943),('FJ2629',21598,2871)]
    for r in summary['records']:
        packed=(REVIEW/r['file']).read_bytes();payload=gzip.decompress(packed);p=json.loads(payload)
        assert hashlib.sha256(packed).hexdigest()==r['compressed_sha256'] and hashlib.sha256(payload).hexdigest()==r['uncompressed_sha256']
        assert len(payload)==r['uncompressed_bytes']
        assert p['source_inventory_sha256']==hashlib.sha256(inventory_path.read_bytes()).hexdigest()
        expected=contexts(counts)[r['parenchymal_context']]
        assert p['included_source_element_ids']==expected and len(expected)==24
        assert sum(counts[i] for i in expected)==r['source_triangle_count']
        assert p['source_coordinate_units']=='millimetres' and p['source_coordinate_unit_conversion_performed'] is False
        assert p['alternative_parenchyma_compared_as_one_biological_context'] is False
        contacts=p['triangle_contact_audit'];assert len(contacts['unexpected_contacts'])==r['contact_count']
        assert contacts['conservative_aabb_candidate_pairs']==contacts['pairs_explicitly_intersection_tested']+contacts['noncoplanar_shared_edge_pairs_resolved_geometrically']
        pairs=Counter()
        for c in contacts['unexpected_contacts']:
            assert c['same_source_element'] is False
            for f in c['original_source_faces']:assert f['source_part'] in expected and 0<=f['source_face_index']<counts[f['source_part']]
            pairs[tuple(sorted(f['source_part'] for f in c['original_source_faces']))]+=1
        assert dict(pairs)=={tuple(pair['elements']):pair['contact_pairs'] for pair in p['affected_source_element_pairs']}
        assert p['contact_categories']=={'between_source_elements':r['contact_count']}
        assert p['preparation']['invalid_source_triangles']==[] and p['source_geometry_changed'] is False
        assert p['clinical_approval'] is False and p['runtime_promoted'] is False


def test_location_views_include_all_contacts_and_every_affected_face():
    summary=json.loads((REVIEW/'complete-contact-summary.json').read_text())
    figures=json.loads((REVIEW/'contact-location-review.json').read_text())
    assert figures['derived_figure_license']=='CC BY-SA 2.1 Japan'
    for r,f in zip(summary['records'],figures['figures']):
        assert f['parenchymal_context']==r['parenchymal_context']
        assert hashlib.sha256((REVIEW/f['file']).read_bytes()).hexdigest()==f['sha256']
        evidence=json.loads(gzip.decompress((REVIEW/r['file']).read_bytes()))
        affected=defaultdict(set)
        for c in evidence['triangle_contact_audit']['unexpected_contacts']:
            for original in c['original_source_faces']:affected[original['source_part']].add(original['source_face_index'])
        assert f['panels'][0]['contact_pairs']==r['contact_count']
        actual={p['element_id']:set(p['face_indices']) for p in f['panels'][0]['original_affected_faces']}
        assert actual==dict(affected)
        assert f['panels'][1]['contact_pairs']==(45 if r['parenchymal_context']=='FJ1895' else 46)
        assert all(p['source_positions_or_faces_changed'] is False for p in f['panels'])
    assert figures['clinical_approval'] is False and figures['runtime_promoted'] is False


def test_common_element_contacts_are_not_altered_by_parenchymal_choice():
    common=[]
    for parent in ['FJ1895','FJ2629']:
        p=json.loads(gzip.decompress((REVIEW/(parent+'-complete-contacts.json.gz')).read_bytes()))
        records={tuple((f['source_part'],f['source_face_index']) for f in r['original_source_faces']):r['contact_points_mm']
                 for r in p['triangle_contact_audit']['unexpected_contacts']
                 if all(f['source_part'] not in ['FJ1895','FJ2629'] for f in r['original_source_faces'])}
        assert len(records)==1606
        common.append(records)
    assert common[0]==common[1]
