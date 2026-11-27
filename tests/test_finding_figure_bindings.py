import json
import re

from tools.anatomy_sources import bind_finding_figures as tool
from tools.anatomy_sources import bind_stored_caption_assets_pass2 as second
from tools.anatomy_sources.bind_stored_caption_assets import only_caption_bindings
from tools.anatomy_sources.bind_unlocked_figures import before_unlocked_figure_bindings as before_unlocked
from tools.anatomy_sources.bind_models import before_model_bindings as before_models
from tools.anatomy_sources.bind_body_reader_models import before_body_reader_model_records as before_body_readers
from tools.anatomy_sources.bind_reader_models import before_reader_model_records as before_readers
from tools.anatomy_sources.repair_source_context_codes import before_source_context_repairs as before_repairs
from tools.check_msk_fidelity import inspect_binding, inspect_requirement_coverage, side_unstated


def records():
    review = json.loads(tool.REVIEW.read_text())
    assets = {item['id']: item for item in json.loads(tool.EVIDENCE.read_text())['assets']}
    required, holders = second.requirements()
    return review, assets, required, holders


def test_every_finding_binding_quotes_a_stored_sentence_about_a_selected_panel():
    review, assets, required, holders = records()
    described = second.captions()
    rows = review['accepted']
    assert len(rows) == 462 and len({row['asset_id'] for row in rows}) == 245
    assert len({row['structure_id'] for row in rows}) == 237
    assert 'not a radiologist review' in review['reviewer'] and '2026-11-18' in review['decision']
    for row in rows:
        asset = assets[row['asset_id']]
        assert holders[row['structure_id']] & set(asset['investigation_ids'])
        text = second.descriptions(described[row['asset_id']])[row['field']]
        assert row['quote'] in text and row.get('side_quote', row['quote']) in text
        coverage = asset['requirement_coverage'][row['structure_id']]
        assert row['structure_id'] in asset['structure_ids'] and coverage == {'extent': 'partial', 'basis': tool.basis(row)}
        assert '“%s”' % row['quote'] in coverage['basis']
        assert asset['anatomical_review']['status'] != 'approved' and only_caption_bindings(asset)
        selected = (asset.get('source_context') or {}).get('selected_panels')
        if selected:
            assert row['panels'] and {str(panel).lower() for panel in row['panels']} <= {str(panel).lower() for panel in selected}
        for requirement in required[row['structure_id']]:
            assert inspect_binding(asset, requirement) == []
            assert inspect_requirement_coverage(asset, requirement) == ['requirement_coverage_partial']


def test_each_quote_names_the_finding_in_one_of_three_recorded_ways():
    review, _, required, _ = records()
    counts = {}
    for row in review['accepted']:
        counts[row['evidence']] = counts.get(row['evidence'], 0) + 1
        assert tool.evidence_fits(row, required[row['structure_id']], review['kind_of_pairs'])
        assert ('term' in row) == ('listed_parts' in row) == (row['evidence'] == 'listed_term')
        assert ('kind_of' in row) == (row['evidence'] == 'kind_of')
        if row['evidence'] == 'listed_term':
            # The row names the parts its term stands for, and the stored basis repeats them.
            listed = tool.parts(required[row['structure_id']])
            assert row['listed_parts'] and set(row['listed_parts']) <= set(listed)
            assert all(part.lower() == row['term'].lower() or '“%s”' % part in tool.basis(row) for part in row['listed_parts'])
    assert counts == {'own_word': 362, 'listed_term': 66, 'kind_of': 34}
    # Every kind-of pair is listed with its reason, so the owner can veto any of them.
    assert len(review['kind_of_pairs']) == 21
    assert {'%s>%s' % (pair['caption_word'], pair['requirement_word']) for pair in review['kind_of_pairs']} == set(review['kind_of_reasons'])
    # A quote that does not name the finding is refused, whatever evidence it claims.
    row = dict(next(row for row in review['accepted'] if row['evidence'] == 'own_word'), quote='A normal appearance is shown.')
    assert not tool.evidence_fits(row, required[row['structure_id']], review['kind_of_pairs'])
    row = dict(next(row for row in review['accepted'] if row['evidence'] == 'kind_of'))
    assert not tool.evidence_fits(row, required[row['structure_id']], [])
    # A listed term must name parts of this requirement that contain it.
    row = next(row for row in review['accepted'] if row['evidence'] == 'listed_term')
    assert not tool.evidence_fits(dict(row, listed_parts=[]), required[row['structure_id']], review['kind_of_pairs'])
    assert not tool.evidence_fits(dict(row, listed_parts=['not a part']), required[row['structure_id']], review['kind_of_pairs'])
    other = next(part for part in tool.parts(required[row['structure_id']]) if part not in row['listed_parts']
                 and not all(any(tool.same(word, found) for found in tool.words(part)) for word in tool.words(row['term'])))
    assert not tool.evidence_fits(dict(row, listed_parts=[other]), required[row['structure_id']], review['kind_of_pairs'])


def test_side_is_stated_by_the_caption_or_recorded_as_an_assumption():
    review, assets, required, _ = records()
    counts = {}
    for row in review['accepted']:
        asset = assets[row['asset_id']]
        sides = {requirement.get('laterality') for requirement in required[row['structure_id']]} & {'left', 'right'}
        assumed = any(side_unstated(asset, requirement) for requirement in required[row['structure_id']])
        counts[row['side']] = counts.get(row['side'], 0) + 1
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
    assert counts == {'not_sided': 277, 'caption_states_side': 118, 'side_not_stated': 51, 'record_states_side': 16}
    # Lung findings are never bound on the mirror-image assumption.
    assert not [row for row in review['accepted'] if row['side'] == 'side_not_stated'
                and row['structure_id'].split('.')[0] in ('hrct_lung', 'cystic_lung', 'thoracic_tb', 'cxr', 'pulm_htn')]


def test_catch_all_requirements_and_guarded_figures_stay_unbound():
    review, assets, _, _ = records()
    assert not [row['name'] for row in review['accepted'] if re.search(r'unlisted|every other', row['name'], re.I)]
    assert len(review['rejected']) == 240 and all(row['reason'] and row['asset_id'] in assets for row in review['rejected'])
    # A finding named only in a note that the source's suggestion or attribution is unconfirmed is not bound.
    bound = {(row['asset_id'], row['structure_id']) for row in review['accepted']}
    for pair in (('open-renal-trauma-pmc4376814-fig11', 'trauma_ct.injury'),
                 ('open-bowel-wall-pmc3999365-fig14', 'bowel_wall.infectious_immune'),
                 ('open-bowel-obstruction-pmc4729712-fig10', 'bowel_obstruction.causes'),
                 ('open-bowel-obstruction-pmc4729712-fig10', 'bowel_obstruction.positive_examples')):
        assert pair not in bound and pair[1] not in assets[pair[0]]['structure_ids']
        assert any(row['asset_id'] == pair[0] and 'unconfirmed' in row['reason'] for row in review['rejected'])
    from tools.acute_abdomen_panels_compatibility import before_acute_panel_evidence
    from tools.anatomy_sources import build_acute_abdomen_source_panels as panels
    before_panels = json.loads(before_acute_panel_evidence(tool.EVIDENCE.read_bytes()))
    reviewed = json.loads((panels.ROOT / panels.REVIEW).read_bytes())
    for earlier in before_panels['assets']:
        identifier = earlier['id']
        if identifier.startswith('open-acute-abdomen-ref-'):
            assert earlier['structure_ids'] == []
            current = assets[identifier]
            expected = {binding['target_id'] for panel in reviewed['panels'] if panel['figure_id'] == identifier
                        for binding in panel['bindings']}
            assert set(current['structure_ids']) == set(current['requirement_coverage']) == expected
            assert all(row['extent'] == 'partial' for row in current['requirement_coverage'].values())


def test_finding_bindings_have_an_exact_inverse_and_only_add_bindings():
    receipt = json.loads(tool.RECEIPT.read_text())
    raw = before_repairs('data/radiology/radiology-asset-evidence.json', before_unlocked(before_models(before_readers(before_body_readers(tool.EVIDENCE.read_bytes())))))  # Context codes were repaired, and the unlocked figures and the models bound, after this pass.
    assert second.sha(raw) == receipt['after_sha256']
    before = tool.before_finding_figure_bindings(raw)
    assert second.sha(before) == receipt['before_sha256']
    assert tool.before_finding_figure_bindings(before) == before
    assert tool.before_finding_figure_bindings(raw + b'\n') == raw + b'\n'
    assert receipt['clinical_approval'] is False and receipt['extends_historical_approval'] is False
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
