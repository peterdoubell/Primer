#!/usr/bin/env python3
"""Locate every held pancreatic contact and invalid source face in native model projections."""
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
    from tools.anatomy_sources.inspect_hra_renal_glb import read_glb,accessor
    summary=json.loads((output/'complete-contact-summary.json').read_text());figures=[]
    for row in summary['records']:
        sex=row['sex'];key='pancreas-'+sex+'-v1.3';packed=(output/row['file']).read_bytes();payload=gzip.decompress(packed)
        if hashlib.sha256(packed).hexdigest()!=row['compressed_sha256'] or hashlib.sha256(payload).hexdigest()!=row['uncompressed_sha256']:
            raise ValueError('Complete contact evidence changed')
        audit=json.loads(payload);raw=(root/key/('3d-vh-'+sex[0]+'-pancreas.glb')).read_bytes()
        if hashlib.sha256(raw).hexdigest()!=audit['source_glb_sha256']:raise ValueError('Original model changed')
        inventory=json.loads((output/(key+'-original-primitives.json')).read_text());doc,binary=read_glb(raw);triangles={}
        for record in inventory['records']:
            node=doc['nodes'][record['node_index']];p=doc['meshes'][node['mesh']]['primitives'][record['primitive_index']]
            v=accessor(doc,binary,p['attributes']['POSITION']);i=accessor(doc,binary,p['indices']).reshape(-1)
            if hashlib.sha256(v.tobytes()).hexdigest()!=record['position_accessor_sha256'] or hashlib.sha256(i.tobytes()).hexdigest()!=record['indices_accessor_sha256']:
                raise ValueError('Original primitive changed')
            triangles[record['node_name']]=v.astype(float)[i.reshape(-1,3)]*1000
        affected=defaultdict(set);points=[]
        for contact in audit['triangle_contact_audit']['unexpected_contacts']:
            for face in contact['original_source_faces']:affected[face['source_part']].add(face['source_face_index'])
            points.extend(contact['contact_points_mm'])
        invalid=audit['preparation']['invalid_source_triangles']
        invalid_tri=np.asarray([triangles[r['source_part']][r['source_face_index']] for r in invalid]).reshape(-1,3,3)
        held_tri=np.concatenate([triangles[name][sorted(ids)] for name,ids in affected.items()])
        selected=np.concatenate([held_tri.reshape(-1,3),invalid_tri.reshape(-1,3)])
        lo=selected.min(0);hi=selected.max(0);pad=np.maximum((hi-lo)*.1,.25)
        all_tri=np.concatenate(list(triangles.values()));points=np.asarray(points)
        fig,axes=plt.subplots(2,3,figsize=(14,9),layout='constrained')
        for col,(a,b) in enumerate([(0,1),(0,2),(1,2)]):
            for zoom,ax in enumerate(axes[:,col]):
                ax.add_collection(PolyCollection(all_tri[:,:,[a,b]],facecolor='#b99d68',edgecolor='none',alpha=.025))
                ax.add_collection(PolyCollection(held_tri[:,:,[a,b]],facecolor='#bb3075',edgecolor='#bb3075',linewidth=.4,alpha=.5))
                for triangle in invalid_tri:
                    loop=np.vstack([triangle,triangle[0]]);ax.plot(loop[:,a],loop[:,b],color='black',lw=1)
                ax.scatter(points[:,a],points[:,b],s=4,color='#176a9a',zorder=4)
                if zoom:ax.set_xlim(lo[a]-pad[a],hi[a]+pad[a]);ax.set_ylim(lo[b]-pad[b],hi[b]+pad[b])
                else:ax.autoscale_view()
                ax.set_aspect('equal');ax.set_xlabel('Source glTF '+['X','Y','Z'][a]+' mm');ax.set_ylabel('Source glTF '+['X','Y','Z'][b]+' mm')
                ax.set_title(('Held-face region detail' if zoom else 'All five source regions')+' | '+['X–Y','X–Z','Y–Z'][col],fontsize=10)
        fig.suptitle('HRA '+sex+' pancreas v1.3 | every held triangle contact and invalid face\n'
                     'Gold: original context; magenta: affected original faces; blue: contact points; black: invalid source triangles\n'
                     'Native model projections in mm; no fitting, repairs, clinical orientation or anatomical approval',fontsize=11)
        path=output/(key+'-held-contact-locations.png');fig.savefig(path,dpi=120);plt.close(fig)
        figures.append({'sex':sex,'file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                        'contact_evidence_sha256':row['uncompressed_sha256'],'contact_pairs_displayed':len(audit['triangle_contact_audit']['unexpected_contacts']),
                        'affected_original_faces':[{'source_part':name,'source_face_indices':sorted(ids)} for name,ids in sorted(affected.items())],
                        'invalid_original_faces_displayed':len(invalid),'all_source_context_triangles':len(all_tri),
                        'source_coordinate_transform':'Declared metres to millimetres only; native glTF axes preserved.',
                        'source_positions_or_faces_edited':False})
        print(sex,'mapped all contacts',row['contact_count'],'and invalid faces',len(invalid),flush=True)
    (output/'held-contact-location-review.json').write_text(json.dumps({'figures':figures,'clinical_approval':False,'runtime_promoted':False,
            'limits':['Orthogonal model projections can overlap visually; every highlighted source identity and numerical 3D contact remains in the complete evidence.',
                      'Context opacity and held-face highlighting are display only, not source repairs, anatomical classifications or pathological findings.']},indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();render(a.source_root,a.output)
