"""Source locators are link-out reading aids; side panels are partial, source-reviewed bindings."""
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ATLAS = ROOT / 'web/radiology/structure-atlas'


def test_locators_only_link_out_and_never_claim_coverage():
    index = json.loads((ATLAS / 'index.json').read_text())
    assert 'not an asset binding' in index['policy'] and 'does not count towards structure coverage' in index['policy']
    assert not [path for path in ATLAS.rglob('*') if path.suffix.lower() in {'.jpg', '.jpeg', '.png', '.webp', '.gif'}]
    totals = dict.fromkeys(index['totals'], 0)
    required = {}
    for name in ('msk', 'non-msk'):
        data = json.loads((ROOT / 'data/radiology' / (name + '-structure-requirements.json')).read_text())
        for investigation in data['investigations']:
            required[investigation['investigation_id']] = [item['id'] for item in investigation['structures']]
    assert {row['investigation_id'] for row in index['investigations']} == set(required)
    for row in index['investigations']:
        detail = json.loads((ATLAS / row['file']).read_text())
        assert [item['id'] for item in detail['structures']] == required[row['investigation_id']]
        counts = dict.fromkeys(totals, 0)
        for item in detail['structures']:
            counts['requirements'] += 1
            counts['atlas'] += 'atlas' in item
            counts['radiology_assistant'] += 'radiology_assistant' in item
            counts['either'] += 'atlas' in item or 'radiology_assistant' in item
            assert not {'structure_ids', 'requirement_coverage', 'extent', 'fidelity'} & set(item)
            if 'atlas' in item:
                labels = index['atlas_labels'][item['atlas']['region']]
                assert item['atlas']['region'] in detail['atlas_regions']
                assert item['atlas']['match'] in {'same_name', 'reviewed_synonym', 'named_parts_only'}
                assert item['atlas']['labels'] and all(labels[label] for label in item['atlas']['labels'])
            for entry in item.get('radiology_assistant', []):
                assert entry['url'].startswith('https://radiologyassistant.nl/') and '#' in entry['url']
                assert entry['url'].split('#')[0] in detail['articles']
                assert entry.get('figure', 'https://radiologyassistant.nl/assets/').startswith(
                    'https://radiologyassistant.nl/assets/')
        assert counts == detail['counts'] == {key: row[key] for key in counts}
        for key in totals:
            totals[key] += counts[key]
    assert totals == index['totals'] and totals['either'] > 600


def test_locator_page_formats_slice_ranges_and_filters():
    script = ("const L=require('./web/radiology/structure-atlas/lab.js');"
              "const a=require('assert');"
              "a.strictEqual(L.ranges([3,4,5,9]),'3–5, 9');"
              "a.strictEqual(L.slices({sag:[1,2],ax:[7]}),'axial 7; sagittal 1–2');"
              "a.strictEqual(L.visible({name:'Patella'},'pat',true),false);"
              "a.strictEqual(L.visible({name:'Patella',atlas:{}},'PAT',true),true);"
              "a.strictEqual(L.safeUrl('https://evil.example/x','https://radiologyassistant.nl/'),null);")
    result = subprocess.run(['node', '-e', script], cwd=ROOT, capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stderr[-2000:]


def test_side_panels_are_partial_sided_bindings_with_an_exact_inverse():
    from tools.anatomy_sources.package_thoracic_us_side_panels import RECEIPT, before_side_panels, records
    from tools.check_msk_fidelity import inspect_binding, inspect_requirement_coverage
    raw = (ROOT / 'data/radiology/radiology-asset-evidence.json').read_bytes()
    receipt = json.loads(RECEIPT.read_text())
    assert receipt['clinical_approval'] is False and receipt['extends_historical_approval'] is False
    from tools.anatomy_sources.package_radiology_assistant_figures import before_radiology_assistant_figures
    from tools.anatomy_sources.bind_stored_caption_assets import before_stored_caption_bindings
    from tools.anatomy_sources.bind_stored_caption_assets_pass2 import before_stored_caption_bindings_pass2
    from tools.anatomy_sources.package_radiology_assistant_sided_figures import before_radiology_assistant_sided_figures as before_sided
    # Publisher figures, then two passes of stored-caption bindings, were added after the panels.
    raw_panels = before_radiology_assistant_figures(before_stored_caption_bindings(before_stored_caption_bindings_pass2(before_sided(raw))))
    assert hashlib.sha256(raw_panels).hexdigest() == receipt['after_sha256']
    assert hashlib.sha256(before_side_panels(raw_panels)).hexdigest() == receipt['before_sha256']
    assert before_side_panels(raw + b'\n') == raw + b'\n'
    assets = {item['id']: item for item in json.loads(raw)['assets']}
    inventory = json.loads((ROOT / 'data/radiology/non-msk-structure-requirements.json').read_text())
    requirements = {item['id']: item for investigation in inventory['investigations']
                    if investigation['investigation_id'] == 'ra.thoracic-ultrasound' for item in investigation['structures']}
    expected = records()
    assert [item['source_context']['laterality'] for item in expected] == ['right', 'left', 'right']
    for item in expected:
        assert assets[item['id']] == item
        assert hashlib.sha256((ROOT / item['local_path']).read_bytes()).hexdigest() == item['sha256']
        assert item['fidelity'] == 'source_reviewed_not_clinically_approved'
        assert item['anatomical_review']['status'] == 'pending'
        (identifier,) = item['structure_ids']
        assert identifier == 'thoracic_ultrasound.%s_diaphragm' % item['source_context']['laterality']
        assert inspect_binding(item, requirements[identifier]) == []
        assert inspect_requirement_coverage(item, requirements[identifier]) == ['requirement_coverage_partial']
    # A panel of one side cannot satisfy the other side's requirement.
    assert 'source_context_laterality_mismatch' in inspect_binding(expected[0], requirements['thoracic_ultrasound.left_diaphragm'])


def test_publisher_figures_are_stored_reviewed_and_bound_as_partial_educational_use_only():
    from tools.anatomy_sources.package_radiology_assistant_figures import (
        RECEIPT, REVIEW, TERMS, before_radiology_assistant_figures, records, requirements)
    from tools.check_msk_fidelity import inspect_binding, inspect_requirement_coverage
    from tools.msk_runtime_rights import license_issues
    raw = (ROOT / 'data/radiology/radiology-asset-evidence.json').read_bytes()
    receipt = json.loads(RECEIPT.read_text())
    assert receipt['clinical_approval'] is False and receipt['extends_historical_approval'] is False
    from tools.anatomy_sources.bind_stored_caption_assets import before_stored_caption_bindings
    from tools.anatomy_sources.bind_stored_caption_assets_pass2 import before_stored_caption_bindings_pass2
    from tools.anatomy_sources.package_radiology_assistant_sided_figures import before_radiology_assistant_sided_figures as before_sided
    # Two passes of stored-caption bindings were added after these figures.
    raw = before_stored_caption_bindings(before_stored_caption_bindings_pass2(before_sided(raw)))
    assert hashlib.sha256(raw).hexdigest() == receipt['after_sha256']
    assert hashlib.sha256(before_radiology_assistant_figures(raw)).hexdigest() == receipt['before_sha256']
    assert 'educational purposes with due credit' in TERMS.read_text()
    review = json.loads(REVIEW.read_text())
    accepted = {row['figure'] for row in review['accepted']}
    assert 'not a radiologist review' in review['reviewer'] and not accepted & set(review['rejected_figures'])
    assets = {item['id']: item for item in json.loads(raw)['assets']}
    required = {}
    for key, value in requirements().items():
        required.setdefault(key[1], []).append(value)
    expected = records()
    assert len(expected) == 77 and sum(len(item['structure_ids']) for item in expected) == 90
    for item in expected:
        assert assets[item['id']] == item and item['source']['asset_url'] in accepted
        assert hashlib.sha256((ROOT / item['local_path']).read_bytes()).hexdigest() == item['sha256']
        licence = item['source']['license']
        # The publisher grants educational reproduction only, and the record says so.
        assert licence['commercial_use'] is False and licence['educational_reproduction'] is True
        assert license_issues(item, ROOT) == ['commercial_rights_unverified']
        assert 'The Radiology Assistant' in licence['attribution'] and item['source']['url'] in licence['attribution']
        assert item['fidelity'] == 'source_reviewed_not_clinically_approved'
        assert item['anatomical_review']['status'] == 'pending'
        for identifier in item['structure_ids']:
            # Shared structure ids: the figure must suit every investigation that lists the structure.
            for requirement in required[identifier]:
                assert inspect_binding(item, requirement) == []
                assert inspect_requirement_coverage(item, requirement) == ['requirement_coverage_partial']
