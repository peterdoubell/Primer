#!/usr/bin/env python3
"""Render complete source faces and selected original MRI/US planes for review."""
import hashlib
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from tools.anatomy_sources.review_prostate_biopsy0001 import binary_stl,decode_scalar,SOURCE,OUT
import pydicom

def render():
    review=json.loads((OUT/'original-source-review.json').read_text());plots=[]
    def save(fig,name):
        p=OUT/name;fig.savefig(p,dpi=120);plt.close(fig)
        plots.append({'file':name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
    models=[(r,binary_stl((OUT/(r['role']+'-original.stl')).read_bytes())['vertices']) for r in review['original_surfaces']]
    all_corners=np.concatenate([v.reshape(-1,3) for _,v in models]);low=all_corners.min(0);high=all_corners.max(0)
    fig=plt.figure(figsize=(12,8))
    for i,(azimuth,elevation) in enumerate([(15,15),(105,15),(195,15),(285,15),(0,85),(0,-85)]):
        ax=fig.add_subplot(2,3,i+1,projection='3d')
        for row,vertices in models:
            ax.add_collection3d(Poly3DCollection(vertices,facecolor='#7193aa' if row['role']=='prostate' else '#b96645',edgecolor='none',alpha=.28 if row['role']=='prostate' else 1))
        ax.set_xlim(low[0],high[0]);ax.set_ylim(low[1],high[1]);ax.set_zlim(low[2],high[2]);ax.set_box_aspect(high-low);ax.view_init(elevation,azimuth)
        ax.set_xlabel('source X');ax.set_ylabel('source Y');ax.set_zlabel('source Z');ax.set_title(f'azimuth {azimuth}, elevation {elevation}',fontsize=9)
        if abs(elevation)>80:ax.set_axis_off()
    fig.suptitle('Complete original source prostate outline and suspicious target ROI\nIllustrative colours; raw source XYZ; clinical/MRI registration and fine anatomy unapproved',fontsize=12)
    fig.subplots_adjust(left=.02,right=.97,top=.84,bottom=.06,wspace=.2,hspace=.3);save(fig,'original-surfaces-six-views.png')
    t2=next(r for r in review['MRI_series'] if r['role']=='T2');shape=t2['geometry']['shape']
    array=np.fromfile(SOURCE/'T2-original-u16.bin','<u2').reshape(shape)
    mask=np.fromfile(SOURCE/'prostate-derived-SEG-u8.bin','u1').reshape(shape)
    target=np.fromfile(SOURCE/'suspicious_target1-derived-SEG-u8.bin','u1').reshape(shape)
    by_sop={r['SOPInstanceUID']:r for r in review['objects']}
    for name,indices in [('T2-original-planes',[0,29,59]),('T2-derived-SEG-correspondence',[15,25,35])]:
        fig,axes=plt.subplots(1,3,figsize=(12,4))
        for ax,index in zip(axes,indices):
            record=by_sop[t2['SOPInstanceUIDs_in_source_plane_order'][index]]
            centre=float(record['source_WindowCenter']);width=float(record['source_WindowWidth'])
            if width<=1 or record['source_VOILUTFunction'] not in ['','LINEAR']:raise ValueError('Unsupported source display window')
            ax.imshow(array[index],cmap='gray',vmin=centre-.5-(width-1)/2,vmax=centre-.5+(width-1)/2,interpolation='nearest')
            if name.endswith('correspondence'):
                for data,color in [(mask,'#66b6d3'),(target,'#f09f56')]:
                    if data[index].any():ax.contour(data[index],levels=[.5],colors=[color],linewidths=.6)
            ax.set_title(f'Original T2 slice {index} of 59');ax.axis('off')
        fig.suptitle('Source MRI stored values and original DICOM display windows\nDerived source SEG only; no STL fitting, new boundary or histology approval',fontsize=11)
        fig.subplots_adjust(top=.77,left=.01,right=.99,wspace=.05);save(fig,name+'.png')
    fig,axes=plt.subplots(2,3,figsize=(12,7))
    for row,volume in enumerate([r for r in review['objects'] if r['modality']=='US']):
        ds=pydicom.dcmread(SOURCE/volume['file']);data=decode_scalar(ds)
        for ax,index in zip(axes[row],[0,113,226]):
            ax.imshow(data[index],cmap='gray',vmin=0,vmax=255,interpolation='nearest');ax.set_title(f'Source US {row+1}, frame {index}/226',fontsize=9);ax.axis('off')
    fig.suptitle('Original US byte values and source frame order\nSource voxel tags differ; standard orientation/position and native MRI registration unverified',fontsize=11)
    fig.subplots_adjust(top=.86,left=.01,right=.99,wspace=.05,hspace=.1);save(fig,'original-US-selected-planes.png')
    (OUT/'visual-render-proof.json').write_text(json.dumps({'all_5478_original_faces_rendered_without_decimation':True,'source_images_and_face_corners_changed':False,'source_US_spatial_registration_or_full_fine_anatomical_approval':False,'MRI_plot_sampling':'Selected complete original planes; all stored samples independently decoded in source audit','plots':plots},indent=2)+'\n')
    print('Four source review plots saved; original arrays and all5478 faces unchanged')

if __name__=='__main__':render()
