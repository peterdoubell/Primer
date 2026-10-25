"""Deterministic rendering of explicitly selected, source-backed descriptors.

This dependency-free module is shared with the reporting API. No selection,
measurement or normal statement is inferred from an unanswered control.
"""
import math
import re

MAX_REPEAT_INSTANCES = 50


def expand_repeated_sections(investigation, selections):
    """Expand explicit records without mutating the saved schema or selections."""
    expanded, values, issues = [], dict(selections), []
    for section in investigation['sections']:
        expanded.append(section)
        selected = selections.get(section['id'], {})
        if not isinstance(selected, dict) or 'instances' not in selected:
            continue
        location = {'section_id': section['id'], 'severity': 'error'}
        instances = selected['instances']
        if (not section.get('repeatable') or not isinstance(instances, list)
                or len(instances) > MAX_REPEAT_INSTANCES
                or set(selected) - {'normal', 'not_assessed', 'findings', 'instances'}
                or not isinstance(selected.get('findings', {}), dict)
                or any(type(selected.get(flag, False)) is not bool for flag in ('normal', 'not_assessed'))
                or selected.get('normal') or selected.get('not_assessed') or selected.get('findings')):
            issues.append({'code': 'invalid_repeat_instances', **location})
            values[section['id']] = {}
            continue
        values[section['id']] = {}
        for index, instance in enumerate(instances):
            key = section['id'] + '@' + str(index + 1)
            label = section.get('repeat_label', section['label']) + ' ' + str(index + 1)
            expanded.append(dict(section, id=key, label=label, normal=None, repeat_instance_label=label))
            values[key] = instance
            if isinstance(instance, dict) and not instance.get('not_assessed') and not instance.get('findings'):
                issues.append({'code': 'empty_repeat_instance', 'instance_index': index, **location})
    return dict(investigation, sections=expanded), values, issues


def render_descriptors(form, state):
    issues = []

    def problem(code, **location):
        issues.append({'code': code, 'severity': 'error', **location})

    if not isinstance(state, dict) or set(state) - {'investigation_id', 'selections'}:
        return {'valid': False, 'text': '', 'sections': [], 'issues': [{'code': 'invalid_descriptor_state', 'severity': 'error'}]}
    investigation = next((x for x in form['investigations'] if x['id'] == state.get('investigation_id')), None)
    if investigation is None:
        return {'valid': False, 'text': '', 'sections': [], 'issues': [{'code': 'unknown_investigation', 'severity': 'error'}]}
    selections = state.get('selections', {})
    if not isinstance(selections, dict) or len(selections) > 1000:
        return {'valid': False, 'text': '', 'sections': [], 'issues': [{'code': 'invalid_descriptor_selections', 'severity': 'error'}]}
    original_ids = {section['id'] for section in investigation['sections']}
    for key in selections:
        if key not in original_ids:
            problem('unknown_descriptor_section', section_id=key)
    investigation, selections, repeated_issues = expand_repeated_sections(investigation, selections)
    issues.extend(repeated_issues)

    def active(finding, chosen, definitions, chain=None):
        chain = set() if chain is None else chain
        if finding['id'] in chain: return False
        return not finding.get('requires_any') or any(
            key in chosen and key in definitions and active(definitions[key], chosen, definitions, chain | {finding['id']})
            for key in finding['requires_any'])

    blocked_normals = set()
    for section in investigation['sections']:
        selected = selections.get(section['id'], {})
        chosen = selected.get('findings', {}) if isinstance(selected, dict) else {}
        if not isinstance(chosen, dict): continue
        definitions = {item['id']:item for item in section['findings']}
        for finding in section['findings']:
            if finding['id'] in chosen and active(finding, chosen, definitions):
                blocked_normals.update(finding.get('invalidates_normal', []))

    def statement(descriptor, values, section_id):
        location = {'section_id': section_id, 'finding_id': descriptor['id']}
        if not isinstance(values, dict) or len(values) > 100:
            problem('invalid_descriptor_values', **location)
            return None
        slots = {x['id']: x for x in descriptor['slots']}
        count = len(issues)
        for key in values:
            if key not in slots:
                problem('unknown_descriptor_slot', slot_id=key, **location)
        rendered = {}
        for key, slot in slots.items():
            value = values.get(key)
            if value is None or value == '':
                problem('missing_descriptor_value', slot_id=key, label=slot['label'], **location)
                continue
            if slot['kind'] == 'choice':
                if not isinstance(value, str) or value not in {x['value'] for x in slot['options']}:
                    problem('invalid_descriptor_choice', slot_id=key, **location)
                    continue
                rendered[key] = value
            elif slot['kind'] == 'number':
                try:
                    finite = type(value) in (int, float) and math.isfinite(value)
                except OverflowError:
                    finite = False
                if not finite:
                    problem('invalid_descriptor_number', slot_id=key, **location)
                    continue
                if ('minimum' in slot and value < slot['minimum']) or ('maximum' in slot and value > slot['maximum']):
                    problem('descriptor_number_out_of_range', slot_id=key, **location)
                    continue
                rendered[key] = format(value, '.15g')
            elif slot['kind'] == 'context':
                if not isinstance(value, str) or not value.strip() or len(value) > 4000 or re.search(r'[\x00-\x1f\x7f\[\]]|_{2,}|\b(?:TODO|TBD)\b', value, flags=re.I):
                    problem('invalid_descriptor_context', slot_id=key, **location)
                    continue
                rendered[key] = value.strip()
            else:
                problem('unsupported_descriptor_slot', slot_id=key, **location)
        if len(issues) != count:
            return None
        return ''.join(part.get('text', '') if 'text' in part else rendered[part['slot']] for part in descriptor['segments'])

    grouped = {}
    selected_count = 0
    for section in investigation['sections']:
        key = section['id']
        selection = selections.get(key, {})
        if not isinstance(selection, dict) or set(selection) - {'normal', 'not_assessed', 'findings'}:
            problem('invalid_descriptor_selection', section_id=key)
            continue
        if any(type(selection.get(flag, False)) is not bool for flag in ('normal', 'not_assessed')):
            problem('invalid_descriptor_selection', section_id=key)
            continue
        chosen = selection.get('findings', {})
        if not isinstance(chosen, dict) or len(chosen) > 100:
            problem('invalid_descriptor_findings', section_id=key)
            continue
        normal, unassessed = selection.get('normal', False), selection.get('not_assessed', False)
        if sum((normal, unassessed, bool(chosen))) > 1:
            problem('conflicting_descriptor_status', section_id=key)
            continue
        lines = []
        if normal:
            if key in blocked_normals:
                problem('conflicting_anatomic_normal', section_id=key)
                continue
            if not section.get('normal'):
                problem('normal_not_available', section_id=key)
            else:
                line = statement(section['normal'], {}, key)
                if line: lines.append(line)
        elif unassessed:
            lines.append(section['label'] + ': not assessed.')
        else:
            definitions = {x['id']: x for x in section['findings']}
            exclusive = {}
            for finding_id in chosen:
                if finding_id not in definitions:
                    problem('unknown_descriptor_finding', section_id=key, finding_id=finding_id)
            for descriptor in section['findings']:
                if descriptor['id'] not in chosen: continue
                if not active(descriptor, chosen, definitions):
                    problem('inactive_descriptor_finding', section_id=key, finding_id=descriptor['id'])
                    continue
                group = descriptor.get('exclusive_group')
                if group:
                    if group in exclusive:
                        problem('conflicting_descriptor_findings', section_id=key, finding_id=descriptor['id'])
                    exclusive[group] = descriptor['id']
                if descriptor.get('report') is not False:
                    selected_count += 1
                line = statement(descriptor, chosen[descriptor['id']], key)
                if line and descriptor.get('report') is not False: lines.append(line)
        if lines:
            if section.get('repeat_instance_label') and not unassessed:
                lines = [section['repeat_instance_label'] + ':\n' + '\n'.join(lines)]
            report_id = section.get('report_section_id') or key
            group = grouped.setdefault(report_id, {'section_id': report_id, 'label': section.get('report_section_label') or section['label'], 'lines': [], 'status': 'not_assessed' if unassessed else 'provided'})
            if not unassessed: group['status'] = 'provided'
            for line in lines:
                if line not in group['lines']: group['lines'].append(line)
    rendered_sections = [{'section_id': x['section_id'], 'label': x['label'], 'text': '\n'.join(x['lines']), 'status': x['status']} for x in grouped.values()]
    valid = not issues
    return {'valid': valid, 'issues': issues, 'sections': rendered_sections,
            'text': '\n\n'.join(x['label'] + '\n' + x['text'] for x in rendered_sections) if valid else '',
            'investigation_id': investigation['id'], 'selected_finding_count': selected_count}
