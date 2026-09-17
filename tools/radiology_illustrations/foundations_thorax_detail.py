"""Lesson-specific radiology plates for foundations and thoracic imaging.

These scenes are deliberately diagrams, not synthetic patient scans.  They
make acquisition choices, observable signs, inference limits and the next
action spatially explicit.  Short labels remain useful in the 800 px export;
the curriculum's long descriptions carry the full clinical wording.

The module is intentionally registration-free.  ``RENDERERS`` is consumed by
the cohort aggregator after its exact lesson-id set has been checked.
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
    RadiologyPlate,
    _text_tone,
    hex_rgba,
)


Point = Tuple[float, float]
Box = Tuple[float, float, float, float]
Renderer = Callable[[RadiologyPlate, Mapping[str, object]], None]

TONES = (BLUE, TEAL, CORAL, PLUM)
PALES = (BLUE_LIGHT, TEAL_LIGHT, CORAL_LIGHT, PLUM_LIGHT)


def _panel(plate: RadiologyPlate, box: Box, title: str, tone: str = BLUE,
           *, subtitle: str = "") -> Box:
    """Draw one high-contrast evidence panel and return its working area."""
    plate.card(box, fill=hex_rgba(PAPER_LIGHT, 224), outline=tone, width=4, radius=24)
    x0, y0, x1, y1 = box
    plate.text(((x0 + x1) / 2, y0 + 36), title, size=27, bold=True,
               fill=_text_tone(tone), anchor="mm")
    plate.draw.line((x0 + 24, y0 + 72, x1 - 24, y0 + 72),
                    fill=hex_rgba(tone, 125), width=3)
    if subtitle:
        plate.text(((x0 + x1) / 2, y0 + 98), subtitle, size=22,
                   fill=INK_SOFT, anchor="mm")
        return x0 + 24, y0 + 126, x1 - 24, y1 - 24
    return x0 + 24, y0 + 92, x1 - 24, y1 - 24


def _tag(plate: RadiologyPlate, center: Point, value: str, tone: str = BLUE,
         *, size: int = 24, light: bool = False) -> None:
    plate.label(center, value, size=size, fill=(PALES[TONES.index(tone)]
                                                if light and tone in TONES
                                                else tone),
                text_fill=(INK if light else PAPER_LIGHT))


def _note(plate: RadiologyPlate, box: Box, value: str, *, size: int = 24,
          tone: str = INK_SOFT, bold: bool = False) -> None:
    plate.wrapped_text(tuple(int(v) for v in box), value, size=size,
                       bold=bold, fill=tone, line_gap=7)


def _bottom_note(plate: RadiologyPlate, inner: Box, value: str, *,
                 height: int = 88, size: int = 23, bold: bool = True) -> None:
    """Keep an inference line inside the lower edge of a returned panel box."""
    x0, _y0, x1, y1 = inner
    _note(plate, (x0 + 8, y1 - height, x1 - 8, y1 - 4), value,
          size=size, tone=INK, bold=bold)


def _arrow(plate: RadiologyPlate, start: Point, end: Point, label: str = "",
           tone: str = GOLD, *, label_at: Point | None = None,
           width: int = 7) -> None:
    plate.arrow(start, end, fill=tone, width=width, head=20)
    if label:
        center = label_at or ((start[0] + end[0]) / 2,
                              (start[1] + end[1]) / 2 - 22)
        _tag(plate, center, label, tone, size=22)


def _check(plate: RadiologyPlate, center: Point, tone: str = GREEN,
           *, scale: float = 1.0) -> None:
    x, y = center
    plate.draw.ellipse((x - 24 * scale, y - 24 * scale,
                        x + 24 * scale, y + 24 * scale),
                       fill=hex_rgba(GREEN_LIGHT, 190), outline=tone,
                       width=max(3, int(4 * scale)))
    plate.draw.line((x - 12 * scale, y,
                     x - 2 * scale, y + 11 * scale,
                     x + 15 * scale, y - 12 * scale),
                    fill=_text_tone(tone), width=max(3, int(5 * scale)),
                    joint="curve")


def _cross(plate: RadiologyPlate, center: Point, tone: str = CORAL,
           *, scale: float = 1.0) -> None:
    x, y = center
    reach = 17 * scale
    plate.draw.line((x - reach, y - reach, x + reach, y + reach),
                    fill=tone, width=max(3, int(6 * scale)))
    plate.draw.line((x - reach, y + reach, x + reach, y - reach),
                    fill=tone, width=max(3, int(6 * scale)))


def _axis(plate: RadiologyPlate, box: Box, x_label: str, y_label: str) -> None:
    x0, y0, x1, y1 = box
    plate.arrow((x0, y1), (x1, y1), fill=INK_SOFT, width=4, head=13)
    plate.arrow((x0, y1), (x0, y0), fill=INK_SOFT, width=4, head=13)
    plate.text((x1, y1 + 20), x_label, size=22, bold=True,
               fill=INK_SOFT, anchor="ra")
    plate.text((x0 + 10, y0), y_label, size=22, bold=True,
               fill=INK_SOFT, anchor="la")


def _lung_pair(plate: RadiologyPlate, center: Point, scale: float = 1.0,
               *, fill: str = BLUE_LIGHT, outline: str = BLUE) -> None:
    x, y = center
    plate.draw.line((x, y - 105 * scale, x, y - 58 * scale),
                    fill=INK_SOFT, width=max(4, int(8 * scale)))
    plate.draw.line((x, y - 58 * scale, x - 34 * scale, y - 23 * scale),
                    fill=INK_SOFT, width=max(3, int(6 * scale)))
    plate.draw.line((x, y - 58 * scale, x + 34 * scale, y - 23 * scale),
                    fill=INK_SOFT, width=max(3, int(6 * scale)))
    plate.draw.ellipse((x - 101 * scale, y - 56 * scale,
                        x - 8 * scale, y + 111 * scale),
                       fill=hex_rgba(fill, 96), outline=outline,
                       width=max(3, int(4 * scale)))
    plate.draw.ellipse((x + 8 * scale, y - 56 * scale,
                        x + 101 * scale, y + 111 * scale),
                       fill=hex_rgba(fill, 96), outline=outline,
                       width=max(3, int(4 * scale)))


def _vessel_branch(plate: RadiologyPlate, start: Point, tone: str = CORAL,
                   *, scale: float = 1.0, width: int = 18) -> Sequence[Point]:
    x, y = start
    trunk = ((x, y + 115 * scale), (x, y + 8 * scale),
             (x - 76 * scale, y - 70 * scale), (x - 125 * scale, y - 112 * scale))
    right = ((x, y + 8 * scale), (x + 76 * scale, y - 70 * scale),
             (x + 125 * scale, y - 112 * scale))
    plate.draw.line(trunk, fill=hex_rgba(tone, 220),
                    width=max(6, int(width * scale)), joint="curve")
    plate.draw.line(right, fill=hex_rgba(tone, 220),
                    width=max(6, int(width * scale)), joint="curve")
    return trunk


def _signal_map(plate: RadiologyPlate, center: Point, *, outer: str,
                fluid: str, fat: str, lesion: str | None = None) -> None:
    x, y = center
    plate.draw.ellipse((x - 105, y - 86, x + 105, y + 86),
                       fill=outer, outline=INK_SOFT, width=4)
    for dx in (-61, 61):
        plate.draw.ellipse((x + dx - 22, y - 31, x + dx + 22, y + 13),
                           fill=fat, outline=GRID, width=2)
    plate.draw.ellipse((x - 31, y - 18, x + 31, y + 27),
                       fill=fluid, outline=GRID, width=2)
    if lesion:
        plate.draw.ellipse((x + 27, y + 17, x + 58, y + 48),
                           fill=lesion, outline=INK, width=3)


def _draw_contrast(plate: RadiologyPlate, item: Mapping[str, object]) -> None:
    left = _panel(plate, (92, 220, 470, 785), "1  CLINICAL QUESTION", BLUE)
    middle = _panel(plate, (515, 220, 1085, 785), "2  MATCH TISSUE + PHASE", TEAL)
    right = _panel(plate, (1130, 220, 1508, 785), "3  SAFETY GATE", CORAL,
                   subtitle="agent-specific")

    x0, y0, x1, y1 = left
    plate.draw.ellipse((x0 + 66, y0 + 46, x1 - 66, y0 + 268),
                       fill=hex_rgba(BLUE_LIGHT, 105), outline=BLUE, width=5)
    plate.draw.ellipse((x0 + 123, y0 + 106, x1 - 123, y0 + 212),
                       fill=PAPER_LIGHT, outline=BLUE, width=4)
    plate.text(((x0 + x1) / 2, y0 + 160), "?", size=62, bold=True,
               fill=_text_tone(BLUE), anchor="mm")
    _bottom_note(plate, left,
          "What tissue property must become visible?\nWill enhancement change the answer?",
          height=128, size=25)

    x0, y0, x1, y1 = middle
    graph = (x0 + 32, y0 + 42, x1 - 28, y0 + 286)
    _axis(plate, graph, "time", "enhancement")
    gx0, gy0, gx1, gy1 = graph
    curve = []
    for index in range(101):
        t = index / 100
        value = (1 - math.exp(-9 * max(0, t - .09))) * math.exp(-2.1 * max(0, t - .25))
        curve.append((gx0 + t * (gx1 - gx0), gy1 - 23 - value * 174))
    plate.polyline(curve, fill=TEAL, width=8)
    phases = ((.05, "PRE", BLUE), (.29, "ARTERIAL", CORAL), (.62, "VENOUS", PLUM))
    for fraction, label, tone in phases:
        x = gx0 + fraction * (gx1 - gx0)
        plate.draw.line((x, gy0 + 14, x, gy1), fill=hex_rgba(tone, 150), width=4)
        _tag(plate, (x, gy1 + 42), label, tone, size=21)
    _bottom_note(plate, middle,
          "The same lesion can answer a different question in a different phase.",
          height=94, size=24)

    x0, y0, x1, y1 = right
    gates = (("prior reaction", "history", BLUE),
             ("renal / organ", "patient context", TEAL),
             ("agent + route", "protocol", CORAL))
    for index, (label, small, tone) in enumerate(gates):
        top = y0 + 34 + index * 105
        plate.draw.rounded_rectangle((x0 + 12, top, x1 - 12, top + 79),
                                     radius=18, fill=hex_rgba(PALES[index], 115),
                                     outline=tone, width=3)
        _check(plate, (x0 + 49, top + 40), tone=GREEN, scale=.75)
        plate.text((x0 + 87, top + 29), label, size=24, bold=True,
                   fill=_text_tone(tone), anchor="lm")
        plate.text((x0 + 87, top + 57), small, size=21,
                   fill=INK_SOFT, anchor="lm")
    _tag(plate, ((x0 + x1) / 2, y1 - 39), "benefit > avoidable risk", GREEN, size=22)


def _draw_radiation_safety(plate: RadiologyPlate, item: Mapping[str, object]) -> None:
    question = (263, 470)
    diamond = ((263, 276), (434, 470), (263, 664), (92, 470))
    plate.draw.polygon(diamond, fill=hex_rgba(BLUE_LIGHT, 145), outline=BLUE)
    plate.text((263, 405), "CLINICAL", size=27, bold=True,
               fill=_text_tone(BLUE), anchor="mm")
    plate.text((263, 448), "QUESTION", size=27, bold=True,
               fill=_text_tone(BLUE), anchor="mm")
    plate.text((263, 519), "changes care?", size=24, bold=True,
               fill=INK, anchor="mm")

    _arrow(plate, (434, 420), (610, 327), "US / MRI apt", TEAL,
           label_at=(526, 336), width=6)
    _tag(plate, (740, 305), "NO IONISING EXPOSURE", TEAL, size=23)
    _arrow(plate, (434, 514), (590, 514), "X-RAY / CT NEEDED", CORAL,
           label_at=(520, 482), width=6)

    plate.card((590, 390, 1065, 706), fill=hex_rgba(CORAL_LIGHT, 72),
               outline=CORAL, width=4, radius=24)
    plate.text((827, 425), "OPTIMISE THE ANSWER", size=27, bold=True,
               fill=_text_tone(CORAL), anchor="mm")
    # Broad field is dashed; the useful collimated field is solid and smaller.
    for y in (482, 648):
        for x in range(654, 998, 28):
            plate.draw.line((x, y, min(x + 16, 998), y), fill=GRID, width=4)
    for x in (654, 998):
        for y in range(482, 649, 25):
            plate.draw.line((x, y, x, min(y + 14, 648)), fill=GRID, width=4)
    plate.draw.ellipse((747, 475, 907, 659), fill=hex_rgba(GOLD_LIGHT, 80),
                       outline=GOLD, width=3)
    plate.draw.rectangle((720, 510, 934, 620), outline=CORAL, width=7)
    for corner in ((720, 510, 748, 510), (906, 510, 934, 510),
                   (720, 620, 748, 620), (906, 620, 934, 620)):
        plate.draw.line(corner, fill=CORAL, width=9)
    plate.text((827, 678), "range • protocol • patient size", size=23,
               bold=True, fill=INK_SOFT, anchor="mm")

    _arrow(plate, (1065, 548), (1150, 548), "record", GOLD,
           label_at=(1108, 514), width=6)
    plate.card((1150, 265, 1505, 742), fill=hex_rgba(GREEN_LIGHT, 88),
               outline=GREEN, width=4, radius=24)
    plate.text((1327, 306), "VERIFY + REVIEW", size=27, bold=True,
               fill=_text_tone(GREEN), anchor="mm")
    # Review prompts, not arbitrary bars that resemble measured patient dose.
    for index, (label, detail) in enumerate((
            ("delivered field", "matches the task?"),
            ("exposure metric", "record and compare"),
            ("child / repeats", "extra scrutiny"))):
        y = 385 + index * 105
        plate.text((1190, y), label, size=23, bold=True, fill=INK, anchor="lm")
        plate.text((1190, y + 43), detail, size=21, fill=INK_SOFT, anchor="lm")
    _check(plate, (1327, 693), scale=1.05)


def _draw_mri_sequences(plate: RadiologyPlate, item: Mapping[str, object]) -> None:
    plate.text((800, 205), "SCHEMATIC SIGNAL MAPS — IDENTIFY THE SEQUENCE FIRST",
               size=25, bold=True, fill=INK_SOFT, anchor="mm")
    boxes = ((92, 244, 500, 770), (596, 244, 1004, 770), (1100, 244, 1508, 770))

    inner = _panel(plate, boxes[0], "T1-WEIGHTED", BLUE, subtitle="relative brightness")
    _signal_map(plate, ((inner[0] + inner[2]) / 2, inner[1] + 130),
                outer=hex_rgba(PLUM_LIGHT, 110), fluid=INK_SOFT,
                fat=GOLD_LIGHT)
    _tag(plate, (207, 571), "FAT BRIGHT", GOLD, size=23)
    _tag(plate, (383, 571), "FLUID DARK", BLUE, size=23)
    _note(plate, (inner[0] + 15, 620, inner[2] - 15, 738),
          "Typical T1 without fat suppression: fat is bright, simple fluid dark.", size=24,
          tone=INK, bold=True)

    inner = _panel(plate, boxes[1], "T2 / FLUID-SENSITIVE", TEAL,
                   subtitle="water-rich tissue stands out")
    _signal_map(plate, ((inner[0] + inner[2]) / 2, inner[1] + 130),
                outer=hex_rgba(PLUM_LIGHT, 92), fluid=BLUE_LIGHT,
                fat=hex_rgba(GOLD_LIGHT, 80), lesion=TEAL_LIGHT)
    plate.draw.arc((730, 409, 870, 549), 210, 510, fill=TEAL, width=7)
    _tag(plate, (800, 571), "FLUID BRIGHT", TEAL, size=23)
    _note(plate, (inner[0] + 15, 620, inner[2] - 15, 738),
          "Simple fluid is usually bright; fluid suppression changes this pattern.", size=24,
          tone=INK, bold=True)

    inner = _panel(plate, boxes[2], "DIFFUSION PAIR", CORAL,
                   subtitle="both maps must agree")
    for index, (label, background, spot) in enumerate((
            ("DWI HIGH", INK_SOFT, PAPER_LIGHT),
            ("ADC LOW", PAPER_LIGHT, INK_SOFT))):
        cx = 1213 + index * 182
        plate.draw.rounded_rectangle((cx - 76, 377, cx + 76, 529), radius=20,
                                     fill=background, outline=CORAL, width=4)
        plate.draw.ellipse((cx + 9, 421, cx + 52, 464), fill=spot,
                           outline=CORAL, width=4)
        plate.text((cx, 558), label, size=23, bold=True,
                   fill=_text_tone(CORAL), anchor="mm")
    plate.draw.line((1288, 455, 1318, 455), fill=CORAL, width=7)
    plate.text((1303, 420), "+", size=30, bold=True,
               fill=_text_tone(CORAL), anchor="mm")
    _tag(plate, (1304, 623), "RESTRICTION", CORAL, size=23)
    _note(plate, (inner[0] + 14, 654, inner[2] - 14, 738),
          "High DWI alone can be T2 shine-through.", size=23,
          tone=INK, bold=True)


def _draw_modalities(plate: RadiologyPlate, item: Mapping[str, object]) -> None:
    plate.text((800, 211), "QUESTION  →  MEASURABLE PHYSICAL PROPERTY  →  OUTPUT",
               size=26, bold=True, fill=INK_SOFT, anchor="mm")
    boxes = ((78, 252, 432, 776), (452, 252, 806, 776),
             (826, 252, 1180, 776), (1200, 252, 1522, 776))
    titles = ("X-RAY / CT", "ULTRASOUND", "MRI", "NUCLEAR")
    subtitles = ("attenuation", "echo + motion", "magnetic signal", "tracer distribution")
    for index, box in enumerate(boxes):
        tone = TONES[index]
        inner = _panel(plate, box, titles[index], tone, subtitle=subtitles[index])
        cx = (inner[0] + inner[2]) / 2
        if index == 0:
            plate.draw.rectangle((cx - 124, 404, cx - 103, 566), fill=BLUE)
            for dy, width in ((-42, 7), (0, 5), (42, 3)):
                plate.arrow((cx - 96, 485 + dy), (cx + 101, 485 + dy),
                            fill=BLUE, width=width, head=13)
            plate.draw.ellipse((cx - 36, 399, cx + 36, 571),
                               fill=hex_rgba(GOLD_LIGHT, 150), outline=GOLD, width=4)
            plate.draw.rectangle((cx + 104, 399, cx + 124, 571), fill=INK_SOFT)
            labels = "projection / slices\ngas • bone • blood"
        elif index == 1:
            plate.draw.polygon(((cx - 119, 420), (cx - 66, 438),
                                (cx - 66, 489), (cx - 119, 507)), fill=TEAL)
            for radius in (35, 66, 96):
                plate.draw.arc((cx - 67 - radius, 464 - radius,
                                cx - 67 + radius, 464 + radius),
                               308, 412, fill=TEAL, width=4)
            plate.draw.line((cx + 50, 397, cx + 50, 571), fill=INK_SOFT, width=8)
            plate.arrow((cx + 105, 530), (cx + 105, 416), fill=CORAL, width=7, head=18)
            labels = "interfaces / flow\nreal-time • portable"
        elif index == 2:
            plate.draw.arc((cx - 118, 391, cx + 118, 579), 75, 285,
                           fill=PLUM, width=14)
            for dy in (-48, 0, 48):
                plate.arrow((cx - 55, 485 + dy), (cx + 62, 485 + dy),
                            fill=PLUM, width=5, head=15)
            labels = "soft-tissue signal\nno ionising radiation"
        else:
            plate.draw.ellipse((cx - 45, 405, cx + 45, 565),
                               fill=hex_rgba(GOLD_LIGHT, 80), outline=GOLD, width=4)
            plate.dot((cx, 476), 17, fill=CORAL, outline=INK, width=3)
            for angle in (-55, -20, 20, 55):
                radians = math.radians(angle)
                plate.arrow((cx, 476),
                            (cx + 125 * math.cos(radians), 476 + 125 * math.sin(radians)),
                            fill=CORAL, width=4, head=12)
            plate.draw.rectangle((cx - 143, 393, cx - 128, 577), fill=INK_SOFT)
            plate.draw.rectangle((cx + 128, 393, cx + 143, 577), fill=INK_SOFT)
            labels = "physiology map\nuptake needs context"
        _note(plate, (inner[0] + 4, 612, inner[2] - 4, 744), labels,
              size=24, tone=INK, bold=True)


def _draw_ultrasound_physics(plate: RadiologyPlate,
                             item: Mapping[str, object]) -> None:
    boxes = ((82, 230, 512, 790), (585, 230, 1015, 790), (1088, 230, 1518, 790))
    inner = _panel(plate, boxes[0], "FREQUENCY TRADE-OFF", BLUE)
    graph = (inner[0] + 30, inner[1] + 25, inner[2] - 22, inner[1] + 288)
    _axis(plate, graph, "frequency", "relative")
    gx0, gy0, gx1, gy1 = graph
    detail = []
    penetration = []
    for index in range(61):
        t = index / 60
        detail.append((gx0 + t * (gx1 - gx0), gy1 - 25 - 185 * t))
        penetration.append((gx0 + t * (gx1 - gx0), gy1 - 25 - 185 * (1 - t)))
    plate.polyline(detail, fill=TEAL, width=8)
    plate.polyline(penetration, fill=CORAL, width=8)
    _tag(plate, (inner[0] + 112, inner[1] + 342), "PENETRATION", CORAL, size=21)
    _tag(plate, (inner[2] - 92, inner[1] + 112), "DETAIL", TEAL, size=21)
    _bottom_note(plate, inner,
          "Higher frequency resolves smaller detail but reaches less depth.",
          height=72, size=22)

    inner = _panel(plate, boxes[1], "DOPPLER GEOMETRY", TEAL)
    # Vessel and velocity vector.
    plate.draw.rounded_rectangle((inner[0] + 25, inner[1] + 177,
                                  inner[2] - 25, inner[1] + 257), radius=35,
                                 fill=hex_rgba(CORAL_LIGHT, 140), outline=CORAL, width=4)
    sample = (inner[2] - 91, inner[1] + 217)
    probe = (inner[0] + 48, inner[1] + 19)
    plate.arrow(sample, (inner[0] + 77, sample[1]),
                fill=CORAL, width=8, head=20)
    plate.draw.line((*probe, *sample), fill=TEAL, width=8)
    plate.draw.polygon(((inner[0] + 20, inner[1] + 5),
                        (inner[0] + 92, inner[1] + 28),
                        (inner[0] + 69, inner[1] + 75)), fill=TEAL)
    # Angle shares the sampled point with the leftward flow and probe line.
    beam_angle = math.degrees(math.atan2(probe[1] - sample[1],
                                        probe[0] - sample[0])) % 360
    plate.draw.arc((sample[0] - 65, sample[1] - 65,
                    sample[0] + 65, sample[1] + 65), 180, beam_angle,
                   fill=GOLD, width=6)
    plate.text((inner[2] - 132, inner[1] + 151), "angle", size=23,
               bold=True, fill=_text_tone(GOLD), anchor="mm")
    _tag(plate, ((inner[0] + inner[2]) / 2, inner[1] + 309),
         "shift ~ velocity × cos(angle)", TEAL, size=22)
    _bottom_note(plate, inner,
          "Angle, velocity scale and direction shape the displayed flow signal.",
          height=96, size=22)

    inner = _panel(plate, boxes[2], "ARTEFACT AS EVIDENCE", CORAL)
    # Two ray paths: stone/air shadow, then fluid enhancement.
    centers = (inner[0] + 102, inner[2] - 102)
    for cx in centers:
        plate.draw.polygon(((cx - 44, inner[1] + 20), (cx + 44, inner[1] + 20),
                            (cx + 76, inner[1] + 312), (cx - 76, inner[1] + 312)),
                           fill=hex_rgba(BLUE_LIGHT, 55), outline=BLUE)
    plate.draw.ellipse((centers[0] - 45, inner[1] + 126,
                        centers[0] + 45, inner[1] + 185), fill=GOLD,
                       outline=INK_SOFT, width=4)
    plate.draw.polygon(((centers[0] - 49, inner[1] + 187),
                        (centers[0] + 49, inner[1] + 187),
                        (centers[0] + 73, inner[1] + 313),
                        (centers[0] - 73, inner[1] + 313)), fill=INK_SOFT)
    plate.text((centers[0], inner[1] + 349), "SHADOW", size=23, bold=True,
               fill=INK, anchor="mm")
    plate.draw.ellipse((centers[1] - 48, inner[1] + 120,
                        centers[1] + 48, inner[1] + 193), fill=BLUE_LIGHT,
                       outline=BLUE, width=4)
    plate.draw.polygon(((centers[1] - 50, inner[1] + 195),
                        (centers[1] + 50, inner[1] + 195),
                        (centers[1] + 76, inner[1] + 313),
                        (centers[1] - 76, inner[1] + 313)),
                       fill=hex_rgba(GOLD_LIGHT, 150))
    plate.text((centers[1], inner[1] + 349), "ENHANCEMENT", size=23, bold=True,
               fill=_text_tone(CORAL), anchor="mm")
    _bottom_note(plate, inner,
          "Interfaces and transmission can reveal hidden material.",
          height=72, size=22)


def _draw_biopsy_safety(plate: RadiologyPlate,
                        item: Mapping[str, object]) -> None:
    boxes = ((72, 226, 522, 790), (575, 226, 1025, 790), (1078, 226, 1528, 790))
    inner = _panel(plate, boxes[0], "PLAN THE TRACT", BLUE,
                   subtitle="target + no-go structures")
    cx, cy = (inner[0] + inner[2]) / 2, inner[1] + 192
    plate.draw.ellipse((cx - 145, cy - 125, cx + 145, cy + 125),
                       fill=hex_rgba(GOLD_LIGHT, 55), outline=INK_SOFT, width=4)
    plate.draw.ellipse((cx + 46, cy - 25, cx + 104, cy + 33),
                       fill=hex_rgba(TEAL_LIGHT, 170), outline=TEAL, width=5)
    plate.text((cx + 75, cy + 70), "TARGET", size=22, bold=True,
               fill=_text_tone(TEAL), anchor="mm")
    # Vulnerable vessel and bowel are patterned differently.
    plate.draw.rounded_rectangle((cx - 42, cy - 105, cx - 5, cy + 105),
                                 radius=18, fill=hex_rgba(CORAL_LIGHT, 180),
                                 outline=CORAL, width=4)
    plate.draw.ellipse((cx - 20, cy + 51, cx + 37, cy + 108),
                       fill=PAPER_LIGHT, outline=PLUM, width=5)
    for step in range(0, 115, 18):
        plate.draw.line((cx - 39, cy - 101 + step, cx - 8, cy - 84 + step),
                        fill=CORAL, width=3)
    plate.draw.line((cx - 171, cy - 66, cx + 74, cy + 2),
                    fill=hex_rgba(CORAL, 170), width=5)
    _cross(plate, (cx - 12, cy - 22), scale=1.0)
    # Approach from the target's clear side, never through the vessel/bowel.
    plate.arrow((cx + 171, cy - 66), (cx + 97, cy - 12),
                fill=GREEN, width=8, head=21)
    _tag(plate, (cx, inner[1] + 326), "SAFE PATH", GREEN, size=22)
    _bottom_note(plate, inner,
          "Plan haemostasis and future surgical planes before puncture.",
          height=60, size=20)

    inner = _panel(plate, boxes[1], "GUIDE TIP + WHOLE PATH", TEAL)
    cx = (inner[0] + inner[2]) / 2
    plate.draw.polygon(((cx - 150, inner[1] + 38), (cx + 150, inner[1] + 38),
                        (cx + 98, inner[1] + 332), (cx - 98, inner[1] + 332)),
                       fill=hex_rgba(BLUE_LIGHT, 80), outline=BLUE, width=4)
    for radius in (65, 118, 170):
        plate.draw.arc((cx - radius, inner[1] - 5,
                        cx + radius, inner[1] - 5 + radius * 2),
                       32, 148, fill=hex_rgba(BLUE, 130), width=3)
    target = (cx + 55, inner[1] + 257)
    plate.draw.ellipse((target[0] - 42, target[1] - 34,
                        target[0] + 42, target[1] + 34),
                       fill=hex_rgba(TEAL_LIGHT, 185), outline=TEAL, width=5)
    plate.draw.line((cx - 184, inner[1] + 74, target[0], target[1]),
                    fill=CORAL, width=7)
    plate.dot(target, 9, fill=CORAL, outline=INK, width=3)
    _tag(plate, (cx, inner[1] + 326), "TIP IN TARGET", TEAL, size=22)
    _bottom_note(plate, inner,
          "Imaging must show the tip and the entire safe path.",
          height=60, size=20)

    inner = _panel(plate, boxes[2], "MONITOR + RESCUE", CORAL)
    # Waveform and complication branch.
    points = []
    for index in range(90):
        x = inner[0] + 20 + index * (inner[2] - inner[0] - 40) / 89
        base = inner[1] + 122
        y = base
        if index % 23 in (11, 12):
            y -= 66 if index % 23 == 11 else 24
        points.append((x, y))
    plate.polyline(points, fill=GREEN, width=6)
    plate.draw.line((inner[0] + 20, inner[1] + 162,
                     inner[2] - 20, inner[1] + 162), fill=GRID, width=3)
    plate.dot(((inner[0] + inner[2]) / 2, inner[1] + 239), 29,
              fill=CORAL_LIGHT, outline=CORAL, width=5)
    plate.text(((inner[0] + inner[2]) / 2, inner[1] + 239), "!", size=37,
               bold=True, fill=_text_tone(CORAL), anchor="mm")
    _tag(plate, ((inner[0] + inner[2]) / 2, inner[1] + 305),
         "PLANNED RESPONSE", CORAL, size=22)
    _bottom_note(plate, inner,
          "Watch for bleeding or injury; have a rescue plan.",
          height=60, size=20)


def _draw_oncology_response(plate: RadiologyPlate,
                            item: Mapping[str, object]) -> None:
    boxes = ((76, 230, 516, 790), (580, 230, 1020, 790), (1084, 230, 1524, 790))
    headings = (("BASELINE", "select reproducible targets", BLUE),
                ("INTERVAL", "same plane + technique", TEAL),
                ("EXCEPTION CHECK", "confirmation may be needed", CORAL))
    sizes = ((92, 58), (61, 39), (112, 75))
    for index, (box, (title, subtitle, tone)) in enumerate(zip(boxes, headings)):
        inner = _panel(plate, box, title, tone, subtitle=subtitle)
        cx = (inner[0] + inner[2]) / 2
        # Same two target locations at each timepoint.
        for lesion_index, (dx, dy) in enumerate(((-66, 86), (72, 216))):
            width, height = sizes[index]
            if lesion_index:
                width *= .72
                height *= .72
            x, y = cx + dx, inner[1] + dy
            plate.draw.ellipse((x - width / 2, y - height / 2,
                                x + width / 2, y + height / 2),
                               fill=(hex_rgba(tone, 85) if index == 2 else
                                     hex_rgba(PALES[index], 180)),
                               outline=tone, width=5)
            plate.double_arrow((x - width / 2, y + height / 2 + 16),
                               (x + width / 2, y + height / 2 + 16),
                               fill=tone, width=4)
            plate.text((x, y + height / 2 + 42), "d{}".format(lesion_index + 1),
                       size=22, bold=True, fill=_text_tone(tone), anchor="mm")
        plate.draw.line((inner[0] + 24, inner[1] + 300,
                         inner[2] - 24, inner[1] + 300), fill=GRID, width=3)
        if index == 0:
            _tag(plate, (cx, inner[1] + 320), "SUM = d1 + d2", BLUE, size=22)
            bottom = "Record lesions and technique."
        elif index == 1:
            _tag(plate, (cx, inner[1] + 320), "BASELINE / NADIR", TEAL, size=21)
            bottom = "RECIST: shrinkage vs baseline; growth vs smallest prior sum."
        else:
            for radius in (58, 72):
                plate.draw.arc((cx - 66 - radius, inner[1] + 86 - radius,
                                cx - 66 + radius, inner[1] + 86 + radius),
                               205, 505, fill=CORAL, width=3)
            # Clock / repeat symbol.
            plate.draw.ellipse((cx - 19, inner[1] + 302, cx + 19, inner[1] + 340),
                               fill=PAPER_LIGHT, outline=CORAL, width=4)
            plate.draw.line((cx, inner[1] + 321, cx, inner[1] + 308,
                             cx + 11, inner[1] + 321), fill=CORAL, width=4)
            bottom = "Also check new/non-target disease and therapy-specific rules."
        _bottom_note(plate, inner, bottom, height=72, size=21)


def _draw_structured_reporting(plate: RadiologyPlate,
                               item: Mapping[str, object]) -> None:
    # A provenance pipeline rather than three disconnected report cards.
    y = 470
    plate.draw.line((125, y, 1470, y), fill=hex_rgba(GRID, 155), width=10)
    evidence = _panel(plate, (82, 235, 492, 745), "EVIDENCE", BLUE,
                      subtitle="finding + decisive negatives")
    # Document with anchored measurement/location.
    plate.draw.rounded_rectangle((evidence[0] + 42, evidence[1] + 25,
                                  evidence[2] - 42, evidence[1] + 245), radius=18,
                                 fill=PAPER_LIGHT, outline=BLUE, width=4)
    rows = (("site", 126), ("size", 93), ("prior", 110), ("negative", 110))
    for index, (label, length) in enumerate(rows):
        yy = evidence[1] + 69 + index * 47
        plate.text((evidence[0] + 66, yy), label, size=21, bold=True,
                   fill=_text_tone(BLUE), anchor="lm")
        plate.draw.line((evidence[0] + 180, yy,
                         min(evidence[0] + 180 + length, evidence[2] - 54), yy), fill=BLUE, width=4)
    plate.double_arrow((evidence[0] + 193, evidence[1] + 132),
                       (evidence[0] + 291, evidence[1] + 132), fill=CORAL, width=4)
    _bottom_note(plate, evidence, "Fixed structure prevents silent omission.",
                 height=66, size=22)

    category = _panel(plate, (595, 235, 1005, 745), "VALIDATED CATEGORY", TEAL,
                      subtitle="only inside its intended scope")
    # Three scope gates feed the category rather than implying universal RADS.
    for index, label in enumerate(("population", "indication", "technique")):
        yy = category[1] + 58 + index * 75
        plate.draw.rounded_rectangle((category[0] + 32, yy,
                                      category[2] - 32, yy + 51), radius=15,
                                     fill=hex_rgba(TEAL_LIGHT, 125),
                                     outline=TEAL, width=3)
        _check(plate, (category[0] + 67, yy + 25), scale=.58)
        plate.text((category[0] + 105, yy + 26), label, size=23,
                   bold=True, fill=INK, anchor="lm")
    _arrow(plate, ((category[0] + category[2]) / 2, category[1] + 289),
           ((category[0] + category[2]) / 2, category[1] + 339),
           tone=TEAL, width=5)
    _tag(plate, ((category[0] + category[2]) / 2, category[1] + 377),
         "CATEGORY + ACTION", TEAL, size=22)

    loop = _panel(plate, (1108, 235, 1518, 745), "CLOSE THE LOOP", CORAL,
                  subtitle="urgent / unexpected finding")
    centers = ((loop[0] + 68, loop[1] + 156),
               ((loop[0] + loop[2]) / 2, loop[1] + 216),
               (loop[2] - 68, loop[1] + 156))
    for center, label, tone in zip(centers, ("ALERT", "OWNER", "ACK"),
                                   (CORAL, BLUE, GREEN)):
        plate.draw.ellipse((center[0] - 50, center[1] - 50,
                            center[0] + 50, center[1] + 50),
                           fill=hex_rgba(CORAL_LIGHT if tone == CORAL else
                                         BLUE_LIGHT if tone == BLUE else GREEN_LIGHT, 160),
                           outline=tone, width=4)
        plate.text(center, label, size=21, bold=True,
                   fill=_text_tone(tone), anchor="mm")
    for start, end, tone in ((centers[0], centers[1], CORAL),
                             (centers[1], centers[2], BLUE),
                             (centers[2], centers[0], GREEN)):
        dx, dy = end[0] - start[0], end[1] - start[1]
        distance = math.hypot(dx, dy)
        plate.arrow((start[0] + 53 * dx / distance, start[1] + 53 * dy / distance),
                    (end[0] - 53 * dx / distance, end[1] - 53 * dy / distance),
                    fill=tone, width=5, head=12)
    _bottom_note(plate, loop,
                 "Named owner, acknowledged message, documented action.",
                 height=78, size=21)


def _draw_ir_basics(plate: RadiologyPlate, item: Mapping[str, object]) -> None:
    boxes = ((78, 232, 510, 784), (584, 232, 1016, 784), (1090, 232, 1522, 784))
    # Frame 1: safe access route to a branch target.
    inner = _panel(plate, boxes[0], "1  ACCESS", BLUE,
                   subtitle="route can be closed")
    start = ((inner[0] + inner[2]) / 2, inner[1] + 180)
    _vessel_branch(plate, start, CORAL, scale=.83, width=20)
    plate.draw.line((inner[0] + 22, inner[1] + 276,
                     start[0], start[1] + 97), fill=BLUE, width=8)
    plate.draw.polygon(((inner[0] + 13, inner[1] + 262),
                        (inner[0] + 47, inner[1] + 271),
                        (inner[0] + 26, inner[1] + 302)), fill=BLUE)
    plate.text((inner[0] + 66, inner[1] + 314), "sheath", size=23, bold=True,
               fill=_text_tone(BLUE), anchor="lm")
    _bottom_note(plate, inner,
                 "Map access, closure and vulnerable branches before treatment.",
                 height=86, size=21)

    # Frame 2: delivery at an intended level, with non-target branch spared.
    inner = _panel(plate, boxes[1], "2  TREAT", TEAL,
                   subtitle="agent behaviour matches endpoint")
    start = ((inner[0] + inner[2]) / 2, inner[1] + 180)
    _vessel_branch(plate, start, CORAL, scale=.83, width=20)
    catheter = ((start[0], start[1] + 100), (start[0], start[1] + 9),
                (start[0] - 67, start[1] - 60), (start[0] - 101, start[1] - 90))
    plate.draw.line(catheter, fill=TEAL, width=7, joint="curve")
    for dx, dy in ((-116, -104), (-128, -91), (-104, -84)):
        plate.dot((start[0] + dx, start[1] + dy), 7, fill=GOLD,
                  outline=INK, width=2)
    plate.draw.line((start[0] + 52, start[1] - 42,
                     start[0] + 123, start[1] - 106), fill=CORAL, width=19)
    plate.text((start[0] + 93, start[1] - 128), "SPARED", size=21, bold=True,
               fill=_text_tone(GREEN), anchor="mm")
    _bottom_note(plate, inner,
                 "Deliver at the intended level; protect non-target tissue.",
                 height=86, size=21)

    # Frame 3: compare pre/post endpoint and screen complications.
    inner = _panel(plate, boxes[2], "3  CHECK", CORAL,
                   subtitle="endpoint + complication search")
    for index, (label, flowing) in enumerate((("PRE", True), ("POST", False))):
        cx = inner[0] + 105 + index * 200
        cy = inner[1] + 153
        plate.draw.line((cx, cy + 94, cx, cy - 10,
                         cx - 57, cy - 74), fill=CORAL, width=15, joint="curve")
        plate.draw.line((cx, cy - 10, cx + 57, cy - 74), fill=CORAL,
                        width=15, joint="curve")
        if flowing:
            plate.arrow((cx, cy + 70), (cx - 49, cy - 63),
                        fill=BLUE, width=5, head=14)
        else:
            # Occlude the selected left branch, not the parent trunk:
            # the contralateral non-target branch must remain patent.
            stop_x, stop_y = cx - 32, cy - 46
            plate.draw.line((stop_x - 10, stop_y - 10, stop_x + 10, stop_y + 10),
                            fill=GOLD, width=9)
            plate.draw.line((stop_x - 10, stop_y + 10, stop_x + 10, stop_y - 10),
                            fill=GOLD, width=9)
            plate.arrow((cx, cy + 70), (cx + 49, cy - 63),
                        fill=BLUE, width=5, head=14)
        plate.text((cx, cy + 105), label, size=22, bold=True,
                   fill=INK_SOFT, anchor="mm")
    plate.draw.rounded_rectangle((inner[0] + 20, inner[1] + 278,
                                  inner[2] - 20, inner[1] + 326), radius=15,
                                 fill=hex_rgba(GREEN_LIGHT, 145), outline=GREEN, width=3)
    _check(plate, (inner[0] + 53, inner[1] + 302), scale=.52)
    plate.text((inner[0] + 82, inner[1] + 302), "other branch open",
               size=20, bold=True, fill=INK, anchor="lm")
    _bottom_note(plate, inner,
                 "Then search immediately for complications.",
                 height=68, size=21)


def _draw_airways(plate: RadiologyPlate, item: Mapping[str, object]) -> None:
    boxes = ((76, 228, 516, 790), (580, 228, 1020, 790), (1084, 228, 1524, 790))
    inner = _panel(plate, boxes[0], "BRONCHIECTASIS", BLUE,
                   subtitle="airway : artery + taper")
    cx, cy = (inner[0] + inner[2]) / 2, inner[1] + 145
    # Signet-ring comparison and a parallel branch that fails to taper.
    plate.draw.ellipse((cx - 112, cy - 71, cx + 28, cy + 69),
                       fill=PAPER_LIGHT, outline=BLUE, width=10)
    plate.dot((cx + 86, cy), 40, fill=CORAL, outline=INK, width=3)
    plate.text((cx - 42, cy), "AIRWAY", size=22, bold=True,
               fill=_text_tone(BLUE), anchor="mm")
    plate.text((cx + 86, cy + 66), "artery", size=21, bold=True,
               fill=_text_tone(CORAL), anchor="mm")
    plate.draw.line((cx - 118, inner[1] + 245, cx - 25, inner[1] + 303,
                     cx + 93, inner[1] + 344), fill=BLUE, width=17, joint="curve")
    plate.draw.line((cx - 116, inner[1] + 281, cx - 23, inner[1] + 326,
                     cx + 91, inner[1] + 352), fill=CORAL, width=7, joint="curve")
    _tag(plate, (cx, inner[1] + 383), "AIRWAY DOES NOT TAPER", BLUE, size=21)

    inner = _panel(plate, boxes[1], "SMALL AIRWAYS", TEAL,
                   subtitle="tree-in-bud + expiratory trapping")
    cx = (inner[0] + inner[2]) / 2
    # Branching centrilobular pattern.
    root = (cx - 86, inner[1] + 67)
    segments = [(root, (cx - 28, inner[1] + 126)),
                ((cx - 28, inner[1] + 126), (cx + 27, inner[1] + 177)),
                ((cx - 28, inner[1] + 126), (cx - 64, inner[1] + 206)),
                ((cx + 27, inner[1] + 177), (cx + 73, inner[1] + 126)),
                ((cx + 27, inner[1] + 177), (cx + 80, inner[1] + 231))]
    for start, end in segments:
        plate.draw.line((*start, *end), fill=TEAL, width=7)
        for offset in (-9, 9):
            plate.dot((end[0] + offset, end[1] + 8), 7, fill=TEAL,
                      outline=INK, width=2)
    # Expiration pair: one region remains lucent/large.
    for index, (label, width, patterned) in enumerate((
            ("INSP", 104, False), ("TRAPPING", 84, True))):
        ccx = cx - 83 + index * 166
        yy = inner[1] + 315
        plate.draw.ellipse((ccx - width / 2, yy - 55,
                            ccx + width / 2, yy + 55),
                           fill=(hex_rgba(BLUE_LIGHT, 95) if not patterned
                                 else hex_rgba(GOLD_LIGHT, 165)),
                           outline=TEAL, width=4)
        if patterned:
            for offset in range(-48, 49, 18):
                plate.draw.line((ccx - 33, yy + offset, ccx + 33, yy + offset),
                                fill=GOLD, width=3)
        plate.text((ccx, yy + 83), label, size=22, bold=True,
                   fill=INK_SOFT, anchor="mm")

    inner = _panel(plate, boxes[2], "LARGE AIRWAY", CORAL,
                   subtitle="fixed narrowing vs dynamic collapse")
    cx = (inner[0] + inner[2]) / 2
    plate.text((cx, inner[1] + 33), "INSP", size=22, bold=True,
               fill=INK_SOFT, anchor="mm")
    plate.text((cx, inner[1] + 235), "EXP", size=22, bold=True,
               fill=INK_SOFT, anchor="mm")
    for column, label in enumerate(("FIXED", "DYNAMIC")):
        ccx = cx - 84 + column * 168
        plate.text((ccx, inner[1] + 69), label, size=21, bold=True,
                   fill=_text_tone(CORAL), anchor="mm")
        sizes = ((60, 34), (60, 34)) if column == 0 else ((65, 43), (65, 14))
        for row, (rx, ry) in enumerate(sizes):
            yy = inner[1] + 125 + row * 170
            plate.draw.ellipse((ccx - rx, yy - ry, ccx + rx, yy + ry),
                               fill=PAPER_LIGHT, outline=CORAL, width=7)
            if column == 1 and row == 1:
                plate.draw.line((ccx - 46, yy, ccx + 46, yy),
                                fill=CORAL, width=5)
    _bottom_note(plate, inner,
                 "Compare calibre through expiration; then use distribution.",
                 height=72, size=21)


def _texture_swatch(plate: RadiologyPlate, box: Box, kind: str,
                    tone: str) -> None:
    x0, y0, x1, y1 = box
    plate.draw.rounded_rectangle(box, radius=14, fill=hex_rgba(PAPER_LIGHT, 210),
                                 outline=tone, width=3)
    if kind == "reticulation":
        for offset in range(18, int(y1 - y0 - 9), 25):
            other = min(offset + 18, int(y1 - y0 - 10))
            plate.draw.line((x0 + 11, y0 + offset,
                             x1 - 11, y0 + other), fill=tone, width=3)
            plate.draw.line((x0 + 11, y0 + other,
                             x1 - 11, y0 + offset), fill=tone, width=2)
    elif kind == "ground glass":
        plate.draw.rectangle((x0 + 12, y0 + 12, x1 - 12, y1 - 12),
                             fill=hex_rgba(tone, 72))
        for yy in range(int(y0 + 24), int(y1 - 10), 28):
            plate.draw.line((x0 + 18, yy, x1 - 18, yy), fill=GRID, width=2)
    elif kind == "nodules":
        for dx, dy, radius in ((40, 33, 7), (85, 61, 10), (131, 36, 6),
                               (54, 92, 8), (145, 92, 9)):
            plate.dot((x0 + dx, y0 + dy), radius, fill=tone, outline=INK, width=2)
    else:
        plate.draw.polygon(((x0 + 20, y0 + 86), (x0 + 55, y0 + 29),
                            (x1 - 25, y0 + 48), (x1 - 12, y1 - 17),
                            (x0 + 43, y1 - 12)), fill=hex_rgba(tone, 175))


def _draw_hrct(plate: RadiologyPlate, item: Mapping[str, object]) -> None:
    left = _panel(plate, (67, 225, 555, 790), "1  NAME THE SIGN", BLUE,
                  subtitle="describe before diagnosing")
    swatches = (("reticulation", BLUE), ("ground glass", TEAL),
                ("nodules", CORAL), ("consolidation", PLUM))
    for index, (label, tone) in enumerate(swatches):
        col, row = index % 2, index // 2
        box = (left[0] + col * 218, left[1] + 18 + row * 183,
               left[0] + col * 218 + 195, left[1] + 137 + row * 183)
        _texture_swatch(plate, box, label, tone)
        plate.text(((box[0] + box[2]) / 2, box[3] + 25), label.upper(),
                   size=20, bold=True, fill=_text_tone(tone), anchor="mm")
    _bottom_note(plate, left,
                 "The elementary sign is evidence, not the final diagnosis.",
                 height=60, size=20)

    middle = _panel(plate, (585, 225, 1015, 790), "2  MAP DISTRIBUTION", TEAL,
                    subtitle="where the sign lives")
    cx, cy = (middle[0] + middle[2]) / 2, middle[1] + 185
    _lung_pair(plate, (cx, cy), .95)
    # Redundant location codes: U/L and peripheral ring versus central dots.
    plate.draw.arc((cx - 97, cy - 60, cx - 6, cy + 111), 95, 270,
                   fill=TEAL, width=10)
    plate.draw.arc((cx + 6, cy - 60, cx + 97, cy + 111), 270, 445,
                   fill=TEAL, width=10)
    for dx, dy in ((-41, -23), (38, -6), (-34, 45), (42, 63)):
        plate.dot((cx + dx, cy + dy), 7, fill=CORAL, outline=INK, width=2)
    plate.text((cx - 122, cy - 55), "U", size=22, bold=True,
               fill=INK_SOFT, anchor="mm")
    plate.text((cx - 122, cy + 84), "L", size=22, bold=True,
               fill=INK_SOFT, anchor="mm")
    _tag(plate, (cx, middle[1] + 329), "C / P  +  U / L",
         TEAL, size=24)
    _bottom_note(plate, middle,
                 "Distribution changes the differential before categorisation.",
                 height=62, size=20)

    right = _panel(plate, (1045, 225, 1533, 790), "3  FIBROTIC CATEGORY", CORAL,
                   subtitle="combine positive + discordant signs")
    # A decision ladder.  Honeycombing is shown as stacked subpleural cysts.
    for index, (label, mark, tone) in enumerate((
            ("HONEYCOMBING", "rings", CORAL),
            ("TRACTION AIRWAYS", "branches", TEAL),
            ("DISCORDANT SIGN", "cross", PLUM))):
        yy = right[1] + 21 + index * 105
        plate.draw.rounded_rectangle((right[0] + 16, yy, right[2] - 16, yy + 94),
                                     radius=18, fill=hex_rgba(PALES[index], 105),
                                     outline=tone, width=3)
        icon_x = right[0] + 77
        if mark == "rings":
            for row in range(2):
                for col in range(3):
                    plate.draw.ellipse((icon_x - 43 + col * 31, yy + 18 + row * 31,
                                        icon_x - 21 + col * 31, yy + 40 + row * 31),
                                       outline=tone, width=4)
        elif mark == "branches":
            # Hollow, distorted airway with a side branch, not a generic slash.
            paths = ((icon_x - 36, yy + 76, icon_x - 12, yy + 48,
                      icon_x + 9, yy + 52, icon_x + 36, yy + 18),
                     (icon_x - 12, yy + 48, icon_x - 33, yy + 18))
            for path in paths:
                plate.draw.line(path, fill=tone, width=19, joint="curve")
            for path in paths:
                plate.draw.line(path, fill=PAPER_LIGHT, width=9, joint="curve")
        else:
            _cross(plate, (icon_x, yy + 47), tone=tone, scale=1.2)
        plate.text((right[0] + 145, yy + 47), label, size=22, bold=True,
                   fill=_text_tone(tone), anchor="lm")
    plate.text(((right[0] + right[2]) / 2, right[1] + 349),
               "UIP / PROBABLE / INDETERMINATE",
               size=20, bold=True, fill=INK, anchor="mm")
    plate.text(((right[0] + right[2]) / 2, right[1] + 382),
               "ALTERNATIVE DIAGNOSIS",
               size=20, bold=True, fill=INK, anchor="mm")


def _draw_mediastinum(plate: RadiologyPlate,
                      item: Mapping[str, object]) -> None:
    plate.text((800, 208), "SCHEMATIC AXIAL COMPARTMENTS — ANTERIOR AT TOP",
               size=25, bold=True, fill=INK_SOFT, anchor="mm")
    cx, cy = 800, 505
    # Thoracic contour, lungs, sternum and vertebra orient the map.
    plate.draw.ellipse((566, 270, 1034, 744), fill=hex_rgba(GOLD_LIGHT, 48),
                       outline=INK_SOFT, width=5)
    plate.draw.ellipse((600, 345, 752, 658), fill=hex_rgba(BLUE_LIGHT, 92),
                       outline=BLUE, width=4)
    plate.draw.ellipse((848, 345, 1000, 658), fill=hex_rgba(BLUE_LIGHT, 92),
                       outline=BLUE, width=4)
    plate.draw.ellipse((773, 279, 827, 317), fill=GOLD_LIGHT, outline=GOLD, width=4)
    plate.text((800, 251), "ANTERIOR", size=22, bold=True,
               fill=INK_SOFT, anchor="mm")
    plate.draw.ellipse((746, 652, 854, 723), fill=GOLD_LIGHT,
                       outline=GOLD, width=4)
    plate.text((800, 768), "POSTERIOR", size=22, bold=True,
               fill=INK_SOFT, anchor="mm")

    # Compartment regions are coded by number, fill and outline.
    plate.draw.rounded_rectangle((742, 325, 858, 422), radius=35,
                                 fill=hex_rgba(BLUE_LIGHT, 190),
                                 outline=BLUE, width=5)
    plate.draw.rounded_rectangle((728, 420, 872, 668), radius=48,
                                 fill=hex_rgba(TEAL_LIGHT, 190),
                                 outline=TEAL, width=5)
    plate.draw.rounded_rectangle((695, 668, 905, 735), radius=28,
                                 fill=hex_rgba(CORAL_LIGHT, 190),
                                 outline=CORAL, width=5)
    # Posterior region begins within the vertebral body, not anterior to it.
    plate.draw.ellipse((746, 652, 854, 723), fill=GOLD_LIGHT,
                       outline=GOLD, width=4)
    for number, center, tone in (("1", (800, 374), BLUE),
                                 ("2", (800, 602), TEAL),
                                 ("3", (881, 700), CORAL)):
        plate.dot(center, 25, fill=tone, outline=INK, width=3)
        plate.text(center, number, size=24, bold=True,
                   fill=PAPER_LIGHT, anchor="mm")
    # Trachea and oesophagus live in the visceral compartment.
    plate.draw.ellipse((773, 451, 827, 505), fill=PAPER_LIGHT,
                       outline=INK_SOFT, width=4)
    plate.draw.ellipse((786, 523, 814, 548), fill=PLUM_LIGHT,
                       outline=PLUM, width=3)

    callouts = (((66, 287, 475, 432), "1  PREVASCULAR",
                 "thymic • germ-cell • thyroid • lymphoid", BLUE, (742, 374)),
                ((1125, 287, 1534, 432), "2  VISCERAL",
                 "trachea • oesophagus • nodes", TEAL, (872, 499)),
                ((1084, 611, 1493, 756), "3  PARAVERTEBRAL",
                 "neural • vertebral origins", CORAL, (905, 700)))
    for box, title, note, tone, anchor in callouts:
        plate.card(box, fill=hex_rgba(PAPER_LIGHT, 230), outline=tone,
                   width=4, radius=20)
        plate.text((box[0] + 24, box[1] + 37), title, size=24, bold=True,
                   fill=_text_tone(tone), anchor="lm")
        plate.text((box[0] + 24, box[1] + 91), note, size=21,
                   fill=INK, anchor="lm")
        start = (box[2], (box[1] + box[3]) / 2) if box[0] < 800 else \
                (box[0], (box[1] + box[3]) / 2)
        plate.arrow(start, anchor, fill=tone, width=5, head=16)


def _draw_pleura(plate: RadiologyPlate, item: Mapping[str, object]) -> None:
    boxes = ((75, 228, 515, 790), (580, 228, 1020, 790), (1085, 228, 1525, 790))
    inner = _panel(plate, boxes[0], "PLEURAL AIR", BLUE,
                   subtitle="line + absent peripheral markings")
    cx, cy = (inner[0] + inner[2]) / 2, inner[1] + 160
    plate.draw.ellipse((cx - 132, cy - 145, cx + 132, cy + 145),
                       fill=hex_rgba(BLUE_LIGHT, 58), outline=INK_SOFT, width=4)
    plate.draw.arc((cx - 78, cy - 120, cx + 92, cy + 120), 278, 445,
                   fill=BLUE, width=9)
    # Vascular markings remain only medial to the pleural line.
    for dx, dy in ((-60, -55), (-42, 0), (-67, 64), (10, 20)):
        plate.draw.line((cx - 7, cy, cx + dx, cy + dy), fill=GRID, width=4)
    plate.text((cx, cy - 166), "NO MARKINGS BEYOND LINE", size=19, bold=True,
               fill=_text_tone(BLUE), anchor="mm")
    plate.arrow((cx + 104, cy - 147), (cx + 111, cy - 12),
                fill=BLUE, width=3, head=10)
    _tag(plate, (cx, inner[1] + 322), "PLEURAL LINE", BLUE, size=22)
    _bottom_note(plate, inner,
                 "Confirm the line; a skin fold keeps lung markings beyond it.",
                 height=70, size=20)

    inner = _panel(plate, boxes[1], "PLEURAL FLUID", TEAL,
                   subtitle="dependent layer or fixed locule")
    centers = (inner[0] + 104, inner[2] - 104)
    for index, cx in enumerate(centers):
        cy = inner[1] + 160
        plate.draw.ellipse((cx - 82, cy - 135, cx + 82, cy + 135),
                           fill=hex_rgba(BLUE_LIGHT, 45), outline=INK_SOFT, width=4)
        if index == 0:
            plate.draw.pieslice((cx - 80, cy - 133, cx + 80, cy + 133),
                                0, 180, fill=hex_rgba(TEAL_LIGHT, 210))
            label = "LAYERS"
        else:
            plate.draw.ellipse((cx + 20, cy - 37, cx + 78, cy + 46),
                               fill=hex_rgba(TEAL_LIGHT, 210), outline=TEAL, width=5)
            label = "LOCULATED"
        plate.text((cx, cy + 162), label, size=21, bold=True,
                   fill=_text_tone(TEAL), anchor="mm")
    _bottom_note(plate, inner,
                 "Fluid layers with gravity unless adhesions fix its shape.",
                 height=70, size=20)

    inner = _panel(plate, boxes[2], "COMPLEX PLEURA", CORAL,
                   subtitle="thickening, nodularity, septation")
    cx, cy = (inner[0] + inner[2]) / 2, inner[1] + 160
    plate.draw.ellipse((cx - 132, cy - 145, cx + 132, cy + 145),
                       fill=hex_rgba(BLUE_LIGHT, 45), outline=INK_SOFT, width=4)
    plate.draw.arc((cx - 125, cy - 140, cx + 125, cy + 140), 265, 455,
                   fill=CORAL, width=17)
    for angle in (-62, -10, 43, 92):
        radians = math.radians(angle)
        px = cx + 119 * math.cos(radians)
        py = cy + 130 * math.sin(radians)
        plate.dot((px, py), 12, fill=CORAL, outline=INK, width=3)
    for offset in (-55, 15, 71):
        plate.draw.line((cx - 72, cy + offset, cx + 77, cy + offset + 28),
                        fill=TEAL, width=4)
    _tag(plate, (cx, inner[1] + 322), "MORPHOLOGY CHANGES ACTION", CORAL, size=21)
    _bottom_note(plate, inner,
                 "Complex morphology needs clinical and sampling context.",
                 height=70, size=20)


def _draw_chest_infection(plate: RadiologyPlate,
                          item: Mapping[str, object]) -> None:
    # Three evidence dimensions converge on a ranked differential.
    left = _panel(plate, (68, 225, 596, 790), "PATTERN + DISTRIBUTION", BLUE)
    patterns = (("AIR-SPACE", "lobar / multifocal", BLUE),
                ("TREE-IN-BUD", "airway spread", TEAL),
                ("CAVITY", "wall + contents", CORAL))
    for index, (label, subtitle, tone) in enumerate(patterns):
        yy = left[1] + 25 + index * 126
        plate.draw.rounded_rectangle((left[0] + 12, yy, left[0] + 150, yy + 96),
                                     radius=16, fill=hex_rgba(PALES[index], 120),
                                     outline=tone, width=3)
        if index == 0:
            plate.draw.polygon(((left[0] + 30, yy + 74), (left[0] + 65, yy + 25),
                                (left[0] + 132, yy + 42), (left[0] + 125, yy + 82)),
                               fill=hex_rgba(tone, 180))
        elif index == 1:
            plate.draw.line((left[0] + 36, yy + 80, left[0] + 79, yy + 51,
                             left[0] + 117, yy + 26), fill=tone, width=6)
            for dx, dy in ((72, 47), (110, 23), (83, 60), (122, 39)):
                plate.dot((left[0] + dx, yy + dy), 6, fill=tone, outline=INK, width=2)
        else:
            plate.draw.ellipse((left[0] + 40, yy + 18,
                                left[0] + 125, yy + 87), fill=PAPER_LIGHT,
                               outline=tone, width=10)
        plate.text((left[0] + 181, yy + 33), label, size=23, bold=True,
                   fill=_text_tone(tone), anchor="lm")
        plate.text((left[0] + 181, yy + 70), subtitle, size=22,
                   fill=INK_SOFT, anchor="lm")
    _bottom_note(plate, left,
                 "A pattern suggests a mechanism; it does not name the organism.",
                 height=62, size=21)

    middle = _panel(plate, (626, 225, 1054, 790), "HOST FILTER", TEAL,
                    subtitle="immune setting changes priors")
    rows = (("IMMUNE INTACT", BLUE, "common + exposure"),
            ("IMMUNE IMPAIRED", CORAL, "opportunistic + mimic"))
    for index, (label, tone, note) in enumerate(rows):
        yy = middle[1] + 50 + index * 167
        plate.draw.rounded_rectangle((middle[0] + 18, yy,
                                      middle[2] - 18, yy + 124), radius=20,
                                     fill=hex_rgba(BLUE_LIGHT if index == 0 else
                                                   CORAL_LIGHT, 120),
                                     outline=tone, width=4)
        # Shield with different internal texture, not colour alone.
        shield = ((middle[0] + 63, yy + 23), (middle[0] + 104, yy + 23),
                  (middle[0] + 111, yy + 71), (middle[0] + 84, yy + 101),
                  (middle[0] + 56, yy + 71))
        plate.draw.polygon(shield, fill=PAPER_LIGHT, outline=tone)
        if index:
            _cross(plate, (middle[0] + 84, yy + 57), tone=tone, scale=.75)
        else:
            _check(plate, (middle[0] + 84, yy + 57), tone=GREEN, scale=.7)
        plate.text((middle[0] + 137, yy + 43), label, size=20, bold=True,
                   fill=_text_tone(tone), anchor="lm")
        plate.text((middle[0] + 137, yy + 83), note, size=18,
                   fill=INK_SOFT, anchor="lm")
    _bottom_note(plate, middle,
                 "Therapy, immune status and exposure alter the differential.",
                 height=62, size=20)

    right = _panel(plate, (1084, 225, 1532, 790), "TIME COURSE", CORAL,
                   subtitle="schematic response, not patient data")
    x0, x1 = right[0] + 38, right[2] - 30
    y = right[1] + 213
    plate.arrow((x0, y), (x1, y), fill=INK_SOFT, width=5, head=16)
    for fraction, label in ((0, "DAY 0"), (.5, "REVIEW"), (1, "LATER")):
        x = x0 + fraction * (x1 - x0)
        plate.draw.line((x, y - 23, x, y + 23), fill=CORAL, width=5)
        plate.text((x, y + 51), label, size=20, bold=True,
                   fill=_text_tone(CORAL), anchor="rm" if fraction == 1 else "lm" if fraction == 0 else "mm")
    # Two trajectories: expected improvement and non-response.
    plate.polyline(((x0, y - 92), ((x0 + x1) / 2, y - 39), (x1, y - 15)),
                   fill=GREEN, width=7)
    plate.polyline(((x0, y - 92), ((x0 + x1) / 2, y - 111), (x1, y - 105)),
                   fill=CORAL, width=7)
    _tag(plate, ((x0 + x1) / 2, right[1] + 315),
         "PATTERN + HOST + TIME", CORAL, size=22)
    _arrow(plate, ((x0 + x1) / 2, right[1] + 347),
           ((x0 + x1) / 2, right[1] + 392), tone=GOLD, width=5)
    plate.text(((x0 + x1) / 2, right[1] + 421), "RANKED DIFFERENTIAL",
               size=23, bold=True, fill=INK, anchor="mm")


def _draw_pe_pulm_htn(plate: RadiologyPlate,
                      item: Mapping[str, object]) -> None:
    boxes = ((67, 226, 542, 790), (563, 226, 1038, 790), (1059, 226, 1533, 790))
    inner = _panel(plate, boxes[0], "1  ACQUISITION QUALITY", BLUE,
                   subtitle="arterial contrast + motion control")
    graph = (inner[0] + 38, inner[1] + 32, inner[2] - 28, inner[1] + 257)
    _axis(plate, graph, "time", "PA contrast")
    gx0, gy0, gx1, gy1 = graph
    curve = []
    for index in range(81):
        t = index / 80
        signal = math.exp(-((t - .52) / .19) ** 2)
        curve.append((gx0 + t * (gx1 - gx0), gy1 - 23 - signal * 157))
    plate.polyline(curve, fill=BLUE, width=8)
    scan0, scan1 = gx0 + .39 * (gx1 - gx0), gx0 + .64 * (gx1 - gx0)
    plate.draw.rectangle((scan0, gy0 + 8, scan1, gy1),
                         fill=hex_rgba(TEAL_LIGHT, 65), outline=TEAL, width=4)
    plate.text(((scan0 + scan1) / 2, gy0 + 29), "SCAN WINDOW", size=20,
               bold=True, fill=_text_tone(TEAL), anchor="mm")
    plate.polyline(((inner[0] + 28, inner[1] + 325),
                    (inner[0] + 94, inner[1] + 325),
                    (inner[0] + 109, inner[1] + 290),
                    (inner[0] + 125, inner[1] + 352),
                    (inner[0] + 144, inner[1] + 325),
                    (inner[2] - 28, inner[1] + 325)), fill=CORAL, width=5)
    _tag(plate, ((inner[0] + inner[2]) / 2, inner[1] + 385),
         "CONTRAST ADEQUATE • MOTION LOW", BLUE, size=20)

    inner = _panel(plate, boxes[1], "2  PROVE THE DEFECT", TEAL,
                   subtitle="intraluminal + multiplanar")
    cx, cy = (inner[0] + inner[2]) / 2, inner[1] + 188
    _vessel_branch(plate, (cx, cy + 20), CORAL, scale=.82, width=29)
    defect = (cx + 58, cy - 49)
    plate.draw.ellipse((defect[0] - 18, defect[1] - 30,
                        defect[0] + 18, defect[1] + 30),
                       fill=PAPER_LIGHT, outline=TEAL, width=6)
    plate.draw.ellipse((defect[0] - 7, defect[1] - 21,
                        defect[0] + 7, defect[1] + 21), fill=INK_SOFT)
    # Orthogonal confirmation inset.
    plate.draw.rounded_rectangle((inner[0] + 28, inner[1] + 280,
                                  inner[2] - 28, inner[1] + 377), radius=18,
                                 fill=hex_rgba(TEAL_LIGHT, 85), outline=TEAL, width=4)
    for index in range(2):
        ccx = inner[0] + 103 + index * 207
        plate.draw.ellipse((ccx - 42, inner[1] + 297,
                            ccx + 42, inner[1] + 361),
                           fill=CORAL_LIGHT, outline=CORAL, width=4)
        plate.draw.ellipse((ccx - 10, inner[1] + 310,
                            ccx + 10, inner[1] + 348), fill=INK_SOFT)
        plate.text((ccx, inner[1] + 395), ("AXIAL", "REFORMAT")[index],
                   size=20, bold=True, fill=INK_SOFT, anchor="mm")

    inner = _panel(plate, boxes[2], "3  ASSESS STRAIN", CORAL,
                   subtitle="risk features, not clot size alone")
    cx, cy = (inner[0] + inner[2]) / 2, inner[1] + 173
    # Qualitative four-chamber comparison with labels and different hatch.
    plate.draw.ellipse((cx - 141, cy - 105, cx + 141, cy + 112),
                       fill=hex_rgba(CORAL_LIGHT, 70), outline=INK_SOFT, width=4)
    plate.draw.ellipse((cx - 104, cy - 63, cx - 2, cy + 70),
                       fill=hex_rgba(BLUE_LIGHT, 150), outline=BLUE, width=6)
    plate.draw.ellipse((cx + 20, cy - 44, cx + 95, cy + 54),
                       fill=hex_rgba(TEAL_LIGHT, 150), outline=TEAL, width=6)
    plate.text((cx - 53, cy), "RV", size=27, bold=True,
               fill=_text_tone(BLUE), anchor="mm")
    plate.text((cx + 57, cy), "LV", size=27, bold=True,
               fill=_text_tone(TEAL), anchor="mm")
    plate.double_arrow((cx - 104, cy + 91), (cx - 2, cy + 91), fill=BLUE, width=4)
    plate.double_arrow((cx + 20, cy + 91), (cx + 95, cy + 91), fill=TEAL, width=4)
    # IVC/reflux schematic.
    plate.draw.line((cx + 111, cy + 34, cx + 111, cy + 179),
                    fill=CORAL, width=13)
    plate.arrow((cx + 111, cy + 76), (cx + 111, cy + 150),
                fill=GOLD, width=6, head=17)
    plate.text((cx + 111, cy + 204), "IVC reflux", size=21, bold=True,
               fill=_text_tone(GOLD), anchor="mm")


def _draw_lung_cancer(plate: RadiologyPlate,
                      item: Mapping[str, object]) -> None:
    plate.text((800, 207), "ONE STAGING MAP — THREE INDEPENDENT QUESTIONS",
               size=26, bold=True, fill=INK_SOFT, anchor="mm")
    cx, cy = 800, 500
    _lung_pair(plate, (cx, cy), 1.15)
    # Primary near pleura/airway/vessel.
    primary = (706, 486)
    plate.draw.ellipse((primary[0] - 37, primary[1] - 32,
                        primary[0] + 37, primary[1] + 32),
                       fill=hex_rgba(BLUE, 205), outline=INK, width=4)
    plate.draw.line((cx, cy - 58, primary[0] + 11, primary[1] - 9),
                    fill=INK_SOFT, width=8)
    plate.draw.arc((cx - 116, cy - 74, cx - 6, cy + 126), 95, 270,
                   fill=CORAL, width=5)
    # Named station examples: right paratracheal 4R and subcarinal 7.
    nodes = (((763, 407), "4R"), ((800, 475), "7"))
    for center, label in nodes:
        plate.dot(center, 17, fill=TEAL, outline=INK, width=3)
        plate.text((center[0] - 29 if label == "4R" else center[0] + 29,
                    center[1]), label, size=20, bold=True,
                   fill=_text_tone(TEAL), anchor="rm" if label == "4R" else "lm")
    plate.text((650, 630), "PATIENT R", size=20, bold=True,
               fill=INK_SOFT, anchor="mm")
    # Distant/other-compartment markers: opposite lung, pleura, adrenal.
    plate.dot((886, 528), 14, fill=CORAL, outline=INK, width=3)
    plate.dot((902, 616), 11, fill=CORAL, outline=INK, width=3)
    plate.draw.arc((900, 623, 956, 681), 205, 515, fill=CORAL, width=7)

    callouts = (((76, 275, 490, 457), "T  PRIMARY",
                 "size • invasion • pleura / airway / vessels", BLUE, primary),
                ((1110, 275, 1524, 457), "N  NODES",
                 "name the nodal station", TEAL, (763, 407)),
                ((1080, 631, 1494, 784), "M  SPREAD",
                 "opposite lung • pleura • distant organs", CORAL, (902, 616)))
    for box, title, note, tone, target in callouts:
        plate.card(box, fill=hex_rgba(PAPER_LIGHT, 230), outline=tone,
                   width=4, radius=20)
        plate.text((box[0] + 25, box[1] + 42), title, size=26, bold=True,
                   fill=_text_tone(tone), anchor="lm")
        _note(plate, (box[0] + 25, box[1] + 70, box[2] - 25, box[3] - 14),
              note, size=22, tone=INK, bold=True)
        start = (box[2], (box[1] + box[3]) / 2) if box[0] < 800 else \
                (box[0], (box[1] + box[3]) / 2)
        plate.arrow(start, target, fill=tone, width=5, head=16)


def _draw_chest_xray(plate: RadiologyPlate,
                     item: Mapping[str, object]) -> None:
    boxes = ((66, 225, 526, 790), (570, 225, 1030, 790), (1074, 225, 1534, 790))
    inner = _panel(plate, boxes[0], "1  TECHNIQUE: P-R-I-E", BLUE)
    checks = (("P", "projection", "PA / AP"),
              ("R", "rotation", "clavicles"),
              ("I", "inspiration", "lung volume"),
              ("E", "exposure", "through heart"))
    for index, (letter, label, clue) in enumerate(checks):
        yy = inner[1] + 23 + index * 92
        plate.dot((inner[0] + 42, yy + 31), 27, fill=BLUE,
                  outline=INK, width=3)
        plate.text((inner[0] + 42, yy + 31), letter, size=25, bold=True,
                   fill=PAPER_LIGHT, anchor="mm")
        plate.text((inner[0] + 88, yy + 19), label.upper(), size=22,
                   bold=True, fill=_text_tone(BLUE), anchor="lm")
        plate.text((inner[0] + 88, yy + 50), clue, size=21,
                   fill=INK_SOFT, anchor="lm")
    _bottom_note(plate, inner,
                 "Technique can create or conceal an apparent abnormality.",
                 height=67, size=21)

    inner = _panel(plate, boxes[1], "2  SYSTEMATIC SEARCH", TEAL,
                   subtitle="one pass per structure")
    cx, cy = (inner[0] + inner[2]) / 2, inner[1] + 206
    _lung_pair(plate, (cx, cy), .98)
    path = ((cx, cy - 108), (cx - 67, cy - 31), (cx + 67, cy - 6),
            (cx - 59, cy + 62), (cx + 67, cy + 92), (cx - 23, cy + 100))
    plate.polyline(path, fill=TEAL, width=5)
    for index, point in enumerate(path, 1):
        plate.dot(point, 16, fill=TEAL, outline=INK, width=2)
        plate.text(point, str(index), size=20, bold=True,
                   fill=PAPER_LIGHT, anchor="mm")
    _tag(plate, (cx, inner[1] + 350), "A • L • P • H • H • B",
         TEAL, size=22)
    _bottom_note(plate, inner,
                 "Repeatable passes preserve decisive negatives.",
                 height=58, size=20)

    inner = _panel(plate, boxes[2], "3  SILHOUETTE SIGN", CORAL,
                   subtitle="lost border → touching lobe")
    cx, cy = (inner[0] + inner[2]) / 2, inner[1] + 198
    _lung_pair(plate, (cx, cy), .93)
    # Heart and diaphragms; lost-border examples are dashed overpaint segments.
    plate.draw.ellipse((cx - 29, cy + 10, cx + 72, cy + 126),
                       fill=hex_rgba(CORAL_LIGHT, 110), outline=CORAL, width=5)
    plate.draw.arc((cx - 104, cy + 59, cx - 4, cy + 139), 185, 350,
                   fill=INK_SOFT, width=5)
    plate.draw.arc((cx + 4, cy + 59, cx + 104, cy + 139), 190, 355,
                   fill=INK_SOFT, width=5)
    # Right-heart-border contact region.
    plate.draw.line((cx - 29, cy + 23, cx - 29, cy + 92),
                    fill=PAPER_LIGHT, width=12)
    for yy in range(int(cy + 28), int(cy + 92), 20):
        plate.draw.line((cx - 35, yy, cx - 23, yy + 10), fill=CORAL, width=4)
    _arrow(plate, (cx - 29, cy + 56), (inner[0] + 53, inner[1] + 332),
           tone=CORAL, width=5)
    _tag(plate, (cx, inner[1] + 347), "RIGHT HEART BORDER → RML",
         CORAL, size=20)
    _bottom_note(plate, inner,
                 "A lost border localises opacity to the lobe touching it.",
                 height=61, size=20)


def _draw_pulmonary_nodule(plate: RadiologyPlate,
                           item: Mapping[str, object]) -> None:
    boxes = ((67, 226, 542, 790), (563, 226, 1038, 790), (1059, 226, 1533, 790))
    inner = _panel(plate, boxes[0], "1  MEASURE REPRODUCIBLY", BLUE,
                   subtitle="recommended plane + same method")
    cx, cy = (inner[0] + inner[2]) / 2, inner[1] + 194
    # Irregular but bounded nodule, with orthogonal long/short axes.
    points = []
    for index in range(48):
        angle = math.tau * index / 48
        radius = 83 * (1 + .08 * math.sin(5 * angle))
        points.append((cx + radius * math.cos(angle),
                       cy + .68 * radius * math.sin(angle)))
    plate.draw.polygon(points, fill=hex_rgba(BLUE_LIGHT, 185), outline=BLUE)
    plate.double_arrow((cx - 89, cy), (cx + 89, cy), fill=BLUE, width=5)
    plate.double_arrow((cx, cy - 61), (cx, cy + 61), fill=TEAL, width=5)
    plate.text((cx, cy - 85), "short: vertical", size=22, bold=True,
               fill=_text_tone(TEAL), anchor="mm")
    plate.text((cx, cy + 76), "long: horizontal", size=22, bold=True,
               fill=_text_tone(BLUE), anchor="mm")
    _tag(plate, (cx, inner[1] + 325), "AVERAGE DIAMETER", BLUE, size=22)
    _bottom_note(plate, inner,
                 "Repeat the plane, edge convention and comparison method.",
                 height=61, size=20)

    inner = _panel(plate, boxes[1], "2  CLASSIFY ATTENUATION", TEAL,
                   subtitle="solid component changes behaviour")
    kinds = ((("SOLID",), "solid"), (("PART-", "SOLID"), "part"),
             (("GROUND-", "GLASS"), "ggo"))
    for index, (lines, kind) in enumerate(kinds):
        cx = inner[0] + 75 + index * 136
        cy = inner[1] + 181
        plate.draw.ellipse((cx - 53, cy - 53, cx + 53, cy + 53),
                           fill=(hex_rgba(INK_SOFT, 215) if kind == "solid" else
                                 hex_rgba(TEAL_LIGHT, 125)),
                           outline=TEAL, width=5)
        if kind == "part":
            plate.draw.ellipse((cx - 20, cy - 18, cx + 20, cy + 22),
                               fill=INK_SOFT, outline=INK, width=3)
        elif kind == "ggo":
            for yy in range(int(cy - 36), int(cy + 40), 18):
                plate.draw.line((cx - 38, yy, cx + 38, yy), fill=GRID, width=3)
        for line_index, label in enumerate(lines):
            plate.text((cx, cy + 78 + line_index * 24), label, size=20,
                       bold=True, fill=_text_tone(TEAL), anchor="mm")
    _bottom_note(plate, inner,
                 "For subsolid nodules, record any measurable solid component.",
                 height=86, size=20)

    inner = _panel(plate, boxes[2], "3  APPLY CONTEXT", CORAL,
                   subtitle="guideline eligibility before interval")
    cx = (inner[0] + inner[2]) / 2
    gates = (("age / population", BLUE), ("risk + history", TEAL),
             ("exclusions", CORAL))
    for index, (label, tone) in enumerate(gates):
        yy = inner[1] + 32 + index * 91
        plate.draw.rounded_rectangle((inner[0] + 34, yy, inner[2] - 34, yy + 61),
                                     radius=16, fill=hex_rgba(PALES[index], 120),
                                     outline=tone, width=3)
        _check(plate, (inner[0] + 70, yy + 30), scale=.55)
        plate.text((inner[0] + 108, yy + 31), label, size=22, bold=True,
                   fill=INK, anchor="lm")
    _arrow(plate, (cx, inner[1] + 285), (cx, inner[1] + 327),
           tone=GOLD, width=5)
    _tag(plate, (cx, inner[1] + 330), "FOLLOW-UP IF IT HELPS", CORAL, size=21)
    _bottom_note(plate, inner,
                 "Use the current pathway; individualise.",
                 height=34, size=20)


RENDERERS: Dict[str, Renderer] = {
    "rad.3.contrast": _draw_contrast,
    "rad.2.radiation-safety": _draw_radiation_safety,
    "rad.3.mri-sequences": _draw_mri_sequences,
    "rad.2.modalities": _draw_modalities,
    "rad.5.ultrasound-physics": _draw_ultrasound_physics,
    "rad.5.biopsy-safety": _draw_biopsy_safety,
    "rad.4.oncology-response": _draw_oncology_response,
    "rad.4.structured-reporting": _draw_structured_reporting,
    "rad.5.ir-basics": _draw_ir_basics,
    "rad.5.airways": _draw_airways,
    "rad.4.hrct": _draw_hrct,
    "rad.5.mediastinum": _draw_mediastinum,
    "rad.5.pleura": _draw_pleura,
    "rad.5.chest-infection": _draw_chest_infection,
    "rad.5.pe-pulm-htn": _draw_pe_pulm_htn,
    "rad.4.lung-cancer": _draw_lung_cancer,
    "rad.3.chest-xray": _draw_chest_xray,
    "rad.4.pulmonary-nodule": _draw_pulmonary_nodule,
}


EXPECTED_IDS = {
    "rad.3.contrast", "rad.2.radiation-safety", "rad.3.mri-sequences",
    "rad.2.modalities", "rad.5.ultrasound-physics", "rad.5.biopsy-safety",
    "rad.4.oncology-response", "rad.4.structured-reporting", "rad.5.ir-basics",
    "rad.5.airways", "rad.4.hrct", "rad.5.mediastinum", "rad.5.pleura",
    "rad.5.chest-infection", "rad.5.pe-pulm-htn", "rad.4.lung-cancer",
    "rad.3.chest-xray", "rad.4.pulmonary-nodule",
}

if set(RENDERERS) != EXPECTED_IDS:
    raise ValueError("Foundations/thorax renderer inventory drift")
if len({id(renderer) for renderer in RENDERERS.values()}) != len(RENDERERS):
    raise ValueError("Each foundations/thorax lesson needs a unique renderer")


__all__ = ["EXPECTED_IDS", "RENDERERS"]
