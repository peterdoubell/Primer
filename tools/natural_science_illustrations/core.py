"""Shared deterministic drawing grammar for biology, chemistry, and Earth science.

The renderer intentionally uses auditable geometry, labelled flows, measured axes,
and conserved inventories.  The plates are teaching diagrams rather than decorative
art: every arrow and spatial relationship is supplied by the lesson spec.
"""

from __future__ import annotations

import io
import math
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Sequence, Tuple

from PIL import Image

from math_illustrations.core import (
    BLUE,
    BLUE_LIGHT,
    CONTENT,
    CORAL,
    CORAL_LIGHT,
    EDGE,
    GOLD,
    GOLD_LIGHT,
    GREEN,
    GREEN_LIGHT,
    GRID,
    HEIGHT,
    INK,
    INK_SOFT,
    PAPER,
    PAPER_LIGHT,
    PLUM,
    PLUM_LIGHT,
    STAGE_DIRS,
    STAGE_NAMES,
    TEAL,
    TEAL_LIGHT,
    WIDTH,
    Plate as _BasePlate,
    font,
    hex_rgba,
    mix,
)


Spec = Dict[str, object]
Point = Tuple[float, float]
Box = Tuple[float, float, float, float]

DOMAIN_DIRS = {
    "biology": "biology",
    "chemistry": "chemistry",
    "earth-space": "earth-space",
}

DOMAIN_ACCENTS = {
    "biology": GREEN,
    "chemistry": PLUM,
    "earth-space": BLUE,
}

PALETTE = [TEAL, CORAL, BLUE, GOLD, GREEN, PLUM]
PALE = [TEAL_LIGHT, CORAL_LIGHT, BLUE_LIGHT, GOLD_LIGHT, GREEN_LIGHT, PLUM_LIGHT]


def _symbol_text(value: str) -> bool:
    return any(ord(character) > 127 for character in value)


class SciencePlate(_BasePlate):
    """Primer plate with symbol-font fallback and a domain identifier."""

    def __init__(self, node_id: str, title: str, stage: int, domain: str):
        super().__init__(node_id, title, stage)
        self.domain = domain
        self.domain_accent = DOMAIN_ACCENTS[domain]
        self.text((1500, 92), domain.replace("-", " & ").upper(), size=20,
                  bold=True, fill=self.domain_accent, anchor="ra")

    def text(self, xy: Point, value: str, *, size: int = 36,
             bold: bool = False, math_face: bool = False, fill: str = INK,
             anchor: str = "la", stroke_width: int = 0) -> None:
        super().text(xy, value, size=size, bold=bold,
                     math_face=math_face or _symbol_text(value), fill=fill,
                     anchor=anchor, stroke_width=stroke_width)

    def label(self, xy: Point, value: str, *, size: int = 28,
              fill: str | None = None, text_fill: str = PAPER_LIGHT) -> None:
        face = font(size, bold=True, math_face=_symbol_text(value))
        left, top, right, bottom = self.draw.textbbox(xy, value, font=face, anchor="mm")
        self.draw.rounded_rectangle(
            (left - 17, top - 9, right + 17, bottom + 9), radius=15,
            fill=fill or self.accent,
        )
        self.draw.text(xy, value, font=face, fill=text_fill, anchor="mm")


def science_spec(node_id: str, title: str, stage: int, domain: str,
                 layout: str, content: Mapping[str, object], alt: str,
                 caption: str) -> Spec:
    return {
        "id": node_id,
        "title": title,
        "stage": stage,
        "domain": domain,
        "plate_id": node_id.replace(".", "-") + "-insight",
        "layout": layout,
        "content": dict(content),
        "alt": alt,
        "caption": caption,
    }


def validate_specs(specs: Mapping[str, Spec], expected_ids: Iterable[str]) -> None:
    expected = set(expected_ids)
    actual = set(specs)
    if actual != expected:
        raise ValueError("Natural-science spec mismatch; missing={}, extra={}".format(
            sorted(expected - actual), sorted(actual - expected)))
    required = {"id", "title", "stage", "domain", "plate_id", "layout",
                "content", "alt", "caption"}
    plate_ids = set()
    allowed_layouts = {"cards", "cycle", "flow", "branch", "graph",
                       "layers", "network", "scale", "matrix"}
    for node_id, item in specs.items():
        if set(item) != required or item["id"] != node_id:
            raise ValueError("Malformed natural-science spec for {}".format(node_id))
        if item["domain"] not in DOMAIN_DIRS:
            raise ValueError("Unknown domain for {}".format(node_id))
        if type(item["stage"]) is not int or item["stage"] not in STAGE_NAMES:
            raise ValueError("Invalid stage for {}".format(node_id))
        if item["layout"] not in allowed_layouts:
            raise ValueError("Invalid layout for {}".format(node_id))
        if not isinstance(item["content"], dict) or not item["content"]:
            raise ValueError("Missing diagram content for {}".format(node_id))
        for key in ("title", "plate_id", "alt", "caption"):
            if not isinstance(item[key], str) or not item[key].strip():
                raise ValueError("Missing {} for {}".format(key, node_id))
        if item["alt"] == item["caption"]:
            raise ValueError("Alt and caption must differ for {}".format(node_id))
        if min(len(str(item[key]).split()) for key in ("alt", "caption")) < 10:
            raise ValueError("Alt and caption need explanatory detail for {}".format(node_id))
        if item["plate_id"] in plate_ids:
            raise ValueError("Duplicate plate id {}".format(item["plate_id"]))
        plate_ids.add(item["plate_id"])


def _wrapped_center(plate: SciencePlate, box: Box, value: str, *, size: int = 23,
                    bold: bool = False, fill: str = INK, line_gap: int = 6) -> None:
    x0, y0, x1, y1 = box
    face = font(size, bold=bold, math_face=_symbol_text(value))
    words = value.split()
    lines: List[str] = []
    line = ""
    for word in words:
        trial = (line + " " + word).strip()
        if plate.draw.textlength(trial, font=face) <= x1 - x0 or not line:
            line = trial
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    leading = size + line_gap
    y = (y0 + y1 - (len(lines) * leading - line_gap)) / 2
    for line in lines:
        plate.draw.text(((x0 + x1) / 2, y), line, font=face, fill=fill,
                        anchor="ma")
        y += leading


def _pill(plate: SciencePlate, center: Point, text: str, *, fill: str,
          size: int = 21) -> None:
    face = font(size, bold=True, math_face=_symbol_text(text))
    box = plate.draw.textbbox(center, text, font=face, anchor="mm")
    plate.draw.rounded_rectangle((box[0] - 15, box[1] - 8, box[2] + 15, box[3] + 8),
                                 radius=14, fill=hex_rgba(fill, 225))
    plate.draw.text(center, text, font=face, fill=PAPER_LIGHT, anchor="mm")


def _footer(plate: SciencePlate, value: str) -> None:
    plate.draw.rounded_rectangle((165, 815, 1435, 880), radius=24,
                                 fill=hex_rgba(plate.domain_accent, 34),
                                 outline=hex_rgba(plate.domain_accent, 125), width=3)
    _wrapped_center(plate, (195, 823, 1405, 872), value, size=25, bold=True,
                    fill=INK)


def _arrow_between(plate: SciencePlate, start: Point, end: Point,
                   label: str = "", color: str | None = None) -> None:
    tone = color or plate.domain_accent
    plate.arrow(start, end, fill=tone, width=7, head=20)
    if label:
        _pill(plate, ((start[0] + end[0]) / 2,
                      (start[1] + end[1]) / 2 - 20), label, fill=tone, size=17)


def _draw_icon(plate: SciencePlate, center: Point, token: str,
               *, size: float = 82, color: str | None = None) -> None:
    """Draw a compact semantic glyph; labels carry meaning, glyphs aid scanning."""
    x, y = center
    c = color or plate.domain_accent
    pale = mix(c, PAPER_LIGHT, .62)
    d = plate.draw
    r = size / 2

    if token in {"sun", "light"}:
        d.ellipse((x-r*.48, y-r*.48, x+r*.48, y+r*.48), fill=GOLD_LIGHT,
                  outline=GOLD, width=5)
        for angle in range(0, 360, 45):
            a = math.radians(angle)
            d.line((x+math.cos(a)*r*.65, y+math.sin(a)*r*.65,
                    x+math.cos(a)*r, y+math.sin(a)*r), fill=GOLD, width=5)
    elif token in {"water", "drop", "rain"}:
        d.polygon(((x, y-r), (x-r*.58, y+r*.25), (x, y+r), (x+r*.58, y+r*.25)),
                  fill=BLUE_LIGHT, outline=BLUE)
        d.arc((x-r*.58, y, x+r*.58, y+r*.8), 5, 175, fill=BLUE, width=4)
    elif token == "cloud":
        d.ellipse((x-r*.8, y-r*.1, x-r*.05, y+r*.55), fill=BLUE_LIGHT, outline=BLUE, width=4)
        d.ellipse((x-r*.35, y-r*.55, x+r*.38, y+r*.55), fill=BLUE_LIGHT, outline=BLUE, width=4)
        d.ellipse((x+r*.05, y-r*.2, x+r*.8, y+r*.55), fill=BLUE_LIGHT, outline=BLUE, width=4)
    elif token in {"plant", "leaf", "seed"}:
        if token == "seed":
            d.ellipse((x-r*.35, y-r*.2, x+r*.35, y+r*.28), fill=GOLD_LIGHT,
                      outline=GOLD, width=5)
            d.arc((x-r*.12, y-r*.48, x+r*.38, y+r*.05), 160, 310, fill=GREEN, width=5)
        else:
            d.line((x, y+r*.8, x, y-r*.5), fill=GREEN, width=7)
            d.ellipse((x-r*.62, y-r*.4, x, y+r*.05), fill=GREEN_LIGHT,
                      outline=GREEN, width=4)
            d.ellipse((x, y-r*.62, x+r*.62, y-r*.15), fill=GREEN_LIGHT,
                      outline=GREEN, width=4)
            if token == "plant":
                for dx in (-.42, 0, .42):
                    d.line((x, y+r*.72, x+dx*r, y+r), fill=EDGE, width=4)
    elif token in {"animal", "fish", "bird"}:
        if token == "fish":
            d.ellipse((x-r*.65, y-r*.36, x+r*.48, y+r*.36), fill=BLUE_LIGHT,
                      outline=BLUE, width=4)
            d.polygon(((x+r*.42, y), (x+r, y-r*.48), (x+r, y+r*.48)),
                      fill=BLUE_LIGHT, outline=BLUE)
            d.ellipse((x-r*.42, y-r*.12, x-r*.31, y-.01*r), fill=INK)
        elif token == "bird":
            d.arc((x-r, y-r*.3, x, y+r*.6), 205, 350, fill=c, width=7)
            d.arc((x, y-r*.3, x+r, y+r*.6), 190, 335, fill=c, width=7)
        else:
            d.ellipse((x-r*.52, y-r*.28, x+r*.52, y+r*.38), fill=pale,
                      outline=c, width=4)
            d.ellipse((x+r*.25, y-r*.62, x+r*.78, y-r*.05), fill=pale,
                      outline=c, width=4)
            for dx in (-.36, .1, .42):
                d.line((x+dx*r, y+r*.28, x+dx*r, y+r*.78), fill=c, width=5)
    elif token in {"body", "person"}:
        d.ellipse((x-r*.22, y-r, x+r*.22, y-r*.56), fill=CORAL_LIGHT,
                  outline=CORAL, width=4)
        d.line((x, y-r*.54, x, y+r*.35), fill=c, width=8)
        d.line((x-r*.58, y-r*.15, x+r*.58, y-r*.15), fill=c, width=7)
        d.line((x, y+r*.3, x-r*.42, y+r), fill=c, width=7)
        d.line((x, y+r*.3, x+r*.42, y+r), fill=c, width=7)
    elif token in {"heart", "health"}:
        d.ellipse((x-r*.72, y-r*.55, x+.02*r, y+r*.18), fill=CORAL_LIGHT,
                  outline=CORAL, width=4)
        d.ellipse((x-.02*r, y-r*.55, x+r*.72, y+r*.18), fill=CORAL_LIGHT,
                  outline=CORAL, width=4)
        d.polygon(((x-r*.72, y-r*.12), (x+r*.72, y-r*.12), (x, y+r)),
                  fill=CORAL_LIGHT, outline=CORAL)
    elif token == "lungs":
        d.line((x, y-r, x, y-r*.22), fill=BLUE, width=8)
        d.ellipse((x-r*.76, y-r*.35, x-r*.04, y+r*.9), fill=BLUE_LIGHT,
                  outline=BLUE, width=4)
        d.ellipse((x+r*.04, y-r*.35, x+r*.76, y+r*.9), fill=BLUE_LIGHT,
                  outline=BLUE, width=4)
    elif token in {"brain", "neuron"}:
        if token == "brain":
            d.ellipse((x-r*.78, y-r*.64, x+r*.78, y+r*.62), fill=PLUM_LIGHT,
                      outline=PLUM, width=4)
            for dx, dy in ((-.35,-.2),(.25,-.25),(-.2,.25),(.35,.2)):
                d.arc((x+(dx-.25)*r, y+(dy-.2)*r, x+(dx+.25)*r, y+(dy+.2)*r),
                      20, 250, fill=PLUM, width=3)
        else:
            d.ellipse((x-r*.28, y-r*.28, x+r*.28, y+r*.28), fill=PLUM_LIGHT,
                      outline=PLUM, width=4)
            for angle in (135, 180, 225):
                a = math.radians(angle)
                d.line((x-r*.2, y, x+math.cos(a)*r, y+math.sin(a)*r), fill=PLUM, width=4)
            d.line((x+r*.25, y, x+r, y), fill=PLUM, width=6)
    elif token in {"cell", "microbe", "bacteria", "virus", "fungus"}:
        if token == "virus":
            d.ellipse((x-r*.43, y-r*.43, x+r*.43, y+r*.43), fill=CORAL_LIGHT,
                      outline=CORAL, width=4)
            for angle in range(0, 360, 45):
                a = math.radians(angle)
                p0=(x+math.cos(a)*r*.43,y+math.sin(a)*r*.43)
                p1=(x+math.cos(a)*r*.78,y+math.sin(a)*r*.78)
                d.line((*p0,*p1),fill=CORAL,width=4)
                d.ellipse((p1[0]-5,p1[1]-5,p1[0]+5,p1[1]+5),fill=CORAL)
        elif token == "bacteria":
            d.rounded_rectangle((x-r*.78,y-r*.38,x+r*.58,y+r*.38),radius=int(r*.35),
                                fill=TEAL_LIGHT,outline=TEAL,width=4)
            d.arc((x+r*.35,y-r*.1,x+r*1.15,y+r*.75),270,80,fill=TEAL,width=4)
            for dx in (-.35,0,.3): d.ellipse((x+dx*r-5,y-5,x+dx*r+5,y+5),fill=TEAL)
        elif token == "fungus":
            d.line((x,y+r*.75,x,y-r*.05),fill=EDGE,width=8)
            d.arc((x-r*.82,y-r*.72,x+r*.82,y+r*.35),180,360,fill=CORAL,width=7)
            d.line((x-r*.78,y-r*.15,x+r*.78,y-r*.15),fill=CORAL,width=6)
        else:
            d.ellipse((x-r*.82, y-r*.72, x+r*.82, y+r*.72), fill=GREEN_LIGHT,
                      outline=GREEN, width=4)
            d.ellipse((x-r*.25, y-r*.25, x+r*.25, y+r*.25), fill=PLUM_LIGHT,
                      outline=PLUM, width=4)
            for dx,dy in ((-.45,-.25),(.4,-.2),(-.35,.35),(.38,.3)):
                d.ellipse((x+dx*r-7,y+dy*r-7,x+dx*r+7,y+dy*r+7),fill=TEAL)
    elif token in {"dna", "genome", "chromosome", "sequence"}:
        if token == "chromosome":
            d.line((x-r*.55,y-r*.9,x+r*.55,y+r*.9),fill=PLUM,width=10)
            d.line((x+r*.55,y-r*.9,x-r*.55,y+r*.9),fill=CORAL,width=10)
        elif token == "sequence":
            for i, base in enumerate("ACGT"):
                _pill(plate,(x-r*.78+i*r*.52,y),base,fill=PALETTE[i],size=18)
        else:
            points1=[]; points2=[]
            for i in range(17):
                yy=y-r+i*r/8
                xx=x+math.sin(i*math.pi/4)*r*.45
                points1.append((xx,yy)); points2.append((2*x-xx,yy))
                if i%2==0: d.line((xx,yy,2*x-xx,yy),fill=GRID,width=3)
            d.line(points1,fill=PLUM,width=5); d.line(points2,fill=CORAL,width=5)
    elif token in {"atom", "orbital"}:
        d.ellipse((x-r*.17,y-r*.17,x+r*.17,y+r*.17),fill=CORAL,outline=INK,width=3)
        for angle in (0,60,120):
            d.ellipse((x-r*.85,y-r*.34,x+r*.85,y+r*.34),outline=BLUE,width=4)
            # Ellipse rotation is suggested by offset electrons rather than transformed pixels.
            a=math.radians(angle)
            d.ellipse((x+math.cos(a)*r*.72-7,y+math.sin(a)*r*.45-7,
                       x+math.cos(a)*r*.72+7,y+math.sin(a)*r*.45+7),fill=BLUE)
    elif token in {"molecule", "bond", "carbon", "polymer"}:
        count = 5 if token == "polymer" else 3
        spacing = r*1.45/(count-1)
        start=x-r*.72
        for i in range(count-1):
            d.line((start+i*spacing,y,start+(i+1)*spacing,y),fill=INK_SOFT,width=6)
        for i in range(count):
            fill = CORAL_LIGHT if (token == "molecule" and i==1) else BLUE_LIGHT
            d.ellipse((start+i*spacing-r*.22,y-r*.22,start+i*spacing+r*.22,y+r*.22),
                      fill=fill,outline=BLUE if fill==BLUE_LIGHT else CORAL,width=4)
    elif token in {"beaker", "acid", "base", "mix"}:
        d.polygon(((x-r*.58,y-r*.9),(x-r*.35,y+r*.75),(x+r*.35,y+r*.75),
                   (x+r*.58,y-r*.9)),fill=hex_rgba(PAPER_LIGHT,180),outline=c)
        liquid = CORAL_LIGHT if token=="acid" else (BLUE_LIGHT if token=="base" else TEAL_LIGHT)
        d.polygon(((x-r*.43,y+r*.05),(x-r*.35,y+r*.75),(x+r*.35,y+r*.75),
                   (x+r*.43,y+r*.05)),fill=liquid)
        d.line((x-r*.43,y+r*.05,x+r*.43,y+r*.05),fill=c,width=4)
    elif token == "ionic":
        for row in range(3):
            for col in range(3):
                tone = CORAL if (row + col) % 2 else BLUE
                px=x+(col-1)*r*.55; py=y+(row-1)*r*.55
                plate.dot((px,py),r*.15,fill=mix(tone,PAPER_LIGHT,.35),outline=tone,width=3)
                plate.text((px,py),"+" if tone==BLUE else "−",size=max(10,int(r*.24)),bold=True,fill=tone,anchor="mm")
    elif token in {"solid", "liquid", "gas", "particles"}:
        positions=[]
        if token=="solid":
            positions=[(-.55,-.5),(0,-.5),(.55,-.5),(-.55,0),(0,0),(.55,0),(-.55,.5),(0,.5),(.55,.5)]
        elif token=="liquid":
            positions=[(-.6,.45),(-.15,.52),(.35,.45),(.65,.05),(.05,.05),(-.45,-.02),(.4,-.42),(-.2,-.38)]
        else:
            positions=[(-.75,-.68),(.58,-.6),(-.1,-.1),(.74,.28),(-.62,.6),(.12,.7)]
        for dx,dy in positions: plate.dot((x+dx*r,y+dy*r),r*.12,fill=c,outline=INK_SOFT,width=2)
    elif token in {"flame", "energy"}:
        d.polygon(((x,y-r),(x-r*.68,y+r*.35),(x-r*.28,y+r),(x+r*.42,y+r*.75),
                   (x+r*.68,y+r*.12)),fill=CORAL_LIGHT,outline=CORAL)
        d.polygon(((x+.05*r,y-r*.2),(x-r*.25,y+r*.48),(x,y+r*.78),(x+r*.3,y+r*.35)),fill=GOLD)
    elif token in {"metal", "material", "rock"}:
        d.polygon(((x-r*.8,y+r*.45),(x-r*.55,y-r*.5),(x,y-r*.85),(x+r*.72,y-r*.3),
                   (x+r*.85,y+r*.55),(x,y+r*.85)),fill=pale,outline=c)
        d.line((x-r*.45,y-r*.2,x+r*.35,y+r*.35),fill=c,width=4)
    elif token in {"earth", "planet", "ringed-planet"}:
        d.ellipse((x-r*.85,y-r*.85,x+r*.85,y+r*.85),fill=BLUE_LIGHT,outline=BLUE,width=5)
        if token=="earth":
            d.polygon(((x-r*.48,y-r*.55),(x-r*.08,y-r*.72),(x+r*.18,y-r*.28),
                       (x-.04*r,y+.04*r),(x+r*.22,y+r*.52),(x-r*.3,y+r*.6)),fill=GREEN_LIGHT,outline=GREEN)
        elif token=="ringed-planet":
            d.arc((x-r*1.15,y-r*.35,x+r*1.15,y+r*.35),5,175,fill=GOLD,width=5)
    elif token == "snow":
        for angle in (0, 60, 120):
            a=math.radians(angle); dx,dy=math.cos(a)*r*.82,math.sin(a)*r*.82
            d.line((x-dx,y-dy,x+dx,y+dy),fill=BLUE,width=5)
    elif token == "bone":
        d.line((x-r*.55,y+r*.45,x+r*.55,y-r*.45),fill=GOLD_LIGHT,width=16)
        for px,py in ((x-r*.62,y+r*.52),(x-r*.48,y+r*.63),(x+r*.62,y-r*.52),(x+r*.48,y-r*.63)):
            d.ellipse((px-r*.18,py-r*.18,px+r*.18,py+r*.18),fill=GOLD_LIGHT,outline=GOLD,width=3)
    elif token == "food":
        d.ellipse((x-r*.82,y-r*.56,x+r*.82,y+r*.56),fill=PAPER_LIGHT,outline=BLUE,width=5)
        d.ellipse((x-r*.5,y-r*.3,x+r*.5,y+r*.3),fill=GREEN_LIGHT,outline=GREEN,width=3)
        d.line((x+r*.62,y-r*.72,x+r*.62,y+r*.72),fill=CORAL,width=5)
    elif token == "ocean":
        for offset in (-.34,.05,.44):
            points=[]
            for i in range(17):
                xx=x-r+i*r/8; yy=y+offset*r+math.sin(i*math.pi/4)*r*.13
                points.append((xx,yy))
            d.line(points,fill=BLUE,width=5)
    elif token == "telescope":
        d.polygon(((x-r*.72,y-r*.36),(x+r*.55,y-r*.08),(x+r*.46,y+r*.3),(x-r*.78,y)),fill=BLUE_LIGHT,outline=BLUE)
        d.line((x,y+r*.15,x-r*.35,y+r*.85),fill=INK,width=6)
        d.line((x,y+r*.15,x+r*.4,y+r*.85),fill=INK,width=6)
    elif token == "branch":
        d.line((x,y+r*.9,x,y-r*.75),fill=GREEN,width=7)
        for yy,side in ((.45,-1),(.1,1),(-.25,-1),(-.55,1)):
            d.line((x,y+yy*r,x+side*r*.62,y+(yy-.35)*r),fill=GREEN,width=6)
            d.ellipse((x+side*r*.72-r*.16,y+(yy-.45)*r-r*.16,x+side*r*.72+r*.16,y+(yy-.45)*r+r*.16),fill=GREEN_LIGHT,outline=GREEN,width=3)
    elif token == "graph":
        d.line((x-r*.75,y+r*.72,x-r*.75,y-r*.65),fill=INK,width=5)
        d.line((x-r*.75,y+r*.72,x+r*.78,y+r*.72),fill=INK,width=5)
        d.line((x-r*.6,y+r*.45,x-r*.15,y+.1*r,x+r*.18,y+.28*r,x+r*.7,y-r*.55),fill=c,width=7)
    elif token == "enzyme":
        d.arc((x-r*.82,y-r*.72,x+r*.45,y+r*.72),55,300,fill=GREEN,width=10)
        d.ellipse((x+r*.12,y-r*.24,x+r*.68,y+r*.32),fill=CORAL_LIGHT,outline=CORAL,width=4)
    elif token == "layers":
        for i,tone in enumerate((GOLD, CORAL, PLUM)):
            yy=y-r*.55+i*r*.5
            d.polygon(((x-r*.82,yy),(x+r*.62,yy),(x+r*.82,yy+r*.28),(x-r*.62,yy+r*.28)),fill=PALE[(i+3)%len(PALE)],outline=tone)
    elif token in {"star", "galaxy"}:
        if token=="star":
            points=[]
            for i in range(16):
                a=-math.pi/2+i*math.pi/8; rr=r*(.85 if i%2==0 else .38)
                points.append((x+math.cos(a)*rr,y+math.sin(a)*rr))
            d.polygon(points,fill=GOLD_LIGHT,outline=GOLD)
        else:
            for scale in (1,.72,.44):
                d.arc((x-r*scale,y-r*.38*scale,x+r*scale,y+r*.38*scale),15,205,fill=PLUM,width=5)
                d.arc((x-r*scale,y-r*.38*scale,x+r*scale,y+r*.38*scale),195,385,fill=BLUE,width=5)
            d.ellipse((x-8,y-8,x+8,y+8),fill=GOLD)
    elif token in {"mountain", "volcano"}:
        d.polygon(((x-r,y+r*.72),(x,y-r*.82),(x+r,y+r*.72)),fill=EDGE,outline=INK_SOFT)
        d.polygon(((x-r*.2,y-r*.5),(x,y-r*.82),(x+r*.24,y-r*.46)),fill=PAPER_LIGHT)
        if token=="volcano":
            d.line((x-r*.12,y-r*.7,x-r*.28,y-r*1.0),fill=CORAL,width=8)
            d.line((x+r*.1,y-r*.72,x+r*.32,y-r*1.02),fill=CORAL,width=8)
    elif token in {"rocket", "satellite"}:
        if token=="rocket":
            d.ellipse((x-r*.3,y-r,x+r*.3,y+r*.55),fill=PAPER_LIGHT,outline=BLUE,width=4)
            d.polygon(((x-r*.3,y+r*.2),(x-r*.72,y+r*.65),(x-r*.25,y+r*.58)),fill=CORAL_LIGHT,outline=CORAL)
            d.polygon(((x+r*.3,y+r*.2),(x+r*.72,y+r*.65),(x+r*.25,y+r*.58)),fill=CORAL_LIGHT,outline=CORAL)
            d.polygon(((x-r*.18,y+r*.55),(x,y+r),(x+r*.18,y+r*.55)),fill=GOLD)
        else:
            d.rectangle((x-r*.25,y-r*.25,x+r*.25,y+r*.25),fill=GOLD_LIGHT,outline=GOLD,width=4)
            d.rectangle((x-r,y-r*.18,x-r*.3,y+r*.18),fill=BLUE_LIGHT,outline=BLUE,width=3)
            d.rectangle((x+r*.3,y-r*.18,x+r,y+r*.18),fill=BLUE_LIGHT,outline=BLUE,width=3)
    elif token in {"shield", "antibody"}:
        if token=="antibody":
            d.line((x,y+r*.9,x,y),fill=PLUM,width=9)
            d.line((x,y,x-r*.65,y-r*.72),fill=PLUM,width=9)
            d.line((x,y,x+r*.65,y-r*.72),fill=PLUM,width=9)
        else:
            d.polygon(((x,y-r),(x+r*.75,y-r*.65),(x+r*.58,y+r*.45),
                       (x,y+r),(x-r*.58,y+r*.45),(x-r*.75,y-r*.65)),
                      fill=GREEN_LIGHT,outline=GREEN)
            d.line((x-r*.34,y,x-r*.05,y+r*.3,x+r*.42,y-r*.35),fill=GREEN,width=7)
    elif token in {"computer", "model"}:
        d.rounded_rectangle((x-r*.9,y-r*.7,x+r*.9,y+r*.52),radius=10,
                            fill=INK,outline=BLUE,width=4)
        d.rectangle((x-r*.72,y-r*.52,x+r*.72,y+r*.32),fill=BLUE_LIGHT)
        d.line((x,y+r*.52,x,y+r*.78),fill=INK,width=7)
        d.line((x-r*.45,y+r*.78,x+r*.45,y+r*.78),fill=INK,width=7)
    elif token in {"network", "system"}:
        pts=[(x,y-r*.72),(x-r*.7,y+r*.38),(x+r*.7,y+r*.38),(x,y+r*.76)]
        for a,b in ((0,1),(0,2),(1,3),(2,3),(1,2)):
            d.line((*pts[a],*pts[b]),fill=GRID,width=5)
        for i,p in enumerate(pts): plate.dot(p,r*.16,fill=PALETTE[i],outline=INK,width=3)
    elif token == "cycle":
        d.arc((x-r*.82,y-r*.82,x+r*.82,y+r*.82),25,335,fill=c,width=8)
        a=math.radians(25); tip=(x+math.cos(a)*r*.82,y+math.sin(a)*r*.82)
        d.polygon((tip,(tip[0]-18,tip[1]-22),(tip[0]+5,tip[1]-27)),fill=c)
    else:
        d.ellipse((x-r*.78,y-r*.78,x+r*.78,y+r*.78),fill=pale,outline=c,width=4)
        label=token[:2].upper()
        plate.text((x,y),label,size=max(18,int(r*.58)),bold=True,fill=c,anchor="mm")


def _draw_cards(plate: SciencePlate, content: Mapping[str, object]) -> None:
    items = list(content["items"])
    n = len(items)
    # Arrow labels need their own channel between cards.  The earlier 28px gap
    # was narrower than the label pills, and the next card was painted over
    # them, erasing the stated transition on every sequence plate.
    gap = 92 if content.get("arrows") else 28
    total = 1360
    width = (total - gap * (n - 1)) / n
    y0, y1 = 228, 780
    for i, item in enumerate(items):
        x0 = 120 + i * (width + gap); x1 = x0 + width
        tone = item.get("color", PALETTE[i % len(PALETTE)])
        plate.card((x0, y0, x1, y1), fill=hex_rgba(PAPER_LIGHT, 235),
                   outline=tone, width=4, radius=22)
        plate.label(((x0+x1)/2, y0+42), str(item["heading"]), size=19,
                    fill=tone)
        _draw_icon(plate, ((x0+x1)/2, y0+205), str(item.get("icon", "system")),
                   size=min(105, width*.38), color=tone)
        if item.get("stat"):
            _pill(plate, ((x0+x1)/2, y0+315), str(item["stat"]), fill=tone, size=18)
            detail_top = y0+350
        else:
            detail_top = y0+300
        _wrapped_center(plate, (x0+18, detail_top, x1-18, y1-20),
                        str(item["detail"]), size=20 if n >= 4 else 22,
                        fill=INK_SOFT)
    # Paint connectors after every opaque card so their heads and labels stay
    # visible.  The reserved gap above keeps those labels off card content.
    if content.get("arrows"):
        for i, item in enumerate(items[:-1]):
            x1 = 120 + i * (width + gap) + width
            _arrow_between(plate, (x1 + 7, (y0 + y1) / 2),
                           (x1 + gap - 7, (y0 + y1) / 2),
                           str(item.get("arrow", "")), plate.domain_accent)
    _footer(plate, str(content["footer"]))


def _draw_cycle(plate: SciencePlate, content: Mapping[str, object]) -> None:
    items=list(content["items"])
    if not 3 <= len(items) <= 6:
        raise ValueError("Cycle diagrams need three to six steps")
    cx,cy=800,500
    rx,ry=500,235
    card_w=250 if len(items)>=5 else 290
    card_h=150
    centers=[]
    for i,item in enumerate(items):
        angle=-math.pi/2 + i*2*math.pi/len(items)
        centers.append((cx+math.cos(angle)*rx,cy+math.sin(angle)*ry))
    for i,item in enumerate(items):
        p=centers[i]; q=centers[(i+1)%len(items)]
        vx=q[0]-p[0]; vy=q[1]-p[1]; mag=max(1,math.hypot(vx,vy))
        ux,uy=vx/mag,vy/mag
        pad=min(card_w*.5/max(abs(ux),.001),card_h*.5/max(abs(uy),.001))+9
        _arrow_between(plate,(p[0]+ux*pad,p[1]+uy*pad),
                       (q[0]-ux*pad,q[1]-uy*pad),
                       str(item.get("arrow", "")),plate.domain_accent)
    center_icon=str(content.get("center_icon","cycle"))
    _draw_icon(plate,(cx,cy),center_icon,size=120,color=plate.domain_accent)
    if content.get("center"):
        _pill(plate,(cx,cy+92),str(content["center"]),fill=plate.domain_accent,size=19)
    for i,item in enumerate(items):
        x,y=centers[i]; tone=PALETTE[i%len(PALETTE)]
        plate.card((x-card_w/2,y-card_h/2,x+card_w/2,y+card_h/2),
                   fill=hex_rgba(PAPER_LIGHT,242),outline=tone,width=4,radius=20)
        plate.label((x,y-card_h/2+30),str(item["heading"]),size=17,fill=tone)
        _draw_icon(plate,(x-card_w*.33,y+25),str(item.get("icon","cycle")),size=48,color=tone)
        _wrapped_center(plate,(x-card_w*.2,y-5,x+card_w*.45,y+card_h/2-10),
                        str(item["detail"]),size=16 if len(items)>=5 else 18,fill=INK_SOFT)
    _footer(plate,str(content["footer"]))


def _draw_flow(plate: SciencePlate, content: Mapping[str, object]) -> None:
    inputs=list(content["inputs"]); outputs=list(content["outputs"])
    left=(130,245,475,770); middle=(610,260,990,750); right=(1125,245,1470,770)
    for box,heading,items,tone in ((left,str(content.get("input_heading","INPUTS")),inputs,BLUE),
                                   (right,str(content.get("output_heading","OUTPUTS")),outputs,CORAL)):
        plate.card(box,fill=hex_rgba(PAPER_LIGHT,236),outline=tone,width=4,radius=24)
        plate.label(((box[0]+box[2])/2,box[1]+40),heading,size=19,fill=tone)
        usable=(box[3]-box[1]-100)/max(1,len(items))
        for i,item in enumerate(items):
            y=box[1]+100+(i+.5)*usable
            _draw_icon(plate,(box[0]+65,y),str(item.get("icon","system")),size=48,color=tone)
            _wrapped_center(plate,(box[0]+105,y-usable*.42,box[2]-16,y+usable*.42),
                            str(item["label"]),size=19,bold=True,fill=INK_SOFT)
    tone=plate.domain_accent
    plate.card(middle,fill=hex_rgba(mix(tone,PAPER_LIGHT,.72),235),outline=tone,width=5,radius=28)
    plate.label((800,middle[1]+48),str(content["process"]),size=21,fill=tone)
    _draw_icon(plate,(800,475),str(content.get("icon","system")),size=145,color=tone)
    _wrapped_center(plate,(middle[0]+35,585,middle[2]-35,715),str(content["mechanism"]),
                    size=21,bold=True,fill=INK)
    _arrow_between(plate,(490,500),(595,500),str(content.get("in_arrow","")),BLUE)
    _arrow_between(plate,(1005,500),(1110,500),str(content.get("out_arrow","")),CORAL)
    _footer(plate,str(content["footer"]))


def _draw_branch(plate: SciencePlate, content: Mapping[str, object]) -> None:
    root=str(content["root"]); branches=list(content["branches"])
    root_x=280; root_y=500
    plate.card((130,350,430,650),fill=hex_rgba(PAPER_LIGHT,240),outline=plate.domain_accent,width=5,radius=25)
    _draw_icon(plate,(280,455),str(content.get("root_icon","system")),size=100,color=plate.domain_accent)
    plate.label((280,585),root,size=20,fill=plate.domain_accent)
    ys=[285+i*(430/max(1,len(branches)-1)) for i in range(len(branches))] if len(branches)>1 else [500]
    for i,(item,y) in enumerate(zip(branches,ys)):
        tone=PALETTE[i%len(PALETTE)]
        plate.arrow((445,500),(660,y),fill=tone,width=6,head=18)
        plate.card((680,y-92,1460,y+92),fill=hex_rgba(PAPER_LIGHT,240),outline=tone,width=4,radius=21)
        _draw_icon(plate,(755,y),str(item.get("icon","system")),size=62,color=tone)
        plate.text((820,y-35),str(item["heading"]),size=22,bold=True,fill=tone)
        _wrapped_center(plate,(820,y-5,1430,y+72),str(item["detail"]),size=19,fill=INK_SOFT)
        if item.get("edge"):
            _pill(plate,(550,(500+y)/2-15),str(item["edge"]),fill=tone,size=15)
    _footer(plate,str(content["footer"]))


def _draw_graph(plate: SciencePlate, content: Mapping[str, object]) -> None:
    box=(155,250,1025,750)
    x_min,x_max=content.get("x_range",(0,10)); y_min,y_max=content.get("y_range",(0,10))
    x0,y0,x1,y1=box
    def pt(x:float,y:float)->Point:
        return (x0+(x-x_min)/(x_max-x_min)*(x1-x0),
                y1-(y-y_min)/(y_max-y_min)*(y1-y0))
    for frac in (.2,.4,.6,.8):
        xx=x0+frac*(x1-x0); yy=y0+frac*(y1-y0)
        plate.draw.line((xx,y0,xx,y1),fill=hex_rgba(GRID,150),width=2)
        plate.draw.line((x0,yy,x1,yy),fill=hex_rgba(GRID,150),width=2)
    plate.arrow((x0,y1),(x1+8,y1),fill=INK,width=5,head=18)
    plate.arrow((x0,y1),(x0,y0-8),fill=INK,width=5,head=18)
    plate.text(((x0+x1)/2,y1+45),str(content["x_label"]),size=22,bold=True,anchor="mm")
    plate.text((x0-20,y0-18),str(content["y_label"]),size=22,bold=True,anchor="ls")
    curves = list(content["curves"])
    # A fixed legend is more robust than putting labels on curve endpoints:
    # several curves meet at the same endpoint, while right-edge labels used
    # to disappear underneath the callout card.
    legend_width = (x1 - x0) / max(1, len(curves))
    for i, curve in enumerate(curves):
        tone = curve.get("color", PALETTE[i % len(PALETTE)])
        center_x = x0 + (i + .5) * legend_width
        plate.draw.line((center_x - 105, 218, center_x - 52, 218),
                        fill=tone, width=8)
        _wrapped_center(plate, (center_x - 40, 198, center_x + 120, 238),
                        str(curve["label"]), size=18, bold=True, fill=INK)
    for i,curve in enumerate(curves):
        tone=curve.get("color",PALETTE[i%len(PALETTE)])
        points=[pt(float(a),float(b)) for a,b in curve["points"]]
        plate.polyline(points,fill=tone,width=8)
        for p in points:
            plate.dot(p,7,fill=tone,outline=PAPER_LIGHT,width=2)
    side=(1085,250,1460,750)
    plate.card(side,fill=hex_rgba(PAPER_LIGHT,240),outline=plate.domain_accent,width=4,radius=22)
    _draw_icon(plate,(1272,360),str(content.get("icon","model")),size=105,color=plate.domain_accent)
    plate.label((1272,470),str(content["callout_heading"]),size=19,fill=plate.domain_accent)
    _wrapped_center(plate,(1110,505,1435,710),str(content["callout"]),size=21,fill=INK_SOFT)
    _footer(plate,str(content["footer"]))


def _draw_layers(plate: SciencePlate, content: Mapping[str, object]) -> None:
    layers=list(content["layers"])
    mode=str(content.get("mode","stack"))
    if mode=="concentric":
        cx,cy=520,500
        max_r=260
        for i,item in enumerate(layers):
            radius=max_r-i*max_r/(len(layers)+.3)
            tone=item.get("color",PALETTE[i%len(PALETTE)])
            plate.draw.ellipse((cx-radius,cy-radius,cx+radius,cy+radius),
                               fill=hex_rgba(item.get("fill",PALE[i%len(PALE)]),235),
                               outline=tone,width=4)
        for i,item in enumerate(reversed(layers)):
            original=len(layers)-1-i
            radius=max_r-original*max_r/(len(layers)+.3)
            _pill(plate,(cx,cy-radius+25),str(item["heading"]),
                  fill=item.get("color",PALETTE[original%len(PALETTE)]),size=16)
        right=(880,230,1460,780)
        plate.card(right,fill=hex_rgba(PAPER_LIGHT,240),outline=plate.domain_accent,width=4,radius=22)
        slot=(right[3]-right[1]-50)/len(layers)
        for i,item in enumerate(layers):
            y=right[1]+25+(i+.5)*slot
            tone=item.get("color",PALETTE[i%len(PALETTE)])
            plate.dot((925,y),13,fill=tone,outline=INK,width=2)
            plate.text((958,y-slot*.22),str(item["heading"]),size=20,bold=True,fill=tone)
            _wrapped_center(plate,(958,y-5,1428,y+slot*.37),str(item["detail"]),size=17,fill=INK_SOFT)
    else:
        n=len(layers); h=500/n
        for i,item in enumerate(layers):
            y0=240+i*h; y1=y0+h-8; tone=item.get("color",PALETTE[i%len(PALETTE)])
            plate.card((190,y0,1410,y1),fill=hex_rgba(item.get("fill",PALE[i%len(PALE)]),220),
                       outline=tone,width=3,radius=14)
            plate.label((340,(y0+y1)/2),str(item["heading"]),size=18,fill=tone)
            _wrapped_center(plate,(520,y0+10,1365,y1-10),str(item["detail"]),size=20,fill=INK_SOFT)
    _footer(plate,str(content["footer"]))


def _draw_network(plate: SciencePlate, content: Mapping[str, object]) -> None:
    nodes=list(content["nodes"]); edges=list(content["edges"])
    positions={}
    for i,item in enumerate(nodes):
        if "pos" in item:
            px,py=item["pos"]
            positions[str(item["id"])]=(145+float(px)*1310,235+float(py)*520)
        else:
            angle=-math.pi/2+i*2*math.pi/len(nodes)
            positions[str(item["id"])]=(800+math.cos(angle)*470,500+math.sin(angle)*225)
    for edge in edges:
        a=positions[str(edge[0])]; b=positions[str(edge[1])]
        color=edge[3] if len(edge)>3 else plate.domain_accent
        bidirectional = (len(edge)>4 and edge[4] == "both") or (len(edge)>2 and edge[2] == "both")
        dx, dy = b[0] - a[0], b[1] - a[1]
        distance = max(1.0, math.hypot(dx, dy))
        ux, uy = dx / distance, dy / distance

        def boundary(center: Point, direction: Point) -> Point:
            vx, vy = direction
            horizontal = 120 / max(abs(vx), 1e-6)
            vertical = 68 / max(abs(vy), 1e-6)
            travel = min(horizontal, vertical) + 8
            return center[0] + vx * travel, center[1] + vy * travel

        start = boundary(a, (ux, uy))
        end = boundary(b, (-ux, -uy))
        if bidirectional: plate.double_arrow(start,end,fill=color,width=5)
        else: plate.arrow(start,end,fill=color,width=5,head=17)
        if len(edge)>2 and edge[2] not in {"", "both"}:
            _pill(plate,((a[0]+b[0])/2,(a[1]+b[1])/2-15),str(edge[2]),fill=color,size=14)
    for i,item in enumerate(nodes):
        x,y=positions[str(item["id"])]; tone=item.get("color",PALETTE[i%len(PALETTE)])
        plate.card((x-120,y-68,x+120,y+68),fill=hex_rgba(PAPER_LIGHT,245),outline=tone,width=4,radius=19)
        _draw_icon(plate,(x-76,y),str(item.get("icon","system")),size=48,color=tone)
        _wrapped_center(plate,(x-38,y-52,x+108,y+52),str(item["label"]),size=17,bold=True,fill=INK)
    _footer(plate,str(content["footer"]))


def _draw_scale(plate: SciencePlate, content: Mapping[str, object]) -> None:
    x0,x1=170,1430; y=520
    plate.arrow((x0,y),(x1,y),fill=plate.domain_accent,width=9,head=24)
    # Endpoint prose grows inward from bounded boxes instead of being centred
    # on the canvas margins, which clipped long pH and cosmology labels.
    _wrapped_center(plate, (x0, y + 35, x0 + 520, y + 112),
                    str(content["low_label"]), size=19, bold=True, fill=INK_SOFT)
    _wrapped_center(plate, (x1 - 520, y + 35, x1, y + 112),
                    str(content["high_label"]), size=19, bold=True, fill=INK_SOFT)
    points=list(content["points"])
    for i,item in enumerate(points):
        px=x0+float(item["position"])*(x1-x0); above=i%2==0; tone=item.get("color",PALETTE[i%len(PALETTE)])
        plate.draw.line((px,y-18,px,y+18),fill=INK,width=5)
        cy=y-145 if above else y+155
        plate.arrow((px,cy+(40 if above else -40)),(px,y+(-22 if above else 22)),fill=tone,width=4,head=14)
        _draw_icon(plate,(px,cy),str(item.get("icon","system")),size=60,color=tone)
        label_x = max(260, min(1340, px))
        plate.label((label_x,cy+(-62 if above else 62)),str(item["heading"]),size=16,fill=tone)
        if item.get("value"):
            plate.text((label_x,cy+30),str(item["value"]),size=17,bold=True,fill=INK_SOFT,anchor="mm")
    if content.get("note"):
        _wrapped_center(plate,(250,190,1350,255),str(content["note"]),size=20,bold=True,fill=INK)
    _footer(plate,str(content["footer"]))


def _draw_matrix(plate: SciencePlate, content: Mapping[str, object]) -> None:
    columns=list(content["columns"]); rows=list(content["rows"])
    x0,x1=190,1430; y0,y1=240,770
    row_label_w=300; col_w=(x1-x0-row_label_w)/len(columns); row_h=(y1-y0)/(len(rows)+1)
    plate.card((x0,y0,x1,y1),fill=hex_rgba(PAPER_LIGHT,240),outline=plate.domain_accent,width=4,radius=20)
    for j,col in enumerate(columns):
        cx=x0+row_label_w+(j+.5)*col_w
        plate.label((cx,y0+row_h/2),str(col),size=17,fill=PALETTE[j%len(PALETTE)])
    for i,row in enumerate(rows):
        cy=y0+(i+1.5)*row_h
        tone=PALETTE[i%len(PALETTE)]
        _wrapped_center(plate,(x0+18,cy-row_h*.43,x0+row_label_w-15,cy+row_h*.43),
                        str(row[0]),size=18,bold=True,fill=tone)
        for j,value in enumerate(row[1:]):
            cx=x0+row_label_w+(j+.5)*col_w
            _wrapped_center(plate,(cx-col_w*.45,cy-row_h*.43,cx+col_w*.45,cy+row_h*.43),
                            str(value),size=17,fill=INK_SOFT)
        if i<len(rows)-1:
            yy=y0+(i+2)*row_h
            plate.draw.line((x0+18,yy,x1-18,yy),fill=hex_rgba(GRID,160),width=2)
    _footer(plate,str(content["footer"]))


RENDERERS = {
    "cards": _draw_cards,
    "cycle": _draw_cycle,
    "flow": _draw_flow,
    "branch": _draw_branch,
    "graph": _draw_graph,
    "layers": _draw_layers,
    "network": _draw_network,
    "scale": _draw_scale,
    "matrix": _draw_matrix,
}


def render_image(item: Spec) -> Image.Image:
    plate = SciencePlate(str(item["id"]), str(item["title"]), int(item["stage"]),
                         str(item["domain"]))
    RENDERERS[str(item["layout"])](plate, item["content"])
    return plate.image


def encoded_pair(item: Spec) -> Tuple[bytes, bytes]:
    image = render_image(item)
    large = io.BytesIO(); small = io.BytesIO()
    image.save(large, "WEBP", quality=86, method=6)
    image.resize((800, 500), Image.Resampling.LANCZOS).save(
        small, "WEBP", quality=84, method=6)
    return large.getvalue(), small.getvalue()


def asset_paths(output_root: Path, item: Spec) -> Tuple[Path, Path]:
    directory = output_root / STAGE_DIRS[int(item["stage"])] / DOMAIN_DIRS[str(item["domain"])]
    stem = str(item["id"]).replace(".", "-")
    return directory / (stem + "-1600.webp"), directory / (stem + "-800.webp")


def render_spec(output_root: Path, item: Spec, *, overwrite: bool = False) -> List[Path]:
    paths = asset_paths(output_root, item)
    if not overwrite:
        existing = [path for path in paths if path.exists()]
        if existing:
            raise FileExistsError("Refusing to overwrite: {}".format(", ".join(map(str, existing))))
    paths[0].parent.mkdir(parents=True, exist_ok=True)
    large, small = encoded_pair(item)
    paths[0].write_bytes(large)
    paths[1].write_bytes(small)
    return list(paths)


def illustration_entry(item: Spec) -> Dict[str, object]:
    stage=int(item["stage"]); domain=DOMAIN_DIRS[str(item["domain"])]
    stem=str(item["id"]).replace(".", "-")
    prefix="/app/illustrations/{}/{}/{}".format(STAGE_DIRS[stage],domain,stem)
    return {
        "id": item["plate_id"],
        "kind": "illustration",
        "src": prefix + "-800.webp",
        "srcset": "{}-800.webp 800w, {}-1600.webp 1600w".format(prefix,prefix),
        "alt": item["alt"],
        "caption": item["caption"],
        "width": WIDTH,
        "height": HEIGHT,
    }
