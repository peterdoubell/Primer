"""Exact categorical cell boundaries; no interpolation, smoothing or cleanup."""
from collections import Counter
import json
import struct
import numpy as np
from scipy.ndimage import label as connected
from tools.anatomy_sources.spl_limbic_source import CODES, RESEARCH, sha, require, apply_affine


def prepare_label_boundaries(array, affine, labels, source, write_payload):
    rows, audits = [], []
    require(np.array_equal(affine[:3,:3].T @ affine[:3,:3],np.eye(3)), 'This source is an orthonormal 1mm label grid')
    for label in labels:
        code=label['code']; cells=np.argwhere(array==code)
        cell_set=set(map(tuple,cells))
        corner_map={}; source_corners=[]; triangles=[]; provenance=[]
        for cell in cells:
            for axis in range(3):
                others=[a for a in range(3) if a!=axis]
                for sign in (-1,1):
                    neighbor=cell.copy(); neighbor[axis]+=sign
                    if tuple(neighbor) in cell_set: continue
                    corners=[]
                    for u,v in [(-1,-1),(1,-1),(1,1),(-1,1)]:
                        doubled=cell*2; doubled[axis]+=sign; doubled[others[0]]+=u; doubled[others[1]]+=v
                        key=tuple(doubled)
                        if key not in corner_map:
                            corner_map[key]=len(source_corners); source_corners.append(doubled*.5)
                        corners.append(corner_map[key])
                    xyz=apply_affine(affine,np.asarray([source_corners[i] for i in corners]))
                    outward=affine[:3,axis]*sign
                    if np.dot(np.cross(xyz[1]-xyz[0],xyz[2]-xyz[0]),outward)<0: corners=[corners[0],corners[3],corners[2],corners[1]]
                    triangles.extend([(corners[0],corners[1],corners[2]),(corners[0],corners[2],corners[3])])
                    provenance.append([*map(int,cell),axis,sign])
        positions=apply_affine(affine,np.asarray(source_corners)).astype('<f4')
        indices=np.asarray(triangles,dtype='<u4')
        pbytes,ibytes=positions.tobytes(),indices.tobytes()
        payload=struct.pack('<4sIII',b'HVX1',len(positions),len(indices),0)+pbytes+ibytes
        xyz=positions.astype(float)[indices]
        normals=np.cross(xyz[:,1]-xyz[:,0],xyz[:,2]-xyz[:,0])
        areas=np.linalg.norm(normals,axis=1)*.5
        require(np.array_equal(areas,np.full(len(indices),.5)), 'A label boundary triangle is not a half square millimetre')
        volume=float(np.einsum('ij,ij->i',xyz[:,0],np.cross(xyz[:,1],xyz[:,2])).sum()/6.)
        require(volume==len(cells), 'Oriented boundary volume does not equal complete categorical voxel count')
        require(np.array_equal(positions*2,np.round(positions*2)), 'Source cell corner precision changed')
        # Independent face oracle: six shifted occupancy arrays, not the generator cell-set traversal.
        mask=array==code; oracle=set()
        for axis in range(3):
            for sign in (-1,1):
                adjacent=np.zeros_like(mask)
                target=[slice(None)]*3; neighbor=[slice(None)]*3
                target[axis]=slice(None,-1) if sign==1 else slice(1,None)
                neighbor[axis]=slice(1,None) if sign==1 else slice(None,-1)
                adjacent[tuple(target)]=mask[tuple(neighbor)]
                oracle.update((*map(int,cell),axis,sign) for cell in np.argwhere(mask & ~adjacent))
        require(len(provenance)==len(oracle) and set(map(tuple,provenance))==oracle, 'Generated faces differ from independent full-grid exposed-face oracle')
        for face,record in enumerate(provenance):
            i,j,k,axis,sign=record
            outward=affine[:3,axis]*sign
            require(np.array_equal(normals[2*face],outward) and np.array_equal(normals[2*face+1],outward), 'Boundary winding is not outward')
            expected_center=apply_affine(affine,(np.array([i,j,k])+np.eye(3)[axis]*sign*.5)[None,:])[0]
            vertex_ids=np.unique(indices[2*face:2*face+2])
            require(len(vertex_ids)==4 and np.array_equal(positions[vertex_ids].mean(0),expected_center), 'Boundary quad is not the source cell face')
        counts=Counter()
        signed=Counter()
        for tri in indices:
            for u,v in zip(tri,np.roll(tri,-1)):
                key=(min(int(u),int(v)),max(int(u),int(v)))
                counts[key]+=1; signed[key]+=1 if int(u)<int(v) else -1
        require(all(value==0 for value in signed.values()), 'Boundary has an unmatched oriented edge')
        low,high=cells.min(0),cells.max(0)
        crop=tuple(slice(int(a),int(b)+1) for a,b in zip(low,high))
        component_sizes={}
        for connectivity in (6,26):
            structure=np.ones((3,3,3),dtype='u1') if connectivity==26 else np.array([[[int(abs(i-1)+abs(j-1)+abs(k-1)<=1) for k in range(3)] for j in range(3)] for i in range(3)],dtype='u1')
            comp,n=connected(mask[crop],structure)
            component_sizes[str(connectivity)]=sorted(np.bincount(comp.ravel())[1:].tolist(),reverse=True)
        face_bytes=np.asarray(provenance,dtype='<i2').tobytes()
        face_row={**write_payload(f'label-{code}-faces.bin.gz',face_bytes),'dtype':'<i2','components':5,'count':len(provenance),'layout':['i','j','k','native_axis','outward_sign']}
        row={**write_payload(f'label-{code}.mesh.gz',payload),'code':code,'name':label['name'],
             'kind':'exact-categorical-voxel-cell-boundary','structure':label['sourceName'],
             'source':source,'sourceLabelCode':code,'sourceVoxelCount':len(cells),
             'coordinateSystem':'RAS','spaceUnits':'mm','sourceAffine':np.eye(4).tolist(),'voxelToRAS':np.eye(4).tolist(),
             'sourceLabelVoxelToRAS':affine.tolist(),'positionsAlreadyRAS':True,'sourceGridPosition':False,
             'vertexCount':len(positions),'triangleCount':len(indices),'exposedFaceCount':len(provenance),
             'positionByteSHA256':sha(pbytes),'indexByteSHA256':sha(ibytes),
             'layout':{'headerBytes':16,'magic':'HVX1','byteOrder':'little','headerFields':['magic[4]','vertexCount:uint32','triangleCount:uint32','reserved:uint32=0'],
                       'positions':{'offset':16,'dtype':'<f4','components':3,'count':len(positions)},
                       'triangles':{'offset':16+len(pbytes),'dtype':'<u4','components':3,'count':len(indices)}},
             'boundsRAS':[positions.min(0).tolist(),positions.max(0).tolist()],
             'faceProvenance':face_row,'allComponentsAndCavitiesRetained':True,'allCellFacesExact':True,
             'smoothedOrRepairedByPrimer':False,'interpretation':'Exact boundaries of this original categorical label class, including voxel stair steps and small components. This is not an independently validated anatomical truth or a smooth patient surface.'}
        rows.append(row)
        audits.append({'code':code,'source_voxel_count':len(cells),'connected_component_sizes':component_sizes,
                       'all_exposed_faces_equal_independent_full_grid_oracle':True,'face_count':len(provenance),'vertex_count':len(positions),'triangle_count':len(indices),
                       'every_quad_has_four_exact_half_integer_RAS_corners':True,'every_triangle_area_mm2':.5,'surface_area_mm2':float(areas.sum()),
                       'signed_enclosed_volume_mm3':volume,'volume_equals_all_source_voxels':True,'every_triangle_winds_outward':True,
                       'edge_incidence_histogram':{str(k):v for k,v in sorted(Counter(counts.values()).items())},
                       'oriented_edge_balance_everywhere_zero':True,'nonmanifold_source_contacts_preserved':True,'all_faces_and_components_preserved':True,
                       'position_sha256':sha(pbytes),'indices_sha256':sha(ibytes),'face_provenance_sha256':sha(face_bytes)})
        print('Exact cell boundary',code,len(provenance),'faces',len(indices),'triangles',flush=True)
    proof={'schema_version':1,'source':source,'source_affine':affine.tolist(),'method':'Expose all six faces of each selected voxel whose neighbor is not the same code; retain cavity and small-component faces; triangulate each exact world-space unit square outward without smoothing, fitting, deletion or closing.',
           'independent_oracle':'Full-grid boolean occupancy shifted in each of six axis directions; exact equality with the emitted unique face records.',
           'topology_note':'Shared coincident corners are indexed once. Edge/corner-touching source voxels can produce nonmanifold contacts; these are preserved, not repaired.',
           'clinical_approval':False,'rows':audits}
    (RESEARCH/'label-boundary-proof.json').write_text(json.dumps(proof,indent=2)+'\n')
    return rows
