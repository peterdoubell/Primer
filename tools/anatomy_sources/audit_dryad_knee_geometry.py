#!/usr/bin/env python3
"""Audit unmodified Dryad Raw MRI knee STLs and render native-coordinate reviews.

No remeshing, smoothing, fitted transform, component removal, clinical approval,
or runtime publication. Exact ASCII coordinates are parsed as float64. Topology
uses exact equal positions, without a weld tolerance. Render projections are
explicit coordinate permutations; optional context clipping affects images only.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path
import re
import struct
import zipfile

import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCE = Path('/tmp/primer-msk-sources/dryad-knee')
ARCHIVE_SHA = '873f56215c90634e249ce122cf6f558ce85615d80a708c0c1b45b7b6d7379362'
PARTS = {
    'ACL': ('Anterior cruciate ligament', 'ligament', '#e7b542'),
    'PCL': ('Posterior cruciate ligament', 'ligament', '#7a65c5'),
    'MCL': ('Medial collateral ligament', 'ligament', '#d57858'),
    'LCL': ('Lateral collateral ligament', 'ligament', '#5ba2a8'),
    'Femur_Cartilage': ('Femoral cartilage', 'cartilage', '#ba67a4'),
    'Tibia_cartilage_med': ('Medial tibial cartilage', 'cartilage', '#6b98cb'),
    'Tibial_cartilage_lat': ('Lateral tibial cartilage', 'cartilage', '#6bbdaf'),
    'Medial_Meniscus': ('Medial meniscus', 'meniscus', '#c27c35'),
    'Lateral_Meniscus': ('Lateral meniscus', 'meniscus', '#6f63b4'),
    'Femur': ('Femur', 'bone', '#d6d0c0'),
    'Tibia': ('Tibia source object (README: tibia/fibula)', 'bone', '#c8c7bb'),
    'Patella': ('Patella', 'bone', '#aaa495'),
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def parse_ascii_stl(raw):
    """Keep every source facet and facet normal, including degeneracies."""
    assert raw.lstrip().startswith(b'solid'), 'Expected the source ASCII STL format'
    verts = re.findall(rb'^\s*vertex\s+([^\r\n]+)', raw, re.M)
    norms = re.findall(rb'^\s*facet\s+normal\s+([^\r\n]+)', raw, re.M)
    assert len(verts) == 3 * len(norms) > 0
    triangles = np.fromstring(b' '.join(verts).decode('ascii'), sep=' ').reshape(-1, 3, 3)
    normals = np.fromstring(b' '.join(norms).decode('ascii'), sep=' ').reshape(-1, 3)
    assert len(triangles) == len(normals)
    assert np.isfinite(triangles).all() and np.isfinite(normals).all()
    return triangles, normals


def geometry_stats(triangles, normals):
    crosses = np.cross(triangles[:, 1] - triangles[:, 0], triangles[:, 2] - triangles[:, 0])
    twice_area = np.linalg.norm(crosses, axis=1)
    zero = np.all(crosses == 0, axis=1)
    repeated = (np.all(triangles[:, 0] == triangles[:, 1], axis=1)
                | np.all(triangles[:, 1] == triangles[:, 2], axis=1)
                | np.all(triangles[:, 0] == triangles[:, 2], axis=1))
    # All facets enter the counts and topology. Nothing is silently discarded.
    positions, inverse = np.unique(triangles.reshape(-1, 3), axis=0, return_inverse=True)
    faces = inverse.reshape(-1, 3)
    oriented = np.concatenate((faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]))
    edges, edge_inverse, incidence = np.unique(np.sort(oriented, axis=1), axis=0,
                                              return_inverse=True, return_counts=True)
    balances = np.bincount(edge_inverse, weights=np.where(oriented[:, 0] < oriented[:, 1], 1, -1))
    edge_order = np.argsort(edge_inverse, kind='stable')
    sorted_groups = edge_inverse[edge_order]
    adjacent = sorted_groups[1:] == sorted_groups[:-1]
    edge_faces = np.tile(np.arange(len(faces)), 3)[edge_order]
    graph = coo_matrix((np.ones(int(adjacent.sum()), dtype=np.uint8),
                        (edge_faces[:-1][adjacent], edge_faces[1:][adjacent])),
                       shape=(len(faces), len(faces)))
    count, labels = connected_components(graph, directed=False)
    components = []
    for label in range(count):
        ids = np.flatnonzero(labels == label)
        tri = triangles[ids]
        components.append({
            'triangles': len(ids), 'first_source_facet_index': int(ids[0]),
            'bounds_native': [tri.min((0, 1)).tolist(), tri.max((0, 1)).tolist()],
            'area_native_squared': float(twice_area[ids].sum() / 2),
            'signed_volume_native_cubed': float(np.einsum('ij,ij->i', tri[:, 0],
                                                         np.cross(tri[:, 1], tri[:, 2])).sum() / 6),
            'exact_zero_area_facets': int(zero[ids].sum()),
        })
    components.sort(key=lambda row: (-row['triangles'], row['first_source_facet_index']))
    length = np.linalg.norm(normals, axis=1)
    valid = (~zero) & (length > 0)
    cosine = np.einsum('ij,ij->i', normals[valid], crosses[valid]) / (length[valid] * twice_area[valid])
    angles = np.degrees(np.arccos(np.clip(cosine, -1, 1)))
    _, face_repeats = np.unique(np.sort(faces, axis=1), axis=0, return_counts=True)
    edge_lengths = np.linalg.norm(positions[edges[:, 0]] - positions[edges[:, 1]], axis=1)
    return {
        'source_triangles': len(triangles), 'nonzero_area_facets': int((~zero).sum()),
        'exact_zero_area_facet_indices': np.flatnonzero(zero).tolist(),
        'repeated_vertex_facet_indices': np.flatnonzero(repeated).tolist(),
        'unique_exact_positions': len(positions),
        'unique_exact_edges': len(edges),
        'euler_characteristic': int(len(positions) - len(edges) + len(faces)),
        'bounds_native': [positions.min(0).tolist(), positions.max(0).tolist()],
        'axis_extent_native': np.ptp(positions, axis=0).tolist(),
        'boundary_edges': int((incidence == 1).sum()),
        'nonmanifold_edges': int((incidence > 2).sum()),
        'maximum_edge_incidence': int(incidence.max()),
        'paired_edges_with_inconsistent_direction': int(((incidence == 2) & (balances != 0)).sum()),
        'duplicate_facet_count_ignoring_winding': int(np.maximum(face_repeats - 1, 0).sum()),
        'closed_edge_manifold': bool(np.all(incidence == 2) and not zero.any()),
        'face_components_shared_exact_edges': count, 'components': components,
        'source_normal_zero_count': int((length == 0).sum()),
        'source_normal_length_range': [float(length.min()), float(length.max())],
        'normal_vs_winding_angle_degrees_quantiles_0_50_95_100': np.quantile(angles, [0, .5, .95, 1]).tolist(),
        'source_normals_opposed_to_winding': int((cosine < 0).sum()),
        'edge_length_native_quantiles_0_50_95_100': np.quantile(edge_lengths, [0, .5, .95, 1]).tolist(),
        'facet_area_native_squared_quantiles_0_50_95_100': np.quantile(twice_area / 2, [0, .5, .95, 1]).tolist(),
        'surface_area_native_squared': float(twice_area.sum() / 2),
        'self_intersections_checked': False,
    }


def read_runtime_part(part):
    raw = (ROOT / 'web' / part['file'].removeprefix('/app/')).read_bytes()
    assert sha(raw) == part['sha256']
    payload = gzip.decompress(raw) if raw[:2] == b'\x1f\x8b' else raw
    magic, vertex_count, index_count = struct.unpack('<III', payload[:12])
    assert magic == 0x44335042 and len(payload) == 12 + vertex_count * 24 + index_count * 4
    vertices = np.frombuffer(payload, '<f4', vertex_count * 3, offset=12).reshape(-1, 3)
    normals = np.frombuffer(payload, '<f4', vertex_count * 3, offset=12 + vertex_count * 12).reshape(-1, 3)
    indices = np.frombuffer(payload, '<u4', index_count, offset=12 + vertex_count * 24).reshape(-1, 3)
    triangles = vertices[indices].astype('f8')
    assert np.allclose([triangles.min((0, 1)), triangles.max((0, 1))], part['bounds'], rtol=0, atol=1e-5)
    return triangles, normals[indices[:, 0]].astype('f8')


def run(source, output):
    archive = source / 'STLs.zip'
    assert sha(archive.read_bytes()) == ARCHIVE_SHA
    folder = source / 'extracted/STLs/Raw MRI Scan STLs'
    assert {p.name for p in folder.glob('*.stl')} == {f'S192803_L_knee_{key}_smooth.stl' for key in PARTS}
    geometry, records = {}, []
    with zipfile.ZipFile(archive) as z:
        for key, (label, tissue, color) in PARTS.items():
            path = folder / f'S192803_L_knee_{key}_smooth.stl'
            raw = path.read_bytes()
            member = path.relative_to(source / 'extracted').as_posix()
            assert raw == z.read(member), 'Extracted original does not match archived member'
            triangles, normals = parse_ascii_stl(raw)
            record = {'source_key': key, 'name': label, 'tissue_class': tissue,
                      'source_path': str(path), 'archive_member': member,
                      'sha256': sha(raw), 'bytes': len(raw),
                      'stl_header': raw.splitlines()[0].decode('ascii'),
                      'author_smoothing_disclosed_by_filename': True,
                      'color_for_review_only': color, **geometry_stats(triangles, normals)}
            geometry[key] = triangles
            records.append(record)
            print(key, record['source_triangles'], 'facets;',
                  record['boundary_edges'], 'boundary;', record['nonmanifold_edges'], 'nonmanifold;',
                  [c['triangles'] for c in record['components']], 'components', flush=True)
    result = {
        'schema_version': 1, 'status': 'technical and visual review only; no clinical approval',
        'source_doi': '10.5061/dryad.zkh1893gw', 'source_archive_sha256': ARCHIVE_SHA,
        'expected_source_objects': 12, 'actual_source_objects': len(records),
        'source_labels_match_readme_inventory': True,
        'readme_sha256': sha((source / 'README.md').read_bytes()),
        'coordinate_handling': {
            'native_coordinates_retained': True, 'fitted_registration': False,
            'author_frame_description': 'Original standard MRI scan coordinate system, according to README.',
            'anatomical_axes_and_units': 'Not established by ASCII STL alone; verify MRI MetaImage headers independently.',
            'side': 'left, source filename and README',
        },
        'no_source_geometry_changed': True,
        'topology_method': 'Exact float64 ASCII positions; no tolerance weld; face connectivity across shared edges.',
        'limits': [
            'Filename _smooth and MeshLab header disclose processed surfaces, not untouched voxel boundaries.',
            'The current primary paper validates CT/surface-scan kinematics models, not these Raw MRI surface boundaries.',
            'The paper\'s connector bundles are not labelled subdivisions of these ligament volumes.',
            'No independent patellar-cartilage, tendon, meniscal-root/attachment or fine-ligament component objects in this 12-object set.',
            'Facets and topology cannot establish anatomical correctness or source sampling resolution.',
            'No global self-intersection or MRI tissue-boundary validation in this geometry audit.',
        ],
        'parts': records,
    }
    header_folder = source / 'range-headers'
    if header_folder.exists():
        result['available_image_headers'] = []
        for path in sorted(header_folder.glob('*.mhd')):
            raw = path.read_bytes()
            fields = dict(line.split(' = ', 1) for line in raw.decode('ascii').splitlines() if ' = ' in line)
            result['available_image_headers'].append({
                'path': str(path), 'sha256': sha(raw),
                'fields': {key: fields[key] for key in ('TransformMatrix', 'Offset', 'AnatomicalOrientation',
                                                       'ElementSpacing', 'DimSize', 'ElementType')},
                'limit': 'Header metadata only; does not prove MRI payload completeness or STL coordinate registration.',
            })
    output.mkdir(parents=True, exist_ok=True)
    (output / 'geometry-audit.json').write_text(json.dumps(result, indent=2) + '\n')
    return result, geometry


def render(result, geometry, output):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.collections import PolyCollection
    from matplotlib.colors import to_rgb

    def project(ax, meshes, plane, box=None):
        # Orthographic projections only. Never fit or change relative anatomy.
        u, v, depth, usign, vsign = plane
        for triangles, color, alpha in meshes:
            tri = triangles
            if box is not None:
                tri = tri[((tri >= box[0]) & (tri <= box[1])).all(2).any(1)]
            if not len(tri):
                continue
            order = np.argsort(tri[:, :, depth].mean(1))
            tri = tri[order]
            cross = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
            lengths = np.linalg.norm(cross, axis=1)
            unit = np.divide(cross, lengths[:, None], out=np.zeros_like(cross), where=lengths[:, None] != 0)
            light = .4 + .6 * np.abs(unit[:, depth])
            colors = np.clip(np.array(to_rgb(color))[None, :] * light[:, None], 0, 1)
            xy = tri[:, :, [u, v]] * np.array([usign, vsign])
            ax.add_collection(PolyCollection(xy, facecolors=colors, edgecolors='none', alpha=alpha))
        ax.autoscale_view()
        ax.set_aspect('equal')
        ax.grid(alpha=.15)
        ax.set_xlabel(f'Native {"XYZ"[u]} × {usign}')
        ax.set_ylabel(f'Native {"XYZ"[v]} × {vsign}')

    planes = [(0, 1, 2, 1, 1), (0, 2, 1, 1, 1), (1, 2, 0, 1, 1)]
    groups = [
        ('bone-source-objects', ['Femur', 'Tibia', 'Patella']),
        ('cartilage', ['Femur_Cartilage', 'Tibia_cartilage_med', 'Tibial_cartilage_lat']),
        ('menisci', ['Medial_Meniscus', 'Lateral_Meniscus']),
        ('ligaments', ['MCL', 'LCL', 'ACL', 'PCL']),
    ]
    for group, keys in groups:
        fig, axes = plt.subplots(1, 3, figsize=(16, 6.5), facecolor='white')
        bounds = np.array([np.concatenate([geometry[k].reshape(-1, 3) for k in keys]).min(0),
                           np.concatenate([geometry[k].reshape(-1, 3) for k in keys]).max(0)])
        context_box = bounds + np.array([[-5, -5, -5], [5, 5, 5]])
        for ax, plane in zip(axes, planes):
            meshes = ([] if group == 'bone-source-objects' else
                      [(geometry[k], '#aaa89d', .12) for k in ('Femur', 'Tibia', 'Patella')])
            meshes += [(geometry[k], PARTS[k][2], 1) for k in keys]
            project(ax, meshes, plane, context_box)
            ax.set_title(f'Native {"XYZ"[plane[0]]}{"XYZ"[plane[1]]} projection')
        fig.suptitle(f'Dryad S192803 left knee — {group}, unchanged native surfaces', fontsize=14)
        context_note = ('All source bone facets shown.' if group == 'bone-source-objects'
                        else 'Faint bone context clipped for display only.')
        fig.text(.5, .025, ' · '.join(PARTS[k][0] for k in keys)
                 + '\nSource surfaces are smoothed. ' + context_note + ' No registration or anatomical approval.',
                 ha='center', fontsize=10)
        fig.tight_layout(rect=(0, .10, 1, .94))
        fig.savefig(output / f'{group}-three-planes.png', dpi=160)
        plt.close(fig)

    # Each cartilage/meniscus separately, avoiding inter-object painter-order occlusion.
    keys = ['Femur_Cartilage', 'Tibia_cartilage_med', 'Tibial_cartilage_lat',
            'Medial_Meniscus', 'Lateral_Meniscus', 'ACL', 'PCL', 'MCL', 'LCL']
    fig, axes = plt.subplots(3, 3, figsize=(15, 14), facecolor='white')
    for ax, key in zip(axes.flat, keys):
        plane = planes[0] if PARTS[key][1] != 'ligament' else planes[1]
        project(ax, [(geometry[key], PARTS[key][2], 1)], plane)
        record = next(p for p in result['parts'] if p['source_key'] == key)
        ax.set_title(PARTS[key][0] + f'\n{record["source_triangles"]:,} facets, '
                     + f'{record["face_components_shared_exact_edges"]} component(s)', fontsize=10)
    fig.suptitle('Dryad source objects isolated — axis units remain native, each panel framed independently', fontsize=14)
    fig.tight_layout(rect=(0, 0, 1, .96))
    fig.savefig(output / 'individual-soft-tissue-surfaces.png', dpi=160)
    plt.close(fig)

    manifest_path = ROOT / 'web/anatomy/msk-mri-knee/manifest.json'
    manifest = json.loads(manifest_path.read_text())
    comparisons = [('Menisci', ['Medial_Meniscus', 'Lateral_Meniscus'], ['um-knee-meniscus-knee']),
                   ('Tibial cartilage', ['Tibia_cartilage_med', 'Tibial_cartilage_lat'], ['um-knee-cartilage-tibia']),
                   ('Femoral cartilage', ['Femur_Cartilage'], ['um-knee-cartilage-femur-distal'])]
    fig, axes = plt.subplots(2, 3, figsize=(15, 11), facecolor='white')
    for col, (title, dryad_keys, malaya_keys) in enumerate(comparisons):
        meshes = [(geometry[k], PARTS[k][2], 1) for k in dryad_keys]
        project(axes[0, col], meshes, planes[0])
        axes[0, col].set_title('Dryad left — ' + title)
        meshes = []
        for key in malaya_keys:
            tri, _ = read_runtime_part(manifest['parts'][key])
            meshes.append((tri, '#8a80b0', 1))
        project(axes[1, col], meshes, (0, 1, 2, 1, -1))
        axes[1, col].set_title('Malaya right — ' + title)
    fig.suptitle('Separate subjects / source frames — visual review, not a registered accuracy comparison', fontsize=14)
    fig.text(.5, .015, 'No geometric alignment, smoothing or mirroring. Each panel autoscaled independently.\n'
             'Malaya lower row uses established LPS X/−Y view; Dryad upper row is native XY only.', ha='center')
    fig.tight_layout(rect=(0, .08, 1, .95))
    fig.subplots_adjust(hspace=.4)
    fig.savefig(output / 'dryad-malaya-separate-source-comparison.png', dpi=160)
    plt.close(fig)
    print('Saved render reviews:', output, flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=DEFAULT_SOURCE)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--render', action='store_true')
    args = parser.parse_args()
    output = args.output or args.source / 'geometry-audit'
    result, geometry = run(args.source, output)
    if args.render:
        render(result, geometry, output)
