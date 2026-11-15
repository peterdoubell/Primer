"""Pinned SPL native MRI, categorical boundaries and distinct publisher surfaces."""
import hashlib
import json
import os
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ATLAS = 'spl-nac-limbic'
IDENTIFIER = 'spl-nac-limbic-native-reference'
PREFIX = '/app/anatomy/' + ATLAS + '/'
REGISTRY = ROOT / 'data/radiology/spl-limbic-reference.json'
REGISTRY_SHA256 = 'b39194d1d98f6223816df1af5eb6754006d0810b5e814c03a6e0a1f4d01a8895'
SOURCE_COMMIT = 'bec24db25aad5f7600e2df3becfb1f883e61ff56'
SOURCE_MANIFEST_SHA256 = '204f87b6d88a9570eb34664497a1462a5d8bba1afa0c2f7abe1cdf11082de2e6'
SOURCE_REVIEW_SHA256 = 'a68a06adab2658924a02f5367de168ac4a55b87ed02b9be3b719fcb8ccdf8e81'
AUTHORED = frozenset({'index.html', 'viewer.css', 'viewer.js', 'coordinates.js', 'payload.js', 'manifest.json'})
BINDINGS = frozenset({'ra.mri-epilepsy', 'ra.mri-dementia', 'ra.brain-anatomy'})
STRUCTURES = {17: 'left_hippocampus', 53: 'right_hippocampus', 18: 'left_amygdala', 54: 'right_amygdala',
              3007: 'left_fornix_of_forebrain', 3005: 'right_fornix_of_forebrain',
              3003: 'left_mammillary_body', 3002: 'right_mammillary_body',
              1016: 'left_parahippocampal_gyrus', 2016: 'right_parahippocampal_gyrus',
              100: 'left_mammillothalamic_tract', 200: 'right_mammillothalamic_tract'}
APPROVAL_FLAGS = ('clinical_approval', 'fine_anatomical_approval', 'current_patient_registration',
                  'normal_anatomical_atlas_approval', 'complete_reporting_anatomy_approved')
MRI_AFFINE = [[0., 0., -.75, 77.625], [-.75, 0., 0., 107.625], [0., -.75, 0., 119.625], [0., 0., 0., 1.]]
LABEL_AFFINE = [[0., 0., -1., 128.], [-1., 0., 0., 128.], [0., -1., 0., 128.], [0., 0., 0., 1.]]
IDENTITY = [[1., 0., 0., 0.], [0., 1., 0., 0.], [0., 0., 1., 0.], [0., 0., 0., 1.]]


def expected_files():
    result = set(AUTHORED) | {'T1.bin.gz', 'T2.bin.gz', 'labels.bin.gz', 'LICENSE.txt', 'ATTRIBUTION.txt',
                              'SOURCE-README.md', 'SOURCE-LICENSE.md'}
    result |= {'originals/' + name + '.header.txt' for name in ['A1_grayT1.nrrd', 'A1_grayT2.nrrd', 'hncma-atlas.nrrd']}
    for code, name in STRUCTURES.items():
        result |= {f'model-{code}.mesh.gz', f'model-{code}-normals.bin.gz', f'model-{code}-strips.bin.gz',
                   f'originals/Model_{code}_{name}.vtk.gz', f'label-{code}.mesh.gz', f'label-{code}-faces.bin.gz'}
    return result


@lru_cache(maxsize=1)
def registry():
    raw = REGISTRY.read_bytes()
    if hashlib.sha256(raw).hexdigest() != REGISTRY_SHA256:
        raise ValueError('SPL limbic reference registry changed')
    data = json.loads(raw)
    if (data.get('schema_version') != 1 or data.get('source_commit') != SOURCE_COMMIT
            or data.get('source_repository') != 'https://github.com/mhalle/spl-brain-atlas'
            or data.get('source_review_sha256') != SOURCE_REVIEW_SHA256
            or set(data.get('files', {})) != expected_files()
            or data.get('bindings') != {key: [IDENTIFIER] for key in BINDINGS}
            or set(data.get('inspectors', {})) != {IDENTIFIER}
            or data['files']['manifest.json']['sha256'] != SOURCE_MANIFEST_SHA256):
        raise ValueError('SPL limbic source scope differs')
    return data


def validate_file(asset):
    data = registry()
    if asset not in data['files']:
        raise ValueError('Unknown SPL limbic reference asset')
    path = ROOT / 'web/anatomy' / ATLAS / asset
    within_root = [path, *(parent for parent in path.parents if parent == ROOT or ROOT in parent.parents)]
    if any(part.is_symlink() for part in within_root) or (path.exists() and not path.is_file()):
        raise ValueError('SPL limbic reference must be a regular file')
    row = data['files'][asset]
    if path.is_file():
        raw = path.read_bytes()
        if len(raw) != row['bytes'] or hashlib.sha256(raw).hexdigest() != row['sha256']:
            raise ValueError('SPL limbic reference bytes changed')
    elif asset in AUTHORED or not os.environ.get('VERCEL'):
        raise ValueError('SPL limbic reference file missing')
    return path


@lru_cache(maxsize=1)
def references():
    data = registry()
    for asset in data['files']:
        validate_file(asset)
    item = data['inspectors'][IDENTIFIER]
    if (item.get('id') != IDENTIFIER or item.get('src') != PREFIX + 'index.html'
            or item.get('manifest_url') != PREFIX + 'manifest.json'
            or item.get('modality') != 'Native T1/T2 MRI and limbic source-label boundaries'
            or item.get('coordinate_context') != 'source-native-mri-and-separate-label-grid-in-declared-RAS'
            or item.get('bound_source_ids') != [IDENTIFIER]
            or any(item.get(flag) is not False for flag in APPROVAL_FLAGS)
            or item.get('sha256') != data['files']['index.html']['sha256']
            or item.get('manifest_sha256') != SOURCE_MANIFEST_SHA256
            or item.get('source_grain', {}).get('subject_count') != 1
            or item.get('source_grain', {}).get('separately_labelled_CA_fields_or_subiculum') is not False
            or item.get('source_grant', {}).get('terms_url') != PREFIX + 'LICENSE.txt'
            or item.get('source_grant', {}).get('marked_derived_version') is not True):
        raise ValueError('SPL limbic reference identity or approval differs')
    for field in ['title', 'caption', 'attribution', 'source_url', 'license', 'license_url']:
        if not isinstance(item.get(field), str) or not item[field].strip():
            raise ValueError('SPL limbic reference lacks source meaning')
    manifest = json.loads(validate_file('manifest.json').read_bytes())
    if (manifest.get('sourceCommit') != SOURCE_COMMIT or manifest.get('sourceCoordinateSystem') != 'RAS'
            or manifest.get('defaultSurfaceSet') != 'labelMeshes'
            or any(manifest.get(flag) is not False for flag in ['clinicalApproval', 'completeReportingAnatomyApproved',
                       'normalPopulationAtlas', 'currentPatientRegistration', 'newFittedTransforms'])
            or {row['code'] for row in manifest['labels']} != set(STRUCTURES)
            or len(manifest['labels']) != len(STRUCTURES)
            or set(manifest['volumes']) != {'T1', 'T2'}):
        raise ValueError('SPL limbic manifest meaning differs')
    arrays = [*manifest['volumes'].values(), manifest['labelVolume']]
    for row in arrays:
        is_label = row is manifest['labelVolume']
        expected = ([256, 256, 256], '<i2', LABEL_AFFINE) if is_label else ([288, 320, 208], '<f4', MRI_AFFINE)
        if ((row['shape'], row['dtype'], row['voxelToRAS']) != expected or row['storageOrder'] != 'F'
                or row.get('allOriginalSampleBitsPreserved') is not True or row.get('resampled') is not False):
            raise ValueError('SPL limbic native grid differs')
    payloads = list(arrays)
    for kind, total in [('meshes', 29130), ('labelMeshes', 37892)]:
        rows = manifest[kind]
        if len(rows) != 12 or {row['code'] for row in rows} != set(STRUCTURES) or sum(row['triangleCount'] for row in rows) != total:
            raise ValueError('SPL limbic surface scope differs')
        for row in rows:
            if (row['sourceAffine'] != IDENTITY or row['coordinateSystem'] != 'RAS'
                    or row['positionsAlreadyRAS'] is not True or row['layout']['headerBytes'] != 16
                    or row['smoothedOrRepairedByPrimer'] is not False):
                raise ValueError('SPL limbic mesh coordinates differ')
            payloads.append(row)
            if kind == 'meshes':
                if row['exactCategoricalVoxelBoundaryClaim'] is not False or row['sourceVerticesNormalsAndStripBitsExact'] is not True:
                    raise ValueError('SPL original surface meaning differs')
                payloads.extend([row['originalVTK'], row['originalNormals'], row['originalStrips']])
            else:
                if (row['kind'] != 'exact-categorical-voxel-cell-boundary'
                        or row['allComponentsAndCavitiesRetained'] is not True or row['allCellFacesExact'] is not True
                        or row['sourceLabelVoxelToRAS'] != LABEL_AFFINE):
                    raise ValueError('SPL categorical boundary meaning differs')
                payloads.append(row['faceProvenance'])
    extras = {'LICENSE.txt', 'ATTRIBUTION.txt', 'SOURCE-README.md', 'SOURCE-LICENSE.md'} | {row['sourceHeaderFile'] for row in arrays}
    if {row['file'] for row in payloads} != set(data['files']) - AUTHORED - extras or len(payloads) != 75:
        raise ValueError('SPL limbic source payload inventory differs')
    for row in payloads:
        if row['gzipSHA256'] != data['files'][row['file']]['sha256'] or row['byteLength'] <= 0:
            raise ValueError('SPL limbic source payload identity differs')
    return {key: [item] for key in BINDINGS}
