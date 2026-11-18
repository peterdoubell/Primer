import collections
import json
import re

from tools import lesson_activities_compatibility as history
from tools.anatomy_sources import bind_stored_caption_assets_pass2 as second
from tools.anatomy_sources import bind_unlocked_figures as tool
from tools.anatomy_sources.bind_models import before_model_bindings
from tools.anatomy_sources import repair_source_context_codes as repair
from tools.anatomy_sources.bind_stored_caption_assets import only_caption_bindings
from tools.check_msk_fidelity import inspect_binding, inspect_requirement_coverage, side_unstated

PATH = 'data/radiology/radiology-asset-evidence.json'


def records():
    review = json.loads(tool.REVIEW.read_text())
    assets = {item['id']: item for item in json.loads(tool.EVIDENCE.read_text())['assets']}
    required, holders = second.requirements()
    return review, assets, required, holders


def test_every_binding_quotes_a_stored_sentence_about_a_selected_panel_of_an_unlocked_figure():
    review, assets, required, holders = records()
    described = second.captions()
    repaired = {row['asset_id'] for row in json.loads(repair.REVIEW.read_text())['repairs']}
    rows = review['accepted']
    assert len(rows) == 515 and len({row['asset_id'] for row in rows}) == 138
    assert len({row['structure_id'] for row in rows}) == 283
    assert collections.Counter(row['kind'] for row in rows) == {'structure': 293, 'finding': 222}
    assert 'not a radiologist review' in review['reviewer'] and '2026-11-18' in review['decision']
    for row in rows:
        asset = assets[row['asset_id']]
        assert row['asset_id'] in repaired and asset['kind'] != 'model'
        assert holders[row['structure_id']] & set(asset['investigation_ids'])
        assert row['name'] == required[row['structure_id']][0]['name']
        text = second.descriptions(described[row['asset_id']])[row['field']]
        assert row['quote'] in text and row.get('side_quote', row['quote']) in text
        coverage = asset['requirement_coverage'][row['structure_id']]
        assert row['structure_id'] in asset['structure_ids'] and coverage == {'extent': 'partial', 'basis': tool.basis(row)}
        assert '“%s”' % row['quote'] in coverage['basis']
        if row['evidence'] == 'own_word':
            assert 'names the %s:' % row['kind'] in coverage['basis']
        assert asset['anatomical_review']['status'] != 'approved' and only_caption_bindings(asset)
        selected = (asset.get('source_context') or {}).get('selected_panels')
        if selected:
            assert row['panels'] and {str(panel).lower() for panel in row['panels']} <= {str(panel).lower() for panel in selected}
        for requirement in required[row['structure_id']]:
            assert inspect_binding(asset, requirement) == []
            assert inspect_requirement_coverage(asset, requirement) == ['requirement_coverage_partial']


def test_each_quote_names_the_requirement_in_a_recorded_way():
    review, _, required, _ = records()
    counts = collections.Counter(row['evidence'] for row in review['accepted'])
    assert counts == {'own_word': 464, 'kind_of': 51}
    for row in review['accepted']:
        assert tool.evidence_fits(row, required[row['structure_id']], review['kind_of_pairs'])
        assert ('kind_of' in row) == (row['evidence'] == 'kind_of')
    # Every kind-of pair is listed with its reason, so the owner can veto any of them.
    assert len(review['kind_of_pairs']) == 28
    assert {'%s>%s' % (pair['caption_word'], pair['requirement_word']) for pair in review['kind_of_pairs']} == set(review['kind_of_reasons'])
    # A quote that does not name the requirement is refused, whatever evidence it claims.
    row = dict(next(row for row in review['accepted'] if row['evidence'] == 'own_word'), quote='A normal appearance is shown.')
    assert not tool.evidence_fits(row, required[row['structure_id']], review['kind_of_pairs'])
    row = next(row for row in review['accepted'] if row['evidence'] == 'kind_of')
    assert not tool.evidence_fits(row, required[row['structure_id']], [])


def test_labels_are_spelled_out_by_the_quoted_legend():
    review, assets, _, _ = records()
    labelled = [row for row in review['accepted'] if 'label' in row]
    assert len(labelled) == 10
    for row in labelled:
        assert row['label'].lower() in row['quote'].lower()
        assert '“%s”' % row['label'] in assets[row['asset_id']]['requirement_coverage'][row['structure_id']]['basis']
    # A legend letter on a panel that is not selected is not used: the bladder of the node figure is only on other panels.
    assert 'cervical_cancer.adjacent.bladder_covered_extent' not in assets['open-cervical-cancer-pmc10886638-fig10']['structure_ids']


def test_side_is_stated_by_the_caption_or_recorded_as_an_assumption():
    review, assets, required, _ = records()
    counts = collections.Counter()
    for row in review['accepted']:
        asset = assets[row['asset_id']]
        sides = {requirement.get('laterality') for requirement in required[row['structure_id']]} & {'left', 'right'}
        assumed = any(side_unstated(asset, requirement) for requirement in required[row['structure_id']])
        counts[row['side']] += 1
        assert row['side'] in tool.SIDES and (row['side'] == 'not_sided') == (not sides)
        assert (row['side'] in ('caption_states_side', 'side_not_stated')) == assumed
        if row['side'] == 'record_states_side':
            assert asset['source_context']['laterality'] in sides
        basis = asset['requirement_coverage'][row['structure_id']]['basis']
        assert ('assumption that the two sides are mirror images' in basis) == (row['side'] == 'side_not_stated')
        assert ('side_quote' in row) <= (row['side'] == 'caption_states_side')
        if row['side'] == 'caption_states_side':
            stated = row['quote'] + ' ' + row.get('side_quote', '')
            assert any(re.search(second.SIDE_WORDS[side], stated, re.I if side in stated.lower() else 0)
                       for side in sides) or re.search(tool.BOTH_WORDS, stated, re.I)
    assert counts == {'not_sided': 300, 'caption_states_side': 133, 'side_not_stated': 78, 'record_states_side': 4}


def test_withdrawn_and_out_of_scope_pairs_stay_unbound():
    review, assets, _, _ = records()
    bound = {(row['asset_id'], row['structure_id']) for row in review['accepted']}
    assert not [row['name'] for row in review['accepted'] if re.search(r'unlisted|every other|each other', row['name'], re.I)]
    assert not [row for row in review['accepted'] if re.search(r'\.(measure|acquisition)', row['structure_id'])]
    assert len(review['rejected']) == 133 and all(row['reason'] and row['asset_id'] in assets for row in review['rejected'])
    # The orbit cyst whose stated side conflicts with the image is bound to neither side.
    orbit = 'open-orbit-mri-pmc6095049-fig13'
    assert not [pair for pair in bound if pair[0] == orbit] and assets[orbit]['structure_ids'] == []
    assert any(row['asset_id'] == orbit and 'cannot be settled' in row['reason'] for row in review['rejected'])
    # An unsided pouch above the diaphragm is not bound on the mirror-image assumption.
    pouch = 'open-esophagus-pmc5438315-fig14'
    assert not [pair for pair in bound if pair[0] == pouch and 'lateral_pouch' in pair[1]]
    # The repaired 3D models are reference-only and are not bound here.
    assert all(assets[asset_id]['kind'] != 'model' for asset_id, _ in bound)
    assert 'models' in review['not_bound'] and 'checker' in review['not_bound']


def test_unlocked_bindings_have_an_exact_inverse_and_only_add_bindings():
    receipt = json.loads(tool.RECEIPT.read_text())
    raw = before_model_bindings(tool.EVIDENCE.read_bytes())  # The 3D models were bound afterwards.
    assert second.sha(raw) == receipt['after_sha256']
    before = tool.before_unlocked_figure_bindings(raw)
    assert second.sha(before) == receipt['before_sha256']
    assert tool.before_unlocked_figure_bindings(before) == before
    assert tool.before_unlocked_figure_bindings(raw + b'\n') == raw + b'\n'
    assert receipt['clinical_approval'] is False and receipt['extends_historical_approval'] is False
    # The ledger before this pass is the ledger right after the context-code repair.
    assert second.sha(before) == json.loads(repair.RECEIPT.read_text())['after_sha256']
    added = {}
    for row in json.loads(tool.REVIEW.read_text())['accepted']:
        added.setdefault(row['asset_id'], []).append(row['structure_id'])
    old_view, new_view = json.loads(before), json.loads(raw)
    assert {key: value for key, value in old_view.items() if key != 'assets'} == \
        {key: value for key, value in new_view.items() if key != 'assets'}
    for old, new in zip(old_view['assets'], new_view['assets']):
        assert {key: value for key, value in old.items() if key not in ('structure_ids', 'requirement_coverage')} == \
            {key: value for key, value in new.items() if key not in ('structure_ids', 'requirement_coverage')}
        assert new.get('structure_ids', []) == old.get('structure_ids', []) + added.get(old['id'], [])
        for identifier, entry in old.get('requirement_coverage', {}).items():
            assert new['requirement_coverage'][identifier] == entry
    # The history chain peels this pass first, then the repair.
    assert history.before_activity_registry_bytes(PATH, raw) == \
        history.before_activity_registry_bytes(PATH, repair.before_source_context_repairs(PATH, before))
