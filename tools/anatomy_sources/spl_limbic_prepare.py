"""Lossless proposal only: native SPL MRI/labels and original RAS mesh geometry."""
import json
from pathlib import Path
import shutil
import sys
import xml.etree.ElementTree as ET

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.anatomy_sources.spl_limbic_source import (
    SOURCE, PROPOSAL, REVIEW, RESEARCH, COMMIT, CODES, VOLUMES,
    parse_nrrd, parse_vtk, pack_mesh, deterministic_gzip, sha, require, apply_affine)


def payload_row(filename, decoded, packed=None):
    packed = deterministic_gzip(decoded) if packed is None else packed
    target = PROPOSAL / filename
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(packed)
    return {'file': filename, 'byteLength': len(decoded), 'gzipBytes': len(packed),
            'gzipSHA256': sha(packed), 'decodedSHA256': sha(decoded)}


def prepare():
    PROPOSAL.mkdir(parents=True, exist_ok=True)
    REVIEW.mkdir(parents=True, exist_ok=True)
    index = json.loads((RESEARCH / 'external-metadata/spl-tree.json').read_text())
    blobs = {row['path']: row for row in index['tree'] if row['type'] == 'blob'}
    import hashlib
    def original(path):
        raw = (SOURCE / path).read_bytes()
        row = blobs[path]
        require(len(raw) == row['size'] and hashlib.sha1(('blob ' + str(len(raw)) + '\0').encode() + raw).hexdigest() == row['sha'],
                'Original Git blob differs: ' + path)
        return {'repositoryPath': path, 'url': 'https://raw.githubusercontent.com/mhalle/spl-brain-atlas/' + COMMIT + '/' + path,
                'bytes': len(raw), 'sha256': sha(raw), 'gitBlobSHA1': row['sha']}
    scene_info = original('slicer/brain-atlas.mrml')
    scene = ET.parse(SOURCE / 'slicer/brain-atlas.mrml').getroot()
    require(scene.attrib.get('version') == 'Slicer4.4.0', 'Scene version differs from the original RAS convention')
    storage = {node.attrib['id']: node.attrib for node in scene if node.tag in {'VolumeArchetypeStorage', 'ModelStorage'}}
    volumes, volume_proofs = {}, {}
    labels_array = None
    for key, path in VOLUMES.items():
        source = original(path)
        model = parse_nrrd(SOURCE / path)
        name = {'T1w': 'T1', 'T2w': 'T2', 'labels': 'labels'}[key]
        expected_type = '<i2' if name == 'labels' else '<f4'
        expected_shape = (256, 256, 256) if name == 'labels' else (288, 320, 208)
        require(model['shape'] == expected_shape and model['dtype'] == expected_type, 'Native volume shape/type changed')
        matches = [node for node in scene if node.tag in {'Volume', 'LabelMapVolume'}
                   and storage.get(node.attrib.get('storageNodeRef'), {}).get('fileName') == path.removeprefix('slicer/')]
        require(matches, 'Selected source volume is absent from the main MRML scene')
        valid = []
        for node in matches:
            attrs = node.attrib
            require(not attrs.get('transformNodeRef') and 'transform:' not in attrs.get('references', ''), 'A selected volume has a parent transform')
            mrml = np.eye(4)
            mrml[:3, :3] = np.asarray([float(v) for v in attrs['ijkToRASDirections'].split()]).reshape(3, 3) * np.asarray([float(v) for v in attrs['spacing'].split()])
            mrml[:3, 3] = [float(v) for v in attrs['origin'].split()]
            require(np.array_equal(mrml, model['voxelToRAS']), 'NRRD LPS and main MRML RAS matrices disagree')
            valid.append({'id': attrs['id'], 'name': attrs['name'], 'voxelToRAS': mrml.tolist(), 'parentTransform': None})
        row = {**payload_row(name + '.bin.gz', model['decoded'], model['gzip']), 'name': name,
               'shape': list(model['shape']), 'dtype': model['dtype'], 'storageOrder': 'F',
               'offsetFormula': 'i + nx * (j + ny * k)', 'voxelToRAS': model['voxelToRAS'].tolist(),
               'voxelToLPS': model['voxelToLPS'].tolist(), 'spaceUnits': 'mm', 'source': source,
               'allOriginalSampleBitsPreserved': True, 'resampled': False}
        header_name = 'originals/' + Path(path).name + '.header.txt'
        (PROPOSAL / header_name).parent.mkdir(exist_ok=True)
        (PROPOSAL / header_name).write_bytes(model['header'].encode('ascii') + b'\n\n')
        row['sourceHeaderFile'] = header_name
        require(sha((PROPOSAL / header_name).read_bytes() + (PROPOSAL / row['file']).read_bytes()) == source['sha256'],
                'Original NRRD cannot be exactly reconstructed from header and unchanged gzip body')
        a = model['array']
        row['intensityRange'] = [float(a.min()), float(a.max())]
        row['finiteSampleCount'] = int(a.size)
        if name == 'labels':
            labels_array = a.copy()
            label_affine = model['voxelToRAS'].copy()
            row['labelCodesInSource'] = [int(v) for v in np.unique(a)]
        else:
            positive = a[a > 0]
            require(len(positive) > 0, 'MRI has no positive finite samples for a display window')
            low, high = np.percentile(positive, [.5, 99.5])
            row['positiveIntensityPercentiles'] = {'0.5': float(low), '99.5': float(high)}
            row['defaultWindow'] = [0., float(high)]
            row['displayWindowMeaning'] = 'Presentation-only clipping; source MRI intensities and native samples remain unchanged. MRI values are not HU.'
        volumes[name] = row
        volume_proofs[name] = {'source': source, 'header': model['header'], 'MRML_nodes': valid,
                               'sampleCount': int(a.size), 'all_original_sample_bytes_exact': True}
        print('Preserved native', name, a.size, 'samples', flush=True)
        del model, a
    require(volumes['T1']['voxelToRAS'] == volumes['T2']['voxelToRAS'], 'Native T1/T2 source grids differ')
    palette = {}
    original('slicer/colortables/hncma-atlas-lut.ctbl')
    for line in (SOURCE / 'slicer/colortables/hncma-atlas-lut.ctbl').read_text().splitlines():
        if not line.strip() or line.startswith('#'):
            continue
        values = line.split()
        require(len(values) == 6, 'Original color table row differs')
        palette[int(values[0])] = (values[1], [int(v) for v in values[2:]])
    labels, meshes, mesh_proofs = [], [], []
    for code in CODES:
        source_name, rgba = palette[code]
        ijk = np.argwhere(labels_array == code)
        require(len(ijk) > 0, 'Selected source class is empty')
        centroid = apply_affine(label_affine, ijk.mean(0)[None, :])[0].tolist()
        labels.append({'code': code, 'name': source_name.replace('_', ' '), 'sourceName': source_name,
                       'color': rgba[:3], 'sourceRGBA': rgba, 'voxelCount': len(ijk), 'centroidRAS': centroid})
        paths = list((SOURCE / 'slicer/models').glob('Model_' + str(code) + '_*.vtk'))
        require(len(paths) == 1, 'A selected class does not have one exact original mesh')
        path = str(paths[0].relative_to(SOURCE))
        source = original(path)
        nodes = [node.attrib for node in scene if node.tag == 'Model'
                 and storage.get(node.attrib.get('storageNodeRef'), {}).get('fileName') == path.removeprefix('slicer/')]
        require(nodes, 'Selected VTK model absent from the original main scene')
        require(all(not node.get('transformNodeRef') and 'transform:' not in node.get('references', '') for node in nodes),
                'Selected original model has a parent transform')
        model = parse_vtk(paths[0])
        payload, layout, extra = pack_mesh(model)
        normals = payload_row('model-' + str(code) + '-normals.bin.gz', extra['normals'])
        strips = payload_row('model-' + str(code) + '-strips.bin.gz', extra['originalStrips'])
        original_vtk = payload_row('originals/' + Path(path).name + '.gz', model['raw'])
        positions = model['positions'].astype('<f4').tobytes()
        triangles = model['triangles'].tobytes()
        mesh = {**payload_row('model-' + str(code) + '.mesh.gz', payload), 'code': code,
                'name': source_name.replace('_', ' '), 'structure': source_name,
                'originalFile': path, 'source': source, 'originalVTK': original_vtk,
                'coordinateSystem': 'RAS', 'sourceAffine': np.eye(4).tolist(), 'voxelToRAS': np.eye(4).tolist(),
                'positionsAlreadyRAS': True, 'sourceGridPosition': False, 'spaceUnits': 'mm',
                'vertexCount': model['vertexCount'], 'triangleCount': model['triangleCount'],
                'positionByteSHA256': sha(positions), 'indexByteSHA256': sha(triangles),
                'layout': layout, 'originalNormals': {**normals, 'dtype': '<f4', 'components': 3, 'count': model['vertexCount']},
                'originalStrips': {**strips, 'dtype': '<i4', 'stripCount': model['stripCount'],
                                   'intCount': model['stripIntCount'], 'encoding': 'length-prefixed original point indices'},
                'boundsRAS': [model['positions'].min(0).astype(float).tolist(), model['positions'].max(0).astype(float).tolist()],
                'winding': 'For each original strip offset i: (v_i,v_i+1,v_i+2) for even i; swap the first two for odd i. Every implied triangle, including degeneracies, is retained.',
                'sourceVerticesNormalsAndStripBitsExact': True, 'smoothedOrRepairedByPrimer': False,
                'exactCategoricalVoxelBoundaryClaim': False}
        meshes.append(mesh)
        mesh_proofs.append({'code': code, 'source': source, 'mainMRMLNodes': nodes,
                            'all_position_and_normal_float32_bits_recover_original_big_endian_bytes': True,
                            'all_source_strip_int32_bits_recover_original_big_endian_bytes': True,
                            'every_implied_triangle_retained': True,
                            'triangle_provenance_sha256': sha(model['triangleProvenance'].tobytes()),
                            'originalStripCount': model['stripCount'], 'triangleCount': model['triangleCount']})
    from tools.anatomy_sources.spl_limbic_label_boundary import prepare_label_boundaries
    label_meshes = prepare_label_boundaries(labels_array, label_affine, labels, volumes['labels']['source'], payload_row)
    license_raw = (RESEARCH / 'coordinate-evidence/slicer-4.4-License.txt').read_bytes()
    (PROPOSAL / 'LICENSE.txt').write_bytes(license_raw)
    for original_notice in ['README.md', 'LICENSE.md']:
        shutil.copyfile(SOURCE / original_notice, PROPOSAL / ('SOURCE-' + original_notice))
    notice = ('All or portions of this licensed product (such portions are the "Software") have been obtained under license from The Brigham and Women\'s Hospital, Inc. and are subject to the following terms and conditions:\n\n'
              'The complete 3D Slicer license, including all Part B conditions, accompanies this package as LICENSE.txt. It applies to the SPL atlas data. Retain the license and this notice in redistributed copies and documentation.\n\n'
              'SPL-PNL/NAC Brain Atlas: Michael Halle, Florin Talos, Marianna Jakab, Nikos Makris, Dominic Meier, Laurence Wald, Bruce Fischl and Ron Kikinis; Brigham and Women\'s Hospital, Harvard Medical School, Massachusetts General Hospital and collaborators. Source commit ' + COMMIT + '.\n'
              'https://www.openanatomy.org/atlas-pages/atlas-spl-nac-brain.html\nhttps://github.com/mhalle/spl-brain-atlas\n\n'
              'Publisher-listed additional contributors: Ilwoo Lyu and Martin Styner (Sulcal Curves); Samira Farough (Ventricular System); Ibraheem Naeem and Maria Naeem (Head and Neck Muscles); George Papadimitriou (Cerebellar Parcellation); Madiha Tahir (White Matter). The original source README, including funding acknowledgements and citation instructions, accompanies this package as SOURCE-README.md.\n\n'
              'Modified transport and derived visualization version by Primer, 2026-10-16. Exact categorical label-boundary meshes are newly derived from every exposed original label voxel-cell face; they are not original publisher VTK files. No components, cavities, or faces are deleted. The original publisher VTK models are separately retained for comparison.\n'
              'Conversion: native MRI/label sample bytes are unchanged; original NRRD gzip bodies and headers permit exact source-file reconstruction. VTK coordinate/normal/strip bits are retained; triangle strips are expanded without deleting any implied triangle. Display colors follow the original lookup table. No MRI resampling, coordinate fitting, smoothing, capping, merging or anatomical repair is applied.\n'
              'This single source case and its processed anatomical labels/surfaces do not establish normal populations, pathology, current-patient registration, complete fine anatomy or clinical approval. The source license states that clinical applications are neither recommended nor advised. No source institution endorsement is implied.\n')
    (PROPOSAL / 'ATTRIBUTION.txt').write_text(notice)
    result = {'schemaVersion': 1, 'source': 'SPL-PNL/NAC Brain Atlas', 'sourceCommit': COMMIT,
              'sourceCoordinateSystem': 'RAS', 'sourceCoordinateUnits': 'mm',
              'sourceCoordinateExplanation': 'Legacy Slicer4.4.0 model coordinates are already RAS millimetres. NRRD LPS affines are converted by diag(-1,-1,1,1). Do not apply modern unmarked-VTK=LPS defaults or a second sign flip to these original model vertices.',
              'volumes': {key: volumes[key] for key in ['T1', 'T2']}, 'labelVolume': volumes['labels'],
              'labels': labels, 'meshes': meshes, 'labelMeshes': label_meshes, 'defaultSurfaceSet': 'labelMeshes', 'licenseFile': 'LICENSE.txt', 'attributionFile': 'ATTRIBUTION.txt',
              'license': '3D Slicer Contribution and Software License Agreement v1.0, Part B and applicable Part C',
              'licenseURL': 'https://www.openanatomy.org/atlas-pages/slicer-license.html',
              'sourceNoticeFiles': ['SOURCE-README.md', 'SOURCE-LICENSE.md'],
              'originalSurfaceWarning': 'Original publisher surfaces are distinct processed objects and do not coincide exactly with categorical labels. The fornix shows substantial differences: left original vertex-to-label-boundary maximum 5.48 mm and label-face-center-to-original-surface maximum 12.24 mm; right vertex maximum 7.17 mm. These sampled distances are not continuous Hausdorff bounds. Use labelMeshes for exact categorical cell boundaries.',
              'clinicalApproval': False, 'completeReportingAnatomyApproved': False, 'normalPopulationAtlas': False,
              'currentPatientRegistration': False, 'newFittedTransforms': False,
              'surfaceMeaning': 'labelMeshes are exact categorical voxel-cell boundaries from all selected source label voxels. meshes are distinct original publisher-processed surfaces. Their spatial relation to original categorical labels is audited separately; they are not relabelled as exact voxel-cell boundaries.',
              'halfVoxelWarning': 'The separately published 1mm T1 resample starts at(-127.5,-127.5,127.5)LPS; labels start at(-128,-128,128)LPS. That resample is not used here. Native0.75mm images and1mm labels retain separate affines.'}
    (PROPOSAL / 'manifest.json').write_text(json.dumps(result, indent=2) + '\n')
    proof = {'source_commit': COMMIT, 'scene': scene_info, 'scene_version': scene.attrib['version'],
             'volume_proofs': volume_proofs, 'mesh_proofs': mesh_proofs,
             'original_native_sample_count': sum(row['finiteSampleCount'] for row in volumes.values()),
             'transport_manifest_sha256': sha((PROPOSAL / 'manifest.json').read_bytes()),
             'source_mesh_triangles': sum(row['triangleCount'] for row in meshes),
             'exact_label_boundary_triangles': sum(row['triangleCount'] for row in label_meshes),
             'exact_label_boundary_proof_sha256': sha((RESEARCH / 'label-boundary-proof.json').read_bytes()),
             'geometry_or_native_samples_changed': False, 'clinical_approval': False}
    (RESEARCH / 'transport-proof.json').write_text(json.dumps(proof, indent=2) + '\n')
    print(json.dumps({'manifest': str(PROPOSAL / 'manifest.json'), 'sha256': proof['transport_manifest_sha256'],
                      'native_samples': proof['original_native_sample_count'], 'meshes': len(meshes),
                      'triangles': proof['source_mesh_triangles']}))
    return result


if __name__ == '__main__':
    prepare()
