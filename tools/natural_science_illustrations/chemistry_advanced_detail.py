"""Bespoke field-guide plates for generator-owned advanced chemistry lessons.

The shared natural-science layouts are intentionally simple, but chemistry at
Stages 3--5 is learned through particle inventories, energy landscapes,
electron density, apparatus, and measured signals.  These renderers put that
evidence in the picture.  They are deterministic Pillow drawings and share the
same ``(plate, content)`` interface as the generic renderer registry.

``RENDERERS`` is deliberately keyed by lesson id.  Importing this module has no
side effects; the natural-science entry point decides when to register it.
"""

from __future__ import annotations

import math
from typing import Callable, Dict, Mapping, Sequence, Tuple

from .core import (
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
    SciencePlate,
    _science_font,
    hex_rgba,
    mix,
)


Point = Tuple[float, float]
Box = Tuple[float, float, float, float]
Renderer = Callable[[SciencePlate, Mapping[str, object]], None]


def _surface(plate: SciencePlate, box: Box, tone: str = PLUM, *, alpha: int = 225,
             radius: int = 24, width: int = 4) -> None:
    """A quiet plotting surface, not a semantic card."""
    plate.draw.rounded_rectangle(
        box,
        radius=radius,
        fill=hex_rgba(mix(tone, PAPER_LIGHT, .90), alpha),
        outline=hex_rgba(tone, 185),
        width=width,
    )


def _center_text(plate: SciencePlate, box: Box, value: str, *, size: int = 26,
                 bold: bool = False, fill: str = INK, line_gap: int = 6) -> None:
    """Wrap centred copy with the science-aware sans-serif face."""
    size = max(24, size)
    x0, y0, x1, y1 = box
    face = _science_font(value, size, bold=bold)
    lines = []
    line = ""
    for word in value.split():
        trial = (line + " " + word).strip()
        if not line or plate.draw.textlength(trial, font=face) <= x1 - x0:
            line = trial
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    leading = size + line_gap
    block = len(lines) * leading - line_gap
    y = y0 + max(0, (y1 - y0 - block) / 2)
    for line in lines:
        plate.text(((x0 + x1) / 2, y), line, size=size, bold=bold,
                   fill=fill, anchor="ma")
        y += leading


def _tag(plate: SciencePlate, center: Point, value: str, tone: str = PLUM,
         *, size: int = 24, pale: bool = False) -> None:
    size = max(24, size)
    face = _science_font(value, size, bold=True)
    left, top, right, bottom = plate.draw.textbbox(center, value, font=face, anchor="mm")
    fill = mix(tone, PAPER_LIGHT, .76) if pale else tone
    text_fill = INK if pale else PAPER_LIGHT
    plate.draw.rounded_rectangle(
        (left - 16, top - 9, right + 16, bottom + 9),
        radius=15,
        fill=hex_rgba(fill, 242),
        outline=hex_rgba(tone, 210) if pale else None,
        width=2,
    )
    plate.text(center, value, size=size, bold=True, fill=text_fill, anchor="mm")


def _footer(plate: SciencePlate, content: Mapping[str, object]) -> None:
    value = str(content["footer"])
    plate.draw.rounded_rectangle(
        (165, 808, 1435, 890),
        radius=24,
        fill=hex_rgba(plate.domain_accent, 34),
        outline=hex_rgba(plate.domain_accent, 125),
        width=3,
    )
    _center_text(plate, (195, 814, 1405, 884), value, size=26,
                 bold=True, fill=INK, line_gap=6)


def _arrow(plate: SciencePlate, start: Point, end: Point, *, tone: str = PLUM,
           label: str = "", label_at: Point | None = None, width: int = 8,
           head: int = 22, label_size: int = 24) -> None:
    plate.arrow(start, end, fill=tone, width=width, head=head)
    if label:
        _tag(plate, label_at or ((start[0] + end[0]) / 2,
                                 (start[1] + end[1]) / 2 - 25),
             label, tone, size=label_size)


def _double_arrow(plate: SciencePlate, start: Point, end: Point, *, tone: str,
                  label: str = "", label_at: Point | None = None) -> None:
    plate.double_arrow(start, end, fill=tone, width=6)
    if label:
        _tag(plate, label_at or ((start[0] + end[0]) / 2,
                                 (start[1] + end[1]) / 2 - 25),
             label, tone, size=24)


def _dot_pattern(plate: SciencePlate, center: Point, tone: str, *, radius: float = 22,
                 pattern: str = "plain", label: str = "") -> None:
    x, y = center
    fill = mix(tone, PAPER_LIGHT, .55)
    if pattern == "square":
        plate.draw.rounded_rectangle((x - radius, y - radius, x + radius, y + radius),
                                     radius=6, fill=hex_rgba(fill, 245),
                                     outline=tone, width=4)
    else:
        plate.dot((x, y), radius, fill=fill, outline=tone, width=4)
    if pattern == "striped":
        for offset in (-10, 0, 10):
            plate.draw.line((x - radius * .70, y + offset,
                             x + radius * .70, y + offset), fill=tone, width=3)
    elif pattern == "spotted":
        for dx, dy in ((-8, -7), (9, -5), (-3, 9)):
            plate.dot((x + dx, y + dy), 3, fill=tone, outline=tone, width=1)
    if label:
        plate.text((x, y), label, size=max(24, int(radius * .9)), bold=True,
                   fill=INK, anchor="mm")


def _bond(plate: SciencePlate, start: Point, end: Point, *, tone: str = INK,
          order: int = 1, width: int = 6) -> None:
    x0, y0 = start
    x1, y1 = end
    dx, dy = x1 - x0, y1 - y0
    mag = max(1.0, math.hypot(dx, dy))
    px, py = -dy / mag, dx / mag
    offsets = (0,) if order == 1 else (-5, 5) if order == 2 else (-8, 0, 8)
    for offset in offsets:
        plate.draw.line((x0 + px * offset, y0 + py * offset,
                         x1 + px * offset, y1 + py * offset),
                        fill=tone, width=width)


def _atom(plate: SciencePlate, center: Point, symbol: str, *, tone: str = BLUE,
          radius: float = 25, pattern: str = "plain") -> None:
    _dot_pattern(plate, center, tone, radius=radius, pattern=pattern)
    plate.text(center, symbol, size=max(24, int(radius * .82)), bold=True,
               fill=INK, anchor="mm")


def _h2(plate: SciencePlate, center: Point, *, scale: float = 1.0) -> None:
    x, y = center
    gap = 26 * scale
    _bond(plate, (x - gap, y), (x + gap, y), width=max(4, int(5 * scale)))
    _atom(plate, (x - gap, y), "H", tone=BLUE, radius=20 * scale)
    _atom(plate, (x + gap, y), "H", tone=BLUE, radius=20 * scale)


def _o2(plate: SciencePlate, center: Point, *, scale: float = 1.0) -> None:
    x, y = center
    gap = 29 * scale
    _bond(plate, (x - gap, y), (x + gap, y), order=2,
          width=max(3, int(4 * scale)))
    _atom(plate, (x - gap, y), "O", tone=CORAL, radius=22 * scale,
          pattern="striped")
    _atom(plate, (x + gap, y), "O", tone=CORAL, radius=22 * scale,
          pattern="striped")


def _water(plate: SciencePlate, center: Point, *, scale: float = 1.0) -> None:
    x, y = center
    oxygen = (x, y + 6 * scale)
    left = (x - 39 * scale, y - 25 * scale)
    right = (x + 39 * scale, y - 25 * scale)
    _bond(plate, oxygen, left, width=max(3, int(5 * scale)))
    _bond(plate, oxygen, right, width=max(3, int(5 * scale)))
    _atom(plate, oxygen, "O", tone=CORAL, radius=22 * scale,
          pattern="striped")
    _atom(plate, left, "H", tone=BLUE, radius=17 * scale)
    _atom(plate, right, "H", tone=BLUE, radius=17 * scale)


def _plot_axes(plate: SciencePlate, box: Box, x_label: str, y_label: str,
               *, x_ticks: Sequence[Tuple[float, str]] = (),
               y_ticks: Sequence[Tuple[float, str]] = ()) -> Callable[[float, float], Point]:
    x0, y0, x1, y1 = box
    for fraction in (.25, .5, .75):
        xx = x0 + fraction * (x1 - x0)
        yy = y1 - fraction * (y1 - y0)
        plate.draw.line((xx, y0, xx, y1), fill=hex_rgba(GRID, 125), width=2)
        plate.draw.line((x0, yy, x1, yy), fill=hex_rgba(GRID, 125), width=2)
    plate.arrow((x0, y1), (x1 + 8, y1), fill=INK, width=5, head=17)
    plate.arrow((x0, y1), (x0, y0 - 8), fill=INK, width=5, head=17)
    plate.text(((x0 + x1) / 2, y1 + 42), x_label, size=24, bold=True,
               anchor="mm")
    plate.text((x0 - 12, y0 - 18), y_label, size=24, bold=True, anchor="ls")
    for fraction, label in x_ticks:
        x = x0 + fraction * (x1 - x0)
        plate.draw.line((x, y1 - 7, x, y1 + 7), fill=INK, width=3)
        plate.text((x, y1 + 18), label, size=24, fill=INK_SOFT, anchor="ma")
    for fraction, label in y_ticks:
        y = y1 - fraction * (y1 - y0)
        plate.draw.line((x0 - 7, y, x0 + 7, y), fill=INK, width=3)
        plate.text((x0 - 15, y), label, size=24, fill=INK_SOFT, anchor="rm")
    return lambda xf, yf: (x0 + xf * (x1 - x0), y1 - yf * (y1 - y0))


def _polyline(plate: SciencePlate, points: Sequence[Point], *, tone: str,
              width: int = 7, dashed: bool = False) -> None:
    if not dashed:
        plate.draw.line(list(points), fill=tone, width=width, joint="curve")
        return
    for first, second in zip(points, points[1:]):
        x0, y0 = first
        x1, y1 = second
        length = max(1.0, math.hypot(x1 - x0, y1 - y0))
        ux, uy = (x1 - x0) / length, (y1 - y0) / length
        distance = 0.0
        while distance < length:
            end = min(length, distance + 15)
            plate.draw.line((x0 + ux * distance, y0 + uy * distance,
                             x0 + ux * end, y0 + uy * end),
                            fill=tone, width=width)
            distance += 27


def _bracket(plate: SciencePlate, x: float, y0: float, y1: float, label: str,
             *, tone: str = PLUM, side: str = "right") -> None:
    direction = 1 if side == "right" else -1
    plate.draw.line((x, y0, x, y1), fill=tone, width=5)
    plate.draw.line((x, y0, x + direction * 15, y0), fill=tone, width=5)
    plate.draw.line((x, y1, x + direction * 15, y1), fill=tone, width=5)
    plate.text((x + direction * 24, (y0 + y1) / 2), label, size=24,
               bold=True, fill=tone, anchor="lm" if direction > 0 else "rm")


def draw_atomic_structure(plate: SciencePlate, content: Mapping[str, object]) -> None:
    """Orbitals as probability shapes plus a quantised energy ladder."""
    _surface(plate, (105, 215, 850, 785), BLUE)
    _tag(plate, (480, 250), "ORBITALS ARE PROBABILITY DISTRIBUTIONS", BLUE)

    # 1s: nested translucent density, explicitly not a path.
    cx, cy = 300, 480
    for radius, alpha in ((160, 28), (128, 38), (96, 52), (66, 72)):
        plate.draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius),
                           fill=hex_rgba(BLUE, alpha), outline=None)
    for dx, dy, tone, label in ((-14, 4, CORAL, "p+"),
                                (15, -7, GOLD, "n"),
                                (7, 18, CORAL, "p+")):
        plate.dot((cx + dx, cy + dy), 14, fill=mix(tone, PAPER_LIGHT, .35),
                  outline=tone, width=3)
    plate.text((300, 662), "1s · spherical density", size=26, bold=True,
               fill=BLUE, anchor="mm")
    plate.text((300, 704), "cloud ≠ electron orbit", size=24, fill=INK_SOFT,
               anchor="mm")

    # 2p: signed lobes make phase and node visible.
    px, py = 650, 485
    plate.draw.ellipse((px - 145, py - 66, px - 13, py + 66),
                       fill=hex_rgba(CORAL_LIGHT, 230), outline=CORAL, width=5)
    plate.draw.ellipse((px + 13, py - 66, px + 145, py + 66),
                       fill=hex_rgba(TEAL_LIGHT, 230), outline=TEAL, width=5)
    plate.draw.line((px, py - 92, px, py + 92), fill=INK, width=4)
    plate.text((px - 79, py), "+", size=34, bold=True, fill=CORAL, anchor="mm")
    plate.text((px + 79, py), "−", size=34, bold=True, fill=TEAL, anchor="mm")
    plate.text((650, 602), "2p · angular node", size=26, bold=True,
               fill=PLUM, anchor="mm")
    plate.text((650, 646), "sign = wave phase, not charge", size=24,
               fill=INK_SOFT, anchor="mm")

    # Energy level map; capacities count spin-orbital states, not rings.
    _surface(plate, (900, 215, 1495, 785), PLUM)
    plate.arrow((975, 725), (975, 270), fill=INK, width=5, head=18)
    plate.text((960, 250), "ENERGY", size=24, bold=True, anchor="mm")
    levels = [
        (675, "1s", "1 orbital · max 2 e−", GOLD, 1),
        (565, "2s", "1 orbital · max 2 e−", TEAL, 1),
        (450, "2p", "3 orbitals · max 6 e−", BLUE, 3),
        (335, "3s", "1 orbital · max 2 e−", CORAL, 1),
    ]
    for y, name, detail, tone, count in levels:
        start = 1040
        for index in range(count):
            plate.draw.line((start + index * 72, y, start + 49 + index * 72, y),
                            fill=tone, width=7)
        plate.text((1015, y), name, size=28, bold=True, fill=tone, anchor="rm")
        plate.text((1040, y + 25), detail, size=24, fill=INK_SOFT, anchor="la")
    plate.text((1250, 755), "Z = protons · isotopes differ in neutrons",
               size=24, bold=True, fill=INK, anchor="mm")
    _footer(plate, content)


def draw_bonding(plate: SciencePlate, content: Mapping[str, object]) -> None:
    """Three electron-distribution limits drawn as actual particle structures."""
    plate.draw.line((555, 228, 555, 745), fill=hex_rgba(GRID, 175), width=3)
    plate.draw.line((1045, 228, 1045, 745), fill=hex_rgba(GRID, 175), width=3)

    _tag(plate, (320, 240), "IONIC LATTICE", CORAL)
    # Alternating shapes and signs provide non-colour redundancy.
    for row in range(3):
        for col in range(3):
            positive = (row + col) % 2 == 0
            x, y = 205 + col * 112, 370 + row * 105
            _dot_pattern(plate, (x, y), CORAL if positive else BLUE,
                         radius=34, pattern="plain" if positive else "square",
                         label="+" if positive else "−")
    plate.text((320, 705), "Coulomb attraction extends", size=24, bold=True,
               fill=INK, anchor="mm")
    plate.text((320, 739), "through the crystal—not NaCl molecules", size=24,
               fill=INK_SOFT, anchor="mm")

    _tag(plate, (800, 240), "POLAR COVALENT", TEAL)
    # H--Cl density is continuous but biased toward Cl.
    plate.draw.ellipse((635, 378, 958, 550), fill=hex_rgba(TEAL_LIGHT, 105),
                       outline=hex_rgba(TEAL, 170), width=5)
    for radius, alpha in ((92, 35), (70, 45), (48, 62)):
        plate.draw.ellipse((855 - radius, 464 - radius, 855 + radius, 464 + radius),
                           fill=hex_rgba(TEAL, alpha))
    _atom(plate, (700, 464), "H", tone=BLUE, radius=33)
    _atom(plate, (875, 464), "Cl", tone=TEAL, radius=48, pattern="striped")
    plate.text((700, 370), "δ+", size=30, bold=True, fill=BLUE, anchor="mm")
    plate.text((875, 360), "δ−", size=30, bold=True, fill=TEAL, anchor="mm")
    plate.text((800, 610), "Shared density is continuous", size=24, bold=True,
               fill=INK, anchor="mm")
    plate.text((800, 648), "electronegativity shifts its centre", size=24,
               fill=INK_SOFT, anchor="mm")

    _tag(plate, (1280, 240), "METALLIC SOLID", PLUM)
    for row in range(3):
        for col in range(3):
            x, y = 1168 + col * 112, 370 + row * 105
            _dot_pattern(plate, (x, y), PLUM, radius=31, pattern="striped", label="+")
    # Delocalised electrons and arrows show mobile charge carriers.
    electron_points = ((1110, 420), (1218, 470), (1408, 405),
                       (1138, 590), (1328, 575), (1430, 655))
    for point in electron_points:
        plate.dot(point, 9, fill=GOLD, outline=INK, width=2)
    _arrow(plate, (1110, 670), (1435, 670), tone=GOLD,
           label="mobile e−", label_at=(1272, 716), width=6, head=18)
    plate.text((1280, 750), "ion cores remain ordered", size=24,
               fill=INK_SOFT, anchor="mm")

    plate.text((800, 780), "Bond labels are useful limits on a continuum of electron distribution.",
               size=24, bold=True, fill=INK, anchor="mm")
    _footer(plate, content)


def draw_stoichiometry(plate: SciencePlate, content: Mapping[str, object]) -> None:
    """A fully counted limiting-reagent particle ledger."""
    _tag(plate, (800, 222), "2 H₂ + O₂ → 2 H₂O", PLUM, size=28)
    plate.text((340, 276), "START · 5 mol H₂ + 2 mol O₂", size=27,
               bold=True, fill=INK, anchor="mm")
    plate.text((1250, 276), "FINISH · 4 mol H₂O + 1 mol H₂", size=27,
               bold=True, fill=INK, anchor="mm")

    # Reactant inventory: symbols and surface patterns distinguish species.
    for center in ((185, 365), (330, 365), (475, 365),
                   (255, 485), (400, 485)):
        _h2(plate, center, scale=.92)
    for center in ((255, 625), (405, 625)):
        _o2(plate, center, scale=.88)
    plate.text((332, 705), "10 mol H · 4 mol O", size=25, bold=True,
               fill=INK_SOFT, anchor="mm")

    # Reaction extent gate makes the limiting reagent causal.
    plate.draw.rounded_rectangle((630, 320, 945, 705), radius=36,
                                 fill=hex_rgba(GOLD_LIGHT, 175),
                                 outline=GOLD, width=5)
    plate.text((787, 372), "REACTION EXTENT", size=25, bold=True,
               fill=INK, anchor="mm")
    plate.text((787, 437), "ξ = 2 mol", size=37, bold=True,
               fill=PLUM, anchor="mm")
    plate.draw.line((685, 484, 890, 484), fill=GOLD, width=5)
    plate.text((787, 530), "O₂ reaches zero first", size=25, bold=True,
               fill=CORAL, anchor="mm")
    plate.text((787, 578), "consume 4 mol H₂", size=24, fill=INK_SOFT, anchor="mm")
    plate.text((787, 614), "consume 2 mol O₂", size=24, fill=INK_SOFT, anchor="mm")
    plate.text((787, 650), "form 4 mol H₂O", size=24, fill=INK_SOFT, anchor="mm")
    _arrow(plate, (550, 512), (617, 512), tone=PLUM, width=7, head=17)
    _arrow(plate, (958, 512), (1025, 512), tone=PLUM, width=7, head=17)

    for center in ((1120, 370), (1300, 370), (1120, 515), (1300, 515)):
        _water(plate, center, scale=.91)
    _h2(plate, (1210, 655), scale=.92)
    plate.draw.rounded_rectangle((1128, 705, 1292, 753), radius=18,
                                 outline=BLUE, width=3,
                                 fill=hex_rgba(BLUE_LIGHT, 150))
    plate.text((1210, 729), "excess H₂", size=24, bold=True,
               fill=BLUE, anchor="mm")
    plate.text((1250, 780), "total: 10 mol H · 4 mol O",
               size=24, bold=True, fill=INK_SOFT, anchor="mm")
    _footer(plate, content)


def _reaction_species(plate: SciencePlate, center: Point, text: str, tone: str,
                      *, shape: str = "circle") -> None:
    x, y = center
    if shape == "solid":
        plate.draw.rounded_rectangle((x - 70, y - 30, x + 70, y + 30), radius=8,
                                     fill=hex_rgba(tone, 215), outline=INK, width=3)
    else:
        _dot_pattern(plate, center, tone, radius=34,
                     pattern="square" if shape == "square" else "plain")
    plate.text(center, text, size=24, bold=True, fill=INK, anchor="mm")


def draw_reactions(plate: SciencePlate, content: Mapping[str, object]) -> None:
    """Three reaction classes as particle-level transfers, not a table."""
    lanes = ((275, "PROTON TRANSFER", TEAL),
             (500, "ELECTRON TRANSFER", CORAL),
             (725, "LATTICE FORMATION", BLUE))
    for y, heading, tone in lanes:
        plate.draw.line((125, y + 78, 1475, y + 78), fill=hex_rgba(GRID, 115), width=2)
        _tag(plate, (260, y - 55), heading, tone)

    # Hydronium + hydroxide -> two water molecules.
    _reaction_species(plate, (260, 285), "H₃O⁺", TEAL)
    _reaction_species(plate, (500, 285), "OH⁻", BLUE, shape="square")
    _arrow(plate, (590, 285), (880, 285), tone=TEAL,
           label="H+ moves", label_at=(735, 244))
    _water(plate, (1020, 285), scale=.72)
    _water(plate, (1260, 285), scale=.72)
    plate.text((1390, 285), "2 H₂O", size=26, bold=True, fill=TEAL, anchor="mm")

    # Zinc/Cu redox: explicit two-electron bookkeeping.
    _reaction_species(plate, (250, 510), "Zn", PLUM, shape="solid")
    _reaction_species(plate, (490, 510), "Cu²⁺", BLUE)
    _arrow(plate, (585, 510), (875, 510), tone=CORAL,
           label="2 e−", label_at=(730, 469))
    _reaction_species(plate, (1015, 510), "Zn²⁺", PLUM)
    _reaction_species(plate, (1270, 510), "Cu", CORAL, shape="solid")
    plate.text((250, 572), "oxidised", size=24, bold=True, fill=PLUM, anchor="mm")
    plate.text((1270, 572), "reduced", size=24, bold=True, fill=CORAL, anchor="mm")

    # AgCl precipitation: dissolved ions become a repeating contact solid.
    _reaction_species(plate, (250, 735), "Ag⁺", CORAL)
    _reaction_species(plate, (490, 735), "Cl⁻", BLUE, shape="square")
    _arrow(plate, (585, 735), (875, 735), tone=BLUE,
           label="low Ksp", label_at=(730, 694))
    for row in range(2):
        for col in range(4):
            is_ag = (row + col) % 2 == 0
            _dot_pattern(plate, (1010 + col * 86, 704 + row * 62),
                         CORAL if is_ag else BLUE, radius=24,
                         pattern="plain" if is_ag else "square",
                         label="+" if is_ag else "−")
    plate.text((1375, 735), "AgCl(s)", size=27, bold=True, fill=BLUE, anchor="mm")
    _footer(plate, content)


def _gas_box(plate: SciencePlate, box: Box, points: Sequence[Point], *,
             piston_fraction: float, label: str) -> None:
    x0, y0, x1, y1 = box
    piston_y = y0 + piston_fraction * (y1 - y0)
    plate.draw.rounded_rectangle(box, radius=16, fill=hex_rgba(BLUE_LIGHT, 115),
                                 outline=BLUE, width=4)
    plate.draw.rectangle((x0 + 4, y0 + 4, x1 - 4, piston_y),
                         fill=hex_rgba(PAPER_LIGHT, 220))
    plate.draw.line((x0 + 3, piston_y, x1 - 3, piston_y), fill=INK, width=10)
    plate.draw.line(((x0 + x1) / 2, y0 - 20, (x0 + x1) / 2, piston_y),
                    fill=INK_SOFT, width=8)
    usable_y0 = piston_y + 18
    for xf, yf in points:
        x = x0 + 18 + xf * (x1 - x0 - 36)
        y = usable_y0 + yf * max(10, y1 - usable_y0 - 18)
        plate.dot((x, y), 8, fill=PLUM, outline=INK, width=2)
        # Motion tick: each molecule is visibly kinetic, not static packing.
        plate.draw.line((x + 9, y - 7, x + 22, y - 15), fill=PLUM, width=3)
    plate.text(((x0 + x1) / 2, y1 + 24), label, size=24, bold=True,
               fill=INK, anchor="ma")


def draw_gases(plate: SciencePlate, content: Mapping[str, object]) -> None:
    """Ideal-gas isotherms paired with a fixed-particle piston model."""
    graph = (150, 275, 925, 680)
    point = _plot_axes(
        plate, graph, "", "P / kPa",
        x_ticks=((0, "1"), (.25, "2"), (.5, "3"), (.75, "4"), (1, "5")),
        y_ticks=((0, "0"), (.3125, "50"), (.625, "100"), (.9375, "150")),
    )

    volumes = [1 + index * .08 for index in range(51)]
    lower = [point((v - 1) / 4, (100 / v) / 160) for v in volumes]
    higher = [point((v - 1) / 4, (150 / v) / 160) for v in volumes]
    _polyline(plate, lower, tone=BLUE, width=8)
    _polyline(plate, higher, tone=CORAL, width=7, dashed=True)
    plate.draw.line((270, 225, 335, 225), fill=BLUE, width=8)
    plate.text((350, 225), "300 K · PV ≈ 100 kPa·L", size=24,
               bold=True, fill=INK, anchor="lm")
    _polyline(plate, ((270, 255), (335, 255)), tone=CORAL, width=7, dashed=True)
    plate.text((350, 255), "450 K · PV ≈ 150 kPa·L", size=24,
               bold=True, fill=INK, anchor="lm")
    plate.text((900, 716), "V / L", size=24, bold=True, fill=INK,
               anchor="rm")

    # Same eight particles in both cylinders: compression changes collision rate.
    particles = ((.08, .12), (.30, .24), (.57, .10), (.82, .29),
                 (.18, .62), (.44, .75), (.68, .56), (.88, .81))
    _gas_box(plate, (1040, 305, 1230, 615), particles,
             piston_fraction=.56, label="small V · high P")
    _gas_box(plate, (1285, 305, 1475, 615), particles,
             piston_fraction=.18, label="large V · low P")
    _arrow(plate, (1430, 270), (1110, 270), tone=PLUM,
           label="compress at fixed n, T", label_at=(1270, 220), width=7)
    _center_text(plate, (1025, 680, 1490, 775),
                 "Same molecule count; smaller volume means more wall collisions per second.",
                 size=24, bold=True, fill=INK)
    _footer(plate, content)


def _reaction_curve(plate: SciencePlate, point: Callable[[float, float], Point],
                    *, peak: float, end: float, tone: str, dashed: bool = False) -> None:
    values = []
    for index in range(81):
        x = index / 80
        baseline = 0.58 + (end - 0.58) * (3 * x * x - 2 * x * x * x)
        barrier = (peak - (0.58 + end) / 2) * math.exp(-((x - .46) / .16) ** 2)
        values.append(point(x, min(.96, baseline + barrier)))
    _polyline(plate, values, tone=tone, width=8 if not dashed else 6, dashed=dashed)


def draw_energy(plate: SciencePlate, content: Mapping[str, object]) -> None:
    """One reaction coordinate with activation and enthalpy separated."""
    graph = (185, 265, 1090, 735)
    point = _plot_axes(plate, graph, "reaction progress", "enthalpy H")
    _reaction_curve(plate, point, peak=.93, end=.25, tone=CORAL)
    _reaction_curve(plate, point, peak=.73, end=.25, tone=GREEN, dashed=True)

    react_y = point(0, .58)[1]
    product_y = point(1, .25)[1]
    uncat_y = point(.46, .93)[1]
    cat_y = point(.46, .73)[1]
    plate.draw.line((185, react_y, 295, react_y), fill=INK, width=4)
    plate.draw.line((980, product_y, 1090, product_y), fill=INK, width=4)
    plate.text((235, react_y - 22), "reactants", size=24, bold=True,
               fill=INK, anchor="mm")
    plate.text((1035, product_y - 22), "products", size=24, bold=True,
               fill=INK, anchor="mm")
    _bracket(plate, 352, react_y, uncat_y, "Ea", tone=CORAL)
    _bracket(plate, 455, react_y, cat_y, "Ea, cat", tone=GREEN)
    _bracket(plate, 1122, react_y, product_y, "ΔH < 0", tone=PLUM,
             side="left")

    # Line-style legend and an explicit energy-flow cue.
    plate.draw.line((1130, 315, 1215, 315), fill=CORAL, width=8)
    plate.text((1235, 315), "uncatalysed", size=24, bold=True,
               fill=INK, anchor="lm")
    _polyline(plate, ((1130, 375), (1215, 375)), tone=GREEN, width=6, dashed=True)
    plate.text((1235, 375), "catalysed", size=24, bold=True,
               fill=INK, anchor="lm")
    _surface(plate, (1150, 440, 1465, 708), GOLD)
    plate.text((1308, 478), "ENERGY ACCOUNT", size=25, bold=True,
               fill=GOLD, anchor="mm")
    plate.text((1308, 545), "same endpoints", size=25, bold=True,
               fill=INK, anchor="mm")
    plate.text((1308, 586), "lower barrier", size=25, bold=True,
               fill=GREEN, anchor="mm")
    _arrow(plate, (1240, 636), (1380, 636), tone=CORAL, width=7, head=18)
    plate.text((1308, 684), "heat → surroundings", size=24, bold=True,
               fill=CORAL, anchor="mm")
    _footer(plate, content)


def _carbon(plate: SciencePlate, center: Point, *, radius: float = 27) -> None:
    _atom(plate, center, "C", tone=INK_SOFT, radius=radius, pattern="striped")


def draw_organic_intro(plate: SciencePlate, content: Mapping[str, object]) -> None:
    """Carbon connectivity tied to local geometry and reactivity."""
    plate.draw.line((555, 235, 555, 760), fill=hex_rgba(GRID, 155), width=3)
    plate.draw.line((1045, 235, 1045, 760), fill=hex_rgba(GRID, 155), width=3)

    _tag(plate, (315, 235), "C—C σ BOND", BLUE)
    _carbon(plate, (245, 445), radius=31)
    _carbon(plate, (385, 445), radius=31)
    _bond(plate, (276, 445), (354, 445), tone=BLUE, width=8)
    # Tetrahedral substituent strokes and rotation arc.
    for x, direction in ((245, -1), (385, 1)):
        _bond(plate, (x, 414), (x + direction * 55, 350), width=5)
        _bond(plate, (x, 476), (x + direction * 55, 540), width=5)
        _bond(plate, (x, 445), (x, 570 if x == 245 else 320), width=5)
    plate.draw.arc((270, 360, 360, 530), 65, 290, fill=BLUE, width=6)
    plate.text((315, 615), "tetrahedral C · ≈109.5°", size=25,
               bold=True, fill=BLUE, anchor="mm")
    plate.text((315, 657), "rotation about single bond", size=24,
               fill=INK_SOFT, anchor="mm")

    _tag(plate, (800, 235), "C=C π BOND", CORAL)
    _carbon(plate, (730, 445), radius=31)
    _carbon(plate, (870, 445), radius=31)
    _bond(plate, (761, 445), (839, 445), tone=CORAL, order=2, width=6)
    # p-orbital overlap above/below the molecular plane.
    for x in (730, 870):
        plate.draw.ellipse((x - 38, 310, x + 38, 410),
                           fill=hex_rgba(CORAL_LIGHT, 190), outline=CORAL, width=4)
        plate.draw.ellipse((x - 38, 480, x + 38, 580),
                           fill=hex_rgba(TEAL_LIGHT, 190), outline=TEAL, width=4)
    for x, direction in ((730, -1), (870, 1)):
        _bond(plate, (x, 445), (x + direction * 78, 375), width=5)
        _bond(plate, (x, 445), (x + direction * 78, 515), width=5)
    plate.text((800, 615), "trigonal planar · ≈120°", size=25,
               bold=True, fill=CORAL, anchor="mm")
    plate.text((800, 657), "π overlap restricts rotation", size=24,
               fill=INK_SOFT, anchor="mm")

    _tag(plate, (1285, 235), "ALCOHOL C—OH", TEAL)
    _carbon(plate, (1168, 445), radius=31)
    _atom(plate, (1300, 445), "O", tone=CORAL, radius=31, pattern="striped")
    _atom(plate, (1415, 385), "H", tone=BLUE, radius=24)
    _bond(plate, (1199, 445), (1269, 445), tone=TEAL, width=7)
    _bond(plate, (1330, 429), (1392, 397), tone=TEAL, width=6)
    plate.text((1168, 375), "δ+", size=28, bold=True, fill=BLUE, anchor="mm")
    plate.text((1300, 365), "δ−", size=28, bold=True, fill=CORAL, anchor="mm")
    # Hydrogen-bond acceptor water is shown with a dashed contact.
    _water(plate, (1285, 595), scale=.62)
    _polyline(plate, ((1403, 404), (1358, 477), (1310, 548)),
              tone=PLUM, width=5, dashed=True)
    plate.text((1285, 690), "polar O—H enables H bonding", size=24,
               bold=True, fill=TEAL, anchor="mm")
    plate.text((800, 775), "Connectivity + 3-D geometry + functional group determine reactivity.",
               size=25, bold=True, fill=INK, anchor="mm")
    _footer(plate, content)


def draw_physical(plate: SciencePlate, content: Mapping[str, object]) -> None:
    """A free-energy landscape that keeps equilibrium and rate independent."""
    graph = (170, 270, 1050, 735)
    point = _plot_axes(plate, graph, "reaction coordinate", "Gibbs free energy G")
    _reaction_curve(plate, point, peak=.95, end=.28, tone=CORAL)
    _reaction_curve(plate, point, peak=.73, end=.28, tone=GREEN, dashed=True)
    plate.text((800, 265), "uncatalysed", size=24, bold=True,
               fill=CORAL, anchor="mm")
    plate.text((800, 310), "catalysed", size=24, bold=True,
               fill=GREEN, anchor="mm")
    r_y = point(0, .58)[1]
    p_y = point(1, .28)[1]
    _bracket(plate, 340, r_y, point(.46, .95)[1], "ΔG‡", tone=CORAL)
    _bracket(plate, 1100, r_y, p_y, "ΔG° < 0", tone=PLUM, side="left")
    plate.text((230, r_y - 22), "R", size=28, bold=True, fill=INK, anchor="mm")
    plate.text((1015, p_y - 22), "P", size=28, bold=True, fill=INK, anchor="mm")

    _surface(plate, (1175, 260, 1475, 735), PLUM)
    plate.text((1325, 305), "TWO PREDICTIONS", size=25, bold=True,
               fill=PLUM, anchor="mm")
    plate.draw.line((1208, 340, 1442, 340), fill=hex_rgba(GRID, 180), width=3)
    plate.text((1325, 390), "EQUILIBRIUM", size=24, bold=True,
               fill=BLUE, anchor="mm")
    plate.text((1325, 434), "ΔG° = −RT ln K", size=27, bold=True,
               fill=INK, anchor="mm")
    _center_text(plate, (1205, 462, 1445, 530),
                 "endpoint difference sets K",
                 size=24, fill=INK_SOFT)
    plate.draw.line((1208, 553, 1442, 553), fill=hex_rgba(GRID, 180), width=3)
    plate.text((1325, 600), "RATE", size=24, bold=True,
               fill=CORAL, anchor="mm")
    plate.text((1325, 644), "k ∝ e^(−ΔG‡/RT)", size=26, bold=True,
               fill=INK, anchor="mm")
    plate.text((1325, 695), "barrier controls speed", size=24,
               fill=INK_SOFT, anchor="mm")
    _footer(plate, content)


def _wedge(plate: SciencePlate, start: Point, end: Point, *, tone: str = INK) -> None:
    x0, y0 = start
    x1, y1 = end
    dx, dy = x1 - x0, y1 - y0
    mag = max(1.0, math.hypot(dx, dy))
    px, py = -dy / mag, dx / mag
    plate.draw.polygon((start, (x1 + px * 10, y1 + py * 10),
                        (x1 - px * 10, y1 - py * 10)), fill=tone)


def _hashed_bond(plate: SciencePlate, start: Point, end: Point, *, tone: str = INK) -> None:
    x0, y0 = start
    x1, y1 = end
    dx, dy = x1 - x0, y1 - y0
    mag = max(1.0, math.hypot(dx, dy))
    px, py = -dy / mag, dx / mag
    for index in range(1, 7):
        fraction = index / 7
        half = 2 + index * 1.3
        cx, cy = x0 + dx * fraction, y0 + dy * fraction
        plate.draw.line((cx - px * half, cy - py * half,
                         cx + px * half, cy + py * half), fill=tone, width=3)


def _sn2_carbon(plate: SciencePlate, center: Point, *, inverted: bool = False,
                transition: bool = False) -> None:
    x, y = center
    _carbon(plate, center, radius=32)
    sign = -1 if inverted else 1
    # Three labelled substituents make stereochemical inversion visible.
    endpoints = ((x, y - 120), (x - 92 * sign, y + 78), (x + 92 * sign, y + 78))
    labels = ("H", "CH₃", "D")
    _bond(plate, (x, y - 32), endpoints[0], width=5)
    _wedge(plate, (x - sign * 12, y + 22), endpoints[1])
    _hashed_bond(plate, (x + sign * 12, y + 22), endpoints[2])
    for endpoint, label in zip(endpoints, labels):
        plate.text(endpoint, label, size=25, bold=True, fill=INK, anchor="mm")
    if transition:
        plate.draw.rounded_rectangle((x - 120, y - 145, x + 120, y + 125),
                                     radius=20, outline=PLUM, width=4)


def draw_organic(plate: SciencePlate, content: Mapping[str, object]) -> None:
    """A stereochemically explicit concerted SN2 mechanism."""
    _tag(plate, (800, 225), "SN2 · ONE CONCERTED ELECTRON-PAIR EVENT", PLUM)

    # Reactant geometry.
    _sn2_carbon(plate, (405, 500))
    _reaction_species(plate, (165, 500), ":Nu−", TEAL)
    _reaction_species(plate, (620, 500), "LG", CORAL, shape="square")
    _bond(plate, (437, 500), (584, 500), tone=CORAL, width=7)
    plate.text((405, 690), "backside approach", size=24, bold=True,
               fill=TEAL, anchor="mm")

    # Curved electron-source paths, approximated with smooth polylines and heads.
    attack = ((200, 465), (250, 405), (330, 395), (375, 445))
    _polyline(plate, attack, tone=TEAL, width=7)
    _arrow(plate, attack[-2], attack[-1], tone=TEAL, width=7, head=18)
    leaving = ((470, 470), (520, 420), (585, 455))
    _polyline(plate, leaving, tone=CORAL, width=7)
    _arrow(plate, leaving[-2], leaving[-1], tone=CORAL, width=7, head=18)
    plate.text((285, 365), "lone pair → C", size=24, bold=True,
               fill=TEAL, anchor="mm")
    plate.text((545, 365), "C—LG pair → LG", size=24, bold=True,
               fill=CORAL, anchor="mm")

    _arrow(plate, (680, 500), (850, 500), tone=PLUM,
           label="[Nu···C···LG]‡", label_at=(765, 440))

    # Product has inverted wedge/dash ordering and free leaving group.
    _sn2_carbon(plate, (1080, 500), inverted=True)
    _reaction_species(plate, (875, 500), "Nu", TEAL)
    _bond(plate, (909, 500), (1048, 500), tone=TEAL, width=7)
    _reaction_species(plate, (1365, 500), ":LG−", CORAL, shape="square")
    plate.text((1080, 690), "configuration inverted", size=25, bold=True,
               fill=PLUM, anchor="mm")

    plate.draw.rounded_rectangle((245, 730, 1355, 785), radius=20,
                                 fill=hex_rgba(PLUM_LIGHT, 145), outline=PLUM, width=3)
    plate.text((800, 757), "rate = k[Nu−][R—LG] · no carbocation intermediate · steric crowding slows attack",
               size=24, bold=True, fill=INK, anchor="mm")
    _footer(plate, content)


def _orbital_lobes(plate: SciencePlate, center: Point, *, along: str,
                   tone: str, scale: float = 1.0) -> None:
    x, y = center
    length, width = 68 * scale, 32 * scale
    if along == "x":
        boxes = ((x - length, y - width, x - 8, y + width),
                 (x + 8, y - width, x + length, y + width))
    else:
        boxes = ((x - width, y - length, x + width, y - 8),
                 (x - width, y + 8, x + width, y + length))
    for box in boxes:
        plate.draw.ellipse(box, fill=hex_rgba(mix(tone, PAPER_LIGHT, .45), 225),
                           outline=tone, width=4)


def draw_inorganic(plate: SciencePlate, content: Mapping[str, object]) -> None:
    """Octahedral ligand directions causally connected to d-orbital splitting."""
    _tag(plate, (420, 230), "[ML₆]ⁿ⁺ · OCTAHEDRAL", BLUE)
    cx, cy = 430, 505
    # Back axis is dashed; front axis solid. The four in-plane ligands are explicit.
    axes = [((cx, cy), (cx - 190, cy), False), ((cx, cy), (cx + 190, cy), False),
            ((cx, cy), (cx, cy - 190), False), ((cx, cy), (cx, cy + 190), False),
            ((cx, cy), (cx - 120, cy - 105), True), ((cx, cy), (cx + 120, cy + 105), False)]
    for start, end, dashed in axes:
        if dashed:
            _polyline(plate, (start, end), tone=INK_SOFT, width=5, dashed=True)
        else:
            _bond(plate, start, end, tone=INK_SOFT, width=5)
    _atom(plate, (cx, cy), "M", tone=PLUM, radius=45, pattern="striped")
    ligand_points = ((cx - 190, cy), (cx + 190, cy), (cx, cy - 190),
                     (cx, cy + 190), (cx - 120, cy - 105), (cx + 120, cy + 105))
    for index, point in enumerate(ligand_points):
        _atom(plate, point, "L", tone=BLUE, radius=30,
              pattern="square" if index >= 4 else "plain")
    plate.text((430, 748), "six donor atoms on ±x, ±y, ±z", size=25,
               bold=True, fill=INK, anchor="mm")

    # Causal arrow from ligand axes to the energy split.
    _arrow(plate, (675, 505), (790, 505), tone=GOLD,
           label="axis repulsion", label_at=(700, 455), width=7)

    _surface(plate, (815, 220, 1490, 785), PLUM)
    plate.arrow((875, 720), (875, 275), fill=INK, width=5, head=18)
    plate.text((855, 260), "E", size=27, bold=True, anchor="mm")
    # Dashed barycentre preserves the unsplit reference.
    # Octahedral barycentre: eg is +0.6Δo and t2g is −0.4Δo.
    _polyline(plate, ((930, 531), (1435, 531)), tone=GRID, width=4, dashed=True)
    plate.text((1450, 500), "free-ion barycentre", size=24, fill=INK_SOFT,
               anchor="rm")
    for x in (1020, 1190):
        plate.draw.line((x - 50, 352, x + 50, 352), fill=CORAL, width=8)
        _orbital_lobes(plate, (x, 303), along="x" if x == 1020 else "y",
                       tone=CORAL, scale=.42)
    plate.text((1440, 400), "eg · dz², dx²−y²", size=25, bold=True,
               fill=CORAL, anchor="rm")
    for x in (990, 1140, 1290):
        plate.draw.line((x - 43, 650, x + 43, 650), fill=GREEN, width=8)
    plate.text((1440, 610), "t₂g · dxy, dxz, dyz", size=25, bold=True,
               fill=GREEN, anchor="rm")
    _bracket(plate, 940, 352, 650, "Δo", tone=GOLD, side="left")
    _center_text(plate, (965, 700, 1445, 766),
                 "eg lobes point toward ligands; t₂g lobes point between axes",
                 size=24, bold=True, fill=INK)
    _footer(plate, content)


def _gaussian(x: float, centre: float, width: float, height: float) -> float:
    return height * math.exp(-.5 * ((x - centre) / width) ** 2)


def draw_analytical(plate: SciencePlate, content: Mapping[str, object]) -> None:
    """Chromatographic separation plus calibration and uncertainty."""
    chrom = (135, 285, 850, 650)
    point = _plot_axes(
        plate, chrom, "", "signal",
        x_ticks=((0, "0"), (.25, "2.5"), (.5, "5.0"), (.75, "7.5"), (1, "10")),
    )
    curve = []
    for index in range(241):
        x = 10 * index / 240
        signal = (.035 + _gaussian(x, 2.4, .16, .42)
                  + _gaussian(x, 5.2, .28, .86)
                  + _gaussian(x, 8.2, .20, .30))
        curve.append(point(x / 10, min(.96, signal)))
    _polyline(plate, curve, tone=TEAL, width=7)
    for time, label, tone in ((2.4, "A", BLUE), (5.2, "B", CORAL), (8.2, "C", PLUM)):
        x = point(time / 10, 0)[0]
        plate.draw.line((x, point(0, 0)[1], x, point(0, .91)[1]),
                        fill=hex_rgba(tone, 115), width=3)
        _tag(plate, (x, 250), f"{label} · tR {time:.1f}", tone, size=24)
    # Integration hatch under B explicitly encodes area, not peak height.
    b_points = []
    for index in range(45):
        x = 4.55 + index * (1.3 / 44)
        y = .035 + _gaussian(x, 5.2, .28, .86)
        b_points.append(point(x / 10, y))
    polygon = [point(4.55 / 10, .035), *b_points, point(5.85 / 10, .035)]
    plate.draw.polygon(polygon, fill=hex_rgba(CORAL, 52))
    plate.text((820, 715), "retention time / min", size=24, bold=True,
               fill=INK, anchor="rm")
    plate.text((505, 770), "identity: tR vs standard · amount: integrated area",
               size=24, bold=True, fill=INK, anchor="mm")

    # Calibration plot with independent standards and a sample interpolation.
    cal = (980, 330, 1460, 650)
    cal_pt = _plot_axes(
        plate, cal, "", "peak area",
        x_ticks=((0, "0"), (.5, "4"), (1, "8")),
        y_ticks=((0, "0"), (.5, "50"), (1, "100")),
    )
    standards = ((0, .04), (.25, .27), (.5, .49), (.75, .72), (1, .94))
    line = (cal_pt(0, .04), cal_pt(1, .94))
    _polyline(plate, line, tone=BLUE, width=6)
    for xf, yf in standards:
        # Squares distinguish standards from the round unknown.
        x, y = cal_pt(xf, yf)
        plate.draw.rectangle((x - 8, y - 8, x + 8, y + 8),
                             fill=BLUE, outline=INK, width=2)
    sample_x, sample_y = .625, .60
    sx, sy = cal_pt(sample_x, sample_y)
    _polyline(plate, (cal_pt(sample_x, 0), (sx, sy), cal_pt(0, sample_y)),
              tone=CORAL, width=4, dashed=True)
    plate.dot((sx, sy), 11, fill=CORAL, outline=INK, width=3)
    _tag(plate, (1220, 265), "CALIBRATION", BLUE)
    plate.text((1440, 715), "concentration / mg L−1", size=24, bold=True,
               fill=INK, anchor="rm")
    plate.text((1220, 755), "calibrated estimate ≈ 5.0 mg L−1", size=24,
               bold=True, fill=CORAL, anchor="mm")
    plate.text((1220, 790), "CI needs replicates + model uncertainty", size=24,
               fill=INK_SOFT, anchor="mm")
    _footer(plate, content)


def _phase_lobe(plate: SciencePlate, box: Box, sign: str, tone: str) -> None:
    plate.draw.ellipse(box, fill=hex_rgba(mix(tone, PAPER_LIGHT, .50), 230),
                       outline=tone, width=5)
    plate.text(((box[0] + box[2]) / 2, (box[1] + box[3]) / 2), sign,
               size=27, bold=True, fill=tone, anchor="mm")


def draw_quantum_chem(plate: SciencePlate, content: Mapping[str, object]) -> None:
    """Worked H2 MO construction with phase, occupancy, and bond order."""
    _surface(plate, (105, 215, 1495, 785), PLUM)
    plate.arrow((155, 730), (155, 275), fill=INK, width=5, head=18)
    plate.text((140, 255), "E", size=27, bold=True, anchor="mm")
    plate.text((310, 255), "H 1sA", size=25, bold=True, fill=BLUE, anchor="mm")
    plate.text((800, 255), "H₂ MOLECULAR ORBITALS", size=25, bold=True,
               fill=PLUM, anchor="mm")
    plate.text((1290, 255), "H 1sB", size=25, bold=True, fill=BLUE, anchor="mm")

    # AO and MO energy correlation lines.
    plate.draw.line((230, 510, 405, 510), fill=BLUE, width=8)
    plate.draw.line((1195, 510, 1370, 510), fill=BLUE, width=8)
    plate.draw.line((665, 340, 935, 340), fill=CORAL, width=8)
    plate.draw.line((665, 650, 935, 650), fill=GREEN, width=8)
    for start, end in (((405, 510), (665, 340)), ((405, 510), (665, 650)),
                       ((1195, 510), (935, 340)), ((1195, 510), (935, 650))):
        plate.draw.line((*start, *end), fill=hex_rgba(GRID, 190), width=4)
    _arrow(plate, (345, 504), (345, 465), tone=PLUM, width=4, head=12)
    _arrow(plate, (1255, 504), (1255, 465), tone=PLUM, width=4, head=12)

    # Antibonding: opposite phases separated by a node.
    plate.text((800, 307), "σu*(1s) · antibonding · empty", size=25,
               bold=True, fill=CORAL, anchor="mm")
    _phase_lobe(plate, (700, 376, 788, 443), "+", CORAL)
    _phase_lobe(plate, (812, 376, 900, 443), "−", BLUE)
    plate.draw.line((800, 366, 800, 452), fill=INK, width=4)
    plate.text((800, 472), "internuclear node", size=24, bold=True,
               fill=INK_SOFT, anchor="mm")

    # Bonding density is continuous between two explicit nuclei.
    plate.text((800, 610), "σg(1s) · bonding · ↑↓", size=25,
               bold=True, fill=GREEN, anchor="mm")
    plate.draw.rounded_rectangle((680, 680, 920, 746), radius=33,
                                 fill=hex_rgba(GREEN_LIGHT, 220),
                                 outline=GREEN, width=5)
    for nx in (765, 835):
        plate.dot((nx, 713), 8, fill=INK, outline=INK, width=1)
    plate.text((720, 713), "+", size=25, bold=True, fill=GREEN, anchor="mm")
    plate.text((880, 713), "+", size=25, bold=True, fill=GREEN, anchor="mm")
    plate.text((1080, 690), "bond order = (2 − 0) / 2 = 1", size=25,
               bold=True, fill=INK, anchor="mm")
    plate.text((1080, 733), "in-phase density stabilises H₂", size=24,
               fill=INK_SOFT, anchor="mm")
    _footer(plate, content)


def _electrode(plate: SciencePlate, box: Box, tone: str, metal: str,
               ion: str, *, solution_tone: str) -> None:
    x0, y0, x1, y1 = box
    plate.draw.rounded_rectangle(box, radius=20, fill=hex_rgba(BLUE_LIGHT, 95),
                                 outline=BLUE, width=4)
    liquid_y = y0 + 105
    plate.draw.rectangle((x0 + 4, liquid_y, x1 - 4, y1 - 4),
                         fill=hex_rgba(solution_tone, 90))
    plate.draw.rectangle((x0 + 85, y0 - 5, x0 + 145, y1 - 32),
                         fill=hex_rgba(tone, 215), outline=tone, width=4)
    plate.text((x0 + 115, y0 + 35), metal, size=27, bold=True,
               fill=INK, anchor="mm")
    for row in range(2):
        for col in range(2):
            _dot_pattern(plate, (x0 + 255 + col * 150, liquid_y + 62 + row * 94),
                         solution_tone, radius=31,
                         pattern="square" if row else "plain", label=ion)


def draw_electrochem(plate: SciencePlate, content: Mapping[str, object]) -> None:
    """A complete Daniell cell with electron and ion paths kept distinct."""
    _tag(plate, (800, 220), "DANIELL GALVANIC CELL · E°cell = +1.10 V", PLUM)
    left = (110, 390, 650, 730)
    right = (950, 390, 1490, 730)
    _electrode(plate, left, PLUM, "Zn", "Zn²⁺", solution_tone=PLUM)
    _electrode(plate, right, CORAL, "Cu", "Cu²⁺", solution_tone=BLUE)

    # External electron circuit and load.
    plate.draw.line((225, 385, 225, 300, 1375, 300, 1375, 385),
                    fill=INK, width=8, joint="curve")
    plate.draw.rounded_rectangle((710, 258, 890, 342), radius=18,
                                 fill=hex_rgba(GOLD_LIGHT, 225), outline=GOLD, width=5)
    plate.text((800, 300), "LOAD", size=27, bold=True, fill=INK, anchor="mm")
    _arrow(plate, (400, 300), (690, 300), tone=GOLD,
           label="e− through wire", label_at=(545, 253), width=7)
    _arrow(plate, (910, 300), (1200, 300), tone=GOLD, width=7)

    # Salt bridge carries ions, not electrons.
    plate.draw.arc((570, 420, 1030, 655), 180, 360, fill=TEAL, width=28)
    plate.draw.arc((588, 438, 1012, 637), 180, 360, fill=TEAL_LIGHT, width=18)
    _tag(plate, (800, 380), "KNO₃ salt bridge", TEAL)
    _arrow(plate, (750, 505), (625, 590), tone=BLUE,
           label="NO₃−", label_at=(665, 510), width=5, head=15)
    _arrow(plate, (850, 505), (975, 590), tone=CORAL,
           label="K+", label_at=(935, 510), width=5, head=15)

    plate.text((380, 750), "ANODE (−) · oxidation", size=25, bold=True,
               fill=PLUM, anchor="mm")
    plate.text((380, 782), "Zn → Zn²⁺ + 2e− · mass falls", size=24,
               fill=INK_SOFT, anchor="mm")
    plate.text((1220, 750), "CATHODE (+) · reduction", size=25, bold=True,
               fill=CORAL, anchor="mm")
    plate.text((1220, 782), "Cu²⁺ + 2e− → Cu · mass rises", size=24,
               fill=INK_SOFT, anchor="mm")
    _footer(plate, content)


def _enzyme(plate: SciencePlate, center: Point, *, occupied: bool,
            tone: str = PLUM, scale: float = 1.0) -> None:
    x, y = center
    r = 30 * scale
    plate.draw.arc((x - r, y - r, x + r, y + r), 35, 325,
                   fill=tone, width=max(5, int(7 * scale)))
    # Active-site notch and substrate triangle are explicit.
    plate.draw.line((x + r * .78, y - r * .34, x + r * .25, y),
                    fill=tone, width=max(4, int(6 * scale)))
    plate.draw.line((x + r * .78, y + r * .34, x + r * .25, y),
                    fill=tone, width=max(4, int(6 * scale)))
    if occupied:
        plate.draw.polygon(((x + r * .17, y), (x + r * .88, y - r * .30),
                            (x + r * .88, y + r * .30)),
                           fill=GOLD, outline=INK)


def draw_biochem(plate: SciencePlate, content: Mapping[str, object]) -> None:
    """Michaelis-Menten geometry joined to active-site occupancy."""
    graph = (160, 285, 970, 665)
    point = _plot_axes(
        plate, graph, "", "initial rate v",
        x_ticks=((0, "0"), (.25, "Km"), (.5, "2Km"), (1, "4Km")),
        y_ticks=((0, "0"), (.5, "Vmax/2"), (1, "Vmax")),
    )
    # Scale x as [S]/Km from 0..4; v/Vmax = x/(1+x).
    curve = []
    for index in range(101):
        scaled_s = 4 * index / 100
        velocity = scaled_s / (1 + scaled_s) if scaled_s else 0
        curve.append(point(index / 100, velocity))
    _polyline(plate, curve, tone=GREEN, width=9)
    _polyline(plate, (point(.25, 0), point(.25, .5), point(0, .5)),
              tone=PLUM, width=5, dashed=True)
    plate.dot(point(.25, .5), 11, fill=PLUM, outline=INK, width=3)
    plate.draw.line((*point(0, 1), *point(1, 1)), fill=CORAL, width=5)
    plate.text((565, 238), "v = Vmax[S] / (Km + [S])", size=28,
               bold=True, fill=GREEN, anchor="mm")
    plate.text((945, 742), "substrate concentration [S]", size=24,
               bold=True, fill=INK, anchor="rm")

    _surface(plate, (1060, 250, 1480, 750), TEAL)
    plate.text((1270, 290), "ACTIVE-SITE OCCUPANCY", size=24, bold=True,
               fill=TEAL, anchor="mm")
    plate.text((1120, 352), "low [S]", size=24, bold=True, fill=INK, anchor="mm")
    plate.text((1400, 352), "high [S]", size=24, bold=True, fill=INK, anchor="mm")
    low_states = (False, False, True, False, True, False)
    high_states = (True, True, True, False, True, True)
    for index, occupied in enumerate(low_states):
        _enzyme(plate, (1110 + (index % 2) * 85, 425 + (index // 2) * 90),
                occupied=occupied, tone=BLUE, scale=.78)
    for index, occupied in enumerate(high_states):
        _enzyme(plate, (1350 + (index % 2) * 85, 425 + (index // 2) * 90),
                occupied=occupied, tone=GREEN, scale=.78)
    _center_text(plate, (1090, 665, 1450, 735),
                 "Saturation makes v approach—not exceed—Vmax.",
                 size=24, bold=True, fill=INK)
    plate.text((1270, 770), "simple model · initial-rate · one substrate",
               size=24, fill=INK_SOFT, anchor="mm")
    _footer(plate, content)


def _polymer_chain(plate: SciencePlate, points: Sequence[Point], tone: str) -> None:
    plate.draw.line(list(points), fill=tone, width=7, joint="curve")
    for point in points:
        plate.dot(point, 8, fill=mix(tone, PAPER_LIGHT, .45), outline=tone, width=2)


def draw_materials(plate: SciencePlate, content: Mapping[str, object]) -> None:
    """Three structure-property mechanisms at molecule, nano, and band scales."""
    plate.draw.line((555, 225, 555, 770), fill=hex_rgba(GRID, 150), width=3)
    plate.draw.line((1045, 225, 1045, 770), fill=hex_rgba(GRID, 150), width=3)

    _tag(plate, (315, 230), "POLYMER NETWORK", BLUE)
    chains = (
        ((150, 350), (215, 325), (285, 365), (355, 330), (475, 365)),
        ((150, 470), (220, 500), (295, 455), (370, 500), (475, 470)),
        ((150, 600), (225, 570), (300, 615), (390, 575), (475, 610)),
    )
    for chain in chains:
        _polymer_chain(plate, chain, BLUE)
    for x, y0, y1 in ((250, 338, 480), (335, 480, 594), (420, 345, 590)):
        plate.draw.line((x, y0, x, y1), fill=CORAL, width=6)
        plate.dot((x, y0), 7, fill=CORAL, outline=INK, width=2)
        plate.dot((x, y1), 7, fill=CORAL, outline=INK, width=2)
    _arrow(plate, (165, 680), (460, 680), tone=BLUE, width=6, head=18)
    plate.text((315, 730), "crosslinks resist chain flow", size=24,
               bold=True, fill=INK, anchor="mm")

    _tag(plate, (800, 230), "NANOPARTICLE SURFACE", CORAL)
    # Equal total sphere volume: one radius-2r particle versus eight radius-r
    # particles, whose combined surface area is twice as large.
    plate.dot((680, 455), 56, fill=CORAL_LIGHT, outline=CORAL, width=6)
    # Highlight perimeter sites with repeated ticks.
    for angle in range(0, 360, 30):
        rad = math.radians(angle)
        point = (680 + math.cos(rad) * 56, 455 + math.sin(rad) * 56)
        plate.dot(point, 7, fill=GOLD, outline=INK, width=2)
    for index in range(8):
        row, col = divmod(index, 3)
        x, y = 820 + col * 70, 390 + row * 70
        plate.dot((x, y), 28, fill=CORAL_LIGHT, outline=CORAL, width=4)
        for angle in (0, 90, 180, 270):
            rad = math.radians(angle)
            plate.dot((x + math.cos(rad) * 28, y + math.sin(rad) * 28),
                      4, fill=GOLD, outline=GOLD, width=1)
    plate.text((800, 610), "same total volume → more exposed surface", size=24,
               bold=True, fill=INK, anchor="mm")
    plate.text((800, 650), "sphere surface/volume = 3/r", size=25,
               bold=True, fill=CORAL, anchor="mm")
    plate.text((800, 708), "interfaces can dominate reactivity", size=24,
               fill=INK_SOFT, anchor="mm")

    _tag(plate, (1285, 230), "n-TYPE SEMICONDUCTOR", PLUM)
    # Band diagram: donor level close to conduction band; band gap is retained.
    plate.draw.line((1110, 355, 1460, 355), fill=BLUE, width=16)
    plate.draw.line((1110, 625, 1460, 625), fill=CORAL, width=16)
    plate.draw.line((1135, 455, 1435, 455), fill=PLUM, width=7)
    plate.text((1285, 320), "conduction band", size=24, bold=True,
               fill=BLUE, anchor="mm")
    plate.text((1285, 660), "valence band", size=24, bold=True,
               fill=CORAL, anchor="mm")
    plate.text((1285, 492), "donor level", size=24, bold=True,
               fill=PLUM, anchor="mm")
    plate.dot((1270, 445), 10, fill=GOLD, outline=INK, width=2)
    _arrow(plate, (1270, 430), (1270, 372), tone=GOLD,
           label="thermal excitation", label_at=(1380, 402), width=5, head=14)
    _bracket(plate, 1090, 355, 625, "Eg", tone=TEAL, side="left")
    _center_text(plate, (1080, 690, 1490, 770),
                 "Dopant adds carriers; Eg is largely unchanged.",
                 size=24, bold=True, fill=INK)
    _footer(plate, content)


def _potential(theta: float) -> float:
    # Two minima over 0..360 degrees with a modest asymmetry.
    radians = math.radians(theta)
    return .46 - .28 * math.cos(2 * radians) + .06 * math.cos(radians)


def draw_compchem(plate: SciencePlate, content: Mapping[str, object]) -> None:
    """A torsional energy model exposing sampling and validation limits."""
    graph = (145, 300, 880, 650)
    point = _plot_axes(
        plate, graph, "", "model energy E(φ)",
        x_ticks=((0, "0°"), (.25, "90°"), (.5, "180°"), (.75, "270°"), (1, "360°")),
    )
    samples = []
    for index in range(181):
        theta = index * 2
        samples.append(point(theta / 360, _potential(theta)))
    _polyline(plate, samples, tone=PLUM, width=8)
    plate.text((265, 610), "minimum A", size=24, bold=True,
               fill=BLUE, anchor="mm")
    plate.text((515, 480), "minimum B", size=24, bold=True,
               fill=GREEN, anchor="mm")
    plate.text((330, 340), "barrier", size=24, bold=True,
               fill=CORAL, anchor="mm")
    plate.text((700, 340), "barrier", size=24, bold=True,
               fill=CORAL, anchor="mm")
    plate.text((515, 225), "FORCE FIELD / QUANTUM MODEL", size=25,
               bold=True, fill=PLUM, anchor="mm")

    # Finite samples are dots on the model surface; patterns show trapping.
    short_angles = (5, 15, 24, 340, 350, 358)
    broad_angles = (5, 38, 94, 155, 184, 220, 280, 340)
    for theta in short_angles:
        plate.dot(point(theta / 360, _potential(theta)), 8,
                  fill=CORAL, outline=INK, width=2)
    for theta in broad_angles:
        plate.draw.rectangle((point(theta / 360, _potential(theta))[0] - 6,
                              point(theta / 360, _potential(theta))[1] - 6,
                              point(theta / 360, _potential(theta))[0] + 6,
                              point(theta / 360, _potential(theta))[1] + 6),
                             fill=TEAL, outline=INK, width=2)
    plate.text((850, 715), "torsion angle φ", size=24, bold=True,
               fill=INK, anchor="rm")
    plate.text((510, 765), "● short run can remain trapped · ■ broader sampling crosses barrier",
               size=24, bold=True, fill=INK, anchor="mm")

    _surface(plate, (965, 245, 1480, 755), BLUE)
    _tag(plate, (1222, 280), "PREDICTION MUST SURVIVE", BLUE)
    # Predicted spectrum and independent measured points.
    mini = (1025, 410, 1425, 600)
    mini_pt = _plot_axes(plate, mini, "", "intensity")
    predicted = ((.05, .05), (.20, .08), (.28, .72), (.36, .08),
                 (.58, .10), (.67, .92), (.75, .12), (.95, .06))
    _polyline(plate, tuple(mini_pt(x, y) for x, y in predicted),
              tone=BLUE, width=6)
    measured = ((.27, .68), (.66, .86))
    for xf, yf in measured:
        x, y = mini_pt(xf, yf)
        plate.draw.rectangle((x - 8, y - 8, x + 8, y + 8),
                             fill=CORAL, outline=INK, width=2)
    plate.text((1250, 360), "line = model · ■ = test points", size=24,
               bold=True, fill=INK, anchor="mm")
    plate.text((1400, 650), "frequency", size=24, bold=True,
               fill=INK, anchor="rm")
    _center_text(plate, (1010, 680, 1440, 745),
                 "Check convergence and model uncertainty",
                 size=24, bold=True, fill=INK)
    _footer(plate, content)


def _cycle_arrow(plate: SciencePlate, box: Box, start: int, end: int,
                 tone: str) -> None:
    plate.draw.arc(box, start, end, fill=tone, width=8)
    angle = math.radians(end)
    cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
    rx, ry = (box[2] - box[0]) / 2, (box[3] - box[1]) / 2
    tip = (cx + math.cos(angle) * rx, cy + math.sin(angle) * ry)
    tangent = angle + math.pi / 2
    left = (tip[0] - math.cos(tangent - .55) * 22,
            tip[1] - math.sin(tangent - .55) * 22)
    right = (tip[0] - math.cos(tangent + .55) * 22,
             tip[1] - math.sin(tangent + .55) * 22)
    plate.draw.polygon((tip, left, right), fill=tone)


def draw_frontier(plate: SciencePlate, content: Mapping[str, object]) -> None:
    """A systems-boundary catalytic cycle with useful failure branches."""
    # Whole-process boundary: upstream burdens remain visible.
    plate.draw.rounded_rectangle((95, 210, 1505, 785), radius=30,
                                 fill=hex_rgba(PAPER_LIGHT, 105),
                                 outline=hex_rgba(PLUM, 170), width=4)
    plate.text((125, 238), "WHOLE-SYSTEM BOUNDARY", size=24, bold=True,
               fill=PLUM, anchor="la")

    # Central catalytic loop: catalyst must return, not be consumed.
    cx, cy = 790, 505
    _cycle_arrow(plate, (540, 300, 1040, 710), 205, 330, GREEN)
    _cycle_arrow(plate, (540, 300, 1040, 710), 25, 150, GREEN)
    states = ((790, 315, "CAT", PLUM), (1015, 505, "CAT·S", BLUE),
              (790, 695, "CAT", PLUM), (565, 505, "CAT·P", GREEN))
    for x, y, label, tone in states:
        _dot_pattern(plate, (x, y), tone, radius=45,
                     pattern="striped" if tone == PLUM else "plain")
        plate.text((x, y), label, size=24, bold=True, fill=INK, anchor="mm")
    plate.text((790, 490), "SELECTIVE", size=29, bold=True,
               fill=GREEN, anchor="mm")
    plate.text((790, 530), "CATALYTIC CYCLE", size=29, bold=True,
               fill=GREEN, anchor="mm")
    plate.text((790, 573), "TON · TOF · lifetime", size=24,
               fill=INK_SOFT, anchor="mm")

    # Inputs and intended output are material/energy flows, not decorative nodes.
    _arrow(plate, (120, 390), (520, 420), tone=BLUE,
           label="feedstock S", label_at=(300, 365))
    _arrow(plate, (120, 555), (520, 555), tone=GOLD,
           label="photon / electricity", label_at=(315, 515))
    _arrow(plate, (1060, 440), (1460, 375), tone=GREEN,
           label="desired P", label_at=(1270, 375))
    plate.text((1270, 475), "yield · selectivity · purity", size=24,
               bold=True, fill=INK, anchor="mm")

    # Failure paths remain inside accounting boundary and use blunt ends.
    plate.draw.line((1030, 565, 1320, 650), fill=CORAL, width=8)
    plate.draw.line((1320, 630, 1320, 670), fill=CORAL, width=9)
    _tag(plate, (1235, 600), "side products", CORAL)
    plate.draw.line((730, 700, 545, 755), fill=CORAL, width=8)
    plate.draw.line((540, 735, 550, 775), fill=CORAL, width=9)
    _tag(plate, (555, 755), "deactivation / leaching", CORAL)

    # Solvent/catalyst recycle is an explicit return stream.
    _polyline(plate, ((1420, 530), (1420, 730), (1100, 730), (1040, 655)),
              tone=TEAL, width=7, dashed=True)
    _arrow(plate, (1100, 730), (1040, 655), tone=TEAL, width=7, head=18)
    _tag(plate, (1305, 735), "solvent + catalyst recycle", TEAL)

    _center_text(plate, (125, 610, 535, 715),
                 "Include upstream energy, solvent, scarce elements and end-of-life",
                 size=24, fill=INK_SOFT)
    _footer(plate, content)


RENDERERS: Dict[str, Renderer] = {
    "chem.3.atomic-structure": draw_atomic_structure,
    "chem.3.bonding": draw_bonding,
    "chem.3.stoichiometry": draw_stoichiometry,
    "chem.3.reactions": draw_reactions,
    "chem.3.gases": draw_gases,
    "chem.3.energy": draw_energy,
    "chem.3.organic-intro": draw_organic_intro,
    "chem.4.physical": draw_physical,
    "chem.4.organic": draw_organic,
    "chem.4.inorganic": draw_inorganic,
    "chem.4.analytical": draw_analytical,
    "chem.4.quantum-chem": draw_quantum_chem,
    "chem.4.electrochem": draw_electrochem,
    "chem.5.biochem": draw_biochem,
    "chem.5.materials": draw_materials,
    "chem.5.compchem": draw_compchem,
    "chem.5.frontier": draw_frontier,
}
