"""Specific regressions found during direct language-plate inspection."""
import sys
from pathlib import Path


def modules():
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
    try:
        from language_cs_illustrations import language_advanced_detail, core
    finally:
        sys.path.pop(0)
    return language_advanced_detail, core


def test_revision_underlines_point_to_verb_and_roof(monkeypatch):
    advanced, core = modules()
    plate = core.Plate('lang.4.creative', 'Creative Writing', 4)
    original = plate.draw.line
    lines = []

    def line(points, *args, **kwargs):
        lines.append((points, kwargs.get('fill')))
        return original(points, *args, **kwargs)

    monkeypatch.setattr(plate.draw, 'line', line)
    advanced._render_creative(plate)
    assert ((1135, 423, 1335, 423), core.CORAL) in lines
    assert ((1094, 475, 1331, 475), core.BLUE) in lines
    assert ((1016, 475, 1165, 475), core.CORAL) not in lines


def test_lens_question_bounds_fit_inside_circle(monkeypatch):
    advanced, core = modules()
    plate = core.Plate('lang.4.lit-theory', 'Literary Theory', 4)
    bounds = []
    original = advanced._wrapped

    def wrapped(plate, box, value, **kwargs):
        bounds.append(box)
        return original(plate, box, value, **kwargs)

    monkeypatch.setattr(advanced, '_wrapped', wrapped)
    advanced._lens(plate, (280, 325), core.BLUE, 'FORMAL', 'How do gate and crossing relate?')
    assert len(bounds) == 1
    x0, y0, x1, y1 = bounds[0]
    assert all((x-280)**2 + (y-325)**2 < 110**2
               for x in (x0, x1) for y in (y0, y1))
