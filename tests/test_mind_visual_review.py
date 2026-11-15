"""Geometry regressions discovered during mind-and-society visual review."""
import sys
from pathlib import Path


def module():
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
    try:
        from humanities_illustrations import mind_society
        return mind_society
    finally:
        sys.path.pop(0)


def test_growth_bars_share_zero_and_centimetre_scale(monkeypatch):
    m = module()
    plate = m.Plate("mind.1.thinking", "Good Thinking", 1, m.DOMAIN)
    rectangles = []
    original = plate.draw.rectangle

    def capture(bounds, **kwargs):
        rectangles.append(bounds)
        return original(bounds, **kwargs)

    monkeypatch.setattr(plate.draw, "rectangle", capture)
    m._draw_growth_evidence(plate)
    bars = [b for b in rectangles if b[2]-b[0] == 100]
    assert len(bars) == 2
    assert [b[3] for b in bars] == [670, 670]
    assert [b[3]-b[1] for b in bars] == [8*20, 14*20]


def test_epistemology_circles_fit_panel_and_clock_shows_three(monkeypatch):
    m = module()
    plate = m.Plate("mind.4.epistemology", "Epistemology", 4, m.DOMAIN)
    ellipses, lines = [], []
    ellipse, line = plate.draw.ellipse, plate.draw.line

    def capture_ellipse(bounds, **kwargs):
        ellipses.append(bounds)
        return ellipse(bounds, **kwargs)

    def capture_line(coords, **kwargs):
        lines.append(coords)
        return line(coords, **kwargs)

    monkeypatch.setattr(plate.draw, "ellipse", capture_ellipse)
    monkeypatch.setattr(plate.draw, "line", capture_line)
    m._draw_epistemology(plate)
    circles = [b for b in ellipses if b[0] < 900]
    assert len(circles) == 3
    assert all(120 < b[0] < b[2] < 900 and 235 < b[1] < b[3] < 780 for b in circles)
    assert (1215, 457, 1215, 505, 1248, 505) in lines
