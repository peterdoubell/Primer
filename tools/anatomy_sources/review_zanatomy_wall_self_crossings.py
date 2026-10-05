#!/usr/bin/env python3
"""Classify original triangular wall self-crossings without biological inference or repair."""
import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path


def sha(raw):return hashlib.sha256(raw).hexdigest()


def barycentric(triangle,point):
    import numpy as np
    uv=np.linalg.lstsq((triangle[1:]-triangle[0]).T,point-triangle[0],rcond=None)[0]
    weights=np.asarray([1-uv.sum(),*uv])
    return weights,float(np.linalg.norm(weights@triangle-point))


def review(output):
    import numpy as np
    from tools.anatomy_sources.render_zanatomy_wall_source import decode
    from tools.anatomy_sources.review_zanatomy_wall_source import native_polygons
    summary=json.loads((output/'wall-interface-summary.json').read_text());packed=(output/summary['file']).read_bytes();raw=gzip.decompress(packed)
    if sha(packed)!=summary['compressed_sha256'] or sha(raw)!=summary['uncompressed_sha256']:raise ValueError('Complete contact evidence differs')
    contacts=json.loads(raw);native_raw=(output/'native-wall-review.json').read_bytes();native=json.loads(native_raw)
    if sha(native_raw)!=contacts['source_native_review_sha256']:raise ValueError('Native source review differs')
    models={str(i['source_model_id']):i for i in native['instances']};geometries={g['geometry_id']:g for g in native['geometries']};cache={};records=[]
    for c in contacts['contacts']:
        if not c['within_source_instance']:continue
        identities=c['original_source_faces'];model=models[identities[0]['source_part']];gid=model['source_geometry_id']
        if gid not in cache:
            g=geometries[gid];payload=gzip.decompress((output/g['file']).read_bytes())
            if sha(payload)!=g['uncompressed_sha256']:raise ValueError('Original native arrays differ')
            e=json.loads(payload);local=np.asarray(decode(e['positions'])).reshape(-1,3)
            polygons=native_polygons(decode(e['polygon_vertex_index']),len(local))
            materials=list(decode(e['original_layers']['LayerElementMaterial']['Materials']))
            if e['original_layers']['LayerElementMaterial']['MappingInformationType']==['AllSame']:materials*=len(polygons)
            cache[gid]=(local,polygons,materials)
        local,polygons,materials=cache[gid];ids=[f['native_face_index'] for f in identities];vertices=[polygons[i] for i in ids]
        if any(len(p)!=3 for p in vertices):raise ValueError('Native nontriangle requires separate surface-choice review')
        matrix=np.asarray(model['world_transform_columns']).T;world=np.column_stack([local,np.ones(len(local))])@matrix.T
        if sha(world.astype('<f8').tobytes())!=model['world_positions_float64_cm_sha256']:raise ValueError('Original source instance transform differs')
        triangles=world[np.asarray(vertices)]*10;points=np.asarray(c['contact_points_mm'])
        if points.shape!=(2,3):raise ValueError('Nonsegment source contact requires separate review')
        normals=np.cross(triangles[:,1]-triangles[:,0],triangles[:,2]-triangles[:,0]);normals/=np.linalg.norm(normals,axis=1)[:,None]
        midpoint=points.mean(0);weights=[];residuals=[];endpoints=[]
        for triangle in triangles:
            w,error=barycentric(triangle,midpoint);weights.append(w.tolist());residuals.append(error)
            endpoints.append([{'weights':barycentric(triangle,p)[0].tolist(),'plane_reconstruction_error_mm':barycentric(triangle,p)[1]} for p in points])
        interior=all(min(w)>1e-9 for w in weights) and max(residuals)<1e-9
        cross=float(np.linalg.norm(np.cross(normals[0],normals[1])));length=float(np.linalg.norm(points[1]-points[0]))
        records.append({'source_model_id':identities[0]['source_part'],'source_model_name':model['name'],'source_geometry_id':gid,
            'native_source_face_ids':ids,'native_source_vertex_ids':vertices,'native_source_triangles_world_mm':triangles.tolist(),
            'source_contact_points_mm':points.tolist(),'contact_segment_length_mm':length,
            'native_shared_vertex_ids':sorted(set(vertices[0])&set(vertices[1])),
            'source_material_slots':[materials[i] for i in ids],'source_material_labels':[model['materials'][materials[i]] for i in ids],
            'midpoint_barycentric_weights':weights,'midpoint_reconstruction_errors_mm':residuals,'endpoint_barycentric_coordinates':endpoints,
            'unit_normal_cross_norm':cross,'source_instance_is_reflected':model['native_reflected_instance'],
            'classification':'nonparallel_native_triangle_interior_crossing' if interior and cross>1e-12 and length>1e-9 else 'unresolved_numerical_contact',
            'source_geometry_changed':False,'anatomical_tissue_or_pathology_classified':False,'clinical_approval':False})
    if len(records)!=summary['within_instance_contacts']:raise ValueError('Within-instance contacts are incomplete')
    regions=[]
    for model_id in sorted({r['source_model_id'] for r in records}):
        selected=[r for r in records if r['source_model_id']==model_id];remaining=set(range(len(selected)))
        while remaining:
            group={remaining.pop()};faces=set(selected[next(iter(group))]['native_source_face_ids'])
            while True:
                joined={i for i in remaining if faces&set(selected[i]['native_source_face_ids'])}
                if not joined:break
                remaining-=joined;group|=joined;faces|={fid for i in joined for fid in selected[i]['native_source_face_ids']}
            regions.append({'source_model_id':model_id,'source_model_name':models[model_id]['name'],
                'source_geometry_id':models[model_id]['source_geometry_id'],'contact_record_indices':[records.index(selected[i]) for i in sorted(group)],
                'native_source_face_ids':sorted(faces),'source_geometry_changed':False})
    result={'complete_contact_evidence_sha256':summary['uncompressed_sha256'],'native_review_sha256':sha(native_raw),
        'records':records,'regions':regions,'record_count':len(records),
        'model_quality_holds':[{'source_model_id':key,'source_model_name':models[key]['name'],
            'status':'source_surface_resolution_and_anatomical_review_required_before_clinical_promotion',
            'original_crossing_count':sum(r['source_model_id']==key for r in records)} for key in sorted({r['source_model_id'] for r in records})],
        'unique_native_geometry_face_pairs':len({(r['source_geometry_id'],*sorted(r['native_source_face_ids'])) for r in records}),
        'classifications':dict(Counter(r['classification'] for r in records)),
        'midpoint_barycentric_interior_tolerance':1e-9,'plane_reconstruction_tolerance_mm':1e-9,'normal_parallel_tolerance':1e-12,
        'source_geometry_changed':False,'clinical_approval':False,'runtime_promoted':False,
        'limits':['Triangle interior crossing is a source surface-geometry finding, not biological tissue identity or patient injury.',
            'Reflected instances repeat source geometry; their findings are not independent patient-side observations.',
            'Source material labels are artist slots, not validated histology. Numeric lengths and tolerances are not acquired resolution or clinical measurements.',
            'No repair, pruning, welding, smoothing, capping, extrusion, source-axis registration or clinical coverage is introduced.']}
    (output/'native-self-crossing-review.json').write_text(json.dumps(result,indent=2)+'\n')
    print('Classified',len(records),'original triangular self contacts;',len(regions),'source-instance regions.')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    review(p.parse_args().output)
