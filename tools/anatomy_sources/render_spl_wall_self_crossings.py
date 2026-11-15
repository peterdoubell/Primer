#!/usr/bin/env python3
"""Show all independent original crossing regions with unchanged native CT/label context."""
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
    from matplotlib.collections import PolyCollection,LineCollection
    from matplotlib.ticker import MaxNLocator
    from tools.anatomy_sources.review_spl_wall_source import vtk,nrrd
    raw=(output/'original-self-crossing-review.json').read_bytes();review=json.loads(raw)
    source_raw=(output/'independent-wall-source-review.json').read_bytes();source=json.loads(source_raw)
    if hashlib.sha256(source_raw).hexdigest()!=review['source_review_sha256']:raise ValueError('Source review differs')
    meshes={};figures=[]
    with zipfile.ZipFile(archive) as z:
        _,ct=nrrd(z.read('abdomen-2016-09/Data/I.nrrd'));_,labels=nrrd(z.read('abdomen-2016-09/Data/seg.nrrd'))
        for r in source['records']:
            data=z.read(r['source_member'])
            if hashlib.sha256(data).hexdigest()!=r['source_vtk_sha256']:raise ValueError('Original strip model differs')
            v,n,f,*_=vtk(data);meshes[r['label_value']]=v[f]
        for index,region in enumerate(review['regions']):
            records=[review['records'][i] for i in region['contact_record_indices']];triangles=meshes[region['label_value']]
            held=triangles[region['original_triangle_indices']];segments=np.asarray([r['contact_points_ras'] for r in records]);points=segments.reshape(-1,3)
            lo=held.reshape(-1,3).min(0);hi=held.reshape(-1,3).max(0);pad=np.maximum((hi-lo)*.18,max(float((hi-lo).max())*.1,.01))
            witness=max(records,key=lambda r:r['contact_segment_length_mm']);i,j,k=witness['nearest_native_voxel_ijk']
            fig,axes=plt.subplots(2,2,figsize=(12,10),layout='constrained');fig.get_layout_engine().set(rect=(0,.05,1,.94))
            for ax,(a,b) in zip(axes.flat,[(0,1),(0,2),(1,2)]):
                ax.add_collection(PolyCollection(triangles[:,:,[a,b]],facecolor='#b7aa85',edgecolor='none',alpha=.025))
                ax.add_collection(PolyCollection(held[:,:,[a,b]],facecolor='#bc467b',edgecolor='#84355d',linewidth=.3,alpha=.35))
                ax.add_collection(LineCollection(segments[:,:,[a,b]],colors='#146b99',linewidths=2,zorder=4));ax.scatter(points[:,a],points[:,b],s=8,color='#146b99',zorder=5)
                ax.set_xlim(lo[a]-pad[a],hi[a]+pad[a]);ax.set_ylim(lo[b]-pad[b],hi[b]+pad[b]);ax.set_aspect('equal');ax.tick_params(labelsize=8);ax.xaxis.set_major_locator(MaxNLocator(nbins=2));ax.yaxis.set_major_locator(MaxNLocator(nbins=3))
                ax.set_xlabel('Source RAS '+['X','Y','Z'][a]);ax.set_ylabel('Source RAS '+['X','Y','Z'][b]);ax.set_title('Original affected faces | '+str(len(records))+' crossings',fontsize=10)
            ax=axes[1,1];ax.imshow(ct[k],cmap='gray',vmin=900,vmax=1400,interpolation='nearest',origin='upper')
            mask=np.ma.masked_where(labels[k]!=region['label_value'],np.ones_like(labels[k]));ax.imshow(mask,cmap='autumn',alpha=.4,interpolation='nearest',origin='upper');ax.scatter([i],[j],s=30,facecolor='none',edgecolor='#19b8de')
            ax.set_title('Native K='+str(k)+' | nearest voxel of longest segment midpoint\nContext only; labels/source values are not clinical adjudication',fontsize=9);ax.set_xlabel('Native I index');ax.set_ylabel('Native J index')
            fig.suptitle(region['source_name']+' | original strip-triangle interior crossings\nMagenta: unchanged source faces; blue: geometrically validated segments\nNo repair, source fitting, HU/phase claim, tissue/pathology classification or clinical approval',fontsize=11)
            fig.text(.5,.01,'SPL / Brigham and Women’s Hospital | 3D Slicer License Part B\nAdaptation: source-coordinate projections, native stored-value display window [900,1400], label overlay and review markers',ha='center',fontsize=8)
            name='label-'+str(region['label_value'])+'-original-crossing-region-'+str(index)+'.png';target=output/name;fig.savefig(target,dpi=120);plt.close(fig)
            figures.append({'file':name,'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'label_value':region['label_value'],
                'contact_record_indices':region['contact_record_indices'],'all_original_context_triangles':len(triangles),'original_triangle_indices':region['original_triangle_indices'],
                'crossing_segments_displayed':len(records),'native_plane_k':k,'native_witness_voxel_ijk':[i,j,k],
                'original_ct_plane_sha256':hashlib.sha256(ct[k].astype('<i2').tobytes()).hexdigest(),'original_label_plane_sha256':hashlib.sha256(labels[k].astype('<i2').tobytes()).hexdigest(),
                'source_geometry_or_voxels_changed':False})
    (output/'original-self-crossing-location-review.json').write_text(json.dumps({'source_crossing_review_sha256':hashlib.sha256(raw).hexdigest(),'figures':figures,
        'source_geometry_changed':False,'clinical_approval':False,'runtime_promoted':False},indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--archive',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();render(a.archive,a.output)
