import collections
import hashlib
import json

from tools.anatomy_sources import repair_source_context_codes as tool
from tools.anatomy_sources.bind_models import before_model_bindings
from tools.anatomy_sources.bind_unlocked_figures import before_unlocked_figure_bindings
from tools.check_msk_fidelity import NORMAL_REFERENCE_STATES, inspect_binding, inspect_source_context


def records():
    review = json.loads(tool.REVIEW.read_text())
    raw = before_unlocked_figure_bindings(before_model_bindings((tool.ROOT / tool.EVIDENCE).read_bytes()))  # The unlocked figures and the models were bound afterwards.
    assets = {item['id']: item for item in json.loads(raw)['assets']}
    return review, raw, assets


def test_no_ledger_record_keeps_an_unreadable_context_code_except_deliberate_empty_selections():
    review, _, assets = records()
    kept = {row['asset_id'] for row in review['left_unchanged']}
    unreadable = {asset_id for asset_id, asset in assets.items()
                  if any(issue.endswith('_invalid') for issue in inspect_source_context(asset, {}))}
    assert unreadable == kept and len(kept) == 6
    assert all(row['issue'] == 'source_context_panel_selection_invalid' and 'content decision' in row['reason']
               for row in review['left_unchanged'])
    assert len(review['repairs']) == 250 and sum(len(row['changes']) for row in review['repairs']) == 318
    assert 'not a radiologist review' in review['reviewer'] and '2026-11-18' in review['decision']


def test_every_repair_follows_its_rule_from_the_stored_value():
    review, raw, assets = records()
    planned = tool.plan(tool.before_source_context_repairs(tool.EVIDENCE, raw))
    assert set(planned) == {row['asset_id'] for row in review['repairs']}
    for asset_id, context in planned.items():
        assert assets[asset_id]['source_context'] == context
    rules = collections.Counter(change['rule'] for row in review['repairs'] for change in row['changes'])
    assert rules == {'extent_vocabulary': 132, 'state_lowercase': 82, 'state_reviewed': 36, 'laterality_vocabulary': 30,
                     'life_stage_vocabulary': 13, 'prose_to_record': 12, 'state_same_meaning': 5, 'state_mixed_panels': 4,
                     'setting_vocabulary': 2, 'laterality_stated': 2}
    assert set(rules) == set(review['rules']) == set(tool.RULES)
    # A change that does not start from the stored value, or does not follow its rule, is refused.
    before = {item['id']: item for item in json.loads(tool.before_source_context_repairs(tool.EVIDENCE, raw))['assets']}
    row = next(item for item in review['repairs'] if item['changes'][0]['rule'] == 'extent_vocabulary')
    change = dict(row['changes'][0], new='complete')
    context = tool.put(dict(before[row['asset_id']]['source_context']), change['field'], change['new'])
    assert not tool.check_change(row['asset_id'], change, context, row, review['vocabulary'])


def test_the_app_catalog_keeps_the_original_codes_and_the_ledger_maps_back_to_them():
    review, _, assets = records()
    rows = tool.catalog_rows(json.loads((tool.ROOT / tool.CATALOG).read_text()))
    mirrored = [row for row in review['repairs'] if row['catalog_mirror']]
    assert len(mirrored) == 181
    for row in review['repairs']:
        asset = assets[row['asset_id']]
        if row['catalog_mirror']:
            assert tool.catalog_view(asset['id'], asset['source_context']) == rows[asset['id']][0]['source_context']
            assert rows[asset['id']][0]['source_context'] != asset['source_context']
        else:
            assert asset['id'] not in rows and asset['kind'] == 'model'


def test_reviewed_states_say_what_the_figure_shows():
    review, _, assets = records()
    state = {asset_id: asset['source_context'].get('depicted_state') for asset_id, asset in assets.items()
             if isinstance(asset.get('source_context'), dict)}
    sinus = 'open-sinonasal-operative-pmc6472854-fig'
    assert [n for n in range(1, 18) if state[sinus + str(n)] == 'normal_variant'] == [1, 2, 3, 4, 6, 7, 9, 10, 11, 12, 13, 14, 15, 16, 17]
    assert state[sinus + '8'] == 'normal_anatomy' and state[sinus + '5'] == 'source_sinonasal_ct_pathology_example'
    # Figures of normal anatomy are now refused as pathology examples, as the checker intends.
    pathology = {'id': 'probe', 'context_requirements': {'purpose': 'pathology_example'}}
    for asset_id in ('open-endometrial-cancer-pmc11119523-fig18', 'open-cervical-cancer-pmc11171278-fig1', sinus + '8'):
        assert state[asset_id] in NORMAL_REFERENCE_STATES
        assert 'source_context_purpose_mismatch' in inspect_source_context(assets[asset_id], pathology)
    assert all(state['open-incidental-cardiac-ct-pmc6365314-fig%d' % n] == 'source_cardiac_ct_case' for n in range(1, 22))
    assert sorted(asset_id for asset_id, value in state.items() if value == 'mixed'
                  and any(row['asset_id'] == asset_id for row in review['repairs'])) == [
        'open-cervical-nodes-pmc13049566-fig3', 'open-epilepsy-pmc8353251-fig3', 'open-epilepsy-pmc8353251-fig4',
        'open-thoracic-us-pmc5401877-fig13']
    assert assets['open-epilepsy-pmc4557590-fig1']['source_context']['laterality'] == 'right'
    assert assets['open-epilepsy-pmc4557590-fig6']['source_context']['laterality'] == 'left'
    prose = [row for row in review['repairs'] if row['changes'][0]['rule'] == 'prose_to_record']
    assert len(prose) == 12 and all(row['asset_id'].startswith('source-only-bp3d-sella-') for row in prose)
    for row in prose:
        context = assets[row['asset_id']]['source_context']
        assert context == {'population': {'life_stage': 'adult'}, 'source_note': row['changes'][0]['old']}


def test_context_only_restrictions_are_kept_and_still_refuse_the_figure():
    review, _, assets = records()
    refused = {row['asset_id']: row for row in review['still_refused']}
    assert len(refused) == 9
    for asset_id, row in refused.items():
        context = assets[asset_id]['source_context']
        assert inspect_source_context(assets[asset_id], {}) == [row['issue']] == ['source_context_selected_panel_state_mismatch']
        assert set(context['panel_states'].values()) <= {'source_case_context_only', 'source_only_case_or_illustration'}
        assert context['depicted_state'] not in context['panel_states'].values()
        assert inspect_binding(dict(assets[asset_id], structure_ids=['probe']), {'id': 'probe'}) != []


def test_the_repair_has_an_exact_inverse_and_changes_only_context_codes():
    review, raw, _ = records()
    receipt = json.loads(tool.RECEIPT.read_text())
    assert receipt['path'] == tool.EVIDENCE and receipt['clinical_approval'] is False and receipt['extends_historical_approval'] is False
    assert hashlib.sha256(raw).hexdigest() == receipt['after_sha256']
    before = tool.before_source_context_repairs(tool.EVIDENCE, raw)
    assert hashlib.sha256(before).hexdigest() == receipt['before_sha256']
    assert tool.before_source_context_repairs(tool.EVIDENCE, before) == before
    assert tool.before_source_context_repairs(tool.EVIDENCE, raw + b'\n') == raw + b'\n'
    assert tool.before_source_context_repairs(tool.CATALOG, raw) == raw
    repaired = {row['asset_id'] for row in review['repairs']}
    old_view, new_view = json.loads(before), json.loads(raw)
    assert tool.unchanged_elsewhere(old_view, new_view, repaired)
    for old, new in zip(old_view['assets'], new_view['assets']):
        assert old.get('structure_ids') == new.get('structure_ids') and old.get('requirement_coverage') == new.get('requirement_coverage')
        assert (old.get('source_context') != new.get('source_context')) == (old['id'] in repaired)
