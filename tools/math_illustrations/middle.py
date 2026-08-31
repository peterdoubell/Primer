"""Deterministic mathematics plates for the Sapling and Tree stages."""

from __future__ import annotations

import math
from typing import Callable, Dict, Iterable, Sequence, Tuple

from .core import (
    BLUE,
    BLUE_LIGHT,
    CORAL,
    CORAL_LIGHT,
    EDGE,
    GOLD,
    GOLD_LIGHT,
    GREEN,
    GREEN_LIGHT,
    INK,
    INK_SOFT,
    PAPER_LIGHT,
    PLUM,
    PLUM_LIGHT,
    TEAL,
    TEAL_LIGHT,
    Plate,
    Spec,
    hex_rgba,
    validate_specs,
)


Box = Tuple[float, float, float, float]
Point = Tuple[float, float]


def _panel(plate: Plate, box: Box, title: str) -> Box:
    """Draw a titled card and return its usable interior."""
    x0, y0, x1, y1 = box
    plate.card(box, fill="#fffaf0")
    plate.text((x0 + 24, y0 + 22), title, size=28, bold=True, fill=plate.accent)
    plate.draw.line((x0 + 22, y0 + 66, x1 - 22, y0 + 66), fill=hex_rgba(plate.accent, 95), width=3)
    return x0 + 24, y0 + 88, x1 - 24, y1 - 24


def _center(plate: Plate, xy: Point, value: str, *, size: int = 32, bold: bool = False,
            fill: str = INK, math_face: bool = False) -> None:
    plate.text(xy, value, size=size, bold=bold, fill=fill, math_face=math_face, anchor="mm")


def _hatched_rect(plate: Plate, box: Box, *, fill: str, outline: str = INK,
                  spacing: int = 18, cross: bool = False, width: int = 2) -> None:
    """Fill a rectangle and add a clipped, non-colour texture."""
    x0, y0, x1, y1 = box
    plate.draw.rectangle(box, fill=fill, outline=outline, width=width)
    for y in range(int(y0) + 5, int(y1) - 3, spacing):
        for x in range(int(x0) + 5, int(x1) - 3, spacing):
            end_x = min(x + 10, x1 - 3)
            end_y = min(y + 10, y1 - 3)
            plate.draw.line((x, y, end_x, end_y), fill=hex_rgba(outline, 155), width=2)
            if cross:
                plate.draw.line((end_x, y, x, end_y), fill=hex_rgba(outline, 130), width=2)


def _diamond(plate: Plate, center: Point, radius: float, *, fill: str, outline: str = INK,
             width: int = 3) -> None:
    x, y = center
    plate.draw.polygon(((x, y - radius), (x + radius, y), (x, y + radius), (x - radius, y)),
                       fill=fill, outline=outline)
    if width > 1:
        for inset in range(1, width):
            r = max(1, radius - inset)
            plate.draw.line(((x, y - r), (x + r, y), (x, y + r), (x - r, y), (x, y - r)),
                            fill=outline, width=1)


def _number_line(plate: Plate, box: Box, low: int, high: int, *, label_every: int = 1,
                 label_formatter: Callable[[int], str] = str) -> Callable[[float], float]:
    x0, y0, x1, y1 = box
    y = (y0 + y1) / 2
    plate.double_arrow((x0 + 4, y), (x1 - 4, y), fill=INK, width=5)

    def map_x(value: float) -> float:
        return x0 + (value - low) / (high - low) * (x1 - x0)

    for value in range(low, high + 1):
        x = map_x(value)
        tick = 18 if value % label_every == 0 else 10
        plate.draw.line((x, y - tick, x, y + tick), fill=INK, width=3)
        if value % label_every == 0:
            _center(plate, (x, y + 43), label_formatter(value).replace("-", "−"), size=22)
    return map_x


def _plot(plate: Plate, point: Callable[[float, float], Point], function: Callable[[float], float],
          start: float, end: float, *, samples: int = 160, fill: str = BLUE,
          width: int = 7) -> None:
    values = []
    for index in range(samples + 1):
        x = start + (end - start) * index / samples
        values.append(point(x, function(x)))
    plate.polyline(values, fill=fill, width=width)


def _dashed_polyline(plate: Plate, points: Sequence[Point], *, fill: str, width: int = 5) -> None:
    for first, second in zip(points, points[1:]):
        plate.dashed_line(first, second, fill=fill, width=width, dash=13, gap=9)


def _dot_array(plate: Plate, box: Box, rows: int, columns: int, *, fill: str,
               shape: str = "circle") -> None:
    x0, y0, x1, y1 = box
    spacing_x = (x1 - x0) / max(columns, 1)
    spacing_y = (y1 - y0) / max(rows, 1)
    radius = min(spacing_x, spacing_y) * 0.24
    for row in range(rows):
        for column in range(columns):
            center = (x0 + (column + 0.5) * spacing_x, y0 + (row + 0.5) * spacing_y)
            if shape == "diamond":
                _diamond(plate, center, radius, fill=fill)
            elif shape == "square":
                x, y = center
                _hatched_rect(plate, (x - radius, y - radius, x + radius, y + radius),
                              fill=fill, spacing=12)
            else:
                plate.dot(center, radius, fill=fill, outline=INK, width=2)


def draw_decimals(plate: Plate) -> None:
    left = _panel(plate, (120, 210, 770, 850), "PLACE VALUE")
    x0, y0, x1, _ = left
    headers = ("ones", "tenths", "hundredths", "thousandths")
    values = (("0.700", (0, 7, 0, 0)), ("0.089", (0, 0, 8, 9)))
    table_top = y0 + 52
    table_left = x0 + 100
    cell_w = (x1 - table_left) / 4
    for column, header in enumerate(headers):
        cx0 = table_left + column * cell_w
        plate.draw.rectangle((cx0, table_top, cx0 + cell_w, table_top + 218),
                             fill=hex_rgba(BLUE_LIGHT if column == 1 else PAPER_LIGHT, 190),
                             outline=EDGE, width=2)
        _center(plate, (cx0 + cell_w / 2, table_top + 30), header, size=15, bold=True)
    for row, (label, digits) in enumerate(values):
        cy = table_top + 92 + row * 80
        plate.text((table_left - 16, cy), label, size=25, bold=True, fill=INK_SOFT, anchor="rm")
        for column, digit in enumerate(digits):
            _center(plate, (table_left + (column + 0.5) * cell_w, cy), str(digit), size=43,
                    bold=(row == 0 and column == 1) or (row == 1 and column == 2),
                    fill=BLUE if row == 0 else CORAL)
    _center(plate, ((x0 + x1) / 2, table_top + 290), "7 tenths > 0 tenths", size=29, bold=True)
    _center(plate, ((x0 + x1) / 2, table_top + 340), "so 0.700 > 0.089", size=35, bold=True, fill=plate.accent)

    right = _panel(plate, (800, 210, 1480, 850), "SAME SCALE: 0 TO 1")
    rx0, ry0, rx1, _ = right
    _number_line(plate, (rx0 + 35, ry0 + 230, rx1 - 35, ry0 + 350), 0, 10,
                 label_every=1, label_formatter=lambda value: "{:.1f}".format(value / 10))
    # Map tenths labels to decimal values; the exact points are placed independently.
    line_left, line_right = rx0 + 35, rx1 - 35
    point_x = lambda value: line_left + value * (line_right - line_left)
    _diamond(plate, (point_x(0.089), ry0 + 250), 18, fill=CORAL_LIGHT)
    plate.dot((point_x(0.700), ry0 + 250), 18, fill=BLUE_LIGHT)
    plate.text((point_x(0.089), ry0 + 185), "0.089", size=24, bold=True, fill=CORAL, anchor="ma")
    plate.text((point_x(0.700), ry0 + 185), "0.700", size=24, bold=True, fill=BLUE, anchor="ma")
    _center(plate, ((rx0 + rx1) / 2, ry0 + 435), "0.700 = 0.7", size=36, bold=True)
    _center(plate, ((rx0 + rx1) / 2, ry0 + 495), "Trailing zeros do not change value.", size=24, fill=INK_SOFT)


def draw_percent(plate: Plate) -> None:
    left = _panel(plate, (120, 210, 740, 770), "THREE OF FIVE EQUAL PARTS")
    x0, y0, x1, _ = left
    strip = (x0 + 35, y0 + 85, x1 - 35, y0 + 255)
    cell_w = (strip[2] - strip[0]) / 5
    for index in range(5):
        box = (strip[0] + index * cell_w, strip[1], strip[0] + (index + 1) * cell_w, strip[3])
        if index < 3:
            _hatched_rect(plate, box, fill=BLUE_LIGHT, cross=True, spacing=22)
        else:
            plate.draw.rectangle(box, fill=PAPER_LIGHT, outline=INK, width=3)
        _center(plate, ((box[0] + box[2]) / 2, box[3] + 34), str(index + 1), size=20, fill=INK_SOFT)
    _center(plate, ((x0 + x1) / 2, y0 + 335), "3 / 5", size=54, bold=True, math_face=True)
    _center(plate, ((x0 + x1) / 2, y0 + 400), "3 ÷ 5 = 0.60", size=31, bold=True, fill=BLUE)

    right = _panel(plate, (770, 210, 1480, 770), "SIXTY OF ONE HUNDRED")
    rx0, ry0, rx1, _ = right
    cell = 36
    grid_x = (rx0 + rx1 - 10 * cell) / 2
    grid_y = ry0 + 30
    for row in range(10):
        for column in range(10):
            box = (grid_x + column * cell, grid_y + row * cell,
                   grid_x + (column + 1) * cell, grid_y + (row + 1) * cell)
            if row * 10 + column < 60:
                _hatched_rect(plate, box, fill=TEAL_LIGHT, spacing=13, width=1)
            else:
                plate.draw.rectangle(box, fill=PAPER_LIGHT, outline=INK_SOFT, width=1)
    plate.label(((rx0 + rx1) / 2, grid_y + 410), "60 shaded squares = 60%", fill=TEAL)
    plate.card((260, 795, 1340, 875), fill=GOLD_LIGHT, outline=GOLD, radius=18)
    _center(plate, (800, 835), "3/5  =  0.60  =  60%  =  60 per 100", size=37, bold=True)


def draw_negatives(plate: Plate) -> None:
    inner = _panel(plate, (120, 220, 1480, 820), "NUMBERS GROW AS YOU MOVE RIGHT")
    x0, y0, x1, _ = inner
    map_x = _number_line(plate, (x0 + 25, y0 + 125, x1 - 25, y0 + 265), -12, 12, label_every=2)
    movement_y = y0 + 75
    plate.arrow((map_x(-2), movement_y), (map_x(-9), movement_y), fill=CORAL, width=11, head=28)
    plate.draw.rectangle((map_x(-2) - 16, movement_y - 16, map_x(-2) + 16, movement_y + 16),
                         fill=BLUE_LIGHT, outline=INK, width=3)
    _diamond(plate, (map_x(-9), movement_y), 18, fill=CORAL_LIGHT)
    plate.text((map_x(-2), movement_y - 36), "START −2", size=24, bold=True, fill=BLUE, anchor="ms")
    plate.text((map_x(-9), movement_y - 36), "END −9", size=24, bold=True, fill=CORAL, anchor="ms")
    _center(plate, ((x0 + x1) / 2, y0 + 340), "−2 − 7 = −9", size=48, bold=True, math_face=True)
    plate.card((x0 + 110, y0 + 395, x1 - 110, y0 + 500), fill=PLUM_LIGHT, outline=PLUM)
    _center(plate, ((x0 + x1) / 2, y0 + 430), "−8 < −3", size=38, bold=True)
    _center(plate, ((x0 + x1) / 2, y0 + 474), "−3 is greater because it lies farther right.", size=25)


def draw_order_ops(plate: Plate) -> None:
    labels = ("START", "DIVIDE", "MULTIPLY", "ADD")
    expressions = ("6 + 12 ÷ 3 × 2", "6 + 4 × 2", "6 + 8", "14")
    boxes = []
    for index in range(4):
        x0 = 120 + index * 345
        box = (x0, 295, x0 + 300, 610)
        boxes.append(box)
        _panel(plate, box, labels[index])
        _center(plate, ((box[0] + box[2]) / 2, 455), expressions[index], size=38, bold=True, math_face=True)
        plate.label(((box[0] + box[2]) / 2, 555), "STEP {}".format(index + 1),
                    fill=(BLUE, TEAL, GOLD, CORAL)[index])
        if index:
            plate.arrow((box[0] - 38, 455), (box[0] - 8, 455), fill=INK_SOFT, width=6, head=17)
    plate.card((190, 675, 1410, 825), fill=GOLD_LIGHT, outline=GOLD)
    _center(plate, (800, 720), "Division and multiplication have equal priority.", size=31, bold=True)
    _center(plate, (800, 770), "Work them from left to right; brackets can change the order.", size=28)


def draw_primes(plate: Plate) -> None:
    panels = ((120, 220, 550, 820), (585, 220, 1015, 820), (1050, 220, 1480, 820))
    # Twelve has more than one non-trivial array.
    x0, y0, x1, _ = _panel(plate, panels[0], "12: COMPOSITE")
    _dot_array(plate, (x0 + 20, y0 + 20, x1 - 20, y0 + 155), 2, 6, fill=BLUE_LIGHT)
    _center(plate, ((x0 + x1) / 2, y0 + 185), "2 × 6", size=27, bold=True)
    _dot_array(plate, (x0 + 65, y0 + 225, x1 - 65, y0 + 405), 3, 4, fill=TEAL_LIGHT, shape="square")
    _center(plate, ((x0 + x1) / 2, y0 + 440), "3 × 4", size=27, bold=True)
    _center(plate, ((x0 + x1) / 2, y0 + 485), "factors: 1, 2, 3, 4, 6, 12", size=20)
    # Thirteen only has the 1 by 13 array.
    x0, y0, x1, _ = _panel(plate, panels[1], "13: PRIME")
    _dot_array(plate, (x0 + 10, y0 + 95, x1 - 10, y0 + 185), 1, 13, fill=GOLD_LIGHT, shape="diamond")
    _center(plate, ((x0 + x1) / 2, y0 + 235), "1 × 13 only", size=30, bold=True)
    plate.label(((x0 + x1) / 2, y0 + 330), "exactly two divisors", fill=GOLD)
    _center(plate, ((x0 + x1) / 2, y0 + 410), "1 and 13", size=40, bold=True)
    # One is neither prime nor composite.
    x0, y0, x1, _ = _panel(plate, panels[2], "1: NEITHER")
    plate.dot(((x0 + x1) / 2, y0 + 165), 42, fill=PLUM_LIGHT)
    _center(plate, ((x0 + x1) / 2, y0 + 250), "one divisor", size=31, bold=True)
    _center(plate, ((x0 + x1) / 2, y0 + 315), "1", size=50, bold=True, fill=PLUM)
    plate.wrapped_text((x0 + 30, y0 + 365, x1 - 30, y0 + 505),
                       "Prime means exactly two distinct positive divisors.", size=25, bold=True)


def _ratio_legend(plate: Plate, x0: float, y: float, x1: float) -> None:
    """Keep the symbol key in its own row, clear of every countable token."""
    _hatched_rect(plate, (x0 + 8, y - 13, x0 + 34, y + 13), fill=GOLD_LIGHT, spacing=9)
    plate.text((x0 + 46, y), "flour", size=20, bold=True, fill=INK, anchor="lm")
    plate.dot((x1 - 116, y), 13, fill=BLUE_LIGHT, outline=INK, width=2)
    plate.text((x1 - 92, y), "milk", size=20, bold=True, fill=INK, anchor="lm")


def _ratio_batch(plate: Plate, box: Box, copy_label: str) -> None:
    """Draw one visibly bounded, directly countable copy of the 2:3 batch."""
    x0, y0, x1, y1 = box
    plate.draw.rounded_rectangle(box, radius=16, fill="#ffffff", outline=TEAL, width=4)
    cx = (x0 + x1) / 2
    _center(plate, (cx, y0 + 27), copy_label, size=18, bold=True, fill=TEAL)
    for x in (cx - 28, cx + 28):
        _hatched_rect(plate, (x - 15, y0 + 61, x + 15, y0 + 91),
                      fill=GOLD_LIGHT, spacing=10)
    for x in (cx - 39, cx, cx + 39):
        plate.dot((x, y0 + 135), 15, fill=BLUE_LIGHT, outline=INK, width=2)
    _center(plate, (cx, y1 - 26), "2 : 3", size=24, bold=True)


def draw_ratio(plate: Plate) -> None:
    left = _panel(plate, (120, 220, 700, 780), "ONE BATCH: 2 : 3")
    x0, y0, x1, _ = left
    _ratio_legend(plate, x0 + 25, y0 + 24, x1 - 25)
    _ratio_batch(plate, (x0 + 125, y0 + 68, x1 - 125, y0 + 330), "ORIGINAL")
    _center(plate, ((x0 + x1) / 2, y0 + 385), "2 flour : 3 milk", size=28, bold=True)

    right = _panel(plate, (900, 220, 1480, 780), "THREE BATCHES: 6 : 9")
    rx0, ry0, rx1, _ = right
    _ratio_legend(plate, rx0 + 25, ry0 + 24, rx1 - 25)
    batch_width = 158
    for index, batch_x in enumerate((rx0 + 10, rx0 + 184, rx0 + 358), start=1):
        _ratio_batch(
            plate,
            (batch_x, ry0 + 68, batch_x + batch_width, ry0 + 330),
            "COPY {}".format(index),
        )
    _center(plate, ((rx0 + rx1) / 2, ry0 + 385),
            "3 copies = 6 flour : 9 milk", size=25, bold=True)
    plate.arrow((735, 485), (865, 485), fill=TEAL, width=10, head=28)
    plate.label((800, 425), "× 3", fill=TEAL)
    plate.card((300, 805, 1300, 875), fill=TEAL_LIGHT, outline=TEAL, radius=18)
    _center(plate, (800, 840), "2 : 3  =  (2 × 3) : (3 × 3)  =  6 : 9", size=34, bold=True)


def _tiled_rectangle(plate: Plate, origin: Point, columns: int, rows: int, cell: int, *, fill: str) -> None:
    x0, y0 = origin
    for row in range(rows):
        for column in range(columns):
            box = (x0 + column * cell, y0 + row * cell,
                   x0 + (column + 1) * cell, y0 + (row + 1) * cell)
            plate.draw.rectangle(box, fill=fill, outline=INK_SOFT, width=2)
            if (row + column) % 2 == 0:
                plate.draw.line((box[0] + 5, box[1] + 5, box[2] - 5, box[3] - 5),
                                fill=hex_rgba(INK_SOFT, 90), width=2)


def draw_geometry(plate: Plate) -> None:
    first = _panel(plate, (120, 220, 540, 820), "8 × 2 RECTANGLE")
    x0, y0, x1, _ = first
    _tiled_rectangle(plate, (x0 + 30, y0 + 120), 8, 2, 40, fill=BLUE_LIGHT)
    _center(plate, ((x0 + x1) / 2, y0 + 250), "perimeter = 20 units", size=25, bold=True)
    _center(plate, ((x0 + x1) / 2, y0 + 300), "area = 16 square units", size=25, bold=True, fill=BLUE)
    _center(plate, ((x0 + x1) / 2, y0 + 385), "length around", size=21, fill=INK_SOFT)
    _center(plate, ((x0 + x1) / 2, y0 + 425), "space inside", size=21, fill=INK_SOFT)

    second = _panel(plate, (590, 220, 1010, 820), "5 × 5 SQUARE")
    x0, y0, x1, _ = second
    _tiled_rectangle(plate, (x0 + 82, y0 + 60), 5, 5, 42, fill=GOLD_LIGHT)
    _center(plate, ((x0 + x1) / 2, y0 + 320), "perimeter = 20 units", size=25, bold=True)
    _center(plate, ((x0 + x1) / 2, y0 + 370), "area = 25 square units", size=25, bold=True, fill=GOLD)
    _center(plate, ((x0 + x1) / 2, y0 + 445), "same perimeter ≠ same area", size=23, bold=True)

    third = _panel(plate, (1060, 220, 1480, 820), "4 × 3 × 2 CUBOID")
    x0, y0, x1, _ = third
    cell = 35
    layer_y = y0 + 125
    layer_origins = (x0 + 22, x0 + 208)
    for layer, origin_x in enumerate(layer_origins, start=1):
        _center(plate, (origin_x + 2 * cell, y0 + 82), "LAYER {}: 4 × 3".format(layer),
                size=18, bold=True, fill=TEAL if layer == 1 else GREEN)
        _tiled_rectangle(
            plate, (origin_x, layer_y), 4, 3, cell,
            fill=TEAL_LIGHT if layer == 1 else GREEN_LIGHT,
        )
    _center(plate, ((x0 + x1) / 2, layer_y + 1.5 * cell), "+", size=36, bold=True)
    _center(plate, ((x0 + x1) / 2, y0 + 285), "12 cubes + 12 cubes = 24 cubes",
            size=22, bold=True, fill=TEAL)
    _center(plate, ((x0 + x1) / 2, y0 + 350), "2 layers × 4 × 3", size=24, bold=True)
    _center(plate, ((x0 + x1) / 2, y0 + 410), "volume = 24 cubic units", size=23, bold=True)


def draw_exponents(plate: Plate) -> None:
    left = _panel(plate, (120, 230, 625, 800), "POWER")
    x0, y0, x1, _ = left
    _center(plate, ((x0 + x1) / 2, y0 + 145), "4³", size=120, bold=True, math_face=True)
    plate.arrow((x0 + 115, y0 + 260), (x0 + 180, y0 + 205), fill=BLUE, width=6, head=17)
    plate.text((x0 + 20, y0 + 277), "base: 4", size=27, bold=True, fill=BLUE)
    plate.arrow((x1 - 70, y0 + 70), (x1 - 155, y0 + 112), fill=CORAL, width=6, head=17)
    plate.text((x1 - 10, y0 + 32), "exponent: 3", size=27, bold=True, fill=CORAL, anchor="ra")
    plate.wrapped_text((x0 + 35, y0 + 330, x1 - 35, y0 + 455),
                       "The exponent counts copies of the base.", size=27, bold=True)

    right = _panel(plate, (675, 230, 1480, 800), "REPEATED MULTIPLICATION")
    rx0, ry0, rx1, _ = right
    for index in range(3):
        box = (rx0 + 70 + index * 205, ry0 + 80, rx0 + 210 + index * 205, ry0 + 220)
        _hatched_rect(plate, box, fill=GOLD_LIGHT, cross=index == 1, spacing=22)
        _center(plate, ((box[0] + box[2]) / 2, (box[1] + box[3]) / 2), "4", size=62, bold=True)
        if index < 2:
            _center(plate, (box[2] + 32, (box[1] + box[3]) / 2), "×", size=39, bold=True)
    _center(plate, ((rx0 + rx1) / 2, ry0 + 305), "4 × 4 × 4 = 64", size=43, bold=True, fill=GOLD)
    plate.card((rx0 + 85, ry0 + 365, rx1 - 85, ry0 + 455), fill=CORAL_LIGHT, outline=CORAL)
    _center(plate, ((rx0 + rx1) / 2, ry0 + 410), "Not 4 × 3 = 12", size=31, bold=True)


def draw_coordinates(plate: Plate) -> None:
    graph_box = (150, 250, 940, 820)
    point = plate.axes(graph_box, x_range=(-6, 6), y_range=(-5, 5), grid_step=1)
    for value in range(-6, 7, 2):
        if value:
            plate.text((point(value, 0)[0], point(0, 0)[1] + 16), str(value).replace("-", "−"),
                       size=18, anchor="ma", fill=INK_SOFT)
    for value in range(-4, 5, 2):
        if value:
            plate.text((point(0, 0)[0] - 14, point(0, value)[1]), str(value).replace("-", "−"),
                       size=18, anchor="rm", fill=INK_SOFT)
    _center(plate, point(3.8, 3.8), "I", size=24, bold=True, fill=INK_SOFT)
    _center(plate, point(-3.8, 3.8), "II", size=24, bold=True, fill=INK_SOFT)
    _center(plate, point(-3.8, -3.8), "III", size=24, bold=True, fill=INK_SOFT)
    _center(plate, point(3.8, -3.8), "IV", size=24, bold=True, fill=INK_SOFT)
    plate.arrow(point(0, 0), point(-3, 0), fill=BLUE, width=10, head=23)
    plate.arrow(point(-3, 0), point(-3, 2), fill=CORAL, width=10, head=23)
    plate.draw.rectangle((point(-3, 2)[0] - 17, point(-3, 2)[1] - 17,
                         point(-3, 2)[0] + 17, point(-3, 2)[1] + 17),
                        fill=GOLD_LIGHT, outline=INK, width=3)
    plate.text((point(-3, 2)[0] + 28, point(-3, 2)[1] - 12), "(−3, 2)", size=25, bold=True)
    plate.label((point(-1.5, 0)[0], point(0, 0)[1] + 62), "left 3", fill=BLUE)
    plate.label((point(-3, 1)[0] - 65, point(-3, 1)[1]), "up 2", fill=CORAL)
    right = _panel(plate, (990, 250, 1480, 820), "READ x, THEN y")
    x0, y0, x1, _ = right
    _center(plate, ((x0 + x1) / 2, y0 + 90), "(−3, 2)", size=58, bold=True, math_face=True)
    _center(plate, ((x0 + x1) / 2, y0 + 175), "x = −3, move left", size=28, bold=True, fill=BLUE)
    _center(plate, ((x0 + x1) / 2, y0 + 235), "y = 2, move up", size=28, bold=True, fill=CORAL)
    plate.card((x0 + 20, y0 + 310, x1 - 20, y0 + 450), fill=PLUM_LIGHT, outline=PLUM)
    plate.wrapped_text((x0 + 42, y0 + 325, x1 - 42, y0 + 435),
                       "A point on an axis is not inside a quadrant.", size=25, bold=True)


def draw_data(plate: Plate) -> None:
    inner = _panel(plate, (120, 220, 1480, 820), "FIVE SCORES: 4, 5, 6, 7, 68")
    x0, y0, x1, _ = inner
    line_left, line_right = x0 + 45, x1 - 45
    y = y0 + 190
    plate.arrow((line_left, y), (line_right, y), fill=INK, width=5, head=17)
    map_x = lambda value: line_left + value / 70 * (line_right - line_left)
    for value in range(0, 71, 10):
        x = map_x(value)
        plate.draw.line((x, y - 15, x, y + 15), fill=INK, width=3)
        _center(plate, (x, y + 38), str(value), size=20)
    for index, value in enumerate((4, 5, 6, 7, 68)):
        shape_y = y - 44 - (index % 2) * 42 if value < 10 else y - 48
        if value == 68:
            _diamond(plate, (map_x(value), shape_y), 15, fill=CORAL_LIGHT)
            plate.text((map_x(value), shape_y - 26), "outlier 68", size=22, bold=True,
                       fill=CORAL, anchor="ms")
        else:
            plate.dot((map_x(value), shape_y), 10, fill=BLUE_LIGHT)
            plate.text((map_x(value), shape_y - 20), str(value), size=18, bold=True, anchor="ms")
    median_x, mean_x = map_x(6), map_x(18)
    plate.dashed_line((median_x, y + 65), (median_x, y + 180), fill=BLUE, width=6)
    plate.dashed_line((mean_x, y + 65), (mean_x, y + 180), fill=CORAL, width=6)
    plate.draw.rectangle((median_x - 12, y + 172, median_x + 12, y + 196),
                         fill=BLUE_LIGHT, outline=BLUE, width=3)
    _diamond(plate, (mean_x, y + 184), 14, fill=CORAL_LIGHT, outline=CORAL)
    plate.text((median_x, y + 212), "median = 6", size=24, bold=True, fill=BLUE, anchor="ma")
    plate.text((mean_x, y + 212), "mean = 18", size=24, bold=True, fill=CORAL, anchor="ma")
    plate.card((x0 + 185, y0 + 440, x1 - 185, y0 + 505), fill=GOLD_LIGHT, outline=GOLD)
    _center(plate, ((x0 + x1) / 2, y0 + 472),
            "One distant value pulls the mean much more than the median.", size=25, bold=True)


def _tile(plate: Plate, box: Box, value: str, *, fill: str, pattern: bool = False) -> None:
    if pattern:
        _hatched_rect(plate, box, fill=fill, spacing=17, cross=True)
    else:
        plate.draw.rounded_rectangle(box, radius=16, fill=fill, outline=INK, width=3)
    _center(plate, ((box[0] + box[2]) / 2, (box[1] + box[3]) / 2), value,
            size=38, bold=True, math_face=True)


def draw_prealgebra(plate: Plate) -> None:
    left = _panel(plate, (120, 235, 700, 790), "EXPRESSION")
    x0, y0, x1, _ = left
    for index in range(3):
        _tile(plate, (x0 + 30 + index * 135, y0 + 90, x0 + 135 + index * 135, y0 + 195),
              "x", fill=BLUE_LIGHT)
        if index < 2:
            _center(plate, (x0 + 150 + index * 135, y0 + 142), "+", size=30, bold=True)
    _center(plate, ((x0 + x1) / 2, y0 + 235), "+ 5", size=38, bold=True)
    _center(plate, ((x0 + x1) / 2, y0 + 300), "x + x + x + 5", size=34, bold=True)
    _center(plate, ((x0 + x1) / 2, y0 + 365), "3x + 5", size=43, bold=True, fill=BLUE)
    _center(plate, ((x0 + x1) / 2, y0 + 420), "same x in every card", size=23, fill=INK_SOFT)

    right = _panel(plate, (900, 235, 1480, 790), "SUBSTITUTE x = 4")
    rx0, ry0, rx1, _ = right
    for index in range(3):
        _tile(plate, (rx0 + 30 + index * 135, ry0 + 90, rx0 + 135 + index * 135, ry0 + 195),
              "4", fill=GOLD_LIGHT)
        if index < 2:
            _center(plate, (rx0 + 150 + index * 135, ry0 + 142), "+", size=30, bold=True)
    _center(plate, ((rx0 + rx1) / 2, ry0 + 235), "+ 5", size=38, bold=True)
    _center(plate, ((rx0 + rx1) / 2, ry0 + 300),
            "4 + 4 + 4 + 5 = 17", size=32, bold=True)
    _center(plate, ((rx0 + rx1) / 2, ry0 + 365),
            "12 + 5 = 17", size=41, bold=True, fill=GOLD)
    plate.arrow((735, 495), (865, 495), fill=TEAL, width=10, head=28)
    plate.label((800, 435), "replace every x", fill=TEAL)


def _function_step(plate: Plate, box: Box, rule: str, check: str, *, fill: str,
                   outline: str) -> None:
    plate.card(box, fill=fill, outline=outline, radius=16)
    cx = (box[0] + box[2]) / 2
    cy = (box[1] + box[3]) / 2
    _center(plate, (cx, cy - 16), rule, size=27, bold=True, math_face=True)
    _center(plate, (cx, cy + 20), check, size=20, bold=True, fill=outline, math_face=True)


def _function_value(plate: Plate, center: Point, value: str, *, fill: str) -> None:
    x, y = center
    plate.draw.rounded_rectangle((x - 50, y - 42, x + 50, y + 42), radius=15,
                                 fill=fill, outline=INK, width=3)
    _center(plate, center, value, size=43, bold=True, math_face=True)


def _function_composition_row(plate: Plate, box: Box, title: str, first_rule: str,
                              first_check: str, middle: str, second_rule: str,
                              second_check: str, result: str, equation: str,
                              *, first_fill: str, first_outline: str,
                              second_fill: str, second_outline: str) -> None:
    x0, y0, _, _ = _panel(plate, box, title)
    cy = y0 + 53
    _function_value(plate, (x0 + 56, cy), "3", fill=PAPER_LIGHT)
    plate.arrow((x0 + 115, cy), (x0 + 180, cy), fill=INK_SOFT, width=5, head=16)
    _function_step(plate, (x0 + 195, cy - 45, x0 + 430, cy + 45),
                   first_rule, first_check, fill=first_fill, outline=first_outline)
    plate.arrow((x0 + 445, cy), (x0 + 510, cy), fill=INK_SOFT, width=5, head=16)
    _function_value(plate, (x0 + 570, cy), middle, fill=PAPER_LIGHT)
    plate.arrow((x0 + 630, cy), (x0 + 695, cy), fill=INK_SOFT, width=5, head=16)
    _function_step(plate, (x0 + 710, cy - 45, x0 + 945, cy + 45),
                   second_rule, second_check, fill=second_fill, outline=second_outline)
    plate.arrow((x0 + 960, cy), (x0 + 1025, cy), fill=INK_SOFT, width=5, head=16)
    _function_value(plate, (x0 + 1085, cy), result, fill=GOLD_LIGHT)
    _center(plate, (x0 + 1195, cy), equation, size=27, bold=True, fill=PLUM,
            math_face=True)


def draw_functions(plate: Plate) -> None:
    _function_composition_row(
        plate, (120, 210, 1480, 475), "DO f, THEN g",
        "f(x) = 2x", "f(3) = 6", "6", "g(x) = x + 1", "g(6) = 7", "7",
        "g(f(3)) = 7", first_fill=BLUE_LIGHT, first_outline=BLUE,
        second_fill=CORAL_LIGHT, second_outline=CORAL,
    )
    _function_composition_row(
        plate, (120, 500, 1480, 765), "DO g, THEN f",
        "g(x) = x + 1", "g(3) = 4", "4", "f(x) = 2x", "f(4) = 8", "8",
        "f(g(3)) = 8", first_fill=CORAL_LIGHT, first_outline=CORAL,
        second_fill=BLUE_LIGHT, second_outline=BLUE,
    )
    plate.card((230, 795, 1370, 885), fill=PLUM_LIGHT, outline=PLUM, radius=18)
    _center(plate, (800, 825), "Same input and rules, different order: 7 ≠ 8", size=31, bold=True)
    _center(plate, (800, 862), "Function composition is not usually commutative.", size=24, bold=True,
            fill=PLUM)


def draw_linear(plate: Plate) -> None:
    equations = ("2x + 6 = x + 10", "x + 6 = 10", "x = 4")
    operations = ("START", "subtract x from both sides", "subtract 6 from both sides")
    fills = (BLUE_LIGHT, TEAL_LIGHT, GOLD_LIGHT)
    for index in range(3):
        x0 = 130 + index * 455
        box = (x0, 250, x0 + 400, 730)
        inner = _panel(plate, box, "BALANCE {}".format(index + 1))
        ix0, iy0, ix1, _ = inner
        plate.draw.line((ix0 + 35, iy0 + 155, ix1 - 35, iy0 + 155), fill=INK, width=6)
        plate.draw.polygon(((ix0 + 70, iy0 + 155), (ix1 - 70, iy0 + 155),
                           ((ix0 + ix1) / 2, iy0 + 235)), fill=hex_rgba(fills[index], 165), outline=INK)
        _center(plate, ((ix0 + ix1) / 2, iy0 + 90), equations[index], size=35, bold=True, math_face=True)
        plate.card((ix0 + 20, iy0 + 275, ix1 - 20, iy0 + 365), fill=fills[index],
                   outline=(BLUE, TEAL, GOLD)[index], radius=16)
        plate.wrapped_text((ix0 + 38, iy0 + 284, ix1 - 38, iy0 + 356),
                           operations[index], size=20, bold=True, line_gap=3)
        if index < 2:
            plate.arrow((box[2] + 10, 480), (box[2] + 43, 480), fill=INK_SOFT, width=6, head=16)
    plate.card((300, 775, 1300, 860), fill=PLUM_LIGHT, outline=PLUM, radius=18)
    _center(plate, (800, 817), "The same operation on both sides preserves equality.", size=30, bold=True)


def draw_slope(plate: Plate) -> None:
    # The ranges and plot dimensions use the same pixels per unit on both axes.
    graph = (155, 235, 455, 835)
    point = plate.axes(graph, x_range=(-0.25, 3.25), y_range=(-1.5, 5.5), grid_step=1)
    _plot(plate, point, lambda x: -2 * x + 5, -0.2, 3.2, fill=BLUE, width=8)
    a, b, corner = point(1, 3), point(3, -1), point(3, 3)
    plate.dot(a, 15, fill=BLUE_LIGHT)
    _diamond(plate, b, 17, fill=CORAL_LIGHT)
    plate.dashed_line(a, corner, fill=TEAL, width=7)
    plate.dashed_line(corner, b, fill=CORAL, width=7)
    plate.label(((a[0] + corner[0]) / 2, a[1] - 38), "run = +2", fill=TEAL)
    plate.label((corner[0] + 112, (corner[1] + b[1]) / 2), "rise = −4", fill=CORAL)
    plate.dot(point(0, 5), 13, fill=GOLD_LIGHT)
    plate.text((point(0, 5)[0] + 22, point(0, 5)[1]), "y-intercept 5", size=22, bold=True, fill=GOLD)
    right = _panel(plate, (700, 235, 1480, 835), "SLOPE")
    x0, y0, x1, _ = right
    _center(plate, ((x0 + x1) / 2, y0 + 75), "m = rise / run", size=38, bold=True, math_face=True)
    _center(plate, ((x0 + x1) / 2, y0 + 155), "m = −4 / 2 = −2", size=38, bold=True, fill=BLUE)
    _center(plate, ((x0 + x1) / 2, y0 + 230), "y = −2x + 5", size=39, bold=True, math_face=True)
    plate.card((x0 + 15, y0 + 310, x1 - 15, y0 + 445), fill=CORAL_LIGHT, outline=CORAL)
    plate.wrapped_text((x0 + 38, y0 + 322, x1 - 38, y0 + 432),
                       "A vertical line has zero run, so its slope is undefined.", size=24, bold=True)


def _system_panel(plate: Plate, box: Box, title: str, kind: str) -> None:
    x0, y0, x1, y1 = _panel(plate, box, title)
    graph = (x0 + 25, y0 + 25, x1 - 25, y0 + 320)
    point = plate.axes(graph, x_range=(-3, 3), y_range=(-3, 3), grid_step=1, labels=False)
    if kind == "one":
        _plot(plate, point, lambda x: 0.7 * x + 0.5, -3, 3, fill=BLUE, width=7)
        dashed = [point(-3, 2.2), point(3, -1.4)]
        _dashed_polyline(plate, dashed, fill=CORAL, width=7)
        intersection_x = -0.1 / 1.3
        intersection = point(intersection_x, 0.7 * intersection_x + 0.5)
        plate.dot(intersection, 14, fill=GOLD_LIGHT)
        _center(plate, ((x0 + x1) / 2, y0 + 365), "one shared point", size=24, bold=True)
    elif kind == "none":
        _plot(plate, point, lambda x: 0.6 * x + 1, -3, 3, fill=BLUE, width=7)
        _dashed_polyline(plate, [point(-3, -2), point(3, 1.6)], fill=CORAL, width=7)
        _center(plate, ((x0 + x1) / 2, y0 + 365), "parallel: no shared point", size=22, bold=True)
    else:
        _plot(plate, point, lambda x: -0.55 * x + 0.3, -3, 3, fill=BLUE, width=10)
        dashed = [point(-3, -0.55 * -3 + 0.3), point(3, -0.55 * 3 + 0.3)]
        _dashed_polyline(plate, dashed, fill=CORAL, width=5)
        _center(plate, ((x0 + x1) / 2, y0 + 365), "A and B overlap", size=24, bold=True)
    plate.text((x0 + 14, y0 + 412), "A — solid", size=20, bold=True, fill=BLUE)
    plate.text((x1 - 14, y0 + 412), "B -- dashed", size=20, bold=True, fill=CORAL, anchor="ra")


def draw_systems(plate: Plate) -> None:
    _system_panel(plate, (120, 220, 550, 830), "ONE SOLUTION", "one")
    _system_panel(plate, (585, 220, 1015, 830), "NO SOLUTION", "none")
    _system_panel(plate, (1050, 220, 1480, 830), "INFINITELY MANY", "many")


def draw_quadratics(plate: Plate) -> None:
    graph = (145, 245, 905, 825)
    point = plate.axes(graph, x_range=(0, 5), y_range=(-1, 7), grid_step=1)
    _plot(plate, point, lambda x: x * x - 5 * x + 6, 0, 5, fill=PLUM, width=8)
    for root, shape in ((2, "circle"), (3, "diamond")):
        if shape == "circle":
            plate.dot(point(root, 0), 16, fill=GOLD_LIGHT)
        else:
            _diamond(plate, point(root, 0), 18, fill=CORAL_LIGHT)
        plate.text((point(root, 0)[0], point(root, 0)[1] + 25), str(root), size=22, bold=True, anchor="ma")
    vertex = point(2.5, -0.25)
    plate.draw.rectangle((vertex[0] - 12, vertex[1] - 12, vertex[0] + 12, vertex[1] + 12),
                         fill=BLUE_LIGHT, outline=INK, width=3)
    plate.text((vertex[0], vertex[1] + 25), "vertex (2.5, −0.25)", size=21, bold=True, anchor="ma")
    right = _panel(plate, (950, 245, 1480, 825), "ONE QUADRATIC, MANY VIEWS")
    x0, y0, x1, _ = right
    lines = (
        ("standard", "x² − 5x + 6"),
        ("factored", "(x − 2)(x − 3)"),
        ("roots", "x = 2,  x = 3"),
        ("discriminant", "b² − 4ac = 1 > 0"),
    )
    for index, (label, value) in enumerate(lines):
        top = y0 + index * 92
        plate.text((x0 + 10, top + 18), label.upper(), size=18, bold=True, fill=INK_SOFT)
        plate.text((x0 + 10, top + 53), value, size=28, bold=True, math_face=True,
                   fill=(PLUM, BLUE, GOLD, CORAL)[index])
    plate.wrapped_text((x0 + 10, y0 + 395, x1 - 10, y0 + 500),
                       "Two real roots match two x-axis crossings.", size=25, bold=True)


def draw_polynomials(plate: Plate) -> None:
    graph = (145, 245, 900, 825)
    point = plate.axes(graph, x_range=(0, 4), y_range=(-7, 7), grid_step=1)
    cubic = lambda x: (x - 1) * (x - 2) * (x - 3)
    _plot(plate, point, cubic, 0, 4, fill=BLUE, width=8)
    shapes = ("circle", "square", "diamond")
    for root, shape in zip((1, 2, 3), shapes):
        px, py = point(root, 0)
        if shape == "circle":
            plate.dot((px, py), 15, fill=GOLD_LIGHT)
        elif shape == "square":
            plate.draw.rectangle((px - 15, py - 15, px + 15, py + 15),
                                 fill=TEAL_LIGHT, outline=INK, width=3)
        else:
            _diamond(plate, (px, py), 17, fill=CORAL_LIGHT)
        plate.text((px, py + 24), "root {}".format(root), size=20, bold=True, anchor="ma")
    right = _panel(plate, (950, 245, 1480, 825), "FACTORS CONTROL ZEROS")
    x0, y0, x1, _ = right
    _center(plate, ((x0 + x1) / 2, y0 + 72), "p(x) = (x−1)(x−2)(x−3)", size=31, bold=True, math_face=True)
    _center(plate, ((x0 + x1) / 2, y0 + 145), "= x³ − 6x² + 11x − 6", size=29, bold=True, math_face=True)
    plate.card((x0 + 20, y0 + 205, x1 - 20, y0 + 315), fill=TEAL_LIGHT, outline=TEAL)
    _center(plate, ((x0 + x1) / 2, y0 + 240), "degree 3", size=27, bold=True)
    _center(plate, ((x0 + x1) / 2, y0 + 282), "three simple zeros: 1, 2, 3", size=23)
    plate.card((x0 + 20, y0 + 345, x1 - 20, y0 + 465), fill=GOLD_LIGHT, outline=GOLD)
    _center(plate, ((x0 + x1) / 2, y0 + 385), "positive leading term", size=25, bold=True)
    _center(plate, ((x0 + x1) / 2, y0 + 425), "left end down; right end up", size=22)


def draw_euclid(plate: Plate) -> None:
    a, b, c, d = (190, 715), (690, 715), (455, 315), (930, 715)
    plate.polyline((a, b, c, a), fill=BLUE, width=8)
    plate.draw.line((b, d), fill=CORAL, width=8)
    for point, name, offset in ((a, "A", (-30, 20)), (b, "B", (-5, 28)),
                                (c, "C", (0, -28)), (d, "D", (20, 20))):
        plate.dot(point, 8, fill=INK)
        plate.text((point[0] + offset[0], point[1] + offset[1]), name, size=24, bold=True, anchor="mm")
    plate.text((285, 650), "angle A", size=24, bold=True, fill=BLUE)
    plate.text((510, 390), "angle C", size=24, bold=True, fill=BLUE)
    exterior_arc = []
    for degree in range(-118, -1, 4):
        radians = math.radians(degree)
        exterior_arc.append((b[0] + 88 * math.cos(radians), b[1] + 88 * math.sin(radians)))
    plate.polyline(exterior_arc, fill=CORAL, width=6)
    plate.text((705, 585), "exterior angle CBD", size=23, bold=True, fill=CORAL)
    proof = _panel(plate, (980, 230, 1480, 825), "PROOF CHAIN")
    x0, y0, x1, _ = proof
    statements = (
        ("1", "∠A + ∠B + ∠C = 180°", "triangle angle sum"),
        ("2", "∠B + ∠CBD = 180°", "straight line"),
        ("3", "∠CBD = ∠A + ∠C", "subtract angle B"),
    )
    for index, (step, statement, reason) in enumerate(statements):
        top = y0 + index * 130
        plate.label((x0 + 35, top + 45), step, fill=(BLUE, TEAL, CORAL)[index])
        plate.text((x0 + 78, top + 25), statement, size=24, bold=True, math_face=True)
        plate.text((x0 + 78, top + 65), "reason: " + reason, size=20, fill=INK_SOFT)
        if index < 2:
            plate.arrow((x0 + 35, top + 83), (x0 + 35, top + 117), fill=INK_SOFT, width=4, head=13)
    plate.card((x0 + 8, y0 + 420, x1 - 8, y0 + 500), fill=GOLD_LIGHT, outline=GOLD)
    _center(plate, ((x0 + x1) / 2, y0 + 460), "givens, reasons, conclusion", size=23, bold=True)


def draw_trig(plate: Plate) -> None:
    center, radius = (470, 520), 255
    plate.draw.ellipse((center[0] - radius, center[1] - radius,
                       center[0] + radius, center[1] + radius),
                      fill=hex_rgba(BLUE_LIGHT, 40), outline=BLUE, width=7)
    plate.double_arrow((center[0] - radius - 35, center[1]),
                       (center[0] + radius + 35, center[1]), fill=INK, width=4)
    plate.double_arrow((center[0], center[1] + radius + 35),
                       (center[0], center[1] - radius - 35), fill=INK, width=4)
    angle = math.radians(150)
    endpoint = (center[0] + radius * math.cos(angle), center[1] - radius * math.sin(angle))
    plate.arrow(center, endpoint, fill=CORAL, width=9, head=24)
    plate.dashed_line(endpoint, (endpoint[0], center[1]), fill=BLUE, width=5)
    plate.dashed_line(endpoint, (center[0], endpoint[1]), fill=TEAL, width=5)
    _diamond(plate, endpoint, 18, fill=CORAL_LIGHT)
    plate.text((endpoint[0] - 15, endpoint[1] - 35), "P at 150°", size=24, bold=True, anchor="ms")
    arc_points = []
    for degree in range(0, 151, 5):
        radians = math.radians(degree)
        arc_points.append((center[0] + 75 * math.cos(radians), center[1] - 75 * math.sin(radians)))
    plate.polyline(arc_points, fill=GOLD, width=5)
    plate.text((center[0] - 45, center[1] - 88), "150°", size=23, bold=True, fill=GOLD)
    plate.text((endpoint[0], center[1] + 24), "cos θ = −√3/2", size=22, bold=True, fill=BLUE, anchor="ma")
    plate.text((center[0] + 20, endpoint[1]), "sin θ = 1/2", size=22, bold=True, fill=TEAL)
    right = _panel(plate, (900, 230, 1480, 825), "UNIT-CIRCLE COORDINATES")
    x0, y0, x1, _ = right
    _center(plate, ((x0 + x1) / 2, y0 + 80), "P = (cos θ, sin θ)", size=36, bold=True, math_face=True)
    _center(plate, ((x0 + x1) / 2, y0 + 165), "P = (−√3/2, 1/2)", size=34, bold=True, fill=CORAL, math_face=True)
    plate.card((x0 + 20, y0 + 230, x1 - 20, y0 + 355), fill=PLUM_LIGHT, outline=PLUM)
    _center(plate, ((x0 + x1) / 2, y0 + 270), "Quadrant II", size=29, bold=True)
    _center(plate, ((x0 + x1) / 2, y0 + 315), "cosine −   sine +", size=25, bold=True)
    _center(plate, ((x0 + x1) / 2, y0 + 425), "radius = 1", size=31, bold=True, fill=BLUE)


def draw_expo_logs(plate: Plate) -> None:
    # Equal horizontal and vertical scales make inverse reflection across y = x literal.
    graph = (145, 235, 745, 835)
    point = plate.axes(graph, x_range=(-1, 9), y_range=(-1, 9), grid_step=1)
    _plot(plate, point, lambda x: 2 ** x, -1, math.log(9, 2), fill=BLUE, width=7)
    # Start where the curve enters the visible y-range; do not draw through the frame.
    _plot(plate, point, lambda x: math.log(x, 2), 0.5, 9, fill=CORAL, width=7)
    plate.dashed_line(point(-1, -1), point(9, 9), fill=INK_SOFT, width=4)
    plate.text(point(5.2, 5.4), "y = x (mirror)", size=20, bold=True, fill=INK_SOFT)
    plate.dot(point(3, 8), 15, fill=BLUE_LIGHT)
    _diamond(plate, point(8, 3), 17, fill=CORAL_LIGHT)
    plate.text((point(3, 8)[0] + 18, point(3, 8)[1] - 7), "(3, 8)", size=22, bold=True, fill=BLUE)
    plate.text((point(8, 3)[0] - 18, point(8, 3)[1] + 10), "(8, 3)", size=22,
               bold=True, fill=CORAL, anchor="ra")
    right = _panel(plate, (800, 235, 1480, 835), "INVERSE OPERATIONS")
    x0, y0, x1, _ = right
    _center(plate, ((x0 + x1) / 2, y0 + 65), "2³ = 8", size=43, bold=True, fill=BLUE)
    plate.double_arrow(((x0 + x1) / 2, y0 + 115), ((x0 + x1) / 2, y0 + 175), fill=TEAL, width=6)
    _center(plate, ((x0 + x1) / 2, y0 + 225), "log₂(8) = 3", size=41, bold=True, fill=CORAL, math_face=True)
    plate.card((x0 + 20, y0 + 290, x1 - 20, y0 + 405), fill=GOLD_LIGHT, outline=GOLD)
    _center(plate, ((x0 + x1) / 2, y0 + 330), "input and output swap", size=25, bold=True)
    _center(plate, ((x0 + x1) / 2, y0 + 370), "(3, 8) swaps with (8, 3)", size=25, bold=True)
    _center(plate, ((x0 + x1) / 2, y0 + 465), "For real logs: base > 0, base ≠ 1, input > 0.",
            size=20, bold=True)


def draw_sequences(plate: Plate) -> None:
    left = _panel(plate, (120, 220, 980, 835), "PARTIAL SUMS APPROACH 2")
    x0, y0, x1, _ = left
    bar_left, bar_width = x0 + 70, x1 - x0 - 135
    scale = bar_width / 2
    partials = (1, 1.5, 1.75, 1.875)
    terms = (1, 0.5, 0.25, 0.125)
    colors = (BLUE_LIGHT, TEAL_LIGHT, GOLD_LIGHT, CORAL_LIGHT)
    target_x = bar_left + 2 * scale
    for row, partial in enumerate(partials):
        y = y0 + 55 + row * 105
        plate.text((bar_left - 18, y + 27), "S{}".format(row + 1), size=23, bold=True, anchor="ra")
        cursor = bar_left
        for term_index, term in enumerate(terms[:row + 1]):
            width = term * scale
            _hatched_rect(plate, (cursor, y, cursor + width, y + 56), fill=colors[term_index],
                          spacing=14 + term_index * 3, cross=term_index % 2 == 1)
            cursor += width
        plate.text((target_x + 18, y + 28), str(partial), size=21, bold=True, anchor="lm")
    plate.dashed_line((target_x, y0 + 30), (target_x, y0 + 455), fill=PLUM, width=6)
    plate.label((target_x, y0 + 495), "limit 2", fill=PLUM)

    right = _panel(plate, (1025, 220, 1480, 835), "GEOMETRIC SERIES")
    x0, y0, x1, _ = right
    _center(plate, ((x0 + x1) / 2, y0 + 60), "1 + 1/2 + 1/4 + ⋯", size=33, bold=True, math_face=True)
    _center(plate, ((x0 + x1) / 2, y0 + 140), "ratio r = 1/2", size=31, bold=True, fill=TEAL)
    plate.card((x0 + 20, y0 + 205, x1 - 20, y0 + 315), fill=GOLD_LIGHT, outline=GOLD)
    _center(plate, ((x0 + x1) / 2, y0 + 245), "sum = a / (1 − r)", size=27, bold=True, math_face=True)
    _center(plate, ((x0 + x1) / 2, y0 + 285), "= 1 / (1 − 1/2) = 2", size=25, bold=True)
    plate.card((x0 + 20, y0 + 360, x1 - 20, y0 + 475), fill=CORAL_LIGHT, outline=CORAL)
    plate.wrapped_text((x0 + 42, y0 + 372, x1 - 42, y0 + 462),
                       "Convergence requires |r| < 1.", size=27, bold=True)


def _branch(plate: Plate, start: Point, end: Point, label: str, *, fill: str,
            dashed: bool = False, selected: bool = False) -> None:
    if selected:
        plate.draw.line((start[0], start[1] - 4, end[0], end[1] - 4), fill=GOLD, width=14)
    if dashed:
        plate.dashed_line(start, end, fill=fill, width=7)
    else:
        plate.draw.line((*start, *end), fill=fill, width=7)
    midpoint = ((start[0] + end[0]) / 2, (start[1] + end[1]) / 2 - 22)
    plate.label(midpoint, label, size=20, fill=fill)


def draw_probability(plate: Plate) -> None:
    root = (230, 520)
    red_first, blue_first = (610, 340), (610, 690)
    endpoints = ((1040, 250), (1040, 430), (1040, 610), (1040, 790))
    plate.dot(root, 24, fill=PAPER_LIGHT)
    plate.text((root[0], root[1] + 45), "bag: 3 R, 2 B", size=23, bold=True, anchor="ma")
    _branch(plate, root, red_first, "R: 3/5", fill=CORAL, selected=True)
    _branch(plate, root, blue_first, "B: 2/5", fill=BLUE, dashed=True)
    _branch(plate, red_first, endpoints[0], "R: 2/4", fill=CORAL, selected=True)
    _branch(plate, red_first, endpoints[1], "B: 2/4", fill=BLUE, dashed=True)
    _branch(plate, blue_first, endpoints[2], "R: 3/4", fill=CORAL)
    _branch(plate, blue_first, endpoints[3], "B: 1/4", fill=BLUE, dashed=True)
    for node, label, fill, shape in ((red_first, "R removed", CORAL_LIGHT, "diamond"),
                                     (blue_first, "B removed", BLUE_LIGHT, "circle")):
        if shape == "diamond":
            _diamond(plate, node, 23, fill=fill)
        else:
            plate.dot(node, 23, fill=fill)
        plate.text((node[0] + 36, node[1]), label, size=21, bold=True, anchor="lm")
    labels = ("RR", "RB", "BR", "BB")
    for endpoint, label in zip(endpoints, labels):
        plate.draw.rounded_rectangle((endpoint[0] - 35, endpoint[1] - 25,
                                     endpoint[0] + 35, endpoint[1] + 25), radius=12,
                                    fill=PAPER_LIGHT, outline=GOLD if label == "RR" else INK, width=5)
        _center(plate, endpoint, label, size=22, bold=True)
    result = _panel(plate, (1120, 235, 1480, 835), "HIGHLIGHTED PATH")
    x0, y0, x1, _ = result
    _center(plate, ((x0 + x1) / 2, y0 + 75), "R then R", size=31, bold=True, fill=CORAL)
    _center(plate, ((x0 + x1) / 2, y0 + 155), "3/5 × 2/4", size=36, bold=True, math_face=True)
    _center(plate, ((x0 + x1) / 2, y0 + 225), "= 3/10", size=45, bold=True, fill=GOLD)
    plate.wrapped_text((x0 + 25, y0 + 285, x1 - 25, y0 + 455),
                       "Without replacement, the second denominator and numerator can change.",
                       size=20, bold=True)


def _dot_plot(plate: Plate, box: Box, values: Iterable[int], *, title: str, sd: str,
              fill: str, shape: str) -> None:
    x0, y0, x1, y1 = _panel(plate, box, title)
    baseline = y0 + 265
    left, right = x0 + 35, x1 - 35
    map_x = lambda value: left + value / 20 * (right - left)
    plate.draw.line((left, baseline, right, baseline), fill=INK, width=5)
    for value in range(0, 21, 2):
        x = map_x(value)
        plate.draw.line((x, baseline - 10, x, baseline + 10), fill=INK, width=2)
        _center(plate, (x, baseline + 30), str(value), size=16)
    stacks: Dict[int, int] = {}
    for value in values:
        level = stacks.get(value, 0)
        stacks[value] = level + 1
        center = (map_x(value), baseline - 38 - level * 42)
        if shape == "diamond":
            _diamond(plate, center, 15, fill=fill)
        else:
            plate.dot(center, 15, fill=fill)
    mean_x = map_x(10)
    plate.dashed_line((mean_x, baseline + 48), (mean_x, baseline + 135), fill=PLUM, width=5)
    plate.label((mean_x, baseline + 165), "mean = 10", size=20, fill=PLUM)
    plate.text(((x0 + x1) / 2, y0 + 485), sd, size=29, bold=True, fill=fill, anchor="mm")


def draw_statistics(plate: Plate) -> None:
    _dot_plot(plate, (120, 225, 775, 825), (9, 10, 10, 11), title="TIGHT CLUSTER: 9, 10, 10, 11",
              sd="standard deviation ≈ 0.7", fill=BLUE, shape="circle")
    _dot_plot(plate, (825, 225, 1480, 825), (2, 8, 12, 18), title="WIDER SPREAD: 2, 8, 12, 18",
              sd="standard deviation ≈ 5.8", fill=CORAL, shape="diamond")
    plate.label((800, 855), "same mean, different spread", fill=TEAL)


def draw_vectors(plate: Plate) -> None:
    origin, north, result = (270, 785), (270, 345), (600, 345)
    plate.arrow(origin, north, fill=BLUE, width=12, head=30)
    plate.arrow(north, result, fill=CORAL, width=12, head=30)
    plate.arrow(origin, result, fill=TEAL, width=14, head=33)
    plate.dashed_line(origin, (600, 785), fill=INK_SOFT, width=4)
    plate.dashed_line((600, 785), result, fill=INK_SOFT, width=4)
    plate.text((origin[0] - 28, (origin[1] + north[1]) / 2), "8 north", size=29, bold=True,
               fill=BLUE, anchor="rm")
    plate.text(((north[0] + result[0]) / 2, north[1] - 28), "6 east", size=29, bold=True,
               fill=CORAL, anchor="ms")
    plate.text(((origin[0] + result[0]) / 2 + 25, (origin[1] + result[1]) / 2),
               "resultant 10", size=30, bold=True, fill=TEAL)
    for point, label, shape in ((origin, "START", "circle"), (north, "TURN", "square"),
                                (result, "END", "diamond")):
        if shape == "circle":
            plate.dot(point, 14, fill=PAPER_LIGHT)
        elif shape == "square":
            plate.draw.rectangle((point[0] - 14, point[1] - 14, point[0] + 14, point[1] + 14),
                                 fill=GOLD_LIGHT, outline=INK, width=3)
        else:
            _diamond(plate, point, 16, fill=PLUM_LIGHT)
        plate.text((point[0], point[1] + 26), label, size=18, bold=True, anchor="ma")
    right = _panel(plate, (850, 240, 1480, 820), "ADD COMPONENTS")
    x0, y0, x1, _ = right
    _center(plate, ((x0 + x1) / 2, y0 + 70), "⟨6, 0⟩ + ⟨0, 8⟩", size=39, bold=True, math_face=True)
    _center(plate, ((x0 + x1) / 2, y0 + 145), "= ⟨6, 8⟩", size=43, bold=True, fill=TEAL, math_face=True)
    plate.card((x0 + 25, y0 + 210, x1 - 25, y0 + 335), fill=GOLD_LIGHT, outline=GOLD)
    _center(plate, ((x0 + x1) / 2, y0 + 250), "magnitude = √(6² + 8²)", size=29, bold=True, math_face=True)
    _center(plate, ((x0 + x1) / 2, y0 + 295), "= 10", size=35, bold=True)
    plate.wrapped_text((x0 + 35, y0 + 380, x1 - 35, y0 + 490),
                       "Direction matters: vector magnitudes do not always simply add.", size=25, bold=True)


def draw_precalc(plate: Plate) -> None:
    graph = (140, 240, 930, 825)
    point = plate.axes(graph, x_range=(0, 4), y_range=(0, 6), grid_step=1)
    # The graph is y = x + 2 with the point at x = 2 removed.
    _plot(plate, point, lambda x: x + 2, 0, 1.93, fill=BLUE, width=8)
    _plot(plate, point, lambda x: x + 2, 2.07, 4, fill=BLUE, width=8)
    hole = point(2, 4)
    plate.draw.ellipse((hole[0] - 18, hole[1] - 18, hole[0] + 18, hole[1] + 18),
                      fill=PAPER_LIGHT, outline=CORAL, width=7)
    value = point(2, 2)
    plate.dot(value, 16, fill=PLUM_LIGHT)
    plate.text((value[0] + 25, value[1]), "f(2) = 2", size=22, bold=True, fill=PLUM)
    plate.text((hole[0] + 25, hole[1] - 18), "open point (2, 4)", size=22, bold=True, fill=CORAL)
    plate.arrow(point(0.9, 2.9), point(1.75, 3.75), fill=TEAL, width=7, head=20)
    plate.arrow(point(3.1, 5.1), point(2.25, 4.25), fill=GOLD, width=7, head=20)
    plate.label((hole[0], hole[1] - 90), "both sides approach 4", fill=TEAL)
    right = _panel(plate, (980, 240, 1480, 825), "NEARBY, NOT AT")
    x0, y0, x1, _ = right
    _center(plate, ((x0 + x1) / 2, y0 + 72), "lim   f(x) = 4", size=42, bold=True, math_face=True)
    _center(plate, ((x0 + x1) / 2 - 10, y0 + 108), "x→2", size=21, bold=True, math_face=True)
    plate.card((x0 + 20, y0 + 165, x1 - 20, y0 + 295), fill=BLUE_LIGHT, outline=BLUE)
    _center(plate, ((x0 + x1) / 2, y0 + 205), "left-hand approach = 4", size=24, bold=True)
    _center(plate, ((x0 + x1) / 2, y0 + 250), "right-hand approach = 4", size=24, bold=True)
    plate.card((x0 + 20, y0 + 335, x1 - 20, y0 + 455), fill=CORAL_LIGHT, outline=CORAL)
    plate.wrapped_text((x0 + 42, y0 + 345, x1 - 42, y0 + 445),
                       "The limit can exist even when f(2) is different or undefined.", size=24, bold=True)


def draw_complex(plate: Plate) -> None:
    # A square plotting box is required for distances and rotations on the Argand plane.
    graph = (140, 235, 740, 835)
    point = plate.axes(graph, x_range=(-2.2, 2.2), y_range=(-2.2, 2.2), grid_step=1, labels=False)
    center = point(0, 0)
    # The axes use equal visual scales, so this is the radius corresponding to |z| = sqrt(2).
    radius = abs(point(math.sqrt(2), 0)[0] - center[0])
    plate.draw.ellipse((center[0] - radius, center[1] - radius,
                       center[0] + radius, center[1] + radius),
                      fill=hex_rgba(BLUE_LIGHT, 32), outline=hex_rgba(BLUE, 150), width=5)
    z, iz = point(1, 1), point(-1, 1)
    plate.arrow(center, z, fill=BLUE, width=11, head=27)
    plate.arrow(center, iz, fill=CORAL, width=11, head=27)
    plate.dot(z, 16, fill=BLUE_LIGHT)
    _diamond(plate, iz, 18, fill=CORAL_LIGHT)
    plate.text((z[0] + 22, z[1] - 10), "z = 1 + i", size=24, bold=True, fill=BLUE)
    plate.text((iz[0] - 22, iz[1] - 10), "iz = −1 + i", size=24, bold=True, fill=CORAL, anchor="ra")
    arc = []
    for degree in range(45, 136, 5):
        radians = math.radians(degree)
        arc.append((center[0] + radius * 0.62 * math.cos(radians),
                    center[1] - radius * 0.62 * math.sin(radians)))
    plate.polyline(arc, fill=GOLD, width=8)
    if len(arc) >= 2:
        plate.arrow(arc[-2], arc[-1], fill=GOLD, width=8, head=22)
    plate.label((center[0], center[1] - radius * 0.72), "+90°", fill=GOLD)
    plate.text((graph[2] - 14, center[1] + 24), "real axis", size=21, bold=True, anchor="ra")
    plate.text((center[0] + 20, graph[1] + 18), "imaginary axis", size=21, bold=True)
    right = _panel(plate, (790, 235, 1480, 835), "MULTIPLY BY i")
    x0, y0, x1, _ = right
    _center(plate, ((x0 + x1) / 2, y0 + 65), "i(1 + i)", size=41, bold=True, math_face=True)
    _center(plate, ((x0 + x1) / 2, y0 + 130), "= i + i²", size=38, bold=True, math_face=True)
    _center(plate, ((x0 + x1) / 2, y0 + 195), "= −1 + i", size=40, bold=True, fill=CORAL, math_face=True)
    plate.card((x0 + 20, y0 + 260, x1 - 20, y0 + 380), fill=TEAL_LIGHT, outline=TEAL)
    _center(plate, ((x0 + x1) / 2, y0 + 300), "modulus stays √2", size=26, bold=True)
    _center(plate, ((x0 + x1) / 2, y0 + 345), "argument adds 90°", size=26, bold=True)
    plate.wrapped_text((x0 + 25, y0 + 420, x1 - 25, y0 + 500),
                       "Complex multiplication multiplies moduli and adds their directed arguments.", size=23, bold=True)


def _spec(node_id: str, title: str, stage: int, plate_id: str, alt: str, caption: str,
          draw: Callable[[Plate], None]) -> Spec:
    return {
        "id": node_id,
        "title": title,
        "stage": stage,
        "plate_id": plate_id,
        "alt": alt,
        "caption": caption,
        "draw": draw,
    }


SPECS: Dict[str, Spec] = {
    "math.2.decimals": _spec(
        "math.2.decimals", "Decimals", 2, "decimal-place-value-plate",
        "A place-value chart and number line show that 0.700 is greater than 0.089.",
        "Compare decimals from the highest place value; trailing zeros do not change the number.",
        draw_decimals,
    ),
    "math.2.percent": _spec(
        "math.2.percent", "Percentages", 2, "percent-equivalence-plate",
        "Three-fifths, 0.60, and 60 percent are shown as equivalent parts of one whole.",
        "Percent means per hundred; the whole being measured still matters.", draw_percent,
    ),
    "math.2.negatives": _spec(
        "math.2.negatives", "Negative Numbers", 2, "integer-number-line-plate",
        "A counter moves seven units left from negative two to negative nine on a number line.",
        "Numbers farther right are greater; adding and subtracting are directed moves.", draw_negatives,
    ),
    "math.2.order-ops": _spec(
        "math.2.order-ops", "Order of Operations", 2, "operation-order-plate",
        "An expression is evaluated with division and multiplication from left to right before addition.",
        "Equal-priority operations are handled left to right; brackets can change the order.", draw_order_ops,
    ),
    "math.2.primes": _spec(
        "math.2.primes", "Primes and Factors", 2, "factor-array-plate",
        "Twelve forms several rectangular arrays, thirteen only one factor pair, and one has only one divisor.",
        "A prime has exactly two distinct positive divisors.", draw_primes,
    ),
    "math.2.ratio": _spec(
        "math.2.ratio", "Ratio and Proportion", 2, "ratio-scale-plate",
        "A two-to-three mixture scales to six-to-nine by multiplying both parts by three.",
        "Equivalent ratios multiply or divide every part by the same factor.", draw_ratio,
    ),
    "math.2.geometry": _spec(
        "math.2.geometry", "Area, Perimeter and Volume", 2, "measurement-dimensions-plate",
        "Two shapes share a perimeter but have different areas, beside a cuboid made from 24 unit cubes.",
        "Length uses units, area square units, and volume cubic units.", draw_geometry,
    ),
    "math.2.exponents": _spec(
        "math.2.exponents", "Powers", 2, "powers-expanded-plate",
        "Four cubed is expanded as three factors of four, giving sixty-four.",
        "The exponent counts copies of the base in repeated multiplication.", draw_exponents,
    ),
    "math.2.coordinates": _spec(
        "math.2.coordinates", "The Coordinate Plane", 2, "coordinate-plane-plate",
        "A path moves left three and up two to plot negative three, two in Quadrant Two.",
        "Read x first, then y; points on an axis are not inside a quadrant.", draw_coordinates,
    ),
    "math.2.data": _spec(
        "math.2.data", "Data and Averages", 2, "averages-outlier-plate",
        "Four scores cluster near six while an outlier at sixty-eight pulls the mean to eighteen; the median stays six.",
        "Outliers can move the mean much more than the median.", draw_data,
    ),
    "math.2.prealgebra": _spec(
        "math.2.prealgebra", "Letters for Numbers", 2, "variable-substitution-plate",
        "Three plain x cards become three plain four cards; four plus four plus four plus five is then combined as twelve plus five to make seventeen.",
        "Substitution replaces every occurrence of a variable with the same value before simplifying.", draw_prealgebra,
    ),
    "math.3.functions": _spec(
        "math.3.functions", "Functions", 3, "composition-order-check-plate",
        "Two checkable function chains start at three: applying f of x equals two x before g of x equals x plus one gives seven, while reversing the order gives eight.",
        "Composition depends on order: g of f of three is seven, but f of g of three is eight, so composition is not usually commutative.",
        draw_functions,
    ),
    "math.3.linear": _spec(
        "math.3.linear", "Linear Equations", 3, "linear-balance-plate",
        "A balanced equation is simplified by removing equal quantities from both sides until x equals four.",
        "Equivalent operations preserve the solution because both sides remain equal.", draw_linear,
    ),
    "math.3.slope": _spec(
        "math.3.slope", "Slope and Lines", 3, "slope-rise-run-plate",
        "A line falls four units over a run of two, giving slope negative two, and crosses the y-axis at five.",
        "Slope is vertical change divided by horizontal change; a vertical line has undefined slope.", draw_slope,
    ),
    "math.3.systems": _spec(
        "math.3.systems", "Systems of Equations", 3, "systems-solution-types-plate",
        "Three systems show one intersection, no intersection, and two coincident lines.",
        "A shared point solves both equations; systems may have one, no, or infinitely many solutions.", draw_systems,
    ),
    "math.3.quadratics": _spec(
        "math.3.quadratics", "Quadratic Equations", 3, "quadratic-forms-plate",
        "A parabola crosses the x-axis at two and three, matching its two linear factors.",
        "Factors, roots, intercepts, vertex, and discriminant describe the same quadratic.", draw_quadratics,
    ),
    "math.3.polynomials": _spec(
        "math.3.polynomials", "Polynomials", 3, "polynomial-roots-plate",
        "A factored cubic and its graph share zeros at one, two, and three.",
        "Factors locate zeros; degree, leading sign, and multiplicity control graph behavior.", draw_polynomials,
    ),
    "math.3.euclid": _spec(
        "math.3.euclid", "Euclidean Geometry and Proof", 3, "exterior-angle-proof-plate",
        "A triangle's exterior-angle theorem is justified by two angle sums of 180 degrees.",
        "A proof links givens to a conclusion through established definitions and theorems.", draw_euclid,
    ),
    "math.3.trig": _spec(
        "math.3.trig", "Trigonometry", 3, "unit-circle-trig-plate",
        "A point at 150 degrees on the unit circle has negative cosine and positive sine.",
        "Cosine is the horizontal coordinate and sine the vertical coordinate on the unit circle.", draw_trig,
    ),
    "math.3.expo-logs": _spec(
        "math.3.expo-logs", "Exponentials and Logarithms", 3, "exponential-log-inverses-plate",
        "Base-two exponential and logarithm graphs mirror each other, swapping three-eight and eight-three.",
        "A logarithm returns the exponent, so it reverses exponentiation.", draw_expo_logs,
    ),
    "math.3.sequences": _spec(
        "math.3.sequences", "Sequences and Series", 3, "geometric-series-plate",
        "Successively smaller geometric terms fill a bar toward, but not past, a total of two.",
        "An infinite geometric series converges only when the ratio's absolute value is below one.", draw_sequences,
    ),
    "math.3.probability": _spec(
        "math.3.probability", "Probability", 3, "probability-tree-plate",
        "A two-draw tree shows how removing the first marble changes the second probability.",
        "Without replacement, later chances depend on earlier outcomes; replacement restores independence.", draw_probability,
    ),
    "math.3.statistics": _spec(
        "math.3.statistics", "Statistics", 3, "statistics-spread-plate",
        "Two distributions share a mean, but one has values much farther from it and a larger standard deviation.",
        "Centre and spread describe different features; neither alone tells the whole distribution.", draw_statistics,
    ),
    "math.3.vectors": _spec(
        "math.3.vectors", "Vectors", 3, "vector-resultant-plate",
        "Perpendicular north and east velocity vectors combine into a ten-unit diagonal resultant.",
        "Vectors add component by component; direction determines whether magnitudes combine, cancel, or form a right triangle.",
        draw_vectors,
    ),
    "math.3.precalc": _spec(
        "math.3.precalc", "Limits: a First Look", 3, "removable-limit-plate",
        "A graph approaches height four from both sides while the function value at x equals two is shown at height two.",
        "A limit describes nearby values and can exist even when the function value is different or undefined.", draw_precalc,
    ),
    "math.4.complex": _spec(
        "math.4.complex", "Complex Numbers and Beyond", 3, "complex-rotation-plate",
        "Multiplying one plus i by i rotates its point ninety degrees counterclockwise without changing its distance from the origin.",
        "Complex multiplication multiplies moduli and adds their directed arguments.", draw_complex,
    ),
}


_EXPECTED_IDS = {
    "math.2.decimals", "math.2.percent", "math.2.negatives", "math.2.order-ops",
    "math.2.primes", "math.2.ratio", "math.2.geometry", "math.2.exponents",
    "math.2.coordinates", "math.2.data", "math.2.prealgebra",
    "math.3.functions", "math.3.linear", "math.3.slope", "math.3.systems",
    "math.3.quadratics", "math.3.polynomials", "math.3.euclid", "math.3.trig",
    "math.3.expo-logs", "math.3.sequences", "math.3.probability",
    "math.3.statistics", "math.3.vectors", "math.3.precalc", "math.4.complex",
}

validate_specs(SPECS, _EXPECTED_IDS)


__all__ = ["SPECS"]
