import collections
import json
import re

import pytest

from tools import lesson_activities_compatibility as history
from tools.anatomy_sources import bind_models as tool
from tools.anatomy_sources import bind_stored_caption_assets_pass2 as second
from tools.anatomy_sources import bind_unlocked_figures as unlocked
from tools.anatomy_sources.bind_body_reader_models import before_body_reader_model_records
from tools.anatomy_sources.bind_reader_models import before_reader_model_records
from tools.anatomy_sources.bind_stored_caption_assets import only_caption_bindings
from tools.check_msk_fidelity import inspect_binding, inspect_requirement_coverage, side_unstated

PATH = 'data/radiology/radiology-asset-evidence.json'
HRA = 'hra-female-pelvis-v1.10-'


def current():
    """The evidence file as this pass left it: the brain and body readers' label meshes were recorded afterwards."""
    return before_reader_model_records(before_body_reader_model_records(tool.EVIDENCE.read_bytes()))


def records():
    review = json.loads(tool.REVIEW.read_text())
    assets = {item['id']: item for item in json.loads(tool.EVIDENCE.read_text())['assets']}
    required, holders = second.requirements()
    return review, assets, required, holders


def pairs(review):
    return {'another_name': review['another_name_pairs'], 'kind_of': review['kind_of_pairs']}


def test_every_binding_quotes_the_models_own_label_and_passes_the_checker():
    review, assets, required, holders = records()
    rows = review['accepted']
    assert len(rows) == 108 and len({row['asset_id'] for row in rows}) == 69
    assert len({row['structure_id'] for row in rows}) == 94 and {row['kind'] for row in rows} == {'structure'}
    assert 'not a radiologist review' in review['reviewer'] and '2026-11-18' in review['decision']
    for row in rows:
        asset = assets[row['asset_id']]
        assert asset['kind'] == 'model' and holders[row['structure_id']] & set(asset['investigation_ids'])
        assert row['name'] == required[row['structure_id']][0]['name']
        assert row['quote'] in asset['name'] and row.get('side_quote', row['quote']) in asset['name']
        coverage = asset['requirement_coverage'][row['structure_id']]
        assert row['structure_id'] in asset['structure_ids'] and coverage == {'extent': 'partial', 'basis': tool.basis(row)}
        assert '“%s”' % row['quote'] in coverage['basis'] and 'One source-labelled model' in coverage['basis']
        assert asset['anatomical_review']['status'] == 'pending' and only_caption_bindings(asset)
        for requirement in required[row['structure_id']]:
            assert inspect_binding(asset, requirement) == []
            assert inspect_requirement_coverage(asset, requirement) == ['requirement_coverage_partial']


def test_each_label_names_the_requirement_in_a_recorded_way():
    review, _, required, _ = records()
    assert collections.Counter(row['evidence'] for row in review['accepted']) == {'own_word': 87, 'another_name': 13, 'kind_of': 8}
    for row in review['accepted']:
        assert tool.evidence_fits(row, required[row['structure_id']], pairs(review))
        assert ('term' in row) == (row['evidence'] == 'own_word')
    # Every pair in other words is listed with its reason, so the owner can veto any of them.
    assert len(review['another_name_pairs']) == 10 and len(review['kind_of_pairs']) == 4
    for kind in ('another_name', 'kind_of'):
        assert {'%s>%s' % (pair['label_word'], pair['requirement_word']) for pair in review[kind + '_pairs']} == set(review[kind + '_reasons'])
    # A label that does not name the requirement is refused, whatever evidence it claims.
    row = next(row for row in review['accepted'] if row['evidence'] == 'own_word')
    assert not tool.evidence_fits(dict(row, quote='Bone'), required[row['structure_id']], pairs(review))
    assert not tool.evidence_fits(dict(row, term='trachea'), required[row['structure_id']], pairs(review))
    for kind in ('another_name', 'kind_of'):
        row = next(row for row in review['accepted'] if row['evidence'] == kind)
        assert not tool.evidence_fits(row, required[row['structure_id']], {'another_name': [], 'kind_of': []})


def test_stated_sides_agree_with_where_each_mesh_lies():
    review, assets, required, _ = records()
    counts, cache = collections.Counter(), {}
    for row in review['accepted']:
        asset = assets[row['asset_id']]
        sides = {requirement.get('laterality') for requirement in required[row['structure_id']]} & {'left', 'right'}
        counts[row['side']] += 1
        assert row['side'] in tool.SIDES and (row['side'] == 'not_sided') == (not sides)
        assert (row['side'] in tool.SIDE_NOT_IN_RECORD) == any(side_unstated(asset, requirement) for requirement in required[row['structure_id']])
        basis = asset['requirement_coverage'][row['structure_id']]['basis']
        assert ('assumption that the two sides are mirror images' in basis) == (row['side'] == 'side_not_stated')
        if row['side'] in ('label_states_side', 'mesh_spans_both_sides'):
            assert tool.side_fits_mesh(row, sides, review['frames'], assets, cache)
        if row['side'] == 'label_states_side' and not tool.states_both(row):
            stated = (row['quote'] + ' ' + row.get('side_quote', '')).replace('_', ' ').lower()
            assert sides <= set(stated.split())
            # The same mesh would be refused for the other side.
            assert not tool.side_fits_mesh(row, {'left', 'right'} - sides, review['frames'], assets, cache)
    assert counts == {'label_states_side': 48, 'not_sided': 35, 'mesh_spans_both_sides': 12, 'side_not_stated': 12,
                      'record_states_side': 1}
    # Only the OpenEar specimen, whose ear is not recorded, rests on the mirror-image assumption.
    assert {row['asset_id'].rsplit('-part', 1)[0] for row in review['accepted'] if row['side'] == 'side_not_stated'} == {'openear-zeta'}


def test_the_source_swaps_its_round_ligament_labels_and_neither_is_bound():
    review, assets, _, _ = records()
    frames, cache = review['frames'], {}
    left_labelled, right_labelled = HRA + 'n0454-p0-vh_f_left_round_ligament_of_uterus', HRA + 'n0453-p0-vh_f_right_round_ligament_of_uterus'
    frame, offset, _ = tool.side_position(right_labelled, frames, assets, cache)
    assert offset > frame['margin']  # labelled right, lies on the body's left
    frame, offset, _ = tool.side_position(left_labelled, frames, assets, cache)
    assert offset < -frame['margin']  # labelled left, lies on the body's right
    # Every other sided mesh of the source (30) lies on its labelled side.
    checked = 0
    for identifier in assets:
        stem = identifier[len(HRA):]
        if identifier.startswith(HRA) and 'round_ligament' not in stem and re.search(r'(_r|_l|right|left)(_|$)', stem):
            _, offset, _ = tool.side_position(identifier, frames, assets, cache)
            assert (offset > frames[HRA]['margin']) if re.search(r'(_l|left)(_|$)', stem) else (offset < -frames[HRA]['margin']), identifier
            checked += 1
    assert checked == 30
    for identifier in (left_labelled, right_labelled):
        assert assets[identifier]['structure_ids'] == [] and 'swapped' in review['not_bound'][identifier]
    assert any('round ligament labels are swapped' in finding for finding in review['source_findings'])


def test_every_other_model_is_listed_with_its_reason_and_wholes_are_not_bound_to_parts():
    review, assets, _, _ = records()
    before = {item['id']: item for item in json.loads(tool.before_model_bindings(current()))['assets']}
    unbound_before = {identifier for identifier, item in before.items() if item['kind'] == 'model' and not item['structure_ids']}
    assert len(unbound_before) == 142
    bound = {row['asset_id'] for row in review['accepted']}
    assert bound | set(review['not_bound']) == unbound_before and not bound & set(review['not_bound'])
    for identifier, reason in review['not_bound'].items():
        assert reason and assets[identifier]['structure_ids'] == [] and assets[identifier]['requirement_coverage'] == {}
    # A whole is not bound to a requirement that names its parts.
    for identifier in ('totalseg-v3-esophagus-s0358-aorta', 'totalseg-v3-esophagus-s0358-esophagus', 'hvsmr2-pat7-label5',
                       'bp3d-carotid-4.3-fj4993', 'openear-zeta-part2', 'totalseg-v3-s0358-thyroid_gland'):
        assert identifier in review['not_bound']
    assert 'parts' in review['not_bound']['totalseg-v3-esophagus-s0358-aorta']
    # Tumour and target models stay unbound: their requirements are findings the checker cannot read without a depicted state.
    for identifier in ('ispy1-expert1002-expert-structural-tumour', 'prostate-biopsy0001-suspicious-target1', 'fedbca-center1-001-label1-cells'):
        assert 'depicted state' in review['not_bound'][identifier]


def test_model_bindings_have_an_exact_inverse_and_only_add_bindings():
    receipt = json.loads(tool.RECEIPT.read_text())
    raw = current()
    assert second.sha(raw) == receipt['after_sha256']
    before = tool.before_model_bindings(raw)
    assert second.sha(before) == receipt['before_sha256']
    assert tool.before_model_bindings(before) == before
    assert tool.before_model_bindings(raw + b'\n') == raw + b'\n'
    assert receipt['clinical_approval'] is False and receipt['extends_historical_approval'] is False
    # The ledger before this pass is the ledger right after the unlocked-figure pass.
    assert second.sha(before) == json.loads(unlocked.RECEIPT.read_text())['after_sha256']
    added = {}
    for row in json.loads(tool.REVIEW.read_text())['accepted']:
        added.setdefault(row['asset_id'], []).append(row['structure_id'])
    old_view, new_view = json.loads(before), json.loads(raw)
    assert {key: value for key, value in old_view.items() if key != 'assets'} == \
        {key: value for key, value in new_view.items() if key != 'assets'}
    for old, new in zip(old_view['assets'], new_view['assets']):
        assert {key: value for key, value in old.items() if key not in ('structure_ids', 'requirement_coverage')} == \
            {key: value for key, value in new.items() if key not in ('structure_ids', 'requirement_coverage')}
        assert new['structure_ids'] == old['structure_ids'] + added.get(old['id'], [])
        if old['id'] in added:
            assert old['kind'] == 'model' and old['structure_ids'] == [] and old['requirement_coverage'] == {}
    # The history chain peels this pass first, then the unlocked figures.
    assert history.before_activity_registry_bytes(PATH, raw) == history.before_activity_registry_bytes(PATH, before)


def test_the_tool_refuses_a_row_that_breaks_a_rule(tmp_path, monkeypatch):
    review = json.loads(tool.REVIEW.read_text())
    before = tool.before_model_bindings(current())
    ledger, document = tmp_path / 'evidence.json', tmp_path / 'review.json'
    ledger.write_bytes(before)
    monkeypatch.setattr(tool, 'EVIDENCE', ledger)
    monkeypatch.setattr(tool, 'REVIEW', document)
    document.write_text(json.dumps(review))
    assert sum(len(item['structure_ids']) for item in tool.plan().values()) == 108
    ovary = next(index for index, row in enumerate(review['accepted']) if row['structure_id'] == 'endometriosis.right.adnexa.ovary')
    # The right-labelled round ligament mesh lies on the body's left, so binding it to a right requirement is refused.
    swapped = {'asset_id': HRA + 'n0453-p0-vh_f_right_round_ligament_of_uterus',
               'structure_id': 'endometriosis.right.ligament.round_ligament_distal_pelvic_course',
               'name': 'Right round ligament distal pelvic course', 'kind': 'structure', 'quote': 'Right round ligament of uterus',
               'evidence': 'own_word', 'term': 'round ligament', 'side': 'label_states_side'}
    cases = {
        'does not lie on the stated side': swapped,
        'Label is not in the model record': dict(review['accepted'][ovary], quote='Right ovary and tube'),
        'does not name the requirement': dict(review['accepted'][ovary], term='uterus'),
        'Label does not state the side': dict(review['accepted'][ovary], structure_id='endometriosis.left.adnexa.ovary',
                                              name='Left ovary'),
    }
    for problem, row in cases.items():
        broken = dict(review, accepted=review['accepted'][:ovary] + [row] + review['accepted'][ovary + 1:])
        document.write_text(json.dumps(broken))
        with pytest.raises(ValueError, match=problem):
            tool.plan()
