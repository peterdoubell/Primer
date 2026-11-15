"""Reviewer-owned physical-oracle and actual-engine regression checks."""
from decimal import Decimal, localcontext
import hashlib
import json
import math
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
C, MPC, GM_SUN, RSUN = 299792458, 3.085677581491367e22, 1.3271244e20, 6.957e8


def build(states):
    script = "const l=require('./web/physics-cosmology-lab.js');process.stdout.write(JSON.stringify(JSON.parse(process.argv[1]).map(s=>l.build(s))));"
    run = subprocess.run(['node', '-e', script, json.dumps(states)], cwd=ROOT,
                         capture_output=True, text=True, check=True)
    return json.loads(run.stdout)


def test_actual_engine_arrows_surfaces_full_charts_markers_and_nine_bus_keys():
    run = subprocess.run(['node', 'tools/check_maxwell_cosmology_independent.js'],
                         cwd=ROOT, capture_output=True, text=True, check=True)
    receipt = json.loads(run.stdout)
    assert receipt == dict(passed=True, maxwellStates=77, cosmologyStates=114,
                          fieldVectors=4428, engineArrowShafts=42336,
                          surfaceFaces=19616, chartPoints=55440, markers=220,
                          stateKeys=9, wholeGoalComplete=False)


def test_flrw_tensor_from_metric_ricci_components_at_80_digit_precision():
    states = [dict(mode='geometry', H0=73, omegaM=m, omegaR=r,
                   omegaLambda=l, scaleFactor=a)
              for m, r, l in [(.27, .00009, .73), (1, 0, 0),
                               (0, 1, 0), (1.5, 0, 0)]
              for a in [.00001, .001, .3, 1, 2]]
    for state, model in zip(states, build(states)):
        a, m, r, l = [state[k] for k in ['scaleFactor', 'omegaM', 'omegaR', 'omegaLambda']]
        # Metric route, not the core's eliminated matter/pressure formula.
        # High precision prevents cancellation of an exactly zero dust Gii
        # against early-epoch components that are many orders larger.
        with localcontext() as context:
            context.prec = 80
            a, m, r, l = map(lambda x: Decimal(str(x)), [a, m, r, l])
            K, h0, c = 1-m-r-l, Decimal(73000)/Decimal(str(MPC)), Decimal(C)
            H2 = h0*h0*(m/a**3+r/a**4+K/a**2+l)
            Hdot = a/2*h0*h0*(-3*m/a**4-4*r/a**5-2*K/a**3)
            spatial_curvature = -K*h0*h0/a**2
            R00 = -3*(Hdot+H2)/c**2
            Rii = (Hdot+3*H2+2*spatial_curvature)/c**2
            scalar = -R00+3*Rii
            expected00, expectedii, expectedscalar = map(float, [R00+scalar/2, Rii-scalar/2, scalar])
        g = model['current']
        assert g['G00M2'] == pytest.approx(expected00, rel=2e-13, abs=1e-65)
        assert g['GiiM2'] == pytest.approx(expectedii, rel=3e-8, abs=1e-63)
        assert g['RicciScalarM2'] == pytest.approx(expectedscalar, rel=3e-8, abs=1e-63)
        assert g['allowed']


def test_all_displayed_horizon_curves_against_exact_matter_radiation_desitter_limits():
    cases = [dict(mode='horizons', H0=70, omegaM=1, omegaR=0, omegaLambda=0),
             dict(mode='horizons', H0=70, omegaM=0, omegaR=1, omegaLambda=0),
             dict(mode='horizons', H0=70, omegaM=0, omegaR=0, omegaLambda=1)]
    scale = C/70000
    for case, model in zip(cases, build(cases)):
        curves = {c['key']: c for c in model['panels'][0]['curves']}
        if case['omegaM']:
            for p in curves['particle']['points']:
                assert p['y'] == pytest.approx(2*scale*10**(1.5*p['x']), rel=1e-10)
            assert 'event' not in curves
        elif case['omegaR']:
            for p in curves['particle']['points']:
                assert p['y'] == pytest.approx(scale*10**(2*p['x']), rel=1e-10)
            assert 'event' not in curves
        else:
            assert 'particle' not in curves
            for p in curves['event']['points']:
                assert p['y'] == pytest.approx(scale, rel=1e-10)
        for p in curves['hubble']['points']:
            expected = scale*(10**(1.5*p['x']) if case['omegaM'] else
                              10**(2*p['x']) if case['omegaR'] else 1)
            assert p['y'] == pytest.approx(expected, rel=1e-12)


def test_physical_blackbody_points_and_log_primordial_axis_values():
    states = [dict(mode='redshift', redshift=z, cmbT0=2.7255) for z in [0, .2, 1100, 1500]]
    for state, model in zip(states, build(states)):
        for key, temp in [('emittedSpectrum', 2.7255*(1+state['redshift'])),
                          ('observedSpectrum', 2.7255)]:
            points = model['current'][key]
            def radiance(wavelength):
                return 2*6.62607015e-34*C*C/wavelength**5/math.expm1(6.62607015e-34*C/(wavelength*1.380649e-23*temp))
            peak = radiance(2.897771955e-3/temp)
            for p in points:
                assert p['x'] == pytest.approx(math.log10(p['lambdaM']*1e6), abs=1e-14)
                assert p['y'] == pytest.approx(math.log10(radiance(p['lambdaM'])/peak), abs=3e-14)
    states = [dict(mode='inflation', ns=n, running=q, pivotK=.027)
              for n in [.8, 1, 1.2] for q in [-.05, 0, .05]]
    for state, model in zip(states, build(states)):
        curve = model['panels'][1]['curves'][0]
        for p in curve['points']:
            x = (p['x']-math.log10(state['pivotK']))*math.log(10)
            expected = math.log10(2.1e-9)+((state['ns']-1)*x+.5*state['running']*x*x)/math.log(10)
            assert p['y'] == pytest.approx(expected, abs=3e-14)


def test_lens_curve_from_transverse_geodesic_acceleration_and_tidal_log_axis():
    quad = pytest.importorskip('scipy.integrate').quad
    states = [dict(mode='blackhole', bhView='lensing', massSolar=mass, impactSolarR=impact)
              for mass, impact in [(1, 1), (100, 1), (10, 3)]]
    for state, model in zip(states, build(states)):
        rs = 2*GM_SUN*state['massSolar']/C**2
        b = state['impactSolarR']*RSUN
        for p in model['current']['rayDisplacement'][::16]:
            x = p['x']*RSUN/b
            # Integrate the weak-field transverse acceleration along a straight
            # zeroth-order ray from past infinity, with zero displacement/slope.
            value = quad(lambda u: -(x-u)/(1+u*u)**1.5, -math.inf, x,
                         epsabs=1e-11, epsrel=1e-11)[0]*rs/1000
            assert p['y'] == pytest.approx(value, rel=3e-11, abs=1e-9)
    for model in build([dict(mode='blackhole', bhView='radius', massSolar=m) for m in [.1, 10, 100]]):
        for p in model['panels'][1]['curves'][0]['points']:
            radius = p['x']*model['current']['rsM']
            invariant = 48*model['current']['GM']**2/(C**4*radius**6)
            assert p['y'] == pytest.approx(math.log10(invariant), abs=2e-13)


def test_independent_review_scope_and_frozen_asset_pins():
    review = json.loads((ROOT/'docs/maxwell-cosmology-independent-review-20261011.json').read_text())
    assert review['independent_of_implementation_authors']
    assert review['whole_goal_complete'] is False
    assert review['production_verification'] is False
    assert len(review['quiz_mapping']['phys.4.em-maxwell']) == 10
    assert len(review['quiz_mapping']['phys.5.gr-cosmo']) == 10
    for path, pin in review['files'].items():
        blob = (ROOT/path).read_bytes()
        assert len(blob) == pin['bytes']
        assert hashlib.sha256(blob).hexdigest() == pin['sha256']
