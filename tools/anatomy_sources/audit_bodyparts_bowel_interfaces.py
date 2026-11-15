#!/usr/bin/env python3
"""Retain every original bowel source-pair contact without modifying ducts or tributaries."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path


def audit(root, output):
    from tools.anatomy_sources.review_bodyparts_pancreatic_geometry import read_obj
    from tools.anatomy_sources.audit_hra_renal_contacts import contact_arrays
    from tools.anatomy_sources.audit_massp_surface_intersections import inspect
    report_path = output / 'original-obj-geometry-review.json'
    report = json.loads(report_path.read_text()); parts = []
    for r in report['records']:
        raw = (root / 'objects' / (r['id'] + '.obj')).read_bytes()
        if hashlib.sha256(raw).hexdigest() != r['source_sha256']:
            raise ValueError('Original object changed')
        v, n, f, nf = read_obj(raw.decode())
        parts.append({'id': r['id'], 'vertices': v, 'faces': f})
    group_by_id = {i: g['source_fma'] for g in report['source_groups'] for i in g['element_ids']}
    vertices, faces, identities, preparation = contact_arrays(parts, source_units='millimetres')
    contacts = inspect(vertices, faces)
    for contact in contacts['unexpected_contacts']:
        contact['original_source_faces'] = [identities[i] for i in contact['face_indices']]
        source_ids = {r['source_part'] for r in contact['original_source_faces']}
        contact['same_source_part'] = len(source_ids) == 1
        contact['same_source_fma_group'] = len({group_by_id[i] for i in source_ids}) == 1
    result = {'source_geometry_review_sha256': hashlib.sha256(report_path.read_bytes()).hexdigest(),
        'source_coordinate_units': 'millimetres', 'preparation': preparation, 'triangle_contact_audit': contacts,
        'source_part_ids': [r['id'] for r in report['records']], 'source_fma_groups': group_by_id, 'biological_tree_assembled_or_approved': False, 'source_positions_faces_or_normals_changed': False,
        'clinical_approval': False, 'runtime_promoted': False,
        'limits': ['All sixty source pieces are compared numerically in their original coordinates. This is not a fused or anatomically approved biological bowel tree.',
            'Contacts beyond ordinary adjacency are numerical findings, not pathological invasion or grounds to prune tissue.',
            'Same-label regional pieces remain unclassified source parts; their overlaps are not independent biological contacts or validated branch identities.',
            'Numerical tolerance is not native acquired resolution; no clinical geometry approval or patient registration is inferred.']}
    payload = (json.dumps(result, indent=2) + '\n').encode(); packed = gzip.compress(payload, compresslevel=9, mtime=0)
    target = output / 'complete-source-pair-contacts.json.gz'; target.write_bytes(packed)
    if gzip.decompress(target.read_bytes()) != payload:
        raise ValueError('Lossless contact evidence differs')
    summary = {'file': target.name, 'compressed_sha256': hashlib.sha256(packed).hexdigest(),
        'uncompressed_sha256': hashlib.sha256(payload).hexdigest(), 'uncompressed_bytes': len(payload),
        'compressed_bytes': len(packed), 'source_triangles': preparation['original_source_triangles'],
        'testable_triangles': preparation['numerically_testable_triangles'],
        'candidate_pairs': contacts['conservative_aabb_candidate_pairs'],
        'contact_count': contacts['unexpected_contact_count'],
        'within_object_contact_count': sum(c['same_source_part'] for c in contacts['unexpected_contacts']),
        'same_source_group_between_object_contact_count': sum(c['same_source_fma_group'] and not c['same_source_part'] for c in contacts['unexpected_contacts']),
        'different_source_group_contact_count': sum(not c['same_source_fma_group'] for c in contacts['unexpected_contacts']),
        'between_object_contact_count': sum(not c['same_source_part'] for c in contacts['unexpected_contacts']),
        'all_sixty_original_objects_inspected': len(parts) == 60, 'source_geometry_changed': False,
        'clinical_approval': False, 'runtime_promoted': False}
    (output / 'complete-source-pair-summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print('Complete original bowel source-pair contact evidence preserved.')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source-root', type=Path, required=True); p.add_argument('--output', type=Path, required=True)
    args = p.parse_args(); audit(args.source_root, args.output)
