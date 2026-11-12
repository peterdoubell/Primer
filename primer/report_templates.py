"""Fast report templates and normal reports, laid out for pasting into a RIS.

Each examination has a study title and short sentence-case headings. Under a
heading the first line is the normal finding; the lines after it are the
common abnormal findings, written with picks ``[a / b]`` and blanks ``[ ]``
only where the reader must explain. The same data renders a complete normal
report. Radiographs have no Technique or Comparison headings.
"""
from functools import lru_cache
import json
import re
from pathlib import Path

LIBRARY = Path(__file__).resolve().parents[1] / 'data' / 'radiology' / 'report-templates'
SCHEMA = 'primer.fast-report-templates/1'
RESERVED = {'clinical history', 'technique', 'comparison', 'impression', 'recommendation'}
COMPARISON = {'heading': 'Comparison', 'normal': 'None.', 'options': ['Compared with [ ].']}
LIMITATION = 'Limited by [ ].'
HISTORY = 'Clinical history:\n[ ].'
BLANK_IMPRESSION = 'Impression:\n1. []\n2. []\n3. []'
BLANK_RECOMMENDATION = 'Recommendation:\n[ ].'
HEADING = re.compile(r"[A-Z][\w ,/()'\-]*[\w)]")


def _sentence(text, where):
    if not isinstance(text, str) or not text.strip() or text != text.strip() or '\n' in text:
        raise ValueError(f'{where}: expected one trimmed line')
    if not text.endswith('.'):
        raise ValueError(f'{where}: end with a full stop')
    return text


def _normal(text, where):
    _sentence(text, where)
    if '[' in text or ']' in text:
        raise ValueError(f'{where}: a normal line is complete, without picks or blanks')
    return text


def _option(text, where):
    _sentence(text, where)
    depth = 0
    for character in text:
        depth += {'[': 1, ']': -1}.get(character, 0)
        if depth not in (0, 1):
            raise ValueError(f'{where}: brackets must be paired and not nested')
    if depth:
        raise ValueError(f'{where}: brackets must be paired')
    for field in re.findall(r'\[([^\[\]]*)\]', text):
        choices = field.split(' / ')
        if field != ' ' and (len(choices) < 2 or any(not choice.strip() or choice != choice.strip() for choice in choices)):
            raise ValueError(f'{where}: write [ ] for a blank or [a / b] for a pick, not [{field}]')
    return text


def _section(section, where):
    if set(section) - {'heading', 'normal', 'options'} or 'heading' not in section or 'normal' not in section:
        raise ValueError(f'{where}: a section has heading, normal and options')
    heading = section['heading']
    if not isinstance(heading, str) or not HEADING.fullmatch(heading) or len(heading) > 60:
        raise ValueError(f'{where}: heading {heading!r} must be short sentence case without punctuation at the end')
    if heading.upper() == heading and ' ' in heading:
        raise ValueError(f'{where}: heading {heading!r} must be sentence case')
    _normal(section['normal'], f'{where} {heading}')
    options = section.get('options', [])
    if not isinstance(options, list) or len(options) > 4:
        raise ValueError(f'{where} {heading}: at most four finding lines')
    for option in options:
        _option(option, f'{where} {heading}')
    return section


def validate(identifier, item):
    """Return the template unchanged, or raise ValueError naming the defect."""
    allowed = {'title', 'radiograph', 'technique', 'sections', 'impression', 'recommendation'}
    if not isinstance(item, dict) or set(item) - allowed:
        raise ValueError(f'{identifier}: unknown template fields')
    title = item.get('title')
    if (not isinstance(title, str) or not title or title != title.strip() or '\n' in title
            or '[' in title or title.endswith((':', '.'))):
        raise ValueError(f'{identifier}: the study title is one line without brackets or a final colon')
    if not isinstance(item.get('radiograph'), bool):
        raise ValueError(f'{identifier}: say whether the examination is a radiograph')
    if item['radiograph'] == ('technique' in item):
        raise ValueError(f'{identifier}: radiographs have no technique; every other examination has one')
    if 'technique' in item:
        _section({'heading': 'Technique', **item['technique']}, identifier)
    sections = item.get('sections')
    if not isinstance(sections, list) or not 2 <= len(sections) <= 12:
        raise ValueError(f'{identifier}: two to twelve finding headings')
    seen = set()
    for section in sections:
        _section(section, identifier)
        key = section['heading'].lower()
        if key in RESERVED or key in seen:
            raise ValueError(f'{identifier}: heading {section["heading"]!r} is reserved or repeated')
        seen.add(key)
    impression = item.get('impression')
    impression = [impression] if isinstance(impression, str) else impression
    if not isinstance(impression, list) or not 1 <= len(impression) <= 3:
        raise ValueError(f'{identifier}: one to three normal impression lines')
    for line in impression:
        _normal(line, f'{identifier} impression')
    if 'recommendation' in item:
        _normal(item['recommendation'], f'{identifier} recommendation')
    return item


def _sections(item):
    if item['radiograph']:
        return item['sections']
    technique = item['technique']
    technique = {'heading': 'Technique', 'normal': technique['normal'],
                 'options': [*technique.get('options', []), LIMITATION]}
    return [technique, COMPARISON, *item['sections']]


def render(item, normal=False):
    """The fast template, or with ``normal=True`` the complete normal report."""
    body = '\n\n'.join(section['heading'] + ':\n' + '\n'.join(
        [section['normal'], *([] if normal else section.get('options', []))]) for section in _sections(item))
    blocks = [HISTORY, item['title'] + '\n' + body]
    if normal:
        impression = item['impression']
        impression = [impression] if isinstance(impression, str) else impression
        blocks.append('Impression:\n' + '\n'.join(f'{number}. {line}' for number, line in enumerate(impression, 1)))
        blocks.append('Recommendation:\n' + item.get('recommendation', 'None.'))
    else:
        blocks += [BLANK_IMPRESSION, BLANK_RECOMMENDATION]
    return '\n\n'.join(blocks)


@lru_cache(maxsize=1)
def library():
    """Every authored template by investigation id, validated on first use."""
    templates = {}
    for path in sorted(LIBRARY.glob('*.json')):
        data = json.loads(path.read_text(encoding='utf-8'))
        if data.get('schema') != SCHEMA or not isinstance(data.get('templates'), dict):
            raise ValueError(f'{path.name}: not a {SCHEMA} file')
        for identifier, item in data['templates'].items():
            if identifier in templates:
                raise ValueError(f'{identifier}: defined twice')
            templates[identifier] = validate(identifier, item)
    return templates


def quick_report(identifier):
    item = library().get(identifier)
    if item is None:
        return None
    return {'title': item['title'], 'radiograph': item['radiograph'],
            'headings': [section['heading'] for section in _sections(item)],
            'template': render(item), 'normal': render(item, normal=True)}


def with_quick_report(detail):
    """Attach the fast template and the normal report to a module response."""
    if not isinstance(detail, dict) or not isinstance(detail.get('radiology_reference'), dict):
        return detail
    report = quick_report(detail.get('id'))
    if report is None:
        return detail
    result = dict(detail)
    result['radiology_reference'] = dict(detail['radiology_reference'], quick_report=report)
    return result
