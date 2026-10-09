"""Radiology Assistant's source taxonomy projected into investigation references.

The learning curriculum remains independent. Only published foundation topics
are eligible for this clinical reference catalogue.
"""
import copy
import gzip
import struct
import hashlib
import json
from datetime import date
import re
from functools import lru_cache
from pathlib import Path

from .radiology import DATA, validate_reference, validate_reporting_guide
from .source_raster_integrity import verified_raster_header
from .source_mesh_integrity import verified_mesh_contract
from .source_motion import validate_motion_references

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


SOURCE_REFERENCE_ATLASES = {'liu-lumbosacral-sub03': 'lumbosacral-neural', 'verse521': 'thoracolumbar-source', 'massp2-subcortex': 'brain-subcortex', 'bodyparts3d': 'brain'}
SOURCE_REFERENCE_ATLASES['hvsmr2-pat7'] = 'cardiac-venous-source'
SOURCE_REFERENCE_ATLASES['nasalseg-p001'] = 'sinonasal-source'
SOURCE_REFERENCE_ATLASES['openear-zeta'] = 'temporal-source'
SOURCE_REFERENCE_ATLASES['totalseg-v3-s0358'] = 'thyroid-source'
SOURCE_REFERENCE_ATLASES['totalseg-v3-esophagus-s0358'] = 'esophagus-source'
SOURCE_REFERENCE_ATLASES['wt9fc-sub007'] = 'tongue-source'
SOURCE_REFERENCE_ATLASES['ispy1-expert1002'] = 'breast-tumour-source'
SOURCE_REFERENCE_ATLASES['prostate-biopsy0001'] = 'prostate-source'
SOURCE_REFERENCE_ATLASES['larynx-jasa19629778-phase01'] = 'larynx-phonation-source'
SOURCE_REFERENCE_ATLASES['hra-bladder-female-v1.1'] = 'bladder-source'
SOURCE_REFERENCE_ATLASES['hra-bladder-male-v1.1'] = 'bladder-source'


@lru_cache(maxsize=1)
def _source_motion_references():
    return validate_motion_references(_read('source-motion-references.json',{}),
        {i['id'] for i in catalogue()['investigations']},DATA.parents[1]/'web')


@lru_cache(maxsize=1)
def _source_study_references():
    from .source_study import validate_study_references
    return validate_study_references(_read('source-study-references.json', {}),
        {i['id'] for i in catalogue()['investigations']}, DATA.parents[1] / 'web')


@lru_cache(maxsize=1)
def _source_anatomy_references():
    """Validate curated source resources without assigning anatomical completeness."""
    references = _read('source-anatomy-references.json', {})
    if not isinstance(references, dict):
        raise ValueError('Source anatomy references must be an investigation mapping')
    known = {item['id'] for item in catalogue()['investigations']}
    web = DATA.parents[1] / 'web'
    for investigation, entries in references.items():
        if investigation not in known or not isinstance(entries, list) or not entries:
            raise ValueError('Source anatomy requires a known investigation and nonempty list')
        seen = set()
        for entry in entries:
            if not isinstance(entry, dict):
                raise ValueError('Source anatomy entry must be an object')
            for key in ('id', 'label', 'atlas', 'family', 'manifest_url', 'manifest_sha256', 'initial_layer', 'population_note'):
                _text(entry.get(key), 'Source anatomy requires explicit ' + key)
            if entry['id'] in seen:
                raise ValueError('Duplicate source anatomy reference')
            seen.add(entry['id'])
            if SOURCE_REFERENCE_ATLASES.get(entry['atlas']) != entry['family']:
                raise ValueError('Unknown source anatomy atlas/family')
            expected_url = '/app/anatomy/' + entry['atlas'] + '/manifest.json'
            if entry['manifest_url'] != expected_url or not isinstance(entry.get('initial_cropped'), bool):
                raise ValueError('Source anatomy manifest or initial framing is invalid')
            path = web / expected_url.removeprefix('/app/')
            raw = path.read_bytes()
            if hashlib.sha256(raw).hexdigest() != entry['manifest_sha256']:
                raise ValueError('Source anatomy manifest changed')
            manifest = json.loads(raw)
            region = manifest.get('regions', {}).get(entry['family'])
            legacy_brain = entry['atlas'] == 'bodyparts3d' and entry['family'] == 'brain'
            if not region or (not legacy_brain and not manifest.get('viewer_notes')) or not manifest.get('license'):
                raise ValueError('Source anatomy requires region, scope notes and attribution')
            layers = ({part['layer'] for part in region['parts']} if legacy_brain
                      else {layer[0] for layer in region['layers']})
            if entry['initial_layer'] not in layers:
                raise ValueError('Source anatomy initial layer is unavailable')
            volume = entry.get('source_volume')
            if volume:
                from .source_volume_integrity import verified_volume_identity, CDN_VOLUME_FILES
                filename = CDN_VOLUME_FILES.get(entry['atlas'], 'ct-reference.html')
                if not isinstance(volume, dict) or volume.get('src') != '/app/anatomy/' + entry['atlas'] + '/' + filename:
                    raise ValueError('Source volume must use its registered local viewer')
                if filename=='mri-reference.html' and volume.get('modality')!='MRI':
                    raise ValueError('Registered source MRI viewer needs its actual MRI modality')
                volume_path = web / volume['src'].removeprefix('/app/')
                verified_volume_identity(volume, web, DATA)
                expected_levels = {part_id: manifest['parts'][part_id]['name'].split(' · ')[0] for part_id in manifest['parts']}
                if volume.get('level_by_part') != expected_levels:
                    raise ValueError('Source volume label selections must match the registered source parts')
                script_path = volume_path.with_suffix('.js')
                if hashlib.sha256(script_path.read_bytes()).hexdigest() != volume.get('script_sha256'):
                    raise ValueError('Source volume plane renderer changed')
                for key in ('id', 'title', 'caption', 'attribution', 'source_url', 'license_url'):
                    _text(volume.get(key), 'Source volume requires explicit ' + key)
            source_image = entry.get('source_image')
            if source_image:
                if not isinstance(source_image, dict):
                    raise ValueError('Source anatomy image metadata is invalid')
                prefix = '/app/reference-media/' + entry['atlas'] + '/'
                url = source_image.get('src', '')
                if not isinstance(url, str) or not url.startswith(prefix) or '%' in url or '\\' in url:
                    raise ValueError('Source anatomy image must stay within its source folder')
                image_path = (web / url.removeprefix('/app/')).resolve()
                if (web / prefix.removeprefix('/app/')).resolve() not in image_path.parents:
                    raise ValueError('Source anatomy image leaves its source folder')
                data = image_path.read_bytes()
                if (hashlib.sha256(data).hexdigest() != source_image.get('sha256')
                        or len(data) < 24 or data[:8] != b'\x89PNG\r\n\x1a\n'
                        or struct.unpack('>II', data[16:24]) != (source_image.get('width'), source_image.get('height'))):
                    raise ValueError('Source anatomy image changed or dimensions are invalid')
                for key in ('title', 'alt', 'caption', 'attribution', 'source_url', 'license_url'):
                    _text(source_image.get(key), 'Source anatomy image requires explicit ' + key)
            for selected in region['parts']:
                part = manifest['parts'][selected['id']]
                prefix = '/app/anatomy/' + entry['atlas'] + '/'
                url = part.get('file', '')
                if not isinstance(url, str) or not url.startswith(prefix) or '%' in url or '\\' in url:
                    raise ValueError('Source anatomy mesh must remain in its atlas')
                header, decoded_size = verified_mesh_contract(part, path.parent, DATA)
                if len(header) < 12:
                    raise ValueError('Incomplete source anatomy mesh')
                magic, vertices, indices = struct.unpack('<4sII', header)
                if (magic != b'BP3D' or decoded_size != 12 + vertices * 24 + indices * 4
                        or vertices != part['vertices'] or indices != part['triangles'] * 3
                        or selected['layer'] not in layers):
                    raise ValueError('Invalid source anatomy geometry contract')
    return references


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
    key_images = [image['id'] for image in ref['key_images']]
    images = key_images + [image['id'] for image in ref.get('structure_atlas', [])]
    if len(images) != len(set(images)):
        raise ValueError('Walkthrough figure IDs must be distinct across image collections: ' + item['id'])
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
        for key in ('look', 'tip', 'anatomy_note'):
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
    introduction = authored.get('start', {})
    if not isinstance(introduction, dict):
        raise ValueError('Reporting introduction must be an object: ' + item['id'])
    introductory_images = introduction.get('images', [i for i in key_images if i not in used_images])
    if (not isinstance(introductory_images, list) or any(i not in images for i in introductory_images)
            or len(set(introductory_images)) != len(introductory_images)):
        raise ValueError('Reporting introduction needs distinct registered figures: ' + item['id'])
    module_illustrations = introduction.get('module_illustrations', True)
    if not isinstance(module_illustrations, bool):
        raise ValueError('Reporting introduction illustration choice must be boolean: ' + item['id'])
    return {'reviewed_at': _steps()['reviewed_at'].get(item['id'], guide['reviewed_at']),
            'complete': complete, 'template_id': template['id'],
            'start': {'sections': headings[:first], 'images': introductory_images,
                      **({'module_illustrations': False} if not module_illustrations else {})},
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


@lru_cache(maxsize=1)
def cancer_staging_catalog():
    """Versioned, source-linked oncology reporting tables and original diagrams."""
    catalog = _read('cancer-staging.json')
    date.fromisoformat(catalog['reviewed_at'])
    known = {item['id'] for item in catalogue()['investigations']}
    if not set(catalog['bindings']).issubset(known):
        raise ValueError('Cancer staging assigned to an unknown investigation')
    root = DATA.parents[1] / 'web/reference-media/reporting-diagrams/cancer'
    for identifier, system in catalog['systems'].items():
        if system.get('id') != identifier or system.get('kind') not in {'staging', 'response'}:
            raise ValueError('Invalid cancer staging identity or scope')
        for field in ('title', 'version', 'scope'):
            _text(system.get(field), 'Cancer staging needs ' + field)
        date.fromisoformat(system['reviewed_at'])
        for field in ('tables', 'report_fields', 'limits', 'sources'):
            if not isinstance(system.get(field), list) or not system[field]:
                raise ValueError('Cancer staging needs ' + field)
        for table in system['tables']:
            _text(table.get('title'), 'Staging table needs a title')
            if not table.get('rows'):
                raise ValueError('Staging table needs criteria')
            for row in table['rows']:
                for field in ('category', 'criteria', 'report_note'):
                    _text(row.get(field), 'Staging row needs ' + field)
        for source in system['sources']:
            from .radiology import _source
            _source(source)
        figure = system['illustration']
        if figure['src'] != '/app/reference-media/reporting-diagrams/cancer/' + identifier + '.svg':
            raise ValueError('Cancer staging diagram must use its registered local SVG')
        path = (root / (identifier + '.svg')).resolve()
        if not path.is_relative_to(root.resolve()) or not path.is_file():
            raise ValueError('Missing cancer staging illustration')
        _text(figure.get('alt'), 'Cancer staging diagram needs accessible text')
    for selection in catalog['bindings'].values():
        if (not selection or len(selection) != len(set(selection))
                or not set(selection).issubset(catalog['systems'])):
            raise ValueError('Cancer staging binding needs distinct known systems')
    return catalog


@lru_cache(maxsize=1)
def annotated_anatomy_links():
    """External annotated case references, distinct from licensed local images."""
    from .radiology import _source
    data = _read('annotated-anatomy-links.json')
    known = {item['id'] for item in catalogue()['investigations']}
    if not set(data['bindings']).issubset(known):
        raise ValueError('Annotated anatomy link has an unknown investigation')
    for reference in data['references'].values():
        _source(reference)
        _text(reference.get('reporting_use'), 'Anatomy reference needs its reporting use')
        if reference.get('stack'):
            stack = reference['stack']
            expected = '/app/reference-media/annotated-ct/' + reference['id'] + '.json'
            if stack.get('manifest_url') != expected:
                raise ValueError('Annotated CT stack must use its registered manifest')
            manifest = _read('../../web/reference-media/annotated-ct/' + reference['id'] + '.json')
            frames = manifest.get('frames', [])
            if (len(frames) != stack['frame_count'] or not frames
                    or len({frame['src'] for frame in frames}) != len(frames)
                    or [frame['index'] for frame in frames] != list(range(len(frames)))
                    or manifest['source_url'] != reference['url']):
                raise ValueError('Annotated CT stack identity, count or order differs')
            for frame in frames:
                if not re.fullmatch(r'https://prod-images-static\.radiopaedia\.org/images/[0-9]+/[a-zA-Z0-9]+_big_gallery\.jpeg', frame['source_image_url']):
                    raise ValueError('Annotated CT stack has an unreviewed image host or path')
                expected_frame = '/app/reference-media/annotated-ct/' + reference['id'] + '/' + str(frame['index'] + 1).zfill(3) + '.jpeg'
                if frame['src'] != expected_frame:
                    raise ValueError('Annotated CT stack has an unregistered local frame')
                frame_path = DATA.parents[1] / 'web' / frame['src'].removeprefix('/app/')
                if hashlib.sha256(frame_path.read_bytes()).hexdigest() != frame['sha256']:
                    raise ValueError('Preserved annotated CT frame changed after acquisition')
    return {identifier: [copy.deepcopy(data['references'][key]) for key in selection]
            for identifier, selection in data['bindings'].items()}


def _validate_native_volume_figure(image, root):
    """Validate packaged section provenance without approving clinical anatomy."""
    if (image.get('kind') != 'clinical-image' or image.get('modality') not in {'CT','MRI'}
            or not isinstance(image.get('figure_title'), str) or not image['figure_title'].strip()
            or any(key in image for key in ('figure_number', 'source_panel'))):
        raise ValueError('Native volume figure needs an explicit source section title')
    derivation = image.get('derivation', {})
    prefix = '/app/reference-media/radiology-open/'
    url = derivation.get('evidence_url', '') if isinstance(derivation, dict) else ''
    if not url.startswith(prefix) or '%' in url or '\\' in url:
        raise ValueError('Native section provenance must be preserved locally')
    path = (root / url.removeprefix(prefix)).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise ValueError('Native section provenance leaves source folder')
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != derivation.get('evidence_sha256'):
        raise ValueError('Native section provenance changed')
    evidence = json.loads(raw)
    source = evidence.get('source', {})
    doi = source.get('dataset_doi')
    if image['modality'] != ('MRI' if doi=='10.7937/TCIA.2020.A61IOC1A' else 'CT'):
        raise ValueError('Native section modality differs from its registered source')
    if doi == '10.7937/TCIA.2020.A61IOC1A':
        verified_source = (source.get('data_license')=='CC BY 4.0'
            and source.get('case_id')=='Prostate-MRI-US-Biopsy-0001'
            and source.get('source_role')=='T2'
            and source.get('source_series_UID')=='1.3.6.1.4.1.14519.5.2.1.266717969984343981963002258381778490221'
            and source.get('whole_object_md5_and_scalar_readback_verified') is True
            and source.get('source_MRI_stored_sample_count')==3932160
            and all(re.fullmatch(r'[0-9a-f]{64}',source.get(k,'')) for k in ('source_T2_payload_sha256','source_object_sha256','source_plane_stored_samples_sha256'))
            and evidence.get('source_shape')==[60,256,256]
            and evidence.get('source_dtype')=='<u2'
            and evidence.get('source_sampling_zyx_mm')==[1.5,.6640625,.6640625]
            and evidence.get('source_display_adaptation')=='original_DICOM_LINEAR_VOI_to_8bit'
            and len(evidence.get('planes',[]))==1
            and evidence['planes'][0].get('axis')==0
            and evidence['planes'][0].get('index') in [15,25,35]
            and evidence.get('clinical_approval') is False)
    elif doi == '10.5281/zenodo.10069289':
        verified_source = (source.get('data_license') == 'CC BY 4.0'
            and source.get('mirror_repository') == 'andreped/AeroPath'
            and re.fullmatch(r'[0-9a-f]{40}', source.get('mirror_revision', ''))
            and re.fullmatch(r'[0-9a-f]{64}', source.get('ct_sha256', ''))
            and source.get('per_file_sha256_verified') is True)
    elif doi == '10.7937/K9/TCIA.2015.AQIIDCNM':
        verified_source = (source.get('data_license') == 'CC BY 3.0'
            and source.get('case_id') == 'MED_LYMPH_001'
            and source.get('publisher_per_file_md5_verified') is True
            and source.get('ct_dicom_files') == 666
            and source.get('original_label_pixel_mismatches') == 0
            and source.get('original_acquisition_resolution_verified') is False
            and source.get('conversion_lineage') == 'Analyze/NIfTI to DICOM'
            and evidence.get('source_shape') == [512, 512, 666]
            and type(evidence.get('source_label')) is int
            and evidence.get('source_label') in (1, 2, 3)
            and evidence.get('annotation_geometry_overlaid') is False
            and all(re.fullmatch(r'[0-9a-f]{64}', source.get(k, '')) for k in
                    ('ct_archive_sha256', 'original_mask_sha256', 'native_review_sha256')))
    elif doi == '10.7937/K9/TCIA.2018.SC20FO18':
        pancreatic_sources = {
            'arterial-labelled': (365, 1, '114104.584535',
                'e228860b6eecf4c8ea8912112285832b380598d20c9c05ea7949772ff7df3b6c',
                'caed65d16998a757267c661db41afb7788e15197a0645bb8c51921bec4b374b5', [154, 245, 201]),
            'venous-labelled': (713, 2, '114147.324919',
                '1c262fc56cb4b8d763ad28d3275a12db46f5ed4da6dabe937e629f5582b6891c',
                'bf751cd33c964ab7ca146f186171272760d3d70657f70aae717627b3f7ef6f28', [511, 243, 199]),
        }
        role = source.get('source_role')
        expected = pancreatic_sources.get(role) if isinstance(role, str) else None
        verified_source = (expected is not None
            and image.get('id') == 'native-cptac-c3l02112-' + role + '-ct'
            and source.get('data_license') == 'CC BY 4.0'
            and source.get('case_id') == 'C3L-02112'
            and source.get('annotation_doi') == '10.7937/BW9V-BX61'
            and source.get('publisher_per_file_md5_verified') is True
            and source.get('ct_dicom_files') == expected[0]
            and source.get('selected_acquisition_number') == expected[1]
            and source.get('source_acquisition_time') == expected[2]
            and source.get('ct_archive_sha256') == expected[3]
            and source.get('annotation_archive_sha256') == expected[4]
            and source.get('source_selection_sha256') == '17ee2ba3d4e227ca5ce588ed54eecd3c887840474397731c8d6e64b053332442'
            and source.get('original_geometry_review_sha256') == 'ce923ffa19f53a83692c6c87299b65df1839d0784c7f1d4bc27b3252f49d5e63'
            and source.get('native_section_review_sha256') == '63eb7b9635d908347535df547aba94f0f18a11f944b4f1521e9d0bf33c50b15d'
            and evidence.get('source_shape') == [expected[0], 512, 512]
            and evidence.get('source_sampling_zyx_mm') == [.625, .703125, .703125]
            and evidence.get('source_slice_thickness_mm') == .625
            and evidence.get('declared_spacing_between_slices_mm') == -.625
            and evidence.get('observed_interplane_step_mm') == .625
            and evidence.get('original_instance_order_signed_steps_mm') == [-.625, -.625]
            and isinstance(evidence.get('planes'), list)
            and all(isinstance(p, dict) for p in evidence['planes'])
            and [(p.get('axis'), p.get('index')) for p in evidence['planes']] == list(enumerate(expected[5]))
            and evidence.get('annotation_is_location_aid_only') is True
            and evidence.get('runtime_reference_only') is True
            and all(evidence.get(key) is False for key in ('source_acquisitions_interleaved_or_deduplicated',
                'cross_acquisition_registration', 'annotation_geometry_overlaid', 'named_phase_verified',
                'histological_diagnosis_verified', 'complete_pancreatic_anatomy_verified',
                'source_annotation_is_whole_pancreas', 'tracking_identity_reconciled', 'source_volume_and_end_extent_reconciled')))
    elif doi == '10.7937/K9/TCIA.2018.OBLAMN27':
        verified_source = (source.get('data_license') == 'CC BY 4.0'
            and source.get('case_id') == 'C3N-03018'
            and source.get('publisher_per_file_md5_verified') is True
            and source.get('ct_dicom_files') == 850
            and source.get('selected_acquisition_number') == 1
            and source.get('selected_acquisition_dicom_files') == 417
            and source.get('other_acquisition_dicom_files') == 433
            and source.get('ct_archive_sha256') == 'a9ab6c3999aa6d852db6a420dbad6a396cb7d2d3abf0bc3af9df946cbf5bf339'
            and source.get('original_geometry_review_sha256') == '8044c9ac249121d65f09fd7d9988f60c277b6ea30f680f9a4ccb276fb68e9144'
            and source.get('source_selection_sha256') == '7bdd465bf39303a2b3bb471067ecd172febac79de40b8dfa9924708e9145f82b'
            and evidence.get('source_shape') == [417, 512, 512]
            and evidence.get('source_sampling_zyx_mm') == [0.625, 0.976562, 0.976562]
            and evidence.get('source_slice_thickness_mm') == 0.625
            and evidence.get('declared_spacing_between_slices_mm') == 2.5
            and evidence.get('observed_interplane_step_mm') == 0.625
            and evidence.get('source_acquisitions_interleaved_or_deduplicated') is False
            and evidence.get('annotation_geometry_overlaid') is False
            and all(evidence.get(key) is False for key in ('named_phase_verified',
                'histological_diagnosis_verified', 'complete_renal_anatomy_verified',
                'source_annotation_is_whole_kidney', 'source_volume_and_end_extent_reconciled')))
    else:
        verified_source = False
    if not verified_source or source.get('data_license') != image.get('license'):
        raise ValueError('Native source identity or licence is unverified')
    if (evidence.get('figure_sha256') != image['sha256']
            or evidence.get('clinical_approval') is not False
            or evidence.get('source_voxels_changed') is not False
            or evidence.get('model_geometry_overlaid') is not False):
        raise ValueError('Native figure scope or byte contract changed')
    pixels = verified_raster_header(image, root, DATA)
    if (len(pixels) < 24 or pixels[:8] != b'\x89PNG\r\n\x1a\n'
            or struct.unpack('>II', pixels[16:24]) != (image['width'], image['height'])):
        raise ValueError('Native section figure dimensions changed')
    shape = evidence.get('source_shape')
    planes = evidence.get('planes')
    if (not isinstance(shape, list) or len(shape) != 3
            or any(type(n) is not int or n <= 0 for n in shape)
            or not isinstance(planes, list) or not planes):
        raise ValueError('Native section source shape/planes are missing')
    for plane in planes:
        axis, index = plane.get('axis'), plane.get('index')
        if (type(axis) is not int or axis not in (0, 1, 2) or type(index) is not int
                or not 0 <= index < shape[axis] or plane.get('source_resampling') is not False):
            raise ValueError('Native section plane is invalid or resampled')


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


def _validate_source_panel_roles(image):
    """Reject contradictions in declared source roles, without inferring missing panels or approval."""
    if (image.get('kind') == 'schematic') != (image.get('modality') == 'Schematic'):
        raise ValueError('Source figure kind and schematic modality disagree')
    context = image.get('source_context', {})
    if not isinstance(context, dict):
        raise ValueError('Source figure context must be a record')
    if not any(key in context for key in ('selected_panels', 'panel_types', 'panel_states')):
        return
    selected, types = context.get('selected_panels'), context.get('panel_types')
    if (not isinstance(selected, list) or not isinstance(types, dict)
            or any(not isinstance(panel, str) or not panel.strip() for panel in selected)
            or len(set(selected)) != len(selected)):
        raise ValueError('Source figure panel selection must be explicit and unique')
    primary_field = ('schematic_panels' if image.get('kind') == 'schematic'
                     and 'schematic_panels' in image else 'clinical_panels')
    declared = image.get(primary_field)
    if (primary_field in image and (not isinstance(declared, list)
            or any(not isinstance(panel, str) or not panel.strip() for panel in declared)
            or len(set(declared)) != len(declared)
            or set(declared) != set(selected))):
        raise ValueError('Source figure selected panels disagree with the displayed primary selection')
    if any(types.get(panel) != image.get('modality') for panel in selected):
        raise ValueError('Source figure selected panel type disagrees with the displayed modality')
    occupied = set(selected)
    ancillary = image.get('ancillary_panels', [])
    if not isinstance(ancillary, list):
        raise ValueError('Source ancillary panel roles must be records')
    for entry in ancillary:
        if not isinstance(entry, dict) or not isinstance(entry.get('panels'), list):
            raise ValueError('Source ancillary panel selection must be explicit')
        panels = entry['panels']
        if (not panels or any(not isinstance(panel, str) or not panel.strip() for panel in panels)
                or len(set(panels)) != len(panels)
                or occupied.intersection(panels)
                or any(types.get(panel) != entry.get('kind') for panel in panels)):
            raise ValueError('Source ancillary panel roles overlap or contradict the declared source types')
        occupied.update(panels)
    if image.get('panel_identifier_scheme') == 'descriptive_source_positions':
        if (not types or len(types) > 32
                or context.get('panel_identifier_scheme') != 'descriptive_source_positions'
                or any(not isinstance(panel, str)
                       or not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]{0,63}', panel)
                       for panel in types)):
            raise ValueError('Descriptive source positions need explicit complete panel roles')
        schematics = image.get('schematic_panels', [])
        if (not isinstance(schematics, list)
                or any(not isinstance(panel, str) or types.get(panel) != 'Schematic'
                       for panel in schematics)
                or len(schematics) != len(set(schematics))
                or occupied.intersection(schematics)):
            raise ValueError('Descriptive source schematic roles overlap or contradict source types')
        occupied.update(schematics)
        if occupied != set(types):
            raise ValueError('Descriptive source positions must partition every source role')


@lru_cache(maxsize=1)
def _structure_atlases():
    """Locally preserved, licensed figures with narrowly stated anatomy scope."""
    catalog = copy.deepcopy(_read('msk-open-images.json', {}))
    for identifier, figures in _read('radiology-open-images.json', {}).items():
        if not isinstance(figures, list):
            raise ValueError('Source atlas figures must be a list')
        catalog.setdefault(identifier, []).extend(figures)
    known = {item['id'] for item in catalogue()['investigations']}
    topics = {item['id']: item['topic'] for item in catalogue()['investigations']}
    if not set(catalog).issubset(known):
        raise ValueError('MSK atlas figure has no matching investigation')
    media = (DATA.parents[1] / 'web/reference-media').resolve()
    seen = set()
    for images in catalog.values():
        for image in images:
            if image['id'] in seen or image.get('kind') not in {'clinical-image', 'schematic'}:
                raise ValueError('Invalid or duplicated MSK atlas figure')
            if image.get('modality') not in {'MRI', 'MR arthrography', 'CT', 'CT arthrography', 'Ultrasound', 'Radiography', 'Nuclear medicine', 'Histology', 'Schematic'}:
                raise ValueError('MSK atlas figure needs its actual source modality')
            _validate_source_panel_roles(image)
            if 'source_panel' in image and image['source_panel'] not in tuple('abcdefABCDEF'):
                raise ValueError('MSK source panel needs an explicit publication panel identifier')
            if image.get('contains_schematic_panels'):
                if image['contains_schematic_panels'] is not True or not image.get('schematic_structures_visible'):
                    raise ValueError('Mixed MSK figures need separate schematic coverage')
            ancillary = image.get('ancillary_panels', [])
            position_panels = image.get('panel_identifier_scheme') == 'position_unlettered'
            grid_panels = image.get('panel_identifier_scheme') == 'grid_unlettered'
            descriptive_panels = image.get('panel_identifier_scheme') == 'descriptive_source_positions'
            grid_positions = set()
            descriptive_positions = set()
            if descriptive_panels:
                descriptive_positions = set(image['source_context']['panel_types'])
            if grid_panels:
                context = image.get('source_context', {})
                rows, columns = context.get('panel_grid_rows'), context.get('panel_grid_columns')
                if (type(rows) is not int or type(columns) is not int or min(rows, columns) < 1
                        or rows * columns > 64 or context.get('panel_identifier_scheme') != 'grid_unlettered'):
                    raise ValueError('Unlettered grid needs explicit source dimensions')
                grid_positions = {f'r{r}c{c}' for r in range(1, rows + 1) for c in range(1, columns + 1)}
                if set(context.get('panel_types', {})) != grid_positions:
                    raise ValueError('Unlettered grid needs every original panel role')
            if position_panels:
                context = image.get('source_context', {})
                types = context.get('panel_types', {}) if isinstance(context, dict) else {}
                if (not isinstance(context, dict) or not isinstance(types, dict)
                        or context.get('panel_identifier_scheme') != 'position_unlettered'
                        or set(types) != {'left', 'middle', 'right'}
                        or not image.get('clinical_panels')
                        or any(types.get(p) != image['modality'] for p in image.get('clinical_panels', []))):
                    raise ValueError('Unlettered positions need explicit source modality roles')
            if image.get('source_background') not in (None, 'white'):
                raise ValueError('Source background must use the reviewed paper colour')
            if not isinstance(ancillary, list):
                raise ValueError('Ancillary anatomical panels must be explicit records')
            for entry in ancillary:
                if (not isinstance(entry, dict) or entry.get('kind') not in {'Dissection', 'Histology', 'Endoscopy', 'Ultrasound', 'MRI', 'CT', 'PET-CT', 'Radiography', 'Nuclear medicine', 'Haemodynamic tracing', 'Anatomical specimen photograph', 'Clinical photograph', 'Segmentation mask', 'Masked ultrasound', 'Masked histology', 'MRI-derived plot', 'Ultrasound-derived display'}
                        or entry.get('kind') == image.get('modality')
                        or not isinstance(entry.get('panels'), list) or not entry['panels']
                        or any(not isinstance(panel, str) or
                               (panel not in descriptive_positions if descriptive_panels else panel not in grid_positions if grid_panels else panel not in {'left', 'middle', 'right'} if position_panels else
                                len(panel) != 1 or panel not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ')
                               for panel in entry['panels'])
                        or not isinstance(entry.get('structures_visible'), list) or not entry['structures_visible']
                        or any(not isinstance(name, str) or not name.strip() for name in entry['structures_visible'])
                        or not isinstance(entry.get('limits'), str)
                        or not entry['limits'].strip()
                        or (position_panels and any(types.get(p) != entry.get('kind') for p in entry['panels']))):
                    raise ValueError('Ancillary panels need distinct types, observations and limits')
            seen.add(image['id'])
            prefix = next((p for p in ('/app/reference-media/msk-open/', '/app/reference-media/radiology-open/')
                           if image['src'].startswith(p)), None)
            if prefix is None:
                raise ValueError('MSK atlas figures must be preserved locally')
            root = media / prefix.rstrip('/').rsplit('/',1)[1]
            verified_raster_header(image, root, DATA)
            # Preserve the source's actual version. Aubry's 2010 hip figures
            # use CC BY 2.0; their grant must not be relabelled as CC BY 4.0.
            reviewed_licenses = {
                'CC BY 2.0': 'https://creativecommons.org/licenses/by/2.0/',
                'CC BY 3.0': 'https://creativecommons.org/licenses/by/3.0/',
                'CC BY 4.0': 'https://creativecommons.org/licenses/by/4.0/',
                'CC BY-ND 4.0': 'https://creativecommons.org/licenses/by-nd/4.0/',
                'CC BY-SA 3.0 Unported': 'https://creativecommons.org/licenses/by-sa/3.0/',
            }
            if (image.get('license') not in reviewed_licenses
                    or image.get('license_url') != reviewed_licenses[image['license']]):
                raise ValueError('MSK atlas figure needs a reviewed commercial-use license')
            if image.get('origin') == 'native-volume-sections':
                _validate_native_volume_figure(image, root)
            elif image.get('origin') == 'source-derived':
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
                        or not isinstance(image.get('source_bytes_md5'), str)
                        or not re.fullmatch(r'[0-9a-f]{32}', image['source_bytes_md5'])):
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
    if identifier == 'ra.hrct-cystic-lung':
        identifier = 'ra.hrct-lung'
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


def reporting_image(image):
    """Keep diagnostic images and teaching diagrams out of research-figure clutter.

    Preserve original source records/bytes for provenance; exclude whole mixed
    figures rather than silently cropping licensed publisher panels.
    """
    if image.get('origin') == 'source-derived':
        return False
    excluded = ('dissection', 'histology', 'photograph', 'specimen', 'experimental')
    if any(any(term in panel.get('kind', '').lower() for term in excluded)
           for panel in image.get('ancillary_panels', [])):
        return False
    description = ' '.join(str(image.get(key, '')) for key in
                           ('caption', 'alt', 'title', 'source_url')).lower()
    return not any(term in description for term in
                   ('synchrotron', 'phase-contrast tomography', 's41597-022-01353',
                    'micro-ct', 'microct', 'experimental setup'))


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
    walkthrough_model = _step_model(item, _steps()['investigations'].get(item['id'], {})) or copy.deepcopy(ref['spatial_model'])
    model_binding = _read('investigation-model-bindings.json', {}).get(item['id'])
    has_source_binding = bool(model_binding)
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
        if model_binding.get('reporting_aim'):
            aim = _text(model_binding['reporting_aim'], 'Source anatomy needs an explicit reporting aim')
            ref['spatial_model'].update(reporting_aim=aim, instructions='Drag to rotate and inspect the native anatomy. ' + aim)
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
    ref['source_anatomy_references'] = copy.deepcopy(_source_anatomy_references().get(item['id'], []))
    ref['source_motion_references'] = copy.deepcopy(_source_motion_references().get(item['id'], []))
    ref['source_study_references'] = copy.deepcopy(_source_study_references().get(item['id'], []))
    ref['annotated_anatomy_links'] = copy.deepcopy(annotated_anatomy_links().get(item['id'], []))
    ref['investigation'] = copy.deepcopy(item)
    if item['id'] == 'ra.hrct-lung':
        ref['quick_reference'] = _read('hrct-quick-reference.json')
    if item['module_id'] == 'rad.5.aorta':
        ref['reporting_diagrams'] = _read('aortic-reporting-diagrams.json')
    cancer = cancer_staging_catalog()
    if item['id'] in cancer['bindings']:
        ref['cancer_staging'] = [copy.deepcopy(cancer['systems'][key])
                                 for key in cancer['bindings'][item['id']]]
        ref['cancer_staging_reviewed_at'] = cancer['reviewed_at']
    corrected = _step_model(item, _steps()['investigations'].get(item['id'], {}))
    if corrected and not has_source_binding:
        ref['spatial_model'] = corrected
    ref['spatial_model']['title'] = item['title'] + ' · spatial orientation'
    if not override.get('report_templates'):
        for template in ref['report_templates']:
            template['title'] = item['title'].upper()
    # Readings and clinical figure captions are specific to the investigation.
    # Preserve the underlying diagram/model until a source mesh is available.
    validate_reference(ref)
    ref['walkthrough'] = _walkthrough(item, dict(ref, spatial_model=walkthrough_model))
    ref['walkthrough']['spatial_model'] = walkthrough_model
    for collection in ('key_images', 'structure_atlas'):
        ref[collection] = [image for image in ref[collection] if reporting_image(image)]
    visible = {image['id'] for key in ('key_images', 'structure_atlas') for image in ref[key]}
    for step in [ref['walkthrough']['start'], *ref['walkthrough']['steps']]:
        step['images'] = [identifier for identifier in step['images'] if identifier in visible]
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
                *[system['title'] for system in reference.get('cancer_staging', [])],
                *({'Musculoskeletal': ['MSK'], 'Head/Neck': ['ENT'], 'Pediatrics': ['paediatric', 'pediatric']}.get(item['section'], [])),
                *({'ra.ct-coronary': ['CCTA', 'CTCA'], 'ra.mri-prostate': ['mpMRI', 'PI-RADS']}.get(item['id'], []))])),
            'image_count': len(reference['key_images']) + len(reference.get('structure_atlas', []))
                + sum(bool(source.get('source_image')) for source in reference.get('source_anatomy_references', [])),
            'motion_count': len(reference.get('source_motion_references',[])),
            'template_count': len(reference['report_templates']),
            'classification': classification['name'] if classification else '',
            'staging_systems': [system['title'] for system in reference.get('cancer_staging', [])],
            'model_family': reference['spatial_model']['family'],
            'step_count': len(reference['walkthrough']['steps']),
            'reviewed_at': reference['reporting']['reviewed_at'],
        })
    return {'modules': modules, 'count': len(modules), 'foundation': catalogue()['foundation_url']}
