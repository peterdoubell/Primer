"""Read original wall objects in background Blender with file auto-execution disabled.

Run after --factory-startup --disable-autoexec; never saves or edits the scene.
Original mesh values and evaluated modifier output are explicitly separated.
"""
import bpy
import gzip
import hashlib
import json
from pathlib import Path
import sys

STEMS=['Rectus abdominis muscle','External abdominal oblique muscle','Internal abdominal oblique muscle',
       'Transversus abdominis muscle','Pyramidalis muscle','Investing abdominal fascia','Inguinal ligament']
TARGETS=[stem+side for stem in STEMS for side in ['.r','.l']]+['Linea alba','Transversalis fascia']


def mesh_record(mesh):
    return {'name':mesh.name,'positions':[list(v.co) for v in mesh.vertices],
        'polygons':[list(p.vertices) for p in mesh.polygons],'polygon_material_indices':[p.material_index for p in mesh.polygons],
        'materials':[m.name if m else None for m in mesh.materials]}


def main(output):
    output.mkdir(parents=True,exist_ok=True)
    rows=[];depsgraph=bpy.context.evaluated_depsgraph_get()
    for name in TARGETS:
        obj=bpy.data.objects.get(name)
        if obj is None or obj.type!='MESH':raise ValueError('Original wall object missing: '+name)
        original=mesh_record(obj.data)
        evaluated=obj.evaluated_get(depsgraph);mesh=evaluated.to_mesh(preserve_all_data_layers=True,depsgraph=depsgraph)
        derived=mesh_record(mesh);evaluated.to_mesh_clear()
        row={'object_name':name,'mesh_name':obj.data.name,'matrix_world':[list(r) for r in obj.matrix_world],
            'original_mesh':original,'evaluated_mesh':derived,'evaluated_output_is_original_mesh':original==derived,
            'parent':obj.parent.name if obj.parent else None,'modifiers':[{'name':m.name,'type':m.type,'show_viewport':m.show_viewport,'show_render':m.show_render} for m in obj.modifiers],
            'source_custom_properties':{k:str(obj[k]) for k in obj.keys()},'source_mesh_changed_or_saved':False,'clinical_approval':False}
        raw=(json.dumps(row,indent=2)+'\n').encode();packed=gzip.compress(raw,mtime=0);file=name.replace(' ','_')+'.json.gz';(output/file).write_bytes(packed)
        rows.append({'object_name':name,'file':file,'sha256':hashlib.sha256(packed).hexdigest(),'uncompressed_sha256':hashlib.sha256(raw).hexdigest(),
            'original_positions':len(original['positions']),'original_polygons':len(original['polygons']),
            'evaluated_positions':len(derived['positions']),'evaluated_polygons':len(derived['polygons']),
            'evaluated_output_is_original_mesh':row['evaluated_output_is_original_mesh'],'mesh_name':obj.data.name,'modifiers':row['modifiers']})
    queries=['rectus sheath','semilunar','scarpa','camper','aponeurosis']
    data={'reader_version':bpy.app.version_string,'reader_build_hash':bpy.app.build_hash.decode(),
        'scene_file':bpy.data.filepath,'scene_units':{'system':bpy.context.scene.unit_settings.system,'scale_length':bpy.context.scene.unit_settings.scale_length},
        'file_autoexec_failure':bpy.app.autoexec_fail,'file_autoexec_failure_message':bpy.app.autoexec_fail_message,
        'object_count':len(bpy.data.objects),'records':rows,
        'named_object_queries':{q:[{'name':o.name,'type':o.type} for o in bpy.data.objects if q in o.name.lower()] for q in queries},
        'source_mesh_changed_or_saved':False,'clinical_approval':False,'runtime_promoted':False}
    (output/'original-blend-wall-inventory.json').write_text(json.dumps(data,indent=2)+'\n')
    print('Read all',len(rows),'original wall objects without saving source scene.')


if __name__=='__main__':
    args=sys.argv[sys.argv.index('--')+1:]
    main(Path(args[0]))
