"""Full esophageal draft scope must not collapse into an outline or static diagnosis."""
import copy
import json
from pathlib import Path

import pytest
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail, resolve
from tools.anatomy_sources.expand_esophagus_requirements import build_draft
from tools.check_msk_fidelity import requirements_for
from tools.check_radiology_fidelity import digest

ROOT = Path(__file__).resolve().parents[1]
INV = "ra.esophagus"


def inputs():
    ref = detail(Curriculum(), resolve(INV))["radiology_reference"]
    node = json.loads((ROOT / "data/radiology/reporting-steps/chest.json").read_text())["investigations"][INV]
    return ref, node


def test_draft_is_pure_full_scope_and_removes_every_unsupported_preset():
    ref, node = inputs()
    saved_ref, saved_node = copy.deepcopy(ref), copy.deepcopy(node)
    guide, draft_node, item, removed = build_draft(ref, node)
    assert (ref, node) == (saved_ref, saved_node)
    assert removed == sum(bool(step.get("normal")) for step in node["steps"])
    assert all(step["normal"] == {} for step in draft_node["steps"])
    assert len(guide["checklist"]) == len(draft_node["steps"]) == 5
    assert len(item["structures"]) == 139
    assert len(requirements_for(item)) == 834
    assert len({structure["id"] for structure in item["structures"]}) == 139
    assert item["module_id"] == "rad.5.esophagus-swallowing"
    assert item["clinical_validation_status"].startswith("draft_requires_")


def test_all_actual_layers_branch_sites_lesions_hiatal_and_treated_routes_remain_required():
    _, _, item, _ = build_draft(*inputs())
    structures = {structure["id"]: structure for structure in item["structures"]}
    for segment in ["cervical", "upper_thoracic", "middle_thoracic", "lower_thoracic", "abdominal"]:
        for part in [
            "lumen_and_actual_contents", "mucosal_epithelium_and_luminal_surface",
            "lamina_propria_and_muscularis_mucosae", "submucosa_and_actual_glands_ducts",
            "inner_circular_and_outer_longitudinal_muscularis_propria",
            "actual_neural_vascular_and_lymphatic_plexuses",
            "every_actual_lesion_variant_or_treated_component",
        ]:
            assert "esophagus.not_applicable_" + segment + "_" + part in structures
    for side in ["left", "right"]:
        for key in [
            "recurrent_or_nonrecurrent_laryngeal_nerve_and_connections",
            "subclavian_carotid_and_each_actual_arch_variant_connection",
            "pulmonary_arterial_venous_and_actual_variant_routes",
            "diaphragmatic_crus_hiatal_margin_and_actual_attachments",
            "actual_perigastric_left_gastric_and_coeliac_nodes",
            "every_actual_lateral_leak_fistula_collection_or_repair",
        ]:
            assert "esophagus." + side + "_" + key in structures
        nodal = structures["esophagus." + side + "_actual_upper_paratracheal_and_paraeosophageal_nodes"]
        assert any("cortex_hilum_margin_and_capsular_interface" in part["id"] for part in nodal["required_parts"])
    for key in [
        "azygos_hemiazygos_accessory_hemiazygos_and_connections",
        "thoracic_duct_and_every_actual_lymphatic_connection",
        "actual_abdominal_peritoneal_serosal_and_lesser_omental_interfaces",
        "gastric_cardia_fundus_folds_and_actual_squamocolumnar_transition",
        "each_actual_hernia_sac_neck_attachment_and_diaphragmatic_interface",
        "each_actual_pseudodiverticular_gland_duct_and_mucosal_orifice",
        "every_actual_intramural_hematoma_or_dissection_lumen_and_septum",
        "each_actual_anastomosis_conduit_and_reconstructed_route",
        "each_actual_stent_tube_drain_and_device_to_tissue_connection",
        "each_encountered_unlisted_segment_branch_variant_lesion_or_repair",
    ]:
        assert "esophagus.not_applicable_" + key in structures
    assert all(structure["requires_site_instantiation"] for structure in structures.values())
    assert all(len(structure["required_parts"]) == 6 for structure in structures.values())
    assert all(0 <= report["checklist_index"] < 5 for structure in structures.values() for report in structure["report_refs"])


def test_screening_pressure_histology_and_temporal_evidence_are_separate():
    guide, node, item, _ = build_draft(*inputs())
    assert sum(structure["requires_actual_temporal_evidence"] for structure in item["structures"]) == 12
    assert "screening does not constitute a complete dedicated esophagram" in node["steps"][0]["look"]
    assert "not proof of benignity" in node["steps"][2]["tip"]
    assert "not alone a diagnosis of GERD" in node["steps"][3]["tip"]
    assert "does not exclude every perforation" in node["steps"][4]["tip"]
    assert "whole-esophagus mask is not every layer" in node["steps"][1]["look"]
    assert "Partial esophageal orientation" in node["model"]["reporting_aim"]
    protocol = " ".join(guide["protocol"])
    assert "stored frame rate/order/timestamps/gaps" in protocol
    assert "adult guidance is not an automatic pediatric protocol" in protocol
    functional = " ".join(item["functional_evidence_requirements"])
    assert "without prior invasive foregut intervention" in functional
    assert "large/paraesophageal hernias" in functional
    assert "mechanical obstruction" in functional
    assert "a still or animated geometric model does not supply the events" in functional
    assert "No smooth taper, plaque, ulcer, calcification or reticular pattern" in functional
    assert all(not structure.get("requirement_coverage") for structure in item["structures"])


def test_changed_reader_topology_requires_review_instead_of_truncation():
    ref, node = inputs()
    node["steps"].append(copy.deepcopy(node["steps"][0]))
    with pytest.raises(ValueError, match="no longer has five sections"):
        build_draft(ref, node)


def test_applied_scope_binds_effective_reader_when_present():
    data = json.loads((ROOT / "data/radiology/non-msk-structure-requirements.json").read_text())
    applied = next((item for item in data["investigations"] if item["investigation_id"] == INV), None)
    if applied is None or applied.get("scope_status") != "expanded_draft_requires_independent_esophageal_anatomical_and_temporal_review":
        pytest.skip("Draft has not been explicitly applied to the global reader")
    ref, node = inputs()
    _, _, draft, _ = build_draft(ref, node)
    assert applied["structures"] == draft["structures"]
    assert applied["source_contract_sha256"] == digest({key: ref.get(key) for key in ["reporting", "report_templates", "walkthrough", "reading"]})
    assert all(step["normal"] == {} for step in ref["walkthrough"]["steps"])


def test_every_source_measurement_is_attached_to_relevant_walkthrough_steps():
    guide,node,_,_=build_draft(*inputs())
    expected={r['name'] for r in guide['measurements']};used={m for s in node['steps'] for m in s.get('measurements',[])}
    assert expected==used
    assert 'Timed source retention' in node['steps'][0]['measurements']
    assert 'Stricture extent' in node['steps'][2]['measurements']
