"""Independent complex-matrix and probability oracles for the assessed lab."""
import json
import math
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def actual(name, states):
    script = "const l=require('./web/physics-quantum-info-lab.js');const x=JSON.parse(process.argv[1]);process.stdout.write(JSON.stringify(x.map(s=>l[process.argv[2]](s))));"
    result = subprocess.run(['node', '-e', script, json.dumps(states), name], cwd=ROOT, text=True, capture_output=True, check=True)
    return json.loads(result.stdout)


def vector(values):
    return [complex(z['re'], z['im']) for z in values]


def test_independent_checker_calibrated_dom_drafts_and_complete_stations():
    result = subprocess.run(['node', 'tools/check_physics_quantum_info_lab.js'], cwd=ROOT, text=True, capture_output=True, check=True)
    assert '2062 analytic fixtures across 7' in result.stdout
    assert '133 mounted control/preset states' in result.stdout
    assert 'basis paging' in result.stdout


def test_tensor_register_dimension_born_distribution_and_repeat_measurement():
    states = [dict(nQubits=n, preparation=prep, thetaDeg=63, phiDeg=58, measurementOutcome=2**n-1, basisPage=63)
              for n in [1, 3, 10, 12] for prep in ['uniform', 'tensor', 'basis']]
    for s, r in zip(states, actual('registerSnapshot', states)):
        assert r['dimension'] == len(r['amplitudes']) == 2**s['nQubits']
        assert sum(r['probabilities']) == pytest.approx(1, abs=3e-13)
        p1 = math.sin(math.radians(63)/2)**2
        for row in r['amplitudes']:
            ones = row['basis'].count('1')
            expected = (1/2**s['nQubits'] if s['preparation']=='uniform' else
                        p1**ones * (1-p1)**(s['nQubits']-ones) if s['preparation']=='tensor' else
                        1 if row['index']==s['measurementOutcome'] else 0)
            assert row['probability'] == pytest.approx(expected, rel=3e-13, abs=1e-15)
        assert r['repeatProbabilities'][s['measurementOutcome']] == 1
        assert sum(r['repeatProbabilities']) == 1
        assert r['freshPreparationProbabilities'] == r['probabilities']
        assert r['displayStart'] == 64*min(63, (2**s['nQubits']-1)//64)


def test_teleportation_independent_full_three_qubit_matrix_all_phases_and_branches():
    np = pytest.importorskip('numpy')
    H = np.array([[1, 1], [1, -1]], complex)/math.sqrt(2)
    X = np.array([[0, 1], [1, 0]], complex)
    Z = np.diag([1, -1]).astype(complex)
    CX = np.zeros((8, 8), complex)
    for q in range(2):
        for a in range(2):
            for b in range(2):
                CX[4*q+2*(a^q)+b, 4*q+2*a+b] = 1
    circuit = np.kron(np.kron(H, np.eye(2)), np.eye(2))@CX
    bell = np.array([1, 0, 0, 1], complex)/math.sqrt(2)
    states = [dict(thetaDeg=t, phiDeg=p, globalPhaseDeg=g, bellBits=bits, teleportStage='corrected')
              for t, p, g in [(0, 0, 75), (180, 33, -71), (90, 90, 35), (63, -48, 157)] for bits in range(4)]
    for s, r in zip(states, actual('teleportationSnapshot', states)):
        t, p, g = map(math.radians, [s['thetaDeg'], s['phiDeg'], s['globalPhaseDeg']])
        psi = np.exp(1j*g)*np.array([math.cos(t/2), np.exp(1j*p)*math.sin(t/2)])
        after = circuit@np.kron(psi, bell)
        assert np.array(vector(r['afterBellUnitary'])) == pytest.approx(after, abs=3e-15)
        for bits, branch in enumerate(r['branches']):
            q, a = divmod(bits, 2)
            projected = after[2*bits:2*bits+2]
            probability = np.vdot(projected, projected).real
            assert branch['probability'] == pytest.approx(probability, abs=2e-15)
            bob = projected/math.sqrt(probability)
            correction = np.linalg.matrix_power(Z, q)@np.linalg.matrix_power(X, a)
            corrected = correction@bob
            assert np.array(vector(branch['corrected'])) == pytest.approx(corrected, abs=3e-15)
            assert corrected == pytest.approx(psi, abs=3e-15)
            assert branch['fidelity'] == pytest.approx(abs(np.vdot(psi, corrected))**2, abs=3e-15)
        assert np.array([[complex(z['re'], z['im']) for z in row] for row in r['bobBeforeMessage']]) == pytest.approx(np.eye(2)/2, abs=3e-15)
    # The four corrected branch Kraus operators each equal I/2. Their sum
    # implements identity on a reference-entangled input as well as pure qubits.
    basis_results = actual('teleportationSnapshot', [dict(thetaDeg=0, phiDeg=0), dict(thetaDeg=180, phiDeg=0)])
    kraus = [np.column_stack([vector(x['branches'][b]['corrected']) for x in basis_results])/2 for b in range(4)]
    entangled_density = np.outer(bell, bell.conj())
    transferred = sum(np.kron(np.eye(2), k)@entangled_density@np.kron(np.eye(2), k.conj().T) for k in kraus)
    assert transferred == pytest.approx(entangled_density, abs=3e-15)


def test_bell_reduced_density_no_signaling_and_conditional_statistics():
    states = [dict(bellState=bell, axisADeg=a, axisBDeg=b, aliceAction=operation, aliceOutcome=outcome)
              for bell in ['phi+', 'phi-', 'psi+', 'psi-'] for a, b in [(0, 0), (0, 90), (35, -64)]
              for operation in ['none', 'H', 'X', 'Z', 'dephase'] for outcome in [0, 1]]
    for s, r in zip(states, actual('bellSnapshot', states)):
        assert r['bobMarginal'] == pytest.approx([.5, .5], abs=2e-15)
        assert r['branchProbability'] == pytest.approx(.5, abs=2e-15)
        for key in ['bobBefore', 'bobAfter', 'nonselectiveBob']:
            for i in range(2):
                for j in range(2):
                    assert complex(**dict(real=r[key][i][j]['re'], imag=r[key][i][j]['im'])) == pytest.approx(.5 if i==j else 0, abs=2e-15)
        if s['aliceAction']=='none' and s['bellState']=='phi+':
            correlation = math.cos(math.radians(s['axisADeg']-s['axisBDeg']))
            assert r['joint'] == pytest.approx([(1+correlation)/4, (1-correlation)/4, (1-correlation)/4, (1+correlation)/4], abs=2e-15)
        if s['aliceAction']=='none' and s['bellState']=='psi-':
            assert r['correlation'] == pytest.approx(-math.cos(math.radians(s['axisADeg']-s['axisBDeg'])), abs=2e-15)


def test_cloning_physical_equality_and_linearity_not_phase_dependent_vector_equality():
    states = [dict(thetaDeg=t, phiDeg=p, globalPhaseDeg=g) for t in [0, 90, 180] for p in [-75, 0, 67] for g in [-93, 0, 150]]
    for s, r in zip(states, actual('cloningSnapshot', states)):
        if s['thetaDeg'] in [0, 180]:
            assert r['pairFidelity'] == pytest.approx(1, abs=3e-15)
        else:
            assert r['firstFidelity'] == pytest.approx(.5, abs=3e-15)
            assert r['secondFidelity'] == pytest.approx(.5, abs=3e-15)
        psi = vector(r['input'])
        desired = [a*b for a in psi for b in psi]
        output = [psi[0], 0, 0, psi[1]]
        assert vector(r['desired']) == pytest.approx(desired, abs=2e-15)
        assert vector(r['actual']) == pytest.approx(output, abs=2e-15)
        assert r['pairFidelity'] == pytest.approx(abs(sum(a.conjugate()*b for a, b in zip(desired, output)))**2, abs=3e-15)


def test_grover_independent_oracle_diffusion_arbitrary_domain_and_integer_peak():
    states = [dict(searchN=n, markedIndex=n-1, iterations=k) for n in [4, 5, 8, 16, 64] for k in [0, 1, 2, 7, 17]]
    for s, r in zip(states, actual('groverSnapshot', states)):
        amplitudes = [1/math.sqrt(s['searchN'])]*s['searchN']
        for _ in range(s['iterations']):
            amplitudes[s['markedIndex']] *= -1
            mean = sum(amplitudes)/s['searchN']
            amplitudes = [2*mean-a for a in amplitudes]
        assert vector(r['actual']['diffusion']) == pytest.approx(amplitudes, abs=3e-14)
        assert r['successProbability'] == pytest.approx(amplitudes[s['markedIndex']]**2, abs=3e-14)
    for n, expected in [(1000000, 785), (100000000, 7853)]:
        r = actual('groverSnapshot', [dict(searchN=n, iterations=expected)])[0]
        theta = math.asin(1/math.sqrt(n))
        assert r['optimalIterations'] == expected
        assert r['successProbability'] == pytest.approx(math.sin((2*expected+1)*theta)**2, abs=2e-15)
        assert r['actual'] is None
        assert r['classicalExpectedQueries'] == (n+1)/2


def test_explicit_noise_channels_density_positive_trace_and_observability_limits():
    np = pytest.importorskip('numpy')
    states = [dict(nQubits=n, thetaDeg=t, phiDeg=58, errorP=p, noiseRounds=g, noiseChannel=channel)
              for n in [1, 3, 4] for t in [0, 63, 90] for p, g in [(0, 0), (.005, 200), (.5, 1000)]
              for channel in ['global-depolarizing', 'local-phase-flip']]
    for s, r in zip(states, actual('noiseSnapshot', states)):
        rho = np.array([[complex(z['re'], z['im']) for z in row] for row in r['density']])
        assert np.trace(rho) == pytest.approx(1, abs=3e-14)
        assert np.linalg.eigvalsh(rho).min() >= -3e-14
        assert rho == pytest.approx(rho.conj().T, abs=3e-14)
        psi = np.array(vector(r['idealVector']))
        assert r['fidelity'] == pytest.approx(np.vdot(psi, rho@psi).real, abs=3e-14)
        if s['noiseChannel']=='global-depolarizing':
            w = (1-s['errorP'])**s['noiseRounds']
            expected = w*np.outer(psi, psi.conj())+(1-w)*np.eye(2**s['nQubits'])/(2**s['nQubits'])
        else:
            lam = (1-2*s['errorP'])**s['noiseRounds']
            one = np.outer(vector(r['input']), np.conj(vector(r['input'])))
            one[0, 1] *= lam
            one[1, 0] *= lam
            expected = np.ones((1, 1))
            for _ in range(s['nQubits']):
                expected = np.kron(expected, one)
            assert r['probabilities'] == pytest.approx(r['idealProbabilities'], abs=3e-15)
        assert rho == pytest.approx(expected, abs=3e-14)
    global_noise, phase_noise = actual('noiseSnapshot', [dict(nQubits=9, thetaDeg=90, errorP=.005, noiseRounds=200, noiseChannel=c) for c in ['global-depolarizing', 'local-phase-flip']])
    assert global_noise['noErrorProbability'] == pytest.approx(.995**200)
    assert phase_noise['noErrorProbability'] == pytest.approx(.995**1800)
    assert global_noise['probabilities'] == pytest.approx(global_noise['idealProbabilities'], abs=3e-15)
    assert global_noise['fidelity'] < .4
    assert phase_noise['fidelity'] < .01
