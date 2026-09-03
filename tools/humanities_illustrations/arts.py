"""Lesson-specific explanatory plates for Arts & Music."""

from __future__ import annotations

import math
from typing import Dict, Sequence, Tuple

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
    box_text,
    draw_branch,
    draw_comparison,
    draw_cycle,
    draw_flow,
    draw_network,
    draw_timeline,
    draw_tracks,
    footer,
    panel,
    pill,
    spec,
)


DOMAIN = "arts"


def flow(node_id: str, title: str, stage: int, plate_id: str, alt: str,
         caption: str, steps: Sequence[Tuple[str, str]], conclusion: str) -> Spec:
    return spec(node_id, title, stage, DOMAIN, plate_id, alt, caption,
                lambda plate: draw_flow(plate, steps, conclusion))


def compare(node_id: str, title: str, stage: int, plate_id: str, alt: str,
            caption: str, columns: Sequence[Tuple[str, str, str]], conclusion: str,
            relation: str = "COMPARE THE SAME ARTISTIC PROBLEM") -> Spec:
    return spec(node_id, title, stage, DOMAIN, plate_id, alt, caption,
                lambda plate: draw_comparison(
                    plate, columns, conclusion, relation=relation))


def timeline(node_id: str, title: str, stage: int, plate_id: str, alt: str,
             caption: str, events: Sequence[Tuple[str, str, str]], conclusion: str,
             qualifier: str = "TIME RUNS LEFT → RIGHT") -> Spec:
    return spec(node_id, title, stage, DOMAIN, plate_id, alt, caption,
                lambda plate: draw_timeline(
                    plate, events, conclusion, qualifier=qualifier))


def _note(plate: Plate, x: float, y: float, *, color: str = INK,
          stem: bool = True, filled: bool = True) -> None:
    plate.draw.ellipse((x - 15, y - 11, x + 15, y + 11),
                       fill=color if filled else PAPER_LIGHT, outline=color, width=4)
    if stem:
        plate.draw.line((x + 14, y, x + 14, y - 92), fill=color, width=5)


def _staff(plate: Plate, box: Tuple[float, float, float, float]) -> Sequence[float]:
    x0, y0, x1, _ = box
    ys = [y0 + index * 34 for index in range(5)]
    for y in ys:
        plate.draw.line((x0, y, x1, y), fill=INK_SOFT, width=3)
    return ys


def _draw_singing(plate: Plate) -> None:
    panel(plate, (120, 236, 1480, 782), fill=BLUE_LIGHT, outline=BLUE)
    pill(plate, (800, 272), "ONE FOUR-BEAT PHRASE", color=BLUE, size=19)
    xs = [320, 590, 860, 1130]
    syllables = ["HEL-", "LO", "MY", "FRIEND"]
    pitch_y = [520, 440, 480, 390]
    for index, (x, syllable, y) in enumerate(zip(xs, syllables, pitch_y), start=1):
        plate.draw.line((x, 340, x, 680), fill=GRID, width=3)
        plate.dot((x, 650), 24, fill=GOLD_LIGHT, outline=GOLD, width=5)
        plate.text((x, 650), str(index), size=22, bold=True, anchor="mm")
        _note(plate, x, y, color=(TEAL, BLUE, PLUM, CORAL)[index - 1])
        plate.text((x, 585), syllable, size=27, bold=True, anchor="mm")
    plate.arrow((250, 715), (1350, 715), fill=GOLD, width=6, head=20)
    plate.text((800, 747), "steady pulse →", size=22, bold=True, fill=GOLD, anchor="mm")
    plate.polyline(list(zip(xs, pitch_y)), fill=PLUM, width=5)
    plate.text((1260, 420), "pitch contour", size=21, bold=True, fill=PLUM, anchor="mm")
    footer(plate, "The beat stays even while the melody rises and falls; listening keeps the group together.")


def _draw_beat_melody(plate: Plate) -> None:
    panel(plate, (120, 230, 1480, 780), fill=PAPER_LIGHT, outline=TEAL)
    pill(plate, (800, 270), "ALIGN SOUND TO FOUR PULSES", color=TEAL, size=19)
    xs = [300, 570, 840, 1110, 1380]
    for x in xs:
        plate.draw.line((x, 330, x, 704), fill=GRID, width=3)
    # Four equal beat intervals.
    for index, x in enumerate(xs[:-1], start=1):
        plate.dot((x, 670), 22, fill=GOLD_LIGHT, outline=GOLD, width=5)
        plate.text((x, 670), str(index), size=20, bold=True, anchor="mm")
    # Durations: quarter, two eighths, half = four beats.
    _note(plate, 300, 470, color=BLUE)
    _note(plate, 570, 430, color=TEAL)
    _note(plate, 705, 455, color=TEAL)
    _note(plate, 840, 400, color=PLUM, filled=False)
    plate.draw.line((854, 400, 854, 308), fill=PLUM, width=5)
    plate.draw.line((840, 400, 1110, 400), fill=PLUM, width=6)
    plate.text((300, 540), "1 beat", size=22, bold=True, fill=BLUE, anchor="mm")
    plate.text((638, 540), "½ + ½", size=22, bold=True, fill=TEAL, anchor="mm")
    plate.text((975, 540), "2 beats", size=22, bold=True, fill=PLUM, anchor="mm")
    plate.polyline(((300, 470), (570, 430), (705, 455), (840, 400), (1110, 400)),
                   fill=CORAL, width=4)
    box_text(plate, (170, 300, 275, 580), "MELODY\n(pitch)", size=20, bold=True, fill=CORAL)
    footer(plate, "Rhythm places durations on the pulse; melody gives those sounds a pitch contour.")


def _draw_color_composition(plate: Plate) -> None:
    # Complementary color contrast.
    panel(plate, (120, 240, 540, 770), fill=PAPER_LIGHT, outline=BLUE)
    pill(plate, (330, 278), "COLOR RELATION", color=BLUE, size=18)
    plate.draw.ellipse((210, 350, 360, 500), fill="#315fba", outline=INK, width=4)
    plate.draw.ellipse((300, 430, 450, 580), fill="#d9822b", outline=INK, width=4)
    plate.double_arrow((280, 620), (380, 620), fill=PLUM, width=5)
    box_text(plate, (155, 650, 505, 738), "Blue and orange sit opposite on this simplified wheel: adjacency heightens contrast.",
             size=20, minimum=15)
    # Balance.
    panel(plate, (570, 240, 1010, 770), fill=PAPER_LIGHT, outline=TEAL)
    pill(plate, (790, 278), "VISUAL BALANCE", color=TEAL, size=18)
    plate.draw.line((640, 550, 940, 550), fill=INK, width=7)
    plate.draw.polygon(((790, 550), (740, 675), (840, 675)), fill=GOLD_LIGHT, outline=GOLD)
    plate.draw.ellipse((655, 410, 775, 530), fill=CORAL_LIGHT, outline=CORAL, width=5)
    for x in (860, 910):
        plate.draw.ellipse((x - 30, 470, x + 30, 530), fill=BLUE_LIGHT, outline=BLUE, width=4)
    box_text(plate, (610, 650, 970, 738), "One large form can balance several smaller forms through size, distance and contrast.",
             size=20, minimum=15)
    # Perspective.
    panel(plate, (1040, 240, 1480, 770), fill=PAPER_LIGHT, outline=CORAL)
    pill(plate, (1260, 278), "DEPTH CUE", color=CORAL, size=18)
    vanishing = (1260, 430)
    plate.dot(vanishing, 10, fill=GOLD_LIGHT, outline=GOLD, width=4)
    for start in ((1080, 700), (1440, 700), (1080, 540), (1440, 540)):
        plate.draw.line((*start, *vanishing), fill=INK_SOFT, width=4)
    plate.draw.rectangle((1120, 585, 1195, 700), outline=BLUE, width=5)
    plate.draw.rectangle((1300, 500, 1345, 560), outline=TEAL, width=5)
    box_text(plate, (1075, 650, 1445, 738), "Parallel edges appear to converge; farther forms are drawn smaller.",
             size=20, minimum=15)
    footer(plate, "Color, balance and perspective are choices that direct attention—not automatic recipes.")


def _draw_music_reading(plate: Plate) -> None:
    panel(plate, (120, 230, 1480, 780), fill=PAPER_LIGHT, outline=BLUE)
    pill(plate, (800, 270), "A COMPLETE 4/4 BAR", color=BLUE, size=19)
    ys = _staff(plate, (255, 366, 1400, 535))

    # A vector treble clef: its lower loop wraps the staff's G line.
    plate.draw.arc((280, 330, 360, 455), 72, 332, fill=PLUM, width=8)
    plate.draw.line((336, 350, 310, 542), fill=PLUM, width=8)
    plate.draw.ellipse((282, ys[3] - 34, 344, ys[3] + 34),
                       outline=PLUM, width=7)
    plate.dot((313, ys[3]), 7, fill=PLUM, outline=PLUM)
    box_text(plate, (245, 300, 390, 340), "TREBLE CLEF", size=16,
             minimum=12, bold=True, fill=PLUM)
    plate.text((420, 440), "4\n4", size=38, bold=True, math_face=True, anchor="mm")

    # Quarter; two beamed eighths; half. Brackets bind symbols to durations.
    _note(plate, 560, ys[3], color=BLUE)
    _note(plate, 760, ys[2], color=TEAL)
    _note(plate, 860, ys[1], color=TEAL)
    plate.draw.line((774, ys[2] - 90, 874, ys[1] - 90), fill=TEAL, width=8)
    _note(plate, 1120, ys[1], color=PLUM, filled=False)
    plate.draw.line((1134, ys[1], 1134, ys[1] - 92), fill=PLUM, width=5)
    plate.draw.line((1400, 342, 1400, 550), fill=INK, width=8)

    def duration_bracket(x0: float, x1: float, label: str, color: str) -> None:
        y = 576
        plate.draw.line((x0, y, x1, y), fill=color, width=5)
        plate.draw.line((x0, y - 14, x0, y + 14), fill=color, width=5)
        plate.draw.line((x1, y - 14, x1, y + 14), fill=color, width=5)
        box_text(plate, (x0 - 12, y + 14, x1 + 12, y + 62), label,
                 size=19, minimum=14, bold=True, fill=color)

    duration_bracket(500, 620, "quarter = 1 beat", BLUE)
    duration_bracket(690, 930, "two eighths = 1 beat", TEAL)
    duration_bracket(1010, 1270, "half = 2 beats", PLUM)
    box_text(plate, (330, 668, 1270, 735),
             "1 + (½ + ½) + 2 = 4 beats", size=31,
             minimum=23, bold=True, fill=GOLD)
    footer(plate, "The staff locates pitch; note shapes encode duration; the time signature organizes beats.")


def _draw_photography(plate: Plate) -> None:
    panel(plate, (120, 240, 620, 770), fill=BLUE_LIGHT, outline=BLUE)
    pill(plate, (370, 278), "FRAMING CHANGES EMPHASIS", color=BLUE, size=17)
    # wide shot
    plate.draw.rectangle((170, 340, 570, 500), outline=INK, width=6)
    plate.draw.line((170, 450, 570, 450), fill=GREEN, width=5)
    plate.dot((360, 410), 22, fill=GOLD_LIGHT, outline=GOLD, width=4)
    plate.draw.line((360, 432, 360, 480), fill=GOLD, width=6)
    plate.text((370, 520), "wide: place + person", size=21, bold=True, anchor="mm")
    # close shot
    plate.draw.rectangle((235, 555, 505, 690), outline=INK, width=6)
    plate.draw.ellipse((300, 565, 440, 685), fill=GOLD_LIGHT, outline=GOLD, width=5)
    plate.text((370, 720), "close: face + feeling", size=21, bold=True, anchor="mm")
    panel(plate, (660, 240, 1480, 770), fill=PAPER_LIGHT, outline=CORAL)
    pill(plate, (1070, 278), "MOVIES BUILD MEANING ACROSS SHOTS", color=CORAL, size=17)
    shots = [
        ("SHOT 1", "door opens", BLUE),
        ("SHOT 2", "face reacts", TEAL),
        ("SHOT 3", "empty chair", PLUM),
    ]
    for index, (head, detail, color) in enumerate(shots):
        x0 = 705 + index * 245
        panel(plate, (x0, 365, x0 + 205, 610), fill=PAPER_LIGHT, outline=color, radius=12)
        pill(plate, (x0 + 102, 395), head, color=color, size=15)
        box_text(plate, (x0 + 18, 440, x0 + 187, 570), detail, size=26,
                 minimum=18, bold=True, fill=color)
        if index < 2:
            plate.arrow((x0 + 210, 490), (x0 + 238, 490), fill=CORAL, width=5, head=14)
    box_text(plate, (720, 635, 1420, 730),
             "The cut asks the viewer to connect separate images into an event.",
             size=23, minimum=17, bold=True, fill=CORAL)
    footer(plate, "A camera records light, but framing and editing select what the audience notices and infers.")


def _still_life(plate: Plate, box: Tuple[float, float, float, float], mode: str,
                color: str) -> None:
    x0, y0, x1, y1 = box
    panel(plate, box, fill=PAPER_LIGHT, outline=color, radius=14)
    table_y = y1 - 68
    apple = (x0 + 54, y1 - 182, x0 + 168, y1 - 72)
    vase = ((x0 + 238, y1 - 244), (x0 + 294, y1 - 244),
            (x0 + 302, y1 - 207), (x0 + 344, y1 - 92),
            (x0 + 326, y1 - 72), (x0 + 206, y1 - 72),
            (x0 + 188, y1 - 92), (x0 + 230, y1 - 207))
    plate.draw.line((x0 + 25, table_y, x1 - 25, table_y), fill=INK_SOFT, width=4)
    if mode == "perspective":
        vanishing = ((x0 + x1) / 2, y0 + 62)
        plate.draw.line((x0 + 25, table_y, *vanishing), fill=GRID, width=3)
        plate.draw.line((x1 - 25, table_y, *vanishing), fill=GRID, width=3)
        plate.draw.ellipse(apple, fill=CORAL_LIGHT, outline=CORAL, width=5)
        plate.draw.arc((apple[0] + 12, apple[1] + 9, apple[2] - 8, apple[3] - 8),
                       95, 260, fill=GOLD, width=5)
        plate.draw.line((x0 + 110, y1 - 184, x0 + 118, y1 - 207), fill=GREEN, width=5)
        plate.draw.polygon(vase, fill=BLUE_LIGHT, outline=BLUE)
        plate.draw.ellipse((x0 + 238, y1 - 252, x0 + 294, y1 - 236),
                           fill=PAPER_LIGHT, outline=BLUE, width=4)
        plate.draw.line((x0 + 220, y1 - 96, x0 + 319, y1 - 190), fill=TEAL, width=5)
    elif mode == "light":
        plate.draw.ellipse(apple, fill=GOLD_LIGHT, outline=CORAL, width=5)
        plate.draw.line((x0 + 110, y1 - 184, x0 + 118, y1 - 207), fill=GREEN, width=5)
        plate.draw.polygon(vase, fill=TEAL_LIGHT, outline=TEAL)
        plate.draw.ellipse((x0 + 238, y1 - 252, x0 + 294, y1 - 236),
                           fill=PAPER_LIGHT, outline=TEAL, width=4)
        # Broken touches preserve the subject while making changing light visible.
        for offset in range(0, 88, 16):
            plate.draw.arc((apple[0] - offset / 7, apple[1] + offset / 8,
                            apple[2] + offset / 8, apple[3] - offset / 10),
                           205, 330, fill=GOLD if offset % 32 == 0 else CORAL, width=6)
        for y in range(int(y1 - 218), int(y1 - 92), 24):
            plate.draw.line((x0 + 215, y, x0 + 250, y - 13), fill=BLUE, width=6)
            plate.draw.line((x0 + 285, y + 5, x0 + 326, y - 8), fill=TEAL, width=6)
    else:
        # The same apple and vase remain legible, now faceted and seen from
        # several implied viewpoints.
        faceted_apple = ((x0 + 60, y1 - 132), (x0 + 83, y1 - 174),
                         (x0 + 126, y1 - 185), (x0 + 163, y1 - 152),
                         (x0 + 158, y1 - 102), (x0 + 116, y1 - 72),
                         (x0 + 72, y1 - 91))
        plate.draw.polygon(faceted_apple, fill=CORAL_LIGHT, outline=CORAL)
        plate.draw.line((x0 + 60, y1 - 132, x0 + 158, y1 - 102), fill=GOLD, width=6)
        plate.draw.line((x0 + 116, y1 - 72, x0 + 126, y1 - 185), fill=PLUM, width=5)
        plate.draw.line((x0 + 110, y1 - 184, x0 + 121, y1 - 207), fill=GREEN, width=5)
        plate.draw.polygon(vase, fill=BLUE_LIGHT, outline=BLUE)
        plate.draw.line((x0 + 230, y1 - 207, x0 + 326, y1 - 72), fill=CORAL, width=6)
        plate.draw.line((x0 + 294, y1 - 244, x0 + 206, y1 - 72), fill=TEAL, width=6)
        plate.draw.line((x0 + 188, y1 - 92, x0 + 344, y1 - 92), fill=PLUM, width=6)
        plate.draw.ellipse((x0 + 238, y1 - 252, x0 + 294, y1 - 236),
                           fill=PAPER_LIGHT, outline=BLUE, width=4)


def _draw_art_movements(plate: Plate) -> None:
    labels = [
        ("RENAISSANCE", "perspective + modeled volume", "perspective", BLUE),
        ("IMPRESSIONISM", "fleeting light + visible touch", "light", TEAL),
        ("CUBISM", "multiple viewpoints + fractured plane", "fracture", CORAL),
    ]
    for index, (head, detail, mode, color) in enumerate(labels):
        x0 = 120 + index * 455
        pill(plate, (x0 + 210, 250), head, color=color, size=17)
        _still_life(plate, (x0, 290, x0 + 420, 675), mode, color)
        box_text(plate, (x0 + 12, 686, x0 + 408, 760), detail, size=21,
                 minimum=16, bold=True, fill=color)
    footer(plate, "The same subject can be reorganized by different aims; movements overlap and contain disagreement.")


def _draw_music_theory(plate: Plate) -> None:
    panel(plate, (120, 235, 1480, 780), fill=PAPER_LIGHT, outline=PLUM)
    pill(plate, (800, 272), "FROM SCALE TO HARMONY", color=PLUM, size=19)
    notes = ["C", "D", "E", "F", "G", "A", "B", "C"]
    intervals = ["W", "W", "H", "W", "W", "W", "H"]
    xs = [240 + index * 160 for index in range(8)]
    ys = [500 - index * 24 for index in range(8)]
    for index, (x, y, note_name) in enumerate(zip(xs, ys, notes)):
        plate.dot((x, y), 30, fill=(GOLD_LIGHT if index in (0, 2, 4, 7) else BLUE_LIGHT),
                  outline=(GOLD if index in (0, 2, 4, 7) else BLUE), width=5)
        plate.text((x, y), note_name, size=24, bold=True, anchor="mm")
        if index < 7:
            plate.arrow((x + 38, y - 2), (xs[index + 1] - 38, ys[index + 1] - 2),
                        fill=TEAL, width=5, head=15)
            plate.text(((x + xs[index + 1]) / 2, (y + ys[index + 1]) / 2 - 34),
                       intervals[index], size=18, bold=True, fill=TEAL, anchor="mm")
    panel(plate, (210, 615, 730, 745), fill=GOLD_LIGHT, outline=GOLD)
    box_text(plate, (230, 628, 710, 686), "C MAJOR TRIAD = 1 + 3 + 5", size=24,
             bold=True, fill=GOLD)
    box_text(plate, (230, 688, 710, 733), "C – E – G: stack alternate scale degrees", size=19, minimum=15)
    panel(plate, (850, 615, 1390, 745), fill=PLUM_LIGHT, outline=PLUM)
    box_text(plate, (870, 628, 1370, 686), "G–B–D  →  C–E–G", size=25,
             bold=True, fill=PLUM)
    box_text(plate, (870, 688, 1370, 733), "dominant tension → tonic resolution", size=19, minimum=15)
    footer(plate, "A key organizes pitch relationships; chords select simultaneous scale degrees and create motion.")


def _draw_film_meaning(plate: Plate) -> None:
    # Shared neutral face in two sequences.
    def face(cx: float, cy: float) -> None:
        plate.draw.ellipse((cx - 62, cy - 72, cx + 62, cy + 72),
                           fill=GOLD_LIGHT, outline=GOLD, width=5)
        plate.dot((cx - 22, cy - 12), 5, fill=INK, outline=INK)
        plate.dot((cx + 22, cy - 12), 5, fill=INK, outline=INK)
        plate.draw.line((cx - 20, cy + 30, cx + 20, cy + 30), fill=INK, width=4)
    for row, (object_name, reading, color) in enumerate([
        ("BOWL OF SOUP", "viewer infers hunger", TEAL),
        ("EMPTY HOSPITAL BED", "viewer infers worry or grief", PLUM),
    ]):
        y = 350 + row * 285
        panel(plate, (120, y - 110, 1480, y + 125), fill=PAPER_LIGHT, outline=color)
        face(330, y)
        plate.arrow((420, y), (570, y), fill=color, width=7, head=20)
        panel(plate, (600, y - 78, 910, y + 78), fill=(TEAL_LIGHT if row == 0 else PLUM_LIGHT), outline=color)
        box_text(plate, (620, y - 60, 890, y + 60), object_name, size=25,
                 minimum=18, bold=True, fill=color)
        plate.arrow((930, y), (1050, y), fill=color, width=7, head=20)
        box_text(plate, (1070, y - 68, 1440, y + 68), reading, size=25,
                 minimum=18, bold=True, fill=color)
    pill(plate, (330, 220), "IDENTICAL FACE SHOT", color=GOLD, size=17)
    footer(plate, "Editing makes adjacent shots interact; the audience supplies a connection the camera never recorded.")


def _draw_counterpoint(plate: Plate) -> None:
    panel(plate, (120, 235, 1480, 780), fill=PAPER_LIGHT, outline=PLUM)
    pill(plate, (800, 270), "TWO LINES — HORIZONTAL AND VERTICAL LOGIC", color=PLUM, size=18)
    xs = [250 + index * 155 for index in range(8)]
    upper = [390, 350, 370, 320, 345, 300, 330, 285]
    lower = [570, 540, 510, 535, 485, 505, 455, 480]
    plate.polyline(list(zip(xs, upper)), fill=BLUE, width=8)
    plate.polyline(list(zip(xs, lower)), fill=CORAL, width=8)
    for x, y in zip(xs, upper):
        _note(plate, x, y, color=BLUE, stem=False)
    for x, y in zip(xs, lower):
        _note(plate, x, y, color=CORAL, stem=False)
    for index, x in enumerate(xs):
        plate.dashed_line((x, upper[index] + 18), (x, lower[index] - 18),
                          fill=GRID, width=3, dash=8, gap=8)
    plate.text((180, 335), "line A", size=23, bold=True, fill=BLUE)
    plate.text((180, 565), "line B", size=23, bold=True, fill=CORAL)
    for index, (label, color) in enumerate((("A", BLUE), ("B", TEAL), ("A′", PLUM))):
        x0 = 310 + index * 330
        panel(plate, (x0, 655, x0 + 280, 735), fill=(BLUE_LIGHT, TEAL_LIGHT, PLUM_LIGHT)[index],
              outline=color, radius=10)
        box_text(plate, (x0 + 8, 663, x0 + 272, 727), label, size=29, bold=True, fill=color)
    footer(plate, "Counterpoint coordinates independent melodies; form organizes how larger sections return and change.")


def _draw_semiotic_triangle(plate: Plate) -> None:
    """Keep one visible form fixed while mapping its semiotic relations."""

    box_text(plate, (170, 194, 1430, 236),
             "ONE VISIBLE FORM — MEANING CHANGES THROUGH RELATIONS",
             size=22, bold=True, fill=INK_SOFT)
    cards = [
        ((120, 258, 505, 420), "SIGNIFIER",
         "Red pigment, triangular boundary, scale and placement.", BLUE, BLUE_LIGHT),
        ((1095, 258, 1480, 420), "POSSIBLE REFERENT",
         "A hazard, mountain, political emblem—or no depicted object.", TEAL, TEAL_LIGHT),
        ((120, 590, 505, 752), "INTERPRETANT",
         "Learned codes let a situated viewer infer warning, motion or affiliation.", PLUM, PLUM_LIGHT),
        ((1095, 590, 1480, 752), "FRAME / CONTEXT",
         "Street, gallery label, protest or market changes how the form is taken up.", GOLD, GOLD_LIGHT),
    ]
    center = (800, 505)
    for box, _, _, color, _ in cards:
        x = box[2] if box[2] < center[0] else box[0]
        y = (box[1] + box[3]) / 2
        start = (615, 460 if y < center[1] else 560) if x < center[0] else (
            985, 460 if y < center[1] else 560)
        plate.double_arrow(start, (x, y), fill=color, width=5)
    for box, heading, detail, color, light in cards:
        panel(plate, box, fill=light, outline=color, radius=16)
        box_text(plate, (box[0] + 14, box[1] + 10, box[2] - 14, box[1] + 68),
                 heading, size=22, minimum=15, bold=True, fill=color)
        box_text(plate, (box[0] + 18, box[1] + 70, box[2] - 18, box[3] - 10),
                 detail, size=18, minimum=13)
    panel(plate, (615, 350, 985, 660), fill=PAPER_LIGHT, outline=CORAL)
    plate.draw.polygon(((800, 390), (688, 585), (912, 585)),
                       fill=CORAL_LIGHT, outline=CORAL, width=9)
    plate.draw.polygon(((800, 424), (724, 558), (876, 558)),
                       fill=PAPER_LIGHT, outline=CORAL, width=5)
    box_text(plate, (650, 596, 950, 642), "ONE RED TRIANGLE", size=22,
             minimum=16, bold=True, fill=CORAL)
    footer(plate, "Context constrains interpretation without making either form or evidence irrelevant.")


_ITEMS = [
    spec(
        "arts.0.drawing", "Drawing and Painting", 0, DOMAIN,
        "observe-mark-compare-cycle-plate",
        "Four cards in a closed arrow loop move from looking at the largest shapes, comparing height, width and angles, making a light mark, and looking again to notice a mismatch and revise.",
        "Observation drawing is a repeated comparison between subject and mark. Imaginative drawing enters the same loop through memory, play and deliberate choices.",
        lambda plate: draw_cycle(
            plate,
            [
                ("LOOK", "Find edges, spaces and the largest shapes."),
                ("COMPARE", "Check height ÷ width, angles and relative position."),
                ("MARK", "Place a light line or patch of paint."),
                ("LOOK AGAIN", "Notice a mismatch; keep, erase or change it."),
            ],
            "Drawing improves through seeing, marking and revising—not by naming the object once.",
            center_text=("EYE ↔ HAND", "The picture changes what the artist notices next."),
        ),
    ),
    spec(
        "arts.0.singing", "Songs and Sounds", 0, DOMAIN,
        "beat-pitch-phrase-plate",
        "A worked four-beat phrase aligns four numbered pulse dots with the syllables HEL-, LO, MY and FRIEND while colored notes and a connecting line rise and fall above the steady beat.",
        "A song combines a steady pulse, changing rhythm and a pitch contour. Singers listen and breathe together so separate voices can coordinate.",
        _draw_singing,
    ),
    flow(
        "arts.0.dance", "Moving to Music", 0, "four-count-movement-plate",
        "Four numbered cards connected left to right align a four-count rhythm with bend on one, step on two, reach on three and turn on four, ending ready to repeat on the next count one.",
        "Counting connects musical time to movement. A dancer can change shape, level, direction and energy while keeping the same four-beat phrase.",
        [
            ("1 — BEND", "Lower the body on the strongest pulse."),
            ("2 — STEP", "Transfer weight and travel sideways."),
            ("3 — REACH", "Stretch upward while the pulse continues."),
            ("4 — TURN", "Change direction and arrive ready for count one."),
        ],
        "Beat organizes when movement happens; rhythm and dynamics shape how it happens.",
    ),
    compare(
        "arts.1.crafts", "Making Things", 1, "craft-processes-materials-plate",
        "Three process columns compare additive sculpture by joining clay, subtractive carving by removing wood, and collage assembly by arranging and attaching paper, each linked to an irreversible or reversible material decision.",
        "Making methods change material in different ways. Planning joins, cuts and order helps a maker choose what can still be revised.",
        [
            ("ADDITIVE SCULPTURE", "Build volume by joining clay coils or pieces.", "Add → press or score → support → refine"),
            ("SUBTRACTIVE CARVING", "Reveal a form by removing wood or stone.", "Cut removed material cannot simply be put back"),
            ("COLLAGE / ASSEMBLY", "Arrange separate parts, test placement, then attach.", "Dry layout remains revisable before glue"),
        ],
        "Match the sequence of actions to the material's properties and what can be undone.",
        relation="THREE WAYS MATERIAL BECOMES FORM",
    ),
    compare(
        "arts.1.instruments", "Musical Instruments", 1, "instrument-vibration-families-plate",
        "Four columns trace how a plucked string, blown air column, struck membrane and struck solid body begin vibrating, how the instrument reinforces that vibration and the resulting sound.",
        "Instrument families can be compared by what first vibrates. Resonators and player technique then shape loudness, pitch and tone color.",
        [
            ("STRING", "Pluck or bow → string vibrates.", "Body and air reinforce: guitar, violin"),
            ("AIR COLUMN", "Blow or buzz → enclosed air vibrates.", "Tube length changes pitch: flute, trumpet"),
            ("MEMBRANE", "Strike → stretched skin vibrates.", "Shell reinforces: many drums"),
            ("SOLID BODY", "Strike or shake → object itself vibrates.", "Shape and material matter: bell, shaker"),
        ],
        "Sound begins with vibration, but families describe the source—not every detail of timbre.",
        relation="ACTION → FIRST VIBRATING PART → RESONANCE",
    ),
    spec(
        "arts.1.beat", "Beat and Melody", 1, DOMAIN,
        "beat-duration-melody-plate",
        "A worked measure aligns four numbered beat dots to a quarter note, two eighth notes and a half note totaling four beats, while a red contour connects their changing pitches.",
        "The beat is the steady reference; rhythm divides its duration; melody arranges pitches through time. One bar can make all three relationships visible.",
        _draw_beat_melody,
    ),
    timeline(
        "arts.2.art-history-intro", "Art Through Time", 2, "art-media-time-plate",
        "A long timeline moves from cave and rock art before 30,000 BCE through ancient public monuments, manuscript and workshop traditions, print and photography, and modern to digital practices, each paired with a material constraint rather than ranked as progress.",
        "Art history follows changing materials, patrons, audiences and purposes. New media add possibilities without making earlier practices obsolete or less complex.",
        [
            ("before 30,000 BCE", "Rock + cave art", "mineral pigments, engraving and place-based meaning"),
            ("ancient worlds", "Public objects", "architecture, sculpture and images tied to ritual and power"),
            ("c. 500–1500", "Manuscript + workshop", "portable texts and images; many regional traditions"),
            ("c. 1450–1900", "Print + photography", "mechanical reproduction changes scale and audience"),
            ("1900s–today", "Modern to digital", "abstraction, mass media, installation, code and networks"),
        ],
        "The timeline tracks changing conditions of making—not a ladder from simple to advanced.",
        qualifier="SELECTED MEDIA HISTORIES — DATES OVERLAP ACROSS REGIONS",
    ),
    spec(
        "arts.2.color-theory", "Color and Composition", 2, DOMAIN,
        "color-balance-perspective-plate",
        "Three worked panels show blue and orange as a simplified complementary pair, one large form balancing two smaller forms at a distance, and receding rectangles whose parallel edges converge at a vanishing point.",
        "Color relations, visual balance and perspective guide attention in different ways. They are compositional tools, not universal formulas for beauty.",
        _draw_color_composition,
    ),
    spec(
        "arts.2.music-reading", "Reading Music", 2, DOMAIN,
        "four-four-measure-plate",
        "A treble-clef five-line staff in four-four time contains a quarter note, two beamed eighth notes and a half note; brackets bind the symbols to one beat, one combined beat and two beats, and the equation one plus one-half plus one-half plus two equals four.",
        "Notation coordinates pitch and duration. In this worked 4/4 measure, one quarter plus two eighths plus one half fills all four beats.",
        _draw_music_reading,
    ),
    flow(
        "arts.2.theatre", "Drama and Theatre", 2, "script-to-live-event-plate",
        "A five-step theatre process runs from a script's words and stage directions through rehearsal and blocking, coordinated design, live performance and audience response that informs the next performance.",
        "Theatre is a live collaboration. Text, bodies, space, light, sound and audience attention combine differently in every production and performance.",
        [
            ("SCRIPT / IDEA", "Dialogue, action and stage directions propose what may happen."),
            ("REHEARSE", "Actors test intention, voice, timing and relationships."),
            ("BLOCK + DESIGN", "Movement, set, costume, light and sound direct attention."),
            ("PERFORM LIVE", "Many cues coordinate in shared time before an audience."),
            ("AUDIENCE RESPONSE", "Laughter, silence and interpretation affect rhythm and future choices."),
        ],
        "A production interprets a script; it does not merely copy words onto a stage.",
    ),
    spec(
        "arts.2.photography", "Photography & Film", 2, DOMAIN,
        "framing-editing-selection-plate",
        "A wide camera frame emphasizes a person in place while a close frame emphasizes a face; beside them, three shots of a door opening, a reacting face and an empty chair are connected by editing arrows.",
        "Photography selects a frame from space; film editing selects a sequence through time. Both choices guide what viewers notice and infer.",
        _draw_photography,
    ),
    spec(
        "arts.3.art-history", "Art History", 3, DOMAIN,
        "same-subject-art-movements-plate",
        "The same apple-and-blue-vase still life stays in the same positions across three panels: a linear-perspective modeled study, an Impressionist treatment with broken light marks, and a Cubist treatment with faceted shapes and multiple implied viewpoints.",
        "Comparing a shared subject reveals different artistic problems and conventions. Renaissance, Impressionist and Cubist practices overlapped internally and historically rather than forming a simple improvement sequence.",
        _draw_art_movements,
    ),
    spec(
        "arts.3.music-theory", "Music Theory", 3, DOMAIN,
        "scale-triad-resolution-plate",
        "Eight labeled notes C through C rise through the whole-step and half-step pattern of a major scale; highlighted scale degrees one, three and five form C–E–G, while G–B–D points to C–E–G as dominant-to-tonic motion.",
        "A scale orders intervals, a chord combines scale degrees, and harmonic function describes how chords create expectation and resolution within a tonal context.",
        _draw_music_theory,
    ),
    spec(
        "arts.3.design", "Design & Architecture", 3, DOMAIN,
        "design-test-revision-cycle-plate",
        "A five-step design loop moves from a user's need through measurable constraints, multiple prototypes, observation during testing and revision, with form and function written together at the center.",
        "Design turns needs and constraints into testable proposals. A prototype is evidence: observing use reveals where form supports or obstructs function.",
        lambda plate: draw_cycle(
            plate,
            [
                ("UNDERSTAND", "Who uses it, where, and for what purpose?"),
                ("CONSTRAIN", "Size, safety, access, cost, climate and material."),
                ("PROTOTYPE", "Make several concrete alternatives, not one favorite."),
                ("TEST", "Watch real use; measure failure as well as success."),
                ("REVISE", "Change the proposal and record the tradeoff."),
            ],
            "Form follows a tested purpose—and purposes themselves should be questioned.",
            center_text=("FORM ↔ FUNCTION", "Evidence from use sends the process around again."),
        ),
    ),
    timeline(
        "arts.3.music-history", "History of Music", 3, "music-periods-overlap-plate",
        "An overlapping timeline marks Baroque around 1600 to 1750, Classical around 1750 to 1820, Romantic in the long nineteenth century, jazz from the early twentieth century and electronic and global popular practices from the later twentieth century, with a warning that labels center particular histories.",
        "Period names help organize some European art-music histories; jazz and later genres grow from different communities and exchanges. Styles overlap, borrow and persist beyond textbook dates.",
        [
            ("c. 1600–1750", "Baroque", "continuo, counterpoint and contrasting affect in European courts and churches"),
            ("c. 1750–1820", "Classical", "formal balance and changing public institutions; dates approximate"),
            ("c. 1800–1910", "Romantic", "expanded color, form and expressive ideals; overlaps other traditions"),
            ("from c. 1900", "Jazz", "Black American creation joining improvisation, groove and changing forms"),
            ("later 1900s–today", "Beyond", "recording, electronics, migration and global circulation transform genres"),
        ],
        "A useful timeline shows overlap and whose history a category was built to describe.",
        qualifier="SELECTED, OVERLAPPING HISTORIES — STYLE DOES NOT CHANGE ON A SINGLE DATE",
    ),
    spec(
        "arts.3.film-studies", "Film & Media", 3, DOMAIN,
        "editing-context-meaning-plate",
        "Two editing rows reuse an identical neutral face shot: when followed by a bowl of soup the viewer may infer hunger, while an empty hospital bed prompts worry or grief, showing how adjacent images alter interpretation.",
        "A shot gains meaning from sequence as well as content. Editing can suggest a relation that no single shot establishes, while viewers may still interpret it differently.",
        _draw_film_meaning,
    ),
    spec(
        "arts.4.aesthetics", "Aesthetics", 4, DOMAIN,
        "aesthetic-judgment-lenses-plate",
        "A reciprocal network places one artwork at the center and connects formal organization, maker and historical context, viewer experience and institutional framing, each with a different question about aesthetic judgment.",
        "Aesthetic judgments can cite formal qualities, experience, context and institutions. Disagreement becomes more informative when people identify the evidence and value behind a response.",
        lambda plate: draw_network(
            plate,
            ("ONE ARTWORK", "The object stays the same while questions and relations change."),
            [
                ("FORM", "How do rhythm, proportion, color and material organize attention?"),
                ("CONTEXT", "Who made it, for whom, under what historical conditions?"),
                ("EXPERIENCE", "What perception, emotion or imagination occurs for this viewer?"),
                ("INSTITUTION", "How do museums, markets and categories frame it as art?"),
            ],
            "Taste is neither a bare fact nor a context-free formula: reasons make judgment discussable.",
            edge_word="SEVERAL GROUNDS FOR JUDGMENT",
        ),
    ),
    flow(
        "arts.4.art-theory", "Art Criticism & Theory", 4,
        "critical-reading-evidence-chain-plate",
        "A five-step critical reading begins with observable details, analyzes formal relations, researches cultural and historical context, tests an interpretation against evidence and considers a counter-reading or missing voice.",
        "Critical interpretation separates what is visible from what is inferred, then uses context and counterevidence. Symbols do not carry one universal meaning across cultures.",
        [
            ("DESCRIBE", "Inventory visible material, scale, placement and repeated motifs before evaluating."),
            ("ANALYZE FORM", "Trace contrast, rhythm, hierarchy, viewpoint and relation to a viewer."),
            ("CONTEXTUALIZE", "Research maker, audience, function and the motif's local history."),
            ("INTERPRET", "Make a claim that explains several observations rather than one detail."),
            ("TEST / COUNTERREAD", "Ask what resists the claim and whose standpoint or knowledge is absent."),
        ],
        "An interpretation grows stronger when evidence could have shown it wrong.",
    ),
    spec(
        "arts.4.composition", "Composition & Analysis", 4, DOMAIN,
        "counterpoint-form-analysis-plate",
        "Two colored melodic lines move independently across eight moments while dashed vertical links show their simultaneous intervals; below, blocks labeled A, B and A-prime show return with variation in larger form.",
        "Musical analysis reads horizontally and vertically: each contrapuntal line has a contour, their simultaneous intervals interact, and larger form organizes recurrence and change.",
        _draw_counterpoint,
    ),
    spec(
        "arts.4.world-arts", "World Arts & Music", 4, DOMAIN,
        "world-practices-structure-context-plate",
        "Three parallel rows compare West African ensemble polyrhythm, North Indian raga performance and Javanese gamelan interlocking through structure, social setting and transmission, without ranking them against one canon.",
        "World arts require comparison without flattening traditions. Musical structure, social function and ways of learning belong together, and every named tradition contains regional and historical variation.",
        lambda plate: draw_tracks(
            plate,
            [
                ("WEST AFRICAN ENSEMBLES", [("structure", "interlocking parts and layered pulse in many traditions"), ("setting", "dance, ceremony and social participation may be inseparable"), ("transmission", "embodied listening, imitation and specialist teaching")]),
                ("NORTH INDIAN RAGA", [("structure", "melodic framework, tala and improvisational development"), ("setting", "performance unfolds through musician–audience attention"), ("transmission", "long apprenticeship and lineage alongside modern institutions")]),
                ("JAVANESE GAMELAN", [("structure", "cyclic form and interlocking stratified parts"), ("setting", "ensemble relates to dance, theatre, ritual and community"), ("transmission", "group practice and local court or village traditions")]),
            ],
            "Compare relationships inside practices, then name the limits of every broad label.",
            direction="THREE CASES — EACH DIVERSE, LIVING AND HISTORICALLY CHANGING",
        ),
    ),
    spec(
        "arts.5.theory-advanced", "Advanced Aesthetics & Theory", 5, DOMAIN,
        "art-meaning-semiotic-network-plate",
        "A plain red triangle is visibly centered between four connected cards for signifier, possible referent, interpretant and frame or context; examples show how the same form can function differently in a street, gallery, protest or market.",
        "Meaning emerges through signs, conventions, contexts and interpreters. Competing readings remain answerable to the work's form, circulation and historical evidence.",
        _draw_semiotic_triangle,
    ),
    spec(
        "arts.5.creative-practice", "Mastery of a Craft", 5, DOMAIN,
        "creative-practice-feedback-loop-plate",
        "A six-step cycle links targeted practice, making a complete work, critique against an intention, revision, portfolio selection and reflective planning, with evidence from each pass feeding the next rather than a straight path to mastery.",
        "A sustained creative practice alternates focused skill-building with complete work, external critique, revision and curation. Originality emerges through accumulated choices, not inspiration alone.",
        lambda plate: draw_cycle(
            plate,
            [
                ("PRACTICE", "Isolate one weak skill with a measurable exercise."),
                ("MAKE", "Complete work under real material and time constraints."),
                ("CRITIQUE", "Compare intention, audience response and concrete evidence."),
                ("REVISE", "Change structure, craft or scope; preserve a version."),
                ("CURATE", "Select and sequence work to reveal decisions and growth."),
                ("REFLECT", "Name the next question, risk and practice target."),
            ],
            "Mastery is a durable feedback practice, not a finish line that eliminates uncertainty.",
            center_text=("DELIBERATE LOOP", "Records, versions and feedback make improvement visible."),
        ),
    ),
    spec(
        "arts.5.frontier", "Art at the Frontier", 5, DOMAIN,
        "generative-system-authorship-plate",
        "A generative-art system combines an artist's rules, chosen input data and controlled randomness or audience interaction, then branches into two outputs, audience input, and a curation and audit step.",
        "In generative art the artist shapes a system and its conditions, not only a single output. Authorship questions therefore include rules, data, randomness, interaction, selection and disclosure.",
        lambda plate: draw_branch(
            plate,
            ("GENERATIVE SYSTEM", "Artist-chosen rules + inputs or data + randomness or live interaction"),
            [
                ("OUTPUT A", "One seed produces a sparse arrangement; save its parameters and provenance."),
                ("OUTPUT B", "A second seed exposes variation while the governing rule stays fixed."),
                ("AUDIENCE INPUT", "A gesture or sensor changes the work in real time within designed bounds."),
                ("CURATE + AUDIT", "Selection becomes part of authorship; inspect bias, consent and resource cost."),
            ],
            "The artwork may be the output, the process, the interaction—or an argued relation among all three.",
            relation="GENERATES",
        ),
    ),
]


SPECS: Dict[str, Spec] = {item["id"]: item for item in _ITEMS}
