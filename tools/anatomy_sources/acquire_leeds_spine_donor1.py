#!/usr/bin/env python3
"""Acquire one public CC BY4 Leeds CT ZIP with resumable, verified HTTP ranges.

No authentication, source modification or automatic clinical promotion. A
checkpoint records only completed ranges; final success requires the published
whole-object MD5. Resume only after confirming the earlier process has stopped.
"""
import concurrent.futures as cf
import hashlib,json,re,threading,time,urllib.request
from pathlib import Path

URL='https://archive.researchdata.leeds.ac.uk/1620/1/G24-12-007_L4-S1.zip'
SIZE=13325473922
MD5='bdf6b02ec6d6965f0f13a6f735769efc'
ROOT=Path(__file__).resolve().parents[2]
STAGE=ROOT/'.research/leeds-spine-1921'
CHUNK=32*1024*1024


def main():
    STAGE.mkdir(parents=True,exist_ok=True)
    part=STAGE/'G24-12-007_L4-S1.zip.partial';final=STAGE/'G24-12-007_L4-S1.zip';checkpoint=STAGE/'download-progress.json'
    if final.exists():raise SystemExit('Final archive already exists; inspect its integrity record instead of restarting.')
    state=json.loads(checkpoint.read_text()) if checkpoint.exists() else {'url':URL,'archive_bytes':SIZE,'source_md5':MD5,'ranges':{},'complete':False}
    assert state['url']==URL and state['archive_bytes']==SIZE and state['source_md5']==MD5
    if not part.exists():
        assert not state['ranges']
        with part.open('xb') as f:f.truncate(SIZE)
    assert part.stat().st_size==SIZE
    stop=threading.Event()
    def save():
        tmp=checkpoint.with_suffix('.tmp');tmp.write_text(json.dumps(state,indent=2)+'\n');tmp.replace(checkpoint)
    def fetch(start):
        end=min(start+CHUNK,SIZE)-1;digest=hashlib.sha256();received=0
        if stop.is_set():raise RuntimeError('Acquisition stopped after another range failed')
        request=urllib.request.Request(URL,headers={'Range':f'bytes={start}-{end}'})
        with urllib.request.urlopen(request,timeout=60) as response:
            if response.status!=206 or response.headers.get('Content-Range')!=f'bytes {start}-{end}/{SIZE}' or response.headers.get('ETag','').strip('"')!=MD5:raise ValueError('Unexpected range or changed source object')
            with part.open('r+b') as target:
                target.seek(start)
                while received<end-start+1:
                    if stop.is_set():raise RuntimeError('Acquisition stopped after another range failed')
                    block=response.read(min(1024*1024,end-start+1-received))
                    if not block:raise ValueError('Truncated range')
                    target.write(block);digest.update(block);received+=len(block)
                if response.read(1):raise ValueError('Overlong range')
        return {'start':start,'end':end,'bytes':received,'sha256':digest.hexdigest()}
    # A resumed checkpoint must match the bytes actually on disk.
    with part.open('rb') as source:
        for key,r in state['ranges'].items():
            source.seek(r['start']);assert hashlib.sha256(source.read(r['bytes'])).hexdigest()==r['sha256'],'Checkpoint bytes changed'
    pending_starts=iter(start for start in range(0,SIZE,CHUNK) if str(start) not in state['ranges'])
    state.pop('error',None);save()
    with cf.ThreadPoolExecutor(max_workers=4) as pool:
        jobs={pool.submit(fetch,start):start for start in [next(pending_starts,None) for _ in range(4)] if start is not None}
        while jobs:
            finished,_=cf.wait(jobs,return_when=cf.FIRST_COMPLETED)
            for future in finished:
                start=jobs.pop(future)
                try:record=future.result()
                except Exception as error:
                    stop.set();state['error']=type(error).__name__+': '+str(error);save();raise
                state['ranges'][str(start)]=record;save()
                if len(state['ranges'])%8==0:print(f"Verified {sum(r['bytes'] for r in state['ranges'].values())}/{SIZE} bytes",flush=True)
                next_start=next(pending_starts,None)
                if next_start is not None:jobs[pool.submit(fetch,next_start)]=next_start
    md5,sha=hashlib.md5(),hashlib.sha256()
    with part.open('rb') as source:
        for block in iter(lambda:source.read(8*1024*1024),b''):md5.update(block);sha.update(block)
    assert md5.hexdigest()==MD5,'Whole-object MD5 mismatch'
    part.replace(final);state.update(complete=True,sha256=sha.hexdigest(),md5=md5.hexdigest());save()
    print('Complete archive verified: '+sha.hexdigest(),flush=True)


if __name__=='__main__':main()
