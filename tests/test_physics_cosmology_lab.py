"""Independent quadrature, geodesic, tensor, distance and spectrum oracles."""
import json
import math
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
C = 299792458
MPC = 3.085677581491367e22
YEAR = 31557600
G = 6.67430e-11
GM_SUN = 1.3271244e20


def actual(name, states):
    script = "const l=require('./web/physics-cosmology-lab.js');const x=JSON.parse(process.argv[1]);process.stdout.write(JSON.stringify(x.map(s=>l[process.argv[2]](s))));"
    r = subprocess.run(['node', '-e', script, json.dumps(states), name], cwd=ROOT, text=True, capture_output=True, check=True)
    return json.loads(r.stdout)


def test_analytic_and_rendered_quantitative_values_exact_drafts_and_full_stations():
    r = subprocess.run(['node', 'tools/check_physics_cosmology_lab.js'], cwd=ROOT, text=True, capture_output=True, check=True)
    assert '371 independent analytic' in r.stdout
    assert 'across 8 full stations' in r.stdout
    assert 'calibrated SVG curves' in r.stdout
    assert 'exact draft/blur/Enter/Escape' in r.stdout


def test_independent_friedmann_age_acceleration_and_infinite_endpoint_horizons():
    quad = pytest.importorskip('scipy.integrate').quad
    states = [dict(H0=h, omegaM=m, omegaR=r, omegaLambda=l, scaleFactor=a)
              for h, m, r, l in [(70, .3, .000085, .699915), (67.4, .315, .000092, .684908),
                                 (70, 1, 0, 0), (70, 0, 1, 0), (70, .3, 0, 0)]
              for a in [.00001, .001, .3, 1, 2]]
    for s, e, horizon in zip(states, actual('expansionSnapshot', states), actual('horizonSnapshot', states)):
        m, r, l = s['omegaM'], s['omegaR'], s['omegaLambda']
        k = 1-m-r-l
        a = s['scaleFactor']
        h0 = s['H0']*1000/MPC
        hubble_gyr = 1/h0/YEAR/1e9
        E = lambda x: math.sqrt(r*x**-4 + m*x**-3 + k*x**-2 + l)
        t = quad(lambda x: 1/(x*E(x)), 0, a, epsabs=1e-12, epsrel=1e-11)[0]
        eta = quad(lambda x: 1/(x*x*E(x)), 0, a, epsabs=1e-11, epsrel=1e-10)[0]
        assert e['ageGyr'] == pytest.approx(t*hubble_gyr, rel=2e-8, abs=2e-10)
        assert e['E'] == pytest.approx(E(a), rel=2e-14)
        assert e['q'] == pytest.approx((m/(2*a**3)+r/a**4-l)/E(a)**2, rel=2e-14, abs=1e-14)
        assert horizon['particleProperMpc'] == pytest.approx(a*C/h0/MPC*eta, rel=3e-8, abs=1e-6)
        if l:
            future = quad(lambda x: 1/(x*x*E(x)), a, math.inf, epsabs=1e-10, epsrel=1e-10)[0]
            assert horizon['eventProperMpc'] == pytest.approx(a*C/h0/MPC*future, rel=3e-8)
        else:
            assert horizon['eventProperMpc'] is None
    for s, h in zip([dict(omegaM=0, omegaR=0, omegaLambda=0), dict(omegaM=0, omegaR=0, omegaLambda=1)],
                    actual('horizonSnapshot', [dict(omegaM=0, omegaR=0, omegaLambda=0), dict(omegaM=0, omegaR=0, omegaLambda=1)])):
        assert h['particleProperMpc'] is None
        assert (h['eventProperMpc'] is None) == (s['omegaLambda'] == 0)


def test_independent_tensor_components_pressure_continuity_and_ricci_trace():
    states = [dict(H0=70, omegaM=.3, omegaR=.000085, omegaLambda=.699915, scaleFactor=a) for a in [.00001, .001, .2, 1, 3]]
    for s, g in zip(states, actual('geometrySnapshot', states)):
        a = s['scaleFactor']
        h0 = 70000/MPC
        H2 = h0*h0*(s['omegaM']/a**3+s['omegaR']/a**4+s['omegaLambda'])
        hdot = -h0*h0*(1.5*s['omegaM']/a**3+2*s['omegaR']/a**4)
        assert g['G00M2'] == pytest.approx(3*H2/C**2, rel=3e-14)
        assert g['GiiM2'] == pytest.approx(-(2*hdot+3*H2)/C**2, rel=2e-10, abs=1e-60)
        assert g['RicciScalarM2'] == pytest.approx(6*(hdot+2*H2)/C**2, rel=2e-10)
        assert g['left00M2'] == pytest.approx(8*math.pi*G*g['T00Jm3']/C**4, rel=3e-14)
        assert g['leftiiM2'] == pytest.approx(8*math.pi*G*g['TiiPa']/C**4, rel=5e-8, abs=1e-65)
        # Independently conserved dust/radiation: a dρ/da = -3(ρ+p/c²).
        rho0 = 3*h0*h0/(8*math.pi*G)
        derivative_times_a = rho0*(-3*s['omegaM']/a**3-4*s['omegaR']/a**4)
        assert derivative_times_a == pytest.approx(-3*(g['rhoKgM3']+g['pressurePa']/C**2), rel=3e-14)


def test_independent_distance_quadrature_curvature_reciprocity_and_supernova_flux():
    quad = pytest.importorskip('scipy.integrate').quad
    states = [dict(H0=70, omegaM=m, omegaR=r, omegaLambda=l, snRedshift=z)
              for m, r, l in [(.3, .000085, .699915), (.3, 0, 0), (1.5, 0, 0), (1, 0, 0)] for z in [.01, .2, .5, 1, 3]]
    for s, d in zip(states, actual('distanceSnapshot', states)):
        m, r, l, z = s['omegaM'], s['omegaR'], s['omegaLambda'], s['snRedshift']
        k = 1-m-r-l
        chi = quad(lambda q: 1/math.sqrt(r*(1+q)**4+m*(1+q)**3+k*(1+q)**2+l), 0, z, epsabs=1e-12)[0]
        trans = chi if abs(k)<1e-12 else math.sinh(math.sqrt(k)*chi)/math.sqrt(k) if k>0 else math.sin(math.sqrt(-k)*chi)/math.sqrt(-k)
        dm = C/70000*trans
        dl = (1+z)*dm
        assert d['current']['radialComovingMpc'] == pytest.approx(C/70000*chi, rel=2e-10)
        assert d['current']['luminosityMpc'] == pytest.approx(dl, rel=2e-10)
        assert d['current']['angularDiameterMpc'] == pytest.approx(dl/(1+z)**2, rel=2e-10)
        assert d['current']['distanceModulus'] == pytest.approx(5*math.log10(dl)+25, abs=2e-9)
        assert d['relativeFlux'] == pytest.approx(10**(-.4*d['deltaMagnitude']), rel=3e-14)

    # A concrete counterexample prevents implying that dimming versus one
    # matter-only comparator alone logically proves acceleration.
    open_matter = actual('distanceSnapshot', [dict(omegaM=.3, omegaR=0, omegaLambda=0, snRedshift=.5)])[0]
    assert open_matter['deltaMagnitude'] > 0
    assert open_matter['q0'] == pytest.approx(.15)


def test_independent_blackhole_geodesic_quadrature_regular_horizon_and_outgoing_light():
    integrate = pytest.importorskip('scipy.integrate')
    states = [dict(massSolar=mass, fallStartRs=5, radiusRs=r) for mass in [1, 10, 100] for r in [.2, .8, 1, 1.001, 1.2, 3]]
    for s, b in zip(states, actual('blackholeSnapshot', states)):
        r = s['radiusRs']
        rs = 2*GM_SUN*s['massSolar']/C**2
        proper = integrate.quad(lambda x: math.sqrt(x), r, 5, epsabs=1e-12)[0]
        advanced = integrate.quad(lambda x: x/(math.sqrt(x)+1), r, 5, epsabs=1e-12)[0]
        assert b['event']['properTimeS'] == pytest.approx(proper*rs/C, rel=3e-13)
        assert b['event']['advancedTimeS'] == pytest.approx(advanced*rs/C, rel=3e-13)
        assert b['kretschmannM4'] == pytest.approx(12/rs**4/r**6, rel=3e-13)
        if r>1:
            t = integrate.quad(lambda x: x**1.5/(x-1), r, 5, epsabs=1e-10, epsrel=1e-10)[0]
            assert b['event']['schwarzschildTimeS'] == pytest.approx(t*rs/C, rel=1e-10)
            assert b['event']['frequencyAtInfinityRatio'] == pytest.approx(1-1/math.sqrt(r), rel=2e-13)
        else:
            assert b['event']['schwarzschildTimeS'] is None
    states = [dict(bhView='cones', efRadius=r, efTime=-1.3, efSpan=.5) for r in [.8, 1, 1.2, 3]]
    for s, b in zip(states, actual('blackholeSnapshot', states)):
        pts = b['nullRay']
        solution = integrate.solve_ivp(lambda _v, r: [(1-1/r[0])/2], (0, .5), [s['efRadius']],
                                       rtol=1e-11, atol=1e-12, dense_output=True)
        for p in pts:
            assert p['rRs'] == pytest.approx(solution.sol(p['vRsC']-s['efTime'])[0], rel=3e-9, abs=3e-10)


def test_blackbody_temperature_and_primordial_spectrum_are_not_fabricated_observations():
    r = actual('redshiftSnapshot', [dict(redshift=3000/2.7255-1, cmbT0=2.7255)])[0]
    assert r['emittedTemperatureK'] == pytest.approx(3000)
    assert r['observedPeakMicrom'] == pytest.approx(2.897771955e3/2.7255)
    states = [dict(ns=n, running=q, amplitude1e9=2.1, pivotK=.05) for n in [.8, .9649, 1, 1.2] for q in [-.05, 0, .05]]
    for s, p in zip(states, actual('inflationSnapshot', states)):
        for row in p['spectrum']:
            x = math.log(row['k']/.05)
            assert row['power'] == pytest.approx(2.1e-9*math.exp((s['ns']-1)*x+.5*s['running']*x*x), rel=3e-14)
    note = actual('build', [dict(mode='inflation'), dict(mode='distances')])
    assert 'not the angular CMB' in note[0]['note']
    assert 'not copied or synthetic observed' in note[1]['note']


def test_closed_turnaround_bounce_and_vacuum_coordinate_origin_are_distinct():
    states = [dict(omegaM=1.5, omegaR=0, omegaLambda=0, scaleFactor=a) for a in [.1, 1, 2, 2.999997, 3]]
    for s, r in zip(states, actual('expansionSnapshot', states)):
        assert r['futureBarrier'] == pytest.approx(3)
        if s['scaleFactor'] == 3:
            assert r['ageGyr'] is None
            assert r['E'] is None
        else:
            eta = math.acos(1-2*.5*s['scaleFactor']/1.5)
            t_h0 = 1.5/(2*.5**1.5)*(eta-math.sin(eta))
            assert r['ageGyr']/r['hubbleGyr'] == pytest.approx(t_h0, rel=2e-9)
    states = [dict(omegaM=.05, omegaR=0, omegaLambda=1.5),
              dict(omegaM=0, omegaR=0, omegaLambda=0),
              dict(omegaM=0, omegaR=0, omegaLambda=.7),
              dict(omegaM=0, omegaR=0, omegaLambda=1)]
    bounce, milne, open_ds, flat_ds = actual('expansionSnapshot', states)
    assert bounce['ageGyr'] is None and 0 < bounce['pastBarrier'] < 1
    assert not milne['bigBang'] and milne['finiteScaleOrigin']
    assert not open_ds['bigBang'] and open_ds['finiteScaleOrigin']
    assert not flat_ds['bigBang'] and not flat_ds['finiteScaleOrigin'] and flat_ds['ageGyr'] is None
