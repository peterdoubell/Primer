#!/usr/bin/env python3
"""Inventory exact published pelvic template arrays without granting clinical coverage."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def inspect_arrays(value):
    import numpy as np
    if not isinstance(value, list) or len(value) != 2:
        raise ValueError('Each source object needs points and original VTK cells')
    points, cells = value
    vertices = np.asarray(points, dtype='<f8')
    raw_cells = np.asarray(cells)
    if (vertices.ndim != 2 or vertices.shape[1] != 3 or not len(vertices)
            or not np.isfinite(vertices).all() or raw_cells.ndim != 1
            or raw_cells.dtype.kind not in 'iu' or not len(raw_cells)
            or len(raw_cells) % 4):
        raise ValueError('Invalid source points or integer triangle cells')
    if raw_cells.min() < 0 or raw_cells.max() > 0xffffffff:
        raise ValueError('Source cells exceed the retained unsigned integer range')
    raw_cells = raw_cells.astype('<u4')
    groups = raw_cells.reshape(-1, 4)
    if not np.all(groups[:, 0] == 3):
        raise ValueError('Only original source triangles are accepted; no triangulation inferred')
    faces = groups[:, 1:]
    if faces.max() >= len(vertices):
        raise ValueError('Source face references an absent vertex')
    triangles = vertices[faces]
    area = np.linalg.norm(np.cross(triangles[:, 1] - triangles[:, 0],
                                   triangles[:, 2] - triangles[:, 0]), axis=1)
    edges = np.sort(np.concatenate([faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]]), axis=1)
    _, counts = np.unique(edges, axis=0, return_counts=True)
    return {
        'positions': len(vertices), 'triangles': len(faces),
        'positions_float64_le_sha256': sha(vertices.tobytes()),
        'original_VTK_cells_uint32_le_sha256': sha(raw_cells.tobytes()),
        'ordered_triangle_indices_uint32_le_sha256': sha(faces.astype('<u4').tobytes()),
        'bounds': [vertices.min(0).tolist(), vertices.max(0).tolist()],
        'unreferenced_points': len(vertices) - len(np.unique(faces)),
        'zero_area_triangles': int((area == 0).sum()),
        'boundary_edges': int((counts == 1).sum()),
        'nonmanifold_edges': int((counts > 2).sum()),
        'topology_findings_are_anatomical_accuracy_metrics': False,
    }


def review(source, output, node_binary='node'):
    metadata = json.loads((source / 'record.json').read_text())
    archive = source / 'Pelvic_Visualiser.zip'
    file_record = next(f for f in metadata['files'] if f['key'] == archive.name)
    raw = archive.read_bytes()
    if len(raw) != file_record['size'] or hashlib.md5(raw).hexdigest() != file_record['checksum'].split(':')[1]:
        raise ValueError('Published archive checksum changed')
    output.mkdir(parents=True, exist_ok=True)
    report = {
        'reviewed_on': '2026-10-09', 'doi': '10.5281/zenodo.17423100',
        'source_url': 'https://zenodo.org/records/17423100',
        'source_archive_sha256': sha(raw), 'source_archive_MD5_verified': True,
        'source_metadata_sha256': sha((source / 'record.json').read_bytes()),
        'software_license': metadata['metadata'].get('license'),
        'software_license_does_not_independently_prove_anatomical_accuracy': True,
        'models': [], 'source_geometry_changed': False,
        'MRI_subject_demographics_or_acquisition_verified': False,
        'physical_coordinate_units_or_clinical_axes_verified': False,
        'template_registered_to_CVH5_or_current_MRI': False,
        'fine_reported_layer_boundaries_verified': False,
        'clinical_approval': False, 'runtime_promoted': False, 'structure_coverage_granted': False,
    }
    with zipfile.ZipFile(archive) as package:
        license_raw = package.read('Pelvic_Visualiser/License.txt')
        if license_raw != (source / 'License.txt').read_bytes():
            raise ValueError('Embedded licence differs from published file')
        (output / 'original-License.txt').write_bytes(license_raw)
        report['license_sha256'] = sha(license_raw)
        for name, expected_objects in [('Basic_model.json', 22), ('Advanced_model.json', 43)]:
            member = 'Pelvic_Visualiser/' + name
            raw = package.read(member)  # zipfile verifies the original member CRC.
            if raw != (source / name).read_bytes():
                raise ValueError('Extracted original JSON differs')
            model = json.loads(raw)
            if not isinstance(model, dict) or len(model) != expected_objects:
                raise ValueError('Original object inventory changed')
            objects = []
            for label, value in model.items():
                if not isinstance(label, str) or not label.strip():
                    raise ValueError('Original part label is missing')
                objects.append({'source_label': label, **inspect_arrays(value),
                                'source_side_suffix': label[-1] if label.endswith(('_L', '_R')) else None,
                                'side_label_independently_anatomically_verified': False})
            # V8 JSON/IEEE754 and a cursor-based VTK cell reader provide a
            # second implementation; no shared Python topology parser is used.
            result = subprocess.run([node_binary, str(Path(__file__).with_name('read_pelvic_source_arrays.cjs')),
                                     str(source / name)], text=True, capture_output=True, check=True)
            independent = json.loads(result.stdout)
            fields = ['positions', 'triangles', 'positions_float64_le_sha256',
                      'original_VTK_cells_uint32_le_sha256', 'ordered_triangle_indices_uint32_le_sha256']
            if set(independent) != set(model):
                raise ValueError('Independent object selection changed')
            for obj in objects:
                if independent[obj['source_label']] != {key: obj[key] for key in fields}:
                    raise ValueError('Independent scalar or index readback differs: ' + obj['source_label'])
            retained = gzip.compress(raw, mtime=0)
            (output / (name + '.gz')).write_bytes(retained)
            row = {'source_filename': name, 'source_archive_member': member,
                   'source_member_CRC32': package.getinfo(member).CRC,
                   'source_JSON_sha256': sha(raw), 'retained_file': name + '.gz',
                   'retained_file_sha256': sha(retained), 'original_JSON_bytes_retained': True,
                   'independent_complete_scalar_and_index_readback_verified': True,
                   'objects': objects, 'object_count': len(objects),
                   'positions': sum(o['positions'] for o in objects),
                   'triangles': sum(o['triangles'] for o in objects),
                   'source_normals_or_biological_colour_supplied_in_JSON': False}
            report['models'].append(row)
            print(name, row['object_count'], 'objects;', row['positions'], 'positions;', row['triangles'], 'triangles')
    basic, advanced = [json.loads(gzip.decompress((output / m['retained_file']).read_bytes())) for m in report['models']]
    organs = ['Bladder', 'Urethra', 'Uterus', 'Vagina', 'Rectum & intestinum']
    if any(basic[label] != advanced[label] for label in organs):
        raise ValueError('Shared source organ arrays differ')
    report['identical_shared_organ_arrays'] = organs
    report['limits'] = [
        'These are authored software templates, not a verified complete native MRI case or current patient.',
        'Combined Anal sphincter and Rectum & intestinum objects do not separately supply all reported layers or lumens.',
        'Source-side labels and view directions are retained, not silently declared clinical LPS/RAS axes.',
        'No dynamics, material calibration, deformation, registration, smoothing or anatomical repair is introduced.',
        'Scalar/index agreement verifies transport and interpretation, not independent tissue fidelity or clinical completeness.',
    ]
    (output / 'review.json').write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--node-binary', default='node')
    args = parser.parse_args()
    review(args.source, args.output, args.node_binary)
