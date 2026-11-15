#!/usr/bin/env python3
"""Draft every acquired tinnitus interface; apply only when explicitly executed.

This is a reporting/source inventory, not anatomical approval of existing media.
Importing the module and calling build_draft() perform no file mutations.
"""
import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from primer.curriculum import Curriculum
from primer import radiology_catalog as catalog
from tools.check_radiology_fidelity import digest
from tools.check_msk_fidelity import requirements_for

ROOT = Path(__file__).resolve().parents[2]
INV = "ra.tinnitus"
DATE = "2026-10-08"
SOURCES = [
    {"title": "Radiology Assistant tinnitus source approach", "url": "https://radiologyassistant.nl/head-neck/tinnitus/pulsatile-and-non-pulsatile-tinnitus"},
    {"title": "Original Pegge et al. imaging work-up review", "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC5263210/"},
    {"title": "NICE NG155 phenotype and clinical assessment guidance", "url": "https://www.nice.org.uk/guidance/ng155/chapter/Recommendations"},
    {"title": "Original compartmental imaging review and patient series", "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC3719451/"},
    {"title": "Institutional physiology-based MR protocol and limitations", "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC8917066/"},
    {"title": "Original palatal-tremor case and pathway review", "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC3639700/"},
]


def build_draft(ref, original_node):
    """Return reporting, walkthrough and requirement drafts without writing files."""
    guide = copy.deepcopy(ref["reporting"])
    node = copy.deepcopy(original_node)
    details = [
        "Record supplied symptom side, pulse synchrony or non-synchronous rhythm, audiology and examination; identify actual source coverage and each missing anatomical or temporal question.",
        "Trace every acquired CN VII/VIII component, IAC/CPA and labyrinthine interface; record source-resolved lesion or vessel contact without assigning symptom causation from contact alone.",
        "Review every acquired external/middle/inner-ear, ossicular, otic-capsule, skull-base and vascular-channel wall/interface, including every actual lesion, variant and treated component.",
        "Trace actual covered arteries, veins, each feeder/shunt/nidus/drainage connection and adjacent neural/bone interfaces; record source-supported morphology and only actually acquired transit or flow evidence.",
        "Correlate actual findings with supplied phenotype, clinical/audiological data and source confidence; describe acquired intracranial-pressure/tremor-related anatomy, unresolved high-risk questions and protocol limits.",
    ]
    looks = [
        "Use actual reported pulse synchrony, laterality, onset, hearing findings, neurological/otological findings, otoscopy and supplied comparison. Record obtained modalities, sequence/phase, spatial resolution, neck/skull-base/intracranial extent and dynamic frame order/rate if acquired. The imaging pathway depends on clinical context; neither all non-pulsatile symptoms nor all pulsatile symptoms imply one universal scan combination.",
        "Review acquired heavily T2 source images and pre/postcontrast, DWI/ADC or other sequences as available. Trace facial, cochlear, superior and inferior vestibular components with CSF/dural/IAC fundal interfaces and obtained labyrinthine/central extent. Describe every source vessel relationship, nerve deformation and lesion extension; a named nerve or generic dot does not resolve all fascicles or prove function.",
        "Use actual thin-section CT bone/source planes for fine osseous questions and appropriate acquired MRI for soft tissue/labyrinthine questions. Inspect the tympanic membrane/cavity, each ossicle and muscle interface, windows, cochlear/vestibular/canal boundaries, tegmen, carotid canal, jugular plate and sigmoid plate. Separate true source-resolved defects from partial-volume/artifact and record every actual mass, erosion, extension, repair or device.",
        "Review full obtained cervical and intracranial arterial/venous source extent, wall/lumen, actual variants and lesions, all identified meningeal/pial feeders, shunt site/nidus, venous pouch and outflow. Read acquired time-resolved CTA/MRA/DSA phases in order for transit and cortical/deep/perimedullary reflux. Static TOF/ASL/contrast-enhanced images have technique-specific clues and artifacts; they are not a complete angiographic time series or direct pressure measurement.",
        "Describe source findings and clinical concordance without requiring ipsilateral location as proof of causality. When covered, inspect brain/CSF, sella, optic/sheath/globe and venous findings relevant to intracranial-pressure differential, and palate/muscle/brainstem/cerebellar interfaces relevant to supplied non-synchronous tremor. Clinical movement, audiometry, CSF pressure or invasive vascular evidence remains separately supplied. Escalate a suspected significant vascular lesion through the relevant specialist pathway with actual uncertainty.",
    ]
    tips = [
        "Do not prescribe temporal-bone CT plus all vascular studies for every pulsatile symptom or MRI for every non-pulsatile symptom. State the applicable phenotype/examination and actual acquired coverage; unacquired structures remain unassessed.",
        "A vascular loop/contact, enhancement pattern or lesion size does not independently prove tinnitus causation, tissue identity, neural dysfunction or benefit from decompression.",
        "A high jugular bulb, diverticulum or apparent plate defect may be incidental or artifact; an enhancing promontory mass is not uniquely paraganglioma. Imaging morphology is not histology or the patient's hearing mechanics.",
        "A routine negative MRI does not exclude every dural arteriovenous fistula. TOF signal loss is not uniquely thrombosis and static sinus calibre does not measure pressure. Reflux classification and risk need adequate source angioarchitecture/transit rather than a generic vascular model.",
        "No visible cause on a limited protocol is not an automatic normal or complete-exclusion finding. IIH, palatal/middle-ear muscle activity, systemic causes and treatment benefit require corresponding clinical/physiological evidence; catheter angiography is a specialist decision for the actual unresolved question, not an automatic consequence of every negative scan.",
    ]
    guide.update(
        reviewed_at=DATE,
        protocol=[
            "Record source/patient/side, actual pulse synchrony or other rhythm, onset, supplied otoscopy/audiology/neurological and systemic context, and obtained comparison. Select and document a phenotype- and examination-specific pathway; current guidance does not require imaging for every symmetrical non-pulsatile symptom without associated findings.",
            "Record actually acquired CT/MRI/ultrasound/angiography, field coverage, source sampling, reconstruction/plane, motion and bone/soft-tissue evaluability. Record obtained pre/postcontrast, diffusion/ADC, TOF/ASL or venographic technique without substituting one for another.",
            "For obtained dynamic vascular sources record injection/labeling, arterial/venous phases, timestamps/frame rate, ordering/gaps, projections and transit limitations. A static reconstruction, source flow void or simulated model animation does not supply temporal shunting, physiological pressure, sound or neural/muscle function.",
        ],
        checklist=[{"label": label, "detail": text} for label, text in zip(
            ["Phenotype and acquired coverage", "IAC CPA nerves and labyrinth", "Temporal bone and local interfaces", "Arterial venous and shunt anatomy", "Clinical concordance and source limits"], details)],
        pitfalls=tips,
        sources=SOURCES,
        measurements=[
            {"name": "Focal lesion", "method": "Measure each actual lesion and obtained extension on source-supported orthogonal planes with sequence, side and uncertainty.", "pitfall": "Size or enhancement alone does not prove tissue identity, auditory dysfunction or symptom causation."},
            {"name": "Vascular abnormality", "method": "Describe and measure actual acquired wall/lumen, stenosis, aneurysm/pouch, defect and source feeder/drainage interfaces where evaluable; state source technique and reference segment.", "pitfall": "No universal size cutoff proves tinnitus causation; a static narrowing or geometric model does not directly measure a pressure gradient or flow/transit."},
        ],
        impression_prompts=[
            "Summarise actual acquired anatomical and vascular findings, supplied clinical concordance, source confidence and available temporal evidence.",
            "State unresolved dangerous vascular or skull-base questions and missing coverage; do not automatically supply normality, exclusion, causality or treatment effect.",
        ],
        escalation=["Communicate suspected shunting, dissection or another significant vascular/skull-base lesion through the appropriate specialist pathway, documenting the actual concerning source finding and uncertainty."],
    )
    bodies = [
        "Supplied phenotype/pulse synchrony/other rhythm and side [ ]; source audiology/otoscopy/neurological context [ ]; obtained modality, sequence/phase and anatomical/temporal extent [ ]; unavailable evidence [ ].",
        "Each acquired facial/cochlear/vestibular component and IAC/CPA/labyrinthine interface [ ]; source lesion/contact/extension and actual dimensions [ ]; nerve morphology, sequence/comparison and uncertainty [ ]; unresolved fascicles/function or uncovered course [ ].",
        "Every acquired external/middle/inner-ear, ossicle/window/otic-capsule and skull-base component [ ]; actual carotid/jugular/sigmoid/tegmen wall or defect and adjacent interface [ ]; every lesion/variant/repair and source limitation [ ]; separate tissue/clinical evidence [ ].",
        "Each actual covered artery/vein, source wall/lumen and variant/lesion [ ]; every identified feeder, shunt/nidus/pouch and drainage/reflux route [ ]; acquired phases/transit and confidence [ ]; unavailable microscopic connections, flow/pressure or coverage [ ].",
        "Source-supported findings and supplied symptom/clinical concordance [ ]; actual acquired pressure/tremor-related structures and separate physiological evidence [ ]; incidental-versus-contributory differential [ ]; unresolved high-risk question and targeted specialist communication [ ].",
    ]
    for section, body in zip(guide["template_sections"], bodies):
        section["body"] = body
    removed = sum(bool(s.get("normal")) for s in node["steps"])
    node["reviewed_at"] = DATE
    for index, step in enumerate(node["steps"]):
        step.update(detail=details[index], normal={}, look=looks[index], tip=tips[index], findings=[
            "Actual acquired " + step["label"].lower() + " findings [ ]; source/side/sequence/phase and extent [ ]; supplied clinical context, uncertainty and unassessed evidence [ ]."
        ])
    node["model"] = {
        "family": "temporal",
        "reporting_aim": "Partial tinnitus/temporal-bone orientation only. This schematic does not provide every native nerve/fascicle, labyrinthine/ossicular/muscle/wall interface, arterial feeder, shunt/nidus or venous drain, patient variant, lesion or treated structure. It supplies no acquired vascular transit/reflux, pressure, sound, neural/muscle function, causal diagnosis or treatment effect.",
    }
    structures = []
    shape_parts = [
        "every_actual_component_and_full_source_extent",
        "each_source_resolved_wall_layer_or_margin",
        "every_branch_connection_or_compartment_boundary",
        "each_adjacent_neural_vascular_bone_or_soft_tissue_interface",
        "each_actual_variant_lesion_repair_and_source_coordinate",
        "unresolved_microscopic_functional_or_uncovered_extent",
    ]
    vascular_parts = [
        "actual_origin_full_obtained_course_and_every_branch",
        "source_resolved_wall_lumen_or_pouch_boundary",
        "each_actual_anastomosis_feeder_shunt_or_drainage_connection",
        "every_adjacent_tissue_bone_nerve_or_vascular_interface",
        "every_lesion_variant_repair_and_source_phase_coordinate",
        "unresolved_microvascular_transit_pressure_or_uncovered_extent",
    ]
    event_parts = [
        "actual_patient_trial_or_injection_and_source_identity",
        "every_observed_frame_phase_and_temporal_boundary",
        "each_resolved_flow_movement_or_response_landmark",
        "source_order_rate_projection_calibration_and_gaps",
        "actual_recorded_comparison_or_test_response",
        "unobserved_time_or_unresolved_causal_functional_mechanism",
    ]

    def add(key, steps, side="not_applicable", vascular=False, event=False, pathology=False,
            modalities=None, urls=None, basis="full_effective_tinnitus_reporting_anatomy_and_actual_source_interfaces"):
        ident = "tinnitus." + side + "_" + key
        parts = event_parts if event else vascular_parts if vascular else shape_parts
        structures.append({
            "id": ident,
            "name": side.replace("_", " ").capitalize() + " " + key.replace("_", " "),
            "tissue_class": "source_tinnitus_neural_temporal_vascular_or_clinical_event_interface",
            "required_parts": [{"id": ident + "." + part, "name": part.replace("_", " ").capitalize()} for part in parts],
            "laterality": side,
            "modality_scope": modalities or ["CT", "MRI"],
            "condition": "Independently instantiate each actual source side, component, branch, wall, feeder, shunt/nidus, drain, variant, lesion, repair and acquisition/phase interface. The listed group is a known floor; modality permission is not source resolution or proof that every fine boundary was acquired. Missing, microscopic and functional extent remains explicit.",
            "requirement_basis": basis,
            "report_refs": [{"checklist_index": index, **guide["checklist"][index]} for index in steps],
            "walkthrough_step_indices": steps,
            "source_urls": urls or [source["url"] for source in SOURCES[:5]],
            "requires_site_instantiation": True,
            "context_requirements": {"purpose": "pathology_example" if pathology or event else "anatomical_reference"},
            "requires_actual_temporal_evidence": event,
        })

    for side in ["left", "right"]:
        for key in [
            "facial_nerve_cisternal_IAC_and_obtained_intratemporal_course",
            "cochlear_nerve_full_obtained_course_and_fundal_connections",
            "superior_vestibular_nerve_and_actual_branches",
            "inferior_vestibular_nerve_and_actual_branches",
            "IAC_porus_fundus_and_crista_boundaries",
            "CPA_CSF_and_dural_interfaces",
            "obtained_CN_V_VI_and_lower_cranial_nerve_interfaces",
            "cochlear_nuclei_and_obtained_auditory_pathways",
            "obtained_lateral_lemniscus_and_inferior_colliculus",
            "obtained_medial_geniculate_radiation_and_auditory_cortex",
            "every_actual_IAC_CPA_neurovascular_contact",
        ]:
            add(key, [1, 4], side, modalities=["MRI"])
        for key in [
            "external_auditory_canal_wall_lumen_and_content",
            "tympanic_membrane_and_annular_interfaces",
            "epitympanum_mesotympanum_and_hypotympanum",
            "cochlear_promontory_and_adjacent_vascular_interfaces",
            "malleus_each_actual_component_and_connection",
            "incus_each_actual_component_and_connection",
            "stapes_crura_footplate_and_annular_interface",
            "ossicular_joints_ligaments_and_suspension",
            "stapedius_muscle_tendon_and_pyramidal_eminence",
            "tensor_tympani_muscle_tendon_and_semicanal",
            "oval_window_and_vestibular_interface",
            "round_window_membrane_niche_and_cochlear_interface",
            "cochlear_turns_modiolus_and_otic_capsule",
            "source_resolved_cochlear_fluid_compartments_and_membranes",
            "vestibule_utricle_saccule_and_actual_interfaces",
            "superior_semicircular_canal_wall_lumen_and_roof",
            "posterior_semicircular_canal_wall_lumen_and_interfaces",
            "lateral_semicircular_canal_wall_lumen_and_interfaces",
            "vestibular_aqueduct_and_endolymphatic_duct_sac",
            "cochlear_aqueduct_and_obtained_connections",
            "facial_canal_geniculate_and_actual_branches",
            "tegmen_tympani_mastoideum_dura_and_brain_interface",
            "mastoid_antrum_air_cells_and_each_actual_septum",
            "carotid_canal_plate_and_carotid_cochlear_interface",
            "jugular_bulb_plate_and_jugular_foramen_interfaces",
            "sigmoid_plate_and_each_mastoid_or_middle_ear_interface",
            "foramen_spinosum_and_stapedial_artery_passage",
            "petrous_apex_and_obtained_skull_base_interfaces",
            "Eustachian_tube_and_obtained_nasopharyngeal_interfaces",
        ]:
            add(key, [2, 4], side)
        for key in [
            "common_carotid_artery_and_bifurcation",
            "cervical_internal_carotid_artery",
            "petrous_internal_carotid_artery_and_aberrant_course",
            "cavernous_supraclinoid_internal_carotid_and_actual_branches",
            "external_carotid_artery_and_every_actual_feeder",
            "occipital_artery_and_actual_transosseous_dural_branches",
            "middle_meningeal_artery_and_actual_branches",
            "ascending_pharyngeal_artery_and_neuromeningeal_branches",
            "posterior_auricular_superficial_temporal_and_other_ECA_branches",
            "ICA_meningohypophyseal_inferolateral_and_other_dural_branches",
            "vertebral_V1_V2_V3_V4_and_actual_dural_branches",
            "anterior_inferior_cerebellar_and_labyrinthine_artery",
            "posterior_inferior_and_superior_cerebellar_artery_contacts",
            "persistent_stapedial_and_each_aberrant_carotid_connection",
            "every_other_actual_pial_dural_or_cervical_feeder",
        ]:
            add(key, [3, 4], side, vascular=True, modalities=["CT", "MRI", "Radiography", "Ultrasound"])
        for key in [
            "transverse_sinus_lumen_wall_and_actual_granulations",
            "sigmoid_sinus_lumen_wall_and_actual_diverticulum",
            "jugular_bulb_and_every_actual_pouch_or_variant",
            "internal_jugular_vein_full_obtained_course",
            "styloid_C1_soft_tissue_and_jugular_compression_interface",
            "cavernous_sinus_and_actual_arteriovenous_interfaces",
            "superior_and_inferior_petrosal_sinus",
            "mastoid_and_other_actual_emissary_veins",
            "anterior_posterior_condylar_veins_and_channels",
            "vertebral_paravertebral_and_epidural_venous_plexus",
            "each_obtained_cortical_or_deep_venous_drain",
            "each_actual_perimedullary_drainage_connection",
            "each_actual_shunt_site_nidus_or_receiving_pouch",
            "each_actual_stenosis_thrombus_or_collateral_interface",
        ]:
            add(key, [3, 4], side, vascular=True, pathology="shunt" in key or "thrombus" in key,
                modalities=["CT", "MRI", "Radiography", "Ultrasound"])
        for key in [
            "every_actual_IAC_CPA_or_intracochlear_lesion_interface",
            "every_actual_tympanic_jugular_or_skull_base_mass_interface",
            "each_actual_carotid_or_vagal_space_lesion_interface",
            "each_actual_inflammatory_or_cholesteatoma_interface",
            "each_actual_otosclerotic_or_other_osseous_lesion_extent",
            "each_actual_dehiscence_fistula_or_encephalocele_interface",
            "each_actual_aneurysm_dissection_or_vessel_wall_lesion",
            "each_actual_postoperative_irradiated_or_device_interface",
        ]:
            add(key, [1, 2, 3, 4], side, pathology=True)
        for key in [
            "optic_nerve_sheath_and_perioptic_CSF",
            "posterior_globe_and_obtained_orbital_interfaces",
            "Meckel_cave_and_obtained_CSF_recesses",
        ]:
            add(key, [4], side, modalities=["MRI", "CT"])
        for key in [
            "tensor_and_levator_veli_palatini_and_actual_connections",
            "inferior_olive_and_obtained_medullary_interfaces",
            "dentate_nucleus_and_superior_cerebellar_peduncle",
            "obtained_red_nucleus_and_central_tegmental_tract",
            "inferior_cerebellar_peduncle_and_actual_pathway_interfaces",
        ]:
            add(key, [4], side, modalities=["MRI"], urls=[SOURCES[2]["url"], SOURCES[5]["url"]])
    for key in [
        "basilar_artery_and_every_actual_branch_or_variant",
        "superior_sagittal_straight_sinus_and_torcular_connections",
        "obtained_falx_tentorium_and_every_dural_shunt_interface",
        "obtained_brainstem_cerebellum_brain_and_CSF_spaces",
        "sella_pituitary_suprasellar_and_CSF_interfaces",
        "obtained_craniocervical_junction_and_spinal_extent",
        "every_actual_midline_or_crossing_vascular_lesion_extent",
        "soft_palate_uvula_and_obtained_pharyngeal_interfaces",
        "each_encountered_unlisted_branch_variant_lesion_or_treatment",
    ]:
        add(key, [1, 2, 3, 4], pathology="lesion" in key)
    for key in [
        "each_actual_dynamic_arterial_to_venous_transit",
        "each_observed_cortical_deep_or_perimedullary_reflux_route",
        "each_actual_recorded_flow_or_pressure_measurement",
        "each_actual_symptom_pulse_or_other_rhythm_correlation",
        "each_observed_palatal_or_middle_ear_movement_and_response",
        "each_actual_recorded_comparison_or_treatment_response",
    ]:
        add(key, [0, 3, 4], event=True, modalities=["CT", "MRI", "Radiography", "Ultrasound"])
    item = {
        "investigation_id": INV,
        "module_id": ref["investigation"]["module_id"],
        "title": "Every acquired tinnitus neural temporal vascular and actual dynamic interface",
        "scope_status": "expanded_draft_requires_independent_tinnitus_anatomical_and_vascular_review",
        "modality_scope": ["CT", "MRI", "Radiography", "Ultrasound"],
        "sources": [dict(source, reviewed_at=DATE, review_status="primary_reporting_context_no_graphics_or_cine_reused") for source in SOURCES],
        "reporting_checklist": guide["checklist"],
        "reporting_template_sections": guide["template_sections"],
        "structures": structures,
        "expansion_rules": [
            "Independently instantiate every actual side, branch, fine tissue/wall, variant, feeder/shunt/nidus/drain, lesion and repair; these groups are a known floor rather than a complete list of all possible patient anatomy.",
            "One CT/MRI/DSA source, generic temporal model or isolated still does not supply all components or the same patient across sequences; anatomy and clinical findings require actual matched source provenance.",
            "Fine membrane, fascicle, microscopic vessel, layer and complete 3D boundaries remain required but unproven until source-resolved anatomy is independently reviewed; modality permission is not acquisition or anatomical approval.",
        ],
        "source_scope_issues": [
            "The current partial temporal model and selected reference stills do not establish complete patient IAC/labyrinthine/bony/neural anatomy, all arterial feeders or every shunt and venous drainage connection.",
            "Source pathways differ by phenotype and examination; older reviews or one institutional MR protocol are not a universal imaging mandate, an automatic catheter angiography indication or a validated present-patient classifier.",
            "No source graphics or cine are reused by this script, and no structure/asset receives clinical coverage approval from this draft inventory.",
        ],
        "functional_evidence_requirements": [
            "Shunt transit and drainage/reflux direction require adequate actual recorded angiographic phases/frame order/rate, injection/projection and source coverage; a static TOF/ASL clue or smooth model animation is not the complete temporal evidence.",
            "Physiological pressure/gradient and flow measurements require actual calibrated clinical measurements and technique; sinus calibre, signal loss or geometric model data are not direct pressure results.",
            "Supplied pulse synchrony, sound, audiometry, otoscopy, neural function and clinical palatal/middle-ear movement are separate evidence; static anatomy alone does not prove symptoms or exclude non-structural/systemic causes.",
            "Imaging signs associated with intracranial pressure are not alone the clinical diagnosis of IIH; corresponding actual clinical/ophthalmic and pressure evidence, when supplied, stays separate.",
            "Tissue identity, causal attribution, future risk and treatment effect need actual relevant clinical/pathological/comparison evidence; absent clinical response recording is not a negative or successful result.",
        ],
        "clinical_validation_status": "draft_requires_neuroradiologist_neurovascular_otological_and_anatomical_review",
    }
    return guide, node, item, removed


def build():
    ref = catalog.detail(Curriculum(), catalog.resolve(INV))["radiology_reference"]
    steps_path = ROOT / "data/radiology/reporting-steps/head-neck.json"
    text = steps_path.read_text()
    start = text.index("{", text.index('"' + INV + '"'))
    original_node, end = json.JSONDecoder().raw_decode(text, start)
    guide, node, item, removed = build_draft(ref, original_node)
    overrides_path = ROOT / "data/radiology/investigation-overrides-non-msk.json"
    overrides = json.loads(overrides_path.read_text())
    overrides.setdefault(INV, {})["reporting"] = guide
    overrides_path.write_text(json.dumps(overrides, indent=2) + "\n")
    steps_path.write_text(text[:start] + json.dumps(node, indent=2).replace("\n", "\n    ") + text[end:])
    for value in vars(catalog).values():
        if callable(getattr(value, "cache_clear", None)):
            value.cache_clear()
    effective_ref = catalog.detail(Curriculum(), catalog.resolve(INV))["radiology_reference"]
    item["source_contract_sha256"] = digest({key: effective_ref.get(key) for key in ["reporting", "report_templates", "walkthrough", "reading"]})
    requirements_path = ROOT / "data/radiology/non-msk-structure-requirements.json"
    data = json.loads(requirements_path.read_text())
    data["investigations"] = [existing for existing in data["investigations"] if existing["investigation_id"] != INV] + [item]
    data["scope"]["catalog_investigation_ids"] = [existing["investigation_id"] for existing in data["investigations"]]
    requirements_path.write_text(json.dumps(data, indent=2) + "\n")
    parts = len(requirements_for(item))
    print(len(item["structures"]), "groups;", parts, "parts;", parts * 3, "representation obligations;", removed, "unsupported normal presets removed")


if __name__ == "__main__":
    build()
