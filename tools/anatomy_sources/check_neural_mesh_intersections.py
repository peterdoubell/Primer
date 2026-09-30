"""Independent face-intersection screen with explicit positive/negative controls."""
from pathlib import Path
import gzip,hashlib,json,struct,importlib.metadata
import numpy as np
import pymeshlab
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'docs/msk-lumbosacral-nerve-source-review';PACKAGE=ROOT/'output/msk-lumbosacral-sub03/surface-candidates'


def screen(vertices,faces):
    mesh=pymeshlab.Mesh(vertex_matrix=np.asarray(vertices,dtype=np.float64),face_matrix=np.asarray(faces,dtype=np.int32));group=pymeshlab.MeshSet();group.add_mesh(mesh)
    before_v=group.current_mesh().vertex_matrix().copy();before_f=group.current_mesh().face_matrix().copy();group.compute_selection_by_self_intersections_per_face();current=group.current_mesh();selected=np.flatnonzero(current.face_selection_array()).tolist()
    assert np.array_equal(current.vertex_matrix(),before_v) and np.array_equal(current.face_matrix(),before_f)
    assert np.array_equal(before_v,np.asarray(vertices)) and np.array_equal(before_f,np.asarray(faces))
    return selected


def main():
    fixtures=[
      ('separated', [[-1,-1,0],[1,-1,0],[0,1,0],[-1,-1,2],[1,-1,2],[0,1,2]],[[0,1,2],[3,4,5]],False),
      ('transverse_crossing',[[-1,-1,0],[1,-1,0],[0,1,0],[0,-.5,-1],[0,-.5,1],[.5,.5,0]],[[0,1,2],[3,4,5]],True),
      ('coplanar_overlap',[[-1,-1,0],[1,-1,0],[0,1,0],[-.2,0,0],[.2,0,0],[0,.4,0]],[[0,1,2],[3,4,5]],True),
      ('crossing_shared_vertex',[[0,0,0],[2,0,0],[0,2,0],[1,1,-1],[1,1,1]],[[0,1,2],[0,3,4]],True),
      ('valid_shared_edge',[[0,0,0],[1,0,0],[1,1,0],[0,1,0]],[[0,1,2],[0,2,3]],False),
      ('folded_shared_edge',[[0,0,0],[1,0,0],[0,1,0],[.25,.25,0]],[[0,1,2],[1,0,3]],True),
    ]
    controls=[]
    for name,v,f,expected in fixtures:
        selected=screen(v,f);controls.append({'fixture':name,'expected_intersection':expected,'selected_faces':selected,'matches_expected':bool(selected)==expected});print(name,selected,flush=True)
    manifest=json.loads((PACKAGE/'manifest.json').read_text());parts={};results=[]
    for name in ['cord','dura']:
        part=manifest['parts'][name];path=PACKAGE/part['file'];raw=path.read_bytes();assert hashlib.sha256(raw).hexdigest()==part['sha256'];decoded=gzip.decompress(raw);magic,n,k=struct.unpack('<4sII',decoded[:12]);assert magic==b'BP3D' and len(decoded)==12+n*24+k*4
        vertices=np.frombuffer(decoded,dtype='<f4',count=n*3,offset=12).reshape(-1,3).astype(float);faces=np.frombuffer(decoded,dtype='<u4',offset=12+n*24).reshape(-1,3);parts[name]=(vertices,faces)
        selected=screen(vertices,faces);results.append({'part':name,'source_mesh_sha256':part['sha256'],'faces':len(faces),'selected_face_count':len(selected),'selected_faces':selected});print(name,len(selected),'selected faces',flush=True)
    cv,cf=parts['cord'];dv,df=parts['dura'];selected=screen(np.vstack([cv,dv]),np.vstack([cf,df+len(cv)]));combined={'faces':len(cf)+len(df),'selected_face_count':len(selected),'selected_cord_faces':[i for i in selected if i<len(cf)],'selected_dura_faces':[i-len(cf) for i in selected if i>=len(cf)]}
    report={'engine':'PyMeshLab '+importlib.metadata.version('pymeshlab'),'filter':'compute_selection_by_self_intersections_per_face','controls':controls,'parts':results,'combined':combined,'input_geometry_unchanged':True,'limits':['A numerical library screen is not an exact-arithmetic proof or anatomical validation.','Any control failure limits the interpretation of zero selected faces.','Open source boundaries remain intentional; no repair, closure, smoothing or face deletion performed.'],'clinical_approval':False,'runtime_promoted':False}
    (OUT/'independent-intersection-screen.json').write_text(json.dumps(report,indent=2)+'\n');print('Combined selected faces:',len(selected));print('All controls pass:',all(c['matches_expected'] for c in controls))


if __name__=='__main__':main()
