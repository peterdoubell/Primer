"""SI mechanics: independent Cartesian and canonical Hamiltonian oracles."""
import copy
import json
import math
from pathlib import Path
import shutil
import subprocess

import pytest
from primer.curriculum import Curriculum, _validate_lesson_media

ROOT = Path(__file__).resolve().parents[1]


def test_actual_constraints_binding_rejects_extra_props_and_cross_lesson():
    node = copy.deepcopy(Curriculum().node('phys.4.classical'))
    model = next(m for m in node['lesson_media'] if m.get('renderer') == 'physics-constraints-lab')
    assert model['props'] == {'scenario': 'phys.4.classical.constraints-energy'}
    _validate_lesson_media(node)
    model['props']['extra'] = True
    with pytest.raises(ValueError, match='physics-constraints-lab'):
        _validate_lesson_media(node)
    del model['props']['extra']
    model['props']['scenario'] = 'phys.3.thermo.cycle-entropy'
    with pytest.raises(ValueError, match='physics-constraints-lab'):
        _validate_lesson_media(node)
    model['props']['scenario'] = 'phys.4.classical.constraints-energy'
    node['id'] = 'phys.3.thermo'
    node['lesson_media'] = [model]
    with pytest.raises(ValueError, match='physics-constraints-lab'):
        _validate_lesson_media(node)


def test_shell_dependency_and_asset_routes():
    shell = (ROOT / 'web/index.html').read_text()
    assert shell.index('/app/physics-constraints-lab.js') < shell.index('/app/lesson-models.js')
    assert '/app/physics-constraints-lab.css' in shell
    assert '"physics-constraints-lab.js"' in (ROOT / 'primer/server.py').read_text()
    assert '"physics-constraints-lab.css"' in (ROOT / 'primer/server.py').read_text()


def run(*args):
    if not shutil.which('node'):
        pytest.skip('Node is required')
    result = subprocess.run(['node', 'tools/check_physics_constraints_lab.js', *args],
                            cwd=ROOT, capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stdout + result.stderr
    return result.stdout


def test_independent_cartesian_work_and_rendered_si_ledgers():
    output = run()
    assert '3645 Cartesian hoop force/work states' in output
    assert '648 Newtonian double-rod states' in output
    assert '115 mounted SI-geometry/energy states' in output


@pytest.fixture(scope='module')
def trajectories():
    return json.loads(run('--json'))


def canonical_oracle(s, sample_times):
    """Integrate canonical momenta, not the runtime's angular accelerations.

    For the double pendulum, velocities come from independently solving its
    kinetic-energy mass matrix. This uses Hamilton's momentum equations and an
    eighth-order adaptive method, independent of the runtime's fixed-step RK4.
    """
    np = pytest.importorskip('numpy')
    solve_ivp = pytest.importorskip('scipy.integrate').solve_ivp
    m, n, l, r, g = (s[k] for k in ('mass', 'mass2', 'length', 'length2', 'gravity'))
    a, b = math.radians(s['angle']), math.radians(s['angle2'])
    w, v, omega = s['rate'], s['rate2'], s['driveOmega']
    if s['mode'] == 'double':
        def matrix(q1, q2):
            return np.array([[(m+n)*l*l, n*l*r*math.cos(q1-q2)],
                             [n*l*r*math.cos(q1-q2), n*r*r]])
        momenta = matrix(a, b) @ np.array([w, v])
        y0 = [a, b, *momenta]
        def rhs(_t, y):
            q1, q2, p1, p2 = y
            u1, u2 = np.linalg.solve(matrix(q1, q2), [p1, p2])
            coupling = n*l*r*math.sin(q1-q2)*u1*u2
            return [u1, u2, -coupling-(m+n)*g*l*math.sin(q1),
                    coupling-n*g*r*math.sin(q2)]
        def rates(y):
            return np.linalg.solve(matrix(y[0], y[1]), y[2:4])
    else:
        inertia = m*l*l
        y0 = [a, inertia*w, 0.0]
        def rhs(_t, y):
            q, p, _work = y
            u = p/inertia
            dp = -m*g*l*math.sin(q)
            power = 0.0
            if s['mode'] == 'hoop':
                dp += inertia*omega*omega*math.sin(q)*math.cos(q)
                power = 2*inertia*omega*omega*math.sin(q)*math.cos(q)*u
            return [u, dp, power]
        def rates(y):
            return [y[1]/inertia]
    reference = solve_ivp(rhs, (0, 4), y0, method='DOP853', rtol=1e-12,
                          atol=2e-13, max_step=.01, t_eval=sample_times)
    assert reference.success, reference.message
    return reference.y.T, rates


def test_all_refined_trajectories_against_independent_canonical_dop853(trajectories):
    # These are absolute coordinate/rate tolerances in radians and rad/s.
    # They include all visible controls' extrema, joint extreme states, zero
    # gravity/drive/rest, and every plotted sample through the full 4 s window.
    for model in trajectories:
        s, points = model['state'], model['points']
        assert points[0]['t'] == 0 and points[-1]['t'] == 4
        reference, rates = canonical_oracle(s, [p['t'] for p in points])
        for point, y in zip(points, reference):
            expected_q = y[:2] if s['mode'] == 'double' else y[:1]
            for actual, expected in zip(point['q'], expected_q):
                assert abs(actual-expected) <= 2e-6, (s, point['t'], 'angle', actual, expected)
            for actual, expected in zip(point['rates'], rates(y)):
                assert abs(actual-expected) <= 2e-5, (s, point['t'], 'rate', actual, expected)
            if s['mode'] == 'hoop':
                energy_scale = max(1, abs(model['start']['Elab']), abs(model['start']['Hreduced']))
                assert abs(point['driveWork']-y[2]) <= 1e-8+2e-7*energy_scale
