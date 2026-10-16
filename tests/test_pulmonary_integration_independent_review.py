"""Independent integration invariants, without promoting source parity to approval."""
import copy
import hashlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CASE = 'ra.ct-pulmonary-nodules'
NODE = 'rad.4.pulmonary-nodule'


def read(path):
    return json.loads((ROOT / path).read_bytes())


def test_current_questions_are_exact_bounded_independent_amendment():
    path = ROOT / 'docs/pulmonary-nodule-independent-review-20261011/clinical-amendment-proposal.json'
    assert hashlib.sha256(path.read_bytes()).hexdigest() == 'f172a46b75c14554b830c480e65ea7991a5e63457b71bc054ce8be65eb5075a1'
    current = next(n for n in read('data/curriculum/11-radiology.json')['nodes'] if n['id'] == NODE)
    amended = json.loads(path.read_bytes())
    assert len(current['quiz']) == 13
    assert current['quiz'] == amended['independent_amended_questions']
    assert amended['source_case_supplies_question_patient_or_prior_PET_history'] is False


def test_every_pulmonary_obligation_stays_unverified_and_unbound():
    row = next(r for r in read('data/radiology/non-msk-structure-requirements.json')['investigations']
               if r['investigation_id'] == CASE)
    assert len(row['structures']) == 79
    assert sum(len(r['required_parts']) for r in row['structures']) == 625
    assert row['representation_obligations_floor'] == 1875
    assert row['verified_representation_obligations'] == 0
    assert row['unresolved_instantiated_denominator']
    assert row['clinical_approval'] is row['fine_anatomical_approval'] is row['structure_coverage_granted'] is False
    for structure in row['structures']:
        assert structure['image_bindings'] == structure['schematic_bindings'] == structure['model_bindings'] == []
        assert structure['clinical_approval'] is structure['fine_anatomical_approval'] is False
        assert structure['coverage_status'] == 'required_not_verified'


def test_all_other_effective_reporting_contracts_preserved():
    from primer.curriculum import Curriculum
    from primer import radiology_catalog as catalog
    curriculum = Curriculum()
    baseline = read('docs/pulmonary-nodule-integration-review-20261011/baseline-effective-contracts.json')
    count = 0
    for row in baseline['investigations']:
        if row['id'] == CASE:
            continue
        ref = catalog.detail(curriculum, catalog.resolve(row['id']))['radiology_reference']
        from tools.thoracic_data_compatibility import restore_contract
        from tools.hippunfold_runtime_compatibility import restore_prior_contract
        historical = restore_prior_contract(row['id'], {key: ref.get(key) for key in ('reporting', 'report_templates', 'walkthrough', 'reading')})
        assert restore_contract(row['id'], historical) == row['contract']
        count += 1
    assert count == 135


def test_hippunfold_contract_inverse_rejects_unreviewed_local_and_unrelated_changes():
    from tools import hippunfold_runtime_compatibility as bridge
    identifier = 'ra.mri-epilepsy'
    row = bridge.reviewed()['contracts'][identifier]
    original = copy.deepcopy(row['after'])
    assert bridge.restore_prior_contract(identifier, original) == row['before']
    assert original == row['after']
    assert bridge.restore_prior_contract(identifier, row['before']) == row['before']
    for field in ['walkthrough', 'reading']:
        changed = copy.deepcopy(original)
        if field == 'walkthrough':
            changed[field]['steps'][1]['tip'] += ' Unreviewed subtype claim.'
        else:
            changed[field].append({'unreviewed': True})
        with pytest.raises(ValueError, match='effective contract value'):
            bridge.restore_prior_contract(identifier, changed)
    unrelated = {'unreviewed': 'must remain visible to its own historical comparison'}
    assert bridge.restore_prior_contract('another-investigation', unrelated) == unrelated


def test_shared_lesson_and_report_keep_same_exact_source_and_no_part_highlights():
    from primer.curriculum import Curriculum
    from primer import radiology_catalog as catalog
    curriculum = Curriculum()
    lesson = curriculum.nodes[NODE]
    reference = catalog.detail(curriculum, catalog.resolve(CASE))['radiology_reference']
    assert reference['source_native_only'] is True
    assert reference['key_images'] == reference['source_anatomy_references'] == []
    assert reference['walkthrough']['preset_mode'] == 'assessment-prompts'
    assert len(reference['walkthrough']['steps']) == 5
    assert all(step['parts'] == step['images'] == [] for step in reference['walkthrough']['steps'])
    models = [r for r in lesson['lesson_media'] if r.get('renderer') == 'radiology-anatomy']
    assert len(models) == 1 and models[0]['props']['source_native_only'] is True
    assert models[0]['props']['native_inspectors'] == reference['source_native_inspectors']
    assert [r['id'] for r in reference['source_native_inspectors']] == ['lidc-idri-0525-native']


def test_native_model_cannot_be_attached_to_another_lesson():
    from primer.curriculum import Curriculum
    from primer.module_media import radiology_model_props
    lesson = copy.deepcopy(Curriculum().nodes[NODE])
    lesson['id'] = 'rad.4.stroke'
    with pytest.raises(ValueError, match='exact pulmonary source'):
        radiology_model_props(lesson)


def test_missing_native_source_cannot_fall_back_to_generic_anatomy(monkeypatch):
    from primer.curriculum import Curriculum
    from primer import radiology_catalog as catalog
    from primer import source_native_inspectors
    curriculum = Curriculum()
    monkeypatch.setattr(source_native_inspectors, 'references', lambda: {})
    with pytest.raises(ValueError, match='missing source or unreviewed fallback'):
        catalog.detail(curriculum, catalog.resolve(CASE))
