"""Recover the exact reader and server from before the fast report templates.

Only the literal additions below are removed, and only from the exact reviewed
bytes; every other byte must already match the previous fingerprint.
"""
import hashlib

QUICK_REPORT = b"""function renderQuickReport(report, nodeId) {
  // Two editable texts in the reporting-system layout: the fast template and the all-normal report.
  return [['template', 'Fast template', report.template, 'Under each heading the first line is normal. Delete the lines that do not apply, choose within [a / b] and fill [ ].'],
    ['normal', 'Normal report', report.normal, 'Every heading normal. Add the clinical history and keep one study title.']]
    .map(([kind, title, text, description], index) => renderRadiologyTemplate({ id: nodeId + '-' + kind, title, description, text },
      'quick-' + index, nodeId, true));
}

"""

CHANGES = {
    'web/app.js': {
        'before': '1bcc58db62c46a558d7e1c691e1b9db44b09cd92bea386c2bf1b8b338d6d113b',
        'after': '4b36894adc650ada89f1518f152cf64c1e5385c59587d31dafd690de0b0e7d4b',
        'literals': (
            (b"  const original = template.text ?? radiologyReportText(template);\n",
             b"  const original = radiologyReportText(template);\n"),
            (QUICK_REPORT, b''),
            (b"  if (templates.length || ref.quick_report) section.append(el('div', { class: 'rad-report-templates' },\n"
             b"    ...(ref.quick_report ? renderQuickReport(ref.quick_report, n.id) : []),\n",
             b"  if (templates.length) section.append(el('div', { class: 'rad-report-templates' },\n"),
            (b"    ...(ref.quick_report || ref.structured_form?.descriptor_form && window.PrimerStructuredReporting ? [] : [\n",
             b"    ...(ref.structured_form?.descriptor_form && window.PrimerStructuredReporting ? [] : [\n"),
            (b"      ...(ref.quick_report ? [el('div', { class: 'rad-report-templates' }, ...renderQuickReport(ref.quick_report, n.id))] : []),\n",
             b''),
        ),
    },
    'primer/server.py': {
        'before': '33b88d44e2e45132098b39ea79dbf9bfa681ff913fcf25912c111fa7775e67b3',
        'after': '8c92004c98c75dec1e63a1067415859de5669235bfdd79464632586e2fd02f32',
        'literals': (
            (b"    from .report_templates import with_quick_report\n", b''),
            (b"            return with_quick_report(with_structured_form(descriptor_variant_detail(variant, resolve(variant['base_investigation_id']) if variant.get('base_investigation_id') else None)))\n",
             b"            return with_structured_form(descriptor_variant_detail(variant, resolve(variant['base_investigation_id']) if variant.get('base_investigation_id') else None))\n"),
            (b"    return with_quick_report(with_structured_form(detail(curr, investigation)))\n",
             b"    return with_structured_form(detail(curr, investigation))\n"),
        ),
    },
}


def before_fast_templates_bytes(path, raw):
    """Project the fast report template additions out of the exact current file."""
    record = CHANGES.get(str(path))
    if record is None or hashlib.sha256(raw).hexdigest() != record['after']:
        return raw
    restored = raw
    for current, previous in record['literals']:
        if restored.count(current) != 1:
            raise ValueError('Fast report template inverse literal is not unique')
        restored = restored.replace(current, previous, 1)
    if hashlib.sha256(restored).hexdigest() != record['before']:
        raise ValueError('Fast report templates changed unrelated bytes')
    return restored
