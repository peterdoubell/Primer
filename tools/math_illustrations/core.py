"""Small deterministic drawing system for Primer mathematics plates.

The curriculum spans counting through research mathematics.  Exact diagrams
are drawn from geometry rather than generated pixels so that arrows, axes,
partitions and equations remain trustworthy.  Cohort modules provide the
lesson-specific composition, alt text and caption.
"""

from __future__ import annotations

import hashlib
import math
import os
import random
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Sequence, Tuple

from PIL import Image, ImageDraw, ImageFont


WIDTH = 1600
HEIGHT = 1000
CONTENT = (92, 176, 1508, 900)

INK = "#24303a"
INK_SOFT = "#53616b"
PAPER = "#f4ecd8"
PAPER_LIGHT = "#fbf7ea"
EDGE = "#8e7957"
GRID = "#c9bda2"
BLUE = "#315f7c"
BLUE_LIGHT = "#a9c7d5"
TEAL = "#34756f"
TEAL_LIGHT = "#b8d8cf"
GOLD = "#c8902f"
GOLD_LIGHT = "#efd69b"
CORAL = "#b45f4d"
CORAL_LIGHT = "#e9b7a8"
PLUM = "#765b7e"
PLUM_LIGHT = "#cbb9cf"
GREEN = "#56724b"
GREEN_LIGHT = "#bfd0ae"

STAGE_NAMES = {
    0: "SEEDLING",
    1: "SPROUT",
    2: "SAPLING",
    3: "TREE",
    4: "GROVE",
    5: "FOREST",
}
STAGE_COLORS = {
    0: TEAL,
    1: GREEN,
    2: BLUE,
    3: PLUM,
    4: CORAL,
    5: GOLD,
}
STAGE_DIRS = {
    0: "seedling",
    1: "sprout",
    2: "sapling",
    3: "tree",
    4: "grove",
    5: "forest",
}

_REGULAR_CANDIDATES = (
    "/System/Library/Fonts/Avenir Next.ttc",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
)
_BOLD_CANDIDATES = (
    "/System/Library/Fonts/Supplemental/Verdana Bold.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
)
_MATH_CANDIDATES = (
    "/System/Library/Fonts/Supplemental/STIXTwoMath.otf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
)


def _font_path(candidates: Sequence[str]) -> str:
    for candidate in candidates:
        if os.path.isfile(candidate):
            return candidate
    raise RuntimeError("No suitable illustration font is installed")


REGULAR_FONT = _font_path(_REGULAR_CANDIDATES)
BOLD_FONT = _font_path(_BOLD_CANDIDATES)
MATH_FONT = _font_path(_MATH_CANDIDATES)


def font(size: int, *, bold: bool = False, math_face: bool = False) -> ImageFont.FreeTypeFont:
    path = MATH_FONT if math_face else (BOLD_FONT if bold else REGULAR_FONT)
    return ImageFont.truetype(path, size=size)


def hex_rgba(value: str, alpha: int) -> Tuple[int, int, int, int]:
    value = value.lstrip("#")
    return tuple(int(value[index:index + 2], 16) for index in (0, 2, 4)) + (alpha,)


def mix(first: str, second: str, amount: float) -> str:
    def channels(value: str) -> Tuple[int, int, int]:
        value = value.lstrip("#")
        return tuple(int(value[index:index + 2], 16) for index in (0, 2, 4))

    a = channels(first)
    b = channels(second)
    result = tuple(round(x + (y - x) * amount) for x, y in zip(a, b))
    return "#{:02x}{:02x}{:02x}".format(*result)


class Plate:
    """A 1600×1000 paper plate with a consistent Primer visual grammar."""

    def __init__(self, node_id: str, title: str, stage: int):
        self.node_id = node_id
        self.title = title
        self.stage = stage
        self.accent = STAGE_COLORS[stage]
        self.image = Image.new("RGB", (WIDTH, HEIGHT), PAPER)
        self.draw = ImageDraw.Draw(self.image, "RGBA")
        self._paper_texture()
        self.draw.rounded_rectangle(
            (44, 42, WIDTH - 44, HEIGHT - 42), radius=34,
            fill=hex_rgba(PAPER_LIGHT, 226), outline=hex_rgba(EDGE, 150), width=4,
        )
        self.draw.rounded_rectangle(
            (CONTENT[0], CONTENT[1], CONTENT[2], CONTENT[3]), radius=28,
            fill=hex_rgba("#fffaf0", 176), outline=hex_rgba(self.accent, 105), width=3,
        )
        self.text((96, 84), STAGE_NAMES[stage], size=24, bold=True, fill=self.accent)
        self.text((96, 102), title, size=50, bold=True, fill=INK)
        self.draw.line((96, 168, 1504, 168), fill=hex_rgba(self.accent, 150), width=4)

    def _paper_texture(self) -> None:
        seed = int(hashlib.sha256(self.node_id.encode("utf-8")).hexdigest()[:16], 16)
        rng = random.Random(seed)
        for _ in range(1050):
            x = rng.randrange(WIDTH)
            y = rng.randrange(HEIGHT)
            radius = rng.choice((1, 1, 1, 2, 2, 3))
            color = rng.choice(("#806e50", "#ffffff", "#b99d70"))
            self.draw.ellipse(
                (x - radius, y - radius, x + radius, y + radius),
                fill=hex_rgba(color, rng.randrange(8, 22)),
            )

    def text(
        self,
        xy: Tuple[float, float],
        value: str,
        *,
        size: int = 36,
        bold: bool = False,
        math_face: bool = False,
        fill: str = INK,
        anchor: str = "la",
        stroke_width: int = 0,
    ) -> None:
        self.draw.text(
            xy, value, font=font(size, bold=bold, math_face=math_face),
            fill=fill, anchor=anchor, stroke_width=stroke_width,
            stroke_fill=PAPER_LIGHT,
        )

    def wrapped_text(
        self,
        box: Tuple[int, int, int, int],
        value: str,
        *,
        size: int = 32,
        bold: bool = False,
        fill: str = INK,
        line_gap: int = 9,
    ) -> None:
        x0, y0, x1, y1 = box
        face = font(size, bold=bold)
        words = value.split()
        lines: List[str] = []
        current = ""
        for word in words:
            candidate = (current + " " + word).strip()
            if self.draw.textlength(candidate, font=face) <= x1 - x0 or not current:
                current = candidate
            else:
                lines.append(current)
                current = word
        if current:
            lines.append(current)
        line_height = size + line_gap
        block_height = len(lines) * line_height - line_gap
        y = y0 + max(0, (y1 - y0 - block_height) / 2)
        for line in lines:
            self.draw.text((x0, y), line, font=face, fill=fill)
            y += line_height

    def card(
        self,
        box: Tuple[float, float, float, float],
        *,
        fill: str = PAPER_LIGHT,
        outline: str | None = None,
        width: int = 3,
        radius: int = 24,
    ) -> None:
        self.draw.rounded_rectangle(
            box, radius=radius, fill=fill,
            outline=outline or mix(self.accent, PAPER, 0.35), width=width,
        )

    def label(
        self,
        xy: Tuple[float, float],
        value: str,
        *,
        size: int = 28,
        fill: str | None = None,
        text_fill: str = PAPER_LIGHT,
    ) -> None:
        face = font(size, bold=True)
        left, top, right, bottom = self.draw.textbbox(xy, value, font=face, anchor="mm")
        pad_x, pad_y = 18, 10
        self.draw.rounded_rectangle(
            (left - pad_x, top - pad_y, right + pad_x, bottom + pad_y),
            radius=16, fill=fill or self.accent,
        )
        self.draw.text(xy, value, font=face, fill=text_fill, anchor="mm")

    def arrow(
        self,
        start: Tuple[float, float],
        end: Tuple[float, float],
        *,
        fill: str | None = None,
        width: int = 10,
        head: int = 24,
    ) -> None:
        color = fill or self.accent
        x0, y0 = start
        x1, y1 = end
        self.draw.line((x0, y0, x1, y1), fill=color, width=width)
        angle = math.atan2(y1 - y0, x1 - x0)
        left = (
            x1 - head * math.cos(angle - math.pi / 6),
            y1 - head * math.sin(angle - math.pi / 6),
        )
        right = (
            x1 - head * math.cos(angle + math.pi / 6),
            y1 - head * math.sin(angle + math.pi / 6),
        )
        self.draw.polygon((end, left, right), fill=color)

    def double_arrow(
        self,
        start: Tuple[float, float],
        end: Tuple[float, float],
        *,
        fill: str | None = None,
        width: int = 8,
    ) -> None:
        self.arrow(start, end, fill=fill, width=width)
        self.arrow(end, start, fill=fill, width=width)

    def dot(
        self,
        center: Tuple[float, float],
        radius: float = 15,
        *,
        fill: str | None = None,
        outline: str = INK,
        width: int = 3,
    ) -> None:
        x, y = center
        self.draw.ellipse(
            (x - radius, y - radius, x + radius, y + radius),
            fill=fill or self.accent, outline=outline, width=width,
        )

    def axes(
        self,
        box: Tuple[float, float, float, float],
        *,
        x_range: Tuple[float, float] = (-5, 5),
        y_range: Tuple[float, float] = (-5, 5),
        grid_step: float = 1,
        labels: bool = True,
    ) -> Callable[[float, float], Tuple[float, float]]:
        x0, y0, x1, y1 = box
        xmin, xmax = x_range
        ymin, ymax = y_range

        def point(x: float, y: float) -> Tuple[float, float]:
            px = x0 + (x - xmin) / (xmax - xmin) * (x1 - x0)
            py = y1 - (y - ymin) / (ymax - ymin) * (y1 - y0)
            return px, py

        first_x = math.ceil(xmin / grid_step) * grid_step
        value = first_x
        while value <= xmax + 1e-9:
            px, _ = point(value, 0)
            self.draw.line((px, y0, px, y1), fill=hex_rgba(GRID, 150), width=2)
            value += grid_step
        first_y = math.ceil(ymin / grid_step) * grid_step
        value = first_y
        while value <= ymax + 1e-9:
            _, py = point(0, value)
            self.draw.line((x0, py, x1, py), fill=hex_rgba(GRID, 150), width=2)
            value += grid_step
        if xmin <= 0 <= xmax:
            px, _ = point(0, 0)
            self.arrow((px, y1), (px, y0 + 4), fill=INK, width=5, head=18)
        if ymin <= 0 <= ymax:
            _, py = point(0, 0)
            self.arrow((x0, py), (x1 - 4, py), fill=INK, width=5, head=18)
        if labels:
            self.text((x1 - 8, point(0, 0)[1] - 12), "x", size=25, math_face=True, anchor="ra")
            self.text((point(0, 0)[0] + 12, y0 + 8), "y", size=25, math_face=True, anchor="la")
        return point

    def polyline(
        self,
        points: Iterable[Tuple[float, float]],
        *,
        fill: str | None = None,
        width: int = 8,
        joint: str = "curve",
    ) -> None:
        points = list(points)
        if len(points) >= 2:
            self.draw.line(points, fill=fill or self.accent, width=width, joint=joint)

    def dashed_line(
        self,
        start: Tuple[float, float],
        end: Tuple[float, float],
        *,
        fill: str = INK_SOFT,
        width: int = 5,
        dash: int = 18,
        gap: int = 12,
    ) -> None:
        x0, y0 = start
        x1, y1 = end
        distance = math.hypot(x1 - x0, y1 - y0)
        if distance == 0:
            return
        ux, uy = (x1 - x0) / distance, (y1 - y0) / distance
        cursor = 0.0
        while cursor < distance:
            segment_end = min(distance, cursor + dash)
            self.draw.line(
                (x0 + ux * cursor, y0 + uy * cursor,
                 x0 + ux * segment_end, y0 + uy * segment_end),
                fill=fill, width=width,
            )
            cursor += dash + gap

    def save(self, output_root: Path, *, overwrite: bool = False) -> List[Path]:
        stage_dir = output_root / STAGE_DIRS[self.stage] / "math"
        stage_dir.mkdir(parents=True, exist_ok=True)
        stem = self.node_id.replace(".", "-")
        outputs = [stage_dir / (stem + "-1600.webp"), stage_dir / (stem + "-800.webp")]
        if not overwrite:
            existing = [path for path in outputs if path.exists()]
            if existing:
                raise FileExistsError("Refusing to overwrite: {}".format(", ".join(map(str, existing))))
        self.image.save(outputs[0], "WEBP", quality=86, method=6)
        resized = self.image.resize((800, 500), Image.Resampling.LANCZOS)
        resized.save(outputs[1], "WEBP", quality=84, method=6)
        return outputs


Spec = Dict[str, object]


def validate_specs(specs: Dict[str, Spec], expected_ids: Iterable[str] | None = None) -> None:
    if len(specs) != len(set(specs)):
        raise ValueError("Duplicate mathematics illustration specs")
    if expected_ids is not None:
        expected = set(expected_ids)
        actual = set(specs)
        if actual != expected:
            raise ValueError("Spec mismatch; missing={}, extra={}".format(
                sorted(expected - actual), sorted(actual - expected)))
    required = {"id", "title", "stage", "plate_id", "alt", "caption", "draw"}
    for node_id, spec in specs.items():
        if set(spec) != required or spec["id"] != node_id:
            raise ValueError("Malformed illustration spec for {}".format(node_id))
        if not callable(spec["draw"]):
            raise ValueError("{} needs a drawing function".format(node_id))
        if not isinstance(spec["stage"], int) or spec["stage"] not in STAGE_NAMES:
            raise ValueError("{} has an invalid stage".format(node_id))
        for key in ("title", "plate_id", "alt", "caption"):
            if not isinstance(spec[key], str) or not spec[key].strip():
                raise ValueError("{} needs {}".format(node_id, key))


def illustration_entry(spec: Spec) -> Dict[str, object]:
    node_id = str(spec["id"])
    stage = int(spec["stage"])
    stem = node_id.replace(".", "-")
    prefix = "/app/illustrations/{}/math/{}".format(STAGE_DIRS[stage], stem)
    return {
        "id": spec["plate_id"],
        "kind": "illustration",
        "src": prefix + "-800.webp",
        "srcset": "{}-800.webp 800w, {}-1600.webp 1600w".format(prefix, prefix),
        "alt": spec["alt"],
        "caption": spec["caption"],
        "width": 1600,
        "height": 1000,
    }
