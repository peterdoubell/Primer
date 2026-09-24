#!/usr/bin/env python3
"""Render authored pathway diagrams using the Primer's deterministic grammar.

Each illustration exposes its complete authored relationship as an accessible
long description. Arrows signify sequence only in flow diagrams; comparison
panels intentionally have no arrows, quantities, or invented measurements.
"""
import argparse
import json
import os
from pathlib import Path

from PIL import Image
from math_illustrations.core import Plate, font, STAGE_DIRS, INK, PAPER_LIGHT
from natural_science_illustrations.core import _science_font
from imaging_foundation_art import draw as draw_imaging_foundation

ROOT = Path(__file__).resolve().parents[1]


def fit(plate, text, box, size=30, bold=False, color=INK):
    """Wrap and shrink within a real measured box; never crop authored labels."""
    left, top, right, bottom = box
    for candidate in range(size, 17, -1):
        face = _science_font(text, candidate, bold=bold)
        lines, line = [], ''
        for word in text.split():
            trial = (line + ' ' + word).strip()
            if plate.draw.textlength(trial, font=face) > right - left and line:
                lines.append(line)
                line = word
            else:
                line = trial
        if line:
            lines.append(line)
        if len(lines) * (candidate + 8) <= bottom - top and all(
                plate.draw.textlength(line, font=face) <= right - left for line in lines):
            y = top + (bottom - top - len(lines) * (candidate + 8)) / 2
            for line in lines:
                plate.draw.text((left, y), line, font=face, fill=color)
                y += candidate + 8
            return
    raise ValueError('Diagram text does not fit: ' + text)


def draw(node, domain):
    spec = node['visual_spec']
    assert set(spec) == {'title', 'mode', 'items', 'takeaway'}, node['id']
    assert spec['mode'] in ('flow', 'compare'), node['id']
    assert 2 <= len(spec['items']) <= 4, node['id']
    plate = Plate(node['id'], '', node['stage'])
    fit(plate, node['title'], (96, 105, 1504, 162), 44, True)
    fit(plate, spec['title'], (110, 185, 1490, 250), 36, True)
    drawn = draw_imaging_foundation(plate, node, spec)
    gap, count = 40, (0 if drawn else len(spec['items']))
    width = (1380 - (count - 1) * gap) / max(1, count)
    for index, item in enumerate([] if drawn else spec['items']):
        assert set(item) == {'heading', 'label', 'detail'}, node['id']
        x = 110 + index * (width + gap)
        plate.card((x, 330, x + width, 745), fill=PAPER_LIGHT)
        if spec['mode'] == 'flow':
            plate.draw.ellipse((x + width/2 - 24, 275, x + width/2 + 24, 323), fill=plate.accent)
            plate.draw.text((x + width/2, 299), str(index + 1), font=font(25, bold=True), fill=PAPER_LIGHT, anchor='mm')
            if index < count - 1:
                plate.arrow((x + width/2 + 35, 299), (x + width + gap + width/2 - 35, 299), width=4)
        else:
            plate.draw.line((x + 12, 300, x + width - 12, 300), fill=plate.accent, width=7)
        fit(plate, item['heading'], (x + 24, 352, x + width - 24, 410), 28, True, plate.accent)
        fit(plate, item['label'], (x + 24, 432, x + width - 24, 525), 34, True)
        plate.draw.line((x + 24, 545, x + width - 24, 545), fill=plate.accent, width=2)
        fit(plate, item['detail'], (x + 24, 560, x + width - 24, 718), 27)
    fit(plate, spec['takeaway'], (115, 805, 1485, 925), 30)
    slug = node['id'].replace('.', '-')
    folder = ROOT / 'web/illustrations' / STAGE_DIRS[node['stage']] / domain
    folder.mkdir(parents=True, exist_ok=True)
    urls = {}
    for size in (800, 1600):
        path = folder / (slug + '-' + str(size) + '.webp')
        temporary = path.with_suffix('.webp.tmp')
        plate.image.resize((size, size * 5 // 8), Image.Resampling.LANCZOS).save(temporary, 'WEBP', quality=88, method=6)
        os.replace(temporary, path)
        urls[size] = '/app/' + path.relative_to(ROOT / 'web').as_posix()
    return {
        'id': slug + '-relationship-plate', 'kind': 'illustration',
        'src': urls[800], 'srcset': urls[800] + ' 800w, ' + urls[1600] + ' 1600w',
        'width': 1600, 'height': 1000,
        'alt': ('A sequence diagram showing ' if spec['mode'] == 'flow' else 'A side-by-side comparison showing ') +
               '; '.join(item['heading'] + ': ' + item['label'] for item in spec['items']) + '.',
        'caption': spec['takeaway'] + (' ' + spec['items'][-1]['detail']
                                     if len(spec['takeaway'].split()) < 8 else ''),
        'long_description': spec,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--domain', help='Regenerate only one field')
    args = parser.parse_args()
    count = 0
    for source in sorted((ROOT / 'data/curriculum').glob('*.json')):
        data = json.loads(source.read_text())
        if args.domain and data['id'] != args.domain:
            continue
        changed = False
        for node in data['nodes']:
            if not node.get('lesson'):
                continue
            media = node.setdefault('lesson_media', [])
            illustration = draw(node, data['id'])
            originals = [item for item in media if item.get('kind') == 'illustration']
            if originals and any(item['id'] != illustration['id'] for item in originals):
                raise ValueError('Refusing to replace another authored plate: ' + node['id'])
            node['lesson_media'] = [illustration] + [item for item in media if item.get('kind') != 'illustration']
            count += 1
            changed = True
        if changed:
            temporary = source.with_suffix('.json.tmp')
            temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
            os.replace(temporary, source)
    print('Rendered and bound {} diagrams at 800 and 1600 pixels'.format(count))


if __name__ == '__main__':
    main()
