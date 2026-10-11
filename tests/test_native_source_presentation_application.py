"""Presentation reconciliation cannot grant fine anatomical approval."""
import json
from pathlib import Path

import pytest

from tools.anatomy_sources import apply_native_source_presentation_review as application

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT/'docs/native-source-presentation-review-20261011'


def test_applied_review_preserves_source_and_pending_anatomical_scope():
    contract = json.loads((FOLDER/'proposed-presentation-amendments.json').read_text())
    applied = json.loads((FOLDER/'applied-presentation-review.json').read_text())
    independent = json.loads(application.INDEPENDENT.read_text())
    assets = {row['id']: row for row in json.loads((ROOT/'data/radiology/msk-asset-evidence.json').read_text())['assets']}
    assert applied['contract_sha256'] == independent['contract_sha256'] == application.sha(application.CONTRACT)
    assert applied['independent_review_sha256'] == application.sha(application.INDEPENDENT)
    assert len(applied['dependency_changes']) == 41 and applied['historical_issues_retained'] == 40
    assert set(applied['applied_asset_ids']) == set(independent['approved_amendment_ids'])
    assert not applied['clinical_approval'] and not applied['fine_anatomical_approval']
    for change in contract['amendments']:
        asset = assets[change['id']]
        assert application.sha(ROOT/asset['local_path']) == asset['sha256'] == change['unchanged_source_sha256']
        assert asset['anatomical_review']['status'] == 'pending'
        assert not asset['structure_ids'] and not asset.get('requirement_coverage')
        preserved = {key: asset.get(key) for key in change['preserve_fields_exactly']}
        assert application.digest(preserved) == applied['preserved_field_fingerprints'][asset['id']]
        assert asset['presentation_dependencies'] == change['proposed_presentation_dependencies']
        assert all(application.sha(ROOT/path) == value for path,value in asset['presentation_dependencies'].items())
        review = asset['source_presentation_reconciliation_review']
        assert review['historical_issue_count'] == 2
        assert not review['clinical_approval'] and not review['fine_anatomical_approval']
        for key,value in change.get('proposed_geometry_coordinate_metadata', {}).items():
            assert asset['geometry'][key] == value
        for value in change.get('proposed_source_unknowns_append', []):
            assert value in asset['source_context']['unknowns']


@pytest.mark.parametrize('invalid', ['stale_contract', 'clinical_approval', 'fine_approval', 'blocker'])
def test_application_rejects_unreviewed_or_anatomical_approval_before_writes(tmp_path, monkeypatch, invalid):
    contract = tmp_path/'contract.json'
    contract.write_text('{}')
    independent = {'contract_sha256': application.sha(contract), 'source_presentation_only_verified': True,
                   'blockers': [], 'clinical_approval': False, 'fine_anatomical_approval': False}
    if invalid == 'stale_contract': independent['contract_sha256'] = '0'*64
    if invalid == 'clinical_approval': independent['clinical_approval'] = True
    if invalid == 'fine_approval': independent['fine_anatomical_approval'] = True
    if invalid == 'blocker': independent['blockers'] = ['unresolved source defect']
    review = tmp_path/'independent.json'
    review.write_text(json.dumps(independent))
    monkeypatch.setattr(application, 'CONTRACT', contract)
    monkeypatch.setattr(application, 'INDEPENDENT', review)
    with pytest.raises(AssertionError):
        application.apply()
    assert sorted(path.name for path in tmp_path.iterdir()) == ['contract.json', 'independent.json']
