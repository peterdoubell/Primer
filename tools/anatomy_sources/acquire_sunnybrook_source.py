#!/usr/bin/env python3
"""Acquire the pinned public-domain Sunnybrook source files; never accept landing HTML as image data."""
import argparse,hashlib,json,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'docs/sunnybrook-native-source-review'

def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()

def acquire(root,include_cine=False):
    root.mkdir(parents=True,exist_ok=True)
    small=json.loads((OUT/'small-source-acquisition.json').read_text())
    cine=json.loads((OUT/'native-cine-linkage-review.json').read_text())['source_archive']
    for row in small+([cine] if include_cine else []):
        target=root/row['file']
        if target.exists():
            if target.stat().st_size!=row['bytes'] or digest(target)!=row['sha256']:raise ValueError('Cached original source differs: '+row['file'])
            print('Verified cached source:',row['file'],flush=True);continue
        temporary=target.with_suffix(target.suffix+'.part');h=hashlib.sha256();size=0
        request=urllib.request.Request(row['url'],headers={'User-Agent':'Primer source-fidelity research'})
        try:
            with urllib.request.urlopen(request,timeout=60) as response,temporary.open('wb') as output:
                if response.status!=200 or 'attachment' not in response.headers.get('Content-Disposition','').lower():raise ValueError('Expected original source attachment, not landing page')
                while True:
                    chunk=response.read(1024*1024)
                    if not chunk:break
                    size+=len(chunk)
                    if size>row['bytes']:raise ValueError('Original source exceeds pinned byte length')
                    output.write(chunk);h.update(chunk)
            if size!=row['bytes'] or h.hexdigest()!=row['sha256']:raise ValueError('Original source byte length/hash differs')
            temporary.replace(target);print('Acquired exact source:',row['file'],size,flush=True)
        finally:
            temporary.unlink(missing_ok=True)
    (root/'small-source-acquisition.json').write_text(json.dumps(small,indent=2)+'\n')
    if include_cine:(root/'batch1-acquisition.json').write_text(json.dumps(cine,indent=2)+'\n')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--source-root',type=Path,required=True);parser.add_argument('--include-cine',action='store_true',help='Also acquire the 433,585,535-byte first DICOM archive')
    args=parser.parse_args();acquire(args.source_root,args.include_cine)
