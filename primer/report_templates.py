"""Fast report templates and normal reports, laid out for pasting into a RIS.

Each examination has a study title and short sentence-case headings, one for
every structure the study is routinely reported on. Headings that belong
together (the intrinsic ligaments, the extensor compartments, the disc levels)
share a ``group``, which is printed once as a subheading above them. Under a
heading the first line is the normal finding; the lines after it are the
common abnormal findings, written with picks ``[a / b]`` and blanks ``[ ]``
only where the reader must explain. The same data renders a complete normal
report. Every MRI opens with its Protocol and every CT with its Technique,
then a Findings subheading; radiographs, ultrasound and fluoroscopy have neither.
"""
from functools import lru_cache

from .reporting_bridge import descriptor_forms
import json
import re
from pathlib import Path

LIBRARY = Path(__file__).resolve().parents[1] / 'data' / 'radiology' / 'report-templates'
SCHEMA = 'primer.fast-report-templates/1'
RESERVED = {'clinical history', 'technique', 'comparison', 'impression', 'recommendation'}
LIMITATION = 'Limited by [ ].'
# Review worksheets and the contrast record are not acquired studies.
NOT_ACQUIRED = {'template:ct-image-report', 'template:mri-sequences-report', 'ra.ct-contrast-protocols'}
BLANK_IMPRESSION = 'Impression:\n1. []\n2. []\n3. []'
BLANK_RECOMMENDATION = 'Recommendation:\n1. []\n2. []\n3. []'
BULLET = '• '
MOST_HEADINGS = 30  # a joint MRI names every ligament, tendon and compartment it reports
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


def _heading(heading, where):
    if not isinstance(heading, str) or not HEADING.fullmatch(heading) or len(heading) > 60:
        raise ValueError(f'{where}: heading {heading!r} must be short sentence case without punctuation at the end')
    if heading.upper() == heading and ' ' in heading:
        raise ValueError(f'{where}: heading {heading!r} must be sentence case')
    return heading


def _section(section, where):
    if set(section) - {'heading', 'group', 'normal', 'options'} or 'heading' not in section or 'normal' not in section:
        raise ValueError(f'{where}: a section has heading, normal and options, and may have a group')
    heading = _heading(section['heading'], where)
    if 'group' in section:
        _heading(section['group'], where)
    _normal(section['normal'], f'{where} {heading}')
    options = section.get('options', [])
    if not isinstance(options, list) or len(options) > 5:
        raise ValueError(f'{where} {heading}: at most five finding lines')
    for option in options:
        _option(option, f'{where} {heading}')
    return section


def validate(identifier, item):
    """Return the template unchanged, or raise ValueError naming the defect."""
    allowed = {'title', 'radiograph', 'technique', 'sections', 'impression', 'recommendation', 'dictation'}
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
    if not isinstance(sections, list) or not 2 <= len(sections) <= MOST_HEADINGS:
        raise ValueError(f'{identifier}: two to {MOST_HEADINGS} finding headings')
    seen = set()
    for section in sections:
        _section(section, identifier)
        key = section['heading'].lower()
        if key in RESERVED or key in seen:
            raise ValueError(f'{identifier}: heading {section["heading"]!r} is reserved or repeated')
        seen.add(key)
    for group, members in _blocks(sections):
        if group is None:
            continue
        key = group.lower()
        if key in RESERVED or key == 'findings' or key in seen:
            raise ValueError(f'{identifier}: subheading {group!r} is reserved, repeated or split')
        if len(members) < 2:
            raise ValueError(f'{identifier}: subheading {group!r} needs two or more headings under it')
        seen.add(key)
    impression = item.get('impression')
    impression = [impression] if isinstance(impression, str) else impression
    if not isinstance(impression, list) or not 1 <= len(impression) <= 3:
        raise ValueError(f'{identifier}: one to three normal impression lines')
    for line in impression:
        _normal(line, f'{identifier} impression')
    if 'recommendation' in item:
        _normal(item['recommendation'], f'{identifier} recommendation')
    if 'dictation' in item:
        draft = item['dictation']
        if (not isinstance(draft, dict) or set(draft) != {'title', 'technique', 'findings'}
                or any(not isinstance(draft[key], str) or not draft[key].strip()
                       or '\n' in draft[key] for key in ('title', 'technique'))
                or not isinstance(draft['findings'], list) or not draft['findings']
                or any(not isinstance(block, str) or '[]' not in block
                       or re.sub(r'\[\]', '', block).find('[') >= 0
                       or re.sub(r'\[\]', '', block).find(']') >= 0
                       for block in draft['findings'])):
            raise ValueError(f'{identifier}: invalid dictation layout')
    return item


@lru_cache(maxsize=1)
def examination_profiles():
    return {exam['id']: exam for form in descriptor_forms()['forms'].values()
            for exam in form['investigations']}


def acquisition_heading(identifier, item):
    """'Protocol' for an MRI study, 'Technique' for a CT study, otherwise None."""
    if identifier in NOT_ACQUIRED or 'technique' not in item:
        return None
    title = item['title']
    if re.search(r'\bCT\b|\bHRCT\b', title):
        return 'Technique'
    return 'Protocol' if re.search(r'\bMRI?\b|\bMRCP\b', title) else None


def _blocks(sections):
    """The sections in order, those that share a subheading gathered under it: [(group or None, [section])]."""
    blocks = []
    for section in sections:
        group = section.get('group')
        if group and blocks and blocks[-1][0] == group:
            blocks[-1][1].append(section)
        else:
            blocks.append((group, [section]))
    return blocks


def _sections(item, heading):
    sections = list(item['sections'])
    if not heading:
        return sections
    technique = item['technique']
    return [{'heading': heading, 'normal': technique['normal'],
             'options': [*technique.get('options', []), LIMITATION]}, *sections]


def render(item, normal=False, heading=None):
    """Render the editable template, or its normal findings variant.

    Layout: main headings (clinical history, comparison, study name, protocol or technique,
    findings, impression, recommendation), then anatomical subheadings whose findings are
    bullet lines. Headings that share a group follow its subheading without a blank line.
    The study name runs into its first heading and Findings into its first subheading;
    impression and recommendation are numbered lists.
    """
    blocks = []
    for group, members in _blocks(_sections(item, heading)):
        parts = []
        for section in members:
            acquisition = bool(heading) and not blocks and not parts
            # One sentence per bullet for the normal finding, as dictated.
            first = [section['normal']] if acquisition else re.split(r'(?<=\.)\s+(?=[A-Z])', section['normal'])
            lines = [*first, *([] if normal else section.get('options', []))]
            parts.append(section['heading'] + ':\n' + '\n'.join(line if acquisition else BULLET + line for line in lines))
        blocks.append((group + ':\n' if group else '') + '\n'.join(parts))
    if heading:
        blocks[1] = 'Findings:\n' + blocks[1]
    blocks[0] = item['title'] + '\n' + blocks[0]
    if normal:
        impression = item['impression']
        impression = [impression] if isinstance(impression, str) else impression
        closing = ['Impression:\n' + '\n'.join(f'{number}. {line}' for number, line in enumerate(impression, 1)),
                   'Recommendation:\n1. ' + item.get('recommendation', 'None.')]
    else:
        closing = [BLANK_IMPRESSION, BLANK_RECOMMENDATION]
    return '\n\n'.join(['Clinical history:\n[]', 'Comparison:\n[]', *blocks, *closing]).replace('[ ].', '[]').replace('[ ]', '[]')


def render_dictation(item, heading):
    """Render a fill-in report with the study's anatomical search pattern."""
    draft = item.get('dictation')
    title = draft['title'] if draft else item['title']
    study = title
    if heading:
        label = 'Technique' if draft else heading
        technique = draft['technique'] if draft else item['technique']['normal']
        study += f'\n{label}:\n{technique}'
    findings = draft['findings'] if draft else [
        (group + ':\n' if group else '') + '\n'.join(section['heading'] + ': []' for section in members)
        for group, members in _blocks(item['sections'])]
    if heading:
        findings = ['Findings:\n' + findings[0], *findings[1:]]
    text = '\n\n'.join(['Clinical history:\n[]', 'Comparison:\n[]', study, *findings,
                       'Impression:\n[]', 'Recommendation:\n[]'])
    return {'title': title, 'text': text}


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
    heading = acquisition_heading(identifier, item)
    headings = [name for group, members in _blocks(_sections(item, heading))
                for name in [*([group] if group else []), *(section['heading'] for section in members)]]
    if heading:
        headings.insert(1, 'Findings')
    return {'title': item['title'], 'radiograph': item['radiograph'], 'headings': headings,
            'dictation': render_dictation(item, heading),
            'template': render(item, heading=heading), 'normal': render(item, normal=True, heading=heading)}


def align_builder_protocols(catalogue):
    """Give the click builder the same default acquisition wording as the report template.

    The builder's selectable acquisition choices are unchanged; only the text used when
    none is chosen is replaced, and only for studies whose template has a Protocol or Technique.
    """
    templates = library()
    for form in catalogue.get('forms', {}).values():
        for investigation in form.get('investigations', []):
            item = templates.get(investigation.get('id'))
            acquisition = investigation.get('report_protocol')
            if acquisition and item and acquisition_heading(investigation['id'], item):
                acquisition['standard_text'] = item['technique']['normal']
    return catalogue


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
