"""Deterministic Seedling and Sprout mathematics illustration plates.

The drawings in this module deliberately encode quantities with geometry,
labels, and texture as well as colour.  That keeps every comparison, array,
measurement, clock position, and fraction partition mathematically legible.
"""

from __future__ import annotations

import math
from typing import Dict, Iterable, Tuple

from .core import (
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
    INK,
    INK_SOFT,
    PAPER,
    PAPER_LIGHT,
    PLUM,
    PLUM_LIGHT,
    TEAL,
    TEAL_LIGHT,
    Plate,
    font,
    hex_rgba,
    mix,
)


Point = Tuple[float, float]


def _counter(
    plate: Plate,
    center: Point,
    *,
    radius: int = 24,
    fill: str = TEAL_LIGHT,
    outline: str = TEAL,
    mark: str | None = None,
) -> None:
    """Draw a tactile counter, optionally with a non-colour identifying mark."""

    plate.dot(center, radius, fill=fill, outline=outline, width=4)
    plate.draw.ellipse(
        (
            center[0] - radius + 7,
            center[1] - radius + 7,
            center[0] + radius - 7,
            center[1] + radius - 7,
        ),
        outline=hex_rgba(PAPER_LIGHT, 180),
        width=2,
    )
    if mark is not None:
        plate.text(center, mark, size=max(18, radius - 2), bold=True, anchor="mm")


def _section_heading(plate: Plate, xy: Point, value: str, *, fill: str) -> None:
    plate.label(xy, value, size=22, fill=fill)


def _hatch_rect(
    plate: Plate,
    box: Tuple[int, int, int, int],
    *,
    fill: str,
) -> None:
    """Add a clipped, repeated slash texture to a rectangular region."""

    x0, y0, x1, y1 = box
    for y in range(y0 + 14, y1 - 7, 28):
        for x in range(x0 + 12, x1 - 7, 28):
            end_x = min(x + 13, x1 - 7)
            end_y = min(y + 13, y1 - 7)
            plate.draw.line((x, y, end_x, end_y), fill=fill, width=4)


def _ten_frame(
    plate: Plate,
    origin: Point,
    *,
    filled: int,
    label: str,
) -> None:
    """Draw an exact 2-by-5 ten-frame, filled in row-major order."""

    x0, y0 = origin
    cell_w, cell_h = 102, 112
    outer = (x0, y0, x0 + 5 * cell_w, y0 + 2 * cell_h)
    plate.draw.rounded_rectangle(
        outer,
        radius=16,
        fill=hex_rgba(PAPER_LIGHT, 230),
        outline=INK,
        width=5,
    )
    index = 0
    for row in range(2):
        for column in range(5):
            left = x0 + column * cell_w
            top = y0 + row * cell_h
            if column:
                plate.draw.line((left, y0, left, y0 + 2 * cell_h), fill=INK_SOFT, width=3)
            if row:
                plate.draw.line((x0, top, x0 + 5 * cell_w, top), fill=INK_SOFT, width=3)
            if index < filled:
                _counter(
                    plate,
                    (left + cell_w / 2, top + cell_h / 2),
                    radius=32,
                    fill=GOLD_LIGHT,
                    outline=GOLD,
                )
            index += 1
    plate.text((x0 + 2.5 * cell_w, y0 + 2 * cell_h + 38), label, size=28, bold=True, anchor="ma")


def _leaf(plate: Plate, center: Point) -> None:
    """Draw one countable leaf with outline and central vein."""

    x, y = center
    plate.draw.polygon(
        ((x, y - 24), (x + 21, y), (x, y + 24), (x - 21, y)),
        fill=GREEN_LIGHT,
        outline=GREEN,
    )
    plate.draw.line((x, y - 17, x, y + 17), fill=GREEN, width=3)
    plate.draw.line((x, y + 24, x + 10, y + 34), fill=GREEN, width=3)


def draw_compare(plate: Plate) -> None:
    """Pair five counters with five of seven and expose two unmatched extras."""

    x0, _, x1, _ = CONTENT
    plate.card((120, 208, 1480, 866), fill=hex_rgba(PAPER_LIGHT, 232))
    _section_heading(plate, (800, 244), "PAIR ONE-TO-ONE", fill=TEAL)

    plate.text((190, 352), "5", size=46, bold=True, anchor="mm")
    plate.text((190, 650), "7", size=46, bold=True, anchor="mm")
    plate.text((190, 401), "objects", size=22, fill=INK_SOFT, anchor="mm")
    plate.text((190, 699), "objects", size=22, fill=INK_SOFT, anchor="mm")

    centers = [350, 520, 690, 860, 1030, 1200, 1370]
    for pair_number, x in enumerate(centers[:5], start=1):
        plate.dashed_line((x, 392), (x, 600), fill=GRID, width=4, dash=13, gap=10)
        _counter(plate, (x, 352), radius=34, fill=BLUE_LIGHT, outline=BLUE, mark=str(pair_number))
        _counter(plate, (x, 650), radius=34, fill=BLUE_LIGHT, outline=BLUE, mark=str(pair_number))

    for x in centers[5:]:
        _counter(plate, (x, 650), radius=34, fill=GOLD_LIGHT, outline=GOLD, mark="+")

    plate.draw.line((1148, 725, 1422, 725), fill=GOLD, width=5)
    plate.draw.line((1148, 711, 1148, 739), fill=GOLD, width=5)
    plate.draw.line((1422, 711, 1422, 739), fill=GOLD, width=5)
    plate.text((1285, 760), "2 unmatched", size=27, bold=True, fill=GOLD, anchor="ma")
    plate.text((800, 820), "7 is 2 more than 5", size=38, bold=True, anchor="mm", math_face=True)

    # The explicit bounds assertion documents the intended drawing envelope.
    assert (x0, x1) == (92, 1508)


def draw_patterns(plate: Plate) -> None:
    """Contrast a repeating AB unit with a sequence that grows by one."""

    plate.card((120, 208, 1480, 502), fill=hex_rgba(BLUE_LIGHT, 64), outline=BLUE)
    _section_heading(plate, (270, 246), "REPEATING UNIT", fill=BLUE)
    shape_xs = [410, 570, 730, 890, 1050, 1210]
    for index, x in enumerate(shape_xs):
        if index % 2 == 0:
            plate.draw.ellipse(
                (x - 42, 320, x + 42, 404),
                fill=BLUE_LIGHT,
                outline=BLUE,
                width=5,
            )
            plate.text((x, 362), "A", size=30, bold=True, anchor="mm")
        else:
            plate.draw.rounded_rectangle(
                (x - 42, 320, x + 42, 404),
                radius=8,
                fill=GOLD_LIGHT,
                outline=GOLD,
                width=5,
            )
            plate.text((x, 362), "B", size=30, bold=True, anchor="mm")

    for left, right in ((354, 626), (674, 946), (994, 1266)):
        plate.draw.line((left, 440, right, 440), fill=INK_SOFT, width=4)
        plate.draw.line((left, 428, left, 452), fill=INK_SOFT, width=4)
        plate.draw.line((right, 428, right, 452), fill=INK_SOFT, width=4)
        plate.text(((left + right) / 2, 472), "AB", size=23, bold=True, anchor="mm")

    plate.card((120, 532, 1480, 866), fill=hex_rgba(GREEN_LIGHT, 58), outline=GREEN)
    _section_heading(plate, (264, 570), "GROWING RULE", fill=GREEN)
    group_centers = [400, 700, 1000, 1300]
    for count, cx in enumerate(group_centers, start=1):
        plate.draw.rounded_rectangle(
            (cx - 112, 618, cx + 112, 796),
            radius=18,
            fill=hex_rgba(PAPER_LIGHT, 220),
            outline=hex_rgba(GREEN, 150),
            width=3,
        )
        spacing = 46
        start_x = cx - (count - 1) * spacing / 2
        for leaf_index in range(count):
            _leaf(plate, (start_x + leaf_index * spacing, 694))
        plate.text((cx, 765), str(count), size=30, bold=True, anchor="mm")
        if count < 4:
            plate.arrow((cx + 124, 707), (cx + 164, 707), fill=INK_SOFT, width=5, head=15)
    plate.text((850, 832), "add one leaf each step", size=27, bold=True, fill=GREEN, anchor="mm")


def draw_numbers20(plate: Plate) -> None:
    """Build sixteen from one complete ten-frame and six more counters."""

    plate.card((120, 208, 1480, 866), fill=hex_rgba(GOLD_LIGHT, 45), outline=GOLD)
    plate.draw.rounded_rectangle(
        (675, 228, 925, 338),
        radius=24,
        fill=GOLD_LIGHT,
        outline=GOLD,
        width=5,
    )
    plate.text((800, 282), "16", size=72, bold=True, math_face=True, anchor="mm")
    plate.text((800, 366), "one ten and six more", size=30, bold=True, anchor="mm")

    _ten_frame(plate, (180, 426), filled=10, label="one full ten")
    _ten_frame(plate, (910, 426), filled=6, label="six more")
    plate.text((800, 538), "+", size=60, bold=True, math_face=True, anchor="mm")

    plate.text((800, 798), "10 + 6 = 16", size=44, bold=True, math_face=True, anchor="mm")


def draw_subtraction(plate: Plate) -> None:
    """Show subtraction as both taking away and comparing quantities."""

    plate.card((120, 208, 782, 866), fill=hex_rgba(CORAL_LIGHT, 52), outline=CORAL)
    plate.card((818, 208, 1480, 866), fill=hex_rgba(BLUE_LIGHT, 52), outline=BLUE)
    _section_heading(plate, (451, 248), "TAKE AWAY", fill=CORAL)
    _section_heading(plate, (1149, 248), "FIND THE DIFFERENCE", fill=BLUE)

    left_positions = [
        (285 + column * 130, 370 + row * 118)
        for row in range(3)
        for column in range(3)
    ]
    for index, center in enumerate(left_positions):
        _counter(
            plate,
            center,
            radius=31,
            fill=CORAL_LIGHT if index < 5 else PAPER_LIGHT,
            outline=CORAL,
            mark=str(index + 1),
        )
        if index >= 5:
            x, y = center
            plate.draw.line((x - 24, y - 24, x + 24, y + 24), fill=CORAL, width=7)
            plate.draw.line((x - 24, y + 24, x + 24, y - 24), fill=CORAL, width=7)
    plate.text((451, 699), "cross out 4; 5 remain", size=28, bold=True, fill=CORAL, anchor="mm")
    plate.text((451, 788), "9 − 4 = 5", size=43, bold=True, math_face=True, anchor="mm")

    compare_xs = [894 + index * 65 for index in range(9)]
    for index, x in enumerate(compare_xs):
        _counter(plate, (x, 400), radius=21, fill=BLUE_LIGHT, outline=BLUE)
        if index < 4:
            plate.dashed_line((x, 426), (x, 556), fill=GRID, width=3, dash=10, gap=8)
            _counter(plate, (x, 582), radius=21, fill=PLUM_LIGHT, outline=PLUM)
    plate.text((862, 400), "9", size=28, bold=True, anchor="rm")
    plate.text((862, 582), "4", size=28, bold=True, anchor="rm")
    unmatched_left = compare_xs[4] - 28
    unmatched_right = compare_xs[-1] + 28
    plate.draw.line((unmatched_left, 474, unmatched_right, 474), fill=BLUE, width=5)
    plate.draw.line((unmatched_left, 462, unmatched_left, 486), fill=BLUE, width=5)
    plate.draw.line((unmatched_right, 462, unmatched_right, 486), fill=BLUE, width=5)
    plate.text(((unmatched_left + unmatched_right) / 2, 510), "5 extra", size=25, bold=True, fill=BLUE, anchor="mm")
    plate.text((1149, 699), "the difference is 5", size=28, bold=True, fill=BLUE, anchor="mm")
    plate.text((1149, 788), "4 + 5 = 9", size=43, bold=True, math_face=True, anchor="mm")


def draw_place_value(plate: Plate) -> None:
    """Place four ten-rods and seven unit squares in a labelled place-value mat."""

    plate.card((120, 208, 1480, 866), fill=hex_rgba(GREEN_LIGHT, 45), outline=GREEN)
    plate.draw.line((800, 226, 800, 790), fill=INK_SOFT, width=5)
    plate.text((460, 258), "TENS", size=30, bold=True, fill=GREEN, anchor="mm")
    plate.text((1140, 258), "ONES", size=30, bold=True, fill=BLUE, anchor="mm")

    plate.draw.rounded_rectangle(
        (380, 292, 540, 376), radius=18, fill=GREEN_LIGHT, outline=GREEN, width=4
    )
    plate.text((460, 334), "4", size=55, bold=True, math_face=True, anchor="mm")
    plate.draw.rounded_rectangle(
        (1060, 292, 1220, 376), radius=18, fill=BLUE_LIGHT, outline=BLUE, width=4
    )
    plate.text((1140, 334), "7", size=55, bold=True, math_face=True, anchor="mm")

    rod_lefts = [240, 355, 470, 585]
    rod_top, cell_height, rod_width = 432, 30, 58
    for left in rod_lefts:
        plate.draw.rectangle(
            (left, rod_top, left + rod_width, rod_top + 10 * cell_height),
            fill=GREEN_LIGHT,
            outline=GREEN,
            width=4,
        )
        for cell in range(1, 10):
            y = rod_top + cell * cell_height
            plate.draw.line((left, y, left + rod_width, y), fill=GREEN, width=2)
        plate.text((left + rod_width / 2, 762), "10", size=21, bold=True, anchor="mm")

    unit_centers = [
        (970 + column * 112, 500 + row * 112)
        for row, count in ((0, 4), (1, 3))
        for column in range(count)
    ]
    for unit_number, (x, y) in enumerate(unit_centers, start=1):
        plate.draw.rectangle(
            (x - 34, y - 34, x + 34, y + 34),
            fill=BLUE_LIGHT,
            outline=BLUE,
            width=4,
        )
        plate.text((x, y), str(unit_number), size=22, bold=True, anchor="mm")
    plate.text((1140, 762), "7 single units", size=25, bold=True, fill=BLUE, anchor="mm")
    plate.text((800, 835), "4 tens + 7 ones = 47", size=34, bold=True, math_face=True, anchor="mm")


def _array(
    plate: Plate,
    *,
    origin: Point,
    rows: int,
    columns: int,
    gap_x: int,
    gap_y: int,
    fill: str,
    outline: str,
) -> None:
    x0, y0 = origin
    for row in range(rows):
        for column in range(columns):
            _counter(
                plate,
                (x0 + column * gap_x, y0 + row * gap_y),
                radius=24,
                fill=fill,
                outline=outline,
            )


def draw_multiplication(plate: Plate) -> None:
    """Draw equal 4-by-3 and 3-by-4 arrays, each containing twelve counters."""

    plate.card((120, 208, 750, 866), fill=hex_rgba(TEAL_LIGHT, 55), outline=TEAL)
    plate.card((850, 208, 1480, 866), fill=hex_rgba(GOLD_LIGHT, 55), outline=GOLD)
    _section_heading(plate, (435, 252), "4 ROWS OF 3", fill=TEAL)
    _section_heading(plate, (1165, 252), "3 ROWS OF 4", fill=GOLD)

    _array(
        plate,
        origin=(315, 365),
        rows=4,
        columns=3,
        gap_x=120,
        gap_y=105,
        fill=TEAL_LIGHT,
        outline=TEAL,
    )
    for row in range(4):
        plate.text((205, 365 + row * 105), str(row + 1), size=22, bold=True, fill=TEAL, anchor="mm")
        plate.draw.line((230, 365 + row * 105, 260, 365 + row * 105), fill=TEAL, width=3)

    _array(
        plate,
        origin=(995, 410),
        rows=3,
        columns=4,
        gap_x=112,
        gap_y=125,
        fill=GOLD_LIGHT,
        outline=GOLD,
    )
    for column in range(4):
        plate.text((995 + column * 112, 328), str(column + 1), size=22, bold=True, fill=GOLD, anchor="mm")
        plate.draw.line((995 + column * 112, 348, 995 + column * 112, 370), fill=GOLD, width=3)

    plate.arrow((770, 510), (830, 510), fill=INK_SOFT, width=6, head=18)
    plate.text((800, 475), "turn", size=22, bold=True, fill=INK_SOFT, anchor="mm")
    plate.text((435, 794), "4 × 3 = 12", size=40, bold=True, math_face=True, anchor="mm")
    plate.text((1165, 794), "3 × 4 = 12", size=40, bold=True, math_face=True, anchor="mm")


def draw_division(plate: Plate) -> None:
    """Share exactly twelve counters equally among three outlined bowls."""

    plate.card((120, 208, 1480, 866), fill=hex_rgba(PLUM_LIGHT, 45), outline=PLUM)
    plate.text((800, 265), "12 counters shared among 3 bowls", size=34, bold=True, anchor="mm")
    bowl_centers = [370, 800, 1230]
    for bowl_number, cx in enumerate(bowl_centers, start=1):
        plate.label((cx, 340), "BOWL {}".format(bowl_number), size=21, fill=PLUM)
        # A horizontal rim plus the lower half of an ellipse makes the bowl.
        plate.draw.line((cx - 145, 505, cx + 145, 505), fill=PLUM, width=6)
        plate.draw.arc((cx - 145, 335, cx + 145, 705), 0, 180, fill=PLUM, width=6)
        plate.draw.line((cx - 132, 520, cx + 132, 520), fill=hex_rgba(PLUM, 110), width=3)
        positions = (
            (cx - 55, 575),
            (cx + 55, 575),
            (cx - 55, 645),
            (cx + 55, 645),
        )
        for count, center in enumerate(positions, start=1):
            _counter(
                plate,
                center,
                radius=25,
                fill=PLUM_LIGHT,
                outline=PLUM,
                mark=str(count),
            )
        plate.text((cx, 744), "4 each", size=27, bold=True, fill=PLUM, anchor="mm")
    plate.text((800, 818), "12 ÷ 3 = 4", size=43, bold=True, math_face=True, anchor="mm")


def _draw_ruler(plate: Plate, *, x0: int, y: int, units: int, step: int) -> None:
    x1 = x0 + units * step
    plate.draw.rounded_rectangle(
        (x0, y, x1, y + 70), radius=8, fill=GOLD_LIGHT, outline=GOLD, width=4
    )
    for tick in range(units + 1):
        x = x0 + tick * step
        tick_height = 30 if tick in (0, units) else (24 if tick % 5 == 0 else 17)
        plate.draw.line((x, y, x, y + tick_height), fill=INK, width=3)
        plate.text((x, y + 48), str(tick), size=14, bold=True, anchor="mm")


def draw_measurement(plate: Plate) -> None:
    """Match length, mass, and liquid volume with distinct instruments."""

    card_boxes = ((120, 208, 550, 866), (585, 208, 1015, 866), (1050, 208, 1480, 866))
    for box, outline in zip(card_boxes, (GOLD, CORAL, BLUE)):
        plate.card(box, fill=hex_rgba(PAPER_LIGHT, 230), outline=outline)

    _section_heading(plate, (335, 252), "LENGTH", fill=GOLD)
    _section_heading(plate, (800, 252), "MASS", fill=CORAL)
    _section_heading(plate, (1265, 252), "VOLUME", fill=BLUE)

    # Pencil endpoints align exactly with the 0 cm and 7 cm ruler ticks.
    ruler_x, ruler_y, ruler_step = 160, 606, 35
    _draw_ruler(plate, x0=ruler_x, y=ruler_y, units=10, step=ruler_step)
    pencil_y = 520
    pencil_end = ruler_x + 7 * ruler_step
    plate.draw.rounded_rectangle(
        (ruler_x, pencil_y - 18, pencil_end - 30, pencil_y + 18),
        radius=6,
        fill=GOLD_LIGHT,
        outline=INK,
        width=4,
    )
    plate.draw.polygon(
        ((pencil_end - 30, pencil_y - 18), (pencil_end, pencil_y), (pencil_end - 30, pencil_y + 18)),
        fill=PAPER,
        outline=INK,
    )
    plate.draw.line((ruler_x, 480, ruler_x, 592), fill=INK_SOFT, width=3)
    plate.draw.line((pencil_end, 480, pencil_end, 592), fill=INK_SOFT, width=3)
    plate.text((335, 397), "pencil", size=25, bold=True, fill=INK_SOFT, anchor="mm")
    plate.text((335, 752), "7 cm", size=37, bold=True, math_face=True, anchor="mm")
    plate.text((335, 811), "ruler", size=24, fill=INK_SOFT, anchor="mm")

    # A generic apple has no asserted universal mass; the scale poses the reading.
    plate.draw.ellipse((731, 368, 869, 516), fill=CORAL_LIGHT, outline=CORAL, width=5)
    plate.draw.arc((718, 385, 807, 508), 285, 65, fill=CORAL, width=4)
    plate.draw.line((800, 370, 808, 330), fill=GREEN, width=7)
    plate.draw.ellipse((807, 326, 859, 354), fill=GREEN_LIGHT, outline=GREEN, width=3)
    plate.draw.rounded_rectangle(
        (676, 536, 924, 686), radius=24, fill=CORAL_LIGHT, outline=CORAL, width=5
    )
    plate.draw.rectangle((710, 512, 890, 552), fill=PAPER_LIGHT, outline=CORAL, width=4)
    plate.draw.rounded_rectangle(
        (742, 584, 858, 638), radius=8, fill=PAPER_LIGHT, outline=INK_SOFT, width=3
    )
    plate.text((800, 611), "? g", size=28, bold=True, math_face=True, anchor="mm")
    plate.text((800, 752), "weigh it", size=30, bold=True, fill=CORAL, anchor="mm")
    plate.text((800, 811), "scale", size=24, fill=INK_SOFT, anchor="mm")

    # The water surface lies exactly on the 300 mL graduation.
    jug_left, jug_right, jug_top, jug_bottom = 1160, 1390, 390, 700
    plate.draw.rounded_rectangle(
        (jug_left, jug_top, jug_right, jug_bottom),
        radius=22,
        fill=hex_rgba(BLUE_LIGHT, 34),
        outline=BLUE,
        width=5,
    )
    plate.draw.rectangle((jug_left + 7, 506, jug_right - 7, jug_bottom - 7), fill=hex_rgba(BLUE_LIGHT, 150))
    plate.draw.line((jug_left + 7, 506, jug_right - 7, 506), fill=BLUE, width=5)
    for value, y in ((400, 430), (300, 506), (200, 582), (100, 658)):
        plate.draw.line((jug_left, y, jug_left + 35, y), fill=INK, width=4)
        plate.text((jug_left - 13, y), str(value), size=17, bold=True, anchor="rm")
    plate.dashed_line((1085, 506), (1120, 506), fill=INK_SOFT, width=3, dash=12, gap=9)
    plate.dashed_line((1400, 506), (1450, 506), fill=INK_SOFT, width=3, dash=12, gap=9)
    plate.text((1265, 746), "300 mL", size=34, bold=True, math_face=True, anchor="mm")
    plate.text((1265, 805), "read at eye level", size=23, fill=INK_SOFT, anchor="mm")


def draw_time(plate: Plate) -> None:
    """Set an exact 3:00 clock beside an unambiguous June-to-July transition."""

    plate.card((120, 208, 930, 866), fill=hex_rgba(BLUE_LIGHT, 44), outline=BLUE)
    plate.card((970, 208, 1480, 866), fill=hex_rgba(GREEN_LIGHT, 44), outline=GREEN)
    _section_heading(plate, (525, 250), "CLOCK", fill=BLUE)
    _section_heading(plate, (1225, 250), "CALENDAR", fill=GREEN)

    center, radius = (525, 535), 235
    plate.draw.ellipse(
        (center[0] - radius, center[1] - radius, center[0] + radius, center[1] + radius),
        fill=hex_rgba(PAPER_LIGHT, 235),
        outline=BLUE,
        width=7,
    )
    for hour in range(1, 13):
        angle = -math.pi / 2 + hour * math.tau / 12
        outer = (
            center[0] + (radius - 12) * math.cos(angle),
            center[1] + (radius - 12) * math.sin(angle),
        )
        inner = (
            center[0] + (radius - 34) * math.cos(angle),
            center[1] + (radius - 34) * math.sin(angle),
        )
        plate.draw.line((*inner, *outer), fill=INK, width=5 if hour % 3 == 0 else 3)
        numeral = (
            center[0] + (radius - 67) * math.cos(angle),
            center[1] + (radius - 67) * math.sin(angle),
        )
        plate.text(numeral, str(hour), size=26, bold=True, math_face=True, anchor="mm")

    # Long minute hand at 12; short hour hand at 3.
    plate.arrow(center, (center[0], center[1] - 145), fill=BLUE, width=8, head=18)
    plate.arrow(center, (center[0] + 112, center[1]), fill=CORAL, width=12, head=21)
    plate.dot(center, 13, fill=INK, outline=INK, width=2)
    plate.text((525, 807), "3:00", size=45, bold=True, math_face=True, anchor="mm")

    plate.text((1225, 327), "JUNE", size=30, bold=True, fill=GREEN, anchor="mm")
    plate.draw.rounded_rectangle(
        (1050, 366, 1260, 570), radius=16, fill=PAPER_LIGHT, outline=GREEN, width=4
    )
    plate.draw.line((1155, 366, 1155, 570), fill=GREEN, width=3)
    plate.text((1102, 469), "29", size=45, bold=True, math_face=True, anchor="mm")
    plate.text((1207, 469), "30", size=45, bold=True, math_face=True, anchor="mm")

    plate.arrow((1268, 469), (1311, 469), fill=INK_SOFT, width=5, head=15)
    plate.text((1370, 327), "JULY", size=30, bold=True, fill=GREEN, anchor="mm")
    plate.draw.rounded_rectangle(
        (1318, 366, 1455, 570), radius=16, fill=GREEN_LIGHT, outline=GREEN, width=4
    )
    plate.draw.line((1364, 366, 1364, 570), fill=GREEN, width=3)
    plate.draw.line((1410, 366, 1410, 570), fill=GREEN, width=3)
    for date, x in zip((1, 2, 3), (1341, 1387, 1432)):
        plate.text((x, 469), str(date), size=34, bold=True, math_face=True, anchor="mm")
    plate.text((1225, 652), "June 30 is followed", size=26, bold=True, anchor="mm")
    plate.text((1225, 693), "by July 1", size=26, bold=True, anchor="mm")
    plate.text((1225, 784), "days continue; the month changes", size=22, fill=INK_SOFT, anchor="mm")


def _fraction_whole(
    plate: Plate,
    box: Tuple[int, int, int, int],
    *,
    parts: int,
    shaded_parts: Iterable[int],
) -> None:
    x0, y0, x1, y1 = box
    part_width = (x1 - x0) // parts
    shaded = set(shaded_parts)
    for part in range(parts):
        left = x0 + part * part_width
        right = x1 if part == parts - 1 else left + part_width
        plate.draw.rectangle(
            (left, y0, right, y1),
            fill=GOLD_LIGHT if part in shaded else PAPER_LIGHT,
        )
        if part in shaded:
            _hatch_rect(plate, (left, y0, right, y1), fill=GOLD)
    plate.draw.rectangle(box, outline=INK, width=6)
    for part in range(1, parts):
        x = x0 + part * part_width
        plate.draw.line((x, y0, x, y1), fill=INK, width=5)
    for part in range(parts):
        left = x0 + part * part_width
        right = x1 if part == parts - 1 else left + part_width
        plate.text(
            ((left + right) / 2, (y0 + y1) / 2),
            "1/{}".format(parts),
            size=36,
            bold=True,
            math_face=True,
            anchor="mm",
        )


def draw_fractions_intro(plate: Plate) -> None:
    """Partition equal-sized wholes into exact halves and quarters."""

    plate.card((120, 208, 1480, 866), fill=hex_rgba(GOLD_LIGHT, 38), outline=GOLD)
    _section_heading(plate, (450, 256), "HALVES", fill=GOLD)
    _section_heading(plate, (1150, 256), "QUARTERS", fill=GOLD)

    left_whole = (170, 360, 730, 680)
    right_whole = (870, 360, 1430, 680)
    _fraction_whole(plate, left_whole, parts=2, shaded_parts=(0,))
    _fraction_whole(plate, right_whole, parts=4, shaded_parts=(0, 1))
    plate.text((450, 728), "2 equal parts", size=28, bold=True, anchor="mm")
    plate.text((1150, 728), "4 equal parts", size=28, bold=True, anchor="mm")
    plate.text((800, 808), "1/2 = 2/4", size=43, bold=True, math_face=True, anchor="mm")


SPECS: Dict[str, Dict[str, object]] = {
    "math.0.compare": {
        "id": "math.0.compare",
        "title": "Bigger and Smaller",
        "stage": 0,
        "plate_id": "paired-comparison-plate",
        "alt": "Five counters are paired with five of seven counters, leaving two unmatched in the larger set.",
        "caption": "Pairing one object from each set proves that seven is two more than five. Size and spacing do not change how many objects a set contains.",
        "draw": draw_compare,
    },
    "math.0.patterns": {
        "id": "math.0.patterns",
        "title": "Patterns",
        "stage": 0,
        "plate_id": "repeating-and-growing-patterns-plate",
        "alt": "An alternating circle-square unit repeats three times above groups of one, two, three, and four leaves.",
        "caption": "Some patterns repeat a smallest unit; others grow by a stated rule. A sequence is predictable only after its rule is identified.",
        "draw": draw_patterns,
    },
    "math.0.numbers20": {
        "id": "math.0.numbers20",
        "title": "Numbers to Twenty",
        "stage": 0,
        "plate_id": "sixteen-ten-frame-plate",
        "alt": "A full ten-frame and six counters in a second frame represent the number sixteen.",
        "caption": "Sixteen is one group of ten and six more. Its numeral comes after 15 and before 17.",
        "draw": draw_numbers20,
    },
    "math.1.subtraction": {
        "id": "math.1.subtraction",
        "title": "Subtraction",
        "stage": 1,
        "plate_id": "subtraction-two-meanings-plate",
        "alt": "Nine counters with four crossed out leave five; paired rows of nine and four also differ by five.",
        "caption": "The equation 9 − 4 = 5 can describe what remains or the difference between two quantities. Addition checks the result because 4 + 5 = 9.",
        "draw": draw_subtraction,
    },
    "math.1.place-value": {
        "id": "math.1.place-value",
        "title": "Place Value",
        "stage": 1,
        "plate_id": "forty-seven-place-value-plate",
        "alt": "Four ten-rods sit in the tens column and seven unit squares sit in the ones column to make 47.",
        "caption": "In 47, position gives the 4 a value of forty and the 7 a value of seven. One ten can be exchanged for ten ones without changing the total.",
        "draw": draw_place_value,
    },
    "math.1.multiplication": {
        "id": "math.1.multiplication",
        "title": "Multiplication",
        "stage": 1,
        "plate_id": "twelve-array-turn-plate",
        "alt": "Four rows of three counters form an array of twelve; turning the array gives three rows of four.",
        "caption": "Four groups of three total twelve. Rotating the array shows that 4 × 3 and 3 × 4 have the same product.",
        "draw": draw_multiplication,
    },
    "math.1.division": {
        "id": "math.1.division",
        "title": "Division",
        "stage": 1,
        "plate_id": "twelve-shared-three-ways-plate",
        "alt": "Twelve counters are shared equally among three bowls, leaving four counters in each bowl.",
        "caption": "Sharing 12 among 3 equal groups gives 4 in each group. Making groups of 3 from the same 12 instead produces 4 groups.",
        "draw": draw_division,
    },
    "math.1.measurement": {
        "id": "math.1.measurement",
        "title": "Measuring Things",
        "stage": 1,
        "plate_id": "measurement-tools-plate",
        "alt": "A pencil is aligned with a ruler, an apple rests on a scale, and water reaches a marked level in a measuring jug.",
        "caption": "Length, mass, and liquid volume require different instruments and units. A measurement is a number together with its unit.",
        "draw": draw_measurement,
    },
    "math.1.time": {
        "id": "math.1.time",
        "title": "Time and Calendars",
        "stage": 1,
        "plate_id": "three-oclock-calendar-plate",
        "alt": "A clock shows three o'clock with its short hour hand at 3 and long minute hand at 12, beside a calendar changing from June to July.",
        "caption": "At exactly 3:00, the minute hand points to 12 and the hour hand points to 3. As minutes pass, both hands move; this calendar uses the common Gregorian month sequence.",
        "draw": draw_time,
    },
    "math.1.fractions-intro": {
        "id": "math.1.fractions-intro",
        "title": "Halves and Quarters",
        "stage": 1,
        "plate_id": "halves-and-quarters-plate",
        "alt": "Two identical rectangles are divided into two equal parts and four equal parts, showing halves and quarters of the same-sized whole.",
        "caption": "Fraction names require equal parts of the same whole. Two halves or four quarters make one whole, and two quarters cover the same amount as one half.",
        "draw": draw_fractions_intro,
    },
}
