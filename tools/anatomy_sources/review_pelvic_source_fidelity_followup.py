#!/usr/bin/env python3
"""Static producer-code and native-geometry correspondence; no source execution."""
import argparse
import dis
import gzip
import hashlib
import json
import marshal
from pathlib import Path
import struct
import sys
import types
import zipfile
import zlib

import numpy as np

ARCHIVE_SHA256 = '21ed60ce4d47deb23ba20d6b3bd37cd529abb3b94d640ae6e8c8e3cf6f00308d'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def static_module(executable):
    """Read PyInstaller CArchive only; never import or run packaged software."""
    magic = b'MEI\x0c\x0b\x0a\x0b\x0e'
    cookie_offset = executable.rfind(magic)
    if cookie_offset < 0 or cookie_offset + 88 != len(executable):
        raise ValueError('Expected complete PyInstaller cookie at original EOF')
    _, length, toc_offset, toc_length, python_version, library = struct.unpack(
        '!8sIIII64s', executable[cookie_offset:])
    start = len(executable) - length
    if start < 0 or start + toc_offset + toc_length != cookie_offset:
        raise ValueError('CArchive extent mismatch')
    toc = executable[start + toc_offset:start + toc_offset + toc_length]
    cursor = 0
    entries = []
    while cursor < len(toc):
        size, pos, compressed, original, flag, kind = struct.unpack(
            '!IIIIBc', toc[cursor:cursor + 18])
        if size < 19 or cursor + size > len(toc) or pos + compressed > toc_offset:
            raise ValueError('Invalid CArchive table range')
        name = toc[cursor + 18:cursor + size].split(b'\0')[0].decode('utf-8')
        entries.append((name, pos, compressed, original, flag, kind))
        cursor += size
    module = [entry for entry in entries if entry[0] == 'Pelvic_visualiser']
    if len(module) != 1:
        raise ValueError('Producer module is not unique')
    name, pos, compressed, original, flag, kind = module[0]
    raw = executable[start + pos:start + pos + compressed]
    decoded = zlib.decompress(raw) if flag else raw
    if len(decoded) != original or kind != b's' or python_version != 312:
        raise ValueError('Unexpected module length/type/Python version')
    if sys.version_info[:2] != (3, 12):
        raise ValueError('Read Python 3.12 code objects with a Python 3.12 interpreter')
    code = marshal.loads(decoded)
    if not isinstance(code, types.CodeType):
        raise ValueError('Module is not a code object')
    return code, {'executable_sha256': sha(executable),
                  'executable_bytes': len(executable),
                  'module_marshaled_sha256': sha(decoded),
                  'module_marshaled_bytes': len(decoded),
                  'CArchive_table_sha256': sha(toc),
                  'python_version': python_version,
                  'library': library.split(b'\0')[0].decode(),
                  'source_module_name': name,
                  'source_module_executed': False}


def read_literal_landmarks(code):
    """Interpret only the producer's literal dict-building instructions."""
    instructions = list(dis.get_instructions(code))
    end = next(i for i, op in enumerate(instructions)
               if op.opname == 'STORE_NAME' and op.argval == 'refe_points')
    start = max(i for i, op in enumerate(instructions[:end])
                if op.opname == 'STORE_NAME' and op.argval == 'deformed_points') + 1
    stack = []
    retained = []
    for op in instructions[start:end]:
        retained.append({'bytecode_offset': op.offset, 'opcode': op.opname,
                         'argument': op.argval})
        n = op.arg
        if op.opname == 'LOAD_CONST':
            if isinstance(op.argval, types.CodeType):
                raise ValueError('Code object in literal landmark expression')
            stack.append(op.argval)
        elif op.opname == 'BUILD_MAP' and n == 0:
            stack.append({})
        elif op.opname == 'BUILD_LIST' and n == 0:
            stack.append([])
        elif op.opname == 'LIST_EXTEND':
            value = stack.pop()
            stack[-n].extend(value)
        elif op.opname == 'MAP_ADD':
            value, key = stack.pop(), stack.pop()
            stack[-n][key] = value
        elif op.opname == 'BUILD_CONST_KEY_MAP':
            keys = stack.pop()
            values = stack[-n:]
            del stack[-n:]
            if len(keys) != n:
                raise ValueError('Literal key count mismatch')
            stack.append(dict(zip(keys, values)))
        elif op.opname == 'DICT_UPDATE':
            value = stack.pop()
            stack[-n].update(value)
        else:
            raise ValueError('Unexpected operation in literal expression: ' + op.opname)
    if len(stack) != 1 or len(stack[0]) != 24:
        raise ValueError('Expected 24 producer reference landmarks')
    return stack[0], retained


def named_code(code):
    result = {}
    def visit(value):
        result.setdefault(value.co_name, []).append(value)
        for child in value.co_consts:
            if isinstance(child, types.CodeType):
                visit(child)
    visit(code)
    return result


def surface_distance(point, vertices, faces):
    """Exact minimum against every original triangle, plus independent vertex bound."""
    triangles = vertices[faces]
    a, b, c = triangles[:, 0], triangles[:, 1], triangles[:, 2]
    ab, ac = b - a, c - a
    normals = np.cross(ab, ac)
    normal_squared = np.einsum('ij,ij->i', normals, normals)
    signed = np.einsum('ij,ij->i', point - a, normals)
    projected = point - normals * np.divide(signed, normal_squared,
        out=np.zeros_like(signed), where=normal_squared != 0)[:, None]
    v = projected - a
    aa = np.einsum('ij,ij->i', ab, ab)
    bb = np.einsum('ij,ij->i', ab, ac)
    cc = np.einsum('ij,ij->i', ac, ac)
    dd = np.einsum('ij,ij->i', v, ab)
    ee = np.einsum('ij,ij->i', v, ac)
    denominator = aa * cc - bb * bb
    u = np.divide(cc * dd - bb * ee, denominator,
                  out=np.zeros_like(dd), where=denominator != 0)
    w = np.divide(aa * ee - bb * dd, denominator,
                  out=np.zeros_like(ee), where=denominator != 0)
    inside = (denominator != 0) & (u >= 0) & (w >= 0) & (u + w <= 1)
    distance_squared = np.where(inside, np.einsum('ij,ij->i', point - projected,
                                                point - projected), np.inf)
    closest = projected.copy()
    for first, second in [(a, b), (b, c), (c, a)]:
        edge = second - first
        squared = np.einsum('ij,ij->i', edge, edge)
        fraction = np.clip(np.divide(np.einsum('ij,ij->i', point - first, edge),
                                    squared, out=np.zeros_like(squared),
                                    where=squared != 0), 0, 1)
        edge_point = first + fraction[:, None] * edge
        value = np.einsum('ij,ij->i', point - edge_point, point - edge_point)
        better = value < distance_squared
        distance_squared[better] = value[better]
        closest[better] = edge_point[better]
    index = int(distance_squared.argmin())
    vertex_distance = np.sqrt(np.sum((vertices - point) ** 2, axis=1)).min()
    value = float(np.sqrt(distance_squared[index]))
    if value > vertex_distance + 1e-9:
        raise ValueError('All-triangle distance exceeds vertex upper bound')
    return value, index, closest[index].tolist(), float(vertex_distance)


def components(vertices, faces):
    parent = list(range(len(vertices)))
    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    for a, b, c in faces.tolist():
        a = root(a)
        for v in [b, c]:
            parent[root(v)] = a
    groups = {}
    for i, face in enumerate(faces):
        groups.setdefault(root(int(face[0])), []).append(i)
    return sorted(({'triangles': len(ids), 'referenced_vertices': len(np.unique(faces[ids]))}
                   for ids in groups.values()), key=lambda x: -x['triangles'])


def review(source, preserved, output):
    raw_archive = (source / 'Pelvic_Visualiser.zip').read_bytes()
    if sha(raw_archive) != ARCHIVE_SHA256:
        raise ValueError('Original source archive changed')
    output.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(source / 'Pelvic_Visualiser.zip') as archive:
        code, executable = static_module(archive.read('Pelvic_Visualiser/Pelvic_visualiser.exe'))
        landmarks, literal_instructions = read_literal_landmarks(code)
        raw_model = archive.read('Pelvic_Visualiser/Advanced_model.json')
        if raw_model != gzip.decompress((preserved / 'Advanced_model.json.gz').read_bytes()):
            raise ValueError('Preserved source JSON does not match original ZIP member')
        model = json.loads(raw_model)
        examples = {n: json.loads(archive.read(n)) for n in archive.namelist()
                    if n.startswith('Pelvic_Visualiser/Morphs/') and n.endswith('.json')}
    codes = named_code(code)
    selected = ['mesh_creator', 'model_setup', 'fast_directed_hausdorff_with_points',
                'hide_show_distance', 'side_detection']
    disassembly = []
    for name in selected:
        if len(codes[name]) != 1:
            raise ValueError('Selected producer function ambiguous')
        function = codes[name][0]
        disassembly.append({'source_function': name, 'source_filename': function.co_filename,
            'source_line': function.co_firstlineno,
            'instructions': [{'offset': op.offset, 'opcode': op.opname, 'argument': op.argrepr}
                             for op in dis.get_instructions(function)]})
    bones = {}
    for name, arrays in model.items():
        if name.startswith(('Pelvic Bone_', 'Sacrum_', 'Coccyx_')):
            bones[name] = (np.asarray(arrays[0], dtype='<f8'),
                           np.asarray(arrays[1], dtype='<u4').reshape(-1, 4)[:, 1:])
    rows = []
    for name, point in landmarks.items():
        measured = []
        for bone, (vertices, faces) in bones.items():
            value, face, closest, vertex_bound = surface_distance(np.asarray(point), vertices, faces)
            measured.append({'source_bone_label': bone, 'distance_source_units': value,
                'original_triangle_index': face, 'closest_surface_point': closest,
                'independent_nearest_vertex_upper_bound': vertex_bound})
        nearest = min(measured, key=lambda x: x['distance_source_units'])
        rows.append({'source_landmark': name, 'original_coordinate': point, **nearest,
                     'anatomical_landmark_adjudicated': False})
    organs = []
    for name in ['Bladder', 'Urethra', 'Uterus', 'Vagina', 'Rectum & intestinum']:
        arrays = model[name]
        points = np.asarray(arrays[0], dtype='<f8')
        faces = np.asarray(arrays[1], dtype='<u4').reshape(-1, 4)[:, 1:]
        organs.append({'source_label': name, 'positions': len(points), 'triangles': len(faces),
            'positions_float64_le_sha256': sha(points.tobytes()),
            'ordered_triangle_indices_uint32_le_sha256': sha(faces.astype('<u4').tobytes()),
            'source_bounds': [points.min(0).tolist(), points.max(0).tolist()],
            'index_connected_triangle_components': components(points, faces),
            'named_or_material_organ_layers_in_original_JSON': [],
            'fine_layer_boundaries_verified': False})
    pairs = []
    for name, point in landmarks.items():
        if name.endswith('_L'):
            other = landmarks[name[:-2] + '_R']
            delta = np.asarray(point) - other
            pairs.append({'left_landmark': name, 'right_landmark': name[:-2] + '_R',
                          'left_minus_right': delta.tolist(),
                          'distance_source_units': float(np.linalg.norm(delta))})
    report = {'reviewed_on': '2026-10-10', 'source_doi': '10.5281/zenodo.17423100',
        'source_archive_sha256': sha(raw_archive), 'static_executable_read': executable,
        'source_geometry_bytes_changed': False, 'original_JSON_sha256': sha(raw_model),
        'producer_reference_landmarks': rows,
        'producer_landmark_literal_instructions': literal_instructions,
        'source_axis_evidence': {
            'paired_laterality_vectors': pairs,
            'PSP_minus_PSA': (np.asarray(landmarks['PSP']) - landmarks['PSA']).tolist(),
            'L5_minus_PSI': (np.asarray(landmarks['L5']) - landmarks['PSI']).tolist(),
            'assessment': 'Authored directions: +X left, +Y posterior, +Z superior, supported by producer reference labels and original bone surfaces. Clinical acquisition axes and DICOM/model registration are not established.',
            'original_model_oriented_or_scaled_by_review': False,
            'source_units_declared': 'millimetres',
            'manual_evidence': 'User_manual.pdf printed p25, Hausdorff distance; printed p40, Figure 37',
            'producer_code_evidence': 'PolyData(vertices, faces) direct construction; unscaled cKDTree coordinate distance displayed as millimeter',
            'acquired_physical_calibration_independently_verified': False},
        'source_organ_geometry': organs,
        'shipped_example_target_landmarks': examples,
        'example_targets_assumed_source_reference': False,
        'producer_model_anatomical_origin_established': False,
        'fine_reported_layer_fidelity_verified': False,
        'clinical_approval': False, 'runtime_promoted': False,
        'CVH5_decoder_or_registration_holds_cleared': False}
    (output / 'native-correspondence-review.json').write_text(json.dumps(report, indent=2) + '\n')
    (output / 'producer-code-evidence.json').write_text(json.dumps(disassembly, indent=2) + '\n')
    print(json.dumps({'landmarks': len(rows), 'nearest_surface_distance_range_source_units':
        [min(x['distance_source_units'] for x in rows), max(x['distance_source_units'] for x in rows)],
        'organs': [{'name': x['source_label'], 'components': len(x['index_connected_triangle_components'])}
                   for x in organs]}, indent=2))


def read_glb(path):
    raw = path.read_bytes()
    if len(raw) < 20:
        raise ValueError('Truncated GLB')
    magic, version, declared = struct.unpack_from('<4sII', raw)
    if magic != b'glTF' or version != 2 or declared != len(raw):
        raise ValueError('GLB header/length mismatch')
    chunks = []
    cursor = 12
    while cursor < len(raw):
        length, kind = struct.unpack_from('<II', raw, cursor)
        start = cursor + 8
        if length % 4 or start + length > len(raw):
            raise ValueError('Invalid GLB chunk range')
        chunks.append((kind, raw[start:start + length]))
        cursor = start + length
    if [x[0] for x in chunks] != [0x4E4F534A, 0x004E4942]:
        raise ValueError('Expected native JSON and BIN chunks only')
    gltf = json.loads(chunks[0][1])
    if gltf['asset']['version'] != '2.0' or gltf.get('extensionsRequired'):
        raise ValueError('Unexpected required decoder extension')
    return raw, gltf, chunks[1][1]


def gltf_accessor(gltf, binary, index):
    accessor = gltf['accessors'][index]
    if accessor.get('sparse') or accessor.get('normalized'):
        raise ValueError('Unexpected sparse or normalized native array')
    view = gltf['bufferViews'][accessor['bufferView']]
    if view['buffer'] != 0:
        raise ValueError('Native array references an external buffer')
    dtypes = {5121: '<u1', 5123: '<u2', 5125: '<u4', 5126: '<f4'}
    dimensions = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}
    dtype = np.dtype(dtypes[accessor['componentType']])
    components = dimensions[accessor['type']]
    size = components * dtype.itemsize
    stride = view.get('byteStride', size)
    offset = view.get('byteOffset', 0) + accessor.get('byteOffset', 0)
    end = offset + (accessor['count'] - 1) * stride + size
    if stride < size or end > view.get('byteOffset', 0) + view['byteLength'] or end > len(binary):
        raise ValueError('Accessor exceeds native binary span')
    array = np.ndarray((accessor['count'], components), dtype=dtype,
                       buffer=binary, offset=offset, strides=(stride, dtype.itemsize)).copy()
    if not np.isfinite(array).all():
        raise ValueError('Nonfinite native accessor')
    return array, {'source_accessor_index': index, 'source_bufferView': accessor['bufferView'],
        'source_BIN_offset': offset, 'source_span_bytes': end - offset, 'byteStride': stride,
        'component_type': accessor['componentType'], 'type': accessor['type'],
        'count': accessor['count'], 'native_packed_array_sha256': sha(array.tobytes()),
        'source_span_sha256': sha(binary[offset:end])}


def review_hra(source, output):
    path = source / '3d-vh-f-united.glb'
    raw, gltf, binary = read_glb(path)
    metadata_path = source / 'united-female-v1.10-metadata.json'
    metadata_raw = metadata_path.read_bytes()
    metadata = json.loads(metadata_raw)
    original = metadata['was_derived_from']
    if (metadata['version'] != 'v1.10' or
            metadata['license'] != 'https://creativecommons.org/licenses/by/4.0/' or
            not any(d['downloadUrl'].endswith('/3d-vh-f-united.glb')
                    for d in original['distributions'])):
        raise ValueError('HRA source identity or rights changed')
    names = ['VH_F_vagina', 'VH_F_fallopian_tube', 'VH_F_ligaments_of_uterus_and_ovaries',
             'VH_F_ovary', 'VH_F_uterus', 'VH_F_rectum', 'VH_F_sigmoid_colon',
             'VH_F_right_ureter', 'VH_F_left_ureter', 'VH_F_urinary_bladder', 'VH_F_pelvis']
    name_map = {}
    parent = {}
    for i, node in enumerate(gltf['nodes']):
        name_map.setdefault(node.get('name'), []).append(i)
        for child in node.get('children', []):
            if child in parent or child < 0 or child >= len(gltf['nodes']):
                raise ValueError('Source hierarchy is not a strict tree')
            parent[child] = i
    selected = set()
    def select(index, active):
        if index in active:
            raise ValueError('Source hierarchy cycle')
        selected.add(index)
        for child in gltf['nodes'][index].get('children', []):
            select(child, active | {index})
    for name in names:
        if len(name_map.get(name, [])) != 1:
            raise ValueError('Named source reference is absent or ambiguous: ' + name)
        select(name_map[name][0], set())
    rows = []
    for index in sorted(selected):
        node = gltf['nodes'][index]
        if 'mesh' not in node:
            continue
        ancestry = []
        cursor = index
        while True:
            if cursor in ancestry:
                raise ValueError('Parent cycle')
            ancestry.append(cursor)
            if any(k in gltf['nodes'][cursor] for k in ['matrix', 'scale', 'rotation', 'translation']):
                raise ValueError('Selected native pelvic geometry has a nonidentity ancestor')
            if cursor not in parent:
                break
            cursor = parent[cursor]
        primitives = []
        for primitive_index, primitive in enumerate(gltf['meshes'][node['mesh']]['primitives']):
            if primitive.get('mode', 4) != 4 or primitive.get('targets'):
                raise ValueError('Unexpected nontriangle or morphed native mesh')
            attributes = {}
            arrays = {}
            for name, accessor in primitive['attributes'].items():
                arrays[name], attributes[name] = gltf_accessor(gltf, binary, accessor)
            indices, index_record = gltf_accessor(gltf, binary, primitive['indices'])
            if (indices.size % 3 or indices.max() >= len(arrays['POSITION'])
                    or arrays['POSITION'].shape[1] != 3):
                raise ValueError('Invalid original source triangles')
            points = arrays['POSITION']
            primitives.append({'primitive_index': primitive_index,
                'attributes': attributes, 'indices': index_record,
                'positions': len(points), 'triangles': int(indices.size // 3),
                'original_native_bounds_metres': [points.min(0).tolist(), points.max(0).tolist()],
                'source_material_index': primitive.get('material'),
                'original_source_material': gltf['materials'][primitive['material']]
                    if 'material' in primitive else None})
        rows.append({'source_node_index': index, 'source_node_name': node['name'],
            'source_mesh_index': node['mesh'], 'source_mesh_name': gltf['meshes'][node['mesh']].get('name'),
            'source_node_extras': node.get('extras', {}),
            'source_ancestry_node_indices': ancestry,
            'source_world_transform_identity_verified': True,
            'primitives': primitives, 'fine_structure_anatomical_review': 'pending'})
    standalones = []
    for item in sorted(source.glob('*-v1.1-metadata.json')):
        value = json.loads(item.read_bytes())
        for distribution in value['was_derived_from']['distributions']:
            if distribution['downloadUrl'].endswith('.glb'):
                local = source / distribution['downloadUrl'].rsplit('/', 1)[1]
                if local.exists():
                    small_raw, small_gltf, _ = read_glb(local)
                    standalones.append({'metadata_filename': item.name,
                        'metadata_sha256': sha(item.read_bytes()),
                        'original_glb_filename': local.name, 'original_glb_bytes': len(small_raw),
                        'original_glb_sha256': sha(small_raw),
                        'original_source_download_url': distribution['downloadUrl'],
                        'source_license': value['license'],
                        'source_raw_data_doi': value['was_derived_from'].get('doi'),
                        'original_provenance_description': value['was_derived_from'].get('description'),
                        'original_mesh_count': len(small_gltf['meshes']),
                        'original_node_count': len(small_gltf['nodes'])})
    report = {'reviewed_on': '2026-10-10', 'source_version': 'v1.10',
        'source_raw_data_doi': original['doi'], 'source_citation': original['citation'],
        'source_metadata_sha256': sha(metadata_raw),
        'source_license': metadata['license'], 'source_raw_data_license': original['license'],
        'source_provenance_description': original['description'],
        'original_GLB_staging_path': str(path.resolve()), 'original_GLB_bytes': len(raw),
        'original_GLB_sha256': sha(raw), 'original_GLTF_asset_metadata': gltf['asset'],
        'original_scene_count': len(gltf['scenes']), 'original_mesh_count': len(gltf['meshes']),
        'original_node_count': len(gltf['nodes']), 'required_format_extensions': gltf.get('extensionsRequired', []),
        'selected_named_roots': names, 'selected_original_mesh_occurrences': rows,
        'selected_mesh_occurrence_count': len(rows),
        'selected_triangles': sum(p['triangles'] for row in rows for p in row['primitives']),
        'selected_original_packed_attribute_and_index_bytes': sum(
            (p['indices']['count'] * np.dtype({5121: '<u1', 5123: '<u2', 5125: '<u4'}[
                p['indices']['component_type']]).itemsize) + sum(
                a['count'] * {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[a['type']] *
                np.dtype({5121: '<u1', 5123: '<u2', 5125: '<u4', 5126: '<f4'}[
                    a['component_type']]).itemsize for a in p['attributes'].values())
            for row in rows for p in row['primitives']),
        'native_geometry_modified': False, 'source_materials_are_biological_or_MRI_signal': False,
        'native_GLTF_linear_unit': 'metre', 'native_GLTF_up_axis': '+Y',
        'GLTF_format_reference': 'https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html#coordinate-system-and-units',
        'clinical_patient_registration_verified': False,
        'authoring_preprocessing_or_layer_boundary_accuracy_independently_verified': False,
        'fine_structures_pending': ['uterine junctional zone, endometrium and myometrium',
            'torus uterinus and rectovaginal septum', 'parametrial and nerve boundaries',
            'bowel-wall layers', 'endometriosis lesions and surgical margins'],
        'older_standalone_originals_acquired': standalones,
        'standalone_uterus_provenance_inconsistency': 'v1.1 original metadata says Visible Human Male; NIH 3D entry 3DPX-020996 says Visible Human Dataset and describes VH_F_Uterus. No silent correction or donor equivalence inferred.',
        'clinical_approval': False, 'runtime_promoted': False,
        'CVH5_decoder_or_registration_holds_cleared': False}
    (output / 'hra-original-geometry-review.json').write_text(json.dumps(report, indent=2) + '\n')
    (output / 'original-hra-united-female-v1.10-metadata.json').write_bytes(metadata_raw)
    print(json.dumps({'HRA_original_GLB_sha256': sha(raw), 'selected_native_occurrences': len(rows),
                     'selected_native_triangles': report['selected_triangles'],
                     'standalone_originals_acquired': len(standalones)}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--preserved', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--hra-source', type=Path)
    args = parser.parse_args()
    review(args.source, args.preserved, args.output)
    if args.hra_source:
        review_hra(args.hra_source, args.output)
