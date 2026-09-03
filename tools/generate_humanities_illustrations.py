#!/usr/bin/env python3
"""Render, integrate and exhaustively verify humanities illustration plates.

This generator owns the missing illustration set for History & Civics, Arts &
Music, and Mind, Society & Philosophy.  Six earlier hand-authored illustration
and model pairs are intentionally excluded from generation and protected by
canonical media fingerprints.

Examples from the repository root::

    python3 tools/generate_humanities_illustrations.py --render --overwrite
    python3 tools/generate_humanities_illustrations.py --sync-curriculum --check
    python3 tools/generate_humanities_illustrations.py --check-determinism
    python3 tools/generate_humanities_illustrations.py --contact-sheet-dir /tmp/humanities
"""

from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, MutableMapping, Tuple

from PIL import Image, ImageDraw, ImageFont, ImageOps

from humanities_illustrations.core import (
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
CURRICULUM_FILES = {
    "history": ROOT / "data" / "curriculum" / "07-history.json",
    "arts": ROOT / "data" / "curriculum" / "09-arts.json",
    "mind-society": ROOT / "data" / "curriculum" / "10-mind-society.json",
}

# These hashes cover the entire pre-existing lesson_media list: authored
# illustrations and their companion interactive models.  A check fails if any
# key, value, order or nested property changes.
AUTHORED_MEDIA_FINGERPRINTS = {
    "hist.0.family": "2b20d85e11094d891d92654517da027cf5fbd7552796e5c48a19f740626a0494",
    "hist.1.timelines": "37b8881ac688a64472a07a9f223a6d7522fd6d0031b8ad3ff571608b6dccf9af",
    "arts.0.colors": "41fa1207cdf9f6af316b2a8560e861aabcfe63d0855bea18c49c516a9cd2fdbb",
    "arts.1.elements": "569b9419bb2b07a53fdb7e5d6859198d97476cb1db12377c94ed2834fa1a8c38",
    "mind.2.logic-intro": "4e14b5dd9734af0e0bff0fd57ee96b16df34c950d095c34c3940a19d0421d3a0",
    "mind.3.logic": "15e5431d4ad1ed648c80de0dac7a34b81753e2447a408d2a4c0167e7175bbcad",
}


def load_curricula() -> Dict[str, MutableMapping[str, object]]:
    curricula: Dict[str, MutableMapping[str, object]] = {}
    for domain, path in CURRICULUM_FILES.items():
        with path.open(encoding="utf-8") as handle:
            curricula[domain] = json.load(handle)
    return curricula


def all_specs() -> Dict[str, Spec]:
    from humanities_illustrations.arts import SPECS as arts
    from humanities_illustrations.history import SPECS as history
    from humanities_illustrations.mind_society import SPECS as mind_society

    result: Dict[str, Spec] = {}
    for cohort in (history, arts, mind_society):
        overlap = set(result).intersection(cohort)
        if overlap:
            raise ValueError(f"Duplicate humanities specs: {sorted(overlap)}")
        result.update(cohort)
    return result


def _media_fingerprint(media: object) -> str:
    encoded = json.dumps(
        media, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def validate_inventory(
    curricula: Mapping[str, Mapping[str, object]], specs: Mapping[str, Spec]
) -> None:
    nodes = {
        node["id"]: (domain, node)
        for domain, curriculum in curricula.items()
        for node in curriculum["nodes"]
    }
    expected = set(nodes) - set(AUTHORED_MEDIA_FINGERPRINTS)
    validate_specs(dict(specs), expected)
    for node_id, item in specs.items():
        domain, node = nodes[node_id]
        if item["title"] != node["title"] or item["stage"] != node["stage"]:
            raise ValueError(f"Spec metadata drift for {node_id}")
        if item["domain"] != domain:
            raise ValueError(f"Spec domain drift for {node_id}")
    for node_id, expected_hash in AUTHORED_MEDIA_FINGERPRINTS.items():
        if node_id not in nodes:
            raise ValueError(f"Authored media node disappeared: {node_id}")
        actual = _media_fingerprint(nodes[node_id][1].get("lesson_media"))
        if actual != expected_hash:
            raise ValueError(
                f"Refusing to proceed: authored lesson_media changed for {node_id}"
            )


def render_assets(specs: Mapping[str, Spec], overwrite: bool) -> List[Path]:
    if not overwrite:
        collisions = [
            path
            for item in specs.values()
            for path in asset_paths(OUTPUT_ROOT, item)
            if path.exists()
        ]
        if collisions:
            raise FileExistsError(
                "Refusing to overwrite {} existing outputs; first paths: {}".format(
                    len(collisions), collisions[:5]
                )
            )
    outputs: List[Path] = []
    for item in specs.values():
        outputs.extend(render_spec(OUTPUT_ROOT, item, overwrite=overwrite))
    return outputs


def sync_curricula(
    curricula: Mapping[str, MutableMapping[str, object]], specs: Mapping[str, Spec]
) -> int:
    changed = 0
    for domain, curriculum in curricula.items():
        domain_changed = 0
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
                current = illustrations[0] if len(illustrations) == 1 else None
                # A matching generated id and path prove that this is our own
                # entry, which may be refreshed after an audited alt/caption fix.
                # Anything else is treated as authored and remains untouchable.
                if (
                    current is None
                    or current.get("id") != expected["id"]
                    or current.get("src") != expected["src"]
                ):
                    raise ValueError(
                        f"Refusing to replace an illustration on {node_id}"
                    )
                media[media.index(current)] = expected
            else:
                media.insert(0, expected)
            changed += 1
            domain_changed += 1
        if domain_changed:
            # A canonical one-space indent matches the curriculum repository.
            with CURRICULUM_FILES[domain].open("w", encoding="utf-8") as handle:
                json.dump(curriculum, handle, indent=1, ensure_ascii=False)
                handle.write("\n")
    return changed


def _url_path(url: str) -> Path:
    prefix = "/app/"
    if not url.startswith(prefix):
        raise ValueError(f"Illustration URL must start with {prefix}: {url}")
    return ROOT / "web" / url[len(prefix):]


def verify(
    curricula: Mapping[str, Mapping[str, object]], specs: Mapping[str, Spec]
) -> None:
    all_nodes = [node for curriculum in curricula.values() for node in curriculum["nodes"]]
    if len(all_nodes) != 83:
        raise ValueError(f"Expected 83 assigned lessons, found {len(all_nodes)}")

    paths_seen = set()
    hashes_seen = set()
    alts = set()
    captions = set()
    plate_ids = set()
    problems: List[str] = []

    for node in all_nodes:
        node_id = node["id"]
        media = node.get("lesson_media", [])
        illustrations = [item for item in media if item.get("kind") == "illustration"]
        if len(illustrations) != 1:
            problems.append(f"{node_id}: {len(illustrations)} illustrations")
            continue
        item = illustrations[0]
        if node_id in specs and item != illustration_entry(specs[node_id]):
            problems.append(f"{node_id}: generated metadata drift")
        if (item.get("width"), item.get("height")) != (WIDTH, HEIGHT):
            problems.append(f"{node_id}: declared dimensions are not {WIDTH}×{HEIGHT}")
        if item.get("id") in plate_ids:
            problems.append(f"{node_id}: duplicate plate id {item.get('id')}")
        plate_ids.add(item.get("id"))
        for key, seen in (("alt", alts), ("caption", captions)):
            value = item.get(key)
            if not isinstance(value, str) or len(value.split()) < 12:
                problems.append(f"{node_id}: {key} is not sufficiently descriptive")
            elif value in seen:
                problems.append(f"{node_id}: duplicate {key}")
            seen.add(value)
        if item.get("alt") == item.get("caption"):
            problems.append(f"{node_id}: alt and caption must serve different purposes")

        srcset = item.get("srcset", "")
        candidates = [part.strip().split() for part in srcset.split(",") if part.strip()]
        if len(candidates) != 2 or any(len(candidate) != 2 for candidate in candidates):
            problems.append(f"{node_id}: srcset must have exactly two candidates")
            continue
        candidate_urls = {candidate[0] for candidate in candidates}
        if item.get("src") not in candidate_urls:
            problems.append(f"{node_id}: fallback src is absent from srcset")
        expected_widths = {800, 1600}
        actual_widths = set()
        for url, descriptor in candidates:
            if not descriptor.endswith("w") or not descriptor[:-1].isdigit():
                problems.append(f"{node_id}: invalid descriptor {descriptor}")
                continue
            declared_width = int(descriptor[:-1])
            actual_widths.add(declared_width)
            path = _url_path(url)
            if path in paths_seen:
                problems.append(f"{node_id}: raster path reused by another lesson: {path}")
            paths_seen.add(path)
            if not path.is_file():
                problems.append(f"{node_id}: missing raster {path}")
                continue
            if path.suffix.lower() != ".webp":
                problems.append(f"{node_id}: raster is not .webp: {path}")
            with Image.open(path) as image:
                if image.format != "WEBP":
                    problems.append(f"{node_id}: raster format is {image.format}")
                expected_size = (declared_width, declared_width * HEIGHT // WIDTH)
                if image.size != expected_size:
                    problems.append(
                        f"{node_id}: {path.name} is {image.size}, expected {expected_size}"
                    )
                if image.mode not in {"RGB", "RGBA"}:
                    problems.append(f"{node_id}: unexpected image mode {image.mode}")
            if path.stat().st_size >= 400_000:
                problems.append(f"{node_id}: raster exceeds 400 KB: {path}")
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            if digest in hashes_seen:
                problems.append(f"{node_id}: raster bytes duplicate another lesson")
            hashes_seen.add(digest)
        if actual_widths != expected_widths:
            problems.append(f"{node_id}: responsive widths are {sorted(actual_widths)}")

    expected_paths = len(all_nodes) * 2
    if len(paths_seen) != expected_paths:
        problems.append(f"found {len(paths_seen)} unique paths; expected {expected_paths}")
    for node_id, expected_hash in AUTHORED_MEDIA_FINGERPRINTS.items():
        node = next(node for node in all_nodes if node["id"] == node_id)
        if _media_fingerprint(node.get("lesson_media")) != expected_hash:
            problems.append(f"{node_id}: authored media fingerprint changed")
    if problems:
        raise ValueError("Humanities illustration verification failed:\n- " + "\n- ".join(problems))


def verify_determinism(specs: Mapping[str, Spec]) -> None:
    """Freshly regenerate every owned plate and byte-compare both sizes."""

    with tempfile.TemporaryDirectory(prefix="primer-humanities-") as temporary:
        temporary_root = Path(temporary) / "illustrations"
        for node_id, item in specs.items():
            fresh_paths = render_spec(temporary_root, item, overwrite=False)
            committed_paths = asset_paths(OUTPUT_ROOT, item)
            for fresh, committed in zip(fresh_paths, committed_paths):
                if not committed.is_file():
                    raise FileNotFoundError(committed)
                if fresh.read_bytes() != committed.read_bytes():
                    raise ValueError(
                        f"Non-deterministic or stale illustration output for {node_id}: "
                        f"{committed.name}"
                    )


def _contact_sheet_font(size: int) -> ImageFont.FreeTypeFont:
    candidates = (
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    )
    for candidate in candidates:
        if Path(candidate).is_file():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def write_contact_sheets(
    curricula: Mapping[str, Mapping[str, object]], destination: Path
) -> List[Path]:
    destination.mkdir(parents=True, exist_ok=True)
    outputs: List[Path] = []
    thumb_w, thumb_h, label_h, columns = 400, 250, 46, 4
    face = _contact_sheet_font(20)
    for domain, curriculum in curricula.items():
        nodes = curriculum["nodes"]
        rows = (len(nodes) + columns - 1) // columns
        sheet = Image.new("RGB", (columns * thumb_w, rows * (thumb_h + label_h)), "#efe7d2")
        draw = ImageDraw.Draw(sheet)
        for index, node in enumerate(nodes):
            illustration = next(
                item for item in node["lesson_media"] if item["kind"] == "illustration"
            )
            source = _url_path(illustration["src"])
            with Image.open(source) as opened:
                thumb = ImageOps.fit(
                    opened.convert("RGB"),
                    (thumb_w, thumb_h),
                    method=Image.Resampling.LANCZOS,
                )
            x = index % columns * thumb_w
            y = index // columns * (thumb_h + label_h)
            sheet.paste(thumb, (x, y))
            draw.text((x + 8, y + thumb_h + 9), node["id"], font=face, fill="#24303a")
        output = destination / f"{domain}-contact-sheet.png"
        sheet.save(output)
        outputs.append(output)
    return outputs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--render", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--sync-curriculum", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--check-determinism", action="store_true")
    parser.add_argument("--contact-sheet-dir", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    curricula = load_curricula()
    specs = all_specs()
    validate_inventory(curricula, specs)
    if args.render:
        outputs = render_assets(specs, overwrite=args.overwrite)
        print(f"Rendered {len(outputs)} humanities illustration files")
    if args.sync_curriculum:
        changed = sync_curricula(curricula, specs)
        print(f"Added illustrations to {changed} curriculum lessons")
        curricula = load_curricula()
        validate_inventory(curricula, specs)
    if args.check:
        verify(curricula, specs)
        print("Verified 83 humanities lessons and 166 unique responsive WebPs")
    if args.check_determinism:
        verify_determinism(specs)
        print("Byte-verified deterministic regeneration for 77 generated plates")
    if args.contact_sheet_dir:
        outputs = write_contact_sheets(curricula, args.contact_sheet_dir)
        for output in outputs:
            print(f"Wrote {output}")
    if not any((args.render, args.sync_curriculum, args.check,
                args.check_determinism, args.contact_sheet_dir)):
        print(f"{len(specs)} generated specs complete 83 assigned humanities lessons")


if __name__ == "__main__":
    main()
