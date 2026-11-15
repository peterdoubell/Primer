#!/usr/bin/env python3
"""Acquire the pinned original AAA archive and primary paper, preserving the reviewed metadata snapshot."""
import argparse
import hashlib
from pathlib import Path
import urllib.request
from tools.anatomy_sources.review_aaa_kinematic_source import OUTPUT,METADATA_SHA,ARCHIVE_SHA,PAPER_SHA


def download(url,path,expected):
    if not path.exists():
        staging=path.with_suffix(path.suffix+'.download')
        with urllib.request.urlopen(url,timeout=60) as response,staging.open('wb') as out:
            while True:
                chunk=response.read(1024*1024)
                if not chunk:break
                out.write(chunk)
        if hashlib.sha256(staging.read_bytes()).hexdigest()!=expected:raise ValueError('Pinned source bytes differ')
        staging.replace(path)
    if hashlib.sha256(path.read_bytes()).hexdigest()!=expected:raise ValueError('Existing source bytes differ')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);a=p.parse_args()
    a.source_root.mkdir(parents=True,exist_ok=True)
    metadata=(OUTPUT/'source-metadata.json').read_bytes()
    if hashlib.sha256(metadata).hexdigest()!=METADATA_SHA:raise ValueError('Reviewed metadata snapshot differs')
    (a.source_root/'kinematic-metadata.json').write_bytes(metadata)
    download('https://zenodo.org/api/records/15477710/files/4DCTA_AAA_Dataset.zip/content',a.source_root/'4DCTA_AAA_Dataset.zip',ARCHIVE_SHA)
    download('https://arxiv.org/pdf/2505.17647v2',a.source_root/'kinematic-paper.pdf',PAPER_SHA)
    print('Pinned archive, reviewed metadata snapshot and primary paper verified.')
