"""Bespoke field-guide renderers for the generated early biology cohort.

The shared natural-science layouts are intentionally compact and generic.  Early
biology benefits from a different emphasis: recognisable organisms and organs,
large causal marks, and a visual relationship that remains legible in the 800px
lesson asset.  This module keeps that richer drawing grammar local to biology so
changes here cannot silently restyle chemistry or Earth science.

Every renderer is deterministic.  It receives the existing ``SciencePlate`` and
lesson content, draws only inside the plate's content frame, and preserves the
lesson's authored footer verbatim.
"""

from __future__ import annotations

import math
from typing import Callable, Dict, Mapping, Sequence, Tuple

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
    GRID,
    INK,
    INK_SOFT,
    PAPER,
    PAPER_LIGHT,
    PLUM,
    PLUM_LIGHT,
    TEAL,
    TEAL_LIGHT,
    SciencePlate,
    _wrapped_center,
    hex_rgba,
    mix,
)


Point = Tuple[float, float]
Box = Tuple[float, float, float, float]
Renderer = Callable[[SciencePlate, Mapping[str, object]], None]


# The 800 px responsive asset is a one-half reduction of this canvas. Keep
# instructional labels large enough to survive that reduction; dense copy is
# shortened or reflowed instead of rendered as fine print.
LABEL_TEXT_MIN = 28
BODY_TEXT_MIN = 28
FOOTER_TEXT_SIZE = 29


def _tint(tone: str, amount: float = .78) -> str:
    return mix(tone, PAPER_LIGHT, amount)


def _panel(plate: SciencePlate, box: Box, tone: str, *, radius: int = 24) -> None:
    plate.draw.rounded_rectangle(
        box,
        radius=radius,
        fill=hex_rgba(_tint(tone, .88), 224),
        outline=hex_rgba(tone, 215),
        width=4,
    )


def _section_label(plate: SciencePlate, center: Point, value: str, tone: str,
                   *, size: int = 24) -> None:
    plate.label(center, value, size=max(size, LABEL_TEXT_MIN), fill=tone)


def _body_text(plate: SciencePlate, box: Box, value: str, *, size: int = 25,
               bold: bool = True, fill: str = INK_SOFT) -> None:
    _wrapped_center(plate, box, value, size=max(size, BODY_TEXT_MIN), bold=bold, fill=fill,
                    line_gap=7)


def _mechanism_arrow(plate: SciencePlate, start: Point, end: Point, label: str,
                     tone: str, *, label_offset: Point = (0, -25)) -> None:
    plate.arrow(start, end, fill=tone, width=8, head=22)
    if label:
        mx = (start[0] + end[0]) / 2 + label_offset[0]
        my = (start[1] + end[1]) / 2 + label_offset[1]
        _section_label(plate, (mx, my), label, tone, size=22)


def _leader(plate: SciencePlate, start: Point, end: Point, tone: str,
            *, width: int = 5) -> None:
    plate.draw.line((*start, *end), fill=tone, width=width)
    plate.dot(end, 7, fill=tone, outline=PAPER_LIGHT, width=2)


def _ground(plate: SciencePlate, y: float, x0: float, x1: float) -> None:
    plate.draw.rounded_rectangle((x0, y, x1, y + 54), radius=16,
                                 fill=hex_rgba(GOLD_LIGHT, 105))
    plate.draw.line((x0, y, x1, y), fill=EDGE, width=4)
    for x in range(int(x0) + 18, int(x1), 44):
        plate.draw.line((x, y + 13, x + 15, y + 25),
                        fill=hex_rgba(EDGE, 110), width=2)


def _transform(points: Sequence[Point], center: Point, angle: float = 0.0,
               scale: float = 1.0) -> list[Point]:
    ca, sa = math.cos(angle), math.sin(angle)
    cx, cy = center
    return [
        (cx + (x * ca - y * sa) * scale,
         cy + (x * sa + y * ca) * scale)
        for x, y in points
    ]


def _leaf(plate: SciencePlate, center: Point, *, length: float = 105,
          width: float = 48, angle: float = 0.0, tone: str = GREEN) -> None:
    points = []
    for i in range(13):
        t = i / 12
        points.append((-length / 2 + length * t,
                       -math.sin(math.pi * t) * width / 2))
    for i in range(12, -1, -1):
        t = i / 12
        points.append((-length / 2 + length * t,
                       math.sin(math.pi * t) * width / 2))
    transformed = _transform(points, center, angle)
    plate.draw.polygon(transformed, fill=_tint(tone, .62), outline=tone)
    vein = _transform(((-length * .42, 0), (length * .42, 0)), center, angle)
    plate.draw.line((*vein[0], *vein[1]), fill=tone, width=4)


def _roots(plate: SciencePlate, origin: Point, *, span: float = 125,
           depth: float = 115, tone: str = EDGE) -> None:
    x, y = origin
    for fraction in (-1, -.65, -.3, 0, .32, .68, 1):
        end_x = x + fraction * span
        elbow_x = x + fraction * span * .35
        plate.draw.line((x, y, elbow_x, y + depth * .42, end_x, y + depth),
                        fill=tone, width=5, joint="curve")
        if fraction:
            twig = -1 if fraction > 0 else 1
            plate.draw.line((elbow_x, y + depth * .42,
                             elbow_x + twig * 20, y + depth * .66),
                            fill=tone, width=3)


def _flower(plate: SciencePlate, center: Point, *, radius: float = 46,
            tone: str = CORAL) -> None:
    x, y = center
    for angle in range(0, 360, 60):
        a = math.radians(angle)
        px, py = x + math.cos(a) * radius * .68, y + math.sin(a) * radius * .68
        plate.draw.ellipse((px - radius * .38, py - radius * .28,
                            px + radius * .38, py + radius * .28),
                           fill=_tint(tone, .58), outline=tone, width=3)
    plate.draw.ellipse((x - radius * .32, y - radius * .32,
                        x + radius * .32, y + radius * .32),
                       fill=GOLD_LIGHT, outline=GOLD, width=4)


def _seed(plate: SciencePlate, center: Point, *, size: float = 64,
          split: bool = False) -> None:
    x, y = center
    plate.draw.ellipse((x - size * .62, y - size * .38,
                        x + size * .62, y + size * .38),
                       fill=GOLD_LIGHT, outline=GOLD, width=5)
    plate.draw.arc((x - size * .5, y - size * .33, x + size * .18, y + size * .34),
                   285, 75, fill=EDGE, width=4)
    if split:
        plate.draw.line((x + size * .06, y - size * .28,
                         x + size * .04, y + size * .25), fill=EDGE, width=3)


def _plant(plate: SciencePlate, base: Point, *, height: float = 245,
           flowering: bool = False, roots: bool = True, tone: str = GREEN,
           root_depth: float = 72) -> None:
    x, y = base
    top = y - height
    plate.draw.line((x, y, x, top + 20), fill=tone, width=10)
    _leaf(plate, (x - 49, top + height * .38), length=106, width=52,
          angle=-.43, tone=tone)
    _leaf(plate, (x + 52, top + height * .22), length=112, width=54,
          angle=math.pi + .42, tone=tone)
    if height > 195:
        _leaf(plate, (x - 42, top + height * .67), length=86, width=42,
              angle=-.3, tone=tone)
    if flowering:
        _flower(plate, (x, top), radius=47)
    else:
        _leaf(plate, (x, top + 12), length=92, width=46,
              angle=-math.pi / 2, tone=tone)
    if roots:
        _roots(plate, (x, y), span=80, depth=root_depth)


def _tree(plate: SciencePlate, base: Point, *, height: float = 235,
          canopy: str = "full") -> None:
    x, y = base
    top = y - height
    plate.draw.polygon(((x - 28, y), (x - 16, top + 63),
                        (x + 15, top + 63), (x + 31, y)),
                       fill=_tint(EDGE, .35), outline=EDGE)
    for dx, dy in ((-75, 42), (-42, 3), (0, -10), (43, 4), (78, 45)):
        plate.draw.line((x, top + 92, x + dx, top + dy), fill=EDGE, width=8)
    if canopy == "full":
        for dx, dy, radius in ((-79, 35, 60), (-35, 3, 69), (22, 1, 72),
                               (75, 34, 60), (0, 54, 75)):
            plate.draw.ellipse((x + dx - radius, top + dy - radius,
                                x + dx + radius, top + dy + radius),
                               fill=hex_rgba(GREEN_LIGHT, 225), outline=GREEN, width=3)
    elif canopy == "buds":
        for dx, dy in ((-75, 40), (-42, 0), (0, -12), (43, 3), (76, 43),
                       (-25, 55), (29, 52)):
            plate.draw.ellipse((x + dx - 11, top + dy - 8,
                                x + dx + 11, top + dy + 8),
                               fill=GREEN_LIGHT, outline=GREEN, width=3)
    elif canopy == "autumn":
        for dx, dy, tone in ((-70, 31, GOLD), (-30, 0, CORAL), (17, 2, GOLD),
                             (65, 35, CORAL), (0, 52, GOLD)):
            plate.draw.ellipse((x + dx - 52, top + dy - 43,
                                x + dx + 52, top + dy + 43),
                               fill=_tint(tone, .55), outline=tone, width=3)
        for dx, dy in ((-93, 170), (64, 185), (-25, 204)):
            _leaf(plate, (x + dx, top + dy), length=35, width=17,
                  angle=.7, tone=CORAL if dx > 0 else GOLD)
    _roots(plate, (x, y), span=70, depth=35, tone=EDGE)


def _fish(plate: SciencePlate, center: Point, *, scale: float = 1.0,
          tone: str = BLUE) -> None:
    x, y = center
    w, h = 210 * scale, 98 * scale
    plate.draw.ellipse((x - w * .52, y - h * .5, x + w * .43, y + h * .5),
                       fill=_tint(tone, .58), outline=tone, width=max(3, int(5 * scale)))
    plate.draw.polygon(((x + w * .37, y), (x + w * .72, y - h * .55),
                        (x + w * .72, y + h * .55)),
                       fill=_tint(tone, .45), outline=tone)
    plate.draw.polygon(((x - w * .04, y), (x + w * .12, y - h * .43),
                        (x + w * .24, y)), fill=BLUE_LIGHT, outline=tone)
    plate.draw.ellipse((x - w * .36, y - h * .16, x - w * .30, y - h * .03),
                       fill=INK)
    for offset in (-.21, -.16, -.11):
        plate.draw.arc((x + w * offset, y - h * .34,
                        x + w * (offset + .16), y + h * .34),
                       86, 274, fill=CORAL, width=max(2, int(3 * scale)))


def _bird(plate: SciencePlate, center: Point, *, scale: float = 1.0,
          tone: str = CORAL) -> None:
    x, y = center
    plate.draw.ellipse((x - 104 * scale, y - 50 * scale,
                        x + 76 * scale, y + 67 * scale),
                       fill=_tint(tone, .62), outline=tone, width=max(3, int(5 * scale)))
    plate.draw.ellipse((x + 42 * scale, y - 91 * scale,
                        x + 112 * scale, y - 22 * scale),
                       fill=_tint(tone, .55), outline=tone, width=max(3, int(5 * scale)))
    plate.draw.polygon(((x + 108 * scale, y - 64 * scale),
                        (x + 149 * scale, y - 51 * scale),
                        (x + 108 * scale, y - 40 * scale)),
                       fill=GOLD_LIGHT, outline=GOLD)
    wing = _transform(((-76, -8), (-12, -55), (46, 7), (-10, 43)),
                      (x, y), 0, scale)
    plate.draw.polygon(wing, fill=_tint(BLUE, .58), outline=BLUE)
    eye = (x + 84 * scale, y - 63 * scale)
    plate.draw.ellipse((eye[0] - 5 * scale, eye[1] - 5 * scale,
                        eye[0] + 5 * scale, eye[1] + 5 * scale), fill=INK)
    for dx in (-35, 12):
        plate.draw.line((x + dx * scale, y + 55 * scale,
                         x + (dx - 5) * scale, y + 94 * scale), fill=EDGE,
                        width=max(3, int(4 * scale)))
        plate.draw.line((x + (dx - 5) * scale, y + 94 * scale,
                         x + (dx + 17) * scale, y + 99 * scale), fill=EDGE,
                        width=max(2, int(3 * scale)))


def _rabbit(plate: SciencePlate, center: Point, *, scale: float = 1.0,
            tone: str = TEAL) -> None:
    x, y = center
    plate.draw.ellipse((x - 100 * scale, y - 52 * scale,
                        x + 70 * scale, y + 65 * scale),
                       fill=_tint(tone, .66), outline=tone, width=max(3, int(5 * scale)))
    plate.draw.ellipse((x + 43 * scale, y - 84 * scale,
                        x + 115 * scale, y - 12 * scale),
                       fill=_tint(tone, .58), outline=tone, width=max(3, int(5 * scale)))
    for dx in (56, 82):
        plate.draw.ellipse((x + dx * scale, y - 168 * scale,
                            x + (dx + 25) * scale, y - 73 * scale),
                           fill=_tint(tone, .55), outline=tone,
                           width=max(3, int(4 * scale)))
    plate.draw.ellipse((x - 128 * scale, y - 35 * scale,
                        x - 82 * scale, y + 11 * scale),
                       fill=PAPER_LIGHT, outline=tone, width=max(3, int(4 * scale)))
    plate.draw.ellipse((x + 90 * scale, y - 58 * scale,
                        x + 99 * scale, y - 49 * scale), fill=INK)
    plate.draw.ellipse((x - 74 * scale, y + 40 * scale,
                        x + 3 * scale, y + 78 * scale),
                       fill=_tint(tone, .55), outline=tone)


def _fox(plate: SciencePlate, center: Point, *, scale: float = 1.0) -> None:
    x, y = center
    plate.draw.ellipse((x - 108 * scale, y - 46 * scale,
                        x + 68 * scale, y + 60 * scale),
                       fill=_tint(CORAL, .48), outline=CORAL, width=max(3, int(5 * scale)))
    plate.draw.polygon(((x + 45 * scale, y - 33 * scale),
                        (x + 131 * scale, y - 4 * scale),
                        (x + 55 * scale, y + 35 * scale)),
                       fill=_tint(CORAL, .55), outline=CORAL)
    for dx in (57, 101):
        plate.draw.polygon(((x + dx * scale, y - 22 * scale),
                            (x + (dx + 9) * scale, y - 78 * scale),
                            (x + (dx + 33) * scale, y - 13 * scale)),
                           fill=_tint(CORAL, .53), outline=CORAL)
    tail = _transform(((-91, 15), (-177, -23), (-216, 16), (-159, 51)),
                      (x, y), 0, scale)
    plate.draw.polygon(tail, fill=_tint(CORAL, .58), outline=CORAL)
    plate.draw.polygon(_transform(((-216, 16), (-183, 2), (-170, 38), (-198, 46)),
                                  (x, y), 0, scale),
                       fill=PAPER_LIGHT, outline=CORAL)
    plate.draw.ellipse((x + 111 * scale, y - 5 * scale,
                        x + 120 * scale, y + 4 * scale), fill=INK)


def _camel(plate: SciencePlate, center: Point, *, scale: float = 1.0) -> None:
    x, y = center
    body = _transform(((-120, 34), (-107, -36), (-73, -74), (-26, -28),
                       (11, -81), (55, -31), (99, -18), (111, 39)),
                      (x, y), 0, scale)
    plate.draw.polygon(body, fill=_tint(GOLD, .54), outline=GOLD)
    plate.draw.polygon(_transform(((74, -20), (93, -106), (118, -132),
                                   (146, -111), (125, -78), (113, -2)),
                                  (x, y), 0, scale),
                       fill=_tint(GOLD, .58), outline=GOLD)
    for dx in (-84, -40, 56, 94):
        plate.draw.line((x + dx * scale, y + 29 * scale,
                         x + (dx - 4) * scale, y + 121 * scale),
                        fill=GOLD, width=max(4, int(7 * scale)))
        plate.draw.line((x + (dx - 16) * scale, y + 121 * scale,
                         x + (dx + 14) * scale, y + 121 * scale),
                        fill=EDGE, width=max(3, int(6 * scale)))
    plate.draw.ellipse((x + 126 * scale, y - 115 * scale,
                        x + 134 * scale, y - 107 * scale), fill=INK)


def _polar_bear(plate: SciencePlate, center: Point, *, scale: float = 1.0) -> None:
    x, y = center
    outline = BLUE
    plate.draw.ellipse((x - 118 * scale, y - 55 * scale,
                        x + 68 * scale, y + 64 * scale),
                       fill=mix(BLUE_LIGHT, PAPER_LIGHT, .77), outline=outline,
                       width=max(3, int(5 * scale)))
    plate.draw.ellipse((x + 38 * scale, y - 90 * scale,
                        x + 124 * scale, y - 12 * scale),
                       fill=mix(BLUE_LIGHT, PAPER_LIGHT, .77), outline=outline,
                       width=max(3, int(5 * scale)))
    plate.draw.ellipse((x + 52 * scale, y - 105 * scale,
                        x + 82 * scale, y - 72 * scale),
                       fill=BLUE_LIGHT, outline=outline, width=3)
    for dx in (-78, -24, 39, 72):
        plate.draw.rounded_rectangle((x + (dx - 12) * scale, y + 40 * scale,
                                      x + (dx + 16) * scale, y + 112 * scale),
                                     radius=max(4, int(8 * scale)),
                                     fill=mix(BLUE_LIGHT, PAPER_LIGHT, .72),
                                     outline=outline, width=max(2, int(4 * scale)))
        plate.draw.line((x + (dx - 22) * scale, y + 112 * scale,
                         x + (dx + 28) * scale, y + 112 * scale),
                        fill=outline, width=max(3, int(5 * scale)))
    plate.draw.ellipse((x + 104 * scale, y - 56 * scale,
                        x + 113 * scale, y - 47 * scale), fill=INK)


def _rock(plate: SciencePlate, center: Point, *, scale: float = 1.0) -> None:
    x, y = center
    points = _transform(((-94, 61), (-109, 3), (-59, -72), (14, -101),
                         (89, -42), (108, 55), (39, 91)), (x, y), 0, scale)
    plate.draw.polygon(points, fill=mix(BLUE_LIGHT, PAPER, .34), outline=BLUE)
    plate.draw.line((*_transform(((-58, -48), (-8, -3), (53, 38)),
                                 (x, y), 0, scale)[0],
                     *_transform(((-58, -48), (-8, -3), (53, 38)),
                                 (x, y), 0, scale)[1],
                     *_transform(((-58, -48), (-8, -3), (53, 38)),
                                 (x, y), 0, scale)[2]),
                    fill=BLUE, width=max(3, int(5 * scale)), joint="curve")


def _cell(plate: SciencePlate, center: Point, *, radius: float = 82,
          tone: str = TEAL, nucleus: bool = True, wall: bool = False) -> None:
    x, y = center
    if wall:
        plate.draw.rounded_rectangle((x - radius * 1.08, y - radius * .78,
                                      x + radius * 1.08, y + radius * .78),
                                     radius=int(radius * .18),
                                     fill=hex_rgba(GREEN_LIGHT, 150),
                                     outline=GREEN, width=5)
        membrane = (x - radius * .94, y - radius * .65,
                    x + radius * .94, y + radius * .65)
        plate.draw.rounded_rectangle(membrane, radius=int(radius * .2),
                                     fill=_tint(tone, .72), outline=tone, width=4)
    else:
        plate.draw.ellipse((x - radius, y - radius * .78,
                            x + radius, y + radius * .78),
                           fill=_tint(tone, .69), outline=tone, width=5)
    if nucleus:
        plate.draw.ellipse((x - radius * .28, y - radius * .26,
                            x + radius * .28, y + radius * .26),
                           fill=PLUM_LIGHT, outline=PLUM, width=4)
    for angle in (.2, 1.75, 3.6, 5.1):
        px = x + math.cos(angle) * radius * .55
        py = y + math.sin(angle) * radius * .38
        plate.draw.ellipse((px - 8, py - 5, px + 8, py + 5),
                           fill=GOLD_LIGHT, outline=GOLD, width=2)


def _bacterium(plate: SciencePlate, center: Point, *, scale: float = 1.0) -> None:
    x, y = center
    plate.draw.rounded_rectangle((x - 112 * scale, y - 49 * scale,
                                  x + 86 * scale, y + 49 * scale),
                                 radius=int(48 * scale), fill=TEAL_LIGHT,
                                 outline=TEAL, width=max(3, int(5 * scale)))
    for dx, dy in ((-67, -15), (-28, 18), (12, -18), (51, 15)):
        plate.draw.ellipse((x + (dx - 7) * scale, y + (dy - 7) * scale,
                            x + (dx + 7) * scale, y + (dy + 7) * scale),
                           fill=TEAL)
    plate.draw.arc((x + 59 * scale, y - 3 * scale,
                    x + 180 * scale, y + 101 * scale), 265, 75,
                   fill=TEAL, width=max(3, int(5 * scale)))


def _virus(plate: SciencePlate, center: Point, *, radius: float = 53) -> None:
    x, y = center
    plate.draw.ellipse((x - radius, y - radius, x + radius, y + radius),
                       fill=CORAL_LIGHT, outline=CORAL, width=5)
    for angle in range(0, 360, 30):
        a = math.radians(angle)
        p0 = (x + math.cos(a) * radius, y + math.sin(a) * radius)
        p1 = (x + math.cos(a) * radius * 1.42, y + math.sin(a) * radius * 1.42)
        plate.draw.line((*p0, *p1), fill=CORAL, width=4)
        plate.draw.ellipse((p1[0] - 7, p1[1] - 7, p1[0] + 7, p1[1] + 7),
                           fill=CORAL)
    plate.draw.arc((x - radius * .48, y - radius * .34,
                    x + radius * .51, y + radius * .40), 5, 180,
                   fill=PLUM, width=4)
    plate.draw.arc((x - radius * .48, y - radius * .10,
                    x + radius * .51, y + radius * .64), 185, 355,
                   fill=PLUM, width=4)


def _lungs(plate: SciencePlate, center: Point, *, scale: float = 1.0) -> None:
    x, y = center
    plate.draw.line((x, y - 112 * scale, x, y - 34 * scale),
                    fill=BLUE, width=max(5, int(9 * scale)))
    plate.draw.line((x, y - 36 * scale, x - 35 * scale, y - 3 * scale),
                    fill=BLUE, width=max(4, int(7 * scale)))
    plate.draw.line((x, y - 36 * scale, x + 35 * scale, y - 3 * scale),
                    fill=BLUE, width=max(4, int(7 * scale)))
    plate.draw.ellipse((x - 100 * scale, y - 36 * scale,
                        x - 9 * scale, y + 111 * scale),
                       fill=mix(CORAL_LIGHT, PAPER_LIGHT, .53), outline=CORAL,
                       width=max(3, int(5 * scale)))
    plate.draw.ellipse((x + 9 * scale, y - 36 * scale,
                        x + 100 * scale, y + 111 * scale),
                       fill=mix(CORAL_LIGHT, PAPER_LIGHT, .53), outline=CORAL,
                       width=max(3, int(5 * scale)))
    for side in (-1, 1):
        for branch in (18, 43, 68):
            plate.draw.line((x + side * 34 * scale, y + branch * scale,
                             x + side * 72 * scale, y + (branch + 18) * scale),
                            fill=BLUE, width=max(2, int(3 * scale)))


def _heart(plate: SciencePlate, center: Point, *, scale: float = 1.0) -> None:
    x, y = center
    r = 58 * scale
    plate.draw.ellipse((x - r, y - r * .7, x + 4, y + r * .25),
                       fill=CORAL_LIGHT, outline=CORAL, width=max(3, int(5 * scale)))
    plate.draw.ellipse((x - 4, y - r * .7, x + r, y + r * .25),
                       fill=CORAL_LIGHT, outline=CORAL, width=max(3, int(5 * scale)))
    plate.draw.polygon(((x - r, y - r * .08), (x + r, y - r * .08),
                        (x, y + r * 1.18)), fill=CORAL_LIGHT, outline=CORAL)
    plate.draw.line((x - 15 * scale, y - 45 * scale,
                     x - 15 * scale, y + 51 * scale), fill=BLUE, width=max(3, int(4 * scale)))
    plate.draw.line((x + 15 * scale, y - 45 * scale,
                     x + 15 * scale, y + 51 * scale), fill=CORAL, width=max(3, int(4 * scale)))


def _kidneys(plate: SciencePlate, center: Point, *, scale: float = 1.0) -> None:
    x, y = center
    for side in (-1, 1):
        cx = x + side * 37 * scale
        plate.draw.ellipse((cx - 28 * scale, y - 47 * scale,
                            cx + 28 * scale, y + 47 * scale),
                           fill=_tint(PLUM, .62), outline=PLUM,
                           width=max(3, int(4 * scale)))
        plate.draw.ellipse((cx - side * 4 * scale - 15 * scale, y - 12 * scale,
                            cx - side * 4 * scale + 15 * scale, y + 12 * scale),
                           fill=PAPER_LIGHT)
        plate.draw.line((cx, y + 43 * scale, x + side * 15 * scale,
                         y + 91 * scale), fill=GOLD, width=max(2, int(4 * scale)))


def _brain(plate: SciencePlate, center: Point, *, scale: float = 1.0) -> None:
    x, y = center
    r = 67 * scale
    lobes = ((-.48, -.16), (-.18, -.48), (.20, -.48), (.51, -.14),
             (.41, .27), (.05, .46), (-.36, .35), (-.56, .08))
    for dx, dy in lobes:
        cx, cy = x + dx * r, y + dy * r
        plate.draw.ellipse((cx - r * .42, cy - r * .38,
                            cx + r * .42, cy + r * .38),
                           fill=PLUM_LIGHT, outline=PLUM,
                           width=max(2, int(3 * scale)))
    plate.draw.line((x, y - r * .62, x, y + r * .66), fill=PLUM, width=max(2, int(3 * scale)))


def _finish(plate: SciencePlate, content: Mapping[str, object]) -> None:
    # A taller local footer preserves the shared plate voice without reducing
    # lesson conclusions below the responsive-image legibility floor.
    plate.draw.rounded_rectangle(
        (165, 800, 1435, 900),
        radius=24,
        fill=hex_rgba(plate.domain_accent, 34),
        outline=hex_rgba(plate.domain_accent, 125),
        width=3,
    )
    _wrapped_center(
        plate,
        (195, 804, 1405, 896),
        str(content["footer"]),
        size=FOOTER_TEXT_SIZE,
        bold=True,
        fill=INK,
        line_gap=2,
    )


def draw_living(plate: SciencePlate, content: Mapping[str, object]) -> None:
    boxes = ((115, 225, 555, 785), (580, 225, 1020, 785), (1045, 225, 1485, 785))
    tones = (GREEN, CORAL, BLUE)
    for box, tone in zip(boxes, tones):
        _panel(plate, box, tone)
    _section_label(plate, (335, 267), "PLANT", GREEN)
    _ground(plate, 590, 170, 500)
    _plant(plate, (335, 590), height=240, flowering=True)
    _body_text(plate, (150, 675, 520, 765),
               "CELLS · ENERGY · RESPONSE\nGROWTH · REPRODUCTION")

    _section_label(plate, (800, 267), "ANIMAL", CORAL)
    _rabbit(plate, (800, 505), scale=.9, tone=CORAL)
    _body_text(plate, (615, 675, 985, 765),
               "CELLS · METABOLISM · SENSES\nGROWTH · REPRODUCTION")

    _section_label(plate, (1265, 267), "ROCK", BLUE)
    _rock(plate, (1265, 500), scale=1.05)
    _body_text(plate, (1080, 675, 1450, 765),
               "NO CELLS OR METABOLISM\nMOVEMENT ≠ LIFE")
    _finish(plate, content)


def draw_animals(plate: SciencePlate, content: Mapping[str, object]) -> None:
    boxes = ((110, 225, 555, 785), (578, 225, 1022, 785), (1045, 225, 1490, 785))
    for box, tone in zip(boxes, (BLUE, CORAL, GOLD)):
        _panel(plate, box, tone)

    _section_label(plate, (333, 267), "FISH / POND", BLUE)
    plate.draw.rounded_rectangle((135, 315, 530, 585), radius=26,
                                 fill=hex_rgba(BLUE_LIGHT, 92))
    for y in (360, 425, 500):
        plate.draw.arc((150, y, 515, y + 70), 190, 350, fill=BLUE, width=3)
    _fish(plate, (326, 445), scale=1.03)
    _leader(plate, (256, 424), (193, 342), CORAL)
    _section_label(plate, (203, 319), "GILLS", CORAL, size=22)
    _body_text(plate, (150, 620, 515, 757), "Gills exchange gases; fins push and steer through water.", size=24)

    _section_label(plate, (800, 267), "BIRD / WOODS", CORAL)
    _bird(plate, (782, 460), scale=.95)
    _leader(plate, (746, 455), (640, 350), BLUE)
    _section_label(plate, (646, 324), "WING", BLUE, size=22)
    _leader(plate, (888, 406), (934, 334), GOLD)
    _section_label(plate, (941, 308), "BEAK", GOLD, size=22)
    _body_text(plate, (615, 620, 985, 757), "Wings shape airflow; feet and beak fit perching and feeding.", size=24)

    _section_label(plate, (1267, 267), "CAMEL / DESERT", GOLD)
    _ground(plate, 580, 1080, 1450)
    _camel(plate, (1240, 495), scale=.82)
    _leader(plate, (1260, 405), (1395, 340), CORAL)
    _section_label(plate, (1390, 314), "HUMPS", CORAL, size=22)
    _leader(plate, (1160, 594), (1115, 625), BLUE)
    _section_label(plate, (1135, 650), "LONG LEGS", BLUE)
    _body_text(plate, (1090, 690, 1450, 765),
               "Water-saving kidneys reduce water loss.")
    _finish(plate, content)


def draw_plants(plate: SciencePlate, content: Mapping[str, object]) -> None:
    centers = (235, 610, 990, 1365)
    tones = (GOLD, BLUE, GREEN, CORAL)
    labels = ("1  SEED", "2  ROOT FIRST", "3  LEAVES OPEN", "4  FLOWER + SEEDS")
    for x, tone, label in zip(centers, tones, labels):
        _panel(plate, (x - 155, 245, x + 155, 755), tone)
        _section_label(plate, (x, 284), label, tone, size=22)
        _ground(plate, 580, x - 125, x + 125)

    _seed(plate, (235, 495), size=90, split=True)
    _body_text(plate, (105, 655, 365, 735), "Stored food fuels germination")

    _seed(plate, (610, 500), size=69, split=True)
    plate.draw.line((624, 514, 624, 588), fill=GREEN, width=8)
    _roots(plate, (624, 570), span=70, depth=73)
    _leaf(plate, (642, 435), length=75, width=35, angle=-1.05)
    _body_text(plate, (480, 655, 740, 735), "Water starts growth; root first")

    _plant(plate, (990, 580), height=210, flowering=False, root_depth=50)
    _body_text(plate, (860, 655, 1120, 735), "Leaves begin sugar making")

    _plant(plate, (1365, 580), height=240, flowering=True, root_depth=50)
    for dx in (-72, 70):
        _seed(plate, (1365 + dx, 535), size=30)
    _body_text(plate, (1235, 655, 1495, 735), "Fertilisation produces seeds")

    for left, right, label in zip(centers[:-1], centers[1:],
                                  ("WATER", "LIGHT", "POLLINATION")):
        _mechanism_arrow(plate, (left + 164, 500), (right - 164, 500), label,
                         GREEN, label_offset=(0, -31))
    _mechanism_arrow(plate, (1360, 230), (250, 230), "DISPERSAL RESTARTS THE CYCLE",
                     GOLD, label_offset=(0, -28))
    _finish(plate, content)


def draw_body(plate: SciencePlate, content: Mapping[str, object]) -> None:
    _panel(plate, (110, 225, 820, 785), PLUM)
    _panel(plate, (850, 225, 1490, 785), GREEN)
    _section_label(plate, (465, 268), "FIVE INPUT CHANNELS", PLUM)
    _section_label(plate, (1170, 268), "ONE INTEGRATING SYSTEM", GREEN)

    # A recognisable head carries the organs; stimuli arrive from outside.
    plate.draw.ellipse((320, 320, 655, 710), fill=hex_rgba(CORAL_LIGHT, 115),
                       outline=CORAL, width=6)
    plate.draw.polygon(((655, 420), (715, 475), (655, 500)),
                       fill=hex_rgba(CORAL_LIGHT, 115), outline=CORAL)
    for x in (400, 565):
        plate.draw.ellipse((x - 31, 430, x + 31, 468),
                           fill=PAPER_LIGHT, outline=BLUE, width=5)
        plate.draw.ellipse((x - 8, 440, x + 8, 458), fill=BLUE)
    plate.draw.arc((626, 475, 688, 560), 70, 280, fill=CORAL, width=6)
    plate.draw.arc((432, 570, 558, 642), 10, 170, fill=CORAL, width=5)
    plate.draw.ellipse((286, 470, 353, 568), fill=CORAL_LIGHT,
                       outline=CORAL, width=5)
    plate.draw.arc((300, 493, 342, 549), 260, 100, fill=CORAL, width=4)
    _brain(plate, (487, 380), scale=.85)

    stimuli = [
        ((171, 366), "LIGHT", BLUE, (370, 442)),
        ((169, 493), "SOUND", CORAL, (317, 516)),
        ((174, 621), "CHEMICALS", TEAL, (669, 490)),
        ((704, 610), "TASTE", GOLD, (548, 603)),
        ((585, 735), "TOUCH", GREEN, (612, 682)),
    ]
    for origin, label, tone, target in stimuli:
        _section_label(plate, origin, label, tone, size=21)
        plate.arrow((origin[0] + (62 if origin[0] < 450 else -62), origin[1]),
                    target, fill=tone, width=6, head=18)

    # Enlarged brain/spinal destination and five converging coloured signals.
    _brain(plate, (1250, 448), scale=1.65)
    plate.draw.line((1250, 545, 1250, 605), fill=PLUM, width=13)
    for i, (label, tone) in enumerate((("SIGHT", BLUE), ("HEARING", CORAL),
                                       ("SMELL", TEAL), ("TASTE", GOLD),
                                       ("TOUCH", GREEN))):
        y = 337 + i * 65
        _section_label(plate, (927, y), label, tone, size=20)
        plate.arrow((1030, y), (1145, 405 + i * 24), fill=tone, width=6, head=17)
    _body_text(plate, (885, 635, 1455, 765),
               "Sense organs send nerve signals. Brain and spinal cord combine them to guide action.")
    _finish(plate, content)


def draw_seasons(plate: SciencePlate, content: Mapping[str, object]) -> None:
    centers = (245, 615, 985, 1355)
    labels = ("SPRING", "SUMMER", "AUTUMN", "WINTER")
    tones = (TEAL, GREEN, CORAL, BLUE)
    canopies = ("buds", "full", "autumn", "bare")
    for x, label, tone, canopy in zip(centers, labels, tones, canopies):
        _panel(plate, (x - 157, 245, x + 157, 780), tone)
        _section_label(plate, (x, 284), label, tone)
        _ground(plate, 620, x - 126, x + 126)
        _tree(plate, (x, 620), height=240, canopy=canopy)
    _body_text(plate, (112, 682, 378, 764), "Buds open; young are born")
    _body_text(plate, (482, 682, 748, 764), "Long days support growth")
    _body_text(plate, (852, 682, 1118, 764), "Leaves fall; some migrate")
    _body_text(plate, (1222, 682, 1488, 764), "Dormancy saves energy")
    for left, right in zip(centers[:-1], centers[1:]):
        _mechanism_arrow(plate, (left + 166, 435), (right - 166, 435), "TIME",
                         GREEN, label_offset=(0, -25))
    plate.draw.arc((180, 205, 1425, 770), 205, 332, fill=GOLD, width=7)
    _section_label(plate, (800, 224), "ONE TEMPERATE-YEAR EXAMPLE", GOLD, size=22)
    _finish(plate, content)


def draw_habitats(plate: SciencePlate, content: Mapping[str, object]) -> None:
    boxes = ((105, 225, 565, 785), (570, 225, 1030, 785), (1035, 225, 1495, 785))
    for box, tone in zip(boxes, (GOLD, BLUE, TEAL)):
        _panel(plate, box, tone)

    _section_label(plate, (335, 268), "DESERT / SCARCE WATER", GOLD, size=22)
    _ground(plate, 600, 145, 525)
    plate.draw.line((335, 600, 335, 370), fill=GREEN, width=24)
    plate.draw.line((335, 465, 275, 430, 275, 385), fill=GREEN, width=18, joint="curve")
    plate.draw.line((335, 510, 397, 470, 397, 414), fill=GREEN, width=18, joint="curve")
    for x, y in ((275, 380), (335, 360), (397, 407)):
        plate.draw.ellipse((x - 10, y - 13, x + 10, y + 13), fill=GREEN)
    _leader(plate, (347, 470), (468, 377), BLUE)
    _section_label(plate, (461, 351), "STORED WATER", BLUE, size=19)
    _body_text(plate, (145, 640, 525, 765), "Stem stores water; spines deter hungry animals.", size=23)

    _section_label(plate, (800, 268), "OCEAN / WATER + SALT", BLUE, size=22)
    plate.draw.rounded_rectangle((600, 323, 1000, 598), radius=26,
                                 fill=hex_rgba(BLUE_LIGHT, 100))
    for y in (360, 442, 520):
        plate.draw.arc((620, y, 980, y + 62), 190, 350, fill=BLUE, width=3)
    _fish(plate, (787, 458), scale=1.18)
    _leader(plate, (705, 440), (650, 348), CORAL)
    _section_label(plate, (667, 323), "GILLS", CORAL, size=20)
    _body_text(plate, (610, 640, 990, 754), "Streamlined form cuts drag; gills exchange gases with water.", size=23)

    _section_label(plate, (1265, 268), "POLAR / COLD", TEAL, size=22)
    plate.draw.rounded_rectangle((1065, 560, 1465, 623), radius=18,
                                 fill=hex_rgba(BLUE_LIGHT, 125), outline=BLUE, width=3)
    _polar_bear(plate, (1252, 472), scale=.92)
    _leader(plate, (1180, 430), (1108, 345), CORAL)
    _section_label(plate, (1124, 320), "INSULATION", CORAL, size=19)
    _leader(plate, (1320, 574), (1421, 650), GOLD)
    _section_label(plate, (1405, 675), "BROAD FEET", GOLD, size=19)
    _body_text(plate, (1080, 696, 1450, 775),
               "Fur traps heat; broad feet spread weight.")
    _finish(plate, content)


def draw_food_chains(plate: SciencePlate, content: Mapping[str, object]) -> None:
    plate.draw.rounded_rectangle((110, 235, 1490, 770), radius=28,
                                 fill=hex_rgba(GREEN_LIGHT, 50), outline=GREEN, width=3)
    _ground(plate, 624, 120, 1480)
    # Large field specimens make the chain readable before its labels.
    plate.draw.ellipse((145, 305, 245, 405), fill=GOLD_LIGHT, outline=GOLD, width=6)
    for angle in range(0, 360, 45):
        a = math.radians(angle)
        plate.draw.line((195 + math.cos(a) * 62, 355 + math.sin(a) * 62,
                         195 + math.cos(a) * 91, 355 + math.sin(a) * 91),
                        fill=GOLD, width=6)
    # Grass has narrow blades, not the broad leaves of the generic plant glyph.
    for dx, tip_y in ((-85, 455), (-45, 395), (-10, 365), (35, 410), (80, 450)):
        plate.draw.polygon(((500, 624), (510 + dx, tip_y), (527, 624)),
                           fill=GREEN_LIGHT, outline=GREEN)
    _roots(plate, (510, 624), span=70, depth=60)
    _rabbit(plate, (840, 531), scale=.72)
    _fox(plate, (1240, 525), scale=.72)
    for x, y in ((470, 698), (530, 709), (585, 689)):
        plate.draw.line((x, y, x, y - 70), fill=EDGE, width=8)
        plate.draw.arc((x - 42, y - 105, x + 42, y - 30), 180, 360,
                       fill=PLUM, width=8)
        plate.draw.line((x - 36, y - 67, x + 36, y - 67), fill=PLUM, width=5)

    _section_label(plate, (195, 473), "SUNLIGHT", GOLD)
    _section_label(plate, (480, 325), "GRASS / PRODUCER", GREEN, size=22)
    _section_label(plate, (880, 327), "RABBIT / CONSUMER", TEAL, size=22)
    _section_label(plate, (1240, 327), "FOX / PREDATOR", CORAL, size=22)
    _section_label(plate, (530, 750), "DECOMPOSERS RETURN MATTER", PLUM, size=21)

    _mechanism_arrow(plate, (285, 410), (397, 459), "ENERGY", GOLD)
    _mechanism_arrow(plate, (633, 493), (721, 493), "FOOD", GREEN)
    _mechanism_arrow(plate, (972, 493), (1097, 493), "FOOD", CORAL)
    for start in ((520, 618), (825, 594), (1215, 587)):
        plate.arrow(start, (615, 675), fill=PLUM, width=5, head=17)
    plate.arrow((1335, 421), (1435, 305), fill=GOLD, width=6, head=18)
    _section_label(plate, (1400, 283), "HEAT LEAVES", GOLD, size=20)
    _finish(plate, content)


def draw_plant_parts(plate: SciencePlate, content: Mapping[str, object]) -> None:
    _panel(plate, (510, 225, 1090, 785), GREEN)
    _ground(plate, 625, 590, 1010)
    # Whole-plant cutaway: blue xylem goes up, teal phloem leaves the source.
    plate.draw.line((790, 625, 790, 350), fill=BLUE, width=15)
    plate.draw.line((815, 350, 815, 625), fill=GREEN, width=15)
    _roots(plate, (802, 625), span=180, depth=123)
    _leaf(plate, (696, 425), length=205, width=92, angle=-.38)
    _leaf(plate, (918, 457), length=205, width=92, angle=math.pi + .38)
    _flower(plate, (802, 317), radius=66)
    for dx in (-78, 83):
        _seed(plate, (802 + dx, 565), size=31)

    labels = [
        ((135, 300, 465, 445), "LEAF", "light + CO₂ → sugar", GREEN, (665, 412)),
        ((135, 480, 465, 625), "ROOT", "takes up water + ions", GOLD, (720, 670)),
        ((1100, 290, 1490, 445), "FLOWER",
         "pollen enables fertilisation; ovules become seeds", CORAL, (855, 318)),
        ((1135, 480, 1465, 625), "GROWING SINK", "imports sugar for growth", PLUM, (885, 565)),
    ]
    for box, heading, detail, tone, target in labels:
        _panel(plate, box, tone, radius=18)
        _section_label(plate, ((box[0] + box[2]) / 2, box[1] + 35), heading, tone)
        _body_text(plate, (box[0] + 16, box[1] + 66, box[2] - 16, box[3] - 12), detail)
        start_x = box[2] if box[2] < 800 else box[0]
        _leader(plate, (start_x, (box[1] + box[3]) / 2), target, tone)

    plate.arrow((777, 596), (777, 365), fill=BLUE, width=8, head=22)
    _section_label(plate, (665, 535), "XYLEM ↑", BLUE)
    # A leaf can supply sinks above or below it. Split the phloem route so the
    # flower and lower growing/storage tissues are both visible sinks.
    plate.arrow((830, 470), (830, 350), fill=GREEN, width=8, head=22)
    plate.arrow((830, 470), (830, 598), fill=GREEN, width=8, head=22)
    plate.arrow((840, 480), (885, 550), fill=GREEN, width=7, head=19)
    _section_label(plate, (955, 535), "PHLOEM ↕", GREEN)
    _finish(plate, content)


def draw_human_body(plate: SciencePlate, content: Mapping[str, object]) -> None:
    _panel(plate, (245, 225, 1100, 785), CORAL)
    _panel(plate, (1130, 225, 1485, 785), BLUE)
    _section_label(plate, (672, 270), "COOPERATING ORGAN SYSTEMS", CORAL)
    # Torso silhouette instead of a person glyph.
    plate.draw.polygon(((525, 350), (615, 315), (730, 315), (820, 350),
                        (870, 520), (830, 735), (515, 735), (475, 520)),
                       fill=hex_rgba(CORAL_LIGHT, 75), outline=EDGE)
    _lungs(plate, (672, 456), scale=.82)
    _heart(plate, (672, 544), scale=.76)
    # A femur and muscle bundle demonstrate the mechanical output.
    plate.draw.rounded_rectangle((763, 574, 797, 710), radius=15,
                                 fill=GOLD_LIGHT, outline=GOLD, width=4)
    plate.draw.ellipse((750, 553, 810, 606), fill=GOLD_LIGHT, outline=GOLD, width=4)
    plate.draw.ellipse((750, 686, 810, 739), fill=GOLD_LIGHT, outline=GOLD, width=4)
    plate.draw.polygon(((817, 574), (852, 592), (845, 704), (813, 718),
                        (800, 683), (806, 606)),
                       fill=PLUM_LIGHT, outline=PLUM)

    _section_label(plate, (395, 400), "LUNGS", BLUE, size=22)
    _leader(plate, (450, 400), (590, 430), BLUE)
    _section_label(plate, (412, 555), "HEART", CORAL, size=22)
    _leader(plate, (462, 555), (624, 544), CORAL)
    _section_label(plate, (925, 625), "BONE + MUSCLE", PLUM, size=21)
    _leader(plate, (873, 625), (820, 635), PLUM)

    plate.arrow((598, 480), (628, 527), fill=BLUE, width=7, head=18)
    _section_label(plate, (536, 505), "O2", BLUE, size=20)
    plate.arrow((715, 570), (793, 615), fill=CORAL, width=7, head=18)
    _section_label(plate, (749, 570), "BLOOD", CORAL, size=20)
    plate.arrow((782, 676), (704, 594), fill=TEAL, width=6, head=17)
    _section_label(plate, (707, 685), "CO2", TEAL, size=20)
    plate.arrow((642, 521), (612, 473), fill=TEAL, width=6, head=17)

    _section_label(plate, (1307, 270), "ROUTE", BLUE)
    route = ((1185, 340, "AIR"), (1307, 425, "LUNGS"),
             (1185, 510, "HEART"), (1307, 595, "MUSCLE"))
    for i, (x, y, label) in enumerate(route):
        plate.draw.ellipse((x - 54, y - 42, x + 54, y + 42),
                           fill=PAPER_LIGHT, outline=(BLUE, TEAL, CORAL, PLUM)[i], width=4)
        plate.text((x, y), label, size=20, bold=True, anchor="mm")
        if i:
            px, py, _ = route[i - 1]
            dx, dy = x - px, y - py
            trim = 1 / math.sqrt((dx / 54) ** 2 + (dy / 42) ** 2)
            plate.arrow((px + dx * trim, py + dy * trim),
                        (x - dx * trim, y - dy * trim),
                        fill=(BLUE, TEAL, CORAL, PLUM)[i], width=6, head=17)
    _body_text(plate, (1160, 651, 1455, 770),
               "Lungs exchange gases. Blood carries oxygen.")
    _finish(plate, content)


def draw_health(plate: SciencePlate, content: Mapping[str, object]) -> None:
    boxes = ((115, 235, 760, 500), (840, 235, 1485, 500),
             (115, 525, 760, 790), (840, 525, 1485, 790))
    entries = (
        ("VARIED FOOD + WATER", "supplies energy, building materials, and micronutrients", GREEN),
        ("SLEEP", "supports attention, memory, and recovery", BLUE),
        ("ACTIVE PLAY", "loads heart, lungs, muscle, and bone to build fitness", CORAL),
        ("HAND + TOOTH HYGIENE", "removes microbes, plaque, and food residue", GOLD),
    )
    for box, (heading, detail, tone) in zip(boxes, entries):
        _panel(plate, box, tone)
        _section_label(plate, ((box[0] + box[2]) / 2, box[1] + 36), heading, tone, size=22)
        text_left = box[0] + (355 if box[0] < 800 else 365)
        _body_text(plate, (text_left, box[1] + 80, box[2] - 24, box[3] - 18), detail)

    # Food bowl, glass, and produce.
    plate.draw.pieslice((175, 330, 350, 475), 0, 180, fill=GREEN_LIGHT, outline=GREEN, width=5)
    plate.draw.ellipse((190, 345, 230, 385), fill=CORAL_LIGHT, outline=CORAL, width=3)
    plate.draw.ellipse((246, 332, 292, 378), fill=GOLD_LIGHT, outline=GOLD, width=3)
    _leaf(plate, (306, 365), length=62, width=29, angle=-.6)
    plate.draw.rectangle((366, 331, 430, 458), fill=hex_rgba(BLUE_LIGHT, 120), outline=BLUE, width=5)
    plate.draw.line((370, 382, 426, 382), fill=BLUE, width=3)

    # Bed and moon.
    plate.draw.rounded_rectangle((905, 350, 1055, 439), radius=14,
                                 fill=BLUE_LIGHT, outline=BLUE, width=5)
    plate.draw.rectangle((885, 420, 1080, 455), fill=_tint(PLUM, .55), outline=PLUM, width=4)
    plate.draw.line((898, 455, 898, 478), fill=EDGE, width=6)
    plate.draw.line((1065, 455, 1065, 478), fill=EDGE, width=6)
    plate.draw.pieslice((1085, 325, 1170, 410), 65, 285, fill=GOLD_LIGHT, outline=GOLD, width=4)
    plate.draw.ellipse((1110, 318, 1175, 390), fill=PAPER_LIGHT)

    # Shoe + cardiopulmonary response, no stick person.
    plate.draw.polygon(((175, 657), (285, 657), (350, 704), (330, 742),
                        (196, 738), (157, 710)), fill=_tint(BLUE, .55), outline=BLUE)
    _heart(plate, (403, 643), scale=.48)
    _lungs(plate, (411, 718), scale=.40)

    # Toothbrush, tooth, soap bubbles.
    plate.draw.rounded_rectangle((907, 675, 1110, 701), radius=10,
                                 fill=TEAL_LIGHT, outline=TEAL, width=4)
    for x in range(1082, 1125, 10):
        plate.draw.line((x, 659, x, 676), fill=TEAL, width=4)
    plate.draw.pieslice((934, 585, 1038, 681), 180, 360,
                        fill=PAPER_LIGHT, outline=GOLD, width=5)
    for x, y, r in ((1115, 615, 18), (1160, 650, 25), (1108, 687, 13)):
        plate.draw.ellipse((x-r, y-r, x+r, y+r), fill=hex_rgba(BLUE_LIGHT, 65),
                           outline=BLUE, width=3)
    _finish(plate, content)


def _prokaryote(plate: SciencePlate, center: Point, *, scale: float,
                tone: str, surface: str) -> None:
    x, y = center
    plate.draw.rounded_rectangle((x - 90 * scale, y - 47 * scale,
                                  x + 90 * scale, y + 47 * scale),
                                 radius=int(45 * scale), fill=_tint(tone, .58),
                                 outline=tone, width=max(3, int(5 * scale)))
    plate.draw.arc((x - 46 * scale, y - 27 * scale,
                    x + 50 * scale, y + 28 * scale), 10, 350,
                   fill=PLUM, width=max(3, int(5 * scale)))
    for i in range(-3, 4):
        px = x + i * 24 * scale
        direction = -1 if i % 2 else 1
        plate.draw.line((px, y + direction * 44 * scale,
                         px + 9 * scale, y + direction * 70 * scale),
                        fill=tone, width=max(2, int(3 * scale)))
    plate.text((x, y + 94 * scale), surface, size=22, bold=True,
               fill=tone, anchor="mm")


def draw_classification(plate: SciencePlate, content: Mapping[str, object]) -> None:
    _panel(plate, (105, 225, 1495, 785), TEAL)
    _section_label(plate, (800, 265), "BRANCHING ANCESTRY, NOT A LADDER", TEAL)
    # Tree geometry; the archaeal host continues into eukaryotes.
    plate.dot((190, 505), 24, fill=PLUM, outline=INK, width=4)
    plate.text((190, 560), "LUCA", size=25, bold=True, fill=PLUM, anchor="mm")
    plate.draw.line((215, 505, 350, 505), fill=INK, width=8)
    plate.draw.line((350, 505, 350, 370, 515, 370), fill=TEAL, width=8)
    plate.draw.line((350, 505, 350, 650, 515, 650), fill=GOLD, width=8)
    plate.draw.line((685, 650, 850, 650), fill=GOLD, width=8)
    plate.draw.line((850, 650, 850, 560, 1040, 560), fill=GREEN, width=8)
    plate.draw.line((850, 650, 850, 695, 1280, 695), fill=BLUE, width=8)

    _prokaryote(plate, (605, 370), scale=.88, tone=TEAL, surface="BACTERIA")
    _prokaryote(plate, (605, 650), scale=.88, tone=GOLD, surface="ARCHAEAL HOST")
    _prokaryote(plate, (1370, 695), scale=.72, tone=BLUE, surface="OTHER ARCHAEA")
    _cell(plate, (1160, 500), radius=108, tone=GREEN, nucleus=True)
    plate.text((1160, 635), "EUKARYOTES", size=24, bold=True, fill=GREEN, anchor="mm")

    plate.arrow((640, 370), (1055, 465), fill=CORAL, width=7, head=21)
    _section_label(plate, (848, 395), "MITOCHONDRIAL ANCESTOR", CORAL, size=20)
    plate.draw.ellipse((1196, 515, 1237, 536), fill=CORAL_LIGHT, outline=CORAL, width=3)
    plate.draw.arc((1203, 517, 1231, 534), 20, 340, fill=CORAL, width=2)
    _finish(plate, content)


def _chloroplast(plate: SciencePlate, box: Box) -> None:
    x0, y0, x1, y1 = box
    plate.draw.rounded_rectangle(box, radius=int((y1-y0) * .42),
                                 fill=hex_rgba(GREEN_LIGHT, 135), outline=GREEN, width=7)
    inset = (x0 + 18, y0 + 18, x1 - 18, y1 - 18)
    plate.draw.rounded_rectangle(inset, radius=int((y1-y0) * .36),
                                 outline=TEAL, width=4)
    for column_x in (x0 + 118, x0 + 255, x0 + 392):
        for i in range(5):
            y = y0 + 92 + i * 22
            plate.draw.ellipse((column_x - 48, y - 8, column_x + 48, y + 8),
                               fill=TEAL_LIGHT, outline=TEAL, width=2)
    # Stroma cycle.
    cx, cy = x1 - 185, (y0 + y1) / 2
    plate.draw.arc((cx - 75, cy - 75, cx + 75, cy + 75), 22, 326,
                   fill=GOLD, width=8)
    a = math.radians(22)
    tip = (cx + math.cos(a) * 75, cy + math.sin(a) * 75)
    plate.draw.polygon((tip, (tip[0]-23, tip[1]-8), (tip[0]-8, tip[1]+17)), fill=GOLD)


def draw_photosynthesis(plate: SciencePlate, content: Mapping[str, object]) -> None:
    _panel(plate, (525, 245, 1110, 755), GREEN)
    _section_label(plate, (817, 285), "CHLOROPLAST", GREEN)
    _chloroplast(plate, (585, 350, 1050, 650))
    _section_label(plate, (715, 684), "THYLAKOIDS", TEAL)
    _section_label(plate, (950, 684), "STROMA", GOLD)

    # Inputs and outputs are large, material-specific marks.
    plate.draw.ellipse((130, 300, 235, 405), fill=GOLD_LIGHT, outline=GOLD, width=5)
    for angle in range(0, 360, 45):
        a = math.radians(angle)
        plate.draw.line((182 + math.cos(a)*65, 352 + math.sin(a)*65,
                         182 + math.cos(a)*91, 352 + math.sin(a)*91), fill=GOLD, width=5)
    _mechanism_arrow(plate, (300, 352), (555, 412), "LIGHT CAPTURE", GOLD)

    plate.draw.ellipse((145, 515, 210, 580), fill=BLUE_LIGHT, outline=BLUE, width=4)
    plate.text((265, 548), "H2O", size=29, bold=True, fill=BLUE, anchor="mm")
    plate.text((330, 635), "CO2", size=29, bold=True, fill=TEAL, anchor="mm")
    plate.draw.ellipse((150, 605, 190, 645), fill=TEAL_LIGHT, outline=TEAL, width=3)
    plate.draw.ellipse((183, 590, 230, 638), fill=TEAL_LIGHT, outline=TEAL, width=3)
    plate.draw.ellipse((215, 605, 255, 645), fill=TEAL_LIGHT, outline=TEAL, width=3)
    _mechanism_arrow(plate, (410, 575), (555, 540), "ATOM INPUTS", BLUE)

    plate.draw.polygon(((1270, 355), (1303, 412), (1368, 412),
                        (1401, 355), (1368, 298), (1303, 298)),
                       fill=GOLD_LIGHT, outline=GOLD)
    plate.text((1335, 355), "SUGAR", size=23, bold=True, fill=INK, anchor="mm")
    _mechanism_arrow(plate, (1080, 435), (1230, 365), "BUILD", CORAL)
    for x in (1294, 1340, 1386):
        plate.draw.ellipse((x - 18, 570, x + 18, 606), fill=BLUE_LIGHT,
                           outline=BLUE, width=3)
    plate.text((1340, 640), "O2 RELEASED", size=25, bold=True, fill=BLUE, anchor="mm")
    _mechanism_arrow(plate, (1080, 555), (1240, 583), "RELEASE", BLUE)
    _finish(plate, content)


def draw_digestion(plate: SciencePlate, content: Mapping[str, object]) -> None:
    _panel(plate, (275, 225, 1055, 785), CORAL)
    _panel(plate, (1090, 225, 1490, 785), BLUE)
    _section_label(plate, (665, 267), "COUPLED BODY SYSTEMS", CORAL)
    # Torso with distinguishable lungs, gut, kidneys, and colon.
    plate.draw.polygon(((505, 334), (588, 304), (742, 304), (825, 334),
                        (870, 520), (835, 742), (495, 742), (460, 520)),
                       fill=hex_rgba(CORAL_LIGHT, 62), outline=EDGE)
    _lungs(plate, (664, 420), scale=.63)
    plate.draw.line((665, 480, 665, 535), fill=EDGE, width=8)
    plate.draw.arc((600, 498, 733, 614), 175, 520, fill=CORAL, width=13)
    # Small intestine loops and colon frame.
    for y in (596, 625, 654):
        plate.draw.arc((582, y - 24, 748, y + 27), 5, 355, fill=GOLD, width=6)
    plate.draw.rounded_rectangle((570, 565, 760, 704), radius=32,
                                 outline=TEAL, width=9)
    _kidneys(plate, (808, 574), scale=.55)

    # Inputs.
    _section_label(plate, (170, 355), "FOOD", GOLD)
    plate.draw.ellipse((105, 405, 235, 458), fill=PAPER_LIGHT, outline=GOLD, width=5)
    plate.draw.ellipse((132, 383, 206, 438), fill=GREEN_LIGHT, outline=GREEN, width=3)
    plate.arrow((238, 430), (486, 505), fill=GOLD, width=8, head=21)
    _section_label(plate, (168, 605), "O2", BLUE)
    plate.draw.ellipse((102, 650, 145, 692), fill=BLUE_LIGHT, outline=BLUE, width=3)
    plate.draw.ellipse((137, 632, 185, 680), fill=BLUE_LIGHT, outline=BLUE, width=3)
    plate.draw.ellipse((174, 650, 217, 692), fill=BLUE_LIGHT, outline=BLUE, width=3)
    plate.arrow((228, 660), (585, 433), fill=BLUE, width=8, head=21)

    _section_label(plate, (1290, 267), "DIFFERENT EXIT ROUTES", BLUE, size=21)
    outputs = ((350, "CO₂", "Lungs", BLUE), (505, "Urea + water", "Kidneys", PLUM),
               (660, "Unabsorbed food", "Colon", GOLD))
    for y, material, organ, tone in outputs:
        _panel(plate, (1120, y - 55, 1460, y + 55), tone, radius=17)
        _body_text(plate, (1134, y - 47, 1446, y), material, fill=tone)
        _body_text(plate, (1134, y, 1446, y + 47), organ, fill=tone)
    plate.arrow((720, 395), (1110, 350), fill=BLUE, width=7, head=20)
    plate.arrow((835, 575), (1110, 505), fill=PLUM, width=7, head=20)
    plate.arrow((665, 702), (1110, 660), fill=GOLD, width=7, head=20)
    _body_text(plate, (310, 730, 1015, 774),
               "Blood connects these organs.")
    _finish(plate, content)


def draw_reproduction(plate: SciencePlate, content: Mapping[str, object]) -> None:
    _panel(plate, (105, 235, 685, 505), TEAL)
    _panel(plate, (105, 530, 685, 790), CORAL)
    _panel(plate, (925, 280, 1490, 745), GREEN)
    _section_label(plate, (395, 274), "ASEXUAL ROUTE", TEAL)
    _section_label(plate, (395, 569), "SEXUAL ROUTE", CORAL)
    _section_label(plate, (1208, 320), "NEW ORGANISM, THEN GROWTH", GREEN, size=22)

    _cell(plate, (225, 405), radius=68, tone=TEAL)
    _cell(plate, (545, 380), radius=42, tone=TEAL)
    _cell(plate, (545, 455), radius=42, tone=TEAL)
    _mechanism_arrow(plate, (308, 405), (475, 405), "MITOSIS", TEAL,
                     label_offset=(0, -80))

    plate.draw.ellipse((185, 618, 302, 735), fill=GOLD_LIGHT, outline=GOLD, width=5)
    plate.draw.ellipse((230, 658, 258, 686), fill=PLUM_LIGHT, outline=PLUM, width=3)
    plate.text((243, 756), "EGG", size=22, bold=True, fill=GOLD, anchor="mm")
    for offset in (-28, 0, 28):
        plate.draw.ellipse((438, 656 + offset, 472, 678 + offset),
                           fill=BLUE_LIGHT, outline=BLUE, width=3)
        plate.draw.arc((461, 660 + offset, 530, 700 + offset), 270, 70,
                       fill=BLUE, width=3)
    plate.text((485, 756), "SPERM", size=22, bold=True, fill=BLUE, anchor="mm")
    _mechanism_arrow(plate, (555, 675), (782, 675), "FERTILISATION", CORAL,
                     label_offset=(0, -78))

    # Only the sexual route creates a zygote. Both routes meet later at the
    # new-organism/growth stage.
    _cell(plate, (850, 665), radius=60, tone=GOLD)
    _section_label(plate, (850, 760), "SEXUAL ZYGOTE", GOLD)
    plate.arrow((610, 405), (1010, 465), fill=TEAL, width=7, head=20)
    _section_label(plate, (800, 380), "OFFSPRING", TEAL)
    plate.arrow((918, 635), (1010, 560), fill=GREEN, width=8, head=22)
    _section_label(plate, (1115, 395), "NEW OFFSPRING", GREEN)
    for row, count in enumerate((2, 3, 4)):
        for col in range(count):
            _cell(plate, (1115 + col * 57 - count * 27, 468 + row * 58),
                  radius=30, tone=GREEN, nucleus=True)
    plate.arrow((1250, 545), (1380, 545), fill=GREEN, width=8, head=22)
    _plant(plate, (1410, 656), height=205, flowering=False, roots=False, tone=GREEN)
    _body_text(plate, (1035, 645, 1450, 730), "Mitosis adds cells; differentiation assigns specialised jobs.")
    _finish(plate, content)


def draw_ecosystems(plate: SciencePlate, content: Mapping[str, object]) -> None:
    _panel(plate, (105, 230, 1495, 785), GREEN)
    _ground(plate, 624, 120, 1480)
    # A recognisable food web in a shared habitat.
    plate.draw.ellipse((145, 283, 245, 383), fill=GOLD_LIGHT, outline=GOLD, width=5)
    for angle in range(0, 360, 45):
        a = math.radians(angle)
        plate.draw.line((195 + math.cos(a)*60, 333 + math.sin(a)*60,
                         195 + math.cos(a)*84, 333 + math.sin(a)*84), fill=GOLD, width=5)
    _plant(plate, (465, 624), height=235)
    _rabbit(plate, (780, 543), scale=.60)
    _fox(plate, (1165, 535), scale=.62)
    for x in (445, 520, 1300):
        plate.draw.line((x, 708, x, 651), fill=EDGE, width=7)
        plate.draw.arc((x - 38, 622, x + 38, 682), 180, 360, fill=PLUM, width=7)
        plate.draw.line((x - 33, 650, x + 33, 650), fill=PLUM, width=4)

    _section_label(plate, (195, 444), "SUNLIGHT INPUT", GOLD, size=21)
    _section_label(plate, (465, 330), "PRODUCER", GREEN, size=21)
    _section_label(plate, (780, 350), "CONSUMER", TEAL, size=21)
    _section_label(plate, (1165, 338), "PREDATOR", CORAL, size=21)
    _section_label(plate, (1270, 744), "DECOMPOSERS", PLUM, size=20)

    plate.arrow((280, 380), (375, 454), fill=GOLD, width=8, head=21)
    plate.arrow((575, 495), (675, 510), fill=GOLD, width=8, head=21)
    plate.arrow((900, 510), (1030, 500), fill=GOLD, width=8, head=21)
    plate.arrow((1265, 475), (1405, 320), fill=GOLD, width=7, head=20)
    _section_label(plate, (1390, 291), "HEAT OUT", GOLD, size=20)

    # Matter cycles by a second, visually distinct route.
    plate.arrow((452, 611), (492, 675), fill=PLUM, width=6, head=18)
    plate.arrow((780, 594), (610, 686), fill=PLUM, width=6, head=18)
    plate.arrow((1160, 586), (1260, 682), fill=PLUM, width=6, head=18)
    plate.arrow((1250, 720), (540, 735), fill=TEAL, width=7, head=20)
    plate.arrow((540, 735), (420, 624), fill=TEAL, width=7, head=20)
    _section_label(plate, (860, 736), "NUTRIENTS CYCLE", TEAL, size=21)
    _section_label(plate, (800, 268), "GOLD = ENERGY FLOW     TEAL + PLUM = MATTER CYCLE", GREEN, size=20)
    _finish(plate, content)


def draw_microbes(plate: SciencePlate, content: Mapping[str, object]) -> None:
    _panel(plate, (105, 230, 1495, 785), BLUE)
    _section_label(plate, (800, 254), "LOG₁₀ SCALE · EACH EQUAL GAP = ×10", BLUE)
    x0, x1, axis_y = 185, 1415, 525
    plate.arrow((x0, axis_y), (x1, axis_y), fill=INK, width=8, head=22)
    ticks = ((185, "0.1 µm"), (595, "1 µm"), (1005, "10 µm"), (1415, "100 µm"))
    for x, label in ticks:
        plate.draw.line((x, axis_y - 20, x, axis_y + 20), fill=INK, width=5)
        plate.text((x, axis_y + 46), label, size=23, bold=True, fill=INK, anchor="mm")

    _virus(plate, (185, 365), radius=48)
    _section_label(plate, (185, 268 + 35), "VIRUS", CORAL, size=20)
    plate.arrow((185, 427), (185, 497), fill=CORAL, width=5, head=16)

    _bacterium(plate, (595, 682), scale=.66)
    _section_label(plate, (595, 754), "BACTERIUM", TEAL, size=20)
    plate.arrow((595, 625), (595, 553), fill=TEAL, width=5, head=16)

    # Yeast and the animal-cell range meet at the same 10 µm tick.
    plate.draw.ellipse((930, 325, 1080, 465), fill=_tint(PLUM, .58), outline=PLUM, width=5)
    plate.draw.ellipse((972, 354, 1030, 410), fill=PLUM_LIGHT, outline=PLUM, width=3)
    plate.draw.ellipse((1040, 342, 1088, 387), fill=_tint(PLUM, .65), outline=PLUM, width=4)
    _section_label(plate, (1005, 306), "YEAST", PLUM)
    plate.arrow((1005, 467), (1005, 497), fill=PLUM, width=5, head=16)

    _cell(plate, (1240, 690), radius=74, tone=GREEN)
    _cell(plate, (1395, 690), radius=92, tone=GREEN)
    plate.draw.line((1005, 640, 1415, 640), fill=GREEN, width=7)
    plate.draw.line((1005, 624, 1005, 657), fill=GREEN, width=5)
    plate.draw.line((1415, 624, 1415, 657), fill=GREEN, width=5)
    _section_label(plate, (1210, 607), "ANIMAL-CELL RANGE", GREEN)
    _body_text(plate, (275, 320, 875, 442),
               "Viruses are acellular. Bacteria and yeast are cells. Smaller animal cells overlap yeast in size.", size=24)
    _finish(plate, content)


RENDERERS: Dict[str, Renderer] = {
    "bio.0.living": draw_living,
    "bio.0.animals": draw_animals,
    "bio.0.plants": draw_plants,
    "bio.0.body": draw_body,
    "bio.0.seasons": draw_seasons,
    "bio.1.habitats": draw_habitats,
    "bio.1.food-chains": draw_food_chains,
    "bio.1.plants-parts": draw_plant_parts,
    "bio.1.human-body": draw_human_body,
    "bio.1.health": draw_health,
    "bio.2.classification": draw_classification,
    "bio.2.photosynthesis": draw_photosynthesis,
    "bio.2.digestion": draw_digestion,
    "bio.2.reproduction": draw_reproduction,
    "bio.2.ecosystems": draw_ecosystems,
    "bio.2.microbes": draw_microbes,
}


__all__ = ["RENDERERS"]
