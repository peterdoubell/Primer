#!/usr/bin/env python3
"""Build offline native MASSP label surfaces with explicit probability uncertainty."""
import argparse
import hashlib
import json
from pathlib import Path

import nibabel as nib
import numpy as np
from scipy import ndimage
from skimage import measure

LABELS = {9: ('gpi', 'l'), 10: ('gpi', 'r'), 11: ('gpe', 'l'),
          12: ('gpe', 'r'), 38: ('put', 'l'), 39: ('put', 'r')}


class MeshTopologyError(ValueError):
    def __init__(self, diagnostics):
        super().__init__('Mesh has boundary or nonmanifold edges; retain source for review')
        self.diagnostics = diagnostics


def mesh_mask(mask, affine):
    """Extract every component; affine changes coordinates, never label values."""
    if mask.dtype != np.bool_ or mask.ndim != 3 or not mask.any():
        raise ValueError('Need a nonempty three-dimensional selection')
    if not np.isfinite(affine).all() or affine.shape != (4, 4) or abs(np.linalg.det(affine[:3, :3])) < 1e-12:
        raise ValueError('Invalid source affine')
    if any(mask.take(index, axis=axis).any() for axis in range(3) for index in (0, -1)):
        raise ValueError('Selection touches source boundary; cannot close it artificially')
    coords = np.argwhere(mask)
    lo, hi = coords.min(0) - 1, coords.max(0) + 2
    crop = mask[tuple(slice(a, b) for a, b in zip(lo, hi))]
    verts, faces, _, _ = measure.marching_cubes(crop.astype(np.float32), level=0.5, allow_degenerate=False)
    verts = nib.affines.apply_affine(affine, verts.astype(np.float64) + lo)
    tri = verts[faces]
    volume = np.einsum('ij,ij->i', tri[:, 0], np.cross(tri[:, 1], tri[:, 2])).sum() / 6
    if volume < 0:
        faces = faces[:, ::-1].copy()
        volume = -volume
    edges = np.sort(np.concatenate([faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]]), axis=1)
    _, counts = np.unique(edges, axis=0, return_counts=True)
    unique_positions, position_index = np.unique(verts, axis=0, return_inverse=True)
    position_faces = position_index[faces]
    position_edges = np.sort(np.concatenate([position_faces[:, [0, 1]], position_faces[:, [1, 2]], position_faces[:, [2, 0]]]), axis=1)
    _, position_counts = np.unique(position_edges, axis=0, return_counts=True)
    areas = np.linalg.norm(np.cross(verts[faces[:, 1]] - verts[faces[:, 0]], verts[faces[:, 2]] - verts[faces[:, 0]]), axis=1) / 2
    if not np.isfinite(verts).all() or np.any(areas <= 0):
        raise ValueError('Invalid or degenerate surface')
    _, components6 = ndimage.label(crop)
    _, components26 = ndimage.label(crop, ndimage.generate_binary_structure(3, 3))
    stats = {'vertices': len(verts), 'triangles': len(faces),
                          'native_selected_voxels': int(mask.sum()),
                          'selected_voxel_volume_mm3': float(mask.sum() * abs(np.linalg.det(affine[:3, :3]))),
                          'surface_signed_volume_mm3': float(volume),
                          'source_components_6_connected': int(components6),
                          'source_components_26_connected': int(components26),
                          'boundary_edges': int(np.count_nonzero(counts == 1)), 'nonmanifold_edges': int(np.count_nonzero(counts > 2)),
                          'exact_duplicate_vertex_positions': int(len(verts) - len(unique_positions)),
                          'coincident_position_boundary_edges': int(np.count_nonzero(position_counts == 1)),
                          'coincident_position_nonmanifold_edges': int(np.count_nonzero(position_counts > 2)),
                          'world_bounds_mm': [verts.min(0).tolist(), verts.max(0).tolist()],
                          'removed_components': 0, 'smoothing_or_decimation': False,
                          'clinical_approval': False}
    if np.any(counts != 2):
        raise MeshTopologyError(stats)
    return verts, faces, stats


def load_verified(root, name, source):
    entries = {entry['name']: entry for entry in source['files']}
    path = root / name
    if name not in entries or hashlib.sha256(path.read_bytes()).hexdigest() != entries[name]['sha256']:
        raise ValueError('Changed or unregistered source: ' + name)
    image = nib.load(path)
    sform, code = image.get_sform(coded=True)
    qform, qcode = image.get_qform(coded=True)
    if not code or not np.array_equal(image.affine, sform):
        raise ValueError('No unambiguous declared sform')
    if qcode and not np.allclose(qform, sform, rtol=0, atol=1e-5):
        raise ValueError('Conflicting source affines')
    return image


def build(root, output, selection='maxlabel'):
    if selection not in ('maxlabel','bestlabel'):
        raise ValueError('Unknown publisher label selection')
    output.mkdir(parents=True, exist_ok=True)
    source = json.loads((root / 'acquisition.json').read_text())
    if source['doi'] != '10.21942/uva.27291579.v2':
        raise ValueError('Unexpected dataset version')
    table_path = root / 'massp_2p0-label-list.txt'
    table_record = next(e for e in source['files'] if e['name'] == table_path.name)
    if hashlib.sha256(table_path.read_bytes()).hexdigest() != table_record['sha256']:
        raise ValueError('Source label table hash changed')
    table = table_path.read_text()
    for label, (code, side) in LABELS.items():
        if not any(line.split(':')[0].strip() == str(label) and line.split(':')[-2].strip() == code
                   and line.split(':')[-1].strip() == side for line in table.splitlines() if ':' in line):
            raise ValueError('Publisher label table mismatch')
    selection_file = f'ahead-massp2_avg-{selection}_decade-18to80.nii.gz'
    label_image = load_verified(root, selection_file, source)
    labels = np.asarray(label_image.dataobj)
    records = []
    for label, (code, side) in LABELS.items():
        name = f'proba_ahead-massp2_avg-{code}_hem-{side}_decade-18to80_n97.nii.gz'
        image = load_verified(root, name, source)
        if image.shape != label_image.shape or not np.array_equal(image.affine, label_image.affine):
            raise ValueError('Probability and label grids differ')
        prob = np.asarray(image.dataobj)
        if not np.isfinite(prob).all() or prob.min() < 0 or prob.max() > 1:
            raise ValueError('Invalid probabilities')
        selected = labels == label
        mesh_name = f'{code}-{side}-{selection}.npz'
        mesh_details = {}
        try:
            verts, faces, stats = mesh_mask(selected, image.affine)
        except MeshTopologyError as error:
            stats = error.diagnostics
            mesh_details = {'surface_status': 'held_topology_failure', 'output_mesh_created': False}
        else:
            np.savez_compressed(output / mesh_name, vertices=verts, faces=faces)
            mesh_details = {'surface_status': 'offline_candidate_requires_anatomical_review', 'output_mesh_created': True,
                            'mesh_file': mesh_name, 'mesh_sha256': hashlib.sha256((output / mesh_name).read_bytes()).hexdigest()}
        comparisons = []
        for threshold in (.25, .5, .75):
            binary = prob >= threshold
            overlap = int(np.count_nonzero(binary & selected))
            comparisons.append({'threshold': threshold, 'probability_voxels': int(binary.sum()),
                                'label_voxels': int(selected.sum()), 'overlap_voxels': overlap,
                                'dice_with_publisher_label_selection': float(2 * overlap / (binary.sum() + selected.sum()))})
        records.append({'label_id': label, 'code': code, 'side': side, 'probability_file': name,
                        **mesh_details,
                        'native_selected_probability_range': [float(prob[selected].min()), float(prob[selected].max())],
                        'native_selected_mean_probability': float(prob[selected].mean()),
                        'probability_comparisons': comparisons, **stats})
        print(code, side, mesh_details['surface_status'], stats['triangles'], flush=True)
    record = {'source_doi': source['doi'], 'source_acquisition_sha256': hashlib.sha256((root / 'acquisition.json').read_bytes()).hexdigest(),
              'selection': 'Original publisher '+selection+' map; not an independently chosen probability threshold',
              'publisher_selection_file': selection_file,
              'surface_construction': 'All selected label voxels, binary indicator isosurface 0.5, native affine to RAS millimetres; no source resampling, component removal, smoothing, decimation or anatomical edits',
              'coordinate_frame': 'Publisher MNI2009b; no registration to BodyParts3D implied',
              'records': records, 'clinical_approval': False, 'runtime_binding_added': False,
              'limits': 'A maximum-probability population label is a reference selection, not a proven individual anatomical boundary. Comparison Dice scores measure alternative source selections, not segmentation accuracy.'}
    (output / 'surface-review.json').write_text(json.dumps(record, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--selection',choices=('maxlabel','bestlabel'),default='maxlabel')
    args = parser.parse_args()
    build(args.source, args.output,args.selection)
