#!/usr/bin/env python3
"""Show serialized source interfaces in declared LPS and intersect them with original CT planes."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.colors import LightSource, to_rgb
from matplotlib.ticker import MaxNLocator
from mpl_toolkits.mplot3d.art3d import Poly3DCollection, Line3DCollection
from tools.anatomy_sources.review_nasalseg_case import parse

COLORS = {1:'#f4a261', 2:'#2a9d8f', 3:'#e76f51', 4:'#457b9d', 5:'#aa66cc'}


def read_surface(path, row):
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != row['sha256']:
        raise ValueError('Reviewed serialized surface changed')
    lines = gzip.decompress(raw).decode().splitlines()
    vertices = np.array([[float(x) for x in line.split()[1:]] for line in lines if line.startswith('v ')])
    faces = np.array([[int(x)-1 for x in line.split()[1:]] for line in lines if line.startswith('f ')])
    if vertices.shape != (row['vertices'], 3) or faces.shape != (row['triangles'], 3) or not np.isfinite(vertices).all():
        raise ValueError('Reviewed surface dimensions differ')
    return vertices, faces


def plane_segments(vertices, faces, axis, index):
    """Intersect actual triangles, without projecting off-plane vertices onto the plane."""
    triangles = vertices[faces]
    distances = triangles[:, :, axis]-index
    points = []
    valid = []
    for a, b in [(0, 1), (1, 2), (2, 0)]:
        crossing = ((distances[:, a] <= 0) & (distances[:, b] > 0)) | ((distances[:, b] <= 0) & (distances[:, a] > 0))
        fraction = np.divide(-distances[:, a], distances[:, b]-distances[:, a], out=np.zeros(len(faces)), where=crossing)
        points.append(triangles[:, a]+fraction[:, None]*(triangles[:, b]-triangles[:, a]))
        valid.append(crossing)
    valid = np.array(valid).T
    points = np.stack(points, axis=1)
    selected = valid.sum(axis=1) == 2
    segments = points[selected][valid[selected]].reshape(-1, 2, 3)
    # Plane-coincident faces are counted explicitly, not silently claimed as intersections.
    coplanar = int(np.count_nonzero(np.all(distances == 0, axis=1)))
    if len(segments) and not np.allclose(segments[:, :, axis], index, rtol=0, atol=1e-9):
        raise ValueError('Intersection is not on the requested original source plane')
    return segments, coplanar


def render(root, proof_dir, output):
    proof_path = proof_dir/'source-label-surface-review.json'
    proof = json.loads(proof_path.read_text())
    source_path = root/'P001/P001_img.nrrd'; mask_path = root/'P001/P001_seg.nrrd'
    source, provenance = parse(source_path.read_bytes()); mask, mp = parse(mask_path.read_bytes())
    grid = json.loads((proof_dir/'original-case-grid-review.json').read_text())
    if hashlib.sha256(source_path.read_bytes()).hexdigest() != grid['files'][0]['sha256'] or hashlib.sha256(mask_path.read_bytes()).hexdigest() != proof['source_mask_sha256']:
        raise ValueError('Original reviewed source changed')
    affine = np.array(proof['source_affine']); inverse = np.linalg.inv(affine)
    if provenance['declared_LPS_affine'] != proof['source_affine'] or mp['declared_LPS_affine'] != proof['source_affine']:
        raise ValueError('Surface and CT/mask declared geometry differ')
    output.mkdir(parents=True, exist_ok=True)
    surfaces = []
    for row in proof['models']:
        v, f = read_surface(root/'P001-source-surfaces'/row['file'], row)
        zyx = (v @ inverse[:3, :3].T+inverse[:3, 3])[:, ::-1]
        surfaces.append((row, v, f, zyx))
    panels = []
    fig = plt.figure(figsize=(15, 22))
    for i, (row, vertices, faces, _) in enumerate(surfaces):
        ax = fig.add_subplot(3, 2, i+1, projection='3d')
        triangles = vertices[faces]
        normals = np.cross(triangles[:, 1]-triangles[:, 0], triangles[:, 2]-triangles[:, 0])
        normals /= np.linalg.norm(normals, axis=1)[:, None]
        illumination = .35+.65*LightSource(azdeg=315, altdeg=45).shade_normals(normals)
        colors = illumination[:, None]*np.array(to_rgb(COLORS[row['source_label']]))
        ax.add_collection3d(Poly3DCollection(triangles, facecolors=colors, edgecolors='none', linewidths=0))
        edges = np.sort(np.concatenate([faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]]), axis=1)
        unique, counts = np.unique(edges, axis=0, return_counts=True); boundary = unique[counts == 1]
        if len(boundary): ax.add_collection3d(Line3DCollection(vertices[boundary], colors='red', linewidths=1.1))
        low = vertices.min(axis=0); high = vertices.max(axis=0)
        ax.set_xlim(low[0], high[0]); ax.set_ylim(low[1], high[1]); ax.set_zlim(low[2], high[2]); ax.set_box_aspect(high-low)
        ax.view_init(elev=20, azim=-65)
        ax.set_xlabel('LPS x (mm)', labelpad=8); ax.set_ylabel('LPS y (mm)', labelpad=8); ax.set_zlabel('LPS z (mm)', labelpad=8)
        ax.tick_params(labelsize=8)
        for axis in [ax.xaxis, ax.yaxis, ax.zaxis]: axis.set_major_locator(MaxNLocator(nbins=4))
        ax.set_title(row['source_name'].replace('_', ' ')+'\n'+f"{len(faces):,} triangles; {row['surface_components']} components; {len(boundary)} open edges")
        panels.append({'source_name':row['source_name'],'all_original_extracted_triangles_rendered':len(faces),
                       'boundary_edges_highlighted':len(boundary),'camera_elevation':20,'camera_azimuth':-65,'triangle_normal_display_illumination_only':True})
    ax = fig.add_subplot(3, 2, 6); ax.axis('off')
    ax.text(0, .9, 'Source label interfaces only\n\nRed: acquired-volume open boundary\n\nOriginal disconnected components retained\n\nNo padding, smoothing, repair or decimation\n\nNot separate bone, mucosa, nerve or vessel walls\n\nDeclared source LPS, not verified raw DICOM\n\nNo independent anatomical/clinical approval', va='top', fontsize=12)
    fig.suptitle('NasalSeg P001 — serialized source-label surfaces\nComplete extracted geometry; visibility depends on camera, not anatomical coverage', fontsize=15)
    fig.subplots_adjust(top=.9, bottom=.05, hspace=.38, wspace=.18); model_path = output/'P001-label-surfaces.png'; fig.savefig(model_path, dpi=120, bbox_inches="tight"); plt.close(fig)
    fig, axes = plt.subplots(3, 2, figsize=(14, 16)); planes = []
    pitch = list(reversed(provenance['source_pitch_mm'])); centre = [int(np.median(x)) for x in np.where(mask > 0)]
    for axis, index in enumerate(centre):
        ct = np.take(source, index, axis=axis); labels = np.take(mask, index, axis=axis)
        others = [x for x in range(3) if x != axis]; aspect = pitch[others[0]]/pitch[others[1]]
        for ax in axes[axis]:
            ax.imshow(ct, cmap='gray', origin='lower', vmin=-1000, vmax=1500, aspect=aspect)
            ax.set_xlabel('Original in-plane source index'); ax.set_ylabel('Original in-plane source index')
        stats = []
        for row, _, faces, zyx in surfaces:
            label = row['source_label']; color = COLORS[label]
            if (labels == label).any(): axes[axis, 0].contour(labels == label, levels=[.5], colors=[color], linewidths=.9)
            segments, coplanar = plane_segments(zyx, faces, axis, index)
            if len(segments): axes[axis, 1].add_collection(LineCollection(segments[:, :, others[::-1]], colors=color, linewidths=.9))
            stats.append({'source_label':label,'actual_mesh_plane_segments':len(segments),'plane_coincident_faces':coplanar})
        axes[axis, 0].set_title(f'Original mask contour on CT\nzyx axis {axis}, index {index}')
        axes[axis, 1].set_title('Serialized LPS mesh intersected with same CT plane\nNo registration, fitted transform or source repair')
        planes.append({'source_normal_axis_zyx':axis,'source_index':index,'display_pixel_aspect':aspect,'intersections':stats})
    fig.suptitle('NasalSeg P001 — original masks versus serialized mesh cross-sections\nDeclared shared geometry; display window −1000..1500 source units (HU unverified)\nSurface triangulation in ambiguous cells is not independent anatomical truth', fontsize=13)
    fig.tight_layout(rect=[0, 0, 1, .92]); plane_path = output/'P001-mesh-CT-alignment.png'; fig.savefig(plane_path, dpi=120, bbox_inches="tight"); plt.close(fig)
    result = {'source_surface_review_sha256':hashlib.sha256(proof_path.read_bytes()).hexdigest(),
              'source_CT_sha256':hashlib.sha256(source_path.read_bytes()).hexdigest(),
              'source_mask_sha256':hashlib.sha256(mask_path.read_bytes()).hexdigest(),
              'source_mesh_hashes':{row['source_name']:row['sha256'] for row,_,_,_ in surfaces},
              'figures':[{'file':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in [model_path,plane_path]],
              'source_surface_views':panels,'actual_mesh_intersection_planes':planes,
              'source_registration_resampling_repair_or_decimation':False,
              'independent_raw_DICOM_geometry_or_anatomical_approval':False,'clinical_approval':False,'runtime_promoted':False}
    (proof_dir/'source-surface-display-review.json').write_text(json.dumps(result, indent=2)+'\n')
    print(model_path); print(plane_path)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', type=Path, required=True); parser.add_argument('--proof-dir', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True); args = parser.parse_args()
    render(args.source_root, args.proof_dir, args.output)
