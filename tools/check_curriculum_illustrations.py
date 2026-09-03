#!/usr/bin/env python3
"""Audit the one-explanatory-plate contract across the whole curriculum."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parents[1]
CURRICULUM_ROOT = ROOT / "data" / "curriculum"
WEB_ROOT = ROOT / "web"
EXPECTED_SIZE = (1600, 1000)


def webp_dimensions(path: Path) -> tuple[int, int]:
    """Read dimensions directly so the release audit has no tool-only dependency."""
    with path.open("rb") as image:
        header = image.read(30)
    if len(header) < 25 or header[:4] != b"RIFF" or header[8:12] != b"WEBP":
        raise ValueError("not a WebP")
    chunk = header[12:16]
    if chunk == b"VP8X" and len(header) >= 30:
        width = 1 + int.from_bytes(header[24:27], "little")
        height = 1 + int.from_bytes(header[27:30], "little")
    elif chunk == b"VP8 " and len(header) >= 30 and header[23:26] == b"\x9d\x01\x2a":
        width = int.from_bytes(header[26:28], "little") & 0x3FFF
        height = int.from_bytes(header[28:30], "little") & 0x3FFF
    elif chunk == b"VP8L" and header[20] == 0x2F:
        packed = int.from_bytes(header[21:25], "little")
        width = 1 + (packed & 0x3FFF)
        height = 1 + ((packed >> 14) & 0x3FFF)
    else:
        raise ValueError("unsupported WebP header")
    if width <= 0 or height <= 0:
        raise ValueError("invalid WebP dimensions")
    return width, height


def audit() -> Dict[str, object]:
    errors: List[str] = []
    domains = []
    urls = set()
    media_ids = set()
    hashes_by_width = {800: {}, 1600: {}}
    total_nodes = 0
    total_illustrated = 0
    for source in sorted(CURRICULUM_ROOT.glob("*.json")):
        curriculum = json.loads(source.read_text(encoding="utf-8"))
        nodes = curriculum.get("nodes", [])
        missing = []
        total_nodes += len(nodes)
        for node in nodes:
            node_id = node.get("id", "<missing-id>")
            plates = [entry for entry in node.get("lesson_media", [])
                      if isinstance(entry, dict) and entry.get("kind") == "illustration"]
            if len(plates) != 1:
                errors.append("{}: expected one illustration, found {}".format(
                    node_id, len(plates)))
                if not plates:
                    missing.append(node_id)
                continue
            total_illustrated += 1
            plate = plates[0]
            media_id = plate.get("id")
            if media_id in media_ids:
                errors.append("{}: duplicate media id {}".format(node_id, media_id))
            media_ids.add(media_id)
            if (plate.get("width"), plate.get("height")) != EXPECTED_SIZE:
                errors.append("{}: declared dimensions are not 1600x1000".format(node_id))
            alt = str(plate.get("alt", "")).strip()
            caption = str(plate.get("caption", "")).strip()
            if alt == caption or min(len(alt.split()), len(caption.split())) < 8:
                errors.append("{}: alt and caption must be distinct explanations".format(node_id))
            candidates = str(plate.get("srcset", "")).split(",")
            local_urls = set()
            widths = set()
            for candidate in candidates:
                pieces = candidate.strip().split()
                if len(pieces) != 2 or not pieces[1].endswith("w"):
                    errors.append("{}: malformed srcset candidate {!r}".format(node_id, candidate))
                    continue
                url, descriptor = pieces
                try:
                    expected_width = int(descriptor[:-1])
                except ValueError:
                    errors.append("{}: invalid width descriptor {}".format(node_id, descriptor))
                    continue
                local_urls.add(url)
                widths.add(expected_width)
                if url in urls:
                    errors.append("{}: raster URL is reused: {}".format(node_id, url))
                urls.add(url)
                if not url.startswith("/app/illustrations/") or not url.endswith(".webp"):
                    errors.append("{}: raster URL leaves the local WebP tree".format(node_id))
                    continue
                path = WEB_ROOT / url.removeprefix("/app/")
                if not path.is_file():
                    errors.append("{}: missing raster {}".format(node_id, path))
                    continue
                try:
                    actual = webp_dimensions(path)
                except ValueError as exc:
                    errors.append("{}: bad raster {}: {}".format(node_id, path, exc))
                    continue
                expected_height = expected_width * EXPECTED_SIZE[1] // EXPECTED_SIZE[0]
                if actual != (expected_width, expected_height):
                    errors.append("{}: bad raster contract {} {}".format(
                        node_id, path, actual))
                digest = hashlib.sha256(path.read_bytes()).hexdigest()
                owner = hashes_by_width.setdefault(expected_width, {}).get(digest)
                if owner:
                    errors.append("{}: duplicates {} at {}px".format(node_id, owner, expected_width))
                hashes_by_width[expected_width][digest] = node_id
                if path.stat().st_size >= 300_000:
                    errors.append("{}: raster exceeds 300KB: {}".format(node_id, path))
            if widths != {800, 1600} or plate.get("src") not in local_urls:
                errors.append("{}: needs 800w/1600w sources and a valid fallback".format(node_id))
        domains.append({
            "id": curriculum.get("id"),
            "name": curriculum.get("name"),
            "lessons": len(nodes),
            "illustrated": len(nodes) - len(missing),
            "missing": missing,
        })
    return {
        "lessons": total_nodes,
        "illustrated": total_illustrated,
        "missing": total_nodes - total_illustrated,
        "responsive_webps": len(urls),
        "domains": domains,
        "errors": errors,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = audit()
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print("{illustrated}/{lessons} lessons illustrated; {responsive_webps} WebPs".format(
            **result))
        for domain in result["domains"]:
            print("{id}: {illustrated}/{lessons}".format(**domain))
        if result["errors"]:
            print("\n".join(result["errors"][:50]))
            if len(result["errors"]) > 50:
                print("... {} more errors".format(len(result["errors"]) - 50))
    if result["errors"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
