#!/usr/bin/env python3
"""Render, integrate, and exhaustively verify natural-science lesson plates.

This covers every previously unillustrated lesson in Life Sciences, Chemistry,
and Earth & Space while leaving all eight pre-existing authored media pairs
byte-for-byte unchanged in curriculum metadata and on disk.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
from typing import Dict, List, Mapping, Tuple

from PIL import Image, ImageDraw, ImageFont, ImageOps

from natural_science_illustrations.core import (
    HEIGHT,
    WIDTH,
    Spec,
    asset_paths,
    encoded_pair,
    illustration_entry,
    render_spec,
    validate_specs,
)


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = ROOT / "web" / "illustrations"

CURRICULA = {
    "biology": ROOT / "data" / "curriculum" / "04-life-sciences.json",
    "chemistry": ROOT / "data" / "curriculum" / "05-chemistry.json",
    "earth-space": ROOT / "data" / "curriculum" / "08-earth-space.json",
}

EXPECTED_NODE_COUNTS = {"biology": 37, "chemistry": 29, "earth-space": 27}

PREEXISTING_ILLUSTRATED_IDS = {
    "bio.1.lifecycles",
    "bio.2.cells",
    "bio.3.human-anatomy",
    "bio.4.molecular",
    "bio.5.developmental",
    "chem.2.atoms",
    "earth.0.sky",
    "earth.1.seasons",
}

# Canonical hashes freeze the exact lesson_media arrays present before this
# generator was introduced.  They guard both model props and authored copy.
PREEXISTING_MEDIA_SHA256 = {
    "bio.1.lifecycles": "297f75bec1c2e0e2e4bad082bdc46f1dc0fe33711a41ae725c9234002d8a587e",
    "bio.2.cells": "e47f62ed2371f5e535a404b3c51dafbae4bfe57b421282beb0079a879c4789d0",
    "bio.3.human-anatomy": "645a88c68ca096d999f41d6e6a67656a70d4addc60d931f1b56d46d54b590ba3",
    "bio.4.molecular": "f58ba195db4316f71d51d749b8aeb13bcf01f1335ae1a1be02ce2e86f5502d6b",
    "bio.5.developmental": "ce68c1dc73c1d007cf0dbc05f465b182c62d80f8e5ddbe6f7aa1a01d69d4c6da",
    "chem.2.atoms": "10990c3b7eb1d310b57265d3fd07aaf2d7e41c7217ffa723e44645c5b8b055cd",
    "earth.0.sky": "290f4f1ac53bbcf443df76b46a4fdcfa64a6d56e869711b84331011c848d5816",
    "earth.1.seasons": "2fba277e801cec581c67c1403b08be60cefb18d7dc6338b5fbe5397be7efc3d9",
}


def canonical_media_hash(media: object) -> str:
    raw = json.dumps(media, sort_keys=True, separators=(",", ":"),
                     ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def load_curricula() -> Dict[str, Dict[str, object]]:
    result = {}
    for domain, path in CURRICULA.items():
        with path.open(encoding="utf-8") as handle:
            result[domain] = json.load(handle)
    return result


def all_specs() -> Dict[str, Spec]:
    from natural_science_illustrations.biology import SPECS as biology
    from natural_science_illustrations.chemistry import SPECS as chemistry
    from natural_science_illustrations.earth_space import SPECS as earth_space

    result: Dict[str, Spec] = {}
    for cohort in (biology, chemistry, earth_space):
        overlap = set(result).intersection(cohort)
        if overlap:
            raise ValueError("Duplicate natural-science specs: {}".format(sorted(overlap)))
        result.update(cohort)
    return result


def validate_inventory(curricula: Mapping[str, Dict[str, object]],
                       specs: Mapping[str, Spec]) -> None:
    all_nodes = []
    for domain, curriculum in curricula.items():
        nodes = curriculum["nodes"]
        if len(nodes) != EXPECTED_NODE_COUNTS[domain]:
            raise ValueError("{} lesson count drifted from {} to {}".format(
                domain, EXPECTED_NODE_COUNTS[domain], len(nodes)))
        all_nodes.extend(nodes)
    ids = {node["id"] for node in all_nodes}
    expected = ids - PREEXISTING_ILLUSTRATED_IDS
    validate_specs(specs, expected)
    if set(PREEXISTING_MEDIA_SHA256) != PREEXISTING_ILLUSTRATED_IDS:
        raise ValueError("Pre-existing media hash inventory is incomplete")
    for domain, curriculum in curricula.items():
        for node in curriculum["nodes"]:
            node_id = node["id"]
            if node_id in specs:
                item = specs[node_id]
                if (item["title"] != node["title"] or item["stage"] != node["stage"]
                        or item["domain"] != domain):
                    raise ValueError("Spec metadata drift for {}".format(node_id))
            elif node_id not in PREEXISTING_ILLUSTRATED_IDS:
                raise ValueError("Unaccounted natural-science lesson {}".format(node_id))


def verify_preexisting(curricula: Mapping[str, Dict[str, object]]) -> None:
    found = set()
    for curriculum in curricula.values():
        for node in curriculum["nodes"]:
            node_id = node["id"]
            if node_id not in PREEXISTING_ILLUSTRATED_IDS:
                continue
            found.add(node_id)
            actual = canonical_media_hash(node.get("lesson_media", []))
            if actual != PREEXISTING_MEDIA_SHA256[node_id]:
                raise ValueError("Authored lesson media changed for {}".format(node_id))
    if found != PREEXISTING_ILLUSTRATED_IDS:
        raise ValueError("Missing authored media nodes: {}".format(
            sorted(PREEXISTING_ILLUSTRATED_IDS - found)))


def render_assets(specs: Mapping[str, Spec], overwrite: bool) -> List[Path]:
    if not overwrite:
        collisions = [path for item in specs.values() for path in asset_paths(OUTPUT_ROOT, item)
                      if path.exists()]
        if collisions:
            raise FileExistsError("Refusing to overwrite {} generated assets; first: {}".format(
                len(collisions), collisions[:5]))
    outputs = []
    for item in specs.values():
        outputs.extend(render_spec(OUTPUT_ROOT, item, overwrite=overwrite))
    return outputs


def sync_curricula(curricula: Mapping[str, Dict[str, object]],
                    specs: Mapping[str, Spec]) -> int:
    authored_before = {}
    for curriculum in curricula.values():
        for node in curriculum["nodes"]:
            if node["id"] in PREEXISTING_ILLUSTRATED_IDS:
                authored_before[node["id"]] = copy.deepcopy(node["lesson_media"])

    additions = 0
    changed_domains = set()
    for domain, curriculum in curricula.items():
        for node in curriculum["nodes"]:
            node_id = node["id"]
            if node_id not in specs:
                continue
            media = node.setdefault("lesson_media", [])
            illustrations = [entry for entry in media if entry.get("kind") == "illustration"]
            expected = illustration_entry(specs[node_id])
            if illustrations:
                # Nodes in ``specs`` are generator-owned (the separately
                # checksummed authored cohort is excluded above), so a source
                # correction must be allowed to refresh its metadata without
                # disturbing companion media such as interactive models.
                if len(illustrations) != 1:
                    raise ValueError("Expected one generated illustration for {}".format(node_id))
                if illustrations != [expected]:
                    position = media.index(illustrations[0])
                    media[position] = expected
                    additions += 1
                    changed_domains.add(domain)
                continue
            media.insert(0, expected)
            additions += 1
            changed_domains.add(domain)

    for curriculum in curricula.values():
        for node in curriculum["nodes"]:
            if node["id"] in authored_before and node["lesson_media"] != authored_before[node["id"]]:
                raise AssertionError("Sync mutated authored media for {}".format(node["id"]))

    for domain in changed_domains:
        with CURRICULA[domain].open("w", encoding="utf-8") as handle:
            json.dump(curricula[domain], handle, indent=1, ensure_ascii=False)
            handle.write("\n")
    return additions


def verify(curricula: Mapping[str, Dict[str, object]], specs: Mapping[str, Spec],
           check_determinism: bool = True) -> None:
    verify_preexisting(curricula)
    seen_urls = set()
    seen_media_ids = set()
    seen_alt = set()
    seen_caption = set()
    generated_hashes = set()
    lesson_count = 0

    for domain, curriculum in curricula.items():
        for node in curriculum["nodes"]:
            lesson_count += 1
            node_id = node["id"]
            illustrations = [entry for entry in node.get("lesson_media", [])
                             if entry.get("kind") == "illustration"]
            if len(illustrations) != 1:
                raise ValueError("{} needs exactly one illustration".format(node_id))
            plate = illustrations[0]
            if node_id in specs and plate != illustration_entry(specs[node_id]):
                raise ValueError("Generated illustration metadata drift for {}".format(node_id))
            if plate["id"] in seen_media_ids:
                raise ValueError("Duplicate illustration id {}".format(plate["id"]))
            seen_media_ids.add(plate["id"])
            if (plate["width"], plate["height"]) != (WIDTH, HEIGHT):
                raise ValueError("Bad declared dimensions for {}".format(node_id))
            if plate["alt"] == plate["caption"]:
                raise ValueError("Alt duplicates caption for {}".format(node_id))
            if plate["alt"] in seen_alt or plate["caption"] in seen_caption:
                raise ValueError("Repeated alt or caption at {}".format(node_id))
            seen_alt.add(plate["alt"]); seen_caption.add(plate["caption"])

            candidates = plate["srcset"].split(",")
            if len(candidates) != 2:
                raise ValueError("{} needs exactly two responsive candidates".format(node_id))
            urls = set()
            for candidate in candidates:
                url, descriptor = candidate.strip().split()
                if url in seen_urls:
                    raise ValueError("Raster URL reused at {}".format(node_id))
                seen_urls.add(url); urls.add(url)
                path = ROOT / "web" / url.removeprefix("/app/")
                if not path.is_file():
                    raise FileNotFoundError(path)
                with Image.open(path) as opened:
                    width, height = opened.size
                    if opened.format != "WEBP":
                        raise ValueError("Not a WebP: {}".format(path))
                    if width != int(descriptor[:-1]) or width * HEIGHT != height * WIDTH:
                        raise ValueError("Bad raster dimensions for {}".format(path))
                size = path.stat().st_size
                if not 3_000 <= size < 300_000:
                    raise ValueError("Implausible illustration size {} for {}".format(size, path))
            if len(urls) != 2 or plate["src"] not in urls or not plate["src"].endswith("-800.webp"):
                raise ValueError("{} has invalid responsive fallback".format(node_id))

            if node_id in specs and check_determinism:
                first = encoded_pair(specs[node_id])
                second = encoded_pair(specs[node_id])
                if first != second:
                    raise ValueError("Non-deterministic rendering for {}".format(node_id))
                paths = asset_paths(OUTPUT_ROOT, specs[node_id])
                disk = (paths[0].read_bytes(), paths[1].read_bytes())
                if first != disk:
                    raise ValueError("Generated raster does not match source for {}".format(node_id))
                for payload in first:
                    digest = hashlib.sha256(payload).hexdigest()
                    if digest in generated_hashes:
                        raise ValueError("Generated raster content reused at {}".format(node_id))
                    generated_hashes.add(digest)

    expected_lessons = sum(EXPECTED_NODE_COUNTS.values())
    if lesson_count != expected_lessons:
        raise ValueError("Expected {} lessons, found {}".format(expected_lessons, lesson_count))
    if len(seen_urls) != expected_lessons * 2:
        raise ValueError("Expected {} responsive rasters, found {}".format(
            expected_lessons * 2, len(seen_urls)))
    if check_determinism and len(generated_hashes) != len(specs) * 2:
        raise ValueError("Generated raster uniqueness check is incomplete")


def write_contact_sheet(specs: Mapping[str, Spec], destination: Path) -> None:
    thumb_w, thumb_h, label_h, columns = 320, 200, 38, 5
    items = sorted(specs.values(), key=lambda item: (str(item["domain"]), int(item["stage"]), str(item["id"])))
    rows = (len(items) + columns - 1) // columns
    sheet = Image.new("RGB", (columns * thumb_w, rows * (thumb_h + label_h)), "#efe7d2")
    draw = ImageDraw.Draw(sheet)
    font_path = ("/System/Library/Fonts/Supplemental/Arial.ttf"
                 if os.path.isfile("/System/Library/Fonts/Supplemental/Arial.ttf")
                 else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    face = ImageFont.truetype(font_path, 17)
    for index, item in enumerate(items):
        source = asset_paths(OUTPUT_ROOT, item)[1]
        with Image.open(source) as opened:
            thumb = ImageOps.fit(opened.convert("RGB"), (thumb_w, thumb_h),
                                 method=Image.Resampling.LANCZOS)
        x = index % columns * thumb_w
        y = index // columns * (thumb_h + label_h)
        sheet.paste(thumb, (x, y))
        draw.text((x + 8, y + thumb_h + 8), str(item["id"]), font=face, fill="#24303a")
    destination.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(destination)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--render", action="store_true")
    parser.add_argument("--sync-curriculum", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--quick-check", action="store_true",
                        help="Skip the source-to-raster determinism rerender")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--contact-sheet", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    curricula = load_curricula()
    specs = all_specs()
    validate_inventory(curricula, specs)
    verify_preexisting(curricula)
    if args.render:
        print("Rendered {} natural-science illustration files".format(
            len(render_assets(specs, args.overwrite))))
    if args.sync_curriculum:
        print("Synced illustrations for {} natural-science lessons".format(
            sync_curricula(curricula, specs)))
        curricula = load_curricula()
    if args.check or args.quick_check:
        verify(curricula, specs, check_determinism=not args.quick_check)
        qualifier = "deterministic " if args.check else ""
        print("Verified {}{} lessons, {} generated plates, and {} responsive rasters".format(
            qualifier, sum(EXPECTED_NODE_COUNTS.values()), len(specs),
            sum(EXPECTED_NODE_COUNTS.values()) * 2))
    if args.contact_sheet:
        write_contact_sheet(specs, args.contact_sheet)
        print("Wrote {}".format(args.contact_sheet))
    if not any((args.render, args.sync_curriculum, args.check,
                args.quick_check, args.contact_sheet)):
        print("{} new specs complete {} natural-science lessons".format(
            len(specs), sum(EXPECTED_NODE_COUNTS.values())))


if __name__ == "__main__":
    main()
