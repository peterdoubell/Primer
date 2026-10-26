"""Reconcile current reporting identities and add its missing named brain targets.

This is a requirements audit, never an asset-coverage or clinical approval test.
The non-brain reconciliation retains unmatched rows and distinguishes shared
anatomy from equivalence of acquisition, age, pathology and reporting extent.
"""
from __future__ import annotations

import argparse
import copy
import gzip
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REQUIREMENTS = "data/radiology/non-msk-structure-requirements.json"
MSK_REQUIREMENTS = "data/radiology/msk-structure-requirements.json"
REPORT_FILE = "data/radiology/anatomic-neuro.json"
OUT = "docs/reporting-requirement-reconciliation-20261026"
BRAIN = "ra.brain-anatomy"
REPRESENTATIONS = ["image", "schematic", "model"]
LEGACY_BRAIN_SHA256 = "6f7b8df6cc14e95374a74d4a950150f23a38cb1c2d2ec3d1bfea626f041d3556"
SURFACE = (
    "superior-frontal-gyrus", "middle-frontal-gyrus", "inferior-frontal-gyrus",
    "superior-parietal-lobule", "inferior-parietal-lobule",
    "superior-temporal-gyrus", "middle-temporal-gyrus", "inferior-temporal-gyrus",
    "cingulate-gyrus", "precuneus", "cuneus", "lingual-gyrus",
)

# These are relationships between reporting scopes, not automatic aliases or
# evidence of represented anatomy. Each retained target is independently named.
# Other investigations remain explicitly unexpanded, including paediatric
# studies: a shared region/module with an adult study does not make it equivalent.
RELATED_SCOPES = {
    "ra.ultrasound-acute-abdomen": ("modality_partition", ["ra.acute-abdomen"], "Ultrasound acquisition partitions the acute-abdomen scope; organ/space requirements remain relevant, but each current row needs acquisition-specific reconciliation."),
    "ra.transvaginal-nongynaecology": ("modality_and_region_partition", ["ra.acute-abdomen"], "The non-gynaecological transvaginal examination shares covered pelvic/bowel/urinary targets; probe approach, accessible extent and current row definitions require separate reconciliation."),
    "ra.ultrasound-gi-tract": ("aggregate_with_additional_targets", ["ra.ultrasound-ibd", "ra.appendicitis", "ra.acute-abdomen"], "Existing bowel and appendiceal requirements overlap, but their disease-specific scopes do not enumerate every general GI ultrasound target."),
    "ra.ovarian-cysts": ("related_anatomy_new_disease_scope", ["ra.mri-endometriosis"], "Existing ovarian/adnexal anatomy is context only; ovarian cyst morphology and O-RADS pathways require a dedicated inventory."),
    "ra.ultrasound-acute-gynaecology": ("related_anatomy_new_acquisition_scope", ["ra.mri-endometriosis", "ra.acute-abdomen"], "Shared pelvic organs do not establish acute gynaecological ultrasound, pregnancy, torsion, perfusion or time-critical pathway representation."),
    "ra.mullerian-anomalies": ("related_anatomy_new_developmental_scope", ["ra.mri-endometriosis", "ra.mri-cervical-cancer", "ra.mri-endometrial-cancer"], "Acquired uterine disease inventories do not enumerate developmental cavity, contour, cervical/vaginal and associated anomaly relationships."),
    "ra.dynamic-rectal-examination": ("related_anatomy_new_dynamic_scope", ["ra.mri-rectal-cancer", "ra.mri-perianal-fistula"], "Static pelvic oncology/fistula anatomy is context; dynamic pelvic-floor compartments and functional states need dedicated requirements."),
    "ra.thoracic-ultrasound": ("related_anatomy_new_acquisition_scope", ["ra.chest-radiography", "ra.hrct-lung"], "Pleural, pulmonary and diaphragmatic anatomy overlaps, while ultrasound windows, dynamic signs and intervention-related states require separate acquisition evidence."),
    "ra.ct-covid": ("related_anatomy_new_disease_scope", ["ra.hrct-lung", "ra.tuberculosis"], "Lung and airway extent overlaps; disease-pattern evidence from fibrosis or tuberculosis is not COVID-specific evidence."),
    "ra.thymus": ("organ_partition_with_additional_targets", ["ra.ct-mediastinum"], "The existing mediastinum.thymus parent supplies named thymic/prevascular requirements; age-dependent morphology and each current thymus finding remain to be reconciled."),
    "cardiology.percutaneous-angiography": ("related_anatomy_new_acquisition_scope", ["ra.ct-coronary"], "Coronary segments overlap with coronary CT; invasive access, projection, flow, procedural and acquired angiographic evidence are not supplied by a CT inventory."),
    "cardiology.echocardiography": ("aggregate_with_additional_targets", ["ra.mri-cardiomyopathy", "ra.ct-tavi", "ra.cardiac-masses", "ra.vascular-anomalies"], "Chambers, myocardium, valves and vessels recur; echocardiographic views, Doppler, motion, measurement and haemodynamic scope need an explicit echo inventory."),
    "template:breast-calcifications-report": ("finding_partition_with_additional_targets", ["ra.mammography"], "Mammographic calcification location and morphology recur; this dedicated template's distribution, extent and comparison rows require explicit bindings."),
    "template:head-trauma-report": ("aggregate_with_additional_targets", ["ra.ct-traumatic-haemorrhage", "ra.brain-anatomy"], "The acquired head-trauma checklist overlaps intracranial trauma and localisation inventories; it remains a distinct template and must retain its own skull/soft-tissue/acquisition scope."),
    "ra.mri-lumbar-disc": ("related_anatomy_new_disease_scope", ["ra.mri-myelopathy", "ra.thoracolumbar-fractures"], "Named spinal levels and compressive structures overlap, but disc morphology and each exiting/traversing root and foramen need a dedicated lumbar-disc inventory."),
    "ra.venous-sinus-thrombosis": ("related_anatomy_new_disease_scope", ["ra.brain-anatomy"], "Named venous drainage targets provide localisation context; venography acquisition, thrombus extent and venous injury are additional requirements."),
    "ra.intracranial-hypotension": ("related_anatomy_new_disease_scope", ["ra.brain-anatomy", "ra.mri-myelopathy"], "CSF and spinal anatomy offer context; leak localisation, acquired displacement and disease signs require separate scoped evidence."),
    "ra.mri-cns-enhancement": ("related_anatomy_new_disease_scope", ["ra.brain-anatomy"], "Normal anatomical localisation does not supply enhancement pattern, compartment or acquired disease extent."),
    "ra.mri-dementia": ("related_anatomy_new_disease_scope", ["ra.brain-anatomy"], "Brain regions offer localisation context; atrophy patterns, scales, white-matter and vascular observations require a dedicated inventory."),
    "ra.mri-epilepsy": ("related_anatomy_new_disease_scope", ["ra.brain-anatomy"], "Hippocampal, amygdala and cortical requirements overlap; acquired sequence, cortical-development and epilepsy-lesion scope remain additional."),
    "ra.intracranial-haemorrhage": ("aggregate_with_additional_targets", ["ra.ct-traumatic-haemorrhage", "ra.brain-anatomy"], "Haemorrhage compartments and localisation overlap, but non-traumatic aetiology, microhaemorrhage and underlying-lesion requirements are not a trauma alias."),
    "ra.mri-ms": ("related_anatomy_new_disease_scope", ["ra.brain-anatomy", "ra.mri-myelopathy"], "Brain/cord localisation is shared; lesion distribution, dissemination, activity and acquisition-specific evidence require independent expansion."),
    "ra.mri-brain-tumours": ("related_anatomy_new_disease_scope", ["ra.brain-anatomy"], "Brain localisation is context only; tumour, spread and treatment-response extent are not represented by a normal atlas."),
    "msk.mri-wrist": ("aggregate_with_additional_targets", ["ra.wrist-instability", "ra.wrist-fractures"], "Carpal bones, joints and ligament complexes overlap; the current MRI template explicitly subdivides ligaments/TFCC and names tendon/retinacular/nerve targets requiring expanded MRI-specific requirements."),
    "msk.mri-hand": ("related_region_new_dedicated_scope", ["ra.arthritis", "ra.wrist-instability"], "The shared wrist-hand module is not an alias: current named digits, pulley levels, extensor slips and neurovascular targets need their own MRI hand inventory."),
    "ra.thoracolumbar-injury": ("declared_duplicate_pathway_with_unresolved_instantiation", ["ra.thoracolumbar-fractures"], "The existing additional_scope explicitly identifies the duplicate trauma pathway. Current T1–L5 rows instantiate the older each_imaged_vertebra template, while acquisition, neural observations and every part still need individual binding."),
    "ra.cervical-spine-injury": ("related_region_new_trauma_scope", ["ra.mri-myelopathy", "ra.thoracolumbar-fractures"], "The shared spine guide does not make cervical trauma a thoracolumbar alias: C1/C2, craniocervical alignment and named craniovertebral ligaments require independent requirements."),
    "msk.mri-hip": ("aggregate_with_additional_targets", ["ra.hip-fai", "ra.hip-arthroplasty"], "Hip bones, cartilage, labrum and periarticular structures overlap; the comprehensive MRI rows include additional sector-specific labrum, ligaments, muscles, bursae and nerves. Postoperative scope is conditional, not interchangeable."),
    "msk.mri-foot": ("aggregate_with_additional_targets", ["ra.foot-ankle-cases", "ra.mri-ankle", "ra.mri-diabetic-foot"], "Existing foot/ankle requirements overlap; each toe joint, collateral ligament, plantar plate, webspace and tendon needs explicit MRI-foot instantiation."),
}


def read(path, root=ROOT):
    return json.loads((root / path).read_text())


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def file_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def brain_additions(report):
    sections = {s["id"]: s for s in report["sections"]}
    additions = []
    for side in ("right", "left"):
        for target in (*SURFACE, "amygdala", "mca-superior-division", "mca-inferior-division"):
            is_territory = target.startswith("mca-")
            section_id = target if is_territory else f"{side}-{target}"
            section = sections[section_id]
            parent = f"brain.{side}_" + ("territories" if is_territory else "source_regions" if target == "amygdala" else "surface")
            suffix = target.replace("-", "_") + ("_territory" if is_territory else "")
            extent = (
                "The side-specific superior/inferior MCA division supply territory, with source-defined variation and collateral/border-zone limitations. Arterial vessel geometry, a whole MCA cortical mask, or a cortical gyrus alone does not establish this territory."
                if is_territory else
                "The named side-specific whole amygdala extent. A source's present nuclear union may omit nuclei or adjacent amygdaloid subdivisions and must disclose that limitation."
                if target == "amygdala" else
                "The named side-specific gyrus/lobule extent, with its constituent cortical subdivisions, limiting landmarks and cortical-versus-subcortical distinction. A broad lobe or differently defined source parcel does not by itself establish full extent."
            )
            part = {
                "id": f"{parent}.{suffix}",
                "name": section["label"].removeprefix(side.title() + " "),
                "required_representations": REPRESENTATIONS,
                "required_extent": extent,
                "reporting_provenance": {
                    "source_file": REPORT_FILE, "investigation_id": BRAIN,
                    "section_id": section_id, "section_sha256": digest(section),
                    "side_instantiation": side, "basis": "explicit_current_anatomical_reporting_row",
                },
                "clinical_validation_status": "draft_requires_neuroradiologist_review",
                "representation_completion_claim": False,
            }
            additions.append((parent, part))
    return additions


def expand_brain(inventory, report):
    result = copy.deepcopy(inventory)
    brain = next(i for i in result["investigations"] if i["investigation_id"] == BRAIN)
    parents = {s["id"]: s for s in brain["structures"]}
    additions = brain_additions(report)
    existing = {}
    for structure in brain["structures"]:
        for part in structure["required_parts"]:
            if part["id"] in existing:
                raise ValueError("Repeated brain requirement: " + part["id"])
            existing[part["id"]] = (structure["id"], part)
    for parent, part in additions:
        if part["id"] in existing:
            if existing[part["id"]] != (parent, part):
                raise ValueError("Conflicting prior expansion: " + part["id"])
        else:
            parents[parent]["required_parts"].append(part)
    return result


def brain_crosswalk(root, inventory, report):
    additions = brain_additions(report)
    fine = json.loads(gzip.decompress((root / "data/radiology/holiatlas-labels.json.gz").read_bytes()))
    fine = {x["code"]: x for x in fine["sourceClasses"] if x["voxels"] > 0}
    hierarchy = json.loads(gzip.decompress((root / "data/radiology/holiatlas-hierarchy.json.gz").read_bytes()))["levels"]
    protocol = read("docs/holiatlas-source-review-20261023/holiatlas-protocol-rows.json", root)
    cells = [{c["cell"][0]: c["value"] for c in row} for row in protocol["xl/worksheets/sheet1.xml"][1:]]
    names = {int(c["B"]): c["A"].strip() for c in cells if c.get("B", "").isdigit() and "A" in c}
    direct = {"middle_frontal_gyrus": 146, "superior_parietal_lobule": 180,
              "superior_temporal_gyrus": 192, "middle_temporal_gyrus": 186,
              "inferior_temporal_gyrus": 184, "precuneus": 174, "cuneus": 200, "lingual_gyrus": 204}
    compositions = {"superior_frontal_gyrus": 5, "inferior_frontal_gyrus": 6, "cingulate_gyrus": 7}
    rows = []
    for _, part in additions:
        suffix = part["id"].split(".")[-1]
        left = part["reporting_provenance"]["side_instantiation"] == "left"
        entries = []
        limits = ["No independent clinical boundary review or patient-specific registration is established by this correspondence."]
        if suffix in direct:
            code = direct[suffix] + int(left)
            entries = [{"scale": "fine", "code": code, "source_name": names[code], "present": code in fine}]
            relation = "present_source_parcel_with_named_correspondence_requires_extent_review"
            if suffix == "superior_temporal_gyrus":
                limits.append("Planum temporale, planum polare and transverse temporal cortex are separately labelled by this source; the single named parcel cannot certify the whole superior temporal gyrus.")
        elif suffix in compositions or suffix == "amygdala":
            scale = "structure" if suffix == "amygdala" else "composition"
            code = 22 + int(left) if suffix == "amygdala" else compositions[suffix] + (8 if left else 0)
            entry = next(x for x in hierarchy[scale]["sourceClasses"] if x["code"] == code)
            entries = [{"scale": scale, "code": code, "source_name": entry["name"],
                        "fine_source_codes": entry["fineSourceCodes"],
                        "present_fine_source_codes": [c for c in entry["fineSourceCodes"] if c in fine]}]
            relation = "existing_explicit_source_union_requires_clinical_extent_review"
            limits.extend(entry["exclusionsAndLimits"])
        elif suffix == "inferior_parietal_lobule":
            # Protocol members are named components, not a validated whole IPL union.
            codes = [170 + int(left), 178 + int(left)]
            assert all(any(w in names[c].lower() for w in ("angular", "supramarginal")) for c in codes)
            entries = [{"scale": "fine", "code": c, "source_name": names[c], "present": c in fine} for c in codes]
            relation = "separate_source_component_candidates_no_existing_whole_lobule_composition"
            limits.append("Angular and supramarginal labels require a source-protocol and clinical boundary review before a whole inferior parietal lobule claim; a new merged mask is not asserted here.")
        else:
            relation = "no_source_territory_mask"
            limits.append("HoliAtlas does not supply an MCA division perfusion/arterial territory segmentation; use a separately sourced territory representation with explicit variation.")
        rows.append({"requirement_id": part["id"], "report_section_id": part["reporting_provenance"]["section_id"],
                     "source_context": entries, "relationship": relation, "limitations": limits,
                     "required_representations": REPRESENTATIONS, "clinical_representation_complete": False})
    old = read("docs/holiatlas-hierarchy-review-20261025/pr167-reporting-inventory-audit.json", root)
    current_rows = {s["id"]: s for s in report["sections"]}
    prior_rows = {s["report_section_id"]: s for s in old["brain_rows"]}
    if set(current_rows) != set(prior_rows):
        raise ValueError("Brain reporting row set changed; reconcile explicitly before generating proof")
    reconciled = []
    for sid, section in current_rows.items():
        added = [r["requirement_id"] for r in rows if r["report_section_id"] == sid]
        ids = added or prior_rows[sid]["inventory_ids"]
        if not ids:
            raise ValueError("Unreconciled brain row: " + sid)
        reconciled.append({"section_id": sid, "label": section["label"], "section_sha256": digest(section),
                           "requirement_ids": ids, "relationship": "explicit_new_side_instantiated_part" if added else prior_rows[sid]["inventory_disposition"],
                           "clinical_representation_complete": False})
    return {"schema_version": 1, "reviewed_at": "2026-10-26", "current_report_rows": len(reconciled),
            "newly_enumerated_report_rows": len({r["report_section_id"] for r in rows}),
            "new_side_instantiated_parts": len(rows), "prior_parts_preserved": 210,
            "current_brain_parts": sum(len(s["required_parts"]) for i in inventory["investigations"] if i["investigation_id"] == BRAIN for s in i["structures"]),
            "clinical_completion_claim": False,
            "current_brain_inventory_sha256": digest(next(i for i in inventory["investigations"] if i["investigation_id"] == BRAIN)),
            "input_sha256": {p: file_hash(root / p) for p in [REPORT_FILE, "data/radiology/holiatlas-labels.json.gz", "data/radiology/holiatlas-hierarchy.json.gz", "docs/holiatlas-source-review-20261023/holiatlas-protocol-rows.json"]},
            "source_context_crosswalk": rows, "all_report_rows": reconciled}


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def reporting_reconciliation(root, inventory):
    current = {}
    files = sorted((root / "data/radiology").glob("*anatomic*.json"))
    for file in files:
        data = json.loads(file.read_text())
        for ident, investigation in data.get("investigations", {}).items():
            if ident in current:
                raise ValueError("Duplicate current reporting investigation: " + ident)
            current[ident] = (str(file.relative_to(root)), investigation)
    compiled = read("data/radiology/descriptor-reporting.json", root)
    compiled_ids = {i["id"] for form in compiled["forms"].values() for i in form["investigations"]}
    if set(current) != compiled_ids:
        raise ValueError("Current authored/compiled reporting investigation inventory differs")
    compiled_rows = {i["id"]: {s["anatomy_id"] for s in i["sections"]} for form in compiled["forms"].values() for i in form["investigations"]}
    for ident, (_, investigation) in current.items():
        if {s["id"] for s in investigation["sections"]} != compiled_rows[ident]:
            raise ValueError("Current authored/compiled anatomical row set differs: " + ident)
    msk = read(MSK_REQUIREMENTS, root)
    required = {i["investigation_id"]: i for i in inventory["investigations"] + msk["investigations"]}
    missing = set(current) - set(required)
    prior = read("docs/holiatlas-hierarchy-review-20261025/pr167-reporting-inventory-audit.json", root)
    prior_missing = {r["investigation_id"] for r in prior["global_exact_id_gaps"]}
    additions_path = root / "data/radiology/anatomic-additions-20261026.json"
    additions = json.loads(additions_path.read_text())["investigations"] if additions_path.exists() else {}
    if set(additions) & (set(required) | prior_missing):
        raise ValueError("New report additions cannot relabel historical investigation identities")
    if missing != prior_missing | set(additions) or set(RELATED_SCOPES) - missing:
        raise ValueError("Current reporting identities changed; review the complete new scope")
    def norm(text):
        return re.sub(r"[^a-z0-9]", "", text.lower())
    rows = []
    for ident, (source_file, inv) in sorted(current.items()):
        if ident in required:
            relation, targets, reason = "same_investigation_identity_requires_row_reconciliation", [ident], "An explicit inventory exists for this investigation. Its presence alone does not prove that every current anatomical report row has been decomposed or represented."
        elif ident in RELATED_SCOPES:
            relation, targets, reason = RELATED_SCOPES[ident]
        elif ident.startswith("template:") or ident in {"ra.ct-contrast-protocols", "ra.recist", "ra.paediatric-ultrasound-values"}:
            relation, targets, reason = "unexpanded_procedure_or_general_template", [], "This scope has no dedicated expanded requirement inventory. Separate anatomy-bearing rows from technique, measurement, workflow and physics rows, then instantiate the selected organ/site/acquisition; do not demand a normal anatomical mesh for a workflow statement."
        else:
            relation, targets, reason = "unexpanded_distinct_investigation", [], "No equivalent expanded investigation has been established. Current named report rows remain explicit expansion work; shared adult regions, titles or module membership cannot supply paediatric, developmental, disease or modality-specific scope."
        structures = {target: required[target]["structures"] for target in targets}
        candidates = {}
        for target, entries in structures.items():
            for structure in entries:
                for entry in [structure, *structure.get("required_parts", [])]:
                    names = {norm(entry["name"])}
                    if structure.get("laterality") in {"left", "right"}:
                        names.add(norm(structure["laterality"] + " " + entry["name"]))
                    for name in names:
                        candidates.setdefault(name, []).append({"investigation_id": target, "requirement_id": entry["id"],
                                                                "relationship": "literal_name_correspondence_only_extent_unverified"})
        report_rows = []
        for section in inv["sections"]:
            matched = candidates.get(norm(section["label"]), [])
            if ident == "ra.thoracolumbar-injury" and re.fullmatch(r"(?:t(?:[1-9]|1[0-2])|l[1-5])", section["id"]):
                matched = [{"investigation_id": "ra.thoracolumbar-fractures", "requirement_id": "thoracolumbar.each_imaged_vertebra",
                            "relationship": "explicit_level_instance_of_unresolved_template", "level": section["id"].upper()}]
            report_rows.append({"section_id": section["id"], "label": section["label"], "section_sha256": digest(section),
                                "candidate_requirements": matched,
                                "reconciliation_status": "candidate_extent_modality_and_representation_review_required" if matched else "explicit_row_expansion_or_typed_nonanatomical_disposition_required",
                                "representation_completion_claim": False})
        same_module = [k for k, v in required.items() if v["module_id"] == inv["guide_id"] and k not in targets]
        additional = [{"index": index, "entry": entry} for index, entry in enumerate(msk["additional_scope"])
                      if entry.get("investigation_id") == ident or (not entry.get("investigation_id") and entry.get("module_id") == inv["guide_id"])]
        rows.append({"investigation_id": ident, "guide_id": inv["guide_id"], "title": inv["title"],
                     "report_source_file": source_file, "report_investigation_sha256": digest(inv),
                     "relationship": relation, "rationale": reason,
                     "related_expanded_investigation_ids": targets,
                     "related_inventory_evidence": [{"investigation_id": target, "title": required[target]["title"],
                         "module_id": required[target]["module_id"], "inventory_sha256": digest(required[target]),
                         "structure_ids": [s["id"] for s in required[target]["structures"]]} for target in targets],
                     "same_module_ids_not_accepted_as_equivalent": same_module,
                     "existing_additional_scope_evidence": additional,
                     "has_dedicated_requirement_inventory": ident in required,
                     "clinical_representation_complete": False, "report_rows": report_rows})
    return {"schema_version": 1, "reviewed_at": "2026-10-26", "scope": "Every current authored and compiled reporting investigation, including supplementary cardiology and general templates",
            "current_investigations": len(rows), "current_report_rows": sum(len(r["report_rows"]) for r in rows),
            "expanded_investigation_identities": len(set(current) & set(required)), "without_dedicated_inventory": len(missing),
            "relationship_counts": dict(sorted(Counter(r["relationship"] for r in rows).items())),
            "clinical_completion_claim": False,
            "limitations": ["Row count includes acquisition, workflow, measurements and disease observations; it is not a count of anatomical meshes required.",
                            "Literal names are review candidates, not proof of extent, laterality, acquisition, disease state, licensing, fidelity or clinical approval.",
                            "A declared duplicate trauma pathway retains unresolved level-specific anatomy. No clinical coverage is inherited through alias, aggregate or partition relationships.",
                            "The 96 exact identities also require review against their newer detailed report rows. Missing identities do not imply that all source artwork is absent."],
            "input_sha256": {str(f.relative_to(root)): file_hash(f) for f in [*files, root / REQUIREMENTS, root / MSK_REQUIREMENTS, root / "data/radiology/descriptor-reporting.json"]},
            "investigations": rows}


def replace_brain_bytes(raw, brain):
    """Replace only the brain object; historical entries use mixed indentation."""
    marker = '    {\n      "investigation_id": "ra.brain-anatomy",'
    if raw.count(marker) != 1:
        raise ValueError("Brain inventory locator is ambiguous")
    start = raw.index(marker) + 4
    _, length = json.JSONDecoder().raw_decode(raw[start:])
    replacement = json.dumps(brain, indent=2, ensure_ascii=True).replace("\n", "\n    ")
    return raw[:start] + replacement + raw[start + length:]


def before_current_brain_requirements(raw, root=ROOT):
    """Strict inverse for frozen receipts; unknown changes are never discarded."""
    text = raw.decode() if isinstance(raw, bytes) else raw
    marker = '    {\n      "investigation_id": "ra.brain-anatomy",'
    if text.count(marker) != 1:
        raise ValueError("Brain inventory locator is ambiguous")
    brain, _ = json.JSONDecoder().raw_decode(text[text.index(marker) + 4:])
    report = read(REPORT_FILE, root)["investigations"][BRAIN]
    additions = {p["id"]: (parent, p) for parent, p in brain_additions(report)}
    seen = set()
    for structure in brain["structures"]:
        parts = []
        for part in structure["required_parts"]:
            if part["id"] in additions:
                if (structure["id"], part) != additions[part["id"]] or part["id"] in seen:
                    raise ValueError("Changed or repeated brain expansion: " + part["id"])
                seen.add(part["id"])
            else:
                parts.append(part)
        structure["required_parts"] = parts
    if seen and seen != set(additions):
        raise ValueError("Incomplete brain expansion")
    if digest(brain) != LEGACY_BRAIN_SHA256:
        raise ValueError("Unrecognized change to preserved brain requirements")
    restored = replace_brain_bytes(text, brain)
    return restored.encode() if isinstance(raw, bytes) else restored


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--write", action="store_true", help="Apply append-only brain expansion and write reconciliation evidence")
    args = parser.parse_args()
    before = read(REQUIREMENTS, args.root)
    report = read(REPORT_FILE, args.root)["investigations"][BRAIN]
    expanded = expand_brain(before, report)
    crosswalk = brain_crosswalk(args.root, expanded, report)
    if args.write:
        brain = next(i for i in expanded["investigations"] if i["investigation_id"] == BRAIN)
        (args.root / REQUIREMENTS).write_text(replace_brain_bytes((args.root / REQUIREMENTS).read_text(), brain))
        write_json(args.root / OUT / "brain-reporting-requirements.json", crosswalk)
        write_json(args.root / "docs/report-additions-20261026/reporting-reconciliation.json", reporting_reconciliation(args.root, expanded))
    print(json.dumps({k: v for k, v in crosswalk.items() if not isinstance(v, list)}))


if __name__ == "__main__":
    main()
