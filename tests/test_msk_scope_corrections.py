"""Keep source-scoped MSK reports honest without shrinking anatomical requirements."""
import hashlib
import json
from pathlib import Path

import pytest

from primer.curriculum import Curriculum
from primer import radiology_catalog

ROOT = Path(__file__).resolve().parents[1]
IDS = ("ra.thoracolumbar-fractures", "ra.ankle-fractures")
WRIST_IDS = ("ra.wrist-instability", "ra.wrist-fractures")
AUDITED_IDS = IDS + WRIST_IDS
# Independent pre-correction minimum. Additions are allowed; removing an older
# structure/subpart requires an explicit scope review, not an easier asset gate.
MINIMUM_SCOPE = {'ra.ankle-fractures': {'ankle.distal_tibia': ['ankle.distal_tibia.medial_malleolus',
                                               'ankle.distal_tibia.posterior_malleolus',
                                               'ankle.distal_tibia.anterior_tibial_lip',
                                               'ankle.distal_tibia.plafond',
                                               'ankle.distal_tibia.fibular_incisura',
                                               'ankle.distal_tibia.distal_physis_if_open',
                                               'ankle.distal_tibia.cortex',
                                               'ankle.distal_tibia.marrow'],
                        'ankle.fibula': ['ankle.fibula.lateral_malleolus',
                                         'ankle.fibula.syndesmotic_level',
                                         'ankle.fibula.proximal_shaft_if_included',
                                         'ankle.fibula.fibular_head_if_included',
                                         'ankle.fibula.cortex',
                                         'ankle.fibula.marrow'],
                        'ankle.talus': ['ankle.talus.medial_dome',
                                        'ankle.talus.lateral_dome',
                                        'ankle.talus.neck',
                                        'ankle.talus.body',
                                        'ankle.talus.head',
                                        'ankle.talus.lateral_process',
                                        'ankle.talus.posterior_process',
                                        'ankle.talus.subtalar_facets'],
                        'ankle.calcaneus': ['ankle.calcaneus.posterior_facet',
                                            'ankle.calcaneus.middle_facet',
                                            'ankle.calcaneus.anterior_facet',
                                            'ankle.calcaneus.sustentaculum_tali',
                                            'ankle.calcaneus.anterior_process',
                                            'ankle.calcaneus.posterior_tuberosity',
                                            'ankle.calcaneus.cortex',
                                            'ankle.calcaneus.marrow'],
                        'ankle.navicular': ['ankle.navicular.body',
                                            'ankle.navicular.tuberosity',
                                            'ankle.navicular.talonavicular_surface',
                                            'ankle.navicular.cortex',
                                            'ankle.navicular.marrow'],
                        'ankle.tibiotalar_joint': ['ankle.tibiotalar_joint.medial_relationship',
                                                   'ankle.tibiotalar_joint.lateral_relationship',
                                                   'ankle.tibiotalar_joint.anterior_relationship',
                                                   'ankle.tibiotalar_joint.posterior_relationship'],
                        'ankle.distal_tibiofibular_syndesmosis': ['ankle.distal_tibiofibular_syndesmosis.medial_relationship',
                                                                  'ankle.distal_tibiofibular_syndesmosis.lateral_relationship',
                                                                  'ankle.distal_tibiofibular_syndesmosis.anterior_relationship',
                                                                  'ankle.distal_tibiofibular_syndesmosis.posterior_relationship'],
                        'ankle.anterior_inferior_tibiofibular_ligament': ['ankle.anterior_inferior_tibiofibular_ligament.origins',
                                                                          'ankle.anterior_inferior_tibiofibular_ligament.course',
                                                                          'ankle.anterior_inferior_tibiofibular_ligament.insertions'],
                        'ankle.posterior_inferior_tibiofibular_ligament': ['ankle.posterior_inferior_tibiofibular_ligament.origins',
                                                                           'ankle.posterior_inferior_tibiofibular_ligament.course',
                                                                           'ankle.posterior_inferior_tibiofibular_ligament.insertions'],
                        'ankle.interosseous_ligament': ['ankle.interosseous_ligament.origins',
                                                        'ankle.interosseous_ligament.course',
                                                        'ankle.interosseous_ligament.insertions'],
                        'ankle.interosseous_membrane': ['ankle.interosseous_membrane.origins',
                                                        'ankle.interosseous_membrane.course',
                                                        'ankle.interosseous_membrane.insertions'],
                        'ankle.deltoid_ligament': ['ankle.deltoid_ligament.origins',
                                                   'ankle.deltoid_ligament.course',
                                                   'ankle.deltoid_ligament.insertions'],
                        'ankle.anterior_talofibular_ligament': ['ankle.anterior_talofibular_ligament.origins',
                                                                'ankle.anterior_talofibular_ligament.course',
                                                                'ankle.anterior_talofibular_ligament.insertions'],
                        'ankle.calcaneofibular_ligament': ['ankle.calcaneofibular_ligament.origins',
                                                           'ankle.calcaneofibular_ligament.course',
                                                           'ankle.calcaneofibular_ligament.insertions'],
                        'ankle.talar_and_tibial_articular_cartilage': ['ankle.talar_and_tibial_articular_cartilage.talar_dome_cartilage',
                                                                       'ankle.talar_and_tibial_articular_cartilage.tibial_plafond_cartilage'],
                        'foot.cuboid': ['foot.cuboid.body',
                                        'foot.cuboid.calcaneocuboid_surface',
                                        'foot.cuboid.fourth_and_fifth_tarsometatarsal_surfaces'],
                        'foot.medial_cuneiform': ['foot.medial_cuneiform.articular_surfaces',
                                                  'foot.medial_cuneiform.cortex',
                                                  'foot.medial_cuneiform.marrow'],
                        'foot.intermediate_cuneiform': ['foot.intermediate_cuneiform.articular_surfaces',
                                                        'foot.intermediate_cuneiform.cortex',
                                                        'foot.intermediate_cuneiform.marrow'],
                        'foot.lateral_cuneiform': ['foot.lateral_cuneiform.articular_surfaces',
                                                   'foot.lateral_cuneiform.cortex',
                                                   'foot.lateral_cuneiform.marrow'],
                        'foot.metatarsal_1': ['foot.metatarsal_1.base',
                                              'foot.metatarsal_1.shaft',
                                              'foot.metatarsal_1.neck',
                                              'foot.metatarsal_1.head'],
                        'foot.metatarsal_2': ['foot.metatarsal_2.base',
                                              'foot.metatarsal_2.shaft',
                                              'foot.metatarsal_2.neck',
                                              'foot.metatarsal_2.head'],
                        'foot.metatarsal_3': ['foot.metatarsal_3.base',
                                              'foot.metatarsal_3.shaft',
                                              'foot.metatarsal_3.neck',
                                              'foot.metatarsal_3.head'],
                        'foot.metatarsal_4': ['foot.metatarsal_4.base',
                                              'foot.metatarsal_4.shaft',
                                              'foot.metatarsal_4.neck',
                                              'foot.metatarsal_4.head'],
                        'foot.metatarsal_5': ['foot.metatarsal_5.base',
                                              'foot.metatarsal_5.shaft',
                                              'foot.metatarsal_5.neck',
                                              'foot.metatarsal_5.head'],
                        'foot.tarsometatarsal_joints': ['foot.tarsometatarsal_joints.first_tmt_joint',
                                                        'foot.tarsometatarsal_joints.second_tmt_joint',
                                                        'foot.tarsometatarsal_joints.third_tmt_joint',
                                                        'foot.tarsometatarsal_joints.fourth_tmt_joint',
                                                        'foot.tarsometatarsal_joints.fifth_tmt_joint'],
                        'foot.lisfranc_ligament_complex': ['foot.lisfranc_ligament_complex.dorsal_component',
                                                           'foot.lisfranc_ligament_complex.interosseous_component',
                                                           'foot.lisfranc_ligament_complex.plantar_component'],
                        'ankle.periarticular_soft_tissues': ['ankle.periarticular_soft_tissues.medial',
                                                             'ankle.periarticular_soft_tissues.lateral',
                                                             'ankle.periarticular_soft_tissues.anterior',
                                                             'ankle.periarticular_soft_tissues.posterior']},
 'ra.thoracolumbar-fractures': {'thoracolumbar.each_imaged_vertebra': ['thoracolumbar.each_imaged_vertebra.vertebral_body_anterior_wall',
                                                                       'thoracolumbar.each_imaged_vertebra.vertebral_body_posterior_wall',
                                                                       'thoracolumbar.each_imaged_vertebra.superior_endplate',
                                                                       'thoracolumbar.each_imaged_vertebra.inferior_endplate',
                                                                       'thoracolumbar.each_imaged_vertebra.left_pedicle',
                                                                       'thoracolumbar.each_imaged_vertebra.right_pedicle',
                                                                       'thoracolumbar.each_imaged_vertebra.left_lamina',
                                                                       'thoracolumbar.each_imaged_vertebra.right_lamina',
                                                                       'thoracolumbar.each_imaged_vertebra.spinous_process',
                                                                       'thoracolumbar.each_imaged_vertebra.left_transverse_process',
                                                                       'thoracolumbar.each_imaged_vertebra.right_transverse_process',
                                                                       'thoracolumbar.each_imaged_vertebra.superior_articular_processes',
                                                                       'thoracolumbar.each_imaged_vertebra.inferior_articular_processes'],
                                'thoracolumbar.intervertebral_disc': ['thoracolumbar.intervertebral_disc.annulus_fibrosus',
                                                                      'thoracolumbar.intervertebral_disc.nucleus_pulposus',
                                                                      'thoracolumbar.intervertebral_disc.superior_endplate_interface',
                                                                      'thoracolumbar.intervertebral_disc.inferior_endplate_interface'],
                                'thoracolumbar.supraspinous_ligament': ['thoracolumbar.supraspinous_ligament.attachments',
                                                                        'thoracolumbar.supraspinous_ligament.intersegmental_course'],
                                'thoracolumbar.interspinous_ligament': ['thoracolumbar.interspinous_ligament.attachments',
                                                                        'thoracolumbar.interspinous_ligament.intersegmental_course'],
                                'thoracolumbar.left_ligamentum_flavum': ['thoracolumbar.left_ligamentum_flavum.attachments',
                                                                         'thoracolumbar.left_ligamentum_flavum.intersegmental_course'],
                                'thoracolumbar.right_ligamentum_flavum': ['thoracolumbar.right_ligamentum_flavum.attachments',
                                                                          'thoracolumbar.right_ligamentum_flavum.intersegmental_course'],
                                'thoracolumbar.left_facet_capsule': ['thoracolumbar.left_facet_capsule.attachments',
                                                                     'thoracolumbar.left_facet_capsule.intersegmental_course'],
                                'thoracolumbar.right_facet_capsule': ['thoracolumbar.right_facet_capsule.attachments',
                                                                      'thoracolumbar.right_facet_capsule.intersegmental_course'],
                                'thoracolumbar.anterior_longitudinal_ligament': ['thoracolumbar.anterior_longitudinal_ligament.attachments',
                                                                                 'thoracolumbar.anterior_longitudinal_ligament.intersegmental_course'],
                                'thoracolumbar.posterior_longitudinal_ligament': ['thoracolumbar.posterior_longitudinal_ligament.attachments',
                                                                                  'thoracolumbar.posterior_longitudinal_ligament.intersegmental_course'],
                                'thoracolumbar.spinal_cord': ['thoracolumbar.spinal_cord.covered_cranial_extent',
                                                              'thoracolumbar.spinal_cord.covered_caudal_extent',
                                                              'thoracolumbar.spinal_cord.compression_interface'],
                                'thoracolumbar.conus_medullaris': ['thoracolumbar.conus_medullaris.covered_cranial_extent',
                                                                   'thoracolumbar.conus_medullaris.covered_caudal_extent',
                                                                   'thoracolumbar.conus_medullaris.compression_interface'],
                                'thoracolumbar.cauda_equina': ['thoracolumbar.cauda_equina.covered_cranial_extent',
                                                               'thoracolumbar.cauda_equina.covered_caudal_extent',
                                                               'thoracolumbar.cauda_equina.compression_interface'],
                                'thoracolumbar.spinal_nerve_roots': ['thoracolumbar.spinal_nerve_roots.left_traversing_root',
                                                                     'thoracolumbar.spinal_nerve_roots.right_traversing_root',
                                                                     'thoracolumbar.spinal_nerve_roots.left_exiting_root',
                                                                     'thoracolumbar.spinal_nerve_roots.right_exiting_root'],
                                'thoracolumbar.spinal_canal_and_foramina': ['thoracolumbar.spinal_canal_and_foramina.central_canal',
                                                                            'thoracolumbar.spinal_canal_and_foramina.left_lateral_recess',
                                                                            'thoracolumbar.spinal_canal_and_foramina.right_lateral_recess',
                                                                            'thoracolumbar.spinal_canal_and_foramina.left_neural_foramen',
                                                                            'thoracolumbar.spinal_canal_and_foramina.right_neural_foramen'],
                                'thoracolumbar.epidural_compartment': ['thoracolumbar.epidural_compartment.anterior_epidural_space',
                                                                       'thoracolumbar.epidural_compartment.posterior_epidural_space',
                                                                       'thoracolumbar.epidural_compartment.lateral_epidural_spaces'],
                                'thoracolumbar.paraspinal_muscles_and_soft_tissues': ['thoracolumbar.paraspinal_muscles_and_soft_tissues.named_multifidus_erector_spinae_components',
                                                                                      'thoracolumbar.paraspinal_muscles_and_soft_tissues.psoas_if_covered',
                                                                                      'thoracolumbar.paraspinal_muscles_and_soft_tissues.prevertebral_tissues',
                                                                                      'thoracolumbar.paraspinal_muscles_and_soft_tissues.intermuscular_planes']},
 'ra.wrist-instability': {'wrist.scaphoid': ['wrist.scaphoid.proximal_articular_contour',
                                             'wrist.scaphoid.distal_articular_contour',
                                             'wrist.scaphoid.cortex',
                                             'wrist.scaphoid.marrow',
                                             'wrist.scaphoid.proximal_pole',
                                             'wrist.scaphoid.waist',
                                             'wrist.scaphoid.distal_pole',
                                             'wrist.scaphoid.tubercle'],
                          'wrist.lunate': ['wrist.lunate.proximal_articular_contour',
                                           'wrist.lunate.distal_articular_contour',
                                           'wrist.lunate.cortex',
                                           'wrist.lunate.marrow'],
                          'wrist.triquetrum': ['wrist.triquetrum.proximal_articular_contour',
                                               'wrist.triquetrum.distal_articular_contour',
                                               'wrist.triquetrum.cortex',
                                               'wrist.triquetrum.marrow'],
                          'wrist.pisiform': ['wrist.pisiform.proximal_articular_contour',
                                             'wrist.pisiform.distal_articular_contour',
                                             'wrist.pisiform.cortex',
                                             'wrist.pisiform.marrow'],
                          'wrist.trapezium': ['wrist.trapezium.proximal_articular_contour',
                                              'wrist.trapezium.distal_articular_contour',
                                              'wrist.trapezium.cortex',
                                              'wrist.trapezium.marrow'],
                          'wrist.trapezoid': ['wrist.trapezoid.proximal_articular_contour',
                                              'wrist.trapezoid.distal_articular_contour',
                                              'wrist.trapezoid.cortex',
                                              'wrist.trapezoid.marrow'],
                          'wrist.capitate': ['wrist.capitate.proximal_articular_contour',
                                             'wrist.capitate.distal_articular_contour',
                                             'wrist.capitate.cortex',
                                             'wrist.capitate.marrow'],
                          'wrist.hamate': ['wrist.hamate.proximal_articular_contour',
                                           'wrist.hamate.distal_articular_contour',
                                           'wrist.hamate.cortex',
                                           'wrist.hamate.marrow',
                                           'wrist.hamate.hook'],
                          'wrist.distal_radius': ['wrist.distal_radius.radial_styloid',
                                                  'wrist.distal_radius.scaphoid_facet',
                                                  'wrist.distal_radius.lunate_facet',
                                                  'wrist.distal_radius.sigmoid_notch',
                                                  'wrist.distal_radius.dorsal_rim',
                                                  'wrist.distal_radius.volar_rim',
                                                  'wrist.distal_radius.metaphysis',
                                                  'wrist.distal_radius.physis_if_open'],
                          'wrist.distal_ulna': ['wrist.distal_ulna.ulnar_head',
                                                'wrist.distal_ulna.ulnar_styloid_tip',
                                                'wrist.distal_ulna.ulnar_styloid_base',
                                                'wrist.distal_ulna.distal_physis_if_open'],
                          'wrist.radiocarpal_joint': ['wrist.radiocarpal_joint.opposing_articular_contours',
                                                      'wrist.radiocarpal_joint.joint_gap_and_alignment'],
                          'wrist.distal_radioulnar_joint': ['wrist.distal_radioulnar_joint.opposing_articular_contours',
                                                            'wrist.distal_radioulnar_joint.joint_gap_and_alignment'],
                          'wrist.scapholunate_interval': ['wrist.scapholunate_interval.opposing_articular_contours',
                                                          'wrist.scapholunate_interval.joint_gap_and_alignment'],
                          'wrist.lunotriquetral_interval': ['wrist.lunotriquetral_interval.opposing_articular_contours',
                                                            'wrist.lunotriquetral_interval.joint_gap_and_alignment'],
                          'wrist.capitolunate_joint': ['wrist.capitolunate_joint.opposing_articular_contours',
                                                       'wrist.capitolunate_joint.joint_gap_and_alignment'],
                          'wrist.scaphocapitate_joint': ['wrist.scaphocapitate_joint.opposing_articular_contours',
                                                         'wrist.scaphocapitate_joint.joint_gap_and_alignment'],
                          'wrist.scaphotrapeziotrapezoid_joint': ['wrist.scaphotrapeziotrapezoid_joint.opposing_articular_contours',
                                                                  'wrist.scaphotrapeziotrapezoid_joint.joint_gap_and_alignment'],
                          'wrist.triquetrohamate_joint': ['wrist.triquetrohamate_joint.opposing_articular_contours',
                                                          'wrist.triquetrohamate_joint.joint_gap_and_alignment'],
                          'wrist.carpometacarpal_joints': ['wrist.carpometacarpal_joints.opposing_articular_contours',
                                                           'wrist.carpometacarpal_joints.joint_gap_and_alignment'],
                          'wrist.scapholunate_interosseous_ligament': [],
                          'wrist.lunotriquetral_interosseous_ligament': [],
                          'wrist.triangular_fibrocartilage_complex': [],
                          'wrist.periarticular_soft_tissues': ['wrist.periarticular_soft_tissues.dorsal',
                                                               'wrist.periarticular_soft_tissues.volar',
                                                               'wrist.periarticular_soft_tissues.radial',
                                                               'wrist.periarticular_soft_tissues.ulnar'],
                          'wrist.gilula_arc_landmarks': ['wrist.gilula_arc_landmarks.arc_i_proximal_proximal_row_contours',
                                                         'wrist.gilula_arc_landmarks.arc_ii_distal_proximal_row_contours',
                                                         'wrist.gilula_arc_landmarks.arc_iii_proximal_capitate_hamate_contours'],
                          'wrist.carpal_axis_landmarks': ['wrist.carpal_axis_landmarks.scaphoid_axis',
                                                          'wrist.carpal_axis_landmarks.lunate_axis',
                                                          'wrist.carpal_axis_landmarks.capitate_axis',
                                                          'wrist.carpal_axis_landmarks.distal_radial_axis']},
 'ra.wrist-fractures': {'wrist.scaphoid': ['wrist.scaphoid.proximal_articular_contour',
                                           'wrist.scaphoid.distal_articular_contour',
                                           'wrist.scaphoid.cortex',
                                           'wrist.scaphoid.marrow',
                                           'wrist.scaphoid.proximal_pole',
                                           'wrist.scaphoid.waist',
                                           'wrist.scaphoid.distal_pole',
                                           'wrist.scaphoid.tubercle'],
                        'wrist.lunate': ['wrist.lunate.proximal_articular_contour',
                                         'wrist.lunate.distal_articular_contour',
                                         'wrist.lunate.cortex',
                                         'wrist.lunate.marrow'],
                        'wrist.triquetrum': ['wrist.triquetrum.proximal_articular_contour',
                                             'wrist.triquetrum.distal_articular_contour',
                                             'wrist.triquetrum.cortex',
                                             'wrist.triquetrum.marrow'],
                        'wrist.pisiform': ['wrist.pisiform.proximal_articular_contour',
                                           'wrist.pisiform.distal_articular_contour',
                                           'wrist.pisiform.cortex',
                                           'wrist.pisiform.marrow'],
                        'wrist.trapezium': ['wrist.trapezium.proximal_articular_contour',
                                            'wrist.trapezium.distal_articular_contour',
                                            'wrist.trapezium.cortex',
                                            'wrist.trapezium.marrow'],
                        'wrist.trapezoid': ['wrist.trapezoid.proximal_articular_contour',
                                            'wrist.trapezoid.distal_articular_contour',
                                            'wrist.trapezoid.cortex',
                                            'wrist.trapezoid.marrow'],
                        'wrist.capitate': ['wrist.capitate.proximal_articular_contour',
                                           'wrist.capitate.distal_articular_contour',
                                           'wrist.capitate.cortex',
                                           'wrist.capitate.marrow'],
                        'wrist.hamate': ['wrist.hamate.proximal_articular_contour',
                                         'wrist.hamate.distal_articular_contour',
                                         'wrist.hamate.cortex',
                                         'wrist.hamate.marrow',
                                         'wrist.hamate.hook'],
                        'wrist.distal_radius': ['wrist.distal_radius.radial_styloid',
                                                'wrist.distal_radius.scaphoid_facet',
                                                'wrist.distal_radius.lunate_facet',
                                                'wrist.distal_radius.sigmoid_notch',
                                                'wrist.distal_radius.dorsal_rim',
                                                'wrist.distal_radius.volar_rim',
                                                'wrist.distal_radius.metaphysis',
                                                'wrist.distal_radius.physis_if_open'],
                        'wrist.distal_ulna': ['wrist.distal_ulna.ulnar_head',
                                              'wrist.distal_ulna.ulnar_styloid_tip',
                                              'wrist.distal_ulna.ulnar_styloid_base',
                                              'wrist.distal_ulna.distal_physis_if_open'],
                        'wrist.radiocarpal_joint': ['wrist.radiocarpal_joint.opposing_articular_contours',
                                                    'wrist.radiocarpal_joint.joint_gap_and_alignment'],
                        'wrist.distal_radioulnar_joint': ['wrist.distal_radioulnar_joint.opposing_articular_contours',
                                                          'wrist.distal_radioulnar_joint.joint_gap_and_alignment'],
                        'wrist.scapholunate_interval': ['wrist.scapholunate_interval.opposing_articular_contours',
                                                        'wrist.scapholunate_interval.joint_gap_and_alignment'],
                        'wrist.lunotriquetral_interval': ['wrist.lunotriquetral_interval.opposing_articular_contours',
                                                          'wrist.lunotriquetral_interval.joint_gap_and_alignment'],
                        'wrist.capitolunate_joint': ['wrist.capitolunate_joint.opposing_articular_contours',
                                                     'wrist.capitolunate_joint.joint_gap_and_alignment'],
                        'wrist.scaphocapitate_joint': ['wrist.scaphocapitate_joint.opposing_articular_contours',
                                                       'wrist.scaphocapitate_joint.joint_gap_and_alignment'],
                        'wrist.scaphotrapeziotrapezoid_joint': ['wrist.scaphotrapeziotrapezoid_joint.opposing_articular_contours',
                                                                'wrist.scaphotrapeziotrapezoid_joint.joint_gap_and_alignment'],
                        'wrist.triquetrohamate_joint': ['wrist.triquetrohamate_joint.opposing_articular_contours',
                                                        'wrist.triquetrohamate_joint.joint_gap_and_alignment'],
                        'wrist.carpometacarpal_joints': ['wrist.carpometacarpal_joints.opposing_articular_contours',
                                                         'wrist.carpometacarpal_joints.joint_gap_and_alignment'],
                        'wrist.scapholunate_interosseous_ligament': [],
                        'wrist.lunotriquetral_interosseous_ligament': [],
                        'wrist.triangular_fibrocartilage_complex': [],
                        'wrist.periarticular_soft_tissues': ['wrist.periarticular_soft_tissues.dorsal',
                                                             'wrist.periarticular_soft_tissues.volar',
                                                             'wrist.periarticular_soft_tissues.radial',
                                                             'wrist.periarticular_soft_tissues.ulnar']}}


@pytest.fixture(scope="module")
def curriculum():
    return Curriculum()


def reference(curriculum, identifier):
    return radiology_catalog.detail(curriculum, radiology_catalog.resolve(identifier))["radiology_reference"]


def combined_text(rows):
    return "\n".join(row["body"] for row in rows).lower()


def test_thoracolumbar_report_is_trauma_scoped_not_a_degenerative_disc_report(curriculum):
    ref = reference(curriculum, IDS[0])
    guide = ref["reporting"]
    classification = guide["classification"]
    assert "AO Spine thoracolumbar" in classification["name"] and "TLICS" in classification["name"]
    assert "disc nomenclature" not in str(classification).lower()
    assert not any("degeneration" in row["heading"].lower() for row in ref["report_templates"][0]["sections"])
    morphology = next(row["body"].lower() for row in guide["template_sections"] if row["heading"] == "FRACTURE MORPHOLOGY")
    for target in ("posterior wall", "superior endplate", "inferior endplate", "pedicles", "laminae", "retropulsion"):
        assert target in morphology
    for target in ("fracture-age evidence", "mri marrow signal [not acquired", "pathological-fracture concern"):
        assert target in morphology
    assert any("aofoundation.org/spine/trauma/thoracolumbar" in source["url"] for source in guide["sources"])
    assert all("cervical-injury" not in source["url"] and "lumbar-disc" not in source["url"] for source in guide["sources"])


def test_spine_preserves_named_tension_band_components_and_modality_uncertainty(curriculum):
    guide = reference(curriculum, IDS[0])["reporting"]
    posterior = next(row["body"].lower() for row in guide["template_sections"] if row["heading"] == "POSTERIOR TENSION BAND")
    for target in ("supraspinous", "interspinous", "left/right ligamentum flavum", "left/right facet capsules"):
        assert target in posterior
    assert "not acquired" in posterior and "not directly assessed" in posterior and "indeterminate" in posterior
    longitudinal = next(row["body"].lower() for row in guide["template_sections"] if row["heading"] == "DISCS AND LONGITUDINAL LIGAMENTS")
    assert "anterior longitudinal" in longitudinal and "posterior longitudinal" in longitudinal
    assert any("vertical laminar fracture" in text.lower() and "does not" in text.lower() for text in guide["pitfalls"])
    assert any("oedema" in text.lower() and "indeterminate" in text.lower() for text in guide["pitfalls"])


def test_spine_does_not_invent_a_neurological_examination_or_complete_tlics_score(curriculum):
    guide = reference(curriculum, IDS[0])["reporting"]
    inputs = next(row["body"].lower() for row in guide["template_sections"] if row["heading"] == "CLASSIFICATION AND SUPPLIED CLINICAL INPUTS")
    assert "clinical neurological status [not supplied" in inputs
    assert "source and time" in inputs
    assert "not assigned because required inputs are missing" in inputs
    assert "all component inputs documented" in inputs
    assert "imaging alone" in guide["classification"]["summary"]
    assert "automatic treatment recommendation" in guide["classification"]["summary"]
    neural = next(row["body"].lower() for row in guide["template_sections"] if row["heading"] == "CANAL, EPIDURAL SPACE AND NEURAL STRUCTURES")
    assert "ct osseous" in neural and "mri [not acquired" in neural
    for target in ("cord/conus", "cauda equina", "roots"):
        assert target in neural


def test_ankle_radiographs_do_not_promise_direct_ligament_or_cartilage_assessment(curriculum):
    ref = reference(curriculum, IDS[1]); guide = ref["reporting"]
    soft = next(row["detail"].lower() for row in guide["checklist"] if row["label"] == "Soft tissues and modality limits")
    assert "do not grade tendon or ligament discontinuity on radiographs" in soft
    assert "acquired mri or ultrasound" in soft
    assert any("normal" in text.lower() and "does not exclude ligament injury" in text.lower() for text in guide["pitfalls"])
    sections = ref["report_templates"][0]["sections"]
    soft_template = next(row["body"].lower() for row in sections if row["heading"] == "SOFT TISSUES AND SUPPLEMENTAL EXAMINATIONS")
    assert "not directly assessed on radiographs" in soft_template
    assert "supplemental mri/ultrasound [not obtained" in soft_template
    articular = next(row["body"].lower() for row in sections if row["heading"] == "OSSEOUS ARTICULAR EXTENT")
    assert "direct cartilage integrity [not assessed" in articular
    assert "supplemental ct [not obtained" in articular


def test_ankle_retains_foot_proximal_fibular_and_developmental_scope(curriculum):
    guide = reference(curriculum, IDS[1])["reporting"]
    text = combined_text(guide["template_sections"])
    for target in ("posterior malleolus", "proximal fibula [not imaged", "calcaneus/subtalar", "navicular/cuboid/cuneiforms", "metatarsals", "tarsometatarsal", "lisfranc", "physeal/epiphyseal/metaphyseal"):
        assert target in text
    assert "additional foot/hindfoot imaging [not obtained" in text
    assert "weight-bearing" in str(guide).lower() and "stress" in str(guide).lower()
    assert "maturity" in guide["classification"]["name"].lower()
    assert "not general foot-injury" in guide["classification"]["applicability"]


@pytest.mark.parametrize("identifier", AUDITED_IDS)
def test_effective_templates_include_every_scoped_finding_section(curriculum, identifier):
    ref = reference(curriculum, identifier)
    # Important for ankle: its existing explicit report_templates override can
    # otherwise shadow a corrected reporting guide and leave the editor stale.
    sections = {row["heading"]: row["body"] for row in ref["report_templates"][0]["sections"]}
    for row in ref["reporting"]["template_sections"]:
        assert sections[row["heading"]] == row["body"]
    assert ref["report_templates"][0]["sources"] == ref["reporting"]["sources"]
    assert not ref["reporting"].get("criteria_table"), "No unrelated inherited classification table"


def test_correcting_one_investigation_does_not_replace_the_shared_spine_module(curriculum):
    shared = curriculum.node("rad.4.spine-imaging")["radiology_reference"]["reporting"]
    scoped = reference(curriculum, IDS[0])["reporting"]
    assert any("DEGENERATION" in row["heading"] for row in shared["template_sections"])
    assert scoped != shared


@pytest.mark.parametrize("identifier", AUDITED_IDS)
def test_structure_scope_and_report_traceability_survive_the_correction(curriculum, identifier):
    requirements = json.loads((ROOT / "data/radiology/msk-structure-requirements.json").read_text())
    investigation = next(row for row in requirements["investigations"] if row["investigation_id"] == identifier)
    guide = reference(curriculum, identifier)["reporting"]
    actual = {s["id"]: {p["id"] for p in s["required_parts"]} for s in investigation["structures"]}
    for structure_id, part_ids in MINIMUM_SCOPE[identifier].items():
        assert structure_id in actual, "A report correction must not delete required anatomy"
        assert set(part_ids) <= actual[structure_id], "A report correction must not drop subparts"
    snapshot = [{"label": row["label"], "detail": row["detail"]} for row in investigation["reporting_checklist"]]
    assert snapshot == guide["checklist"]
    assert [{"heading": row["heading"], "body": row["body"]} for row in investigation["reporting_template_sections"]] == guide["template_sections"]
    digest = hashlib.sha256(json.dumps(guide["checklist"], sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    assert investigation["reporting_checklist_sha256"] == digest
    for structure in investigation["structures"]:
        for link in structure["report_refs"]:
            expected = guide["checklist"][link["checklist_index"]]
            assert link["label"] == expected["label"] and link["detail"] == expected["detail"]
    if identifier in IDS:
        assert any(row["resolved_at"] == "2026-09-26" for row in investigation["resolved_reporting_defects"])



@pytest.mark.parametrize("identifier,modality", [("ra.wrist-instability", "Radiography"), ("ra.wrist-fractures", "Multimodality")])
def test_wrist_scope_is_not_changed_to_fit_normal_mri_reference_figures(curriculum, identifier, modality):
    item = radiology_catalog.resolve(identifier)
    detail = radiology_catalog.detail(curriculum, item)
    assert detail["modality"] == modality
    ref = detail["radiology_reference"]
    template = ref["report_templates"][0]
    assert "RADIOGRAPHS" in template["title"]
    if identifier == "ra.wrist-instability":
        guide = ref["reporting"]
        assert any("true PA and lateral" in text for text in guide["protocol"])
        assert any("CT or MRI findings" in text and "separately when available" in text for text in guide["protocol"])
        assert any("normal neutral view does not exclude dynamic instability" in text for text in guide["pitfalls"])
    else:
        assert "CT" in template["title"]
        guide = ref["reporting"]
        assert any("CT" in text and "when acquired" in text for text in guide["protocol"])
        assert any("ligamentous avulsion clues" in row["detail"] for row in guide["checklist"])
    # A future direct soft-tissue finding section must name a suitable acquired
    # examination and allow it to remain unassessed. Currently these editors
    # contain radiographic observations, not a fabricated SL/LT/TFCC verdict.
    import re
    for row in template["sections"]:
        text = row["body"].lower()
        named_soft_tissue = re.search(r"\btfcc\b|scapholunate ligament|lunotriquetral ligament|ligament continuity", text)
        integrity_claim = re.search(r"intact|torn|tear|continuity", text)
        if named_soft_tissue and integrity_claim:
            assert re.search(r"mri|mr arthrography|ct arthrography", text)
            assert re.search(r"not acquired|not assessed|not performed|when available|if acquired", text)


@pytest.mark.parametrize("identifier", WRIST_IDS)
def test_wrist_soft_tissue_requirements_keep_their_direct_imaging_conditions(identifier):
    data = json.loads((ROOT / "data/radiology/msk-structure-requirements.json").read_text())
    investigation = next(row for row in data["investigations"] if row["investigation_id"] == identifier)
    structures = {row["id"]: row for row in investigation["structures"]}
    for structure_id in ("wrist.scapholunate_interosseous_ligament", "wrist.lunotriquetral_interosseous_ligament", "wrist.triangular_fibrocartilage_complex"):
        structure = structures[structure_id]
        assert {"MRI", "MR arthrography"} <= set(structure["modality_scope"])
        assert "Radiography" not in structure["modality_scope"]
        assert "indirect alignment/avulsion signs" in structure["condition"]
        assert "not ligament or TFCC fibre continuity" in structure["condition"]
    assert any(issue["code"] == "ligament_visibility" for issue in investigation["source_scope_issues"])
