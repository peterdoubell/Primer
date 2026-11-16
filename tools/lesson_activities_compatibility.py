"""Recover the exact reader from before the stand-alone activity registry (2026-11-16).

Only the registry block is removed, and only from the exact reviewed bytes.
"""
import hashlib

PATH = 'web/app.js'
BEFORE = 'cae35e537358fc10387764701b5b00dd072ba90845f0f2e57ee1d0b9d7019a09'
AFTER = 'f3083a94b6994546db9a2d027a6f1134f57cec14718bce59a273e80bd7960929'
BLOCK = b"  // Stand-alone activities are listed in /app/activities/registry.json, so adding one needs no change here.\n  if (typeof fetch === 'function') {\n    const activityRow = el('div', { class: 'model-button-row', style: 'margin:1rem 0', hidden: '' });\n    page.append(activityRow);\n    window.PrimerActivityRegistry = window.PrimerActivityRegistry\n      || fetch('/app/activities/registry.json').then(response => response.ok ? response.json() : {}).catch(() => ({}));\n    window.PrimerActivityRegistry.then(registry => {\n      for (const activity of registry[n.id] || []) {\n        if (String(activity.href).startsWith('/app/')) activityRow.append(el('a', { class: 'btn ghost', href: activity.href }, activity.label));\n      }\n      activityRow.hidden = !activityRow.childNodes.length;\n    });\n  }\n"


def before_activity_registry_bytes(path, raw):
    if str(path) == 'data/radiology/radiology-asset-evidence.json':
        # Newest links for the evidence file: stored Radiology Assistant figures, then the sided ultrasound panels.
        from tools.anatomy_sources.package_radiology_assistant_figures import before_radiology_assistant_figures
        from tools.anatomy_sources.package_thoracic_us_side_panels import before_side_panels
        return before_side_panels(before_radiology_assistant_figures(raw))
    if str(path) != PATH or hashlib.sha256(raw).hexdigest() != AFTER:
        return raw
    if raw.count(BLOCK) != 1:
        raise ValueError('Activity registry inverse literal is not unique')
    restored = raw.replace(BLOCK, b'', 1)
    if hashlib.sha256(restored).hexdigest() != BEFORE:
        raise ValueError('Activity registry changed unrelated reader bytes')
    return restored
