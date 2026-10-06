#!/usr/bin/env python3
"""Recover source scene relationships without inventing biological colour or clinical axes."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import struct
from tools.anatomy_sources.review_cvh5_pelvic_source import string


def sha(raw):return hashlib.sha256(raw).hexdigest()


def world_matrices(nodes,name,trail=()):
    import numpy as np
    if name=='':return [np.eye(4)]
    if name in trail:raise ValueError('Cyclic source hierarchy')
    if name not in nodes:raise ValueError('Unresolved source parent: '+name)
    result=[]
    for p in nodes[name]['parents']:
        values=np.asarray(p['matrix_values_in_source_order']);local=values.reshape(4,4,order='F')
        if not np.isfinite(local).all() or not np.array_equal(local[3],[0,0,0,1]):raise ValueError('Unreviewed projective source transform')
        for parent in world_matrices(nodes,p['name'],trail+(name,)):result.append(parent@local)
    return result


def transform_points(points,matrix):
    import numpy as np
    return np.asarray(points)@matrix[:3,:3].T+matrix[:3,3]


def transform_normals(normals,matrix):
    import numpy as np
    result=np.asarray(normals)@np.linalg.inv(matrix[:3,:3])
    length=np.linalg.norm(result,axis=1)
    if np.any(length==0):raise ValueError('Zero transformed normal')
    return result/length[:,None]


def review(source,candidates,normals,output):
    import numpy as np
    inv_raw=(source/'original-model-inventory.json').read_bytes();inv=json.loads(inv_raw)
    raw=gzip.decompress((source/'original-model.u3d.gz').read_bytes())
    if sha(raw)!=inv['u3d_sha256']:raise ValueError('Original stream differs')
    groups=[];shading={};materials={};shaders={}
    for chain in inv['modifier_chains']:
        for b in chain['modifiers']:
            pos=b['data_start'];stop=b['data_end']
            if b['type']=='0xffffff21':
                name,pos=string(raw,pos,stop);count=struct.unpack_from('<I',raw,pos)[0];pos+=4;parents=[]
                for _ in range(count):
                    parent,pos=string(raw,pos,stop);values=list(struct.unpack_from('<16f',raw,pos));matrix_sha=sha(raw[pos:pos+64]);pos+=64
                    parents.append({'name':parent,'matrix_values_in_source_order':values,'matrix_bytes_sha256':matrix_sha})
                if pos!=stop:raise ValueError('Group fields differ')
                groups.append({'name':name,'parents':parents,'source_block_sha256':b['sha256']})
            elif b['type']=='0xffffff45':
                name,pos=string(raw,pos,stop);index,attrs,count=struct.unpack_from('<III',raw,pos);pos+=12;lists=[]
                for _ in range(count):
                    n=struct.unpack_from('<I',raw,pos)[0];pos+=4;entries=[]
                    for _ in range(n):shader,pos=string(raw,pos,stop);entries.append(shader)
                    lists.append(entries)
                if pos!=stop:raise ValueError('Shading fields differ')
                shading[name]={'chain_index':index,'attributes':attrs,'shader_lists':lists,'source_block_sha256':b['sha256']}
    for b in inv['top_level_blocks']:
        pos=b['data_start'];stop=b['data_end']
        if b['type']=='0xffffff54':
            name,pos=string(raw,pos,stop);attrs=struct.unpack_from('<I',raw,pos)[0];pos+=4;values=list(struct.unpack_from('<14f',raw,pos));pos+=56
            if pos!=stop or not np.isfinite(values).all():raise ValueError('Material fields differ')
            materials[name]={'attributes':attrs,'ambient_rgb':values[:3],'diffuse_rgb':values[3:6],
                             'specular_rgb':values[6:9],'emissive_rgb':values[9:12],'reflectivity':values[12],
                             'opacity':values[13],'source_block_sha256':b['sha256'],'source_float_bytes_sha256':sha(raw[pos-56:pos])}
        elif b['type']=='0xffffff53':
            name,pos=string(raw,pos,stop);attrs,alpha,alpha_fn,blend,passes,channels,alpha_channels=struct.unpack_from('<IfIIIII',raw,pos);pos+=28
            material,pos=string(raw,pos,stop)
            if pos!=stop or channels or alpha_channels:raise ValueError('Unreviewed texture-bearing shader')
            shaders[name]={'attributes':attrs,'alpha_reference':alpha,'alpha_function':alpha_fn,'blend_function':blend,
                           'render_pass_flags':passes,'texture_channels':channels,'alpha_texture_channels':alpha_channels,
                           'material_name':material,'source_block_sha256':b['sha256']}
    all_nodes=groups+inv['model_nodes'];nodes={n['name']:n for n in all_nodes}
    if len(nodes)!=len(all_nodes):raise ValueError('Duplicate source node')
    cand_raw=(candidates/'candidate-geometry-review.json').read_bytes();cand=json.loads(cand_raw)
    norm_raw=(normals/'normal-interpretation-review.json').read_bytes();normal=json.loads(norm_raw)
    if cand['original_u3d_sha256']!=sha(raw) or normal['candidate_geometry_review_sha256']!=sha(cand_raw):raise ValueError('Candidate source link differs')
    occurrences=[]
    for node in inv['model_nodes']:
        row=next(r for r in cand['resources'] if r['resource_name']==node['resource_name']);packed=(candidates/row['file']).read_bytes()
        if sha(packed)!=row['sha256']:raise ValueError('Candidate geometry differs')
        mesh=json.loads(gzip.decompress(packed));nr=next(r for r in normal['resources'] if r['resource_name']==node['resource_name']);npacked=(normals/nr['file']).read_bytes()
        if sha(npacked)!=nr['sha256']:raise ValueError('Candidate normals differ')
        vectors=json.loads(gzip.decompress(npacked))['interpreted_normal_vectors']
        maps=shading[node['name']]['shader_lists']
        if len(maps)!=1 or len(maps[0])!=1 or set(mesh['material_indices'])!={0}:raise ValueError('Ambiguous per-face appearance binding')
        shader=shaders[maps[0][0]];material=materials[shader['material_name']]
        for world in world_matrices(nodes,node['name']):
            placed=transform_points(mesh['positions'],world);nplaced=transform_normals(vectors,world)
            determinant=float(np.linalg.det(world[:3,:3]))
            if determinant==0:raise ValueError('Singular source placement')
            occurrences.append({'node_name':node['name'],'resource_name':node['resource_name'],'source_visibility':node['visibility'],
                                'candidate_file':row['file'],'candidate_sha256':row['sha256'],'normal_file':nr['file'],'normal_sha256':nr['sha256'],
                                'source_world_matrix_rows':world.tolist(),'source_world_matrix_float64_sha256':sha(world.astype('<f8').tobytes()),
                                'source_linear_determinant':determinant,'placed_candidate_positions_float64_sha256':sha(placed.astype('<f8').tobytes()),
                                'placed_candidate_normals_float64_sha256':sha(nplaced.astype('<f8').tobytes()),
                                'placed_candidate_bounds_native_units':[placed.min(0).tolist(),placed.max(0).tolist()],
                                'triangles':len(mesh['faces']),'source_shading':shading[node['name']],
                                'source_shader_name':maps[0][0],'source_shader':shader,'source_material_name':shader['material_name'],
                                'source_material':material,'authored_colour_is_biological_signal':False,'clinical_approval':False})
    output.mkdir(parents=True,exist_ok=True)
    result={'original_u3d_sha256':sha(raw),'source_inventory_sha256':sha(inv_raw),'candidate_review_sha256':sha(cand_raw),'normal_review_sha256':sha(norm_raw),
            'group_nodes':groups,'model_node_count':len(inv['model_nodes']),'occurrences':occurrences,'occurrence_count':len(occurrences),
            'source_materials':materials,'source_shaders':shaders,'source_material_count':len(materials),'source_shader_count':len(shaders),
            'matrix_layout':'ECMA_column_major_parent_relative','source_unit_scale_to_metres':inv['file_header']['units_to_metres'],
            'extra_scale_factor_applied':1,'geometry_fitted_or_repaired':False,'source_bytes_changed':False,
            'original_rendering_engine_pixel_equivalence_verified':False,'patient_axes_or_registration_verified':False,
            'whole_decoder_independently_verified':False,'clinical_approval':False,'runtime_promoted':False,'structure_coverage_granted':False}
    (output/'source-scene-review.json').write_text(json.dumps(result,indent=2)+'\n')
    print('Recovered source groups/materials/shaders/occurrences:',len(groups),len(materials),len(shaders),len(occurrences))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--candidates',type=Path,required=True);p.add_argument('--normals',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();review(a.source,a.candidates,a.normals,a.output)
