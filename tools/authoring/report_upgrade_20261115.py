"""Template upgrade for information density, search order and rapid reporting (2026-11-15).

Rules (enforced by tests/test_report_style.py):
  Protocol   Every MRI ("Protocol") and CT ("Technique") template states its own acquisition:
             planes and weightings, or contrast phases with timing. Radiographs, ultrasound and
             fluoroscopy have none. Sources: Radiology Assistant first, then Radiopaedia.
  Normal     The heading names the structure, so the normal line does not repeat it
             ("Spleen: Normal."), and adds only pertinent negatives.
  Findings   A finding line starts with the finding, then size, site and qualifier; never with
             a blank. At most 145 characters, three picks, six choices per pick (coded scales excepted).
  Review     No generic "Other findings". The last heading names the remaining review areas.
Run from the repository root: python tools/authoring/report_upgrade_20261115.py
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TEMPLATES = ROOT / 'data' / 'radiology' / 'report-templates'
sys.path.insert(0, str(Path(__file__).resolve().parent))
from report_upgrade_content import PROTOCOLS, REVIEW_AREAS, REWRITES, RENAMES  # noqa: E402
from report_style_20261113 import format_file  # noqa: E402

LEAD = {'Normal': 'Normal.', 'Intact': 'Intact.', 'Patent': 'Patent.', 'Clear': 'Clear.', 'No': 'None.',
        'Preserved': 'Preserved.'}
SKIP = {'and', 'the', 'of', 'or', 'both', 'visualised', 'a', 'an'}
UNIT = r'(?:mm|cm|mL|percent|degrees)'
SIZE = re.compile(rf'^(\[ \](?: x \[ \])* {UNIT}) (.+)$')
PREPOSITION = re.compile(r' (?:in|of|at|on|with|from|arising|centred|along|to|between|within|over|through|extending|,)\b|[,;.]')


def stems(text):
    return {word.lower().rstrip('s') for word in re.findall(r"[A-Za-z']+", text)} - SKIP


def strip_echo(heading, normal):
    """'Spleen: Normal spleen.' carries one word of information; keep that word."""
    first, _, rest = normal.partition('. ')
    first = first.rstrip('.')
    lead, _, tail = first.partition(' ')
    if lead not in LEAD or not tail or stems(tail) != stems(heading):
        return normal
    return LEAD[lead] + (' ' + rest if rest else '')


def finding_first(option):
    """'[ ] mm calculus in the kidney.' -> 'Calculus [ ] mm in the kidney.'"""
    match = SIZE.match(option)
    if not match:
        return option
    size, rest = match.groups()
    # The finding is the noun phrase up to the first preposition or punctuation, outside picks.
    depth, cut = 0, None
    for index, character in enumerate(rest):
        depth += {'[': 1, ']': -1}.get(character, 0)
        if depth == 0 and (PREPOSITION.match(rest, index) or (rest.startswith(' [', index) and re.search(r'[a-z]\w* *$', rest[:index].split(']')[-1]))):
            cut = index
            break
    if cut is None or cut == 0:
        return option
    noun, tail = rest[:cut], rest[cut:]
    if noun.startswith('['):
        end = noun.index(']')
        noun = '[' + ' / '.join(choice[:1].upper() + choice[1:] for choice in noun[1:end].split(' / ')) + noun[end:]
    else:
        noun = noun[:1].upper() + noun[1:]
    return f'{noun} {size}{tail}'


def upgrade(identifier, item):
    for old, new in RENAMES.get(identifier, {}).items():
        for section in item['sections']:
            if section['heading'] == old:
                section['heading'] = new
    if identifier in REVIEW_AREAS:
        target = next((s for s in item['sections'] if s['heading'] in ('Other findings', 'Background brain')), None)
        if target is None:
            target = next(s for s in item['sections'] if s['heading'] == REVIEW_AREAS[identifier][0])
        heading, normal, options = REVIEW_AREAS[identifier]
        target.update(heading=heading, normal=normal, options=options)
    for section in item['sections']:
        section['normal'] = strip_echo(section['heading'], section['normal'])
        section['normal'] = REWRITES.get(section['normal'], section['normal'])
        options = []
        for option in section.get('options', []):
            option = finding_first(option)
            replacement = REWRITES.get(option, option)
            options += replacement if isinstance(replacement, list) else [replacement]
        if options or 'options' in section:
            section['options'] = options
    if identifier in PROTOCOLS:
        protocol = PROTOCOLS[identifier]
        normal, options = (protocol, []) if isinstance(protocol, str) else protocol
        item['technique'] = {'normal': normal, **({'options': options} if options else {})}
    return item


def run(write=True):
    changed = 0
    for path in sorted(TEMPLATES.glob('*.json')):
        data = json.loads(path.read_text(encoding='utf-8'))
        before = json.dumps(data, sort_keys=True)
        for identifier, item in data['templates'].items():
            upgrade(identifier, item)
        if json.dumps(data, sort_keys=True) != before:
            changed += 1
            data['revision'] = '2026-11-15'
            if write:
                path.write_text(format_file(data), encoding='utf-8')
    print(json.dumps({'files_changed': changed, 'protocols': len(PROTOCOLS), 'review_areas': len(REVIEW_AREAS),
                      'rewrites': len(REWRITES)}))


if __name__ == '__main__':
    run()
