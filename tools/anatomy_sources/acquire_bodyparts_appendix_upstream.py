#!/usr/bin/env python3
"""Acquire original appendix and mesoappendix objects without inferred bowel interfaces."""
import argparse
from pathlib import Path
from tools.anatomy_sources.acquire_bodyparts_pancreatic_upstream import acquire

TARGETS = {'FMA14542': 'Appendix', 'FMA16549': 'Mesoappendix'}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', type=Path, required=True)
    acquire(parser.parse_args().source_root, targets=TARGETS, filename='appendix-source-4.3')
