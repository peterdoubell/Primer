from pathlib import Path
import json,gzip,zipfile,hashlib,io
import numpy as np,nibabel as nib
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'reader-package';sha=lambda b:hashlib.sha256(b).hexdigest();raw=(OUT/'manifest.json').read_bytes();manifest=json.loads(raw);prior=json.loads((OUT/'plane-reassembly-proof.json').read_text());assert sha(raw)==prior['manifestSHA256'];usage={name:[] for name in manifest['packs']};verified=[]
for name,row in manifest['packs'].items():
 path=OUT/name;assert path.is_file() and not path.is_symlink();raw=path.read_bytes();assert len(raw)==row['bytes'] and sha(raw)==row['sha256'] and len(raw)<=48*1024*1024
with zipfile.ZipFile(ROOT/'atlas_v1.0.zip') as archive:
 for key,volume in manifest['volumes'].items():
  native=gzip.decompress(archive.read(volume['sourceMember']));assert sha(native)==volume['sourceNativeNIfTISHA256'];h=nib.Nifti1Header.from_fileobj(io.BytesIO(native[:352]));body=native[int(h['vox_offset']):];assert sha(body)==volume['sourceSampleSHA256'];shape=volume['shape'];dtype=volume['encodedDatatype'];handles={}
  try:
   for axis in range(3):
    rows=volume['planes'][str(axis)];assert len(rows)==shape[axis] and [r['index'] for r in rows]==list(range(shape[axis]));reassembled=np.empty(shape,dtype=dtype,order='F')
    for row in rows:
     assert row['axis']==axis and row['sourceAxes']==[a for a in range(3) if a!=axis] and row['shape']==[shape[a] for a in row['sourceAxes']];file=row['file'];handle=handles.setdefault(file,(OUT/file).open('rb'));handle.seek(row['offset']);encoded=handle.read(row['gzipBytes']);assert len(encoded)==row['gzipBytes'] and sha(encoded)==row['gzipSHA256'];decoded=gzip.decompress(encoded);assert len(decoded)==row['byteLength'] and sha(decoded)==row['decodedSHA256'];selection=[slice(None)]*3;selection[axis]=row['index'];reassembled[tuple(selection)]=np.frombuffer(decoded,dtype=dtype).reshape(row['shape'],order='F');usage[file].append((row['offset'],row['offset']+row['gzipBytes']))
    back=reassembled.astype('<f4',copy=False).tobytes(order='F');assert back==body;verified.append({'volume':key,'axis':axis,'planes':len(rows),'actualFileRangesReassembleExactOriginalBits':True,'sha256':sha(back)});print(key,axis,'verified',flush=True)
  finally:
   for handle in handles.values():handle.close()
for file,ranges in usage.items():
 ranges.sort();assert ranges[0][0]==0 and ranges[-1][1]==manifest['packs'][file]['bytes'];assert all(a[1]==b[0] for a,b in zip(ranges,ranges[1:]));assert all(a[0]<a[1] for a in ranges)
proof={'scope':'Actual pack bytes and index ranges, not just compressor output; no browser or deployed-range claim','allPassed':True,'planes':sum(r['planes'] for r in verified),'packs':len(usage),'allPackBytesIndexedExactlyOnce':True,'allOriginalSourceSampleBitsPreserved':True,'rows':verified,'manifestSHA256':prior['manifestSHA256']};(OUT/'independent-plane-proof.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps({k:v for k,v in proof.items() if k!='rows'}))
