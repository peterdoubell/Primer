"""Integrity and provenance of native source anatomy, not clinical certification."""
import hashlib
import json
from pathlib import Path
import struct
import shutil
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.skipif(shutil.which('node') is None, reason='Node.js is required')
def test_anatomical_orientation_tracks_the_actual_camera():
    result = subprocess.run(['node', '--test', str(ROOT / 'tests/detailed-anatomy-orientation.test.cjs')],
                            cwd=ROOT, capture_output=True, text=True, timeout=15)
    assert result.returncode == 0, result.stdout + result.stderr


def test_native_msk_atlas_keeps_registration_and_source_geometry():
    manifest = json.loads((ROOT / 'web/anatomy/msk-atlas/manifest.json').read_text())
    assert manifest['license'] == 'CC BY-SA 4.0'
    assert manifest['coordinate_system']['display_basis'] == 'native-x-left-y-superior-z-anterior'
    assert manifest['coordinate_system']['unit_meters'] == .01
    assert set(manifest['regions']) == {'shoulder', 'elbow', 'wrist', 'hip', 'knee', 'ankle'}
    for part in manifest['parts'].values():
        data = (ROOT / 'web' / part['file'].removeprefix('/app/')).read_bytes()
        assert hashlib.sha256(data).hexdigest() == part['sha256'], part['id']
        magic, vertices, indices = struct.unpack('<4sII', data[:12])
        assert magic == b'BP3D'
        assert vertices == part['vertices'] and indices == 3 * part['triangles']
        assert len(data) == part['bytes'] == 12 + vertices * 24 + indices * 4
        assert part['source_model_id'] and part['source_geometry_id'] and part['source_sha256']
        assert not part['name'].endswith(('.i', '.j')), 'UI landmark markers are not anatomical meshes'
        if part.get('surface_overlay'):
            assert part['source_part_id'] in manifest['parts']
            assert 'thickness' in part['limitations']
        else:
            assert len(part['world_transform_columns']) == 4
    for name, region in manifest['regions'].items():
        declared_layers = {layer for layer, _ in region['layers']}
        actual_layers = set()
        for entry in region['parts']:
            part = manifest['parts'][entry['id']]
            assert entry['layer'] == part['layer']
            assert name in part['regions']
            actual_layers.add(entry['layer'])
        assert actual_layers == declared_layers
        assert region['source_up_range'][0] < region['focus_bounds'][0][1]
        assert region['source_up_range'][1] > region['focus_bounds'][1][1]


def test_articular_material_regions_are_not_claimed_as_cartilage_volumes():
    manifest = json.loads((ROOT / 'web/anatomy/msk-atlas/manifest.json').read_text())
    cartilage = [part for part in manifest['parts'].values() if part['layer'] == 'cartilage-surface']
    assert cartilage
    for part in cartilage:
        assert part['surface_overlay'] is True
        assert part['source_material'].lower().startswith('cartilage')
        assert 'surface' in part['name']
        assert 'thickness' in part['limitations']
