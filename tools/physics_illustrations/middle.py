"""Explanatory physics plates for the Sapling and Tree lessons."""

from __future__ import annotations

import math

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
    Plate,
    Spec,
    arrow_label,
    axes,
    cart,
    centered_note,
    energy_bar,
    footer,
    hex_rgba,
    panel,
    particle_box,
    plot_curve,
    spec,
    thermometer,
    three_panel_boxes,
    two_panel_boxes,
    wave,
)


def _block(plate: Plate, center: tuple[float, float], label: str,
           *, fill: str = BLUE_LIGHT, outline: str = BLUE) -> None:
    x, y = center
    plate.draw.rounded_rectangle((x - 70, y - 55, x + 70, y + 55), radius=14,
                                 fill=fill, outline=outline, width=4)
    plate.text((x, y), label, size=23, bold=True, anchor="mm")


def _vertical_force(plate: Plate, x: float, y: float, magnitude: float,
                    label: str, upward: bool, color: str) -> None:
    end_y = y - magnitude if upward else y + magnitude
    arrow_label(plate, (x, y), (x, end_y), label, fill=color, width=7,
                offset=(68, 0))


def draw_forces(plate: Plate) -> None:
    for box, heading in zip(three_panel_boxes(), ("RESTING", "ACCELERATING", "TERMINAL SPEED")):
        panel(plate, box, heading)
    _block(plate, (332, 520), "book", fill=GOLD_LIGHT, outline=GOLD)
    plate.draw.line((180, 582, 484, 582), fill=INK, width=8)
    _vertical_force(plate, 332, 465, 115, "normal 10 N", True, TEAL)
    _vertical_force(plate, 332, 575, 115, "weight 10 N", False, CORAL)
    plate.text((332, 742), "ΣF = 0 → a = 0", size=22, bold=True, anchor="mm")

    _block(plate, (800, 520), "crate")
    arrow_label(plate, (730, 520), (642, 520), "friction 4 N", fill=CORAL, width=7)
    arrow_label(plate, (870, 520), (970, 520), "push 9 N", fill=TEAL, width=7)
    plate.text((800, 664), "ΣF = 5 N right", size=22, bold=True, anchor="mm")
    plate.text((800, 742), "speed changes", size=21, anchor="mm")

    plate.draw.ellipse((1224, 425, 1312, 513), fill=PLUM_LIGHT, outline=PLUM, width=4)
    plate.draw.line((1268, 513, 1268, 615), fill=PLUM, width=8)
    plate.draw.line((1268, 548, 1208, 590), fill=PLUM, width=7)
    plate.draw.line((1268, 548, 1328, 590), fill=PLUM, width=7)
    _vertical_force(plate, 1268, 452, 105, "drag", True, TEAL)
    _vertical_force(plate, 1268, 615, 105, "weight", False, CORAL)
    plate.text((1268, 742), "moving with ΣF = 0", size=21, bold=True, anchor="mm")
    footer(plate, "Zero net force means constant velocity—not necessarily rest.", size=28)


def draw_gravity(plate: Plate) -> None:
    for box, heading in zip(three_panel_boxes(), ("MASS", "WEIGHT", "ORBIT")):
        panel(plate, box, heading)
    _block(plate, (332, 488), "10 kg", fill=GOLD_LIGHT, outline=GOLD)
    plate.text((332, 630), "same amount of matter", size=20, bold=True, anchor="mm")
    centered_note(plate, (172, 682, 492, 776), "Mass stays 10 kg on Earth, Moon, or in orbit.", size=19)

    plate.draw.ellipse((660, 410, 790, 540), fill=BLUE_LIGHT, outline=BLUE, width=4)
    plate.draw.ellipse((846, 438, 948, 540), fill=GRID, outline=INK_SOFT, width=4)
    plate.text((725, 574), "Earth", size=19, bold=True, anchor="mm")
    plate.text((897, 574), "Moon", size=19, bold=True, anchor="mm")
    plate.text((725, 630), "98 N", size=28, bold=True, fill=CORAL, anchor="mm")
    plate.text((897, 630), "16 N", size=28, bold=True, fill=CORAL, anchor="mm")
    plate.text((800, 720), "W = mg", size=25, bold=True, math_face=True, anchor="mm")

    plate.draw.ellipse((1162, 394, 1374, 606), fill=BLUE_LIGHT, outline=BLUE, width=5)
    plate.dot((1420, 500), 18, fill=GOLD_LIGHT, outline=GOLD, width=4)
    arrow_label(plate, (1415, 500), (1358, 500), "gravity", fill=CORAL, width=7)
    arrow_label(plate, (1420, 500), (1420, 405), "sideways speed", fill=TEAL, width=7,
                offset=(-78, 0))
    plate.draw.arc((1115, 348, 1421, 654), 270, 90, fill=PLUM, width=5)
    plate.text((1268, 720), "continuous free fall", size=21, bold=True, anchor="mm")
    footer(plate, "Gravity changes weight and bends motion; it does not change mass.", size=27)


def _battery(plate: Plate, x: float, y: float) -> None:
    # A battery in a vertical branch needs horizontal plates and a real gap in
    # the surrounding wire. The longer plate is the positive terminal.
    plate.draw.line((x - 34, y - 12, x + 34, y - 12), fill=INK, width=5)
    plate.draw.line((x - 22, y + 12, x + 22, y + 12), fill=INK, width=8)
    plate.text((x - 52, y - 25), "+", size=21, bold=True)


def _bulb(plate: Plate, x: float, y: float, label: str = "") -> None:
    plate.draw.ellipse((x - 30, y - 30, x + 30, y + 30), fill=GOLD_LIGHT,
                       outline=GOLD, width=4)
    plate.draw.line((x - 18, y - 18, x + 18, y + 18), fill=GOLD, width=4)
    plate.draw.line((x + 18, y - 18, x - 18, y + 18), fill=GOLD, width=4)
    if label:
        plate.text((x, y + 48), label, size=17, anchor="ma")


def draw_electricity(plate: Plate) -> None:
    for box, heading in zip(three_panel_boxes(), ("OPEN", "SERIES", "PARALLEL")):
        panel(plate, box, heading)
    # Open circuit
    plate.draw.line((180, 528, 180, 430, 280, 430), fill=INK, width=6)
    plate.draw.line((180, 552, 180, 650, 472, 650, 472, 570), fill=INK, width=6)
    plate.draw.line((472, 510, 472, 430, 380, 430), fill=INK, width=6)
    plate.draw.line((280, 430, 342, 384), fill=CORAL, width=7)
    _battery(plate, 180, 540)
    _bulb(plate, 472, 540, "off")
    plate.text((332, 730), "no closed path → I = 0", size=20, bold=True, anchor="mm")
    # Series
    plate.draw.line((632, 523, 632, 410, 728, 410), fill=INK, width=6)
    plate.draw.line((788, 410, 854, 410), fill=INK, width=6)
    plate.draw.line((914, 410, 968, 410, 968, 660, 632, 660, 632, 547), fill=INK, width=6)
    _battery(plate, 632, 535)
    _bulb(plate, 758, 410, "V₁")
    _bulb(plate, 884, 410, "V₂")
    plate.text((800, 730), "V = V₁ + V₂", size=21, bold=True, anchor="mm", math_face=True)
    # Parallel
    plate.draw.line((1100, 523, 1100, 410, 1436, 410, 1436, 660, 1100, 660, 1100, 547), fill=INK, width=6)
    _battery(plate, 1100, 535)
    plate.draw.line((1200, 410, 1200, 505), fill=INK, width=5)
    plate.draw.line((1200, 565, 1200, 660), fill=INK, width=5)
    plate.draw.line((1332, 410, 1332, 505), fill=INK, width=5)
    plate.draw.line((1332, 565, 1332, 660), fill=INK, width=5)
    _bulb(plate, 1200, 535, "branch 1")
    _bulb(plate, 1332, 535, "branch 2")
    plate.text((1268, 730), "I = I₁ + I₂", size=21, bold=True, anchor="mm", math_face=True)
    footer(plate, "Current needs a closed path; voltage and current divide by circuit topology.", size=26)


def draw_heat(plate: Plate) -> None:
    for box, heading in zip(three_panel_boxes(), ("CONDUCTION", "CONVECTION", "RADIATION")):
        panel(plate, box, heading)
    plate.draw.rounded_rectangle((166, 455, 500, 545), radius=12, fill=BLUE_LIGHT,
                                 outline=BLUE, width=4)
    plate.draw.rounded_rectangle((166, 455, 280, 545), radius=12, fill=CORAL_LIGHT,
                                 outline=CORAL, width=4)
    for x in range(205, 475, 48):
        plate.dot((x, 500), 10, fill=CORAL_LIGHT if x < 310 else BLUE_LIGHT,
                  outline=CORAL if x < 310 else BLUE, width=2)
    arrow_label(plate, (270, 620), (430, 620), "neighbor interactions", fill=GOLD, width=7)
    plate.text((332, 665), "+ mobile electrons in conductors", size=16, anchor="mm")
    plate.text((332, 720), "matter required", size=20, bold=True, anchor="mm")

    plate.draw.rounded_rectangle((650, 392, 950, 680), radius=16,
                                 fill=hex_rgba(BLUE_LIGHT, 110), outline=BLUE, width=4)
    plate.draw.arc((690, 430, 910, 640), 190, 345, fill=CORAL, width=8)
    plate.draw.arc((690, 430, 910, 640), 10, 165, fill=TEAL, width=8)
    plate.arrow((707, 540), (707, 460), fill=CORAL, width=7, head=18)
    plate.arrow((893, 480), (893, 560), fill=TEAL, width=7, head=18)
    plate.text((800, 720), "warm fluid rises", size=20, bold=True, anchor="mm")

    plate.draw.ellipse((1160, 430, 1272, 542), fill=CORAL_LIGHT, outline=CORAL, width=5)
    for angle in range(-55, 56, 28):
        radians = math.radians(angle)
        plate.arrow((1275, 486), (1275 + 150 * math.cos(radians), 486 + 150 * math.sin(radians)),
                    fill=GOLD, width=6, head=17)
    plate.draw.rounded_rectangle((1380, 408, 1428, 564), radius=8, outline=PLUM, width=4)
    plate.text((1268, 720), "works through vacuum", size=20, bold=True, anchor="mm")
    footer(plate, "Conduction, convection, and radiation move energy by different mechanisms.", size=27)


def draw_waves(plate: Plate) -> None:
    left, right = two_panel_boxes()
    panel(plate, left, "ONE SPEED: v = fλ")
    panel(plate, right, "AMPLITUDE IS SEPARATE")
    wave(plate, (160, 350, 735, 500), cycles=2, amplitude=48, fill=BLUE)
    plate.double_arrow((160, 548), (447, 548), fill=BLUE, width=5)
    plate.text((304, 580), "λ = 3 m", size=20, bold=True, anchor="mm")
    wave(plate, (160, 630, 735, 748), cycles=4, amplitude=38, fill=TEAL)
    plate.double_arrow((160, 778), (304, 778), fill=TEAL, width=5)
    plate.text((500, 778), "double f → half λ", size=20, bold=True, anchor="mm")

    wave(plate, (865, 350, 1435, 500), cycles=3, amplitude=28, fill=PLUM)
    wave(plate, (865, 610, 1435, 760), cycles=3, amplitude=68, fill=CORAL)
    plate.text((1150, 535), "same f and λ", size=20, bold=True, anchor="mm")
    plate.text((1150, 790), "more energy, not more speed", size=20, bold=True, anchor="mm")
    footer(plate, "At fixed wave speed, frequency and wavelength trade inversely; amplitude does not.", size=26)


def draw_matter(plate: Plate) -> None:
    boxes = three_panel_boxes()
    for box, heading in zip(boxes, ("SOLID", "LIQUID", "GAS")):
        panel(plate, box, heading)
    solid = [(205 + c * 64, 400 + r * 64) for r in range(4) for c in range(5)]
    liquid_offsets = ((0, 8), (9, -7), (-8, 4), (6, -4), (-5, 9),
                      (7, -9), (-6, 7), (10, 1), (-9, -5), (4, 6),
                      (-3, -8), (8, 5), (-10, 9), (5, -6), (0, 2),
                      (9, 7), (-7, -3), (4, -9), (-2, 6), (7, -5))
    liquid = [(674 + (i % 5) * 62 + dx, 410 + (i // 5) * 73 + dy)
              for i, (dx, dy) in enumerate(liquid_offsets)]
    gas_offsets = ((0, 0), (18, -12), (-12, 15), (8, -4),
                   (20, 10), (-14, -8), (15, 5), (-5, 14),
                   (-8, -10), (10, 12), (-16, 2), (18, -7),
                   (14, 8), (-18, -11), (7, 14), (-10, 0),
                   (-16, 4), (6, -9), (17, 9), (-4, -3))
    gas = [(1148 + (i % 4) * 82 + dx, 390 + (i // 4) * 64 + dy)
           for i, (dx, dy) in enumerate(gas_offsets)]
    particle_box(plate, (172, 350, 492, 690), solid, fill=BLUE_LIGHT, outline=BLUE, radius=13)
    particle_box(plate, (640, 350, 960, 690), liquid, fill=TEAL_LIGHT, outline=TEAL, radius=13)
    particle_box(plate, (1108, 350, 1428, 690), gas, fill=GOLD_LIGHT, outline=GOLD, radius=13)
    plate.text((332, 740), "fixed neighbors", size=20, bold=True, anchor="mm")
    plate.text((800, 740), "neighbors change", size=20, bold=True, anchor="mm")
    plate.text((1268, 740), "far apart; compressible", size=20, bold=True, anchor="mm")
    footer(plate, "The particles stay the same; spacing and freedom of motion define the state.", size=27)


def draw_units(plate: Plate) -> None:
    for box, heading in zip(three_panel_boxes(), ("RESOLUTION", "CONVERSION", "REPEATS")):
        panel(plate, box, heading)
    plate.draw.line((170, 510, 494, 510), fill=INK, width=6)
    for i in range(11):
        x = 180 + i * 30
        plate.draw.line((x, 510, x, 510 - (48 if i % 5 == 0 else 28)), fill=INK, width=4)
    plate.arrow((368, 400), (368, 490), fill=CORAL, width=6, head=16)
    plate.text((332, 610), "6.3 ± 0.1 cm", size=24, bold=True, anchor="mm")
    plate.text((332, 722), "digits follow the scale", size=19, anchor="mm")

    plate.text((800, 410), "1.25 m", size=31, bold=True, anchor="mm")
    plate.arrow((800, 452), (800, 548), fill=TEAL, width=7, head=20)
    plate.text((800, 594), "× 100", size=21, bold=True, fill=TEAL, anchor="mm")
    plate.text((800, 664), "125 cm", size=31, bold=True, anchor="mm")
    plate.text((800, 722), "same length, new unit", size=19, anchor="mm")

    values = (9.8, 10.0, 9.9, 10.1, 14.2)
    for index, value in enumerate(values):
        y = 390 + index * 62
        plate.text((1130, y), f"trial {index + 1}", size=18)
        x = 1230 + (value - 9) * 42
        plate.dot((x, y + 8), 9, fill=CORAL if value > 12 else BLUE,
                  outline=CORAL if value > 12 else BLUE, width=1)
    plate.text((1268, 722), "repeat reveals the outlier", size=19, anchor="mm")
    footer(plate, "A measurement needs a value, unit, resolution, and honest uncertainty.", size=27)


def draw_mechanics(plate: Plate) -> None:
    for box, heading in zip(three_panel_boxes(), ("1 · INERTIA", "2 · F = ma", "3 · INTERACTION")):
        panel(plate, box, heading)
    cart(plate, (332, 500), width=150)
    plate.draw.line((160, 575, 504, 575), fill=INK, width=6)
    plate.text((332, 655), "ΣF = 0", size=25, bold=True, anchor="mm")
    plate.text((332, 718), "velocity stays constant", size=19, anchor="mm")

    _block(plate, (800, 500), "2 kg")
    arrow_label(plate, (870, 500), (970, 500), "10 N", fill=TEAL, width=8)
    plate.text((800, 650), "a = F/m = 5 m/s²", size=23, bold=True, anchor="mm")
    plate.text((800, 718), "double mass → half a", size=19, anchor="mm")

    plate.draw.ellipse((1138, 430, 1260, 552), fill=BLUE_LIGHT, outline=BLUE, width=4)
    plate.draw.ellipse((1276, 430, 1398, 552), fill=GOLD_LIGHT, outline=GOLD, width=4)
    arrow_label(plate, (1260, 490), (1190, 490), "on A", fill=BLUE, width=7)
    arrow_label(plate, (1276, 490), (1346, 490), "on B", fill=GOLD, width=7)
    plate.text((1268, 650), "equal and opposite", size=22, bold=True, anchor="mm")
    plate.text((1268, 718), "forces act on different bodies", size=18, anchor="mm")
    footer(plate, "Newton's laws connect net force, acceleration, and paired interactions.", size=27)


def draw_energy_work(plate: Plate) -> None:
    left, right = two_panel_boxes()
    panel(plate, left, "ENERGY LEDGER")
    panel(plate, right, "COLLISION LEDGER")
    plate.draw.arc((180, 355, 730, 815), 180, 350, fill=INK, width=9)
    plate.dot((220, 490), 24, fill=GOLD_LIGHT, outline=GOLD, width=4)
    plate.dot((690, 685), 24, fill=BLUE_LIGHT, outline=BLUE, width=4)
    energy_bar(plate, (190, 710, 690, 770),
               (("GPE 2", 2, GOLD_LIGHT), ("KE 6", 6, BLUE_LIGHT),
                ("internal 2", 2, CORAL_LIGHT)))
    plate.text((450, 325), "gravitational → kinetic + internal", size=21,
               bold=True, anchor="mm")

    _block(plate, (985, 480), "2 kg", fill=BLUE_LIGHT, outline=BLUE)
    _block(plate, (1285, 480), "1 kg", fill=GOLD_LIGHT, outline=GOLD)
    arrow_label(plate, (1055, 480), (1155, 480), "4 m/s", fill=BLUE, width=7)
    plate.arrow((1135, 610), (1135, 680), fill=INK_SOFT, width=5, head=16)
    plate.text((1135, 705), "momentum conserved", size=20, bold=True, anchor="mm")
    plate.text((1135, 752), "total kinetic energy conserved only if elastic", size=17, anchor="mm")
    footer(plate, "Work transfers energy; momentum always balances in an isolated collision.", size=27)


def _coil(plate: Plate, center: tuple[float, float], color: str = BLUE) -> None:
    x, y = center
    for offset in range(-72, 73, 24):
        plate.draw.ellipse((x + offset - 28, y - 90, x + offset + 28, y + 90),
                           outline=color, width=5)


def draw_em(plate: Plate) -> None:
    left, right = two_panel_boxes()
    panel(plate, left, "CHANGING FLUX")
    panel(plate, right, "UNCHANGED FLUX")
    plate.draw.rounded_rectangle((170, 430, 340, 530), radius=12,
                                 fill=CORAL_LIGHT, outline=CORAL, width=4)
    plate.text((215, 480), "N", size=28, bold=True, anchor="mm")
    plate.text((295, 480), "S", size=28, bold=True, anchor="mm")
    _coil(plate, (585, 480))
    arrow_label(plate, (350, 480), (470, 480), "move", fill=TEAL, width=8)
    plate.text((450, 650), "dΦ/dt ≠ 0 → induced emf", size=23, bold=True, anchor="mm")
    plate.draw.arc((380, 680, 520, 800), 190, 350, fill=GOLD, width=7)

    plate.draw.rounded_rectangle((870, 430, 1040, 530), radius=12,
                                 fill=CORAL_LIGHT, outline=CORAL, width=4)
    plate.text((915, 480), "N", size=28, bold=True, anchor="mm")
    plate.text((995, 480), "S", size=28, bold=True, anchor="mm")
    _coil(plate, (1285, 480))
    plate.text((1150, 650), "dΦ/dt = 0 → no emf", size=23, bold=True, anchor="mm")
    plate.text((1150, 720), "a strong stationary field is not enough", size=18, anchor="mm")
    footer(plate, "Induction responds to changing magnetic flux, not magnetism alone.", size=28)


def draw_optics_waves(plate: Plate) -> None:
    left, right = two_panel_boxes()
    panel(plate, left, "INTERFERENCE")
    panel(plate, right, "THIN LENS")
    plate.dot((180, 510), 18, fill=GOLD_LIGHT, outline=GOLD, width=4)
    plate.draw.line((390, 330, 390, 700), fill=INK, width=9)
    for y in (460, 560):
        plate.draw.line((385, y - 18, 395, y + 18), fill=PAPER_LIGHT, width=13)
    for target_y, color, label in ((410, TEAL, "Δr = 2λ → bright"), (640, CORAL, "Δr = 2½λ → dark")):
        plate.draw.line((198, 510, 390, 460, 700, target_y), fill=color, width=5)
        plate.draw.line((198, 510, 390, 560, 700, target_y), fill=color, width=5)
        plate.text((450, target_y - 24), label, size=18, bold=True, fill=color)

    plate.draw.line((850, 520, 1450, 520), fill=GRID, width=3)
    plate.draw.line((1150, 330, 1150, 730), fill=BLUE, width=9)
    plate.draw.arc((1085, 330, 1215, 730), 90, 270, fill=BLUE, width=5)
    plate.draw.arc((1085, 330, 1215, 730), 270, 90, fill=BLUE, width=5)
    plate.arrow((900, 520), (900, 430), fill=CORAL, width=7, head=18)
    object_tip = (900, 430)
    image_tip = (1347, 591)
    # Parallel, central, and near-focus rays all leave the same object tip.
    plate.draw.line((*object_tip, 1150, 430, *image_tip), fill=GOLD, width=4)
    plate.draw.line((*object_tip, 1150, 520, *image_tip), fill=TEAL, width=4)
    plate.draw.line((*object_tip, 1040, 520, 1150, 591, *image_tip), fill=CORAL, width=4)
    plate.dot((1040, 520), 8, fill=CORAL_LIGHT, outline=CORAL, width=2)
    plate.dot((1260, 520), 8, fill=GOLD_LIGHT, outline=GOLD, width=2)
    plate.arrow((1347, 520), image_tip, fill=TEAL, width=7, head=18)
    plate.text((1150, 755), "1/f = 1/u + 1/v", size=22, bold=True, math_face=True, anchor="mm")
    footer(plate, "Path difference sets interference; lens geometry sets where rays reconverge.", size=27)


def draw_thermo(plate: Plate) -> None:
    left, right = two_panel_boxes()
    panel(plate, left, "HEAT ENGINE")
    panel(plate, right, "CARNOT LIMIT")
    plate.draw.rounded_rectangle((250, 320, 650, 410), radius=16,
                                 fill=CORAL_LIGHT, outline=CORAL, width=4)
    plate.text((450, 365), "hot reservoir 600 K", size=24, bold=True, anchor="mm")
    plate.draw.rounded_rectangle((330, 500, 570, 610), radius=18,
                                 fill=GOLD_LIGHT, outline=GOLD, width=4)
    plate.text((450, 555), "engine", size=28, bold=True, anchor="mm")
    plate.draw.rounded_rectangle((250, 710, 650, 790), radius=16,
                                 fill=BLUE_LIGHT, outline=BLUE, width=4)
    plate.text((450, 750), "cold reservoir 300 K", size=22, bold=True, anchor="mm")
    arrow_label(plate, (450, 414), (450, 494), "Q_h = 100 J", fill=CORAL, width=8, offset=(75, 0))
    arrow_label(plate, (574, 555), (700, 555), "W ≤ 50 J", fill=TEAL, width=8)
    arrow_label(plate, (450, 614), (450, 704), "Q_c >= 50 J", fill=BLUE, width=8, offset=(75, 0))

    mapping = axes(plate, (900, 350, 1400, 730), x_label="Tcold / Thot", y_label="ηmax",
                   x_range=(0, 1), y_range=(0, 1))
    plot_curve(plate, mapping, ((x / 50, 1 - x / 50) for x in range(51)), fill=PLUM)
    plate.text((1150, 765), "eta_max = 1 - T_c/T_h", size=22, bold=True, math_face=True, anchor="mm")
    footer(plate, "Every engine rejects heat; no real engine exceeds the Carnot bound.", size=27)


def draw_nuclear(plate: Plate) -> None:
    left, right = two_panel_boxes()
    panel(plate, left, "BINDING ENERGY")
    panel(plate, right, "HALF-LIFE ENSEMBLE")
    mapping = axes(plate, (170, 350, 720, 720), x_label="mass number A", y_label="binding / nucleon",
                   x_range=(0, 240), y_range=(0, 10))
    samples = ((1, 0.0), (4, 7.1), (12, 7.7), (16, 8.0), (40, 8.55),
               (56, 8.790), (62, 8.795), (100, 8.60), (160, 8.20), (240, 7.60))
    plot_curve(plate, mapping, samples, fill=BLUE)
    peak = mapping(62, 8.795)
    plate.dot(peak, 10, fill=GOLD, outline=GOLD, width=1)
    plate.text((peak[0] + 15, peak[1] - 18), "Fe/Ni peak", size=18, bold=True, fill=GOLD)
    plate.text((445, 770), "light fusion → peak ← heavy fission", size=19, bold=True, anchor="mm")

    counts = (32, 16, 8, 4)
    for column, count in enumerate(counts):
        x0 = 880 + column * 140
        plate.text((x0 + 55, 360), f"{column} t½", size=18, bold=True, anchor="mm")
        for index in range(count):
            x = x0 + 12 + (index % 4) * 28
            y = 410 + (index // 4) * 34
            plate.dot((x, y), 8, fill=PLUM_LIGHT, outline=PLUM, width=2)
        plate.text((x0 + 55, 720), str(count), size=27, bold=True, anchor="mm")
    plate.text((1150, 770), "expected count halves; atoms decay randomly", size=18, anchor="mm")
    footer(plate, "Binding explains nuclear energy; half-life predicts ensembles, not individual decay times.", size=25)


def draw_relativity_intro(plate: Plate) -> None:
    left, right = two_panel_boxes()
    panel(plate, left, "LIGHT CLOCK AT REST")
    panel(plate, right, "SAME CLOCK, PLATFORM FRAME")
    plate.draw.line((350, 390, 550, 390), fill=BLUE, width=12)
    plate.draw.line((350, 690, 550, 690), fill=BLUE, width=12)
    plate.double_arrow((450, 410), (450, 670), fill=GOLD, width=7)
    plate.text((450, 740), "vertical round trip = 2L", size=21, bold=True, anchor="mm")

    snapshots = ((910, "emission", "bottom"), (1150, "reflection", "top"),
                 (1390, "return", "bottom"))
    for x, label, event in snapshots:
        plate.draw.line((x - 25, 390, x + 25, 390),
                        fill=BLUE if event == "top" else GRID, width=10)
        plate.draw.line((x - 25, 690, x + 25, 690),
                        fill=BLUE if event == "bottom" else GRID, width=10)
        plate.draw.line((x, 405, x, 675), fill=GRID, width=3)
        plate.text((x, 720), label, size=16, bold=True, anchor="mm")
    plate.polyline(((910, 690), (1150, 390), (1390, 690)), fill=GOLD, width=8)
    plate.arrow((960, 755), (1340, 755), fill=TEAL, width=7, head=20)
    plate.text((1150, 785), "successive positions of one moving clock", size=15, anchor="mm")
    plate.text((1150, 330), "same light speed c; longer path in this frame", size=19,
               bold=True, anchor="mm")
    footer(plate, "In the frame where the clock moves, invariant light speed makes its longer path take more coordinate time.", size=23)


def draw_modern(plate: Plate) -> None:
    left, right = two_panel_boxes()
    panel(plate, left, "FREQUENCY SETS ENERGY")
    panel(plate, right, "INTENSITY SETS COUNT")
    plate.draw.rounded_rectangle((170, 620, 720, 690), radius=12,
                                 fill=PLUM_LIGHT, outline=PLUM, width=4)
    for index, (freq, color, outcome) in enumerate(((2, CORAL, "below f₀: none"),
                                                    (5, BLUE, "above f₀: emitted"))):
        y = 380 + index * 150
        wave(plate, (190, y, 420, y + 80), cycles=freq, amplitude=26, fill=color, width=5)
        plate.arrow((430, y + 40), (535, y + 40), fill=color, width=6, head=18)
        if index:
            plate.dot((610, y + 40), 13, fill=GOLD_LIGHT, outline=GOLD, width=3)
            plate.arrow((610, y + 40), (680, y - 10), fill=TEAL, width=5, head=15)
        plate.text((450, y - 20), outcome, size=18, bold=True, fill=color)
    plate.text((445, 755), "Kmax = hf − φ", size=22, bold=True, math_face=True, anchor="mm")

    plate.draw.rounded_rectangle((870, 620, 1430, 690), radius=12,
                                 fill=PLUM_LIGHT, outline=PLUM, width=4)
    for row, photons in enumerate((2, 7)):
        y = 400 + row * 170
        for i in range(photons):
            plate.dot((900 + i * 52, y), 10, fill=BLUE_LIGHT, outline=BLUE, width=2)
        emitted = round(photons * 0.5)
        for i in range(emitted):
            plate.dot((910 + i * 52, y + 105), 9, fill=GOLD_LIGHT, outline=GOLD, width=2)
        plate.text((1390, y + 50), f"{photons} arrivals → about {emitted} emitted", size=16, anchor="ra")
    plate.text((1150, 755), "fixed 50% yield example; same f → same maximum energy", size=17, bold=True, anchor="mm")
    footer(plate, "Frequency sets maximum electron energy; at fixed frequency, intensity changes photon arrival rate.", size=24)


SPECS: dict[str, Spec] = {
    "phys.2.forces": spec("phys.2.forces", "Forces and Friction", 2,
        "phys-forces-net-force",
        "Free-body diagrams compare a resting book, accelerating crate, and moving skydiver at terminal speed.",
        "Balanced forces preserve velocity even during motion; only a nonzero net force produces acceleration.", draw_forces),
    "phys.2.gravity": spec("phys.2.gravity", "Gravity", 2,
        "phys-gravity-mass-weight-orbit",
        "Panels distinguish ten-kilogram mass, different Earth and Moon weights, and sideways free fall around a planet.",
        "Mass is intrinsic, weight depends on gravitational field, and orbit combines inward fall with sideways motion.", draw_gravity),
    "phys.2.electricity": spec("phys.2.electricity", "Electricity", 2,
        "phys-electricity-circuit-topology",
        "Circuit schematics compare an open path, two bulbs in series, and two parallel current branches.",
        "A closed topology permits current; voltage adds across series elements while current divides among parallel branches.", draw_electricity),
    "phys.2.heat": spec("phys.2.heat", "Heat and Temperature", 2,
        "phys-heat-transfer-mechanisms",
        "A solid bar, circulating fluid, and radiant rays distinguish conduction, convection, and radiation.",
        "Conduction uses neighboring interactions and mobile electrons in conductors; convection moves fluid, while radiation uses electromagnetic waves.", draw_heat),
    "phys.2.waves": spec("phys.2.waves", "Waves", 2,
        "phys-waves-speed-frequency-amplitude",
        "Wave traces show frequency and wavelength trading at fixed speed while amplitude changes independently.",
        "The relation v equals frequency times wavelength constrains spacing; amplitude controls energy without changing that speed.", draw_waves),
    "phys.2.matter": spec("phys.2.matter", "States of Matter", 2,
        "phys-matter-particle-states",
        "Identical particles appear ordered in a solid, mobile in a liquid, and widely separated in a gas.",
        "A phase change rearranges spacing and motion rather than changing the identity of the particles.", draw_matter),
    "phys.2.units": spec("phys.2.units", "Measuring the World", 2,
        "phys-measurement-resolution-repeats",
        "A ruler resolution, metre-to-centimetre conversion, and repeated readings with an outlier form a measurement audit.",
        "Units preserve meaning, scale limits precision, and repeated measurements reveal variation and possible outliers.", draw_units),
    "phys.3.mechanics": spec("phys.3.mechanics", "Newton's Laws", 3,
        "phys-newton-laws-system-map",
        "Three system diagrams connect constant velocity, force divided by mass, and equal opposite interaction forces.",
        "Zero net force means constant velocity—not necessarily rest; nonzero net force produces acceleration, and interaction forces act on different bodies.", draw_mechanics),
    "phys.3.energy-work": spec("phys.3.energy-work", "Work, Energy and Momentum", 3,
        "phys-energy-momentum-ledgers",
        "A rolling energy bar and two-body collision distinguish energy transfers from momentum accounting.",
        "Total momentum is conserved in isolated collisions, whereas total kinetic energy is conserved only in an elastic collision.", draw_energy_work),
    "phys.3.em": spec("phys.3.em", "Electricity and Magnetism", 3,
        "phys-induction-changing-flux",
        "A moving magnet and stationary magnet face identical coils, but only changing magnetic flux induces an emf.",
        "Faraday induction depends on flux-change rate, so a strong unchanging flux produces no induced emf in this stationary coil.", draw_em),
    "phys.3.optics-waves": spec("phys.3.optics-waves", "Waves and Optics", 3,
        "phys-interference-lens-paths",
        "Double-slit paths mark bright and dark path differences beside ray convergence through a thin lens.",
        "Interference follows relative path length, while lens geometry predicts the location and orientation of the image.", draw_optics_waves),
    "phys.3.thermo": spec("phys.3.thermo", "Thermodynamics", 3,
        "phys-heat-engine-carnot-budget",
        "A heat-engine budget sends energy from hot to cold while a graph shows the Carnot efficiency ceiling.",
        "Every engine rejects heat; no real engine exceeds the Carnot bound set by its absolute reservoir temperatures.", draw_thermo),
    "phys.3.nuclear": spec("phys.3.nuclear", "Atoms and Nuclei", 3,
        "phys-binding-half-life",
        "The nuclear binding-energy curve peaks in the iron-nickel region beside an ensemble halving from thirty-two to four nuclei.",
        "Fusion of light nuclei and fission of heavy nuclei can move products toward the iron-nickel binding peak; half-life predicts ensemble averages, not individual events.", draw_nuclear),
    "phys.3.relativity-intro": spec("phys.3.relativity-intro", "Special Relativity: a First Look", 3,
        "phys-light-clock-time-dilation",
        "A resting light clock's vertical round trip is compared with successive moving-clock positions and a longer diagonal light path.",
        "In the frame where the clock moves, invariant light speed makes its longer optical path correspond to more coordinate time.", draw_relativity_intro),
    "phys.3.modern": spec("phys.3.modern", "The Quantum Idea", 3,
        "phys-photoelectric-frequency-intensity",
        "Photoelectric panels separate the frequency threshold from a same-frequency comparison of photon arrival counts.",
        "Frequency sets each photon's energy and the electron maximum; at fixed frequency, intensity changes arrival rate.", draw_modern),
}
