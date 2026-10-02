#!/usr/bin/env python3
"""Compare four native-cell interpolation choices without changing LNQ labels."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


def restore_native_indices(vertices, faces, shape, reflected_axis):
    import numpy as np
    restored = vertices.copy(); oriented = faces.copy()
    if reflected_axis is not None:
        if reflected_axis not in (0, 1, 2):
            raise ValueError('Unknown source index reflection')
        restored[:, reflected_axis] = shape[reflected_axis] - 1 - restored[:, reflected_axis]
        oriented = oriented[:, [0, 2, 1]]
    return restored, oriented


def voxel_audit(labels, vertices, faces):
    import numpy as np
    from tools.anatomy_sources.audit_massp_mesh_voxels import section, raster_section
    triangles = vertices[faces]
    low = np.floor(vertices.min(0)).astype(int) - 1; high = np.ceil(vertices.max(0)).astype(int) + 2
    if np.any(low < 0) or np.any(high > labels.shape):
        raise ValueError('Surface leaves source field')
    xs = np.arange(low[2], high[2]); ys = np.arange(low[1], high[1])
    tested = selected = false_positive = false_negative = 0
    for z in range(low[0], high[0]):
        predicted = raster_section(section(triangles, 0, z, 2, 1), xs, ys)
        expected = labels[z, low[1]:high[1], low[2]:high[2]] > 0
        false_positive += int(np.count_nonzero(predicted & ~expected)); false_negative += int(np.count_nonzero(expected & ~predicted))
        selected += int(expected.sum()); tested += expected.size
    if selected != int(np.count_nonzero(labels)):
        raise ValueError('Not every labelled voxel was checked')
    return {'compared_native_voxel_centres': tested, 'all_source_positive_voxels_compared': selected,
            'false_positive': false_positive, 'false_negative': false_negative,
            'exact_native_voxel_centre_match': false_positive == 0 and false_negative == 0}


def compare(root, source_review, output, evidence_path):
    import numpy as np
    import nibabel as nib
    from tools.anatomy_sources.build_massp_joint_interfaces import build_label_surfaces
    from tools.anatomy_sources.audit_lnq_surface_geometry import topology
    report = json.loads(source_review.read_text())
    path = root / 'lnq-case-0571-derived/source-annotation-on-ct-indices.npy'
    if hashlib.sha256(path.read_bytes()).hexdigest() != report['reconstructed_mask_sha256']:
        raise ValueError('Source annotation changed')
    labels = np.load(path); original = labels.copy(); labels.flags.writeable = False
    if (list(labels.shape) != report['ct_shape_zyx'] or int(labels.sum()) != report['encoded_annotation_voxels']
            or set(np.unique(labels)) != {0, 1}):
        raise ValueError('Unexpected native selection')
    offset = np.asarray(report['frame_records'][0]['seg_position_lps']) - np.asarray(report['frame_records'][0]['ct_position_lps'])
    origin = np.asarray(report['ct_origin_lps']) + offset
    sz, sy, sx = report['ct_spacing_zyx_mm']
    affine = np.array([[0, 0, -sx, -origin[0]], [0, -sy, 0, -origin[1]], [sz, 0, 0, origin[2]], [0, 0, 0, 1]], float)
    output.mkdir(parents=True, exist_ok=True); rows = []
    for axis, name in [(None, 'native-diagonal'), (0, 'z-reflected-diagonal'), (1, 'y-reflected-diagonal'), (2, 'x-reflected-diagonal')]:
        view = labels if axis is None else np.flip(labels, axis=axis)
        built, construction = build_label_surfaces(view, {1})
        native, faces = restore_native_indices(*built[1], labels.shape, axis)
        world = nib.affines.apply_affine(affine, native)
        world_faces = faces[:, [0, 2, 1]] if np.linalg.det(affine[:3, :3]) < 0 else faces
        topo = topology(world, world_faces); voxels = voxel_audit(labels, native, faces)
        mesh = output / (name + '.npz'); np.savez_compressed(mesh, vertices=world, faces=world_faces)
        rows.append({'choice': name, 'reflected_index_axis': axis, 'reflection_restored_to_original_indices': True,
                     'mesh_file': mesh.name, 'mesh_sha256': hashlib.sha256(mesh.read_bytes()).hexdigest(),
                     'triangles': len(faces), 'vertices': len(native), 'topology': topo, 'voxel_audit': voxels,
                     'construction': construction, 'source_components_removed': 0, 'clinical_approval': False,
                     'continuous_contacts_audited': False})
        print(name, 'Euler:', [c['euler_characteristic'] for c in topo['mesh_components']],
              'source voxel errors:', voxels['false_positive'], voxels['false_negative'], flush=True)
        if not np.array_equal(labels, original):
            raise ValueError('Native annotation changed')
    result = {'case_id': 'case_0571', 'source_doi': report['source_doi'], 'source_annotation_sha256': report['reconstructed_mask_sha256'],
              'source_native_review_sha256': hashlib.sha256(source_review.read_bytes()).hexdigest(),
              'native_seg_affine_zyx_to_ras': affine.tolist(), 'native_original_labels_changed': False,
              'original_marching_cubes_baseline_replaced': False, 'source_voxels_resampled': False,
              'method': 'Binary one-hot source labels interpolated within a conforming six-tetrahedron Freudenthal split. Four different native-cell body diagonals are compared by index reflections restored exactly before the original SEG affine; no fitted registration.',
              'records': rows, 'clinical_approval': False, 'runtime_promoted': False,
              'status': 'interpolation_sensitivity_study_requires_anatomical_review',
              'limits': ['Tetrahedral interpolation adds a directional subvoxel assumption; it is not measured anatomy.',
                         'Fewer handles or exact native voxel-centre agreement cannot select an anatomically correct surface.',
                         'Continuous contacts, field boundaries, individual-node identity and station context remain separate checks.',
                         'All source components are retained; no smoothing, decimation, label editing or source-derived hole filling.']}
    evidence_path.write_text(json.dumps(result, indent=2) + '\n')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source-root', type=Path, required=True); p.add_argument('--review', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True); p.add_argument('--evidence', type=Path, required=True)
    a = p.parse_args(); compare(a.source_root, a.review, a.output, a.evidence)
