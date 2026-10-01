#!/usr/bin/env python3
"""Preserve all LNQ label components in an offline native surface baseline."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


def build(source_root, review_path, output):
    import numpy as np
    import nibabel as nib
    from tools.anatomy_sources.massp_probability_mesh import mesh_mask
    from tools.anatomy_sources.audit_massp_mesh_voxels import section, raster_section
    report = json.loads(review_path.read_text())
    path = source_root / 'lnq-case-0571-derived/source-annotation-on-ct-indices.npy'
    if hashlib.sha256(path.read_bytes()).hexdigest() != report['reconstructed_mask_sha256']:
        raise ValueError('Reconstructed source selection changed')
    labels = np.load(path)
    if (list(labels.shape) != report['ct_shape_zyx'] or int(labels.sum()) != report['encoded_annotation_voxels']
            or set(np.unique(labels)) != {0, 1}):
        raise ValueError('Source selection differs')
    offset = np.asarray(report['frame_records'][0]['seg_position_lps']) - np.asarray(report['frame_records'][0]['ct_position_lps'])
    origin = np.asarray(report['ct_origin_lps']) + offset
    z_spacing, y_spacing, x_spacing = report['ct_spacing_zyx_mm']
    affine = np.array([[0, 0, -x_spacing, -origin[0]], [0, -y_spacing, 0, -origin[1]],
                       [z_spacing, 0, 0, origin[2]], [0, 0, 0, 1]], dtype=float)
    vertices, faces, stats = mesh_mask(labels.astype(bool), affine)
    native = nib.affines.apply_affine(np.linalg.inv(affine), vertices)
    triangles = native[faces]
    low = np.floor(native.min(0)).astype(int) - 1
    high = np.ceil(native.max(0)).astype(int) + 2
    if np.any(low < 0) or np.any(high > labels.shape):
        raise ValueError('Surface outside source grid')
    xs, ys = np.arange(low[2], high[2]), np.arange(low[1], high[1])
    tested = positive = false_positive = false_negative = 0
    for z in range(low[0], high[0]):
        predicted = raster_section(section(triangles, 0, z, 2, 1), xs, ys)
        expected = labels[z, low[1]:high[1], low[2]:high[2]] > 0
        false_positive += int(np.count_nonzero(predicted & ~expected))
        false_negative += int(np.count_nonzero(expected & ~predicted))
        tested += expected.size; positive += int(expected.sum())
    if positive != report['encoded_annotation_voxels']:
        raise ValueError('Full source annotation extent was not compared')
    output.mkdir(parents=True, exist_ok=True)
    mesh_path = output / 'case-0571-source-annotation.npz'
    np.savez_compressed(mesh_path, vertices=vertices, faces=faces)
    result = {'case_id': 'case_0571', 'source_doi': report['source_doi'], 'source_review_sha256': hashlib.sha256(review_path.read_bytes()).hexdigest(),
        'source_selection_sha256': report['reconstructed_mask_sha256'], 'mesh_sha256': hashlib.sha256(mesh_path.read_bytes()).hexdigest(),
        'mesh_file': mesh_path.name, 'index_axes': 'z,y,x', 'world_coordinates': 'RAS millimetres', 'native_seg_affine_zyx_to_ras': affine.tolist(),
        'source_ct_to_seg_position_difference_preserved_mm': offset.tolist(), 'source_coordinate_registration_fitted': False,
        **stats, 'compared_voxel_centres': tested, 'complete_source_positive_voxels_compared': positive,
        'false_positive_voxel_interiors': false_positive, 'false_negative_voxel_interiors': false_negative,
        'exact_native_voxel_centre_match': false_positive == 0 and false_negative == 0,
        'named_station_identity_verified': False, 'individual_node_count_verified': False,
        'clinical_approval': False, 'runtime_promoted': False,
        'limitations': ['Native 2.5 mm slice sampling remains anisotropic; mesh interpolation is derived, not a finer measured boundary.',
                        'All five connected source components retained; no node or station identities invented.',
                        'This check proves source-export consistency at voxel centres, not anatomical accuracy or continuous self-contact absence.',
                        'Annotation coverage and node malignancy remain source/case review obligations.']}
    (output / 'surface-review.json').write_text(json.dumps(result, indent=2) + '\n')
    print('Triangles', len(faces), '; all source voxels', positive, '; false positive/negative', false_positive, false_negative)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source-root', type=Path, required=True); p.add_argument('--review', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True); a = p.parse_args(); build(a.source_root, a.review, a.output)
