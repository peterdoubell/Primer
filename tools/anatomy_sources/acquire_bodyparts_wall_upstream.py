#!/usr/bin/env python3
"""Acquire explicit original wall source pieces, retaining the source M-marked representation."""
import argparse
from pathlib import Path
from tools.anatomy_sources.acquire_bodyparts_pancreatic_upstream import acquire

TARGETS={'FMA11336':'Linea alba','FMA13336':'Right external oblique','FMA13337':'Left external oblique',
         'FMA21964':'Right inguinal ligament','FMA21965':'Left inguinal ligament'}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True)
    acquire(p.parse_args().source_root,targets=TARGETS,filename='wall-source-4.3',allow_mirrored_source_ids=True)
