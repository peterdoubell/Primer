"""The ankle source subset must preserve geometry and disclose its actual scope."""
import gzip
import hashlib
import json
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[1]


def test_ankle_native_geometry_and_shared_resources_are_exact():
    atlas = json.loads((ROOT / 'web/anatomy/msk-mri-ankle/manifest.json').read_text())
    knee = json.loads((ROOT / 'web/anatomy/msk-mri-knee/manifest.json').read_text())
    assert set(atlas['regions']) == {'ankle'}
    assert atlas['coordinate_system']['basis'] == 'LPS'
    assert atlas['coordinate_system']['units'] == 'millimeters'
    assert atlas['source_archive_sha256'] == knee['source_archive_sha256']
    assert atlas['regions']['ankle']['lazy_layers'] is True
    assert len(atlas['parts']) == 20
    shared = 0
    for part in atlas['parts'].values():
        encoded = (ROOT / 'web' / part['file'].removeprefix('/app/')).read_bytes()
        assert hashlib.sha256(encoded).hexdigest() == part['sha256']
        decoded = gzip.decompress(encoded)
        assert hashlib.sha256(decoded).hexdigest() == part['decoded_sha256']
        magic, vertices, indices = struct.unpack('<4sII', decoded[:12])
        assert magic == b'BP3D' and vertices == part['vertices']
        assert indices == 3 * part['triangles']
        assert len(decoded) == 12 + vertices * 24 + indices * 4
        assert part['source_triangles'] - part['triangles'] == len(part['omitted_source_facet_indices'])
        assert part['source_segmentation']['id']
        if part.get('shared_binary_from'):
            original = knee['parts'][part['shared_binary_from']]
            assert part['file'] == original['file']
            assert part['source_sha256'] == original['source_sha256']
            assert part['decoded_sha256'] == original['decoded_sha256']
            shared += 1
    assert shared == 5


def test_no_ankle_cartilage_or_ligament_volume_is_inferred_from_the_source():
    atlas = json.loads((ROOT / 'web/anatomy/msk-mri-ankle/manifest.json').read_text())
    assert {part['layer'] for part in atlas['parts'].values()} == {'bone', 'tendon', 'muscle'}
    tendons = [part for part in atlas['parts'].values() if part['layer'] == 'tendon']
    assert [part['name'] for part in tendons] == ['Achilles tendon']
    assert atlas['clinical_image_pair']['available'] is False
    assert 'local_image' not in atlas['clinical_image_pair']
    assert 'paired_T2_FS_exported_grid_mm' not in atlas['sampling_limits']
    notes = ' '.join(atlas['viewer_notes'])
    assert 'no ankle-specific mri image stack' in notes.lower()
    assert 'not separately labelled distal tendons' in notes
    region = atlas['regions']['ankle']
    assert tendons[0]['bounds'][1][2] > region['source_up_range'][1]
    assert 'Full structures' in notes


def test_wrist_panels_and_mixed_figures_preserve_display_scope():
    catalog = json.loads((ROOT / 'data/radiology/msk-open-images.json').read_text())
    wrist = catalog['ra.wrist-instability']
    singles = [asset for asset in wrist if asset.get('source_panel')]
    assert {(asset['figure_number'], asset['source_panel']) for asset in singles} == {
        (22, 'a'), (22, 'b'), (24, 'a'), (24, 'b')}
    for asset in singles:
        assert asset['modality'] == 'MR arthrography'
        assert asset['source_caption_full'] != asset['caption']
        assert ('panel ' + asset['source_panel'].upper()) in asset['limits']
    mixed = [asset for asset in wrist if asset.get('contains_schematic_panels')]
    assert len(mixed) == 2
    for asset in mixed:
        assert asset['kind'] == 'clinical-image'
        assert asset['structures_visible'] and asset['schematic_structures_visible']
        assert 'Crespi' in asset['attribution']
