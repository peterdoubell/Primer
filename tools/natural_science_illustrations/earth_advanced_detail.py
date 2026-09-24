"""Bespoke field-guide plates for advanced Earth and space science.

The shared natural-science layouts are useful for inventories, but the later
Earth-and-space lessons are taught through geometry and evidence: ray paths
through an inaccessible planet, calibrated axes, spectra, orbital burns,
reservoir fluxes, and uncertainty envelopes.  These deterministic Pillow
renderers put those relationships in the image instead of decorating prose.

``RENDERERS`` is intentionally keyed by lesson id and importing this module has
no side effects.  The natural-science entry point owns renderer registration.
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
    _science_font,
    hex_rgba,
    mix,
)


Point = Tuple[float, float]
Box = Tuple[float, float, float, float]
Renderer = Callable[[SciencePlate, Mapping[str, object]], None]


def _surface(plate: SciencePlate, box: Box, tone: str = BLUE, *, alpha: int = 226,
             radius: int = 24, width: int = 4) -> None:
    """A quiet plotting field; geometry, not the container, carries meaning."""
    plate.draw.rounded_rectangle(
        box,
        radius=radius,
        fill=hex_rgba(mix(tone, PAPER_LIGHT, .91), alpha),
        outline=hex_rgba(tone, 185),
        width=width,
    )


def _center_text(plate: SciencePlate, box: Box, value: str, *, size: int = 26,
                 bold: bool = False, fill: str = INK, line_gap: int = 6) -> None:
    """Wrap centred copy using the Unicode-aware scientific sans face."""
    size = max(24, size)
    x0, y0, x1, y1 = box
    face = _science_font(value, size, bold=bold)
    lines = []
    line = ""
    for word in value.split():
        candidate = (line + " " + word).strip()
        if not line or plate.draw.textlength(candidate, font=face) <= x1 - x0:
            line = candidate
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    leading = size + line_gap
    block = len(lines) * leading - line_gap
    y = y0 + max(0, (y1 - y0 - block) / 2)
    for row in lines:
        plate.text(((x0 + x1) / 2, y), row, size=size, bold=bold,
                   fill=fill, anchor="ma")
        y += leading


def _tag(plate: SciencePlate, center: Point, value: str, tone: str = BLUE,
         *, size: int = 24, pale: bool = False) -> None:
    size = max(24, size)
    face = _science_font(value, size, bold=True)
    left, top, right, bottom = plate.draw.textbbox(center, value, font=face, anchor="mm")
    fill = mix(tone, PAPER_LIGHT, .76) if pale else tone
    plate.draw.rounded_rectangle(
        (left - 15, top - 8, right + 15, bottom + 8), radius=14,
        fill=hex_rgba(fill, 242),
        outline=hex_rgba(tone, 205) if pale else None,
        width=2,
    )
    plate.text(center, value, size=size, bold=True,
               fill=INK if pale else PAPER_LIGHT, anchor="mm")


def _footer(plate: SciencePlate, content: Mapping[str, object]) -> None:
    value = str(content["footer"])
    plate.draw.rounded_rectangle(
        (165, 805, 1435, 892), radius=24,
        fill=hex_rgba(plate.domain_accent, 34),
        outline=hex_rgba(plate.domain_accent, 125), width=3,
    )
    _center_text(plate, (190, 811, 1410, 885), value, size=24,
                 bold=True, fill=INK, line_gap=4)


def _arrow(plate: SciencePlate, start: Point, end: Point, *, tone: str = BLUE,
           label: str = "", label_at: Point | None = None, width: int = 8,
           head: int = 22, dashed: bool = False) -> None:
    if dashed:
        plate.dashed_line(start, end, fill=tone, width=width, dash=16, gap=10)
        # A short final segment supplies an unambiguous arrow head.
        angle = math.atan2(end[1] - start[1], end[0] - start[0])
        lead = (end[0] - math.cos(angle) * 32, end[1] - math.sin(angle) * 32)
        plate.arrow(lead, end, fill=tone, width=width, head=head)
    else:
        plate.arrow(start, end, fill=tone, width=width, head=head)
    if label:
        _tag(plate, label_at or ((start[0] + end[0]) / 2,
                                 (start[1] + end[1]) / 2 - 24),
             label, tone, size=24)


def _axis(plate: SciencePlate, box: Box, x_range: Tuple[float, float],
          y_range: Tuple[float, float], *, x_ticks: Sequence[Tuple[float, str]],
          y_ticks: Sequence[Tuple[float, str]], x_label: str, y_label: str,
          grid: bool = True) -> Callable[[float, float], Point]:
    """Measured axes whose tick text remains legible in the 800px derivative."""
    x0, y0, x1, y1 = box
    xmin, xmax = x_range
    ymin, ymax = y_range

    def point(x: float, y: float) -> Point:
        return (x0 + (x - xmin) / (xmax - xmin) * (x1 - x0),
                y1 - (y - ymin) / (ymax - ymin) * (y1 - y0))

    for value, label in x_ticks:
        px, _ = point(value, ymin)
        if grid:
            plate.draw.line((px, y0, px, y1), fill=hex_rgba(GRID, 115), width=2)
        plate.draw.line((px, y1, px, y1 + 8), fill=INK, width=3)
        plate.text((px, y1 + 15), label, size=24, fill=INK_SOFT, anchor="ma")
    for value, label in y_ticks:
        _, py = point(xmin, value)
        if grid:
            plate.draw.line((x0, py, x1, py), fill=hex_rgba(GRID, 115), width=2)
        plate.draw.line((x0 - 8, py, x0, py), fill=INK, width=3)
        plate.text((x0 - 14, py), label, size=24, fill=INK_SOFT, anchor="rm")
    plate.arrow((x0, y1), (x1 + 3, y1), fill=INK, width=4, head=15)
    plate.arrow((x0, y1), (x0, y0 - 3), fill=INK, width=4, head=15)
    plate.text(((x0 + x1) / 2, y1 + 57), x_label, size=25, bold=True,
               fill=INK, anchor="mm")
    # A horizontal heading above the ordinate survives the responsive 800px
    # asset better than a long side-running phrase.
    plate.text((x0, y0 - 22), y_label, size=25, bold=True,
               fill=INK, anchor="lb")
    return point


def _star(plate: SciencePlate, center: Point, radius: float, tone: str = GOLD,
          *, rays: bool = True) -> None:
    x, y = center
    if rays:
        for index in range(12):
            angle = index * math.pi / 6
            plate.draw.line((x + math.cos(angle) * radius * 1.15,
                             y + math.sin(angle) * radius * 1.15,
                             x + math.cos(angle) * radius * 1.47,
                             y + math.sin(angle) * radius * 1.47),
                            fill=hex_rgba(tone, 205), width=max(3, int(radius / 10)))
    plate.draw.ellipse((x - radius, y - radius, x + radius, y + radius),
                       fill=hex_rgba(mix(tone, PAPER_LIGHT, .34), 255),
                       outline=tone, width=max(4, int(radius / 9)))
    plate.draw.ellipse((x - radius * .55, y - radius * .55,
                        x + radius * .55, y + radius * .55),
                       fill=hex_rgba(mix(tone, PAPER_LIGHT, .62), 150))


def _planet(plate: SciencePlate, center: Point, radius: float, tone: str = BLUE,
            *, striped: bool = False, ring: bool = False) -> None:
    x, y = center
    if ring:
        plate.draw.ellipse((x - radius * 1.6, y - radius * .45,
                            x + radius * 1.6, y + radius * .45),
                           outline=hex_rgba(GOLD, 230), width=max(4, int(radius / 8)))
    plate.draw.ellipse((x - radius, y - radius, x + radius, y + radius),
                       fill=hex_rgba(mix(tone, PAPER_LIGHT, .45), 255),
                       outline=tone, width=max(4, int(radius / 9)))
    if striped:
        for fraction in (-.45, -.15, .2, .5):
            half = radius * math.sqrt(max(0, 1 - fraction * fraction))
            plate.draw.line((x - half, y + radius * fraction,
                             x + half, y + radius * fraction),
                            fill=hex_rgba(tone, 190), width=max(3, int(radius / 12)))
    else:
        plate.draw.arc((x - radius * .65, y - radius * .35,
                        x + radius * .25, y + radius * .5), 25, 235,
                       fill=hex_rgba(tone, 210), width=max(3, int(radius / 12)))


def _marker(plate: SciencePlate, point: Point, tone: str, shape: str,
            *, size: int = 9) -> None:
    x, y = point
    if shape == "square":
        plate.draw.rectangle((x - size, y - size, x + size, y + size),
                             fill=PAPER_LIGHT, outline=tone, width=4)
    elif shape == "triangle":
        plate.draw.polygon(((x, y - size - 2), (x - size, y + size),
                            (x + size, y + size)), fill=PAPER_LIGHT,
                           outline=tone)
        plate.draw.line((x, y - size - 2, x - size, y + size,
                         x + size, y + size, x, y - size - 2), fill=tone, width=3)
    else:
        plate.dot(point, size, fill=tone, outline=PAPER_LIGHT, width=2)


def _line_key(plate: SciencePlate, at: Point, label: str, tone: str,
              *, dashed: bool = False, shape: str = "circle") -> None:
    x, y = at
    if dashed:
        plate.dashed_line((x, y), (x + 52, y), fill=tone, width=5, dash=10, gap=7)
    else:
        plate.draw.line((x, y, x + 52, y), fill=tone, width=6)
    _marker(plate, (x + 26, y), tone, shape, size=6)
    plate.text((x + 64, y), label, size=24, bold=True, fill=INK, anchor="lm")


def draw_earth_science(plate: SciencePlate, content: Mapping[str, object]) -> None:
    """Connect an Earth cross-section to surface cycling and seismic evidence."""
    cx, cy = 500, 490
    radii = ((260, GREEN_LIGHT, GREEN), (238, GOLD_LIGHT, GOLD),
             (133, CORAL_LIGHT, CORAL), (67, PLUM_LIGHT, PLUM))
    for radius, fill, outline in radii:
        plate.draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius),
                           fill=hex_rgba(fill, 245), outline=outline, width=5)
    # Remove a wedge to make the concentric structure visibly a cutaway.
    wedge = ((cx, cy), (cx + 285, cy - 178), (cx + 285, cy + 178))
    plate.draw.polygon(wedge, fill=hex_rgba(PAPER_LIGHT, 248), outline=EDGE)
    for radius, _, outline in radii:
        angle = .56
        for sign in (-1, 1):
            plate.draw.line((cx, cy,
                             cx + math.cos(angle) * radius,
                             cy + sign * math.sin(angle) * radius),
                            fill=outline, width=5)
    _tag(plate, (252, 284), "crust: 5–70 km", GREEN, size=24)
    _tag(plate, (312, 380), "solid mantle flows", GOLD, size=24)
    _tag(plate, (355, 500), "liquid outer core", CORAL, size=24)
    _tag(plate, (500, 583), "solid inner core", PLUM, size=24)

    # Surface coupling: plate creation, weathering, and subduction.
    plate.draw.line((760, 405, 1445, 405), fill=EDGE, width=7)
    plate.draw.polygon(((820, 405), (1010, 405), (965, 500), (835, 475)),
                       fill=hex_rgba(BLUE_LIGHT, 210), outline=BLUE)
    plate.draw.polygon(((1010, 405), (1370, 405), (1300, 475), (1075, 470)),
                       fill=hex_rgba(GOLD_LIGHT, 205), outline=GOLD)
    _arrow(plate, (925, 440), (1135, 575), tone=CORAL)
    _arrow(plate, (1210, 300), (1080, 390), tone=BLUE, label="erosion + sediment",
           label_at=(1215, 330))
    # Convection is schematic and explicitly marked as slow solid flow.
    plate.draw.arc((940, 470, 1360, 735), 15, 172, fill=GOLD, width=9)
    plate.draw.arc((940, 470, 1360, 735), 195, 350, fill=GOLD, width=9)
    _tag(plate, (1055, 520), "subduction", CORAL, size=24)
    _arrow(plate, (1160, 715), (1010, 655), tone=GOLD, label="heat / slow flow",
           label_at=(1200, 690))
    plate.text((1105, 230), "INTERIOR ↔ SURFACE", size=29, bold=True,
               fill=BLUE, anchor="mm")
    plate.text((1105, 760), "seismic waves reveal layers; rocks preserve time",
               size=25, bold=True, fill=INK_SOFT, anchor="mm")
    _footer(plate, content)


def draw_astronomy(plate: SciencePlate, content: Mapping[str, object]) -> None:
    """Show mass-dependent stellar fates beside the calibrated distance ladder."""
    # A diffuse cloud, not an already formed star: overlapping gas lobes
    # surround denser seed regions without a stellar disc or radial rays.
    for dx, dy, radius in ((-45, 0, 38), (-15, -30, 44), (30, -20, 38),
                           (45, 20, 34), (0, 30, 42), (-32, 28, 30)):
        plate.draw.ellipse((240 + dx - radius, 475 + dy - radius,
                            240 + dx + radius, 475 + dy + radius),
                           fill=hex_rgba(PLUM_LIGHT, 160), outline=PLUM, width=2)
    for dx, dy in ((-25, -8), (10, 20), (30, -15)):
        plate.dot((240 + dx, 475 + dy), 8, fill=GOLD_LIGHT, outline=GOLD, width=2)
    _center_text(plate, (105, 565, 265, 635), "star-forming cloud", size=24,
                 bold=True, fill=INK, line_gap=3)
    _arrow(plate, (320, 430), (500, 315), tone=TEAL, label="lower mass",
           label_at=(405, 340))
    _arrow(plate, (320, 520), (500, 655), tone=CORAL, label="higher mass",
           label_at=(410, 570))

    _star(plate, (570, 310), 43, TEAL)
    _planet(plate, (745, 310), 55, CORAL)
    _arrow(plate, (620, 310), (685, 310), tone=TEAL)
    plate.text((570, 385), "main sequence", size=24, bold=True,
               fill=TEAL, anchor="mm")
    plate.text((745, 385), "red giant", size=24, bold=True,
               fill=CORAL, anchor="mm")
    _arrow(plate, (805, 310), (905, 310), tone=TEAL)
    plate.draw.ellipse((902, 283, 956, 337), fill=PAPER_LIGHT, outline=BLUE, width=6)
    plate.text((930, 385), "white dwarf", size=24, bold=True,
               fill=BLUE, anchor="mm")

    _star(plate, (570, 655), 70, CORAL)
    _center_text(plate, (510, 505, 630, 550), "massive star", size=24,
                 bold=True, fill=CORAL)
    for ray in range(16):
        angle = ray * math.pi / 8
        length = 62 if ray % 2 else 92
        plate.draw.line((760, 655,
                         760 + math.cos(angle) * length,
                         655 + math.sin(angle) * length), fill=GOLD, width=6)
    plate.dot((760, 655), 24, fill=PAPER_LIGHT, outline=GOLD, width=5)
    _arrow(plate, (645, 655), (690, 655), tone=CORAL)
    _center_text(plate, (675, 715, 850, 780), "core-collapse supernova", size=24,
                 bold=True, fill=GOLD)
    _arrow(plate, (835, 635), (930, 590), tone=PLUM)
    _arrow(plate, (835, 675), (930, 720), tone=PLUM)
    plate.dot((968, 575), 22, fill=PLUM_LIGHT, outline=PLUM, width=5)
    plate.draw.ellipse((937, 687, 999, 749), fill=INK, outline=PLUM, width=5)
    plate.text((1020, 575), "neutron star", size=24, bold=True, fill=PLUM, anchor="lm")
    plate.text((1020, 720), "black hole", size=24, bold=True, fill=PLUM, anchor="lm")

    # A logarithmic evidence ladder; overlaps show calibration, not replacement.
    x0, x1, y = 1090, 1450, 470
    plate.arrow((x0, y), (x1, y), fill=INK, width=4, head=15)
    ticks = ((0, "1 pc"), (.33, "1 kpc"), (.66, "1 Mpc"), (1, "1 Gpc"))
    for fraction, label in ticks:
        x = x0 + fraction * (x1 - x0)
        plate.draw.line((x, y - 10, x, y + 10), fill=INK, width=3)
        plate.text((x, y + 22), label, size=24, fill=INK_SOFT, anchor="ma")
    plate.draw.line((1095, 400, 1220, 400), fill=BLUE, width=10)
    plate.draw.line((1160, 355, 1355, 355), fill=TEAL, width=10)
    plate.draw.line((1280, 310, 1440, 310), fill=CORAL, width=10)
    plate.text((1095, 387), "parallax", size=24, bold=True, fill=BLUE, anchor="lb")
    plate.text((1160, 342), "standard candles", size=24, bold=True, fill=TEAL, anchor="lb")
    plate.text((1280, 297), "redshift + model", size=24, bold=True, fill=CORAL, anchor="lb")
    _tag(plate, (1270, 230), "overlap calibrates distance", BLUE, size=24, pale=True)
    _footer(plate, content)


def draw_climate_science(plate: SciencePlate, content: Mapping[str, object]) -> None:
    """Balance shortwave and longwave energy with an explicit forcing step."""
    # Space, atmosphere, and surface are spatial layers rather than boxes.
    plate.draw.rectangle((120, 210, 1480, 410), fill=hex_rgba(BLUE_LIGHT, 72))
    plate.draw.rectangle((120, 410, 1480, 610), fill=hex_rgba(TEAL_LIGHT, 105))
    plate.draw.polygon(((120, 610), (1480, 610), (1480, 790), (120, 790)),
                       fill=hex_rgba(GREEN_LIGHT, 190))
    plate.text((1450, 250), "SPACE", size=26, bold=True, fill=BLUE, anchor="ra")
    plate.text((300, 550), "ATMOSPHERE", size=26, bold=True, fill=TEAL, anchor="mm")
    plate.text((1450, 655), "SURFACE", size=26, bold=True, fill=GREEN, anchor="ra")
    _star(plate, (220, 285), 42, GOLD)

    # Normalised global-mean accounting: the exact 100/30/70 partition is a
    # teaching normalisation, while the spectral forcing mechanism is explicit.
    _arrow(plate, (300, 305), (520, 625), tone=GOLD, label="100 shortwave in",
           label_at=(440, 410), width=10)
    _arrow(plate, (505, 475), (405, 315), tone=GOLD, label="≈30 reflected",
           label_at=(520, 365), dashed=True)
    _tag(plate, (505, 700), "≈70 absorbed", GREEN, size=25)
    for offset in (-28, 0, 28):
        start = (790 + offset, 625)
        end = (790 + offset, 360)
        _arrow(plate, start, end, tone=CORAL, width=6, dashed=True)
    _tag(plate, (825, 700), "thermal infrared", CORAL, size=24)
    # Molecular absorption/emission is drawn as a band with bidirectional rays.
    for x in range(690, 1010, 38):
        plate.dot((x, 500 + (x // 38 % 2) * 16), 8, fill=CORAL_LIGHT,
                  outline=CORAL, width=3)
    _arrow(plate, (850, 490), (850, 320), tone=CORAL, width=6, dashed=True)
    _arrow(plate, (900, 505), (960, 625), tone=CORAL, width=6, dashed=True)
    _tag(plate, (850, 570), "GHGs absorb + emit IR", CORAL, size=24)

    # Synthetic before/after spectral slice illustrates a wavelength-specific
    # deficit; these curves are not measured spectra.
    gx0, gy0, gx1, gy1 = 1090, 300, 1405, 560
    plate.arrow((gx0, gy1), (gx1, gy1), fill=INK, width=4, head=14)
    plate.arrow((gx0, gy1), (gx0, gy0), fill=INK, width=4, head=14)
    plate.text(((gx0 + gx1) / 2, gy1 + 38), "infrared wavelength", size=24,
               bold=True, fill=INK, anchor="mm")
    before = []
    after = []
    for i in range(81):
        f = i / 80
        x = gx0 + f * (gx1 - gx0)
        base = 175 * math.sin(math.pi * f) ** .72
        dip = 72 * math.exp(-((f - .60) / .09) ** 2)
        before.append((x, gy1 - base))
        after.append((x, gy1 - base + dip))
    plate.draw.line(before, fill=BLUE, width=6)
    for start, end in zip(after[::2], after[1::2]):
        plate.draw.line((*start, *end), fill=CORAL, width=6)
    _tag(plate, (1165, 280), "baseline IR", BLUE, size=24)
    _tag(plate, (1325, 335), "just after added CO₂", CORAL, size=24)
    plate.text((1250, 505), "CO₂ band:\nless outgoing IR", size=24, bold=True,
               fill=CORAL, anchor="mm")
    plate.text((1240, 735), "warming restores outgoing ≈ incoming",
               size=25, bold=True, fill=INK, anchor="mm")
    _footer(plate, content)


def draw_ecology_earth(plate: SciencePlate, content: Mapping[str, object]) -> None:
    """Place schematic biome ranges on temperature–precipitation axes."""
    plot = (250, 245, 1395, 650)
    p = _axis(
        plate, plot, (-15, 30), (0, 400),
        x_ticks=((-15, "−15"), (0, "0"), (15, "15"), (30, "30")),
        y_ticks=((0, "0"), (100, "100"), (200, "200"), (300, "300"), (400, "400")),
        x_label="mean annual temperature (°C)",
        y_label="annual precipitation (cm)",
    )
    regions = (
        ("TUNDRA", [(-15, 0), (3, 0), (5, 75), (-10, 100)], BLUE, "///"),
        ("BOREAL FOREST", [(-5, 55), (8, 55), (12, 180), (0, 220), (-8, 145)], TEAL, "||"),
        ("TEMPERATE FOREST", [(5, 75), (22, 85), (25, 250), (10, 285), (2, 190)], GREEN, "...") ,
        ("GRASSLAND", [(5, 20), (25, 20), (27, 110), (10, 135)], GOLD, "---"),
        ("DESERT", [(-2, 0), (30, 0), (30, 65), (12, 55)], CORAL, "xx"),
        ("TROPICAL FOREST", [(20, 140), (30, 125), (30, 400), (22, 400)], PLUM, "oo"),
    )
    for name, values, tone, pattern in regions:
        points = [p(x, y) for x, y in values]
        plate.draw.polygon(points, fill=hex_rgba(mix(tone, PAPER_LIGHT, .58), 205),
                           outline=tone)
        plate.draw.line(points + [points[0]], fill=tone, width=5, joint="curve")
    # Labels must be painted after every region, not hidden by later polygons.
    for name, values, tone, pattern in regions:
        points = [p(x, y) for x, y in values]
        # Explicit names distinguish regions without relying on colour.
        xs = [point[0] for point in points]
        ys = [point[1] for point in points]
        _center_text(plate, (min(xs) + 4, min(ys) + 8, max(xs) - 4, max(ys) - 8),
                     name, size=24, bold=True, fill=INK)
    plate.text((820, 752),
               "boundaries overlap: soils, fire, seasonality and history shift the realised biome",
               size=25, bold=True, fill=INK_SOFT, anchor="mm")
    _footer(plate, content)


def _transfer_geometry(earth: Point, periapsis: float, apoapsis: float):
    """Ellipse with Earth at its left focus, tangent to the inner orbit."""
    a = (periapsis + apoapsis) / 2
    c = (apoapsis - periapsis) / 2
    b = math.sqrt(a * a - c * c)
    cx, cy = earth[0] + c, earth[1]
    return (cx - a, cy - b, cx + a, cy + b), (cx - a, cy), (cx + a, cy)


def draw_space_exploration(plate: SciencePlate, content: Mapping[str, object]) -> None:
    """Explain orbit and a two-burn transfer through trajectories and velocity."""
    earth = (420, 500)
    _planet(plate, earth, 92, BLUE)
    # Circular low orbit and a high transfer ellipse share one focus (Earth).
    plate.draw.ellipse((255, 335, 585, 665), outline=TEAL, width=6)
    transfer, craft1, craft2 = _transfer_geometry(earth, 165, 515)
    plate.draw.ellipse(transfer, outline=CORAL, width=7)
    plate.draw.polygon(((craft1[0] - 18, craft1[1] - 12),
                        (craft1[0], craft1[1] + 22),
                        (craft1[0] + 18, craft1[1] - 12)), fill=TEAL)
    plate.draw.polygon(((craft2[0] - 18, craft2[1] + 12),
                        (craft2[0], craft2[1] - 22),
                        (craft2[0] + 18, craft2[1] + 12)), fill=CORAL)
    _arrow(plate, (craft1[0], 525), (craft1[0], 605), tone=CORAL,
           label="1: raise far side", label_at=(280, 655))
    _arrow(plate, (craft2[0], 475), (craft2[0], 395), tone=PLUM,
           label="2: circularise", label_at=(1065, 355))
    # Velocity and gravity vectors at one point explain free fall.
    _arrow(plate, (420, 335), (285, 335), tone=TEAL, label="sideways velocity",
           label_at=(440, 285))
    _arrow(plate, (420, 335), (420, 390), tone=BLUE, label="gravity inward",
           label_at=(620, 405))
    _center_text(plate, (1080, 220, 1435, 295), "ORBIT = CONTINUAL FREE FALL",
                 size=28, bold=True, fill=BLUE)

    # A mission sequence, not an invented additive speed/climb budget.
    plate.text((1250, 475), "BURN · COAST · BURN", size=27, bold=True,
               fill=INK, anchor="mm")
    _center_text(plate, (1080, 515, 1435, 665),
                 "Two prograde burns change the orbit. Between burns, gravity bends the coasting path. Final circular orbit is not shown.",
                 size=25, fill=INK_SOFT)
    _line_key(plate, (1115, 705), "coast under gravity", CORAL)
    _footer(plate, content)


def draw_geophysics(plate: SciencePlate, content: Mapping[str, object]) -> None:
    """Pair schematic ray paths through Earth with a synthetic seismogram."""
    cx, cy, radius = 465, 485, 255
    plate.draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius),
                       fill=hex_rgba(GOLD_LIGHT, 205), outline=EDGE, width=6)
    plate.draw.ellipse((cx - 138, cy - 138, cx + 138, cy + 138),
                       fill=hex_rgba(CORAL_LIGHT, 220), outline=CORAL, width=6)
    plate.draw.ellipse((cx - 68, cy - 68, cx + 68, cy + 68),
                       fill=hex_rgba(PLUM_LIGHT, 230), outline=PLUM, width=5)
    source = (245, 355)
    plate.dot(source, 13, fill=CORAL, outline=PAPER_LIGHT, width=3)
    _tag(plate, (215, 300), "earthquake", CORAL, size=24)
    # P-wave paths refract through the liquid outer core; the changing slope is
    # intentionally visible. S paths stop at the core–mantle boundary.
    p_paths = (
        (source, (390, 425), (465, 485), (560, 445), (690, 350)),
        (source, (360, 555), (465, 605), (585, 550), (710, 500)),
    )
    for path in p_paths:
        plate.draw.line(path, fill=BLUE, width=7, joint="curve")
        _marker(plate, path[-1], BLUE, "circle", size=8)
    s_paths = (
        (source, (cx + 138 * math.cos(math.radians(205)),
                  cy + 138 * math.sin(math.radians(205)))),
        (source, (310, 490),
         (cx + 138 * math.cos(math.radians(155)),
          cy + 138 * math.sin(math.radians(155)))),
    )
    for path in s_paths:
        plate.draw.line(path, fill=CORAL, width=7, joint="curve")
        x, y = path[-1]
        plate.draw.line((x - 10, y - 10, x + 10, y + 10), fill=CORAL, width=5)
        plate.draw.line((x - 10, y + 10, x + 10, y - 10), fill=CORAL, width=5)
    _line_key(plate, (190, 770), "P: solid / liquid", BLUE)
    _line_key(plate, (525, 770), "S: solid only", CORAL, shape="square")
    plate.text((465, 660), "liquid outer core", size=25, bold=True,
               fill=CORAL, anchor="mm")

    # A true time axis separates the earlier P and later S arrival.
    plot = (860, 300, 1430, 625)
    p = _axis(plate, plot, (0, 80), (-1, 1),
              x_ticks=((0, "0"), (20, "20"), (40, "40"), (60, "60"), (80, "80")),
              y_ticks=((-1, "−"), (0, "0"), (1, "+")),
              x_label="time after earthquake (s)", y_label="ground motion",
              grid=True)
    signal = []
    for t in range(161):
        seconds = t / 2
        if seconds < 18:
            value = 0
        elif seconds < 39:
            value = .24 * math.sin((seconds - 18) * 2.4) * math.exp(-(seconds - 18) / 14)
        else:
            value = .75 * math.sin((seconds - 39) * 1.9) * math.exp(-(seconds - 39) / 23)
        signal.append(p(seconds, value))
    plate.draw.line(signal, fill=INK, width=5, joint="curve")
    for seconds, label, tone in ((18, "P arrives", BLUE), (39, "S arrives", CORAL)):
        x, _ = p(seconds, 0)
        plate.dashed_line((x, plot[1]), (x, plot[3]), fill=tone, width=4,
                          dash=10, gap=8)
        _tag(plate, (x, 225), label, tone, size=24)
    plate.text((1145, 735), "arrival gap grows with source–station distance",
               size=24, bold=True, fill=INK_SOFT, anchor="mm")
    _footer(plate, content)


def draw_astrophysics(plate: SciencePlate, content: Mapping[str, object]) -> None:
    """Render schematic stellar samples with a log luminosity axis and radius guides."""
    plot = (260, 245, 1415, 650)
    p = _axis(plate, plot, (30000, 2500), (-4, 6),
              x_ticks=((30000, "30,000"), (10000, "10,000"),
                       (5800, "5,800"), (2500, "2,500")),
              y_ticks=((-4, "10⁻⁴"), (-2, "10⁻²"), (0, "1"),
                       (2, "10²"), (4, "10⁴"), (6, "10⁶")),
              x_label="surface temperature (K)  — hotter to cooler →",
              y_label="luminosity (Sun = 1; log)")
    # Constant-radius guides follow L ∝ R²T⁴. Lines are dashed so they cannot be
    # mistaken for evolutionary tracks or observed sequences.
    for radius, tone in ((.01, BLUE), (1, TEAL), (100, CORAL)):
        points = []
        for index in range(101):
            t = 30000 - index * 275
            log_l = 2 * math.log10(radius) + 4 * math.log10(t / 5772)
            if -4 <= log_l <= 6:
                points.append(p(t, log_l))
        for a, b in zip(points[::2], points[1::2]):
            plate.draw.line((*a, *b), fill=hex_rgba(tone, 145), width=3)
        if points:
            x, y = points[len(points) // 2]
            plate.text((x + 8, y - 8), f"R={radius:g} R⊙", size=24,
                       bold=True, fill=tone, anchor="lm")
    main = ((28000, 5.2), (20000, 4.1), (10000, 1.7), (7500, .7),
            (5800, 0), (4500, -.8), (3200, -2.4))
    plate.draw.line([p(*value) for value in main], fill=GOLD, width=13,
                    joint="curve")
    for value in main:
        _marker(plate, p(*value), GOLD, "circle", size=8)
    giants = ((5200, 2.4), (4300, 3.1), (3500, 3.8), (3000, 4.8))
    for value in giants:
        _marker(plate, p(*value), CORAL, "triangle", size=12)
    dwarfs = ((25000, -1.3), (16000, -2.0), (10000, -2.8), (7000, -3.3))
    for value in dwarfs:
        _marker(plate, p(*value), BLUE, "square", size=10)
    _tag(plate, p(16500, 3.15), "main sequence", GOLD, size=24)
    _tag(plate, p(4100, 4.25), "giants", CORAL, size=24)
    _tag(plate, p(15500, -3.1), "white dwarfs", BLUE, size=24)
    plate.text((840, 755), "position constrains radius and evolutionary state—not age by itself",
               size=25, bold=True, fill=INK_SOFT, anchor="mm")
    _footer(plate, content)


def draw_planetary(plate: SciencePlate, content: Mapping[str, object]) -> None:
    """Track radial disk chemistry into accretion and a differentiated world."""
    _star(plate, (205, 455), 58, GOLD)
    # Log radial ruler and a disk whose vertical thickness is schematic.
    x0, x1, y = 310, 995, 450
    plate.draw.polygon(((x0, y - 55), (x1, y - 15), (x1, y + 15), (x0, y + 55)),
                       fill=hex_rgba(GOLD_LIGHT, 135), outline=GOLD)
    positions = ((.1, "0.1 AU"), (1, "1 AU"), (3, "3 AU"), (10, "10 AU"), (30, "30 AU"))
    for distance, label in positions:
        fraction = math.log10(distance / .1) / math.log10(300)
        x = x0 + fraction * (x1 - x0)
        plate.draw.line((x, y + 65, x, y + 86), fill=INK, width=3)
        plate.text((x, y + 96), label, size=24, fill=INK_SOFT, anchor="ma")
    snow_x = x0 + math.log10(30) / math.log10(300) * (x1 - x0)
    plate.dashed_line((snow_x, 270), (snow_x, 625), fill=BLUE, width=5,
                      dash=13, gap=9)
    _tag(plate, (snow_x, 245), "water snow line", BLUE, size=24)
    for x in range(345, int(snow_x), 56):
        plate.draw.polygon(((x, y - 12), (x - 9, y + 9), (x + 10, y + 8)),
                           fill=CORAL, outline=INK)
    for x in range(int(snow_x) + 28, 965, 56):
        plate.dot((x, y), 11, fill=BLUE_LIGHT, outline=BLUE, width=3)
        plate.draw.line((x - 7, y, x + 7, y), fill=PAPER_LIGHT, width=2)
    plate.text((420, 350), "rock + metal solids", size=25, bold=True,
               fill=CORAL, anchor="mm")
    _tag(plate, (800, 350), "ices add solid mass", BLUE, size=24)

    # Accretion is represented by converging trajectories, followed by a cutaway.
    for start in ((1050, 315), (1030, 425), (1045, 590)):
        _arrow(plate, start, (1160, 470), tone=PLUM, width=5, head=16)
        plate.dot(start, 12, fill=PLUM_LIGHT, outline=PLUM, width=3)
    _tag(plate, (1080, 680), "collision + gravity", PLUM, size=24)
    cx, cy, radius = 1320, 470, 128
    plate.draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius),
                       fill=hex_rgba(CORAL_LIGHT, 235), outline=CORAL, width=6)
    plate.draw.pieslice((cx - radius, cy - radius, cx + radius, cy + radius),
                        -62, 62, fill=hex_rgba(PAPER_LIGHT, 255), outline=CORAL)
    for r, fill, tone in ((105, GOLD_LIGHT, GOLD), (70, CORAL_LIGHT, CORAL),
                          (36, PLUM_LIGHT, PLUM)):
        plate.draw.pieslice((cx - r, cy - r, cx + r, cy + r),
                            -62, 62, fill=hex_rgba(fill, 245), outline=tone, width=4)
    _tag(plate, (1320, 285), "differentiation", CORAL, size=24)
    plate.text((1320, 640), "dense metal sinks\nwhen melting permits flow",
               size=24, bold=True, fill=INK, anchor="mm")
    plate.text((800, 745), "distance sets starting materials; mass and history drive divergence",
               size=25, bold=True, fill=INK_SOFT, anchor="mm")
    _footer(plate, content)


def draw_climatology(plate: SciencePlate, content: Mapping[str, object]) -> None:
    """Expose a carbon-budget read-off and the uncertainty around the response."""
    plot = (270, 255, 1125, 650)
    p = _axis(plate, plot, (0, 4000), (0, 3),
              x_ticks=((0, "0"), (1000, "1,000"), (2000, "2,000"),
                       (3000, "3,000"), (4000, "4,000")),
              y_ticks=((0, "0"), (1, "1"), (2, "2"), (3, "3")),
              x_label="additional cumulative CO₂ from one baseline (GtCO₂)",
              y_label="CO₂-caused warming (°C)")
    # IPCC AR6 likely TCRE range is represented as a broad slope envelope;
    # values are teaching-scale, not a live estimate of the remaining budget.
    upper = [p(x, .00063 * x) for x in range(0, 4001, 100)]
    lower = [p(x, .00027 * x) for x in range(4000, -1, -100)]
    plate.draw.polygon(upper + lower, fill=hex_rgba(BLUE_LIGHT, 125))
    for slope, tone, width in ((.00027, BLUE, 3), (.00063, BLUE, 3),
                               (.00045, CORAL, 8)):
        points = [p(x, slope * x) for x in range(0, 4001, 80)
                  if slope * x <= 3]
        plate.draw.line(points, fill=tone, width=width)
    _tag(plate, p(3000, 1.35), "central response", CORAL, size=24)
    plate.text((680, 300), "likely response range", size=24, bold=True,
               fill=BLUE, anchor="mm")
    # Demonstrate reading a finite budget from a chosen warming increment.
    target = 1.5
    budget = target / .00045
    tx, ty = p(budget, target)
    plate.dashed_line((plot[0], ty), (tx, ty), fill=GOLD, width=5, dash=12, gap=8)
    plate.dashed_line((tx, ty), (tx, plot[3]), fill=GOLD, width=5, dash=12, gap=8)
    _tag(plate, (1310, 320), "example read-off", GOLD, size=24)
    plate.text((1310, 390), "choose ΔT", size=25, bold=True, fill=INK, anchor="mm")
    _arrow(plate, (1310, 420), (1310, 485), tone=GOLD, width=6)
    plate.text((1310, 520), "intersect response", size=25, bold=True, fill=INK, anchor="mm")
    _arrow(plate, (1310, 550), (1310, 615), tone=GOLD, width=6)
    plate.text((1310, 650), "read finite emissions", size=25, bold=True, fill=INK, anchor="mm")
    plate.text((700, 758),
               "band = response uncertainty; scenarios and non-CO₂ forcing add further uncertainty",
               size=24, bold=True, fill=INK_SOFT, anchor="mm")
    _footer(plate, content)


def draw_oceanatmos(plate: SciencePlate, content: Mapping[str, object]) -> None:
    """Draw Northern-Hemisphere coastal upwelling as a signed vector process."""
    # Coast and vertical ocean section.
    coast_x = 1210
    plate.draw.polygon(((coast_x, 350), (1480, 350), (1480, 780),
                        (coast_x, 780)), fill=hex_rgba(GOLD_LIGHT, 175), outline=EDGE)
    plate.draw.rectangle((130, 470, coast_x, 780), fill=hex_rgba(BLUE_LIGHT, 145))
    plate.draw.line((130, 470, coast_x, 470), fill=BLUE, width=7)
    plate.text((1340, 390), "COAST", size=27, bold=True, fill=GOLD, anchor="mm")
    plate.text((255, 710), "cold, nutrient-rich deep water", size=26, bold=True,
               fill=BLUE, anchor="lm")
    # Along-coast wind is represented as a plan-view arrow, while the cross-
    # section shows offshore Ekman transport and upwelling.
    _arrow(plate, (1310, 485), (1310, 675), tone=TEAL, label="wind along coast",
           label_at=(1390, 585))
    _arrow(plate, (1130, 430), (690, 430), tone=PLUM, label="surface Ekman transport",
           label_at=(900, 380), width=10)
    _arrow(plate, (1120, 710), (1120, 500), tone=BLUE, width=11)
    # Thermocline rises toward the coast; stippling identifies the cold side.
    thermocline = ((160, 650), (420, 640), (700, 610), (970, 565), (1180, 520))
    plate.draw.line(thermocline, fill=CORAL, width=7)
    for x in range(190, 1120, 55):
        y = 655 - max(0, x - 350) * .12
        plate.dot((x, y + 45), 4, fill=BLUE, outline=BLUE, width=1)
    _tag(plate, (510, 665), "thermocline shoals", CORAL, size=24)
    _tag(plate, (960, 620), "upwelling", BLUE, size=24)

    # Top-view vector inset makes the hemispheric sign explicit.
    _surface(plate, (145, 220, 600, 385), TEAL, alpha=238)
    _center_text(plate, (160, 225, 585, 275),
                 "NORTHERN HEMISPHERE — IDEAL OPEN OCEAN",
                 size=24, bold=True, fill=INK, line_gap=3)
    _arrow(plate, (255, 275), (255, 345), tone=TEAL, width=7)
    _arrow(plate, (470, 315), (285, 315), tone=PLUM, width=7)
    plate.text((210, 310), "wind", size=24, bold=True, fill=TEAL, anchor="rm")
    plate.text((375, 350), "transport 90° right", size=24, bold=True,
               fill=PLUM, anchor="mm")
    plate.text((800, 745),
               "ideal direction reverses in the Southern Hemisphere; coasts and stratification modify flow",
               size=24, bold=True, fill=INK_SOFT, anchor="mm")
    _footer(plate, content)


def draw_cosmology(plate: SciencePlate, content: Mapping[str, object]) -> None:
    """Use a logarithmic time axis so early-universe intervals are not erased."""
    x0, x1, axis_y = 185, 1430, 665
    # Map log10 years from ~seconds to the present. Pre-year events use a
    # negative log-year coordinate while labels carry the readable chronology.
    def tx(log_years: float) -> float:
        return x0 + (log_years + 8) / (10.14 + 8) * (x1 - x0)

    # Three local patches, not rays emerging from an explosion centre.
    # Uniformly increasing separation has no privileged central galaxy.
    for cx, spacing in ((350, 25), (780, 50), (1220, 80)):
        for row in (-1, 0, 1):
            for column in (-1, 0, 1):
                plate.dot((cx + column * spacing, 455 + row * spacing),
                          8, fill=PLUM, outline=PLUM, width=2)
    _arrow(plate, (440, 455), (665, 455), tone=BLUE)
    _arrow(plate, (890, 455), (1090, 455), tone=BLUE)
    plate.text((780, 560), "schematic patches: separation grows everywhere", size=24,
               bold=True, fill=INK_SOFT, anchor="mm")
    plate.arrow((x0, axis_y), (x1, axis_y), fill=INK, width=5, head=17)
    events = (
        (-7.5, "hot early state", CORAL, (205, 720)),
        (-5.3, "nuclei ~3 min", GOLD, (375, 720)),
        (5.58, "CMB released 380,000 y", TEAL, (1000, 720)),
        (8.0, "first stars ~100 My", PLUM, (1190, 720)),
        (9.75, "acceleration late universe", BLUE, (1260, 585)),
        (10.14, "now 13.8 Gy", GREEN, (1415, 720)),
    )
    for index, (value, label, tone, label_center) in enumerate(events):
        x = tx(value)
        plate.draw.line((x, axis_y - 12, x, axis_y + 14), fill=tone, width=5)
        _marker(plate, (x, axis_y), tone,
                ("circle", "triangle", "square")[index % 3], size=9)
        lx, ly = label_center
        end_y = ly - 27 if ly > axis_y else ly + 27
        plate.draw.line((x, axis_y + (14 if ly > axis_y else -14), lx, end_y),
                        fill=hex_rgba(tone, 165), width=3)
        _center_text(plate, (lx - 82, ly - 36, lx + 82, ly + 36), label,
                     size=24, bold=True, fill=INK, line_gap=3)
    # Evidence bands link distinct observations to distinct epochs.
    _tag(plate, (370, 235), "abundances: H / He / Li", GOLD, size=24)
    _tag(plate, (830, 300), "CMB: near-perfect blackbody + anisotropy", TEAL, size=24)
    _tag(plate, (1225, 235), "redshift + structure growth", PLUM, size=24)
    plate.text((800, 600), "LOGARITHMIC COSMIC TIME →", size=28, bold=True,
               fill=INK, anchor="mm")
    _footer(plate, content)


def draw_astrobiology(plate: SciencePlate, content: Mapping[str, object]) -> None:
    """Carry a transit signal through spectral measurement and model testing."""
    # Transit geometry.
    _star(plate, (245, 405), 100, GOLD)
    _planet(plate, (245, 405), 31, BLUE)
    plate.draw.ellipse((209, 369, 281, 441), outline=TEAL, width=9)
    _arrow(plate, (365, 405), (500, 405), tone=TEAL, label="transit light",
           label_at=(430, 350))
    plate.text((245, 575), "planet atmosphere filters\na tiny fraction of starlight",
               size=25, bold=True, fill=INK, anchor="mm")

    # Synthetic transmission spectrum with uncertainty bars. The label is
    # explicit: features are candidates, not detections of life.
    plot = (565, 300, 1060, 625)
    p = _axis(plate, plot, (.5, 5), (0, 1),
              x_ticks=((.5, "0.5"), (1, "1"), (2, "2"), (3, "3"), (4, "4"), (5, "5")),
              y_ticks=((0, "0"), (.5, ".5"), (1, "1")),
              x_label="wavelength (µm)", y_label="relative absorption")
    features = ((.76, .32, "O₂?"), (1.4, .60, "H₂O?"),
                (3.3, .48, "CH₄?"), (4.3, .72, "CO₂?"))
    points = []
    for i in range(24):
        wavelength = .55 + i * .185
        value = .11
        for centre, height, _ in features:
            value += height * math.exp(-((wavelength - centre) / .16) ** 2)
        value = min(.94, value)
        point = p(wavelength, value)
        points.append(point)
        uncertainty = 18 + (i % 3) * 5
        plate.draw.line((point[0], point[1] - uncertainty,
                         point[0], point[1] + uncertainty), fill=INK_SOFT, width=3)
        _marker(plate, point, BLUE, "square", size=6)
    plate.draw.line(points, fill=hex_rgba(BLUE, 145), width=3)
    for centre, height, label in features:
        x, y = p(centre, min(.94, .11 + height))
        plate.text((x, max(plot[1] + 8, y - 28)), label, size=24,
                   bold=True, fill=PLUM, anchor="mm")
    plate.text((815, 220), "SIMULATED CANDIDATE SPECTRUM", size=25,
               bold=True, fill=BLUE, anchor="mm")

    # Competing hypotheses cross the evidence boundary to the right.
    plate.draw.line((1125, 245, 1125, 720), fill=EDGE, width=4)
    plate.text((1290, 260), "MODEL COMPARISON", size=27, bold=True,
               fill=INK, anchor="mm")
    for y, label, tone, pattern in (
        (355, "stellar activity", GOLD, "△"),
        (455, "abiotic chemistry", CORAL, "□"),
        (555, "biology + context", GREEN, "●"),
    ):
        plate.text((1180, y), pattern, size=34, bold=True, fill=tone, anchor="mm")
        plate.text((1220, y), label, size=25, bold=True, fill=INK, anchor="lm")
        plate.draw.line((1165, y + 34, 1415, y + 34), fill=hex_rgba(tone, 115), width=3)
    _tag(plate, (1290, 660), "repeat + falsify", PLUM, size=24)
    plate.text((800, 760), "no single gas proves life; context and false-positive tests carry the inference",
               size=24, bold=True, fill=INK_SOFT, anchor="mm")
    _footer(plate, content)


def draw_earth_systems(plate: SciencePlate, content: Mapping[str, object]) -> None:
    """Separate material fluxes from radiative forcing in a coupled system."""
    centers = {
        "atm": (800, 315), "land": (430, 560), "ocean": (1110, 565),
        "ice": (250, 335), "human": (1350, 325),
    }
    # Reservoir silhouettes differ in shape and hatch, so hue is redundant.
    plate.draw.ellipse((665, 240, 935, 390), fill=hex_rgba(BLUE_LIGHT, 190),
                       outline=BLUE, width=6)
    plate.text(centers["atm"], "ATMOSPHERE\nheat + gases", size=27,
               bold=True, fill=INK, anchor="mm")
    plate.draw.polygon(((275, 625), (430, 430), (585, 625)),
                       fill=hex_rgba(GREEN_LIGHT, 215), outline=GREEN)
    for x in range(325, 550, 45):
        plate.draw.line((x, 600, x + 45, 540), fill=hex_rgba(GREEN, 125), width=3)
    plate.text((430, 650), "LAND + BIOSPHERE", size=25, bold=True,
               fill=GREEN, anchor="mm")
    plate.draw.ellipse((955, 455, 1265, 675), fill=hex_rgba(TEAL_LIGHT, 210),
                       outline=TEAL, width=6)
    for y in (495, 635):
        plate.draw.arc((985, y - 30, 1235, y + 30), 10, 170, fill=TEAL, width=4)
    plate.text((1110, 565), "OCEAN\nheat + carbon", size=26, bold=True,
               fill=INK, anchor="mm")
    plate.draw.polygon(((165, 390), (250, 255), (335, 390)),
                       fill=hex_rgba(BLUE_LIGHT, 235), outline=BLUE)
    plate.text((250, 420), "ICE / ALBEDO", size=24, bold=True,
               fill=BLUE, anchor="mm")
    plate.draw.rectangle((1285, 265, 1415, 385), fill=hex_rgba(CORAL_LIGHT, 215),
                         outline=CORAL, width=5)
    for x in (1310, 1350, 1390):
        plate.draw.line((x, 265, x, 225), fill=CORAL, width=7)
    plate.text((1350, 425), "HUMAN SYSTEM", size=24, bold=True,
               fill=CORAL, anchor="mm")

    # Solid bidirectional arrows = material; dashed one-way = energy/forcing.
    plate.double_arrow((600, 475), (690, 365), fill=GREEN, width=7)
    plate.double_arrow((930, 375), (1035, 475), fill=TEAL, width=7)
    plate.arrow((585, 585), (955, 585), fill=PLUM, width=7)
    _tag(plate, (635, 425), "CO₂ + H₂O", GREEN, size=24)
    _tag(plate, (985, 425), "heat + CO₂", TEAL, size=24)
    _tag(plate, (770, 620), "runoff + carbon", PLUM, size=24)
    _arrow(plate, (1350, 455), (930, 345), tone=CORAL, label="emissions / forcing",
           label_at=(1125, 365), dashed=True)
    _arrow(plate, (255, 245), (255, 205), tone=GOLD, dashed=True, width=6)
    _arrow(plate, (295, 205), (295, 245), tone=GOLD, dashed=True, width=6)
    plate.text((355, 220), "reflected / absorbed sunlight", size=24,
               bold=True, fill=GOLD, anchor="lm")
    # Feedback loop: warming -> ice loss -> lower albedo -> warming.
    plate.draw.arc((185, 475, 610, 755), 185, 350, fill=BLUE, width=7)
    _arrow(plate, (555, 690), (405, 715), tone=BLUE, label="less ice → lower albedo",
           label_at=(350, 735), width=6)
    _line_key(plate, (1010, 715), "exchanges", TEAL)
    _line_key(plate, (1010, 770), "energy / forcing", GOLD, dashed=True)
    _footer(plate, content)


def draw_frontier(plate: SciencePlate, content: Mapping[str, object]) -> None:
    """Replace a frontier matrix with three calibrated evidence signatures."""
    # The three plots share a baseline rather than sitting in decorative cards.
    columns = ((125, 505), (575, 955), (1025, 1475))
    headings = ("GRAVITATIONAL WAVES", "DARK MATTER", "DARK ENERGY")
    tones = (PLUM, BLUE, CORAL)
    for (x0, x1), heading, tone in zip(columns, headings, tones):
        plate.text(((x0 + x1) / 2, 230), heading, size=26, bold=True,
                   fill=tone, anchor="mm")
        plate.draw.line((x0, 260, x1, 260), fill=hex_rgba(tone, 150), width=4)

    # Chirp: amplitude and frequency rise toward merger.
    x0, x1, ymid = 150, 480, 470
    plate.arrow((x0, 650), (x1, 650), fill=INK, width=4, head=13)
    plate.arrow((x0, 650), (x0, 300), fill=INK, width=4, head=13)
    plate.text((160, 285), "strain", size=24, bold=True, fill=INK, anchor="la")
    chirp = []
    phase = 0.0
    for i in range(180):
        f = i / 179
        phase += .11 + .42 * f * f
        amplitude = 18 + 120 * f ** 2
        chirp.append((x0 + f * (x1 - x0), ymid - math.sin(phase) * amplitude))
    plate.draw.line(chirp, fill=PLUM, width=5, joint="curve")
    plate.text((315, 690), "time to merger →", size=24, bold=True,
               fill=INK, anchor="mm")
    _tag(plate, (315, 740), "strain waveform → compact binary", PLUM, size=24)

    # Galaxy rotation: observed velocities stay roughly flat while visible-
    # matter-only expectation falls. Distinct line style and point shape encode it.
    gx0, gx1, gy0, gy1 = 610, 925, 315, 650
    plate.arrow((gx0, gy1), (gx1, gy1), fill=INK, width=4, head=13)
    plate.arrow((gx0, gy1), (gx0, gy0), fill=INK, width=4, head=13)
    observed = []
    baryons = []
    for i in range(1, 20):
        f = i / 20
        x = gx0 + f * (gx1 - gx0)
        observed.append((x, gy1 - (180 + 70 * (1 - math.exp(-f * 9)))))
        baryons.append((x, gy1 - (250 * math.sqrt(f) * math.exp(-f * .9))))
    plate.draw.line(observed, fill=BLUE, width=7)
    # Draw the curved dashed baryonic expectation segment by segment.
    for a, b in zip(baryons[::2], baryons[1::2]):
        plate.draw.line((*a, *b), fill=GOLD, width=4)
    for index, point in enumerate(observed[::3]):
        _marker(plate, point, BLUE, "square" if index % 2 else "circle", size=6)
    plate.text((767, 690), "galactic radius →", size=24, bold=True,
               fill=INK, anchor="mm")
    plate.text((625, 285), "orbital speed", size=24, bold=True,
               fill=INK, anchor="la")
    plate.text((750, 455), "observed pattern", size=24, bold=True,
               fill=BLUE, anchor="lm")
    plate.text((775, 555), "visible matter only", size=24, bold=True,
               fill=GOLD, anchor="lm")

    # Expansion: distance residual versus redshift; error bars preserve the
    # measurement/model boundary and the zero line marks no acceleration model.
    hx0, hx1, hy0, hy1 = 1060, 1445, 315, 650
    plate.arrow((hx0, hy1), (hx1, hy1), fill=INK, width=4, head=13)
    plate.arrow((hx0, hy1), (hx0, hy0), fill=INK, width=4, head=13)
    zero_y = 500
    plate.text((1070, 285), "distance residual", size=24, bold=True,
               fill=INK, anchor="la")
    plate.dashed_line((hx0, zero_y), (hx1, zero_y), fill=INK_SOFT,
                      width=3, dash=10, gap=8)
    data = ((.08, -.05), (.17, .00), (.27, .09), (.38, .17), (.50, .23),
            (.64, .27), (.78, .31), (.92, .34))
    for index, (z, residual) in enumerate(data):
        x = hx0 + z * (hx1 - hx0)
        y = zero_y - residual * 360
        plate.draw.line((x, y - 18, x, y + 18), fill=CORAL, width=3)
        _marker(plate, (x, y), CORAL, "triangle" if index % 2 else "circle", size=7)
    plate.text((1250, 690), "redshift →", size=24, bold=True,
               fill=INK, anchor="mm")
    plate.text((1250, 535), "non-accelerating reference", size=24, bold=True,
               fill=INK_SOFT, anchor="mm")
    _tag(plate, (1250, 720), "distance residual → acceleration", CORAL, size=24)

    plate.text((800, 777),
               "calibrated signal → supported inference → mechanism still open",
               size=26, bold=True, fill=INK, anchor="mm")
    _footer(plate, content)


RENDERERS: Dict[str, Renderer] = {
    "earth.3.earth-science": draw_earth_science,
    "earth.3.astronomy": draw_astronomy,
    "earth.3.climate-sci": draw_climate_science,
    "earth.3.ecology-earth": draw_ecology_earth,
    "earth.3.space-exploration": draw_space_exploration,
    "earth.4.geophysics": draw_geophysics,
    "earth.4.astrophysics": draw_astrophysics,
    "earth.4.planetary": draw_planetary,
    "earth.4.climatology": draw_climatology,
    "earth.4.oceanatmos": draw_oceanatmos,
    "earth.5.cosmology": draw_cosmology,
    "earth.5.astrobiology": draw_astrobiology,
    "earth.5.earth-systems": draw_earth_systems,
    "earth.5.frontier": draw_frontier,
}
