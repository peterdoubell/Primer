"""Lossless source planes, indexed into bounded files for HTTP range delivery."""
from pathlib import Path
import gzip,io,json,zipfile,hashlib,time
import numpy as np,nibabel as nib
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'reader-package';OUT.mkdir(exist_ok=True)
sha=lambda b:hashlib.sha256(b).hexdigest();limit=48*1024*1024
manifest={'schemaVersion':1,'sourceRecord':'https://zenodo.org/records/15690524','licenseAsRecorded':'CC BY 4.0','clinicalApproval':False,'currentPatientRegistration':False,'sourceGridIsAcquisitionResolution':False,'sulcalLabelsAreCSFTerritories':True,'labelOriginalDatatype':'<f4','labelEncoding':'<u2; exact float32 bit round-trip checked','sourceContrasts':{},'volumes':{},'packs':{}}
checks={'scope':'Complete lossless plane reassembly of all supplied arrays; not clinical approval or deployed range support','allPassed':False,'volumes':{}}
with zipfile.ZipFile(ROOT/'atlas_v1.0.zip') as archive:
 for key,name,kind in [('labels','substructure_atlas.nii.gz','categorical'),('T1','T1w_average.nii.gz','processed population MRI template'),('T2','T2w_average.nii.gz','processed population MRI template'),('WMn','WMn_average.nii.gz','population template of source-author synthesized WMn-like contrast')]:
  native=gzip.decompress(archive.read(name));h=nib.Nifti1Header.from_fileobj(io.BytesIO(native[:352]));data=np.frombuffer(native,offset=int(h['vox_offset']),dtype=h.get_data_dtype()).reshape(h.get_data_shape(),order='F');assert np.isfinite(data).all() and float(h['scl_slope'])==1 and float(h['scl_inter'])==0
  sourceBytes=data.tobytes(order='F');sourceHash=sha(sourceBytes);dtype='<u2' if key=='labels' else '<f4'
  if key=='labels':assert data.astype(dtype).astype('<f4').tobytes(order='F')==sourceBytes
  planes={};volumeChecks=[]
  for axis in range(3):
   remain=[a for a in range(3) if a!=axis];planeShape=[data.shape[a] for a in remain];part=0;pack=None;packName=None;written=0;planeRows=[];reconstructed=np.empty(data.shape,dtype=dtype,order='F')
   for index in range(data.shape[axis]):
    selection=[slice(None)]*3;selection[axis]=index;array=data[tuple(selection)].astype(dtype,copy=False);decoded=array.tobytes(order='F');compressed=gzip.compress(decoded,compresslevel=6,mtime=0)
    if pack is None or written+len(compressed)>limit:
     if pack is not None:pack.close();raw=(OUT/packName).read_bytes();manifest['packs'][packName]={'bytes':len(raw),'sha256':sha(raw)}
     packName=f'{key}-axis-{axis}-part-{part}.pack';part+=1;pack=(OUT/packName).open('wb');written=0
    offset=written;pack.write(compressed);written+=len(compressed);back=gzip.decompress(compressed);assert back==decoded;reconstructed[tuple(selection)]=np.frombuffer(back,dtype=dtype).reshape(planeShape,order='F')
    planeRows.append({'file':packName,'offset':offset,'gzipBytes':len(compressed),'gzipSHA256':sha(compressed),'byteLength':len(decoded),'decodedSHA256':sha(decoded),'axis':axis,'index':index,'shape':planeShape,'sourceAxes':remain,'dtype':dtype,'storageOrder':'F'})
   pack.close();raw=(OUT/packName).read_bytes();manifest['packs'][packName]={'bytes':len(raw),'sha256':sha(raw)}
   reconstructedBytes=reconstructed.astype('<f4',copy=False).tobytes(order='F');assert reconstructedBytes==sourceBytes
   volumeChecks.append({'axis':axis,'planes':len(planeRows),'reconstructedSourceSampleBytes':len(reconstructedBytes),'reconstructedSourceSHA256':sha(reconstructedBytes),'allOriginalSourceSampleBitsPreserved':True});planes[str(axis)]=planeRows;print(key,'axis',axis,'planes',len(planeRows),'packs',part,flush=True)
  manifest['volumes'][key]={'sourceMember':name,'shape':list(data.shape),'sourceDatatype':'<f4','encodedDatatype':dtype,'storageOrder':'F','sourceSampleSHA256':sourceHash,'sourceNativeNIfTISHA256':sha(native),'voxelToSourceWorld':h.get_sform().tolist(),'sourceWorldUnits':'mm','kind':kind,'planes':planes}
  manifest['sourceContrasts'][key]=kind;checks['volumes'][key]={'sourceSampleSHA256':sourceHash,'sourceNativeNIfTISHA256':sha(native),'axisChecks':volumeChecks}
  (OUT/'manifest.json').write_text(json.dumps(manifest,separators=(',',':'))+'\n');del native,data,sourceBytes,reconstructed,reconstructedBytes
manifestBytes=(OUT/'manifest.json').read_bytes();(OUT/'manifest.json.gz').write_bytes(gzip.compress(manifestBytes,mtime=0));checks.update(allPassed=True,packs=len(manifest['packs']),planes=sum(len(p) for v in manifest['volumes'].values() for p in v['planes'].values()),bytes=sum(p['bytes'] for p in manifest['packs'].values()),manifestSHA256=sha(manifestBytes));(OUT/'plane-reassembly-proof.json').write_text(json.dumps(checks,indent=2)+'\n');print(json.dumps({k:v for k,v in checks.items() if k!='volumes'}),flush=True)
