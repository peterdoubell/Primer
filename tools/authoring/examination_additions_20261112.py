"""One performed examination in one modality, covering the practice's study list.

Writes:
  data/radiology/anatomic-additions-20261112.json   selectable reports for new examinations
  data/radiology/report-templates/additions-20261112.json   their fast templates
  data/radiology/prism-titles.json   practice (RIS/Prism) study titles per examination

Two kinds of new examination:
  splits  an existing examination whose title spans modalities keeps its first modality;
          each other modality becomes its own examination, cloned from the same rows with
          the other modalities' choices and statements removed;
  gaps    a practice study with no examination; its rows come from the practice's normal
          report, one structure per line, with enumerated abnormal findings.
Standard protocols come from tools/authoring/radiology_exam_definitions.py.

Run from the repository root: python3 tools/authoring/examination_additions_20261112.py
"""
import copy
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tools' / 'authoring'))
from radiology_exam_definitions import EXAMS  # noqa: E402
from tools.build_descriptor_reporting import compile_statement  # noqa: E402

DATA = ROOT / 'data' / 'radiology'
FORMS = json.loads((DATA / 'descriptor-reporting.json').read_text())['forms']
FAST = {}
for path in sorted((DATA / 'report-templates').glob('*.json')):
    if path.name != 'additions-20261112.json':
        FAST.update(json.loads(path.read_text())['templates'])
PRACTICE = {n['name']: n for n in json.loads((DATA / 'radproof-practice-library.json').read_text())['templates']}
INVESTIGATIONS = {i['id']: i for i in json.loads((DATA / 'reference-investigations.json').read_text())['investigations']}
SPEC = {'ex.' + e['id']: e for e in EXAMS}
for exam in SPEC.values():
    exam.setdefault('practice', [])

SOURCES = [
    {'id': 'acr-parameters', 'title': 'ACR practice parameters and technical standards',
     'url': 'https://www.acr.org/clinical-resources/clinical-tools-and-reference/practice-parameters-and-technical-standards'},
    {'id': 'rcr-standards', 'title': 'The Royal College of Radiologists: clinical radiology standards and guidance',
     'url': 'https://www.rcr.ac.uk/our-services/all-our-publications/clinical-radiology-publications/'},
]
OUT = {'version': '2026-11-12', 'sources': SOURCES, 'investigations': {}, 'coverage': []}
FAST_OUT = {'schema': 'primer.fast-report-templates/1', 'revision': '2026-11-12', 'templates': {}}
RETITLED = {}

MODALITY = {
    'CT': r'\bCT\b|\bCTA\b|\bHRCT\b|Hounsfield|\bHU\b|CT angiograph|CT perfusion',
    'MRI': r'\bMRI?\b|\bMRA\b|\bMRV\b|MRCP|\bDWI\b|\bADC\b|FLAIR|\bSWI\b|gadolinium|T1|T2|STIR|diffusion|susceptib|MR angiograph|MR venograph|chemical[- ]shift|sequence|signal',
    'Ultrasound': r'ultrason|sonograph|Doppler|duplex|graded compression|compressib|Murphy|transducer|echogen|acoustic|\b3D ultrasound',
    'Radiography': r'radiograph|projection|plain film|X-ray',
    'Fluoroscopy': r'fluoroscop|barium|oral contrast swallow',
}


def other_only(text, modality):
    own = re.search(MODALITY.get(modality, r'$^'), text, re.I)
    return (not own) and any(re.search(p, text, re.I) for m, p in MODALITY.items() if m != modality)


def filter_text(text, modality):
    """Drop choices naming another modality; None if the statement itself is about another."""
    def keep(match):
        choices = [c for c in match.group(1).split(' / ') if not other_only(c, modality)]
        if not choices:
            return '\0'
        return '[' + ' / '.join(choices) + ']' if len(choices) > 1 else choices[0]
    out = re.sub(r'\[([^\[\]]*\/[^\[\]]*)\]', keep, text)
    if '\0' in out or other_only(re.sub(r'\[[^\]]*\]', '', out), modality):
        return None
    return out


def one_line(lines):
    text = ' '.join(lines)
    text = re.sub(r'[\[\]]', '', text).replace('\n', ' ').strip()
    return text if text.endswith('.') else text + '.'


# ----------------------------------------------------------------------------- splits
SPLITS = {  # existing examination -> new examinations (id, modality, title, spec giving the protocol)
    'ra.appendicitis': [('ct.appendix', 'CT', 'CT abdomen and pelvis with contrast, appendicitis', 'ex.ct-appendix')],
    'ra.liver-masses': [('ct.liver-mass', 'CT', 'CT liver, multiphase', 'ex.ct-liver-mass')],
    'ra.liver-lirads': [('ct.liver-lirads', 'CT', 'CT liver, multiphase, HCC surveillance', 'ex.ct-liver-lirads')],
    'liver.lirads-calculated': [('ct.liver-lirads-calculated', 'CT', 'CT liver, LI-RADS v2018', 'ex.ct-liver-lirads')],
    'ra.esophagus': [('ct.oesophagus', 'CT', 'CT chest with oral contrast', 'ex.ct-oesophagus')],
    'ra.breast-implants': [('us.breast-implants', 'Ultrasound', 'Ultrasound breast implants', 'ex.us-breast-implants')],
    'ra.cardiac-masses': [('ct.cardiac-mass', 'CT', 'CT heart', 'ex.ct-cardiac-mass')],
    'ra.carotid-obstruction': [('ct.angiogram-carotids', 'CT', 'CT angiogram carotids', 'ex.cta-neck'),
                               ('mri.angiogram-carotids', 'MRI', 'MR angiogram carotids', 'ex.mra-neck')],
    'ra.thymus': [('mri.thymus', 'MRI', 'MRI thymus', 'ex.mri-thymus')],
    'ra.paediatric-mediastinum': [('mri.paediatric-mediastinum', 'MRI', 'MRI chest, paediatric', None)],
    'ra.renal-cysts-bosniak': [('mri.renal-cyst', 'MRI', 'MRI kidneys, renal cyst', 'ex.mri-renal-cyst')],
    'ra.solid-renal-masses': [('mri.renal-mass', 'MRI', 'MRI kidneys, renal mass', 'ex.mri-renal-mass')],
    'ra.adrenal-lesions': [('mri.adrenals', 'MRI', 'MRI adrenals', 'ex.mri-adrenal')],
    'ra.ovarian-cysts': [('mri.adnexal-mass', 'MRI', 'MRI pelvis, adnexal mass', 'ex.mri-ovarian-cyst')],
    'ra.mullerian-anomalies': [('us.uterus-3d', 'Ultrasound', '3D ultrasound uterus', None)],
    'ra.bone-tumours': [('xr.bone-lesion', 'Radiography', 'Radiographs, bone lesion', 'ex.xr-bone-tumour')],
    'ra.cartilage-tumours': [('xr.cartilage-lesion', 'Radiography', 'Radiographs, cartilage lesion', None)],
    'ra.stress-fractures': [('xr.stress-injury', 'Radiography', 'Radiographs, stress injury', None)],
    'ra.acute-stroke': [('mri.brain-stroke', 'MRI', 'MRI brain, stroke protocol', 'ex.mri-brain-stroke')],
    'ra.brain-anatomy': [('mri.brain-anatomy', 'MRI', 'MRI brain', None)],
    'ra.intracranial-haemorrhage': [('mri.brain-haemorrhage', 'MRI', 'MRI brain, haemorrhage', 'ex.mri-brain-haemorrhage')],
    'ra.venous-sinus-thrombosis': [('mri.venogram', 'MRI', 'MR venogram', 'ex.mr-venogram')],
    'ra.ct-mri-eye': [('mri.orbits', 'MRI', 'MRI orbits', 'ex.mri-orbits')],
    'ra.tinnitus': [('ct.angiogram-head-neck-tinnitus', 'CT', 'CT angiogram head and neck, pulsatile tinnitus', None)],
    'ra.mri-sinuses': [('ct.sinuses', 'CT', 'CT paranasal sinuses', 'ex.ct-sinuses')],
    'ra.head-neck-malignancy': [('mri.neck-tumour', 'MRI', 'MRI neck, cancer staging', 'ex.mri-neck-tumour')],
    'ra.cervical-lymph-nodes': [('ct.neck-nodes', 'CT', 'CT neck with contrast, lymph nodes', None)],
    'ra.paediatric-cystic-abdominal-masses': [('mri.paediatric-abdomen-cystic', 'MRI', 'MRI abdomen, paediatric', None)],
    'ra.paediatric-solid-abdominal-masses': [('ct.paediatric-abdomen-solid', 'CT', 'CT abdomen with contrast, paediatric', None),
                                            ('mri.paediatric-abdomen-solid', 'MRI', 'MRI abdomen, paediatric', None)],
    'ra.paediatric-renal-tumours': [('mri.paediatric-renal-tumour', 'MRI', 'MRI abdomen, paediatric renal tumour', None)],
    'ra.thoracolumbar-fractures': [('mri.thoracolumbar-trauma', 'MRI', 'MRI thoracic and lumbar spine, trauma', 'ex.mri-thoracolumbar-spine-trauma')],
    'ra.male-breast': [('us.male-breast', 'Ultrasound', 'Ultrasound male breast', 'ex.us-male-breast')],
    'ra.cervical-spine-injury': [('mri.cervical-spine-trauma', 'MRI', 'MRI cervical spine, trauma', 'ex.mri-cervical-spine-trauma')],
}


def compiled_rows(identifier):
    for form_id, form in FORMS.items():
        for investigation in form['investigations']:
            if investigation['id'] == identifier:
                return form_id, investigation['sections']
    raise KeyError(identifier)


def source_rows(sections, modality):
    rows = []
    for section in sections:
        normal = section['normal']['text'] if isinstance(section['normal'], dict) else section['normal']
        if normal:
            normal = filter_text(normal, modality)
            if normal is None:
                continue
        findings, dropped = [], set()
        for finding in section['findings']:
            text = filter_text(finding['text'], modality)
            local = finding['id'].split(':')[-1]
            if text is None:
                dropped.add(local)
                continue
            item = {'id': local, 'label': finding['label'], 'text': text}
            for key in ('exclusive_group', 'report'):
                if key in finding:
                    item[key] = finding[key]
            findings.append((item, [r.split(':')[-1] for r in finding.get('requires_any', [])]))
        kept = []
        local_ids = {f['id'] for f, _ in findings}
        for item, needs in findings:
            needs = [n for n in needs if n in local_ids and n != item['id']]
            if needs:
                item['requires_any'] = needs
            kept.append(item)
        if not kept and not normal:
            continue
        if not kept:
            kept = [{'id': 'assessment', 'label': section['label'],
                     'text': section['label'] + ' is [abnormal / not assessed].'}]
        row = {'id': section.get('anatomy_id') or re.sub(r'^anatomy-', '', section['id']), 'label': section['label'],
               'group': section['group'], 'normal': normal, 'findings': kept, 'source_ids': ['acr-parameters']}
        if section.get('exclude_from_bulk_normal'):
            row['exclude_from_bulk_normal'] = True
        rows.append(row)
    seen, unique = set(), []
    for row in rows:
        base, n = row['id'], 2
        while row['id'] in seen:
            row['id'] = f'{base}-{n}'
            n += 1
        seen.add(row['id'])
        unique.append(row)
    return unique


def fast_split(base, modality, title, protocol):
    item = copy.deepcopy(FAST[base])
    item['title'] = title
    item['radiograph'] = modality == 'Radiography'
    sections = []
    for section in item['sections']:
        normal = filter_text(section['normal'], modality)
        if normal is None or '[' in normal:
            continue
        options = [o for o in (filter_text(x, modality) for x in section.get('options', [])) if o]
        sections.append(dict(section, normal=normal, options=options[:4]))
    item['sections'] = sections
    impressions = item['impression'] if isinstance(item['impression'], list) else [item['impression']]
    item['impression'] = [i for i in impressions if filter_text(i, modality) and '[' not in i] or ['No significant abnormality.']
    if item['radiograph']:
        item.pop('technique', None)
    else:
        options = [o for o in (filter_text(x, modality) for x in item.get('technique', {}).get('options', [])) if o]
        item['technique'] = {'normal': protocol, 'options': options[:3]}
    return item


def retitle_base(base):
    """The existing examination keeps the modality of its technique line (its first title part)."""
    title = {'ra.male-breast': 'Mammography, male breast'}.get(base, FAST[base]['title'].split(' / ')[0])
    RETITLED[base] = title


# ----------------------------------------------------------------------------- gaps
CATEGORY = [
    (r'fracture|bone|osseous|cortex|cortical|alignment|dislocation|vertebra|joint|ossification|calcan|mortise|talar|carpal|scaph|hardware|prosthe', 'a [fracture / dislocation / lytic lesion / sclerotic lesion / degenerative change] is present'),
    (r'lung|pleura|pneumothorax|airway|bronch|consolidation', 'there is [consolidation / a nodule / a mass / pleural effusion / pneumothorax / interstitial change]'),
    (r'heart|cardiac|mediastin|hila|pericard', 'there is [enlargement / a mass / an effusion / abnormal contour]'),
    (r'aort|arter|vein|venous|vessel|flow|thromb|doppler|stenosis|anastom', 'there is [stenosis / occlusion / thrombus / an aneurysm / abnormal flow]'),
    (r'bowel|colon|caec|rectum|rectal|stomach|duoden|oesophag|esophag|swallow|peristal|reflux|mucosa|lumen|contrast passes|hernia|gas', 'there is [a stricture / a filling defect / a mass / wall thickening / dilatation / a leak / reflux]'),
    (r'liver|spleen|pancrea|kidney|renal|adrenal|gallbladder|biliary|bile|bladder|uter|ovar|prostat|thyroid|testi|scrot|epididym|endometr|adnex|pituitar|gland', 'there is [a focal lesion / diffuse abnormality / enlargement / atrophy / calculus / dilatation]'),
    (r'brain|ventric|white matter|grey|intracranial|sulci|cerebell|ventricular|midline|haemorrhage', 'there is [haemorrhage / infarction / a mass / atrophy / hydrocephalus / white matter change]'),
    (r'fluid|collection|effusion|ascites|abscess', 'there is [free fluid / a collection / an effusion / free gas]'),
    (r'node|lymph', 'there is [lymphadenopathy / an abnormal node]'),
    (r'soft tissue|tendon|ligament|muscle|fascia|bursa|lump|mass|nerve', 'there is [a tear / tendinopathy / a collection / a mass / inflammation]'),
]


def label_of(line):
    text = re.sub(r'^(The|No|Normal)\s+', '', line.strip().rstrip('.'), flags=re.I)
    text = re.split(r'\s+(?:is|are|was|were|shows?|has|have)\b|,| with ', text)[0]
    words = text.split()
    label = ' '.join(words[:6]) or 'Findings'
    return label[0].upper() + label[1:]


def finding_for(label, line):
    for pattern, phrase in CATEGORY:
        if re.search(pattern, line, re.I):
            return f'{label}: {phrase}.'
    return f'{label}: [abnormal appearance / indeterminate appearance / not assessed].'


def practice_lines(normal):
    text = re.sub(r'(?:[ \t]+#[a-z][a-z0-9-]*)+[ \t]*$', '', normal['text'], flags=re.M)
    text = text.replace('**', '').replace('__', '')
    text = re.sub(r'\{(?:SIDE|Side|side)\}\s*', '', text).replace('{S}', 'S').replace('{s}', 's')
    lines = text.split('\n')[1:]
    groups, group, conclusion, in_conclusion = [], 'Findings', [], False
    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        if line.endswith(':') and len(line.split()) <= 6:
            if re.match(r'(?i)conclusions?:', line):
                in_conclusion = True
            else:
                group = line[:-1].strip().capitalize()
            continue
        if in_conclusion:
            conclusion.append(line)
        elif '[' not in line:
            groups.append((group, line))
    return groups, conclusion


def gap_rows(groups):
    rows, seen = [], set()
    for group, line in groups:
        label = label_of(line)
        key = re.sub(r'[^a-z0-9]+', '-', label.lower()).strip('-')[:40] or 'findings'
        base, n = key, 2
        while key in seen:
            key, n = f'{base}-{n}', n + 1
        seen.add(key)
        normal = line if line.endswith('.') else line + '.'
        rows.append({'id': key, 'label': label, 'group': group, 'normal': normal, 'source_ids': ['acr-parameters'],
                     'findings': [{'id': 'abnormal', 'label': label, 'text': finding_for(label, line)}]})
    return rows


def gap_fast(title, modality, protocol, rows, conclusion):
    groups = {}
    for row in rows:
        groups.setdefault(row['group'], []).append(row)
    if len(groups) < 2:
        groups = {re.sub(r'[^\w ,/()\'\-]', '', row['label'])[:60].strip() or 'Findings': [row] for row in rows}
    sections = []
    for heading, members in list(groups.items())[:12]:
        heading = heading[0].upper() + heading[1:]
        heading = re.sub(r'[^\w)]+$', '', heading)
        if heading.lower() in {'clinical history', 'technique', 'comparison', 'impression', 'recommendation'}:
            heading += ' findings'
        sections.append({'heading': heading, 'normal': ' '.join(m['normal'] for m in members),
                         'options': [m['findings'][0]['text'] for m in members][:4]})
    if not sections:
        sections.append({'heading': 'Findings', 'normal': 'Images obtained during the procedure.',
                         'options': ['[Device / Fracture reduction / Contrast] position [ ].']})
    if len(sections) < 2:
        sections.append({'heading': 'Other findings', 'normal': 'No other significant finding.',
                         'options': ['[Incidental / Indeterminate] finding in the [ ].']})
    item = {'title': title, 'radiograph': modality == 'Radiography', 'sections': sections,
            'impression': [c if c.endswith('.') else c + '.' for c in conclusion[:3] if '[' not in c] or ['No significant abnormality.']}
    if modality != 'Radiography':
        item['technique'] = {'normal': protocol, 'options': []}
    return item


def add(identifier, title, modality, guide, base, rows):
    OUT['investigations'][identifier] = {'guide_id': guide, 'title': title, 'modality': modality,
                                         'base_investigation_id': base, 'sections': rows}
    OUT['coverage'].append({'investigation_id': identifier, 'expected_anatomy_ids': [r['id'] for r in rows]})


ACRONYMS = {'ct', 'mri', 'recist', 'cta', 'mra', 'us'}


def sentence(text):
    words = text.lower().split()
    words = [w.upper() if w.strip('(),') in ACRONYMS else w for w in words]
    out = ' '.join(words)
    return out[0].upper() + out[1:] if out else out


PREFIX = {'CT': 'ct', 'MRI': 'mri', 'Ultrasound': 'us', 'Radiography': 'xr', 'Fluoroscopy': 'fl', 'Mammography': 'mg', 'DXA': 'dxa'}
TECHNIQUE_ROW = lambda modality: {  # noqa: E731
    'id': 'technique', 'label': 'Examination performed', 'group': 'Technique', 'normal': None,
    'source_ids': ['acr-parameters'], 'exclude_from_bulk_normal': True,
    'findings': [{'id': 'assessment', 'label': 'Examination performed',
                  'text': 'The examination was performed [to the standard protocol / with a modified protocol / as a limited examination].'}]}


def build():
    served = set(FAST)
    for base, splits in SPLITS.items():
        if base not in FAST:
            raise SystemExit('Unknown split base ' + base)
        retitle_base(base)
        guide, sections = compiled_rows(base)
        for identifier, modality, title, spec_id in splits:
            protocol = one_line(SPEC[spec_id]['protocol']) if spec_id else one_line([FAST[base].get('technique', {}).get('normal', title)])
            rows = source_rows(sections, modality)
            if len(rows) < 2:
                raise SystemExit(identifier + ': too little left after the modality filter')
            teaching = base if base in INVESTIGATIONS else next(
                i.get('base_investigation_id') for f in FORMS.values() for i in f['investigations'] if i['id'] == base)
            add(identifier, title, modality, guide, teaching, rows)
            FAST_OUT['templates'][identifier] = fast_split(base, modality, title, protocol)
    practice_map = json.loads((ROOT / 'tools' / 'authoring' / 'practice_examinations.json').read_text())
    if practice_map is None: raise SystemExit('no practice map')
    for name, target in practice_map.items():
        if target is not None:
            continue
        spec = next(s for s in SPEC.values() if name in s.get('default', []))
        modality = spec['modality']
        identifier = PREFIX[modality] + '.' + re.sub(r'^(ct|mri|us|xr|fl|mg|dxa|cta|mra|mr)-', '', spec['id'])
        if identifier in served or identifier in OUT['investigations']:
            identifier = PREFIX[modality] + '.' + spec['id']
        groups, conclusion = practice_lines(PRACTICE[name])
        rows = [TECHNIQUE_ROW(modality)] + gap_rows(groups)
        if spec['findings'] not in ('practice',) and isinstance(spec['findings'], dict):
            rows = [TECHNIQUE_ROW(modality)] + [
                {'id': re.sub(r'[^a-z0-9]+', '-', heading.lower()).strip('-'), 'label': sentence(heading),
                 'group': sentence(re.sub(r'[^\w ,/\'\-]', '', heading.replace('RECIST 1.1', 'RECIST')).strip()), 'normal': f'{sentence(heading)}: no acute abnormality.',
                 'source_ids': ['acr-parameters'],
                 'findings': [{'id': 'abnormal', 'label': sentence(heading),
                               'text': finding_for(sentence(heading), heading)}]}
                for heading, body in spec['findings'].items()]
            conclusion = ['No acute abnormality.']
        base = spec['teaching']
        guide = INVESTIGATIONS[base]['module_id']
        title = {'Bone age': 'Bone age radiograph', 'Lateral cephalogram': 'Lateral cephalometric radiograph'}.get(spec['title'], spec['title'])
        add(identifier, title, modality, guide, base, rows)
        authored = spec['findings'] if isinstance(spec['findings'], dict) else None
        FAST_OUT['templates'][identifier] = gap_fast(title, modality, one_line(spec['protocol']),
                                                     rows[1:], conclusion)
        if authored:
            item = FAST_OUT['templates'][identifier]
            for section, (heading, body) in zip(item['sections'], authored.items()):
                lines = [l.strip() for l in body.split('\n') if l.strip()]
                def pick(m):
                    choices = m.group(1).split(' / ')
                    return m.group(0) if len(choices) > 1 and all(c and c == c.strip() for c in choices) else '[ ]'
                lines = [re.sub(r'\[([^\[\]]*)\]', pick, l) for l in lines]
                section['options'] = [l if l.endswith('.') else l + '.' for l in lines][:4]
            item['impression'] = ['No acute abnormality.']
        practice_map[name] = identifier
    # Validate every authored statement as the compiler will.
    for identifier, investigation in OUT['investigations'].items():
        for position, row in enumerate(investigation['sections']):
            for finding in row['findings']:
                compiled = compile_statement(finding['text'], kind='finding', label=finding['label'],
                                             source={'investigation_id': identifier, 'step_index': position})
                if any(s['kind'] == 'context' for s in compiled['slots']):
                    raise SystemExit(f'{identifier}/{row["id"]}: unenumerated blank in {finding["text"]!r}')
            if row['normal']:
                compiled = compile_statement(row['normal'], kind='normal',
                                             source={'investigation_id': identifier, 'step_index': position})
                if compiled['slots']:
                    raise SystemExit(f'{identifier}/{row["id"]}: a normal statement has slots')
    (DATA / 'anatomic-additions-20261112.json').write_text(json.dumps(OUT, ensure_ascii=False, indent=1) + '\n')
    (DATA / 'report-templates' / 'additions-20261112.json').write_text(json.dumps(FAST_OUT, ensure_ascii=False, indent=1) + '\n')
    # Retitle in place, as text, so the hand-formatted files keep their layout.
    for path in (DATA / 'report-templates').glob('*.json'):
        if path.name == 'additions-20261112.json':
            continue
        text = path.read_text()
        data = json.loads(text)
        for base, title in RETITLED.items():
            item = data['templates'].get(base)
            if not item or item['title'] == title:
                continue
            old = json.dumps(item['title'], ensure_ascii=False)
            at = text.index('"title": ' + old, text.index('"' + base + '": {'))
            text = text[:at] + '"title": ' + json.dumps(title, ensure_ascii=False) + text[at + len('"title": ' + old):]
            modality = next((m for m, p in MODALITY.items() if re.search(p, title, re.I)), None)
            # Edit only this template's technique line.
            start = text.index('"' + base + '": {')
            tech = text.index('"technique": {', start)
            end = text.index('}', tech) + 1
            block = text[tech:end]
            for option in item.get('technique', {}).get('options', []):
                if modality and other_only(option, modality):
                    q = re.escape(json.dumps(option, ensure_ascii=False))
                    before = block
                    for pattern in (r',\s*' + q, q + r',\s*', q):
                        if len(re.findall(pattern, block)) == 1:
                            block = re.sub(pattern, '', block)
                            break
                    assert block != before, (base, option)
            text = text[:tech] + block + text[end:]
        try:
            json.loads(text)
        except ValueError as error:
            raise SystemExit(f'{path.name}: {error}: ' + text[max(0, error.pos - 300):error.pos + 100])
        path.write_text(text)
    # Practice (Prism) study titles per examination: each title belongs to one examination.
    titles, owners = {}, {}
    for name, identifier in practice_map.items():
        for title in PRACTICE[name]['names']:
            owners.setdefault(title.lower(), (title, set()))[1].add(identifier)
    for key, (title, ids) in owners.items():
        if len(ids) == 1:
            titles.setdefault(next(iter(ids)), []).append(title)
    extras = {'ra.mri-rectal-cancer': ['MRI pelvis (rectum)'], 'ra.mri-prostate': ['MRI pelvis (prostate)'],
              practice_map['MRI female pelvis']: ['MRI pelvis (female)']}
    for identifier, values in extras.items():
        titles.setdefault(identifier, []).extend(values)
    shared = sorted(title for title, ids in owners.values() if len(ids) > 1)
    (DATA / 'prism-titles.json').write_text(json.dumps({
        'source': 'RadProof practice template library (Prism study titles), 2026-11-11',
        'practice_studies': practice_map, 'titles': titles, 'shared_left_to_practice': shared},
        ensure_ascii=False, indent=1) + '\n')
    print(json.dumps({'new_examinations': len(OUT['investigations']), 'retitled': len(RETITLED),
                      'practice_mapped': sum(v is not None for v in practice_map.values()),
                      'titles': sum(len(v) for v in titles.values()), 'shared': shared}))


if __name__ == '__main__':
    build()
