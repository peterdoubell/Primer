"""Per-station reading aids retain exact source node IDs and literal assignments."""
import json
from pathlib import Path
import shutil
import subprocess

from tools.anatomy_sources.lynos_station_locators import source_examples, refresh, STUDIES
from tools.lynos_station_locator_compatibility import before_lynos_station_locator_bytes

ROOT = Path(__file__).resolve().parents[1]
ATLAS = 'web/radiology/structure-atlas'
OMITTED = {12, 14, 19, 21, 26}


def test_station_locators_match_only_the_reviewed_original_primary_ids():
    examples, context = source_examples(ROOT)
    source = json.loads((ROOT / 'web/anatomy/lynos-pat9/source.json').read_text())
    nodes = {row['label']: row for row in source['nodalLabels']}
    index = json.loads((ROOT / ATLAS / 'index.json').read_text())
    assert len(examples) == 30
    assert context['whole_station_boundaries_represented'] is False
    assert {entry['sourceMaskValue'] for entry in context['omitted_primary_assignments']} == OMITTED
    for study in STUDIES:
        path = f"{ATLAS}/locators/{study.removeprefix('ra.')}.json"
        data = json.loads((ROOT / path).read_text())
        original = json.loads(before_lynos_station_locator_bytes(path, (ROOT / path).read_bytes()))
        assert data['counts'] == original['counts']
        original_rows = {row['id']: row for row in original['structures']}
        ids = set()
        matches = [row for row in data['structures'] if row.get('native_examples')]
        assert len(matches) == 15
        for row in data['structures']:
            assert {key: value for key, value in row.items() if key != 'native_examples'} == original_rows[row['id']]
            if 'native_examples' not in row:
                continue
            assert row['native_examples'] == examples[row['id']]
            for entry in row['native_examples']:
                label = entry['source_node_id']
                ids.add(label)
                node = nodes[label]
                assert entry['primary_station'] == node['primaryStationLiteral']
                assert entry['secondary_station'] == node['secondaryStationLiteral']
                assert entry['tertiary_station'] == node['tertiaryStationLiteral']
                assert entry['ct_url'] == f'/app/anatomy/lynos-pat9/index.html?node={label}'
                assert entry['model_url'] == f'/app/anatomy/lynos-pat9/surfaces.html?node={label}'
        assert ids == set(range(1, 45)) - OMITTED
        current, = [row for row in index['investigations'] if row['investigation_id'] == study]
        assert current['native_example_rows'] == 15
        assert current['located_structures'] == len([
            row for row in data['structures'] if row.get('atlas') or row.get('radiology_assistant') or row.get('native_examples')
        ])


def test_station_refresh_preserves_other_source_matches_and_display_labels(tmp_path):
    files = [
        f'{ATLAS}/index.json',
        *(f"{ATLAS}/locators/{study.removeprefix('ra.')}.json" for study in STUDIES),
        'web/anatomy/lynos-pat9/source.json',
        'docs/lynos-pat9-source-review/pat9-primary-station-crosswalk.json',
        'docs/lynos-pat9-source-review/pat9-station-geometry-audit.json',
    ]
    for file in files:
        target = tmp_path / file
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / file, target)
    name = tmp_path / ATLAS / 'locators/ct-mediastinum.json'
    data = json.loads(name.read_text())
    example = next(row for row in data['structures'] if row.get('native_examples'))
    example['name'] = 'Updated display label'
    example['radiology_assistant'] = [{'url': 'https://radiologyassistant.nl/chest/mediastinum/example#heading'}]
    name.write_text(json.dumps(data))
    assert refresh(tmp_path)['station_requirement_rows'] == 30
    changed = json.loads(name.read_text())
    current = next(row for row in changed['structures'] if row['id'] == example['id'])
    assert current['name'] == example['name'] and current['radiology_assistant'] == example['radiology_assistant']
    assert refresh(tmp_path)['changed'] == []


def test_native_urls_and_filters_include_node_sources_without_open_redirects():
    script = """
const assert = require('node:assert/strict');
const L = require('./web/radiology/structure-atlas/lab.js');
const row = {name:'IASLC station 3A', native_examples:[{source_node_id:39,primary_station:'3a - Prevascular'}]};
assert.equal(L.visible(row,'node 39',true), true);
assert.equal(L.visible(row,'PREVASCULAR',false), true);
assert.equal(L.visible({name:'IASLC station 11L'},'',true), false);
assert.equal(L.nativeUrl('/app/anatomy/lynos-pat9/index.html?node=39'),'/app/anatomy/lynos-pat9/index.html?node=39');
for (const href of [
  'https://evil.example/index.html?node=39',
  '/app/anatomy/lynos-pat9/index.html?node=0',
  '/app/anatomy/lynos-pat9/index.html?node=45',
  '/app/anatomy/lynos-pat9/index.html?node=39&next=https://evil.example',
]) assert.equal(L.nativeUrl(href), null);
"""
    result = subprocess.run(['node', '-e', script], cwd=ROOT, capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
