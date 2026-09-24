"""Lesson-specific explanatory plates for Arts & Music."""

from __future__ import annotations

import math
import random
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


def _draw_theatre(plate: Plate) -> None:
    pill(plate, (800, 225), 'SAME LINE: “I HAVE SOMETHING TO TELL YOU.”', color=PLUM, size=25)
    for cx, revised in ((430, False), (1170, True)):
        panel(plate, (cx-300, 275, cx+300, 795), outline=TEAL if revised else CORAL)
        pill(plate, (cx, 315), "REHEARSE: MOVE B SIDEWAYS" if revised else "FIRST BLOCKING", color=TEAL if revised else CORAL, size=23)
        plate.draw.rectangle((cx-250, 375, cx+250, 630), fill=BLUE_LIGHT, outline=BLUE, width=3)
        plate.text((cx, 395), "STAGE — VIEW FROM ABOVE", size=19, anchor="mm")
        bx = cx+145 if revised else cx
        # A single audience position is the stated geometric test, not every seat.
        plate.draw.line((cx, 690, cx, 475), fill=GOLD, width=4)
        for x, y, label, tone in ((cx, 475, "A", PLUM), (bx, 565, "B", TEAL)):
            plate.draw.ellipse((x-30, y-30, x+30, y+30), fill=tone)
            plate.text((x, y), label, size=27, bold=True, fill=PAPER_LIGHT, anchor="mm")
        if revised:
            plate.arrow((cx+38, 565), (bx-38, 565), fill=CORAL, width=5, head=14)
        plate.draw.arc((cx-30, 665, cx+30, 715), 180, 360, fill=GOLD, width=6)
        plate.text((cx, 730), "ONE AUDIENCE SIGHTLINE", size=20, anchor="mm")
        plate.text((cx, 768), "A is visible along this line." if revised else "B stands between this seat and A.", size=22, anchor="mm")
    footer(plate, "Blocking changes attention. Test other seats, voice, timing and the scene’s intention too.")


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


def _draw_observation(plate: Plate) -> None:
    """A specific subject and revision, rather than a text-only process loop."""
    for x0, label, color in ((120, "1  LOOK", TEAL), (590, "2  COMPARE", CORAL),
                             (1060, "3  REVISE", BLUE)):
        panel(plate, (x0, 235, x0 + 420, 790), outline=color)
        pill(plate, (x0 + 210, 280), label, color=color, size=23)

    def cup(cx: int, width: int, *, solid: bool, color: str) -> None:
        left, right = cx - width // 2, cx + width // 2
        # Handle is behind the vessel; a hollow opening is genuinely visible.
        plate.draw.ellipse((right - 20, 410, right + 65, 530),
                           fill=PAPER_LIGHT, outline=color, width=7)
        plate.draw.ellipse((right + 5, 434, right + 42, 505),
                           fill=PAPER_LIGHT, outline=color, width=3)
        plate.draw.rounded_rectangle((left, 382, right, 585), radius=32,
                                     fill=TEAL_LIGHT if solid else PAPER_LIGHT,
                                     outline=color, width=6)
        if solid:
            plate.draw.rounded_rectangle((left + 18, 422, left + 40, 553),
                                         radius=10, fill=PAPER_LIGHT)
        plate.draw.ellipse((left, 363, right, 409),
                           fill=PAPER_LIGHT, outline=color, width=6)
        plate.draw.arc((left + 12, 377, right - 12, 403), 180, 360,
                       fill=color, width=3)

    cup(295, 190, solid=True, color=TEAL)
    cup(765, 110, solid=False, color=CORAL)
    cup(1235, 190, solid=False, color=BLUE)
    for cx in (765, 1235):
        for x in (cx - 95, cx + 95):
            plate.dashed_line((x, 340), (x, 606), fill=TEAL, width=3, dash=9, gap=8)
        plate.arrow((cx - 95, 625), (cx + 95, 625), fill=TEAL, width=3, head=12)
    for x0, text, color in (
        (120, "A wide cup. Notice its oval rim and the space inside the handle.", TEAL),
        (590, "My first outline is too narrow. The dashed guides mark the cup's width.", CORAL),
        (1060, "Widen the outline; keep its height. Look back at the cup again.", BLUE),
    ):
        box_text(plate, (x0 + 18, 655, x0 + 402, 765), text,
                 size=25, minimum=23, bold=True, fill=color)
    footer(plate, "Look → make a light mark → compare → change one thing → look again.")


def _draw_craft_processes(plate: Plate) -> None:
    """Show material changing, with the same before/after grammar in each panel."""
    for x0, label, color in ((120, "ADD CLAY", CORAL), (590, "REMOVE SOAP", TEAL),
                             (1060, "ARRANGE PAPER", BLUE)):
        panel(plate, (x0, 235, x0 + 420, 790), outline=color)
        pill(plate, (x0 + 210, 280), label, color=color, size=21)
        plate.arrow((x0 + 210, 433), (x0 + 210, 484), fill=color, width=5, head=16)
    # Loose clay coils become a hollow coil pot: added material builds height.
    for y in (337, 371, 405):
        plate.draw.rounded_rectangle((215, y - 12, 445, y + 12), radius=12,
                                     fill=CORAL_LIGHT, outline=CORAL, width=4)
    for y in (581, 551, 521):
        plate.draw.ellipse((225, y - 20, 435, y + 33),
                           fill=CORAL_LIGHT, outline=CORAL, width=4)
    plate.draw.ellipse((247, 510, 413, 537), fill=PAPER_LIGHT, outline=CORAL, width=4)
    # Block and rounded relief share the same material tone; chips show removal.
    plate.draw.rounded_rectangle((700, 319, 900, 421), radius=10,
                                 fill=TEAL_LIGHT, outline=TEAL, width=5)
    plate.draw.ellipse((700, 505, 900, 607), fill=TEAL_LIGHT, outline=TEAL, width=5)
    plate.draw.arc((718, 521, 881, 590), 200, 335, fill=TEAL, width=3)
    for points in (((680, 530), (665, 557), (685, 550)),
                   ((914, 558), (938, 572), (920, 588)),
                   ((735, 619), (762, 624), (747, 640))):
        plate.draw.polygon(points, fill=TEAL_LIGHT, outline=TEAL, width=3)
    # The identical square, triangle and door are assembled into a paper house.
    plate.draw.rectangle((1095, 341, 1170, 416), fill=GOLD_LIGHT, outline=GOLD, width=4)
    plate.draw.polygon(((1205, 402), (1260, 337), (1315, 402)),
                       fill=CORAL_LIGHT, outline=CORAL, width=4)
    plate.draw.rectangle((1380, 366, 1404, 411), fill=BLUE_LIGHT, outline=BLUE, width=4)
    plate.draw.rectangle((1232, 545, 1307, 620), fill=GOLD_LIGHT, outline=GOLD, width=4)
    plate.draw.polygon(((1215, 550), (1270, 485), (1325, 550)),
                       fill=CORAL_LIGHT, outline=CORAL, width=4)
    plate.draw.rectangle((1258, 575, 1282, 620), fill=BLUE_LIGHT, outline=BLUE, width=4)
    for x0, text, color in (
        (120, "Join coils to build a pot. Press the joins so the pieces hold together.", CORAL),
        (590, "A block becomes rounded as pieces come off. Removed material stays off.", TEAL),
        (1060, "Try the pieces in new places. Choose a layout before you glue.", BLUE),
    ):
        box_text(plate, (x0 + 18, 655, x0 + 402, 765), text,
                 size=25, minimum=23, bold=True, fill=color)
    footer(plate, "Add, remove or rearrange: different actions change what you can revise. Ask an adult before carving.")


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
    plate.draw.line((584, 338, 719, 363), fill=TEAL, width=12)
    _note(plate, 840, 400, color=PLUM, filled=False)
    plate.draw.line((854, 400, 854, 308), fill=PLUM, width=5)
    plate.draw.line((840, 400, 1380, 400), fill=PLUM, width=6)
    plate.text((300, 540), "1 beat", size=22, bold=True, fill=BLUE, anchor="mm")
    plate.text((638, 540), "½ + ½", size=22, bold=True, fill=TEAL, anchor="mm")
    plate.text((1110, 540), "2 beats", size=22, bold=True, fill=PLUM, anchor="mm")
    plate.polyline(((300, 470), (570, 430), (705, 455), (840, 400), (1380, 400)),
                   fill=CORAL, width=4)
    box_text(plate, (170, 300, 275, 580), "MELODY\n(pitch)", size=20, bold=True, fill=CORAL)
    footer(plate, "Rhythm places durations on the pulse; melody gives those sounds a pitch contour.")


def _draw_dance(plate: Plate) -> None:
    """Solid clothed figures show changing level, travel, reach and orientation."""
    tones = (BLUE, TEAL, GOLD, CORAL)
    labels = ('BEND', 'STEP', 'REACH', 'TURN')
    # Coordinates relative to each panel centre: head, shoulders, hips, hands, knees, feet.
    poses = (
        ((0,410), (-30,452), (30,452), (-24,515), (24,515), (-73,494), (73,494), (-65,554), (65,554), (-45,625), (45,625)),
        ((-20,365), (-48,407), (8,407), (-40,495), (0,495), (-90,457), (72,433), (-48,562), (51,549), (-56,625), (90,625)),
        ((0,365), (-28,407), (28,407), (-24,495), (24,495), (-66,325), (66,325), (-28,561), (28,561), (-32,625), (32,625)),
        ((15,365), (-12,407), (28,407), (-13,495), (23,495), (-65,454), (74,432), (-31,561), (38,561), (-38,625), (58,612)),
    )
    for i, (tone, label, pose) in enumerate(zip(tones, labels, poses)):
        cx = 275 + i * 350
        panel(plate, (cx-155, 245, cx+155, 775), fill=PAPER_LIGHT, outline=tone)
        pill(plate, (cx, 282), '{}  {}'.format(i+1, label), color=tone, size=21)
        head, ls, rs, lh, rh, handl, handr, kl, kr, fl, fr = pose
        def p(point):
            return (cx+point[0], point[1])
        # Broad filled limbs with rounded joints, not bare skeleton lines.
        for joints in ((ls,handl), (rs,handr), (lh,kl,fl), (rh,kr,fr)):
            plate.draw.line([p(j) for j in joints], fill=tone, width=24, joint='curve')
            for j in joints:
                x,y=p(j)
                plate.draw.ellipse((x-12,y-12,x+12,y+12), fill=tone)
        plate.draw.polygon([p(j) for j in (ls,rs,rh,lh)], fill=tone)
        x,y=p(head)
        plate.draw.ellipse((x-23,y-24,x+23,y+24), fill=GOLD_LIGHT, outline=tone, width=3)
        plate.dot((x+(12 if i==3 else 5),y-2), 3, fill=INK, outline=INK, width=1)
        plate.draw.line((cx-112,643,cx+112,643), fill=GRID, width=3)
        if i==0:
            plate.arrow((cx+105,440),(cx+105,520),fill=tone,width=5,head=14)
        elif i==1:
            plate.arrow((cx-60,684),(cx+80,684),fill=tone,width=5,head=14)
        elif i==2:
            plate.arrow((cx+110,420),(cx+110,338),fill=tone,width=5,head=14)
        else:
            plate.draw.arc((cx-82,653,cx+82,704),190,355,fill=tone,width=5)
            plate.arrow((cx+71,665),(cx+83,680),fill=tone,width=5,head=13)
        plate.text((cx,735), ('lower','travel sideways','stretch upward','change direction')[i],
                   size=20,bold=True,fill=tone,anchor='mm')
    footer(plate, 'One pose on each count; adapt the range of movement to your comfort.')


def _draw_instruments(plate: Plate) -> None:
    """Concrete vibrating parts; arrows show motion, not sound travelling in solids."""
    tones = (BLUE, TEAL, GOLD, CORAL)
    labels = ('STRING', 'AIR COLUMN', 'MEMBRANE', 'SOLID BODY')
    for i,(tone,label) in enumerate(zip(tones,labels)):
        x = 275 + 350*i
        panel(plate,(x-155,260,x+155,780),fill=PAPER_LIGHT,outline=tone)
        pill(plate,(x,305),label,color=tone,size=19)
        if i==0:
            plate.draw.rounded_rectangle((x-105,400,x+105,585),radius=55,fill=BLUE_LIGHT,outline=tone,width=4)
            plate.draw.ellipse((x-32,470,x+32,530),fill=INK_SOFT)
            plate.draw.line((x-115,485,x+115,485),fill=GRID,width=3)
            for end in (x-115,x+115):
                plate.draw.line((end,463,end,507),fill=INK_SOFT,width=6)
            points=[(x-115+j*230/40,485-30*math.sin(j*math.pi/40)) for j in range(41)]
            plate.polyline(points,fill=tone,width=6)
            plate.arrow((x,378),(x,442),fill=tone,width=5,head=15)
            plate.text((x,365),'pluck',size=22,bold=True,fill=tone,anchor='mm')
            detail='string moves\nbody reinforces sound'
        elif i==1:
            plate.draw.rectangle((x-115,450,x+115,540),fill=TEAL_LIGHT,outline=tone,width=4)
            # Open ends and longitudinal particle motion, not a waving tube.
            plate.draw.line((x-115,455,x-115,535),fill=PAPER_LIGHT,width=7)
            plate.draw.line((x+115,455,x+115,535),fill=PAPER_LIGHT,width=7)
            for dx in (-76,-62,-48,0,47,61,75):
                for dy in (478,507): plate.dot((x+dx,dy),4,fill=tone,outline=tone,width=1)
            plate.double_arrow((x-46,575),(x+46,575),fill=tone,width=4)
            plate.arrow((x-95,391),(x-55,443),fill=tone,width=5,head=15)
            plate.text((x,365),'blow across an edge',size=19,bold=True,fill=tone,anchor='mm')
            detail='air moves back + forth\ntube selects resonances'
        elif i==2:
            plate.draw.rectangle((x-102,470,x+102,590),fill=GOLD_LIGHT,outline=tone,width=4)
            plate.draw.arc((x-102,560,x+102,620),0,180,fill=tone,width=4)
            plate.draw.ellipse((x-102,434,x+102,500),fill=PAPER_LIGHT,outline=tone,width=5)
            plate.draw.arc((x-80,447,x+80,484),0,180,fill=tone,width=5)
            plate.draw.line((x+88,371,x+12,430),fill=INK_SOFT,width=10)
            plate.dot((x+8,434),14,fill=GOLD_LIGHT,outline=tone,width=3)
            plate.arrow((x-40,382),(x-40,432),fill=tone,width=5,head=14)
            detail='stretched skin flexes\nair + shell reinforce'
        else:
            plate.draw.polygon(((x-32,423),(x+32,423),(x+65,536),(x+96,561),(x-96,561),(x-65,536)),fill=CORAL_LIGHT,outline=tone)
            plate.draw.ellipse((x-96,545,x+96,581),fill=PAPER_LIGHT,outline=tone,width=4)
            plate.draw.line((x,445,x+72,557),fill=tone,width=4)
            plate.dot((x+72,557),12,fill=tone,outline=tone,width=1)
            plate.draw.arc((x-25,392,x+25,444),180,360,fill=tone,width=4)
            for dx in (110,126): plate.draw.arc((x-dx,426,x+dx,590),295,65,fill=tone,width=3)
            plate.text((x,365),'clapper strikes bell',size=20,bold=True,fill=tone,anchor='mm')
            detail='metal body flexes\nshape sets resonances'
        plate.text((x,666),detail,size=20,bold=True,fill=tone,anchor='mm')
    footer(plate,'Different vibrating parts disturb the surrounding air; all four produce sound.')


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
    plate.draw.polygon(((790, 550), (755, 625), (825, 625)), fill=GOLD_LIGHT, outline=GOLD)
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
    for start in ((1080, 620), (1440, 620), (1080, 500), (1440, 500)):
        plate.draw.line((*start, *vanishing), fill=INK_SOFT, width=4)
    plate.draw.rectangle((1120, 540, 1195, 620), outline=BLUE, width=5)
    plate.draw.rectangle((1300, 470, 1345, 520), outline=TEAL, width=5)
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
    for x in (340,400):
        plate.dot((x,608),5,fill=INK,outline=INK,width=1)
    plate.draw.arc((338,619,402,655),0,180,fill=INK,width=4)
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
        if index == 0:
            # Open door: the visible gap, leaf and knob distinguish it from a label.
            plate.draw.rectangle((x0+42,433,x0+164,555),fill=BLUE_LIGHT,outline=color,width=4)
            plate.draw.polygon(((x0+42,433),(x0+114,456),(x0+114,574),(x0+42,555)),fill=GOLD_LIGHT,outline=color)
            plate.dot((x0+98,509),4,fill=color,outline=color,width=1)
        elif index == 1:
            plate.draw.ellipse((x0+54,431,x0+151,542),fill=GOLD_LIGHT,outline=color,width=4)
            for dx in (82,125):
                plate.dot((x0+dx,471),4,fill=INK,outline=INK,width=1)
                plate.draw.line((x0+dx-9,456,x0+dx+8,452),fill=INK,width=3)
            plate.draw.ellipse((x0+94,501,x0+113,522),outline=INK,width=3)
            plate.draw.polygon(((x0+70,541),(x0+135,541),(x0+165,569),(x0+42,569)),fill=TEAL_LIGHT,outline=color)
        else:
            plate.draw.rectangle((x0+60,435,x0+146,504),fill=PLUM_LIGHT,outline=color,width=4)
            plate.draw.polygon(((x0+60,504),(x0+146,504),(x0+165,530),(x0+41,530)),fill=PLUM_LIGHT,outline=color)
            for dx,top in ((47,530),(159,530),(64,504),(141,504)):
                plate.draw.line((x0+dx,top,x0+dx,568),fill=color,width=6)
        plate.text((x0+102,590),detail,size=18,bold=True,fill=color,anchor='mm')
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


def _draw_design(plate: Plate) -> None:
    """A visible clearance test changes a carry-handle prototype."""
    pill(plate,(800,225),'NEED -> PROTOTYPE -> TEST -> REVISE',color=BLUE,size=22)
    plate.text((800,282),'Carry-box handle: can the same test gauge pass through?',size=27,bold=True,anchor='mm')
    for i,(gap,tone,label) in enumerate(((22,CORAL,'A: TOO NARROW'),(36,TEAL,'B: CLEARANCE'))):
        cx=430+i*740
        panel(plate,(cx-305,325,cx+305,770),fill=PAPER_LIGHT,outline=tone)
        pill(plate,(cx,365),label,color=tone,size=20)
        plate.draw.rounded_rectangle((cx-190,420,cx+190,662),radius=20,fill=GOLD_LIGHT,outline=GOLD,width=4)
        # Same scale: 4 drawing units per mm; both slots are 70 mm long.
        y=520
        plate.draw.rounded_rectangle((cx-140,y-gap*2,cx+140,y+gap*2),radius=12,fill=PAPER_LIGHT,outline=tone,width=4)
        # A translucent-looking outline gauge remains the same size in both panels.
        plate.draw.ellipse((cx-60,y-60,cx+60,y+60),outline=BLUE,width=6)
        plate.text((cx,y),'30',size=27,bold=True,fill=BLUE,anchor='mm')
        plate.double_arrow((cx+215,y-gap*2),(cx+215,y+gap*2),fill=tone,width=4)
        plate.text((cx+210,624),'{} mm'.format(gap),size=22,bold=True,fill=tone,anchor='mm')
        plate.text((cx,704),'22 < 30: blocked' if i==0 else '36 > 30: fits',size=25,bold=True,fill=tone,anchor='mm')
        plate.text((cx,741),'same 30 mm gauge; same scale',size=20,fill=INK_SOFT,anchor='mm')
    footer(plate,'Widen the opening, then retest grip comfort and strength; one test is not the whole design.')


def _draw_film_meaning(plate: Plate) -> None:
    # Shared neutral face in two sequences.
    def face(cx: float, cy: float) -> None:
        plate.draw.ellipse((cx - 62, cy - 72, cx + 62, cy + 72),
                           fill=GOLD_LIGHT, outline=GOLD, width=5)
        plate.dot((cx - 22, cy - 12), 5, fill=INK, outline=INK)
        plate.dot((cx + 22, cy - 12), 5, fill=INK, outline=INK)
        plate.draw.line((cx - 20, cy + 30, cx + 20, cy + 30), fill=INK, width=4)
    for row, (object_name, reading, color) in enumerate([
        ("BOWL OF SOUP", "may suggest hunger", TEAL),
        ("EMPTY HOSPITAL BED", "may suggest worry or grief", PLUM),
    ]):
        y = 350 + row * 285
        panel(plate, (120, y - 110, 1480, y + 125), fill=PAPER_LIGHT, outline=color)
        face(330, y)
        plate.arrow((420, y), (570, y), fill=color, width=7, head=20)
        panel(plate, (600, y - 78, 910, y + 78), fill=(TEAL_LIGHT if row == 0 else PLUM_LIGHT), outline=color)
        if row == 0:
            plate.draw.pieslice((669,y-60,841,y+48),0,180,fill=PAPER_LIGHT,outline=color,width=4)
            plate.draw.ellipse((669,y-30,841,y+13),fill=GOLD_LIGHT,outline=color,width=4)
            for dx,dy in ((720,-8),(755,-15),(787,-4)):
                plate.dot((dx,y+dy),5,fill=CORAL,outline=CORAL,width=1)
            for dx in (718,755,792):
                plate.draw.arc((dx-8,y-62,dx+8,y-30),80,260,fill=color,width=3)
        else:
            plate.draw.line((668,y-40,668,y+47),fill=color,width=5)
            plate.draw.line((844,y-17,844,y+47),fill=color,width=5)
            plate.draw.rectangle((671,y-18,841,y+17),fill=PAPER_LIGHT,outline=color,width=4)
            plate.draw.rounded_rectangle((678,y-29,716,y-8),radius=8,fill=GOLD_LIGHT,outline=color,width=3)
            plate.draw.rectangle((721,y-17,836,y+12),fill=BLUE_LIGHT,outline=color,width=2)
            for dx in (672,841):
                plate.dot((dx,y+48),7,fill=PAPER_LIGHT,outline=color,width=3)
        plate.text((755,y+64),object_name,size=17,bold=True,fill=color,anchor='mm')
        plate.arrow((930, y), (1050, y), fill=color, width=7, head=20)
        box_text(plate, (1070, y - 68, 1440, y + 68), reading, size=25,
                 minimum=18, bold=True, fill=color)
    pill(plate, (330, 220), "IDENTICAL FACE SHOT", color=GOLD, size=17)
    footer(plate, "Editing makes adjacent shots interact; the audience supplies a connection the camera never recorded.")


def _draw_art_criticism(plate: Plate) -> None:
    pill(plate,(800,225),'OBSERVATION IS NOT YET INTERPRETATION',color=PLUM,size=22)
    panel(plate,(120,300,640,749),fill=PAPER_LIGHT,outline=BLUE)
    plate.draw.rectangle((170,370,590,647),fill=BLUE_LIGHT,outline=INK_SOFT,width=5)
    plate.draw.polygon(((181,571),(579,389),(579,443),(181,625)),fill=CORAL)
    plate.draw.ellipse((245,416,393,564),fill=GOLD_LIGHT,outline=GOLD,width=5)
    plate.text((380,691),'invented composition; no supplied history',size=20,fill=INK_SOFT,anchor='mm')
    rows=(('DESCRIBE','Gold circle overlaps a rising coral diagonal.',BLUE),
          ('INTERPRET','The diagonal may suggest movement or ascent.',TEAL),
          ('COUNTERREAD','The circle and frame may also suggest stability.',CORAL),
          ('RESEARCH','Maker, date and purpose need external evidence.',PLUM))
    for i,(label,detail,tone) in enumerate(rows):
        y=307+i*116
        panel(plate,(700,y,1480,y+101),fill=PAPER_LIGHT,outline=tone)
        plate.text((730,y+27),label,size=20,bold=True,fill=tone,anchor='lm')
        plate.text((730,y+67),detail,size=22,fill=INK,anchor='lm')
    footer(plate,'Test a reading against visible details and context; a colour is not a universal symbol.')


def _draw_creative_practice(plate: Plate) -> None:
    pill(plate,(800,224),'PRACTISE HIERARCHY — KEEP BOTH VERSIONS',color=TEAL,size=22)
    for i,cx in enumerate((360,1240)):
        panel(plate,(cx-230,290,cx+230,737),fill=PAPER_LIGHT,outline=BLUE if i==0 else TEAL)
        plate.text((cx,321),'DRAFT A' if i==0 else 'REVISION B',size=23,bold=True,anchor='mm')
        plate.draw.rectangle((cx-178,363,cx+178,674),fill=BLUE_LIGHT,outline=BLUE,width=3)
        if i==0:
            for j,line in enumerate(('RIVER CLEANUP','SATURDAY 10 AM','MEET AT THE BRIDGE','Bring gloves and a bag')):
                plate.text((cx,417+j*58),line,size=22,fill=INK,anchor='mm')
        else:
            plate.text((cx,418),'RIVER',size=43,bold=True,fill=TEAL,anchor='mm')
            plate.text((cx,470),'CLEANUP',size=43,bold=True,fill=TEAL,anchor='mm')
            plate.draw.line((cx-140,511,cx+140,511),fill=CORAL,width=5)
            plate.text((cx,546),'SATURDAY 10 AM',size=24,bold=True,fill=INK,anchor='mm')
            plate.text((cx,588),'MEET AT THE BRIDGE',size=21,fill=INK,anchor='mm')
            plate.text((cx,640),'Bring gloves and a bag',size=19,fill=INK_SOFT,anchor='mm')
        plate.text((cx,705),'every line competes' if i==0 else 'title, then time and place',size=22,bold=True,anchor='mm')
    pill(plate,(800,367),'CRITIQUE',color=CORAL,size=22)
    box_text(plate,(625,410,975,555),'Intention: invite people.\nThe event name is hard to find.\nTry a stronger title hierarchy.',size=24,bold=True,fill=INK)
    plate.arrow((609,584),(987,584),fill=TEAL,width=6,head=18)
    plate.text((800,623),'same words; changed emphasis',size=20,fill=INK_SOFT,anchor='mm')
    plate.text((800,785),'Next test: can readers find the event and time quickly?',size=25,bold=True,anchor='mm')
    footer(plate,'Practise -> make -> critique -> revise -> curate -> reflect; a revision is still a hypothesis.')


def _generative_marks(seed: int, density: float):
    rng = random.Random(seed)
    return [(col,row,value) for row in range(5) for col in range(5)
            for value in (rng.random(),) if value < density]


def _draw_frontier(plate: Plate) -> None:
    pill(plate,(800,224),'ONE RULE — SEEDS AND INPUT CHANGE THE OUTPUT',color=PLUM,size=21)
    plate.text((800,277),'25 grid sites; seeded value r in [0, 1); draw a disk when r < density',
               size=23,bold=True,anchor='mm')
    for i,(seed,density,label) in enumerate(((7,.35,'OUTPUT A'),(19,.35,'OUTPUT B'),(7,.70,'AUDIENCE INPUT'))):
        cx=300+i*500
        panel(plate,(cx-210,315,cx+210,763),fill=PAPER_LIGHT,outline=(BLUE,TEAL,CORAL)[i])
        pill(plate,(cx,351),label,color=(BLUE,TEAL,CORAL)[i],size=20)
        plate.text((cx,397),'seed {} | density {:.2f}'.format(seed,density),size=21,bold=True,anchor='mm')
        for row in range(5):
            for col in range(5):
                plate.dot((cx-128+col*64,449+row*51),3,fill=GRID,outline=GRID,width=1)
        marks=_generative_marks(seed,density)
        for col,row,value in marks:
            tone=(BLUE,TEAL,CORAL,GOLD,PLUM)[int(value*100)%5]
            radius=10+value*15
            x,y=cx-128+col*64,449+row*51
            plate.draw.ellipse((x-radius,y-radius,x+radius,y+radius),fill=tone,outline=INK_SOFT,width=2)
        plate.text((cx,704),'{} disks'.format(len(marks)),size=23,bold=True,anchor='mm')
        plate.text((cx,742),'same rule' if i<2 else 'same seed as A; more sites pass',size=18,fill=INK_SOFT,anchor='mm')
    footer(plate,'Authorship includes rule, input and selection; save seeds and disclose the process.')


def _draw_aesthetics(plate: Plate) -> None:
    draw_network(plate, ('', ''), [
        ('FORM', 'How do the circle, diagonal and warm/cool contrast direct attention?'),
        ('CONTEXT', 'What maker, purpose and history would we need to research?'),
        ('EXPERIENCE', 'Does this arrangement feel balanced or tense to you? Why?'),
        ('INSTITUTION', 'Would a gallery wall or a product label change your reading?'),
    ], 'Give reasons for a judgment; do not invent a history from the image alone.',
        edge_word='SAME COMPOSITION — DIFFERENT QUESTIONS')
    plate.draw.rectangle((646,405,954,607),fill=PAPER_LIGHT,outline=INK_SOFT,width=4)
    plate.draw.rectangle((658,417,942,595),fill=BLUE_LIGHT)
    plate.draw.polygon(((658,548),(942,435),(942,475),(658,588)),fill=CORAL)
    plate.draw.ellipse((698,437,812,551),fill=GOLD_LIGHT,outline=GOLD,width=4)
    plate.text((800,626),'invented composition',size=18,fill=INK_SOFT,anchor='mm')


# Original four-beat example: MIDI pitches make every vertical interval testable.
COMPOSITION_VOICES = ((60, 62, 64, 62), (57, 59, 60, 59))


def _draw_counterpoint(plate: Plate) -> None:
    panel(plate, (120, 235, 1480, 780), fill=PAPER_LIGHT, outline=PLUM)
    pill(plate, (800, 270), "PITCH + DURATION + SIMULTANEOUS INTERVAL", color=PLUM, size=18)
    names = {57: "A3", 59: "B3", 60: "C4", 62: "D4", 64: "E4"}
    pitch_y = lambda pitch: 560 - (pitch - 57) * 30
    for pitch in range(57, 65):
        y = pitch_y(pitch)
        plate.draw.line((255, y, 1385, y), fill=GRID, width=2)
        if pitch in names:
            plate.text((205, y), names[pitch], size=23, anchor="mm", fill=INK_SOFT)
    for beat, (upper, lower) in enumerate(zip(*COMPOSITION_VOICES)):
        x = 280 + beat * 280
        plate.text((x + 100, 300), "beat " + str(beat + 1), size=20, anchor="mm")
        # Equal-length horizontal bars are held notes, not sliding pitch contours.
        for pitch, color in ((upper, BLUE), (lower, CORAL)):
            y = pitch_y(pitch)
            plate.draw.rounded_rectangle((x, y - 7, x + 200, y + 7), radius=7, fill=color)
            plate.text((x + 100, y - 22), names[pitch], size=20, anchor="mm", bold=True, fill=color)
        interval = upper - lower
        plate.text((x + 100, 602), ("minor" if interval == 3 else "major") + " 3rd",
                   size=23, anchor="mm", bold=True, fill=PLUM)
        plate.text((x + 100, 631), str(interval) + " semitones", size=19, anchor="mm", fill=INK_SOFT)
    plate.text((800, 669), "Separate form example: opening → contrast → varied return",
               size=21, anchor="mm", fill=INK_SOFT)
    for index, (label, color) in enumerate((("A", BLUE), ("B", TEAL), ("A′", PLUM))):
        x0 = 310 + index * 330
        panel(plate, (x0, 695, x0 + 280, 754), fill=(BLUE_LIGHT, TEAL_LIGHT, PLUM_LIGHT)[index],
              outline=color, radius=10)
        box_text(plate, (x0 + 8, 702, x0 + 272, 748), label, size=29, bold=True, fill=color)
    footer(plate, "Each bar lasts one beat. C4 is middle C; grid steps are semitones, not loudness.")


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
        "Three panels show a wide cup with an oval rim and open handle, a first outline that is too narrow beside dashed width guides, and a revised wider outline with the same height.",
        "Observation drawing is a repeated comparison between subject and mark. Imaginative drawing enters the same loop through memory, play and deliberate choices.",
        _draw_observation,
    ),
    spec(
        "arts.0.singing", "Songs and Sounds", 0, DOMAIN,
        "beat-pitch-phrase-plate",
        "A worked four-beat phrase aligns four numbered pulse dots with the syllables HEL-, LO, MY and FRIEND while colored notes and a connecting line rise and fall above the steady beat.",
        "A song combines a steady pulse, changing rhythm and a pitch contour. Singers listen and breathe together so separate voices can coordinate.",
        _draw_singing,
    ),
    spec(
        "arts.0.dance", "Moving to Music", 0, DOMAIN, "four-count-movement-plate",
        "Four numbered panels show solid figures bending low, stepping sideways, reaching upward and changing direction, with arrows distinguishing level, travel, reach and turn on successive counts.",
        "Counting connects musical time to movement. A dancer can change shape, level, direction and energy while keeping the same four-beat phrase.",
        _draw_dance,
    ),
    spec(
        "arts.1.crafts", "Making Things", 1, DOMAIN, "craft-processes-materials-plate",
        "Three before-and-after drawings show loose clay coils joined into a hollow pot, a rectangular soap block rounded by removing chips, and a paper square, triangle and door arranged into a house before gluing.",
        "Making methods change material in different ways. Planning joins, cuts and order helps a maker choose what can still be revised.",
        _draw_craft_processes,
    ),
    spec(
        "arts.1.instruments", "Musical Instruments", 1, DOMAIN, "instrument-vibration-families-plate",
        "Four columns trace how a plucked string, blown air column, struck membrane and struck solid body begin vibrating, how the instrument reinforces that vibration and the resulting sound.",
        "Instrument families can be compared by what first vibrates. Resonators and player technique then shape loudness, pitch and tone color.",
        _draw_instruments,
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
        "A selected timeline connects early rock art and ancient public objects with East Asian woodblock printing from the 600s onward, photography from the 1800s onward, and modern to digital practices. Older media continue; these are overlapping examples, not a universal sequence of progress.",
        "Art history follows changing materials, patrons, audiences and purposes. New media add possibilities without making earlier practices obsolete or less complex.",
        [
            ("before 30,000 BCE", "Rock + cave art", "mineral pigments, engraving and place-based meaning"),
            ("ancient worlds", "Public objects", "architecture, sculpture and images tied to ritual and power"),
            ("600s onward", "East Asian printing", "woodblocks reproduce texts and images; manuscripts continue"),
            ("1800s onward", "Photography", "light-sensitive surfaces add new ways to record images"),
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
    spec(
        "arts.2.theatre", "Drama and Theatre", 2, DOMAIN, "script-to-live-event-plate",
        "Two overhead stage plans keep the same line of dialogue. Initially actor B stands between one audience seat and actor A; moving B sideways clears that seat's sightline to A. Other seats and performance choices still need rehearsal.",
        "Theatre is a live collaboration. Text, bodies, space, light, sound and audience attention combine differently in every production and performance.",
        _draw_theatre,
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
        "These invented schematic studies isolate perspective, broken brushwork and faceting; they are not reproductions or comprehensive portraits of Renaissance, Impressionist or Cubist art. Compare the shared subject, then study actual works: each movement contains varied practices, not a single recipe or a ladder of improvement.",
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
        "Two carry-box handle openings are drawn at the same scale: a 30 mm circular test gauge cannot fit through a 22 mm opening but fits through a revised 36 mm opening.",
        "This invented clearance test shows how evidence can change a prototype. The gauge is not a human-hand standard: real testing must also examine grip comfort, load, strength and the trade-off from removing more material.",
        _draw_design,
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
        _draw_aesthetics,
    ),
    spec(
        "arts.4.art-theory", "Art Criticism & Theory", 4, DOMAIN,
        "critical-reading-evidence-chain-plate",
        "An invented gold circle overlaps a coral diagonal on blue. Four annotations distinguish a visible overlap, a possible movement reading, a stability counter-reading and contextual facts that still require research.",
        "Critical interpretation separates what is visible from what is inferred, then uses context and counterevidence. Symbols do not carry one universal meaning across cultures.",
        _draw_art_criticism,
    ),
    spec(
        "arts.4.composition", "Composition & Analysis", 4, DOMAIN,
        "counterpoint-form-analysis-plate",
        "Four one-beat blue notes C4, D4, E4, D4 sound above coral notes A3, B3, C4, B3. Their intervals are minor third, minor third, major third and minor third; a separate A, B, A-prime diagram shows return with variation.",
        "Read each voice through time and both voices at each beat. This original parallel-thirds example uses a semitone pitch grid and equal one-beat durations, not a claim to satisfy every rule of strict counterpoint. The separate form diagram describes larger sections, not these four notes.",
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
        "Two versions of an invented river-cleanup poster preserve the wording while changing title size, spacing and emphasis. A critique identifies weak hierarchy, and the revised version remains subject to a reader test.",
        "This fictional critique illustrates a specific practice decision, not measured evidence of improved readership. Keep versions, test whether readers find the event and time, then revise again. The poster is an example, not an announcement of a real event.",
        _draw_creative_practice,
    ),
    spec(
        "arts.5.frontier", "Art at the Frontier", 5, DOMAIN,
        "generative-system-authorship-plate",
        "Three reproducible 5-by-5 disk fields apply one threshold rule: seeds 7 and 19 at density 0.35 yield 12 and 13 disks; seed 7 at density 0.70 retains the first field and adds nine disks.",
        "At each grid site, a seeded value r is compared with density; passing sites receive a disk whose size and colour also depend on r. Changing the seed changes the arrangement; increasing density with the same seed preserves existing disks. These are static snapshots of a possible audience-controlled parameter, not a live sensor.",
        _draw_frontier,
    ),
]


SPECS: Dict[str, Spec] = {item["id"]: item for item in _ITEMS}
