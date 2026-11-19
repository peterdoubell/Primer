"""Export every performed study's report template as RadProof (M3GAN) template text.

Every template opens with the clinical history and the comparison, then the study name, as Peter asked
(2026-11-19). RadProof puts a template's first line in Prism's title slot, so Clinical history takes it:
  **__Clinical history:__** []  bold and underlined, each with a blank to fill
  **__Comparison:__** []
  **__<Study title>:__**       bold and underlined, in sentence case: no heading is all capitals
                               (Peter, 2026-11-19); {Side} where Prism supplies the side, radiograph{s}
                               for the views. The bar itself prints the first line in capitals.
  **__Protocol:__** / **__Technique:__**  MRI protocol or CT technique (no other modality has one)
  **__Findings:__**            after a protocol or technique; radiographs, ultrasound and
                               fluoroscopy run from the study title straight into their findings
  **__Impression:__** (dictation) or **__Conclusion:__** (normal report)
The dictation layout (--dictation) lists every heading with a blank, one under another; a subheading over
the headings it groups (Intrinsic ligaments:) stands apart with a blank line around it. Bold and underline
are only for section headings (Peter, 2026-11-19): subheadings and the headings with a blank are plain.
The normal-report layout writes one sentence per line. Every line reads on its own, adjective first: a
bare "Normal." under Spleen is written "Normal spleen.", and a line that two sections share takes its
heading ("Right vertebral artery: patent ..."). Headings under one subheading that are normal in the same
words are said once ("Intact intrinsic ligaments.", "Right carotid: no plaque or stenosis."). A section
that only restates the conclusion (stage, category) is left out.
A single-region radiograph says radiograph{s}: the bar adds the s for two or more views, which it reads
from Prism's title ("Right knee, two views").
RadProof markup: ** toggles bold, __ toggles underline; a short line ending in a colon is a heading.

Usage: python3 tools/authoring/radproof_export.py --dictation > radproof-templates.json
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from primer import report_templates as rt  # noqa: E402

DATA = ROOT / 'data' / 'radiology'
MULTI_REGION = {'ct.trauma-panscan', 'ct.oncology-staging', 'xr.acute-abdomen-series', 'ra.recist',
                'oncology.recist-follow-up', 'ra.ct-peritoneal-carcinomatosis'}
# Normal lines that say nothing without their heading.
BARE = {'Normal.', 'None.', 'Clear.', 'Intact.', 'Patent.', 'Preserved.', 'Not involved.'}
# One region, so one radiograph or several by the views Prism's title gives.
COUNTED = re.compile(r"^(?:\{Side\} )?[A-Za-z' -]+ radiographs?$")
VIEWS = re.compile(r', (?:PA and lateral|AP|supine)$')  # Prism's title gives the views
NAME = re.compile(r"^[A-Za-z0-9 ,()&+'.\-]{1,80}$")


# Sections that restate the conclusion in a normal report: the stage or the category.
SUMMARY = re.compile(r'^(?:[A-Za-z]{1,4}-RADS|(?:FIGO |Modified Bell )?[Ss]tage|Classification|Resectability'
                     r'|(?:[A-Za-z-]+ )?[Cc]ategory|Response assessment|Expression for therapy)$')
# "None." under these headings needs more than "No <heading>.".
NONE = {'Fractures': 'No fracture.', 'Strictures': 'No stricture.', 'Subdural collections': 'No subdural collection.',
        'Other pain generators': 'No other pain generator.', 'Lines and tubes': 'No lines or tubes.',
        'Satellite lesions and lymph nodes': 'No satellite lesion or lymphadenopathy.',
        'Joint and neurovascular bundle': 'No joint or neurovascular involvement.'}
PROPER = {'Graf', 'Agatston', 'Böhler', 'Lisfranc', 'Baker', 'Morton', 'Achilles', 'Hoffa', 'Meckel', 'Bosniak', 'Bern'}


def study_title(title):
    parts = title.split(' / ')
    if len(parts) >= 2 and parts[0].replace('Right', 'Left').replace('right', 'left') == parts[1]:
        if len(parts) > 2:  # right, left or both: one template serves all three, so it names no side
            return re.sub(r'\b[Rr]ight ', '', parts[0])
        return parts[0].replace('Right', '{Side}').replace('right', '{side}')
    return parts[0]


def lower_first(text):
    first = re.match(r"[\w'-]+", text).group()
    proper = first in PROPER or first.isupper() or any(c.isupper() or c.isdigit() for c in first[1:])
    return text if proper else text[0].lower() + text[1:]


def self_contained(heading, sentence):
    """A bare normal ("Normal.", "None.") as a sentence that names its subject."""
    if sentence not in BARE:
        return sentence
    if sentence in {'None.', 'Not involved.'}:
        return NONE.get(heading) or 'No ' + lower_first(heading).replace(' and ', ' or ') + '.'
    return f'{sentence[:-1]} {lower_first(heading)}.'


def findings(item, multi_region):
    """The normal findings, one sentence per line, each readable without its section heading.

    Headings under one subheading that are all normal in the same words are said once, of the
    subheading ("Intact intrinsic ligaments.", "Lumbar discs: no disc herniation ..."). In a
    multi-region study a subheading is the region, printed above its lines.
    """
    rows = []  # (label, line, always labelled); a row without a label is printed as it is
    for group, members in rt._blocks([section for section in item['sections']
                                      if multi_region or not SUMMARY.match(section['heading'])]):
        normals = [sentences(section['normal']) for section in members]
        if multi_region and not group:
            rows += [(None, line, False) for line in [members[0]['heading'], *normals[0]]]
            continue
        if multi_region:
            rows.append((None, group, False))
        elif group and len(normals[0]) == 1 and all(lines == normals[0] for lines in normals):
            rows.append((group, self_contained(group, normals[0][0]), normals[0][0] not in BARE))
            continue
        rows += [(section['heading'], self_contained(section['heading'], sentence), False)
                 for section, lines in zip(members, normals) for sentence in lines]
    shared = {line for label, line, _ in rows if label and sum(bool(other) and text == line for other, text, _ in rows) > 1}
    return [f'{label}: {lower_first(line)}' if label and (always or line in shared) else line for label, line, always in rows]


def is_radiograph(identifier, item):
    return rt.acquisition_heading(identifier, item) is None and 'radiograph' in item['title'].lower()


def counted(text):
    return re.sub(r'\bradiographs?\b', 'radiograph{s}', text)


def sentences(text):
    return [s if s.endswith('.') else s + '.' for s in re.split(r'(?<=\.)\s+(?=[A-Z])', text.strip()) if s]


# Every template opens with the clinical history and the comparison, then the study name (Peter, 2026-11-19).
# RadProof puts a template's first line in Prism's title slot, so Clinical history takes that line and the
# study name follows, a heading like the others.
HISTORY = ['**__Clinical history:__**', '[]', '', '**__Comparison:__**', '[]', '']
# Bold and underline only for headings (Peter's M3GAN layout, 2026-11-19): every section heading is both,
# as RadProof sets out a section heading; subheadings and the headings with a blank are plain.
SECTION = {name + ':': '**__' + name + ':__**' for name in ('Protocol', 'Technique', 'Findings', 'Impression', 'Recommendation')}


def title_heading(title):
    """The study name as a heading: bold, underlined and in sentence case, never all capitals (Peter, 2026-11-19)."""
    return '**__' + title + ':__**'


def dictation_text(item, acquisition, title):
    """Clinical history, comparison, the study name, then the study's headings, each with a blank to fill."""
    draft = rt.render_dictation(item, acquisition)
    study = draft['text'].split('\n\n', 2)[2].splitlines()
    name = draft['title'] if item.get('dictation') else title
    return '\n'.join([*HISTORY, title_heading(name), *(SECTION.get(line, line) for line in study[1:])])


def export(*, dictation=False):
    library = rt.library()
    prism = json.loads((DATA / 'prism-titles.json').read_text())
    practice = {n['name'].lower() for n in json.loads((DATA / 'radproof-practice-library.json').read_text())['templates']}
    out, names = [], set()
    for identifier, item in library.items():
        if identifier in prism['not_performed_studies']:
            continue
        title = study_title(item['title'])
        name = title.replace('{Side} ', '').replace('{side} ', '')
        name = re.sub(r'[^A-Za-z0-9 ,()&+\'.\-]', ' ', name[0].upper() + name[1:]).replace('  ', ' ').strip()
        if name.lower() in practice:
            name += ' (Primer)'  # a practice name would replace the practice's own normal
        base, n = name, 2
        while name.lower() in names:
            name, n = f'{base} ({n})', n + 1
        names.add(name.lower())
        assert NAME.match(name), name
        impression = item['impression'] if isinstance(item['impression'], list) else [item['impression']]
        radiograph = is_radiograph(identifier, item)
        if radiograph and COUNTED.match(VIEWS.sub('', title)):
            title = VIEWS.sub('', title)
            title, impression = counted(title), [counted(line) for line in impression]
        lines = [*HISTORY, title_heading(title)]
        acquisition = rt.acquisition_heading(identifier, item)
        if acquisition:
            lines += [SECTION[acquisition + ':'], item['technique']['normal'], '']
        if not radiograph:
            lines.append(SECTION['Findings:'])
        lines += findings(item, identifier in MULTI_REGION)
        lines += ['', '**__Conclusion:__**', *impression]
        text = dictation_text(item, acquisition, title) if dictation else '\n'.join(lines)
        out.append({'id': identifier, 'name': name, 'names': prism['titles'][identifier], 'text': text})
    return out


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dictation', action='store_true', help='Export the editable dictation templates.')
    result = export(dictation=parser.parse_args().dictation)
    sys.stdout.write(json.dumps(result, ensure_ascii=False, separators=(',', ':')))
    print(len(result), 'templates;', sum(len(t['names']) for t in result), 'Prism titles', file=sys.stderr)
