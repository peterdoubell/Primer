"""Regression checks for specific Earth illustration review findings."""

import math
import sys
from pathlib import Path

import pytest


def modules():
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
    try:
        from natural_science_illustrations import earth_space, earth_advanced_detail, core
    finally:
        sys.path.pop(0)
    return earth_space, earth_advanced_detail, core


def test_transfer_ellipse_has_earth_at_focus_and_burns_at_apsides(monkeypatch):
    earth, detail, core = modules()
    spec = earth.SPECS['earth.3.space-exploration']
    plate = core.SciencePlate('earth.3.space-exploration', spec['title'], 3, 'earth-space')
    original = plate.draw.ellipse
    ellipses = []

    def ellipse(box, *args, **kwargs):
        if kwargs.get('width') == 7 and kwargs.get('outline') == core.CORAL:
            ellipses.append(box)
        return original(box, *args, **kwargs)

    monkeypatch.setattr(plate.draw, 'ellipse', ellipse)
    detail.draw_space_exploration(plate, spec['content'])
    assert len(ellipses) == 1
    box, near, far = detail._transfer_geometry((420, 500), 165, 515)
    assert ellipses[0] == box
    x0, y0, x1, y1 = box
    a, b = (x1 - x0) / 2, (y1 - y0) / 2
    assert (x0 + x1) / 2 - math.sqrt(a*a - b*b) == pytest.approx(420)
    assert math.dist(near, (420, 500)) == pytest.approx(165)
    assert math.dist(far, (420, 500)) == pytest.approx(515)
    assert near == (255, 500)  # Same point and vertical tangent as inner circle.
    assert far == (935, 500)


def test_s_wave_rays_stop_at_liquid_boundary(monkeypatch):
    earth, detail, core = modules()
    spec = earth.SPECS['earth.4.geophysics']
    plate = core.SciencePlate('earth.4.geophysics', spec['title'], 4, 'earth-space')
    original = plate.draw.line
    endpoints = []

    def line(points, *args, **kwargs):
        if (kwargs.get('fill') == core.CORAL and kwargs.get('width') == 7
                and points[0] == (245, 355)):
            endpoints.append(points[-1])
        return original(points, *args, **kwargs)

    monkeypatch.setattr(plate.draw, 'line', line)
    detail.draw_geophysics(plate, spec['content'])
    assert len(endpoints) == 2
    assert all(math.dist(point, (465, 485)) == pytest.approx(138) for point in endpoints)


def test_planetary_radial_labels_follow_log_distance(monkeypatch):
    earth, detail, core = modules()
    spec = earth.SPECS['earth.4.planetary']
    plate = core.SciencePlate('earth.4.planetary', spec['title'], 4, 'earth-space')
    original = plate.text
    positions = {}

    def text(point, value, *args, **kwargs):
        if value.endswith(' AU'):
            positions[float(value[:-3])] = point[0]
        return original(point, value, *args, **kwargs)

    monkeypatch.setattr(plate, 'text', text)
    detail.draw_planetary(plate, spec['content'])
    assert set(positions) == {.1, 1, 3, 10, 30}
    assert positions[1] - positions[.1] == pytest.approx(positions[10] - positions[1])
    assert positions[3] - positions[1] == pytest.approx(positions[30] - positions[10])


def test_synthetic_data_and_absent_final_orbit_are_disclosed():
    earth, _detail, _core = modules()
    for lesson in ('earth.4.geophysics', 'earth.5.astrobiology', 'earth.5.frontier'):
        copy = earth.SPECS[lesson]['caption'].lower()
        assert any(word in copy for word in ('schematic', 'simulated', 'synthetic'))
    assert 'final circular orbit is not shown' in earth.SPECS['earth.3.space-exploration']['alt']
    assert "not today's remaining carbon budget" in earth.SPECS['earth.4.climatology']['caption']
