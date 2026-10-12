"""Actual educational QFT contracts and independent finite-model checks."""
import copy
import hashlib
import json
import subprocess
from pathlib import Path

import pytest

from primer.curriculum import Curriculum, _validate_lesson_media

ROOT = Path(__file__).resolve().parents[1]


def test_independent_scientific_oracles_and_actual_adapter_coordinates():
    result = subprocess.run(['node', 'tools/check_physics_qft_independent.js'], cwd=ROOT,
                            capture_output=True, text=True, check=True, timeout=30)
    record = json.loads(result.stdout)
    assert record['status'] == 'pass'
    assert record['comparisons'] > 38000
    assert record['counts']['elastic_com_states'] == 72
    assert record['counts']['actual_spatial_adapter_states'] == 27
    assert record['standingFaces'] == 11036
    for field, name in [('runtime_sha256', 'web/physics-qft-lab.js'),
                        ('spatial_sha256', 'web/spatial-qft.js'),
                        ('check_sha256', 'tools/check_physics_qft_independent.js')]:
        assert record[field] == hashlib.sha256((ROOT/name).read_bytes()).hexdigest()


def test_mounted_all_stations_calibrated_curves_and_exact_drafts():
    result = subprocess.run(['node', 'tools/check_physics_qft_lab.js'], cwd=ROOT,
                            capture_output=True, text=True, check=True, timeout=30)
    assert '109 mounted QFT states' in result.stdout
    assert '317 calibrated SVG curves' in result.stdout
    assert '27 exact draft/blur/Enter/Escape controls' in result.stdout


def test_full_assessment_node_and_retained_existing_bosonic_example():
    curriculum = Curriculum()
    node = curriculum.node('phys.5.qft')
    assert len(node['quiz']) == 10 and len(node['learning_outcomes']) == 9
    assert set(node['lesson']) == {'overview', 'worked_example', 'activity', 'reflection'}
    models = node['lesson_media']
    assert [m['props'] for m in models if m.get('renderer') == 'physics-qft-lab'] == [
        {'scenario': 'phys.5.qft.fields-observables'}]
    assert any(m.get('renderer') == 'physics-concept-lab' and m['props'] == {'scenario': 'phys.5.qft'} for m in models)
    assert any(m.get('props', {}).get('family') == 'qft-observable-geometry' for m in models)
    assert node['quiz'][3]['answer'] == '2.43'
    assert node['quiz'][6]['answer'] == '0.7'
    assert node['quiz'][7]['answer'] == '1'
    assert 'tree level' in node['quiz'][1]['explain']
    assert 'Finite cutoff' in node['quiz'][9]['explain']


@pytest.mark.parametrize('mutation', ['lesson', 'scenario', 'extra'])
def test_strict_renderer_rejects_cross_lesson_and_unknown_scenario(mutation):
    raw = json.loads((ROOT/'data/curriculum/03-physics.json').read_text())
    node = copy.deepcopy(next(n for n in raw['nodes'] if n['id'] == 'phys.5.qft'))
    model = next(m for m in node['lesson_media'] if m.get('renderer') == 'physics-qft-lab')
    if mutation == 'lesson':
        node['id'] = 'phys.4.quantum'
    elif mutation == 'scenario':
        model['props']['scenario'] = 'phys.5.qft'
    else:
        model['props']['unknown'] = True
    with pytest.raises(ValueError):
        _validate_lesson_media(node)


def test_current_scientific_sources_reconcile_with_frozen_independent_scope():
    review = json.loads((ROOT/'docs/physics-qft-independent-review-20261011.json').read_text())
    amendment = json.loads((ROOT/'docs/physics-qft-independent-amendment-20261011.json').read_text())
    bridge_path = ROOT/'docs/physics-qft-integrated-reader-review-20261011/historical-source-compatibility-amendment.json'
    bridge = json.loads(bridge_path.read_text())
    digest = lambda value: hashlib.sha256(value).hexdigest()
    for record in [bridge['original_review'], bridge['original_amendment'], bridge['current_scientific_amendment']]:
        assert digest((ROOT/record['path']).read_bytes()) == record['sha256']
    assert digest((ROOT/amendment['original_review']['path']).read_bytes()) == amendment['original_review']['sha256']
    for file in ['web/physics-qft-lab.js', 'web/spatial-qft.js', 'tools/check_physics_qft_independent.js']:
        row = bridge['source_history'][file]
        historical = (ROOT/row['historical_copy']).read_bytes()
        expected = amendment['readout_change']['current_adapter_sha256'] if file == 'web/spatial-qft.js' else review['pins'][file]['sha256']
        assert digest(historical) == row['historical_sha256'] == expected
        assert digest((ROOT/file).read_bytes()) == row['current_sha256']
    for file in ['web/physics-qft-lab.css', 'web/illustrations/forest/physics/phys-5-qft-1600.webp']:
        assert digest((ROOT/file).read_bytes()) == review['pins'][file]['sha256']
    text = (ROOT/bridge['source_history']['web/spatial-qft.js']['historical_copy']).read_text()
    change = amendment['readout_change']
    assert text.count(change['new_literal']) == 1
    assert digest(text.replace(change['new_literal'], change['old_literal']).encode()) == change['previous_adapter_sha256'] == review['pins']['web/spatial-qft.js']['sha256']
    current = json.loads((ROOT/bridge['current_scientific_amendment']['path']).read_text())
    inverse_path = ROOT/'docs/number-theory-shared-runtime-amendment-20261012.json'
    inverse = json.loads(inverse_path.read_text())
    assert set(inverse['files']) == {'web/spatial-models.js', 'web/spatial-module-objects.js'}
    assert inverse['original_receipt']['path'] == bridge['current_scientific_amendment']['path']
    assert digest((ROOT/inverse['original_receipt']['path']).read_bytes()) == inverse['original_receipt']['sha256']
    for path, pin in current['current_pins'].items():
        source = (ROOT/path).read_bytes()
        if path in inverse['files']:
            change = inverse['files'][path]
            assert digest(source) == change['current_sha256']
            restored = source.decode()
            for replacement in change['inverse_replacements']:
                assert replacement['occurrences'] == 1
                assert restored.count(replacement['new_literal']) == 1
                restored = restored.replace(replacement['new_literal'], replacement['old_literal'], 1)
            assert digest(restored.encode()) == change['historical_sha256'] == pin
        else:
            assert digest(source) == pin
    assert current['educational_scientific_go'] and not current['browser_reader_approval']
    node = next(n for n in json.loads((ROOT/'data/curriculum/03-physics.json').read_text())['nodes'] if n['id']=='phys.5.qft')
    canonical = json.dumps(node, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()
    assert digest(canonical) == review['curriculum_node']['sha256']
    for record in [review, amendment, current]:
        assert record['full_goal_complete'] is False
        assert record['whole_continuum_qft_approved'] is False
        assert record['clinical_approved'] is False
