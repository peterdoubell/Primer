"""Explanatory physics plates for the missing Seedling and Sprout lessons."""

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
    cart,
    centered_note,
    energy_bar,
    footer,
    force_pair,
    hex_rgba,
    panel,
    spec,
    thermometer,
    three_panel_boxes,
    two_panel_boxes,
    wave,
)


def draw_push_pull(plate: Plate) -> None:
    for box, heading in zip(three_panel_boxes(), ("BALANCED", "UNBALANCED", "SQUEEZE")):
        panel(plate, box, heading)

    cart(plate, (332, 488), width=150)
    force_pair(plate, (332, 488), 6, 6, scale=13,
               left_label="6 N", right_label="6 N")
    plate.text((332, 680), "net force = 0 N", size=25, bold=True, anchor="mm")
    centered_note(plate, (162, 710, 502, 780), "No change in motion", size=20)

    cart(plate, (800, 488), width=150)
    force_pair(plate, (800, 488), 2, 7, scale=13,
               left_label="2 N", right_label="7 N")
    arrow_label(plate, (728, 650), (872, 650), "net 5 N", fill=TEAL, width=7)
    centered_note(plate, (630, 710, 970, 780), "Acceleration is rightward", size=20)

    plate.draw.rounded_rectangle((1194, 416, 1342, 558), radius=22,
                                 fill=CORAL_LIGHT, outline=CORAL, width=4)
    arrow_label(plate, (1112, 488), (1190, 488), "push", fill=CORAL, width=9)
    arrow_label(plate, (1424, 488), (1346, 488), "push", fill=TEAL, width=9)
    plate.text((1268, 650), "shape changes", size=25, bold=True, anchor="mm")
    centered_note(plate, (1098, 710, 1438, 780), "Opposing forces can compress", size=20)
    footer(plate, "Motion changes only when the forces do not balance.")


def draw_hot_cold(plate: Plate) -> None:
    left, right = two_panel_boxes()
    panel(plate, left, "AT FIRST")
    panel(plate, right, "AFTER CONTACT")
    thermometer(plate, (290, 450), 80, "hot: 80 °C", fill=CORAL)
    thermometer(plate, (610, 450), 20, "cold: 20 °C", fill=BLUE)
    arrow_label(plate, (392, 470), (510, 470), "energy", fill=GOLD, width=10)
    plate.text((450, 662), "hot → cold", size=27, bold=True, fill=GOLD, anchor="mm")

    thermometer(plate, (998, 450), 50, "50 °C", fill=PLUM)
    thermometer(plate, (1304, 450), 50, "50 °C", fill=PLUM)
    plate.double_arrow((1070, 470), (1232, 470), fill=GRID, width=5)
    plate.text((1151, 662), "same temperature", size=27, bold=True,
               fill=PLUM, anchor="mm")
    centered_note(plate, (892, 708, 1410, 778),
                  "Particles still move, but there is no net transfer.", size=20)
    footer(plate, "Equal heat capacities: energy spreads until both reach equilibrium.", size=27)


def _water(plate: Plate, box: tuple[int, int, int, int]) -> None:
    x0, y0, x1, y1 = box
    plate.draw.rounded_rectangle(box, radius=22, fill=hex_rgba(BLUE_LIGHT, 115),
                                 outline=BLUE, width=4)
    for x in range(x0 + 20, x1 - 20, 54):
        plate.draw.arc((x, y0 + 8, x + 54, y0 + 38), 190, 350, fill=BLUE, width=3)


def draw_float_sink(plate: Plate) -> None:
    for box, heading in zip(three_panel_boxes(), ("FLOATS", "SINKS", "RESHAPE")):
        panel(plate, box, heading)
    _water(plate, (168, 420, 496, 690))
    plate.draw.rounded_rectangle((276, 372, 388, 476), radius=14,
                                 fill=GOLD_LIGHT, outline=GOLD, width=4)
    force_pair(plate, (332, 488), 0, 0)
    arrow_label(plate, (332, 516), (332, 418), "buoyancy", fill=TEAL, width=7, offset=(78, 0))
    arrow_label(plate, (332, 516), (332, 614), "weight", fill=CORAL, width=7, offset=(62, 0))
    plate.text((332, 738), "forces balance", size=22, bold=True, anchor="mm")

    _water(plate, (636, 420, 964, 690))
    plate.draw.ellipse((750, 520, 850, 620), fill=CORAL_LIGHT, outline=CORAL, width=4)
    arrow_label(plate, (800, 566), (800, 496), "up", fill=TEAL, width=7, offset=(48, 0))
    arrow_label(plate, (800, 566), (800, 688), "weight", fill=CORAL, width=8, offset=(65, 0))
    plate.text((800, 738), "weight is larger", size=22, bold=True, anchor="mm")

    _water(plate, (1104, 420, 1432, 690))
    plate.draw.ellipse((1185, 375, 1265, 455), fill=PLUM_LIGHT, outline=PLUM, width=4)
    plate.text((1225, 494), "clay ball", size=20, anchor="mm")
    plate.arrow((1276, 420), (1344, 420), fill=INK_SOFT, width=5, head=16)
    plate.draw.polygon(((1322, 418), (1368, 418), (1355, 476), (1335, 476)),
                       fill=PLUM_LIGHT, outline=PLUM)
    plate.text((1345, 514), "same clay, boat shape", size=18, anchor="mm")
    plate.text((1268, 738), "more water displaced", size=22, bold=True, anchor="mm")
    footer(plate, "Floating depends on average density: shape can change volume, not mass.", size=27)


def draw_motion(plate: Plate) -> None:
    surfaces = (("ICE", BLUE, 0.0, 0), ("GRASS", GREEN, 0.4, 22), ("SAND", GOLD, 1.2, 42))
    for box, (name, color, slowdown, drag) in zip(three_panel_boxes(), surfaces):
        inner = panel(plate, box, name, outline=color)
        x0, y0, x1, y1 = inner
        baseline = 610
        plate.draw.line((x0 + 6, baseline, x1 - 6, baseline), fill=color, width=8)
        if name != "ICE":
            for x in range(int(x0 + 20), int(x1 - 20), 35):
                plate.draw.line((x, baseline, x + (8 if name == "GRASS" else 15),
                                 baseline - (14 if name == "GRASS" else 7)), fill=color, width=3)
        available = x1 - x0 - 80
        positions = []
        for index in range(9):
            time = index / 8
            x = x0 + 40 + available * time / (1 + slowdown * time)
            positions.append(x)
            plate.dot((x, baseline - 26), 8, fill=color, outline=color, width=1)
        cart(plate, (positions[-1], baseline - 58),
             width=80, height=38, fill=hex_rgba(color, 80), outline=color)
        if drag:
            arrow_label(plate, (x0 + 175, 700), (x0 + 175 - drag * 2, 700),
                        "friction", fill=CORAL, width=6, offset=(0, -18))
        plate.text(((x0 + x1) / 2, 758), "equal time marks", size=20,
                   fill=INK_SOFT, anchor="mm")
    footer(plate, "Friction transfers kinetic energy; shrinking gaps reveal the slowing.", size=27)


def draw_machines(plate: Plate) -> None:
    for box, heading in zip(three_panel_boxes(), ("RAMP", "LEVER", "PULLEY")):
        panel(plate, box, heading)
    plate.draw.polygon(((164, 690), (500, 690), (500, 360)),
                       fill=hex_rgba(BLUE_LIGHT, 100), outline=BLUE)
    plate.draw.rounded_rectangle((360, 473, 444, 557), radius=8,
                                 fill=GOLD_LIGHT, outline=GOLD, width=4)
    arrow_label(plate, (270, 635), (370, 535), "smaller force", fill=TEAL, width=7)
    plate.text((332, 748), "more distance", size=22, bold=True, anchor="mm")

    plate.draw.polygon(((764, 690), (836, 690), (800, 613)), fill=CORAL_LIGHT,
                       outline=CORAL)
    plate.draw.line((638, 574, 944, 648), fill=INK, width=14)
    plate.draw.ellipse((899, 570, 963, 634), fill=GOLD_LIGHT, outline=GOLD, width=4)
    arrow_label(plate, (662, 502), (638, 570), "small effort", fill=TEAL, width=7)
    plate.text((800, 748), "long arm × small force", size=21, bold=True, anchor="mm")

    plate.draw.ellipse((1200, 352, 1336, 488), fill=PAPER_LIGHT, outline=BLUE, width=10)
    plate.draw.arc((1200, 352, 1336, 488), 180, 360, fill=TEAL, width=12)
    plate.draw.line((1200, 420, 1200, 675), fill=INK_SOFT, width=7)
    plate.draw.line((1336, 420, 1336, 675), fill=INK_SOFT, width=7)
    plate.draw.rounded_rectangle((1160, 622, 1240, 704), radius=8,
                                 fill=GOLD_LIGHT, outline=GOLD, width=4)
    arrow_label(plate, (1336, 560), (1336, 670), "pull", fill=TEAL, width=7, offset=(42, 0))
    plate.text((1268, 748), "redirects force", size=22, bold=True, anchor="mm")
    footer(plate, "Machines trade force for distance or direction; work is not free.", size=27)


def _magnet(plate: Plate, box: tuple[int, int, int, int], left: str, right: str) -> None:
    x0, y0, x1, y1 = box
    mid = (x0 + x1) / 2
    plate.draw.rounded_rectangle(box, radius=12, fill=PAPER_LIGHT, outline=INK, width=4)
    plate.draw.rounded_rectangle((x0, y0, mid, y1), radius=10,
                                 fill=CORAL_LIGHT if left == "N" else BLUE_LIGHT,
                                 outline=CORAL if left == "N" else BLUE, width=2)
    plate.draw.rounded_rectangle((mid, y0, x1, y1), radius=10,
                                 fill=CORAL_LIGHT if right == "N" else BLUE_LIGHT,
                                 outline=CORAL if right == "N" else BLUE, width=2)
    plate.text(((x0 + mid) / 2, (y0 + y1) / 2), left, size=28, bold=True, anchor="mm")
    plate.text(((mid + x1) / 2, (y0 + y1) / 2), right, size=28, bold=True, anchor="mm")


def draw_magnets(plate: Plate) -> None:
    boxes = three_panel_boxes()
    for box, heading in zip(boxes, ("ATTRACT", "REPEL", "FIELD")):
        panel(plate, box, heading)
    _magnet(plate, (160, 435, 308, 525), "N", "S")
    _magnet(plate, (356, 435, 504, 525), "N", "S")
    arrow_label(plate, (322, 590), (348, 590), "pull together", fill=TEAL, width=6)
    plate.text((332, 708), "opposite poles", size=22, bold=True, anchor="mm")

    _magnet(plate, (628, 435, 776, 525), "N", "S")
    _magnet(plate, (824, 435, 972, 525), "S", "N")
    arrow_label(plate, (786, 590), (740, 590), "", fill=CORAL, width=6)
    arrow_label(plate, (814, 590), (860, 590), "push apart", fill=CORAL, width=6)
    plate.text((800, 708), "like poles", size=22, bold=True, anchor="mm")

    _magnet(plate, (1170, 455, 1366, 545), "N", "S")
    for radius in (90, 132, 172):
        plate.draw.arc((1268 - radius, 500 - radius, 1268 + radius, 500 + radius),
                       195, 345, fill=PLUM, width=4)
        plate.draw.arc((1268 - radius, 500 - radius, 1268 + radius, 500 + radius),
                       15, 165, fill=PLUM, width=4)
    plate.text((1268, 708), "closed field loops", size=22, bold=True, anchor="mm")
    footer(plate, "Magnetic poles set the direction and shape of the surrounding field.", size=27)


def draw_sound(plate: Plate) -> None:
    left, right = two_panel_boxes()
    panel(plate, left, "PITCH: FREQUENCY")
    panel(plate, right, "LOUDNESS: AMPLITUDE")
    plate.text((450, 300), "air-pressure trace over time", size=18, bold=True,
               fill=INK_SOFT, anchor="mm")
    plate.text((1150, 300), "air-pressure trace over time", size=18, bold=True,
               fill=INK_SOFT, anchor="mm")
    wave(plate, (165, 365, 730, 515), cycles=2, amplitude=42, fill=BLUE)
    wave(plate, (165, 595, 730, 745), cycles=5, amplitude=42, fill=TEAL)
    plate.text((180, 332), "low: 2 cycles", size=21, bold=True)
    plate.text((180, 562), "high: 5 cycles", size=21, bold=True)
    plate.text((690, 770), "same amplitude", size=19, fill=INK_SOFT, anchor="ra")

    wave(plate, (865, 365, 1430, 515), cycles=4, amplitude=26, fill=PLUM)
    wave(plate, (865, 595, 1430, 745), cycles=4, amplitude=74, fill=CORAL)
    plate.text((880, 332), "quiet: small height", size=21, bold=True)
    plate.text((880, 562), "loud: large height", size=21, bold=True)
    plate.text((1390, 770), "same frequency", size=19, fill=INK_SOFT, anchor="ra")
    footer(plate, "These are pressure graphs, not sideways air paths: frequency changes pitch; amplitude changes loudness.", size=25)


def draw_energy(plate: Plate) -> None:
    panels = three_panel_boxes()
    headings = ("TOP", "MOVING", "STOPPED")
    for box, heading in zip(panels, headings):
        panel(plate, box, heading)
    energy_bar(plate, (160, 410, 504, 494), (("GPE 10", 10, GOLD_LIGHT),))
    plate.text((332, 525), "gravitational potential store", size=16, anchor="mm")
    plate.draw.ellipse((270, 560, 394, 684), fill=GOLD_LIGHT, outline=GOLD, width=4)
    plate.text((332, 622), "ball", size=24, bold=True, anchor="mm")
    plate.text((332, 738), "10 energy tokens", size=21, bold=True, anchor="mm")

    energy_bar(plate, (628, 410, 972, 494),
               (("GPE 4", 4, GOLD_LIGHT), ("kinetic 6", 6, BLUE_LIGHT)))
    plate.text((800, 525), "potential + kinetic stores", size=16, anchor="mm")
    arrow_label(plate, (664, 622), (922, 622), "moving", fill=BLUE, width=8)
    plate.text((800, 738), "4 + 6 = 10", size=23, bold=True, anchor="mm")

    energy_bar(plate, (1096, 410, 1440, 494),
               (("thermal 7", 7, CORAL_LIGHT), ("env. 3", 3, PLUM_LIGHT)))
    plate.text((1268, 525), "thermal stores: object + surroundings", size=15, anchor="mm")
    for radius in (36, 58, 80):
        plate.draw.arc((1268 - radius, 620 - radius, 1268 + radius, 620 + radius),
                       205, 335, fill=PLUM, width=4)
    plate.text((1268, 610), "sound transfer", size=18, bold=True, fill=PLUM, anchor="mm")
    plate.text((1268, 738), "7 + 3 = 10", size=23, bold=True, anchor="mm")
    footer(plate, "Stores change; heating and sound transfer energy, while the accounted total stays 10.", size=25)


SPECS: dict[str, Spec] = {
    "phys.0.push-pull": spec(
        "phys.0.push-pull", "Pushes and Pulls", 0, "phys-push-pull-forces",
        "Three force diagrams compare balanced pushes, an unbalanced push, and compression from opposing pushes.",
        "Arrow length exposes the net force: equal pushes cancel, while unequal pushes change motion and inward pushes squeeze.",
        draw_push_pull,
    ),
    "phys.0.hot-cold": spec(
        "phys.0.hot-cold", "Hot and Cold", 0, "phys-hot-cold-equilibrium",
        "Equal-heat-capacity objects at eighty and twenty degrees approach a shared fifty-degree equilibrium temperature.",
        "For this insulated equal-capacity pair, thermal energy flows hot to cold until equal temperatures remove net transfer.",
        draw_hot_cold,
    ),
    "phys.0.float-sink": spec(
        "phys.0.float-sink", "Floating and Sinking", 0, "phys-float-sink-buoyancy",
        "Water tanks compare balanced buoyancy and weight, sinking when weight wins, and a clay boat displacing more water.",
        "Floating depends on average density and displaced water, so reshaping the same mass can change whether it floats.",
        draw_float_sink,
    ),
    "phys.1.motion": spec(
        "phys.1.motion", "How Things Move", 1, "phys-motion-friction",
        "Equal-time position marks compare the same cart launch across ice, grass, and sand with increasing friction.",
        "More friction transfers kinetic energy faster after an equal launch; shrinking timestamp gaps reveal the greater slowing.",
        draw_motion,
    ),
    "phys.1.machines": spec(
        "phys.1.machines", "Simple Machines", 1, "phys-simple-machines-tradeoff",
        "A ramp, lever, and pulley diagram show smaller force over distance, lever arms, and redirected force.",
        "Simple machines trade force for distance or direction rather than creating work from nothing.",
        draw_machines,
    ),
    "phys.1.magnets": spec(
        "phys.1.magnets", "Magnets", 1, "phys-magnet-poles-fields",
        "Bar magnets show opposite poles attracting, like poles repelling, and curved magnetic field loops.",
        "Pole orientation predicts attraction or repulsion while the surrounding magnetic field always forms closed loops.",
        draw_magnets,
    ),
    "phys.1.sound": spec(
        "phys.1.sound", "Sound", 1, "phys-sound-frequency-amplitude",
        "Air-pressure traces independently compare low and high frequency with small and large amplitude.",
        "The curves graph pressure over time, not sideways air motion: frequency controls pitch and amplitude controls loudness.",
        draw_sound,
    ),
    "phys.1.energy": spec(
        "phys.1.energy", "Energy Everywhere", 1, "phys-energy-accounting",
        "Three ten-token bars track gravitational, kinetic, thermal, and surroundings energy before, during, and after movement.",
        "Energy stores change while heating and sound are transfer pathways; a complete account preserves the same total.",
        draw_energy,
    ),
}
