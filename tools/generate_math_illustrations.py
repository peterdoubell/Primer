#!/usr/bin/env python3
"""Render, integrate, and verify the complete mathematics illustration set.

Usage from the repository root::

    python3 tools/generate_math_illustrations.py --render --overwrite
    python3 tools/generate_math_illustrations.py --sync-curriculum --check

All 54 generated concept diagrams are deterministic so their mathematical relationships,
labels, and boundary cases can be audited and reproduced exactly.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

from PIL import Image, ImageDraw, ImageFont, ImageOps

from math_illustrations.core import (
    HEIGHT,
    STAGE_DIRS,
    WIDTH,
    Plate,
    Spec,
    illustration_entry,
    validate_specs,
)


ROOT = Path(__file__).resolve().parents[1]
CURRICULUM_PATH = ROOT / "data" / "curriculum" / "01-mathematics.json"
OUTPUT_ROOT = ROOT / "web" / "illustrations"
PREEXISTING_ILLUSTRATED_IDS = {
    "math.0.counting",
    "math.0.shapes",
    "math.1.addition",
    "math.2.fractions",
    "math.5.pde",
}


def load_curriculum() -> Dict[str, object]:
    with CURRICULUM_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


def all_specs() -> Dict[str, Spec]:
    from math_illustrations.advanced import SPECS as advanced
    from math_illustrations.early import SPECS as early
    from math_illustrations.middle import SPECS as middle

    specs: Dict[str, Spec] = {}
    for cohort in (early, middle, advanced):
        overlap = set(specs).intersection(cohort)
        if overlap:
            raise ValueError("Duplicate cohort specs: {}".format(sorted(overlap)))
        specs.update(cohort)
    return specs


def validate_inventory(curriculum: Dict[str, object], specs: Dict[str, Spec]) -> None:
    nodes = curriculum["nodes"]
    math_ids = {node["id"] for node in nodes}
    expected = math_ids - PREEXISTING_ILLUSTRATED_IDS
    validate_specs(specs, expected)
    for node in nodes:
        node_id = node["id"]
        if node_id in specs:
            spec = specs[node_id]
            if spec["title"] != node["title"] or spec["stage"] != node["stage"]:
                raise ValueError("Spec metadata drift for {}".format(node_id))


def _paths(spec: Spec) -> Tuple[Path, Path]:
    stage_dir = OUTPUT_ROOT / STAGE_DIRS[int(spec["stage"])] / "math"
    stem = str(spec["id"]).replace(".", "-")
    return stage_dir / (stem + "-1600.webp"), stage_dir / (stem + "-800.webp")


def render_assets(specs: Dict[str, Spec], overwrite: bool) -> List[Path]:
    if not overwrite:
        collisions = [path for spec in specs.values() for path in _paths(spec) if path.exists()]
        if collisions:
            raise FileExistsError(
                "Refusing to overwrite {} existing outputs; first paths: {}".format(
                    len(collisions), collisions[:5]))

    outputs: List[Path] = []
    for node_id, spec in specs.items():
        plate = Plate(node_id, str(spec["title"]), int(spec["stage"]))
        spec["draw"](plate)
        outputs.extend(plate.save(OUTPUT_ROOT, overwrite=overwrite))
    return outputs


def sync_curriculum(curriculum: Dict[str, object], specs: Dict[str, Spec]) -> int:
    changed = 0
    for node in curriculum["nodes"]:
        node_id = node["id"]
        if node_id not in specs:
            continue
        media = node.setdefault("lesson_media", [])
        illustrations = [item for item in media if item.get("kind") == "illustration"]
        if illustrations:
            if illustrations != [illustration_entry(specs[node_id])]:
                raise ValueError("Refusing to replace authored illustration for {}".format(node_id))
            continue
        media.insert(0, illustration_entry(specs[node_id]))
        changed += 1
    if changed:
        with CURRICULUM_PATH.open("w", encoding="utf-8") as handle:
            json.dump(curriculum, handle, indent=1, ensure_ascii=False)
            handle.write("\n")
    return changed


def verify(curriculum: Dict[str, object]) -> None:
    missing: List[str] = []
    seen_paths = set()
    for node in curriculum["nodes"]:
        plates = [item for item in node.get("lesson_media", []) if item.get("kind") == "illustration"]
        if len(plates) != 1:
            missing.append(node["id"])
            continue
        plate = plates[0]
        if (plate["width"], plate["height"]) != (WIDTH, HEIGHT):
            raise ValueError("Bad declared dimensions for {}".format(node["id"]))
        for candidate in plate["srcset"].split(","):
            url, descriptor = candidate.strip().split()
            path = ROOT / "web" / url.removeprefix("/app/")
            if not path.is_file():
                raise FileNotFoundError(path)
            with Image.open(path) as image:
                width, height = image.size
                if width != int(descriptor[:-1]) or width * HEIGHT != height * WIDTH:
                    raise ValueError("Bad raster dimensions for {}".format(path))
            if path.stat().st_size >= 300_000:
                raise ValueError("Oversize illustration {}".format(path))
            seen_paths.add(path)
        if plate["src"] not in {part.strip().split()[0] for part in plate["srcset"].split(",")}:
            raise ValueError("Fallback missing from srcset for {}".format(node["id"]))
    if missing:
        raise ValueError("Mathematics nodes without exactly one illustration: {}".format(missing))
    if len(seen_paths) != len(curriculum["nodes"]) * 2:
        raise ValueError("Expected two unique rasters per mathematics node")


def write_contact_sheet(curriculum: Dict[str, object], destination: Path) -> None:
    thumb_w, thumb_h = 320, 200
    columns = 5
    rows = (len(curriculum["nodes"]) + columns - 1) // columns
    label_h = 38
    sheet = Image.new("RGB", (columns * thumb_w, rows * (thumb_h + label_h)), "#efe7d2")
    draw = ImageDraw.Draw(sheet)
    face = ImageFont.truetype(
        "/System/Library/Fonts/Supplemental/Arial.ttf"
        if os.path.isfile("/System/Library/Fonts/Supplemental/Arial.ttf")
        else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        18,
    )
    for index, node in enumerate(curriculum["nodes"]):
        plate = next(item for item in node["lesson_media"] if item["kind"] == "illustration")
        source = ROOT / "web" / plate["src"].removeprefix("/app/")
        with Image.open(source) as opened:
            thumb = ImageOps.fit(opened.convert("RGB"), (thumb_w, thumb_h), method=Image.Resampling.LANCZOS)
        x = index % columns * thumb_w
        y = index // columns * (thumb_h + label_h)
        sheet.paste(thumb, (x, y))
        draw.text((x + 8, y + thumb_h + 8), node["id"], font=face, fill="#24303a")
    destination.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(destination)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--render", action="store_true")
    parser.add_argument("--sync-curriculum", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--contact-sheet", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    curriculum = load_curriculum()
    specs = all_specs()
    validate_inventory(curriculum, specs)
    if args.render:
        outputs = render_assets(specs, args.overwrite)
        print("Rendered {} mathematics illustration files".format(len(outputs)))
    if args.sync_curriculum:
        print("Added illustrations to {} curriculum nodes".format(sync_curriculum(curriculum, specs)))
        curriculum = load_curriculum()
    if args.check:
        verify(curriculum)
        print("Verified {} mathematics illustration pairs".format(len(curriculum["nodes"])))
    if args.contact_sheet:
        write_contact_sheet(curriculum, args.contact_sheet)
        print("Wrote {}".format(args.contact_sheet))
    if not any((args.render, args.sync_curriculum, args.check, args.contact_sheet)):
        print("{} new specs cover {} total mathematics modules".format(
            len(specs), len(curriculum["nodes"])))


if __name__ == "__main__":
    main()
