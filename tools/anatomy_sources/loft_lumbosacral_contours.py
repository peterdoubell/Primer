"""Open-ended contour-loft candidates preserving every sampled source ring.

The connecting faces are newly derived, not measured tissue between MRI planes.
"""
from pathlib import Path
import gzip,hashlib,json,struct,sys
from collections import defaultdict,Counter
import numpy as np
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'output/msk-lumbosacral-sub03/surface-candidates';DOC=ROOT/'docs/msk-lumbosacral-nerve-source-review'
sys.path.insert(0,str(ROOT))
from tools.anatomy_sources.check_atlantoaxial_topology import topology


def strip(a,b,ai,bi):
    # Preserve cyclic order. Reserve the first/last quads so the seam is not
    # revisited as an interior edge by a degenerate all-around fan.
    pair=np.linalg.norm(a[:,None,:]-b[None,:,:],axis=2);start=np.unravel_index(np.argmin(pair),pair.shape)
    ia=np.roll(np.arange(len(a)),-start[0]);ib=np.roll(np.arange(len(b)),-start[1]);a=a[ia];b=b[ib];ga=ai+ia;gb=bi+ib;n,m=len(a),len(b)
    distance=np.linalg.norm(a[:,None,:]-b[None,:,:],axis=2);cost=np.full((n,m),np.inf);step=np.zeros((n,m),np.uint8);cost[1,1]=0
    for i in range(1,n):
        for j in range(1,m):
            if i==1 and j==1:continue
            left=cost[i-1,j] if i>1 else np.inf;down=cost[i,j-1] if j>1 else np.inf
            if left<=down:cost[i,j]=left+distance[i,j];step[i,j]=1
            else:cost[i,j]=down+distance[i,j];step[i,j]=2
    faces=[];i,j=n-1,m-1
    while (i,j)!=(1,1):
        if step[i,j]==1:faces.append([ga[i-1],ga[i],gb[j]]);i-=1
        elif step[i,j]==2:faces.append([ga[i],gb[j],gb[j-1]]);j-=1
        else:raise ValueError('Unreachable strip state')
    faces.reverse();faces=[[ga[0],ga[1],gb[0]],[ga[1],gb[1],gb[0]]]+faces+[[ga[-1],ga[0],gb[-1]],[ga[0],gb[0],gb[-1]]]
    assert len(faces)==n+m
    return np.asarray(faces,dtype=np.uint32),{'lower_seam_vertex':int(ia[0]),'upper_seam_vertex':int(ib[0]),'cross_edge_cost_mm':float(cost[-1,-1])}


def section(vertices,faces,height):
    nodes={};positions=[];links=[]
    for face in faces:
        crossing=[]
        for a,b in zip(face,np.roll(face,-1)):
            a,b=sorted((int(a),int(b)));p,q=vertices[[a,b]]
            if (p[2]-height)*(q[2]-height)<0:
                key=(a,b)
                if key not in nodes:
                    nodes[key]=len(positions);positions.append(p+(height-p[2])/(q[2]-p[2])*(q-p))
                crossing.append(nodes[key])
        assert len(crossing)==2
        links.append(crossing)
    graph=defaultdict(list)
    for a,b in links:graph[a].append(b);graph[b].append(a)
    assert all(len(v)==2 for v in graph.values())
    order=[0];previous=-1;current=0
    while True:
        nxt=next(n for n in graph[current] if n!=previous)
        if nxt==0:break
        assert nxt not in order;order.append(nxt);previous,current=current,nxt
    assert len(order)==len(positions)
    return np.asarray(positions)[order,:2]


def crossings(p):
    e=np.roll(p,-1,axis=0)-p;delta=p[None,:,:]-p[:,None,:]
    def cross(a,b):return a[...,0]*b[...,1]-a[...,1]*b[...,0]
    den=cross(e[:,None,:],e[None,:,:]);valid=np.abs(den)>1e-10;t=np.zeros_like(den);u=np.zeros_like(den)
    np.divide(cross(delta,e[None,:,:]),den,out=t,where=valid);np.divide(cross(delta,e[:,None,:]),den,out=u,where=valid)
    allowed=np.triu(np.ones(den.shape,bool),2);allowed[0,-1]=False
    return int(np.count_nonzero(allowed&valid&(t>0)&(t<1)&(u>0)&(u<1)))


def inside(p,q):
    a=q;b=np.roll(q,-1,axis=0);crosses=(a[None,:,1]>p[:,None,1])!=(b[None,:,1]>p[:,None,1]);x=np.zeros(crosses.shape)
    np.divide((p[:,None,1]-a[None,:,1])*(b-a)[None,:,0],(b-a)[None,:,1],out=x,where=crosses);x+=a[None,:,0]
    return ((crosses&(p[:,None,0]<x)).sum(axis=1)%2)==1


def main():
    source=json.loads((DOC/'default-curve-reconstruction.json').read_text());images=json.loads((DOC/'annotation-and-image-audit.json').read_text());inverse=np.linalg.inv(images['images']['CISS']['selected_affine']);OUT.mkdir(parents=True,exist_ok=True);parts={};audit=[];sections={}
    for category,color in [('cord','#79ccd7'),('dura','#d9b66a')]:
        rows=sorted([r for r in source['curves'] if r['category']==category],key=lambda r:r['native_slice']);rings=[];offsets=[];count=0
        for row in rows:
            path=ROOT/row['file'];assert hashlib.sha256(path.read_bytes()).hexdigest()==row['sha256'];curve=np.load(path)['default_curve_lps_mm'];assert np.array_equal(curve[0],curve[-1]);ring=curve[:-1];assert len(np.unique(ring,axis=0))==len(ring);assert row['signed_sampled_area_lps_xy_mm2']>0;offsets.append(count);count+=len(ring);rings.append(ring)
        vertices=np.concatenate(rings);faces=[];strips=[]
        for i in range(len(rings)-1):
            assert rows[i+1]['native_slice']==rows[i]['native_slice']+1
            f,info=strip(rings[i],rings[i+1],offsets[i],offsets[i+1]);strips.append(dict(info,lower_slice=rows[i]['native_slice'],faces=f));faces.append(f)
        faces=np.concatenate(faces);check=topology(vertices.tolist(),faces.tolist());assert not any(check[k] for k in ['nonmanifold_edges','inconsistent_two_face_edges','degenerate_triangles']);assert check['boundary_edges']==len(rings[0])+len(rings[-1]);assert check['edge_connected_components']==[len(faces)]
        incidence=Counter(tuple(sorted((int(a),int(b)))) for f in faces for a,b in zip(f,np.roll(f,-1)));boundary={edge for edge,n in incidence.items() if n==1};expected=set()
        for ring_index in [0,len(rings)-1]:
            ids=np.arange(len(rings[ring_index]))+offsets[ring_index];expected.update(tuple(sorted((int(a),int(b)))) for a,b in zip(ids,np.roll(ids,-1)))
        assert boundary==expected
        vox=(vertices*[-1,-1,1])@inverse[:3,:3].T+inverse[:3,3];section_rows=[]
        for band in strips:
            for fraction in [.25,.5,.75]:
                height=band['lower_slice']+fraction;polygon=section(vox,band['faces'],height);hits=crossings(polygon);assert hits==0,(category,height,hits);sections[(category,height)]=polygon;section_rows.append({'native_slice_position':height,'vertices':len(polygon),'strict_crossings':hits,'closed_components':1})
        tri=vertices[faces];cross=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);normals=np.zeros_like(vertices)
        for corner in range(3):np.add.at(normals,faces[:,corner],cross)
        norm=np.linalg.norm(normals,axis=1);assert np.all(norm>0);normals=(normals/norm[:,None]).astype('<f4');positions=vertices.astype('<f4');assert np.array_equal(positions.astype(float),vertices)
        raw=struct.pack('<4sII',b'BP3D',len(vertices),faces.size)+positions.tobytes()+normals.tobytes()+faces.astype('<u4').tobytes();name=category+'-open-envelope.bin.gz';compressed=gzip.compress(raw,mtime=0);(OUT/name).write_bytes(compressed);assert gzip.decompress(compressed)==raw
        np.savez_compressed(OUT/(category+'-open-envelope.npz'),vertices_lps_mm=vertices,faces=faces,ring_offsets=np.asarray(offsets),native_slice_indices=np.asarray([r['native_slice'] for r in rows]))
        parts[category]={'id':category,'name':category.capitalize()+' contour envelope · partial','file':name,'sha256':hashlib.sha256(compressed).hexdigest(),'color':color,'vertices':len(vertices),'triangles':len(faces),'bounds':[vertices.min(0).tolist(),vertices.max(0).tolist()]}
        audit.append({'category':category,'source_curves':[{'member':r['member'],'sha256':r['sha256']} for r in rows],'vertices':len(vertices),'triangles':len(faces),'all_sampled_ring_positions_preserved':True,'topology':check,'boundary_matches_only_first_last_rings':True,'sampled_sections':section_rows,'strip_correspondence':[dict((k,v) for k,v in s.items() if k!='faces') for s in strips]})
        print(category,len(vertices),'vertices',len(faces),'triangles; expected open boundaries:',check['boundary_edges'],flush=True)
    pairs=[]
    for (category,height),polygon in sections.items():
        if category!='cord':continue
        contained=inside(polygon,sections[('dura',height)]);pairs.append({'native_slice_position':height,'cord_section_points':len(polygon),'outside_dura_section':int((~contained).sum())})
    report={'parts':audit,'sampled_inter_surface_containment':pairs,'source_reconstruction_sha256':hashlib.sha256((DOC/'default-curve-reconstruction.json').read_bytes()).hexdigest(),'method':'Piecewise triangular strips joining adjacent sampled rings. Dynamic programming minimizes cross-ring edge-length cost with fixed seam quads. Every sampled ring vertex retained; only repeated closure endpoints deduplicated. No end caps or smoothing.','limits':['Connecting surfaces between sampled MRI planes are derived, not measured.','Three section fractions per interval do not prove absence of all continuous self-intersections or cross-surface intersections.','Default-curve assumptions and source coverage limits remain applicable.','A dural contour envelope is not a measured dura wall thickness or complete CSF tissue volume.'],'clinical_approval':False,'runtime_promoted':False}
    (DOC/'open-envelope-loft-audit.json').write_text(json.dumps(report,indent=2)+'\n');print('Between-plane containment violations:',sum(r['outside_dura_section'] for r in pairs))
    manifest={'dataset':'Liu et al. sub-03 · open cord/dura contour envelopes','source_url':'https://doi.org/10.6084/m9.figshare.c.7372564','license':'CC BY 4.0','license_url':'https://creativecommons.org/licenses/by/4.0/','coordinate_system':{'basis':'LPS','units':'millimetres','unit_meters':.001,'display_basis':'native-lps-to-x-left-y-superior-z-anterior'},'parts':parts,'regions':{'spine':{'title':'Sub-03 cord and dura · partial source envelopes','side':'midline','parts':[{'id':k,'layer':k} for k in parts],'layers':[['cord','Cord envelope'],['dura','Dural envelope']],'source_up_range':[min(p['bounds'][0][2] for p in parts.values())-1,max(p['bounds'][1][2] for p in parts.values())+1]}},'viewer_notes':report['limits']+['Source: Liu, Zhang, Zhou, Xu, Chu and Jia (2024), Figshare collection 10.6084/m9.figshare.c.7372564. CC BY 4.0. Derived default curves and uncapped triangulated envelopes; original source points retained separately.'],'clinical_approval':False,'runtime_promoted':False}
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')


if __name__=='__main__':main()
