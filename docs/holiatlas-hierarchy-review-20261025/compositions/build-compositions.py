"""Offline exact exposed-cell meshes for explicit holiAtlas source unions.

Uses only the original source NIfTI and reviewed memberships. No smoothing,
meshing repair, interpolation, voxel relabelling or component deletion.
"""
from __future__ import annotations
import argparse
import datetime
import gc
import gzip
import hashlib
import io
import json
from pathlib import Path
import struct
import time
import zipfile

import nibabel as nib
import numpy as np
from scipy import ndimage

HERE = Path(__file__).resolve().parent
WORKTREE = HERE.parents[2]
SOURCE_DEFAULT = WORKTREE.parent / 'fidelity-next-20261023/.research/brain-source-followup/atlas_v1.0.zip'
EXPECTED_SOURCE = '6d34608fd32ecb04eda638e7877cc90f903cb7edf16d7fbf84e1b8819c8ae7d8'
EXPECTED_ARCHIVE = '6932bc8063568f0037627d5b85199ff6142b4457413f8fef8817871a3ffa1ee5'
sha = lambda b: hashlib.sha256(b).hexdigest()


def atomic_json(path, obj):
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + '\n')
    tmp.replace(path)


def write_payload(out, name, data):
    compressed = gzip.compress(data, mtime=0)
    (out / name).write_bytes(compressed)
    return {'file': name, 'bytes': len(data), 'gzipBytes': len(compressed), 'sha256': sha(data), 'gzipSHA256': sha(compressed)}


def components(mask, origin, affine):
    result, size_map = [], {}
    for connectivity, label in [(1, '6'), (2, '18'), (3, '26')]:
        cc, count = ndimage.label(mask, ndimage.generate_binary_structure(3, connectivity))
        sizes = np.bincount(cc.ravel())[1:]
        size_map[label] = sorted(sizes.tolist(), reverse=True)
        if connectivity != 3:
            continue
        for code, bounds in enumerate(ndimage.find_objects(cc), 1):
            points = np.argwhere(cc[bounds] == code) + np.array([s.start for s in bounds])
            centroid = points.mean(0)
            focus = points[np.argmin(np.sum((points - centroid) ** 2, axis=1))] + origin
            assert mask[tuple(focus - origin)]
            result.append({'id': code, 'voxels': len(points), 'focusSourceIJK': focus.tolist(), 'focusSourceWorld': (affine @ np.r_[focus, 1])[:3].tolist()})
    result.sort(key=lambda x: (-x['voxels'], x['id']))
    return size_map, result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-archive', type=Path, default=SOURCE_DEFAULT)
    parser.add_argument('--compositions', type=Path, default=HERE.parent / 'proposed-source-compositions.json')
    parser.add_argument('--output', type=Path, default=HERE)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    specs_raw = args.compositions.read_bytes()
    specs = json.loads(specs_raw)['compositions']
    assert len(specs) == 16 and len({tuple(sorted(s['fine_codes'])) for s in specs}) == 16
    archive_sha = sha(args.source_archive.read_bytes())
    assert archive_sha == EXPECTED_ARCHIVE
    with zipfile.ZipFile(args.source_archive) as z:
        source = gzip.decompress(z.read('substructure_atlas.nii.gz'))
    assert sha(source) == EXPECTED_SOURCE
    header = nib.Nifti1Header.from_fileobj(io.BytesIO(source[:352]))
    data = np.frombuffer(source, offset=int(header['vox_offset']), dtype=header.get_data_dtype()).reshape(header.get_data_shape(), order='F')
    affine = header.get_sform()
    assert np.array_equal(affine, header.get_qform())
    assert np.array_equal(affine, np.array([[.5, 0, 0, -90], [0, .5, 0, -126], [0, 0, .5, -72], [0, 0, 0, 1]]))
    assert header.get_xyzt_units()[0] == 'mm'
    assert float(header['scl_slope']) == 1.0 and float(header['scl_inter']) == 0.0
    labels = data.astype(np.uint16)
    assert np.array_equal(labels.astype(data.dtype).view(np.uint32), data.view(np.uint32))
    boxes = ndimage.find_objects(labels)
    counts = np.bincount(labels.ravel())
    proof = {
        'scope': 'Exact source-label unions, not new clinical anatomical delineations.',
        'source': 'https://zenodo.org/records/15690524',
        'sourceArchiveSHA256': archive_sha, 'sourceMember': 'substructure_atlas.nii.gz',
        'sourceLabelSHA256': EXPECTED_SOURCE, 'sourceAffine': affine.tolist(),
        'sourceGridShape': list(data.shape), 'sourceHeaderUnits': list(header.get_xyzt_units()),
        'compositionSpecificationSHA256': sha(specs_raw), 'generatorSHA256': sha(Path(__file__).read_bytes()),
        'meshMethod': 'Every exposed 0.5 mm source-cell face; outward triangles; no smoothing, filling, repairs or component deletion.',
        'clinicalApproval': False, 'runtimeBound': False, 'sourceCompositions': len(specs),
        'allPassed': False, 'rows': [],
    }
    atomic_json(args.output / 'boundary-proof.json', proof)
    for spec in specs:
        started = time.monotonic()
        members = sorted(spec['fine_codes'])
        assert all(counts[c] > 0 for c in members) and len(members) == len(set(members))
        origin = np.min([[x.start for x in boxes[c - 1]] for c in members], axis=0)
        end = np.max([[x.stop for x in boxes[c - 1]] for c in members], axis=0)
        crop = tuple(slice(int(a), int(b)) for a, b in zip(origin, end))
        mask = np.isin(labels[crop], members)
        n = int(mask.sum())
        assert n == spec['source_voxels'] == sum(int(counts[c]) for c in members)
        records, pairs = [], 0
        for axis in range(3):
            left = [slice(None)] * 3; right = left.copy()
            left[axis] = slice(None, -1); right[axis] = slice(1, None)
            pairs += int(np.count_nonzero(mask[tuple(left)] & mask[tuple(right)]))
            for sign in [-1, 1]:
                other = np.zeros_like(mask)
                target = [slice(None)] * 3; neighbor = target.copy()
                target[axis] = slice(None, -1) if sign == 1 else slice(1, None)
                neighbor[axis] = slice(1, None) if sign == 1 else slice(None, -1)
                other[tuple(target)] = mask[tuple(neighbor)]
                cells = np.argwhere(mask & ~other).astype(np.int16) + origin
                records.append(np.column_stack([cells, np.full(len(cells), axis), np.full(len(cells), sign)]).astype('<i2'))
        records = np.concatenate(records)
        f = len(records)
        assert f == 6 * n - 2 * pairs and len(np.unique(records, axis=0)) == f
        cell = records[:, :3].astype(np.int32)
        assert np.all(np.isin(data[tuple(cell.T)], members))
        neighbor = cell.copy(); neighbor[np.arange(f), records[:, 3]] += records[:, 4]
        inside = np.all((neighbor >= 0) & (neighbor < np.array(data.shape)), axis=1)
        assert not np.any(np.isin(data[tuple(neighbor[inside].T)], members))
        corners = np.repeat((2 * cell)[:, None, :], 4, axis=1)
        for axis in range(3):
            use = records[:, 3] == axis; others = [i for i in range(3) if i != axis]
            corners[use, :, axis] += records[use, 4, None]
            for j, (u, v) in enumerate([(-1, -1), (1, -1), (1, 1), (-1, 1)]):
                corners[use, j, others[0]] += u; corners[use, j, others[1]] += v
        vertices, inverse = np.unique(corners.reshape(-1, 3), axis=0, return_inverse=True)
        quads = inverse.reshape(-1, 4)
        positions = (vertices * .25 + affine[:3, 3]).astype('<f4')
        quad = positions[quads].astype(np.float64)
        normal = np.cross(quad[:, 1] - quad[:, 0], quad[:, 2] - quad[:, 0])
        expected = np.eye(3)[records[:, 3]] * records[:, 4, None] * .25
        flip = np.sum(normal * expected, axis=1) < 0
        quads[flip] = quads[flip][:, [0, 3, 2, 1]]
        triangles = np.stack([quads[:, [0, 1, 2]], quads[:, [0, 2, 3]]], axis=1).reshape(-1, 3).astype('<u4')
        xyz = positions[triangles].astype(np.float64)
        normal = np.cross(xyz[:, 1] - xyz[:, 0], xyz[:, 2] - xyz[:, 0])
        assert np.array_equal(normal, np.repeat(expected, 2, axis=0))
        volume = float(np.einsum('ij,ij->i', xyz[:, 0], np.cross(xyz[:, 1], xyz[:, 2])).sum() / 6)
        assert volume == n * .125
        size_map, foci = components(mask, origin, affine)
        assert sum(x['voxels'] for x in foci) == n
        for x in foci:
            assert int(data[tuple(x['focusSourceIJK'])]) in members
        mesh = struct.pack('<4sIII', b'HVX1', len(positions), len(triangles), 0) + positions.tobytes() + triangles.tobytes()
        mesh_info = write_payload(args.output, spec['id'] + '.mesh.gz', mesh)
        faces_info = write_payload(args.output, spec['id'] + '-faces.bin.gz', records.tobytes())
        proof['rows'].append({
            'id': spec['id'], 'displayName': spec['display_name'], 'sourceMemberCodes': members,
            'sourceMemberNames': [dict(zip(spec['fine_codes'], spec['source_names']))[c] for c in members],
            'sourceVoxelsByMember': {str(c): int(counts[c]) for c in members}, 'sourceVoxels': n,
            'sourceVolumeMM3': n * .125, 'signedEnclosedVolumeMM3': volume,
            'vertices': len(positions), 'faces': f, 'triangles': len(triangles),
            'boundsSourceWorld': [positions.min(0).tolist(), positions.max(0).tolist()],
            'boundsSourceIJK': [origin.tolist(), (end - 1).tolist()],
            'componentsByConnectivity': size_map, 'components26': foci,
            'focusSourceIJK': foci[0]['focusSourceIJK'], 'focusSourceWorld': foci[0]['focusSourceWorld'],
            'mesh': mesh_info, 'facesPayload': faces_info,
            'everyFaceSourceValidAndUnique': True, 'faceCountEqualsSixVoxelsMinusTwiceAdjacentPairs': True,
            'everyTriangleAreaMM2': .125, 'everyTriangleWindsOutward': True,
            'allComponentsAndCavitiesRetained': True,
            'extentDefinition': spec['display_name'], 'remainingLimit': spec['remaining_limit'],
            'clinicalRequirementComplete': False, 'seconds': round(time.monotonic() - started, 2),
        })
        atomic_json(args.output / 'boundary-proof.json', proof)
        print(spec['id'], 'voxels', n, 'faces', f, 'components26', len(foci), flush=True)
        del mask, records, corners, vertices, inverse, quads, positions, triangles, xyz, quad, normal, expected, mesh
        gc.collect()
    proof.update(allPassed=True, totalTriangles=sum(r['triangles'] for r in proof['rows']), totalFaces=sum(r['faces'] for r in proof['rows']), totalComponents26=sum(len(r['components26']) for r in proof['rows']), completedAtUTC=datetime.datetime.now(datetime.timezone.utc).isoformat())
    atomic_json(args.output / 'boundary-proof.json', proof)
    print(json.dumps({k: proof[k] for k in ['allPassed', 'sourceCompositions', 'totalTriangles', 'totalFaces', 'totalComponents26']}), flush=True)


if __name__ == '__main__':
    main()
