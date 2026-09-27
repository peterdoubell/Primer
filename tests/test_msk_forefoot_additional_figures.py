"""Normal forefoot adjuncts retain native pixels and cannot acquire MRI/site credit."""
import hashlib
import json
from pathlib import Path

import pytest
from PIL import Image

from tools.check_msk_fidelity import (
    inspect_asset, inspect_binding, requirements_for, review_scope_fingerprint,
)


ROOT = Path(__file__).resolve().parents[1]
MAAS = 'open-forefoot-lesser-mtp-schematic-maas-fig2'
CHEN = 'open-forefoot-second-fdl-ultrasound-chen-fig7c'


def records():
    catalog = json.loads((ROOT / 'data/radiology/msk-open-images.json').read_text())
    images = {image['id']: image for image in catalog['ra.mri-diabetic-foot']}
    ledger = json.loads((ROOT / 'data/radiology/msk-asset-evidence.json').read_text())
    assets = {asset['id']: asset for asset in ledger['assets']}
    requirements = json.loads((ROOT / 'data/radiology/msk-structure-requirements.json').read_text())
    foot = next(item for item in requirements['investigations']
                if item['investigation_id'] == 'ra.mri-diabetic-foot')
    return images, assets, foot


@pytest.mark.parametrize('identifier,filename,size,fingerprint', [
    (MAAS, 'forefoot-lesser-mtp-schematic-maas-fig2.jpg', (1420, 963),
     '2c683969e02f03a17d94db4f4333ffcda48f00d11ad0ebe11b8b7b852f977d01'),
    (CHEN, 'forefoot-second-fdl-ultrasound-chen-fig7c.png', (1398, 704),
     '89dce1a38224f0db8933c829353b88a74de96c6c4b59ba0b8c09580a9cd053d5'),
])
def test_runtime_artifacts_preserve_independently_checked_native_source(
        identifier, filename, size, fingerprint):
    images, assets, _ = records()
    image, asset = images[identifier], assets[identifier]
    path = ROOT / 'web/reference-media/msk-open' / filename
    assert image['src'] == '/app/reference-media/msk-open/' + filename
    assert asset['local_path'] == str(path.relative_to(ROOT))
    # These constants come from the encoded PDF stream / lossless native panel,
    # independently compared with Poppler, rather than from the mutable catalog.
    assert hashlib.sha256(path.read_bytes()).hexdigest() == fingerprint
    assert image['sha256'] == asset['sha256'] == fingerprint
    with Image.open(path) as raster:
        assert raster.size == (image['width'], image['height']) == size
        raster.load()
    provenance = asset['pixel_provenance']
    for field in ('source_pdf_sha256', 'source_pdf_page', 'source_pdf_image',
                  'width', 'height'):
        assert provenance[field] == image[field]


def test_generic_lesser_mtp_schematic_is_a_whole_figure_without_digit_claims():
    images, assets, foot = records()
    image, asset = images[MAAS], assets[MAAS]
    assert image['kind'] == asset['kind'] == 'schematic'
    assert image['modality'] == asset['modality'] == 'Schematic'
    assert image['figure_number'] == 2
    assert image['source_pdf_page'] == 5 and image['source_pdf_image'] == '/Im4'
    assert image['source_pdf_sha256'] == '2b16d950bef3ddd024169e96f6914386ec5eb054672b7fece276e8a17d2994ab'
    assert not image.get('source_panel') and not image.get('clinical_panels')
    assert not asset.get('representation_selection', {}).get('panels')
    assert not image.get('anatomical_digit')
    assert not asset['source_context'].get('anatomical_site', {}).get('digit')
    assert not asset['source_context'].get('anatomical_site', {}).get('joint')
    assert not asset.get('requirement_binding_evidence')
    for identifier in ('diabetic_foot.lesser_mtp_plantar_plates',
                       'diabetic_foot.lesser_mtp_collateral_complexes'):
        structure = next(s for s in foot['structures'] if s['id'] == identifier)
        assert structure['requires_site_instantiation']
        assert set(structure['required_site_ids']) == {'mtp2', 'mtp3', 'mtp4', 'mtp5'}


def test_second_fdl_panel_is_ultrasound_not_mri_or_mtp_plate_coverage():
    images, assets, foot = records()
    image, asset = images[CHEN], assets[CHEN]
    assert image['kind'] == 'clinical-image' and asset['kind'] == 'clinical_image'
    assert image['modality'] == asset['modality'] == 'Ultrasound'
    assert image['anatomical_digit'] == 2 and image['source_panel'] == 'c'
    assert image['figure_number'] == 7
    assert image['source_pdf_page'] == 7 and image['source_pdf_image'] == '/Im11 /Im26'
    assert image['source_pdf_sha256'] == 'f205b6f7bdb729fda74cfd6c28211e6b6952965f2775f9d152d35d0315fe9565'
    assert asset['source_context']['selected_panels'] == ['c']
    assert asset['representation_selection'] == {'kind': 'clinical_image', 'panels': ['c']}
    assert asset['source_context']['panel_types']['c'] == 'Ultrasound'
    assert str(asset['source_context']['anatomical_site']['digit']) == '2'
    assert not image.get('clinical_panels') and not image.get('schematic_panels')
    assert not asset.get('requirement_binding_evidence')
    with Image.open(ROOT / asset['local_path']) as raster:
        pixels = hashlib.sha256(raster.convert('RGB').tobytes()).hexdigest()
    assert pixels == image['decoded_source_pixels_sha256'] == image['decoded_saved_pixels_sha256']
    assert pixels == 'e66877c209db2981481e51ee409c715bc8b75f69c293ce6a6af1ffb70095da26'
    leaves = {part['id']: part for part in requirements_for(foot)}
    target = leaves['diabetic_foot.flexor_digitorum_longus_tendons.distal_attachment']
    assert target['modality_scope'] == ['MRI']
    assert 'clinical_image_modality_not_in_requirement_scope' in inspect_binding(asset, target)


@pytest.mark.parametrize('identifier', [MAAS, CHEN])
def test_additional_references_remain_unbound_and_clinically_unapproved(identifier):
    images, assets, foot = records()
    image, asset = images[identifier], assets[identifier]
    assert asset['investigation_ids'] == ['ra.mri-diabetic-foot']
    assert asset['structure_ids'] == []
    assert asset['anatomical_review']['status'] == 'pending'
    assert image['license'] == asset['source']['license']['name'] == 'CC BY 4.0'
    assert image['license_url'] == asset['source']['license']['url'] == 'https://creativecommons.org/licenses/by/4.0/'
    fingerprint = review_scope_fingerprint(asset, {'investigations': [foot]})
    issues = inspect_asset(asset, ROOT, fingerprint)
    assert 'asset_fingerprint_mismatch' not in issues
    assert 'commercial_rights_unverified' not in issues
    assert 'high_fidelity_unproven' in issues
    assert 'anatomical_review_missing_or_stale' in issues
