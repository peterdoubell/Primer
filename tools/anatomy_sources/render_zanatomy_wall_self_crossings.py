#!/usr/bin/env python3
"""Show every original triangular self-crossing region without editing source geometry."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path


def render(output):
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.collections import PolyCollection, LineCollection
    from matplotlib.ticker import MaxNLocator
    from tools.anatomy_sources.render_zanatomy_wall_source import decode
    from tools.anatomy_sources.review_zanatomy_wall_source import native_polygons
    raw=(output/'native-self-crossing-review.json').read_bytes();review=json.loads(raw)
    native_raw=(output/'native-wall-review.json').read_bytes();native=json.loads(native_raw)
    if hashlib.sha256(native_raw).hexdigest()!=review['native_review_sha256']:raise ValueError('Native source review changed')
    models={str(i['source_model_id']):i for i in native['instances']};meshes={};figures=[]
    for index,region in enumerate(review['regions']):
        model=models[region['source_model_id']];gid=model['source_geometry_id']
        if region['source_model_id'] not in meshes:
            g=next(g for g in native['geometries'] if g['geometry_id']==gid);payload=gzip.decompress((output/g['file']).read_bytes())
            if hashlib.sha256(payload).hexdigest()!=g['uncompressed_sha256']:raise ValueError('Original geometry arrays changed')
            e=json.loads(payload);local=np.asarray(decode(e['positions'])).reshape(-1,3);polygons=native_polygons(decode(e['polygon_vertex_index']),len(local))
            if any(len(p)!=3 for p in polygons):raise ValueError('Nontriangle context requires separate projection policy')
            matrix=np.asarray(model['world_transform_columns']).T;world=np.column_stack([local,np.ones(len(local))])@matrix.T
            if hashlib.sha256(world.astype('<f8').tobytes()).hexdigest()!=model['world_positions_float64_cm_sha256']:raise ValueError('Source instance frame changed')
            meshes[region['source_model_id']]=(world*10)[np.asarray(polygons)]
        triangles=meshes[region['source_model_id']];held=triangles[region['native_source_face_ids']]
        records=[review['records'][i] for i in region['contact_record_indices']]
        segments=np.asarray([r['source_contact_points_mm'] for r in records]);points=segments.reshape(-1,3)
        lo=held.reshape(-1,3).min(0);hi=held.reshape(-1,3).max(0);pad=np.maximum((hi-lo)*.18,.01)
        fig,axes=plt.subplots(2,3,figsize=(14,9),layout='constrained');fig.get_layout_engine().set(rect=(0,.05,1,.95))
        for col,(a,b) in enumerate([(0,1),(0,2),(1,2)]):
            for row in range(2):
                ax=axes[row,col]
                ax.add_collection(PolyCollection(triangles[:,:,[a,b]],facecolor='#b6aa83',edgecolor='none',alpha=.025))
                ax.add_collection(PolyCollection(held[:,:,[a,b]],facecolor='#b9457a',edgecolor='#7e345b',linewidth=.35,alpha=.35))
                ax.add_collection(LineCollection(segments[:,:,[a,b]],colors='#15669a',linewidths=2,zorder=4))
                ax.scatter(points[:,a],points[:,b],s=8,color='#15669a',zorder=5)
                if row:ax.set_xlim(lo[a]-pad[a],hi[a]+pad[a]);ax.set_ylim(lo[b]-pad[b],hi[b]+pad[b])
                else:ax.autoscale_view()
                ax.set_aspect('equal');ax.tick_params(labelsize=8);ax.xaxis.set_major_locator(MaxNLocator(nbins=2));ax.yaxis.set_major_locator(MaxNLocator(nbins=3))
                ax.set_xlabel('Source '+['X','Y','Z'][a]+' mm');ax.set_ylabel('Source '+['X','Y','Z'][b]+' mm')
                ax.set_title(('All original source context' if row==0 else 'Original face region enlarged')+' | '+str(len(records))+' pairs',fontsize=10)
        fig.suptitle(model['name']+' | original native triangular self-crossing region\nGold: unchanged source; magenta: original faces; blue: geometrically validated contact segments\nGeometry finding only; no tissue/pathology inference, repair or clinical approval',fontsize=11)
        fig.text(.5,.01,'Z-Anatomy / BodyParts3D DBCLS | CC BY-SA 4.0; original BodyParts3D lineage CC BY-SA 2.1 Japan\nAdaptation: source-coordinate projections, review colours and contact markers',ha='center',fontsize=8)
        name=region['source_model_id']+'-self-crossing-region-'+str(index)+'.png';target=output/name;fig.savefig(target,dpi=120);plt.close(fig)
        figures.append({'file':name,'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'source_model_id':region['source_model_id'],
            'source_geometry_id':gid,'contact_record_indices':region['contact_record_indices'],'native_source_face_ids':region['native_source_face_ids'],
            'all_original_context_triangles':len(triangles),'contact_segments_displayed':len(records),'source_geometry_changed':False})
    (output/'native-self-crossing-location-review.json').write_text(json.dumps({'source_crossing_review_sha256':hashlib.sha256(raw).hexdigest(),
        'figures':figures,'source_geometry_changed':False,'clinical_approval':False,'runtime_promoted':False},indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    render(p.parse_args().output)
