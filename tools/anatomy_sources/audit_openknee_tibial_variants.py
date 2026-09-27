#!/usr/bin/env python3
"""Compare tibial-cartilage source variants, without inventing their lineage."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy import ndimage
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt
from matplotlib.collections import LineCollection
from audit_openknee_pair import nifti, mesh
from audit_malaya_knee_images import section, raster_section, slice_plane


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    candidates = args.source / 'tibial-mask-candidates'
    acquisitions = json.loads((candidates / 'acquisition.json').read_text())
    sources = json.loads((candidates / 'comparison-source-acquisition.json').read_text())
    hashes = {r.get('filename', r.get('name')): r['sha256'] for r in acquisitions + sources}
    geometry = json.loads((args.source / 'oks003-native/geometry-audit.json').read_text())
    image = nifti(args.source / 'oks003-cartilage-mri.nii')
    report = {'status': 'Source-variant comparison, no clinical approval or inferred ancestry',
              'no_fitted_transform': True, 'no_geometry_changes': True,
              'image': image['metadata'], 'structures': [],
              'limits': 'Label agreement and volume changes measure representation consistency, not biological accuracy. An unversioned mask is a candidate, not proof of the selected processed mesh revision.'}
    for side, process in [('L', 'LVTTIT'), ('M', 'LVTIT')]:
        key = 'TBC-' + side
        mask_path = candidates / ('oks003_' + key + '_AGS.nii')
        assert sha(mask_path) == hashes[mask_path.name]
        label = nifti(mask_path)
        assert list(np.unique(label['data'])) == [0, 1]
        voxels = np.argwhere(label['data'] != 0)
        points = voxels @ label['directions'].T + label['origin']
        bounds = np.array([points.min(0)-3, points.max(0)+3])
        center = np.median(points, axis=0)
        label_volume = len(voxels) * abs(np.linalg.det(label['directions']))
        current = next(p for p in geometry['parts'] if p['id'] == key)
        paths = [candidates / ('oks003_' + key + '_AGS_RAW.stl'),
                 candidates / ('oks003_' + key + '_AGS_' + process + '.stl'),
                 args.source / 'oks003-native' / current['filename']]
        row = {'id': key, 'candidate_mask': label['metadata'],
               'mask_nonzero_voxels': len(voxels), 'voxel_volume_mm3': float(label_volume),
               'exact_selected_revision_lineage_established': False, 'variants': []}
        fig, axes = plt.subplots(4, 3, figsize=(12, 11))
        for col, (axis,h,v) in enumerate([(0,1,2),(1,0,2),(2,0,1)]):
            plane, world, x, y, actual, _ = slice_plane(image,axis,center[axis],h,v,bounds)
            idx=(world-label['origin'])@np.linalg.inv(label['directions']).T
            selected=ndimage.map_coordinates(label['data'],np.moveaxis(idx,-1,0),order=0,mode='constant',cval=0)!=0
            for plot in axes[:,col]:
                plot.imshow(plane,origin='lower',extent=[x[0],x[-1],y[0],y[-1]],cmap='gray',vmin=0,vmax=max(1,float(np.percentile(plane,99.5))),interpolation='nearest')
                plot.set_xlabel('RAS axis %d (mm)' % h)
            axes[0,col].set_title(['Sagittal MRI','Coronal MRI','Axial MRI'][col])
            for index,path in enumerate(paths):
                expected=current['sha256'] if index==2 else hashes[path.name]
                triangles=mesh(path,expected)
                if col==0:
                    volume=float(abs(np.einsum('ij,ij->i',triangles[:,0],np.cross(triangles[:,1],triangles[:,2])).sum()/6))
                    row['variants'].append({'name':['raw','earlier_processed','selected_02'][index],
                        'filename':path.name,'sha256':expected,'triangles':len(triangles),
                        'enclosed_volume_mm3':volume,'relative_to_mask_volume_percent':100*(volume/label_volume-1),
                        'sections':[]})
                lines=section(triangles,axis,actual,h,v)
                rendered=raster_section(lines,x,y)
                denominator=int(rendered.sum()+selected.sum())
                dice=2*int((rendered&selected).sum())/denominator if denominator else None
                row['variants'][index]['sections'].append({'axis':axis,'world_coordinate_mm':actual,'mask_mesh_dice':dice})
                plot=axes[index+1,col]
                plot.contour(x,y,selected,levels=[.5],colors=['cyan'],linewidths=.8)
                plot.add_collection(LineCollection(lines,colors='#ffc249',linewidths=.8))
                plot.set_title('%s; overlap %.3f' % (row['variants'][index]['name'],dice))
        fig.suptitle('oks003 '+key+' — unchanged source variants on native MRI\nCyan: unversioned candidate mask; gold: surface. No fitted registration or clinical approval.',fontsize=12)
        fig.tight_layout();fig.savefig(args.output/(key.lower()+'-variants.png'),dpi=140);plt.close(fig)
        report['structures'].append(row)
        print(key,[(v['name'],round(v['relative_to_mask_volume_percent'],2)) for v in row['variants']],flush=True)
    (args.output/'variant-audit.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__ == '__main__':
    main()
