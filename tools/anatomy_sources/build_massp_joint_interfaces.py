#!/usr/bin/env python3
"""Joint label interfaces from one unchanged native source selection.

Within each consistently split grid tetrahedron, label weights are sums of
barycentric weights of its original source vertices. Regions are their argmax.
Interfaces are shared exactly; this interpolation is not measured anatomy.
"""
import argparse
from functools import lru_cache
import hashlib
from itertools import combinations, permutations
import json
from pathlib import Path
import numpy as np
import nibabel as nib
from tools.anatomy_sources.massp_probability_mesh import load_verified, LABELS

SCALE=12
CORNERS=np.array(list(__import__('itertools').product((0,1),repeat=3)),dtype=int)
TETS=[]
for order in permutations(range(3)):
    points=[np.zeros(3,dtype=int)];point=points[0].copy()
    for axis in order:
        point=point.copy();point[axis]+=1;points.append(point)
    TETS.append(np.array(points))
BARY_COEFFICIENTS=np.array([[-1,-1,-1],[1,0,0],[0,1,0],[0,0,1]],dtype=int)
BARY_CONSTANTS=np.array([1,0,0,0],dtype=int)


def det3(matrix):
    a,b,c=matrix
    return int(a[0]*(b[1]*c[2]-b[2]*c[1])-a[1]*(b[0]*c[2]-b[2]*c[0])+a[2]*(b[0]*c[1]-b[1]*c[0]))


@lru_cache(maxsize=None)
def region_interfaces(pattern,target):
    # All inequalities are A*t <= b in tetrahedral barycentric coordinates.
    classes=sorted(set(pattern))
    weights={label:BARY_COEFFICIENTS[np.array(pattern)==label].sum(0) for label in classes}
    constants={label:int(BARY_CONSTANTS[np.array(pattern)==label].sum()) for label in classes}
    planes=[(-BARY_COEFFICIENTS[i],int(BARY_CONSTANTS[i]),None) for i in range(4)]
    for other in classes:
        if other!=target:
            planes.append((weights[other]-weights[target],constants[target]-constants[other],other))
    vertices=set()
    for indices in combinations(range(len(planes)),3):
        matrix=np.array([planes[i][0] for i in indices]);rhs=np.array([planes[i][1] for i in indices])
        denominator=det3(matrix)
        if not denominator:continue
        numerators=[]
        for column in range(3):
            modified=matrix.copy();modified[:,column]=rhs;numerators.append(det3(modified))
        if denominator<0:denominator=-denominator;numerators=[-v for v in numerators]
        if any(int(a@np.array(numerators))>b*denominator for a,b,_ in planes):continue
        if any((value*SCALE)%denominator for value in numerators):
            raise ValueError('Interface vertex outside exact rational lattice')
        vertices.add(tuple(value*SCALE//denominator for value in numerators))
    vertices=np.array(sorted(vertices),dtype=int).reshape(-1,3)
    interfaces=[]
    for normal,rhs,other in planes:
        if other is None:continue  # Internal tetrahedral boundaries are not anatomy surfaces.
        polygon=vertices[vertices@normal==rhs*SCALE]
        if len(polygon)<3:continue
        center=polygon.mean(0);unit=normal/np.linalg.norm(normal)
        helper=np.eye(3)[int(np.argmin(np.abs(unit)))];horizontal=np.cross(helper,unit);horizontal/=np.linalg.norm(horizontal)
        vertical=np.cross(unit,horizontal)
        angles=np.arctan2((polygon-center)@vertical,(polygon-center)@horizontal)
        polygon=polygon[np.argsort(angles)]
        anchor=min(range(len(polygon)),key=lambda i:tuple(polygon[i]))
        polygon=np.roll(polygon,-anchor,axis=0)
        faces=[]
        for i in range(1,len(polygon)-1):
            triangle=polygon[[0,i,i+1]]
            cross=np.cross(triangle[1]-triangle[0],triangle[2]-triangle[0])
            if np.all(cross==0):continue
            if cross@normal<0:triangle=triangle[[0,2,1]]
            faces.append(triangle)
        interfaces.extend(faces)
    return tuple(tuple(tuple(int(v) for v in point) for point in triangle) for triangle in interfaces)


def build_label_surfaces(labels,targets):
    targets=set(targets)
    selected=np.isin(labels,list(targets));coords=np.argwhere(selected)
    if not len(coords):raise ValueError('No source targets')
    if any(selected.take(i,axis=a).any() for a in range(3) for i in (0,-1)):
        raise ValueError('Source targets touch field boundary')
    lo=coords.min(0)-1;hi=coords.max(0)+1
    corner_values=np.stack([labels[tuple(slice(a+c,b+c) for a,b,c in zip(lo,hi,corner))] for corner in CORNERS])
    needed=np.any(np.isin(corner_values,list(targets)),axis=0) & np.any(corner_values!=corner_values[0],axis=0)
    cell_origins=np.argwhere(needed)+lo
    vertex_maps={label:{} for label in targets};vertices={label:[] for label in targets};faces={label:[] for label in targets}
    emitted_tetrahedra=0
    for count,origin in enumerate(cell_origins):
        for tetra in TETS:
            codes=tuple(int(labels[tuple(origin+point)]) for point in tetra)
            present=targets.intersection(codes)
            if not present or len(set(codes))==1:continue
            canonical={code:i for i,code in enumerate(dict.fromkeys(codes))};pattern=tuple(canonical[code] for code in codes)
            basis=(tetra[1:]-tetra[0]).T;orientation=det3(basis)
            emitted_tetrahedra+=1
            for code in present:
                for tri in region_interfaces(pattern,canonical[code]):
                    lattice=np.array(tri,dtype=int)@basis.T+(origin+tetra[0])*SCALE
                    if orientation<0:lattice=lattice[[0,2,1]]
                    face=[]
                    for point in lattice:
                        key=tuple(int(x) for x in point)
                        if key not in vertex_maps[code]:
                            vertex_maps[code][key]=len(vertices[code]);vertices[code].append(key)
                        face.append(vertex_maps[code][key])
                    faces[code].append(face)
        if count and count%5000==0:print('Boundary cells:',count,flush=True)
    result={code:(np.array(vertices[code],dtype=float)/SCALE,np.array(faces[code],dtype=np.int64)) for code in targets}
    return result,{'boundary_cells':len(cell_origins),'mixed_target_tetrahedra':emitted_tetrahedra,'exact_native_index_lattice_denominator':SCALE}


def build(root,output):
    output.mkdir(parents=True,exist_ok=True)
    source=json.loads((root/'acquisition.json').read_text())
    source_file='ahead-massp2_avg-bestlabel_decade-18to80.nii.gz'
    image=load_verified(root,source_file,source);data=np.asarray(image.dataobj)
    if not np.isfinite(data).all() or not np.equal(data,np.rint(data)).all():raise ValueError('Invalid source labels')
    surfaces,stats=build_label_surfaces(data,LABELS)
    records=[]
    for label,(native,faces) in surfaces.items():
        world=nib.affines.apply_affine(image.affine,native)
        if np.linalg.det(image.affine[:3,:3])<0:faces=faces[:,[0,2,1]]
        code,side=LABELS[label];name=f'{code}-{side}-joint.npz';np.savez_compressed(output/name,vertices=world,faces=faces)
        records.append({'label_id':label,'code':code,'side':side,'mesh_file':name,'mesh_sha256':hashlib.sha256((output/name).read_bytes()).hexdigest(),
                        'vertices':len(world),'triangles':len(faces),'output_mesh_created':True,'surface_status':'offline_joint_interface_candidate_requires_validation',
                        'native_selected_voxels':int(np.count_nonzero(data==label)),'source_components_removed':0,'source_label_changes':False})
        print(code,side,len(faces),flush=True)
    record={'source_doi':source['doi'],'publisher_selection_file':source_file,'selection':'Unchanged publisher best-label volume',
            'source_acquisition_sha256':hashlib.sha256((root/'acquisition.json').read_bytes()).hexdigest(),
            'construction':'Consistent six-tetrahedron Freudenthal split of each native cell; original source-label one-hot weights interpolated barycentrically, with their shared argmax interfaces triangulated identically. Exact 1/12 index lattice before native affine. Other source labels remain distinct competitors, not merged into background.',
            'source_values_changed':False,'smoothing_or_decimation':False,'records':records,**stats,
            'clinical_approval':False,'runtime_binding_added':False,
            'limits':'Derived subvoxel partition, not measured anatomy. Tetrahedral subdivision introduces a directional interpolation assumption; anatomical boundaries and all geometric checks require validation.'}
    (output/'surface-review.json').write_text(json.dumps(record,indent=2)+'\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();build(args.source,args.output)
