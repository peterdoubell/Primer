#!/usr/bin/env python3
"""Track human visual review against current illustration bytes and descriptions.

This is not an automatic visual-quality judge. Review records must be earned by
inspection; asset integrity, model behavior and runtime checks remain separate.
"""
import argparse
import hashlib
import json
from pathlib import Path

from check_model_coverage import inventory

ROOT = Path(__file__).resolve().parents[1]


def audit(root=ROOT, reviews=None):
    root = Path(root)
    inventory(root / "data/curriculum")  # Reject empty and duplicated curricula.
    if reviews is None:
        reviews = json.loads((root / "docs/illustration-reviews.json").read_text())
    if not isinstance(reviews, list):
        raise ValueError("Review records must be a list")
    records = {}
    for review in reviews:
        identifier = review["lesson"]
        if identifier in records:
            raise ValueError("Duplicate review: " + identifier)
        if not review.get("evidence", "").strip() or not review.get("finding", "").strip():
            raise ValueError("Review needs evidence and a finding: " + identifier)
        records[identifier] = review
    rows = []
    for source in sorted((root / "data/curriculum").glob("[0-9]*.json")):
        curriculum = json.loads(source.read_text())
        for node in curriculum["nodes"]:
            plates = [m for m in node.get("lesson_media", []) if m.get("kind") == "illustration"]
            if len(plates) != 1:
                raise ValueError("Expected one illustration: " + node["id"])
            plate = plates[0]
            urls = {plate["src"]} | {part.strip().split()[0] for part in plate["srcset"].split(",")}
            images = {}
            for url in sorted(urls):
                if not url.startswith("/app/illustrations/"):
                    raise ValueError("Nonlocal illustration: " + url)
                path = (root / "web" / url.removeprefix("/app/")).resolve()
                if (root / "web/illustrations").resolve() not in path.parents:
                    raise ValueError("Illustration escapes asset directory: " + url)
                images[url] = hashlib.sha256(path.read_bytes()).hexdigest()
            payload = {"lesson": {k: node.get(k) for k in ("id", "title", "stage", "goal")},
                       "illustration": plate, "images": images}
            fingerprint = hashlib.sha256(json.dumps(payload, sort_keys=True,
                                                   ensure_ascii=False).encode()).hexdigest()
            record = records.pop(node["id"], None)
            status = "pending" if record is None else (
                "reviewed" if record.get("fingerprint") == fingerprint else "stale")
            rows.append({"lesson": node["id"], "domain": curriculum["id"],
                         "stage": node["stage"], "title": node["title"],
                         "fingerprint": fingerprint, "status": status})
    if records:
        raise ValueError("Review refers to unknown lesson: " + ", ".join(sorted(records)))
    return {"lessons": len(rows), "reviewed": sum(r["status"] == "reviewed" for r in rows),
            "stale": sum(r["status"] == "stale" for r in rows), "rows": rows}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--require-complete", action="store_true")
    args = parser.parse_args()
    try:
        report = audit()
    except (ValueError, KeyError, OSError, TypeError) as error:
        parser.error(str(error))
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print("{reviewed}/{lessons} illustrations have current review records; {stale} stale".format(**report))
        for domain in sorted({r["domain"] for r in report["rows"]}):
            rows = [r for r in report["rows"] if r["domain"] == domain]
            print("{}: {}/{} reviewed".format(domain, sum(r["status"] == "reviewed" for r in rows), len(rows)))
    raise SystemExit(int(args.require_complete and report["reviewed"] != report["lessons"]))
