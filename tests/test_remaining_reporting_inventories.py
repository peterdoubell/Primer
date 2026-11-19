"""Draft inventories for the 37 investigations that had none, derived from their reporting checklists."""
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = 'data/radiology/non-msk-structure-requirements.json'
RECEIPT = json.loads((ROOT / 'docs/remaining-reporting-inventories-20261116/inverse.json').read_text())


def added():
    data = json.loads((ROOT / PATH).read_text())
    return data, [i for i in data['investigations'] if i['investigation_id'] in set(RECEIPT['investigation_ids'])]


def test_every_investigation_now_has_a_draft_inventory_and_none_is_approved():
    scope = json.loads((ROOT / 'docs/radiology-fidelity-scope.json').read_text())
    assert all(i['structure_expansion_status'] == 'draft_inventory_exists' and i['clinical_approval'] is False for i in scope['investigations'])
    data, items = added()
    assert len(items) == 37 and set(RECEIPT['investigation_ids']) <= set(data['scope']['catalog_investigation_ids'])
    assert data['scope']['whole_radiology_scope_complete'] is False
    for item in items:
        assert item['clinical_validation_status'] == 'draft_requires_specialist_review'
        assert item['scope_type'] == 'reporting_checklist_rows_without_sub_part_expansion' and item['derivation_note']


def test_each_requirement_is_one_reporting_checklist_row_and_nothing_else():
    from primer.reporting_bridge import descriptor_forms
    checklists = {i['id']: i for form in descriptor_forms()['forms'].values() for i in form['investigations']}
    _, items = added()
    total = 0
    for item in items:
        rows = {s['id']: s for s in checklists[item['investigation_id']]['sections']}
        ids = [s['id'] for s in item['structures']]
        assert ids and len(ids) == len(set(ids)), item['investigation_id']
        for structure in item['structures']:
            row = rows[structure['checklist_row']['section_id']]
            assert structure['name'].endswith(row['label']) and row.get('anatomy_id')
            assert 'required_parts' not in structure                      # no sub-parts are invented
            assert str(row.get('compartment', '')).casefold() != 'technique'
            assert structure['laterality'] in {'left', 'right', 'examined_side'}
            for reference in structure['report_refs']:
                assert item['reporting_checklist'][reference['checklist_index']]['label'] == reference['label']
            total += 1
    assert total == 733


def test_new_requirements_are_bound_only_where_a_source_states_the_structure_and_side():
    """Binding needs a reviewed image per structure: the sided diaphragm panels and reviewed publisher figures."""
    import sys
    sys.path.insert(0, str(ROOT / 'tools'))
    import audit_structure_coverage
    by_id = {row['investigation_id']: row for row in audit_structure_coverage.coverage()}
    assert len(by_id) == 136
    for identifier in RECEIPT['investigation_ids']:
        expected = {'ra.ct-covid': 2, 'ra.dynamic-rectal-examination': 2, 'ra.intracranial-hypotension': 1, 'ra.mri-brain-tumours': 1, 'ra.mri-dementia': 5, 'ra.mri-ms': 2, 'ra.paediatric-chest-ct': 4, 'ra.thoracic-ultrasound': 2, 'ra.thymus': 1, 'ra.transvaginal-nongynaecology': 4, 'ra.ultrasound-acute-abdomen': 4, 'ra.ultrasound-acute-gynaecology': 3, 'ra.ultrasound-gi-tract': 3, 'ra.ultrasound-neonatal-brain': 5, 'ra.ultrasound-paediatric-scrotum': 6, 'ra.venous-sinus-thrombosis': 11}.get(identifier, 0)
        assert by_id[identifier]['bound'] == expected and by_id[identifier]['required'] > 0


def test_the_additions_are_removed_byte_for_byte():
    from tools.anatomy_sources.expand_remaining_requirements import before_remaining_inventories
    from tools.source_studies_compatibility import before_source_studies_bytes
    raw = (ROOT / PATH).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == RECEIPT['after_sha256']
    restored = before_remaining_inventories(raw)
    assert hashlib.sha256(restored).hexdigest() == RECEIPT['before_sha256']
    assert before_remaining_inventories(raw + b'\n') == raw + b'\n'
    old = json.loads(restored)
    assert not set(RECEIPT['investigation_ids']) & {i['investigation_id'] for i in old['investigations']}
    assert hashlib.sha256(before_source_studies_bytes(PATH, raw)).hexdigest() not in (RECEIPT['after_sha256'], RECEIPT['before_sha256'])
    scope = 'docs/radiology-fidelity-scope.json'
    receipt = json.loads((ROOT / 'docs/remaining-reporting-inventories-20261116/scope-inverse.json').read_text())[scope]
    from tools.recist_pelvic_runtime_compatibility import before_recist_pelvic_delivery_bytes
    current_scope = (ROOT / scope).read_bytes()
    historical_scope = before_recist_pelvic_delivery_bytes(scope, current_scope)
    assert hashlib.sha256(historical_scope).hexdigest() == receipt['after']
