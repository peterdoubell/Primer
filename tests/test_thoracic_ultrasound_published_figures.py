"""Original thoracic US pixels and honest report state survive module integration."""
import gzip
import hashlib
import json
from pathlib import Path
from PIL import Image
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail, resolve

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / 'docs/thoracic-ultrasound-source-review-20261013'


def test_all_sixteen_original_figures_preserve_bytes_pixels_and_attribution():
    manifest = json.loads((REVIEW / 'manifest.json').read_text())
    package = json.loads((REVIEW / 'integrated-stills.json').read_text())
    originals = {a['id']: a for a in manifest['assets'] if a['kind'] == 'image'}
    assert len(package['figures']) == len(originals) == 16
    for row in package['figures']:
        source = originals[row['source_asset_id']]
        raw = (ROOT / row['local_path']).read_bytes()
        assert raw == (REVIEW / source['path']).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == row['sha256'] == source['sha256']
        with Image.open(ROOT / row['local_path']) as image:
            assert list(image.size) == source['dimensions']
            assert hashlib.sha256(image.tobytes()).hexdigest() == row['decoded_pixel_sha256']
        assert manifest['sources'][source['source']]['authors']
    for source in manifest['sources'].values():
        assert hashlib.sha256(gzip.decompress((REVIEW / source['jats_path']).read_bytes())).hexdigest() == source['jats_sha256']


def test_all_five_steps_have_correct_examples_without_normal_shortcuts():
    ref = detail(Curriculum(), resolve('ra.thoracic-ultrasound'))['radiology_reference']
    package = json.loads((REVIEW / 'integrated-stills.json').read_text())
    assert len(ref['structure_atlas']) == 16
    assert not ref['key_images']
    assert not ref['walkthrough']['start']['module_illustrations']
    assert len(ref['walkthrough']['steps']) == 5
    for i, step in enumerate(ref['walkthrough']['steps']):
        assert set(step['images']) == {r['id'] for r in package['figures'] if i in r['steps']}
        assert not step['normal']
    assert all('not assessed' in s['body'] for s in ref['reporting']['template_sections'])


def test_source_examples_never_grant_anatomical_coverage_or_mix_diagram_with_doppler():
    ref = detail(Curriculum(), resolve('ra.thoracic-ultrasound'))['radiology_reference']
    mixed = next(r for r in ref['structure_atlas'] if r['id'] == 'open-thoracic-us-pmc5401877-fig13')
    assert mixed['clinical_panels'] == ['B', 'C']
    assert mixed['schematic_panels'] == ['A']
    assert mixed['source_context']['panel_types'] == {'A': 'Schematic', 'B': 'Ultrasound', 'C': 'Ultrasound'}
    evidence = json.loads((ROOT / 'data/radiology/radiology-asset-evidence.json').read_text())
    assets = [a for a in evidence['assets'] if a['id'].startswith('open-thoracic-us-')]
    assert len(assets) == 16
    for asset in assets:
        assert not asset['structure_ids'] and not asset['requirement_coverage']
        assert asset['anatomical_review']['status'] == 'pending'
        license = asset['source']['license']
        assert hashlib.sha256((ROOT / license['evidence_path']).read_bytes()).hexdigest() == license['evidence_sha256']


def test_only_thoracic_effective_contract_changes_from_previous_main():
    from tools.check_radiology_fidelity import build_scope
    current = build_scope()
    baseline = json.loads((REVIEW / 'evidence/previous-main-contract-hashes.json').read_text())
    actual = {r['id']: r['reporting_contract_sha256'] for r in current['investigations']}
    assert set(actual) == set(baseline)
    assert [key for key in baseline if baseline[key] != actual[key]] == ['ra.thoracic-ultrasound']
