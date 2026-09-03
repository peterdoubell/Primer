"""Shared, deterministic drawing grammar for language and computer-science plates.

The diagrams in this package carry an argument: a trace, hierarchy, contrast,
causal sequence, state transition, or evidence relationship.  The reusable
layouts keep the visual language consistent without turning the plates into
generic decoration; lesson modules supply every label and relationship.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Sequence, Tuple

from PIL import Image

from math_illustrations.core import (
    BLUE,
    BLUE_LIGHT,
    CORAL,
    CORAL_LIGHT,
    GOLD,
    GOLD_LIGHT,
    GREEN,
    GREEN_LIGHT,
    GRID,
    HEIGHT,
    INK,
    INK_SOFT,
    PAPER_LIGHT,
    PLUM,
    PLUM_LIGHT,
    STAGE_DIRS,
    STAGE_NAMES,
    TEAL,
    TEAL_LIGHT,
    WIDTH,
    Plate,
    font,
    hex_rgba,
)


Spec = Dict[str, object]
Diagram = Dict[str, object]
Box = Tuple[float, float, float, float]
Point = Tuple[float, float]

COLORS = (BLUE, TEAL, GOLD, CORAL, PLUM, GREEN)
LIGHTS = (BLUE_LIGHT, TEAL_LIGHT, GOLD_LIGHT, CORAL_LIGHT, PLUM_LIGHT, GREEN_LIGHT)


def panel(plate: Plate, box: Box, heading: str, *, index: int = 0) -> Box:
    """Draw a labelled content panel and return its usable inner bounds."""

    color = COLORS[index % len(COLORS)]
    light = LIGHTS[index % len(LIGHTS)]
    plate.card(box, fill=hex_rgba(light, 84), outline=color, width=3, radius=22)
    x0, y0, x1, y1 = box
    plate.label(((x0 + x1) / 2, y0 + 42), heading, size=20, fill=color)
    return (x0 + 25, y0 + 87, x1 - 25, y1 - 24)


def fit_text(plate: Plate, box: Box, value: str, *, size: int = 28,
             bold: bool = False, fill: str = INK) -> None:
    plate.wrapped_text(tuple(int(v) for v in box), value, size=size,
                       bold=bold, fill=fill, line_gap=7)


def footer(plate: Plate, value: str, *, size: int = 28) -> None:
    """State the inference the learner should take from the diagram."""

    plate.draw.rounded_rectangle((180, 816, 1420, 880), radius=24,
                                 fill=hex_rgba(plate.accent, 30),
                                 outline=hex_rgba(plate.accent, 120), width=2)
    plate.text((800, 848), value, size=size, bold=True, fill=plate.accent,
               anchor="mm")


def arrow_between(plate: Plate, start: Point, end: Point, label: str = "",
                  *, color: str = INK_SOFT) -> None:
    plate.arrow(start, end, fill=color, width=7, head=20)
    if label:
        plate.text(((start[0] + end[0]) / 2, (start[1] + end[1]) / 2 - 18),
                   label, size=20, bold=True, fill=color, anchor="mm")


def _draw_flow(plate: Plate, diagram: Diagram) -> None:
    steps = list(diagram["steps"])
    count = len(steps)
    gap = 38
    left, right = 125, 1475
    width = (right - left - gap * (count - 1)) / count
    top, bottom = 270, 728
    for index, step in enumerate(steps):
        x0 = left + index * (width + gap)
        x1 = x0 + width
        inner = panel(plate, (x0, top, x1, bottom), str(step[0]), index=index)
        plate.text(((x0 + x1) / 2, top + 112), str(index + 1), size=25,
                   bold=True, fill=COLORS[index % len(COLORS)], anchor="mm")
        fit_text(plate, (inner[0] + 5, inner[1] + 52, inner[2] - 5, inner[3]),
                 str(step[1]), size=25, bold=index == count - 1)
        if index < count - 1:
            arrow_between(plate, (x1 + 7, (top + bottom) / 2),
                          (x1 + gap - 7, (top + bottom) / 2))
    footer(plate, str(diagram["footer"]), size=int(diagram.get("footer_size", 28)))


def _draw_compare(plate: Plate, diagram: Diagram) -> None:
    columns = list(diagram["columns"])
    count = len(columns)
    gap = 34
    left, right = 120, 1480
    width = (right - left - gap * (count - 1)) / count
    for index, column in enumerate(columns):
        x0 = left + index * (width + gap)
        x1 = x0 + width
        inner = panel(plate, (x0, 228, x1, 780), str(column[0]), index=index)
        lines = list(column[1]) if not isinstance(column[1], str) else [column[1]]
        line_h = min(120, 440 / max(1, len(lines)))
        for row, line in enumerate(lines):
            y0 = inner[1] + row * line_h
            if row:
                plate.draw.line((inner[0] + 20, y0, inner[2] - 20, y0),
                                fill=hex_rgba(GRID, 170), width=2)
            fit_text(plate, (inner[0] + 12, y0 + 8, inner[2] - 12,
                             min(inner[3], y0 + line_h - 4)), str(line),
                     size=24, bold=row == 0)
    footer(plate, str(diagram["footer"]), size=int(diagram.get("footer_size", 28)))


def _draw_layers(plate: Plate, diagram: Diagram) -> None:
    layers = list(diagram["layers"])
    count = len(layers)
    x0, x1 = 180, 1420
    top, bottom = 230, 775
    gap = 18
    height = (bottom - top - gap * (count - 1)) / count
    for index, layer in enumerate(layers):
        y0 = top + index * (height + gap)
        y1 = y0 + height
        color = COLORS[index % len(COLORS)]
        light = LIGHTS[index % len(LIGHTS)]
        plate.draw.rounded_rectangle((x0, y0, x1, y1), radius=20,
                                     fill=hex_rgba(light, 94), outline=color, width=3)
        plate.text((x0 + 28, (y0 + y1) / 2), str(layer[0]), size=25,
                   bold=True, fill=color, anchor="lm")
        fit_text(plate, (x0 + 335, y0 + 7, x1 - 25, y1 - 7), str(layer[1]),
                 size=23, bold=index == count - 1)
        if index < count - 1:
            plate.arrow((800, y1 + 3), (800, y1 + gap - 3), fill=INK_SOFT,
                        width=5, head=14)
    footer(plate, str(diagram["footer"]), size=int(diagram.get("footer_size", 28)))


def _draw_tree(plate: Plate, diagram: Diagram) -> None:
    root = tuple(diagram["root"])
    leaves = list(diagram["leaves"])
    root_box = (510, 220, 1090, 390)
    inner = panel(plate, root_box, str(root[0]), index=0)
    fit_text(plate, inner, str(root[1]), size=25, bold=True)
    count = len(leaves)
    gap = 28
    left, right = 120, 1480
    width = (right - left - gap * (count - 1)) / count
    for index, leaf in enumerate(leaves):
        x0 = left + index * (width + gap)
        x1 = x0 + width
        center = (x0 + x1) / 2
        plate.draw.line((800, 390, center, 480), fill=INK_SOFT, width=5)
        inner = panel(plate, (x0, 480, x1, 776), str(leaf[0]), index=index + 1)
        fit_text(plate, inner, str(leaf[1]), size=23, bold=False)
    footer(plate, str(diagram["footer"]), size=int(diagram.get("footer_size", 28)))


def _draw_timeline(plate: Plate, diagram: Diagram) -> None:
    events = list(diagram["events"])
    count = len(events)
    xs = [180 + index * 1240 / max(1, count - 1) for index in range(count)]
    y = 505
    plate.arrow((145, y), (1455, y), fill=INK_SOFT, width=6, head=22)
    for index, (heading, detail) in enumerate(events):
        x = xs[index]
        color = COLORS[index % len(COLORS)]
        plate.dot((x, y), 17, fill=color, outline=INK, width=3)
        above = index % 2 == 0
        box = (x - 150, 235 if above else 555, x + 150, 455 if above else 775)
        # Keep end cards inside the content frame.
        dx = max(120 - box[0], 0) + min(1480 - box[2], 0)
        box = tuple(value + dx if i % 2 == 0 else value for i, value in enumerate(box))
        inner = panel(plate, box, str(heading), index=index)
        fit_text(plate, inner, str(detail), size=22)
        plate.draw.line((x, y - 18 if above else y + 18,
                         x, box[3] if above else box[1]), fill=color, width=4)
    footer(plate, str(diagram["footer"]), size=int(diagram.get("footer_size", 28)))


def _draw_network(plate: Plate, diagram: Diagram) -> None:
    columns = list(diagram["columns"])
    edges = list(diagram.get("edges", []))
    positions: Dict[str, Point] = {}
    col_count = len(columns)
    for column_index, column in enumerate(columns):
        heading, nodes = column
        x = 220 + column_index * 1160 / max(1, col_count - 1)
        plate.label((x, 242), str(heading), size=19,
                    fill=COLORS[column_index % len(COLORS)])
        node_count = len(nodes)
        ys = [390 + row * 300 / max(1, node_count - 1) for row in range(node_count)]
        if node_count == 1:
            ys = [540]
        for row, node in enumerate(nodes):
            node_id, label = node
            positions[str(node_id)] = (x, ys[row])
            color = COLORS[(column_index + row) % len(COLORS)]
            light = LIGHTS[(column_index + row) % len(LIGHTS)]
            plate.draw.rounded_rectangle((x - 145, ys[row] - 55, x + 145, ys[row] + 55),
                                         radius=22, fill=hex_rgba(light, 120),
                                         outline=color, width=4)
            fit_text(plate, (x - 125, ys[row] - 44, x + 125, ys[row] + 44),
                     str(label), size=22, bold=True, fill=INK)
    for source, target, label in edges:
        sx, sy = positions[str(source)]
        tx, ty = positions[str(target)]
        direction = 1 if tx >= sx else -1
        arrow_between(plate, (sx + direction * 150, sy),
                      (tx - direction * 150, ty), str(label), color=INK_SOFT)
    footer(plate, str(diagram["footer"]), size=int(diagram.get("footer_size", 28)))


def _draw_trace(plate: Plate, diagram: Diagram) -> None:
    code = list(diagram["code"])
    states = list(diagram["states"])
    left = panel(plate, (120, 228, 755, 780), str(diagram.get("code_heading", "INPUT")), index=0)
    right = panel(plate, (845, 228, 1480, 780), str(diagram.get("state_heading", "TRACE")), index=1)
    line_face = font(24, math_face=True)
    line_height = min(68, 440 / max(1, len(code)))
    for index, line in enumerate(code, start=1):
        y = left[1] + 14 + (index - 1) * line_height
        plate.text((left[0] + 8, y), str(index), size=19, fill=INK_SOFT, anchor="la")
        plate.draw.text((left[0] + 52, y), str(line), font=line_face, fill=INK)
    state_height = min(92, 430 / max(1, len(states)))
    for index, state in enumerate(states):
        y0 = right[1] + 8 + index * state_height
        color = COLORS[index % len(COLORS)]
        plate.draw.rounded_rectangle((right[0] + 8, y0, right[2] - 8,
                                     y0 + state_height - 12), radius=14,
                                     fill=hex_rgba(LIGHTS[index % len(LIGHTS)], 90),
                                     outline=color, width=2)
        fit_text(plate, (right[0] + 25, y0 + 4, right[2] - 25,
                         y0 + state_height - 16), str(state), size=22,
                 bold=index == len(states) - 1)
    arrow_between(plate, (770, 510), (830, 510), "run", color=plate.accent)
    footer(plate, str(diagram["footer"]), size=int(diagram.get("footer_size", 28)))


def _draw_cycle(plate: Plate, diagram: Diagram) -> None:
    steps = list(diagram["steps"])
    count = len(steps)
    center = (800, 505)
    radius_x, radius_y = 475, 245
    positions = []
    for index in range(count):
        angle = -math.pi / 2 + index * 2 * math.pi / count
        positions.append((center[0] + radius_x * math.cos(angle),
                          center[1] + radius_y * math.sin(angle)))
    for index, (heading, detail) in enumerate(steps):
        x, y = positions[index]
        color = COLORS[index % len(COLORS)]
        light = LIGHTS[index % len(LIGHTS)]
        plate.draw.rounded_rectangle((x - 165, y - 72, x + 165, y + 72), radius=23,
                                     fill=hex_rgba(light, 112), outline=color, width=4)
        plate.text((x, y - 27), str(heading), size=23, bold=True,
                   fill=color, anchor="mm")
        fit_text(plate, (x - 145, y - 5, x + 145, y + 59), str(detail), size=19)
    for index in range(count):
        start = positions[index]
        end = positions[(index + 1) % count]
        dx, dy = end[0] - start[0], end[1] - start[1]
        distance = math.hypot(dx, dy)
        unit = (dx / distance, dy / distance)
        arrow_between(plate, (start[0] + unit[0] * 175, start[1] + unit[1] * 82),
                      (end[0] - unit[0] * 175, end[1] - unit[1] * 82), color=INK_SOFT)
    footer(plate, str(diagram["footer"]), size=int(diagram.get("footer_size", 28)))


def _draw_state(plate: Plate, diagram: Diagram) -> None:
    states = list(diagram["states"])
    transitions = list(diagram["transitions"])
    positions: Dict[str, Point] = {}
    count = len(states)
    for index, state in enumerate(states):
        node_id, label, accepting = state
        x = 230 + index * 1140 / max(1, count - 1)
        y = 500 + (95 if index % 2 else -95)
        positions[str(node_id)] = (x, y)
        color = COLORS[index % len(COLORS)]
        plate.draw.ellipse((x - 86, y - 86, x + 86, y + 86),
                           fill=hex_rgba(LIGHTS[index % len(LIGHTS)], 110),
                           outline=color, width=5)
        if accepting:
            plate.draw.ellipse((x - 72, y - 72, x + 72, y + 72),
                               outline=color, width=3)
        fit_text(plate, (x - 64, y - 52, x + 64, y + 52),
                 "{}\n{}".format(node_id, label),
                 size=21, bold=True)
    plate.arrow((105, 405), (positions[str(states[0][0])][0] - 92,
                             positions[str(states[0][0])][1]), fill=INK, width=5, head=18)
    directed_pairs = {(str(source), str(target)) for source, target, _ in transitions}
    for source, target, label in transitions:
        source = str(source)
        target = str(target)
        sx, sy = positions[str(source)]
        tx, ty = positions[str(target)]
        if source == target:
            plate.draw.arc((sx - 65, sy - 155, sx + 65, sy - 25), 185, 355,
                           fill=INK_SOFT, width=5)
            plate.text((sx, sy - 157), str(label), size=20, bold=True,
                       fill=INK_SOFT, anchor="mm")
        else:
            dx, dy = tx - sx, ty - sy
            distance = math.hypot(dx, dy)
            unit = (dx / distance, dy / distance)
            # Reciprocal transitions get parallel tracks.  Using the local
            # left-hand normal for both directions places them on opposite
            # physical sides because the reverse edge flips its unit vector.
            reciprocal = (target, source) in directed_pairs
            offset = 22 if reciprocal else 0
            normal = (-unit[1], unit[0])
            start = (sx + unit[0] * 92 + normal[0] * offset,
                     sy + unit[1] * 92 + normal[1] * offset)
            end = (tx - unit[0] * 92 + normal[0] * offset,
                   ty - unit[1] * 92 + normal[1] * offset)
            arrow_between(plate, start, end, str(label))
    footer(plate, str(diagram["footer"]), size=int(diagram.get("footer_size", 28)))


DRAWERS: Dict[str, Callable[[Plate, Diagram], None]] = {
    "flow": _draw_flow,
    "compare": _draw_compare,
    "layers": _draw_layers,
    "tree": _draw_tree,
    "timeline": _draw_timeline,
    "network": _draw_network,
    "trace": _draw_trace,
    "cycle": _draw_cycle,
    "state": _draw_state,
}


def draw_diagram(plate: Plate, diagram: Diagram) -> None:
    kind = str(diagram["kind"])
    if kind not in DRAWERS:
        raise ValueError("Unknown language/CS diagram kind {}".format(kind))
    DRAWERS[kind](plate, diagram)


def spec(node_id: str, title: str, stage: int, plate_id: str,
         alt: str, caption: str, diagram: Diagram) -> Spec:
    """Build the strict public spec while keeping layout data in its closure."""

    def draw(plate: Plate, payload: Diagram = diagram) -> None:
        draw_diagram(plate, payload)

    return {
        "id": node_id,
        "title": title,
        "stage": stage,
        "plate_id": plate_id,
        "alt": alt,
        "caption": caption,
        "draw": draw,
    }


def validate_specs(specs: Dict[str, Spec], expected_ids: Iterable[str]) -> None:
    expected = set(expected_ids)
    actual = set(specs)
    if actual != expected:
        raise ValueError("Language/CS spec mismatch; missing={}, extra={}".format(
            sorted(expected - actual), sorted(actual - expected)))
    required = {"id", "title", "stage", "plate_id", "alt", "caption", "draw"}
    plate_ids = set()
    alts = set()
    captions = set()
    for node_id, item in specs.items():
        if set(item) != required or item["id"] != node_id:
            raise ValueError("Malformed illustration spec for {}".format(node_id))
        if type(item["stage"]) is not int or item["stage"] not in STAGE_NAMES:
            raise ValueError("{} has an invalid stage".format(node_id))
        if not callable(item["draw"]):
            raise ValueError("{} needs a drawing function".format(node_id))
        for key in ("title", "plate_id", "alt", "caption"):
            if not isinstance(item[key], str) or not item[key].strip():
                raise ValueError("{} needs {}".format(node_id, key))
        if len(str(item["alt"])) < 45 or len(str(item["caption"])) < 55:
            raise ValueError("{} needs explanatory alt and caption text".format(node_id))
        for key, seen in (("plate_id", plate_ids), ("alt", alts), ("caption", captions)):
            if item[key] in seen:
                raise ValueError("Duplicate {} for {}".format(key, node_id))
            seen.add(item[key])


def subject_for(node_id: str) -> str:
    if node_id.startswith("lang."):
        return "language"
    if node_id.startswith("cs."):
        return "computer-science"
    raise ValueError("Unknown curriculum subject for {}".format(node_id))


def asset_paths(output_root: Path, item: Spec) -> Tuple[Path, Path]:
    subject = subject_for(str(item["id"]))
    directory = output_root / STAGE_DIRS[int(item["stage"])] / subject
    stem = str(item["id"]).replace(".", "-")
    return directory / (stem + "-1600.webp"), directory / (stem + "-800.webp")


def render_image(item: Spec) -> Image.Image:
    plate = Plate(str(item["id"]), str(item["title"]), int(item["stage"]))
    item["draw"](plate)
    return plate.image


def render_spec(output_root: Path, item: Spec, *, overwrite: bool = False) -> List[Path]:
    paths = asset_paths(output_root, item)
    existing = [path for path in paths if path.exists()]
    if existing and not overwrite:
        raise FileExistsError("Refusing to overwrite: {}".format(", ".join(map(str, existing))))
    image = render_image(item)
    paths[0].parent.mkdir(parents=True, exist_ok=True)
    image.save(paths[0], "WEBP", quality=86, method=6)
    image.resize((800, 500), Image.Resampling.LANCZOS).save(
        paths[1], "WEBP", quality=84, method=6)
    return list(paths)


def illustration_entry(item: Spec) -> Dict[str, object]:
    node_id = str(item["id"])
    subject = subject_for(node_id)
    stem = node_id.replace(".", "-")
    prefix = "/app/illustrations/{}/{}/{}".format(
        STAGE_DIRS[int(item["stage"])], subject, stem)
    return {
        "id": item["plate_id"],
        "kind": "illustration",
        "src": prefix + "-800.webp",
        "srcset": "{}-800.webp 800w, {}-1600.webp 1600w".format(prefix, prefix),
        "alt": item["alt"],
        "caption": item["caption"],
        "width": WIDTH,
        "height": HEIGHT,
    }


__all__ = [
    "Diagram", "HEIGHT", "Spec", "STAGE_DIRS", "WIDTH", "asset_paths",
    "illustration_entry", "render_image", "render_spec", "spec", "validate_specs",
]
