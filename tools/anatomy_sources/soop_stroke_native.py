"""Lossless SOOP source-index arrays and all three literal source mask boundaries.

Fixed source subject and output paths. No resampling, inferred registration, mask
union, anatomy labels, clinical judgement, or component filtering is performed.
"""
from pathlib import Path
import gzip
import hashlib
import json
import struct
import nibabel as nib
import numpy as np
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'web/anatomy/soop-stroke-sub342'
REVIEW = ROOT / 'docs/soop-stroke-native-source-review-20261011'
BASE = '/app/anatomy/soop-stroke-sub342/'
ROLES = {
    'trace': 'sub-342_rec-TRACE_dwi.nii.gz',
    'adc': 'sub-342_rec-ADC_dwi.nii.gz',
    't1': 'sub-342_T1w.nii.gz',
    'flair': 'sub-342_FLAIR.nii.gz',
    'acute': 'sub-342_space-TRACE_desc-lesionAcute_mask.nii.gz',
    'chronic': 'sub-342_space-TRACE_desc-lesionChronic_mask.nii.gz',
    'combined': 'sub-342_space-TRACE_desc-lesion_mask.nii.gz',
}
MASKS = ('acute', 'chronic', 'combined')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def cell_boundary(mask, affine):
    """Every exposed source cell face; corners are exactly index +/-0.5."""
    points, triangles, index, records = [], [], {}, []
    for axis in range(3):
        other = [x for x in range(3) if x != axis]
        for sign in (-1, 1):
            neighbor = np.zeros_like(mask, dtype=bool)
            dest, src = [slice(None)] * 3, [slice(None)] * 3
            dest[axis] = slice(0, -1) if sign == 1 else slice(1, None)
            src[axis] = slice(1, None) if sign == 1 else slice(0, -1)
            neighbor[tuple(dest)] = mask[tuple(src)]
            for p in np.argwhere(mask & ~neighbor):
                corners = []
                for a, b in [(-1, -1), (1, -1), (1, 1), (-1, 1)]:
                    q = 2 * p.copy()
                    q[axis] += sign
                    q[other[0]] += a
                    q[other[1]] += b
                    corners.append(tuple(map(int, q)))
                v = np.asarray(corners, dtype=float) / 2
                if np.cross(v[1] - v[0], v[2] - v[0])[axis] * sign < 0:
                    corners.reverse()
                ids = []
                for q in corners:
                    if q not in index:
                        index[q] = len(points)
                        points.append(q)
                    ids.append(index[q])
                triangles.extend([(ids[0], ids[1], ids[2]), (ids[0], ids[2], ids[3])])
                records.append([*map(int, p), axis, sign])
    voxel = np.asarray(points, dtype='<f8') / 2
    world = np.column_stack([
        affine[r, 3] + sum(affine[r, c] * voxel[:, c] for c in range(3))
        for r in range(3)
    ]).astype('<f8')
    faces = np.asarray(triangles, dtype='<u4')
    if np.linalg.det(affine[:3, :3]) < 0:
        faces = faces[:, [0, 2, 1]]
    return world, faces, np.asarray(records, dtype='<i4'), voxel


def payload(name, raw):
    compressed = gzip.compress(raw, mtime=0)
    (OUT / name).write_bytes(compressed)
    return dict(file=BASE + name, bytes=len(compressed), sha256=sha(compressed),
                decoded_bytes=len(raw), decoded_sha256=sha(raw), codec='gzip',
                source_sample_changes=False)


def build():
    receipt_bytes = (REVIEW / 'source/sub-342-acquisition.json').read_bytes()
    if sha(receipt_bytes) != 'a9913b4a7b56152ea53e79afaeb5baacb47c1d8eeee954832b1159792d943767':
        raise ValueError('Pinned source acquisition receipt differs')
    receipt = json.loads(receipt_bytes)
    if receipt['pinned_root_tree'] != 'a62344db73f18f384a95b452f4a1a423087e059b' or receipt['subject'] != 'sub-342':
        raise ValueError('Fixed source binding changed')
    manifest = dict(schema_version=1, id='soop-stroke-sub342', source_case='sub-342',
        dataset='ds004889', version='1.1.2', source_url='https://doi.org/10.18112/openneuro.ds004889.v1.1.2',
        publication_url='https://doi.org/10.1038/s41597-024-03667-5', license='CC0',
        license_url='https://creativecommons.org/publicdomain/zero/1.0/',
        attribution='Rorden, Absher and Newman-Norlund. Stroke Outcome Optimization Project (SOOP), OpenNeuro ds004889 v1.1.2. CC0. Source images and three source labels unchanged; lossless transport and literal voxel-cell geometry added.',
        pinned_root_tree=receipt['pinned_root_tree'], arrays={}, meshes={},
        clinical_approval=False, fine_anatomical_approval=False, structure_coverage_granted=False,
        current_patient_registration=False, T1_registered_to_diffusion=False,
        FLAIR_registered_to_diffusion=False, T1_registered_to_FLAIR=False,
        ADC_physical_units_verified=False, timing_or_pretreatment_state_known=False,
        complete_arrays_no_crop=True, source_resampling=False, source_sample_changes=False,
        source_defacing=True, source_skull_stripped=False,
        source_sampling_not_histologic_boundary_resolution=True,
        masks_are_separate_original_files=True, source_mask_union_performed=False,
        source_rater_method_uncertainty='Primary article describes trained neuroscientist manual annotation, but mentions T2, ADC and TRACE inconsistently. Data Records and filenames specify native TRACE-space released masks; neither timing nor histological validity is established.',
        source_dimensions_note='TRACE/ADC retain original 4D shape with one source frame. Its 0 temporal spacing supplies no temporal duration. Spatial controls select native i/j/k and fixed frame0; no original dimension is discarded.')
    arrays, images = {}, {}
    for role, name in ROLES.items():
        source = (OUT / name).read_bytes()
        record = next(x for x in receipt['files'] if Path(x['path']).name == name)
        if len(source) != record['bytes'] or sha(source) != record['sha256']:
            raise ValueError('Original source differs: ' + role)
        im = nib.load(OUT / name)
        raw = im.dataobj.get_unscaled()
        dtype = '<u1' if role in MASKS else '<i2'
        if raw.dtype != np.dtype(dtype) or not np.isfinite(raw).all():
            raise ValueError('Source storage type differs: ' + role)
        slope, intercept = float(im.dataobj.slope), float(im.dataobj.inter)
        if not np.isfinite([slope, intercept]).all():
            raise ValueError('Nonfinite source scaling')
        arrays[role], images[role] = raw, im
        row = payload(role + '.native.gz', raw.astype(dtype).tobytes(order='F'))
        scaled = raw.astype(np.float64) * slope + intercept
        nonzero = scaled[raw != 0]
        qform, qcode = im.header.get_qform(coded=True)
        sform, scode = im.header.get_sform(coded=True)
        row.update(dtype=dtype, shape=list(raw.shape), spatial_shape=list(raw.shape[:3]),
            frames=raw.shape[3] if raw.ndim == 4 else 1,
            affine=im.affine.tolist(), voxel_sizes_mm=list(map(float, im.header.get_zooms()[:3])),
            all_dimension_spacing=list(map(float, im.header.get_zooms())),
            qform=None if qform is None else qform.tolist(), qform_code=int(qcode),
            sform=None if sform is None else sform.tolist(), sform_code=int(scode),
            selected_affine_method='nibabel best affine; sform when valid',
            axis_codes=list(nib.aff2axcodes(im.affine)), source_units=list(im.header.get_xyzt_units()),
            slope=slope, intercept=intercept, raw_min=int(raw.min()), raw_max=int(raw.max()),
            scaled_min=float(scaled.min()), scaled_max=float(scaled.max()),
            nonzero=int(np.count_nonzero(raw)), source_file=BASE + name,
            source_file_sha256=sha(source), source_file_bytes=len(source),
            source_grid='diffusion' if role in ('trace', 'adc', *MASKS) else role,
            display_window=[0, 1] if role in MASKS else list(map(float, np.percentile(nonzero, [1, 99]))))
        manifest['arrays'][role] = row
        del scaled, nonzero
    for role in ('adc', *MASKS):
        if arrays[role].shape[:3] != arrays['trace'].shape[:3] or not np.array_equal(images[role].affine, images['trace'].affine):
            raise ValueError('Exact source TRACE grid is required for linked overlay')
    manifest['diffusion_and_masks_stored_affines_equal'] = True
    for role in MASKS:
        raw = arrays[role]
        if set(np.unique(raw)) != {0, 1}:
            raise ValueError('Source mask label IDs changed')
        mask = raw == 1
        positions, faces, records, voxel = cell_boundary(mask, images[role].affine)
        geometry = b'SPV1' + struct.pack('<II', len(positions), len(faces)) + positions.tobytes() + faces.tobytes()
        row = payload(role + '-cell-boundary.native.gz', geometry)
        connectivity = {}
        for c, label in ((1, '6'), (3, '26')):
            component, count = ndimage.label(mask, ndimage.generate_binary_structure(3, c))
            connectivity[label] = dict(components=int(count), voxel_counts_descending=sorted(map(int, np.bincount(component.ravel())[1:]), reverse=True))
        row.update(source_mask_role=role, vertices=len(positions), triangles=len(faces),
            exposed_original_cell_faces=len(records), native_mask_voxels=int(mask.sum()),
            label_volume_ml=float(mask.sum() * abs(np.linalg.det(images[role].affine[:3, :3])) / 1000),
            positions_dtype='<f8', indices_dtype='<u4', bounds_RAS_mm=[positions.min(0).tolist(), positions.max(0).tolist()],
            world_positions_sha256=sha(positions.tobytes()), triangle_indices_sha256=sha(faces.tobytes()),
            voxel_corner_sha256=sha(voxel.tobytes()), complete_exposed_face_records_sha256=sha(records.tobytes()),
            connectivity=connectivity, source_mask_sha256=manifest['arrays'][role]['source_file_sha256'],
            boundary_definition='Every original mask=1 voxel cell at +/-0.5 source index; no interpolation, smoothing, decimation, union, component removal or healing.',
            world_coordinate_convention='RAS millimetres from exact selected source affine',
            GPU_display_rounding='Float64 geometry is retained and verified. GPU display coordinates/normals are float32; this does not add source resolution.',
            edge_or_corner_contacts_may_be_nonmanifold=True,
            label_volume_is_pretreatment_core_or_irreversible_tissue=False,
            clinical_or_named_anatomical_boundary_approval=False)
        manifest['meshes'][role] = row
    pts = np.argwhere(arrays['acute'] == 1)
    manifest['initial_diffusion_cursor'] = pts[np.argmin(((pts - pts.mean(0)) ** 2).sum(axis=1))].tolist()
    # Audit combined source without constructing a replacement or changing any source.
    a, c, combined = (arrays[x] == 1 for x in MASKS)
    manifest['source_mask_comparison'] = dict(acute_chronic_overlap_voxels=int((a & c).sum()),
        combined_differs_from_boolean_union_voxels=int((combined != (a | c)).sum()), comparison_only_no_union_used=True)
    (OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    proof = dict(reviewed_at='2026-10-11', manifest_sha256=sha((OUT / 'manifest.json').read_bytes()),
        original_files=receipt['files'], source_original_bytes=receipt['total_bytes'],
        array_values={k: int(v.size) for k, v in arrays.items()},
        total_source_values=sum(int(v.size) for v in arrays.values()),
        meshes=manifest['meshes'], clinical_approval=False, fine_anatomical_approval=False)
    (REVIEW / 'native-source-proof.json').write_text(json.dumps(proof, indent=2) + '\n')
    print(json.dumps(dict(array_values=proof['array_values'], meshes={k: [v['native_mask_voxels'], v['triangles']] for k, v in manifest['meshes'].items()})))
    return manifest


if __name__ == '__main__':
    build()
