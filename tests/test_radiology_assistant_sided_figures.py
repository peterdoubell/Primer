import json
import re

from tools.anatomy_sources import package_radiology_assistant_sided_figures as tool
from tools.check_msk_fidelity import inspect_binding, inspect_requirement_coverage, side_unstated
from tools.msk_runtime_rights import license_issues


def test_sided_publisher_figures_are_stored_quoted_and_partial():
    review = json.loads(tool.REVIEW.read_text())
    assets = {item['id']: item for item in json.loads(tool.EVIDENCE.read_text())['assets']}
    made, required = tool.records(), tool.requirements()
    assert len(made) == 39 and len(review['accepted']) == 62 and review['candidate_figures'] == 118
    assert 'not a radiologist review' in review['reviewer']
    rows = {(row['figure'], row['structure_id']): row for row in review['accepted']}
    for asset in made:
        assert assets[asset['id']] == asset
        assert tool.sha((tool.ROOT / asset['local_path']).read_bytes()) == asset['sha256']
        assert asset['anatomical_review']['status'] == 'pending' and asset['source_context']['laterality'] == 'not_reported'
        assert asset['source']['license']['commercial_use'] is False and license_issues(asset, tool.ROOT) == ['commercial_rights_unverified']
        for identifier in asset['structure_ids']:
            row = rows[(asset['source']['asset_url'], identifier)]
            users = [item for (_, key), item in required.items() if key == identifier]
            assert {item['laterality'] for item in users} <= {'left', 'right'}
            coverage = asset['requirement_coverage'][identifier]
            assert coverage == {'extent': 'partial', 'basis': tool.basis(row)} and '“%s”' % row['quote'] in coverage['basis']
            for requirement in users:
                assert side_unstated(asset, requirement) and inspect_binding(asset, requirement) == []
                assert inspect_requirement_coverage(asset, requirement) == ['requirement_coverage_partial']
            stated = any(re.search(r'\b%s\b' % item['laterality'], row['quote'], re.I) for item in users)
            # A sentence may use left or right for a panel position, so only the stated case is checked.
            assert row['side'] in ('caption_states_side', 'side_not_stated') and (stated or row['side'] == 'side_not_stated')
            assert ('assumption that the paired structure is a mirror image' in coverage['basis']) == (row['side'] == 'side_not_stated')


def test_sided_publisher_figures_have_an_exact_inverse():
    receipt = json.loads(tool.RECEIPT.read_text())
    from tools.anatomy_sources.bind_finding_figures import before_finding_figure_bindings
    from tools.anatomy_sources.repair_source_context_codes import before_source_context_repairs as before_repairs
    raw = before_finding_figure_bindings(before_repairs('data/radiology/radiology-asset-evidence.json', tool.EVIDENCE.read_bytes()))  # A findings pass and a context repair followed.
    assert tool.sha(raw) == receipt['after_sha256']
    before = tool.before_radiology_assistant_sided_figures(raw)
    assert tool.sha(before) == receipt['before_sha256'] and tool.before_radiology_assistant_sided_figures(before) == before
    assert receipt['clinical_approval'] is False and receipt['extends_historical_approval'] is False
    assert len(json.loads(raw)['assets']) - len(json.loads(before)['assets']) == 39
