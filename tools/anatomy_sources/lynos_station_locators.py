"""Append reviewed individual LyNoS node examples to the two station locators."""
from hashlib import sha256
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STUDIES = ('ra.ct-mediastinum', 'ra.ct-lung-cancer')
PREFIX = '/app/anatomy/lynos-pat9/'
NOTE = ('These examples link the authors’ primary station terms to individual Pat9 masks under '
        'their IASLC 2009 scheme. The source retains secondary and tertiary assignments. '
        'Whole-station region boundaries remain unrepresented by these node masks.')


def source_examples(root):
    review = root / 'docs/lynos-pat9-source-review'
    crosswalk = json.loads((review / 'pat9-primary-station-crosswalk.json').read_text())
    original = review / 'pat9-station-geometry-audit.json'
    if sha256(original.read_bytes()).hexdigest() != crosswalk['sourceAuditSha256']:
        raise ValueError('The reviewed LyNoS station crosswalk source changed')
    source = json.loads((root / 'web/anatomy/lynos-pat9/source.json').read_text())
    nodes = {row['label']: row for row in source['nodalLabels']}
    if set(nodes) != set(range(1, 45)):
        raise ValueError('LyNoS original node identifiers changed')
    rows = {}
    matched = set()
    for code, entry in crosswalk['directlyMatchedPrimaryCodes'].items():
        examples = []
        for label in entry['originalMaskValues']:
            node = nodes[label]
            literal = node['primaryStationLiteral']
            if literal.split(' - ', 1)[0].lower() != code or label in matched:
                raise ValueError('LyNoS primary station identity differs')
            matched.add(label)
            examples.append({
                'source_node_id': label,
                'primary_station': literal,
                'secondary_station': node['secondaryStationLiteral'],
                'tertiary_station': node['tertiaryStationLiteral'],
                'ct_url': PREFIX + 'index.html?node=' + str(label),
                'model_url': PREFIX + 'surfaces.html?node=' + str(label),
            })
        for identifier in entry['investigationStructureIds']:
            rows[identifier] = examples
    omitted = crosswalk['sourceAssignmentsWithOtherLiteralCodesOrDiscrepancies']
    if (len(rows) != 30 or len(matched) != 39
            or matched | {row['sourceMaskValue'] for row in omitted} != set(nodes)):
        raise ValueError('LyNoS primary station crosswalk scope changed')
    return rows, {
        'name': 'LyNoS Pat9 individual node examples',
        'source_url': crosswalk['sourceRecordURL'],
        'license': 'CC BY 4.0',
        'license_url': 'https://creativecommons.org/licenses/by/4.0/',
        'note': NOTE,
        'whole_station_boundaries_represented': False,
        'omitted_primary_assignments': omitted,
    }


def refresh(root=ROOT):
    """Update this source only, preserving names, atlas matches and article matches."""
    atlas = root / 'web/radiology/structure-atlas'
    index_file = atlas / 'index.json'
    index = json.loads(index_file.read_text())
    examples, context = source_examples(root)
    changed = []
    expected = {key for key in examples}
    for study in STUDIES:
        target = atlas / 'locators' / (study.removeprefix('ra.') + '.json')
        data = json.loads(target.read_text())
        if data['investigation_id'] != study:
            raise ValueError('LyNoS locator investigation changed')
        selected = 0
        total = 0
        for row in data['structures']:
            matches = examples.get(row['id'])
            if matches:
                expected.remove(row['id'])
                row['native_examples'] = matches
                selected += 1
            elif 'native_examples' in row:
                raise ValueError('An unreviewed native example already exists')
            total += bool(row.get('atlas') or row.get('radiology_assistant') or matches)
        if selected != 15:
            raise ValueError('LyNoS matching station requirements are missing')
        data['native_source'] = context
        encoded = json.dumps(data, indent=1, sort_keys=True) + '\n'
        if target.read_text() != encoded:
            target.write_text(encoded)
            changed.append(str(target.relative_to(root)))
        item, = [row for row in index['investigations'] if row['investigation_id'] == study]
        item['native_example_rows'] = selected
        item['located_structures'] = total
    if expected:
        raise ValueError('LyNoS station crosswalk did not match the complete locator scope')
    encoded = json.dumps(index, indent=1, sort_keys=True) + '\n'
    if index_file.read_text() != encoded:
        index_file.write_text(encoded)
        changed.append(str(index_file.relative_to(root)))
    return {'station_requirement_rows': len(examples), 'original_node_ids': 39, 'changed': changed}


if __name__ == '__main__':
    print(json.dumps(refresh()))
