#!/usr/bin/env python3
"""Package original BodyParts3D thoracic candidates for source-faithful review.

No geometry repair, decimation, welding, fitting, current-patient registration,
or anatomical approval is performed. Exact-position matching is diagnostic only.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.anatomy_sources.review_bodyparts_pancreatic_geometry import read_obj

EXPECTED = {
    'FJ1451': 'FMA9756', 'FJ1451M': 'FMA9756',
    'FJ1455': 'FMA9757', 'FJ1455M': 'FMA9757',
    'FJ1454': 'FMA9758', 'FJ1454M': 'FMA9758',
    'FJ2420': 'FMA7242', 'FJ2432': 'FMA7243',
    'FJ2421': 'FMA7238', 'FJ2433': 'FMA7239', 'FJ2436': 'FMA7240',
    'FJ3131': 'FMA13295',
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def package(source, output):
    import numpy as np
    acquisition = json.loads((source / 'upstream-acquisition.json').read_text())
    if acquisition['version_manifest'] != '4.3' or acquisition['archive_crc_verified'] is not True:
        raise ValueError('Original source version or acquisition integrity missing')
    if sha((source / 'upstream-selected-4.3.zip').read_bytes()) != acquisition['archive_sha256']:
        raise ValueError('Original archive changed')
    records = {row['id']: row for row in acquisition['objects']}
    if set(records) != set(EXPECTED) or len(acquisition['objects']) != 12:
        raise ValueError('Exactly twelve original source objects required')
    for name, digest in acquisition['source_metadata_sha256'].items():
        if sha((source / name).read_bytes()) != digest:
            raise ValueError('Original mapping/license evidence changed')
    license_bytes = (source / 'upstream-license.html').read_bytes()
    if b'creativecommons.org/licenses/by-sa/2.1/jp/' not in license_bytes:
        raise ValueError('Original upstream license not established')
    originals = output / 'originals'; transport = output / 'transport'; evidence = output / 'evidence'
    for folder in [originals, transport, evidence]:
        folder.mkdir(parents=True, exist_ok=True)
    parts = []; events = []
    for identifier in sorted(EXPECTED):
        row = records[identifier]; raw = (source / 'objects' / (identifier + '.obj')).read_bytes()
        if sha(raw) != row['sha256']:
            raise ValueError('Original OBJ changed: ' + identifier)
        header = {}
        for line in raw.decode().splitlines():
            if line.startswith('#') and ':' in line:
                key, value = line[1:].split(':', 1); header[key.strip()] = value.strip()
        if (header.get('File ID') != identifier or header.get('Concept ID') != EXPECTED[identifier]
                or header.get('Compatibility version') != '4.3'):
            raise ValueError('Original OBJ identity differs')
        v, normals, faces, normal_faces = read_obj(raw.decode())
        if len(v) != len(normals) or not np.array_equal(faces, normal_faces):
            raise ValueError('Source face/normal association requires separate review')
        positions = v.astype('<f4'); normal_values = normals.astype('<f4'); indices = faces.astype('<u4')
        body = struct.pack('<4sII', b'BP3D', len(v), faces.size) + positions.tobytes() + normal_values.tobytes() + indices.tobytes()
        encoded = gzip.compress(body, mtime=0)
        (transport / (identifier + '.bin.gz')).write_bytes(encoded)
        (originals / (identifier + '.obj.gz')).write_bytes(gzip.compress(raw, mtime=0))
        decoded = gzip.decompress((transport / (identifier + '.bin.gz')).read_bytes())
        if decoded != body:
            raise ValueError('Transport round trip failed')
        points, remap = np.unique(v, axis=0, return_inverse=True); diagnostic_faces = remap[faces]
        edges = np.sort(np.concatenate([diagnostic_faces[:, [0, 1]], diagnostic_faces[:, [1, 2]], diagnostic_faces[:, [2, 0]]]), axis=1)
        unique, counts = np.unique(edges, axis=0, return_counts=True)
        for edge in unique[counts > 2]:
            incident = np.flatnonzero(np.sum(np.isin(diagnostic_faces, edge), axis=1) == 2)
            events.append({'source_id': identifier, 'edge_coordinates_source_mm': points[edge].tolist(),
                           'length_source_mm': float(np.linalg.norm(points[edge[1]] - points[edge[0]])),
                           'incident_face_indices_zero_based': incident.tolist(),
                           'incident_original_vertex_indices_zero_based': faces[incident].tolist()})
        parts.append({'id': identifier, 'label': row['source_label'], 'source_concept_id': EXPECTED[identifier],
                      'file': 'transport/' + identifier + '.bin.gz', 'source_obj': 'originals/' + identifier + '.obj.gz',
                      'source_sha256': sha(raw), 'transport_sha256': sha(encoded), 'decoded_sha256': sha(body),
                      'vertices': len(v), 'faces': len(faces), 'bounds': [v.min(0).tolist(), v.max(0).tolist()],
                      'max_position_conversion_error_source_mm': float(np.abs(positions.astype(float) - v).max()),
                      'max_normal_conversion_error': float(np.abs(normal_values.astype(float) - normals).max()),
                      'all_face_indices_preserved_in_order': True, 'original_authored_normals_retained': True,
                      'geometry_altered_beyond_measured_float32_transport': False,
                      'exact_position_boundary_edges': int((counts == 1).sum()),
                      'exact_position_nonmanifold_edges': int((counts > 2).sum()),
                      'exact_position_matching_used_only_for_diagnostics': True,
                      'producer_M_variant': identifier.endswith('M')})
    manifest = {'schema_version': 1, 'title': 'Original thoracic anatomy source candidates',
                'source_version': 'BodyParts3D 4.3', 'source_url': 'https://lifesciencedb.jp/bp3d/',
                'license': 'CC BY-SA 2.1 Japan', 'license_url': 'https://creativecommons.org/licenses/by-sa/2.1/jp/',
                'attribution': 'BodyParts3D, Copyright 2008 Database Center for Life Science (DBCLS). Geometric transport adaptation remains CC BY-SA 2.1 Japan.',
                'clinical_approval': False, 'current_patient_registration': False,
                'source_acquisition_resolution_verified': False, 'runtime_integrated': False,
                'parts': parts, 'total_faces': sum(p['faces'] for p in parts),
                'limitations': ['Curated source anatomy, not a patient-matched ultrasound volume.',
                    'Producer M variants are retained original source forms, not independent bilateral acquisitions.',
                    'No smoothing, fitting, decimation, welding, capping or artificial tissue bridges.',
                    'Source millimetres and coordinates follow original headers; acquisition calibration and patient axes remain unverified.',
                    'Four exact-position nonmanifold edges remain in the original diaphragm, spanning approximately 0.002–0.003 source mm each. They are not repaired or clinically interpreted.',
                    'Topology and triangle counts do not prove anatomical accuracy. Pleural and pericardial layers and other reportable structures remain missing.']}
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    (evidence / 'topology-events.json').write_text(json.dumps({'diagnostic_only': True, 'geometry_repaired': False, 'events': events}, indent=2) + '\n')
    (evidence / 'upstream-acquisition.json').write_bytes((source / 'upstream-acquisition.json').read_bytes())
    (evidence / 'upstream-license.html').write_bytes(license_bytes)
    for name in ['FMA2Obj-4.3.txt', 'obj2FMA-4.3.html', 'obj2FMA-partof-4.3.html']:
        (evidence / (name + '.gz')).write_bytes(gzip.compress((source / name).read_bytes(), mtime=0))
    print(len(parts), 'original objects;', manifest['total_faces'], 'faces; source topology retained')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    package(args.source_root, args.output)
