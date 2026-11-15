#!/usr/bin/env python3
"""Compare native Open Knee(s) images, cropped labels and author-selected STLs.

Only declared NIfTI affines are used. MRI samples and original surfaces remain
unchanged. Label/mesh Dice is source consistency, not clinical ground truth.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

import numpy as np
from scipy import ndimage
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt
from matplotlib.collections import LineCollection
from audit_malaya_knee_images import section, raster_section, slice_plane


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def nifti(path):
    with path.open('rb') as source:
        raw = source.read(352)
    endian = '<' if struct.unpack_from('<i', raw)[0] == 348 else '>'
    def fields(fmt, offset):
        return struct.unpack_from(endian + fmt, raw, offset)
    if fields('i', 0)[0] != 348 or raw[344:348] != b'n+1\0':
        raise ValueError('Expected single-file NIfTI-1')
    dims = fields('8h', 40)
    datatype, bits = fields('2h', 70)
    pixdim = fields('8f', 76)
    offset, slope, intercept = fields('3f', 108)
    qcode, scode = fields('2h', 252)
    dtype = {2: 'u1', 4: 'i2', 8: 'i4', 16: 'f4', 512: 'u2'}[datatype]
    if dims[0] != 3 or raw[123] & 7 != 2 or int(offset) != offset:
        raise ValueError('Expected three-dimensional millimeter volume')
    if bits != np.dtype(dtype).itemsize * 8:
        raise ValueError('Inconsistent scalar type')
    affines = {}
    if qcode:
        b, c, d = fields('3f', 256)
        remainder = 1 - b*b - c*c - d*d
        if remainder < -1e-6:
            raise ValueError('Invalid quaternion')
        a = np.sqrt(max(0, remainder))
        rotation = np.array([
            [a*a+b*b-c*c-d*d, 2*(b*c-a*d), 2*(b*d+a*c)],
            [2*(b*c+a*d), a*a+c*c-b*b-d*d, 2*(c*d-a*b)],
            [2*(b*d-a*c), 2*(c*d+a*b), a*a+d*d-b*b-c*c],
        ])
        q = np.eye(4)
        q[:3,:3] = rotation @ np.diag([pixdim[1], pixdim[2], pixdim[3] * (-1 if pixdim[0] < 0 else 1)])
        q[:3,3] = fields('3f', 268)
        affines['qform'] = q
    if scode:
        s = np.eye(4)
        s[:3,:] = np.array(fields('12f', 280)).reshape(3,4)
        affines['sform'] = s
    if not affines:
        raise ValueError('No declared spatial affine')
    if len(affines) == 2 and not np.allclose(affines['qform'], affines['sform'], atol=1e-4, rtol=0):
        raise ValueError('Conflicting qform and sform')
    affine = affines.get('sform', affines.get('qform'))
    direction, origin = affine[:3,:3], affine[:3,3]
    if not np.all(np.count_nonzero(abs(direction) > 1e-7, axis=0) == 1):
        raise ValueError('Oblique volume requires a different native-plane audit')
    if path.stat().st_size != int(offset) + int(np.prod(dims[1:4])) * bits // 8:
        raise ValueError('Volume length differs from header')
    if slope not in (0, 1) or intercept != 0:
        raise ValueError('Unexpected scaling; inspect before comparison')
    data = np.memmap(path, mode='r', dtype=endian + dtype, offset=int(offset),
                     shape=tuple(reversed(dims[1:4]))).transpose(2,1,0)
    return {'data': data, 'directions': direction, 'origin': origin,
            'metadata': {'filename': path.name, 'bytes': path.stat().st_size,
                         'sha256': sha(path), 'shape_xyz': list(dims[1:4]),
                         'spacing_mm': list(pixdim[1:4]), 'datatype': datatype,
                         'qform_code': qcode, 'sform_code': scode,
                         'affines_ras_mm': {k:v.tolist() for k,v in affines.items()}}}


def mesh(path, expected_sha):
    if sha(path) != expected_sha:
        raise ValueError('Changed source STL')
    raw = path.read_bytes()
    count = struct.unpack_from('<I', raw, 80)[0]
    if len(raw) != 84 + 50 * count:
        raise ValueError('Unexpected binary STL size')
    record = np.dtype([('normal','<f4',(3,)), ('vertices','<f4',(3,3)), ('attribute','<u2')])
    return np.frombuffer(raw, dtype=record, count=count, offset=84)['vertices'].astype(float)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    native = args.source / 'oks003-native'
    mapping = json.loads((native / 'mask-mapping.json').read_text())
    geometry = json.loads((native / 'geometry-audit.json').read_text())
    images = [nifti(args.source / ('oks003-' + name + '-mri.nii')) for name in ('general','cartilage')]
    report = {'status':'Source correspondence review; no clinical approval',
              'specimen':'oks003', 'no_fitted_transform':True, 'no_source_geometry_edits':True,
              'coordinate_method':'Declared NIfTI qform/sform in RAS millimeters; original native STL coordinates, no fitting or reorientation.',
              'metric_limits':'Mask-versus-mesh consistency only. Source MRI pixels are not an independent expert tissue segmentation. Complete reporting substructures remain unverified.',
              'images':[image['metadata'] for image in images], 'structures':[]}
    for part in geometry['parts']:
        if part['id'] not in mapping:
            continue
        label = nifti(native / mapping[part['id']])
        values = np.unique(label['data'])
        if len(values) != 2 or values[0] != 0:
            raise ValueError('Expected one explicit binary label')
        points = np.argwhere(label['data'] != 0)
        world_points = points @ label['directions'].T + label['origin']
        center = np.median(world_points, axis=0)
        triangles = mesh(native / part['filename'], part['sha256'])
        bounds = np.array([triangles.min((0,1)), triangles.max((0,1))]) + np.array([[-6], [6]])
        inv = np.linalg.inv(label['directions'])
        entry = {'id':part['id'], 'mesh_file':part['filename'], 'mesh_sha256':part['sha256'],
                 'mask':label['metadata'], 'label_values':values.tolist(),
                 'mask_voxels':len(points), 'mask_voxel_centers_bounds_ras_mm':[world_points.min(0).tolist(),world_points.max(0).tolist()],
                 'mesh_bounds_ras_mm':[triangles.min((0,1)).tolist(),triangles.max((0,1)).tolist()],
                 'planes':[]}
        fig, plots = plt.subplots(4,3,figsize=(12,13))
        for image_index, image in enumerate(images):
            for plane_index, (name,axis,horizontal,vertical) in enumerate((('Sagittal',0,1,2),('Coronal',1,0,2),('Axial',2,0,1))):
                plane, world, x, y, actual, index = slice_plane(image,axis,center[axis],horizontal,vertical,bounds)
                coords = (world - label['origin']) @ inv.T
                mask = ndimage.map_coordinates(label['data'],np.moveaxis(coords,-1,0),order=0,mode='constant',cval=0) != 0
                lines = section(triangles,axis,actual,horizontal,vertical)
                rendered = raster_section(lines,x,y)
                denominator = int(mask.sum() + rendered.sum())
                dice = 2 * int((mask & rendered).sum()) / denominator if denominator else None
                extent=[x[0],x[-1],y[0],y[-1]]
                high=float(np.percentile(plane,99.5))
                for row in (image_index*2,image_index*2+1):
                    plot=plots[row,plane_index]
                    plot.imshow(plane,origin='lower',extent=extent,cmap='gray',vmin=0,vmax=max(high,1),interpolation='nearest')
                    plot.set_xlabel('RAS world axis %d (mm)' % horizontal)
                    plot.set_ylabel('RAS world axis %d (mm)' % vertical)
                plots[image_index*2,plane_index].set_title(('General' if image_index==0 else 'Cartilage')+' MRI — '+name)
                overlay=plots[image_index*2+1,plane_index]
                if mask.any(): overlay.contour(x,y,mask,levels=[.5],colors=['cyan'],linewidths=.8)
                overlay.add_collection(LineCollection(lines,colors='#ffc249',linewidths=.8))
                overlay.set_title('Mask/mesh overlap: %.3f' % (dice if dice is not None else float('nan')))
                entry['planes'].append({'image':image['metadata']['filename'],'plane':name,'world_coordinate_mm':actual,'native_index':index,'mask_pixels':int(mask.sum()),'mesh_pixels':int(rendered.sum()),'mask_mesh_dice':dice})
        fig.suptitle('Open Knee(s) oks003 '+part['id']+' — source MRI, label and mesh\nCyan: author label; gold: mesh. Declared affines only; no clinical approval',fontsize=13)
        fig.tight_layout()
        fig.savefig(args.output/(part['id'].lower()+'-source-planes.png'),dpi=135)
        plt.close(fig)
        report['structures'].append(entry)
        print(part['id'],[round(p['mask_mesh_dice'],3) if p['mask_mesh_dice'] is not None else None for p in entry['planes']],flush=True)
    (args.output/'paired-source-audit.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__ == '__main__':
    main()
