"""Bespoke explanatory renderers for advanced language and literature plates.

The Branch, Canopy, and Emergent lessons need more than renamed instances of
the shared flow/tree templates.  This module therefore draws the evidence or
representation that each discipline actually reasons with: highlighted
passages, genre trajectories, linguistic analyses, parallel word histories,
manuscript descent, incremental parses, corpus splits, and story/discourse
order.  Colour is always paired with a label, shape, line style, or position so
that no inference depends on hue alone.

Renderers accept an initialised :class:`~math_illustrations.core.Plate` and draw
inside its content frame.  The registry contains exactly the generator-owned
language lessons from stages 3--5.
"""

from __future__ import annotations

import math
from typing import Callable, Dict, Iterable, Sequence, Tuple

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

from .language_early_detail import _ipa_font


Point = Tuple[float, float]
Box = Tuple[float, float, float, float]
Renderer = Callable[[Plate], None]


def _tint(tone: str, amount: float = .82) -> str:
    return mix(tone, PAPER_LIGHT, amount)


def _panel(plate: Plate, box: Box, tone: str, *, radius: int = 24,
           alpha: int = 224, width: int = 4, dashed: bool = False) -> None:
    if dashed:
        plate.draw.rounded_rectangle(
            box, radius=radius, fill=hex_rgba(_tint(tone, .9), alpha),
        )
        x0, y0, x1, y1 = box
        # A dashed perimeter redundantly marks inferred or provisional objects.
        plate.dashed_line((x0 + radius, y0), (x1 - radius, y0),
                          fill=tone, width=width, dash=18, gap=11)
        plate.dashed_line((x1, y0 + radius), (x1, y1 - radius),
                          fill=tone, width=width, dash=18, gap=11)
        plate.dashed_line((x1 - radius, y1), (x0 + radius, y1),
                          fill=tone, width=width, dash=18, gap=11)
        plate.dashed_line((x0, y1 - radius), (x0, y0 + radius),
                          fill=tone, width=width, dash=18, gap=11)
        return
    plate.draw.rounded_rectangle(
        box, radius=radius, fill=hex_rgba(_tint(tone, .88), alpha),
        outline=hex_rgba(tone, 210), width=width,
    )


def _tag(plate: Plate, center: Point, value: str, tone: str, *, size: int = 24) -> None:
    plate.label(center, value, size=max(size, 24), fill=tone)


def _footer(plate: Plate, value: str, *, tone: str | None = None,
            size: int = 27) -> None:
    tone = tone or plate.accent
    plate.draw.rounded_rectangle(
        (170, 816, 1430, 881), radius=25,
        fill=hex_rgba(_tint(tone, .78), 218),
        outline=hex_rgba(tone, 180), width=3,
    )
    plate.text((800, 849), value, size=size, bold=True, fill=tone, anchor="mm")


def _arrow(plate: Plate, start: Point, end: Point, tone: str, label: str = "",
           *, width: int = 7, head: int = 20, label_dy: float = -23) -> None:
    plate.arrow(start, end, fill=tone, width=width, head=head)
    if label:
        plate.text(((start[0] + end[0]) / 2,
                    (start[1] + end[1]) / 2 + label_dy),
                   label, size=21, bold=True, fill=tone, anchor="mm")


def _center_lines(plate: Plate, center: Point, lines: Sequence[str], *,
                  size: int = 26, gap: int = 8, bold: bool = False,
                  fill: str = INK) -> None:
    line_height = size + gap
    y = center[1] - (len(lines) - 1) * line_height / 2
    for line in lines:
        plate.text((center[0], y), line, size=size, bold=bold,
                   fill=fill, anchor="mm")
        y += line_height


def _wrapped(plate: Plate, box: Box, value: str, *, size: int = 24,
             bold: bool = False, fill: str = INK) -> None:
    plate.wrapped_text(tuple(int(v) for v in box), value, size=size,
                       bold=bold, fill=fill, line_gap=7)


def _document(plate: Plate, box: Box, tone: str, *, fold: bool = True) -> None:
    x0, y0, x1, y1 = box
    plate.draw.rounded_rectangle(box, radius=15,
                                 fill=hex_rgba(PAPER_LIGHT, 245),
                                 outline=tone, width=4)
    if fold:
        plate.draw.polygon(((x1 - 54, y0), (x1, y0 + 54),
                            (x1 - 54, y0 + 54)),
                           fill=_tint(tone, .65), outline=tone)


def _open_book(plate: Plate, box: Box, tone: str) -> Tuple[Box, Box]:
    x0, y0, x1, y1 = box
    mid = (x0 + x1) / 2
    plate.draw.polygon(((x0, y0 + 18), (mid - 10, y0),
                        (mid - 10, y1), (x0 + 18, y1 - 20)),
                       fill=hex_rgba(PAPER_LIGHT, 248), outline=tone)
    plate.draw.polygon(((mid + 10, y0), (x1, y0 + 18),
                        (x1 - 18, y1 - 20), (mid + 10, y1)),
                       fill=hex_rgba(PAPER_LIGHT, 248), outline=tone)
    plate.draw.line((mid, y0 + 7, mid, y1 - 3), fill=EDGE, width=5)
    return ((x0 + 30, y0 + 32, mid - 32, y1 - 30),
            (mid + 32, y0 + 32, x1 - 30, y1 - 30))


def _node(plate: Plate, center: Point, heading: str, detail: str, tone: str,
          *, size: Tuple[float, float] = (260, 120), shape: str = "round",
          dashed: bool = False, detail_size: int = 22) -> Box:
    x, y = center
    w, h = size
    box = (x - w / 2, y - h / 2, x + w / 2, y + h / 2)
    if shape == "diamond":
        points = ((x, y - h / 2), (x + w / 2, y),
                  (x, y + h / 2), (x - w / 2, y))
        plate.draw.polygon(points, fill=hex_rgba(_tint(tone, .86), 230),
                           outline=tone)
        plate.draw.line(points + (points[0],), fill=tone, width=4)
    else:
        _panel(plate, box, tone, radius=22 if shape == "round" else 8,
               dashed=dashed)
    plate.text((x, y - 22), heading, size=23, bold=True,
               fill=tone, anchor="mm")
    detail_face = font(detail_size, bold=True)
    if plate.draw.textlength(detail, font=detail_face) > w - 38:
        _wrapped(plate, (x - w / 2 + 24, y + 1,
                         x + w / 2 - 24, y + h / 2 - 8),
                 detail, size=detail_size, bold=True)
    else:
        plate.text((x, y + 24), detail, size=detail_size, bold=True,
                   fill=INK, anchor="mm")
    return box


def _check_mark(plate: Plate, center: Point, tone: str, *, scale: float = 1.0) -> None:
    x, y = center
    plate.draw.line((x - 17 * scale, y, x - 4 * scale, y + 14 * scale,
                     x + 23 * scale, y - 20 * scale),
                    fill=tone, width=max(4, int(7 * scale)), joint="curve")


def _cross_mark(plate: Plate, center: Point, tone: str, *, scale: float = 1.0) -> None:
    x, y = center
    d = 16 * scale
    plate.draw.line((x - d, y - d, x + d, y + d), fill=tone,
                    width=max(4, int(6 * scale)))
    plate.draw.line((x - d, y + d, x + d, y - d), fill=tone,
                    width=max(4, int(6 * scale)))


def _scroll(plate: Plate, box: Box, tone: str) -> None:
    x0, y0, x1, y1 = box
    plate.draw.rounded_rectangle((x0 + 17, y0, x1 - 17, y1), radius=12,
                                 fill=hex_rgba(PAPER_LIGHT, 244),
                                 outline=tone, width=4)
    plate.draw.ellipse((x0, y0 - 8, x0 + 34, y0 + 24),
                       fill=_tint(tone, .65), outline=tone, width=3)
    plate.draw.ellipse((x1 - 34, y1 - 24, x1, y1 + 8),
                       fill=_tint(tone, .65), outline=tone, width=3)


def _render_literature(plate: Plate) -> None:
    _tag(plate, (395, 216), "TEXTUAL EVIDENCE", BLUE)
    left, right = _open_book(plate, (110, 262, 770, 760), BLUE)
    # Two repeated details are highlighted in the passage itself.
    plate.text((left[0], left[1] + 18), "At dusk, Mara", size=24, fill=INK)
    plate.text((left[0], left[1] + 57), "reached the hall.", size=24, fill=INK)
    plate.draw.rounded_rectangle((left[0] - 5, left[1] + 101,
                                  left[2] - 5, left[1] + 150),
                                 radius=9, fill=hex_rgba(GOLD_LIGHT, 225),
                                 outline=GOLD, width=3)
    plate.text((left[0] + 5, left[1] + 125), "the door stayed locked",
               size=21, bold=True, fill=INK, anchor="lm")
    plate.text((left[0], left[1] + 191), "She waited outside.",
               size=23, fill=INK)
    plate.text((right[0], right[1] + 18), "At dawn, the", size=24, fill=INK)
    plate.text((right[0], right[1] + 57), "key turned away.", size=24, fill=INK)
    plate.draw.rounded_rectangle((right[0] - 5, right[1] + 101,
                                  right[2] - 5, right[1] + 150),
                                 radius=9, fill=hex_rgba(GOLD_LIGHT, 225),
                                 outline=GOLD, width=3)
    plate.text((right[0] + 5, right[1] + 125), "again: barred entry",
               size=21, bold=True, fill=INK, anchor="lm")
    plate.text((right[0], right[1] + 191), "The image repeats.",
               size=23, fill=INK)
    plate.draw.line((left[0], left[1] + 257, left[2], left[1] + 257),
                    fill=hex_rgba(GRID, 180), width=3)
    plate.draw.line((right[0], right[1] + 257, right[2], right[1] + 257),
                    fill=hex_rgba(GRID, 180), width=3)
    plate.text((440, 714), "quoted detail + recurrence", size=23,
               bold=True, fill=BLUE, anchor="mm")

    _node(plate, (1010, 388), "PATTERN", "barriers exclude Mara",
          TEAL, size=(390, 150), detail_size=22)
    _node(plate, (1255, 650), "QUALIFIED THEME",
          "belonging is made conditional", PLUM,
          size=(410, 160), dashed=True, detail_size=22)
    _arrow(plate, (770, 442), (812, 420), TEAL)
    _arrow(plate, (1095, 462), (1180, 563), PLUM, "supports")
    plate.text((1015, 776), "inference, not a hidden label", size=22,
               bold=True, fill=PLUM, anchor="mm")
    _footer(plate, "detail -> repeated pattern -> interpretation with a visible warrant", size=25)


def _genre_track(plate: Plate, box: Box, tone: str, labels: Sequence[str],
                 heights: Sequence[float], *, marker: str) -> None:
    x0, y0, x1, y1 = box
    xs = [x0 + i * (x1 - x0) / (len(labels) - 1) for i in range(len(labels))]
    ys = [y1 - value * (y1 - y0) for value in heights]
    plate.polyline(zip(xs, ys), fill=tone, width=8)
    for index, (x, y, label) in enumerate(zip(xs, ys, labels)):
        if marker == "circle":
            plate.dot((x, y), 14, fill=PAPER_LIGHT, outline=tone, width=5)
        else:
            plate.draw.polygon(((x, y - 16), (x + 16, y + 14),
                                (x - 16, y + 14)),
                               fill=PAPER_LIGHT, outline=tone)
        align_y = y - 43 if index % 2 == 0 else y + 47
        plate.text((x, align_y), label, size=19, bold=True,
                   fill=tone, anchor="mm")


def _render_shakespeare(plate: Plate) -> None:
    _panel(plate, (105, 225, 780, 780), TEAL)
    _panel(plate, (820, 225, 1495, 780), CORAL)
    _tag(plate, (442, 267), "COMIC TRAJECTORY", TEAL)
    _tag(plate, (1158, 267), "TRAGIC TRAJECTORY", CORAL)

    _genre_track(plate, (165, 350, 720, 660), TEAL,
                 ("desire", "block", "confusion", "recognition", "reunion"),
                 (.35, .18, .42, .68, .83), marker="circle")
    plate.draw.line((220, 681, 665, 681), fill=TEAL, width=4)
    plate.draw.line((220, 672, 220, 690), fill=TEAL, width=4)
    plate.draw.line((665, 672, 665, 690), fill=TEAL, width=4)
    plate.text((442, 724), "renewed social relation (often)", size=22,
               bold=True, fill=TEAL, anchor="mm")

    _genre_track(plate, (880, 350, 1435, 660), CORAL,
                 ("choice", "pressure", "reversal", "recognition", "loss"),
                 (.73, .85, .55, .37, .12), marker="triangle")
    plate.text((1158, 724), "loss remains irreversible (often)", size=22,
               bold=True, fill=CORAL, anchor="mm")
    plate.text((800, 796), "genre expectations guide inference; individual plays complicate them",
               size=22, bold=True, fill=INK_SOFT, anchor="mm")
    _footer(plate, "recognition can reopen a comedy; tragic recognition may arrive too late", size=24)


def _tradition_card(plate: Plate, box: Box, tone: str, title: str,
                    witness: str, question: str, marker: str) -> None:
    _panel(plate, box, tone)
    x0, y0, x1, y1 = box
    plate.text(((x0 + x1) / 2, y0 + 48), title, size=25,
               bold=True, fill=tone, anchor="mm")
    cx = (x0 + x1) / 2
    if marker == "tablet":
        plate.draw.rounded_rectangle((cx - 58, y0 + 88, cx + 58, y0 + 177),
                                     radius=12, fill=hex_rgba(GOLD_LIGHT, 235),
                                     outline=tone, width=4)
        for row in range(3):
            for col in range(4):
                px = cx - 37 + col * 25
                py = y0 + 111 + row * 22
                plate.draw.line((px - 6, py - 4, px + 5, py + 3,
                                 px - 1, py + 9), fill=tone, width=2)
    elif marker == "folio":
        _document(plate, (cx - 58, y0 + 85, cx + 58, y0 + 180), tone,
                  fold=False)
        for row in range(3):
            plate.draw.line((cx - 37, y0 + 111 + row * 20,
                             cx + 37, y0 + 111 + row * 20),
                            fill=hex_rgba(tone, 170), width=3)
    else:
        plate.draw.arc((cx - 66, y0 + 87, cx + 66, y0 + 180),
                       205, 335, fill=tone, width=6)
        for radius in (28, 50):
            plate.draw.arc((cx - radius, y0 + 103,
                            cx + radius, y0 + 159), 205, 335,
                           fill=tone, width=4)
        plate.dot((cx, y0 + 131), 9, fill=tone, outline=tone, width=1)
    plate.text((cx, y0 + 212), marker.upper(), size=20,
               bold=True, fill=tone, anchor="mm")
    _wrapped(plate, (x0 + 26, y0 + 235, x1 - 26, y0 + 322), witness,
             size=21, bold=True)
    plate.draw.line((x0 + 28, y0 + 340, x1 - 28, y0 + 340),
                    fill=hex_rgba(GRID, 180), width=3)
    _wrapped(plate, (x0 + 26, y0 + 355, x1 - 26, y1 - 22), question,
             size=21, fill=INK_SOFT)


def _render_world_lit(plate: Plate) -> None:
    _tradition_card(plate, (105, 235, 535, 738), GOLD, "GILGAMESH",
                    "clay-tablet witnesses; Mesopotamian epic",
                    "mortality and responsible kingship", "tablet")
    _tradition_card(plate, (585, 235, 1015, 738), BLUE, "MAHABHARATA",
                    "Sanskrit epic traditions; layered transmission",
                    "duty amid kinship conflict", "folio")
    _tradition_card(plate, (1065, 235, 1495, 738), TEAL, "SUNDIATA",
                    "Mande oral performance traditions",
                    "founding, authority and communal memory", "voice")
    plate.text((800, 780), "compare a question  |  preserve form, language, history and community",
               size=22, bold=True, fill=INK_SOFT, anchor="mm")
    _footer(plate, "texts can travel through comparison without becoming interchangeable", size=24)


def _render_rhetoric(plate: Plate) -> None:
    _node(plate, (800, 485), "PROPOSAL", "add a marked crossing", GOLD,
          size=(410, 150), shape="diamond", detail_size=23)
    supports = (
        ((325, 330), "ETHOS", "engineer reviews the site", BLUE, "seal"),
        ((1275, 330), "PATHOS", "a child's risky walk", CORAL, "voice"),
        ((800, 665), "LOGOS", "counts + stopping distance", TEAL, "graph"),
    )
    for center, heading, detail, tone, icon in supports:
        _node(plate, center, heading, detail, tone, size=(390, 145),
              detail_size=21)
    _arrow(plate, (488, 369), (642, 438), BLUE, "credibility", label_dy=-37)
    _arrow(plate, (1112, 369), (958, 438), CORAL, "felt stakes", label_dy=-37)
    _arrow(plate, (800, 592), (800, 566), TEAL, "reasoning",
           label_dy=-31)

    plate.draw.rounded_rectangle((215, 752, 1385, 805), radius=21,
                                 fill=hex_rgba(PLUM_LIGHT, 215),
                                 outline=PLUM, width=3)
    _check_mark(plate, (260, 778), PLUM, scale=.65)
    plate.text((800, 778), "INTEGRITY CHECK: true evidence + valid inference + no manipulation",
               size=23, bold=True, fill=PLUM, anchor="mm")
    _footer(plate, "ethos, pathos and logos can cooperate; none licenses dishonesty", size=24)


def _render_essays(plate: Plate) -> None:
    _tag(plate, (800, 215), "ARGUMENT MAP: LATER BUSES AND ATTENDANCE", PLUM)
    evidence = _node(plate, (245, 435), "EVIDENCE [E]",
                     "absences follow missed transfers", BLUE,
                     size=(320, 150), detail_size=21)
    warrant = _node(plate, (625, 435), "WARRANT [W]",
                    "some missed transfers cause absence", TEAL,
                    size=(340, 150), shape="diamond", detail_size=20)
    claim = _node(plate, (1040, 360), "QUALIFIED THESIS [T]",
                  "later buses may improve attendance", GOLD,
                  size=(390, 155), dashed=True, detail_size=21)
    _arrow(plate, (evidence[2] + 8, 435), (warrant[0] - 8, 435), BLUE)
    _arrow(plate, (warrant[2] + 8, 416), (claim[0] - 8, 389), TEAL)

    _node(plate, (500, 670), "COUNTERARGUMENT [C]",
          "a later route costs more", CORAL,
          size=(390, 135), detail_size=21)
    _node(plate, (965, 670), "RESPONSE + SCOPE [R]",
          "pilot one route; measure both effects", PLUM,
          size=(450, 135), detail_size=21)
    _node(plate, (1370, 500), "JUDGMENT", "test + revise",
          GREEN, size=(220, 145), detail_size=20)
    _arrow(plate, (695, 670), (740, 670), CORAL)
    _arrow(plate, (1185, 640), (1270, 545), PLUM)
    plate.dashed_line((1040, 438), (1040, 596), fill=GOLD,
                      width=4, dash=14, gap=10)
    plate.text((1040, 521), "scope: may | pilot | measure",
               size=20, bold=True, fill=GOLD, anchor="mm")
    _footer(plate, "evidence needs a warrant; objections sharpen a bounded conclusion", size=24)


def _sound_wave(plate: Plate, box: Box, tone: str) -> None:
    x0, y0, x1, y1 = box
    mid = (y0 + y1) / 2
    points = []
    for index in range(90):
        x = x0 + index * (x1 - x0) / 89
        phase = index / 6
        envelope = .35 + .65 * math.sin(math.pi * index / 89) ** 2
        y = mid + math.sin(phase) * envelope * (y1 - y0) * .34
        points.append((x, y))
    plate.polyline(points, fill=tone, width=5)


def _cat_face(plate: Plate, center: Point, tone: str, *, scale: float = 1.0) -> None:
    x, y = center
    r = 25 * scale
    plate.draw.ellipse((x - r, y - r, x + r, y + r),
                       fill=hex_rgba(_tint(tone, .62), 235),
                       outline=tone, width=max(2, int(4 * scale)))
    plate.draw.polygon(((x - r * .78, y - r * .7),
                        (x - r * .45, y - r * 1.45),
                        (x - r * .12, y - r * .72)),
                       fill=_tint(tone, .62), outline=tone)
    plate.draw.polygon(((x + r * .12, y - r * .72),
                        (x + r * .45, y - r * 1.45),
                        (x + r * .78, y - r * .7)),
                       fill=_tint(tone, .62), outline=tone)
    plate.dot((x - r * .35, y - r * .05), max(2, 3 * scale),
              fill=INK, outline=INK, width=1)
    plate.dot((x + r * .35, y - r * .05), max(2, 3 * scale),
              fill=INK, outline=INK, width=1)


def _render_linguistics_intro(plate: Plate) -> None:
    _tag(plate, (800, 192), "ONE UTTERANCE, INTERACTING LEVELS", BLUE, size=18)
    # The left labels and distinct row shapes make the hierarchy readable
    # without the palette.
    rows = ((260, "SOUND", BLUE), (390, "MORPHEME", GOLD),
            (530, "SYNTAX", PLUM), (690, "MEANING", TEAL))
    for y, label, tone in rows:
        plate.draw.rounded_rectangle((105, y - 44, 310, y + 44), radius=20,
                                     fill=hex_rgba(_tint(tone, .82), 225),
                                     outline=tone, width=4)
        plate.text((207, y), label, size=22, bold=True,
                   fill=tone, anchor="mm")

    _panel(plate, (345, 215, 1495, 305), BLUE, radius=18)
    _sound_wave(plate, (390, 235, 765, 287), BLUE)
    plate.draw.text((830, 260), "/kæts/  /sliːp/", font=_ipa_font(31),
                    fill=INK, anchor="lm")
    plate.text((1255, 260), "contrastive forms", size=23,
               bold=True, fill=BLUE, anchor="mm")

    _panel(plate, (345, 330, 1495, 450), GOLD, radius=18)
    for box, value, tone in (((395, 354, 640, 424), "cat", GOLD),
                             ((655, 354, 845, 424), "-s", CORAL),
                             ((910, 354, 1210, 424), "sleep", TEAL)):
        _panel(plate, box, tone, radius=16)
        plate.text(((box[0] + box[2]) / 2, 389), value, size=32,
                   bold=True, fill=tone, anchor="mm")
    plate.text((1350, 389), "plural", size=22, bold=True,
               fill=CORAL, anchor="mm")

    _panel(plate, (345, 470, 1495, 605), PLUM, radius=18)
    plate.text((900, 493), "CLAUSE", size=21, bold=True,
               fill=PLUM, anchor="mm")
    plate.draw.line((900, 512, 650, 548), fill=PLUM, width=4)
    plate.draw.line((900, 512, 1165, 548), fill=PLUM, width=4)
    plate.text((650, 563), "NP: Cats", size=25, bold=True,
               fill=INK, anchor="mm")
    plate.text((1165, 563), "VP: sleep", size=25, bold=True,
               fill=INK, anchor="mm")

    _panel(plate, (345, 625, 1495, 780), TEAL, radius=18)
    for x in (635, 720, 805):
        _cat_face(plate, (x, 704), TEAL, scale=.9)
    plate.text((1040, 680), "more than one cat", size=23,
               bold=True, fill=TEAL, anchor="lm")
    plate.text((1040, 724), "is in a sleeping state", size=23,
               bold=True, fill=INK, anchor="lm")
    plate.text((1040, 758), "(compositional interpretation)", size=20,
               fill=INK_SOFT, anchor="lm")
    _footer(plate, "sounds form words; structured combinations support an interpretation", size=24)


def _render_media(plate: Plate) -> None:
    _tag(plate, (365, 216), "ONE DATASET: n = 100", BLUE)
    _panel(plate, (110, 250, 650, 775), BLUE)
    for row in range(10):
        for col in range(10):
            x = 155 + col * 49
            y = 294 + row * 46
            index = row * 10 + col
            if index < 90:
                plate.draw.ellipse((x - 13, y - 13, x + 13, y + 13),
                                   fill=hex_rgba(TEAL_LIGHT, 235),
                                   outline=TEAL, width=2)
                _check_mark(plate, (x, y), TEAL, scale=.35)
            else:
                plate.draw.rectangle((x - 13, y - 13, x + 13, y + 13),
                                     fill=hex_rgba(CORAL_LIGHT, 220),
                                     outline=CORAL, width=2)
                _cross_mark(plate, (x, y), CORAL, scale=.35)
    plate.text((380, 743), "90 checks  |  10 crosses", size=22,
               bold=True, fill=INK_SOFT, anchor="mm")

    _panel(plate, (760, 245, 1490, 420), TEAL)
    _tag(plate, (860, 282), "FRAME A", TEAL)
    plate.text((1125, 337), "90% SUCCESS", size=39,
               bold=True, fill=TEAL, anchor="mm")
    plate.text((1125, 381), "numerator: 90 of 100", size=22,
               fill=INK_SOFT, anchor="mm")
    _panel(plate, (760, 455, 1490, 630), CORAL)
    _tag(plate, (860, 492), "FRAME B", CORAL)
    plate.text((1125, 547), "10% DID NOT", size=39,
               bold=True, fill=CORAL, anchor="mm")
    plate.text((1125, 591), "complement: 10 of 100", size=22,
               fill=INK_SOFT, anchor="mm")
    _arrow(plate, (652, 400), (747, 342), TEAL)
    _arrow(plate, (652, 505), (747, 538), CORAL)

    plate.draw.rounded_rectangle((760, 670, 1490, 780), radius=22,
                                 fill=hex_rgba(PLUM_LIGHT, 216),
                                 outline=PLUM, width=4)
    plate.text((800, 700), "SOURCE CHECK", size=21,
               bold=True, fill=PLUM)
    plate.text((800, 742), "Who was counted?  What comparison?  Which method?",
               size=20, bold=True, fill=INK)
    _footer(plate, "different headlines can preserve the numbers while changing emphasis", size=24)


def _render_second_language(plate: Plate) -> None:
    _tag(plate, (800, 215), "SPACED PRACTICE LOOP", TEAL)
    center = (800, 495)
    radius = 260
    items = (
        (-math.pi / 2, "1  INPUT", "hear a phrase in context", BLUE, "ear"),
        (0, "2  NOTICE", "connect form + meaning", GOLD, "link"),
        (math.pi / 2, "3  RETRIEVE", "recall without copying", PLUM, "blank"),
        (math.pi, "4  USE + FEEDBACK", "speak, adjust, return", CORAL, "voice"),
    )
    positions = []
    for angle, heading, detail, tone, marker in items:
        x = center[0] + math.cos(angle) * radius
        y = center[1] + math.sin(angle) * 205
        positions.append((x, y))
        _node(plate, (x, y), heading, detail, tone,
              size=(360 if marker == "voice" else 310, 125),
              detail_size=20)
    for index, current in enumerate(positions):
        target = positions[(index + 1) % len(positions)]
        # Short tangential arrows keep the circular reading order explicit.
        sx = current[0] + (target[0] - current[0]) * .30
        sy = current[1] + (target[1] - current[1]) * .30
        tx = current[0] + (target[0] - current[0]) * .67
        ty = current[1] + (target[1] - current[1]) * .67
        _arrow(plate, (sx, sy), (tx, ty), TEAL, width=5, head=16)
    plate.draw.ellipse((718, 419, 882, 583),
                       fill=hex_rgba(GREEN_LIGHT, 224), outline=GREEN, width=5)
    plate.text((800, 468), "RETURN", size=23, bold=True,
               fill=GREEN, anchor="mm")
    plate.text((800, 514), "tomorrow", size=25, bold=True,
               fill=INK, anchor="mm")
    plate.text((800, 548), "then later", size=20,
               fill=INK_SOFT, anchor="mm")
    # Increasing bars encode strengthened access without relying on colour.
    for index, height in enumerate((18, 32, 48, 67)):
        x = 1180 + index * 58
        plate.draw.rectangle((x, 780 - height, x + 34, 780),
                             fill=hex_rgba(GREEN, 165), outline=GREEN, width=2)
        plate.text((x + 17, 796), str(index + 1), size=17,
                   bold=True, fill=GREEN, anchor="mm")
    plate.text((1295, 684), "ACCESS AFTER\nSPACED RETRIEVAL",
               size=20, bold=True, fill=GREEN, anchor="mm")
    _footer(plate, "meaningful use + feedback + spaced return build usable access", size=24)


def _quadrant(plate: Plate, box: Box, tone: str, heading: str) -> Box:
    _panel(plate, box, tone, radius=20)
    x0, y0, x1, y1 = box
    _tag(plate, ((x0 + x1) / 2, y0 + 37), heading, tone, size=21)
    return (x0 + 24, y0 + 78, x1 - 24, y1 - 18)


def _render_linguistics(plate: Plate) -> None:
    plate.draw.rounded_rectangle((465, 201, 1135, 266), radius=22,
                                 fill=hex_rgba(GOLD_LIGHT, 226),
                                 outline=GOLD, width=4)
    plate.text((800, 233), "Those dogs bark.", size=34,
               bold=True, fill=INK, anchor="mm")
    boxes = ((100, 295, 760, 520), (840, 295, 1500, 520),
             (100, 550, 760, 790), (840, 550, 1500, 790))
    sound = _quadrant(plate, boxes[0], BLUE, "PHONOLOGY  ~")
    _sound_wave(plate, (sound[0] + 10, sound[1] + 15,
                        sound[2] - 10, sound[1] + 75), BLUE)
    plate.text(((sound[0] + sound[2]) / 2, sound[3] - 34),
               "prosodic phrase + sound contrasts", size=21,
               bold=True, fill=INK, anchor="mm")

    morph = _quadrant(plate, boxes[1], GOLD, "MORPHOSYNTAX  +")
    entries = (("those", "DEM  NUM:pl"), ("dog + -s", "N  NUM:pl"),
               ("bark", "V  agrees:pl"))
    for index, (form, feature) in enumerate(entries):
        y = morph[1] + 24 + index * 42
        plate.text((morph[0] + 25, y), form, size=22, bold=True,
                   fill=GOLD, anchor="lm")
        plate.text((morph[0] + 285, y), feature, size=20,
                   fill=INK, anchor="lm")

    syntax = _quadrant(plate, boxes[2], PLUM, "SYNTAX  Y")
    root = ((syntax[0] + syntax[2]) / 2, syntax[1] + 25)
    np = (syntax[0] + 170, syntax[1] + 68)
    vp = (syntax[2] - 150, syntax[1] + 68)
    plate.text(root, "S", size=24, bold=True, fill=PLUM, anchor="mm")
    for point, label in ((np, "NP"), (vp, "VP")):
        plate.draw.line((root[0], root[1] + 14, point[0], point[1] - 15),
                        fill=PLUM, width=4)
        plate.text(point, label, size=23, bold=True, fill=PLUM, anchor="mm")
    plate.draw.line((np[0], np[1] + 14, np[0] - 80, np[1] + 37),
                    fill=PLUM, width=3)
    plate.draw.line((np[0], np[1] + 14, np[0] + 80, np[1] + 37),
                    fill=PLUM, width=3)
    plate.text((np[0] - 80, np[1] + 55), "Those", size=20,
               fill=INK, anchor="mm")
    plate.text((np[0] + 80, np[1] + 55), "dogs", size=20,
               fill=INK, anchor="mm")
    plate.draw.line((vp[0], vp[1] + 14, vp[0], vp[1] + 37),
                    fill=PLUM, width=3)
    plate.text((vp[0], vp[1] + 55), "bark", size=20,
               fill=INK, anchor="mm")

    sem = _quadrant(plate, boxes[3], TEAL, "SEMANTICS [MEANING]")
    for x in (sem[0] + 75, sem[0] + 150, sem[0] + 225):
        _cat_face(plate, (x, sem[1] + 72), TEAL, scale=.72)
    plate.text((sem[0] + 305, sem[1] + 57), "context picks a dog group",
               size=20, bold=True, fill=INK, anchor="lm")
    plate.text((sem[0] + 305, sem[1] + 99), "bark' applies to that group",
               size=20, bold=True, fill=TEAL, anchor="lm")
    _footer(plate, "each representation captures a different, testable regularity", size=24)


def _lens(plate: Plate, center: Point, tone: str, heading: str,
          question: str) -> None:
    x, y = center
    plate.draw.ellipse((x - 110, y - 110, x + 110, y + 110),
                       fill=hex_rgba(_tint(tone, .86), 218),
                       outline=tone, width=6)
    plate.draw.line((x + 78, y + 78, x + 142, y + 142),
                    fill=tone, width=14)
    plate.text((x, y - 50), heading, size=18, bold=True,
               fill=tone, anchor="mm")
    _wrapped(plate, (x - 74, y - 22, x + 74, y + 64), question,
             size=17, bold=True)


def _render_lit_theory(plate: Plate) -> None:
    _document(plate, (555, 310, 1045, 675), GOLD, fold=False)
    _tag(plate, (800, 342), "SAME PASSAGE", GOLD)
    plate.text((800, 420), "“At dawn, the gate opened,", size=27,
               bold=True, fill=INK, anchor="mm")
    plate.text((800, 463), "but no one crossed.”", size=27,
               bold=True, fill=INK, anchor="mm")
    plate.draw.line((620, 503, 980, 503), fill=hex_rgba(GRID, 190), width=3)
    plate.text((800, 552), "evidence remains shared", size=22,
               bold=True, fill=GOLD, anchor="mm")
    plate.text((800, 594), "questions and assumptions differ", size=21,
               fill=INK_SOFT, anchor="mm")

    lenses = (((280, 325), BLUE, "FORMAL", "How do gate and crossing relate?"),
              ((1320, 325), CORAL, "HISTORICAL", "Who made this boundary?"),
              ((280, 675), TEAL, "READER", "How do I respond to uncertainty?"),
              ((1320, 675), PLUM, "POST-STRUCTURAL", "Is inside / outside stable?"))
    for center, tone, heading, question in lenses:
        _lens(plate, center, tone, heading, question)
        x, y = center
        ex = 555 if x < 800 else 1045
        ey = 420 if y < 500 else 565
        plate.dashed_line((x + (110 if x < 800 else -110), y), (ex, ey),
                          fill=tone, width=4, dash=13, gap=10)
    plate.text((800, 772), "LENS = foregrounded question, not an automatic answer",
               size=22, bold=True, fill=PLUM, anchor="mm")
    _footer(plate, "interpretations remain accountable to text and stated assumptions", size=24)


def _magnifier(plate: Plate, center: Point, tone: str, *, radius: float = 52) -> None:
    x, y = center
    plate.draw.ellipse((x - radius, y - radius, x + radius, y + radius),
                       fill=hex_rgba(PAPER_LIGHT, 110), outline=tone, width=7)
    plate.draw.line((x + radius * .72, y + radius * .72,
                     x + radius * 1.55, y + radius * 1.55),
                    fill=tone, width=14)


def _render_creative(plate: Plate) -> None:
    _document(plate, (105, 255, 635, 670), CORAL)
    _tag(plate, (370, 300), "DRAFT", CORAL)
    plate.text((370, 405), "The storm was bad.", size=34,
               bold=True, fill=INK, anchor="mm")
    plate.draw.line((235, 434, 505, 434), fill=CORAL, width=5)
    plate.text((370, 486), "bad = vague evaluation", size=22,
               bold=True, fill=CORAL, anchor="mm")
    plate.text((370, 534), "no sound, surface or action", size=21,
               fill=INK_SOFT, anchor="mm")
    _magnifier(plate, (650, 470), GOLD, radius=56)
    _arrow(plate, (718, 470), (830, 470), GOLD)
    plate.text((756, 417), "choose\nevidence", size=20, bold=True, fill=GOLD, anchor="mm")

    _document(plate, (850, 255, 1495, 670), TEAL)
    _tag(plate, (1172, 300), "REVISION", TEAL)
    plate.text((1172, 397), "Rain hammered", size=36,
               bold=True, fill=INK, anchor="mm")
    plate.text((1172, 445), "the tin roof.", size=36,
               bold=True, fill=INK, anchor="mm")
    plate.draw.line((1135, 423, 1335, 423), fill=CORAL, width=5)
    plate.text((1090, 510), "precise verb", size=20,
               bold=True, fill=CORAL, anchor="mm")
    plate.draw.line((1094, 475, 1331, 475), fill=BLUE, width=5)
    plate.text((1261, 510), "sound + surface", size=20,
               bold=True, fill=BLUE, anchor="mm")
    for x in range(955, 1395, 36):
        plate.draw.line((x, 550, x + 20, 575), fill=BLUE, width=3)
    plate.draw.polygon(((980, 625), (1365, 625), (1325, 575), (1020, 575)),
                       fill=hex_rgba(BLUE_LIGHT, 180), outline=BLUE)
    plate.text((1172, 608), "tin roof: sensory consequence", size=20,
               bold=True, fill=BLUE, anchor="mm")

    stages = ((270, "1", "diagnose"), (590, "2", "revise"),
              (910, "3", "reread"), (1230, "4", "test fit"))
    for x, number, label in stages:
        plate.dot((x, 755), 29, fill=PAPER_LIGHT, outline=PLUM, width=5)
        plate.text((x, 755), number, size=22, bold=True,
                   fill=PLUM, anchor="mm")
        plate.text((x, 797), label, size=20, bold=True,
                   fill=PLUM, anchor="mm")
    for (x0, _, _), (x1, _, _) in zip(stages, stages[1:]):
        _arrow(plate, (x0 + 38, 755), (x1 - 38, 755), PLUM,
               width=4, head=14)
    _footer(plate, "revision changes what the reader senses, infers and remembers", size=24)


def _timeline_arrow(plate: Plate, y: float, tone: str) -> None:
    plate.arrow((135, y), (1465, y), fill=tone, width=5, head=18)


def _render_history_english(plate: Plate) -> None:
    _tag(plate, (800, 215), "ONE WORD: TWO RATES OF CHANGE", GOLD)
    xs = (245, 650, 1055, 1400)
    labels = ("c. 1000", "c. 1400", "EARLY MODERN", "PRESENT")
    _timeline_arrow(plate, 390, BLUE)
    _timeline_arrow(plate, 650, CORAL)
    plate.text((105, 355), "SOUND", size=22, bold=True, fill=BLUE)
    plate.text((105, 615), "SPELLING", size=22, bold=True, fill=CORAL)
    sound = ("initial /k/ + fricative audible", "consonants shifting",
             "sound changes accumulate", "/naɪt/")
    spelling = ("cniht", "knyght", "knight", "knight")
    for index, x in enumerate(xs):
        plate.dot((x, 390), 9, fill=BLUE if index == 3 else PAPER_LIGHT,
                  outline=BLUE, width=4)
        plate.draw.rectangle((x - 8, 642, x + 8, 658),
                             fill=CORAL if index == 3 else PAPER_LIGHT,
                             outline=CORAL, width=3)
        plate.text((x, 295), labels[index], size=21, bold=True,
                   fill=INK_SOFT, anchor="mm")
        if index == 3:
            plate.draw.text((x, 468), "/naɪt/", font=_ipa_font(24),
                            fill=BLUE, anchor="mm")
        else:
            _wrapped(plate, (x - 150, 415, x + 150, 520), sound[index],
                     size=20, bold=True, fill=BLUE)
        plate.text((x, 704), spelling[index], size=33, bold=True,
                   fill=CORAL, anchor="mm")
        plate.dashed_line((x, 527), (x, 618), fill=EDGE,
                          width=3, dash=11, gap=8)
    plate.draw.rounded_rectangle((1120, 735, 1490, 790), radius=18,
                                 fill=hex_rgba(GOLD_LIGHT, 220),
                                 outline=GOLD, width=3)
    plate.text((1305, 762), "k + gh remain as history", size=21,
               bold=True, fill=GOLD, anchor="mm")
    _footer(plate, "pronunciation changed faster than conventional spelling", size=25)


def _render_classics(plate: Plate) -> None:
    _tag(plate, (800, 215), "RECEPTION IS TRANSFORMATION", PLUM)
    # Two inherited epic streams converge, are redirected, then branch again.
    _scroll(plate, (105, 285, 400, 440), BLUE)
    plate.text((252, 326), "ILIAD", size=25, bold=True,
               fill=BLUE, anchor="mm")
    plate.text((252, 370), "battle + simile", size=21,
               fill=INK, anchor="mm")
    _scroll(plate, (105, 560, 400, 715), TEAL)
    plate.text((252, 601), "ODYSSEY", size=25, bold=True,
               fill=TEAL, anchor="mm")
    plate.text((252, 645), "journey + return", size=21,
               fill=INK, anchor="mm")

    _node(plate, (710, 500), "VIRGIL: AENEID", "selects + redirects",
          GOLD, size=(430, 205), shape="diamond", detail_size=22)
    _arrow(plate, (405, 363), (530, 451), BLUE, "reuse")
    _arrow(plate, (405, 637), (530, 549), TEAL, "reuse")
    plate.text((710, 555), "Roman history and imperial stakes",
               size=20, bold=True, fill=GOLD, anchor="mm")

    _document(plate, (945, 355, 1175, 645), CORAL)
    plate.text((1060, 412), "TRANSMISSION", size=21, bold=True,
               fill=CORAL, anchor="mm")
    for index, item in enumerate(("copy", "teach", "translate")):
        y = 475 + index * 55
        plate.text((990, y), str(index + 1), size=19, bold=True,
                   fill=CORAL, anchor="mm")
        plate.text((1030, y), item, size=22, bold=True,
                   fill=INK, anchor="lm")
    _arrow(plate, (915, 500), (938, 500), CORAL)

    branches = ((1360, 325, "IMITATE", "[I]"),
                (1360, 500, "REVISE", "[R]"),
                (1360, 675, "RESIST", "[X]"))
    for x, y, label, marker in branches:
        _panel(plate, (1240, y - 63, 1490, y + 63), PLUM, radius=19)
        plate.text((1270, y), marker, size=26, bold=True,
                   fill=PLUM, anchor="lm")
        plate.text((1374, y), label, size=22, bold=True,
                   fill=PLUM, anchor="mm")
        plate.draw.line((1178, 500, 1238, y), fill=PLUM, width=4)
    plate.text((800, 768), "later works inherit earlier choices, not an unchanged template",
               size=22, bold=True, fill=INK_SOFT, anchor="mm")
    _footer(plate, "influence becomes visible as selective reuse, redirection and response", size=24)


def _render_comp_lit(plate: Plate) -> None:
    _tag(plate, (800, 211), "COMPARISON WITH CONTEXT", TEAL)
    # A matrix forces the comparison to stay on matched dimensions.
    x_edges = (105, 480, 1120, 1495)
    y_edges = (255, 340, 455, 570, 685)
    headings = (("TEXT A", BLUE), ("RELATION", GOLD), ("TEXT B", CORAL))
    for index, (heading, tone) in enumerate(headings):
        x0, x1 = x_edges[index], x_edges[index + 1]
        _panel(plate, (x0, y_edges[0], x1, y_edges[-1]), tone, radius=18)
        plate.text(((x0 + x1) / 2, 296), heading, size=23,
                   bold=True, fill=tone, anchor="mm")
    rows = (
        ("FORM", "wording + structure", "similar device? different effect", "wording + structure"),
        ("CONTEXT", "language + setting A", "circulation / contact / contrast", "language + setting B"),
        ("STAKES", "problem as framed in A", "shared question, unequal conditions", "problem as framed in B"),
    )
    for row, (label, a, relation, b) in enumerate(rows):
        y0, y1 = y_edges[row + 1], y_edges[row + 2]
        for x0, x1 in zip(x_edges, x_edges[1:]):
            plate.draw.line((x0, y0, x1, y0), fill=hex_rgba(GRID, 190), width=3)
        plate.text((800, y0 + 20), label, size=19, bold=True,
                   fill=GOLD, anchor="mm")
        _wrapped(plate, (130, y0 + 24, 455, y1 - 8), a,
                 size=20, bold=True)
        _wrapped(plate, (520, y0 + 24, 1080, y1 - 8), relation,
                 size=20, bold=True, fill=INK_SOFT)
        _wrapped(plate, (1145, y0 + 24, 1470, y1 - 8), b,
                 size=20, bold=True)

    _panel(plate, (290, 705, 1310, 812), PLUM, radius=18)
    plate.text((395, 756), "TRANSLATION", size=20, bold=True,
               fill=PLUM, anchor="mm")
    plate.draw.line((525, 756, 1075, 756), fill=PLUM, width=6)
    for index, (x, label) in enumerate(((550, "rhythm"),
                                        (800, "trade-offs"),
                                        (1050, "idiom"))):
        if index == 0:
            plate.dot((x, 756), 10, fill=PAPER_LIGHT,
                      outline=PLUM, width=4)
        elif index == 1:
            plate.draw.polygon(((x, 744), (x + 12, 756),
                                (x, 768), (x - 12, 756)),
                               fill=PAPER_LIGHT, outline=PLUM)
            plate.draw.line(((x, 744), (x + 12, 756), (x, 768),
                             (x - 12, 756), (x, 744)),
                            fill=PLUM, width=3)
        else:
            plate.draw.rectangle((x - 10, 746, x + 10, 766),
                                 fill=PAPER_LIGHT, outline=PLUM, width=4)
        plate.text((x, 788), label, size=18, bold=True,
                   fill=PLUM, anchor="mm")
    _footer(plate, "compare matched relations; state what translation foregrounds or loses", size=23)


def _render_philology(plate: Plate) -> None:
    _tag(plate, (800, 211), "MANUSCRIPT STEMMA: A REVISABLE HYPOTHESIS", PLUM)
    # Dashed nodes are reconstructed; solid nodes are surviving witnesses.
    _node(plate, (800, 305), "*A", "lost archetype", PLUM,
          size=(270, 110), dashed=True, detail_size=21)
    _node(plate, (515, 485), "*x", "shared innovation enters", GOLD,
          size=(320, 120), dashed=True, detail_size=20)
    _node(plate, (1085, 485), "*y", "different copied branch", BLUE,
          size=(320, 120), dashed=True, detail_size=20)
    plate.draw.line((800, 361, 515, 423), fill=EDGE, width=5)
    plate.draw.line((800, 361, 1085, 423), fill=EDGE, width=5)

    witnesses = ((300, "B", "... sea ...", GOLD, "SAME"),
                 (690, "C", "... sea ...", GOLD, "SAME"),
                 (1190, "D", "... see ...", BLUE, "ALT"))
    for x, siglum, reading, tone, marker in witnesses:
        _document(plate, (x - 135, 625, x + 135, 770), tone)
        plate.text((x, 663), f"[{marker}]  {siglum}", size=24,
                   bold=True, fill=tone, anchor="mm")
        plate.text((x, 718), reading, size=25, bold=True,
                   fill=INK, anchor="mm")
    plate.draw.line((515, 547, 300, 623), fill=GOLD, width=5)
    plate.draw.line((515, 547, 690, 623), fill=GOLD, width=5)
    plate.draw.line((1085, 547, 1190, 623), fill=BLUE, width=5)
    plate.draw.rounded_rectangle((1250, 360, 1490, 535), radius=20,
                                 fill=hex_rgba(TEAL_LIGHT, 215),
                                 outline=TEAL, width=4)
    plate.text((1370, 401), "LEGEND", size=20, bold=True,
               fill=TEAL, anchor="mm")
    plate.text((1370, 443), "- - inferred", size=19, bold=True,
               fill=INK, anchor="mm")
    plate.text((1370, 479), "— surviving", size=19, bold=True,
               fill=INK, anchor="mm")
    plate.text((1370, 515), "B = C shared variant", size=18,
               bold=True, fill=INK, anchor="mm")
    plate.text((800, 790), "B + C share a reading: descent clue, not automatic proof of correctness",
               size=21, bold=True, fill=INK_SOFT, anchor="mm")
    _footer(plate, "shared innovations suggest relationships; every reading still needs evaluation", size=23)


def _speaker(plate: Plate, center: Point, tone: str) -> None:
    x, y = center
    plate.draw.ellipse((x - 44, y - 95, x + 44, y - 7),
                       fill=hex_rgba(_tint(tone, .55), 235),
                       outline=tone, width=4)
    plate.draw.pieslice((x - 105, y - 18, x + 105, y + 150), 180, 360,
                        fill=hex_rgba(_tint(tone, .64), 230),
                        outline=tone, width=4)
    plate.text((x, y + 72), "SAME", size=21, bold=True,
               fill=tone, anchor="mm")
    plate.text((x, y + 104), "SPEAKER", size=21, bold=True,
               fill=tone, anchor="mm")


def _render_socioling(plate: Plate) -> None:
    _speaker(plate, (800, 465), GOLD)
    contexts = (
        ((290, 315), "FRIEND [1]", "Can you send it?", "shared context | speech", BLUE),
        ((1310, 315), "SEMINAR [2]", "Could you share the source?", "disciplinary audience | speech", TEAL),
        ((800, 715), "APPLICATION [3]", "Please provide the cited record.", "formal purpose | writing", PLUM),
    )
    for center, heading, utterance, context, tone in contexts:
        x, y = center
        width = 440 if x == 800 else 420
        _panel(plate, (x - width / 2, y - 105, x + width / 2, y + 105),
               tone)
        plate.text((x, y - 62), heading, size=22, bold=True,
                   fill=tone, anchor="mm")
        plate.text((x, y - 9), utterance, size=23, bold=True,
                   fill=INK, anchor="mm")
        plate.text((x, y + 48), context, size=19, bold=True,
                   fill=INK_SOFT, anchor="mm")
        ex = 690 if x < 800 else 910 if x > 800 else 800
        ey = 428 if y < 500 else 600
        plate.draw.line((x + (160 if x < 800 else -160 if x > 800 else 0),
                         y + (60 if y < 500 else -105), ex, ey),
                        fill=tone, width=5)
    plate.draw.rounded_rectangle((115, 566, 525, 790), radius=22,
                                 fill=hex_rgba(CORAL_LIGHT, 208),
                                 outline=CORAL, width=4)
    plate.text((320, 606), "REGISTER TRACKS", size=21,
               bold=True, fill=CORAL, anchor="mm")
    for index, pair in enumerate(("audience", "purpose", "medium", "identity stance")):
        plate.text((165, 651 + index * 38), f"{index + 1}. {pair}",
                   size=20, bold=True, fill=INK, anchor="lm")
    plate.text((1280, 666), "NOT A CORRECTNESS LADDER", size=21,
               bold=True, fill=CORAL, anchor="mm")
    plate.draw.line((1130, 706, 1430, 706), fill=CORAL, width=5)
    plate.draw.line((1130, 735, 1430, 735), fill=CORAL, width=5)
    _cross_mark(plate, (1280, 721), CORAL, scale=.8)
    plate.text((1280, 772), "every dialect has structure", size=21,
               bold=True, fill=TEAL, anchor="mm")
    _footer(plate, "register variation is systematic social meaning, not grammatical deficiency", size=23)


def _word_row(plate: Plate, words: Sequence[str], y: float,
              highlights: Iterable[int] = ()) -> Tuple[Tuple[float, float], ...]:
    widths = [max(118, plate.draw.textlength(word, font=font(23, bold=True)) + 42)
              for word in words]
    total = sum(widths) + 14 * (len(words) - 1)
    cursor = 800 - total / 2
    centers = []
    highlight_set = set(highlights)
    for index, (word, width) in enumerate(zip(words, widths)):
        tone = CORAL if index in highlight_set else BLUE
        _panel(plate, (cursor, y - 38, cursor + width, y + 38), tone,
               radius=15)
        plate.text((cursor + width / 2, y), word, size=23,
                   bold=True, fill=tone if index in highlight_set else INK,
                   anchor="mm")
        centers.append((cursor + width / 2, y))
        cursor += width + 14
    return tuple(centers)


def _render_psycholing(plate: Plate) -> None:
    _tag(plate, (800, 211), "INCREMENTAL PARSING", BLUE)
    words = ("While", "Anna", "dressed", "the", "baby", "played")
    centers = _word_row(plate, words, 300, highlights=(5,))
    for index, center in enumerate(centers):
        plate.text((center[0], 352), str(index + 1), size=18,
                   bold=True, fill=INK_SOFT, anchor="mm")

    _panel(plate, (105, 400, 720, 755), GOLD)
    _tag(plate, (412, 438), "FIRST COMMITMENT", GOLD)
    plate.text((412, 489), "While Anna dressed [the baby]", size=26,
               bold=True, fill=INK, anchor="mm")
    plate.text((412, 531), "temporary parse: baby = object", size=21,
               bold=True, fill=GOLD, anchor="mm")
    plate.text((412, 593), "SUBORDINATE CLAUSE", size=20,
               bold=True, fill=INK_SOFT, anchor="mm")
    plate.draw.line((240, 628, 412, 582, 585, 628), fill=GOLD, width=4)
    plate.text((240, 660), "Anna", size=21, bold=True,
               fill=INK, anchor="mm")
    plate.text((412, 660), "dressed", size=21, bold=True,
               fill=INK, anchor="mm")
    plate.text((585, 660), "baby [OBJ]", size=21, bold=True,
               fill=INK, anchor="mm")

    plate.draw.ellipse((746, 485, 854, 593),
                       fill=hex_rgba(CORAL_LIGHT, 230), outline=CORAL, width=6)
    plate.text((800, 520), "played", size=22, bold=True,
               fill=CORAL, anchor="mm")
    plate.text((800, 559), "CONFLICT", size=19, bold=True,
               fill=CORAL, anchor="mm")
    _cross_mark(plate, (800, 624), CORAL, scale=1.1)
    _arrow(plate, (725, 655), (875, 655), CORAL, "reanalyze")

    _panel(plate, (880, 400, 1495, 755), TEAL)
    _tag(plate, (1187, 438), "REVISED STRUCTURE", TEAL)
    _panel(plate, (935, 487, 1180, 675), BLUE, radius=18)
    _panel(plate, (1200, 487, 1440, 675), PLUM, radius=18)
    plate.text((1057, 525), "WHILE-CLAUSE", size=19,
               bold=True, fill=BLUE, anchor="mm")
    plate.text((1057, 578), "Anna dressed", size=23,
               bold=True, fill=INK, anchor="mm")
    plate.text((1057, 625), "(no object)", size=20,
               fill=INK_SOFT, anchor="mm")
    plate.text((1320, 525), "MAIN CLAUSE", size=19,
               bold=True, fill=PLUM, anchor="mm")
    plate.text((1320, 578), "the baby", size=23,
               bold=True, fill=INK, anchor="mm")
    plate.text((1320, 620), "played", size=23,
               bold=True, fill=PLUM, anchor="mm")
    plate.draw.line((1187, 690, 1187, 721), fill=TEAL, width=5)
    plate.text((1187, 730), "two clauses", size=20,
               bold=True, fill=TEAL, anchor="mm")
    _footer(plate, "later input can overturn an earlier attachment: comprehension is incremental", size=23)


def _render_comp_ling(plate: Plate) -> None:
    _tag(plate, (800, 211), "CORPUS -> MODEL -> BOUNDED CLAIM", BLUE)
    _panel(plate, (95, 250, 375, 770), BLUE)
    plate.text((235, 291), "DOCUMENTED CORPUS", size=20,
               bold=True, fill=BLUE, anchor="mm")
    for index, (label, width) in enumerate((("text + source", 190),
                                            ("metadata", 155),
                                            ("usage rights", 178),
                                            ("sampling notes", 170))):
        y = 360 + index * 78
        _document(plate, (235 - width / 2, y - 27,
                          235 + width / 2, y + 27), BLUE, fold=False)
        plate.text((235, y), label, size=19, bold=True,
                   fill=INK, anchor="mm")
    plate.text((235, 721), "what population?", size=20,
               bold=True, fill=BLUE, anchor="mm")

    _panel(plate, (435, 250, 750, 770), GOLD)
    plate.text((592, 291), "SPLIT + REPRESENT", size=20,
               bold=True, fill=GOLD, anchor="mm")
    _panel(plate, (480, 340, 705, 435), GOLD, radius=17)
    plate.text((592, 370), "TRAIN", size=22, bold=True,
               fill=GOLD, anchor="mm")
    plate.text((592, 407), "fit parameters", size=19,
               fill=INK, anchor="mm")
    plate.dashed_line((460, 485), (725, 485), fill=CORAL,
                      width=4, dash=13, gap=9)
    plate.text((592, 510), "NO LEAKAGE", size=19,
               bold=True, fill=CORAL, anchor="mm")
    _panel(plate, (480, 548, 705, 645), TEAL, radius=17)
    plate.text((592, 578), "HELD OUT", size=22, bold=True,
               fill=TEAL, anchor="mm")
    plate.text((592, 616), "evaluate later", size=19,
               fill=INK, anchor="mm")
    plate.text((592, 704), "tokens | features | annotations",
               size=19, bold=True, fill=INK_SOFT, anchor="mm")

    _panel(plate, (790, 330, 1065, 535), PLUM, radius=22)
    plate.text((927, 375), "MODEL [M]", size=23, bold=True,
               fill=PLUM, anchor="mm")
    _wrapped(plate, (825, 405, 1030, 505),
             "estimate a parse or next-token probability",
             size=20, bold=True)
    _arrow(plate, (754, 390), (780, 390), GOLD)
    plate.text((767, 357), "fit", size=19, bold=True,
               fill=GOLD, anchor="mm")
    _arrow(plate, (754, 590), (780, 493), TEAL)
    plate.text((758, 536), "test", size=19, bold=True,
               fill=TEAL, anchor="mm")

    _panel(plate, (1100, 250, 1505, 770), TEAL)
    plate.text((1302, 291), "EVALUATE + INSPECT", size=20,
               bold=True, fill=TEAL, anchor="mm")
    metrics = (("accuracy", .76, "A"), ("calibration", .61, "C"),
               ("subgroup error", .44, "E"))
    for index, (label, value, marker) in enumerate(metrics):
        y = 377 + index * 91
        plate.text((1145, y), f"[{marker}]", size=19, bold=True,
                   fill=TEAL, anchor="lm")
        plate.text((1182, y), label, size=19, bold=True,
                   fill=INK, anchor="lm")
        plate.draw.rounded_rectangle((1360, y - 15, 1470, y + 15), radius=12,
                                     fill=hex_rgba(GRID, 100), outline=GRID, width=2)
        plate.draw.rounded_rectangle((1360, y - 15,
                                      1360 + 110 * value, y + 15), radius=12,
                                     fill=hex_rgba(TEAL, 180), outline=TEAL, width=2)
    plate.draw.rounded_rectangle((1140, 650, 1465, 735), radius=18,
                                 fill=hex_rgba(CORAL_LIGHT, 215),
                                 outline=CORAL, width=3)
    plate.text((1302, 676), "CLAIM BOUNDARY", size=19,
               bold=True, fill=CORAL, anchor="mm")
    plate.text((1302, 713), "task + data + metric", size=21,
               bold=True, fill=INK, anchor="mm")
    _arrow(plate, (1072, 430), (1088, 430), PLUM, width=5, head=13)
    _footer(plate, "held-out performance measures a task; it does not prove human understanding", size=23)


def _event_symbol(plate: Plate, center: Point, label: str, tone: str,
                  marker: str) -> None:
    x, y = center
    if marker == "circle":
        plate.dot(center, 35, fill=PAPER_LIGHT, outline=tone, width=6)
    elif marker == "triangle":
        plate.draw.polygon(((x, y - 40), (x + 39, y + 33),
                            (x - 39, y + 33)),
                           fill=PAPER_LIGHT, outline=tone)
        plate.draw.line(((x, y - 40), (x + 39, y + 33),
                         (x - 39, y + 33), (x, y - 40)),
                        fill=tone, width=5)
    else:
        plate.draw.rectangle((x - 34, y - 34, x + 34, y + 34),
                             fill=PAPER_LIGHT, outline=tone, width=6)
    plate.text(center, label, size=23, bold=True, fill=tone, anchor="mm")


def _render_narratology(plate: Plate) -> None:
    _tag(plate, (265, 224), "STORY: CHRONOLOGY", BLUE)
    story_x = (300, 700, 1100)
    story = (("A", "departure", BLUE, "circle"),
             ("B", "discovery", GOLD, "triangle"),
             ("C", "return", CORAL, "square"))
    plate.arrow((205, 350), (1220, 350), fill=BLUE, width=6, head=20)
    for x, (label, detail, tone, marker) in zip(story_x, story):
        _event_symbol(plate, (x, 350), label, tone, marker)
        plate.text((x, 408), detail, size=21, bold=True,
                   fill=tone, anchor="mm")
    plate.text((1355, 350), "event time", size=21,
               bold=True, fill=BLUE, anchor="mm")

    _tag(plate, (275, 505), "DISCOURSE: TELLING ORDER", PLUM)
    discourse_x = (300, 700, 1100)
    reordered = (story[2], story[0], story[1])
    plate.arrow((205, 630), (1220, 630), fill=PLUM, width=6, head=20)
    for x, (label, detail, tone, marker) in zip(discourse_x, reordered):
        _event_symbol(plate, (x, 630), label, tone, marker)
        plate.text((x, 688), detail, size=21, bold=True,
                   fill=tone, anchor="mm")
    # Thin mappings expose that order changes while event identity persists.
    mapping = ((300, 700), (700, 1100), (1100, 300))
    for source_x, target_x in mapping:
        plate.dashed_line((source_x, 418), (target_x, 565),
                          fill=EDGE, width=3, dash=10, gap=8)

    # A focalization aperture shows the knowledge constraint separately.
    plate.draw.polygon(((1245, 505), (1490, 420), (1490, 700)),
                       fill=hex_rgba(TEAL_LIGHT, 105), outline=TEAL)
    plate.draw.ellipse((1207, 470, 1283, 546),
                       fill=hex_rgba(TEAL_LIGHT, 235), outline=TEAL, width=5)
    plate.dot((1245, 508), 9, fill=INK, outline=INK, width=1)
    plate.text((1365, 458), "FOCALIZATION", size=20,
               bold=True, fill=TEAL, anchor="mm")
    plate.text((1365, 739), "reader receives what\nthis observer can know",
               size=20, bold=True, fill=TEAL, anchor="mm")
    plate.draw.line((1280, 765, 1450, 765), fill=TEAL, width=4)
    plate.text((800, 783), "chronology A-B-C  |  narrated order C-A-B  |  knowledge is filtered",
               size=21, bold=True, fill=INK_SOFT, anchor="mm")
    _footer(plate, "presentation changes inference without changing the underlying event sequence", size=23)


RENDERERS: Dict[str, Renderer] = {
    "lang.3.literature": _render_literature,
    "lang.3.shakespeare": _render_shakespeare,
    "lang.3.world-lit": _render_world_lit,
    "lang.3.rhetoric": _render_rhetoric,
    "lang.3.essays": _render_essays,
    "lang.3.linguistics-intro": _render_linguistics_intro,
    "lang.3.media": _render_media,
    "lang.3.second-language": _render_second_language,
    "lang.4.linguistics": _render_linguistics,
    "lang.4.lit-theory": _render_lit_theory,
    "lang.4.creative": _render_creative,
    "lang.4.history-english": _render_history_english,
    "lang.4.classics": _render_classics,
    "lang.4.comp-lit": _render_comp_lit,
    "lang.5.philology": _render_philology,
    "lang.5.socioling": _render_socioling,
    "lang.5.psycholing": _render_psycholing,
    "lang.5.comp-ling": _render_comp_ling,
    "lang.5.narratology": _render_narratology,
}


__all__ = ["RENDERERS"]
