"""Bespoke explanatory renderers for advanced computer-science plates.

Tree, Grove, and Forest computing lessons need diagrams that expose a real
mechanism rather than repeat a generic flow-card motif.  Every renderer below
therefore works through one inspectable example: merge-sort comparisons,
object state, browser rendering, SQL predicates, Boolean gates, a commit DAG,
graph relaxation, a DFA trace, virtual-memory translation, transaction commit,
held-out evaluation, authenticated encryption, pointer aliasing, attention,
quorum commit, typed reduction, quantum interference, or a specification /
counterexample loop.

The compositions are deterministic and legible in the 800 px derivative.
Colour is always backed by labels, line styles, shapes, values, or ordering.
The registry contains only the eighteen generator-owned stage 3--5 lessons;
the authored data-structures, networks, and complexity plates remain untouched.
"""

from __future__ import annotations

import math
from typing import Callable, Dict, Iterable, Sequence, Tuple

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
    INK,
    INK_SOFT,
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
Box = Tuple[float, float, float, float]
Renderer = Callable[[Plate], None]

TONES = (BLUE, TEAL, GOLD, CORAL, PLUM, GREEN)
LIGHTS = (BLUE_LIGHT, TEAL_LIGHT, GOLD_LIGHT, CORAL_LIGHT, PLUM_LIGHT, GREEN_LIGHT)


def _tint(tone: str, amount: float = .84) -> str:
    return mix(tone, PAPER_LIGHT, amount)


def _panel(plate: Plate, box: Box, tone: str, *, radius: int = 20,
           alpha: int = 226, width: int = 4) -> None:
    plate.draw.rounded_rectangle(
        box, radius=radius, fill=hex_rgba(_tint(tone, .88), alpha),
        outline=hex_rgba(tone, 210), width=width,
    )


def _tag(plate: Plate, center: Point, value: str, tone: str, *, size: int = 22) -> None:
    plate.label(center, value, size=max(20, size), fill=tone)


def _footer(plate: Plate, value: str, *, tone: str | None = None,
            size: int = 25) -> None:
    tone = tone or plate.accent
    plate.draw.rounded_rectangle(
        (150, 816, 1450, 882), radius=25,
        fill=hex_rgba(_tint(tone, .78), 225),
        outline=hex_rgba(tone, 185), width=3,
    )
    plate.text((800, 849), value, size=size, bold=True, fill=tone, anchor="mm")


def _arrow(plate: Plate, start: Point, end: Point, tone: str = INK_SOFT,
           label: str = "", *, label_dy: float = -22, width: int = 6,
           head: int = 18) -> None:
    plate.arrow(start, end, fill=tone, width=width, head=head)
    if label:
        plate.text(((start[0] + end[0]) / 2,
                    (start[1] + end[1]) / 2 + label_dy),
                   label, size=19, bold=True, fill=tone, anchor="mm")


def _line_text(plate: Plate, xy: Point, value: str, *, size: int = 22,
               bold: bool = False, fill: str = INK, anchor: str = "lm") -> None:
    plate.text(xy, value, size=size, bold=bold, fill=fill, anchor=anchor)


def _center_lines(plate: Plate, center: Point, lines: Sequence[str], *,
                  size: int = 21, gap: int = 8, bold: bool = False,
                  fill: str = INK) -> None:
    step = size + gap
    y = center[1] - (len(lines) - 1) * step / 2
    for line in lines:
        plate.text((center[0], y), line, size=size, bold=bold,
                   fill=fill, anchor="mm")
        y += step


def _node(plate: Plate, center: Point, value: str, tone: str, *,
          radius: int = 42, double: bool = False, shape: str = "circle",
          size: int = 22) -> None:
    x, y = center
    if shape == "square":
        plate.draw.rounded_rectangle((x - radius, y - radius, x + radius, y + radius),
                                     radius=13, fill=hex_rgba(_tint(tone, .68), 245),
                                     outline=tone, width=5)
    elif shape == "diamond":
        plate.draw.polygon(((x, y - radius), (x + radius + 12, y),
                            (x, y + radius), (x - radius - 12, y)),
                           fill=hex_rgba(_tint(tone, .68), 245), outline=tone)
        plate.draw.line((x, y - radius, x + radius + 12, y, x, y + radius,
                         x - radius - 12, y, x, y - radius), fill=tone, width=5)
    else:
        plate.draw.ellipse((x - radius, y - radius, x + radius, y + radius),
                           fill=hex_rgba(_tint(tone, .68), 245), outline=tone, width=5)
        if double:
            plate.draw.ellipse((x - radius + 10, y - radius + 10,
                                x + radius - 10, y + radius - 10),
                               outline=tone, width=3)
    plate.text((x, y), value, size=size, bold=True, fill=tone, anchor="mm")


def _code(plate: Plate, box: Box, value: str, *, tone: str = BLUE,
          active: bool = False, size: int = 21) -> None:
    x0, y0, x1, y1 = box
    plate.draw.rounded_rectangle(
        box, radius=11,
        fill=hex_rgba(_tint(tone, .76), 236) if active else hex_rgba(PAPER_LIGHT, 218),
        outline=tone if active else hex_rgba(GRID, 190), width=4 if active else 2,
    )
    plate.draw.text((x0 + 17, (y0 + y1) / 2), value,
                    font=font(size, math_face=True), fill=INK, anchor="lm")


def _value_tile(plate: Plate, box: Box, value: str, tone: str, *,
                sub: str = "", crossed: bool = False, size: int = 26) -> None:
    _panel(plate, box, tone, radius=14, alpha=238, width=3)
    x0, y0, x1, y1 = box
    plate.text(((x0 + x1) / 2, (y0 + y1) / 2 - (10 if sub else 0)),
               value, size=size, bold=True, fill=tone, anchor="mm")
    if sub:
        plate.text(((x0 + x1) / 2, y1 - 16), sub, size=16,
                   bold=True, fill=INK_SOFT, anchor="mm")
    if crossed:
        plate.draw.line((x0 + 9, y0 + 9, x1 - 9, y1 - 9),
                        fill=CORAL, width=6)


def _table_grid(plate: Plate, box: Box, rows: int, cols: int,
                *, tone: str = GRID, width: int = 2) -> Tuple[float, float]:
    x0, y0, x1, y1 = box
    cell_w = (x1 - x0) / cols
    cell_h = (y1 - y0) / rows
    plate.draw.rounded_rectangle(box, radius=12, fill=hex_rgba(PAPER_LIGHT, 226),
                                 outline=hex_rgba(tone, 205), width=3)
    for col in range(1, cols):
        x = x0 + col * cell_w
        plate.draw.line((x, y0, x, y1), fill=hex_rgba(tone, 175), width=width)
    for row in range(1, rows):
        y = y0 + row * cell_h
        plate.draw.line((x0, y, x1, y), fill=hex_rgba(tone, 175), width=width)
    return cell_w, cell_h


def _render_algorithms(plate: Plate) -> None:
    """Expose the recursive split tree and the comparisons in the final merge."""

    _tag(plate, (260, 219), "DIVIDE", PLUM)
    _tag(plate, (778, 219), "SORT SUBPROBLEMS", BLUE)
    _tag(plate, (1310, 219), "MERGE BY COMPARISON", GREEN)

    # A recursive tree makes the logarithmic depth visible without using colour.
    levels = (
        (("7  2  5  1", 360),),
        (("7  2", 265), ("5  1", 455)),
        (("7", 218), ("2", 312), ("5", 408), ("1", 502)),
    )
    ys = (292, 455, 625)
    for level, (items, y) in enumerate(zip(levels, ys)):
        for label, x in items:
            half_width = 40 if level == 2 else 72
            _value_tile(plate, (x - half_width, y - 37, x + half_width, y + 37), label,
                        (PLUM, BLUE, TEAL)[level], size=21 if len(label) > 3 else 25)
    for start, end in (((360, 331), (265, 416)), ((360, 331), (455, 416)),
                       ((265, 494), (218, 586)), ((265, 494), (312, 586)),
                       ((455, 494), (408, 586)), ((455, 494), (502, 586))):
        _arrow(plate, start, end, INK_SOFT, width=4, head=12)
    plate.text((360, 711), "depth = log2 4 = 2", size=21, bold=True,
               fill=PLUM, anchor="mm")

    # Sorted halves retain source identities with L/R labels.
    for i, (value, origin) in enumerate(((2, "L1"), (7, "L2"), (1, "R1"), (5, "R2"))):
        x = 640 + i * 105
        _value_tile(plate, (x - 42, 349, x + 42, 430), str(value),
                    BLUE if origin.startswith("L") else TEAL, sub=origin)
    _center_lines(plate, (798, 500),
                  ("compare heads: 2 vs 1 -> take 1", "2 vs 5 -> take 2",
                   "7 vs 5 -> take 5", "append remaining 7"),
                  size=19, gap=10, bold=True)
    for index, value in enumerate((1, 2, 5, 7)):
        x = 642 + index * 105
        _value_tile(plate, (x - 42, 638, x + 42, 715), str(value), GREEN,
                    sub=str(index + 1))

    # A small operation accounting panel distinguishes depth from total work.
    _panel(plate, (1080, 281, 1482, 744), GREEN)
    plate.text((1281, 321), "WORK BY LEVEL", size=22, bold=True,
               fill=GREEN, anchor="mm")
    bars = (("split", 4, "n touches"), ("merge pairs", 4, "n comparisons/touches"),
            ("final merge", 4, "n comparisons/touches"))
    for row, (label, units, note) in enumerate(bars):
        y = 399 + row * 105
        plate.text((1110, y), label, size=19, bold=True, fill=INK, anchor="lm")
        for unit in range(units):
            plate.draw.rectangle((1248 + unit * 49, y - 18, 1284 + unit * 49, y + 18),
                                 fill=hex_rgba(GREEN, 75 + unit * 24), outline=GREEN, width=2)
        plate.text((1446, y + 35), note, size=15, fill=INK_SOFT, anchor="ra")
    plate.text((1281, 687), "n work x log n levels", size=23,
               bold=True, fill=GREEN, anchor="mm")
    _footer(plate, "merge sort divides to singletons, then performs linear work across each level", size=23)


def _render_oop(plate: Plate) -> None:
    """Separate class definition, inheritance, and per-instance state."""

    _tag(plate, (296, 220), "CLASS CONTRACT", BLUE)
    _tag(plate, (800, 220), "IS-A SPECIALIZATION", PLUM)
    _tag(plate, (1315, 220), "DISTINCT OBJECT STATE", TEAL)

    _panel(plate, (110, 278, 506, 744), BLUE)
    plate.text((308, 321), "Vehicle", size=31, bold=True, fill=BLUE, anchor="mm")
    plate.draw.line((142, 356, 474, 356), fill=BLUE, width=3)
    for y, text in ((404, "field  speed: Number"), (458, "method move(): Position"),
                    (530, "invariant: speed >= 0")):
        _code(plate, (142, y - 25, 474, y + 25), text, tone=BLUE,
              active=y == 530, size=18)
    plate.text((308, 625), "definition: shared", size=22, bold=True,
               fill=BLUE, anchor="mm")
    plate.text((308, 672), "state: supplied by each object", size=19,
               fill=INK_SOFT, anchor="mm")

    _panel(plate, (604, 278, 996, 744), PLUM)
    _node(plate, (800, 355), "Vehicle", BLUE, radius=56, shape="square")
    _node(plate, (703, 555), "Bike", PLUM, radius=53, shape="square")
    _node(plate, (897, 555), "Car", GOLD, radius=53, shape="square")
    _arrow(plate, (727, 504), (770, 416), PLUM, width=5, head=14)
    _arrow(plate, (873, 504), (830, 416), GOLD, width=5, head=14)
    plate.text((674, 449), "inherits", size=16, bold=True,
               fill=PLUM, anchor="mm")
    plate.text((926, 449), "inherits", size=16, bold=True,
               fill=GOLD, anchor="mm")
    plate.text((703, 650), "+ ringBell()", size=19, bold=True,
               fill=PLUM, anchor="mm")
    plate.text((897, 650), "+ refuel()", size=19, bold=True,
               fill=GOLD, anchor="mm")
    plate.text((800, 704), "arrows point to the inherited contract", size=17,
               fill=INK_SOFT, anchor="mm")

    _panel(plate, (1094, 278, 1490, 744), TEAL)
    for row, (name, speed, wheel) in enumerate((("b1", "12 km/h", "#1"),
                                                ("b2", "20 km/h", "#2"))):
        y0 = 347 + row * 178
        plate.draw.rounded_rectangle((1130, y0, 1454, y0 + 135), radius=17,
                                     fill=hex_rgba(TEAL_LIGHT, 110), outline=TEAL, width=4)
        plate.text((1160, y0 + 34), "Bike " + name, size=23, bold=True,
                   fill=TEAL, anchor="lm")
        plate.text((1160, y0 + 75), "speed = " + speed, size=20, fill=INK, anchor="lm")
        plate.text((1160, y0 + 107), "identity " + wheel, size=18,
                   fill=INK_SOFT, anchor="lm")
    plate.text((1292, 684), "same methods; separate fields", size=20,
               bold=True, fill=TEAL, anchor="mm")
    _footer(plate, "a class shares structure and behavior; each object keeps its own state", size=24)


def _render_web(plate: Plate) -> None:
    """Show the browser's parse/style/event pipeline and a concrete DOM update."""

    _tag(plate, (242, 219), "SOURCE RESOURCES", BLUE)
    _tag(plate, (795, 219), "BROWSER PIPELINE", PLUM)
    _tag(plate, (1350, 219), "ACCESSIBLE OUTPUT", GREEN)

    _panel(plate, (104, 274, 545, 760), BLUE)
    source = (("HTML", '<button id="save">Save</button>', BLUE),
              ("CSS", "button { background: teal; }", TEAL),
              ("JS", "click -> status = 'Saved'", GOLD))
    for row, (kind, text, tone) in enumerate(source):
        y = 326 + row * 137
        _tag(plate, (171, y), kind, tone, size=18)
        _code(plate, (237, y - 35, 514, y + 35), text, tone=tone,
              active=row == 2, size=16)
    plate.text((325, 709), "three files; one interface", size=20,
               bold=True, fill=BLUE, anchor="mm")

    _panel(plate, (630, 274, 990, 760), PLUM)
    stages = (("1", "parse HTML", "DOM tree"), ("2", "apply CSS", "styled boxes"),
              ("3", "wire event", "click handler"), ("4", "paint + announce", "screen + AT"))
    for row, (num, action, result) in enumerate(stages):
        y = 331 + row * 100
        _node(plate, (688, y), num, (BLUE, TEAL, GOLD, GREEN)[row],
              radius=28, shape="square", size=19)
        plate.text((737, y - 11), action, size=19, bold=True,
                   fill=INK, anchor="lm")
        plate.text((737, y + 21), result, size=17, fill=INK_SOFT, anchor="lm")
        if row < len(stages) - 1:
            _arrow(plate, (688, y + 31), (688, y + 68), INK_SOFT, width=4, head=11)

    _panel(plate, (1075, 274, 1496, 760), GREEN)
    # A miniature browser window shows both visual and semantic state.
    plate.draw.rounded_rectangle((1112, 318, 1459, 662), radius=20,
                                 fill=hex_rgba(PAPER_LIGHT, 245), outline=GREEN, width=4)
    plate.draw.line((1112, 369, 1459, 369), fill=GREEN, width=3)
    for i in range(3):
        plate.dot((1141 + i * 29, 344), 7, fill=(CORAL, GOLD, GREEN)[i],
                  outline=(CORAL, GOLD, GREEN)[i], width=1)
    plate.draw.rounded_rectangle((1194, 421, 1377, 497), radius=15,
                                 fill=TEAL, outline=INK, width=3)
    plate.text((1285, 459), "SAVE", size=24, bold=True,
               fill=PAPER_LIGHT, anchor="mm")
    _arrow(plate, (1285, 510), (1285, 558), GOLD, width=5, head=14)
    plate.text((1330, 535), "click", size=21, bold=True, fill=GOLD, anchor="lm")
    plate.text((1285, 595), "status: Saved", size=23, bold=True,
               fill=GREEN, anchor="mm")
    plate.text((1285, 632), 'live region: role="status"', size=18, fill=INK_SOFT, anchor="mm")
    plate.text((1285, 698), "role=button  |  status announced", size=18,
               bold=True, fill=INK_SOFT, anchor="mm")
    _footer(plate, "HTML gives structure, CSS presentation, and JavaScript changes state on events", size=23)


def _render_databases(plate: Plate) -> None:
    """Evaluate both SQL predicates row by row and separate result from storage."""

    _tag(plate, (346, 219), "STORED TABLE: books", BLUE)
    _tag(plate, (1073, 219), "WHERE year >= 2020 AND rating > 4.0", PLUM)

    table_box = (105, 280, 794, 711)
    cw, ch = _table_grid(plate, table_box, 5, 4, tone=BLUE)
    headers = ("title", "year", "rating", "row id")
    rows = (("Atlas", "2018", "4.7", "r1"), ("Moss", "2021", "4.3", "r2"),
            ("Cloud", "2022", "3.9", "r3"), ("Tide", "2024", "4.8", "r4"))
    for col, value in enumerate(headers):
        plate.text((table_box[0] + (col + .5) * cw, table_box[1] + ch / 2),
                   value, size=20, bold=True, fill=BLUE, anchor="mm")
    for row, values in enumerate(rows, start=1):
        for col, value in enumerate(values):
            plate.text((table_box[0] + (col + .5) * cw,
                        table_box[1] + (row + .5) * ch), value,
                       size=20, bold=col == 0, fill=INK, anchor="mm")
    plate.text((449, 751), "SELECT does not alter these four stored rows", size=19,
               bold=True, fill=BLUE, anchor="mm")

    _panel(plate, (844, 280, 1495, 711), PLUM)
    checks = (("r1 Atlas", "2018 >= 2020", "FALSE", "reject"),
              ("r2 Moss", "2021 >= 2020; 4.3 > 4", "TRUE AND TRUE", "KEEP"),
              ("r3 Cloud", "2022 >= 2020; 3.9 > 4", "TRUE AND FALSE", "reject"),
              ("r4 Tide", "2024 >= 2020; 4.8 > 4", "TRUE AND TRUE", "KEEP"))
    for row, (name, predicate, truth, outcome) in enumerate(checks):
        y = 329 + row * 87
        tone = GREEN if outcome == "KEEP" else CORAL
        plate.text((873, y), name, size=19, bold=True, fill=INK, anchor="lm")
        plate.text((873, y + 29), predicate, size=16, fill=INK_SOFT, anchor="lm")
        plate.text((1265, y), truth, size=16, bold=True, fill=tone, anchor="mm")
        _tag(plate, (1438, y + 15), outcome, tone, size=16)
        if row < 3:
            plate.draw.line((872, y + 60, 1464, y + 60),
                            fill=hex_rgba(GRID, 165), width=2)
    _arrow(plate, (1050, 693), (1262, 693), GREEN, "result: Moss, Tide", label_dy=-28)
    _footer(plate, "WHERE keeps a row only when the complete Boolean condition evaluates true", size=23)


def _gate(plate: Plate, center: Point, label: str, tone: str,
          *, shape: str = "curved") -> None:
    x, y = center
    if shape == "xor":
        def curve(start: Point, control: Point, end: Point) -> None:
            points = []
            for index in range(25):
                t = index / 24
                points.append(((1 - t) ** 2 * start[0] + 2 * (1 - t) * t * control[0] + t ** 2 * end[0],
                               (1 - t) ** 2 * start[1] + 2 * (1 - t) * t * control[1] + t ** 2 * end[1]))
            plate.draw.line(points, fill=tone, width=5, joint="curve")

        # Standard XOR outline: an OR gate plus a second offset input curve.
        curve((x - 63, y - 60), (x + 34, y - 64), (x + 88, y))
        curve((x + 88, y), (x + 34, y + 64), (x - 63, y + 60))
        curve((x - 63, y - 60), (x - 10, y), (x - 63, y + 60))
        curve((x - 77, y - 60), (x - 24, y), (x - 77, y + 60))
    else:
        plate.draw.line((x - 70, y - 60, x - 5, y - 60), fill=tone, width=5)
        plate.draw.line((x - 70, y + 60, x - 5, y + 60), fill=tone, width=5)
        plate.draw.line((x - 70, y - 60, x - 70, y + 60), fill=tone, width=5)
        plate.draw.arc((x - 65, y - 60, x + 92, y + 60), -90, 90,
                       fill=tone, width=5)
    plate.text((x, y), label, size=20, bold=True, fill=tone, anchor="mm")


def _render_hardware(plate: Plate) -> None:
    """Derive a half-adder output from gates and its complete truth table."""

    _tag(plate, (363, 219), "SIGNAL PATH FOR A=1, B=1", BLUE)
    _tag(plate, (1160, 219), "COMPLETE HALF-ADDER TABLE", GOLD)

    _panel(plate, (105, 278, 820, 748), BLUE)
    _node(plate, (184, 403), "A=1", BLUE, radius=38, shape="square", size=20)
    _node(plate, (184, 604), "B=1", BLUE, radius=38, shape="square", size=20)
    _gate(plate, (435, 395), "XOR", TEAL, shape="xor")
    _gate(plate, (435, 612), "AND", PLUM, shape="and")
    for start, end in (((225, 403), (348, 386)), ((225, 604), (348, 414)),
                       ((225, 403), (348, 585)), ((225, 604), (348, 622))):
        _arrow(plate, start, end, INK_SOFT, width=5, head=14)
    _arrow(plate, (529, 395), (654, 395), TEAL, "exactly one?", label_dy=-24)
    _arrow(plate, (529, 612), (654, 612), PLUM, "both one?", label_dy=-24)
    _value_tile(plate, (663, 348, 778, 442), "SUM 0", TEAL, sub="low")
    _value_tile(plate, (663, 565, 778, 659), "CARRY 1", PLUM, sub="high", size=22)
    plate.text((463, 705), "output bits: carry,sum = 10 (binary 2)", size=21,
               bold=True, fill=BLUE, anchor="mm")

    _panel(plate, (884, 278, 1495, 748), GOLD)
    box = (932, 340, 1447, 676)
    cw, ch = _table_grid(plate, box, 5, 4, tone=GOLD)
    values = (("A", "B", "SUM XOR", "CARRY AND"),
              ("0", "0", "0", "0"), ("0", "1", "1", "0"),
              ("1", "0", "1", "0"), ("1", "1", "0", "1"))
    for row, cells in enumerate(values):
        for col, value in enumerate(cells):
            tone = GOLD if row == 0 else (PLUM if row == 4 and col == 3 else INK)
            plate.text((box[0] + (col + .5) * cw, box[1] + (row + .5) * ch),
                       value, size=19 if col > 1 else 21, bold=row in (0, 4),
                       fill=tone, anchor="mm")
    plate.text((1189, 708), "XOR and AND are different Boolean functions", size=18,
               bold=True, fill=GOLD, anchor="mm")
    _footer(plate, "XOR supplies the sum bit while AND supplies the carry bit", size=24)


def _commit(plate: Plate, center: Point, name: str, tone: str, *,
            ring: bool = False, dashed: bool = False) -> None:
    x, y = center
    plate.draw.ellipse((x - 32, y - 32, x + 32, y + 32),
                       fill=hex_rgba(_tint(tone, .58), 245), outline=tone, width=5)
    if ring:
        plate.draw.ellipse((x - 43, y - 43, x + 43, y + 43),
                           outline=tone, width=3)
    plate.text((x, y), name, size=17, bold=True, fill=tone, anchor="mm")
    if dashed:
        for angle in range(0, 360, 45):
            a = math.radians(angle)
            plate.draw.line((x + math.cos(a) * 38, y + math.sin(a) * 38,
                             x + math.cos(a) * 47, y + math.sin(a) * 47),
                            fill=tone, width=3)


def _render_versioncontrol(plate: Plate) -> None:
    """Draw a commit DAG with two evidence gates and non-destructive integration."""

    _tag(plate, (799, 219), "COMMITS FORM A DIRECTED ACYCLIC GRAPH", PLUM)
    _panel(plate, (106, 278, 1494, 748), PLUM)

    positions = {
        "A": (183, 507), "B": (450, 391), "C": (450, 624),
        "B2": (785, 391), "M": (1129, 507),
    }
    edges = (("A", "B", PLUM, ""), ("A", "C", GOLD, ""),
             ("B", "B2", PLUM, "more work"), ("B2", "M", GREEN, "parent 1"),
             ("C", "M", GREEN, "parent 2"))
    for source, target, tone, label in edges:
        sx, sy = positions[source]
        tx, ty = positions[target]
        _arrow(plate, (sx + 42, sy), (tx - 42, ty), tone, label,
               label_dy=-25 if sy <= ty else 25, width=5, head=14)
    for key, (x, y) in positions.items():
        tone = PLUM if key in ("B", "B2") else GOLD if key == "C" else GREEN if key == "M" else BLUE
        _commit(plate, (x, y), key, tone)
    _tag(plate, (785, 305), "checks + review pass", GREEN, size=20)
    _tag(plate, (785, 685), "checks + review pass", GREEN, size=20)
    _value_tile(plate, (1280, 464, 1470, 550), "main / HEAD", BLUE, size=20)
    _arrow(plate, (1275, 507), (1171, 507), BLUE, "points to", label_dy=-30)
    plate.text((183, 576), "base", size=18, bold=True, fill=BLUE, anchor="mm")
    plate.text((450, 320), "feature branch", size=19, bold=True, fill=PLUM, anchor="mm")
    plate.text((450, 696), "bug-fix branch", size=19, bold=True, fill=GOLD, anchor="mm")
    plate.text((1129, 596), "merge commit has two parents", size=19,
               bold=True, fill=GREEN, anchor="mm")
    _footer(plate, "ancestry runs left to right; circles are commits, labels are references", size=24)


def _graph_node(plate: Plate, center: Point, name: str, distance: str,
                tone: str, *, settled: bool = False) -> None:
    x, y = center
    plate.draw.ellipse((x - 55, y - 55, x + 55, y + 55),
                       fill=hex_rgba(_tint(tone, .67), 245), outline=tone, width=6)
    if settled:
        plate.draw.ellipse((x - 44, y - 44, x + 44, y + 44),
                           outline=tone, width=3)
    plate.text((x, y - 11), name, size=25, bold=True, fill=tone, anchor="mm")
    plate.text((x, y + 23), "d=" + distance, size=17, bold=True,
               fill=INK, anchor="mm")


def _weighted_edge(plate: Plate, start: Point, end: Point, weight: int,
                   tone: str = INK_SOFT, *, active: bool = False,
                   offset: Point = (0, -18)) -> None:
    width = 8 if active else 5
    _arrow(plate, start, end, tone, width=width, head=17)
    mx, my = (start[0] + end[0]) / 2 + offset[0], (start[1] + end[1]) / 2 + offset[1]
    plate.draw.ellipse((mx - 21, my - 21, mx + 21, my + 21),
                       fill=PAPER_LIGHT, outline=tone, width=3)
    plate.text((mx, my), str(weight), size=18, bold=True, fill=tone, anchor="mm")


def _render_algorithms_adv(plate: Plate) -> None:
    """Show one correct Dijkstra relaxation and its invariant."""

    _tag(plate, (458, 219), "NONNEGATIVE WEIGHTED GRAPH", BLUE)
    _tag(plate, (1184, 219), "RELAXATION TABLE", GREEN)

    _panel(plate, (104, 275, 865, 755), BLUE)
    pos = {"S": (194, 512), "A": (439, 365), "B": (439, 645), "T": (751, 512)}
    # Edges terminate outside nodes so weights and directions remain legible.
    _weighted_edge(plate, (246, 481), (386, 396), 3, BLUE, active=True)
    _weighted_edge(plate, (246, 543), (386, 614), 5, TEAL, active=True, offset=(0, 24))
    _weighted_edge(plate, (491, 391), (699, 480), 4, CORAL, offset=(0, -18))
    _weighted_edge(plate, (491, 619), (699, 544), 1, GREEN, active=True, offset=(0, 24))
    _graph_node(plate, pos["S"], "S", "0", BLUE, settled=True)
    _graph_node(plate, pos["A"], "A", "3", BLUE, settled=True)
    _graph_node(plate, pos["B"], "B", "5", TEAL, settled=True)
    _graph_node(plate, pos["T"], "T", "6", GREEN, settled=True)
    plate.text((483, 712), "double ring = settled shortest distance", size=19,
               bold=True, fill=BLUE, anchor="mm")

    _panel(plate, (925, 275, 1496, 755), GREEN)
    headers = ("step", "candidate", "d(T)")
    rows = (("start", "unknown", "infinity"), ("via A", "3 + 4", "7"),
            ("via B", "5 + 1", "6  improved"), ("settle T", "minimum", "6"))
    box = (966, 332, 1455, 659)
    cw, ch = _table_grid(plate, box, 5, 3, tone=GREEN)
    for row, cells in enumerate((headers,) + rows):
        for col, value in enumerate(cells):
            tone = GREEN if row in (0, 3, 4) else INK
            plate.text((box[0] + (col + .5) * cw, box[1] + (row + .5) * ch),
                       value, size=18, bold=row in (0, 3, 4), fill=tone, anchor="mm")
    plate.text((1210, 704), "relax when candidate < current", size=21,
               bold=True, fill=GREEN, anchor="mm")
    _footer(plate, "relaxing B -> T lowers the tentative distance from 7 to 6", size=25)


def _transition(plate: Plate, start: Point, end: Point, label: str,
                *, bend: float = 0, tone: str = INK_SOFT) -> None:
    sx, sy = start
    ex, ey = end
    if bend:
        mx, my = (sx + ex) / 2, (sy + ey) / 2 + bend
        # Quadratic Bezier approximation keeps reciprocal transitions separate.
        points = []
        for i in range(21):
            t = i / 20
            points.append(((1 - t) ** 2 * sx + 2 * (1 - t) * t * mx + t * t * ex,
                           (1 - t) ** 2 * sy + 2 * (1 - t) * t * my + t * t * ey))
        plate.draw.line(points, fill=tone, width=5, joint="curve")
        _arrow(plate, points[-2], points[-1], tone, width=5, head=15)
        ly = my + (-18 if bend < 0 else 18)
        plate.text((mx, ly), label, size=19, bold=True, fill=tone, anchor="mm")
    else:
        _arrow(plate, start, end, tone, label, width=5, head=15)


def _render_theory(plate: Plate) -> None:
    """Trace a DFA that recognizes exactly binary strings ending in 01."""

    _tag(plate, (487, 219), "DFA: LANGUAGE = STRINGS ENDING IN 01", PLUM)
    _tag(plate, (1250, 219), "TRACE INPUT 1101", GREEN)
    _panel(plate, (103, 275, 963, 753), PLUM)
    q0, q1, q2 = (263, 514), (529, 371), (795, 514)
    _arrow(plate, (126, 514), (202, 514), INK, "start", width=5, head=15)
    _node(plate, q0, "q0", BLUE, radius=59)
    _node(plate, q1, "q1", GOLD, radius=59)
    _node(plate, q2, "q2", GREEN, radius=59, double=True)
    plate.text((263, 594), "other suffix", size=17, bold=True, fill=BLUE, anchor="mm")
    plate.text((529, 291), "last symbol 0", size=17, bold=True, fill=GOLD, anchor="mm")
    plate.text((795, 594), "suffix 01 / ACCEPT", size=17, bold=True, fill=GREEN, anchor="mm")
    _transition(plate, (317, 485), (478, 400), "0", bend=-30, tone=GOLD)
    _transition(plate, (575, 408), (748, 483), "1", bend=-24, tone=GREEN)
    _transition(plate, (740, 534), (318, 534), "1", bend=94, tone=BLUE)
    _transition(plate, (762, 461), (562, 397), "0", bend=-68, tone=GOLD)
    # Self-loops are deliberately labelled and shaped, not just colour-coded.
    plate.draw.arc((190, 415, 316, 531), 177, 351, fill=BLUE, width=5)
    plate.text((226, 413), "1", size=20, bold=True, fill=BLUE, anchor="mm")
    plate.draw.arc((473, 300, 585, 408), 180, 355, fill=GOLD, width=5)
    plate.text((529, 298), "0", size=20, bold=True, fill=GOLD, anchor="mm")
    plate.text((530, 703), "each state summarizes only the suffix needed for the next decision",
               size=18, bold=True, fill=PLUM, anchor="mm")

    _panel(plate, (1012, 275, 1496, 753), GREEN)
    trace = (("start", "q0", ""), ("read 1", "q0", "other"),
             ("read 1", "q0", "other"), ("read 0", "q1", "last 0"),
             ("read 1", "q2", "ends 01"))
    for row, (action, state, reason) in enumerate(trace):
        y = 328 + row * 80
        tone = GREEN if state == "q2" else GOLD if state == "q1" else BLUE
        _node(plate, (1090, y), state, tone, radius=29,
              double=state == "q2", size=16)
        plate.text((1142, y - 10), action, size=19, bold=True, fill=INK, anchor="lm")
        plate.text((1322, y + 19), reason, size=16, fill=INK_SOFT, anchor="mm")
        if row < 4:
            _arrow(plate, (1090, y + 32), (1090, y + 47), tone, width=4, head=10)
    plate.text((1254, 716), "final state q2 is double-ringed: accept", size=18,
               bold=True, fill=GREEN, anchor="mm")
    _footer(plate, "1101 ends in 01, so its trace finishes in accepting state q2", size=24)


def _render_os(plate: Plate) -> None:
    """Connect scheduling, address translation, and checked I/O mediation."""

    _tag(plate, (360, 219), "ONE CPU, TWO PROCESSES", CORAL)
    _tag(plate, (1004, 219), "VIRTUAL -> PHYSICAL MEMORY", BLUE)
    _tag(plate, (1390, 219), "CHECKED I/O", GREEN)

    _panel(plate, (103, 275, 657, 754), CORAL)
    plate.text((380, 315), "scheduler timeline (milliseconds)", size=19,
               bold=True, fill=CORAL, anchor="mm")
    x0, x1, y = 150, 610, 431
    segments = (("P1", 5, BLUE), ("P2", 5, GOLD), ("P1", 5, BLUE), ("P2", 5, GOLD))
    cursor = x0
    for index, (name, duration, tone) in enumerate(segments):
        width = (x1 - x0) / len(segments)
        plate.draw.rectangle((cursor, y - 44, cursor + width, y + 44),
                             fill=hex_rgba(_tint(tone, .55), 245), outline=tone, width=4)
        plate.text((cursor + width / 2, y), name, size=22, bold=True,
                   fill=tone, anchor="mm")
        plate.text((cursor, y + 71), str(index * 5), size=16,
                   fill=INK_SOFT, anchor="mm")
        cursor += width
    plate.text((x1, y + 71), "20", size=16, fill=INK_SOFT, anchor="mm")
    _center_lines(plate, (380, 610),
                  ("timer interrupt returns control to kernel", "scheduler selects the next runnable process",
                   "context switch restores that process state"), size=18, gap=13, bold=True)

    _panel(plate, (703, 275, 1266, 754), BLUE)
    for col, heading in enumerate(("P1 virtual pages", "page table", "physical frames")):
        plate.text((784 + col * 198, 318), heading, size=17, bold=True,
                   fill=(BLUE, PLUM, TEAL)[col], anchor="mm")
    for row in range(3):
        y = 390 + row * 104
        _value_tile(plate, (739, y - 31, 829, y + 31), "v" + str(row), BLUE, size=19)
        _value_tile(plate, (936, y - 31, 1026, y + 31),
                    "-> f" + str((2, 5, 1)[row]), PLUM, size=18)
    for frame in range(6):
        y = 357 + frame * 56
        tone = TEAL if frame in (1, 2, 5) else INK_SOFT
        plate.draw.rectangle((1124, y, 1210, y + 44),
                             fill=hex_rgba(_tint(tone, .72), 235), outline=tone, width=3)
        plate.text((1167, y + 22), "f" + str(frame), size=17, bold=True,
                   fill=tone, anchor="mm")
    for row, frame in enumerate((2, 5, 1)):
        _arrow(plate, (1031, 390 + row * 104), (1115, 379 + frame * 56),
               TEAL, width=4, head=12)
    plate.text((985, 711), "mapping + permissions isolate address spaces", size=17,
               bold=True, fill=BLUE, anchor="mm")

    _panel(plate, (1311, 275, 1497, 754), GREEN)
    for row, (label, shape, tone) in enumerate((("P1", "square", BLUE),
                                                ("syscall", "diamond", CORAL),
                                                ("kernel", "square", PLUM),
                                                ("device", "circle", GREEN))):
        y = 345 + row * 105
        _node(plate, (1404, y), label, tone, radius=37, shape=shape, size=16)
        if row < 3:
            _arrow(plate, (1404, y + 40), (1404, y + 63), tone,
                   width=4, head=11)
    _footer(plate, "the kernel time-slices CPU, translates memory, and validates device access", size=22)


def _render_databases_adv(plate: Plate) -> None:
    """Distinguish indexing, atomicity, and replication as separate mechanisms."""

    _tag(plate, (306, 219), "INDEX: FEWER PAGE READS", BLUE)
    _tag(plate, (802, 219), "TRANSACTION: ATOMIC", PLUM)
    _tag(plate, (1300, 219), "REPLICATION: VISIBILITY RULE", TEAL)

    _panel(plate, (103, 278, 510, 755), BLUE)
    _node(plate, (306, 350), "root", BLUE, radius=42, shape="square")
    for index, label in enumerate(("< 40", "40..79", ">= 80")):
        x = 180 + index * 126
        _node(plate, (x, 495), label, TEAL if index == 1 else INK_SOFT,
              radius=42, shape="square", size=16)
        _arrow(plate, (306, 394), (x, 449), TEAL if index == 1 else INK_SOFT,
               width=6 if index == 1 else 3, head=13)
    for index, value in enumerate((42, 57, 73)):
        x = 180 + index * 126
        _value_tile(plate, (x - 38, 607, x + 38, 674), str(value), TEAL,
                    sub="leaf", size=19)
    _arrow(plate, (306, 539), (306, 598), TEAL, "find key 57", label_dy=-12)
    plate.text((306, 718), "root -> branch -> leaf", size=19,
               bold=True, fill=BLUE, anchor="mm")

    _panel(plate, (554, 278, 1050, 755), PLUM)
    balances = (("BEFORE", "$100", "$50"), ("AFTER COMMIT", "$90", "$60"))
    for col, (heading, a, b) in enumerate(balances):
        x = 682 + col * 244
        plate.text((x, 339), heading, size=18, bold=True, fill=PLUM, anchor="mm")
        _value_tile(plate, (x - 82, 381, x + 82, 451), "A = " + a, PLUM, size=19)
        _value_tile(plate, (x - 82, 475, x + 82, 545), "B = " + b, PLUM, size=19)
        plate.text((x, 566), "total = $150", size=18, bold=True,
                   fill=GREEN, anchor="mm")
    _arrow(plate, (765, 607), (844, 607), PLUM, width=5, head=14)
    _code(plate, (632, 636, 972, 691), "COMMIT both  |  ABORT both", tone=PLUM,
          active=True, size=18)
    plate.text((802, 723), "declared invariant remains true", size=17,
               bold=True, fill=PLUM, anchor="mm")

    _panel(plate, (1094, 278, 1497, 755), TEAL)
    logs = (("leader", (40, 41, 42)), ("replica A", (40, 41, 42)),
            ("replica B", (40, 41, None)))
    for row, (name, entries) in enumerate(logs):
        y = 357 + row * 115
        plate.text((1120, y), name, size=18, bold=True, fill=INK, anchor="lm")
        for col, entry in enumerate(entries):
            x = 1302 + col * 67
            tone = TEAL if entry is not None else CORAL
            _value_tile(plate, (x - 28, y - 28, x + 28, y + 28),
                        str(entry) if entry is not None else "--", tone, size=16)
    plate.text((1362, 630), "entry 42 stored on 2 of 3", size=17,
               bold=True, fill=TEAL, anchor="mm")
    plate.text((1296, 696), "visibility follows the protocol's ack rule", size=16,
               bold=True, fill=INK_SOFT, anchor="mm")
    _footer(plate, "indexes, atomic transactions, and replication solve different database problems", size=22)


def _point(plate: Plate, xy: Point, cls: str, *, train: bool = True) -> None:
    x, y = xy
    tone = BLUE if cls == "A" else CORAL
    if cls == "A":
        plate.draw.ellipse((x - 9, y - 9, x + 9, y + 9),
                           fill=tone if train else PAPER_LIGHT, outline=tone, width=4)
    else:
        plate.draw.polygon(((x, y - 12), (x + 11, y + 10), (x - 11, y + 10)),
                           fill=tone if train else PAPER_LIGHT, outline=tone)
        plate.draw.line((x, y - 12, x + 11, y + 10, x - 11, y + 10, x, y - 12),
                        fill=tone, width=3)


def _render_ml(plate: Plate) -> None:
    """Visualize a proper train/test split, fitted boundary, and held-out errors."""

    _tag(plate, (346, 219), "LABELLED SAMPLE", BLUE)
    _tag(plate, (798, 219), "FIT ON TRAIN ONLY", PLUM)
    _tag(plate, (1260, 219), "EVALUATE HELD-OUT", GREEN)

    panels = ((103, 277, 547, 752), (578, 277, 1022, 752), (1053, 277, 1497, 752))
    for index, box in enumerate(panels):
        _panel(plate, box, (BLUE, PLUM, GREEN)[index])
    base_points = (((168, 622), "A"), ((221, 558), "A"), ((276, 611), "A"),
                   ((329, 524), "A"), ((374, 577), "A"), ((410, 482), "A"),
                   ((248, 438), "B"), ((310, 396), "B"), ((361, 435), "B"),
                   ((430, 356), "B"), ((467, 414), "B"), ((489, 338), "B"))
    for xy, cls in base_points:
        _point(plate, xy, cls)
    plate.text((325, 698), "circle = class A   triangle = class B", size=17,
               bold=True, fill=BLUE, anchor="mm")
    _arrow(plate, (555, 514), (570, 514), PLUM, width=4, head=11)

    # Training panel reuses only eight filled points; held-out examples are absent.
    for (xy, cls), (dx, dy) in zip(base_points[:8], ((510, 0),) * 8):
        _point(plate, (xy[0] + dx, xy[1]), cls, train=True)
    plate.draw.line((646, 648, 948, 339), fill=PLUM, width=7)
    plate.text((800, 324), "learned boundary", size=19, bold=True,
               fill=PLUM, anchor="mm")
    plate.text((800, 690), "update parameters to reduce training loss", size=17,
               bold=True, fill=PLUM, anchor="mm")

    test_points = (((1125, 646), "A", True), ((1188, 600), "A", True),
                   ((1265, 450), "A", False), ((1331, 380), "B", True),
                   ((1404, 330), "B", True), ((1450, 420), "B", False))
    for xy, cls, correct in test_points:
        _point(plate, xy, cls, train=False)
        if not correct:
            plate.draw.line((xy[0] - 16, xy[1] - 16, xy[0] + 16, xy[1] + 16),
                            fill=CORAL, width=5)
            plate.draw.line((xy[0] - 16, xy[1] + 16, xy[0] + 16, xy[1] - 16),
                            fill=CORAL, width=5)
    plate.draw.line((1102, 648, 1458, 300), fill=PLUM, width=5)
    plate.text((1275, 321), "frozen boundary", size=18, bold=True,
               fill=GREEN, anchor="mm")
    plate.text((1275, 676), "4 correct / 6 = 67%   |   2 marked errors", size=18,
               bold=True, fill=GREEN, anchor="mm")
    plate.text((1275, 713), "open symbols were never used for fitting", size=16,
               fill=INK_SOFT, anchor="mm")
    _footer(plate, "held-out labels measure generalization only if they never tune the model", size=22)


def _render_security(plate: Plate) -> None:
    """Contrast authenticated encryption with hashing under an explicit attacker."""

    _tag(plate, (399, 219), "AUTHENTICATED ENCRYPTION", BLUE)
    _tag(plate, (965, 219), "HASH FOR INTEGRITY", PLUM)
    _tag(plate, (1345, 219), "THREAT MODEL", CORAL)

    _panel(plate, (103, 278, 735, 754), BLUE)
    _value_tile(plate, (135, 352, 301, 433), "PAY 10", TEAL, sub="plaintext", size=21)
    _value_tile(plate, (135, 526, 321, 607), "K secret + N7 unique", GOLD,
                sub="nonce may be public", size=14)
    _arrow(plate, (312, 392), (407, 467), BLUE, "Enc", label_dy=-28)
    _arrow(plate, (312, 566), (407, 491), BLUE, width=5, head=14)
    _node(plate, (472, 479), "AEAD", BLUE, radius=54, shape="diamond", size=19)
    _arrow(plate, (533, 479), (593, 479), BLUE, width=6, head=16)
    _value_tile(plate, (590, 409, 715, 549), "CIPHERTEXT\n+ TAG", BLUE,
                sub="", size=18)
    plate.text((652, 584), "encrypted", size=17, fill=BLUE, anchor="mm")
    plate.text((652, 610), "+ integrity tag", size=17, fill=BLUE, anchor="mm")
    plate.text((419, 659), "receiver verifies tag before accepting plaintext", size=18,
               bold=True, fill=BLUE, anchor="mm")
    plate.text((419, 704), "sender must never reuse a nonce where the scheme forbids it", size=15,
               fill=CORAL, anchor="mm")

    _panel(plate, (766, 278, 1165, 754), PLUM)
    _code(plate, (796, 351, 1135, 415), "Hash(message) -> digest", tone=PLUM,
          active=True, size=19)
    digest = ("9A", "2F", "71", "C0", "8D", "44")
    for index, byte in enumerate(digest):
        x = 820 + index * 56
        _value_tile(plate, (x - 23, 472, x + 23, 524), byte, PLUM, size=14)
    plate.text((965, 582), "same input -> same digest", size=19,
               bold=True, fill=PLUM, anchor="mm")
    plate.text((965, 626), "not reversible encryption", size=19,
               bold=True, fill=CORAL, anchor="mm")
    plate.text((965, 690), "use a MAC or signature against active editing", size=15,
               fill=INK_SOFT, anchor="mm")

    _panel(plate, (1195, 278, 1497, 754), CORAL)
    threat = (("1", "CAN read network", CORAL), ("2", "CAN alter packets", CORAL),
              ("3", "CANNOT obtain K", GREEN), ("4", "protocol rejects replay", GOLD))
    for row, (number, detail, tone) in enumerate(threat):
        y = 350 + row * 91
        _node(plate, (1241, y), number, tone, radius=25, shape="square", size=15)
        plate.text((1280, y), detail, size=16, bold=True, fill=INK, anchor="lm")
    plate.text((1346, 711), "goal: confidential + authentic", size=16,
               bold=True, fill=CORAL, anchor="mm")
    _footer(plate, "choose a cryptographic primitive only after naming property and attacker", size=23)


def _render_systems(plate: Plate) -> None:
    """Trace pointer creation, dereference, mutation, and an invalid lifetime."""

    _tag(plate, (333, 219), "C-LIKE PROGRAM", BLUE)
    _tag(plate, (962, 219), "MEMORY AFTER EACH LINE", PLUM)
    _tag(plate, (1382, 219), "VALIDITY", CORAL)

    _panel(plate, (103, 276, 594, 756), BLUE)
    code = (("1", "int x = 42;"), ("2", "int *p = &x;"),
            ("3", "*p = 43;"), ("4", 'printf("%d", x);'))
    for row, (num, line) in enumerate(code):
        y = 335 + row * 91
        _node(plate, (158, y), num, BLUE if row < 2 else PLUM,
              radius=26, shape="square", size=16)
        _code(plate, (202, y - 29, 552, y + 29), line,
              tone=PLUM if row == 2 else BLUE, active=row == 2, size=20)
    plate.text((349, 705), "line 3 writes through the address in p", size=18,
               bold=True, fill=BLUE, anchor="mm")

    _panel(plate, (637, 276, 1268, 756), PLUM)
    # Memory cells share an address, making aliasing explicit.
    plate.text((707, 326), "address", size=18, bold=True, fill=PLUM, anchor="mm")
    plate.text((925, 326), "object", size=18, bold=True, fill=PLUM, anchor="mm")
    plate.text((1144, 326), "stored value", size=18, bold=True, fill=PLUM, anchor="mm")
    _value_tile(plate, (655, 367, 780, 447), "0x1000", BLUE, sub="live", size=18)
    _value_tile(plate, (829, 367, 1021, 447), "int x", PLUM, sub="same cell", size=20)
    _value_tile(plate, (1070, 367, 1218, 447), "42 -> 43", GREEN, sub="line 3", size=20)
    _value_tile(plate, (655, 522, 780, 602), "0x2000", BLUE, sub="p lives here", size=17)
    _value_tile(plate, (829, 522, 1021, 602), "int *p", PLUM, sub="typed address", size=19)
    _value_tile(plate, (1070, 522, 1218, 602), "0x1000", BLUE, sub="points to x", size=18)
    _arrow(plate, (1144, 515), (786, 446), BLUE, "dereference *p", label_dy=-27)
    plate.text((952, 687), "x and *p name the same live integer object", size=19,
               bold=True, fill=PLUM, anchor="mm")

    _panel(plate, (1311, 276, 1497, 756), CORAL)
    rules = (("1", "correct type"), ("2", "inside bounds"),
             ("3", "object still alive"))
    for row, (num, rule) in enumerate(rules):
        y = 348 + row * 106
        _node(plate, (1362, y), num, GREEN, radius=27, shape="square", size=16)
        _center_lines(plate, (1430, y), tuple(rule.split()), size=15, gap=4,
                      bold=True, fill=INK)
    plate.draw.line((1335, 650, 1473, 650), fill=CORAL, width=5)
    plate.text((1404, 684), "otherwise:", size=16,
               bold=True, fill=CORAL, anchor="mm")
    plate.text((1404, 711), "undefined behavior", size=15,
               bold=True, fill=CORAL, anchor="mm")
    _footer(plate, "a pointer is a typed address; dereference is valid only within lifetime and bounds", size=22)


def _heat_cell(plate: Plate, box: Box, value: float, *, selected: bool = False) -> None:
    # Tone intensity is duplicated by a numeric weight and the selected outline.
    tone = GOLD if value >= .5 else BLUE
    alpha = int(42 + value * 170)
    x0, y0, x1, y1 = box
    plate.draw.rectangle(box, fill=hex_rgba(tone, alpha),
                         outline=GREEN if selected else hex_rgba(GRID, 180),
                         width=5 if selected else 2)
    plate.text(((x0 + x1) / 2, (y0 + y1) / 2), "{:.2f}".format(value),
               size=16, bold=True, fill=INK, anchor="mm")


def _render_deep_learning(plate: Plate) -> None:
    """Make contextual attention and the loss-to-gradient update concrete."""

    _tag(plate, (283, 219), "TOKEN REPRESENTATIONS", BLUE)
    _tag(plate, (792, 219), "ATTENTION WEIGHTS", GOLD)
    _tag(plate, (1300, 219), "PREDICTION + UPDATE", GREEN)

    _panel(plate, (102, 278, 508, 755), BLUE)
    tokens = (("river", "v1"), ("bank", "v2"), ("was", "v3"), ("steep", "v4"))
    for row, (token, vector) in enumerate(tokens):
        y = 338 + row * 89
        _value_tile(plate, (136, y - 31, 292, y + 31), token, BLUE,
                    sub="token", size=20)
        _arrow(plate, (302, y), (354, y), BLUE, width=4, head=11)
        _value_tile(plate, (364, y - 31, 472, y + 31), vector, TEAL,
                    sub="vector", size=19)
    plate.text((305, 716), "tokens + positions become vectors", size=17,
               bold=True, fill=BLUE, anchor="mm")

    _panel(plate, (552, 278, 1037, 755), GOLD)
    matrix = (
        (.55, .24, .11, .10),
        (.58, .17, .10, .15),
        (.18, .46, .25, .11),
        (.23, .44, .09, .24),
    )
    x0, y0, cell = 657, 357, 72
    for col, (token, _) in enumerate(tokens):
        plate.text((x0 + col * cell + cell / 2, 326), token, size=15,
                   bold=True, fill=INK_SOFT, anchor="mm")
    for row, (token, _) in enumerate(tokens):
        plate.text((628, y0 + row * cell + cell / 2), token, size=15,
                   bold=True, fill=INK_SOFT, anchor="rm")
        for col, value in enumerate(matrix[row]):
            _heat_cell(plate, (x0 + col * cell, y0 + row * cell,
                               x0 + (col + 1) * cell, y0 + (row + 1) * cell),
                       value, selected=(row == 1 and col == 0))
    plate.text((794, 675), "bank attends strongly to river: 0.58", size=18,
               bold=True, fill=GOLD, anchor="mm")
    plate.text((794, 713), "each row sums to 1.00 in this toy head", size=16,
               fill=INK_SOFT, anchor="mm")

    _panel(plate, (1081, 278, 1498, 755), GREEN)
    _code(plate, (1118, 333, 1460, 393), "P(next = green) = 0.22", tone=GREEN,
          active=True, size=18)
    _code(plate, (1118, 420, 1460, 480), "target next = green", tone=BLUE,
          size=18)
    _arrow(plate, (1289, 515), (1289, 546), CORAL)
    plate.text((1289, 499), "cross-entropy loss", size=18,
               bold=True, fill=CORAL, anchor="mm")
    _node(plate, (1289, 596), "L=1.51", CORAL, radius=47, shape="diamond", size=18)
    _arrow(plate, (1241, 621), (1180, 656), PLUM)
    plate.text((1370, 644), "gradient", size=18, bold=True, fill=PLUM, anchor="mm")
    plate.text((1290, 680), "theta <- theta - eta * grad L", size=18,
               bold=True, math_face=True, fill=PLUM, anchor="mm")
    plate.text((1289, 719), "only training updates parameters", size=15,
               bold=True, fill=GREEN, anchor="mm")
    _footer(plate, "attention mixes context; prediction loss supplies gradients for parameter updates", size=22)


def _log_row(plate: Plate, y: float, name: str, entries: Sequence[int | None],
             tone: str, *, offline: bool = False) -> None:
    plate.text((182, y - 14 if offline else y), name, size=20, bold=True,
               fill=CORAL if offline else tone, anchor="lm")
    if offline:
        plate.text((182, y + 16), "OFFLINE", size=17, bold=True,
                   fill=CORAL, anchor="lm")
    for index, entry in enumerate(entries):
        x = 443 + index * 119
        label = "--" if entry is None else str(entry)
        box = (x - 44, y - 35, x + 44, y + 35)
        _value_tile(plate, box, label, CORAL if entry is None else tone,
                    crossed=offline and entry is None, size=19)


def _render_distributed(plate: Plate) -> None:
    """Trace one Raft-like majority commit without overstating the protocol."""

    _tag(plate, (467, 219), "REPLICATED LOG / TERM 8", BLUE)
    _tag(plate, (1247, 219), "COMMIT RULE", GREEN)

    _panel(plate, (103, 276, 1030, 755), BLUE)
    plate.text((263, 316), "node / index", size=17, bold=True,
               fill=INK_SOFT, anchor="mm")
    for index, entry in enumerate((40, 41, 42)):
        plate.text((443 + index * 119, 316), str(entry), size=17,
                   bold=True, fill=INK_SOFT, anchor="mm")
    _log_row(plate, 390, "leader L", (40, 41, 42), BLUE)
    _log_row(plate, 510, "follower F1", (40, 41, 42), TEAL)
    _log_row(plate, 630, "follower F2", (40, 41, None), CORAL, offline=True)
    plate.text((866, 390), "append x=7", size=18, bold=True, fill=BLUE, anchor="lm")
    plate.text((866, 510), "ACK 42", size=18, bold=True, fill=TEAL, anchor="lm")
    plate.text((866, 630), "no reply", size=18, bold=True, fill=CORAL, anchor="lm")
    _arrow(plate, (786, 410), (786, 483), TEAL, width=5, head=14)
    plate.text((806, 447), "replicate", size=19, bold=True, fill=TEAL, anchor="lm")
    plate.text((566, 707), "entry 42 is stored on L + F1 = 2 of 3 nodes", size=19,
               bold=True, fill=BLUE, anchor="mm")

    _panel(plate, (1073, 276, 1498, 755), GREEN)
    _node(plate, (1285, 368), "2 / 3", GREEN, radius=65, double=True, size=25)
    plate.text((1285, 454), "majority reached", size=20, bold=True,
               fill=GREEN, anchor="mm")
    plate.text((1285, 494), "leader marks index 42", size=19,
               bold=True, fill=GREEN, anchor="mm")
    _arrow(plate, (1285, 515), (1285, 545), GREEN, head=12)
    _value_tile(plate, (1168, 570, 1402, 655), "COMMIT  x=7", GREEN,
                sub="apply in log order", size=23)
    plate.text((1285, 705), "any two majorities share at least one node", size=17,
               bold=True, fill=GREEN, anchor="mm")
    _footer(plate, "a 2-of-3 quorum permits progress with one node offline; full safety needs all protocol rules", size=21)


def _judgement(plate: Plate, box: Box, premise: str, conclusion: str,
               tone: str, *, name: str) -> None:
    _panel(plate, box, tone, radius=15, alpha=230, width=3)
    x0, y0, x1, y1 = box
    plate.text((x0 + 16, y0 + 17), name, size=16, bold=True, fill=tone, anchor="la")
    plate.text(((x0 + x1) / 2, y0 + 49), premise, size=18,
               math_face=True, fill=INK, anchor="mm")
    plate.draw.line((x0 + 35, y0 + 71, x1 - 35, y0 + 71), fill=tone, width=3)
    plate.text(((x0 + x1) / 2, y0 + 98), conclusion, size=19,
               bold=True, math_face=True, fill=tone, anchor="mm")


def _render_pl_theory(plate: Plate) -> None:
    """Separate static typing from the small-step operational reduction."""

    _tag(plate, (447, 219), "STATIC TYPE DERIVATION", BLUE)
    _tag(plate, (1173, 219), "OPERATIONAL SEMANTICS", PLUM)

    _panel(plate, (103, 276, 791, 755), BLUE)
    plate.text((447, 314), "term: (lambda x:Int. x + 1) 4", size=22,
               bold=True, math_face=True, fill=BLUE, anchor="mm")
    _judgement(plate, (145, 357, 464, 476), "x : Int    1 : Int",
               "x + 1 : Int", BLUE, name="T-ADD")
    _judgement(plate, (487, 357, 749, 476), "4 is an integer literal",
               "4 : Int", TEAL, name="T-INT")
    _judgement(plate, (216, 522, 678, 649), "x:Int entails x+1:Int",
               "lambda x:Int. x+1 : Int -> Int", PLUM, name="T-ABS")
    _arrow(plate, (447, 658), (447, 689), GREEN, width=4, head=11)
    plate.text((447, 713), "whole application : Int", size=21,
               bold=True, fill=GREEN, anchor="mm")

    _panel(plate, (835, 276, 1497, 755), PLUM)
    reductions = (("E-APP", "(lambda x:Int. x+1) 4"),
                  ("beta", "[4/x](x+1)"),
                  ("substitute", "4 + 1"),
                  ("arithmetic", "5 : Int"))
    for row, (rule, term) in enumerate(reductions):
        y = 348 + row * 105
        tone = GREEN if row == 3 else PLUM if row in (1, 2) else BLUE
        _tag(plate, (918, y), rule, tone, size=15)
        _code(plate, (1010, y - 32, 1455, y + 32), term, tone=tone,
              active=row == 3, size=20)
        if row < 3:
            _arrow(plate, (1232, y + 34), (1232, y + 68), tone,
                   width=4, head=11)
    plate.text((1166, 716), "preservation: every step remains type Int", size=18,
               bold=True, fill=GREEN, anchor="mm")
    _footer(plate, "typing predicts a valid result class; semantics explains each evaluation step", size=23)


def _amplitude_bar(plate: Plate, x: float, baseline: float, value: float,
                   label: str, tone: str, *, contribution: str = "") -> None:
    scale = 115
    y = baseline - value * scale
    plate.draw.line((x, baseline, x, y), fill=tone, width=18)
    plate.draw.line((x - 22, baseline, x + 22, baseline), fill=INK_SOFT, width=3)
    plate.text((x, baseline + 30), label, size=18, bold=True, fill=INK, anchor="mm")
    plate.text((x, y - (18 if value >= 0 else -18)),
               "+" if value > 0 else "-" if value < 0 else "0",
               size=21, bold=True, fill=tone, anchor="mm")
    if contribution:
        plate.text((x, baseline + 57), contribution, size=14,
                   fill=INK_SOFT, anchor="mm")


def _render_quantum(plate: Plate) -> None:
    """Show signed amplitudes through H twice and why one outcome cancels."""

    _tag(plate, (275, 219), "PREPARE |0>", BLUE)
    _tag(plate, (790, 219), "FIRST HADAMARD", PLUM)
    _tag(plate, (1310, 219), "SECOND H: INTERFERENCE", GREEN)
    panels = ((103, 278, 458, 755), (497, 278, 1053, 755), (1092, 278, 1497, 755))
    for index, box in enumerate(panels):
        _panel(plate, box, (BLUE, PLUM, GREEN)[index])

    plate.text((280, 335), "amplitude vector (1, 0)", size=20,
               bold=True, fill=BLUE, anchor="mm")
    _amplitude_bar(plate, 220, 590, 1.0, "|0>", BLUE)
    _amplitude_bar(plate, 340, 590, 0.0, "|1>", CORAL)
    plate.text((280, 685), "P(0)=1    P(1)=0", size=20,
               bold=True, fill=BLUE, anchor="mm")

    plate.text((775, 331), "H|0> = (|0> + |1>) / sqrt(2)", size=20,
               bold=True, math_face=True, fill=PLUM, anchor="mm")
    _amplitude_bar(plate, 684, 590, .707, "|0>", PLUM, contribution="+1/sqrt(2)")
    _amplitude_bar(plate, 866, 590, .707, "|1>", PLUM, contribution="+1/sqrt(2)")
    plate.text((775, 685), "P(0)=1/2    P(1)=1/2", size=20,
               bold=True, fill=PLUM, anchor="mm")

    plate.text((1294, 327), "path contributions after H", size=19,
               bold=True, fill=GREEN, anchor="mm")
    # Contribution equations retain signs; cancellation is not inferred from colour.
    _code(plate, (1125, 371, 1465, 431), "to |0>:  +1/2 + 1/2 = 1", tone=GREEN,
          active=True, size=18)
    _code(plate, (1125, 464, 1465, 524), "to |1>:  +1/2 - 1/2 = 0", tone=CORAL,
          active=True, size=18)
    plate.draw.line((1142, 558, 1448, 558), fill=GREEN, width=4)
    _amplitude_bar(plate, 1235, 665, 1.0, "|0>", GREEN)
    _amplitude_bar(plate, 1370, 665, 0.0, "|1>", CORAL)
    plate.text((1297, 723), "H x H = I; measure 0 with probability 1", size=17,
               bold=True, fill=GREEN, anchor="mm")
    _footer(plate, "signed amplitudes interfere: paths to |0> add while paths to |1> cancel", size=23)


def _render_frontier(plate: Plate) -> None:
    """Join specification, bounded proof, runtime testing, and counterexample repair."""

    _tag(plate, (800, 219), "RESEARCH LOOP: CLAIM -> EVIDENCE -> REVISION", GOLD)
    center = (800, 500)
    steps = (
        ((800, 314), "1", "CLAIM", "allocator never gives\ntwo owners one block", BLUE, "square"),
        ((1162, 460), "2", "FORMALIZE", "state model + invariant\nowner_count <= 1", PLUM, "diamond"),
        ((1026, 686), "3", "VERIFY MODEL", "bounded proof checks\nall modeled states", GREEN, "square"),
        ((574, 686), "4", "TEST SYSTEM", "adversarial schedule\nruns implementation", TEAL, "square"),
        ((438, 460), "5", "COUNTEREXAMPLE", "race: check and set\ninterleave", CORAL, "diamond"),
    )
    for position, number, heading, detail, tone, shape in steps:
        x, y = position
        _panel(plate, (x - 167, y - 70, x + 167, y + 70), tone, radius=18)
        _node(plate, (x - 124, y), number, tone, radius=25, shape=shape, size=15)
        plate.text((x - 82, y - 29), heading, size=18, bold=True,
                   fill=tone, anchor="lm")
        for line_no, line in enumerate(detail.split("\n")):
            plate.text((x - 82, y + 4 + line_no * 25), line, size=16,
                       fill=INK, anchor="lm")
    # Clockwise evidence arrows plus a return edge from counterexample to claim.
    links = ((0, 1, BLUE, "specify"), (1, 2, PLUM, "prove"),
             (2, 3, GREEN, "implement"), (3, 4, TEAL, "find"),
             (4, 0, CORAL, "revise claim / design"))
    for source, target, tone, label in links:
        sx, sy = steps[source][0]
        tx, ty = steps[target][0]
        dx, dy = tx - sx, ty - sy
        distance = math.hypot(dx, dy)
        ux, uy = dx / distance, dy / distance
        _arrow(plate, (sx + ux * 174, sy + uy * 76),
               (tx - ux * 174, ty - uy * 76), tone, label,
               label_dy=-18 if source in (0, 1) else 22, width=5, head=14)
    plate.draw.rounded_rectangle((650, 442, 950, 568), radius=24,
                                 fill=hex_rgba(GOLD_LIGHT, 150), outline=GOLD, width=4)
    plate.text((800, 476), "ASSUMPTIONS", size=19, bold=True, fill=GOLD, anchor="mm")
    _center_lines(plate, (800, 526), ("memory model", "scheduler + bounds"),
                  size=17, gap=5, bold=True)
    _footer(plate, "proof covers the stated model; tests probe the implementation; counterexamples refine both", size=21)


def _render_complexity(plate: Plate) -> None:
    """Expose exact scaling and an independently checkable SAT witness."""
    _tag(plate, (439, 219), "GROWTH: EXACT COUNTS", BLUE)
    _tag(plate, (1142, 219), "VERIFY A CERTIFICATE", GREEN)
    _panel(plate, (103, 278, 775, 765), BLUE)
    _panel(plate, (814, 278, 1497, 765), GREEN)
    columns = (190, 355, 510, 680)
    for x, label in zip(columns, ('n', 'n', 'n squared', '2 to n')):
        plate.text((x, 325), label, size=23, bold=True, fill=BLUE, anchor='mm')
    for row, n in enumerate((4, 8, 16)):
        y = 415 + row * 94
        for x, value in zip(columns, (n, n, n*n, 2**n)):
            _value_tile(plate, (x-60, y-32, x+60, y+32), str(value), BLUE, size=24)
    plate.text((439, 700), 'doubling n: linear x2; quadratic x4', size=22,
               bold=True, fill=BLUE, anchor='mm')
    plate.text((439, 735), 'exponential: 16 -> 256 -> 65,536', size=21,
               fill=INK_SOFT, anchor='mm')
    _code(plate, (845, 309, 1465, 373), 'witness: x = true, y = false', tone=GREEN, size=23)
    clauses = (('(x OR y)', 'T OR F = T'),
               ('(NOT x OR NOT y)', 'F OR T = T'),
               ('(x OR NOT y)', 'T OR T = T'))
    for row, (clause, result) in enumerate(clauses):
        y = 437 + row * 87
        plate.text((849, y), clause, size=22, fill=INK, anchor='lm')
        plate.text((1445, y), result, size=21, bold=True, fill=GREEN, anchor='rm')
    plate.text((1155, 697), 'AND all clauses: TRUE', size=24,
               bold=True, fill=GREEN, anchor='mm')
    plate.text((1155, 735), 'scan the formula to check this witness', size=21,
               fill=INK_SOFT, anchor='mm')
    _footer(plate, 'checking a supplied solution is different from finding one', size=25)


RENDERERS: Dict[str, Renderer] = {
    "cs.5.complexity": _render_complexity,
    "cs.3.algorithms": _render_algorithms,
    "cs.3.oop": _render_oop,
    "cs.3.web": _render_web,
    "cs.3.databases": _render_databases,
    "cs.3.hardware": _render_hardware,
    "cs.3.versioncontrol": _render_versioncontrol,
    "cs.4.algorithms-adv": _render_algorithms_adv,
    "cs.4.theory": _render_theory,
    "cs.4.os": _render_os,
    "cs.4.databases-adv": _render_databases_adv,
    "cs.4.ml": _render_ml,
    "cs.4.security": _render_security,
    "cs.4.systems": _render_systems,
    "cs.5.deep-learning": _render_deep_learning,
    "cs.5.distributed": _render_distributed,
    "cs.5.pl-theory": _render_pl_theory,
    "cs.5.quantum": _render_quantum,
    "cs.5.frontier": _render_frontier,
}


__all__ = ["RENDERERS"]
