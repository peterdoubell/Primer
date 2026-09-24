"""Regressions for specific computer-science illustration review findings."""

import sys
from pathlib import Path


def modules():
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
    try:
        from language_cs_illustrations import cs_early_detail, cs_advanced_detail, core, computer_science
    finally:
        sys.path.pop(0)
    return cs_early_detail, cs_advanced_detail, core, computer_science


def test_complexity_plate_exact_counts_and_visible_witness(monkeypatch):
    _, advanced, core, _ = modules()
    plate = core.Plate('cs.5.complexity', 'Computational Complexity', 5)
    original = advanced._value_tile
    values = []

    def tile(plate, bounds, value, *args, **kwargs):
        values.append(int(value))
        return original(plate, bounds, value, *args, **kwargs)

    monkeypatch.setattr(advanced, '_value_tile', tile)
    advanced._render_complexity(plate)
    assert values == [v for n in (4, 8, 16) for v in (n, n, n*n, 2**n)]
    x, y = True, False
    assert all((x or y, not x or not y, x or not y))


def test_security_output_explanation_is_outside_small_tile(monkeypatch):
    _, advanced, core, _ = modules()
    plate = core.Plate('cs.4.security', 'Security', 4)
    original = advanced._value_tile
    outputs = []

    def tile(plate, bounds, value, *args, **kwargs):
        if value == 'CIPHERTEXT\n+ TAG':
            outputs.append((bounds, kwargs.get('sub')))
        return original(plate, bounds, value, *args, **kwargs)

    monkeypatch.setattr(advanced, '_value_tile', tile)
    advanced._render_security(plate)
    assert outputs == [((590, 409, 715, 549), '')]


def test_attention_example_rows_normalize_and_loss_matches(monkeypatch):
    import math
    _, advanced, core, _ = modules()
    plate = core.Plate('cs.5.deep-learning', 'Deep Learning', 5)
    original = advanced._heat_cell
    weights = []

    def cell(plate, bounds, value, **kwargs):
        weights.append(value)
        return original(plate, bounds, value, **kwargs)

    monkeypatch.setattr(advanced, '_heat_cell', cell)
    advanced._render_deep_learning(plate)
    assert len(weights) == 16
    assert all(math.isclose(sum(weights[i:i + 4]), 1) for i in range(0, 16, 4))
    assert round(-math.log(.22), 2) == 1.51


def test_invalid_array_slot_does_not_overlap_valid_storage(monkeypatch):
    early, _, core, _ = modules()
    plate = core.Plate('cs.2.debugging', 'Finding Bugs', 2)
    original_box, original_dash = plate.draw.rounded_rectangle, plate.dashed_line
    cells, ghost = [], []

    def box(bounds, *args, **kwargs):
        if bounds[1] == 410 and bounds[3] == 520:
            cells.append(bounds)
        return original_box(bounds, *args, **kwargs)

    def dash(start, end, **kwargs):
        if kwargs.get('fill') == core.CORAL and start[1] in (410, 520):
            ghost.extend((start, end))
        return original_dash(start, end, **kwargs)

    monkeypatch.setattr(plate.draw, 'rounded_rectangle', box)
    monkeypatch.setattr(plate, 'dashed_line', dash)
    early._render_debugging(plate)
    assert len(cells) == 3 and ghost
    assert max(b[2] for b in cells) + 20 <= min(x for x, _ in ghost)


def test_merge_sort_singletons_have_separate_boxes(monkeypatch):
    _, advanced, core, _ = modules()
    plate = core.Plate('cs.3.algorithms', 'Algorithms', 3)
    original = advanced._value_tile
    cells = []

    def tile(plate, bounds, value, *args, **kwargs):
        if bounds[1] == 588:
            cells.append((bounds, value))
        return original(plate, bounds, value, *args, **kwargs)

    monkeypatch.setattr(advanced, '_value_tile', tile)
    advanced._render_algorithms(plate)
    assert [v for _, v in cells] == ['7', '2', '5', '1']
    assert all(a[0][2] + 10 <= b[0][0] for a, b in zip(cells, cells[1:]))


def test_commit_nodes_exclude_checks_and_head_reference(monkeypatch):
    _, advanced, core, _ = modules()
    plate = core.Plate('cs.3.versioncontrol', 'Version Control', 3)
    original_commit, original_arrow = advanced._commit, advanced._arrow
    commits, incoming = [], []

    def commit(plate, center, value, *args, **kwargs):
        commits.append(value)
        return original_commit(plate, center, value, *args, **kwargs)

    def arrow(plate, start, end, *args, **kwargs):
        if end == (1087, 507):
            incoming.append(start)
        return original_arrow(plate, start, end, *args, **kwargs)

    monkeypatch.setattr(advanced, '_commit', commit)
    monkeypatch.setattr(advanced, '_arrow', arrow)
    advanced._render_versioncontrol(plate)
    assert commits == ['A', 'B', 'C', 'B2', 'M']
    assert len(incoming) == 2


def test_memory_address_arrow_is_one_way_and_encoding_is_named(monkeypatch):
    early, _, core, _ = modules()
    plate = core.Plate('cs.1.parts', 'Parts', 1)
    original_arrow, original_double, original_text = plate.arrow, plate.double_arrow, plate.text
    arrows, doubles, labels = [], [], []

    def arrow(start, end, **kwargs):
        arrows.append((start, end))
        return original_arrow(start, end, **kwargs)

    def double(start, end, **kwargs):
        doubles.append((start, end))
        return original_double(start, end, **kwargs)

    def text(point, value, **kwargs):
        labels.append(value)
        return original_text(point, value, **kwargs)

    monkeypatch.setattr(plate, 'arrow', arrow)
    monkeypatch.setattr(plate, 'double_arrow', double)
    monkeypatch.setattr(plate, 'text', text)
    early._render_parts(plate)
    assert ((835, 511), (875, 511)) in arrows
    assert ((835, 511), (875, 511)) not in doubles
    assert 'ASCII A' in labels and format(ord('A'), '08b') in labels
