#!/usr/bin/env python3
"""Render unchanged source facets and native CT planes without repairing or fitting anatomy."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile
from tools.anatomy_sources.review_aaa_kinematic_source import ROOT,OUTPUT,ARCHIVE_SHA,stl,ras_to_ijk
from tools.anatomy_sources.review_spl_wall_source import nrrd


def plane_segments(triangles,z):
    """Intersect actual triangle edges with a native axial plane; coplanar facets remain explicit."""
    import numpy as np
    d=triangles[:,:,2]-z;coplanar=np.all(d==0,axis=1)
    crossing=(d.min(1)<=0)&(d.max(1)>=0)&~coplanar;segments=[]
    for tri,dist in zip(triangles[crossing],d[crossing]):
        points=[]
        for a,b in ((0,1),(1,2),(2,0)):
            if dist[a]==0:points.append(tri[a,:2])
            elif dist[a]*dist[b]<0:
                t=-dist[a]/(dist[b]-dist[a]);points.append(tri[a,:2]+t*(tri[b,:2]-tri[a,:2]))
        unique=[]
        for p in points:
            if not any(np.array_equal(p,q) for q in unique):unique.append(p)
        if len(unique)==2:segments.append(unique)
    return np.asarray(segments,dtype='float64').reshape(-1,2,2),int(coplanar.sum())


def render(root):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.collections import LineCollection
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    import numpy as np
    archive=root/'4DCTA_AAA_Dataset.zip'
    if hashlib.sha256(archive.read_bytes()).hexdigest()!=ARCHIVE_SHA:raise ValueError('Original archive differs')
    proof_raw=(OUTPUT/'native-source-review.json').read_bytes();proof=json.loads(proof_raw);render_rows=[]
    with zipfile.ZipFile(archive) as z:
        for record in proof['records']:
            phase=record['review_phase_percent'];frame=next(f for f in record['frames'] if f['cardiac_phase_percent']==phase)
            raw=z.read(frame['member']);fields,ct=nrrd(raw)
            surface_raw=z.read(record['surface_member']);facets=stl(surface_raw)['vertices'].astype('float64')
            if hashlib.sha256(raw).hexdigest()!=frame['nrrd_sha256'] or hashlib.sha256(surface_raw).hexdigest()!=record['surface_sha256']:raise ValueError('Source binding differs')
            ijk=ras_to_ijk(facets.reshape(-1,3),fields).reshape(-1,3,3)
            fig=plt.figure(figsize=(14,5.2));slice_rows=[]
            for column,fraction in enumerate((.25,.5,.75),start=1):
                index=round((ct.shape[0]-1)*fraction);ax=fig.add_subplot(1,4,column)
                ax.imshow(ct[index],cmap='gray',vmin=-200,vmax=600,origin='lower',interpolation='nearest')
                segments,coplanar=plane_segments(ijk,index);ax.add_collection(LineCollection(segments,colors='#ffaf35',linewidths=.65))
                ax.set_xlim(-.5,ct.shape[2]-.5);ax.set_ylim(-.5,ct.shape[1]-.5)
                ax.set_title(f'Original axial voxel plane k={index}\n{len(segments)} source-facet intersections',fontsize=9)
                ax.set_xlabel('Native i (RAS +R)',fontsize=8);ax.set_ylabel('Native j (RAS +A)',fontsize=8)
                slice_rows.append({'voxel_k':index,'source_facet_intersections':len(segments),'coplanar_facets_omitted_from_line_overlay':coplanar})
            ax=fig.add_subplot(1,4,4,projection='3d');lo=facets.min((0,1));hi=facets.max((0,1))
            ax.add_collection3d(Poly3DCollection(facets,facecolors='#b5c6cc',edgecolors='none',linewidths=0,alpha=1))
            ax.set_xlim(lo[0],hi[0]);ax.set_ylim(lo[1],hi[1]);ax.set_zlim(lo[2],hi[2]);ax.set_box_aspect(hi-lo)
            ax.set_xlabel('R');ax.set_ylabel('A');ax.set_zlabel('S');ax.view_init(elev=15,azim=-65)
            ax.set_title('Unchanged external surface\nOpen ends retained; no caps/fitting',fontsize=9)
            fig.suptitle(f"{record['patient_source_id']} · source CT {phase}% cardiac frame and original external-wall STL",fontsize=12)
            fig.text(.02,.035,'Amber lines: mathematical facet/plane intersections, not independent wall labels. Stored-value display window −200..600; HU/physical units unverified.',fontsize=8)
            fig.text(.02,.005,'Automated source segmentation was cropped/smoothed/remeshed; branches removed. No lumen/thrombus/inner-wall map, clinical approval or rupture prediction.',fontsize=8)
            fig.tight_layout(rect=(0,.15,1,.91));name=record['patient_source_id']+'-native-ct-surface-context.png';fig.savefig(OUTPUT/name,dpi=180);plt.close(fig)
            render_rows.append({'patient_source_id':record['patient_source_id'],'ct_member':frame['member'],'ct_sha256':frame['nrrd_sha256'],
                'surface_sha256':record['surface_sha256'],'image_file':name,'image_sha256':hashlib.sha256((OUTPUT/name).read_bytes()).hexdigest(),
                'native_slice_contexts':slice_rows,'display_window_stored_values':[-200,600],
                'ct_spatial_interpolation_applied':False,'source_geometry_changed':False,'source_alignment_fitted':False,
                'overlay_is_independent_anatomical_boundary_validation':False})
    (OUTPUT/'render-review.json').write_text(json.dumps({'native_source_proof_sha256':hashlib.sha256(proof_raw).hexdigest(),
        'records':render_rows,'camera_and_surface_colour_are_review_choices':True,'clinical_approval':False,'runtime_promoted':False},indent=2)+'\n')
    print('Rendered ten unchanged external surfaces with thirty native CT slice contexts.')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True)
    render(p.parse_args().source_root)
