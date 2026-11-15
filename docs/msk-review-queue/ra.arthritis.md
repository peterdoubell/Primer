# Arthritis imaging

Investigation: `ra.arthritis`

## Reporting obligations

- **Distribution:** Describe symmetry and which joint groups are involved or spared.
- **Cartilage space:** Distinguish uniform from nonuniform joint-space loss.
- **Bone response:** Assess marginal/central erosions, osteophytes, periostitis and mineralisation.
- **Alignment:** Look for subluxation, deformity and ankylosis.
- **Soft tissue and change:** Describe swelling, calcification/tophi and interval structural progression.

## Requirement coverage

| Structure | Clinical image | Schematic | Model | Conditions / modalities |
|---|---|---|---|---|
| Opposing articular surfaces (`site_specific_arthritis.each_examined_joint.opposing_articular_surfaces`) | missing | missing | missing | Within the acquired anatomical coverage. / Radiography, MRI, Ultrasound as actually acquired |
| Joint gap (`site_specific_arthritis.each_examined_joint.joint_gap`) | missing | missing | missing | Within the acquired anatomical coverage. / Radiography, MRI, Ultrasound as actually acquired |
| Alignment (`site_specific_arthritis.each_examined_joint.alignment`) | missing | missing | missing | Within the acquired anatomical coverage. / Radiography, MRI, Ultrasound as actually acquired |
| Marginal bare areas (`site_specific_arthritis.periarticular_bone.marginal_bare_areas`) | missing | missing | missing | Within the acquired anatomical coverage. / Radiography, MRI, Ultrasound as actually acquired |
| Central subchondral surface (`site_specific_arthritis.periarticular_bone.central_subchondral_surface`) | missing | missing | missing | Within the acquired anatomical coverage. / Radiography, MRI, Ultrasound as actually acquired |
| Cortex (`site_specific_arthritis.periarticular_bone.cortex`) | missing | missing | missing | Within the acquired anatomical coverage. / Radiography, MRI, Ultrasound as actually acquired |
| Trabecular bone (`site_specific_arthritis.periarticular_bone.trabecular_bone`) | missing | missing | missing | Within the acquired anatomical coverage. / Radiography, MRI, Ultrasound as actually acquired |
| Periosteum (`site_specific_arthritis.periarticular_bone.periosteum`) | missing | missing | missing | Within the acquired anatomical coverage. / Radiography, MRI, Ultrasound as actually acquired |
| Entheses (`site_specific_arthritis.periarticular_bone.entheses`) | missing | missing | missing | Within the acquired anatomical coverage. / Radiography, MRI, Ultrasound as actually acquired |
| Each opposing surface (`site_specific_arthritis.articular_cartilage.each_opposing_surface`) | missing | missing | missing | Within the acquired anatomical coverage. / Radiography, MRI, Ultrasound as actually acquired |
| Compartmental distribution (`site_specific_arthritis.articular_cartilage.compartmental_distribution`) | missing | missing | missing | Within the acquired anatomical coverage. / Radiography, MRI, Ultrasound as actually acquired |
| Capsular contours (`site_specific_arthritis.synovium_and_capsule.capsular_contours`) | missing | missing | missing | Within the acquired anatomical coverage. / Radiography, MRI, Ultrasound as actually acquired |
| Synovial recesses (`site_specific_arthritis.synovium_and_capsule.synovial_recesses`) | missing | missing | missing | Within the acquired anatomical coverage. / Radiography, MRI, Ultrasound as actually acquired |
| Each named tendon (`site_specific_arthritis.periarticular_tendons_and_entheses.each_named_tendon`) | missing | missing | missing | Within the acquired anatomical coverage. / Radiography, MRI, Ultrasound as actually acquired |
| Enthesis (`site_specific_arthritis.periarticular_tendons_and_entheses.enthesis`) | missing | missing | missing | Within the acquired anatomical coverage. / Radiography, MRI, Ultrasound as actually acquired |
| Tendon sheath (`site_specific_arthritis.periarticular_tendons_and_entheses.tendon_sheath`) | missing | missing | missing | Within the acquired anatomical coverage. / Radiography, MRI, Ultrasound as actually acquired |
| Subcutaneous tissue (`site_specific_arthritis.periarticular_soft_tissues.subcutaneous_tissue`) | missing | missing | missing | Within the acquired anatomical coverage. / Radiography, MRI, Ultrasound as actually acquired |
| Tophus or calcific deposit relationship (`site_specific_arthritis.periarticular_soft_tissues.tophus_or_calcific_deposit_relationship`) | missing | missing | missing | Within the acquired anatomical coverage. / Radiography, MRI, Ultrasound as actually acquired |
| Dens attachment (`arthritis.cervical.left_alar_ligament.dens_attachment`) | missing | missing | missing | When cervical MRI is acquired for the covered atlantoaxial region in arthritis/instability assessment. Do not infer direct ligament integrity from radiographs, alignment alone or a reference model. / MRI |
| Visible course (`arthritis.cervical.left_alar_ligament.visible_course`) | missing | missing | missing | When cervical MRI is acquired for the covered atlantoaxial region in arthritis/instability assessment. Do not infer direct ligament integrity from radiographs, alignment alone or a reference model. / MRI |
| Cranial attachment (`arthritis.cervical.left_alar_ligament.cranial_attachment`) | missing | missing | missing | When cervical MRI is acquired for the covered atlantoaxial region in arthritis/instability assessment. Do not infer direct ligament integrity from radiographs, alignment alone or a reference model. / MRI |
| Dens attachment (`arthritis.cervical.right_alar_ligament.dens_attachment`) | missing | missing | missing | When cervical MRI is acquired for the covered atlantoaxial region in arthritis/instability assessment. Do not infer direct ligament integrity from radiographs, alignment alone or a reference model. / MRI |
| Visible course (`arthritis.cervical.right_alar_ligament.visible_course`) | missing | missing | missing | When cervical MRI is acquired for the covered atlantoaxial region in arthritis/instability assessment. Do not infer direct ligament integrity from radiographs, alignment alone or a reference model. / MRI |
| Cranial attachment (`arthritis.cervical.right_alar_ligament.cranial_attachment`) | missing | missing | missing | When cervical MRI is acquired for the covered atlantoaxial region in arthritis/instability assessment. Do not infer direct ligament integrity from radiographs, alignment alone or a reference model. / MRI |
| Left atlas attachment (`arthritis.cervical.transverse_atlantal_ligament.left_atlas_attachment`) | missing | missing | missing | When cervical MRI is acquired for the covered atlantoaxial region in arthritis/instability assessment. Do not infer direct ligament integrity from radiographs, alignment alone or a reference model. / MRI |
| Visible course (`arthritis.cervical.transverse_atlantal_ligament.visible_course`) | unverified | missing | missing | When cervical MRI is acquired for the covered atlantoaxial region in arthritis/instability assessment. Do not infer direct ligament integrity from radiographs, alignment alone or a reference model. / MRI |
| Right atlas attachment (`arthritis.cervical.transverse_atlantal_ligament.right_atlas_attachment`) | missing | missing | missing | When cervical MRI is acquired for the covered atlantoaxial region in arthritis/instability assessment. Do not infer direct ligament integrity from radiographs, alignment alone or a reference model. / MRI |

## Candidate evidence

### arthritis.cervical.transverse_atlantal_ligament.visible_course — clinical_image

- Asset: `open-cervical-transverse-alar-offiah-fig4`
- Local file: [web/reference-media/msk-open/normal-alar-transverse-offiah-fig4.jpg](../../web/reference-media/msk-open/normal-alar-transverse-offiah-fig4.jpg)
- Artifact SHA-256: `88cb8b673f063f795316b0974aba7e893694eab2a7550600cd99ca12472a3902`
- Review-scope SHA-256: `97a5d9809a195c2b6177aaccb14fd41ee17923eaab83a281b80f8050f92e0a83`
- Source: [Original source](https://link.springer.com/article/10.1007/s13244-016-0530-5)
- Licence: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)
- Recorded rights: commercial use=True; redistribution=True; review status=verified
- Attribution: Curtis Edward Offiah and Emily Day. The craniocervical junction: embryology, anatomy, biomechanics and imaging in blunt trauma. Published online 2016; Insights into Imaging 8:29–47 (2017). DOI 10.1007/s13244-016-0530-5. Figure 4. CC BY 4.0. Original complete PDF-embedded JPEG, unchanged.
- Rights evidence: docs/msk-craniocervical-mri-review.md
- Licence use plan: No separate use plan recorded; inspect the exact licence and rights evidence
- Presentation dependencies: Not separately recorded
- Coverage: {'extent': 'partial', 'basis': 'One coronal image does not establish entire ligament courses, attachment footprints, clinical stability or a 3D model. Individual age and sex are not reported. Alar labels remain visible but no side-specific alar or attachment binding is inferred. The reported 0.8-mm slices do not establish isotropic voxels or fine-fibre resolution.'}
- Selection: {'kind': 'clinical_image', 'panels': ['whole_asset']}
- Source context: {'setting': 'in_vivo', 'laterality': 'bilateral', 'population': {'life_stage': 'unknown'}, 'depicted_state': 'normal_anatomical_reference', 'extent': 'local', 'selected_panels': ['whole_asset'], 'panel_types': {'whole_asset': 'MRI'}, 'panel_states': {'whole_asset': 'normal_anatomical_reference'}, 'anatomical_site': {'region': 'craniocervical_junction'}, 'unknowns': ['Age and sex not reported.'], 'acquisition_note': 'Coronal 3D T2 SPACE, 1.5 T, 0.8-mm slices without gap; single published image, not the source volume.'}
- Limits: One coronal image does not establish entire ligament courses, attachment footprints, clinical stability or a 3D model. Individual age and sex are not reported. Alar labels remain visible but no side-specific alar or attachment binding is inferred. The reported 0.8-mm slices do not establish isotropic voxels or fine-fibre resolution.
- Gate findings: anatomical_review_scope_missing_or_stale, anatomical_review_missing_or_stale, visual_review_scope_missing_or_stale, visual_review_missing_or_stale, high_fidelity_unproven, requirement_coverage_partial

## Scope blockers

- ra.arthritis: site expansion unverified
- ra.arthritis: source scope issue pattern_not_one_joint: classification missing or unknown
- ra.arthritis: generic structure requires site-specific anatomy
