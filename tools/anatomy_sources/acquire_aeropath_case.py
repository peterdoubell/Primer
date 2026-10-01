#!/usr/bin/env python3
"""Acquire source CT and labels from the author-endorsed pinned mirror."""
import argparse
import hashlib
import json
from pathlib import Path
from urllib.request import urlopen


def acquire(root,case):
    root.mkdir(parents=True,exist_ok=True)
    metadata_raw=urlopen('https://huggingface.co/api/datasets/andreped/AeroPath',timeout=60).read();metadata=json.loads(metadata_raw);revision=metadata['sha']
    tree_raw=urlopen('https://huggingface.co/api/datasets/andreped/AeroPath/tree/'+revision+'?recursive=true',timeout=60).read();tree=json.loads(tree_raw)
    license_url='https://huggingface.co/datasets/andreped/AeroPath/raw/'+revision+'/license.md';license_raw=urlopen(license_url,timeout=60).read()
    if not license_raw.startswith(b'Attribution 4.0 International'):raise ValueError('Author dataset licence changed')
    names=[f'data/{case}/{case}_CT_HR.nii.gz',f'data/{case}/{case}_CT_HR_label_airways.nii.gz',f'data/{case}/{case}_CT_HR_label_lungs.nii.gz']
    files=[]
    for name in names:
        entry=next(e for e in tree if e['path']==name);expected=entry['lfs']['oid'];path=root/Path(name).name
        if not path.is_file() or path.stat().st_size!=entry['size'] or hashlib.sha256(path.read_bytes()).hexdigest()!=expected:
            temporary=path.with_name(path.name+'.part');sha=hashlib.sha256();total=0
            url='https://huggingface.co/datasets/andreped/AeroPath/resolve/'+revision+'/'+name
            with urlopen(url,timeout=60) as response,temporary.open('wb') as out:
                for block in iter(lambda:response.read(4*1024*1024),b''):out.write(block);sha.update(block);total+=len(block)
            if total!=entry['size'] or sha.hexdigest()!=expected:raise ValueError('Author file size/SHA-256 mismatch')
            temporary.replace(path)
        files.append({'source_path':name,'name':path.name,'size':entry['size'],'sha256':expected,'sha256_and_size_passed':True})
        print(path.name,'verified',flush=True)
    (root/'source-data-license.md').write_bytes(license_raw)
    (root/'acquisition.json').write_text(json.dumps({'case':case,'source_dataset_doi':'10.5281/zenodo.10069289','source_author_repository':'https://github.com/raidionics/AeroPath','mirror_repository':'andreped/AeroPath','mirror_revision':revision,
             'mirror_metadata_sha256':hashlib.sha256(metadata_raw).hexdigest(),'mirror_tree_sha256':hashlib.sha256(tree_raw).hexdigest(),'license_url':license_url,'license_name':'CC BY 4.0','license_sha256':hashlib.sha256(license_raw).hexdigest(),'card_metadata_license':metadata.get('cardData',{}).get('license'),'files':files,'source_data_changed':False,'clinical_approval':False,'runtime_promoted':False},indent=2)+'\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--destination',type=Path,required=True);parser.add_argument('--case',default='1');args=parser.parse_args();acquire(args.destination,args.case)
