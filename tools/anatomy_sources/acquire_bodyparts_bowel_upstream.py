#!/usr/bin/env python3
"""Acquire all original bowel-region pieces without converting source groups into approved continuity."""
import argparse
from pathlib import Path
from tools.anatomy_sources.acquire_bodyparts_pancreatic_upstream import acquire

TARGETS={'FMA7206':'Duodenum','FMA16981':'Proximal part of jejunum','FMA16982':'Middle part of jejunum',
         'FMA16983':'Distal part of jejunum','FMA14964':'Proximal part of ileum','FMA14965':'Middle part of ileum',
         'FMA14966':'Distal part of ileum','FMA14545':'Ascending colon','FMA14546':'Transverse colon',
         'FMA14547':'Descending colon','FMA14544':'Rectum'}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True)
    acquire(p.parse_args().source_root,targets=TARGETS,filename='bowel-source-4.3')
