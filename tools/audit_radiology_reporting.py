#!/usr/bin/env python3
"""Audit local reporting-reference coverage; this is not clinical sign-off."""
import argparse
import json
from collections import Counter
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from primer.curriculum import Curriculum


def audit():
    curriculum = Curriculum()
    modules = []
    for node in curriculum.nodes.values():
        if node['domain'] != 'radiology' or not node['id'].startswith('rad.'):
            continue
        ref = node['radiology_reference']
        guide = ref['reporting']
        generic = [section['heading'] for report in ref['report_templates'] for section in report['sections']
                   if section['body'] == '[Observations / measurements with units / not assessed and reason].']
        modules.append({
            'id': node['id'], 'title': node['title'], 'section': node['section'],
            'reviewed_at': guide['reviewed_at'], 'checklist_items': len(guide['checklist']),
            'measurements': len(guide['measurements']), 'finding_sections': len(guide['template_sections']),
            'templates': len(ref['report_templates']), 'image_slots': len(ref['key_images']),
            'diagrams': sum(media['kind'] == 'illustration' for media in node['lesson_media']),
            'model_family': ref['spatial_model']['family'], 'scenario': ref['spatial_model']['scenario'],
            'reporting_sources': len(guide['sources']), 'criteria_table': bool(guide.get('criteria_table')),
            'generic_findings': generic,
        })
    images = [image for node in curriculum.nodes.values()
              if node['domain'] == 'radiology' and node['id'].startswith('rad.')
              for image in node['radiology_reference']['key_images']]
    failures = [row['id'] for row in modules if not row['diagrams'] or row['generic_findings']
                or row['checklist_items'] < 4 or row['finding_sections'] < 5 or not row['reporting_sources']]
    return {'modules': len(modules), 'checklist_items': sum(row['checklist_items'] for row in modules),
            'measurement_references': sum(row['measurements'] for row in modules),
            'finding_sections': sum(row['finding_sections'] for row in modules),
            'templates': sum(row['templates'] for row in modules), 'image_slots': len(images),
            'image_types': dict(Counter(image['image_type'] for image in images)),
            'diagrams': sum(row['diagrams'] for row in modules), 'reporting_3d_models': len(modules),
            'model_families': len({row['model_family'] for row in modules}),
            'criteria_tables': sum(row['criteria_table'] for row in modules),
            'failures': failures, 'module_details': modules}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()
    report = audit()
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(json.dumps({key: value for key, value in report.items() if key != 'module_details'}, indent=2))
    raise SystemExit(bool(report['failures']))
