"""Recover the exact shared UI used by historical source checks."""

import hashlib


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
