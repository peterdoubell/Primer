"""Bespoke explanatory renderers for early computer-science plates.

The generic language/CS layouts communicate the curriculum metadata, but the
Seedling, Sprout, and Sapling computing lessons deserve the same visual proof
standard as Primer mathematics.  These plates therefore show a runnable toy
example: state before and after an instruction, the key used by a sort, binary
place values, a block-program trace, typed operations, call frames, a failing
index, a routed packet, or two search-growth curves.

Every composition is deterministic and remains readable in the 800 px asset.
Colour supports grouping, but numerals, shapes, labels, strokes, and ordering
also encode every important distinction.  The registry contains only the
twelve generator-owned stage 0--2 computer-science lessons; the authored
``cs.1.algorithms`` plate remains untouched.
"""

from __future__ import annotations

from typing import Callable, Dict, Sequence, Tuple

from math_illustrations.core import (
    BLUE,
    BLUE_LIGHT,
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
Box = Tuple[float, float, float, float]
Renderer = Callable[[Plate], None]


def _tint(tone: str, amount: float = .82) -> str:
    return mix(tone, PAPER_LIGHT, amount)


def _panel(plate: Plate, box: Box, tone: str, *, radius: int = 22,
           alpha: int = 222, width: int = 4) -> None:
    plate.draw.rounded_rectangle(
        box,
        radius=radius,
        fill=hex_rgba(_tint(tone, .88), alpha),
        outline=hex_rgba(tone, 210),
        width=width,
    )


def _tag(plate: Plate, center: Point, value: str, tone: str, *, size: int = 23) -> None:
    plate.label(center, value, size=max(21, size), fill=tone)


def _footer(plate: Plate, value: str, *, tone: str | None = None,
            size: int = 26) -> None:
    tone = tone or plate.accent
    plate.draw.rounded_rectangle(
        (164, 816, 1436, 881), radius=25,
        fill=hex_rgba(_tint(tone, .78), 220),
        outline=hex_rgba(tone, 180), width=3,
    )
    plate.text((800, 849), value, size=size, bold=True, fill=tone, anchor="mm")


def _arrow(plate: Plate, start: Point, end: Point, tone: str = INK_SOFT,
           label: str = "", *, label_dy: float = -23, width: int = 6,
           head: int = 19) -> None:
    plate.arrow(start, end, fill=tone, width=width, head=head)
    if label:
        plate.text(((start[0] + end[0]) / 2,
                    (start[1] + end[1]) / 2 + label_dy),
                   label, size=21, bold=True, fill=tone, anchor="mm")


def _center_lines(plate: Plate, center: Point, lines: Sequence[str], *,
                  size: int = 25, gap: int = 7, bold: bool = False,
                  fill: str = INK) -> None:
    line_height = size + gap
    y = center[1] - (len(lines) - 1) * line_height / 2
    for line in lines:
        plate.text((center[0], y), line, size=size, bold=bold,
                   fill=fill, anchor="mm")
        y += line_height


def _mini_label(plate: Plate, xy: Point, value: str, tone: str = INK_SOFT,
                *, anchor: str = "mm", size: int = 20) -> None:
    plate.text(xy, value, size=size, bold=True, fill=tone, anchor=anchor)


def _number_tile(plate: Plate, box: Box, value: str, tone: str, *,
                 sublabel: str = "", fill: str | None = None,
                 size: int = 36) -> None:
    _panel(plate, box, tone, radius=17, alpha=232)
    x0, y0, x1, y1 = box
    if fill:
        plate.draw.rounded_rectangle((x0 + 7, y0 + 7, x1 - 7, y1 - 7),
                                     radius=12, fill=hex_rgba(fill, 80))
    plate.text(((x0 + x1) / 2, (y0 + y1) / 2 - (12 if sublabel else 0)),
               value, size=size, bold=True, fill=tone, anchor="mm")
    if sublabel:
        plate.text(((x0 + x1) / 2, y1 - 19), sublabel, size=18,
                   bold=True, fill=INK_SOFT, anchor="mm")


def _code_line(plate: Plate, box: Box, value: str, *, active: bool = False,
               tone: str = BLUE, number: int | None = None,
               size: int = 24) -> None:
    x0, y0, x1, y1 = box
    fill = hex_rgba(_tint(tone, .78), 235) if active else hex_rgba(PAPER_LIGHT, 210)
    outline = tone if active else hex_rgba(GRID, 190)
    plate.draw.rounded_rectangle(box, radius=12, fill=fill, outline=outline,
                                 width=4 if active else 2)
    if number is not None:
        plate.draw.rounded_rectangle((x0 + 9, y0 + 8, x0 + 52, y1 - 8),
                                     radius=9, fill=hex_rgba(tone, 40),
                                     outline=hex_rgba(tone, 150), width=2)
        plate.text((x0 + 31, (y0 + y1) / 2), str(number), size=18,
                   bold=True, fill=tone, anchor="mm")
        text_x = x0 + 69
    else:
        text_x = x0 + 18
    plate.draw.text((text_x, (y0 + y1) / 2), value,
                    font=font(size, math_face=True), fill=INK, anchor="lm")


def _state_badge(plate: Plate, center: Point, value: str, tone: str, *,
                 shape: str = "circle") -> None:
    x, y = center
    if shape == "diamond":
        plate.draw.polygon(((x, y - 34), (x + 44, y), (x, y + 34), (x - 44, y)),
                           fill=hex_rgba(_tint(tone, .65), 240), outline=tone)
    elif shape == "square":
        plate.draw.rounded_rectangle((x - 37, y - 37, x + 37, y + 37), radius=12,
                                     fill=hex_rgba(_tint(tone, .65), 240),
                                     outline=tone, width=4)
    else:
        plate.draw.ellipse((x - 38, y - 38, x + 38, y + 38),
                           fill=hex_rgba(_tint(tone, .65), 240),
                           outline=tone, width=4)
    plate.text((x, y), value, size=25, bold=True, fill=tone, anchor="mm")


def _render_instructions(plate: Plate) -> None:
    """Execute a dependent procedure while exposing pre- and post-state."""

    _tag(plate, (225, 220), "START STATE", TEAL)
    _tag(plate, (795, 220), "EXECUTE IN ORDER", BLUE)
    _tag(plate, (1372, 220), "END STATE", GREEN)

    # Inventory makes the procedure's inputs explicit.
    _panel(plate, (116, 278, 350, 754), TEAL)
    plate.text((233, 315), "MATERIALS", size=22, bold=True,
               fill=TEAL, anchor="mm")
    for row, (symbol, label) in enumerate((("1", "dry brush"),
                                           ("2", "toothpaste"),
                                           ("3", "water"))):
        y = 390 + row * 128
        if row == 0:
            plate.draw.rounded_rectangle((154, y-24, 169, y+41), radius=6,
                                         fill=TEAL_LIGHT, outline=TEAL, width=3)
            plate.draw.rounded_rectangle((150, y-43, 181, y-14), radius=5,
                                         fill=PAPER_LIGHT, outline=TEAL, width=3)
            for x in (157, 165, 173):
                plate.draw.line((x, y-38, x, y-19), fill=TEAL, width=2)
        elif row == 1:
            plate.draw.polygon(((146,y-25),(186,y-25),(180,y+27),(152,y+27)),
                               fill=GOLD_LIGHT, outline=GOLD, width=3)
            plate.draw.rectangle((155,y+27,177,y+37), fill=PAPER_LIGHT, outline=GOLD, width=3)
            plate.draw.line((150,y-12,182,y-12), fill=GOLD, width=4)
        else:
            plate.draw.polygon(((141,y-32),(194,y-32),(186,y+35),(149,y+35)),
                               fill=BLUE_LIGHT, outline=BLUE, width=3)
            plate.draw.line((146,y-5,189,y-5), fill=BLUE, width=3)
        plate.text((225, y), label, size=23, bold=True, fill=INK, anchor="lm")
    plate.text((233, 704), "mouth: not brushed", size=21,
               bold=True, fill=INK_SOFT, anchor="mm")

    steps = (
        ("1", "GET BRUSH", "hand: empty -> brush"),
        ("2", "ADD PASTE", "brush: dry -> ready"),
        ("3", "BRUSH", "teeth: not clean -> clean"),
        ("4", "RINSE", "task: active -> done"),
    )
    for index, (number, action, change) in enumerate(steps):
        y = 266 + index * 126
        tone = (TEAL, GOLD, PLUM, GREEN)[index]
        _panel(plate, (438, y, 1110, y + 101), tone, radius=18)
        plate.draw.ellipse((458, y + 17, 525, y + 84), fill=tone, outline=tone)
        plate.text((491, y + 51), number, size=25, bold=True,
                   fill=PAPER_LIGHT, anchor="mm")
        plate.text((553, y + 31), action, size=22, bold=True, fill=tone)
        plate.text((553, y + 66), change, size=22, bold=True, fill=INK)
        if index < len(steps) - 1:
            _arrow(plate, (774, y + 103), (774, y + 122), tone, width=5, head=13)

    _panel(plate, (1230, 300, 1481, 731), GREEN)
    plate.draw.ellipse((1280, 356, 1431, 507), fill=GREEN_LIGHT,
                       outline=GREEN, width=5)
    # A non-colour check mark and explicit state identify completion.
    plate.draw.line((1318, 433, 1358, 473, 1410, 391),
                    fill=GREEN, width=13, joint="curve")
    _center_lines(plate, (1356, 592), ("brush used", "mouth rinsed", "DONE = true"),
                  size=23, gap=12, bold=True)
    _arrow(plate, (1123, 502), (1217, 502), GREEN, "produces")
    _footer(plate, "each command changes state needed by the next command", size=25)


def _sort_object(plate: Plate, x: float, base_y: float, *, object_id: str,
                 rank: int, tone: str, pattern: int) -> None:
    width = 82
    height = 38 + rank * 26
    x0, y0, x1, y1 = x - width / 2, base_y - height, x + width / 2, base_y
    plate.draw.rounded_rectangle((x0, y0, x1, y1), radius=11,
                                 fill=hex_rgba(_tint(tone, .7), 245),
                                 outline=tone, width=4)
    # Stripe count is a second, non-colour encoding of the pattern group.
    if pattern == 1:
        for yy in range(int(y0 + 14), int(y1 - 6), 20):
            plate.draw.line((x0 + 8, yy, x1 - 8, yy), fill=hex_rgba(tone, 150), width=3)
    else:
        for yy in range(int(y0 + 17), int(y1 - 8), 25):
            for xx in range(int(x0 + 16), int(x1 - 8), 25):
                plate.dot((xx, yy), 3, fill=tone, outline=tone, width=1)
    plate.text((x, y0 - 17), object_id, size=18, bold=True, fill=INK, anchor="mm")
    plate.text((x, y1 + 20), str(rank), size=18, bold=True, fill=INK_SOFT, anchor="mm")


def _render_sorting(plate: Plate) -> None:
    """Show that one collection supports different correct key-driven orders."""

    _tag(plate, (316, 219), "SAME SIX OBJECTS", TEAL)
    _tag(plate, (850, 219), "KEY: HEIGHT", BLUE)
    _tag(plate, (1292, 219), "KEY: PATTERN", PLUM)

    objects = {
        "A": (3, TEAL, 1), "B": (1, PLUM, 2), "C": (5, TEAL, 1),
        "D": (2, PLUM, 2), "E": (6, TEAL, 1), "F": (4, PLUM, 2),
    }
    _panel(plate, (110, 270, 552, 760), TEAL)
    mixed = ("C", "B", "F", "A", "E", "D")
    for index, key in enumerate(mixed):
        col, row = index % 3, index // 3
        rank, tone, pattern = objects[key]
        _sort_object(plate, 190 + col * 135, 488 + row * 225,
                     object_id=key, rank=rank, tone=tone, pattern=pattern)
    _arrow(plate, (565, 491), (635, 491), BLUE, "sort")
    _panel(plate, (646, 270, 1054, 760), BLUE)
    ordered = tuple(sorted(objects, key=lambda key: objects[key][0]))
    for index, key in enumerate(ordered):
        rank, tone, pattern = objects[key]
        _sort_object(plate, 691 + index * 64, 664,
                     object_id=key, rank=rank, tone=tone, pattern=pattern)
    plate.draw.line((681, 694, 1018, 694), fill=INK_SOFT, width=4)
    _arrow(plate, (688, 718), (1010, 718), BLUE, "ascending 1 to 6",
           label_dy=29, width=5, head=15)
    plate.text((850, 335), "B  D  A  F  C  E", size=28,
               bold=True, fill=BLUE, anchor="mm")
    plate.text((850, 378), "shortest -> tallest", size=22,
               bold=True, fill=INK_SOFT, anchor="mm")

    _panel(plate, (1110, 270, 1490, 760), PLUM)
    for group, (heading, members, tone, pattern) in enumerate((
        ("STRIPES", ("A", "C", "E"), TEAL, 1),
        ("DOTS", ("B", "D", "F"), PLUM, 2),
    )):
        y = 354 + group * 205
        plate.text((1162, y), heading, size=21, bold=True, fill=tone, anchor="lm")
        for index, key in enumerate(members):
            rank = objects[key][0]
            _sort_object(plate, 1210 + index * 103, y + 137,
                         object_id=key, rank=rank, tone=tone, pattern=pattern)
    _footer(plate, "the key defines the result: order by height, or group by pattern", size=23)


def _pattern_shape(plate: Plate, center: Point, kind: str, tone: str,
                   *, scale: float = 1.0) -> None:
    x, y = center
    radius = 42 * scale
    if kind == "A":
        plate.draw.ellipse((x - radius, y - radius, x + radius, y + radius),
                           fill=hex_rgba(_tint(tone, .55), 245), outline=tone, width=5)
        plate.draw.ellipse((x - 14 * scale, y - 14 * scale,
                            x + 14 * scale, y + 14 * scale),
                           fill=PAPER_LIGHT, outline=tone, width=3)
    else:
        points = ((x, y - radius), (x + radius, y + radius),
                  (x - radius, y + radius))
        plate.draw.polygon(points, fill=hex_rgba(_tint(tone, .55), 245), outline=tone)
        plate.draw.line(points + (points[0],), fill=tone, width=5)
    plate.text((x, y + 69 * scale), kind, size=max(17, int(20 * scale)),
               bold=True, fill=tone, anchor="mm")


def _render_patterns(plate: Plate) -> None:
    """Separate observation from rule inference and test a prediction."""

    _tag(plate, (290, 219), "OBSERVE POSITIONS", TEAL)
    _tag(plate, (805, 219), "ISOLATE UNIT", GOLD)
    _tag(plate, (1304, 219), "PREDICT + CHECK", GREEN)

    positions = ("A", "B", "A", "B", "A", "?")
    xs = (145, 265, 385, 505, 625, 745)
    for index, (x, kind) in enumerate(zip(xs, positions), start=1):
        plate.text((x, 302), str(index), size=19, bold=True,
                   fill=INK_SOFT, anchor="mm")
        if kind == "?":
            plate.draw.rounded_rectangle((x - 48, 347, x + 48, 443), radius=15,
                                         fill=hex_rgba(PAPER_LIGHT, 220),
                                         outline=INK_SOFT, width=4)
            plate.text((x, 395), "?", size=44, bold=True,
                       fill=INK_SOFT, anchor="mm")
        else:
            _pattern_shape(plate, (x, 395), kind,
                           TEAL if kind == "A" else PLUM, scale=.92)
    # Repetition brackets label complete units rather than merely colouring them.
    for start, end, number in ((110, 300, "unit 1"), (350, 540, "unit 2")):
        plate.draw.line((start, 493, start, 516, end, 516, end, 493),
                        fill=GOLD, width=4, joint="curve")
        plate.text(((start + end) / 2, 542), number, size=20,
                   bold=True, fill=GOLD, anchor="mm")
    plate.draw.line((590, 493, 590, 516, 780, 516, 780, 493),
                    fill=hex_rgba(GOLD, 130), width=4)
    plate.text((685, 542), "unit 3", size=20, bold=True,
               fill=GOLD, anchor="mm")

    _panel(plate, (842, 296, 1090, 586), GOLD)
    _pattern_shape(plate, (920, 420), "A", TEAL, scale=.9)
    _pattern_shape(plate, (1014, 420), "B", PLUM, scale=.9)
    plate.text((966, 330), "RULE = AB", size=27, bold=True,
               fill=GOLD, anchor="mm")
    plate.text((966, 540), "repeat without a gap", size=20,
               bold=True, fill=INK_SOFT, anchor="mm")
    _arrow(plate, (1099, 437), (1172, 437), GREEN, "apply")

    _panel(plate, (1185, 296, 1484, 586), GREEN)
    plate.text((1334, 338), "position 5 is A", size=22,
               bold=True, fill=INK, anchor="mm")
    _pattern_shape(plate, (1270, 450), "A", TEAL, scale=.9)
    _arrow(plate, (1322, 450), (1362, 450), GREEN, width=5, head=14)
    _pattern_shape(plate, (1418, 450), "B", PLUM, scale=.9)
    plate.text((1334, 555), "so position 6 = B", size=23,
               bold=True, fill=GREEN, anchor="mm")

    # Counterexample check: AA would break the proposed AB rule.
    _panel(plate, (179, 629, 1420, 776), CORAL, radius=18)
    plate.text((224, 670), "TEST", size=21, bold=True, fill=CORAL)
    plate.text((343, 670), "Does AB generate every known position?", size=23,
               bold=True, fill=INK)
    plate.text((343, 719), "yes:  A B | A B | A _", size=25,
               bold=True, fill=GREEN)
    plate.text((902, 719), "AA would fail at position 2", size=23,
               bold=True, fill=CORAL)
    _footer(plate, "a repeat unit predicts the missing shape—and the known positions test the rule", size=22)


def _render_binary(plate: Plate) -> None:
    """Decode a binary word through weighted switches, not visual analogy."""

    _tag(plate, (350, 219), "FOUR BITS", TEAL)
    _tag(plate, (800, 219), "PLACE VALUES", BLUE)
    _tag(plate, (1300, 219), "ADD ACTIVE PLACES", GOLD)

    bits = (("1", 8, True), ("1", 4, True), ("0", 2, False), ("1", 1, True))
    xs = (178, 365, 552, 739)
    for index, (x, (bit, value, active)) in enumerate(zip(xs, bits)):
        tone = (TEAL, BLUE, PLUM, GREEN)[index]
        plate.text((x, 286), str(value), size=22, bold=True,
                   fill=INK_SOFT, anchor="mm")
        plate.text((x, 318), "place", size=18, bold=True,
                   fill=INK_SOFT, anchor="mm")
        # Lever position plus ON/OFF label makes state independent of colour.
        plate.draw.rounded_rectangle((x - 63, 353, x + 63, 511), radius=31,
                                     fill=hex_rgba(_tint(tone, .8), 230),
                                     outline=tone, width=4)
        plate.draw.line((x, 400 if active else 466,
                         x + 36, 366 if active else 484), fill=tone, width=9)
        plate.dot((x, 400 if active else 466), 12, fill=PAPER_LIGHT,
                  outline=tone, width=4)
        plate.text((x, 548), bit, size=48, bold=True, fill=tone, anchor="mm")
        plate.text((x, 590), "ON" if active else "OFF", size=20,
                   bold=True, fill=tone, anchor="mm")
        plate.text((x, 637), "include {}".format(value if active else 0), size=20,
                   bold=True, fill=INK, anchor="mm")

    _arrow(plate, (808, 470), (881, 470), GOLD, "decode")
    _panel(plate, (894, 306, 1477, 711), GOLD)
    plate.text((1185, 360), "1101 (base 2)", size=34, bold=True,
               fill=INK, anchor="mm")
    summands = (("1 x 8", "8", TEAL), ("1 x 4", "4", BLUE),
                ("0 x 2", "0", PLUM), ("1 x 1", "1", GREEN))
    for row, (term, result, tone) in enumerate(summands):
        y = 420 + row * 60
        plate.text((1004, y), term, size=25, bold=True, fill=tone, anchor="lm")
        plate.text((1300, y), "= " + result, size=25, bold=True,
                   fill=INK, anchor="lm")
    plate.draw.line((990, 647, 1390, 647), fill=GOLD, width=4)
    plate.text((1187, 680), "8 + 4 + 0 + 1 = 13", size=29,
               bold=True, fill=GOLD, anchor="mm")
    plate.text((800, 757), "each move left doubles the place value: 1, 2, 4, 8",
               size=24, bold=True, fill=INK_SOFT, anchor="mm")
    _footer(plate, "a 1 includes its place value; a 0 excludes it", size=25)


def _block(plate: Plate, box: Box, text: str, tone: str, *,
           kind: str = "command", active: bool = False) -> None:
    x0, y0, x1, y1 = box
    outline = INK if active else tone
    fill = _tint(tone, .64 if active else .78)
    if kind == "condition":
        notch = 20
        points = ((x0 + notch, y0), (x1 - notch, y0), (x1, (y0 + y1) / 2),
                  (x1 - notch, y1), (x0 + notch, y1), (x0, (y0 + y1) / 2))
        plate.draw.polygon(points, fill=hex_rgba(fill, 245), outline=outline)
        plate.draw.line(points + (points[0],), fill=outline, width=5 if active else 3)
    else:
        plate.draw.rounded_rectangle(box, radius=15, fill=hex_rgba(fill, 245),
                                     outline=outline, width=5 if active else 3)
        # A puzzle notch marks executable blocks without relying on colour.
        plate.draw.arc((x0 + 24, y0 - 9, x0 + 62, y0 + 27), 0, 180,
                       fill=outline, width=3)
    plate.text(((x0 + x1) / 2, (y0 + y1) / 2), text, size=22,
               bold=True, fill=INK, anchor="mm")


def _render_blocks(plate: Plate) -> None:
    """Pair a block stack with an iteration-by-iteration position trace."""

    _tag(plate, (352, 219), "PROGRAM", TEAL)
    _tag(plate, (1024, 219), "TRACE ON THE TRACK", BLUE)

    _panel(plate, (115, 270, 602, 776), TEAL)
    _block(plate, (171, 309, 546, 374), "when START", GOLD, active=True)
    _block(plate, (171, 393, 546, 458), "repeat 2 times", PLUM)
    _block(plate, (214, 474, 527, 537), "move +1", BLUE)
    _block(plate, (171, 558, 546, 623), "if on STAR?", CORAL, kind="condition")
    _block(plate, (214, 642, 527, 705), "jump +2", GREEN)
    for y in (374, 458, 537, 623):
        plate.draw.line((190, y, 190, y + 17), fill=INK_SOFT, width=4)
    plate.text((358, 744), "sequence -> loop -> branch", size=21,
               bold=True, fill=INK_SOFT, anchor="mm")

    # Track squares are numbered states, and the star is a geometric marker.
    track_y = 438
    for position in range(5):
        x = 715 + position * 165
        tone = CORAL if position == 2 else BLUE
        plate.draw.rounded_rectangle((x - 57, track_y - 57, x + 57, track_y + 57),
                                     radius=15, fill=hex_rgba(_tint(tone, .83), 235),
                                     outline=tone, width=4)
        plate.text((x, track_y + 3), str(position), size=31, bold=True,
                   fill=INK, anchor="mm")
        if position == 2:
            # Four-point star marker is visible in greyscale.
            plate.draw.polygon(((x, track_y - 46), (x + 11, track_y - 12),
                                (x + 45, track_y), (x + 11, track_y + 12),
                                (x, track_y + 46), (x - 11, track_y + 12),
                                (x - 45, track_y), (x - 11, track_y - 12)),
                               outline=CORAL)
            plate.draw.line(((x, track_y - 46), (x + 11, track_y - 12),
                             (x + 45, track_y), (x + 11, track_y + 12),
                             (x, track_y + 46), (x - 11, track_y + 12),
                             (x - 45, track_y), (x - 11, track_y - 12),
                             (x, track_y - 46)), fill=CORAL, width=4)
    plate.draw.line((650, track_y + 80, 1435, track_y + 80), fill=INK_SOFT, width=4)

    trace = (("start", "p = 0", 0, TEAL), ("loop 1", "p = 1", 1, BLUE),
             ("loop 2", "p = 2", 2, PLUM), ("star? true", "p = 4", 4, GREEN))
    for start, end, label, tone in ((0, 1, "+1", BLUE), (1, 2, "+1", PLUM),
                                   (2, 4, "+2", GREEN)):
        _arrow(plate, (715+start*165, 325), (715+end*165, 325), tone, label)
    for row, (event, state, position, tone) in enumerate(trace):
        y = 585 + row * 53
        plate.text((704, y), str(row + 1), size=19, bold=True,
                   fill=tone, anchor="mm")
        plate.text((746, y), event, size=21, bold=True, fill=tone, anchor="lm")
        plate.text((1030, y), state, size=22, bold=True, fill=INK, anchor="lm")
    _footer(plate, "the loop repeats movement; the true branch changes the next state", size=23)


def _render_parts(plate: Plate) -> None:
    """Trace one character through input, CPU, memory, and output hardware."""

    _tag(plate, (220, 220), "INPUT", TEAL)
    _tag(plate, (792, 220), "PROCESS + STORE", BLUE)
    _tag(plate, (1370, 220), "OUTPUT", GREEN)

    # Simplified character path after key-event interpretation, not a raw
    # keyboard scan-code or USB protocol trace.
    _panel(plate, (113, 292, 350, 690), TEAL)
    plate.text((231, 329), "KEYBOARD", size=21, bold=True,
               fill=TEAL, anchor="mm")
    for row in range(3):
        for col in range(4):
            x0 = 141 + col * 45
            y0 = 384 + row * 45
            plate.draw.rounded_rectangle((x0, y0, x0 + 34, y0 + 31), radius=6,
                                         fill=hex_rgba(PAPER_LIGHT, 235),
                                         outline=INK_SOFT, width=2)
    plate.draw.rounded_rectangle((169, 519, 290, 582), radius=12,
                                 fill=hex_rgba(TEAL_LIGHT, 230), outline=TEAL, width=4)
    plate.text((229, 551), "A", size=34, bold=True, fill=TEAL, anchor="mm")
    plate.text((231, 626), "key event", size=21, bold=True,
               fill=INK_SOFT, anchor="mm")

    _arrow(plate, (359, 479), (500, 479), TEAL, "01000001")
    plate.text((429, 512), "ASCII A", size=18, bold=True, fill=TEAL, anchor="mm")

    # CPU and RAM share address/data/control buses; labels state what moves.
    _panel(plate, (514, 283, 1113, 718), BLUE)
    plate.draw.rounded_rectangle((574, 347, 815, 570), radius=21,
                                 fill=hex_rgba(BLUE_LIGHT, 200), outline=BLUE, width=5)
    plate.text((694, 386), "CPU", size=28, bold=True, fill=BLUE, anchor="mm")
    _center_lines(plate, (694, 477), ("fetch instruction", "decode key event", "execute draw(A)"),
                  size=21, gap=11, bold=True)
    # Pins make the processor visibly a component.
    for y in range(377, 556, 34):
        plate.draw.line((555, y, 574, y), fill=BLUE, width=4)
        plate.draw.line((815, y, 834, y), fill=BLUE, width=4)

    plate.draw.rounded_rectangle((887, 347, 1054, 570), radius=18,
                                 fill=hex_rgba(GOLD_LIGHT, 205), outline=GOLD, width=5)
    plate.text((970, 386), "RAM", size=27, bold=True, fill=GOLD, anchor="mm")
    for row, (address, value) in enumerate((("0x10", "draw"), ("0x11", "A"),
                                            ("0x12", "cursor"))):
        y = 433 + row * 49
        plate.draw.line((908, y + 20, 1035, y + 20), fill=GOLD, width=2)
        plate.text((914, y), address, size=17, bold=True, fill=INK_SOFT)
        plate.text((990, y), value, size=18, bold=True, fill=INK)
    plate.double_arrow((835, 430), (875, 430), fill=BLUE, width=5)
    plate.text((855, 397), "data", size=18, bold=True, fill=BLUE, anchor="mm")
    plate.arrow((835, 511), (875, 511), fill=GOLD, width=5)
    plate.text((855, 545), "addr", size=17, bold=True, fill=GOLD, anchor="mm")
    plate.text((813, 656), "RAM holds live instructions + state",
               size=21, bold=True, fill=INK_SOFT, anchor="mm")

    _arrow(plate, (1122, 479), (1232, 479), GREEN, "pixels")
    _panel(plate, (1244, 292, 1485, 690), GREEN)
    plate.draw.rounded_rectangle((1277, 345, 1452, 555), radius=12,
                                 fill=hex_rgba("#ffffff", 210), outline=GREEN, width=5)
    plate.text((1364, 449), "A", size=104, bold=True, fill=GREEN, anchor="mm")
    plate.draw.line((1322, 576, 1406, 576), fill=GREEN, width=8)
    plate.draw.line((1364, 555, 1364, 609), fill=GREEN, width=7)
    plate.text((1364, 649), "SCREEN", size=21, bold=True,
               fill=GREEN, anchor="mm")
    _footer(plate, "input is encoded; the CPU executes; memory supplies state; output renders", size=22)


def _trace_row(plate: Plate, y: float, values: Sequence[str], tones: Sequence[str], *,
               widths: Sequence[int] = (100, 130, 150, 150, 208)) -> None:
    x = 740
    for value, tone, width in zip(values, tones, widths):
        plate.draw.rounded_rectangle((x, y, x + width - 10, y + 62), radius=10,
                                     fill=hex_rgba(_tint(tone, .84), 225),
                                     outline=hex_rgba(tone, 180), width=2)
        plate.text((x + (width - 10) / 2, y + 31), value, size=19,
                   bold=True, fill=INK, anchor="mm")
        x += width


def _render_programming(plate: Plate) -> None:
    """Make loop execution inspectable through a complete state table."""

    _tag(plate, (373, 219), "PROGRAM", BLUE)
    _tag(plate, (1089, 219), "STATE AFTER EACH ITERATION", TEAL)
    _panel(plate, (113, 273, 650, 760), BLUE)
    code = (("total = 0", False), ("for n in [2, 5, 8]:", True),
            ("    if n > 4:", True), ("        total = total + n", True),
            ("print(total)", False))
    for index, (line, active) in enumerate(code, start=1):
        _code_line(plate, (144, 320 + (index - 1) * 80, 618, 380 + (index - 1) * 80),
                   line, active=active, tone=TEAL if active else BLUE,
                   number=index, size=20)
    plate.text((381, 730), "variable = named state", size=21,
               bold=True, fill=BLUE, anchor="mm")

    headers = ("STEP", "n", "n > 4", "ACTION", "total")
    header_tones = (BLUE, TEAL, GOLD, PLUM, GREEN)
    _trace_row(plate, 289, headers, header_tones)
    rows = (
        ("start", "-", "-", "assign 0", "0"),
        ("1", "2", "false", "skip add", "0"),
        ("2", "5", "true", "0 + 5", "5"),
        ("3", "8", "true", "5 + 8", "13"),
    )
    for row, values in enumerate(rows):
        tones = (BLUE, TEAL, CORAL if values[2] == "false" else GREEN,
                 PLUM, GREEN)
        _trace_row(plate, 371 + row * 80, values, tones)
        if row < len(rows) - 1:
            plate.draw.line((1452, 433 + row * 80, 1452, 451 + row * 80),
                            fill=GREEN, width=4)
    plate.draw.rounded_rectangle((1237, 701, 1478, 766), radius=18,
                                 fill=hex_rgba(GREEN_LIGHT, 220),
                                 outline=GREEN, width=4)
    plate.text((1357, 733), "OUTPUT  13", size=25, bold=True,
               fill=GREEN, anchor="mm")
    _footer(plate, "the condition decides whether each loop iteration changes total", size=24)


def _render_data_types(plate: Plate) -> None:
    """Contrast values that look alike but support different operations."""

    _tag(plate, (800, 218), "TYPE DETERMINES THE OPERATION", BLUE)
    panels = (
        ((111, 275, 437, 585), "NUMBER", BLUE, "7 + 2", "9", "arithmetic"),
        ((461, 275, 787, 585), "STRING", TEAL, '"7" + "2"', '"72"', "join text"),
        ((811, 275, 1137, 585), "BOOLEAN", GOLD, "true AND false", "false", "logic"),
        ((1161, 275, 1487, 585), "LIST", PLUM, "[7, 2] append 5", "[7, 2, 5]", "grow sequence"),
    )
    for index, (box, heading, tone, expression, result, operation) in enumerate(panels):
        _panel(plate, box, tone)
        x0, y0, x1, y1 = box
        # Distinct shape badges make types legible without colour.
        shape = ("circle", "square", "diamond", "square")[index]
        _state_badge(plate, ((x0 + x1) / 2, y0 + 62),
                     ("#", "T", "?", "[]")[index], tone, shape=shape)
        plate.text(((x0 + x1) / 2, y0 + 119), heading, size=22,
                   bold=True, fill=tone, anchor="mm")
        plate.draw.rounded_rectangle((x0 + 26, y0 + 152, x1 - 26, y0 + 214),
                                     radius=12, fill=hex_rgba(PAPER_LIGHT, 225),
                                     outline=hex_rgba(tone, 145), width=2)
        plate.draw.text(((x0 + x1) / 2, y0 + 183), expression,
                        font=font(20, math_face=True), fill=INK, anchor="mm")
        _arrow(plate, ((x0 + x1) / 2, y0 + 224),
               ((x0 + x1) / 2, y0 + 251), tone, width=4, head=12)
        plate.text(((x0 + x1) / 2, y0 + 270), result, size=28,
                   bold=True, fill=tone, anchor="mm")
        plate.text(((x0 + x1) / 2, y1 - 18), operation, size=18,
                   bold=True, fill=INK_SOFT, anchor="mm")

    # A type-error counterexample prevents treating types as decorative labels.
    _panel(plate, (219, 628, 1381, 778), CORAL, radius=18)
    plate.text((267, 667), "TYPE CHECK", size=21, bold=True, fill=CORAL)
    plate.draw.text((486, 668), '7 + "2"', font=font(25, math_face=True), fill=INK)
    plate.draw.line((478, 708, 650, 708), fill=CORAL, width=5)
    plate.text((708, 689), "X", size=31, bold=True, fill=CORAL, anchor="mm")
    plate.text((758, 667), "number + string has no defined result here",
               size=22, bold=True, fill=INK)
    plate.text((758, 717), "convert deliberately: 7 + int(\"2\") = 9",
               size=22, bold=True, fill=GREEN)
    _footer(plate, "appearance is not type: 7 and \"7\" have different representations and rules", size=22)


def _render_functions(plate: Plate) -> None:
    """Show parameter binding, frame isolation, and return to each caller."""

    _tag(plate, (343, 219), "ONE DEFINITION", BLUE)
    _tag(plate, (973, 219), "TWO CALL FRAMES", TEAL)
    _tag(plate, (1390, 219), "RETURNS", GREEN)
    _panel(plate, (112, 286, 573, 703), BLUE)
    _code_line(plate, (146, 342, 539, 410), "def double(x):", active=True,
               tone=BLUE, number=1, size=23)
    _code_line(plate, (146, 429, 539, 497), "return x * 2", active=True,
               tone=BLUE, number=2, size=23)
    plate.text((343, 554), "parameter x", size=23, bold=True,
               fill=BLUE, anchor="mm")
    plate.text((343, 598), "names the input inside", size=21,
               bold=True, fill=INK_SOFT, anchor="mm")
    plate.text((343, 630), "this function call", size=21,
               bold=True, fill=INK_SOFT, anchor="mm")

    frames = (
        ((681, 297, 1151, 489), "CALL 1", "a = double(3)", "x = 3", "3 * 2"),
        ((681, 534, 1151, 726), "CALL 2", "b = double(5)", "x = 5", "5 * 2"),
    )
    for index, (box, heading, call, binding, expression) in enumerate(frames):
        tone = TEAL if index == 0 else PLUM
        _panel(plate, box, tone)
        x0, y0, x1, y1 = box
        plate.text((x0 + 27, y0 + 30), heading, size=21, bold=True, fill=tone)
        plate.draw.text((x0 + 27, y0 + 76), call,
                        font=font(23, math_face=True), fill=INK)
        plate.draw.rounded_rectangle((x0 + 28, y0 + 103, x0 + 195, y0 + 163),
                                     radius=12, fill=hex_rgba(_tint(tone, .74), 235),
                                     outline=tone, width=3)
        plate.text((x0 + 111, y0 + 133), binding, size=23,
                   bold=True, fill=tone, anchor="mm")
        _arrow(plate, (x0 + 215, y0 + 133), (x0 + 274, y0 + 133), tone,
               "substitute", label_dy=-27, width=4, head=13)
        plate.draw.text((x0 + 292, y0 + 133), expression,
                        font=font(24, math_face=True), fill=INK, anchor="lm")

    _arrow(plate, (580, 392), (666, 392), TEAL, "call")
    _arrow(plate, (580, 628), (666, 628), PLUM, "call")
    for y, result, variable, tone in ((392, "6", "a", TEAL),
                                      (628, "10", "b", PLUM)):
        _arrow(plate, (1162, y), (1252, y), tone, "return")
        plate.draw.ellipse((1274, y - 61, 1396, y + 61),
                           fill=hex_rgba(_tint(tone, .6), 240), outline=tone, width=5)
        plate.text((1335, y - 10), result, size=38, bold=True,
                   fill=tone, anchor="mm")
        plate.text((1335, y + 34), variable + " = " + result, size=20,
                   bold=True, fill=INK, anchor="mm")
    plate.draw.line((1199, 275, 1199, 735), fill=hex_rgba(GRID, 190), width=3)
    plate.text((975, 771), "each call gets a fresh local x", size=22,
               bold=True, fill=INK_SOFT, anchor="mm")
    _footer(plate, "reuse the function body; bind a fresh argument; return to the caller", size=23)


def _render_debugging(plate: Plate) -> None:
    """Diagnose a reproducible off-by-one error from the invalid state."""

    _tag(plate, (341, 219), "FAILING LOOP", CORAL)
    _tag(plate, (941, 219), "REPRODUCE THE STATE", BLUE)
    _tag(plate, (1379, 219), "SMALLEST FIX", GREEN)

    _panel(plate, (112, 276, 584, 737), CORAL)
    code = (("items = ['A','B','C']", False), ("i = 0", False),
            ("while i <= len(items):", True), ("    print(items[i])", True),
            ("    i = i + 1", False))
    for index, (line, active) in enumerate(code, start=1):
        _code_line(plate, (143, 313 + (index - 1) * 74, 553, 369 + (index - 1) * 74),
                   line, active=active, tone=CORAL, number=index, size=18)
    plate.text((348, 700), "suspect: loop boundary", size=21,
               bold=True, fill=CORAL, anchor="mm")

    # Array cells show valid indexes; the dashed fourth cell is not allocated.
    _panel(plate, (641, 276, 1195, 737), BLUE)
    plate.text((918, 318), "len(items) = 3", size=24,
               bold=True, fill=BLUE, anchor="mm")
    for index, value in enumerate(("A", "B", "C")):
        x0 = 675 + index * 125
        plate.text((x0 + 50, 385), "index " + str(index), size=18,
                   bold=True, fill=INK_SOFT, anchor="mm")
        plate.draw.rounded_rectangle((x0, 410, x0 + 100, 520), radius=14,
                                     fill=hex_rgba(BLUE_LIGHT, 205),
                                     outline=BLUE, width=4)
        plate.text((x0 + 50, 465), value, size=39, bold=True,
                   fill=BLUE, anchor="mm")
    plate.text((1100, 385), "index 3", size=18, bold=True,
               fill=CORAL, anchor="mm")
    plate.dashed_line((1050, 410), (1150, 410), fill=CORAL, width=4, dash=12, gap=8)
    plate.dashed_line((1150, 410), (1150, 520), fill=CORAL, width=4, dash=12, gap=8)
    plate.dashed_line((1150, 520), (1050, 520), fill=CORAL, width=4, dash=12, gap=8)
    plate.dashed_line((1050, 520), (1050, 410), fill=CORAL, width=4, dash=12, gap=8)
    plate.text((1100, 465), "X", size=42, bold=True, fill=CORAL, anchor="mm")
    events = (("i=0", "A", GREEN), ("i=1", "B", GREEN),
              ("i=2", "C", GREEN), ("i=3", "IndexError", CORAL))
    for row, (state, output, tone) in enumerate(events):
        y = 572 + row * 39
        plate.text((707, y), state, size=19, bold=True, fill=INK, anchor="lm")
        plate.text((841, y), "->", size=18, bold=True, fill=INK_SOFT, anchor="mm")
        plate.text((876, y), output, size=19, bold=True, fill=tone, anchor="lm")

    _arrow(plate, (1205, 503), (1257, 503), GREEN, "fix")
    _panel(plate, (1267, 321, 1487, 685), GREEN)
    plate.text((1377, 365), "CHANGE ONE", size=20, bold=True,
               fill=GREEN, anchor="mm")
    plate.draw.rounded_rectangle((1293, 409, 1461, 478), radius=12,
                                 fill=hex_rgba(CORAL_LIGHT, 190), outline=CORAL, width=3)
    plate.draw.text((1377, 443), "i <= 3", font=font(22, math_face=True),
                    fill=CORAL, anchor="mm")
    plate.draw.line((1318, 443, 1436, 443), fill=CORAL, width=4)
    _arrow(plate, (1377, 491), (1377, 534), GREEN, width=5, head=14)
    plate.draw.rounded_rectangle((1293, 548, 1461, 617), radius=12,
                                 fill=hex_rgba(GREEN_LIGHT, 210), outline=GREEN, width=4)
    plate.draw.text((1377, 582), "i < 3", font=font(24, math_face=True),
                    fill=GREEN, anchor="mm")
    plate.text((1377, 650), "stop before length", size=19,
               bold=True, fill=INK_SOFT, anchor="mm")
    _footer(plate, "valid indexes are 0, 1, 2; stopping before length removes index 3", size=22)


def _router(plate: Plate, center: Point, label: str, tone: str, *,
            shape: str = "circle") -> None:
    _state_badge(plate, center, label, tone, shape=shape)


def _render_internet(plate: Plate) -> None:
    """Trace a name lookup and one protected request across routed packets."""

    _tag(plate, (267, 218), "1  RESOLVE NAME", TEAL)
    _tag(plate, (799, 218), "2  ROUTE PACKETS", BLUE)
    _tag(plate, (1360, 218), "3  REASSEMBLE", GREEN)

    _panel(plate, (109, 278, 477, 724), TEAL)
    plate.draw.rounded_rectangle((150, 325, 436, 480), radius=16,
                                 fill=hex_rgba(PAPER_LIGHT, 235), outline=TEAL, width=4)
    plate.text((293, 357), "BROWSER", size=21, bold=True,
               fill=TEAL, anchor="mm")
    plate.draw.text((293, 412), "example.org", font=font(26, math_face=True),
                    fill=INK, anchor="mm")
    _arrow(plate, (182, 526), (405, 526), TEAL, "DNS query", label_dy=-22)
    _arrow(plate, (405, 599), (182, 599), TEAL, "203.0.113.7", label_dy=23)
    plate.text((293, 661), "name -> IP address", size=22,
               bold=True, fill=INK_SOFT, anchor="mm")

    # A packet has explicit headers/payload; route choice happens hop by hop.
    _panel(plate, (523, 278, 1112, 724), BLUE)
    plate.text((818, 313), "PACKET  #1 of 3", size=21,
               bold=True, fill=BLUE, anchor="mm")
    fields = (("TO", "203.0.113.7", BLUE, 181),
              ("SEQ", "1 / 3", PLUM, 118),
              ("DATA", "encrypted bytes", GOLD, 209))
    x = 554
    for heading, value, tone, width in fields:
        plate.draw.rounded_rectangle((x, 345, x + width, 439), radius=11,
                                     fill=hex_rgba(_tint(tone, .78), 230),
                                     outline=tone, width=3)
        plate.text((x + width / 2, 370), heading, size=17,
                   bold=True, fill=tone, anchor="mm")
        plate.text((x + width / 2, 411), value, size=17,
                   bold=True, fill=INK, anchor="mm")
        x += width + 9

    routers = ((594, 574, "R1", TEAL, "circle"),
               (774, 508, "R2", BLUE, "square"),
               (955, 589, "R3", PLUM, "diamond"))
    for x, y, label, tone, shape in routers:
        _router(plate, (x, y), label, tone, shape=shape)
    _arrow(plate, (637, 558), (729, 525), BLUE, "next hop", label_dy=-31, width=5)
    _arrow(plate, (819, 526), (911, 568), BLUE, "next hop", label_dy=32, width=5)
    plate.dashed_line((637, 596), (912, 621), fill=hex_rgba(INK_SOFT, 120),
                      width=3, dash=14, gap=10)
    _center_lines(plate, (818, 667),
                  ("routers forward by destination", "each packet chooses a next hop"),
                  size=18, gap=5, bold=True, fill=INK_SOFT)

    _arrow(plate, (1122, 498), (1190, 498), GREEN)
    _panel(plate, (1200, 278, 1490, 724), GREEN)
    plate.draw.rounded_rectangle((1240, 326, 1450, 472), radius=15,
                                 fill=hex_rgba(GREEN_LIGHT, 205), outline=GREEN, width=5)
    plate.text((1345, 361), "SERVER", size=21, bold=True,
               fill=GREEN, anchor="mm")
    plate.draw.text((1345, 410), "203.0.113.7", font=font(22, math_face=True),
                    fill=INK, anchor="mm")
    plate.text((1345, 519), "order  1 | 2 | 3", size=22,
               bold=True, fill=INK, anchor="mm")
    plate.draw.line((1260, 544, 1430, 544), fill=GREEN, width=4)
    _center_lines(plate, (1345, 620), ("browser checks", "server identity; TLS", "encrypts content", "in transit"),
                  size=20, gap=9, bold=True)
    plate.text((800, 770), "DNS finds an address; routing forwards packets; HTTPS protects the connection",
               size=22, bold=True, fill=INK_SOFT, anchor="mm")
    _footer(plate, "encryption protects packet contents—not every fact about the endpoint or site", size=21)


def _search_cell(plate: Plate, center: Point, value: int, *, checked: bool,
                 target: bool = False, eliminated: bool = False,
                 tone: str = BLUE) -> None:
    x, y = center
    if eliminated:
        fill = hex_rgba(PAPER, 125)
        outline = hex_rgba(GRID, 165)
    else:
        fill = hex_rgba(_tint(tone, .75), 235)
        outline = tone
    plate.draw.rounded_rectangle((x - 27, y - 27, x + 27, y + 27), radius=8,
                                 fill=fill, outline=outline, width=4 if checked else 2)
    plate.text((x, y), str(value), size=17, bold=checked or target,
               fill=INK_SOFT if eliminated else (GREEN if target else INK), anchor="mm")
    if checked:
        plate.draw.line((x - 19, y + 34, x + 19, y + 34),
                        fill=GREEN if target else CORAL, width=5)
    if eliminated:
        plate.draw.line((x - 22, y - 22, x + 22, y + 22),
                        fill=hex_rgba(INK_SOFT, 90), width=2)


def _render_bigo(plate: Plate) -> None:
    """Compare two complete searches and then expose how work grows with n."""

    _tag(plate, (444, 219), "LINEAR SEARCH: TARGET 16", CORAL)
    _tag(plate, (1156, 219), "BINARY SEARCH: SORTED DATA", BLUE)

    _panel(plate, (108, 274, 778, 598), CORAL)
    values = tuple(range(1, 17))
    for index, value in enumerate(values):
        x = 153 + (index % 8) * 78
        y = 367 + (index // 8) * 102
        _search_cell(plate, (x, y), value, checked=True,
                     target=value == 16, tone=CORAL)
        plate.text((x, y + 54), str(index + 1), size=15,
                   bold=True, fill=INK_SOFT, anchor="mm")
    plate.text((443, 563), "check each item: 16 comparisons", size=22,
               bold=True, fill=CORAL, anchor="mm")

    _panel(plate, (822, 274, 1492, 598), BLUE)
    check_order = (8, 12, 14, 15, 16)
    for index, value in enumerate(values):
        x = 867 + (index % 8) * 78
        y = 367 + (index // 8) * 102
        _search_cell(plate, (x, y), value, checked=value in check_order,
                     target=value == 16, eliminated=False, tone=BLUE)
        if value in check_order:
            plate.text((x, y + 54), str(check_order.index(value) + 1),
                       size=15, bold=True, fill=BLUE, anchor="mm")
    plate.text((1157, 563), "check 8, 12, 14, 15, 16: 5 comparisons", size=21,
               bold=True, fill=BLUE, anchor="mm")

    # Growth table is small but direct: doubling n doubles linear work, while
    # binary worst-case work adds only one comparison for these sizes.
    _panel(plate, (193, 635, 1407, 784), GOLD, radius=18)
    headers = ("items n", "4", "8", "16", "when n doubles")
    linear = ("linear worst case", "4", "8", "16", "work doubles")
    binary = ("binary worst case", "3", "4", "5", "+1 comparison")
    widths = (285, 145, 145, 145, 365)
    xs = [228]
    for width in widths[:-1]:
        xs.append(xs[-1] + width)
    for row, (values_row, tone) in enumerate(((headers, GOLD), (linear, CORAL), (binary, BLUE))):
        y = 660 + row * 42
        for index, (x, width, value) in enumerate(zip(xs, widths, values_row)):
            if index:
                plate.draw.line((x - 15, 648, x - 15, 766),
                                fill=hex_rgba(GRID, 180), width=2)
            plate.text((x + (width - 25) / 2, y), value,
                       size=18 if index in (0, 4) else 20,
                       bold=True, fill=tone if row else INK, anchor="mm")
    _footer(plate, "sorted order lets binary search discard half the candidates after each check", size=22)


RENDERERS: Dict[str, Renderer] = {
    "cs.0.instructions": _render_instructions,
    "cs.0.sorting": _render_sorting,
    "cs.0.patterns": _render_patterns,
    "cs.1.binary": _render_binary,
    "cs.1.blocks": _render_blocks,
    "cs.1.parts": _render_parts,
    "cs.2.programming": _render_programming,
    "cs.2.data-types": _render_data_types,
    "cs.2.functions": _render_functions,
    "cs.2.debugging": _render_debugging,
    "cs.2.internet": _render_internet,
    "cs.2.bigo-intro": _render_bigo,
}


__all__ = ["RENDERERS"]
