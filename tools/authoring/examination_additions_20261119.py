"""Two performed examinations added on 2026-11-19 at Peter's request.

  us.soft-tissue-neck       Ultrasound soft tissue neck: the general survey of the neck. Its headings follow
                            the neck's elsewhere: the salivary glands and thyroid as in MRI neck, the nodes by
                            side as in the lymph node ultrasound. Teaching: the cervical lymph node investigation.
  ct.chest-abdomen-pelvis   CT chest, abdomen and pelvis with contrast: the practice's oncology scan, organ by
                            organ. It is the skull base to pubic symphysis staging template without the neck,
                            heading for heading, with the practice's own technique. Teaching: RECIST.

Writes:
  data/radiology/anatomic-additions-20261119.json          their selectable report rows
  data/radiology/report-templates/additions-20261119.json  their fast templates
  data/radiology/prism-titles.json and tools/authoring/practice_examinations.json
      the practice's general titles move to them: "ultrasound neck", "ultrasound soft tissue neck" and the like
      from the cervical lymph node study, which keeps the lymph node titles; "CT chest abdomen and pelvis",
      "CT CAP" and the like from the RECIST 1.1 baseline study, which takes titles that name it.

Then rebuild the selectable reports from the shipped catalogue:
  python3 tools/build_descriptor_reporting.py --catalog <catalog.json> --archive-current
Run from the repository root: python3 tools/authoring/examination_additions_20261119.py   (idempotent)
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.build_descriptor_reporting import compile_statement  # noqa: E402

DATA = ROOT / 'data' / 'radiology'
NECK = 'us.soft-tissue-neck'
CAP = 'ct.chest-abdomen-pelvis'
STAGING = 'ct.oncology-staging'

# Prism titles after the move, and the practice study each new examination answers.
TITLES = {
    NECK: ['ultrasound soft tissue neck', 'ultrasound neck', 'neck ultrasound', 'sonar neck', 'ultrasound salivary glands',
           'US soft tissue neck', 'soft tissue neck ultrasound'],
    'ra.cervical-lymph-nodes': ['ultrasound neck lymph nodes', 'ultrasound cervical lymph nodes'],
    CAP: ['CT chest abdomen and pelvis', 'CT chest abdomen pelvis', 'CT chest abdo pelvis', 'CT CAP',
          'CT thorax abdomen and pelvis', 'CT of the chest abdomen and pelvis'],
    'ra.recist': ['CT chest abdomen and pelvis RECIST baseline', 'CT CAP baseline'],
}
PRACTICE = {'Ultrasound neck': NECK, 'CT chest, abdomen and pelvis': CAP}

NECK_TECHNIQUE = 'Ultrasound of both sides of the neck, including the salivary glands, thyroid and cervical lymph nodes, with colour Doppler.'
# The practice's own wording (Peter's photos of its oncology reports, 2026-11-19), kept word for word.
CAP_TECHNIQUE = 'Arterial phase chest and upper abdomen. Portal venous abdomen and pelvis.'

# A fast template: heading, subheading, normal, finding lines.
NECK_SECTIONS = [
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


def staging_without_neck():
    """The staging template's headings below the neck: the same scan, read the same way."""
    library = json.loads((DATA / 'report-templates' / 'additions-20261112.json').read_text(encoding='utf-8'))['templates']
    return [(section['heading'], section.get('group'), section['normal'], section.get('options', []))
            for section in library[STAGING]['sections'] if section.get('group') != 'Neck']


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


def technique_row():
    return row('technique', 'Examination performed', 'Technique', None, [
        finding('assessment', 'Examination performed',
                'The examination was performed [to the standard protocol / with a modified protocol / as a limited examination].')],
        exclude=True)


def node_row(side):
    return row(f'{side}-neck-nodes', f'{side.capitalize()} neck', 'Lymph nodes',
               f'No morphologically abnormal lymph node is seen in levels I to VI of the {side} neck.', [
                   finding('node', f'Abnormal {side} neck node',
                           f'An abnormal {side} level [I / II / III / IV / V / VI] lymph node is present.'),
                   finding('size', 'Short axis', f'The {side} neck node measures __ mm in short axis.', ['node']),
                   finding('features', 'Node features',
                           'The node shows [loss of the fatty hilum / a round shape / cystic change / necrosis / calcification / peripheral vascularity].',
                           ['node'])])


# The selectable reports: one row per structure, every finding enumerated.
NECK_ROWS = [
    technique_row(),
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

CAP_ROWS = [
    technique_row(),
    row('lungs-and-airways', 'Lungs and airways', 'Chest',
        'The lungs are clear, with no pulmonary nodule, mass or consolidation, and the central airways are patent.', [
            finding('nodule', 'Pulmonary nodule',
                    'A pulmonary nodule is present in the [right upper lobe / right middle lobe / right lower lobe / left upper lobe / lingula / left lower lobe].'),
            finding('size', 'Nodule size', 'The pulmonary nodule measures __ mm.', ['nodule']),
            finding('parenchyma', 'Lung abnormality',
                    'There is [a mass / consolidation / lymphangitic thickening / atelectasis] in the [right lung / left lung / both lungs].'),
            finding('airway', 'Airway abnormality', 'There is [bronchial wall thickening / an endobronchial lesion / bronchial obstruction].')]),
    row('pleura-and-pericardium', 'Pleura and pericardium', 'Chest', 'No pleural or pericardial effusion.', [
        finding('effusion', 'Pleural effusion', 'There is a [small / moderate / large] [right / left / bilateral] pleural effusion.'),
        finding('pleura', 'Pleural disease', 'There is [right / left / bilateral] pleural [thickening / nodularity].'),
        finding('pericardium', 'Pericardial effusion', 'There is a [small / moderate / large] pericardial effusion.')]),
    row('thoracic-lymph-nodes', 'Thoracic lymph nodes', 'Chest', 'No mediastinal, hilar or axillary lymphadenopathy.', [
        finding('node', 'Enlarged node', 'An enlarged [mediastinal / hilar / axillary / supraclavicular] lymph node is present.'),
        finding('size', 'Short axis', 'The thoracic lymph node measures __ mm in short axis.', ['node'])]),
    row('heart-and-great-vessels', 'Heart and great vessels', 'Chest', 'The heart and great vessels are normal.', [
        finding('abnormal', 'Cardiovascular abnormality',
                'There is [a pulmonary embolus / tumour thrombus / cardiomegaly / an aortic aneurysm / coronary artery calcification].')]),
    row('liver', 'Liver', 'Abdomen and pelvis', 'No focal liver lesion.', [
        finding('lesion', 'Liver lesion', 'A focal liver lesion is present in the [right lobe / left lobe / caudate lobe].'),
        finding('size', 'Lesion size', 'The liver lesion measures __ mm.', ['lesion']),
        finding('nature', 'Lesion appearance', 'The liver lesion is [hypodense / hyperenhancing / cystic / indeterminate].', ['lesion']),
        finding('diffuse', 'Diffuse liver disease', 'The liver shows [steatosis / cirrhotic morphology / hepatomegaly].')]),
    row('gallbladder-pancreas-and-spleen', 'Gallbladder, pancreas and spleen', 'Abdomen and pelvis',
        'The gallbladder, pancreas and spleen are normal.', [
            finding('abnormal', 'Abnormality',
                    'There is [a pancreatic lesion / pancreatic duct dilatation / a splenic lesion / splenomegaly / gallstones / biliary dilatation].')]),
    row('adrenal-glands', 'Adrenal glands', 'Abdomen and pelvis', 'The adrenal glands are normal.', [
        finding('nodule', 'Adrenal nodule', 'There is a [right / left] adrenal nodule.'),
        finding('size', 'Nodule size', 'The adrenal nodule measures __ mm.', ['nodule'])]),
    row('kidneys-and-bladder', 'Kidneys and bladder', 'Abdomen and pelvis',
        'The kidneys and bladder are normal, with no hydronephrosis.', [
            finding('renal', 'Renal lesion', 'There is a [renal cyst / renal mass / renal calculus] in the [right / left] kidney.'),
            finding('hydronephrosis', 'Hydronephrosis', 'There is [right / left / bilateral] hydronephrosis.'),
            finding('bladder', 'Bladder abnormality', 'There is [bladder wall thickening / a bladder mass].')]),
    row('bowel-and-peritoneum', 'Bowel and peritoneum', 'Abdomen and pelvis',
        'The bowel is normal in calibre, with no wall thickening, ascites or peritoneal nodularity.', [
            finding('bowel', 'Bowel abnormality',
                    'There is [bowel wall thickening / a bowel mass / bowel obstruction] involving the [stomach / small bowel / colon / rectum].'),
            finding('peritoneum', 'Peritoneal disease', 'There is [ascites / peritoneal nodularity / omental disease / a collection].')]),
    row('reproductive-organs', 'Reproductive organs', 'Abdomen and pelvis', 'The reproductive organs are unremarkable.', [
        finding('abnormal', 'Abnormality', 'There is [an adnexal mass / a uterine mass / prostatic enlargement / a prostatic lesion].')]),
    row('abdominal-and-pelvic-lymph-nodes', 'Abdominal and pelvic lymph nodes', 'Abdomen and pelvis',
        'No abdominal or pelvic lymphadenopathy.', [
            finding('node', 'Enlarged node', 'An enlarged [retroperitoneal / mesenteric / pelvic / inguinal] lymph node is present.'),
            finding('size', 'Short axis', 'The abdominal or pelvic lymph node measures __ mm in short axis.', ['node'])]),
    row('bones', 'Bones', 'Bones', 'No suspicious bone lesion.', [
        finding('lesion', 'Bone lesion',
                'There is a [lytic / sclerotic / mixed] bone lesion in the [spine / ribs / pelvis / sternum / proximal femur / proximal humerus].'),
        finding('fracture', 'Pathological fracture', 'The bone lesion [has / does not have] an associated pathological fracture.',
                ['lesion'])]),
    row('target-lesions', 'Target lesions', 'Target lesions', 'No measurable disease.', [
        finding('measurable', 'Measurable disease', 'Measurable disease is present.'),
        finding('sum', 'Sum of diameters', 'The sum of target lesion diameters is __ mm.', ['measurable']),
        finding('response', 'Response',
                'The response is [complete response / partial response / stable disease / progressive disease] by RECIST 1.1.',
                ['measurable'])]),
]


def examinations():
    return [
        {'id': NECK, 'title': 'Ultrasound soft tissue neck', 'modality': 'Ultrasound', 'guide': 'rad.5.neck-nodes',
         'base': 'ra.cervical-lymph-nodes', 'technique': NECK_TECHNIQUE, 'sections': NECK_SECTIONS,
         'impression': 'Normal ultrasound soft tissue neck.', 'rows': NECK_ROWS},
        {'id': CAP, 'title': 'CT chest, abdomen and pelvis with contrast', 'modality': 'CT', 'guide': 'rad.4.oncology-response',
         'base': 'ra.recist', 'technique': CAP_TECHNIQUE, 'sections': staging_without_neck(),
         'impression': 'Normal CT chest, abdomen and pelvis.', 'rows': CAP_ROWS},
    ]


def dumps(value):
    return json.dumps(value, ensure_ascii=False)


def template_text(exams):
    """The fast templates in the library's hand-formatted layout (as report_structures_20261117.py writes it)."""
    blocks = []
    for exam in exams:
        sections = []
        for heading, group, normal, options in exam['sections']:
            head = ', '.join(f'"{key}": {dumps(value)}' for key, value in
                             (('heading', heading), ('group', group), ('normal', normal)) if value is not None)
            lines = (',\n' + ' ' * 21).join(dumps(option) for option in options)
            sections.append(f'        {{{head},\n         "options": [{lines}]}}')
        blocks.append(f'    "{exam["id"]}": {{\n      "title": {dumps(exam["title"])},\n      "radiograph": false,\n'
                      f'      "technique": {{"normal": {dumps(exam["technique"])},\n                    "options": []}},\n'
                      '      "sections": [\n' + ',\n'.join(sections) + '\n      ],\n'
                      f'      "impression": {dumps(exam["impression"])}\n    }}')
    return ('{\n  "schema": "primer.fast-report-templates/1",\n  "revision": "2026-11-19",\n  "templates": {\n'
            + ',\n'.join(blocks) + '\n  }\n}\n')


def check(exams):
    """Every authored statement compiles as the catalogue build will compile it: no free-text blank."""
    for exam in exams:
        identifiers = [r['id'] for r in exam['rows']]
        assert len(set(identifiers)) == len(identifiers), exam['id']
        for position, authored in enumerate(exam['rows']):
            source = {'investigation_id': exam['id'], 'step_index': position}
            for item in authored['findings']:
                compiled = compile_statement(item['text'], kind='finding', label=item['label'], source=source)
                if any(slot['kind'] == 'context' for slot in compiled['slots']):
                    raise SystemExit(f'{exam["id"]}/{authored["id"]}: unenumerated blank in {item["text"]!r}')
            if authored['normal'] and compile_statement(authored['normal'], kind='normal', source=source)['slots']:
                raise SystemExit(f'{exam["id"]}/{authored["id"]}: a normal statement has slots')


def rewrite_json(path, change):
    text = path.read_text(encoding='utf-8')
    data = json.loads(text)
    if json.dumps(data, ensure_ascii=False, indent=1) + '\n' != text:
        raise SystemExit(f'{path.name} is not in the expected layout')
    change(data)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')


def main():
    exams = examinations()
    check(exams)
    additions = {
        'version': '2026-11-19',
        'sources': [{'id': 'acr-parameters', 'title': 'ACR practice parameters and technical standards',
                     'url': 'https://www.acr.org/clinical-resources/clinical-tools-and-reference/practice-parameters-and-technical-standards'}],
        'investigations': {exam['id']: {'guide_id': exam['guide'], 'title': exam['title'], 'modality': exam['modality'],
                                        'base_investigation_id': exam['base'], 'sections': exam['rows']} for exam in exams},
        'coverage': [{'investigation_id': exam['id'], 'expected_anatomy_ids': [r['id'] for r in exam['rows']]} for exam in exams],
    }
    (DATA / 'anatomic-additions-20261119.json').write_text(json.dumps(additions, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    (DATA / 'report-templates' / 'additions-20261119.json').write_text(template_text(exams), encoding='utf-8')

    def titles(data):
        data['practice_studies'].update(PRACTICE)
        data['titles'].update(TITLES)
    rewrite_json(DATA / 'prism-titles.json', titles)
    rewrite_json(ROOT / 'tools' / 'authoring' / 'practice_examinations.json', lambda data: data.update(PRACTICE))
    for exam in exams:
        print(f'{exam["id"]}: {len(exam["sections"])} headings, {len(exam["rows"])} selectable rows, {len(TITLES[exam["id"]])} Prism titles')


if __name__ == '__main__':
    main()
