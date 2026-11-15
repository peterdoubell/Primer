#!/usr/bin/env python3
"""Acquire original adrenal glands and available vessels without inferring missing anatomy."""
import argparse
from pathlib import Path
from tools.anatomy_sources.acquire_bodyparts_pancreatic_upstream import acquire

TARGETS = {
    'FMA15630': 'Left adrenal gland', 'FMA15629': 'Right adrenal gland',
    'FMA69266': 'Left inferior suprarenal artery', 'FMA69265': 'Right inferior suprarenal artery',
    'FMA14756': 'Left middle suprarenal artery', 'FMA14755': 'Right middle suprarenal artery',
    'FMA14349': 'Left suprarenal vein', 'FMA14343': 'Right suprarenal vein',
}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', type=Path, required=True)
    acquire(parser.parse_args().source_root, targets=TARGETS, filename='adrenal-source-4.3')
