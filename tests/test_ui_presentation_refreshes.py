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
        else:
            assert step['native_presentation_code_touched'] is False


def test_every_refresh_left_the_native_files_exactly_as_reviewed():
    ledger, bound = ui_refresh.load(), reviewed()
    for step in ledger['refreshes']:
        assert step['guarded_paths_sha256'] == {path: bound[path] for path in ledger['guarded_paths']}
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
