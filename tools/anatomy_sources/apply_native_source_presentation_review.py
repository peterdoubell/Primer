#!/usr/bin/env python3
"""Apply byte-checked, independently reviewed presentation changes only."""
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FOLDER = ROOT/'docs/native-source-presentation-review-20261011'
CONTRACT = FOLDER/'proposed-presentation-amendments.json'
INDEPENDENT = ROOT/'docs/native-source-presentation-independent-review-20261011.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def save(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False)+'\n')


def apply():
    contract = json.loads(CONTRACT.read_text())
    independent = json.loads(INDEPENDENT.read_text())
    assert independent['contract_sha256'] == sha(CONTRACT)
    assert independent['source_presentation_only_verified'] and not independent['blockers']
    assert not independent['clinical_approval'] and not independent['fine_anatomical_approval']
    assert independent['preserved_source_files_checked'] == 20
    ids = {row['id'] for row in contract['amendments']}
    assert len(ids) == contract['asset_count'] == 20
    assert set(independent['approved_amendment_ids']) == ids
    assert contract['original_issue_count'] == len(contract['original_issues']) == 40
    assert contract['source_presentation_verified'] and not contract['clinical_approval'] and not contract['fine_anatomical_approval']
    assert sha(ROOT/'data/radiology/source-anatomy-references.json') == contract['source_reference_registry_sha256']
    for item in contract['evidence']:
        path = ROOT/item['path']
        assert path.resolve().is_relative_to(FOLDER.resolve()) and sha(path) == item['sha256']
    path = ROOT/'data/radiology/msk-asset-evidence.json'
    evidence = json.loads(path.read_text())
    before = copy.deepcopy(evidence)
    assets = {asset['id']: asset for asset in evidence['assets']}
    changes = []
    preserved_fingerprints = {}
    for item in contract['amendments']:
        asset = assets[item['id']]
        assert asset['anatomical_review']['status'] == 'pending'
        assert asset['sha256'] == item['unchanged_source_sha256'] == sha(ROOT/asset['local_path'])
        assert asset['local_path'] == item['source_local_path']
        assert not asset['structure_ids'] and not asset.get('requirement_coverage')
        for name, change in item['proposed_dependency_changes'].items():
            assert asset['presentation_dependencies'][name] == change['before']
            assert sha(ROOT/name) == change['after']
            changes.append({'id': asset['id'], 'path': name, **change})
        for name, expected in item['proposed_presentation_dependencies'].items():
            assert sha(ROOT/name) == expected
        preserved = {key: copy.deepcopy(asset.get(key)) for key in item['preserve_fields_exactly']}
        asset['presentation_dependencies'] = item['proposed_presentation_dependencies']
        asset['source_presentation_reconciliation_review'] = {
            **item['proposed_presentation_reconciliation_review'],
            'independent_review_path': str(INDEPENDENT.relative_to(ROOT)),
            'independent_review_sha256': sha(INDEPENDENT),
            'historical_issue_count': item['original_issue_count'],
            'clinical_approval': False, 'fine_anatomical_approval': False,
        }
        if 'proposed_geometry_coordinate_metadata' in item:
            for key, value in item['proposed_geometry_coordinate_metadata'].items():
                assert key not in asset['geometry'] or asset['geometry'][key] == value
                asset['geometry'][key] = value
        for value in item.get('proposed_source_unknowns_append', []):
            unknowns = asset['source_context'].setdefault('unknowns', [])
            if value not in unknowns:
                unknowns.append(value)
        assert all(asset.get(key) == value for key, value in preserved.items())
        preserved_fingerprints[asset['id']] = digest(preserved)
    assert len(changes) == 41
    assert all(old == assets[old['id']] for old in before['assets'] if old['id'] not in ids)
    save(path, evidence)
    save(FOLDER/'applied-presentation-review.json', {
        'contract_sha256': sha(CONTRACT), 'independent_review_sha256': sha(INDEPENDENT),
        'applied_asset_ids': sorted(ids), 'dependency_changes': changes,
        'preserved_field_fingerprints': preserved_fingerprints,
        'historical_issues_retained': 40, 'source_bytes_changed': False,
        'anatomical_or_fidelity_or_coverage_or_licence_fields_changed': False,
        'clinical_approval': False, 'fine_anatomical_approval': False,
    })
    print('20 independently source/presentation-checked assets reconciled; 41 dependency entries, 40 historical issues retained; no anatomical or clinical approval.')


if __name__ == '__main__':
    apply()
