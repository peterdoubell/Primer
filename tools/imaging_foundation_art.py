"""Explanatory geometry for the ten nonclinical imaging foundations.

The caller owns the 1600-by-1000 Plate, heading and takeaway. These drawings
stay within its content band (110, 265)-(1490, 775). They are diagrams of toys,
ideal signals and invented measurements, never synthetic diagnostic images.
"""
from __future__ import annotations

import math

from math_illustrations.core import (
    BLUE, BLUE_LIGHT, CORAL, CORAL_LIGHT, GOLD, GOLD_LIGHT, GREEN,
    GRID, INK, INK_SOFT, PAPER_LIGHT, PLUM, TEAL, TEAL_LIGHT, font,
)


def _text(p, xy, value, size=28, color=INK, bold=False, anchor="mm"):
    p.text(xy, value, size=size, fill=color, bold=bold, anchor=anchor)


def _fit(p, box, value, size=27, color=INK, bold=False):
    """Measured wrapping with a fixed lower bound; fail rather than crop."""
    left, top, right, bottom = box
    for candidate in range(size, 19, -1):
        face = font(candidate, bold=bold)
        lines, line = [], ""
        for word in value.split():
            trial = (line + " " + word).strip()
            if p.draw.textlength(trial, font=face) > right - left and line:
                lines.append(line)
                line = word
            else:
                line = trial
        if line:
            lines.append(line)
        height = len(lines) * (candidate + 7)
        if height <= bottom - top and all(p.draw.textlength(line, font=face) <= right - left for line in lines):
            y = top + (bottom - top - height) / 2
            for line in lines:
                p.draw.text((left, y), line, font=face, fill=color)
                y += candidate + 7
            return
    raise ValueError("Imaging label exceeds its box: " + value)


def _dashed(p, start, end, color=INK_SOFT, width=3, dash=12):
    dx, dy = end[0] - start[0], end[1] - start[1]
    length = math.hypot(dx, dy)
    if not length:
        return
    for distance in range(0, math.ceil(length), dash * 2):
        stop = min(distance + dash, length)
        a = (start[0] + dx * distance / length, start[1] + dy * distance / length)
        b = (start[0] + dx * stop / length, start[1] + dy * stop / length)
        p.draw.line((a, b), fill=color, width=width)


def _wave(p, x0, x1, y, amplitude=17, cycles=5, color=TEAL, width=5):
    points = [(x0 + (x1 - x0) * i / 140,
               y + amplitude * math.sin(2 * math.pi * cycles * i / 140)) for i in range(141)]
    p.draw.line(points, fill=color, width=width)


def _shadows(p):
    source = (245, 470)
    # The shadow boundaries pass through the blocker edges: similar triangles.
    screen_x, blocker_x, half = 1340, 680, 47
    screen_half = half * (screen_x - source[0]) / (blocker_x - source[0])
    p.draw.polygon([source, (screen_x, 300), (screen_x, 650)], fill=GOLD_LIGHT)
    p.draw.polygon([(blocker_x, 470 - half), (screen_x, 470 - screen_half),
                    (screen_x, 470 + screen_half), (blocker_x, 470 + half)], fill="#d3cdbb")
    p.draw.line((screen_x, 300, screen_x, 655), fill=GRID, width=16)
    p.draw.line((screen_x, 470 - screen_half, screen_x, 470 + screen_half), fill=INK, width=19)
    for y in (470 - half, 470 + half):
        p.arrow(source, (blocker_x - 5, y), fill=GOLD, width=4, head=16)
    p.draw.rounded_rectangle((blocker_x - 13, 470 - half, blocker_x + 13, 470 + half),
                             radius=5, fill=BLUE, outline=INK, width=3)
    p.draw.rounded_rectangle((150, 438, 235, 502), radius=12, fill=TEAL, outline=INK, width=3)
    p.draw.ellipse((220, 440, 262, 500), fill=GOLD, outline=INK, width=3)
    _text(p, (220, 330), "LAMP", color=TEAL, bold=True)
    _text(p, (680, 330), "CARDBOARD", color=BLUE, bold=True)
    _text(p, (1310, 285), "WALL", size=24, bold=True)
    _fit(p, (370, 540, 610, 625), "Light reaches the card", color=GOLD)
    _fit(p, (885, 515, 1230, 600), "Less light reaches this patch", color=INK_SOFT)
    _text(p, (800, 720), "The shadow shows an outline, but not the card color.", size=29)


def _box(p, x, y, opened=False):
    width, height = 300, 155
    p.draw.polygon([(x, y), (x + 62, y - 50), (x + width + 62, y - 50),
                    (x + width, y)], fill=TEAL_LIGHT, outline=INK, width=3)
    if opened:
        # Visible contents belong only to the opened view.
        p.draw.polygon([(x + 22, y - 2), (x + 68, y - 38),
                        (x + width + 38, y - 38), (x + width - 12, y - 2)], fill="#b4a98d")
        p.draw.rounded_rectangle((x + 80, y - 32, x + 220, y + 50), radius=23, fill=CORAL, outline=INK, width=3)
        p.draw.line((x + 95, y - 15, x + 206, y + 25), fill=CORAL_LIGHT, width=10)
        p.draw.polygon([(x + 62, y - 50), (x + 104, y - 150),
                        (x + width + 104, y - 150), (x + width + 62, y - 50)],
                       fill=BLUE_LIGHT, outline=INK, width=4)
    p.draw.polygon([(x + width, y), (x + width + 62, y - 50),
                    (x + width + 62, y + height - 50), (x + width, y + height)],
                   fill=TEAL, outline=INK, width=3)
    p.draw.rectangle((x, y, x + width, y + height), fill=BLUE_LIGHT, outline=INK, width=4)
    if not opened:
        p.draw.line((x, y, x + width, y), fill=INK, width=8)
        _text(p, (x + 150, y + 75), "?", size=70, color=BLUE, bold=True)


def _inside(p):
    p.card((120, 285, 735, 750), fill=PAPER_LIGHT)
    p.card((785, 285, 1480, 750), fill=PAPER_LIGHT)
    _text(p, (425, 325), "CLOSED", color=BLUE, bold=True)
    _text(p, (1125, 325), "OPENED VIEW", color=TEAL, bold=True)
    _box(p, 230, 480)
    _box(p, 920, 505, opened=True)
    _fit(p, (170, 666, 690, 737), "We see the box. The contents are hidden.")
    _fit(p, (835, 684, 1425, 745), "Now the scarf is visible. Update the guess.")


def _viewpoints(p):
    p.card((130, 290, 720, 750), fill=PAPER_LIGHT)
    p.card((775, 290, 1470, 750), fill=PAPER_LIGHT)
    _text(p, (425, 335), "FRONT VIEW", color=BLUE, bold=True)
    _text(p, (1120, 335), "SIDE VIEW", color=TEAL, bold=True)
    p.draw.rectangle((330, 410, 525, 605), fill=BLUE_LIGHT, outline=BLUE, width=6)
    _text(p, (425, 505), "A", size=58, color=BLUE, bold=True)
    for x, color, fill, label in ((865, BLUE, BLUE_LIGHT, "A"), (1160, CORAL, CORAL_LIGHT, "B")):
        p.draw.rectangle((x, 410, x + 195, 605), fill=fill, outline=color, width=6)
        _text(p, (x + 98, 505), label, size=58, color=color, bold=True)
    p.draw.line((300, 610, 555, 610), fill=GRID, width=4)
    p.draw.line((830, 610, 1390, 610), fill=GRID, width=4)
    _fit(p, (175, 650, 675, 733), "A hides B from the front. One outline does not prove one block.")
    _fit(p, (820, 650, 1415, 733), "From the side, both blocks are visible. The blocks have not moved.")


def _layer(p, center, rx, label, color):
    x, y = center
    ry, thick = 26, 26
    p.draw.rectangle((x - rx, y, x + rx, y + thick), fill=color, outline=color)
    p.draw.ellipse((x - rx, y + thick - ry, x + rx, y + thick + ry), fill=color, outline=INK, width=3)
    p.draw.ellipse((x - rx, y - ry, x + rx, y + ry), fill=PAPER_LIGHT, outline=INK, width=3)
    p.draw.line((x + rx, y, x + rx, y + thick), fill=INK, width=3)
    p.draw.line((x - rx, y, x - rx, y + thick), fill=INK, width=3)
    _text(p, (x, y - 1), str(label), size=24, bold=True, color=color)
    p.arrow((x + rx * .25, y + 6), (x + rx * .7, y + 6), fill=color, width=2, head=7)


def _slices(p):
    _text(p, (405, 300), "SEPARATE LAYERS", color=BLUE, bold=True)
    _text(p, (1160, 300), "KEEP THE ORDER", color=TEAL, bold=True)
    for index, (y, rx, color) in enumerate(((390, 100, BLUE), (515, 200, TEAL), (640, 100, CORAL)), 1):
        _layer(p, (405, y), rx, index, color)
    p.arrow((670, 510), (825, 510), width=6, head=20)
    # Draw bottom-to-top so each disk occludes the one beneath correctly.
    for y, rx, label, color in ((580, 100, 3, CORAL), (526, 200, 2, TEAL), (472, 100, 1, BLUE)):
        _layer(p, (1150, y), rx, label, color)
    _fit(p, (875, 645, 1440, 750), "Small, large, small: the middle is widest. Numbers keep the shape in order.")
    _text(p, (405, 737), "Match the direction marks too.", size=24)


def _pixels(p):
    _text(p, (410, 300), "CALIBRATED GRID", color=BLUE, bold=True)
    _text(p, (1190, 300), "ENLARGED CELLS", color=TEAL, bold=True)
    x0, y0, side = 155, 350, 70
    pattern = {(2, 1), (3, 1), (3, 2), (4, 2), (3, 3)}
    for row in range(4):
        for col in range(7):
            x, y = x0 + col * side, y0 + row * side
            p.draw.rectangle((x, y, x + side, y + side), fill=BLUE if (col, row) in pattern else PAPER_LIGHT,
                             outline=GRID, width=2)
    start, end = (190, 455), (610, 455)
    p.dot(start, 9, fill=CORAL, outline=PAPER_LIGHT, width=2)
    p.dot(end, 9, fill=CORAL, outline=PAPER_LIGHT, width=2)
    p.draw.rectangle((x0 + 2 * side, y0 + side, x0 + 5 * side, y0 + 4 * side), outline=TEAL, width=5)
    p.double_arrow((start[0], 665), (end[0], 665), width=4, fill=CORAL)
    for col in range(7):
        x = start[0] + side * col
        p.draw.line((x, 652, x, 677), fill=CORAL, width=3)
    _text(p, (410, 711), "6 intervals × 2 mm = 12 mm", size=28, color=CORAL, bold=True)
    for row in range(3):
        for col in range(3):
            x, y = 1020 + col * 95, 350 + row * 95
            p.draw.rectangle((x, y, x + 95, y + 95), fill=BLUE if (col + 2, row + 1) in pattern else PAPER_LIGHT,
                             outline=TEAL, width=3)
    p.arrow((715, 490), (955, 490), width=5, head=20, fill=TEAL)
    _text(p, (834, 447), "DISPLAY ZOOM", size=21, color=TEAL, bold=True)
    _fit(p, (965, 663, 1435, 754), "Same recorded cells. No new object detail was measured.")


def _echoes(p):
    p.draw.rounded_rectangle((175, 375, 260, 605), radius=20, fill=BLUE_LIGHT, outline=BLUE, width=5)
    p.draw.line((1290, 345, 1290, 650), fill=CORAL, width=14)
    _text(p, (320, 302), "SOURCE / RECEIVER", size=25, color=BLUE, bold=True)
    _text(p, (1280, 302), "BOUNDARY", size=25, color=CORAL, bold=True)
    _wave(p, 300, 1200, 423, amplitude=18, cycles=5, color=GOLD)
    p.arrow((1200, 423), (1265, 423), fill=GOLD, width=5, head=20)
    _wave(p, 320, 1250, 558, amplitude=13, cycles=5, color=TEAL)
    p.arrow((320, 558), (280, 558), fill=TEAL, width=5, head=20)
    _text(p, (770, 360), "OUTWARD PATH = d", color=GOLD, bold=True)
    _text(p, (770, 620), "RETURN PATH = d", color=TEAL, bold=True)
    _text(p, (800, 710), "Total path = 2d       depth = speed × return time ÷ 2", size=32, bold=True)
    _text(p, (800, 758), "Ideal direct path, stationary boundary and known constant speed", size=22, color=INK_SOFT)


def _attenuation_row(p, top, title, factors, middle):
    p.card((120, top, 1480, top + 210), fill=PAPER_LIGHT)
    _text(p, (160, top + 27), title, size=23, bold=True, anchor="lm")
    y = top + 126
    segments = ((235, 535, 80, GOLD), (585, 965, middle, TEAL), (1015, 1390, 10, CORAL))
    for left, right, value, color in segments:
        p.draw.rectangle((left, y - value / 2, right, y + value / 2), fill=color)
        _text(p, ((left + right) / 2, top + 72), str(value) + " units", size=27, color=color, bold=True)
    for x, factor in ((560, factors[0]), (990, factors[1])):
        p.draw.rectangle((x - 13, y - 56, x + 13, y + 56), fill=BLUE_LIGHT, outline=BLUE, width=3)
        _text(p, (x, top + 35), "× " + factor, size=27, color=BLUE, bold=True)
    p.draw.line((1410, y - 53, 1410, y + 53), fill=INK, width=7)


def _attenuation(p):
    _attenuation_row(p, 280, "ORDER A", ("1/2", "1/4"), 40)
    _attenuation_row(p, 530, "ORDER B", ("1/4", "1/2"), 20)
    _text(p, (800, 760), "Beam thickness depicts signal amount; both paths finish with 10 units.", size=24)


def _signals(p):
    for x in (110, 580, 1050):
        p.card((x, 280, x + 440, 765), fill=PAPER_LIGHT)
    _text(p, (330, 320), "TRANSMISSION", size=26, color=GOLD, bold=True)
    _text(p, (800, 320), "ECHO", size=26, color=TEAL, bold=True)
    _text(p, (1270, 320), "RESONANCE", size=26, color=PLUM, bold=True)
    p.dot((175, 475), 20, fill=GOLD)
    p.draw.rectangle((290, 400, 355, 550), fill=BLUE_LIGHT, outline=BLUE, width=4)
    for y in (430, 475, 520):
        p.arrow((200, y), (282, y), fill=GOLD, width=5, head=13)
        p.arrow((365, y), (483, y), fill=GOLD, width=3, head=13)
    p.draw.line((493, 400, 493, 550), fill=INK, width=7)
    p.draw.rounded_rectangle((630, 422, 672, 567), radius=10, fill=TEAL_LIGHT, outline=TEAL, width=3)
    p.draw.line((954, 407, 954, 587), fill=CORAL, width=9)
    _wave(p, 688, 909, 455, amplitude=14, cycles=3, color=GOLD)
    p.arrow((909, 455), (938, 455), fill=GOLD, width=4, head=12)
    _wave(p, 700, 930, 535, amplitude=10, cycles=3, color=TEAL)
    p.arrow((700, 535), (680, 535), fill=TEAL, width=4, head=12)
    p.draw.ellipse((1155, 392, 1385, 610), fill=BLUE_LIGHT, outline=PLUM, width=5)
    p.draw.ellipse((1202, 420, 1340, 580), fill=PAPER_LIGHT, outline=PLUM, width=4)
    p.draw.line((1240, 453, 1305, 540), fill=PLUM, width=5)
    p.arrow((1240, 453), (1260, 480), fill=PLUM, width=5, head=14)
    _wave(p, 1080, 1195, 489, amplitude=11, cycles=3, color=GOLD)
    _wave(p, 1345, 1460, 516, amplitude=11, cycles=3, color=TEAL)
    for x, text in ((140, "X-ray signal passing through an object; many angles support CT reconstruction."),
                    (610, "Return time and strength of high-frequency sound."),
                    (1080, "Magnetic fields, radiofrequency excitation and spatial encoding.")):
        _fit(p, (x, 638, x + 375, 748), text, size=26)
    _text(p, (1270, 365), "Schematic apparatus", size=21, color=INK_SOFT)


def _inverse(p):
    _text(p, (445, 295), "TWO UNKNOWN CELLS", color=BLUE, bold=True)
    for x, name, color, fill in ((270, "a", BLUE, BLUE_LIGHT), (485, "b", CORAL, CORAL_LIGHT)):
        p.draw.rectangle((x, 345, x + 145, 470), fill=fill, outline=color, width=4)
        _text(p, (x + 73, 407), name, size=58, bold=True, color=color)
    _text(p, (450, 527), "a + b = 10", size=36, color=BLUE, bold=True)
    _text(p, (450, 590), "2a + b = 14", size=36, color=CORAL, bold=True)
    _fit(p, (170, 646, 740, 759), "One sum allows many pairs. An independent second sum fixes a = 4, b = 6.", size=29)
    x0, x1, y0, y1 = 925, 1380, 345, 690
    point = lambda a, b: (x0 + a * (x1 - x0) / 10, y1 - b * (y1 - y0) / 10)
    for value in range(0, 11, 2):
        x, y = point(value, value)
        p.draw.line((x, y0, x, y1), fill=GRID, width=1)
        p.draw.line((x0, y, x1, y), fill=GRID, width=1)
        _text(p, (x, y1 + 24), str(value), size=20)
        _text(p, (x0 - 27, y), str(value), size=20)
    p.arrow((x0, y1), (x1 + 35, y1), width=3, head=12, fill=INK)
    p.arrow((x0, y1), (x0, y0 - 25), width=3, head=12, fill=INK)
    _text(p, (1440, y1), "a", size=28, bold=True)
    _text(p, (x0, y0 - 52), "b", size=28, bold=True)
    p.draw.line((point(0, 10), point(10, 0)), fill=BLUE, width=5)
    p.draw.line((point(2, 10), point(7, 0)), fill=CORAL, width=5)
    p.dot(point(4, 6), 11, fill=GREEN, outline=PAPER_LIGHT, width=3)
    _text(p, (1165, 425), "(4, 6)", size=28, bold=True, color=GREEN)
    _text(p, (1155, 761), "The two constraints meet at one pair.", size=23)


def _validation(p):
    x = lambda value: 480 + (value - 7) * 155
    reference = x(10)
    _text(p, (reference, 290), "REFERENCE: 10 mm", size=27, color=GREEN, bold=True)
    _dashed(p, (reference, 325), (reference, 676), color=GREEN, width=4)
    for y, name, values, color in ((420, "METHOD A", (11.9, 12.0, 12.1), CORAL),
                                   (585, "METHOD B", (9.0, 10.0, 11.0), BLUE)):
        _text(p, (150, y - 12), name, size=28, color=color, bold=True, anchor="lm")
        p.draw.line((x(7), y, x(13), y), fill=GRID, width=3)
        for value in range(7, 14):
            p.draw.line((x(value), y - 7, x(value), y + 7), fill=GRID, width=2)
        for value in values:
            p.dot((x(value), y), 7, fill=color, outline=PAPER_LIGHT, width=2)
        mean = sum(values) / len(values)
        p.draw.polygon([(x(mean), y + 29), (x(mean) - 8, y + 43), (x(mean) + 8, y + 43)], fill=color)
        _text(p, (x(mean), y + 70), "mean " + str(round(mean)) + " mm", size=23, color=color, bold=True)
    for value in range(7, 14):
        _text(p, (x(value), 684), str(value), size=22)
    _text(p, (1460, 684), "mm", size=22)
    _fit(p, (145, 450, 430, 515), "Tight repeats, +2 mm bias", size=25, color=CORAL)
    _fit(p, (145, 615, 430, 680), "More spread, zero mean error here", size=25, color=BLUE)
    _text(p, (800, 746), "Dots = repeated measurements       Triangles = their means", size=26)


_DRAWERS = {
    "img.0.shadows": _shadows,
    "img.0.inside-outside": _inside,
    "img.1.viewpoints": _viewpoints,
    "img.1.slices": _slices,
    "img.2.pixels": _pixels,
    "img.2.echoes": _echoes,
    "img.3.attenuation": _attenuation,
    "img.3.signals": _signals,
    "img.4.inverse-problems": _inverse,
    "img.4.validation": _validation,
}


def draw(plate, node, spec):
    """Draw a supported imaging lesson in-place; return False for other nodes."""
    renderer = _DRAWERS.get(node["id"])
    if renderer is None:
        return False
    renderer(plate)
    return True
