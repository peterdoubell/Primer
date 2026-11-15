"""Lossless provided-grid planes, retaining both coded NIfTI coordinate forms."""
from pathlib import Path
import gzip,hashlib,json
import nibabel as nib
import numpy as np

def main():
    parser=__import__('argparse').ArgumentParser();parser.add_argument('--source',type=Path,default=Path(__file__).resolve().parents[2]/'.research/pituitary-case-source-20261101');parser.add_argument('--output',type=Path);args=parser.parse_args();
    D=args.source;O=args.output or D/'plane-package';O.mkdir(exist_ok=True);P=O/'payloads';P.mkdir(exist_ok=True);acq=json.loads((D/'case-1-acquisition.json').read_bytes());sha=lambda b:hashlib.sha256(b).hexdigest();maximum=16*1024*1024;volumes={};packs={}
    inputs=[('T1CE','1_T1.nii.gz','provided processed contrast-enhanced T1'),('T2','1_T2_f.nii.gz','provided registered/resampled T2'),('tumourGland','1_tumor_f.nii.gz','source tumour-gland complex annotation'),('carotids','1_carotids_f.nii.gz','source combined carotid annotation')]
    for key,name,meaning in inputs:
     path=D/'case-1'/name;record=next(r for r in acq['files']if r['sourceFile']==name);assert path.stat().st_size==record['bytes']and sha(path.read_bytes())==record['sha256'];image=nib.load(path);array=image.dataobj.get_unscaled();dtype=np.dtype(image.get_data_dtype()).newbyteorder('<');assert array.shape==(499,404,342)and image.dataobj.slope==1 and image.dataobj.inter==0 and np.isfinite(array).all();voxelbytes=np.asarray(array,dtype=dtype).tobytes(order='F');sourceVoxelSHA=sha(voxelbytes);del voxelbytes
     row={'sourceFile':name,'sourceFileBytes':record['bytes'],'sourceFileSHA256':record['sha256'],'meaning':meaning,'shape':list(array.shape),'dtype':dtype.str,'sourceStorageOrder':'F','unscaledSourceVoxelSHA256':sourceVoxelSHA,'sourceVoxelBytes':int(array.size*dtype.itemsize),'providedVoxelSizeMm':list(map(float,image.header.get_zooms())),'originalSform':image.get_sform().tolist(),'originalQform':image.get_qform().tolist(),'originalSformCode':int(image.header['sform_code']),'originalQformCode':int(image.header['qform_code']),'units':list(image.header.get_xyzt_units()),'acquisitionNative':False,'sourceSamplesResampledByPrimer':False,'planes':{}}
     for axis in range(3):
      remaining=[a for a in range(3)if a!=axis];u,v=remaining;number=0;buffer=bytearray();members=[];active=None
      def finish():
       nonlocal buffer,active
       if not buffer:return
       data=bytes(buffer);(P/active).write_bytes(data);packs[active]={'bytes':len(data),'sha256':sha(data)};buffer=bytearray()
      for index in range(array.shape[axis]):
       # Each stored row follows increasing native-v; columns follow increasing native-u.
       plane=np.ascontiguousarray(np.take(array,index,axis=axis).T,dtype=dtype);raw=plane.tobytes(order='C');packed=gzip.compress(raw,compresslevel=1,mtime=0)
       assert len(packed)<maximum
       if active is None or len(buffer)+len(packed)>maximum:
        finish();active=f'{key}-axis-{axis}-part-{number}.pack';number+=1
       offset=len(buffer);buffer.extend(packed);members.append({'pack':active,'offset':offset,'compressedBytes':len(packed),'compressedSHA256':sha(packed),'decodedBytes':len(raw),'decodedSHA256':sha(raw),'sourceFixedAxis':axis,'sourceIndex':index,'horizontalNativeAxis':u,'verticalNativeAxis':v,'width':array.shape[u],'height':array.shape[v],'planeStorageOrder':'rows-v-columns-u'})
      finish();row['planes'][str(axis)]=members
     volumes[key]=row
     (O/'partial-manifest.json').write_text(json.dumps({'volumes':volumes,'packs':packs},indent=2)+'\n');print({'volume':key,'sourceVoxels':int(array.size),'planes':sum(map(len,row['planes'].values())),'packFiles':sum(name.startswith(key+'-')for name in packs)},flush=True)
    manifest={'schemaVersion':1,'sourceDatasetDOI':'10.6084/m9.figshare.27894084.v1','sourceCaseId':'1','sourceFileId':50793273,'sourceETag':acq['sourceETag'],'volumes':volumes,'packs':packs,'planePayloadsPreserveAllProvidedSourceSamples':True,'storedPlanesAreAnatomicalReslices':False,'coordinateDisplayPolicy':'Retain exact supplied matrices. Display original source-index planes; use supplied coded sform explicitly for correspondence, with annotation qform discrepancy disclosed. No header repair or fitted registration.','sourceImagesAreAcquisitionNative':False,'sourceHeadersChanged':False,'clinicalApproval':False,'completeReportingCoverage':False,'wholeGoalComplete':False};(O/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print({'allVolumesPacked':True,'packFiles':len(packs),'packBytes':sum(r['bytes']for r in packs.values()),'planeMembers':sum(len(m)for v in volumes.values()for m in v['planes'].values())})

if __name__=='__main__':main()
