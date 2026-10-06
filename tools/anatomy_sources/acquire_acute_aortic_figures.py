#!/usr/bin/env python3
"""Preserve original AAS CT artwork and a separately typed conceptual diagram."""
import argparse
import hashlib
from pathlib import Path
import urllib.request
from tools.anatomy_sources.acquire_hernia_valsalva_figures import acquire

SELECTION={1:(3,0,48),3:(4,2,52),4:(5,3,75),5:(6,4,94),6:(7,5,110),7:(8,6,125),8:(9,7,133),9:(9,8,134),10:(10,9,141)}
PANELS={1:dict.fromkeys('abcd','CT'),3:dict.fromkeys('abcd','CT'),4:dict.fromkeys('abc','CT'),
        5:dict.fromkeys('abc','CT'),6:dict.fromkeys('abcd','CT'),7:dict.fromkeys('abc','CT'),
        8:dict.fromkeys('ab','CT'),9:dict.fromkeys('abc','CT'),10:dict.fromkeys('abcd','CT')}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();a.source_root.mkdir(parents=True,exist_ok=True);metadata=a.source_root/'PMC3505562.1.json'
    if not metadata.exists():
        with urllib.request.urlopen('https://pmc-oa-opendata.s3.amazonaws.com/PMC3505562.1/PMC3505562.1.json',timeout=60) as r:metadata.write_bytes(r.read())
    if hashlib.sha256(metadata.read_bytes()).hexdigest()!='4cbde10caededb5e29c67669144f339810ea3729c582046a479923e83f5499fe':raise ValueError('Reviewed metadata snapshot differs')
    acquire(a.source_root,a.output,SELECTION,PANELS,pmcid='PMC3505562',extraction_prefix='acute-aortic-pdf',allow_icc_without_alternate=True)
    acquire(a.source_root,a.output/'conceptual-diagram',{2:(4,1,51)},{2:{'diagram':'Schematic'}},
            modality='Schematic',pmcid='PMC3505562',extraction_prefix='acute-aortic-pdf',allow_icc_without_alternate=True)
