"""Radiology Assistant's source taxonomy projected into investigation references.

The learning curriculum remains independent. Only published foundation topics
are eligible for this clinical reference catalogue.
"""
import copy
import hashlib
import json
from datetime import date
import re
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


def _validate_source_derived_figure(image, root):
    """Bind a new teaching projection to its reviewed native mesh sources.

    These checks preserve provenance, not anatomical or clinical approval.
    A derived view must not pretend to be a numbered publisher figure.
    """
    if (image.get('kind') != 'schematic' or image.get('modality') != 'Schematic'
            or not isinstance(image.get('figure_title'), str) or not image['figure_title'].strip()
            or any(key in image for key in ('figure_number', 'source_panel', 'contains_schematic_panels'))):
        raise ValueError('Derived MSK figure needs an explicit schematic title and origin')
    derivation = image.get('derivation', {})
    if not isinstance(derivation, dict):
        raise ValueError('Derived MSK figure needs source and rendering evidence')
    source_url = derivation.get('source_manifest')
    if source_url != '/app/anatomy/openknee-oks003/manifest.json':
        raise ValueError('Derived MSK figure has no reviewed source provider')
    web = root.parents[1]
    source_path = web / source_url.removeprefix('/app/')
    source_bytes = source_path.read_bytes()
    source_sha = hashlib.sha256(source_bytes).hexdigest()
    if derivation.get('source_manifest_sha256') != source_sha:
        raise ValueError('Derived MSK figure source manifest changed')
    source = json.loads(source_bytes)
    if (image.get('license') != source['license']
            or image.get('license_url') != source['license_url']):
        raise ValueError('Derived MSK figure must preserve the reviewed source ShareAlike terms')
    evidence_url = derivation.get('rendering_evidence', '')
    prefix = '/app/reference-media/msk-open/'
    if not isinstance(evidence_url, str) or not evidence_url.startswith(prefix):
        raise ValueError('Derived MSK figure rendering evidence must be local')
    evidence_path = (root / evidence_url.removeprefix(prefix)).resolve()
    if not evidence_path.is_relative_to(root) or not evidence_path.is_file():
        raise ValueError('Derived MSK figure rendering evidence is missing')
    raw = evidence_path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != derivation.get('rendering_evidence_sha256'):
        raise ValueError('Derived MSK figure rendering evidence changed')
    evidence = json.loads(raw)
    if (not isinstance(evidence, dict) or not isinstance(evidence.get('figures'), list)
            or any(not isinstance(row, dict) for row in evidence['figures'])):
        raise ValueError('Derived MSK figure rendering evidence is invalid')
    rows = [row for row in evidence['figures']
            if row.get('filename') == Path(image['src']).name]
    if (evidence.get('source_manifest_sha256') != source_sha or len(rows) != 1
            or rows[0].get('sha256') != image['sha256']
            or (rows[0].get('width'), rows[0].get('height')) != (image['width'], image['height'])):
        raise ValueError('Derived MSK figure does not match its recorded rendering')
    renderer = evidence.get('renderer', {})
    if (not isinstance(renderer, dict)
            or any(renderer.get(key) is not False for key in
                   ('geometry_changed', 'fitted_transform', 'raw_mri_pixels_used'))):
        raise ValueError('Derived MSK figure must retain its reviewed native projection method')
    parts = rows[0].get('parts', [])
    if (not isinstance(parts, list) or not parts
            or any(not isinstance(part, dict) or not isinstance(part.get('id'), str) for part in parts)
            or len({part.get('id') for part in parts}) != len(parts)):
        raise ValueError('Derived MSK figure needs unique native source parts')
    for part in parts:
        original = source['parts'].get(part.get('id'), {})
        if (not original or part.get('source_sha256') != original['source_sha256']
                or part.get('triangles') != original['triangles']
                or part.get('retained_triangles') != original['triangles']
                or part.get('source_positions_and_facet_normals_retained') is not True):
            raise ValueError('Derived MSK figure source geometry changed')
        mesh = web / original['file'].removeprefix('/app/')
        if hashlib.sha256(mesh.read_bytes()).hexdigest() != original['sha256']:
            raise ValueError('Derived MSK figure runtime source geometry changed')


@lru_cache(maxsize=1)
def _structure_atlases():
    """Locally preserved, licensed figures with narrowly stated anatomy scope."""
    catalog = _read('msk-open-images.json', {})
    known = {item['id'] for item in catalogue()['investigations']
             if item['section'] == 'Musculoskeletal'}
    topics = {item['id']: item['topic'] for item in catalogue()['investigations']}
    if not set(catalog).issubset(known):
        raise ValueError('MSK atlas figure has no matching investigation')
    root = (DATA.parents[1] / 'web/reference-media/msk-open').resolve()
    seen = set()
    for images in catalog.values():
        for image in images:
            if image['id'] in seen or image.get('kind') not in {'clinical-image', 'schematic'}:
                raise ValueError('Invalid or duplicated MSK atlas figure')
            if image.get('modality') not in {'MRI', 'MR arthrography', 'CT arthrography', 'Ultrasound', 'Schematic'}:
                raise ValueError('MSK atlas figure needs its actual source modality')
            if 'source_panel' in image and image['source_panel'] not in ('a', 'b', 'c', 'd', 'e', 'f'):
                raise ValueError('MSK source panel needs an explicit publication panel identifier')
            if image.get('contains_schematic_panels'):
                if image['contains_schematic_panels'] is not True or not image.get('schematic_structures_visible'):
                    raise ValueError('Mixed MSK figures need separate schematic coverage')
            ancillary = image.get('ancillary_panels', [])
            if not isinstance(ancillary, list):
                raise ValueError('Ancillary anatomical panels must be explicit records')
            for entry in ancillary:
                if (not isinstance(entry, dict) or entry.get('kind') not in {'Dissection', 'Histology'}
                        or not isinstance(entry.get('panels'), list) or not entry['panels']
                        or any(not isinstance(panel, str) or len(panel) != 1
                               or panel not in 'abcdefghijklmnopqrstuvwxyz' for panel in entry['panels'])
                        or not isinstance(entry.get('structures_visible'), list) or not entry['structures_visible']
                        or any(not isinstance(name, str) or not name.strip() for name in entry['structures_visible'])
                        or not isinstance(entry.get('limits'), str)
                        or not entry['limits'].strip()):
                    raise ValueError('Dissection and histology need distinct panels, observations and limits')
            seen.add(image['id'])
            if not image['src'].startswith('/app/reference-media/msk-open/'):
                raise ValueError('MSK atlas figures must be preserved locally')
            path = (root / image['src'].removeprefix('/app/reference-media/msk-open/')).resolve()
            if not path.is_relative_to(root) or not path.is_file():
                raise ValueError('MSK atlas figure leaves its reviewed directory')
            if hashlib.sha256(path.read_bytes()).hexdigest() != image['sha256']:
                raise ValueError('MSK atlas figure changed after source review')
            # Preserve the source's actual version. Aubry's 2010 hip figures
            # use CC BY 2.0; their grant must not be relabelled as CC BY 4.0.
            reviewed_licenses = {
                'CC BY 2.0': 'https://creativecommons.org/licenses/by/2.0/',
                'CC BY 4.0': 'https://creativecommons.org/licenses/by/4.0/',
                'CC BY-ND 4.0': 'https://creativecommons.org/licenses/by-nd/4.0/',
                'CC BY-SA 3.0 Unported': 'https://creativecommons.org/licenses/by-sa/3.0/',
            }
            if (image.get('license') not in reviewed_licenses
                    or image.get('license_url') != reviewed_licenses[image['license']]):
                raise ValueError('MSK atlas figure needs a reviewed commercial-use license')
            if image.get('origin') == 'source-derived':
                _validate_source_derived_figure(image, root)
            elif (image.get('origin') is not None or 'figure_title' in image or 'derivation' in image
                    or not ((type(image.get('figure_number')) is int and image['figure_number'] > 0)
                            or (isinstance(image.get('figure_number'), str)
                                and re.fullmatch(r'(?:S[1-9][0-9]*|[1-9][0-9]*(?:\.[1-9][0-9]*)+)', image['figure_number'])))):
                raise ValueError('Published MSK figure needs its actual source figure number')
            if image['license'] == 'CC BY-ND 4.0':
                use = image.get('license_use_plan', {})
                if (use.get('mode') != 'unchanged_complete_figure'
                        or use.get('preserve_original_bytes') is not True
                        or use.get('preserve_all_panels') is not True
                        or use.get('distribution_of_adapted_material_permitted') is not False
                        or image.get('source_bytes_sha256') != image['sha256']
                        or image.get('source_bytes_md5') != hashlib.md5(path.read_bytes()).hexdigest()):
                    raise ValueError('ND reference must preserve its complete reviewed original bytes')
            for field in ('alt', 'caption', 'attribution', 'limits', 'rights_review', 'rights_reviewed_on'):
                if not isinstance(image.get(field), str) or not image[field].strip():
                    raise ValueError('MSK atlas figure missing ' + field)
            if not image.get('structures_visible') or not all(isinstance(image.get(key), int)
                    and image[key] > 0 for key in ('width', 'height')):
                raise ValueError('MSK atlas figure needs observed structures and dimensions')
            for field in ('source_url', 'figure_url'):
                if not image[field].startswith('https://'):
                    raise ValueError('MSK atlas source must use HTTPS')
    # A normal anatomical figure can support more than one investigation in
    # the same region. Reuse its exact metadata and modality limits; do not
    # create new source IDs or infer direct radiographic soft-tissue findings.
    authored_sources = set(catalog)
    for target, selection in _read('msk-atlas-sharing.json', {}).items():
        append = False
        if isinstance(selection, str):
            source, include_ids = selection, None
        elif (isinstance(selection, dict) and {'source', 'include_ids'} <= set(selection)
              and not set(selection) - {'source', 'include_ids', 'cross_topic_review', 'mode'}):
            if 'mode' in selection and selection['mode'] != 'append':
                raise ValueError('Shared MSK mode must explicitly append')
            append = selection.get('mode') == 'append'
            source, include_ids = selection['source'], selection['include_ids']
            if (not isinstance(include_ids, list) or not include_ids
                    or any(not isinstance(identifier, str) for identifier in include_ids)
                    or len(set(include_ids)) != len(include_ids)):
                raise ValueError('Shared MSK selection needs unique explicit figure IDs')
        else:
            raise ValueError('Invalid shared MSK figure selection')
        if not isinstance(source, str) or target not in known or source not in authored_sources:
            raise ValueError('Shared MSK anatomy must refer to a known source in the same region')
        if topics[target] != topics[source]:
            review = selection.get('cross_topic_review') if isinstance(selection, dict) else None
            project = DATA.parents[1].resolve()
            if not isinstance(review, dict) or not isinstance(review.get('evidence_path'), str) or not include_ids:
                raise ValueError('Shared MSK cross-topic anatomy needs an explicit selection and scope review')
            evidence = (project / review['evidence_path']).resolve()
            scope_fields = {'source': source, 'target': target, 'include_ids': include_ids,
                            'evidence_sha256': review.get('sha256')}
            if append:
                scope_fields['mode'] = 'append'
            scope = json.dumps(scope_fields, sort_keys=True, separators=(',', ':'))
            if (not evidence.is_relative_to(project / 'docs') or not evidence.is_file()
                    or hashlib.sha256(evidence.read_bytes()).hexdigest() != review.get('sha256')
                    or hashlib.sha256(scope.encode()).hexdigest() != review.get('scope_sha256')):
                raise ValueError('Shared MSK cross-topic anatomy scope review is missing or changed')
        if target in catalog and not append:
            raise ValueError('Shared MSK anatomy cannot overwrite an authored investigation gallery')
        if append and (target not in authored_sources or target == source):
            raise ValueError('Shared MSK append requires a distinct authored target gallery')
        source_images = {image['id']: image for image in catalog[source]}
        if include_ids is not None and not set(include_ids).issubset(source_images):
            raise ValueError('Shared MSK selection includes an unknown figure')
        selected_images = copy.deepcopy(catalog[source] if include_ids is None
                                        else [source_images[identifier] for identifier in include_ids])
        if append:
            if {image['id'] for image in catalog[target]} & {image['id'] for image in selected_images}:
                raise ValueError('Shared MSK append cannot duplicate figure identities')
            catalog[target].extend(selected_images)
        else:
            catalog[target] = selected_images
    return catalog


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
    model_binding = _read('investigation-model-bindings.json', {}).get(item['id'])
    if model_binding and 'regional_references' in model_binding:
        if not isinstance(model_binding['regional_references'], list) or not model_binding['regional_references']:
            raise ValueError('Regional anatomy requires a nonempty list of source references')
        regional = []
        seen_regions = set()
        for entry in model_binding['regional_references']:
            if (not isinstance(entry, dict) or any(not isinstance(entry.get(key), str) or not entry[key].strip()
                    for key in ('source_module_id', 'label', 'population_note'))):
                raise ValueError('Regional anatomy source, label and scope note must be explicit text')
            source_node = curriculum.node(entry['source_module_id'])
            if not source_node or not source_node.get('radiology_reference'):
                raise ValueError('Regional anatomy binding has no source module')
            model = copy.deepcopy(source_node['radiology_reference']['spatial_model'])
            if entry.get('source_atlas') == 'cervical-bones':
                if model['family'] != 'spine':
                    raise ValueError('Cervical source bones require a spine reference binding')
                model.update(family='cervical', source_atlas='cervical-bones')
            elif entry.get('source_atlas'):
                raise ValueError('Unknown regional anatomy source override')
            family = {'hand': 'wrist'}.get(model['family'], model['family'])
            if family not in {'shoulder', 'elbow', 'wrist', 'hip', 'knee', 'ankle', 'cervical'} or family in seen_regions:
                raise ValueError('Regional anatomy binding must identify distinct MSK anatomy')
            if not entry.get('label') or not entry.get('population_note'):
                raise ValueError('Regional anatomy binding needs its scope and limits')
            seen_regions.add(family)
            model.update(label=entry['label'], population_note=entry['population_note'])
            if entry.get('display_mode'):
                if entry['display_mode'] != 'full-muscles' or family == 'cervical' or entry.get('source_view'):
                    raise ValueError('Regional muscle mode requires a registered limb muscle group')
                model.update(initial_layer='muscle', initial_cropped=False)
            if entry.get('source_view'):
                if entry['source_view'] != 'whole-foot' or family != 'ankle':
                    raise ValueError('Regional whole-foot framing requires the ankle/foot source')
                model.update(family='foot', source_view='whole-foot', source_atlas='z-anatomy')
            regional.append(model)
        ref['spatial_model_options'] = regional
        ref['regional_reference_note'] = model_binding.get('regional_reference_note',
            'Regional source anatomy for orientation; complete target-specific clinical anatomy remains unverified.')
        ref['spatial_model'] = copy.deepcopy(regional[0])
        model_binding = None
    if model_binding:
        source_node = curriculum.node(model_binding['source_module_id'])
        if not source_node or not source_node.get('radiology_reference'):
            raise ValueError('Investigation anatomy binding has no source module')
        ref['spatial_model'] = copy.deepcopy(source_node['radiology_reference']['spatial_model'])
        ref['spatial_model']['population_note'] = model_binding['population_note']
        if model_binding.get('source_view'):
            if model_binding['source_view'] == 'hamstrings':
                if model_binding.get('source_atlas') != 'z-anatomy' or ref['spatial_model']['family'] != 'knee':
                    raise ValueError('Hamstring binding requires registered posterior-thigh source muscles')
                ref['spatial_model'].update(source_view='hamstrings', source_atlas='z-anatomy')
            elif (model_binding['source_view'] != 'whole-foot'
                    or model_binding.get('source_atlas') != 'z-anatomy'
                    or ref['spatial_model']['family'] != 'ankle'):
                raise ValueError('Whole-foot anatomy binding requires the registered ankle/foot source')
            else:
                ref['spatial_model'].update(family='foot', source_view='whole-foot', source_atlas='z-anatomy')
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
    ref['structure_atlas'] = copy.deepcopy(_structure_atlases().get(item['id'], []))
    ref['investigation'] = copy.deepcopy(item)
    corrected = _step_model(item, _steps()['investigations'].get(item['id'], {}))
    if corrected:
        ref['spatial_model'] = corrected
    ref['spatial_model']['title'] = item['title'] + ' · spatial orientation'
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
            'image_count': len(reference['key_images']) + len(reference.get('structure_atlas', [])),
            'template_count': len(reference['report_templates']),
            'classification': classification['name'] if classification else '',
            'model_family': reference['spatial_model']['family'],
            'step_count': len(reference['walkthrough']['steps']),
            'reviewed_at': reference['reporting']['reviewed_at'],
        })
    return {'modules': modules, 'count': len(modules), 'foundation': catalogue()['foundation_url']}
