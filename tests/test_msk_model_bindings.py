import collections
import json

import pytest

from tools.anatomy_sources import bind_msk_models as tool
from tools.anatomy_sources import bind_stored_caption_assets_pass2 as second
from tools.check_msk_fidelity import inspect_binding, inspect_requirement_coverage

MSK_FAMILIES = {'shoulder', 'elbow', 'wrist', 'hip', 'knee', 'ankle'}
ALIASES = {'hand': 'wrist', 'foot': 'ankle', 'pelvis': 'hip'}


def records():
    review = json.loads(tool.REVIEW.read_text())
    assets = {item['id']: item for item in json.loads(tool.EVIDENCE.read_text())['assets']}
    leaves, names = tool.requirement_leaves()
    return review, assets, leaves, names


def test_every_binding_quotes_the_models_own_label_and_passes_the_checker():
    review, assets, leaves, names = records()
    rows = review['accepted']
    assert len(rows) == 147 and len({row['asset_id'] for row in rows}) == 115 and len({row['structure_id'] for row in rows}) == 129
    assert 'not a radiologist review' in review['reviewer'] and '2026-11-18' in review['decision']
    for row in rows:
        asset = assets[row['asset_id']]
        assert asset['kind'] == 'model' and row['name'] == names[row['structure_id']] and row['quote'] in asset['name']
        coverage = asset['requirement_coverage'][row['structure_id']]
        assert row['structure_id'] in asset['structure_ids'] and coverage == {'extent': 'partial', 'basis': tool.basis(row)}
        assert '“%s”' % row['quote'] in coverage['basis'] and 'One source-labelled model' in coverage['basis']
        assert set(row['investigations']) <= set(asset['investigation_ids']) and asset['anatomical_review']['status'] == 'pending'
        for investigation in row['investigations']:
            requirement = leaves[row['structure_id']][investigation]
            assert requirement['laterality'] == 'examined_side'
            assert inspect_binding(asset, requirement) == []
            assert inspect_requirement_coverage(asset, requirement) == ['requirement_coverage_partial']


def test_each_label_names_the_requirement_and_the_leaf_is_the_recorded_kind():
    review, _, leaves, names = records()
    rows = review['accepted']
    assert collections.Counter(row['evidence'] for row in rows) == {'own_word': 108, 'another_name': 35, 'kind_of': 4}
    assert collections.Counter(row['leaf_basis'] for row in rows) == {'body_part': 60, 'named_part': 55, 'structure': 22, 'group_member': 10}
    pairs = {'another_name': review['another_name_pairs'], 'kind_of': review['kind_of_pairs']}
    for row in rows:
        assert tool.evidence_fits(row, names[row['structure_id']], pairs)
        requirement = next(iter(leaves[row['structure_id']].values()))
        is_part = requirement['parent_id'] != row['structure_id']
        if row['leaf_basis'] == 'structure':
            assert not is_part
        if row['leaf_basis'] == 'body_part':
            assert is_part and names[row['structure_id']].split(': ', 1)[1].lower() in review['body_parts']
    for kind in ('another_name', 'kind_of'):
        assert {'%s>%s' % (pair['label_word'], pair['requirement_word']) for pair in review[kind + '_pairs']} == set(review[kind + '_reasons'])
    # A label that does not name the requirement is refused, and so is a pair that is no longer listed.
    row = next(row for row in rows if row['evidence'] == 'own_word')
    assert not tool.evidence_fits(dict(row, term='meniscus'), names[row['structure_id']], pairs)
    row = next(row for row in rows if row['evidence'] == 'another_name')
    assert not tool.evidence_fits(row, names[row['structure_id']], {'another_name': [], 'kind_of': []})
    # Wholes are not bound to regions, bundles or components.
    bound = {row['structure_id'] for row in rows}
    for leaf in ('knee.anterior_cruciate_ligament.anteromedial_bundle', 'knee.medial_meniscus.anterior_horn', 'ankle.distal_tibia.medial_malleolus',
                 'shoulder.glenoid_labrum.anteroinferior_segment', 'foot.plantar_fascia.central_band'):
        assert leaf not in bound


def test_investigations_are_added_only_where_their_3d_view_shows_the_model():
    from primer.curriculum import Curriculum
    from primer.radiology_catalog import detail, resolve
    review, assets, _, _ = records()
    curriculum = Curriculum()
    # The regions each MSK investigation's 3D view loads, as web/app.js chooses them from the catalog's spatial model.
    for investigation, recorded in review['displays'].items():
        reference = detail(curriculum, resolve(investigation))['radiology_reference']
        if reference.get('spatial_model_options'):
            expected = [[option.get('source_atlas') or 'z-anatomy', ALIASES.get(option['family'], option['family'])]
                        for option in reference['spatial_model_options']]
        else:
            model = reference['spatial_model']
            family = ALIASES.get(model['family'], model['family'])
            if model.get('source_view') in ('whole-foot', 'hamstrings'):
                expected = [[model['source_atlas'], family]]
            elif family == 'knee':
                expected = [['malaya-mri', 'knee'], ['openknee-oks003', 'knee'], ['z-anatomy', 'knee']]
            elif family == 'ankle':
                expected = [['z-anatomy', 'ankle'], ['malaya-ankle', 'ankle']]
            else:
                expected = [['z-anatomy' if family in MSK_FAMILIES else 'bodyparts3d', family]]
        assert recorded == expected, investigation
    regions = tool.region_sides(review)
    added = 0
    for row in review['accepted']:
        for investigation in row['added_investigations']:
            assert tool.shown_in(row['asset_id'], investigation, review, regions) == [row['model_side']]
            added += 1
    assert added == 136


def test_earlier_decisions_and_unshown_models_stay_unbound():
    review, assets, _, _ = records()
    # An earlier Open Knee(s) review left both tibial cartilages unbound: their mask revision lineage is unresolved.
    for identifier in ('oks003-tbc-l', 'oks003-tbc-m'):
        assert assets[identifier]['structure_ids'] == [] and 'lineage' in review['not_bound'][identifier]
    # The hamstring muscle objects keep only their muscle-belly bindings, and their tendon surfaces stay unbound.
    for identifier in ('za-muscles-906368294', 'za-muscles-266598907', 'za-muscles-312860247', 'za-muscles-63886170'):
        assert len(assets[identifier]['structure_ids']) == 1 and assets[identifier + '-material-0']['structure_ids'] == []
    # No MSK investigation shows the BodyParts3D muscle and bone models, so none is bound.
    unshown = [identifier for identifier in assets if identifier.startswith('bodyparts3d.') and assets[identifier]['kind'] == 'model']
    assert len(unshown) == 57 and all(review['not_bound'][identifier].startswith('No MSK investigation') for identifier in unshown)


def test_every_other_model_is_listed_with_its_reason():
    review, assets, _, _ = records()
    before = {item['id']: item for item in json.loads(tool.before_msk_model_bindings(tool.EVIDENCE.read_bytes()))['assets']}
    unbound = {identifier for identifier, item in before.items() if item['kind'] == 'model' and not item['structure_ids']}
    assert len(unbound) == 624
    bound = {row['asset_id'] for row in review['accepted']}
    assert bound | set(review['not_bound']) == unbound and not bound & set(review['not_bound'])
    for identifier, reason in review['not_bound'].items():
        assert reason and assets[identifier]['structure_ids'] == [] and not assets[identifier].get('requirement_coverage')
        assert assets[identifier]['investigation_ids'] == before[identifier]['investigation_ids']


def test_msk_model_bindings_have_an_exact_inverse_and_only_add_bindings():
    receipt = json.loads(tool.RECEIPT.read_text())
    raw = tool.EVIDENCE.read_bytes()
    assert second.sha(raw) == receipt['after_sha256'] and receipt['path'] == 'data/radiology/msk-asset-evidence.json'
    before = tool.before_msk_model_bindings(raw)
    assert second.sha(before) == receipt['before_sha256']
    assert tool.before_msk_model_bindings(before) == before
    assert tool.before_msk_model_bindings(raw + b'\n') == raw + b'\n'
    assert receipt['clinical_approval'] is False and receipt['extends_historical_approval'] is False
    rows = collections.defaultdict(list)
    for row in json.loads(tool.REVIEW.read_text())['accepted']:
        rows[row['asset_id']].append(row)
    old_view, new_view = json.loads(before), json.loads(raw)
    assert {key: value for key, value in old_view.items() if key != 'assets'} == \
        {key: value for key, value in new_view.items() if key != 'assets'}
    fields = ('investigation_ids', 'structure_ids', 'requirement_coverage')
    for old, new in zip(old_view['assets'], new_view['assets']):
        assert {key: value for key, value in old.items() if key not in fields} == {key: value for key, value in new.items() if key not in fields}
        if old['id'] not in rows:
            assert old == new
            continue
        added = [investigation for row in rows[old['id']] for investigation in row['added_investigations']]
        assert new['investigation_ids'] == old['investigation_ids'] + list(dict.fromkeys(added))
        assert new['structure_ids'] == [row['structure_id'] for row in rows[old['id']]] and old['structure_ids'] == []


def test_the_tool_refuses_a_row_that_breaks_a_rule(tmp_path, monkeypatch):
    review = json.loads(tool.REVIEW.read_text())
    ledger, document = tmp_path / 'evidence.json', tmp_path / 'review.json'
    ledger.write_bytes(tool.before_msk_model_bindings(tool.EVIDENCE.read_bytes()))
    monkeypatch.setattr(tool, 'EVIDENCE', ledger)
    monkeypatch.setattr(tool, 'REVIEW', document)
    document.write_text(json.dumps(review))
    assert sum(len(item['structure_ids']) for item in tool.plan().values()) == 147
    index = next(i for i, row in enumerate(review['accepted']) if row['structure_id'] == 'knee.popliteofibular_ligament.course')
    row = review['accepted'][index]
    cases = {
        # The knee view shows this ligament; the shoulder investigation does not.
        'not in an investigation that lists or shows': dict(row, investigations=['ra.mri-shoulder'], added_investigations=['ra.mri-shoulder']),
        'Label is not in the model record': dict(row, quote='Popliteofibular ligament complex'),
        'does not name the requirement': dict(row, term='arcuate ligament'),
        # An attachment is a region of the ligament, not its body.
        'not the kind of requirement recorded': dict(row, structure_id='knee.popliteofibular_ligament.attachments',
                                                     name='Popliteofibular ligament: Attachments'),
    }
    for problem, broken_row in cases.items():
        document.write_text(json.dumps(dict(review, accepted=review['accepted'][:index] + [broken_row] + review['accepted'][index + 1:])))
        with pytest.raises(ValueError, match=problem):
            tool.plan()
