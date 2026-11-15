# Knee source-image acquisition — 26 September 2026

**Six source figures are integrated in `ra.mri-knee`.** Their original files are in `web/reference-media/msk-open/`; this batch brought the image catalog to 54 unique entries. The six figures have seven evidence-ledger records because Wu Figure 1 has separate MRI and schematic claims. All previous 48 catalog entries and 655 ledger records are preserved. Exact captions and rights evidence are in the image manifest and asset attribution file. The original staging package remains at `/tmp/primer-msk-sources/knee-image-batch/`; only its six selected files were copied into the app.

## Source and native-pixel review

| Entry | Native pixels | Visible structure and annotation evidence | Candidate scope |
|---|---:|---|---|
| `open-knee-mcl-layers-bolog-fig14` | 769×1115 | Coronal PD MRI, 20-year-old female patient. Large arrow points to superficial MCL; arrowhead to deep meniscofemoral component; small arrow to deep meniscotibial component. | Three MCL component leaves. No complete MCL, femoral/distal tibial footprint, or posterior-knee Humphrey/Wrisberg claim. |
| `open-knee-anterior-meniscofemoral-bolog-fig18` | 769×629 | Coronal PD MRI, 19-year-old male patient. Large arrow identifies normal Humphrey ligament, small arrow PCL. | `knee.meniscofemoral_ligaments.anterior_meniscofemoral_ligament` only. |
| `open-knee-posterior-meniscofemoral-bolog-fig19` | 1302×548 | Sagittal PD MRI, 43-year-old female patient. Large arrows identify Wrisberg in a/b; small arrow identifies the adjacent lateral posterior-horn margin in a. | `knee.meniscofemoral_ligaments.posterior_meniscofemoral_ligament` only. The horn/root extent is not inferred. |
| `open-knee-plc-anatomy-wu-fig1` | 1416×1239 | a is a labeled cadaver cross-section; b is labeled axial MRI (IT band, ALL, LCL, popliteus, PFL, biceps, arcuate, plantaris, lateral gastrocnemius); c/d are color-coded schematic overlays. | Keep MRI b unbound until the exact course/attachment leaves can be matched beyond one cross-section. Schematic c/d can be local candidates for PFL course, arcuate course and distal biceps-femoris course. Dissection a remains ancillary. |
| `open-knee-popliteofibular-mri-wu-fig4` | 1180×708 | Black arrowhead marks local PFL in a; white arrow marks fabellofibular ligament in b. | Local `knee.popliteofibular_ligament.course` candidate from a; no two-attachment or complete-length claim. No invented fabellofibular leaf. |
| `open-knee-medial-posterior-root-mri-ssr-fig2a` | 733×523 | Normal medial posterior root on MRI A from a 22-year-old man **with ACL tear**. Original asterisks and brackets are intact. | `knee.medial_meniscus.posterior_root` only. Normal root in an injured examination, not a normal whole knee or intact ACL. No lateral-root inference. |

The batch has ten proposed structure/representation candidates: five from Bolog MRI, three from Wu schematic c/d, one from Wu MRI 4a, and one from SSR MRI 2A. All require independent anatomical/clinical review; none should be marked approved or high fidelity merely after import.

## Exact rights review

- **Bolog and Andreisek (2016)**, [publisher article](https://link.springer.com/article/10.1007/s13244-016-0472-y), [Figure 14](https://link.springer.com/article/10.1007/s13244-016-0472-y/figures/14), [Figure 18](https://link.springer.com/article/10.1007/s13244-016-0472-y/figures/18), [Figure 19](https://link.springer.com/article/10.1007/s13244-016-0472-y/figures/19). Article license is CC BY 4.0. Exact selected captions and pixels show no different license or restriction. General thanks to Suzanne Potter for helping acquire some images are preserved as attribution, not treated as exclusion.
- **Wu et al. (2024)**, [publisher article](https://link.springer.com/article/10.1186/s13244-024-01606-x), [Figure 1](https://link.springer.com/article/10.1186/s13244-024-01606-x/figures/1), [Figure 4](https://link.springer.com/article/10.1186/s13244-024-01606-x/figures/4). Publisher explicitly includes images in CC BY 4.0 unless a contrary credit line appears. None appears on these selected figures. Authors acknowledge the donated-body material created at Charles University. Figure 1's original caption repeats “a” for MRI; the visible MRI label is **b**. Full caption is kept verbatim; curated caption/metadata disclose the typo and select b correctly. Healthy-volunteer demographics in this paper refer to **ultrasound**, so they are not applied to the MRI panels. MRI age, sex, side and preparation remain unknown.
- **Nguyen et al. (2026), SSR consensus panel report**, [publisher Figure 2](https://link.springer.com/article/10.1007/s00256-026-05281-5/figures/2), [publisher-deposited primary XML](https://pmc-oa-opendata.s3.amazonaws.com/PMC13424353.1/PMC13424353.1.xml). The actual primary grant is CC BY 4.0 and includes images unless excluded. Figure 2 identifies MRI A and arthroscopy B separately; the credit is specifically **“Arthroscopic view courtesy of Theodore J. Ganley, MD.”** This is attribution to B, not a different license or an MRI-A restriction. Only MRI A is proposed for distribution. In contrast, the separate Bennett/CHOP illustrations (Figures 1, 4, 9 and 13) explicitly state **“All rights reserved. Used with permission”** and were not imported. A blanket article license is not used to override that explicit notice.

## Pixel provenance and exclusions

The Bolog HTML figure files are only 307×445, 307×251 and 520×219. The much larger **native PDF JPEGs**, with their intact arrows, were selected instead:

- Figure 14: PDF page 8, `Im0.jpg`, index 0, 769×1115.
- Figure 18: PDF page 9, `Im0.jpg`, index 0, 769×629.
- Figure 19: PDF page 10, `Im0.jpg`, index 0, 1302×548.

All three are original JPEG bytes. Source/saved decoded pixel hashes match. No PDF vector labels were lost: all displayed arrows and panel letters are embedded and were visually checked.

Wu 1/4 are the unmodified full-size publisher PNGs. All printed labels, leader lines, color overlays and arrows are intact. The full composite in Wu 1 is retained with explicit MRI/schematic/dissection distinctions.

SSR Figure 2A is the exact pixel rectangle `[0,0,733,523]` of the publisher's 1496×523 PNG, ending at the white divider (x733–742). No resampling, colorspace alteration, reconstruction or annotation replacement was performed. The full composite is retained **only** at `offline-provenance/ssr-fig2-complete-offline-only.png`; it is not in `assets/`, has no suggested application URL, and must not be copied into web output. The selected crop contains no B pixels. Full source caption and attribution remain in the image record; no arthroscopic/pediatric facts are borrowed as MRI-A context.

All six final files decode, match their native dimensions and SHA-256 hashes, and their candidate IDs exist in the current knee requirement inventory. No generation, sharpening, resizing or upscaling was used. Native source detail remains finite. High-fidelity review and browser rendering are not established by these staging checks.

## Unfilled gaps and nonselected leads

- The initial six-figure batch did not supply normal **lateral posterior root** MRI. A subsequent [source review](msk-knee-root-nd-review.md) established that the 2018 young-volunteer study (PMC6392791) expressly permits commercial redistribution of unchanged complete figures under **CC BY-ND 4.0**; its complete Figures 6/7 were integrated unchanged. The earlier blanket no-ND exclusion was an over-carried delegated sourcing filter, not an explicit user or project prohibition. No unrestricted-modification requirement should be inferred from the commercial-use goal.
- ESSR 2024 (PMC11399221) is CC BY 4.0 but its relevant root/PLC panels depict tears, avulsions or instability; they were not passed off as normal anatomy.
- Bolog 17 includes a normal Wrisberg ligament but also an explicit medial posterior-horn radial tear. Bolog 19 supplies the requested local normal relationship without substituting that pathology case.
- Wu 3 was inspected and is a useful additional original MRI lead for LCL/biceps/arcuate structures, but is **not selected for this six-entry batch**. Its research copy remains outside `assets/` and `records.json`.
- No complete posterior-root/PLC volume, quantitative attachment surfaces, patient-specific 3D registration or clinical validation has been established. The six integrations preserve all 48 prior source figures; no requirement definitions or fidelity gates were changed.

## Evidence-ledger integration and validation

Seven rows were appended to `data/radiology/msk-asset-evidence.json` without changing any of its 655 existing rows, bringing the ledger to 662 assets. The extra row is `open-knee-plc-anatomy-wu-fig1-schematic-panels`, which uses the original composite pixels but selects only c/d and has modality **Schematic**. The corresponding clinical row selects MRI b, has no requirement bindings, and cannot borrow schematic or cadaver coverage.

Exact candidate requirement bindings:

| Source | Leaf IDs |
|---|---|
| Bolog 14, single unlettered MRI | `knee.medial_collateral_ligament.superficial_component`; `knee.medial_collateral_ligament.deep_meniscofemoral_component`; `knee.medial_collateral_ligament.deep_meniscotibial_component` |
| Bolog 18, single unlettered MRI | `knee.meniscofemoral_ligaments.anterior_meniscofemoral_ligament` |
| Bolog 19, MRI a/b | `knee.meniscofemoral_ligaments.posterior_meniscofemoral_ligament` |
| Wu 1 schematic c/d | `knee.popliteofibular_ligament.course` (d); `knee.arcuate_ligament.course` (d); `knee.biceps_femoris_tendon.distal_course` (c) |
| Wu 4 MRI a only | `knee.popliteofibular_ligament.course` |
| SSR 2 MRI A only | `knee.medial_meniscus.posterior_root` |

These are **ten local candidates**, not complete-course or attachment-surface assertions. Each bound leaf has a source-panel/marker explanation. The Wu 4 evidence row intentionally excludes fabellofibular ligament from its `structures_observed`, because only a is selected for PFL evidence. The full two-panel figure remains unchanged in the viewer. SSR 2A preserves the adult MRI population and explicitly records `normal_root_in_acl_injured_knee`; the omitted pediatric arthroscopy contributes no MRI claim.

Every new row retains `visual_review.status: source_checked`, `anatomical_review.status: pending` and `fidelity: source_reviewed_not_clinically_approved`. No approval fingerprints were invented and no gates were weakened. The full audit changed from **0 verified / 116 unverified / 5086 missing** to **0 verified / 126 unverified / 5076 missing**, out of **5202 representation requirements**. Clinical/commercial readiness remains **not established**.

All seven rows passed file SHA-256 and native-dimension checks; retained original decoded pixel fingerprints also match. All 655 pre-existing ledger rows compare exactly with the pre-append snapshot. **138 focused tests passed** across knee-source, fidelity and runtime-rights checks. The tests reject replacing MRI b with the cadaver/schematic panels, prevent the ACL-injured root source from satisfying a normal-whole-examination context, preserve the PFL-a-only selection, and confirm that source reconciliation cannot grant clinical approval. Full audit evidence is in `/tmp/primer-msk-sources/knee-image-batch/full-audit-after-ledger.json`. Browser presentation is a separate check.
