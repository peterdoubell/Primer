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
