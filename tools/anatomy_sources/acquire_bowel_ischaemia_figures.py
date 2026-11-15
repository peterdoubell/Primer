#!/usr/bin/env python3
"""Verify complete original arterial, venous and wall-injury CT source figures."""
import argparse
from pathlib import Path
from tools.anatomy_sources.acquire_bowel_obstruction_figures import acquire

# Original PDF page, pdfimages index and object ID; uppercase labels are native.
SELECTION = {'PMC10066158': {
    2: (4, 1, 54, dict.fromkeys('AB', 'CT')),
    3: (5, 2, 84, dict.fromkeys('AB', 'CT')),
    4: (6, 3, 94, dict.fromkeys('ABC', 'CT')),
    5: (7, 4, 103, dict.fromkeys('AB', 'CT')),
    6: (7, 5, 105, dict.fromkeys('AB', 'CT')),
    7: (8, 6, 117, dict.fromkeys('AB', 'CT')),
    8: (9, 7, 133, dict.fromkeys('ABCD', 'CT')),
    9: (10, 8, 140, dict.fromkeys('AB', 'CT')),
}}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    acquire(args.source_root, args.output, SELECTION)
