"""Radiograph Prism titles name the region only, and 3D ultrasound uterus is not a template of its own.

Prism titles radiographs by region and views, never by modality: "Right knee, two views",
"Chest, single view", "Right ankle". The bar takes the side and the number of views from the
title itself, so a radiograph's Prism titles keep only the region ("knee", "skyline knee"). Commas
separate titles in RadProof's Names: line, so a title cannot hold one.

3D ultrasound of the uterus is reported in the pelvic ultrasound report; its titles move there.

Usage: python3 tools/authoring/radiograph_titles_20261116.py   (idempotent; rewrites prism-titles.json)
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from primer import report_templates as rt  # noqa: E402

PATH = ROOT / 'data' / 'radiology' / 'prism-titles.json'
MODALITY_WORD = re.compile(r'\b(?:x-?rays?|radiographs?|radiography|xr)\b', re.I)
# Bare words that would name another study once the modality is gone.
AMBIGUOUS = {'neck'}
MERGED = {'us.uterus-3d': 'ra.ultrasound-acute-gynaecology'}


def is_radiograph(identifier, item):
    return rt.acquisition_heading(identifier, item) is None and 'radiograph' in item['title'].lower()


# Adjectives that read as regions once "x-ray" is gone ("abdominal x-ray" is the abdomen).
REGION = {'abdominal': 'abdomen', 'pelvic': 'pelvis', 'femoral': 'femur', 'orbital': 'orbits',
          'sternal': 'sternum', 'cephalometric': 'cephalogram'}


def region_only(title):
    words = re.sub(r'\s+', ' ', MODALITY_WORD.sub(' ', title)).strip().split(' ')
    return ' '.join(REGION.get(word, word) for word in words if word)


def apply(prism, library):
    titles = prism['titles']
    for identifier, home in MERGED.items():
        for title in titles.pop(identifier, []):
            if title.lower() not in {t.lower() for t in titles[home]}:
                titles[home].append(title)
        if identifier not in prism['not_performed_studies']:
            prism['not_performed_studies'].append(identifier)
    taken = {t.lower() for i, ts in titles.items() if not is_radiograph(i, library[i]) for t in ts}
    for identifier, item in library.items():
        if identifier not in titles or not is_radiograph(identifier, item):
            continue
        kept = []
        for title in titles[identifier]:
            title = region_only(title)
            if title and title.lower() not in AMBIGUOUS and title.lower() not in taken:
                kept.append(title)
                taken.add(title.lower())
        titles[identifier] = kept
    return prism


if __name__ == '__main__':
    prism = apply(json.loads(PATH.read_text()), rt.library())
    PATH.write_text(json.dumps(prism, indent=1, ensure_ascii=False) + '\n')
