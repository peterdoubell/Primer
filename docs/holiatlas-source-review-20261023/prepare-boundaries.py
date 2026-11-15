"""Research-only exact boundaries of all supplied categorical atlas classes."""
from pathlib import Path
import gzip,io,json,struct,zipfile,hashlib,time,gc
import numpy as np
import nibabel as nib
from scipy import ndimage
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'boundaries';OUT.mkdir(exist_ok=True)
sha=lambda b:hashlib.sha256(b).hexdigest()
review=json.loads((ROOT/'holiatlas-label-review.json').read_text());rows=[x for x in review['classes'] if x['code'] and x['voxels']]
with zipfile.ZipFile(ROOT/'atlas_v1.0.zip') as z:raw=gzip.decompress(z.read('substructure_atlas.nii.gz'))
h=nib.Nifti1Header.from_fileobj(io.BytesIO(raw[:352]));labels=np.frombuffer(raw,offset=int(h['vox_offset']),dtype=h.get_data_dtype()).reshape(h.get_data_shape(),order='F');affine=h.get_sform();assert np.array_equal(affine,np.diag([.5,.5,.5,1])+np.array([[0,0,0,-90],[0,0,0,-126],[0,0,0,-72],[0,0,0,0]]))
# Crop boxes are derived once from the complete, losslessly represented label grid.
small=labels.astype(np.uint16);assert np.array_equal(small,labels);boxes=ndimage.find_objects(small);del small
proof={'scope':'All present non-background categorical classes; research only, no clinical or runtime approval','sourceLabelSHA256':sha(raw),'sourceAffine':affine.tolist(),'sulcalMeaning':'CSF territories assigned around labelled folds, not original traced sulcal centre-lines or independently validated gyral banks','meshMethod':'Every exposed 0.5 mm cell face; all cavities and components; two outward triangles per square; no smoothing or repair','clinicalApproval':False,'runtimeBound':False,'sourceClasses':len(rows),'rows':[]}
def save():
 p=OUT/'boundary-proof.json';temporary=p.with_suffix('.tmp');temporary.write_text(json.dumps(proof,indent=2)+'\n');temporary.replace(p)
def payload(name,raw):
 encoded=gzip.compress(raw,mtime=0);(OUT/name).write_bytes(encoded);return {'file':name,'bytes':len(raw),'gzipBytes':len(encoded),'sha256':sha(raw),'gzipSHA256':sha(encoded)}
for row in rows:
 started=time.monotonic();code=row['code'];box=boxes[code-1];origin=np.array([x.start for x in box]);mask=labels[box]==code;assert int(mask.sum())==row['voxels'];N=int(mask.sum());records=[];pairs=0
 for axis in range(3):
  left=[slice(None)]*3;right=left.copy();left[axis]=slice(None,-1);right[axis]=slice(1,None);pairs+=int(np.count_nonzero(mask[tuple(left)]&mask[tuple(right)]))
  for sign in [-1,1]:
   other=np.zeros_like(mask);target=[slice(None)]*3;neighbor=target.copy();target[axis]=slice(None,-1) if sign==1 else slice(1,None);neighbor[axis]=slice(1,None) if sign==1 else slice(None,-1);other[tuple(target)]=mask[tuple(neighbor)]
   cells=np.argwhere(mask&~other).astype(np.int16)+origin
   records.append(np.column_stack([cells,np.full(len(cells),axis),np.full(len(cells),sign)]).astype('<i2'))
 records=np.concatenate(records);F=len(records);assert F==6*N-2*pairs;assert len(np.unique(records,axis=0))==F
 # Independent per-record validity against the original full source grid, plus
 # the adjacency-count identity, proves both validity and completeness.
 cell=records[:,:3].astype(np.int32);assert np.all(labels[tuple(cell.T)]==code);neighbor=cell.copy();neighbor[np.arange(F),records[:,3]]+=records[:,4];inside=np.all((neighbor>=0)&(neighbor<np.array(labels.shape)),axis=1);assert not np.any(labels[tuple(neighbor[inside].T)]==code)
 corners=np.repeat((2*cell)[:,None,:],4,axis=1)
 for axis in range(3):
  use=records[:,3]==axis;others=[i for i in range(3) if i!=axis];corners[use,:,axis]+=records[use,4,None]
  for j,(u,v) in enumerate([(-1,-1),(1,-1),(1,1),(-1,1)]):corners[use,j,others[0]]+=u;corners[use,j,others[1]]+=v
 vertices,inverse=np.unique(corners.reshape(-1,3),axis=0,return_inverse=True);quads=inverse.reshape(-1,4)
 positions=(vertices*.25+affine[:3,3]).astype('<f4');quad=positions[quads].astype(np.float64);normal=np.cross(quad[:,1]-quad[:,0],quad[:,2]-quad[:,0]);expected=np.eye(3)[records[:,3]]*records[:,4,None]*.25;flip=np.sum(normal*expected,axis=1)<0;quads[flip]=quads[flip][:,[0,3,2,1]]
 triangles=np.stack([quads[:,[0,1,2]],quads[:,[0,2,3]]],axis=1).reshape(-1,3).astype('<u4');xyz=positions[triangles].astype(np.float64);normal=np.cross(xyz[:,1]-xyz[:,0],xyz[:,2]-xyz[:,0]);assert np.array_equal(normal,np.repeat(expected,2,axis=0));areas=np.linalg.norm(normal,axis=1)*.5;assert np.array_equal(areas,np.full(2*F,.125));volume=float(np.einsum('ij,ij->i',xyz[:,0],np.cross(xyz[:,1],xyz[:,2])).sum()/6);assert volume==N*.125,(code,volume,N*.125)
 assert np.array_equal(positions*4,np.rint(positions*4))
 components={}
 for connectivity in [1,2,3]:
  connected,count=ndimage.label(mask,ndimage.generate_binary_structure(3,connectivity));sizes=sorted(np.bincount(connected.ravel())[1:].tolist(),reverse=True);assert sum(sizes)==N;components[str([6,18,26][connectivity-1])]=sizes
 mesh=struct.pack('<4sIII',b'HVX1',len(positions),len(triangles),0)+positions.tobytes()+triangles.tobytes();mesh_info=payload(f'label-{code}.mesh.gz',mesh);face_info=payload(f'label-{code}-faces.bin.gz',records.tobytes())
 proof['rows'].append({'code':code,'sourceName':row['name'],'sideAsProvided':row['side'],'sourceVoxels':N,'vertices':len(positions),'faces':F,'triangles':2*F,'allFaceRecordsUniqueAndSourceValid':True,'faceCountEqualsSixVoxelsMinusTwiceAdjacentPairs':True,'everyTriangleAreaMM2':.125,'everyTriangleWindsOutward':True,'signedEnclosedVolumeMM3':volume,'volumeEqualsCompleteSourceCellVolume':True,'allComponentsAndCavitiesRetained':True,'componentsByConnectivity':components,'boundsSourceWorld':[positions.min(0).tolist(),positions.max(0).tolist()],'mesh':mesh_info,'facesPayload':face_info,'seconds':round(time.monotonic()-started,2)})
 save();print(code,row['name'],N,F,flush=True);del mask,records,corners,vertices,inverse,quads,positions,triangles,xyz,quad,normal,expected,connected,mesh;gc.collect()
proof['allPassed']=True;proof['totalTriangles']=sum(r['triangles'] for r in proof['rows']);save();print(json.dumps({'allPassed':True,'classes':len(rows),'triangles':proof['totalTriangles']}),flush=True)
