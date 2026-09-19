"""Guard the bespoke visual cohorts that already meet the shared quality bar."""

from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"


def _import_generators():
    sys.path.insert(0, str(TOOLS))
    try:
        import generate_humanities_illustrations as humanities
        import generate_math_illustrations as mathematics
        import generate_physics_media as physics
    finally:
        sys.path.pop(0)
    return mathematics, physics, humanities


def test_existing_high_quality_cohorts_stay_lesson_specific_and_complete():
    """Preserved cohorts must not regress to shared generic compositions."""
    mathematics, physics, humanities = _import_generators()

    math_specs = mathematics.all_specs()
    physics_specs = physics.all_specs()
    humanities_specs = humanities.all_specs()

    mathematics.validate_inventory(mathematics.load_curriculum(), math_specs)
    physics.validate_inventory(physics.load_curriculum(), physics_specs)
    humanities.validate_inventory(humanities.load_curricula(), humanities_specs)

    for specs, expected_count in (
        (math_specs, 54),
        (physics_specs, 36),
        (humanities_specs, 77),
    ):
        assert len(specs) == expected_count
        assert len({id(item["draw"]) for item in specs.values()}) == expected_count


def test_introductory_arts_worked_examples_render_deterministically(tmp_path):
    """Keep these concrete examples from reverting to generic text-card helpers."""
    _, _, humanities = _import_generators()
    from humanities_illustrations.core import render_spec
    from PIL import Image

    specs = humanities.all_specs()
    examples = {
        "arts.0.drawing": ("_draw_observation", "same height"),
        "arts.1.crafts": ("_draw_craft_processes", "before gluing"),
        "arts.4.composition": ("_draw_counterpoint", "Four one-beat"),
        "mind.0.feelings": ("_draw_feelings", "same new school"),
        "mind.0.fair": ("_draw_fairness", "equitable support"),
        "hist.0.community": ("_draw_community_tools", "protective helmet"),
        "hist.0.longago": ("_draw_message_history", "1840"),
        "hist.1.maps": ("_draw_worked_map", "two-kilometre scale bar"),
    }
    for node_id, (renderer, description) in examples.items():
        item = specs[node_id]
        assert item["draw"].__name__ == renderer
        assert description in item["alt"]
        paths = render_spec(tmp_path, item)
        original = [path.read_bytes() for path in paths]
        for path, size in zip(paths, ((1600, 1000), (800, 500))):
            with Image.open(path) as image:
                assert image.size == size
                assert image.format == "WEBP"
        render_spec(tmp_path, item, overwrite=True)
        assert original == [path.read_bytes() for path in paths]


def test_composition_example_encodes_named_intervals():
    _import_generators()
    from humanities_illustrations.arts import COMPOSITION_VOICES

    upper, lower = COMPOSITION_VOICES
    assert upper == (60, 62, 64, 62)  # C4 D4 E4 D4
    assert lower == (57, 59, 60, 59)  # A3 B3 C4 B3
    assert [a - b for a, b in zip(upper, lower)] == [3, 3, 4, 3]


def test_map_route_and_scale_remain_proportional_when_resized():
    _import_generators()
    from humanities_illustrations.history import MAP_ROUTE, MAP_SCALE_PIXELS, MAP_SCALE_KM
    import math

    assert MAP_ROUTE[0][0] == MAP_ROUTE[1][0]
    assert MAP_ROUTE[1][1] < MAP_ROUTE[0][1]  # north is up here
    for factor in (.25, .5, 1, 2):
        length = math.dist(*MAP_ROUTE) * factor
        assert length / (MAP_SCALE_PIXELS * factor) * MAP_SCALE_KM == 6


def test_statistics_plate_labels_population_not_sample_spread(monkeypatch):
    _import_generators()
    from math_illustrations import middle
    from statistics import mean, pstdev
    from types import SimpleNamespace

    examples = []
    monkeypatch.setattr(middle, "_dot_plot", lambda plate, box, values, **labels:
                        examples.append((values, labels)))
    middle.draw_statistics(SimpleNamespace(label=lambda *args, **kwargs: None))
    assert len(examples) == 2
    for values, labels in examples:
        assert mean(values) == 10
        assert labels["sd"] == "population SD ≈ {:.1f}".format(pstdev(values))
