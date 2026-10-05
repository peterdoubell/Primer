#!/usr/bin/env python3
"""Acquire pinned original/correction documents and checksum-bearing NLM source metadata."""
import argparse
import hashlib
from pathlib import Path
import urllib.request

FILES = {
    'pone.0132226.xml': ('https://journals.plos.org/plosone/article/file?id=10.1371/journal.pone.0132226&type=manuscript', None),
    'pone.0140736.xml': ('https://journals.plos.org/plosone/article/file?id=10.1371/journal.pone.0140736&type=manuscript', None),
    'PMC4549266.1.json': ('https://pmc-oa-opendata.s3.amazonaws.com/PMC4549266.1/PMC4549266.1.json', None),
    'pone.0132226.s003.pdf': ('https://journals.plos.org/plosone/article/file?type=supplementary&id=10.1371/journal.pone.0132226.s003', '8000e610a7ce93509d4a288d75c5ff65'),
    'pone.0132226.s004.pdf': ('https://journals.plos.org/plosone/article/file?type=supplementary&id=10.1371/journal.pone.0132226.s004', '37eb9f245e953aeb379edfc7da18151b'),
}
SNAPSHOT_SHA256 = {
    'pone.0132226.xml':'bf427e64527e45e26a303350a2a0f81a511873403c03585b277929fb77742f43',
    'pone.0140736.xml':'1263efc0e011e588932247133d923c43f5d6a3add4414deb0d0682a37711dc23',
    'PMC4549266.1.json':'f45880920bcc8f05207ed37b4973d3d6ced2cee6e6c8dd9e0f717e08bc7ed0e2',
}


def acquire(root):
    root.mkdir(parents=True,exist_ok=True)
    for name,(url,md5) in FILES.items():
        target=root/name
        if target.exists():raw=target.read_bytes()
        else:
            with urllib.request.urlopen(url,timeout=60) as response:raw=response.read()
            target.write_bytes(raw)
        if md5 and hashlib.md5(raw).hexdigest()!=md5:raise ValueError('Pinned original supplement differs: '+name)
        if name in SNAPSHOT_SHA256 and hashlib.sha256(raw).hexdigest()!=SNAPSHOT_SHA256[name]:raise ValueError('Reviewed source snapshot differs: '+name)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True)
    acquire(p.parse_args().source_root)
