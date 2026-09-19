"""Notation regressions found during the arts illustration review."""
import sys
from pathlib import Path


def test_generative_art_preserves_rule_and_seed_subset():
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
    try:
        from humanities_illustrations.arts import _generative_marks
    finally:
        sys.path.pop(0)
    a = _generative_marks(7,.35)
    b = _generative_marks(19,.35)
    dense = _generative_marks(7,.70)
    assert (len(a),len(b),len(dense)) == (12,13,21)
    assert a == _generative_marks(7,.35)
    assert a != b
    assert set(a) < set(dense)
    assert all(0 <= col < 5 and 0 <= row < 5 and 0 <= value < .35
               for col,row,value in a+b)


def test_design_gauge_and_slots_use_one_scale(monkeypatch):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
    try:
        from humanities_illustrations import arts
    finally:
        sys.path.pop(0)
    plate = arts.Plate('arts.3.design', 'Design', 3, 'arts')
    original_box, original_circle = plate.draw.rounded_rectangle, plate.draw.ellipse
    slots, gauges = [], []

    def box(bounds, *args, **kwargs):
        if bounds[2]-bounds[0] == 280:
            slots.append(bounds)
        return original_box(bounds, *args, **kwargs)

    def circle(bounds, *args, **kwargs):
        if kwargs.get('outline') == arts.BLUE and kwargs.get('width') == 6:
            gauges.append(bounds)
        return original_circle(bounds, *args, **kwargs)

    monkeypatch.setattr(plate.draw, 'rounded_rectangle', box)
    monkeypatch.setattr(plate.draw, 'ellipse', circle)
    arts._draw_design(plate)
    assert [b[3]-b[1] for b in slots] == [22*4,36*4]
    assert [b[3]-b[1] for b in gauges] == [30*4,30*4]


def test_eighth_beam_and_two_beat_half_note(monkeypatch):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
    try:
        from humanities_illustrations import arts
    finally:
        sys.path.pop(0)
    plate = arts.Plate('arts.1.beat', 'Beat and Melody', 1, 'arts')
    original = plate.draw.line
    lines = []

    def line(points, *args, **kwargs):
        lines.append((points, kwargs.get('fill')))
        return original(points, *args, **kwargs)

    monkeypatch.setattr(plate.draw, 'line', line)
    arts._draw_beat_melody(plate)
    assert ((584, 338, 719, 363), arts.TEAL) in lines
    assert ((840, 400, 1380, 400), arts.PLUM) in lines
    assert 1380 - 840 == 2 * (570 - 300)
