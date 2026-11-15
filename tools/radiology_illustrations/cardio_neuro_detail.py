"""Cardiovascular, neuroradiology, and head-and-neck reasoning plates.

These deterministic diagrams do not imitate diagnostic scans.  They expose
the geometry and reasoning that imaging supports: compartments, territories,
flow paths, sequence concordance, measurements, acquisition planes, and
decision gates.  Each clinically important distinction is encoded by labels,
shape, line style, position, or numeric relationship in addition to colour.

The module is deliberately registration-free.  Its 24 callables cover exactly
the seven cardiovascular and seventeen brain/head-neck records owned by the
radiology generator; the cohort aggregator validates and registers them.
"""

from __future__ import annotations

import math
from typing import Callable, Dict, Mapping, Tuple

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
    RadiologyPlate,
    _text_tone,
    hex_rgba,
)


Point = Tuple[float, float]
Box = Tuple[float, float, float, float]
Renderer = Callable[[RadiologyPlate, Mapping[str, object]], None]

TONES = (BLUE, TEAL, CORAL, PLUM, GOLD, GREEN)
PALES = (BLUE_LIGHT, TEAL_LIGHT, CORAL_LIGHT, PLUM_LIGHT, GOLD_LIGHT, GREEN_LIGHT)


def _panel(plate: RadiologyPlate, box: Box, title: str, tone: str = BLUE,
           *, subtitle: str = "") -> Box:
    plate.card(box, fill=hex_rgba(PAPER_LIGHT, 226), outline=tone, width=4, radius=22)
    x0, y0, x1, y1 = box
    plate.text(((x0 + x1) / 2, y0 + 34), title, size=25, bold=True,
               fill=_text_tone(tone), anchor="mm")
    plate.draw.line((x0 + 22, y0 + 68, x1 - 22, y0 + 68),
                    fill=hex_rgba(tone, 135), width=3)
    if subtitle:
        plate.text(((x0 + x1) / 2, y0 + 91), subtitle, size=19,
                   fill=INK_SOFT, anchor="mm")
        return x0 + 22, y0 + 117, x1 - 22, y1 - 20
    return x0 + 22, y0 + 88, x1 - 22, y1 - 20


def _tag(plate: RadiologyPlate, center: Point, value: str, tone: str = BLUE,
         *, size: int = 20, pale: bool = False) -> None:
    plate.label(center, value, size=size,
                fill=(hex_rgba(PALES[TONES.index(tone)], 230)
                      if pale and tone in TONES else tone),
                text_fill=(INK if pale else PAPER_LIGHT))


def _note(plate: RadiologyPlate, box: Box, value: str, *, size: int = 20,
          tone: str = INK_SOFT, bold: bool = False) -> None:
    plate.wrapped_text(tuple(int(v) for v in box), value, size=size,
                       bold=bold, fill=tone, line_gap=5)


def _arrow(plate: RadiologyPlate, start: Point, end: Point, label: str = "",
           tone: str = GOLD, *, label_at: Point | None = None,
           width: int = 6, head: int = 18) -> None:
    plate.arrow(start, end, fill=tone, width=width, head=head)
    if label:
        x, y = label_at or ((start[0] + end[0]) / 2,
                            (start[1] + end[1]) / 2 - 20)
        plate.text((x, y), label, size=18, bold=True,
                   fill=_text_tone(tone), anchor="mm")


def _measure(plate: RadiologyPlate, start: Point, end: Point, label: str,
             tone: str = GOLD, *, label_at: Point | None = None) -> None:
    plate.double_arrow(start, end, fill=tone, width=5)
    for x, y in (start, end):
        dx, dy = end[0] - start[0], end[1] - start[1]
        length = max(1.0, math.hypot(dx, dy))
        nx, ny = -dy / length, dx / length
        plate.draw.line((x - nx * 13, y - ny * 13, x + nx * 13, y + ny * 13),
                        fill=tone, width=4)
    x, y = label_at or ((start[0] + end[0]) / 2,
                        (start[1] + end[1]) / 2 - 22)
    plate.text((x, y), label, size=17, bold=True,
               fill=_text_tone(tone), anchor="mm")


def _check(plate: RadiologyPlate, center: Point, tone: str = GREEN,
           *, radius: int = 23) -> None:
    x, y = center
    plate.draw.ellipse((x - radius, y - radius, x + radius, y + radius),
                       fill=hex_rgba(GREEN_LIGHT, 205), outline=tone, width=4)
    plate.draw.line((x - 11, y, x - 2, y + 10, x + 14, y - 12),
                    fill=_text_tone(tone), width=5, joint="curve")


def _cross(plate: RadiologyPlate, center: Point, tone: str = CORAL,
           *, radius: int = 18) -> None:
    x, y = center
    plate.draw.line((x - radius, y - radius, x + radius, y + radius),
                    fill=tone, width=6)
    plate.draw.line((x - radius, y + radius, x + radius, y - radius),
                    fill=tone, width=6)


def _brain(plate: RadiologyPlate, center: Point, scale: float = 1.0,
           *, outline: str = BLUE, fill: str = BLUE_LIGHT,
           midline: bool = True) -> Box:
    """Draw a neutral axial brain orientation schematic, not a scan."""
    x, y = center
    box = (x - 128 * scale, y - 104 * scale, x + 128 * scale, y + 104 * scale)
    plate.draw.ellipse(box, fill=hex_rgba(fill, 82), outline=outline,
                       width=max(3, int(5 * scale)))
    # Scalloped cortical line reads as anatomy rather than a featureless head.
    for angle in range(20, 341, 40):
        radians = math.radians(angle)
        cx = x + math.cos(radians) * 111 * scale
        cy = y + math.sin(radians) * 88 * scale
        plate.draw.arc((cx - 17 * scale, cy - 12 * scale,
                        cx + 17 * scale, cy + 12 * scale), 15, 165,
                       fill=hex_rgba(outline, 145), width=max(1, int(2 * scale)))
    if midline:
        plate.draw.line((x, y - 83 * scale, x, y + 83 * scale),
                        fill=hex_rgba(INK_SOFT, 115), width=max(2, int(3 * scale)))
    # Paired ventricles provide a reproducible internal landmark.
    for dx in (-25, 25):
        plate.draw.arc((x + (dx - 24) * scale, y - 23 * scale,
                        x + (dx + 24) * scale, y + 28 * scale),
                       55 if dx < 0 else 125, 305 if dx < 0 else 235,
                       fill=INK_SOFT, width=max(2, int(3 * scale)))
    return box


def _heart(plate: RadiologyPlate, center: Point, scale: float = 1.0,
           *, tone: str = CORAL) -> None:
    """Draw a labelled four-chamber flow schematic rather than a scan."""
    x, y = center
    plate.draw.rounded_rectangle((x - 116 * scale, y - 116 * scale,
                                  x + 116 * scale, y + 124 * scale),
                                 radius=max(18, int(45 * scale)),
                                 fill=hex_rgba(CORAL_LIGHT, 78), outline=tone,
                                 width=max(3, int(5 * scale)))
    plate.draw.line((x, y - 104 * scale, x, y + 105 * scale),
                    fill=INK_SOFT, width=max(2, int(4 * scale)))
    plate.draw.line((x - 102 * scale, y - 5 * scale,
                     x + 102 * scale, y - 5 * scale),
                    fill=INK_SOFT, width=max(2, int(4 * scale)))
    for dx, dy, label in ((-55, -59, "RA"), (55, -59, "LA"),
                          (-55, 56, "RV"), (55, 56, "LV")):
        plate.text((x + dx * scale, y + dy * scale), label,
                   size=max(13, int(18 * scale)), bold=True,
                   fill=INK, anchor="mm")


def _vessel_section(plate: RadiologyPlate, center: Point, radius: float,
                    *, tone: str = CORAL, wall: str = GOLD_LIGHT) -> None:
    x, y = center
    plate.draw.ellipse((x - radius, y - radius, x + radius, y + radius),
                       fill=hex_rgba(wall, 170), outline=_text_tone(tone), width=5)
    inner = radius * .68
    plate.draw.ellipse((x - inner, y - inner, x + inner, y + inner),
                       fill=hex_rgba(BLUE_LIGHT, 100), outline=tone, width=4)


def _landmark(plate: RadiologyPlate, center: Point, label: str, tone: str,
              *, shape: str = "circle", size: int = 17, radius: int = 31) -> None:
    x, y = center
    if shape == "diamond":
        plate.draw.polygon(((x, y - 28), (x + 34, y), (x, y + 28), (x - 34, y)),
                           fill=hex_rgba(PALES[TONES.index(tone)], 175), outline=tone)
        plate.draw.line((x, y - 28, x + 34, y, x, y + 28, x - 34, y, x, y - 28),
                        fill=tone, width=4)
    elif shape == "square":
        plate.draw.rounded_rectangle((x - 35, y - 28, x + 35, y + 28), radius=9,
                                     fill=hex_rgba(PALES[TONES.index(tone)], 175),
                                     outline=tone, width=4)
    else:
        plate.draw.ellipse((x - radius, y - radius, x + radius, y + radius),
                           fill=hex_rgba(PALES[TONES.index(tone)], 175),
                           outline=tone, width=4)
    plate.text((x, y), label, size=size, bold=True,
               fill=_text_tone(tone), anchor="mm")


def _draw_aorta(plate: RadiologyPlate, item: Mapping[str, object]) -> None:
    boxes = ((92, 220, 555, 790), (568, 220, 1031, 790), (1044, 220, 1508, 790))
    # Dissection: two contrast-filled lumina separated by a visible flap.
    inner = _panel(plate, boxes[0], "DISSECTION", BLUE,
                   subtitle="flap separates true and false lumina")
    c = ((inner[0] + inner[2]) / 2, inner[1] + 174)
    _vessel_section(plate, c, 111, tone=CORAL)
    x, y = c
    # A wall-to-wall flap must actually partition the lumen, not trace its rim.
    flap = [(x - 18 * math.sin(math.pi * i / 40), y - 73 + 146 * i / 40)
            for i in range(41)]
    plate.polyline(flap, fill=PLUM, width=8)
    plate.text((x - 42, y), "TL", size=23, bold=True, fill=_text_tone(BLUE), anchor="mm")
    plate.text((x + 48, y), "FL", size=23, bold=True, fill=_text_tone(PLUM), anchor="mm")
    _arrow(plate, (inner[0] + 45, inner[1] + 70), (x - 10, y - 49),
           "INTIMAL FLAP", PLUM, label_at=(inner[0] + 107, inner[1] + 47), width=5)
    _note(plate, (inner[0] + 12, inner[1] + 323, inner[2] - 12, inner[3]),
          "Trace both channels and branch-vessel involvement; TL/FL labels encode the distinction.",
          size=20, tone=INK, bold=True)

    # IMH: the abnormality is in the wall, with no flowing false lumen shown.
    inner = _panel(plate, boxes[1], "INTRAMURAL HAEMATOMA", PLUM,
                   subtitle="crescentic blood within the wall")
    c = ((inner[0] + inner[2]) / 2, inner[1] + 174)
    _vessel_section(plate, c, 111, tone=CORAL)
    x, y = c
    plate.draw.pieslice((x - 108, y - 108, x + 108, y + 108), 103, 257,
                        fill=hex_rgba(PLUM, 185), outline=PLUM)
    plate.draw.ellipse((x - 71, y - 71, x + 71, y + 71),
                       fill=hex_rgba(BLUE_LIGHT, 255), outline=CORAL, width=4)
    plate.text((x - 82, y), "WALL", size=15, bold=True,
               fill=PAPER_LIGHT, anchor="mm")
    plate.text((x + 30, y), "single lumen", size=17, bold=True,
               fill=_text_tone(BLUE), anchor="mm")
    _tag(plate, (x, inner[1] + 323), "NO VISIBLE FLAP / FLOWING FL", CORAL, size=18)
    _note(plate, (inner[0] + 12, inner[1] + 360, inner[2] - 12, inner[3]),
          "The crescent belongs to the wall; noncontrast and contrast phases answer different questions.",
          size=19, tone=INK, bold=True)

    # PAU: a focal luminal crater penetrates an atherosclerotic wall.
    inner = _panel(plate, boxes[2], "PENETRATING ULCER", CORAL,
                   subtitle="focal contrast crater enters the wall")
    c = ((inner[0] + inner[2]) / 2, inner[1] + 174)
    _vessel_section(plate, c, 111, tone=CORAL)
    x, y = c
    plate.draw.polygon(((x + 65, y - 22), (x + 112, y - 45),
                        (x + 137, y), (x + 112, y + 45), (x + 65, y + 22)),
                       fill=hex_rgba(BLUE_LIGHT, 155), outline=CORAL)
    plate.draw.line((x + 66, y - 23, x + 112, y - 45, x + 137, y,
                     x + 112, y + 45, x + 66, y + 23), fill=CORAL, width=5)
    for angle in (135, 180, 225):
        radians = math.radians(angle)
        px, py = x + math.cos(radians) * 92, y + math.sin(radians) * 92
        plate.dot((px, py), 5, fill=GOLD, outline=GOLD, width=1)
    _arrow(plate, (inner[2] - 21, inner[1] + 65), (x + 109, y - 18),
           "FOCAL CRATER", CORAL, label_at=(inner[2] - 99, inner[1] + 45), width=5)
    _note(plate, (inner[0] + 10, inner[1] + 326, inner[2] - 10, inner[3]),
          "A focal outpouching through diseased intima is not the long flap of dissection.",
          size=20, tone=INK, bold=True)


def _draw_cardiac_mri(plate: RadiologyPlate, item: Mapping[str, object]) -> None:
    # One heart is interrogated by three sequence families, each answering a
    # different question; the diagram avoids pretending to be an MR image.
    _tag(plate, (800, 233), "SAME MYOCARDIUM, DIFFERENT SEQUENCE QUESTIONS", PLUM, size=22)

    inner = _panel(plate, (92, 277, 520, 780), "CINE: FUNCTION", BLUE)
    plate.draw.ellipse((inner[0] + 64, inner[1] + 65, inner[0] + 220, inner[1] + 221),
                       fill=hex_rgba(CORAL_LIGHT, 80), outline=BLUE, width=5)
    plate.draw.ellipse((inner[0] + 111, inner[1] + 109, inner[0] + 173, inner[1] + 177),
                       fill=PAPER_LIGHT, outline=BLUE, width=4)
    plate.draw.ellipse((inner[0] + 236, inner[1] + 92, inner[0] + 366, inner[1] + 214),
                       fill=hex_rgba(CORAL_LIGHT, 80), outline=BLUE, width=5)
    plate.draw.ellipse((inner[0] + 279, inner[1] + 128, inner[0] + 323, inner[1] + 178),
                       fill=PAPER_LIGHT, outline=BLUE, width=4)
    _arrow(plate, (inner[0] + 209, inner[1] + 151),
           (inner[0] + 228, inner[1] + 151), "systole", BLUE,
           label_at=(inner[0] + 219, inner[1] + 110), width=4, head=11)
    plate.text(((inner[0] + inner[2]) / 2, inner[1] + 257),
               "ED volume -> ES volume -> motion", size=18, bold=True,
               fill=_text_tone(BLUE), anchor="mm")
    _note(plate, (inner[0] + 9, inner[1] + 282, inner[2] - 9, inner[3]),
          "Measure chamber volumes and wall motion across the cardiac cycle.",
          size=19, tone=INK, bold=True)

    inner = _panel(plate, (540, 277, 1017, 780), "FLUID-SENSITIVE: OEDEMA", TEAL)
    cx, cy = (inner[0] + inner[2]) / 2, inner[1] + 165
    plate.draw.ellipse((cx - 113, cy - 92, cx + 113, cy + 92),
                       fill=hex_rgba(CORAL_LIGHT, 85), outline=TEAL, width=5)
    plate.draw.ellipse((cx - 62, cy - 48, cx + 62, cy + 48),
                       fill=PAPER_LIGHT, outline=TEAL, width=4)
    plate.draw.arc((cx - 105, cy - 84, cx + 105, cy + 84), 310, 55,
                   fill=TEAL, width=22)
    _arrow(plate, (cx + 145, cy - 77), (cx + 80, cy - 32),
           "high fluid signal", TEAL, label_at=(cx + 103, cy - 103), width=5)
    _note(plate, (inner[0] + 12, inner[1] + 282, inner[2] - 12, inner[3]),
          "Regional high signal supports acute injury only when acquisition and other sequences agree.",
          size=19, tone=INK, bold=True)

    inner = _panel(plate, (1037, 277, 1508, 780), "LATE ENHANCEMENT", CORAL)
    left, right, cy = inner[0] + 115, inner[0] + 324, inner[1] + 157
    for cx in (left, right):
        plate.draw.ellipse((cx - 83, cy - 72, cx + 83, cy + 72),
                           fill=hex_rgba(CORAL_LIGHT, 75), outline=CORAL, width=4)
        plate.draw.ellipse((cx - 47, cy - 39, cx + 47, cy + 39),
                           fill=PAPER_LIGHT, outline=CORAL, width=3)
    # Ischaemic scar begins at the subendocardium; keep the mark beside the
    # cavity rather than at the epicardial edge of this schematic wall.
    plate.draw.arc((left - 61, cy - 51, left + 61, cy + 51), 302, 60,
                   fill=CORAL, width=17)
    plate.draw.arc((right - 63, cy - 54, right + 63, cy + 54), 62, 246,
                   fill=PLUM, width=11)
    plate.text((left, cy + 100), "coronary + subendo", size=16,
               bold=True, fill=_text_tone(CORAL), anchor="mm")
    plate.text((right, cy + 100), "mid-wall scar", size=16,
               bold=True, fill=_text_tone(PLUM), anchor="mm")
    _note(plate, (inner[0] + 10, inner[1] + 292, inner[2] - 10, inner[3]),
          "Distribution, not brightness alone, links scar pattern to mechanism.",
          size=19, tone=INK, bold=True)


def _draw_cardiac_masses_devices(plate: RadiologyPlate,
                                 item: Mapping[str, object]) -> None:
    boxes = ((92, 220, 555, 790), (568, 220, 1031, 790), (1044, 220, 1508, 790))
    inner = _panel(plate, boxes[0], "THROMBUS", BLUE,
                   subtitle="location + stasis; usually non-perfused")
    _heart(plate, ((inner[0] + inner[2]) / 2, inner[1] + 170), .83)
    cx, cy = (inner[0] + inner[2]) / 2 + 43, inner[1] + 246
    plate.draw.ellipse((cx - 36, cy - 24, cx + 36, cy + 24),
                       fill=hex_rgba(BLUE, 170), outline=INK, width=4)
    _arrow(plate, (inner[0] + 28, inner[1] + 74), (cx - 24, cy - 20),
           "LV apical thrombus", BLUE, label_at=(inner[0] + 145, inner[1] + 50), width=5)
    plate.draw.line((inner[0] + 88, inner[1] + 326,
                     inner[2] - 88, inner[1] + 326), fill=BLUE, width=5)
    plate.text(((inner[0] + inner[2]) / 2, inner[1] + 354),
               "usually no perfusion", size=20, bold=True,
               fill=_text_tone(BLUE), anchor="mm")
    _note(plate, (inner[0] + 9, inner[1] + 376, inner[2] - 9, inner[3]),
          "Organised thrombus can enhance peripherally or heterogeneously; use location and stasis too.",
          size=17, tone=INK, bold=True)

    inner = _panel(plate, boxes[1], "TUMOUR", PLUM,
                   subtitle="attachment + tissue + perfusion")
    _heart(plate, ((inner[0] + inner[2]) / 2, inner[1] + 170), .83)
    cx, cy = (inner[0] + inner[2]) / 2 + 38, inner[1] + 127
    plate.draw.ellipse((cx - 39, cy - 34, cx + 39, cy + 34),
                       fill=hex_rgba(PLUM_LIGHT, 220), outline=PLUM, width=5)
    plate.draw.line((cx - 38, cy, cx - 76, cy + 32), fill=PLUM, width=7)
    _arrow(plate, (inner[2] - 30, inner[1] + 58), (cx - 60, cy + 20),
           "attachment", PLUM, label_at=(inner[2] - 102, inner[1] + 38), width=5)
    # Acquisition steps, not invented tumour enhancement measurements.
    for index, label in enumerate(("pre", "early", "late")):
        x = inner[0] + 118 + index * 78
        plate.draw.rounded_rectangle((x - 30, inner[1] + 326, x + 30, inner[1] + 361),
                                     radius=7, fill=PLUM_LIGHT, outline=PLUM, width=2)
        plate.text((x, inner[1] + 344), label,
                   size=15, bold=True, fill=INK_SOFT, anchor="mm")
    plate.text(((inner[0] + inner[2]) / 2, inner[1] + 382),
               "compare enhancement across phases", size=16, bold=True,
               fill=INK, anchor="mm")
    plate.text(((inner[0] + inner[2]) / 2, inner[1] + 414),
               "No single feature names every mass.", size=17, bold=True,
               fill=INK, anchor="mm")

    inner = _panel(plate, boxes[2], "DEVICE CHECK", CORAL,
                   subtitle="lead path + tip + surrounding anatomy")
    _heart(plate, ((inner[0] + inner[2]) / 2, inner[1] + 171), .83)
    hx, hy = (inner[0] + inner[2]) / 2, inner[1] + 171
    plate.draw.line((hx - 78, hy - 152, hx - 54, hy - 72,
                     hx - 41, hy + 48, hx - 8, hy + 88),
                    fill=GOLD, width=8, joint="curve")
    plate.draw.ellipse((hx - 17, hy + 78, hx + 2, hy + 97), fill=GOLD)
    for y, label in ((inner[1] + 329, "1  lead follows expected course"),
                     (inner[1] + 374, "2  tip position is named"),
                     (inner[1] + 419, "3  effusion / perforation sought")):
        _check(plate, (inner[0] + 43, y), radius=17)
        plate.text((inner[0] + 73, y), label, size=17, bold=True,
                   fill=INK, anchor="lm")


def _draw_congenital_ct(plate: RadiologyPlate, item: Mapping[str, object]) -> None:
    _tag(plate, (800, 227), "SEGMENTAL ANALYSIS: NAME EACH CONNECTION", BLUE, size=22)
    # Connected schematic: situs -> AV connections -> VA connections -> vessels.
    y = 485
    stages = ((230, "1", "SITUS", "atria + organs", BLUE),
              (535, "2", "AV", "atria -> ventricles", TEAL),
              (865, "3", "VA", "ventricles -> arteries", PLUM),
              (1260, "4", "VESSELS", "arches + veins", CORAL))
    for x, number, heading, detail, tone in stages:
        half_width = 130 if number == "1" else 145
        plate.draw.rounded_rectangle((x - half_width, 315, x + half_width, 682), radius=24,
                                     fill=hex_rgba(PALES[TONES.index(tone)], 90),
                                     outline=tone, width=4)
        _landmark(plate, (x, 365), number, tone, shape="square", size=19)
        plate.text((x, 420), heading, size=23, bold=True,
                   fill=_text_tone(tone), anchor="mm")
        plate.text((x, 455), detail, size=17, fill=INK_SOFT, anchor="mm")
    # Situs panel: explicit L/R and abdominal organs.
    plate.text((174, 540), "patient L", size=16, bold=True, fill=_text_tone(BLUE), anchor="mm")
    plate.text((286, 540), "patient R", size=16, bold=True, fill=_text_tone(CORAL), anchor="mm")
    plate.draw.ellipse((148, 565, 205, 604), fill=BLUE_LIGHT, outline=BLUE, width=3)
    plate.draw.polygon(((260, 565), (315, 565), (303, 610), (251, 600)),
                       fill=CORAL_LIGHT, outline=CORAL)
    plate.text((174, 624), "stomach", size=15, fill=INK_SOFT, anchor="mm")
    plate.text((286, 624), "liver", size=15, fill=INK_SOFT, anchor="mm")
    plate.text((230, 655), "example: situs solitus", size=15, bold=True,
               fill=_text_tone(BLUE), anchor="mm")
    # AV panel.
    for dx, label in ((-59, "RA"), (59, "LA")):
        _landmark(plate, (535 + dx, 527), label, BLUE, size=15)
    for dx, label in ((-59, "RV"), (59, "LV")):
        _landmark(plate, (535 + dx, 620), label, TEAL, shape="square", size=15)
    _arrow(plate, (476, 558), (476, 587), "", BLUE, width=5, head=12)
    _arrow(plate, (594, 558), (594, 587), "", BLUE, width=5, head=12)
    # VA panel.
    for dx, label in ((-59, "RV"), (59, "LV")):
        _landmark(plate, (865 + dx, 527), label, TEAL, shape="square", size=15)
    for dx, label in ((-59, "PA"), (59, "AO")):
        _landmark(plate, (865 + dx, 620), label, PLUM, size=15)
    _arrow(plate, (806, 558), (806, 587), "", TEAL, width=5, head=12)
    _arrow(plate, (924, 558), (924, 587), "", TEAL, width=5, head=12)
    # Great-vessel map.
    plate.draw.line((1260, 632, 1260, 551, 1195, 500), fill=CORAL, width=14, joint="curve")
    plate.draw.line((1260, 551, 1325, 500), fill=CORAL, width=14, joint="curve")
    plate.draw.arc((1210, 486, 1358, 584), 170, 350, fill=CORAL, width=12)
    plate.draw.line((1202, 611, 1152, 553), fill=BLUE, width=10)
    plate.draw.line((1202, 611, 1352, 553), fill=BLUE, width=10)
    plate.text((1260, 650), "map arch, PA, veins, collaterals", size=16,
               bold=True, fill=_text_tone(CORAL), anchor="mm")
    for first, second in ((363, 387), (680, 720), (1010, 1110)):
        _arrow(plate, (first, y), (second, y), "trace", GOLD,
               label_at=((first + second) / 2, y - 27), width=5, head=14)
    plate.text((800, 743), "A normal-looking chamber does not prove a normal connection.",
               size=21, bold=True, fill=INK, anchor="mm")


def _draw_coronary_ct(plate: RadiologyPlate, item: Mapping[str, object]) -> None:
    # One coronary path moves through a quality gate, orthogonal measurement,
    # and structured action rather than three generic cards.
    _tag(plate, (800, 227), "QUALITY -> SEGMENT -> CATEGORY / ACTION", CORAL, size=22)
    inner = _panel(plate, (92, 258, 650, 766), "1  ACQUIRE", BLUE,
                   subtitle="motion controlled + lumen opacified")
    hx, hy = (inner[0] + inner[2]) / 2, inner[1] + 178
    _heart(plate, (hx, hy), .80)
    # Coronary paths on the epicardial surface are drawn after the panel so
    # they remain visible in the responsive asset.
    plate.draw.line((hx + 6, hy - 97, hx + 75, hy - 53, hx + 90, hy + 32),
                    fill=CORAL, width=8, joint="curve")
    plate.draw.line((hx + 2, hy - 95, hx - 63, hy - 47, hx - 79, hy + 29),
                    fill=BLUE, width=8, joint="curve")
    plate.text((hx, inner[1] + 331), "trace every interpretable segment", size=18,
               bold=True, fill=_text_tone(BLUE), anchor="mm")
    _tag(plate, (488, 678), "QUALITY GATE", BLUE, size=18)
    _check(plate, (581, 678), radius=19)

    inner = _panel(plate, (685, 258, 1121, 766), "2  GRADE NARROWING", PLUM,
                   subtitle="plane normal to the vessel")
    cx, cy = (inner[0] + inner[2]) / 2, inner[1] + 175
    # Longitudinal lumen with a focal plaque and the orthogonal cross-section.
    plate.draw.line((inner[0] + 34, cy, inner[2] - 35, cy),
                    fill=BLUE_LIGHT, width=65)
    plate.draw.line((inner[0] + 34, cy, inner[2] - 35, cy),
                    fill=BLUE, width=4)
    plate.draw.polygon(((cx - 54, cy - 32), (cx + 45, cy - 32),
                        (cx + 22, cy - 6), (cx - 31, cy - 6)),
                       fill=GOLD_LIGHT, outline=GOLD)
    _measure(plate, (cx, cy - 6), (cx, cy + 32), "Dmin", PLUM,
             label_at=(cx + 75, cy + 15))
    plate.draw.ellipse((cx - 58, cy + 85, cx + 58, cy + 201),
                       fill=hex_rgba(GOLD_LIGHT, 165), outline=GOLD, width=4)
    plate.draw.ellipse((cx - 26, cy + 117, cx + 26, cy + 169),
                       fill=hex_rgba(BLUE_LIGHT, 150), outline=BLUE, width=4)
    plate.text((cx, cy + 202), "compare with reference lumen", size=16,
               bold=True, fill=INK, anchor="mm")

    inner = _panel(plate, (1156, 258, 1508, 766), "3  REPORT", GREEN,
                   subtitle="worst interpretable segment")
    decisions = (("category", "stenosis"), ("plaque", "burden"),
                 ("modifier", "quality / context"), ("action", "next step"))
    for index, (head, detail) in enumerate(decisions):
        y = inner[1] + 54 + index * 89
        _landmark(plate, (inner[0] + 45, y), str(index + 1),
                  (BLUE, PLUM, CORAL, GREEN)[index], shape="square", size=15)
        plate.text((inner[0] + 92, y - 11), head, size=19, bold=True,
                   fill=INK, anchor="lm")
        plate.text((inner[0] + 92, y + 18), detail, size=16,
                   fill=INK_SOFT, anchor="lm")


def _draw_peripheral_vascular(plate: RadiologyPlate,
                              item: Mapping[str, object]) -> None:
    _tag(plate, (800, 227), "FROM BOLUS TIMING TO A USABLE VASCULAR ROADMAP", BLUE, size=21)
    # Timing strip.
    _panel(plate, (92, 266, 475, 770), "1  TIME THE BOLUS", BLUE)
    x0, y0 = 133, 443
    plate.arrow((x0, y0), (432, y0), fill=INK_SOFT, width=4, head=13)
    points = ((145, 434), (197, 422), (245, 365), (292, 328),
              (342, 382), (397, 423))
    plate.polyline(points, fill=BLUE, width=7)
    plate.draw.line((292, 318, 292, 499), fill=CORAL, width=4)
    plate.text((355, 362), "target window", size=17, bold=True,
               fill=_text_tone(CORAL), anchor="mm")
    plate.text((146, 480), "inject", size=16, bold=True, fill=INK_SOFT, anchor="mm")
    plate.text((416, 480), "late", size=16, bold=True, fill=INK_SOFT, anchor="mm")
    _note(plate, (122, 535, 445, 724),
          "Match the acquisition window to the arterial or venous question; poor timing can mimic occlusion.",
          size=20, tone=INK, bold=True)

    # Measurement strip.
    _panel(plate, (505, 266, 955, 770), "2  MEASURE TRUE LUMEN", PLUM)
    cx, cy = 730, 453
    plate.draw.line((555, cy, 905, cy), fill=BLUE_LIGHT, width=85)
    plate.draw.line((555, cy - 42, 905, cy - 42), fill=BLUE, width=4)
    plate.draw.line((555, cy + 42, 905, cy + 42), fill=BLUE, width=4)
    plate.draw.polygon(((679, cy - 42), (780, cy - 42),
                        (758, cy - 10), (704, cy - 10)),
                       fill=GOLD_LIGHT, outline=GOLD)
    plate.draw.line((730, cy - 105, 730, cy + 105), fill=PLUM, width=4)
    _measure(plate, (730, cy - 10), (730, cy + 42), "normal plane", PLUM,
             label_at=(811, cy + 85))
    _note(plate, (538, 588, 922, 724),
          "Avoid oblique overestimation: measure the true lumen on a plane normal to its centreline.",
          size=19, tone=INK, bold=True)

    # Roadmap: inflow -> lesion -> runoff with a labelled collateral.
    _panel(plate, (985, 266, 1508, 770), "3  MAP CONSEQUENCES", TEAL)
    trunk_x, top_y = 1160, 357
    plate.draw.line((trunk_x, top_y, trunk_x, 489), fill=CORAL, width=17)
    plate.draw.line((trunk_x, 489, 1085, 603), fill=CORAL, width=15)
    plate.draw.line((trunk_x, 489, 1235, 603), fill=CORAL, width=15)
    plate.draw.line((1085, 603, 1060, 704), fill=CORAL, width=11)
    plate.draw.line((1235, 603, 1260, 704), fill=CORAL, width=11)
    plate.draw.line((1218, 577, 1230, 595), fill=PAPER_LIGHT, width=8)
    plate.text((1330, 563), "lesion", size=17, bold=True,
               fill=_text_tone(CORAL), anchor="lm")
    plate.polyline(((1190, 535), (1245, 531), (1293, 561),
                    (1305, 610), (1282, 647), (1247, 651)),
                   fill=TEAL, width=7)
    plate.text((1436, 623), "collateral", size=17, bold=True,
               fill=_text_tone(TEAL), anchor="rm")
    plate.text((1377, 368), "INFLOW", size=18, bold=True,
               fill=_text_tone(CORAL), anchor="mm")
    plate.text((1372, 693), "RUNOFF + END-ORGAN RISK", size=15, bold=True,
               fill=INK, anchor="mm")


def _draw_tavi_ct(plate: RadiologyPlate, item: Mapping[str, object]) -> None:
    boxes = ((92, 220, 555, 790), (568, 220, 1031, 790), (1044, 220, 1508, 790))
    inner = _panel(plate, boxes[0], "ANNULAR PLANE", BLUE,
                   subtitle="systolic sizing geometry")
    cx, cy = (inner[0] + inner[2]) / 2, inner[1] + 176
    plate.draw.ellipse((cx - 132, cy - 83, cx + 132, cy + 83),
                       fill=hex_rgba(BLUE_LIGHT, 80), outline=BLUE, width=6)
    for angle in (90, 210, 330):
        r = math.radians(angle)
        plate.dot((cx + math.cos(r) * 78, cy + math.sin(r) * 49), 8,
                  fill=GOLD, outline=GOLD, width=1)
    _measure(plate, (cx - 126, cy), (cx + 126, cy), "major diameter", BLUE,
             label_at=(cx, cy - 105))
    _measure(plate, (cx, cy - 77), (cx, cy + 77), "minor", TEAL,
             label_at=(cx + 66, cy + 101))
    plate.text((cx, inner[1] + 327), "area + perimeter complete sizing", size=19,
               bold=True, fill=_text_tone(BLUE), anchor="mm")
    _note(plate, (inner[0] + 9, inner[1] + 348, inner[2] - 9, inner[3]),
          "Select the true annular plane before comparing measurements with the device chart.",
          size=19, tone=INK, bold=True)

    inner = _panel(plate, boxes[1], "CORONARY CLEARANCE", PLUM,
                   subtitle="annulus -> ostium + sinus geometry")
    cx, base = (inner[0] + inner[2]) / 2, inner[1] + 340
    plate.draw.arc((cx - 123, base - 250, cx + 123, base - 40), 180, 360,
                   fill=CORAL, width=15)
    plate.draw.line((cx - 115, base - 143, cx - 115, base), fill=CORAL, width=12)
    plate.draw.line((cx + 115, base - 143, cx + 115, base), fill=CORAL, width=12)
    plate.draw.ellipse((cx - 18, base - 33, cx + 18, base + 3),
                       fill=GOLD_LIGHT, outline=GOLD, width=4)
    ostium = (cx + 111, base - 145)
    plate.dot(ostium, 9, fill=PLUM, outline=PLUM, width=1)
    plate.draw.line((cx - 144, base, cx + 144, base), fill=BLUE, width=7)
    _measure(plate, (ostium[0] + 38, base - 1), (ostium[0] + 38, ostium[1]),
             "coronary height", PLUM, label_at=(cx - 6, base - 73))
    plate.text((cx, base + 51), "annular reference plane", size=17,
               bold=True, fill=_text_tone(BLUE), anchor="mm")
    plate.text((cx, base + 92), "also inspect sinus and leaflet relationship", size=17,
               bold=True, fill=INK, anchor="mm")

    inner = _panel(plate, boxes[2], "ACCESS ROUTE", TEAL,
                   subtitle="calibre + plaque + tortuosity")
    points = ((inner[0] + 65, inner[1] + 61), (inner[0] + 145, inner[1] + 125),
              (inner[0] + 92, inner[1] + 209), (inner[0] + 212, inner[1] + 286),
              (inner[0] + 302, inner[1] + 372))
    plate.draw.line(points, fill=TEAL_LIGHT, width=55, joint="curve")
    plate.draw.line(points, fill=TEAL, width=5, joint="curve")
    lesion_x, lesion_y = inner[0] + 106, inner[1] + 187
    plate.draw.ellipse((lesion_x - 18, lesion_y - 20, lesion_x + 25, lesion_y + 23),
                       fill=GOLD_LIGHT, outline=GOLD, width=3)
    # Orthogonal inset: measure the patent lumen, not plaque or an oblique
    # width across the tortuous longitudinal roadmap.
    ix, iy = inner[0] + 295, inner[1] + 112
    plate.draw.line((lesion_x + 25, lesion_y - 20, ix - 57, iy + 36),
                    fill=INK_SOFT, width=3)
    plate.draw.ellipse((ix - 58, iy - 58, ix + 58, iy + 58),
                       fill=GOLD_LIGHT, outline=TEAL, width=4)
    plate.draw.ellipse((ix - 29, iy - 36, ix + 29, iy + 36),
                       fill=TEAL_LIGHT, outline=TEAL, width=3)
    _measure(plate, (ix - 29, iy), (ix + 29, iy),
             "minimum lumen", TEAL, label_at=(ix, iy + 84))
    plate.text((ix, iy - 80), "normal-plane inset", size=16,
               bold=True, fill=_text_tone(TEAL), anchor="mm")
    plate.text(((inner[0] + inner[2]) / 2, inner[1] + 408),
               "narrowest hazardous segment sets feasibility", size=16,
               bold=True, fill=INK, anchor="mm")


def _draw_stroke(plate: RadiologyPlate, item: Mapping[str, object]) -> None:
    boxes = ((92, 220, 555, 790), (568, 220, 1031, 790), (1044, 220, 1508, 790))
    inner = _panel(plate, boxes[0], "1  NONCONTRAST CT", BLUE,
                   subtitle="exclude haemorrhage; assess early change")
    cx, cy = (inner[0] + inner[2]) / 2, inner[1] + 171
    _brain(plate, (cx, cy), .94)
    # Question-marked comparator avoids implying this is an actual CT case.
    plate.draw.ellipse((cx + 37, cy - 49, cx + 91, cy + 7),
                       fill=hex_rgba(CORAL, 185), outline=INK, width=4)
    plate.text((cx + 64, cy - 21), "?", size=24, bold=True,
               fill=PAPER_LIGHT, anchor="mm")
    _arrow(plate, (inner[0] + 36, inner[1] + 64), (cx + 39, cy - 42),
           "blood?", CORAL, label_at=(inner[0] + 84, inner[1] + 43), width=5)
    for index, label in enumerate(("haemorrhage", "early ischaemia", "ASPECTS region")):
        y = inner[1] + 326 + index * 47
        _check(plate, (inner[0] + 45, y), radius=16)
        plate.text((inner[0] + 76, y), label, size=18, bold=True,
                   fill=INK, anchor="lm")

    inner = _panel(plate, boxes[1], "2  CTA", PLUM,
                   subtitle="locate occlusion; inspect collateral routes")
    cx, cy = (inner[0] + inner[2]) / 2, inner[1] + 191
    plate.draw.line((cx, cy + 111, cx, cy - 12), fill=CORAL, width=17)
    plate.draw.line((cx, cy - 12, cx - 103, cy - 93), fill=CORAL, width=13)
    plate.draw.line((cx, cy - 12, cx + 103, cy - 93), fill=CORAL, width=13)
    plate.draw.line((cx + 53, cy - 53, cx + 72, cy - 68), fill=PAPER_LIGHT, width=13)
    plate.draw.line((cx + 54, cy - 54, cx + 71, cy - 67), fill=INK, width=3)
    _tag(plate, (cx + 111, cy - 18), "LVO", CORAL, size=18)
    _arrow(plate, (cx + 91, cy - 26), (cx + 66, cy - 58), "", CORAL, width=5)
    # Dashed collateral arc has a second encoding by its label.
    for start in range(0, 150, 24):
        plate.draw.arc((cx - 114, cy - 142, cx + 114, cy + 33),
                       190 + start, 201 + start, fill=TEAL, width=5)
    plate.text((cx, cy - 143), "collateral route", size=18, bold=True,
               fill=_text_tone(TEAL), anchor="mm")
    plate.text((cx, inner[1] + 361), "confirm the defect across planes / branches", size=18,
               bold=True, fill=INK, anchor="mm")

    inner = _panel(plate, boxes[2], "3  TREATMENT SELECTION", GREEN,
                   subtitle="tissue + time + clinical status")
    cx, cy = (inner[0] + inner[2]) / 2, inner[1] + 172
    plate.draw.ellipse((cx - 127, cy - 96, cx + 127, cy + 96),
                       fill=hex_rgba(GREEN_LIGHT, 100), outline=GREEN, width=5)
    plate.draw.ellipse((cx - 65, cy - 51, cx + 65, cy + 51),
                       fill=hex_rgba(CORAL_LIGHT, 210), outline=CORAL, width=5)
    plate.text((cx, cy), "CORE", size=22, bold=True,
               fill=_text_tone(CORAL), anchor="mm")
    plate.text((cx, cy - 72), "PENUMBRA", size=18, bold=True,
               fill=_text_tone(GREEN), anchor="mm")
    _measure(plate, (cx - 121, cy + 123), (cx + 121, cy + 123),
             "tissue profile", GREEN, label_at=(cx, cy + 105))
    for index, label in enumerate(("time window", "deficit / function", "risk + contraindications")):
        y = inner[1] + 332 + index * 43
        _landmark(plate, (inner[0] + 42, y), str(index + 1),
                  (BLUE, PLUM, GREEN)[index], size=14, radius=17)
        plate.text((inner[0] + 84, y), label, size=17, bold=True,
                   fill=INK, anchor="lm")


def _draw_brain_tumour(plate: RadiologyPlate, item: Mapping[str, object]) -> None:
    _tag(plate, (800, 227), "LOCALISE BEFORE NAMING THE MASS", PLUM, size=22)
    inner = _panel(plate, (92, 266, 543, 780), "1  COMPARTMENT", BLUE)
    left, right, cy = inner[0] + 111, inner[0] + 312, inner[1] + 165
    for cx in (left, right):
        _brain(plate, (cx, cy), .55)
    plate.draw.ellipse((left + 24, cy - 17, left + 68, cy + 27),
                       fill=hex_rgba(CORAL, 190), outline=INK, width=3)
    plate.draw.ellipse((right + 54, cy - 28, right + 96, cy + 14),
                       fill=hex_rgba(PLUM, 185), outline=INK, width=3)
    plate.draw.line((right + 83, cy - 24, right + 109, cy - 51),
                    fill=PLUM, width=7)
    plate.text((left, cy + 89), "INTRA-AXIAL", size=18, bold=True,
               fill=_text_tone(BLUE), anchor="mm")
    plate.text((right, cy + 89), "EXTRA-AXIAL", size=18, bold=True,
               fill=_text_tone(PLUM), anchor="mm")
    _note(plate, (inner[0] + 5, inner[1] + 286, inner[2] - 5, inner[3]),
          "Use interface, displaced cortex, CSF cleft, dura and bone together; one sign alone can mislead.",
          size=19, tone=INK, bold=True)

    inner = _panel(plate, (565, 266, 1055, 780), "2  MULTIPARAMETRIC", PLUM)
    labels = (("T2 / FLAIR", "water + oedema", BLUE),
              ("DWI + ADC", "paired diffusion", TEAL),
              ("SWI", "blood / mineral", CORAL),
              ("T1 + contrast", "enhancement", PLUM),
              ("perfusion", "vascularity", GOLD),
              ("spectroscopy", "metabolites", GREEN))
    for index, (head, detail, tone) in enumerate(labels):
        col, row = index % 2, index // 2
        x = inner[0] + 109 + col * 232
        y = inner[1] + 73 + row * 108
        plate.draw.rounded_rectangle((x - 96, y - 37, x + 96, y + 37), radius=13,
                                     fill=hex_rgba(PALES[TONES.index(tone)], 115),
                                     outline=tone, width=3)
        plate.text((x, y - 11), head, size=17, bold=True,
                   fill=_text_tone(tone), anchor="mm")
        plate.text((x, y + 18), detail, size=15, fill=INK_SOFT, anchor="mm")
    plate.text(((inner[0] + inner[2]) / 2, inner[1] + 382),
               "concordant pattern > isolated bright spot", size=18,
               bold=True, fill=_text_tone(PLUM), anchor="mm")

    inner = _panel(plate, (1077, 266, 1508, 780), "3  EFFECT + OPERATIVE MAP", CORAL)
    cx, cy = (inner[0] + inner[2]) / 2, inner[1] + 164
    _brain(plate, (cx, cy), .72)
    plate.draw.ellipse((cx + 22, cy - 33, cx + 86, cy + 31),
                       fill=hex_rgba(CORAL, 190), outline=INK, width=4)
    plate.draw.ellipse((cx - 11, cy - 15, cx + 20, cy + 18),
                       outline=INK_SOFT, width=3)
    plate.draw.line((cx - 12, cy - 73, cx - 37, cy + 75), fill=CORAL, width=5)
    _measure(plate, (cx - 9, cy + 102), (cx - 37, cy + 102),
             "shift", CORAL, label_at=(cx - 23, cy + 135))
    checks = ("oedema / herniation", "artery + vein relation", "eloquent cortex / tract")
    for index, label in enumerate(checks):
        y = inner[1] + 315 + index * 39
        _check(plate, (inner[0] + 42, y), radius=16)
        plate.text((inner[0] + 73, y), label, size=17, bold=True,
                   fill=INK, anchor="lm")


def _draw_brain_anatomy(plate: RadiologyPlate, item: Mapping[str, object]) -> None:
    _tag(plate, (433, 227), "ARTERIAL TERRITORIES", BLUE, size=21)
    _tag(plate, (1030, 227), "VENOUS MAP", PLUM, size=21)
    _tag(plate, (1378, 227), "CLINICAL CROSS-CHECK", GREEN, size=19)

    _panel(plate, (92, 266, 775, 780), "LOCATION -> SUPPLYING ARTERY", BLUE)
    cx, cy = 425, 496
    _brain(plate, (cx, cy), 1.16)
    # Bilateral axial schematic: medial ACA, lateral MCA, posterior PCA.
    # These broad regions are not patient-specific sulcal boundaries.
    bounds = (cx - 147, cy - 120, cx + 147, cy + 120)
    plate.draw.ellipse(bounds, fill=BLUE_LIGHT, outline=BLUE, width=3)
    plate.draw.pieslice(bounds, 250, 290,
                        fill=hex_rgba(GOLD_LIGHT, 150), outline=GOLD)
    plate.draw.pieslice(bounds, 35, 145,
                        fill=hex_rgba(PLUM_LIGHT, 170), outline=PLUM)
    plate.draw.line((cx, cy - 120, cx, cy + 120), fill=INK_SOFT, width=2)
    plate.text((425, 416), "ACA", size=20, bold=True,
               fill=_text_tone(GOLD), anchor="mm")
    plate.text((517, 505), "MCA", size=20, bold=True,
               fill=_text_tone(BLUE), anchor="mm")
    plate.text((333, 505), "MCA", size=20, bold=True,
               fill=_text_tone(BLUE), anchor="mm")
    plate.text((425, 578), "PCA", size=20, bold=True,
               fill=_text_tone(PLUM), anchor="mm")
    plate.text((425, 355), "ANTERIOR (axial schematic)", size=16, bold=True,
               fill=INK_SOFT, anchor="mm")
    plate.text((620, 608), "POSTERIOR", size=16, bold=True,
               fill=INK_SOFT, anchor="mm")
    for dx in (-28, 28):
        plate.draw.ellipse((cx + dx - 18, cy - 16, cx + dx + 18, cy + 20),
                           fill=hex_rgba(TEAL_LIGHT, 195), outline=TEAL, width=3)
    plate.text((425, 646), "deep perforators", size=18, bold=True,
               fill=_text_tone(TEAL), anchor="mm")
    plate.text((425, 708), "territories overlap and vary: use vessel imaging when needed",
               size=18, bold=True, fill=INK, anchor="mm")

    inner = _panel(plate, (797, 266, 1245, 780), "SINUSES + CORTICAL VEINS", PLUM)
    cx, cy = 1021, 484
    _brain(plate, (cx, cy), .78, outline=PLUM, fill=PLUM_LIGHT)
    plate.draw.line((cx, cy - 80, cx, cy + 91), fill=PLUM, width=13)
    plate.draw.line((cx, cy + 91, cx - 78, cy + 133), fill=PLUM, width=11)
    plate.draw.line((cx, cy + 91, cx + 78, cy + 133), fill=PLUM, width=11)
    for side in (-1, 1):
        for offset in (-59, -13, 38):
            plate.draw.line((cx + side * 104, cy + offset,
                             cx + side * 11, cy + offset + 18),
                            fill=TEAL, width=5)
    plate.text((cx, cy - 117), "superior sagittal sinus", size=17,
               bold=True, fill=_text_tone(PLUM), anchor="mm")
    plate.text((cx, cy + 173), "venous injury may cross arterial borders", size=17,
               bold=True, fill=INK, anchor="mm")
    _note(plate, (inner[0] + 8, inner[1] + 326, inner[2] - 8, inner[3]),
          "Confirm absent flow against variants and technique before calling thrombosis.",
          size=17, tone=INK, bold=True)

    _panel(plate, (1267, 266, 1508, 780), "FUNCTION", GREEN)
    mapping = (("frontal", "motor / executive"), ("parietal", "sensation / space"),
               ("temporal", "language / memory"), ("occipital", "vision"))
    for index, (region, function) in enumerate(mapping):
        y = 382 + index * 91
        _landmark(plate, (1312, y), str(index + 1),
                  (BLUE, TEAL, PLUM, GREEN)[index], shape="square", size=14)
        plate.text((1357, y - 11), region, size=16, bold=True,
                   fill=INK, anchor="lm")
        plate.text((1357, y + 18), function, size=13,
                   fill=INK_SOFT, anchor="lm")
    plate.draw.line((1296, 718, 1479, 718), fill=GREEN, width=4)
    plate.text((1387, 747), "deficit should fit anatomy", size=15,
               bold=True, fill=_text_tone(GREEN), anchor="mm")


def _draw_cns_infection(plate: RadiologyPlate, item: Mapping[str, object]) -> None:
    boxes = ((92, 220, 555, 790), (568, 220, 1031, 790), (1044, 220, 1508, 790))
    inner = _panel(plate, boxes[0], "ABSCESS PATTERN", BLUE,
                   subtitle="capsule + central paired diffusion")
    cx, cy = (inner[0] + inner[2]) / 2, inner[1] + 169
    plate.draw.ellipse((cx - 104, cy - 88, cx + 104, cy + 88),
                       fill=hex_rgba(BLUE_LIGHT, 65), outline=BLUE, width=4)
    plate.draw.ellipse((cx - 68, cy - 58, cx + 68, cy + 58),
                       fill=hex_rgba(CORAL_LIGHT, 130), outline=CORAL, width=13)
    plate.draw.ellipse((cx - 43, cy - 35, cx + 43, cy + 35),
                       fill=hex_rgba(GOLD_LIGHT, 165), outline=GOLD, width=3)
    plate.text((cx, cy), "CENTRE", size=18, bold=True,
               fill=_text_tone(GOLD), anchor="mm")
    # The paired DWI/ADC requirement is encoded with opposite bars and words.
    for x, head, height, tone, value in ((inner[0] + 105, "DWI", 74, TEAL, "HIGH"),
                                         (inner[0] + 286, "ADC", 25, PLUM, "LOW")):
        base = inner[1] + 359
        plate.draw.line((x, base, x, base - height), fill=tone, width=23)
        plate.text((x, base + 26), head, size=17, bold=True,
                   fill=INK, anchor="mm")
        plate.text((x, base - height - 21), value, size=16, bold=True,
                   fill=_text_tone(tone), anchor="mm")
    plate.text(((inner[0] + inner[2]) / 2, inner[1] + 409),
               "paired DWI-high / ADC-low supports pus",
               size=16, bold=True, fill=INK, anchor="mm")

    inner = _panel(plate, boxes[1], "ENCEPHALITIS DISTRIBUTION", PLUM,
                   subtitle="parenchymal pattern suggests, not proves")
    cx, cy = (inner[0] + inner[2]) / 2, inner[1] + 177
    _brain(plate, (cx, cy), .94, outline=PLUM, fill=PLUM_LIGHT)
    for dx, dy in ((-67, 35), (-26, 58), (52, 27)):
        plate.draw.ellipse((cx + dx - 31, cy + dy - 22,
                            cx + dx + 31, cy + dy + 22),
                           fill=hex_rgba(PLUM, 135), outline=PLUM, width=3)
    _arrow(plate, (inner[2] - 25, inner[1] + 70), (cx + 51, cy + 16),
           "regional signal", PLUM, label_at=(inner[2] - 107, inner[1] + 47), width=5)
    plate.draw.rounded_rectangle((inner[0] + 36, inner[1] + 333,
                                  inner[2] - 36, inner[1] + 397), radius=13,
                                 fill=hex_rgba(CORAL_LIGHT, 100), outline=CORAL, width=3)
    plate.text(((inner[0] + inner[2]) / 2, inner[1] + 365),
               "NOT A PATHOGEN LABEL", size=18, bold=True,
               fill=_text_tone(CORAL), anchor="mm")
    plate.text(((inner[0] + inner[2]) / 2, inner[1] + 411),
               "tempo + CSF + host narrow the cause", size=16,
               bold=True, fill=INK, anchor="mm")

    inner = _panel(plate, boxes[2], "HOST + DIFFERENTIAL", CORAL,
                   subtitle="infection and mimic change together")
    matrix = (("immune setting", "organisms", "mimics"),
              ("intact", "common + exposure", "tumour / inflammation"),
              ("suppressed", "opportunistic", "therapy + tumour"))
    x0, y0, widths, row_h = inner[0] + 4, inner[1] + 41, (128, 124, 126), 92
    for row, values in enumerate(matrix):
        x = x0
        for col, (value, width) in enumerate(zip(values, widths)):
            plate.draw.rectangle((x, y0 + row * row_h, x + width,
                                  y0 + (row + 1) * row_h),
                                 fill=hex_rgba(PALES[(row + col) % 6], 75),
                                 outline=GRID, width=2)
            _note(plate, (x + 8, y0 + row * row_h + 5,
                          x + width - 8, y0 + (row + 1) * row_h - 5),
                  value, size=15 if row else 16, tone=INK, bold=row == 0)
            x += width
    plate.text(((inner[0] + inner[2]) / 2, inner[1] + 362),
               "same ring pattern != same diagnosis", size=18,
               bold=True, fill=_text_tone(CORAL), anchor="mm")
    plate.text(((inner[0] + inner[2]) / 2, inner[1] + 411),
               "urgency follows patient + compartment", size=16,
               bold=True, fill=INK, anchor="mm")


def _draw_venous_csf(plate: RadiologyPlate, item: Mapping[str, object]) -> None:
    boxes = ((92, 220, 555, 790), (568, 220, 1031, 790), (1044, 220, 1508, 790))
    inner = _panel(plate, boxes[0], "VENOUS THROMBOSIS", PLUM,
                   subtitle="prove a filling / flow defect; exclude variant")
    cx, cy = (inner[0] + inner[2]) / 2, inner[1] + 177
    _brain(plate, (cx, cy), .91, outline=PLUM, fill=PLUM_LIGHT)
    plate.draw.line((cx, cy - 82, cx, cy + 82), fill=PLUM, width=14)
    plate.draw.line((cx, cy - 1, cx, cy + 43), fill=PAPER_LIGHT, width=11)
    plate.draw.line((cx, cy - 1, cx, cy + 43), fill=CORAL, width=3)
    _arrow(plate, (inner[2] - 28, inner[1] + 78), (cx + 6, cy + 21),
           "defect", CORAL, label_at=(inner[2] - 83, inner[1] + 57), width=5)
    plate.text((cx, inner[1] + 324), "check source images + alternate planes", size=18,
               bold=True, fill=INK, anchor="mm")
    _tag(plate, (cx, inner[1] + 354), "VARIANT / TIMING CHECK", PLUM, size=18)
    _note(plate, (inner[0] + 12, inner[1] + 382, inner[2] - 12, inner[3]),
          "Asymmetry may be normal: verify source images and technique.",
          size=16, tone=INK, bold=True)

    inner = _panel(plate, boxes[1], "RAISED PRESSURE CLUES", BLUE)
    # Eye/orbit, sella and venous clues are grouped as supporting signs.
    cx, cy = inner[0] + 140, inner[1] + 142
    plate.draw.ellipse((cx - 70, cy - 48, cx + 70, cy + 48),
                       fill=hex_rgba(BLUE_LIGHT, 90), outline=BLUE, width=4)
    plate.draw.ellipse((cx - 29, cy - 29, cx + 29, cy + 29),
                       fill=PAPER_LIGHT, outline=INK_SOFT, width=3)
    plate.draw.line((cx - 123, cy, cx - 70, cy), fill=GOLD, width=18)
    _measure(plate, (cx - 116, cy - 29), (cx - 116, cy + 29),
             "sheath", GOLD, label_at=(cx - 79, cy + 78))
    plate.draw.arc((inner[0] + 237, inner[1] + 89,
                    inner[0] + 366, inner[1] + 200), 192, 349,
                   fill=PLUM, width=9)
    plate.text((inner[0] + 301, inner[1] + 219), "sella", size=17,
               bold=True, fill=_text_tone(PLUM), anchor="mm")
    signs = ("optic-nerve / globe signs", "sella + ventricular context",
             "venous cause or narrowing")
    for index, label in enumerate(signs):
        y = inner[1] + 285 + index * 49
        _landmark(plate, (inner[0] + 43, y), str(index + 1),
                  (GOLD, PLUM, BLUE)[index], size=14, radius=18)
        plate.text((inner[0] + 86, y), label, size=17, bold=True,
                   fill=INK, anchor="lm")
    plate.text(((inner[0] + inner[2]) / 2, inner[1] + 445),
               "supportive pattern, not a diagnosis", size=16,
               bold=True, fill=_text_tone(BLUE), anchor="mm")

    inner = _panel(plate, boxes[2], "LOW PRESSURE / CSF LOSS", TEAL)
    cx, cy = (inner[0] + inner[2]) / 2, inner[1] + 184
    # Sagittal schematic with lowered brainstem and diffuse dural outline.
    plate.draw.ellipse((cx - 122, cy - 99, cx + 97, cy + 84),
                       fill=hex_rgba(TEAL_LIGHT, 80), outline=TEAL, width=5)
    plate.draw.arc((cx - 130, cy - 107, cx + 105, cy + 92), 18, 342,
                   fill=PLUM, width=10)
    plate.draw.line((cx + 3, cy + 56, cx + 8, cy + 136), fill=TEAL, width=18)
    _arrow(plate, (cx + 62, cy + 41), (cx + 22, cy + 101),
           "sag", TEAL, label_at=(cx + 90, cy + 82), width=5)
    plate.text((cx, inner[1] + 348), "diffuse dural enhancement + brain sag", size=18,
               bold=True, fill=_text_tone(TEAL), anchor="mm")
    _note(plate, (inner[0] + 8, inner[1] + 378, inner[2] - 8, inner[3]),
          "Correlate with symptoms and search for a leak using the appropriate pathway.",
          size=18, tone=INK, bold=True)


def _draw_dementia(plate: RadiologyPlate, item: Mapping[str, object]) -> None:
    _tag(plate, (800, 227), "REGIONAL ATROPHY IS EVIDENCE, NOT A DIAGNOSIS", PLUM, size=22)
    inner = _panel(plate, (92, 266, 600, 780), "MEDIAL TEMPORAL COMPARISON", BLUE,
                   subtitle="judge against age and whole-brain context")
    for index, (cx, label, hip_size) in enumerate(((225, "reference", 31),
                                                    (467, "disproportionate loss", 16))):
        cy = inner[1] + 170
        _brain(plate, (cx, cy), .66)
        for dx in (-31, 31):
            plate.draw.ellipse((cx + dx - hip_size, cy + 22 - hip_size * .58,
                                cx + dx + hip_size, cy + 22 + hip_size * .58),
                               fill=hex_rgba(GOLD_LIGHT, 160), outline=GOLD, width=4)
        plate.text((cx, cy + 95), label, size=16, bold=True,
                   fill=_text_tone(BLUE if index == 0 else CORAL), anchor="mm")
    _measure(plate, (225, inner[1] + 278), (467, inner[1] + 278),
             "compare pattern, not raw size", BLUE, label_at=(346, inner[1] + 307))
    plate.text(((inner[0] + inner[2]) / 2, inner[1] + 354),
               "supports phenotype only with clinical fit", size=17,
               bold=True, fill=INK, anchor="mm")

    inner = _panel(plate, (622, 266, 1105, 780), "REGIONAL PREDOMINANCE", PLUM)
    cx, cy = (inner[0] + inner[2]) / 2, inner[1] + 172
    _brain(plate, (cx, cy), .91, outline=PLUM, fill=PLUM_LIGHT)
    regions = (((cx, cy - 67), "frontal", BLUE),
               ((cx - 78, cy + 14), "temporal", GOLD),
               ((cx + 73, cy + 39), "posterior", PLUM))
    for (rx, ry), label, tone in regions:
        plate.draw.ellipse((rx - 41, ry - 28, rx + 41, ry + 28),
                           fill=hex_rgba(PALES[TONES.index(tone)], 145),
                           outline=tone, width=4)
        plate.text((rx, ry), label, size=15, bold=True,
                   fill=_text_tone(tone), anchor="mm")
    plate.text((cx, inner[1] + 326), "predominant region -> phenotype hypothesis", size=17,
               bold=True, fill=_text_tone(PLUM), anchor="mm")
    plate.text(((inner[0] + inner[2]) / 2, inner[1] + 405),
               "overlap and mixed pathology remain common", size=16,
               bold=True, fill=INK, anchor="mm")

    inner = _panel(plate, (1127, 266, 1508, 780), "TREATABLE MIMIC CHECK", GREEN)
    cx, cy = (inner[0] + inner[2]) / 2, inner[1] + 165
    _brain(plate, (cx, cy), .82, outline=GREEN, fill=GREEN_LIGHT)
    for dx in (-36, 36):
        plate.draw.ellipse((cx + dx - 32, cy - 31, cx + dx + 32, cy + 41),
                           fill=hex_rgba(BLUE_LIGHT, 180), outline=BLUE, width=4)
    _measure(plate, (cx - 69, cy + 91), (cx + 69, cy + 91),
             "ventricular pattern", GREEN, label_at=(cx, cy + 111))
    gates = (("gait", "clinical"), ("cognition", "fit"), ("urinary", "context"))
    for index, (head, sub) in enumerate(gates):
        y = inner[1] + 322 + index * 36
        _landmark(plate, (inner[0] + 39, y), str(index + 1), GREEN,
                  size=13, radius=15)
        plate.text((inner[0] + 78, y - 8), head, size=17, bold=True,
                   fill=INK, anchor="lm")
        plate.text((inner[2] - 9, y + 10), sub, size=14,
                   fill=INK_SOFT, anchor="ra")


def _draw_epilepsy_mri(plate: RadiologyPlate, item: Mapping[str, object]) -> None:
    _tag(plate, (800, 227), "CORE HARNESS ACQUISITION -> CONCORDANT LOCALISATION", BLUE, size=21)
    inner = _panel(plate, (92, 266, 720, 780), "1  CORE HARNESS", BLUE,
                   subtitle="standard geometry makes subtle structure reviewable")
    acquisitions = (("3D T1", "isotropic", BLUE, "cube"),
                    ("3D FLAIR", "isotropic", PLUM, "cube"),
                    ("CORONAL T2", "perpendicular to hippocampi", TEAL, "plane"))
    for index, (head, detail, tone, kind) in enumerate(acquisitions):
        x = inner[0] + 105 + index * 196
        y = inner[1] + 167
        if kind == "cube":
            plate.draw.rectangle((x - 50, y - 50, x + 50, y + 50),
                                 fill=hex_rgba(PALES[TONES.index(tone)], 120),
                                 outline=tone, width=4)
            plate.draw.polygon(((x - 50, y - 50), (x - 17, y - 78),
                                (x + 82, y - 78), (x + 50, y - 50)),
                               fill=hex_rgba(PALES[TONES.index(tone)], 80),
                               outline=tone)
            plate.draw.line((x + 50, y - 50, x + 82, y - 78,
                             x + 82, y + 20, x + 50, y + 50),
                            fill=tone, width=4)
            for shift in (-24, 0, 24):
                plate.draw.line((x - 44, y + shift, x + 44, y + shift),
                                fill=hex_rgba(tone, 110), width=2)
        else:
            plate.draw.ellipse((x - 82, y - 57, x + 82, y + 57),
                               fill=hex_rgba(TEAL_LIGHT, 90), outline=TEAL, width=4)
            # Sagittal planning schematic: a long axis and a truly orthogonal
            # coronal acquisition plane (dot product 60*24-24*60 = 0).
            plate.draw.line((x - 60, y + 24, x + 60, y - 24),
                            fill=GOLD_LIGHT, width=24)
            plate.draw.line((x - 60, y + 24, x + 60, y - 24),
                            fill=GOLD, width=4)
            plate.draw.line((x - 24, y - 60, x + 24, y + 60),
                            fill=CORAL, width=6)
            plate.text((x, y + 85), "long axis / plane", size=15,
                       fill=INK_SOFT, anchor="mm")
        plate.text((x, inner[1] + 286), head, size=18, bold=True,
                   fill=_text_tone(tone), anchor="mm")
        _note(plate, (x - 85, inner[1] + 309, x + 85, inner[1] + 371),
              detail, size=16, tone=INK, bold=True)

    inner = _panel(plate, (742, 266, 1174, 780), "2  CONCORDANT SEARCH", PLUM)
    cx, cy = (inner[0] + inner[2]) / 2, inner[1] + 176
    _brain(plate, (cx, cy), .76, outline=PLUM, fill=PLUM_LIGHT)
    target = (cx - 61, cy + 34)
    plate.draw.ellipse((target[0] - 23, target[1] - 16,
                        target[0] + 23, target[1] + 16),
                       fill=hex_rgba(CORAL, 170), outline=CORAL, width=4)
    links = (((inner[0] + 46, inner[1] + 296), "MRI", BLUE),
             ((cx, inner[1] + 342), "EEG", TEAL),
             ((inner[2] - 46, inner[1] + 296), "semiology", GOLD))
    for position, label, tone in links:
        _landmark(plate, position, label, tone, shape="square", size=14)
        _arrow(plate, position, target, "", tone, width=4, head=11)
    plate.text((cx, inner[1] + 400), "agreement strengthens localisation",
               size=17, bold=True, fill=_text_tone(PLUM), anchor="mm")

    inner = _panel(plate, (1196, 266, 1508, 780), "3  IF NEGATIVE", GREEN)
    steps = (("1", "re-review with hypothesis"), ("2", "check acquisition / motion"),
             ("3", "advanced methods if indicated"))
    for index, (number, label) in enumerate(steps):
        y = inner[1] + 86 + index * 112
        _landmark(plate, (inner[0] + 43, y), number,
                  (BLUE, PLUM, GREEN)[index], shape="square", size=15)
        _note(plate, (inner[0] + 85, y - 37, inner[2] - 5, y + 37),
              label, size=17, tone=INK, bold=True)
        if index < 2:
            _arrow(plate, (inner[0] + 43, y + 31),
                   (inner[0] + 43, y + 78), "", GREEN, width=4, head=11)
    plate.draw.line((inner[0] + 26, inner[1] + 370,
                     inner[2] - 26, inner[1] + 370), fill=GREEN, width=4)
    plate.text(((inner[0] + inner[2]) / 2, inner[1] + 398),
               "negative MRI != no epilepsy", size=17, bold=True,
               fill=_text_tone(GREEN), anchor="mm")


def _draw_head_trauma(plate: RadiologyPlate, item: Mapping[str, object]) -> None:
    _tag(plate, (800, 227), "TRIAGE IMMEDIATE THREATS, THEN FOLLOW THE MECHANISM", CORAL, size=21)
    inner = _panel(plate, (92, 266, 493, 780), "1  SELECT + TIME", BLUE)
    timeline_y = inner[1] + 193
    plate.arrow((inner[0] + 35, timeline_y), (inner[2] - 29, timeline_y),
                fill=INK_SOFT, width=5, head=15)
    for index, (label, tone) in enumerate((("NOW", CORAL), ("WATCH", GOLD),
                                           ("REPEAT*", BLUE))):
        x = inner[0] + 67 + index * 118
        plate.draw.line((x, timeline_y - 17, x, timeline_y + 17),
                        fill=tone, width=5)
        plate.text((x, timeline_y - 40), label, size=14, bold=True,
                   fill=_text_tone(tone), anchor="mm")
    _note(plate, (inner[0] + 8, inner[1] + 264, inner[2] - 8, inner[3]),
          "Clinical risk determines whether CT is immediate, deferred or repeated; the diagram is not a stand-alone rule.",
          size=19, tone=INK, bold=True)

    inner = _panel(plate, (515, 266, 1035, 780), "2  IMMEDIATE THREAT", CORAL)
    cx, cy = (inner[0] + inner[2]) / 2, inner[1] + 177
    _brain(plate, (cx, cy), .90, outline=CORAL, fill=CORAL_LIGHT)
    # Crescent blood, focal contusion and midline displacement are distinct.
    plate.draw.arc((cx - 121, cy - 94, cx + 121, cy + 94), 285, 72,
                   fill=CORAL, width=24)
    plate.draw.ellipse((cx - 83, cy + 5, cx - 32, cy + 50),
                       fill=hex_rgba(PLUM, 180), outline=PLUM, width=3)
    plate.draw.line((cx - 11, cy - 74, cx - 36, cy + 76),
                    fill=BLUE, width=5)
    _measure(plate, (cx - 9, cy + 111), (cx - 36, cy + 111),
             "shift", CORAL, label_at=(cx + 83, cy + 116))
    for index, label in enumerate(("blood compartment", "swelling / herniation",
                                   "fracture + pneumocephalus")):
        y = inner[1] + 322 + index * 38
        _check(plate, (inner[0] + 44, y), radius=16)
        plate.text((inner[0] + 75, y), label, size=17, bold=True,
                   fill=INK, anchor="lm")

    inner = _panel(plate, (1057, 266, 1508, 780), "3  EXTEND WHEN INDICATED", PLUM)
    branches = (("artery / venous sinus risk", "CTA / CTV as indicated", CORAL),
                ("unexplained deficit", "MRI for axonal injury", PLUM),
                ("clinical deterioration", "urgent repeat / escalate", GREEN))
    for index, (trigger, test, tone) in enumerate(branches):
        y = inner[1] + 84 + index * 119
        plate.draw.rounded_rectangle((inner[0] + 13, y - 38, inner[0] + 183, y + 38),
                                     radius=12, fill=hex_rgba(PALES[TONES.index(tone)], 100),
                                     outline=tone, width=3)
        _note(plate, (inner[0] + 23, y - 32, inner[0] + 173, y + 32),
              trigger, size=16, tone=INK, bold=True)
        _arrow(plate, (inner[0] + 188, y), (inner[0] + 233, y), "", tone,
               width=4, head=12)
        plate.draw.rounded_rectangle((inner[0] + 241, y - 38, inner[2] - 12, y + 38),
                                     radius=12, fill=hex_rgba(PAPER_LIGHT, 225),
                                     outline=tone, width=3)
        _note(plate, (inner[0] + 251, y - 32, inner[2] - 22, y + 32),
              test, size=16, tone=_text_tone(tone), bold=True)
    plate.text(((inner[0] + inner[2]) / 2, inner[1] + 405),
               "mechanism chooses the added test", size=17, bold=True,
               fill=_text_tone(PLUM), anchor="mm")


def _draw_intracranial_haemorrhage(plate: RadiologyPlate,
                                   item: Mapping[str, object]) -> None:
    boxes = ((92, 220, 555, 790), (568, 220, 1031, 790), (1044, 220, 1508, 790))
    inner = _panel(plate, boxes[0], "EXTRA-AXIAL SHAPE", BLUE,
                   subtitle="epidural lens vs subdural crescent")
    left, right, cy = inner[0] + 111, inner[0] + 314, inner[1] + 173
    for cx in (left, right):
        _brain(plate, (cx, cy), .56)
    # Convex lens and concave crescent are encoded by geometry and labels.
    plate.draw.ellipse((left + 46, cy - 51, left + 81, cy + 51),
                       fill=hex_rgba(CORAL, 200), outline=CORAL, width=3)
    plate.draw.arc((right - 71, cy - 72, right + 75, cy + 72), 275, 85,
                   fill=PLUM, width=22)
    plate.text((left, cy + 91), "EPIDURAL: BICONVEX", size=15, bold=True,
               fill=_text_tone(CORAL), anchor="mm")
    plate.text((right, cy + 91), "SUBDURAL: CRESCENT", size=15, bold=True,
               fill=_text_tone(PLUM), anchor="mm")
    _note(plate, (inner[0] + 8, inner[1] + 304, inner[2] - 8, inner[3]),
          "Compartment geometry points to a meningeal space and likely mechanism; mass effect sets urgency.",
          size=19, tone=INK, bold=True)

    inner = _panel(plate, boxes[1], "INTRAPARENCHYMAL", CORAL,
                   subtitle="location + ventricular extension")
    cx, cy = (inner[0] + inner[2]) / 2, inner[1] + 176
    _brain(plate, (cx, cy), .91, outline=CORAL, fill=CORAL_LIGHT)
    plate.draw.ellipse((cx + 7, cy - 30, cx + 76, cy + 39),
                       fill=hex_rgba(CORAL, 205), outline=INK, width=4)
    plate.draw.line((cx + 25, cy + 12, cx + 3, cy + 18), fill=CORAL, width=12)
    _arrow(plate, (inner[2] - 24, inner[1] + 71), (cx + 56, cy - 17),
           "focus", CORAL, label_at=(inner[2] - 75, inner[1] + 49), width=5)
    plate.text((cx, inner[1] + 328), "lobar / deep / posterior fossa", size=18,
               bold=True, fill=_text_tone(CORAL), anchor="mm")
    _note(plate, (inner[0] + 8, inner[1] + 356, inner[2] - 8, inner[3]),
          "Age, location, anticoagulation and vessel pattern determine the next aetiologic test.",
          size=18, tone=INK, bold=True)

    inner = _panel(plate, boxes[2], "SUBARACHNOID", PLUM,
                   subtitle="blood follows cisterns and sulci")
    cx, cy = (inner[0] + inner[2]) / 2, inner[1] + 176
    _brain(plate, (cx, cy), .91, outline=PLUM, fill=PLUM_LIGHT)
    plate.draw.ellipse((cx - 31, cy - 23, cx + 31, cy + 24),
                       outline=PLUM, width=12)
    for angle in (18, 62, 116, 164, 224, 276, 325):
        r = math.radians(angle)
        x0, y0 = cx + math.cos(r) * 43, cy + math.sin(r) * 33
        x1, y1 = cx + math.cos(r) * 102, cy + math.sin(r) * 76
        plate.draw.line((x0, y0, x1, y1), fill=PLUM, width=8)
    plate.text((cx, inner[1] + 328), "basal cisterns + cortical sulci", size=18,
               bold=True, fill=_text_tone(PLUM), anchor="mm")
    _tag(plate, (cx, inner[1] + 354), "URGENT VESSEL WORK-UP IF INDICATED", CORAL, size=15)
    _note(plate, (inner[0] + 10, inner[1] + 383, inner[2] - 10, inner[3]),
          "Distribution and setting choose the traumatic or spontaneous pathway.",
          size=16, tone=INK, bold=True)


def _draw_ms_white_matter(plate: RadiologyPlate, item: Mapping[str, object]) -> None:
    _tag(plate, (800, 227), "DISTRIBUTION + LESION-SPECIFIC SIGNS, NOT SPOT COUNT", BLUE, size=21)
    inner = _panel(plate, (92, 266, 630, 780), "1  CHARACTERISTIC REGIONS", BLUE)
    cx, cy = (inner[0] + inner[2]) / 2, inner[1] + 177
    _brain(plate, (cx, cy), .98)
    # Periventricular fingers, juxtacortical and infratentorial lesions.
    for dx in (-61, -25, 24, 62):
        plate.draw.ellipse((cx + dx - 8, cy - 61, cx + dx + 8, cy - 16),
                           fill=hex_rgba(BLUE, 165), outline=BLUE, width=2)
    for dx in (-92, 91):
        plate.draw.ellipse((cx + dx - 13, cy - 12, cx + dx + 13, cy + 14),
                           fill=hex_rgba(TEAL, 170), outline=TEAL, width=2)
    # Separate hindbrain inset: an infratentorial lesion must not appear
    # inside the supratentorial cerebral slice.
    hx, hy = cx + 192, cy + 78
    plate.draw.ellipse((hx - 42, hy - 30, hx + 42, hy + 30),
                       fill=PLUM_LIGHT, outline=PLUM, width=3)
    plate.draw.line((hx, hy - 39, hx, hy + 39), fill=TEAL, width=9)
    plate.draw.ellipse((hx - 29, hy - 10, hx - 10, hy + 9),
                       fill=hex_rgba(PLUM, 170), outline=PLUM, width=2)
    plate.text((hx, hy + 52), "hindbrain inset", size=13,
               fill=INK_SOFT, anchor="mm")
    labels = (("periventricular", BLUE), ("cortical / juxtacortical", TEAL),
              ("infratentorial", PLUM))
    for index, (label, tone) in enumerate(labels):
        y = inner[1] + 292 + index * 38
        plate.draw.line((inner[0] + 22, y, inner[0] + 54, y), fill=tone, width=8)
        plate.text((inner[0] + 70, y), label, size=17, bold=True,
                   fill=INK, anchor="lm")
    plate.text((cx, inner[1] + 405), "separate regions establish dissemination in space",
               size=16, bold=True, fill=_text_tone(BLUE), anchor="mm")

    inner = _panel(plate, (652, 266, 1058, 780), "2  CORD + OPTIC NERVE", TEAL)
    # Cord with short-segment lesion and an orbital nerve comparator.
    cord_x = inner[0] + 111
    plate.draw.rounded_rectangle((cord_x - 35, inner[1] + 65,
                                  cord_x + 35, inner[1] + 307), radius=28,
                                 fill=hex_rgba(TEAL_LIGHT, 100), outline=TEAL, width=5)
    plate.draw.ellipse((cord_x - 21, inner[1] + 172,
                        cord_x + 21, inner[1] + 224),
                       fill=hex_rgba(CORAL, 175), outline=CORAL, width=3)
    _measure(plate, (cord_x + 58, inner[1] + 172),
             (cord_x + 58, inner[1] + 224), "short segment", CORAL,
             label_at=(cord_x + 112, inner[1] + 198))
    eye_x, eye_y = inner[0] + 295, inner[1] + 157
    plate.draw.ellipse((eye_x - 63, eye_y - 45, eye_x + 63, eye_y + 45),
                       fill=hex_rgba(BLUE_LIGHT, 90), outline=BLUE, width=4)
    plate.draw.ellipse((eye_x - 25, eye_y - 25, eye_x + 25, eye_y + 25),
                       fill=PAPER_LIGHT, outline=INK_SOFT, width=3)
    plate.draw.line((eye_x - 115, eye_y, eye_x - 62, eye_y),
                    fill=CORAL, width=18)
    plate.text((eye_x, inner[1] + 246), "optic nerve", size=18, bold=True,
               fill=_text_tone(TEAL), anchor="mm")
    _note(plate, (inner[0] + 8, inner[1] + 337, inner[2] - 8, inner[3]),
          "Typical cord and optic-nerve sites add dissemination; mimics differ in length or distribution.",
          size=17, tone=INK, bold=True)

    inner = _panel(plate, (1080, 266, 1508, 780), "3  LESION-SPECIFIC SIGNS", PLUM)
    signs = (("CENTRAL VEIN", "perivenular origin", BLUE),
             ("ENHANCEMENT", "current activity", CORAL),
             ("PARAMAGNETIC RIM", "chronic active edge", PLUM))
    for index, (head, detail, tone) in enumerate(signs):
        y = inner[1] + 86 + index * 118
        cx = inner[0] + 78
        plate.draw.ellipse((cx - 39, y - 31, cx + 39, y + 31),
                           fill=hex_rgba(PALES[TONES.index(tone)], 120),
                           outline=tone, width=5)
        if index == 0:
            plate.draw.line((cx, y - 42, cx, y + 42), fill=BLUE, width=6)
        elif index == 1:
            plate.draw.ellipse((cx - 26, y - 20, cx + 26, y + 20),
                               fill=hex_rgba(CORAL, 155))
        else:
            plate.draw.ellipse((cx - 29, y - 22, cx + 29, y + 22),
                               outline=PLUM, width=8)
        plate.text((inner[0] + 136, y - 13), head, size=17, bold=True,
                   fill=_text_tone(tone), anchor="lm")
        plate.text((inner[0] + 136, y + 17), detail, size=16,
                   fill=INK_SOFT, anchor="lm")
    plate.text(((inner[0] + inner[2]) / 2, inner[1] + 392),
               "supportive signs answer distinct questions", size=17,
               bold=True, fill=_text_tone(PLUM), anchor="mm")


def _draw_spine_imaging(plate: RadiologyPlate, item: Mapping[str, object]) -> None:
    boxes = ((92, 220, 555, 790), (568, 220, 1031, 790), (1044, 220, 1508, 790))
    inner = _panel(plate, boxes[0], "DISC + ROOT RELATION", BLUE,
                   subtitle="name level, direction and contact")
    cx = (inner[0] + inner[2]) / 2
    for index in range(5):
        y = inner[1] + 57 + index * 72
        plate.draw.rounded_rectangle((cx - 100, y, cx + 100, y + 43), radius=8,
                                     fill=hex_rgba(GOLD_LIGHT, 160), outline=GOLD, width=3)
        if index < 4:
            plate.draw.line((cx - 91, y + 55, cx + 91, y + 55),
                            fill=BLUE, width=11)
    # Focal posterior-lateral protrusion and exiting root.
    lesion_y = inner[1] + 57 + 2 * 72 + 55
    plate.draw.polygon(((cx + 22, lesion_y - 7), (cx + 102, lesion_y - 3),
                        (cx + 79, lesion_y + 22), (cx + 26, lesion_y + 7)),
                       fill=hex_rgba(CORAL, 180), outline=CORAL)
    plate.draw.line((cx + 100, lesion_y + 10, cx + 155, lesion_y + 57),
                    fill=PLUM, width=8)
    _arrow(plate, (inner[2] - 17, inner[1] + 78), (cx + 77, lesion_y + 8),
           "posterolateral", CORAL, label_at=(inner[2] - 92, inner[1] + 54), width=5)
    plate.text((cx, inner[1] + 412), "contact  !=  displacement  !=  compression",
               size=17, bold=True, fill=_text_tone(BLUE), anchor="mm")

    inner = _panel(plate, boxes[1], "COMPRESSION CANNOT WAIT", CORAL)
    cx = (inner[0] + inner[2]) / 2
    plate.draw.rounded_rectangle((cx - 55, inner[1] + 49, cx + 55, inner[1] + 345),
                                 radius=44, fill=hex_rgba(TEAL_LIGHT, 80),
                                 outline=TEAL, width=5)
    top = inner[1]
    plate.draw.polygon(((cx - 16, top + 67), (cx + 16, top + 67),
                        (cx + 16, top + 327), (cx - 16, top + 327),
                        (cx - 16, top + 258), (cx + 5, top + 218),
                        (cx - 16, top + 178)),
                       fill=hex_rgba(BLUE, 155), outline=BLUE)
    plate.draw.ellipse((cx - 74, inner[1] + 184, cx + 6, inner[1] + 251),
                       fill=hex_rgba(CORAL, 185), outline=CORAL, width=4)
    _arrow(plate, (cx + 130, inner[1] + 218), (cx + 10, inner[1] + 218),
           "cord deformation", CORAL, label_at=(cx + 82, inner[1] + 183))
    for index, label in enumerate(("cord signal", "cauda equina", "epidural disease")):
        y = inner[1] + 378 + index * 37
        plate.text((inner[0] + 31, y), str(index + 1) + "  " + label,
                   size=17, bold=True, fill=INK, anchor="lm")

    inner = _panel(plate, boxes[2], "TRAUMA: STABILITY", PLUM)
    cx = (inner[0] + inner[2]) / 2
    centers = []
    for index in range(5):
        y = inner[1] + 54 + index * 72
        shift = 31 if index >= 3 else 0
        centers.append((cx + shift, y + 21))
        plate.draw.rounded_rectangle((cx - 91 + shift, y, cx + 91 + shift, y + 43),
                                     radius=8, fill=hex_rgba(GOLD_LIGHT, 155),
                                     outline=GOLD, width=3)
    # Posterior alignment line makes step-off visible.
    plate.draw.line(tuple(coord for point in centers for coord in (point[0] + 92, point[1])),
                    fill=PLUM, width=5, joint="curve")
    plate.draw.line((cx - 36, inner[1] + 47, cx - 9, inner[1] + 346),
                    fill=TEAL, width=7)
    plate.draw.line((cx - 30, inner[1] + 227, cx + 19, inner[1] + 268),
                    fill=CORAL, width=7)
    plate.text((cx, inner[1] + 407), "alignment + ligament + marrow", size=18,
               bold=True, fill=_text_tone(PLUM), anchor="mm")
    _note(plate, (inner[0] + 8, inner[1] + 422, inner[2] - 8, inner[3]),
          "Instability is a relationship across structures, not a single bright line.",
          size=17, tone=INK, bold=True)


def _draw_neck_nodes(plate: RadiologyPlate, item: Mapping[str, object]) -> None:
    _tag(plate, (800, 227), "LEVEL + MORPHOLOGY + DRAINAGE TERRITORY", TEAL, size=22)
    inner = _panel(plate, (92, 266, 695, 780), "1  ASSIGN A CERVICAL LEVEL", BLUE,
                   subtitle="landmarks assign a map coordinate, not a diagnosis")
    cx = 367
    # Frontal neck orientation with paired SCM and jugular chains.
    plate.draw.arc((cx - 105, inner[1] + 29, cx + 105, inner[1] + 194), 180, 360,
                   fill=INK_SOFT, width=5)
    plate.draw.line((cx - 80, inner[1] + 102, cx - 133, inner[1] + 374),
                    fill=GOLD, width=15)
    plate.draw.line((cx + 80, inner[1] + 102, cx + 133, inner[1] + 374),
                    fill=GOLD, width=15)
    plate.draw.line((cx - 54, inner[1] + 123, cx - 75, inner[1] + 377),
                    fill=BLUE, width=9)
    plate.draw.line((cx + 54, inner[1] + 123, cx + 75, inner[1] + 377),
                    fill=BLUE, width=9)
    hyoid_y = inner[1] + 245
    plate.draw.line((cx - 159, hyoid_y, cx + 159, hyoid_y),
                    fill=PLUM, width=5)
    plate.text((cx + 173, hyoid_y), "hyoid", size=16, bold=True,
               fill=_text_tone(PLUM), anchor="lm")
    cricoid_y = inner[1] + 322
    plate.draw.line((cx - 159, cricoid_y, cx + 159, cricoid_y),
                    fill=INK_SOFT, width=3)
    plate.text((cx + 173, cricoid_y), "cricoid", size=16, bold=True,
               fill=INK_SOFT, anchor="lm")
    positions = ((cx - 22, inner[1] + 118, "I"),
                 (cx - 95, inner[1] + 181, "II"),
                 (cx - 92, inner[1] + 281, "III"),
                 (cx - 99, inner[1] + 365, "IV"),
                 (cx + 170, inner[1] + 280, "V"),
                 (cx, inner[1] + 333, "VI"))
    for index, (x, y, label) in enumerate(positions):
        _landmark(plate, (x, y), label, TONES[index % len(TONES)], size=14)
    inner = _panel(plate, (717, 266, 1117, 780), "2  JUDGE MORPHOLOGY", CORAL)
    examples = (("oval + fatty hilum", "context dependent", GREEN, "oval"),
                ("round + necrotic", "raises concern", CORAL, "round"),
                ("irregular margin", "assess extranodal spread", PLUM, "irregular"))
    for index, (head, detail, tone, shape) in enumerate(examples):
        y = inner[1] + 84 + index * 115
        cx = inner[0] + 75
        if shape == "oval":
            plate.draw.ellipse((cx - 49, y - 27, cx + 49, y + 27),
                               fill=hex_rgba(GREEN_LIGHT, 110), outline=GREEN, width=4)
            plate.draw.ellipse((cx - 25, y - 8, cx + 25, y + 8), fill=GOLD_LIGHT)
        elif shape == "round":
            plate.draw.ellipse((cx - 38, y - 38, cx + 38, y + 38),
                               fill=hex_rgba(CORAL_LIGHT, 130), outline=CORAL, width=5)
            plate.draw.ellipse((cx - 18, y - 18, cx + 18, y + 18),
                               fill=PAPER_LIGHT, outline=CORAL, width=3)
        else:
            points = tuple((cx + math.cos(math.radians(a)) * (45 if a % 60 else 58),
                            y + math.sin(math.radians(a)) * (36 if a % 60 else 49))
                           for a in range(0, 360, 30))
            plate.draw.polygon(points, fill=hex_rgba(PLUM_LIGHT, 135), outline=PLUM)
        plate.text((inner[0] + 143, y - 12), head, size=17, bold=True,
                   fill=_text_tone(tone), anchor="lm")
        plate.text((inner[0] + 143, y + 19), detail, size=15,
                   fill=INK_SOFT, anchor="lm")
    plate.text(((inner[0] + inner[2]) / 2, inner[1] + 397),
               "size alone is insufficient", size=18, bold=True,
               fill=_text_tone(CORAL), anchor="mm")

    inner = _panel(plate, (1139, 266, 1508, 780), "3  CHANGE THE PLAN", GREEN)
    map_rows = (("side + level", "stage"), ("drainage territory", "primary search"),
                ("ENE suspicion", "operation / RT plan"))
    for index, (evidence, action) in enumerate(map_rows):
        y = inner[1] + 84 + index * 112
        plate.draw.rounded_rectangle((inner[0] + 7, y - 35, inner[0] + 142, y + 35),
                                     radius=12, fill=hex_rgba(PALES[index], 100),
                                     outline=TONES[index], width=3)
        _note(plate, (inner[0] + 16, y - 28, inner[0] + 133, y + 28),
              evidence, size=15, tone=INK, bold=True)
        _arrow(plate, (inner[0] + 148, y), (inner[0] + 190, y), "",
               TONES[index], width=4, head=11)
        plate.draw.rounded_rectangle((inner[0] + 198, y - 35, inner[2] - 7, y + 35),
                                     radius=12, fill=hex_rgba(PAPER_LIGHT, 225),
                                     outline=TONES[index], width=3)
        _note(plate, (inner[0] + 207, y - 28, inner[2] - 16, y + 28),
              action, size=15, tone=_text_tone(TONES[index]), bold=True)
    plate.text(((inner[0] + inner[2]) / 2, inner[1] + 397),
               "name the level in every conclusion", size=16, bold=True,
               fill=_text_tone(GREEN), anchor="mm")


def _draw_deep_neck_spaces(plate: RadiologyPlate,
                           item: Mapping[str, object]) -> None:
    _tag(plate, (800, 227), "DISPLACEMENT REVEALS THE SPACE OF ORIGIN", PLUM, size=22)
    inner = _panel(plate, (92, 266, 865, 780), "AXIAL SPACE MAP", BLUE,
                   subtitle="schematic fascial relationships, not a patient scan")
    cx, cy = (inner[0] + inner[2]) / 2, inner[1] + 211
    # Neck outline and central aerodigestive tract.
    plate.draw.ellipse((cx - 225, cy - 155, cx + 225, cy + 155),
                       fill=hex_rgba(BLUE_LIGHT, 42), outline=BLUE, width=5)
    plate.draw.ellipse((cx - 48, cy - 59, cx + 48, cy + 59),
                       fill=PAPER_LIGHT, outline=INK_SOFT, width=4)
    plate.text((cx, cy), "airway", size=17, bold=True, fill=INK, anchor="mm")
    spaces = (((cx - 125, cy - 26), "PP", GOLD, "diamond"),
              ((cx + 135, cy - 26), "carotid", CORAL, "circle"),
              ((cx - 176, cy + 80), "masticator", PLUM, "square"),
              ((cx, cy + 111), "retropharyngeal", TEAL, "square"))
    for position, label, tone, shape in spaces:
        _landmark(plate, position, label, tone, shape=shape, size=14)
    plate.text((cx - 125, cy - 87), "parapharyngeal fat", size=16,
               bold=True, fill=_text_tone(GOLD), anchor="mm")
    # A schematic mass displaces PP fat; the labelled vector, not colour,
    # carries the localisation clue without claiming patient-specific anatomy.
    lesion = (cx - 213, cy + 48)
    plate.draw.ellipse((lesion[0] - 38, lesion[1] - 34,
                        lesion[0] + 38, lesion[1] + 34),
                       fill=hex_rgba(CORAL, 170), outline=CORAL, width=4)
    _arrow(plate, (cx - 176, cy + 42), (cx - 137, cy - 5),
           "fat displaced", GOLD, label_at=(cx - 220, cy - 12), width=5)
    plate.text((cx, inner[1] + 378), "direction of displaced fat narrows the origin",
               size=18, bold=True, fill=_text_tone(BLUE), anchor="mm")
    inner = _panel(plate, (887, 266, 1179, 780), "FASCIAL ROUTES", PLUM)
    routes = (("suprahyoid", "skull base", BLUE), ("infrahyoid", "mediastinum", CORAL),
              ("carotid space", "neurovascular", PLUM), ("mucosal space", "airway", TEAL))
    for index, (origin, destination, tone) in enumerate(routes):
        y = inner[1] + 61 + index * 88
        plate.text((inner[0] + 13, y - 11), origin, size=15, bold=True,
                   fill=INK, anchor="lm")
        _arrow(plate, (inner[0] + 24, y + 24), (inner[0] + 67, y + 24),
               "", tone, width=4, head=11)
        plate.text((inner[0] + 80, y + 24), destination, size=15, bold=True,
                   fill=_text_tone(tone), anchor="lm")
    plate.text(((inner[0] + inner[2]) / 2, inner[1] + 389),
               "routes predict spread", size=17, bold=True,
               fill=_text_tone(PLUM), anchor="mm")

    inner = _panel(plate, (1201, 266, 1508, 780), "URGENCY MAP", CORAL)
    threats = (("airway", "narrowing"), ("mediastinum", "descending spread"),
               ("perineural", "skull-base route"))
    for index, (site, effect) in enumerate(threats):
        y = inner[1] + 82 + index * 111
        _landmark(plate, (inner[0] + 42, y), "!", CORAL,
                  shape="diamond", size=17)
        plate.text((inner[0] + 82, y - 12), site, size=17, bold=True,
                   fill=INK, anchor="lm")
        plate.text((inner[0] + 82, y + 19), effect, size=15,
                   fill=INK_SOFT, anchor="lm")
    plate.text(((inner[0] + inner[2]) / 2, inner[1] + 389),
               "map threat before cause", size=16, bold=True,
               fill=_text_tone(CORAL), anchor="mm")


def _orbit_outline(plate: RadiologyPlate, center: Point, scale: float = 1.0,
                   *, tone: str = BLUE) -> None:
    x, y = center
    plate.draw.polygon(((x - 115 * scale, y - 75 * scale),
                        (x + 34 * scale, y - 108 * scale),
                        (x + 116 * scale, y), (x + 35 * scale, y + 108 * scale),
                        (x - 115 * scale, y + 75 * scale)),
                       fill=hex_rgba(BLUE_LIGHT, 65), outline=tone)
    plate.draw.line((x - 115 * scale, y - 75 * scale, x + 34 * scale, y - 108 * scale,
                     x + 116 * scale, y, x + 35 * scale, y + 108 * scale,
                     x - 115 * scale, y + 75 * scale, x - 115 * scale, y - 75 * scale),
                    fill=tone, width=max(3, int(5 * scale)), joint="curve")
    plate.draw.ellipse((x - 76 * scale, y - 60 * scale,
                        x + 44 * scale, y + 60 * scale),
                       fill=hex_rgba(PAPER_LIGHT, 230), outline=INK_SOFT,
                       width=max(2, int(4 * scale)))
    plate.draw.ellipse((x - 34 * scale, y - 34 * scale,
                        x + 34 * scale, y + 34 * scale),
                       fill=hex_rgba(TEAL_LIGHT, 90), outline=TEAL,
                       width=max(2, int(4 * scale)))
    plate.draw.line((x + 44 * scale, y, x + 118 * scale, y),
                    fill=GOLD, width=max(4, int(10 * scale)))


def _draw_orbit(plate: RadiologyPlate, item: Mapping[str, object]) -> None:
    boxes = ((92, 220, 555, 790), (568, 220, 1031, 790), (1044, 220, 1508, 790))
    inner = _panel(plate, boxes[0], "TRAUMA", BLUE,
                   subtitle="wall + globe + muscle + optic nerve")
    cx, cy = (inner[0] + inner[2]) / 2, inner[1] + 182
    _orbit_outline(plate, (cx, cy), .90)
    plate.draw.line((cx - 25, cy + 97, cx + 37, cy + 107), fill=CORAL, width=8)
    plate.draw.line((cx + 3, cy + 33, cx + 25, cy + 92), fill=PLUM, width=7)
    _arrow(plate, (inner[0] + 32, inner[1] + 67), (cx + 11, cy + 101),
           "wall defect", CORAL, label_at=(inner[0] + 92, inner[1] + 45), width=5)
    checks = ("globe contour", "muscle entrapment", "optic nerve / apex")
    for index, label in enumerate(checks):
        y = inner[1] + 345 + index * 45
        _check(plate, (inner[0] + 43, y), radius=16)
        plate.text((inner[0] + 73, y), label, size=17, bold=True,
                   fill=INK, anchor="lm")

    inner = _panel(plate, boxes[1], "INFLAMMATION / INFECTION", TEAL,
                   subtitle="which tissue, which compartment, which tempo?")
    cx, cy = (inner[0] + inner[2]) / 2, inner[1] + 181
    _orbit_outline(plate, (cx, cy), .90, tone=TEAL)
    # Muscle enlargement and sinus-to-orbit route are separately encoded.
    plate.draw.line((cx - 64, cy - 23, cx + 39, cy - 16), fill=CORAL, width=17)
    plate.draw.rounded_rectangle((cx - 105, cy + 99, cx - 14, cy + 150), radius=8,
                                 fill=hex_rgba(GOLD_LIGHT, 175), outline=GOLD, width=4)
    _arrow(plate, (cx - 57, cy + 96), (cx - 44, cy + 52),
           "sinus route", GOLD, label_at=(cx - 110, cy + 82), width=5)
    plate.text((cx, inner[1] + 347), "fat  |  muscle  |  sinus  |  apex",
               size=18, bold=True, fill=_text_tone(TEAL), anchor="mm")
    _note(plate, (inner[0] + 8, inner[1] + 374, inner[2] - 8, inner[3]),
          "Pattern and clinical tempo distinguish inflammatory spread; geometry alone does not name the cause.",
          size=18, tone=INK, bold=True)

    inner = _panel(plate, boxes[2], "MASS", PLUM,
                   subtitle="compartment + bone + enhancement")
    cx, cy = (inner[0] + inner[2]) / 2, inner[1] + 182
    _orbit_outline(plate, (cx, cy), .90, tone=PLUM)
    plate.draw.ellipse((cx + 19, cy - 77, cx + 86, cy - 12),
                       fill=hex_rgba(PLUM, 170), outline=PLUM, width=4)
    plate.draw.line((cx + 55, cy - 13, cx + 76, cy + 2), fill=PLUM, width=7)
    _measure(plate, (cx + 86, cy - 77), (cx + 86, cy - 12),
             "extent", PLUM, label_at=(cx + 131, cy - 45))
    questions = ("intraconal / extraconal?", "bone remodelled or destroyed?",
                 "optic nerve displaced or involved?")
    for index, label in enumerate(questions):
        y = inner[1] + 345 + index * 45
        plate.text((inner[0] + 26, y), str(index + 1) + "  " + label,
                   size=16, bold=True, fill=INK, anchor="lm")


def _draw_sinuses(plate: RadiologyPlate, item: Mapping[str, object]) -> None:
    _tag(plate, (800, 227), "DRAINAGE PATHWAY + HAZARD MAP + UNILATERAL RED FLAG", BLUE, size=20)
    inner = _panel(plate, (92, 266, 760, 780), "1  TRACE THE DRAINAGE UNIT", BLUE,
                   subtitle="coronal surgical-orientation schematic")
    cx, cy = 426, inner[1] + 198
    # Orbit, ethmoid, maxillary and frontal sinus geometry.
    for dx in (-126, 126):
        plate.draw.ellipse((cx + dx - 62, cy - 83, cx + dx + 62, cy + 5),
                           fill=hex_rgba(BLUE_LIGHT, 70), outline=BLUE, width=4)
    for dx in (-61, -22, 22, 61):
        plate.draw.rounded_rectangle((cx + dx - 17, cy - 72,
                                      cx + dx + 17, cy - 21), radius=6,
                                     fill=hex_rgba(TEAL_LIGHT, 110), outline=TEAL, width=3)
    for dx in (-119, 119):
        plate.draw.rounded_rectangle((cx + dx - 74, cy + 28,
                                      cx + dx + 74, cy + 142), radius=29,
                                     fill=hex_rgba(GOLD_LIGHT, 105), outline=GOLD, width=4)
    plate.draw.arc((cx - 91, cy - 185, cx + 91, cy - 62), 180, 360,
                   fill=PLUM, width=8)
    for side in (-1, 1):
        _arrow(plate, (cx + side * 118, cy + 28), (cx + side * 49, cy - 4),
               "ostium", TEAL, label_at=(cx + side * 115, cy + 7), width=4, head=11)
    # Separate nasal drainage channels, not a connection through the septum.
    for side in (-1, 1):
        plate.draw.line((cx + side * 49, cy - 4,
                         cx + side * 29, cy + 45,
                         cx + side * 29, cy + 114), fill=TEAL, width=5)
    plate.text((cx, cy + 176), "obstruction location predicts which sinus is retained",
               size=18, bold=True, fill=_text_tone(BLUE), anchor="mm")

    inner = _panel(plate, (782, 266, 1150, 780), "2  FLAG HAZARDS", CORAL)
    hazards = (("skull base", "superior", BLUE), ("orbit", "lateral", TEAL),
               ("optic nerve", "variant course", PLUM), ("carotid", "sphenoid relation", CORAL))
    cx, cy = (inner[0] + inner[2]) / 2, inner[1] + 208
    plate.draw.rounded_rectangle((cx - 58, cy - 69, cx + 58, cy + 69), radius=16,
                                 fill=hex_rgba(GOLD_LIGHT, 110), outline=GOLD, width=4)
    plate.text((cx, cy), "SINUS", size=18, bold=True,
               fill=_text_tone(GOLD), anchor="mm")
    positions = ((cx, cy - 137), (cx - 137, cy), (cx + 137, cy - 50), (cx + 137, cy + 66))
    for (head, detail, tone), position in zip(hazards, positions):
        _landmark(plate, position, "!", tone, shape="diamond", size=15)
        _arrow(plate, position, (cx, cy), "", tone, width=4, head=11)
        plate.text((position[0], position[1] + (42 if position[1] < cy else 41)),
                   head, size=15, bold=True, fill=_text_tone(tone), anchor="mm")
        if position[0] > cx:
            plate.text((position[0], position[1] + 61), detail, size=13,
                       fill=INK_SOFT, anchor="mm")
    plate.text((cx, inner[1] + 394), "variants alter the safe surgical corridor",
               size=16, bold=True, fill=_text_tone(CORAL), anchor="mm")

    inner = _panel(plate, (1172, 266, 1508, 780), "3  ESCALATE", PLUM)
    cx, cy = (inner[0] + inner[2]) / 2, inner[1] + 164
    plate.draw.rounded_rectangle((cx - 109, cy - 80, cx + 109, cy + 80), radius=28,
                                 fill=hex_rgba(PLUM_LIGHT, 90), outline=PLUM, width=5)
    plate.draw.ellipse((cx - 71, cy - 51, cx + 32, cy + 54),
                       fill=hex_rgba(CORAL, 170), outline=CORAL, width=4)
    for angle in (15, 92, 168, 241, 316):
        r = math.radians(angle)
        x0, y0 = cx + math.cos(r) * 47, cy + math.sin(r) * 47
        x1, y1 = cx + math.cos(r) * 88, cy + math.sin(r) * 77
        plate.draw.line((x0, y0, x1, y1), fill=CORAL, width=5)
    _tag(plate, (cx, inner[1] + 285), "UNILATERAL + DESTRUCTIVE", CORAL, size=16)
    plate.text((cx, inner[1] + 335), "question tumour / invasive process", size=16,
               bold=True, fill=INK, anchor="mm")
    _note(plate, (inner[0] + 8, inner[1] + 356, inner[2] - 8, inner[3]),
          "Destruction or mass-like asymmetry needs a pathway beyond routine inflammation.",
          size=16, tone=INK, bold=True)


def _draw_temporal_bone(plate: RadiologyPlate,
                        item: Mapping[str, object]) -> None:
    boxes = ((92, 220, 555, 790), (568, 220, 1031, 790), (1044, 220, 1508, 790))
    inner = _panel(plate, boxes[0], "MIDDLE EAR", BLUE,
                   subtitle="ossicles + scutum + diffusion")
    cx, cy = (inner[0] + inner[2]) / 2, inner[1] + 177
    plate.draw.rounded_rectangle((cx - 139, cy - 103, cx + 139, cy + 103), radius=26,
                                 fill=hex_rgba(BLUE_LIGHT, 55), outline=BLUE, width=5)
    # Malleus-incus-stapes chain.
    plate.draw.ellipse((cx - 72, cy - 24, cx - 31, cy + 17),
                       fill=GOLD_LIGHT, outline=GOLD, width=3)
    plate.draw.line((cx - 39, cy + 5, cx + 6, cy + 22), fill=GOLD, width=10)
    plate.draw.ellipse((cx - 1, cy + 3, cx + 45, cy + 45),
                       fill=GOLD_LIGHT, outline=GOLD, width=3)
    plate.draw.line((cx + 37, cy + 28, cx + 79, cy + 3), fill=GOLD, width=7)
    plate.draw.ellipse((cx + 70, cy - 7, cx + 95, cy + 14),
                       outline=GOLD, width=5)
    plate.draw.line((cx - 139, cy - 75, cx - 91, cy - 42), fill=PLUM, width=9)
    plate.text((cx - 117, cy - 96), "scutum", size=16, bold=True,
               fill=_text_tone(PLUM), anchor="mm")
    plate.draw.ellipse((cx - 109, cy + 18, cx - 54, cy + 73),
                       fill=hex_rgba(CORAL, 165), outline=CORAL, width=4)
    _arrow(plate, (inner[0] + 32, inner[1] + 55), (cx - 80, cy + 33),
           "soft tissue", CORAL, label_at=(inner[0] + 83, inner[1] + 37), width=5)
    plate.text((cx, inner[1] + 328), "erosion + non-EPI DWI support the pattern",
               size=16, bold=True, fill=_text_tone(BLUE), anchor="mm")
    _note(plate, (inner[0] + 8, inner[1] + 360, inner[2] - 8, inner[3]),
          "Tiny landmarks are read as an operative map, not merely as a density pattern.",
          size=18, tone=INK, bold=True)

    inner = _panel(plate, boxes[1], "OTIC CAPSULE", PLUM,
                   subtitle="cochlea + labyrinth + fracture course")
    cx, cy = (inner[0] + inner[2]) / 2, inner[1] + 178
    # Cochlear spiral.
    points = []
    for index in range(90):
        t = index / 89 * math.tau * 2.3
        radius = 77 * (1 - index / 110)
        points.append((cx - 48 + math.cos(t) * radius,
                       cy + math.sin(t) * radius))
    plate.draw.line(points, fill=PLUM, width=8, joint="curve")
    # Semicircular canals.
    for dx, dy, start in ((70, -43, 20), (72, 35, 165), (19, -70, 70)):
        plate.draw.arc((cx + dx - 54, cy + dy - 54,
                        cx + dx + 54, cy + dy + 54), start, start + 250,
                       fill=TEAL, width=8)
    plate.draw.line((cx - 137, cy - 107, cx + 123, cy + 112),
                    fill=CORAL, width=7)
    _tag(plate, (cx + 111, cy - 117), "FRACTURE COURSE", CORAL, size=16)
    plate.text((cx, inner[1] + 333), "otic-capsule involvement changes hearing risk",
               size=16, bold=True, fill=_text_tone(PLUM), anchor="mm")
    _note(plate, (inner[0] + 8, inner[1] + 367, inner[2] - 8, inner[3]),
          "Relate the line to labyrinth, facial canal and ossicular chain rather than naming it by direction alone.",
          size=17, tone=INK, bold=True)

    inner = _panel(plate, boxes[2], "IMPLANT ROUTE", GREEN,
                   subtitle="cochlea + nerve + surgical access")
    cx, cy = (inner[0] + inner[2]) / 2, inner[1] + 178
    points = []
    for index in range(95):
        t = index / 94 * math.tau * 2.25
        radius = 92 * (1 - index / 120)
        points.append((cx + math.cos(t) * radius,
                       cy + math.sin(t) * radius))
    plate.draw.line(points, fill=GREEN, width=12, joint="curve")
    electrode = points[12:83:8]
    plate.draw.line(electrode, fill=GOLD, width=6, joint="curve")
    for point in electrode:
        plate.dot(point, 5, fill=GOLD, outline=GOLD, width=1)
    plate.draw.line((cx + 92, cy + 26, cx + 157, cy + 79), fill=BLUE, width=9)
    plate.text((cx + 127, cy + 105), "cochlear nerve", size=16, bold=True,
               fill=_text_tone(BLUE), anchor="mm")
    questions = ("patent cochlear turn", "nerve present", "safe access corridor")
    for index, label in enumerate(questions):
        y = inner[1] + 342 + index * 45
        _check(plate, (inner[0] + 43, y), radius=16)
        plate.text((inner[0] + 74, y), label, size=17, bold=True,
                   fill=INK, anchor="lm")


def _draw_thyroid_tirads(plate: RadiologyPlate,
                         item: Mapping[str, object]) -> None:
    _tag(plate, (800, 227), "FEATURE POINTS SET SUSPICION; SIZE SETS THE ACTION", TEAL, size=21)
    inner = _panel(plate, (92, 266, 680, 780), "1  SCORE FIVE FEATURE GROUPS", BLUE)
    # The value sets are intentionally exact: a repeated 0/1/2 ladder would
    # be wrong for shape, margin, echogenicity, and echogenic foci.
    features = (("composition", "cystic / spongiform -> solid", BLUE, (0, 1, 2)),
                ("echogenicity", "anechoic -> very hypo", TEAL, (0, 1, 2, 3)),
                ("shape", "wide -> tall", CORAL, (0, 3)),
                ("margin", "smooth -> invasive", PLUM, (0, 2, 3)),
                ("echogenic foci", "foci may be additive", GOLD, (0, 1, 2, 3)))
    for index, (head, scale, tone, point_values) in enumerate(features):
        y = inner[1] + 47 + index * 73
        plate.text((inner[0] + 13, y), head, size=17, bold=True,
                   fill=INK, anchor="lm")
        plate.text((inner[0] + 201, y), scale, size=15,
                   fill=INK_SOFT, anchor="lm")
        last_x, step = inner[2] - 28, 34
        first_x = last_x - (len(point_values) - 1) * step
        for ordinal, point in enumerate(point_values):
            x = first_x + ordinal * step
            plate.draw.rounded_rectangle((x - 14, y - 14, x + 14, y + 14), radius=6,
                                         fill=hex_rgba(PALES[TONES.index(tone)],
                                                       70 + ordinal * 45),
                                         outline=tone, width=2)
            plate.text((x, y), str(point), size=13, bold=True,
                       fill=_text_tone(tone), anchor="mm")
    plate.text(((inner[0] + inner[2]) / 2, inner[1] + 400),
               "use the published point table; do not score by gestalt",
               size=17, bold=True, fill=_text_tone(BLUE), anchor="mm")

    inner = _panel(plate, (702, 266, 1064, 780), "2  ASSIGN TR CATEGORY", PLUM)
    bars = (("0 points", "TR1", 82, GREEN),
            ("2 points", "TR2", 108, BLUE),
            ("3 points", "TR3", 136, TEAL),
            ("4-6 points", "TR4", 166, GOLD),
            ("7+ points", "TR5", 198, CORAL))
    for index, (points, category, width, tone) in enumerate(bars):
        y = inner[1] + 47 + index * 69
        plate.draw.rounded_rectangle((inner[0] + 18, y - 19,
                                      inner[0] + 18 + width, y + 19), radius=9,
                                     fill=hex_rgba(PALES[TONES.index(tone)], 160),
                                     outline=tone, width=3)
        plate.text((inner[0] + 29, y), points, size=15, bold=True,
                   fill=_text_tone(tone), anchor="lm")
        plate.text((inner[2] - 17, y), category, size=17, bold=True,
                   fill=_text_tone(tone), anchor="rm")
    plate.draw.line((inner[0] + 25, inner[1] + 380,
                     inner[2] - 25, inner[1] + 380), fill=PLUM, width=4)
    plate.text(((inner[0] + inner[2]) / 2, inner[1] + 409),
               "suspicion != certainty", size=18, bold=True,
               fill=_text_tone(PLUM), anchor="mm")

    inner = _panel(plate, (1086, 266, 1508, 780), "3  CATEGORY + SIZE", GREEN)
    cx = (inner[0] + inner[2]) / 2
    # A ruler and two threshold gates deliberately avoid stale hard-coded
    # numbers; the current applicable table remains the source of precision.
    plate.draw.line((inner[0] + 35, inner[1] + 130,
                     inner[2] - 35, inner[1] + 130), fill=INK_SOFT, width=5)
    for index in range(9):
        x = inner[0] + 35 + index * (inner[2] - inner[0] - 70) / 8
        height = 20 if index % 2 == 0 else 11
        plate.draw.line((x, inner[1] + 130 - height, x, inner[1] + 130 + height),
                        fill=INK_SOFT, width=3)
    plate.draw.ellipse((cx - 62, inner[1] + 57, cx + 62, inner[1] + 181),
                       fill=hex_rgba(TEAL_LIGHT, 100), outline=TEAL, width=5)
    _measure(plate, (cx - 62, inner[1] + 192), (cx + 62, inner[1] + 192),
             "measured size", TEAL, label_at=(cx, inner[1] + 30))
    gates = (("below category threshold", "no biopsy; follow current table", BLUE),
             ("surveillance threshold met", "follow-up", GOLD),
             ("aspiration threshold met", "FNA if appropriate", CORAL))
    for index, (condition, action, tone) in enumerate(gates):
        y = inner[1] + 250 + index * 62
        plate.draw.rounded_rectangle((inner[0] + 10, y - 25, inner[2] - 10, y + 25),
                                     radius=10, fill=hex_rgba(PALES[TONES.index(tone)], 90),
                                     outline=tone, width=3)
        plate.text(((inner[0] + inner[2]) / 2, y - 9), condition,
                   size=15, bold=True, fill=INK, anchor="mm")
        plate.text(((inner[0] + inner[2]) / 2, y + 12), action,
                   size=14, bold=True, fill=_text_tone(tone), anchor="mm")


RENDERERS: Dict[str, Renderer] = {
    "rad.5.aorta": _draw_aorta,
    "rad.5.cardiac-mri": _draw_cardiac_mri,
    "rad.5.cardiac-masses-devices": _draw_cardiac_masses_devices,
    "rad.5.congenital-ct": _draw_congenital_ct,
    "rad.5.coronary-ct": _draw_coronary_ct,
    "rad.5.peripheral-vascular": _draw_peripheral_vascular,
    "rad.5.tavi-ct": _draw_tavi_ct,
    "rad.4.stroke": _draw_stroke,
    "rad.5.brain-tumour": _draw_brain_tumour,
    "rad.5.brain-anatomy": _draw_brain_anatomy,
    "rad.5.cns-infection": _draw_cns_infection,
    "rad.5.venous-csf": _draw_venous_csf,
    "rad.5.dementia": _draw_dementia,
    "rad.5.epilepsy-mri": _draw_epilepsy_mri,
    "rad.4.head-trauma": _draw_head_trauma,
    "rad.5.intracranial-haemorrhage": _draw_intracranial_haemorrhage,
    "rad.5.ms-white-matter": _draw_ms_white_matter,
    "rad.4.spine-imaging": _draw_spine_imaging,
    "rad.5.neck-nodes": _draw_neck_nodes,
    "rad.5.deep-neck-spaces": _draw_deep_neck_spaces,
    "rad.5.orbit": _draw_orbit,
    "rad.5.sinuses": _draw_sinuses,
    "rad.5.temporal-bone": _draw_temporal_bone,
    "rad.5.thyroid-tirads": _draw_thyroid_tirads,
}


EXPECTED_IDS = {
    "rad.5.aorta", "rad.5.cardiac-mri", "rad.5.cardiac-masses-devices",
    "rad.5.congenital-ct", "rad.5.coronary-ct", "rad.5.peripheral-vascular",
    "rad.5.tavi-ct", "rad.4.stroke", "rad.5.brain-tumour",
    "rad.5.brain-anatomy", "rad.5.cns-infection", "rad.5.venous-csf",
    "rad.5.dementia", "rad.5.epilepsy-mri", "rad.4.head-trauma",
    "rad.5.intracranial-haemorrhage", "rad.5.ms-white-matter",
    "rad.4.spine-imaging", "rad.5.neck-nodes", "rad.5.deep-neck-spaces",
    "rad.5.orbit", "rad.5.sinuses", "rad.5.temporal-bone",
    "rad.5.thyroid-tirads",
}

if set(RENDERERS) != EXPECTED_IDS:
    raise ValueError("Cardiovascular/neuro renderer inventory drift")
if len({id(renderer) for renderer in RENDERERS.values()}) != len(RENDERERS):
    raise ValueError("Each cardiovascular/neuro lesson needs a unique renderer")


__all__ = ["EXPECTED_IDS", "RENDERERS"]
