#!/usr/bin/env python3
"""Acquire public CC0 Universiti Malaya meshes and bounded registration evidence.

The public Dataverse data-access API supports HTTP ranges. ZIP members are
retrieved by their published central-directory offsets and verified with ZIP
CRC, avoiding a 382 MB image archive when only registration data are required.
No account, login or restricted file is used.
"""
import concurrent.futures,hashlib,io,json,pathlib,struct,urllib.request,zipfile,zlib
CACHE=pathlib.Path('/tmp/primer-msk-sources/high-fidelity')
API='https://researchdata.um.edu.my/api/access/datafile/'

def get(url,path,size=None,md5=None):
 if not path.exists():
  with urllib.request.urlopen(url,timeout=180) as r:data=r.read(500000001)
  if len(data)>500000000:raise ValueError('Per-asset budget exceeded')
  path.write_bytes(data)
 data=path.read_bytes()
 if size is not None:assert len(data)==size
 if md5:assert hashlib.md5(data).hexdigest()==md5
 return {'file':str(path),'url':url,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'published_md5':md5}

def ranged(url,start,end):
 request=urllib.request.Request(url,headers={'Range':f'bytes={start}-{end}'})
 with urllib.request.urlopen(request,timeout=90) as r:
  if r.status!=206:raise ValueError('Server did not honor range request')
  raw=r.read(end-start+2)
  if len(raw)!=end-start+1:raise ValueError('Unexpected range length')
  return raw

def main():
 CACHE.mkdir(parents=True,exist_ok=True)
 data=json.loads(urllib.request.urlopen('https://researchdata.um.edu.my/api/datasets/:persistentId/?persistentId=doi:10.22452/RD/5T6TZ7').read())
 (CACHE/'um-dataset.json').write_text(json.dumps(data,indent=2)+'\n')
 version=data['data']['latestVersion'];assert version['license']['name']=='CC0 1.0'
 files={f['dataFile']['id']:f for f in version['files']}
 for fid in [593,594,595,596]:assert files[fid]['restricted'] is False
 records=[]
 for fid,name in [(593,'um-readme.txt'),(596,'um-final-model-stl.zip')]:
  f=files[fid]['dataFile'];records.append(get(API+str(fid),CACHE/name,f['filesize'],f['md5']))
 archive=files[595]['dataFile'];size=archive['filesize'];base=size-65536
 tail=ranged(API+'595',base,size-1)
 (CACHE/'um-segmentation-zip-tail.bin').write_bytes(tail)
 with zipfile.ZipFile(io.BytesIO(tail)) as z:entries=z.infolist()
 targets=['Final model.mrml','Segmentation.seg.nrrd','Segmentation-label.nrrd','Segmentation-label_ColorTable.ctbl','19 RT T2 FS spc_SAG_iso (KNEE).nrrd']
 folder=CACHE/'um-registration';folder.mkdir(exist_ok=True)
 def member(name):
  entry=next(e for e in entries if e.filename.rsplit('/',1)[-1]==name)
  assert entry.file_size<100000000
  offset=entry.header_offset+base
  path=folder/name
  if not path.exists():
   header=ranged(API+'595',offset,offset+29);assert header[:4]==b'PK\x03\x04'
   fn,extra=struct.unpack_from('<HH',header,26);start=offset+30+fn+extra
   compressed=ranged(API+'595',start,start+entry.compress_size-1)
   raw=zlib.decompress(compressed,-15) if entry.compress_type==8 else compressed
   assert len(raw)==entry.file_size and zlib.crc32(raw)==entry.CRC
   path.write_bytes(raw)
  raw=path.read_bytes();assert len(raw)==entry.file_size and zlib.crc32(raw)==entry.CRC
  return {'file':str(path),'source_archive_url':API+'595','source_member':entry.filename,'source_archive_published_md5':archive['md5'],'source_archive_full_md5_verified':False,'zip_crc32':f'{entry.CRC:08x}','bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:records.extend(pool.map(member,targets))
 # A single derivative DICOM frame provides standard geometric units. Retain
 # only an allowlisted geometry summary in provenance; never log identity tags.
 import pydicom
 dcm=folder/'representative-source-frame.dcm';dcm_index=CACHE/'um-dicom-zip-index.json'
 if not dcm.exists():
  dcm_size=files[594]['dataFile']['filesize'];dcm_tail=ranged(API+'594',dcm_size-65536,dcm_size-1)
  marker=dcm_tail.rfind(b'PK\x05\x06');end=struct.unpack('<4s4H2LH',dcm_tail[marker:marker+22]);central_start=end[6]
  central=ranged(API+'594',central_start,dcm_size-1)
  with zipfile.ZipFile(io.BytesIO(central)) as z:
   e=next(e for e in z.infolist() if e.filename=='DICOM/RT T1 VIBE SAG DIXON_IN/IMG0080.dcm')
  offset=e.header_offset+central_start;h=ranged(API+'594',offset,offset+29);fn,extra=struct.unpack_from('<HH',h,26);start=offset+30+fn+extra
  payload=ranged(API+'594',start,start+e.compress_size-1);raw=zlib.decompress(payload,-15);assert zlib.crc32(raw)==e.CRC
  dcm.write_bytes(raw)
 d=pydicom.dcmread(dcm,stop_before_pixels=True)
 fields=['ImagePositionPatient','ImageOrientationPatient','PixelSpacing','SliceThickness','SpacingBetweenSlices','Rows','Columns','Modality','SeriesDescription']
 geometry={k:str(getattr(d,k,'missing')) for k in fields}
 (folder/'dicom-geometry-evidence.json').write_text(json.dumps(geometry,indent=2)+'\n')
 records.append({'file':str(dcm),'source_archive_url':API+'594','source_member':'DICOM/RT T1 VIBE SAG DIXON_IN/IMG0080.dcm','sha256':hashlib.sha256(dcm.read_bytes()).hexdigest(),'use':'Geometric metadata only; not a clinically approved acquisition image'})
 (CACHE/'um-acquisition.json').write_text(json.dumps(records,indent=2)+'\n')
 print('Acquired',len(records),'public files; STL archive published checksum verified; partial ZIP members CRC-verified')

if __name__=='__main__':main()
