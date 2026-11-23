"""Audit the actual reporting index without inferring complete anatomy from source presence.

The default live view separates image, schematic and model obligations from
patient findings/measurements/flow. Unknown examination scope remains unknown.
The original literal parent/part binding counter is preserved in coverage()
and --legacy-json; it does not establish fidelity or clinical approval.

Usage: python tools/audit_structure_coverage.py [--json | --legacy-json]
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


def representation_counts(requirements, kind):
    from collections import Counter
    selected = [row for row in requirements if row['kind'] == kind]
    statuses = Counter(row['status'] for row in selected)
    partial = sum(any('requirement_coverage_partial' in issues for issues in row['candidates'].values()) for row in selected)
    return dict(required=len(selected), verified=statuses['verified'], partial=statuses['partial'], unverified=statuses['unverified'],
                missing=statuses['missing'], explicitly_bound=sum(bool(row['candidates']) for row in selected),
                with_partial_candidates=partial, source_linked=sum(bool(row.get('source_links')) for row in selected),
                complete_set=bool(selected) and statuses['verified'] == len(selected))


def descriptor_anatomical_inventory(typed):
    """Adapt only ordinary anatomy, retaining all requirement semantics for the existing auditor."""
    return {'schema_version': 1, 'purpose': 'Separate ordinary anatomy representations from actual patient evidence.',
        'clinical_validation_status': 'unreviewed', 'scope': {'catalog_investigation_ids': [typed['investigation_id']]},
        'conventions': typed['conventions'], 'additional_scope': [],
        'investigations': [{'investigation_id': typed['investigation_id'], 'title': typed['title'], 'module_id': typed['guide_id'],
                            'structures': typed['anatomical_requirements'], 'clinical_approval': False,
                            'source_report': typed['source_report'], 'guidance_sources': typed['sources']}]}


def live_coverage():
    """Audit every actual reporting identity; keep binding presence separate from fidelity."""
    root = DATA.parents[1]
    sys.path.insert(0, str(root))
    from primer.curriculum import Curriculum
    from primer.radiology_catalog import index
    from primer.reporting_bridge import with_descriptor_investigations, descriptor_forms
    from tools.check_msk_fidelity import audit, KINDS
    from tools.anatomy_sources.build_soft_tissue_neck_inventory import OUTPUT, validate, digest
    from tools.anatomy_sources.neck_source_links import OUTPUT as LINKS, validate as validate_links, apply_partial_sources

    actual_index = with_descriptor_investigations(index(Curriculum()))
    current = {row['id']: row for row in actual_index['modules']}
    if len(current) != actual_index['count']:
        raise ValueError('Live reporting index has duplicate identities')
    forms = descriptor_forms()
    report_rows = {row['id']: row['sections'] for form in forms['forms'].values() for row in form['investigations']}
    if set(report_rows) != set(current):
        raise ValueError('Actual reporting index and descriptor denominator differ')
    assets = [asset for name in ('radiology-asset-evidence.json', 'msk-asset-evidence.json')
              for asset in json.loads((DATA / name).read_text())['assets']]
    if len({asset['id'] for asset in assets}) != len(assets):
        raise ValueError('Repeated source evidence identity')
    literal = {row['investigation_id']: row for row in coverage()}
    inventories, obligations = {}, {}
    for name in ('non-msk-structure-requirements.json', 'msk-structure-requirements.json'):
        requirements = json.loads((DATA / name).read_text())
        ids = {row['investigation_id'] for row in requirements['investigations']}
        if ids.intersection(inventories) or not ids <= set(current):
            raise ValueError('Legacy inventory identities are duplicated or absent from the current app')
        report = audit(requirements, {'assets': [asset for asset in assets if ids.intersection(asset.get('investigation_ids', []))]}, root=root)
        for item in requirements['investigations']:
            identifier = item['investigation_id']
            inventories[identifier] = dict(kind='legacy_structure_inventory', path='data/radiology/' + name,
                                           typed_evidence_records=0, clinical_completion_claim=False)
            obligations[identifier] = [row for row in report['requirements'] if row['investigation_id'] == identifier]
    typed = validate(json.loads((root / OUTPUT).read_text()), root)
    identifier = typed['investigation_id']
    if identifier in inventories or identifier not in current:
        raise ValueError('Descriptor inventory must name one new exact current reporting identity')
    adapted = descriptor_anatomical_inventory(typed)
    typed_audit = audit(adapted, {'assets': [asset for asset in assets if identifier in asset.get('investigation_ids', [])]}, root=root)
    source_links = validate_links(json.loads((root / LINKS).read_text()), root)
    obligations[identifier] = apply_partial_sources(typed_audit['requirements'], source_links['links'])
    inventories[identifier] = dict(kind='typed_descriptor_inventory', path=OUTPUT,
        sha256=digest(typed), report_section_ids=typed['source_report']['source_section_ids'],
        typed_evidence_records=len(typed['evidence_requirements']),
        typed_evidence_by_type=typed['counts']['evidence_records_by_type'],
        patient_evidence_status='Requires actual current examination; teaching assets cannot satisfy these records.',
        clinical_completion_claim=False)


    rows = []
    for identifier, item in sorted(current.items()):
        known = identifier in inventories
        reps = {kind: representation_counts(obligations[identifier], kind) if known else
                dict(required=None, verified=0, partial=None, unverified=None, missing=None, explicitly_bound=None,
                     with_partial_candidates=None, source_linked=None, complete_set=False) for kind in KINDS}
        rows.append(dict(investigation_id=identifier, title=item['title'],
            report_sections=len(report_rows[identifier]),
            inventory_status='dedicated_inventory_present' if known else 'no_dedicated_inventory',
            inventory=inventories.get(identifier), legacy_literal_binding_counts=literal.get(identifier),
            source_links=source_links['links'] if identifier == typed['investigation_id'] else [],
            representations=reps, anatomical_representation_complete=known and all(row['complete_set'] for row in reps.values()),
            clinical_completion_claim=False))
    all_obligations = [row for group in obligations.values() for row in group]
    return dict(schema_version=3, source_reference_schema_version=1,
        scope='All actual reporting examination identities, including descriptor-only studies.',
        denominator_source='/api/radiology/modules via its actual index functions',
        investigations=len(current), report_sections=sum(len(rows) for rows in report_rows.values()),
        with_dedicated_inventory=len(inventories), without_dedicated_inventory=len(current) - len(inventories),
        legacy_inventory_investigations=len(literal),
        typed_descriptor_investigations=sum(row['kind'] == 'typed_descriptor_inventory' for row in inventories.values()),
        known_representation_obligations=len(all_obligations), total_representation_obligations=None,
        representations={kind: dict(representation_counts(all_obligations, kind), denominator='known inventories only; remaining examinations have unknown requirements') for kind in KINDS},
        typed_patient_evidence_records=sum(row['typed_evidence_records'] for row in inventories.values()),
        clinical_approval=False, clinical_completion_claim=False,
        limitations=['Source-specific partial links are distinct from verified complete evidence and clinical approval.',
            'Explicitly bound counts retain fidelity-ledger candidates; source_linked counts the separately reviewed native references.',
            'Explicit bindings and partial candidates are not verified complete representations.',
            "The legacy literal counter still counts parent/part ID attachments; representation denominators use the established fidelity auditor's leaves.",
            'No requirements or complete-set denominator are invented for studies without dedicated inventories.',
            'An unknown inventory does not mean that all source artwork is absent.',
            'The typed neck records distinguish actual patient findings, flow and measurements from ordinary anatomy.'],
        rows=rows)


if __name__ == '__main__':
    if '--legacy-json' in sys.argv:
        rows = coverage()
        print(json.dumps({'investigations': len(rows), 'required': sum(r['required'] for r in rows),
                          'bound': sum(r['bound'] for r in rows), 'rows': rows}, indent=1))
    else:
        report = live_coverage()
        if '--json' in sys.argv:
            print(json.dumps(report, indent=1))
        else:
            print(f"{report['investigations']} reporting exams: {report['with_dedicated_inventory']} dedicated inventories; {report['without_dedicated_inventory']} remain unexpanded.")
            for kind, counts in report['representations'].items():
                print(f"{kind}: {counts['verified']} verified, {counts['partial']} partial source, {counts['unverified']} unverified and {counts['missing']} missing of {counts['required']} known obligations.")
            for row in report['rows']:
                if row['inventory'] and row['inventory']['kind'] == 'typed_descriptor_inventory':
                    counts = row['representations']
                    print(f"{row['investigation_id']}: {row['report_sections']} report sections; "
                          + ', '.join(f"{kind} {value['verified']}/{value['required']} verified + {value['partial']} partial source" for kind, value in counts.items())
                          + f"; {row['inventory']['typed_evidence_records']} separate patient-evidence records.")
                    for source in row['source_links']:
                        print(f"  partial {source['representation']} {source['requirement_id']}: {source['href']}")
            print('No clinical completion is claimed.')
