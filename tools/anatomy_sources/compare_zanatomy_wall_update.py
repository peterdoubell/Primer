#!/usr/bin/env python3
"""Compare current original Blender wall geometry with the pinned native FBX evidence."""
import argparse
import gzip
import hashlib
import json
import re
import zipfile
from pathlib import Path
import shutil


def sha(raw):return hashlib.sha256(raw).hexdigest()


def compare(root,previous,output):
    import numpy as np
    from tools.anatomy_sources.render_zanatomy_wall_source import decode
    from tools.anatomy_sources.review_zanatomy_wall_source import native_polygons
    output.mkdir(parents=True,exist_ok=True)
    old_raw=(previous/'native-wall-review.json').read_bytes();old=json.loads(old_raw)
    inv_raw=(root/'native-wall/original-blend-wall-inventory.json').read_bytes();inv=json.loads(inv_raw)
    meta=json.loads((root/'archive-metadata.json').read_text());archive=(root/'Z-Anatomy.zip').read_bytes()
    if len(archive)!=meta['size'] or hashlib.sha1(('blob '+str(len(archive))+'\0').encode()+archive).hexdigest()!=meta['sha']:raise ValueError('Pinned Git archive identity differs')
    with zipfile.ZipFile(root/'Z-Anatomy.zip') as zipped:
        if zipped.testzip() is not None or sha(zipped.read('Z-Anatomy/Startup.blend'))!=sha((root/'Startup.blend').read_bytes()):raise ValueError('Original scene archive CRC or extracted bytes differ')
    commit=json.loads((root/'commit.json').read_text());records=[]
    if {r['object_name'] for r in inv['records']}!={i['name'] for i in old['instances']}:raise ValueError('Complete original wall object set differs')
    for item in inv['records']:
        packed=(root/'native-wall'/item['file']).read_bytes();raw=gzip.decompress(packed)
        if sha(packed)!=item['sha256'] or sha(raw)!=item['uncompressed_sha256']:raise ValueError('Native Blender capture differs')
        source=json.loads(raw);model=next(i for i in old['instances'] if i['name']==item['object_name'])
        g=next(g for g in old['geometries'] if g['geometry_id']==model['source_geometry_id']);payload=gzip.decompress((previous/g['file']).read_bytes())
        if sha(payload)!=g['uncompressed_sha256']:raise ValueError('Original FBX arrays differ')
        e=json.loads(payload);positions=np.asarray(decode(e['positions'])).reshape(-1,3)
        polygons=native_polygons(decode(e['polygon_vertex_index']),len(positions));new=np.asarray(source['original_mesh']['positions'])
        equal=np.array_equal(positions,new);faces=polygons==source['original_mesh']['polygons']
        assignments=list(decode(e['original_layers']['LayerElementMaterial']['Materials']))
        if e['original_layers']['LayerElementMaterial']['MappingInformationType']==['AllSame']:assignments*=len(polygons)
        matrix=np.asarray(source['matrix_world']);det=float(np.linalg.det(matrix[:3,:3]))
        if not np.isfinite(matrix).all() or abs(det)<1e-12:raise ValueError('Singular/unreviewed original Blender transform')
        records.append({'object_name':item['object_name'],'previous_model_id':model['source_model_id'],'previous_geometry_id':model['source_geometry_id'],
            'current_mesh_name':source['mesh_name'],'capture_compressed_sha256':item['sha256'],'capture_uncompressed_sha256':item['uncompressed_sha256'],
            'previous_positions_float64_sha256':sha(positions.astype('<f8').tobytes()),'current_positions_float64_sha256':sha(new.astype('<f8').tobytes()),
            'original_positions':len(new),'original_polygons':len(source['original_mesh']['polygons']),
            'local_positions_exactly_equal':equal,'polygon_corner_order_exactly_equal':faces,
            'material_assignments_exactly_equal':assignments==source['original_mesh']['polygon_material_indices'],
            'material_slot_names_exactly_equal':model['materials']==source['original_mesh']['materials'],
            'previous_material_slots':model['materials'],'current_material_slots':source['original_mesh']['materials'],
            'resolved_per_face_material_names_equal':[model['materials'][i] for i in assignments]==[source['original_mesh']['materials'][i] for i in source['original_mesh']['polygon_material_indices']],
            'original_and_evaluated_meshes_exactly_equal':source['original_mesh']==source['evaluated_mesh'],
            'modifiers':source['modifiers'],'native_blender_matrix_world':source['matrix_world'],'matrix_determinant':det,
            'unchanged_geometry_cannot_remove_existing_interior_crossings':equal and faces and abs(det)>1e-12,
            'clinical_approval':False,'source_mesh_changed_or_saved':False})
    runtime=json.loads((root/'runtime-selection.json').read_text());dmg=root/runtime['file']
    sums=(root/runtime['file'].replace('-macos-arm64.dmg','.sha256')).read_text()
    match=re.search(r'([0-9a-f]{64})\s+\*?'+re.escape(runtime['file']),sums)
    if match is None or sha(dmg.read_bytes())!=match[1]:raise ValueError('Official reader checksum differs')
    result={'source_repository':'https://github.com/Z-Anatomy/Models-of-human-anatomy','observed_head':commit['sha'],
        'source_license_sha256':sha((root/'License.txt').read_bytes()),'source_commit_date':commit['commit']['committer']['date'],'archive_url':meta['download_url'],
        'archive_crc_verified':True,'scene_bytes_match_original_archive':True,'archive_bytes':len(archive),'archive_git_blob_sha1':meta['sha'],'archive_sha256':sha(archive),
        'scene_sha256':sha((root/'Startup.blend').read_bytes()),'scene_bytes':(root/'Startup.blend').stat().st_size,
        'scene_header':(root/'Startup.blend').read_bytes()[:12].decode(),'previous_native_review_sha256':sha(old_raw),
        'original_blender_inventory_sha256':sha(inv_raw),'reader_version':inv['reader_version'],'reader_build_hash':inv['reader_build_hash'],
        'runtime_url':runtime['url'],'runtime_dmg_sha256':sha(dmg.read_bytes()),'runtime_checksum_verified':True,
        'inspection_script_sha256':sha(Path(__file__).with_name('inspect_zanatomy_wall_blend.py').read_bytes()),
        'file_autoexec_failure':inv['file_autoexec_failure'],'file_autoexec_failure_message':inv['file_autoexec_failure_message'],
        'scene_units':inv['scene_units'],'named_object_queries':inv['named_object_queries'],'records':records,
        'all_sixteen_original_wall_objects_compared':len(records)==16,'existing_model_quality_holds_resolved':False,
        'source_mesh_changed_or_saved':False,'clinical_approval':False,'runtime_promoted':False,
        'limits':['Current repository head is the observed pinned revision, not a promise about future updates.',
            'Raw mesh values and evaluated modifier output are compared separately. Embedded source script was blocked; source was not saved.',
            'Unchanged local geometry under an invertible affine source transform retains triangle interior intersections. A newer release date alone does not resolve source-quality holds.',
            'Matching material assignments and source names do not establish histology, acquired resolution, anatomical accuracy or clinical registration.']}
    (output/'current-wall-comparison.json').write_text(json.dumps(result,indent=2)+'\n')
    shutil.copyfile(root/'License.txt',output/'License.txt')
    shutil.copyfile(root/'inspection.log',output/'background-reader-log.txt')
    print('Compared all',len(records),'original current wall objects; exact local geometry matches',sum(r['local_positions_exactly_equal'] and r['polygon_corner_order_exactly_equal'] for r in records))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);p.add_argument('--previous',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();compare(a.source_root,a.previous,a.output)
