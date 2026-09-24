"""Bespoke field-guide renderers for generated early Earth & Space lessons.

The shared natural-science layouts are useful fallbacks, but Earth science is
spatial: water crosses reservoirs, rock changes at boundaries, and scale is
often the central fact.  These deterministic compositions therefore use
landscape sections, measured profiles, nested views, and labelled material or
energy paths instead of generic cards.

Every important distinction has a position, shape, texture, or line treatment
in addition to colour, and instructional text remains readable after the
standard 1600 x 1000 plate is reduced to its 800 px responsive asset.
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

LABEL_MIN = 27
BODY_MIN = 26
FOOTER_SIZE = 28


def _tint(tone: str, amount: float = .78) -> str:
    return mix(tone, PAPER_LIGHT, amount)


def _panel(plate: SciencePlate, box: Box, tone: str, *, radius: int = 24,
           alpha: int = 222) -> None:
    plate.draw.rounded_rectangle(
        box, radius=radius, fill=hex_rgba(_tint(tone, .89), alpha),
        outline=hex_rgba(tone, 218), width=4,
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
    plate.draw.rounded_rectangle(
        (165, 800, 1435, 900), radius=24,
        fill=hex_rgba(plate.domain_accent, 34),
        outline=hex_rgba(plate.domain_accent, 125), width=3,
    )
    _wrapped_center(
        plate, (195, 804, 1405, 896), str(content["footer"]),
        size=FOOTER_SIZE, bold=True, fill=INK, line_gap=2,
    )


def _arrow(plate: SciencePlate, start: Point, end: Point, label: str,
           tone: str, *, offset: Point = (0, -26), width: int = 8) -> None:
    plate.arrow(start, end, fill=tone, width=width, head=21)
    if label:
        _label(
            plate,
            ((start[0] + end[0]) / 2 + offset[0],
             (start[1] + end[1]) / 2 + offset[1]),
            label, tone, size=22,
        )


def _curved_arrow(plate: SciencePlate, points: Sequence[Point], tone: str,
                  *, width: int = 8) -> None:
    plate.polyline(points, fill=tone, width=width)
    if len(points) > 1:
        plate.arrow(points[-2], points[-1], fill=tone, width=width, head=21)


def _leader(plate: SciencePlate, start: Point, end: Point, tone: str) -> None:
    plate.draw.line((*start, *end), fill=tone, width=5)
    plate.dot(end, 7, fill=tone, outline=PAPER_LIGHT, width=2)


def _hatch(plate: SciencePlate, box: Box, tone: str, *, gap: int = 18,
           width: int = 3) -> None:
    x0, y0, x1, y1 = map(int, box)
    height = y1 - y0
    for start in range(x0 - height, x1, gap):
        ax = max(x0, start)
        ay = y1 - (ax - start)
        bx = min(x1, start + height)
        by = y1 - (bx - start)
        plate.draw.line((ax, ay, bx, by), fill=hex_rgba(tone, 95), width=width)


def _sun(plate: SciencePlate, center: Point, *, radius: float = 44) -> None:
    x, y = center
    for angle in range(0, 360, 45):
        a = math.radians(angle)
        plate.draw.line(
            (x + math.cos(a) * radius * 1.25, y + math.sin(a) * radius * 1.25,
             x + math.cos(a) * radius * 1.65, y + math.sin(a) * radius * 1.65),
            fill=GOLD, width=5,
        )
    plate.draw.ellipse((x-radius, y-radius, x+radius, y+radius),
                       fill=GOLD_LIGHT, outline=GOLD, width=5)


def _cloud(plate: SciencePlate, center: Point, *, scale: float = 1.0,
           tone: str = BLUE) -> None:
    x, y = center
    blobs = ((-66, 12, 43), (-28, -15, 55), (24, -22, 61), (70, 10, 45))
    for dx, dy, radius in blobs:
        plate.draw.ellipse(
            (x+(dx-radius)*scale, y+(dy-radius)*scale,
             x+(dx+radius)*scale, y+(dy+radius)*scale),
            fill=_tint(tone, .72), outline=tone, width=max(3, int(4*scale)),
        )
    plate.draw.rounded_rectangle(
        (x-105*scale, y+5*scale, x+110*scale, y+54*scale),
        radius=max(12, int(24*scale)), fill=_tint(tone, .72),
        outline=tone, width=max(3, int(4*scale)),
    )


def _drop(plate: SciencePlate, center: Point, *, size: float = 18,
          tone: str = BLUE) -> None:
    x, y = center
    plate.draw.polygon(((x, y-size*1.4), (x-size*.78, y),
                        (x, y+size), (x+size*.78, y)),
                       fill=_tint(tone, .48), outline=tone)


def _mountain(plate: SciencePlate, points: Sequence[Point], *,
              fill: str = GOLD_LIGHT, outline: str = EDGE,
              snow: bool = False) -> None:
    plate.draw.polygon(points, fill=fill, outline=outline)
    plate.draw.line(tuple(coordinate for point in points for coordinate in point),
                    fill=outline, width=5, joint="curve")
    if snow and len(points) >= 3:
        peak = min(points, key=lambda point: point[1])
        x, y = peak
        plate.draw.polygon(((x-42, y+60), (x, y), (x+45, y+66),
                            (x+18, y+52), (x-3, y+63), (x-24, y+45)),
                           fill=PAPER_LIGHT, outline=BLUE)


def _tree(plate: SciencePlate, base: Point, *, scale: float = 1.0) -> None:
    x, y = base
    plate.draw.rectangle((x-9*scale, y-83*scale, x+9*scale, y),
                         fill=_tint(EDGE, .22), outline=EDGE, width=3)
    for dx, dy, radius in ((0, -112, 40), (-31, -88, 34), (34, -86, 35)):
        plate.draw.ellipse((x+(dx-radius)*scale, y+(dy-radius)*scale,
                            x+(dx+radius)*scale, y+(dy+radius)*scale),
                           fill=GREEN_LIGHT, outline=GREEN, width=3)


def _rock(plate: SciencePlate, center: Point, *, size: float = 70,
          kind: str = "igneous") -> None:
    x, y = center
    shape = ((x-size*.78, y+size*.34), (x-size*.55, y-size*.45),
             (x-size*.05, y-size*.68), (x+size*.61, y-size*.42),
             (x+size*.83, y+size*.30), (x+size*.30, y+size*.63),
             (x-size*.38, y+size*.60))
    tone = {"igneous": CORAL, "sedimentary": GOLD,
            "metamorphic": PLUM}.get(kind, EDGE)
    plate.draw.polygon(shape, fill=_tint(tone, .62), outline=tone)
    plate.draw.line(tuple(coordinate for point in shape + (shape[0],)
                          for coordinate in point), fill=tone, width=5)
    if kind == "igneous":
        for dx, dy, radius in ((-24, -11, 7), (20, -27, 6), (32, 18, 8), (-11, 28, 5)):
            plate.dot((x+dx, y+dy), radius, fill=EDGE, outline=EDGE, width=1)
    elif kind == "sedimentary":
        for offset in (-28, -5, 20):
            plate.draw.line((x-size*.57, y+offset, x+size*.58, y+offset+7),
                            fill=EDGE, width=4)
    elif kind == "metamorphic":
        for offset in (-30, -8, 16):
            plate.draw.arc((x-size*.65, y+offset-16, x+size*.65, y+offset+22),
                           5, 175, fill=EDGE, width=4)


def _planet(plate: SciencePlate, center: Point, radius: float, tone: str,
            *, rings: bool = False, stripes: bool = False,
            hatch: bool = False) -> None:
    x, y = center
    if rings:
        plate.draw.ellipse((x-radius*1.65, y-radius*.48,
                            x+radius*1.65, y+radius*.48),
                           outline=EDGE, width=max(3, int(radius*.10)))
    plate.draw.ellipse((x-radius, y-radius, x+radius, y+radius),
                       fill=_tint(tone, .48), outline=tone,
                       width=max(3, int(radius*.10)))
    if stripes:
        for factor in (-.48, -.18, .14, .46):
            half = math.sqrt(max(0, 1-factor*factor)) * radius * .88
            yy = y + factor*radius
            plate.draw.line((x-half, yy, x+half, yy), fill=EDGE,
                            width=max(2, int(radius*.055)))
    if hatch:
        for factor in (-.45, -.1, .28):
            half = math.sqrt(max(0, 1-factor*factor)) * radius * .72
            yy = y + factor*radius
            plate.draw.line((x-half, yy, x+half, yy+radius*.18), fill=EDGE,
                            width=max(2, int(radius*.045)))


def _volcano(plate: SciencePlate, base: Point, *, scale: float = 1.0) -> None:
    x, y = base
    plate.draw.polygon(((x-105*scale, y), (x-25*scale, y-145*scale),
                        (x+12*scale, y-145*scale), (x+110*scale, y)),
                       fill=GOLD_LIGHT, outline=EDGE)
    plate.draw.line((x-105*scale, y, x-25*scale, y-145*scale,
                     x+12*scale, y-145*scale, x+110*scale, y),
                    fill=EDGE, width=max(3, int(5*scale)))
    plate.draw.polygon(((x-18*scale, y-145*scale), (x+5*scale, y-145*scale),
                        (x+35*scale, y-70*scale), (x+7*scale, y-15*scale),
                        (x-12*scale, y-70*scale)), fill=CORAL_LIGHT,
                       outline=CORAL)
    for dx, dy, radius in ((-9, -178, 17), (20, -192, 23), (-24, -214, 18)):
        plate.draw.ellipse((x+(dx-radius)*scale, y+(dy-radius)*scale,
                            x+(dx+radius)*scale, y+(dy+radius)*scale),
                           fill=_tint(PLUM, .72), outline=PLUM, width=3)


def _quake(plate: SciencePlate, center: Point, *, size: float = 18,
           tone: str = CORAL) -> None:
    x, y = center
    points = []
    for index in range(16):
        a = math.pi*2*index/16 - math.pi/2
        radius = size if index % 2 == 0 else size*.42
        points.append((x+math.cos(a)*radius, y+math.sin(a)*radius))
    plate.draw.polygon(points, fill=_tint(tone, .25), outline=tone)


def draw_weather(plate: SciencePlate, content: Mapping[str, object]) -> None:
    _panel(plate, (105, 230, 1495, 785), BLUE)
    # One weather-making cross-section: uneven heating sets air and water moving.
    plate.draw.rectangle((120, 514, 1480, 770), fill=hex_rgba(BLUE_LIGHT, 72))
    plate.draw.polygon(((120, 606), (315, 505), (515, 579), (690, 505),
                        (840, 612), (840, 770), (120, 770)),
                       fill=GOLD_LIGHT, outline=EDGE)
    _hatch(plate, (120, 620, 840, 770), GOLD, gap=27, width=2)
    plate.draw.rectangle((840, 610, 1480, 770), fill=hex_rgba(BLUE, 95))
    for y in (645, 690, 735):
        plate.draw.arc((850, y-24, 1465, y+30), 190, 350, fill=BLUE, width=3)
    _sun(plate, (1275, 325), radius=45)
    _cloud(plate, (650, 346), scale=.72)
    for x, y in ((590, 431), (640, 459), (697, 430), (741, 468)):
        _drop(plate, (x, y), size=14)

    for x in (1030, 1140, 1250):
        plate.arrow((x, 600), (x-15, 455), fill=TEAL, width=7, head=19)
    _label(plate, (1140, 554), "EVAPORATION", TEAL, size=23)
    _curved_arrow(plate, ((1220, 414), (1060, 382), (870, 356), (776, 356)), GOLD)
    _label(plate, (1010, 329), "WIND: HIGH → LOW PRESSURE", GOLD, size=21)
    _curved_arrow(plate, ((816, 584), (790, 515), (758, 446), (728, 403)), CORAL)
    _label(plate, (873, 427), "MOIST AIR RISES", CORAL, size=20)
    plate.arrow((690, 318), (690, 274), fill=BLUE, width=6, head=18)
    _label(plate, (690, 252), "COOLS · CONDENSES", BLUE, size=21)
    _label(plate, (630, 516), "RAIN / SNOW", BLUE, size=22)
    _label(plate, (430, 699), "LAND", GOLD, size=22)
    _label(plate, (1180, 699), "WATER", BLUE, size=22)
    _body(plate, (138, 258, 430, 370),
          "Sunlight warms surfaces unevenly. Pressure differences move air.",
          size=25)
    _finish(plate, content)


def draw_land_water(plate: SciencePlate, content: Mapping[str, object]) -> None:
    _panel(plate, (105, 230, 1495, 785), BLUE)
    # Watershed profile with surface flow, groundwater, and sediment fate.
    land = ((120, 650), (250, 560), (390, 330), (540, 520), (680, 430),
            (790, 595), (940, 650), (1080, 678), (1200, 694),
            (1200, 770), (120, 770))
    plate.draw.polygon(land, fill=GOLD_LIGHT, outline=EDGE)
    plate.draw.line(tuple(c for p in land[:9] for c in p), fill=EDGE,
                    width=6, joint="curve")
    plate.draw.rectangle((1200, 650, 1480, 770), fill=hex_rgba(BLUE_LIGHT, 125))
    for y in (672, 710, 748):
        plate.draw.arc((1195, y-18, 1480, y+26), 190, 350, fill=BLUE, width=3)
    # Stream network follows two slopes into the trunk river.
    plate.polyline(((392, 345), (430, 450), (520, 535), (645, 585),
                    (790, 625), (940, 653), (1100, 675), (1245, 687)),
                   fill=BLUE, width=14)
    plate.polyline(((685, 445), (700, 515), (760, 584)), fill=BLUE, width=10)
    plate.polyline(((250, 565), (315, 578), (410, 515)), fill=BLUE, width=8)
    # Delta distributaries and deposited sediment wedges.
    for end in ((1335, 664), (1340, 689), (1332, 718)):
        plate.draw.line((1180, 684, *end), fill=BLUE, width=7)
    plate.draw.polygon(((1160, 689), (1275, 661), (1310, 727)),
                       fill=hex_rgba(GOLD, 90), outline=GOLD)
    # Groundwater is separated by a dashed saturated path.
    plate.draw.polygon(((150, 704), (390, 675), (670, 688), (955, 708),
                        (1160, 694), (1160, 758), (150, 758)),
                       fill=hex_rgba(TEAL_LIGHT, 100), outline=TEAL)
    plate.dashed_line((210, 716), (1115, 715), fill=TEAL, width=6,
                      dash=24, gap=15)
    for x in (324, 465, 720):
        plate.arrow((x, 620), (x+10, 699), fill=TEAL, width=5, head=16)
    _cloud(plate, (445, 275), scale=.52)
    for x in (390, 440, 490):
        _drop(plate, (x, 348), size=12)
    _label(plate, (394, 394), "RIDGELINE DIVIDE", GOLD, size=21)
    _label(plate, (570, 548), "TRIBUTARIES JOIN", BLUE, size=21)
    _label(plate, (905, 578), "RIVER + SEDIMENT", BLUE, size=20)
    _label(plate, (1333, 607), "DELTA: FLOW SLOWS", GOLD, size=20)
    _label(plate, (705, 743), "GROUNDWATER BASEFLOW", TEAL, size=21)
    _body(plate, (810, 267, 1450, 425),
          "A watershed is all land draining to one outlet. Gravity sets the route; flowing water erodes high ground and deposits sediment where it slows.",
          size=24)
    _finish(plate, content)


def draw_solar_system(plate: SciencePlate, content: Mapping[str, object]) -> None:
    _panel(plate, (105, 230, 1495, 785), PLUM)
    _sun(plate, (175, 486), radius=70)
    plate.text((175, 585), "SUN", size=28, bold=True, fill=GOLD, anchor="mm")
    # A folded distance axis keeps every world legible while retaining AU data.
    plate.arrow((275, 382), (1435, 382), fill=EDGE, width=6, head=18)
    plate.arrow((275, 643), (1435, 643), fill=EDGE, width=6, head=18)
    plate.text((285, 300), "INNER SYSTEM · DISTANCE FROM SUN (AU)",
               size=26, bold=True, fill=INK, anchor="la")
    plate.text((285, 558), "OUTER SYSTEM · DISTANCE FROM SUN (AU)",
               size=26, bold=True, fill=INK, anchor="la")

    inner = (
        (390, "MERCURY", "0.39", 15, EDGE, False),
        (650, "VENUS", "0.72", 24, GOLD, False),
        (920, "EARTH", "1.00", 25, BLUE, False),
        (1265, "MARS", "1.52", 19, CORAL, True),
    )
    for x, name, au, radius, tone, texture in inner:
        plate.draw.line((x, 366, x, 398), fill=INK, width=4)
        _planet(plate, (x, 382), radius, tone, hatch=texture)
        plate.text((x, 427), name, size=23, bold=True, fill=tone, anchor="mm")
        plate.text((x, 460), f"{au} AU", size=23, fill=INK_SOFT, anchor="mm")

    outer = (
        (430, "JUPITER", "5.20", 60, GOLD, False, True),
        (750, "SATURN", "9.58", 51, TEAL, True, True),
        (1060, "URANUS", "19.2", 35, BLUE, False, False),
        (1360, "NEPTUNE", "30.1", 34, PLUM, False, False),
    )
    for x, name, au, radius, tone, rings, stripes in outer:
        plate.draw.line((x, 627, x, 659), fill=INK, width=4)
        _planet(plate, (x, 643), radius, tone, rings=rings, stripes=stripes)
        plate.text((x, 720), name, size=23, bold=True, fill=tone, anchor="mm")
        plate.text((x, 752), f"{au} AU", size=22, fill=INK_SOFT, anchor="mm")
    plate.draw.line((1430, 458, 1430, 528), fill=EDGE, width=4)
    plate.text((1405, 493), "AXIS FOLDS", size=22, bold=True,
               fill=EDGE, anchor="ra")
    _label(plate, (1130, 275), "ROCKY → GIANTS", PLUM, size=22)
    _body(plate, (235, 241, 820, 292),
          "Order and orbital distances are data; icon sizes and gaps are compressed.",
          size=23)
    _finish(plate, content)


def draw_rocks(plate: SciencePlate, content: Mapping[str, object]) -> None:
    _panel(plate, (105, 230, 1495, 785), GOLD)
    # A process network rather than a falsely compulsory circular sequence.
    magma = (230, 535)
    igneous = (510, 345)
    sediment = (820, 325)
    sedimentary = (1120, 355)
    metamorphic = (1050, 650)
    _volcano(plate, (230, 665), scale=.62)
    plate.draw.ellipse((162, 507, 298, 580), fill=CORAL_LIGHT,
                       outline=CORAL, width=5)
    for dx in (-36, 0, 35):
        plate.draw.arc((230+dx-19, 510, 230+dx+19, 566), 15, 160,
                       fill=GOLD, width=4)
    _rock(plate, igneous, size=70, kind="igneous")
    for x, y, radius in ((760, 310, 15), (803, 345, 11), (847, 307, 17),
                         (884, 346, 13)):
        plate.dot((x, y), radius, fill=GOLD_LIGHT, outline=GOLD, width=3)
    _rock(plate, sedimentary, size=72, kind="sedimentary")
    _rock(plate, metamorphic, size=76, kind="metamorphic")

    _arrow(plate, (303, 499), (448, 394), "COOL + CRYSTALLISE", CORAL,
           offset=(0, -35), width=7)
    _arrow(plate, (584, 338), (741, 328), "WEATHER · ERODE", BLUE,
           offset=(0, -32), width=7)
    _arrow(plate, (902, 331), (1043, 348), "", GOLD, width=7)
    _curved_arrow(plate, ((1158, 424), (1172, 520), (1100, 589)), PLUM, width=7)
    _curved_arrow(plate, ((976, 676), (702, 738), (378, 670), (279, 587)), CORAL,
                  width=7)
    _label(plate, (660, 720), "MELT", CORAL, size=22)
    # Cross-links make the many-pathway nature explicit.
    plate.dashed_line((562, 405), (973, 621), fill=PLUM, width=5,
                      dash=18, gap=13)
    plate.dashed_line((1038, 607), (875, 374), fill=BLUE, width=5,
                      dash=18, gap=13)
    # Callouts are drawn above alternate paths, with a leader to the gold edge.
    plate.draw.line((850, 410, 965, 352), fill=GOLD, width=3)
    _label(plate, (850, 430), "COMPACT + CEMENT", GOLD, size=21)
    _label(plate, (1010, 560), "HEAT + PRESSURE", PLUM, size=21)
    _label(plate, (762, 503), "OTHER PATHS", EDGE, size=20)

    _label(plate, (230, 443), "MAGMA", CORAL, size=22)
    _label(plate, (510, 255), "IGNEOUS", CORAL, size=22)
    _label(plate, (820, 260), "SEDIMENT", GOLD, size=22)
    _label(plate, (1120, 263), "SEDIMENTARY", GOLD, size=21)
    _label(plate, (1050, 758), "METAMORPHIC", PLUM, size=21)
    _panel(plate, (1235, 292, 1465, 715), GREEN, radius=20)
    plate.draw.rectangle((1262, 420, 1438, 680), fill=GOLD_LIGHT,
                         outline=EDGE, width=4)
    for y, fill, texture in ((455, GREEN_LIGHT, "organic matter"),
                             (510, GOLD_LIGHT, "topsoil"),
                             (575, _tint(GOLD, .73), "subsoil"),
                             (645, _tint(EDGE, .72), "weathered rock")):
        plate.draw.rectangle((1265, y-24, 1435, y+24), fill=fill)
        plate.text((1350, y), texture, size=20, bold=True, fill=INK, anchor="mm")
    plate.text((1350, 323), "SOIL PROFILE", size=24, bold=True,
               fill=GREEN, anchor="mm")
    plate.text((1350, 356), "mineral + organic matter", size=18, bold=True,
               fill=INK_SOFT, anchor="mm")
    plate.text((1350, 382), "+ air + water", size=18, bold=True,
               fill=INK_SOFT, anchor="mm")
    _finish(plate, content)


def draw_water_cycle(plate: SciencePlate, content: Mapping[str, object]) -> None:
    _panel(plate, (105, 230, 1495, 785), TEAL)
    _sun(plate, (1320, 310), radius=42)
    # Continuous landscape makes reservoirs and transfers explicit.
    plate.draw.polygon(((115, 650), (245, 575), (420, 365), (565, 540),
                        (690, 610), (850, 650), (1010, 673), (1115, 688),
                        (1115, 770), (115, 770)),
                       fill=GOLD_LIGHT, outline=EDGE)
    _mountain(plate, ((225, 583), (420, 365), (585, 552)), snow=True)
    plate.polyline(((425, 397), (470, 495), (560, 562), (685, 620),
                    (850, 652), (1115, 692)), fill=BLUE, width=12)
    plate.draw.rectangle((1115, 622, 1480, 770), fill=hex_rgba(BLUE_LIGHT, 135))
    for y in (650, 698, 744):
        plate.draw.arc((1118, y-18, 1470, y+25), 190, 350, fill=BLUE, width=3)
    _tree(plate, (780, 625), scale=.70)
    _cloud(plate, (720, 330), scale=.72)
    for x, y in ((640, 420), (700, 447), (760, 420), (810, 454)):
        _drop(plate, (x, y), size=13)
    for x in (1215, 1325, 1410):
        plate.arrow((x, 620), (x-30, 452), fill=TEAL, width=7, head=18)
    _label(plate, (1315, 555), "EVAPORATION", TEAL, size=22)
    plate.arrow((812, 539), (850, 429), fill=GREEN, width=7, head=18)
    _label(plate, (1020, 520), "TRANSPIRATION", GREEN, size=21)
    _curved_arrow(plate, ((1150, 421), (1000, 352), (875, 334), (823, 334)), GOLD)
    _label(plate, (1030, 310), "VAPOUR COOLS", GOLD, size=21)
    _label(plate, (720, 265), "CONDENSATION", BLUE, size=22)
    _label(plate, (660, 485), "PRECIPITATION", BLUE, size=21)
    _label(plate, (575, 634), "RUNOFF", BLUE, size=22)

    # Infiltration and groundwater are a slower, visually dashed route.
    plate.draw.polygon(((210, 690), (1050, 700), (1100, 753), (210, 753)),
                       fill=hex_rgba(TEAL_LIGHT, 90), outline=TEAL)
    plate.dashed_line((280, 724), (1088, 724), fill=TEAL, width=6,
                      dash=22, gap=15)
    for x in (520, 650, 880):
        plate.arrow((x, 651), (x+6, 710), fill=TEAL, width=5, head=15)
    _label(plate, (720, 756), "INFILTRATION → GROUNDWATER", TEAL, size=20)
    _body(plate, (135, 250, 470, 350),
          "SUN supplies energy ↑   GRAVITY returns water ↓", size=23)
    _finish(plate, content)


def draw_geology(plate: SciencePlate, content: Mapping[str, object]) -> None:
    _panel(plate, (105, 230, 1495, 785), CORAL)
    # Three boundary geometries share a datum but not a boxed-card treatment.
    separators = (565, 1030)
    for x in separators:
        plate.draw.line((x, 270, x, 742), fill=hex_rgba(EDGE, 105), width=3)

    # Divergent boundary: a cross-section with upwelling and new crust.
    plate.text((330, 275), "DIVERGENT · SIDE VIEW", size=25, bold=True,
               fill=CORAL, anchor="mm")
    plate.draw.rectangle((130, 520, 545, 714), fill=_tint(CORAL, .74),
                         outline=EDGE, width=4)
    plate.draw.polygon(((130, 520), (260, 514), (326, 467), (392, 514),
                        (545, 520), (545, 558), (400, 546), (326, 501),
                        (252, 546), (130, 558)), fill=INK_SOFT, outline=EDGE)
    plate.draw.polygon(((281, 708), (324, 506), (371, 708)),
                       fill=CORAL_LIGHT, outline=CORAL)
    plate.arrow((308, 445), (190, 445), fill=BLUE, width=8, head=22)
    plate.arrow((344, 445), (465, 445), fill=BLUE, width=8, head=22)
    plate.arrow((326, 675), (326, 535), fill=CORAL, width=8, head=22)
    _label(plate, (325, 370), "PLATES SEPARATE", BLUE, size=20)
    _label(plate, (325, 748), "NEW CRUST FORMS", CORAL, size=18)
    for x, y in ((260, 533), (389, 531), (328, 489)):
        _quake(plate, (x, y), size=11)

    # Convergent boundary: oceanic slab subducts beneath continental crust.
    plate.text((797, 275), "CONVERGENT · SIDE VIEW", size=25, bold=True,
               fill=PLUM, anchor="mm")
    plate.draw.polygon(((585, 500), (765, 500), (825, 542), (1005, 573),
                        (1005, 642), (817, 603), (755, 552), (585, 552)),
                       fill=hex_rgba(BLUE_LIGHT, 150), outline=BLUE)
    plate.draw.polygon(((766, 498), (850, 478), (890, 415), (928, 478),
                        (1012, 485), (1012, 710), (862, 710), (806, 570)),
                       fill=GOLD_LIGHT, outline=EDGE)
    plate.draw.polygon(((585, 553), (750, 553), (845, 708), (925, 708),
                        (813, 548), (748, 520)), fill=INK_SOFT,
                       outline=EDGE)
    plate.arrow((665, 455), (752, 455), fill=BLUE, width=8, head=22)
    plate.arrow((968, 455), (888, 455), fill=GOLD, width=8, head=22)
    plate.draw.polygon(((855, 482), (882, 420), (903, 482)),
                       fill=CORAL_LIGHT, outline=CORAL)
    plate.draw.line((882, 420, 882, 378), fill=CORAL, width=7)
    _cloud(plate, (882, 347), scale=.25, tone=PLUM)
    for x, y in ((782, 538), (820, 595), (850, 650)):
        _quake(plate, (x, y), size=12)
    _label(plate, (790, 372), "SUBDUCTION", PLUM, size=20)
    _label(plate, (790, 746), "TRENCH · VOLCANIC ARC", PLUM, size=18)

    # Transform boundary is correctly shown in plan view.
    plate.text((1260, 275), "TRANSFORM · MAP VIEW", size=25, bold=True,
               fill=TEAL, anchor="mm")
    plate.draw.rectangle((1060, 395, 1460, 690), fill=_tint(GREEN, .78),
                         outline=EDGE, width=4)
    plate.draw.polygon(((1060, 395), (1236, 395), (1290, 690), (1060, 690)),
                       fill=GOLD_LIGHT, outline=EDGE)
    plate.draw.polygon(((1236, 395), (1460, 395), (1460, 690), (1290, 690)),
                       fill=GREEN_LIGHT, outline=EDGE)
    plate.draw.line((1236, 395, 1290, 690), fill=CORAL, width=10)
    plate.arrow((1160, 625), (1110, 475), fill=BLUE, width=8, head=22)
    plate.arrow((1365, 463), (1415, 610), fill=GREEN, width=8, head=22)
    for x, y in ((1255, 485), (1270, 565), (1284, 635)):
        _quake(plate, (x, y), size=13)
    _label(plate, (1260, 330), "SLIDE PAST", TEAL, size=20)
    _label(plate, (1260, 746), "LOCK → STRAIN → SLIP", TEAL, size=19)
    _finish(plate, content)


def draw_atmosphere(plate: SciencePlate, content: Mapping[str, object]) -> None:
    _panel(plate, (105, 230, 1495, 785), BLUE)
    # A measured, deliberately broken altitude profile gives useful boundaries.
    x0, x1 = 235, 1075
    bands = (
        (664, 748, GREEN_LIGHT, GREEN, "TROPOSPHERE", "0–12 km", "weather · most air + vapour"),
        (538, 664, TEAL_LIGHT, TEAL, "STRATOSPHERE", "12–50 km", "ozone absorbs UV"),
        (418, 538, BLUE_LIGHT, BLUE, "MESOSPHERE", "50–85 km", "many meteors ablate"),
        (260, 418, PLUM_LIGHT, PLUM, "THERMOSPHERE", "85–500+ km", "very thin air · aurora / low orbits"),
    )
    for y0, y1, pale, tone, name, altitude, detail in bands:
        plate.draw.rectangle((x0, y0, x1, y1), fill=hex_rgba(pale, 145),
                             outline=hex_rgba(tone, 170), width=3)
        plate.text((270, (y0+y1)/2-14), name, size=26, bold=True,
                   fill=tone, anchor="lm")
        plate.text((270, (y0+y1)/2+23), detail, size=22,
                   fill=INK_SOFT, anchor="lm")
        altitude_y = 395 if name == "THERMOSPHERE" else (y0+y1)/2
        plate.text((1035, altitude_y), altitude, size=23, bold=True,
                   fill=INK, anchor="rm")

    # Evidence-bearing objects anchor each band.
    _cloud(plate, (850, 701), scale=.27)
    for x in (825, 850, 875):
        _drop(plate, (x, 739), size=7)
    # Ozone is a patterned absorbing band, not a solid shield.
    for x in range(700, 940, 30):
        plate.draw.ellipse((x-8, 577, x+8, 593), fill=TEAL,
                           outline=PAPER_LIGHT, width=2)
    plate.arrow((850, 258), (850, 558), fill=GOLD, width=5, head=18)
    plate.draw.line((850, 558, 850, 577), fill=GOLD, width=5)
    plate.text((884, 555), "UV absorbed", size=20, bold=True,
               fill=GOLD, anchor="la")
    # Meteor trail and orbiting satellite.
    plate.draw.line((690, 430, 770, 492), fill=CORAL, width=8)
    plate.draw.line((678, 421, 742, 472), fill=GOLD, width=3)
    _quake(plate, (775, 496), size=10, tone=CORAL)
    plate.draw.rectangle((845, 328, 885, 351), fill=INK_SOFT, outline=INK)
    plate.draw.rectangle((792, 318, 840, 361), fill=BLUE_LIGHT, outline=BLUE, width=3)
    plate.draw.rectangle((890, 318, 938, 361), fill=BLUE_LIGHT, outline=BLUE, width=3)
    plate.draw.line((865, 350, 865, 374), fill=INK, width=4)

    # Qualitative temperature trend: direction reverses at layer boundaries.
    gx0, gx1 = 1155, 1435
    plate.arrow((gx0, 748), (gx0, 260), fill=INK, width=5, head=18)
    plate.draw.line((gx0, 748, gx1, 748), fill=INK, width=5)
    profile = ((1370, 748), (1225, 664), (1390, 538), (1210, 418), (1410, 275))
    plate.polyline(profile, fill=CORAL, width=8)
    for point in profile:
        plate.dot(point, 7, fill=CORAL, outline=PAPER_LIGHT, width=2)
    plate.text((1295, 772), "TEMPERATURE TREND →", size=21, bold=True,
               fill=CORAL, anchor="mm")
    plate.text((1292, 287), "rises", size=20, bold=True,
               fill=CORAL, anchor="mm")
    plate.text((270, 395), "Altitude above 85 km compressed", size=19,
               fill=INK_SOFT, anchor="lm")
    _finish(plate, content)


def draw_planets(plate: SciencePlate, content: Mapping[str, object]) -> None:
    _panel(plate, (105, 230, 1495, 785), PLUM)
    # A continuous formation-temperature gradient avoids treating families as
    # unrelated flash cards while preserving their structural distinctions.
    plate.arrow((160, 370), (1440, 370), fill=EDGE, width=7, head=21)
    plate.text((170, 324), "HOTTER DISK · ROCK / METAL", size=24, bold=True,
               fill=CORAL, anchor="la")
    plate.text((1425, 324), "COOLER DISK · ICES AVAILABLE", size=24, bold=True,
               fill=BLUE, anchor="ra")
    plate.draw.line((735, 300, 735, 744), fill=hex_rgba(BLUE, 155), width=4)
    plate.text((735, 277), "SNOW LINE (EARLY DISK, APPROX.)", size=21,
               bold=True, fill=BLUE, anchor="mm")

    # Rocky worlds: solid surfaces, with atmosphere thickness visibly varied.
    rocky = (
        (210, 555, 26, EDGE, "MERCURY", "0.38× Earth"),
        (350, 555, 43, GOLD, "VENUS", "0.95× Earth"),
        (510, 555, 45, BLUE, "EARTH", "1.00× Earth"),
        (650, 555, 31, CORAL, "MARS", "0.53× Earth"),
    )
    for x, y, radius, tone, name, size in rocky:
        _planet(plate, (x, y), radius, tone, hatch=name in {"MERCURY", "MARS"})
        if name == "VENUS":
            plate.draw.ellipse((x-radius-6, y-radius-6, x+radius+6, y+radius+6),
                               outline=GOLD, width=5)
        plate.text((x, 636), name, size=21, bold=True, fill=tone, anchor="mm")
        plate.text((x, 668), size, size=19, fill=INK_SOFT, anchor="mm")
    _label(plate, (430, 725), "TERRESTRIAL · DENSE · SOLID SURFACE", CORAL, size=19)

    # Giant worlds: diagram radii use a second scale, explicitly annotated.
    giants = (
        (850, 540, 83, GOLD, "JUPITER", "11.2× Earth", False, True),
        (1070, 540, 70, TEAL, "SATURN", "9.45× Earth", True, True),
        (1270, 540, 50, BLUE, "URANUS", "4.01× Earth", False, False),
        (1410, 540, 48, PLUM, "NEPTUNE", "3.88× Earth", False, False),
    )
    for x, y, radius, tone, name, size, rings, stripes in giants:
        _planet(plate, (x, y), radius, tone, rings=rings, stripes=stripes)
        plate.text((x, 650), name, size=20, bold=True, fill=tone, anchor="mm")
        plate.text((x, 680), size, size=18, fill=INK_SOFT, anchor="mm")
    _label(plate, (1128, 725), "GIANTS · NO SOLID OUTER SURFACE",
           PLUM, size=18)
    plate.text((1128, 755), "Giant icons use a smaller drawing scale than rocky icons.",
               size=19, bold=True, fill=INK_SOFT, anchor="mm")
    _body(plate, (185, 390, 655, 485),
          "Small bodies preserve early rock and ice. Migration and impacts changed later orbits.", size=22)
    # Small bodies straddle the gap with unmistakable shapes.
    _rock(plate, (700, 432), size=32, kind="igneous")
    plate.draw.ellipse((780, 416, 825, 447), fill=BLUE_LIGHT, outline=BLUE, width=3)
    plate.draw.polygon(((778, 420), (730, 399), (754, 427), (721, 451),
                        (782, 443)), fill=hex_rgba(BLUE_LIGHT, 100), outline=BLUE)
    _finish(plate, content)


def draw_stars(plate: SciencePlate, content: Mapping[str, object]) -> None:
    _panel(plate, (105, 230, 1495, 785), PLUM)
    # Nested physical scales, with real order-of-magnitude labels.
    centers = ((250, 500), (560, 500), (900, 500), (1270, 500))
    for start, end in zip(centers, centers[1:]):
        plate.arrow((start[0]+112, 500), (end[0]-128, 500),
                    fill=PLUM, width=6, head=17)
        plate.text(((start[0]+end[0])/2, 462), "ZOOM OUT", size=18,
                   bold=True, fill=PLUM, anchor="mm")

    # Earth–Sun system.
    _sun(plate, centers[0], radius=49)
    plate.draw.ellipse((centers[0][0]-105, centers[0][1]-60,
                        centers[0][0]+105, centers[0][1]+60),
                       outline=BLUE, width=4)
    _planet(plate, (centers[0][0]+103, centers[0][1]), 10, BLUE)
    _label(plate, (250, 325), "EARTH + SUN", BLUE, size=22)
    plate.text((250, 660), "1 AU = 8 light-min", size=22, bold=True,
               fill=INK, anchor="mm")

    # Solar neighbourhood: one star among neighbours, 4.24 ly nearest.
    for dx, dy, radius, tone in ((0, 0, 22, GOLD), (-72, -61, 10, CORAL),
                                 (65, -72, 12, TEAL), (-83, 57, 8, BLUE),
                                 (85, 52, 9, PLUM), (20, 84, 7, EDGE)):
        x, y = centers[1][0]+dx, centers[1][1]+dy
        plate.dot((x, y), radius, fill=_tint(tone, .35), outline=tone, width=3)
    _label(plate, (560, 325), "NEARBY STARS", TEAL, size=22)
    plate.text((560, 660), "nearest star: 4.24 ly", size=22, bold=True,
               fill=INK, anchor="mm")

    # Milky Way disk, central bulge, and the Sun's approximate radius.
    cx, cy = centers[2]
    for radius, start in ((118, 15), (92, 105), (66, 195), (40, 285)):
        plate.draw.arc((cx-radius*1.35, cy-radius*.67,
                        cx+radius*1.35, cy+radius*.67),
                       start, start+210, fill=PLUM, width=6)
    plate.draw.ellipse((cx-38, cy-25, cx+38, cy+25),
                       fill=GOLD_LIGHT, outline=GOLD, width=3)
    plate.dot((cx+82, cy+14), 8, fill=GOLD, outline=PAPER_LIGHT, width=2)
    plate.text((cx+88, cy+44), "SUN", size=18, bold=True,
               fill=GOLD, anchor="mm")
    _label(plate, (900, 325), "MILKY WAY", PLUM, size=22)
    plate.text((900, 660), "~100,000 light-years wide", size=21, bold=True,
               fill=INK, anchor="mm")

    # Local Group: many galaxy shapes gravitationally associated.
    cx, cy = centers[3]
    for dx, dy, rx, ry, tone in ((0, 0, 76, 28, PLUM), (-82, -70, 53, 20, BLUE),
                                 (77, 68, 60, 22, TEAL), (97, -57, 29, 15, CORAL),
                                 (-94, 65, 25, 14, GOLD), (0, 92, 21, 12, EDGE)):
        plate.draw.ellipse((cx+dx-rx, cy+dy-ry, cx+dx+rx, cy+dy+ry),
                           fill=hex_rgba(_tint(tone, .70), 155),
                           outline=tone, width=4)
        plate.draw.line((cx+dx-rx*.65, cy+dy+ry*.40,
                         cx+dx+rx*.65, cy+dy-ry*.40), fill=tone, width=3)
    _label(plate, (1270, 325), "LOCAL GROUP", CORAL, size=22)
    plate.text((1270, 660), "~10 million light-years across", size=21,
               bold=True, fill=INK, anchor="mm")
    _body(plate, (225, 700, 1320, 770),
          "A star shines by core fusion. A galaxy is a gravity-bound system of stars, gas, dust, and dark matter.", size=24)
    _finish(plate, content)


def draw_oceans(plate: SciencePlate, content: Mapping[str, object]) -> None:
    _panel(plate, (105, 230, 1495, 785), BLUE)
    # Basin section: surface and density circulation occupy different depths.
    plate.draw.polygon(((125, 390), (320, 455), (430, 520), (1120, 520),
                        (1275, 448), (1475, 390), (1475, 755), (125, 755)),
                       fill=hex_rgba(BLUE_LIGHT, 125), outline=BLUE)
    plate.draw.polygon(((125, 390), (320, 455), (430, 520), (430, 755),
                        (125, 755)), fill=GOLD_LIGHT, outline=EDGE)
    plate.draw.polygon(((1120, 520), (1275, 448), (1475, 390), (1475, 755),
                        (1120, 755)), fill=GOLD_LIGHT, outline=EDGE)
    plate.draw.line((430, 520, 1120, 520), fill=BLUE, width=6)
    # Thermocline uses a dashed boundary because it is a gradient, not a wall.
    plate.dashed_line((450, 610), (1100, 610), fill=TEAL, width=5,
                      dash=22, gap=15)
    plate.text((775, 590), "THERMOCLINE",
               size=20, bold=True, fill=TEAL, anchor="mm")

    # Wind stress drives a shallow surface current.
    for x in (500, 650, 800):
        plate.arrow((x, 350), (x+95, 350), fill=GOLD, width=6, head=18)
    _label(plate, (750, 300), "WIND STRESS", GOLD, size=22)
    _curved_arrow(plate, ((475, 550), (660, 535), (850, 538), (1055, 558)), BLUE)
    _label(plate, (770, 490), "SURFACE CURRENT · HEAT", BLUE, size=21)

    # Cooling and salinity can raise density; sinking is regional, not global.
    plate.arrow((1070, 550), (1070, 686), fill=PLUM, width=9, head=23)
    _label(plate, (1165, 615), "COLD + SALTY → DENSER", PLUM, size=19)
    _curved_arrow(plate, ((1035, 704), (820, 730), (595, 720), (490, 674)), PLUM)
    _label(plate, (760, 686), "DEEP RETURN", PLUM, size=21)
    plate.arrow((475, 674), (475, 575), fill=TEAL, width=8, head=21)
    _label(plate, (525, 646), "UPWELLING", TEAL, size=20)

    # Distinct insets separate river input and tidal forcing from circulation.
    plate.polyline(((155, 315), (245, 344), (320, 410), (430, 520)),
                   fill=BLUE, width=10)
    _label(plate, (270, 282), "RIVER INPUT", GREEN, size=19)
    plate.text((270, 322), "freshwater + sediment", size=20, bold=True,
               fill=GREEN, anchor="mm")
    plate.draw.ellipse((1290, 255, 1360, 325), fill=_tint(EDGE, .68),
                       outline=EDGE, width=4)
    plate.draw.ellipse((1180, 323, 1395, 392), outline=CORAL, width=5)
    plate.dot((1288, 358), 30, fill=BLUE_LIGHT, outline=BLUE, width=4)
    plate.arrow((1270, 330), (1314, 316), fill=CORAL, width=5, head=15)
    _label(plate, (1270, 270), "MOON GRAVITY", CORAL, size=19)
    plate.text((1287, 405), "TIDES: PERIODIC", size=19, bold=True,
               fill=CORAL, anchor="mm")
    plate.text((1287, 430), "SEA-LEVEL RESPONSE", size=19, bold=True,
               fill=CORAL, anchor="mm")
    _finish(plate, content)


def draw_environment(plate: SciencePlate, content: Mapping[str, object]) -> None:
    _panel(plate, (105, 230, 1495, 785), GREEN)
    # One connected landscape: causes upstream, interventions at source, and
    # measured responses downstream.
    plate.draw.polygon(((115, 700), (245, 615), (380, 650), (520, 570),
                        (690, 645), (840, 615), (1010, 670), (1160, 640),
                        (1310, 680), (1480, 645), (1480, 770), (115, 770)),
                       fill=GREEN_LIGHT, outline=EDGE)
    plate.polyline(((120, 690), (370, 688), (620, 705), (900, 692),
                    (1180, 710), (1480, 698)), fill=BLUE, width=18)
    # Climate source and solution: stack, energy retrofit, emissions meter.
    plate.draw.rectangle((165, 455, 270, 625), fill=_tint(EDGE, .62),
                         outline=EDGE, width=5)
    plate.draw.rectangle((188, 392, 224, 463), fill=_tint(EDGE, .60),
                         outline=EDGE, width=4)
    for dx, dy, radius in ((0, 0, 23), (31, -18, 30), (62, 3, 26)):
        plate.draw.ellipse((206+dx-radius, 365+dy-radius,
                            206+dx+radius, 365+dy+radius),
                           fill=_tint(PLUM, .70), outline=PLUM, width=3)
    plate.draw.rectangle((315, 500, 445, 623), fill=GOLD_LIGHT,
                         outline=GOLD, width=5)
    for row in range(2):
        for col in range(3):
            plate.draw.rectangle((330+col*34, 520+row*35,
                                  357+col*34, 546+row*35),
                                 fill=BLUE_LIGHT, outline=BLUE, width=2)
    _label(plate, (300, 292), "CLIMATE", CORAL, size=22)
    _arrow(plate, (265, 435), (355, 435), "CUT SOURCE", CORAL,
           offset=(0, -35), width=6)
    plate.text((300, 655), "CO₂e / kWh ↓", size=22, bold=True,
               fill=CORAL, anchor="mm")

    # Water pressure and interception: fertilizer path, buffer, sampler.
    for x in (560, 610, 660, 710):
        plate.draw.line((x, 590, x, 526), fill=GREEN, width=5)
        plate.draw.ellipse((x-20, 505, x+20, 548), fill=GREEN_LIGHT,
                           outline=GREEN, width=3)
    plate.arrow((650, 574), (725, 680), fill=CORAL, width=7, head=20)
    for x in range(744, 802, 18):
        plate.draw.line((x, 667, x, 600), fill=GREEN, width=5)
    plate.draw.rectangle((845, 624, 865, 684), fill=PAPER_LIGHT,
                         outline=BLUE, width=4)
    plate.draw.line((855, 624, 855, 580), fill=BLUE, width=4)
    plate.draw.ellipse((837, 565, 873, 600), fill=BLUE_LIGHT,
                       outline=BLUE, width=4)
    _label(plate, (710, 292), "WATER", BLUE, size=22)
    _arrow(plate, (650, 446), (785, 446), "BUFFER STRIP", GREEN,
           offset=(0, -35), width=6)
    _label(plate, (710, 655), "nitrate (mg/L) ↓", BLUE, size=21)

    # Habitat pressure and response: a road gap becomes a wildlife corridor.
    for x in (1010, 1080, 1150, 1290, 1360, 1430):
        _tree(plate, (x, 625), scale=.48)
    plate.draw.polygon(((1165, 545), (1265, 545), (1305, 750), (1210, 750)),
                       fill=_tint(EDGE, .40), outline=EDGE)
    plate.draw.line((1184, 565, 1276, 565), fill=PAPER_LIGHT, width=5)
    plate.draw.line((1198, 630, 1289, 630), fill=PAPER_LIGHT, width=5)
    plate.draw.arc((1168, 535, 1298, 636), 180, 360, fill=GREEN, width=16)
    plate.draw.arc((1175, 545, 1290, 625), 180, 360, fill=GOLD_LIGHT, width=11)
    # Track marks make monitoring visible without relying on colour.
    for x, y in ((1070, 700), (1110, 685), (1325, 694), (1370, 681)):
        plate.draw.ellipse((x-8, y-5, x+8, y+5), fill=INK_SOFT)
        plate.draw.ellipse((x-3, y-15, x+3, y-7), fill=INK_SOFT)
    _label(plate, (1215, 292), "HABITAT", GREEN, size=22)
    _arrow(plate, (1150, 446), (1280, 446), "RECONNECT", GREEN,
           offset=(0, -35), width=6)
    plate.text((1215, 655), "native crossings / survival ↑", size=21,
               bold=True, fill=GREEN, anchor="mm")

    # Common causal grammar across all three systems.
    for x, label in ((300, "PRESSURE → ACTION → MEASURE"),
                     (710, "PRESSURE → ACTION → MEASURE"),
                     (1215, "PRESSURE → ACTION → MEASURE")):
        plate.text((x, 755), label, size=18, bold=True, fill=INK, anchor="mm")
    _finish(plate, content)


RENDERERS: Dict[str, Renderer] = {
    "earth.0.weather": draw_weather,
    "earth.0.land-water": draw_land_water,
    "earth.1.solar-system": draw_solar_system,
    "earth.1.rocks": draw_rocks,
    "earth.1.water-cycle": draw_water_cycle,
    "earth.2.geology": draw_geology,
    "earth.2.atmosphere": draw_atmosphere,
    "earth.2.planets": draw_planets,
    "earth.2.stars": draw_stars,
    "earth.2.oceans": draw_oceans,
    "earth.2.environment": draw_environment,
}


__all__ = ["RENDERERS"]
