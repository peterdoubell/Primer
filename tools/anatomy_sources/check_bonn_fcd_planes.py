"""Compare every delivered plane sample with its original NIfTI volume."""
from pathlib import Path
import json,gzip,hashlib,nibabel as nib,numpy as np
R=Path(__file__).resolve().parents[2];S=R/'.research/fcd-source-20261028';D=S/'native-package'
m=json.loads((D/'manifest.json').read_bytes());count=0;samples=0
for role,v in m['volumes'].items():
 source=S/v['sourceFile'];assert hashlib.sha256(source.read_bytes()).hexdigest()==v['sourceSHA256']
 image=nib.load(source);original=np.asarray(image.dataobj.get_unscaled())
 assert np.array_equal(image.affine,np.asarray(v['affine']))
 assert image.dataobj.slope==v['slope'] and image.dataobj.inter==v['intercept']
 for axis,p in v['planes'].items():
  axis=int(axis);pack=(D/p['file']).read_bytes();assert len(pack)==p['bytes'] and hashlib.sha256(pack).hexdigest()==p['sha256'];end=0
  for i,row in enumerate(p['planes']):
   assert row['index']==i and row['offset']==end
   end+=row['gzipBytes'];encoded=pack[row['offset']:end];assert hashlib.sha256(encoded).hexdigest()==row['gzipSHA256']
   decoded=gzip.decompress(encoded);assert len(decoded)==row['decodedBytes'] and hashlib.sha256(decoded).hexdigest()==row['decodedSHA256']
   actual=np.frombuffer(decoded,dtype=v['dtype']).reshape(row['shape']);selection=[slice(None)]*3;selection[axis]=i;expected=original[tuple(selection)]
   assert np.array_equal(actual,expected);count+=1;samples+=actual.size
  assert end==len(pack) and len(p['planes'])==original.shape[axis]
proof=dict(allPassed=True,planes=count,sourceSamplesCompared=samples,manifestSHA256=hashlib.sha256((D/'manifest.json').read_bytes()).hexdigest(),resampling=False,t1RegistrationVerified=False,clinicalApproval=False)
(S/'independent-plane-proof.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof))
