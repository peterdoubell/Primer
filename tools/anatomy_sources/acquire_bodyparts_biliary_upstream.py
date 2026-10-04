#!/usr/bin/env python3
"""Acquire original biliary source groups without fusing repeated representations."""
import argparse
from pathlib import Path
from tools.anatomy_sources.acquire_bodyparts_pancreatic_upstream import acquire

TARGETS = {
    'FMA14668': 'Common hepatic duct', 'FMA14539': 'Cystic duct', 'FMA7202': 'Gallbladder',
    'FMA14670': 'Left hepatic duct', 'FMA14669': 'Right hepatic duct',
    'FMA71867': 'Anterior superior tributary of right hepatic biliary tree',
    'FMA71868': 'Anterior inferior tributary of right hepatic biliary tree',
    'FMA71869': 'Posterior superior tributary of right hepatic biliary tree',
    'FMA71870': 'Posterior inferior tributary of right hepatic biliary tree',
    'FMA71887': 'Lateral superior tributary of left hepatic biliary tree',
    'FMA71888': 'Lateral inferior tributary of left hepatic biliary tree',
    'FMA71885': 'Medial superior tributary of left hepatic biliary tree',
    'FMA71886': 'Medial inferior tributary of left hepatic biliary tree',
    'FMA71889': 'Caudate lobe tributary of left hepatic biliary tree',
}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('--source-root', type=Path, required=True)
    acquire(p.parse_args().source_root, targets=TARGETS, filename='biliary-source-4.3')
