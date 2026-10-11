"""Independent Lorentz, ODE, metric, tidal Hessian and reception-event oracles."""
import json
import math
from decimal import Decimal, localcontext
from pathlib import Path
import shutil
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[1]
NODE = shutil.which('node')
C = 299792458
YEAR = 31557600
DAY = 86400
GM = 3.986004418e14
R = 6378137
OMEGA = 7.292115e-5
G0 = 9.80665


def actual(method, arguments):
    if NODE is None:
        pytest.skip('Node is needed to inspect the browser model')
    script = """
const l=require('./web/physics-relativity-lab.js');
const input=JSON.parse(require('fs').readFileSync(0,'utf8'));
process.stdout.write(JSON.stringify(input.arguments.map(args=>l[input.method](...args))));
"""
    result = subprocess.run([NODE, '-e', script], cwd=ROOT,
                            input=json.dumps({'method': method, 'arguments': arguments}),
                            text=True, capture_output=True, check=True)
    return json.loads(result.stdout)


def test_mounted_controls_exact_drafts_units_scoped_stations_and_current_speech():
    if NODE is None:
        pytest.skip('Node is required')
    result = subprocess.run([NODE, str(ROOT / 'tools/check_physics_relativity_lab.js')],
                            cwd=ROOT, text=True, capture_output=True, check=True)
    assert 'mounted' in result.stdout
    assert '8 relativity stations' in result.stdout


def test_lorentz_boosts_from_rapidity_matrix_invariant_inverse_and_causal_order():
    cases = [(dict(xM=x, ctM=ct), b) for b in [-.995, -.8, 0, .6, .995]
             for x in [-40, 0, 17, 40] for ct in [-40, 0, 23, 40]]
    values = actual('lorentzEvent', [[e, b] for e, b in cases])
    for (event, beta), value in zip(cases, values):
        eta = math.atanh(beta)
        x, ct = event['xM'], event['ctM']
        expected_x = math.cosh(eta) * x - math.sinh(eta) * ct
        expected_ct = math.cosh(eta) * ct - math.sinh(eta) * x
        assert value['xM'] == pytest.approx(expected_x, abs=3e-12)
        assert value['ctM'] == pytest.approx(expected_ct, abs=3e-12)
        # Inverse matrix checks the unchanged physical event, not a copied formula.
        back_x = math.cosh(eta) * value['xM'] + math.sinh(eta) * value['ctM']
        back_ct = math.cosh(eta) * value['ctM'] + math.sinh(eta) * value['xM']
        assert back_x == pytest.approx(x, abs=2e-11)
        assert back_ct == pytest.approx(ct, abs=2e-11)
        assert (value['ctM'] - value['xM']) * (value['ctM'] + value['xM']) == pytest.approx(ct * ct - x * x, abs=1e-9)
        if ct * ct >= x * x and ct:
            assert math.copysign(1, value['ctM']) == math.copysign(1, ct)
    pairs = [dict(xM=3, ctM=5), dict(xM=5, ctM=3), dict(xM=5, ctM=5), dict(xM=0, ctM=0)]
    intervals = actual('interval', [[p] for p in pairs])
    assert [v['type'] for v in intervals] == ['timelike', 'spacelike', 'null', 'coincident']
    assert intervals[0]['properTimeS'] == pytest.approx(4 / C)
    assert intervals[1]['properDistanceM'] == pytest.approx(4)
    reversed_pair = actual('eventSnapshot', [[dict(beta=.8, eventXM=30, eventCtM=10)]])[0]
    assert reversed_pair['boosted']['ctM'] < 0
    assert reversed_pair['invariant']['type'] == 'spacelike'


def test_lifetime_mean_and_length_simultaneity_with_exact_assessed_values():
    quad = pytest.importorskip('scipy.integrate').quad
    cases = [dict(beta=b, properTimeUs=t, properLengthM=length)
             for b in [-.995, -.6, 0, .6, .995]
             for t, length in [(2, 10), (.1, 1), (10, 40)]]
    for state, value in zip(cases, actual('clockSnapshot', [[s] for s in cases])):
        b = state['beta']
        proper_elapsed = quad(lambda _t: math.sqrt(1 - b * b), 0,
                              value['labLifetimeUs'] * 1e-6, epsabs=1e-16)[0]
        assert proper_elapsed == pytest.approx(state['properTimeUs'] * 1e-6, rel=2e-13)
        assert value['decayRest']['xM'] == pytest.approx(0, abs=5e-9)
        assert value['decayRest']['ctM'] / C == pytest.approx(proper_elapsed, rel=2e-13)
        assert value['rodLabEvents'][0]['ctM'] == value['rodLabEvents'][1]['ctM']
        assert value['rodRestEvents'][1]['xM'] - value['rodRestEvents'][0]['xM'] == pytest.approx(state['properLengthM'])
        assert value['rodRestEvents'][1]['ctM'] != 0 if b else value['rodRestEvents'][1]['ctM'] == 0
        assert value['rodLabDifferentTimes'][1]['ctM'] != 0 if b else value['rodLabDifferentTimes'][1]['ctM'] == 0
    fixture = actual('clockSnapshot', [[dict(beta=math.sqrt(24)/5, properTimeUs=2)],
                                       [dict(beta=math.sqrt(21)/5, properLengthM=10)]])
    assert fixture[0]['labLifetimeUs'] == pytest.approx(10, abs=1e-13)
    assert fixture[1]['lengthLabM'] == pytest.approx(4, abs=1e-13)


def test_pole_barn_door_events_and_pole_frame_simultaneous_barn_length():
    states = [dict(poleLengthM=length, barnLengthM=barn, barnBeta=beta)
              for length, barn in [(20, 10), (40, 5), (3, 30)]
              for beta in [.01, .6, math.sqrt(3)/2, .995]]
    for state, value in zip(states, actual('barnSnapshot', [[s] for s in states])):
        beta, barn = state['barnBeta'], state['barnLengthM']
        eta = math.atanh(beta)
        exit_event = value['doorEventsPole'][1]
        assert exit_event['xM'] == pytest.approx(math.cosh(eta) * barn)
        assert exit_event['ctM'] == pytest.approx(-math.sinh(eta) * barn)
        assert exit_event['ctM'] < 0
        assert exit_event['ctM'] ** 2 - exit_event['xM'] ** 2 == pytest.approx(-barn ** 2, abs=2e-10)
        # Intersect the exit worldline x′=L/γ−βct′ with ct′=0.
        assert value['poleFrameSimultaneousBarnEnds'][1]['xM'] == pytest.approx(barn / math.cosh(eta))
        rear, front = value['worldlinesPole'][2:]
        for point in rear['points']:
            assert point['xM'] == pytest.approx(0, abs=2e-10)
        for point in front['points']:
            assert point['xM'] == pytest.approx(state['poleLengthM'], abs=2e-10)
    example = actual('barnSnapshot', [[dict(poleLengthM=20, barnLengthM=10, barnBeta=math.sqrt(3)/2)]])[0]
    assert example['contractedPoleM'] == pytest.approx(10)
    assert example['contractedBarnM'] == pytest.approx(5)
    assert example['fitsAtBarnTimeZero']
    assert example['doorTimeDifferencePoleS'] == pytest.approx(-10*math.sqrt(3)/C)


def test_velocity_addition_by_rapidity_energy_invariant_and_assessed_fixtures():
    pairs = [(a, b) for a in [-.995, -.5, 0, .5, .995]
             for b in [-.995, -.5, 0, .5, .995]]
    for (u, v), value in zip(pairs, actual('relativeVelocity', [[u, v] for u, v in pairs])):
        assert value == pytest.approx(math.tanh(math.atanh(u)-math.atanh(v)), abs=3e-15)
        assert abs(value) < 1
    states = [dict(particleGamma=g, restEnergyMeV=e) for g in [1, 1.1, 5, 10] for e in [1, 500, 1000]]
    for state, value in zip(states, actual('momentumSnapshot', [[s] for s in states])):
        eta = math.acosh(state['particleGamma'])
        assert value['totalEnergyMeV'] == pytest.approx(state['restEnergyMeV'] * math.cosh(eta))
        assert value['pcMeV'] == pytest.approx(state['restEnergyMeV'] * math.sinh(eta), abs=1e-10)
        assert value['invariantMeV2'] == pytest.approx(state['restEnergyMeV'] ** 2, rel=5e-14)
    assessed = actual('momentumSnapshot', [[dict(shipABeta=.5, shipBBeta=-.5, restEnergyMeV=500, particleGamma=5)]])[0]
    assert assessed['relativeSpeedC'] == pytest.approx(.8)
    assert assessed['stationClosingRateC'] == 1
    assert assessed['totalEnergyMeV'] == 2500
    assert assessed['gamma'] == 5


def test_constant_proper_acceleration_independent_time_ode_and_quadrature():
    solve_ivp = pytest.importorskip('scipy.integrate').solve_ivp
    states = [dict(accelerationG=g, crewYears=years, restEnergyMeV=500)
              for g in [.1, 1, 2] for years in [0, .3, 2, 5]]
    for state, value in zip(states, actual('accelerationSnapshot', [[s] for s in states])):
        a, tau = state['accelerationG'] * G0, state['crewYears'] * YEAR
        # y0=a*t/c, y1=a*x/c². Integrate dt/dτ=√(1+(at/c)²),
        # dx/dτ=at, independent of the production hyperbolic worldline.
        end = a * tau / C
        if end:
            solution = solve_ivp(lambda _eta, y: [math.sqrt(1+y[0]**2), y[0]],
                                 (0, end), [0, 0], method='DOP853', rtol=2e-13, atol=1e-14)
            assert solution.success
            y0, y1 = solution.y[:, -1]
            assert value['tS'] == pytest.approx(C/a*y0, rel=3e-12)
            assert value['xM'] == pytest.approx(C*C/a*y1, rel=3e-12)
            beta_from_ode = y0/math.sqrt(1+y0*y0)
            assert value['beta'] == pytest.approx(beta_from_ode, abs=3e-14)
        else:
            assert value['tS'] == value['xM'] == value['beta'] == 0
        assert value['beta'] < 1
        assert value['oneMinusBeta'] > 0
        assert value['oneMinusBeta'] == pytest.approx(1-value['beta'], rel=2e-8, abs=1e-16)
        assert value['coordinateAccelerationMS2'] == pytest.approx(a/value['gamma']**3)
        assert math.isfinite(value['totalEnergyMeV'])
        assert value['restEnergyMeV'] == 500
        assert value['totalEnergyMeV']-value['kineticEnergyMeV'] == pytest.approx(500, abs=2e-9)
    zero = actual('properAccelerationAt', [[0, 10, 500]])[0]
    assert zero['tS'] == 10 and zero['xM'] == zero['beta'] == 0


def test_tower_schwarzschild_clock_ratio_high_precision_and_differential_rotation():
    states = [dict(heightM=h, elapsedDays=365.25, latitudeDeg=lat)
              for h in [0, .33, 100, 1000] for lat in [0, 45, 90]]
    for state, value in zip(states, actual('towerSnapshot', [[s] for s in states])):
        with localcontext() as context:
            context.prec = 60
            rs = 2 * Decimal(str(GM)) / Decimal(C) ** 2
            r = Decimal(R)
            h = Decimal(str(state['heightM']))
            ratio = ((1-rs/(r+h))/(1-rs/r)).sqrt()-1
            expected = float(ratio)
        assert value['gravFraction'] == pytest.approx(expected, rel=3e-14, abs=1e-30)
        top_v = OMEGA*(R+state['heightM'])*math.cos(math.radians(state['latitudeDeg']))
        foot_v = OMEGA*R*math.cos(math.radians(state['latitudeDeg']))
        rotation = -(top_v**2-foot_v**2)/(2*C*C)
        assert value['rotFraction'] == pytest.approx(rotation, rel=3e-9, abs=1e-30)
        assert value['netGainUs'] == pytest.approx((expected+rotation)*YEAR*1e6, rel=2e-12, abs=1e-14)
        if state['heightM']:
            assert value['netGainUs'] > 0
        else:
            assert value['netGainUs'] == 0
    example = actual('towerSnapshot', [[dict(heightM=100, elapsedDays=365.25, latitudeDeg=45)]])[0]
    assert example['netGainUs'] == pytest.approx(.343442094, rel=1e-7)


def test_gps_signed_rate_prescription_and_range_equivalent_not_position_error():
    states = [dict(orbitAltitudeKm=h, latitudeDeg=lat, elapsedDays=day, clockCorrection=correction)
              for h in [1000, 20200, 40000] for lat in [0, 45, 90]
              for day, correction in [(1, 'uncorrected'), (365.25, 'corrected')]]
    for state, value in zip(states, actual('gpsSnapshot', [[s] for s in states])):
        radius = R+state['orbitAltitudeKm']*1000
        potential_difference = -GM/radius+GM/R
        v_orbit2 = GM/radius
        v_ground2 = (OMEGA*R*math.cos(math.radians(state['latitudeDeg'])))**2
        expected_gr = potential_difference/C**2
        expected_sr = -(v_orbit2-v_ground2)/(2*C**2)
        assert value['gravUsDay'] == pytest.approx(expected_gr*DAY*1e6)
        assert value['srUsDay'] == pytest.approx(expected_sr*DAY*1e6)
        assert value['netUsDay'] == pytest.approx((expected_gr+expected_sr)*DAY*1e6)
        assert (1+value['preoffsetFraction'])*(1+expected_gr+expected_sr) == pytest.approx(1, abs=2e-16)
        assert value['displayGainUs'] == (0 if state['clockCorrection']=='corrected' else value['uncorrectedGainUs'])
        assert value['rangeEquivalentM'] == pytest.approx(C*value['uncorrectedGainUs']*1e-6)
    gps = actual('gpsSnapshot', [[dict(orbitAltitudeKm=20200, latitudeDeg=45, elapsedDays=1)]])[0]
    assert 45 < gps['gravUsDay'] < 46
    assert -8 < gps['srUsDay'] < -7
    assert 38 < gps['netUsDay'] < 39
    assert gps['roundedNetUsDay'] == 38
    assert gps['historicalGPSOffsetFraction'] < 0


def test_equivalence_tidal_hessian_finite_extent_and_local_zero_limits():
    np = pytest.importorskip('numpy')
    def gravity(position):
        p = np.asarray(position, dtype=float)
        return -GM*p/np.linalg.norm(p)**3
    reference = np.array([R, 0, 0], float)
    delta = 100
    jacobian = np.column_stack([(gravity(reference+delta*np.eye(3)[j])-gravity(reference-delta*np.eye(3)[j]))/(2*delta) for j in range(3)])
    states = [dict(capsuleHeightM=h, capsuleWidthM=w, fallTimeS=t)
              for h, w in [(0, 0), (2, 2), (1000, 1000), (.00001, .00001)] for t in [0, 1, 10]]
    for state, value in zip(states, actual('equivalenceSnapshot', [[s] for s in states])):
        assert value['radialGradient'] == pytest.approx(jacobian[0, 0], rel=2e-9)
        assert value['transverseGradient'] == pytest.approx(jacobian[1, 1], rel=2e-9)
        assert value['radialGradient']+2*value['transverseGradient'] == pytest.approx(0, abs=1e-20)
        expected_radial = GM*state['capsuleHeightM']*(2*R+state['capsuleHeightM'])/(R*R*(R+state['capsuleHeightM'])**2)
        assert value['radialInitialRelativeAccelerationMS2'] == pytest.approx(expected_radial, rel=3e-14)
        transverse = gravity([R, state['capsuleWidthM']/2, 0])[1]-gravity([R, -state['capsuleWidthM']/2, 0])[1]
        assert value['transverseInitialRelativeAccelerationMS2'] == pytest.approx(transverse, abs=1e-18)
        assert value['radialChangeM'] == pytest.approx(.5*jacobian[0, 0]*state['capsuleHeightM']*state['fallTimeS']**2, rel=2e-9, abs=1e-24)
        assert value['transverseChangeM'] == pytest.approx(.5*jacobian[1, 1]*state['capsuleWidthM']*state['fallTimeS']**2, rel=2e-9, abs=1e-24)
        assert value['radialChangeM'] >= 0 and value['transverseChangeM'] <= 0
        assert value['radialCurvatureMInverse2']*C*C == pytest.approx(value['radialGradient'])
        if not state['fallTimeS'] or not state['capsuleHeightM']:
            assert value['radialChangeM'] == 0
        if not state['fallTimeS'] or not state['capsuleWidthM']:
            assert value['transverseChangeM'] == 0
        assert value['rindlerTopProperAcceleration'] <= value['rindlerBottomProperAcceleration']


def test_sagnac_independent_null_reception_intersections_and_detector_proper_integral():
    brentq = pytest.importorskip('scipy.optimize').brentq
    quad = pytest.importorskip('scipy.integrate').quad
    states = [dict(ringRadiusM=r, ringBeta=b, flightFraction=f)
              for r in [.1, 10, 10000] for b in [-.6, -.1, 0, 10/C, .1, .6] for f in [0, .47, 1]]
    for state, value in zip(states, actual('sagnacSnapshot', [[s] for s in states])):
        radius, b = state['ringRadiusM'], state['ringBeta']
        # Solve in q = ct/R to avoid a seconds root tolerance swallowing tiny rings.
        plus_q = brentq(lambda q: q-(b*q+2*math.pi), 0, 20, xtol=1e-14)
        minus_q = brentq(lambda q: -q-(b*q-2*math.pi), 0, 20, xtol=1e-14)
        expected_plus, expected_minus = plus_q*radius/C, minus_q*radius/C
        assert value['tPlusS'] == pytest.approx(expected_plus, rel=3e-14)
        assert value['tMinusS'] == pytest.approx(expected_minus, rel=3e-14)
        for light_key, detector_key in [('plusArrival', 'detectorPlus'), ('minusArrival', 'detectorMinus')]:
            light, detector = value[light_key], value[detector_key]
            assert light['xM'] == pytest.approx(detector['xM'], abs=3e-10)
            assert light['yM'] == pytest.approx(detector['yM'], abs=3e-10)
            assert light['tS'] == detector['tS']
        # Same rotating clock integrates dτ = sqrt(1−β²)dt between receptions.
        integrated = quad(lambda _t: math.sqrt(1-b*b), expected_minus, expected_plus, epsabs=1e-25)[0]
        if abs(b) > 1e-6 or b == 0:
            assert value['deltaProperS'] == pytest.approx(integrated, rel=3e-13, abs=1e-25)
        else:
            # Stable low-speed oracle preserves differences smaller than subtraction precision.
            assert value['deltaProperS'] == pytest.approx(4*math.pi*radius*b/(C*math.sqrt(1-b*b)), rel=3e-14)
        assert value['coordinateLoopLengthM'] == pytest.approx(2*math.pi*radius)
        assert value['localLightSpeedMS'] == C
        assert value['inertialDistancePlusM'] == pytest.approx(C*expected_plus)
        assert value['inertialDistanceMinusM'] == pytest.approx(C*expected_minus)
        assert value['nowS'] == pytest.approx(state['flightFraction']*max(expected_plus, expected_minus))
        if b:
            assert math.copysign(1, value['deltaProperS']) == math.copysign(1, b)
        else:
            assert value['deltaTS'] == value['deltaProperS'] == 0



def test_exact_curriculum_binding_rejects_cross_lesson_and_unknown_props():
    from copy import deepcopy
    from primer.curriculum import _validate_lesson_media
    data = json.loads((ROOT / 'data/curriculum/03-physics.json').read_text())
    def find(value):
        if isinstance(value, dict):
            if value.get('id') == 'phys.4.relativity':
                return value
            for child in value.values():
                found = find(child)
                if found:
                    return found
        elif isinstance(value, list):
            for child in value:
                found = find(child)
                if found:
                    return found
        return None
    node = find(data)
    assert node is not None
    media = [m for m in node['lesson_media'] if m.get('renderer') == 'physics-relativity-lab']
    assert len(media) == 1
    assert media[0]['props'] == {'scenario': 'phys.4.relativity.events-clocks'}
    _validate_lesson_media(node)
    cross_lesson = {'id': 'phys.4.quantum', 'lesson_media': deepcopy(media)}
    with pytest.raises(ValueError, match='cross-lesson'):
        _validate_lesson_media(cross_lesson)
    unknown = {'id': node['id'], 'lesson_media': deepcopy(media)}
    unknown['lesson_media'][0]['props']['unexpected'] = 1
    with pytest.raises(ValueError):
        _validate_lesson_media(unknown)


def test_small_proper_time_and_resolved_near_light_speed_readout():
    small = actual('properAccelerationAt', [[G0, 1e-18, 500]])[0]
    assert small['beta'] == pytest.approx(G0*1e-18/C, rel=3e-14)
    assert small['xM'] == pytest.approx(.5*G0*1e-36, rel=3e-14)
    assert small['kineticEnergyMeV'] > 0
    large = actual('build', [[dict(mode='acceleration', accelerationG=2, crewYears=5)]])[0]
    assert 0 < large['current']['beta'] < 1
    assert 'v/c = 1,' not in large['readout']
    assert 'v/c = 0.999999' in large['readout']
    assert large['current']['oneMinusBeta'] > 0
