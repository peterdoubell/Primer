"""Bound mesh-to-source distance using exact binary-grid boundary witnesses.

This is a directed upper bound, not a clinical or symmetric Hausdorff metric.
"""
from pathlib import Path
import hashlib,json
import numpy as np,nibabel as nib
ROOT=Path(__file__).resolve().parents[2];CASE=Path('/tmp/primer-msk-sources/verse/verse521')


def main():
    audit=json.loads((ROOT/'docs/msk-verse-source-review/chain-surface-audit.json').read_text());ray=json.loads((ROOT/'docs/msk-verse-source-review/triangle-centre-correspondence.json').read_text())
    for name,digest in audit['source_files'].items():assert hashlib.sha256((CASE/name).read_bytes()).hexdigest()==digest
    seg=nib.load(CASE/'sub-verse521_dir-ax_seg-vert_msk.nii.gz');mask=np.asanyarray(seg.dataobj);rows=[]
    for row in audit['levels']:
        path=ROOT/row['file'];assert hashlib.sha256(path.read_bytes()).hexdigest()==row['sha256'];mesh=np.load(path);voxel=mesh['vertices_voxel'];world=mesh['vertices_world_mm'];faces=mesh['faces']
        assert np.array_equal(mesh['affine'],seg.affine) and np.array_equal(nib.affines.apply_affine(seg.affine,voxel),world)
        frac=voxel-np.floor(voxel);half=frac==.5;integer=frac==0;edge=(half.sum(axis=1)==1)&np.all(half|integer,axis=1);ids=np.flatnonzero(edge)
        lower=np.floor(voxel[ids]).astype(int);upper=lower.copy();upper[np.arange(len(ids)),np.argmax(half[ids],axis=1)]+=1
        a=mask[tuple(lower.T)]==row['label'];b=mask[tuple(upper.T)]==row['label'];assert np.all(a!=b)
        # Each witness is the exact midpoint of a foreground/background grid edge.
        # Its trilinearly interpolated binary value is therefore exactly 0.5.
        eligible=edge[faces];assert np.all(eligible.any(axis=1))
        vertices=world[faces];centres=vertices.mean(axis=1);dist=np.linalg.norm(vertices-centres[:,None,:],axis=2);dist[~eligible]=np.inf;witness_corner=dist.argmin(axis=1);centroid_bound=dist.min(axis=1)
        pair=np.linalg.norm(vertices[:,:,None,:]-vertices[:,None,:,:],axis=3);radii=pair.max(axis=2);radii[~eligible]=np.inf;whole_triangle_bound=radii.min(axis=1)
        source_ray=next(r for r in ray['levels'] if r['level']==row['level']);examples=[]
        for sample in source_ray['largest_or_unbracketed_samples']:
            face=sample['face'];witness=int(faces[face,witness_corner[face]]);d=float(centroid_bound[face]);examples.append({'face':face,'normal_ray_distance_mm':sample['normal_distance_mm'],'known_exact_boundary_vertex':witness,'boundary_vertex_world_mm':world[witness].tolist(),'centroid_to_boundary_witness_mm':d,'ray_is_not_nearest':sample['normal_distance_mm'] is None or sample['normal_distance_mm']>d+1e-6})
        rows.append({'level':row['level'],'triangles':len(faces),'exact_boundary_edge_vertices':len(ids),'helper_vertices_not_used_as_witnesses':int((~edge).sum()),'every_triangle_has_exact_boundary_witness':True,'centroid_directed_distance_upper_bound_mm':float(centroid_bound.max()),'all_triangle_interiors_directed_distance_upper_bound_mm':float(whole_triangle_bound.max()),'normal_ray_outlier_comparisons':examples})
    report={'source_files':audit['source_files'],'levels':rows,'proof':'Every witness is an exact half-grid point on an edge with opposite binary endpoint labels. For each triangle choose an eligible witness vertex. Convexity of Euclidean norm bounds every barycentric interior point distance to that witness by the greatest distance from the witness to the three corners. Minimize this radius over eligible witness vertices.','scope':'Directed distance from derived mesh to trilinear source-mask 0.5 boundary only; reverse source-to-mesh distance and biological anatomy are not bounded.','geometry_changed':False,'clinical_approval':False,'runtime_promoted':False}
    (ROOT/'docs/msk-verse-source-review/surface-witness-bounds.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Triangles bounded:',sum(r['triangles'] for r in rows));print('Maximum centroid bound:',max(r['centroid_directed_distance_upper_bound_mm'] for r in rows));print('Maximum all-interior bound:',max(r['all_triangle_interiors_directed_distance_upper_bound_mm'] for r in rows))


if __name__=='__main__':main()
