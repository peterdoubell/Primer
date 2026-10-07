#!/usr/bin/env python3
"""Audit every required MSK structure separately in images, schematics and 3D.

Presence, resolution, a familiar filename, or an anatomical name is not evidence
of high fidelity. Completion requires reviewed, fingerprinted representations
and commercial-use evidence. Missing evidence remains a gap.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.msk_runtime_rights import audit_reference_image_rights, reference_images
KINDS = ("clinical_image", "schematic", "model")
REVIEW_FIELDS = ("anatomical_review", "visual_review")
REVIEW_SCOPE_VERSION = 1
IMAGE_MODALITIES = frozenset(('PET-CT', 'MRI', 'MR arthrography', 'CT', 'CT arthrography',
                             'Ultrasound', 'Radiography', 'Nuclear medicine'))
NORMAL_REFERENCE_STATES = frozenset(('normal_anatomy', 'normal_anatomical_reference',
                                     'normal_variant', 'normal_appearing_projection'))
# Explicitly recorded alternatives, never a substring guess from an unknown
# clinical phrase. Acquisition/site conditions still need their scope review.
QUALIFIED_MODALITIES = {
    'Ultrasound when accessible': ('Ultrasound',),
    'Ultrasound as actually acquired': ('Ultrasound',),
    'MRI or ultrasound for unossified components': ('MRI', 'Ultrasound'),
    'CT when indicated': ('CT',),
}
REQUIREMENT_REVIEW_FIELDS = frozenset((
    "clinical_validation_status", "review_status", "reviewed_at", "reviewed_by",
    "reviewer", "site_expansion_review",
))


def validate_reporting_snapshots(requirements, reporting):
    """A changed report cannot keep a stale all-structures completeness claim."""
    for investigation in requirements['investigations']:
        identifier = investigation['investigation_id']
        guide = reporting[identifier]
        snapshot = [{key: entry[key] for key in ('label', 'detail')}
                    for entry in investigation['reporting_checklist']]
        if snapshot != guide['checklist']:
            raise ValueError(identifier + ': reporting checklist changed; reconcile structure requirements')
        snapshot = [{key: entry[key] for key in ('heading', 'body')}
                    for entry in investigation['reporting_template_sections']]
        if snapshot != guide['template_sections']:
            raise ValueError(identifier + ': report fields changed; reconcile structure requirements')
        for structure in investigation['structures']:
            for reference in structure.get('report_refs', []):
                index = reference['checklist_index']
                if not isinstance(index, int) or not 0 <= index < len(guide['checklist']):
                    raise ValueError(identifier + ': structure points to a missing reporting field')
                if any(reference[key] != guide['checklist'][index][key] for key in ('label', 'detail')):
                    raise ValueError(identifier + ': structure/reporting binding is stale')


def requirements_for(investigation):
    """A parent label cannot stand in for separately reportable substructures."""
    result = []
    seen = set()
    for structure in investigation["structures"]:
        children = structure.get("required_parts") or []
        entries = children or [structure]
        for part in entries:
            if part["id"] in seen:
                raise ValueError("Duplicate structure requirement: " + part["id"])
            seen.add(part["id"])
            result.append({
                "id": part["id"], "name": part["name"],
                "parent_id": structure["id"],
                "laterality": structure.get("laterality", "unspecified"),
                "condition": structure.get("condition", ""),
                "report_refs": structure.get("report_refs", []),
                "modality_scope": part.get("modality_scope", structure.get("modality_scope", [])),
                # A child can add a constraint, not silently erase a parent's.
                "context_requirements": [entry["context_requirements"] for entry in ((structure,) if part is structure else (structure, part))
                                         if "context_requirements" in entry],
            })
    return result


def inspect_source_context(asset, requirement):
    """Check explicit context claims only; prose and module names imply none.

    Context fields are non-review claims, so the existing scope fingerprint
    covers them. This check cannot grant approval or establish anatomical extent.
    """
    constraints = requirement.get('context_requirements', [])
    if isinstance(constraints, dict):
        constraints = [constraints]
    if not isinstance(constraints, list) or any(not isinstance(item, dict) for item in constraints):
        return ['requirement_context_invalid']
    # The established requirement schema already has a typed laterality field.
    # Enforce explicit sides there too; "examined_side" remains unresolved
    # site context, never a guess that the reference is bilateral.
    if requirement.get('laterality') in ('left', 'right', 'bilateral'):
        constraints = [{'laterality': requirement['laterality']}, *constraints]
    context = asset.get('source_context', {})
    if not isinstance(context, dict):
        return ['source_context_invalid']
    issues = []
    unknown = {'unknown', 'not_reported', 'unspecified'}
    fields = {'setting', 'laterality', 'depicted_state', 'extent', 'projection', 'anatomical_variant'}
    vocabularies = {
        'setting': {'in_vivo', 'cadaveric', 'mixed', 'conceptual'},
        'projection': {'anteroposterior', 'lateral'},
        'anatomical_variant': {'none', 'peroneus_quartus', 'accessory_soleus', 'flexor_digitorum_accessorius_longus'},
        'laterality': {'left', 'right', 'bilateral'},
        'extent': {'local', 'complete'},
        'life_stage': {'adult', 'immature', 'mixed'},
    }

    def valid_value(value, field, allow_unknown=False):
        if not isinstance(value, str) or not value:
            return False
        if value in unknown:
            return allow_unknown
        if field in vocabularies:
            return value in vocabularies[field]
        # Depiction states are explicit codes (e.g. infection or normal_anatomy),
        # never inferred from a free-text caption or from the investigation title.
        return value.isascii() and value[0].isalpha() and all(c.islower() or c.isdigit() or c == '_' for c in value)

    def compare(field, expected, actual):
        allowed = expected if isinstance(expected, list) else [expected]
        if not allowed or any(not valid_value(item, field) for item in allowed):
            issues.append('requirement_context_' + field + '_invalid')
        elif actual is None or isinstance(actual, str) and actual in unknown:
            issues.append('source_context_' + field + '_unresolved')
        elif not valid_value(actual, field, allow_unknown=True):
            issues.append('source_context_' + field + '_invalid')
        elif actual not in allowed and not (field == 'extent' and actual == 'complete' and 'local' in allowed):
            issues.append('source_context_' + field + '_mismatch')

    population = context.get('population', {})
    if not isinstance(population, dict):
        issues.append('source_context_population_invalid')
        population = {}
    for field in fields:
        if field in context and not valid_value(context[field], field, allow_unknown=True):
            issues.append('source_context_' + field + '_invalid')
    if 'life_stage' in population and not valid_value(population['life_stage'], 'life_stage', allow_unknown=True):
        issues.append('source_context_life_stage_invalid')
    for target in constraints:
        if set(target) - fields - {'population', 'purpose'}:
            issues.append('requirement_context_field_unknown')
        for field in fields & set(target):
            compare(field, target[field], context.get(field))
        if 'population' in target:
            desired = target['population']
            if not isinstance(desired, dict) or not desired or set(desired) - {'life_stage'}:
                issues.append('requirement_context_population_invalid')
            else:
                compare('life_stage', desired['life_stage'], population.get('life_stage'))
        purpose = target.get('purpose')
        if purpose is not None and (not isinstance(purpose, str) or purpose not in {'anatomical_reference', 'pathology_example', 'measurement_validation'}):
            issues.append('requirement_context_purpose_invalid')
        if purpose == 'pathology_example':
            state = context.get('depicted_state')
            if state is None or isinstance(state, str) and state in unknown:
                issues.append('source_context_depicted_state_unresolved')
            elif isinstance(state, str) and state in NORMAL_REFERENCE_STATES:
                issues.append('source_context_purpose_mismatch')

    # A credited composite selection must not borrow the acquisition type of
    # another panel. Sources without typed panel facts retain existing behavior.
    if any(key in context for key in ('selected_panels', 'panel_types', 'panel_states')):
        selected, types = context.get('selected_panels'), context.get('panel_types')
        if (not isinstance(selected, list) or not selected
                or any(not isinstance(panel, str) or not panel for panel in selected)
                or not isinstance(types, dict)):
            issues.append('source_context_panel_selection_invalid')
        else:
            selection = asset.get('representation_selection', {})
            if not isinstance(selection, dict):
                issues.append('source_context_panel_selection_invalid')
            else:
                declared = selection.get('panels')
                if isinstance(declared, list):
                    if any(not isinstance(panel, str) for panel in declared):
                        issues.append('source_context_panel_selection_invalid')
                    elif set(declared) != set(selected):
                        issues.append('source_context_panel_selection_mismatch')
            for panel in selected:
                actual = types.get(panel)
                if not isinstance(actual, str) or actual in unknown or actual is None:
                    issues.append('source_context_panel_type_unresolved')
                elif actual not in IMAGE_MODALITIES | {'Dissection', 'Histology', 'Schematic', 'Haemodynamic tracing', 'Anatomical specimen photograph', 'Clinical photograph'}:
                    issues.append('source_context_panel_type_invalid')
                elif asset['kind'] == 'clinical_image' and actual not in IMAGE_MODALITIES:
                    issues.append('source_context_selected_panel_not_clinical_image')
                elif asset['kind'] == 'clinical_image' and actual != asset.get('modality'):
                    issues.append('source_context_selected_panel_modality_mismatch')
                elif asset['kind'] == 'schematic' and actual != 'Schematic':
                    issues.append('source_context_selected_panel_not_schematic')
            # A fresh review fingerprint cannot erase a known contradiction
            # between a selected panel and the claimed depiction state. No
            # states are inferred from captions or assigned to legacy records.
            if 'panel_states' in context:
                states = context['panel_states']
                if (not isinstance(states, dict)
                        or any(not isinstance(key, str) or not key.strip()
                               or not valid_value(state, 'depicted_state', allow_unknown=True)
                               for key, state in states.items())):
                    issues.append('source_context_panel_states_invalid')
                else:
                    claimed = context.get('depicted_state')
                    uniform_claim = (isinstance(claimed, str) and claimed not in unknown | {'mixed'})
                    for panel in selected:
                        actual_state = states.get(panel)
                        if actual_state is None or (uniform_claim and actual_state in unknown):
                            issues.append('source_context_selected_panel_state_unresolved')
                        elif uniform_claim and actual_state != claimed:
                            if not (claimed in NORMAL_REFERENCE_STATES
                                    and actual_state in NORMAL_REFERENCE_STATES):
                                issues.append('source_context_selected_panel_state_mismatch')
    return list(dict.fromkeys(issues))


def inspect_binding(asset, requirement):
    """A source in another modality cannot prove a direct-image requirement."""
    context_issues = inspect_source_context(asset, requirement)
    if asset['kind'] != 'clinical_image':
        return context_issues
    actual = asset.get('modality')
    if not isinstance(actual, str) or actual not in IMAGE_MODALITIES:
        return context_issues + ['clinical_image_modality_missing_or_unknown']
    scope = requirement.get('modality_scope')
    if not isinstance(scope, list) or not scope:
        return context_issues + ['requirement_modality_scope_missing_or_unknown']
    allowed = set()
    for label in scope:
        if not isinstance(label, str):
            return context_issues + ['requirement_modality_scope_missing_or_unknown']
        if label in IMAGE_MODALITIES:
            allowed.add(label)
        elif label in QUALIFIED_MODALITIES:
            allowed.update(QUALIFIED_MODALITIES[label])
        else:
            return context_issues + ['requirement_modality_scope_missing_or_unknown']
    return context_issues + ([] if actual in allowed else ['clinical_image_modality_not_in_requirement_scope'])


def inspect_requirement_coverage(asset, requirement):
    """A reviewed local depiction is not proof of the entire named requirement.

    Coverage is per requirement, independent of source-context extent. A local
    source can fully depict a local requirement, but that must be explicit.
    Multiple partial candidates are not automatically a complete collection.
    These claims are included in the existing review-scope fingerprint.
    """
    coverage = asset.get('requirement_coverage')
    if not isinstance(coverage, dict):
        return ['requirement_coverage_missing']
    entry = coverage.get(requirement['id'])
    if not isinstance(entry, dict):
        return ['requirement_coverage_missing']
    if not isinstance(entry.get('extent'), str) or entry['extent'] not in {'complete', 'partial', 'unknown'}:
        return ['requirement_coverage_invalid']
    if not isinstance(entry.get('basis'), str) or not entry['basis'].strip():
        return ['requirement_coverage_basis_missing']
    return [] if entry['extent'] == 'complete' else ['requirement_coverage_' + entry['extent']]


def requirement_definition(value):
    """Keep requirement meaning separate from the act of reviewing it."""
    if isinstance(value, dict):
        return {key: requirement_definition(item) for key, item in value.items()
                if key not in REQUIREMENT_REVIEW_FIELDS}
    if isinstance(value, list):
        return [requirement_definition(item) for item in value]
    return value


def review_scope_payload(asset, requirements):
    """Bind review to claims and the current meaning of their requirements.

    All non-review asset fields are claims, including future panel/modality or
    provenance fields. Do not allowlist them: omitting a new claim would let an
    old approval silently authorize a different representation. Whole matched
    parent definitions retain component boundaries and inherited conditions.
    Unrelated structures/investigations are excluded from the review scope.
    """
    investigation_ids = set(asset.get("investigation_ids", []))
    structure_ids = set(asset.get("structure_ids", []))
    matched = []
    for investigation in requirements.get("investigations", []):
        if investigation["investigation_id"] not in investigation_ids:
            continue
        structures = []
        for structure in investigation["structures"]:
            identifiers = {structure["id"]}
            identifiers.update(part["id"] for part in (structure.get("required_parts") or []))
            if identifiers & structure_ids:
                structures.append(structure)
        matched.append({
            "context": {key: value for key, value in investigation.items() if key != "structures"},
            "structures": sorted(structures, key=lambda item: item["id"]),
        })
    return {
        "review_scope_version": REVIEW_SCOPE_VERSION,
        "asset_claims": {key: value for key, value in asset.items() if key not in REVIEW_FIELDS},
        "requirement_schema_version": requirements.get("schema_version"),
        "requirement_purpose": requirements.get("purpose"),
        "requirement_conventions": requirement_definition(requirements.get("conventions", {})),
        "matched_requirements": requirement_definition(
            sorted(matched, key=lambda item: item["context"]["investigation_id"])),
    }


def review_scope_fingerprint(asset, requirements):
    """Compute a reproducible review target, never an approval of that target."""
    payload = json.dumps(review_scope_payload(asset, requirements), sort_keys=True,
                         separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def boundary_scope_fingerprint(investigation, issue):
    """Bind a boundary decision to report and anatomy meaning, not review status."""
    definition = requirement_definition({
        'investigation': {key: value for key, value in investigation.items()
                          if key != 'source_scope_issues'},
        'boundary': {key: value for key, value in issue.items() if key != 'documentation'},
    })
    payload = json.dumps(definition, sort_keys=True, separators=(',', ':'),
                         ensure_ascii=False, allow_nan=False)
    return hashlib.sha256(payload.encode('utf-8')).hexdigest()


def inspect_scope_issue(issue, investigation, root):
    """Only a specifically documented boundary stops being a defect blocker.

    This is a classification of the reporting issue, not a waiver of anatomy,
    representation, site-expansion or review requirements. Unknown/legacy
    records remain blocking. A resolved defect belongs in its resolution
    history; setting an arbitrary status here cannot silently waive it.
    """
    record = issue if isinstance(issue, dict) else {}
    result = {"code": record.get("code"), "kind": record.get("kind"),
              "status": record.get("status"), "detail": record.get("detail"),
              "blocking": True, "reason": "classification_missing_or_unknown"}
    if record.get("kind") == "reporting_defect":
        result["reason"] = "reporting_defect_unresolved"
        return result
    if not (record.get("kind") == "boundary_constraint"
            and record.get("status") == "documented"):
        return result
    if any(not isinstance(record.get(key), str) or not record[key].strip()
           for key in ("code", "detail", "classification_note")):
        result["reason"] = "boundary_explanation_missing"
        return result
    indices = record.get("affected_checklist_indices")
    checklist = investigation.get("reporting_checklist", [])
    if (not isinstance(checklist, list) or not isinstance(indices, list) or not indices
            or any(type(index) is not int or not 0 <= index < len(checklist)
                   for index in indices)):
        result["reason"] = "boundary_reporting_refs_invalid"
        return result
    documentation = record.get("documentation")
    if not (isinstance(documentation, dict)
            and isinstance(documentation.get("path"), str)
            and documentation["path"].strip()):
        result["reason"] = "boundary_documentation_missing"
        return result
    path = (root / documentation["path"]).resolve()
    if not path.is_relative_to(root.resolve()):
        result["reason"] = "boundary_documentation_outside_project"
        return result
    try:
        content = path.read_bytes()
    except OSError:
        result["reason"] = "boundary_documentation_missing"
        return result
    if not content or hashlib.sha256(content).hexdigest() != documentation.get("sha256"):
        result["reason"] = "boundary_documentation_missing_or_stale"
        return result
    if documentation.get('reviewed_scope_sha256') != boundary_scope_fingerprint(investigation, record):
        result['reason'] = 'boundary_scope_missing_or_stale'
        return result
    result.update(blocking=False, reason="documented_boundary_requirements_retained",
                  classification_note=record["classification_note"],
                  documentation=dict(documentation))
    return result


def inspect_asset(asset, root, review_scope_sha256):
    issues = []
    if 'presentation_dependencies' in asset:
        dependencies = asset['presentation_dependencies']
        if not isinstance(dependencies, dict) or not dependencies:
            issues.append('presentation_dependencies_invalid')
        else:
            for name, expected in dependencies.items():
                if not isinstance(name, str) or not name or not isinstance(expected, str):
                    issues.append('presentation_dependencies_invalid')
                    continue
                path = (root / name).resolve()
                if not path.is_relative_to(root.resolve()) or not path.is_file():
                    issues.append('presentation_dependency_missing_or_outside_project')
                elif hashlib.sha256(path.read_bytes()).hexdigest() != expected:
                    issues.append('presentation_dependency_fingerprint_mismatch')
    if asset.get("kind") not in KINDS:
        raise ValueError("Unknown representation kind: " + str(asset.get("kind")))
    if not asset.get("structure_ids"):
        issues.append("no_verified_structure_binding")
    source = asset.get("source", {})
    license_info = source.get("license", {})
    if not (source.get("url") and license_info.get("url")
            and license_info.get("commercial_use") is True
            and license_info.get("redistribution") is True
            and license_info.get("review_status") == "verified"
            and license_info.get("attribution")):
        issues.append("commercial_rights_unverified")
    # Assets must be locally available and immutable for a clinical review to
    # survive. A live publisher URL may change independently of its caption.
    local_path = asset.get("local_path")
    digest = None
    if not isinstance(local_path, str) or not local_path:
        issues.append("no_local_reviewable_asset")
    else:
        path = (root / local_path).resolve()
        if not path.is_relative_to(root.resolve()):
            raise ValueError("Asset path leaves project: " + local_path)
        if not path.is_file():
            issues.append("asset_missing")
        else:
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            if digest != asset.get("sha256"):
                issues.append("asset_fingerprint_mismatch")
    for field in REVIEW_FIELDS:
        review = asset.get(field, {})
        if review.get("review_scope_sha256") != review_scope_sha256:
            issues.append(field + "_scope_missing_or_stale")
        if not (review.get("status") == "approved" and review.get("reviewer")
                and review.get("evidence_path") and review.get("reviewed_at")
                and digest and review.get("sha256") == digest):
            issues.append(field + "_missing_or_stale")
        else:
            evidence = (root / review["evidence_path"]).resolve()
            if not evidence.is_relative_to(root.resolve()) or not evidence.is_file():
                issues.append(field + "_evidence_missing")
    if asset.get("fidelity") != "high":
        issues.append("high_fidelity_unproven")
    return issues


def audit(requirements, evidence, root=ROOT, expected_catalog_ids=None, runtime_images=None):
    investigations = requirements.get("investigations", [])
    if not investigations:
        raise ValueError("An empty requirements inventory cannot prove completion")
    expected = set(requirements["scope"]["catalog_investigation_ids"])
    observed = [entry["investigation_id"] for entry in investigations]
    if len(observed) != len(set(observed)) or set(observed) != expected:
        raise ValueError("Investigation scope is missing, duplicated or changed")
    if expected_catalog_ids is not None and expected != set(expected_catalog_ids):
        raise ValueError("Requirements do not cover the authoritative MSK catalogue")
    assets = evidence.get("assets", [])
    if len({a["id"] for a in assets}) != len(assets):
        raise ValueError("Repeated asset identifier")
    review_scopes = {asset["id"]: review_scope_fingerprint(asset, requirements) for asset in assets}
    asset_issues = {asset["id"]: inspect_asset(asset, root, review_scopes[asset["id"]]) for asset in assets}
    rows = []
    for investigation in investigations:
        identifier = investigation["investigation_id"]
        leaves = requirements_for(investigation)
        if not leaves:
            raise ValueError("No structure requirements for " + identifier)
        for structure in leaves:
            for kind in KINDS:
                candidates = [asset for asset in assets
                              if asset["kind"] == kind
                              and identifier in asset.get("investigation_ids", [])
                              and structure["id"] in asset.get("structure_ids", [])]
                candidate_issues = {asset['id']: asset_issues[asset['id']] + inspect_binding(asset, structure)
                                    + inspect_requirement_coverage(asset, structure)
                                    for asset in candidates}
                valid = [asset["id"] for asset in candidates if not candidate_issues[asset["id"]]]
                rows.append({"investigation_id": identifier,
                             "structure_id": structure["id"],
                             "structure_name": structure["name"], "kind": kind,
                             "status": "verified" if valid else "unverified" if candidates else "missing",
                             "verified_assets": valid,
                             "candidates": candidate_issues})
    scope_gaps = []
    scope_issue_assessments = []
    for investigation in investigations:
        if investigation.get("expansion_rules"):
            # Region-dependent conditions require an explicit exhaustive site
            # inventory; a generic joint is never a complete substitute.
            if investigation.get("site_expansion_review", {}).get("status") != "approved":
                scope_gaps.append(investigation["investigation_id"] + ": site expansion unverified")
        issues = investigation.get("source_scope_issues", [])
        if not isinstance(issues, list):
            scope_gaps.append(investigation["investigation_id"] + ": source scope issues must be a list")
            scope_issue_assessments.append({"investigation_id": investigation["investigation_id"],
                "code": None, "kind": None, "status": None, "blocking": True,
                "reason": "source_scope_issues_invalid"})
        else:
            for index, issue in enumerate(issues):
                assessment = {"investigation_id": investigation["investigation_id"], "index": index,
                              **inspect_scope_issue(issue, investigation, root)}
                scope_issue_assessments.append(assessment)
                if assessment["blocking"]:
                    scope_gaps.append(investigation["investigation_id"] + ": source scope issue "
                                      + str(assessment["code"] or index) + ": "
                                      + assessment["reason"].replace("_", " "))
        if any(structure.get("requires_site_instantiation") for structure in investigation["structures"]):
            scope_gaps.append(investigation["investigation_id"] + ": generic structure requires site-specific anatomy")
    for additional in requirements.get("additional_scope", []):
        if additional.get("unresolved_requirements") or not additional.get("covered_by_investigation_ids"):
            scope_gaps.append(additional["module_id"] + ": additional MSK scope unresolved")
    if requirements.get("clinical_validation_status") != "approved":
        scope_gaps.append("Reporting structure inventory requires clinical review")
    totals = {status: sum(row["status"] == status for row in rows)
              for status in ("verified", "unverified", "missing")}
    runtime_rights = audit_reference_image_rights(runtime_images, evidence, root)
    return {"clinical_commercial_ready": not scope_gaps and totals["verified"] == len(rows)
            and runtime_rights['rights_ready'],
            "investigations": len(investigations), "representation_requirements": len(rows),
            "counts": totals, "scope_gaps": scope_gaps, "asset_issues": asset_issues,
            "runtime_reference_image_rights": runtime_rights,
            "scope_issue_assessments": scope_issue_assessments,
            "review_scope_sha256": review_scopes,
            "requirements": rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--require-complete", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    data = ROOT / "data/radiology"
    requirements = json.loads((data / "msk-structure-requirements.json").read_text())
    evidence = json.loads((data / "msk-asset-evidence.json").read_text())
    catalog = json.loads((data / "reference-investigations.json").read_text())
    expected = {item["id"] for item in catalog["investigations"] if item["section"] == "Musculoskeletal"}
    sys.path.insert(0, str(ROOT))
    from primer.curriculum import Curriculum
    from primer.radiology_catalog import detail
    curriculum = Curriculum()
    reporting = {item['id']: detail(curriculum, item)['radiology_reference']['reporting']
                 for item in catalog['investigations'] if item['id'] in expected}
    validate_reporting_snapshots(requirements, reporting)
    runtime_images = reference_images(curriculum, catalog, requirements, detail)
    report = audit(requirements, evidence, expected_catalog_ids=expected, runtime_images=runtime_images)
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print("{} investigations; {} structure/representation requirements".format(
            report["investigations"], report["representation_requirements"]))
        print("Verified: {verified}; unverified: {unverified}; missing: {missing}".format(**report["counts"]))
        print("Clinical/commercial readiness: " + ("verified" if report["clinical_commercial_ready"] else "NOT ESTABLISHED"))
        rights = report['runtime_reference_image_rights']
        print('Runtime reference images: {cleared} rights-cleared; {unverified} unverified; {images} total'.format(**rights['counts']))
        for issue in report["scope_gaps"]:
            print("Scope: " + issue)
        for issue in report["scope_issue_assessments"]:
            if not issue["blocking"]:
                print("Documented boundary (requirements retained): {}: {}".format(
                    issue["investigation_id"], issue["code"]))
    raise SystemExit(1 if args.require_complete and not report["clinical_commercial_ready"] else 0)


if __name__ == "__main__":
    main()
