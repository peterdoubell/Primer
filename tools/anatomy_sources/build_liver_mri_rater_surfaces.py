#!/usr/bin/env python3
"""Retain independent liver MRI rater surfaces and audit full native voxel extents."""
import argparse
import hashlib
import json
from pathlib import Path


def audit_voxel_centres(mask, affine, vertices, faces):
    import numpy as np
    import nibabel as nib
    from tools.anatomy_sources.audit_massp_mesh_voxels import section, raster_section
    native = nib.affines.apply_affine(np.linalg.inv(affine), vertices)
    triangles = native[faces]
    lo = np.floor(native.min(0)).astype(int) - 1
    hi = np.ceil(native.max(0)).astype(int) + 2
    if np.any(lo < 0) or np.any(hi > mask.shape):
        raise ValueError('Surface audit region leaves source grid')
    horizontal = np.arange(lo[0], hi[0]); vertical = np.arange(lo[1], hi[1])
    planes = []; compared = positive = false_positive = false_negative = 0
    for z in range(lo[2], hi[2]):
        predicted = raster_section(section(triangles, 2, z, 0, 1), horizontal, vertical)
        expected = mask[lo[0]:hi[0], lo[1]:hi[1], z].T
        fp = int(np.count_nonzero(predicted & ~expected)); fn = int(np.count_nonzero(expected & ~predicted))
        positive += int(expected.sum()); compared += expected.size; false_positive += fp; false_negative += fn
        planes.append({'native_z_index': int(z), 'source_positive_voxels': int(expected.sum()), 'false_positive': fp, 'false_negative': fn})
    if positive != int(mask.sum()):
        raise ValueError('Full source annotation extent was not compared')
    return {'bounds_start_ijk': lo.tolist(), 'bounds_stop_exclusive_ijk': hi.tolist(),
            'compared_voxel_centres': int(compared), 'complete_source_positive_voxels': positive,
            'false_positive': false_positive, 'false_negative': false_negative,
            'exact_voxel_centre_match': false_positive == 0 and false_negative == 0, 'planes': planes,
            'outside_audit_region': 'All triangles lie within the audit bounds; source positives outside are absent by full-mask count.'}


def build(root, inventory_path, output, report_path):
    import numpy as np
    import nibabel as nib
    from tools.anatomy_sources.massp_probability_mesh import mesh_mask, MeshTopologyError
    from tools.anatomy_sources.audit_lnq_surface_geometry import topology
    from skimage.measure import euler_number
    inventory = json.loads(inventory_path.read_text()); entries = {row['filename']: row for row in inventory['records']}
    images = {}; masks = {}
    for name in ['art.nii.gz', 'rater1_liver.nii.gz', 'rater2_liver.nii.gz', 'rater1_tumor1.nii.gz', 'rater2_tumor1.nii.gz']:
        path = root / name
        if hashlib.sha256(path.read_bytes()).hexdigest() != entries[name]['sha256']:
            raise ValueError('Source MRI or mask changed')
        images[name] = nib.load(path)
    arterial = images['art.nii.gz']; rows = []; output.mkdir(parents=True, exist_ok=True)
    for name, image in images.items():
        if name == 'art.nii.gz': continue
        if image.shape != arterial.shape or not np.array_equal(image.affine, arterial.affine):
            raise ValueError('Independent rater mask geometry differs from source arterial MRI')
        values = np.asanyarray(image.dataobj)
        if set(np.unique(values)) != {0, 1}:
            raise ValueError('Expected source binary mask')
        mask = values > 0; masks[name] = mask
        row = {'source_file': name, 'source_sha256': entries[name]['sha256'], 'source_affine_ijk_to_ras': image.affine.tolist(),
               'source_shape_ijk': list(image.shape), 'source_sampling_mm': list(map(float, image.header.get_zooms()[:3])),
               'clinical_approval': False, 'source_rater_boundary_changed': False}
        try:
            vertices, faces, stats = mesh_mask(mask, image.affine)
        except MeshTopologyError as error:
            row.update(status='held_source_surface_topology', mesh_created=False, diagnostics=error.diagnostics); rows.append(row)
            print(name, 'held', flush=True); continue
        path = output / (name.removesuffix('.nii.gz') + '.npz')
        np.savez_compressed(path, vertices=vertices, faces=faces)
        topo = topology(vertices, faces)
        for component in topo['mesh_components']:
            component.pop('independent_node_identity_verified', None); component.pop('station_identity_verified', None)
            chi = component['euler_characteristic']
            manifold = all(topo[key] == 0 for key in ('boundary_edges', 'nonmanifold_edges', 'inconsistent_closed_edge_orientation', 'nonmanifold_vertex_count'))
            component['orientable_closed_surface_genus'] = (2 - chi) // 2 if manifold and chi <= 2 and chi % 2 == 0 else None
            component['anatomical_cause_of_surface_topology_verified'] = False
        row.update(mesh_created=True, mesh_file=path.name, mesh_sha256=hashlib.sha256(path.read_bytes()).hexdigest(), extraction=stats,
                   topology=topo, voxel_centre_audit=audit_voxel_centres(mask, image.affine, vertices, faces),
                   continuous_self_contacts_audited=False,
                   native_mask_euler_6_connectivity=int(euler_number(mask, connectivity=1)),
                   native_mask_euler_26_connectivity=int(euler_number(mask, connectivity=3)),
                   status='held_unclassified_source_surface_handles' if any((c['orientable_closed_surface_genus'] or 0) > 0 for c in topo['mesh_components']) else 'offline_independent_rater_candidate_requires_boundary_and_contact_review')
        rows.append(row)
        audit = row['voxel_centre_audit']; print(name, 'triangles', len(faces), 'source positives', int(mask.sum()), 'FP/FN', audit['false_positive'], audit['false_negative'], flush=True)
    relations = []
    for rater in (1, 2):
        liver = masks[f'rater{rater}_liver.nii.gz']; tumour = masks[f'rater{rater}_tumor1.nii.gz']
        relations.append({'rater': rater, 'tumour_voxels': int(tumour.sum()), 'tumour_voxels_in_liver_mask': int((tumour & liver).sum()),
                          'tumour_voxels_outside_liver_mask': int((tumour & ~liver).sum()),
                          'mask_relation_is_clinical_invasion': False, 'source_masks_merged_or_repaired': False})
    result = {'case_id': inventory['case_id'], 'source_doi': inventory['source_doi'],
              'source_inventory_sha256': hashlib.sha256(inventory_path.read_bytes()).hexdigest(),
              'original_arterial_sha256': entries['art.nii.gz']['sha256'], 'records': rows, 'same_rater_mask_relations': relations,
              'world_coordinates': 'Original declared RAS millimetres; no fitting or resampling',
              'source_components_pruned': False, 'source_raters_averaged_or_selected_as_truth': False,
              'smoothing_or_decimation': False, 'clinical_approval': False, 'runtime_promoted': False,
              'limits': ['Each surface reproduces one source rater selection, not a consensus or independent anatomical truth.',
                         'Native voxel-centre consistency and manifold topology do not prove continuous contact absence or anatomical fidelity.',
                         'Interpolation between original 1.40625 × 1.40625 × 2.5 mm samples does not measure a finer boundary.',
                         'Liver/tumour mask relations describe annotations only; no clinical invasion, compartment or treatment interpretation is granted.',
                         'No capsule, segmental vessels, bile ducts, other lesions or complete reporting anatomy is supplied by these masks.']}
    report_path.write_text(json.dumps(result, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case-root', type=Path, required=True); parser.add_argument('--inventory', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True); parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args(); build(args.case_root, args.inventory, args.output, args.report)
