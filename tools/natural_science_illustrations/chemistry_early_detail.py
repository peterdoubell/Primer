"""Bespoke field-guide renderers for generated early chemistry lessons.

The shared natural-science layouts are useful fallbacks, but early chemistry
needs a more literal visual language: recognisable materials and apparatus,
species-correct particles, visible conservation, and property-to-use causal
links.  These compositions are deliberately lesson-specific and deterministic.

All important distinctions have a shape, label, position, or line treatment in
addition to colour, and instructional type remains legible after the standard
1600 x 1000 plate is reduced to the 800 px responsive asset.
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

LABEL_MIN = 28
BODY_MIN = 27
FOOTER_SIZE = 28


def _tint(tone: str, amount: float = .78) -> str:
    return mix(tone, PAPER_LIGHT, amount)


def _panel(plate: SciencePlate, box: Box, tone: str, *, radius: int = 24,
           alpha: int = 222) -> None:
    plate.draw.rounded_rectangle(
        box,
        radius=radius,
        fill=hex_rgba(_tint(tone, .89), alpha),
        outline=hex_rgba(tone, 220),
        width=4,
    )


def _label(plate: SciencePlate, center: Point, value: str, tone: str,
           *, size: int = LABEL_MIN) -> None:
    plate.label(center, value, size=max(size, LABEL_MIN), fill=tone)


def _body(plate: SciencePlate, box: Box, value: str, *, size: int = BODY_MIN,
          bold: bool = True, fill: str = INK_SOFT, line_gap: int = 6) -> None:
    _wrapped_center(
        plate, box, value, size=max(size, BODY_MIN), bold=bold,
        fill=fill, line_gap=line_gap,
    )


def _finish(plate: SciencePlate, content: Mapping[str, object]) -> None:
    """Use a tall footer so the authored conclusion survives 800 px output."""
    plate.draw.rounded_rectangle(
        (165, 800, 1435, 900), radius=24,
        fill=hex_rgba(plate.domain_accent, 34),
        outline=hex_rgba(plate.domain_accent, 125), width=3,
    )
    _wrapped_center(
        plate, (195, 804, 1405, 896), str(content["footer"]),
        size=FOOTER_SIZE, bold=True, fill=INK, line_gap=2,
    )


def _mechanism_arrow(plate: SciencePlate, start: Point, end: Point, label: str,
                     tone: str, *, offset: Point = (0, -27)) -> None:
    plate.arrow(start, end, fill=tone, width=8, head=21)
    if label:
        _label(
            plate,
            ((start[0] + end[0]) / 2 + offset[0],
             (start[1] + end[1]) / 2 + offset[1]),
            label, tone, size=22,
        )


def _leader(plate: SciencePlate, start: Point, end: Point, tone: str) -> None:
    plate.draw.line((*start, *end), fill=tone, width=5)
    plate.dot(end, 7, fill=tone, outline=PAPER_LIGHT, width=2)


def _hatch(plate: SciencePlate, box: Box, tone: str, *, gap: int = 18,
           width: int = 3) -> None:
    """Add a bounded diagonal texture so categories never depend on hue."""
    x0, y0, x1, y1 = map(int, box)
    height = y1 - y0
    for start in range(x0 - height, x1, gap):
        ax = max(x0, start)
        ay = y1 - (ax - start)
        bx = min(x1, start + height)
        by = y1 - (bx - start)
        plate.draw.line((ax, ay, bx, by), fill=hex_rgba(tone, 100), width=width)


def _atom(plate: SciencePlate, center: Point, symbol: str, *, radius: float,
          tone: str, shape: str = "circle", scale_text: float = 1.0) -> None:
    x, y = center
    box = (x - radius, y - radius, x + radius, y + radius)
    fill = _tint(tone, .55)
    if shape == "square":
        plate.draw.rounded_rectangle(box, radius=max(7, int(radius * .23)),
                                     fill=fill, outline=tone, width=4)
    elif shape == "diamond":
        plate.draw.polygon(((x, y-radius), (x+radius, y),
                            (x, y+radius), (x-radius, y)),
                           fill=fill, outline=tone)
        plate.draw.line((x, y-radius, x+radius, y, x, y+radius,
                         x-radius, y, x, y-radius), fill=tone, width=4)
    else:
        plate.draw.ellipse(box, fill=fill, outline=tone, width=4)
    plate.text((x, y), symbol, size=max(22, int(radius * .78 * scale_text)),
               bold=True, fill=INK, anchor="mm")


def _bond(plate: SciencePlate, first: Point, second: Point, *, double: bool = False,
          tone: str = INK, width: int = 6) -> None:
    x0, y0 = first
    x1, y1 = second
    dx, dy = x1 - x0, y1 - y0
    length = math.hypot(dx, dy) or 1
    ox, oy = -dy / length * 6, dx / length * 6
    if double:
        plate.draw.line((x0+ox, y0+oy, x1+ox, y1+oy), fill=tone, width=width)
        plate.draw.line((x0-ox, y0-oy, x1-ox, y1-oy), fill=tone, width=width)
    else:
        plate.draw.line((x0, y0, x1, y1), fill=tone, width=width)


def _h2(plate: SciencePlate, center: Point, *, scale: float = 1.0) -> None:
    x, y = center
    a, b = (x - 34*scale, y), (x + 34*scale, y)
    _bond(plate, a, b, width=max(3, int(5*scale)))
    _atom(plate, a, "H", radius=25*scale, tone=BLUE)
    _atom(plate, b, "H", radius=25*scale, tone=BLUE)


def _o2(plate: SciencePlate, center: Point, *, scale: float = 1.0) -> None:
    x, y = center
    a, b = (x - 39*scale, y), (x + 39*scale, y)
    _bond(plate, a, b, double=True, width=max(3, int(5*scale)))
    _atom(plate, a, "O", radius=30*scale, tone=CORAL)
    _atom(plate, b, "O", radius=30*scale, tone=CORAL)


def _water(plate: SciencePlate, center: Point, *, scale: float = 1.0,
           angle: float = -math.pi / 2) -> None:
    """Draw one bent H2O molecule at the approximate 104.5 degree angle."""
    x, y = center
    spread = math.radians(52.25)
    distance = 61 * scale
    hydrogens = [
        (x + math.cos(angle-spread)*distance,
         y + math.sin(angle-spread)*distance),
        (x + math.cos(angle+spread)*distance,
         y + math.sin(angle+spread)*distance),
    ]
    for hydrogen in hydrogens:
        _bond(plate, (x, y), hydrogen, width=max(3, int(5*scale)))
    _atom(plate, (x, y), "O", radius=29*scale, tone=CORAL)
    for hydrogen in hydrogens:
        _atom(plate, hydrogen, "H", radius=22*scale, tone=BLUE)


def _ion(plate: SciencePlate, center: Point, symbol: str, *, positive: bool,
         radius: float = 27) -> None:
    _atom(
        plate, center, symbol, radius=radius,
        tone=BLUE if positive else CORAL,
        shape="circle" if positive else "square",
        scale_text=.78,
    )


def _beaker(plate: SciencePlate, box: Box, *, level: float = .62,
            liquid: str = BLUE_LIGHT, outline: str = BLUE) -> Box:
    """Return the liquid rectangle inside a tapered open beaker."""
    x0, y0, x1, y1 = box
    inset = (x1 - x0) * .10
    lip_y = y0 + 10
    liquid_y = y1 - (y1-y0) * level
    liquid_box = (x0+inset+4, liquid_y, x1-inset-4, y1-7)
    plate.draw.rectangle(liquid_box, fill=hex_rgba(liquid, 135))
    plate.draw.line((x0+inset, lip_y, x0+inset, y1,
                     x1-inset, y1, x1-inset, lip_y),
                    fill=outline, width=6, joint="curve")
    plate.draw.line((x0, lip_y, x1, lip_y), fill=outline, width=6)
    plate.draw.line((liquid_box[0], liquid_y, liquid_box[2], liquid_y),
                    fill=outline, width=3)
    return liquid_box


def _motion_mark(plate: SciencePlate, center: Point, *, angle: float,
                 length: float = 30, tone: str = INK_SOFT) -> None:
    x, y = center
    dx, dy = math.cos(angle)*length, math.sin(angle)*length
    plate.draw.line((x-dx, y-dy, x+dx, y+dy), fill=tone, width=4)


def _material_plank(plate: SciencePlate, box: Box) -> None:
    plate.draw.rounded_rectangle(box, radius=12, fill=GOLD_LIGHT,
                                 outline=EDGE, width=5)
    x0, y0, x1, y1 = box
    for fraction in (.22, .48, .73):
        y = y0 + (y1-y0)*fraction
        plate.draw.arc((x0+18, y-18, x1-18, y+20), 180, 360,
                       fill=EDGE, width=3)
    plate.draw.ellipse((x0+42, y0+31, x0+84, y0+58),
                       outline=EDGE, width=3)


def _saucepan(plate: SciencePlate, center: Point, *, scale: float = 1.0) -> None:
    x, y = center
    plate.draw.rounded_rectangle((x-102*scale, y-55*scale,
                                  x+92*scale, y+56*scale),
                                 radius=max(10, int(18*scale)),
                                 fill=_tint(PLUM, .55), outline=PLUM, width=5)
    plate.draw.line((x+88*scale, y-25*scale, x+175*scale, y-48*scale),
                    fill=PLUM, width=max(6, int(12*scale)))
    for offset in (-48, 0, 48):
        plate.arrow((x+offset*scale, y+116*scale),
                    (x+offset*scale, y+68*scale),
                    fill=CORAL, width=5, head=15)


def draw_materials(plate: SciencePlate, content: Mapping[str, object]) -> None:
    centers = (268, 623, 978, 1333)
    tones = (GOLD, PLUM, BLUE, TEAL)
    headings = ("WOOD", "METAL", "WATER", "AIR")
    for x, tone, heading in zip(centers, tones, headings):
        _panel(plate, (x-163, 225, x+163, 785), tone)
        _label(plate, (x, 267), heading, tone)
    _material_plank(plate, (centers[0]-105, 355, centers[0]+105, 500))
    _hatch(plate, (centers[0]-98, 362, centers[0]+98, 493), GOLD, gap=26, width=2)
    _body(plate, (centers[0]-145, 548, centers[0]+145, 752),
          "SOLID\nSTIFF + LIGHT\nabsorbs water\n→ dry furniture")

    _saucepan(plate, (centers[1]-22, 425), scale=.76)
    _body(plate, (centers[1]-145, 548, centers[1]+145, 752),
          "SOLID\nstrong + conducts heat\n→ pan base or wire")

    _beaker(plate, (centers[2]-100, 325, centers[2]+100, 515), level=.72)
    plate.arrow((centers[2]+115, 400), (centers[2]+145, 480),
                fill=BLUE, width=6, head=18)
    _body(plate, (centers[2]-145, 548, centers[2]+145, 752),
          "LIQUID\nflows + keeps volume\n→ drinking or washing")

    # A labelled syringe makes invisible, compressible air physically visible.
    x = centers[3]
    plate.draw.rounded_rectangle((x-115, 355, x+90, 482), radius=13,
                                 outline=TEAL, width=6)
    plate.draw.line((x-74, 365, x-74, 472), fill=INK, width=7)
    plate.draw.line((x-74, 419, x-160, 419), fill=INK, width=8)
    plate.draw.line((x+90, 419, x+147, 419), fill=TEAL, width=6)
    for px, py in ((x-35, 390), (x+8, 440), (x+52, 390)):
        plate.dot((px, py), 8, fill=TEAL_LIGHT, outline=TEAL, width=2)
    plate.arrow((x-169, 520), (x-88, 520), fill=CORAL, width=6, head=18)
    _label(plate, (x-125, 554), "PUSH", CORAL, size=21)
    _body(plate, (x-145, 578, x+145, 752),
          "GAS MIXTURE\nfills space + compresses\n→ breathing or tyre")
    _finish(plate, content)


def _mixing_beaker(plate: SciencePlate, center_x: float, tone: str,
                   kind: str) -> None:
    liquid = _beaker(plate, (center_x-126, 342, center_x+126, 614), level=.77)
    lx0, ly0, lx1, ly1 = liquid
    if kind == "salt":
        positions = ((-77, -135), (-30, -88), (34, -142), (82, -74),
                     (-73, -42), (5, -24), (69, -18), (-10, -175))
        for index, (dx, dy) in enumerate(positions):
            _ion(plate, (center_x+dx, ly1+dy), "Na+" if index % 2 == 0 else "Cl−",
                 positive=index % 2 == 0, radius=21)
    elif kind == "sand":
        for row, count in enumerate((6, 7, 8)):
            for column in range(count):
                # Reserve room for each triangular grain inside the glass.
                px = lx0 + 16 + column * (lx1 - lx0 - 32) / (count - 1)
                py = ly1 - 18 - row*23
                plate.draw.polygon(((px, py-10), (px+12, py+7),
                                    (px-9, py+12)), fill=GOLD_LIGHT, outline=EDGE)
        for px, py in ((center_x-65, ly0+45), (center_x+26, ly0+76),
                       (center_x+79, ly0+32)):
            plate.draw.polygon(((px, py-7), (px+8, py+6), (px-7, py+8)),
                               fill=GOLD_LIGHT, outline=EDGE)
    elif kind == "oil":
        plate.draw.rectangle((lx0, ly0, lx1, ly0+60),
                             fill=hex_rgba(GOLD_LIGHT, 205))
        plate.draw.line((lx0, ly0+60, lx1, ly0+60), fill=GOLD, width=5)
        for dx, dy, radius in ((-62, 103, 17), (8, 139, 24), (72, 92, 14)):
            plate.draw.ellipse((center_x+dx-radius, ly0+dy-radius,
                                center_x+dx+radius, ly0+dy+radius),
                               fill=GOLD_LIGHT, outline=GOLD, width=3)
    plate.draw.line((center_x-150, 304, center_x-117, 342), fill=tone, width=5)


def draw_mixing(plate: SciencePlate, content: Mapping[str, object]) -> None:
    centers = (330, 800, 1270)
    tones = (TEAL, GOLD, PLUM)
    headings = ("SALT + WATER", "SAND + WATER", "OIL + WATER")
    states = ("UNIFORM SOLUTION", "SETTLING SUSPENSION", "TWO LIQUID LAYERS")
    tests = ("EVAPORATE → SALT RETURNS", "FILTER → SAND RESIDUE",
             "LET STAND → OIL JOINS TOP")
    kinds = ("salt", "sand", "oil")
    for x, tone, heading, state, test, kind in zip(
            centers, tones, headings, states, tests, kinds):
        _panel(plate, (x-220, 225, x+220, 785), tone)
        _label(plate, (x, 267), heading, tone, size=22)
        _mixing_beaker(plate, x, tone, kind)
        _label(plate, (x, 650), state, tone, size=21)
        _body(plate, (x-190, 680, x+190, 766), test, size=25)
    _finish(plate, content)


def _state_container(plate: SciencePlate, box: Box, *, tone: str) -> None:
    x0, y0, x1, y1 = box
    plate.draw.line((x0, y0, x0, y1, x1, y1, x1, y0),
                    fill=tone, width=6, joint="curve")
    plate.draw.line((x0-12, y0, x1+12, y0), fill=hex_rgba(tone, 90), width=3)


def draw_water_states(plate: SciencePlate, content: Mapping[str, object]) -> None:
    centers = (325, 800, 1275)
    tones = (BLUE, TEAL, PLUM)
    headings = ("ICE · ORDERED", "LIQUID · MOBILE", "VAPOUR · SEPARATE")
    for x, tone, heading in zip(centers, tones, headings):
        _panel(plate, (x-207, 245, x+207, 770), tone)
        _label(plate, (x, 286), heading, tone, size=21)
        _state_container(plate, (x-157, 348, x+157, 650), tone=tone)

    # Ice: repeatable positions and dashed hydrogen-bond neighbours.
    ice_positions = [(325+dx, 420+dy) for dy in (0, 112) for dx in (-95, 0, 95)]
    for first, second in zip(ice_positions[:-1], ice_positions[1:]):
        plate.dashed_line(first, second, fill=GRID, width=3, dash=10, gap=9)
    for index, point in enumerate(ice_positions):
        _water(plate, point, scale=.49, angle=(-1 if index % 2 else 1)*math.pi/2)
    _body(plate, (155, 666, 495, 752), "vibrates around fixed neighbours")

    liquid_positions = ((715, 424), (797, 402), (879, 437), (744, 516),
                        (839, 508), (706, 589), (803, 586), (890, 571))
    for index, point in enumerate(liquid_positions):
        _water(plate, point, scale=.43, angle=(index*.79) % (2*math.pi))
        if index in (1, 4, 7):
            _motion_mark(plate, (point[0]+29, point[1]-29), angle=.6, length=12, tone=TEAL)
    _body(plate, (630, 666, 970, 752), "stays close; continually changes neighbours")

    vapour_positions = ((1175, 412), (1375, 395), (1242, 525),
                        (1392, 584), (1165, 602))
    for index, point in enumerate(vapour_positions):
        _water(plate, point, scale=.42, angle=(index*.9)-1.5)
        _motion_mark(plate, (point[0]+33, point[1]+28), angle=index*.7,
                     length=20, tone=PLUM)
    _body(plate, (1105, 666, 1445, 752), "large gaps; molecules move freely")

    _mechanism_arrow(plate, (535, 224), (650, 224), "ADD ENERGY", CORAL,
                     offset=(0, -20))
    _mechanism_arrow(plate, (1010, 224), (1125, 224), "ADD ENERGY", CORAL,
                     offset=(0, -20))
    plate.arrow((1125, 776), (1010, 776), fill=BLUE, width=6, head=18)
    plate.arrow((650, 776), (535, 776), fill=BLUE, width=6, head=18)
    _label(plate, (800, 776), "REMOVE ENERGY · REVERSE", BLUE, size=20)
    _finish(plate, content)


def _generic_particle(plate: SciencePlate, center: Point, *, tone: str,
                      radius: int = 18, shape: str = "circle") -> None:
    x, y = center
    if shape == "square":
        plate.draw.rounded_rectangle((x-radius, y-radius, x+radius, y+radius),
                                     radius=5, fill=_tint(tone, .48),
                                     outline=tone, width=3)
    else:
        plate.draw.ellipse((x-radius, y-radius, x+radius, y+radius),
                           fill=_tint(tone, .48), outline=tone, width=3)
    plate.draw.line((x-5, y, x+5, y), fill=INK, width=2)


def draw_matter(plate: SciencePlate, content: Mapping[str, object]) -> None:
    centers = (325, 800, 1275)
    headings = ("SOLID", "LIQUID", "GAS")
    tones = (GOLD, TEAL, PLUM)
    for x, heading, tone in zip(centers, headings, tones):
        _panel(plate, (x-205, 225, x+205, 785), tone)
        _label(plate, (x, 267), heading, tone)
        _state_container(plate, (x-150, 342, x+150, 620), tone=tone)

    # Stable neighbours: a self-supporting block retains a boundary.
    for row in range(4):
        for column in range(5):
            _generic_particle(plate, (245+column*40, 452+row*40), tone=GOLD,
                              shape="square")
    plate.draw.rounded_rectangle((220, 426, 430, 603), radius=10,
                                 outline=EDGE, width=3)
    _body(plate, (155, 642, 495, 760),
          "stable neighbours\n→ fixed shape + volume")

    # Close, disordered particles take the vessel's lower shape.
    liquid_points = ((680, 555), (726, 523), (775, 568), (825, 527),
                     (874, 568), (916, 529), (704, 592), (755, 607),
                     (808, 586), (860, 608), (906, 593))
    for index, point in enumerate(liquid_points):
        _generic_particle(plate, point, tone=TEAL)
        if index in (1, 4, 7):
            _motion_mark(plate, (point[0], point[1]-27), angle=.35, length=10, tone=TEAL)
    plate.draw.line((650, 495, 950, 495), fill=TEAL, width=4)
    _body(plate, (630, 642, 970, 760),
          "close + rearranging\n→ flows; fixed volume")

    gas_points = ((1158, 401), (1282, 382), (1390, 448), (1212, 520),
                  (1360, 572), (1268, 592))
    for index, point in enumerate(gas_points):
        _generic_particle(plate, point, tone=PLUM)
        _motion_mark(plate, (point[0]+30, point[1]), angle=index*.8,
                     length=18, tone=PLUM)
    # A descending piston shows that the large gaps can be reduced.
    plate.draw.rectangle((1135, 329, 1415, 356), fill=_tint(CORAL, .42),
                         outline=CORAL, width=4)
    plate.arrow((1275, 304), (1275, 340), fill=CORAL, width=6, head=16)
    _body(plate, (1105, 642, 1445, 760),
          "far apart + colliding\n→ fills space; compressible")
    _finish(plate, content)


def _identity_stamp(plate: SciencePlate, center: Point, text: str,
                    tone: str, *, same: bool) -> None:
    x, y = center
    plate.draw.rounded_rectangle((x-154, y-34, x+154, y+34), radius=18,
                                 fill=hex_rgba(_tint(tone, .72), 235),
                                 outline=tone, width=4)
    symbol = "=" if same else "≠"
    plate.text((x-117, y), symbol, size=33, bold=True, fill=tone, anchor="mm")
    plate.text((x+17, y), text, size=23, bold=True, fill=tone, anchor="mm")


def draw_changes(plate: SciencePlate, content: Mapping[str, object]) -> None:
    centers = (330, 800, 1270)
    tones = (BLUE, TEAL, CORAL)
    headings = ("MELTING / FREEZING", "DISSOLVE / RECOVER", "BURNING · MODEL")
    for x, tone, heading in zip(centers, tones, headings):
        _panel(plate, (x-215, 225, x+215, 785), tone)
        _label(plate, (x, 266), heading, tone, size=21)

    # One water species changes arrangement, not identity.
    for row in range(2):
        for col in range(2):
            _water(plate, (225+col*78, 400+row*96), scale=.43,
                   angle=(-1 if (row+col) % 2 else 1)*math.pi/2)
    plate.arrow((330, 470), (408, 470), fill=CORAL, width=7, head=19)
    for index, point in enumerate(((449, 397), (407, 494), (482, 521))):
        _water(plate, point, scale=.40, angle=index*.8)
    _label(plate, (330, 591), "HEAT ⇄ COOL", BLUE, size=21)
    _identity_stamp(plate, (330, 698), "SAME H2O", BLUE, same=True)

    # Alternating ionic solid becomes separated hydrated ions; evaporation
    # returns the solid, so no salt atoms vanish.
    for row in range(2):
        for col in range(2):
            positive = (row+col) % 2 == 0
            _ion(plate, (682+col*66, 410+row*70),
                 "Na+" if positive else "Cl−", positive=positive, radius=22)
    plate.arrow((800, 470), (877, 470), fill=TEAL, width=7, head=19)
    for index, point in enumerate(((905, 385), (949, 451), (900, 530), (977, 536))):
        positive = index % 2 == 0
        _ion(plate, point, "Na+" if positive else "Cl−",
             positive=positive, radius=21)
    _label(plate, (800, 591), "WATER ⇄ EVAPORATE", TEAL, size=20)
    _identity_stamp(plate, (800, 698), "SAME IONS", TEAL, same=True)

    # A deliberately explicit carbon-combustion model avoids pretending that
    # heterogeneous wood has one simple molecule.
    _atom(plate, (1110, 455), "C", radius=34, tone=INK_SOFT, shape="diamond")
    plate.text((1162, 455), "+", size=35, bold=True, anchor="mm")
    _o2(plate, (1228, 455), scale=.58)
    plate.arrow((1285, 455), (1322, 455), fill=CORAL, width=7, head=17)
    product = ((1350, "O", CORAL, "circle"),
               (1405, "C", INK_SOFT, "diamond"),
               (1460, "O", CORAL, "circle"))
    _bond(plate, (1350, 455), (1405, 455), double=True, width=4)
    _bond(plate, (1405, 455), (1460, 455), double=True, width=4)
    for x, symbol, tone, shape in product:
        _atom(plate, (x, 455), symbol, radius=22, tone=tone, shape=shape)
    # Keep the equation legible below the particle sketch.
    plate.text((1270, 562), "C + O₂ → CO₂", size=30, bold=True,
               fill=INK, anchor="mm")
    _body(plate, (1085, 594, 1455, 650),
          "real wood also yields H₂O + mineral ash", size=25)
    _identity_stamp(plate, (1270, 698), "NEW BONDS", CORAL, same=False)
    _finish(plate, content)


def _light_rays(plate: SciencePlate, start_x: float, end_x: float,
                ys: Sequence[float]) -> None:
    for y in ys:
        plate.arrow((start_x, y), (end_x, y), fill=GOLD, width=5, head=14)


def draw_material_properties(plate: SciencePlate,
                             content: Mapping[str, object]) -> None:
    boxes = ((105, 225, 785, 490), (815, 225, 1495, 490),
             (105, 515, 785, 785), (815, 515, 1495, 785))
    tones = (BLUE, CORAL, TEAL, PLUM)
    for box, tone in zip(boxes, tones):
        _panel(plate, box, tone, radius=20)

    _label(plate, (260, 263), "WINDOW", BLUE)
    plate.draw.rectangle((360, 303, 520, 414), fill=hex_rgba(BLUE_LIGHT, 72),
                         outline=BLUE, width=6)
    plate.draw.line((440, 303, 440, 414), fill=BLUE, width=3)
    _light_rays(plate, 180, 535, (333, 360, 387))
    _body(plate, (535, 300, 755, 450),
          "transparent + rigid\n→ light passes; shape holds", size=25)

    _label(plate, (970, 263), "PAN BASE", CORAL)
    _saucepan(plate, (1080, 360), scale=.60)
    plate.draw.line((915, 436, 1188, 436), fill=CORAL, width=6)
    for x in (950, 1005, 1060, 1115):
        plate.arrow((x, 452), (x+70, 452), fill=CORAL, width=4, head=12)
    _body(plate, (1210, 300, 1470, 450),
          "conducts heat + high melting point\n→ spreads heat; stays solid", size=24)

    _label(plate, (260, 555), "RAINCOAT", TEAL)
    plate.draw.polygon(((380, 600), (450, 568), (520, 600), (570, 735),
                        (470, 750), (440, 665), (410, 750), (310, 735)),
                       fill=_tint(TEAL, .50), outline=TEAL)
    _hatch(plate, (329, 600, 551, 728), TEAL, gap=24, width=2)
    for x, y in ((315, 608), (570, 625), (290, 694)):
        plate.draw.ellipse((x-10, y-16, x+10, y+16),
                           fill=BLUE_LIGHT, outline=BLUE, width=3)
    _body(plate, (548, 580, 758, 752),
          "flexible + water-resistant\n→ bends; droplets stay outside", size=24)

    _label(plate, (970, 555), "PAN HANDLE", PLUM)
    plate.draw.rounded_rectangle((1040, 602, 1120, 730), radius=18,
                                 fill=_tint(PLUM, .48), outline=PLUM, width=6)
    plate.draw.rounded_rectangle((1120, 626, 1285, 706), radius=26,
                                 outline=PLUM, width=11)
    for x, tone, mark in ((1048, CORAL, "HOT"), (1218, BLUE, "COOLER")):
        _label(plate, (x, 756), mark, tone, size=19)
    for x in (1150, 1190, 1230):
        plate.draw.line((x, 648, x, 685), fill=GRID, width=5)
    _body(plate, (1295, 580, 1470, 744),
          "low thermal conductivity\n→ slows heat flow to the hand", size=23)
    _finish(plate, content)


def draw_molecules(plate: SciencePlate, content: Mapping[str, object]) -> None:
    centers = (325, 800, 1275)
    tones = (BLUE, TEAL, PLUM)
    headings = ("ELEMENT · OXYGEN", "MOLECULAR COMPOUND", "IONIC COMPOUND")
    for x, tone, heading in zip(centers, tones, headings):
        _panel(plate, (x-212, 225, x+212, 785), tone)
        _label(plate, (x, 267), heading, tone, size=20)

    plate.draw.rounded_rectangle((200, 340, 450, 520), radius=82,
                                 outline=BLUE, width=3)
    _o2(plate, (325, 430), scale=1.20)
    plate.text((325, 559), "O=O", size=34, bold=True, fill=INK, anchor="mm")
    _body(plate, (150, 594, 500, 748),
          "one discrete O2 molecule\n2 oxygen atoms · same element")

    plate.draw.rounded_rectangle((650, 330, 950, 535), radius=92,
                                 outline=TEAL, width=3)
    _water(plate, (800, 445), scale=1.18, angle=-math.pi/2)
    plate.text((800, 559), "H—O—H · BENT", size=30, bold=True,
               fill=INK, anchor="mm")
    _body(plate, (625, 594, 975, 748),
          "one discrete H2O molecule\n2 H + 1 O · different elements")

    # Alternating shapes and charge labels show an extended ionic lattice,
    # not a collection of separate NaCl molecules.
    for row in range(3):
        for column in range(4):
            positive = (row+column) % 2 == 0
            _ion(plate, (1165+column*74, 365+row*78),
                 "Na+" if positive else "Cl−", positive=positive, radius=25)
    plate.draw.line((1108, 330, 1108, 558), fill=PLUM, width=5)
    plate.draw.line((1442, 330, 1442, 558), fill=PLUM, width=5)
    plate.text((1275, 584), "… REPEATING LATTICE …", size=25,
               bold=True, fill=PLUM, anchor="mm")
    _body(plate, (1100, 614, 1450, 748),
          "NaCl is a 1:1 formula ratio\nnot one isolated NaCl molecule")
    _finish(plate, content)


def _funnel(plate: SciencePlate, center: Point, *, scale: float = 1.0) -> None:
    x, y = center
    plate.draw.polygon(((x-78*scale, y-60*scale), (x+78*scale, y-60*scale),
                        (x+24*scale, y+25*scale), (x+12*scale, y+105*scale),
                        (x-12*scale, y+105*scale), (x-24*scale, y+25*scale)),
                       fill=hex_rgba(PAPER_LIGHT, 205), outline=BLUE)
    plate.draw.line((x-70*scale, y-48*scale, x, y+18*scale,
                     x+70*scale, y-48*scale), fill=GRID, width=3)


def _flask(plate: SciencePlate, center: Point, *, scale: float = 1.0,
           tone: str = BLUE) -> None:
    x, y = center
    points = ((x-30*scale, y-100*scale), (x+30*scale, y-100*scale),
              (x+30*scale, y-48*scale), (x+100*scale, y+82*scale),
              (x+82*scale, y+108*scale), (x-82*scale, y+108*scale),
              (x-100*scale, y+82*scale), (x-30*scale, y-48*scale))
    plate.draw.polygon(points, fill=hex_rgba(PAPER_LIGHT, 205), outline=tone)
    plate.draw.line(points + (points[0],), fill=tone, width=max(4, int(6*scale)))
    plate.draw.polygon(((x-80*scale, y+50*scale), (x+80*scale, y+50*scale),
                        (x+91*scale, y+84*scale), (x+76*scale, y+98*scale),
                        (x-76*scale, y+98*scale), (x-91*scale, y+84*scale)),
                       fill=hex_rgba(BLUE_LIGHT, 125))


def draw_mixtures(plate: SciencePlate, content: Mapping[str, object]) -> None:
    centers = (330, 800, 1270)
    tones = (GOLD, TEAL, PLUM)
    headings = ("LARGE SOLID + LIQUID", "DISSOLVED SOLID", "MISCIBLE LIQUIDS")
    tests = ("PARTICLE SIZE", "VOLATILITY", "BOILING-POINT RANGE")
    for x, tone, heading, test in zip(centers, tones, headings, tests):
        _panel(plate, (x-215, 225, x+215, 785), tone)
        _label(plate, (x, 266), heading, tone, size=19)
        _label(plate, (x, 739), test, tone, size=20)

    # Filtration: visibly separate residue and filtrate.
    plate.draw.polygon(((165, 337), (235, 337), (220, 425), (180, 425)),
                       fill=hex_rgba(BLUE_LIGHT, 120), outline=BLUE)
    for x, y in ((182, 370), (205, 391), (221, 356)):
        plate.dot((x, y), 7, fill=GOLD_LIGHT, outline=EDGE, width=2)
    plate.arrow((235, 390), (272, 422), fill=GOLD, width=6, head=16)
    _funnel(plate, (330, 478), scale=.72)
    for x in (293, 316, 340, 363):
        plate.dot((x, 439), 6, fill=GOLD_LIGHT, outline=EDGE, width=2)
    _beaker(plate, (265, 578, 395, 690), level=.50)
    plate.text((330, 563), "RESIDUE", size=24, bold=True, fill=GOLD, anchor="mm")
    plate.text((330, 705), "FILTRATE", size=24, bold=True, fill=BLUE, anchor="mm")

    # Simple distillation: solvent leaves as vapour and is collected; dissolved
    # non-volatile solid remains in the heated flask.
    _flask(plate, (720, 505), scale=.67, tone=TEAL)
    for px in (685, 720, 755):
        plate.dot((px, 558), 6, fill=CORAL_LIGHT, outline=CORAL, width=2)
    plate.draw.line((740, 435, 740, 350, 865, 350, 925, 405),
                    fill=TEAL, width=7, joint="curve")
    plate.draw.line((782, 326, 887, 326), fill=BLUE, width=4)
    plate.draw.line((782, 374, 887, 374), fill=BLUE, width=4)
    plate.arrow((800, 313), (875, 313), fill=BLUE, width=4, head=12)
    _beaker(plate, (884, 404, 1000, 635), level=.35)
    for x in (682, 720, 758):
        plate.arrow((x, 690), (x, 645), fill=CORAL, width=4, head=12)
    plate.text((721, 713), "SALT STAYS", size=23, bold=True, fill=CORAL, anchor="mm")
    plate.text((944, 665), "SOLVENT\nCOLLECTED", size=21, bold=True,
               fill=BLUE, anchor="mm")

    # Fractional distillation: repeated condensation/evaporation in a column
    # precedes condensation into the receiver.
    _flask(plate, (1178, 581), scale=.58, tone=PLUM)
    plate.draw.rounded_rectangle((1152, 320, 1204, 518), radius=12,
                                 fill=hex_rgba(PLUM_LIGHT, 100), outline=PLUM, width=5)
    for y in (355, 395, 435, 475):
        plate.draw.line((1158, y, 1198, y), fill=PLUM, width=4)
        plate.arrow((1178, y+24), (1178, y+5), fill=CORAL, width=3, head=9)
    plate.draw.line((1204, 337, 1360, 337, 1415, 405),
                    fill=PLUM, width=7, joint="curve")
    plate.draw.line((1260, 313, 1367, 313), fill=BLUE, width=4)
    plate.draw.line((1260, 361, 1367, 361), fill=BLUE, width=4)
    _beaker(plate, (1366, 404, 1468, 635), level=.30, liquid=CORAL_LIGHT,
            outline=CORAL)
    plate.text((1314, 392), "LOWER-BOILING\nENRICHED FIRST", size=20,
               bold=True, fill=CORAL, anchor="mm")
    plate.text((1270, 694), "REPEATED VAPOUR ⇄ LIQUID", size=22,
               bold=True, fill=PLUM, anchor="mm")
    _finish(plate, content)


def draw_reactions_intro(plate: SciencePlate,
                         content: Mapping[str, object]) -> None:
    _panel(plate, (110, 225, 690, 680), BLUE)
    _panel(plate, (910, 225, 1490, 680), GREEN)
    _label(plate, (400, 265), "REACTANTS · BEFORE", BLUE)
    _label(plate, (1200, 265), "PRODUCTS · AFTER", GREEN)

    # Molecule enclosures define exactly which atoms belong together.
    for center in ((275, 400), (525, 400)):
        plate.draw.rounded_rectangle((center[0]-95, 335, center[0]+95, 465),
                                     radius=60, outline=BLUE, width=3)
        _h2(plate, center, scale=1.05)
    plate.draw.rounded_rectangle((285, 495, 515, 640), radius=67,
                                 outline=CORAL, width=3)
    _o2(plate, (400, 568), scale=1.12)
    plate.text((400, 646), "2 H2  +  1 O2", size=29, bold=True,
               fill=INK, anchor="mm")

    for center in ((1065, 442), (1335, 442)):
        plate.draw.rounded_rectangle((center[0]-115, 335, center[0]+115, 555),
                                     radius=90, outline=GREEN, width=3)
        _water(plate, center, scale=1.05, angle=-math.pi/2)
    plate.text((1200, 646), "2 H2O", size=30, bold=True, fill=INK, anchor="mm")

    plate.arrow((720, 455), (880, 455), fill=PLUM, width=10, head=28)
    _label(plate, (800, 318), "BONDS REARRANGE", PLUM, size=21)
    plate.text((800, 510), "atoms persist", size=27, bold=True,
               fill=PLUM, anchor="mm")

    # A count ledger provides a redundant non-colour conservation check.
    plate.draw.rounded_rectangle((205, 701, 1395, 780), radius=20,
                                 fill=hex_rgba(GOLD_LIGHT, 100), outline=GOLD, width=4)
    plate.text((330, 740), "ATOM LEDGER", size=25, bold=True,
               fill=GOLD, anchor="mm")
    plate.text((625, 740), "H: 4 before = 4 after", size=27, bold=True,
               fill=INK, anchor="mm")
    plate.text((1055, 740), "O: 2 before = 2 after", size=27, bold=True,
               fill=INK, anchor="mm")
    _finish(plate, content)


def _scale_marker(plate: SciencePlate, x: float, y: float, shape: str,
                  tone: str, label: str, value: str) -> None:
    if shape == "triangle":
        plate.draw.polygon(((x, y-40), (x+36, y+25), (x-36, y+25)),
                           fill=_tint(tone, .50), outline=tone)
        plate.draw.line((x, y-40, x+36, y+25, x-36, y+25, x, y-40),
                        fill=tone, width=4)
    elif shape == "square":
        plate.draw.rounded_rectangle((x-32, y-32, x+32, y+32), radius=8,
                                     fill=_tint(tone, .50), outline=tone, width=4)
    elif shape == "diamond":
        plate.draw.polygon(((x, y-39), (x+39, y), (x, y+39), (x-39, y)),
                           fill=_tint(tone, .50), outline=tone)
        plate.draw.line((x, y-39, x+39, y, x, y+39, x-39, y, x, y-39),
                        fill=tone, width=4)
    else:
        plate.draw.ellipse((x-33, y-33, x+33, y+33),
                           fill=_tint(tone, .50), outline=tone, width=4)
    plate.text((x, y+105), label, size=24, bold=True, fill=tone, anchor="mm")
    plate.text((x, y+136), value, size=23, bold=True, fill=INK, anchor="mm")


def draw_acids(plate: SciencePlate, content: Mapping[str, object]) -> None:
    _panel(plate, (110, 225, 1490, 530), PLUM)
    _label(plate, (310, 263), "MORE ACIDIC · [H3O+]", CORAL, size=20)
    _label(plate, (1290, 263), "MORE BASIC · [OH−]", BLUE, size=20)
    x0, x1, axis_y = 180, 1420, 386
    plate.arrow((x0, axis_y), (x1, axis_y), fill=INK, width=8, head=22)
    for value in range(15):
        x = x0 + (x1-x0)*value/14
        height = 19 if value in (0, 2, 7, 10, 13, 14) else 11
        plate.draw.line((x, axis_y-height, x, axis_y+height), fill=INK, width=4)
        if value in (0, 14):
            plate.text((x, axis_y+38), str(value), size=22, bold=True,
                       fill=INK, anchor="mm")
    marker_y = 326
    positions = ((2, "triangle", CORAL, "LEMON", "pH ≈ 2"),
                 (7, "circle", GREEN, "PURE WATER", "pH 7 · 25 °C"),
                 (10, "square", BLUE, "SOAP", "pH ≈ 10"),
                 (12.5, "diamond", PLUM, "BLEACH", "pH ≈ 12–13"))
    for value, shape, tone, label, text in positions:
        x = x0 + (x1-x0)*value/14
        plate.draw.line((x, marker_y+40, x, axis_y-21), fill=tone, width=4)
        _scale_marker(plate, x, marker_y, shape, tone, label, text)

    _panel(plate, (110, 555, 760, 785), CORAL, radius=20)
    _label(plate, (435, 592), "ONE pH STEP = TENFOLD", CORAL, size=21)
    plate.text((225, 651), "pH 3", size=25, bold=True, fill=INK, anchor="mm")
    plate.text((610, 651), "pH 4", size=25, bold=True, fill=INK, anchor="mm")
    # Ten patterned hydronium counters versus one: a ratio model, not a claim
    # about literal molecules in a sample.
    for row in range(2):
        for col in range(5):
            x, y = 335+col*45, 644+row*48
            plate.draw.ellipse((x-14, y-14, x+14, y+14),
                               fill=CORAL_LIGHT, outline=CORAL, width=3)
            plate.text((x, y), "+", size=17, bold=True, fill=INK, anchor="mm")
    plate.draw.ellipse((610-17, 700-17, 610+17, 700+17),
                       fill=CORAL_LIGHT, outline=CORAL, width=3)
    plate.text((610, 700), "+", size=19, bold=True, fill=INK, anchor="mm")
    plate.text((435, 755), "relative hydronium activity · 10 : 1", size=23,
               bold=True, fill=CORAL, anchor="mm")

    _panel(plate, (790, 555, 1490, 785), BLUE, radius=20)
    _label(plate, (1140, 592), "NEUTRALISATION · PROTON TRANSFER", BLUE, size=20)
    _atom(plate, (905, 690), "H3O+", radius=45, tone=CORAL, scale_text=.62)
    plate.text((985, 690), "+", size=34, bold=True, anchor="mm")
    _atom(plate, (1055, 690), "OH−", radius=43, tone=BLUE, shape="square",
          scale_text=.62)
    plate.arrow((1120, 690), (1215, 690), fill=PLUM, width=8, head=21)
    _water(plate, (1300, 690), scale=.55, angle=-math.pi/2)
    plate.text((1395, 690), "× 2", size=29, bold=True, fill=INK, anchor="mm")
    _finish(plate, content)


def _periodic_cell(plate: SciencePlate, box: Box, *, symbol: str = "",
                   tone: str = PAPER_LIGHT, outline: str = GRID,
                   hatch: bool = False, atomic_number: str = "") -> None:
    plate.draw.rounded_rectangle(box, radius=5, fill=hex_rgba(tone, 180),
                                 outline=outline, width=3)
    if hatch:
        _hatch(plate, box, outline, gap=15, width=2)
    x0, y0, x1, y1 = box
    if atomic_number:
        plate.text((x0+6, y0+5), atomic_number, size=16, bold=True,
                   fill=INK_SOFT, anchor="la")
    if symbol:
        plate.text(((x0+x1)/2, (y0+y1)/2+3), symbol, size=24, bold=True,
                   fill=INK, anchor="mm")


def _outer_shell_atom(plate: SciencePlate, center: Point, symbol: str,
                      configuration: str, outer: int, tone: str) -> None:
    x, y = center
    for radius in (18, 36, 56):
        plate.draw.ellipse((x-radius, y-radius, x+radius, y+radius),
                           outline=hex_rgba(tone, 170), width=3)
    plate.dot((x, y), 9, fill=tone, outline=INK, width=2)
    for index in range(outer):
        angle = -math.pi/2 + 2*math.pi*index/outer if outer else 0
        px, py = x+math.cos(angle)*56, y+math.sin(angle)*56
        plate.dot((px, py), 5, fill=PAPER_LIGHT, outline=tone, width=2)
    plate.text((x+95, y-18), symbol, size=30, bold=True, fill=tone, anchor="lm")
    plate.text((x+95, y+20), configuration, size=24, bold=True,
               fill=INK, anchor="lm")


def draw_periodic(plate: SciencePlate, content: Mapping[str, object]) -> None:
    _panel(plate, (105, 225, 1085, 785), BLUE)
    _panel(plate, (1110, 225, 1495, 785), PLUM)
    _label(plate, (595, 263), "ATOMIC NUMBER INCREASES →", BLUE, size=22)
    _label(plate, (1302, 263), "PERIOD 3 SHELLS", PLUM, size=21)

    left, top, cell_w, cell_h = 132, 332, 51, 52
    occupied = {
        1: {1: ("H", "1"), 18: ("He", "2")},
        2: {1: ("Li", "3"), 2: ("Be", "4"), 13: ("B", "5"),
            14: ("C", "6"), 15: ("N", "7"), 16: ("O", "8"),
            17: ("F", "9"), 18: ("Ne", "10")},
        3: {1: ("Na", "11"), 2: ("Mg", "12"), 13: ("Al", "13"),
            14: ("Si", "14"), 15: ("P", "15"), 16: ("S", "16"),
            17: ("Cl", "17"), 18: ("Ar", "18")},
        4: {group: ("", "") for group in range(1, 19)},
        5: {group: ("", "") for group in range(1, 19)},
        6: {group: ("", "") for group in range(1, 19)},
        7: {group: ("", "") for group in range(1, 19)},
    }
    for group in (1, 2, 13, 17, 18):
        x = left + (group-1)*cell_w + cell_w/2
        plate.text((x, top-28), str(group), size=21, bold=True,
                   fill=INK, anchor="mm")
    for period in range(1, 8):
        plate.text((left-19, top+(period-1)*cell_h+cell_h/2), str(period),
                   size=21, bold=True, fill=INK, anchor="mm")
        for group, (symbol, atomic) in occupied[period].items():
            box = (left+(group-1)*cell_w, top+(period-1)*cell_h,
                   left+group*cell_w-3, top+period*cell_h-3)
            if group == 1:
                tone, outline, hatch = GOLD_LIGHT, GOLD, True
            elif group == 17:
                tone, outline, hatch = CORAL_LIGHT, CORAL, True
            elif group == 18:
                tone, outline, hatch = PLUM_LIGHT, PLUM, False
            elif period == 3:
                tone, outline, hatch = BLUE_LIGHT, BLUE, False
            else:
                tone, outline, hatch = PAPER_LIGHT, GRID, False
            _periodic_cell(plate, box, symbol=symbol, tone=tone,
                           outline=outline, hatch=hatch, atomic_number=atomic)

    # Empty positions in the short periods remain genuinely empty rather than
    # suggesting nonexistent elements. A bracket names the recurring groups.
    plate.draw.line((left, top-8, left, top+7*cell_h+5), fill=GOLD, width=5)
    plate.draw.line((left+16*cell_w, top-8, left+16*cell_w,
                     top+7*cell_h+5), fill=CORAL, width=5)
    plate.draw.line((left+17*cell_w, top-8, left+17*cell_w,
                     top+7*cell_h+5), fill=PLUM, width=5)
    plate.text((190, 736), "G1 · 1 OUTER e−", size=27, bold=True,
               fill=GOLD, anchor="lm")
    plate.text((495, 736), "G17 · 7 OUTER e−", size=27, bold=True,
               fill=CORAL, anchor="lm")
    plate.text((795, 736), "G18 · FULL OUTER", size=27,
               bold=True, fill=PLUM, anchor="lm")

    _outer_shell_atom(plate, (1192, 385), "Na", "2 | 8 | 1", 1, GOLD)
    _outer_shell_atom(plate, (1192, 545), "Cl", "2 | 8 | 7", 7, CORAL)
    _outer_shell_atom(plate, (1192, 705), "Ar", "2 | 8 | 8", 8, PLUM)
    plate.text((1287, 430), "reactive metal", size=22, bold=True,
               fill=GOLD, anchor="lm")
    plate.text((1287, 615), "reactive\nnonmetal", size=21, bold=True,
               fill=CORAL, anchor="lm")
    plate.text((1287, 750), "low reactivity", size=22, bold=True,
               fill=PLUM, anchor="lm")
    _finish(plate, content)


RENDERERS: Dict[str, Renderer] = {
    "chem.0.materials": draw_materials,
    "chem.0.mixing": draw_mixing,
    "chem.0.water-states": draw_water_states,
    "chem.1.matter": draw_matter,
    "chem.1.changes": draw_changes,
    "chem.1.materials-props": draw_material_properties,
    "chem.2.molecules": draw_molecules,
    "chem.2.mixtures": draw_mixtures,
    "chem.2.reactions-intro": draw_reactions_intro,
    "chem.2.acids": draw_acids,
    "chem.2.periodic": draw_periodic,
}


__all__ = ["RENDERERS"]
