#!/usr/bin/env python3
"""Join every original object-pair vertex bound to complete continuous triangle contact evidence."""
import argparse
from collections import defaultdict
import gzip
import hashlib
import itertools
import json
from pathlib import Path


def review(output):
    summary = json.loads((output / 'complete-source-pair-summary.json').read_text())
    packed = (output / summary['file']).read_bytes(); raw = gzip.decompress(packed)
    if hashlib.sha256(packed).hexdigest() != summary['compressed_sha256'] or hashlib.sha256(raw).hexdigest() != summary['uncompressed_sha256']:
        raise ValueError('Complete contact evidence differs')
    evidence = json.loads(raw)
    proximity_path = output / 'all-source-pair-proximity-review.json'
    proximity_raw = proximity_path.read_bytes(); proximity = json.loads(proximity_raw)
    if proximity['source_geometry_review_sha256'] != evidence['source_geometry_review_sha256']:
        raise ValueError('Pair reviews refer to different original geometry')
    expected = set(itertools.combinations(sorted(evidence['source_part_ids']), 2))
    if {tuple(r['source_ids']) for r in proximity['pairs']} != expected or len(proximity['pairs']) != len(expected):
        raise ValueError('Complete original pair set differs')
    by_pair = defaultdict(list); within = 0
    for contact in evidence['triangle_contact_audit']['unexpected_contacts']:
        key = tuple(sorted(f['source_part'] for f in contact['original_source_faces']))
        if key[0] == key[1]:
            within += 1
        else:
            by_pair[key].append(contact)
    rows = []
    for row in proximity['pairs']:
        key = tuple(row['source_ids']); events = by_pair.get(key, [])
        rows.append({**row, 'continuous_triangle_contact_count': len(events),
            'different_source_vessel_categories': len({evidence['source_vessel_category_by_part'][i] for i in key}) > 1,
            'shares_requested_source_group': bool(set(evidence['requested_source_groups_by_part'][key[0]]) & set(evidence['requested_source_groups_by_part'][key[1]])),
            'biological_junction_or_gap_verified': False})
    if sum(r['continuous_triangle_contact_count'] for r in rows) + within != summary['contact_count']:
        raise ValueError('Complete contact accounting differs')
    (output / 'complete-pair-proximity-contact-review.json').write_text(json.dumps({
        'complete_contact_evidence_uncompressed_sha256': summary['uncompressed_sha256'],
        'source_proximity_review_sha256': hashlib.sha256(proximity_raw).hexdigest(),
        'source_geometry_review_sha256': evidence['source_geometry_review_sha256'],
        'pairs': rows, 'within_source_contact_count': within, 'source_geometry_changed': False,
        'clinical_approval': False, 'runtime_promoted': False,
        'limits': ['All original source-object pairs are retained; numerical contacts, label categories and vertex upper bounds do not prove a patent vessel junction, anatomical gap or correct biological identity.',
                   'Actual returned source labels and shared requested compound groups are distinct categories, not independently validated clinical anatomy.']}, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    review(parser.parse_args().output)
