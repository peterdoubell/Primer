#!/usr/bin/env python3
"""Preserve complete original T2 anal tumour/timepoint examples without volume or outcome inference."""
import argparse
import hashlib
from pathlib import Path
import urllib.request
from tools.anatomy_sources.acquire_hernia_valsalva_figures import acquire

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    a.source_root.mkdir(parents=True,exist_ok=True)
    metadata=a.source_root/'PMC10784345.1.json'
    if not metadata.exists():
        with urllib.request.urlopen('https://pmc-oa-opendata.s3.amazonaws.com/PMC10784345.1/PMC10784345.1.json',timeout=60) as response:
            metadata.write_bytes(response.read())
    if hashlib.sha256(metadata.read_bytes()).hexdigest()!='459fcbbc69457bebed28500068bc31789c3bc0a989f41a05a6899543497771b3':
        raise ValueError('Reviewed source metadata snapshot differs')
    acquire(a.source_root,a.output,{2:(6,1,65)},{2:dict.fromkeys('abcd','MRI')},
            modality='MRI',pmcid='PMC10784345',extraction_prefix='anal-mri-pdf',allow_icc_without_alternate=True)
