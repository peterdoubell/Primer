"""Shared, deterministic drawing grammar for humanities and social-science plates.

The reusable layouts in this module encode relationships: chronology, causation,
comparison, feedback, evidence, argument and worked examples.  Domain modules
supply the lesson-specific claims and labels; this file supplies consistent,
auditable geometry and typography.
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
    PAPER,
    PAPER_LIGHT,
    PLUM,
    PLUM_LIGHT,
    STAGE_DIRS,
    STAGE_NAMES,
    TEAL,
    TEAL_LIGHT,
    WIDTH,
    Plate as _BasePlate,
    font,
    hex_rgba,
    mix,
)


Spec = Dict[str, object]
Point = Tuple[float, float]
Box = Tuple[float, float, float, float]

COLORS = (BLUE, TEAL, GOLD, CORAL, PLUM, GREEN)
LIGHTS = (BLUE_LIGHT, TEAL_LIGHT, GOLD_LIGHT, CORAL_LIGHT, PLUM_LIGHT, GREEN_LIGHT)

# The display accents are excellent borders, but several are too light to be
# small text on paper or on their pale companion fills.  Keep the hue as the
# category cue and use these darker, WCAG-AA text/pill tones for every label.
TEXT_TONES = {
    BLUE: "#20465f",
    TEAL: "#20544f",
    GOLD: "#76520f",
    CORAL: "#7f3d31",
    PLUM: "#513957",
    GREEN: "#344b2d",
}


def _readable_tone(color: str) -> str:
    return TEXT_TONES.get(color, color)


def _relative_luminance(color: str) -> float:
    channels = [int(color[index:index + 2], 16) / 255 for index in (1, 3, 5)]
    linear = [value / 12.92 if value <= .04045
              else ((value + .055) / 1.055) ** 2.4 for value in channels]
    return .2126 * linear[0] + .7152 * linear[1] + .0722 * linear[2]


def _contrast_ratio(first: str, second: str) -> float:
    a, b = _relative_luminance(first), _relative_luminance(second)
    return (max(a, b) + .05) / (min(a, b) + .05)


for _accent, _light in zip(COLORS, LIGHTS):
    assert _contrast_ratio(_readable_tone(_accent), _light) >= 4.5
    assert _contrast_ratio(_readable_tone(_accent), PAPER_LIGHT) >= 4.5


def _needs_symbol_font(value: str) -> bool:
    return any(ord(character) > 127 for character in value)


class Plate(_BasePlate):
    """Primer plate with Unicode-safe text and domain-aware saving."""

    def __init__(self, node_id: str, title: str, stage: int, domain: str):
        self.domain = domain
        super().__init__(node_id, title, stage)

    def text(
        self,
        xy: Point,
        value: str,
        *,
        size: int = 36,
        bold: bool = False,
        math_face: bool = False,
        fill: str = INK,
        anchor: str = "la",
        stroke_width: int = 0,
    ) -> None:
        super().text(
            xy,
            value,
            size=size,
            bold=bold,
            math_face=math_face or _needs_symbol_font(value),
            fill=_readable_tone(fill),
            anchor=anchor,
            stroke_width=stroke_width,
        )

    def save(self, output_root: Path, *, overwrite: bool = False) -> List[Path]:
        directory = output_root / STAGE_DIRS[self.stage] / self.domain
        directory.mkdir(parents=True, exist_ok=True)
        stem = self.node_id.replace(".", "-")
        outputs = [directory / f"{stem}-1600.webp", directory / f"{stem}-800.webp"]
        if not overwrite:
            existing = [path for path in outputs if path.exists()]
            if existing:
                raise FileExistsError("Refusing to overwrite: {}".format(
                    ", ".join(map(str, existing))))
        self.image.save(outputs[0], "WEBP", quality=86, method=6)
        self.image.resize((800, 500), Image.Resampling.LANCZOS).save(
            outputs[1], "WEBP", quality=84, method=6)
        return outputs


def spec(
    node_id: str,
    title: str,
    stage: int,
    domain: str,
    plate_id: str,
    alt: str,
    caption: str,
    draw: Callable[[Plate], None],
) -> Spec:
    return {
        "id": node_id,
        "title": title,
        "stage": stage,
        "domain": domain,
        "plate_id": plate_id,
        "alt": alt,
        "caption": caption,
        "draw": draw,
    }


def _wrap_lines(plate: Plate, text: str, face, width: float) -> List[str]:
    words = text.split()
    if not words:
        return []
    lines: List[str] = []
    current = words[0]
    for word in words[1:]:
        candidate = current + " " + word
        if plate.draw.textlength(candidate, font=face) <= width:
            current = candidate
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def box_text(
    plate: Plate,
    box: Box,
    text: str,
    *,
    size: int = 28,
    minimum: int = 16,
    bold: bool = False,
    fill: str = INK,
    align: str = "center",
    pad: int = 12,
) -> None:
    """Fit wrapped text into a box, shrinking only as far as needed."""

    x0, y0, x1, y1 = box
    fill = _readable_tone(fill)
    chosen = minimum
    lines: List[str] = []
    face = font(minimum, bold=bold, math_face=_needs_symbol_font(text))
    for candidate_size in range(size, minimum - 1, -1):
        candidate_face = font(
            candidate_size, bold=bold, math_face=_needs_symbol_font(text))
        candidate_lines = _wrap_lines(plate, text, candidate_face, x1 - x0 - 2 * pad)
        line_height = candidate_size * 1.18
        if len(candidate_lines) * line_height <= y1 - y0 - 2 * pad:
            chosen = candidate_size
            face = candidate_face
            lines = candidate_lines
            break
    if not lines:
        lines = _wrap_lines(plate, text, face, x1 - x0 - 2 * pad)
    line_height = chosen * 1.18
    y = (y0 + y1 - len(lines) * line_height) / 2
    anchor = "ma" if align == "center" else "la"
    x = (x0 + x1) / 2 if align == "center" else x0 + pad
    for line in lines:
        plate.draw.text((x, y), line, font=face, fill=fill, anchor=anchor)
        y += line_height


def panel(
    plate: Plate,
    box: Box,
    *,
    fill: str = PAPER_LIGHT,
    outline: str | None = None,
    radius: int = 22,
    width: int = 3,
) -> None:
    plate.draw.rounded_rectangle(
        box,
        radius=radius,
        fill=hex_rgba(fill, 225),
        outline=outline or hex_rgba(plate.accent, 145),
        width=width,
    )


def pill(plate: Plate, center: Point, text: str, *, color: str, size: int = 21) -> None:
    face = font(size, bold=True, math_face=_needs_symbol_font(text))
    bounds = plate.draw.textbbox(center, text, font=face, anchor="mm")
    plate.draw.rounded_rectangle(
        (bounds[0] - 15, bounds[1] - 8, bounds[2] + 15, bounds[3] + 8),
        radius=14,
        fill=_readable_tone(color),
    )
    plate.draw.text(center, text, font=face, fill=PAPER_LIGHT, anchor="mm")


def footer(plate: Plate, text: str, *, color: str | None = None) -> None:
    box_text(
        plate,
        (130, 820, 1470, 875),
        text,
        size=27,
        minimum=20,
        bold=True,
        fill=color or plate.accent,
    )


def draw_flow(
    plate: Plate,
    steps: Sequence[Tuple[str, str]],
    conclusion: str,
    *,
    relation: str = "LEADS TO",
) -> None:
    """Draw a left-to-right process or causal chain."""

    count = len(steps)
    gap = 46 if count <= 4 else 34
    left, right = 126, 1474
    width = (right - left - gap * (count - 1)) / count
    y0, y1 = 274, 760
    for index, (heading, detail) in enumerate(steps):
        x0 = left + index * (width + gap)
        x1 = x0 + width
        color = COLORS[index % len(COLORS)]
        light = LIGHTS[index % len(LIGHTS)]
        panel(plate, (x0, y0, x1, y1), fill=light, outline=color)
        pill(plate, ((x0 + x1) / 2, 314), f"{index + 1}", color=color)
        box_text(plate, (x0 + 14, 350, x1 - 14, 445), heading,
                 size=29, minimum=19, bold=True, fill=color)
        plate.draw.line((x0 + 24, 462, x1 - 24, 462), fill=hex_rgba(color, 140), width=3)
        box_text(plate, (x0 + 16, 480, x1 - 16, 724), detail,
                 size=24, minimum=17, fill=INK)
        if index < count - 1:
            arrow_y = 520
            plate.arrow((x1 + 7, arrow_y), (x1 + gap - 7, arrow_y),
                        fill=plate.accent, width=7, head=18)
            if width > 250:
                box_text(plate, (x1 - 8, arrow_y + 25, x1 + gap + 8, arrow_y + 70),
                         relation, size=14, minimum=11, bold=True, fill=INK_SOFT)
    footer(plate, conclusion)


def draw_comparison(
    plate: Plate,
    columns: Sequence[Tuple[str, str, str]],
    conclusion: str,
    *,
    relation: str = "COMPARE THE SAME QUESTION",
) -> None:
    """Draw two to four commensurable columns with a shared comparison bar."""

    count = len(columns)
    gap = 24
    left, right = 120, 1480
    width = (right - left - gap * (count - 1)) / count
    box_text(plate, (150, 198, 1450, 242), relation, size=23, bold=True, fill=INK_SOFT)
    for index, (heading, mechanism, evidence) in enumerate(columns):
        x0 = left + index * (width + gap)
        x1 = x0 + width
        color = COLORS[index % len(COLORS)]
        light = LIGHTS[index % len(LIGHTS)]
        panel(plate, (x0, 256, x1, 770), fill=light, outline=color)
        box_text(plate, (x0 + 12, 278, x1 - 12, 365), heading,
                 size=28, minimum=18, bold=True, fill=color)
        plate.draw.line((x0 + 22, 378, x1 - 22, 378), fill=hex_rgba(color, 150), width=3)
        box_text(plate, (x0 + 18, 392, x1 - 18, 570), mechanism,
                 size=23, minimum=16)
        panel(plate, (x0 + 18, 592, x1 - 18, 742), fill=PAPER_LIGHT,
              outline=mix(color, PAPER, 0.35), radius=16, width=2)
        box_text(plate, (x0 + 28, 604, x1 - 28, 730), evidence,
                 size=20, minimum=14, bold=True, fill=INK_SOFT)
    footer(plate, conclusion)


def draw_timeline(
    plate: Plate,
    events: Sequence[Tuple[str, str, str]],
    conclusion: str,
    *,
    qualifier: str = "TIME RUNS LEFT → RIGHT",
) -> None:
    """Draw a labelled chronology with alternating evidence cards."""

    count = len(events)
    left, right, axis_y = 154, 1446, 520
    box_text(plate, (150, 194, 1450, 236), qualifier, size=22, bold=True, fill=INK_SOFT)
    plate.arrow((left, axis_y), (right, axis_y), fill=INK, width=7, head=22)
    xs = [left + 42 + index * (right - left - 110) / max(1, count - 1)
          for index in range(count)]
    card_width = min(260, (right - left) / count * 0.93)
    for index, ((date, heading, detail), x) in enumerate(zip(events, xs)):
        color = COLORS[index % len(COLORS)]
        above = index % 2 == 0
        y0, y1 = (260, 464) if above else (574, 778)
        panel(plate, (x - card_width / 2, y0, x + card_width / 2, y1),
              fill=LIGHTS[index % len(LIGHTS)], outline=color, radius=16)
        pill(plate, (x, y0 + 28), date, color=color, size=17)
        box_text(plate, (x - card_width / 2 + 10, y0 + 55,
                         x + card_width / 2 - 10, y0 + 110),
                 heading, size=22, minimum=15, bold=True, fill=color)
        box_text(plate, (x - card_width / 2 + 12, y0 + 112,
                         x + card_width / 2 - 12, y1 - 10),
                 detail, size=17, minimum=12, fill=INK)
        plate.draw.line((x, y1 if above else y0, x, axis_y), fill=color, width=4)
        plate.dot((x, axis_y), 12, fill=PAPER_LIGHT, outline=color, width=5)
    footer(plate, conclusion)


def draw_branch(
    plate: Plate,
    source: Tuple[str, str],
    branches: Sequence[Tuple[str, str]],
    conclusion: str,
    *,
    relation: str = "CAN PRODUCE",
) -> None:
    """Draw one cause or question branching to several distinct consequences."""

    panel(plate, (124, 310, 500, 710), fill=GOLD_LIGHT, outline=GOLD)
    pill(plate, (312, 346), "START", color=GOLD)
    box_text(plate, (150, 380, 474, 478), source[0], size=30, minimum=20,
             bold=True, fill=GOLD)
    box_text(plate, (150, 492, 474, 682), source[1], size=23, minimum=16)
    count = len(branches)
    total_h = 500
    gap = 22
    height = (total_h - gap * (count - 1)) / count
    for index, (heading, detail) in enumerate(branches):
        y0 = 248 + index * (height + gap)
        y1 = y0 + height
        color = COLORS[(index + 2) % len(COLORS)]
        panel(plate, (760, y0, 1478, y1), fill=LIGHTS[(index + 2) % len(LIGHTS)],
              outline=color, radius=18)
        box_text(plate, (790, y0 + 10, 1048, y1 - 10), heading,
                 size=25, minimum=17, bold=True, fill=color)
        box_text(plate, (1070, y0 + 10, 1454, y1 - 10), detail,
                 size=21, minimum=14, fill=INK, align="left")
        join_y = (y0 + y1) / 2
        plate.arrow((505, 510), (744, join_y), fill=color, width=6, head=18)
    box_text(plate, (520, 450, 738, 490), relation, size=16, minimum=12,
             bold=True, fill=INK_SOFT)
    footer(plate, conclusion)


def draw_network(
    plate: Plate,
    center: Tuple[str, str],
    nodes: Sequence[Tuple[str, str]],
    conclusion: str,
    *,
    edge_word: str = "SHAPES",
) -> None:
    """Draw a reciprocal system rather than a one-way list."""

    cx, cy = 800, 510
    panel(plate, (615, 382, 985, 638), fill=GOLD_LIGHT, outline=GOLD)
    box_text(plate, (640, 404, 960, 482), center[0], size=29, minimum=20,
             bold=True, fill=GOLD)
    box_text(plate, (642, 492, 958, 614), center[1], size=22, minimum=16)
    positions = ((310, 320), (1290, 320), (310, 700), (1290, 700), (800, 760))
    for index, ((heading, detail), (x, y)) in enumerate(zip(nodes, positions)):
        color = COLORS[index % len(COLORS)]
        w, h = (340, 190) if y != 760 else (410, 132)
        box = (x - w / 2, y - h / 2, x + w / 2, y + h / 2)
        panel(plate, box, fill=LIGHTS[index % len(LIGHTS)], outline=color, radius=18)
        box_text(plate, (box[0] + 12, box[1] + 10, box[2] - 12, box[1] + h * .43),
                 heading, size=24, minimum=16, bold=True, fill=color)
        box_text(plate, (box[0] + 14, box[1] + h * .43, box[2] - 14, box[3] - 8),
                 detail, size=18, minimum=13)
        dx, dy = x - cx, y - cy
        distance = max(math.hypot(dx, dy), 1)
        ux, uy = dx / distance, dy / distance
        plate.double_arrow((cx + ux * 192, cy + uy * 132),
                           (x - ux * (w / 2 + 14), y - uy * (h / 2 + 12)),
                           fill=color, width=5)
    pill(plate, (800, 230), edge_word, color=plate.accent, size=19)
    footer(plate, conclusion)


def draw_evidence(
    plate: Plate,
    sources: Sequence[Tuple[str, str]],
    method: Tuple[str, str],
    result: Tuple[str, str],
    conclusion: str,
) -> None:
    """Draw converging evidence, an explicit method and a qualified result."""

    count = len(sources)
    gap = 18
    left, right = 120, 710
    height = (520 - gap * (count - 1)) / count
    for index, (heading, detail) in enumerate(sources):
        y0 = 244 + index * (height + gap)
        color = COLORS[index % len(COLORS)]
        panel(plate, (left, y0, right, y0 + height),
              fill=LIGHTS[index % len(LIGHTS)], outline=color, radius=16)
        box_text(plate, (142, y0 + 8, 365, y0 + height - 8), heading,
                 size=23, minimum=16, bold=True, fill=color)
        box_text(plate, (380, y0 + 8, 690, y0 + height - 8), detail,
                 size=18, minimum=13, align="left")
        plate.arrow((right + 8, y0 + height / 2), (830, 510), fill=color,
                    width=5, head=16)
    panel(plate, (846, 348, 1120, 672), fill=PLUM_LIGHT, outline=PLUM)
    pill(plate, (983, 382), "METHOD", color=PLUM, size=18)
    box_text(plate, (866, 414, 1100, 500), method[0], size=26, minimum=18,
             bold=True, fill=PLUM)
    box_text(plate, (868, 514, 1098, 646), method[1], size=20, minimum=14)
    plate.arrow((1132, 510), (1210, 510), fill=plate.accent, width=7, head=20)
    panel(plate, (1224, 332, 1480, 688), fill=GOLD_LIGHT, outline=GOLD)
    pill(plate, (1352, 368), "CLAIM", color=GOLD, size=18)
    box_text(plate, (1244, 406, 1460, 505), result[0], size=25, minimum=17,
             bold=True, fill=GOLD)
    box_text(plate, (1246, 520, 1458, 660), result[1], size=19, minimum=13)
    footer(plate, conclusion)


def draw_cycle(
    plate: Plate,
    steps: Sequence[Tuple[str, str]],
    conclusion: str,
    *,
    center_text: Tuple[str, str] = ("ITERATE", "Each pass changes the next."),
) -> None:
    """Draw a process whose result feeds the next attempt."""

    count = len(steps)
    cx, cy, rx, ry = 800, 510, 500, 245
    positions = []
    for index in range(count):
        angle = -math.pi / 2 + index * 2 * math.pi / count
        positions.append((cx + rx * math.cos(angle), cy + ry * math.sin(angle)))
    for index, (x, y) in enumerate(positions):
        nx, ny = positions[(index + 1) % count]
        vx, vy = nx - x, ny - y
        distance = math.hypot(vx, vy)
        ux, uy = vx / distance, vy / distance
        plate.arrow((x + ux * 112, y + uy * 70),
                    (nx - ux * 112, ny - uy * 70),
                    fill=COLORS[index % len(COLORS)], width=6, head=18)
    for index, ((heading, detail), (x, y)) in enumerate(zip(steps, positions)):
        color = COLORS[index % len(COLORS)]
        panel(plate, (x - 122, y - 72, x + 122, y + 72),
              fill=LIGHTS[index % len(LIGHTS)], outline=color, radius=18)
        box_text(plate, (x - 110, y - 60, x + 110, y - 8), heading,
                 size=22, minimum=15, bold=True, fill=color)
        box_text(plate, (x - 110, y - 2, x + 110, y + 60), detail,
                 size=16, minimum=12)
    panel(plate, (620, 430, 980, 590), fill=PAPER_LIGHT, outline=plate.accent)
    box_text(plate, (642, 448, 958, 500), center_text[0], size=27, minimum=20,
             bold=True, fill=plate.accent)
    box_text(plate, (642, 510, 958, 574), center_text[1], size=18, minimum=14)
    footer(plate, conclusion)


def draw_matrix(
    plate: Plate,
    row_labels: Sequence[str],
    column_labels: Sequence[str],
    cells: Sequence[Sequence[str]],
    conclusion: str,
    *,
    corner: str = "CASE",
) -> None:
    """Draw an explicit comparison or payoff matrix."""

    rows, columns = len(row_labels), len(column_labels)
    x0, y0, x1, y1 = 300, 290, 1450, 760
    row_head_w, col_head_h = 230, 86
    cell_w = (x1 - x0 - row_head_w) / columns
    cell_h = (y1 - y0 - col_head_h) / rows
    panel(plate, (x0, y0, x1, y1), fill=PAPER_LIGHT, outline=INK_SOFT, radius=12)
    box_text(plate, (x0 + 8, y0 + 8, x0 + row_head_w - 8, y0 + col_head_h - 8),
             corner, size=22, minimum=16, bold=True, fill=INK_SOFT)
    for col, label in enumerate(column_labels):
        left = x0 + row_head_w + col * cell_w
        panel(plate, (left, y0, left + cell_w, y0 + col_head_h),
              fill=BLUE_LIGHT, outline=BLUE, radius=4, width=2)
        box_text(plate, (left + 8, y0 + 8, left + cell_w - 8, y0 + col_head_h - 8),
                 label, size=22, minimum=15, bold=True, fill=BLUE)
    for row, label in enumerate(row_labels):
        top = y0 + col_head_h + row * cell_h
        panel(plate, (x0, top, x0 + row_head_w, top + cell_h),
              fill=TEAL_LIGHT, outline=TEAL, radius=4, width=2)
        box_text(plate, (x0 + 10, top + 8, x0 + row_head_w - 10, top + cell_h - 8),
                 label, size=22, minimum=15, bold=True, fill=TEAL)
        for col in range(columns):
            left = x0 + row_head_w + col * cell_w
            fill = LIGHTS[(row * columns + col + 2) % len(LIGHTS)]
            color = COLORS[(row * columns + col + 2) % len(COLORS)]
            panel(plate, (left, top, left + cell_w, top + cell_h),
                  fill=fill, outline=color, radius=4, width=2)
            box_text(plate, (left + 12, top + 10, left + cell_w - 12, top + cell_h - 10),
                     cells[row][col], size=23, minimum=15, bold=True, fill=color)
    footer(plate, conclusion)


def draw_tracks(
    plate: Plate,
    tracks: Sequence[Tuple[str, Sequence[Tuple[str, str]]]],
    conclusion: str,
    *,
    direction: str = "PARALLEL DEVELOPMENTS — NOT A SINGLE LADDER",
) -> None:
    """Draw concurrent or nested tracks with comparable phases."""

    box_text(plate, (170, 192, 1430, 232), direction, size=21, bold=True, fill=INK_SOFT)
    row_h = 500 / len(tracks)
    for row, (label, segments) in enumerate(tracks):
        top = 260 + row * row_h
        bottom = top + row_h - 18
        color = COLORS[row % len(COLORS)]
        box_text(plate, (118, top, 326, bottom), label, size=22, minimum=15,
                 bold=True, fill=color)
        left, right = 350, 1480
        segment_w = (right - left - 16 * (len(segments) - 1)) / len(segments)
        for index, (heading, detail) in enumerate(segments):
            x0 = left + index * (segment_w + 16)
            panel(plate, (x0, top, x0 + segment_w, bottom),
                  fill=LIGHTS[(row + index) % len(LIGHTS)], outline=color, radius=14)
            box_text(plate, (x0 + 10, top + 6, x0 + segment_w - 10,
                             top + (bottom - top) * .43), heading,
                     size=20, minimum=14, bold=True, fill=color)
            box_text(plate, (x0 + 10, top + (bottom - top) * .43,
                             x0 + segment_w - 10, bottom - 6), detail,
                     size=16, minimum=11)
    footer(plate, conclusion)


def validate_specs(specs: Dict[str, Spec], expected_ids: Iterable[str]) -> None:
    expected = set(expected_ids)
    actual = set(specs)
    if actual != expected:
        raise ValueError("Humanities spec mismatch; missing={}, extra={}".format(
            sorted(expected - actual), sorted(actual - expected)))
    required = {"id", "title", "stage", "domain", "plate_id", "alt", "caption", "draw"}
    plate_ids = set()
    alts = set()
    captions = set()
    for node_id, item in specs.items():
        if set(item) != required or item["id"] != node_id:
            raise ValueError(f"Malformed humanities illustration spec for {node_id}")
        if type(item["stage"]) is not int or item["stage"] not in STAGE_NAMES:
            raise ValueError(f"{node_id} has an invalid stage")
        if item["domain"] not in {"history", "arts", "mind-society"}:
            raise ValueError(f"{node_id} has an invalid asset domain")
        if not callable(item["draw"]):
            raise ValueError(f"{node_id} needs a drawing function")
        for key in ("title", "plate_id", "alt", "caption"):
            if not isinstance(item[key], str) or not item[key].strip():
                raise ValueError(f"{node_id} needs {key}")
        if len(str(item["alt"]).split()) < 12 or len(str(item["caption"]).split()) < 12:
            raise ValueError(f"{node_id} needs descriptive alt text and caption")
        for key, seen in (("plate_id", plate_ids), ("alt", alts), ("caption", captions)):
            if item[key] in seen:
                raise ValueError(f"Duplicate humanities {key}: {item[key]}")
            seen.add(item[key])


def asset_paths(output_root: Path, item: Spec) -> Tuple[Path, Path]:
    directory = output_root / STAGE_DIRS[int(item["stage"])] / str(item["domain"])
    stem = str(item["id"]).replace(".", "-")
    return directory / f"{stem}-1600.webp", directory / f"{stem}-800.webp"


def render_spec(output_root: Path, item: Spec, *, overwrite: bool = False) -> List[Path]:
    paths = asset_paths(output_root, item)
    existing = [path for path in paths if path.exists()]
    if existing and not overwrite:
        raise FileExistsError("Refusing to overwrite: {}".format(", ".join(map(str, existing))))
    plate = Plate(str(item["id"]), str(item["title"]), int(item["stage"]), str(item["domain"]))
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
    prefix = "/app/illustrations/{}/{}/{}".format(
        STAGE_DIRS[stage], item["domain"], stem)
    return {
        "id": item["plate_id"],
        "kind": "illustration",
        "src": prefix + "-800.webp",
        "srcset": f"{prefix}-800.webp 800w, {prefix}-1600.webp 1600w",
        "alt": item["alt"],
        "caption": item["caption"],
        "width": WIDTH,
        "height": HEIGHT,
    }
