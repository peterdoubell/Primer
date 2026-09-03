#!/usr/bin/env python3
"""Render, bind, and exhaustively verify every radiology reasoning plate."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Dict, List, Tuple

from PIL import Image, ImageDraw, ImageFont, ImageOps

from math_illustrations.core import HEIGHT, WIDTH
from radiology_illustrations.core import (
    Spec,
    asset_paths,
    illustration_entry,
    render_spec,
    validate_specs,
)
from radiology_illustrations.specs import SPECS as RAW_SPECS


ROOT = Path(__file__).resolve().parents[1]
CURRICULUM_PATH = ROOT / "data" / "curriculum" / "11-radiology.json"
OUTPUT_ROOT = ROOT / "web" / "illustrations"
PREEXISTING_IDS = {"rad.3.ct-image"}


def load_curriculum() -> Dict[str, object]:
    with CURRICULUM_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


def bound_specs(curriculum: Dict[str, object]) -> Dict[str, Spec]:
    nodes = {node["id"]: node for node in curriculum["nodes"]}
    specs = copy.deepcopy(RAW_SPECS)
    for node_id, item in specs.items():
        node = nodes[node_id]
        item["title"] = node["title"]
        item["stage"] = node["stage"]
    return specs


def validate_inventory(curriculum: Dict[str, object], specs: Dict[str, Spec]) -> None:
    nodes = curriculum["nodes"]
    all_ids = {node["id"] for node in nodes}
    illustrated = {
        node["id"] for node in nodes
        if any(entry.get("kind") == "illustration"
               for entry in node.get("lesson_media", []))
    }
    if illustrated != PREEXISTING_IDS:
        # Once synced, all nodes are illustrated; permit that exact end state.
        if illustrated != all_ids:
            raise ValueError("Unexpected pre-existing radiology plates: {}".format(
                sorted(illustrated - PREEXISTING_IDS)))
    validate_specs(specs, all_ids - PREEXISTING_IDS)
    for node_id, item in specs.items():
        node = next(node for node in nodes if node["id"] == node_id)
        if item["title"] != node["title"] or item["stage"] != node["stage"]:
            raise ValueError("Radiology metadata drift for {}".format(node_id))


def render_assets(specs: Dict[str, Spec], overwrite: bool) -> List[Path]:
    if not overwrite:
        collisions = [
            path for item in specs.values()
            for path in asset_paths(OUTPUT_ROOT, str(item["id"]), int(item["stage"]))
            if path.exists()
        ]
        if collisions:
            raise FileExistsError("Refusing to overwrite {} radiology assets".format(
                len(collisions)))
    outputs: List[Path] = []
    for item in specs.values():
        outputs.extend(render_spec(OUTPUT_ROOT, item, overwrite=overwrite))
    return outputs


def sync_curriculum(curriculum: Dict[str, object], specs: Dict[str, Spec]) -> int:
    changed = 0
    for node in curriculum["nodes"]:
        item = specs.get(node["id"])
        if item is None:
            continue
        media = node.setdefault("lesson_media", [])
        illustrations = [entry for entry in media if entry.get("kind") == "illustration"]
        expected = illustration_entry(item)
        if illustrations:
            if illustrations == [expected]:
                continue
            current = illustrations[0] if len(illustrations) == 1 else None
            # Specs never include the separately preserved CT phantom. A
            # stable generated id and local source therefore prove ownership
            # while still failing closed around genuinely authored media.
            if (current is None or current.get("id") != expected["id"]
                    or current.get("src") != expected["src"]):
                raise ValueError("Refusing to replace authored plate for {}".format(node["id"]))
            media[media.index(current)] = expected
        else:
            media.insert(0, expected)
        changed += 1
    if changed:
        with CURRICULUM_PATH.open("w", encoding="utf-8") as handle:
            json.dump(curriculum, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
    return changed


def verify(curriculum: Dict[str, object]) -> None:
    nodes = curriculum["nodes"]
    if len(nodes) != 84:
        raise ValueError("Expected 84 radiology lessons, found {}".format(len(nodes)))
    urls = set()
    media_ids = set()
    for node in nodes:
        plates = [entry for entry in node.get("lesson_media", [])
                  if entry.get("kind") == "illustration"]
        if len(plates) != 1:
            raise ValueError("{} needs exactly one illustration".format(node["id"]))
        plate = plates[0]
        if plate["id"] in media_ids:
            raise ValueError("Duplicate radiology media id {}".format(plate["id"]))
        media_ids.add(plate["id"])
        if (plate["width"], plate["height"]) != (WIDTH, HEIGHT):
            raise ValueError("Bad dimensions for {}".format(node["id"]))
        if plate["alt"] == plate["caption"] or min(
                len(str(plate[key]).split()) for key in ("alt", "caption")) < 8:
            raise ValueError("{} needs explanatory, distinct copy".format(node["id"]))
        candidates = plate["srcset"].split(",")
        local_urls = set()
        for candidate in candidates:
            url, descriptor = candidate.strip().split()
            if url in urls:
                raise ValueError("Raster URL reused at {}".format(node["id"]))
            urls.add(url)
            local_urls.add(url)
            path = ROOT / "web" / url.removeprefix("/app/")
            if not path.is_file():
                raise FileNotFoundError(path)
            with Image.open(path) as opened:
                width, height = opened.size
                if opened.format != "WEBP" or width != int(descriptor[:-1]):
                    raise ValueError("Bad WebP contract for {}".format(path))
                if width * HEIGHT != height * WIDTH:
                    raise ValueError("Bad aspect ratio for {}".format(path))
            if path.stat().st_size >= 300_000:
                raise ValueError("Oversize radiology plate {}".format(path))
        if len(local_urls) != 2 or plate["src"] not in local_urls:
            raise ValueError("{} needs two responsive sources".format(node["id"]))
    if len(urls) != 168:
        raise ValueError("Expected 168 radiology rasters, found {}".format(len(urls)))


def verify_determinism(specs: Dict[str, Spec]) -> None:
    with tempfile.TemporaryDirectory(prefix="primer-radiology-determinism-") as temporary:
        destination = Path(temporary)
        for item in specs.values():
            generated = render_spec(destination, item)
            committed = asset_paths(OUTPUT_ROOT, str(item["id"]), int(item["stage"]))
            for fresh, current in zip(generated, committed):
                if hashlib.sha256(fresh.read_bytes()).digest() != \
                        hashlib.sha256(current.read_bytes()).digest():
                    raise ValueError("Non-deterministic radiology asset {}".format(current))


def write_contact_sheet(curriculum: Dict[str, object], destination: Path) -> None:
    thumb_w, thumb_h, label_h, columns = 320, 200, 38, 5
    rows = (len(curriculum["nodes"]) + columns - 1) // columns
    sheet = Image.new("RGB", (columns * thumb_w, rows * (thumb_h + label_h)), "#efe7d2")
    draw = ImageDraw.Draw(sheet)
    font_path = ("/System/Library/Fonts/Supplemental/Arial.ttf"
                 if os.path.isfile("/System/Library/Fonts/Supplemental/Arial.ttf")
                 else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    face = ImageFont.truetype(font_path, 17)
    for index, node in enumerate(curriculum["nodes"]):
        plate = next(entry for entry in node["lesson_media"]
                     if entry["kind"] == "illustration")
        source = ROOT / "web" / plate["src"].removeprefix("/app/")
        with Image.open(source) as opened:
            thumb = ImageOps.fit(opened.convert("RGB"), (thumb_w, thumb_h),
                                 method=Image.Resampling.LANCZOS)
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
    parser.add_argument("--check-determinism", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--contact-sheet", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    curriculum = load_curriculum()
    specs = bound_specs(curriculum)
    validate_inventory(curriculum, specs)
    if args.render:
        print("Rendered {} radiology files".format(
            len(render_assets(specs, args.overwrite))))
    if args.sync_curriculum:
        print("Synced {} radiology media entries".format(
            sync_curriculum(curriculum, specs)))
        curriculum = load_curriculum()
    if args.check:
        verify(curriculum)
        print("Verified 84 radiology lessons and 168 responsive WebPs")
    if args.check_determinism:
        verify_determinism(specs)
        print("Verified deterministic radiology regeneration")
    if args.contact_sheet:
        write_contact_sheet(curriculum, args.contact_sheet)
        print("Wrote {}".format(args.contact_sheet))


if __name__ == "__main__":
    main()
