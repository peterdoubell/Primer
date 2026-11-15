"""Local development package generation for the fixed Dryad case10 source.

Outputs stay in ignored research storage. Full publisher-archive SHA256
verification remains a separate mandatory publication gate.
"""
from pathlib import Path
import gzip,hashlib,json,struct
import nibabel as nib,numpy as np
from scipy import ndimage
D=Path(__file__).resolve().parents[2]/'.research/epilepsy-source-20261028';S=D/'dryad-case10';O=D/'native-package';O.mkdir(exist_ok=True)
sha=lambda b:hashlib.sha256(b).hexdigest()
acquisitionPath=D/'dryad-case10-acquisition.json'
assert hashlib.sha256(acquisitionPath.read_bytes()).hexdigest()=='dfab764bc92a28f6366c926cb90eae0201a20acd2c23db00bfb47893ddb5f63b'
for sourceRow in json.loads(acquisitionPath.read_bytes())['files']:
 assert hashlib.sha256((D/sourceRow['file']).read_bytes()).hexdigest()==sourceRow['sha256']

sources=[('mean','anon_meansMT04294-0008-00001-000001-01_denoised_prinlm_b2.0.nii'),('repeat0008','anon_sMT04294-0008-00001-000001-01.nii'),('repeat0009','anon_sMT04294-0009-00001-000001-01.nii'),('repeat0010','anon_sMT04294-0010-00001-000001-01.nii'),('primary','Hippocampal_Segmentation.nii'),('second','DICE_Hippocampal_Segmentation.nii')]
manifest={'schemaVersion':1,'source':'Clark and Maguire Dryad case10','sourceDOI':'10.5061/dryad.2v6wwpzt3','sourceVersion':7,'license':'CC0-1.0','fullArchiveVerificationPending':True,'annotationReferenceVolume':'mean','rawRepetitionAnatomicalRegistrationVerified':False,'clinicalApproval':False,'wholeGoalComplete':False,'sourceResampled':False,'sourceCropped':False,'sourceSmoothingAppliedByPrimer':False,'volumes':{},'packs':{},'meshes':{},'labelNames':{'1':'dentate gyrus','2':'ca 2/3','3':'ca 1','4':'subiculum','5':'uncus','6':'pre/parasubiculum','7':'Cyst'},'protocolNotes':['Publication protocol groups DG/CA4 under source label1; original LUT name retained.','Source labels2 and6 are combined regions, not separate CA2/CA3 or pre/parasubiculum boundaries.','Main Sample and DICE masks represent two manual annotations, not independent anatomical truth.','Source Cyst label7 appears only in the DICE mask; no independent diagnosis inferred.','Source files0009 and0010 are byte-identical, not two independent image contents.'],'planeCount':0}
packIndex=0;pack=bytearray();LIMIT=8*1024*1024
packName=lambda:f'planes-{packIndex:03d}.pack'
def flush():
 global pack,packIndex
 if not pack:return
 name=packName();raw=bytes(pack);(O/name).write_bytes(raw);manifest['packs'][name]={'bytes':len(raw),'sha256':sha(raw)};pack=bytearray();packIndex+=1
for key,name in sources:
 im=nib.load(S/name);a=np.asanyarray(im.dataobj.get_unscaled());assert a.shape==(328,384,112);dtype='<i2'if a.dtype.kind=='i'else'<u2';a=np.asarray(a,dtype=dtype)
 volume={'sourceFile':name,'sourceFileSHA256':sha((S/name).read_bytes()),'shape':list(a.shape),'dtype':dtype,'slope':float(im.dataobj.slope),'intercept':float(im.dataobj.inter),'affine':im.affine.tolist(),'qformCode':int(im.header['qform_code']),'sformCode':int(im.header['sform_code']),'sourceValueRange':[int(a.min()),int(a.max())],'rawCOrderSHA256':sha(a.tobytes()),'planes':{},'annotation':key in ['primary','second']}
 if not volume['annotation']:
  values=np.asarray(im.dataobj);volume['scaledNonzeroPercentiles']=np.percentile(values[values!=0],[1,50,99]).tolist()
 else:
  volume['counts']={str(int(k)):int(n)for k,n in zip(*np.unique(a,return_counts=True))};volume['components']={}
  for code in np.unique(a):
   if not code:continue
   labels,n=ndimage.label(a==code,structure=np.ones((3,3,3),bool));boxes=ndimage.find_objects(labels);items=[]
   for label,box in enumerate(boxes,1):
    local=np.argwhere(labels[box]==label);origin=np.array([s.start for s in box]);center=local.mean(0);focus=local[np.argmin(np.sum((local-center)**2,axis=1))]+origin;assert a[tuple(focus)]==code;lower=origin-.5;upper=np.array([s.stop for s in box])-.5;corners=np.array([[x,y,z]for x in [lower[0],upper[0]]for y in [lower[1],upper[1]]for z in [lower[2],upper[2]]]);world=nib.affines.apply_affine(im.affine,corners);items.append({'sourceComponentId':label,'voxels':len(local),'focusIJK':focus.tolist(),'focusWorld':nib.affines.apply_affine(im.affine,focus).tolist(),'boundsSourceIJK':[lower.tolist(),upper.tolist()],'boundsSourceWorld':[world.min(0).tolist(),world.max(0).tolist()]})
   assert sum(x['voxels']for x in items)==volume['counts'][str(int(code))];volume['components'][str(int(code))]=sorted(items,key=lambda x:(-x['voxels'],x['sourceComponentId']))
 for axis in range(3):
  other=[j for j in range(3)if j!=axis];rows=[]
  for index in range(a.shape[axis]):
   plane=np.ascontiguousarray(np.take(a,index,axis=axis).T,dtype=dtype);raw=plane.tobytes();compressed=gzip.compress(raw,compresslevel=6,mtime=0)
   if len(pack)+len(compressed)>LIMIT:flush()
   offset=len(pack);pack.extend(compressed);rows.append({'index':index,'pack':packName(),'offset':offset,'compressedBytes':len(compressed),'compressedSHA256':sha(compressed),'bytes':len(raw),'sha256':sha(raw)})
  volume['planes'][str(axis)]={'axis':axis,'uAxis':other[0],'vAxis':other[1],'width':a.shape[other[0]],'height':a.shape[other[1]],'sourceRowOrder':'v increasing; u increasing inside each row','rows':rows};manifest['planeCount']+=len(rows)
 manifest['volumes'][key]=volume;print(key,'all native planes encoded',flush=True)
flush()
assert manifest['volumes']['repeat0009']['sourceFileSHA256']==manifest['volumes']['repeat0010']['sourceFileSHA256']
proof=json.loads((D/'case10-boundary-proof.json').read_text());assert proof['allPassed']
for row in proof['meshes']:
 f=D/row['file'];assert sha(f.read_bytes())==row['sha256'];z=np.load(f);world=z['world'];positions=world.astype('<f4');faces=z['triangles'].astype('<u4');error=float(np.max(np.abs(world-positions)));assert error<1e-5
 name=f"{row['rater']}-{row['code']}.mesh.gz";raw=struct.pack('<4sIII',b'HVX1',len(positions),len(faces),0)+positions.tobytes()+faces.tobytes();compressed=gzip.compress(raw,mtime=0);(O/name).write_bytes(compressed)
 manifest['meshes'][f"{row['rater']}:{row['code']}"]={'file':name,'rater':row['rater'],'code':row['code'],'bytes':len(raw),'sha256':sha(raw),'compressedBytes':len(compressed),'compressedSHA256':sha(compressed),'vertices':len(positions),'triangles':len(faces),'maximumFloat32PositionErrorMm':error,'completeSourceBoundaries':True}
(O/'manifest.json').write_text(json.dumps(manifest,separators=(',',':'))+'\n');print(json.dumps({'planes':manifest['planeCount'],'packs':len(manifest['packs']),'meshes':len(manifest['meshes']),'bytes':sum(p.stat().st_size for p in O.iterdir())}),flush=True)
