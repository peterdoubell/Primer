#!/usr/bin/env python3
"""Preserve original published dynamic wall MRI figures without stacking time as depth."""
import argparse
from pathlib import Path
from tools.anatomy_sources.acquire_hernia_valsalva_figures import acquire

SELECTION = {2: (4, 3, 129), 3: (5, 5, 157)}
PANELS = {2: {'A':'MRI','B':'MRI','C':'Schematic','D':'MRI','E':'Schematic'}, 3: dict.fromkeys('ab', 'MRI')}

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source-root', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    acquire(a.source_root, a.output, SELECTION, PANELS, modality='MRI',
            pmcid='PMC13045036', extraction_prefix='wall-dynamic-pdf', allow_icc_without_alternate=True)
