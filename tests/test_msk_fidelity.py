"""The MSK goal must not be satisfied by name matches or arbitrary green counts."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("msk_fidelity", ROOT / "tools/check_msk_fidelity.py")
fidelity = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fidelity)


def bind_synthetic_reviews(asset, requirements):
    """Only fixtures may simulate the result of a new review in these tests."""
    digest = fidelity.review_scope_fingerprint(asset, requirements)
    for field in fidelity.REVIEW_FIELDS:
        asset[field]["review_scope_sha256"] = digest


@pytest.fixture
def case(tmp_path):
    (tmp_path / "mesh.bin").write_bytes(b"isolated test fixture, not anatomical evidence")
    digest = hashlib.sha256((tmp_path / "mesh.bin").read_bytes()).hexdigest()
    (tmp_path / "review.md").write_text("Synthetic test review, never real clinical approval")
    requirements = {"clinical_validation_status": "approved",
                    "scope": {"catalog_investigation_ids": ["ra.example"]},
                    "investigations": [{"investigation_id": "ra.example", "modality": "MRI",
                        "reporting_checklist": [{"label": "Menisci", "detail": "Describe body and root"}],
                        "structures": [
                        {"id": "knee.meniscus", "name": "Meniscus", "condition": "Examined knee",
                         "modality_scope": ["MRI"], "laterality": "examined_side",
                         "report_refs": [{"checklist_index": 0, "label": "Menisci",
                                          "detail": "Describe body and root"}], "required_parts": [
                            {"id": "knee.meniscus.root", "name": "Root"},
                            {"id": "knee.meniscus.body", "name": "Body"}]}]}]}
    asset = {"id": "fixture", "kind": "model", "modality": "MRI", "local_path": "mesh.bin", "sha256": digest,
             "structure_ids": ["knee.meniscus.root", "knee.meniscus.body"],
             "investigation_ids": ["ra.example"], "fidelity": "high",
             "source": {"url": "https://example.test/source", "license": {
                 "url": "https://example.test/license", "commercial_use": True,
                 "redistribution": True, "review_status": "verified", "attribution": "Test fixture"}}}
    asset['requirement_coverage'] = {
        identifier: {'extent': 'complete', 'basis': 'Synthetic fixture only, not anatomical evidence'}
        for identifier in asset['structure_ids']
    }
    for kind in ("anatomical_review", "visual_review"):
        asset[kind] = {"status": "approved", "reviewer": "TEST FIXTURE", "evidence_path": "review.md",
                       "reviewed_at": "2026-09-26", "sha256": digest}
    bind_synthetic_reviews(asset, requirements)
    return requirements, {"assets": [asset]}, tmp_path


def test_three_representation_types_are_required_independently(case):
    requirements, evidence, root = case
    result = fidelity.audit(requirements, evidence, root)
    assert result["representation_requirements"] == 6
    assert result["counts"] == {"verified": 2, "unverified": 0, "missing": 4}
    assert not result["clinical_commercial_ready"]


def test_parent_mesh_does_not_prove_substructures(case):
    requirements, evidence, root = case
    evidence["assets"][0]["structure_ids"] = ["knee.meniscus"]
    assert fidelity.audit(requirements, evidence, root)["counts"]["missing"] == 6


def test_refreshed_fixture_reviews_do_not_clear_a_contradictory_panel_state(case):
    requirements, evidence, root = case
    asset = evidence['assets'][0]
    asset.update(kind='clinical_image', modality='MRI',
                 source_context={'depicted_state': 'normal_anatomical_reference',
                                 'selected_panels': ['a'], 'panel_types': {'a': 'MRI', 'b': 'MRI'},
                                 'panel_states': {'a': 'normal_anatomy', 'b': 'tear'}},
                 representation_selection={'kind': 'clinical_image', 'panels': ['a']})
    bind_synthetic_reviews(asset, requirements)
    assert fidelity.audit(requirements, evidence, root)['counts']['verified'] == 2
    asset['source_context']['selected_panels'] = ['b']
    asset['representation_selection']['panels'] = ['b']
    bind_synthetic_reviews(asset, requirements)  # TEST FIXTURE ONLY; never a real approval.
    result = fidelity.audit(requirements, evidence, root)
    assert not any('_scope_missing_or_stale' in issue for issue in result['asset_issues'][asset['id']])
    assert result['counts']['verified'] == 0
    rows = [row for row in result['requirements'] if row['kind'] == 'clinical_image']
    assert all('source_context_selected_panel_state_mismatch' in row['candidates'][asset['id']] for row in rows)


@pytest.mark.parametrize("change,expected", [
    ("fidelity", "high_fidelity_unproven"),
    ("license", "commercial_rights_unverified"),
    ("review", "anatomical_review_missing_or_stale"),
    ("hash", "asset_fingerprint_mismatch"),
    ("review_hash", "anatomical_review_missing_or_stale"),
    ("review_evidence", "anatomical_review_evidence_missing"),
])
def test_missing_or_stale_proof_cannot_pass(case, change, expected):
    requirements, evidence, root = case
    asset = evidence["assets"][0]
    if change == "fidelity": asset["fidelity"] = "schematic"
    if change == "license": asset["source"]["license"]["commercial_use"] = False
    if change == "review": asset["anatomical_review"]["status"] = "pending"
    if change == "hash": (root / "mesh.bin").write_bytes(b"changed after review")
    if change == "review_hash": asset["anatomical_review"]["sha256"] = "0" * 64
    if change == "review_evidence": (root / "review.md").unlink()
    result = fidelity.audit(requirements, evidence, root)
    assert expected in result["asset_issues"]["fixture"]
    assert result["counts"]["verified"] == 0


def test_one_approved_example_cannot_satisfy_region_dependent_scope(case):
    requirements, evidence, root = case
    for kind in ("clinical_image", "schematic"):
        extra = copy.deepcopy(evidence["assets"][0]); extra["kind"] = kind; extra["id"] = kind
        bind_synthetic_reviews(extra, requirements)
        evidence["assets"].append(extra)
    assert fidelity.audit(requirements, evidence, root,
                          runtime_images={'surfaces': [], 'images': []})["clinical_commercial_ready"]
    requirements["investigations"][0]["expansion_rules"] = ["Must support the affected anatomical site"]
    assert not fidelity.audit(requirements, evidence, root)["clinical_commercial_ready"]


def test_empty_scope_and_path_escape_are_rejected(case):
    requirements, evidence, root = case
    with pytest.raises(ValueError, match="empty"):
        fidelity.audit({"investigations": []}, evidence, root)
    evidence["assets"][0]["local_path"] = "../private.bin"
    with pytest.raises(ValueError, match="leaves project"):
        fidelity.audit(requirements, evidence, root)


def test_scope_cannot_be_narrowed_to_the_assets_already_available(case):
    requirements, evidence, root = case
    with pytest.raises(ValueError, match="authoritative"):
        fidelity.audit(requirements, evidence, root, expected_catalog_ids={'ra.example', 'ra.missing'})


def test_changed_report_fields_invalidate_the_structure_inventory():
    requirements = {'investigations': [{'investigation_id': 'ra.example', 'structures': [],
                    'reporting_checklist': [{'label': 'Ligament', 'detail': 'Describe attachments'}],
                    'reporting_template_sections': [{'heading': 'LIGAMENT', 'body': 'Attachments [ ]'}]}]}
    guide = {'checklist': [{'label': 'Ligament', 'detail': 'Describe attachments'}],
             'template_sections': [{'heading': 'LIGAMENT', 'body': 'Attachments [ ]'}]}
    fidelity.validate_reporting_snapshots(requirements, {'ra.example': guide})
    guide['checklist'].append({'label': 'New structure', 'detail': 'Report this too'})
    with pytest.raises(ValueError, match='checklist changed'):
        fidelity.validate_reporting_snapshots(requirements, {'ra.example': guide})


@pytest.mark.parametrize("field", fidelity.REVIEW_FIELDS)
def test_file_hash_alone_cannot_authorize_an_unrecorded_scope(case, field):
    requirements, evidence, root = case
    asset = evidence["assets"][0]
    del asset[field]["review_scope_sha256"]
    result = fidelity.audit(requirements, evidence, root)
    assert field + "_scope_missing_or_stale" in result["asset_issues"]["fixture"]
    assert result["counts"]["verified"] == 0


@pytest.mark.parametrize("field,value", [
    ("id", "different-evidence-record"),
    ("kind", "schematic"),
    ("structure_ids", ["knee.meniscus.root"]),
    ("investigation_ids", ["ra.example", "ra.other"]),
    ("modality", "Radiography"),
    ("context", "Direct evidence of intact anatomy"),
    ("representation_selection", {"panels": ["b"], "kind": "schematic"}),
    ("structures_observed", ["Different structure"]),
    ("future_anatomical_claim", "A new meaning-bearing field"),
])
def test_changed_claims_cannot_reuse_approved_bytes(case, field, value):
    requirements, evidence, root = case
    asset = evidence["assets"][0]
    original_file_hash = asset["sha256"]
    asset[field] = value
    result = fidelity.audit(requirements, evidence, root)
    assert hashlib.sha256((root / "mesh.bin").read_bytes()).hexdigest() == original_file_hash
    assert result["counts"]["verified"] == 0
    for review in fidelity.REVIEW_FIELDS:
        assert review + "_scope_missing_or_stale" in result["asset_issues"][asset["id"]]


@pytest.mark.parametrize("change", [
    "parent_name", "part_name", "part_definition", "condition", "laterality",
    "modality_scope", "image_visibility", "report_refs", "component_boundary",
    "investigation_modality", "reporting_checklist", "conventions",
])
def test_changed_requirement_meaning_invalidates_old_review(case, change):
    requirements, evidence, root = case
    investigation = requirements["investigations"][0]
    parent = investigation["structures"][0]
    if change == "parent_name": parent["name"] = "A different anatomical target"
    if change == "part_name": parent["required_parts"][0]["name"] = "Different attachment"
    if change == "part_definition": parent["required_parts"][0]["condition"] = "Include the insertion"
    if change == "condition": parent["condition"] = "Direct continuity evidence required"
    if change == "laterality": parent["laterality"] = "right"
    if change == "modality_scope": parent["modality_scope"] = ["MR arthrography"]
    if change == "image_visibility": parent["image_visibility"] = "direct_only"
    if change == "report_refs": parent["report_refs"][0]["detail"] = "New report obligation"
    if change == "component_boundary":
        parent["required_parts"].append({"id": "knee.meniscus.attachment", "name": "Attachment"})
    if change == "investigation_modality": investigation["modality"] = "Radiography"
    if change == "reporting_checklist": investigation["reporting_checklist"][0]["detail"] = "New scope"
    if change == "conventions": requirements["conventions"] = {"visibility": "Direct evidence only"}
    result = fidelity.audit(requirements, evidence, root)
    assert result["counts"]["verified"] == 0
    for review in fidelity.REVIEW_FIELDS:
        assert review + "_scope_missing_or_stale" in result["asset_issues"]["fixture"]


def test_rebinding_to_another_real_investigation_requires_review(case):
    requirements, evidence, root = case
    other = copy.deepcopy(requirements["investigations"][0])
    other["investigation_id"] = "ra.other"
    requirements["investigations"].append(other)
    requirements["scope"]["catalog_investigation_ids"].append("ra.other")
    asset = evidence["assets"][0]
    assert fidelity.audit(requirements, evidence, root)["counts"]["verified"] == 2
    asset["investigation_ids"] = ["ra.other"]
    result = fidelity.audit(requirements, evidence, root)
    assert result["counts"]["verified"] == 0
    assert "anatomical_review_scope_missing_or_stale" in result["asset_issues"]["fixture"]


def test_same_figure_bytes_do_not_transfer_approval_between_panels(case):
    requirements, evidence, root = case
    asset = evidence["assets"][0]
    asset.update(kind="clinical_image", representation_selection={"panels": ["a"]})
    bind_synthetic_reviews(asset, requirements)
    drawing = copy.deepcopy(asset)
    drawing.update(id="drawing-panel", kind="schematic", representation_selection={"panels": ["b"]})
    evidence["assets"].append(drawing)
    result = fidelity.audit(requirements, evidence, root)
    assert asset["sha256"] == drawing["sha256"]
    assert result["counts"] == {"verified": 2, "unverified": 2, "missing": 2}
    assert result["asset_issues"]["fixture"] == []
    assert "visual_review_scope_missing_or_stale" in result["asset_issues"]["drawing-panel"]


def test_exact_scope_is_stable_and_review_metadata_is_not_circular(case):
    requirements, evidence, root = case
    asset = evidence["assets"][0]
    expected = fidelity.review_scope_fingerprint(asset, requirements)
    # Object serialization order and separate review bookkeeping do not change claims.
    reordered = json.loads(json.dumps(asset, sort_keys=True))
    reordered["anatomical_review"]["reviewer"] = "ANOTHER SYNTHETIC REVIEWER"
    assert fidelity.review_scope_fingerprint(reordered, copy.deepcopy(requirements)) == expected
    result = fidelity.audit(requirements, {"assets": [reordered]}, root)
    assert result["review_scope_sha256"]["fixture"] == expected
    assert result["asset_issues"]["fixture"] == []
    assert result["counts"]["verified"] == 2


def test_unrelated_structure_does_not_invalidate_exact_scope(case):
    requirements, evidence, root = case
    requirements["investigations"][0]["structures"].append({"id": "knee.patella", "name": "Patella"})
    result = fidelity.audit(requirements, evidence, root)
    assert result["asset_issues"]["fixture"] == []
    assert result["counts"]["verified"] == 2


def test_requirement_review_bookkeeping_does_not_change_anatomical_scope(case):
    requirements, evidence, root = case
    asset = evidence["assets"][0]
    investigation = requirements["investigations"][0]
    investigation["sources"] = [{"url": "https://example.test/anatomy", "review_status": "pending"}]
    bind_synthetic_reviews(asset, requirements)
    expected = fidelity.review_scope_fingerprint(asset, requirements)
    requirements.update(clinical_validation_status="draft", reviewed_at="2026-09-27")
    investigation.update(clinical_validation_status="approved", reviewed_at="2026-09-27",
                         site_expansion_review={"status": "approved", "reviewer": "TEST FIXTURE"})
    investigation["sources"][0]["review_status"] = "reviewed"
    investigation["structures"][0].update(reviewed_by="TEST FIXTURE", reviewed_at="2026-09-27")
    assert fidelity.review_scope_fingerprint(asset, requirements) == expected
    result = fidelity.audit(requirements, evidence, root)
    assert result["asset_issues"]["fixture"] == []
    assert result["counts"]["verified"] == 2
    # Inventory approval is still an independent completeness gate.
    assert not result["clinical_commercial_ready"]


def synthetic_boundary(case):
    """A fixture document is classification evidence, never clinical approval."""
    requirements, _, root = case
    content = b"SYNTHETIC FIXTURE: this boundary retains all anatomical requirements."
    (root / "boundary.md").write_bytes(content)
    issue = {"code": "fixture_modality_limit", "detail": "Direct imaging has an acquisition condition.",
            "affected_checklist_indices": [0], "kind": "boundary_constraint", "status": "documented",
            "classification_note": "The report already states this condition; required targets remain.",
            "documentation": {"path": "boundary.md", "sha256": hashlib.sha256(content).hexdigest()}}
    issue['documentation']['reviewed_scope_sha256'] = fidelity.boundary_scope_fingerprint(requirements['investigations'][0], issue)
    return issue


def complete_synthetic_representations(case):
    requirements, evidence, _ = case
    for kind in ("clinical_image", "schematic"):
        asset = copy.deepcopy(evidence["assets"][0])
        asset.update(id=kind, kind=kind)
        evidence["assets"].append(asset)
    for asset in evidence["assets"]:
        bind_synthetic_reviews(asset, requirements)


def test_documented_boundary_is_visible_without_becoming_a_false_report_defect(case):
    requirements, evidence, root = case
    requirements["investigations"][0]["source_scope_issues"] = [synthetic_boundary(case)]
    complete_synthetic_representations(case)
    result = fidelity.audit(requirements, evidence, root,
                            runtime_images={'surfaces': [], 'images': []})
    assert result["clinical_commercial_ready"]
    assert result["representation_requirements"] == 6
    assert result["counts"] == {"verified": 6, "unverified": 0, "missing": 0}
    assert result["scope_gaps"] == []
    assert len(result["scope_issue_assessments"]) == 1
    issue = result["scope_issue_assessments"][0]
    assert issue["kind"] == "boundary_constraint" and issue["status"] == "documented"
    assert issue["blocking"] is False
    assert issue["reason"] == "documented_boundary_requirements_retained"
    assert issue["documentation"]["path"] == "boundary.md"


@pytest.mark.parametrize('change', ['checklist', 'template', 'anatomy', 'expansion', 'representations', 'boundary_claim'])
def test_boundary_decision_reopens_when_its_reviewed_scope_changes(case, change):
    requirements, _, root = case
    investigation = requirements['investigations'][0]
    issue = synthetic_boundary(case)
    assert fidelity.inspect_scope_issue(issue, investigation, root)['blocking'] is False
    if change == 'checklist':
        investigation['reporting_checklist'][0]['detail'] = 'Changed acquisition claim'
    elif change == 'template':
        investigation['reporting_template_sections'] = [{'heading': 'Changed', 'body': 'Changed claim'}]
    elif change == 'anatomy':
        investigation['structures'][0]['condition'] = 'A changed coverage condition'
    elif change == 'expansion':
        investigation['expansion_rules'] = ['A changed site expansion rule']
    elif change == 'representations':
        investigation['required_representations'] = ['model']
    else:
        issue['classification_note'] = 'A different interpretation of the same scope'
    # An unchanged document cannot justify a different report or anatomy scope.
    result = fidelity.inspect_scope_issue(issue, investigation, root)
    assert result['blocking'] is True
    assert result['reason'] == 'boundary_scope_missing_or_stale'


def test_boundary_scope_is_independent_of_review_status_and_other_issue_records(case):
    requirements, _, root = case
    investigation = requirements['investigations'][0]
    issue = synthetic_boundary(case)
    investigation['clinical_validation_status'] = 'a different review status'
    investigation['source_scope_issues'] = [issue, {'code': 'another_unresolved_issue'}]
    assert fidelity.inspect_scope_issue(issue, investigation, root)['blocking'] is False
    assert fidelity.inspect_scope_issue(investigation['source_scope_issues'][1], investigation, root)['blocking'] is True


@pytest.mark.parametrize("change", [
    "legacy", "unknown_kind", "unknown_status", "reporting_defect", "resolved_defect",
    "missing_note", "blank_detail", "missing_documentation", "missing_file", "stale_file",
    "missing_hash", "empty_file", "outside_project", "invalid_reference", "boolean_reference", "missing_scope_hash",
])
def test_only_explicit_supported_documented_boundaries_are_nonblocking(case, change):
    requirements, evidence, root = case
    issue = synthetic_boundary(case)
    if change == "legacy":
        issue.pop("kind"); issue.pop("status")
    if change == "unknown_kind": issue["kind"] = "informational"
    if change == "unknown_status": issue["status"] = "approved"
    if change == "reporting_defect": issue.update(kind="reporting_defect", status="unresolved")
    if change == "resolved_defect": issue.update(kind="reporting_defect", status="resolved")
    if change == "missing_note": issue.pop("classification_note")
    if change == "blank_detail": issue["detail"] = "  "
    if change == "missing_documentation": issue.pop("documentation")
    if change == "missing_file": (root / "boundary.md").unlink()
    if change == "stale_file": (root / "boundary.md").write_text("Changed after classification")
    if change == "missing_hash": issue["documentation"].pop("sha256")
    if change == "missing_scope_hash": issue["documentation"].pop("reviewed_scope_sha256")
    if change == "empty_file":
        (root / "boundary.md").write_bytes(b"")
        issue["documentation"]["sha256"] = hashlib.sha256(b"").hexdigest()
    if change == "outside_project": issue["documentation"]["path"] = "../outside.md"
    if change == "invalid_reference": issue["affected_checklist_indices"] = [9]
    if change == "boolean_reference": issue["affected_checklist_indices"] = [False]
    requirements["investigations"][0]["source_scope_issues"] = [issue]
    complete_synthetic_representations(case)
    result = fidelity.audit(requirements, evidence, root)
    assert result["counts"]["verified"] == 6, "Scope defect must block independently of asset approval"
    assert not result["clinical_commercial_ready"]
    assert result["scope_gaps"] and result["scope_issue_assessments"][0]["blocking"] is True


@pytest.mark.parametrize("issues", [None, {}, "unresolved", [None], ["legacy issue"]])
def test_malformed_or_legacy_scope_issues_fail_closed(case, issues):
    requirements, evidence, root = case
    requirements["investigations"][0]["source_scope_issues"] = issues
    complete_synthetic_representations(case)
    result = fidelity.audit(requirements, evidence, root)
    assert not result["clinical_commercial_ready"]
    assert result["scope_issue_assessments"][0]["blocking"] is True


def test_one_documented_boundary_does_not_hide_another_unclassified_issue(case):
    requirements, evidence, root = case
    requirements["investigations"][0]["source_scope_issues"] = [synthetic_boundary(case),
        {"code": "not_inspected", "detail": "This unrelated issue has not been reconciled."}]
    complete_synthetic_representations(case)
    result = fidelity.audit(requirements, evidence, root)
    assert [issue["blocking"] for issue in result["scope_issue_assessments"]] == [False, True]
    assert len(result["scope_gaps"]) == 1
    assert not result["clinical_commercial_ready"]


@pytest.mark.parametrize("gate", ["site_expansion", "site_instance", "inventory_review",
                                  "missing_representation", "asset_review", "commercial_rights"])
def test_documented_boundaries_do_not_waive_any_other_completion_gate(case, gate):
    requirements, evidence, root = case
    investigation = requirements["investigations"][0]
    investigation["source_scope_issues"] = [synthetic_boundary(case)]
    complete_synthetic_representations(case)
    if gate == "site_expansion": investigation["expansion_rules"] = ["Enumerate each actual site"]
    if gate == "site_instance": investigation["structures"][0]["requires_site_instantiation"] = True
    if gate == "inventory_review": requirements["clinical_validation_status"] = "draft"
    if gate == "missing_representation": evidence["assets"].pop()
    if gate == "asset_review": evidence["assets"][0]["visual_review"]["status"] = "pending"
    if gate == "commercial_rights": evidence["assets"][0]["source"]["license"]["commercial_use"] = False
    # This test gives the boundary a fresh scope review, then verifies that
    # independent site/asset/inventory obligations still prevent completion.
    boundary = investigation['source_scope_issues'][0]
    boundary['documentation']['reviewed_scope_sha256'] = fidelity.boundary_scope_fingerprint(investigation, boundary)
    for asset in evidence["assets"]:
        bind_synthetic_reviews(asset, requirements)
    result = fidelity.audit(requirements, evidence, root)
    assert result["scope_issue_assessments"][0]["blocking"] is False
    assert not result["clinical_commercial_ready"]


@pytest.mark.parametrize("change", ["kind", "status", "classification_note", "documentation"])
def test_scope_issue_classification_stays_inside_the_exact_review_fingerprint(case, change):
    requirements, evidence, root = case
    issue = synthetic_boundary(case)
    requirements["investigations"][0]["source_scope_issues"] = [issue]
    complete_synthetic_representations(case)
    original_hash = evidence["assets"][0]["sha256"]
    if change == "kind": issue["kind"] = "reporting_defect"
    if change == "status": issue["status"] = "pending"
    if change == "classification_note": issue["classification_note"] = "A different interpretation"
    if change == "documentation":
        (root / "another-boundary.md").write_bytes((root / "boundary.md").read_bytes())
        issue["documentation"]["path"] = "another-boundary.md"
    result = fidelity.audit(requirements, evidence, root)
    assert hashlib.sha256((root / "mesh.bin").read_bytes()).hexdigest() == original_hash
    assert result["counts"]["verified"] == 0
    for asset in evidence["assets"]:
        for review in fidelity.REVIEW_FIELDS:
            assert review + "_scope_missing_or_stale" in result["asset_issues"][asset["id"]]


def test_real_inventory_classifies_only_the_seven_explicitly_audited_boundaries():
    requirements = json.loads((ROOT / "data/radiology/msk-structure-requirements.json").read_text())
    documented = []
    unclassified = []
    for investigation in requirements["investigations"]:
        for issue in investigation.get("source_scope_issues", []):
            result = fidelity.inspect_scope_issue(issue, investigation, ROOT)
            if issue.get("kind") == "boundary_constraint":
                assert result["blocking"] is False
                documented.append((investigation["investigation_id"], issue["code"]))
            else:
                assert result["blocking"] is True
                unclassified.append(investigation["investigation_id"])
    assert set(documented) == {
        ("ra.ankle-fractures", "radiographic_soft_tissue_limit"),
        ("ra.ankle-fractures", "foot_coverage_conditional"),
        ("ra.thoracolumbar-fractures", "clinical_inputs_and_modality_limits"),
        ("ra.wrist-instability", "ligament_visibility"),
        ("ra.wrist-fractures", "ligament_visibility"),
        ("ra.mri-elbow", "historical_source_wording"),
        ("ra.hip-fai", "modality_condition_required"),
    }
    assert unclassified, "Uninspected source-scope records must not be mass reclassified"


@pytest.mark.parametrize('actual,scope,expected', [
    ('MRI', ['MRI'], None),
    ('Ultrasound', ['MRI'], 'clinical_image_modality_not_in_requirement_scope'),
    ('MRI', ['Radiography'], 'clinical_image_modality_not_in_requirement_scope'),
    ('MR arthrography', ['MRI', 'MR arthrography'], None),
    ('Ultrasound', ['Ultrasound when accessible'], None),
    ('MRI', ['MRI or ultrasound for unossified components'], None),
    ('Ultrasound', ['MRI or ultrasound for unossified components'], None),
    (None, ['MRI'], 'clinical_image_modality_missing_or_unknown'),
    ('Picture', ['MRI'], 'clinical_image_modality_missing_or_unknown'),
    ('MRI', [], 'requirement_modality_scope_missing_or_unknown'),
    ('MRI', ['some new MRI phrase'], 'requirement_modality_scope_missing_or_unknown'),
])
def test_even_reviewed_images_must_match_the_required_modality(case, actual, scope, expected):
    requirements, evidence, root = case
    requirements['investigations'][0]['structures'][0]['modality_scope'] = scope
    asset = evidence['assets'][0]
    asset.update(kind='clinical_image', modality=actual)
    bind_synthetic_reviews(asset, requirements)
    result = fidelity.audit(requirements, evidence, root)
    rows = [r for r in result['requirements'] if r['kind'] == 'clinical_image']
    assert all(r['status'] == ('unverified' if expected else 'verified') for r in rows)
    if expected:
        assert all(expected in r['candidates']['fixture'] for r in rows)


def test_image_compatibility_is_checked_per_investigation_binding(case):
    requirements, evidence, root = case
    other = copy.deepcopy(requirements['investigations'][0])
    other['investigation_id'] = 'ra.ultrasound-example'
    other['structures'][0]['modality_scope'] = ['Ultrasound']
    requirements['investigations'].append(other)
    requirements['scope']['catalog_investigation_ids'].append(other['investigation_id'])
    asset = evidence['assets'][0]
    asset.update(kind='clinical_image', modality='Ultrasound',
                 investigation_ids=['ra.example', other['investigation_id']])
    bind_synthetic_reviews(asset, requirements)
    rows = fidelity.audit(requirements, evidence, root)['requirements']
    for row in (r for r in rows if r['kind'] == 'clinical_image'):
        assert row['status'] == ('verified' if row['investigation_id'] == other['investigation_id'] else 'unverified')


def test_all_approved_representations_still_require_actual_runtime_rights_inventory(case):
    requirements, evidence, root = case
    complete_synthetic_representations(case)
    result = fidelity.audit(requirements, evidence, root)
    assert result['counts']['verified'] == result['representation_requirements']
    assert not result['clinical_commercial_ready']
    assert not result['runtime_reference_image_rights']['inspected']
    result = fidelity.audit(requirements, evidence, root, runtime_images={
        'surfaces': ['reporting:ra.example'],
        'images': [{'src': 'https://publisher.test/unreviewed.jpg', 'uses': []}]})
    assert not result['clinical_commercial_ready']
    assert result['runtime_reference_image_rights']['counts']['unverified'] == 1


def context_case(case, source, target):
    requirements, evidence, root = case
    asset = evidence['assets'][0]
    asset['kind'] = 'clinical_image'
    asset['source_context'] = source
    requirements['investigations'][0]['structures'][0]['context_requirements'] = target
    bind_synthetic_reviews(asset, requirements)
    return requirements, evidence, root


@pytest.mark.parametrize('source,target,reason', [
    ({'laterality': 'left'}, {'laterality': 'right'}, 'source_context_laterality_mismatch'),
    ({'setting': 'cadaveric'}, {'setting': ['in_vivo']}, 'source_context_setting_mismatch'),
    ({'population': {'life_stage': 'adult'}}, {'population': {'life_stage': 'immature'}}, 'source_context_life_stage_mismatch'),
    ({'depicted_state': 'normal_anatomy'}, {'depicted_state': ['infection']}, 'source_context_depicted_state_mismatch'),
    ({'depicted_state': 'normal_anatomy'}, {'purpose': 'pathology_example'}, 'source_context_purpose_mismatch'),
    ({'extent': 'local'}, {'extent': 'complete'}, 'source_context_extent_mismatch'),
    ({'selected_panels': ['e'], 'panel_types': {'c': 'MRI', 'e': 'Histology'}}, {}, 'source_context_selected_panel_not_clinical_image'),
    ({'selected_panels': ['b'], 'panel_types': {'b': 'Dissection'}}, {}, 'source_context_selected_panel_not_clinical_image'),
    ({'selected_panels': ['a'], 'panel_types': {'a': 'Ultrasound'}}, {}, 'source_context_selected_panel_modality_mismatch'),
])
def test_fresh_review_cannot_override_explicit_source_context_conflict(case, source, target, reason):
    requirements, evidence, root = context_case(case, source, target)
    result = fidelity.audit(requirements, evidence, root)
    rows = [row for row in result['requirements'] if row['kind'] == 'clinical_image']
    assert all(row['status'] == 'unverified' for row in rows)
    assert all(reason in row['candidates']['fixture'] for row in rows)
    assert result['asset_issues']['fixture'] == [], 'This tests compatibility, not stale review rejection'


def test_normal_cadaveric_reference_remains_eligible_for_explicit_reference_purpose(case):
    source = {'setting': 'cadaveric', 'laterality': 'left', 'population': {'life_stage': 'adult'},
              'depicted_state': 'normal_anatomy', 'extent': 'local',
              'selected_panels': ['c', 'd'], 'panel_types': {'c': 'MRI', 'd': 'MRI', 'b': 'Dissection', 'e': 'Histology'}}
    target = {'purpose': 'anatomical_reference', 'setting': ['cadaveric', 'in_vivo'],
              'laterality': ['left', 'right'], 'depicted_state': ['normal_anatomy'], 'extent': 'local'}
    requirements, evidence, root = context_case(case, source, target)
    result = fidelity.audit(requirements, evidence, root)
    assert result['counts']['verified'] == 2
    assert not result['clinical_commercial_ready'], 'Other independent representations remain absent'


def test_unstated_population_or_pathology_constraints_are_not_inferred_from_titles(case):
    requirements, evidence, root = context_case(case, {'setting': 'cadaveric', 'depicted_state': 'normal_anatomy',
                                                       'laterality': 'not_reported'}, {'purpose': 'anatomical_reference'})
    requirements['investigations'][0]['title'] = 'Diabetic infection and pediatric trauma teaching references'
    bind_synthetic_reviews(evidence['assets'][0], requirements)
    assert fidelity.audit(requirements, evidence, root)['counts']['verified'] == 2


@pytest.mark.parametrize('source,target,reason', [
    ({}, {'laterality': 'right'}, 'source_context_laterality_unresolved'),
    ({'laterality': 'not_reported'}, {'laterality': 'right'}, 'source_context_laterality_unresolved'),
    ({'population': {'life_stage': 'not_reported'}}, {'population': {'life_stage': 'immature'}}, 'source_context_life_stage_unresolved'),
    ({}, {'purpose': 'pathology_example'}, 'source_context_depicted_state_unresolved'),
    ({'laterality': []}, {'laterality': 'right'}, 'source_context_laterality_invalid'),
    ({'setting': True}, {}, 'source_context_setting_invalid'),
    ({'population': []}, {}, 'source_context_population_invalid'),
    ({}, {'setting': []}, 'requirement_context_setting_invalid'),
    ({}, {'population': {'age': 12}}, 'requirement_context_population_invalid'),
    ({}, {'imagined_field': True}, 'requirement_context_field_unknown'),
    ({}, {'purpose': {}}, 'requirement_context_purpose_invalid'),
    ({'selected_panels': ['c'], 'panel_types': {}}, {}, 'source_context_panel_type_unresolved'),
    ({'selected_panels': 'imaging', 'panel_types': {'c': 'MRI'}}, {}, 'source_context_panel_selection_invalid'),
    ({'selected_panels': ['c'], 'panel_types': {'c': 'made-up-modality'}}, {}, 'source_context_panel_type_invalid'),
])
def test_explicit_context_unknowns_or_malformed_claims_fail_closed(case, source, target, reason):
    requirements, evidence, root = context_case(case, source, target)
    result = fidelity.audit(requirements, evidence, root)
    rows = [row for row in result['requirements'] if row['kind'] == 'clinical_image']
    assert result['counts']['verified'] == 0
    assert all(reason in row['candidates']['fixture'] for row in rows)


def test_child_context_cannot_erase_inherited_side_constraint(case):
    requirements, evidence, root = context_case(case, {'laterality': 'left', 'extent': 'complete'}, {'laterality': 'right'})
    requirements['investigations'][0]['structures'][0]['required_parts'][0]['context_requirements'] = {'extent': 'local'}
    bind_synthetic_reviews(evidence['assets'][0], requirements)
    result = fidelity.audit(requirements, evidence, root)
    assert result['counts']['verified'] == 0
    assert all('source_context_laterality_mismatch' in row['candidates']['fixture']
               for row in result['requirements'] if row['kind'] == 'clinical_image')


def test_context_claims_remain_bound_to_exact_scope_fingerprint(case):
    requirements, evidence, root = context_case(case, {'setting': 'cadaveric'}, {'purpose': 'anatomical_reference'})
    evidence['assets'][0]['source_context']['setting'] = 'in_vivo'
    result = fidelity.audit(requirements, evidence, root)
    assert result['counts']['verified'] == 0
    assert 'anatomical_review_scope_missing_or_stale' in result['asset_issues']['fixture']
    bind_synthetic_reviews(evidence['assets'][0], requirements)
    requirements['investigations'][0]['structures'][0]['context_requirements']['setting'] = ['in_vivo']
    result = fidelity.audit(requirements, evidence, root)
    assert result['counts']['verified'] == 0
    assert 'anatomical_review_scope_missing_or_stale' in result['asset_issues']['fixture']


def test_complete_source_can_satisfy_explicit_local_extent_but_not_reverse(case):
    requirements, evidence, root = context_case(case, {'extent': 'complete'}, {'extent': 'local'})
    assert fidelity.audit(requirements, evidence, root)['counts']['verified'] == 2


def test_context_does_not_waive_site_expansion_or_review(case):
    requirements, evidence, root = context_case(case, {'setting': 'cadaveric'}, {'purpose': 'anatomical_reference'})
    requirements['investigations'][0]['structures'][0]['requires_site_instantiation'] = True
    bind_synthetic_reviews(evidence['assets'][0], requirements)
    result = fidelity.audit(requirements, evidence, root)
    assert any('site-specific anatomy' in gap for gap in result['scope_gaps'])
    assert not result['clinical_commercial_ready']
    evidence['assets'][0]['anatomical_review']['status'] = 'pending'
    assert fidelity.audit(requirements, evidence, root)['counts']['verified'] == 0


def test_source_context_cannot_ignore_the_existing_typed_laterality_field(case):
    requirements, evidence, root = case
    requirements['investigations'][0]['structures'][0]['laterality'] = 'right'
    asset = evidence['assets'][0]
    asset.update(kind='clinical_image', source_context={'laterality': 'left'})
    bind_synthetic_reviews(asset, requirements)
    result = fidelity.audit(requirements, evidence, root)
    rows = [row for row in result['requirements'] if row['kind'] == 'clinical_image']
    assert all(row['status'] == 'unverified' for row in rows)
    assert all('source_context_laterality_mismatch' in row['candidates']['fixture'] for row in rows)


def test_typed_panel_context_cannot_disagree_with_the_credited_selection(case):
    requirements, evidence, root = case
    asset = evidence['assets'][0]
    asset.update(kind='clinical_image', representation_selection={'panels': ['e']},
                 source_context={'selected_panels': ['c'], 'panel_types': {'c': 'MRI', 'e': 'Histology'}})
    bind_synthetic_reviews(asset, requirements)
    result = fidelity.audit(requirements, evidence, root)
    rows = [row for row in result['requirements'] if row['kind'] == 'clinical_image']
    assert all(row['status'] == 'unverified' for row in rows)
    assert all('source_context_panel_selection_mismatch' in row['candidates']['fixture'] for row in rows)


@pytest.mark.parametrize('kind', fidelity.KINDS)
@pytest.mark.parametrize('extent,expected', [
    ('partial', 'requirement_coverage_partial'),
    ('unknown', 'requirement_coverage_unknown'),
    ('unsupported', 'requirement_coverage_invalid'),
    (None, 'requirement_coverage_missing'),
])
def test_fresh_approval_cannot_turn_partial_or_unknown_coverage_complete(case, kind, extent, expected):
    requirements, evidence, root = case
    asset = evidence['assets'][0]
    asset['kind'] = kind
    identifier = asset['structure_ids'][0]
    if extent is None:
        del asset['requirement_coverage'][identifier]
    else:
        asset['requirement_coverage'][identifier]['extent'] = extent
    bind_synthetic_reviews(asset, requirements)  # Fixture review, never real approval.
    result = fidelity.audit(requirements, evidence, root)
    row = next(r for r in result['requirements'] if r['kind'] == kind and r['structure_id'] == identifier)
    assert row['status'] == 'unverified'
    assert expected in row['candidates'][asset['id']]
    assert not result['asset_issues'][asset['id']]
    assert result['counts']['verified'] == 1  # Other complete fixture binding stays independent.


def test_partial_candidates_do_not_silently_combine_into_complete_coverage(case):
    requirements, evidence, root = case
    first = evidence['assets'][0]
    for entry in first['requirement_coverage'].values():
        entry['extent'] = 'partial'
    bind_synthetic_reviews(first, requirements)
    second = copy.deepcopy(first)
    second['id'] = 'second-partial-fixture'
    bind_synthetic_reviews(second, requirements)
    evidence['assets'].append(second)
    result = fidelity.audit(requirements, evidence, root)
    assert result['counts']['verified'] == 0
    assert result['counts']['unverified'] == 2


def test_coverage_upgrade_requires_new_scope_review(case):
    requirements, evidence, root = case
    asset = evidence['assets'][0]
    identifier = asset['structure_ids'][0]
    asset['requirement_coverage'][identifier]['extent'] = 'partial'
    bind_synthetic_reviews(asset, requirements)
    asset['requirement_coverage'][identifier]['extent'] = 'complete'
    result = fidelity.audit(requirements, evidence, root)
    assert result['counts']['verified'] == 0
    assert 'anatomical_review_scope_missing_or_stale' in result['asset_issues'][asset['id']]


def test_complete_coverage_claim_needs_a_basis(case):
    requirements, evidence, root = case
    asset = evidence['assets'][0]
    identifier = asset['structure_ids'][0]
    asset['requirement_coverage'][identifier]['basis'] = '  '
    bind_synthetic_reviews(asset, requirements)
    result = fidelity.audit(requirements, evidence, root)
    row = next(r for r in result['requirements'] if r['kind'] == 'model' and r['structure_id'] == identifier)
    assert 'requirement_coverage_basis_missing' in row['candidates'][asset['id']]


@pytest.mark.parametrize('value', [[], {}, True, 1])
def test_malformed_coverage_extent_fails_closed_without_crashing(value):
    asset = {'requirement_coverage': {'example': {'extent': value, 'basis': 'Test'}}}
    assert fidelity.inspect_requirement_coverage(asset, {'id': 'example'}) == ['requirement_coverage_invalid']


def test_presentation_change_invalidates_otherwise_fresh_review(case):
    requirements,evidence,root=case
    asset=evidence['assets'][0]
    path=root/'viewer.js'
    path.write_text('original framing')
    asset['presentation_dependencies']={'viewer.js':hashlib.sha256(path.read_bytes()).hexdigest()}
    bind_synthetic_reviews(asset,requirements)
    assert fidelity.audit(requirements,evidence,root)['counts']['verified']==2
    path.write_text('changed framing with unchanged mesh')
    result=fidelity.audit(requirements,evidence,root)
    assert result['counts']['verified']==0
    assert 'presentation_dependency_fingerprint_mismatch' in result['asset_issues'][asset['id']]
    path.unlink()
    assert 'presentation_dependency_missing_or_outside_project' in fidelity.audit(requirements,evidence,root)['asset_issues'][asset['id']]
