"""Bespoke field-guide plates for advanced, generator-owned biology lessons.

The shared natural-science layouts are useful for broad inventories, but the
later biology lessons depend on spatial mechanisms: material crosses a
membrane, alleles change frequency, ions cross an axon, and evidence separates
competing hypotheses.  These renderers put those mechanisms in the picture.

Every renderer is deterministic, takes the same ``(plate, content)`` arguments
as the shared layout functions, and draws only with the repository's Primer
palette and Pillow primitives.  ``RENDERERS`` is intentionally keyed by lesson
id so importing code can register the set without changing chemistry or Earth
science plates.
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


def _panel(plate: SciencePlate, box: Box, tone: str = GREEN, *, alpha: int = 232,
           radius: int = 24) -> None:
    plate.card(
        box,
        fill=hex_rgba(mix(tone, PAPER_LIGHT, .84), alpha),
        outline=hex_rgba(tone, 210),
        width=4,
        radius=radius,
    )


def _tag(plate: SciencePlate, center: Point, value: str, tone: str = GREEN,
         *, size: int = 24, text_fill: str = PAPER_LIGHT) -> None:
    size = max(24, size)
    face = _science_font(value, size, bold=True)
    left, top, right, bottom = plate.draw.textbbox(center, value, font=face, anchor="mm")
    plate.draw.rounded_rectangle(
        (left - 16, top - 9, right + 16, bottom + 9),
        radius=15,
        fill=hex_rgba(tone, 238),
    )
    plate.text(center, value, size=size, bold=True, fill=text_fill, anchor="mm")


def _center_text(plate: SciencePlate, box: Box, value: str, *, size: int = 26,
                 bold: bool = False, fill: str = INK, line_gap: int = 7) -> None:
    size = max(24, size)
    x0, y0, x1, y1 = box
    face = _science_font(value, size, bold=bold)
    words = value.split()
    lines = []
    line = ""
    for word in words:
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


def _footer(plate: SciencePlate, value: str) -> None:
    """Render the inherited takeaway at a legible two-line floor."""
    plate.draw.rounded_rectangle(
        (165, 808, 1435, 890),
        radius=24,
        fill=hex_rgba(plate.domain_accent, 34),
        outline=hex_rgba(plate.domain_accent, 125),
        width=3,
    )
    _center_text(plate, (195, 814, 1405, 884), value, size=26,
                 bold=True, fill=INK, line_gap=6)


def _arrow(plate: SciencePlate, start: Point, end: Point, label: str,
           tone: str = GREEN, *, label_center: Point | None = None,
           size: int = 24, width: int = 8) -> None:
    plate.arrow(start, end, fill=tone, width=width, head=22)
    if label:
        center = label_center or ((start[0] + end[0]) / 2,
                                  (start[1] + end[1]) / 2 - 24)
        _tag(plate, center, label, tone, size=size)


def _inhibition(plate: SciencePlate, start: Point, end: Point, label: str,
                tone: str = CORAL, *, label_center: Point | None = None) -> None:
    x0, y0 = start
    x1, y1 = end
    plate.draw.line((x0, y0, x1, y1), fill=tone, width=8)
    angle = math.atan2(y1 - y0, x1 - x0)
    px, py = -math.sin(angle), math.cos(angle)
    plate.draw.line((x1 - px * 18, y1 - py * 18,
                     x1 + px * 18, y1 + py * 18), fill=tone, width=9)
    _tag(plate, label_center or ((x0 + x1) / 2, (y0 + y1) / 2 - 22),
         label, tone, size=24)


def _dna(plate: SciencePlate, box: Box, *, left: str = PLUM,
         right: str = CORAL, rungs: bool = True) -> None:
    x0, y0, x1, y1 = box
    mid = (x0 + x1) / 2
    amplitude = (x1 - x0) * .28
    count = 28
    first = []
    second = []
    for index in range(count + 1):
        fraction = index / count
        y = y0 + fraction * (y1 - y0)
        x = mid + math.sin(fraction * math.pi * 4) * amplitude
        mirror = 2 * mid - x
        first.append((x, y))
        second.append((mirror, y))
        if rungs and index % 3 == 0:
            plate.draw.line((x, y, mirror, y), fill=hex_rgba(GRID, 230), width=4)
    plate.draw.line(first, fill=left, width=8, joint="curve")
    plate.draw.line(second, fill=right, width=8, joint="curve")


def _chromosome(plate: SciencePlate, center: Point, *, size: float = 100,
                tone: str = PLUM, allele: str | None = None) -> None:
    x, y = center
    r = size / 2
    pale = mix(tone, PAPER_LIGHT, .58)
    for direction in (-1, 1):
        points = [
            (x, y),
            (x + direction * r * .44, y - r * .48),
            (x + direction * r * .34, y - r),
        ]
        plate.draw.line(points, fill=hex_rgba(tone, 245), width=max(7, int(r * .18)), joint="curve")
        points = [
            (x, y),
            (x + direction * r * .46, y + r * .47),
            (x + direction * r * .36, y + r),
        ]
        plate.draw.line(points, fill=hex_rgba(pale, 255), width=max(7, int(r * .18)), joint="curve")
    plate.dot((x, y), max(7, r * .13), fill=GOLD_LIGHT, outline=GOLD, width=3)
    if allele:
        plate.text((x + r * .63, y - r * .52), allele, size=30, bold=True,
                   fill=tone, anchor="mm")


def _chromatid(plate: SciencePlate, center: Point, *, height: float = 145,
               tone: str = PLUM, allele: str, locus_fraction: float = .43) -> None:
    """Draw one unreplicated chromosome with an explicit allele locus."""
    x, y = center
    half = height / 2
    plate.draw.rounded_rectangle(
        (x - 18, y - half, x + 18, y + half),
        radius=18,
        fill=hex_rgba(mix(tone, PAPER_LIGHT, .42), 245),
        outline=tone,
        width=5,
    )
    locus_y = y - half + height * locus_fraction
    plate.draw.line((x - 24, locus_y, x + 24, locus_y), fill=INK, width=7)
    plate.draw.ellipse((x - 8, locus_y - 8, x + 8, locus_y + 8),
                       fill=GOLD_LIGHT, outline=GOLD, width=3)
    plate.text((x + 50, locus_y), allele, size=30, bold=True,
               fill=INK, anchor="mm")


def _allele_legend(plate: SciencePlate, center: Point, *, tone: str = GREEN) -> None:
    """Key allele states by surface pattern, so colour is never the sole cue."""
    x, y = center
    _beetle(plate, (x - 92, y), size=48, tone=tone, marked=False)
    plate.text((x - 58, y), "plain A", size=24, bold=True, fill=INK, anchor="lm")
    _beetle(plate, (x + 82, y), size=48, tone=tone, marked=True)
    plate.text((x + 116, y), "spotted a", size=24, bold=True, fill=INK, anchor="lm")


def _allele_bar(plate: SciencePlate, box: Box, spotted_fraction: float,
                label: str, *, tone: str = GREEN) -> None:
    """Show allele frequency with fill extent plus repeated spot marks."""
    x0, y0, x1, y1 = box
    split = x0 + (x1 - x0) * spotted_fraction
    plate.draw.rounded_rectangle(box, radius=12, fill=hex_rgba(GREEN_LIGHT, 190),
                                 outline=tone, width=3)
    plate.draw.rounded_rectangle((x0, y0, max(x0 + 12, split), y1), radius=12,
                                 fill=hex_rgba(mix(tone, PAPER_LIGHT, .48), 235))
    dot_x = x0 + 14
    while dot_x < split - 7:
        plate.dot((dot_x, (y0 + y1) / 2), 4, fill=GOLD, outline=INK, width=1)
        dot_x += 22
    plate.text(((x0 + x1) / 2, (y0 + y1) / 2), label, size=24,
               bold=True, fill=INK, anchor="mm")


def _cell(plate: SciencePlate, center: Point, *, rx: float = 110, ry: float = 82,
          tone: str = TEAL, nucleus: bool = True) -> None:
    x, y = center
    plate.draw.ellipse((x - rx, y - ry, x + rx, y + ry),
                       fill=hex_rgba(mix(tone, PAPER_LIGHT, .72), 235),
                       outline=tone, width=6)
    plate.draw.ellipse((x - rx + 12, y - ry + 12, x + rx - 12, y + ry - 12),
                       outline=hex_rgba(tone, 120), width=3)
    if nucleus:
        nr = min(rx, ry) * .36
        plate.draw.ellipse((x - nr, y - nr, x + nr, y + nr),
                           fill=hex_rgba(PLUM_LIGHT, 230), outline=PLUM, width=5)


def _mitochondrion(plate: SciencePlate, center: Point, *, scale: float = 1.0) -> None:
    x, y = center
    rx, ry = 70 * scale, 37 * scale
    plate.draw.ellipse((x - rx, y - ry, x + rx, y + ry),
                       fill=hex_rgba(GOLD_LIGHT, 235), outline=GOLD, width=max(4, int(5 * scale)))
    points = []
    for index in range(17):
        fraction = index / 16
        points.append((x - rx * .72 + fraction * rx * 1.44,
                       y + math.sin(fraction * math.pi * 5) * ry * .42))
    plate.draw.line(points, fill=CORAL, width=max(3, int(4 * scale)), joint="curve")


def _protein(plate: SciencePlate, start: Point, *, count: int = 7,
             spacing: float = 27) -> None:
    colors = (BLUE, CORAL, GOLD, GREEN, PLUM, TEAL)
    points = []
    for index in range(count):
        x = start[0] + index * spacing
        y = start[1] + math.sin(index * 1.25) * 19
        points.append((x, y))
    plate.draw.line(points, fill=INK_SOFT, width=6, joint="curve")
    for index, point in enumerate(points):
        plate.dot(point, 12, fill=colors[index % len(colors)], outline=PAPER_LIGHT, width=3)


def _leaf(plate: SciencePlate, center: Point, *, size: float = 100,
          tone: str = GREEN) -> None:
    x, y = center
    r = size / 2
    box = (x - r, y - r * .62, x + r, y + r * .62)
    plate.draw.ellipse(box, fill=hex_rgba(GREEN_LIGHT, 235), outline=tone, width=6)
    plate.draw.line((x - r * .82, y + r * .42, x + r * .82, y - r * .42),
                    fill=tone, width=6)
    for fraction in (-.45, -.1, .25, .55):
        px = x + fraction * r
        py = y - fraction * r * .42
        plate.draw.line((px, py, px - r * .28, py - r * .25), fill=tone, width=3)
        plate.draw.line((px, py, px + r * .22, py + r * .27), fill=tone, width=3)


def _beetle(plate: SciencePlate, center: Point, *, size: float = 70,
            tone: str = GREEN, marked: bool = False) -> None:
    x, y = center
    r = size / 2
    pale = mix(tone, PAPER_LIGHT, .42)
    plate.draw.ellipse((x - r * .62, y - r * .72, x + r * .62, y + r * .68),
                       fill=hex_rgba(pale, 245), outline=tone, width=4)
    plate.draw.ellipse((x - r * .43, y - r, x + r * .43, y - r * .48),
                       fill=hex_rgba(tone, 235), outline=tone, width=3)
    plate.draw.line((x, y - r * .65, x, y + r * .56), fill=tone, width=3)
    for dy in (-.35, .05, .42):
        plate.draw.line((x - r * .5, y + dy * r, x - r, y + (dy - .17) * r),
                        fill=INK_SOFT, width=3)
        plate.draw.line((x + r * .5, y + dy * r, x + r, y + (dy - .17) * r),
                        fill=INK_SOFT, width=3)
    if marked:
        for dx, dy in ((-.24, -.18), (.24, -.18), (-.22, .27), (.22, .27)):
            plate.dot((x + dx * r, y + dy * r), 4, fill=GOLD, outline=GOLD, width=1)


def _virus(plate: SciencePlate, center: Point, *, size: float = 80,
           tone: str = CORAL) -> None:
    x, y = center
    r = size / 2
    plate.draw.ellipse((x - r * .46, y - r * .46, x + r * .46, y + r * .46),
                       fill=hex_rgba(CORAL_LIGHT, 240), outline=tone, width=5)
    for angle in range(0, 360, 45):
        rad = math.radians(angle)
        start = (x + math.cos(rad) * r * .46, y + math.sin(rad) * r * .46)
        end = (x + math.cos(rad) * r * .82, y + math.sin(rad) * r * .82)
        plate.draw.line((*start, *end), fill=tone, width=4)
        plate.dot(end, 5, fill=tone, outline=tone, width=1)


def _antibody(plate: SciencePlate, center: Point, *, size: float = 78,
              tone: str = PLUM) -> None:
    x, y = center
    r = size / 2
    plate.draw.line((x, y + r, x, y), fill=tone, width=9)
    plate.draw.line((x, y, x - r * .72, y - r), fill=tone, width=9)
    plate.draw.line((x, y, x + r * .72, y - r), fill=tone, width=9)
    for px in (x - r * .72, x + r * .72):
        plate.draw.line((px - 8, y - r - 5, px + 8, y - r + 5), fill=GOLD, width=5)


def _mini_bar(plate: SciencePlate, box: Box, fraction: float, tone: str,
              label: str) -> None:
    x0, y0, x1, y1 = box
    plate.draw.rounded_rectangle(box, radius=12, fill=hex_rgba(GRID, 95),
                                 outline=hex_rgba(INK_SOFT, 100), width=2)
    plate.draw.rounded_rectangle((x0, y0, x0 + max(12, (x1 - x0) * fraction), y1),
                                 radius=12, fill=hex_rgba(tone, 235))
    plate.text(((x0 + x1) / 2, (y0 + y1) / 2), label, size=24, bold=True,
               fill=INK, anchor="mm")


def draw_genetics(plate: SciencePlate, content: Mapping[str, object]) -> None:
    _panel(plate, (110, 220, 500, 790), BLUE)
    _panel(plate, (590, 220, 1010, 790), PLUM)
    _panel(plate, (1100, 220, 1490, 790), GREEN)
    _tag(plate, (305, 260), "HAPLOID GAMETES", BLUE)

    # Gametes carry one unreplicated homolog apiece: a single chromatid, not X.
    for center, tone, allele, label in (
        ((305, 405), BLUE, "A", "egg · one homolog"),
        ((305, 635), CORAL, "a", "sperm · one homolog"),
    ):
        plate.draw.ellipse((center[0] - 115, center[1] - 82,
                            center[0] + 115, center[1] + 82),
                           fill=hex_rgba(mix(tone, PAPER_LIGHT, .72), 220),
                           outline=tone, width=5)
        _chromatid(plate, center, height=120, tone=PLUM, allele=allele)
        plate.text((305, center[1] + 112), label, size=24, bold=True,
                   fill=INK, anchor="mm")

    _tag(plate, (800, 260), "DIPLOID GENOTYPE Aa", PLUM)
    plate.draw.ellipse((665, 325, 935, 625), fill=hex_rgba(PLUM_LIGHT, 160),
                       outline=PLUM, width=6)
    # Homologs have equal length and loci at the same vertical coordinate.
    _chromatid(plate, (750, 475), height=205, tone=PLUM, allele="A")
    _chromatid(plate, (850, 475), height=205, tone=PLUM, allele="a")
    locus_y = 475 - 205 / 2 + 205 * .43
    plate.dashed_line((726, locus_y), (874, locus_y), fill=GOLD,
                      width=4, dash=10, gap=8)
    _tag(plate, (800, 625), "SAME LOCUS ON HOMOLOGS", GOLD,
         text_fill=INK)
    _dna(plate, (760, 655, 840, 750))

    _tag(plate, (1295, 260), "EXPRESSION → PHENOTYPE", GREEN)
    _protein(plate, (1145, 375), count=8, spacing=40)
    _center_text(plate, (1120, 402, 1470, 468),
                 "Alleles can alter protein activity", size=24,
                 bold=True, fill=CORAL)
    _leaf(plate, (1238, 585), size=155)
    plate.draw.ellipse((1350, 530, 1450, 630), fill=hex_rgba(GOLD_LIGHT, 215),
                       outline=GOLD, width=5)
    plate.text((1400, 580), "ENV", size=25, bold=True, fill=GOLD, anchor="mm")
    plate.double_arrow((1305, 585), (1340, 585), fill=GOLD, width=6)
    _center_text(plate, (1120, 670, 1470, 755),
                 "Genes and environment influence traits", size=24,
                 bold=True, fill=INK)

    _arrow(plate, (505, 500), (580, 500), "fertilisation", TEAL,
           label_center=(542, 445))
    _arrow(plate, (1015, 500), (1090, 500), "expression", CORAL,
           label_center=(1052, 560))
    _footer(plate, str(content["footer"]))


def draw_evolution(plate: SciencePlate, content: Mapping[str, object]) -> None:
    _panel(plate, (115, 225, 525, 770), BLUE)
    _panel(plate, (635, 225, 965, 770), GOLD)
    _panel(plate, (1075, 225, 1485, 770), GREEN)
    _tag(plate, (320, 265), "GENERATION 0", BLUE)
    _tag(plate, (800, 265), "ENVIRONMENTAL FILTER", GOLD)
    _tag(plate, (1280, 265), "GENERATION 5", GREEN)
    start_spotted = [False, True, False, False, True, False,
                     False, True, False, True, False, False]
    end_spotted = [True, True, False, True, True, True,
                   False, True, True, True, True, False]
    for index, marked in enumerate(start_spotted):
        _beetle(plate, (205 + (index % 3) * 115, 365 + (index // 3) * 105),
                size=64, tone=GREEN, marked=marked)
    for index, marked in enumerate(end_spotted):
        _beetle(plate, (1165 + (index % 3) * 115, 365 + (index // 3) * 105),
                size=64, tone=GREEN, marked=marked)
    plate.draw.rounded_rectangle((735, 350, 865, 565), radius=58,
                                 fill=hex_rgba(GOLD_LIGHT, 190), outline=GOLD, width=5)
    for x, y in ((755, 390), (800, 420), (845, 375), (775, 500), (830, 520)):
        plate.dot((x, y), 7, fill=GOLD, outline=INK, width=2)
    _beetle(plate, (800, 455), size=105, tone=GREEN, marked=True)
    plate.text((800, 595), "camouflage changes\nsurvival + reproduction", size=26,
               bold=True, fill=INK, anchor="mm")
    _allele_legend(plate, (720, 665), tone=GREEN)
    _allele_bar(plate, (155, 710, 485, 752), 4 / 12, "spotted a = 4 / 12")
    _allele_bar(plate, (1115, 710, 1445, 752), 9 / 12, "spotted a = 9 / 12")
    _arrow(plate, (530, 500), (625, 500), "selection", GOLD,
           label_center=(578, 450))
    _arrow(plate, (970, 500), (1065, 500), "inherit", GREEN,
           label_center=(1018, 450))
    _footer(plate, str(content["footer"]))


def draw_cell_biology(plate: SciencePlate, content: Mapping[str, object]) -> None:
    _panel(plate, (115, 220, 995, 790), TEAL)
    _panel(plate, (1050, 220, 1485, 790), GREEN)
    _tag(plate, (555, 260), "COMPARTMENTALISED EUKARYOTIC CELL", TEAL)
    plate.draw.ellipse((195, 300, 915, 735), fill=hex_rgba(TEAL_LIGHT, 150),
                       outline=TEAL, width=9)
    plate.draw.ellipse((215, 320, 895, 715), outline=hex_rgba(TEAL, 135), width=4)
    plate.draw.ellipse((330, 390, 585, 645), fill=hex_rgba(PLUM_LIGHT, 220),
                       outline=PLUM, width=7)
    _dna(plate, (410, 430, 505, 600))
    _tag(plate, (457, 665), "NUCLEUS · DNA", PLUM)
    _mitochondrion(plate, (690, 420), scale=1.05)
    # A transcript exits through a nuclear pore and is read by ribosomes.
    transcript = [(585, 500), (635, 525), (685, 555), (740, 590), (825, 610)]
    plate.draw.line(transcript, fill=PLUM, width=7, joint="curve")
    plate.draw.ellipse((574, 485, 598, 515), fill=PAPER_LIGHT,
                       outline=TEAL, width=5)
    for center in ((685, 555), (740, 590), (800, 607)):
        plate.draw.ellipse((center[0] - 20, center[1] - 13,
                           center[0] + 20, center[1] + 13),
                          fill=hex_rgba(CORAL_LIGHT, 235), outline=CORAL, width=4)
    _tag(plate, (680, 505), "mRNA exits pore", PLUM)
    _tag(plate, (755, 665), "ribosomes translate", CORAL, size=25)
    _arrow(plate, (835, 605), (1040, 430), "protein", CORAL,
           label_center=(930, 500))
    plate.text((855, 355), "selective\nmembrane", size=25, bold=True,
               fill=TEAL, anchor="mm")

    _tag(plate, (1268, 260), "COUPLED OUTPUTS", GREEN)
    _protein(plate, (1110, 385), count=7, spacing=43)
    plate.text((1268, 440), "proteins build + regulate", size=25,
               bold=True, fill=CORAL, anchor="mm")
    _mitochondrion(plate, (1195, 575), scale=1.25)
    _tag(plate, (1370, 575), "ATP", GOLD, size=26)
    _arrow(plate, (1268, 620), (1268, 675), "cell work", GREEN,
           label_center=(1370, 650), size=24)
    plate.draw.rounded_rectangle((1110, 688, 1425, 750), radius=18,
                                 fill=hex_rgba(GREEN_LIGHT, 225), outline=GREEN, width=4)
    plate.text((1268, 719), "growth · repair · division", size=25,
               bold=True, fill=GREEN, anchor="mm")
    plate.text((555, 752), "information, matter, and energy converge on cell work",
               size=24, bold=True, fill=INK, anchor="mm")
    _footer(plate, str(content["footer"]))


def draw_ecology(plate: SciencePlate, content: Mapping[str, object]) -> None:
    _panel(plate, (115, 220, 1485, 790), GREEN)
    _tag(plate, (800, 250), "CARBON FLUXES · ARROWS SHOW TRANSFER", GREEN)
    plate.draw.rounded_rectangle((630, 300, 970, 390), radius=38,
                                 fill=hex_rgba(BLUE_LIGHT, 205), outline=BLUE, width=5)
    plate.text((800, 345), "ATMOSPHERE · CO₂", size=30, bold=True,
               fill=BLUE, anchor="mm")
    _leaf(plate, (300, 515), size=190)
    _tag(plate, (300, 650), "PRODUCERS", GREEN)
    _beetle(plate, (740, 525), size=145, tone=CORAL, marked=True)
    _tag(plate, (740, 650), "CONSUMERS", CORAL)
    plate.draw.ellipse((1150, 435, 1370, 625), fill=hex_rgba(PLUM_LIGHT, 190),
                       outline=PLUM, width=6)
    for center in ((1200, 485), (1295, 500), (1235, 560), (1320, 565)):
        plate.draw.ellipse((center[0] - 28, center[1] - 16,
                           center[0] + 28, center[1] + 16),
                          fill=hex_rgba(PLUM, 215), outline=PLUM, width=3)
    _tag(plate, (1260, 650), "DECOMPOSERS", PLUM)
    _arrow(plate, (630, 345), (270, 430), "photosynthesis", GREEN,
           label_center=(365, 335), size=22)
    _arrow(plate, (405, 515), (655, 525), "feeding", CORAL,
           label_center=(530, 480), size=22)
    _arrow(plate, (825, 540), (1140, 540), "waste + remains", PLUM,
           label_center=(985, 500), size=22)
    for start, end, label in (((325, 435), (700, 390), (510, 450)),
                              ((740, 445), (800, 400), (900, 435)),
                              ((1260, 435), (930, 390), (1330, 405))):
        plate.arrow(start, end, fill=GOLD, width=6, head=18)
        plate.text(label, "respiration", size=24, bold=True,
                   fill=GOLD, anchor="mm")
    plate.draw.line((185, 730, 1415, 730), fill=hex_rgba(GRID, 150), width=3)
    plate.text((800, 755), "ENERGY LEAVES AS HEAT · MATTER CONTINUES CYCLING",
               size=25, bold=True, fill=INK, anchor="mm")
    _footer(plate, str(content["footer"]))


def draw_microbiology(plate: SciencePlate, content: Mapping[str, object]) -> None:
    _panel(plate, (115, 220, 1485, 790), CORAL)
    x_positions = (220, 560, 930, 1300)
    labels = ("0 h · EXPOSURE", "HOURS · INNATE", "DAYS · ADAPTIVE", "LATER · MEMORY")
    tones = (CORAL, GOLD, PLUM, GREEN)
    for x, label, tone in zip(x_positions, labels, tones):
        _tag(plate, (x, 265), label, tone, size=22)
    plate.draw.line((180, 735, 1360, 735), fill=INK, width=6)
    for x, value in zip(x_positions, ("start", "hours", "days", "later")):
        plate.draw.line((x, 720, x, 752), fill=INK, width=5)
        plate.text((x, 770), value, size=24, bold=True, fill=INK, anchor="mm")

    _virus(plate, (200, 450), size=125)
    plate.draw.rounded_rectangle((120, 565, 320, 600), radius=16,
                                 fill=hex_rgba(TEAL_LIGHT, 230), outline=TEAL, width=4)
    plate.text((220, 582), "body barrier", size=25, bold=True, fill=TEAL, anchor="mm")
    plate.arrow((220, 510), (220, 560), fill=CORAL, width=7, head=18)

    _cell(plate, (560, 485), rx=110, ry=90, tone=GOLD, nucleus=False)
    _virus(plate, (560, 485), size=62)
    plate.text((560, 620), "phagocyte engulfs", size=25, bold=True,
               fill=GOLD, anchor="mm")

    _cell(plate, (865, 430), rx=66, ry=66, tone=PLUM)
    for center in ((835, 560), (900, 560), (965, 560),
                   (865, 630), (935, 630), (1005, 630)):
        _cell(plate, center, rx=28, ry=28, tone=PLUM, nucleus=True)
    plate.text((930, 690), "lymphocyte clone expands", size=24, bold=True,
               fill=PLUM, anchor="mm")

    for center in ((1240, 430), (1330, 470), (1240, 550), (1340, 595)):
        _cell(plate, center, rx=48, ry=40, tone=GREEN)
    plate.draw.rounded_rectangle((1185, 655, 1420, 700), radius=18,
                                 fill=hex_rgba(GREEN_LIGHT, 220), outline=GREEN, width=4)
    plate.text((1302, 677), "memory persists", size=24, bold=True,
               fill=GREEN, anchor="mm")
    for left, right, label, tone in ((300, 445, "breach", CORAL),
                                      (670, 805, "antigen", GOLD),
                                      (1050, 1160, "memory fate", GREEN)):
        _arrow(plate, (left, 500), (right, 500), label, tone,
               label_center=((left + right) / 2, 455), size=22)
    _footer(plate, str(content["footer"]))


def draw_botany(plate: SciencePlate, content: Mapping[str, object]) -> None:
    _panel(plate, (115, 220, 1010, 790), GREEN)
    _panel(plate, (1050, 220, 1485, 790), TEAL)
    _tag(plate, (560, 255), "WHOLE-PLANT TRANSPORT", GREEN)
    plate.draw.rectangle((145, 650, 980, 760), fill=hex_rgba(GOLD_LIGHT, 135),
                         outline=GOLD, width=3)
    plate.text((180, 675), "SOIL", size=25,
               bold=True, fill=GOLD, anchor="lm")
    plate.text((180, 735), "water + ions", size=25,
               bold=True, fill=GOLD, anchor="lm")
    plate.draw.line((560, 650, 560, 355), fill=GREEN, width=28)
    for dx in (-150, -90, -35, 35, 90, 150):
        plate.draw.line((560, 650, 560 + dx, 745), fill=GOLD, width=8)
    _leaf(plate, (420, 400), size=220)
    _leaf(plate, (700, 350), size=220)
    _leaf(plate, (745, 520), size=190)
    plate.draw.line((538, 640, 538, 355), fill=BLUE, width=10)
    plate.arrow((538, 620), (538, 365), fill=BLUE, width=10, head=24)
    plate.draw.line((582, 365, 582, 640), fill=CORAL, width=10)
    plate.arrow((582, 385), (582, 625), fill=CORAL, width=10, head=24)
    _tag(plate, (350, 570), "XYLEM ↑ WATER", BLUE, size=22)
    _tag(plate, (775, 635), "PHLOEM ↕ SUGAR", CORAL, size=22)
    plate.arrow((250, 705), (500, 630), fill=BLUE, width=7, head=20)
    plate.arrow((705, 390), (600, 470), fill=CORAL, width=7, head=20)

    _tag(plate, (1268, 255), "STOMA TRADE-OFF", TEAL)
    _leaf(plate, (1268, 405), size=220)
    plate.draw.ellipse((1218, 375, 1255, 455), fill=hex_rgba(GREEN_LIGHT, 230),
                       outline=GREEN, width=5)
    plate.draw.ellipse((1281, 375, 1318, 455), fill=hex_rgba(GREEN_LIGHT, 230),
                       outline=GREEN, width=5)
    plate.draw.ellipse((1257, 392, 1279, 438), fill=INK)
    plate.arrow((1170, 405), (1245, 415), fill=CORAL, width=7, head=18)
    plate.text((1130, 405), "CO₂ in", size=25, bold=True, fill=CORAL, anchor="rm")
    plate.arrow((1290, 370), (1370, 315), fill=BLUE, width=7, head=18)
    plate.text((1390, 295), "H₂O out", size=25, bold=True, fill=BLUE, anchor="mm")
    _center_text(plate, (1090, 535, 1445, 720),
                 "Guard cells balance carbon gain against water loss.",
                 size=28, bold=True, fill=INK)
    _footer(plate, str(content["footer"]))


def draw_biochemistry(plate: SciencePlate, content: Mapping[str, object]) -> None:
    """Reaction coordinates make the enzyme's kinetic role measurable."""
    _panel(plate, (115, 220, 1045, 790), GREEN)
    _panel(plate, (1080, 220, 1485, 790), CORAL)
    _tag(plate, (580, 250), "REACTION COORDINATE", GREEN)
    graph = (175.0, 310.0, 985.0, 715.0)
    x0, y0, x1, y1 = graph
    x_min, x_max = content.get("x_range", (0, 10))
    y_min, y_max = content.get("y_range", (0, 10))

    def point(x: float, y: float) -> Point:
        return (
            x0 + (x - float(x_min)) / (float(x_max) - float(x_min)) * (x1 - x0),
            y1 - (y - float(y_min)) / (float(y_max) - float(y_min)) * (y1 - y0),
        )

    for value in range(0, 11, 2):
        px, py = point(value, value)
        plate.draw.line((point(value, 0)[0], y0, point(value, 0)[0], y1),
                        fill=hex_rgba(GRID, 130), width=2)
        plate.draw.line((x0, point(0, value)[1], x1, point(0, value)[1]),
                        fill=hex_rgba(GRID, 130), width=2)
        if value in (0, 4, 8):
            plate.text((point(value, 0)[0], y1 + 25), str(value), size=24,
                       fill=INK_SOFT, anchor="mm")
            plate.text((x0 - 20, point(0, value)[1]), str(value), size=24,
                       fill=INK_SOFT, anchor="rm")
    plate.arrow((x0, y1), (x1, y1), fill=INK, width=5, head=18)
    plate.arrow((x0, y1), (x0, y0), fill=INK, width=5, head=18)
    plate.text(((x0 + x1) / 2, 770), "reaction progress", size=26,
               bold=True, fill=INK, anchor="mm")
    plate.text((185, 285), "free energy G", size=25, bold=True,
               fill=INK, anchor="lm")

    curves = list(content["curves"])
    for index, curve in enumerate(curves):
        tone = str(curve.get("color", (CORAL, GREEN)[index % 2]))
        points = [point(float(a), float(b)) for a, b in curve["points"]]
        plate.draw.line(points, fill=tone, width=9, joint="curve")
        for marked in points:
            plate.dot(marked, 6, fill=tone, outline=PAPER_LIGHT, width=2)
        _tag(plate, (735, 325 + index * 52), str(curve["label"]), tone, size=22)

    reactant_y = point(0, 7)[1]
    uncatalysed_peak = point(4, 9.2)[1]
    enzyme_peak = point(4, 7.8)[1]
    plate.double_arrow((390, reactant_y), (390, uncatalysed_peak), fill=CORAL, width=5)
    plate.text((365, (reactant_y + uncatalysed_peak) / 2), "higher barrier", size=24,
               bold=True, fill=CORAL, anchor="rm")
    plate.double_arrow((505, reactant_y), (505, enzyme_peak), fill=GREEN, width=5)
    plate.text((480, 460), "lower barrier", size=24,
               bold=True, fill=GREEN, anchor="rm")
    plate.double_arrow((900, point(10, 7)[1]), (900, point(10, 3)[1]),
                       fill=PLUM, width=5)
    plate.text((925, (point(10, 7)[1] + point(10, 3)[1]) / 2), "same ΔG",
               size=24, bold=True, fill=PLUM, anchor="lm")

    _tag(plate, (1282, 255), "ENZYME PATHWAY", CORAL)
    plate.draw.arc((1140, 335, 1335, 595), 55, 305, fill=GREEN, width=18)
    plate.draw.ellipse((1260, 415, 1365, 520), fill=hex_rgba(CORAL_LIGHT, 230),
                       outline=CORAL, width=6)
    plate.draw.pieslice((1282, 433, 1343, 495), 30, 210, fill=PAPER_LIGHT)
    plate.text((1280, 625), "transition state stabilised",
               size=26, bold=True, fill=GREEN, anchor="mm")
    _center_text(plate, (1110, 650, 1450, 760),
                 "Catalyst returns unchanged; equilibrium does not move.",
                 size=25, bold=True, fill=INK)
    _footer(plate, str(content["footer"]))


def draw_genomics(plate: SciencePlate, content: Mapping[str, object]) -> None:
    _panel(plate, (105, 225, 1495, 790), PLUM)
    boxes = ((125, 300, 425, 735), (465, 300, 765, 735),
             (805, 300, 1105, 735), (1145, 300, 1475, 735))
    headings = ("1 · SEQUENCE", "2 · ALIGN + CALL", "3 · TARGET EDIT", "4 · VALIDATE")
    tones = (BLUE, TEAL, PLUM, GREEN)
    for box, heading, tone in zip(boxes, headings, tones):
        _panel(plate, box, tone, alpha=242, radius=20)
        _tag(plate, ((box[0] + box[2]) / 2, box[1] + 32), heading, tone, size=22)

    # Overlapping reads contain a real alternate base, not a colour-only hint.
    reads = ("ACGTTG", "CGTTGC", "GTTGCA",
             "ACGTAG", "CGTAGC", "GTAGCA")
    for row, bases in enumerate(reads):
        y = 400 + row * 46
        offset = 150 + (row % 3) * 28
        plate.draw.rounded_rectangle((offset, y - 15, offset + 220, y + 15),
                                     radius=12, fill=hex_rgba(BLUE_LIGHT, 205),
                                     outline=BLUE, width=3)
        for index, base in enumerate(bases):
            tone = CORAL if base == "A" and row >= 3 and index in (3, 4) else INK
            plate.text((offset + 24 + index * 33, y), base, size=24,
                       bold=True, fill=tone, anchor="mm")
    plate.text((275, 695), "overlap + quality", size=25, bold=True,
               fill=BLUE, anchor="mm")

    reference_y = 445
    plate.text((615, 395), "REFERENCE", size=24, bold=True, fill=TEAL, anchor="mm")
    for index, base in enumerate("ACGTTGCA"):
        x = 500 + index * 32
        plate.text((x, reference_y), base, size=24, bold=True,
                   fill=CORAL if index == 4 else INK, anchor="mm")
        plate.draw.line((x, reference_y + 25, x, reference_y + 160),
                        fill=hex_rgba(GRID, 160), width=2)
    alt_x = 500 + 4 * 32
    for row in range(3):
        for index, base in enumerate("ACGTAGCA"):
            plate.text((500 + index * 32, 515 + row * 46), base, size=24,
                       bold=True, fill=CORAL if index == 4 else INK_SOFT, anchor="mm")
    # A box and pointer make the variant legible in monochrome as well as colour.
    plate.draw.rounded_rectangle((alt_x - 17, 485, alt_x + 17, 628),
                                 radius=10, outline=INK, width=4)
    plate.draw.polygon(((alt_x - 10, 648), (alt_x + 10, 648), (alt_x, 632)),
                       fill=INK)
    _tag(plate, (615, 685), "variant T → A · 3 / 3 reads", CORAL)

    _dna(plate, (835, 400, 900, 620))
    guide = [(930, 470), (970, 455), (1010, 470), (1050, 455)]
    plate.draw.line(guide, fill=TEAL, width=8, joint="curve")
    plate.text((990, 420), "guide RNA", size=24, bold=True, fill=TEAL, anchor="mm")
    plate.draw.ellipse((920, 500, 1060, 640), fill=hex_rgba(PLUM_LIGHT, 205),
                       outline=PLUM, width=7)
    plate.text((990, 570), "Cas", size=34, bold=True, fill=PLUM, anchor="mm")
    plate.draw.line((893, 525, 940, 565), fill=CORAL, width=8)
    plate.draw.line((893, 565, 940, 525), fill=CORAL, width=8)
    plate.text((955, 690), "match → cut → repair", size=25, bold=True,
               fill=PLUM, anchor="mm")

    plate.text((1310, 390), "INDEPENDENT ASSAYS", size=24, bold=True,
               fill=GREEN, anchor="mm")
    plate.text((1310, 430), "A · amplicon sequencing", size=24, bold=True,
               fill=BLUE, anchor="mm")
    # Read-count composition; hatching makes the edited fraction non-colour-only.
    assay_box = (1180, 458, 1440, 498)
    plate.draw.rounded_rectangle(assay_box, radius=12,
                                 fill=hex_rgba(BLUE_LIGHT, 185),
                                 outline=BLUE, width=3)
    plate.draw.rounded_rectangle((1180, 458, 1368, 498), radius=12,
                                 fill=hex_rgba(GREEN_LIGHT, 235))
    for x in range(1190, 1368, 20):
        plate.draw.line((x, 494, x + 22, 462), fill=GREEN, width=3)
    plate.text((1310, 520), "edited / unedited reads", size=24,
               bold=True, fill=INK, anchor="mm")

    plate.text((1310, 555), "B · phenotype + controls", size=24, bold=True,
               fill=PLUM, anchor="mm")
    plate.text((1310, 590), "normalised readout", size=24, bold=True,
               fill=INK, anchor="mm")
    ax0, ay0, ax1, ay1 = 1190, 660, 1435, 610
    plate.draw.line((ax0, ay0, ax1, ay0), fill=INK, width=4)
    plate.draw.line((ax0, ay0, ax0, ay1), fill=INK, width=4)
    for x, label, values, tone in (
        (1250, "control", (648, 641, 653), BLUE),
        (1370, "edited", (626, 618, 632), PLUM),
    ):
        plate.draw.line((x, min(values) - 8, x, max(values) + 8),
                        fill=tone, width=5)
        for value in values:
            plate.dot((x, value), 7, fill=PAPER_LIGHT, outline=tone, width=4)
        plate.text((x, 695), label, size=24, bold=True,
                   fill=tone, anchor="mm")

    for x, label, tone in ((430, "align", TEAL), (770, "interpret", PLUM),
                           (1110, "verify", GREEN)):
        _arrow(plate, (x + 2, 520), (x + 30, 520), "", tone, width=7)
    _footer(plate, str(content["footer"]))


def draw_neuroscience(plate: SciencePlate, content: Mapping[str, object]) -> None:
    _panel(plate, (110, 220, 1050, 790), BLUE)
    _panel(plate, (1085, 220, 1490, 790), PLUM)
    _tag(plate, (575, 250), "ACTION POTENTIAL · SCHEMATIC VOLTAGE", BLUE)
    x0, y0, x1, y1 = 175.0, 305.0, 995.0, 710.0
    x_min, x_max = content.get("x_range", (0, 10))
    y_min, y_max = content.get("y_range", (-90, 50))

    def point(x: float, y: float) -> Point:
        return (
            x0 + (x - float(x_min)) / (float(x_max) - float(x_min)) * (x1 - x0),
            y1 - (y - float(y_min)) / (float(y_max) - float(y_min)) * (y1 - y0),
        )

    for x_value in (0, 2, 4, 6, 8, 10):
        px = point(x_value, 0)[0]
        plate.draw.line((px, y0, px, y1), fill=hex_rgba(GRID, 130), width=2)
        plate.text((px, y1 + 26), str(x_value), size=24, fill=INK_SOFT, anchor="mm")
    for y_value in (-90, -70, -55, 0, 35):
        py = point(0, y_value)[1]
        plate.draw.line((x0, py, x1, py), fill=hex_rgba(GRID, 135), width=2)
        plate.text((x0 - 18, py), str(y_value), size=24, bold=y_value in (-70, -55),
                   fill=INK, anchor="rm")
    plate.arrow((x0, y1), (x1, y1), fill=INK, width=5, head=18)
    plate.arrow((x0, y1), (x0, y0), fill=INK, width=5, head=18)
    plate.text(((x0 + x1) / 2, 770), "time (ms)", size=26, bold=True,
               fill=INK, anchor="mm")
    plate.text((180, 280), "membrane potential (mV)", size=24, bold=True,
               fill=INK, anchor="lm")
    for curve in content["curves"]:
        tone = str(curve.get("color", BLUE))
        points = [point(float(a), float(b)) for a, b in curve["points"]]
        plate.draw.line(points, fill=tone, width=10, joint="curve")
    for value, label in ((-70, "REST"), (-55, "THRESHOLD")):
        py = point(0, value)[1]
        plate.dashed_line((x0, py), (x1, py), fill=BLUE if value == -70 else CORAL,
                          width=4, dash=16, gap=10)
        _tag(plate, (865, py - 24), label, BLUE if value == -70 else CORAL, size=20)
    _tag(plate, (455, 345), "Na⁺ IN · DEPOLARISE", GOLD, size=21)
    _tag(plate, (660, 390), "K⁺ OUT · REPOLARISE", CORAL, size=21)
    undershoot = point(5.2, -82)
    plate.arrow((690, 555), (undershoot[0] + 6, undershoot[1] - 6),
                fill=GREEN, width=5, head=15)
    _tag(plate, (805, 535), "UNDERSHOOT → RECOVERY", GREEN)

    _tag(plate, (1288, 255), "MEMBRANE MECHANISM", PLUM)
    plate.draw.rounded_rectangle((1120, 440, 1455, 520), radius=35,
                                 fill=hex_rgba(TEAL_LIGHT, 210), outline=TEAL, width=6)
    # Two explicit ion channels crossing a lipid bilayer.  Arrow shafts begin
    # and end on opposite sides, so the transport direction cannot be read as
    # motion merely toward a channel.
    for x, tone, ion, direction in ((1210, GOLD, "Na⁺", 1), (1370, CORAL, "K⁺", -1)):
        plate.draw.rectangle((x - 28, 420, x + 28, 540),
                             fill=hex_rgba(mix(tone, PAPER_LIGHT, .48), 245),
                             outline=tone, width=5)
        if direction > 0:
            plate.arrow((x, 365), (x, 585), fill=tone, width=7, head=18)
        else:
            plate.arrow((x, 585), (x, 365), fill=tone, width=7, head=18)
        plate.text((x, 330 if direction > 0 else 620), ion, size=30,
                   bold=True, fill=tone, anchor="mm")
    plate.text((1288, 620), "cytosol", size=24, bold=True,
               fill=INK_SOFT, anchor="mm")
    plate.text((1288, 385), "outside", size=24, bold=True,
               fill=INK_SOFT, anchor="mm")
    _center_text(plate, (1115, 655, 1460, 760),
                 "Voltage-gated Na⁺ channels amplify depolarisation; delayed K⁺ efflux repolarises.",
                 size=25, bold=True, fill=INK)
    _footer(plate, str(content["footer"]))


def draw_evolutionary_biology(plate: SciencePlate, content: Mapping[str, object]) -> None:
    _panel(plate, (110, 220, 1490, 790), BLUE)
    _tag(plate, (800, 250), "ONE GENE POOL · TWO DISTINCT MECHANISMS", BLUE)
    _panel(plate, (135, 310, 470, 735), PLUM, alpha=240)
    _tag(plate, (302, 345), "START", PLUM)
    for index, marked in enumerate((False, True, False, True,
                                    False, True, False, True)):
        _beetle(plate, (210 + (index % 2) * 185, 425 + (index // 2) * 62),
                size=48, tone=GREEN, marked=marked)
    plate.text((302, 635), "plain A  ·  spotted a", size=24,
               bold=True, fill=INK, anchor="mm")
    _allele_bar(plate, (175, 670, 430, 712), .5, "a = 4 / 8")

    _panel(plate, (620, 310, 950, 545), GREEN, alpha=240)
    _tag(plate, (785, 345), "SELECTION", GREEN)
    for index, marked in enumerate((True, True, True, True, True, False)):
        _beetle(plate, (680 + (index % 3) * 105, 410 + (index // 3) * 62),
                size=44, tone=GREEN, marked=marked)
    _allele_bar(plate, (660, 495, 910, 530), 5 / 6,
                "spotted a ↑ 5 / 6")

    _panel(plate, (620, 575, 950, 755), GOLD, alpha=240)
    _tag(plate, (785, 610), "DRIFT", GOLD)
    _allele_bar(plate, (650, 650, 920, 690), .80,
                "replicate 1 · a = .80")
    _allele_bar(plate, (650, 702, 920, 742), .20,
                "replicate 2 · a = .20")

    _panel(plate, (1090, 310, 1465, 755), TEAL, alpha=240)
    _tag(plate, (1278, 345), "PHYLOGENY", TEAL)
    # Conventional rectangular cladogram: internal nodes are branch points;
    # labels appear only at terminal tips, which are the observed taxa.
    plate.draw.line((1135, 530, 1200, 530), fill=TEAL, width=7)
    plate.draw.line((1200, 445, 1200, 615), fill=TEAL, width=7)
    for branch_y, top_y, bottom_y in ((445, 400, 480), (615, 570, 650)):
        plate.draw.line((1200, branch_y, 1265, branch_y), fill=TEAL, width=7)
        plate.draw.line((1265, top_y, 1265, bottom_y), fill=TEAL, width=7)
        plate.draw.line((1265, top_y, 1340, top_y), fill=TEAL, width=7)
        plate.draw.line((1265, bottom_y, 1340, bottom_y), fill=TEAL, width=7)
        plate.dot((1265, branch_y), 8, fill=GOLD_LIGHT, outline=GOLD, width=2)
    for y, label in ((400, "taxon A"), (480, "taxon B"),
                     (570, "taxon C"), (650, "taxon D")):
        plate.dot((1340, y), 8, fill=TEAL, outline=INK, width=2)
        plate.text((1360, y), label, size=24, bold=True,
                   fill=INK, anchor="lm")
    plate.text((1278, 710), "tips = sampled taxa", size=24,
               bold=True, fill=TEAL, anchor="mm")

    _arrow(plate, (480, 430), (610, 410), "fitness", GREEN,
           label_center=(545, 370), size=22)
    _arrow(plate, (480, 620), (610, 655), "sampling", GOLD,
           label_center=(545, 690), size=22)
    plate.text((1018, 475), "infer\nlineages", size=24,
               bold=True, fill=TEAL, anchor="mm")
    plate.arrow((965, 535), (1080, 535), fill=TEAL, width=8, head=22)
    _footer(plate, str(content["footer"]))


def draw_physiology(plate: SciencePlate, content: Mapping[str, object]) -> None:
    _panel(plate, (110, 220, 1490, 790), CORAL)
    _tag(plate, (800, 250), "NEGATIVE FEEDBACK · HEAT-LOSS RESPONSE", CORAL)
    centers = ((280, 475), (610, 410), (990, 410), (1320, 475), (800, 680))
    labels = ("TEMP RISE", "SENSORS", "CONTROL CENTRE",
              "HEAT LOSS", "TEMP FALLS")
    tones = (GOLD, BLUE, PLUM, TEAL, GREEN)
    for center, label, tone in zip(centers, labels, tones):
        bottom = center[1] + (30 if label == "TEMP FALLS" else 90)
        _panel(plate, (center[0] - 145, center[1] - 90,
                       center[0] + 145, bottom), tone, alpha=242)
        label_y = center[1] - (125 if center[1] == 475 else 70)
        if label == "HEAT LOSS":
            label_y = 315
        _tag(plate, (center[0], label_y), label, tone)

    # Thermometer with a true high-to-target scale.
    plate.draw.rounded_rectangle((250, 380, 280, 490), radius=15,
                                 fill=PAPER_LIGHT, outline=INK, width=4)
    plate.draw.ellipse((225, 465, 305, 545), fill=hex_rgba(CORAL_LIGHT, 240),
                       outline=CORAL, width=5)
    plate.draw.rectangle((260, 410, 270, 495), fill=CORAL)
    for y, value in ((400, "39"), (440, "37"), (480, "35")):
        plate.draw.line((282, y, 298, y), fill=INK, width=3)
        plate.text((305, y), value + "°", size=24, bold=value == "37",
                   fill=INK, anchor="lm")

    # Receptor ending: a myelinated afferent rather than a person glyph.
    plate.draw.line((520, 430, 700, 430), fill=BLUE, width=9)
    for x in (540, 590, 640, 690):
        plate.draw.ellipse((x - 19, 405, x + 19, 455),
                           fill=hex_rgba(BLUE_LIGHT, 235), outline=BLUE, width=4)
    plate.draw.arc((535, 365, 685, 455), 190, 345, fill=BLUE, width=6)

    # Hypothalamus shown within a filled brain profile.
    plate.draw.ellipse((900, 380, 1080, 510), fill=hex_rgba(PLUM_LIGHT, 225),
                       outline=PLUM, width=6)
    for dx, dy in ((-45, -20), (25, -25), (-20, 25), (45, 20)):
        plate.draw.arc((990 + dx - 30, 445 + dy - 20,
                        990 + dx + 30, 445 + dy + 20), 20, 250,
                       fill=PLUM, width=4)
    plate.dot((1010, 475), 12, fill=CORAL, outline=INK, width=3)

    # Effector skin inset: sweat gland and widened vessel.
    plate.draw.rectangle((1190, 385, 1450, 445), fill=hex_rgba(GOLD_LIGHT, 180),
                         outline=GOLD, width=4)
    plate.draw.line((1260, 445, 1260, 505), fill=BLUE, width=6)
    plate.draw.arc((1215, 475, 1305, 545), 0, 330, fill=BLUE, width=7)
    for x in (1340, 1390):
        plate.draw.ellipse((x - 14, 345, x + 14, 385),
                           fill=hex_rgba(BLUE_LIGHT, 230), outline=BLUE, width=4)
    plate.draw.line((1195, 515, 1445, 515), fill=CORAL, width=16)
    plate.text((1320, 545), "sweat + blood flow", size=24,
               bold=True, fill=TEAL, anchor="mm")

    _mini_bar(plate, (650, 640, 950, 690), .55, GREEN, "39°C → target range")
    for start, end, label, tone, label_center in (
        ((425, 455), (470, 425), "detect", BLUE, (450, 365)),
        ((755, 410), (835, 410), "compare", PLUM, (795, 465)),
        ((1135, 425), (1170, 455), "", TEAL, (1150, 525)),
        ((1190, 575), (940, 635), "cool", GREEN, (1100, 600)),
        ((650, 680), (410, 520), "opposes rise", GREEN, (505, 625)),
    ):
        _arrow(plate, start, end, label, tone, label_center=label_center)
    plate.text((800, 745), "response opposes the rise; temperature varies around a range",
               size=24, bold=True, fill=INK, anchor="mm")
    _footer(plate, str(content["footer"]))


def draw_ethology(plate: SciencePlate, content: Mapping[str, object]) -> None:
    """Three experiments distinguish mechanism, learning, and fitness logic."""
    _panel(plate, (105, 220, 1495, 790), GOLD)
    panels = ((125, 300, 535, 745), (595, 300, 1005, 745),
              (1065, 300, 1475, 745))
    headings = ("INHERITED RESPONSE", "LEARNING CURVE", "COOPERATION TEST")
    tones = (CORAL, BLUE, GREEN)
    for box, heading, tone in zip(panels, headings, tones):
        _panel(plate, box, tone, alpha=242, radius=22)
        _tag(plate, ((box[0] + box[2]) / 2, 335), heading, tone, size=22)

    # A cue travels through a sensory-to-motor circuit and produces a turn.
    plate.draw.ellipse((165, 410, 225, 470), fill=hex_rgba(CORAL_LIGHT, 240),
                       outline=CORAL, width=5)
    plate.text((195, 440), "cue", size=24, bold=True, fill=CORAL, anchor="mm")
    for center in ((290, 440), (380, 440)):
        _cell(plate, center, rx=38, ry=34, tone=PLUM)
    _arrow(plate, (230, 440), (250, 440), "", CORAL, width=6)
    _arrow(plate, (330, 440), (340, 440), "", PLUM, width=6)
    _arrow(plate, (420, 440), (475, 440), "motor", TEAL,
           label_center=(450, 400), size=20, width=6)
    # Filled fish body: a visible action, not an animal stick glyph.
    plate.draw.ellipse((350, 535, 465, 605), fill=hex_rgba(TEAL_LIGHT, 230),
                       outline=TEAL, width=5)
    plate.draw.polygon(((455, 570), (510, 530), (510, 610)),
                       fill=hex_rgba(TEAL_LIGHT, 230), outline=TEAL)
    plate.dot((375, 560), 5, fill=INK, outline=INK, width=1)
    plate.arrow((405, 625), (310, 650), fill=TEAL, width=7, head=20)
    plate.text((330, 690), "same cue → reliable turn", size=24,
               bold=True, fill=CORAL, anchor="mm")

    # Acquisition is measured during training; retention is a separate,
    # delayed observation, so no line implies practice during the delay.
    gx0, gy0, gx1, gy1 = 645, 405, 955, 655
    for fraction in (.25, .5, .75):
        plate.draw.line((gx0, gy1 - fraction * (gy1 - gy0), gx1,
                         gy1 - fraction * (gy1 - gy0)),
                        fill=hex_rgba(GRID, 140), width=2)
    plate.arrow((gx0, gy1), (gx1, gy1), fill=INK, width=5, head=16)
    plate.arrow((gx0, gy1), (gx0, gy0), fill=INK, width=5, head=16)
    training = [(gx0, gy1 - 35), (700, 590), (750, 535),
                (795, 485), (830, 455)]
    plate.draw.line(training, fill=BLUE, width=9, joint="curve")
    for point in training:
        plate.dot(point, 7, fill=BLUE, outline=PAPER_LIGHT, width=2)
    for boundary in (850, 905):
        plate.dashed_line((boundary, gy0), (boundary, gy1), fill=GRID,
                          width=3, dash=10, gap=9)
    plate.dashed_line((852, gy1 - 12), (900, gy1 - 12), fill=INK_SOFT,
                      width=4, dash=8, gap=7)
    retention = (935, 485)
    plate.draw.line((retention[0], retention[1] - 22,
                     retention[0], retention[1] + 22), fill=CORAL, width=5)
    plate.dot(retention, 10, fill=PAPER_LIGHT, outline=CORAL, width=5)
    plate.text((745, 690), "training", size=24, bold=True,
               fill=BLUE, anchor="mm")
    plate.text((900, 690), "delay → test", size=24, bold=True,
               fill=CORAL, anchor="mm")
    plate.text((620, 390), "correct %", size=24, bold=True,
               fill=INK, anchor="lm")
    _tag(plate, (895, 550), "delayed retention", CORAL)

    # Kin-directed alarm experiment with explicit cost/benefit accounting.
    for center, tone in (((1160, 470), GREEN), ((1300, 430), GREEN),
                         ((1400, 500), GREEN), ((1310, 600), PLUM)):
        x, y = center
        plate.draw.ellipse((x - 48, y - 28, x + 48, y + 28),
                           fill=hex_rgba(mix(tone, PAPER_LIGHT, .48), 240),
                           outline=tone, width=5)
        plate.draw.ellipse((x + 28, y - 42, x + 62, y - 8),
                           fill=hex_rgba(tone, 220), outline=tone, width=3)
        plate.draw.polygon(((x - 48, y), (x - 82, y - 28), (x - 82, y + 28)),
                           fill=hex_rgba(mix(tone, PAPER_LIGHT, .48), 240), outline=tone)
    plate.arrow((1195, 465), (1260, 440), fill=GREEN, width=6, head=18)
    plate.arrow((1195, 485), (1360, 500), fill=GREEN, width=6, head=18)
    _tag(plate, (1270, 655), "rB > C ?", PLUM, size=30)
    plate.text((1270, 705), "benefit, cost,\nrelatedness", size=24,
               bold=True, fill=GREEN, anchor="mm")
    _footer(plate, str(content["footer"]))


def draw_systems_biology(plate: SciencePlate, content: Mapping[str, object]) -> None:
    _panel(plate, (105, 220, 1495, 790), BLUE)
    _tag(plate, (800, 250), "SYNTHETIC GENE CIRCUIT · SIGNAL FLOW", BLUE)
    y = 470
    x_values = (190, 430, 690, 970, 1260)
    labels = ("INPUT", "SENSOR", "REGULATOR", "OUTPUT GENE", "PRODUCT")
    tones = (GOLD, PLUM, CORAL, GREEN, TEAL)
    for x, label, tone in zip(x_values, labels, tones):
        _panel(plate, (x - 90, y - 105, x + 90, y + 105), tone, alpha=242, radius=22)
        _tag(plate, (x, y - 70), label, tone, size=21)
    # Input light pulse.
    plate.draw.ellipse((145, 420, 235, 510), fill=hex_rgba(GOLD_LIGHT, 240),
                       outline=GOLD, width=6)
    for angle in range(0, 360, 45):
        rad = math.radians(angle)
        plate.draw.line((190 + math.cos(rad) * 55, 465 + math.sin(rad) * 55,
                         190 + math.cos(rad) * 75, 465 + math.sin(rad) * 75),
                        fill=GOLD, width=5)
    # Promoter / gene strips encode parts directly.
    for x, tone, name in ((430, PLUM, "P_s"), (970, GREEN, "GFP")):
        plate.draw.line((x - 65, 475, x + 65, 475), fill=INK, width=7)
        plate.draw.polygon(((x - 55, 450), (x - 15, 450), (x - 15, 430),
                            (x + 15, 462), (x - 15, 494), (x - 15, 475),
                            (x - 55, 475)), fill=tone)
        plate.text((x + 35, 520), name, size=28, bold=True, fill=tone, anchor="mm")
    # Regulator protein and measured fluorescent product.
    _protein(plate, (625, 470), count=5, spacing=33)
    plate.draw.rounded_rectangle((1210, 415, 1310, 530), radius=28,
                                 fill=hex_rgba(TEAL_LIGHT, 225), outline=TEAL, width=6)
    plate.draw.ellipse((1235, 440, 1285, 490), fill=hex_rgba(GREEN_LIGHT, 245),
                       outline=GREEN, width=5)
    plate.text((1260, 550), "fluorescence", size=24, bold=True,
               fill=TEAL, anchor="mm")
    for start, end, label, tone in (
        ((285, y), (330, y), "activates", GOLD),
        ((525, y), (585, y), "expression", PLUM),
        ((785, y), (870, y), "binds", CORAL),
        ((1065, y), (1160, y), "expression", GREEN),
    ):
        _arrow(plate, start, end, label, tone,
               label_center=((start[0] + end[0]) / 2, 320), size=20)
    # Measured product feeds back to the sensor with a repression bar.
    plate.draw.line((1260, 585, 1260, 680, 430, 680, 430, 585),
                    fill=BLUE, width=9, joint="curve")
    plate.draw.line((405, 585, 455, 585), fill=BLUE, width=10)
    _tag(plate, (845, 680), "negative feedback", BLUE, size=24)
    plate.text((800, 740), "network topology + rates + noise determine behaviour",
               size=25, bold=True, fill=INK, anchor="mm")
    _footer(plate, str(content["footer"]))


def draw_immunology(plate: SciencePlate, content: Mapping[str, object]) -> None:
    _panel(plate, (105, 220, 1495, 790), PLUM)
    _tag(plate, (800, 250), "ADAPTIVE IMMUNITY · B CELLS ≠ T CELLS", PLUM)
    plate.draw.line((135, 525, 1465, 525), fill=hex_rgba(GRID, 175), width=3)

    # B cells bind extracellular antigen, clone, and produce plasma cells that
    # secrete antibody.  Memory B cells are a sibling cellular fate.
    _tag(plate, (315, 310), "B CELL · SECRETED ANTIBODY", BLUE)
    _virus(plate, (175, 400), size=70, tone=CORAL)
    plate.text((175, 470), "antigen", size=24, bold=True,
               fill=CORAL, anchor="mm")
    _cell(plate, (395, 400), rx=52, ry=46, tone=BLUE)
    plate.text((395, 470), "matching B cell", size=24, bold=True,
               fill=BLUE, anchor="mm")
    for center in ((545, 370), (600, 400), (545, 435)):
        _cell(plate, center, rx=30, ry=27, tone=BLUE)
    plate.text((575, 480), "clone", size=24, bold=True,
               fill=BLUE, anchor="mm")
    # Plasma cell with abundant secretory material.
    _cell(plate, (760, 380), rx=65, ry=52, tone=GOLD)
    for y in (360, 380, 400):
        plate.draw.arc((725, y - 12, 795, y + 12), 185, 355,
                       fill=GOLD, width=4)
    plate.text((760, 450), "plasma cell", size=24, bold=True,
               fill=GOLD, anchor="mm")
    for center in ((900, 350), (955, 390), (900, 430)):
        _antibody(plate, center, size=48, tone=GOLD)
    _virus(plate, (1080, 390), size=58, tone=CORAL)
    plate.text((1080, 470), "antibody binds antigen", size=24,
               bold=True, fill=INK, anchor="mm")
    for x in (735, 815):
        _cell(plate, (x, 495), rx=34, ry=28, tone=GREEN)
    plate.text((970, 510), "memory B cells", size=24, bold=True,
               fill=GREEN, anchor="mm")
    plate.arrow((230, 400), (330, 400), fill=CORAL, width=6, head=18)
    plate.text((280, 355), "binds", size=24, bold=True,
               fill=CORAL, anchor="mm")
    plate.arrow((450, 400), (505, 400), fill=BLUE, width=6, head=18)
    plate.text((478, 355), "clones", size=24, bold=True,
               fill=BLUE, anchor="mm")
    plate.arrow((635, 390), (690, 385), fill=GOLD, width=6, head=18)
    plate.arrow((625, 430), (695, 480), fill=GREEN, width=6, head=18)
    plate.arrow((825, 380), (865, 385), fill=GOLD, width=6, head=18)
    plate.arrow((990, 390), (1040, 390), fill=GOLD, width=6, head=18)

    # T cells recognise peptide–MHC, then act through cellular contact or
    # signals.  Memory T cells remain cells; no antibody encodes this branch.
    _tag(plate, (315, 565), "T CELL · CELLULAR RESPONSE", TEAL)
    _cell(plate, (175, 660), rx=62, ry=54, tone=CORAL)
    plate.draw.rectangle((220, 628, 248, 684),
                         fill=hex_rgba(BLUE_LIGHT, 235), outline=BLUE, width=4)
    plate.draw.polygon(((234, 618), (223, 598), (245, 598)),
                       fill=CORAL, outline=INK)
    plate.text((175, 750), "APC", size=24, bold=True,
               fill=CORAL, anchor="mm")
    _cell(plate, (395, 660), rx=52, ry=46, tone=TEAL)
    plate.text((395, 750), "matching T cell", size=24, bold=True,
               fill=TEAL, anchor="mm")
    for center in ((545, 630), (600, 660), (545, 695)):
        _cell(plate, center, rx=30, ry=27, tone=TEAL)
    plate.text((575, 750), "clone", size=24, bold=True,
               fill=TEAL, anchor="mm")
    _cell(plate, (760, 635), rx=56, ry=47, tone=PLUM)
    plate.text((760, 700), "effector T cell", size=24, bold=True,
               fill=PLUM, anchor="mm")
    _cell(plate, (1010, 635), rx=88, ry=55, tone=CORAL)
    _virus(plate, (1010, 635), size=40, tone=CORAL)
    plate.text((1010, 710), "infected target", size=24, bold=True,
               fill=CORAL, anchor="mm")
    for x in (735, 815):
        _cell(plate, (x, 755), rx=34, ry=27, tone=GREEN)
    plate.text((990, 755), "memory T cells", size=24, bold=True,
               fill=GREEN, anchor="mm")
    plate.arrow((248, 660), (330, 660), fill=CORAL, width=6, head=18)
    plate.text((290, 615), "pMHC", size=24, bold=True,
               fill=CORAL, anchor="mm")
    plate.arrow((450, 660), (505, 660), fill=TEAL, width=6, head=18)
    plate.text((478, 615), "clones", size=24, bold=True,
               fill=TEAL, anchor="mm")
    plate.arrow((635, 650), (695, 640), fill=PLUM, width=6, head=18)
    plate.arrow((625, 695), (695, 745), fill=GREEN, width=6, head=18)
    plate.arrow((820, 635), (915, 635), fill=PLUM, width=6, head=18)
    plate.text((868, 550), "contact / signal", size=24, bold=True,
               fill=PLUM, anchor="mm")
    _footer(plate, str(content["footer"]))


def draw_computational_biology(plate: SciencePlate,
                               content: Mapping[str, object]) -> None:
    _panel(plate, (105, 220, 1495, 790), TEAL)
    lanes = ((125, 300, 535, 745), (595, 300, 1005, 745),
             (1065, 300, 1475, 745))
    headings = ("SEQUENCE", "STRUCTURE", "EVOLUTION")
    tones = (BLUE, CORAL, GREEN)
    for box, heading, tone in zip(lanes, headings, tones):
        _panel(plate, box, tone, alpha=242, radius=22)
        _tag(plate, ((box[0] + box[2]) / 2, 335), heading, tone)

    # Alignment with a visibly scored mismatch and gap.
    for row, sequence in enumerate(("ACG-TGCA", "ACGATGCA", "ACG-TGGA")):
        y = 420 + row * 54
        for index, base in enumerate(sequence):
            x = 175 + index * 40
            tone = CORAL if index in (3, 6) and base not in ("-", "C") else INK
            plate.text((x, y), base, size=28, bold=True, fill=tone, anchor="mm")
    plate.draw.rounded_rectangle((155, 385, 495, 580), radius=18,
                                 outline=BLUE, width=4)
    _tag(plate, (330, 630), "dynamic programming", BLUE, size=21)
    plate.text((330, 690), "claim: homology / variant", size=24,
               bold=True, fill=INK, anchor="mm")

    # Contact map plus a folded-chain hypothesis.
    grid_x, grid_y, cell_size = 640, 400, 30
    contacts = {(0, 0), (1, 1), (2, 2), (3, 3), (4, 4),
                (0, 3), (3, 0), (1, 4), (4, 1), (2, 3), (3, 2)}
    for row in range(5):
        for col in range(5):
            tone = CORAL if (row, col) in contacts else PAPER_LIGHT
            plate.draw.rectangle((grid_x + col * cell_size, grid_y + row * cell_size,
                                  grid_x + (col + 1) * cell_size,
                                  grid_y + (row + 1) * cell_size),
                                 fill=hex_rgba(tone, 230), outline=GRID, width=2)
    fold = [(835, 420), (900, 395), (950, 445), (910, 505),
            (840, 485), (805, 545), (885, 585), (960, 555)]
    plate.draw.line(fold, fill=CORAL, width=10, joint="curve")
    for index, point in enumerate(fold):
        plate.dot(point, 9, fill=(GOLD, PLUM, TEAL)[index % 3],
                  outline=PAPER_LIGHT, width=2)
    _tag(plate, (800, 630), "energy / learned model", CORAL, size=21)
    plate.text((800, 690), "claim: fold + binding", size=24,
               bold=True, fill=INK, anchor="mm")

    # Rooted tree with support values makes uncertainty part of the result.
    plate.draw.line((1145, 620, 1145, 405), fill=GREEN, width=7)
    branches = (((1145, 450), (1240, 405)), ((1145, 520), (1240, 500)),
                ((1145, 590), (1240, 630)), ((1240, 405), (1390, 380)),
                ((1240, 405), (1390, 450)), ((1240, 500), (1390, 510)),
                ((1240, 630), (1390, 610)), ((1240, 630), (1390, 690)))
    for start, end in branches:
        plate.draw.line((*start, *end), fill=GREEN, width=6)
    for point, value in (((1240, 405), "92"), ((1240, 500), "61"),
                         ((1240, 630), "98")):
        plate.dot(point, 13, fill=GOLD_LIGHT, outline=GOLD, width=3)
        plate.text((point[0] + 28, point[1] - 18), value + "%", size=24,
                   bold=True, fill=GOLD, anchor="lm")
    _tag(plate, (1270, 715), "likelihood + uncertainty", GREEN, size=21)
    _footer(plate, str(content["footer"]))


def draw_frontiers(plate: SciencePlate, content: Mapping[str, object]) -> None:
    """Open questions are rendered as discriminating experiments, not scenery."""
    _panel(plate, (105, 220, 1495, 790), GOLD)
    panels = ((125, 300, 535, 775), (595, 300, 1005, 775),
              (1065, 300, 1475, 775))
    headings = ("ORIGIN OF LIFE", "AGEING", "LIFE ELSEWHERE")
    tones = (TEAL, CORAL, BLUE)
    for box, heading, tone in zip(panels, headings, tones):
        _panel(plate, box, tone, alpha=242, radius=22)
        _tag(plate, ((box[0] + box[2]) / 2, 335), heading, tone, size=22)

    # A vesicle containing a copying polymer and an external feedstock.
    plate.draw.ellipse((185, 395, 475, 635), fill=hex_rgba(TEAL_LIGHT, 135),
                       outline=TEAL, width=9)
    plate.draw.ellipse((205, 415, 455, 615), outline=hex_rgba(TEAL, 130), width=4)
    polymer = []
    for index in range(12):
        polymer.append((250 + index * 15, 520 + math.sin(index * .9) * 35))
    plate.draw.line(polymer, fill=PLUM, width=8, joint="curve")
    for index, point in enumerate(polymer):
        plate.dot(point, 8, fill=(PLUM, GOLD, CORAL)[index % 3],
                  outline=PAPER_LIGHT, width=2)
    plate.arrow((145, 515), (195, 515), fill=GOLD, width=7, head=19)
    plate.text((330, 665), "test: plausible chemistry →\nheritable copying", size=24,
               bold=True, fill=TEAL, anchor="mm")

    # A controlled comparison asks whether an intervention delays loss of
    # function.  Axes, threshold, curves, and point shapes carry the claim.
    plate.draw.line((650, 385, 700, 385), fill=CORAL, width=7)
    plate.dot((675, 385), 6, fill=CORAL, outline=CORAL, width=1)
    plate.text((710, 385), "control", size=24, bold=True,
               fill=CORAL, anchor="lm")
    plate.draw.line((830, 385, 860, 385), fill=GREEN, width=7)
    plate.draw.rectangle((839, 378, 851, 390), fill=PAPER_LIGHT,
                         outline=GREEN, width=3)
    plate.text((870, 385), "treated", size=24, bold=True,
               fill=GREEN, anchor="lm")
    gx0, gy0, gx1, gy1 = 650, 430, 950, 650
    plate.arrow((gx0, gy1), (gx1, gy1), fill=INK, width=4, head=15)
    plate.arrow((gx0, gy1), (gx0, gy0), fill=INK, width=4, head=15)
    threshold_y = 575
    plate.dashed_line((gx0, threshold_y), (gx1, threshold_y), fill=INK_SOFT,
                      width=3, dash=10, gap=8)
    plate.text((670, threshold_y - 20), "threshold", size=24, bold=True,
               fill=INK_SOFT, anchor="lm")
    control = ((650, 445), (720, 455), (790, 485),
               (850, 535), (900, 610), (940, 645))
    intervention = ((650, 445), (740, 450), (815, 465),
                    (875, 500), (925, 560), (950, 620))
    plate.draw.line(control, fill=CORAL, width=8, joint="curve")
    plate.draw.line(intervention, fill=GREEN, width=8, joint="curve")
    for point in control:
        plate.dot(point, 6, fill=CORAL, outline=PAPER_LIGHT, width=2)
    for x, y in intervention:
        plate.draw.rectangle((x - 6, y - 6, x + 6, y + 6),
                             fill=PAPER_LIGHT, outline=GREEN, width=3)
    plate.text((620, 420), "function ↑", size=24, bold=True,
               fill=INK, anchor="lm")
    plate.text((800, 680), "age", size=24, bold=True,
               fill=INK, anchor="mm")
    _center_text(plate, (620, 700, 980, 765),
                 "test: does treatment delay threshold crossing?",
                 size=24, bold=True, fill=CORAL, line_gap=4)

    # A transit spectrum: repeated contextual biosignatures beat one gas.
    plate.draw.ellipse((1135, 405, 1265, 535), fill=hex_rgba(BLUE_LIGHT, 230),
                       outline=BLUE, width=6)
    plate.draw.arc((1090, 385, 1310, 555), 15, 170, fill=GOLD, width=8)
    sx0, sy0, sx1, sy1 = 1190, 575, 1440, 685
    plate.arrow((sx0, sy1), (sx1, sy1), fill=INK, width=4, head=14)
    plate.arrow((sx0, sy1), (sx0, sy0), fill=INK, width=4, head=14)
    spectrum = []
    for index in range(51):
        fraction = index / 50
        depth = 15
        for center, strength in ((.28, 38), (.57, 68), (.80, 48)):
            depth += strength * math.exp(-((fraction - center) / .045) ** 2)
        spectrum.append((sx0 + fraction * (sx1 - sx0), sy0 + depth))
    plate.draw.line(spectrum, fill=BLUE, width=7, joint="curve")
    for fraction, label in ((.28, "H₂O"), (.57, "O₂"), (.80, "CH₄")):
        x = sx0 + fraction * (sx1 - sx0)
        plate.text((x, sy0 - 12), label, size=24, bold=True,
                   fill=BLUE, anchor="mm")
    _center_text(plate, (1100, 700, 1440, 765),
                 "test: multiple contextual signals", size=24,
                 bold=True, fill=BLUE, line_gap=4)
    _footer(plate, str(content["footer"]))


RENDERERS: Dict[str, Renderer] = {
    "bio.3.genetics": draw_genetics,
    "bio.3.evolution": draw_evolution,
    "bio.3.cell-bio": draw_cell_biology,
    "bio.3.ecology": draw_ecology,
    "bio.3.microbiology": draw_microbiology,
    "bio.3.botany": draw_botany,
    "bio.4.biochem": draw_biochemistry,
    "bio.4.genomics": draw_genomics,
    "bio.4.neuro": draw_neuroscience,
    "bio.4.evo-bio": draw_evolutionary_biology,
    "bio.4.physiology": draw_physiology,
    "bio.4.ethology": draw_ethology,
    "bio.5.systems-bio": draw_systems_biology,
    "bio.5.immunology": draw_immunology,
    "bio.5.comp-bio": draw_computational_biology,
    "bio.5.frontier": draw_frontiers,
}


if len(RENDERERS) != 16:
    raise ValueError("Advanced biology renderer inventory must contain 16 lessons")
