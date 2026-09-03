"""A compact, auditable drawing grammar for radiology lesson plates.

The plates do not pretend to be diagnostic images.  They expose the reasoning
that a diagnostic image supports: acquisition -> visible sign -> inference ->
next action.  Anatomy silhouettes orient the relationship while authored
labels carry the exact discriminators and thresholds taught by each lesson.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

from PIL import Image

from physics_illustrations.core import (
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
    arrow_label,
    footer,
    hex_rgba,
    panel,
)
from math_illustrations.core import HEIGHT, STAGE_DIRS, STAGE_NAMES, WIDTH


Spec = Dict[str, object]
Point = Tuple[float, float]
Box = Tuple[float, float, float, float]

COLORS = (BLUE, TEAL, CORAL)
LIGHTS = (BLUE_LIGHT, TEAL_LIGHT, CORAL_LIGHT)

# The base palette was chosen for strokes and areas, not small text.  These
# paired tones retain each hue while meeting WCAG AA contrast on PAPER_LIGHT
# and on the corresponding pale panel colour.
TEXT_TONES = {
    BLUE: "#20465f",
    TEAL: "#20544f",
    GOLD: "#76520f",
    CORAL: "#7f3d31",
    PLUM: "#513957",
    GREEN: "#344b2d",
}


def _text_tone(color: str) -> str:
    return TEXT_TONES.get(color, INK)


class RadiologyPlate(Plate):
    """Plate whose small stage label uses the accessible palette tone."""

    def __init__(self, node_id: str, title: str, stage: int):
        super().__init__(node_id, title, stage)
        # Repaint the identical glyphs in place: this fully covers the lighter
        # base-palette text without flattening the paper texture behind it.
        self.text((96, 84), STAGE_NAMES[stage], size=24, bold=True,
                  fill=_text_tone(self.accent))


def _flow_headings(item: Spec) -> Tuple[str, str, str]:
    """Return authored headings without imposing a false clinical workflow.

    Specs may put a ``heading`` on each explanatory item or provide a top-level
    three-item ``headings`` sequence.  ``STEP`` is a deliberately neutral
    fallback for older records; the item label below it carries the clinical
    verb.  This avoids calling observations "ACQUIRE" or decisions "READ".
    """
    entries = list(item["items"])
    supplied = item.get("headings")
    if isinstance(supplied, (list, tuple)) and len(supplied) == 3:
        defaults = tuple(str(value) for value in supplied)
    else:
        defaults = ("STEP 1", "STEP 2", "STEP 3")
    return tuple(
        str(entry.get("heading") or defaults[index])
        for index, entry in enumerate(entries)
    )  # type: ignore[return-value]


def asset_paths(output_root: Path, node_id: str, stage: int) -> Tuple[Path, Path]:
    stem = node_id.replace(".", "-")
    directory = output_root / STAGE_DIRS[stage] / "radiology"
    return directory / (stem + "-1600.webp"), directory / (stem + "-800.webp")


def illustration_entry(item: Spec) -> Dict[str, object]:
    node_id = str(item["id"])
    stage = int(item["stage"])
    stem = node_id.replace(".", "-")
    prefix = "/app/illustrations/{}/radiology/{}".format(STAGE_DIRS[stage], stem)
    entries = list(item["items"])
    labels = [str(entry["label"]) for entry in entries]
    headings = _flow_headings(item) if item.get("mode") == "flow" else tuple(labels)
    return {
        "id": stem + "-reasoning-plate",
        "kind": "illustration",
        "src": prefix + "-800.webp",
        "srcset": "{}-800.webp 800w, {}-1600.webp 1600w".format(prefix, prefix),
        "alt": "A radiology reasoning diagram for {} linking {}.".format(
            item["title"], ", ".join(labels[:-1]) + ", and " + labels[-1]),
        "caption": item["takeaway"],
        "long_description": {
            "title": item["title"],
            "mode": item["mode"],
            "items": [
                {
                    "heading": headings[index],
                    "label": str(entry["label"]),
                    "detail": str(entry["detail"]),
                }
                for index, entry in enumerate(entries)
            ],
            "takeaway": item["takeaway"],
        },
        "width": WIDTH,
        "height": HEIGHT,
    }


def _short_title(value: str) -> str:
    first = value.split(":", 1)[0].strip()
    replacements = {
        "Peripheral, Carotid and Mesenteric Vascular Imaging": "Peripheral & Visceral Vessels",
        "Cerebral Venous Thrombosis and CSF Disorders": "Venous Thrombosis & CSF",
        "Multiple Sclerosis and the White Matter Differential": "MS & White Matter Mimics",
        "Uterus and Cervix": "Uterus, Cervix & Endometriosis",
        "Bone Marrow, Stress Injury, Muscle and the Diabetic Foot": "Marrow, Muscle & Diabetic Foot",
        "Developmental Dysplasia of the Hip and the Child's Elbow": "The Child's Hip & Elbow",
        "Paediatric Masses and Neonatal Neurosonography": "Paediatric Masses & Neurosonography",
        "Pulmonary Embolism and Pulmonary Hypertension": "Pulmonary Embolism & Hypertension",
        "Biliary Obstruction, Stones and the Thickened Gallbladder": "Biliary Obstruction & Gallbladder",
        "Bowel Ischaemia and Wall Thickening Patterns": "Bowel Ischaemia & Wall Thickening",
        "Pancreatic Cancer Staging and Cystic Lesions": "Pancreatic Cancer & Cystic Lesions",
        "Peritoneum, Mesentery and the Abdominal Wall": "Peritoneum, Mesentery & Abdominal Wall",
    }
    first = replacements.get(first, first)
    if len(first) <= 43:
        return first
    words = first.split()
    while len(" ".join(words)) > 40 and len(words) > 4:
        words.pop()
    # Keep this ASCII: the Plate font selector treats any non-ASCII character
    # as mathematical notation, so a Unicode ellipsis changed the whole title
    # to the STIX maths face.
    return " ".join(words) + "..."


def _body_outline(plate: Plate, center: Point, scale: float = 1.0) -> None:
    x, y = center
    plate.draw.ellipse((x - 42 * scale, y - 160 * scale,
                        x + 42 * scale, y - 76 * scale),
                       fill=hex_rgba(GOLD_LIGHT, 95), outline=INK_SOFT, width=max(2, int(3 * scale)))
    plate.draw.rounded_rectangle((x - 92 * scale, y - 78 * scale,
                                  x + 92 * scale, y + 150 * scale),
                                 radius=int(38 * scale), fill=hex_rgba(PAPER_LIGHT, 80),
                                 outline=INK_SOFT, width=max(2, int(3 * scale)))


def _lungs(plate: Plate, center: Point, scale: float, mark: str, color: str,
           *, context: str = "", label: str = "", variant: int = 0) -> None:
    x, y = center
    plate.draw.line((x, y - 125 * scale, x, y - 54 * scale), fill=INK_SOFT,
                    width=max(4, int(9 * scale)))
    plate.draw.ellipse((x - 112 * scale, y - 68 * scale, x - 8 * scale, y + 112 * scale),
                       fill=hex_rgba(BLUE_LIGHT, 90), outline=BLUE, width=max(2, int(4 * scale)))
    plate.draw.ellipse((x + 8 * scale, y - 68 * scale, x + 112 * scale, y + 112 * scale),
                       fill=hex_rgba(BLUE_LIGHT, 90), outline=BLUE, width=max(2, int(4 * scale)))
    if mark == "none":
        return
    if context == "rad.5.paeds-chest" and mark == "paeds-device-tip":
        # A neonatal chest device check: endotracheal tube ends above the
        # carina and the enteric tube continues below the diaphragm.  These are
        # tip zones, not a claim about an individual radiograph.
        carina_y = y - 45 * scale
        plate.draw.line((x - 13 * scale, y - 145 * scale,
                         x - 13 * scale, carina_y - 18 * scale),
                        fill=color, width=max(2, int(5 * scale)))
        plate.draw.line((x + 17 * scale, y - 145 * scale,
                         x + 17 * scale, y + 124 * scale),
                        fill=TEAL, width=max(2, int(5 * scale)))
        plate.draw.arc((x - 116 * scale, y + 54 * scale,
                        x + 116 * scale, y + 136 * scale), 190, 350,
                       fill=INK_SOFT, width=max(2, int(4 * scale)))
        plate.text((x - 25 * scale, y - 108 * scale), "ETT", size=max(12, int(17 * scale)),
                   bold=True, fill=_text_tone(color), anchor="ra")
        plate.text((x + 28 * scale, y + 105 * scale), "NG", size=max(12, int(17 * scale)),
                   bold=True, fill=_text_tone(TEAL), anchor="la")
    elif context == "rad.5.paeds-chest" and mark == "paeds-lung-pattern":
        # A diffuse, asymmetric air-space pattern is more honest here than the
        # old solitary "mass" dot.
        for dx, dy, radius in ((-55, -5, 28), (-30, 42, 23), (45, 25, 35)):
            plate.draw.ellipse((x + (dx - radius) * scale, y + (dy - radius) * scale,
                                x + (dx + radius) * scale, y + (dy + radius) * scale),
                               fill=hex_rgba(color, 90), outline=_text_tone(color),
                               width=max(1, int(2 * scale)))
    elif context == "rad.5.pe-pulm-htn" and label == "Assess strain":
        # Paired chamber areas communicate the RV:LV comparison without
        # pretending this frontal lung icon is an axial CTPA slice.
        plate.draw.ellipse((x - 54 * scale, y - 14 * scale,
                            x + 16 * scale, y + 68 * scale),
                           outline=color, width=max(3, int(7 * scale)))
        plate.draw.ellipse((x + 20 * scale, y - 2 * scale,
                            x + 70 * scale, y + 58 * scale),
                           outline=TEAL, width=max(3, int(7 * scale)))
        plate.text((x - 20 * scale, y + 28 * scale), "RV", size=max(12, int(18 * scale)),
                   bold=True, fill=_text_tone(color), anchor="mm")
        plate.text((x + 45 * scale, y + 28 * scale), "LV", size=max(12, int(18 * scale)),
                   bold=True, fill=_text_tone(TEAL), anchor="mm")
    elif context == "rad.5.pe-pulm-htn" and label == "Acquire CTPA":
        plate.draw.line((x, y - 54 * scale, x - 62 * scale, y + 24 * scale),
                        fill=color, width=max(3, int(8 * scale)))
        plate.draw.line((x, y - 54 * scale, x + 62 * scale, y + 24 * scale),
                        fill=color, width=max(3, int(8 * scale)))
        for dx in (-62, 62):
            plate.draw.line((x + dx * scale, y + 22 * scale,
                             x + dx * 1.28 * scale, y + 68 * scale),
                            fill=color, width=max(2, int(5 * scale)))
    elif context == "rad.3.chest-xray" and label == "Search in order":
        # A numbered sweep is an evidence glyph for the search pattern; a
        # fabricated lung mass would falsely imply the lesson teaches a case.
        for number, (dx, dy) in enumerate(((-56, -36), (44, -15), (-34, 60)), 1):
            plate.draw.ellipse((x + (dx - 15) * scale, y + (dy - 15) * scale,
                                x + (dx + 15) * scale, y + (dy + 15) * scale),
                               fill=_text_tone(color))
            plate.text((x + dx * scale, y + dy * scale), str(number),
                       size=max(11, int(16 * scale)), bold=True, fill=PAPER_LIGHT,
                       anchor="mm")
    elif context == "rad.3.chest-xray" and label == "Localise":
        # The highlighted cardiomediastinal border makes the silhouette-sign
        # relationship visible without inventing a discrete mass.
        plate.draw.arc((x - 34 * scale, y - 18 * scale,
                        x + 62 * scale, y + 104 * scale), 95, 250,
                       fill=color, width=max(3, int(8 * scale)))
        plate.draw.line((x - 65 * scale, y + 48 * scale,
                         x - 8 * scale, y + 48 * scale), fill=color,
                        width=max(2, int(5 * scale)))
    elif mark in {"air", "pneumothorax", "paeds-air-leak"} and context != "rad.5.airways":
        plate.draw.arc((x + 20 * scale, y - 50 * scale, x + 98 * scale, y + 95 * scale),
                       75, 275, fill=color, width=max(3, int(8 * scale)))
        # No vascular markings peripheral to the pleural line.
        plate.draw.line((x + 91 * scale, y - 35 * scale, x + 91 * scale, y + 65 * scale),
                        fill=PAPER_LIGHT, width=max(4, int(12 * scale)))
    elif mark in {"fluid", "effusion"}:
        plate.draw.pieslice((x - 108 * scale, y - 65 * scale, x - 8 * scale, y + 112 * scale),
                            25, 155, fill=hex_rgba(color, 150))
    elif context == "rad.5.airways" and label == "Bronchiectasis":
        # Airway-artery pairs: a dilated airway exceeds its companion artery
        # and fails to taper along a branching path.
        plate.draw.line((x - 68 * scale, y + 64 * scale,
                         x - 35 * scale, y + 2 * scale,
                         x - 67 * scale, y - 50 * scale), fill=color,
                        width=max(4, int(10 * scale)), joint="curve")
        for cx, cy in ((-36, 2), (-67, -50)):
            plate.draw.ellipse((x + (cx - 14) * scale, y + (cy - 14) * scale,
                                x + (cx + 14) * scale, y + (cy + 14) * scale),
                               fill=PAPER_LIGHT, outline=color,
                               width=max(3, int(6 * scale)))
            plate.draw.ellipse((x + (cx + 18) * scale, y + (cy - 7) * scale,
                                x + (cx + 32) * scale, y + (cy + 7) * scale),
                               fill=CORAL)
    elif context == "rad.5.airways" and label == "Small airways":
        for dx, dy in ((25, -40), (46, -19), (61, 5), (34, 27), (63, 48)):
            plate.draw.line((x + (dx - 17) * scale, y + (dy - 17) * scale,
                             x + dx * scale, y + dy * scale), fill=color,
                            width=max(1, int(3 * scale)))
            for angle in (-40, 40):
                radians = math.radians(angle)
                plate.draw.ellipse((x + (dx + 13 * math.cos(radians) - 4) * scale,
                                    y + (dy + 13 * math.sin(radians) - 4) * scale,
                                    x + (dx + 13 * math.cos(radians) + 4) * scale,
                                    y + (dy + 13 * math.sin(radians) + 4) * scale), fill=color)
    elif mark in {"nodule", "mass"}:
        plate.draw.ellipse((x + 32 * scale, y - 12 * scale, x + 62 * scale, y + 18 * scale),
                           fill=color, outline=INK, width=max(1, int(2 * scale)))
    elif mark in {"embolus", "clot"}:
        plate.draw.line((x, y - 54 * scale, x + 55 * scale, y - 5 * scale), fill=CORAL,
                        width=max(3, int(7 * scale)))
        plate.draw.ellipse((x + 39 * scale, y - 21 * scale, x + 67 * scale, y + 7 * scale),
                           fill=color)
    elif mark == "reticulation":
        for shift in (-62, -30, 22, 54):
            plate.draw.line((x + shift * scale, y + 38 * scale,
                             x + (shift + 28) * scale, y + 88 * scale),
                            fill=color, width=max(2, int(4 * scale)))
            plate.draw.line((x + shift * scale, y + 88 * scale,
                             x + (shift + 28) * scale, y + 38 * scale),
                            fill=color, width=max(1, int(3 * scale)))
    elif mark == "fibrosis":
        for cx in (-62, -32, 28, 58):
            for cy in (54, 82):
                plate.draw.ellipse((x + (cx - 13) * scale, y + (cy - 10) * scale,
                                    x + (cx + 13) * scale, y + (cy + 10) * scale),
                                   outline=color, width=max(2, int(4 * scale)))
        plate.draw.line((x - 71 * scale, y - 29 * scale,
                         x - 47 * scale, y + 45 * scale), fill=color,
                        width=max(3, int(6 * scale)))
    elif mark == "narrowing":
        plate.draw.line((x, y - 124 * scale, x, y - 88 * scale), fill=color,
                        width=max(3, int(8 * scale)))
        plate.draw.line((x, y - 82 * scale, x, y - 55 * scale), fill=color,
                        width=max(1, int(3 * scale)))
    else:
        plate.draw.ellipse((x - 13 * scale, y - 13 * scale, x + 13 * scale, y + 13 * scale),
                           fill=color)


def _heart(plate: Plate, center: Point, scale: float, mark: str, color: str,
           *, context: str = "", label: str = "", variant: int = 0) -> None:
    x, y = center
    points = []
    for step in range(80):
        t = math.tau * step / 80
        px = 16 * math.sin(t) ** 3
        py = -(13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t))
        points.append((x + px * 6.0 * scale, y + py * 6.0 * scale))
    plate.draw.polygon(points, fill=hex_rgba(CORAL_LIGHT, 125), outline=CORAL)
    if mark == "none":
        return
    if context == "rad.5.congenital-ct" and label == "Situs":
        plate.text((x - 52 * scale, y + 98 * scale), "L", size=max(12, int(18 * scale)),
                   bold=True, fill=_text_tone(BLUE), anchor="mm")
        plate.text((x + 52 * scale, y + 98 * scale), "R", size=max(12, int(18 * scale)),
                   bold=True, fill=_text_tone(CORAL), anchor="mm")
        plate.draw.ellipse((x - 67 * scale, y + 45 * scale,
                            x - 34 * scale, y + 72 * scale), fill=BLUE_LIGHT, outline=BLUE)
        plate.draw.polygon(((x + 30 * scale, y + 44 * scale),
                            (x + 76 * scale, y + 44 * scale),
                            (x + 62 * scale, y + 76 * scale),
                            (x + 25 * scale, y + 70 * scale)),
                           fill=CORAL_LIGHT, outline=CORAL)
    elif context == "rad.5.congenital-ct" and label == "Connections":
        plate.arrow((x - 48 * scale, y - 8 * scale), (x - 10 * scale, y + 40 * scale),
                    fill=BLUE, width=max(2, int(5 * scale)), head=max(7, int(12 * scale)))
        plate.arrow((x + 48 * scale, y - 8 * scale), (x + 10 * scale, y + 40 * scale),
                    fill=CORAL, width=max(2, int(5 * scale)), head=max(7, int(12 * scale)))
    elif context == "rad.5.congenital-ct" and label == "Great vessels":
        plate.draw.arc((x - 18 * scale, y - 116 * scale,
                        x + 82 * scale, y - 22 * scale), 160, 350,
                       fill=CORAL, width=max(3, int(7 * scale)))
        plate.draw.line((x - 22 * scale, y - 76 * scale,
                         x - 70 * scale, y - 126 * scale), fill=BLUE,
                        width=max(3, int(7 * scale)))
        for dx in (-70, 0, 58):
            plate.draw.line((x + dx * scale, y - 105 * scale,
                             x + dx * scale, y - 139 * scale), fill=color,
                            width=max(2, int(4 * scale)))
    elif mark in {"enhancement", "oedema", "mass", "thrombus"}:
        plate.draw.ellipse((x + 12 * scale, y - 18 * scale, x + 48 * scale, y + 18 * scale),
                           fill=color, outline=INK, width=max(1, int(2 * scale)))
        if mark == "oedema":
            for radius in (28, 42):
                plate.draw.arc((x + (30 - radius) * scale, y - radius * scale,
                                x + (30 + radius) * scale, y + radius * scale),
                               200, 500, fill=color, width=max(1, int(3 * scale)))
        elif mark == "thrombus":
            # Broad-based avascular filling material at a chamber wall.
            plate.draw.line((x + 8 * scale, y + 18 * scale,
                             x + 50 * scale, y + 18 * scale), fill=INK_SOFT,
                            width=max(2, int(3 * scale)))
    elif mark in {"device", "lead"}:
        # Venous lead path with a curved distal tip in the right ventricle.
        path = ((x - 35 * scale, y - 122 * scale), (x - 25 * scale, y - 50 * scale),
                (x - 8 * scale, y + 20 * scale), (x + 28 * scale, y + 54 * scale))
        plate.polyline(path, fill=color, width=max(3, int(6 * scale)))
        plate.draw.arc((x + 4 * scale, y + 28 * scale,
                        x + 45 * scale, y + 69 * scale), 5, 170,
                       fill=color, width=max(2, int(4 * scale)))
    elif mark in {"strain", "dilation"}:
        plate.draw.ellipse((x - 74 * scale, y - 22 * scale, x - 18 * scale, y + 56 * scale),
                           outline=color, width=max(3, int(7 * scale)))


def _aortic_syndrome(plate: Plate, center: Point, scale: float,
                     mark: str, color: str) -> None:
    """Axial aortic-wall schematics for the three acute aortic syndromes."""
    x, y = center
    outer = (x - 88 * scale, y - 88 * scale, x + 88 * scale, y + 88 * scale)
    inner = (x - 59 * scale, y - 59 * scale, x + 59 * scale, y + 59 * scale)
    plate.draw.ellipse(outer, fill=hex_rgba(CORAL_LIGHT, 155), outline=CORAL,
                       width=max(3, int(6 * scale)))
    if mark == "aortic-intramural-haematoma":
        # Intramural haematoma is a crescent *within the wall*, not a luminal
        # thrombus.  The patent lumen remains separate.
        plate.draw.pieslice(outer, 88, 272, fill=hex_rgba(color, 210))
        plate.draw.ellipse((x - 48 * scale, y - 56 * scale,
                            x + 68 * scale, y + 56 * scale), fill=PAPER_LIGHT,
                           outline=INK_SOFT, width=max(2, int(3 * scale)))
        plate.text((x - 65 * scale, y), "wall", size=max(11, int(15 * scale)),
                   bold=True, fill=INK, anchor="mm")
        return
    plate.draw.ellipse(inner, fill=PAPER_LIGHT, outline=INK_SOFT,
                       width=max(2, int(3 * scale)))
    if mark == "aortic-dissection-flap":
        plate.draw.arc((x - 47 * scale, y - 62 * scale,
                        x + 44 * scale, y + 62 * scale), 275, 445,
                       fill=color, width=max(3, int(6 * scale)))
        plate.text((x - 25 * scale, y), "T", size=max(12, int(18 * scale)),
                   bold=True, fill=_text_tone(TEAL), anchor="mm")
        plate.text((x + 30 * scale, y), "F", size=max(12, int(18 * scale)),
                   bold=True, fill=_text_tone(color), anchor="mm")
    elif mark == "aortic-penetrating-ulcer":
        # A contrast-filled neck crosses the intimal contour into a focal wall
        # pouch; this is not drawn as an ordinary stenosing plaque.
        plate.draw.polygon(((x + 30 * scale, y - 47 * scale),
                            (x + 59 * scale, y - 70 * scale),
                            (x + 84 * scale, y - 53 * scale),
                            (x + 51 * scale, y - 25 * scale)),
                           fill=color, outline=_text_tone(color))
        plate.draw.line((x + 27 * scale, y - 45 * scale,
                         x + 58 * scale, y - 69 * scale), fill=PAPER_LIGHT,
                        width=max(2, int(3 * scale)))


def _vessel(plate: Plate, center: Point, scale: float, mark: str, color: str,
            *, context: str = "", label: str = "", variant: int = 0) -> None:
    if context == "rad.5.aorta":
        _aortic_syndrome(plate, center, scale, mark, color)
        return
    x, y = center
    plate.draw.rounded_rectangle((x - 122 * scale, y - 57 * scale,
                                  x + 122 * scale, y + 57 * scale),
                                 radius=int(52 * scale), fill=hex_rgba(CORAL_LIGHT, 90),
                                 outline=CORAL, width=max(2, int(4 * scale)))
    plate.draw.rounded_rectangle((x - 118 * scale, y - 28 * scale,
                                  x + 118 * scale, y + 28 * scale),
                                 radius=int(25 * scale), fill=hex_rgba(PAPER_LIGHT, 180))
    if mark == "biopsy-plan":
        plate.draw.line((x - 130 * scale, y - 104 * scale,
                         x + 115 * scale, y - 104 * scale), fill=color,
                        width=max(2, int(4 * scale)))
        plate.arrow((x + 110 * scale, y - 104 * scale),
                    (x + 110 * scale, y - 68 * scale), fill=color,
                    width=max(2, int(4 * scale)), head=max(7, int(12 * scale)))
        plate.draw.line((x - 5 * scale, y - 88 * scale,
                         x - 5 * scale, y - 65 * scale), fill=INK_SOFT,
                        width=max(2, int(3 * scale)))
    elif mark == "biopsy-guidance":
        plate.draw.line((x - 140 * scale, y - 92 * scale,
                         x + 8 * scale, y - 12 * scale), fill=color,
                        width=max(2, int(5 * scale)))
        plate.draw.ellipse((x - 2 * scale, y - 22 * scale,
                            x + 18 * scale, y - 2 * scale), fill=color, outline=INK)
        plate.draw.arc((x - 75 * scale, y - 78 * scale,
                        x + 42 * scale, y + 51 * scale), 305, 405,
                       fill=color, width=max(1, int(3 * scale)))
    elif ((mark == "biopsy-rescue") or
          (context == "rad.5.ir-basics" and label == "Check") or
          (context == "rad.5.coronary-ct" and label == "Report action")):
        plate.draw.ellipse((x + 38 * scale, y - 25 * scale,
                            x + 88 * scale, y + 25 * scale),
                           fill=GREEN_LIGHT, outline=GREEN,
                           width=max(2, int(4 * scale)))
        plate.draw.line((x + 49 * scale, y, x + 61 * scale, y + 12 * scale,
                         x + 81 * scale, y - 13 * scale), fill=_text_tone(GREEN),
                        width=max(2, int(5 * scale)), joint="curve")
    elif mark in {"clot", "embolus", "occlusion"}:
        plate.draw.ellipse((x - 25 * scale, y - 31 * scale,
                            x + 25 * scale, y + 31 * scale), fill=color)
    elif mark in {"stenosis", "plaque"}:
        plate.draw.polygon(((x - 35 * scale, y - 28 * scale),
                            (x + 35 * scale, y - 28 * scale),
                            (x + 14 * scale, y - 4 * scale),
                            (x - 14 * scale, y - 4 * scale)), fill=color)
    elif mark in {"dissection", "flap"}:
        plate.draw.line((x - 85 * scale, y - 13 * scale, x + 90 * scale, y + 12 * scale),
                        fill=color, width=max(3, int(6 * scale)))
    elif mark in {"bleed", "extravasation"}:
        plate.draw.ellipse((x + 86 * scale, y + 42 * scale,
                            x + 118 * scale, y + 76 * scale), fill=color)
    else:
        for shift in (-60, 0, 60):
            plate.arrow((x - 90 * scale + shift * scale, y),
                        (x - 45 * scale + shift * scale, y), fill=color,
                        width=max(2, int(5 * scale)), head=max(8, int(14 * scale)))


def _brain(plate: Plate, center: Point, scale: float, mark: str, color: str,
           *, context: str = "", label: str = "", variant: int = 0) -> None:
    x, y = center
    plate.draw.ellipse((x - 120 * scale, y - 95 * scale,
                        x + 120 * scale, y + 95 * scale),
                       fill=hex_rgba(PLUM_LIGHT, 85), outline=PLUM,
                       width=max(2, int(4 * scale)))
    plate.draw.line((x, y - 88 * scale, x, y + 82 * scale), fill=GRID,
                    width=max(2, int(3 * scale)))
    for dy in (-50, 0, 48):
        plate.draw.arc((x - 100 * scale, y + (dy - 28) * scale,
                        x + 100 * scale, y + (dy + 28) * scale), 5, 175,
                       fill=hex_rgba(PLUM, 105), width=max(1, int(3 * scale)))
    if mark == "none":
        return
    if context == "rad.5.intracranial-haemorrhage" and mark == "ich-extra-axial-shapes":
        # Show the two canonical extra-axial shapes side-by-side: an epidural
        # biconvex lens and a subdural crescent.
        plate.draw.ellipse((x - 105 * scale, y - 54 * scale,
                            x - 46 * scale, y + 54 * scale),
                           fill=hex_rgba(color, 205), outline=_text_tone(color))
        plate.draw.arc((x + 43 * scale, y - 76 * scale,
                        x + 112 * scale, y + 76 * scale), 86, 274,
                       fill=color, width=max(5, int(13 * scale)))
    elif context == "rad.5.intracranial-haemorrhage" and mark == "ich-intraparenchymal":
        # Irregular deep parenchymal blood with a short ventricular extension.
        plate.draw.polygon(((x + 8 * scale, y - 34 * scale),
                            (x + 50 * scale, y - 22 * scale),
                            (x + 62 * scale, y + 14 * scale),
                            (x + 36 * scale, y + 45 * scale),
                            (x - 2 * scale, y + 29 * scale),
                            (x - 10 * scale, y - 5 * scale)),
                           fill=hex_rgba(color, 215), outline=_text_tone(color))
        plate.draw.line((x + 5 * scale, y + 4 * scale,
                         x - 30 * scale, y + 38 * scale), fill=color,
                        width=max(3, int(7 * scale)))
    elif (context == "rad.5.intracranial-haemorrhage" and
          mark == "ich-subarachnoid-cisterns-sulci"):
        # Basal cistern and sulcal blood for subarachnoid haemorrhage.  The
        # former generic "venous dot" was anatomically misleading.
        for angle in range(0, 360, 60):
            radians = math.radians(angle)
            plate.draw.line((x, y, x + 58 * scale * math.cos(radians),
                             y + 43 * scale * math.sin(radians)),
                            fill=color, width=max(3, int(7 * scale)))
        for dx in (-62, 62):
            plate.draw.arc((x + (dx - 34) * scale, y - 68 * scale,
                            x + (dx + 34) * scale, y + 25 * scale), 210, 330,
                           fill=color, width=max(2, int(5 * scale)))
    elif context == "rad.5.brain-tumour" and label == "Characterise":
        plate.draw.ellipse((x + 18 * scale, y - 35 * scale,
                            x + 66 * scale, y + 13 * scale),
                           fill=hex_rgba(color, 155), outline=color,
                           width=max(2, int(4 * scale)))
        for radius in (32, 47):
            plate.draw.arc((x + (42 - radius) * scale, y + (-11 - radius) * scale,
                            x + (42 + radius) * scale, y + (-11 + radius) * scale),
                           15, 165, fill=color, width=max(1, int(3 * scale)))
    elif context == "rad.5.brain-tumour" and label == "Map effect":
        plate.draw.ellipse((x + 24 * scale, y - 38 * scale,
                            x + 76 * scale, y + 14 * scale), fill=color)
        plate.draw.line((x + 18 * scale, y - 80 * scale,
                         x + 18 * scale, y + 76 * scale), fill=_text_tone(color),
                        width=max(3, int(6 * scale)))
        plate.arrow((x - 2 * scale, y + 58 * scale),
                    (x + 16 * scale, y + 58 * scale), fill=color,
                    width=max(2, int(4 * scale)), head=max(7, int(11 * scale)))
    elif mark == "epilepsy-protocol":
        # Orthogonal thin-volume/hippocampal planes, not a fictitious focal
        # epileptogenic lesion.
        for dx, angle in ((-48, 0), (0, 90), (48, 35)):
            plate.draw.ellipse((x + (dx - 27) * scale, y - 42 * scale,
                                x + (dx + 27) * scale, y + 42 * scale),
                               outline=color, width=max(2, int(4 * scale)))
            radians = math.radians(angle)
            plate.draw.line((x + (dx - 25 * math.cos(radians)) * scale,
                             y - 25 * math.sin(radians) * scale,
                             x + (dx + 25 * math.cos(radians)) * scale,
                             y + 25 * math.sin(radians) * scale), fill=color,
                            width=max(2, int(4 * scale)))
    elif mark == "ms-brain-locations":
        for dx, dy, rx, ry in ((-14, -42, 19, 7), (52, -18, 17, 7),
                               (-72, 5, 14, 6), (18, 58, 16, 7)):
            plate.draw.ellipse((x + (dx - rx) * scale, y + (dy - ry) * scale,
                                x + (dx + rx) * scale, y + (dy + ry) * scale),
                               fill=hex_rgba(color, 175), outline=color)
    elif mark == "ms-cord-optic-nerve":
        # Optic nerves extend anteriorly; a separate short cord segment sits
        # below the posterior fossa.  Highlighting both avoids pretending they
        # are additional cerebral white-matter dots.
        plate.draw.line((x - 30 * scale, y - 27 * scale,
                         x - 92 * scale, y - 67 * scale), fill=color,
                        width=max(3, int(7 * scale)))
        plate.draw.line((x + 30 * scale, y - 27 * scale,
                         x + 92 * scale, y - 67 * scale), fill=color,
                        width=max(3, int(7 * scale)))
        plate.draw.rounded_rectangle((x - 13 * scale, y + 72 * scale,
                                      x + 13 * scale, y + 132 * scale),
                                     radius=max(3, int(6 * scale)), fill=PAPER_LIGHT,
                                     outline=INK_SOFT, width=max(2, int(3 * scale)))
        plate.draw.ellipse((x - 15 * scale, y + 91 * scale,
                            x + 15 * scale, y + 108 * scale), fill=color)
    elif mark == "ms-central-vein-sign":
        plate.draw.ellipse((x - 47 * scale, y - 34 * scale,
                            x + 47 * scale, y + 34 * scale),
                           fill=hex_rgba(color, 95), outline=color,
                           width=max(3, int(6 * scale)))
        plate.draw.line((x, y - 47 * scale, x, y + 47 * scale),
                        fill=_text_tone(PLUM), width=max(3, int(6 * scale)))
        plate.draw.arc((x - 58 * scale, y - 45 * scale,
                        x + 58 * scale, y + 45 * scale), 215, 500,
                       fill=INK_SOFT, width=max(2, int(4 * scale)))
    elif mark == "atrophy":
        plate.draw.line((x - 18 * scale, y - 62 * scale, x - 18 * scale, y + 62 * scale),
                        fill=color, width=max(3, int(7 * scale)))
        plate.draw.line((x + 18 * scale, y - 62 * scale, x + 18 * scale, y + 62 * scale),
                        fill=color, width=max(3, int(7 * scale)))
    elif mark == "csf":
        plate.draw.ellipse((x - 36 * scale, y - 18 * scale, x + 36 * scale, y + 36 * scale),
                           fill=hex_rgba(BLUE_LIGHT, 145), outline=BLUE)
    elif mark in {"territory", "infarct"}:
        # A cortical wedge follows a vascular territory rather than implying a
        # spherical lesion.
        plate.draw.polygon(((x - 8 * scale, y - 4 * scale),
                            (x - 105 * scale, y - 54 * scale),
                            (x - 91 * scale, y + 62 * scale)),
                           fill=hex_rgba(color, 150), outline=color)
    elif mark == "venous":
        plate.draw.arc((x - 94 * scale, y - 94 * scale,
                        x + 94 * scale, y - 28 * scale), 190, 350,
                       fill=color, width=max(4, int(9 * scale)))
        plate.draw.line((x, y - 89 * scale, x, y - 35 * scale), fill=color,
                        width=max(3, int(6 * scale)))
    elif mark == "white-matter":
        for dx, dy in ((-34, -35), (35, -29), (-45, 14), (46, 23), (14, 52)):
            plate.draw.ellipse((x + (dx - 14) * scale, y + (dy - 7) * scale,
                                x + (dx + 14) * scale, y + (dy + 7) * scale),
                               fill=hex_rgba(color, 175), outline=color)
    elif mark == "infection":
        plate.draw.ellipse((x - 42 * scale, y - 28 * scale,
                            x + 14 * scale, y + 28 * scale),
                           fill=PAPER_LIGHT, outline=color,
                           width=max(4, int(9 * scale)))
        plate.draw.ellipse((x - 27 * scale, y - 13 * scale,
                            x - 1 * scale, y + 13 * scale), fill=hex_rgba(color, 70))
    elif mark == "extra-axial":
        plate.draw.arc((x + 38 * scale, y - 76 * scale,
                        x + 113 * scale, y + 76 * scale), 85, 275,
                       fill=color, width=max(4, int(10 * scale)))
    elif mark == "trauma":
        for dx, dy in ((-76, 48), (70, -42)):
            plate.draw.ellipse((x + (dx - 18) * scale, y + (dy - 14) * scale,
                                x + (dx + 18) * scale, y + (dy + 14) * scale),
                               fill=hex_rgba(color, 180), outline=color)
    else:
        positions = {"mass": (52, -26), "epilepsy": (-68, 45)}
        dx, dy = positions.get(mark, (45, -12))
        plate.draw.ellipse((x + (dx - 22) * scale, y + (dy - 18) * scale,
                            x + (dx + 22) * scale, y + (dy + 18) * scale),
                           fill=hex_rgba(color, 170), outline=color,
                           width=max(2, int(3 * scale)))


def _kidney_shape(plate: Plate, center: Point, scale: float,
                  fill: str = PLUM_LIGHT, outline: str = PLUM) -> None:
    """Draw a bean-shaped kidney with a visible medial hilum."""
    x, y = center
    plate.draw.ellipse((x - 30 * scale, y - 47 * scale,
                        x + 30 * scale, y + 47 * scale),
                       fill=hex_rgba(fill, 150), outline=outline,
                       width=max(2, int(3 * scale)))
    plate.draw.ellipse((x + 8 * scale, y - 20 * scale,
                        x + 34 * scale, y + 20 * scale),
                       fill=PAPER_LIGHT, outline=outline,
                       width=max(1, int(2 * scale)))


def _abdomen(plate: Plate, center: Point, scale: float, mark: str, color: str,
             *, context: str = "", label: str = "", variant: int = 0) -> None:
    x, y = center
    plate.draw.rounded_rectangle((x - 108 * scale, y - 125 * scale,
                                  x + 108 * scale, y + 125 * scale),
                                 radius=int(62 * scale), fill=hex_rgba(GOLD_LIGHT, 55),
                                 outline=INK_SOFT, width=max(2, int(3 * scale)))
    pancreas_context = "pancreas" in context
    hepatobiliary_context = context in {
        "rad.4.liver", "rad.5.biliary", "rad.5.abdominal-trauma"
    }
    renal_context = context in {"rad.4.kidney", "rad.5.adrenal"}
    pelvic_context = context in {
        "rad.5.scrotum", "rad.5.bladder-virads", "rad.5.ovarian-orads",
        "rad.5.prostate-mri", "rad.5.rectal-mr", "rad.5.uterine-mr",
    }

    if pancreas_context:
        # Head in the duodenal curve, tapering body and tail toward the spleen.
        plate.draw.polygon(((x - 72 * scale, y - 16 * scale),
                            (x - 30 * scale, y - 30 * scale),
                            (x + 78 * scale, y - 16 * scale),
                            (x + 68 * scale, y + 15 * scale),
                            (x - 35 * scale, y + 23 * scale),
                            (x - 76 * scale, y + 8 * scale)),
                           fill=hex_rgba(GOLD_LIGHT, 180), outline=GOLD)
        plate.draw.arc((x - 105 * scale, y - 51 * scale,
                        x - 31 * scale, y + 56 * scale), 270, 450,
                       fill=TEAL, width=max(2, int(5 * scale)))
        if mark == "pancreas-severity":
            for radius in (4, 8, 12):
                plate.draw.ellipse((x - (radius + 2) * scale, y - radius * scale,
                                    x + (radius + 2) * scale, y + radius * scale),
                                   outline=color, width=max(1, int(2 * scale)))
            plate.draw.arc((x - 91 * scale, y - 46 * scale,
                            x + 91 * scale, y + 53 * scale), 5, 175,
                           fill=color, width=max(2, int(5 * scale)))
        elif mark == "pancreas-collection":
            plate.draw.rounded_rectangle((x + 20 * scale, y + 28 * scale,
                                          x + 84 * scale, y + 84 * scale),
                                         radius=max(7, int(14 * scale)),
                                         fill=hex_rgba(BLUE_LIGHT, 145), outline=BLUE,
                                         width=max(2, int(4 * scale)))
            plate.draw.arc((x + 15 * scale, y + 21 * scale,
                            x + 90 * scale, y + 90 * scale), 5, 175,
                           fill=color, width=max(2, int(4 * scale)))
        elif mark == "pancreas-complication":
            plate.draw.line((x - 85 * scale, y + 43 * scale,
                             x + 84 * scale, y + 43 * scale), fill=CORAL,
                            width=max(3, int(7 * scale)))
            plate.draw.ellipse((x + 22 * scale, y + 26 * scale,
                                x + 56 * scale, y + 60 * scale),
                               outline=color, width=max(3, int(6 * scale)))
            for dx, dy in ((-34, 58), (-14, 72), (8, 60)):
                plate.draw.ellipse((x + (dx - 4) * scale, y + (dy - 4) * scale,
                                    x + (dx + 4) * scale, y + (dy + 4) * scale),
                                   fill=INK_SOFT)
        elif mark == "pancreas-protocol":
            for index, opacity in enumerate((55, 130, 210)):
                cx = x - 35 * scale + index * 35 * scale
                plate.draw.ellipse((cx - 10 * scale, y - 87 * scale,
                                    cx + 10 * scale, y - 67 * scale),
                                   fill=hex_rgba(color, opacity), outline=_text_tone(color))
        elif mark == "pancreas-vessel-contact":
            plate.draw.line((x - 5 * scale, y - 88 * scale,
                             x - 5 * scale, y + 88 * scale), fill=CORAL,
                            width=max(3, int(7 * scale)))
            plate.draw.arc((x - 39 * scale, y - 37 * scale,
                            x + 28 * scale, y + 37 * scale), 275, 445,
                           fill=color, width=max(3, int(7 * scale)))
        elif mark == "pancreas-lesion-types":
            plate.draw.ellipse((x - 45 * scale, y - 10 * scale,
                                x - 13 * scale, y + 22 * scale),
                               fill=hex_rgba(BLUE_LIGHT, 155), outline=BLUE)
            plate.draw.ellipse((x + 15 * scale, y - 10 * scale,
                                x + 47 * scale, y + 22 * scale),
                               fill=color, outline=_text_tone(color))
    elif hepatobiliary_context:
        # Liver in the right upper abdomen (viewer left), gallbladder inferior,
        # spleen contralateral.  This replaces the old unlabelled central oval.
        plate.draw.polygon(((x - 91 * scale, y - 77 * scale),
                            (x + 30 * scale, y - 68 * scale),
                            (x + 17 * scale, y + 2 * scale),
                            (x - 80 * scale, y + 12 * scale)),
                           fill=hex_rgba(CORAL_LIGHT, 155), outline=CORAL)
        plate.draw.ellipse((x - 27 * scale, y - 2 * scale,
                            x - 7 * scale, y + 39 * scale),
                           fill=TEAL_LIGHT, outline=TEAL)
        plate.draw.ellipse((x + 59 * scale, y - 60 * scale,
                            x + 88 * scale, y - 2 * scale),
                           fill=hex_rgba(PLUM_LIGHT, 150), outline=PLUM)
        if mark == "lesion":
            plate.draw.ellipse((x - 53 * scale, y - 48 * scale,
                                x - 23 * scale, y - 18 * scale),
                               fill=hex_rgba(color, 195), outline=_text_tone(color))
        elif mark == "biliary-stones":
            for dy in (18, 27, 34):
                plate.draw.ellipse((x - 23 * scale, y + (dy - 4) * scale,
                                    x - 15 * scale, y + (dy + 4) * scale), fill=color)
        elif mark == "biliary-obstruction":
            plate.draw.line((x - 17 * scale, y - 33 * scale,
                             x - 17 * scale, y + 78 * scale), fill=color,
                            width=max(4, int(9 * scale)))
            plate.draw.line((x - 52 * scale, y - 12 * scale,
                             x - 17 * scale, y + 9 * scale,
                             x + 18 * scale, y - 12 * scale), fill=color,
                            width=max(3, int(7 * scale)), joint="curve")
            plate.draw.line((x - 27 * scale, y + 43 * scale,
                             x - 7 * scale, y + 43 * scale), fill=PAPER_LIGHT,
                            width=max(3, int(7 * scale)))
        elif mark == "biliary-inflammation":
            plate.draw.ellipse((x - 34 * scale, y - 9 * scale,
                                x, y + 46 * scale),
                               outline=color, width=max(4, int(8 * scale)))
    elif renal_context:
        _kidney_shape(plate, (x - 52 * scale, y - 8 * scale), scale)
        _kidney_shape(plate, (x + 52 * scale, y - 8 * scale), scale)
        if mark in {"adrenal", "adrenal-ct", "adrenal-chemical-shift", "adrenal-washout"}:
            plate.draw.polygon(((x + 30 * scale, y - 62 * scale),
                                (x + 72 * scale, y - 66 * scale),
                                (x + 54 * scale, y - 93 * scale)),
                               fill=color, outline=_text_tone(color))
            if mark == "adrenal-chemical-shift":
                for dx, opacity in ((-15, 190), (15, 55)):
                    plate.draw.ellipse((x + (54 + dx - 9) * scale, y - 118 * scale,
                                        x + (54 + dx + 9) * scale, y - 100 * scale),
                                       fill=hex_rgba(color, opacity), outline=_text_tone(color))
            elif mark == "adrenal-washout":
                plate.polyline(((x + 23 * scale, y - 106 * scale),
                                (x + 50 * scale, y - 126 * scale),
                                (x + 84 * scale, y - 105 * scale)),
                               fill=color, width=max(2, int(4 * scale)))
        elif mark in {"renal-baseline", "renal-enhancement", "renal-cystic-mass"}:
            if mark == "renal-baseline":
                plate.draw.ellipse((x + 34 * scale, y - 26 * scale,
                                    x + 59 * scale, y - 1 * scale),
                                   fill=hex_rgba(color, 65), outline=color)
            elif mark == "renal-enhancement":
                for dx, opacity in ((34, 65), (65, 205)):
                    plate.draw.ellipse((x + (dx - 11) * scale, y - 25 * scale,
                                        x + (dx + 11) * scale, y - 3 * scale),
                                       fill=hex_rgba(color, opacity), outline=_text_tone(color))
            else:
                plate.draw.ellipse((x + 26 * scale, y - 34 * scale,
                                    x + 78 * scale, y + 18 * scale),
                                   fill=hex_rgba(BLUE_LIGHT, 145), outline=color,
                                   width=max(2, int(4 * scale)))
                plate.draw.line((x + 51 * scale, y - 32 * scale,
                                 x + 51 * scale, y + 17 * scale), fill=color,
                                width=max(2, int(4 * scale)))
                plate.draw.ellipse((x + 63 * scale, y - 6 * scale,
                                    x + 77 * scale, y + 8 * scale), fill=color)
        elif mark == "lesion":
            plate.draw.ellipse((x + 39 * scale, y - 27 * scale,
                                x + 63 * scale, y - 3 * scale), fill=color)
    elif pelvic_context:
        # Select the named pelvic structure instead of reusing one blue oval
        # for bladder, uterus, ovaries, prostate and rectum.
        if context == "rad.5.scrotum":
            plate.draw.arc((x - 62 * scale, y + 8 * scale,
                            x + 62 * scale, y + 119 * scale), 0, 180,
                           fill=INK_SOFT, width=max(2, int(4 * scale)))
            for dx in (-27, 27):
                plate.draw.ellipse((x + (dx - 22) * scale, y + 43 * scale,
                                    x + (dx + 22) * scale, y + 91 * scale),
                                   fill=hex_rgba(GOLD_LIGHT, 160), outline=GOLD)
            if mark == "testis-perfusion":
                for dy in (51, 63, 75):
                    plate.arrow((x - 42 * scale, y + dy * scale),
                                (x - 12 * scale, y + dy * scale), fill=color,
                                width=max(1, int(3 * scale)), head=max(5, int(8 * scale)))
            elif mark == "testis-mass-location":
                plate.draw.ellipse((x + 15 * scale, y + 52 * scale,
                                    x + 39 * scale, y + 76 * scale), fill=color)
            elif mark == "testis-staging":
                plate.arrow((x + 28 * scale, y + 42 * scale),
                            (x + 72 * scale, y + 5 * scale), fill=color,
                            width=max(2, int(4 * scale)), head=max(7, int(11 * scale)))
        elif context == "rad.5.prostate-mri":
            plate.draw.ellipse((x - 42 * scale, y - 24 * scale,
                                x + 42 * scale, y + 37 * scale),
                               fill=hex_rgba(PLUM_LIGHT, 165), outline=PLUM)
            plate.draw.ellipse((x - 18 * scale, y - 11 * scale,
                                x + 18 * scale, y + 25 * scale),
                               fill=PAPER_LIGHT, outline=GRID)
            if mark in {"prostate", "prostate-peripheral"}:
                plate.draw.arc((x - 39 * scale, y - 21 * scale,
                                x + 39 * scale, y + 34 * scale), 80, 280,
                               fill=color, width=max(3, int(6 * scale)))
            elif mark == "prostate-transition":
                plate.draw.ellipse((x - 17 * scale, y - 10 * scale,
                                    x + 17 * scale, y + 24 * scale),
                                   outline=color, width=max(3, int(6 * scale)))
            elif mark == "prostate-stage-target":
                plate.draw.ellipse((x + 20 * scale, y - 4 * scale,
                                    x + 43 * scale, y + 19 * scale), fill=color)
                plate.arrow((x + 89 * scale, y - 62 * scale),
                            (x + 44 * scale, y - 2 * scale), fill=color,
                            width=max(2, int(4 * scale)), head=max(7, int(11 * scale)))
        elif context == "rad.5.bladder-virads":
            plate.draw.ellipse((x - 57 * scale, y + 6 * scale,
                                x + 57 * scale, y + 86 * scale),
                               fill=hex_rgba(BLUE_LIGHT, 125), outline=BLUE,
                               width=max(2, int(4 * scale)))
            if mark in {"bladder", "phase", "bladder-t2", "bladder-dwi-enhancement"}:
                plate.draw.arc((x - 52 * scale, y + 12 * scale,
                                x + 52 * scale, y + 80 * scale), 300, 415,
                               fill=color, width=max(3, int(7 * scale)))
                if mark == "bladder-dwi-enhancement":
                    plate.draw.line((x + 24 * scale, y + 19 * scale,
                                     x + 42 * scale, y + 53 * scale), fill=color,
                                    width=max(4, int(8 * scale)))
            elif mark == "bladder-virads":
                plate.draw.line((x + 62 * scale, y + 52 * scale,
                                 x + 76 * scale, y + 66 * scale,
                                 x + 98 * scale, y + 35 * scale),
                                fill=_text_tone(GREEN), width=max(3, int(7 * scale)),
                                joint="curve")
        else:
            # Uterus with endometrial cavity and paired ovaries.
            plate.draw.polygon(((x, y + 63 * scale),
                                (x - 37 * scale, y + 4 * scale),
                                (x - 28 * scale, y - 35 * scale),
                                (x + 28 * scale, y - 35 * scale),
                                (x + 37 * scale, y + 4 * scale)),
                               fill=hex_rgba(CORAL_LIGHT, 145), outline=CORAL)
            plate.draw.line((x, y - 26 * scale, x, y + 44 * scale),
                            fill=PAPER_LIGHT, width=max(2, int(4 * scale)))
            for dx in (-64, 64):
                plate.draw.line((x + (28 if dx > 0 else -28) * scale, y - 24 * scale,
                                 x + dx * scale, y - 14 * scale), fill=CORAL,
                                width=max(2, int(3 * scale)))
                plate.draw.ellipse((x + (dx - 15) * scale, y - 29 * scale,
                                    x + (dx + 15) * scale, y + 1 * scale),
                                   fill=hex_rgba(GOLD_LIGHT, 165), outline=GOLD)
            if context == "rad.5.ovarian-orads" and mark in {
                    "ovary-morphology", "ovary-solid-tissue"}:
                plate.draw.ellipse((x + 47 * scale, y - 35 * scale,
                                    x + 82 * scale, y + 3 * scale),
                                   outline=color, width=max(3, int(6 * scale)))
                if mark == "ovary-morphology":
                    plate.draw.line((x + 64 * scale, y - 33 * scale,
                                     x + 64 * scale, y + 1 * scale), fill=color,
                                    width=max(2, int(4 * scale)))
                else:
                    plate.draw.ellipse((x + 61 * scale, y - 18 * scale,
                                        x + 78 * scale, y - 1 * scale), fill=color)
            elif context == "rad.5.ovarian-orads" and mark == "ovary-action":
                plate.draw.line((x + 55 * scale, y + 34 * scale,
                                 x + 68 * scale, y + 47 * scale,
                                 x + 92 * scale, y + 17 * scale),
                                fill=_text_tone(GREEN), width=max(3, int(7 * scale)),
                                joint="curve")
    else:
        # Bowel is drawn as continuous loops.  Marks alter the wall/lumen
        # relationship rather than dropping an unrelated organ-shaped blob.
        for offset in (-45, 0, 45):
            plate.draw.arc((x - 74 * scale, y + (offset - 27) * scale,
                            x + 74 * scale, y + (offset + 27) * scale), 0, 180,
                           fill=color if offset == 0 else TEAL,
                           width=max(3, int(7 * scale)))
            plate.draw.arc((x - 74 * scale, y + (offset - 8) * scale,
                            x + 74 * scale, y + (offset + 46) * scale), 180, 360,
                           fill=color if offset == 0 else TEAL,
                           width=max(3, int(7 * scale)))
        if mark == "appendix":
            plate.draw.line((x + 58 * scale, y + 46 * scale,
                             x + 84 * scale, y + 91 * scale),
                            fill=color, width=max(3, int(7 * scale)))
            if label == "Combine signs":
                for angle in (-40, 0, 40):
                    radians = math.radians(angle)
                    plate.draw.line((x + 82 * scale, y + 89 * scale,
                                     x + (82 + 26 * math.cos(radians)) * scale,
                                     y + (89 + 26 * math.sin(radians)) * scale),
                                    fill=color, width=max(1, int(3 * scale)))
        elif mark in {"obstruction", "ischaemia"}:
            plate.draw.ellipse((x - 68 * scale, y - 22 * scale,
                                x + 68 * scale, y + 26 * scale),
                               outline=color, width=max(3, int(7 * scale)))
            if mark == "obstruction":
                plate.draw.line((x - 4 * scale, y - 25 * scale,
                                 x + 12 * scale, y + 28 * scale), fill=color,
                                width=max(3, int(6 * scale)))

        if context == "rad.3.acute-abdomen" and mark == "phase":
            # Free intraperitoneal gas as a subdiaphragmatic crescent.
            plate.draw.arc((x - 86 * scale, y - 111 * scale,
                            x + 86 * scale, y - 59 * scale), 195, 345,
                           fill=color, width=max(4, int(8 * scale)))
        elif context == "rad.5.ibd" and mark == "ibd":
            plate.draw.arc((x - 76 * scale, y - 31 * scale,
                            x + 76 * scale, y + 31 * scale), 0, 180,
                           fill=color, width=max(5, int(11 * scale)))
        elif context == "rad.5.ibd" and mark == "bowel":
            plate.draw.line((x + 44 * scale, y + 21 * scale,
                             x + 92 * scale, y + 79 * scale), fill=color,
                            width=max(3, int(6 * scale)))
            plate.draw.ellipse((x + 74 * scale, y + 61 * scale,
                                x + 108 * scale, y + 95 * scale),
                               outline=color, width=max(3, int(6 * scale)))
        elif context == "rad.5.paeds-abdomen":
            if mark == "paeds-abdomen-radiograph":
                for dx, dy in ((-48, -32), (20, -8), (-12, 43)):
                    plate.draw.ellipse((x + (dx - 11) * scale, y + (dy - 11) * scale,
                                        x + (dx + 11) * scale, y + (dy + 11) * scale),
                                       outline=color, width=max(2, int(4 * scale)))
                plate.draw.arc((x - 79 * scale, y - 109 * scale,
                                x + 79 * scale, y - 63 * scale), 195, 345,
                               fill=color, width=max(3, int(6 * scale)))
            elif mark == "paeds-abdomen-ultrasound":
                plate.draw.polygon(((x - 93 * scale, y - 96 * scale),
                                    (x - 43 * scale, y - 80 * scale),
                                    (x - 49 * scale, y - 44 * scale),
                                    (x - 99 * scale, y - 60 * scale)), fill=color)
                for radius in (30, 52, 74):
                    plate.draw.arc((x + (-40 - radius) * scale,
                                    y + (-62 - radius) * scale,
                                    x + (-40 + radius) * scale,
                                    y + (-62 + radius) * scale),
                                   310, 410, fill=color, width=max(1, int(3 * scale)))
            elif mark == "paeds-abdomen-surgical-red-flags":
                plate.draw.polygon(((x, y - 104 * scale),
                                    (x - 84 * scale, y + 84 * scale),
                                    (x + 84 * scale, y + 84 * scale)),
                                   outline=color)
                plate.text((x, y + 27 * scale), "!", size=max(18, int(34 * scale)),
                           bold=True, fill=_text_tone(color), anchor="mm")

    if (mark == "phase" and context != "rad.3.acute-abdomen" and
            not (context == "rad.5.abdominal-trauma" and label == "Route treatment")):
        # Three time points indicate dynamic enhancement.  They are separate
        # from the organ drawing so "phase" is never mistaken for a lesion.
        for index, opacity in enumerate((55, 120, 205)):
            cx = x - 32 * scale + index * 32 * scale
            plate.draw.ellipse((cx - 9 * scale, y - 111 * scale,
                                cx + 9 * scale, y - 93 * scale),
                               fill=hex_rgba(color, opacity), outline=_text_tone(color))
    elif context == "rad.5.abdominal-trauma" and label == "Route treatment":
        plate.arrow((x - 15 * scale, y + 55 * scale),
                    (x + 72 * scale, y + 91 * scale), fill=color,
                    width=max(3, int(6 * scale)), head=max(9, int(15 * scale)))
        plate.draw.line((x + 61 * scale, y + 73 * scale,
                         x + 72 * scale, y + 84 * scale,
                         x + 96 * scale, y + 54 * scale),
                        fill=_text_tone(GREEN), width=max(3, int(6 * scale)),
                        joint="curve")


def _long_bone(plate: Plate, center: Point, scale: float,
               fill: str = GOLD_LIGHT, outline: str = GOLD) -> None:
    x, y = center
    plate.draw.rounded_rectangle((x - 22 * scale, y - 90 * scale,
                                  x + 22 * scale, y + 90 * scale),
                                 radius=max(8, int(18 * scale)), fill=fill,
                                 outline=outline, width=max(2, int(4 * scale)))
    for dy in (-92, 92):
        plate.draw.ellipse((x - 43 * scale, y + (dy - 28) * scale,
                            x + 43 * scale, y + (dy + 28) * scale),
                           fill=fill, outline=outline,
                           width=max(2, int(4 * scale)))


def _knee_joint(plate: Plate, center: Point, scale: float,
                mark: str, color: str, label: str) -> None:
    x, y = center
    plate.draw.line((x - 34 * scale, y - 116 * scale,
                     x - 20 * scale, y - 28 * scale), fill=GOLD_LIGHT,
                    width=max(10, int(26 * scale)))
    plate.draw.line((x + 34 * scale, y - 116 * scale,
                     x + 20 * scale, y - 28 * scale), fill=GOLD_LIGHT,
                    width=max(10, int(26 * scale)))
    for dx in (-28, 28):
        plate.draw.ellipse((x + (dx - 28) * scale, y - 48 * scale,
                            x + (dx + 28) * scale, y + 8 * scale),
                           fill=GOLD_LIGHT, outline=GOLD)
    plate.draw.rounded_rectangle((x - 56 * scale, y + 26 * scale,
                                  x + 56 * scale, y + 62 * scale),
                                 radius=max(4, int(8 * scale)), fill=GOLD_LIGHT,
                                 outline=GOLD, width=max(2, int(3 * scale)))
    plate.draw.line((x - 24 * scale, y + 60 * scale,
                     x - 18 * scale, y + 122 * scale), fill=GOLD_LIGHT,
                    width=max(10, int(24 * scale)))
    plate.draw.line((x + 24 * scale, y + 60 * scale,
                     x + 18 * scale, y + 122 * scale), fill=GOLD_LIGHT,
                    width=max(10, int(24 * scale)))
    if mark in {"knee-meniscus", "joint"}:
        plate.draw.polygon(((x - 49 * scale, y + 10 * scale),
                            (x - 5 * scale, y + 22 * scale),
                            (x - 45 * scale, y + 26 * scale)), fill=color)
    elif mark == "knee-ligament":
        plate.draw.line((x - 30 * scale, y - 14 * scale,
                         x + 30 * scale, y + 47 * scale), fill=color,
                        width=max(3, int(6 * scale)))
        plate.draw.line((x + 30 * scale, y - 14 * scale,
                         x - 30 * scale, y + 47 * scale), fill=TEAL,
                        width=max(3, int(6 * scale)))
    elif mark in {"knee-cartilage", "cartilage"}:
        plate.draw.arc((x - 56 * scale, y - 43 * scale,
                        x + 56 * scale, y + 16 * scale), 5, 175,
                       fill=color, width=max(3, int(7 * scale)))


def _hip_joint(plate: Plate, center: Point, scale: float,
               mark: str, color: str, label: str) -> None:
    x, y = center
    plate.draw.arc((x - 92 * scale, y - 104 * scale,
                    x + 44 * scale, y + 45 * scale), 265, 455,
                   fill=GOLD, width=max(10, int(23 * scale)))
    plate.draw.ellipse((x - 42 * scale, y - 28 * scale,
                        x + 38 * scale, y + 52 * scale),
                       fill=GOLD_LIGHT, outline=GOLD,
                       width=max(2, int(4 * scale)))
    plate.draw.line((x + 13 * scale, y + 42 * scale,
                     x + 75 * scale, y + 125 * scale), fill=GOLD_LIGHT,
                    width=max(12, int(29 * scale)))
    if ("Infant" in label or "Shape" in label or
            mark in {"joint", "hip-coverage", "infant-hip-ultrasound", "older-hip-lines"}):
        plate.draw.arc((x - 47 * scale, y - 35 * scale,
                        x + 45 * scale, y + 58 * scale), 185, 410,
                       fill=color, width=max(3, int(7 * scale)))
    elif mark in {"lesion", "hip-osteonecrosis"}:
        plate.draw.arc((x - 30 * scale, y - 17 * scale,
                        x + 26 * scale, y + 39 * scale), 25, 320,
                       fill=color, width=max(3, int(7 * scale)))
    else:
        plate.draw.line((x + 24 * scale, y + 40 * scale,
                         x + 82 * scale, y + 121 * scale), fill=color,
                        width=max(3, int(7 * scale)))


def _shoulder_joint(plate: Plate, center: Point, scale: float,
                    mark: str, color: str, label: str) -> None:
    x, y = center
    plate.draw.arc((x - 92 * scale, y - 65 * scale,
                    x - 13 * scale, y + 70 * scale), 275, 445,
                   fill=GOLD, width=max(8, int(20 * scale)))
    plate.draw.ellipse((x - 8 * scale, y - 45 * scale,
                        x + 72 * scale, y + 35 * scale),
                       fill=GOLD_LIGHT, outline=GOLD)
    plate.draw.line((x + 55 * scale, y + 18 * scale,
                     x + 75 * scale, y + 125 * scale), fill=GOLD_LIGHT,
                    width=max(12, int(28 * scale)))
    if mark in {"shoulder-cuff", "joint"}:
        plate.draw.arc((x - 26 * scale, y - 85 * scale,
                        x + 86 * scale, y + 27 * scale), 190, 335,
                       fill=color, width=max(3, int(7 * scale)))
    elif mark in {"shoulder-labrum", "cartilage"}:
        plate.draw.arc((x - 31 * scale, y - 53 * scale,
                        x + 5 * scale, y + 45 * scale), 265, 95,
                       fill=color, width=max(3, int(7 * scale)))
    else:
        plate.arrow((x + 32 * scale, y - 4 * scale),
                    (x + 91 * scale, y - 45 * scale), fill=color,
                    width=max(3, int(6 * scale)), head=max(9, int(15 * scale)))


def _bone(plate: Plate, center: Point, scale: float, mark: str, color: str,
          *, context: str = "", label: str = "", variant: int = 0) -> None:
    x, y = center
    if context == "rad.4.spine-imaging":
        for offset in (-66, -22, 22, 66):
            plate.draw.rounded_rectangle((x - 61 * scale, y + (offset - 17) * scale,
                                          x + 61 * scale, y + (offset + 17) * scale),
                                         radius=max(4, int(7 * scale)), fill=GOLD_LIGHT,
                                         outline=GOLD, width=max(2, int(3 * scale)))
        if mark == "spine-disc":
            plate.draw.line((x - 55 * scale, y - 43 * scale,
                             x + 55 * scale, y - 43 * scale), fill=color,
                            width=max(3, int(7 * scale)))
        elif mark == "spine-compression":
            plate.draw.ellipse((x - 72 * scale, y - 11 * scale,
                                x - 39 * scale, y + 22 * scale), fill=color)
        else:
            plate.draw.line((x - 56 * scale, y + 8 * scale,
                             x + 50 * scale, y + 37 * scale), fill=color,
                            width=max(3, int(7 * scale)))
    elif context == "rad.5.knee":
        _knee_joint(plate, center, scale, mark, color, label)
    elif context == "rad.5.shoulder":
        _shoulder_joint(plate, center, scale, mark, color, label)
    elif context in {"rad.5.hip", "rad.5.paeds-hip-elbow"} and "elbow" not in label.lower():
        _hip_joint(plate, center, scale, mark, color, label)
    elif context == "rad.5.paeds-hip-elbow" and mark == "child-elbow-lines":
        # Distal humeral ossification/alignment schematic.
        plate.draw.line((x, y - 116 * scale, x, y - 8 * scale), fill=GOLD_LIGHT,
                        width=max(12, int(28 * scale)))
        plate.draw.ellipse((x - 45 * scale, y - 28 * scale,
                            x + 45 * scale, y + 36 * scale), fill=GOLD_LIGHT,
                           outline=GOLD)
        plate.draw.line((x - 23 * scale, y + 30 * scale,
                         x - 55 * scale, y + 120 * scale), fill=GOLD_LIGHT,
                        width=max(10, int(23 * scale)))
        plate.draw.line((x + 23 * scale, y + 30 * scale,
                         x + 55 * scale, y + 120 * scale), fill=GOLD_LIGHT,
                        width=max(10, int(23 * scale)))
        plate.draw.line((x - 70 * scale, y - 18 * scale,
                         x + 70 * scale, y + 35 * scale), fill=color,
                        width=max(3, int(6 * scale)))
    elif context == "rad.5.wrist-hand":
        plate.draw.line((x - 28 * scale, y + 119 * scale,
                         x - 18 * scale, y + 48 * scale), fill=GOLD_LIGHT,
                        width=max(10, int(23 * scale)))
        plate.draw.line((x + 28 * scale, y + 119 * scale,
                         x + 18 * scale, y + 48 * scale), fill=GOLD_LIGHT,
                        width=max(10, int(23 * scale)))
        for row in range(2):
            for col in range(4):
                cx = x - 39 * scale + col * 26 * scale
                cy = y + 24 * scale - row * 25 * scale
                plate.draw.ellipse((cx - 10 * scale, cy - 9 * scale,
                                    cx + 10 * scale, cy + 9 * scale),
                                   fill=GOLD_LIGHT, outline=GOLD)
        for col in range(5):
            cx = x - 52 * scale + col * 26 * scale
            plate.draw.line((cx, y - 2 * scale, cx - 5 * scale, y - 103 * scale),
                            fill=GOLD_LIGHT, width=max(6, int(13 * scale)))
        if mark in {"wrist-occult-fracture", "wrist-instability"}:
            plate.draw.line((x - 40 * scale, y + 50 * scale,
                             x - 7 * scale, y + 76 * scale), fill=color,
                            width=max(3, int(6 * scale)))
        else:
            plate.draw.arc((x - 70 * scale, y - 7 * scale,
                            x + 70 * scale, y + 62 * scale), 10, 170,
                           fill=color, width=max(3, int(6 * scale)))
    elif context == "rad.5.ankle-foot":
        plate.draw.line((x - 32 * scale, y - 120 * scale,
                         x - 25 * scale, y + 10 * scale), fill=GOLD_LIGHT,
                        width=max(12, int(28 * scale)))
        plate.draw.ellipse((x - 55 * scale, y - 5 * scale,
                            x + 20 * scale, y + 62 * scale), fill=GOLD_LIGHT,
                           outline=GOLD)
        for index in range(5):
            plate.draw.line((x - 22 * scale, y + 53 * scale,
                             x + (22 + index * 18) * scale, y + (71 + index * 7) * scale),
                            fill=GOLD_LIGHT, width=max(6, int(13 * scale)))
        if mark in {"ankle-stability", "midfoot-occult"}:
            plate.draw.line((x - 47 * scale, y + 18 * scale,
                             x - 5 * scale, y + 43 * scale), fill=color,
                            width=max(3, int(6 * scale)))
        else:
            plate.draw.arc((x - 60 * scale, y - 9 * scale,
                            x + 25 * scale, y + 66 * scale), 10, 175,
                           fill=color, width=max(3, int(6 * scale)))
    elif context == "rad.4.arthritis":
        _knee_joint(plate, center, scale, "joint", GRID, label)
        if label == "Degenerative":
            plate.draw.line((x - 53 * scale, y + 14 * scale,
                             x + 5 * scale, y + 14 * scale), fill=color,
                            width=max(4, int(9 * scale)))
            plate.draw.polygon(((x + 52 * scale, y + 22 * scale),
                                (x + 82 * scale, y + 32 * scale),
                                (x + 54 * scale, y + 42 * scale)), fill=color)
        elif label == "Inflammatory":
            plate.draw.arc((x - 62 * scale, y - 36 * scale,
                            x + 62 * scale, y + 58 * scale), 5, 175,
                           fill=color, width=max(5, int(11 * scale)))
        else:
            for dx in (-39, -15, 14, 40):
                plate.draw.ellipse((x + (dx - 6) * scale, y + 8 * scale,
                                    x + (dx + 6) * scale, y + 20 * scale), fill=color)
    else:
        _long_bone(plate, center, scale)
        if context == "rad.5.bone-tumours" and label == "Protect the pathway":
            plate.draw.ellipse((x - 28 * scale, y - 24 * scale,
                                x + 28 * scale, y + 24 * scale),
                               fill=hex_rgba(color, 150), outline=color)
            plate.arrow((x + 38 * scale, y + 3 * scale),
                        (x + 91 * scale, y + 58 * scale), fill=color,
                        width=max(3, int(6 * scale)), head=max(9, int(15 * scale)))
            plate.draw.line((x + 56 * scale, y - 56 * scale,
                             x + 94 * scale, y - 18 * scale), fill=CORAL,
                            width=max(3, int(7 * scale)))
            plate.draw.line((x + 94 * scale, y - 56 * scale,
                             x + 56 * scale, y - 18 * scale), fill=CORAL,
                            width=max(3, int(7 * scale)))
        elif mark in {"fracture", "trauma", "stress"}:
            plate.draw.line((x - 24 * scale, y - 18 * scale,
                             x + 24 * scale, y + 18 * scale), fill=color,
                            width=max(3, int(8 * scale)))
            plate.draw.line((x - 14 * scale, y - 30 * scale,
                             x + 22 * scale, y + 2 * scale), fill=color,
                            width=max(2, int(5 * scale)))
        elif mark in {"lesion", "tumour", "marrow"}:
            if mark == "marrow":
                plate.draw.rounded_rectangle((x - 10 * scale, y - 68 * scale,
                                              x + 10 * scale, y + 68 * scale),
                                             radius=max(3, int(6 * scale)), fill=color)
            elif mark == "tumour":
                plate.draw.polygon(((x - 29 * scale, y - 40 * scale),
                                    (x + 24 * scale, y - 29 * scale),
                                    (x + 35 * scale, y + 17 * scale),
                                    (x - 17 * scale, y + 37 * scale),
                                    (x - 34 * scale, y + 3 * scale)),
                                   fill=hex_rgba(color, 175), outline=color)
                for dy in (-31, -8, 18, 35):
                    plate.draw.line((x + 26 * scale, y + dy * scale,
                                     x + 57 * scale, y + (dy + 12) * scale),
                                    fill=color, width=max(1, int(3 * scale)))
            else:
                plate.draw.ellipse((x - 28 * scale, y - 24 * scale,
                                    x + 28 * scale, y + 24 * scale),
                                   fill=hex_rgba(color, 175), outline=color)
        elif mark in {"joint", "arthritis", "cartilage"}:
            plate.draw.line((x - 43 * scale, y, x + 43 * scale, y),
                            fill=PAPER_LIGHT, width=max(4, int(10 * scale)))
            plate.draw.arc((x - 52 * scale, y - 52 * scale,
                            x + 52 * scale, y + 52 * scale), 20, 160,
                           fill=color, width=max(3, int(7 * scale)))


def _head_neck(plate: Plate, center: Point, scale: float, mark: str, color: str,
               *, context: str = "", label: str = "", variant: int = 0) -> None:
    x, y = center
    plate.draw.ellipse((x - 88 * scale, y - 130 * scale,
                        x + 88 * scale, y + 45 * scale),
                       fill=hex_rgba(GOLD_LIGHT, 70), outline=INK_SOFT,
                       width=max(2, int(3 * scale)))
    plate.draw.rounded_rectangle((x - 50 * scale, y + 34 * scale,
                                  x + 50 * scale, y + 135 * scale),
                                 radius=int(22 * scale), fill=hex_rgba(PAPER_LIGHT, 80),
                                 outline=INK_SOFT, width=max(2, int(3 * scale)))
    positions = {
        "orbit": (40, -55), "sinus": (0, -42), "temporal": (62, -18),
        "thyroid": (0, 88), "node": (44, 55), "space": (-35, 28),
        "airway": (0, 45),
    }
    dx, dy = positions.get(mark, (30, 25))
    if mark == "none":
        return
    if context == "rad.5.orbit" and label == "Trauma":
        plate.draw.ellipse((x + 10 * scale, y - 83 * scale,
                            x + 70 * scale, y - 27 * scale),
                           fill=PAPER_LIGHT, outline=INK_SOFT,
                           width=max(2, int(4 * scale)))
        plate.draw.line((x + 38 * scale, y - 31 * scale,
                         x + 63 * scale, y - 8 * scale), fill=color,
                        width=max(3, int(6 * scale)))
    elif context == "rad.5.orbit" and label == "Inflammation":
        plate.draw.ellipse((x + 10 * scale, y - 83 * scale,
                            x + 70 * scale, y - 27 * scale),
                           fill=PAPER_LIGHT, outline=INK_SOFT,
                           width=max(2, int(4 * scale)))
        for shift in (-10, 10):
            plate.draw.line((x + 40 * scale, y - 55 * scale,
                             x + 76 * scale, y + shift * scale), fill=color,
                            width=max(3, int(7 * scale)))
    elif context == "rad.5.orbit" and label == "Mass":
        plate.draw.ellipse((x + 10 * scale, y - 83 * scale,
                            x + 70 * scale, y - 27 * scale),
                           fill=PAPER_LIGHT, outline=INK_SOFT,
                           width=max(2, int(4 * scale)))
        plate.draw.ellipse((x + 45 * scale, y - 67 * scale,
                            x + 70 * scale, y - 42 * scale), fill=color)
    else:
        plate.draw.ellipse((x + (dx - 22) * scale, y + (dy - 18) * scale,
                            x + (dx + 22) * scale, y + (dy + 18) * scale),
                           fill=hex_rgba(color, 165), outline=color,
                           width=max(2, int(3 * scale)))


def _breast(plate: Plate, center: Point, scale: float, mark: str, color: str,
            *, context: str = "", label: str = "", variant: int = 0) -> None:
    x, y = center
    if mark != "calcification-morphologies":
        plate.draw.arc((x - 118 * scale, y - 88 * scale,
                        x + 118 * scale, y + 118 * scale), 205, 520,
                       fill=CORAL, width=max(3, int(6 * scale)))
    if mark == "calcification-morphologies":
        # Paired magnification fields make morphology—not merely “more dots”—
        # visible: smooth coarse particles contrast with irregular pleomorphic
        # flecks and fine linear / fine-linear-branching forms.
        left_x = x - 62 * scale
        right_x = x + 62 * scale
        plate.text((left_x, y - 78 * scale), "COARSE", size=18, bold=True,
                   fill=INK_SOFT, anchor="mm")
        plate.text((right_x, y - 78 * scale), "FINE", size=18,
                   bold=True, fill=_text_tone(color), anchor="mm")
        for field_x, outline in ((left_x, INK_SOFT), (right_x, color)):
            plate.draw.ellipse((field_x - 43 * scale, y - 53 * scale,
                                field_x + 43 * scale, y + 55 * scale),
                               fill=hex_rgba(PAPER_LIGHT, 120), outline=outline,
                               width=max(2, int(4 * scale)))
        # Typically benign coarse comparator: deliberately smooth and large.
        for dx, dy, radius in ((-15, -14, 12), (13, -2, 15), (-8, 24, 11)):
            cx, cy = left_x + dx * scale, y + dy * scale
            plate.draw.ellipse((cx - radius * scale, cy - radius * scale,
                                cx + radius * scale, cy + radius * scale),
                               fill=hex_rgba(GOLD_LIGHT, 185), outline=INK_SOFT,
                               width=max(2, int(3 * scale)))
        # Suspicious comparator: angular pleomorphic flecks plus narrow rods
        # whose branches retain their linear character at the 800px export.
        for dx, dy, points in (
                (-18, -22, ((-7, -2), (-1, -8), (7, -3), (4, 7), (-5, 6))),
                (10, 17, ((-8, 1), (-2, -7), (8, -5), (5, 6), (-4, 9))),
                (-21, 25, ((-6, -5), (5, -8), (8, 3), (-2, 7)))):
            plate.draw.polygon(tuple(
                (right_x + (dx + px) * scale, y + (dy + py) * scale)
                for px, py in points), fill=color)
        branch_width = max(3, int(6 * scale))
        plate.draw.line((right_x - 5 * scale, y - 30 * scale,
                         right_x + 17 * scale, y - 4 * scale),
                        fill=color, width=branch_width)
        plate.draw.line((right_x + 6 * scale, y - 17 * scale,
                         right_x + 27 * scale, y - 28 * scale),
                        fill=color, width=branch_width)
        plate.draw.line((right_x + 6 * scale, y - 17 * scale,
                         right_x + 29 * scale, y + 2 * scale),
                        fill=color, width=branch_width)
    elif mark == "calcification-distributions":
        # Duct-oriented segmental distribution widens toward the periphery.
        plate.draw.polygon(((x - 32 * scale, y), (x + 88 * scale, y - 72 * scale),
                            (x + 88 * scale, y + 72 * scale)),
                           outline=hex_rgba(color, 135))
        for distance, spread in ((0, 0), (24, -8), (39, 10), (55, -22),
                                 (69, 27), (84, -41), (88, 42)):
            radius = 4 if distance < 60 else 3
            plate.draw.ellipse((x + (distance - radius) * scale,
                                y + (spread - radius) * scale,
                                x + (distance + radius) * scale,
                                y + (spread + radius) * scale), fill=color)
    elif mark == "calcification-sampling-target":
        # Target, biopsy path and clip/check make imaging-pathology concordance
        # visible without inventing a histologic outcome.
        plate.draw.ellipse((x + 8 * scale, y - 22 * scale,
                            x + 45 * scale, y + 15 * scale),
                           outline=color, width=max(3, int(6 * scale)))
        plate.arrow((x - 82 * scale, y - 57 * scale),
                    (x + 6 * scale, y - 12 * scale), fill=color,
                    width=max(2, int(4 * scale)), head=max(7, int(12 * scale)))
        plate.draw.line((x + 48 * scale, y + 35 * scale,
                         x + 62 * scale, y + 49 * scale,
                         x + 88 * scale, y + 18 * scale),
                        fill=_text_tone(GREEN), width=max(3, int(7 * scale)),
                        joint="curve")
    elif context == "rad.5.breast-mri" and label == "Choose indication":
        plate.draw.ellipse((x + 2 * scale, y - 18 * scale,
                            x + 42 * scale, y + 22 * scale),
                           outline=color, width=max(3, int(6 * scale)))
        plate.text((x + 22 * scale, y + 2 * scale), "?", size=max(16, int(26 * scale)),
                   bold=True, fill=_text_tone(color), anchor="mm")
    elif context == "rad.5.breast-mri" and label == "Read enhancement":
        plate.draw.ellipse((x + 2 * scale, y - 18 * scale,
                            x + 42 * scale, y + 22 * scale), fill=color)
        points = ((x - 76 * scale, y + 62 * scale),
                  (x - 48 * scale, y + 22 * scale),
                  (x - 10 * scale, y + 42 * scale),
                  (x + 38 * scale, y + 31 * scale))
        plate.polyline(points, fill=color, width=max(2, int(5 * scale)))
    elif context == "rad.5.breast-mri" and label == "Map extent":
        for dx in (2, 66):
            plate.draw.ellipse((x + dx * scale, y - 18 * scale,
                                x + (dx + 32) * scale, y + 14 * scale), fill=color)
        plate.double_arrow((x + 18 * scale, y + 31 * scale),
                           (x + 82 * scale, y + 31 * scale), fill=color,
                           width=max(2, int(4 * scale)))
    elif mark in {"calcification", "mass"}:
        for dx, dy in ((8, -12), (28, 4), (15, 20), (39, 24), (48, -5)):
            radius = 4 if mark == "calcification" else 10
            plate.draw.ellipse((x + (dx - radius) * scale, y + (dy - radius) * scale,
                                x + (dx + radius) * scale, y + (dy + radius) * scale), fill=color)
        if context == "rad.4.breast" and label == "Assign action":
            plate.draw.line((x + 56 * scale, y + 43 * scale,
                             x + 70 * scale, y + 57 * scale,
                             x + 96 * scale, y + 25 * scale),
                            fill=_text_tone(GREEN), width=max(3, int(7 * scale)),
                            joint="curve")
    else:
        plate.draw.ellipse((x + 2 * scale, y - 18 * scale, x + 42 * scale, y + 22 * scale),
                           fill=color)


def _evidence_glyph(plate: Plate, center: Point, scale: float,
                    kind: str, color: str) -> None:
    """Neutral evidence/decision glyph for concepts with no honest anatomy."""
    x, y = center
    if kind == "document":
        plate.draw.rounded_rectangle((x - 75 * scale, y - 100 * scale,
                                      x + 75 * scale, y + 100 * scale),
                                     radius=max(5, int(10 * scale)), fill=PAPER_LIGHT,
                                     outline=INK_SOFT, width=max(2, int(4 * scale)))
        for offset, length in ((-55, 105), (-23, 82), (9, 108), (41, 68)):
            plate.draw.line((x - 51 * scale, y + offset * scale,
                             x + (length - 51) * scale, y + offset * scale),
                            fill=color, width=max(2, int(4 * scale)))
    elif kind == "category":
        for index, width in enumerate((118, 92, 65)):
            top = y - 75 * scale + index * 57 * scale
            plate.draw.rounded_rectangle((x - width / 2 * scale, top,
                                          x + width / 2 * scale, top + 37 * scale),
                                         radius=max(4, int(8 * scale)),
                                         fill=hex_rgba(color, 70 + index * 55),
                                         outline=color, width=max(1, int(3 * scale)))
    elif kind == "action":
        plate.draw.rounded_rectangle((x - 86 * scale, y - 76 * scale,
                                      x + 86 * scale, y + 76 * scale),
                                     radius=max(6, int(13 * scale)), fill=PAPER_LIGHT,
                                     outline=INK_SOFT, width=max(2, int(4 * scale)))
        plate.draw.line((x - 48 * scale, y + 3 * scale,
                         x - 13 * scale, y + 38 * scale,
                         x + 57 * scale, y - 40 * scale),
                        fill=_text_tone(GREEN), width=max(4, int(9 * scale)),
                        joint="curve")
    elif kind == "age":
        for index, height in enumerate((62, 103, 145)):
            cx = x - 72 * scale + index * 72 * scale
            plate.draw.ellipse((cx - 16 * scale, y - height / 2 * scale - 28 * scale,
                                cx + 16 * scale, y - height / 2 * scale + 4 * scale),
                               fill=hex_rgba(color, 80 + index * 55), outline=color)
            plate.draw.line((cx, y - height / 2 * scale + 6 * scale,
                             cx, y + height / 2 * scale), fill=color,
                            width=max(3, int(7 * scale)))
    else:
        plate.draw.ellipse((x - 73 * scale, y - 73 * scale,
                            x + 73 * scale, y + 73 * scale),
                           fill=PAPER_LIGHT, outline=INK_SOFT,
                           width=max(2, int(4 * scale)))
        plate.draw.line((x - 46 * scale, y, x - 12 * scale, y + 34 * scale,
                         x + 52 * scale, y - 38 * scale), fill=color,
                        width=max(3, int(7 * scale)), joint="curve")


def _modality_motif(plate: Plate, center: Point, scale: float,
                    mark: str, color: str) -> None:
    x, y = center
    if mark == "xray-ct":
        # Attenuation: a beam loses intensity through material before reaching
        # a detector.  This covers the shared physical property, not a fake CT.
        plate.draw.rectangle((x - 112 * scale, y - 48 * scale,
                              x - 91 * scale, y + 48 * scale), fill=color)
        for offset in (-28, 0, 28):
            plate.arrow((x - 86 * scale, y + offset * scale),
                        (x + 101 * scale, y + offset * scale), fill=color,
                        width=max(1, int((5 - abs(offset) / 14) * scale)),
                        head=max(6, int(10 * scale)))
        plate.draw.ellipse((x - 25 * scale, y - 67 * scale,
                            x + 25 * scale, y + 67 * scale),
                           fill=hex_rgba(GOLD_LIGHT, 150), outline=GOLD)
        plate.draw.rectangle((x + 104 * scale, y - 75 * scale,
                              x + 122 * scale, y + 75 * scale), fill=INK_SOFT)
    elif mark == "ultrasound-mri":
        # Two honest miniatures: pulse/echo at left, magnetic alignment and RF
        # signal at right.  Neither is represented as an x-ray gantry.
        plate.draw.polygon(((x - 113 * scale, y - 55 * scale),
                            (x - 66 * scale, y - 43 * scale),
                            (x - 66 * scale, y - 8 * scale),
                            (x - 113 * scale, y + 4 * scale)), fill=color)
        for radius in (26, 46, 66):
            plate.draw.arc((x + (-67 - radius) * scale, y + (-2 - radius) * scale,
                            x + (-67 + radius) * scale, y + (-2 + radius) * scale),
                           300, 420, fill=color, width=max(1, int(3 * scale)))
        plate.draw.arc((x - 8 * scale, y - 82 * scale,
                        x + 125 * scale, y + 82 * scale), 80, 280,
                       fill=PLUM, width=max(5, int(11 * scale)))
        for dy in (-29, 0, 29):
            plate.arrow((x + 35 * scale, y + dy * scale),
                        (x + 86 * scale, y + dy * scale), fill=PLUM,
                        width=max(2, int(4 * scale)), head=max(7, int(11 * scale)))
    else:
        # Tracer emissions are detected outside the body; uptake is not drawn
        # as an arbitrary diagnostic hotspot.
        _body_outline(plate, center, scale * .62)
        plate.draw.rectangle((x - 132 * scale, y - 86 * scale,
                              x - 111 * scale, y + 86 * scale), fill=INK_SOFT)
        plate.draw.rectangle((x + 111 * scale, y - 86 * scale,
                              x + 132 * scale, y + 86 * scale), fill=INK_SOFT)
        for angle in (-28, 0, 28):
            radians = math.radians(angle)
            plate.arrow((x, y), (x + 104 * scale * math.cos(radians),
                                  y + 104 * scale * math.sin(radians)),
                        fill=color, width=max(1, int(3 * scale)),
                        head=max(6, int(9 * scale)))


def _scanner(plate: Plate, center: Point, scale: float, mark: str, color: str,
             *, context: str = "", label: str = "", variant: int = 0) -> None:
    x, y = center
    if context == "rad.2.radiation-safety":
        if label == "Justify the examination":
            plate.draw.ellipse((x - 76 * scale, y - 76 * scale,
                                x + 76 * scale, y + 76 * scale),
                               fill=hex_rgba(BLUE_LIGHT, 65), outline=color,
                               width=max(3, int(7 * scale)))
            plate.text((x, y), "?", size=max(24, int(58 * scale)), bold=True,
                       fill=_text_tone(color), anchor="mm")
        elif label == "Choose and optimise":
            # Collimation makes the optimisation trade visible: a broad
            # incident field is narrowed to the anatomy needed for the task.
            plate.draw.polygon(((x - 95 * scale, y - 67 * scale),
                                (x - 18 * scale, y - 31 * scale),
                                (x - 18 * scale, y + 31 * scale),
                                (x - 95 * scale, y + 67 * scale)),
                               fill=hex_rgba(color, 75), outline=color)
            plate.draw.rectangle((x - 17 * scale, y - 45 * scale,
                                  x + 17 * scale, y + 45 * scale),
                                 fill=PAPER_LIGHT, outline=INK_SOFT,
                                 width=max(2, int(4 * scale)))
            plate.draw.rectangle((x + 30 * scale, y - 31 * scale,
                                  x + 98 * scale, y + 31 * scale),
                                 fill=hex_rgba(GOLD_LIGHT, 105), outline=color,
                                 width=max(2, int(4 * scale)))
        else:
            # A checked record stands for verifying the delivered field/dose
            # and reviewing higher-risk circumstances after acquisition.
            plate.draw.rounded_rectangle((x - 83 * scale, y - 78 * scale,
                                          x + 83 * scale, y + 78 * scale),
                                         radius=max(7, int(14 * scale)),
                                         fill=hex_rgba(PAPER_LIGHT, 140),
                                         outline=color,
                                         width=max(2, int(5 * scale)))
            for dy in (-42, 0, 42):
                plate.draw.line((x - 57 * scale, y + dy * scale,
                                 x - 45 * scale, y + (dy + 12) * scale,
                                 x - 24 * scale, y + (dy - 13) * scale),
                                fill=_text_tone(GREEN),
                                width=max(3, int(7 * scale)), joint="curve")
                plate.draw.line((x - 8 * scale, y + dy * scale,
                                 x + 58 * scale, y + dy * scale),
                                fill=INK_SOFT, width=max(2, int(4 * scale)))
        return
    if context == "rad.2.modalities":
        _modality_motif(plate, center, scale, mark, color)
        return
    if context == "rad.3.mri-sequences":
        plate.draw.ellipse((x - 91 * scale, y - 78 * scale,
                            x + 91 * scale, y + 78 * scale),
                           fill=hex_rgba(PLUM_LIGHT, 90), outline=PLUM,
                           width=max(2, int(4 * scale)))
        if label == "T1 pattern":
            plate.draw.ellipse((x - 25 * scale, y - 14 * scale,
                                x + 25 * scale, y + 22 * scale), fill=INK_SOFT)
            for dx in (-52, 52):
                plate.draw.ellipse((x + (dx - 17) * scale, y - 25 * scale,
                                    x + (dx + 17) * scale, y + 9 * scale),
                                   fill=GOLD_LIGHT)
        elif label == "T2 / fluid":
            plate.draw.ellipse((x - 29 * scale, y - 18 * scale,
                                x + 29 * scale, y + 25 * scale),
                               fill=BLUE_LIGHT, outline=BLUE)
        else:
            plate.draw.rectangle((x - 77 * scale, y - 46 * scale,
                                  x - 5 * scale, y + 46 * scale),
                                 fill=INK_SOFT, outline=PLUM)
            plate.draw.rectangle((x + 5 * scale, y - 46 * scale,
                                  x + 77 * scale, y + 46 * scale),
                                 fill=PAPER_LIGHT, outline=PLUM)
            for cx in (x - 41 * scale, x + 41 * scale):
                plate.draw.ellipse((cx - 16 * scale, y - 16 * scale,
                                    cx + 16 * scale, y + 16 * scale), fill=color)
            plate.text((x - 41 * scale, y + 65 * scale), "DWI", size=max(11, int(15 * scale)),
                       bold=True, fill=_text_tone(color), anchor="mm")
            plate.text((x + 41 * scale, y + 65 * scale), "ADC", size=max(11, int(15 * scale)),
                       bold=True, fill=_text_tone(color), anchor="mm")
        return
    if context == "rad.4.structured-reporting":
        kind = {"image": "document", "category": "category",
                "action": "action"}.get(mark, "document")
        _evidence_glyph(plate, center, scale, kind, color)
        return
    if context == "rad.4.paediatric":
        if label == "Choose by age":
            _evidence_glyph(plate, center, scale, "age", color)
        elif label == "Read the whole study":
            _body_outline(plate, center, scale * .62)
            for dy in (-52, 0, 52):
                plate.draw.ellipse((x + 55 * scale, y + (dy - 8) * scale,
                                    x + 71 * scale, y + (dy + 8) * scale),
                                   outline=color, width=max(2, int(3 * scale)))
        else:
            # A bounded field communicates collimation/dose optimisation; no
            # misleading lead-shield icon is used.
            _body_outline(plate, center, scale * .62)
            plate.draw.rectangle((x - 59 * scale, y - 45 * scale,
                                  x + 59 * scale, y + 52 * scale),
                                 outline=color, width=max(3, int(7 * scale)))
            for corner_x, corner_y in ((-59, -45), (59, -45), (-59, 52), (59, 52)):
                plate.draw.line((x + corner_x * scale, y + corner_y * scale,
                                 x + (corner_x * .72) * scale,
                                 y + (corner_y * .72) * scale), fill=color,
                                width=max(2, int(4 * scale)))
        return
    if context == "rad.5.paeds-masses-neuro":
        if label == "Age prior":
            _evidence_glyph(plate, center, scale, "age", color)
        elif label == "Find origin":
            plate.draw.ellipse((x - 88 * scale, y - 72 * scale,
                                x + 88 * scale, y + 72 * scale),
                               fill=PAPER_LIGHT, outline=INK_SOFT,
                               width=max(2, int(4 * scale)))
            plate.draw.line((x - 88 * scale, y, x + 88 * scale, y), fill=GRID,
                            width=max(1, int(2 * scale)))
            plate.draw.line((x, y - 72 * scale, x, y + 72 * scale), fill=GRID,
                            width=max(1, int(2 * scale)))
            plate.draw.ellipse((x + 23 * scale, y - 38 * scale,
                                x + 57 * scale, y - 4 * scale), fill=color)
        else:
            plate.draw.polygon(((x - 89 * scale, y - 74 * scale),
                                (x - 28 * scale, y - 55 * scale),
                                (x - 35 * scale, y - 15 * scale),
                                (x - 96 * scale, y - 34 * scale)), fill=color)
            for radius in (34, 58, 82):
                plate.draw.arc((x + (-24 - radius) * scale, y + (-34 - radius) * scale,
                                x + (-24 + radius) * scale, y + (-34 + radius) * scale),
                               310, 410, fill=color, width=max(1, int(3 * scale)))
        return
    if context == "rad.5.ultrasound-physics":
        if label == "Transmit":
            plate.draw.polygon(((x - 102 * scale, y - 48 * scale),
                                (x - 40 * scale, y - 35 * scale),
                                (x - 40 * scale, y + 35 * scale),
                                (x - 102 * scale, y + 48 * scale)), fill=color)
            for radius in (35, 65, 95):
                plate.draw.arc((x + (-41 - radius) * scale, y - radius * scale,
                                x + (-41 + radius) * scale, y + radius * scale),
                               310, 410, fill=color, width=max(1, int(3 * scale)))
        elif label == "Echo / Doppler":
            plate.arrow((x - 100 * scale, y - 28 * scale),
                        (x + 75 * scale, y - 28 * scale), fill=BLUE,
                        width=max(2, int(4 * scale)), head=max(7, int(11 * scale)))
            plate.arrow((x + 75 * scale, y + 28 * scale),
                        (x - 100 * scale, y + 28 * scale), fill=CORAL,
                        width=max(2, int(4 * scale)), head=max(7, int(11 * scale)))
            plate.draw.ellipse((x + 54 * scale, y - 51 * scale,
                                x + 97 * scale, y + 51 * scale),
                               fill=hex_rgba(GOLD_LIGHT, 145), outline=GOLD)
        else:
            plate.draw.rectangle((x - 96 * scale, y - 76 * scale,
                                  x + 96 * scale, y + 76 * scale),
                                 outline=INK_SOFT, width=max(2, int(4 * scale)))
            plate.draw.line((x - 72 * scale, y - 25 * scale,
                             x - 20 * scale, y - 25 * scale), fill=color,
                            width=max(3, int(7 * scale)))
            plate.draw.polygon(((x - 20 * scale, y - 54 * scale),
                                (x + 66 * scale, y - 54 * scale),
                                (x + 31 * scale, y + 64 * scale)),
                               fill=hex_rgba(color, 80), outline=color)
        return
    if context == "rad.3.contrast":
        if label == "Question":
            plate.draw.ellipse((x - 74 * scale, y - 74 * scale,
                                x + 74 * scale, y + 74 * scale),
                               outline=color, width=max(3, int(7 * scale)))
            plate.text((x, y), "?", size=max(20, int(42 * scale)), bold=True,
                       fill=_text_tone(color), anchor="mm")
        elif label == "Enhancement":
            points = ((x - 92 * scale, y + 62 * scale),
                      (x - 55 * scale, y + 45 * scale),
                      (x - 20 * scale, y - 43 * scale),
                      (x + 18 * scale, y - 5 * scale),
                      (x + 92 * scale, y + 22 * scale))
            plate.polyline(points, fill=color, width=max(3, int(7 * scale)))
            plate.draw.line((x - 99 * scale, y + 64 * scale,
                             x + 99 * scale, y + 64 * scale), fill=INK_SOFT,
                            width=max(2, int(3 * scale)))
        else:
            _kidney_shape(plate, (x - 35 * scale, y), scale * .75)
            _kidney_shape(plate, (x + 35 * scale, y), scale * .75)
            plate.draw.line((x + 63 * scale, y + 61 * scale,
                             x + 77 * scale, y + 75 * scale,
                             x + 102 * scale, y + 43 * scale),
                            fill=_text_tone(GREEN), width=max(3, int(7 * scale)),
                            joint="curve")
        return
    plate.draw.ellipse((x - 110 * scale, y - 110 * scale,
                        x + 110 * scale, y + 110 * scale),
                       fill=hex_rgba(BLUE_LIGHT, 80), outline=BLUE,
                       width=max(3, int(8 * scale)))
    plate.draw.ellipse((x - 58 * scale, y - 58 * scale,
                        x + 58 * scale, y + 58 * scale),
                       fill=PAPER_LIGHT, outline=GRID, width=max(2, int(4 * scale)))
    plate.draw.line((x - 155 * scale, y + 68 * scale, x + 68 * scale, y + 68 * scale),
                    fill=INK_SOFT, width=max(4, int(10 * scale)))
    if mark in {"radiation", "ct", "contrast", "window"}:
        for angle in range(0, 360, 45):
            radians = math.radians(angle)
            plate.draw.line((x + 62 * scale * math.cos(radians),
                             y + 62 * scale * math.sin(radians),
                             x + 96 * scale * math.cos(radians),
                             y + 96 * scale * math.sin(radians)),
                            fill=color, width=max(2, int(5 * scale)))
    elif mark in {"mri", "sequence", "signal"}:
        for radius in (72, 88, 104):
            plate.draw.arc((x - radius * scale, y - radius * scale,
                            x + radius * scale, y + radius * scale),
                           210, 330, fill=color, width=max(2, int(4 * scale)))


def _molecular_target(plate: Plate, center: Point, scale: float,
                      color: str, *, therapeutic: bool = False) -> None:
    """Ligand-receptor binding without implying a specific radiopharmaceutical."""
    x, y = center
    plate.draw.arc((x - 103 * scale, y - 88 * scale,
                    x + 103 * scale, y + 88 * scale), 10, 170,
                   fill=PLUM, width=max(4, int(9 * scale)))
    # Membrane receptor pocket.
    plate.draw.line((x - 18 * scale, y + 3 * scale,
                     x - 18 * scale, y - 43 * scale,
                     x + 18 * scale, y - 43 * scale,
                     x + 18 * scale, y + 3 * scale),
                    fill=PLUM, width=max(3, int(7 * scale)), joint="curve")
    plate.draw.polygon(((x, y - 92 * scale),
                        (x - 22 * scale, y - 60 * scale),
                        (x + 22 * scale, y - 60 * scale)), fill=color)
    plate.arrow((x, y - 119 * scale), (x, y - 94 * scale), fill=color,
                width=max(2, int(4 * scale)), head=max(7, int(11 * scale)))
    if therapeutic:
        for angle in range(0, 360, 45):
            radians = math.radians(angle)
            plate.draw.line((x, y - 106 * scale,
                             x + 31 * scale * math.cos(radians),
                             y - 106 * scale + 31 * scale * math.sin(radians)),
                            fill=CORAL, width=max(1, int(3 * scale)))


def _tracer(plate: Plate, center: Point, scale: float, mark: str, color: str,
            *, context: str = "", label: str = "", variant: int = 0) -> None:
    x, y = center
    if mark == "bone-vq":
        # Two physiological maps, explicitly separated: skeletal turnover at
        # left and ventilation/perfusion pairing at right.
        plate.draw.line((x - 64 * scale, y - 78 * scale,
                         x - 64 * scale, y + 85 * scale), fill=GOLD_LIGHT,
                        width=max(6, int(13 * scale)))
        for dy in (-71, -20, 31, 82):
            plate.draw.ellipse((x - 77 * scale, y + (dy - 12) * scale,
                                x - 51 * scale, y + (dy + 12) * scale),
                               fill=color, outline=INK_SOFT)
        for dx in (25, 76):
            plate.draw.ellipse((x + (dx - 23) * scale, y - 59 * scale,
                                x + (dx + 23) * scale, y + 55 * scale),
                               fill=hex_rgba(BLUE_LIGHT, 135), outline=BLUE)
        # Matching arrows on one lung, mismatch on the other.
        plate.arrow((x + 25 * scale, y - 88 * scale),
                    (x + 25 * scale, y - 60 * scale), fill=TEAL,
                    width=max(2, int(4 * scale)), head=max(7, int(11 * scale)))
        plate.arrow((x + 25 * scale, y + 84 * scale),
                    (x + 25 * scale, y + 57 * scale), fill=CORAL,
                    width=max(2, int(4 * scale)), head=max(7, int(11 * scale)))
        plate.arrow((x + 76 * scale, y - 88 * scale),
                    (x + 76 * scale, y - 60 * scale), fill=TEAL,
                    width=max(2, int(4 * scale)), head=max(7, int(11 * scale)))
        plate.draw.line((x + 61 * scale, y + 67 * scale,
                         x + 91 * scale, y + 67 * scale), fill=CORAL,
                        width=max(3, int(6 * scale)))
        return
    if mark == "thyroid-neck":
        # Butterfly-shaped functioning tissue in the neck.
        plate.draw.ellipse((x - 76 * scale, y - 70 * scale,
                            x - 8 * scale, y + 63 * scale),
                           fill=hex_rgba(color, 175), outline=_text_tone(color))
        plate.draw.ellipse((x + 8 * scale, y - 70 * scale,
                            x + 76 * scale, y + 63 * scale),
                           fill=hex_rgba(color, 175), outline=_text_tone(color))
        plate.draw.rectangle((x - 15 * scale, y - 20 * scale,
                              x + 15 * scale, y + 20 * scale), fill=color)
        for dy in (-48, -8, 34):
            plate.draw.ellipse((x + 32 * scale, y + dy * scale,
                                x + 46 * scale, y + (dy + 14) * scale),
                               fill=PAPER_LIGHT)
        return
    if mark == "sentinel-lymph-drainage":
        injection = (x - 91 * scale, y + 67 * scale)
        node = (x + 70 * scale, y - 48 * scale)
        plate.draw.ellipse((injection[0] - 15 * scale, injection[1] - 15 * scale,
                            injection[0] + 15 * scale, injection[1] + 15 * scale),
                           fill=color, outline=INK)
        path = ((injection[0] + 13 * scale, injection[1] - 7 * scale),
                (x - 24 * scale, y + 26 * scale),
                (x + 20 * scale, y - 14 * scale), node)
        plate.polyline(path, fill=TEAL, width=max(3, int(6 * scale)))
        plate.draw.ellipse((node[0] - 25 * scale, node[1] - 20 * scale,
                            node[0] + 25 * scale, node[1] + 20 * scale),
                           fill=TEAL_LIGHT, outline=TEAL,
                           width=max(2, int(4 * scale)))
        plate.arrow(path[-2], node, fill=TEAL, width=max(2, int(4 * scale)),
                    head=max(7, int(11 * scale)))
        return
    if mark == "theranostic-diagnostic-target":
        _molecular_target(plate, center, scale, color, therapeutic=False)
        plate.draw.ellipse((x + 66 * scale, y + 40 * scale,
                            x + 98 * scale, y + 72 * scale),
                           outline=color, width=max(2, int(4 * scale)))
        return
    if mark == "theranostic-therapy-same-target":
        _molecular_target(plate, center, scale, color, therapeutic=True)
        return
    if mark == "theranostic-followup-organs":
        _body_outline(plate, center, scale * .67)
        # Kidneys and salivary glands are monitoring examples; the adjacent
        # dose bars make the dosimetry concept explicit.
        for dx in (-31, 31):
            _kidney_shape(plate, (x + dx * scale, y + 25 * scale), scale * .32,
                          fill=PLUM_LIGHT, outline=PLUM)
            plate.draw.ellipse((x + (dx - 6) * scale, y - 83 * scale,
                                x + (dx + 6) * scale, y - 71 * scale), fill=color)
        for index, height in enumerate((30, 48, 68)):
            left = x + (67 + index * 18) * scale
            plate.draw.rectangle((left, y + (75 - height) * scale,
                                  left + 11 * scale, y + 75 * scale),
                                 fill=hex_rgba(color, 100 + index * 50))
        return
    if context == "rad.5.pet-ct":
        if label == "Prepare":
            plate.draw.ellipse((x - 77 * scale, y - 77 * scale,
                                x + 77 * scale, y + 77 * scale),
                               outline=INK_SOFT, width=max(2, int(4 * scale)))
            plate.draw.line((x, y, x, y - 52 * scale), fill=color,
                            width=max(3, int(6 * scale)))
            plate.draw.line((x, y, x + 42 * scale, y + 17 * scale), fill=color,
                            width=max(3, int(6 * scale)))
            plate.draw.ellipse((x - 108 * scale, y + 50 * scale,
                                x - 78 * scale, y + 80 * scale), fill=color)
        elif label == "Match anatomy":
            plate.draw.ellipse((x - 88 * scale, y - 78 * scale,
                                x + 88 * scale, y + 78 * scale),
                               fill=hex_rgba(BLUE_LIGHT, 80), outline=BLUE)
            plate.draw.ellipse((x - 55 * scale, y - 50 * scale,
                                x + 55 * scale, y + 50 * scale),
                               outline=INK_SOFT, width=max(2, int(4 * scale)))
            plate.draw.ellipse((x + 14 * scale, y - 18 * scale,
                                x + 42 * scale, y + 10 * scale), fill=color)
            plate.draw.line((x + 28 * scale, y - 55 * scale,
                             x + 28 * scale, y + 50 * scale), fill=color,
                            width=max(1, int(3 * scale)))
        else:
            _evidence_glyph(plate, center, scale, "action", color)
        return
    _body_outline(plate, center, scale)
    for dx, dy in ((0, -110), (0, 15), (0, 85)):
        plate.draw.ellipse((x + (dx - 10) * scale, y + (dy - 10) * scale,
                            x + (dx + 10) * scale, y + (dy + 10) * scale),
                           fill=color, outline=INK, width=max(1, int(2 * scale)))


def draw_motif(plate: Plate, motif: str, center: Point, scale: float,
               mark: str, color: str, *, context: str = "", label: str = "",
               variant: int = 0) -> None:
    if motif == "lungs":
        _lungs(plate, center, scale, mark, color, context=context,
               label=label, variant=variant)
    elif motif == "heart":
        _heart(plate, center, scale, mark, color, context=context,
               label=label, variant=variant)
    elif motif == "vessel":
        _vessel(plate, center, scale, mark, color, context=context,
                label=label, variant=variant)
    elif motif == "brain":
        _brain(plate, center, scale, mark, color, context=context,
               label=label, variant=variant)
    elif motif == "head-neck":
        _head_neck(plate, center, scale, mark, color, context=context,
                   label=label, variant=variant)
    elif motif == "abdomen":
        _abdomen(plate, center, scale, mark, color, context=context,
                 label=label, variant=variant)
    elif motif == "bone":
        _bone(plate, center, scale, mark, color, context=context,
              label=label, variant=variant)
    elif motif == "breast":
        _breast(plate, center, scale, mark, color, context=context,
                label=label, variant=variant)
    elif motif == "tracer":
        _tracer(plate, center, scale, mark, color, context=context,
                label=label, variant=variant)
    else:
        _scanner(plate, center, scale, mark, color, context=context,
                 label=label, variant=variant)


def _item_text(plate: Plate, box: Box, item: Dict[str, str], color: str) -> None:
    x0, y0, x1, y1 = box
    plate.text(((x0 + x1) / 2, y0 + 18), item["label"], size=23, bold=True,
               fill=_text_tone(color), anchor="ma")
    plate.wrapped_text((int(x0 + 10), int(y0 + 54), int(x1 - 10), int(y1)),
                       item["detail"], size=19, fill=INK_SOFT, line_gap=6)


def _draw_flow(plate: Plate, item: Spec) -> None:
    boxes = ((124, 236, 514, 790), (605, 236, 995, 790), (1086, 236, 1476, 790))
    motif = str(item["motif"])
    entries = item["items"]
    headings = _flow_headings(item)
    for index, (box, entry) in enumerate(zip(boxes, entries)):
        color = COLORS[index]
        inner = panel(plate, box, headings[index], outline=color,
                      heading_fill=_text_tone(color))
        x0, y0, x1, y1 = inner
        draw_motif(plate, motif, ((x0 + x1) / 2, y0 + 155), .68,
                   str(entry.get("mark", "")), color, context=str(item["id"]),
                   label=str(entry["label"]), variant=index)
        _item_text(plate, (x0, y0 + 270, x1, y1), entry, color)
    arrow_label(plate, (519, 500), (596, 500), "", fill=GOLD, width=7)
    arrow_label(plate, (1000, 500), (1077, 500), "", fill=GOLD, width=7)


def _draw_compare(plate: Plate, item: Spec) -> None:
    boxes = ((124, 236, 514, 790), (605, 236, 995, 790), (1086, 236, 1476, 790))
    motif = str(item["motif"])
    for index, (box, entry) in enumerate(zip(boxes, item["items"])):
        color = COLORS[index]
        inner = panel(plate, box, str(entry["label"]).upper(), outline=color,
                      heading_fill=_text_tone(color))
        x0, y0, x1, y1 = inner
        draw_motif(plate, motif, ((x0 + x1) / 2, y0 + 155), .72,
                   str(entry.get("mark", "")), color, context=str(item["id"]),
                   label=str(entry["label"]), variant=index)
        plate.wrapped_text((int(x0 + 10), int(y0 + 285), int(x1 - 10), int(y1)),
                           str(entry["detail"]), size=20, fill=INK_SOFT, line_gap=6)


def _draw_map_subject(plate: Plate, item: Spec) -> Tuple[Point, Point, Point]:
    """Draw each map's actual spatial relationships and return its targets."""
    context = str(item["id"])
    if context == "rad.5.mediastinum":
        # Axial thorax: anterior is up.  The compartment targets occupy actual
        # prevascular, visceral and paravertebral regions.
        plate.draw.ellipse((645, 330, 955, 650), fill=hex_rgba(GOLD_LIGHT, 50),
                           outline=INK_SOFT, width=4)
        for box in ((675, 385, 755, 575), (845, 385, 925, 575)):
            plate.draw.ellipse(box, fill=hex_rgba(BLUE_LIGHT, 95), outline=BLUE, width=3)
        zones = ((800, 380), (800, 485), (800, 605))
        for index, (cx, cy) in enumerate(zones):
            plate.draw.rounded_rectangle((cx - 38, cy - 24, cx + 38, cy + 24),
                                         radius=13, fill=hex_rgba(LIGHTS[index], 165),
                                         outline=COLORS[index], width=3)
        return zones
    if context == "rad.4.lung-cancer":
        _lungs(plate, (800, 490), 1.05, "none", PLUM)
        targets = ((724, 516), (800, 448), (884, 404))
        plate.draw.ellipse((700, 492, 748, 540), fill=COLORS[0], outline=INK)
        plate.draw.ellipse((784, 432, 816, 464), fill=COLORS[1], outline=INK)
        plate.draw.ellipse((870, 390, 898, 418), fill=COLORS[2], outline=INK)
        return targets
    if context == "rad.5.tavi-ct":
        _heart(plate, (800, 470), .88, "none", PLUM)
        plate.draw.ellipse((754, 416, 846, 452), outline=COLORS[0], width=7)
        plate.draw.line((800, 416, 800, 330), fill=CORAL, width=12)
        for cx in (770, 830):
            plate.draw.ellipse((cx - 9, 350, cx + 9, 368), fill=COLORS[1])
        plate.draw.line((800, 542, 770, 635), fill=COLORS[2], width=10)
        plate.draw.line((770, 635, 735, 675), fill=COLORS[2], width=10)
        return ((800, 434), (830, 359), (752, 650))
    if context == "rad.5.brain-anatomy":
        _brain(plate, (800, 490), 1.08, "none", PLUM)
        plate.draw.polygon(((793, 486), (688, 418), (704, 560)),
                           fill=hex_rgba(COLORS[0], 145), outline=COLORS[0])
        plate.draw.arc((704, 378, 896, 447), 190, 350, fill=COLORS[1], width=10)
        plate.draw.ellipse((856, 492, 891, 527), fill=COLORS[2], outline=INK)
        return ((714, 486), (800, 408), (874, 510))
    if context == "rad.5.neck-nodes":
        _head_neck(plate, (800, 480), 1.0, "none", PLUM)
        # One nodal chain: level position, morphology, then drainage/plan route.
        plate.draw.line((848, 415, 848, 595), fill=GRID, width=5)
        for cy in (432, 490, 550):
            plate.draw.ellipse((832, cy - 13, 864, cy + 13),
                               fill=hex_rgba(TEAL_LIGHT, 150), outline=TEAL, width=3)
        plate.draw.ellipse((830, 474, 866, 506), fill=COLORS[1], outline=INK, width=3)
        plate.arrow((848, 554), (800, 618), fill=COLORS[2], width=6, head=17)
        return ((848, 432), (848, 490), (810, 606))
    if context == "rad.5.deep-neck-spaces":
        _head_neck(plate, (800, 480), 1.0, "none", PLUM)
        plate.draw.rounded_rectangle((738, 440, 790, 555), radius=22,
                                     fill=hex_rgba(COLORS[0], 125),
                                     outline=COLORS[0], width=4)
        plate.arrow((790, 490), (835, 490), fill=COLORS[1], width=6, head=17)
        plate.draw.line((815, 433, 815, 583), fill=INK_SOFT, width=8)
        plate.arrow((786, 548), (810, 590), fill=COLORS[2], width=6, head=17)
        return ((764, 480), (830, 490), (808, 580))
    if context == "rad.5.sinuses":
        _head_neck(plate, (800, 480), 1.0, "none", PLUM)
        plate.draw.ellipse((761, 399, 839, 454), fill=hex_rgba(BLUE_LIGHT, 125),
                           outline=COLORS[0], width=4)
        plate.draw.ellipse((844, 379, 891, 423), fill=PAPER_LIGHT,
                           outline=COLORS[1], width=5)
        plate.arrow((800, 452), (800, 514), fill=COLORS[0], width=5, head=15)
        plate.draw.ellipse((770, 431, 813, 472), fill=hex_rgba(COLORS[2], 150),
                           outline=COLORS[2], width=3)
        return ((800, 462), (866, 401), (791, 451))
    if context == "rad.5.temporal-bone":
        plate.draw.ellipse((680, 350, 920, 640), fill=hex_rgba(GOLD_LIGHT, 85),
                           outline=INK_SOFT, width=4)
        plate.draw.ellipse((720, 445, 775, 500), fill=PAPER_LIGHT,
                           outline=COLORS[0], width=5)
        plate.draw.arc((774, 405, 884, 535), 20, 340, fill=COLORS[1], width=10)
        plate.polyline(((699, 527), (748, 548), (805, 525), (855, 572)),
                       fill=COLORS[2], width=7)
        return ((748, 472), (830, 470), (805, 525))
    if context == "rad.5.peritoneum":
        plate.draw.rounded_rectangle((685, 330, 915, 665), radius=90,
                                     fill=hex_rgba(GOLD_LIGHT, 55),
                                     outline=INK_SOFT, width=4)
        plate.draw.arc((705, 355, 895, 440), 190, 350, fill=COLORS[0], width=10)
        plate.draw.line((720, 420, 720, 594), fill=COLORS[1], width=10)
        plate.draw.line((880, 420, 880, 594), fill=COLORS[1], width=10)
        plate.draw.arc((740, 555, 860, 642), 0, 180, fill=COLORS[2], width=10)
        return ((800, 388), (720, 500), (800, 590))
    if context == "rad.5.rectal-mr":
        plate.draw.rounded_rectangle((770, 355, 830, 630), radius=26,
                                     fill=hex_rgba(CORAL_LIGHT, 110), outline=CORAL, width=5)
        plate.draw.ellipse((737, 325, 863, 660), outline=COLORS[1], width=6)
        plate.draw.ellipse((794, 450, 837, 505), fill=COLORS[0], outline=INK)
        plate.polyline(((812, 520), (862, 552), (895, 612)), fill=COLORS[2], width=8)
        return ((816, 477), (850, 477), (874, 572))
    if context == "rad.5.uterine-mr":
        plate.draw.polygon(((800, 620), (744, 500), (755, 385),
                            (845, 385), (856, 500)),
                           fill=hex_rgba(CORAL_LIGHT, 135), outline=CORAL)
        plate.draw.line((800, 408, 800, 577), fill=PAPER_LIGHT, width=8)
        plate.draw.ellipse((820, 447, 854, 493), fill=COLORS[0], outline=INK)
        plate.draw.ellipse((711, 520, 752, 561), fill=COLORS[1], outline=INK)
        plate.draw.arc((750, 360, 850, 432), 180, 360, fill=COLORS[2], width=8)
        return ((837, 470), (732, 540), (800, 386))

    # Validated fallback: keep targets tied to three explicitly marked regions
    # rather than to arbitrary fixed coordinates.
    draw_motif(plate, str(item["motif"]), (800, 500), 1.0, "none", PLUM,
               context=context)
    targets = ((725, 445), (875, 445), (800, 590))
    for index, target in enumerate(targets):
        plate.draw.ellipse((target[0] - 15, target[1] - 15,
                            target[0] + 15, target[1] + 15), fill=COLORS[index])
    return targets


def _draw_map(plate: Plate, item: Spec) -> None:
    anchors = _draw_map_subject(plate, item)
    boxes = ((118, 245, 490, 405), (1110, 245, 1482, 405), (614, 690, 986, 842))
    # Route arrows first so the cards mask their tails and the authored text
    # remains clean; every arrowhead lands on a drawn anatomical feature.
    for index, (box, anchor) in enumerate(zip(boxes, anchors)):
        color = COLORS[index]
        start = ((box[2], (box[1] + box[3]) / 2) if index == 0 else
                 (box[0], (box[1] + box[3]) / 2) if index == 1 else
                 ((box[0] + box[2]) / 2, box[1]))
        plate.arrow(start, anchor, fill=color, width=5, head=16)
    for index, (box, entry) in enumerate(zip(boxes, item["items"])):
        color = COLORS[index]
        plate.card(box, fill=hex_rgba(LIGHTS[index], 70), outline=color, width=3, radius=20)
        _item_text(plate, (box[0] + 16, box[1] + 16, box[2] - 16, box[3] - 10), entry, color)


def _draw_scale(plate: Plate, item: Spec) -> None:
    y0, y1 = 390, 610
    entries = item["items"]
    for index, entry in enumerate(entries):
        x0 = 150 + index * 433
        x1 = x0 + 410
        color = COLORS[index]
        plate.draw.rounded_rectangle((x0, y0, x1, y1), radius=24,
                                     fill=hex_rgba(LIGHTS[index], 100),
                                     outline=color, width=4)
        plate.text(((x0 + x1) / 2, y0 + 58), str(entry["label"]), size=28,
                   bold=True, fill=_text_tone(color), anchor="mm")
        plate.wrapped_text((x0 + 28, y0 + 92, x1 - 28, y1 - 28),
                           str(entry["detail"]), size=22, fill=INK_SOFT)
        if index < 2:
            plate.arrow((x1 + 8, 500), (x1 + 23, 500), fill=GOLD, width=5, head=13)
    plate.draw.line((170, 680, 1430, 680), fill=GRID, width=7)
    for index, entry in enumerate(entries):
        x = 355 + index * 433
        plate.draw.ellipse((x - 15, 665, x + 15, 695), fill=COLORS[index])
        plate.text((x, 730), str(entry.get("mark", "category")), size=20,
                   bold=True, fill=_text_tone(COLORS[index]), anchor="mm")


def _draw_physics(plate: Plate, item: Spec) -> None:
    entries = item["items"]
    centers = ((300, 485), (800, 485), (1300, 485))
    motif = str(item["motif"])
    for index, (center, entry) in enumerate(zip(centers, entries)):
        color = COLORS[index]
        draw_motif(plate, motif if index == 1 else "scanner", center, .75,
                   str(entry.get("mark", "signal")), color, context=str(item["id"]),
                   label=str(entry["label"]), variant=index)
        plate.text((center[0], 660), str(entry["label"]), size=25, bold=True,
                   fill=_text_tone(color), anchor="mm")
        plate.wrapped_text((center[0] - 170, 690, center[0] + 170, 790),
                           str(entry["detail"]), size=19, fill=INK_SOFT, line_gap=5)
    arrow_label(plate, (430, 485), (650, 485), "interaction",
                fill=_text_tone(GOLD), width=8)
    arrow_label(plate, (950, 485), (1170, 485), "measurement",
                fill=_text_tone(GOLD), width=8)


def render_spec(output_root: Path, item: Spec, *, overwrite: bool = False) -> List[Path]:
    paths = asset_paths(output_root, str(item["id"]), int(item["stage"]))
    if not overwrite and any(path.exists() for path in paths):
        raise FileExistsError("Refusing to overwrite {}".format(paths))
    plate = RadiologyPlate(str(item["id"]), _short_title(str(item["title"])),
                           int(item["stage"]))
    mode = str(item["mode"])
    if mode == "compare":
        _draw_compare(plate, item)
    elif mode == "map":
        _draw_map(plate, item)
    elif mode == "scale":
        _draw_scale(plate, item)
    elif mode == "physics":
        _draw_physics(plate, item)
    else:
        _draw_flow(plate, item)
    footer(plate, str(item["takeaway"]), size=24,
           fill=_text_tone(plate.accent))
    paths[0].parent.mkdir(parents=True, exist_ok=True)
    plate.image.save(paths[0], "WEBP", quality=86, method=6)
    plate.image.resize((800, 500), Image.Resampling.LANCZOS).save(
        paths[1], "WEBP", quality=84, method=6)
    return list(paths)


def validate_specs(specs: Dict[str, Spec], expected_ids: Iterable[str]) -> None:
    expected = set(expected_ids)
    if set(specs) != expected:
        raise ValueError("Radiology spec mismatch; missing={}, extra={}".format(
            sorted(expected - set(specs)), sorted(set(specs) - expected)))
    for node_id, item in specs.items():
        if item.get("id") != node_id or item.get("mode") not in {
                "flow", "compare", "map", "scale", "physics"}:
            raise ValueError("Malformed radiology spec for {}".format(node_id))
        if item.get("motif") not in {
                "scanner", "lungs", "heart", "vessel", "brain", "head-neck",
                "abdomen", "bone", "breast", "tracer"}:
            raise ValueError("Unknown motif for {}".format(node_id))
        entries = item.get("items")
        if not isinstance(entries, list) or len(entries) != 3:
            raise ValueError("{} needs exactly three explanatory items".format(node_id))
        for entry in entries:
            if not isinstance(entry, dict) or not str(entry.get("label", "")).strip() \
                    or len(str(entry.get("detail", "")).split()) < 3:
                raise ValueError("{} has an empty explanatory item".format(node_id))
        if item.get("mode") == "flow":
            supplied = item.get("headings")
            per_item = all(str(entry.get("heading", "")).strip() for entry in entries)
            if not per_item and not (
                    isinstance(supplied, (list, tuple)) and len(supplied) == 3 and
                    all(str(value).strip() for value in supplied)):
                raise ValueError("{} needs three role-specific flow headings".format(node_id))
        if len(str(item.get("takeaway", "")).split()) < 8:
            raise ValueError("{} needs a substantive takeaway".format(node_id))
