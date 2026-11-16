#!/usr/bin/env python3
"""Draft structure inventories for the investigations that had none (2026-11-16).

Each inventory lists the structures the investigation's own click-builder checklist asks the
reader to report. Nothing is inferred beyond that checklist: one requirement per reportable
checklist row, with no invented sub-parts. Technique and report-review rows are not anatomy and
are left out. Every inventory is a draft that still needs specialist review.

The inventory file is byte-pinned, so the additions are inserted as literal text at two points
and `before_remaining_inventories` removes exactly those bytes.

Usage: python tools/anatomy_sources/expand_remaining_requirements.py [--write]
"""
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
REQUIREMENTS = ROOT / 'data/radiology/non-msk-structure-requirements.json'
RECEIPT = ROOT / 'docs/remaining-reporting-inventories-20261116/inverse.json'
NOT_ANATOMY = {'technique', 'report review', 'protocol', 'acquisition'}
IDS_END = '\n    ],\n    "whole_radiology_scope_complete"'
LIST_END = '\n  ],\n  "additional_scope": [],'
# Checklist rows that record context, method or a conclusion: they are reported but are not anatomy to depict.
NOT_STRUCTURE = re.compile(r'\b(?:time point|comparab|check|assessment|context|age|height|scope|protocol|planned phase|timing|access|reaction|'
                           r'review|consideration|pregnancy|decision|administration|sums|measurements?|stability|interpretation)\b', re.I)
NOTE = ('Derived on 2026-11-16 from the investigation\'s click-builder reporting checklist: one requirement per reportable row, '
        'no sub-parts inferred. Sub-structure expansion, laterality instantiation and source review are still required.')


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def modalities(investigation, item):
    text = (item['title'] + ' ' + item['modality']).lower()
    found = [name for name, pattern in (('CT', r'\bct\b'), ('MRI', r'\bmri?\b|\bmr\b'), ('Ultrasound', r'ultrasound'),
                                         ('Radiography', r'radiograph|x-ray'), ('Fluoroscopy', r'fluoroscop'))
             if re.search(pattern, text)]
    return found or ['as_acquired']


def side(section):
    text = ' '.join(str(section.get(k, '')) for k in ('label', 'compartment', 'group')).lower()
    left, right = bool(re.search(r'\bleft\b', text)), bool(re.search(r'\bright\b', text))
    return 'left' if left and not right else 'right' if right and not left else 'examined_side'


def build(item, guide_reference, descriptor):
    guide = guide_reference['reporting']
    labels = {entry['label'].casefold(): index for index, entry in enumerate(guide['checklist'])}
    urls = [source['url'] for source in descriptor.get('sources', []) if source.get('url')]
    prefix = re.sub(r'[^a-z0-9]+', '_', item['id'].removeprefix('ra.')).strip('_')
    rows = [s for s in descriptor['sections'] if s.get('anatomy_id')
            and not {str(s.get(k, '')).casefold() for k in ('compartment', 'report_section_label', 'group')} & NOT_ANATOMY
            and (s.get('normal') or s.get('findings'))]
    repeated = {label for label in [s['label'] for s in rows] if [s['label'] for s in rows].count(label) > 1}
    structures, seen = [], set()
    for section in rows:
        identifier = prefix + '.' + re.sub(r'[^a-z0-9]+', '_', section['anatomy_id'].lower()).strip('_')
        if identifier in seen:
            raise ValueError('Repeated structure id: ' + identifier)
        seen.add(identifier)
        match = next((labels[str(section.get(k, '')).casefold()] for k in ('compartment', 'group', 'label')
                      if str(section.get(k, '')).casefold() in labels), None)
        structures.append({
            'id': identifier,
            'name': (section.get('group', '') + ' · ' if section['label'] in repeated and section.get('group') else '') + section['label'],
            'tissue_class': ('reporting_item_not_an_anatomical_structure' if NOT_STRUCTURE.search(section['label'])
                             else 'reportable_structure_or_finding_site_from_reporting_checklist'),
            'laterality': side(section), 'modality_scope': modalities(descriptor, item),
            'condition': 'Show the actual acquired structure and its full reported extent; record any part not covered.',
            'requirement_basis': 'click_builder_reporting_checklist_row',
            'report_refs': [] if match is None else [{'checklist_index': match, **guide['checklist'][match]}],
            'context_requirements': {'purpose': 'anatomical_reference'},
            'requires_site_instantiation': bool(section.get('repeatable')),
            'source_urls': urls,
            'checklist_row': {'section_id': section['id'], 'compartment': section.get('compartment'), 'group': section.get('group')},
        })
    contract = {k: guide_reference.get(k) for k in ('reporting', 'report_templates', 'walkthrough', 'reading')}
    return {
        'investigation_id': item['id'], 'module_id': item['module_id'], 'title': item['title'], 'modality': item['modality'],
        'scope_type': 'reporting_checklist_rows_without_sub_part_expansion',
        'clinical_validation_status': 'draft_requires_specialist_review',
        'required_representations': ['image', 'schematic', 'model'],
        'sources': urls, 'source_contract_sha256': digest(contract),
        'reporting_checklist': [{'index': i, **entry} for i, entry in enumerate(guide['checklist'])],
        'reporting_template_sections': guide['template_sections'],
        'structures': structures, 'expansion_rules': [], 'source_scope_issues': [], 'functional_evidence_requirements': [],
        'derivation_note': NOTE,
    }


def additions():
    from primer.curriculum import Curriculum
    from primer import radiology_catalog
    from primer.reporting_bridge import descriptor_forms
    curriculum, catalog = Curriculum(), radiology_catalog.catalogue()
    existing = set(json.loads(before_remaining_inventories(REQUIREMENTS.read_text()))['scope']['catalog_investigation_ids'])
    descriptors = {i['id']: i for form in descriptor_forms()['forms'].values() for i in form['investigations']}
    out = []
    for item in catalog['investigations']:
        if item['section'] == 'Musculoskeletal' or item['id'] in existing:
            continue
        reference = radiology_catalog.detail(curriculum, item)['radiology_reference']
        out.append(build(item, reference, descriptors[item['id']]))
    return out


def insert(text, items):
    """Insert the ids and inventories as literal text; return the new text and the two inserted strings."""
    if text.count(IDS_END) != 1 or text.count(LIST_END) != 1:
        raise ValueError('Inventory insertion points are ambiguous')
    ids = ''.join(',\n      ' + json.dumps(item['investigation_id']) for item in items)
    body = ''.join(',\n    ' + json.dumps(item, indent=2, ensure_ascii=True).replace('\n', '\n    ') for item in items)
    at = text.index(IDS_END)
    text = text[:at] + ids + text[at:]
    at = text.index(LIST_END)
    return text[:at] + body + text[at:], ids, body


def before_remaining_inventories(raw):
    """Remove exactly the bytes this tool inserted; any other content is returned untouched."""
    if not RECEIPT.exists():
        return raw
    receipt = json.loads(RECEIPT.read_text())
    encoded = raw.encode() if isinstance(raw, str) else raw
    if hashlib.sha256(encoded).hexdigest() != receipt['after_sha256']:
        return raw
    (a0, a1), (b0, b1) = receipt['removed_byte_ranges']
    restored = encoded[:a0] + encoded[a1:b0] + encoded[b1:]
    if hashlib.sha256(restored).hexdigest() != receipt['before_sha256']:
        raise ValueError('Remaining inventory inverse changed unrelated bytes')
    return restored.decode() if isinstance(raw, str) else restored


def main():
    text = before_remaining_inventories(REQUIREMENTS.read_text())
    items = additions()
    updated, ids, body = insert(text, items)
    json.loads(updated)
    a0 = len(text[:text.index(IDS_END)].encode()); a1 = a0 + len(ids.encode())
    b0 = len(updated[:updated.index(LIST_END)].encode()) - len(body.encode()); b1 = b0 + len(body.encode())
    print(json.dumps({'investigations': len(items), 'structures': sum(len(i['structures']) for i in items),
                      'with_report_ref': sum(bool(s['report_refs']) for i in items for s in i['structures']),
                      'not_anatomy': sum(s['tissue_class'].startswith('reporting_item') for i in items for s in i['structures']),
                      'smallest': sorted((len(i['structures']), i['investigation_id']) for i in items)[:5]}))
    if '--write' in sys.argv:
        RECEIPT.parent.mkdir(parents=True, exist_ok=True)
        REQUIREMENTS.write_text(updated)
        RECEIPT.write_text(json.dumps({
            'path': 'data/radiology/non-msk-structure-requirements.json', 'scope': 'appended_draft_inventories_only',
            'clinical_approval': False, 'investigation_ids': [i['investigation_id'] for i in items],
            'before_sha256': hashlib.sha256(text.encode()).hexdigest(), 'after_sha256': hashlib.sha256(updated.encode()).hexdigest(),
            'removed_byte_ranges': [[a0, a1], [b0, b1]]}, indent=2) + '\n')


if __name__ == '__main__':
    main()
