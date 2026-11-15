#!/usr/bin/env python3
"""Expose disconnected knee source components without changing any source facet.

The native right-sided LPS frame and nonoverlapping X bounds identify the medial
and lateral components. This is a documented positional interpretation, not an
original separate source label or a clinical approval. No roots, horns or
cartilage sublayers are inferred from connectivity.
"""
from __future__ import annotations
import argparse
import copy
import gzip
import hashlib
import json
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[2]
PARENTS = {
    'um-knee-meniscus-knee': ('meniscus', {2000, 3196}),
    'um-knee-cartilage-tibia': ('tibial-plateau-cartilage', {2772, 3576}),
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def parse(raw):
    magic, nv, ni = struct.unpack('<4sII', raw[:12])
    if magic != b'BP3D' or ni % 3 or len(raw) != 12 + nv * 24 + ni * 4:
        raise ValueError('Invalid native mesh')
    positions = list(struct.iter_unpack('<fff', raw[12:12 + nv * 12]))
    normals = list(struct.iter_unpack('<fff', raw[12 + nv * 12:12 + nv * 24]))
    faces = list(struct.iter_unpack('<III', raw[12 + nv * 24:]))
    return positions, normals, faces


def components(positions, faces):
    """Exact positional edge adjacency, retaining the original face ordering."""
    representatives = list(range(len(faces)))
    def find(i):
        while representatives[i] != i:
            representatives[i] = representatives[representatives[i]]
            i = representatives[i]
        return i
    edges = {}
    for i, face in enumerate(faces):
        corners = [positions[j] for j in face]
        for a, b in zip(corners, corners[1:] + corners[:1]):
            edge = tuple(sorted((a, b)))
            if edge in edges:
                representatives[find(i)] = find(edges[edge])
            else:
                edges[edge] = i
    groups = {}
    for i in range(len(faces)):
        groups.setdefault(find(i), []).append(i)
    return list(groups.values())


def bounds(positions, faces):
    used = {index for face in faces for index in face}
    return [[min(positions[i][axis] for i in used) for axis in range(3)],
            [max(positions[i][axis] for i in used) for axis in range(3)]]


def subset(raw, selected):
    positions, normals, faces = parse(raw)
    retained = [faces[i] for i in selected]
    used = sorted({index for face in retained for index in face})
    remap = {old: new for new, old in enumerate(used)}
    # Copy original float32 bytes, including signed zero and facet-normal seams.
    nv = len(positions)
    out = bytearray(struct.pack('<4sII', b'BP3D', len(used), len(retained) * 3))
    out.extend(b''.join(raw[12 + i * 12:24 + i * 12] for i in used))
    out.extend(b''.join(raw[12 + nv * 12 + i * 12:24 + nv * 12 + i * 12] for i in used))
    out.extend(b''.join(struct.pack('<III', *(remap[i] for i in face)) for face in retained))
    return bytes(out), bounds(positions, retained)


def add_components(manifest, destination):
    if manifest['coordinate_system']['basis'] != 'LPS' or manifest['regions']['knee']['side'] != 'right':
        raise ValueError('Component identities require the verified native right-sided LPS frame')
    records = []
    for parent_id, (kind, expected_counts) in PARENTS.items():
        parent = manifest['parts'][parent_id]
        raw = gzip.decompress((destination / Path(parent['file']).name).read_bytes())
        if sha(raw) != parent['decoded_sha256']:
            raise ValueError('Source parent geometry changed: ' + parent_id)
        positions, normals, faces = parse(raw)
        groups = components(positions, faces)
        if len(groups) != 2 or {len(group) for group in groups} != expected_counts:
            raise ValueError('Unexpected native connected components: ' + parent_id)
        groups.sort(key=lambda group: bounds(positions, [faces[i] for i in group])[0][0])
        extents = [bounds(positions, [faces[i] for i in group]) for group in groups]
        if not extents[0][1][0] < extents[1][0][0]:
            raise ValueError('Medial/lateral component X bounds overlap; identity needs a new review')
        omitted = set(parent['omitted_source_facet_indices'])
        original_indices = [i for i in range(parent['source_triangles']) if i not in omitted]
        if len(original_indices) != len(faces):
            raise ValueError('Source facet correspondence changed')
        children = []
        for side, selected in zip(('lateral', 'medial'), groups):
            child_raw, extent = subset(raw, selected)
            child_id = 'um-knee-' + side + '-' + kind
            filename = child_id + '.bin.gz'
            encoded = gzip.compress(child_raw, compresslevel=9, mtime=0)
            (destination / filename).write_bytes(encoded)
            child = copy.deepcopy({key: value for key, value in parent.items() if key != 'components'})
            title = side.title() + (' meniscus' if kind == 'meniscus' else ' tibial plateau cartilage')
            child.update({
                'id': child_id, 'name': title,
                'file': '/app/anatomy/msk-mri-knee/' + filename,
                'bytes': len(encoded), 'sha256': sha(encoded),
                'decoded_bytes': len(child_raw), 'decoded_sha256': sha(child_raw),
                'vertices': struct.unpack('<I', child_raw[4:8])[0],
                'export_vertices': struct.unpack('<I', child_raw[4:8])[0],
                'triangles': len(selected), 'source_triangles': len(selected),
                'bounds': extent, 'source_bounds_including_empty_facets': extent,
                'omitted_source_facet_indices': [], 'component_count': 1,
                'component_triangles': [len(selected)],
                'fidelity_review': 'pending',
                'identity_interpretation': 'Positional identification of an exact disconnected component in the source right-sided LPS frame; not a separate author-provided segmentation label.',
                'source_component': {
                    'parent_id': parent_id, 'parent_decoded_sha256': parent['decoded_sha256'],
                    'parent_source_triangles': parent['source_triangles'],
                    'parent_render_facet_indices': selected,
                    'original_source_facet_indices': [original_indices[i] for i in selected],
                    'selection': 'Complete native component connected by exact shared positional edges',
                    'identity_basis': 'On this right knee, higher native LPS X is medial. The two component X bounds do not overlap; the fibula and labelled collateral ligaments provide side anchors.',
                    'limitations': 'Whole source component only. No independent horn/root/attachment or cartilage sublayer segmentation; source sampling and smoothing limits remain.',
                },
            })
            # These source-parent measurements must not be inherited as if
            # recomputed for a separately author-labelled component.
            for key in ('volume_native_units_cubed', 'source_unique_positions',
                        'mesh_to_voxel_extent_difference_mm'):
                child.pop(key, None)
            children.append(child)
            records.append({'id': child_id, 'name': title, 'parent_id': parent_id,
                            'triangles': len(selected), 'bounds': extent,
                            'decoded_sha256': child['decoded_sha256'],
                            'retained_positions_and_normals': 'byte-exact subset of parent'})
        parent['components'] = children
    manifest['component_interpretation'] = {
        'method': 'Exact disconnected source components; no geometry fitting, cutting, smoothing or interpolation.',
        'source_label_status': 'Medial/lateral names are positional interpretations of combined author source labels.',
        'new_source_anatomy': False,
        'records': records,
        'review_status': 'source_geometry_checked; anatomical fidelity pending',
    }
    notes = manifest.get('viewer_notes', [])
    combined_note = 'The original combined meniscus and tibial-cartilage labels are displayed as their complete disconnected medial/lateral components, identified by the native right-sided LPS positions. No roots, horns, attachments or cartilage sublayers are independently segmented.'
    if len(notes) > 1:
        notes[1] = 'Cartilage is represented by segmented surfaces enclosing tissue. ' + combined_note
    return records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, default=ROOT / 'web/anatomy/msk-mri-knee/manifest.json')
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text())
    records = add_components(manifest, args.manifest.parent)
    args.manifest.write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps(records, indent=2))


if __name__ == '__main__':
    main()
