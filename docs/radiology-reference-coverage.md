# Radiology foundation and reporting coverage

This update uses [The Radiology Assistant](https://radiologyassistant.nl/) as the illustrated reading foundation for Primer's radiology curriculum. The source index was reviewed on **23 September 2026**. It maps the medical educational articles linked from the site's home-page specialty navigation, including CT protocols and RECIST, to curriculum modules.

The resulting curriculum contains **96 modules**, including **12 new modules with 120 original quiz questions**. Its foundation index contains **188 distinct article bodies represented by 196 navigation URLs**: eight duplicate article bodies appear as aliases, preserving their original navigation titles, sections and links. Six nonmedical links about site information, finances, apps or media authoring are documented as exclusions. The index is bounded by this navigation snapshot; it does not assert an inventory of every historical, unlinked or future page on the website.

## What is available locally

All 96 modules have an original structured report scaffold or review worksheet. The coronary CTA and prostate MRI guides have more detailed templates. All 298 key-image slots now display attributed teaching figures: 285 clinical examples, 10 diagrams and 3 reference tables, using 289 distinct image sources. No module repeats an image within its own gallery. The cases are independent teaching examples, not a single patient study; report series/image references remain blank for the reader's own examination. Captions identify the actual view and do not imply that a related example is the exact acquisition described in the report prompt.

The gallery loads 293 image references from Radiology Assistant and four from Wikimedia Commons, with one original local Doppler illustration. Publisher images remain remotely hosted and require a connection. Commons entries include the credited author, license and license link. Every figure has alt text, a caption and a source link. Pictures open in the keyboard-accessible viewer; native-size viewing uses the original pixel width and does not upscale small source images. Failed loads retain their explanatory caption and source link.

The CCTA template adapts the user's supplied example. No readable prostate attachment was available in this task, so the prostate template follows the linked PI-RADS foundation and its stated reporting structure; it has not been checked against the unavailable example document.

Article titles, links, topic headings and source relationships are available in the local catalog. Full source prose and videos remain on the publisher's website; selected images are displayed directly from their credited hosts. The catalog provides comprehensive navigation-topic coverage within its stated scope, but does not establish full local content parity with those articles. A source heading is an indexed reading topic, not evidence that a matching local lesson, quiz or diagnostic image has been authored for every subsection.

Thirteen additional professional source records support eleven of the new modules. These include ACR appropriateness guidance, NCI anal cancer staging, ESUR/ESGAR pelvic-floor recommendations, AIUM neonatal-spine guidance, EFSUMB intestinal-ultrasound guidance and CNS positional-plagiocephaly guidance. These **13 source records** are separate from the **13 supplementary curriculum modules** described below.

## Coverage by curriculum section

Counts group each source article by its assigned Primer module, not necessarily by the publisher's original specialty. Each article has one primary `module_id`, so shared clinical relevance does not multiply the count. “Mapped modules” have at least one directly assigned foundation article. “URLs” includes the eight retained aliases.

| Curriculum section | Modules | New modules | Mapped modules | Foundation articles | URLs |
| --- | ---: | ---: | ---: | ---: | ---: |
| Foundations | 5 | 0 | 1 | 1 | 1 |
| Physics & Technique | 1 | 0 | 0 | 0 | 0 |
| Safety & Governance | 1 | 0 | 0 | 0 | 0 |
| Reporting & Oncology | 2 | 0 | 1 | 3 | 3 |
| Intervention | 1 | 0 | 1 | 1 | 1 |
| Chest | 9 | 0 | 9 | 25 | 25 |
| Cardiovascular | 7 | 0 | 7 | 14 | 15 |
| Neuroradiology | 12 | 1 | 11 | 20 | 21 |
| Head & Neck | 9 | 3 | 9 | 15 | 17 |
| Abdomen | 17 | 4 | 17 | 40 | 40 |
| Genitourinary | 6 | 0 | 6 | 12 | 14 |
| Breast | 4 | 1 | 4 | 8 | 8 |
| Musculoskeletal | 11 | 1 | 9 | 31 | 31 |
| Paediatrics | 8 | 2 | 8 | 18 | 20 |
| Nuclear & Molecular | 3 | 0 | 0 | 0 | 0 |
| **Total** | **96** | **12** | **83** | **188** | **196** |

The video-only “US of Mimics of Inflammatory Bowel Disease” reading has no published text-section outline. Its catalog entry explicitly records this instead of inventing headings. The publisher's navigation entry titled “...” is represented as “Foot and ankle cases (Wrist archive)”, with the original navigation label preserved.

## New modules

The additions cover esophagus and swallowing; anal cancer; small bowel tumours and gastrointestinal foreign bodies; dynamic pelvic-floor imaging; breast implants and the male breast; tinnitus; trigeminal neuralgia and neuropathy; sellar and parasellar MRI; elbow MRI; neonatal-spine ultrasound; bowel-ultrasound technique and anatomy; and craniosynostosis. They use anatomy and physiology prerequisites rather than gating one radiology peer module behind another.

## Supplementary curriculum modules

These 13 existing modules have **no directly assigned Radiology Assistant article** in the dated catalog. They retain original teaching material, diagrams and new reporting or review scaffolds, and the reference layer marks them as supplementary. They are not silently counted as source-mapped coverage. None currently has a record in `supplemental-sources.json`, whose 13 professional references support the new modules instead.

| Module ID | Module |
| --- | --- |
| `rad.2.radiation-safety` | Radiation Safety |
| `rad.3.ct-image` | Reading the CT Image |
| `rad.3.mri-sequences` | Telling MRI Sequences Apart |
| `rad.2.modalities` | What Each Modality Detects |
| `rad.5.ultrasound-physics` | Ultrasound Physics, Doppler and Artefacts |
| `rad.5.biopsy-safety` | Image-guided Biopsy and Drainage |
| `rad.4.structured-reporting` | Structured Reporting |
| `rad.4.head-trauma` | Head Injury: Selecting, Timing and Reading the Trauma CT |
| `rad.3.fracture-description` | Describing a Fracture |
| `rad.5.msk-mri` | Musculoskeletal MRI |
| `rad.5.nuclear-general` | Bone Scan, V/Q, Thyroid and Sentinel Node |
| `rad.5.pet-ct` | FDG PET/CT in Oncology |
| `rad.5.theranostics` | PSMA, DOTATATE and Theranostics |

This primary-assignment rule explains some apparent gaps. For example, the publisher's traumatic intracranial haemorrhage article is assigned to the dedicated intracranial haemorrhage module, while the more general head-injury module remains supplementary. General MSK MRI and fracture-description modules likewise complement the mapped regional modules.

## Clinical version review

The review date establishes when the links and topic map were inspected. It is not a clinical sign-off date for every pre-existing quiz answer. Source articles have different publication dates, and terminology and staging editions may differ between older local material, the foundation articles and current professional guidance. The current navigation includes TNM ninth-edition lung staging and BI-RADS v2025 manuals; references to earlier editions should be assessed in their specific clinical context rather than changed by a global text replacement.

Two concrete source discrepancies informed the additions: the foundation anal-cancer page's wording at the 2 cm T-stage boundary differs from the NCI staging definition, and its neonatal-spine page gives a restrictive conus-level statement. The new questions avoid relying on those ambiguous boundaries. For clinical thresholds and classifications, maintain the named edition, patient population and primary reference alongside the authored material.

## Data and update workflow

- `data/radiology/source-catalog.json` is the dated foundation inventory, including article IDs, titles, URLs, headings, primary module assignments, aliases and exclusions.
- `data/radiology/additional-modules.json` holds the twelve authored additions; the consolidated curriculum contains these nodes in `data/curriculum/11-radiology.json`.
- `data/radiology/supplemental-sources.json` holds the additional professional source records.
- `tools/build_radiology_guides.py` contains the original per-module reporting specifications and generates `data/radiology/module-guides.json`.
- `data/radiology/flagship-templates.json` supplies the detailed CCTA and prostate guide overrides.
- `data/radiology/key-images-flagship.json`, `key-images-foundations-body.json` and `key-images-neuro-msk.json` map every image slot to its reviewed figure, caption and attribution. These overlays survive guide regeneration. Review replacement figures in their source context and verify their visible content before changing an assignment.
- `primer/radiology.py` combines guides, overrides and source assignments into the module reference payload, validating identifiers, source URLs and template structure.

To update the foundation, inspect the current publisher navigation and relevant article pages, add or revise source metadata, preserve alias evidence, resolve each article to a valid module, and record the new review date. Check the associated professional guidance before changing version-sensitive teaching. The catalog was assembled from the inspected site; **no scraper or automatic source-content synchronisation is committed**.

Author reporting changes in the generator's `SPECS` or the flagship override file, then regenerate the ordinary guide data from the repository root:

```sh
python3 tools/build_radiology_guides.py
```

The generator reads the consolidated curriculum and any additional module IDs not already present; it writes the guide JSON, not the curriculum. When adding or revising a module, keep its authored node and consolidated curriculum entry consistent, update its original illustration through the illustration generator, and check that all source mappings, report fields, key-image slots and quiz answers still resolve. Recalculate this document's coverage table after changing assignments or module counts.

## Reporting desk upgrade

The September reporting-reference pass replaces the generic findings bodies in
ordinary templates and adds a direct `#/radiology` workspace with six views per
module. All 96 modules now have reviewed reporting checklists, measurement
methods, impression prompts and a local interactive 3D companion. See
[radiology-reporting-desk.md](radiology-reporting-desk.md) and the
[per-module audit](radiology-reporting-audit.json) for coverage and validation.
