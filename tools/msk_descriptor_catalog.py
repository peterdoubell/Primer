"""Compile independently authored anatomical report controls with provenance."""
import copy
import json
from pathlib import Path


def apply_anatomic_reports(forms, root, compile_statement, digest, slug):
    coverage = []
    changed = set()
    paths = sorted({* (root / 'data/radiology').glob('msk-anatomic-*.json'),
                    * (root / 'data/radiology').glob('anatomic-*.json')})
    for path in paths:
        authored = json.loads(path.read_text())
        sources = {source['id']: source for source in authored['sources']}
        for identifier, definition in authored['investigations'].items():
            guide_id = definition['guide_id']
            if guide_id not in forms:
                raise ValueError(f'Unknown anatomical report guide: {guide_id}')
            form = forms[guide_id]
            if definition.get('calculator_ids'):
                form['calculator_ids'] = list(dict.fromkeys(form.get('calculator_ids', []) + definition['calculator_ids']))
            # The imported source catalogue is immutable; authored references
            # belong to the compiled form, not the caller's guide dictionary.
            form['sources'] = copy.deepcopy(form['sources'])
            structure_ids = {row['id'] for row in definition['sections']}
            seen = set()
            sections = []
            for position, row in enumerate(definition['sections']):
                if row['id'] in seen:
                    raise ValueError(f'Duplicate anatomy: {identifier}/{row["id"]}')
                seen.add(row['id'])
                section_id = 'anatomy-' + row['id']
                local_ids = {finding['id'] for finding in row['findings']}
                if len(local_ids) != len(row['findings']):
                    raise ValueError(f'Duplicate finding: {identifier}/{row["id"]}')
                references = row.get('source_ids', [])
                if not references or any(key not in sources for key in references):
                    raise ValueError(f'Missing anatomy references: {identifier}/{row["id"]}')
                provenance = {
                    'source_file': str(path.relative_to(root)), 'source_kind': 'curated-anatomic-report',
                    'investigation_id': identifier, 'step_index': position,
                    'reviewed_at': authored['version'], 'source_ids': references,
                    'reference_ids': [path.stem + ':' + key for key in references],
                    'clinical_approval': False,
                }
                form.setdefault('anatomic_sources', {}).update({path.stem + ':' + key:sources[key] for key in references})
                def compile_one(item, kind):
                    result = compile_statement(item['text'], kind=kind, label=item['label'], source=provenance)
                    result['id'] = identifier + ':' + row['id'] + ':' + item['id']
                    for key, override in item.get('slot_overrides', {}).items():
                        target = next((slot for slot in result['slots'] if slot['id'] == key), None)
                        if target is None:
                            raise ValueError(f'Unknown anatomical slot: {result["id"]}/{key}')
                        if set(override) - {'label','minimum','maximum','type','kind','unit','step'}:
                            raise ValueError(f'Unsupported slot override: {result["id"]}/{key}')
                        if 'kind' in override and override['kind'] != target['kind']:
                            raise ValueError(f'Anatomical slot kind mismatch: {result["id"]}/{key}')
                        target.update(override)
                    if any(slot['kind'] == 'context' for slot in result['slots']):
                        raise ValueError(f'Anatomical reports must enumerate every descriptor: {result["id"]}')
                    dependencies = item.get('requires_any', [])
                    if any(key not in local_ids or key == item['id'] for key in dependencies):
                        raise ValueError(f'Invalid anatomical dependency: {result["id"]}')
                    if dependencies:
                        result['requires_any'] = [identifier + ':' + row['id'] + ':' + key for key in dependencies]
                    if item.get('exclusive_group'):
                        result['exclusive_group'] = item['exclusive_group']
                    if item.get('report') is False:
                        result['report'] = False
                    invalidates = item.get('invalidates_normal', [])
                    if any(key not in structure_ids for key in invalidates):
                        raise ValueError(f'Unknown related anatomy: {result["id"]}')
                    if invalidates:
                        result['invalidates_normal'] = ['anatomy-' + key for key in invalidates]
                    result['requires_context'] = False
                    return result
                normal = compile_one({'id':'normal','label':'Normal','text':row['normal']}, 'normal') if row.get('normal') else None
                if normal and normal['slots']:
                    raise ValueError(f'A normal choice must be explicit and complete: {identifier}/{row["id"]}')
                findings = [compile_one(item, 'finding') for item in row['findings']]
                by_id = {item['id']:item for item in findings}
                def check_dependency(item, chain):
                    if item['id'] in chain:
                        raise ValueError(f'Cyclic anatomy dependency: {item["id"]}')
                    for parent in item.get('requires_any', []):
                        check_dependency(by_id[parent], chain | {item['id']})
                for item in findings:
                    check_dependency(item, set())
                group = row.get('group') or row['label']
                sections.append({'id':section_id,'anatomy_id':row['id'],'label':row['label'],'group':group,
                                 'source_sections':[group], 'report_section_id':'anatomic-'+slug(group),
                                 'report_section_label':group.upper(),'normal':normal,'findings':findings,
                                 'exclude_from_bulk_normal':bool(row.get('exclude_from_bulk_normal'))})
                if row.get('repeatable'):
                    sections[-1].update(repeatable=True, repeat_label=row.get('repeat_label', row['label']))
            investigation = {'id':identifier,'title':definition['title'],'modality':definition['modality'],
                             'sections':sections,'presentation':'anatomic_rows','content_revision':authored['version'],
                             'sources':[sources[key] for key in sorted({key for row in definition['sections'] for key in row['source_ids']})],
                             'clinical_approval':False}
            if definition.get('base_investigation_id'):
                investigation['base_investigation_id'] = definition['base_investigation_id']
            previous = next((i for i,x in enumerate(form['investigations']) if x['id'] == identifier), None)
            if previous is None:
                if not investigation.get('base_investigation_id'):
                    raise ValueError(f'New examination needs a regional reference: {identifier}')
                form['investigations'].append(investigation)
            else:
                if form['investigations'][previous].get('kind'):
                    investigation['kind'] = form['investigations'][previous]['kind']
                form['investigations'][previous] = investigation
            known_urls = {source['url'] for source in form['sources']}
            for source in investigation['sources']:
                if source['url'] not in known_urls:
                    form['sources'].append(copy.deepcopy(source));known_urls.add(source['url'])
            coverage.append({'guide_id':guide_id,'investigation_id':identifier,'structures':len(sections),
                             'findings':sum(len(row['findings']) for row in sections),
                             'anatomy_ids':[row['anatomy_id'] for row in sections],
                             'source_file':str(path.relative_to(root))})
            changed.add(guide_id)
    binding_path = root / 'data/radiology/descriptor-calculation-bindings.json'
    if binding_path.exists():
        try:
            from tools.descriptor_calculation_binding_compiler import attach_calculation_bindings
        except ModuleNotFoundError:
            from descriptor_calculation_binding_compiler import attach_calculation_bindings
        changed.update(attach_calculation_bindings(forms, json.loads(binding_path.read_text())))
    for guide_id in changed:
        form = forms[guide_id]
        form['provenance']['anatomic_expansion'] = 'Original structure-specific reporting choices; references retained; no clinical approval implied.'
        form['schema_hash'] = digest({key:value for key,value in form.items() if key != 'schema_hash'})
    return coverage
