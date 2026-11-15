#!/usr/bin/env python3
"""Offline review projections of the staged Leeds 981 author assembly.

Retains all six source face nodes in a declared four-triangle planar display.
Exact quadratic arrays remain audit truth. No fitting, anatomy relabelling,
runtime publication, clinical approval or new source acquisition is performed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont, __version__ as PILLOW_VERSION

# Only the source-agnostic depth rasterizer/camera/font utilities are reused.
# No OpenKnee anatomy, source metadata, labels or license is used.
from render_openknee_schematics import camera_basis, rasterize

ROOT = Path(__file__).resolve().parents[2]
SOURCE = Path('/tmp/primer-msk-sources/leeds-knee-981/geometry-audit')
OUTPUT = SOURCE.parent / 'visual-review'
SIZE = (1800, 1500)
VIEWPORT = (80, 245, 1350, 1100)
PARTS = {
    'PT_FEMUR': ('Femur', '#d4cdbc'),
    'PT_TIBIA': ('Tibia', '#bcb8ad'),
    'PT_FCART': ('Femoral cartilage', '#459eaf'),
    'PT_TCART_MED': ('Medial tibial cartilage', '#75bcb1'),
    'PT_TCART_LAT': ('Lateral tibial cartilage', '#5493b0'),
    'PT_MEDIAL_MEN': ('Medial meniscus', '#d59649'),
    'PT_LATERAL_MEN': ('Lateral meniscus', '#916eb8'),
}
# Quadratic-face columns: a,b,c,ab,bc,ca. All six positions are retained.
DISPLAY_MAP = np.array([[0, 3, 5], [3, 1, 4], [5, 4, 2], [3, 4, 5]])
VIEWS = [
    dict(filename='leeds-author-assembly.png', title='Author assembly: seven source tissues',
         parts=list(PARTS), right=[1, 0, 0], up=[0, 0, 1], eye=[0, -1, 0],
         axes='Screen right +X  |  screen up +Z  |  eye on -Y',
         omissions='All seven solid tissue groups included; opaque surfaces conceal some joint contents.'),
    dict(filename='leeds-tibial-cartilage-menisci.png', title='Tibial cartilage and menisci',
         parts=['PT_TCART_MED', 'PT_TCART_LAT', 'PT_MEDIAL_MEN', 'PT_LATERAL_MEN'],
         right=[1, 0, 0], up=[0, 1, 0], eye=[0, 0, 1],
         axes='Screen right +X  |  screen up +Y  |  eye on +Z',
         omissions='Femur, tibia and femoral cartilage omitted to reveal these four whole source tissues.'),
    dict(filename='leeds-femoral-cartilage-bone.png', title='Femoral cartilage with femur',
         parts=['PT_FEMUR', 'PT_FCART'], right=[1, 0, 0],
         up=[0, -np.cos(np.deg2rad(40)), np.sin(np.deg2rad(40))],
         eye=[0, -np.sin(np.deg2rad(40)), -np.cos(np.deg2rad(40))],
         axes='Screen right +X  |  up -0.766 Y +0.643 Z  |  eye -0.643 Y -0.766 Z',
         omissions='Tibia, tibial cartilage and menisci omitted; femur and cartilage keep author positions.'),
]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fonts():
    candidates = [
        (Path('/System/Library/Fonts/Supplemental/Arial.ttf'),
         Path('/System/Library/Fonts/Supplemental/Arial Bold.ttf')),
        (Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'),
         Path('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf')),
    ]
    for regular, bold in candidates:
        if regular.is_file() and bold.is_file():
            return regular, bold, dict(regular_file=str(regular), bold_file=str(bold),
                                       regular_sha256=sha(regular), bold_sha256=sha(bold))
    raise FileNotFoundError('No supported local font pair; no download attempted')


def read_part(source, identifier, artifact):
    path = source / (identifier + '.npz')
    if sha(path) != artifact['sha256']:
        raise ValueError('Changed staged source: ' + identifier)
    with np.load(path, allow_pickle=False) as data:
        positions = data['positions_author_instance']
        faces = data['quadratic_faces']
        if faces.ndim != 2 or faces.shape[1] != 6 or not np.isfinite(positions).all():
            raise ValueError('Expected finite source positions and six-node faces')
        triangles = positions[faces[:, DISPLAY_MAP]].reshape(-1, 3, 3)
        if not np.array_equal(np.unique(faces), np.unique(faces[:, DISPLAY_MAP])):
            raise ValueError('Display dropped source midside nodes')
        normals = np.cross(triangles[:, 1] - triangles[:, 0], triangles[:, 2] - triangles[:, 0])
        if np.any(np.linalg.norm(normals, axis=1) == 0):
            raise ValueError('Zero-area display triangle')
        face_count = len(faces)
        nodal_bounds = [positions.min(0).tolist(), positions.max(0).tolist()]
    return dict(id=identifier, triangles=triangles, normals=normals, color=PARTS[identifier][1],
                source=dict(filename=path.name, sha256=artifact['sha256'], quadratic_faces=face_count,
                            display_triangles=len(triangles), nodal_bounds_author_instance=nodal_bounds))


def projection_for(meshes, basis):
    points = np.concatenate([m['triangles'].reshape(-1, 3) @ basis.T for m in meshes])
    low, high = points[:, :2].min(0), points[:, :2].max(0)
    x0, y0, x1, y1 = VIEWPORT
    scale = .91 * min((x1 - x0) / (high[0] - low[0]), (y1 - y0) / (high[1] - low[1]))
    # Rasterizer API uses legacy *_mm keys; here these are native source units.
    return dict(pixels_per_mm=float(scale), center_uv_mm=((low + high) / 2).tolist(),
                center_pixel=[(x0 + x1) / 2, (y0 + y1) / 2],
                native_uv_bounds_mm=[low.tolist(), high.tolist()], viewport_pixels=list(VIEWPORT))


def annotate(rgb, records, view, projection, font_paths):
    regular, bold, _ = font_paths
    image = Image.fromarray(rgb, 'RGB')
    draw = ImageDraw.Draw(image)
    ink, gray = '#23343e', '#52616b'

    def font(size, strong=False):
        return ImageFont.truetype(str(bold if strong else regular), size)

    def text(xy, value, size=22, strong=False, fill=gray):
        if draw.textlength(value, font=font(size, strong)) > SIZE[0] - xy[0] - 45:
            raise ValueError('Caption exceeds layout: ' + value)
        draw.text(xy, value, font=font(size, strong), fill=fill)

    text((55, 40), view['title'], 49, True, ink)
    text((58, 115), 'LEEDS 981  /  LTKN8941  /  seg_intact_fix  /  OFFLINE SOURCE REVIEW', 25, True)
    text((58, 164), 'Native author-assembly axes; anatomical axis identity and MRI registration unverified.', 23)
    text((58, 203), view['axes'], 22)
    stats = {row['id']: row for row in records}
    text((1390, 274), 'Whole source tissues', 22, True, ink)
    for index, identifier in enumerate(view['parts']):
        y = 324 + index * 92
        name, color = PARTS[identifier]
        draw.rounded_rectangle((1390, y + 4, 1412, y + 26), radius=3, fill=color)
        words = name.split(' ')
        lines = [' '.join(words[:-1]), words[-1]] if len(words) > 2 else [name]
        for line_index, line in enumerate(lines):
            text((1428, y + line_index * 27), line, 21, True, ink)
        if not stats[identifier]['visible_pixels']:
            text((1428, y + 54), 'Occluded in this view', 16)
    scale_length = 10 * projection['pixels_per_mm']
    x, y = 100, 1136
    draw.line([(x, y), (x + scale_length, y)], fill=ink, width=4)
    for xx in (x, x + scale_length):
        draw.line([(xx, y - 8), (xx, y + 8)], fill=ink, width=3)
    text((100, 1155), '10 native units (no conversion)', 20)
    draw.line([(55, 1200), (1745, 1200)], fill='#d5dce0', width=2)
    lines = [
        view['omissions'],
        'Source-processed CT bone/cartilage; MRI-derived menisci contact-adjusted for solver convergence.',
        'All six quadratic-face nodes retained in four planar display triangles; exact quadratic arrays remain audit truth.',
        'Author positions retained. No fitting, smoothing or clinical approval. Roots are mechanical springs and are excluded.',
        'Other knee tissues are absent from this model; colors, lighting and projection are added for source review.',
        'Source: Cooper, Day, Wijayathunga, Yao, Mengoni, Wilcox & Jones (2023), University of Leeds. doi:10.5518/981',
        'CC BY 4.0 — creativecommons.org/licenses/by/4.0/  |  This is a model rendering, not an MRI or clinical measurement.',
    ]
    for index, line in enumerate(lines):
        text((58, 1221 + index * 35), line, 20)
    return image


def render_all(source, output):
    if output.resolve().is_relative_to((ROOT / 'web').resolve()):
        raise ValueError('Only stage source review; do not publish to runtime')
    manifest_path = source / 'geometry-audit.json'
    audit = json.loads(manifest_path.read_text())
    if audit['source']['license'] != 'CC BY 4.0' or audit['source']['doi'] != '10.5518/981':
        raise ValueError('Unexpected source')
    artifacts = {a['file']: a for a in audit['artifacts']}
    meshes = {identifier: read_part(source, identifier, artifacts[identifier + '.npz']) for identifier in PARTS}
    output.mkdir(parents=True, exist_ok=True)
    font_paths = fonts()
    evidence = dict(schema='primer.leeds-knee-visual-review.v1', status='offline visual review; no clinical approval',
                    source=audit['source'], source_geometry_audit_sha256=sha(manifest_path),
                    coordinates=audit['coordinates'], clinical_approval=False,
                    runtime_catalog_ledger_changed=False, figures=[],
                    renderer=dict(script_sha256=sha(Path(__file__)),
                                  rasterizer_script_sha256=sha(Path(__file__).with_name('render_openknee_schematics.py')),
                                  numpy=np.__version__, pillow=PILLOW_VERSION, fonts=font_paths[2],
                                  size_pixels=list(SIZE), source_nodes_moved=False, fitted_alignment=False,
                                  source_frame='positions_author_instance, before FE displacements',
                                  normals='Geometry-derived cross products per planar display triangle; no source normals or smoothing',
                                  depth='Opaque global pixel-center z-buffer, largest camera-depth wins; canonical primitive resolves 1e-9 native-unit ties',
                                  preview='Four planar triangles through all six source nodes per quadratic face, columns a,b,c,ab,bc,ca',
                                  display_node_map=DISPLAY_MAP.tolist(),
                                  exact_quadratic_geometry_preserved_in='Unchanged PT_*.npz; display is an explicitly approximate planar tessellation',
                                  preview_error_bound='Not established; no quantitative geometry claims from render pixels',
                                  source_max_midside_midpoint_deviation_native_units=audit['volume']['midpoint_deviation_native_units']['max']))
    for view in VIEWS:
        selected = [meshes[identifier] for identifier in view['parts']]
        basis = camera_basis(view['right'], view['up'], view['eye'])
        projection = projection_for(selected, basis)
        rgb, _, _, _, _, records = rasterize(selected, basis, projection, SIZE)
        image = annotate(rgb, records, view, projection, font_paths)
        path = output / view['filename']
        image.save(path, format='PNG', compress_level=6)
        evidence['figures'].append(dict(filename=path.name, sha256=sha(path), bytes=path.stat().st_size,
                                       title=view['title'], part_sources=[m['source'] for m in selected],
                                       whole_tissue_names={i: PARTS[i][0] for i in view['parts']},
                                       camera=dict(orthographic_basis_rows=basis.tolist(),
                                                   screen_right=view['right'], screen_up=view['up'],
                                                   eye_from_target=view['eye'], axes_caption=view['axes'],
                                                   pixels_per_native_unit=projection['pixels_per_mm'],
                                                   center_uv_native_units=projection['center_uv_mm'],
                                                   center_pixel=projection['center_pixel'], viewport_pixels=list(VIEWPORT)),
                                       visibility=records, omitted_context=view['omissions']))
        print(path.name, [(r['id'], r['visible_pixels']) for r in records], flush=True)
    (output / 'rendering-evidence.json').write_text(json.dumps(evidence, indent=2, ensure_ascii=False) + '\n')
    return evidence


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=SOURCE)
    parser.add_argument('--output', type=Path, default=OUTPUT)
    args = parser.parse_args()
    render_all(args.source, args.output)
