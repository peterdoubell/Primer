"""Descriptor compiler invariants; clinical source statements remain unchanged."""

from __future__ import annotations

import copy
import gzip
import importlib.util
import json
import re
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("descriptor_compiler", ROOT / "tools/build_descriptor_reporting.py")
COMPILER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(COMPILER)
CATALOG = json.loads((ROOT / "data/radiology/descriptor-reporting.json").read_text())
# Retained contract for existing saved drafts; source-only assertions do not
# confuse the new, independently authored anatomy rows with verbatim sources.
SOURCE_CATALOG = json.loads(gzip.decompress((ROOT / "data/radiology/descriptor-reporting-v1.json.gz").read_bytes()))


def descriptors():
    for form in CATALOG["forms"].values():
        for investigation in form["investigations"]:
            for section in investigation["sections"]:
                if section["normal"]:
                    yield form, investigation, section, section["normal"]
                for descriptor in section["findings"]:
                    yield form, investigation, section, descriptor


def test_complete_source_inventory_is_separated_from_template_worksheets():
    summary = CATALOG["summary"]
    assert len(CATALOG["forms"]) == summary["guides"] == 98
    assert summary["source_investigations"] == 138
    assert summary["source_sections"] == 705
    assert summary["investigations"] == sum(len(form["investigations"]) for form in CATALOG["forms"].values())
    assert summary["sections"] == sum(len(inv["sections"]) for form in CATALOG["forms"].values() for inv in form["investigations"])
    assert summary["source_finding_statements"] == 1924
    assert summary["source_normal_statements"] == 524
    assert summary["source_worksheets"] == 14
    assert summary["worksheet_sections"] == 74
    assert summary["source_descriptors"] == 2522
    assert summary["anatomic_investigations"] == len(CATALOG["anatomic_coverage"])
    assert summary["anatomic_structures"] > summary["source_sections"]
    assert len(list(descriptors())) == summary["descriptors"]


def test_source_snapshot_and_content_hashes_pin_the_actual_contract():
    structured = json.loads((ROOT / "data/radiology/structured-reporting.json").read_text())
    assert CATALOG["source_snapshot_id"] == structured["source_snapshot_id"]
    for form in CATALOG["forms"].values():
        assert form["source_snapshot_id"] == CATALOG["source_snapshot_id"]
        assert form["schema_hash"] == COMPILER.digest({key: value for key, value in form.items() if key != "schema_hash"})
    assert CATALOG["schema_hash"] == COMPILER.digest({key: value for key, value in CATALOG.items() if key != "schema_hash"})


def test_shoulder_modalities_are_separate_without_normalizing_away_limits():
    form = SOURCE_CATALOG["forms"]["rad.5.shoulder"]
    investigations = {item["id"]: item for item in form["investigations"]}
    assert set(investigations) == {"ra.mri-shoulder", "ra.ultrasound-shoulder"}
    mr = investigations["ra.mri-shoulder"]
    us = investigations["ra.ultrasound-shoulder"]
    assert mr["modality"] == "MRI"
    assert us["modality"] == "Ultrasound"
    assert len(mr["sections"]) == len(us["sections"]) == 5
    us_text = " ".join(section["normal"]["text"] for section in us["sections"] if section["normal"])
    assert "labrum and deep intra-articular structures are not assessed by ultrasound" in us_text
    assert "Glenoid labrum intact" not in us_text
    assert next(section for section in us["sections"] if section["label"] == "Long head of biceps")["report_section_id"] is None


def test_every_source_character_survives_compilation_and_slots_cover_all_tokens():
    for form, investigation, section, descriptor in descriptors():
        text = descriptor["text"]
        slots = {slot["id"]: slot for slot in descriptor["slots"]}
        restored = "".join(segment["text"] if "text" in segment else slots[segment["slot"]]["source_token"] for segment in descriptor["segments"])
        assert restored == text, (form["guide_id"], descriptor["id"])
        assert descriptor["source"]["statement_sha256"] == COMPILER.digest(text)
        assert descriptor["source"]["investigation_id"] == investigation["id"]
        assert descriptor["requires_context"] == any(slot["kind"] == "context" for slot in slots.values())
        for segment in descriptor["segments"]:
            if "text" in segment:
                assert not re.search(r"\[|\]|_{2,}", segment["text"]), descriptor["id"]
        for slot in slots.values():
            span = slot["source_span"]
            assert text[span["start"]:span["end"]] == slot["source_token"]
            assert slot["required"] is True
            assert slot["kind"] in {"choice", "number", "context"}
            assert "default" not in slot
            if slot["kind"] == "choice":
                assert len(slot["options"]) >= 2
                if "options_source" in slot:
                    source = slot["options_source"]
                    assert source["kind"] == "same-investigation-authored-anatomy"
                    assert form["guide_id"] == "rad.5.shoulder"
                    assert investigation["id"] == "ra.mri-shoulder"
                    assert COMPILER.digest(source["normal_statement"]) == source["normal_statement_sha256"]
                    assert all(option["value"] in source["normal_statement"].lower() for option in slot["options"])
                else:
                    assert [item["value"] for item in slot["options"]] == COMPILER.choice_options(slot["source_token"][1:-1].strip())
                    assert all(option["value"] == option["label"] for option in slot["options"])
            else:
                assert slot["options"] == []


def test_source_normals_are_explicit_complete_statements_not_placeholder_prompts():
    normals = 0
    assessment = 0
    for form in SOURCE_CATALOG["forms"].values():
        for investigation in form["investigations"]:
            section_ids = [section["id"] for section in investigation["sections"]]
            assert len(set(section_ids)) == len(section_ids)
            for section in investigation["sections"]:
                if section["normal"]:
                    normals += 1
                    assert section["normal"]["slots"] == []
                    assert section["normal"]["label"] == "Normal"
                finding_ids = [finding["id"] for finding in section["findings"]]
                assert len(set(finding_ids)) == len(finding_ids)
                for finding in section["findings"]:
                    if finding["source"]["kind"] == "normal":
                        assessment += 1
                        assert finding["label"] == "Assessment"
                        assert finding["slots"]
    assert normals == 438
    assert assessment == 86


@pytest.mark.parametrize("token", [
    "right", "date", "method", "size / distribution", "structure / question",
    "not included / findings", "source/coverage", "restored / persistent shift of __ mm",
    "none / reason and range", "not assessable / specify", "absent / site and course",
])
def test_examples_and_context_prompts_are_not_guessed_choices(token):
    assert COMPILER.choice_options(token) == []


@pytest.mark.parametrize(("token", "choices"), [
    ("articular-sided / bursal-sided / intrasubstance", ["articular-sided", "bursal-sided", "intrasubstance"]),
    ("with / without", ["with", "without"]),
    ("adequate source/coverage / limited / unassessed", ["adequate source/coverage", "limited", "unassessed"]),
])
def test_only_authored_alternatives_become_selectable_values(token, choices):
    assert COMPILER.choice_options(token) == choices


def test_nested_placeholders_remain_explicit_context_not_invalid_choice_text():
    text = "Alignment [restored / persistent talar shift of __ mm]. Size __ × __ mm."
    statement = COMPILER.compile_statement(text, kind="finding", source={"investigation_id": "example", "step_index": 0})
    assert [slot["kind"] for slot in statement["slots"]] == ["context", "number", "number"]
    assert statement["slots"][0]["options"] == []
    assert [slot.get("unit") for slot in statement["slots"]] == [None, "mm", "mm"]


def test_stage_strings_are_not_assumed_to_be_plain_measurement_numbers():
    statement = COMPILER.compile_statement("Stage cT__ cN__ cM__; size __ mm.", kind="finding", source={"investigation_id": "example", "step_index": 0})
    assert [slot["kind"] for slot in statement["slots"]] == ["context", "context", "context", "number"]


def test_mri_shoulder_partial_tear_and_tendinosis_need_no_unenumerated_tendon_text():
    form = SOURCE_CATALOG["forms"]["rad.5.shoulder"]
    investigation = next(item for item in form["investigations"] if item["id"] == "ra.mri-shoulder")
    cuff = next(section for section in investigation["sections"] if section["source_sections"] == ["ROTATOR CUFF"])
    partial = next(finding for finding in cuff["findings"] if finding["text"].startswith("Partial-thickness"))
    tendinosis = next(finding for finding in cuff["findings"] if finding["text"].startswith("Tendinosis"))
    assert not partial["requires_context"]
    assert not tendinosis["requires_context"]
    assert [slot["kind"] for slot in partial["slots"]] == ["choice", "choice", "number", "number"]
    tendon = partial["slots"][1]
    assert [option["value"] for option in tendon["options"]] == ["supraspinatus", "infraspinatus", "subscapularis", "teres minor"]
    structured = json.loads((ROOT / "data/radiology/structured-reporting.json").read_text())["forms"]["rad.5.shoulder"]
    fields = {field["id"]: field for section in structured["sections"] for field in section["fields"]}
    for option in tendon["options"]:
        field = fields[option["source_field_id"]]
        assert field["group_label"] == option["label"]
        assert option["value"] == field["group_label"].lower()
        assert field["source_kind"] == "curated-source-backed"
    chosen = {"slot-1": "articular-sided", "slot-2": "supraspinatus", "slot-3": 30, "slot-4": 8}
    report = "".join(segment["text"] if "text" in segment else str(chosen[segment["slot"]]) for segment in partial["segments"])
    assert report == "Partial-thickness articular-sided supraspinatus tear involving approximately 30% of tendon thickness, 8 mm long."


def test_shoulder_numeric_constraints_match_existing_source_fields():
    form = SOURCE_CATALOG["forms"]["rad.5.shoulder"]
    investigation = next(item for item in form["investigations"] if item["id"] == "ra.mri-shoulder")
    cuff = next(section for section in investigation["sections"] if section["source_sections"] == ["ROTATOR CUFF"])
    structured = json.loads((ROOT / "data/radiology/structured-reporting.json").read_text())["forms"]["rad.5.shoulder"]
    fields = {field["id"]: field for section in structured["sections"] for field in section["fields"]}
    for finding in cuff["findings"]:
        for slot in finding["slots"]:
            if "constraints_source" not in slot:
                continue
            for source_id in slot["constraints_source"]["source_field_ids"]:
                source_field = fields[source_id]
                assert {key: slot[key] for key in ("minimum", "maximum") if key in slot} == {key: source_field[key] for key in ("minimum", "maximum") if key in source_field}
                assert source_field["unit"] == slot["unit"]
    partial = next(finding for finding in cuff["findings"] if finding["text"].startswith("Partial-thickness"))
    assert partial["slots"][2]["minimum"] == 0
    assert partial["slots"][2]["maximum"] == 100
    assert partial["slots"][3]["minimum"] == 0
    assert partial["slots"][2]["label"] == "Tendon thickness involved (%)"
    assert partial["slots"][3]["label"] == "Tear length (mm)"


@pytest.mark.parametrize(("depth", "length"), [(150, 8), (-1, 8), (30, -3)])
def test_shoulder_report_rejects_impossible_source_bounded_measurements(depth, length):
    engine_spec = importlib.util.spec_from_file_location("descriptor_engine", ROOT / "primer/descriptor_reporting.py")
    engine = importlib.util.module_from_spec(engine_spec)
    engine_spec.loader.exec_module(engine)
    form = SOURCE_CATALOG["forms"]["rad.5.shoulder"]
    investigation = next(item for item in form["investigations"] if item["id"] == "ra.mri-shoulder")
    cuff = next(section for section in investigation["sections"] if section["source_sections"] == ["ROTATOR CUFF"])
    partial = next(finding for finding in cuff["findings"] if finding["text"].startswith("Partial-thickness"))
    state = {"investigation_id": investigation["id"], "selections": {cuff["id"]: {"findings": {partial["id"]: {"slot-1": "articular-sided", "slot-2": "supraspinatus", "slot-3": depth, "slot-4": length}}}}}
    result = engine.render_descriptors(form, state)
    assert not result["valid"]
    assert result["text"] == ""
    assert "descriptor_number_out_of_range" in {issue["code"] for issue in result["issues"]}


@pytest.mark.parametrize(("source", "required", "forbidden"), [
    ("Medial [subluxation / dislocation] of the long-head biceps tendon from the bicipital groove, with an associated upper subscapularis tear.", "subluxation/dislocation", "Medial of"),
    ("Glenohumeral cartilage loss, [focal / diffuse], with [osteophytes / subchondral change].", "Glenohumeral cartilage loss", ", ,"),
    ("Os acromiale at the [pre-acromion / meso-acromion / meta-acromion] level [with / without] oedema at the synchondrosis.", "Os acromiale", "at the level"),
])
def test_selectable_labels_keep_diagnostic_words_and_readable_punctuation(source, required, forbidden):
    label = COMPILER.short_label(source, "Assessment")
    assert required in label
    assert forbidden not in label
    assert len(label) <= 76


def test_compilation_is_reproducible_and_defaults_are_never_inserted():
    catalogue = {"manifest": {"snapshot_id": "source-123"}, "guides": [{
        "id": "example", "title": "Two investigations", "templates": [{"id": "example-report"}],
        "investigations": [{"id": "mri", "modality": "MRI"}, {"id": "us", "modality": "Ultrasound"}],
        "steps": [{"investigation_id": identity, "title": title, "source_file": "source.json", "steps": [{
            "sections": ["TENDON"], "normal": "Tendon intact.",
            "findings": ["[Partial / complete] tear, __ mm at [location]."],
        }]} for identity, title in [("mri", "MRI tendon"), ("us", "Ultrasound tendon")]],
    }]}
    structured = {"forms": {"example": {"template_id": "example-report", "sections": [{"section_id": "tendon", "label": "TENDON"}], "calculator_ids": []}}}
    first = COMPILER.build_catalog(catalogue, structured, anatomic=False)
    second = COMPILER.build_catalog(copy.deepcopy(catalogue), copy.deepcopy(structured), anatomic=False)
    assert first == second
    section = first["forms"]["example"]["investigations"][0]["sections"][0]
    assert section["report_section_id"] == "tendon"
    assert [slot["kind"] for slot in section["findings"][0]["slots"]] == ["choice", "number", "context"]
    assert '"default":' not in json.dumps(first)
