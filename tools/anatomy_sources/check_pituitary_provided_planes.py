"""Reconstruct every provided source volume from each independent plane family."""
from pathlib import Path
import gzip,hashlib,json
import nibabel as nib
import numpy as np

def main():
    parser=__import__('argparse').ArgumentParser();parser.add_argument('--source',type=Path,default=Path(__file__).resolve().parents[2]/'.research/pituitary-case-source-20261101');parser.add_argument('--package',type=Path);args=parser.parse_args();
    D=args.source;O=args.package or D/'plane-package';manifest=json.loads((O/'manifest.json').read_bytes());sha=lambda b:hashlib.sha256(b).hexdigest();seen=set();packdata={};records=[];totalvoxels=0;plane_count=0
    for name,row in manifest['packs'].items():
     p=O/'payloads'/name;assert p.stat().st_size==row['bytes']and sha(p.read_bytes())==row['sha256']and row['bytes']<=16*1024*1024
    for key,row in manifest['volumes'].items():
     path=D/'case-1'/row['sourceFile'];assert path.stat().st_size==row['sourceFileBytes']and sha(path.read_bytes())==row['sourceFileSHA256'];image=nib.load(path);dtype=np.dtype(row['dtype']);shape=row['shape'];count=int(np.prod(shape));assert image.header.endianness=='<'and dtype.itemsize==image.get_data_dtype().itemsize
     # Check against the literal NIfTI data segment, independently of the packer's array transpose.
     h=hashlib.sha256();read=0
     with gzip.open(path,'rb')as stream:
      stream.read(image.dataobj.offset)
      while True:
       chunk=stream.read(8*1024*1024)
       if not chunk:break
       h.update(chunk);read+=len(chunk)
     assert read==row['sourceVoxelBytes']and h.hexdigest()==row['unscaledSourceVoxelSHA256'];axis_results=[]
     for axis in range(3):
      reconstructed=np.empty(count,dtype=dtype);coverage=np.zeros(count,dtype=np.uint8);members=row['planes'][str(axis)];assert [r['sourceIndex']for r in members]==list(range(shape[axis]));current_pack=None;data=None;next_offset={}
      for member in members:
       name=member['pack'];assert member['sourceFixedAxis']==axis
       if current_pack!=name:data=(O/'payloads'/name).read_bytes();current_pack=name
       start=member['offset'];end=start+member['compressedBytes'];assert start==next_offset.get(name,0)and 0<=start<end<=len(data);next_offset[name]=end;encoded=data[start:end];assert sha(encoded)==member['compressedSHA256'];raw=gzip.decompress(encoded);assert len(raw)==member['decodedBytes']and sha(raw)==member['decodedSHA256'];pixels=np.frombuffer(raw,dtype=dtype);W,H=member['width'],member['height'];assert len(pixels)==W*H
       u=member['horizontalNativeAxis'];v=member['verticalNativeAxis'];assert {axis,u,v}=={0,1,2}and W==shape[u]and H==shape[v];y,x=np.indices((H,W));p=[np.zeros((H,W),dtype=np.int64)for _ in range(3)];p[axis].fill(member['sourceIndex']);p[u]=x;p[v]=y;offset=(p[0]+shape[0]*(p[1]+shape[1]*p[2])).ravel();assert np.all(coverage[offset]==0);reconstructed[offset]=pixels;coverage[offset]+=1;plane_count+=1
      assert np.all(coverage==1)and sha(reconstructed.tobytes())==row['unscaledSourceVoxelSHA256']
      for name,end in next_offset.items():assert end==manifest['packs'][name]['bytes'];seen.add(name)
      axis_results.append({'sourceFixedAxis':axis,'planes':len(members),'everyVoxelWrittenExactlyOnce':True,'reconstructedSourceVoxelSHA256':sha(reconstructed.tobytes())});totalvoxels+=count
      del reconstructed,coverage
     assert np.array_equal(image.get_sform(),row['originalSform'])and np.array_equal(image.get_qform(),row['originalQform'])
     records.append({'volume':key,'axes':axis_results,'literalOriginalNiftiDataSegmentVerified':True,'originalHeaderFormsUnchanged':True})
    assert seen==set(manifest['packs'])
    proof={'allPassed':True,'volumes':records,'volumeCount':len(records),'planeMembers':plane_count,'packFiles':len(seen),'providedVoxelValuesIndependentlyReconstructed':totalvoxels,'allSourceDataReconstructedFromEachAxis':True,'allPackRangesAndGzipMembersVerified':True,'sourceHeaderChanged':False,'sourceImageResampled':False,'coordinateConflictResolved':False,'clinicalApproval':False,'wholeGoalComplete':False,'manifestSHA256':sha((O/'manifest.json').read_bytes()),'checkerSHA256':sha(Path(__file__).read_bytes())};(O/'independent-proof.json').write_text(json.dumps(proof,indent=2)+'\n');print({k:v for k,v in proof.items()if k!='volumes'})

if __name__=='__main__':main()
