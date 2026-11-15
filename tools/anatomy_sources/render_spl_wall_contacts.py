#!/usr/bin/env python3
"""Locate all independent wall contacts in unchanged original RAS strip geometry."""
import argparse
from collections import defaultdict
import gzip
import hashlib
import json
from pathlib import Path
import zipfile


def render(archive,output):
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.collections import PolyCollection
    from tools.anatomy_sources.review_spl_wall_source import vtk
    summary=json.loads((output/'independent-wall-contact-summary.json').read_text());packed=(output/summary['file']).read_bytes();raw=gzip.decompress(packed)
    if hashlib.sha256(packed).hexdigest()!=summary['compressed_sha256'] or hashlib.sha256(raw).hexdigest()!=summary['uncompressed_sha256']:raise ValueError('Complete contact evidence differs')
    e=json.loads(raw);source_raw=(output/'independent-wall-source-review.json').read_bytes();source=json.loads(source_raw)
    if hashlib.sha256(source_raw).hexdigest()!=e['source_review_sha256']:raise ValueError('Original source review differs')
    meshes={}
    with zipfile.ZipFile(archive) as z:
        for model in source['records']:
            raw=z.read(model['source_member'])
            if hashlib.sha256(raw).hexdigest()!=model['source_vtk_sha256']:raise ValueError('Native strip model differs')
            v,n,f,*_=vtk(raw);meshes[str(model['label_value'])]=v[f]
    all_tri=np.concatenate(list(meshes.values()));groups=[('all retained contacts',e['contacts']),
        ('within original model',[c for c in e['contacts'] if c['within_original_model']]),
        ('between original models',[c for c in e['contacts'] if not c['within_original_model']])]
    fig,axes=plt.subplots(3,3,figsize=(14,12),layout='constrained');fig.get_layout_engine().set(rect=(0,.05,1,.93));panels=[]
    for row,(name,contacts) in enumerate(groups):
        points=np.asarray([p for c in contacts for p in c['contact_points_ras_mm']]).reshape(-1,3);affected=defaultdict(set)
        for c in contacts:
            for f in c['original_source_faces']:affected[f['source_part']].add(f['source_face_index'])
        held=np.concatenate([meshes[key][sorted(ids)] for key,ids in affected.items()]) if affected else np.empty((0,3,3))
        for col,(a,b) in enumerate([(0,1),(0,2),(1,2)]):
            ax=axes[row,col];ax.add_collection(PolyCollection(all_tri[:,:,[a,b]],facecolor='#b7aa85',edgecolor='none',alpha=.025))
            ax.add_collection(PolyCollection(held[:,:,[a,b]],facecolor='#bc467b',edgecolor='none',alpha=.2))
            if len(points):ax.scatter(points[:,a],points[:,b],s=1,color='#146b99',zorder=4)
            ax.autoscale_view();ax.set_aspect('equal');ax.tick_params(labelsize=8)
            ax.set_xlabel('Source RAS '+['X','Y','Z'][a]);ax.set_ylabel('Source RAS '+['X','Y','Z'][b]);ax.set_title(name+' | '+str(len(contacts))+' pairs',fontsize=10)
        panels.append({'category':name,'contact_pairs':len(contacts),'all_contact_points_displayed':len(points),'all_original_context_triangles':len(all_tri),
            'affected_source_faces':[{'label_value':key,'expanded_strip_triangle_indices':sorted(ids)} for key,ids in sorted(affected.items())]})
    fig.suptitle('Independent SPL wall source contacts | full numerical evidence, not clinical approval\nGold: every original strip triangle; magenta: affected source faces; blue: all retained contact points\nNo pruning, fitting, smoothing, repair, tissue-interface or pathology classification',fontsize=11)
    fig.text(.5,.01,'SPL / Brigham and Women’s Hospital | 3D Slicer License Part B\nAdaptation: original source-coordinate projections, review colours and numerical contact markers',ha='center',fontsize=8)
    target=output/'independent-wall-contact-locations.png';fig.savefig(target,dpi=120);plt.close(fig)
    (output/'independent-wall-contact-location-review.json').write_text(json.dumps({'file':target.name,'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),
        'complete_contact_evidence_sha256':summary['uncompressed_sha256'],'panels':panels,
        'source_geometry_changed':False,'clinical_approval':False,'runtime_promoted':False},indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--archive',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();render(a.archive,a.output)
