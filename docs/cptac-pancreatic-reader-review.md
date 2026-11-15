# Pancreatic native CT references in the reader

The local pancreatic cancer staging lesson now includes two distinct original C3L-02112 CT references in the Images tab. Each 1800 × 1200 figure retains its own axial/coronal/sagittal native sections, source sampling, crop and two display windows. The existing picture viewer supports fitting the whole figure and reading labels at full size, including a scrollable 1800 px image within the mobile dialog. The selected series are not registered or shown as matched planes.

Captions identify each source role as arterial-labelled or venous-labelled without granting phase adequacy. Visible limits retain the CSV/RTSTRUCT tracking mismatch, two unannotated acquired venous planes, positive contour endpoints and unreconciled ROI-volume construction. Whole pancreas, histology, ducts/vessels/neural anatomy, invasion, complete staging and resectability are not inferred from these unmarked source sections. No contour or model is overlaid.

Reader provenance pins each source acquisition to its actual object count, acquisition number/time, CT and annotation archive hashes, original selection/geometry audit and native-section review. It preserves the negative original spacing tag/instance-order direction separately from positive actual-position analysis indices. The validator rejects exchanged acquisitions and rehashed changes that assert registration, phase verification, whole pancreas, histology, resolved tracking or resolved endpoint/volume construction. Packaging verifies the separate source archive integrity receipts and retains named original imaging and annotation attribution with their separate CC BY 4.0 records.

Both assets are registered only for `ra.ct-pancreatic-cancer`. Anatomy review remains pending, structure IDs are empty and requirement coverage remains empty. The clinical-fidelity inventory was refreshed to include the new references; all 759 pancreatic representation obligations remain unverified/missing, the known all-radiology floor remains 12,399, 104 investigations remain unexpanded, and complete clinical/commercial readiness remains unestablished. Interface availability is not approval.

Verification on 4 October 2026: 116 combined reader/reference/visual/pancreatic/fidelity checks passed. Local API served both figures and both provenance records with HTTP 200 and matching SHA-256. Final API response included named annotation authors. Desktop 1440 × 1000 and mobile 390 × 844 checks loaded both full-resolution images; document widths were 1440 and 390 respectively. Both picture dialogs and mobile full-size mode were exercised, and no browser runtime errors were reported. Desktop arterial-dialog and mobile screenshots were directly inspected. These are local checks on this branch, not authenticated production verification or a new deployment.

- [Desktop image tab](cptac-pancreatic-reader-review/desktop.png)
- [Arterial desktop dialog](cptac-pancreatic-reader-review/arterial-dialog-desktop.png)
- [Mobile source caption and limits](cptac-pancreatic-reader-review/mobile.png)
- [Venous full-size mobile view](cptac-pancreatic-reader-review/venous-full-size-mobile.png)
- [Browser checks](cptac-pancreatic-reader-review/browser-checks.json) and [API asset checks](cptac-pancreatic-reader-review/api-assets.json)
- [Original source acquisition and rights](cptac-pancreatic-source-review.md), [native figures](cptac-pancreatic-native-sections.md), [every contour and raster error](cptac-pancreatic-contour-review.md), and [exact 3D source outlines](cptac-pancreatic-contour-geometry.md)

The source contour models and raw archives remain offline. Full reporting-anatomy coverage, additional source cases/modalities and independent anatomical/clinical review remain required for the complete all-radiology objective.
