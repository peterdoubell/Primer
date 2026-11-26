#!/usr/bin/env python3
"""Audit the explanatory-plate coverage across the whole curriculum."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
from typing import Dict, List

ROOT = Path(__file__).resolve().parents[1]
CURRICULUM_ROOT = ROOT / "data" / "curriculum"
WEB_ROOT = ROOT / "web"
EXPECTED_SIZE = (1600, 1000)
CANONICAL_WEBP = re.compile(r"^[a-z0-9][a-z0-9-]*-(?:800|1600)\.webp$")


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


def activity_source_illustrations(errors: List[str]) -> set[Path]:
    """Recognise the registered corpus's source art, separate from lesson plates."""
    corpus_path = WEB_ROOT / "language/word-samples/corpus.json"
    if not corpus_path.is_file():
        return set()
    paths = set()
    try:
        registry = json.loads((WEB_ROOT / "activities/registry.json").read_text())
        if not any(link.get("href") == "/app/language/word-samples/index.html"
                   for link in registry.get("lang.5.comp-ling", [])):
            raise ValueError("corpus has no registered Computational Linguistics entry")
        if not (WEB_ROOT / "language/word-samples/index.html").is_file():
            raise ValueError("registered corpus activity page is missing")
        receipt = json.loads((ROOT / "docs/word-samples/source.json").read_text())
        raw = corpus_path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != receipt["corpusSHA256"]:
            raise ValueError("corpus fingerprint differs from its source receipt")
        book = json.loads(raw)
        if book["commit"] != receipt["commit"]:
            raise ValueError("corpus and source receipt identify different editions")
        chapters = {row["number"]: row for row in receipt["chapters"]}
        figures = {(row["chapter"], row["offset"]): row for row in receipt["illustrations"]}
        if len(chapters) != 12 or len(figures) != 41 or len(figures) != len(receipt["illustrations"]):
            raise ValueError("source receipt must identify twelve chapters and 41 figures")
        dimensions = json.loads((ROOT / "data/lesson-illustrations.json").read_text())
        used_figures = set()
        used_chapters = set()
        for chapter in book["chapters"]:
            number = chapter["number"]
            if number in used_chapters or hashlib.sha256(chapter["text"].encode()).hexdigest() != chapters[number]["textSHA256"]:
                raise ValueError("chapter identity or source text differs")
            used_chapters.add(number)
            for figure in chapter["illustrations"]:
                key = (number, figure["offset"])
                if key in used_figures or not 0 <= figure["offset"] <= len(chapter["text"]) or not figure["alt"].strip():
                    raise ValueError("figure has an invalid or repeated chapter anchor")
                source = figures[key]
                used_figures.add(key)
                for width, field in ((800, "file"), (1600, "large")):
                    rendition = source["variants"][str(width)]
                    url = figure[field]
                    relative = Path(url.removeprefix("/app/"))
                    if (url != rendition["url"] or not url.startswith("/app/illustrations/word-samples/")
                            or ".." in relative.parts or not CANONICAL_WEBP.fullmatch(relative.name)
                            or relative in paths):
                        raise ValueError("figure rendition has an invalid or repeated source URL")
                    path = WEB_ROOT / relative
                    blob = path.read_bytes()
                    actual = webp_dimensions(path)
                    if (actual != (width, rendition["height"]) or rendition["width"] != width
                            or len(blob) != rendition["bytes"]
                            or hashlib.sha256(blob).hexdigest() != rendition["sha256"]
                            or any(dimensions[url][name] != rendition[name] for name in ("width", "height", "sha256"))):
                        raise ValueError("figure rendition differs from its source receipt: " + url)
                    if width == 800 and (figure["width"], figure["height"]) != actual:
                        raise ValueError("figure display dimensions differ: " + url)
                    paths.add(relative)
        if used_chapters != set(chapters) or used_figures != set(figures) or len(paths) != 82:
            raise ValueError("corpus does not reference exactly the reviewed chapters and figures")
    except (KeyError, TypeError, ValueError, OSError) as exc:
        errors.append("word-samples source artwork: " + str(exc))
        return set()
    return paths



def manuscript_illustrations(errors: List[str]) -> set[Path]:
    """Recognise the four facsimiles only when the manuscript activity actually references them."""
    catalog = WEB_ROOT / 'language/address-drafts/witnesses.json'
    if not catalog.is_file():
        return set()
    try:
        entry = '/app/language/address-drafts/index.html'
        registry = json.loads((WEB_ROOT / 'activities/registry.json').read_bytes())
        if not (WEB_ROOT / entry.removeprefix('/app/')).is_file() or any(
                not any(row.get('href') == entry for row in registry.get(node, []))
                for node in ('lang.5.philology', 'lang.3.rhetoric')):
            raise ValueError('manuscript activity registration is incomplete')
        receipt = json.loads((ROOT / 'docs/address-drafts/source.json').read_bytes())
        raw = catalog.read_bytes()
        if hashlib.sha256(raw).hexdigest() != receipt['catalogSHA256']:
            raise ValueError('manuscript catalog differs from its source receipt')
        witnesses = json.loads(raw)['witnesses']
        index = json.loads((ROOT / 'data/lesson-illustrations.json').read_bytes())
        expected_pages = {page['image']: page for page in receipt['pages']}
        paths = set()
        for key in ('nicolay', 'hay'):
            pages = witnesses[key]['pages']
            if [p['number'] for p in pages] != [1, 2]:
                raise ValueError('each manuscript requires its two original pages')
            for number, page in zip((1, 2), pages):
                relative = Path('illustrations/address-drafts') / f'{key}-{number}.webp'
                url = '/app/' + relative.as_posix()
                if page['image'] != url or expected_pages.get(url) != page:
                    raise ValueError('source manuscript page identity differs')
                image = WEB_ROOT / relative
                metadata = {k: page[k] for k in ('width', 'height', 'sha256')}
                if (index.get(url) != metadata or webp_dimensions(image) != (page['width'], page['height'])
                        or image.stat().st_size != page['bytes'] or hashlib.sha256(image.read_bytes()).hexdigest() != page['sha256']):
                    raise ValueError('source manuscript rendition differs: ' + url)
                paths.add(relative)
        if len(expected_pages) != 4:
            raise ValueError('unexpected source pages')
        return paths
    except (KeyError, TypeError, ValueError, OSError) as exc:
        errors.append('manuscript source art: ' + str(exc))
        return set()

def audit() -> Dict[str, object]:
    errors: List[str] = []
    domains = []
    urls = set()
    media_ids = set()
    hashes_by_width = {800: {}, 1600: {}}
    total_nodes = 0
    total_illustrated = 0
    total_models = 0
    total_long_descriptions = 0
    total_plates = 0
    for source in sorted(CURRICULUM_ROOT.glob("*.json")):
        curriculum = json.loads(source.read_text(encoding="utf-8"))
        nodes = curriculum.get("nodes", [])
        missing = []
        domain_models = 0
        domain_long_descriptions = 0
        total_nodes += len(nodes)
        for node in nodes:
            node_id = node.get("id", "<missing-id>")
            models = [entry for entry in node.get("lesson_media", [])
                      if isinstance(entry, dict) and entry.get("kind") == "model"]
            # A spatial view can complement the lesson's existing manipulative.
            renderers = [entry.get("renderer") for entry in models]
            if len(renderers) != len(set(renderers)):
                errors.append("{}: duplicate interactive renderer".format(node_id))
            for model in models:
                if not model.get("id") or model["id"] in media_ids:
                    errors.append("{}: missing or duplicate model id".format(node_id))
                media_ids.add(model.get("id"))
            total_models += len(models)
            domain_models += len(models)
            plates = [entry for entry in node.get("lesson_media", [])
                      if isinstance(entry, dict) and entry.get("kind") == "illustration"]
            if not plates:
                errors.append("{}: expected an illustration, found {}".format(
                    node_id, len(plates)))
                if not plates:
                    missing.append(node_id)
                continue
            total_illustrated += 1
            total_plates += len(plates)
            for plate in plates:
                if str(plate.get("long_description", "")).strip():
                    total_long_descriptions += 1
                    domain_long_descriptions += 1
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
            "models": domain_models,
            "long_descriptions": domain_long_descriptions,
            "missing": missing,
        })
    referenced_paths = {Path(url.removeprefix("/app/")) for url in urls}
    activity_paths = activity_source_illustrations(errors) | manuscript_illustrations(errors)
    audited_paths = {
        path.relative_to(WEB_ROOT)
        for path in (WEB_ROOT / "illustrations").rglob("*.webp")
        if CANONICAL_WEBP.fullmatch(path.name)
        or path.parent in {WEB_ROOT / "illustrations/word-samples", WEB_ROOT / "illustrations/address-drafts"}
    }
    orphan_webps = sorted(str(path) for path in audited_paths - referenced_paths - activity_paths)
    for path in orphan_webps:
        errors.append("orphan raster is not referenced by curriculum: {}".format(path))
    return {
        "lessons": total_nodes,
        "illustrated": total_illustrated,
        "missing": total_nodes - total_illustrated,
        "plates": total_plates,
        "responsive_webps": len(urls),
        "activity_source_webps": len(activity_paths),
        "interactive_models": total_models,
        "long_descriptions": total_long_descriptions,
        "orphan_webps": orphan_webps,
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
        print(("{illustrated}/{lessons} lessons illustrated; {responsive_webps} WebPs; "
               "{interactive_models} interactive models; {long_descriptions} long descriptions")
              .format(**result))
        for domain in result["domains"]:
            model_word = "model" if domain["models"] == 1 else "models"
            description_word = ("description" if domain["long_descriptions"] == 1
                                else "descriptions")
            print("{id}: {illustrated}/{lessons}; {models} {model_word}; "
                  "{long_descriptions} long {description_word}".format(
                      model_word=model_word, description_word=description_word,
                      **domain))
        if result["errors"]:
            print("\n".join(result["errors"][:50]))
            if len(result["errors"]) > 50:
                print("... {} more errors".format(len(result["errors"]) - 50))
    if result["errors"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
