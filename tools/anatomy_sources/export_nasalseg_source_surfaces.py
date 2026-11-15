#!/usr/bin/env python3
"""Extract unsmoothed source-label interfaces; never pad/cap an acquired volume boundary."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.ndimage import map_coordinates
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from skimage.measure import marching_cubes

from tools.anatomy_sources.review_nasalseg_case import LABELS, parse


def surface(region, affine):
    """Use original sample-centre indices and the declared xyz-to-LPS transform."""
    vertices, faces, _, _ = marching_cubes(
        region.astype(np.float32), level=0.5, allow_degenerate=False,
        gradient_direction='descent', method='lewiner',
    )
    xyz = vertices[:, ::-1].astype(np.float64)
    affine = np.asarray(affine, dtype=np.float64)
    # zyx->xyz is a reflection. Preserve the extractor winding under that map.
    if np.linalg.det(affine[:3, :3]) > 0:
        faces = faces[:, ::-1]
    world = xyz @ affine[:3, :3].T + affine[:3, 3]
    edges = np.sort(np.concatenate([faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]]), axis=1)
    unique, counts = np.unique(edges, axis=0, return_counts=True)
    graph = coo_matrix((np.ones(len(unique)), (unique[:, 0], unique[:, 1])), shape=(len(world), len(world)))
    components, _ = connected_components(graph, directed=False)
    triangles = world[faces]
    areas = np.linalg.norm(np.cross(triangles[:, 1]-triangles[:, 0], triangles[:, 2]-triangles[:, 0]), axis=1)/2
    # Lewiner resolves ambiguous cells with additional interior vertices.
    # Keep them and expose their binary-field residual rather than pretending
    # every triangulation vertex is an exact midpoint of a source sample edge.
    fractional = np.abs(vertices-np.rint(vertices)) > 1e-6
    edge_vertices = fractional.sum(axis=1) == 1
    lower = np.floor(vertices[edge_vertices]).astype(int)
    upper = np.ceil(vertices[edge_vertices]).astype(int)
    if not np.all(region[tuple(lower.T)] != region[tuple(upper.T)]):
        raise ValueError('Extracted edge does not separate original source labels')
    values = map_coordinates(region.astype(float), vertices.T, order=1, mode='nearest')
    residual = np.abs(values-.5)
    inverse = np.linalg.inv(affine)
    reconstructed = (world @ inverse[:3, :3].T + inverse[:3, 3])[:, ::-1]
    error = float(np.max(np.abs(reconstructed-vertices)))
    if error > 1e-8:
        raise ValueError('Source affine roundtrip differs')
    return world, faces, {
        'vertices': len(world), 'triangles': len(faces),
        'surface_components': int(components),
        'boundary_edges': int(np.count_nonzero(counts == 1)),
        'nonmanifold_edges': int(np.count_nonzero(counts > 2)),
        'zero_area_triangles': int(np.count_nonzero(areas == 0)),
        'sample_edge_interface_vertices_verified': int(edge_vertices.sum()),
        'ambiguity_resolution_interior_vertices_retained': int((~edge_vertices).sum()),
        'maximum_trilinear_binary_field_residual': float(residual.max()),
        'maximum_affine_roundtrip_error_source_indices': error,
        'source_index_bounds_zyx': [vertices.min(axis=0).tolist(), vertices.max(axis=0).tolist()],
        'declared_LPS_bounds_mm': [world.min(axis=0).tolist(), world.max(axis=0).tolist()],
    }


def export(root, output, proof_dir):
    mask_path = root/'P001/P001_seg.nrrd'
    mask, provenance = parse(mask_path.read_bytes())
    source_proof = json.loads((proof_dir/'original-case-grid-review.json').read_text())
    if hashlib.sha256(mask_path.read_bytes()).hexdigest() != source_proof['files'][1]['sha256']:
        raise ValueError('Mask differs from archive-verified original')
    output.mkdir(parents=True, exist_ok=True)
    models = []
    for label, name in LABELS.items():
        vertices, faces, stats = surface(mask == label, provenance['declared_LPS_affine'])
        text = '# NasalSeg P001 original label interface; declared LPS mm; no clinical approval\n'
        text += ''.join('v %.12g %.12g %.12g\n' % tuple(v) for v in vertices)
        text += ''.join('f %d %d %d\n' % tuple(f+1) for f in faces)
        path = output/(name+'.obj.gz')
        path.write_bytes(gzip.compress(text.encode(), mtime=0))
        # Read actual serialized coordinates/faces, rather than only trusting arrays.
        lines = gzip.decompress(path.read_bytes()).decode().splitlines()
        read_vertices = np.array([[float(v) for v in line.split()[1:]] for line in lines if line.startswith('v ')])
        read_faces = np.array([[int(v)-1 for v in line.split()[1:]] for line in lines if line.startswith('f ')])
        if not np.array_equal(read_faces, faces) or not np.allclose(read_vertices, vertices, rtol=0, atol=1e-8):
            raise ValueError('Serialized source surface differs')
        models.append({'source_label': label, 'source_name': name, 'file': path.name,
                       'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                       'serialized_vertex_and_face_readback_verified': True, **stats})
    proof = {
        'case': 'P001', 'dataset_record': 'https://zenodo.org/records/13893419',
        'source_mask_sha256': hashlib.sha256(mask_path.read_bytes()).hexdigest(),
        'dataset_license': source_proof['dataset_license'],
        'representation': 'binary source-label interface, not separately segmented mucosa/bone/nerve/wall',
        'extraction': 'skimage Lewiner marching cubes at original binary 0.5 interface',
        'coordinate_system': 'original declared LPS millimetres',
        'source_affine': provenance['declared_LPS_affine'], 'models': models,
        'source_padding_capping_smoothing_decimation_repair_or_component_filtering': False,
        'complete_anatomical_extent_verified': False, 'clinical_approval': False,
        'runtime_promoted': False, 'structure_coverage_granted': False,
    }
    (proof_dir/'source-label-surface-review.json').write_text(json.dumps(proof, indent=2)+'\n')
    print([(m['source_name'], m['triangles'], m['boundary_edges'], m['surface_components']) for m in models])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--proof-dir', type=Path, required=True)
    args = parser.parse_args()
    export(args.source_root, args.output, args.proof_dir)
