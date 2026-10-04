#!/usr/bin/env python3
"""Map every numerical contact without assigning biological junction or invasion meaning."""
import argparse
from collections import defaultdict
import gzip
import hashlib
import json
from pathlib import Path


def render(root,output):
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.collections import PolyCollection
    from matplotlib.ticker import MaxNLocator
    from tools.anatomy_sources.review_bodyparts_pancreatic_geometry import read_obj
    inventory=json.loads((output/'original-obj-geometry-review.json').read_text());meshes={}
    for r in inventory['records']:
        raw=(root/'objects'/(r['id']+'.obj')).read_bytes()
        if hashlib.sha256(raw).hexdigest()!=r['source_sha256']:raise ValueError('Source OBJ changed')
        v,n,f,nf=read_obj(raw.decode());meshes[r['id']]=v[f]
    summary=json.loads((output/'complete-contact-summary.json').read_text());figures=[]
    for record in summary['records']:
        payload=gzip.decompress((output/record['file']).read_bytes())
        if hashlib.sha256(payload).hexdigest()!=record['uncompressed_sha256']:raise ValueError('Original contact evidence changed')
        audit=json.loads(payload);parent=record['parenchymal_context'];contacts=audit['triangle_contact_audit']['unexpected_contacts']
        selected=[c for c in contacts if {r['source_part'] for r in c['original_source_faces']}=={parent,'FJ1896'}]
        fig,axes=plt.subplots(2,3,figsize=(14,9),layout='constrained');panels=[]
        fig.get_layout_engine().set(rect=(0,.045,1,.955))
        for row,subset in enumerate([contacts,selected]):
            points=np.asarray([p for c in subset for p in c['contact_points_mm']]);affected=defaultdict(set)
            for c in subset:
                for r in c['original_source_faces']:affected[r['source_part']].add(r['source_face_index'])
            included=audit['included_source_element_ids'] if row==0 else [parent,'FJ1896']
            all_tri=np.concatenate([meshes[i] for i in included]);held=np.concatenate([meshes[i][sorted(indices)] for i,indices in affected.items()])
            lo=held.reshape(-1,3).min(0);hi=held.reshape(-1,3).max(0);pad=np.maximum((hi-lo)*.1,.1)
            for col,(a,b) in enumerate([(0,1),(0,2),(1,2)]):
                ax=axes[row,col]
                ax.add_collection(PolyCollection(all_tri[:,:,[a,b]],facecolor='#b4a780',edgecolor='none',alpha=.025))
                ax.add_collection(PolyCollection(held[:,:,[a,b]],facecolor='#bd467e',edgecolor='none',alpha=.35))
                ax.scatter(points[:,a],points[:,b],s=2,color='#176c97',zorder=4)
                if row:ax.set_xlim(lo[a]-pad[a],hi[a]+pad[a]);ax.set_ylim(lo[b]-pad[b],hi[b]+pad[b])
                else:ax.autoscale_view()
                ax.xaxis.set_major_locator(MaxNLocator(nbins=2,prune='both'));ax.tick_params(labelsize=8)
                ax.set_aspect('equal');ax.set_xlabel('Source '+['X','Y','Z'][a]+' mm');ax.set_ylabel('Source '+['X','Y','Z'][b]+' mm')
                ax.set_title(('All context contacts' if row==0 else 'Duct/parenchyma surface contacts')+' | '+str(len(subset))+' pairs',fontsize=10)
            panels.append({'group':'all_context_contacts' if row==0 else 'duct_parenchyma_contacts','contact_pairs':len(subset),
                           'original_affected_faces':[{'element_id':i,'face_indices':sorted(indices)} for i,indices in sorted(affected.items())],
                           'source_context_element_ids':included,'source_positions_or_faces_changed':False})
        fig.suptitle('Original upstream pancreatic geometry | separate '+parent+' context\nGold: original context; magenta: affected original triangles; blue: numerical contact points\nNo repair, fitting, biological junction classification or clinical approval',fontsize=11)
        fig.text(.5,.006,'BodyParts3D © 2008 DBCLS | CC BY-SA 2.1 Japan | adaptation: source contact projections and review colours',ha='center',fontsize=8)
        path=output/(parent+'-source-contact-locations.png');fig.savefig(path,dpi=120);plt.close(fig)
        figures.append({'parenchymal_context':parent,'file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                        'contact_evidence_sha256':record['uncompressed_sha256'],'panels':panels,'source_coordinate_units':'millimetres'})
        print(parent,'mapped all',len(contacts),'contacts and',len(selected),'duct/parenchyma contacts',flush=True)
    (output/'contact-location-review.json').write_text(json.dumps({'figures':figures,'source_geometry_changed':False,'clinical_approval':False,'runtime_promoted':False,
        'derived_figure_license':'CC BY-SA 2.1 Japan','limits':['Model coordinate projections may overlap visually; every numerical contact and original face identity remain in the complete 3D evidence.',
        'Duct/parenchyma surface crossings do not identify invasion, native duct containment or an approved biological interface.']},indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();render(a.source_root,a.output)
