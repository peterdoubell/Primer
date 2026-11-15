#!/usr/bin/env python3
"""Account for every original appendix source pair without approving anatomical joins."""
import argparse
from collections import Counter
import gzip
import hashlib
import itertools
import json
from pathlib import Path


def review(output):
    summary = json.loads((output / 'complete-source-pair-summary.json').read_text())
    packed = (output / summary['file']).read_bytes()
    raw = gzip.decompress(packed)
    if hashlib.sha256(packed).hexdigest() != summary['compressed_sha256'] or hashlib.sha256(raw).hexdigest() != summary['uncompressed_sha256']:
        raise ValueError('Complete contact evidence differs')
    evidence = json.loads(raw)
    proximity_raw = (output / 'all-source-pair-proximity-review.json').read_bytes()
    proximity = json.loads(proximity_raw)
    expected = set(itertools.combinations(sorted(evidence['source_part_ids']), 2))
    if (proximity['source_geometry_review_sha256'] != evidence['source_geometry_review_sha256']
            or {tuple(p['source_ids']) for p in proximity['pairs']} != expected or len(proximity['pairs']) != len(expected)):
        raise ValueError('Complete source pair set or geometry differs')
    counts = Counter(tuple(sorted(f['source_part'] for f in c['original_source_faces'])) for c in evidence['triangle_contact_audit']['unexpected_contacts'])
    rows = [{**p, 'continuous_triangle_contact_count': counts[tuple(p['source_ids'])],
             'biological_junction_or_gap_verified': False} for p in proximity['pairs']]
    within = sum(v for (a, b), v in counts.items() if a == b)
    if sum(p['continuous_triangle_contact_count'] for p in rows) + within != summary['contact_count']:
        raise ValueError('Complete contact accounting differs')
    (output / 'complete-pair-proximity-contact-review.json').write_text(json.dumps({
        'complete_contact_evidence_uncompressed_sha256': summary['uncompressed_sha256'],
        'source_proximity_review_sha256': hashlib.sha256(proximity_raw).hexdigest(),
        'source_geometry_review_sha256': evidence['source_geometry_review_sha256'], 'pairs': rows,
        'within_source_contact_count': within, 'source_geometry_changed': False,
        'clinical_approval': False, 'runtime_promoted': False,
        'limits': ['Nearest vertices are an upper bound on minimum continuous surface distance; positive vertex distance does not exclude triangle intersections.',
                   'Repeated mesoappendix labels do not establish independent tissue, exact surface correspondence or anatomical attachment.',
                   'Every original object and contact is retained; no deduplication, fitting, pruning, capping or approved lumen/caecal continuity.']}, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    review(parser.parse_args().output)
