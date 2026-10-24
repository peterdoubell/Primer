"""Validate finite data mappings to the existing versioned calculator APIs."""
import copy
import math


def attach_calculation_bindings(forms, authored):
    changed = set()
    investigations = {item['id']:(form,item) for form in forms.values() for item in form['investigations']}
    for investigation_id, bindings in authored.get('investigations', {}).items():
        if investigation_id not in investigations:
            raise ValueError('Unknown calculation investigation: ' + investigation_id)
        form, investigation = investigations[investigation_id]
        sections = {section.get('anatomy_id', section['id']):section for section in investigation['sections']}
        for section_key, specifications in bindings.items():
            if section_key not in sections:
                raise ValueError('Unknown calculation section: ' + section_key)
            section = sections[section_key]
            def finding_id(row, raw):
                found = next((finding for finding in row['findings'] if finding['id'] == raw or finding['id'] == investigation_id + ':' + row['anatomy_id'] + ':' + raw), None)
                if found is None: raise ValueError('Unknown calculation finding: ' + raw)
                return found
            compiled = []
            for original in specifications:
                spec = copy.deepcopy(original)
                if spec['calculator_id'] not in form.get('calculator_ids', []):
                    raise ValueError('Calculator does not belong to guide: ' + spec['calculator_id'])
                spec['trigger_any'] = [finding_id(section, identifier)['id'] for identifier in spec['trigger_any']]
                if not spec['trigger_any']: raise ValueError('Automatic calculation requires an explicit trigger')
                if not spec.get('inputs'): raise ValueError('Automatic calculation requires input mappings')
                for rule in spec['inputs'].values():
                    if rule.get('aggregate','first') not in ('first','max') or not rule.get('sources'):
                        raise ValueError('Unsupported calculation aggregation')
                    if 'scale' in rule and (type(rule['scale']) not in (int,float) or not math.isfinite(rule['scale']) or rule['scale'] <= 0):
                        raise ValueError('Invalid calculation unit scale')
                    for source in rule['sources']:
                        source_key = source.get('section_id', section_key)
                        if source_key.startswith('anatomy-') and source_key not in sections:
                            source_key = source_key.removeprefix('anatomy-')
                        source_section = sections.get(source_key)
                        if source_section is None: raise ValueError('Unknown calculation source section')
                        if source_key != section_key and source_section.get('repeatable'):
                            raise ValueError('An external repeated record is ambiguous')
                        if 'section_id' in source: source['section_id'] = source_section['id']
                        finding = finding_id(source_section, source['finding_id'])
                        source['finding_id'] = finding['id']
                        if source.get('slot_id'):
                            slot = next((slot for slot in finding['slots'] if slot['id'] == source['slot_id']), None)
                            if slot is None: raise ValueError('Unknown calculation source slot')
                            if slot['kind'] == 'choice':
                                options = {option['value'] for option in slot['options']}
                                if set(source.get('map', {})) != options:
                                    raise ValueError('Every clinical choice needs an explicit calculator mapping: ' + finding['id'])
                            elif slot['kind'] != 'number':
                                raise ValueError('Calculation sources cannot require typed context')
                        elif 'value' not in source:
                            raise ValueError('A selected control needs an explicit calculator value')
                for condition in spec.get('skip_when', []):
                    if condition['input'] not in spec['inputs'] or not condition.get('message') or not condition.get('values'):
                        raise ValueError('Invalid calculator applicability condition')
                compiled.append(spec)
            section['calculations'] = compiled
            changed.add(form['guide_id'])
    return changed
