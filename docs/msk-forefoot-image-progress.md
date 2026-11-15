# Normal hallux and forefoot image acquisition

Reviewed and acquired on 26 September 2026. Six new entries from six source figures are appended to `data/radiology/msk-open-images.json`, under the existing `ra.mri-diabetic-foot` investigation. The base collection now contains 36 unique entries. Its loader provides 47 placements after existing explicit wrist sharing. The prior 30 records, source IDs and asset bytes were preserved. Source acquisition itself did not edit the requirement inventory or ledger. Subsequent integration added nine representation records with narrow hallux-only candidate bindings, keeping MRI, schematic and ancillary panels separate and all clinical-fidelity reviews pending.

The acquired figures describe **hallux/digit 1 anatomy**. They are normal anatomical adjuncts to the diabetic-foot reference, not examples of infection or Charcot disease, and do not create an instability indication. Hallux capsulosesamoid anatomy is not substituted for a lesser-MTP plantar plate. No new investigation was introduced. The separate source-grounded [forefoot scope reconciliation](msk-diabetic-foot-forefoot-scope-audit.md) adds conditional draft requirements while preserving the original infection report and all earlier anatomy.

## Primary sources and commercial reuse

**Wang et al., 2021** — [High-resolution 3T magnetic resonance imaging and histological analysis of capsuloligamentous complex of the first metatarsophalangeal joint](https://link.springer.com/article/10.1186/s13018-021-02795-7), *Journal of Orthopaedic Surgery and Research* 16:638. The publisher explicitly applies CC BY 4.0 to images/third-party material unless a figure-specific credit says otherwise. Figures 1, 2, 3 and 7 have no courtesy/reproduction exclusion. Their schematic diagrams are described in the methods as drawn according to the corresponding MR images.

This is a study of **fresh-frozen cadaveric feet**, with associated MR images, anatomical sections and histology. It is not a healthy living-patient atlas. The publication's terminology for a central plantar portion and its relationship to other hallux components is retained as source terminology, without treating the study's proposed anatomical interpretation as a universal equivalence with lesser-toe plates. Each representation is explicit in metadata.

**Chen et al., 2022** — [High-Resolution Ultrasound of the Forefoot and Common Pathologies](https://doi.org/10.3390/diagnostics12071541), *Diagnostics* 12:1541. The primary publication has CC BY 4.0 terms. The selected normal ultrasound panels 5c and 9d have no excluded third-party credit. The [PMC Open Access dataset metadata](https://pmc-oa-opendata.s3.amazonaws.com/PMC9322853.1/PMC9322853.1.json) confirms the CC BY published version and provides the source PDF and captions. NLM is credited as the retrieval source for that dated snapshot; no endorsement or latest-version claim is made.

Attribution, license links, source/figure URLs and complete source captions are preserved in the manifest and `web/reference-media/msk-open/ATTRIBUTION.md`. The selected excerpts are not derivative AI anatomy. No author-contact messages were sent.

## Exact figure and panel observations

| New entry | Actual source and size | Visible component evidence | Limits relevant to the ledger |
| --- | --- | --- | --- |
| `open-hallux-capsulosesamoid-schematic-wang-fig1` | Complete schematic, 1594 × 630 | Source text labels PP, IS, paired sesamoid-phalangeal, metatarsosesamoid and accessory sesamoid ligaments; medial/lateral sesamoids; FHL, medial/lateral FHB and abductor/adductor tendons. | Diagrammatic structure separation only. No measured attachment surfaces, clinical signal or high-fidelity mesh is supplied. No side is asserted from this generic drawing. |
| `open-hallux-central-plantar-mri-wang-fig2` | Complete mixed figure, 1276 × 2480; **left foot, 33-year-old specimen** | MRI c/d contains the curved PP marker, intersesamoid triangle, FHL arrow, proximal marker and normal distal recess. | Only c/d count as MRI. Panel a is schematic; b is dissection; e–h are histology. Microscopic collagen continuity cannot be attributed to the MR images. |
| `open-hallux-medial-sesamoid-mri-wang-fig3` | Complete mixed figure, 1593 × 1242; **left foot, 58-year-old specimen** | MRI c/d retains medial sesamoid-phalangeal triangle, medial metatarsosesamoid circled arrowhead, medial-FHB marker and the medial sesamoid. | Medial complex only; no lateral counterpart is inferred. Panel a is schematic and b is dissection, separately described. |
| `open-hallux-sesamoid-complex-mri-wang-fig7` | Complete mixed figure, 1540 × 2479; **right foot, 45-year-old specimen** | MRI c/d retains distinct markers for intersesamoid ligament, FHL, medial/lateral accessory sesamoid ligaments, FHB heads and abductor/adductor tendons; paired sesamoid profiles are visible. | a is schematic, b dissection, e/f histology. The medial sesamoid-phalangeal marker described across the complete figure is not separately counted as MRI evidence where it is only resolved in another representation. |
| `open-hallux-fhl-sesamoids-ultrasound-chen-fig5c` | Native ultrasound panel c, 1000 × 591 | Embedded labels identify FHL, MS, LS and I: FHL between medial/lateral hallux sesamoids and the intersesamoid ligament. | Only transverse US panel c is shown; no dissection/probe photograph or longitudinal panel is present. Side is not specified. No MRI or full tendon-insertion claim. |
| `open-hallux-plantar-complex-ultrasound-chen-fig9d` | Native ultrasound panel d, 1259 × 710 | The asterisk identifies hallux plantar tissue beneath a separately labeled FHL tendon, with M and P1 bony landmarks. | First-MTP ultrasound only. No individual sesamoid ligament or digit 2–5 plantar plate is resolved. Side is not specified. |

The complete Wang source figures retain their original panel letters and arrows. `clinical_panels`, `schematic_panels`, `schematic_structures_visible` and `ancillary_panels` explicitly separate MRI, schematic, dissection and histology. Every ancillary record has its own panel letters, visible structures and limits. No dissection or histological panel is labeled as acquired MRI or used as clinical-image coverage.

The two Chen extracts preserve only the selected source ultrasound raster. `source_panel` identifies c/d, the display caption is scoped to that panel, and `source_caption_full` preserves the complete original figure caption. Page-level letters were not embedded in those source rasters and were not artificially added. The actual ultrasound labels and star are embedded and remain visible. The figure 5 full caption uses “EHL” in its probe-position sentence; the displayed panel is explicitly labeled **FHL**. The entry's limits point out that distinction rather than reproducing the typo as an anatomical claim.

## Existing targets and boundaries

Existing inventory anchors include the hallux sesamoids, `foot.metatarsophalangeal_joints.mtp1`, FHL, joint capsules and intrinsic muscles in the MRI diabetic-foot reference. The source entries identify observed structures by name; the root task owns any exact bindings to current or proposed leaf IDs. Proposed named hallux and lesser-MTP requirements were not added by this acquisition task.

These figures can support review of central hallux plantar tissue, the sesamoid complex and neighboring tendons. They do not imply that every tissue layer, origin, insertion, dynamic function or pathology is shown. Ultrasound entries remain modality-specific and must not satisfy MRI-only leaves. Cadaveric MRI examples are separately identified from in-vivo normal ultrasound.

## Rejected or deferred candidates

- The requested lead, [Reijnierse and Griffith, 2023](https://pmc.ncbi.nlm.nih.gov/articles/PMC10668940/), explicitly uses **CC BY-NC-ND 4.0**. Its figures were not downloaded or added.
- Previously rejected Turf Toe/Najefi and Kimura noncommercial sources were not re-downloaded. Unclear rights for the 2026 Chinese plantar-plate MRI article were not treated as permission.
- Chen figure 7 was inspected. Its ultrasound labels P1/P2/P3 and stars identify **interphalangeal** plate relationships along a second toe. It was not mislabeled as a normal second-MTP plantar plate.
- Córdoba-Fernández et al., [Reports 2024;7:87](https://doi.org/10.3390/reports7040087), is CC BY 4.0. Figure 4 contains a specifically described healthy **left third-MTP** comparison in a patient with disease/postoperative change at other rays. Its native right-hand MRI panel is 571 × 424 and lacks specific plate/attachment markers. It remains a locally inspected candidate, not an added high-detail attachment atlas or a blanket normal-foot case.
- Velleman's [2014 forefoot review](https://sajr.org.za/index.php/sajr/article/view/732) is commercially reusable under CC BY 4.0, but no extra figure from it was needed in this bounded batch. No source count was increased merely to reach a target.

**Normal, digit-specific lesser-MTP plantar-plate attachment coverage remains open.** The new hallux material must not close it by analogy. There is also no independent clinical sign-off or complete normal-population reference implied by this batch.

## Pixel and loader validation

The four full-size Springer PNGs were copied byte-for-byte. The two ultrasound panels were extracted from original embedded JPEG 2000 PDF images (`Im41.jp2`, page 6; `Im66.jp2`, page 9) and encoded losslessly as PNG. Saved mode, dimensions and decoded bytes match the embedded source exactly; both decoded-pixel hashes are recorded. No crop, resampling, sharpening, synthetic detail, anatomical reconstruction or image-generation tool was used.

All six final image files were opened for visual inspection at useful resolution. All file SHA-256 hashes and saved dimensions match the manifest. The six new files total **7,441,606 bytes**. The application loader accepts the 36 unique entries and 47 placements including pre-existing explicit sharing. The previous 30 manifest records were compared for deep equality before the append. These are source and depiction checks, not a clinical release approval.


## Subsequent lesser-MTP reference

A separate [third-MTP MRI reference](msk-lesser-plantar-plate-source.md) now
supplies an intact plate-body example in panels a/b, with the pathological
comparison panels explicitly distinguished. This is a partial digit-3 candidate;
attachment coverage and the remaining lesser-digit sites are still unresolved.
The original six hallux figures and their narrower source scopes are preserved.
