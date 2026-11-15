"""Independent primitive, SI, Born, Fourier, and barrier-matching checks.

The Node entry point loads only fixed known CommonJS files. The observation
packet is actual scene data; Python's SciPy/NumPy references do not call shipped
formula helpers or use production checker values as their numerical oracle.
"""
import cmath
import copy
import json
import math
from pathlib import Path
import shutil
import subprocess

import pytest

from primer.curriculum import Curriculum, _validate_lesson_media

ROOT = Path(__file__).resolve().parents[1]
NODE = shutil.which('node')
H = 6.62607015e-34
HBAR = H / (2 * math.pi)
MASS = 9.1093837139e-31
EV = 1.602176634e-19
C = 299792458


def _node(*arguments):
    if NODE is None:
        pytest.skip('Node is required for the actual CommonJS spatial models')
    result = subprocess.run([NODE, 'tools/check_complex_quantum_spatial.js', *arguments],
                            cwd=ROOT, capture_output=True, text=True,
                            timeout=45, check=False)
    assert result.returncode == 0, result.stdout + result.stderr
    return json.loads(result.stdout)


@pytest.fixture(scope='module')
def observations():
    return {item['state']['mode']: item for item in _node('--fixtures')}


def _primitive(scene, kind):
    matches = [item for item in scene['primitives'] if item.get('cq_kind') == kind]
    assert len(matches) == 1
    return matches[0]


def _complex(value):
    return complex(value['re'], value['im'])


@pytest.mark.parametrize(('node_id', 'family', 'retired_family'), [
    ('math.5.complex-analysis', 'complex-function-domain', 'complex-map'),
    ('phys.4.quantum', 'quantum-state-geometry', 'orbital-cloud'),
])
def test_quantitative_families_are_bound_to_actual_lessons(node_id, family, retired_family):
    node = copy.deepcopy(Curriculum().node(node_id))
    item = next(model for model in node['lesson_media'] if model.get('renderer') == 'spatial-3d')
    assert item['props']['scenario'] == 'module.' + node_id
    assert item['props']['family'] == family
    assert item['props']['mode'] == 'model'
    _validate_lesson_media(node)

    item['props']['family'] = retired_family
    with pytest.raises(ValueError, match='module spatial'):
        _validate_lesson_media(node)


def test_all_stations_primitive_oracles_state_retention_and_negative_calibrations():
    report = _node()
    assert report['status'] == 'passed'
    assert report['complexStations'] == 6
    assert report['quantumModes'] == 5
    assert report['complexStates'] >= 73
    assert report['quantumStates'] >= 80
    assert 'calibration mutation rejection' in report['regressionChecks']
    assert 'exact assessed well widths' in report['regressionChecks']
    assert 'zero-locus log-facet omission' in report['regressionChecks']
    assert 'impossible alternative energy outcomes retain preparation' in report['regressionChecks']
    assert 'four-equation barrier matching/current/energy/potential' in report['independentOracles']


def test_well_born_geometry_and_semantic_ledger_against_independent_quadrature(observations):
    quad = pytest.importorskip('scipy.integrate').quad
    scene = observations['well']
    state = scene['state']
    length = state['lengthNm']

    def energy(n):
        return H * H * n * n / (8 * MASS * (length * 1e-9) ** 2 * EV)

    def psi(x):
        if not 0 < x < length:
            return 0j
        common = cmath.exp(1j * math.radians(state['globalPhaseDeg']))
        coefficients = [math.sqrt(1 - state['mix']),
                        math.sqrt(state['mix']) * cmath.exp(1j * math.radians(state['phaseDeg']))]
        return common * sum(coefficient * math.sqrt(2 / length) * math.sin(n * math.pi * x / length)
                            * cmath.exp(-1j * energy(n) * EV * state['timeFs'] * 1e-15 / HBAR)
                            for n, coefficient in enumerate(coefficients, 1))

    for point in _primitive(scene, 'well_amplitude')['points']:
        expected = psi(point[0])
        assert point[1] == pytest.approx(expected.real, abs=2e-11)
        assert point[2] == pytest.approx(expected.imag, abs=2e-11)
    interval = quad(lambda x: abs(psi(x)) ** 2,
                    length * state['regionStart'], length * state['regionEnd'], epsabs=1e-12)[0]
    current = scene['current']
    assert current['regionalProbability'] == pytest.approx(interval, abs=2e-12)
    assert sum(bin_['count'] for bin_ in current['counts']['histogram']) == state['detections']
    for bin_ in current['counts']['histogram']:
        probability = quad(lambda x: abs(psi(x)) ** 2,
                           length * bin_['start'], length * bin_['end'], epsabs=1e-12)[0]
        assert bin_['probability'] == pytest.approx(probability, abs=3e-12)
    ledger = {row[0]: row[1:] for row in scene['ledger']}
    assert ledger['Exact regional probability'][0] == pytest.approx(interval, abs=2e-12)
    assert ledger['Mean energy'][0] == pytest.approx((1 - state['mix']) * energy(1) + state['mix'] * energy(2))
    assert ledger['Probe Re ψ'][0] == pytest.approx(psi(state['probe'] * length).real)
    assert ledger['Probe Im ψ'][0] == pytest.approx(psi(state['probe'] * length).imag)
    assert ledger['Probe Born density'][0] == pytest.approx(abs(psi(state['probe'] * length)) ** 2)
    assert ledger['State norm'][0] == 1
    assert ledger['Immediate energy repeat (given outcome)'][0] == 1
    assert ledger['Probe Born density'][1] == 'nm⁻¹'
    assert 'fresh copy' in scene['note']


def test_gaussian_fourier_phase_density_coordinates_and_tail_ledger(observations):
    quad = pytest.importorskip('scipy.integrate').quad
    scene = observations['gaussian']
    state = scene['state']
    sigma = state['sigmaNm']
    center = state['centerNm']
    chirp = state['chirp']
    k0 = state['kCenter']

    def psi(x):
        return (2 * math.pi * sigma * sigma) ** -.25 * cmath.exp(
            -(1 - 1j * chirp) * (x - center) ** 2 / (4 * sigma * sigma) + 1j * k0 * x)

    def fourier(k):
        integrand = lambda x: psi(x) * cmath.exp(-1j * k * x)
        lo, hi = center - 12 * sigma, center + 12 * sigma
        real = quad(lambda x: integrand(x).real, lo, hi, epsabs=1e-12)[0]
        imag = quad(lambda x: integrand(x).imag, lo, hi, epsabs=1e-12)[0]
        return complex(real, imag) / math.sqrt(2 * math.pi)

    points = _primitive(scene, 'gaussian_momentum_amplitude')['points']
    for point in [points[32], points[80], points[120]]:
        k = 10 * (point[0] - 4)
        expected = fourier(k)
        assert complex(point[1] / 5, point[2] / 5) == pytest.approx(expected, abs=2e-11)
    density = _primitive(scene, 'gaussian_momentum_density')['points']
    for point in [density[32], density[80], density[120]]:
        assert point[1] / 5 == pytest.approx(abs(fourier(10 * (point[0] - 4))) ** 2, abs=2e-11)
        assert point[2] == -2.5
    sigma_k = math.sqrt(1 + chirp * chirp) / (2 * sigma)
    tail = math.erfc(state['cropSigma'] / math.sqrt(2)) / 2
    current = scene['current']
    assert current['positionCrop']['leftTail'] == pytest.approx(tail, rel=2e-13)
    assert current['momentumCrop']['rightTail'] == pytest.approx(tail, rel=2e-13)
    assert current['sigmaPSI'] == pytest.approx(HBAR * sigma_k * 1e9, rel=3e-14, abs=0)
    ledger = {row[0]: row[1:] for row in scene['ledger']}
    assert ledger['σ(p/ℏ)'][0] == pytest.approx(sigma_k)
    assert ledger['σxσp / ℏ'][0] == pytest.approx(math.sqrt(1 + chirp * chirp) / 2)
    assert ledger['Position crop mass'][0] == pytest.approx(1 - 2 * tail)
    assert ledger['Momentum crop mass'][0] == pytest.approx(1 - 2 * tail)
    assert ledger['σp'][1] == 'kg·m/s'


def test_barrier_numpy_matching_current_and_actual_coordinate_gains(observations):
    np = pytest.importorskip('numpy')
    scene = observations['barrier']
    state = scene['state']
    k = math.sqrt(2 * MASS * state['energyEV'] * EV) / HBAR * 1e-9
    kappa = math.sqrt(2 * MASS * (state['heightEV'] - state['energyEV']) * EV) / HBAR * 1e-9
    width = state['widthNm']
    growing, decaying = math.exp(kappa * width), math.exp(-kappa * width)
    travel = cmath.exp(1j * k * width)
    matrix = np.array([[1, -1, -1, 0], [-1j * k, -kappa, kappa, 0],
                       [0, growing, decaying, -travel],
                       [0, kappa * growing, -kappa * decaying, -1j * k * travel]], dtype=complex)
    r, a, b, t = np.linalg.solve(matrix, np.array([-1, -1j * k, 0, 0], dtype=complex))
    for key, expected in [('r', r), ('A', a), ('B', b), ('t', t)]:
        assert _complex(scene['current'][key]) == pytest.approx(expected, abs=3e-13)

    def wave(x):
        if x < 0:
            incoming, reflected = cmath.exp(1j * k * x), r * cmath.exp(-1j * k * x)
            return incoming + reflected, 1j * k * (incoming - reflected)
        if x > width:
            value = t * cmath.exp(1j * k * x)
            return value, 1j * k * value
        grow, decay = a * math.exp(kappa * x), b * math.exp(-kappa * x)
        return grow + decay, kappa * (grow - decay)

    expected_current = HBAR * k * 1e9 / MASS * abs(t) ** 2
    for point in _primitive(scene, 'barrier_amplitude')['points'][::20]:
        value, derivative = wave(point[0])
        assert complex(point[1], point[2]) == pytest.approx(value, abs=3e-13)
        current = HBAR / MASS * 1e9 * (value.conjugate() * derivative).imag
        assert current == pytest.approx(expected_current, rel=3e-11, abs=2e-9)
    potential = _primitive(scene, 'barrier_potential')['points']
    assert potential[2] == pytest.approx([0, .25 * state['heightEV'], -2])
    assert potential[3] == pytest.approx([width, .25 * state['heightEV'], -2])
    assert _primitive(scene, 'barrier_energy')['points'][0][1] == .25 * state['energyEV']
    assert scene['current']['currents']['internal'] == pytest.approx(expected_current, rel=3e-11)
    ledger = {row[0]: row[1:] for row in scene['ledger']}
    assert ledger['Transmission T'][0] == pytest.approx(abs(t) ** 2, rel=2e-13)
    assert ledger['Reflection R'][0] == pytest.approx(abs(r) ** 2, rel=2e-13)
    assert ledger['R + T'][0] == pytest.approx(1, abs=3e-13)
    assert ledger['Internal current'][0] == pytest.approx(expected_current, rel=3e-11)


def test_spin_denominators_and_photon_phase_reference_semantics(observations):
    spin = observations['spin']
    ledger = {row[0]: row[1:] for row in spin['ledger']}
    assert ledger['Single-axis + probability'][0] == .5
    assert ledger['First z+ selected'] == [.5, 'per original input']
    assert ledger['Middle selected'] == [.5, 'per first z+ survivor']
    assert ledger['Final z+'] == [.5, 'per middle survivor']
    assert ledger['Final z+ from original'] == [.125, 'per original input']
    assert ledger['Final z− from original'] == [.125, 'per original input']
    photon = observations['photon']
    state = photon['state']
    energy = H * C / (state['wavelengthNm'] * 1e-9 * EV)
    assert _primitive(photon, 'photon_energy_probe')['points'][0] == pytest.approx(
        [state['wavelengthNm'] / 100, energy, 0], rel=3e-14)
    points = _primitive(photon, 'photon_phase_reference')['points']
    assert points[0] == pytest.approx([0, 0, -2], abs=1e-14)
    assert points[-1] == pytest.approx([state['wavelengthNm'] / 100, 0, -2], abs=1e-14)
    assert max(p[2] for p in points) - min(p[2] for p in points) == 1
    ledger = {row[0]: row[1:] for row in photon['ledger']}
    assert ledger['Exact photon energy'][0] == pytest.approx(energy, rel=3e-14)
    assert ledger['Photon energy in SI'][0] == pytest.approx(energy * EV, rel=3e-14, abs=0)
    assert ledger['Rounded 1240 / λ'][0] == pytest.approx(1240 / state['wavelengthNm'])
