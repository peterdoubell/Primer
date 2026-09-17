"""Lesson-specific abdomen, pelvis, and breast radiology diagrams.

These plates are explanatory schematics rather than synthetic patient scans.
They expose the anatomy, acquisition choice, observation bundle, measurement,
classification boundary, or management relationship taught by each lesson.
Every colour cue is repeated by text, geometry, texture, or line style, and the
short labels are designed to survive the 800 px responsive export.

The module is intentionally registration-free.  ``RENDERERS`` is consumed by
the cohort aggregator after its exact lesson-id inventory has been checked.
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

TONES = (BLUE, TEAL, CORAL, PLUM, GOLD, GREEN)
PALES = (BLUE_LIGHT, TEAL_LIGHT, CORAL_LIGHT, PLUM_LIGHT,
         GOLD_LIGHT, GREEN_LIGHT)


def _panel(plate: RadiologyPlate, box: Box, title: str, tone: str = BLUE,
           *, subtitle: str = "", dashed: bool = False) -> Box:
    """Draw a high-contrast panel and return its inner working area."""
    plate.card(box, fill=hex_rgba(PAPER_LIGHT, 224), outline=tone,
               width=4, radius=22)
    x0, y0, x1, y1 = box
    if dashed:
        for x in range(int(x0 + 20), int(x1 - 20), 30):
            plate.draw.line((x, y0, min(x + 17, x1 - 20), y0),
                            fill=tone, width=5)
            plate.draw.line((x, y1, min(x + 17, x1 - 20), y1),
                            fill=tone, width=5)
    plate.text(((x0 + x1) / 2, y0 + 35), title, size=25, bold=True,
               fill=_text_tone(tone), anchor="mm")
    plate.draw.line((x0 + 22, y0 + 68, x1 - 22, y0 + 68),
                    fill=hex_rgba(tone, 130), width=3)
    if subtitle:
        plate.text(((x0 + x1) / 2, y0 + 94), subtitle, size=20,
                   bold=True, fill=INK_SOFT, anchor="mm")
        return x0 + 22, y0 + 121, x1 - 22, y1 - 20
    return x0 + 22, y0 + 88, x1 - 22, y1 - 20


def _tag(plate: RadiologyPlate, center: Point, value: str, tone: str = BLUE,
         *, size: int = 22) -> None:
    plate.label(center, value, size=max(20, size), fill=tone,
                text_fill=PAPER_LIGHT)


def _note(plate: RadiologyPlate, box: Box, value: str, *, size: int = 22,
          tone: str = INK, bold: bool = False) -> None:
    plate.wrapped_text(tuple(int(v) for v in box), value, size=size,
                       bold=bold, fill=tone, line_gap=6)


def _arrow(plate: RadiologyPlate, start: Point, end: Point, label: str = "",
           tone: str = GOLD, *, width: int = 6,
           label_at: Point | None = None) -> None:
    plate.arrow(start, end, fill=tone, width=width, head=18)
    if label:
        point = label_at or ((start[0] + end[0]) / 2,
                             (start[1] + end[1]) / 2 - 20)
        plate.text(point, label, size=20, bold=True,
                   fill=_text_tone(tone), anchor="mm")


def _check(plate: RadiologyPlate, center: Point, tone: str = GREEN,
           *, scale: float = 1.0) -> None:
    x, y = center
    plate.draw.ellipse((x - 21 * scale, y - 21 * scale,
                        x + 21 * scale, y + 21 * scale),
                       fill=hex_rgba(GREEN_LIGHT, 190), outline=tone,
                       width=max(3, int(4 * scale)))
    plate.draw.line((x - 11 * scale, y, x - 2 * scale, y + 10 * scale,
                     x + 14 * scale, y - 11 * scale),
                    fill=_text_tone(tone), width=max(3, int(5 * scale)),
                    joint="curve")


def _cross(plate: RadiologyPlate, center: Point, tone: str = CORAL,
           *, scale: float = 1.0) -> None:
    x, y = center
    reach = 15 * scale
    plate.draw.line((x - reach, y - reach, x + reach, y + reach),
                    fill=tone, width=max(3, int(6 * scale)))
    plate.draw.line((x - reach, y + reach, x + reach, y - reach),
                    fill=tone, width=max(3, int(6 * scale)))


def _hatch(plate: RadiologyPlate, box: Box, tone: str,
           *, spacing: int = 20) -> None:
    x0, y0, x1, y1 = box
    for shift in range(int(x0 - (y1 - y0)), int(x1), spacing):
        start_x = max(x0, shift)
        start_y = y0 + max(0, x0 - shift)
        end_x = min(x1, shift + (y1 - y0))
        end_y = y0 + max(0, end_x - shift)
        plate.draw.line((start_x, start_y, end_x, min(end_y, y1)),
                        fill=hex_rgba(tone, 115), width=3)


def _measure(plate: RadiologyPlate, start: Point, end: Point, label: str,
             tone: str = PLUM, *, label_at: Point | None = None) -> None:
    plate.double_arrow(start, end, fill=tone, width=5)
    point = label_at or ((start[0] + end[0]) / 2,
                         (start[1] + end[1]) / 2 - 23)
    plate.text(point, label, size=20, bold=True,
               fill=_text_tone(tone), anchor="mm")


def _step(plate: RadiologyPlate, box: Box, number: str, heading: str,
          detail: str, tone: str) -> None:
    _panel(plate, box, heading, tone)
    x0, y0, x1, y1 = box
    plate.draw.ellipse((x0 + 18, y0 + 17, x0 + 68, y0 + 67),
                       fill=tone, outline=tone)
    plate.text((x0 + 43, y0 + 42), number, size=21, bold=True,
               fill=PAPER_LIGHT, anchor="mm")
    _note(plate, (x0 + 24, y0 + 88, x1 - 24, y1 - 18), detail,
          size=21, bold=True)


def _duct_tree(plate: RadiologyPlate, center: Point, scale: float = 1.0,
               tone: str = TEAL) -> None:
    x, y = center
    plate.draw.line((x, y - 120 * scale, x, y + 125 * scale),
                    fill=tone, width=max(5, int(10 * scale)))
    for direction in (-1, 1):
        plate.draw.line((x, y - 65 * scale,
                         x + direction * 80 * scale, y - 125 * scale),
                        fill=tone, width=max(4, int(8 * scale)))
        plate.draw.line((x + direction * 44 * scale, y - 98 * scale,
                         x + direction * 105 * scale, y - 84 * scale),
                        fill=tone, width=max(3, int(6 * scale)))


def _bowel_loop(plate: RadiologyPlate, box: Box, tone: str = TEAL,
                *, width: int = 14) -> Sequence[Point]:
    x0, y0, x1, y1 = box
    points = ((x0 + 20, y0 + 25), (x1 - 25, y0 + 25),
              (x1 - 25, y0 + 82), (x0 + 40, y0 + 82),
              (x0 + 40, y0 + 139), (x1 - 42, y0 + 139),
              (x1 - 42, y1 - 20), (x0 + 20, y1 - 20))
    plate.draw.line(points, fill=tone, width=width, joint="curve")
    return points


def _kidney(plate: RadiologyPlate, center: Point, tone: str = BLUE,
            *, scale: float = 1.0) -> None:
    x, y = center
    plate.draw.ellipse((x - 78 * scale, y - 105 * scale,
                        x + 68 * scale, y + 105 * scale),
                       fill=hex_rgba(BLUE_LIGHT, 100), outline=tone,
                       width=max(3, int(5 * scale)))
    plate.draw.ellipse((x + 20 * scale, y - 44 * scale,
                        x + 88 * scale, y + 44 * scale),
                       fill=PAPER_LIGHT, outline=tone,
                       width=max(2, int(4 * scale)))


def _liver(plate: RadiologyPlate, box: Box, tone: str = CORAL) -> None:
    x0, y0, x1, y1 = box
    plate.draw.polygon(((x0 + 15, y0 + 45), (x0 + 130, y0),
                        (x1 - 25, y0 + 32), (x1, y0 + 105),
                        (x1 - 90, y1), (x0 + 35, y1 - 28)),
                       fill=hex_rgba(CORAL_LIGHT, 100), outline=tone)
    plate.draw.line(((x0 + 15, y0 + 45), (x0 + 130, y0),
                     (x1 - 25, y0 + 32), (x1, y0 + 105),
                     (x1 - 90, y1), (x0 + 35, y1 - 28),
                     (x0 + 15, y0 + 45)), fill=tone, width=5)


def _pancreas(plate: RadiologyPlate, center: Point, tone: str = GOLD,
              *, scale: float = 1.0) -> None:
    x, y = center
    points = []
    for index in range(35):
        t = index / 34
        px = x - 150 * scale + 300 * scale * t
        py = y + math.sin(t * math.pi * 2.2) * 18 * scale
        points.append((px, py))
    plate.draw.line(points, fill=tone, width=max(12, int(34 * scale)),
                    joint="curve")
    plate.draw.line(points, fill=hex_rgba(GOLD_LIGHT, 205),
                    width=max(7, int(22 * scale)), joint="curve")


def _breast_outline(plate: RadiologyPlate, center: Point,
                    tone: str = CORAL, *, scale: float = 1.0) -> None:
    x, y = center
    plate.draw.arc((x - 130 * scale, y - 115 * scale,
                    x + 130 * scale, y + 135 * scale),
                   95, 305, fill=tone, width=max(4, int(7 * scale)))
    plate.draw.line((x - 7 * scale, y - 113 * scale,
                     x - 7 * scale, y + 118 * scale),
                    fill=INK_SOFT, width=max(3, int(5 * scale)))
    plate.dot((x + 104 * scale, y + 20 * scale), 7 * scale,
              fill=tone, outline=tone, width=1)


def _render_pancreas_acute(plate: RadiologyPlate,
                           item: Mapping[str, object]) -> None:
    _ = item
    _tag(plate, (800, 205), "ATLANTA COLLECTION NAMES: TIME + CONTENT", PLUM)
    # Two-by-two matrix prevents every collection being called a pseudocyst.
    x_edges = (320, 820, 1450)
    y_edges = (285, 495, 705)
    plate.text((210, 385), "FLUID ONLY", size=18, bold=True,
               fill=_text_tone(BLUE), anchor="mm")
    plate.text((210, 600), "NECROSIS", size=18, bold=True,
               fill=_text_tone(CORAL), anchor="mm")
    plate.text((570, 250), "EARLY: <4 WEEKS", size=23, bold=True,
               fill=INK, anchor="mm")
    plate.text((1135, 250), "LATER: USUALLY >4 WEEKS + WALL", size=23,
               bold=True, fill=INK, anchor="mm")
    cells = (("APFC", "no defined wall", BLUE, False),
             ("PSEUDOCYST", "encapsulated fluid", TEAL, True),
             ("ANC", "fluid + necrosis", CORAL, False),
             ("WON", "encapsulated necrosis", PLUM, True))
    for index, (name, detail, tone, walled) in enumerate(cells):
        row, col = divmod(index, 2)
        box = (x_edges[col] + 18, y_edges[row] + 18,
               x_edges[col + 1] - 18, y_edges[row + 1] - 18)
        _panel(plate, box, name, tone, dashed=not walled)
        cx, cy = (box[0] + box[2]) / 2, box[1] + 107
        plate.draw.ellipse((cx - 64, cy - 26, cx + 64, cy + 26),
                           fill=hex_rgba(BLUE_LIGHT, 125), outline=tone,
                           width=5 if walled else 2)
        if row == 1:
            for dx, dy in ((-30, -8), (8, 11), (35, -12)):
                plate.draw.rectangle((cx + dx - 7, cy + dy - 7,
                                     cx + dx + 7, cy + dy + 7), fill=CORAL)
        plate.text((cx, box[3] - 24), detail, size=20, bold=True,
                   fill=_text_tone(tone), anchor="mm")
    plate.draw.rounded_rectangle((100, 742, 1500, 798), radius=19,
                                 fill=hex_rgba(GOLD_LIGHT, 170),
                                 outline=GOLD, width=3)
    plate.text((800, 770),
               "severity: organ failure course | complication: gas, bleeding, vessel injury",
               size=21, bold=True, fill=_text_tone(GOLD), anchor="mm")


def _render_appendicitis(plate: RadiologyPlate,
                         item: Mapping[str, object]) -> None:
    _ = item
    left = _panel(plate, (75, 225, 505, 790), "1  CHOOSE INITIAL TEST", BLUE)
    routes = (("ADULT CONTEXT", "CT often answers", BLUE),
              ("CHILD / US EXPERTISE", "US-first pathway", TEAL),
              ("PREGNANCY", "US or MRI without contrast", PLUM))
    for index, (heading, detail, tone) in enumerate(routes):
        y = left[1] + 15 + index * 125
        plate.draw.rounded_rectangle((left[0] + 10, y, left[2] - 10, y + 96),
                                     radius=17, fill=hex_rgba(PALES[index], 112),
                                     outline=tone, width=3)
        plate.text((left[0] + 29, y + 28), heading, size=19, bold=True,
                   fill=_text_tone(tone))
        plate.text((left[0] + 29, y + 66), detail, size=20, bold=True,
                   fill=INK)
    plate.text(((left[0] + left[2]) / 2, left[3] - 26),
               "patient + resources matter", size=20, bold=True,
               fill=INK_SOFT, anchor="mm")

    middle = _panel(plate, (545, 225, 1080, 790), "2  COMBINE SIGNS", TEAL)
    cx, cy = (middle[0] + middle[2]) / 2, middle[1] + 170
    plate.draw.arc((cx - 115, cy - 105, cx + 115, cy + 105),
                   0, 360, fill=TEAL, width=26)
    plate.draw.arc((cx - 92, cy - 82, cx + 92, cy + 82),
                   0, 360, fill=PAPER_LIGHT, width=12)
    _measure(plate, (cx - 115, cy), (cx + 115, cy), "outer diameter", BLUE,
             label_at=(cx, cy - 41))
    signs = (("noncompressible", "[A]"), ("wall / hyperaemia", "[B]"),
             ("fat + focal tenderness", "[C]"))
    for index, (label, code) in enumerate(signs):
        y = middle[1] + 285 + index * 52
        plate.text((middle[0] + 25, y), code, size=20, bold=True,
                   fill=_text_tone(TEAL), anchor="lm")
        plate.text((middle[0] + 78, y), label, size=20, bold=True,
                   fill=INK, anchor="lm")
    plate.text((cx, middle[3] - 27), "diameter alone is not the diagnosis",
               size=20, bold=True, fill=CORAL, anchor="mm")

    right = _panel(plate, (1120, 225, 1525, 790), "3  COMPLICATION", CORAL)
    for index, (label, symbol) in enumerate((("collection", "ring"),
                                             ("extraluminal gas", "dots"),
                                             ("wall defect", "gap"))):
        y = right[1] + 36 + index * 125
        if symbol == "ring":
            plate.draw.ellipse((right[0] + 20, y, right[0] + 82, y + 62),
                               fill=hex_rgba(CORAL_LIGHT, 120),
                               outline=CORAL, width=4)
        elif symbol == "dots":
            for dx, dy in ((30, 17), (55, 9), (67, 41)):
                plate.dot((right[0] + dx, y + dy), 6, fill=CORAL,
                          outline=CORAL, width=1)
        else:
            plate.draw.line((right[0] + 18, y + 31, right[0] + 43, y + 31),
                            fill=CORAL, width=10)
            plate.draw.line((right[0] + 63, y + 31, right[0] + 88, y + 31),
                            fill=CORAL, width=10)
        plate.text((right[0] + 110, y + 31), label, size=20, bold=True,
                   fill=INK, anchor="lm")
    _tag(plate, ((right[0] + right[2]) / 2, right[3] - 45),
         "URGENT ROUTE", CORAL, size=21)


def _render_biliary(plate: RadiologyPlate,
                     item: Mapping[str, object]) -> None:
    _ = item
    _tag(plate, (800, 205), "DUCT MAP: LEVEL -> CAUSE -> INFLAMMATION", TEAL)
    _duct_tree(plate, (760, 475), 1.15, TEAL)
    # Gallbladder and a labelled stone sit beside, not inside, the duct tree.
    plate.draw.ellipse((505, 430, 665, 625),
                       fill=hex_rgba(GREEN_LIGHT, 130), outline=GREEN, width=5)
    plate.draw.line((625, 440, 706, 386), fill=GREEN, width=8)
    plate.dot((570, 558), 17, fill=GOLD, outline=INK, width=3)
    _tag(plate, (565, 666), "STONE + DISTENSION", GREEN, size=20)

    plate.draw.line((760, 348, 760, 595), fill=TEAL, width=11)
    plate.draw.line((760, 516, 842, 516), fill=TEAL, width=8)
    plate.dot((760, 520), 16, fill=CORAL, outline=INK, width=3)
    _tag(plate, (930, 516), "OBSTRUCTION LEVEL", CORAL, size=20)
    for y, width in ((322, 185), (357, 150), (392, 116)):
        plate.draw.arc((760 - width, y - 28, 760 + width, y + 28),
                       200, 340, fill=BLUE, width=4)
    plate.text((760, 275), "upstream ducts dilate", size=21, bold=True,
               fill=_text_tone(BLUE), anchor="mm")

    left = _panel(plate, (80, 255, 390, 735), "FIRST BRANCH", BLUE)
    _note(plate, (left[0] + 5, left[1] + 5, left[2] - 5, left[1] + 120),
          "Ultrasound: stones, duct calibre, distension and focal tenderness.",
          size=21, bold=True)
    _arrow(plate, (390, 470), (490, 470), "US", BLUE)
    right = _panel(plate, (1125, 255, 1520, 735), "WALL THICKENING", CORAL)
    conditions = (("distension", "D"), ("stone", "S"),
                  ("surrounding change", "P"), ("tenderness", "T"))
    for index, (label, code) in enumerate(conditions):
        y = right[1] + 25 + index * 67
        plate.draw.rectangle((right[0] + 12, y - 17,
                             right[0] + 46, y + 17), outline=CORAL, width=4)
        plate.text((right[0] + 29, y), code, size=18, bold=True,
                   fill=CORAL, anchor="mm")
        plate.text((right[0] + 65, y), label, size=20, bold=True,
                   fill=INK, anchor="lm")
    plate.text(((right[0] + right[2]) / 2, right[3] - 30),
               "one sign alone is nonspecific", size=20, bold=True,
               fill=CORAL, anchor="mm")


def _vessel_bowel(plate: RadiologyPlate, box: Box, tone: str,
                  *, inflow: bool, outflow: bool, closed: bool = False) -> None:
    x0, y0, x1, y1 = box
    cx = (x0 + x1) / 2
    plate.draw.ellipse((cx - 96, y0 + 63, cx + 96, y0 + 192),
                       fill=hex_rgba(PAPER_LIGHT, 200), outline=tone, width=16)
    plate.draw.ellipse((cx - 72, y0 + 84, cx + 72, y0 + 171),
                       fill=PAPER_LIGHT, outline=GRID, width=2)
    # Incoming artery and outgoing vein use different line patterns and labels.
    plate.arrow((x0 + 32, y0 + 127), (cx - 102, y0 + 127),
                fill=CORAL, width=8, head=17)
    plate.arrow((cx + 102, y0 + 127), (x1 - 32, y0 + 127),
                fill=BLUE, width=8, head=17)
    if not inflow:
        _cross(plate, (x0 + 88, y0 + 127), CORAL, scale=.8)
    if not outflow:
        _cross(plate, (x1 - 88, y0 + 127), BLUE, scale=.8)
        _hatch(plate, (cx - 85, y0 + 73, cx + 85, y0 + 181), BLUE, spacing=18)
    if closed:
        plate.draw.arc((cx - 118, y0 + 35, cx + 118, y0 + 220),
                       20, 340, fill=PLUM, width=7)
        plate.draw.line((cx - 84, y0 + 50, cx - 55, y0 + 83),
                        fill=PLUM, width=6)
        plate.draw.line((cx + 84, y0 + 50, cx + 55, y0 + 83),
                        fill=PLUM, width=6)


def _render_bowel_ischaemia(plate: RadiologyPlate,
                            item: Mapping[str, object]) -> None:
    _ = item
    boxes = ((65, 230, 550, 765), (575, 230, 1060, 765),
             (1085, 230, 1535, 765))
    titles = (("ARTERIAL: INFLOW", CORAL, False, True, False),
              ("VENOUS: OUTFLOW", BLUE, True, False, False),
              ("STRANGULATION", PLUM, False, False, True))
    details = (("arterial occlusion", "reduced wall enhancement"),
               ("venous clot", "congestion + oedema"),
               ("closed-loop geometry", "both flows threatened"))
    for index, (box, config, detail) in enumerate(zip(boxes, titles, details)):
        title, tone, inflow, outflow, closed = config
        inner = _panel(plate, box, title, tone)
        _vessel_bowel(plate, (inner[0], inner[1] + 15,
                             inner[2], inner[1] + 250), tone,
                      inflow=inflow, outflow=outflow, closed=closed)
        for row, value in enumerate(detail):
            plate.text(((inner[0] + inner[2]) / 2, inner[1] + 315 + row * 45),
                       value, size=21, bold=True,
                       fill=_text_tone(tone) if row == 0 else INK,
                       anchor="mm")
        action = "urgent viability decision" if index == 2 else "mechanism changes pattern"
        _tag(plate, ((inner[0] + inner[2]) / 2, inner[3] - 38),
             action.upper(), tone, size=19)


def _render_bowel_obstruction(plate: RadiologyPlate,
                              item: Mapping[str, object]) -> None:
    _ = item
    _tag(plate, (800, 205), "MECHANICAL OBSTRUCTION: FOLLOW THE CALIBRE", BLUE)
    # A single bowel path makes upstream/downstream and the transition explicit.
    upstream = ((115, 620), (680, 620), (680, 520), (135, 520),
                (135, 350), (660, 350), (750, 445))
    plate.draw.line(upstream, fill=BLUE, width=60, joint="curve")
    plate.draw.line(upstream, fill=BLUE_LIGHT, width=40, joint="curve")
    plate.text((360, 255), "DILATED UPSTREAM", size=22, bold=True,
               fill=_text_tone(BLUE), anchor="mm")
    plate.draw.polygon(((732, 463), (768, 427), (805, 440), (805, 450)),
                       fill=BLUE, outline=BLUE)
    _arrow(plate, (800, 380), (784, 439), tone=CORAL)
    _tag(plate, (800, 350), "TRANSITION POINT", CORAL, size=21)
    plate.draw.line((805, 445, 1465, 445), fill=TEAL, width=11)
    plate.text((1245, 405), "COLLAPSED DISTAL", size=22, bold=True,
               fill=_text_tone(TEAL), anchor="mm")

    causes = (("adhesion", "line"), ("hernia", "gate"),
              ("mass", "dot"), ("twist", "cross"))
    for index, (label, mark) in enumerate(causes):
        x = 870 + index * 175
        plate.draw.rounded_rectangle((x - 72, 535, x + 72, 650), radius=18,
                                     fill=hex_rgba(GOLD_LIGHT, 105),
                                     outline=GOLD, width=3)
        if mark == "line":
            plate.draw.line((x - 27, 575, x + 27, 610), fill=GOLD, width=6)
        elif mark == "gate":
            plate.draw.arc((x - 34, 566, x + 34, 624), 180, 360,
                           fill=GOLD, width=6)
        elif mark == "dot":
            plate.dot((x, 593), 21, fill=CORAL, outline=INK, width=3)
        else:
            plate.draw.arc((x - 33, 567, x + 33, 621), 20, 340,
                           fill=PLUM, width=6)
        plate.text((x, 630), label, size=19, bold=True,
                   fill=_text_tone(GOLD), anchor="mm")
    plate.draw.rounded_rectangle((245, 705, 1355, 790), radius=22,
                                 fill=hex_rgba(CORAL_LIGHT, 120),
                                 outline=CORAL, width=4)
    plate.text((800, 735), "VIABILITY CHECK", size=21, bold=True,
               fill=_text_tone(CORAL), anchor="mm")
    plate.text((800, 770), "closed loop | oedema | reduced enhancement -> higher urgency",
               size=21, bold=True, fill=INK, anchor="mm")


def _render_abdominal_trauma(plate: RadiologyPlate,
                             item: Mapping[str, object]) -> None:
    _ = item
    left = _panel(plate, (65, 225, 525, 785), "1  CONTRAST PHASES", BLUE)
    plate.arrow((left[0] + 25, left[1] + 110),
                (left[2] - 25, left[1] + 110), fill=INK_SOFT,
                width=4, head=14)
    for x, title, tone, detail in ((left[0] + 105, "ARTERIAL", CORAL,
                                    "active arterial focus"),
                                   (left[2] - 105, "PORTAL", TEAL,
                                    "organ + venous injury")):
        plate.draw.line((x, left[1] + 74, x, left[1] + 150),
                        fill=tone, width=5)
        _tag(plate, (x, left[1] + 188), title, tone, size=20)
        _note(plate, (x - 90, left[1] + 225, x + 90, left[1] + 335),
              detail, size=20, bold=True)
    _note(plate, (left[0] + 35, left[3] - 82,
                  left[2] - 35, left[3] - 20),
          "phases answer different bleeding questions", size=19,
          tone=INK_SOFT, bold=True)

    middle = _panel(plate, (555, 225, 1045, 785), "2  DESCRIBE ORGAN INJURY", CORAL)
    _liver(plate, (middle[0] + 70, middle[1] + 30,
                   middle[2] - 70, middle[1] + 280), CORAL)
    surface = (middle[2] - 160, middle[1] + 280)
    tip = (720, 410)
    plate.draw.line((tip, surface), fill=PAPER_LIGHT, width=28)
    plate.draw.line((tip, surface), fill=PLUM, width=7)
    _measure(plate, tip, surface, "depth", PLUM,
             label_at=(720, 545))
    plate.draw.line((830, 365, 830, 640), fill=BLUE, width=9)
    crossing_y = tip[1] + (830 - tip[0]) * (surface[1] - tip[1]) / (surface[0] - tip[0])
    plate.dot((830, crossing_y), 16, fill=GOLD, outline=INK, width=3)
    plate.text((805, 664), "vessel involvement", size=20, bold=True,
               fill=_text_tone(BLUE), anchor="mm")
    _note(plate, (middle[0] + 35, middle[3] - 88,
                  middle[2] - 35, middle[3] - 18),
          "grade communicates pattern; it does not replace physiology",
          size=18, tone=INK_SOFT, bold=True)

    right = _panel(plate, (1075, 225, 1535, 785), "3  ROUTE CARE", PLUM)
    gates = (("active extravasation", CORAL), ("haemodynamic state", GOLD),
             ("hollow-viscus signs", TEAL))
    for index, (label, tone) in enumerate(gates):
        y = right[1] + 20 + index * 105
        _check(plate, (right[0] + 48, y + 34), tone, scale=.7)
        plate.text((right[0] + 87, y + 34), label, size=20,
                   bold=True, fill=INK, anchor="lm")
    _arrow(plate, ((right[0] + right[2]) / 2, right[1] + 355),
           ((right[0] + right[2]) / 2, right[1] + 405), tone=PLUM)
    _tag(plate, ((right[0] + right[2]) / 2, right[3] - 58),
         "OBSERVE / IR / SURGERY", PLUM, size=19)


def _render_ibd(plate: RadiologyPlate,
                item: Mapping[str, object]) -> None:
    _ = item
    _tag(plate, (800, 205), "CROHN STRICTURE: MIXED COMPONENTS", PLUM)
    # Central wall layers deliberately overlap inflammatory and fibrotic cues.
    plate.draw.rounded_rectangle((320, 300, 1280, 570), radius=110,
                                 fill=hex_rgba(PAPER_LIGHT, 230),
                                 outline=INK_SOFT, width=4)
    plate.draw.rounded_rectangle((385, 345, 1215, 525), radius=80,
                                 fill=hex_rgba(CORAL_LIGHT, 145),
                                 outline=CORAL, width=8)
    plate.draw.rounded_rectangle((510, 385, 1090, 485), radius=48,
                                 fill=hex_rgba(PLUM_LIGHT, 155),
                                 outline=PLUM, width=11)
    # Patent lumen narrows through the thickened segment and opens at both
    # ends; a closed oval incorrectly suggests a sealed cyst or total block.
    lumen = ((320, 370), (430, 383), (650, 408), (950, 408),
             (1160, 400), (1280, 390), (1280, 480), (1160, 470),
             (950, 462), (650, 462), (430, 487), (320, 500))
    plate.draw.polygon(lumen, fill=PAPER_LIGHT)
    plate.draw.line(lumen[:6], fill=INK, width=3)
    plate.draw.line(lumen[6:], fill=INK, width=3)
    _tag(plate, (535, 330), "OEDEMA + ENHANCEMENT", CORAL, size=19)
    _tag(plate, (1060, 552), "FIXED NARROWING", PLUM, size=19)
    plate.arrow((170, 435), (300, 435), fill=BLUE, width=12, head=20)
    plate.arrow((1300, 435), (1430, 435), fill=BLUE, width=6, head=17)
    plate.text((210, 390), "upstream", size=20, bold=True,
               fill=_text_tone(BLUE), anchor="mm")
    plate.text((1390, 390), "downstream", size=20, bold=True,
               fill=_text_tone(BLUE), anchor="mm")

    plate.draw.rounded_rectangle((105, 625, 750, 790), radius=22,
                                 fill=hex_rgba(GOLD_LIGHT, 135),
                                 outline=GOLD, width=4)
    plate.text((427, 660), "IMAGING LIMIT", size=22, bold=True,
               fill=_text_tone(GOLD), anchor="mm")
    plate.text((427, 711), "detect stricture + inflammatory component",
               size=21, bold=True, fill=INK, anchor="mm")
    plate.text((427, 755), "cannot accurately quantify fibrosis",
               size=21, bold=True, fill=CORAL, anchor="mm")

    plate.draw.rounded_rectangle((805, 625, 1495, 790), radius=22,
                                 fill=hex_rgba(TEAL_LIGHT, 115),
                                 outline=TEAL, width=4)
    plate.text((1150, 660), "COMPLICATION MAP", size=22, bold=True,
               fill=_text_tone(TEAL), anchor="mm")
    for index, label in enumerate(("fistula", "abscess", "upstream dilatation")):
        x = 925 + index * 225
        plate.dot((x, 714), 18, fill=PAPER_LIGHT, outline=TEAL, width=5)
        plate.text((x, 760), label, size=19, bold=True,
                   fill=INK, anchor="mm")


def _render_pancreas_tumour(plate: RadiologyPlate,
                            item: Mapping[str, object]) -> None:
    _ = item
    _tag(plate, (800, 205), "PANCREAS PROTOCOL + VESSEL MAP", GOLD)
    # Phase strip.
    for index, (title, tone, purpose) in enumerate((
            ("PANCREATIC", CORAL, "tumour conspicuity"),
            ("PORTAL", TEAL, "veins + liver"),
            ("REFORMATS", BLUE, "arterial anatomy"))):
        x0 = 85 + index * 315
        plate.draw.rounded_rectangle((x0, 245, x0 + 280, 345), radius=18,
                                     fill=hex_rgba(PALES[index], 120),
                                     outline=tone, width=3)
        plate.text((x0 + 140, 278), title, size=20, bold=True,
                   fill=_text_tone(tone), anchor="mm")
        plate.text((x0 + 140, 319), purpose, size=19, bold=True,
                   fill=INK, anchor="mm")
    _arrow(plate, (365, 295), (389, 295), tone=GOLD, width=4)
    _arrow(plate, (680, 295), (704, 295), tone=GOLD, width=4)

    _pancreas(plate, (705, 520), GOLD, scale=1.25)
    plate.draw.line((520, 565, 910, 565), fill=BLUE, width=16)
    plate.draw.line((690, 345, 690, 700), fill=CORAL, width=15)
    plate.dot((745, 500), 46, fill=hex_rgba(PLUM, 205), outline=INK, width=4)
    plate.draw.arc((665, 420, 825, 580), 205, 520, fill=PLUM, width=8)
    _tag(plate, (705, 740), "REPORT CONTACT + CONTOUR + PATENCY", PLUM, size=19)
    plate.text((505, 610), "vein", size=20, bold=True,
               fill=_text_tone(BLUE), anchor="mm")
    plate.text((650, 365), "artery", size=20, bold=True,
               fill=_text_tone(CORAL), anchor="mm")

    right = _panel(plate, (1010, 245, 1515, 785), "LESION TRIAGE", TEAL)
    lesion_types = (("hypovascular solid", "SOLID", CORAL),
                    ("cystic pathway", "CYST", BLUE),
                    ("hypervascular", "VASC", GOLD))
    for index, (label, code, tone) in enumerate(lesion_types):
        y = right[1] + 25 + index * 105
        plate.draw.ellipse((right[0] + 18, y, right[0] + 82, y + 64),
                           fill=hex_rgba(PALES[(index + 2) % len(PALES)], 150),
                           outline=tone, width=4)
        plate.text((right[0] + 50, y + 32), code, size=16, bold=True,
                   fill=_text_tone(tone), anchor="mm")
        plate.text((right[0] + 105, y + 32), label, size=20, bold=True,
                   fill=INK, anchor="lm")
    plate.draw.line((right[0] + 35, right[1] + 365,
                     right[2] - 35, right[1] + 365), fill=GRID, width=3)
    _note(plate, (right[0] + 12, right[1] + 378,
                  right[2] - 12, right[3] - 6),
          "Imaging maps extent; resectability is a multidisciplinary decision.",
          size=18, bold=True)


def _render_peritoneum(plate: RadiologyPlate,
                       item: Mapping[str, object]) -> None:
    _ = item
    _tag(plate, (800, 205), "PERITONEAL ROUTES: SPACES SHAPE SPREAD", TEAL)
    # Central abdomen with labelled recesses and gravity arrows.
    plate.draw.rounded_rectangle((500, 245, 1100, 745), radius=150,
                                 fill=hex_rgba(GOLD_LIGHT, 55),
                                 outline=INK_SOFT, width=5)
    plate.draw.arc((560, 285, 1040, 420), 190, 350, fill=BLUE, width=9)
    plate.draw.line((610, 385, 610, 650), fill=TEAL, width=10)
    plate.draw.line((990, 385, 990, 650), fill=TEAL, width=10)
    plate.draw.arc((650, 585, 950, 705), 0, 180, fill=CORAL, width=10)
    for x, y, label, tone in ((800, 330, "subphrenic", BLUE),
                              (610, 505, "paracolic", TEAL),
                              (990, 505, "paracolic", TEAL),
                              (800, 660, "pelvic recess", CORAL)):
        plate.dot((x, y), 12, fill=PAPER_LIGHT, outline=tone, width=4)
        plate.text((x, y + 31), label, size=18, bold=True,
                   fill=_text_tone(tone), anchor="mm")
    _arrow(plate, (800, 375), (800, 610), "gravity / communication",
           TEAL, label_at=(800, 505))

    left = _panel(plate, (70, 270, 425, 735), "SURFACE SIGNS", BLUE)
    for index, (label, mark) in enumerate((("nodules", "dots"),
                                           ("omental cake", "bar"),
                                           ("ascites", "wave"))):
        y = left[1] + 30 + index * 105
        if mark == "dots":
            for dx in (0, 22, 44):
                plate.dot((left[0] + 35 + dx, y), 6, fill=BLUE,
                          outline=BLUE, width=1)
        elif mark == "bar":
            plate.draw.rounded_rectangle((left[0] + 12, y - 12,
                                          left[0] + 92, y + 12), radius=8,
                                         fill=BLUE)
        else:
            plate.draw.arc((left[0] + 10, y - 25,
                            left[0] + 92, y + 25), 190, 350,
                           fill=BLUE, width=5)
        plate.text((left[0] + 112, y), label, size=20, bold=True,
                   fill=INK, anchor="lm")
    plate.text(((left[0] + left[2]) / 2, left[3] - 33),
               "distribution supports inference", size=19,
               bold=True, fill=INK_SOFT, anchor="mm")

    right = _panel(plate, (1175, 270, 1530, 735), "ABDOMINAL WALL", CORAL)
    hx, wall_y = (right[0] + right[2]) / 2, right[1] + 175
    # Bowel protrudes through a visible wall defect, rather than floating
    # beneath an unrelated arch.
    plate.draw.line((right[0] + 35, wall_y, hx - 45, wall_y),
                    fill=CORAL, width=13)
    plate.draw.line((hx + 45, wall_y, right[2] - 35, wall_y),
                    fill=CORAL, width=13)
    bowel = ((hx - 88, wall_y - 82), (hx - 25, wall_y - 30),
             (hx - 25, wall_y + 30), (hx - 56, wall_y + 75),
             (hx - 36, wall_y + 114), (hx + 36, wall_y + 114),
             (hx + 56, wall_y + 75), (hx + 25, wall_y + 30),
             (hx + 25, wall_y - 30), (hx + 88, wall_y - 82))
    plate.draw.line(bowel, fill=PLUM, width=17, joint="curve")
    plate.draw.line(bowel, fill=PLUM_LIGHT, width=8, joint="curve")
    plate.text((hx, wall_y - 110), "wall defect + bowel loop", size=16,
               fill=INK_SOFT, anchor="mm")
    _tag(plate, ((right[0] + right[2]) / 2, right[1] + 350),
         "HERNIA CONTENT", CORAL, size=19)
    plate.text(((right[0] + right[2]) / 2, right[3] - 35),
               "bowel viability sets urgency", size=19,
               bold=True, fill=INK, anchor="mm")


def _render_rectal_mr(plate: RadiologyPlate,
                      item: Mapping[str, object]) -> None:
    _ = item
    left = _panel(plate, (65, 225, 965, 790), "RECTAL CANCER: SURGICAL PLANES", PLUM)
    cx, cy = 500, 495
    # Axial rectum, mesorectum and mesorectal fascia.
    plate.draw.ellipse((cx - 245, cy - 190, cx + 245, cy + 190),
                       fill=hex_rgba(GOLD_LIGHT, 70), outline=PLUM, width=6)
    plate.draw.ellipse((cx - 155, cy - 125, cx + 155, cy + 125),
                       fill=hex_rgba(TEAL_LIGHT, 90), outline=TEAL, width=6)
    plate.draw.ellipse((cx - 64, cy - 83, cx + 64, cy + 83),
                       fill=PAPER_LIGHT, outline=INK_SOFT, width=8)
    plate.draw.pieslice((cx - 91, cy - 109, cx + 91, cy + 109),
                        285, 355, fill=hex_rgba(CORAL, 210), outline=CORAL)
    _tag(plate, (360, 337), "MRF", PLUM, size=19)
    _tag(plate, (310, 408), "MESORECTUM", TEAL, size=18)
    _tag(plate, (705, 405), "TUMOUR", CORAL, size=19)
    # Measure the shortest gap from the actual outer tumour arc to fascia.
    tumour_edge = [(cx + 91 * math.cos(math.radians(a)),
                    cy + 109 * math.sin(math.radians(a))) for a in range(285, 356)]
    fascia = [(cx + 245 * math.cos(math.radians(a)),
               cy + 190 * math.sin(math.radians(a))) for a in range(360)]
    edge, margin = min(((t, f) for t in tumour_edge for f in fascia),
                       key=lambda pair: math.dist(*pair))
    _measure(plate, edge, margin, "MRF distance", PLUM,
             label_at=(650, 351))
    # Along the rightward near-horizontal edge, start at the muscular wall,
    # not at the mesorectal compartment outline.
    angle = math.radians(355)
    wall_radius = 1 / math.sqrt((math.cos(angle) / 64) ** 2 +
                               (math.sin(angle) / 83) ** 2)
    tumour_radius = 1 / math.sqrt((math.cos(angle) / 91) ** 2 +
                                 (math.sin(angle) / 109) ** 2)
    wall = (cx + wall_radius * math.cos(angle), cy + wall_radius * math.sin(angle))
    outer = (cx + tumour_radius * math.cos(angle), cy + tumour_radius * math.sin(angle))
    _measure(plate, wall, outer, "extramural depth", CORAL,
             label_at=(670, 570))
    plate.draw.line((outer, (617, 549)), fill=CORAL, width=2)
    plate.text((500, 718), "also report nodes + extramural venous invasion",
               size=20, bold=True, fill=INK_SOFT, anchor="mm")

    right = _panel(plate, (995, 225, 1535, 790), "FISTULA: CLOCK + LAYERS", TEAL)
    fx, fy = 1265, 470
    for radius, tone in ((155, PLUM), (105, TEAL), (58, INK_SOFT)):
        plate.draw.ellipse((fx - radius, fy - radius,
                            fx + radius, fy + radius),
                           outline=tone, width=7)
    plate.text((fx, fy - 178), "12", size=20, bold=True,
               fill=INK_SOFT, anchor="mm")
    plate.text((fx + 178, fy), "3", size=20, bold=True,
               fill=INK_SOFT, anchor="mm")
    plate.dot((fx - 51, fy - 27), 13, fill=CORAL, outline=INK, width=3)
    plate.polyline(((fx - 51, fy - 27), (fx - 130, fy - 85),
                    (fx - 174, fy - 25)), fill=CORAL, width=8)
    plate.draw.ellipse((fx - 215, fy - 70, fx - 163, fy - 18),
                       fill=hex_rgba(CORAL_LIGHT, 190), outline=CORAL, width=4)
    plate.text((fx, 684), "opening | sphincter relation | abscess",
               size=19, bold=True, fill=INK, anchor="mm")
    _tag(plate, (fx, 742), "ONE OPERATIVE MAP", TEAL, size=20)


def _render_acute_abdomen(plate: RadiologyPlate,
                          item: Mapping[str, object]) -> None:
    _ = item
    _tag(plate, (800, 205), "ACUTE CT SEARCH: THREE ORGANISING QUESTIONS", PLUM)
    boxes = ((65, 245, 550, 775), (575, 245, 1060, 775),
             (1085, 245, 1535, 775))
    titles = (("FREE GAS", CORAL), ("CALIBRE CHANGE", BLUE),
              ("EPICENTRE", TEAL))
    for box, (title, tone) in zip(boxes, titles):
        _panel(plate, box, title, tone)

    # Perforation: free bubbles must be related to the nearest diseased viscus.
    for x, y, radius in ((190, 390, 8), (230, 355, 6), (280, 410, 10)):
        plate.dot((x, y), radius, fill=CORAL, outline=CORAL, width=1)
    _bowel_loop(plate, (150, 435, 460, 610), CORAL, width=12)
    _arrow(plate, (270, 410), (300, 474), "nearest source", CORAL,
           label_at=(360, 415))
    plate.text((307, 690), "extraluminal gas + diseased viscus",
               size=20, bold=True, fill=INK, anchor="mm")

    # Mechanical obstruction versus diffuse ileus.
    plate.draw.line((630, 465, 820, 465), fill=BLUE, width=24)
    plate.draw.polygon(((835, 465), (875, 425), (875, 505)), fill=CORAL)
    plate.draw.line((885, 465, 1000, 465), fill=TEAL, width=9)
    plate.text((725, 420), "wide", size=20, bold=True,
               fill=_text_tone(BLUE), anchor="mm")
    plate.text((945, 420), "collapsed", size=20, bold=True,
               fill=_text_tone(TEAL), anchor="mm")
    _tag(plate, (817, 575), "TRANSITION", CORAL, size=20)
    plate.text((817, 690), "focal change -> mechanical pathway",
               size=20, bold=True, fill=INK, anchor="mm")

    # Inflammation: intensity rings center on an organ rather than a free dot.
    for radius, alpha in ((120, 45), (80, 80), (42, 145)):
        plate.draw.ellipse((1310 - radius, 480 - radius,
                            1310 + radius, 480 + radius),
                           fill=hex_rgba(TEAL, alpha), outline=TEAL,
                           width=3)
    plate.dot((1310, 480), 18, fill=CORAL, outline=INK, width=3)
    plate.text((1310, 640), "centre on the organ with",
               size=20, bold=True, fill=INK, anchor="mm")
    plate.text((1310, 680), "the strongest local signs",
               size=20, bold=True, fill=_text_tone(TEAL), anchor="mm")


def _render_liver(plate: RadiologyPlate,
                  item: Mapping[str, object]) -> None:
    _ = item
    _tag(plate, (800, 205), "LIVER LESION: CHANGE ACROSS MATCHED PHASES", CORAL)
    phases = (("UNENHANCED", BLUE, .34), ("ARTERIAL", CORAL, .86),
              ("PORTAL / DELAYED", TEAL, .52))
    for index, (name, tone, intensity) in enumerate(phases):
        x = 245 + index * 430
        _panel(plate, (75 + index * 430, 250,
                       415 + index * 430, 600), name, tone)
        _liver(plate, (x - 115, 350, x + 115, 520), tone)
        value = int(40 + intensity * 170)
        plate.draw.ellipse((x + 18, 399, x + 82, 463),
                           fill=(value, value, value, 255),
                           outline=tone, width=5)
        plate.text((x, 559), ("baseline tissue" if index == 0 else
                              "relative uptake" if index == 1 else
                              "relative washout"),
                   size=20, bold=True, fill=_text_tone(tone), anchor="mm")
        if index < 2:
            _arrow(plate, (415 + index * 430, 425),
                   (490 + index * 430, 425), tone=GOLD)

    plate.draw.rounded_rectangle((100, 645, 1500, 790), radius=22,
                                 fill=hex_rgba(PLUM_LIGHT, 105),
                                 outline=PLUM, width=4)
    plate.text((260, 688), "CONTEXT GATE", size=21, bold=True,
               fill=_text_tone(PLUM), anchor="mm")
    _check(plate, (445, 690), PLUM, scale=.75)
    plate.text((485, 690), "LI-RADS-eligible risk population?", size=21,
               bold=True, fill=INK, anchor="lm")
    plate.text((1040, 690), "ancillary features + comparison",
               size=21, bold=True, fill=INK, anchor="lm")
    plate.text((800, 752), "a phase pattern is interpreted inside the applicable clinical system",
               size=21, bold=True, fill=_text_tone(PLUM), anchor="mm")


def _render_kidney(plate: RadiologyPlate,
                   item: Mapping[str, object]) -> None:
    _ = item
    left = _panel(plate, (65, 225, 550, 790), "1  TRUE ENHANCEMENT", BLUE,
                  subtitle="matched region, matched phase")
    for x, label, grey in ((left[0] + 120, "PRE", 115),
                           (left[2] - 120, "POST", 175)):
        _kidney(plate, (x, left[1] + 155), BLUE, scale=.72)
        plate.draw.ellipse((x - 25, left[1] + 120,
                            x + 25, left[1] + 170),
                           fill=(grey, grey, grey, 255), outline=PLUM, width=4)
        plate.text((x, left[1] + 265), label, size=20, bold=True,
                   fill=_text_tone(BLUE), anchor="mm")
    _arrow(plate, (left[0] + 210, left[1] + 155),
           (left[2] - 210, left[1] + 155), "compare ROI", PLUM,
           label_at=((left[0] + left[2]) / 2, left[1] + 105))
    _note(plate, (left[0] + 34, left[1] + 320,
                  left[2] - 34, left[1] + 400),
          "compare baseline; apparent enhancement can still be artefactual",
          size=19, bold=True)

    right = _panel(plate, (585, 225, 1535, 790), "2  CYSTIC MASS FEATURES -> BOSNIAK", TEAL)
    features = (("WALL", "thin / thick / irregular", "ring"),
                ("SEPTA", "number + thickness + enhancement", "septa"),
                ("NODULE", "enhancing convex tissue", "nodule"))
    for index, (title, detail, kind) in enumerate(features):
        x = right[0] + 145 + index * 290
        y = right[1] + 170
        plate.draw.ellipse((x - 83, y - 83, x + 83, y + 83),
                           fill=hex_rgba(BLUE_LIGHT, 95),
                           outline=TEAL, width=5 if kind == "ring" else 3)
        if kind == "septa":
            for angle in (-35, 20, 65):
                radians = math.radians(angle)
                plate.draw.line((x - 70 * math.cos(radians),
                                 y - 70 * math.sin(radians),
                                 x + 70 * math.cos(radians),
                                 y + 70 * math.sin(radians)),
                                fill=PLUM, width=5)
        elif kind == "nodule":
            plate.draw.ellipse((x + 35, y - 19, x + 83, y + 31),
                               fill=CORAL, outline=INK, width=3)
        plate.text((x, right[1] + 282), title, size=21, bold=True,
                   fill=_text_tone(TEAL), anchor="mm")
        _note(plate, (x - 125, right[1] + 308, x + 125, right[1] + 400),
              detail, size=19, bold=True)
    _arrow(plate, (right[0] + 80, right[1] + 438),
           (right[2] - 80, right[1] + 438), tone=GOLD)
    _tag(plate, ((right[0] + right[2]) / 2, right[3] - 43),
         "CATEGORY INFORMS CARE WITH CLINICAL CONTEXT", PLUM, size=19)


def _render_scrotum(plate: RadiologyPlate,
                    item: Mapping[str, object]) -> None:
    _ = item
    left = _panel(plate, (65, 225, 650, 790), "ACUTE PAIN: COMPARE PERFUSION", CORAL)
    for index, (x, label, flowing) in enumerate(((left[0] + 155, "SIDE A", True),
                                                 (left[2] - 155, "SIDE B", False))):
        plate.draw.ellipse((x - 88, left[1] + 80, x + 88, left[1] + 285),
                           fill=hex_rgba(GOLD_LIGHT, 105), outline=GOLD, width=5)
        if flowing:
            for row in range(4):
                yy = left[1] + 120 + row * 41
                plate.arrow((x - 48, yy), (x + 48, yy), fill=TEAL,
                            width=4, head=12)
        else:
            for row in range(4):
                yy = left[1] + 120 + row * 41
                plate.draw.line((x - 48, yy, x + 48, yy),
                                fill=GRID, width=3)
            _cross(plate, (x, left[1] + 184), CORAL, scale=1.2)
        plate.text((x, left[1] + 330), label, size=20, bold=True,
                   fill=INK, anchor="mm")
        plate.text((x, left[1] + 370),
                   "flow present" if flowing else "reduced / absent flow",
                   size=19, bold=True,
                   fill=_text_tone(TEAL if flowing else CORAL), anchor="mm")
    _tag(plate, ((left[0] + left[2]) / 2, left[3] - 43),
         "TORSION = EMERGENCY PATHWAY", CORAL, size=19)
    plate.text(((left[0] + left[2]) / 2, left[3] - 9),
               "preserved flow does not exclude torsion", size=17,
               bold=True, fill=INK, anchor="mm")

    right = _panel(plate, (685, 225, 1535, 790), "MASS: LOCALISE THEN STAGE", TEAL)
    cx, cy = 970, 450
    plate.draw.ellipse((cx - 120, cy - 145, cx + 120, cy + 145),
                       fill=hex_rgba(GOLD_LIGHT, 90), outline=GOLD, width=5)
    plate.dot((cx + 32, cy - 15), 30, fill=CORAL, outline=INK, width=3)
    plate.draw.ellipse((cx - 150, cy - 175, cx + 150, cy + 175),
                       outline=PLUM, width=4)
    _tag(plate, (970, 650), "INTRA vs EXTRA", PLUM, size=20)
    _arrow(plate, (1125, 455), (1200, 455), tone=GOLD)
    for index, label in enumerate(("US location", "markers", "nodes / spread")):
        y = 350 + index * 105
        plate.draw.rounded_rectangle((1215, y, 1485, y + 72), radius=17,
                                     fill=hex_rgba(PALES[index], 105),
                                     outline=TONES[index], width=3)
        plate.text((1350, y + 36), label, size=20, bold=True,
                   fill=INK, anchor="mm")
    plate.text((1350, 700), "integrated staging -> surgery",
               size=20, bold=True, fill=_text_tone(TEAL), anchor="mm")


def _render_adrenal(plate: RadiologyPlate,
                    item: Mapping[str, object]) -> None:
    _ = item
    boxes = ((65, 230, 550, 780), (575, 230, 1060, 780),
             (1085, 230, 1535, 780))
    inner = _panel(plate, boxes[0], "UNENHANCED CT", BLUE)
    plate.draw.ellipse((inner[0] + 60, inner[1] + 65,
                        inner[2] - 60, inner[1] + 275),
                       fill=hex_rgba(BLUE_LIGHT, 90), outline=BLUE, width=5)
    plate.text(((inner[0] + inner[2]) / 2, inner[1] + 143), "HU", size=40,
               bold=True, fill=_text_tone(BLUE), anchor="mm")
    _tag(plate, ((inner[0] + inner[2]) / 2, inner[1] + 310),
         "HOMOGENEOUS + <=10 HU", GREEN, size=19)
    _note(plate, (inner[0] + 8, inner[1] + 350,
                  inner[2] - 8, inner[3]),
          "Supports a benign lipid-rich adrenal mass in the applicable setting.",
          size=20, bold=True)

    inner = _panel(plate, boxes[1], "CHEMICAL SHIFT MRI", TEAL)
    plate.text((inner[0] + 65, inner[1] + 83), "IN-PHASE", size=19,
               bold=True, fill=INK)
    plate.draw.rounded_rectangle((inner[0] + 65, inner[1] + 113,
                                  inner[2] - 40, inner[1] + 158), radius=15,
                                 fill=hex_rgba(TEAL, 175), outline=TEAL, width=3)
    plate.text((inner[0] + 65, inner[1] + 215), "OPPOSED-PHASE", size=19,
               bold=True, fill=INK)
    plate.draw.rounded_rectangle((inner[0] + 65, inner[1] + 245,
                                  inner[0] + 205, inner[1] + 290), radius=15,
                                 fill=hex_rgba(TEAL, 110), outline=TEAL, width=3)
    _arrow(plate, (inner[2] - 85, inner[1] + 154),
           (inner[2] - 85, inner[1] + 235), "signal loss", TEAL,
           label_at=(inner[2] - 120, inner[1] + 195))
    _note(plate, (inner[0] + 8, inner[1] + 335,
                  inner[2] - 8, inner[3]),
          "Signal drop demonstrates intracellular lipid; absence is not a diagnosis.",
          size=20, bold=True)

    inner = _panel(plate, boxes[2], "WASHOUT: SELECTED CASES", CORAL)
    graph = (inner[0] + 35, inner[1] + 65, inner[2] - 35, inner[1] + 285)
    plate.arrow((graph[0], graph[3]), (graph[2], graph[3]),
                fill=INK_SOFT, width=4, head=13)
    plate.arrow((graph[0], graph[3]), (graph[0], graph[1]),
                fill=INK_SOFT, width=4, head=13)
    curve = []
    for index in range(81):
        t = index / 80
        value = (1 - math.exp(-10 * t)) * math.exp(-1.8 * max(0, t - .22))
        curve.append((graph[0] + t * (graph[2] - graph[0]),
                      graph[3] - value * (graph[3] - graph[1] - 15)))
    plate.polyline(curve, fill=CORAL, width=7)
    plate.text(((graph[0] + graph[2]) / 2, graph[3] + 28),
               "timed enhancement", size=19, bold=True,
               fill=INK_SOFT, anchor="mm")
    _note(plate, (inner[0] + 8, inner[1] + 340,
                  inner[2] - 8, inner[3]),
          "Kinetics help selected indeterminate lesions; they do not settle every diagnosis.",
          size=20, bold=True)


def _render_bladder_virads(plate: RadiologyPlate,
                           item: Mapping[str, object]) -> None:
    _ = item
    _tag(plate, (800, 205), "VI-RADS: DOES TUMOUR INTERRUPT MUSCLE?", PLUM)
    sequences = (("T2 ANATOMY", BLUE, "wall layer"),
                 ("DWI / ADC", CORAL, "restricted focus"),
                 ("EARLY DCE", TEAL, "enhancing focus"))
    for index, (title, tone, detail) in enumerate(sequences):
        x0 = 70 + index * 360
        _panel(plate, (x0, 260, x0 + 325, 690), title, tone)
        cx, cy = x0 + 162, 450
        plate.draw.ellipse((cx - 105, cy - 92, cx + 105, cy + 92),
                           fill=hex_rgba(BLUE_LIGHT, 80),
                           outline=INK_SOFT, width=4)
        for start, end in ((0, 275), (330, 360)):
            plate.draw.arc((cx - 90, cy - 77, cx + 90, cy + 77),
                           start, end, fill=PLUM, width=13)
        plate.draw.pieslice((cx - 89, cy - 78, cx + 89, cy + 78),
                            275, 330, fill=hex_rgba(tone, 195), outline=tone)
        # The muscle discontinuity is at the tumour, not an unrelated slash.
        plate.text((cx, 590), detail, size=20, bold=True,
                   fill=_text_tone(tone), anchor="mm")
    _arrow(plate, (1150, 470), (1235, 470), "combine", GOLD)
    right = _panel(plate, (1240, 260, 1530, 690), "5-POINT SCORE", GOLD)
    likelihood = ("highly unlikely", "unlikely", "equivocal",
                  "likely", "very likely")
    for index in range(5):
        y = right[1] + 30 + index * 56
        plate.draw.rectangle((right[0] + 18, y - 17,
                             right[0] + 52, y + 17),
                            fill=PAPER_LIGHT, outline=GOLD, width=3)
        plate.text((right[0] + 35, y), str(index + 1), size=18,
                   bold=True, fill=_text_tone(GOLD), anchor="mm")
        plate.text((right[0] + 72, y), likelihood[index],
                   size=19, bold=True, fill=INK, anchor="lm")
    plate.draw.rounded_rectangle((160, 725, 1440, 792), radius=21,
                                 fill=hex_rgba(CORAL_LIGHT, 110),
                                 outline=CORAL, width=4)
    plate.text((800, 758),
               "sequence concordance estimates muscle invasion; report extravesical extension separately",
               size=20, bold=True, fill=_text_tone(CORAL), anchor="mm")


def _render_ovarian_orads(plate: RadiologyPlate,
                          item: Mapping[str, object]) -> None:
    _ = item
    _tag(plate, (800, 205), "O-RADS: MORPHOLOGY -> SOLID TISSUE -> ACTION", TEAL)
    # Morphology branches.
    shapes = ((270, "SIMPLE FLUID", "none"),
              (585, "SEPTA", "septa"), (900, "SOLID PART", "solid"))
    for x, label, kind in shapes:
        plate.draw.ellipse((x - 100, 300, x + 100, 500),
                           fill=hex_rgba(BLUE_LIGHT, 85),
                           outline=TEAL, width=5)
        if kind == "septa":
            plate.draw.line((x, 310, x, 490), fill=TEAL, width=5)
            plate.draw.line((x - 85, 400, x + 85, 400), fill=TEAL, width=5)
        elif kind == "solid":
            plate.draw.ellipse((x + 24, 355, x + 94, 425),
                               fill=CORAL, outline=INK, width=3)
        plate.text((x, 545), label, size=20, bold=True,
                   fill=_text_tone(TEAL), anchor="mm")
    plate.text((585, 255), "1  DESCRIBE", size=22, bold=True,
               fill=_text_tone(TEAL), anchor="mm")

    _arrow(plate, (1015, 400), (1090, 400), tone=GOLD)
    tissue = _panel(plate, (1100, 270, 1515, 590), "2  ASSESS SOLID TISSUE", CORAL)
    for index, count in enumerate((0, 1, 2, 4)):
        y = tissue[1] + 16 + index * 45
        plate.text((tissue[0] + 10, y), f"FLOW {index + 1}", size=19,
                   bold=True, fill=INK, anchor="lm")
        for dot in range(count):
            plate.dot((tissue[0] + 165 + dot * 34, y), 8,
                      fill=CORAL, outline=CORAL, width=1)
        if count == 0:
            plate.draw.line((tissue[0] + 165, y,
                             tissue[0] + 260, y), fill=GRID, width=4)
    plate.text(((tissue[0] + tissue[2]) / 2, tissue[3] - 20),
               "MRI can refine an indeterminate lesion",
               size=17, bold=True, fill=INK_SOFT, anchor="mm")

    plate.draw.rounded_rectangle((210, 645, 1390, 790), radius=22,
                                 fill=hex_rgba(PLUM_LIGHT, 105),
                                 outline=PLUM, width=4)
    plate.text((430, 685), "3  CATEGORY", size=21, bold=True,
               fill=_text_tone(PLUM), anchor="mm")
    _arrow(plate, (580, 690), (760, 690), "clinical setting", PLUM)
    plate.text((1040, 685), "FOLLOW / MRI / REFER", size=22,
               bold=True, fill=_text_tone(PLUM), anchor="mm")
    plate.text((800, 752), "category links imaging risk to an appropriate pathway",
               size=20, bold=True, fill=INK, anchor="mm")


def _render_prostate_mri(plate: RadiologyPlate,
                         item: Mapping[str, object]) -> None:
    _ = item
    _tag(plate, (800, 205), "PI-RADS: DOMINANT SEQUENCE DEPENDS ON ZONE", PLUM)
    cx, cy = 500, 480
    plate.draw.ellipse((cx - 270, cy - 215, cx + 270, cy + 215),
                       fill=hex_rgba(BLUE_LIGHT, 80), outline=BLUE, width=6)
    plate.draw.ellipse((cx - 150, cy - 145, cx + 150, cy + 145),
                       fill=hex_rgba(GOLD_LIGHT, 135), outline=GOLD, width=6)
    plate.draw.ellipse((cx - 62, cy - 100, cx + 62, cy + 100),
                       fill=hex_rgba(PAPER_LIGHT, 230), outline=INK_SOFT, width=4)
    plate.dot((cx - 190, cy + 30), 30, fill=CORAL, outline=INK, width=3)
    plate.dot((cx + 82, cy - 18), 30, fill=PLUM, outline=INK, width=3)
    _tag(plate, (300, 690), "PERIPHERAL ZONE", BLUE, size=19)
    _tag(plate, (650, 690), "TRANSITION ZONE", GOLD, size=19)
    plate.text((300, 742), "DWI dominant", size=21, bold=True,
               fill=_text_tone(BLUE), anchor="mm")
    plate.text((650, 742), "T2 dominant", size=21, bold=True,
               fill=_text_tone(GOLD), anchor="mm")

    _arrow(plate, (785, 480), (865, 480), "target", PLUM)
    right = _panel(plate, (875, 250, 1525, 790), "STAGE + BIOPSY MAP", CORAL)
    layers = (("capsule", 375, BLUE), ("extraprostatic extension", 465, CORAL),
              ("seminal vesicles", 555, PLUM), ("lesion coordinates", 645, TEAL))
    for index, (label, y, tone) in enumerate(layers):
        plate.draw.rounded_rectangle((right[0] + 20, y - 31,
                                      right[2] - 20, y + 31), radius=15,
                                     fill=hex_rgba(PALES[index], 105),
                                     outline=tone, width=3)
        plate.text(((right[0] + right[2]) / 2, y), label, size=20,
                   bold=True, fill=INK, anchor="mm")
    plate.text(((right[0] + right[2]) / 2, 727),
               "zone score + extent + map", size=20, bold=True,
               fill=_text_tone(CORAL), anchor="mm")


def _render_uterine_mr(plate: RadiologyPlate,
                       item: Mapping[str, object]) -> None:
    _ = item
    _tag(plate, (800, 205), "UTERINE MRI: PLANES, COMPARTMENTS, FORM", CORAL)
    # Cancer planes: endometrium, myometrium, stroma/parametrium relationship.
    left = _panel(plate, (60, 240, 560, 780), "CANCER PLANES", CORAL)
    cx, cy = 310, 470
    plate.draw.polygon(((cx, cy + 180), (cx - 135, cy + 15),
                        (cx - 105, cy - 145), (cx + 105, cy - 145),
                        (cx + 135, cy + 15)),
                       fill=hex_rgba(CORAL_LIGHT, 100), outline=CORAL)
    plate.draw.polygon(((cx, cy + 125), (cx - 70, cy + 5),
                        (cx - 58, cy - 105), (cx + 58, cy - 105),
                        (cx + 70, cy + 5)), fill=PAPER_LIGHT, outline=PLUM)
    plate.draw.line((cx, cy - 92, cx, cy + 105), fill=TEAL, width=9)
    plate.dot((cx + 57, cy - 10), 30, fill=PLUM, outline=INK, width=3)
    # Inner wall is the straight segment (58,-105)->(70,5); measure
    # invasion from that boundary to the lesion's outer edge at this level.
    inner_wall_x = cx + 58 + 12 * 95 / 110
    _measure(plate, (inner_wall_x, cy - 10), (cx + 87, cy - 10),
             "myometrial depth", PLUM, label_at=(cx, cy + 195))
    plate.text((cx, 720), "stroma | myometrium | parametrium",
               size=19, bold=True, fill=INK, anchor="mm")

    middle = _panel(plate, (590, 240, 1055, 780), "SURGICAL DISEASE MAP", TEAL)
    compartments = (("anterior", 690, 365, BLUE),
                    ("middle", 825, 480, CORAL),
                    ("posterior", 930, 610, PLUM))
    for index, (label, x, y, tone) in enumerate(compartments):
        plate.draw.rounded_rectangle((x - 92, y - 48, x + 92, y + 48),
                                     radius=18, fill=hex_rgba(PALES[index], 120),
                                     outline=tone, width=4)
        plate.text((x, y), label, size=20, bold=True,
                   fill=INK, anchor="mm")
        if index:
            plate.draw.line((compartments[index - 1][1] + 88,
                             compartments[index - 1][2], x - 88, y),
                            fill=TEAL, width=4)
    plate.text((822, 702), "fibroids + deep endometriosis",
               size=20, bold=True, fill=_text_tone(TEAL), anchor="mm")
    plate.text((822, 741), "reported by compartment", size=20,
               bold=True, fill=INK, anchor="mm")

    right = _panel(plate, (1085, 240, 1540, 780), "CONGENITAL FORM", GOLD)
    rcx = (right[0] + right[2]) / 2
    plate.text((rcx, 350), "[A]  OUTER FUNDAL CONTOUR", size=18,
               bold=True, fill=_text_tone(GOLD), anchor="mm")
    plate.draw.arc((right[0] + 70, 360, right[2] - 70, 500),
                   180, 360, fill=GOLD, width=8)
    plate.draw.line((rcx, 395, rcx, 475), fill=GRID, width=3)
    plate.text((rcx, 512), "+", size=28, bold=True,
               fill=INK_SOFT, anchor="mm")
    plate.text((rcx, 548), "[B]  ENDOMETRIAL CAVITY", size=18,
               bold=True, fill=_text_tone(PLUM), anchor="mm")
    plate.draw.line((rcx - 70, 585, rcx, 655, rcx + 70, 585),
                    fill=PLUM, width=8)
    plate.draw.line((rcx, 655, rcx, 690), fill=PLUM, width=8)
    _tag(plate, (rcx, 733), "CLASSIFY TOGETHER", GOLD, size=18)


def _calc_cluster(plate: RadiologyPlate, center: Point, kind: str,
                  tone: str) -> None:
    x, y = center
    if kind == "coarse":
        for dx, dy in ((-45, -25), (5, 20), (48, -15)):
            plate.draw.ellipse((x + dx - 16, y + dy - 12,
                                x + dx + 16, y + dy + 12),
                               fill=hex_rgba(GOLD_LIGHT, 195),
                               outline=tone, width=3)
    elif kind == "pleomorphic":
        marks = ((-53, -25, 7), (-22, 20, 11), (14, -10, 6),
                 (42, 28, 9), (57, -32, 5), (-2, 40, 5))
        for dx, dy, radius in marks:
            plate.draw.polygon(((x + dx, y + dy - radius),
                                (x + dx + radius, y + dy + radius),
                                (x + dx - radius, y + dy + radius)),
                               fill=tone)
    else:
        for dx, dy, angle in ((-52, -20, -.2), (-18, 8, .3),
                              (20, 28, -.35), (48, -15, .45)):
            length = 35
            plate.draw.line((x + dx - math.cos(angle) * length / 2,
                             y + dy - math.sin(angle) * length / 2,
                             x + dx + math.cos(angle) * length / 2,
                             y + dy + math.sin(angle) * length / 2),
                            fill=tone, width=7)
            if dx in (20, 48):
                plate.draw.line((x + dx, y + dy,
                                 x + dx + 10, y + dy - 18), fill=tone, width=6)


def _render_breast_calcifications(plate: RadiologyPlate,
                                  item: Mapping[str, object]) -> None:
    _ = item
    _tag(plate, (800, 205), "CALCIFICATIONS: MORPHOLOGY x DISTRIBUTION", CORAL)
    morph = _panel(plate, (60, 240, 900, 590), "1  PARTICLE MORPHOLOGY", CORAL)
    kinds = ((250, "COARSE", "coarse", GOLD),
             (480, "FINE PLEOMORPHIC", "pleomorphic", CORAL),
             (745, "FINE LINEAR / BRANCHING", "linear", PLUM))
    for x, label, kind, tone in kinds:
        _calc_cluster(plate, (x, 415), kind, tone)
        plate.text((x, 522), label, size=18, bold=True,
                   fill=_text_tone(tone), anchor="mm")

    dist = _panel(plate, (930, 240, 1540, 590), "2  DISTRIBUTION", TEAL)
    patterns = ((1045, "GROUPED", ((-25, -15), (0, 18), (24, -10))),
                (1235, "LINEAR", ((-35, -25), (0, 0), (35, 25))),
                (1430, "SEGMENTAL", ((-40, 0), (-12, -14), (-12, 14),
                                      (18, -27), (18, 0), (18, 27),
                                      (48, -40), (48, 0), (48, 40))))
    for x, label, points in patterns:
        for dx, dy in points:
            plate.dot((x + dx, 420 + dy), 7, fill=TEAL,
                      outline=TEAL, width=1)
        plate.text((x, 522), label, size=18, bold=True,
                   fill=_text_tone(TEAL), anchor="mm")

    plate.draw.rounded_rectangle((125, 640, 1475, 790), radius=22,
                                 fill=hex_rgba(BLUE_LIGHT, 95),
                                 outline=BLUE, width=4)
    steps = ((315, "SPECIMEN IMAGE", "target retrieved"),
             (800, "PATHOLOGY", "explains same target"),
             (1285, "CONCORDANCE", "sample / follow-up plan"))
    for index, (x, heading, detail) in enumerate(steps):
        plate.text((x, 681), heading, size=20, bold=True,
                   fill=_text_tone(BLUE), anchor="mm")
        plate.text((x, 733), detail, size=20, bold=True,
                   fill=INK, anchor="mm")
        if index < 2:
            _arrow(plate, (x + 140, 710), (steps[index + 1][0] - 140, 710),
                   tone=GOLD)


def _render_breast_mri(plate: RadiologyPlate,
                       item: Mapping[str, object]) -> None:
    _ = item
    left = _panel(plate, (60, 230, 460, 785), "1  INDICATION", BLUE)
    indications = ("high-risk screening", "extent / staging",
                   "problem solving", "treatment response")
    for index, label in enumerate(indications):
        y = left[1] + 20 + index * 78
        plate.draw.rectangle((left[0] + 12, y - 17,
                             left[0] + 46, y + 17), outline=BLUE, width=4)
        plate.text((left[0] + 67, y), label, size=19, bold=True,
                   fill=INK, anchor="lm")
    _note(plate, (left[0] + 32, left[3] - 88,
                  left[2] - 32, left[3] - 20),
          "use when sensitivity can change care", size=19,
          tone=_text_tone(BLUE), bold=True)

    middle = _panel(plate, (495, 230, 1110, 785), "2  CHARACTERISE TOGETHER", CORAL)
    descriptors = (("MORPHOLOGY", "mass / non-mass", "outline"),
                   ("DISTRIBUTION", "focal | linear | segmental", "dots"),
                   ("KINETICS", "initial + delayed curve", "curve"))
    for index, (heading, detail, mark) in enumerate(descriptors):
        y = middle[1] + 55 + index * 125
        plate.text((middle[0] + 25, y), heading, size=19, bold=True,
                   fill=_text_tone(CORAL), anchor="lm")
        plate.text((middle[0] + 215, y), detail, size=18, bold=True,
                   fill=INK, anchor="lm")
        if mark == "outline":
            plate.draw.ellipse((middle[2] - 60, y - 25,
                                middle[2] - 10, y + 25), outline=CORAL, width=4)
        elif mark == "dots":
            for dx in (0, 20, 40):
                plate.dot((middle[2] - 60 + dx, y), 5,
                          fill=CORAL, outline=CORAL, width=1)
        else:
            plate.polyline(((middle[2] - 70, y + 20),
                            (middle[2] - 45, y - 20),
                            (middle[2] - 10, y - 3)),
                           fill=CORAL, width=5)
    plate.draw.rounded_rectangle((middle[0] + 70, middle[3] - 82,
                                  middle[2] - 70, middle[3] - 22), radius=18,
                                 fill=hex_rgba(GOLD_LIGHT, 145),
                                 outline=GOLD, width=3)
    plate.text(((middle[0] + middle[2]) / 2, middle[3] - 52),
               "no descriptor stands alone", size=20, bold=True,
               fill=_text_tone(GOLD), anchor="mm")

    right = _panel(plate, (1145, 230, 1540, 785), "3  MAP EXTENT", TEAL)
    _breast_outline(plate, (1340, 430), TEAL, scale=.85)
    plate.dot((1375, 420), 20, fill=CORAL, outline=INK, width=3)
    for y, label in ((590, "nodes"), (645, "implants"), (700, "therapy change")):
        plate.draw.line((right[0] + 45, y, right[0] + 90, y),
                        fill=TEAL, width=5)
        plate.text((right[0] + 110, y), label, size=20, bold=True,
                   fill=INK, anchor="lm")


def _finding_icon(plate: RadiologyPlate, center: Point, kind: str,
                  tone: str) -> None:
    x, y = center
    if kind == "mass":
        plate.draw.ellipse((x - 34, y - 28, x + 34, y + 28),
                           fill=hex_rgba(tone, 130), outline=tone, width=4)
    elif kind == "distortion":
        for angle in range(0, 360, 45):
            radians = math.radians(angle)
            plate.draw.line((x + math.cos(radians) * 12,
                             y + math.sin(radians) * 12,
                             x + math.cos(radians) * 43,
                             y + math.sin(radians) * 43),
                            fill=tone, width=4)
    elif kind == "asymmetry":
        plate.draw.arc((x - 48, y - 36, x + 15, y + 36),
                       90, 270, fill=tone, width=6)
        plate.draw.arc((x - 15, y - 36, x + 48, y + 36),
                       270, 90, fill=GRID, width=4)
    else:
        for dx, dy in ((-23, -13), (0, 16), (25, -9)):
            plate.dot((x + dx, y + dy), 6, fill=tone,
                      outline=tone, width=1)


def _render_breast(plate: RadiologyPlate,
                   item: Mapping[str, object]) -> None:
    _ = item
    _tag(plate, (800, 205), "FROM SCREENING SIGN TO COMPLETE BI-RADS ACTION", BLUE)
    detection = _panel(plate, (55, 235, 555, 785), "1  DETECTION", BLUE)
    findings = (("mass", "MASS"), ("distortion", "DISTORTION"),
                ("asymmetry", "ASYMMETRY"), ("calcs", "CALCIFICATIONS"))
    for index, (kind, label) in enumerate(findings):
        x = detection[0] + 95 + (index % 2) * 210
        y = detection[1] + 95 + (index // 2) * 185
        _finding_icon(plate, (x, y), kind, BLUE)
        plate.text((x, y + 72), label, size=18, bold=True,
                   fill=_text_tone(BLUE), anchor="mm")
    plate.text(((detection[0] + detection[2]) / 2, detection[3] - 33),
               "different signs start different analyses", size=19,
               bold=True, fill=INK_SOFT, anchor="mm")

    _arrow(plate, (560, 500), (635, 500), tone=GOLD)
    workup = _panel(plate, (645, 235, 1085, 785), "2  DIAGNOSTIC WORK-UP", TEAL)
    for index, (heading, detail) in enumerate((
            ("VIEWS", "does the sign persist?"),
            ("ULTRASOUND", "cystic, solid, margin?"),
            ("COMPARE", "new or changing?"))):
        y = workup[1] + 35 + index * 125
        plate.draw.rounded_rectangle((workup[0] + 20, y,
                                      workup[2] - 20, y + 103), radius=17,
                                     fill=hex_rgba(TEAL_LIGHT, 105),
                                     outline=TEAL, width=3)
        plate.text((workup[0] + 45, y + 29), heading, size=19,
                   bold=True, fill=_text_tone(TEAL))
        plate.text((workup[0] + 45, y + 63), detail, size=19,
                   bold=True, fill=INK)

    _arrow(plate, (1090, 500), (1160, 500), tone=GOLD)
    action = _panel(plate, (1170, 235, 1545, 785), "3  CATEGORY + ACTION", CORAL)
    paths = (("BI-RADS 1-2", "routine screening"),
             ("BI-RADS 3", "short-interval follow-up"),
             ("BI-RADS 4-5", "tissue diagnosis"))
    for index, (heading, detail) in enumerate(paths):
        y = action[1] + 35 + index * 122
        shape = "circle" if index == 0 else "square" if index == 1 else "triangle"
        if shape == "circle":
            plate.dot((action[0] + 50, y + 32), 22,
                      fill=PAPER_LIGHT, outline=CORAL, width=5)
        elif shape == "square":
            plate.draw.rectangle((action[0] + 29, y + 11,
                                  action[0] + 71, y + 53),
                                 fill=PAPER_LIGHT, outline=CORAL, width=5)
        else:
            plate.draw.polygon(((action[0] + 50, y + 8),
                                (action[0] + 74, y + 54),
                                (action[0] + 26, y + 54)),
                               fill=PAPER_LIGHT, outline=CORAL)
        plate.text((action[0] + 92, y + 15), heading, size=19,
                   bold=True, fill=_text_tone(CORAL))
        plate.text((action[0] + 92, y + 50), detail, size=16,
                   bold=True, fill=INK)
    _note(plate, (action[0] + 18, action[3] - 84,
                  action[2] - 18, action[3] - 16),
          "BI-RADS 0 = incomplete work-up, not a final assessment",
          size=18, tone=INK_SOFT, bold=True)


RENDERERS: Dict[str, Renderer] = {
    "rad.5.pancreas-acute": _render_pancreas_acute,
    "rad.5.appendicitis": _render_appendicitis,
    "rad.5.biliary": _render_biliary,
    "rad.5.bowel-ischaemia": _render_bowel_ischaemia,
    "rad.5.bowel-obstruction": _render_bowel_obstruction,
    "rad.5.abdominal-trauma": _render_abdominal_trauma,
    "rad.5.ibd": _render_ibd,
    "rad.5.pancreas-tumour": _render_pancreas_tumour,
    "rad.5.peritoneum": _render_peritoneum,
    "rad.5.rectal-mr": _render_rectal_mr,
    "rad.3.acute-abdomen": _render_acute_abdomen,
    "rad.4.liver": _render_liver,
    "rad.4.kidney": _render_kidney,
    "rad.5.scrotum": _render_scrotum,
    "rad.5.adrenal": _render_adrenal,
    "rad.5.bladder-virads": _render_bladder_virads,
    "rad.5.ovarian-orads": _render_ovarian_orads,
    "rad.5.prostate-mri": _render_prostate_mri,
    "rad.5.uterine-mr": _render_uterine_mr,
    "rad.5.breast-calcifications": _render_breast_calcifications,
    "rad.5.breast-mri": _render_breast_mri,
    "rad.4.breast": _render_breast,
}


EXPECTED_IDS = {
    "rad.5.pancreas-acute", "rad.5.appendicitis", "rad.5.biliary",
    "rad.5.bowel-ischaemia", "rad.5.bowel-obstruction",
    "rad.5.abdominal-trauma", "rad.5.ibd", "rad.5.pancreas-tumour",
    "rad.5.peritoneum", "rad.5.rectal-mr", "rad.3.acute-abdomen",
    "rad.4.liver", "rad.4.kidney", "rad.5.scrotum", "rad.5.adrenal",
    "rad.5.bladder-virads", "rad.5.ovarian-orads",
    "rad.5.prostate-mri", "rad.5.uterine-mr",
    "rad.5.breast-calcifications", "rad.5.breast-mri", "rad.4.breast",
}

if set(RENDERERS) != EXPECTED_IDS:
    raise ValueError("Abdomen/breast renderer inventory drift")
if len({id(renderer) for renderer in RENDERERS.values()}) != len(RENDERERS):
    raise ValueError("Each abdomen/breast lesson needs a unique renderer")


__all__ = ["EXPECTED_IDS", "RENDERERS"]
