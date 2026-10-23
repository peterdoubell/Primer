"""A UI-only refresh may move app.js/styles.css on, and nothing else."""
import hashlib
import json
from pathlib import Path

from tools.anatomy_sources import ui_refresh

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / 'docs/native-source-presentation-review-20261011'


def sha(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def reviewed():
    """Every hash the native presentation review bound, by path."""
    proof = json.loads((REVIEW / 'reader-presentation-proof.json').read_text())
    contract = json.loads((REVIEW / 'proposed-presentation-amendments.json').read_text())
    bound = dict(proof['served'])
    for amendment in contract['amendments']:
        for path, value in amendment['proposed_presentation_dependencies'].items():
            assert bound.setdefault(path, value) == value, path
    return bound


def test_only_the_two_shared_ui_files_are_refreshable_and_nothing_is_approved():
    ledger = ui_refresh.load()
    assert ledger['refreshable_paths'] == ['web/app.js', 'web/styles.css']
    assert not ledger['clinical_approval'] and not ledger['fine_anatomical_approval']
    assert not ledger['reopens_or_extends_any_review']
    assert set(ledger['guarded_paths']) == set(reviewed()) - set(ledger['refreshable_paths'])
    for step in ledger['refreshes']:
        assert set(step['files']) <= set(ledger['refreshable_paths'])
        assert not step['clinical_approval'] and not step['fine_anatomical_approval']
        if step['id']=='2026-10-11-source-case-citation-wrapper':
            proof=ui_refresh.validate_source_case_citation_refresh(step)
            assert step['native_presentation_code_touched'] is True
            assert proof['native_decoder_mesh_CT_renderer_code_touched'] is False
        elif step['id']=='2026-10-11-pulmonary-source-only-mounting':
            from tools.anatomy_sources.pulmonary_ui_compatibility import validate_refresh
            proof=validate_refresh(step)
            assert step['native_presentation_code_touched'] is True
            assert proof['app_bytes_outside_changed_functions_identical'] is True
        elif step['id']=='2026-10-13-source-motion-frame-status':
            from tools.thoracic_motion_ui_compatibility import validate_refresh
            assert len(validate_refresh(step)['rows']) == 24
        elif step['id']=='2026-10-13-thoracic-curated-source-viewer':
            from tools.thoracic_native_runtime_compatibility import validate_refresh
            assert len(validate_refresh(step)['rows']) == 4
        elif step['id']=='2026-10-14-thoracic-lung-source':
            from tools.thoracic_lung_runtime_compatibility import validate_refresh
            assert len(validate_refresh(step)['rows']) == 4
        elif step['id']=='2026-10-14-thoracic-basal-source':
            from tools.thoracic_basal_runtime_compatibility import validate_refresh
            assert len(validate_refresh(step)['rows']) == 4
        elif step['id']=='2026-10-14-thoracic-source-labels':
            from tools.thoracic_label_runtime_compatibility import validate_refresh
            assert len(validate_refresh(step)['rows']) == 4
        elif step['id']=='2026-10-14-cardiac-native-source':
            from tools.cardiac_native_runtime_compatibility import validate_refresh
            assert len(validate_refresh(step)['rows']) == 16
        elif step['id']=='2026-10-16-cardiac-wall-context':
            from tools.cardiac_wall_runtime_compatibility import validate_refresh
            assert len(validate_refresh(step)['rows']) == 16
        elif step['id']=='2026-10-16-hippunfold-registered-reference':
            from tools.hippunfold_runtime_compatibility import validate_refresh
            assert len(validate_refresh(step)['cases']) == 16
        elif step['id']=='2026-10-16-spl-native-limbic-reference':
            from tools.spl_limbic_runtime_compatibility import validate_refresh
            assert len(validate_refresh(step)['cases']) == 24
        elif step['id']=='2026-10-16-spl-reporting-relationships':
            from tools.spl_reporting_runtime_compatibility import validate_refresh
            assert len(validate_refresh(step)['cases']) == 8
        else:
            assert step['native_presentation_code_touched'] is False


def test_every_refresh_left_the_native_files_exactly_as_reviewed():
    ledger, bound = ui_refresh.load(), reviewed()
    for step in ledger['refreshes']:
        assert step['guarded_paths_sha256'] == {path: bound[path] for path in ledger['guarded_paths']}
        if step['id']=='2026-10-23-msk-anatomic-reporting':
            from tools.msk_report_compatibility import validate_refresh
            validate_refresh(step)
            continue
        if step['id']=='2026-10-23-descriptor-reporting':
            from tools.descriptor_report_compatibility import validate_refresh
            validate_refresh(step)
            continue
        if step['id']=='2026-10-22-structured-reporting':
            from tools.structured_reporting_runtime_compatibility import validate_refresh
            validate_refresh(step)
            continue
        if step['id']=='2026-10-22-spine-cardiology-references':
            from tools.spine_cardiology_runtime_compatibility import validate_refresh
            validate_refresh(step)
            continue
        if step['id']=='2026-10-13-source-motion-frame-status':
            from tools.thoracic_motion_ui_compatibility import validate_refresh
            validate_refresh(step)
            continue
        if step['id']=='2026-10-13-thoracic-curated-source-viewer':
            from tools.thoracic_native_runtime_compatibility import validate_refresh
            validate_refresh(step)
            continue
        if step['id']=='2026-10-14-thoracic-lung-source':
            from tools.thoracic_lung_runtime_compatibility import validate_refresh
            validate_refresh(step)
            continue
        if step['id']=='2026-10-14-thoracic-basal-source':
            from tools.thoracic_basal_runtime_compatibility import validate_refresh
            validate_refresh(step)
            continue
        if step['id']=='2026-10-14-thoracic-source-labels':
            from tools.thoracic_label_runtime_compatibility import validate_refresh
            validate_refresh(step)
            continue
        if step['id']=='2026-10-14-cardiac-native-source':
            from tools.cardiac_native_runtime_compatibility import validate_refresh
            validate_refresh(step)
            continue
        if step['id']=='2026-10-16-cardiac-wall-context':
            from tools.cardiac_wall_runtime_compatibility import validate_refresh
            validate_refresh(step)
            continue
        if step['id']=='2026-10-16-hippunfold-registered-reference':
            from tools.hippunfold_runtime_compatibility import validate_refresh
            validate_refresh(step)
            continue
        if step['id']=='2026-10-16-spl-native-limbic-reference':
            from tools.spl_limbic_runtime_compatibility import validate_refresh
            validate_refresh(step)
            continue
        if step['id']=='2026-10-16-spl-reporting-relationships':
            from tools.spl_reporting_runtime_compatibility import validate_refresh
            validate_refresh(step)
            continue
        smoke = step['native_reader_smoke']
        assert smoke['passed'] and [row['width'] for row in smoke['rows']] == [1440, 390]
        for row in smoke['rows']:
            assert row['verse_meshes'] == 17 and row['levels_linking_their_own_ct_reference'] == 17
            assert row['liu_meshes'] == 2 and row['liu_ct_links_after_switch'] == 0
            assert row['native_files_served_identical_to_reviewed']
            assert not row['page_errors'] and not row['failed_requests'] and not row['horizontal_overflow']


def test_the_chain_runs_unbroken_from_the_reviewed_files_to_the_current_ones():
    ledger, bound = ui_refresh.load(), reviewed()
    for path in ledger['refreshable_paths']:
        current = bound[path]
        for step in ledger['refreshes']:
            if path in step['files']:
                assert step['files'][path]['before'] == current, (step['id'], path)
                current = step['files'][path]['after']
        assert current == ui_refresh.advance(path, bound[path]) == sha(path)
    for path in ledger['guarded_paths']:
        assert ui_refresh.advance(path, bound[path]) == bound[path] == sha(path)


def test_an_unrecorded_hash_does_not_advance():
    ledger = ui_refresh.load()
    assert ui_refresh.advance('web/app.js', '0' * 64, ledger) == '0' * 64
    assert ui_refresh.advance('web/radiology-detailed-anatomy.js', '0' * 64, ledger) == '0' * 64


def test_descriptor_refresh_is_exact_and_cannot_extend_source_or_clinical_scope():
    import copy
    import pytest
    from tools import descriptor_report_compatibility as bridge
    step = next(row for row in ui_refresh.load()['refreshes'] if row['id'] == '2026-10-23-descriptor-reporting')
    proof = bridge.validate_refresh(step)
    assert len(proof['files']['web/app.js']['changes']) == 2
    assert step['native_presentation_code_touched'] is False
    for key, value in [
        ('id', 'arbitrary-reporting-refresh'),
        ('clinical_approval', True),
        ('fine_anatomical_approval', True),
        ('reopens_or_extends_any_review', True),
        ('canonical_lesson_data_changed', True),
        ('native_decoder_mesh_CT_renderer_code_touched', True),
        ('native_presentation_change_scope', 'native_image_renderer'),
        ('new_reporting_workflow_validated_by_this_inverse', True),
        ('scoped_compatibility_amendment', {'path': bridge.PROOF, 'sha256': '0' * 64}),
    ]:
        changed = copy.deepcopy(step)
        changed[key] = value
        with pytest.raises(ValueError, match='scope'):
            bridge.validate_refresh(changed)
    for field in ('before', 'after'):
        changed = copy.deepcopy(step)
        changed['files']['web/app.js'][field] = '0' * 64
        with pytest.raises(ValueError, match='scope'):
            bridge.validate_refresh(changed)
    changed = copy.deepcopy(step)
    changed['guarded_paths_sha256']['web/radiology-detailed-anatomy.js'] = '0' * 64
    with pytest.raises(ValueError, match='scope'):
        bridge.validate_refresh(changed)
    for path, row in proof['files'].items():
        raw = (ROOT / path).read_bytes()
        restored = bridge.before_descriptor_bytes(path, raw)
        assert hashlib.sha256(restored).hexdigest() == row['before_sha256']
        assert bridge.before_descriptor_bytes(path, restored) == restored
        with pytest.raises(ValueError, match='Unreviewed'):
            bridge.before_descriptor_bytes(path, raw + b'\n')
    assert bridge.before_descriptor_bytes('unrelated', b'unmodified') == b'unmodified'


def test_only_exact_citation_wrapper_delta_can_use_the_explicit_native_ui_scope():
    import copy
    import pytest
    step=next(s for s in ui_refresh.load()['refreshes'] if s['id']=='2026-10-11-source-case-citation-wrapper')
    proof=ui_refresh.validate_source_case_citation_refresh(step)
    assert proof['native_presentation_code_touched'] is True
    assert proof['app_bytes_outside_changed_function_identical']
    assert len(proof['uterine_compatibility_amendments'])==2
    for key,value in [
        ('id','unreviewed-wrapper'),
        ('native_decoder_mesh_CT_renderer_code_touched',True),
        ('native_presentation_change_scope','mesh_or_image_renderer'),
        ('new_explicit_metadata_field','arbitrary_schema_alias'),
        ('clinical_approval',True),
    ]:
        changed=copy.deepcopy(step);changed[key]=value
        with pytest.raises(ValueError,match='scope'):ui_refresh.validate_source_case_citation_refresh(changed)
    changed=copy.deepcopy(step);changed['files']['web/app.js']['after']='0'*64
    with pytest.raises(ValueError,match='scope'):ui_refresh.validate_source_case_citation_refresh(changed)
    changed=copy.deepcopy(step);changed['guarded_paths_sha256']['web/radiology-detailed-anatomy.js']='0'*64
    with pytest.raises(ValueError,match='guarded'):ui_refresh.validate_source_case_citation_refresh(changed)


def test_hippunfold_inverse_rejects_unrecorded_bytes_and_recovers_every_base_file():
    import pytest
    from tools import hippunfold_runtime_compatibility as bridge
    for path, row in bridge.reviewed()['files'].items():
        raw = (ROOT / path).read_bytes()
        restored = bridge.before_hippunfold_bytes(path, raw)
        assert hashlib.sha256(restored).hexdigest() == row['before_sha256']
        assert bridge.before_hippunfold_bytes(path, restored) == restored
        with pytest.raises(ValueError, match='Unreviewed'):
            bridge.before_hippunfold_bytes(path, raw + b'\n')
    assert bridge.before_hippunfold_bytes('unknown', b'unchanged') == b'unchanged'


def test_hippunfold_semantic_inverse_removes_only_exact_companions_and_reviewed_fields():
    import copy
    import pytest
    from primer.curriculum import Curriculum
    from tools import hippunfold_runtime_compatibility as bridge
    from tools.epilepsy_figure_runtime_compatibility import before_figure_lesson_fields
    from tools.check_radiology_fidelity import digest
    curriculum = Curriculum()
    fields = ['goal', 'learning_outcomes', 'lesson', 'reference', 'radiology_reference', 'visual_spec',
              'lesson_media', 'model_family', 'model_context', 'practice', 'quiz', 'kid_text']
    for identifier, row in bridge.reviewed()['lessons'].items():
        current = {key: curriculum.node(identifier).get(key) for key in fields}
        current = before_figure_lesson_fields(identifier, current)
        assert digest(current) == row['after_contract_sha256']
        original = copy.deepcopy(current)
        restored = bridge.before_hippunfold_lesson_fields(identifier, current)
        assert current == original and digest(restored) == row['before_contract_sha256']
        assert bridge.before_hippunfold_lesson_fields(identifier, restored) == restored
        changed = copy.deepcopy(current)
        changed['unrelated'] = 'retain'
        assert bridge.before_hippunfold_lesson_fields(identifier, changed)['unrelated'] == 'retain'
        changed = copy.deepcopy(current)
        next(m for m in changed['lesson_media'] if m['id'] == row['added_media'][0]['id'])['clinical_approval'] = True
        with pytest.raises(ValueError, match='Unreviewed'):
            bridge.before_hippunfold_lesson_fields(identifier, changed)
        for alteration in row['clinical_fields']:
            changed = copy.deepcopy(current)
            target = changed
            for key in alteration['path'][:-1]:
                target = target[key]
            target[alteration['path'][-1]] += ' unreviewed change'
            with pytest.raises(ValueError, match='Unreviewed'):
                bridge.before_hippunfold_lesson_fields(identifier, changed)


def test_hippunfold_data_and_contract_inverse_keeps_unrelated_drift_visible():
    import copy
    import pytest
    from tools import hippunfold_runtime_compatibility as bridge
    from tools.epilepsy_figure_runtime_compatibility import before_figure_bytes
    for path, row in bridge.reviewed()['data_values'].items():
        data = json.loads(before_figure_bytes(path, (ROOT / path).read_bytes()))
        tokens = {row['token_key']: row['after_raw_token_sha256'], 'unrelated': 'f' * 64}
        data['unrelated'] = 'preserved'
        original = copy.deepcopy(data)
        restored, old_tokens = bridge.restore_prior_view(path, data, tokens)
        assert data == original and restored['unrelated'] == 'preserved'
        assert old_tokens['unrelated'] == 'f' * 64 and tokens[row['token_key']] == row['after_raw_token_sha256']
        assert restored['investigations'][row['investigation_id']] == row['before']
        assert old_tokens[row['token_key']] == row['before_raw_token_sha256']
        for invalid in ['semantics', 'token']:
            changed, bad_tokens = copy.deepcopy(data), dict(tokens)
            if invalid == 'semantics':
                changed['investigations'][row['investigation_id']]['unreviewed'] = True
            else:
                bad_tokens[row['token_key']] = '0' * 64
            with pytest.raises(ValueError, match='Unreviewed'):
                bridge.restore_prior_view(path, changed, bad_tokens)
    records = bridge.reviewed()['contracts']
    contracts = {key: row['after_sha256'] for key, row in records.items()} | {'unrelated': 'f' * 64}
    assert bridge.restore_prior_contracts(contracts) == {key: row['before_sha256'] for key, row in records.items()} | {'unrelated': 'f' * 64}
    for key in records:
        bad = dict(contracts)
        bad[key] = '0' * 64
        with pytest.raises(ValueError, match='Unreviewed'):
            bridge.restore_prior_contracts(bad)


def test_hippunfold_refresh_cannot_extend_approval_or_substitute_reader_evidence():
    import copy
    import pytest
    from tools import hippunfold_runtime_compatibility as bridge
    step = next(row for row in ui_refresh.load()['refreshes']
                if row['id'] == '2026-10-16-hippunfold-registered-reference')
    assert len(bridge.validate_refresh(step)['cases']) == 16
    for field, value in [('clinical_approval', True), ('fine_anatomical_approval', True),
                         ('reopens_or_extends_any_review', True), ('existing_reporting_guides_retained', False),
                         ('native_decoder_mesh_CT_renderer_code_touched', True),
                         ('hippunfold_reader_smoke', {'path': bridge.READER_PROOF, 'sha256': '0' * 64})]:
        changed = copy.deepcopy(step)
        changed[field] = value
        with pytest.raises(ValueError, match='scope'):
            bridge.validate_refresh(changed)
