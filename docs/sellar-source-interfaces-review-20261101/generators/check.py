from pathlib import Path
import gzip,hashlib,json,struct,itertools
import numpy as np
from xml.etree import ElementTree as ET
R=Path.cwd();D=R/'.research/sellar-source-interfaces-20261101';sha=lambda b:hashlib.sha256(b).hexdigest();audit=json.loads((D/'audit.json').read_bytes());manifest=json.loads((D/'manifest.json').read_bytes());diagrams=json.loads((D/'schematics.json').read_bytes());m=json.loads((R/'web/anatomy/spl-nac-limbic/manifest.json').read_bytes());v=m['labelVolume'];raw=gzip.decompress((R/'web/anatomy/spl-nac-limbic'/v['file']).read_bytes());assert sha(raw)==audit['labelDecodedSHA256']==manifest['labelDecodedSHA256'];labels=np.frombuffer(raw,dtype=v['dtype']).reshape(v['shape'],order='F');A=np.asarray(v['voxelToRAS']);inverse=np.linalg.inv(A);codes=sorted(r['code']for r in manifest['sourceClasses']);expected=[]
# Independent cell-centred six-neighbour enumeration, rather than shifted full-grid slabs.
for code in codes:
 owners=np.argwhere(labels==code)
 for axis,sign in itertools.product(range(3),[-1,1]):
  adjacent=owners.copy();adjacent[:,axis]+=sign;inside=np.all((adjacent>=0)&(adjacent<np.asarray(labels.shape)),axis=1);p=owners[inside];q=adjacent[inside];other=labels[tuple(q.T)];keep=np.isin(other,codes)&(other>code);expected.extend([*map(int,cell),axis,sign,code,int(neighbour)]for cell,neighbour in zip(p[keep],other[keep]))
expected={tuple(r)for r in expected};assert len(expected)==audit['sourceFaceCount']==652;found=set();counts={};reconstructed=0;sections=0;vertices=0;triangles=0;SVG_NS={'s':'http://www.w3.org/2000/svg'}
for model in manifest['models']:
 packed=(D/'package'/model['file']).read_bytes();assert sha(packed)==model['gzipSHA256'];data=gzip.decompress(packed);assert sha(data)==model['decodedSHA256'];magic,N,T,flag=struct.unpack('<4sIII',data[:16]);assert magic==b'HVX1'and flag==0 and N==model['vertices']and T==model['triangles']and len(data)==16+N*12+T*12;pos=np.frombuffer(data,dtype='<f4',count=N*3,offset=16).reshape(-1,3).astype(float);idx=np.frombuffer(data,dtype='<u4',offset=16+N*12).reshape(-1,3);assert idx.max()<N and np.isfinite(pos).all();natives=np.column_stack([pos,np.ones(N)])@inverse.T;assert np.array_equal(natives[:,:3]*2,np.round(natives[:,:3]*2));source=model['sourceFaceProvenance'];fpacked=(D/'package'/source['file']).read_bytes();assert sha(fpacked)==source['gzipSHA256'];fraw=gzip.decompress(fpacked);assert sha(fraw)==source['decodedSHA256'];faces=np.frombuffer(fraw,dtype='<i4').reshape(-1,7);assert len(faces)*2==T
 for k,f in enumerate(faces):
  record=tuple(map(int,f));assert record in expected and record not in found;found.add(record);p=f[:3];axis=int(f[3]);sign=int(f[4]);q=p.copy();q[axis]+=sign;assert int(labels[tuple(p)])==f[5]and int(labels[tuple(q)])==f[6]and list(map(int,f[5:]))==model['sourceCodes'];actual=natives[np.unique(idx[k*2:k*2+2]),:3];assert len(actual)==4
  wanted={tuple(p+np.eye(3)[axis]*sign*.5+sum(np.eye(3)[other]*delta*.5 for other,delta in zip([i for i in range(3)if i!=axis],offsets)))for offsets in itertools.product([-1,1],repeat=2)};assert set(map(tuple,actual))==wanted
  xyz=pos[idx[k*2:k*2+2]];normal=np.cross(xyz[:,1]-xyz[:,0],xyz[:,2]-xyz[:,0]);assert np.array_equal(np.linalg.norm(normal,axis=1)*.5,np.array([.5,.5]));assert np.all(np.einsum('ij,j->i',normal,A[:3,axis]*sign)==1)
 counts[tuple(model['sourceCodes'])]=len(faces);vertices+=N;triangles+=T;diagram=next(r for r in diagrams if r['pair']==model['id'])
 for plane in diagram['planes']:
  file=D/'schematics'/plane['file'];assert sha(file.read_bytes())==plane['sha256'];svg=ET.fromstring(file.read_bytes());g=svg.find('s:g',SVG_NS);W,H=plane['widthCells'],plane['heightCells'];actual=np.zeros((H,W),dtype='<i2')
  for rect in g.findall('s:rect',SVG_NS):
   if 'data-source-code'not in rect.attrib:continue
   x,y,width,height=[int(rect.attrib[k])for k in ['x','y','width','height']];assert height==1 and np.all(actual[y:y+height,x:x+width]==0);actual[y:y+height,x:x+width]=int(rect.attrib['data-source-code'])
  # Construct each displayed sample in physical RAS, then invert the original affine.
  wa={'axial':[2,0,1],'coronal':[1,0,2],'sagittal':[0,1,2]}[plane['plane']];lo=np.asarray(plane['cropLowIJK']);hi=np.asarray(plane['cropHighIJK']);ends=np.column_stack([np.stack([lo,hi]),np.ones(2)])@A.T;upper=ends.max(0);fixed_native=np.array(model['anchorOwnerIJK']);fixed_world=np.r_[fixed_native,1]@A.T;y,x=np.indices((H,W));world=np.ones((H,W,4));world[:,:,wa[0]]=fixed_world[wa[0]];world[:,:,wa[1]]=upper[wa[1]]-x;world[:,:,wa[2]]=upper[wa[2]]-y;native=np.einsum('...j,ij->...i',world,inverse)[...,:3];assert np.array_equal(native,np.round(native));native=native.astype(int);wanted=labels[tuple(native.transpose(2,0,1))];assert np.array_equal(actual,wanted)and sha(actual.tobytes())==plane['sourcePlaneBytesSHA256'];reconstructed+=W*H
  n=plane['nativeFixedAxis'];slice_=plane['nativeSlice'];wanted_ids={i for i,f in enumerate(faces)if f[3]!=n and f[n]==slice_};got_ids=set()
  for line in g.findall('s:line',SVG_NS):
   faceid=int(line.attrib['data-source-face-id']);assert faceid not in got_ids and faceid in wanted_ids;got_ids.add(faceid);f=faces[faceid];endpoints=[]
   for suffix in ['1','2']:
    pworld=fixed_world.copy();pworld[wa[1]]=upper[wa[1]]-(float(line.attrib['x'+suffix])-.5);pworld[wa[2]]=upper[wa[2]]-(float(line.attrib['y'+suffix])-.5);endpoints.append((inverse@pworld)[:3])
   p=f[:3].astype(float);axis=int(f[3]);p[axis]+=int(f[4])*.5;other=next(i for i in range(3)if i not in [n,axis]);q=p.copy();p[other]-=.5;q[other]+=.5;assert set(map(tuple,endpoints))=={tuple(p),tuple(q)}
  assert got_ids==wanted_ids;sections+=len(got_ids)
assert found==expected;assert counts=={tuple(r['codes']):r['sharedCellFaces']for r in audit['pairs']if r['sharedCellFaces']};assert len(manifest['models'])==36 and triangles==1304
proof={'allPassed':True,'sourceClasses':len(codes),'allCandidatePairs':210,'contactPairs':36,'sourceFaces':len(found),'vertices':vertices,'triangles':triangles,'SVGsections':len(diagrams)*3,'sourceCellsIndependentlyReconstructedFromSVG':reconstructed,'sourceFaceSectionSegmentsChecked':sections,'allSourceFacesMatchedIndependentSixNeighbourOracle':True,'allModelQuadsAreasWindingAndNativeCornersVerified':True,'allSVGSourceCellsAndContactSectionsVerifiedViaOriginalAffine':True,'sourceLabelsChanged':False,'sourceMRIResampled':False,'gapsBridged':False,'anatomicalInterfaceVerified':False,'clinicalApproval':False,'wholeGoalComplete':False,'checkerSHA256':sha(Path(__file__).read_bytes()),'manifestSHA256':sha((D/'manifest.json').read_bytes()),'auditSHA256':sha((D/'audit.json').read_bytes()),'schematicsManifestSHA256':sha((D/'schematics.json').read_bytes())};(D/'proof.json').write_text(json.dumps(proof,indent=2)+'\n');print(proof)
