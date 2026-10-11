"""Current emitted geometry and independent accepted-Float64 kinematic limits."""
from decimal import Decimal, localcontext
import json
import math
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
PI = Decimal('3.1415926535897932384626433832795028841971693993751058209749445923078164062862089986280348253421170679')


def sine(value):
    term = total = value
    for n in range(1, 90):
        term *= -(value * value) / Decimal((2*n)*(2*n+1))
        total += term
    return total


def test_actual_emitted_singletons_adaptive_facets_and_trusted_geometry_limits():
    result = subprocess.run(['node', 'tools/check_physics_qft_integrated_geometry.js'], cwd=ROOT,
                            capture_output=True, text=True, check=True, timeout=30)
    value = json.loads(result.stdout)
    assert value['singletonStates'] == 27 and value['facetStates'] == 24
    assert value['facetProbes'] == 643552 and value['facets'] == 160888
    assert value['maxObservedError'] < value['errorBudget'] == .02
    assert value['maxFaces'] == 47500


def test_both_transfer_invariants_retain_accepted_subnormal_and_endpoint_magnitudes():
    angles = [0.0, math.nextafter(0.0, 1.0), 5e-322, 1e-321, 1e-200, 1e-7, 90.0,
              math.nextafter(math.nextafter(180.0, 0.0), 0.0), math.nextafter(180.0, 0.0), 180.0]
    momenta = [0.0, math.nextafter(0.0, 1.0), 5e-322, 1e-200, 1.0, 10.0]
    cases = [{'angleDeg': angle, 'momentumMeV': p, 'mode': 'scattering'} for angle in angles for p in momenta]
    code = "const fs=require('node:fs'),q=require('./web/physics-qft-lab.js');process.stdout.write(JSON.stringify(JSON.parse(fs.readFileSync(0,'utf8')).map(s=>{const m=q.build(s);return {state:m.state,d:m.current,ledger:m.ledger,readout:m.readout};})));"
    result = subprocess.run(['node', '-e', code], cwd=ROOT, input=json.dumps(cases),
                            capture_output=True, text=True, check=True, timeout=30)
    values = json.loads(result.stdout)
    assert len(values) == 60
    with localcontext() as context:
        context.prec = 110
        for value in values:
            theta = Decimal.from_float(value['state']['angleDeg'])
            p = Decimal.from_float(value['state']['momentumMeV'])
            for channel, angle in [('t', theta), ('u', Decimal(180)-theta)]:
                zero = p == 0 or angle == 0
                flag = 'zeroTransfer' if channel == 't' else 'uZeroTransfer'
                shell = 'photonOnShell' if channel == 't' else 'uPhotonOnShell'
                assert value['d'][flag] is zero and value['d'][shell] is zero
                if zero:
                    assert value['d'][channel] == 0 and value['d']['log10Abs'+channel.upper()] is None
                    continue
                magnitude = 4*p*p*sine(angle*PI/Decimal(360))**2
                expected_log = float(magnitude.log10())
                assert abs(value['d']['log10Abs'+channel.upper()]-expected_log) < 1e-12
                if value['d'][channel] == 0:
                    assert value['d'][channel+'Underflow'] is True
                    assert 'underflows Float64' in value['readout']
                    row = next(row for row in value['ledger'] if row[0] == channel+' channel q²')
                    assert isinstance(row[1], str) and 'negative' in row[1] and 'Float64 underflow' in row[1]
                else:
                    expected = -float(magnitude)
                    assert abs(value['d'][channel]-expected) <= max(abs(expected)*3e-14, math.ulp(expected)*3)
