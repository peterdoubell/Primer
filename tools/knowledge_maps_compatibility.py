"""Recover the exact shared UI used by historical source checks."""

import hashlib

from tools.source_studies_compatibility import before_source_studies_bytes


_MAP_CHANGES = {
    'web/app.js': (
        '9d93a0f6dd960989e74a874d7617da89e420785e33971fe607acebc3cd926868',
        '35698cc1fa6e713a975d6008765701965187ae1b49f07f06a76867f49b130d3e',
        (
            (57,
             b'  visualGallery: null, knowledgeMapIndex: null, restoreFocus: null, readerTitle: null };\n',
             b'  visualGallery: null, restoreFocus: null, readerTitle: null };\n'),
            (422,
             b"  if (view === 'maps') return '#/maps' + (arg ? '/' + arg.map(encodeURIComponent).join('/') : '');\n",
             b''),
            (445,
             b"  let parts;\n  try { parts = h.split('/').map(decodeURIComponent); }\n  catch (e) { if (e instanceof URIError) return { view: 'today', corrected: true }; throw e; }\n",
             b"  const parts = h.split('/').map(decodeURIComponent);\n"),
            (449,
             b"  if (view === 'maps') return { view, arg: parts.slice(1) };\n",
             b''),
            (495,
             b"  if (view !== 'maps') S.knowledgeMapIndex = null;\n",
             b''),
            (498,
             b"    const active = b.dataset.nav === view || (view === 'review-game' && b.dataset.nav === 'review')\n      || (view === 'maps' && b.dataset.nav === 'atlas');\n",
             b"    const active = b.dataset.nav === view || (view === 'review-game' && b.dataset.nav === 'review');\n"),
            (504,
             b'    maps: renderKnowledgeMaps,\n',
             b''),
            (3700,
             b"    el('a', { class: 'btn ghost small', href: hashFor('maps', ['module', n.id]) },\n      glyph('atlas', 16), ' Module map'),\n",
             b''),
            (5829,
             b"      el('a', { class: 'btn gold small', href: hashFor('maps') }, glyph('atlas', 16), ' Explore knowledge maps'),\n",
             b''),
            (6012,
             b"      el('a', { class: 'btn ghost small', href: hashFor('maps', ['subject', d.id]) }, 'Subject map'),\n",
             b''),
        ),
    ),
    'web/index.html': (
        '528c7b9793bc601214767509642a9307b5645d1c9bb8b2c5447d83850f927d92',
        '4f8b1b541d29a8186934a5b82057db8690241d2863817b882b5359b14442aac5',
        (
            (67,
             b'  <link rel="stylesheet" href="/app/knowledge-maps.css">\n',
             b''),
            (171,
             b'  <script src="/app/knowledge-maps.js"></script>\n',
             b''),
        ),
    ),
}


def before_knowledge_maps_bytes(path, raw):
    """Project only the known Knowledge Maps additions out of a shared file."""
    raw = before_source_studies_bytes(path, raw)
    # Recover the exact reader before the native endometrial case links.
    if str(path) == 'web/app.js' and hashlib.sha256(raw).hexdigest() == '6b81721dd7418583d432c5a225847399425492bd3cea07c374a6314cd95eb30c':
        raw = raw.replace(b"  if (n.id === 'rad.5.uterine-mr') page.append(el('div', { class: 'model-button-row', style: 'margin:1rem 0' },\n    el('a', { class: 'btn ghost', href: '/app/anatomy/cptac-endometrial/index.html' },\n      'Inspect an endometrial tumour on original MRI'),\n    el('a', { class: 'btn ghost', href: '/app/reference-studies/mullerian-2025/index.html' },\n      'Compare uterine cavity and external contour on source images')));\n", b"  if (n.id === 'rad.5.uterine-mr') page.append(el('a', { class: 'btn ghost', href: '/app/reference-studies/mullerian-2025/index.html' },\n    'Compare uterine cavity and external contour on source images'));\n", 1)
        raw = raw.replace(b"  if (n.id === 'ra.mri-endometrial-cancer') page.append(el('div', { class: 'model-button-row', style: 'margin:1rem 0' },\n    el('a', { class: 'btn ghost', href: '/app/anatomy/cptac-endometrial/index.html' },\n      'Inspect an endometrial tumour on original MRI')));\n", b'', 1)
        if hashlib.sha256(raw).hexdigest() != '031524a17ba08bdb3e17531acbabae2fc16d731c3f693dd2d4aaec84d173db17':
            raise ValueError('Endometrial case links changed unrelated reader bytes')
    # Recover the reviewed reader before the differential-calculus study link.
    if str(path) == 'web/app.js' and hashlib.sha256(raw).hexdigest() == '031524a17ba08bdb3e17531acbabae2fc16d731c3f693dd2d4aaec84d173db17':
        raw = raw.replace(b"  if (n.id === 'math.4.diff-calc') page.append(el('a', { class: 'btn ghost', href: '/app/math/derivative-signs/index.html' },\n    'Explore derivative signs and optimization'));\n", b'', 1)
        if hashlib.sha256(raw).hexdigest() != '5273aa946196c7275d761dda3c42b52b753127da96d12094b4090cbd58bfda62':
            raise ValueError('Differential calculus link changed unrelated reader bytes')
    # Remove the two later lesson links only from the exact reviewed reader.
    if str(path) == 'web/app.js' and hashlib.sha256(raw).hexdigest() == '5273aa946196c7275d761dda3c42b52b753127da96d12094b4090cbd58bfda62':
        raw = raw.replace(b"  if (n.id === 'phys.5.frontier') page.append(el('a', { class: 'btn ghost', href: '/app/physics/sparc/index.html' },\n    'Explore observed galaxy rotation curves'));\n", b'', 1)
        raw = raw.replace(b"  if (n.id === 'lang.5.philology') page.append(el('a', { class: 'btn ghost', href: '/app/language/stemma/index.html' },\n    'Compare manuscript families'));\n", b'', 1)
        if hashlib.sha256(raw).hexdigest() != '35698cc1fa6e713a975d6008765701965187ae1b49f07f06a76867f49b130d3e':
            raise ValueError('Source and learning links changed unrelated reader bytes')
    record = _MAP_CHANGES.get(str(path))
    if record is None:
        return raw
    before_hash, after_hash, changes = record
    if hashlib.sha256(raw).hexdigest() != after_hash:
        return raw

    lines = raw.splitlines(keepends=True)
    for start, current, previous in reversed(changes):
        end = start + len(current.splitlines(keepends=True))
        if b"".join(lines[start:end]) != current:
            raise ValueError("Knowledge Maps integration literal differs")
        lines[start:end] = previous.splitlines(keepends=True)
    restored = b"".join(lines)
    if hashlib.sha256(restored).hexdigest() != before_hash:
        raise ValueError("Knowledge Maps inverse changed unrelated bytes")
    return restored
