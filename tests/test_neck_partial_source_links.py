"""Only exact, navigable source-specific roles become partial references."""
from copy import deepcopy
from collections import Counter
import json
from pathlib import Path
import subprocess

import pytest
from tools.anatomy_sources import neck_source_links as links
from tools.anatomy_sources.build_soft_tissue_neck_inventory import read as inventory_read, OUTPUT as INVENTORY
from tools.audit_structure_coverage import representation_counts

ROOT = Path(__file__).resolve().parents[1]


def test_reviewed_links_match_exact_targets_sides_representations_and_source_objects():
    data = links.validate(links.read(ROOT / links.OUTPUT))
    assert len(data['links']) == 20
    assert Counter(row['representation'] for row in data['links']) == {'clinical_image': 2, 'model': 10, 'schematic': 8}
    targets = {row['id']: row for row in inventory_read(INVENTORY)['anatomical_requirements']}
    objects = {row['label']: row for row in links.read(ROOT / links.ZANATOMY / 'surfaces.json')}
    for row in data['links']:
        target = targets[row['requirement_id']]
        assert row['side'] == target['laterality'] and row['anatomy_role'] == target['tissue_class']
        assert row['status'] == 'partial'
        assert row['complete_extent'] is row['clinical_approval'] is row['current_patient_registration'] is False
        if row['source_id'] == 'zanatomy-salivary':
            actual = objects[row['source_structure_id']]
            assert (actual['side'], actual['name'], actual['sourceObject']) == (row['side'], row['source_name'], row['source_object'])
            assert row['href'].endswith('#surface' if row['representation'] == 'model' else '#section')
        else:
            assert row['source_id'] == 'segthy-001' and row['source_label'] == 1
            assert row['requirement_id'] in ['neck_us.thyroid_lobe.left', 'neck_us.thyroid_lobe.right']
            assert row['representation'] in ['clinical_image', 'model']
    assert not any('carotid' in row['requirement_id'] or 'jugular' in row['requirement_id'] or 'isthmus' in row['requirement_id'] for row in data['links'])
    assert not any(row['source_id'] in ['salivary-us-2025', 'cervical-node-figures'] for row in data['links'])


@pytest.mark.parametrize('change', ['side', 'structure', 'role', 'representation', 'selector', 'metadata', 'complete', 'approval', 'photo'])
def test_a_changed_or_stronger_match_cannot_gain_partial_credit(change):
    data = deepcopy(links.read(ROOT / links.OUTPUT)); row = data['links'][0]
    if change == 'side': row['side'] = 'left' if row['side'] == 'right' else 'right'
    elif change == 'structure': row['requirement_id'] = 'neck_us.common_carotid.right'
    elif change == 'role': row['anatomy_role'] = 'duct_lumen'
    elif change == 'representation': row['representation'] = 'clinical_image'
    elif change == 'selector': row['href'] = row['href'].replace('structure=', 'unsupported=')
    elif change == 'metadata': row['source_metadata_sha256'] = '0' * 64
    elif change == 'complete': row['status'] = 'complete'
    elif change == 'approval': row['clinical_approval'] = True
    else: row['source_id'] = 'salivary-us-2025'
    with pytest.raises(ValueError, match='exact reviewed'):
        links.validate(data)


def test_partial_records_reclassify_source_presence_without_changing_strict_fidelity_or_clinical_approval():
    data = links.validate(links.read(ROOT / links.OUTPUT))
    rows = [{'structure_id': row['requirement_id'], 'kind': row['representation'], 'status': 'missing', 'candidates': {}}
            for row in data['links']]
    original = deepcopy(rows)
    marked = links.apply_partial_sources(rows, data['links'])
    assert rows == original
    assert all(row['status'] == 'partial' and row['complete_fidelity_status'] == 'missing' and row['source_links'] for row in marked)
    for kind in ['clinical_image', 'model', 'schematic']:
        result = representation_counts(marked, kind)
        assert result['partial'] == result['required'] and result['verified'] == result['missing'] == 0
        assert result['complete_set'] is False and result['explicitly_bound'] == 0
    marked = links.apply_partial_sources([dict(rows[0], status='verified')], data['links'])
    assert marked[0]['status'] == 'verified' and marked[0]['source_links']


def test_native_sweep_selection_is_literal_per_volume_and_defaults_remain_unchanged():
    script = '''import assert from 'node:assert/strict';
import fs from 'node:fs';
import {sourceSelection} from './web/anatomy/segthy-001/source-selection.mjs';
const cases=JSON.parse(fs.readFileSync('./web/anatomy/segthy-001/manifest.json')).cases;
assert.equal(sourceSelection('',cases),null);assert.equal(sourceSelection('?from=neck',cases),null);
for(const row of cases)for(const label of row.labels){
 const query='?volume='+row.id+'&label='+label.code;
 assert.deepEqual(sourceSelection(query,cases),{volume:row.id,label:label.code,representation:null});
 for(const representation of ['clinical_image','model'])assert.equal(sourceSelection(query+'&representation='+representation,cases).representation,representation);
}
for(const query of ['?label=1','?volume=unknown&label=1','?volume=001_P1_1_left&label=4','?volume=001_P1_1_left&label=01','?volume=001_P1_1_left&label=1.0','?volume=001_P1_1_left&label=1&label=2','?volume=001_P1_1_left&volume=001_P1_1_right&label=1','?volume=001_P1_1_left&label=1&representation=schematic','?volume=001_P1_1_left&label=1&representation=model&representation=clinical_image'])assert.throws(()=>sourceSelection(query,cases),/released source sweep and label/);
'''
    result = subprocess.run(['node', '--input-type=module', '-e', script], cwd=ROOT, text=True, capture_output=True)
    assert result.returncode == 0, result.stdout + result.stderr
