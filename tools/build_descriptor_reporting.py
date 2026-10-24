#!/usr/bin/env python3
"""Compile authored reporting-step statements into deterministic selectable reports.

This is a presentation compiler, not a clinical authoring tool. It preserves the
statement verbatim and records every replacement span. Only alternatives actually
present in the source become choices. A source placeholder such as ``[method]`` or
``[right]`` is context, not evidence that a method or side has been observed.

Usage::

    python tools/build_descriptor_reporting.py --catalog /path/to/catalog.json

The catalogue is the existing, versioned Primer reporting API export. The generated
file is standalone: consumers need neither this build script nor the catalogue at
runtime. Unknown values have no defaults. Missing context is supplied through the
API, never guessed or turned into a typing field in the descriptor sheet.
"""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
import re
import gzip
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "1.0"
VERSION = "2026-10-23"

# These are requests for information, not enumerated descriptions. In particular,
# "[size / distribution]" must not become a choice between the words size and
# distribution. We deliberately leave unenumerated clinical vocabulary unresolved.
CONTEXT_WORDS = {
    "structure", "question", "finding", "findings", "size", "distribution",
    "location", "locations", "method", "methods", "measurement", "measurements",
    "details", "extent", "date", "time", "value", "values", "reason", "number",
    "management", "handover", "interpretation", "observations", "description",
    "site", "image", "type", "specify", "source", "level", "coverage",
}
TOKEN = re.compile(r"\[[^\[\]]*\]|_{2,}")
UNIT = re.compile(
    r"^\s*(mGy[·.]cm|mL/min/1\.73\s*m²|mL/m²|mL/min|mL/s|mmHg|mm(?:²|³)?|"
    r"cm/s|m/s|cm(?:²|³)?|mL|mgI/mL|ng/mL|mmol/L|g/m²|g|bpm|mGy|MBq|SUV|ms|HU|%|°|"
    r"years?|months?|weeks?|days?|hours?|minutes?|seconds?|degrees?|o['’]clock)(?![A-Za-z_])",
    re.I,
)
GENERIC_TERMS = re.compile(r"\b(?:and|or|the|a|an|of|at|in|on|with|without|by|to|from)\s*$", re.I)


def digest(value: Any) -> str:
    if not isinstance(value, str):
        value = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def slug(value: str, length: int = 45) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")[:length].rstrip("-") or "item"


def title_label(text: str) -> str:
    """Human-readable heading without destroying meaningful clinical acronyms."""
    if text.isupper():
        keep = {"MRI", "CT", "US", "AC", "ACL", "PCL", "MCL", "LCL", "RV", "LV", "IVC", "CBD", "CNS", "DWI", "ADC", "BI-RADS", "PI-RADS", "TI-RADS", "CAD-RADS"}
        text = " ".join(word if word in keep else word.lower() for word in text.split())
        text = text[:1].upper() + text[1:]
    return text


def short_label(text: str, fallback: str) -> str:
    """Use source words only; labels are display aids, never report wording."""
    first = re.split(r"[.;:]", text, maxsplit=1)[0]
    def display_token(match):
        token = match.group()
        options = choice_options(token[1:-1].strip()) if token.startswith("[") else []
        # Keep the diagnostic words in alternatives such as subluxation /
        # dislocation. Example/context blanks still cannot assert a finding.
        return "/".join(options)
    first = TOKEN.sub(display_token, first)
    first = re.sub(r"\s+([,;:])", r"\1", first)
    first = re.sub(r"([,;:])(?:\s*[,;:])+", r"\1", first)
    first = re.sub(r"\s+", " ", first).strip(" ,;:–—-")
    # Avoid displaying a dimension fragment as the finding name.
    first = re.split(r",?\s+(?:measuring|spanning|retracted|involving approximately)\b", first, flags=re.I)[0]
    first = re.split(r"\s+\b(?:mm|cm|mL|HU)\b", first, maxsplit=1)[0].strip(" ,;:×–—-")
    for connector in (" with ", " without ", " from ", " at the "):
        prefix, separator, _ = first.partition(connector)
        if separator and len(prefix) >= 10:
            first = prefix.rstrip(" ,;:")
    first = GENERIC_TERMS.sub("", first).strip()
    if not first or len(first) < 4:
        first = fallback
    if len(first) > 76:
        first = first[:73].rsplit(" ", 1)[0].rstrip(" ,;:") + "…"
    return first[:1].upper() + first[1:]


def choice_options(body: str) -> list[str]:
    """Conservative finite alternatives, without promoting example placeholders."""
    if "/" not in body or "__" in body or "[" in body or "]" in body:
        return []
    # Spaces distinguish authored alternatives from slashes inside a concept
    # such as source/coverage, V/Q, SI/AP or a measurement unit.
    choices = [re.sub(r"\s+", " ", value).strip() for value in re.split(r"\s+/\s+", body)]
    if len(choices) < 2 or any(not value for value in choices):
        return []
    if any(value.lower() in CONTEXT_WORDS for value in choices):
        return []
    # List prompts such as morphology/stenosis/regurgitation and supporting data
    # describe dimensions to supply rather than mutually exclusive observations.
    if any(re.search(r"\b(?:and severity|and finding|and supporting|and side|as appropriate|listed|specified|specify|reason|actual method|acquired region|named structure|site and course|other actual configuration|a different sinus method)\b", value, re.I) for value in choices):
        return []
    return list(dict.fromkeys(choices))


def source_tokens(text: str):
    """Balanced top-level bracket slots and unbracketed underscore slots.

    A bracket containing another placeholder is kept as a single context slot.
    This prevents copying a chosen phrase that still contains '__' or brackets.
    """
    index = 0
    while index < len(text):
        if text[index] == "[":
            start, depth = index, 1
            index += 1
            while index < len(text) and depth:
                depth += (text[index] == "[") - (text[index] == "]")
                index += 1
            if depth:
                raise ValueError(f"Unbalanced source bracket: {text!r}")
            yield start, index, text[start:index]
        elif text[index:index + 2] == "__":
            start = index
            while index < len(text) and text[index] == "_":
                index += 1
            yield start, index, text[start:index]
        else:
            index += 1


def number_unit(text: str, end: int) -> str | None:
    tail = text[end:]
    # A shared trailing unit is valid for an authored range or set of dimensions.
    tail = re.sub(r"^\s*(?:(?:×|x|–|to)\s*__\s*)+", "", tail)
    match = UNIT.match(tail)
    return match.group(1) if match else None


def slot_label(text: str, start: int, token: str, kind: str, unit: str | None, index: int) -> str:
    body = token[1:-1].strip() if token.startswith("[") else ""
    if kind == "context" and body:
        return body[:1].upper() + body[1:]
    before = text[:start]
    clause = re.split(r"[.;:,()]", before)[-1].strip()
    clause = TOKEN.sub("", clause)
    clause = re.sub(r"\s+", " ", clause).strip(" ×–-")
    clause = GENERIC_TERMS.sub("", clause).strip()
    if len(clause) > 48:
        clause = clause[-48:].split(" ", 1)[-1]
    if kind == "number":
        label = clause or f"Measurement {index}"
        if unit:
            label += f" ({unit})"
    else:
        label = clause or ("Description" if kind == "choice" else f"Detail {index}")
    return label[:1].upper() + label[1:]


def compile_statement(text: str, *, kind: str, source: dict, label: str | None = None) -> dict:
    segments, slots, cursor = [], [], 0
    for index, (start, end, token) in enumerate(source_tokens(text), 1):
        if start > cursor:
            segments.append({"text": text[cursor:start]})
        body = token[1:-1].strip() if token.startswith("[") else ""
        options = choice_options(body)
        unit = number_unit(text, end)
        # Bare underscores are authored numeric slots except alphanumeric stage
        # tokens such as cT__, N__ and M__, which require the actual stage string.
        is_stage = bool(re.search(r"\b(?:c|p|y|r)?[TNM]$", text[:start]))
        numeric = (token.startswith("__") and not is_stage) or (token.startswith("[") and not body and unit is not None)
        slot_kind = "choice" if options else ("number" if numeric else "context")
        slot = {
            "id": f"slot-{index}", "kind": slot_kind,
            "label": slot_label(text, start, token, slot_kind, unit, index),
            "required": True, "options": [{"value": value, "label": value} for value in options],
            "source_token": token, "source_span": {"start": start, "end": end, "unit": "unicode_code_points"},
        }
        if unit and numeric:
            slot["unit"] = unit
        if slot_kind == "context":
            slot["context_key"] = f"{source['investigation_id']}:{source['step_index']}:{kind}:{source.get('statement_index', 0)}:{index}"
        slots.append(slot)
        segments.append({"slot": slot["id"]})
        cursor = end
    if cursor < len(text):
        segments.append({"text": text[cursor:]})
    source = {**source, "kind": kind, "statement_sha256": digest(text)}
    descriptor = {
        "id": f"{kind}-{digest(text)[:12]}",
        "label": label or short_label(text, "Assessment"),
        "text": text, "segments": segments, "slots": slots, "source": source,
        "requires_context": any(slot["kind"] == "context" for slot in slots),
    }
    return descriptor


def shoulder_measurement_constraints(descriptor: dict, *, guide_id: str, investigation_id: str, structured_form: dict) -> None:
    """Retain the existing source-backed shoulder measurement constraints."""
    if guide_id != "rad.5.shoulder" or investigation_id != "ra.mri-shoulder":
        return
    mappings = {
        "Partial-thickness [articular-sided / bursal-sided / intrasubstance] [ ] tear involving approximately __% of tendon thickness, __ mm long.": {
            "slot-3": ("depth-percent", "Tendon thickness involved (%)"),
            "slot-4": ("ap-width", "Tear length (mm)"),
        },
        "Full-thickness supraspinatus tear at the footprint, __ mm anteroposterior, retracted __ mm [lateral to / at / medial to] the humeral head apex.": {
            "slot-1": ("ap-width", "Anteroposterior tear width (mm)"),
            "slot-2": ("retraction", "Tendon retraction (mm)"),
        },
    }
    mapping = mappings.get(descriptor["text"])
    if not mapping:
        return
    fields = [field for section in structured_form["sections"] for field in section["fields"]]
    for slot in descriptor["slots"]:
        if slot["id"] not in mapping:
            continue
        suffix, label = mapping[slot["id"]]
        source_fields = [field for field in fields if field.get("source_kind") == "curated-source-backed" and field["id"].endswith("." + suffix) and field.get("group_id", "").startswith("rotator-cuff.")]
        if len(source_fields) != 4:
            raise ValueError("Shoulder measurement source fields changed; review constraints")
        constraints = [{key: field[key] for key in ("minimum", "maximum") if key in field} for field in source_fields]
        if any(value != constraints[0] for value in constraints) or any(field.get("unit") != slot.get("unit") for field in source_fields):
            raise ValueError("Shoulder measurement constraints no longer agree across tendon fields")
        slot.update(constraints[0])
        slot["label"] = label
        slot["constraints_source"] = {
            "source_file": "data/radiology/structured-reporting.json",
            "source_field_ids": [field["id"] for field in source_fields],
            "source_kind": "curated-source-backed",
            "scope": "Shared percentage-depth bounds" if suffix == "depth-percent" else "Shared nonnegative distance bound; no measurement-axis substitution",
        }


def shoulder_tendon_choices(descriptor: dict, *, guide_id: str, investigation_id: str, step: dict, structured_form: dict) -> None:
    """Resolve two authored MRI-shoulder tendon blanks from its own vocabulary.

    The four tendon names are explicitly present both in this investigation's
    normal sentence and in the existing, source-backed per-tendon field groups.
    This narrow mapping is not a general attempt to infer choices for arbitrary
    context slots. Report wording and all measurements remain unchanged.
    """
    if guide_id != "rad.5.shoulder" or investigation_id != "ra.mri-shoulder":
        return
    if step.get("sections") != ["ROTATOR CUFF"]:
        return
    expected_texts = {
        "Partial-thickness [articular-sided / bursal-sided / intrasubstance] [ ] tear involving approximately __% of tendon thickness, __ mm long.",
        "Tendinosis of the [ ] tendon: thickening and intermediate signal without a fluid-signal defect.",
    }
    if descriptor["text"] not in expected_texts:
        return
    section = next((value for value in structured_form.get("sections", []) if value["section_id"] == "rotator-cuff"), None)
    if not section:
        raise ValueError("Shoulder tendon vocabulary needs the authored rotator-cuff fields")
    tendon_fields = [field for field in section["fields"] if field.get("id", "").endswith(".tear") and field.get("source_kind") == "curated-source-backed"]
    expected_names = {"supraspinatus", "infraspinatus", "subscapularis", "teres minor"}
    actual_names = {field["group_label"].lower() for field in tendon_fields}
    normal = step.get("normal", "")
    if actual_names != expected_names or any(name not in normal.lower() for name in expected_names):
        raise ValueError("Shoulder source vocabulary changed; review the bounded tendon mapping")
    blank_slots = [slot for slot in descriptor["slots"] if slot["kind"] == "context" and slot["source_token"].strip() == "[ ]"]
    if len(blank_slots) != 1:
        raise ValueError("Shoulder source tendon blank changed; review the bounded mapping")
    slot = blank_slots[0]
    slot.update({
        "kind": "choice", "label": "Tendon",
        "options": [{"value": field["group_label"].lower(), "label": field["group_label"],
                     "source_field_id": field["id"]} for field in tendon_fields],
        "options_source": {
            "kind": "same-investigation-authored-anatomy",
            "source_file": "data/radiology/structured-reporting.json",
            "guide_id": guide_id, "section_id": "rotator-cuff",
            "source_field_ids": [field["id"] for field in tendon_fields],
            "normal_statement": normal, "normal_statement_sha256": digest(normal),
            "transformation": "Existing group labels, lowercased only for sentence insertion",
        },
    })
    slot.pop("context_key", None)
    descriptor["requires_context"] = any(value["kind"] == "context" for value in descriptor["slots"])


def build_catalog(catalog: dict, structured: dict, *, anatomic=True) -> dict:
    forms, counts = {}, collections.Counter()
    snapshot = catalog["manifest"]["snapshot_id"]
    for guide in catalog["guides"]:
        base = structured.get("forms", {}).get(guide["id"], {})
        investigation_meta = {item["id"]: item for item in guide.get("investigations", [])}
        original_sections = base.get("sections", [])
        heading_map = collections.defaultdict(list)
        for original in original_sections:
            heading_map[slug(original["label"])].append(original["section_id"])
        investigations = []
        for investigation in guide.get("steps", []):
            investigation_id = investigation["investigation_id"]
            meta = investigation_meta.get(investigation_id, {})
            sections = []
            seen_sections = collections.Counter()
            for step_index, step in enumerate(investigation.get("steps", [])):
                raw_label = step.get("label") or " / ".join(step.get("sections", [])) or f"Assessment {step_index + 1}"
                section_key = slug(raw_label)
                seen_sections[section_key] += 1
                section_id = f"section-{section_key}"
                if seen_sections[section_key] > 1:
                    section_id += f"-{seen_sections[section_key]}"
                source = {
                    "source_file": investigation.get("source_file"), "investigation_id": investigation_id,
                    "step_index": step_index, "statement_index": 0,
                    "reviewed_at": investigation.get("reviewed_at", guide.get("reporting_reviewed_at")),
                }
                source_sections = step.get("sections", [])
                matches = heading_map.get(slug(source_sections[0]), []) if source_sections else []
                section = {"id": section_id, "label": title_label(raw_label), "source_sections": source_sections,
                           "report_section_id": matches[0] if len(matches) == 1 else None,
                           "report_section_label": source_sections[0] if source_sections else raw_label,
                           "normal": None, "findings": []}
                if section["report_section_id"] is None:
                    counts["sections_without_template_heading_match"] += 1
                normal = step.get("normal")
                if isinstance(normal, str) and normal.strip():
                    descriptor = compile_statement(normal, kind="normal", source=source, label="Normal")
                    counts["source_normal_statements"] += 1
                    if descriptor["slots"]:
                        descriptor["label"] = "Assessment"
                        section["findings"].append(descriptor)
                        counts["assessment_statements"] += 1
                    else:
                        section["normal"] = descriptor
                        counts["complete_normal_statements"] += 1
                else:
                    counts["sections_without_authored_normal"] += 1
                seen_findings = collections.Counter()
                for finding_index, text in enumerate(step.get("findings", [])):
                    if not isinstance(text, str) or not text.strip():
                        raise ValueError(f"Empty or non-text finding: {guide['id']}/{investigation_id}/{step_index}/{finding_index}")
                    descriptor = compile_statement(text, kind="finding", source={**source, "statement_index": finding_index})
                    shoulder_measurement_constraints(descriptor, guide_id=guide["id"], investigation_id=investigation_id, structured_form=base)
                    shoulder_tendon_choices(descriptor, guide_id=guide["id"], investigation_id=investigation_id, step=step, structured_form=base)
                    seen_findings[descriptor["id"]] += 1
                    if seen_findings[descriptor["id"]] > 1:
                        descriptor["id"] += f"-{seen_findings[descriptor['id']]}"
                    section["findings"].append(descriptor)
                    counts["source_finding_statements"] += 1
                for descriptor in ([section["normal"]] if section["normal"] else []) + section["findings"]:
                    counts["descriptors"] += 1
                    counts["descriptors_requiring_context"] += descriptor["requires_context"]
                    counts["descriptors_complete_without_context"] += not descriptor["requires_context"]
                    for slot in descriptor["slots"]:
                        counts[f"{slot['kind']}_slots"] += 1
                counts["sections"] += 1
                sections.append(section)
            investigations.append({"id": investigation_id, "title": investigation["title"], "modality": meta.get("modality"), "sections": sections})
            counts["investigations"] += 1
        if not investigations:
            # Some guides are source worksheets (for example modality selection
            # and radiation safety), not authored investigation walkthroughs.
            # Keep this distinction explicit rather than inventing an examination
            # or treating general teaching text as a normal clinical finding.
            template = guide["templates"][0]
            worksheet_id = f"template:{template['id']}"
            sections = []
            administrative = {"indication", "comparison", "technique-and-quality", "key-images", "impression", "recommendation-and-communication"}
            for source_index, original in enumerate(template["sections"]):
                if original["id"] in administrative:
                    continue
                descriptor = compile_statement(
                    original["body"], kind="template",
                    label=title_label(original["heading"]),
                    source={"source_file": "catalog.json", "template_id": template["id"],
                            "investigation_id": worksheet_id, "step_index": source_index,
                            "statement_index": 0, "section_id": original["id"],
                            "reviewed_at": guide.get("reporting_reviewed_at")},
                )
                sections.append({"id": f"section-{original['id']}", "label": title_label(original["heading"]),
                                 "source_sections": [original["heading"]],
                                 "report_section_id": original["id"], "report_section_label": original["heading"],
                                 "normal": None, "findings": [descriptor]})
                counts["worksheet_sections"] += 1
                counts["descriptors"] += 1
                counts["descriptors_requiring_context"] += descriptor["requires_context"]
                counts["descriptors_complete_without_context"] += not descriptor["requires_context"]
                for slot in descriptor["slots"]:
                    counts[f"{slot['kind']}_slots"] += 1
            investigations.append({"id": worksheet_id, "title": guide["title"], "modality": None,
                                   "kind": "source-worksheet", "sections": sections})
            counts["source_worksheets"] += 1
        forms[guide["id"]] = {
            "schema_version": SCHEMA_VERSION, "guide_id": guide["id"],
            "template_id": base.get("template_id") or guide["templates"][0]["id"],
            "title": guide["title"], "source_snapshot_id": snapshot,
            "calculator_ids": base.get("calculator_ids", []), "investigations": investigations,
            "sources": guide.get("sources", []),
            "provenance": {**guide.get("provenance", {}), "conversion": "verbatim-source-statements-with-explicit-slots", "defaults": "none"},
        }
        forms[guide["id"]]["schema_hash"] = digest(forms[guide["id"]])
        counts["guides"] += 1
    coverage = []
    if anatomic:
        try:
            from tools.msk_descriptor_catalog import apply_anatomic_reports
        except ModuleNotFoundError:
            from msk_descriptor_catalog import apply_anatomic_reports
        coverage = apply_anatomic_reports(forms, ROOT, compile_statement, digest, slug)
    counts['source_descriptors'] = counts['descriptors']
    for key in ('investigations', 'sections'):
        counts['source_' + key] = counts[key]
    all_investigations = [item for form in forms.values() for item in form['investigations']]
    counts['investigations'] = len(all_investigations)
    counts['sections'] = sum(len(item['sections']) for item in all_investigations)
    counts['complete_normal_sections'] = sum(bool(section['normal']) for item in all_investigations for section in item['sections'])
    current = [descriptor for form in forms.values() for investigation in form['investigations']
               for section in investigation['sections'] for descriptor in
               ([section['normal']] if section['normal'] else []) + section['findings']]
    counts['descriptors'] = len(current)
    counts['anatomic_investigations'] = len(coverage)
    counts['anatomic_structures'] = sum(row['structures'] for row in coverage)
    counts['anatomic_findings'] = sum(row['findings'] for row in coverage)
    for key in ('choice_slots','number_slots','context_slots','descriptors_requiring_context','descriptors_complete_without_context'):
        counts['source_' + key] = counts[key]
    for kind in ('choice','number','context'):
        counts[kind+'_slots'] = sum(slot['kind'] == kind for descriptor in current for slot in descriptor['slots'])
    counts['descriptors_requiring_context'] = sum(descriptor['requires_context'] for descriptor in current)
    counts['descriptors_complete_without_context'] = len(current)-counts['descriptors_requiring_context']
    result = {
        "schema_version": SCHEMA_VERSION, "version": VERSION, "source_snapshot_id": snapshot,
        "forms": forms, "summary": dict(sorted(counts.items())), "anatomic_coverage":coverage,
        "contract": {
            "selection_policy": "Explicit selection only. Normal and not-assessed exclude findings within the same section.",
            "context_policy": "Unenumerated source placeholders require external context. They must not be guessed, auto-filled, silently omitted, or rendered as text inputs.",
            "number_policy": "Only actual supplied measurements; no numeric defaults. A number picker is an input method, not a measurement source.",
            "report_policy": "All slots in selected statements must resolve before a report is complete. Preserve source statement wording.",
        },
    }
    result["schema_hash"] = digest(result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--structured", type=Path, default=ROOT / "data/radiology/structured-reporting.json")
    parser.add_argument("--output", type=Path, default=ROOT / "data/radiology/descriptor-reporting.json")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--archive-current", action="store_true", help="Preserve the current shipped form versions before replacing them")
    args = parser.parse_args()
    result = build_catalog(json.loads(args.catalog.read_text()), json.loads(args.structured.read_text()))
    encoded = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    packed = args.output.with_suffix(args.output.suffix + '.gz')
    if args.check:
        if not args.output.exists() or args.output.read_text() != encoded:
            raise SystemExit("Descriptor catalogue is out of date")
        if not packed.exists() or gzip.decompress(packed.read_bytes()) != encoded.encode():
            raise SystemExit('Packed descriptor catalogue is out of date')
    else:
        if args.archive_current and args.output.exists():
            previous = json.loads(args.output.read_text())
            previous_hash = previous.get('schema_hash')
            if previous_hash != digest({key:value for key,value in previous.items() if key != 'schema_hash'}):
                raise SystemExit('Current catalogue identity is invalid; review before archiving')
            if previous_hash != result['schema_hash']:
                history = args.output.parent / 'descriptor-history'
                history.mkdir(exist_ok=True)
                archive = history / (previous_hash + '.json.gz')
                if archive.exists() and json.loads(gzip.decompress(archive.read_bytes())) != previous:
                    raise SystemExit('A different catalogue already uses this archive identity')
                if not archive.exists():
                    archive.write_bytes(gzip.compress(args.output.read_bytes(), mtime=0))
        args.output.write_text(encoded)
        packed.write_bytes(gzip.compress(encoded.encode(), mtime=0))
    print(json.dumps(result["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
