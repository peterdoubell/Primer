"""Inspect native atlas disc/nucleus geometry without inventing missing tissues."""
from pathlib import Path
import hashlib,json,sys
from collections import Counter,defaultdict
import numpy as np
ROOT=Path(__file__).resolve().parents[2];SOURCE=Path('/tmp/primer-msk-sources/z-anatomy-Joints100.fbx');OUT=ROOT/'docs/msk-disc-component-source-review'
sys.path.insert(0,str(ROOT))
from tools.anatomy_sources.inspect_fbx import load_fbx,child


def polygon_topology(geometry):
    flat=child(geometry,'PolygonVertexIndex')['properties'][0];polygons=[];current=[]
    for value in flat:
        current.append(int(value) if value>=0 else -int(value)-1)
        if value<0:polygons.append(current);current=[]
    assert not current
    edges=Counter();used=set();neighbors=defaultdict(set)
    for polygon in polygons:
        used.update(polygon)
        for a,b in zip(polygon,polygon[1:]+polygon[:1]):edges[tuple(sorted((a,b)))]+=1;neighbors[a].add(b);neighbors[b].add(a)
    remaining=set(used);components=[]
    while remaining:
        stack=[remaining.pop()];count=0
        while stack:
            vertex=stack.pop();count+=1
            for neighbor in neighbors[vertex]:
                if neighbor in remaining:remaining.remove(neighbor);stack.append(neighbor)
        components.append(count)
    return {'referenced_vertices':len(used),'native_polygons':len(polygons),'native_edges':len(edges),'euler_characteristic':len(used)-len(edges)+len(polygons),'boundary_edges':sum(n==1 for n in edges.values()),'nonmanifold_edges':sum(n>2 for n in edges.values()),'vertex_connected_components':sorted(components,reverse=True),'polygon_sizes':dict(Counter(map(len,polygons)))},flat


def main():
    digest=hashlib.sha256(SOURCE.read_bytes()).hexdigest();assert digest=='f4ba7a910cdaef99e31530f368628780d9f06b5d77853f8b721f47f67137e823'
    version,nodes=load_fbx(SOURCE);objects=next(n for n in nodes if n['name']=='Objects')['children'];selected=[];reference=None;reference_indices=None
    for g in objects:
        if g['name']!='Geometry' or not child(g,'Vertices'):continue
        name=g['properties'][1].split('\0')[0]
        if not name.startswith(('Intervertebral disc ','Nucleus pulposus ')):continue
        v=np.asarray(child(g,'Vertices')['properties'][0]).reshape(-1,3);check,indices=polygon_topology(g);row={'name':name,'geometry_id':g['properties'][0],'vertices':len(v),'bounds_local':[v.min(0).tolist(),v.max(0).tolist()],'topology':check}
        if name.startswith('Nucleus pulposus '):
            if reference is None:reference=v.copy();reference_indices=list(indices)
            assert v.shape==reference.shape
            design=np.column_stack([reference,np.ones(len(reference))]);fit,_,_,_=np.linalg.lstsq(design,v,rcond=None);residual=np.linalg.norm(design@fit-v,axis=1);diagonal=np.linalg.norm(v.max(0)-v.min(0));row['comparison_to_first_nucleus']={'same_polygon_indices':list(indices)==reference_indices,'affine_fit_maximum_relative_residual':float(residual.max()/diagonal),'affine_fit_rms_relative_residual':float(np.sqrt(np.mean(residual**2))/diagonal)}
        selected.append(row)
    assert sum(r['name'].startswith('Nucleus pulposus ') for r in selected)==23 and sum(r['name'].startswith('Intervertebral disc ') for r in selected)==23
    material_names=[g['properties'][1].split('\0')[0] for g in objects if g['name']=='Material' and any(k in str(g['properties'][1]).lower() for k in ['annul','nucle'])]
    report={'source_file':str(SOURCE),'source_sha256':digest,'fbx_version':version,'parts':selected,'separately_named_annulus_geometry':[g['properties'][1].split('\0')[0] for g in objects if g['name']=='Geometry' and 'annulus fibrosus' in str(g['properties'][1]).lower()],'matching_material_names':material_names,'limits':['Names and polygon counts do not establish biological accuracy.','Affine-fit similarity assesses corresponding native vertices; it is not proof of source acquisition method.','Native polygon incidence does not rule out self-intersection or prove valid tissue volume.','No internal annulus boundary, endplate interface or MRI correspondence is inferred.'],'runtime_promoted':False,'clinical_approval':False};OUT.mkdir(parents=True,exist_ok=True);(OUT/'native-atlas-disc-audit.json').write_text(json.dumps(report,indent=2)+'\n')
    nuclei=[r for r in selected if r['name'].startswith('Nucleus pulposus ')];print('Native disc/nucleus geometries:',len(selected));print('Nucleus affine-fit max relative residual:',max(r['comparison_to_first_nucleus']['affine_fit_maximum_relative_residual'] for r in nuclei));print('Same connectivity:',sum(r['comparison_to_first_nucleus']['same_polygon_indices'] for r in nuclei));print('Disc Euler counts:',dict(Counter(r['topology']['euler_characteristic'] for r in selected if r['name'].startswith('Intervertebral disc '))));print('Separate annulus:',report['separately_named_annulus_geometry'],'material names:',material_names)


if __name__=='__main__':main()
