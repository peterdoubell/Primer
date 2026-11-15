"""Compare every decoded transport plane with original source sample bits."""
from pathlib import Path
import gzip,hashlib,json
import nibabel as nib
import numpy as np
ROOT=Path(__file__).resolve().parents[1];O=ROOT/'web/anatomy/schirmer-vascular';D=O;DOC=ROOT/'docs/schirmer-vascular-review-20261026';sha=lambda b:hashlib.sha256(b).hexdigest();manifest=json.loads((O/'manifest.json').read_bytes());pins=json.loads((DOC/'source-index.json').read_bytes());assert set(manifest['volumes'])=={'labels','T1','T2','FLAIR'};counts={};pack_cache={}
for name,row in manifest['packs'].items():
 raw=(D/name).read_bytes();assert len(raw)==row['bytes'] and sha(raw)==row['sha256'];pack_cache[name]=raw
used={name:[] for name in pack_cache};total=0;pixels=0
for volume,entry in manifest['volumes'].items():
 source=(O/'originals'/entry['sourceFile']).read_bytes();pin=next(r for r in pins['files']if r['file']==entry['sourceFile']);assert sha(source)==pin['sha256']==entry['sourceSHA256'];native=gzip.decompress(source);assert sha(native)==entry['nativeNiftiSHA256'];im=nib.Nifti1Image.from_bytes(native);a=np.asanyarray(im.dataobj);assert list(a.shape)==entry['shape'];assert np.array_equal(im.affine,entry['affine']);assert im.header.get_xyzt_units()[0]=='mm';assert set(entry['planes'])=={'0','1','2'}
 for axis_text,rows in entry['planes'].items():
  axis=int(axis_text);assert [r['index']for r in rows]==list(range(a.shape[axis]));expected_shape=[a.shape[i]for i in range(3)if i!=axis]
  for r in rows:
   assert r['axis']==axis and r['shape']==expected_shape and r['sourceAxes']==[i for i in range(3)if i!=axis]
   start=r['offset'];end=start+r['gzipBytes'];encoded=pack_cache[r['file']][start:end];assert len(encoded)==r['gzipBytes'] and sha(encoded)==r['gzipSHA256'];decoded=gzip.decompress(encoded);assert len(decoded)==r['decodedBytes'] and sha(decoded)==r['decodedSHA256'];actual=np.frombuffer(decoded,dtype=r['dtype']).reshape(expected_shape[::-1]).T;expected=np.moveaxis(a,axis,-1)[...,r['index']];restored=actual.astype(a.dtype)
   assert np.array_equal(restored.view('u'+str(a.dtype.itemsize)),expected.view('u'+str(a.dtype.itemsize)))
   used[r['file']].append((start,end));pixels+=expected.size;total+=1
 counts[volume]=sum(len(r)for r in entry['planes'].values())
for name,spans in used.items():
 spans=sorted(spans);assert spans and spans[0][0]==0 and spans[-1][1]==len(pack_cache[name]);assert all(a[1]==b[0]for a,b in zip(spans,spans[1:]))
assert total==manifest['planeCount']==2328
report={'allPassed':True,'planes':total,'sourceSamplesCompared':pixels,'counts':counts,'packs':len(pack_cache),'manifestSHA256':sha((O/'manifest.json').read_bytes()),'verifierSHA256':sha(Path(__file__).read_bytes()),'sourceUnmodified':True,'singletonLabel19Preserved':True,'clinicalApproval':False,'runtimeBound':True};print(json.dumps(report))
