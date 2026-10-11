"""Independent quadrature, differential operators and surface/current oracles."""
import json
import math
from pathlib import Path
import shutil
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[1]
NODE = shutil.which('node')
C = 299792458
MU = 1.25663706127e-6
EPS = 1 / (MU * C * C)


def actual(method, arguments):
    if NODE is None:
        pytest.skip('Node required to inspect the delivered browser core')
    result = subprocess.run([NODE, '-e', """
const l=require('./web/physics-maxwell-lab.js');
const input=JSON.parse(require('fs').readFileSync(0,'utf8'));
process.stdout.write(JSON.stringify(input.arguments.map(args=>l[input.method](...args))));
"""], cwd=ROOT, input=json.dumps(dict(method=method, arguments=arguments)),
                            text=True, capture_output=True, check=True)
    return json.loads(result.stdout)


def test_mounted_scope_exact_drafts_calibrated_curves_and_current_speech():
    if NODE is None:
        pytest.skip('Node required')
    result = subprocess.run([NODE, str(ROOT / 'tools/check_physics_maxwell_lab.js')],
                            cwd=ROOT, text=True, capture_output=True, check=True)
    assert '7 Maxwell stations' in result.stdout
    assert '382 calibrated SVG curves' in result.stdout
    assert 'exact draft/blur/Enter/Escape controls' in result.stdout


def test_magnetic_cut_cap_surface_integral_normal_continuity_and_divergence():
    """Integrate the exterior dipole normal component, not the cap-flux formula."""
    quad = pytest.importorskip('scipy.integrate').quad
    states = [dict(magnetRadiusM=a, magnetizationKA=M, cutFraction=h)
              for a in [.02, .1, .3] for M in [-300, 0, 100]
              for h in [-.9, 0, .9]]
    for s, m in zip(states, actual('magneticSnapshot', [[s] for s in states])):
        a, moment = s['magnetRadiusM'], m['dipoleMomentAM2']
        theta_cut = math.acos(s['cutFraction'])
        cap = quad(lambda theta: MU * moment / (4 * math.pi * a**3)
                   * 2 * math.cos(theta) * 2 * math.pi * a*a * math.sin(theta),
                   0, theta_cut, epsabs=1e-15)[0]
        assert m['capFluxWB'] == pytest.approx(cap, abs=3e-15)
        disk = quad(lambda radius: -m['BinsideT'] * 2*math.pi*radius, 0,
                    math.sqrt(a*a - m['cutHeightM']**2), epsabs=1e-15)[0]
        assert m['cutFluxWB'] == pytest.approx(disk, abs=3e-15)
        assert cap + disk == pytest.approx(0, abs=3e-15)
    a, M = .1, 100000
    boundary = [[a*math.sin(t), 0, a*math.cos(t)] for t in [.1, .5, 1, 2, 3]]
    fields = actual('magnetField', [[p, a, M] for p in boundary])
    for p, B in zip(boundary, fields):
        normal = [x/a for x in p]
        assert sum(B[i]*normal[i] for i in range(3)) == pytest.approx(2*MU*M/3*normal[2], rel=1e-13)
    points = [[.2, .1, -.15], [.03, .02, .01], [-.4, .02, .2]]
    step = 1e-6
    requests = []
    for p in points:
        for axis in range(3):
            for sign in [-1, 1]:
                q = p.copy()
                q[axis] += sign * step
                requests.append([q, a, M])
    fields = actual('magnetField', requests)
    for index in range(len(points)):
        divergence = sum((fields[index*6+2*i+1][i]-fields[index*6+2*i][i])/(2*step) for i in range(3))
        assert divergence == pytest.approx(0, abs=8e-10)


def test_gauss_volume_and_surface_quadrature_with_signed_sources():
    quad = pytest.importorskip('scipy.integrate').quad
    states = [dict(chargeNC=Q, chargeRadiusM=a, gaussianRadiusRatio=r)
              for Q in [-10, 0, 1] for a in [.02, .1, .3] for r in [0, .4, 1, 1.8, 3]]
    for s, g in zip(states, actual('gaussSnapshot', [[s] for s in states])):
        charge = quad(lambda radius: g['rhoCM3']*4*math.pi*radius**2,
                      0, min(g['radiusM'], g['gaussianRadiusM']), epsabs=1e-20)[0]
        surface_flux = quad(lambda theta: g['radialEVM'] * 2*math.pi*g['gaussianRadiusM']**2*math.sin(theta),
                            0, math.pi, epsabs=1e-12)[0]
        assert g['enclosedChargeC'] == pytest.approx(charge, abs=1e-23)
        assert g['fluxVM'] == pytest.approx(surface_flux, abs=2e-12)
        assert EPS * surface_flux == pytest.approx(charge, abs=2e-23)
    # Differential Gauss law uses a Cartesian central-difference stencil.
    points = [[.01, .02, .03], [.2, .1, .05]]
    requests, step = [], 1e-6
    for p in points:
        for axis in range(3):
            for sign in [-1, 1]:
                q = p.copy(); q[axis] += sign*step
                requests.append([q, .1, 1e-9])
    fields = actual('electricBallField', requests)
    for j, p in enumerate(points):
        div = sum((fields[j*6+2*i+1][i]-fields[j*6+2*i][i])/(2*step) for i in range(3))
        expected = (1e-9/(4*math.pi*.1**3/3)/EPS) if math.dist(p, [0, 0, 0]) < .1 else 0
        assert div == pytest.approx(expected, abs=3e-6)


def test_faraday_oriented_loop_integral_and_local_curl_independent_stencil():
    quad = pytest.importorskip('scipy.integrate').quad
    states = [dict(solenoidRadiusM=a, magneticRateTS=rate, inductionLoopRatio=ratio)
              for a in [.02, .1, .3] for rate in [-10, 0, 1] for ratio in [0, .5, 1, 2, 3]]
    for s, f in zip(states, actual('faradaySnapshot', [[s] for s in states])):
        r = f['loopRadiusM']
        # Evaluate the tangent field at many positions around a counterclockwise path.
        integral = quad(lambda angle: (-f['EphiVM']*math.sin(angle))*(-r*math.sin(angle))
                        + (f['EphiVM']*math.cos(angle))*(r*math.cos(angle)),
                        0, 2*math.pi, epsabs=1e-13)[0]
        magnetic_disk_rate = quad(lambda rho: f['magneticRateTS']*2*math.pi*rho,
                                 0, min(r, f['sourceRadiusM']), epsabs=1e-13)[0]
        assert integral == pytest.approx(-magnetic_disk_rate, abs=4e-14)
        assert f['emfV'] == pytest.approx(integral, abs=4e-14)
    # Build ∂Ey/∂x−∂Ex/∂y from the exported actual field formula at two spatial points.
    def xy_field(x, y, a=.1, rate=2):
        r = math.hypot(x, y)
        e = actual('azimuthalField', [[r, a, rate, 'faraday']])[0]
        return [-e*y/r, e*x/r]
    h = 1e-6
    for x, y, expected in [(.03, .04, -2), (.2, .1, 0)]:
        curl = (xy_field(x+h, y)[1]-xy_field(x-h, y)[1])/(2*h) - (xy_field(x, y+h)[0]-xy_field(x, y-h)[0])/(2*h)
        assert curl == pytest.approx(expected, abs=3e-10)


def test_capacitor_charge_continuity_two_surfaces_and_partial_flux():
    quad = pytest.importorskip('scipy.integrate').quad
    states = [dict(plateRadiusM=a, plateGapMM=d, chargingCurrentA=I,
                   capacitorLoopRatio=ratio, plateChargeNC=Q)
              for a, d in [(.02, 1), (.1, .1), (.3, 1)] for I in [-10, 0, 5]
              for ratio in [0, .5, 1, 1.5, 3] for Q in [-1, 0, 1]]
    for s, c in zip(states, actual('capacitorSnapshot', [[s] for s in states])):
        gap_current = quad(lambda rho: EPS*c['electricRateVMS']*2*math.pi*rho,
                           0, min(c['loopRadiusM'], c['plateRadiusM']), epsabs=1e-12)[0]
        assert c['displacementGapA'] == pytest.approx(gap_current, abs=2e-14)
        assert c['wireSurfaceTotalA'] == pytest.approx(gap_current, abs=2e-14)
        assert 2*math.pi*c['loopRadiusM']*c['BphiT'] == pytest.approx(MU*gap_current, abs=2e-20)
        assert c['capacitanceF']*c['voltageV'] == pytest.approx(c['plateChargeC'], abs=1e-23)
        assert c['chargeRateCS'] == s['chargingCurrentA']
        assert c['gapRadiusRatio'] <= .05
    full, partial = actual('capacitorSnapshot', [[dict(chargingCurrentA=5, capacitorLoopRatio=1.5)],
                                               [dict(chargingCurrentA=5, capacitorLoopRatio=.5)]])
    assert full['displacementTotalA'] == full['displacementGapA'] == 5
    assert partial['displacementGapA'] == 1.25
    assert partial['wireSurfaceDisplacementA'] == -3.75


def test_plane_wave_maxwell_derivatives_cross_product_and_mean_energy():
    quad = pytest.importorskip('scipy.integrate').quad
    states = [dict(mode='wave', polarizationDeg=p, direction=d, waveCycles=t,
                   epsilonFactor=e, muFactor=m, fieldAmplitudeVM=amp, frequencyTHz=f)
              for p in [0, 37, 90] for d in ['forward', 'backward']
              for t in [0, .21] for e, m in [(1, 1), (4, 1), (.25, 4)]
              for amp, f in [(0, 500), (600, 500), (1200, .001)]]
    for s, w in zip(states, actual('waveSnapshot', [[s] for s in states])):
        direction = 1 if s['direction'] == 'forward' else -1
        assert w['lambdaM']*w['frequencyHz'] == pytest.approx(w['speedMS'], rel=2e-15)
        assert w['speedMS']**2*w['epsilonFM']*w['muHM'] == pytest.approx(1, rel=5e-16)
        for point in w['fieldSamples'][::10]:
            E, B = point['EVM'], point['BT']
            assert abs(sum(a*b for a, b in zip(E, B))) <= max(1e-30, 8*math.ulp(1.0)*math.hypot(*E)*math.hypot(*B))
            assert math.hypot(*E) == pytest.approx(w['speedMS']*math.hypot(*B), abs=4e-13)
            cross_z = E[0]*B[1]-E[1]*B[0]
            assert point['SWM2'][2] == pytest.approx(cross_z/w['muHM'], rel=3e-15, abs=2e-12)
            phase = point['phaseRad']
            e_unit = [math.cos(s['polarizationDeg']*math.pi/180), math.sin(s['polarizationDeg']*math.pi/180)]
            # curl E = (-∂Ey/∂z, ∂Ex/∂z,0), minus dB/dt from independent phase derivatives.
            curl_E = [w['kRM']*s['fieldAmplitudeVM']*e_unit[1]*math.sin(phase),
                      -w['kRM']*s['fieldAmplitudeVM']*e_unit[0]*math.sin(phase)]
            minus_dt_B = [s['fieldAmplitudeVM']*w['omegaRS']/w['speedMS']*e_unit[1]*math.sin(phase),
                          -s['fieldAmplitudeVM']*w['omegaRS']/w['speedMS']*e_unit[0]*math.sin(phase)]
            assert curl_E == pytest.approx(minus_dt_B, abs=2e-4, rel=4e-15)
            # curl B = mu epsilon dE/dt is the other source-free curl equation.
            curl_B = [direction*w['kRM']*s['fieldAmplitudeVM']/w['speedMS']*u*math.sin(phase) for u in e_unit]
            rhs = [w['muHM']*w['epsilonFM']*direction*w['omegaRS']*s['fieldAmplitudeVM']*u*math.sin(phase) for u in e_unit]
            assert curl_B == pytest.approx(rhs, rel=5e-15, abs=5e-12)
        mean = quad(lambda phase: s['fieldAmplitudeVM']**2*math.cos(phase)**2/w['impedanceOhm'],
                    0, 2*math.pi, epsabs=1e-10)[0]/(2*math.pi)
        assert w['meanIntensityWM2'] == pytest.approx(mean, rel=5e-15, abs=1e-12)
    w, hypothetical = actual('waveSnapshot', [[{}], [dict(epsilonFactor=4)]])
    assert w['BpeakT']*1e6 == pytest.approx(2.001384571188912)
    assert w['lambdaM']*1e9 == pytest.approx(599.584916)
    assert hypothetical['speedMS'] == pytest.approx(C/2)


def test_coax_radial_volume_current_integral_and_external_cancellation():
    quad = pytest.importorskip('scipy.integrate').quad
    states = [dict(coaxCurrentA=I, returnFraction=ret, coaxLoopRatio=r,
                   coreRadiusMM=a, coaxGapMM=g, sheathThicknessMM=d)
              for a, g, d in [(.5, .5, .5), (1, 2, 1), (3, 5, 3)]
              for I in [-10, 0, 5] for ret in [0, .8, 1, 1.25]
              for r in [0, .1, .5, .9, 1, 1.5, 2]]
    for s, c in zip(states, actual('coaxSnapshot', [[s] for s in states])):
        a, b, outer, r = c['aM'], c['bM'], c['cM'], c['loopRadiusM']
        core_density = c['coreCurrentA']/(math.pi*a*a)
        sheath_density = c['sheathCurrentA']/(math.pi*(outer*outer-b*b))
        enclosed = quad(lambda rho: core_density*2*math.pi*rho, 0, min(a, r), epsabs=1e-12)[0]
        if r > b:
            enclosed += quad(lambda rho: sheath_density*2*math.pi*rho, b, min(outer, r), epsabs=1e-12)[0]
        assert c['enclosedA'] == pytest.approx(enclosed, abs=8e-15)
        assert 2*math.pi*r*c['BphiT'] == pytest.approx(MU*enclosed, abs=2e-20)
        if s['returnFraction'] == 1 and r >= outer:
            assert c['BphiT'] == 0
            assert c['enclosedA'] == 0


def test_radiation_angular_surface_power_integral_radius_and_dc_limits():
    quad = pytest.importorskip('scipy.integrate').quad
    states = [dict(drive=d, dipoleCurrentA=I, dipoleFrequencyMHz=f,
                   dipoleLengthFraction=length, radiationRadiusLambda=radius,
                   radiationAngleDeg=theta)
              for d in ['ac', 'dc'] for I, f, length in [(0, 100, .01), (1, 1, .001), (5, 1000, .05)]
              for radius in [5, 10, 100] for theta in [0, 45, 90, 180]]
    for s, r in zip(states, actual('radiationSnapshot', [[s] for s in states])):
        Z, k = MU*C, 2*math.pi/r['lambdaM']
        Eeq = Z*k*s['dipoleCurrentA']*r['lengthM']/(4*math.pi*r['radiusM']) if s['drive'] == 'ac' else 0
        integral = quad(lambda theta: Eeq**2*math.sin(theta)**2/(2*Z)*r['radiusM']**2
                        *2*math.pi*math.sin(theta), 0, math.pi, epsabs=1e-12)[0]
        assert r['totalPowerW'] == pytest.approx(integral, rel=3e-15, abs=1e-14)
        assert r['intensityWM2']*r['radiusM']**2 == pytest.approx(r['powerPerSteradianW'], abs=1e-14)
        assert r['kr'] >= 10*math.pi - 1e-12
        assert r['lengthM']/r['lambdaM'] <= .05 + 1e-16
        for p in r['powerSpheres']:
            assert p['meanIntensityWM2']*4*math.pi*p['radiusM']**2 == pytest.approx(integral, abs=1e-13)
            assert p['equatorialIntensityWM2']*p['radiusM']**2 == pytest.approx(Eeq**2*r['radiusM']**2/(2*Z), abs=1e-13)
        if s['radiationAngleDeg'] in [0, 180]:
            assert r['EpeakVM'] == r['BpeakT'] == r['intensityWM2'] == 0
        if s['drive'] == 'dc':
            assert r['totalPowerW'] == r['frequencyHz'] == r['EpeakVM'] == r['BpeakT'] == 0
