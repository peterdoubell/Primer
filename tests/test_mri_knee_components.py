"""Disconnected views must partition the source exactly, without synthetic anatomy."""
import gzip
import hashlib
import json
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[1]


def load(part):
    encoded = (ROOT / 'web' / part['file'].removeprefix('/app/')).read_bytes()
    assert hashlib.sha256(encoded).hexdigest() == part['sha256']
    raw = gzip.decompress(encoded)
    assert hashlib.sha256(raw).hexdigest() == part['decoded_sha256']
    magic, nv, ni = struct.unpack_from('<4sII', raw)
    assert magic == b'BP3D' and ni == part['triangles'] * 3
    assert len(raw) == 12 + nv * 24 + ni * 4
    faces = list(struct.iter_unpack('<III', raw[12 + nv * 24:]))
    # Preserve bit identity (including negative zero), rather than merely
    # comparing close numerical coordinates after resampling or smoothing.
    corners = [tuple((raw[12 + i * 12:24 + i * 12],
                      raw[12 + nv * 12 + i * 12:24 + nv * 12 + i * 12])
                     for i in face) for face in faces]
    return raw, corners


def test_components_partition_every_parent_facet_and_normal_exactly():
    manifest = json.loads((ROOT / 'web/anatomy/msk-mri-knee/manifest.json').read_text())
    parents = [p for p in manifest['parts'].values() if p.get('components')]
    assert {p['id'] for p in parents} == {'um-knee-meniscus-knee', 'um-knee-cartilage-tibia'}
    assert len(manifest['parts']) == 28  # Original source objects remain reviewable.
    for parent in parents:
        _, parent_corners = load(parent)
        selected_all = []
        original_retained = [i for i in range(parent['source_triangles'])
                             if i not in parent['omitted_source_facet_indices']]
        assert len(parent['components']) == 2
        for child in parent['components']:
            _, child_corners = load(child)
            provenance = child['source_component']
            selected = provenance['parent_render_facet_indices']
            assert selected == sorted(set(selected))
            assert child_corners == [parent_corners[i] for i in selected]
            assert provenance['original_source_facet_indices'] == [original_retained[i] for i in selected]
            assert provenance['parent_decoded_sha256'] == parent['decoded_sha256']
            assert provenance['parent_id'] == parent['id']
            assert child['source_sha256'] == parent['source_sha256']
            assert child['source_segmentation'] == parent['source_segmentation']
            assert child['geometry_transform'] == parent['geometry_transform']
            assert child['fidelity_review'] == 'pending'
            assert 'not a separate author-provided segmentation label' in child['identity_interpretation']
            assert 'No independent horn/root/attachment' in provenance['limitations']
            selected_all.extend(selected)
        assert sorted(selected_all) == list(range(parent['triangles']))
        assert len(set(selected_all)) == len(selected_all)
        lateral, medial = parent['components']
        assert lateral['name'].startswith('Lateral') and medial['name'].startswith('Medial')
        assert lateral['bounds'][1][0] < medial['bounds'][0][0]


def test_display_replaces_combined_entries_without_duplicate_surface_geometry():
    manifest = json.loads((ROOT / 'web/anatomy/msk-mri-knee/manifest.json').read_text())
    original = [manifest['parts'][p['id']] for p in manifest['regions']['knee']['parts']]
    displayed = [component for p in original for component in p.get('components', [p])]
    assert len(displayed) == 30
    assert len({p['id'] for p in displayed}) == 30
    assert sum(p['triangles'] for p in displayed) == sum(p['triangles'] for p in original) == 1_307_872
    assert len({p['file'] for p in displayed}) == 30
    for parent in original:
        if parent.get('components'):
            assert parent['id'] not in {p['id'] for p in displayed}
    assert manifest['component_interpretation']['new_source_anatomy'] is False
    assert 'No roots, horns, attachments or cartilage sublayers' in manifest['viewer_notes'][1]
