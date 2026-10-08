#!/usr/bin/env python3
"""Draft full esophageal source anatomy; no mutation on import or build_draft().

The explicit build() command changes only ra.esophagus. This reporting inventory
does not approve existing media, native geometry, clinical diagnosis or function.
"""
import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from primer.curriculum import Curriculum
from primer import radiology_catalog as catalog
from tools.check_msk_fidelity import requirements_for
from tools.check_radiology_fidelity import digest

ROOT = Path(__file__).resolve().parents[2]
INV = "ra.esophagus"
DATE = "2026-10-08"
SOURCES = [
    {"title": "Radiology Assistant esophagus I source reporting", "url": "https://radiologyassistant.nl/chest/esophagus/esophagus-i-anatomy-rings-inflammation"},
    {"title": "Radiology Assistant esophagus II source reporting", "url": "https://radiologyassistant.nl/chest/esophagus/esophagus-ii-strictures-acute-syndromes-neoplasms-and-vascular-impressions"},
    {"title": "ACG esophageal physiologic testing guideline", "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC9468980/"},
    {"title": "ACG adult achalasia guideline", "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC9896940/"},
    {"title": "Chicago Classification v4.0 original consensus", "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC8034247/"},
    {"title": "ACG GERD guideline", "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC8754510/"},
    {"title": "ACG updated Barrett esophagus guideline", "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC10259184/"},
    {"title": "WSES original esophageal emergencies guideline", "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC6544956/"},
    {"title": "ESSD–ESGAR adult VFSS technical consensus", "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC12081525/"},
    {"title": "Original esophageal surgical anatomy review", "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC5538986/"},
    {"title": "Original paraesophageal hernia surgical anatomy review", "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC7263794/"},
    {"title": "Original microscopic esophageal anatomy review", "url": "https://pubmed.ncbi.nlm.nih.gov/29761508/"},
]


def build_draft(ref, original_node):
    """Return reporting, walkthrough, requirements and removed-preset count."""
    guide = copy.deepcopy(ref["reporting"])
    node = copy.deepcopy(original_node)
    if len(node["steps"]) != 5 or len(guide["template_sections"]) != 5:
        raise ValueError("Review required: effective esophagus reader no longer has five sections")
    details = [
        "Map every acquired cervical, thoracic and abdominal esophageal component and EGJ/hiatal relationship; describe actual lumen, contents and recorded transit with source coverage and uncertainty.",
        "Trace every source-resolved wall, mucosal surface and actual lesion component; retain layer, ulcer, gland/duct, neural and vascular interfaces as required anatomy while keeping unresolved microscopic tissue and identity explicit.",
        "Inventory every actual ring, web, bar, stricture, pouch or communication with source site, boundary and passage effect; morphology alone does not supply cause, pressure, histology or an intervention decision.",
        "Trace all acquired esophageal relationships to actual vessels, airways, neural routes, nodes, mediastinal tissues and hiatus/stomach; distinguish source contact or impression from supported invasion or physiological causation.",
        "Map each actual injury, leak, fistula, intramural dissection, collection and treated/device interface, with acquired spread and timing; document concerning findings, negative-study limits and actual clinical communication.",
    ]
    looks = [
        "Trace the full obtained pharyngoesophageal-to-gastric course and every lumen/content component, including actual diverticular or duplicated routes. Describe cervical/thoracic/abdominal site, distension, axes/calibration, EGJ relative to diaphragm and acquired gastric extent. Compare recorded bolus clearance only at actual source times and positions. VFSS esophageal screening does not constitute a complete dedicated esophagram; CT or static MRI does not provide cine transit or sphincter pressure.",
        "Review obtained fluoroscopic single/double-contrast surface detail, CT/MRI wall and extramural interfaces, and separately supplied endoscopic/EUS or pathological evidence. Map actual fold, plaque, erosion, ulcer, intramural/exophytic/intraluminal component, stalk and each adjacent interface. Wall layers, glands/ducts and neural/vascular plexuses remain required but unproven unless their actual source resolution and independent review support them; a whole-esophagus mask is not every layer.",
        "Use actual distended source views for each narrowing, with site, minimum lumen, length, circumferential extent, contour, upstream contents and acquired passage. For every pouch map neck, wall, retained content and communication. Record whether an apparent ring/bar persists across obtained frames. Tapering, shouldering or calcification has a differential; pseudoachalasia, inflammation, treatment and neoplasia are not ruled out by smooth contour.",
        "Trace each actual acquired arterial/venous course and branch, including variant arches/subclavian or pulmonary routes, vessel wall/lumen and intervening tissues. Review trachea/bronchi, left atrium/pericardium, mediastinal compartments, nodes, pleura, spine and neural/lymphatic connections. Map diaphragm/crura, phrenoesophageal attachments, EGJ, herniated stomach/other contents and rotation with coverage limits. Preserve every source variant and treated route rather than substituting a generic vascular or hiatal model.",
        "Identify actual source injury level/circumference, wall defect or intramural tract, extraluminal contrast/material, air/fluid and connections to mediastinum, pleura, lung, airway or abdomen. Record the contrast type/route, pre/postcontrast or fluoroscopic acquisition, timing, obtained extent and artifacts. Review each actual anastomosis, conduit, myotomy/fundoplication region, stent, tube or drain and comparison; management depends on the supplied clinical setting and relevant team, not a templated lesion label.",
    ]
    tips = [
        "A retained column or distal bird-beak pattern is a source observation; the clinical diagnosis and subtype use applicable complementary tests and context. A selected still, screening pass or static surface does not certify normal clearance, sphincter relaxation or absence of aspiration.",
        "Plaques, ulceration, wall thickening or a reticular surface do not independently prove an organism, Barrett metaplasia, dysplasia or tumour histology. Supplied endoscopic sampling/pathology and applicable diagnostic framework stay separate; static imaging does not resolve every microscopic layer.",
        "Smooth tapered narrowing is not proof of benignity, and shouldering is not a unique carcinoma diagnosis. Distension and projection alter apparent calibre; one unacquired or inadequately distended segment cannot be supplied as negative.",
        "External contact, absent visible fat plane or a vascular impression alone does not establish invasion, flow direction, pressure or symptom causation. A hiatal hernia or observed reflux is not alone a diagnosis of GERD or an automatic operative indication.",
        "No extravasation on a limited contrast study does not exclude every perforation. Pneumomediastinum, fluid or wall thickening has a differential; anatomical side or a historical pattern is not a compulsory injury site or a unique causal diagnosis.",
    ]
    guide.update(
        reviewed_at=DATE,
        protocol=[
            "Record source/patient, indication and actual dysphagia/acute-injury context, age/population, prior interventions and dated comparison. Identify whether this is VFSS screening, dedicated esophagram, CT/CT esophagography, MRI or separately supplied endoscopic/EUS/physiological evidence; adult guidance is not an automatic pediatric protocol.",
            "Record actual contrast type/concentration/volume and oral or other delivery route, single/double-contrast technique, bolus/tablet if tested, projections, posture, manoeuvres, distension and obtained cervical/thoracic/EGJ/gastric extent. Record fluoroscopy pulse rate, stored frame rate/order/timestamps/gaps and spatial calibration where known.",
            "For CT/MRI record obtained sampling, source planes/reconstructions, IV/oral contrast and phases or sequences, motion/artifact and wall/soft-tissue evaluability. For timed transit document actual ingestion/time zero, recorded acquisition times, position and calibrated retained column; no generic cutoffs are imposed on a different source protocol.",
            "Keep endoscopic/EUS mucosal and layer evidence, pathological/assay identity, HRM/HRIM pressure or clearance, FLIP distensibility and ambulatory pH/impedance results as identified separate sources. Manometric classification requires its actual applicable protocol, anatomy and clinical context, not a fluoroscopic shape alone.",
        ],
        checklist=[{"label": label, "detail": text} for label, text in zip(
            ["Full course lumen and recorded passage", "Wall surface and lesion components", "Every narrowing pouch and communication", "Extrinsic hiatal and gastric interfaces", "Acute treated and device interfaces"], details)],
        pitfalls=tips,
        sources=SOURCES,
        measurements=[
            {"name": "Stricture extent", "method": "Measure every actual acquired narrowing length and source-resolved minimum lumen on stated distended projection/plane with calibration, site and uncertainty.", "pitfall": "Distension, obliquity and projection overlap change calibre; no source measurement proves cause or safe treatment."},
            {"name": "Wall lesion and extramural extent", "method": "Measure each acquired wall/lesion component and extension on source-supported planes; state distension, sequence/phase, edge definition and comparison.", "pitfall": "Collapsed lumen affects apparent thickness. Source contact is not microscopic invasion or histology."},
            {"name": "Timed source retention", "method": "When actually obtained, record bolus/volume, posture, ingestion time zero, each real acquisition time and calibrated column height/width or observed tablet passage.", "pitfall": "A source protocol and timepoints must accompany observations; a static image or an unrelated threshold cannot establish motility subtype."},
            {"name": "Hiatal and gastric relationships", "method": "Record actual EGJ/diaphragmatic relationships and herniated components or source-supported dimensions with posture, phase and coverage.", "pitfall": "Geometry varies during the examination; a vestibule or gastric fold landmark is not automatically a hiatal hernia, Barrett segment or physiological pressure zone."},
        ],
        classification=None,
        criteria_table=None,
        impression_prompts=[
            "Summarise actual acquired course, wall/lumen, narrowing, lesion and adjacent/hiatal findings, source-supported transit or complications, supplied diagnosis and confidence.",
            "State missing anatomy/time coverage and separate pathological or physiological questions. Do not automatically fill normality, histology, motility subtype, clinical stage or treatment eligibility.",
        ],
        escalation=["Promptly communicate source findings concerning for perforation, significant leak/fistula, acute obstruction, compromised herniated tissues or another important acute complication through the appropriate clinical team, documenting uncertainty, recipient and time."],
    )
    bodies = [
        "Every acquired cervical/thoracic/abdominal segment and lumen/content [ ]; actual EGJ/hiatal/gastric extent [ ]; source distension/projection/calibration [ ]; acquired trial/time-specific transit and uncovered extent [ ].",
        "Every source-resolved wall/surface/layer and actual lesion component/stalk/ulcer [ ]; source site, contour, thickness/length and adjacent interfaces [ ]; separately supplied endoscopic/EUS/pathological evidence [ ]; unresolved microscopic anatomy or tissue identity [ ].",
        "Each actual ring/web/bar/stricture/pouch/communication [ ]; source neck, wall/content, site/length/minimum lumen and distension [ ]; persistence or recorded passage/upstream effect [ ]; differential and unavailable physiological/tissue evidence [ ].",
        "Each actual arterial/venous/airway/neural/nodal/mediastinal interface and variant [ ]; source impression/contact versus supported extension [ ]; diaphragm/crura/EGJ/herniated gastric or other components and rotation [ ]; unresolved flow/function/invasion and source limits [ ].",
        "Every actual wall injury/leak/fistula/intramural tract and obtained spread [ ]; source contrast route/phase/time and confidence [ ]; collections/pleural/airway/abdominal interfaces [ ]; all obtained repair/anastomosis/conduit/device components [ ]; comparison, missing coverage and clinical communication [ ].",
    ]
    for section, body in zip(guide["template_sections"], bodies):
        section["body"] = body
    removed = sum(bool(step.get("normal")) for step in node["steps"])
    node["reviewed_at"] = DATE
    measure_steps = [["Timed source retention", "Hiatal and gastric relationships"], ["Wall lesion and extramural extent"], ["Stricture extent"], ["Hiatal and gastric relationships"], ["Wall lesion and extramural extent"]]
    for index, step in enumerate(node["steps"]):
        step.update(detail=details[index], normal={}, look=looks[index], tip=tips[index], measurements=measure_steps[index], findings=[
            "Actual acquired " + step["label"].lower() + " finding/interface [ ]; source site/side, modality/projection/phase/time and extent [ ]; supplied context, differential and unassessed evidence [ ]."
        ])
    node["model"] = {
        "family": "swallow",
        "reporting_aim": "Partial esophageal orientation only. This static schematic does not contain every native cervical/thoracic/abdominal wall layer, gland/duct, neural/vascular/lymphatic branch, mucosal lesion, pouch/hiatal/gastric or treated interface. It supplies no acquired transit, sphincter pressure/relaxation, reflux diagnosis, histology, complete leak exclusion or treatment effect.",
    }
    structures = []
    shape_parts = [
        "every_actual_component_full_source_extent_and_site",
        "each_source_resolved_layer_wall_or_surface_boundary",
        "every_actual_internal_content_branch_or_communication",
        "each_adjacent_tissue_lumen_vascular_or_neural_interface",
        "every_variant_lesion_repair_and_source_coordinate",
        "unresolved_microscopic_functional_or_uncovered_extent",
    ]
    route_parts = [
        "actual_origin_full_obtained_course_and_each_branch",
        "each_source_resolved_wall_lumen_or_route_boundary",
        "every_actual_connection_anastomosis_target_or_drain",
        "each_esophageal_airway_neural_or_other_tissue_interface",
        "every_variant_lesion_repair_and_source_phase_coordinate",
        "unresolved_microvascular_pressure_function_or_uncovered_extent",
    ]
    event_parts = [
        "actual_patient_bolus_trial_or_test_source_identity",
        "every_observed_event_frame_time_and_temporal_boundary",
        "each_resolved_bolus_wall_lumen_or_leak_interface",
        "source_order_rate_posture_calibration_and_missing_frames",
        "every_actual_recorded_response_or_comparison",
        "unobserved_time_or_unresolved_causal_physiological_mechanism",
    ]
    node_parts = [
        "each_actual_named_region_node_and_component_identity",
        "source_resolved_cortex_hilum_margin_and_capsular_interface",
        "every_resolved_solid_fluid_calcific_or_other_internal_component",
        "each_actual_perinodal_esophageal_airway_vascular_or_other_interface",
        "actual_map_source_axes_phase_comparison_and_site",
        "unresolved_microscopic_or_uncovered_nodal_extent",
    ]

    def add(key, steps, side="not_applicable", route=False, event=False, pathology=False, urls=None):
        ident = "esophagus." + side + "_" + key
        parts = event_parts if event else node_parts if "nodes" in key else route_parts if route else shape_parts
        structures.append({
            "id": ident,
            "name": side.replace("_", " ").capitalize() + " " + key.replace("_", " "),
            "tissue_class": "source_esophageal_tissue_route_lesion_or_recorded_event_interface",
            "required_parts": [{"id": ident + "." + part, "name": part.replace("_", " ").capitalize()} for part in parts],
            "laterality": side,
            "modality_scope": ["Radiography", "CT", "MRI"],
            "condition": "Independently instantiate every actual acquired side, segment, layer, gland/duct, neural/vascular/lymphatic branch, pouch/lesion component, connection, variant, treatment and source trial/time. The known group floor does not approve existing media or turn modality permission into source resolution. Endoscopy/EUS, tissue/assays, manometry/FLIP and reflux monitoring are separate identified sources; uncovered microscopic or functional extent remains explicit.",
            "requirement_basis": "full_effective_esophageal_reporting_anatomy_and_actual_source_interfaces",
            "report_refs": [{"checklist_index": index, **guide["checklist"][index]} for index in steps],
            "walkthrough_step_indices": steps,
            "source_urls": urls or [source["url"] for source in SOURCES],
            "requires_site_instantiation": True,
            "context_requirements": {"purpose": "pathology_example" if pathology or event else "anatomical_reference"},
            "requires_actual_temporal_evidence": event,
            "requires_independent_source_layer_review": not event,
        })

    # Every listed wall substructure applies separately at every source-resolved
    # anatomical segment, lesion and actual supplied histological site.
    for segment in ["cervical", "upper_thoracic", "middle_thoracic", "lower_thoracic", "abdominal"]:
        for component in [
            "lumen_and_actual_contents", "mucosal_epithelium_and_luminal_surface",
            "lamina_propria_and_muscularis_mucosae", "submucosa_and_actual_glands_ducts",
            "inner_circular_and_outer_longitudinal_muscularis_propria",
            "adventitia_and_actual_external_attachment", "actual_neural_vascular_and_lymphatic_plexuses",
            "every_actual_lesion_variant_or_treated_component",
        ]:
            add(segment + "_" + component, [0, 1, 2, 3, 4], pathology="lesion" in component)
    for side in ["left", "right"]:
        for key in [
            "pyriform_recess_apex_and_hypopharyngeal_wall",
            "inferior_constrictor_thyropharyngeal_and_cricopharyngeal_components",
            "thyroid_parathyroid_and_cervical_soft_tissue_interfaces",
            "tracheoesophageal_groove_and_actual_fascial_interfaces",
            "pleural_mediastinal_and_pulmonary_interfaces",
            "bronchial_wall_lumen_and_esophageal_contact",
            "diaphragmatic_crus_hiatal_margin_and_actual_attachments",
        ]:
            add(key, [0, 1, 3, 4], side)
        for key in [
            "vagus_and_each_actual_esophageal_branch",
            "recurrent_or_nonrecurrent_laryngeal_nerve_and_connections",
            "sympathetic_and_actual_autonomic_route_interfaces",
            "inferior_thyroid_and_each_actual_esophageal_arterial_branch",
            "bronchial_and_each_actual_esophageal_arterial_branch",
            "subclavian_carotid_and_each_actual_arch_variant_connection",
            "jugular_brachiocephalic_and_superior_caval_connections",
            "pulmonary_arterial_venous_and_actual_variant_routes",
            "each_actual_paraeosophageal_venous_connection",
        ]:
            add(key, [1, 3, 4], side, route=True)
        for key in [
            "actual_cervical_recurrent_nerve_chain_and_supraclavicular_nodes",
            "actual_upper_paratracheal_and_paraeosophageal_nodes",
            "actual_hilar_bronchial_and_lower_mediastinal_nodes",
            "actual_perigastric_left_gastric_and_coeliac_nodes",
            "every_actual_lateral_pouch_wall_neck_and_content",
            "every_actual_extrinsic_mass_or_invasive_tissue_interface",
            "every_actual_lateral_leak_fistula_collection_or_repair",
        ]:
            add(key, [1, 2, 3, 4], side, pathology=True)
    for key in [
        "postcricoid_wall_and_pharyngoesophageal_lumen",
        "upper_esophageal_segment_and_actual_sphincter_tissue_interfaces",
        "posterior_thyropharyngeal_cricopharyngeal_and_pouch_origin_interfaces",
        "cervical_spine_prevertebral_fascia_and_actual_osteophyte_contact",
        "tracheal_wall_membrane_lumen_and_carinal_interfaces",
        "subcarinal_nodes_and_every_actual_node_component",
        "left_atrial_pericardial_and_cardiac_interfaces",
        "aortic_arch_descending_aorta_and_every_esophageal_branch",
        "azygos_hemiazygos_accessory_hemiazygos_and_connections",
        "thoracic_duct_and_every_actual_lymphatic_connection",
        "esophageal_venous_plexus_left_gastric_and_portal_connections",
        "distal_vestibule_and_actual_intrinsic_EGJ_muscle_interfaces",
        "anterior_posterior_vagal_trunks_and_actual_gastric_branches",
        "left_gastric_short_gastric_and_inferior_phrenic_arterial_branches",
        "diaphragmatic_hiatus_and_phrenoesophageal_ligament_interfaces",
        "actual_abdominal_peritoneal_serosal_and_lesser_omental_interfaces",
        "gastric_cardia_fundus_folds_and_actual_squamocolumnar_transition",
        "actual_gastrophrenic_gastrosplenic_and_other_gastric_attachments",
        "covered_liver_pancreatic_splenic_and_abdominal_vascular_interfaces",
        "every_herniated_gastric_component_and_covered_other_content",
        "each_actual_hernia_sac_neck_attachment_and_diaphragmatic_interface",
        "each_actual_gastric_rotation_axis_and_obstruction_interface",
        "each_actual_A_ring_B_ring_web_or_bar_component",
        "each_actual_stricture_site_length_wall_and_minimum_lumen",
        "each_actual_Zenker_or_other_pouch_neck_wall_content_and_reentry",
        "each_actual_duplication_wall_lumen_and_communication",
        "each_actual_pseudodiverticular_gland_duct_and_mucosal_orifice",
        "every_actual_mucosal_plaque_erosion_ulcer_or_surface_lesion",
        "every_actual_intraluminal_polyp_stalk_or_foreign_material",
        "every_actual_intramural_mass_layer_and_exophytic_component",
        "every_actual_infiltrative_lesion_and_adjacent_tissue_interface",
        "each_actual_varix_wall_lumen_and_venous_route",
        "every_actual_intramural_hematoma_or_dissection_lumen_and_septum",
        "every_actual_mucosal_tear_or_full_wall_defect",
        "each_actual_airway_esophageal_or_other_fistulous_connection",
        "every_actual_extraluminal_air_fluid_contrast_and_collection_route",
        "each_actual_mediastinal_pleural_pulmonary_or_abdominal_spread",
        "each_actual_anastomosis_conduit_and_reconstructed_route",
        "each_actual_myotomy_fundoplication_or_other_treated_interface",
        "each_actual_stent_tube_drain_and_device_to_tissue_connection",
        "each_encountered_unlisted_segment_branch_variant_lesion_or_repair",
    ]:
        add(key, [0, 1, 2, 3, 4], route=any(word in key for word in ["arterial", "aorta", "azygos", "venous_plexus", "thoracic_duct", "vagal"]), pathology=any(word in key for word in ["actual_hernia", "ring", "stricture", "pouch", "duplication", "pseudodiverticular", "lesion", "mass", "varix", "hematoma", "tear", "defect", "fistulous", "extraluminal", "spread", "anastomosis", "treated", "stent"]))
    for key in [
        "each_actual_recorded_bolus_volume_consistency_and_delivery",
        "each_observed_upper_esophageal_opening_and_passage",
        "each_recorded_primary_secondary_or_nonpropulsive_wave_and_clearance",
        "each_actual_timed_column_acquisition_and_retention_boundary",
        "each_actual_tested_tablet_passage_or_retention",
        "each_observed_reflux_event_and_obtained_proximal_extent",
        "each_actual_recorded_position_manoeuvre_or_distension_response",
        "each_observed_hernia_EGJ_or_gastric_configuration_change",
        "each_actual_pouch_filling_emptying_or_reentry_event",
        "each_acquired_leak_or_fistula_contrast_passage_event",
        "each_actual_recorded_aspiration_or_airway_entry_if_covered",
        "each_actual_source_comparison_or_post_treatment_response",
    ]:
        add(key, [0, 2, 3, 4], event=True)
    item = {
        "investigation_id": INV,
        "module_id": ref["investigation"]["module_id"],
        "title": "Every acquired esophageal wall lumen branch lesion hiatal and recorded temporal interface",
        "scope_status": "expanded_draft_requires_independent_esophageal_anatomical_and_temporal_review",
        "modality_scope": ["Radiography", "CT", "MRI"],
        "sources": [dict(source, reviewed_at=DATE, review_status="primary_reporting_context_no_graphics_or_cine_reused") for source in SOURCES],
        "reporting_checklist": guide["checklist"],
        "reporting_template_sections": guide["template_sections"],
        "structures": structures,
        "expansion_rules": [
            "Independently instantiate every actual segment, side, wall layer, gland/duct, nerve/vessel/lymphatic branch, node, lesion/pouch/hernia component, communication, variant and repair. These groups are a known floor, not a closed list of all possible source anatomy.",
            "Each listed parent group requires every actual internal component and source boundary/interface separately. A whole-esophagus segmentation, smooth tube, generic hiatal model or one published example is not full native anatomy or current-patient coverage.",
            "Preserve source patient, site, laterality, modality/projection/sequence/phase, spatial calibration, actual trial/time and treatment provenance. A shared module does not make swallowing screening and dedicated esophageal imaging the same examination.",
            "Microscopic layers, glands, plexuses and tiny branches remain required but unproven until appropriate matched anatomical sources and independent review support them; imaging modality permission never implies their resolution.",
        ],
        "source_scope_issues": [
            "Current partial swallowing orientation, selected figures and source whole-esophagus meshes do not supply all native wall layers, mucosal/glandular, neural/vascular/lymphatic, hiatal or lesion interfaces.",
            "The older Radiology Assistant source vocabulary and morphology are reporting context rather than current motility classification, microbiology, Barrett histology, stage or a universal clinical-action rule.",
            "VFSS screening, dedicated fluoroscopic esophagram and cross-sectional imaging have different acquired scope; endoscopy/EUS, pathological tissue and calibrated physiological tests remain separately identified evidence.",
            "No source graphic or cine is reused and no existing structure, asset or clinical coverage is approved by this draft.",
        ],
        "functional_evidence_requirements": [
            "Source bolus clearance, nonpropulsive contractions, reflux, opening, pouch filling/emptying, changing hiatal relationships and leak passage require their actual recorded frames/times, order/rate/gaps, projections/posture, bolus and calibration; a still or animated geometric model does not supply the events.",
            "For timed retention preserve the actual volume/consistency, ingestion/time-zero convention, recorded timepoints and position. Different source protocols cannot inherit diagnostic thresholds or exclude disease from an unobserved interval.",
            "Pressure, sphincter relaxation, coordinated contractility or motility subtype requires actual applicable HRM/HRIM or other relevant physiology with clinical context. Chicago v4.0 assumes normal foregut anatomy without prior invasive foregut intervention or large/paraesophageal hernias; mechanical obstruction and protocol applicability need review. An EGJ shape or postoperative course is not automatically a classified motility disorder.",
            "Endoscopic/EUS layers or mucosal findings, biopsy/pathology/metaplasia/dysplasia/organisms and supplied clinical diagnoses are separate source evidence. No smooth taper, plaque, ulcer, calcification or reticular pattern independently provides those identities or treatment eligibility.",
            "Observed barium reflux or a hernia alone does not diagnose GERD; relevant endoscopic or reflux-monitoring and clinical evidence stays identified. FLIP distensibility, pH/impedance, vessel flow and neural or muscle physiology are not static model measurements.",
            "A limited negative leak examination does not exclude every perforation, and an unrecorded aspiration response is not absent aspiration. Acute management, tumour staging, resectability or postoperative success requires appropriate acquired extent and actual supplied clinical/pathological/temporal context.",
        ],
        "clinical_validation_status": "draft_requires_esophageal_radiologist_anatomist_gastroenterology_and_relevant_swallowing_or_surgical_review",
    }
    return guide, node, item, removed


def build():
    """Explicitly apply the draft to the three existing global data stores."""
    ref = catalog.detail(Curriculum(), catalog.resolve(INV))["radiology_reference"]
    steps_path = ROOT / "data/radiology/reporting-steps/chest.json"
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
