"""Generate native browser pixels from original holiAtlas volumes, independently.

No viewer JavaScript, runtime hierarchy LUT, packaged MRI planes, or rendered
canvas is used to derive expected pixels. Runtime metadata identifies the UI
selection and focus; source masks independently validate every component/focus.
Mesh bytes are pinned to existing independent source-transition proofs.
"""
from __future__ import annotations
import argparse
import collections
import datetime
import gc
import gzip
import hashlib
import io
import json
from pathlib import Path
import struct
import zipfile

import nibabel as nib
import numpy as np
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / 'web/anatomy/holiatlas'
DOCS = ROOT / 'docs/holiatlas-hierarchy-review-20261025'
EXPECTED_ARCHIVE = '6932bc8063568f0037627d5b85199ff6142b4457413f8fef8817871a3ffa1ee5'
SOURCE_MEMBERS = {'structure': 'structure_atlas.nii.gz', 'tissue': 'tissue_atlas.nii.gz', 'organ': 'icm_atlas.nii.gz', 'fine': 'substructure_atlas.nii.gz', 'T1': 'T1w_average.nii.gz', 'T2': 'T2w_average.nii.gz', 'WMn': 'WMn_average.nii.gz'}
EXPECTED_SHA = {'structure': '115bdeee6b9c9fbcf2ebde2d050add0edb6f6dfb6c8cf53ac330ac812d40c080', 'tissue': '84ba630fe255e52bb1fa74572b26bae088f277c345c9931e8aa6d8930be18fd5', 'organ': '83fbe255789c42354daec630466d218060089eab94fe31104517ff75e2c98fcf', 'fine': '6d34608fd32ecb04eda638e7877cc90f903cb7edf16d7fbf84e1b8819c8ae7d8'}
AFFINE = np.array([[.5, 0, 0, -90], [0, .5, 0, -126], [0, 0, .5, -72], [0, 0, 0, 1]])
sha = lambda b: hashlib.sha256(b).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def atomic_json(path, data):
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n')
    temp.replace(path)


def load_source(archive, key):
    raw = gzip.decompress(archive.read(SOURCE_MEMBERS[key]))
    digest = sha(raw)
    if key in EXPECTED_SHA:
        assert digest == EXPECTED_SHA[key]
    header = nib.Nifti1Header.from_fileobj(io.BytesIO(raw[:352]))
    array = np.frombuffer(raw, offset=int(header['vox_offset']), dtype=header.get_data_dtype()).reshape(header.get_data_shape(), order='F')
    assert array.shape == (362, 434, 362)
    assert np.array_equal(header.get_sform(), AFFINE)
    assert float(header['scl_slope']) == 1.0 and float(header['scl_inter']) == 0.0
    return array, {'sourceMember': SOURCE_MEMBERS[key], 'nativeNIfTISHA256': digest, 'sourceDatatype': str(header.get_data_dtype()), 'shape': list(array.shape), 'sourceHeaderUnits': list(header.get_xyzt_units()), 'voxelToSourceWorld': AFFINE.tolist()}


def component_review(source, row, members=None):
    """Validate the entire source selection and every supplied component focus."""
    full_mask = np.isin(source, members) if members is not None else source == row['code']
    coordinates = np.argwhere(full_mask)
    count = len(coordinates)
    assert count == row['voxels'] and count > 0
    low, high = coordinates.min(0), coordinates.max(0)
    box = tuple(slice(int(a), int(b + 1)) for a, b in zip(low, high))
    # Bounding box is derived from original mask, never from runtime metadata.
    connected, n = ndimage.label(full_mask[box], np.ones((3, 3, 3), dtype=bool))
    sizes = np.bincount(connected.ravel())[1:]
    assert n == len(row['components26'])
    assert sorted(sizes.tolist(), reverse=True) == sorted((c['voxels'] for c in row['components26']), reverse=True)
    seen = set()
    foci = []
    for index, component in enumerate(row['components26']):
        focus = np.asarray(component['focusSourceIJK'])
        assert np.issubdtype(focus.dtype, np.integer)
        assert np.all((focus >= low) & (focus <= high))
        assert full_mask[tuple(focus)]
        cc = int(connected[tuple(focus - low)])
        assert cc > 0 and cc not in seen and sizes[cc - 1] == component['voxels']
        seen.add(cc)
        foci.append({'component': index, 'sourceComponentVoxels': int(sizes[cc - 1]), 'focusSourceIJK': focus.tolist(), 'focusSourceWorld': (AFFINE @ np.r_[focus, 1])[:3].tolist()})
    assert seen == set(range(1, n + 1))
    assert row['boundsSourceWorld'] == [(low * .5 + AFFINE[:3, 3] - .25).tolist(), (high * .5 + AFFINE[:3, 3] + .25).tolist()]
    return {'sourceVoxels': count, 'components26': n, 'allComponentsHaveUniqueValidFocus': True, 'sourceBoundsVerified': True, 'foci': foci}


def get_outline(selected):
    """Interior boundary under 4-neighbour connectivity, including plane edges."""
    padded = np.pad(selected, 1, constant_values=False)
    interior = padded[1:-1, 1:-1] & padded[:-2, 1:-1] & padded[2:, 1:-1] & padded[1:-1, :-2] & padded[1:-1, 2:]
    return selected & ~interior


def pixel_expectation(image, mask, low, high, outline):
    # Source plane dimensions are transposed into canvas row-major order; the
    # second source-plane axis increases upwards and is vertically flipped.
    values = image.astype(np.float64).T[::-1]
    selected = mask.T[::-1]
    highlighted = get_outline(selected) if outline else selected
    gray = np.floor(255 * np.clip((values - low) / (high - low), 0, 1) + .5).astype(np.uint8)
    pixels = np.empty((*gray.shape, 4), np.uint8)
    pixels[:, :, :3] = gray[:, :, None]; pixels[:, :, 3] = 255
    pixels[highlighted, 0] = np.floor(gray[highlighted] * .45 + .5)
    pixels[highlighted, 1] = pixels[highlighted, 2] = np.floor(gray[highlighted] * .45 + 140.25 + .5)
    assert int(selected.sum()) > 0 and int(highlighted.sum()) > 0
    return {'sha256': sha(pixels.tobytes()), 'shape': list(pixels.shape), 'pixels': int(gray.size), 'selectedPixels': int(selected.sum()), 'highlightedPixels': int(highlighted.sum()), 'sourcePlaneSampleSHA256': sha(np.ascontiguousarray(image, dtype='<f4').tobytes(order='F')), 'sourceSelectionSHA256': sha(np.ascontiguousarray(mask, dtype=np.uint8).tobytes(order='F'))}


def mesh_expectation(row, boundary_row, independent_row, *, composition):
    for field in ['sha256', 'gzipSHA256', 'bytes', 'gzipBytes']:
        assert row['mesh'][field] == boundary_row['mesh'][field]
    key = 'exactCompleteOriginalSourceTransitionFaces' if composition else 'exactCompleteGlobalOracleFaces'
    assert independent_row[key] and independent_row['everyTriangleHasSourceSquareCorners'] and independent_row['everyTriangleWindsOutward'] and independent_row['closedOrientedEdgeBalance']
    assert independent_row['signedVolumeMM3'] == row['voxels'] * .125
    encoded = (WEB / row['mesh']['file']).read_bytes()
    assert len(encoded) == row['mesh']['gzipBytes'] and sha(encoded) == row['mesh']['gzipSHA256']
    raw = gzip.decompress(encoded)
    assert len(raw) == row['mesh']['bytes'] and sha(raw) == row['mesh']['sha256']
    magic, vertices, triangles, reserved = struct.unpack_from('<4sIII', raw)
    assert magic == b'HVX1' and reserved == 0 and len(raw) == 16 + 12 * vertices + 12 * triangles
    assert vertices == boundary_row['vertices'] and triangles == boundary_row['triangles']
    return {'positionSHA256': sha(raw[16:16 + 12 * vertices]), 'indexSHA256': sha(raw[16 + 12 * vertices:]), 'vertices': vertices, 'triangles': triangles, 'decodedMeshSHA256': sha(raw), 'gzipMeshSHA256': sha(encoded), 'sourceIndependentBoundaryProofAccepted': True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-archive', type=Path, default=ROOT.parent / 'fidelity-next-20261023/.research/brain-source-followup/atlas_v1.0.zip')
    parser.add_argument('--composition-proof-dir', type=Path, default=ROOT / '.research/brain-hierarchy-review/composition-build')
    parser.add_argument('--output', type=Path, default=DOCS / 'reader-oracle.json')
    args = parser.parse_args()
    assert sha(args.source_archive.read_bytes()) == EXPECTED_ARCHIVE
    hierarchy_raw = (WEB / 'hierarchy.json').read_bytes(); hierarchy = json.loads(hierarchy_raw)
    assert set(hierarchy['levels']) == {'structure', 'tissue', 'organ', 'composition'}
    assert sum(len(level['sourceClasses']) for level in hierarchy['levels'].values()) == 79
    config_raw = (WEB / 'config.json').read_bytes(); config = json.loads(config_raw)
    expected_windows = {'T1': [2., 380.], 'T2': [1., 260.], 'WMn': [9., 375.]}
    assert config['windows'] == expected_windows
    spec_path = args.composition_proof_dir / 'source-compositions.json'
    spec_raw = spec_path.read_bytes(); specs = json.loads(spec_raw)['compositions']
    spec_by_id = {s['id']: s for s in specs}
    comp_boundary_path = args.composition_proof_dir / 'boundary-proof.json'
    comp_independent_path = args.composition_proof_dir / 'independent-verification.json'
    cb_raw = comp_boundary_path.read_bytes(); cb = json.loads(cb_raw)
    ci_raw = comp_independent_path.read_bytes(); ci = json.loads(ci_raw)
    assert cb['allPassed'] and ci['allPassed'] and ci['generatorBoundaryProofSHA256'] == sha(cb_raw)
    assert cb['compositionSpecificationSHA256'] == sha(spec_raw) == ci['specificationSHA256']
    comp_boundary = {r['id']: r for r in cb['rows']}; comp_verified = {r['id']: r for r in ci['rows']}
    output = {
        'schemaVersion': 1, 'scope': 'Independent original-volume browser pixel and GPU buffer oracle for 63 source scale masks and 16 explicit source compositions.',
        'pixelKeyFormat': 'level:code:component:contrast:axis:outline(0|1)', 'meshKeyFormat': 'level:code',
        'clinicalApproval': False, 'runtimeDeliveryVerified': False, 'allGenerated': False,
        'sourceArchiveSHA256': EXPECTED_ARCHIVE,
        'displayContract': {'windows': expected_windows, 'overlay': True, 'outline': 'Selected inside boundary with four orthogonal in-plane neighbours; plane-edge selected cells are boundary; replaces fill.', 'rounding': 'floor(nonnegative value + 0.5)', 'highlightRGB': ['round(gray*0.45)', 'round(gray*0.45+140.25)', 'round(gray*0.45+140.25)'], 'alpha': 255, 'axisOrder': 'Remaining native source axes in increasing order; second remaining axis increases up.'},
        'inputSHA256': {'web/anatomy/holiatlas/hierarchy.json': sha(hierarchy_raw), 'web/anatomy/holiatlas/config.json': sha(config_raw), 'composition-source-specification': sha(spec_raw), 'composition-boundary-proof': sha(cb_raw), 'composition-independent-verification': sha(ci_raw), 'generator': sha(Path(__file__).read_bytes())},
        'sources': {}, 'sourceIndependentProofs': {}, 'selections': [], 'cases': [], 'pixels': {}, 'meshes': {},
    }
    sources = {}
    with zipfile.ZipFile(args.source_archive) as archive:
        for level in ['structure', 'tissue', 'organ', 'fine']:
            sources[level], output['sources'][level] = load_source(archive, level)
        for level in ['structure', 'tissue', 'organ', 'composition']:
            rows = hierarchy['levels'][level]['sourceClasses']
            if level != 'composition':
                boundary_path = DOCS / f'{level}-boundary-proof.json'
                independent_path = DOCS / f'{level}-independent-verification.json'
                boundary = read(boundary_path); independent = read(independent_path)
                assert boundary['allPassed'] and independent['allPassed']
                assert boundary['sourceLabelSHA256'] == EXPECTED_SHA[level] == independent['sourceLabelSHA256']
                assert len(rows) == len(boundary['rows']) == len(independent['rows'])
                by_code = {r['code']: r for r in boundary['rows']}; verified = {r['code']: r for r in independent['rows']}
                output['sourceIndependentProofs'][level] = {'boundaryProofSHA256': sha(boundary_path.read_bytes()), 'independentProofSHA256': sha(independent_path.read_bytes()), 'originalSourceSHA256': EXPECTED_SHA[level], 'allPassed': True}
                assert sorted(int(x) for x in np.unique(sources[level]) if x) == sorted(r['code'] for r in rows)
            else:
                output['sourceIndependentProofs'][level] = {'boundaryProofSHA256': sha(cb_raw), 'independentProofSHA256': sha(ci_raw), 'originalSourceSHA256': EXPECTED_SHA['fine'], 'allPassed': True}
            for row in rows:
                code = row['code']; members = None; composition_id = None
                if level == 'composition':
                    composition_id = row.get('sourceCompositionId') or row.get('compositionId') or specs[code - 1]['id']
                    spec = spec_by_id[composition_id]
                    members = sorted(spec['fine_codes'])
                    assert sorted(row['fineSourceCodes']) == members
                    boundary_row = comp_boundary[composition_id]; verified_row = comp_verified[composition_id]
                else:
                    boundary_row, verified_row = by_code[code], verified[code]
                assert row['voxels'] == boundary_row['sourceVoxels']
                review = component_review(sources['fine'] if members is not None else sources[level], row, members)
                selection = {'level': level, 'code': code, 'name': row['name'], 'compositionId': composition_id, 'fineMemberCodes': members, **review}
                output['selections'].append(selection)
                output['meshes'][f'{level}:{code}'] = mesh_expectation(row, boundary_row, verified_row, composition=level == 'composition')
                for component in review['foci']:
                    for contrast in (['T1', 'T2', 'WMn'] if component['component'] == 0 else ['T1']):
                        output['cases'].append({'level': level, 'code': code, 'component': component['component'], 'contrast': contrast, 'outline': False, 'overlay': True, 'focusSourceIJK': component['focusSourceIJK']})
                    if component['component'] == 0:
                        output['cases'].append({'level': level, 'code': code, 'component': 0, 'contrast': 'T1', 'outline': True, 'overlay': True, 'focusSourceIJK': component['focusSourceIJK']})
                print('Source selection', level, code, review['components26'], 'components validated', flush=True)
                gc.collect()
        # Process each original MRI contrast once. The selection is derived
        # directly from supplied coarse labels or the frozen fine membership.
        selections = {(s['level'], s['code']): s for s in output['selections']}
        for contrast in ['T1', 'T2', 'WMn']:
            image, output['sources'][contrast] = load_source(archive, contrast)
            low, high = expected_windows[contrast]
            for case in output['cases']:
                if case['contrast'] != contrast:
                    continue
                selection = selections[case['level'], case['code']]
                mask_source = sources['fine'] if case['level'] == 'composition' else sources[case['level']]
                for axis in range(3):
                    index = case['focusSourceIJK'][axis]
                    cut = [slice(None)] * 3; cut[axis] = index; cut = tuple(cut)
                    selected = np.isin(mask_source[cut], selection['fineMemberCodes']) if case['level'] == 'composition' else mask_source[cut] == case['code']
                    key = ':'.join(map(str, [case['level'], case['code'], case['component'], contrast, axis, int(case['outline'])]))
                    assert key not in output['pixels']
                    output['pixels'][key] = {'axis': axis, 'sourceIndex': index, 'sourceAxes': [a for a in range(3) if a != axis], **pixel_expectation(image[cut], selected, low, high, case['outline'])}
            print('Contrast oracle', contrast, 'cumulative plane cases', len(output['pixels']), flush=True)
            del image
            gc.collect()
    assert len(output['selections']) == len(output['meshes']) == 79
    assert len(output['pixels']) == 3 * len(output['cases'])
    counts = collections.Counter(c['level'] for c in output['cases'])
    output.update(allGenerated=True, checkedAtUTC=datetime.datetime.now(datetime.timezone.utc).isoformat(), counts={'selections': len(output['selections']), 'meshCases': len(output['meshes']), 'components26': sum(s['components26'] for s in output['selections']), 'viewCases': len(output['cases']), 'nativePlaneCases': len(output['pixels']), 'nativePixels': sum(p['pixels'] for p in output['pixels'].values()), 'outlinePlaneCases': 3 * sum(c['outline'] for c in output['cases']), 'viewCasesByLevel': dict(counts)})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    atomic_json(args.output, output)
    print(json.dumps(output['counts']), flush=True)


if __name__ == '__main__':
    main()
