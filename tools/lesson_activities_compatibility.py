"""Recover the exact reader from before the stand-alone activity registry (2026-11-16).

Only the registry block is removed, and only from the exact reviewed bytes.
"""
import hashlib

PATH = 'web/app.js'
BEFORE = 'cae35e537358fc10387764701b5b00dd072ba90845f0f2e57ee1d0b9d7019a09'
AFTER = 'f3083a94b6994546db9a2d027a6f1134f57cec14718bce59a273e80bd7960929'
BLOCK = b"  // Stand-alone activities are listed in /app/activities/registry.json, so adding one needs no change here.\n  if (typeof fetch === 'function') {\n    const activityRow = el('div', { class: 'model-button-row', style: 'margin:1rem 0', hidden: '' });\n    page.append(activityRow);\n    window.PrimerActivityRegistry = window.PrimerActivityRegistry\n      || fetch('/app/activities/registry.json').then(response => response.ok ? response.json() : {}).catch(() => ({}));\n    window.PrimerActivityRegistry.then(registry => {\n      for (const activity of registry[n.id] || []) {\n        if (String(activity.href).startsWith('/app/')) activityRow.append(el('a', { class: 'btn ghost', href: activity.href }, activity.label));\n      }\n      activityRow.hidden = !activityRow.childNodes.length;\n    });\n  }\n"


DICTATION_LAYOUT = (
    '74520a58e62f3af7284f33a54ea50a3a4ab9333f143df67d2a42f2468f31b797',
    b"function renderQuickReport(report, nodeId) {\n  const reports = [\n    ['dictation', 'Dictation template', report.dictation?.text, report.dictation?.title, 'Fill the [] fields with your findings.'],\n    ['template', 'Fast template', report.template, report.title, 'Choose the findings that apply.'],\n    ['normal', 'Normal report', report.normal, report.title, 'Use after confirming normal findings.'],\n  ].filter(([, , text]) => text);\n  return reports.map(([kind, title, text, studyTitle, description], index) =>\n    renderRadiologyTemplate({ title, description, text, studyTitle }, 'quick-' + kind, nodeId, index === 0));\n}",
    b"function renderQuickReport(report, nodeId) {\n  // Two editable texts in the reporting-system layout: the fast template and the all-normal report.\n  return [['template', 'Fast template', report.template, 'Under each heading the first line is normal. Delete the lines that do not apply, choose within [a / b] and fill [ ].'],\n    ['normal', 'Normal report', report.normal, 'Every heading normal. Add the clinical history and keep one study title.']]\n    .map(([kind, title, text, description], index) => renderRadiologyTemplate({ id: nodeId + '-' + kind, title, description, text, studyTitle: report.title },\n      'quick-' + index, nodeId, true));\n}",
)


def before_activity_registry_bytes(path, raw):
    if str(path) == PATH:
        from tools.recist_pelvic_runtime_compatibility import before_recist_pelvic_delivery_bytes
        raw = before_recist_pelvic_delivery_bytes(path, raw)
    if str(path) == 'data/radiology/radiology-asset-evidence.json':
        # Newest links for the evidence file: sided Radiology Assistant figures, second-pass stored-caption bindings, first-pass stored-caption bindings,
        # Radiology Assistant figures, sided ultrasound panels.
        from tools.anatomy_sources.bind_stored_caption_assets import before_stored_caption_bindings
        from tools.anatomy_sources.bind_stored_caption_assets_pass2 import before_stored_caption_bindings_pass2
        from tools.anatomy_sources.package_radiology_assistant_sided_figures import before_radiology_assistant_sided_figures
        raw = before_stored_caption_bindings_pass2(before_radiology_assistant_sided_figures(raw))
        from tools.anatomy_sources.package_radiology_assistant_figures import before_radiology_assistant_figures
        from tools.anatomy_sources.package_thoracic_us_side_panels import before_side_panels
        return before_side_panels(before_radiology_assistant_figures(before_stored_caption_bindings(raw)))
    if str(path) == PATH and hashlib.sha256(raw).hexdigest() == DICTATION_LAYOUT[0]:
        raw = raw.replace(DICTATION_LAYOUT[1], DICTATION_LAYOUT[2], 1)
        if hashlib.sha256(raw).hexdigest() != AFTER:
            raise ValueError('Dictation layout changed unrelated reader bytes')
    if str(path) != PATH or hashlib.sha256(raw).hexdigest() != AFTER:
        return raw
    if raw.count(BLOCK) != 1:
        raise ValueError('Activity registry inverse literal is not unique')
    restored = raw.replace(BLOCK, b'', 1)
    if hashlib.sha256(restored).hexdigest() != BEFORE:
        raise ValueError('Activity registry changed unrelated reader bytes')
    return restored
