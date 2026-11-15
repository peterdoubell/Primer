"""Independent fluids oracles: collocation BVPs, force ODEs and pressure quadrature.

Default execution emits a receipt without modifying proofs. --write-proof writes only
to the fixed independent-review directory. No network or arbitrary input paths.
"""
from pathlib import Path
from decimal import Decimal, localcontext
import argparse
import hashlib
import json
import math
import subprocess

import numpy as np
import scipy
from scipy.integrate import quad, solve_bvp, solve_ivp
from scipy.optimize import brentq

if not __debug__:
    raise RuntimeError('Assertions must be enabled for scientific verification.')
ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'docs/fluids-fidelity-review-20261016/independent-review'
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--write-proof', action='store_true')
args = parser.parse_args()
requests, cases, checks, metrics = [], {}, [], {}


def ask(name, method, input=None, probes=None):
    requests.append(dict(id=name, method=method, input=input or {}, **({'probes': probes} if probes else {})))
    cases[name] = dict(method=method, input=input or {})
    return name


for i, state in enumerate([{}, {'flow': .0008}, {'flow': 0}, {'areaThroat': .0004}, {'inletGauge': -50000}, {'flow': .001, 'rho': 1500, 'ambientPressure': 50000, 'inletGauge': 0}]):
    ask(f'continuity-{i}', 'continuity', state)
for i, state in enumerate([{}, {'topPressure': 0}, {'ambientPressure': 80000, 'topPressure': 3000, 'rho': 850}, {'topPressure': 150000}, {'topPressure': 1000}, {'ambientPressure': 1000}]):
    ask(f'hydro-{i}', 'hydrostatics', state)
for i, state in enumerate([{}, {'areaIn': .004, 'areaOut': .002, 'forceIn': 30, 'strokeIn': .1}, {'forceIn': 0}, {'strokeIn': 0}]):
    ask(f'piston-{i}', 'pistons', state)
for i, state in enumerate([{}, {'cargoMass': 800}, {'retainedWaterMass': 600}, {'length': 2, 'width': .5, 'height': .8, 'rho': 850, 'cargoMass': 200}, {'dryMass': 0, 'cargoMass': 0}, {'retainedWaterMass': 1000}, {'rho': 850, 'retainedWaterMass': 850}]):
    ask(f'hull-{i}', 'hull', state)
for i, state in enumerate([{}, {'pressureDrop': -2}, {'pressureDrop': 0}, {'radius': .01}, {'mu': .02}, {'pressureDrop': 1000}]):
    ask(f'pipe-{i}', 'pipe', state)
for i, state in enumerate([{}, {'etaMax': 16, 'step': .01}, {'etaMax': 10, 'step': .05}]):
    ask(f'blasius-{i}', 'blasiusSolve', state, [0, .125, 1, 2.75, 4.91, 8, 10])
for i, state in enumerate([{}, {'speed': 4, 'x': 2, 'probeEta': 4.91}, {'speed': .01, 'nu': .1, 'x': .001, 'probeEta': 0}]):
    ask(f'boundary-{i}', 'boundaryLayer', state)
# Force-ODE checks include signed rising, sinking and neutral particles, and tiny t/tau.
for density in [7800, 500, 1000]:
    for mu in [.001, .02]:
        tau = 2 * density * 1e-10 / (9 * mu)
        for q in [0, 1e-9, .1, math.log(20), 20]:
            ask(f'settle-{density}-{mu}-{q}', 'settling', {'particleDensity': density, 'mu': mu, 'time': q * tau})
for i, state in enumerate([{}, {'alphaDegrees': -5}, {'alphaDegrees': 0}, {'alphaDegrees': 10, 'epsilon': .05, 'samples': 128}, {'alphaDegrees': -10, 'epsilon': .25, 'samples': 2048, 'chord': 2, 'speed': 7}]):
    ask(f'lift-{i}', 'joukowski', state, [0, .01, .3, 1.7, math.pi, 5.7, 2 * math.pi])
for count in [256, 720]:
    ask('lift-refined-' + str(count), 'joukowski', {'alphaDegrees': 10, 'epsilon': .05, 'samples': count})
for i, state in enumerate([{}, {'height': 1}, {'height': 16}, {'referenceHeight': 2, 'height': 16, 'referenceSpeed': 3, 'referenceWidth': .2}]):
    ask(f'plume-{i}', 'plume', state)
invalid = []
for method, state in [('continuity', {'areaThroat': .001}), ('continuity', {'flow': -.001}), ('hydrostatics', {'topPressure': -1}), ('hydrostatics', {'rho': 0}), ('pistons', {'areaIn': .2, 'areaOut': 1e-5, 'strokeIn': .5}), ('hull', {'retainedWaterMass': -1}), ('pipe', {'mu': 0}), ('blasiusSolve', {'step': .033}), ('boundaryLayer', {'x': 0}), ('settling', {'time': -1}), ('joukowski', {'epsilon': 0}), ('joukowski', {'samples': 720.5}), ('plume', {'height': 0})]:
    invalid.append(ask(f'invalid-{len(invalid)}', method, state))
for state in [{'retainedWaterMass': 1000.001}, {'rho': 850, 'retainedWaterMass': 850.001}]:
    invalid.append(ask(f'invalid-{len(invalid)}', 'hull', state))
reply = json.loads(subprocess.check_output(['node', str(ROOT / 'tools/check_fluids_independent.cjs')], input=json.dumps(requests).encode(), cwd=ROOT, timeout=60))
assert hashlib.sha256((ROOT / 'web/fluids-lab.js').read_bytes()).hexdigest() == reply['sourceSHA256']
data = {item['id']: item for item in reply['results']}


def result(name):
    assert 'error' not in data[name], data[name]
    return data[name]['result']


def near(actual, expected, label, rel=2e-10, absolute=1e-12):
    assert math.isfinite(actual) and math.isfinite(expected), (label, actual, expected)
    error = abs(actual - expected)
    assert error <= absolute + rel * abs(expected), (label, actual, expected, error)
    return error


def passed(area, method, count, **kwargs):
    checks.append(dict(area=area, method=method, cases=count, result='pass', **kwargs))


for name in [k for k in cases if k.startswith('continuity-')]:
    m = result(name)
    total = m['inletGauge'] + .5 * m['rho'] * (m['flow'] / m['areaIn']) ** 2
    for section in m['sections']:
        near(quad(lambda r: 2 * math.pi * r * section['speed'], 0, section['radius'])[0], m['flow'], name + ' integrated section flux')
        near(section['gauge'] + .5 * m['rho'] * section['speed'] ** 2, total, name + ' conserved energy per volume')
        near(section['head'] * m['rho'] * m['g'], section['gauge'], name + ' pressure head dimension')
        near(section['absolute'] - section['gauge'], m['ambientPressure'], name + ' absolute pressure datum')
    assert m['singlePhaseAllowed'] == all(s['absolute'] >= m['vaporPressure'] for s in m['sections'])
    assert 'MAINTAINS volume flow Q' in m['limits'] and 'lossless' in m['limits']
quiz = result('continuity-1')
near(quiz['inletSpeed'], 2, 'exact quiz inlet speed')
near(quiz['throatSpeed'], 8, 'exact quiz throat speed')
near(quiz['pressureDrop'] / 1000, 30, 'exact quiz pressure drop kPa')
assert result('continuity-4')['sections'][0]['head'] < 0
assert not result('continuity-5')['singlePhaseAllowed']
passed('continuity and Bernoulli', 'Independent annular section flux, conserved energy per volume and signed head/absolute-pressure checks, including exact 2/8 m/s and 30 kPa quiz state', 6)
preservation = json.loads((OUTPUT / 'original-venturi-preservation.json').read_text())
original = (ROOT / 'web/lesson-models.js').read_bytes()
start = original.index(preservation['start_marker'].encode())
end = original.index(preservation['end_marker'].encode(), start)
assert hashlib.sha256(original[start:end]).hexdigest() == preservation['sha256']
assert end - start == preservation['bytes']
passed('original Venturi preservation', 'Exact hash of the original 7,358-byte constants/renderer body remains unchanged after adding the new companion', 1)


for name in [k for k in cases if k.startswith('hydro-')]:
    m = result(name)
    for point in m['profile']:
        p = m['ambientPressure'] - quad(lambda z: m['rho'] * m['g'], 0, point['z'])[0]
        near(point['absolute'], p, name + ' integrated static pressure')
        near(point['gauge'], p - m['ambientPressure'], name + ' gauge reference')
    near(m['profile'][-1]['absolute'], m['topPressure'], name + ' endpoint')
    near(m['idealLimit'], m['ambientPressure'] / (m['rho'] * m['g']), name + ' hypothetical vacuum limit')
    assert m['singlePhaseAllowed'] == (min(m['ambientPressure'], m['topPressure']) >= m['vaporPressure'])
assert result('hydro-3')['height'] < 0 and not result('hydro-4')['singlePhaseAllowed']
passed('hydrostatics', 'Integrate dp/dz=-rho*g; compare every absolute/gauge sample, signed height and saturation constraint', 6)
for name in [k for k in cases if k.startswith('piston-')]:
    m = result(name)
    vi = quad(lambda x: math.pi * m['radiusIn'] ** 2, 0, m['strokeIn'])[0]
    vo = quad(lambda x: math.pi * m['radiusOut'] ** 2, 0, m['strokeOut'])[0]
    near(vi, vo, name + ' swept cylindrical volumes')
    near(m['inputWork'], quad(lambda x: m['forceIn'], 0, m['strokeIn'])[0], name + ' input work integral')
    near(m['outputWork'], quad(lambda x: m['forceOut'], 0, m['strokeOut'])[0], name + ' output work integral')
    near(m['inputWork'], m['outputWork'], name + ' energy conservation')
    near(m['forceIn'] / m['areaIn'], m['forceOut'] / m['areaOut'], name + ' equal pressure')
    assert 'horizontal' in m['limits'].lower() and 'elevation' in m['limits'].lower()
passed('pistons', 'Integrate swept circular area and force-displacement work, same-elevation horizontal geometry', 4)
for name in [k for k in cases if k.startswith('hull-')]:
    m = result(name)
    bottom = quad(lambda x: m['rho'] * m['g'] * m['draft'] * m['width'], 0, m['length'])[0]
    near(m['buoyancy'], bottom, name + ' integrated bottom pressure force')
    for direction, span in [('X', m['width']), ('Y', m['length'])]:
        side = quad(lambda depth: m['rho'] * m['g'] * depth * span, 0, m['draft'])[0]
        near(m['sideForce' + direction], side, name + ' integrated side pressure')
    near(m['weight'], m['g'] * (m['dryMass'] + m['cargoMass'] + m['retainedWaterMass']), name + ' mass ledger')
    near(m['totalVolume'], m['length'] * m['width'] * m['height'], name + ' sealed external volume')
    assert m['equilibriumExists'] == (m['weight'] <= m['rho'] * m['g'] * m['totalVolume'])
    assert m['retainedWaterMass'] <= m['rho'] * m['totalVolume']
    assert 'same declared density' in m['limits'] and 'does not subtract shell or cargo volume' in m['limits']
assert result('hull-1')['state'] == 'neutral' and result('hull-2')['state'] == 'overloaded'
near(result('hull-0')['totalVolume'], result('hull-2')['totalVolume'], 'retained water does not also reduce displaced-volume capacity')
assert result('hull-5')['state'] == result('hull-6')['state'] == 'overloaded'
passed('buoyancy', 'Surface pressure integrals and explicit mass/volume capacity ledger for floating, neutral and overloaded sealed hulls; retained-fluid whole-box bound is necessary only, at the same declared density', 7)

# Solve radial viscous momentum equation in dimensionless radius by collocation.
# Singular term handles symmetry at the centre; no parabolic solution is supplied.
rgrid = np.linspace(0, 1, 41)
radial = solve_bvp(lambda r, y: np.vstack((y[1], -np.ones_like(r))), lambda a, b: np.array([a[1], b[0]]), rgrid, np.zeros((2, len(rgrid))), S=np.array([[0., 0.], [0., -1.]]), tol=1e-10)
assert radial.success, radial.message
for name in [k for k in cases if k.startswith('pipe-')]:
    m = result(name)
    scale = m['pressureDrop'] * m['radius'] ** 2 / (m['mu'] * m['length'])
    velocity = lambda r: scale * radial.sol(r / m['radius'])[0]
    gradient = lambda r: scale / m['radius'] * radial.sol(r / m['radius'])[1]
    flow = quad(lambda r: 2 * math.pi * r * velocity(r), 0, m['radius'], epsabs=1e-15)[0]
    dissipation = quad(lambda r: m['mu'] * gradient(r) ** 2 * 2 * math.pi * r * m['length'], 0, m['radius'], epsabs=1e-15)[0]
    near(m['flow'], flow, name + ' collocation annular flux')
    near(m['power'], dissipation, name + ' integrated viscous dissipation')
    for point in m['profile']:
        near(point['u'], velocity(point['r']), name + ' BVP velocity')
        near(point['shear'], m['mu'] * gradient(point['r']), name + ' BVP shear')
    if flow:
        alpha = quad(lambda r: 2 * math.pi * r * velocity(r) ** 3, 0, m['radius'])[0] / (math.pi * m['radius'] ** 2 * (flow / m['area']) ** 3)
        near(m['kineticEnergyCorrection'], alpha, name + ' kinetic energy flux')
        near(m['pressureDrop'], m['darcyFactor'] * m['length'] / (2 * m['radius']) * m['rho'] * m['mean'] * abs(m['mean']) / 2, name + ' Darcy momentum loss')
    else:
        assert m['darcyFactor'] is None
near(result('pipe-3')['flow'] / result('pipe-0')['flow'], 16, 'radius doubled changes flux sixteenfold')
assert not result('pipe-5')['withinConservativeTeachingRe']
passed('pipe', 'Independent singular collocation radial-momentum BVP, annular volume/energy flux, viscous dissipation and signed Darcy loss', 6)


def blasius_bvp(endpoint, tolerance):
    eta = np.linspace(0, endpoint, 181)
    guess = np.vstack((eta - 1 + np.exp(-eta), 1 - np.exp(-eta), np.exp(-eta)))
    sol = solve_bvp(lambda x, y: np.vstack((y[1], y[2], -.5 * y[0] * y[2])), lambda a, b: np.array([a[0], a[1], b[1] - 1]), eta, guess, tol=tolerance, max_nodes=20000)
    assert sol.success, sol.message
    eta99 = brentq(lambda e: sol.sol(e)[1] - .99, 3, 7, xtol=1e-13)
    displacement = quad(lambda e: 1 - sol.sol(e)[1], 0, endpoint, epsabs=1e-10)[0]
    momentum = quad(lambda e: sol.sol(e)[1] * (1 - sol.sol(e)[1]), 0, endpoint, epsabs=1e-10)[0]
    return sol, np.array([sol.sol(0)[2], eta99, displacement, momentum])


coarse, coarse_values = blasius_bvp(14, 2e-8)
fine, fine_values = blasius_bvp(18, 2e-11)
assert np.max(np.abs(coarse_values - fine_values)) < 2e-8
metrics['independent_blasius'] = dict(zip(['wallSecond', 'eta99', 'displacementEta', 'momentumEta'], fine_values.tolist()))
metrics['blasius_refinement_max_absolute_change'] = float(np.max(np.abs(coarse_values - fine_values)))
for name in [k for k in cases if k.startswith('blasius-')]:
    m = result(name)
    for field, want in zip(['wallSecond', 'eta99', 'displacementEta', 'momentumEta'], fine_values):
        near(m[field], want, name + ' collocation ' + field, rel=2e-8, absolute=2e-9)
    for point in m['samplesAt']:
        for field, want in zip(['f', 'fp', 'fpp'], fine.sol(point['eta'])):
            # The deliberately coarsest supported RK4 step (.05) has O(h^4)
            # truncation error; keep the default/fine profile tolerance tighter.
            near(point[field], want, name + ' BVP profile ' + field, rel=2e-8, absolute=1e-8 if m['step'] == .05 else 2e-9)
for name in [k for k in cases if k.startswith('boundary-')]:
    m = result(name)
    scale = math.sqrt(m['nu'] * m['x'] / m['speed'])
    for point in m['profile']:
        f, fp, fpp = fine.sol(point['y'] / scale)
        near(point['u'], m['speed'] * fp, name + ' dimensional u', rel=2e-8)
        near(point['v'], .5 * math.sqrt(m['nu'] * m['speed'] / m['x']) * (point['y'] / scale * fp - f), name + ' dimensional v', rel=2e-8, absolute=2e-10)
    near(m['wallShear'], m['rho'] * m['nu'] * m['speed'] / scale * fine_values[0], name + ' independent wall gradient', rel=2e-8)
    near(m['Cf'], m['wallShear'] / (.5 * m['rho'] * m['speed'] ** 2), name + ' Cf definition')
    near(m['delta99'], fine_values[1] * scale, name + ' 99 percent thickness', rel=2e-8)
assert not result('boundary-2')['thinTeachingGuard']
passed('boundary layer', 'Two refined collocation BVPs on eta 14/18 independent of RK4 shooting; dimensional profiles, displacement/momentum integrals and wall stress', 6, refinement=metrics['blasius_refinement_max_absolute_change'])

# Direct dimensional force balance integrated with a separate adaptive ODE method.
for name in [k for k in cases if k.startswith('settle-')]:
    m = result(name)
    V = quad(lambda x: math.pi * (m['radius'] ** 2 - x * x), -m['radius'], m['radius'], epsabs=1e-30)[0]
    mass = V * m['particleDensity']
    drive = V * (m['particleDensity'] - m['fluidDensity']) * m['g']
    friction = 6 * math.pi * m['mu'] * m['radius']
    tau = mass / friction
    q = m['time'] / tau
    if q:
        solution = solve_ivp(lambda t, y: [tau * y[1], tau * (drive - friction * y[1]) / mass], [0, q], [0., 0.], method='DOP853', rtol=2e-12, atol=1e-25)
        assert solution.success
        near(m['position'], solution.y[0, -1], name + ' force ODE displacement', rel=2e-9, absolute=1e-25)
        near(m['velocity'], solution.y[1, -1], name + ' force ODE velocity', rel=2e-9, absolute=1e-25)
    near(m['netDownward'], mass * m['acceleration'], name + ' signed Newton second law', absolute=1e-22)
    if drive:
        near(m['terminal'], brentq(lambda v: drive - friction * v, -100, 100, xtol=1e-20), name + ' equilibrium drag root', absolute=1e-16)
        near(m['time95'], tau * math.log(20), name + ' 95 percent clock')
    else:
        assert m['time95'] is None and m['fraction'] is None and m['position'] == m['velocity'] == 0
    if 0 < q < 1e-8 and drive:
        with localcontext() as context:
            context.prec = 60
            qd = Decimal(str(q))
            exact = Decimal(str(m['terminal'])) * Decimal(str(tau)) * (qd + (-qd).exp() - 1)
        near(m['position'], float(exact), name + ' tiny-time high precision displacement', rel=2e-14, absolute=1e-40)
    assert 'added mass' in m['limits'] and 'history' in m['limits'] and 'Low Re alone' in m['limits']
passed('settling', 'Adaptive DOP853 force ODE with signed density difference, neutral state, force root and sixty-digit tiny-time oracle', 30)


def complex_foil(theta, m):
    radius = 1 + m['epsilon']
    a = math.radians(m['alphaDegrees'])
    q = radius * np.exp(1j * theta)
    zeta = -m['epsilon'] + q
    left = -1 - 2 * m['epsilon']
    xleft = left + 1 / left
    scale = m['chord'] / (2 - xleft)
    z = (zeta + 1 / zeta - xleft) * scale
    dz = (1 - 1 / zeta ** 2) * 1j * q * scale
    gamma = 4 * math.pi * radius * scale * m['speed'] * math.sin(a)
    # Complex potential derivative is u-iv, with clockwise-positive circulation.
    velocity = (m['speed'] * (np.exp(-1j * a) - radius ** 2 * np.exp(1j * a) / q ** 2) + 1j * gamma / (2 * math.pi * scale * q)) / (1 - 1 / zeta ** 2)
    cp = 1 - abs(velocity) ** 2 / m['speed'] ** 2
    return z, dz, velocity, cp, gamma


for name in [k for k in cases if k.startswith('lift-')]:
    m = result(name)
    assert m['mapPole'] == 0 and m['criticalPoints'] == [-1, 1] and m['trailingEdgePreimage'] == 1
    for point in m['surface'][::max(1, m['samples'] // 79)]:
        z, dz, velocity, cp, gamma = complex_foil(point['theta'], m)
        for field, want in [('x', z.real), ('y', z.imag), ('dxTheta', dz.real), ('dyTheta', dz.imag), ('velocityX', velocity.real), ('velocityY', -velocity.imag), ('Cp', cp), ('nx', dz.imag / abs(dz)), ('ny', -dz.real / abs(dz))]:
            near(point[field], float(want), name + ' complex potential ' + field, rel=3e-9, absolute=2e-10)
        near(point['nx'] * point['velocityX'] + point['ny'] * point['velocityY'], 0, name + ' no penetration', absolute=2e-10)
    def integrand(theta, kind):
        z, dz, velocity, cp, gamma = complex_foil(theta, m)
        if kind == 0: return -m['dynamicPressure'] * cp * dz.imag
        if kind == 1: return m['dynamicPressure'] * cp * dz.real
        return (velocity * dz).real
    forces = [quad(lambda theta: integrand(theta, kind), 0, 2 * math.pi, epsabs=1e-9, epsrel=1e-11, limit=200)[0] for kind in range(3)]
    for actual, expected, field in zip([m['forceX'], m['forceY'], m['circulationCCW']], forces, ['forceX', 'forceY', 'circulationCCW']):
        near(actual, expected, name + ' adaptive surface integral ' + field, rel=7e-6 if m['samples'] == 128 else 3e-9, absolute=2e-8)
    near(m['circulationCCW'], -m['gammaClockwise'], name + ' circulation orientation', rel=3e-6)
    near(m['lift'], m['rho'] * m['speed'] * m['gammaClockwise'], name + ' Kutta Joukowski', rel=3e-6, absolute=2e-8)
    near(m['drag'], 0, name + ' d Alembert drag', absolute=5e-4 if m['samples'] == 128 else 2e-8)
    near(m['normalIntegralX'], 0, name + ' constant pressure cancels x', absolute=1e-10)
    near(m['normalIntegralY'], 0, name + ' constant pressure cancels y', absolute=1e-10)
    near(m['trailingEdge']['velocityX'], m['speed'] * math.cos(m['alpha']) / (1 + m['epsilon']), name + ' finite Kutta cusp limit')
    assert m['trailingEdge']['nx'] is None and m['trailingEdge']['ny'] is None
    assert 'No equal-transit-time' in m['limits'] and 'per unit span' in m['limits']
near(result('lift-0')['lift'], -result('lift-1')['lift'], 'signed incidence lift reversal')
metrics['thin_foil_quadrature_drag_N_per_m'] = {str(n): result(name)['drag'] for n, name in [(128, 'lift-3'), (256, 'lift-refined-256'), (720, 'lift-refined-720')]}
assert abs(result('lift-refined-256')['drag']) < abs(result('lift-3')['drag']) / 10000
passed('ideal lift', 'Independent complex potential/map derivative, adaptive pressure/circulation contour integrals, impermeability, pressure-reference cancellation and finite Kutta cusp; explicitly refine the least-resolved supported thin foil', 7, coarse_resolution_limit='At 128 samples and epsilon=.05, alpha=10°, pressure-force quadrature has about 6e-6 relative Fx error and 3.06e-4 N/m residual drag. Default 720 samples resolves this case to floating-point precision.')
for name in [k for k in cases if k.startswith('plume-')]:
    m = result(name)
    for point in m['profile'] + [m]:
        near(point['speed'] ** 3 * point['height'], m['referenceSpeed'] ** 3 * m['referenceHeight'], name + ' speed-cubed height invariant')
        near(point['width'] / point['height'], m['referenceWidth'] / m['referenceHeight'], name + ' linear radius invariant')
        near(point['reynolds'], point['speed'] * point['width'] / m['nu'], name + ' radius Reynolds number')
    assert 'does not resolve' in m['limits'] and 'onset' in m['limits']
near(result('plume-0')['speed'] / result('plume-1')['speed'], .5, 'height8 speed factor')
near(result('plume-0')['reynolds'] / result('plume-1')['reynolds'], 4, 'height8 Reynolds factor')
passed('plume scaling', 'Independent power-law invariants and radius-based Reynolds dimensional definition; no onset or resolved-flow claim', 4)
for name in invalid:
    assert 'error' in data[name] and data[name]['error']['name'] in ['RangeError', 'TypeError'], data[name]
passed('invalid domains', 'Reject nonphysical/sign-disallowed and impossible piston travel inputs rather than emit invalid physics', len(invalid))

report = dict(sourceSHA256=reply['sourceSHA256'], checkerSHA256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), runnerSHA256=hashlib.sha256((ROOT / 'tools/check_fluids_independent.cjs').read_bytes()).hexdigest(), scipyVersion=scipy.__version__, numpyVersion=np.__version__, checks=checks, metrics=metrics, requestCount=len(requests), allPassed=True, remainingActionableScientificDefects=[], scope='Independent numerical API verification only; renderer/control evidence is separate. Models remain subject to their declared idealizations, guards are not transition laws, and this does not certify complete fluid mechanics or real-world prediction.')
if args.write_proof:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / 'numerical-review.json').write_text(json.dumps(report, indent=2) + '\n')
    (OUTPUT / 'numerical-cases.json').write_text(json.dumps(requests, indent=2) + '\n')
    (OUTPUT / 'renderer-oracles.json').write_text(json.dumps({'method': 'SciPy collocation BVP on eta 18, tol 2e-11; independent of product RK4 shooting', 'blasius': [{'eta': i / 10, 'f': float(fine.sol(i / 10)[0]), 'fp': float(fine.sol(i / 10)[1]), 'fpp': float(fine.sol(i / 10)[2])} for i in range(121)], 'eta99': float(fine_values[1])}, indent=2) + '\n')
print(json.dumps(report, indent=2))
