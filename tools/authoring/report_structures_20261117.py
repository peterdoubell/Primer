"""Name every structure a study is routinely reported on (2026-11-17).

The standard, for data/radiology/report-templates/*.json (tests/test_report_structures.py enforces it):

Structures
  Every structure the study is routinely reported on has a heading of its own, or shares one with
  the structures it is reported with ("Pancreas", "Long and short radiolunate ligaments").
  No heading hides structures behind a collective word: no "Tendons", "Ligaments", "Other organs",
  "Pelvic organs" or "Remaining chest".

Subheadings
  Headings that belong together share a subheading (the template's ``group``): the intrinsic and the
  extrinsic ligaments of the wrist, the extensor compartments, the disc levels of the spine, the
  regions of a whole-body study.

The rest of the region
  A study done for one question still lists the rest of what it shows, with the same headings as the
  general study of that region (the blocks below: @ABDOMEN, @CHEST, @BRAIN and so on).

The new headings are written in report_structures_content.py, one template per "## id" block:

  ## @NAME                  a block of headings other templates include
  ## id [id ...]            the templates the lines below rewrite
  > Subheading              the headings below share this subheading, up to a bare ">"
  = Old heading             keep a section as it is
  = Old -> New              keep it under a new heading
  = Old -> New | Normal.    ... and with a new normal line (its finding lines stay)
  = Old | | + Finding.      ... and with one more finding line
  ! Old heading             drop a section (its structures are listed by the lines that replace it)
  @NAME except A; B         the block's headings, without A and B
  Heading | Normal. | Finding [a / b] [ ]. | ...     a new section
  A ;; B ;; C | Normal. | Finding.                    the same section under each heading

Every existing section is kept, renamed or dropped by name, so nothing is lost by accident.

Usage: python3 tools/authoring/report_structures_20261117.py   (idempotent)
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from primer import report_templates as rt  # noqa: E402
from report_structures_content import CONTENT  # noqa: E402

LIBRARY = ROOT / 'data' / 'radiology' / 'report-templates'


def parse(text):
    """The content as ({block name: [op]}, {identifier: [op]})."""
    blocks, specs, target = {}, {}, None
    for number, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith('# '):
            continue
        where = f'line {number}: {line[:60]}'
        if line.startswith('## '):
            names = line[3:].split()
            target = []
            for name in names:
                store = blocks if name.startswith('@') else specs
                if name in store:
                    raise SystemExit(f'{where}: {name} is written twice')
                store[name] = target
            continue
        if target is None:
            raise SystemExit(f'{where}: a line before the first "## id"')
        if line.startswith('>'):
            target.append(('group', line[1:].strip() or None))
        elif line.startswith('!'):
            target.append(('drop', line[1:].strip()))
        elif line.startswith('='):
            names, *fields = [part.strip() for part in line[1:].split('|')]
            old, _, new = names.partition('->')
            more = [field[1:].strip() for field in fields[1:]]
            if any(not field.startswith('+') for field in fields[1:]):
                raise SystemExit(f'{where}: a finding line added to a kept section starts with +')
            target.append(('keep', old.strip(), new.strip() or None, (fields[0] if fields else '') or None, more))
        elif line.startswith('@'):
            name, _, without = line.partition(' except ')
            target.append(('block', name.strip(), [h.strip() for h in without.split(';') if h.strip()]))
        else:
            heading, normal, *options = [part.strip() for part in line.split('|')]
            if not normal:
                raise SystemExit(f'{where}: a new section needs its normal line')
            target += [('new', each.strip(), normal, options) for each in heading.split(';;')]
    return blocks, specs


def expand(ops, blocks, seen=()):
    """The ops with every block written out."""
    out = []
    for op in ops:
        if op[0] != 'block':
            out.append(op)
            continue
        _, name, without = op
        if name not in blocks or name in seen:
            raise SystemExit(f'unknown or circular block {name}')
        inner = expand(blocks[name], blocks, (*seen, name))
        missing = set(without) - {o[1] for o in inner if o[0] == 'new'}
        if missing:
            raise SystemExit(f'{name} has no heading {sorted(missing)}')
        inner = [o for o in inner if not (o[0] == 'new' and o[1] in without)]
        # A block ends any subheading it opened, and one included under a subheading stays under it.
        opens = any(o[0] == 'group' for o in inner)
        out += inner + ([('group', None)] if opens else [])
    return out


def build(identifier, current, ops):
    by_heading = {section['heading']: section for section in current}
    used, out, group = set(), [], None
    for op in ops:
        if op[0] == 'group':
            group = op[1]
            continue
        if op[0] == 'drop':
            used.add(op[1])
            continue
        if op[0] == 'keep':
            _, old, new, normal, more = op
            source = by_heading.get(old) or by_heading.get(new)  # found by its new name on a second run
            if source is None:
                raise SystemExit(f'{identifier}: no section {old!r} to keep')
            used.update({old, new} - {None})
            heading, normal, options = new or old, normal or source['normal'], list(source.get('options', []))
            options += [option for option in more if option not in options]
        else:
            _, heading, normal, options = op
            used.add(heading)
        section = {'heading': heading, **({'group': group} if group else {}), 'normal': normal, 'options': options}
        out.append(section)
    left = [heading for heading in by_heading if heading not in used]
    if left:
        raise SystemExit(f'{identifier}: sections neither kept nor dropped: {left}')
    return out


def dump(section):
    head = ', '.join(f'"{key}": {json.dumps(section[key], ensure_ascii=False)}'
                     for key in ('heading', 'group', 'normal') if key in section)
    options = (',\n' + ' ' * 21).join(json.dumps(option, ensure_ascii=False) for option in section['options'])
    return f'        {{{head},\n         "options": [{options}]}}'


def rewrite(text, identifier, sections):
    start = text.index(f'    "{identifier}": {{\n')
    after = re.compile(r'^    "[^"]+": \{$', re.M).search(text, start + 1)
    end = after.start() if after else len(text)
    block = text[start:end]
    opening, closing = '      "sections": [\n', '\n      ],\n'
    first = block.index(opening) + len(opening)
    last = block.index(closing, first)
    return text[:start] + block[:first] + ',\n'.join(dump(section) for section in sections) + block[last:] + text[end:]


def main():
    blocks, specs = parse(CONTENT)
    files = {path: path.read_text(encoding='utf-8') for path in sorted(LIBRARY.glob('*.json'))}
    home = {identifier: path for path, text in files.items() for identifier in json.loads(text)['templates']}
    changed = 0
    for identifier, ops in specs.items():
        if identifier not in home:
            raise SystemExit(f'{identifier}: no such template')
        path = home[identifier]
        current = json.loads(files[path])['templates'][identifier]['sections']
        sections = build(identifier, current, expand(ops, blocks))
        if sections != current:
            files[path] = rewrite(files[path], identifier, sections)
            changed += 1
    for path, text in files.items():
        for identifier, item in json.loads(text)['templates'].items():
            rt.validate(identifier, item)
        if text != path.read_text(encoding='utf-8'):
            path.write_text(text, encoding='utf-8')
    print(f'{changed} of {len(specs)} templates rewritten')


if __name__ == '__main__':
    main()
