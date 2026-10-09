#!/usr/bin/env python3
"""Inspect every original HRA bladder triangle without repairing source regions."""
import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path


def audit(source_root, output):
    from tools.anatomy_sources.package_hra_bladder import source
    from tools.anatomy_sources.audit_hra_renal_contacts import contact_arrays
    from tools.anatomy_sources.audit_massp_surface_intersections import inspect
    summaries = []
    for sex in ['female', 'male']:
        review, parts = source(source_root / sex, sex)
        vertices, faces, identities, preparation = contact_arrays(parts)
        print('Auditing complete original source triangles.', flush=True)
        contacts = inspect(vertices, faces)
        pairs = Counter()
        for row in contacts['unexpected_contacts']:
            a, b = (identities[i] for i in row['face_indices'])
            row['original_source_faces'] = [a, b]
            pairs[tuple(sorted([a['source_part'], b['source_part']]))] += 1
        result = {'sex': sex, 'source_glb_sha256': review['source_glb_sha256'], 'preparation': preparation,
                  'triangle_contact_audit': contacts, 'source_faces_and_coordinates_changed': False,
                  'clinical_approval': False, 'complete_reporting_anatomy_approved': False}
        raw = (json.dumps(result, indent=2) + '\n').encode(); compressed = gzip.compress(raw, mtime=0)
        assert gzip.decompress(compressed) == raw
        name = sex + '-complete-contact-review.json.gz'; (output / name).write_bytes(compressed)
        summaries.append({'sex': sex, 'file': name, 'sha256': hashlib.sha256(compressed).hexdigest(),
                          'original_source_triangles': preparation['original_source_triangles'],
                          'testable_triangles': preparation['numerically_testable_triangles'],
                          'contact_count': contacts['unexpected_contact_count'],
                          'affected_parts': [{'parts': list(k), 'contact_pairs': v} for k, v in sorted(pairs.items())],
                          'clinical_approval': False})
        print('Complete source contact evidence saved.', flush=True)
    (output / 'complete-contact-summary.json').write_text(json.dumps(summaries, indent=2) + '\n')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source-root', type=Path, required=True); p.add_argument('--output', type=Path, required=True)
    a = p.parse_args(); audit(a.source_root, a.output)
