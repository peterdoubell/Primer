#!/usr/bin/env python3
"""Project unchanged independent SPL wall strips beside original native CT/label planes."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile


def render(archive,output):
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    from tools.anatomy_sources.review_spl_wall_source import vtk,nrrd
    review_raw=(output/'independent-wall-source-review.json').read_bytes();review=json.loads(review_raw);figures=[]
    with zipfile.ZipFile(archive) as z:
        _,ct=nrrd(z.read('abdomen-2016-09/Data/I.nrrd'));_,labels=nrrd(z.read('abdomen-2016-09/Data/seg.nrrd'))
        for r in review['records']:
            raw=z.read(r['source_member'])
            if hashlib.sha256(raw).hexdigest()!=r['source_vtk_sha256']:raise ValueError('Native source mesh changed')
            v,n,f,strips,*_=vtk(raw);tri=v[f];lo=v.min(0);hi=v.max(0);span=np.maximum(hi-lo,.1)
            plane=int(np.argmax((labels==r['label_value']).sum(axis=(1,2))))
            fig=plt.figure(figsize=(14,7));panels=[]
            for i,azimuth in enumerate([35,215]):
                ax=fig.add_subplot(1,3,i+1,projection='3d');ax.add_collection3d(Poly3DCollection(tri,facecolor='#768cac',edgecolor='none',linewidths=0))
                ax.set_xlim(lo[0]-.05*span[0],hi[0]+.05*span[0]);ax.set_ylim(lo[1]-.05*span[1],hi[1]+.05*span[1]);ax.set_zlim(lo[2]-.05*span[2],hi[2]+.05*span[2]);ax.set_box_aspect(span)
                ax.view_init(elev=20,azim=azimuth);ax.locator_params(nbins=3);ax.tick_params(labelsize=7)
                ax.set_xlabel('Source RAS X');ax.set_ylabel('Source RAS Y');ax.set_zlabel('Source RAS Z');ax.set_title('Every original strip triangle\nAzimuth '+str(azimuth),fontsize=10)
                panels.append({'azimuth':azimuth,'all_original_strip_triangles':len(f),'source_geometry_changed':False})
            ax=fig.add_subplot(1,3,3);ax.imshow(ct[plane],cmap='gray',vmin=900,vmax=1400,interpolation='nearest',origin='upper')
            mask=np.ma.masked_where(labels[plane]!=r['label_value'],np.ones_like(labels[plane]));ax.imshow(mask,cmap='autumn',alpha=.4,interpolation='nearest',origin='upper')
            ax.set_title('Original CT + authoritative label '+str(r['label_value'])+'\nNative K='+str(plane)+'; delivered stored values',fontsize=10);ax.set_xlabel('Native I index');ax.set_ylabel('Native J index')
            fig.suptitle(r['source_name']+' | independent SPL CT-derived source\nDerived mesh is non-authoritative; original label map is authoritative source annotation\nNo clinical approval, full-wall extent, guessed side split or replacement of missing layers',fontsize=11)
            fig.subplots_adjust(left=.05,right=.96,top=.77,bottom=.22,wspace=.38)
            fig.text(.5,.025,'SPL / Brigham and Women’s Hospital | 3D Slicer License Part B\nReview adaptation: source-coordinate views and native stored-value display window [900,1400] with label overlay\nNo HU calibration, source voxel interpolation, model smoothing, fitting or geometry changes',ha='center',fontsize=8)
            name='source-wall-label-'+str(r['label_value'])+'.png';path=output/name;fig.savefig(path,dpi=120);plt.close(fig)
            figures.append({'file':name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'label_value':r['label_value'],'native_plane_k':plane,
                'ct_plane_original_int16_sha256':hashlib.sha256(ct[plane].astype('<i2').tobytes()).hexdigest(),'label_plane_original_int16_sha256':hashlib.sha256(labels[plane].astype('<i2').tobytes()).hexdigest(),
                'native_plane_label_voxels':int((labels[plane]==r['label_value']).sum()),'panels':panels,'source_voxels_or_geometry_changed':False})
    (output/'source-projection-review.json').write_text(json.dumps({'source_review_sha256':hashlib.sha256(review_raw).hexdigest(),'figures':figures,
        'clinical_approval':False,'runtime_promoted':False},indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--archive',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();render(a.archive,a.output)
