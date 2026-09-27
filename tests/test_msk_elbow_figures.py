"""Elbow source panels cannot acquire a different modality or clinical approval."""
import copy
import json
from pathlib import Path

import pytest

from tools.check_msk_fidelity import inspect_asset, inspect_binding, requirements_for, review_scope_fingerprint


ROOT = Path(__file__).resolve().parents[1]
IDS = (
    'open-elbow-anterior-ucl-mri-acosta-fig5',
    'open-elbow-posterior-ucl-ulnar-nerve-mri-acosta-fig6',
    'open-elbow-triceps-insertion-mri-valgaeren-fig2',
    'open-elbow-common-flexor-ultrasound-mezian-fig6a',
    'open-elbow-distal-biceps-ultrasound-mezian-fig10a',
    'open-elbow-biceps-attachments-mezian-fig8',
)


def records():
    requirements = json.loads((ROOT / 'data/radiology/msk-structure-requirements.json').read_text())
    investigation = next(i for i in requirements['investigations'] if i['investigation_id'] == 'ra.mri-elbow')
    leaves = {r['id']: r for r in requirements_for(investigation)}
    assets = json.loads((ROOT / 'data/radiology/msk-asset-evidence.json').read_text())['assets']
    return requirements, leaves, {a['id']: a for a in assets}


@pytest.mark.parametrize('identifier,target', [
    (IDS[3], 'elbow.common_flexor_tendon.bony_attachment'),
    (IDS[4], 'elbow.distal_biceps_tendon.tendon_substance'),
])
def test_normal_elbow_ultrasound_cannot_satisfy_mri_leaves(identifier, target):
    _, leaves, assets = records()
    asset = assets[identifier]
    assert asset['structure_ids'] == []
    assert asset['modality'] == 'Ultrasound'
    assert asset['source_context']['selected_panels'] == ['a']
    assert 'clinical_image_modality_not_in_requirement_scope' in inspect_binding(asset, leaves[target])


def test_biceps_attachment_overlay_does_not_credit_dissection_as_schematic():
    _, leaves, assets = records()
    asset = assets[IDS[5]]
    target = leaves['elbow.distal_biceps_tendon.bony_attachment']
    assert asset['source_context']['selected_panels'] == ['e']
    assert asset['representation_selection']['panels'] == ['e']
    assert asset['ancillary_panels_not_credited_as_clinical_images'][0]['panels'] == ['a', 'b', 'c', 'd']
    assert not inspect_binding(asset, target)
    altered = copy.deepcopy(asset)
    altered['source_context']['selected_panels'] = ['a']
    altered['representation_selection']['panels'] = ['a']
    assert 'source_context_selected_panel_not_schematic' in inspect_binding(altered, target)


def test_cmyk_reference_uses_documented_lossless_pdf_colour_rendition():
    from PIL import Image
    import hashlib
    _, _, assets = records()
    asset = assets[IDS[2]]
    path = ROOT / asset['local_path']
    assert path.suffix == '.png'
    assert hashlib.sha256(path.read_bytes()).hexdigest() == asset['sha256']
    image = Image.open(path)
    assert image.mode == 'RGB' and image.size == (1511, 838)
    provenance = asset['pixel_provenance']
    assert provenance['source_encoded_stream_sha256'] == 'b8cbed992b3a68c91bc465f160a5cf12eb8cea9dc4dd99f9e0ad3abf1e33212a'
    assert provenance['original_encoded_stream_preserved_in_runtime'] is False
    assert provenance['no_resampling'] is True
    assert provenance['extra_jpeg_compression'] is False


@pytest.mark.parametrize('identifier', IDS)
def test_source_checked_elbow_assets_remain_unapproved(identifier):
    requirements, leaves, assets = records()
    asset = assets[identifier]
    for target in asset['structure_ids']:
        assert not inspect_binding(asset, leaves[target])
    assert asset['visual_review']['status'] == 'source_checked'
    assert asset['anatomical_review']['status'] == 'pending'
    issues = inspect_asset(asset, ROOT, review_scope_fingerprint(asset, requirements))
    assert 'asset_fingerprint_mismatch' not in issues
    assert 'commercial_rights_unverified' not in issues
    assert 'high_fidelity_unproven' in issues
    assert 'anatomical_review_missing_or_stale' in issues
