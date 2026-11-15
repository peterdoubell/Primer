"""Regressions found by inspecting the history teaching plates."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def history_module():
    sys.path.insert(0, str(ROOT / "tools"))
    try:
        from humanities_illustrations import history
        return history
    finally:
        sys.path.pop(0)


def test_geography_labels_river_not_basin(monkeypatch):
    history = history_module()
    plate = history.Plate("hist.2.geography", "World Geography", 2, "history")
    labels = []
    original = plate.text

    def capture(xy, value, **kwargs):
        labels.append((xy, value))
        return original(xy, value, **kwargs)

    monkeypatch.setattr(plate, "text", capture)
    history._draw_geography(plate)
    assert ((370, 490), "river") in labels
    assert not any("river basin" in value for _, value in labels)
    assert "invented" in history.SPECS["hist.2.geography"]["alt"]


def test_300_bce_comparison_marks_qin_unification_as_later(monkeypatch):
    history = history_module()
    captured = []
    monkeypatch.setattr(history, "draw_tracks", lambda plate, rows, *args, **kwargs: captured.extend(rows))
    history.SPECS["hist.2.civilizations"]["draw"](None)
    east_asia = dict(captured)["EAST ASIA"]
    assert east_asia[1] == ("Qin state", "one competing state; unification came later, in 221 BCE")


def test_ordinal_growth_timeline_does_not_claim_equal_duration():
    nodes = json.loads((ROOT / "data/curriculum/07-history.json").read_text())["nodes"]
    node = next(n for n in nodes if n["id"] == "hist.1.timelines")
    plate = next(m for m in node["lesson_media"] if m["kind"] == "illustration")
    assert "equal gaps do not mean equal numbers of years" in plate["caption"]
    assert "order, not elapsed time" in plate["caption"]


def test_market_marker_is_on_both_drawn_curves(monkeypatch):
    history = history_module()
    plate = history.Plate("hist.3.economics-intro", "How Economies Work", 3, "history")
    curves, markers = [], []
    line, dot = plate.draw.line, plate.dot

    def capture_line(coords, **kwargs):
        if kwargs.get("width") == 10:
            curves.append(coords)
        return line(coords, **kwargs)

    def capture_dot(point, radius, **kwargs):
        markers.append(point)
        return dot(point, radius, **kwargs)

    monkeypatch.setattr(plate.draw, "line", capture_line)
    monkeypatch.setattr(plate, "dot", capture_dot)
    history._draw_supply_demand(plate)
    assert len(curves) == 2
    assert markers == [(580, 480)]
    x, y = markers[0]
    for x0, y0, x1, y1 in curves:
        assert (x-x0)*(y1-y0) == (y-y0)*(x1-x0)


def test_drawn_prisoners_dilemma_has_stated_equilibrium(monkeypatch):
    history = history_module()
    plate = history.Plate("hist.5.economic-theory", "Advanced Economics", 5, "history")
    values = []
    original = history.box_text

    def capture(plate, bounds, value, **kwargs):
        if value in {"3, 3", "0, 5", "5, 0", "1, 1"}:
            values.append(tuple(map(int, value.split(","))))
        return original(plate, bounds, value, **kwargs)

    monkeypatch.setattr(history, "box_text", capture)
    history._draw_economic_theory(plate)
    assert values == [(3, 3), (0, 5), (5, 0), (1, 1)]
    # Given the other player's action, defection strictly improves own payoff.
    assert values[2][0] > values[0][0]
    assert values[3][0] > values[1][0]
    assert values[1][1] > values[0][1]
    assert values[3][1] > values[2][1]
