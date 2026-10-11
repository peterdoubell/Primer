"""Actual scene coordinates with independent graph, ODE, and SI references."""
import copy
from decimal import Decimal, localcontext
import json
import math
from pathlib import Path
import shutil
import subprocess

import pytest

from primer.curriculum import Curriculum, _validate_lesson_media

ROOT = Path(__file__).resolve().parents[1]
C = 299792458
YEAR = 31557600
DAY = 86400
GM = 3.986004418e14
RADIUS = 6378137
G0 = 9.80665


def _node(*args):
    executable = shutil.which("node")
    if executable is None:
        pytest.skip("Node is needed for the actual registered spatial families")
    result = subprocess.run([executable, "tools/check_topology_relativity_spatial.js", *args],
                            cwd=ROOT, capture_output=True, text=True,
                            timeout=90, check=False)
    assert result.returncode == 0, result.stdout + result.stderr
    return json.loads(result.stdout)


@pytest.fixture(scope="module")
def observations():
    return {scene["state"].get("mode", "topology"): scene for scene in _node("--fixtures")}


@pytest.mark.parametrize(("node_id", "family", "former_family"), [
    ("math.5.topology", "topology-open-set-geometry", "topological-object"),
    ("phys.4.relativity", "relativistic-event-geometry", "spacetime-grid"),
])
def test_families_are_bound_to_complete_assessed_lessons(node_id, family, former_family):
    node = copy.deepcopy(Curriculum().node(node_id))
    item = next(media for media in node["lesson_media"] if media.get("renderer") == "spatial-3d"
                and media.get("props", {}).get("scenario") == "module." + node_id)
    assert item["props"]["scenario"] == "module." + node_id
    assert item["props"]["family"] == family
    assert item["props"]["mode"] == "model"
    _validate_lesson_media(node)
    item["props"]["family"] = former_family
    with pytest.raises(ValueError, match="module spatial"):
        _validate_lesson_media(node)


def test_all_station_actual_primitives_and_negative_calibrations():
    report = _node()
    assert report["status"] == "passed"
    assert report["topologyStations"] == 7
    assert report["relativityStations"] == 8
    assert report["topologyStates"] >= 790
    assert report["relativityStates"] >= 130
    assert "calibration mutation rejection" in report["regressionChecks"]
    assert "nonmanifold mutation rejection" in report["regressionChecks"]
    assert "three-digit short gain mutation rejection" in report["regressionChecks"]
    assert "sixteen-digit readout gain mutation rejection" in report["regressionChecks"]
    assert "selected compact-Hausdorff proof prefix retained" in report["regressionChecks"]
    assert "full-state bus with source/cross-lesson/disconnected exclusions" in report["regressionChecks"]


def test_actual_browser_dependency_order_loads_scientific_families_before_registry():
    shell = (ROOT / "web/index.html").read_text()
    bus = shell.index("/app/lesson-state.js")
    topology = shell.index("/app/math-topology-lab.js")
    relativity = shell.index("/app/physics-relativity-lab.js")
    family = shell.index("/app/spatial-fidelity.js")
    objects = shell.index("/app/spatial-module-objects.js")
    registry = shell.index("/app/lesson-models.js")
    # Family definitions defer core lookup until ensure()/render(), so their
    # adapter can load first. Both actual cores must exist before the reader.
    assert family < objects < registry
    assert bus < topology < registry
    assert bus < relativity < registry


def test_actual_genus_three_triangles_affine_map_and_closed_incidence(observations):
    np = pytest.importorskip("numpy")
    scene = observations["topology"]
    source = scene["topology"]["active"]["mesh"]
    surface = next(item for item in scene["topology"]["primitives"] if item["kind"] == "surface")
    state = scene["state"]
    source_vertices = np.array(source["vertices"])
    # Independent matrix maps author coordinates to the displayed rigid frame.
    matrix = np.array([[state["stretch"], state["bend"], 0], [0, 0, 1], [0, -1, 0]])
    vertices = np.array(surface["vertices"])
    assert vertices == pytest.approx(np.einsum("ij,nj->ni", matrix, source_vertices), abs=2e-13)
    assert np.linalg.det(matrix) == pytest.approx(state["stretch"])
    inverse = np.linalg.inv(matrix)
    assert np.einsum("ij,nj->ni", inverse, vertices) == pytest.approx(source_vertices, abs=2e-13)
    faces = np.array(surface["faces"])
    triangles = vertices[faces]
    normals = np.cross(triangles[:, 1] - triangles[:, 0], triangles[:, 2] - triangles[:, 0])
    assert np.linalg.norm(normals, axis=1).min() > 0
    edges = np.sort(np.concatenate([faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]]), axis=1)
    unique, count = np.unique(edges, axis=0, return_counts=True)
    assert set(count) == {2}
    assert len(vertices) - len(unique) + len(faces) == -4
    assert len(faces) == 2304
    # Surface is the double of a plane with three holes. Its two sheets have
    # disjoint positive/negative heights away from identified boundary vertices.
    untransformed = np.einsum("ij,nj->ni", inverse, vertices)
    assert set(np.sign(untransformed[:, 2])) == {-1, 0, 1}


def test_constant_proper_acceleration_against_integrated_four_velocity(observations):
    solve_ivp = pytest.importorskip("scipy.integrate").solve_ivp
    scene = observations["acceleration"]
    state = scene["state"]
    acceleration = state["accelerationG"] * G0
    # Integration in crew years; state is rapidity, coordinate time in years,
    # and distance in light-years. Neither shipped hyperbolic helper is called.
    def derivative(_, values):
        eta = values[0]
        return [acceleration * YEAR / C, math.cosh(eta), math.sinh(eta)]

    end = state["crewYears"]
    reference = solve_ivp(derivative, [0, end], [0, 0, 0], method="DOP853",
                          rtol=2e-13, atol=2e-14, max_step=.05, dense_output=True)
    assert reference.success
    current = scene["relativity"]["current"]
    final = reference.sol(end)
    assert current["rapidity"] == pytest.approx(final[0], abs=2e-12)
    assert current["inertialYears"] == pytest.approx(final[1], rel=3e-12)
    assert current["positionLightYears"] == pytest.approx(final[2], rel=3e-12)
    assert current["beta"] < 1
    assert current["oneMinusBeta"] > 0
    assert current["restEnergyMeV"] == state["restEnergyMeV"]
    panel = scene["relativity"]["panels"][0]
    points = next(curve for curve in panel["curves"] if curve["key"] == "ship")["points"]
    times = current["worldline"]
    for point, event in zip(points[::30], times[::30]):
        expected = reference.sol(event["tauS"] / YEAR)
        assert point["x"] == pytest.approx(expected[2], rel=4e-12, abs=2e-12)
        assert point["y"] == pytest.approx(expected[1], rel=4e-12, abs=2e-12)


def test_invariant_simultaneity_and_energy_ledgers_have_actual_units(observations):
    ledger = lambda mode: {row[0]: row[1:] for row in observations[mode]["ledger"]}
    events = ledger("events")
    assert events["Invariant (ct)² − x²"] == [-800, "m²"]
    assert events["Boosted invariant"][0] == pytest.approx(-800, abs=2e-12)
    assert events["Interval type"] == ["spacelike", ""]
    assert events["Proper duration (timelike only)"] == [None, "s"]
    assert events["Proper separation (spacelike only)"] == [pytest.approx(math.sqrt(800)), "m"]
    clocks = ledger("clocks")
    assert clocks["Mean lifetime in lab"] == [pytest.approx(10), "µs"]
    assert clocks["Lab simultaneous length"] == [pytest.approx(2), "m"]
    assert clocks["Lab endpoint Δt"] == [0, "s"]
    assert clocks["Same endpoints Δt′ in rod frame"] == [pytest.approx(-math.sqrt(24) / 5 * 10 / C), "s"]
    barn = ledger("barn")
    assert barn["Pole length in barn"] == [pytest.approx(10), "m"]
    assert barn["Barn length in pole frame"] == [pytest.approx(5), "m"]
    assert barn["Fits at lab t = 0"] == ["yes", ""]
    assert barn["Door event interval"] == [-100, "m²"]
    momentum = ledger("momentum")
    assert momentum["B velocity in A frame"] == [pytest.approx(-.8), "c"]
    assert momentum["Total energy"] == [2500, "MeV"]
    assert momentum["Kinetic energy"] == [2000, "MeV"]
    assert momentum["Momentum times c"] == [pytest.approx(500 * math.sqrt(24)), "MeV"]
    assert momentum["E² − (pc)²"] == [pytest.approx(500 ** 2), "MeV²"]


def test_tower_clock_ratio_with_high_precision_and_gps_si_rates(observations):
    tower_scene = observations["gravity"]
    # The fixture dictionary contains the last gravity scene (GPS); its model
    # retains both physical ledgers, so the tower ratio is observable as well.
    state = tower_scene["state"]
    tower = tower_scene["relativity"]["current"]["tower"]
    with localcontext() as context:
        context.prec = 60
        mass = Decimal(str(GM))
        speed = Decimal(C)
        foot = Decimal(RADIUS)
        top = foot + Decimal(str(state["heightM"]))
        expected = ((1 - 2 * mass / (speed * speed * top)) /
                    (1 - 2 * mass / (speed * speed * foot))).sqrt() - 1
    assert tower["gravFraction"] == pytest.approx(float(expected), rel=3e-15, abs=0)
    gps = tower_scene["relativity"]["current"]["gps"]
    orbit = RADIUS + 1000 * state["orbitAltitudeKm"]
    ground_speed = 7.292115e-5 * RADIUS * math.cos(math.radians(state["latitudeDeg"]))
    expected_gravity = GM * (1 / RADIUS - 1 / orbit) / C ** 2
    expected_sr = -(GM / orbit - ground_speed ** 2) / (2 * C ** 2)
    assert gps["orbitSpeedMS"] == pytest.approx(math.sqrt(GM / orbit), rel=2e-15)
    assert gps["netUsDay"] == pytest.approx((expected_gravity + expected_sr) * DAY * 1e6, rel=3e-15)
    assert gps["rangeEquivalentM"] == pytest.approx(C * (expected_gravity + expected_sr) * DAY, rel=3e-15)
    ledger = {row[0]: row[1:] for row in tower_scene["ledger"]}
    assert ledger["Assessment rounded contributions"] == ["45 − 7 = 38", "µs/day"]
    assert ledger["c × uncorrected time offset"][1].endswith("one-way range equivalent")


def test_tidal_initial_vectors_and_quadratic_extent_match_newtonian_field(observations):
    np = pytest.importorskip("numpy")
    scene = observations["equivalence"]
    state = scene["state"]
    current = scene["relativity"]["current"]
    def field(point):
        point = np.array(point, dtype=float)
        return -GM * point / np.linalg.norm(point) ** 3

    radial = field([0, 0, RADIUS + state["capsuleHeightM"]]) - field([0, 0, RADIUS])
    transverse = field([state["capsuleWidthM"] / 2, 0, RADIUS]) - field([-state["capsuleWidthM"] / 2, 0, RADIUS])
    assert current["radialInitialRelativeAccelerationMS2"] == pytest.approx(radial[2], rel=2e-9)
    assert current["transverseInitialRelativeAccelerationMS2"] == pytest.approx(transverse[0], rel=3e-15)
    assert current["radialChangeM"] == pytest.approx(GM / RADIUS ** 3 * state["capsuleHeightM"] * state["fallTimeS"] ** 2)
    assert current["transverseChangeM"] == pytest.approx(-GM / (2 * RADIUS ** 3) * state["capsuleWidthM"] * state["fallTimeS"] ** 2)
    assert "second order" in scene["note"]
    assert "not a strong-field" in scene["note"]


def test_sagnac_arrival_roots_detector_proper_time_and_three_actual_coordinates(observations):
    brentq = pytest.importorskip("scipy.optimize").brentq
    scene = observations["sagnac"]
    state = scene["state"]
    current = scene["relativity"]["current"]
    radius = state["ringRadiusM"]
    angular_speed = state["ringBeta"] * C / radius
    # Root variable is dimensionless inertial distance ct/R. Reception occurs
    # when the accumulated relative angle is exactly one signed revolution.
    plus = brentq(lambda u: u - angular_speed * radius / C * u - 2 * math.pi, 0, 100)
    minus = brentq(lambda u: -u - angular_speed * radius / C * u + 2 * math.pi, 0, 100)
    plus_time, minus_time = plus * radius / C, minus * radius / C
    assert current["tPlusS"] == pytest.approx(plus_time, rel=3e-15, abs=0)
    assert current["tMinusS"] == pytest.approx(minus_time, rel=3e-15, abs=0)
    expected_proper = (plus_time - minus_time) * math.sqrt(1 - state["ringBeta"] ** 2)
    assert current["deltaProperS"] == pytest.approx(expected_proper, abs=2e-22)
    circular = scene["relativity"]["circular"]
    for primitive in scene["primitives"]:
        if primitive.get("fidelity_kind") != "circular_worldline":
            continue
        points = current["worldlines"][primitive["key"]]
        for actual, event in zip(primitive["points"], points):
            assert actual[0] == pytest.approx(2 * event["xM"] / radius, abs=2e-14)
            assert actual[1] == pytest.approx(2 * C * event["tS"] / circular["ctScale"], abs=2e-14)
            assert actual[2] == pytest.approx(-8 - 2 * event["yM"] / radius, abs=2e-14)
    assert current["localLightSpeedMS"] == C
    assert "not locally measured light speeds" in scene["note"]
