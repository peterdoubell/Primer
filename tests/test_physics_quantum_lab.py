"""Independent SI, quadrature, Pauli-projector and boundary-value oracles.

Fixtures come directly from the CommonJS module used by the browser.  No
production checker or production formula supplies the Python reference values.
"""
import json
import math
from pathlib import Path
import shutil
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[1]
NODE = shutil.which('node')
H = 6.62607015e-34
HBAR = H / (2 * math.pi)
M_E = 9.1093837139e-31
EV = 1.602176634e-19
C = 299792458


def actual(method, arguments):
    if NODE is None:
        pytest.skip('Node is required to inspect the actual browser model')
    script = """
const lab = require('./web/physics-quantum-lab.js');
const input = JSON.parse(require('fs').readFileSync(0, 'utf8'));
const result = input.arguments.map(args => lab[input.method](...args));
process.stdout.write(JSON.stringify(result));
"""
    result = subprocess.run([NODE, '-e', script], input=json.dumps({
        'method': method, 'arguments': arguments,
    }), cwd=ROOT, capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stdout + result.stderr
    return json.loads(result.stdout)


def complex_value(value):
    return complex(value['re'], value['im'])


def well_energy(n, length_nm):
    return H ** 2 * n ** 2 / (8 * M_E * (length_nm * 1e-9) ** 2 * EV)


def well_coefficients(state):
    projection = state.get('projection', 'none')
    if projection != 'none':
        return [(int(projection), 1.0)]
    if state.get('wellState', 'eigen') == 'eigen':
        return [(state.get('n', 1), 1.0)]
    mix = state.get('mix', .5)
    phase = math.radians(state.get('phaseDeg', 0))
    return [(1, math.sqrt(1 - mix)), (2, math.sqrt(mix) * complex(math.cos(phase), math.sin(phase)))]


def well_psi(state, x_nm):
    length = state['lengthNm']
    time = state.get('timeFs', 0) * 1e-15
    phase = math.radians(state.get('globalPhaseDeg', 0))
    phase_factor = complex(math.cos(phase), math.sin(phase))
    return phase_factor * sum(
        coefficient * math.sqrt(2 / length) * math.sin(n * math.pi * x_nm / length)
        * complex(math.cos(well_energy(n, length) * EV * time / HBAR),
                  -math.sin(well_energy(n, length) * EV * time / HBAR))
        for n, coefficient in well_coefficients(state)
    )


def test_well_all_six_levels_hard_walls_normalization_and_exact_quiz_fixtures():
    quad = pytest.importorskip('scipy.integrate').quad
    lengths = [.2, .4336070583942774, .5006863036642564, 1, 2]
    states = [{'mode': 'well', 'wellState': 'eigen', 'n': n, 'lengthNm': length,
               'timeFs': time, 'globalPhaseDeg': phase}
              for n in range(1, 7) for length in lengths
              for time, phase in [(0, 0), (5, -180)]]
    samples = [(state, fraction * state['lengthNm'])
               for state in states for fraction in [0, .13, .25, .5, .75, .91, 1]]
    values = actual('wellAt', [[s, x] for s, x in samples])
    for (state, x), value in zip(samples, values):
        expected = well_psi(state, x)
        assert complex_value(value) == pytest.approx(expected, abs=1e-11)
        assert value['densityNmInverse'] == pytest.approx(abs(expected) ** 2, abs=2e-11)
        if x in (0, state['lengthNm']):
            assert abs(complex_value(value)) <= 2e-14
    intervals = actual('wellInterval', [[s, 0, s['lengthNm']] for s in states])
    energies = actual('wellEnergyEV', [[s['n'], s['lengthNm']] for s in states])
    for state, norm, energy in zip(states, intervals, energies):
        integrated = quad(lambda x: abs(well_psi(state, x)) ** 2, 0,
                          state['lengthNm'], epsabs=1e-12)[0]
        assert norm == pytest.approx(integrated, abs=2e-12)
        assert norm == pytest.approx(1, abs=2e-12)
        assert energy == pytest.approx(well_energy(state['n'], state['lengthNm']), rel=3e-14)
    fixture_lengths = actual('wellLengthNm', [[2], [1.5]])
    fixture_energies = actual('wellEnergyEV', [[3, fixture_lengths[0]], [4, fixture_lengths[1]]])
    assert fixture_energies == pytest.approx([18, 24], rel=3e-14)
    assert fixture_lengths == pytest.approx([
        math.sqrt(H * H / (8 * M_E * 2 * EV)) * 1e9,
        math.sqrt(H * H / (8 * M_E * 1.5 * EV)) * 1e9,
    ], rel=3e-14)
    base, widened = actual('wellEnergyEV', [[1, .5], [1, 1]])
    assert widened / base == pytest.approx(.25, rel=3e-14)
    # Q1's density ratio predicts approximately the same ratio for equal
    # small neighborhoods; probabilities are integrals rather than point mass.
    state = {'mode': 'well', 'wellState': 'eigen', 'n': 1, 'lengthNm': 1}
    probabilities = actual('wellInterval', [[state, center - 1e-4, center + 1e-4]
                                           for center in [.25, 1 / 6]])
    assert probabilities[0] / probabilities[1] == pytest.approx(2, abs=1e-6)


def test_superposition_born_intervals_phase_invariance_and_energy_projection():
    quad = pytest.importorskip('scipy.integrate').quad
    states = [{'mode': 'well', 'wellState': 'superposition', 'lengthNm': length,
               'mix': mix, 'phaseDeg': phase, 'globalPhaseDeg': global_phase,
               'timeFs': time, 'regionStart': .15, 'regionEnd': .7}
              for length in [.2, 1, 2] for mix in [0, .2, .5, 1]
              for phase, global_phase, time in [(0, 0, 0), (180, -140, 0), (65, 110, 5)]]
    snapshots = actual('snapshot', [[s] for s in states])
    intervals = actual('wellInterval', [[s, .15 * s['lengthNm'], .7 * s['lengthNm']] for s in states])
    for state, snapshot, interval in zip(states, snapshots, intervals):
        expected = quad(lambda x: abs(well_psi(state, x)) ** 2,
                        .15 * state['lengthNm'], .7 * state['lengthNm'], epsabs=1e-12)[0]
        assert interval == pytest.approx(expected, abs=2e-12)
        current = snapshot['current'] if 'current' in snapshot else snapshot
        assert current['regionalProbability'] == pytest.approx(expected, abs=2e-12)
        assert current['meanEnergyEV'] == pytest.approx(
            (1 - state['mix']) * well_energy(1, state['lengthNm'])
            + state['mix'] * well_energy(2, state['lengthNm']), rel=3e-14)
        assert [row['probability'] for row in current['energies']] == pytest.approx([1 - state['mix'], state['mix']])
        assert current['energyMeasurement']['immediateRepeatProbability'] == 1
    phase_states = [{'mode': 'well', 'wellState': 'superposition', 'lengthNm': 1,
                     'mix': .5, 'phaseDeg': phase, 'globalPhaseDeg': global_phase}
                    for phase in [0, 180] for global_phase in [-180, 0, 137]]
    pairs = [(s, x) for s in phase_states for x in [.25, .75]]
    densities = actual('wellAt', [[s, x] for s, x in pairs])
    for (state, x), value in zip(pairs, densities):
        constructive = (state['phaseDeg'] == 0) == (x == .25)
        assert value['densityNmInverse'] == pytest.approx((3 + (1 if constructive else -1) * 2 * math.sqrt(2)) / 2)
    projected = [{'mode': 'well', 'wellState': 'superposition', 'lengthNm': 1,
                  'mix': .2, 'phaseDeg': 77, 'projection': projection, 'timeFs': 2}
                 for projection in ['1', '2']]
    for state, value in zip(projected, actual('wellAt', [[s, .31] for s in projected])):
        assert complex_value(value) == pytest.approx(well_psi(state, .31), abs=2e-13)


def test_projection_eligibility_from_independent_born_overlaps():
    quad = pytest.importorskip('scipy.integrate').quad
    preparations = [dict(wellState='eigen', n=n) for n in range(1, 7)]
    preparations += [dict(wellState='superposition', mix=mix, phaseDeg=61)
                     for mix in [0, .17, .5, 1]]
    cases = [(dict(preparation, mode='well', lengthNm=1), n)
             for preparation in preparations for n in range(1, 7)]
    normalized = actual('normalize', [[dict(state, projection=str(n))] for state, n in cases])
    probabilities = actual('preparedEnergyProbability', [[state, n] for state, n in cases])
    densities = actual('wellAt', [[dict(state, projection=str(n)), .31] for state, n in cases])
    for (state, n), result, probability, density in zip(cases, normalized, probabilities, densities):
        # The prepared eigenbasis overlap specifies measurement support without
        # reusing production's mode/mix eligibility branch.
        integrand = lambda x: math.sqrt(2) * math.sin(n * math.pi * x) * well_psi(state, x)
        overlap = complex(quad(lambda x: integrand(x).real, 0, 1, epsabs=1e-13)[0],
                          quad(lambda x: integrand(x).imag, 0, 1, epsabs=1e-13)[0])
        born_probability = abs(overlap) ** 2
        assert probability == pytest.approx(born_probability, abs=2e-13)
        supported = born_probability > 1e-22
        assert result['projection'] == (str(n) if supported else 'none')
        expected_density = (2 * math.sin(n * math.pi * .31) ** 2 if supported
                            else abs(well_psi(state, .31)) ** 2)
        assert density['densityNmInverse'] == pytest.approx(expected_density, abs=2e-12)
    for n in [3, 4]:
        snapshot = actual('snapshot', [[dict(mode='well', wellState='eigen', n=n,
                                             lengthNm=1, projection=str(n))]])[0]
        assert snapshot['energyMeasurement']['projectedN'] == n
        assert snapshot['energyMeasurement']['immediateRepeatProbability'] == 1


def test_schrodinger_hamiltonian_and_evolution_from_independent_finite_differences():
    states = [{'mode': 'well', 'wellState': 'eigen', 'n': n, 'lengthNm': length, 'timeFs': 1.2}
              for n in [1, 3, 6] for length in [.2, 2]]
    states += [{'mode': 'well', 'wellState': 'superposition', 'lengthNm': length,
                'mix': .37, 'phaseDeg': -65, 'timeFs': 1.2}
               for length in [.2, 1, 2]]
    queries, references = [], []
    for state in states:
        for fraction in [.17, .31, .73]:
            x, dx, dt = fraction * state['lengthNm'], state['lengthNm'] * 1e-4, 1e-6
            second = (-well_psi(state, x + 2 * dx) + 16 * well_psi(state, x + dx)
                      - 30 * well_psi(state, x) + 16 * well_psi(state, x - dx)
                      - well_psi(state, x - 2 * dx)) / (12 * dx * dx)
            h_psi = -HBAR ** 2 * second * 1e18 / (2 * M_E * EV)
            before, after = dict(state, timeFs=state['timeFs'] - dt), dict(state, timeFs=state['timeFs'] + dt)
            time_derivative = (well_psi(after, x) - well_psi(before, x)) / (2 * dt * 1e-15)
            queries.append([state, x])
            references.append((second, h_psi, 1j * HBAR * time_derivative / EV))
    for value, (second, h_psi, evolution) in zip(actual('wellAt', queries), references):
        assert complex_value(value['spatialSecondNmInverse2']) == pytest.approx(second, rel=2e-7, abs=1e-6)
        assert complex_value(value['hPsiEV']) == pytest.approx(h_psi, rel=2e-7, abs=1e-6)
        assert complex_value(value['iHbarDtEV']) == pytest.approx(evolution, rel=1e-6, abs=1e-6)
        assert h_psi == pytest.approx(evolution, rel=1e-6, abs=1e-6)


def test_spin_pauli_projectors_all_preparations_axes_and_conditional_denominators():
    np = pytest.importorskip('numpy')
    identity = np.eye(2, dtype=complex)
    pauli = {'x': np.array([[0, 1], [1, 0]], complex),
             'y': np.array([[0, -1j], [1j, 0]], complex),
             'z': np.array([[1, 0], [0, -1]], complex)}
    def projector(axis, sign='+'):
        return (identity + (1 if sign == '+' else -1) * pauli[axis]) / 2
    def probability(rho, project):
        return float(np.trace(project @ rho).real)
    states = [{'mode': 'spin', 'prep': prep, 'axis': axis, 'middle': middle,
               'middleSign': sign}
              for prep in ['z+', 'z-', 'x+', 'x-', 'y+', 'y-', 'unpolarized']
              for axis in ['x', 'y', 'z'] for middle in ['x', 'y', 'z', 'bypass']
              for sign in ['+', '-']]
    for state, value in zip(states, actual('spinSnapshot', [[s] for s in states])):
        rho = identity / 2 if state['prep'] == 'unpolarized' else projector(state['prep'][0], state['prep'][1])
        plus = probability(rho, projector(state['axis']))
        assert value['measurement']['plus'] == pytest.approx(plus, abs=2e-14)
        assert value['measurement']['minus'] == pytest.approx(1 - plus, abs=2e-14)
        first = probability(rho, projector('z'))
        middle = 1 if state['middle'] == 'bypass' else probability(projector('z'), projector(state['middle'], state['middleSign']))
        final_state = projector('z') if state['middle'] == 'bypass' else projector(state['middle'], state['middleSign'])
        final_plus = probability(final_state, projector('z'))
        tree = value['tree']
        assert tree['firstPlus'] == pytest.approx(first)
        assert tree['middleConditional'] == pytest.approx(middle)
        assert tree['finalConditionalPlus'] == pytest.approx(final_plus)
        assert tree['finalConditionalMinus'] == pytest.approx(1 - final_plus)
        assert tree['finalOriginalPlus'] == pytest.approx(first * middle * final_plus)
        assert tree['finalOriginalMinus'] == pytest.approx(first * middle * (1 - final_plus))
    z_x, unpolarized, bypass = actual('spinSnapshot', [
        [{'prep': 'z+', 'axis': 'x', 'middle': 'x', 'middleSign': '+'}],
        [{'prep': 'unpolarized', 'axis': 'x', 'middle': 'x', 'middleSign': '+'}],
        [{'prep': 'z+', 'axis': 'z', 'middle': 'bypass'}],
    ])
    assert z_x['measurement']['plus'] == z_x['tree']['finalConditionalPlus'] == .5
    assert unpolarized['tree']['finalOriginalPlus'] == unpolarized['tree']['finalOriginalMinus'] == .125
    assert bypass['tree']['finalOriginalPlus'] == 1


def gaussian_psi(state, x):
    sigma, center = state['sigmaNm'], state['centerNm']
    b, k0 = state['chirp'], state['kCenter']
    return (2 * math.pi * sigma * sigma) ** (-.25) * math.exp(-((x - center) / sigma) ** 2 / 4) * complex(
        math.cos(b * (x - center) ** 2 / (4 * sigma * sigma) + k0 * x),
        math.sin(b * (x - center) ** 2 / (4 * sigma * sigma) + k0 * x))


def test_gaussian_fourier_quadrature_chirp_moments_and_unrenormalized_crop_tails():
    quad = pytest.importorskip('scipy.integrate').quad
    states = [{'mode': 'gaussian', 'sigmaNm': sigma, 'centerNm': center,
               'kCenter': k0, 'chirp': b, 'cropSigma': crop}
              for sigma in [.05, .3, 1] for b in [-4, 0, 4]
              for center, k0, crop in [(-2, -4, 2), (0, 0, 4), (2, 4, 6)]]
    snapshots = actual('gaussianSnapshot', [[s] for s in states])
    queries, expected_values = [], []
    for state, value in zip(states, snapshots):
        sigma, center, k0, b = (state[k] for k in ['sigmaNm', 'centerNm', 'kCenter', 'chirp'])
        norm = quad(lambda u: abs(gaussian_psi(state, center + sigma * u)) ** 2 * sigma,
                    -12, 12, epsabs=2e-12)[0]
        mean_x = quad(lambda u: (center + sigma * u) * abs(gaussian_psi(state, center + sigma * u)) ** 2 * sigma,
                      -12, 12, epsabs=2e-12)[0]
        variance_x = quad(lambda u: (sigma * u) ** 2 * abs(gaussian_psi(state, center + sigma * u)) ** 2 * sigma,
                          -12, 12, epsabs=2e-12)[0]
        # Parseval computes momentum moments through the derivative of ψ,
        # independent of the runtime's closed-form momentum Gaussian.
        def derivative(x):
            return gaussian_psi(state, x) * (-(1 - 1j * b) * (x - center) / (2 * sigma * sigma) + 1j * k0)
        mean_k = quad(lambda u: (gaussian_psi(state, center + sigma * u).conjugate()
                                 * (-1j * derivative(center + sigma * u))).real * sigma,
                      -12, 12, epsabs=2e-11)[0]
        second_k = quad(lambda u: abs(derivative(center + sigma * u)) ** 2 * sigma,
                        -12, 12, epsabs=2e-10)[0]
        sigma_k = math.sqrt(second_k - mean_k * mean_k)
        assert norm == pytest.approx(1, abs=2e-12)
        assert mean_x == pytest.approx(center, abs=2e-12)
        assert mean_k == pytest.approx(k0, abs=2e-11)
        assert value['sigmaXNm'] == pytest.approx(math.sqrt(variance_x), rel=2e-12)
        assert value['sigmaKNmInverse'] == pytest.approx(sigma_k, rel=2e-12)
        assert value['sigmaPSI'] == pytest.approx(HBAR * sigma_k * 1e9, rel=2e-12)
        assert value['uncertaintySI'] == pytest.approx(math.sqrt(variance_x) * sigma_k * HBAR, rel=2e-12)
        assert value['uncertaintyInHbar'] == pytest.approx(math.sqrt(1 + b * b) / 2, rel=2e-12)
        for crop in [value['positionCrop'], value['momentumCrop']]:
            tail = .5 * math.erfc(state['cropSigma'] / math.sqrt(2))
            assert crop['leftTail'] == pytest.approx(tail, rel=2e-12, abs=1e-16)
            assert crop['rightTail'] == pytest.approx(tail, rel=2e-12, abs=1e-16)
            assert crop['insideMass'] == pytest.approx(1 - 2 * tail, abs=2e-12)
        for offset in [-1.1, 0, .8]:
            k = k0 + offset * sigma_k
            # Fourier convention φ(k)=1/√(2π)∫ψ(x)e^(-ikx)dx.
            def integrand(u):
                x = center + sigma * u
                return gaussian_psi(state, x) * complex(math.cos(k * x), -math.sin(k * x)) * sigma / math.sqrt(2 * math.pi)
            fourier = complex(quad(lambda u: integrand(u).real, -12, 12, epsabs=2e-11)[0],
                              quad(lambda u: integrand(u).imag, -12, 12, epsabs=2e-11)[0])
            queries.append([state, k])
            expected_values.append(fourier)
    for value, reference in zip(actual('gaussianMomentumAt', queries), expected_values):
        assert complex_value(value) == pytest.approx(reference, rel=3e-10, abs=2e-11)
        assert value['densityK'] == pytest.approx(abs(reference) ** 2, rel=6e-10, abs=2e-12)
    position_queries = [[s, s['centerNm'] + offset * s['sigmaNm']] for s in states for offset in [-3, 0, 2]]
    for (state, x), value in zip(position_queries, actual('gaussianAt', position_queries)):
        assert complex_value(value) == pytest.approx(gaussian_psi(state, x), rel=2e-13, abs=2e-13)


def barrier_boundary_oracle(state):
    """Solve four complex matching equations; do not use the runtime's T formula."""
    np = pytest.importorskip('numpy')
    e, v, width = state['energyEV'] * EV, state['heightEV'] * EV, state['widthNm'] * 1e-9
    k, q = math.sqrt(2 * M_E * e) / HBAR, math.sqrt(2 * M_E * (v - e)) / HBAR
    growing, decaying, transmitted = math.exp(q * width), math.exp(-q * width), np.exp(1j * k * width)
    # Unknowns r, A, B, t, with ψ_inside=A exp(qx)+B exp(-qx).
    matrix = np.array([[1, -1, -1, 0], [-1j * k, -q, q, 0],
                       [0, growing, decaying, -transmitted],
                       [0, q * growing, -q * decaying, -1j * k * transmitted]], complex)
    # Rescale derivative rows by q to avoid SI-conditioned linear algebra.
    matrix[[1, 3]] /= q
    rhs = np.array([-1, -1j * k / q, 0, 0], complex)
    r, a, b, t = np.linalg.solve(matrix, rhs)
    incident = HBAR * k / M_E
    reflected, transmission = -incident * abs(r) ** 2, incident * abs(t) ** 2
    mid = width / 2
    psi = a * math.exp(q * mid) + b * math.exp(-q * mid)
    derivative = q * (a * math.exp(q * mid) - b * math.exp(-q * mid))
    internal = HBAR / M_E * (psi.conjugate() * derivative).imag
    return r, a, b, t, incident, reflected, transmission, internal


def test_finite_barrier_complex_four_by_four_matching_and_conserved_si_currents():
    states = [{'mode': 'barrier', 'heightEV': height, 'energyEV': height * fraction,
               'widthNm': width}
              for height in [.2, 1, 4] for fraction in [.5, .7, .9]
              for width in [0, .05, .4, 2]]
    states += [{'mode': 'barrier', 'heightEV': 8, 'energyEV': energy, 'widthNm': width}
               for energy in [.1, 4] for width in [0, .05, .4, 2]]
    # A physical fixture with κa=1 and E=V0/2 is independent of the control scale.
    width_fixture = HBAR / math.sqrt(2 * M_E * EV) * 1e9
    states.append({'mode': 'barrier', 'heightEV': 2, 'energyEV': 1, 'widthNm': width_fixture})
    previous = {}
    for state, value in zip(states, actual('barrierSnapshot', [[s] for s in states])):
        r, a, b, t, incident, reflected, transmitted, internal = barrier_boundary_oracle(state)
        assert complex_value(value['r']) == pytest.approx(r, rel=3e-11, abs=2e-12)
        assert complex_value(value['t']) == pytest.approx(t, rel=3e-11, abs=2e-12)
        assert complex_value(value['A']) == pytest.approx(a, rel=3e-11, abs=2e-12)
        assert complex_value(value['B']) == pytest.approx(b, rel=3e-11, abs=2e-12)
        assert value['R'] == pytest.approx(abs(r) ** 2, rel=3e-11, abs=2e-13)
        assert value['T'] == pytest.approx(abs(t) ** 2, rel=3e-11, abs=1e-25)
        assert value['R'] + value['T'] == pytest.approx(1, abs=2e-12)
        for key, reference in zip(['incident', 'reflected', 'transmitted', 'internal'],
                                  [incident, reflected, transmitted, internal]):
            assert value['currents'][key] == pytest.approx(reference, rel=3e-10, abs=1e-15)
        assert incident + reflected == pytest.approx(transmitted, abs=2e-9)
        assert internal == pytest.approx(transmitted, rel=2e-9, abs=1e-15)
        if state['widthNm'] == 0:
            assert value['T'] == pytest.approx(1, abs=2e-14)
        key = state['heightEV'], state['energyEV']
        if key in previous:
            assert value['T'] < previous[key]
        previous[key] = value['T']
    fixture = actual('barrierSnapshot', [[states[-1]]])[0]
    assert fixture['T'] == pytest.approx(.4199743416140261, rel=2e-13)


def test_photon_si_constants_exact_500_nm_and_inverse_wavelength_scaling():
    wavelengths = [200, 250, 400, 500, 800, 1000]
    values = actual('photonSnapshot', [[{'mode': 'photon', 'wavelengthNm': wavelength}] for wavelength in wavelengths])
    for wavelength, value in zip(wavelengths, values):
        expected_j = H * C / (wavelength * 1e-9)
        assert value['energyEV'] == pytest.approx(expected_j / EV, rel=3e-14)
        assert value['energyJ'] == pytest.approx(expected_j, rel=3e-14)
    assert round(values[3]['energyEV'], 2) == 2.48
    assert values[0]['energyEV'] / values[2]['energyEV'] == pytest.approx(2)
    assert values[3]['energyEV'] / values[-1]['energyEV'] == pytest.approx(2)
