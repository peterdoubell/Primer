#!/usr/bin/env python3
"""Offline native-grid MRI/label/mesh audit; no fitted transform or approval.

MRI planes retain native voxel values. Labels alone use nearest-neighbour
sampling at those MRI voxel centres. Mesh outlines are direct plane/triangle
intersections. Dice measures mesh-versus-author-label consistency, never MRI
accuracy against independent ground truth.
"""
import gzip
import hashlib
import json
from pathlib import Path
import struct
import xml.etree.ElementTree as ET

import numpy as np
from scipy import ndimage
from scipy.spatial import cKDTree
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt
from matplotlib.collections import LineCollection
from verify_malaya_registration import load_nrrd

ROOT = Path(__file__).resolve().parents[2]
CACHE = Path('/tmp/primer-msk-sources/high-fidelity')
REG = CACHE / 'um-registration'
OUT = CACHE / 'um-knee-image-audit'
TARGETS = {'um-knee-meniscus-knee', 'um-knee-cartilage-tibia', 'um-knee-cartilage-femur-distal',
           'um-knee-cartilage-patella', 'um-knee-ligament-acl', 'um-knee-ligament-pcl',
           'um-knee-ligament-patella', 'um-knee-tendon-quadriceps'}
PLANES = [('Sagittal', 0, 1, 2), ('Coronal', 1, 0, 2), ('Axial', 2, 0, 1)]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def volume(path):
    header, image, vectors, origin = load_nrrd(path)
    directions = np.column_stack([v for v in vectors if v is not None])
    assert header['space'] == 'left-posterior-superior'
    assert np.all(np.count_nonzero(directions, axis=0) == 1), 'Oblique MRI needs a different audit'
    return {'path': str(path), 'header': header, 'data': image, 'directions': directions, 'origin': origin}


def mesh(part):
    path = ROOT / 'web' / part['file'].removeprefix('/app/')
    assert sha(path) == part['sha256']
    raw = gzip.decompress(path.read_bytes())
    assert hashlib.sha256(raw).hexdigest() == part['decoded_sha256']
    magic, nv, ni = struct.unpack_from('<4sII', raw)
    assert magic == b'BP3D'
    points = np.frombuffer(raw, '<f4', nv * 3, 12).reshape(-1, 3).astype(float)
    faces = np.frombuffer(raw, '<u4', ni, 12 + nv * 24).reshape(-1, 3)
    return points, faces, points[faces]


def _section_line_keys(lines):
    """Canonical endpoint order without rounding or geometric tolerance."""
    reverse = ((lines[:, 0, 0] > lines[:, 1, 0])
               | ((lines[:, 0, 0] == lines[:, 1, 0])
                  & (lines[:, 0, 1] > lines[:, 1, 1])))
    return np.where(reverse[:, None, None], lines[:, ::-1], lines).reshape(-1, 4)


def section(triangles, axis, coordinate, horizontal, vertical):
    delta = triangles[:, :, axis] - coordinate
    crossing = (delta.min(axis=1) < 0) & (delta.max(axis=1) > 0)
    selected, delta = triangles[crossing], delta[crossing]
    points = np.full((len(selected), 3, 3), np.nan)
    for edge, (a, b) in enumerate(((0, 1), (1, 2), (2, 0))):
        valid = ((delta[:, a] <= 0) & (delta[:, b] > 0)) | ((delta[:, b] <= 0) & (delta[:, a] > 0))
        fraction = -delta[valid, a] / (delta[valid, b] - delta[valid, a])
        points[valid, edge] = selected[valid, a] + fraction[:, None] * (selected[valid, b] - selected[valid, a])
    assert np.all(np.isfinite(points[:, :, 0]).sum(axis=1) == 2)
    lines = points[np.isfinite(points[:, :, 0])].reshape(-1, 2, 3)
    # Native voxel-derived surfaces can have whole edges/faces exactly on the
    # image plane. Strict crossing alone drops their valid section contours.
    original_delta = triangles[:, :, axis] - coordinate
    zero = original_delta == 0
    edge_faces = triangles[zero.sum(axis=1) == 2]
    edge_zero = zero[zero.sum(axis=1) == 2]
    if len(edge_faces):
        lines = np.concatenate((lines, edge_faces[edge_zero].reshape(-1, 2, 3)))
    coplanar = triangles[zero.all(axis=1)]
    if len(coplanar):
        edges = coplanar[:, [(0, 1), (1, 2), (2, 0)], :].reshape(-1, 2, 3)
        # Remove internal triangulation edges of coplanar patches, keeping
        # their boundary. Adjacent noncoplanar faces may contribute it too.
        keys = _section_line_keys(edges[:, :, [horizontal, vertical]])
        _, unique, count = np.unique(keys, axis=0, return_index=True, return_counts=True)
        lines = np.concatenate((lines, edges[unique[count == 1]]))
    projected = lines[:, :, [horizontal, vertical]]
    if not len(projected):
        return np.empty((0, 2, 2))
    projected = projected[np.any(projected[:, 0] != projected[:, 1], axis=1)]
    # Deduplicate shared on-plane edges regardless of direction, otherwise the
    # even/odd raster fill would cancel a real boundary counted twice.
    keys = _section_line_keys(projected)
    _, unique = np.unique(keys, axis=0, return_index=True)
    return projected[np.sort(unique)]


def raster_section(lines, horizontal, vertical):
    x, y = np.meshgrid(horizontal, vertical)
    inside = np.zeros(x.shape, dtype=bool)
    for (x1, y1), (x2, y2) in lines:
        if y1 != y2:
            inside ^= ((y1 > y) != (y2 > y)) & (x < x1 + (y - y1) * (x2 - x1) / (y2 - y1))
    return inside


def slice_plane(image, axis, requested, horizontal, vertical, bounds):
    directions, origin, data = image['directions'], image['origin'], image['data']
    array_axes = np.argmax(abs(directions), axis=1)
    fixed_axis = array_axes[axis]
    index = int(np.rint((requested - origin[axis]) / directions[axis, fixed_axis]))
    assert 0 <= index < data.shape[fixed_axis], 'Requested plane outside MRI field'
    actual = origin[axis] + directions[axis, fixed_axis] * index
    selections, coordinates = {}, {}
    for world_axis in (horizontal, vertical):
        array_axis = array_axes[world_axis]
        values = origin[world_axis] + directions[world_axis, array_axis] * np.arange(data.shape[array_axis])
        indices = np.where((values >= bounds[0, world_axis]) & (values <= bounds[1, world_axis]))[0]
        indices = indices[np.argsort(values[indices])]
        selections[array_axis] = indices; coordinates[world_axis] = values[indices]
    xx, yy = np.meshgrid(coordinates[horizontal], coordinates[vertical])
    ii, jj = np.meshgrid(selections[array_axes[horizontal]], selections[array_axes[vertical]])
    index_grid = np.zeros((3, *xx.shape), dtype=int)
    index_grid[fixed_axis] = index; index_grid[array_axes[horizontal]] = ii; index_grid[array_axes[vertical]] = jj
    plane = data[tuple(index_grid)]
    world = np.zeros((*xx.shape, 3)); world[:, :, axis] = actual
    world[:, :, horizontal] = xx; world[:, :, vertical] = yy
    return plane, world, coordinates[horizontal], coordinates[vertical], float(actual), index


def summary(values):
    return {'min': float(np.min(values)), 'median': float(np.median(values)),
            'p95': float(np.percentile(values, 95)), 'max': float(np.max(values))}


def main():
    OUT.mkdir(exist_ok=True)
    manifest_path = ROOT / 'web/anatomy/msk-mri-knee/manifest.json'
    manifest = json.loads(manifest_path.read_text())
    reference_acquisition = json.loads((OUT / 'reference-volume-acquisition.json').read_text())
    label = volume(REG / 'Segmentation.seg.nrrd')
    images = [volume(Path(reference_acquisition['reference_image_file'])),
              volume(REG / '19 RT T2 FS spc_SAG_iso (KNEE).nrrd')]
    image_labels = ['MRML reference: source-labelled T1 Dixon water', 'Separate source-labelled T2 FS knee']
    direction, origin = label['directions'], label['origin']
    inverse = np.linalg.inv(direction)
    ref_offset = inverse @ (images[0]['origin'] - origin)
    scene = ET.parse(REG / 'Final model.mrml').getroot()
    assert not any('Transform' in node.tag for node in scene), 'Unexpected parent transform'
    targets = []
    for parent in manifest['parts'].values():
        if parent['id'] not in TARGETS:
            continue
        for part in parent.get('components', [parent]):
            selection = None
            if parent.get('components'):
                lateral, medial = parent['components']
                cut = (lateral['bounds'][1][0] + medial['bounds'][0][0]) / 2
                selection = {'axis': 'native LPS X', 'cut_mm': cut,
                             'keep': 'below' if part['name'].startswith('Lateral') else 'above'}
            targets.append((part, selection))
    report = {'status': 'Offline research correspondence audit; no clinical approval',
        # Hash immutable geometry/source labels, not the full manifest that
        # later cites this audit (which would create a circular fingerprint).
        'mesh_geometry_and_source_labels_sha256': hashlib.sha256(json.dumps(
             {'parts': manifest['parts'], 'coordinate_system': manifest['coordinate_system']},
             sort_keys=True, separators=(',', ':')).encode()).hexdigest(),
        'source_hashes': {str(p): sha(p) for p in (REG / 'Final model.mrml',
             REG / 'Segmentation.seg.nrrd', Path(reference_acquisition['reference_image_file']), Path(images[1]['path']))},
        'reference_image_origin_in_segmentation_ijk': ref_offset.tolist(),
        'method': 'No fitted transform. Original MRI pixels retained in native orthogonal planes; source labels nearest-neighbour sampled at MRI voxel centres; mesh contours from exact triangle-plane intersections.',
        'metric_limits': 'Dice compares two source-derived representations (mesh and author labels), not independent MRI truth. Boundary-voxel-centre distances are point-sampling proxies, not exact tissue-boundary distances. Intensity distributions are uncalibrated source values, not HU or a diagnosis.',
        'images': [{'path': image['path'], 'label': name, 'shape': list(image['data'].shape),
                    'origin_lps_mm': image['origin'].tolist(), 'direction_columns': image['directions'].T.tolist()}
                   for image, name in zip(images, image_labels)], 'structures': []}
    for part, selection in targets:
        segment = part['source_segmentation']
        voxels = np.argwhere(label['data'][segment['layer']] == segment['label_value'])
        world_voxels = voxels @ direction.T + origin
        if selection:
            keep = world_voxels[:, 0] < selection['cut_mm'] if selection['keep'] == 'below' else world_voxels[:, 0] > selection['cut_mm']
            voxels, world_voxels = voxels[keep], world_voxels[keep]
        low, high = voxels.min(axis=0) - 3, voxels.max(axis=0) + 3
        mask = np.zeros(tuple(high - low + 1), dtype=bool)
        mask[tuple((voxels - low).T)] = True
        boundary_voxels = np.argwhere(mask & ~ndimage.binary_erosion(mask)) + low
        boundary_world = boundary_voxels @ direction.T + origin
        points, faces, triangles = mesh(part)
        unique = np.unique(points, axis=0)
        distances = cKDTree(boundary_world).query(unique)[0]
        mesh_volume = abs(np.einsum('ij,ij->i', triangles[:, 0], np.cross(triangles[:, 1], triangles[:, 2])).sum() / 6)
        label_volume = len(voxels) * abs(np.linalg.det(direction))
        record = {'id': part['id'], 'name': part['name'], 'source_segment': segment,
                  'component_label_selection': selection, 'source_label_voxels': len(voxels),
                  'label_volume_mm3': float(label_volume), 'mesh_volume_mm3': float(mesh_volume),
                  'mesh_volume_difference_percent': float((mesh_volume / label_volume - 1) * 100),
                  'mesh_vertex_to_boundary_voxel_centre_mm': summary(distances), 'planes': []}
        bounds = np.array(part['bounds'], dtype=float) + np.array([[-12] * 3, [12] * 3])
        requested = {}
        for plane_name, axis, horizontal, vertical in PLANES:
            array_axis = int(np.argmax(abs(direction[axis])))
            peak = np.bincount(voxels[:, array_axis]).argmax()
            requested[axis] = float(origin[axis] + direction[axis, array_axis] * peak)
        fig, axes = plt.subplots(4, 3, figsize=(13, 15), facecolor='white')
        for sequence, (image, sequence_name) in enumerate(zip(images, image_labels)):
            samples = (world_voxels - image['origin']) @ np.linalg.inv(image['directions']).T
            inside_fov = np.all((samples >= -.5) & (samples <= np.array(image['data'].shape) - .5), axis=1)
            intensity = ndimage.map_coordinates(image['data'], samples[inside_fov].T, order=1, mode='nearest')
            record.setdefault('sequence_sampling', []).append({'label': sequence_name,
                'label_voxel_centres_in_fov_fraction': float(inside_fov.mean()),
                'label_interior_intensity_trilinear_for_statistics_only': summary(intensity)})
            slices = [slice_plane(image, axis, requested[axis], horizontal, vertical, bounds)
                      for _, axis, horizontal, vertical in PLANES]
            values = np.concatenate([item[0].ravel() for item in slices])
            window = [float(np.percentile(values, .5)), float(np.percentile(values, 99.5))]
            for column, ((plane_name, axis, horizontal, vertical), (pixels, world, xx, yy, actual, index)) in enumerate(zip(PLANES, slices)):
                label_indices = (world.reshape(-1, 3) - origin) @ inverse.T - low
                sampled = ndimage.map_coordinates(mask.astype('u1'), label_indices.T, order=0, mode='constant', cval=0).reshape(pixels.shape).astype(bool)
                lines = section(triangles, axis, actual, horizontal, vertical)
                mesh_mask = raster_section(lines, xx, yy)
                denominator = int(sampled.sum() + mesh_mask.sum())
                dice = float(2 * np.count_nonzero(sampled & mesh_mask) / denominator) if denominator else None
                record['planes'].append({'sequence': sequence_name, 'plane': plane_name,
                    'requested_world_coordinate_mm': requested[axis], 'actual_world_coordinate_mm': actual,
                    'source_image_index': index, 'mesh_label_plane_dice': dice,
                    'source_label_pixels': int(sampled.sum()), 'mesh_section_pixels': int(mesh_mask.sum()),
                    'display_window_uncalibrated': window})
                for row in (sequence * 2, sequence * 2 + 1):
                    ax = axes[row, column]
                    dx, dy = abs(xx[1] - xx[0]), abs(yy[1] - yy[0])
                    ax.imshow(pixels, cmap='gray', origin='lower', interpolation='nearest',
                        extent=[xx[0] - dx / 2, xx[-1] + dx / 2, yy[0] - dy / 2, yy[-1] + dy / 2],
                        vmin=window[0], vmax=window[1])
                    ax.set_aspect('equal'); ax.set_xlabel('LPS ' + 'XYZ'[horizontal] + ' mm'); ax.set_ylabel('LPS ' + 'XYZ'[vertical] + ' mm')
                    if row % 2:
                        if sampled.any(): ax.contour(xx, yy, sampled, [.5], colors=['#ffd037'], linewidths=1)
                        ax.add_collection(LineCollection(lines, colors='#28dfeb', linewidths=.65))
                        ax.set_title(f'Mesh/label comparison · Dice {dice:.3f}' if dice is not None else 'No contour at this plane', fontsize=9)
                    else:
                        ax.set_title(f'{plane_name} · {"XYZ"[axis]}={actual:.2f} mm\n{sequence_name}', fontsize=9)
        fig.suptitle(part['name'] + ' — native-coordinate source review', fontsize=15)
        fig.text(.5, .018, 'Yellow: author label · Cyan: source mesh intersection · Raw pixels above each overlay row\n'
                 'No fitted alignment. Mesh/label agreement is not independent anatomical or clinical validation. CC0 source.',
                 ha='center', fontsize=9)
        fig.tight_layout(rect=(0, .045, 1, .97))
        filename = part['id'] + '-source-planes.png'
        fig.savefig(OUT / filename, dpi=130); plt.close(fig)
        record['review_image'] = filename
        report['structures'].append(record)
        print(part['name'], 'voxels', len(voxels), 'volume-delta%', round(record['mesh_volume_difference_percent'], 2),
              'plane-Dice', [round(p['mesh_label_plane_dice'], 3) if p['mesh_label_plane_dice'] is not None else None for p in record['planes']], flush=True)
    (OUT / 'paired-source-audit.json').write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    main()
