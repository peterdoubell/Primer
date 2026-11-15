"""Supplement the independent screen's demonstrated coplanar blind spot."""
from pathlib import Path
import gzip,hashlib,json,struct,sys
from collections import Counter
import numpy as np
from vtkmodules.vtkCommonCore import vtkIdList,vtkPoints,vtkVersion
from vtkmodules.vtkCommonDataModel import vtkPolyData,vtkCellArray,vtkStaticCellLocator
from vtkmodules.util.numpy_support import numpy_to_vtk,numpy_to_vtkIdTypeArray
ROOT=Path(__file__).resolve().parents[2];PACKAGE=ROOT/'output/msk-lumbosacral-sub03/surface-candidates';OUT=ROOT/'docs/msk-lumbosacral-nerve-source-review'
DIST=float(sys.argv[1]) if len(sys.argv)>1 else 1e-8
assert DIST in (1e-8,1e-4)
AREA=1e-10


def area2(p):
    if len(p)<3:return 0.
    return .5*float(np.sum(p[:,0]*np.roll(p[:,1],-1)-p[:,1]*np.roll(p[:,0],-1)))


def clipped_area(a,b,normal):
    axis=int(np.argmax(np.abs(normal)));keep=[i for i in range(3) if i!=axis];origin=a[0];subject=(a-origin)[:,keep];clip=(b-origin)[:,keep]
    if area2(clip)<0:clip=clip[::-1]
    polygon=[p.copy() for p in subject]
    for c,d in zip(clip,np.roll(clip,-1,axis=0)):
        if not polygon:break
        edge=d-c
        def side(p):return edge[0]*(p[1]-c[1])-edge[1]*(p[0]-c[0])
        eps=DIST*np.linalg.norm(edge);output=[];previous=polygon[-1];before=side(previous)
        for current in polygon:
            after=side(current);p_in=before>=-eps;c_in=after>=-eps
            if p_in!=c_in:
                denominator=before-after
                if denominator!=0:output.append(previous+before/denominator*(current-previous))
            if c_in:output.append(current)
            previous=current;before=after
        polygon=output
    return abs(area2(np.asarray(polygon)))/abs(normal[axis]) if polygon else 0.


def normal(triangle):
    n=np.cross(triangle[1]-triangle[0],triangle[2]-triangle[0]);return n/np.linalg.norm(n)


def main():
    controls=[]
    fixtures=[('coplanar_overlap',[[-1,-1,0],[1,-1,0],[0,1,0]],[[-.2,0,0],[.2,0,0],[0,.4,0]],.08),('folded_shared_edge',[[0,0,0],[1,0,0],[0,1,0]],[[1,0,0],[0,0,0],[.25,.25,0]],.125),('valid_shared_edge',[[0,0,0],[1,0,0],[1,1,0]],[[0,0,0],[1,1,0],[0,1,0]],0.),('separated',[[0,0,0],[1,0,0],[0,1,0]],[[3,0,0],[4,0,0],[3,1,0]],0.)]
    for name,a,b,expected in fixtures:
        a=np.asarray(a,float);b=np.asarray(b,float);observed=clipped_area(a,b,normal(a));assert abs(observed-expected)<1e-12;controls.append({'case':name,'expected_area_mm2':expected,'observed_area_mm2':observed})
    locator_controls=[]
    for name,a,b,expected in fixtures:
        v=np.asarray(a+b,float);f=np.asarray([[0,1,2],[3,4,5]],np.int64);p=vtkPoints();p.SetData(numpy_to_vtk(v,deep=True));c=vtkCellArray();c.SetCells(2,numpy_to_vtkIdTypeArray(np.column_stack([np.full(2,3,np.int64),f]).ravel(),deep=True));d=vtkPolyData();d.SetPoints(p);d.SetPolys(c);tree=vtkStaticCellLocator();tree.SetDataSet(d);tree.BuildLocator()
        for i in [0,1]:
            tri=v[f[i]];lo=tri.min(0)-DIST;hi=tri.max(0)+DIST;ids=vtkIdList();tree.FindCellsWithinBounds([lo[0],hi[0],lo[1],hi[1],lo[2],hi[2]],ids);found=[ids.GetId(k) for k in range(ids.GetNumberOfIds())]
            if expected>0:assert 1-i in found
            locator_controls.append({'case':name,'query_face':i,'candidate_faces':found})
    manifest=json.loads((PACKAGE/'manifest.json').read_text());vertices=[];faces=[];sources=[];components=[];offset=0
    for name in ['cord','dura']:
        part=manifest['parts'][name];raw=(PACKAGE/part['file']).read_bytes();assert hashlib.sha256(raw).hexdigest()==part['sha256'];decoded=gzip.decompress(raw);magic,n,k=struct.unpack('<4sII',decoded[:12]);assert magic==b'BP3D' and len(decoded)==12+n*24+k*4
        v=np.frombuffer(decoded,dtype='<f4',count=n*3,offset=12).reshape(-1,3).astype(float);f=np.frombuffer(decoded,dtype='<u4',offset=12+n*24).reshape(-1,3).astype(np.int64);vertices.append(v);faces.append(f+offset);offset+=len(v);components.extend([name]*len(f));sources.append({'part':name,'sha256':part['sha256'],'faces':len(f)})
    vertices=np.vstack(vertices);faces=np.vstack(faces);triangles=vertices[faces];normals=np.cross(triangles[:,1]-triangles[:,0],triangles[:,2]-triangles[:,0]);length=np.linalg.norm(normals,axis=1);assert np.all(length>0);normals/=length[:,None]
    points=vtkPoints();points.SetData(numpy_to_vtk(vertices,deep=True));cells=vtkCellArray();packed=np.column_stack([np.full(len(faces),3,np.int64),faces]).ravel();cells.SetCells(len(faces),numpy_to_vtkIdTypeArray(packed,deep=True));poly=vtkPolyData();poly.SetPoints(points);poly.SetPolys(cells);locator=vtkStaticCellLocator();locator.SetDataSet(poly);locator.BuildLocator();candidate_list=vtkIdList();counts=Counter();overlaps=[]
    for i,triangle in enumerate(triangles):
        lo=triangle.min(0)-DIST;hi=triangle.max(0)+DIST;bounds=[lo[0],hi[0],lo[1],hi[1],lo[2],hi[2]];candidate_list.Reset();locator.FindCellsWithinBounds(bounds,candidate_list);ids=np.array([candidate_list.GetId(k) for k in range(candidate_list.GetNumberOfIds()) if candidate_list.GetId(k)>i],dtype=np.int64);counts['broad_phase_pairs']+=len(ids)
        if not len(ids):continue
        distance=np.max(np.abs((triangles[ids]-triangle[0])@normals[i]),axis=1);ids=ids[distance<=DIST]
        if not len(ids):continue
        reverse=np.max(np.abs(np.einsum('kij,kj->ki',triangle[None,:,:]-triangles[ids,0,None,:],normals[ids])),axis=1);ids=ids[reverse<=DIST]
        for j in ids:
            pair='-'.join(sorted([components[i],components[j]]));counts['coplanar_pairs']+=1;counts[pair]+=1;area=clipped_area(triangle,triangles[j],normals[i])
            if area>AREA:overlaps.append({'faces':[i,int(j)],'components':[components[i],components[j]],'area_mm2':area,'shared_vertex_count':len(set(faces[i])&set(faces[j]))})
        if i and i%10000==0:print('Processed',i,'faces',flush=True)
    report={'engine':'VTK '+vtkVersion.GetVTKVersion()+' bounds locator; NumPy convex polygon clipping','sources':sources,'faces':len(faces),'distance_tolerance_mm':DIST,'positive_area_threshold_mm2':AREA,'controls':controls,'locator_controls':locator_controls,'counts':dict(counts),'positive_area_overlaps':overlaps,'input_geometry_modified':False,'limits':['At the wider tolerance, projected overlap is a conservative near-planar warning, not proof of actual intersection.','Tests positive-area overlap between numerically coplanar faces; isolated tangencies are not classified as area overlaps.','Uses floating-point tolerances, not exact arithmetic.','Complements the independent non-coplanar screen; does not establish anatomical accuracy.'],'clinical_approval':False,'runtime_promoted':False}
    (OUT/('coplanar-overlap-screen.json' if DIST==1e-8 else 'near-planar-overlap-screen.json')).write_text(json.dumps(report,indent=2)+'\n');print('Pairs',dict(counts),'positive-area overlaps',len(overlaps))


if __name__=='__main__':main()
