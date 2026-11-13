"""Export every performed study's normal report as RadProof (M3GAN) template text.

Layout follows the practice's Prism reports, from the study title down:
  **__<Study title>__**        bold and underlined; {Side} where Prism supplies the side
  __Protocol:__                underlined; the standard protocol (not for radiographs)
  __Findings:__                underlined; one sentence per line; multi-region studies keep
                               plain region subheadings (RadProof text has no italics)
  **__Conclusion:__**          bold and underlined; the normal impression
Clinical history and comparison sit above the inserted template in Prism.
RadProof markup: ** toggles bold, __ toggles underline; a short line ending in a colon is a
heading, so subheadings carry no colon.

Usage: python3 tools/authoring/radproof_export.py > radproof-templates.json
"""
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
NAME = re.compile(r"^[A-Za-z0-9 ,()&+'.\-]{1,80}$")


def study_title(title):
    parts = title.split(' / ')
    if len(parts) == 2 and parts[0].replace('Right', 'Left').replace('right', 'left') == parts[1]:
        return parts[0].replace('Right', '{Side}').replace('right', '{side}')
    return parts[0]


def sentences(text):
    return [s if s.endswith('.') else s + '.' for s in re.split(r'(?<=\.)\s+(?=[A-Z])', text.strip()) if s]


def export():
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
        lines = ['**__' + title + '__**']
        if not item['radiograph']:
            lines += ['__Protocol:__', item['technique']['normal'], '']
        lines.append('__Findings:__')
        for section in item['sections']:
            if identifier in MULTI_REGION:
                lines.append(section['heading'])
            lines += sentences(section['normal'])
        impression = item['impression'] if isinstance(item['impression'], list) else [item['impression']]
        lines += ['', '**__Conclusion:__**', *impression]
        out.append({'id': identifier, 'name': name, 'names': prism['titles'][identifier], 'text': '\n'.join(lines)})
    return out


if __name__ == '__main__':
    result = export()
    sys.stdout.write(json.dumps(result, ensure_ascii=False, separators=(',', ':')))
    print(len(result), 'templates;', sum(len(t['names']) for t in result), 'Prism titles', file=sys.stderr)
