#!/usr/bin/env python3
"""Acquire every original NLM female head/neck frame and compare planar RGB with PNG."""
import argparse,concurrent.futures,hashlib,json,re,subprocess,threading,urllib.request
from pathlib import Path
from PIL import Image
BASE='https://data.lhncbc.nlm.nih.gov/public/Visible-Human/Female-Images/'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def acquire(root):
    root.mkdir(parents=True,exist_ok=True);frames=root/'female-head-original';frames.mkdir(exist_ok=True)
    index=urllib.request.urlopen(BASE+'PNG_format/head/index.html',timeout=45).read();(root/'female-head-PNG-index.html').write_bytes(index)
    names=sorted(set(re.findall(rb'avf\d{4}[abc]\.png',index)));names=[n.decode() for n in names];expected=[f'avf{n}{c}.png' for n in range(1001,1286) for c in 'abc']
    if names!=expected:raise ValueError('Original full head/neck sequence inventory differs')
    records=[];lock=threading.Lock()
    def download(name,folder):
        path=frames/name;metadata=path.with_suffix(path.suffix+'.json');url=BASE+folder+'/'+name
        if path.exists() and metadata.exists():
            r=json.loads(metadata.read_text());raw=path.read_bytes()
            if sha(raw)!=r['sha256'] or r['url']!=url:raise ValueError('Cached original member changed')
            return raw,r
        with urllib.request.urlopen(urllib.request.Request(url,headers={'Accept-Encoding':'identity'}),timeout=60) as response:raw=response.read();etag=response.headers.get('ETag')
        verified=bool(etag and re.fullmatch(r'"[0-9a-f]{32}"',etag))
        if verified and hashlib.md5(raw).hexdigest()!=etag.strip('"'):raise ValueError('Original object MD5 differs')
        r={'url':url,'bytes':len(raw),'sha256':sha(raw),'entity_tag':etag,'single_object_MD5_verified':verified};temporary=path.with_suffix(path.suffix+'.partial');temporary.write_bytes(raw);temporary.replace(path);metadata.write_text(json.dumps(r,indent=2)+'\n');return raw,r
    def frame(name):
        png,png_record=download(name,'PNG_format/head');stem=name.removesuffix('.png');compressed,raw_record=download(stem+'.raw.Z','Fullcolor/head');planar=subprocess.check_output(['/usr/bin/uncompress','-c',str(frames/(stem+'.raw.Z'))]);count=2048*1216
        if len(planar)!=count*3:raise ValueError('Original planar RGB payload length differs')
        interleaved=bytearray(len(planar));interleaved[0::3]=planar[:count];interleaved[1::3]=planar[count:count*2];interleaved[2::3]=planar[count*2:]
        with Image.open(frames/name) as im:
            if im.mode!='RGB' or im.size!=(2048,1216) or im.tobytes()!=interleaved:raise ValueError('Original raw RGB and PNG samples differ')
        r={'frame':stem,'original_PNG':png_record,'original_raw_Z':raw_record,'decoded_planar_sha256':sha(planar),'decoded_RGB_sha256':sha(interleaved),'all_original_RGB_samples_match_PNG':True}
        with lock:
            records.append(r);(root/'female-head-acquisition-progress.json').write_text(json.dumps({'expected_frames':855,'verified_frames':len(records),'records':sorted(records,key=lambda x:x['frame']),'clinical_approval':False,'runtime_promoted':False},indent=2)+'\n')
            if len(records)%25==0:print('Verified complete original raw/PNG frame pairs:',len(records),'of 855',flush=True)
        return r
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:completed=list(pool.map(frame,names))
    proof={'primary_NLM_source':'https://www.nlm.nih.gov/research/visible/visible_human.html','NLM_terms':'https://www.nlm.nih.gov/databases/download/terms_and_conditions.html','mandatory_attribution':'Courtesy of the U.S. National Library of Medicine','source_kind':'Original female cadaver cryosection photographs','nominal_sampling_mm':[.33,.33,.33],'source_grid':[2048,1216,855],'original_filename_sequence':[names[0],names[-1]],'original_index_sha256':sha(index),'records':completed,'every_original_raw_RGB_sample_matches_PNG':True,'source_RGB_samples_repaired_cropped_or_enhanced':False,'raw_photos_independently_registered_or_physically_calibrated':False,'source_cadaver_photos_are_living_patient_US_CT_or_functional_evidence':False,'clinical_approval':False,'structure_coverage_granted':False,'runtime_promoted':False}
    (root/'female-head-acquisition.json').write_text(json.dumps(proof,indent=2)+'\n');print('All 855 original head/neck RGB frame pairs verified',flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);a=p.parse_args();acquire(a.source_root)
