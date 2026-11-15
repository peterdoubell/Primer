"""Recover the exact report builder from before the Arial 12 pt copy layout (2026-11-15).

Only these three literals are restored, and only from the exact new bytes.
"""
import hashlib

PATH = 'web/radiology-structured.js'
BEFORE = '8445df128aa282ae71ff3439f05e32fe2510e337a9999d5e262b8180d1227a50'
AFTER = '814b3b3c171f98c6f0dfd2e693a4bfbb1a8a75d20a96f11f6c1d01f2426a523a'
LITERALS = (
    (b"/^(Clinical history|Comparison|Protocol|Technique|Findings|Impression|Recommendation):$/",
     b"/^(Clinical history|Comparison|Impression|Recommendation):$/"),
    (b"font-family:Arial,sans-serif;font-size:12pt;line-height:1.4", b"font-family:Arial,sans-serif;line-height:1.4"),
    (b"case 'main': return '<u>' + content + '</u>';", b"case 'main': return '<strong><u>' + content + '</u></strong>';"),
)


def before_report_layout_bytes(path, raw):
    if str(path) != PATH or hashlib.sha256(raw).hexdigest() != AFTER:
        return raw
    restored = raw
    for current, previous in LITERALS:
        if restored.count(current) != 1:
            raise ValueError('Report layout inverse literal is not unique')
        restored = restored.replace(current, previous, 1)
    if hashlib.sha256(restored).hexdigest() != BEFORE:
        raise ValueError('Report layout changed unrelated builder bytes')
    return restored


# 2026-11-15: a checklist normal reads "Supraspinatus tendon: normal."
NORMAL_LINE = {
    'web/radiology-structured.js': ('814b3b3c171f98c6f0dfd2e693a4bfbb1a8a75d20a96f11f6c1d01f2426a523a', '9bbc93a07b3a73f5fcd35fff6955fbd304664ad771bdb1ab8220c64532596bb7', (
        (b"  const absentLabel = /(?:fracture|complications?|fistula|effusion|mass|lesion|collection|haematoma|haemorrhage|thrombosis|stenosis|foreign bod(?:y|ies)|hernia|aneurysm|tumour|spread|invasion|ossification|osteolysis|coalition|gas|air|blood|loose bodies|injury|mass effect|herniation)$|\\b(?:fistula|fracture|foreign bod(?:y|ies))\\b/i;\n  const absentTail = '(?:[.,]| (?:is|are|in|on|at|of|or|and|to|within|either|seen|identified)\\\\b|$)';\n  function normalLine(label, text, group = '') {\n    const lowered = text.toLowerCase();\n    const absent = lowered.startsWith('no ') && (new RegExp('^' + label.toLowerCase().replace(/[.*+?^${}()|[\\]\\\\]/g, '\\\\$&') + '(?:e?s)?' + absentTail).test(lowered.slice(3)) || absentLabel.test(label));\n    const kind = / \xc2\xb7 ([a-z]+)s$/.exec(group);\n    if (kind) label += ' ' + kind[1];\n    else if (group) label = group + ', ' + label.replace(/\\b[A-Z][a-z]+\\b/g, word => word.toLowerCase());\n    return label + (absent ? ': none.' : ': normal.');\n  }\n",
         b''),
        (b'    const normalLabels = (investigation.sections || []).filter(section => section.normal).map(section => section.label);\n',
         b''),
        (b"lines.push(normalLine(section.label, result.text, normalLabels.filter(label => label === section.label).length > 1 ? section.group || '' : ''));",
         b'lines.push(normalSummaries.get(section.id) ?? result.text);'),
    )),
    'primer/descriptor_reporting.py': ('07508d419972f176b301e5ae79869ca5cf3b67caa51128630ca5e808130f29a6', '37538ed99536aab8c3dcd9f5b63c4eb30bbcf30fef3dd1bee5be2b05a9728e3d', (
        (b'ABSENT_LABEL = re.compile(r\'(?:fracture|complications?|fistula|effusion|mass|lesion|collection|haematoma|haemorrhage|thrombosis|stenosis|foreign bod(?:y|ies)|hernia|aneurysm|tumour|spread|invasion|ossification|osteolysis|coalition|gas|air|blood|loose bodies|injury|mass effect|herniation)$|\\b(?:fistula|fracture|foreign bod(?:y|ies))\\b\', re.I)\nABSENT_TAIL = r\'(?:[.,]| (?:is|are|in|on|at|of|or|and|to|within|either|seen|identified)\\b|$)\'\n\n\ndef normal_line(label, text, group=\'\'):\n    """\'Supraspinatus tendon: normal.\' A heading that names a finding reads \'Fracture: none.\'\n\n    A label used twice in one study carries its group: \'Medial meniscus, anterior horn: normal.\'\n    A group that names the kind of structure gives \'Supraspinatus tendon\' and \'Supraspinatus muscle\'.\n    """\n    lowered = text.lower()\n    absent = lowered.startswith(\'no \') and (\n        re.match(re.escape(label.lower()) + \'(?:e?s)?\' + ABSENT_TAIL, lowered[3:]) or ABSENT_LABEL.search(label))\n    kind = re.search(r\' \xc2\xb7 ([a-z]+)s$\', group)\n    if kind:\n        label += \' \' + kind.group(1)\n    elif group:\n        label = group + \', \' + re.sub(r\'\\b[A-Z][a-z]+\\b\', lambda word: word.group().lower(), label)\n    return label + (\': none.\' if absent else \': normal.\')\n',
         b''),
        (b"    normal_labels = [section['label'] for section in investigation['sections'] if section.get('normal')]\n",
         b''),
        (b"line = normal_line(section['label'], line, section.get('group', '')\n                                       if normal_labels.count(section['label']) > 1 else '')",
         b'line = normal_summaries.get(key, line)'),
    )),
}


def before_normal_line_bytes(path, raw):
    row = NORMAL_LINE.get(str(path))
    if not row or hashlib.sha256(raw).hexdigest() != row[1]:
        return raw
    restored = raw
    for current, previous in row[2]:
        if restored.count(current) != 1:
            raise ValueError('Normal line inverse literal is not unique')
        restored = restored.replace(current, previous, 1)
    if hashlib.sha256(restored).hexdigest() != row[0]:
        raise ValueError('Normal line changed unrelated report bytes')
    return restored


# 2026-11-15: the on-screen report draft matches the copied text (Arial 12 pt, headings not bold).
PREVIEW_PATH = 'web/radiology-structured.css'
PREVIEW = ('f19c6250114063631410717561f262a9cf2e52ec60f2a2bc668033399ab9cb25', 'aa0cdb0c82544dac1c0a25120246d1164664d2755adc90a71cd3570ec01b8607',
           b'.rad-report-main-heading { font-weight: 400; }\n.rad-report-text { font: 12pt/1.4 Arial, sans-serif !important; }',
           b'.rad-report-main-heading { font-weight: 700; }')


def before_preview_match_bytes(path, raw):
    if str(path) != PREVIEW_PATH or hashlib.sha256(raw).hexdigest() != PREVIEW[1]:
        return raw
    if raw.count(PREVIEW[2]) != 1:
        raise ValueError('Preview inverse literal is not unique')
    restored = raw.replace(PREVIEW[2], PREVIEW[3], 1)
    if hashlib.sha256(restored).hexdigest() != PREVIEW[0]:
        raise ValueError('Preview match changed unrelated stylesheet bytes')
    return restored


# 2026-11-15: the Report template tab is a rich-text editor.
TEMPLATE_EDITOR = {
    'web/app.js': ('151d1e656067a107b9e6c32522c4989ed99110a692110ef48d6acea8a3c62fde', '2a20c03b28740f18e3cdf73f726185630b22c3903d358017939c20ab451de61b', (
        (b'   Foundation articles stay with their publisher. Our report drafts contain\n   text and its bold, italic and underline only, held in the mounted editor:\n   no storage, patient uploads, background requests, or generated conclusions. */',
         b'   Foundation articles stay with their publisher. Our report drafts contain\n   plain text only, held in the mounted editor: no storage, patient uploads,\n   background requests, or generated conclusions. */'),
        (b'  // A rich-text editor: headings underlined and subheadings italic as they are copied.\n  const editor = el(\'div\', { id: uid, class: \'rad-report-editor rad-report-rich\', contenteditable: \'true\', role: \'textbox\',\n    \'aria-multiline\': \'true\', \'aria-labelledby\': uid + \'-label\', \'aria-describedby\': uid + \'-hint\', spellcheck: \'false\' });\n  const wrap = body => \'<div style="font-family:Arial,sans-serif;font-size:12pt;line-height:1.4">\' + body + \'</div>\';\n  const fill = () => {\n    const formatter = window.PrimerStructuredReporting;\n    if (!formatter || !formatter.reportHTML) { editor.textContent = original; return; }\n    const holder = document.createElement(\'div\');\n    holder.innerHTML = formatter.reportHTML(original, template.studyTitle || template.title);\n    editor.innerHTML = holder.firstChild.innerHTML;\n  };\n  fill();\n  const initial = editor.innerHTML;\n  const draftText = () => editor.innerText.replace(/\\u00a0/g, \' \').replace(/\\n+$/, \'\');\n  const format = (command, label, name) => {\n    const control = btn({ class: \'btn ghost small rad-report-format-\' + command, title: name, \'aria-label\': name,\n      onclick: () => { editor.focus(); document.execCommand(command); } }, label);\n    // Keep the selection in the editor when the control is pressed.\n    control.addEventListener(\'mousedown\', event => event.preventDefault());\n    return control;\n  };\n  const toolbar = el(\'div\', { class: \'rad-report-format\', role: \'toolbar\', \'aria-label\': \'Text formatting\' },\n    format(\'bold\', \'B\', \'Bold\'), format(\'italic\', \'I\', \'Italic\'), format(\'underline\', \'U\', \'Underline\'));\n  // Pasted and dropped content arrives as plain text; a new line is a line break, not a new block.\n  editor.addEventListener(\'paste\', event => {\n    event.preventDefault();\n    document.execCommand(\'insertText\', false, (event.clipboardData || window.clipboardData).getData(\'text/plain\'));\n  });\n  editor.addEventListener(\'drop\', event => event.preventDefault());\n  editor.addEventListener(\'keydown\', event => {\n    if (event.key !== \'Enter\' || event.isComposing) return;\n    event.preventDefault();\n    document.execCommand(\'insertLineBreak\');\n  });\n  let action = 0;\n  const reset = btn({ class: \'btn ghost small\', disabled: \'\', onclick: () => {\n    action++;\n    fill();\n    editor.scrollTop = 0;\n    editor.scrollLeft = 0;\n    reset.disabled = true;\n    status.textContent = \'Original template restored. Changes last until you leave or reload this page.\';\n  } }, \'Reset edits\');\n  editor.addEventListener(\'input\', () => {\n    action++;\n    reset.disabled = editor.innerHTML === initial;\n',
         b"  const editor = el('textarea', { id: uid, class: 'rad-report-editor', rows: 22,\n    spellcheck: 'false', autocomplete: 'off', 'aria-describedby': uid + '-hint' });\n  editor.value = original;\n  let action = 0;\n  const reset = btn({ class: 'btn ghost small', disabled: '', onclick: () => {\n    action++;\n    editor.value = original;\n    editor.setSelectionRange(0, 0);\n    editor.scrollTop = 0;\n    editor.scrollLeft = 0;\n    reset.disabled = true;\n    status.textContent = 'Original template restored. Changes last until you leave or reload this page.';\n  } }, 'Reset edits');\n  editor.addEventListener('input', () => {\n    action++;\n    reset.disabled = editor.value === original;\n"),
        (b"    // A line break typed in the editor is a newline character; rich text needs it as a break.\n    const text = draftText(), html = wrap(editor.innerHTML.replace(/\\n/g, '<br>'));\n    copy.disabled = true;\n    status.textContent = 'Copying template text\xe2\x80\xa6';\n    let copied = false;\n    try {\n      if (navigator.clipboard && navigator.clipboard.write && typeof ClipboardItem !== 'undefined') {\n        await navigator.clipboard.write([new ClipboardItem({\n          'text/plain': new Blob([text], { type: 'text/plain' }),\n          'text/html': new Blob([html], { type: 'text/html' }),\n        })]);\n        copied = true;\n      } else if (navigator.clipboard && navigator.clipboard.writeText) {\n        await navigator.clipboard.writeText(text);\n        copied = true;\n      }\n    } catch (e) { /* Insecure contexts and denied clipboard access use selection. */ }\n",
         b"    const text = editor.value;\n    copy.disabled = true;\n    status.textContent = 'Copying template text\xe2\x80\xa6';\n    let copied = false;\n    try {\n      if (navigator.clipboard && navigator.clipboard.writeText) {\n        if (window.PrimerStructuredReporting) await window.PrimerStructuredReporting.copyReport(text, template.studyTitle || template.title);\n        else await navigator.clipboard.writeText(text);\n        copied = true;\n      }\n    } catch (e) { /* Insecure contexts and denied clipboard access use selection. */ }\n"),
        (b"      const priorFocus = document.activeElement;\n      const selection = window.getSelection();\n      const prior = selection.rangeCount ? selection.getRangeAt(0) : null;\n      const all = document.createRange();\n      all.selectNodeContents(editor);\n      editor.focus();\n      selection.removeAllRanges();\n      selection.addRange(all);\n      try { copied = !!document.execCommand && document.execCommand('copy'); } catch (e) { /* Manual copy remains available. */ }\n      if (copied) {\n        selection.removeAllRanges();\n        if (prior) selection.addRange(prior);\n        if (priorFocus && priorFocus.focus) priorFocus.focus();\n      }\n",
         b"      const priorFocus = document.activeElement;\n      const selection = [editor.selectionStart, editor.selectionEnd, editor.selectionDirection];\n      editor.focus();\n      editor.select();\n      try { copied = !!document.execCommand && document.execCommand('copy'); } catch (e) { /* Manual copy remains available. */ }\n      if (copied) {\n        editor.setSelectionRange(...selection);\n        if (priorFocus && priorFocus.focus) priorFocus.focus();\n      }\n"),
        (b"    status.textContent = copied\n      ? 'Current template copied with its formatting.'\n",
         b"    status.textContent = copied\n      ? 'Current template text copied.'\n"),
        (b"      url = URL.createObjectURL(new Blob([draftText()], { type: 'text/plain;charset=utf-8' }));",
         b"      url = URL.createObjectURL(new Blob([editor.value], { type: 'text/plain;charset=utf-8' }));"),
        (b"      status.textContent = 'Download requested: ' + base + '.txt. The file contains the current editor text without formatting.';",
         b"      status.textContent = 'Download requested: ' + base + '.txt. The file contains the current editor text.';"),
        (b"  content.append(hint, el('p', { id: uid + '-label', class: 'rad-report-label' }, 'Report text \xe2\x80\x94 ' + (template.title || 'template')),\n    toolbar, editor, el(",
         b"  content.append(hint, el('label', { for: uid, class: 'rad-report-label' }, 'Report text \xe2\x80\x94 ' + (template.title || 'template')),\n    editor, el("),
    )),
    'web/radiology-structured.css': ('aa0cdb0c82544dac1c0a25120246d1164664d2755adc90a71cd3570ec01b8607', 'c7fa85e6df72ddc8408879728269d9a7ecd1e37b9c61355ea25e4790c03aa16b', (
        (b'.rad-report-text { font: 12pt/1.4 Arial, sans-serif !important; }\n.rad-report-rich {\n  font: 12pt/1.4 Arial, sans-serif; white-space: pre-wrap; overflow-wrap: anywhere;\n  overflow: auto; height: 60vh; max-height: 90vh; cursor: text;\n}\n.rad-report-rich:focus-visible { outline: 2px solid currentColor; outline-offset: 1px; }\n.rad-report-format { display: flex; gap: 6px; margin: 0 0 8px; }\n.rad-report-format .btn { min-width: 34px; font: 600 14px/1.2 Arial, sans-serif; }\n.rad-report-format-italic { font-style: italic !important; }\n.rad-report-format-underline { text-decoration: underline; }',
         b'.rad-report-text { font: 12pt/1.4 Arial, sans-serif !important; }'),
    )),
}


def before_template_editor_bytes(path, raw):
    row = TEMPLATE_EDITOR.get(str(path))
    if not row or hashlib.sha256(raw).hexdigest() != row[1]:
        return raw
    restored = raw
    for current, previous in row[2]:
        if restored.count(current) != 1:
            raise ValueError('Template editor inverse literal is not unique')
        restored = restored.replace(current, previous, 1)
    if hashlib.sha256(restored).hexdigest() != row[0]:
        raise ValueError('Template editor changed unrelated bytes')
    return restored
