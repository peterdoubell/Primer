import json
import re
from pathlib import Path

from tools.anatomy_sources import bind_stored_caption_assets as first
from tools.anatomy_sources import bind_stored_caption_assets_pass2 as tool
from tools.anatomy_sources.package_radiology_assistant_sided_figures import before_radiology_assistant_sided_figures as before_sided
from tools.check_msk_fidelity import inspect_binding, inspect_requirement_coverage, side_unstated

ROOT = Path(__file__).resolve().parents[1]
FINDING = re.compile(r'haematoma|hematoma|haemorrhage|hemorrhage|contusion|fracture|pneumothorax|thrombus|stenosis|'
                     r'occlusion|dissection|infarct|herniation|fistul|deficiency|sclerosis', re.I)


def records():
    review = json.loads(tool.REVIEW.read_text())
    assets = {item['id']: item for item in json.loads(tool.EVIDENCE.read_text())['assets']}
    required, holders = tool.requirements()
    return review, assets, required, holders


def test_every_binding_quotes_a_stored_sentence_about_a_selected_panel():
    review, assets, required, holders = records()
    described = tool.captions()
    assert len(review['accepted']) == 280 and len({row['asset_id'] for row in review['accepted']}) == 154
    assert len({row['structure_id'] for row in review['accepted']}) == 191
    assert 'not a radiologist review' in review['reviewer']
    for row in review['accepted']:
        asset = assets[row['asset_id']]
        assert holders[row['structure_id']] & set(asset['investigation_ids'])
        assert row['quote'] in tool.descriptions(described[row['asset_id']])[row['field']] and len(row['quote']) >= 12
        coverage = asset['requirement_coverage'][row['structure_id']]
        assert row['structure_id'] in asset['structure_ids'] and coverage == {'extent': 'partial', 'basis': tool.basis(row)}
        assert '“%s”' % row['quote'] in coverage['basis']
        assert asset['anatomical_review']['status'] != 'approved'
        selected = (asset.get('source_context') or {}).get('selected_panels')
        if selected:
            assert row['panels'] and {str(panel).lower() for panel in row['panels']} <= {str(panel).lower() for panel in selected}
        for requirement in required[row['structure_id']]:
            assert inspect_binding(asset, requirement) == []
            assert inspect_requirement_coverage(asset, requirement) == ['requirement_coverage_partial']


def test_side_is_stated_by_the_sentence_or_recorded_as_an_assumption():
    review, assets, required, _ = records()
    counts = {}
    for row in review['accepted']:
        asset = assets[row['asset_id']]
        sides = {requirement.get('laterality') for requirement in required[row['structure_id']]} & {'left', 'right'}
        assumed = any(side_unstated(asset, requirement) for requirement in required[row['structure_id']])
        counts[row['side']] = counts.get(row['side'], 0) + 1
        assert row['side'] in tool.SIDES
        assert (row['side'] == 'not_sided') == (not sides)
        assert (row['side'] in ('caption_states_side', 'side_not_stated')) == assumed
        if row['side'] == 'record_states_side':
            assert asset['source_context']['laterality'] in sides
        basis = asset['requirement_coverage'][row['structure_id']]['basis']
        assert ('assumption that the paired structure is a mirror image' in basis) == (row['side'] == 'side_not_stated')
        if row['side'] == 'caption_states_side':
            assert any(re.search(tool.SIDE_WORDS[side], row['quote'], re.I if side in row['quote'].lower() else 0)
                       for side in sides) or re.search(tool.BOTH_WORDS, row['quote'], re.I)
    assert counts == {'not_sided': 122, 'caption_states_side': 116, 'side_not_stated': 33, 'record_states_side': 9}
    # A figure whose record states no side can never be recorded as complete for a sided requirement.
    row = next(row for row in review['accepted'] if row['side'] == 'side_not_stated')
    asset = json.loads(json.dumps(assets[row['asset_id']]))
    asset['requirement_coverage'][row['structure_id']]['extent'] = 'complete'
    requirement = next(item for item in required[row['structure_id']] if item.get('laterality') in ('left', 'right'))
    assert inspect_requirement_coverage(asset, requirement) == ['requirement_coverage_side_unstated_cannot_be_complete']


def test_findings_and_diagnoses_are_not_bound():
    review, _, _, _ = records()
    assert not [row['name'] for row in review['accepted'] if FINDING.search(row['name'])]
    assert review['findings_not_bound']['candidate_pairs'] == 133
    assert len(review['rejected']) == 126 and all(row['reason'] for row in review['rejected'])


def test_second_pass_has_an_exact_inverse_and_only_rewrites_first_pass_quotes():
    receipt = json.loads(tool.RECEIPT.read_text())
    raw = before_sided(tool.EVIDENCE.read_bytes())  # Sided publisher figures followed.
    assert tool.sha(raw) == receipt['after_sha256']
    before = tool.before_stored_caption_bindings_pass2(raw)
    assert tool.sha(before) == receipt['before_sha256']
    assert tool.before_stored_caption_bindings_pass2(before) == before
    assert tool.before_stored_caption_bindings_pass2(raw + b'\n') == raw + b'\n'
    assert receipt['clinical_approval'] is False and receipt['extends_historical_approval'] is False
    added = {}
    for row in json.loads(tool.REVIEW.read_text())['accepted']:
        added.setdefault(row['asset_id'], []).append(row['structure_id'])
    earlier = {(row['asset_id'], row['structure_id']) for row in json.loads(first.REVIEW.read_text())['accepted']}
    old_view, new_view = json.loads(before), json.loads(raw)
    assert {key: value for key, value in old_view.items() if key != 'assets'} == \
        {key: value for key, value in new_view.items() if key != 'assets'}
    rewritten = 0
    for old, new in zip(old_view['assets'], new_view['assets']):
        assert {key: value for key, value in old.items() if key not in ('structure_ids', 'requirement_coverage')} == \
            {key: value for key, value in new.items() if key not in ('structure_ids', 'requirement_coverage')}
        assert new.get('structure_ids', []) == old.get('structure_ids', []) + added.get(old['id'], [])
        for identifier, entry in old.get('requirement_coverage', {}).items():
            if new['requirement_coverage'][identifier] != entry:
                # Only the wording of a first-pass quote may change, never its extent.
                assert (old['id'], identifier) in earlier
                assert new['requirement_coverage'][identifier]['extent'] == entry['extent'] == 'partial'
                rewritten += 1
    assert rewritten == 14
