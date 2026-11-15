#!/usr/bin/env python3
"""Locate all original peritoneal source contacts without merging related labels or fragments."""
import argparse,gzip,hashlib,json
from pathlib import Path


def render(root,output):
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.collections import PolyCollection
    from matplotlib.ticker import MaxNLocator
    from tools.anatomy_sources.review_bodyparts_pancreatic_geometry import read_obj
    summary=json.loads((output/'complete-self-contact-summary.json').read_text())
    if summary['all_four_original_objects_complete'] is not True:raise ValueError('Original object checks remain live/incomplete')
    figures=[]
    for r in summary['records']:
        payload=gzip.decompress((output/r['file']).read_bytes())
        if hashlib.sha256(payload).hexdigest()!=r['uncompressed_sha256']:raise ValueError('Complete contact evidence changed')
        audit=json.loads(payload);raw=(root/'objects'/(r['element_id']+'.obj')).read_bytes()
        if hashlib.sha256(raw).hexdigest()!=audit['source_obj_sha256']:raise ValueError('Original source changed')
        v,n,f,nf=read_obj(raw.decode());tri=v[f];contacts=audit['triangle_contact_audit']['unexpected_contacts']
        indices=sorted({face['source_face_index'] for c in contacts for face in c['original_source_faces']})
        affected=tri[indices];points=np.asarray([p for c in contacts for p in c['contact_points_mm']]);lo=affected.reshape(-1,3).min(0);hi=affected.reshape(-1,3).max(0);pad=np.maximum((hi-lo)*.1,.1)
        fig,axes=plt.subplots(2,3,figsize=(14,9),layout='constrained');fig.get_layout_engine().set(rect=(0,.045,1,.955))
        for col,(a,b) in enumerate([(0,1),(0,2),(1,2)]):
            for zoom,ax in enumerate(axes[:,col]):
                ax.add_collection(PolyCollection(tri[:,:,[a,b]],facecolor='#b5a881',edgecolor='none',alpha=.025))
                ax.add_collection(PolyCollection(affected[:,:,[a,b]],facecolor='#bf477f',edgecolor='none',alpha=.35))
                ax.scatter(points[:,a],points[:,b],s=3,color='#176a91',zorder=4)
                if zoom:ax.set_xlim(lo[a]-pad[a],hi[a]+pad[a]);ax.set_ylim(lo[b]-pad[b],hi[b]+pad[b])
                else:ax.autoscale_view()
                ax.set_aspect('equal');ax.xaxis.set_major_locator(MaxNLocator(nbins=3,prune='both'));ax.tick_params(labelsize=8)
                ax.set_xlabel('Source '+['X','Y','Z'][a]+' mm');ax.set_ylabel('Source '+['X','Y','Z'][b]+' mm')
                ax.set_title(('All original source context' if not zoom else 'Every affected source-face region')+f' | {len(contacts)} pairs',fontsize=10)
        fig.suptitle(r['element_id']+' | '+audit['source_label']+' | every numerical source contact\nGold: original context; magenta: affected original faces; blue: contact points\nNo repairs, fusion, biological interface classification or anatomical approval',fontsize=11)
        fig.text(.5,.006,'BodyParts3D © 2008 DBCLS | CC BY-SA 2.1 Japan | adaptation: original source contact projections',ha='center',fontsize=8)
        path=output/(r['element_id']+'-source-contact-locations.png');fig.savefig(path,dpi=120);plt.close(fig)
        figures.append({'element_id':r['element_id'],'file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                        'complete_contact_evidence_uncompressed_sha256':r['uncompressed_sha256'],'contact_pairs_displayed':len(contacts),
                        'affected_original_face_indices':indices,'all_original_context_triangles':len(f),'source_positions_faces_or_normals_changed':False})
        print(r['element_id'],'mapped all',len(contacts),'contacts',flush=True)
    (output/'self-contact-location-review.json').write_text(json.dumps({'figures':figures,'clinical_approval':False,'runtime_promoted':False,
        'source_geometry_changed':False,'derived_figure_license':'CC BY-SA 2.1 Japan',
        'limits':['Orthogonal model projections may overlap; every exact numerical contact and original face identity remains in complete evidence.',
                  'Contacts may reflect intended construction, geometry artifacts or invalid anatomy; no pathological or biological role is assigned automatically.']},indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();render(a.source_root,a.output)
