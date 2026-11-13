"""Every practice study has an examination; each examination is one modality; Prism titles are unambiguous."""
import json
import re
from pathlib import Path

from primer import report_templates as rt

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/radiology'
PRACTICE = json.loads((DATA / 'radproof-practice-library.json').read_text())['templates']
TITLES = json.loads((DATA / 'prism-titles.json').read_text())
MODALITY = {
    'CT': r'\bCT\b|\bHRCT\b',
    'MRI': r'\bMRI?\b|\bMRCP\b|MR neurography|MR angiogram|MR venogram|MR enterography',
    'US': r'ultrasound|duplex|doppler|echocardiogram',
    'XR': r'radiograph|skeletal survey|cephalometric',
    'MG': r'mammograph|stereotactic breast',
    'FL': r'fluoroscop|swallow|barium|enema|defecography|cystogram|cystourethrogram|urethrogram|pyelogram|hysterosalpingogram|follow-through|lumbar puncture|arthrogram',
}


def test_every_practice_study_maps_to_a_served_examination():
    library = rt.library()
    assert set(TITLES['practice_studies']) == {n['name'] for n in PRACTICE}
    assert all(identifier in library for identifier in TITLES['practice_studies'].values())


def test_prism_titles_belong_to_one_examination_and_come_from_the_practice():
    library = rt.library()
    seen = {}
    practice_titles = {t.lower() for n in PRACTICE for t in n['names']}
    # Every practice title is owned by an examination unless the practice shares it between studies.
    for identifier, titles in TITLES['titles'].items():
        assert identifier in library
        for title in titles:
            assert title.lower() not in seen, title
            seen[title.lower()] = identifier
    assert not set(seen) & {t.lower() for t in TITLES['shared_left_to_practice']}
    assert practice_titles - {t.lower() for t in TITLES['shared_left_to_practice']} <= set(seen)


def test_each_examination_title_names_one_modality():
    for identifier, item in rt.library().items():
        if identifier.startswith('template:'):
            continue  # review worksheets, not performed examinations
        found = {m for m, p in MODALITY.items() for part in item['title'].split(' / ') if re.search(p, part, re.I)}
        assert len(found) <= 1, (identifier, item['title'], found)
