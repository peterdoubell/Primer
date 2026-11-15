"""Every original pancreatic contact must keep its source identity and held status."""
from collections import Counter,defaultdict
import gzip
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
REVIEW=ROOT/'docs/hra-pancreatic-source-review'


def test_complete_contact_receipts_include_all_testable_faces_and_invalid_holds():
    summary=json.loads((REVIEW/'complete-contact-summary.json').read_text())
    assert summary['clinical_approval'] is False and summary['source_meshes_changed'] is False
    assert [(r['sex'],r['original_source_triangles'],r['testable_triangles'],r['held_invalid_triangles'],r['contact_count']) for r in summary['records']]==[
        ('female',12894,12886,8,17),('male',38930,38930,0,41)]
    for row in summary['records']:
        packed=(REVIEW/row['file']).read_bytes();payload=gzip.decompress(packed);p=json.loads(payload)
        assert hashlib.sha256(packed).hexdigest()==row['compressed_sha256']
        assert hashlib.sha256(payload).hexdigest()==row['uncompressed_sha256']
        assert len(packed)==row['compressed_bytes'] and len(payload)==row['uncompressed_bytes']
        original_path=REVIEW/('pancreas-'+row['sex']+'-v1.3-original-primitives.json')
        original=json.loads(original_path.read_text())
        assert p['source_inventory_sha256']==hashlib.sha256(original_path.read_bytes()).hexdigest()
        assert p['source_glb_sha256']==original['source_glb_sha256']
        counts={r['node_name']:r['triangles'] for r in original['records']}
        assert set(p['source_part_ids'])==set(counts) and p['all_five_source_regions_included'] is True
        prep=p['preparation'];contact=p['triangle_contact_audit']
        assert prep['original_source_triangles']==prep['numerically_testable_triangles']+len(prep['invalid_source_triangles'])
        assert prep['invalid_source_triangles_removed_from_model'] is False and prep['source_positions_changed'] is False
        assert contact['triangles']==row['testable_triangles']
        assert contact['conservative_aabb_candidate_pairs']==contact['pairs_explicitly_intersection_tested']+contact['noncoplanar_shared_edge_pairs_resolved_geometrically']
        assert len(contact['unexpected_contacts'])==row['contact_count']
        for f in prep['invalid_source_triangles']:
            assert 0<=f['source_face_index']<counts[f['source_part']]
        categories=Counter();pairs=Counter()
        for r in contact['unexpected_contacts']:
            a,b=r['original_source_faces']
            assert all(0<=f['source_face_index']<counts[f['source_part']] for f in [a,b])
            same=a['source_part']==b['source_part'];assert r['same_source_part']==same
            categories['within_source_part' if same else 'between_source_parts']+=1
            pairs[tuple(sorted([a['source_part'],b['source_part']]))]+=1
        assert dict(categories)==row['contact_categories']==p['nonshared_or_overlapping_contact_categories']
        assert pairs=={tuple(r['parts']):r['contact_pairs'] for r in p['affected_source_part_pairs']}
        assert p['clinical_approval'] is False and p['runtime_promoted'] is False
        assert p['source_geometry_edited_repaired_or_fitted'] is False


def test_location_atlas_contains_every_affected_original_face():
    summary=json.loads((REVIEW/'complete-contact-summary.json').read_text())
    figures=json.loads((REVIEW/'held-contact-location-review.json').read_text())
    assert figures['clinical_approval'] is False and figures['runtime_promoted'] is False
    for row,f in zip(summary['records'],figures['figures']):
        p=json.loads(gzip.decompress((REVIEW/row['file']).read_bytes()))
        affected=defaultdict(set)
        for c in p['triangle_contact_audit']['unexpected_contacts']:
            for original in c['original_source_faces']:affected[original['source_part']].add(original['source_face_index'])
        actual={r['source_part']:set(r['source_face_indices']) for r in f['affected_original_faces']}
        assert actual==dict(affected)
        assert f['contact_pairs_displayed']==row['contact_count']
        assert f['invalid_original_faces_displayed']==row['held_invalid_triangles']
        assert f['all_source_context_triangles']==row['original_source_triangles']
        assert f['contact_evidence_sha256']==row['uncompressed_sha256']
        assert hashlib.sha256((REVIEW/f['file']).read_bytes()).hexdigest()==f['sha256']
        assert f['source_positions_or_faces_edited'] is False
