#!/usr/bin/env python3
"""Independently replay schematic label rays against native Open Knee(s) meshes.

This checks rendering targets and records three local, unverified surface
candidates. It is not an anatomical approval, a tissue-boundary validation,
or evidence that an entire reporting component is represented accurately.
The renderer is not imported; triangle interpolation and ray depth are
recomputed here from the losslessly packaged native source geometry.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import struct

import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parents[2]
SOURCE_MANIFEST = 'web/anatomy/openknee-oks003/manifest.json'
SOURCE_MANIFEST_SHA = 'c2617979ffafc90349f57174a083bd42410c2ab9f601e49200353a328afafcd4'
PAIRED_REVIEW = 'docs/msk-openknee-source-review/paired-source-audit.json'
PAIRED_REVIEW_SHA = '5bd53e668563dbbd23b8a511caba9c0c6d1f0029658221d5e08b5caf0ea89fa0'
EXPECTED_LABELS = {
    'knee-patellar-cartilage-openknee.png': {
        'oks003-ptc': 'Patellar cartilage', 'oks003-ptb': 'Patella',
    },
    'knee-menisci-openknee.png': {
        'oks003-mns-m': 'Medial meniscus', 'oks003-mns-l': 'Lateral meniscus',
        'oks003-tbb': 'Tibia', 'oks003-fbb': 'Fibula',
    },
    'knee-tibial-cartilage-openknee.png': {
        'oks003-tbc-m': 'Medial tibial cartilage',
        'oks003-tbc-l': 'Lateral tibial cartilage',
        'oks003-tbb': 'Tibia', 'oks003-fbb': 'Fibula',
    },
}
CANDIDATES = {
    'oks003-ptc': ('knee.patellar_cartilage.articular_surface',
                   'knee-patellar-cartilage-openknee.png',
                   'a6230291cd1b827a76d178586ba05c47cae1ae88789eafc1aa7040e802f8cb1c'),
    'oks003-mns-m': ('knee.medial_meniscus.superior_surface',
                     'knee-menisci-openknee.png',
                     '41688fb9199f3faea34652e940558fa8ba2a9fb83293605e9db5f4c16acfa184'),
    'oks003-mns-l': ('knee.lateral_meniscus.superior_surface',
                     'knee-menisci-openknee.png',
                     'd8f2d4ab5b034de6f60cc10d3e1124c7dc784efdc6def39db3b8d62a45a93a65'),
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_mesh(part):
    path = ROOT / 'web' / part['file'].removeprefix('/app/')
    require(digest(path) == part['sha256'], 'Changed runtime mesh: ' + part['id'])
    raw = gzip.decompress(path.read_bytes())
    require(hashlib.sha256(raw).hexdigest() == part['decoded_sha256'],
            'Changed decoded mesh: ' + part['id'])
    magic, vertices, indices = struct.unpack_from('<4sII', raw)
    require(magic == b'BP3D' and vertices == indices == part['triangles'] * 3,
            'Unexpected native triangle protocol')
    require(len(raw) == 12 + vertices * 24 + indices * 4, 'Invalid buffer length')
    corners = np.frombuffer(raw, dtype='<f4', count=vertices * 3, offset=12)
    corners = corners.astype(float).reshape(-1, 3, 3)
    normals = np.frombuffer(raw, dtype='<f4', count=vertices * 3,
                            offset=12 + vertices * 12).astype(float).reshape(-1, 3, 3)
    order = np.frombuffer(raw, dtype='<u4', count=indices, offset=12 + vertices * 24)
    require(np.array_equal(order, np.arange(indices)), 'Non-native facet order')
    require(np.all(normals == normals[:, :1, :]), 'Unexpected interpolated normals')
    bounds = [corners.min(axis=(0, 1)).tolist(), corners.max(axis=(0, 1)).tolist()]
    require(bounds == part['bounds'], 'Changed native bounds')
    return corners, normals[:, 0, :]


def ray_hits(corners, right, up, eye, uv):
    """Find all triangle intersections on one orthographic ray, independently."""
    projected = np.stack([corners @ right, corners @ up], axis=-1)
    origin = projected[:, 0]
    edge_b, edge_c = projected[:, 1] - origin, projected[:, 2] - origin
    delta = uv - origin
    determinant = edge_b[:, 0] * edge_c[:, 1] - edge_b[:, 1] * edge_c[:, 0]
    nonzero = abs(determinant) > 1e-12
    weight_b = np.full(len(corners), np.nan)
    weight_c = np.full(len(corners), np.nan)
    weight_b[nonzero] = ((delta[nonzero, 0] * edge_c[nonzero, 1]
                         - delta[nonzero, 1] * edge_c[nonzero, 0])
                        / determinant[nonzero])
    weight_c[nonzero] = ((edge_b[nonzero, 0] * delta[nonzero, 1]
                         - edge_b[nonzero, 1] * delta[nonzero, 0])
                        / determinant[nonzero])
    weights = np.stack([1 - weight_b - weight_c, weight_b, weight_c], axis=-1)
    selected = np.flatnonzero(nonzero & np.all(weights >= -1e-8, axis=-1))
    depths = ((corners[selected] @ eye) * weights[selected]).sum(axis=-1)
    return selected, depths


def check_anchor(label, figure, meshes):
    camera = figure['camera']
    right, up, eye = (np.array(camera[key], dtype=float) for key in
                      ('screen_right', 'screen_up', 'eye_direction_from_target'))
    corners, normals = meshes[label['part_id']]
    index = label['source_triangle_index']
    require(0 <= index < len(corners), 'Label triangle outside source')
    weights = np.array(label['barycentric_weights'])
    require(np.min(weights) >= 0 and abs(weights.sum() - 1) < 1e-9,
            'Label point outside native triangle')
    point = weights @ corners[index]
    require(np.allclose(point, label['world_ras_mm'], rtol=0, atol=1e-7),
            'Native anchor differs from declared barycentric target')
    require(np.array_equal(normals[index], label['source_facet_normal_ras']),
            'Source facet normal changed')
    uv = np.array([point @ right, point @ up])
    pixel = np.array(camera['center_pixel']) + (
        uv - camera['center_uv_mm']) * [1, -1] * camera['pixels_per_mm']
    require(np.allclose(pixel, label['pixel_center'], rtol=0, atol=1e-7),
            'Pixel does not project to native target')
    hit_count, candidates = 0, []
    for part in figure['parts']:
        selected, depths = ray_hits(meshes[part['id']][0], right, up, eye, uv)
        hit_count += len(selected)
        if len(selected):
            nearest = depths.argmax()
            candidates.append((float(depths[nearest]), part['id'], int(selected[nearest])))
    require(bool(candidates), 'Label ray has no source intersection')
    front = max(candidates)
    require(front[1] == label['part_id'], 'Label target is occluded by another object')
    require(abs(front[0] - point @ eye) < 1e-7, 'Label is behind another source facet')
    require(float(normals[index] @ eye) > 0, 'Label target is back-facing')
    return {
        'label': label['text'], 'part_id': label['part_id'],
        'source_triangle_index': index, 'barycentric_weights': weights.tolist(),
        'native_ras_mm': point.tolist(), 'pixel_center': pixel.tolist(),
        'source_facet_normal_ras': normals[index].tolist(),
        'camera_facing_dot': float(normals[index] @ eye),
        'ray_intersections': hit_count, 'nearest_part': front[1],
        'nearest_triangle_index': front[2], 'nearest_depth_mm': front[0],
        'frontmost': True, 'position_error_mm': float(np.max(abs(point - label['world_ras_mm']))),
    }


def review(staging):
    evidence_path = staging / 'rendering-evidence.json'
    evidence = json.loads(evidence_path.read_text())
    manifest = json.loads((ROOT / SOURCE_MANIFEST).read_text())
    require(digest(ROOT / SOURCE_MANIFEST) == SOURCE_MANIFEST_SHA
            == evidence['source_manifest_sha256'], 'Source changed since bounded review')
    require(digest(ROOT / PAIRED_REVIEW) == PAIRED_REVIEW_SHA,
            'Paired review changed; independently re-inspect before using candidates')
    require(manifest['specimen']['side'] == 'left'
            and manifest['coordinate_system']['basis'] == 'RAS', 'Unexpected source frame')
    require({f['filename'] for f in evidence['figures']} == set(EXPECTED_LABELS),
            'Unexpected schematic scope')
    meshes, checked_figures = {}, []
    for figure in evidence['figures']:
        path = staging / figure['filename']
        require(digest(path) == figure['sha256'], 'PNG differs from rendering evidence')
        with Image.open(path) as image:
            require(image.format == 'PNG' and image.size == (figure['width'], figure['height']),
                    'PNG dimensions differ from evidence')
        require(figure['source_side'] == 'left' and figure['clinical_approval'] is False,
                'Misleading side or approval claim')
        require({label['part_id']: label['text'] for label in figure['labels']}
                == EXPECTED_LABELS[figure['filename']], 'Whole-object labels changed')
        posterior = figure['filename'] == 'knee-patellar-cartilage-openknee.png'
        camera = figure['camera']
        require(camera['screen_right'] == [1, 0, 0]
                and camera['screen_up'] == ([0, 0, 1] if posterior else [0, 1, 0])
                and camera['eye_direction_from_target'] == ([0, -1, 0] if posterior else [0, 0, 1]),
                'Camera no longer shows the reviewed posterior/superior native face')
        require(camera['screen_left_anatomy'] == 'lateral'
                and camera['screen_right_anatomy'] == 'medial', 'Left-side labels are reversed')
        source_parts = []
        for part in figure['parts']:
            native = manifest['parts'][part['id']]
            require(part['source_sha256'] == native['source_sha256']
                    and part['retained_triangles'] == native['triangles'], 'Changed source part')
            if part['id'] not in meshes:
                meshes[part['id']] = read_mesh(native)
            source_parts.append({key: native[key] for key in
                                 ('id', 'source_id', 'source_sha256', 'sha256',
                                  'decoded_sha256', 'triangles', 'file')})
        checked_figures.append({
            'filename': figure['filename'], 'sha256': figure['sha256'],
            'camera': camera, 'source_parts': source_parts,
            'anchors': [check_anchor(label, figure, meshes) for label in figure['labels']],
        })

    paired = json.loads((ROOT / PAIRED_REVIEW).read_text())
    pairs = {entry['id']: entry for entry in paired['structures']}
    proposed = []
    for part_id, (leaf, filename, sheet_sha) in CANDIDATES.items():
        native = manifest['parts'][part_id]
        pair = pairs[native['source_id']]
        require(pair['mesh_sha256'] == native['source_sha256'], 'Paired mesh changed')
        sheet = 'docs/msk-openknee-source-review/' + native['source_id'].lower() + '-source-planes.png'
        require(digest(ROOT / sheet) == sheet_sha, 'Visual source-review sheet changed')
        figure = next(f for f in checked_figures if f['filename'] == filename)
        anchor = next(a for a in figure['anchors'] if a['part_id'] == part_id)
        require(anchor['camera_facing_dot'] > .5, 'Candidate face is not clearly exposed')
        proposed.append({
            'source_part_id': part_id, 'requirement_leaf': leaf,
            'candidate_representations': ['interactive_model', 'source_derived_schematic'],
            'status': 'unverified_local_candidate', 'clinical_approval': False,
            'candidate_scope': 'Local visible posterior articular face' if part_id.endswith('ptc')
                               else 'Local visible superior meniscal face',
            'source_mesh_sha256': native['source_sha256'],
            'source_mask_filename': pair['mask']['filename'],
            'source_mask_sha256': pair['mask']['sha256'],
            'paired_review_sheet': sheet, 'paired_review_sheet_sha256': sheet_sha,
            'paired_source_planes': pair['planes'],
            'schematic_filename': filename, 'schematic_sha256': figure['sha256'],
            'anchor': anchor,
            'basis': 'Visual source-MRI tissue location and source-label/mesh contours, '
                     'unchanged native geometry, and independently verified exposed label ray.',
            'limits': 'Sampled source planes are not the exact label-anchor planes or a complete '
                      'boundary audit. No clinical accuracy, whole-surface extent, thickness, '
                      'subchondral interface, horns, roots or attachment approval. The model '
                      'and its derived schematic share one source; they are not independent '
                      'anatomical validation. Single left cadaver; no contralateral inheritance.',
        })
    return {
        'status': 'passed_technical_anchor_checks_only', 'clinical_approval': False,
        'checker': {'path': str(Path(__file__).relative_to(ROOT)), 'sha256': digest(Path(__file__)),
                    'numpy': np.__version__},
        'source_manifest': {'path': SOURCE_MANIFEST, 'sha256': SOURCE_MANIFEST_SHA},
        'rendering_evidence': {'path': str(evidence_path), 'sha256': digest(evidence_path)},
        'paired_review': {'path': PAIRED_REVIEW, 'sha256': PAIRED_REVIEW_SHA,
                          'source_images': paired['images']},
        'coordinate_frame': 'Unchanged native RAS millimeters, left specimen oks003',
        'independent_method': 'Decode exact BP3D corners and facet normals; reconstruct source '
                              'triangle anchors from barycentric weights; independently intersect '
                              'each orthographic ray with every displayed triangle; verify nearest '
                              'face, projection and source-normal direction. No renderer import.',
        'figures': checked_figures, 'proposed_local_candidates': proposed,
        'unbound_source_parts': {
            'oks003-tbc-l': 'Selected _02 mask revision lineage unresolved; no tissue-boundary approval.',
            'oks003-tbc-m': 'Selected _02 mask revision lineage unresolved; no tissue-boundary approval.',
            'oks003-ptb': 'Context only; no marrow, cortical thickness, facet or ridge binding.',
            'oks003-tbb': 'Context only; no bone subcomponent binding.',
            'oks003-fbb': 'Context only; no bone subcomponent binding.',
        },
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--staging', type=Path,
                        default=Path('/tmp/primer-msk-sources/openknee-schematics'))
    args = parser.parse_args()
    report = review(args.staging.resolve())
    output = args.staging / 'independent-anchor-review.json'
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + '\n')
    print(json.dumps({'status': report['status'], 'figures': len(report['figures']),
                      'anchors': sum(len(f['anchors']) for f in report['figures']),
                      'local_unverified_candidates': len(report['proposed_local_candidates']),
                      'output': str(output)}))


if __name__ == '__main__':
    main()
