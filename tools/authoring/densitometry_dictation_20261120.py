"""Peter's own densitometry line in the dictation layout (2026-11-20).

His densitometry template gives each site one line to fill:

  Spine: BMD = [], T-score = [] ([]).

The uniform dictation layout gives a heading one blank ("Spine: []"), which would leave him to dictate
"BMD equals ..., T-score equals ..." for six sites. So this study carries its own dictation lines, as the
prostate department's draft does: one line for each heading of the template, in the template's order,
stacked like every other template's. The forearm's side is a blank, as in his template. The rest of the
layout is the house one: clinical history, comparison, the study name, impression and recommendation.

The headings themselves are written by report_structures_20261117.py (report_structures_uniform.py).

Usage: python3 tools/authoring/densitometry_dictation_20261120.py   (idempotent)
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from primer import report_templates as rt  # noqa: E402

PATH = ROOT / 'data' / 'radiology' / 'report-templates' / 'additions-20261112.json'
IDENTIFIER = 'dxa.bone-densitometry'
TECHNIQUE = 'DXA of the lumbar spine, both hips and a forearm.'
LINE = 'BMD = [], T-score = [] ([]).'
LABEL = {'Forearm': '[] forearm'}  # he fills in the side


def draft(item):
    """The dictation lines: every heading of the template with his line to fill."""
    return {'title': item['title'], 'technique': TECHNIQUE,
            'findings': [f"{LABEL.get(section['heading'], section['heading'])}: {LINE}" for section in item['sections']]}


def block(value):
    findings = ',\n'.join('          ' + json.dumps(line, ensure_ascii=False) for line in value['findings'])
    return ('      "dictation": {\n'
            f'        "title": {json.dumps(value["title"], ensure_ascii=False)},\n'
            f'        "technique": {json.dumps(value["technique"], ensure_ascii=False)},\n'
            '        "findings": [\n' + findings + '\n        ]\n      },\n')


def rewrite(text):
    """The library file with the study's technique and dictation lines written in."""
    item = json.loads(text)['templates'][IDENTIFIER]
    opening = f'    "{IDENTIFIER}": {{\n'
    start = text.index(opening) + len(opening)
    # The template's own title line, at its indent: an earlier draft, if any, lies before it and is replaced.
    title = text.index('\n      "title": ', start - 1) + 1
    text = text[:start] + block(draft(item)) + text[title:]
    technique = re.compile(r'      "technique": \{"normal": "[^"]*"').search(text, start)
    return (text[:technique.start()] + '      "technique": {"normal": ' + json.dumps(TECHNIQUE, ensure_ascii=False)
            + text[technique.end():])


def main():
    before = PATH.read_text(encoding='utf-8')
    after = rewrite(before)
    for identifier, item in json.loads(after)['templates'].items():
        rt.validate(identifier, item)
    if after != before:
        PATH.write_text(after, encoding='utf-8')
    print('densitometry dictation lines', 'written' if after != before else 'already written')


if __name__ == '__main__':
    main()
