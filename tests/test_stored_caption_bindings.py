import json
import subprocess
from pathlib import Path

from tools.anatomy_sources import bind_stored_caption_assets as tool
from tools.anatomy_sources.bind_stored_caption_assets_pass2 import before_stored_caption_bindings_pass2
from tools.anatomy_sources.package_radiology_assistant_sided_figures import before_radiology_assistant_sided_figures as before_sided
from tools.check_msk_fidelity import inspect_binding

ROOT = Path(__file__).resolve().parents[1]


def test_stored_figures_are_bound_only_to_structures_their_own_caption_names():
    review = json.loads(tool.REVIEW.read_text())
    assets = {item['id']: item for item in json.loads(tool.EVIDENCE.read_text())['assets']}
    described = tool.captions()
    required = {}
    for name in ('msk', 'non-msk'):
        data = json.loads((ROOT / 'data/radiology' / (name + '-structure-requirements.json')).read_text())
        for investigation in data['investigations']:
            for structure in investigation['structures']:
                required.setdefault(structure['id'], []).append(structure)
    assert len(review['accepted']) == 29 and len({row['asset_id'] for row in review['accepted']}) == 21
    assert 'not a radiologist review' in review['reviewer']
    for row in review['accepted']:
        asset = assets[row['asset_id']]
        assert row['structure_id'] in asset['structure_ids']
        coverage = asset['requirement_coverage'][row['structure_id']]
        assert coverage['extent'] == 'partial'
        # The second pass rewrote quotes that had lost a first letter or were cut mid-word.
        assert coverage['basis'] == tool.basis(tool.quote(described[row['asset_id']], row['name'], row.get('prefer')))
        assert asset['anatomical_review']['status'] != 'approved'
        for requirement in required[row['structure_id']]:
            assert inspect_binding(asset, requirement) == []
    # Diagnoses are not anatomy: no figure of a disease is bound to a condition requirement.
    assert all('myelopathy' not in row['asset_id'] for row in review['accepted'])
    assert any('diagnosis' in row['reason'] for row in review['rejected'])


def test_stored_caption_bindings_have_an_exact_inverse():
    receipt = json.loads(tool.RECEIPT.read_text())
    raw = before_stored_caption_bindings_pass2(before_sided(tool.EVIDENCE.read_bytes()))  # A second pass followed.
    assert tool.sha(raw) == receipt['after_sha256']
    before = tool.before_stored_caption_bindings(raw)
    assert tool.sha(before) == receipt['before_sha256']
    assert tool.before_stored_caption_bindings(before) == before
    assert receipt['clinical_approval'] is False and receipt['extends_historical_approval'] is False
    changed = {row['asset_id'] for row in json.loads(tool.REVIEW.read_text())['accepted']}
    old, new = json.loads(before)['assets'], json.loads(raw)['assets']
    assert len(old) == len(new)
    for a, b in zip(old, new):
        if a['id'] not in changed:
            assert a == b
        else:
            assert {k: v for k, v in a.items() if k not in ('structure_ids', 'requirement_coverage')} == \
                {k: v for k, v in b.items() if k not in ('structure_ids', 'requirement_coverage')}
