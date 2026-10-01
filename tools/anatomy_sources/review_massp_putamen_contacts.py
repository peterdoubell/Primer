#!/usr/bin/env python3
"""Localise native label-surface contacts without repairing source geometry."""
import argparse
import json
from pathlib import Path
import hashlib

import nibabel as nib
import numpy as np
from skimage import measure
from tools.anatomy_sources.massp_probability_mesh import load_verified


def review(root, output, background_record=None):
    output.mkdir(parents=True, exist_ok=True)
    source = json.loads((root / 'acquisition.json').read_text())
    image = load_verified(root, 'ahead-massp2_avg-maxlabel_decade-18to80.nii.gz', source)
    background_image = None
    if background_record:
        background = json.loads(background_record.read_text())
        if background['source_doi'] != source['doi']:
            raise ValueError('Background source version differs')
        background_image = load_verified(root,background['file']['name'],{'files':[background['file']]})
        if background_image.shape != image.shape or not np.array_equal(background_image.affine,image.affine):
            raise ValueError('Background grid differs')
    labels = np.asarray(image.dataobj)
    best_image = load_verified(root, 'ahead-massp2_avg-bestlabel_decade-18to80.nii.gz', source)
    if best_image.shape != image.shape or not np.array_equal(best_image.affine,image.affine):
        raise ValueError('Publisher label grids differ')
    best_labels = np.asarray(best_image.dataobj)
    records = []
    for label, side in ((38, 'l'), (39, 'r')):
        name = f'proba_ahead-massp2_avg-put_hem-{side}_decade-18to80_n97.nii.gz'
        prob_image = load_verified(root, name, source)
        if prob_image.shape != image.shape or not np.array_equal(prob_image.affine, image.affine):
            raise ValueError('Source grids differ')
        prob = np.asarray(prob_image.dataobj)
        mask = labels == label
        coords = np.argwhere(mask)
        lo, hi = coords.min(0) - 1, coords.max(0) + 2
        crop = mask[tuple(slice(a, b) for a, b in zip(lo, hi))]
        verts, faces, _, _ = measure.marching_cubes(crop.astype(np.float32), level=.5, allow_degenerate=False)
        verts = verts.astype(np.float64) + lo
        edges = np.sort(np.concatenate([faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]]), axis=1)
        unique_edges, counts = np.unique(edges, axis=0, return_counts=True)
        bad = unique_edges[counts > 2]
        contacts = []
        for edge in bad:
            ends = verts[edge]
            center = np.floor(ends.mean(0)).astype(int)
            start, stop = center - 2, center + 3
            selection = tuple(slice(a, b) for a, b in zip(start, stop))
            faces_at_edge = [int(i) for i, f in enumerate(faces) if set(edge).issubset(f)]
            contacts.append({'vertex_indices': edge.tolist(), 'native_index_endpoints': ends.tolist(),
                             'ras_mm_endpoints': nib.affines.apply_affine(image.affine, ends).tolist(),
                             'incident_faces': faces_at_edge, 'incident_face_count': len(faces_at_edge),
                             'patch_native_start': start.tolist(), 'patch_native_stop_exclusive': stop.tolist(),
                             'native_label_patch_xyz': labels[selection].astype(int).tolist(),
                             'native_probability_patch_xyz': prob[selection].tolist()})
        remaining = set(range(len(bad)))
        clusters = []
        while remaining:
            members = {remaining.pop()}
            nodes = set(bad[next(iter(members))])
            while True:
                neighbours = {i for i in remaining if nodes.intersection(bad[i])}
                if not neighbours:
                    break
                members.update(neighbours)
                remaining.difference_update(neighbours)
                nodes.update(bad[list(neighbours)].ravel())
            points = verts[sorted(nodes)]
            start, stop = np.floor(points.min(0)).astype(int)-2, np.ceil(points.max(0)).astype(int)+3
            patch = tuple(slice(a, b) for a, b in zip(start, stop))
            target_probability = prob[patch][labels[patch] == label]
            support_start, support_stop = np.floor(points.min(0)).astype(int), np.ceil(points.max(0)).astype(int)+1
            support = tuple(slice(a,b) for a,b in zip(support_start,support_stop))
            supporting_probability = prob[support][labels[support]==label]
            extra = {'native_support_publisher_best_labels_xyz': best_labels[support].astype(int).tolist()}
            if background_image is not None:
                values = np.asarray(background_image.dataobj[support])[labels[support]==label]
                if not np.isfinite(values).all() or values.min()<0 or values.max()>1:
                    raise ValueError('Invalid background probabilities')
                extra['native_support_background_probability_range_at_target_voxels']=[float(values.min()),float(values.max())]
            clusters.append({**extra, 'contact_indices': sorted(members),
                             'native_support_start': support_start.tolist(), 'native_support_stop_exclusive': support_stop.tolist(),
                             'native_support_labels_xyz': labels[support].astype(int).tolist(),
                             'native_support_probabilities_xyz': prob[support].tolist(),
                             'target_probability_range_in_contact_support': [float(supporting_probability.min()),float(supporting_probability.max())] if len(supporting_probability) else None, 'native_index_bounds': [points.min(0).tolist(),points.max(0).tolist()],
                             'patch_start': start.tolist(), 'patch_stop_exclusive': stop.tolist(),
                             'target_label_voxels_in_patch': int(len(target_probability)),
                             'publisher_bestlabel_target_voxels_in_same_patch': int(np.count_nonzero(best_labels[patch]==label)),
                             'target_selection_disagreement_between_publisher_label_maps': int(np.count_nonzero((best_labels[patch]==label)!=(labels[patch]==label))),
                             'target_probability_range_in_patch': [float(target_probability.min()),float(target_probability.max())] if len(target_probability) else None})
        records.append({'label_id': label, 'side': side, 'probability_file': name, 'contact_clusters': clusters,
                        'nonmanifold_edges': len(bad), 'contacts': contacts})
        print(side, len(bad), flush=True)
    result = {'source_doi': source['doi'], 'source_acquisition_sha256': hashlib.sha256((root/'acquisition.json').read_bytes()).hexdigest(),
              'source_affine': image.affine.tolist(), 'native_axis_codes': list(nib.aff2axcodes(image.affine)),
              'records': records, 'background_acquisition_record': str(background_record) if background_record else None, 'source_values_unchanged': True, 'mesh_repair_performed': False,
              'clinical_approval': False, 'limits': 'Contacts of the chosen binary label isosurface only. Source probabilities and labels are preserved; contact localisation does not prove clinical boundary or material identity.'}
    (output / 'putamen-contact-localisation.json').write_text(json.dumps(result, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--background-record',type=Path)
    args = parser.parse_args()
    review(args.source, args.output,args.background_record)
