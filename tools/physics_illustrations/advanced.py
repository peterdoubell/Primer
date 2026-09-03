"""Explanatory physics plates for the missing Grove and Forest lessons."""

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
    centered_note,
    footer,
    hex_rgba,
    panel,
    plot_curve,
    spec,
    two_panel_boxes,
    wave,
)


def draw_classical(plate: Plate) -> None:
    left, right = two_panel_boxes()
    panel(plate, left, "STATIONARY ACTION")
    panel(plate, right, "PHASE SPACE")
    start, end = (185, 650), (710, 390)
    plate.dot(start, 13, fill=INK, outline=INK, width=1)
    plate.dot(end, 13, fill=INK, outline=INK, width=1)
    for bend, color, label in (((390, 300), GRID, "trial A"),
                               ((440, 710), GRID, "trial B"),
                               ((450, 505), TEAL, "physical path: δS = 0")):
        bx, by = bend
        points = []
        for i in range(81):
            t = i / 80
            x = start[0] * (1 - t) ** 2 + 2 * bx * t * (1 - t) + end[0] * t ** 2
            y = start[1] * (1 - t) ** 2 + 2 * by * t * (1 - t) + end[1] * t ** 2
            points.append((x, y))
        plate.polyline(points, fill=color, width=8 if color == TEAL else 4)
        plate.text((bx, by - 26), label, size=17, bold=color == TEAL, fill=color, anchor="mm")
    plate.text((445, 756), "stationary does not always mean minimum", size=18, anchor="mm")

    transform = axes(plate, (880, 340, 1410, 730), x_label="position q", y_label="momentum p",
                     x_range=(-2, 2), y_range=(-2, 2))
    for energy, color in ((0.7, BLUE_LIGHT), (1.15, BLUE), (1.65, PLUM)):
        points = [(energy * math.cos(i / 100 * 2 * math.pi),
                   energy * 0.75 * math.sin(i / 100 * 2 * math.pi)) for i in range(101)]
        plot_curve(plate, transform, points, fill=color, width=5)
    plate.arrow(transform(1.1, 0.15), transform(1.0, 0.55), fill=CORAL, width=5, head=15)
    plate.text((1145, 770), "one orbit = constant Hamiltonian H", size=19, bold=True, anchor="mm")
    footer(plate, "Equivalent formulations reveal paths in configuration space and conserved flow in phase space.", size=25)


def draw_em_maxwell(plate: Plate) -> None:
    left, right = two_panel_boxes()
    panel(plate, left, "DISPLACEMENT CURRENT")
    panel(plate, right, "SELF-PROPAGATING WAVE")
    plate.draw.ellipse((350, 425, 550, 625), fill=BLUE_LIGHT, outline=BLUE, width=6)
    plate.draw.ellipse((420, 495, 480, 555), fill=PAPER_LIGHT, outline=CORAL, width=4)
    plate.dot((450, 525), 10, fill=CORAL, outline=CORAL, width=1)
    plate.text((450, 320), "top view of capacitor gap", size=20, bold=True, anchor="mm")
    plate.text((450, 660), "⊙ changing E flux through page", size=18, bold=True,
               math_face=True, anchor="mm")
    for radius in (55, 88, 120):
        plate.draw.ellipse((450 - radius, 525 - radius, 450 + radius, 525 + radius),
                           outline=PLUM, width=4)
    plate.text((450, 710), "circular B field", size=18, bold=True, fill=PLUM, anchor="mm")
    plate.text((450, 752), "∮B·dl = μ₀(I + ε₀ dΦE/dt)", size=20, bold=True,
               math_face=True, anchor="mm")

    wave(plate, (880, 365, 1410, 565), cycles=2.5, amplitude=72, fill=CORAL, width=7)
    plate.text((920, 340), "E: vertical in the page", size=19, bold=True, fill=CORAL)
    for index in range(11):
        x = 880 + index * 53
        phase = math.sin(2 * math.pi * 2.5 * index / 10)
        radius = 8 + 12 * abs(phase)
        plate.draw.ellipse((x - radius, 640 - radius, x + radius, 640 + radius),
                           fill=PAPER_LIGHT, outline=BLUE, width=3)
        if phase > 0.12:
            plate.dot((x, 640), max(3, radius * .22), fill=BLUE, outline=BLUE, width=1)
        elif phase < -0.12:
            arm = radius * .48
            plate.draw.line((x - arm, 640 - arm, x + arm, 640 + arm), fill=BLUE, width=3)
            plate.draw.line((x - arm, 640 + arm, x + arm, 640 - arm), fill=BLUE, width=3)
    plate.text((920, 600), "B: dot out / cross into page", size=18, bold=True, fill=BLUE)
    plate.arrow((900, 735), (1380, 735), fill=TEAL, width=7, head=20)
    plate.text((1145, 780), "E ⟂ B ⟂ travel; c = fλ", size=20, bold=True,
               math_face=True, anchor="mm")
    footer(plate, "Changing electric and magnetic fields complete Maxwell's circuit and carry energy through space.", size=25)


def draw_quantum(plate: Plate) -> None:
    left, right = two_panel_boxes()
    panel(plate, left, "RELATIVE STATE SHAPES")
    panel(plate, right, "MANY DETECTIONS")
    transform = axes(plate, (170, 350, 720, 715), x_label="x", y_label="relative scale (peak = 1)",
                     x_range=(-3, 3), y_range=(-1.2, 1.2))
    psi = [(x / 40, math.sin(2 * math.pi * (x / 40 + 3) / 6)) for x in range(-120, 121, 3)]
    prob = [(x / 40, math.sin(2 * math.pi * (x / 40 + 3) / 6) ** 2) for x in range(-120, 121, 3)]
    plot_curve(plate, transform, psi, fill=PLUM, width=5)
    plot_curve(plate, transform, prob, fill=TEAL, width=7)
    plate.text((200, 315), "scaled ψ: sign matters", size=17, bold=True, fill=PLUM)
    plate.text((465, 315), "relative |ψ|²: peak 1", size=17, bold=True, fill=TEAL)

    baseline = 715
    plate.draw.line((870, baseline, 1420, baseline), fill=INK, width=5)
    counts = (2, 9, 18, 15, 4, 15, 19, 11, 3)
    for index, count in enumerate(counts):
        x = 900 + index * 61
        height = count * 10
        plate.draw.rectangle((x, baseline - height, x + 42, baseline),
                             fill=TEAL_LIGHT, outline=TEAL, width=3)
    plate.text((1145, 340), "reproducible example: 96 trials", size=19, bold=True, anchor="mm")
    plate.text((1145, 760), "individual outcomes vary; the distribution follows |ψ|²", size=18, anchor="mm")
    footer(plate, "The relative |ψ|² shape predicts where detections accumulate; normalization supplies absolute density.", size=23)


def draw_statmech(plate: Plate) -> None:
    left, right = two_panel_boxes()
    panel(plate, left, "16 MICROSTATES")
    panel(plate, right, "MULTIPLICITY → ENTROPY")
    states = [(a, b, c, d) for a in (0, 1) for b in (0, 1) for c in (0, 1) for d in (0, 1)]
    for index, state in enumerate(states):
        x0 = 165 + (index % 4) * 140
        y0 = 345 + (index // 4) * 100
        for coin, value in enumerate(state):
            x = x0 + coin * 28
            plate.dot((x, y0), 10, fill=GOLD_LIGHT if value else BLUE_LIGHT,
                      outline=GOLD if value else BLUE, width=2)
        plate.text((x0 + 42, y0 + 27), str(sum(state)), size=14, fill=INK_SOFT, anchor="mm")
    plate.text((445, 760), "each row is one exact arrangement", size=18, anchor="mm")

    multiplicities = (1, 4, 6, 4, 1)
    baseline = 700
    for index, value in enumerate(multiplicities):
        x = 900 + index * 115
        plate.draw.rectangle((x, baseline - value * 50, x + 72, baseline),
                             fill=PLUM_LIGHT if value < 6 else TEAL_LIGHT,
                             outline=PLUM if value < 6 else TEAL, width=3)
        plate.text((x + 36, baseline + 28), str(index), size=18, bold=True, anchor="mm")
        plate.text((x + 36, baseline - value * 50 - 24), str(value), size=20, bold=True, anchor="mm")
    plate.text((1145, 350), "Ω = 1 : 4 : 6 : 4 : 1", size=24, bold=True, math_face=True, anchor="mm")
    plate.text((1145, 760), "S = k ln Ω; the middle macrostate is most probable", size=18, anchor="mm")
    footer(plate, "Macrostates with more compatible microstates have greater multiplicity and entropy.", size=25)


def draw_relativity(plate: Plate) -> None:
    left, right = two_panel_boxes()
    panel(plate, left, "LIGHT CONE")
    panel(plate, right, "BARN–POLE SIMULTANEITY")
    transform = axes(plate, (170, 350, 720, 730), x_label="x", y_label="ct",
                     x_range=(-2, 2), y_range=(0, 3))
    plate.polyline((transform(-2, 2), transform(0, 0), transform(2, 2)), fill=GOLD, width=8)
    plate.draw.polygon((transform(-2, 2), transform(0, 0), transform(2, 2)),
                       fill=hex_rgba(GOLD_LIGHT, 70))
    plate.polyline((transform(0, 0), transform(0.9, 2.7)), fill=TEAL, width=7)
    plate.text((290, 425), "lightlike", size=17, bold=True, fill=GOLD)
    plate.text((540, 470), "timelike worldline", size=17, bold=True, fill=TEAL)
    plate.text((445, 765), "Δs² = c²Δt² − Δx² is invariant", size=18, bold=True, anchor="mm")

    plate.draw.rounded_rectangle((880, 460, 1410, 600), radius=12,
                                 fill=BLUE_LIGHT, outline=BLUE, width=4)
    plate.text((1145, 530), "barn", size=28, bold=True, anchor="mm")
    plate.draw.line((950, 620, 1340, 620), fill=INK, width=12)
    plate.text((1145, 655), "moving pole", size=20, bold=True, anchor="mm")
    plate.dashed_line((930, 390), (930, 700), fill=CORAL, width=5)
    plate.dashed_line((1360, 390), (1360, 700), fill=CORAL, width=5)
    plate.text((1145, 350), "barn frame: doors close together", size=19, bold=True, anchor="mm")
    plate.text((1145, 760), "pole frame: the two door events are not simultaneous", size=18, anchor="mm")
    footer(plate, "Frames preserve timelike causal order; spacelike event order can reverse.", size=25)


def draw_solid_state(plate: Plate) -> None:
    for box, heading in zip(((116, 212, 548, 800), (584, 212, 1016, 800), (1052, 212, 1484, 800)),
                            ("INSULATOR", "SEMICONDUCTOR", "DOPED")):
        panel(plate, box, heading)
    configs = ((332, 170, 0, 0), (800, 85, 2, 2), (1268, 85, 6, 0))
    for x, gap, carriers, holes in configs:
        plate.draw.rounded_rectangle((x - 155, 390, x + 155, 475), radius=10,
                                     fill=BLUE_LIGHT, outline=BLUE, width=4)
        plate.draw.rounded_rectangle((x - 155, 475 + gap, x + 155, 560 + gap), radius=10,
                                     fill=GOLD_LIGHT, outline=GOLD, width=4)
        plate.text((x, 432), "conduction band", size=18, bold=True, anchor="mm")
        plate.text((x, 518 + gap), "valence band", size=18, bold=True, anchor="mm")
        plate.double_arrow((x - 130, 480), (x - 130, 470 + gap), fill=CORAL, width=4)
        plate.text((x - 112, 480 + gap / 2), "Eg", size=16, bold=True, fill=CORAL)
        for index in range(carriers):
            plate.dot((x - 95 + index * 38, 410), 8, fill=TEAL_LIGHT, outline=TEAL, width=2)
        for index in range(holes):
            plate.dot((x - 95 + index * 38, 518 + gap), 8,
                      fill=PAPER_LIGHT, outline=CORAL, width=3)
            plate.text((x - 95 + index * 38, 518 + gap), "+", size=12,
                       bold=True, fill=CORAL, anchor="mm")
        plate.text((x, 742),
                   "wide gap" if gap > 100 else ("thermal carriers" if carriers == 2 else "donor carriers"),
                   size=20, bold=True, anchor="mm")
    footer(plate, "Band gaps control excitation; temperature and doping change carrier population without closing the gap.", size=24)


def _quark(plate: Plate, center: tuple[float, float], label: str, color: str) -> None:
    plate.dot(center, 35, fill=hex_rgba(color, 90), outline=color, width=4)
    plate.text(center, label, size=25, bold=True, anchor="mm")


def draw_particles(plate: Plate) -> None:
    left, right = two_panel_boxes()
    panel(plate, left, "COMPOSITE CHARGES")
    panel(plate, right, "DECAY CONSERVATION")
    for center, labels, total in (((300, 500), ("u +⅔", "u +⅔", "d −⅓"), "+1 proton"),
                                  ((590, 500), ("u +⅔", "d −⅓", "d −⅓"), "0 neutron")):
        _quark(plate, (center[0], 430), labels[0], CORAL)
        _quark(plate, (center[0] - 55, 530), labels[1], BLUE)
        _quark(plate, (center[0] + 55, 530), labels[2], TEAL)
        plate.draw.ellipse((center[0] - 105, 375, center[0] + 105, 605), outline=PLUM, width=4)
        plate.text((center[0], 655), total, size=20, bold=True, anchor="mm")
    plate.text((445, 742), "quark charges add to the hadron charge", size=18, anchor="mm")

    plate.text((1145, 380), "n -> p + e- + antineutrino", size=26, bold=True,
               math_face=True, anchor="mm")
    rows = (("charge", "0", "+1 −1 +0 = 0"),
            ("baryon no.", "1", "1 +0 +0 = 1"),
            ("lepton no.", "0", "0 +1 −1 = 0"))
    for i, (name, before, after) in enumerate(rows):
        y = 480 + i * 82
        plate.text((900, y), name, size=18, bold=True)
        plate.text((1100, y), before, size=20, anchor="mm")
        plate.arrow((1160, y), (1220, y), fill=GRID, width=4, head=13)
        plate.text((1385, y), after, size=18, anchor="ra")
    plate.text((1145, 742), "allowed channels conserve every required quantum number", size=18, anchor="mm")
    footer(plate, "Particle identities are constrained by additive charges and conservation laws at every interaction.", size=24)


def draw_experiment(plate: Plate) -> None:
    left, right = two_panel_boxes()
    panel(plate, left, "RANDOM VS SYSTEMATIC")
    panel(plate, right, "CALIBRATE, FIT, CHECK")
    plate.draw.line((180, 520, 710, 520), fill=INK, width=5)
    true_x = 445
    plate.draw.line((true_x, 360, true_x, 700), fill=TEAL, width=5)
    plate.text((true_x, 330), "true value", size=18, bold=True, fill=TEAL, anchor="mm")
    for index, dx in enumerate((-80, 35, -25, 72, -8)):
        plate.dot((true_x + dx, 430 + index * 48), 10, fill=BLUE, outline=BLUE, width=1)
    for index, dx in enumerate((92, 110, 78, 103, 88)):
        plate.dot((true_x + dx, 430 + index * 48), 9, fill=CORAL, outline=CORAL, width=1)
    plate.text((445, 752), "averaging reduces random uncertainty; bias remains", size=16,
               bold=True, anchor="mm")

    transform = axes(plate, (880, 350, 1410, 720), x_label="input", y_label="reading",
                     x_range=(0, 5), y_range=(0, 7))
    line = [(x / 20, 0.7 + 1.05 * x / 20) for x in range(101)]
    plot_curve(plate, transform, line, fill=TEAL, width=5)
    measurements = ((.5, 1.1), (1.2, 2.2), (2.0, 2.7), (2.8, 3.9), (3.5, 4.1), (4.2, 6.7))
    for x, y in measurements:
        px, py = transform(x, y)
        expected_y = 0.7 + 1.05 * x
        _, ey = transform(x, expected_y)
        plate.draw.line((px, py, px, ey), fill=CORAL, width=3)
        plate.dot((px, py), 9, fill=GOLD_LIGHT, outline=GOLD, width=2)
    plate.text((1145, 760), "residuals expose offset, scatter, and outliers", size=18, anchor="mm")
    footer(plate, "Precision, calibration, residuals, and uncertainty test a claim more honestly than a neat line.", size=24)


def draw_qft(plate: Plate) -> None:
    left, right = two_panel_boxes()
    panel(plate, left, "ONE BOSONIC MODE: OCCUPATION n")
    panel(plate, right, "AMPLITUDE BOOKKEEPING")
    wave(plate, (190, 325, 690, 455), cycles=2, amplitude=40, fill=PLUM, width=5)
    plate.text((445, 475), "bosonic spatial mode u(x)—not the mean field", size=16,
               bold=True, anchor="mm")
    for number in (0, 1, 2):
        y = 735 - number * 90
        plate.draw.line((250, y, 650, y), fill=INK_SOFT, width=4)
        for quantum in range(number):
            plate.dot((540 + quantum * 36, y - 28), 10,
                      fill=GOLD_LIGHT, outline=GOLD, width=2)
        plate.text((225, y), f"n={number}", size=18, bold=True, anchor="rm")
        plate.text((445, y - 18), f"E = ({number}+½)ℏω", size=16,
                   math_face=True, anchor="mm")

    upper_vertex = (1090, 500)
    lower_vertex = (1220, 585)
    plate.arrow((915, 405), upper_vertex, fill=BLUE, width=6, head=18)
    plate.arrow(upper_vertex, (1375, 390), fill=BLUE, width=6, head=18)
    plate.arrow((915, 690), lower_vertex, fill=BLUE, width=6, head=18)
    plate.arrow(lower_vertex, (1375, 715), fill=BLUE, width=6, head=18)
    mediator = []
    for index in range(17):
        t = index / 16
        base_x = upper_vertex[0] + (lower_vertex[0] - upper_vertex[0]) * t
        base_y = upper_vertex[1] + (lower_vertex[1] - upper_vertex[1]) * t
        offset = 0 if index in (0, 16) else (12 if index % 2 else -12)
        mediator.append((base_x + offset * .55, base_y - offset * .84))
    plate.polyline(mediator, fill=CORAL, width=6)
    plate.dot(upper_vertex, 10, fill=GOLD, outline=GOLD, width=1)
    plate.dot(lower_vertex, 10, fill=GOLD, outline=GOLD, width=1)
    plate.text((1145, 345), "valid 2 → 2 exchange contribution", size=19,
               bold=True, anchor="mm")
    plate.text((1145, 755), "internal mediator line contributes to the amplitude", size=17, anchor="mm")
    plate.text((1145, 735), "not a photographed particle trajectory", size=18, bold=True, fill=CORAL, anchor="mm")
    footer(plate, "For one bosonic mode, occupation sets energy—not classical field amplitude; a Feynman diagram is not a literal path.", size=21)


def draw_gr_cosmo(plate: Plate) -> None:
    left, right = two_panel_boxes()
    panel(plate, left, "CURVED SPACETIME")
    panel(plate, right, "EXPANDING SCALE FACTOR")
    cx, cy = 445, 530
    for offset in range(-240, 241, 60):
        points = []
        for x in range(190, 701, 8):
            pull = 95 * math.exp(-((x - cx) / 120) ** 2) * (1 - abs(offset) / 350)
            points.append((x, cy + offset + pull * (1 if offset <= 0 else -1)))
        plate.polyline(points, fill=GRID, width=3)
    for offset in range(-240, 241, 60):
        points = []
        for y in range(300, 761, 8):
            pull = 95 * math.exp(-((y - cy) / 120) ** 2) * (1 - abs(offset) / 350)
            points.append((cx + offset + pull * (1 if offset <= 0 else -1), y))
        plate.polyline(points, fill=GRID, width=3)
    plate.draw.ellipse((385, 470, 505, 590), fill=INK, outline=PLUM, width=8)
    plate.draw.ellipse((360, 445, 530, 615), outline=GOLD, width=5)
    plate.text((445, 720), "stress-energy sources curvature", size=18, bold=True, anchor="mm")
    plate.text((445, 760), "schematic coordinate grid—not a physical sheet", size=16, anchor="mm")

    epochs = ((960, 470, 38), (1145, 530, 62), (1350, 650, 90))
    for x, y, radius in epochs:
        plate.draw.ellipse((x - radius, y - radius, x + radius, y + radius),
                           fill=hex_rgba(BLUE_LIGHT, 70), outline=BLUE, width=3)
        for angle in range(0, 360, 90):
            rad = math.radians(angle)
            plate.dot((x + radius * .58 * math.cos(rad), y + radius * .58 * math.sin(rad)),
                      7, fill=GOLD, outline=GOLD, width=1)
    plate.arrow((1010, 500), (1090, 520), fill=TEAL, width=6, head=16)
    plate.arrow((1210, 565), (1280, 610), fill=TEAL, width=6, head=16)
    wave(plate, (900, 330, 1390, 410), cycles=4, amplitude=20, fill=PLUM, width=4)
    wave(plate, (900, 715, 1390, 795), cycles=2, amplitude=20, fill=CORAL, width=4)
    plate.text((1145, 300), "short λ early", size=17, bold=True, anchor="mm")
    plate.text((1145, 810), "larger a stretches λ; expansion has no center", size=17, bold=True, anchor="mm")
    footer(plate, "Einstein's equation links stress-energy to geometry; cosmic expansion stretches unbound separations and wavelengths.", size=22)


def draw_condensed(plate: Plate) -> None:
    left, right = two_panel_boxes()
    panel(plate, left, "PERFECT CONDUCTOR")
    panel(plate, right, "MEISSNER SUPERCONDUCTOR")
    plate.draw.rounded_rectangle((300, 390, 590, 680), radius=30,
                                 fill=BLUE_LIGHT, outline=BLUE, width=5)
    for x in (350, 410, 470, 530):
        plate.arrow((x, 330), (x, 740), fill=PLUM, width=4, head=14)
    plate.text((445, 760), "history-dependent trapped flux", size=18, bold=True, anchor="mm")
    plate.text((445, 340), "field present before cooling", size=18, bold=True, anchor="mm")

    plate.draw.rounded_rectangle((1000, 390, 1290, 680), radius=30,
                                 fill=TEAL_LIGHT, outline=TEAL, width=5)
    for x in (920, 970, 1320, 1370):
        plate.arrow((x, 330), (x, 740), fill=PLUM, width=4, head=14)
    plate.polyline(((970, 330), (970, 380), (940, 440), (940, 630), (970, 690), (970, 740)),
                   fill=PLUM, width=5)
    plate.polyline(((1320, 330), (1320, 380), (1350, 440), (1350, 630), (1320, 690), (1320, 740)),
                   fill=PLUM, width=5)
    plate.text((1145, 760), "Meissner state expels B", size=19, bold=True, anchor="mm")
    plate.text((1145, 340), "type-I: T < Tc and H < Hc", size=18, bold=True, anchor="mm")
    footer(plate, "Below the type-I critical field, cooling through Tc expels flux; zero resistance alone does not establish superconductivity.", size=21)


def draw_quantum_info(plate: Plate) -> None:
    left, right = two_panel_boxes()
    panel(plate, left, "TELEPORTATION: WHAT TRAVELS?")
    panel(plate, right, "CORRELATION ≠ SIGNAL")
    plate.dot((180, 420), 18, fill=GOLD, outline=GOLD, width=1)
    plate.text((180, 382), "unknown |psi>", size=16, bold=True, anchor="mm")
    plate.draw.rounded_rectangle((300, 370, 470, 500), radius=15,
                                 fill=PLUM_LIGHT, outline=PLUM, width=4)
    plate.text((385, 435), "Bell measure", size=18, bold=True, anchor="mm")
    plate.arrow((202, 420), (296, 420), fill=GOLD, width=6, head=17)
    plate.dot((250, 625), 16, fill=BLUE, outline=BLUE, width=1)
    plate.dot((550, 625), 16, fill=BLUE, outline=BLUE, width=1)
    plate.draw.line((266, 625, 534, 625), fill=BLUE, width=5)
    plate.text((400, 662), "shared entangled pair", size=15, fill=BLUE, anchor="mm")
    plate.arrow((250, 606), (330, 500), fill=BLUE, width=6, head=17)
    plate.arrow((470, 435), (605, 435), fill=TEAL, width=7, head=19)
    plate.text((538, 402), "2 classical bits", size=16, bold=True, fill=TEAL, anchor="mm")
    plate.draw.rounded_rectangle((605, 370, 715, 500), radius=14,
                                 fill=GREEN_LIGHT, outline=GREEN, width=4)
    plate.text((660, 435), "correct", size=17, bold=True, anchor="mm")
    plate.arrow((550, 606), (625, 500), fill=BLUE, width=6, head=17)
    plate.arrow((715, 435), (754, 435), fill=GOLD, width=6, head=15)
    plate.text((445, 750), "Bell result + Bob's entangled half reconstructs |psi>", size=16, anchor="mm")

    plate.draw.line((960, 360, 960, 700), fill=INK_SOFT, width=5)
    plate.draw.line((1330, 360, 1330, 700), fill=INK_SOFT, width=5)
    plate.dot((1145, 390), 16, fill=BLUE, outline=BLUE, width=1)
    plate.draw.line((1145, 406, 960, 520), fill=BLUE, width=5)
    plate.draw.line((1145, 406, 1330, 520), fill=BLUE, width=5)
    for x, label in ((960, "Alice: random"), (1330, "Bob: random")):
        plate.draw.rounded_rectangle((x - 76, 500, x + 76, 570), radius=12,
                                     fill=GOLD_LIGHT, outline=GOLD, width=3)
        plate.text((x, 535), label, size=16, bold=True, anchor="mm")
    plate.text((1145, 625), "CHSH combines four setting pairs", size=19, bold=True, anchor="mm")
    plate.text((1145, 662), "(a,b)  (a,b')  (a',b)  (a',b')", size=17, anchor="mm")
    plate.text((1145, 710), "either local record alone remains random", size=17, anchor="mm")
    footer(plate, "Entanglement supplies nonclassical correlations, but usable information still needs a classical channel.", size=23)


def draw_frontier(plate: Plate) -> None:
    left, right = two_panel_boxes()
    panel(plate, left, "ROTATION-CURVE INFERENCE")
    panel(plate, right, "BULLET CLUSTER EVIDENCE")
    transform = axes(plate, (170, 350, 720, 720), x_label="radius", y_label="orbital speed",
                     x_range=(0, 10), y_range=(0, 10))
    visible = [(x / 10, 8 / math.sqrt(max(.7, x / 10))) for x in range(8, 101, 2)]
    observed = [(x / 10, 7.0 + .15 * math.sin(x / 7)) for x in range(8, 101, 2)]
    plot_curve(plate, transform, visible, fill=CORAL, width=5)
    plot_curve(plate, transform, observed, fill=TEAL, width=7)
    plate.text((470, 420), "observed: nearly flat", size=18, bold=True, fill=TEAL)
    plate.text((470, 610), "visible mass prediction", size=18, bold=True, fill=CORAL)
    plate.text((445, 760), "the gap motivates extra mass or modified dynamics", size=17, anchor="mm")

    for x, color in ((1010, CORAL_LIGHT), (1280, CORAL_LIGHT)):
        plate.draw.ellipse((x - 95, 440, x + 95, 630), fill=hex_rgba(color, 90),
                           outline=CORAL, width=4)
    for x in (930, 1360):
        plate.draw.ellipse((x - 75, 400, x + 75, 550), fill=hex_rgba(BLUE_LIGHT, 90),
                           outline=BLUE, width=4)
        plate.text((x, 380), "lensing mass", size=16, bold=True, fill=BLUE, anchor="mm")
    plate.text((1145, 650), "hot gas lags behind collisionless mass peaks", size=18, bold=True, anchor="mm")
    plate.text((1145, 720), "one observation constrains—but does not alone settle—the model", size=17, anchor="mm")
    footer(plate, "Frontier physics advances by comparing quantitative predictions with converging, imperfect evidence.", size=24)


SPECS: dict[str, Spec] = {
    "phys.4.classical": spec("phys.4.classical", "Classical Mechanics (Advanced)", 4,
        "phys-action-hamiltonian-phase-space",
        "Trial trajectories approach a stationary-action path beside closed constant-Hamiltonian orbits in phase space.",
        "Lagrangian and Hamiltonian views encode the same dynamics while exposing different constraints and conserved structure.", draw_classical),
    "phys.4.em-maxwell": spec("phys.4.em-maxwell", "Electrodynamics", 4,
        "phys-maxwell-displacement-wave",
        "A capacitor-gap top view shows changing through-page electric flux and circular magnetic field beside an orthogonal electromagnetic wave.",
        "Maxwell's displacement current completes Ampere's law; electromagnetic fields propagate mutually perpendicular to each other and travel.", draw_em_maxwell),
    "phys.4.quantum": spec("phys.4.quantum", "Quantum Mechanics", 4,
        "phys-wavefunction-probability-histogram",
        "A scaled signed wavefunction and relative squared-magnitude shape are compared with repeated position detections.",
        "The state supplies amplitudes; the normalized squared magnitude predicts the distribution of measurement outcomes.", draw_quantum),
    "phys.4.statmech": spec("phys.4.statmech", "Statistical Mechanics", 4,
        "phys-microstates-multiplicity-entropy",
        "Sixteen four-coin microstates produce the one-four-six-four-one multiplicity distribution over macrostates.",
        "Entropy grows with multiplicity, making the balanced macrostate most probable without making any microstate more likely.", draw_statmech),
    "phys.4.relativity": spec("phys.4.relativity", "Relativity", 4,
        "phys-light-cone-simultaneity",
        "A Minkowski light cone and barn-pole event diagram distinguish invariant causality from frame-dependent simultaneity.",
        "Observers share the interval and timelike causal order, while spacelike door-event order and simultaneity depend on frame.", draw_relativity),
    "phys.4.solid-state": spec("phys.4.solid-state", "Solid State Physics", 4,
        "phys-band-gaps-carriers-doping",
        "Energy-band diagrams compare a wide-gap insulator, thermally excited semiconductor, and donor-doped semiconductor.",
        "Conductivity follows available carriers and states; doping changes population without simply erasing the band gap.", draw_solid_state),
    "phys.4.particles": spec("phys.4.particles", "Particle Physics", 4,
        "phys-quark-charge-decay-conservation",
        "Quark charges add to proton and neutron charges beside a beta-decay ledger for three conserved quantum numbers.",
        "Allowed composite particles and decay channels satisfy additive charge, baryon-number, and lepton-number constraints.", draw_particles),
    "phys.4.experiment": spec("phys.4.experiment", "The Art of Experiment", 4,
        "phys-experiment-bias-residuals",
        "Repeated readings contrast random scatter and systematic bias beside a calibration fit with residuals and an outlier.",
        "A sound experiment separates imprecision from bias, calibrates its scale, and tests residual structure rather than appearance.", draw_experiment),
    "phys.5.qft": spec("phys.5.qft", "Quantum Field Theory", 5,
        "phys-qft-field-quanta-amplitudes",
        "One bosonic spatial mode sits above occupation-number energy levels beside a Feynman contribution with external and internal lines.",
        "For a bosonic mode, occupation sets quantized energy rather than classical field amplitude; diagram lines organize amplitudes, not photographed trajectories.", draw_qft),
    "phys.5.gr-cosmo": spec("phys.5.gr-cosmo", "General Relativity and Cosmology", 5,
        "phys-curvature-expansion-redshift",
        "A schematic coordinate grid curves near compact stress-energy beside expanding unbound galaxy separations and a stretched light wave.",
        "Stress-energy and geometry couple locally, while the cosmological scale factor expands unbound separations and redshifts wavelengths without a center.", draw_gr_cosmo),
    "phys.5.condensed": spec("phys.5.condensed", "Condensed Matter", 5,
        "phys-meissner-perfect-conductor",
        "History-dependent flux remains trapped in a perfect conductor while a type-I Meissner state below its critical field expels flux.",
        "Cooling below the critical temperature expels flux only within the critical-field regime; zero resistance alone does not define superconductivity.", draw_condensed),
    "phys.5.quantum-info": spec("phys.5.quantum-info", "Quantum Information", 5,
        "phys-teleportation-correlation-causality",
        "Quantum teleportation routes two classical bits beside Bell-correlated measurements whose individual records remain random.",
        "Entanglement enables nonclassical joint statistics and state transfer, but neither produces faster-than-light signalling.", draw_quantum_info),
    "phys.5.frontier": spec("phys.5.frontier", "Open Problems", 5,
        "phys-dark-matter-evidence-comparison",
        "A flat observed rotation curve differs from visible-mass prediction beside separated gas and lensing peaks in a cluster collision.",
        "Dark-matter inference combines mismatched rotation speeds with lensing and collision evidence while retaining model uncertainty.", draw_frontier),
}
