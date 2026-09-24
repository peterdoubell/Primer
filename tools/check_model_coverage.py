#!/usr/bin/env python3
"""Report every lesson without a model; optionally enforce complete coverage.

Presence reports opportunities for lesson-specific assessment, not educational
quality or working controls. Universal presence is an optional policy; the
user's appropriate-model goal also needs instructional and runtime review.
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def inventory(curriculum_dir=None):
    runtime_nodes = None
    if curriculum_dir is None:
        # The live curriculum also binds shared photos and spatial companions
        # from the module manifests. Audit what readers can actually open.
        sys.path.insert(0, str(ROOT))
        from primer.curriculum import Curriculum
        runtime_nodes = Curriculum().nodes
    curriculum_dir = Path(curriculum_dir) if curriculum_dir is not None else ROOT / "data/curriculum"
    sources = sorted(curriculum_dir.glob("[0-9]*.json"))
    if not sources:
        raise ValueError("No curriculum files found; empty input cannot establish coverage")
    domains = []
    domain_ids, lesson_ids = set(), set()
    for source in sources:
        curriculum = json.loads(source.read_text(encoding="utf-8"))
        domain_id = curriculum["id"]
        if domain_id in domain_ids:
            raise ValueError("Duplicate curriculum domain: " + domain_id)
        domain_ids.add(domain_id)
        if not curriculum["nodes"]:
            raise ValueError("Empty curriculum domain: " + domain_id)
        missing, covered, entries = [], 0, 0
        for node in curriculum["nodes"]:
            if node["id"] in lesson_ids:
                raise ValueError("Duplicate curriculum lesson: " + node["id"])
            lesson_ids.add(node["id"])
            runtime_node = runtime_nodes[node["id"]] if runtime_nodes is not None else node
            models = [item for item in runtime_node.get("lesson_media", []) if item.get("kind") == "model"]
            entries += len(models)
            if models:
                covered += 1
            else:
                missing.append({"id": node["id"], "title": node["title"], "stage": node["stage"]})
        domains.append({"domain": curriculum["id"], "lessons": len(curriculum["nodes"]),
                        "covered": covered, "model_entries": entries, "missing": missing})
    return {"lessons": sum(d["lessons"] for d in domains),
            "covered": sum(d["covered"] for d in domains),
            "model_entries": sum(d["model_entries"] for d in domains), "domains": domains}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Include the full lesson-by-lesson backlog")
    parser.add_argument("--require-complete", action="store_true", help="Fail when any lesson lacks a model")
    args = parser.parse_args()
    try:
        report = inventory()
    except (ValueError, KeyError, TypeError) as error:
        parser.error("Invalid curriculum inventory: " + str(error))
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print("{covered}/{lessons} lessons have models; {model_entries} model entries".format(**report))
        for domain in report["domains"]:
            print("{domain}: {covered}/{lessons}; missing {missing_count}".format(
                **domain, missing_count=len(domain["missing"])))
    raise SystemExit(int(args.require_complete and report["covered"] != report["lessons"]))
