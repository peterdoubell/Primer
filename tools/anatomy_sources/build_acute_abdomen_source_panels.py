"""Generate reviewed panel links and partial candidates for the acute-abdomen report.

All outputs live at fixed paths in this checkout. The review is a source/target
correspondence record, not clinical approval or an anatomical completeness claim.
"""
from collections import defaultdict
import copy
import hashlib
import gzip
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlencode

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.check_msk_fidelity import inspect_binding, requirements_for
from tools.anatomy_sources import bind_stored_caption_assets_pass2 as stored
from tools.anatomy_sources import bind_reader_models as models

REVIEW = Path('docs/acute-abdomen-source-panels/review.json')
EVIDENCE = Path('data/radiology/radiology-asset-evidence.json')
MANIFEST = Path('web/radiology/acute-abdomen-panels/data.json')
LOCATOR = Path('web/radiology/structure-atlas/locators/acute-abdomen.json')
INDEX = Path('web/radiology/structure-atlas/index.json')
READER = '/app/radiology/acute-abdomen-panels/index.html'
EXAM = 'ra.acute-abdomen'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def reader_url(**selection):
    return READER + '?' + urlencode(selection)


def build(root=ROOT):
    review_bytes = (root / REVIEW).read_bytes()
    review = json.loads(review_bytes)
    inventory = json.loads((root / 'data/radiology/non-msk-structure-requirements.json').read_bytes())
    investigation, = [row for row in inventory['investigations'] if row['investigation_id'] == EXAM]
    scope = dict(inventory_context={key: inventory.get(key) for key in ('schema_version', 'purpose', 'conventions')}, investigation=investigation)
    if sha(json.dumps(scope, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()) != review['investigation_definition_sha256']:
        raise ValueError('Reviewed acute-abdomen requirement definitions changed')
    leaves = {row['id']: row for row in requirements_for(investigation)}
    parents = {row['id']: row for row in investigation['structures']}
    evidence = json.loads((root / EVIDENCE).read_bytes())
    assets = {row['id']: row for row in evidence['assets']}
    figures = {row['id']: row for row in json.loads((root / 'data/radiology/radiology-open-images.json').read_text())[EXAM]}
    if len(figures) != 12 or len(review['figures']) != 12 or len(review['panels']) != 17:
        raise ValueError('Expected the twelve preserved source figures and seventeen original panels')
    runtime_figures = []
    for row in review['figures']:
        figure = figures[row['id']]
        path = root / 'web' / figure['src'].removeprefix('/app/')
        if sha(path.read_bytes()) != figure['sha256']:
            raise ValueError('Original figure bytes changed')
        if sha((root / row['caption_evidence']).read_bytes()) != row['caption_evidence_sha256']:
            raise ValueError('Full-caption evidence changed')
        fields = ('id', 'src', 'sha256', 'width', 'height', 'figure_number', 'modality', 'caption',
                  'limits', 'source_url', 'figure_url', 'license', 'license_url', 'attribution')
        runtime_figures.append({**{key: figure[key] for key in fields},
                                'caption_full': row['caption_full'], 'case_group': row['case_group'],
                                'default_panel': row['default_panel'], 'source_context': figure['source_context']})
    panels = copy.deepcopy(review['panels'])
    changes = defaultdict(lambda: {'structure_ids': [], 'requirement_coverage': {}, 'corrected': {}})
    by_target = defaultdict(list)
    grouped_basis = defaultdict(list)
    for panel in panels:
        figure = figures[panel['figure_id']]
        asset = assets[panel['figure_id']]
        x, y, w, h = panel['panel_bounds']
        if (min(x, y) < 0 or min(w, h) <= 0 or x + w > figure['width'] or y + h > figure['height']):
            raise ValueError('A panel rectangle leaves its complete original figure')
        types = figure['source_context'].get('panel_types') or {'whole': figure['modality']}
        panel['modality'] = types[panel['source_panel']]
        selected = figure['source_context'].get('selected_panels') or ['whole']
        if panel['bindings'] and (panel['source_panel'] not in selected or panel['modality'] != asset['modality']):
            raise ValueError('A panel cannot borrow another panel’s modality or selection')
        for binding in panel['bindings']:
            target = leaves[binding['target_id']]
            if binding['extent'] != 'partial' or inspect_binding(asset, target):
                raise ValueError('Source/target context conflict: ' + binding['target_id'])
            grouped_basis[(asset['id'], target['id'])].append(
                'Source panel ' + panel['source_panel'] + ': ' + binding['basis'])
            by_target[target['id']].append(dict(panel_id=panel['id'], kind='clinical_image',
                label='Figure ' + str(figure['figure_number']) + ' ' + panel['source_panel'] + ' · ' + panel['modality'],
                figure_id=figure['id'], url=reader_url(target=target['id'], panel=panel['id'])))
        for target in panel['context_targets']:
            if target not in leaves:
                raise ValueError('Unknown contextual target')
    for (identifier, target), bases in grouped_basis.items():
        changes[identifier]['structure_ids'].append(target)
        changes[identifier]['requirement_coverage'][target] = dict(extent='partial', basis=' '.join(bases)
            + ' Source correspondence reviewed in docs/acute-abdomen-source-panels/review.json; anatomical and clinical review remain pending.')
    native = []
    records = []
    for row in review['native_references']:
        original = assets[row['original_asset_id']]
        target = leaves[row['target_id']]
        if original['kind'] != 'model' or inspect_binding(original, target):
            raise ValueError('Native model/target context conflict')
        if sha((root / original['local_path']).read_bytes()) != original['sha256']:
            raise ValueError('Native source mesh bytes changed')
        identifier = 'acute-abdomen-' + row['id']
        record = copy.deepcopy(original)
        record.update(id=identifier, investigation_ids=[EXAM], structure_ids=[target['id']],
                      requirement_coverage={target['id']: dict(extent='partial', basis=row['basis'])})
        record['source_reuse'] = dict(original_asset_id=original['id'], same_physical_file=True,
                                     source_pixels_or_context_changed=False, shared_patient_or_exam_inferred=False,
                                     inherited_requirement_coverage=False)
        records.append(record)
        native.append(dict(id=row['id'], target_id=target['id'], reader_url=row['reader_url'],
            name=original['name'], source_url=original['source']['url'], license=original['source']['license']['name'],
            license_url=original['source']['license']['url'], attribution=original['source']['license']['attribution'],
            limits=row['basis'], mesh_path='/' + original['local_path'].replace('web/', 'app/', 1),
            mesh_sha256=original['sha256'], kind='model', case_group='ColonVessels-pat_012-separate-case'))
        by_target[target['id']].append(dict(panel_id=row['id'], kind='model', label=review['target_labels'][target['id']],
            url=reader_url(target=target['id'], panel=row['id'])))
    targets = []
    for identifier, examples in by_target.items():
        leaf = leaves[identifier]
        targets.append(dict(id=identifier, label=review['target_labels'][identifier], parent_id=leaf['parent_id'],
            parent_name=parents[leaf['parent_id']]['name'], part_name=leaf['name'], report_refs=leaf['report_refs'],
            modality_scope=leaf['modality_scope'], examples=examples, coverage_extent='partial'))
    descriptors = root / 'data/radiology/descriptor-reporting.json.gz'
    forms = json.loads(gzip.decompress(descriptors.read_bytes())) if descriptors.is_file() else json.loads(descriptors.with_suffix('').read_text())
    report, = [row for form in forms['forms'].values() for row in form['investigations'] if row['id'] == EXAM]
    report_sections = {row['id']: row for row in report['sections']}
    panel_map = {row['id']: row for row in panels}
    for row in review['report_rows']:
        source = report_sections[row['id']]
        snapshot = {key: source.get(key) for key in ('id', 'label', 'group', 'normal', 'findings')}
        if sha(json.dumps(snapshot, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()) != row['report_row_sha256']:
            raise ValueError('Original professional report row changed: ' + row['id'])
        if not row['panels'] or any(not any(binding['target_id'] == row['target_id'] for binding in panel_map[panel]['bindings']) for panel in row['panels']):
            raise ValueError('A report row points to a panel without its reviewed target')
    runtime = dict(schema_version=1, investigation_id=EXAM, title='Acute abdomen: source panels and report targets',
        clinical_approval=False, requirement_completion_granted=False,
        source_cases_registered_to_each_other=False, review_path=str(REVIEW), review_sha256=sha(review_bytes),
        inventory_counts=dict(parent_structures=len(parents), required_leaves=len(leaves)),
        figures=runtime_figures, panels=panels, native_references=native, targets=targets,
        report_rows=review['report_rows'], limits=review['limits'])
    return runtime, dict(changes), records


def refresh(root=ROOT):
    runtime, changes, records = build(root)
    (root / MANIFEST).write_text(json.dumps(runtime, indent=2, ensure_ascii=False) + '\n')
    script = root / 'web/radiology/acute-abdomen-panels/lab.js'
    if script.is_file():
        content, count = re.subn(r"const DATA_SHA = '[^']+';", "const DATA_SHA = '" + sha((root / MANIFEST).read_bytes()) + "';", script.read_text())
        if count != 1:
            raise ValueError('Source reader manifest pin is missing or duplicated')
        script.write_text(content)
    builder = root / 'web/radiology-structured.js'
    row_links = {row['id']: dict(target=row['target_id'], label=row['link_label']) for row in runtime['report_rows']}
    content, count = re.subn(r'  const ACUTE_SOURCE_ROWS = .*?;\n', '  const ACUTE_SOURCE_ROWS = ' + json.dumps(row_links, ensure_ascii=False) + ';\n', builder.read_text())
    if count != 1:
        raise ValueError('Professional report-row source registry is missing or duplicated')
    builder.write_text(content)
    raw = (root / EVIDENCE).read_bytes()
    # Existing source assets retain every claim except the separately reviewed new bindings.
    data = json.loads(raw)
    existing = {row['id']: row for row in data['assets']}
    for identifier, change in changes.items():
        old = existing[identifier]
        for target, entry in change['requirement_coverage'].items():
            if target in old['requirement_coverage'] and old['requirement_coverage'][target] != entry:
                raise ValueError('An existing reviewed binding differs: ' + identifier + ' / ' + target)
        change['structure_ids'] = [identifier for identifier in change['structure_ids'] if identifier not in old['structure_ids']]
    current = {row['id'] for row in data['assets']}
    after, _ = stored.apply(raw, changes)
    additions = [row for row in records if row['id'] not in current]
    if any(row['id'] in existing and existing[row['id']] != row for row in records):
        raise ValueError('An existing native reference record differs')
    if additions:
        after, _ = models.apply(after, additions)
    (root / EVIDENCE).write_bytes(after)
    locator = json.loads((root / LOCATOR).read_text())
    by_parent = defaultdict(list)
    for target in runtime['targets']:
        for example in target['examples']:
            by_parent[target['parent_id']].append(dict(target_id=target['id'], target_name=target['label'], **example))
    for row in locator['structures']:
        if row['id'] in by_parent:
            row['source_panels'] = by_parent[row['id']]
        else:
            row.pop('source_panels', None)
    locator['source_panel_rows'] = len(by_parent)
    locator['source_panel_note'] = 'Selected licensed image panels and separate source-labelled vessel models. All matches are partial source examples; full anatomy and clinical approval remain open.'
    (root / LOCATOR).write_text(json.dumps(locator, indent=1, sort_keys=True, ensure_ascii=True) + '\n')
    index = json.loads((root / INDEX).read_text())
    entry, = [row for row in index['investigations'] if row['investigation_id'] == EXAM]
    entry['source_panel_rows'] = len(by_parent)
    entry['located_structures'] = sum(bool(row.get('atlas') or row.get('radiology_assistant') or row.get('source_panels'))
                                      for row in locator['structures'])
    (root / INDEX).write_text(json.dumps(index, indent=1, sort_keys=True, ensure_ascii=True) + '\n')
    return runtime


if __name__ == '__main__':
    result = refresh()
    print(len(result['figures']), 'original figures;', len(result['panels']), 'panels;',
          len(result['targets']), 'partial target examples;', len(result['native_references']), 'separate native vessel references')
