"""Quantify original surface/label relationship without changing either source."""
import json
from pathlib import Path
import sys
import numpy as np
from scipy.spatial import cKDTree
from scipy.ndimage import label as components
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.anatomy_sources.spl_limbic_source import SOURCE, RESEARCH, PROPOSAL, CODES, parse_nrrd, parse_vtk, apply_affine, sha, require


def triangle_distance2(p, triangles):
    a, b, c = triangles[:, 0], triangles[:, 1], triangles[:, 2]
    ab, ac, ap = b-a, c-a, p-a
    answer = np.full(len(a), np.inf)
    for v, w in ((a,b), (b,c), (c,a)):
        edge = w-v
        denominator = np.einsum('ij,ij->i', edge, edge)
        t = np.divide(np.einsum('ij,ij->i', p-v, edge), denominator, out=np.zeros(len(a)), where=denominator > 0)
        residual = p-(v+np.clip(t, 0, 1)[:, None]*edge)
        answer = np.minimum(answer, np.einsum('ij,ij->i', residual, residual))
    normal = np.cross(ab, ac)
    denom = np.einsum('ij,ij->i', normal, normal)
    # Cross-product barycentrics avoid subtractive cancellation in dot-product denominators.
    u = np.divide(np.einsum('ij,ij->i', np.cross(ap, ac), normal), denom, out=np.zeros(len(a)), where=denom > 0)
    v = np.divide(np.einsum('ij,ij->i', np.cross(ab, ap), normal), denom, out=np.zeros(len(a)), where=denom > 0)
    inside = (denom > 0) & (u >= 0) & (v >= 0) & (u+v <= 1)
    plane = np.divide(np.einsum('ij,ij->i', ap, normal)**2, denom, out=np.full(len(a), np.inf), where=denom > 0)
    return np.where(inside, np.minimum(answer, plane), answer)


def quad_distance2(p, centers, axes):
    delta = np.abs(centers-p)
    excess = np.maximum(delta-.5, 0)
    excess[np.arange(len(axes)), axes] = delta[np.arange(len(axes)), axes]
    return np.einsum('ij,ij->i', excess, excess)


def nearest_exact(points, primitives, centers, radius, distance):
    tree = cKDTree(centers)
    nearest = tree.query(points)[1]
    upper = np.array([np.sqrt(distance(p, np.array([i]))[0]) for p, i in zip(points, nearest)])
    candidates = tree.query_ball_point(points, upper+radius+1e-9)
    out = np.empty(len(points)); indices = np.empty(len(points), dtype='i8')
    for i, (p, choices) in enumerate(zip(points, candidates)):
        choices = np.asarray(choices)
        squared = distance(p, choices)
        best = int(np.argmin(squared))
        out[i] = np.sqrt(max(0., squared[best])); indices[i] = choices[best]
    rng = np.random.default_rng(20261016)
    checked = rng.choice(len(points), min(32, len(points)), replace=False)
    for i in checked:
        brute = np.sqrt(np.min(distance(points[i], np.arange(len(centers)))))
        require(abs(brute-out[i]) < 1e-9, 'Bounded search disagrees with exhaustive exact primitive distance')
    require(np.isfinite(out).all(), 'Nonfinite distance result')
    return out, indices, len(checked)


def stats(values):
    return {'count': len(values), 'min_mm': float(values.min()), 'median_mm': float(np.median(values)),
            'p95_mm': float(np.percentile(values,95)), 'max_mm': float(values.max()),
            'count_above_0_5_mm': int((values > .5).sum()), 'count_above_1_mm': int((values > 1).sum()),
            'count_above_2_mm': int((values > 2).sum())}


def main():
    unit = np.array([[[0.,0.,0.],[1.,0.,0.],[0.,1.,0.]]])
    for p, expected in [([.2,.2,2.],4.), ([1.,1.,0.],.5), ([-1.,0.,0.],1.), ([.2,.2,0.],0.)]:
        require(np.allclose(triangle_distance2(np.array(p), unit), expected, atol=1e-14), 'Triangle analytic fixture failed')
    degenerate = np.array([[[0.,0.,0.],[0.,0.,0.],[1.,0.,0.]], [[0.,0.,0.]]*3])
    require(np.allclose(triangle_distance2(np.array([.5,1.,0.]), degenerate), [1.,1.25]), 'Degenerate fixture failed')
    labels = parse_nrrd(SOURCE / 'slicer/volumes/labels/hncma-atlas.nrrd')
    affine, inverse = labels['voxelToRAS'], np.linalg.inv(labels['voxelToRAS'])
    require(np.array_equal(affine[:3,:3].T @ affine[:3,:3], np.eye(3)), 'Distance assumes source 1mm orthonormal grid')
    rows = []
    for code in CODES:
        cells = np.argwhere(labels['array'] == code)
        cell_set = set(map(tuple,cells))
        face_centers, face_axes, face_cells, face_signs = [], [], [], []
        for cell in cells:
            for axis in range(3):
                for sign in (-1,1):
                    neighbor = cell.copy(); neighbor[axis] += sign
                    if tuple(neighbor) not in cell_set:
                        center = cell.astype(float); center[axis] += sign*.5
                        face_centers.append(center); face_axes.append(axis); face_cells.append(cell); face_signs.append(sign)
        face_centers, face_axes = np.asarray(face_centers), np.asarray(face_axes)
        face_ras = apply_affine(affine, face_centers)
        path = next((SOURCE / 'slicer/models').glob(f'Model_{code}_*.vtk'))
        model = parse_vtk(path)
        vertices = model['positions'].astype(float)
        ijk = apply_affine(inverse, vertices)
        triangles = vertices[model['triangles']]
        tri_centers = triangles.mean(axis=1)
        tri_radius = np.linalg.norm(triangles-tri_centers[:,None,:], axis=2).max()
        to_labels, label_face, brute1 = nearest_exact(ijk, None, face_centers, np.sqrt(.5),
            lambda p, ids: quad_distance2(p, face_centers[ids], face_axes[ids]))
        to_mesh, tri_index, brute2 = nearest_exact(face_ras, None, tri_centers, tri_radius,
            lambda p, ids: triangle_distance2(p, triangles[ids]))
        low = cells.min(0); crop = tuple(slice(int(a), int(b)+1) for a,b in zip(low, cells.max(0)))
        cc,n = components(labels['array'][crop] == code, structure=np.ones((3,3,3), dtype='u1'))
        sizes = sorted(np.bincount(cc.ravel())[1:].tolist(), reverse=True)
        face_components = cc[tuple((np.asarray(face_cells)-low).T)]
        component_distances = [{'component_id':int(component), 'voxel_count':int((cc==component).sum()), 'face_center_to_original_surface':stats(to_mesh[face_components==component])} for component in range(1,n+1)]
        rounded = np.floor(ijk+.5).astype(int)
        inside = ((rounded >= 0) & (rounded < np.array(labels['shape']))).all(1)
        nearest_codes = np.full(len(vertices), -1)
        nearest_codes[inside] = labels['array'][tuple(rounded[inside].T)]
        worst1, worst2 = int(to_labels.argmax()), int(to_mesh.argmax())
        row = {'code': code, 'source_file': str(path.relative_to(SOURCE)), 'source_sha256':sha(model['raw']),
               'voxel_count': len(cells), 'all_26_connected_component_sizes_preserved': sizes,
               'vertex_count':len(vertices), 'triangle_count':len(triangles),
               'degenerate_triangle_count':int((np.linalg.norm(np.cross(triangles[:,1]-triangles[:,0],triangles[:,2]-triangles[:,0]),axis=1)==0).sum()),
               'exposed_voxel_cell_face_count':len(face_centers),
               'all_original_vertices_to_categorical_cell_boundary':stats(to_labels),
               'all_exposed_face_centers_to_original_triangle_surface':stats(to_mesh),
               'label_component_face_center_distances':component_distances,
               'worst_vertex':{'original_index':worst1,'RAS':vertices[worst1].tolist(),'label_cell':face_cells[label_face[worst1]].tolist(),'face_axis':int(face_axes[label_face[worst1]])},
               'worst_face_center':{'cell':face_cells[worst2].tolist(),'axis':int(face_axes[worst2]),'sign':face_signs[worst2],'RAS':face_ras[worst2].tolist(),'original_expanded_triangle_index':int(tri_index[worst2])},
               'nearest_label_code_at_source_vertices':{str(int(k)):int(v) for k,v in zip(*np.unique(nearest_codes,return_counts=True))},
               'deterministic_queries_confirmed_by_full_primitive_scan':brute1+brute2,
               'coordinate_transform_fitted':False,'mesh_repaired_or_welded':False,
               'exact_categorical_boundary':False}
        rows.append(row)
        print(code, 'vertex-to-cell max', round(float(to_labels.max()),4), 'face-center-to-surface max', round(float(to_mesh.max()),4), flush=True)
    result = {'schema_version':1,'source_commit':'bec24db25aad5f7600e2df3becfb1f883e61ff56',
              'manifest_sha256':sha((PROPOSAL / 'manifest.json').read_bytes()),
              'coordinate_basis':'Original legacy Slicer RAS millimetres; exact NRRD-declared label affine, no fitted alignment.',
              'methods':{'vertices_to_labels':'All original vertices measured to every exposed unit voxel-cell quad through exact primitive distances and a provably inclusive center-radius candidate bound.',
                         'labels_to_surface':'Every exposed categorical cell-face center measured to original strip-derived finite triangles, including degeneracies; inclusive center-radius bound, analytic segment/plane distances.',
                         'limits':'This is a vertex/face-center sampling audit, not a continuous Hausdorff bound, voxel-boundary equivalence, segmentation accuracy validation or clinical review. Source processed surfaces and categorical labels are distinct objects.'},
              'analytic_triangle_fixtures_passed':6,'rows':rows,
              'all_source_vertices_and_label_components_retained':True,
              'clinical_approval':False}
    (RESEARCH/'spatial-audit.json').write_text(json.dumps(result,indent=2)+'\n')
    print('Saved', RESEARCH/'spatial-audit.json', flush=True)

if __name__ == '__main__': main()
