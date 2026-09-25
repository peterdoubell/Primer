"""Radiology Assistant's source taxonomy projected into investigation references.

The learning curriculum remains independent. Only published foundation topics
are eligible for this clinical reference catalogue.
"""
import copy
import json
from datetime import date
from functools import lru_cache
from pathlib import Path

from .radiology import DATA, validate_reference, validate_reporting_guide

STEP_DIR = DATA / 'reporting-steps'
MESH_MANIFEST = DATA.parents[1] / 'web' / 'anatomy' / 'bodyparts3d' / 'manifest.json'
# Mirrors the aliases in web/radiology-detailed-anatomy.js.
MESH_ALIASES = {'foot': 'ankle', 'hand': 'wrist', 'pelvis': 'hip', 'heart': 'coronary', 'kidney': 'renal'}


def _read(name, default=None):
    path = DATA / name
    if not path.exists() and default is not None:
        return default
    return json.loads(path.read_text(encoding='utf-8'))


def _text(value, message):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(message)
    return value


@lru_cache(maxsize=1)
def _mesh_regions():
    manifest = json.loads(MESH_MANIFEST.read_text(encoding='utf-8'))
    return {name: [part['id'] for part in region['parts']]
            for name, region in manifest['regions'].items()}


def mesh_region(family):
    """The registered source-mesh region shown for a model family, if any."""
    name = MESH_ALIASES.get(family, family)
    return name if name in _mesh_regions() else None


@lru_cache(maxsize=1)
def _steps():
    """Step guides, one file per Radiology Assistant specialty."""
    sections = {item['id']: item['section'] for item in catalogue()['investigations']}
    merged, reviewed = {}, {}
    for path in sorted(STEP_DIR.glob('*.json')):
        data = json.loads(path.read_text(encoding='utf-8'))
        stamp = date.fromisoformat(data['reviewed_at']).isoformat()
        for identifier, entry in data['investigations'].items():
            if identifier not in sections:
                raise ValueError('Step guide has no Radiology Assistant investigation: ' + identifier)
            if identifier in merged:
                raise ValueError('Duplicate step guide: ' + identifier)
            if sections[identifier] != data['section']:
                raise ValueError('Step guide filed under the wrong specialty: ' + identifier)
            merged[identifier], reviewed[identifier] = entry, stamp
    return {'investigations': merged, 'reviewed_at': reviewed}


def _step_model(item, authored):
    """A corrected 3D companion when the backing module's anatomy is wrong for this examination."""
    model = authored.get('model')
    if not model:
        return None
    aim = _text(model.get('reporting_aim'), 'Corrected 3D companion needs its reporting aim')
    family = _text(model.get('family'), 'Corrected 3D companion needs a family')
    return {'id': 'radiology-model-' + item['id'], 'title': item['title'] + ' · spatial orientation',
            'instructions': 'Drag to rotate; choose a reporting landmark and move the section plane. ' + aim,
            'scenario': 'radiology-investigation:' + item['id'], 'family': family,
            'focus': [authored['steps'][0]['landmark']], 'reporting_aim': aim}


def _walkthrough(item, ref):
    """Order the examination's own report fields, figures, measurements and model into steps.

    Every step edits named sections of the investigation's report template; the
    report is always reassembled in template order. Nothing here scores a study.
    """
    guide, template = ref['reporting'], ref['report_templates'][0]
    headings = [section['heading'] for section in template['sections']]
    checklist = guide['checklist']
    authored = _steps()['investigations'].get(item['id'])
    if authored is None:
        # A newly added investigation still walks through its own fields.
        derived = [section['heading'] for section in guide['template_sections'] if section['heading'] in headings]
        authored = {'steps': [{'sections': [heading], 'landmark': ref['spatial_model']['focus'][0]}
                              for heading in derived or headings[1:-1]]}
        complete = False
    else:
        complete = True
    images = [image['id'] for image in ref['key_images']]
    measures = [row['name'] for row in guide['measurements']]
    region = mesh_region(ref['spatial_model']['family'])
    allowed_parts = set(_mesh_regions()[region]) if region else set()
    owned, used_images, used_measures, steps = [], set(), set(), []
    for index, step in enumerate(authored['steps']):
        sections = step.get('sections')
        if not isinstance(sections, list) or not sections or any(h not in headings for h in sections):
            raise ValueError('Reporting step must edit sections of its own template: ' + item['id'])
        owned.extend(sections)
        base = checklist[index] if index < len(checklist) else {}
        label = _text(step.get('label') or base.get('label') or sections[0].capitalize(), 'Reporting step needs a label')
        detail = _text(step.get('detail') or base.get('detail') or 'Complete the ' + sections[0].lower() + ' field.',
                       'Reporting step needs its assessment')
        normal = step.get('normal')
        if isinstance(normal, str):
            if len(sections) != 1:
                raise ValueError('A shared normal statement needs a section for each field: ' + item['id'])
            normal = {sections[0]: normal}
        normal = normal or {}
        if not isinstance(normal, dict) or not set(normal).issubset(sections):
            raise ValueError('Normal statements must belong to the step sections: ' + item['id'])
        for value in normal.values():
            _text(value, 'Empty normal statement')
        findings = step.get('findings', [])
        if not isinstance(findings, list) or len(findings) > 6 or (complete and not findings):
            raise ValueError('Reporting step needs one to six finding phrases: ' + item['id'])
        for phrase in findings:
            _text(phrase, 'Empty finding phrase')
        step_images, step_measures, parts = (step.get(key, []) for key in ('images', 'measurements', 'parts'))
        for values, known, name in ((step_images, images, 'figure'), (step_measures, measures, 'measurement'),
                                    (parts, allowed_parts, 'anatomical part')):
            if not isinstance(values, list) or len(values) != len(set(values)) or not set(values).issubset(known):
                raise ValueError('Reporting step has an unknown or repeated ' + name + ': ' + item['id'])
        used_images.update(step_images)
        used_measures.update(step_measures)
        entry = {'label': label, 'detail': detail, 'sections': list(sections), 'normal': dict(normal),
                 'findings': list(findings), 'images': list(step_images), 'measurements': list(step_measures),
                 'landmark': _text(step.get('landmark'), 'Reporting step needs a 3D landmark'), 'parts': list(parts)}
        for key in ('look', 'tip'):
            if step.get(key) is not None or (complete and key == 'look'):
                entry[key] = _text(step.get(key), 'Reporting step needs ' + key)
        steps.append(entry)
    if len(owned) != len(set(owned)):
        raise ValueError('A report section belongs to one step: ' + item['id'])
    positions = sorted(headings.index(heading) for heading in owned)
    first, last = positions[0], positions[-1]
    if any(heading not in owned for heading in headings[first:last + 1]):
        raise ValueError('Every finding section between the introduction and impression needs a step: ' + item['id'])
    if not first or last == len(headings) - 1:
        raise ValueError('The walkthrough needs introductory and impression sections: ' + item['id'])
    if complete and set(measures) - used_measures:
        raise ValueError('Every measurement needs a reporting step: ' + item['id'])
    return {'reviewed_at': _steps()['reviewed_at'].get(item['id'], guide['reviewed_at']),
            'complete': complete, 'template_id': template['id'],
            'start': {'sections': headings[:first], 'images': [i for i in images if i not in used_images]},
            'steps': steps, 'finish': {'sections': headings[last + 1:]}}


@lru_cache(maxsize=1)
def _articles():
    return {article['id']: article for article in _read('source-catalog.json')['articles']}


@lru_cache(maxsize=1)
def catalogue():
    source = _read('source-catalog.json')
    catalog = _read('reference-investigations.json')
    articles = _articles()
    seen, identifiers = [], set()
    for item in catalog['investigations']:
        if item['id'] in identifiers or not item['id'].startswith('ra.'):
            raise ValueError('Investigation identifiers must be unique and source-scoped')
        identifiers.add(item['id'])
        selected = [articles[identifier] for identifier in item['article_ids']]
        if not selected or item['source_titles'] != [article['title'] for article in selected]:
            raise ValueError('Investigation headings must preserve the source article titles')
        if item['section'] not in {article['section'] for article in selected}:
            raise ValueError('Investigation uses a specialty absent from its sources')
        if item['module_id'] not in {article['module_id'] for article in selected}:
            raise ValueError('Investigation content must be supported by its assigned articles')
        seen.extend(item['article_ids'])
    if len(seen) != len(set(seen)) or set(seen) != set(articles):
        raise ValueError('Every foundation article must map to exactly one investigation')
    return catalog


@lru_cache(maxsize=1)
def _overrides():
    overrides = {}
    for name in ('investigation-overrides.json', 'investigation-overrides-non-msk.json'):
        values = _read(name, {})
        if set(values) & set(overrides):
            raise ValueError('Duplicate investigation override')
        overrides.update(values)
    known = {item['id'] for item in catalogue()['investigations']}
    if not set(overrides).issubset(known):
        raise ValueError('Override has no Radiology Assistant investigation')
    for override in overrides.values():
        if 'reporting' in override:
            validate_reporting_guide(override['reporting'])
    return overrides


@lru_cache(maxsize=1)
def _visuals():
    merged = {}
    for name in ('detailed-visuals.json', 'investigation-source-images.json'):
        for identifier, images in _read(name, {}).items():
            merged.setdefault(identifier, []).extend(images)
    return merged


def resolve(identifier):
    investigations = catalogue()['investigations']
    exact = next((item for item in investigations if item['id'] == identifier), None)
    if exact:
        return exact
    # Keep previously shared links useful, but never surface unsupported topics.
    return next((item for item in investigations if item['module_id'] == identifier), None)


def _template(item, guide, base):
    template = copy.deepcopy(base)
    template['id'] = item['id'].replace('.', '-') + '-report'
    template['title'] = item['title'].upper()
    # Shared headers must be rebuilt too: retaining a broad module's protocol
    # would, for example, silently put MRI technique into fluorodefecography.
    prefix = [
        {'heading': 'INDICATION', 'body': 'Clinical question: [ ].\nRelevant history, symptoms and prior procedures: [ ].'},
        {'heading': 'COMPARISON', 'body': '[None / examination and date].'},
        {'heading': 'TECHNIQUE AND QUALITY', 'body': '\n'.join(guide['protocol']) +
         '\n\nAcquisition details: [ ].\nQuality: [diagnostic / limited / non-diagnostic].\nLimitation and effect: [ ].'},
        {'heading': 'KEY IMAGES', 'body': '\n'.join('[IMG {}: {}; series __ image __]'.format(i, section['heading'].lower())
            for i, section in enumerate(guide['template_sections'][:3], 1))},
    ]
    template['sections'] = prefix + copy.deepcopy(guide['template_sections']) + [
        {'heading': 'IMPRESSION', 'body': '\n'.join('{}. [{}]'.format(i, prompt)
            for i, prompt in enumerate(guide['impression_prompts'], 1))},
        {'heading': 'RECOMMENDATION AND COMMUNICATION', 'body': 'Recommended next step and rationale: [ ].\nDirect communication, when indicated: [recipient, time, method].'},
    ]
    template['description'] = 'Reporting fields for ' + item['title'] + '. Complete the relevant observations and remove unused alternatives.'
    template['notes'] = guide['pitfalls']
    template['sources'] = guide['sources']
    return template


def detail(curriculum, item):
    node = curriculum.node(item['module_id'])
    if not node:
        raise ValueError('Investigation backing content is missing')
    ref = copy.deepcopy(node['radiology_reference'])
    articles = _articles()
    ref['reading'] = [copy.deepcopy(articles[identifier]) for identifier in item['article_ids']]
    ref['supplementary'] = False
    ref['overview'] = item['summary']
    override = copy.deepcopy(_overrides().get(item['id'], {}))
    for key, value in override.items():
        ref[key] = value
    # A broad module may cover incompatible examinations. The scoped guide is
    # authoritative and does not inherit a classification table by accident.
    if 'reporting' in override and 'report_templates' not in override:
        ref['report_templates'] = [_template(item, ref['reporting'], ref['report_templates'][0])]
    assigned_urls = {article['url'].rstrip('/') for article in ref['reading']}
    candidates = list(_visuals().get(item['id'], [])) + ref['key_images']
    selected, seen = [], set()
    for image in candidates:
        if image.get('source_url', '').rstrip('/') not in assigned_urls:
            continue
        if image['src'] in seen:
            continue
        seen.add(image['src'])
        selected.append(copy.deepcopy(image))
    ref['key_images'] = selected
    ref['investigation'] = copy.deepcopy(item)
    corrected = _step_model(item, _steps()['investigations'].get(item['id'], {}))
    if corrected:
        ref['spatial_model'] = corrected
    ref['spatial_model']['title'] = item['title'] + ' · spatial orientation'
    ref['anatomical_illustrations'] = _read('anatomical-illustrations.json', {}).get(item['id'], [])
    for illustration in ref['anatomical_illustrations']:
        src = illustration.get('src', '')
        if not src.startswith('/app/reference-media/') or '%' in src:
            raise ValueError('Anatomical illustrations must use curated local assets')
        root = DATA.parents[1] / 'web' / 'reference-media'
        path = (root / src.removeprefix('/app/reference-media/')).resolve()
        if root.resolve() not in path.parents or not path.is_file() or path.suffix != '.png':
            raise ValueError('Unknown anatomical illustration asset')
        if illustration.get('kind') != 'generated-illustration':
            raise ValueError('Generated anatomy must retain its provenance label')
    if not override.get('report_templates'):
        for template in ref['report_templates']:
            template['title'] = item['title'].upper()
    # Readings and clinical figure captions are specific to the investigation.
    # Preserve the underlying diagram/model until a source mesh is available.
    validate_reference(ref)
    ref['walkthrough'] = _walkthrough(item, ref)
    return {'id': item['id'], 'module_id': node['id'], 'title': item['title'],
            'section': item['section'], 'topic': item['topic'], 'modality': item['modality'],
            'source_titles': item['source_titles'], 'goal': item['summary'],
            'radiology_reference': ref, 'lesson_media': node['lesson_media']}


def index(curriculum):
    modules = []
    for item in catalogue()['investigations']:
        reference = detail(curriculum, item)['radiology_reference']
        classification = reference['reporting']['classification']
        modules.append({
            'id': item['id'], 'module_id': item['module_id'], 'title': item['title'],
            'section': item['section'], 'topic': item['topic'], 'modality': item['modality'],
            'source_titles': item['source_titles'], 'summary': item['summary'],
            'topics': list(dict.fromkeys([item['topic'], item['modality'], *item['source_titles'],
                *[heading for article in reference['reading'] for heading in article.get('headings', [])],
                *[point['label'] for point in reference['reporting']['checklist']],
                *({'Musculoskeletal': ['MSK'], 'Head/Neck': ['ENT'], 'Pediatrics': ['paediatric', 'pediatric']}.get(item['section'], [])),
                *({'ra.ct-coronary': ['CCTA', 'CTCA'], 'ra.mri-prostate': ['mpMRI', 'PI-RADS']}.get(item['id'], []))])),
            'image_count': len(reference['key_images']),
            'template_count': len(reference['report_templates']),
            'classification': classification['name'] if classification else '',
            'model_family': reference['spatial_model']['family'],
            'step_count': len(reference['walkthrough']['steps']),
            'reviewed_at': reference['reporting']['reviewed_at'],
        })
    return {'modules': modules, 'count': len(modules), 'foundation': catalogue()['foundation_url']}
