#!/usr/bin/env python3
"""Acquire original bilateral renal/ureter/vascular groups without inferred cortical or hilar anatomy."""
import argparse
from pathlib import Path
from tools.anatomy_sources.acquire_bodyparts_pancreatic_upstream import acquire

TARGETS = {'FMA7204':'Right kidney','FMA7205':'Left kidney','FMA15571':'Right ureter','FMA15572':'Left ureter',
           'FMA14335':'Right renal vein','FMA14336':'Left renal vein','FMA66363':'Trunk of right renal artery','FMA66364':'Trunk of left renal artery',
           'FMA70486':'Anterior division of right renal artery','FMA70487':'Anterior division of left renal artery',
           'FMA70489':'Posterior division of right renal artery','FMA70490':'Posterior division of left renal artery',
           'FMA70492':'Ureteric segment of right renal artery','FMA70493':'Ureteric segment of left renal artery'}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root',type=Path,required=True)
    acquire(parser.parse_args().source_root,targets=TARGETS,filename='renal-source-4.3')
