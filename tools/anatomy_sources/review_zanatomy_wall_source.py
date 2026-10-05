#!/usr/bin/env python3
"""Preserve every selected native polygon and source instance, including reflected instances."""
import argparse
import base64
from collections import Counter, defaultdict
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import sys

STEMS = ['Rectus abdominis muscle', 'External abdominal oblique muscle', 'Internal abdominal oblique muscle',
         'Transversus abdominis muscle', 'Pyramidalis muscle', 'Investing abdominal fascia', 'Inguinal ligament']
TARGETS = [stem + side for stem in STEMS for side in ['.r', '.l']] + ['Linea alba', 'Transversalis fascia']


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def array_record(values):
    raw = values.tobytes()
    return {'typecode': values.typecode, 'count': len(values), 'byte_order': 'little',
            'sha256': sha(raw), 'base64': base64.b64encode(raw).decode()}


def native_polygons(indices, count):
    polygons, current = [], []
    for i in indices:
        j = int(i) if i >= 0 else -int(i) - 1
        if not 0 <= j < count:
            raise ValueError('Native polygon index outside source positions')
        current.append(j)
        if i < 0:
            if len(current) < 3:
                raise ValueError('Unsupported native degenerate polygon')
            polygons.append(current); current = []
    if current or not polygons:
        raise ValueError('Native polygon termination differs')
    return polygons


def review(root, output):
    import numpy as np
    from tools.anatomy_sources.acquire_z_anatomy import FILES
    from tools.anatomy_sources.inspect_fbx import child, load_fbx
    from tools.anatomy_sources.audit_knee_ligament_volume_sources import topology
    if sys.byteorder != 'little':
        raise ValueError('Source typed-array parser requires reviewed little-endian runtime')
    source = root / 'MuscularSystem100.fbx'; raw = source.read_bytes()
    if len(raw) != FILES[source.name][1] or sha(raw) != FILES[source.name][2]:
        raise ValueError('Pinned original FBX differs')
    version, nodes = load_fbx(source)
    objects = next(n for n in nodes if n['name'] == 'Objects')['children']
    connections = next(n for n in nodes if n['name'] == 'Connections')['children']
    object_map = {n['properties'][0]: n for n in objects if n['properties']}
    world_raw = (root / 'world-inventory.json').read_bytes(); world = json.loads(world_raw)
    selected = [r for r in world['meshes'] if r['name'] in TARGETS]
    if Counter(r['name'] for r in selected) != Counter(TARGETS) or world['unit_meters'] != .01:
        raise ValueError('Complete selected native instances or units differ')
    output.mkdir(parents=True, exist_ok=True)
    for name in ['acquisition.json', 'ufbx-acquisition.json', 'License.txt']:
        shutil.copyfile(root / name, output / name)
    geometry_records, instance_records = [], []
    for gid in sorted({r['source_geometry_id'] for r in selected}):
        g = object_map[gid]
        if g['name'] != 'Geometry':
            raise ValueError('Native geometry identity differs')
        positions = child(g, 'Vertices')['properties'][0]
        indices = child(g, 'PolygonVertexIndex')['properties'][0]
        local = np.asarray(positions).reshape(-1, 3)
        if not np.isfinite(local).all():
            raise ValueError('Nonfinite native positions')
        polygons = native_polygons(indices, len(local))
        layers = {}
        for name in ['LayerElementNormal', 'LayerElementMaterial']:
            layer = child(g, name)
            if layer is None:
                raise ValueError('Missing original normals or material layer')
            layers[name] = {n['name']: array_record(n['properties'][0]) if hasattr(n['properties'][0], 'typecode') else n['properties']
                            for n in layer['children'] if n['properties']}
        normals=child(g,'LayerElementNormal')
        normal_mapping=child(normals,'MappingInformationType')['properties'][0]
        normal_reference=child(normals,'ReferenceInformationType')['properties'][0]
        normal_values=child(normals,'Normals')['properties'][0]
        if normal_mapping!='ByPolygonVertex' or normal_reference!='Direct' or len(normal_values)!=3*len(indices) or not np.isfinite(normal_values).all():
            raise ValueError('Unreviewed original normal domain/count')
        material = child(g, 'LayerElementMaterial')
        assignment = list(child(material, 'Materials')['properties'][0])
        mapping = child(material, 'MappingInformationType')['properties'][0]
        if mapping == 'AllSame': assignment = assignment * len(polygons)
        if mapping not in ['AllSame', 'ByPolygon'] or len(assignment) != len(polygons):
            raise ValueError('Unreviewed native material assignment')
        edges = defaultdict(list)
        for face_id, polygon in enumerate(polygons):
            for a,b in zip(polygon,polygon[1:]+polygon[:1]):
                edges[tuple(sorted((a,b)))].append({'source_face_index':face_id,'oriented_vertex_indices':[a,b]})
        edge_findings=[{'source_vertex_indices':list(key),'source_positions_local':local[list(key)].tolist(),
                       'source_face_uses':uses,'boundary':len(uses)==1,
                       'nonmanifold':len(uses)>2,'inconsistent_winding':len(uses)==2 and uses[0]['oriented_vertex_indices']==uses[1]['oriented_vertex_indices']}
                      for key,uses in sorted(edges.items()) if len(uses)!=2 or uses[0]['oriented_vertex_indices']==uses[1]['oriented_vertex_indices']]
        unreferenced=sorted(set(range(len(local)))-{i for p in polygons for i in p})
        payload = {'geometry_id': gid, 'native_geometry_name': g['properties'][1].split('\0')[0],
                   'positions': array_record(positions), 'polygon_vertex_index': array_record(indices),
                   'original_edges':array_record(child(g,'Edges')['properties'][0]),
                   'original_layers': layers,'source_edge_findings':edge_findings,
                   'unreferenced_source_position_indices':unreferenced,'source_array_values_changed': False,
                   'polygons_triangulated_or_capped': False, 'clinical_approval': False}
        encoded = (json.dumps(payload, indent=2) + '\n').encode(); packed = gzip.compress(encoded, mtime=0)
        file = str(gid) + '-native-geometry.json.gz'; (output / file).write_bytes(packed)
        if gzip.decompress((output / file).read_bytes()) != encoded:
            raise ValueError('Native-array evidence is not lossless')
        unique,inverse=np.unique(local,axis=0,return_inverse=True)
        exact_polygons=[[int(inverse[i]) for i in p] for p in polygons]
        geometry_records.append({'geometry_id': gid, 'native_geometry_name': payload['native_geometry_name'],
            'file': file, 'compressed_sha256': sha(packed), 'uncompressed_sha256': sha(encoded),
            'positions': len(local), 'polygons': len(polygons), 'polygon_sizes': dict(Counter(map(len, polygons))),
            'derived_triangulation_count_only': sum(len(p) - 2 for p in polygons),
            'native_topology': topology(polygons),
            'exact_position_analysis_topology':topology(exact_polygons),'exact_duplicate_position_records':len(local)-len(unique),
            'analysis_welding_changes_source':False,'unreferenced_source_positions':len(unreferenced), 'material_polygon_counts': dict(Counter(assignment)),
            'source_array_values_changed': False, 'polygons_triangulated_or_capped': False})
        for part in [r for r in selected if r['source_geometry_id'] == gid]:
            model = object_map[part['source_model_id']]
            if model['name'] != 'Model' or model['properties'][1].split('\0')[0] != part['name']:
                raise ValueError('Native source model name or identity differs')
            attached = [c['properties'][1] for c in connections if len(c['properties']) >= 3
                        and c['properties'][0] == 'OO' and c['properties'][2] == part['source_model_id']]
            slots = [object_map[i]['properties'][1].split('\0')[0] for i in attached if object_map[i]['name'] == 'Material']
            if gid not in attached or slots != part['materials'] or min(assignment) < 0 or max(assignment) >= len(slots):
                raise ValueError('Native geometry/material connections differ')
            matrix = np.asarray(part['world_transform_columns']).T
            transformed = np.column_stack([local, np.ones(len(local))]) @ matrix.T
            bounds = np.stack([transformed.min(0), transformed.max(0)])
            if not np.allclose(bounds, part['bounds'], rtol=0, atol=1e-12):
                raise ValueError('Independent native-array world bounds differ')
            world_mm = transformed * 10
            # Test original polygons; material colours and closedness do not prove tissue volume.
            nonplanarity = []
            for polygon in polygons:
                points = world_mm[polygon]
                if len(polygon) == 3: nonplanarity.append(0.); continue
                center = points.mean(0); _, _, basis = np.linalg.svd(points - center, full_matrices=False)
                nonplanarity.append(float(np.max(np.abs((points - center) @ basis[-1]))))
            instance_records.append({**part, 'original_polygon_count': len(polygons),
                'world_positions_float64_cm_sha256': sha(transformed.astype('<f8').tobytes()),
                'world_transform_determinant': float(np.linalg.det(matrix[:, :3])),
                'native_reflected_instance': bool(np.linalg.det(matrix[:, :3]) < 0),
                'world_bounds_cm': bounds.tolist(), 'maximum_native_polygon_nonplanarity_mm': max(nonplanarity),
                'native_model_properties': {n['properties'][0]: n['properties'][4:] for n in child(model, 'Properties70')['children']},
                'source_array_values_changed': False, 'independent_patient_side_anatomy_verified': False,
                'material_labels_are_histological_boundaries': False, 'clinical_approval': False})
    queries = ['rectus sheath', 'semilunar', 'scarpa', 'camper', 'aponeurosis']
    names = [(n['properties'][0], n['properties'][1].split('\0')[0], n['properties'][2])
             for n in objects if n['name'] == 'Model']
    holds = {q: [{'model_id': i, 'name': name, 'native_model_type': kind} for i, name, kind in names if q in name.lower()] for q in queries}
    report = {'source_fbx_sha256': sha(raw), 'fbx_version': version, 'world_inventory_sha256': sha(world_raw),
        'native_source_axes': world['axes'],
        'transform_reader_exporter_sha256':sha(Path(__file__).with_name('export_ufbx.c').read_bytes()), 'unit_meters': world['unit_meters'], 'geometries': geometry_records,
        'instances': instance_records, 'expected_source_instance_count': 16, 'all_expected_native_instances_preserved': len(instance_records) == 16,
        'named_model_queries': holds, 'source_geometry_changed': False, 'clinical_approval': False, 'runtime_promoted': False,
        'limits': ['Native reflected instances share original geometry; labels do not establish independent patient-side anatomy.',
            'Native polygons, normals, materials and transform records are conserved. World arrays use the pinned ufbx transform reader and original positions; no clinical axis registration is approved.',
            'Open fascia and material-region labels cannot supply missing tissue thickness, histology, rectus-sheath subdivisions or pathological wall/repair anatomy.',
            'Nonplanar native polygons retain their original corner order. Display tessellation remains a renderer choice, not source-preserving anatomical repair.',
            'Source named-model queries are bounded to this FBX, and source artist anatomy is not calibrated patient MRI/CT segmentation.']}
    (output / 'native-wall-review.json').write_text(json.dumps(report, indent=2) + '\n')
    print('Preserved', len(geometry_records), 'native geometries and', len(instance_records), 'source instances.')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source-root', type=Path, required=True); p.add_argument('--output', type=Path, required=True)
    a = p.parse_args(); review(a.source_root, a.output)
