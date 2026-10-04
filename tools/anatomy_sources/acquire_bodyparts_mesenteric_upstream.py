#!/usr/bin/env python3
"""Acquire original mesenteric arterial/venous source groups without inventing branch continuity."""
import argparse
from pathlib import Path
from tools.anatomy_sources.acquire_bodyparts_pancreatic_upstream import acquire

REQUESTED_TARGETS = {
    'FMA14812': 'Celiac trunk',
    'FMA14749': 'Source superior mesenteric artery compound',
    'FMA66358': 'Trunk of superior mesenteric artery',
    'FMA14750': 'Source inferior mesenteric artery compound',
    'FMA66359': 'Trunk of inferior mesenteric artery',
    'FMA14815': 'Source ileocolic artery compound',
    'FMA66499': 'Trunk of ileocolic artery',
    'FMA75856': 'Trunk of superior branch of ileocolic artery',
    'FMA75857': 'Trunk of inferior branch of ileocolic artery',
    'FMA14819': 'Ileal branch of inferior branch of ileocolic artery',
    'FMA14820': 'Ascending branch of inferior branch of ileocolic artery',
    'FMA14810': 'Middle colic artery', 'FMA14811': 'Right colic artery',
    'FMA14826': 'Left colic artery', 'FMA14828': 'Ascending branch of left colic artery',
    'FMA14829': 'Descending branch of left colic artery', 'FMA14830': 'Sigmoid artery',
    'FMA14832': 'Source superior rectal artery compound', 'FMA66504': 'Trunk of superior rectal artery',
    'FMA14824': 'Marginal colic artery',
    'FMA14805': 'Source inferior pancreaticoduodenal artery compound',
    'FMA70479': 'Anterior inferior pancreaticoduodenal artery',
    'FMA70480': 'Posterior inferior pancreaticoduodenal artery',
    'FMA14782': 'Anterior superior pancreaticoduodenal artery',
    'FMA14784': 'Posterior superior pancreaticoduodenal artery',
    'FMA14332': 'Superior mesenteric vein', 'FMA15391': 'Inferior mesenteric vein',
    'FMA15408': 'Ileocolic vein', 'FMA15406': 'Middle colic vein', 'FMA15407': 'Right colic vein',
    'FMA15394': 'Left colic vein', 'FMA15398': 'Pancreaticoduodenal vein',
    'FMA14331': 'Splenic vein', 'FMA71904': 'Pre-hepatic portal vein',
}

# This named legacy mapping row has no entry in the selected 4.3 manifest.
# Preserve the requirement as a source hold; do not invent a replacement.
SOURCE_HOLDS = {'FMA14820': 'Ascending branch of inferior branch of ileocolic artery absent from selected version-4.3 manifest'}
TARGETS = {key: label for key, label in REQUESTED_TARGETS.items() if key not in SOURCE_HOLDS}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', type=Path, required=True)
    acquire(parser.parse_args().source_root, targets=TARGETS, filename='mesenteric-source-4.3')
