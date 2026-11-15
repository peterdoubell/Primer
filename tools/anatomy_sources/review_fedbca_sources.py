#!/usr/bin/env python3
"""Independently read all distributed FedBCa voxels and source spatial forms."""
import argparse
import gzip
import hashlib
import itertools
import json
import math
from pathlib import Path
import struct


def read_nifti(path):
    import numpy as np
    raw = gzip.decompress(path.read_bytes())
    if len(raw) < 352 or struct.unpack_from('<i', raw)[0] != 348 or raw[344:348] != b'n+1\0':
        raise ValueError('Complete little-endian single-file NIfTI-1 required')
    dims = struct.unpack_from('<8h', raw, 40); code, bits = struct.unpack_from('<2h', raw, 70)
    types = {2: 'u1', 4: '<i2', 8: '<i4', 16: '<f4', 64: '<f8', 512: '<u2'}
    if dims[0] != 3 or min(dims[1:4]) < 1 or any(d not in [0, 1] for d in dims[4:]) or code not in types:
        raise ValueError('Unsupported source dimensions/datatype')
    dtype = np.dtype(types[code]); offset_float = struct.unpack_from('<f', raw, 108)[0]; offset = int(offset_float)
    if offset != offset_float or offset < 352 or bits != dtype.itemsize * 8 or len(raw) != offset + math.prod(dims[1:4]) * dtype.itemsize:
        raise ValueError('Original scalar extent differs')
    values = np.frombuffer(raw, dtype=dtype, count=math.prod(dims[1:4]), offset=offset).reshape(dims[1:4], order='F')
    if not np.isfinite(values).all(): raise ValueError('Nonfinite source values')
    pixdim = struct.unpack_from('<8f', raw, 76); qcode, scode = struct.unpack_from('<2h', raw, 252)
    slope, intercept = struct.unpack_from('<2f', raw, 112)
    qform = None; sform = None
    if scode > 0:
        sform = np.eye(4); sform[:3] = np.array(struct.unpack_from('<12f', raw, 280)).reshape(3, 4)
    if qcode > 0:
        b, c, d, x, y, z = struct.unpack_from('<6f', raw, 256)
        a2 = 1.0 - (b*b + c*c + d*d)
        # NIfTI quaternion convention, without changing source header values.
        if abs(a2) < 3 * np.finfo(np.float32).eps:
            length = math.sqrt(b*b+c*c+d*d)
            if length == 0: raise ValueError('Invalid source quaternion')
            b, c, d = b/length, c/length, d/length; a = 0.0
        else:
            if a2 < 0: raise ValueError('Invalid source quaternion norm')
            a = math.sqrt(a2)
        rotation = np.array([[a*a+b*b-c*c-d*d, 2*b*c-2*a*d, 2*b*d+2*a*c],
                             [2*b*c+2*a*d, a*a+c*c-b*b-d*d, 2*c*d-2*a*b],
                             [2*b*d-2*a*c, 2*c*d+2*a*b, a*a+d*d-c*c-b*b]])
        if min(pixdim[1:4]) <= 0 or pixdim[0] not in [-1, 1]: raise ValueError('Invalid source qform spacing/qfac')
        qform = np.eye(4); qform[:3, :3] = rotation @ np.diag([pixdim[1], pixdim[2], pixdim[3]*pixdim[0]]); qform[:3, 3] = [x,y,z]
    affine = sform if sform is not None else qform
    if affine is None or not np.isfinite(affine).all() or abs(np.linalg.det(affine[:3,:3])) < 1e-12:
        raise ValueError('Explicit nondegenerate source spatial form required')
    return values, affine, {'dimensions': list(values.shape), 'datatype': code, 'bitpix': bits, 'vox_offset': offset,
        'pixdim': list(pixdim), 'xyzt_units': raw[123], 'slope': slope, 'intercept': intercept, 'qform_code': qcode, 'sform_code': scode,
        'source_quaternion_bcd_offsets': list(struct.unpack_from('<6f', raw, 256)),
        'qform_float32_near_180_policy': 'Derived rotation uses three Float32 eps for near-zero quaternion w-squared; original header values unchanged',
        'source_qform': qform.tolist() if qform is not None else None, 'source_sform': sform.tolist() if sform is not None else None,
        'selected_form': 'sform' if sform is not None else 'qform', 'selected_affine': affine.tolist(),
        'raw_source_voxel_sha256': hashlib.sha256(raw[offset:]).hexdigest(), 'compressed_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
        'uncompressed_sha256': hashlib.sha256(raw).hexdigest(), 'source_voxels': int(values.size), 'raw_value_range': [float(values.min()), float(values.max())]}


def review(root, output):
    import nibabel as nib
    import numpy as np
    paths = sorted((root / 'all-nifti').rglob('*.nii.gz'))
    if len(paths) != 496 or any(p.is_symlink() for p in paths): raise ValueError('Complete 496 regular source files required')
    records = {}; all_voxels = 0
    for path in paths:
        array, affine, row = read_nifti(path); library = nib.load(path); independent = library.dataobj.get_unscaled()
        if not np.array_equal(array, independent) or not np.allclose(affine, library.affine, rtol=0, atol=1e-9):
            raise ValueError('Independent complete source decoder/affine differs: ' + path.name)
        for key, method in [('source_qform', library.get_qform), ('source_sform', library.get_sform)]:
            if row[key] is not None and not np.allclose(row[key], method(), rtol=0, atol=1e-9):
                raise ValueError('Independent source spatial form differs: '+path.name+' '+key+' max='+str(float(np.max(np.abs(np.asarray(row[key])-method())))))
        member = path.relative_to(root / 'all-nifti').as_posix(); row['source_archive_member'] = member
        row['all_stored_values_independently_decoded'] = True; all_voxels += array.size
        if '/Annotation/' in member:
            labels, counts = np.unique(array, return_counts=True)
            if set(labels) != {0,1} or row['slope'] not in [0,1] or row['intercept'] != 0:
                raise ValueError('Binary unscaled producer annotation required')
            row['label_voxels'] = {str(int(k)): int(v) for k,v in zip(labels,counts)}
        if row['source_qform'] is not None and row['source_sform'] is not None:
            corners = np.array([list(p)+[1] for p in itertools.product(*[(0,n-1) for n in array.shape])])
            row['qform_sform_max_corner_difference_mm'] = float(np.linalg.norm((corners@np.asarray(row['source_qform']).T)[:,:3]-(corners@np.asarray(row['source_sform']).T)[:,:3],axis=1).max())
        records[member] = row
        if len(records) % 40 == 0: print('Complete source files independently decoded:', len(records), flush=True)
    pairs=[]; blanks=[]
    for source in json.loads((root/'fedbca-table-correspondence-review.json').read_text()):
        if not source['image_present'] or not source['mask_present']:
            if source['source_fields'].get('image_name',source['source_fields'].get('image')) == '' and source['source_fields'].get('mask_new',source['source_fields'].get('mask_name')) == '':
                blanks.append(source);continue
            raise ValueError('Nonblank source table association missing from archive')
        image, mask = records[source['image_member']], records[source['mask_member']]
        if image['dimensions'] != mask['dimensions']: raise ValueError('Associated source array dimensions differ')
        corners = np.array([list(p)+[1] for p in itertools.product(*[(0,n-1) for n in image['dimensions']])])
        A=np.asarray(image['selected_affine']);B=np.asarray(mask['selected_affine'])
        pairs.append({**source,'selected_affines_bit_identical':np.array_equal(A,B),'max_grid_corner_difference_mm':float(np.linalg.norm((corners@A.T)[:,:3]-(corners@B.T)[:,:3],axis=1).max()),'image_or_mask_fitted_resampled_or_modified':False,'clinical_or_independent_anatomical_registration_approved':False})
    if len(pairs)!=275 or len({p['mask_member'] for p in pairs})!=275 or len({p['image_member'] for p in pairs})!=221:
        raise ValueError('Complete source image/annotation association accounting differs')
    output.mkdir(parents=True,exist_ok=True)
    report={'source_record':13622759,'source_doi':'10.5281/zenodo.13622759','source_image_files':221,'source_annotation_files':275,
            'all_source_files':496,'all_source_voxels_independently_decoded':int(all_voxels),'complete_source_records':records,'complete_table_pairs':pairs,
            'blank_source_table_rows_retained':blanks,'original_DICOM_acquisitions_received':False,'clinical_approval':False,
            'all_reportable_wall_layers_or_native3D_extent_approved':False,'source_values_or_geometry_modified':False,'runtime_promoted':False}
    raw=(json.dumps(report,indent=2)+'\n').encode();packed=gzip.compress(raw,mtime=0);assert gzip.decompress(packed)==raw
    (output/'complete-source-review.json.gz').write_bytes(packed)
    summary={k:v for k,v in report.items() if k not in ['complete_source_records','complete_table_pairs','blank_source_table_rows_retained']}
    summary.update({'pairs_with_bit_identical_selected_affines':sum(p['selected_affines_bit_identical'] for p in pairs),
                    'max_pair_corner_difference_mm':max(p['max_grid_corner_difference_mm'] for p in pairs),
                    'review_sha256':hashlib.sha256(packed).hexdigest(),'blank_source_table_rows':len(blanks)})
    (output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print('Complete source review saved.',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();review(a.root,a.output)
