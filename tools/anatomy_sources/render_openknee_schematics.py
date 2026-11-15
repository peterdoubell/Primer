#!/usr/bin/env python3
"""Render unchanged Open Knee(s) source surfaces with per-pixel depth testing.

Outputs are staged for review only. No MRI pixels, geometry fitting, smoothing,
subdivision labels, or clinical approvals are generated. Requires NumPy, Pillow,
and Matplotlib (only to locate its bundled, fingerprinted DejaVu fonts).
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct

import numpy as np
from PIL import Image, ImageDraw, ImageFont, __version__ as PILLOW_VERSION

ROOT = Path(__file__).resolve().parents[2]
SOURCE = Path('/tmp/primer-msk-sources/openknee-public-pass/oks003-native')
OUTPUT = Path('/tmp/primer-msk-sources/openknee-schematics')
SIZE = (3200, 2280)
VIEWPORT = (610, 380, 2590, 1620)
COLORS = {
    'oks003-ptb': '#cdc8bb', 'oks003-tbb': '#d3cfc4', 'oks003-fbb': '#bbb7ac',
    'oks003-ptc': '#419ab0', 'oks003-mns-m': '#c4873d', 'oks003-mns-l': '#8266b3',
    'oks003-tbc-m': '#419ab0', 'oks003-tbc-l': '#67aa96',
}
VIEWS = [
    {
        'filename': 'knee-patellar-cartilage-openknee.png',
        'figure_title': 'Patella and patellar cartilage', 'view_name': 'Posterior view',
        'parts': ['oks003-ptb', 'oks003-ptc'],
        'right': [1, 0, 0], 'up': [0, 0, 1], 'toward_camera': [0, -1, 0],
        'screen_top': 'Superior (+Z)', 'scale_mm': 10,
        'labels': [
            {'part': 'oks003-ptc', 'text': 'Patellar\ncartilage', 'preferred_uv': [14, 10], 'side': 'right', 'y': 820},
            {'part': 'oks003-ptb', 'text': 'Patella', 'preferred_uv': [-10, -13], 'side': 'left', 'y': 1270},
        ],
        'omitted_context': 'Femur and all other structures omitted to expose the posterior cartilage surface.',
        'specific_limit': 'Whole cartilage object only; no separate cartilage layers, thickness measurement or interface validation.',
    },
    {
        'filename': 'knee-menisci-openknee.png',
        'figure_title': 'Medial and lateral menisci', 'view_name': 'Superior anatomical view',
        'parts': ['oks003-tbb', 'oks003-fbb', 'oks003-mns-m', 'oks003-mns-l'],
        'right': [1, 0, 0], 'up': [0, 1, 0], 'toward_camera': [0, 0, 1],
        'screen_top': 'Anterior (+Y)', 'scale_mm': 20,
        'labels': [
            {'part': 'oks003-mns-l', 'text': 'Lateral\nmeniscus', 'preferred_uv': [-31, 2], 'side': 'left', 'y': 730},
            {'part': 'oks003-mns-m', 'text': 'Medial\nmeniscus', 'preferred_uv': [26, 1], 'side': 'right', 'y': 700},
            {'part': 'oks003-fbb', 'text': 'Fibula', 'preferred_uv': [-44, -15], 'side': 'left', 'y': 1390},
            {'part': 'oks003-tbb', 'text': 'Tibia', 'preferred_uv': [0, 20], 'side': 'right', 'y': 370},
        ],
        'omitted_context': 'Femur, cartilage and ligaments omitted; tibia and fibula remain in unchanged native coordinates.',
        'specific_limit': 'Whole menisci only; roots, horns and capsular/meniscotibial attachments are not separately delineated.',
    },
    {
        'filename': 'knee-tibial-cartilage-openknee.png',
        'figure_title': 'Medial and lateral tibial cartilage', 'view_name': 'Superior anatomical view',
        'parts': ['oks003-tbb', 'oks003-fbb', 'oks003-tbc-m', 'oks003-tbc-l'],
        'right': [1, 0, 0], 'up': [0, 1, 0], 'toward_camera': [0, 0, 1],
        'screen_top': 'Anterior (+Y)', 'scale_mm': 20,
        'labels': [
            {'part': 'oks003-tbc-l', 'text': 'Lateral tibial\ncartilage', 'preferred_uv': [-25, -3], 'side': 'left', 'y': 730},
            {'part': 'oks003-tbc-m', 'text': 'Medial tibial\ncartilage', 'preferred_uv': [18, -3], 'side': 'right', 'y': 700},
            {'part': 'oks003-fbb', 'text': 'Fibula', 'preferred_uv': [-44, -15], 'side': 'left', 'y': 1390},
            {'part': 'oks003-tbb', 'text': 'Tibia', 'preferred_uv': [0, 20], 'side': 'right', 'y': 370},
        ],
        'omitted_context': 'Femur and menisci omitted to expose both source-labelled cartilage objects; no source geometry moved.',
        'specific_limit': 'Tibial-cartilage mask versions remain unresolved; no independent tissue-boundary or thickness validation.',
    },
]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def camera_basis(right, up, toward_camera):
    basis = np.array([right, up, toward_camera], dtype=np.float64)
    if not np.allclose(basis @ basis.T, np.eye(3), atol=1e-12) or not np.isclose(np.linalg.det(basis), 1):
        raise ValueError('Camera must use an orthonormal right-handed basis')
    return basis


def read_part(source, part):
    raw = (source / part['source_name']).read_bytes()
    if sha(raw) != part['source_sha256']:
        raise ValueError('Changed native source: ' + part['id'])
    count = struct.unpack_from('<I', raw, 80)[0]
    if count != part['triangles'] or len(raw) != 84 + count * 50:
        raise ValueError('Unexpected original binary STL')
    dtype = np.dtype([('normal', '<f4', (3,)), ('vertex', '<f4', (3, 3)), ('attribute', '<u2')])
    rows = np.frombuffer(raw, dtype, count=count, offset=84)
    tri = rows['vertex'].astype(np.float64)
    normals = rows['normal'].astype(np.float64)
    if not np.isfinite(tri).all() or not np.isfinite(normals).all():
        raise ValueError('Nonfinite source geometry')
    return {'id': part['id'], 'triangles': tri, 'normals': normals,
            'color': COLORS[part['id']], 'source': part}


def projection_for(meshes, basis, viewport=VIEWPORT):
    points = np.concatenate([mesh['triangles'].reshape(-1, 3) @ basis.T for mesh in meshes])
    lower, upper = points[:, :2].min(0), points[:, :2].max(0)
    x0, y0, x1, y1 = viewport
    scale = .92 * min((x1 - x0) / (upper[0] - lower[0]), (y1 - y0) / (upper[1] - lower[1]))
    center = (lower + upper) / 2
    return {'pixels_per_mm': float(scale), 'center_uv_mm': center.tolist(),
            'center_pixel': [(x0 + x1) / 2, (y0 + y1) / 2],
            'native_uv_bounds_mm': [lower.tolist(), upper.tolist()], 'viewport_pixels': list(viewport)}


def project(triangles, basis, projection):
    result = triangles @ basis.T
    center = projection['center_uv_mm']
    pixels = projection['center_pixel']
    result[..., 0] = pixels[0] + (result[..., 0] - center[0]) * projection['pixels_per_mm']
    result[..., 1] = pixels[1] - (result[..., 1] - center[1]) * projection['pixels_per_mm']
    return result


def rasterize(meshes, basis, projection, size=SIZE):
    """Opaque global z-buffer; canonical primitive IDs resolve exact depth ties."""
    width, height = size
    depth = np.full((height, width), -np.inf, dtype=np.float64)
    owner = np.full((height, width), -1, dtype=np.int16)
    primitive = np.full((height, width), np.iinfo(np.int32).max, dtype=np.int32)
    rgb = np.full((height, width, 3), 255, dtype=np.uint8)
    ordered = sorted(meshes, key=lambda mesh: mesh['id'])
    records, offset = [], 0
    light = np.array([-.25, .45, 1.0]); light /= np.linalg.norm(light)
    for part_index, mesh in enumerate(ordered):
        tri = project(mesh['triangles'], basis, projection)
        normals = mesh['normals'] @ basis.T
        lengths = np.linalg.norm(normals, axis=1)
        unit = np.divide(normals, lengths[:, None], out=np.zeros_like(normals), where=lengths[:, None] > 0)
        # Source facet normals only; no vertex-normal interpolation or smoothing.
        brightness = .62 + .38 * np.clip(unit @ light, 0, 1)
        base = np.array([int(mesh['color'][i:i + 2], 16) for i in (1, 3, 5)])
        shades = np.rint(base[None, :] * brightness[:, None]).astype(np.uint8)
        degenerate, outside, sampled = 0, 0, 0
        for triangle_index, t in enumerate(tri):
            a, b, c = t
            denominator = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
            if abs(denominator) < 1e-12:
                degenerate += 1
                continue
            xmin = max(0, int(np.ceil(t[:, 0].min() - .5)))
            xmax = min(width - 1, int(np.floor(t[:, 0].max() - .5)))
            ymin = max(0, int(np.ceil(t[:, 1].min() - .5)))
            ymax = min(height - 1, int(np.floor(t[:, 1].max() - .5)))
            if xmin > xmax or ymin > ymax:
                outside += 1
                continue
            xx = np.arange(xmin, xmax + 1)[None, :] + .5
            yy = np.arange(ymin, ymax + 1)[:, None] + .5
            w0 = ((b[1] - c[1]) * (xx - c[0]) + (c[0] - b[0]) * (yy - c[1])) / denominator
            w1 = ((c[1] - a[1]) * (xx - c[0]) + (a[0] - c[0]) * (yy - c[1])) / denominator
            w2 = 1 - w0 - w1
            inside = (w0 >= -1e-10) & (w1 >= -1e-10) & (w2 >= -1e-10)
            if not inside.any():
                continue
            sampled += 1
            z = w0 * a[2] + w1 * b[2] + w2 * c[2]
            old = depth[ymin:ymax + 1, xmin:xmax + 1]
            old_id = primitive[ymin:ymax + 1, xmin:xmax + 1]
            pid = offset + triangle_index
            visible = inside & ((z > old + 1e-9) | ((np.abs(z - old) <= 1e-9) & (pid < old_id)))
            old[visible] = z[visible]
            old_id[visible] = pid
            owner[ymin:ymax + 1, xmin:xmax + 1][visible] = part_index
            rgb[ymin:ymax + 1, xmin:xmax + 1][visible] = shades[triangle_index]
        records.append({'id': mesh['id'], 'primitive_offset': offset,
                        'submitted_triangles': len(tri), 'projected_zero_area_triangles': degenerate,
                        'off_pixel_grid_triangles': outside, 'triangles_with_pixel_samples': sampled})
        offset += len(tri)
    for index, row in enumerate(records):
        mask = owner == index
        row['visible_pixels'] = int(mask.sum())
        row['visible_source_triangles'] = int(len(np.unique(primitive[mask])))
    return rgb, depth, owner, primitive, ordered, records


def visible_anchor(label, meshes, raster, basis, projection):
    _, depth, owner, primitive, ordered, stats = raster
    index = next(i for i, mesh in enumerate(ordered) if mesh['id'] == label['part'])
    rows, columns = np.nonzero(owner == index)
    if not len(rows):
        raise ValueError('Cannot label an occluded object: ' + label['part'])
    pref = np.array(label['preferred_uv'])
    scale = projection['pixels_per_mm']
    uv = np.stack([projection['center_uv_mm'][0] + (columns + .5 - projection['center_pixel'][0]) / scale,
                   projection['center_uv_mm'][1] - (rows + .5 - projection['center_pixel'][1]) / scale], axis=1)
    selected = int(np.argmin(((uv - pref) ** 2).sum(axis=1)))
    x, y = int(columns[selected]), int(rows[selected])
    triangle_index = int(primitive[y, x] - stats[index]['primitive_offset'])
    source_triangle = ordered[index]['triangles'][triangle_index]
    t = project(source_triangle, basis, projection)
    a, b, c = t
    denominator = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
    w0 = ((b[1] - c[1]) * (x + .5 - c[0]) + (c[0] - b[0]) * (y + .5 - c[1])) / denominator
    w1 = ((c[1] - a[1]) * (x + .5 - c[0]) + (a[0] - c[0]) * (y + .5 - c[1])) / denominator
    weights = np.array([w0, w1, 1 - w0 - w1])
    world = weights @ source_triangle
    if weights.min() < -1e-9 or not np.isclose(world @ basis[2], depth[y, x], atol=1e-8):
        raise ValueError('Label anchor does not lie on the visible source triangle')
    return {'part_id': label['part'], 'text': label['text'].replace('\n', ' '),
            'source_triangle_index': triangle_index, 'barycentric_weights': weights.tolist(),
            'world_ras_mm': world.tolist(), 'pixel_center': [x + .5, y + .5],
            'source_facet_normal_ras': ordered[index]['normals'][triangle_index].tolist(),
            'source_facet_normal_camera': (ordered[index]['normals'][triangle_index] @ basis.T).tolist(),
            'preferred_native_uv_mm': label['preferred_uv'], 'visibility': 'frontmost part at this pixel'}


def fonts():
    import matplotlib
    directory = Path(matplotlib.get_data_path()) / 'fonts/ttf'
    regular, bold = directory / 'DejaVuSans.ttf', directory / 'DejaVuSans-Bold.ttf'
    return regular, bold, {'regular_sha256': sha(regular.read_bytes()), 'bold_sha256': sha(bold.read_bytes())}


def annotate(raster, meshes, basis, projection, view, font_paths):
    regular, bold, _ = font_paths
    image = Image.fromarray(raster[0], 'RGB')
    draw = ImageDraw.Draw(image)
    def font(size, strong=False):
        return ImageFont.truetype(str(bold if strong else regular), size)
    ink, gray = '#182731', '#53636c'
    draw.text((96, 62), view['figure_title'], font=font(86, True), fill=ink)
    draw.text((100, 181), 'LEFT KNEE  ·  ' + view['view_name'].upper() + '  ·  Open Knee(s) oks003',
              font=font(43, True), fill=gray)
    draw.text((100, 256), 'Screen left: lateral (−X)   |   right: medial (+X)   |   top: ' + view['screen_top'],
              font=font(36), fill=gray)
    anchors = []
    for label in view['labels']:
        anchor = visible_anchor(label, meshes, raster, basis, projection)
        y = label['y']; lines = label['text'].split('\n')
        x = 96 if label['side'] == 'left' else 2670
        for line_index, line in enumerate(lines):
            draw.text((x, y + line_index * 67), line, font=font(52, True), fill=ink)
        leader_y = y + len(lines) * 67 + 16
        start = (560, leader_y) if label['side'] == 'left' else (2640, leader_y)
        elbow = (590, leader_y) if label['side'] == 'left' else (2610, leader_y)
        target = tuple(anchor['pixel_center'])
        draw.line([start, elbow, target], fill=gray, width=4, joint='curve')
        draw.ellipse((target[0] - 8, target[1] - 8, target[0] + 8, target[1] + 8),
                     fill=COLORS[label['part']], outline=ink, width=2)
        anchor['label_origin_pixels'] = [x, y]
        anchor['leader_polyline_pixels'] = [list(start), list(elbow), list(target)]
        anchors.append(anchor)
    length = view['scale_mm'] * projection['pixels_per_mm']
    start = (690, 1720); end = (start[0] + length, start[1])
    draw.line([start, end], fill=ink, width=7)
    for x in (start[0], end[0]):
        draw.line([(x, start[1] - 13), (x, start[1] + 13)], fill=ink, width=5)
    text = str(view['scale_mm']) + ' mm'
    width = draw.textlength(text, font=font(36))
    draw.text(((start[0] + end[0] - width) / 2, 1740), text, fill=ink, font=font(36))
    draw.text((1970, 1715), 'Source-derived anatomical schematic', fill=gray, font=font(33))
    draw.line([(96, 1830), (3104, 1830)], fill='#d5dce0', width=3)
    lines = [
        ('Single 25-year-old female cadaveric reference. Author-processed surfaces; not a clinical image or validated measurement.', 36),
        (view['specific_limit'], 36),
        ('View selection: ' + view['omitted_context'], 32),
        ('Source MRI grids: 0.5 mm isotropic and ~0.35 × 0.35 × 0.7 mm. Render resolution adds no anatomical detail.', 36),
        ('Source: Open Knee(s) Development Team — Chokhandre, Schwartz, Klonowski, Landis & Erdemir (2022/2023).', 32),
        ('doi:10.1007/s10439-022-03074-0  ·  Source revision 3413, oks003 AGS assembly.', 32),
        ('Rendering, colours and labels added; geometry unchanged. CC BY-SA 3.0 Unported — creativecommons.org/licenses/by-sa/3.0/', 32),
    ]
    for index, (text, size) in enumerate(lines):
        if draw.textlength(text, font=font(size)) > 3008:
            raise ValueError('Caption exceeds fixed layout width')
        draw.text((100, 1870 + index * 56), text, fill=gray, font=font(size))
    return image, anchors, {'length_mm': view['scale_mm'], 'line_pixels': [list(start), list(end)],
                            'pixels_per_mm': projection['pixels_per_mm']}


def render_all(source=SOURCE, output=OUTPUT, manifest_path=None):
    manifest_path = manifest_path or ROOT / 'web/anatomy/openknee-oks003/manifest.json'
    manifest_raw = manifest_path.read_bytes(); manifest = json.loads(manifest_raw)
    if (manifest['provider'] != 'openknee-oks003' or manifest['coordinate_system']['basis'] != 'RAS'
            or manifest['coordinate_system']['units'] != 'millimeters'
            or manifest['regions']['knee']['side'] != 'left'
            or manifest['license'] != 'CC BY-SA 3.0 Unported'):
        raise ValueError('Unreviewed source frame, side or license')
    if output.resolve().is_relative_to((ROOT / 'web').resolve()):
        raise ValueError('Stage figures for review before publishing')
    output.mkdir(parents=True, exist_ok=True)
    needed = sorted({identifier for view in VIEWS for identifier in view['parts']})
    loaded = {identifier: read_part(source, manifest['parts'][identifier]) for identifier in needed}
    font_paths = fonts()
    evidence = {
        'schema_version': 1, 'status': 'source-derived schematic; clinical approval pending',
        'source_manifest_sha256': sha(manifest_raw),
        'source_manifest_path': str(manifest_path.relative_to(ROOT)),
        'source_dataset': manifest['dataset'], 'source_provider': manifest['provider'],
        'source_url': manifest['source_url'], 'source_assembly': manifest['source_assembly'],
        'license': manifest['license'], 'license_url': manifest['license_url'],
        'attribution': manifest['attribution'],
        'derived_figure_license': 'CC BY-SA 3.0 Unported',
        'renderer': {'script_sha256': sha(Path(__file__).read_bytes()), 'numpy': np.__version__,
                     'pillow': PILLOW_VERSION, 'fonts': font_paths[2],
                     'raster_size_pixels': list(SIZE), 'background': '#ffffff',
                     'depth_test': 'largest camera-depth coordinate per pixel across all source parts',
                     'tie_rule': 'within 1e-9 mm, smallest canonical source primitive ID wins',
                     'fragment_samples': 'one exact triangle interpolation at each pixel center',
                     'shading': 'source facet normals, directional diffuse plus ambient; no normal smoothing',
                     'geometry_changed': False, 'fitted_transform': False, 'raw_mri_pixels_used': False},
        'figures': [],
    }
    for view in VIEWS:
        meshes = [loaded[identifier] for identifier in view['parts']]
        basis = camera_basis(view['right'], view['up'], view['toward_camera'])
        projection = projection_for(meshes, basis)
        raster = rasterize(meshes, basis, projection)
        image, anchors, scale = annotate(raster, meshes, basis, projection, view, font_paths)
        path = output / view['filename']
        image.save(path, format='PNG', compress_level=9, dpi=(200, 200))
        stats = {r['id']: r for r in raster[5]}
        parts = []
        for mesh in meshes:
            part = mesh['source']
            parts.append({'id': mesh['id'], 'source_name': part['source_name'],
                          'source_url': part['source_url'], 'source_sha256': part['source_sha256'],
                          'triangles': part['triangles'], 'retained_triangles': len(mesh['triangles']),
                          'source_corner_count': int(mesh['triangles'].size // 3),
                          'source_unique_positions': len(np.unique(mesh['triangles'].reshape(-1, 3), axis=0)),
                          'source_positions_and_facet_normals_retained': True,
                          'raster_visibility': stats[mesh['id']], 'display_color': mesh['color']})
        record = {
            'filename': path.name, 'sha256': sha(path.read_bytes()), 'bytes': path.stat().st_size,
            'width': SIZE[0], 'height': SIZE[1], 'figure_title': view['figure_title'],
            'origin': 'source-derived', 'kind': 'schematic', 'source_side': 'left',
            'parts': parts,
            'camera': {'projection': 'orthographic', 'native_basis': 'RAS', 'units': 'millimeters',
                       'screen_right': view['right'], 'screen_up': view['up'],
                       'eye_direction_from_target': view['toward_camera'],
                       'view_direction': (-basis[2]).tolist(), 'view_name': view['view_name'],
                       'screen_left_anatomy': 'lateral', 'screen_right_anatomy': 'medial',
                       'screen_top_anatomy': view['screen_top'], **projection},
            'labels': anchors, 'scale_bar': scale,
            'omitted_context': view['omitted_context'],
            'source_limits': [view['specific_limit'],
                              'Only named whole-source objects are labelled; no anatomical subdivisions are invented.',
                              'Source surfaces were smoothed/remeshed; render pixels are not acquisition resolution.',
                              'Single cadaveric left knee; no universal normality or independent clinical approval.'],
            'output_limits': ['All selected source facets are submitted unchanged; occluded/edge-on facets do not produce visible pixels.',
                              'No transparency or exploded anatomy; opaque per-pixel occlusion is retained.',
                              'Scale bar measures source geometry, not independently validated clinical measurement accuracy.'],
            'clinical_approval': False,
        }
        if view['filename'] == 'knee-tibial-cartilage-openknee.png':
            record['unresolved_mask_source_ids'] = ['TBC-L', 'TBC-M']
        evidence['figures'].append(record)
        print(path.name, path.stat().st_size, 'bytes', [(p['id'], p['raster_visibility']['visible_pixels']) for p in parts], flush=True)
    (output / 'rendering-evidence.json').write_text(json.dumps(evidence, indent=2, ensure_ascii=False) + '\n')
    return evidence


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=SOURCE)
    parser.add_argument('--output', type=Path, default=OUTPUT)
    args = parser.parse_args()
    render_all(args.source, args.output)
