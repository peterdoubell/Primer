"""Add the soft tissue neck ultrasound, the general survey of the neck (Peter, 2026-11-19).

Writes:
  data/radiology/anatomic-additions-20261119.json          its selectable report rows
  data/radiology/report-templates/additions-20261119.json  its fast template
  data/radiology/prism-titles.json and tools/authoring/practice_examinations.json
      the practice's general neck ultrasound titles ("ultrasound neck", "ultrasound soft tissue neck",
      "sonar neck", "ultrasound salivary glands") move to it from the cervical lymph node study, which
      keeps the lymph node titles.

It hangs off the cervical lymph node investigation (module rad.5.neck-nodes) for its teaching, and its
headings follow the neck's elsewhere: the salivary glands and thyroid as in MRI neck, the nodes by side
as in the lymph node ultrasound.

Then rebuild the selectable reports: python3 tools/build_descriptor_reporting.py --catalog <catalog.json> --archive-current
Run from the repository root: python3 tools/authoring/examination_soft_tissue_neck_20261119.py   (idempotent)
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / 'data' / 'radiology'
IDENTIFIER = 'us.soft-tissue-neck'
TITLE = 'Ultrasound soft tissue neck'
GENERAL = ['ultrasound soft tissue neck', 'ultrasound neck', 'neck ultrasound', 'sonar neck', 'ultrasound salivary glands',
           'US soft tissue neck', 'soft tissue neck ultrasound']
NODES = ['ultrasound neck lymph nodes', 'ultrasound cervical lymph nodes']

TECHNIQUE = 'Ultrasound of both sides of the neck, including the salivary glands, thyroid and cervical lymph nodes, with colour Doppler.'

# The fast template: heading, subheading, normal, finding lines.
SECTIONS = [
    ('Area of concern', None, 'No abnormality in the area of concern.',
     ['[Cyst / Solid lesion / Lymph node / Collection / Lipoma] [ ] mm in the [ ].',
      'Features of a [thyroglossal duct cyst / branchial cleft cyst / abscess / haematoma] [ ].']),
    ('Parotid glands', 'Salivary and thyroid glands', 'Normal.',
     ['[Mass / Sialadenitis / Calculus / Duct dilatation] of the [right / left] parotid gland [ ].']),
    ('Submandibular glands', 'Salivary and thyroid glands', 'Normal.',
     ['[Mass / Sialadenitis / Calculus / Duct dilatation] of the [right / left] submandibular gland [ ].']),
    ('Thyroid gland', 'Salivary and thyroid glands', 'Normal thyroid size and echotexture. No thyroid nodule.',
     ['Thyroid nodule [ ] mm in the [right lobe / left lobe / isthmus], ACR TI-RADS [TR1 / TR2 / TR3 / TR4 / TR5].',
      '[Goitre / Thyroiditis / Heterogeneous echotexture] [ ].']),
    ('Right neck', 'Lymph nodes', 'No abnormal lymph node in levels I to VI on the right.',
     ['Level [I / II / III / IV / V / VI] node, [ ] x [ ] mm, [loss of fatty hilum / round shape / necrosis / calcification / peripheral vascularity].']),
    ('Left neck', 'Lymph nodes', 'No abnormal lymph node in levels I to VI on the left.',
     ['Level [I / II / III / IV / V / VI] node, [ ] x [ ] mm, [loss of fatty hilum / round shape / necrosis / calcification / peripheral vascularity].']),
    ('Vessels', None, 'Patent carotid arteries and internal jugular veins.',
     ['[Thrombus / Stenosis / Occlusion] of the [right / left] [carotid artery / internal jugular vein] [ ].']),
    ('Muscles and soft tissues', None, 'Normal.',
     ['[Collection / Oedema / Haematoma / Soft tissue mass / Fibromatosis colli] in the [ ].']),
]
IMPRESSION = 'Normal ultrasound soft tissue neck.'


def finding(identifier, label, text, needs=None):
    item = {'id': identifier, 'label': label, 'text': text}
    if needs:
        item['requires_any'] = needs
    return item


def row(identifier, label, group, normal, findings, exclude=False):
    out = {'id': identifier, 'label': label, 'group': group, 'normal': normal, 'source_ids': ['acr-parameters'],
           'findings': findings}
    if exclude:
        out['exclude_from_bulk_normal'] = True
    return out


def node_row(side):
    return row(f'{side}-neck-nodes', f'{side.capitalize()} neck', 'Lymph nodes',
               f'No morphologically abnormal lymph node is seen in levels I to VI of the {side} neck.', [
                   finding('node', f'Abnormal {side} neck node',
                           f'An abnormal {side} level [I / II / III / IV / V / VI] lymph node is present.'),
                   finding('size', 'Short axis', f'The {side} neck node measures __ mm in short axis.', ['node']),
                   finding('features', 'Node features',
                           'The node shows [loss of the fatty hilum / a round shape / cystic change / necrosis / calcification / peripheral vascularity].',
                           ['node'])])


# The selectable report: one row per structure, every finding enumerated.
ROWS = [
    row('technique', 'Examination performed', 'Technique', None, [
        finding('assessment', 'Examination performed',
                'The examination was performed [to the standard protocol / with a modified protocol / as a limited examination].')],
        exclude=True),
    row('area-of-concern', 'Area of concern', 'Area of concern', 'No abnormality is identified in the area of concern.', [
        finding('lesion', 'Lesion', 'A [cystic / solid / mixed cystic and solid / fatty] lesion is present in the area of concern.'),
        finding('size', 'Size', 'The lesion measures __ × __ × __ mm.', ['lesion']),
        finding('vascularity', 'Vascularity', 'The lesion shows [no / peripheral / internal] Doppler vascularity.', ['lesion']),
        finding('nature', 'Appearance',
                'The appearances are of [a lymph node / a thyroglossal duct cyst / a branchial cleft cyst / a lipoma / an abscess / a haematoma].',
                ['lesion'])]),
    row('parotid-glands', 'Parotid glands', 'Salivary and thyroid glands',
        'The parotid glands are normal in size and echotexture, with no focal lesion.', [
            finding('lesion', 'Parotid lesion', 'A [solid / cystic / mixed] lesion is present in the [right / left] parotid gland.'),
            finding('size', 'Lesion size', 'The parotid lesion measures __ mm.', ['lesion']),
            finding('diffuse', 'Diffuse change', 'The [right / left / both] parotid glands are [enlarged and hypoechoic / heterogeneous / atrophic].'),
            finding('calculus', 'Calculus', 'There is a [right / left] parotid duct calculus [with / without] duct dilatation.')]),
    row('submandibular-glands', 'Submandibular glands', 'Salivary and thyroid glands',
        'The submandibular glands are normal in size and echotexture, with no focal lesion.', [
            finding('lesion', 'Submandibular lesion', 'A [solid / cystic / mixed] lesion is present in the [right / left] submandibular gland.'),
            finding('size', 'Lesion size', 'The submandibular lesion measures __ mm.', ['lesion']),
            finding('diffuse', 'Diffuse change', 'The [right / left / both] submandibular glands are [enlarged and hypoechoic / heterogeneous / atrophic].'),
            finding('calculus', 'Calculus', 'There is a [right / left] submandibular duct calculus [with / without] duct dilatation.')]),
    row('thyroid-gland', 'Thyroid gland', 'Salivary and thyroid glands',
        'The thyroid gland is normal in size and echotexture, with no nodule.', [
            finding('nodule', 'Thyroid nodule', 'A thyroid nodule is present in the [right lobe / left lobe / isthmus].'),
            finding('size', 'Nodule size', 'The thyroid nodule measures __ mm.', ['nodule']),
            finding('tirads', 'ACR TI-RADS', 'The nodule is ACR TI-RADS [TR1 / TR2 / TR3 / TR4 / TR5].', ['nodule']),
            finding('diffuse', 'Diffuse change', 'The thyroid gland is [enlarged / heterogeneous / diffusely hypoechoic / hypervascular].')]),
    node_row('right'),
    node_row('left'),
    row('vessels', 'Vessels', 'Vessels and soft tissues', 'The carotid arteries and internal jugular veins are patent.', [
        finding('thrombus', 'Venous thrombus', 'There is thrombus in the [right / left] internal jugular vein.'),
        finding('carotid', 'Carotid disease', 'There is [plaque / stenosis / occlusion] of the [right / left] common carotid artery.')]),
    row('muscles-and-soft-tissues', 'Muscles and soft tissues', 'Vessels and soft tissues',
        'The neck muscles and subcutaneous soft tissues are normal.', [
            finding('abnormal', 'Soft tissue abnormality',
                    'There is [a collection / oedema / a haematoma / a soft tissue mass / fibromatosis colli] in the [right / left / midline] neck.')]),
]


def dumps(value):
    return json.dumps(value, ensure_ascii=False)


def template_text():
    """The fast template in the library's hand-formatted layout (as report_structures_20261117.py writes it)."""
    sections = []
    for heading, group, normal, options in SECTIONS:
        head = ', '.join(f'"{key}": {dumps(value)}' for key, value in
                         (('heading', heading), ('group', group), ('normal', normal)) if value is not None)
        lines = (',\n' + ' ' * 21).join(dumps(option) for option in options)
        sections.append(f'        {{{head},\n         "options": [{lines}]}}')
    return ('{\n  "schema": "primer.fast-report-templates/1",\n  "revision": "2026-11-19",\n  "templates": {\n'
            f'    "{IDENTIFIER}": {{\n      "title": {dumps(TITLE)},\n      "radiograph": false,\n'
            f'      "technique": {{"normal": {dumps(TECHNIQUE)},\n                    "options": []}},\n'
            '      "sections": [\n' + ',\n'.join(sections) + '\n      ],\n'
            f'      "impression": {dumps(IMPRESSION)}\n    }}\n  }}\n}}\n')


def rewrite_json(path, change):
    text = path.read_text(encoding='utf-8')
    data = json.loads(text)
    if json.dumps(data, ensure_ascii=False, indent=1) + '\n' != text:
        raise SystemExit(f'{path.name} is not in the expected layout')
    change(data)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')


def main():
    additions = {
        'version': '2026-11-19',
        'sources': [{'id': 'acr-parameters', 'title': 'ACR practice parameters and technical standards',
                     'url': 'https://www.acr.org/clinical-resources/clinical-tools-and-reference/practice-parameters-and-technical-standards'}],
        'investigations': {IDENTIFIER: {'guide_id': 'rad.5.neck-nodes', 'title': TITLE, 'modality': 'Ultrasound',
                                        'base_investigation_id': 'ra.cervical-lymph-nodes', 'sections': ROWS}},
        'coverage': [{'investigation_id': IDENTIFIER, 'expected_anatomy_ids': [r['id'] for r in ROWS]}],
    }
    (DATA / 'anatomic-additions-20261119.json').write_text(json.dumps(additions, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    (DATA / 'report-templates' / 'additions-20261119.json').write_text(template_text(), encoding='utf-8')

    def titles(data):
        data['practice_studies']['Ultrasound neck'] = IDENTIFIER
        data['titles']['ra.cervical-lymph-nodes'] = NODES
        data['titles'][IDENTIFIER] = GENERAL
    rewrite_json(DATA / 'prism-titles.json', titles)

    def practice(data):
        data['Ultrasound neck'] = IDENTIFIER
    rewrite_json(ROOT / 'tools' / 'authoring' / 'practice_examinations.json', practice)
    print(f'{IDENTIFIER}: {len(SECTIONS)} headings, {len(ROWS)} selectable rows, {len(GENERAL)} Prism titles')


if __name__ == '__main__':
    main()
