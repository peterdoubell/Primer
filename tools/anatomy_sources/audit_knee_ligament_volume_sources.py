"""Bounded, non-promoting review of the already published Z-Anatomy OPL object.

Reads exact native FBX geometry and the published BP3D buffer; does not fit,
repair, smooth, subdivide, infer partitions, or modify any runtime asset.
NumPy/Matplotlib are review dependencies, not production dependencies.
"""
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import struct
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.anatomy_sources.inspect_fbx import child, load_fbx

STAGE = ROOT / '.research/knee-ligament-volume-sources'
OUT = ROOT / 'docs/msk-knee-ligament-volume-source-review'
SOURCE = STAGE / 'z-anatomy-Joints100.fbx'
SOURCE_SHA = 'f4ba7a910cdaef99e31530f368628780d9f06b5d77853f8b721f47f67137e823'
OPL_ID = 'za-joints-711785439'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_part(part):
    path = ROOT / 'web' / part['file'].removeprefix('/app/')
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != part['sha256']:
        raise ValueError('Published buffer hash mismatch')
    magic, nv, ni = struct.unpack_from('<4sII', raw)
    if magic != b'BP3D' or len(raw) != 12 + nv * 24 + ni * 4:
        raise ValueError('Invalid buffer')
    positions = np.frombuffer(raw, '<f4', nv * 3, 12).reshape(-1, 3)
    indices = np.frombuffer(raw, '<u4', ni, 12 + nv * 24).reshape(-1, 3)
    if np.any(indices >= nv) or not np.isfinite(positions).all():
        raise ValueError('Invalid coordinates or indices')
    return positions, indices


def topology(polygons):
    incidence = Counter()
    directions = defaultdict(list)
    neighbors = defaultdict(set)
    used = set()
    for polygon in polygons:
        used.update(polygon)
        for a, b in zip(polygon, polygon[1:] + polygon[:1]):
            edge = tuple(sorted((a, b)))
            incidence[edge] += 1
            directions[edge].append((a, b))
            neighbors[a].add(b)
            neighbors[b].add(a)
    remaining = set(used)
    components = []
    while remaining:
        stack = [remaining.pop()]
        count = 0
        while stack:
            v = stack.pop()
            count += 1
            for other in neighbors[v]:
                if other in remaining:
                    remaining.remove(other)
                    stack.append(other)
        components.append(count)
    return {
        'referenced_positions': len(used),
        'faces': len(polygons),
        'edges': len(incidence),
        'boundary_edges': sum(n == 1 for n in incidence.values()),
        'nonmanifold_edges': sum(n > 2 for n in incidence.values()),
        'inconsistently_wound_edge_pairs': sum(
            len(d) == 2 and d[0] == d[1] for d in directions.values()),
        'euler_characteristic': len(used) - len(incidence) + len(polygons),
        'vertex_connected_components': sorted(components, reverse=True),
        'face_sizes': dict(Counter(map(len, polygons))),
    }


def main():
    if digest(SOURCE) != SOURCE_SHA:
        raise ValueError('Native source hash mismatch')
    manifest_path = ROOT / 'web/anatomy/msk-atlas/manifest.json'
    manifest = json.loads(manifest_path.read_text())
    part = manifest['parts'][OPL_ID]
    version, nodes = load_fbx(SOURCE)
    objects = next(n for n in nodes if n['name'] == 'Objects')['children']
    native_geometry = next(n for n in objects if n['name'] == 'Geometry'
                           and n['properties'][0] == part['source_geometry_id'])
    native_model = next(n for n in objects if n['name'] == 'Model'
                        and n['properties'][0] == part['source_model_id'])
    local = np.asarray(child(native_geometry, 'Vertices')['properties'][0]).reshape(-1, 3)
    flat = child(native_geometry, 'PolygonVertexIndex')['properties'][0]
    polygons, current = [], []
    for v in flat:
        current.append(int(v) if v >= 0 else -int(v) - 1)
        if v < 0:
            polygons.append(current)
            current = []
    if current:
        raise ValueError('Unterminated polygon')
    matrix = np.asarray(part['world_transform_columns'], dtype=float).T
    source_world = np.column_stack([local, np.ones(len(local))]) @ matrix.T
    positions, faces = load_part(part)
    unique, inverse = np.unique(positions, axis=0, return_inverse=True)
    if not np.array_equal(np.unique(source_world.astype('<f4'), axis=0), unique):
        raise ValueError('Native world-position set differs from published object')
    source_position_ids = {tuple(v): i for i, v in enumerate(source_world.astype('<f4'))}
    mapped = [[source_position_ids[tuple(positions[i])] for i in f] for f in faces]

    def cyclic(face):
        return min(tuple(face[i:] + face[:i]) for i in range(len(face)))

    exported_faces = Counter(cyclic(f) for f in mapped)
    for polygon in polygons:
        if len(polygon) != 4:
            raise ValueError('Unexpected native polygon size for bounded OPL audit')
        a, b, c, d = polygon
        alternatives = [[[a, b, c], [a, c, d]], [[a, b, d], [b, c, d]]]
        found = False
        for pair in alternatives:
            keys = [cyclic(f) for f in pair]
            if all(exported_faces[k] > 0 for k in keys):
                for key in keys:
                    exported_faces[key] -= 1
                found = True
                break
        if not found:
            raise ValueError('Native oriented quad triangulation not preserved')
    if any(exported_faces.values()):
        raise ValueError('Extra exported triangles')
    triangles = positions[faces].astype(float)
    cross = np.cross(triangles[:, 1] - triangles[:, 0], triangles[:, 2] - triangles[:, 0])
    areas = np.linalg.norm(cross, axis=1) * 0.5
    signed_volume = float(np.einsum('ij,ij->i', triangles[:, 0],
                                   np.cross(triangles[:, 1], triangles[:, 2])).sum() / 6)
    singular = np.linalg.svd(unique.astype(float) - unique.mean(axis=0), compute_uv=False)
    exported_topology = topology(inverse[faces].tolist())
    report = {
        'review_date': '2026-09-30',
        'asset_id': OPL_ID,
        'native_model_name': native_model['properties'][1].split('\0')[0],
        'native_geometry_name': native_geometry['properties'][1].split('\0')[0],
        'source': {
            'read_now_from_reacquired_original_fbx': True,
            'acquisition_record': '.research/knee-ligament-volume-sources/acquisition.json',
            'commit': manifest['source_commit'], 'url': manifest['source_url'],
            'file': 'Resources/Models/FBX/Joints100.fbx', 'sha256': SOURCE_SHA,
            'fbx_version': version, 'model_id': part['source_model_id'],
            'geometry_id': part['source_geometry_id'],
            'native_positions': len(local), 'material_names': part['materials'],
            'native_polygon_topology': topology(polygons),
            'coordinate_system': manifest['coordinate_system'],
        },
        'published': {
            'file': part['file'], 'sha256': part['sha256'],
            'manifest_sha256': digest(manifest_path),
            'render_vertices': len(positions), 'triangles': len(faces),
            'unique_positions': len(unique),
            'bounds_cm': [positions.min(0).tolist(), positions.max(0).tolist()],
            'triangle_topology': exported_topology,
            'degenerate_triangles': int(np.count_nonzero(areas == 0)),
            'surface_area_native_cm2': float(areas.sum()),
            'signed_enclosed_volume_native_cm3': signed_volume,
            'centered_position_matrix_singular_values_cm': singular.tolist(),
            'all_native_world_positions_preserved_at_float32': True,
            'all_native_oriented_quads_exhaustively_triangulated': True,
        },
        'interpretation': {
            'original_named_object': True, 'material_subset': False,
            'side': 'right, source model .r and native negative patient-left X',
            'nonplanar_surface': bool(singular[-1] > 1e-8),
            'closed_edge_incidence': exported_topology['boundary_edges'] == 0
                                     and exported_topology['nonmanifold_edges'] == 0,
            'measured_tissue_thickness': False,
            'separate_attachments': False, 'separate_fibers_or_arms': False,
            'segmentation_or_subject_pair': False,
        },
        'limits': [
            'Enclosed artist mesh volume is not measured biological tissue volume or thickness.',
            'Basic edge topology and nonplanarity do not prove self-intersection-free geometry or anatomical fidelity.',
            'No segmented source MRI, subject-specific endpoints, separate attachments or arms are supplied for this object.',
            'Only gross source-labelled course is a plausible partial candidate; no complete requirement coverage or approval.',
        ],
        'runtime_changed': False, 'clinical_approval': False,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'existing-opl-geometry-audit.json').write_text(json.dumps(report, indent=2) + '\n')

    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    bone_ids = ['za-bones-768159355', 'za-bones-179386668', 'za-bones-485011202']
    bones = [(manifest['parts'][key], *load_part(manifest['parts'][key])) for key in bone_ids]
    fig = plt.figure(figsize=(14, 12), facecolor='#faf9f5')
    views = [(-90, 8, 'Posterior context'), (180, 8, 'Patient-right lateral context'),
             (-90, 8, 'Isolated posterior'), (-25, 25, 'Isolated oblique')]
    lo, hi = unique.min(0), unique.max(0)
    for i, (azim, elev, title) in enumerate(views, 1):
        ax = fig.add_subplot(2, 2, i, projection='3d')
        if i <= 2:
            for _, pv, pf in bones:
                pv = pv.astype(float)
                # Native FBX Y is superior. Review axes x,z,y retain coordinates.
                tv = pv[pf]
                display = tv[:, :, [0, 2, 1]]
                centroids = tv.mean(1)
                visible = ((centroids[:, 1] >= lo[1] - 3)
                           & (centroids[:, 1] <= hi[1] + 3))
                ax.add_collection3d(Poly3DCollection(display[visible], facecolor='#a5b7c5',
                                                    edgecolor='none', alpha=0.16))
        ax.add_collection3d(Poly3DCollection(triangles[:, :, [0, 2, 1]],
                                            facecolor='#c2712f', edgecolor='#482f22',
                                            linewidth=0.25, alpha=0.96))
        margin = 3 if i <= 2 else 0.4
        limlo, limhi = lo - margin, hi + margin
        ax.set_xlim(limlo[0], limhi[0]); ax.set_ylim(limlo[2], limhi[2]); ax.set_zlim(limlo[1], limhi[1])
        ax.set_box_aspect((limhi - limlo)[[0, 2, 1]])
        ax.view_init(elev=elev, azim=azim)
        ax.set_xticks([limlo[0], limhi[0]])
        ax.set_yticks([limlo[2], limhi[2]])
        ax.set_zticks([limlo[1], limhi[1]])
        ax.set_xlabel('X (cm)', fontsize=9, labelpad=12)
        ax.set_ylabel('Z (cm)', fontsize=9, labelpad=12)
        ax.set_zlabel('Y (cm)', fontsize=9, labelpad=15)
        if i in (1, 3):
            ax.set_yticks([]); ax.set_ylabel('')
        if i == 2:
            ax.set_xticks([]); ax.set_xlabel('')
        if i == 4:
            ax.set_xticks([limlo[0]]); ax.set_yticks([limhi[2]])
        ax.tick_params(labelsize=8)
        ax.set_title(title, fontsize=12)
    fig.suptitle('Existing Z-Anatomy right oblique popliteal ligament\nOriginal named 186-position object · 368 retained triangles', fontsize=15)
    fig.text(0.04, 0.025, 'Gross artist-surface reference only. No measured thickness, attachment footprint, separate arm or clinical approval.\n'
             'Native X: patient left; Y: superior; Z: anterior. Context bones retain this frame; display limits omit distant triangles.\n'
             'Z-Anatomy / BodyParts3D lineage · CC BY-SA 4.0 · New projection only; no mesh edits.', fontsize=9)
    fig.subplots_adjust(left=0.02, right=0.97, top=0.88, bottom=0.14, wspace=0.15, hspace=0.38)
    image = OUT / 'existing-opl-native-review.png'
    fig.savefig(image, dpi=170); plt.close(fig)
    report['review_projection'] = {'path': str(image.relative_to(ROOT)), 'sha256': digest(image),
                                   'geometry_preserved': True, 'anatomical_approval': False}
    (OUT / 'existing-opl-geometry-audit.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report['published'], indent=2))


if __name__ == '__main__':
    main()
