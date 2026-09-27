"""Local tendon courses retain source pixels, colour interpretation and limits."""
import hashlib
import json
from pathlib import Path

from PIL import Image

from tools.check_msk_fidelity import inspect_binding, inspect_asset, requirements_for, review_scope_fingerprint

ROOT = Path(__file__).resolve().parents[1]
IDENTIFIER = 'open-hip-rectus-femoris-course-mecho-fig2'


def records():
    catalog = json.loads((ROOT / 'data/radiology/msk-open-images.json').read_text())
    image = next(x for x in catalog['ra.hip-fai'] if x['id'] == IDENTIFIER)
    assets = json.loads((ROOT / 'data/radiology/msk-asset-evidence.json').read_text())['assets']
    asset = next(x for x in assets if x['id'] == IDENTIFIER)
    requirements = json.loads((ROOT / 'data/radiology/msk-structure-requirements.json').read_text())
    hip = next(x for x in requirements['investigations'] if x['investigation_id'] == 'ra.hip-fai')
    return image, asset, requirements, hip


def test_native_rgb_samples_and_external_pdf_profile_are_both_preserved():
    image, asset, _, _ = records()
    path = ROOT / asset['local_path']
    assert hashlib.sha256(path.read_bytes()).hexdigest() == image['sha256'] == asset['sha256'] == 'eed1b91fbad07776381ff56a87d803df49b7a85180c42d04c2fd19e22aec7f8c'
    original = ROOT / 'docs/msk-hip-tendon-source-review/source-jpeg-requires-pdf-icc.jpg'
    assert hashlib.sha256(original.read_bytes()).hexdigest() == 'b56ea4409170775290ae27d3a74e1b73e121371f97c78610225c2623f0a5b9d8'
    with Image.open(original) as source, Image.open(path) as displayed:
        source.load(); displayed.load()
        assert source.size == displayed.size == (image['width'], image['height']) == (1805, 502)
        assert source.mode == displayed.mode == 'RGB'
        assert displayed.tobytes() == source.tobytes()
        assert hashlib.sha256(displayed.tobytes()).hexdigest() == 'c29914e081bdc6e3570a60ffdcc04091ca791d5faec16defc83dfbd0ad9c8af3'
        assert hashlib.sha256(displayed.info['icc_profile']).hexdigest() == 'e5f6ffb83b6d3491301dd750975684cc5cc2a1951c994a14b08cfdaa0d75a041'
    assert image['pixel_provenance'] == asset['pixel_provenance']
    assert image['pixel_provenance']['independent_poppler_raw_jpeg_byte_match']


def test_local_course_does_not_inherit_attachments_or_normality():
    image, asset, requirements, hip = records()
    assert image['clinical_panels'] == asset['source_context']['selected_panels'] == ['a', 'b']
    assert asset['representation_selection']['panels'] == ['a', 'b']
    assert asset['structure_ids'] == ['hip.rectus_femoris_tendon.visible_course']
    assert asset['source_context']['depicted_state'] == 'unknown'
    assert asset['source_context']['laterality'] == 'not_reported'
    assert asset['source_context']['population']['life_stage'] == 'unknown'
    leaves = {x['id']: x for x in requirements_for(hip)}
    assert 'hip.rectus_femoris_tendon.attachment' in leaves
    assert inspect_binding(asset, leaves[asset['structure_ids'][0]]) == []
    assert asset['anatomical_review']['status'] == 'pending'
    issues = inspect_asset(asset, ROOT, review_scope_fingerprint(asset, requirements))
    assert 'asset_fingerprint_mismatch' not in issues
    assert 'commercial_rights_unverified' not in issues
    assert 'high_fidelity_unproven' in issues
    assert 'anatomical_review_missing_or_stale' in issues


def test_boutin_complete_figures_keep_local_scope_and_pdf_rendering():
    from primer.radiology_catalog import _structure_atlases
    catalog = _structure_atlases()['ra.hip-fai']
    assets = json.loads((ROOT / 'data/radiology/msk-asset-evidence.json').read_text())['assets']
    _, _, requirements, hip = records()
    leaves = {x['id']: x for x in requirements_for(hip)}
    for number, leaf, panels, state in [
        ('6.5', 'hip.proximal_hamstring_tendons.visible_course', ['a'], 'normal_anatomical_reference'),
        ('6.7', 'hip.iliopsoas_tendon.visible_course', ['a', 'b'], 'mixed'),
    ]:
        identifier = 'open-hip-tendon-boutin-fig' + number.replace('.', '-')
        image = next(x for x in catalog if x['id'] == identifier)
        asset = next(x for x in assets if x['id'] == identifier)
        assert image['figure_number'] == number
        assert asset['structure_ids'] == [leaf]
        assert asset['source_context']['selected_panels'] == panels
        assert asset['source_context']['depicted_state'] == state
        assert inspect_binding(asset, leaves[leaf]) == []
        assert asset['anatomical_review']['status'] == 'pending'
        issues = inspect_asset(asset, ROOT, review_scope_fingerprint(asset, requirements))
        assert 'high_fidelity_unproven' in issues
        assert 'commercial_rights_unverified' not in issues
        assert 'asset_fingerprint_mismatch' not in issues
        path = ROOT / asset['local_path']
        assert hashlib.sha256(path.read_bytes()).hexdigest() == image['pixel_provenance']['output_sha256']
        with Image.open(path) as rendered:
            assert rendered.size == (image['width'], image['height'])
            assert rendered.info['icc_profile'] == (ROOT / 'docs/msk-boutin-hip-source-review/render-srgb.icc').read_bytes()
        assert 'resampling' in image['pixel_provenance']['method']
        assert 'source_decoded_rgb_sha256' not in image['pixel_provenance']
