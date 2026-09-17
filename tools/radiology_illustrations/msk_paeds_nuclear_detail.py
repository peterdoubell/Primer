"""Bespoke musculoskeletal, paediatric, and nuclear-medicine plates.

These deterministic diagrams teach the observable relationship behind an
imaging decision. They deliberately avoid synthetic patient scans: geometry,
signal keys, anatomical landmarks, and decision paths state exactly which
claim a learner may draw from the schematic.
"""

from __future__ import annotations

import math
from typing import Callable, Dict, Mapping, Sequence, Tuple

from math_illustrations.core import font, mix

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
    hex_rgba,
)


Point = Tuple[float, float]
Box = Tuple[float, float, float, float]
Renderer = Callable[[RadiologyPlate, Mapping[str, object]], None]

TONES = (BLUE, TEAL, GOLD, CORAL, PLUM, GREEN)
LIGHTS = (BLUE_LIGHT, TEAL_LIGHT, GOLD_LIGHT, CORAL_LIGHT, PLUM_LIGHT, GREEN_LIGHT)
DARK = {
    BLUE: "#20465f",
    TEAL: "#20544f",
    GOLD: "#76520f",
    CORAL: "#7f3d31",
    PLUM: "#513957",
    GREEN: "#344b2d",
}


def _surface(plate: RadiologyPlate, box: Box, tone: str = BLUE, *,
             alpha: int = 210, radius: int = 24, width: int = 3) -> None:
    plate.draw.rounded_rectangle(
        box, radius=radius, fill=hex_rgba(mix(tone, PAPER_LIGHT, .90), alpha),
        outline=hex_rgba(tone, 200), width=width,
    )


def _tag(plate: RadiologyPlate, center: Point, value: str, tone: str,
         *, size: int = 21) -> None:
    face = DARK.get(tone, INK)
    half_width = max(70, plate.draw.textlength(value, font=font(size, bold=True)) / 2 + 18)
    left = center[0] - half_width
    right = center[0] + half_width
    plate.draw.rounded_rectangle(
        (left, center[1] - 22, right, center[1] + 22), radius=20,
        fill=hex_rgba(mix(tone, PAPER_LIGHT, .78), 238),
        outline=hex_rgba(tone, 210), width=2,
    )
    plate.text(center, value, size=size, bold=True, fill=face, anchor="mm")


def _caption(plate: RadiologyPlate, center: Point, value: str, tone: str = INK,
             *, size: int = 23) -> None:
    # The 800 px derivative halves all coordinates.  Keep the shared teaching
    # sentence clear of cards that commonly end at y=785 while retaining a
    # separate footer band below it.
    if center[1] >= 780:
        center = (center[0], 808)
    plate.text(center, value, size=size, bold=True,
               fill=DARK.get(tone, tone), anchor="mm")


def _wrapped(plate: RadiologyPlate, box: Box, value: str, *, size: int = 22,
             fill: str = INK_SOFT, bold: bool = False) -> None:
    plate.wrapped_text(tuple(int(value) for value in box), value, size=size,
                       fill=fill, bold=bold, line_gap=5)


def _arrow(plate: RadiologyPlate, start: Point, end: Point, value: str = "",
           tone: str = INK_SOFT, *, offset: Point = (0, -22), width: int = 6) -> None:
    plate.arrow(start, end, fill=tone, width=width, head=18)
    if value:
        plate.text(((start[0] + end[0]) / 2 + offset[0],
                    (start[1] + end[1]) / 2 + offset[1]), value,
                   size=19, bold=True, fill=DARK.get(tone, tone), anchor="mm")


def _joint(plate: RadiologyPlate, center: Point, *, gap_left: int = 20,
           gap_right: int = 20, tone: str = BLUE) -> None:
    """Draw opposing articular ends with independently controllable spaces."""
    x, y = center
    plate.draw.rounded_rectangle((x - 118, y - 120, x - gap_left, y + 120),
                                 radius=42, fill=hex_rgba(GOLD_LIGHT, 120),
                                 outline=INK_SOFT, width=4)
    plate.draw.rounded_rectangle((x + gap_right, y - 120, x + 118, y + 120),
                                 radius=42, fill=hex_rgba(GOLD_LIGHT, 120),
                                 outline=INK_SOFT, width=4)
    plate.draw.line((x - gap_left, y - 80, x - gap_left, y + 80),
                    fill=tone, width=8)
    plate.draw.line((x + gap_right, y - 80, x + gap_right, y + 80),
                    fill=tone, width=8)


def _long_bone(plate: RadiologyPlate, box: Box, *, tone: str = GOLD) -> None:
    x0, y0, x1, y1 = box
    mid = (x0 + x1) / 2
    plate.draw.rounded_rectangle((mid - 34, y0 + 55, mid + 34, y1 - 55),
                                 radius=25, fill=hex_rgba(GOLD_LIGHT, 135),
                                 outline=INK_SOFT, width=4)
    plate.draw.ellipse((mid - 72, y0, mid + 72, y0 + 116),
                       fill=hex_rgba(GOLD_LIGHT, 135), outline=INK_SOFT, width=4)
    plate.draw.ellipse((mid - 72, y1 - 116, mid + 72, y1),
                       fill=hex_rgba(GOLD_LIGHT, 135), outline=INK_SOFT, width=4)
    plate.draw.line((mid, y0 + 84, mid, y1 - 84), fill=tone, width=4)


def _signal_key(plate: RadiologyPlate, center: Point, label: str, tone: str,
                pattern: str) -> None:
    x, y = center
    if pattern == "solid":
        plate.draw.ellipse((x - 12, y - 12, x + 12, y + 12), fill=tone,
                           outline=INK, width=2)
    elif pattern == "ring":
        plate.draw.ellipse((x - 12, y - 12, x + 12, y + 12), fill=PAPER_LIGHT,
                           outline=tone, width=5)
    else:
        plate.draw.line((x - 15, y, x + 15, y), fill=tone, width=5)
        plate.draw.line((x - 15, y - 8, x + 15, y - 8), fill=tone, width=2)
    plate.text((x + 23, y), label, size=20, bold=True,
               fill=DARK.get(tone, tone), anchor="lm")


def draw_ankle_foot(plate: RadiologyPlate, _item: Mapping[str, object]) -> None:
    _tag(plate, (300, 195), "1  CLINICAL RULE", BLUE)
    _tag(plate, (800, 195), "2  STABILITY", TEAL)
    _tag(plate, (1300, 195), "3  OCCULT CLUE", CORAL)
    _surface(plate, (95, 235, 505, 785), BLUE)
    # Side-view ankle and foot. Solid targets plus labels avoid a generic body icon.
    plate.draw.line((245, 290, 245, 505), fill=INK_SOFT, width=34)
    plate.draw.line((310, 295, 310, 490), fill=INK_SOFT, width=22)
    plate.draw.arc((205, 445, 345, 575), 175, 355, fill=GOLD, width=38)
    plate.polyline(((270, 540), (350, 590), (440, 610)), fill=INK_SOFT, width=30)
    for point, label in (((220, 465), "malleolus"), ((365, 585), "midfoot")):
        plate.draw.ellipse((point[0] - 14, point[1] - 14,
                            point[0] + 14, point[1] + 14), fill=CORAL)
        plate.text((point[0] - 8, point[1] + 34), label, size=19, bold=True,
                   fill=DARK[CORAL], anchor="ma")
    plate.draw.line((170, 690, 430, 690), fill=GRID, width=5)
    for index in range(4):
        plate.draw.ellipse((205 + index * 64, 666, 230 + index * 64, 690),
                           fill=TEAL)
    _caption(plate, (300, 744), "tender site + weight-bearing", BLUE, size=19)

    _surface(plate, (545, 235, 1055, 785), TEAL)
    # Frontal mortise: fibula, tibia, talus, and measured clear spaces.
    plate.draw.rounded_rectangle((665, 270, 790, 525), radius=25,
                                 fill=hex_rgba(GOLD_LIGHT, 130), outline=INK_SOFT, width=4)
    plate.draw.rounded_rectangle((845, 300, 920, 545), radius=22,
                                 fill=hex_rgba(GOLD_LIGHT, 130), outline=INK_SOFT, width=4)
    plate.draw.polygon(((690, 550), (895, 550), (855, 680), (725, 680)),
                       fill=hex_rgba(BLUE_LIGHT, 105), outline=BLUE)
    plate.dashed_line((790, 350), (845, 350), fill=CORAL, width=4, dash=9, gap=7)
    plate.dashed_line((790, 530), (845, 530), fill=CORAL, width=4, dash=9, gap=7)
    plate.text((817, 325), "syndesmosis", size=18, bold=True,
               fill=DARK[CORAL], anchor="mm")
    plate.arrow((610, 590), (690, 590), fill=TEAL, width=5, head=15)
    plate.arrow((980, 590), (895, 590), fill=TEAL, width=5, head=15)
    _caption(plate, (800, 735), "malleoli + mortise + syndesmosis", TEAL, size=20)

    _surface(plate, (1095, 235, 1505, 785), CORAL)
    plate.polyline(((1160, 600), (1225, 525), (1325, 520), (1425, 575)),
                   fill=INK_SOFT, width=24)
    plate.draw.ellipse((1210, 492, 1250, 532), fill=CORAL, outline=INK)
    plate.draw.ellipse((1378, 542, 1418, 582), fill=PLUM, outline=INK)
    plate.text((1230, 455), "navicular / base of 5th", size=18, bold=True,
               fill=DARK[CORAL], anchor="mm")
    plate.draw.arc((1160, 565, 1450, 690), 190, 345, fill=TEAL, width=8)
    plate.text((1300, 704), "tendon / plantar heel path", size=19, bold=True,
               fill=DARK[TEAL], anchor="mm")
    _arrow(plate, (1180, 335), (1415, 335), "targeted US / CT / MRI", CORAL)
    _caption(plate, (800, 795),
             "The first radiograph follows a clinical rule; later imaging follows a named unresolved structure.",
             INK, size=21)


def draw_marrow_muscle(plate: RadiologyPlate, _item: Mapping[str, object]) -> None:
    _tag(plate, (325, 195), "REACTIVE OEDEMA", BLUE)
    _tag(plate, (800, 195), "STRUCTURAL INJURY", CORAL)
    _tag(plate, (1275, 195), "DIABETIC FOOT", TEAL)
    for index, (left, tone) in enumerate(((105, BLUE), (575, CORAL), (1045, TEAL))):
        _surface(plate, (left, 235, left + 450, 785), tone)
    # Bone marrow: diffuse water-sensitive signal around a mechanically loaded cortex.
    _long_bone(plate, (210, 285, 440, 665), tone=BLUE)
    for y in range(370, 590, 42):
        plate.draw.ellipse((308, y, 334, y + 26), fill=hex_rgba(BLUE, 130),
                           outline=BLUE, width=2)
    plate.text((325, 705), "diffuse signal; cortex remains intact", size=20,
               bold=True, fill=DARK[BLUE], anchor="mm")
    # Fracture line plus torn muscle fibres: structural damage is a separate discriminator.
    _long_bone(plate, (645, 285, 820, 665), tone=CORAL)
    plate.polyline(((710, 430), (755, 458), (716, 492), (760, 520)),
                   fill=CORAL, width=9)
    for offset in range(6):
        y = 340 + offset * 48
        plate.draw.line((850, y, 1000, y + 10), fill=TEAL, width=7)
    plate.draw.line((910, 418, 945, 488), fill=CORAL, width=9)
    plate.draw.line((945, 418, 910, 488), fill=CORAL, width=9)
    plate.text((810, 705), "fracture line or fibre disruption", size=20,
               bold=True, fill=DARK[CORAL], anchor="mm")
    # Ulcer-to-bone route and neuropathic joint redistribution.
    plate.polyline(((1110, 610), (1190, 535), (1310, 528), (1450, 590)),
                   fill=INK_SOFT, width=28)
    plate.draw.ellipse((1200, 490, 1260, 548), fill=CORAL, outline=INK, width=3)
    plate.arrow((1320, 425), (1230, 498), fill=CORAL, width=7, head=18)
    plate.text((1325, 404), "ulcer tract reaches bone?", size=20, bold=True,
               fill=DARK[CORAL], anchor="mm")
    for x, y in ((1335, 560), (1375, 535), (1412, 570)):
        plate.draw.polygon(((x, y - 20), (x + 24, y), (x, y + 20), (x - 24, y)),
                           fill=hex_rgba(GOLD_LIGHT, 160), outline=GOLD)
    plate.text((1275, 705), "infection route ≠ neuropathic remodelling", size=19,
               bold=True, fill=DARK[TEAL], anchor="mm")
    _caption(plate, (800, 795),
             "Distribution suggests a cause; a fracture line, fibre tear, ulcer tract, or destructive replacement changes it.",
             INK, size=21)


def draw_bone_tumours(plate: RadiologyPlate, _item: Mapping[str, object]) -> None:
    _tag(plate, (270, 195), "AGE + EXACT SITE", BLUE)
    _tag(plate, (790, 195), "GROWTH BEHAVIOUR", CORAL)
    _tag(plate, (1310, 195), "PLAN BEFORE BIOPSY", GREEN)
    _surface(plate, (90, 235, 465, 785), BLUE)
    _long_bone(plate, (130, 275, 290, 710), tone=BLUE)
    for y, label in ((330, "epiphysis"), (430, "metaphysis"), (585, "diaphysis")):
        plate.draw.line((225, y, 300, y), fill=GRID, width=3)
        plate.text((310, y), label, size=18, bold=True, fill=INK_SOFT, anchor="lm")
    plate.draw.ellipse((175, 398, 245, 468), fill=hex_rgba(BLUE, 110), outline=BLUE, width=4)
    plate.text((275, 748), "prior = age × bone × segment", size=19, bold=True,
               fill=DARK[BLUE], anchor="mm")

    _surface(plate, (495, 235, 1085, 785), CORAL)
    # Three radiographic signs share one cortex: margin, matrix, periosteum.
    plate.draw.rounded_rectangle((555, 320, 1025, 660), radius=95,
                                 fill=hex_rgba(GOLD_LIGHT, 100), outline=INK_SOFT, width=5)
    # Narrow versus wide transition zone.
    plate.draw.ellipse((610, 400, 725, 535), fill=PAPER_LIGHT, outline=BLUE, width=7)
    plate.dashed_line((790, 380), (910, 545), fill=CORAL, width=8, dash=14, gap=9)
    for x, y in ((825, 430), (875, 470), (850, 520), (920, 430)):
        plate.draw.ellipse((x - 9, y - 9, x + 9, y + 9), fill=PLUM)
    plate.draw.polygon(((1010, 420), (1060, 470), (1010, 510)),
                       fill=hex_rgba(CORAL_LIGHT, 170), outline=CORAL)
    plate.text((667, 570), "sharp margin", size=18, bold=True,
               fill=DARK[BLUE], anchor="mm")
    plate.text((865, 570), "wide zone + matrix", size=18, bold=True,
               fill=DARK[CORAL], anchor="mm")
    plate.text((1010, 365), "periosteal response", size=18, bold=True,
               fill=DARK[CORAL], anchor="mm")
    _caption(plate, (790, 730), "margin + periosteum + matrix = tempo evidence", CORAL, size=20)

    _surface(plate, (1115, 235, 1510, 785), GREEN)
    plate.draw.ellipse((1190, 330, 1335, 510), outline=GREEN, width=6)
    plate.draw.line((1262, 510, 1262, 620), fill=GREEN, width=9)
    plate.dashed_line((1280, 420), (1430, 600), fill=CORAL, width=6, dash=13, gap=9)
    plate.text((1390, 390), "MRI extent", size=19, bold=True,
               fill=DARK[GREEN], anchor="mm")
    _arrow(plate, (1190, 675), (1435, 675), "sarcoma team → planned tract", GREEN)
    plate.draw.line((1435, 650, 1435, 715), fill=CORAL, width=8)
    _caption(plate, (800, 795),
             "An aggressive lesion enters the sarcoma pathway before an unplanned biopsy can contaminate future planes.",
             INK, size=21)


def draw_fracture_description(plate: RadiologyPlate, _item: Mapping[str, object]) -> None:
    _surface(plate, (105, 220, 1495, 785), BLUE)
    _tag(plate, (320, 260), "GEOMETRY", BLUE)
    _tag(plate, (800, 260), "CONSEQUENCES", CORAL)
    _tag(plate, (1280, 260), "HIDDEN PAIR", PLUM)
    # Central displaced fracture with axes and angle arc.
    plate.draw.rounded_rectangle((650, 315, 735, 525), radius=34,
                                 fill=hex_rgba(GOLD_LIGHT, 130), outline=INK_SOFT, width=5)
    plate.draw.polygon(((652, 525), (735, 525), (680, 585)),
                       fill=hex_rgba(GOLD_LIGHT, 130), outline=INK_SOFT)
    plate.draw.polygon(((750, 600), (815, 535), (835, 620)),
                       fill=hex_rgba(GOLD_LIGHT, 130), outline=INK_SOFT)
    plate.draw.rounded_rectangle((750, 600, 835, 745), radius=32,
                                 fill=hex_rgba(GOLD_LIGHT, 130), outline=INK_SOFT, width=5)
    plate.dashed_line((693, 300), (693, 730), fill=BLUE, width=3, dash=11, gap=8)
    plate.dashed_line((795, 520), (850, 740), fill=CORAL, width=3, dash=11, gap=8)
    plate.draw.arc((675, 515, 865, 705), 270, 335, fill=CORAL, width=6)
    plate.text((865, 585), "angulation", size=20, bold=True,
               fill=DARK[CORAL], anchor="lm")
    plate.arrow((700, 570), (775, 570), fill=PLUM, width=6, head=18)
    plate.text((738, 545), "displacement", size=18, bold=True,
               fill=DARK[PLUM], anchor="mm")
    # Structured descriptors converge on the image.
    for index, (label, y) in enumerate((("bone + segment", 345), ("line / comminution", 440),
                                       ("rotation / shortening", 665))):
        tone = (BLUE, TEAL, GOLD)[index]
        _tag(plate, (315, y), label, tone, size=19)
        _arrow(plate, (470, y), (630, 505 if y < 500 else 640), "", tone)
    # Consequences and adjacent sites.
    plate.draw.arc((970, 345, 1120, 515), 15, 335, fill=CORAL, width=8)
    plate.draw.line((1012, 500, 1078, 500), fill=CORAL, width=8)
    plate.text((1045, 545), "joint extension", size=19, bold=True,
               fill=DARK[CORAL], anchor="mm")
    plate.draw.line((980, 620, 1110, 620), fill=BLUE, width=7)
    plate.draw.line((980, 650, 1110, 650), fill=CORAL, width=7)
    plate.text((1045, 690), "nerve / vessel / skin", size=19, bold=True,
               fill=INK_SOFT, anchor="mm")
    # Mechanism points to a second site, not a routine whole-body search.
    plate.draw.ellipse((1230, 360, 1370, 500), outline=PLUM, width=7)
    plate.draw.ellipse((1280, 590, 1420, 730), outline=PLUM, width=7)
    _arrow(plate, (1300, 520), (1350, 575), "same force path", PLUM, offset=(70, 0))
    plate.text((1300, 335), "injury seen", size=18, bold=True,
               fill=DARK[PLUM], anchor="mm")
    plate.text((1330, 755), "joint / paired injury", size=18,
               bold=True, fill=DARK[PLUM], anchor="mm")
    _caption(plate, (800, 795),
             "A useful description names the fracture, then states the joint, soft-tissue, and mechanism-dependent risks.",
             INK, size=21)


def draw_hip(plate: RadiologyPlate, _item: Mapping[str, object]) -> None:
    headings = (("SHAPE + COVERAGE", BLUE), ("OSTEONECROSIS", CORAL),
                ("ARTHROPLASTY", TEAL))
    for index, (heading, tone) in enumerate(headings):
        left = 85 + index * 505
        _surface(plate, (left, 230, left + 470, 785), tone)
        _tag(plate, (left + 235, 270), heading, tone)
    # Coverage angle: both rays and the arc share the femoral-head centre.
    plate.draw.arc((155, 350, 420, 635), 110, 340, fill=INK_SOFT, width=32)
    plate.draw.ellipse((247, 410, 405, 568), fill=hex_rgba(GOLD_LIGHT, 135),
                       outline=BLUE, width=5)
    plate.draw.line((326, 489, 440, 685), fill=INK_SOFT, width=28)
    plate.dashed_line((326, 489), (326, 330), fill=BLUE, width=4, dash=10, gap=7)
    plate.draw.line((326, 489, 412, 445), fill=CORAL, width=4)
    plate.draw.arc((244, 407, 408, 571), 270, 333, fill=CORAL, width=6)
    plate.text((235, 600), "coverage", size=19, bold=True, fill=DARK[BLUE], anchor="mm")
    plate.text((414, 380), "coverage angle", size=18, bold=True, fill=DARK[CORAL], anchor="mm")
    _caption(plate, (320, 735), "measurement supports a mechanical conflict", BLUE, size=18)
    # Osteonecrosis: subchondral geography and collapse.
    plate.draw.ellipse((675, 390, 890, 605), fill=hex_rgba(GOLD_LIGHT, 135),
                       outline=INK_SOFT, width=5)
    plate.draw.arc((700, 405, 865, 560), 190, 340, fill=CORAL, width=10)
    plate.draw.arc((725, 420, 845, 535), 185, 345, fill=PLUM, width=5)
    plate.draw.line((710, 455, 865, 455), fill=CORAL, width=5)
    plate.arrow((905, 430), (855, 455), fill=CORAL, width=5, head=15)
    plate.text((920, 410), "subchondral extent", size=18, bold=True,
               fill=DARK[CORAL], anchor="mm")
    plate.text((782, 635), "assess contour for collapse", size=20, bold=True,
               fill=DARK[PLUM], anchor="mm")
    _caption(plate, (825, 735), "extent and collapse determine stage", CORAL, size=19)
    # Arthroplasty: cup/stem position and interface.
    plate.draw.arc((1195, 345, 1450, 610), 110, 335, fill=INK_SOFT, width=28)
    plate.draw.ellipse((1275, 410, 1415, 550), fill=PAPER_LIGHT,
                       outline=TEAL, width=12)
    plate.draw.ellipse((1310, 445, 1380, 515), fill=GOLD, outline=INK, width=3)
    plate.draw.polygon(((1333, 500), (1365, 500), (1405, 730), (1345, 730)),
                       fill=hex_rgba(BLUE_LIGHT, 140), outline=BLUE)
    plate.dashed_line((1240, 360), (1435, 360), fill=CORAL, width=4, dash=11, gap=8)
    plate.draw.arc((1300, 435, 1420, 555), 90, 250, fill=CORAL, width=5)
    _caption(plate, (1330, 735), "position + lucency + wear + infection clues", TEAL, size=18)
    _caption(plate, (800, 795),
             "Hip measurements become useful only when they answer a mechanism, collapse stage, or implant-failure question.",
             INK, size=21)


def draw_knee(plate: RadiologyPlate, _item: Mapping[str, object]) -> None:
    headings = (("MENISCUS", BLUE), ("LIGAMENT", CORAL), ("CARTILAGE", TEAL))
    for index, (heading, tone) in enumerate(headings):
        left = 85 + index * 505
        _surface(plate, (left, 230, left + 470, 785), tone)
        _tag(plate, (left + 235, 270), heading, tone)
    # Meniscal triangle, tear to surface, and displaced fragment/root.
    plate.draw.polygon(((145, 610), (455, 610), (300, 360)),
                       fill=hex_rgba(BLUE_LIGHT, 125), outline=BLUE)
    plate.polyline(((250, 545), (320, 500), (355, 420)), fill=CORAL, width=8)
    plate.arrow((375, 455), (430, 400), fill=PLUM, width=6, head=17)
    plate.text((300, 652), "signal reaches articular surface", size=19, bold=True,
               fill=DARK[BLUE], anchor="mm")
    plate.text((422, 372), "displaced? root?", size=18, bold=True,
               fill=DARK[PLUM], anchor="mm")
    # ACL/PCL crossing with one discontinuous fibre and translation arrow.
    plate.draw.rounded_rectangle((645, 365, 990, 455), radius=38,
                                 fill=hex_rgba(GOLD_LIGHT, 120), outline=INK_SOFT, width=4)
    plate.draw.rounded_rectangle((645, 600, 990, 690), radius=38,
                                 fill=hex_rgba(GOLD_LIGHT, 120), outline=INK_SOFT, width=4)
    plate.draw.line((705, 600, 880, 455), fill=TEAL, width=10)
    plate.draw.line((930, 600, 860, 540), fill=CORAL, width=10)
    plate.draw.line((810, 500, 760, 455), fill=CORAL, width=10)
    plate.dashed_line((760, 455), (860, 540), fill=CORAL, width=4, dash=10, gap=7)
    plate.arrow((690, 730), (920, 730), fill=CORAL, width=7, head=20)
    plate.text((817, 750), "secondary translation sign", size=18, bold=True,
               fill=DARK[CORAL], anchor="mm")
    # Cartilage defect with depth/area and subchondral response.
    plate.draw.arc((1165, 390, 1425, 650), 195, 345, fill=INK_SOFT, width=48)
    # A real focal cartilage gap, not a pale arc floating inside the joint.
    for start, end in ((195, 250), (290, 345)):
        plate.draw.arc((1175, 400, 1415, 640), start, end, fill=TEAL, width=14)
    plate.draw.line((1254, 370, 1336, 370), fill=CORAL, width=5)
    plate.draw.line((1295, 400, 1295, 414), fill=CORAL, width=5)
    for x, y in ((1265, 590), (1305, 610), (1345, 585)):
        plate.draw.ellipse((x - 11, y - 11, x + 11, y + 11), fill=PLUM)
    plate.text((1295, 680), "depth × area + subchondral response", size=18,
               bold=True, fill=DARK[TEAL], anchor="mm")
    _caption(plate, (800, 795),
             "A tear is reported through surface contact, displacement, instability, or structural depth—not signal alone.",
             INK, size=21)


def draw_msk_mri(plate: RadiologyPlate, _item: Mapping[str, object]) -> None:
    _tag(plate, (315, 195), "T1  ANATOMY", BLUE)
    _tag(plate, (800, 195), "FLUID-SENSITIVE + FS", TEAL)
    _tag(plate, (1285, 195), "NAMED ARTEFACT TESTS", CORAL, size=19)
    boxes = ((90, 235, 540, 785), (575, 235, 1025, 785), (1060, 235, 1510, 785))
    for box, tone in zip(boxes, (BLUE, TEAL, CORAL)):
        _surface(plate, box, tone)
    # The same axial compartment is redrawn with an explicit signal key.
    for center, fat_tone, fluid_tone in (((315, 485), GOLD, BLUE),
                                         ((800, 485), INK_SOFT, TEAL)):
        x, y = center
        plate.draw.ellipse((x - 150, y - 150, x + 150, y + 150),
                           fill=hex_rgba(GOLD_LIGHT, 75), outline=INK_SOFT, width=4)
        plate.draw.ellipse((x - 62, y - 75, x + 62, y + 75),
                           fill=hex_rgba(fat_tone, 135), outline=BLUE, width=5)
        for dx in (-105, 105):
            plate.draw.ellipse((x + dx - 32, y - 68, x + dx + 32, y + 68),
                               fill=hex_rgba(CORAL_LIGHT, 90), outline=CORAL, width=3)
        plate.draw.ellipse((x + 45, y + 55, x + 100, y + 110),
                           fill=hex_rgba(fluid_tone, 175), outline=fluid_tone, width=4)
    _signal_key(plate, (180, 695), "fat / marrow bright", GOLD, "solid")
    _signal_key(plate, (650, 675), "fat suppressed", INK_SOFT, "line")
    _signal_key(plate, (650, 720), "fluid / oedema bright", TEAL, "solid")
    # Different mimics require different acquisition tests.  Phase ghosting
    # follows the phase-encode direction; magic-angle signal changes with
    # collagen orientation and echo time rather than spatially "moving".
    plate.draw.ellipse((1180, 315, 1390, 505),
                       fill=hex_rgba(BLUE_LIGHT, 85), outline=BLUE, width=4)
    plate.draw.rectangle((1265, 360, 1305, 440), fill=INK, outline=CORAL, width=4)
    for offset in (-70, -35, 35, 70):
        plate.draw.rectangle((1265 + offset, 360, 1305 + offset, 440),
                             outline=hex_rgba(CORAL, 115), width=3)
    plate.arrow((1135, 520), (1435, 520), fill=CORAL, width=6, head=18)
    plate.text((1285, 552), "ghosts follow the PE axis", size=20, bold=True,
               fill=DARK[CORAL], anchor="mm")
    plate.draw.line((1100, 580, 1470, 580), fill=GRID, width=3)
    # B0 is vertical; the tendon is drawn about 55 degrees to B0.
    plate.arrow((1160, 735), (1160, 610), fill=INK_SOFT, width=5, head=15)
    plate.text((1132, 620), "B0", size=20, bold=True, fill=INK_SOFT, anchor="rm")
    plate.draw.line((1160, 700, 1307, 597), fill=TEAL, width=13)
    plate.draw.arc((1080, 620, 1240, 780), 270, 325, fill=GOLD, width=5)
    plate.text((1200, 602), "55°", size=21, bold=True, fill=DARK[GOLD], anchor="mm")
    plate.text((1375, 635), "short TE: bright", size=20, bold=True,
               fill=DARK[TEAL], anchor="mm")
    plate.text((1375, 690), "long-TE re-check", size=20, bold=True,
               fill=DARK[PLUM], anchor="mm")
    _caption(plate, (800, 795),
             "Name the suspected artefact, then choose the acquisition change that should alter that specific mimic.",
             INK, size=21)


def draw_shoulder(plate: RadiologyPlate, _item: Mapping[str, object]) -> None:
    headings = (("CUFF REPAIRABILITY", BLUE), ("LABRUM + VARIANT", TEAL),
                ("INSTABILITY BONE LOSS", CORAL))
    for index, (heading, tone) in enumerate(headings):
        left = 85 + index * 505
        _surface(plate, (left, 230, left + 470, 785), tone)
        _tag(plate, (left + 235, 270), heading, tone, size=19)
    # Rotator cuff: tendon gap, retraction distance, and muscle quality.
    plate.draw.ellipse((235, 435, 425, 625), fill=hex_rgba(GOLD_LIGHT, 130),
                       outline=INK_SOFT, width=5)
    plate.draw.arc((135, 330, 360, 520), 250, 355, fill=BLUE, width=15)
    plate.draw.line((235, 430, 275, 445), fill=BLUE, width=14)
    plate.dashed_line((275, 445), (340, 460), fill=CORAL, width=5, dash=9, gap=6)
    plate.draw.line((155, 390, 235, 430), fill=TEAL, width=18)
    plate.arrow((238, 405), (330, 425), fill=CORAL, width=5, head=15)
    plate.text((285, 385), "retraction", size=18, bold=True,
               fill=DARK[CORAL], anchor="mm")
    plate.draw.ellipse((135, 610, 235, 700), fill=hex_rgba(CORAL_LIGHT, 95),
                       outline=CORAL, width=4)
    plate.text((285, 690), "tear + muscle atrophy", size=19, bold=True,
               fill=DARK[BLUE], anchor="mm")
    # Labrum: attachment relationship, not a generic signal dot.
    plate.draw.arc((660, 380, 930, 650), 80, 280, fill=INK_SOFT, width=32)
    plate.draw.ellipse((750, 435, 930, 615), fill=hex_rgba(GOLD_LIGHT, 120),
                       outline=TEAL, width=5)
    plate.draw.polygon(((685, 440), (735, 462), (690, 500)),
                       fill=PLUM, outline=INK)
    plate.polyline(((690, 500), (735, 540), (690, 575)), fill=CORAL, width=8)
    plate.text((790, 690), "attachment + associated sign", size=19, bold=True,
               fill=DARK[TEAL], anchor="mm")
    # Glenoid track and humeral impaction communicate bipolar bone loss.
    plate.draw.arc((1170, 370, 1435, 650), 110, 250, fill=CORAL, width=18)
    plate.draw.ellipse((1210, 420, 1425, 635), fill=hex_rgba(GOLD_LIGHT, 120),
                       outline=INK_SOFT, width=5)
    plate.draw.pieslice((1200, 410, 1435, 645), 300, 345,
                        fill=hex_rgba(CORAL_LIGHT, 180), outline=CORAL)
    plate.dashed_line((1175, 420), (1175, 620), fill=BLUE, width=5, dash=11, gap=7)
    plate.draw.line((1190, 410, 1190, 630), fill=TEAL, width=7)
    plate.text((1290, 690), "glenoid + humeral loss together", size=18,
               bold=True, fill=DARK[CORAL], anchor="mm")
    _caption(plate, (800, 795),
             "The operative map combines tendon and muscle, labral attachment, and both sides of instability bone loss.",
             INK, size=21)


def draw_arthritis(plate: RadiologyPlate, _item: Mapping[str, object]) -> None:
    headings = (("DEGENERATIVE", BLUE), ("INFLAMMATORY", CORAL),
                ("CRYSTAL / PROLIFERATIVE", PLUM))
    for index, (heading, tone) in enumerate(headings):
        left = 85 + index * 505
        _surface(plate, (left, 230, left + 470, 785), tone)
        _tag(plate, (left + 235, 270), heading, tone, size=19)
    # Asymmetric joint loss with osteophytes and sclerosis.
    plate.draw.rounded_rectangle((202, 375, 310, 615), radius=42,
                                 fill=hex_rgba(GOLD_LIGHT, 135), outline=INK_SOFT, width=4)
    plate.draw.polygon(((325, 375), (438, 375), (438, 615), (380, 615)),
                       fill=hex_rgba(GOLD_LIGHT, 135), outline=INK_SOFT, width=4)
    plate.draw.line((310, 415, 310, 575), fill=BLUE, width=8)
    plate.draw.line((334, 415, 371, 575), fill=BLUE, width=8)
    plate.draw.polygon(((290, 610), (335, 630), (300, 575)),
                       fill=GOLD, outline=INK)
    plate.draw.line((296, 420, 296, 570), fill=BLUE, width=11)
    plate.text((320, 700), "nonuniform loss + osteophyte + sclerosis", size=18,
               bold=True, fill=DARK[BLUE], anchor="mm")
    # Uniform loss with marginal erosions and periarticular change.
    _joint(plate, (825, 495), gap_left=28, gap_right=28, tone=CORAL)
    for y in (420, 495, 570):
        plate.draw.ellipse((785, y - 13, 812, y + 13), fill=PAPER_LIGHT,
                           outline=CORAL, width=4)
        plate.draw.ellipse((838, y - 13, 865, y + 13), fill=PAPER_LIGHT,
                           outline=CORAL, width=4)
    plate.text((825, 700), "uniform loss + marginal erosions", size=19,
               bold=True, fill=DARK[CORAL], anchor="mm")
    # Deposits and proliferative new bone are encoded as different marks.
    _joint(plate, (1330, 495), gap_left=34, gap_right=34, tone=PLUM)
    for x, y in ((1300, 410), (1340, 450), (1308, 510), (1352, 555)):
        plate.draw.ellipse((x - 10, y - 5, x + 10, y + 5), fill=PLUM)
    plate.draw.polygon(((1210, 620), (1175, 680), (1240, 658)),
                       fill=hex_rgba(GOLD, 170), outline=GOLD)
    plate.draw.polygon(((1450, 620), (1480, 680), (1415, 658)),
                       fill=hex_rgba(GOLD, 170), outline=GOLD)
    plate.text((1330, 700), "site + mineralisation + new bone", size=18,
               bold=True, fill=DARK[PLUM], anchor="mm")
    _caption(plate, (800, 795),
             "Distribution and the combination of loss, erosion, density, mineralisation, and new bone distinguish patterns.",
             INK, size=21)


def draw_wrist_hand(plate: RadiologyPlate, _item: Mapping[str, object]) -> None:
    _surface(plate, (90, 225, 1510, 785), BLUE)
    _tag(plate, (300, 265), "TRACE 3 GILULA ARCS", BLUE)
    _tag(plate, (800, 265), "OCCULT FRACTURE", CORAL)
    _tag(plate, (1300, 265), "DECISION FEATURE", TEAL)
    # Alignment schematic, fingers above: I/II bound S-L-T; III belongs
    # only to capitate/hamate. Omit unrelated bones instead of inventing a row.
    def contour(x, y):
        return y + .001 * (x - 340) ** 2

    for label, x0, x1, upper, lower in (
        ("S", 180, 280, 500, 580), ("L", 285, 390, 500, 580),
        ("T", 395, 490, 500, 580), ("C", 285, 385, 380, 480),
        ("H", 390, 490, 380, 480),
    ):
        xs = list(range(x0, x1 + 1, 5))
        plate.draw.polygon([(x, contour(x, upper)) for x in xs] +
                           [(x, contour(x, lower)) for x in reversed(xs)],
                           fill=hex_rgba(GOLD_LIGHT, 145), outline=INK_SOFT, width=3)
        x = (x0 + x1) / 2
        plate.text((x, contour(x, (upper + lower) / 2)), label,
                   size=23, bold=True, fill=INK_SOFT, anchor="mm")
    for y, x0, tone, label in ((580, 180, BLUE, "I"),
                               (500, 180, TEAL, "II"),
                               (480, 285, PLUM, "III")):
        plate.polyline([(x, contour(x, y)) for x in range(x0, 491, 5)], fill=tone, width=5)
        plate.text((x0 - 22, contour(x0, y)), label, size=20,
                   bold=True, fill=DARK[tone], anchor="rm")
    plate.text((340, 335), "fingers ↑ · alignment schematic", size=19,
               bold=True, fill=INK_SOFT, anchor="mm")
    plate.text((340, 640), "S scaphoid · L lunate · T triquetrum", size=18,
               bold=True, fill=INK_SOFT, anchor="mm")
    plate.text((340, 675), "C capitate · H hamate", size=18, bold=True,
               fill=INK_SOFT, anchor="mm")
    plate.text((340, 715), "trace continuity; recognise normal variants", size=18, bold=True,
               fill=DARK[BLUE], anchor="mm")
    # Scaphoid with barely visible fracture and focal tenderness target.
    plate.draw.ellipse((690, 370, 865, 650), fill=hex_rgba(GOLD_LIGHT, 140),
                       outline=INK_SOFT, width=5)
    plate.polyline(((720, 510), (775, 490), (820, 520)), fill=CORAL, width=7)
    plate.dashed_line((785, 490), (910, 405), fill=CORAL, width=4, dash=9, gap=7)
    plate.draw.ellipse((898, 390, 924, 416), fill=CORAL)
    plate.text((910, 370), "focal tenderness", size=20, bold=True,
               fill=DARK[CORAL], anchor="mm")
    plate.text((800, 735), "persistent suspicion → repeat / CT / MRI", size=20,
               bold=True, fill=DARK[CORAL], anchor="mm")
    # Alignment and vascular-risk outcomes branch urgency.
    plate.draw.polygon(((1190, 390), (1310, 350), (1425, 430),
                        (1380, 610), (1230, 645), (1145, 520)),
                       fill=hex_rgba(TEAL_LIGHT, 100), outline=TEAL)
    plate.arrow((1160, 500), (1405, 500), fill=CORAL, width=7, head=20)
    plate.dashed_line((1280, 350), (1280, 650), fill=BLUE, width=4, dash=10, gap=8)
    plate.text((1280, 690), "displacement • instability • perfusion risk", size=20,
               bold=True, fill=DARK[TEAL], anchor="mm")
    _caption(plate, (800, 795),
             "Alignment arcs expose instability; mechanism and focal examination decide when a hidden fracture needs more imaging.",
             INK, size=21)


def draw_paeds_hip_elbow(plate: RadiologyPlate, _item: Mapping[str, object]) -> None:
    headings = (("INFANT HIP — ULTRASOUND", BLUE),
                ("OLDER HIP — RADIOGRAPH", TEAL),
                ("CHILD ELBOW — ALIGNMENT", CORAL))
    for index, (heading, tone) in enumerate(headings):
        left = 85 + index * 505
        _surface(plate, (left, 230, left + 470, 785), tone)
        _tag(plate, (left + 235, 270), heading, tone, size=19)

    # Standard coronal infant-hip landmarks plus a separate dynamic-stability
    # arrow.  Direct labels make the construction usable without colour.
    plate.draw.line((175, 335, 175, 625), fill=BLUE, width=8)
    plate.text((195, 350), "straight ilium", size=20, bold=True,
               fill=DARK[BLUE], anchor="lm")
    plate.draw.line((175, 500, 315, 575), fill=CORAL, width=7)
    plate.draw.ellipse((260, 455, 430, 625), fill=PAPER_LIGHT, outline=TEAL, width=6)
    plate.draw.polygon(((430, 520), (450, 540), (430, 560)),
                       fill=PLUM_LIGHT, outline=PLUM)
    plate.draw.ellipse((162, 487, 188, 513), fill=GOLD, outline=INK, width=2)
    plate.text((190, 470), "bony rim", size=18, bold=True,
               fill=DARK[GOLD], anchor="lm")
    plate.text((450, 588), "labrum", size=18, bold=True,
               fill=DARK[PLUM], anchor="mm")
    plate.draw.arc((105, 430, 245, 570), 28, 90, fill=GOLD, width=5)
    plate.text((215, 583), "α", size=24, bold=True, fill=DARK[GOLD], anchor="mm")
    plate.arrow((350, 665), (420, 605), fill=TEAL, width=6, head=17)
    plate.text((310, 710), "coverage + gentle-stress stability", size=20,
               bold=True, fill=DARK[BLUE], anchor="mm")

    # A bilateral AP-pelvis abstraction: Hilgenreiner crosses both triradiate
    # cartilages and each Perkin line passes through its lateral acetabular rim.
    plate.draw.arc((625, 360, 810, 575), 190, 350, fill=INK_SOFT, width=14)
    plate.draw.arc((805, 360, 995, 575), 190, 350, fill=INK_SOFT, width=14)
    plate.draw.ellipse((682, 507, 708, 533), fill=GOLD, outline=INK, width=2)
    plate.draw.ellipse((887, 507, 913, 533), fill=GOLD, outline=INK, width=2)
    plate.draw.line((615, 520, 1030, 520), fill=BLUE, width=5)
    plate.text((630, 500), "H", size=21, bold=True, fill=DARK[BLUE], anchor="mm")
    for x in (650, 980):
        plate.draw.line((x, 335, x, 680), fill=TEAL, width=5)
        plate.text((x, 330), "P", size=21, bold=True, fill=DARK[TEAL], anchor="mm")
    # Normal head inferomedial on the left; displaced head superolateral on right.
    plate.draw.ellipse((690, 555, 770, 635), fill=hex_rgba(GOLD_LIGHT, 160),
                       outline=GREEN, width=5)
    plate.draw.ellipse((985, 405, 1045, 465), fill=hex_rgba(CORAL_LIGHT, 160),
                       outline=CORAL, width=5)
    plate.text((730, 665), "inferomedial", size=20, bold=True,
               fill=DARK[GREEN], anchor="mm")
    plate.text((970, 500), "superolateral", size=20, bold=True,
               fill=DARK[CORAL], anchor="mm")
    plate.text((825, 710), "H + P quadrants; compare both sides", size=20,
               bold=True, fill=DARK[TEAL], anchor="mm")

    # True-view elbow lines.  The RCL is collinear with the radial neck/shaft;
    # the AHL follows the anterior humeral cortex and crosses the capitellum.
    plate.text((1300, 315), "C–R–I–T–O–E: expected order", size=20,
               bold=True, fill=DARK[CORAL], anchor="mm")
    plate.draw.rounded_rectangle((1210, 340, 1285, 575), radius=24,
                                 fill=hex_rgba(GOLD_LIGHT, 130), outline=INK_SOFT, width=4)
    plate.draw.ellipse((1175, 565, 1295, 685), fill=hex_rgba(GOLD_LIGHT, 130),
                       outline=INK_SOFT, width=4)
    plate.draw.line((1285, 655, 1430, 742), fill=INK_SOFT, width=30)
    plate.dashed_line((1215, 300), (1215, 720), fill=CORAL, width=5, dash=10, gap=7)
    plate.dashed_line((1110, 550), (1450, 754), fill=BLUE, width=5, dash=10, gap=7)
    plate.text((1185, 420), "AHL", size=21, bold=True,
               fill=DARK[CORAL], anchor="rm")
    plate.text((1400, 665), "RCL", size=21, bold=True,
               fill=DARK[BLUE], anchor="lm")
    plate.text((1320, 770), "AHL varies by age • RCL: true view", size=17,
               bold=True, fill=DARK[CORAL], anchor="mm")
    _caption(plate, (800, 795),
             "Paediatric alignment tests change with ossification: use the landmark appropriate to the child's age and modality.",
             INK, size=21)


def draw_paediatric(plate: RadiologyPlate, _item: Mapping[str, object]) -> None:
    _surface(plate, (90, 225, 1510, 785), BLUE)
    _tag(plate, (300, 265), "QUESTION + AGE", BLUE)
    _tag(plate, (875, 265), "COMPLETE SEARCH", TEAL)
    _tag(plate, (1300, 265), "PROTECT + ESCALATE", CORAL)
    plate.draw.line((675, 300, 675, 745), fill=GRID, width=3)
    plate.draw.line((1090, 300, 1090, 745), fill=GRID, width=3)
    # A branching modality choice keeps ionising radiation explicit.  Each
    # modality's discriminator lives inside its card so labels cannot collide.
    plate.draw.rounded_rectangle((130, 365, 335, 475), radius=24,
                                 fill=hex_rgba(BLUE_LIGHT, 150), outline=BLUE, width=4)
    plate.text((232, 400), "clinical question", size=22, bold=True,
               fill=DARK[BLUE], anchor="mm")
    plate.text((232, 440), "age • anatomy • urgency", size=20, bold=True,
               fill=INK_SOFT, anchor="mm")
    choices = (("US", "dynamic • no ionising radiation", TEAL, 330),
               ("XR", "targeted projection", GOLD, 435),
               ("MRI", "soft tissue • time / motion", PLUM, 540),
               ("CT", "fast • dose optimised", CORAL, 645))
    for label, note, tone, y in choices:
        plate.arrow((335, 420), (365, y), fill=tone, width=5, head=15)
        plate.draw.rounded_rectangle((370, y - 40, 645, y + 40), radius=18,
                                     fill=hex_rgba(mix(tone, PAPER_LIGHT, .78), 235),
                                     outline=tone, width=3)
        plate.text((410, y), label, size=21, bold=True,
                   fill=DARK[tone], anchor="mm")
        _wrapped(plate, (450, y - 27, 630, y + 33), note, size=17,
                 fill=DARK[tone], bold=True)
    # Search wheel encodes that each structure gets a pass.
    center = (875, 505)
    for index, label in enumerate(("lines", "lungs", "bowel", "bones")):
        angle = -math.pi / 2 + index * math.pi / 2
        x = center[0] + math.cos(angle) * 135
        y = center[1] + math.sin(angle) * 135
        tone = TONES[index]
        plate.draw.ellipse((x - 45, y - 45, x + 45, y + 45),
                           fill=hex_rgba(LIGHTS[index], 150), outline=tone, width=4)
        plate.text((x, y), label, size=20, bold=True,
                   fill=DARK[tone], anchor="mm")
        plate.arrow(center, (x - math.cos(angle) * 55,
                             y - math.sin(angle) * 55), fill=tone, width=4, head=13)
    plate.draw.ellipse((820, 450, 930, 560), fill=PAPER_LIGHT,
                       outline=TEAL, width=5)
    plate.text(center, "whole\nstudy", size=20, bold=True, fill=DARK[TEAL], anchor="mm")
    plate.text((875, 715), "deliberate pass through the full study", size=20,
               bold=True, fill=DARK[TEAL], anchor="mm")
    # Clinical interpretation and safeguarding are parallel duties; a new
    # concern routes to the local pathway rather than implying a diagnosis.
    plate.draw.rounded_rectangle((1130, 350, 1470, 465), radius=22,
                                 fill=hex_rgba(GREEN_LIGHT, 150), outline=GREEN, width=4)
    plate.text((1300, 390), "answer the clinical question", size=21,
               bold=True, fill=DARK[GREEN], anchor="mm")
    plate.text((1300, 430), "lowest useful exposure", size=20,
               bold=True, fill=DARK[GREEN], anchor="mm")
    plate.draw.rounded_rectangle((1130, 570, 1470, 695), radius=22,
                                 fill=hex_rgba(CORAL_LIGHT, 150), outline=CORAL, width=4)
    plate.text((1300, 610), "pattern + history mismatch?", size=21,
               bold=True, fill=DARK[CORAL], anchor="mm")
    plate.text((1300, 655), "document → local pathway", size=20,
               bold=True, fill=DARK[CORAL], anchor="mm")
    _arrow(plate, (1300, 475), (1300, 555), "new concern", CORAL, offset=(92, 0))
    _caption(plate, (800, 795),
             "Paediatric imaging couples age-appropriate modality choice, a complete search, dose optimisation, and safeguarding duty.",
             INK, size=21)


def draw_child_abuse(plate: RadiologyPlate, _item: Mapping[str, object]) -> None:
    _tag(plate, (300, 195), "STANDARD SURVEY", BLUE)
    _tag(plate, (800, 195), "PATTERN + CONTEXT", CORAL)
    _tag(plate, (1300, 195), "DOCUMENT + ESCALATE", GREEN)
    _surface(plate, (90, 235, 510, 785), BLUE)
    # Region-specific, collimated named views replace a misleading generic
    # "paired projection" grid.  Exact local protocols remain authoritative.
    plate.draw.rounded_rectangle((125, 280, 475, 345), radius=14,
                                 fill=PAPER_LIGHT, outline=BLUE, width=3)
    plate.text((300, 317), "ID • date • side • projection", size=20,
               bold=True, fill=DARK[BLUE], anchor="mm")
    survey_rows = (
        "skull — frontal + lateral",
        "chest — frontal + rib obliques",
        "C/T/L spine — dedicated laterals",
        "abdomen + pelvis — frontal",
        "each limb / hand / foot — frontal",
    )
    for row, label in enumerate(survey_rows):
        y = 380 + row * 57
        plate.draw.ellipse((120, y - 9, 138, y + 9), fill=BLUE, outline=INK, width=2)
        plate.text((150, y), label, size=20, bold=True,
                   fill=DARK[BLUE], anchor="lm")
    plate.draw.rounded_rectangle((120, 628, 480, 764), radius=16,
                                 fill=hex_rgba(BLUE_LIGHT, 135), outline=BLUE, width=3)
    plate.text((300, 650), "no babygram • collimate each view", size=19,
               bold=True, fill=DARK[BLUE], anchor="mm")
    plate.text((300, 681), "≤24 mo: complete survey", size=19,
               bold=True, fill=DARK[BLUE], anchor="mm")
    plate.text((300, 712), "older child: targeted • local protocol", size=18,
               bold=True, fill=DARK[BLUE], anchor="mm")
    plate.text((300, 743), "10–14 d follow-up when indicated", size=18,
               bold=True, fill=DARK[BLUE], anchor="mm")

    _surface(plate, (550, 235, 1050, 785), CORAL)
    # Three bones show location, morphology and healing stage as a pattern,
    # not a single pathognomonic icon.
    for index, (x, label) in enumerate(((650, "site"), (800, "shape"), (950, "healing"))):
        plate.draw.rounded_rectangle((x - 24, 355, x + 24, 650), radius=20,
                                     fill=hex_rgba(GOLD_LIGHT, 135), outline=INK_SOFT, width=4)
        if index == 0:
            plate.draw.ellipse((x - 42, 410, x + 42, 490), outline=CORAL, width=7)
        elif index == 1:
            plate.polyline(((x - 28, 490), (x + 24, 450), (x - 18, 415)),
                           fill=CORAL, width=8)
        else:
            plate.draw.arc((x - 48, 415, x + 48, 545), 40, 320, fill=TEAL, width=10)
        plate.text((x, 690), label, size=21, bold=True,
                   fill=(DARK[CORAL] if index < 2 else DARK[TEAL]), anchor="mm")
    plate.text((800, 315), "multiple findings + clinical history", size=20,
               bold=True, fill=DARK[CORAL], anchor="mm")

    _surface(plate, (1090, 235, 1510, 785), GREEN)
    chain = (("structured report", BLUE), ("child-protection MDT", TEAL),
             ("local safeguarding action", CORAL))
    for index, (label, tone) in enumerate(chain):
        y = 320 + index * 155
        plate.draw.rounded_rectangle((1140, y, 1460, y + 90), radius=20,
                                     fill=hex_rgba(mix(tone, PAPER_LIGHT, .78), 235),
                                     outline=tone, width=4)
        plate.text((1300, y + 45), label, size=21, bold=True,
                   fill=DARK[tone], anchor="mm")
        if index < 2:
            plate.arrow((1300, y + 95), (1300, y + 145), fill=tone, width=6, head=17)
    _caption(plate, (800, 795),
             "No imaging sign alone establishes abuse: integrate the survey, history, examination, and multidisciplinary assessment.",
             INK, size=20)


def draw_paeds_masses_neuro(plate: RadiologyPlate, _item: Mapping[str, object]) -> None:
    _surface(plate, (85, 230, 520, 785), BLUE)
    _surface(plate, (565, 230, 1035, 785), CORAL)
    _surface(plate, (1080, 230, 1515, 785), TEAL)
    _tag(plate, (302, 270), "AGE PRIOR", BLUE)
    _tag(plate, (800, 270), "ORGAN OF ORIGIN", CORAL)
    _tag(plate, (1297, 270), "ACOUSTIC WINDOW", TEAL)
    # Named, coarse age bands convey a prior without pretending to be an
    # incidence graph.  The examples deliberately overlap across bands.
    age_rows = (
        ("INFANT", "neuroblastoma\nhepatoblastoma", BLUE, 350),
        ("YOUNG CHILD", "Wilms tumour\nneuroblastoma", CORAL, 480),
        ("OLDER CHILD", "lymphoma\nsarcoma", TEAL, 610),
    )
    for age, examples, tone, y in age_rows:
        plate.draw.rounded_rectangle((115, y, 490, y + 105), radius=20,
                                     fill=hex_rgba(mix(tone, PAPER_LIGHT, .84), 230),
                                     outline=tone, width=3)
        plate.text((302, y + 25), age, size=20, bold=True,
                   fill=DARK[tone], anchor="mm")
        plate.text((302, y + 72), examples.replace("\n", " • "), size=20, bold=True,
                   fill=INK_SOFT, anchor="mm")
    plate.text((302, 745), "age shifts the differential • not diagnosis", size=19,
               bold=True, fill=DARK[BLUE], anchor="mm")
    # A mass displaces organs away from its origin; displacement, a claw sign,
    # and vessel relationships are then traced back as an inference.
    plate.draw.rounded_rectangle((650, 345, 950, 650), radius=100,
                                 fill=hex_rgba(GOLD_LIGHT, 65), outline=INK_SOFT, width=4)
    plate.draw.ellipse((690, 440, 835, 585), fill=hex_rgba(CORAL_LIGHT, 175),
                       outline=CORAL, width=5)
    plate.draw.ellipse((615, 430, 695, 545), fill=hex_rgba(BLUE_LIGHT, 130),
                       outline=BLUE, width=4)
    plate.draw.ellipse((915, 450, 995, 565), fill=hex_rgba(TEAL_LIGHT, 130),
                       outline=TEAL, width=4)
    plate.arrow((705, 500), (655, 485), fill=BLUE, width=6, head=17)
    plate.arrow((825, 515), (955, 510), fill=TEAL, width=6, head=17)
    plate.draw.ellipse((700, 492, 720, 512), fill=GOLD, outline=INK, width=2)
    plate.dashed_line((710, 502), (805, 675), fill=CORAL, width=4, dash=10, gap=7)
    plate.text((800, 690), "displacement + claw + vessels → infer origin", size=20,
               bold=True, fill=DARK[CORAL], anchor="mm")
    # Fontanelle and posterior-element windows are separate, age-limited uses.
    plate.draw.ellipse((1170, 325, 1425, 505), fill=hex_rgba(BLUE_LIGHT, 80),
                       outline=INK_SOFT, width=5)
    plate.draw.polygon(((1275, 300), (1315, 300), (1295, 340)),
                       fill=TEAL, outline=INK)
    for end_x in (1215, 1295, 1375):
        plate.draw.line((1295, 335, end_x, 475), fill=hex_rgba(TEAL, 170), width=5)
    plate.text((1295, 525), "fontanelle — infant brain", size=20,
               bold=True, fill=DARK[TEAL], anchor="mm")
    plate.draw.line((1120, 552, 1470, 552), fill=GRID, width=3)
    plate.draw.arc((1190, 610, 1400, 735), 180, 360, fill=PLUM, width=9)
    plate.draw.polygon(((1275, 570), (1315, 570), (1295, 610)),
                       fill=TEAL, outline=INK)
    plate.draw.line((1295, 605, 1295, 690), fill=hex_rgba(TEAL, 170), width=5)
    plate.text((1295, 725), "posterior elements — early infancy", size=20,
               bold=True, fill=DARK[PLUM], anchor="mm")
    plate.text((1295, 755), "closed / equivocal → MRI", size=20,
               bold=True, fill=DARK[TEAL], anchor="ms")
    _caption(plate, (800, 795),
             "Age alters the prior; displaced anatomy localises origin; paediatric acoustic windows can answer focused questions safely.",
             INK, size=21)


def draw_paeds_chest(plate: RadiologyPlate, _item: Mapping[str, object]) -> None:
    _surface(plate, (70, 225, 700, 785), BLUE)
    _surface(plate, (720, 225, 1110, 785), CORAL)
    _surface(plate, (1130, 225, 1530, 785), TEAL)
    _tag(plate, (385, 265), "DEVICE + LANDMARK", BLUE)
    _tag(plate, (915, 265), "AIR-LEAK SHAPE", CORAL)
    _tag(plate, (1330, 265), "VOLUME + OPACITY", TEAL)
    # A compact babygram abstraction with a vertebral range key.  Tip dots and
    # direct labels matter more than the stylised anatomy.
    plate.draw.ellipse((235, 315, 535, 690), fill=hex_rgba(BLUE_LIGHT, 55),
                       outline=INK_SOFT, width=5)
    plate.draw.ellipse((255, 365, 370, 600), fill=hex_rgba(BLUE_LIGHT, 100),
                       outline=BLUE, width=4)
    plate.draw.ellipse((400, 365, 515, 600), fill=hex_rgba(BLUE_LIGHT, 100),
                       outline=BLUE, width=4)
    carina = (385, 430)
    plate.draw.line((385, 300, 385, 430), fill=INK_SOFT, width=10)
    plate.draw.line((385, 430, 335, 480), fill=INK_SOFT, width=8)
    plate.draw.line((385, 430, 435, 480), fill=INK_SOFT, width=8)
    plate.dashed_line((225, 555), (545, 555), fill=GRID, width=3, dash=10, gap=7)
    plate.text((225, 575), "diaphragm", size=20, bold=True,
               fill=INK_SOFT, anchor="lm")
    # Vertebral labels are a range guide, not a claim about one exact pixel.
    level_y = (("T4", 400), ("T6", 470), ("T8", 535), ("T9", 570))
    plate.draw.line((600, 350, 600, 600), fill=INK_SOFT, width=4)
    for level, y in level_y:
        plate.draw.line((585, y, 615, y), fill=INK_SOFT, width=3)
        plate.text((625, y), level, size=20, bold=True, fill=INK_SOFT, anchor="lm")

    # ETT in neutral head position: tip above carina.
    plate.draw.line((365, 285, 365, 385), fill=CORAL, width=7)
    plate.draw.ellipse((354, 374, 376, 396), fill=CORAL, outline=INK, width=2)
    plate.text((105, 340), "ETT: above carina", size=20, bold=True,
               fill=DARK[CORAL], anchor="lm")
    plate.text((105, 370), "check neutral head", size=19, bold=True,
               fill=DARK[CORAL], anchor="lm")
    plate.dashed_line((235, 385), (354, 385), fill=CORAL, width=3, dash=8, gap=6)

    # Enteric tube: tip and side-port are both shown below the diaphragm.
    plate.polyline(((410, 285), (410, 625), (480, 665)), fill=TEAL, width=7)
    plate.draw.ellipse((399, 604, 421, 626), fill=PAPER_LIGHT, outline=TEAL, width=4)
    plate.draw.ellipse((469, 654, 491, 676), fill=TEAL, outline=INK, width=2)
    plate.draw.arc((420, 615, 535, 710), 170, 350, fill=INK_SOFT, width=4)
    plate.text((445, 720), "enteric tip + side-port below diaphragm", size=19,
               bold=True, fill=DARK[TEAL], anchor="mm")

    # UVC approaches the inferior cavoatrial junction; UAC first descends into
    # an iliac artery before ascending in the aorta.  A high UAC is shown.
    plate.polyline(((370, 745), (370, 640), (430, 565), (430, 545)),
                   fill=PLUM, width=7)
    plate.draw.ellipse((419, 534, 441, 556), fill=PLUM, outline=INK, width=2)
    plate.text((105, 610), "UVC: IVC–RA junction", size=20, bold=True,
               fill=DARK[PLUM], anchor="lm")
    plate.dashed_line((275, 610), (420, 550), fill=PLUM, width=3, dash=8, gap=6)
    plate.polyline(((385, 745), (340, 775), (340, 650), (350, 495)),
                   fill=GOLD, width=7)
    plate.draw.ellipse((339, 484, 361, 506), fill=GOLD, outline=INK, width=2)
    plate.text((465, 455), "high UAC: T6–T9", size=20, bold=True,
               fill=DARK[GOLD], anchor="lm")
    plate.text((465, 485), "low option: L3–L5", size=19, bold=True,
               fill=DARK[GOLD], anchor="lm")
    plate.dashed_line((360, 495), (455, 465), fill=GOLD, width=3, dash=8, gap=6)
    # Three different air distributions, each named directly rather than by
    # colour alone.
    air_rows = (("PLEURAL", "line; no peripheral markings", CORAL, 365),
                ("MEDIASTINAL", "air outlines mediastinum", PLUM, 510),
                ("INTERSTITIAL", "linear + cystic lucencies", GOLD, 655))
    for label, detail, tone, y in air_rows:
        if label == "PLEURAL":
            plate.draw.arc((755, y - 60, 835, y + 60), 80, 280, fill=tone, width=8)
            plate.draw.line((745, y - 55, 745, y + 55), fill=GRID, width=3)
        elif label == "MEDIASTINAL":
            plate.draw.arc((750, y - 55, 845, y + 55), 185, 355, fill=tone, width=8)
            plate.draw.arc((765, y - 35, 830, y + 35), 5, 175, fill=tone, width=5)
        else:
            for dx, dy, radius in ((0, 0, 12), (35, -24, 16), (45, 24, 11),
                                   (-28, 30, 14), (-35, -25, 10)):
                plate.draw.ellipse((795 + dx - radius, y + dy - radius,
                                    795 + dx + radius, y + dy + radius),
                                   outline=tone, width=5)
        plate.text((870, y - 18), label, size=21, bold=True,
                   fill=DARK[tone], anchor="lm")
        _wrapped(plate, (870, y + 5, 1090, y + 65), detail, size=17,
                 fill=INK_SOFT, bold=True)
    # Lung-volume ruler plus explicit focal and diffuse opacity encodings.
    plate.text((1190, 330), "VOLUME", size=21, bold=True,
               fill=DARK[TEAL], anchor="mm")
    plate.draw.line((1190, 365, 1190, 650), fill=INK, width=4)
    for y in range(385, 651, 53):
        plate.draw.line((1175, y, 1205, y), fill=INK, width=3)
    plate.text((1215, 385), "high", size=20, bold=True, fill=INK_SOFT, anchor="lm")
    plate.text((1215, 645), "low", size=20, bold=True, fill=INK_SOFT, anchor="lm")
    plate.draw.ellipse((1280, 355, 1480, 665), fill=hex_rgba(TEAL_LIGHT, 70),
                       outline=TEAL, width=5)
    plate.draw.ellipse((1320, 410, 1385, 475), fill=hex_rgba(CORAL, 125),
                       outline=CORAL, width=4)
    for x, y in ((1425, 420), (1395, 515), (1450, 570), (1350, 600)):
        plate.draw.ellipse((x - 14, y - 14, x + 14, y + 14),
                           fill=hex_rgba(BLUE, 95), outline=BLUE, width=3)
    plate.text((1352, 690), "FOCAL", size=20, bold=True,
               fill=DARK[CORAL], anchor="mm")
    plate.text((1440, 690), "DIFFUSE", size=20, bold=True,
               fill=DARK[BLUE], anchor="mm")
    plate.text((1330, 735), "age + volume + distribution", size=20,
               bold=True, fill=DARK[TEAL], anchor="mm")
    _caption(plate, (800, 795),
             "Trace every device to a landmark, then classify air-leak shape and lung pattern in the context of age and volume.",
             INK, size=21)


def draw_paeds_abdomen(plate: RadiologyPlate, _item: Mapping[str, object]) -> None:
    headings = (("SERIAL RADIOGRAPH", BLUE), ("DYNAMIC ULTRASOUND", TEAL),
                ("SURGICAL RED FLAG", CORAL))
    for index, (heading, tone) in enumerate(headings):
        left = 85 + index * 505
        _surface(plate, (left, 230, left + 470, 785), tone)
        _tag(plate, (left + 235, 270), heading, tone, size=18)
    # Gas pattern with serial arrow and free-air crescent.
    for frame, offset in enumerate((0, 145)):
        x0 = 125 + offset
        plate.draw.rounded_rectangle((x0, 355, x0 + 125, 630), radius=46,
                                     fill=hex_rgba(BLUE_LIGHT, 70), outline=BLUE, width=3)
        for index in range(4):
            y = 415 + index * 48
            plate.draw.arc((x0 + 30, y - 20, x0 + 100, y + 25), 0, 360,
                           fill=TEAL if frame == 0 else CORAL, width=5)
        plate.draw.arc((x0 + 20, 330, x0 + 105, 400), 190, 350,
                       fill=CORAL if frame else GRID, width=7)
    _arrow(plate, (252, 500), (270, 500), "time", BLUE, offset=(0, -32), width=5)
    plate.text((320, 690), "gas distribution + free air can evolve", size=18,
               bold=True, fill=DARK[BLUE], anchor="mm")
    # Compression and Doppler/perfusion as separate ultrasound tests.
    plate.draw.ellipse((660, 400, 930, 650), outline=TEAL, width=7)
    plate.draw.rounded_rectangle((720, 450, 870, 585), radius=55,
                                 fill=hex_rgba(TEAL_LIGHT, 110), outline=TEAL, width=5)
    plate.arrow((795, 350), (795, 455), fill=CORAL, width=8, head=21)
    plate.text((795, 335), "compression", size=18, bold=True,
               fill=DARK[CORAL], anchor="mm")
    for index, tone in enumerate((BLUE, CORAL, BLUE, CORAL)):
        plate.draw.line((690 + index * 65, 630, 720 + index * 65, 600),
                        fill=tone, width=5)
    plate.text((800, 690), "shape + compressibility + perfusion", size=18,
               bold=True, fill=DARK[TEAL], anchor="mm")
    # Whirlpool/closed-loop geometry and explicit escalation arrow.
    for radius in (130, 95, 60, 28):
        plate.draw.arc((1300 - radius, 520 - radius, 1300 + radius, 520 + radius),
                       20, 315, fill=CORAL if radius % 2 else PLUM, width=7)
    plate.arrow((1300, 525), (1465, 370), fill=CORAL, width=8, head=22)
    _tag(plate, (1370, 335), "DO NOT DELAY", CORAL, size=18)
    plate.text((1300, 700), "volvulus • perforation • ischaemia", size=18,
               bold=True, fill=DARK[CORAL], anchor="mm")
    _caption(plate, (800, 795),
             "Choose the test by mechanism and age; a surgical red flag triggers escalation while imaging is completed.",
             INK, size=21)


def draw_nuclear_general(plate: RadiologyPlate, _item: Mapping[str, object]) -> None:
    headings = (("BONE / V-Q", BLUE), ("THYROID", TEAL),
                ("SENTINEL NODE", CORAL))
    for index, (heading, tone) in enumerate(headings):
        left = 85 + index * 505
        _surface(plate, (left, 230, left + 470, 785), tone)
        _tag(plate, (left + 235, 270), heading, tone)
    # Bone turnover and V/Q answer different questions.  V and Q are separate,
    # directly labelled congruent maps so the mismatch is not colour-dependent.
    plate.text((185, 330), "DELAYED BONE", size=20, bold=True,
               fill=DARK[BLUE], anchor="mm")
    plate.draw.line((185, 390, 185, 635), fill=INK_SOFT, width=16)
    plate.draw.ellipse((145, 350, 225, 430), outline=INK_SOFT, width=9)
    plate.draw.ellipse((145, 610, 225, 690), outline=INK_SOFT, width=9)
    for y in (430, 510, 590):
        plate.draw.ellipse((168, y - 12, 202, y + 22), fill=BLUE, outline=INK, width=2)
    plate.text((185, 735), "osteoblastic turnover", size=19, bold=True,
               fill=DARK[BLUE], anchor="mm")
    for x, label, tone in ((340, "V", TEAL), (470, "Q", CORAL)):
        plate.text((x, 350), label, size=24, bold=True,
                   fill=DARK[tone], anchor="mm")
        plate.draw.ellipse((x - 52, 385, x + 52, 620),
                           fill=hex_rgba(mix(tone, PAPER_LIGHT, .74), 150),
                           outline=tone, width=5)
    # Same upper-zone coordinate: ventilation is preserved, perfusion absent.
    plate.draw.ellipse((315, 435, 365, 490), fill=TEAL, outline=TEAL, width=4)
    plate.draw.ellipse((445, 435, 495, 490), fill=PAPER_LIGHT, outline=CORAL, width=5)
    plate.dashed_line((365, 462), (445, 462), fill=INK_SOFT, width=3, dash=8, gap=6)
    plate.text((405, 675), "Q defect + preserved V", size=20, bold=True,
               fill=DARK[CORAL], anchor="mm")
    plate.text((405, 710), "= mismatch pattern", size=20, bold=True,
               fill=DARK[TEAL], anchor="mm")

    # Thyroid distribution plus an explicit time axis; uptake is function, not
    # a histological diagnosis.
    plate.draw.ellipse((710, 390, 800, 585), fill=hex_rgba(TEAL, 120),
                       outline=TEAL, width=5)
    plate.draw.ellipse((800, 390, 890, 585), fill=hex_rgba(TEAL, 120),
                       outline=TEAL, width=5)
    plate.draw.rectangle((785, 455, 815, 525), fill=TEAL)
    for x, y in ((750, 430), (840, 465), (765, 535), (850, 550)):
        plate.draw.ellipse((x - 10, y - 10, x + 10, y + 10), fill=GOLD)
    plate.arrow((675, 650), (930, 650), fill=INK, width=4, head=13)
    plate.text((695, 625), "earlier", size=19, bold=True, fill=INK_SOFT, anchor="mm")
    plate.text((910, 625), "later", size=19, bold=True, fill=INK_SOFT, anchor="mm")
    plate.text((800, 692), "relative distribution + function", size=20,
               bold=True, fill=DARK[TEAL], anchor="mm")
    plate.text((800, 730), "timing matters • not histology", size=20,
               bold=True, fill=INK_SOFT, anchor="mm")
    # Injection-to-first-echelon-node drainage path.
    plate.draw.ellipse((1135, 570, 1195, 630), fill=CORAL, outline=INK, width=3)
    plate.text((1165, 665), "INJECTION", size=20, bold=True,
               fill=DARK[CORAL], anchor="mm")
    path = ((1195, 600), (1270, 540), (1340, 565), (1420, 455))
    plate.draw.line(path, fill=TEAL, width=8, joint="curve")
    plate.text((1320, 485), "LYMPHATIC CHANNEL", size=19, bold=True,
               fill=DARK[TEAL], anchor="mm")
    for index, (x, y) in enumerate(((1270, 540), (1340, 565), (1420, 455))):
        plate.draw.ellipse((x - 21, y - 21, x + 21, y + 21),
                           fill=GOLD if index == 0 else PAPER_LIGHT,
                           outline=CORAL, width=4)
        plate.text((x, y), str(index + 1), size=20, bold=True,
                   fill=INK, anchor="mm")
    plate.dashed_line((1270, 515), (1270, 390), fill=GOLD, width=3, dash=8, gap=6)
    plate.text((1270, 365), "SENTINEL NODE(S)", size=20, bold=True,
               fill=DARK[GOLD], anchor="mm")
    plate.text((1320, 700), "first-echelon node(s)", size=20,
               bold=True, fill=DARK[CORAL], anchor="mm")
    plate.text((1320, 735), "within the draining basin", size=19,
               bold=True, fill=INK_SOFT, anchor="mm")
    _caption(plate, (800, 795),
             "A tracer map is interpreted by its target, route, and time pattern—not by brightness alone.",
             INK, size=21)


def draw_pet_ct(plate: RadiologyPlate, _item: Mapping[str, object]) -> None:
    _surface(plate, (90, 225, 1510, 785), PLUM)
    _tag(plate, (300, 265), "PREPARE", BLUE)
    _tag(plate, (800, 265), "REGISTER PHYSIOLOGY + ANATOMY", TEAL, size=19)
    _tag(plate, (1300, 265), "PROPORTIONATE ACTION", CORAL)
    plate.draw.line((535, 300, 535, 745), fill=GRID, width=3)
    plate.draw.line((1085, 300, 1085, 745), fill=GRID, width=3)
    # A clinically explicit preparation sequence.  "Measure glucose" cannot
    # be mistaken for administering glucose before FDG.
    prep = (("FAST + WATER", BLUE), ("MEASURE GLUCOSE", TEAL),
            ("INJECT FDG", GOLD), ("WARM, QUIET UPTAKE", CORAL))
    for index, (label, tone) in enumerate(prep):
        y = 320 + index * 95
        plate.draw.rounded_rectangle((130, y, 490, y + 62), radius=16,
                                     fill=hex_rgba(mix(tone, PAPER_LIGHT, .82), 235),
                                     outline=tone, width=3)
        plate.text((310, y + 31), label, size=21, bold=True,
                   fill=DARK[tone], anchor="mm")
        if index < len(prep) - 1:
            plate.arrow((310, y + 66), (310, y + 90), fill=tone, width=5, head=13)
    plate.text((310, 712), "record therapy / inflammation", size=18,
               bold=True, fill=DARK[BLUE], anchor="mm")
    plate.text((310, 742), "muscle activity • diabetes protocol", size=18,
               bold=True, fill=INK_SOFT, anchor="mm")
    # Co-registered axial pair and fused view; same focus shares coordinates.
    centers = ((650, 470), (810, 470), (970, 470))
    labels = ("CT anatomy", "PET uptake", "fused")
    for index, ((x, y), label) in enumerate(zip(centers, labels)):
        plate.draw.ellipse((x - 67, y - 92, x + 67, y + 92),
                           fill=hex_rgba(BLUE_LIGHT if index != 1 else PLUM_LIGHT, 110),
                           outline=BLUE if index != 1 else PLUM, width=4)
        plate.draw.ellipse((x + 10, y - 5, x + 42, y + 27),
                           fill=CORAL if index else PAPER_LIGHT,
                           outline=CORAL, width=4)
        plate.text((x, 600), label, size=20, bold=True,
                   fill=DARK[TEAL] if index == 2 else INK_SOFT, anchor="mm")
        if index < 2:
            plate.arrow((x + 75, y), (centers[index + 1][0] - 75, y),
                        fill=TEAL, width=4, head=12)
    plate.text((810, 650), "motion / breathing → check misregistration", size=20,
               bold=True, fill=DARK[CORAL], anchor="mm")
    plate.text((810, 695), "expected physiology is not tumour by itself", size=20,
               bold=True, fill=DARK[TEAL], anchor="mm")
    # Stage-changing and incidental uptake route to explicit, different actions.
    actions = (("STAGE-CHANGING", ("MDT /", "management"), CORAL, 1195),
               ("INCIDENTAL", ("correlate /", "follow if needed"), GOLD, 1400))
    for label, action, tone, x in actions:
        plate.draw.rounded_rectangle((x - 95, 350, x + 95, 435), radius=18,
                                     fill=hex_rgba(mix(tone, PAPER_LIGHT, .76), 220),
                                     outline=tone, width=4)
        plate.text((x, 392), label, size=18, bold=True,
                   fill=DARK[tone], anchor="mm")
        plate.arrow((x, 445), (x, 535), fill=tone, width=6, head=18)
        plate.draw.rounded_rectangle((x - 95, 550, x + 95, 655), radius=18,
                                     fill=PAPER_LIGHT, outline=tone, width=4)
        plate.text((x, 585), action[0], size=19, bold=True,
                   fill=DARK[tone], anchor="mm")
        plate.text((x, 621), action[1], size=19, bold=True,
                   fill=DARK[tone], anchor="mm")
    plate.text((1300, 710), "uptake pattern + clinical context", size=20,
               bold=True, fill=INK_SOFT, anchor="mm")
    _caption(plate, (800, 795),
             "FDG uptake is nonspecific: preparation, timing, registration, anatomy, and expected physiology determine its meaning.",
             INK, size=21)


def draw_theranostics(plate: RadiologyPlate, _item: Mapping[str, object]) -> None:
    _surface(plate, (80, 225, 1520, 785), PLUM)
    _tag(plate, (300, 265), "ELIGIBILITY GATE", BLUE)
    _tag(plate, (800, 265), "SAME MOLECULAR TARGET", PLUM)
    _tag(plate, (1300, 265), "DOSIMETRY + FOLLOW-UP", TEAL)
    # Uptake is one input among several, not an automatic eligibility switch.
    criteria = (("clinical indication / disease", BLUE),
                ("target-positive distribution", TEAL),
                ("discordant disease?", PLUM),
                ("organ function / reserve", GOLD),
                ("prior therapy + criteria", CORAL))
    for index, (label, tone) in enumerate(criteria):
        y = 310 + index * 82
        plate.draw.rounded_rectangle((110, y, 445, y + 58), radius=16,
                                     fill=hex_rgba(mix(tone, PAPER_LIGHT, .80), 235),
                                     outline=tone, width=3)
        plate.text((277, y + 29), label, size=20, bold=True,
                   fill=DARK[tone], anchor="mm")
        plate.arrow((450, y + 29), (515, 500), fill=tone, width=4, head=13)
    plate.draw.polygon(((515, 500), (565, 445), (615, 500), (565, 555)),
                       fill=hex_rgba(BLUE_LIGHT, 160), outline=BLUE)
    plate.text((565, 500), "gate", size=21, bold=True, fill=DARK[BLUE], anchor="mm")
    # The molecular target is shared; exact ligand, radionuclide and
    # biodistribution remain agent-specific.
    for x, isotope, tone, label in ((710, "β+ / γ", BLUE, "image payload"),
                                    (930, "β− / α", CORAL, "therapy payload")):
        plate.draw.ellipse((x - 42, 365, x + 42, 449), fill=tone,
                           outline=INK, width=3)
        plate.text((x, 407), isotope, size=20, bold=True, fill=PAPER_LIGHT, anchor="mm")
        plate.draw.line((x, 449, x, 515), fill=PLUM, width=8)
        plate.draw.polygon(((x - 38, 515), (x + 38, 515), (x + 18, 565),
                            (x - 18, 565)), fill=hex_rgba(PLUM_LIGHT, 180), outline=PLUM)
        plate.draw.arc((x - 70, 530, x + 70, 680), 190, 350, fill=TEAL, width=12)
        plate.text((x, 710), label, size=20, bold=True, fill=DARK[tone], anchor="mm")
    plate.draw.line((710, 330, 930, 330), fill=PLUM, width=5)
    plate.text((820, 315), "same target • paired agent may differ", size=20, bold=True,
               fill=DARK[PLUM], anchor="mm")
    plate.text((820, 750), "PET β+ or SPECT γ • therapy β− or α", size=19,
               bold=True, fill=INK_SOFT, anchor="mm")
    # Equal checklist lanes avoid implying invented dose or risk rankings.
    follow_up = (
        ("POST-THERAPY MAP", "distribution • dosimetry when used", BLUE),
        ("CBC / MARROW", "blood count + marrow reserve", TEAL),
        ("RENAL ± SALIVARY", "agent-specific toxicity review", GOLD),
        ("RESPONSE + SAFETY", "restaging • individual advice", CORAL),
    )
    for index, (label, detail, tone) in enumerate(follow_up):
        y = 320 + index * 105
        plate.draw.rounded_rectangle((1115, y, 1490, y + 82), radius=18,
                                     fill=hex_rgba(mix(tone, PAPER_LIGHT, .83), 230),
                                     outline=tone, width=3)
        plate.text((1140, y + 25), label, size=20, bold=True,
                   fill=DARK[tone], anchor="lm")
        plate.text((1140, y + 58), detail, size=19, bold=True,
                   fill=INK_SOFT, anchor="lm")
    _caption(plate, (800, 795),
             "Target uptake informs eligibility; agent-specific treatment, monitoring, response, and radiation-safety advice complete the system.",
             INK, size=20)


RENDERERS: Dict[str, Renderer] = {
    "rad.5.ankle-foot": draw_ankle_foot,
    "rad.5.marrow-muscle": draw_marrow_muscle,
    "rad.5.bone-tumours": draw_bone_tumours,
    "rad.3.fracture-description": draw_fracture_description,
    "rad.5.hip": draw_hip,
    "rad.5.knee": draw_knee,
    "rad.5.msk-mri": draw_msk_mri,
    "rad.5.shoulder": draw_shoulder,
    "rad.4.arthritis": draw_arthritis,
    "rad.5.wrist-hand": draw_wrist_hand,
    "rad.5.paeds-hip-elbow": draw_paeds_hip_elbow,
    "rad.4.paediatric": draw_paediatric,
    "rad.5.child-abuse": draw_child_abuse,
    "rad.5.paeds-masses-neuro": draw_paeds_masses_neuro,
    "rad.5.paeds-chest": draw_paeds_chest,
    "rad.5.paeds-abdomen": draw_paeds_abdomen,
    "rad.5.nuclear-general": draw_nuclear_general,
    "rad.5.pet-ct": draw_pet_ct,
    "rad.5.theranostics": draw_theranostics,
}


__all__ = ["RENDERERS"]
