"""One house style across every report template (tools/authoring/report_style_20261113.py)."""
import collections
import json
import re
from pathlib import Path

from primer import report_templates as rt

ROOT = Path(__file__).resolve().parents[1]
PRISM = json.loads((ROOT / 'data/radiology/prism-titles.json').read_text())
MODALITY = {
    'CT': r'\bCT\b|\bHRCT\b',
    'MRI': r'\bMRI?\b|\bMRA\b|\bMRCP\b|\bMR\b|STIR|FLAIR|gadolinium',
    'US': r'ultrasound|sonograph|duplex|Doppler|transducer|echocardiogra',
    'XR': r'(?<!correlated with )radiograph',
}


def modalities(text):
    return {m for m, p in MODALITY.items() if re.search(p, text, re.I)}


def test_titles_are_unique_and_name_one_modality():
    library = rt.library()
    counts = collections.Counter(item['title'] for item in library.values())
    assert [t for t, n in counts.items() if n > 1] == []
    for identifier, item in library.items():
        assert len(modalities(item['title'])) <= 1, (identifier, item['title'])


def test_technique_describes_the_examination_s_own_modality():
    for identifier, item in rt.library().items():
        title = modalities(item['title'])
        if 'technique' not in item or not title:
            continue
        for text in [item['technique']['normal'], *item['technique'].get('options', [])]:
            assert not (modalities(text) - title), (identifier, text)


def test_every_performed_study_has_prism_titles_owned_once():
    library = rt.library()
    excluded = set(PRISM['not_performed_studies'])
    assert excluded <= set(library)
    seen = set()
    for identifier in library:
        if identifier in excluded:
            continue
        titles = PRISM['titles'].get(identifier)
        assert titles, identifier
        for title in titles:
            assert title.lower() not in seen and ',' not in title, title
            seen.add(title.lower())


def test_normal_lines_are_terse_full_sentences():
    for identifier, item in rt.library().items():
        for section in item['sections']:
            normal = section['normal']
            assert normal[0].isupper() and normal.endswith('.'), (identifier, normal)
            assert not re.search(r'on the acquired images|\b(?:is|are) (?:identified|seen)\b', normal), (identifier, normal)
