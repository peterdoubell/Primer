"""Count reportable radiology structures that have an explicitly bound source asset.

A structure or required part counts as covered only when an asset in the evidence files lists
its id under structure_ids or requirement_coverage. Names and parents are never used to infer
coverage, in line with the binding policy in data/radiology/msk-asset-evidence.json.

Usage: python tools/audit_structure_coverage.py [--json]
"""
import json
import sys
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / 'data' / 'radiology'


def bound_ids():
    bound = set()
    for name in ('radiology-asset-evidence.json', 'msk-asset-evidence.json'):
        for asset in json.loads((DATA / name).read_text())['assets']:
            bound.update(asset.get('structure_ids') or [])
            bound.update(asset.get('requirement_coverage') or {})
    return bound


def coverage():
    bound, rows = bound_ids(), []
    for name in ('non-msk-structure-requirements.json', 'msk-structure-requirements.json'):
        for investigation in json.loads((DATA / name).read_text())['investigations']:
            ids = []
            for structure in investigation['structures']:
                ids.append(structure['id'])
                ids.extend(part['id'] for part in structure.get('required_parts') or [])
            rows.append({'investigation_id': investigation['investigation_id'], 'title': investigation['title'],
                         'required': len(ids), 'bound': sum(i in bound for i in ids)})
    return rows


if __name__ == '__main__':
    rows = coverage()
    total, bound = sum(r['required'] for r in rows), sum(r['bound'] for r in rows)
    if '--json' in sys.argv:
        print(json.dumps({'investigations': len(rows), 'required': total, 'bound': bound, 'rows': rows}, indent=1))
    else:
        for row in sorted(rows, key=lambda r: -r['bound']):
            print(f"{row['bound']:>5} / {row['required']:<6} {row['investigation_id']}  {row['title']}")
        print(f'{bound} of {total} required structures and parts have a bound asset across {len(rows)} investigations; '
              f"{sum(r['bound'] == 0 for r in rows)} investigations have none.")
