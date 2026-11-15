#!/usr/bin/env python3
"""Independent original-STL audit of the published knee component subsets.

Does not import the splitter, alter manifests, or confer anatomical approval.
Reports exact float32 byte identity separately from source fidelity.
"""
import collections
import gzip
import hashlib
import json
from pathlib import Path
import struct
import zipfile

import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parents[2]
STAGE = Path('/tmp/primer-msk-sources/high-fidelity')
OUT = STAGE / 'malaya-knee/component-audit'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read_binary(part):
    encoded = (ROOT / 'web' / part['file'].removeprefix('/app/')).read_bytes()
    assert sha(encoded) == part['sha256']
    raw = gzip.decompress(encoded)
    assert sha(raw) == part['decoded_sha256']
    magic, nv, ni = struct.unpack_from('<4sII', raw)
    assert magic == b'BP3D' and len(raw) == 12 + nv * 24 + ni * 4
    positions = np.frombuffer(raw, '<f4', nv * 3, 12).reshape(-1, 3)
    normals = np.frombuffer(raw, '<f4', nv * 3, 12 + nv * 12).reshape(-1, 3)
    faces = np.frombuffer(raw, '<u4', ni, 12 + nv * 24).reshape(-1, 3)
    assert len(faces) == part['triangles']
    return raw, positions, normals, faces


def main():
    OUT.mkdir(exist_ok=True)
    manifest_path = ROOT / 'web/anatomy/msk-mri-knee/manifest.json'
    manifest = json.loads(manifest_path.read_text())
    archive_path = STAGE / 'um-final-model-stl.zip'
    assert sha(archive_path.read_bytes()) == manifest['source_archive_sha256']
    records = []
    with zipfile.ZipFile(archive_path) as archive:
        for parent in manifest['parts'].values():
            if not parent.get('components'):
                continue
            source = archive.read(parent['source_member'])
            assert sha(source) == parent['source_sha256']
            source_count = struct.unpack_from('<I', source, 80)[0]
            assert len(source) == 84 + source_count * 50
            assert source_count == parent['source_triangles']
            raw_parent, pv, pn, pf = read_binary(parent)
            covered, render_covered = [], []
            for child in parent['components']:
                raw, vertices, normals, faces = read_binary(child)
                nv = len(vertices)
                provenance = child['source_component']
                source_ids = provenance['original_source_facet_indices']
                render_ids = provenance['parent_render_facet_indices']
                assert len(faces) == len(source_ids) == len(render_ids)
                for triangle, source_id, render_id in zip(faces, source_ids, render_ids):
                    offset = 84 + source_id * 50
                    normal_bytes = source[offset:offset + 12]
                    for corner, index in enumerate(triangle):
                        expected = source[offset + 12 + corner * 12:offset + 24 + corner * 12]
                        assert raw[12 + index * 12:24 + index * 12] == expected
                        assert raw[12 + nv * 12 + index * 12:24 + nv * 12 + index * 12] == normal_bytes
                    assert vertices[triangle].tobytes() == pv[pf[render_id]].tobytes()
                    assert normals[triangle].tobytes() == pn[pf[render_id]].tobytes()
                covered.extend(source_ids); render_covered.extend(render_ids)
                # Weld only numerically identical source positions, rather than
                # the split export's normal-separated vertices or a tolerance.
                unique, inverse = np.unique(vertices, axis=0, return_inverse=True)
                welded = inverse[faces]
                mesh = trimesh.Trimesh(vertices=unique, faces=welded, process=False)
                adjacency = collections.defaultdict(list)
                for left, right in mesh.face_adjacency:
                    adjacency[int(left)].append(int(right))
                    adjacency[int(right)].append(int(left))
                reached, queue = {0}, [0]
                for face in queue:
                    for neighbor in adjacency[face]:
                        if neighbor not in reached:
                            reached.add(neighbor); queue.append(neighbor)
                assert len(reached) == len(faces), 'Each child is one exact-edge connected component'
                lengths = np.linalg.norm(normals, axis=1)
                assert bool(mesh.is_watertight) == child['watertight']
                assert bool(mesh.is_winding_consistent) == child['winding_consistent']
                assert float(lengths.min()) == child['normal_length_min']
                assert float(lengths.max()) == child['normal_length_max']
                assert np.array_equal(vertices.min(axis=0), np.array(child['bounds'][0], dtype='<f4'))
                assert np.array_equal(vertices.max(axis=0), np.array(child['bounds'][1], dtype='<f4'))
                area_twice = np.linalg.norm(np.cross(vertices[faces[:, 1]].astype(float) - vertices[faces[:, 0]],
                                                     vertices[faces[:, 2]].astype(float) - vertices[faces[:, 0]]), axis=1)
                assert np.count_nonzero(area_twice == 0) == child['degenerate_triangles'] == 0
                for field in ('volume_native_units_cubed', 'source_unique_positions',
                              'mesh_to_voxel_extent_difference_mm'):
                    assert field not in child
                assert child['fidelity_review'] == 'pending'
                records.append({'id': child['id'], 'triangles': len(faces),
                    'decoded_sha256': sha(raw), 'original_stl_corner_bytes_exact': True,
                    'original_stl_facet_normal_bytes_exact': True,
                    'source_component_records_parent_label': child['source_segmentation']['name'],
                    'watertight_recomputed': bool(mesh.is_watertight),
                    'winding_consistent_recomputed': bool(mesh.is_winding_consistent),
                    'edge_connected_components_recomputed': 1,
                    'normal_length_bounds_recomputed': [float(lengths.min()), float(lengths.max())],
                    'centroid_native_mm': mesh.centroid.tolist(),
                    'volume_recomputed_for_audit_only_mm3': float(mesh.volume),
                    'bounds_native_mm': child['bounds']})
            omitted = set(parent['omitted_source_facet_indices'])
            assert sorted(covered) == [i for i in range(source_count) if i not in omitted]
            assert len(covered) == len(set(covered))
            assert sorted(render_covered) == list(range(len(pf)))
            for source_id in omitted:
                q = np.frombuffer(source, '<f4', 9, 84 + source_id * 50 + 12).reshape(3, 3).astype(float)
                assert np.all(np.cross(q[1] - q[0], q[2] - q[0]) == 0)
                assert any(np.array_equal(q[a], q[b]) for a, b in ((0, 1), (0, 2), (1, 2)))
    anchors = []
    for identifier in ('um-knee-bone-fibula', 'um-knee-ligament-lcl', 'um-knee-ligament-mcl'):
        _, points, _, _ = read_binary(manifest['parts'][identifier])
        if identifier.endswith('fibula'):
            points = points[points[:, 2] > -380]  # Explicit proximal inspection window only.
        anchors.append({'id': identifier, 'native_x_range_mm': [float(points[:, 0].min()), float(points[:, 0].max())],
                        'native_median_x_mm': float(np.median(points[:, 0]))})
    lateral_x = [r['centroid_native_mm'][0] for r in records if 'lateral' in r['id']]
    medial_x = [r['centroid_native_mm'][0] for r in records if 'medial' in r['id']]
    assert anchors[1]['native_median_x_mm'] < min(lateral_x) < max(lateral_x) < min(medial_x) < max(medial_x) < anchors[2]['native_median_x_mm']
    report = {'status': 'Source-subset and positional identity checks pass; anatomical fidelity remains unapproved',
              'manifest_sha256': sha(manifest_path.read_bytes()),
              'source_archive_sha256': manifest['source_archive_sha256'],
              'retained_child_triangles': sum(record['triangles'] for record in records),
              'records': records, 'side_anchors': anchors,
              'limitations': 'Exact source retention and coherent side assignment do not validate MRI segmentation boundaries, horns, roots, attachments, cartilage layers, or clinical suitability.'}
    (OUT / 'independent-component-audit.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
