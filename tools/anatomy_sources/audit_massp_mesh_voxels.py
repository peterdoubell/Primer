#!/usr/bin/env python3
"""Compare complete native voxel-centre selections with exported surface interiors."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import nibabel as nib
from tools.anatomy_sources.massp_probability_mesh import load_verified

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
    if not np.all(np.isfinite(points[:, :, 0]).sum(axis=1) == 2):
        raise ValueError('Ambiguous source-plane intersection')
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


def audit(root, mesh_root, output):
    source = json.loads((root/'acquisition.json').read_text())
    manifest = json.loads((mesh_root/'surface-review.json').read_text())
    image = load_verified(root,manifest['publisher_selection_file'],source)
    labels = np.asarray(image.dataobj)
    records = []
    for row in manifest['records']:
        if not row['output_mesh_created']:
            raise ValueError('Held mesh cannot enter coverage audit')
        path = mesh_root/row['mesh_file']
        if hashlib.sha256(path.read_bytes()).hexdigest() != row['mesh_sha256']:
            raise ValueError('Exported mesh changed')
        with np.load(path) as mesh:
            points = nib.affines.apply_affine(np.linalg.inv(image.affine),mesh['vertices'])
            faces = mesh['faces'].copy()
        triangles = points[faces]
        lo = np.floor(points.min(0)).astype(int)-1
        hi = np.ceil(points.max(0)).astype(int)+2
        if np.any(lo<0) or np.any(hi>np.array(labels.shape)):
            raise ValueError('Mesh coverage region leaves source grid')
        horizontal = np.arange(lo[0],hi[0]); vertical = np.arange(lo[1],hi[1])
        compared = false_positive = false_negative = expected_total = predicted_total = 0
        planes = []
        for z in range(lo[2],hi[2]):
            lines = section(triangles,2,z,0,1)
            predicted = raster_section(lines,horizontal,vertical)
            expected = labels[lo[0]:hi[0],lo[1]:hi[1],z].T == row['label_id']
            fp = int(np.count_nonzero(predicted & ~expected))
            fn = int(np.count_nonzero(expected & ~predicted))
            false_positive += fp; false_negative += fn
            expected_total += int(expected.sum()); predicted_total += int(predicted.sum()); compared += expected.size
            planes.append({'native_z_index':z,'expected_label_voxels':int(expected.sum()),
                           'surface_interior_voxels':int(predicted.sum()),'false_positive':fp,'false_negative':fn})
        full_source_count = int(np.count_nonzero(labels==row['label_id']))
        if expected_total != full_source_count:
            raise ValueError('Compared region omits labelled source voxels')
        records.append({'label_id':row['label_id'],'code':row['code'],'side':row['side'],
                        'mesh_sha256':row['mesh_sha256'],'native_bounds_start':lo.tolist(),'native_bounds_stop_exclusive':hi.tolist(),
                        'all_source_target_voxels':full_source_count,'source_target_voxels_in_compared_region':expected_total,
                        'surface_interior_voxels':predicted_total,'compared_voxel_centres':compared,
                        'false_positive':false_positive,'false_negative':false_negative,'planes':planes,
                        'complete_source_target_extent_included':True,'exact_voxel_centre_match':false_positive==0 and false_negative==0})
        print(row['code'],row['side'],false_positive,false_negative,flush=True)
    result={'source_doi':source['doi'],'publisher_selection_file':manifest['publisher_selection_file'],
            'mesh_manifest_sha256':hashlib.sha256((mesh_root/'surface-review.json').read_bytes()).hexdigest(),
            'method':'Independent triangle/plane sections on every native Z voxel-centre plane, even/odd 2D fill at all native X/Y centres within complete model bounds. Coplanar face boundaries and shared on-plane edges retained and deduplicated. No fitted transform, resampling, shape edit or jitter.',
            'records':records,'clinical_approval':False,'source_values_changed':False,
            'limits':'Surface-to-publisher-label consistency at every compared voxel centre only. Does not establish independent MRI accuracy, continuous subvoxel fidelity, self-intersection absence or clinical approval.'}
    output.write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True);parser.add_argument('--meshes',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();audit(args.source,args.meshes,args.output)
