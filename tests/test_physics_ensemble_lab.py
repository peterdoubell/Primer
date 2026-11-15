"""Independent Python exact/Fraction and decimal statistical-physics oracles."""
import copy
from decimal import Decimal, localcontext
from fractions import Fraction
import json
import math
from pathlib import Path
import shutil
import subprocess

import pytest
from primer.curriculum import Curriculum, _validate_lesson_media

ROOT = Path(__file__).resolve().parents[1]
NODE = shutil.which('node')


def models(cases):
    if NODE is None:
        pytest.skip('Node required for actual browser model source')
    result = subprocess.run([NODE, 'tools/check_physics_ensemble_lab.js', '--oracle-json'],
                            input=json.dumps(cases), cwd=ROOT, capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stdout + result.stderr
    return json.loads(result.stdout)


def test_exact_binomial_fraction_entropy_and_complete_microstates():
    cases = [{'mode': 'coins', 'N': n, 'j': n // 2} for n in [1, 3, 4, 8, 64, 1000, 1024]]
    for case, model in zip(cases, models(cases)):
        n = case['N']
        assert int(model['totalStates']) == 2 ** n
        assert sum(int(r['omega']) for r in model['rows']) == 2 ** n
        for row in model['rows']:
            count = math.comb(n, row['j'])
            assert int(row['omega']) == count
            exact_probability = Fraction(count, 2 ** n)
            assert row['probability']['value'] == pytest.approx(float(exact_probability), rel=2e-12, abs=1e-300)
            assert row['macroLogP'] == pytest.approx(math.log(count) - n * math.log(2), abs=2e-12)
        assert model['microGibbsOverK'] == pytest.approx(n * math.log(2))
        assert model['entropyDecompositionResidual'] == pytest.approx(0, abs=1e-10)
        assert model['pUpper'] == model['upperProbability']['value'] == .5
        assert model['gibbsOverK'] == pytest.approx(math.log(2))
        if n <= 8:
            assert [s['bits'] for s in model['enumeration']] == [format(i, f'0{n}b') for i in range(2 ** n)]
    three, four = models([{'mode': 'coins', 'N': 3, 'j': 1}, {'mode': 'coins', 'N': 4, 'j': 2}])
    assert [s['bits'] for s in three['enumeration'] if s['j'] == 1] == ['001', '010', '100']
    assert three['microGibbsOverK'] == pytest.approx(math.log(8))
    assert four['multiplicityOverK'] == pytest.approx(math.log(6))
    assert four['macroGibbsOverK'] == pytest.approx(1.407531740719315)
    assert four['microGibbsOverK'] == pytest.approx(math.log(16))


def test_decimal_canonical_normalization_tiny_population_and_entropy():
    cases = [{'temperature': t, 'gap': g} for t in [1, 300, 1200] for g in [0, 1e-16, 4.141947, 100]]
    with localcontext() as context:
        context.prec = 80
        k = Decimal('1.380649e-23')
        for model in models(cases):
            t, gap = Decimal(str(model['state']['temperature'])), Decimal(str(model['state']['gap'])) * Decimal('1e-21')
            x = gap / (k * t)
            factor = (-x).exp()
            p1, p0 = factor / (1 + factor), 1 / (1 + factor)
            entropy = -p0 * p0.ln() - p1 * p1.ln()
            assert model['pUpper'] == pytest.approx(float(p1), rel=2e-13)
            assert model['populationRatio']['value'] == pytest.approx(float(factor), rel=2e-13)
            assert model['gibbsOverK'] == pytest.approx(float(entropy), rel=2e-13)
            assert model['meanEnergyJ'] == pytest.approx(float(gap * p1), rel=2e-13)
            assert model['pUpper'] > 0 and model['gibbsOverK'] > 0
    actual = models([{}])[0]
    assert actual['populationRatio']['value'] == pytest.approx(math.exp(-1))
    assert actual['pUpper'] == pytest.approx(1 / (1 + math.e))
    assert actual['populationRatio']['value'] != actual['pUpper']


def test_logarithmic_finite_probability_and_free_expansion_energy_boundary():
    tail, gas, unchanged = models([
        {'mode': 'particles', 'temperature': 1, 'gap': 100, 'N': 1024, 'j': 1024},
        {'mode': 'expansion', 'log10N': 25, 'volumeRatio': 2},
        {'mode': 'expansion', 'log10N': 25, 'volumeRatio': 1},
    ])
    assert tail['macroProbability']['value'] is None
    assert tail['macroProbability']['positive'] and math.isfinite(tail['macroLogP'])
    assert tail['microGibbsOverK'] > 0
    assert int(gas['particleCount']) == 10 ** 25
    assert gas['allInOriginalProbability']['value'] is None
    assert gas['allInOriginalProbability']['positive']
    assert gas['logP'] == pytest.approx(-(10 ** 25) * math.log(2))
    assert gas['entropyJPerK'] == pytest.approx(1.380649e-23 * 10 ** 25 * math.log(2))
    assert [gas[k] for k in ['Q', 'Wby', 'deltaU', 'deltaT']] == [0, 0, 0, 0]
    assert gas['pressureRatio'] == .5
    assert unchanged['allInOriginalProbability']['value'] == 1 and unchanged['entropyOverK'] == 0


def test_independent_counts_entropy_quadrature_and_mounted_controls():
    if NODE is None:
        pytest.skip('Node required')
    result = subprocess.run([NODE, 'tools/check_physics_ensemble_lab.js'], cwd=ROOT,
                            capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stdout + result.stderr
    assert 'independent exact factorial counts' in result.stdout
    assert 'independent entropy quadratures' in result.stdout
    assert 'mounted physical-coordinate states' in result.stdout


def test_statmech_renderer_is_bound_to_only_the_authored_scenario():
    node = copy.deepcopy(Curriculum().node('phys.4.statmech'))
    model = next(m for m in node['lesson_media'] if m.get('renderer') == 'physics-ensemble-lab')
    assert model['props'] == {'scenario': 'phys.4.statmech.ensembles-entropy'}
    _validate_lesson_media(node)
    other_lesson = copy.deepcopy(Curriculum().node('phys.3.thermo'))
    other_lesson['lesson_media'].append(copy.deepcopy(model))
    with pytest.raises(ValueError, match='ensemble'):
        _validate_lesson_media(other_lesson)
    model['props']['extra'] = True
    with pytest.raises(ValueError, match='ensemble'):
        _validate_lesson_media(node)
    model['props'] = {'scenario': 'phys.3.thermo.cycle-entropy'}
    with pytest.raises(ValueError, match='ensemble'):
        _validate_lesson_media(node)


def test_ensemble_shell_loads_dependency_before_renderer_registry():
    shell = (ROOT / 'web/index.html').read_text()
    assert shell.index('/app/physics-ensemble-lab.js') < shell.index('/app/lesson-models.js')
    assert '/app/physics-ensemble-lab.css' in shell
