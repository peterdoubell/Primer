"""Audit four unchanged source-named hip ligament objects and project their frame.

This bounded review does not publish, edit, repair, fit, smooth, subdivide or
infer tissue geometry. NumPy and Matplotlib are offline review dependencies.
"""
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.anatomy_sources.inspect_fbx import child, load_fbx
from tools.anatomy_sources.audit_knee_ligament_volume_sources import load_part, topology

SOURCE = ROOT / '.research/knee-ligament-volume-sources/z-anatomy-Joints100.fbx'
SOURCE_SHA = 'f4ba7a910cdaef99e31530f368628780d9f06b5d77853f8b721f47f67137e823'
OUT = ROOT / 'docs/msk-hip-capsular-ligament-native-review'
IDS = ('za-joints-318012956', 'za-joints-347770529',
       'za-joints-142701643', 'za-joints-731742504')
COLORS = ('#bf692b', '#dcad42', '#388879', '#7760a3')
SHORT = ('Iliofemoral: transverse', 'Iliofemoral: descending',
         'Pubofemoral', 'Ischiofemoral')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def cyclic(face):
    return min(tuple(face[i:] + face[:i]) for i in range(len(face)))


def audit_part(part, objects, connections):
    geometry = next(n for n in objects if n['name'] == 'Geometry'
                    and n['properties'][0] == part['source_geometry_id'])
    model = next(n for n in objects if n['name'] == 'Model'
                 and n['properties'][0] == part['source_model_id'])
    object_map = {n['properties'][0]: n for n in objects if n['properties']}
    attached_ids = [n['properties'][1] for n in connections
                    if len(n['properties']) >= 3 and n['properties'][0] == 'OO'
                    and n['properties'][2] == part['source_model_id']]
    if part['source_geometry_id'] not in attached_ids:
        raise ValueError('Native geometry is not connected to the expected native model')
    actual_material_slots = [object_map[key]['properties'][1].split('\0')[0]
                             for key in attached_ids
                             if object_map[key]['name'] == 'Material']
    if actual_material_slots != part['materials']:
        raise ValueError('Native material connections differ from published manifest')
    if model['properties'][1].split('\0')[0] != part['name']:
        raise ValueError('Native source name differs from published manifest')
    local = np.asarray(child(geometry, 'Vertices')['properties'][0]).reshape(-1, 3)
    polygons, current = [], []
    for index in child(geometry, 'PolygonVertexIndex')['properties'][0]:
        current.append(int(index) if index >= 0 else -int(index) - 1)
        if index < 0:
            polygons.append(current)
            current = []
    if current or any(len(p) != 4 for p in polygons):
        raise ValueError('Expected terminated native quadrilaterals')
    transform = np.asarray(part['world_transform_columns'], dtype=float).T
    world = np.column_stack([local, np.ones(len(local))]) @ transform.T
    positions, faces = load_part(part)
    unique, inverse = np.unique(positions, axis=0, return_inverse=True)
    native32 = world.astype('<f4')
    if len(np.unique(native32, axis=0)) != len(native32):
        raise ValueError('Ambiguous duplicate native position mapping')
    if not np.array_equal(np.unique(native32, axis=0), unique):
        raise ValueError('Native world position set differs from runtime object')
    native_ids = {tuple(v): i for i, v in enumerate(native32)}
    remaining = Counter(cyclic([native_ids[tuple(positions[i])] for i in face])
                        for face in faces)
    for a, b, c, d in polygons:
        alternatives = (((a, b, c), (a, c, d)), ((a, b, d), (b, c, d)))
        for pair in alternatives:
            keys = [cyclic(list(p)) for p in pair]
            if all(remaining[k] > 0 for k in keys):
                for key in keys:
                    remaining[key] -= 1
                break
        else:
            raise ValueError('Native oriented quad is not preserved by runtime triangles')
    if any(remaining.values()):
        raise ValueError('Extra runtime triangle')
    material = child(geometry, 'LayerElementMaterial')
    mapping = child(material, 'MappingInformationType')['properties'][0]
    assignments = list(child(material, 'Materials')['properties'][0])
    if mapping == 'AllSame':
        assignments = assignments * len(polygons)
    if len(assignments) != len(polygons) or set(assignments) != {0}:
        raise ValueError('Unexpected non-ligament material face assignment')
    triangle_vertices = positions[faces].astype(float)
    cross = np.cross(triangle_vertices[:, 1] - triangle_vertices[:, 0],
                     triangle_vertices[:, 2] - triangle_vertices[:, 0])
    areas = np.linalg.norm(cross, axis=1) / 2
    volume = np.einsum('ij,ij->i', triangle_vertices[:, 0],
                      np.cross(triangle_vertices[:, 1], triangle_vertices[:, 2])).sum() / 6
    singular = np.linalg.svd(unique.astype(float) - unique.mean(0), compute_uv=False)
    report = {
        'asset_id': part['id'],
        'native_model_name': model['properties'][1].split('\0')[0],
        'native_geometry_name': geometry['properties'][1].split('\0')[0],
        'source_model_id': part['source_model_id'],
        'source_geometry_id': part['source_geometry_id'],
        'native_positions': len(local),
        'native_polygon_topology': topology(polygons),
        'runtime_file': part['file'], 'runtime_sha256': part['sha256'],
        'runtime_render_vertices': len(positions),
        'runtime_unique_positions': len(unique),
        'runtime_triangles': len(faces),
        'runtime_triangle_topology': topology(inverse[faces].tolist()),
        'bounds_native_cm': [positions.min(0).tolist(), positions.max(0).tolist()],
        'nonplanar_position_singular_values_cm': singular.tolist(),
        'degenerate_triangles': int(np.count_nonzero(areas == 0)),
        'source_surface_area_cm2': float(areas.sum()),
        'artist_signed_enclosed_volume_cm3': float(volume),
        'all_native_world_positions_preserved_at_float32': True,
        'all_native_oriented_quads_exhaustively_triangulated': True,
        'native_geometry_model_connection_verified': True,
        'world_transform_basis': 'Existing ufbx-evaluated geometry_to_world columns from current manifest; source local positions read directly from original FBX. No independent full FBX hierarchy reevaluation in this bounded audit.',
        'native_material_mapping': mapping,
        'native_material_slots': part['materials'],
        'actual_polygon_material_assignments': {'Ligament (index 0)': len(assignments)},
        'whole_original_named_object': True,
        'material_subset': False,
        'side_evidence': 'Original .r name; all native patient-left X coordinates negative',
        'source_arms_separately_named': part['id'] in IDS[:2],
        'measured_tissue_volume_or_thickness': False,
        'paired_subject_segmentation': False,
        'verified_attachment_footprint': False,
        'anatomical_approval': False,
    }
    return report, positions, faces


def ras(points):
    """Proper basis change from native left/superior/anterior cm to RAS mm."""
    return np.column_stack((-points[:, 0], points[:, 2], points[:, 1])) * 10


def render(parts, manifest):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    geometry = [(ras(positions), faces) for _, positions, faces in parts]
    all_points = np.concatenate([p for p, _ in geometry])
    lo, hi = all_points.min(0), all_points.max(0)
    center = (lo + hi) / 2
    half = max(hi - lo) / 2 + 25
    bones = []
    for key in ('za-bones-83785534', 'za-bones-768159355'):
        positions, faces = load_part(manifest['parts'][key])
        bones.append((key, ras(positions), faces))

    def panel(ax, shown, azimuth, title, context, limits):
        ax.set_proj_type('ortho')
        if context:
            for _, positions, faces in bones:
                # Triangle filtering affects this projection only, never source geometry.
                centroid = positions[faces].mean(1)
                visible = np.all((centroid >= limits[0]) & (centroid <= limits[1]), axis=1)
                ax.add_collection3d(Poly3DCollection(positions[faces[visible]],
                                                    facecolor='#aab9c5', edgecolor='none',
                                                    alpha=.15))
        for i in shown:
            positions, faces = geometry[i]
            ax.add_collection3d(Poly3DCollection(positions[faces],
                                                facecolor=COLORS[i], edgecolor='#342f2a',
                                                linewidth=.15, alpha=.93))
        for method, axis in ((ax.set_xlim, 0), (ax.set_ylim, 1), (ax.set_zlim, 2)):
            method(limits[0][axis], limits[1][axis])
        ax.set_box_aspect(limits[1] - limits[0])
        ax.view_init(elev=9, azim=azimuth)
        ax.set_axis_off()
        ax.set_title(title, fontsize=11)

    fig = plt.figure(figsize=(15, 7), facecolor='#faf9f5')
    shared_limits = (center - half, center + half)
    for i, (azimuth, title) in enumerate(((90, 'Anterior'),
                                        (0, 'Patient-right lateral'),
                                        (-90, 'Posterior')), 1):
        panel(fig.add_subplot(1, 3, i, projection='3d'), range(4), azimuth,
              title, True, shared_limits)
    fig.suptitle('Source-named right hip capsular ligaments in their unchanged shared frame', fontsize=15)
    fig.legend(handles=[Patch(facecolor=c, label=n) for c, n in zip(COLORS, SHORT)],
               loc='lower center', bbox_to_anchor=(.5, .15), ncol=2, frameon=False)
    fig.text(.035, .04, 'Four complete native artist objects, not measured tissue volumes or validated attachments. '
             'No newly inferred arms, footprints, fitting or mesh edits.\n'
             'RAS millimetres: +X patient right, +Y anterior, +Z superior. Context bones retain the source frame; '
             'distant context triangles omitted from projection.\n'
             'Z-Anatomy / BodyParts3D lineage · CC BY-SA 4.0. Native iliofemoral arms are separately named in source; '
             'this does not prove anatomical boundaries.', fontsize=9)
    fig.subplots_adjust(top=.85, bottom=.25, left=.015, right=.985)
    shared = OUT / 'shared-native-frame.png'
    fig.savefig(shared, dpi=150); plt.close(fig)

    fig = plt.figure(figsize=(16, 8), facecolor='#faf9f5')
    for i, (positions, _) in enumerate(geometry):
        local_lo, local_hi = positions.min(0), positions.max(0)
        local_center = (local_lo + local_hi) / 2
        local_half = max(local_hi - local_lo) / 2 + 5
        local_limits = (local_center - local_half, local_center + local_half)
        panel(fig.add_subplot(2, 4, i + 1, projection='3d'), [i], 90,
              SHORT[i] + '\nAnterior, isolated', False, local_limits)
        panel(fig.add_subplot(2, 4, i + 5, projection='3d'), [i], -45,
              'Posterolateral, isolated', False, local_limits)
    fig.suptitle('Isolated source surfaces: visible faceting and curved band envelopes', fontsize=15)
    fig.text(.035, .025, 'Each column uses its own fixed equal-axis scale for both views; columns are not a shared comparison scale. '
             'Geometry and native triangle connectivity unchanged.\n'
             'Closed artist envelopes do not establish biological thickness, segmented volume, capsular recesses, '
             'attachment coverage or clinical fidelity.\n'
             'Z-Anatomy / BodyParts3D lineage · CC BY-SA 4.0. Review projections only; no runtime or requirement change.', fontsize=9)
    fig.subplots_adjust(left=.01, right=.99, top=.87, bottom=.12, hspace=.15)
    isolated = OUT / 'isolated-source-surfaces.png'
    fig.savefig(isolated, dpi=150); plt.close(fig)
    return [shared, isolated], [manifest['parts'][key] for key, _, _ in bones]


def main():
    if digest(SOURCE) != SOURCE_SHA:
        raise ValueError('Original pinned FBX SHA mismatch')
    manifest_path = ROOT / 'web/anatomy/msk-atlas/manifest.json'
    requirements_path = ROOT / 'data/radiology/msk-structure-requirements.json'
    manifest = json.loads(manifest_path.read_text())
    requirements = json.loads(requirements_path.read_text())
    version, nodes = load_fbx(SOURCE)
    objects = next(n for n in nodes if n['name'] == 'Objects')['children']
    connections = next(n for n in nodes if n['name'] == 'Connections')['children']
    parts = [audit_part(manifest['parts'][key], objects, connections) for key in IDS]
    terms = ('iliofemoral', 'pubofemoral', 'ischiofemoral')
    matches = []
    nearby = []
    for investigation in requirements['investigations']:
        for structure in investigation['structures']:
            children = [structure] + structure.get('required_parts', [])
            matches.extend({'investigation_id': investigation['investigation_id'],
                            'structure_id': entry['id'], 'name': entry['name']}
                           for entry in children
                           if any(term in (entry['id'] + ' ' + entry['name']).lower()
                                  for term in terms))
            if structure['id'] == 'hip.hip_capsule_and_synovium':
                nearby.append({'investigation_id': investigation['investigation_id'],
                               'structure': structure})
    OUT.mkdir(parents=True, exist_ok=True)
    images, bones = render(parts, manifest)
    report = {
        'review_date': '2026-09-30',
        'source': {
            'file': '.research/knee-ligament-volume-sources/z-anatomy-Joints100.fbx',
            'sha256': SOURCE_SHA, 'bytes': SOURCE.stat().st_size,
            'fbx_version': version, 'commit': manifest['source_commit'],
            'url': manifest['source_url'],
            'license': 'CC BY-SA 4.0', 'license_url': manifest['license_url'],
            'attribution': manifest['attribution'],
            'coordinate_system': manifest['coordinate_system'],
        },
        'runtime_manifest_sha256': digest(manifest_path),
        'requirement_scope_sha256': digest(requirements_path),
        'review_tool_sha256': digest(Path(__file__)),
        'objects': [p[0] for p in parts],
        'context_bones': [{'id': b['id'], 'name': b['name'], 'sha256': b['sha256']}
                          for b in bones],
        'projections': [{'path': str(path.relative_to(ROOT)), 'sha256': digest(path)}
                        for path in images],
        'current_exact_ligament_requirement_matches': matches,
        'nearby_requirement_is_not_equivalent': nearby,
        'recommendation': 'No current requirement binding: named capsular bands cannot establish anterior/posterior recess or synovium. Preserve source review for future specialist-approved scope.',
        'limits': [
            'Position and connectivity preservation checks establish source correspondence, not biological fidelity.',
            'Closed edge incidence and nonplanarity do not prove absence of self-intersection or anatomical accuracy.',
            'Source-authored transverse/descending names do not establish complete arms, histological boundaries, attachment footprints or measured thickness.',
            'The named ligament surfaces cannot be substituted for capsule recesses, synovium, cartilage or ligamentum teres.',
            'No matching hip ligament requirement is currently specified; no new requirement or ledger binding is inferred.',
        ],
        'runtime_changed': False, 'requirements_changed': False,
        'ledger_changed': False, 'clinical_approval': False,
    }
    path = OUT / 'native-preservation-audit.json'
    path.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'report': str(path), 'objects': len(parts),
                      'source_positions': sum(p[0]['native_positions'] for p in parts),
                      'triangles': sum(p[0]['runtime_triangles'] for p in parts),
                      'exact_current_requirements': len(matches)}, indent=2))


if __name__ == '__main__':
    main()
