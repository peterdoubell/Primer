#!/usr/bin/env python3
"""Preserve complete IUS-bearing source figures, including original grayscale artwork."""
import argparse
from pathlib import Path
from tools.anatomy_sources.acquire_crohn_mri_figures import acquire, PANELS

SELECTION = {1: (5, 14, 65), 2: (6, 15, 85), 4: (8, 17, 109), 5: (8, 18, 110)}
ROLES = {n: PANELS[n] for n in (1, 2, 4)}
ROLES[5] = {'a': 'Ultrasound', 'b': 'CT'}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    acquire(args.source_root, args.output, SELECTION, ROLES, 'Ultrasound')
