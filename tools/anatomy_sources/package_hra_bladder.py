#!/usr/bin/env python3
"""Retain complete HRA bladder primitives; no wall layers, caps or MRI fitting."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import struct


def source(folder, sex):
    from tools.anatomy_sources.inspect_hra_renal_glb import read_glb, accessor, inspect
    name = 'VH_' + sex[0].upper() + '_Urinary_Bladder.glb'
    path = folder / name
    review = inspect(path, folder / 'crosswalk.csv')
    document, binary = read_glb(path.read_bytes())
    if len(review['records']) != 6 or not review['all_source_meshes_inspected']:
        raise ValueError('Complete six original source mesh primitives required')
    parts = []
    for record in review['records']:
        node = document['nodes'][record['node_index']]
        primitive = document['meshes'][node['mesh']]['primitives'][record['primitive_index']]
        positions = accessor(document, binary, primitive['attributes']['POSITION'])
        normals = accessor(document, binary, primitive['attributes']['NORMAL'])
        indices = accessor(document, binary, primitive['indices']).reshape(-1)
        if positions.shape != normals.shape or positions.dtype.str != '<f4' or normals.dtype.str != '<f4':
            raise ValueError('Original positions/normals require reviewed Float32 storage')
        parts.append({'id': record['node_name'], 'vertices': positions, 'normals': normals,
                      'faces': indices.reshape(-1, 3), 'source_indices': indices, 'record': record,
                      'source_material': document['materials'][primitive['material']]})
    return review, parts


def package(source_root, output, review_output):
    import numpy as np
    from tools.anatomy_sources.audit_hra_renal_interfaces import compare_boundaries
    receipts = []
    for sex in ['female', 'male']:
        folder = source_root / sex
        metadata = json.loads((folder / 'metadata.jsonld').read_text())
        nodes = {r['@id']: r for r in metadata['@graph']}
        base = 'https://lod.humanatlas.io/ref-organ/urinary-bladder-' + sex + '/v1.1'
        raw = nodes[base + '#raw-data']
        if 'https://creativecommons.org/licenses/by/4.0/' not in raw.get('dct:license', ''):
            raise ValueError('Raw model commercial grant missing')
        review, original = source(folder, sex)
        boundaries = compare_boundaries(original)
        atlas = 'hra-bladder-' + sex + '-v1.1'
        target = output / atlas; target.mkdir(parents=True, exist_ok=True)
        manifest_parts = {}; all_positions = []
        for part in original:
            r = part['record']; pid = atlas + '-' + part['id'].lower()
            positions = part['vertices']; normals = part['normals']; indices = part['source_indices'].astype('<u4')
            transport = struct.pack('<4sII', b'BP3D', len(positions), len(indices)) + positions.tobytes() + normals.tobytes() + indices.tobytes()
            # Transport index width changes, never its original value/order.
            decoded_positions = np.frombuffer(transport, dtype='<f4', count=positions.size, offset=12).reshape(-1, 3)
            decoded_normals = np.frombuffer(transport, dtype='<f4', count=normals.size, offset=12 + positions.nbytes).reshape(-1, 3)
            decoded_indices = np.frombuffer(transport, dtype='<u4', count=len(indices), offset=12 + positions.nbytes + normals.nbytes)
            if not (np.array_equal(decoded_positions, positions) and np.array_equal(decoded_normals, normals)
                    and np.array_equal(decoded_indices, part['source_indices'])):
                raise ValueError('Original primitive transport differs')
            encoded = gzip.compress(transport, mtime=0); assert gzip.decompress(encoded) == transport
            filename = pid + '.bin.gz'; (target / filename).write_bytes(encoded)
            all_positions.append(positions)
            manifest_parts[pid] = {'id': pid, 'name': r['node_name'] + ' · source label: ' + r['source_label'],
                'source_node_name': r['node_name'], 'source_label': r['source_label'], 'source_ontology_id': r['source_ontology_id'],
                'source_representation_of': r['source_representation_of'], 'canonical_uri_metadata_match': r['semantic_metadata_exact_match'],
                'file': '/app/anatomy/' + atlas + '/' + filename, 'sha256': hashlib.sha256(encoded).hexdigest(),
                'decoded_sha256': hashlib.sha256(transport).hexdigest(), 'vertices': len(positions), 'triangles': len(indices) // 3,
                'bounds': r['bounds_original_gltf_metres'], 'source_positions_sha256': r['position_accessor_sha256'],
                'source_normals_sha256': hashlib.sha256(normals.tobytes()).hexdigest(), 'source_indices_sha256': r['indices_accessor_sha256'],
                'source_index_component_type': part['source_indices'].dtype.str,
                'source_material': part['source_material'], 'layer': 'source_regions', 'clinical_fidelity': 'unverified'}
        points = np.concatenate(all_positions); lo = points.min(0).tolist(); hi = points.max(0).tolist()
        title = 'Original HRA ' + sex + ' bladder regions · partial reference'
        notes = [
            'Six complete original HRA ' + sex + ' bladder mesh primitives are preserved: source dome/base regions, bladder neck smooth muscle, trigone and two ureteral-orifice regions. Source hierarchy names and duplicate fundus labels are retained.',
            'This curated Visible Human reference is separate from the TCGA-DK-AA6P MRI study and from the patient being reported. No fitting, overlay, registration, invented tissue layer or pathological invasion is presented.',
            'Original Float32 positions, normals and triangle order remain unchanged. Original source surfaces have open boundaries; no cap, bridge, repair, welding or smoothing was applied. Named source regions are not solid histological wall layers.',
            'The two orifice nodes retain their original FMA IDs and source labels. Their embedded representation_of strings differ from the canonical FMA URI form; the discrepancy is recorded, not silently rewritten or treated as independent anatomical proof.',
            'glTF declares metre units and Y-up coordinates. Source acquisition calibration and patient anatomical directions remain independently unverified. Cameras show source coordinates rather than anterior/posterior claims.',
            'Urothelium, lamina propria, muscularis mucosae, full detrusor bundles, serosa/adventitia, intramural ureter walls, nodes, adjacent organs, lesions and treatment interfaces are not separately supplied. Complete reporting anatomy and clinical/commercial fidelity remain unverified.',
            raw['schema1:citation'],
        ]
        manifest = {'dataset': title, 'source_url': 'https://purl.humanatlas.io/ref-organ/urinary-bladder-' + sex + '/v1.1',
            'license': 'CC BY 4.0', 'license_url': 'https://creativecommons.org/licenses/by/4.0/',
            'coordinate_system': {'basis': 'original glTF XYZ, right-handed Y-up', 'units': 'glTF declared metres', 'unit_meters': 1,
                                  'display_basis': 'native-gltf-y-up', 'registration': 'No MRI registration or independent patient-axis verification'},
            'parts': manifest_parts, 'regions': {'bladder-source': {'title': title, 'side': 'source ' + sex + ' reference',
                'parts': [{'id': k, 'layer': 'source_regions'} for k in manifest_parts], 'layers': [['source_regions', 'Original source regions']],
                'source_coordinate_cameras': True, 'uncropped_label': 'All original source regions · reporting anatomy incomplete',
                'source_up_range': [lo[1] - .001, hi[1] + .001], 'focus_bounds': [lo, hi]}},
            'viewer_notes': notes, 'clinical_approval': False, 'complete_reporting_anatomy_approved': False,
            'runtime_promoted': True, 'source_meshes_repaired_or_fitted': False,
            'source_glb_sha256': review['source_glb_sha256'], 'total_triangles': sum(r['triangles'] for r in manifest_parts.values())}
        (target / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
        review_output.mkdir(parents=True, exist_ok=True)
        (review_output / (sex + '-original-primitives.json')).write_text(json.dumps(review, indent=2) + '\n')
        (review_output / (sex + '-boundary-review.json')).write_text(json.dumps(boundaries, indent=2) + '\n')
        receipts.append({'sex': sex, 'source_glb_sha256': review['source_glb_sha256'], 'original_triangles': manifest['total_triangles'],
            'original_six_primitives_retained': True, 'source_positions_normals_and_face_order_retained': True,
            'source_boundary_edge_occurrences': boundaries['source_boundary_edge_occurrences'], 'unmatched_boundary_edges': boundaries['unmatched_boundary_edges'],
            'canonical_FMA_URI_mismatches': sum(not r['semantic_metadata_exact_match'] for r in review['records']),
            'clinical_approval': False, 'complete_reporting_anatomy_approved': False})
        print('Complete original source transport and boundary evidence saved.', flush=True)
    (review_output / 'transport-review.json').write_text(json.dumps(receipts, indent=2) + '\n')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source-root', type=Path, required=True); p.add_argument('--output', type=Path, required=True); p.add_argument('--review-output', type=Path, required=True)
    a = p.parse_args(); package(a.source_root, a.output, a.review_output)
