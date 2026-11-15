#!/usr/bin/env python3
"""Acquire original available peritoneal source sheets without inventing missing recesses."""
import argparse
from pathlib import Path
from tools.anatomy_sources.acquire_bodyparts_pancreatic_upstream import acquire

TARGETS={'FMA14643':'Mesentery of small intestine','FMA14647':'Transverse mesocolon','FMA19757':'Posterior part of abdominal peritoneum'}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True)
    acquire(p.parse_args().source_root,targets=TARGETS,filename='peritoneal-source-4.3')
