"""Acquire one source CT/annotation pair by validated public ZIP byte ranges."""
from pathlib import Path
import json,struct,zlib,hashlib
from inspect_lumase_archive import fetch
ROOT=Path(__file__).resolve().parents[2];DOC=ROOT/'docs/msk-vertebral-substructure-source-review';OUT=ROOT/'.research/anatomy-sources/lumase/case'
def read_member(archive,entry):
 r=entry;name=r['name'];assert r['size']<30_000_000 and r['compressed_size']<30_000_000 and not r['flags']&1
 header=fetch(archive['url'],r['offset'],r['offset']+29,archive['archive_bytes']);h=struct.unpack('<4s5H3L2H',header);assert h[0]==b'PK\x03\x04'
 member_name=fetch(archive['url'],r['offset']+30,r['offset']+29+h[9],archive['archive_bytes']).decode();assert member_name==name
 start=r['offset']+30+h[9]+h[10];compressed=fetch(archive['url'],start,start+r['compressed_size']-1,archive['archive_bytes'])
 decoder=zlib.decompressobj(-15) if r['method']==8 else None;assert r['method'] in (0,8)
 raw=decoder.decompress(compressed,r['size']+1) if decoder else compressed
 assert len(raw)==r['size'] and zlib.crc32(raw)==r['crc32'] and (decoder is None or decoder.eof)
 return raw
def main():
 archive=json.loads((DOC/'lumase-archive-inventory.json').read_text());by_name={r['name']:r for r in archive['entries']}
 candidates=sorted(n for n in by_name if n.startswith('L1-L5FineSegMix-663case/') and n.endswith('_L3.nii.gz') and n.removesuffix('.nii.gz')+'_seg.nii.gz' in by_name)
 name=candidates[0];names=[name,name.removesuffix('.nii.gz')+'_seg.nii.gz'];OUT.mkdir(parents=True,exist_ok=True);records=[]
 for name in names:
  r=by_name[name];raw=read_member(archive,r)
  path=OUT/Path(name).name
  if path.exists():assert path.read_bytes()==raw
  else:path.write_bytes(raw)
  records.append({'member':name,'local_path':str(path.relative_to(ROOT)),'bytes':len(raw),'crc32':r['crc32'],'sha256':hashlib.sha256(raw).hexdigest()});print(Path(name).name,len(raw),'CRC verified',flush=True)
 report={'dataset_doi':'10.5281/zenodo.7181338','license':'CC BY 4.0','archive_url':archive['url'],'archive_declared_md5':archive['archive_md5'],'whole_archive_checksum_verified':False,'method':'Validated byte ranges, central/local member names, expanded sizes and per-member CRC32; individual downloaded SHA256 recorded.','files':records,'clinical_approval':False,'runtime_promoted':False};(DOC/'lumase-case-acquisition.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
