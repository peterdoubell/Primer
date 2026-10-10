"""Independent raw glTF/accessor and BP3D checks for the exact HRA excerpt."""
import gzip
import hashlib
import json
from pathlib import Path
import struct

import numpy as np
import pytest


ROOT = Path(__file__).resolve().parents[1]
ATLAS = ROOT / 'web/anatomy/hra-female-pelvis-v1.10'
EVIDENCE = ROOT / 'docs/hra-female-pelvis-native-review'
PINNED_SOURCE = '95f0c3d2f918582608692ca1139e8bdb18c147a16470e9ee9af8b276bd77c422'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def independent_glb(raw):
    # Do not call the packaging decoder. Check every chunk and its real extent.
    assert raw[:4] == b'glTF'
    assert int.from_bytes(raw[4:8], 'little') == 2
    assert int.from_bytes(raw[8:12], 'little') == len(raw)
    chunks = []; offset = 12
    while offset < len(raw):
        count = int.from_bytes(raw[offset:offset + 4], 'little')
        kind = raw[offset + 4:offset + 8]
        assert count % 4 == 0 and offset + 8 + count <= len(raw)
        chunks.append((kind, raw[offset + 8:offset + 8 + count]))
        offset += 8 + count
    assert [kind for kind, _ in chunks] == [b'JSON', b'BIN\0']
    return json.loads(chunks[0][1]), chunks[1][1]


def independent_accessor(document, binary, index):
    # NumPy interprets the raw source storage independently of the stdlib packager.
    accessor = document['accessors'][index]
    view = document['bufferViews'][accessor['bufferView']]
    dtype = np.dtype({5120: 'i1', 5121: 'u1', 5122: '<i2', 5123: '<u2', 5125: '<u4', 5126: '<f4'}[accessor['componentType']])
    width = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[accessor['type']]
    assert 'sparse' not in accessor and view['buffer'] == 0
    packed = dtype.itemsize * width
    stride = view.get('byteStride', packed)
    local = accessor.get('byteOffset', 0)
    assert accessor['count'] > 0 and stride >= packed
    assert local + (accessor['count'] - 1) * stride + packed <= view['byteLength']
    assert view.get('byteOffset', 0) + view['byteLength'] <= len(binary)
    values = np.ndarray((accessor['count'], width), dtype=dtype, buffer=binary,
                        offset=view.get('byteOffset', 0) + local,
                        strides=(stride, dtype.itemsize)).copy()
    assert np.isfinite(values).all()
    return values


def source_files():
    manifest = json.loads((ATLAS / 'manifest.json').read_text())
    receipt = json.loads((EVIDENCE / 'transport-review.json').read_text())
    original = json.loads(gzip.decompress((EVIDENCE / 'original-full-scene-json-chunk.json.gz').read_bytes()))
    encoded = (EVIDENCE / 'selected-original-native.glb.gz').read_bytes()
    native_raw = gzip.decompress(encoded)
    native, binary = independent_glb(native_raw)
    assert sha(encoded) == manifest['native_evidence']['sha256'] == receipt['native_excerpt_sha256']
    assert sha(native_raw) == manifest['native_evidence']['decoded_sha256'] == receipt['native_excerpt_decoded_sha256']
    return manifest, receipt, original, native, binary


def test_every_native_primitive_attribute_and_transport_component_matches_independent_source_proofs():
    manifest, receipt, original, native, binary = source_files()
    review = json.loads((EVIDENCE / 'independent-original-geometry-review.json').read_text())
    three = json.loads((EVIDENCE / 'independent-gltf-decoder-review.json').read_text())
    excerpt_review = json.loads((EVIDENCE / 'independent-package-correspondence-review.json').read_text())
    excerpt_three = json.loads((EVIDENCE / 'independent-packaged-gltf-decoder-review.json').read_text())
    source_occurrences = {o['source_node_index']: o for o in review['selected_original_mesh_occurrences']}
    three_occurrences = {o['source_node_index']: o for o in three['decoded_occurrences']}
    assert len(manifest['parts']) == len(receipt['records']) == len(source_occurrences) == len(three_occurrences) == 54
    assert sum(p['triangles'] for p in manifest['parts'].values()) == manifest['total_triangles'] == 293490
    assert review['original_GLB_sha256'] == three['original_GLB_sha256'] == manifest['source_glb_sha256'] == PINNED_SOURCE
    assert three['complete_selected_native_accessor_bits_match'] and three['complete_selected_native_scene_identity_match']
    assert excerpt_review['packaged_excerpt_sha256'] == excerpt_three['packaged_excerpt_decoded_sha256'] == receipt['native_excerpt_decoded_sha256']
    assert excerpt_review['all_selected_native_accessor_dtype_shape_and_bits_identical']
    assert excerpt_review['all_original_material_objects_identical'] and excerpt_review['all_original_scene_and_ancestry_fields_identical']
    assert excerpt_three['complete_selected_native_accessor_bits_match'] and excerpt_three['complete_selected_native_scene_identity_match']
    assert not excerpt_three['anatomical_or_clinical_approval']
    total_packed = 0; colors = []
    for record in receipt['records']:
        part = manifest['parts'][record['part_id']]
        node_index = record['source_node_index']; primitive_index = record['source_primitive_index']
        proof = source_occurrences[node_index]['primitives'][primitive_index]
        primitive = native['meshes'][native['nodes'][node_index]['mesh']]['primitives'][primitive_index]
        original_primitive = original['meshes'][original['nodes'][node_index]['mesh']]['primitives'][primitive_index]
        assert set(primitive['attributes']) == set(original_primitive['attributes']) == set(record['attributes'])
        arrays = {}
        for name, accessor_index in primitive['attributes'].items():
            array = independent_accessor(native, binary, accessor_index)
            arrays[name] = array
            assert sha(array.tobytes()) == proof['attributes'][name]['native_packed_array_sha256']
            assert sha(array.tobytes()) == three_occurrences[node_index]['attributes'][name]['sha256']
            old_accessor = original['accessors'][original_primitive['attributes'][name]]
            new_accessor = native['accessors'][accessor_index]
            assert {k: v for k, v in old_accessor.items() if k not in ['bufferView', 'byteOffset']} == {
                k: v for k, v in new_accessor.items() if k not in ['bufferView', 'byteOffset']}
            total_packed += array.nbytes
            if name == 'COLOR_0':
                colors.append(node_index)
        original_indices = independent_accessor(native, binary, primitive['indices']).ravel()
        assert sha(original_indices.tobytes()) == proof['indices']['native_packed_array_sha256']
        assert sha(original_indices.tobytes()) == three_occurrences[node_index]['index_sha256']
        assert original_indices.dtype == np.dtype('<u2')
        total_packed += original_indices.nbytes
        assert primitive['material'] == original_primitive['material'] == part['source_material_index']
        assert native['materials'][primitive['material']] == part['source_material'] == proof['original_source_material']
        encoded = (ROOT / 'web' / part['file'].removeprefix('/app/')).read_bytes()
        assert sha(encoded) == part['sha256']
        raw = gzip.decompress(encoded)
        assert sha(raw) == part['decoded_sha256']
        assert struct.unpack('<4sII', raw[:12]) == (b'BP3D', len(arrays['POSITION']), original_indices.size)
        assert len(raw) == 12 + arrays['POSITION'].nbytes + arrays['NORMAL'].nbytes + original_indices.size * 4
        p = np.frombuffer(raw, '<f4', arrays['POSITION'].size, 12).reshape(arrays['POSITION'].shape)
        n = np.frombuffer(raw, '<f4', arrays['NORMAL'].size, 12 + p.nbytes).reshape(arrays['NORMAL'].shape)
        i = np.frombuffer(raw, '<u4', original_indices.size, 12 + p.nbytes + n.nbytes)
        assert p.tobytes() == arrays['POSITION'].tobytes()
        assert n.tobytes() == arrays['NORMAL'].tobytes()
        assert np.array_equal(i, original_indices)
        assert sha(i.tobytes()) == part['transport_indices_uint32_sha256']
        assert [p.min(axis=0).tolist(), p.max(axis=0).tolist()] == part['bounds'] == proof['original_native_bounds_metres']
    assert colors == [483, 484]
    assert total_packed == receipt['native_packed_attribute_and_index_bytes'] == 5558012
    assert not manifest['all_source_meshes_included']


def test_original_scene_hierarchy_extras_materials_and_identity_transforms_survive():
    manifest, receipt, original, native, _binary = source_files()
    selected = {p['source_node_index'] for p in manifest['parts'].values()}
    assert len(native['nodes']) == len(original['nodes']) == 1160
    assert len(original['meshes']) == 956 and len(native['meshes']) == 54
    assert native['scenes'] == original['scenes'] and native['scene'] == original['scene']
    assert native['materials'] == original['materials'] and len(native['materials']) == 151
    assert native['asset'] == original['asset']
    parent = {}
    for index, (old, new) in enumerate(zip(original['nodes'], native['nodes'])):
        assert {k: v for k, v in old.items() if k != 'mesh'} == {k: v for k, v in new.items() if k != 'mesh'}
        assert ('mesh' in new) == (index in selected)
        for child in old.get('children', []):
            assert child not in parent
            parent[child] = index
    for part in manifest['parts'].values():
        ancestry = []; index = part['source_node_index']
        while True:
            ancestry.append(index)
            assert not any(k in original['nodes'][index] for k in ['matrix', 'rotation', 'translation', 'scale', 'skin', 'weights'])
            if index not in parent:
                break
            index = parent[index]
        assert ancestry == part['source_ancestry_node_indices']
        assert part['source_node_extras'] == original['nodes'][part['source_node_index']]['extras']
        assert part['source_global_transform'] == part['source_local_transform'] == 'identity'
    source_json_raw = gzip.decompress((EVIDENCE / 'original-full-scene-json-chunk.json.gz').read_bytes())
    assert sha(source_json_raw) == receipt['original_JSON_chunk_sha256']


def test_full_original_ignored_glb_raw_accessors_match_committed_native_excerpt_when_available():
    _manifest, receipt, _original, native, binary = source_files()
    original_path = Path(receipt['original_glb_ignored_staging_path'])
    if not original_path.is_file():
        pytest.skip('374 MB upstream GLB is acquired separately; committed source hashes are checked above')
    original_raw = original_path.read_bytes()
    assert len(original_raw) == receipt['source_glb_bytes'] == 374505632
    assert sha(original_raw) == PINNED_SOURCE
    original, original_binary = independent_glb(original_raw)
    for record in receipt['records']:
        for name, proof in record['attributes'].items():
            a = independent_accessor(original, original_binary, proof['source_accessor_index'])
            b = independent_accessor(native, binary, record['excerpt_attribute_indices'][name])
            assert a.tobytes() == b.tobytes()
        a = independent_accessor(original, original_binary, record['indices']['source_accessor_index'])
        b = independent_accessor(native, binary, record['excerpt_index_accessor'])
        assert a.tobytes() == b.tobytes()


def test_original_raw_grant_and_conflicting_standalone_donor_wording_are_retained():
    manifest, receipt, _original, _native, _binary = source_files()
    metadata_raw = (EVIDENCE / 'original-united-female-v1.10-metadata.json').read_bytes()
    metadata = json.loads(metadata_raw); raw = metadata['was_derived_from']
    assert (ATLAS / 'source-metadata.json').read_bytes() == metadata_raw
    assert sha(metadata_raw) == receipt['source_metadata_sha256'] == manifest['source_metadata_sha256']
    assert metadata['license'] == manifest['license_url'] == 'https://creativecommons.org/licenses/by/4.0/'
    assert manifest['license'] == 'CC BY 4.0' and manifest['license_url'] in raw['license']
    assert raw['doi'] == manifest['source_raw_data_doi'] == 'https://doi.org/10.48539/HBM637.DWBM.744'
    assert [c['fullName'] for c in raw['creators']] == ['Kristen Browne', 'Heidi Schlehlein']
    assert raw['citation'] == manifest['citation']
    assert 'Female-united set' in raw['description'] and 'Visible Human Dataset' in raw['description']
    uterus = json.loads((EVIDENCE / 'uterus-female-v1.1-metadata.json').read_text())
    assert 'Visible Human Male' in uterus['was_derived_from']['description']
    for organ in ['ovary-female-left', 'ovary-female-right', 'fallopian-tube-female-left', 'fallopian-tube-female-right']:
        original = json.loads((EVIDENCE / (organ + '-v1.1-metadata.json')).read_text())
        assert 'Visible Human\nFemale' in original['was_derived_from']['description']
    notice = (ATLAS / 'ATTRIBUTION.md').read_text()
    assert raw['citation'] in notice and 'Visible Human Male' in notice
    assert 'No silent correction or donor equivalence' in notice


def test_shared_source_wall_triangles_do_not_become_fine_mri_or_histological_layers():
    manifest, receipt, _original, native, binary = source_files()
    def triangles(node_index):
        primitive = native['meshes'][native['nodes'][node_index]['mesh']]['primitives'][0]
        p = independent_accessor(native, binary, primitive['attributes']['POSITION'])
        i = independent_accessor(native, binary, primitive['indices']).ravel().reshape(-1, 3)
        # Exact source float32 bits; independent of vertex IDs or winding.
        return {b''.join(sorted(point.tobytes() for point in triangle)) for triangle in p[i]}
    assert len(triangles(483) & triangles(484)) == 234
    posterior = next(p for p in manifest['parts'].values() if p['source_node_index'] == 483)
    anterior = next(p for p in manifest['parts'].values() if p['source_node_index'] == 484)
    assert posterior['source_label'] == 'Posterior wall of uterus'
    assert anterior['source_label'] == 'Anterior wall of uterus'
    assert 'COLOR_0' in posterior['original_attributes'] and 'COLOR_0' in anterior['original_attributes']
    for value in [manifest, receipt]:
        assert not value['clinical_approval'] and not value['complete_reporting_anatomy_approved']
        assert not value['every_structure_approved'] and not value['full_module_fidelity_approved']
        assert value['fine_structure_review'] == 'pending'
    assert not manifest['source_geometry_smoothed_repaired_fitted_cropped_merged_or_remapped']
    assert not manifest['source_materials_are_biological_or_mri_signal']
    assert manifest['coordinate_system']['display_basis'] == manifest['source_coordinate_system'] == 'native-gltf-y-up'
    assert manifest['coordinate_system']['unit_meters'] == 1
    region = manifest['regions']['female-pelvis-source']
    assert len(region['parts']) == 54 and region['source_coordinate_cameras']
    assert region['layers'] == [['source-surfaces', 'Original source surfaces']]
    assert not region['source_assembly_anatomically_approved']
    assert all(p['clinical_fidelity'] == 'unverified' and p['fine_structure_review'] == 'pending' for p in manifest['parts'].values())
    notes = '\n'.join(manifest['viewer_notes'])
    for term in ['234', 'histological layers', 'junctional zone', 'Display', 'patient', 'parametrial', 'torus uterinus']:
        assert term.lower() in notes.lower()


def test_packager_handles_interleaved_normalized_bits_without_reinterpreting_or_exceeding_view():
    from tools.anatomy_sources.package_hra_female_pelvis import packed_accessor
    doc = {'accessors': [{'bufferView': 0, 'byteOffset': 2, 'componentType': 5121,
                         'count': 2, 'type': 'VEC4', 'normalized': True}],
           'bufferViews': [{'buffer': 0, 'byteOffset': 4, 'byteLength': 14, 'byteStride': 8}]}
    binary = b'HEAD' + b'xx\x00\x7f\x80\xff--' + b'yy\x01\x02\x03\x04'
    packed, proof = packed_accessor(doc, binary, 0)
    assert packed == b'\x00\x7f\x80\xff\x01\x02\x03\x04'
    assert proof['normalized'] is True and proof['source_span_bytes'] == 12
    assert sha(packed) == proof['native_packed_array_sha256']
    doc['accessors'][0]['count'] = 3
    with pytest.raises(ValueError, match='exceeds'):
        packed_accessor(doc, binary, 0)
