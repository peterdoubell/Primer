"""Resolve calculator inputs from explicit, structurally validated descriptors.

This pure module performs no clinical arithmetic and no I/O. Algorithms remain in
reporting_service.calculators. It intentionally never fills an unanswered input.
"""
import copy
import json
import math

_MISSING = object()


def _finite(value):
    if type(value) not in (int, float):
        return False
    try:
        return math.isfinite(value)
    except OverflowError:
        return False


def _equal(left, right):
    """JSON equality retains the distinction between true and the number one."""
    return json.dumps(left, sort_keys=True, allow_nan=False) == json.dumps(right, sort_keys=True, allow_nan=False)


def _mapping_key(value):
    if isinstance(value, str):
        return value
    if value is True:
        return 'true'
    if value is False:
        return 'false'
    if _finite(value):
        return format(value, '.15g')
    return None


def descriptor_calculation_jobs(form, state):
    """Build ordered jobs after render_descriptors has accepted the same state.

    A repeat's local sources always use that record. A source with section_id
    reads the original global selection, never another lesion. Old forms with
    no bindings produce no jobs and retain the existing manual-calculator path.
    """
    if not isinstance(state, dict):
        return []
    investigation = next((item for item in form.get('investigations', [])
                          if item['id'] == state.get('investigation_id')), None)
    selections = state.get('selections', {})
    if investigation is None or not isinstance(selections, dict):
        return []
    jobs = []
    for section in investigation.get('sections', []):
        selected = selections.get(section['id'], {})
        if not isinstance(selected, dict) or selected.get('normal') or selected.get('not_assessed'):
            continue
        if 'instances' in selected:
            if not section.get('repeatable') or not isinstance(selected['instances'], list):
                continue
            records = [(index, record) for index, record in enumerate(selected['instances'])]
        else:
            records = [(None, selected)]
        for index, record in records:
            if not isinstance(record, dict) or record.get('normal') or record.get('not_assessed'):
                continue
            chosen = record.get('findings', {})
            if not isinstance(chosen, dict):
                continue
            for spec in section.get('calculations', []):
                if not any(key in chosen for key in spec.get('trigger_any', [])):
                    continue
                context = (section.get('repeat_label', section['label']) + ' ' + str(index + 1)
                           if index is not None else section['label'])
                job = {
                    'calculator_id': spec['calculator_id'],
                    'label': spec.get('label', spec['calculator_id']),
                    'binding_id': section['id'] + ':' + ('single' if index is None else str(index + 1)) + ':' + spec['calculator_id'],
                    'context_label': context,
                    'section_id': section['id'], 'instance_index': index,
                    'instance_label': context if index is not None else None,
                    'inputs': {},
                }
                input_issues = []
                for name, binding in spec.get('inputs', {}).items():
                    values = []
                    missing = False
                    failed = False
                    for source in binding.get('sources', []):
                        target = selections.get(source['section_id'], {}) if 'section_id' in source else record
                        if not isinstance(target, dict) or target.get('normal') or target.get('not_assessed') or target.get('instances'):
                            missing = True
                            continue
                        findings = target.get('findings', {})
                        payload = findings.get(source['finding_id'], _MISSING) if isinstance(findings, dict) else _MISSING
                        if payload is _MISSING or not isinstance(payload, dict):
                            missing = True
                            continue
                        value = payload.get(source['slot_id'], _MISSING) if 'slot_id' in source else source.get('value', _MISSING)
                        if value is _MISSING or value is None or value == '':
                            missing = True
                            continue
                        if 'map' in source:
                            mapped = source['map'].get(_mapping_key(value), _MISSING)
                            if mapped is _MISSING:
                                failed = True
                                input_issues.append({'code': 'unmapped_calculation_input', 'input': name, 'finding_id': source['finding_id']})
                                continue
                            value = mapped
                        values.append(copy.deepcopy(value))
                    if failed or (binding.get('all_required') and missing) or not values:
                        continue
                    aggregate = binding.get('aggregate', 'first')
                    if aggregate == 'max':
                        if any(not _finite(value) for value in values):
                            input_issues.append({'code': 'invalid_calculation_aggregate', 'input': name})
                            continue
                        value = max(values)
                    elif aggregate == 'first':
                        try:
                            conflicting = any(not _equal(values[0], value) for value in values[1:])
                        except (ValueError, TypeError):
                            input_issues.append({'code': 'invalid_calculation_input', 'input': name})
                            continue
                        if conflicting:
                            input_issues.append({'code': 'conflicting_calculation_inputs', 'input': name})
                            continue
                        value = values[0]
                    else:
                        input_issues.append({'code': 'unsupported_calculation_aggregate', 'input': name})
                        continue
                    if 'scale' in binding:
                        scale = binding['scale']
                        if (not _finite(value) or not _finite(scale)):
                            input_issues.append({'code': 'invalid_calculation_scale', 'input': name})
                            continue
                        value = value * scale
                        if not _finite(value):
                            input_issues.append({'code': 'invalid_calculation_scale', 'input': name})
                            continue
                    job['inputs'][name] = copy.deepcopy(value)
                if input_issues:
                    job['input_issues'] = input_issues
                for rule in spec.get('skip_when', []):
                    if rule['input'] in job['inputs'] and any(_equal(job['inputs'][rule['input']], value) for value in rule['values']):
                        job.update(not_applicable=True, message=rule['message'])
                        break
                jobs.append(job)
    return jobs
