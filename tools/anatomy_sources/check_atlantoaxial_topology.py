"""Non-repairing topology inspection of native craniovertebral exports."""
import hashlib,json,math,struct
from collections import Counter,defaultdict
from pathlib import Path


def topology(vertices,faces):
    # Normal seams duplicate exported positions; exact coordinate welding is
    # for this measurement only and never changes the source geometry.
    unique={}; remap=[]
    for point in vertices:
        key=tuple(point)
        if key not in unique:unique[key]=len(unique)
        remap.append(unique[key])
    edges=defaultdict(list);parent=list(range(len(faces)));degenerate=0;volume=0.
    def find(x):
        while parent[x]!=x:parent[x]=parent[parent[x]];x=parent[x]
        return x
    for n,face in enumerate(faces):
        ids=[remap[i] for i in face]
        a,b,c=[vertices[i] for i in face]
        u=[b[i]-a[i] for i in range(3)];v=[c[i]-a[i] for i in range(3)]
        cross=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]]
        if len(set(ids))<3 or sum(x*x for x in cross)<=1e-24:degenerate+=1
        volume+=sum(a[i]*cross[i] for i in range(3))/6
        for x,y in zip(ids,ids[1:]+ids[:1]):edges[tuple(sorted((x,y)))].append((n,1 if x<y else -1))
    for incident in edges.values():
        for n,_ in incident[1:]:parent[find(n)]=find(incident[0][0])
    counts=Counter(find(i) for i in range(len(faces)))
    boundary=sum(len(v)==1 for v in edges.values());nonmanifold=sum(len(v)>2 for v in edges.values())
    inconsistent=sum(len(v)==2 and v[0][1]==v[1][1] for v in edges.values())
    return {'unique_exact_positions':len(unique),'triangles':len(faces),'edge_connected_components':sorted(counts.values(),reverse=True),'boundary_edges':boundary,'nonmanifold_edges':nonmanifold,'inconsistent_two_face_edges':inconsistent,'degenerate_triangles':degenerate,'signed_volume_source_units_cubed':volume if not(boundary or nonmanifold or inconsistent or degenerate) else None,'limits':'Exact-position seam welding only for measurement. Closed topology does not prove anatomical accuracy, absence of self-intersection or valid tissue volume.'}


if __name__=='__main__':
    directory=Path('docs/msk-atlantoaxial-source-review')
    audit=json.loads((directory/'export-audit.json').read_text());rows=[]
    for part in audit['parts']:
        data=Path(part['file']).read_bytes()
        if hashlib.sha256(data).hexdigest()!=part['sha256']:raise ValueError('Changed export')
        magic,n,k=struct.unpack('<4sII',data[:12])
        if magic!=b'BP3D' or len(data)!=12+n*24+k*4:raise ValueError('Invalid export')
        vertices=list(struct.iter_unpack('<fff',data[12:12+n*12]));faces=list(struct.iter_unpack('<III',data[12+n*24:]))
        if any(not math.isfinite(x) for p in vertices for x in p) or any(i>=n for f in faces for i in f):raise ValueError('Invalid geometry')
        rows.append({'name':part['name'],'sha256':part['sha256'],**topology(vertices,faces)})
    (directory/'topology.json').write_text(json.dumps({'geometry_changed':False,'clinical_approval':False,'parts':rows},indent=2)+'\n')
    print(json.dumps(rows,indent=2))
