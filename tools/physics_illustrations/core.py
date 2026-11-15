"""Shared drawing grammar for auditable Primer physics plates.

Physics diagrams are evidence, not decoration.  This module keeps arrows,
scales, plots, conserved totals and comparison panels reproducible so the
relationships can be inspected in source and regenerated without a model.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Sequence, Tuple

from PIL import Image

from math_illustrations.core import (
    BLUE,
    BLUE_LIGHT,
    CONTENT,
    CORAL,
    CORAL_LIGHT,
    EDGE,
    GOLD,
    GOLD_LIGHT,
    GREEN,
    GREEN_LIGHT,
    GRID,
    HEIGHT,
    INK,
    INK_SOFT,
    PAPER,
    PAPER_LIGHT,
    PLUM,
    PLUM_LIGHT,
    STAGE_DIRS,
    STAGE_NAMES,
    TEAL,
    TEAL_LIGHT,
    WIDTH,
    Plate as _MathPlate,
    font,
    hex_rgba,
    mix,
)


Spec = Dict[str, object]
Box = Tuple[float, float, float, float]
Point = Tuple[float, float]


def _needs_symbol_font(value: str) -> bool:
    return any(ord(character) > 127 for character in value)


class Plate(_MathPlate):
    """Math plate with an automatic STIX fallback for scientific symbols."""

    def text(
        self,
        xy: Tuple[float, float],
        value: str,
        *,
        size: int = 36,
        bold: bool = False,
        math_face: bool = False,
        fill: str = INK,
        anchor: str = "la",
        stroke_width: int = 0,
    ) -> None:
        super().text(xy, value, size=size, bold=bold,
                     math_face=math_face or _needs_symbol_font(value), fill=fill,
                     anchor=anchor, stroke_width=stroke_width)

    def label(
        self,
        xy: Tuple[float, float],
        value: str,
        *,
        size: int = 28,
        fill: str | None = None,
        text_fill: str = PAPER_LIGHT,
    ) -> None:
        face = font(size, bold=True, math_face=_needs_symbol_font(value))
        left, top, right, bottom = self.draw.textbbox(xy, value, font=face, anchor="mm")
        self.draw.rounded_rectangle(
            (left - 18, top - 10, right + 18, bottom + 10),
            radius=16, fill=fill or self.accent,
        )
        self.draw.text(xy, value, font=face, fill=text_fill, anchor="mm")


def spec(
    node_id: str,
    title: str,
    stage: int,
    plate_id: str,
    alt: str,
    caption: str,
    draw: Callable[[Plate], None],
) -> Spec:
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
        raise ValueError("Physics spec mismatch; missing={}, extra={}".format(
            sorted(expected - actual), sorted(actual - expected)))
    required = {"id", "title", "stage", "plate_id", "alt", "caption", "draw"}
    plate_ids = set()
    for node_id, item in specs.items():
        if set(item) != required or item["id"] != node_id:
            raise ValueError("Malformed physics illustration spec for {}".format(node_id))
        if type(item["stage"]) is not int or item["stage"] not in STAGE_NAMES:
            raise ValueError("{} has an invalid stage".format(node_id))
        if not callable(item["draw"]):
            raise ValueError("{} needs a drawing function".format(node_id))
        for key in ("title", "plate_id", "alt", "caption"):
            if not isinstance(item[key], str) or not item[key].strip():
                raise ValueError("{} needs {}".format(node_id, key))
        if item["plate_id"] in plate_ids:
            raise ValueError("Duplicate physics plate id {}".format(item["plate_id"]))
        plate_ids.add(item["plate_id"])


def asset_paths(output_root: Path, item: Spec) -> Tuple[Path, Path]:
    directory = output_root / STAGE_DIRS[int(item["stage"])] / "physics"
    stem = str(item["id"]).replace(".", "-")
    return directory / (stem + "-1600.webp"), directory / (stem + "-800.webp")


def render_spec(output_root: Path, item: Spec, *, overwrite: bool = False) -> List[Path]:
    paths = asset_paths(output_root, item)
    existing = [path for path in paths if path.exists()]
    if existing and not overwrite:
        raise FileExistsError("Refusing to overwrite: {}".format(", ".join(map(str, existing))))
    plate = Plate(str(item["id"]), str(item["title"]), int(item["stage"]))
    item["draw"](plate)
    paths[0].parent.mkdir(parents=True, exist_ok=True)
    plate.image.save(paths[0], "WEBP", quality=86, method=6)
    plate.image.resize((800, 500), Image.Resampling.LANCZOS).save(
        paths[1], "WEBP", quality=84, method=6)
    return list(paths)


def illustration_entry(item: Spec) -> Dict[str, object]:
    node_id = str(item["id"])
    stage = int(item["stage"])
    stem = node_id.replace(".", "-")
    prefix = "/app/illustrations/{}/physics/{}".format(STAGE_DIRS[stage], stem)
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


def panel(
    plate: Plate,
    box: Box,
    heading: str,
    *,
    fill: str | None = None,
    outline: str | None = None,
    heading_fill: str | None = None,
) -> Box:
    plate.card(box, fill=fill or hex_rgba(PAPER_LIGHT, 226),
               outline=outline or plate.accent, width=3, radius=22)
    x0, y0, x1, y1 = box
    plate.label(((x0 + x1) / 2, y0 + 42), heading, size=21,
                fill=heading_fill or outline or plate.accent)
    return (x0 + 24, y0 + 86, x1 - 24, y1 - 24)


def footer(plate: Plate, text: str, *, fill: str | None = None, size: int = 30) -> None:
    plate.text((800, 852), text, size=size, bold=True, math_face=True,
               fill=fill or plate.accent, anchor="mm")


def centered_note(plate: Plate, box: Box, text: str, *, size: int = 24,
                  fill: str = INK_SOFT, bold: bool = False) -> None:
    plate.wrapped_text(tuple(map(int, box)), text, size=size, bold=bold, fill=fill, line_gap=7)


def arrow_label(
    plate: Plate,
    start: Point,
    end: Point,
    label: str,
    *,
    fill: str | None = None,
    width: int = 8,
    offset: Point = (0, -18),
) -> None:
    color = fill or plate.accent
    plate.arrow(start, end, fill=color, width=width, head=22)
    plate.text(((start[0] + end[0]) / 2 + offset[0],
                (start[1] + end[1]) / 2 + offset[1]),
               label, size=21, bold=True, fill=color, anchor="mm")


def cart(plate: Plate, center: Point, *, width: int = 160, height: int = 72,
         fill: str = BLUE_LIGHT, outline: str = BLUE) -> None:
    x, y = center
    plate.draw.rounded_rectangle(
        (x - width / 2, y - height / 2, x + width / 2, y + height / 2),
        radius=14, fill=fill, outline=outline, width=4)
    for wx in (x - width * .28, x + width * .28):
        plate.draw.ellipse((wx - 18, y + height / 2 - 3, wx + 18, y + height / 2 + 33),
                           fill=INK_SOFT, outline=INK, width=3)


def force_pair(plate: Plate, center: Point, left: float, right: float,
               *, scale: float = 6, left_label: str = "", right_label: str = "") -> None:
    x, y = center
    if left:
        arrow_label(plate, (x - 84, y), (x - 84 - left * scale, y),
                    left_label or str(left), fill=CORAL, offset=(0, -18))
    if right:
        arrow_label(plate, (x + 84, y), (x + 84 + right * scale, y),
                    right_label or str(right), fill=TEAL, offset=(0, -18))


def thermometer(plate: Plate, center: Point, value: float, label: str,
                *, low: float = 0, high: float = 100, fill: str = CORAL) -> None:
    x, y = center
    top, bottom = y - 120, y + 88
    plate.draw.rounded_rectangle((x - 18, top, x + 18, bottom), radius=16,
                                 fill=PAPER_LIGHT, outline=INK_SOFT, width=4)
    fraction = max(0.0, min(1.0, (value - low) / (high - low)))
    level = bottom - fraction * (bottom - top - 15)
    plate.draw.rounded_rectangle((x - 9, level, x + 9, bottom + 4), radius=8, fill=fill)
    plate.draw.ellipse((x - 32, bottom - 2, x + 32, bottom + 62),
                       fill=fill, outline=INK_SOFT, width=4)
    plate.text((x, bottom + 88), label, size=21, bold=True, anchor="ma")


def wave(
    plate: Plate,
    box: Box,
    *,
    cycles: float = 2,
    amplitude: float = 70,
    fill: str = BLUE,
    width: int = 7,
    phase: float = 0,
) -> List[Point]:
    x0, y0, x1, y1 = box
    mid = (y0 + y1) / 2
    points = []
    for index in range(161):
        t = index / 160
        points.append((x0 + t * (x1 - x0),
                       mid - amplitude * math.sin(2 * math.pi * cycles * t + phase)))
    plate.polyline(points, fill=fill, width=width)
    plate.draw.line((x0, mid, x1, mid), fill=hex_rgba(GRID, 170), width=2)
    return points


def energy_bar(plate: Plate, box: Box, parts: Sequence[Tuple[str, float, str]]) -> None:
    x0, y0, x1, y1 = box
    total = sum(max(0.0, value) for _, value, _ in parts) or 1
    cursor = x0
    for label, value, color in parts:
        right = cursor + (x1 - x0) * max(0.0, value) / total
        plate.draw.rectangle((cursor, y0, right, y1), fill=color, outline=INK_SOFT, width=2)
        if right - cursor > 72:
            plate.text(((cursor + right) / 2, (y0 + y1) / 2), label,
                       size=18, bold=True, anchor="mm")
        cursor = right
    plate.draw.rounded_rectangle(box, radius=8, outline=INK, width=4)


def particle_box(plate: Plate, box: Box, points: Sequence[Point], *,
                 fill: str = BLUE_LIGHT, outline: str = BLUE,
                 radius: int = 14) -> None:
    plate.draw.rounded_rectangle(box, radius=16, fill=hex_rgba(PAPER_LIGHT, 210),
                                 outline=INK_SOFT, width=3)
    for x, y in points:
        plate.dot((x, y), radius, fill=fill, outline=outline, width=3)


def axes(
    plate: Plate,
    box: Box,
    *,
    x_label: str,
    y_label: str,
    x_range: Tuple[float, float] = (0, 1),
    y_range: Tuple[float, float] = (0, 1),
) -> Callable[[float, float], Point]:
    x0, y0, x1, y1 = box
    plate.arrow((x0, y1), (x1, y1), fill=INK, width=4, head=15)
    plate.arrow((x0, y1), (x0, y0), fill=INK, width=4, head=15)
    plate.text((x1, y1 + 18), x_label, size=20, bold=True, anchor="ra")
    plate.text((x0 + 8, y0 - 2), y_label, size=20, bold=True, anchor="la")
    xmin, xmax = x_range
    ymin, ymax = y_range

    def point(x: float, y: float) -> Point:
        return (x0 + (x - xmin) / (xmax - xmin) * (x1 - x0),
                y1 - (y - ymin) / (ymax - ymin) * (y1 - y0))

    return point


def plot_curve(plate: Plate, transform: Callable[[float, float], Point],
               samples: Iterable[Tuple[float, float]], *, fill: str = BLUE,
               width: int = 7) -> None:
    plate.polyline((transform(x, y) for x, y in samples), fill=fill, width=width)


def state_card(plate: Plate, box: Box, heading: str, symbol: str, note: str,
               *, fill: str | None = None) -> None:
    inner = panel(plate, box, heading, outline=fill or plate.accent,
                  heading_fill=fill or plate.accent)
    x0, y0, x1, y1 = inner
    plate.text(((x0 + x1) / 2, y0 + 80), symbol, size=48, bold=True,
               math_face=True, fill=fill or plate.accent, anchor="mm")
    centered_note(plate, (x0 + 8, y0 + 135, x1 - 8, y1), note, size=21)


def three_panel_boxes() -> Tuple[Box, Box, Box]:
    return ((116, 212, 548, 800), (584, 212, 1016, 800), (1052, 212, 1484, 800))


def two_panel_boxes() -> Tuple[Box, Box]:
    return ((116, 212, 782, 800), (818, 212, 1484, 800))


__all__ = [
    "BLUE", "BLUE_LIGHT", "CONTENT", "CORAL", "CORAL_LIGHT", "EDGE", "GOLD",
    "GOLD_LIGHT", "GREEN", "GREEN_LIGHT", "GRID", "HEIGHT", "INK", "INK_SOFT",
    "PAPER", "PAPER_LIGHT", "PLUM", "PLUM_LIGHT", "STAGE_DIRS", "TEAL",
    "TEAL_LIGHT", "WIDTH", "Plate", "Spec", "arrow_label", "asset_paths", "axes",
    "cart", "centered_note", "energy_bar", "footer", "force_pair", "font",
    "hex_rgba", "illustration_entry", "mix", "panel", "particle_box", "plot_curve",
    "render_spec", "spec", "state_card", "thermometer", "three_panel_boxes",
    "two_panel_boxes", "validate_specs", "wave",
]
