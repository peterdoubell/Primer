"""Reference surfaces of occupied source voxel cells, preserving label volume.

This is a data representation, not a subvoxel estimate of anatomical boundaries.
"""
from pathlib import Path
import gzip,hashlib,json,struct,sys
import numpy as np,nibabel as nib
ROOT=Path(__file__).resolve().parents[2];STAGE=ROOT/'.research/anatomy-sources/rootlets';OUT=ROOT/'output/msk-rootlet-sub-amu02/cell-boundaries';DOC=ROOT/'docs/msk-rootlet-source-review'
sys.path.insert(0,str(ROOT))
from tools.anatomy_sources.check_atlantoaxial_topology import topology


def build_cells(points,affine):
    occupied={tuple(map(int,p)) for p in points};keys={};vertices=[];faces=[];exposed=0
    for point in sorted(occupied):
        p=np.asarray(point,dtype=int)
        for axis in range(3):
            others=[a for a in range(3) if a!=axis]
            for sign in [-1,1]:
                neighbor=p.copy();neighbor[axis]+=sign
                if tuple(neighbor) in occupied:continue
                quad=[]
                for a,b in [(-1,-1),(1,-1),(1,1),(-1,1)]:
                    key=2*p;key[axis]+=sign;key[others[0]]+=a;key[others[1]]+=b;key=tuple(map(int,key))
                    if key not in keys:keys[key]=len(vertices);vertices.append(np.asarray(key,float)/2)
                    quad.append(keys[key])
                if (-1)**axis!=sign:quad=quad[::-1]
                faces.extend([[quad[0],quad[1],quad[2]],[quad[0],quad[2],quad[3]]]);exposed+=1
    voxel=np.asarray(vertices);world=nib.affines.apply_affine(affine,voxel);faces=np.asarray(faces,dtype='<u4')
    if np.linalg.det(affine[:3,:3])<0:faces=faces[:,[0,2,1]]
    return world,faces,exposed


def signed_volume(vertices,faces):
    tri=vertices[faces]-vertices.mean(0);return float(np.einsum('ij,ij->i',tri[:,0],np.cross(tri[:,1],tri[:,2])).sum()/6)


def main():
    acquisition=json.loads((STAGE/'acquisition.json').read_text());sources={Path(x['file']).name:x for x in acquisition['files']};iso=json.loads((DOC/'annotation-surface-comparison.json').read_text());rows=[];OUT.mkdir(parents=True,exist_ok=True)
    for name in ['rater1','rater2','rater3','rater4','staple']:
        filename=f'sub-amu02_T2w_desc-{name}_label-rootlets_dseg.nii.gz';path=STAGE/'sub-amu02'/filename;assert hashlib.sha256(path.read_bytes()).hexdigest()==sources[filename]['sha256'];image=nib.load(path);array=np.asanyarray(image.dataobj)
        for label in range(2,10):
            points=np.argwhere(array==label)
            if not len(points):continue
            world,faces,exposed=build_cells(points,image.affine);expected=float(len(points)*abs(np.linalg.det(image.affine[:3,:3])));observed=signed_volume(world,faces);assert abs(observed-expected)<=max(1e-9,expected*1e-12)
            positions=world.astype('<f4');transport_volume=signed_volume(positions.astype(float),faces);roundoff=float(np.linalg.norm(positions.astype(float)-world,axis=1).max());assert roundoff<1e-4
            normals=np.zeros_like(world);tri=world[faces];cross=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0])
            for c in range(3):np.add.at(normals,faces[:,c],cross)
            magnitude=np.linalg.norm(normals,axis=1);zero=magnitude==0;normals[~zero]/=magnitude[~zero,None];normals[zero]=[0,0,1]
            level=f'C{label}' if label<9 else 'T1';file=f'{name}-{level.lower()}-cells.bin.gz';raw=struct.pack('<4sII',b'BP3D',len(world),faces.size)+positions.tobytes()+normals.astype('<f4').tobytes()+faces.tobytes();payload=gzip.compress(raw,mtime=0);(OUT/file).write_bytes(payload);assert gzip.decompress(payload)==raw
            np.savez_compressed(OUT/file.replace('.bin.gz','.npz'),vertices_ras_mm=world,faces=faces)
            comparison=next(r for r in iso['sources'] if r['annotation']==name and r['label']==label);check=topology(world.tolist(),faces.tolist());rows.append({'annotation':name,'label':label,'level':level,'source_sha256':sources[filename]['sha256'],'voxels':len(points),'exposed_voxel_faces':exposed,'bounds_ras_mm':[world.min(0).tolist(),world.max(0).tolist()],'file':str((OUT/file).relative_to(ROOT)),'sha256':hashlib.sha256(payload).hexdigest(),'occupied_voxel_volume_mm3':expected,'double_precision_boundary_volume_mm3':observed,'float32_transport_volume_mm3':transport_volume,'maximum_transport_position_error_mm':roundoff,'isosurface_volume_mm3':comparison['rendered_isosurface_volume_mm3'],'topology':check,'zero_lighting_normal_fallback_vertices':int(zero.sum())})
    report={'case':'sub-amu02','representation':'Outer faces of labelled voxel-cell union; shared face interiors removed; no smoothing or subvoxel fitting.','parts':rows,'limits':['Voxel-cell boundaries preserve computational occupancy, not true subvoxel nerve boundaries.','Edge or corner contacts in source labels can produce non-manifold boundary geometry; these are retained and reported.','Comparison with the 0.5 isosurface measures representation sensitivity, not anatomical error.','Lighting normal fallback at singular vertices has no effect on positions or topology.'],'clinical_approval':False,'runtime_promoted':False};(DOC/'voxel-cell-boundary-comparison.json').write_text(json.dumps(report,indent=2)+'\n');print('Reference boundaries',len(rows),'exact occupied-volume checks passed');print('Parts with non-manifold edges',sum(r['topology']['nonmanifold_edges']>0 for r in rows));print('Position rounding maximum mm',max(r['maximum_transport_position_error_mm'] for r in rows))


if __name__=='__main__':main()
