"""Concrete regressions from the physics illustration content review."""

import sys
import math
from pathlib import Path

import pytest


def modules():
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
    try:
        from physics_illustrations import early, core
    finally:
        sys.path.pop(0)
    return early, core


def test_magnetic_field_loops_close_and_reverse_inside():
    early, _ = modules()
    for y, control_y in ((470, 285), (530, 690)):
        points = early._closed_field_loop(y, control_y)
        assert points[0] == points[-1] == (1170, y)
        assert points[-2] == (1366, y)
        assert points[28][0] > points[22][0]  # External arrow N to S.
        assert points[-1][0] < points[-2][0]  # Internal return S to N.
        assert all(1050 < x < 1480 and 275 < py < 690 for x, py in points)


def test_ramp_load_rests_on_the_surface(monkeypatch):
    early, core = modules()
    plate = core.Plate('phys.1.machines', 'Simple Machines', 1)
    original = plate.draw.polygon
    loads = []

    def polygon(points, *args, **kwargs):
        if kwargs.get('fill') == core.GOLD_LIGHT and len(points) == 4:
            loads.append(points)
        return original(points, *args, **kwargs)

    monkeypatch.setattr(plate.draw, 'polygon', polygon)
    early.draw_machines(plate)
    assert len(loads) == 1
    for x, y in loads[0][:2]:
        assert y == pytest.approx(690 - (x - 164) * 330 / 336)
    for x, y in loads[0][2:]:
        assert y < 690 - (x - 164) * 330 / 336


def test_hollow_hull_excludes_water_and_ball_is_submerged(monkeypatch):
    early, core = modules()
    plate = core.Plate('phys.0.float-sink', 'Floating and Sinking', 0)
    polygon, ellipse = plate.draw.polygon, plate.draw.ellipse
    hulls, balls = [], []

    def capture_polygon(points, *args, **kwargs):
        if kwargs.get('outline') == core.PLUM:
            hulls.append(points)
        return polygon(points, *args, **kwargs)

    def capture_ellipse(box, *args, **kwargs):
        if kwargs.get('outline') == core.PLUM:
            balls.append(box)
        return ellipse(box, *args, **kwargs)

    monkeypatch.setattr(plate.draw, 'polygon', capture_polygon)
    monkeypatch.setattr(plate.draw, 'ellipse', capture_ellipse)
    early.draw_float_sink(plate)
    assert len(hulls) == 2 and len(balls) == 1
    assert balls[0][1] > 420
    for hull in hulls:
        assert min(y for _, y in hull) < 420 < max(y for _, y in hull)
    assert 'not a volume-scale drawing' in early.SPECS['phys.0.float-sink']['caption']


def test_parallel_circuit_has_no_wire_only_battery_short(monkeypatch):
    _, core = modules()
    from physics_illustrations import middle
    plate = core.Plate('phys.2.electricity', 'Electricity', 2)
    original = plate.draw.line
    wire = set()

    def line(points, *args, **kwargs):
        if kwargs.get('fill') == core.INK:
            pairs = list(zip(points[::2], points[1::2]))
            for (x0, y0), (x1, y1) in zip(pairs, pairs[1:]):
                if min(x0, x1) < 1050:
                    continue
                assert x0 == x1 or y0 == y1
                for x in range(int(min(x0, x1)), int(max(x0, x1)) + 1):
                    for y in range(int(min(y0, y1)), int(max(y0, y1)) + 1):
                        wire.add((x, y))
        return original(points, *args, **kwargs)

    monkeypatch.setattr(plate.draw, 'line', line)
    middle.draw_electricity(plate)
    assert {(1200, 410), (1332, 410), (1200, 660), (1332, 660)} <= wire
    seen, pending = set(), [(1100, 523)]
    while pending:
        x, y = pending.pop()
        if (x, y) in seen:
            continue
        seen.add((x, y))
        pending.extend(p for p in ((x-1,y), (x+1,y), (x,y-1), (x,y+1))
                       if p in wire and p not in seen)
    assert (1100, 547) not in seen
    assert (1200, 505) in seen and (1332, 505) in seen


def test_particle_identity_count_and_spacing_survive_phase_comparison(monkeypatch):
    _, core = modules()
    from physics_illustrations import middle
    plate = core.Plate('phys.2.matter', 'States of Matter', 2)
    original = middle.particle_box
    groups = []

    def box(plate, bounds, points, **kwargs):
        groups.append((points, kwargs))
        return original(plate, bounds, points, **kwargs)

    monkeypatch.setattr(middle, 'particle_box', box)
    middle.draw_matter(plate)
    assert [len(p) for p, _ in groups] == [20, 20, 20]
    assert len({(k['radius'], k['fill'], k['outline']) for _, k in groups}) == 1

    def nearest(points):
        return sum(min(math.dist(p, q) for q in points if p != q)
                   for p in points) / len(points)

    assert nearest(groups[2][0]) > 1.5 * nearest(groups[0][0])
    assert nearest(groups[2][0]) > 1.5 * nearest(groups[1][0])


def test_sticking_collision_ledger_and_velocity_scale(monkeypatch):
    _, core = modules()
    from physics_illustrations import middle
    plate = core.Plate('phys.3.energy-work', 'Work, Energy and Momentum', 3)
    original_text, original_arrow = plate.text, plate.arrow
    labels, arrows = [], []

    def text(point, value, **kwargs):
        labels.append(value)
        return original_text(point, value, **kwargs)

    def arrow(start, end, **kwargs):
        arrows.append((start, end, kwargs.get('fill')))
        return original_arrow(start, end, **kwargs)

    monkeypatch.setattr(plate, 'text', text)
    monkeypatch.setattr(plate, 'arrow', arrow)
    middle.draw_energy_work(plate)
    assert 'p = 2 × 4 + 1 × 0 = 8 kg m/s' in labels
    assert 'p = 3 × 8/3 = 8 kg m/s' in labels
    initial = next((a, b) for a, b, _ in arrows if a == (1055, 400))
    final = next((a, b) for a, b, _ in arrows if a == (1095, 610))
    assert math.dist(*final) / math.dist(*initial) == pytest.approx((8/3)/4)
    assert .5 * 2 * 4**2 - .5 * 3 * (8/3)**2 == pytest.approx(16/3)


def test_oscillator_flow_has_positive_qdot_and_negative_pdot_at_positive_q_p(monkeypatch):
    _, core = modules()
    from physics_illustrations import advanced
    plate = core.Plate('phys.4.classical', 'Classical Mechanics', 4)
    original = plate.arrow
    flow = []

    def arrow(start, end, **kwargs):
        if kwargs.get('fill') == core.CORAL:
            flow.append((start, end))
        return original(start, end, **kwargs)

    monkeypatch.setattr(plate, 'arrow', arrow)
    advanced.draw_classical(plate)
    assert len(flow) == 1
    (x0, y0), (x1, y1) = flow[0]
    assert 1145 < x0 < x1 and y0 < y1 < 535


def test_light_cone_vertex_lies_on_the_time_axis(monkeypatch):
    _, core = modules()
    from physics_illustrations import advanced
    plate = core.Plate('phys.4.relativity', 'Relativity', 4)
    arrow_original, line_original = plate.arrow, plate.polyline
    axes, cones = [], []

    def arrow(start, end, **kwargs):
        axes.append((start, end))
        return arrow_original(start, end, **kwargs)

    def polyline(points, **kwargs):
        if kwargs.get('fill') == core.GOLD:
            cones.append(points)
        return line_original(points, **kwargs)

    monkeypatch.setattr(plate, 'arrow', arrow)
    monkeypatch.setattr(plate, 'polyline', polyline)
    advanced.draw_relativity(plate)
    assert len(cones) == 1
    vertex = cones[0][1]
    assert any(start == vertex and end[0] == vertex[0] and end[1] < vertex[1]
               for start, end in axes)


def test_expansion_and_wavelength_have_same_end_to_end_ratio(monkeypatch):
    _, core = modules()
    from physics_illustrations import advanced
    plate = core.Plate('phys.5.gr-cosmo', 'Cosmology', 5)
    original_ellipse, original_wave = plate.draw.ellipse, advanced.wave
    radii, cycles = [], []

    def ellipse(box, *args, **kwargs):
        if kwargs.get('outline') == core.BLUE and kwargs.get('width') == 3:
            radii.append((box[2]-box[0])/2)
        return original_ellipse(box, *args, **kwargs)

    def wave(plate, box, **kwargs):
        cycles.append(kwargs['cycles'])
        return original_wave(plate, box, **kwargs)

    monkeypatch.setattr(plate.draw, 'ellipse', ellipse)
    monkeypatch.setattr(advanced, 'wave', wave)
    advanced.draw_gr_cosmo(plate)
    assert radii == [38, 57, 76]
    assert radii[-1]/radii[0] == cycles[0]/cycles[-1] == 2
