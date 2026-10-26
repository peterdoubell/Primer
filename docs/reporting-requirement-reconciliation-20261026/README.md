# Current reporting anatomy and representation requirements

This audit reconciles every one of the **156 current reporting investigation identities and 4,124 authored report rows** with the expanded anatomy inventories. It checks the authored investigation and row sets against the compiled descriptor forms. Counts include technique, measurement, disease and workflow rows; they are not counts of distinct anatomical meshes.

The brain inventory now explicitly includes the **28 report rows** that were missing from its earlier 210-part expansion. They require **30 side-specific parts**: 24 cortical targets, two amygdalae and four MCA superior/inferior division territories. Each of the two MCA reporting rows offers right, left and bilateral distributions, so each adds a right and a left anatomical requirement. The inventory now has **240 parts and 720 image/schematic/model obligations**. All 210 earlier part objects, every original parent, and every byte outside the brain object are preserved.

`brain-reporting-requirements.json` records every current brain row, its source hash, the explicit requirement IDs and the available source-context candidates for all 30 additions. All completion flags remain false. Whole clinical extent, acquisition visibility, disease representation and independent anatomical review are separate requirements. In particular:

- The source superior/inferior frontal and cingulate compositions contain only their explicitly named member labels.
- The superior temporal source parcel does not silently include separately labelled planum and transverse temporal regions.
- The source amygdala parents have eight protocol children but only seven present children on each side; the medial nucleus has no source voxels.
- Angular and supramarginal source labels are component candidates for the inferior-parietal target. Their union does not itself prove full clinically defined inferior-parietal extent.
- No source MCA division territory mask is available. An artery model or a cortical gyrus cannot stand in for a supply territory.

`all-current-reporting-reconciliation.json` retains all report rows, investigation snapshots, relevant expanded inventory identities and named structure IDs. The 96 exact inventory identities still need review against the expanded current reporting rows. Among the 60 other identities, the audit distinguishes:

| Relationship | Investigations | Consequence |
| --- | ---: | --- |
| Declared duplicate trauma pathway | 1 | Thoracolumbar injury refers to the established fracture pathway; all 17 T1–L5 rows still need explicit level-specific representation. |
| Modality, region, organ or finding partition | 4 | Existing anatomy is relevant, but the selected acquisition/extent/observation remains explicit. |
| Aggregate with additional targets | 7 | Several existing inventories overlap; their union has not been established as complete. |
| Related anatomy with new acquisition, disease, developmental, dynamic or dedicated regional scope | 17 | Context is available; dedicated requirements remain necessary. |
| Distinct unexpanded investigations | 16 | A dedicated named inventory remains to be expanded. |
| General/procedure templates | 15 | Distinguish anatomy-bearing targets from physics, technique and workflow, and instantiate actual sites/acquisitions. |

Same-module identities are recorded but never accepted as equivalents. For example, paediatric hip and paediatric elbow share a guide but have different anatomy; a comprehensive MRI hand report cannot inherit all coverage from a wrist inventory. Literal name correspondences are review candidates only. This audit does not imply that an unmatched identity has no existing artwork or that a matched identity has complete artwork.

## Evidence and reproducibility

Run `python tools/anatomy_sources/reconcile_current_reporting_requirements.py --write` to apply the idempotent brain expansion and regenerate the two evidence files. Changes to current reporting identities or brain row sets require explicit reconciliation. Tests verify preservation of the previous brain object and full inventory bytes, enforce side instantiation, retain the full reporting population and reject changed/partial expansions. The strict inverse `before_current_brain_requirements` can reproduce the prior inventory for frozen receipts; it rejects unknown edits and grants no clinical credit.

Anatomical report names and conditions are traced to the current repository-authored report. Source labels and source composition membership are traced to the pinned protocol and current runtime metadata. The [released holiAtlas dataset](https://zenodo.org/records/15690524) and [authors' methods paper](https://arxiv.org/html/2501.16879v1) were reviewed on 2026-10-26. They describe a population template derived from 75 subjects, a fused multiscale label protocol, processed T1/T2 contrasts and a synthesized WMn-like contrast. This supports source provenance, not independent clinical validation. The final journal page could not be fetched through the research browser, so no new claim depends on uninspected journal text.

The clinical/commercial goal remains incomplete. Requirements, source masks, rendering proofs and green tests are different kinds of evidence; none alone establishes the requested full anatomical and clinical standard.
