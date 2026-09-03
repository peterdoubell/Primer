#!/usr/bin/env python3
"""Render, integrate, and exhaustively verify language and CS illustrations.

The generator owns the previously unillustrated lessons plus the deliberately
upgraded Step by Step plate. Remaining authored media are immutable: a
conflicting entry causes a hard failure instead of replacement.

From the repository root::

    .venv/bin/python tools/generate_language_cs_illustrations.py \
        --render --sync-curriculum --check \
        --contact-sheet /tmp/primer-language-cs-contact-sheet.png
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Dict, Iterable, List, Set, Tuple

from PIL import Image, ImageDraw, ImageFont, ImageOps

from language_cs_illustrations.core import (
    HEIGHT,
    WIDTH,
    Spec,
    asset_paths,
    illustration_entry,
    render_spec,
    validate_specs,
)


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = ROOT / "web" / "illustrations"
CURRICULA = {
    "language": ROOT / "data" / "curriculum" / "02-language.json",
    "computer-science": ROOT / "data" / "curriculum" / "06-computer-science.json",
}
PREEXISTING_ILLUSTRATED_IDS = {
    "lang.0.alphabet",
    "lang.1.reading",
    "cs.1.algorithms",
    "cs.3.data-structures",
    "cs.4.networks",
    "cs.5.complexity",
}


def load_curricula() -> Dict[str, Dict[str, object]]:
    result = {}
    for subject, path in CURRICULA.items():
        with path.open(encoding="utf-8") as handle:
            result[subject] = json.load(handle)
    return result


def all_specs() -> Dict[str, Spec]:
    from language_cs_illustrations.computer_science import SPECS as cs_specs
    from language_cs_illustrations.language import SPECS as language_specs

    overlap = set(language_specs).intersection(cs_specs)
    if overlap:
        raise ValueError("Duplicate language/CS specs: {}".format(sorted(overlap)))
    return dict(language_specs, **cs_specs)


def _node_map(curricula: Dict[str, Dict[str, object]]) -> Dict[str, Dict[str, object]]:
    nodes = {}
    for curriculum in curricula.values():
        for node in curriculum["nodes"]:
            if node["id"] in nodes:
                raise ValueError("Duplicate curriculum node {}".format(node["id"]))
            nodes[node["id"]] = node
    return nodes


def validate_inventory(curricula: Dict[str, Dict[str, object]], specs: Dict[str, Spec]) -> None:
    nodes = _node_map(curricula)
    expected = set(nodes) - PREEXISTING_ILLUSTRATED_IDS
    validate_specs(specs, expected)
    absent_preexisting = PREEXISTING_ILLUSTRATED_IDS - set(nodes)
    if absent_preexisting:
        raise ValueError("Pre-existing node inventory drift: {}".format(sorted(absent_preexisting)))
    for node_id in PREEXISTING_ILLUSTRATED_IDS:
        illustrations = [item for item in nodes[node_id].get("lesson_media", [])
                         if item.get("kind") == "illustration"]
        if len(illustrations) != 1:
            raise ValueError("Authored illustration missing or duplicated for {}".format(node_id))
    for node_id, item in specs.items():
        node = nodes[node_id]
        if item["title"] != node["title"] or item["stage"] != node["stage"]:
            raise ValueError("Spec metadata drift for {}".format(node_id))
        existing = [media for media in node.get("lesson_media", [])
                    if media.get("kind") == "illustration"]
        expected_entry = illustration_entry(item)
        if existing and existing != [expected_entry]:
            current = existing[0] if len(existing) == 1 else {}
            if (current.get("id"), current.get("src")) != (
                    expected_entry["id"], expected_entry["src"]):
                raise ValueError("Refusing to replace authored illustration for {}".format(node_id))


def render_assets(specs: Dict[str, Spec], overwrite: bool) -> List[Path]:
    if not overwrite:
        collisions = [path for item in specs.values() for path in asset_paths(OUTPUT_ROOT, item)
                      if path.exists()]
        if collisions:
            raise FileExistsError(
                "Refusing to overwrite {} existing outputs; first paths: {}".format(
                    len(collisions), collisions[:5]))
    outputs = []
    for item in specs.values():
        outputs.extend(render_spec(OUTPUT_ROOT, item, overwrite=overwrite))
    return outputs


def sync_curricula(curricula: Dict[str, Dict[str, object]], specs: Dict[str, Spec]) -> int:
    changed = 0
    for subject, curriculum in curricula.items():
        subject_changed = False
        for node in curriculum["nodes"]:
            node_id = node["id"]
            if node_id not in specs:
                continue
            expected = illustration_entry(specs[node_id])
            media = node.setdefault("lesson_media", [])
            illustrations = [item for item in media if item.get("kind") == "illustration"]
            if illustrations:
                if illustrations == [expected]:
                    continue
                # Metadata for an owned plate may evolve during an audited
                # revision, but only when both its stable id and local fallback
                # prove that it is ours.  A different authored plate is never
                # overwritten.
                current = illustrations[0] if len(illustrations) == 1 else {}
                if (current.get("id"), current.get("src")) != (
                        expected["id"], expected["src"]):
                    raise ValueError("Refusing to replace authored illustration for {}".format(node_id))
                media[media.index(illustrations[0])] = expected
                changed += 1
                subject_changed = True
                continue
            media.insert(0, expected)
            changed += 1
            subject_changed = True
        if subject_changed:
            with CURRICULA[subject].open("w", encoding="utf-8") as handle:
                json.dump(curriculum, handle, indent=1, ensure_ascii=False)
                handle.write("\n")
    return changed


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_assets(curricula: Dict[str, Dict[str, object]]) -> None:
    nodes = _node_map(curricula)
    seen_paths: Set[Path] = set()
    seen_hashes: Dict[str, Path] = {}
    seen_alt: Set[str] = set()
    seen_caption: Set[str] = set()
    failures = []
    for node_id, node in nodes.items():
        plates = [item for item in node.get("lesson_media", [])
                  if item.get("kind") == "illustration"]
        if len(plates) != 1:
            failures.append(node_id)
            continue
        plate = plates[0]
        if (plate.get("width"), plate.get("height")) != (WIDTH, HEIGHT):
            raise ValueError("Bad declared dimensions for {}".format(node_id))
        if not isinstance(plate.get("alt"), str) or len(plate["alt"]) < 40:
            raise ValueError("Missing descriptive alt for {}".format(node_id))
        if not isinstance(plate.get("caption"), str) or len(plate["caption"]) < 45:
            raise ValueError("Missing explanatory caption for {}".format(node_id))
        if plate["alt"] in seen_alt or plate["caption"] in seen_caption:
            raise ValueError("Duplicate alt or caption at {}".format(node_id))
        seen_alt.add(plate["alt"])
        seen_caption.add(plate["caption"])

        candidates = plate.get("srcset", "").split(",")
        if len(candidates) != 2:
            raise ValueError("Expected exactly two responsive candidates for {}".format(node_id))
        urls = []
        widths = set()
        for candidate in candidates:
            parts = candidate.strip().split()
            if len(parts) != 2 or not parts[1].endswith("w"):
                raise ValueError("Malformed srcset candidate for {}".format(node_id))
            url, descriptor = parts
            declared_width = int(descriptor[:-1])
            path = ROOT / "web" / url.removeprefix("/app/")
            if path in seen_paths:
                raise ValueError("Raster path reused by multiple lessons: {}".format(path))
            if not path.is_file():
                raise FileNotFoundError(path)
            with Image.open(path) as opened:
                if opened.format != "WEBP":
                    raise ValueError("Expected WebP at {}".format(path))
                actual_width, actual_height = opened.size
                if actual_width != declared_width or actual_width * HEIGHT != actual_height * WIDTH:
                    raise ValueError("Bad raster dimensions for {}".format(path))
            size = path.stat().st_size
            if size < 7_500 or size >= 400_000:
                raise ValueError("Unreasonable illustration size {} bytes: {}".format(size, path))
            payload_hash = _sha256(path)
            if payload_hash in seen_hashes:
                raise ValueError("Duplicate raster payload: {} and {}".format(
                    seen_hashes[payload_hash], path))
            seen_hashes[payload_hash] = path
            seen_paths.add(path)
            urls.append(url)
            widths.add(declared_width)
        if widths != {800, 1600}:
            raise ValueError("Responsive widths must be 800 and 1600 for {}".format(node_id))
        if plate.get("src") not in urls:
            raise ValueError("Fallback source missing from srcset for {}".format(node_id))
    if failures:
        raise ValueError("Nodes without exactly one illustration: {}".format(failures))
    expected_rasters = len(nodes) * 2
    if len(seen_paths) != expected_rasters:
        raise ValueError("Expected {} unique rasters, found {}".format(
            expected_rasters, len(seen_paths)))


def verify_determinism(specs: Dict[str, Spec]) -> None:
    """Regenerate every owned raster twice and compare both runs and checked-in bytes."""

    with tempfile.TemporaryDirectory(prefix="primer-language-cs-a-") as first_name, \
            tempfile.TemporaryDirectory(prefix="primer-language-cs-b-") as second_name:
        first_root = Path(first_name)
        second_root = Path(second_name)
        for node_id, item in specs.items():
            first = render_spec(first_root, item)
            second = render_spec(second_root, item)
            checked_in = asset_paths(OUTPUT_ROOT, item)
            for first_path, second_path, actual_path in zip(first, second, checked_in):
                hashes = {_sha256(first_path), _sha256(second_path), _sha256(actual_path)}
                if len(hashes) != 1:
                    raise ValueError("Non-deterministic regeneration for {}".format(node_id))


def write_contact_sheet(curricula: Dict[str, Dict[str, object]], destination: Path) -> None:
    nodes = [node for curriculum in curricula.values() for node in curriculum["nodes"]]
    thumb_w, thumb_h = 320, 200
    columns = 5
    rows = (len(nodes) + columns - 1) // columns
    label_h = 40
    sheet = Image.new("RGB", (columns * thumb_w, rows * (thumb_h + label_h)), "#efe7d2")
    draw = ImageDraw.Draw(sheet)
    font_path = ("/System/Library/Fonts/Supplemental/Arial.ttf"
                 if os.path.isfile("/System/Library/Fonts/Supplemental/Arial.ttf")
                 else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    face = ImageFont.truetype(font_path, 17)
    for index, node in enumerate(nodes):
        plate = next(item for item in node["lesson_media"] if item["kind"] == "illustration")
        source = ROOT / "web" / plate["src"].removeprefix("/app/")
        with Image.open(source) as opened:
            thumb = ImageOps.fit(opened.convert("RGB"), (thumb_w, thumb_h),
                                 method=Image.Resampling.LANCZOS)
        x = index % columns * thumb_w
        y = index // columns * (thumb_h + label_h)
        sheet.paste(thumb, (x, y))
        draw.text((x + 8, y + thumb_h + 9), node["id"], font=face, fill="#24303a")
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
    curricula = load_curricula()
    specs = all_specs()
    validate_inventory(curricula, specs)
    if args.render:
        outputs = render_assets(specs, args.overwrite)
        print("Rendered {} language and computer-science illustration files".format(len(outputs)))
    if args.sync_curriculum:
        print("Synchronized illustrations for {} curriculum nodes".format(
            sync_curricula(curricula, specs)))
        curricula = load_curricula()
    if args.check:
        verify_assets(curricula)
        print("Verified {} lesson illustration pairs".format(len(_node_map(curricula))))
    if args.check_determinism:
        verify_determinism(specs)
        print("Verified deterministic regeneration for {} owned pairs".format(len(specs)))
    if args.contact_sheet:
        write_contact_sheet(curricula, args.contact_sheet)
        print("Wrote {}".format(args.contact_sheet))
    if not any((args.render, args.sync_curriculum, args.check,
                args.check_determinism, args.contact_sheet)):
        print("{} generated specs cover {} total lessons with {} preserved plates".format(
            len(specs), len(_node_map(curricula)), len(PREEXISTING_ILLUSTRATED_IDS)))


if __name__ == "__main__":
    main()
