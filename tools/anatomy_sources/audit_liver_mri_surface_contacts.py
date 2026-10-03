#!/usr/bin/env python3
"""Audit independent MRI rater surface contacts without repairing source geometry."""
import argparse
import hashlib
import json
from pathlib import Path


def audit(mesh_root, report_path, output):
    import numpy as np
    from tools.anatomy_sources.audit_massp_surface_intersections import inspect
    report = json.loads(report_path.read_text()); rows = []
    for row in report['records']:
        if not row['mesh_created']: continue
        path = mesh_root / row['mesh_file']
        if hashlib.sha256(path.read_bytes()).hexdigest() != row['mesh_sha256']:
            raise ValueError('Independent rater source surface changed')
        with np.load(path) as data:
            result = inspect(data['vertices'], data['faces'])
        rows.append({'source_file': row['source_file'], 'mesh_sha256': row['mesh_sha256'], **result})
        output.write_text(json.dumps({'source_surface_review_sha256': hashlib.sha256(report_path.read_bytes()).hexdigest(),
                                     'records': rows, 'all_source_surfaces_checked': len(rows) == sum(r['mesh_created'] for r in report['records']),
                                     'source_geometry_changed': False, 'between_liver_tumour_contacts_audited': False,
                                     'clinical_approval': False, 'runtime_promoted': False,
                                     'limits': ['Numerical self-contact audit does not establish original anatomy or rater accuracy.',
                                                'Source handles, mask relations and every reporting structure remain separate review obligations.']}, indent=2) + '\n')
        print(row['source_file'], 'unexpected contacts', result['unexpected_contact_count'], 'candidate pairs', result['conservative_aabb_candidate_pairs'], flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mesh-root', type=Path, required=True); parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(); audit(args.mesh_root, args.report, args.output)
