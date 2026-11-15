"""Society-sourced cardiology reporting references in the radiology workbench."""
import copy
import json
from functools import lru_cache

from .radiology import DATA, _source, validate_reference, validate_reporting_guide


@lru_cache(maxsize=1)
def investigations():
    data = json.loads((DATA / 'cardiology-investigations.json').read_text(encoding='utf-8'))
    records = data['investigations']
    identifiers = [item['id'] for item in records]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError('Duplicate cardiology investigation')
    for item in records:
        if not item['id'].startswith('cardiology.') or item['module_id'] != item['id']:
            raise ValueError('Cardiology reference must have its own identity')
        if item['section'] != 'Cardiovascular' or item['source_titles'] != [s['title'] for s in item['reporting']['sources']]:
            raise ValueError('Cardiology heading or source mismatch')
        validate_reporting_guide(item['reporting'])
        for source in item['reporting']['sources']:
            _source(source)
        if [s['heading'] for s in item['steps']] != [s['heading'] for s in item['reporting']['template_sections']]:
            raise ValueError('Cardiology steps must cover every finding section in order')
        assigned = [name for step in item['steps'] for name in step['measurements']]
        if sorted(assigned) != sorted(row['name'] for row in item['reporting']['measurements']):
            raise ValueError('Cardiology measurements must belong to exactly one step')
    return records


def detail(item):
    # Independent content: do not inherit CT/MRI protocols or source images.
    from .radiology_catalog import _template
    item = copy.deepcopy(item)
    guide = item['reporting']
    template = _template(item, guide, {})
    model = {'id': 'radiology-model-' + item['id'], 'title': item['title'] + ' · orientation',
             'scenario': 'radiology-investigation:' + item['id'], 'family': item['family'],
             'focus': [item['focus']],
             'instructions': 'Rotate the reference anatomy and select landmarks. This orientation model does not simulate the examination or intervention.',
             'reporting_aim': 'Relate cardiac structures to the reporting sequence.'}
    steps = [{'label': row['label'], 'detail': row['detail'], 'sections': [row['heading']],
              'normal': {}, 'findings': row['findings'], 'images': [], 'measurements': row['measurements'],
              'landmark': row['landmark'], 'parts': [], 'look': row['look'], 'tip': row['tip']}
             for row in item['steps']]
    diagram_id = 'coronary-tree' if item['family'] == 'coronary' else 'echo-sequence'
    diagram = {'title': 'Coronary territories' if item['family'] == 'coronary' else 'Adult TTE review sequence',
               'src': '/app/reference-media/cardiology/' + diagram_id + '.svg',
               'alt': 'Original schematic for ' + item['title'] + '; not a patient image or procedural simulation.',
               'caption': 'Original educational schematic. Review clinical acquisitions at their source; this diagram does not show a patient examination.',
               'source': guide['sources'][0]}
    ref = {'overview': item['summary'], 'reviewed_at': guide['reviewed_at'],
           'source_label': item['source_label'], 'reading': guide['sources'],
           'supplementary': True, 'additional_sources': [],
           'learning_points': [row['detail'] for row in item['steps']],
           'report_templates': [template], 'reporting': guide, 'spatial_model': model,
           'key_images': [], 'structure_atlas': [], 'source_anatomy_references': [],
           'annotated_anatomy_links': [], 'reporting_diagrams': [diagram],
           'investigation': {key: item[key] for key in ('id', 'module_id', 'title')},
           'walkthrough': {'reviewed_at': guide['reviewed_at'], 'complete': True,
                           'template_id': template['id'], 'spatial_model': model,
                           'start': {'sections': [row['heading'] for row in template['sections'][:4]],
                                     'images': [], 'module_illustrations': False},
                           'steps': steps,
                           'finish': {'sections': [row['heading'] for row in template['sections'][-2:]]}}}
    validate_reference(ref)
    return {**{key: item[key] for key in ('id', 'module_id', 'title', 'section', 'topic', 'modality', 'source_titles', 'source_label')},
            'goal': item['summary'], 'radiology_reference': ref, 'lesson_media': []}
