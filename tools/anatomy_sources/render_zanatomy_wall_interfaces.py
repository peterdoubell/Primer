#!/usr/bin/env python3
"""Locate every retained wall contact against unmodified native source polygons."""
import argparse
from collections import defaultdict
import gzip
import hashlib
import json
from pathlib import Path


def render(output):
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.collections import PolyCollection
    from tools.anatomy_sources.render_zanatomy_wall_source import decode
    from tools.anatomy_sources.review_zanatomy_wall_source import native_polygons
    summary=json.loads((output/'wall-interface-summary.json').read_text());packed=(output/summary['file']).read_bytes();raw=gzip.decompress(packed)
    if hashlib.sha256(packed).hexdigest()!=summary['compressed_sha256'] or hashlib.sha256(raw).hexdigest()!=summary['uncompressed_sha256']:raise ValueError('Complete contact evidence differs')
    evidence=json.loads(raw);review_raw=(output/'native-wall-review.json').read_bytes();review=json.loads(review_raw)
    if hashlib.sha256(review_raw).hexdigest()!=evidence['source_native_review_sha256']:raise ValueError('Original source review differs')
    meshes={}
    for g in review['geometries']:
        packed=(output/g['file']).read_bytes();payload=gzip.decompress(packed)
        if hashlib.sha256(payload).hexdigest()!=g['uncompressed_sha256']:raise ValueError('Original native arrays differ')
        e=json.loads(payload);local=np.asarray(decode(e['positions'])).reshape(-1,3);polygons=native_polygons(decode(e['polygon_vertex_index']),len(local))
        for part in [i for i in review['instances'] if i['source_geometry_id']==g['geometry_id']]:
            matrix=np.asarray(part['world_transform_columns']).T;world=np.column_stack([local,np.ones(len(local))])@matrix.T
            if hashlib.sha256(world.astype('<f8').tobytes()).hexdigest()!=part['world_positions_float64_cm_sha256']:raise ValueError('Native instance frame differs')
            points=world*10;meshes[str(part['source_model_id'])]=[points[p] for p in polygons]
    groups=[('all retained contacts',evidence['contacts']),
            ('within source instance',[c for c in evidence['contacts'] if c['within_source_instance']]),
            ('between source instances',[c for c in evidence['contacts'] if not c['within_source_instance']])]
    fig,axes=plt.subplots(3,3,figsize=(14,12),layout='constrained');fig.get_layout_engine().set(rect=(0,.05,1,.93));panels=[]
    all_polygons=[p for mesh in meshes.values() for p in mesh]
    for row,(name,contacts) in enumerate(groups):
        points=np.asarray([p for c in contacts for p in c['contact_points_mm']]).reshape(-1,3);affected=defaultdict(set)
        for c in contacts:
            for face in c['original_source_faces']:affected[face['source_part']].add(face['native_face_index'])
        held=[meshes[key][i] for key,ids in affected.items() for i in sorted(ids)]
        for col,(a,b) in enumerate([(0,1),(0,2),(1,2)]):
            ax=axes[row,col];ax.add_collection(PolyCollection([p[:,[a,b]] for p in all_polygons],facecolor='#b7aa83',edgecolor='none',alpha=.018))
            if held:ax.add_collection(PolyCollection([p[:,[a,b]] for p in held],facecolor='#bc467c',edgecolor='none',alpha=.15))
            if len(points):ax.scatter(points[:,a],points[:,b],s=.6,color='#14648f',zorder=4)
            ax.autoscale_view();ax.set_aspect('equal');ax.tick_params(labelsize=8)
            ax.set_xlabel('Source '+['X','Y','Z'][a]+' mm');ax.set_ylabel('Source '+['X','Y','Z'][b]+' mm');ax.set_title(name+' | '+str(len(contacts))+' pairs',fontsize=10)
        panels.append({'category':name,'contact_pairs':len(contacts),'contact_points_displayed':len(points),
            'contacts_involving_native_nontriangles':sum(c['includes_nontriangle_native_polygon'] for c in contacts),
            'all_original_context_faces':len(all_polygons),'affected_native_faces':[{'source_model_id':key,'face_indices':sorted(ids)} for key,ids in sorted(affected.items())]})
    fig.suptitle('Native wall source-instance contacts | complete numerical evidence, not anatomical approval\nGold: original polygons; magenta: affected native faces; blue: all retained contact points\nFascia contacts depend on explicit analysis tessellation; no pruning, repair, fitting or tissue classification',fontsize=11)
    fig.text(.5,.01,'Z-Anatomy / BodyParts3D DBCLS | CC BY-SA 4.0; original BodyParts3D lineage CC BY-SA 2.1 Japan\nAdaptation: source-coordinate contact projections and review colours',ha='center',fontsize=8)
    target=output/'wall-interface-locations.png';fig.savefig(target,dpi=120);plt.close(fig)
    (output/'wall-interface-location-review.json').write_text(json.dumps({'file':target.name,'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),
        'complete_contact_evidence_sha256':summary['uncompressed_sha256'],'panels':panels,
        'source_geometry_changed':False,'clinical_approval':False,'runtime_promoted':False},indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    render(p.parse_args().output)
