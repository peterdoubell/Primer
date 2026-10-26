import copy
import hashlib
import json
from pathlib import Path

import pytest

from tools.anatomy_sources.reconcile_current_reporting_requirements import (
    BRAIN, OUT, REPORT_FILE, REQUIREMENTS, REPRESENTATIONS, brain_additions,
    before_current_brain_requirements, brain_crosswalk, digest, expand_brain, read, replace_brain_bytes,
    reporting_reconciliation,
)

ROOT = Path(__file__).resolve().parents[1]
LEGACY_BRAIN_SHA256 = "6f7b8df6cc14e95374a74d4a950150f23a38cb1c2d2ec3d1bfea626f041d3556"
LEGACY_REQUIREMENTS_SHA256 = "405f3fe902e9fdce1f9d3834dff72898911135acd0b6a170bdc7d00868ad868d"


def inputs():
    data = read(REQUIREMENTS)
    report = read(REPORT_FILE)["investigations"][BRAIN]
    brain = next(i for i in data["investigations"] if i["investigation_id"] == BRAIN)
    return data, report, brain


def test_thirty_side_targets_reconcile_twenty_eight_rows_and_preserve_every_prior_byte():
    data, report, brain = inputs()
    additions = brain_additions(report)
    ids = {p["id"] for _, p in additions}
    assert len(ids) == 30
    assert len({p["reporting_provenance"]["section_id"] for _, p in additions}) == 28
    old = copy.deepcopy(brain)
    for structure in old["structures"]:
        structure["required_parts"] = [p for p in structure["required_parts"] if p["id"] not in ids]
    assert sum(len(s["required_parts"]) for s in old["structures"]) == 210
    assert digest(old) == LEGACY_BRAIN_SHA256
    restored = replace_brain_bytes((ROOT / REQUIREMENTS).read_text(), old)
    assert hashlib.sha256(restored.encode()).hexdigest() == LEGACY_REQUIREMENTS_SHA256
    assert before_current_brain_requirements((ROOT / REQUIREMENTS).read_bytes()) == restored.encode()
    assert before_current_brain_requirements(restored) == restored
    assert expand_brain(data, report) == data
    for _, part in additions:
        assert part["required_representations"] == REPRESENTATIONS
        assert part["representation_completion_claim"] is False
        assert part["reporting_provenance"]["side_instantiation"] in ("left", "right")


def test_expansion_rejects_changed_target_and_missing_current_row():
    data, report, brain = inputs()
    next(p for s in brain["structures"] for p in s["required_parts"] if p["id"].endswith("superior_frontal_gyrus"))["name"] = "Different extent"
    with pytest.raises(ValueError, match="Conflicting prior expansion"):
        expand_brain(data, report)
    report["sections"] = [s for s in report["sections"] if s["id"] != "right-amygdala"]
    with pytest.raises(KeyError):
        brain_additions(report)


@pytest.mark.parametrize("change", ["old_part", "added_part", "deleted_added_part"])
def test_receipt_inverse_never_discards_unknown_changes(change):
    _, _, brain = inputs()
    if change == "old_part":
        brain["structures"][0]["required_parts"][0]["name"] = "Altered old anatomy"
    elif change == "added_part":
        brain["structures"][0]["required_parts"][-1]["required_extent"] = "Different extent"
    else:
        brain["structures"][0]["required_parts"].pop()
    raw = replace_brain_bytes((ROOT / REQUIREMENTS).read_text(), brain)
    with pytest.raises(ValueError):
        before_current_brain_requirements(raw)


def test_all_sixty_two_brain_rows_have_explicit_ids_and_source_limitations():
    data, report, _ = inputs()
    actual = brain_crosswalk(ROOT, data, report)
    # The frozen reconciliation predates the separately verified atlas extension.
    # Restore only its exact input bytes; all semantic rows still compare intact.
    from tools.atlas_schematic_runtime_compatibility import before_atlas_schematic_bytes
    actual['input_sha256'] = {path: hashlib.sha256(before_atlas_schematic_bytes(path, (ROOT/path).read_bytes(), allow_older=True)).hexdigest() for path in actual['input_sha256']}
    assert actual == read(OUT + "/brain-reporting-requirements.json")
    assert len(actual["all_report_rows"]) == 62
    assert all(r["requirement_ids"] and not r["clinical_representation_complete"] for r in actual["all_report_rows"])
    rows = actual["source_context_crosswalk"]
    mca = [r for r in rows if "_division_territory" in r["requirement_id"]]
    assert len(mca) == 4
    assert all(not r["source_context"] and r["relationship"] == "no_source_territory_mask" for r in mca)
    amygdala = [r for r in rows if r["requirement_id"].endswith(".amygdala")]
    assert len(amygdala) == 2
    assert all(len(r["source_context"][0]["fine_source_codes"]) == 8 for r in amygdala)
    assert all(len(r["source_context"][0]["present_fine_source_codes"]) == 7 for r in amygdala)


def test_global_reconciliation_retains_all_report_rows_without_module_alias_shortcuts():
    data, _, _ = inputs()
    result = reporting_reconciliation(ROOT, data)
    assert result == read("docs/report-additions-20261026/reporting-reconciliation.json")
    assert (result["current_investigations"], result["current_report_rows"]) == (225, 5776)
    assert (result["expanded_investigation_identities"], result["without_dedicated_inventory"]) == (96, 129)
    rows = {r["investigation_id"]: r for r in result["investigations"]}
    assert rows["ra.thoracolumbar-injury"]["relationship"] == "declared_duplicate_pathway_with_unresolved_instantiation"
    levels = [r for r in rows["ra.thoracolumbar-injury"]["report_rows"] if r["candidate_requirements"] and r["candidate_requirements"][0]["relationship"] == "explicit_level_instance_of_unresolved_template"]
    assert len(levels) == 17
    assert rows["ra.thymus"]["related_expanded_investigation_ids"] == ["ra.ct-mediastinum"]
    assert rows["msk.mri-hand"]["relationship"] == "related_region_new_dedicated_scope"
    assert rows["ra.paediatric-hip"]["relationship"] == "unexpanded_distinct_investigation"
    assert "ra.paediatric-elbow-fractures" in rows["ra.paediatric-hip"]["same_module_ids_not_accepted_as_equivalent"]
    assert all(not r["clinical_representation_complete"] for r in result["investigations"])
    assert all(not s["representation_completion_claim"] for r in result["investigations"] for s in r["report_rows"])


@pytest.mark.parametrize("change", ["relocated", "duplicated"])
def test_expansion_and_inverse_reject_wrong_parent_or_duplicate(change):
    data, report, brain = inputs()
    parents = {s["id"]: s for s in brain["structures"]}
    right = parents["brain.right_surface"]["required_parts"]
    part = next(p for p in right if p["id"] == "brain.right_surface.superior_frontal_gyrus")
    parents["brain.left_surface"]["required_parts"].append(copy.deepcopy(part))
    if change == "relocated":
        right.remove(part)
    with pytest.raises(ValueError):
        expand_brain(data, report)
    raw = replace_brain_bytes((ROOT / REQUIREMENTS).read_text(), brain)
    with pytest.raises(ValueError):
        before_current_brain_requirements(raw)
