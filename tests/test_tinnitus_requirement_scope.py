"""Source-based tinnitus scope; execution of the expansion remains a root decision."""
import copy
import json
from pathlib import Path

from primer.curriculum import Curriculum
from primer.radiology_catalog import detail, resolve
from tools.anatomy_sources.expand_tinnitus_requirements import build_draft
from tools.check_msk_fidelity import requirements_for
from tools.check_radiology_fidelity import digest

ROOT = Path(__file__).resolve().parents[1]
INV = "ra.tinnitus"


def effective_reference():
    return detail(Curriculum(), resolve(INV))["radiology_reference"]


def requirement_item():
    data = json.loads((ROOT / "data/radiology/non-msk-structure-requirements.json").read_text())
    return next(item for item in data["investigations"] if item["investigation_id"] == INV)


def test_pure_draft_does_not_mutate_inputs_or_supply_normal_findings():
    ref = effective_reference()
    nodes = json.loads((ROOT / "data/radiology/reporting-steps/head-neck.json").read_text())
    node = nodes["investigations"][INV]
    saved_ref, saved_node = copy.deepcopy(ref), copy.deepcopy(node)
    guide, draft_node, item, _ = build_draft(ref, node)
    assert ref == saved_ref and node == saved_node
    assert len(item["structures"]) == 185 and len(requirements_for(item)) == 1110
    assert all(step["normal"] == {} for step in draft_node["steps"])
    assert len(guide["checklist"]) == len(draft_node["steps"]) == 5


def test_all_actual_tinnitus_neural_temporal_and_vascular_interfaces_remain_required():
    item = requirement_item()
    assert item["module_id"] == "rad.5.tinnitus"
    assert len(item["structures"]) == 185 and len(requirements_for(item)) == 1110
    ids = {structure["id"] for structure in item["structures"]}
    assert len(ids) == 185
    for side in ["left", "right"]:
        for key in [
            "cochlear_nerve_full_obtained_course_and_fundal_connections",
            "superior_vestibular_nerve_and_actual_branches",
            "inferior_vestibular_nerve_and_actual_branches",
            "source_resolved_cochlear_fluid_compartments_and_membranes",
            "stapes_crura_footplate_and_annular_interface",
            "carotid_canal_plate_and_carotid_cochlear_interface",
            "persistent_stapedial_and_each_aberrant_carotid_connection",
            "occipital_artery_and_actual_transosseous_dural_branches",
            "ascending_pharyngeal_artery_and_neuromeningeal_branches",
            "each_actual_shunt_site_nidus_or_receiving_pouch",
            "each_actual_perimedullary_drainage_connection",
            "each_actual_postoperative_irradiated_or_device_interface",
            "inferior_olive_and_obtained_medullary_interfaces",
        ]:
            assert "tinnitus." + side + "_" + key in ids
    assert "tinnitus.not_applicable_superior_sagittal_straight_sinus_and_torcular_connections" in ids
    assert all(structure["requires_site_instantiation"] for structure in item["structures"])
    assert all(len(structure["required_parts"]) == 6 for structure in item["structures"])
    assert sum(structure["requires_actual_temporal_evidence"] for structure in item["structures"]) == 6
    assert all(0 <= ref["checklist_index"] < 5 for structure in item["structures"] for ref in structure["report_refs"])
    assert item["clinical_validation_status"].startswith("draft_requires_")


def test_negative_static_image_or_variant_is_not_complete_exclusion_causality_or_pressure():
    ref = effective_reference()
    steps = ref["walkthrough"]["steps"]
    assert all(step["normal"] == {} for step in steps)
    assert "Partial tinnitus/temporal-bone orientation" in ref["walkthrough"]["spatial_model"]["reporting_aim"]
    assert "not uniquely paraganglioma" in steps[2]["tip"]
    assert "does not exclude every dural arteriovenous fistula" in steps[3]["tip"]
    assert "does not measure pressure" in steps[3]["tip"]
    assert "specialist decision" in steps[4]["tip"]
    assert "not a complete angiographic time series" in steps[3]["look"]
    functional = " ".join(requirement_item()["functional_evidence_requirements"])
    assert "actual recorded angiographic phases" in functional
    assert "not alone the clinical diagnosis of IIH" in functional
    assert "a negative or successful result" in functional


def test_effective_reporting_source_contract_is_bound_after_application():
    ref = effective_reference()
    assert requirement_item()["source_contract_sha256"] == digest({key: ref.get(key) for key in ["reporting", "report_templates", "walkthrough", "reading"]})
