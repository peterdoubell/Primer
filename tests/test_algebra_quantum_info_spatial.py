"""Actual engine primitives and assessed lesson bindings, not pass-flag approval."""
import json
import math
import subprocess
from functools import lru_cache
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@lru_cache(maxsize=1)
def observations():
    result = subprocess.run(['node', 'tools/check_algebra_quantum_info_spatial.js', '--fixtures'], cwd=ROOT, capture_output=True, text=True, check=True)
    return json.loads(result.stdout)


def test_actual_engine_mapping_all_stations_and_negative_corruptions():
    result = subprocess.run(['node', 'tools/check_algebra_quantum_info_spatial.js'], cwd=ROOT, capture_output=True, text=True, check=True)
    report = json.loads(result.stdout)
    assert report['status'] == 'passed'
    assert report['algebraStations'] == 8 and report['quantumStations'] == 7
    assert report['algebraStates'] > 500 and report['quantumStates'] > 300
    for required in ['table coordinate corruption', 'named graph edge corruption', 'continuous integer join rejection', 'Bloch xyz corruption', 'complex coefficient corruption', 'sixteen-digit probability gain corruption', 'subnormal mixed-state calibration finite', 'full active/inactive bus and exclusion', 'AND/OR visible controls']:
        assert required in report['regressions']


def test_actual_assessment_bindings_cover_twenty_quiz_rows_and_keep_authored_chsh():
    maths = json.loads((ROOT/'data/curriculum/01-mathematics.json').read_text())['nodes']
    physics = json.loads((ROOT/'data/curriculum/03-physics.json').read_text())['nodes']
    algebra = next(n for n in maths if n['id']=='math.5.abstract')
    quantum = next(n for n in physics if n['id']=='phys.5.quantum-info')
    assert len(algebra['quiz']) == len(quantum['quiz']) == 10
    manifest = json.loads((ROOT/'data/module-models.json').read_text())['models']
    for node, family, renderer, scenario in [
        (algebra, 'algebra-operation-geometry', 'math-algebra-lab', 'math.5.abstract.groups-rings-fields'),
        (quantum, 'quantum-information-geometry', 'physics-quantum-info-lab', 'phys.5.quantum-info.qubits-circuits-resources'),
    ]:
        assert next(m for m in manifest if m['node_id']==node['id'])['family'] == family
        assert [m['props'] for m in node['lesson_media'] if m.get('renderer')==renderer] == [dict(scenario=scenario)]
    assert any(m.get('renderer')=='physics-concept-lab' and m['props']==dict(scenario='phys.5.quantum-info') for m in quantum['lesson_media'])
    # Explicit assessed model states: the count alone is not a fidelity proof.
    observed = observations()
    by_station = {s['state']['station']:s for s in observed['algebra']}
    assert len(by_station['A3']['algebra']['active']['orderFour']) == 6
    assert by_station['A4']['algebra']['active']['solutions'] == [0, 4, 8]
    assert by_station['A5']['algebra']['active']['injective'] is True
    assert by_station['A5']['algebra']['active']['onto'] is False
    assert by_station['A6']['algebra']['active']['admissible3'] == [1]
    assert by_station['A6']['algebra']['active']['admissible5'] == [1]
    assert by_station['A7']['algebra']['active']['normal'] is True
    assert by_station['A8']['algebra']['active']['injective'] is True
    by_mode = {s['state']['mode']:s for s in observed['quantum']}
    assert by_mode['register']['quantumInfo']['current']['dimension'] == 4096
    assert len(by_mode['teleportation']['quantumInfo']['current']['branches']) == 4
    assert by_mode['grover']['quantumInfo']['current']['optimalIterations'] == 7853
    assert by_mode['noise']['quantumInfo']['current']['noiseEvents'] == 200


def test_table_coordinates_are_categorical_slots_for_every_actual_cell():
    for scene in observations()['algebra']:
        for panel in scene['algebra']['panels']:
            if panel['kind'] != 'table':
                continue
            table = panel['source']['table']
            values = list(dict.fromkeys(v for row in table for v in row))
            for cell in panel['cells']:
                i, j = cell['row'], cell['column']
                result = table[i][j]
                expected = [4*i/max(1, len(table)-1), 4*j/max(1, len(table[0])-1),
                            7*panel['index']+3*values.index(result)/max(1, len(values)-1)]
                primitive = next(p for p in scene['primitives'] if p.get('fidelity_kind')=='operation_cell' and p['row']==i and p['column']==j)
                assert primitive['points'][0] == pytest.approx(expected, abs=2e-14)
                assert primitive['value'] == result
                assert cell['outputOrdinal'] == values.index(result)
            assert 'categorical' in scene['note']


def test_full_complex_bloch_coordinates_and_corrected_teleportation_mapping():
    np = pytest.importorskip('numpy')
    for scene in observations()['quantum']:
        if scene['state']['mode'] not in ['qubit', 'teleportation']:
            continue
        s, info = scene['state'], scene['quantumInfo']
        t, p, chi = map(math.radians, [s['thetaDeg'], s['phiDeg'], s['globalPhaseDeg']])
        psi = np.exp(1j*chi)*np.array([math.cos(t/2), np.exp(1j*p)*math.sin(t/2)])
        input_bloch = [2*(psi[0].conjugate()*psi[1]).real, 2*(psi[0].conjugate()*psi[1]).imag,
                       abs(psi[0])**2-abs(psi[1])**2]
        vector = info['geometry']['blochVectors'][0]
        assert [vector[k] for k in ['x', 'y', 'z']] == pytest.approx(input_bloch, abs=3e-15)
        endpoint = next(q for q in scene['primitives'] if q.get('fidelity_kind')=='bloch_endpoint' and q['key']=='input')
        assert endpoint['points'][0] == pytest.approx([input_bloch[0], 2+input_bloch[1], input_bloch[2]], abs=3e-15)
        if s['mode']=='teleportation':
            local = next(q for q in scene['primitives'] if q.get('fidelity_kind')=='bloch_endpoint' and q['key']=='bob-local')
            assert local['points'][0] == pytest.approx([3.2, 2, 0], abs=3e-15)
            for branch in info['current']['branches']:
                corrected = [complex(q['re'], q['im']) for q in branch['corrected']]
                assert corrected == pytest.approx(psi, abs=3e-15)
                assert branch['fidelity'] == pytest.approx(abs(np.vdot(psi, corrected))**2, abs=3e-15)
            messages = [q for q in scene['primitives'] if q.get('fidelity_kind')=='classical_message']
            assert len(messages) == 2
            assert {q['from'] for q in messages} == {0, 1}
            assert all(q['target']==2 for q in messages)


def test_twelve_qubit_mixed_view_retains_all_probabilities_and_sixty_four_last_page_rows():
    scene = next(q for q in observations()['quantum'] if q['state']['mode']=='noise')
    s, info = scene['state'], scene['quantumInfo']
    rows = info['geometry']['amplitudes']
    assert len(rows) == 4096
    assert info['calibration']['start'] == 4032 and info['calibration']['visible'] == 64
    p1 = math.sin(math.radians(s['thetaDeg'])/2)**2
    weight = (1-s['errorP'])**s['noiseRounds']
    for row in rows:
        count = row['basis'].count('1')
        pure = p1**count*(1-p1)**(12-count)
        expected = weight*pure+(1-weight)/4096
        assert row['probability'] == pytest.approx(expected, abs=3e-16)
        assert row['densityDiagonal'] is True
        assert 're' not in row and 'im' not in row
    assert sum(row['probability'] for row in rows) == pytest.approx(1, abs=3e-13)
    points = [q for q in scene['primitives'] if q.get('fidelity_kind')=='density_probability' and q['kind']=='sphere']
    assert len(points) == 64
    for point in points:
        row = rows[point['index']]
        assert point['points'][0] == pytest.approx([6*point['index']/4095,
            -2+row['probability']*info['calibration']['valueGain'], 0], abs=3e-14)
    assert not any(q.get('fidelity_kind')=='imaginary_axis' for q in scene['primitives'])


def test_large_domain_grover_uses_two_calibrated_aggregate_slots_and_last_iteration():
    scene = next(q for q in observations()['quantum'] if q['state']['mode']=='grover')
    s, info = scene['state'], scene['quantumInfo']
    theta = math.asin(1/math.sqrt(s['searchN']))
    assert s['searchN'] == 100000000
    assert len(info['geometry']['amplitudes']) == 2
    assert info['calibration']['indexScale'] == 1
    for i, point in enumerate(info['geometry']['trajectories'][0]['points']):
        angle = (2*s['iterations']-1)*theta+2*theta*i/64
        assert [point['x'], point['y'], point['z']] == pytest.approx([math.cos(angle), math.sin(angle), 0], abs=3e-15)
    assert info['current']['actual'] is None
    assert 'not N individual database amplitudes' in scene['readout']


@pytest.mark.parametrize(('node_id', 'family', 'former_family'), [
    ('math.5.abstract', 'algebra-operation-geometry', 'number-line-object'),
    ('phys.5.quantum-info', 'quantum-information-geometry', 'quantum-computer'),
])
def test_runtime_curriculum_attaches_exact_companions_and_rejects_family_corruption(node_id, family, former_family):
    import copy
    from primer.curriculum import Curriculum, _validate_lesson_media
    node = copy.deepcopy(Curriculum().node(node_id))
    model = next(m for m in node['lesson_media'] if m.get('renderer')=='spatial-3d' and m['props']['scenario']=='module.'+node_id)
    assert model['props']['family'] == family
    assert model['props']['mode'] == 'model'
    _validate_lesson_media(node)
    model['props']['family'] = former_family
    with pytest.raises(ValueError, match='module spatial'):
        _validate_lesson_media(node)


def test_actual_browser_load_order_presents_cores_bus_adapters_and_registry():
    shell = (ROOT/'web/index.html').read_text()
    registry = shell.index('/app/lesson-models.js')
    engine = shell.index('/app/spatial-module-objects.js')
    bus = shell.index('/app/lesson-state.js')
    for adapter, core in [('spatial-algebra.js', 'math-algebra-lab.js'), ('spatial-quantum-information.js', 'physics-quantum-info-lab.js')]:
        assert shell.index('/app/'+adapter) < engine < registry
        assert bus < shell.index('/app/'+core) < registry
