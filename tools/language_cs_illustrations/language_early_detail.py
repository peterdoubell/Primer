"""Bespoke explanatory renderers for early language and literature plates.

The generic language layouts are useful as a fallback, but the Seedling,
Sprout, and Sapling lessons are clearer when the learner can see the object of
study itself: graphemes aligned to phonemes, pen strokes on ruled paper,
constituents inside a clause, evidence inside a paragraph, and sources
converging on a qualified answer.  These deterministic compositions share the
Primer field-guide palette while giving every lesson a distinct visual
argument that remains legible in the 800 px responsive asset.

Renderers accept an already initialised :class:`~math_illustrations.core.Plate`
and draw only inside its content frame.  The registry deliberately contains
only generator-owned language lessons from stages 0--2; the authored Alphabet
and Reading plates remain untouched.
"""

from __future__ import annotations

import math
import os
from typing import Callable, Dict, Sequence, Tuple

from PIL import ImageFont

from math_illustrations.core import (
    BLUE,
    BLUE_LIGHT,
    CORAL,
    CORAL_LIGHT,
    EDGE,
    GOLD,
    GOLD_LIGHT,
    GREEN,
    GREEN_LIGHT,
    GRID,
    INK,
    INK_SOFT,
    PAPER,
    PAPER_LIGHT,
    PLUM,
    PLUM_LIGHT,
    TEAL,
    TEAL_LIGHT,
    Plate,
    font,
    hex_rgba,
    mix,
)


Point = Tuple[float, float]
Box = Tuple[float, float, float, float]
Renderer = Callable[[Plate], None]

_IPA_FONT_CANDIDATES = (
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
)


def _ipa_font(size: int) -> ImageFont.FreeTypeFont:
    """Return a sans face with IPA coverage on macOS and Linux builders."""

    for path in _IPA_FONT_CANDIDATES:
        if os.path.isfile(path):
            return ImageFont.truetype(path, size=size)
    # The shared face remains a usable fallback for plain-language labels.
    return font(size)


def _tint(tone: str, amount: float = .78) -> str:
    return mix(tone, PAPER_LIGHT, amount)


def _panel(plate: Plate, box: Box, tone: str, *, radius: int = 24,
           alpha: int = 218) -> None:
    plate.draw.rounded_rectangle(
        box,
        radius=radius,
        fill=hex_rgba(_tint(tone, .88), alpha),
        outline=hex_rgba(tone, 205),
        width=4,
    )


def _tag(plate: Plate, center: Point, value: str, tone: str, *, size: int = 25) -> None:
    plate.label(center, value, size=max(size, 24), fill=tone)


def _center_lines(plate: Plate, center: Point, lines: Sequence[str], *,
                  size: int = 28, gap: int = 9, bold: bool = False,
                  fill: str = INK) -> None:
    line_height = size + gap
    y = center[1] - (len(lines) - 1) * line_height / 2
    for line in lines:
        plate.text((center[0], y), line, size=size, bold=bold,
                   fill=fill, anchor="mm")
        y += line_height


def _footer(plate: Plate, value: str, *, tone: str | None = None,
            size: int = 28) -> None:
    tone = tone or plate.accent
    plate.draw.rounded_rectangle(
        (170, 816, 1430, 881),
        radius=25,
        fill=hex_rgba(_tint(tone, .78), 214),
        outline=hex_rgba(tone, 175),
        width=3,
    )
    plate.text((800, 849), value, size=size, bold=True, fill=tone, anchor="mm")


def _arrow(plate: Plate, start: Point, end: Point, tone: str, label: str = "",
           *, label_dy: float = -24, width: int = 7) -> None:
    plate.arrow(start, end, fill=tone, width=width, head=20)
    if label:
        _tag(plate, ((start[0] + end[0]) / 2,
                     (start[1] + end[1]) / 2 + label_dy), label, tone, size=22)


def _word_tile(plate: Plate, box: Box, value: str, tone: str, *,
               sublabel: str = "", strong: bool = True) -> None:
    _panel(plate, box, tone, radius=20)
    x0, y0, x1, y1 = box
    plate.text(((x0 + x1) / 2, (y0 + y1) / 2 - (16 if sublabel else 0)), value,
               size=48 if len(value) <= 2 else 38, bold=strong,
               fill=tone, anchor="mm")
    if sublabel:
        plate.text(((x0 + x1) / 2, y1 - 25), sublabel, size=23,
                   bold=True, fill=INK_SOFT, anchor="mm")


def _rule(plate: Plate, y: float, x0: float, x1: float, *,
          tone: str = BLUE, dashed: bool = False, width: int = 3) -> None:
    if dashed:
        plate.dashed_line((x0, y), (x1, y), fill=hex_rgba(tone, 155),
                          width=width, dash=15, gap=12)
    else:
        plate.draw.line((x0, y, x1, y), fill=hex_rgba(tone, 165), width=width)


def _speech_bubble(plate: Plate, box: Box, text: str, tone: str,
                   *, tail: str = "left") -> None:
    x0, y0, x1, y1 = box
    plate.draw.rounded_rectangle(box, radius=28, fill=hex_rgba(_tint(tone, .9), 235),
                                 outline=tone, width=4)
    if tail == "left":
        points = ((x0 + 70, y1 - 7), (x0 + 38, y1 + 48), (x0 + 126, y1 - 7))
    else:
        points = ((x1 - 126, y1 - 7), (x1 - 38, y1 + 48), (x1 - 70, y1 - 7))
    plate.draw.polygon(points, fill=_tint(tone, .9), outline=tone)
    plate.wrapped_text((int(x0 + 27), int(y0 + 18), int(x1 - 27), int(y1 - 18)),
                       text, size=28, bold=True, fill=INK, line_gap=7)


def _bust(plate: Plate, center: Point, tone: str, *, facing: int = 1) -> None:
    """Draw a compact filled speaker/listener silhouette, not a stick figure."""

    x, y = center
    plate.draw.ellipse((x - 43, y - 115, x + 43, y - 29),
                       fill=_tint(tone, .48), outline=tone, width=4)
    plate.draw.pieslice((x - 99, y - 45, x + 99, y + 125), 180, 360,
                        fill=_tint(tone, .6), outline=tone, width=4)
    eye_x = x + facing * 16
    plate.dot((eye_x, y - 78), 4, fill=INK, outline=INK, width=1)
    plate.draw.arc((x + facing * 14 - 14, y - 69,
                    x + facing * 14 + 19, y - 43),
                   20 if facing > 0 else 160,
                   125 if facing > 0 else 265, fill=INK_SOFT, width=3)


def _open_book(plate: Plate, box: Box, tone: str) -> Tuple[Box, Box]:
    x0, y0, x1, y1 = box
    mid = (x0 + x1) / 2
    plate.draw.polygon(((x0, y0 + 18), (mid - 10, y0), (mid - 10, y1),
                        (x0 + 18, y1 - 21)),
                       fill=hex_rgba(PAPER_LIGHT, 245), outline=tone)
    plate.draw.polygon(((mid + 10, y0), (x1, y0 + 18), (x1 - 18, y1 - 21),
                        (mid + 10, y1)),
                       fill=hex_rgba(PAPER_LIGHT, 245), outline=tone)
    plate.draw.line((mid, y0 + 8, mid, y1 - 4), fill=EDGE, width=5)
    return ((x0 + 34, y0 + 34, mid - 35, y1 - 32),
            (mid + 35, y0 + 34, x1 - 34, y1 - 32))


def _document(plate: Plate, box: Box, tone: str, *, fold: bool = True) -> None:
    x0, y0, x1, y1 = box
    plate.draw.rounded_rectangle(box, radius=14, fill=hex_rgba(PAPER_LIGHT, 245),
                                 outline=tone, width=4)
    if fold:
        plate.draw.polygon(((x1 - 55, y0), (x1, y0 + 55), (x1 - 55, y0 + 55)),
                           fill=_tint(tone, .72), outline=tone)


def _key(plate: Plate, center: Point, tone: str = GOLD, *, scale: float = 1.0) -> None:
    x, y = center
    radius = 27 * scale
    plate.draw.ellipse((x - radius, y - radius, x + radius, y + radius),
                       fill=GOLD_LIGHT, outline=tone, width=max(3, int(5 * scale)))
    plate.draw.ellipse((x - radius * .38, y - radius * .38,
                        x + radius * .38, y + radius * .38),
                       fill=PAPER_LIGHT, outline=tone, width=max(2, int(3 * scale)))
    plate.draw.line((x + radius, y, x + 103 * scale, y),
                    fill=tone, width=max(4, int(10 * scale)))
    plate.draw.line((x + 77 * scale, y, x + 77 * scale, y + 30 * scale,
                     x + 99 * scale, y + 30 * scale),
                    fill=tone, width=max(3, int(8 * scale)), joint="curve")


def _leaf(plate: Plate, center: Point, tone: str = GREEN, *,
          angle: float = 0.0, scale: float = 1.0) -> None:
    x, y = center
    ca, sa = math.cos(angle), math.sin(angle)
    source = ((-47, 0), (-21, -24), (19, -25), (50, 0),
              (19, 25), (-21, 24))
    points = tuple((x + (px * ca - py * sa) * scale,
                    y + (px * sa + py * ca) * scale) for px, py in source)
    plate.draw.polygon(points, fill=_tint(tone, .56), outline=tone)
    plate.draw.line((x - 42 * ca * scale, y - 42 * sa * scale,
                     x + 42 * ca * scale, y + 42 * sa * scale),
                    fill=tone, width=max(2, int(4 * scale)))


def _render_phonics(plate: Plate) -> None:
    # A spoken waveform meets three aligned grapheme/phoneme pairs, then blends.
    _tag(plate, (220, 229), "LOOK", TEAL)
    _tag(plate, (800, 229), "MAP IN ORDER", BLUE)
    _tag(plate, (1370, 229), "BLEND", CORAL)

    # Eye and printed word.
    plate.draw.ellipse((124, 305, 308, 415), fill=TEAL_LIGHT, outline=TEAL, width=5)
    plate.draw.ellipse((192, 333, 240, 381), fill=PAPER_LIGHT, outline=TEAL, width=4)
    plate.dot((216, 357), 12, fill=INK, outline=INK, width=1)
    plate.text((216, 476), "cat", size=72, bold=True, fill=INK, anchor="mm")
    _arrow(plate, (320, 392), (400, 392), TEAL)

    tiles = ((430, "c", "/k/", TEAL), (685, "a", "/æ/", GOLD),
             (940, "t", "/t/", PLUM))
    for x, letter, sound, tone in tiles:
        _word_tile(plate, (x, 310, x + 185, 490), letter, tone, sublabel="letter")
        plate.draw.line((x + 92, 500, x + 92, 574), fill=tone, width=5)
        plate.draw.ellipse((x + 27, 570, x + 158, 657),
                           fill=hex_rgba(_tint(tone, .76), 235), outline=tone, width=4)
        plate.draw.text((x + 92, 613), sound, font=_ipa_font(35),
                        fill=tone, anchor="mm", stroke_width=1, stroke_fill=tone)
        plate.text((x + 92, 688), "sound", size=23, bold=True,
                   fill=INK_SOFT, anchor="mm")

    # The curves visually merge three sounds into one utterance.
    for source_x, tone in ((522, TEAL), (777, GOLD), (1032, PLUM)):
        plate.draw.arc((source_x - 60, 640, 1285, 788), 7, 86, fill=tone, width=5)
    plate.draw.rounded_rectangle((1248, 451, 1464, 670), radius=105,
                                 fill=CORAL_LIGHT, outline=CORAL, width=5)
    plate.draw.arc((1285, 512, 1431, 614), 10, 170, fill=INK, width=7)
    plate.text((1356, 712), "cat", size=54, bold=True, fill=CORAL, anchor="mm")
    plate.text((800, 275), "one common pronunciation — accents can differ",
               size=22, bold=True, fill=INK_SOFT, anchor="mm")
    _footer(plate, "read left to right: letters cue sounds; sounds blend into a word", size=25)


def _render_rhymes(plate: Plate) -> None:
    _tag(plate, (445, 230), "ONSET + RIME", BLUE)
    _tag(plate, (1190, 230), "STEADY BEAT", GOLD)
    rows = (("c", "at", BLUE, True), ("h", "at", TEAL, True),
            ("s", "un", PLUM, False))
    for row, (onset, rime, tone, matches) in enumerate(rows):
        y = 306 + row * 135
        _word_tile(plate, (155, y, 310, y + 105), onset, tone)
        plate.text((338, y + 53), "+", size=38, bold=True, fill=INK_SOFT, anchor="mm")
        rime_tone = CORAL if matches else PLUM
        _word_tile(plate, (373, y, 590, y + 105), rime, rime_tone)
        whole = onset + rime
        plate.text((690, y + 52), whole, size=44, bold=True,
                   fill=tone, anchor="mm")
        if matches:
            plate.draw.line((640, y + 84, 740, y + 84), fill=CORAL, width=6)
        else:
            plate.text((690, y + 92), "different ending", size=21,
                       bold=True, fill=PLUM, anchor="mm")
    plate.draw.line((447, 291, 447, 696), fill=hex_rgba(CORAL, 85), width=3)
    plate.text((450, 741), "cat + hat share the ending sound", size=23, bold=True,
               fill=CORAL, anchor="mm")

    # Four beats remain constant while two rhyme endings align above them.
    x_positions = (930, 1080, 1230, 1380)
    plate.draw.line((885, 573, 1425, 573), fill=INK_SOFT, width=5)
    for index, x in enumerate(x_positions, start=1):
        plate.draw.ellipse((x - 38, 535, x + 38, 611),
                           fill=GOLD_LIGHT, outline=GOLD, width=5)
        plate.text((x, 573), str(index), size=28, bold=True, fill=GOLD, anchor="mm")
        plate.draw.line((x, 497, x, 526), fill=GOLD, width=5)
    plate.text((1155, 350), "CAT sat on the MAT", size=36, bold=True,
               fill=INK, anchor="mm")
    plate.text((1155, 418), "HAT fell down — like THAT", size=36, bold=True,
               fill=INK, anchor="mm")
    for x in (995, 1300):
        plate.draw.line((x - 38, 375, x + 38, 375), fill=CORAL, width=5)
        plate.draw.line((x - 44, 443, x + 44, 443), fill=CORAL, width=5)
    plate.text((1155, 683), "rhyme = matching final sound", size=27,
               bold=True, fill=CORAL, anchor="mm")
    _footer(plate, "rhyme matches an ending sound; rhythm organises the pulse", size=26)


def _render_stories(plate: Plate) -> None:
    # A garden path makes causal order spatial rather than a row of generic cards.
    plate.draw.rounded_rectangle((122, 254, 1478, 760), radius=35,
                                 fill=hex_rgba(GREEN_LIGHT, 76),
                                 outline=hex_rgba(GREEN, 110), width=3)
    plate.draw.polygon(((130, 672), (1465, 672), (1465, 760), (130, 760)),
                       fill=hex_rgba(GOLD_LIGHT, 85))
    path = ((205, 653), (468, 560), (765, 654), (1030, 514), (1367, 640))
    plate.polyline(path, fill=EDGE, width=18)
    for point in path:
        plate.dot(point, 13, fill=PAPER_LIGHT, outline=EDGE, width=4)

    # Mina as a filled character silhouette, plus a garden tree.
    _bust(plate, (215, 499), TEAL, facing=1)
    _tag(plate, (215, 290), "WHO", TEAL)
    plate.text((215, 337), "Mina", size=33, bold=True, fill=TEAL, anchor="mm")
    plate.draw.polygon(((1016, 637), (1043, 411), (1071, 637)),
                       fill=hex_rgba(EDGE, 180), outline=EDGE)
    for cx, cy, radius in ((978, 410, 83), (1054, 368, 96), (1133, 420, 82)):
        plate.draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius),
                           fill=hex_rgba(GREEN_LIGHT, 235), outline=GREEN, width=4)
    _tag(plate, (1055, 276), "WHERE: GARDEN", GREEN)

    _key(plate, (465, 445), GOLD, scale=.72)
    plate.draw.line((466, 487, 466, 526), fill=GOLD, width=4)
    plate.text((468, 393), "missing", size=27, bold=True, fill=CORAL, anchor="mm")
    plate.draw.line((423, 415, 511, 474), fill=CORAL, width=6)
    plate.draw.line((511, 415, 423, 474), fill=CORAL, width=6)
    _tag(plate, (468, 693), "PROBLEM", CORAL)

    for x, y, angle in ((724, 566, -.3), (792, 541, .3), (853, 579, -.15)):
        _leaf(plate, (x, y), GREEN, angle=angle, scale=.8)
    plate.text((790, 450), "search under leaves", size=29,
               bold=True, fill=GREEN, anchor="mm")
    _tag(plate, (789, 704), "ACTION", GREEN)

    _key(plate, (1321, 494), GOLD, scale=.9)
    plate.draw.ellipse((1259, 440, 1441, 622), outline=GOLD, width=5)
    plate.text((1352, 405), "found!", size=31, bold=True, fill=GOLD, anchor="mm")
    _tag(plate, (1352, 704), "OUTCOME", GOLD)
    _footer(plate, "character + setting anchor a causal chain: problem -> action -> outcome", size=24)


def _render_speaking_seedling(plate: Plate) -> None:
    _bust(plate, (250, 611), TEAL, facing=1)
    _bust(plate, (1350, 611), CORAL, facing=-1)
    _speech_bubble(plate, (125, 250, 590, 425), "What did you build?", TEAL,
                   tail="left")
    _speech_bubble(plate, (1010, 250, 1475, 425), "I built a tall bridge.", CORAL,
                   tail="right")
    # Listening is represented as sound reaching an ear before the response.
    plate.draw.arc((660, 408, 940, 695), 70, 290, fill=BLUE, width=9)
    plate.draw.arc((700, 445, 888, 645), 70, 290, fill=BLUE, width=7)
    plate.draw.arc((747, 487, 842, 599), 70, 290, fill=BLUE, width=6)
    plate.text((800, 365), "LISTEN", size=29, bold=True, fill=BLUE, anchor="mm")
    plate.text((800, 716), "hold the question in mind", size=25,
               bold=True, fill=INK_SOFT, anchor="mm")
    _arrow(plate, (447, 485), (680, 535), TEAL, "question")
    _arrow(plate, (923, 535), (1150, 485), CORAL, "relevant answer")
    # A return arc encodes repair/checking, rather than just alternating talk.
    plate.draw.arc((425, 605, 1175, 791), 8, 172, fill=PLUM, width=6)
    plate.arrow((455, 700), (421, 652), fill=PLUM, width=6, head=18)
    _tag(plate, (800, 760), "CHECK: Do you mean this bridge?", PLUM, size=23)
    _footer(plate, "each turn listens to and answers the turn before it", size=27)


def _render_spelling(plate: Plate) -> None:
    _tag(plate, (219, 229), "SPOKEN", TEAL)
    _tag(plate, (795, 229), "SEGMENT + MAP", BLUE)
    _tag(plate, (1375, 229), "CHECK", PLUM)
    # A waveform makes the distinction between continuous speech and selected units.
    wave = []
    for index in range(90):
        x = 128 + index * 3.1
        envelope = math.sin(index / 89 * math.pi)
        y = 432 + math.sin(index * .55) * 65 * envelope
        wave.append((x, y))
    plate.polyline(wave, fill=TEAL, width=6)
    plate.text((268, 530), "ship", size=52, bold=True, fill=TEAL, anchor="mm")
    _arrow(plate, (405, 431), (484, 431), TEAL)

    groups = ((505, "/ʃ/", "sh", TEAL), (745, "/ɪ/", "i", GOLD),
              (985, "/p/", "p", CORAL))
    for index, (x, sound, letters, tone) in enumerate(groups, start=1):
        plate.draw.ellipse((x, 315, x + 170, 455),
                           fill=hex_rgba(_tint(tone, .76), 230), outline=tone, width=5)
        plate.draw.text((x + 85, 385), sound, font=_ipa_font(33),
                        fill=tone, anchor="mm", stroke_width=1, stroke_fill=tone)
        plate.text((x + 85, 480), "sound {}".format(index), size=23,
                   bold=True, fill=INK_SOFT, anchor="mm")
        plate.draw.line((x + 85, 498, x + 85, 552), fill=tone, width=5)
        _word_tile(plate, (x + 10, 550, x + 160, 690), letters, tone,
                   sublabel="grapheme")
    # Braces/counts expose why the counts differ.
    plate.draw.line((520, 737, 1130, 737), fill=BLUE, width=5)
    plate.draw.line((520, 718, 520, 756), fill=BLUE, width=5)
    plate.draw.line((1130, 718, 1130, 756), fill=BLUE, width=5)
    plate.text((825, 777), "3 sounds  |  4 letters", size=29,
               bold=True, fill=BLUE, anchor="mm")
    plate.text((1360, 405), "s h i p", size=45, bold=True, fill=INK, anchor="mm")
    check_face = font(45, bold=True)
    check_start = 1360 - plate.draw.textlength("s h i p", font=check_face) / 2
    digraph_end = check_start + plate.draw.textlength("s h", font=check_face)
    plate.draw.rounded_rectangle((check_start - 8, 339, digraph_end + 8, 466), radius=15,
                                 outline=TEAL, width=5)
    plate.text((1360, 520), "sh = one sound", size=27,
               bold=True, fill=TEAL, anchor="mm")
    plate.text((1360, 602), "say | map | check", size=23,
               bold=True, fill=INK_SOFT, anchor="mm")
    plate.text((1360, 676), "one common pronunciation",
               size=18, bold=True, fill=INK_SOFT, anchor="mm")
    _footer(plate, "speech is segmented into sounds; spelling maps them to graphemes", size=25)


def _render_vocabulary(plate: Plate) -> None:
    _tag(plate, (390, 229), "INTENSITY", CORAL)
    _tag(plate, (1110, 229), "CONTEXT TEST", BLUE)
    # A calibrated vertical scale makes the semantic relation visible.
    plate.arrow((240, 735), (240, 286), fill=CORAL, width=8, head=23)
    plate.text((184, 509), "degree", size=25, bold=True, fill=CORAL,
               anchor="mm")
    levels = ((652, "big", 76, GREEN), (500, "huge", 112, GOLD),
              (335, "enormous", 158, CORAL))
    for y, word, length, tone in levels:
        plate.draw.line((285, y, 285 + length * 2.2, y), fill=tone, width=13)
        plate.dot((285, y), 12, fill=tone, outline=PAPER_LIGHT, width=3)
        plate.text((330, y - 38), word, size=38, bold=True, fill=tone, anchor="lm")
    plate.text((457, 755), "related meanings, not exact copies", size=27,
               bold=True, fill=INK_SOFT, anchor="mm")

    _panel(plate, (825, 300, 1460, 700), BLUE, radius=28)
    plate.text((1142, 367), "An enormous wave", size=39,
               bold=True, fill=CORAL, anchor="mm")
    plate.text((1142, 421), "crossed the harbour wall.", size=34,
               bold=True, fill=INK, anchor="mm")
    # A wave profile gives the adjective a testable referent.
    wave = ((895, 617), (965, 575), (1037, 589), (1110, 535),
            (1180, 475), (1242, 525), (1315, 615), (1410, 615))
    plate.polyline(wave, fill=BLUE, width=9)
    plate.draw.line((890, 620, 1415, 620), fill=BLUE, width=5)
    plate.draw.line((1345, 513, 1345, 618), fill=EDGE, width=18)
    plate.draw.line((1310, 514, 1400, 514), fill=EDGE, width=12)
    plate.text((1137, 662), "does the scene support that degree?", size=24,
               bold=True, fill=BLUE, anchor="mm")
    _footer(plate, "choose the word whose degree and context match what you mean", size=25)


def _render_sentences(plate: Plate) -> None:
    _tag(plate, (800, 229), "ONE COMPLETE CLAUSE", BLUE)
    _panel(plate, (140, 288, 1460, 520), BLUE, radius=30)
    sentence = "The dog ran fast."
    face = font(70, bold=True)
    start_x, baseline = 265, 420
    plate.draw.text((start_x, baseline), sentence, font=face, fill=INK, anchor="lm")
    # Exact spans are measured, so brackets track the written constituents.
    widths = {part: plate.draw.textlength(part, font=face)
              for part in ("The dog", " ran fast", sentence)}
    subject_end = start_x + widths["The dog"]
    predicate_end = subject_end + widths[" ran fast"]
    plate.draw.line((start_x, 467, subject_end, 467), fill=TEAL, width=8)
    plate.draw.line((subject_end + 8, 467, predicate_end, 467), fill=CORAL, width=8)
    plate.text(((start_x + subject_end) / 2, 505), "SUBJECT", size=24,
               bold=True, fill=TEAL, anchor="mm")
    plate.text(((subject_end + predicate_end) / 2, 505), "PREDICATE", size=24,
               bold=True, fill=CORAL, anchor="mm")

    # Boundary marks are magnified separately from the grammatical relation.
    plate.draw.ellipse((171, 590, 337, 756), fill=TEAL_LIGHT, outline=TEAL, width=5)
    plate.text((254, 668), "T", size=70, bold=True, fill=TEAL, anchor="mm")
    plate.text((254, 780), "capital begins", size=23, bold=True,
               fill=TEAL, anchor="mm")
    _arrow(plate, (350, 666), (546, 666), TEAL)
    plate.text((800, 634), "The dog", size=37, bold=True, fill=TEAL, anchor="mm")
    plate.text((800, 698), "+", size=36, bold=True, fill=INK_SOFT, anchor="mm")
    plate.text((800, 760), "ran fast", size=37, bold=True, fill=CORAL, anchor="mm")
    _arrow(plate, (1050, 666), (1228, 666), CORAL)
    plate.draw.ellipse((1263, 590, 1429, 756), fill=CORAL_LIGHT, outline=CORAL, width=5)
    plate.dot((1346, 668), 15, fill=CORAL, outline=CORAL, width=1)
    plate.text((1346, 780), "full stop ends", size=23, bold=True,
               fill=CORAL, anchor="mm")
    _footer(plate, "subject + predicate express the thought; capitals and stops mark its boundary", size=23)


def _render_handwriting(plate: Plate) -> None:
    _tag(plate, (770, 221), "FORM LOWERCASE a", BLUE)
    # A large ruled-paper specimen with midline, baseline and descender zone.
    _panel(plate, (200, 270, 1325, 742), BLUE, radius=18, alpha=235)
    _rule(plate, 355, 230, 1295, tone=BLUE, dashed=True)
    _rule(plate, 555, 230, 1295, tone=BLUE, width=5)
    _rule(plate, 662, 230, 1295, tone=CORAL, dashed=True)
    plate.text((255, 329), "midline", size=23, bold=True, fill=BLUE)
    plate.text((255, 582), "baseline", size=23, bold=True, fill=BLUE)

    # Stroke one is a counter-clockwise oval; stroke two is a downstroke.
    plate.draw.arc((465, 355, 735, 555), 280, 638, fill=TEAL, width=21)
    plate.arrow((683, 386), (621, 358), fill=TEAL, width=9, head=22)
    plate.text((462, 406), "1", size=31, bold=True, fill=TEAL, anchor="mm")
    plate.draw.line((721, 370, 721, 553), fill=CORAL, width=21)
    plate.arrow((721, 413), (721, 539), fill=CORAL, width=8, head=21)
    plate.text((764, 405), "2", size=31, bold=True, fill=CORAL, anchor="mm")

    # Repeated forms expose consistent size and the whitespace between letters.
    for index, x in enumerate((875, 1022, 1169)):
        tone = INK if index != 1 else BLUE
        plate.draw.ellipse((x - 49, 355, x + 49, 555), outline=tone, width=12)
        plate.draw.line((x + 49, 355, x + 49, 555), fill=tone, width=12)
        if index < 2:
            plate.double_arrow((x + 57, 610), (x + 90, 610), fill=PLUM, width=4)
    plate.text((1019, 650), "even gap", size=23, bold=True, fill=PLUM, anchor="mm")

    # Pencil angle inset.
    plate.draw.rounded_rectangle((1345, 323, 1445, 642), radius=45,
                                 fill=GOLD_LIGHT, outline=GOLD, width=4)
    plate.draw.polygon(((1376, 577), (1402, 356), (1424, 363), (1402, 585)),
                       fill=CORAL_LIGHT, outline=EDGE)
    plate.draw.polygon(((1376, 577), (1402, 585), (1385, 625)),
                       fill=EDGE, outline=EDGE)
    plate.text((1370, 704), "pencil angle", size=21, bold=True,
               fill=GOLD, anchor="mm")
    _footer(plate, "ordered strokes + shared guides + even spacing make writing legible", size=25)


def _render_childrens_lit(plate: Plate) -> None:
    _tag(plate, (475, 224), "DETAIL IN THE BOOK", TEAL)
    left, right = _open_book(plate, (118, 285, 810, 728), TEAL)
    plate.text((285, 340), "The purse", size=29, bold=True, fill=INK, anchor="mm")
    plate.text((285, 388), "was still", size=29, bold=True, fill=INK, anchor="mm")
    plate.text((285, 436), "closed.", size=29, bold=True, fill=INK, anchor="mm")
    plate.text((635, 340), "She returned", size=29, bold=True, fill=INK, anchor="mm")
    plate.text((635, 388), "it to its", size=29, bold=True, fill=INK, anchor="mm")
    plate.text((635, 436), "owner.", size=29, bold=True, fill=INK, anchor="mm")
    for box in (left, right):
        x0, _, x1, _ = box
        for y in (505, 545, 585, 625):
            plate.draw.line((x0, y, x1, y), fill=hex_rgba(GRID, 160), width=3)
    plate.draw.rounded_rectangle((521, 315, 760, 472), radius=16,
                                 outline=CORAL, width=6)
    plate.text((466, 765), "observable evidence", size=25, bold=True,
               fill=TEAL, anchor="mm")

    # Branch from one detail to three different but accountable responses.
    source = (820, 493)
    destinations = ((1085, 329, "INFER", ("the action", "suggests honesty"), BLUE, "because"),
                    (1285, 493, "ASK", ("why was the choice", "difficult?"), GOLD, "wonder"),
                    (1085, 660, "RESPOND", ("I admired", "the choice"), PLUM, "cite"))
    for x, y, heading, detail, tone, relation in destinations:
        _arrow(plate, source, (x - 128, y), tone, relation, label_dy=-18, width=5)
        plate.draw.ellipse((x - 122, y - 78, x + 122, y + 78),
                           fill=hex_rgba(_tint(tone, .82), 230), outline=tone, width=4)
        plate.text((x, y - 28), heading, size=24, bold=True, fill=tone, anchor="mm")
        _center_lines(plate, (x, y + 20), detail, size=21,
                      bold=True, fill=INK)
    _footer(plate, "inference, questions, and response stay accountable to the text", size=25)


def _render_writing_stories(plate: Plate) -> None:
    _tag(plate, (800, 220), "A STORY CHANGES STATE", CORAL)
    # A story mountain doubles as a causal graph.
    points = ((165, 681), (465, 551), (798, 300), (1110, 493), (1432, 681))
    plate.polyline(points, fill=CORAL, width=11)
    for point in points:
        plate.dot(point, 14, fill=PAPER_LIGHT, outline=CORAL, width=5)
    plate.text((242, 726), "BEGINNING", size=25, bold=True, fill=TEAL, anchor="mm")
    plate.text((798, 265), "PROBLEM", size=25, bold=True, fill=CORAL, anchor="mm")
    plate.text((1327, 726), "ENDING", size=25, bold=True, fill=GREEN, anchor="mm")

    # Kite launch.
    plate.draw.polygon(((265, 431), (329, 365), (393, 431), (329, 497)),
                       fill=GOLD_LIGHT, outline=GOLD)
    plate.draw.line((329, 497, 384, 536, 351, 563, 403, 590),
                    fill=INK_SOFT, width=4)
    plate.text((329, 332), "Leo launches a kite", size=27,
               bold=True, fill=TEAL, anchor="mm")

    # Tree catches the kite; the diagonal line is visually interrupted.
    plate.draw.polygon(((763, 617), (788, 403), (817, 617)),
                       fill=hex_rgba(EDGE, 180), outline=EDGE)
    for cx, cy, radius in ((724, 407, 66), (793, 368, 75), (859, 414, 64)):
        plate.draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius),
                           fill=GREEN_LIGHT, outline=GREEN, width=4)
    plate.draw.polygon(((842, 344), (884, 301), (926, 344), (884, 387)),
                       fill=GOLD_LIGHT, outline=GOLD)
    plate.text((798, 669), "kite catches: goal is blocked", size=26,
               bold=True, fill=CORAL, anchor="mm")

    # Ladder changes what is possible.
    plate.draw.line((1159, 668, 1260, 405), fill=BLUE, width=9)
    plate.draw.line((1201, 681, 1302, 418), fill=BLUE, width=9)
    for step in range(6):
        y = 640 - step * 42
        plate.draw.line((1178 + step * 16, y, 1223 + step * 16, y),
                        fill=BLUE, width=6)
    plate.text((1271, 359), "a neighbour brings a ladder", size=25,
               bold=True, fill=GREEN, anchor="mm")
    _arrow(plate, (965, 550), (1110, 520), GREEN, "new means")
    _footer(plate, "beginning sets a goal; the problem blocks it; the ending changes the outcome", size=23)


def _render_dictionary(plate: Plate) -> None:
    _tag(plate, (800, 220), "FOLLOW THE LETTERS", BLUE)
    left, right = _open_book(plate, (375, 270, 1225, 735), BLUE)
    plate.text((513, 322), "cat", size=28, bold=True, fill=BLUE, anchor="mm")
    plate.text((1086, 322), "cattle", size=28, bold=True, fill=BLUE, anchor="mm")
    entries = (("cat", "a small feline"), ("catch", "take hold of"),
               ("cater", "provide food or service"), ("cattle", "domestic bovines"))
    for index, (word, gloss) in enumerate(entries):
        page_x = 430 if index < 2 else 840
        y = 396 + (index % 2) * 123
        if word == "cater":
            plate.draw.rounded_rectangle((814, y - 29, 1167, y + 67), radius=13,
                                         fill=hex_rgba(GOLD_LIGHT, 185),
                                         outline=GOLD, width=4)
        plate.text((page_x, y), word, size=29, bold=True,
                   fill=CORAL if word == "cater" else INK)
        plate.text((page_x, y + 42), gloss, size=22, fill=INK_SOFT)
    plate.text((800, 755), "guide words: cat — cattle", size=26,
               bold=True, fill=BLUE, anchor="mm")

    # Alphabetical narrowing is shown in the margin like physical index tabs.
    stages = ((130, "C", TEAL), (205, "CA", GREEN), (280, "CAT", GOLD))
    for y, letters, tone in stages:
        plate.draw.rounded_rectangle((123, y + 170, 304, y + 250), radius=18,
                                     fill=hex_rgba(_tint(tone, .72), 235),
                                     outline=tone, width=4)
        plate.text((213, y + 210), letters, size=32, bold=True, fill=tone, anchor="mm")
        if y < 280:
            plate.arrow((213, y + 256), (213, y + 322), fill=tone, width=5, head=15)
    plate.text((214, 724), "compare next letter", size=21,
               bold=True, fill=INK_SOFT, anchor="mm")
    _footer(plate, "when earlier letters tie, the next letter decides the order", size=26)


def _render_grammar(plate: Plate) -> None:
    _tag(plate, (800, 216), "CONSTITUENT TREE", BLUE)
    # The tree itself is the explanation: words nest into phrases, then a clause.
    nodes = {
        "clause": (800, 330), "np": (475, 464), "vp": (1115, 464),
        "det": (280, 616), "noun": (556, 616), "verb": (955, 616),
        "pp": (1250, 616), "prep": (1162, 740), "noun2": (1370, 740),
    }
    edges = (("clause", "np"), ("clause", "vp"), ("np", "det"),
             ("np", "noun"), ("vp", "verb"), ("vp", "pp"),
             ("pp", "prep"), ("pp", "noun2"))
    for source, target in edges:
        plate.draw.line((*nodes[source], *nodes[target]), fill=INK_SOFT, width=5)
    labels = (("clause", "CLAUSE", BLUE), ("np", "NOUN PHRASE", TEAL),
              ("vp", "VERB PHRASE", CORAL), ("det", "determiner", TEAL),
              ("noun", "noun", TEAL), ("verb", "verb", CORAL),
              ("pp", "PREPOSITION PHRASE", PLUM), ("prep", "preposition", PLUM),
              ("noun2", "noun", PLUM))
    for key, label, tone in labels:
        x, y = nodes[key]
        if key in ("clause", "np", "vp", "pp"):
            _tag(plate, (x, y), label, tone, size=22)
        else:
            plate.text((x, y), label, size=22, bold=True, fill=tone, anchor="mm")
    words = ((280, "The", TEAL), (556, "fox", TEAL), (955, "jumps", CORAL),
             (1162, "over", PLUM), (1370, "logs", PLUM))
    for x, word, tone in words:
        y = 789 if word not in ("over", "logs") else 795
        plate.text((x, y), word, size=35, bold=True, fill=tone, anchor="mm")
    plate.text((800, 265), "The fox jumps over logs.", size=34,
               bold=True, fill=INK, anchor="mm")
    plate.text((475, 518), "functions as SUBJECT", size=22,
               bold=True, fill=TEAL, anchor="mm")
    plate.text((1115, 518), "functions as PREDICATE", size=22,
               bold=True, fill=CORAL, anchor="mm")
    _footer(plate, "words combine into phrases; phrases combine into a clause", size=27)


def _render_paragraphs(plate: Plate) -> None:
    _tag(plate, (460, 218), "PARAGRAPH ON THE PAGE", BLUE)
    _tag(plate, (1216, 218), "REASONING CHAIN", CORAL)
    _document(plate, (125, 278, 865, 767), BLUE)
    bands = (
        (326, 398, TEAL, "CLAIM", "Street trees can cool a neighbourhood."),
        (416, 500, BLUE, "EVIDENCE", "A shaded sensor read 4 C lower at noon."),
        (518, 615, CORAL, "EXPLAIN", "Leaves intercept sunlight and release water vapour."),
        (633, 723, PLUM, "LINK", "So well-placed canopy can reduce local heat."),
    )
    for y0, y1, tone, label, text in bands:
        plate.draw.rounded_rectangle((158, y0, 831, y1), radius=14,
                                     fill=hex_rgba(_tint(tone, .86), 222),
                                     outline=hex_rgba(tone, 160), width=3)
        plate.text((180, (y0 + y1) / 2), label, size=21, bold=True,
                   fill=tone, anchor="lm")
        plate.wrapped_text((330, y0 + 7, 808, y1 - 7), text,
                           size=23, bold=True, fill=INK, line_gap=5)

    route = ((1016, 346, "claim", TEAL, "C"),
             (1234, 346, "measurement", BLUE, "E"),
             (1234, 602, "mechanism", CORAL, "R"),
             (1016, 602, "qualified link", PLUM, "L"))
    for x, y, label, tone, code in route:
        plate.draw.ellipse((x - 86, y - 86, x + 86, y + 86),
                           fill=hex_rgba(_tint(tone, .78), 232), outline=tone, width=5)
        plate.text((x, y - 14), code, size=42, bold=True, fill=tone, anchor="mm")
        plate.text((x, y + 40), label, size=21, bold=True, fill=INK, anchor="mm")
    _arrow(plate, (1108, 346), (1138, 346), BLUE)
    _arrow(plate, (1234, 440), (1234, 506), CORAL)
    _arrow(plate, (1141, 602), (1108, 602), PLUM)
    plate.arrow((1016, 507), (1016, 441), fill=TEAL, width=5, head=16)
    plate.text((1126, 730), "every sentence earns the next", size=25,
               bold=True, fill=INK_SOFT, anchor="mm")
    _footer(plate, "explain how the evidence supports the claim; qualify its limits", size=25)


def _render_poetry(plate: Plate) -> None:
    _tag(plate, (449, 218), "LINES + SOUND", PLUM)
    _tag(plate, (1174, 218), "FORM AT WORK", GOLD)
    _document(plate, (124, 278, 795, 742), PLUM, fold=False)
    lines = (("Night lays silver on the sea", "A"),
             ("soft rain drums upon the stone", "B"),
             ("Light returns a path to me", "A"),
             ("each bright footstep walks alone", "B"))
    for index, (line, rhyme) in enumerate(lines):
        y = 352 + index * 92
        plate.text((171, y), line, size=29, bold=index in (0, 2), fill=INK)
        plate.draw.ellipse((701, y - 24, 756, y + 31),
                           fill=CORAL_LIGHT if rhyme == "A" else BLUE_LIGHT,
                           outline=CORAL if rhyme == "A" else BLUE, width=3)
        plate.text((728, y + 2), rhyme, size=23, bold=True,
                   fill=CORAL if rhyme == "A" else BLUE, anchor="mm")
    plate.draw.line((596, 390, 690, 390), fill=CORAL, width=5)
    plate.draw.line((589, 574, 690, 574), fill=CORAL, width=5)
    plate.draw.line((600, 482, 690, 482), fill=BLUE, width=5)
    plate.draw.line((599, 666, 690, 666), fill=BLUE, width=5)

    # Scansion and image are related but non-identical dimensions of form.
    _panel(plate, (875, 286, 1461, 474), GOLD)
    plate.text((1168, 334), "RHYTHM", size=23, bold=True, fill=GOLD, anchor="mm")
    plate.text((1168, 391), "soft RAIN | DRUMS upon | the STONE", size=25,
               bold=True, fill=INK, anchor="mm")
    for x in (1030, 1164, 1352):
        plate.draw.arc((x - 23, 417, x + 23, 451), 185, 355, fill=GOLD, width=4)
    _panel(plate, (875, 510, 1461, 742), BLUE)
    plate.text((1168, 557), "IMAGE", size=23, bold=True, fill=BLUE, anchor="mm")
    plate.draw.ellipse((959, 596, 1054, 691), fill=GOLD_LIGHT, outline=GOLD, width=4)
    plate.draw.arc((974, 583, 1095, 704), 90, 270, fill=PAPER_LIGHT, width=28)
    for index in range(5):
        y = 623 + index * 18
        plate.draw.arc((1092, y - 13, 1388, y + 26), 180, 360,
                       fill=BLUE, width=3)
    plate.text((1190, 713), "silver path across water", size=23,
               bold=True, fill=BLUE, anchor="mm")
    _footer(plate, "line breaks, rhythm, rhyme, and image shape how the poem is heard", size=24)


def _render_mythology(plate: Plate) -> None:
    _tag(plate, (800, 215), "COMPARE WITHOUT COLLAPSING CONTEXT", PLUM, size=22)
    columns = (
        (130, 545, "GILGAMESH", "Mesopotamian epic", "mortality + kingship", GOLD, "tablet"),
        (576, 991, "ODYSSEY", "ancient Greek epic", "homecoming + identity", BLUE, "ship"),
        (1022, 1468, "SUNDIATA", "Mande epic tradition", "founding + communal memory", GREEN, "voice"),
    )
    for x0, x1, title, context, question, tone, artifact in columns:
        _panel(plate, (x0, 280, x1, 744), tone, radius=28)
        plate.text(((x0 + x1) / 2, 327), title, size=27,
                   bold=True, fill=tone, anchor="mm")
        plate.text(((x0 + x1) / 2, 373), context, size=22,
                   bold=True, fill=INK_SOFT, anchor="mm")
        cx = (x0 + x1) / 2
        if artifact == "tablet":
            plate.draw.rounded_rectangle((cx - 105, 419, cx + 105, 594), radius=19,
                                         fill=GOLD_LIGHT, outline=EDGE, width=5)
            for row in range(5):
                y = 453 + row * 27
                for col in range(5):
                    x = cx - 76 + col * 36
                    plate.draw.line((x, y, x + 13, y - 8, x + 5, y + 8),
                                    fill=EDGE, width=3)
        elif artifact == "ship":
            plate.draw.arc((cx - 125, 473, cx + 125, 601), 4, 176,
                           fill=EDGE, width=12)
            plate.draw.line((cx, 420, cx, 555), fill=EDGE, width=8)
            plate.draw.polygon(((cx + 5, 430), (cx + 5, 530), (cx + 110, 514)),
                               fill=BLUE_LIGHT, outline=BLUE)
            for y in (602, 626):
                plate.draw.arc((cx - 145, y - 18, cx + 145, y + 24),
                               185, 355, fill=BLUE, width=4)
        else:
            # Concentric sound marks represent a performed oral tradition.
            plate.draw.ellipse((cx - 49, 453, cx + 49, 551),
                               fill=GREEN_LIGHT, outline=GREEN, width=5)
            plate.draw.arc((cx - 106, 421, cx + 106, 585), 300, 60,
                           fill=GREEN, width=6)
            plate.draw.arc((cx - 149, 393, cx + 149, 613), 300, 60,
                           fill=GREEN, width=5)
            plate.draw.line((cx - 118, 635, cx + 118, 635), fill=EDGE, width=6)
        plate.text((cx, 687), question, size=23, bold=True,
                   fill=tone, anchor="mm")
        # Shape coding (1/2/3 bars) reinforces column identity without colour.
        for mark in range((0 if artifact == "tablet" else 1 if artifact == "ship" else 2) + 1):
            plate.draw.line((cx - 24 + mark * 24, 719, cx - 8 + mark * 24, 719),
                            fill=tone, width=6)
    plate.text((800, 782), "shared human questions | distinct forms, languages, and histories",
               size=25, bold=True, fill=INK_SOFT, anchor="mm")
    _footer(plate, "comparison names a relation while preserving each tradition's context", size=24)


def _render_novels(plate: Plate) -> None:
    _tag(plate, (800, 215), "TRACK CHANGE ACROSS CHAPTERS", BLUE)
    x_positions = (232, 548, 864, 1180, 1430)
    for x in x_positions:
        plate.draw.line((x, 286, x, 730), fill=hex_rgba(GRID, 170), width=3)
    for index, x in enumerate(x_positions[:-1], start=1):
        plate.text((x, 258), "CH {}".format(index), size=23, bold=True,
                   fill=BLUE, anchor="mm")
    plate.arrow((158, 385), (1441, 385), fill=CORAL, width=7, head=20)
    plate.arrow((158, 545), (1441, 545), fill=TEAL, width=7, head=20)
    plate.arrow((158, 700), (1441, 700), fill=PLUM, width=7, head=20)
    plate.text((135, 385), "PLOT", size=22, bold=True, fill=CORAL, anchor="rm")
    plate.text((135, 545), "GOAL", size=22, bold=True, fill=TEAL, anchor="rm")
    plate.text((135, 700), "SETTING", size=22, bold=True, fill=PLUM, anchor="rm")

    events = ((232, "letter arrives"), (548, "journey begins"),
              (864, "help is offered"), (1180, "choice is tested"))
    for index, (x, text) in enumerate(events):
        plate.dot((x, 385), 14, fill=CORAL, outline=PAPER_LIGHT, width=3)
        plate.text((x, 340 if index % 2 == 0 else 430), text, size=22,
                   bold=True, fill=INK, anchor="mm")
    goals = ((232, "prove independence"), (548, "refuses help"),
             (864, "reconsiders"), (1180, "accepts help"))
    for x, text in goals:
        plate.dot((x, 545), 14, fill=TEAL, outline=PAPER_LIGHT, width=3)
        plate.text((x, 586), text, size=22, bold=True, fill=TEAL, anchor="mm")
    settings = ((232, "village", "familiar"), (548, "road", "uncertain"),
                (864, "city", "new rules"), (1180, "city", "new allies"))
    for index, (x, place, pressure) in enumerate(settings):
        shape = 20 + index * 3
        plate.draw.polygon(((x, 700 - shape), (x + shape, 700),
                            (x, 700 + shape), (x - shape, 700)),
                           fill=PLUM_LIGHT, outline=PLUM)
        plate.text((x, 751), "{}: {}".format(place, pressure), size=21,
                   bold=True, fill=PLUM, anchor="mm")
    for x in (548, 864, 1180):
        plate.draw.line((x, 400, x, 524), fill=hex_rgba(CORAL, 130), width=4)
        plate.draw.line((x, 566, x, 676), fill=hex_rgba(TEAL, 130), width=4)
    _footer(plate, "an event matters when it changes a goal, relation, or later possibility", size=24)


def _render_research(plate: Plate) -> None:
    _tag(plate, (800, 214), "ONE QUESTION — THREE TRACES TO CHECK", BLUE, size=22)
    plate.text((800, 260), "When was the bridge built?", size=36,
               bold=True, fill=INK, anchor="mm")
    sources = ((300, "ARCHIVE PLAN", "dated 1928", TEAL, "plan"),
               (800, "NEWSPAPER", "opened 1930", CORAL, "paper"),
               (1300, "MUSEUM PHOTO", "works visible, 1929", PLUM, "photo"))
    for x, heading, finding, tone, kind in sources:
        plate.draw.line((800, 285, x, 352), fill=hex_rgba(tone, 150), width=5)
        if kind == "plan":
            _document(plate, (160, 354, 440, 600), tone, fold=False)
            for dx in (205, 260, 315, 370):
                plate.draw.line((dx, 413, dx, 552), fill=TEAL, width=3)
            plate.draw.arc((198, 449, 400, 588), 190, 350, fill=TEAL, width=5)
        elif kind == "paper":
            _document(plate, (660, 354, 940, 600), tone)
            plate.text((800, 402), "CITY NEWS", size=24, bold=True,
                       fill=CORAL, anchor="mm")
            for y in (448, 481, 514, 547):
                plate.draw.line((701, y, 897, y), fill=GRID, width=4)
        else:
            plate.draw.rounded_rectangle((1160, 354, 1440, 600), radius=12,
                                         fill=INK_SOFT, outline=PLUM, width=5)
            plate.draw.arc((1192, 442, 1404, 572), 190, 350,
                           fill=PAPER_LIGHT, width=6)
            for bx in (1230, 1332):
                plate.draw.line((bx, 451, bx, 554), fill=PAPER_LIGHT, width=5)
            plate.draw.ellipse((1290, 377, 1340, 427), fill=PAPER_LIGHT)
        plate.text((x, 631), heading, size=23, bold=True, fill=tone, anchor="mm")
        plate.text((x, 671), finding, size=24, bold=True, fill=INK, anchor="mm")
        # Unique source marks reinforce independence without relying on hue.
        for mark in range(1 + (0 if x == 300 else 1 if x == 800 else 2)):
            plate.dot((x - 22 + mark * 22, 711), 6,
                      fill=tone, outline=tone, width=1)

    for x, tone in ((300, TEAL), (800, CORAL), (1300, PLUM)):
        plate.arrow((x, 727), (x + (800 - x) * .68, 790),
                    fill=tone, width=5, head=16)
    plate.draw.rounded_rectangle((514, 746, 1086, 810), radius=25,
                                 fill=hex_rgba(GOLD_LIGHT, 225), outline=GOLD, width=4)
    plate.text((800, 778), "works seen 1929  |  opened 1930", size=25,
               bold=True, fill=GOLD, anchor="mm")
    _footer(plate, "compare traceable sources, then separate construction from opening", size=25)


def _render_etymology(plate: Plate) -> None:
    _tag(plate, (800, 215), "ATTESTED HISTORY + WORD FORMATION", GOLD, size=22)
    # A root is shown as an earlier form, not as a mystical visual resemblance.
    plate.draw.rounded_rectangle((585, 278, 1015, 415), radius=28,
                                 fill=hex_rgba(GOLD_LIGHT, 230), outline=GOLD, width=5)
    plate.text((800, 326), "Latin portare", size=39, bold=True,
               fill=GOLD, anchor="mm")
    plate.text((800, 375), "to carry", size=27, bold=True,
               fill=INK_SOFT, anchor="mm")
    plate.draw.line((800, 417, 800, 499), fill=EDGE, width=9)
    plate.text((800, 466), "borrow + build", size=22, bold=True,
               fill=EDGE, anchor="mm")

    branches = ((300, "portable", "-able", "able to be carried", TEAL, "○"),
                (800, "import", "im- = inward", "carry in", BLUE, "→"),
                (1300, "export", "ex- = outward", "carry out", CORAL, "←"))
    for x, word, affix, meaning, tone, marker in branches:
        plate.draw.line((800, 499, x, 584), fill=tone, width=6)
        plate.draw.rounded_rectangle((x - 174, 552, x + 174, 744), radius=25,
                                     fill=hex_rgba(_tint(tone, .84), 230),
                                     outline=tone, width=4)
        plate.text((x, 603), word, size=36, bold=True, fill=tone, anchor="mm")
        plate.text((x, 649), affix, size=23, bold=True, fill=INK, anchor="mm")
        plate.text((x, 700), meaning, size=24, bold=True, fill=INK_SOFT, anchor="mm")
        # Shape/arrow marker redundantly encodes semantic contribution.
        if marker == "○":
            plate.draw.ellipse((x - 13, 718, x + 13, 744), outline=tone, width=4)
        elif word == "import":
            plate.arrow((x - 65, 730), (x - 20, 730), fill=tone, width=4, head=14)
        else:
            plate.arrow((x + 20, 730), (x + 65, 730), fill=tone, width=4, head=14)
    plate.text((800, 786), "a shared spelling is evidence only when the historical path is supported",
               size=23, bold=True, fill=INK_SOFT, anchor="mm")
    _footer(plate, "etymology traces forms through history; prefixes redirect the root meaning", size=24)


def _render_public_speaking(plate: Plate) -> None:
    _tag(plate, (382, 216), "VISIBLE ARGUMENT", CORAL)
    _tag(plate, (1195, 216), "AUDIENCE FEEDBACK", TEAL)
    # A speech track, with signposts and an explicit evidence-to-reason bridge.
    route = ((125, 270, "CLAIM", "Our pond needs shade", CORAL, "1"),
             (125, 400, "EXAMPLE", "summer water: 30 C", BLUE, "2"),
             (125, 530, "REASON", "shade reduces solar heating", GOLD, "3"),
             (125, 660, "TAKEAWAY", "plant suitable bank trees", GREEN, "4"))
    for x, y, heading, detail, tone, number in route:
        box = (x, y, x + 525, y + 108)
        _panel(plate, box, tone, radius=20)
        plate.draw.ellipse((x + 18, y + 23, x + 82, y + 87),
                           fill=tone, outline=tone)
        plate.text((x + 50, y + 55), number, size=25, bold=True,
                   fill=PAPER_LIGHT, anchor="mm")
        plate.text((x + 105, y + 31), heading, size=22,
                   bold=True, fill=tone)
        plate.text((x + 105, y + 70), detail, size=23,
                   bold=True, fill=INK)
    _arrow(plate, (388, 380), (388, 394), BLUE, width=5)
    _arrow(plate, (388, 510), (388, 524), GOLD, width=5)
    _arrow(plate, (388, 640), (388, 654), GREEN, width=5)
    _tag(plate, (608, 585), "therefore", GOLD, size=19)

    # Speaker, podium, and three audience states make delivery reciprocal.
    _bust(plate, (850, 465), CORAL, facing=1)
    plate.draw.polygon(((775, 526), (925, 526), (963, 752), (737, 752)),
                       fill=hex_rgba(EDGE, 180), outline=EDGE)
    plate.text((850, 615), "SIGNPOST", size=22, bold=True, fill=PAPER_LIGHT,
               anchor="mm")
    plate.text((850, 653), "“because…”", size=25, bold=True, fill=PAPER_LIGHT,
               anchor="mm")
    _speech_bubble(plate, (984, 268, 1452, 407),
                   "Can we follow the link?", TEAL, tail="right")
    for index, (x, symbol) in enumerate(((1085, "?"), (1260, "OK"), (1412, "!"))):
        tone = (PLUM, GREEN, GOLD)[index]
        plate.draw.ellipse((x - 45, 545, x + 45, 635),
                           fill=hex_rgba(_tint(tone, .7), 235), outline=tone, width=4)
        plate.text((x, 590), symbol, size=35, bold=True, fill=tone, anchor="mm")
        plate.draw.pieslice((x - 70, 620, x + 70, 744), 180, 360,
                            fill=hex_rgba(_tint(tone, .65), 220), outline=tone, width=3)
    plate.text((1250, 774), "pause | watch | clarify", size=24,
               bold=True, fill=TEAL, anchor="mm")
    _footer(plate, "signposts expose the reasoning; audience cues guide pace and clarification", size=24)


RENDERERS: Dict[str, Renderer] = {
    "lang.0.phonics": _render_phonics,
    "lang.0.rhymes": _render_rhymes,
    "lang.0.stories": _render_stories,
    "lang.0.speaking": _render_speaking_seedling,
    "lang.1.spelling": _render_spelling,
    "lang.1.vocabulary": _render_vocabulary,
    "lang.1.sentences": _render_sentences,
    "lang.1.handwriting": _render_handwriting,
    "lang.1.childrens-lit": _render_childrens_lit,
    "lang.1.writing-stories": _render_writing_stories,
    "lang.1.dictionary": _render_dictionary,
    "lang.2.grammar": _render_grammar,
    "lang.2.paragraphs": _render_paragraphs,
    "lang.2.poetry": _render_poetry,
    "lang.2.mythology": _render_mythology,
    "lang.2.novels": _render_novels,
    "lang.2.research": _render_research,
    "lang.2.etymology": _render_etymology,
    "lang.2.speaking": _render_public_speaking,
}


__all__ = ["RENDERERS"]
