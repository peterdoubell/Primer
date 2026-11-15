#!/usr/bin/env python3
"""Package complete original selected HRA occurrences, retaining native evidence.

The excerpt changes glTF storage addresses only. Vertex arrays, vertex IDs,
ordered index values, source metadata, materials and scene transforms survive.
No crop, repair, merge, tissue-layer inference or patient registration occurs.
"""
import argparse
import copy
import gzip
import hashlib
import json
from pathlib import Path
import struct


ATLAS = 'hra-female-pelvis-v1.10'
FAMILY = 'female-pelvis-source'
SOURCE_SHA256 = '95f0c3d2f918582608692ca1139e8bdb18c147a16470e9ee9af8b276bd77c422'
SOURCE_BYTES = 374505632
SOURCE_URL = 'https://purl.humanatlas.io/ref-organ/united-female/v1.10'
LICENSE_URL = 'https://creativecommons.org/licenses/by/4.0/'
ROOT_NAMES = (
    'VH_F_vagina', 'VH_F_fallopian_tube', 'VH_F_ligaments_of_uterus_and_ovaries',
    'VH_F_ovary', 'VH_F_uterus', 'VH_F_rectum', 'VH_F_sigmoid_colon',
    'VH_F_right_ureter', 'VH_F_left_ureter', 'VH_F_urinary_bladder', 'VH_F_pelvis',
)
COMPONENTS = {5120: ('b', 1), 5121: ('B', 1), 5122: ('h', 2),
              5123: ('H', 2), 5125: ('I', 4), 5126: ('f', 4)}
WIDTHS = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')


def read_glb(raw):
    if struct.unpack_from('<4sII', raw) != (b'glTF', 2, len(raw)):
        raise ValueError('Original GLB header differs')
    size, kind = struct.unpack_from('<II', raw, 12)
    if kind != 0x4e4f534a or size % 4:
        raise ValueError('Original JSON chunk differs')
    json_raw = raw[20:20 + size]
    offset = 20 + size
    binary_size, kind = struct.unpack_from('<II', raw, offset)
    if kind != 0x004e4942 or binary_size % 4 or offset + 8 + binary_size != len(raw):
        raise ValueError('Original embedded BIN chunk differs')
    document = json.loads(json_raw)
    if (len(document.get('buffers', [])) != 1 or 'uri' in document['buffers'][0]
            or document['buffers'][0]['byteLength'] > binary_size
            or any(document.get(k) for k in ['skins', 'animations', 'extensionsRequired', 'images', 'textures'])):
        raise ValueError('Unsupported external, dynamic or extension source')
    return document, raw[offset + 8:], json_raw


def packed_accessor(document, binary, index):
    """Read raw component bits, including normalized attributes, without conversion."""
    accessor = document['accessors'][index]
    if 'sparse' in accessor or accessor['type'] not in WIDTHS:
        raise ValueError('Unsupported source accessor layout')
    view = document['bufferViews'][accessor['bufferView']]
    packed = COMPONENTS[accessor['componentType']][1] * WIDTHS[accessor['type']]
    stride = view.get('byteStride', packed)
    local = accessor.get('byteOffset', 0)
    start = view.get('byteOffset', 0) + local
    count = accessor['count']
    end = local + (count - 1) * stride + packed
    if (view['buffer'] != 0 or count <= 0 or stride < packed or end > view['byteLength']
            or view.get('byteOffset', 0) + view['byteLength'] > len(binary)):
        raise ValueError('Source accessor exceeds its declared buffer view')
    data = (binary[start:start + count * packed] if stride == packed else
            b''.join(binary[start + i * stride:start + i * stride + packed] for i in range(count)))
    return data, {'source_accessor_index': index, 'source_bufferView': accessor['bufferView'],
                  'source_BIN_offset': start, 'source_span_bytes': end - local,
                  'byteStride': stride, 'component_type': accessor['componentType'],
                  'type': accessor['type'], 'count': count, 'normalized': accessor.get('normalized', False),
                  'native_packed_array_sha256': sha(data),
                  'source_span_sha256': sha(binary[start:start + end - local])}


def select_nodes(document):
    selected = set()
    def walk(index, ancestors):
        if index in ancestors:
            raise ValueError('Cyclic source hierarchy')
        node = document['nodes'][index]
        if 'mesh' in node:
            selected.add(index)
        for child in node.get('children', []):
            walk(child, ancestors | {index})
    for name in ROOT_NAMES:
        indices = [i for i, n in enumerate(document['nodes']) if n.get('name') == name]
        if len(indices) != 1:
            raise ValueError('Source selection root is ambiguous: ' + name)
        walk(indices[0], set())
    return selected


def bounds(positions):
    values = list(struct.iter_unpack('<fff', positions))
    return [[min(p[i] for p in values) for i in range(3)],
            [max(p[i] for p in values) for i in range(3)]]


def make_glb(document, binary):
    encoded = json.dumps(document, separators=(',', ':'), ensure_ascii=False).encode()
    encoded += b' ' * (-len(encoded) % 4)
    binary += b'\0' * (-len(binary) % 4)
    return (struct.pack('<4sII', b'glTF', 2, 28 + len(encoded) + len(binary))
            + struct.pack('<II', len(encoded), 0x4e4f534a) + encoded
            + struct.pack('<II', len(binary), 0x004e4942) + binary)


def package(source_root, output, review_output, source_review):
    raw = (source_root / '3d-vh-f-united.glb').read_bytes()
    if len(raw) != SOURCE_BYTES or sha(raw) != SOURCE_SHA256:
        raise ValueError('Only the pinned original HRA female v1.10 GLB is accepted')
    document, binary, json_raw = read_glb(raw)
    metadata_raw = (source_root / 'united-female-v1.10-metadata.json').read_bytes()
    metadata = json.loads(metadata_raw)
    author = metadata['was_derived_from']
    source_distribution = next(d for d in author['distributions'] if d['downloadUrl'].endswith('/3d-vh-f-united.glb'))
    if (LICENSE_URL not in author['license'] or metadata['license'] != LICENSE_URL
            or author['doi'] != 'https://doi.org/10.48539/HBM637.DWBM.744'
            or [c['fullName'] for c in author['creators']] != ['Kristen Browne', 'Heidi Schlehlein']):
        raise ValueError('Original raw model license and attribution are required')
    review = json.loads(source_review.read_text())
    reviewed = {o['source_node_index']: o for o in review['selected_original_mesh_occurrences']}
    selected = select_nodes(document)
    if (selected != set(reviewed) or len(selected) != 54 or review['selected_triangles'] != 293490
            or review['original_GLB_sha256'] != SOURCE_SHA256 or review['source_metadata_sha256'] != sha(metadata_raw)):
        raise ValueError('Independent source inventory differs from the complete selection')
    target = output / ATLAS
    target.mkdir(parents=True, exist_ok=True)
    review_output.mkdir(parents=True, exist_ok=True)
    # Preserve all original scene/node slots and material indices. Unselected
    # meshes are omitted; all original child links/local metadata remain intact.
    excerpt = copy.deepcopy(document)
    excerpt['accessors'] = []; excerpt['bufferViews'] = []; excerpt['meshes'] = []
    excerpt['buffers'] = [{'byteLength': 0}]
    for node in excerpt['nodes']:
        node.pop('mesh', None)
    storage = bytearray(); accessor_map = {}; mesh_map = {}; parts = {}; records = []
    all_bounds = []; packed_bytes = 0
    def retain_accessor(index):
        if index in accessor_map:
            return accessor_map[index]
        data, descriptor = packed_accessor(document, binary, index)
        storage.extend(b'\0' * (-len(storage) % 4))
        old = document['accessors'][index]
        new = copy.deepcopy(old)
        new['bufferView'] = len(excerpt['bufferViews']); new['byteOffset'] = 0
        view = {'buffer': 0, 'byteOffset': len(storage), 'byteLength': len(data)}
        original_view = document['bufferViews'][old['bufferView']]
        if 'target' in original_view:
            view['target'] = original_view['target']
        excerpt['bufferViews'].append(view); storage.extend(data)
        mapped = len(excerpt['accessors']); excerpt['accessors'].append(new)
        accessor_map[index] = mapped
        return mapped
    for index in sorted(selected):
        node = document['nodes'][index]; occurrence = reviewed[index]
        if node['name'] != occurrence['source_node_name'] or node['mesh'] != occurrence['source_mesh_index']:
            raise ValueError('Reviewed source node identity differs')
        ancestry = occurrence['source_ancestry_node_indices']
        if (not occurrence['source_world_transform_identity_verified']
                or any(any(k in document['nodes'][i] for k in ['matrix', 'translation', 'rotation', 'scale', 'skin', 'weights']) for i in ancestry)):
            raise ValueError('A nonidentity source transform requires separate supported transport')
        source_mesh = document['meshes'][node['mesh']]
        if node['mesh'] not in mesh_map:
            new_mesh = copy.deepcopy(source_mesh)
            for primitive in new_mesh['primitives']:
                if primitive.get('mode', 4) != 4 or 'targets' in primitive:
                    raise ValueError('Only complete original triangle primitives are reviewed')
                primitive['indices'] = retain_accessor(primitive['indices'])
                primitive['attributes'] = {name: retain_accessor(a) for name, a in primitive['attributes'].items()}
            mesh_map[node['mesh']] = len(excerpt['meshes']); excerpt['meshes'].append(new_mesh)
        excerpt['nodes'][index]['mesh'] = mesh_map[node['mesh']]
        if len(source_mesh['primitives']) != len(occurrence['primitives']):
            raise ValueError('Original primitive occurrence omitted')
        for primitive_index, primitive in enumerate(source_mesh['primitives']):
            proof = occurrence['primitives'][primitive_index]
            arrays = {}; descriptors = {}
            for name, ai in primitive['attributes'].items():
                arrays[name], descriptors[name] = packed_accessor(document, binary, ai)
                if any(descriptors[name][k] != proof['attributes'][name][k] for k in proof['attributes'][name]):
                    raise ValueError('Independent raw attribute proof differs')
            indices_raw, index_descriptor = packed_accessor(document, binary, primitive['indices'])
            if any(index_descriptor[k] != proof['indices'][k] for k in proof['indices']):
                raise ValueError('Independent raw index proof differs')
            if any(document['accessors'][primitive['attributes'][k]]['componentType'] != 5126
                   or document['accessors'][primitive['attributes'][k]]['type'] != 'VEC3'
                   or document['accessors'][primitive['attributes'][k]].get('normalized', False) for k in ['POSITION', 'NORMAL']):
                raise ValueError('Transport requires original Float32 VEC3 positions and normals')
            vertex_count = descriptors['POSITION']['count']; index_count = index_descriptor['count']
            fmt = COMPONENTS[index_descriptor['component_type']][0]
            index_values = struct.unpack('<' + str(index_count) + fmt, indices_raw)
            if (fmt not in ['B', 'H', 'I'] or index_count % 3 or max(index_values) >= vertex_count
                    or len(arrays['POSITION']) != len(arrays['NORMAL'])):
                raise ValueError('Original triangle primitive cannot be transported exactly')
            transport_indices = struct.pack('<' + str(index_count) + 'I', *index_values)
            transport = (struct.pack('<4sII', b'BP3D', vertex_count, index_count)
                         + arrays['POSITION'] + arrays['NORMAL'] + transport_indices)
            encoded = gzip.compress(transport, mtime=0)
            pid = ATLAS + '-n' + str(index).zfill(4) + '-p' + str(primitive_index) + '-' + node['name'].lower()
            filename = pid + '.bin.gz'; (target / filename).write_bytes(encoded)
            source_bounds = bounds(arrays['POSITION']); all_bounds.append(source_bounds)
            if source_bounds != proof['original_native_bounds_metres']:
                raise ValueError('Original primitive bounds differ')
            extras = node.get('extras', {})
            part = {'id': pid, 'name': node['name'] + ' · source label: ' + extras.get('label', '-'),
                    'source_node_index': index, 'source_mesh_index': node['mesh'], 'source_primitive_index': primitive_index,
                    'source_node_name': node['name'], 'source_mesh_name': source_mesh.get('name'),
                    'source_label': extras.get('label'), 'source_ontology_id': extras.get('ontologyid'),
                    'source_representation_of': extras.get('representation_of'), 'source_node_extras': extras,
                    'source_ancestry_node_indices': ancestry, 'source_local_transform': 'identity', 'source_global_transform': 'identity',
                    'file': '/app/anatomy/' + ATLAS + '/' + filename, 'sha256': sha(encoded), 'decoded_sha256': sha(transport),
                    'vertices': vertex_count, 'triangles': index_count // 3, 'bounds': source_bounds,
                    'source_positions_sha256': sha(arrays['POSITION']), 'source_normals_sha256': sha(arrays['NORMAL']),
                    'source_indices_sha256': sha(indices_raw), 'transport_indices_uint32_sha256': sha(transport_indices),
                    'source_index_component_type': index_descriptor['component_type'],
                    'original_attributes': descriptors, 'original_extra_attributes_retained_in_native_evidence': True,
                    'source_material_index': primitive.get('material'),
                    'source_material': document['materials'][primitive['material']],
                    'display_shading_is_biological_or_mri_signal': False,
                    'layer': 'source-surfaces', 'clinical_fidelity': 'unverified', 'fine_structure_review': 'pending'}
            parts[pid] = part
            records.append({'part_id': pid, 'source_node_index': index, 'source_mesh_index': node['mesh'],
                            'source_primitive_index': primitive_index, 'attributes': descriptors, 'indices': index_descriptor,
                            'excerpt_mesh_index': mesh_map[node['mesh']],
                            'excerpt_attribute_indices': excerpt['meshes'][mesh_map[node['mesh']]]['primitives'][primitive_index]['attributes'],
                            'excerpt_index_accessor': excerpt['meshes'][mesh_map[node['mesh']]]['primitives'][primitive_index]['indices'],
                            'original_node': node, 'original_mesh': source_mesh})
            packed_bytes += len(indices_raw) + sum(len(data) for data in arrays.values())
    if len(parts) != 54 or sum(p['triangles'] for p in parts.values()) != 293490 or packed_bytes != 5558012:
        raise ValueError('Complete selected original inventory changed')
    excerpt['buffers'][0]['byteLength'] = len(storage)
    native_raw = make_glb(excerpt, bytes(storage))
    native_encoded = gzip.compress(native_raw, mtime=0)
    native_filename = 'selected-original-native.glb.gz'
    (review_output / native_filename).write_bytes(native_encoded)
    (review_output / 'original-full-scene-json-chunk.json.gz').write_bytes(gzip.compress(json_raw, mtime=0))
    (review_output / 'original-united-female-v1.10-metadata.json').write_bytes(metadata_raw)
    (target / 'source-metadata.json').write_bytes(metadata_raw)
    (review_output / 'original-crosswalk.csv').write_bytes((source_root / 'united-female-v1.10-crosswalk.csv').read_bytes())
    (review_output / 'independent-original-geometry-review.json').write_bytes(source_review.read_bytes())
    for filename in ['independent-gltf-decoder-review.json', 'standalone-to-united-correspondence.json',
                     'source-uterus-morphology-review.json', 'uterus-female-v1.1-metadata.json',
                     'fallopian-tube-female-left-v1.1-metadata.json', 'fallopian-tube-female-right-v1.1-metadata.json',
                     'ovary-female-left-v1.1-metadata.json', 'ovary-female-right-v1.1-metadata.json']:
        (review_output / filename).write_bytes((source_root / filename).read_bytes())
    lo = [min(b[0][i] for b in all_bounds) for i in range(3)]
    hi = [max(b[1][i] for b in all_bounds) for i in range(3)]
    title = 'Original HRA female pelvic source excerpt · partial reference'
    notes = [
        '54 complete original source occurrences retain reproductive structures, uterus source regions, bladder and ureters, rectum and sigmoid colon, and the selected pelvis source meshes. This excerpt does not supply every pelvic reporting structure.',
        'Original Float32 positions, normals, vertex IDs and ordered triangle indices are preserved. Only index storage is widened to uint32 for transport; no cropping, smoothing, welding, filling, repair, merge, remap, fitting or invented geometry is applied.',
        'Source materials and the two uterus-wall COLOR_0 attributes are retained in native evidence. Viewer display colors and lighting aid selection; they are not biological tissue identity, MRI signal or acquisition intensity.',
        'Original source labels remain unchanged, including anterior and posterior wall of uterus. Those walls share 234 exact coordinate triangles. They are not independently verified endometrium, myometrium, junctional zone or histological layers.',
        'Source cutaway-like presentations and open surfaces remain intact. Native glTF uses declared metre units and Y-up coordinates; patient axes, acquisition calibration and MRI registration remain unverified. Camera names describe source coordinates.',
        'The full female assembly metadata cites the Visible Human Dataset. Older standalone uterus v1.1 metadata says Visible Human Male; that conflicting original text is retained separately and donor equivalence is not inferred.',
        'Fine structure accuracy, parametrial and nerve boundaries, rectovaginal septum, torus uterinus, bowel-wall layers, lesions and surgical margins remain pending. No clinical approval, complete reporting anatomy approval or full-module fidelity claim is made.',
        author['citation'],
    ]
    manifest = {'dataset': title, 'source_url': SOURCE_URL, 'source_version': 'v1.10',
                'license': 'CC BY 4.0', 'license_url': LICENSE_URL, 'citation': author['citation'],
                'source_raw_data_doi': author['doi'], 'source_metadata_sha256': sha(metadata_raw),
                'coordinate_system': {'basis': 'original glTF XYZ, right-handed Y-up', 'units': 'glTF declared metres',
                                      'unit_meters': 1, 'display_basis': 'native-gltf-y-up',
                                      'registration': 'No patient-axis verification or MRI registration'},
                'source_coordinate_system': 'native-gltf-y-up',
                'parts': parts, 'default_region': FAMILY,
                'regions': {FAMILY: {'title': title, 'side': 'source female assembly reference',
                                    'parts': [{'id': k, 'layer': 'source-surfaces'} for k in parts],
                                    'layers': [['source-surfaces', 'Original source surfaces']],
                                    'source_coordinate_cameras': True,
                                    'uncropped_label': 'All selected original source occurrences · reporting anatomy incomplete',
                                    'source_up_range': [lo[1] - .001, hi[1] + .001], 'focus_bounds': [lo, hi],
                                    'source_assembly_anatomically_approved': False}},
                'viewer_notes': notes, 'clinical_approval': False, 'complete_reporting_anatomy_approved': False,
                'every_structure_approved': False, 'full_module_fidelity_approved': False,
                'fine_structure_review': 'pending', 'runtime_promoted': False,
                'source_geometry_smoothed_repaired_fitted_cropped_merged_or_remapped': False,
                'source_scene_hierarchy_and_transforms_retained_in_native_evidence': True,
                'original_extra_attributes_and_materials_retained_in_native_evidence': True,
                'source_materials_are_biological_or_mri_signal': False,
                'source_glb_sha256': SOURCE_SHA256, 'source_glb_bytes': SOURCE_BYTES,
                'original_source_scene_node_count': len(document['nodes']),
                'original_source_mesh_count': len(document['meshes']),
                'selected_original_mesh_occurrences': len(selected), 'all_source_meshes_included': False,
                'total_triangles': sum(p['triangles'] for p in parts.values()),
                'native_evidence': {'path': 'docs/hra-female-pelvis-native-review/' + native_filename,
                                    'sha256': sha(native_encoded), 'decoded_sha256': sha(native_raw),
                                    'storage_address_changes_only': True}}
    write_json(target / 'manifest.json', manifest)
    attribution = ('# Original HRA female pelvic source excerpt\n\n' + author['citation'] + '\n\n'
                   + author['citationOverall'] + '\n\n'
                   + 'Original model: [HRA united-female v1.10](' + SOURCE_URL + '). '
                   + 'Creators: Kristen Browne and Heidi Schlehlein. Publisher: HuBMAP. '
                   + 'Raw-data grant: [CC BY 4.0](' + LICENSE_URL + ').\n\n'
                   + 'Changes: selection of 54 complete original source occurrences and lossless transport packaging. '
                   + 'Triangle index storage is widened to uint32. Native excerpt storage addresses change; '
                   + 'vertex IDs, ordered indices, every original attribute, materials, source hierarchy and transforms are retained. '
                   + 'No mesh geometry is cropped, repaired, smoothed, filled, merged, remapped or fitted.\n\n'
                   + 'Source metadata derives the female assembly from the Visible Human Dataset, National Library of Medicine. '
                   + 'The older standalone uterus v1.1 metadata says Visible Human Male; its original metadata is retained '
                   + 'in the review evidence. No silent correction or donor equivalence is asserted.\n\n'
                   + 'The uterus source wall labels are retained; 234 shared exact coordinate triangles do not establish '
                   + 'independent fine MRI or histological layers. Display shading is not biological or MRI signal. '
                   + 'Clinical, every-structure and complete reporting anatomy approval remain false; fine-structure review remains pending.\n')
    (target / 'ATTRIBUTION.md').write_text(attribution)
    (review_output / 'ATTRIBUTION.md').write_text(attribution)
    receipt = {'source_url': SOURCE_URL, 'source_download_url': source_distribution['downloadUrl'],
               'original_glb_ignored_staging_path': str(source_root / '3d-vh-f-united.glb'),
               'source_glb_sha256': SOURCE_SHA256, 'source_glb_bytes': SOURCE_BYTES,
               'original_JSON_chunk_sha256': sha(json_raw), 'source_metadata_sha256': sha(metadata_raw),
               'raw_data_grant': author['license'], 'citation': author['citation'], 'raw_data_doi': author['doi'],
               'selected_original_mesh_occurrences': len(selected), 'selected_original_primitives': len(parts),
               'total_triangles': manifest['total_triangles'], 'native_packed_attribute_and_index_bytes': packed_bytes,
               'native_excerpt_sha256': sha(native_encoded), 'native_excerpt_decoded_sha256': sha(native_raw),
               'native_excerpt_bytes': len(native_encoded), 'native_excerpt_decoded_bytes': len(native_raw),
               'native_excerpt_preserves_all_original_scene_nodes_and_materials': True,
               'selected_meshes_only': True, 'source_geometry_modified': False,
               'storage_address_remapping_changes_vertex_ids_or_triangle_indices': False,
               'BP3D_attributes': ['POSITION', 'NORMAL', 'indices cast to uint32'],
               'all_other_original_attributes_retained_in_native_excerpt': True,
               'transport_total_gzip_bytes': sum((target / Path(p['file']).name).stat().st_size for p in parts.values()),
               'manifest_sha256': sha((target / 'manifest.json').read_bytes()),
               'clinical_approval': False, 'complete_reporting_anatomy_approved': False,
               'every_structure_approved': False, 'full_module_fidelity_approved': False,
               'fine_structure_review': 'pending', 'records': records}
    write_json(review_output / 'transport-review.json', receipt)
    print(json.dumps({k: receipt[k] for k in ['selected_original_mesh_occurrences', 'total_triangles',
                                            'native_excerpt_bytes', 'transport_total_gzip_bytes', 'manifest_sha256']}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--review-output', type=Path, required=True)
    parser.add_argument('--source-review', type=Path, required=True)
    args = parser.parse_args()
    package(args.source_root, args.output, args.review_output, args.source_review)
