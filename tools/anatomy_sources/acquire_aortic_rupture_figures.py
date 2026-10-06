#!/usr/bin/env python3
"""Preserve original clinical CT, schematics and source-rendering panels without geometry inference."""
import argparse
import hashlib
from pathlib import Path
import urllib.request
from tools.anatomy_sources.acquire_hernia_valsalva_figures import acquire

SELECTION={1:(3,0,38),2:(4,1,53),3:(4,2,54),4:(5,3,61),5:(5,4,62),6:(6,5,83),
           7:(7,6,93),8:(7,7,94),9:(8,8,110),10:(8,9,111),11:(9,10,114),12:(9,11,115),13:(10,12,139)}
PANELS={1:dict.fromkeys('abcd','CT'),2:{'a':'Schematic','b':'CT','c':'CT'},3:{'a':'Schematic','b':'CT'},
        4:{'a':'Schematic','b':'CT','c':'CT'},5:{'a':'Schematic','b':'CT'},6:{'a':'Schematic','b':'CT','c':'CT'},
        7:dict.fromkeys('ab','CT'),8:dict.fromkeys('ab','CT'),9:dict.fromkeys('ab','CT'),10:dict.fromkeys('ab','CT'),
        11:{'a':'Schematic','b':'CT','c':'CT'},12:dict.fromkeys('abc','CT'),13:{'a':'CT','b':'Radiography','c':'CT','d':'CT'}}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();a.source_root.mkdir(parents=True,exist_ok=True)
    metadata=a.source_root/'PMC4035490.1.json'
    if not metadata.exists():
        with urllib.request.urlopen('https://pmc-oa-opendata.s3.amazonaws.com/PMC4035490.1/PMC4035490.1.json',timeout=60) as response:
            metadata.write_bytes(response.read())
    if hashlib.sha256(metadata.read_bytes()).hexdigest()!='c5ceb17078c0b6400e021ef398d2e5eb89e1f14e10efda6fab00c701f08f68fd':
        raise ValueError('Reviewed source metadata snapshot differs')
    acquire(a.source_root,a.output,SELECTION,PANELS,pmcid='PMC4035490',extraction_prefix='aortic-rupture-pdf',allow_icc_without_alternate=True,allow_flate_samples=True)
