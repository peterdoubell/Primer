# Actual-reader review screenshots

Six unmodified desktop/mobile captures from a disposable local QA profile, 2026-10-11. These are documentation evidence for existing licensed source delivery. No source case, native volume, annotation array, media binding or anatomical approval is added. Screenshot selection is bounded to both source families and one representative native CT plane; the complete JSON proofs cover all 17 vertebral levels and both Liu surfaces.

## VerSe captures

# VerSe sub-verse521 derived T1–L5 surfaces

Derived from the VerSe data under CC BY-SA 4.0: https://creativecommons.org/licenses/by-sa/4.0/

Source dataset: https://doi.org/10.17605/OSF.IO/T98FZ
Author repository: https://github.com/anjany/verse

Cite Sekuboyina et al. (2021), VerSe: A Vertebrae Labelling and Segmentation Benchmark for Multi-detector CT Images; Liebl and Schinz et al. (2021), A Computed Tomography Vertebral Segmentation Dataset with Anatomical Variations and Multi-Vendor Scanner Data; and Löffler et al. (2020), A Vertebral Segmentation Dataset with Fracture Grading. Full source citation guidance is preserved in docs/msk-verse-source-review/README-source.md.

Adaptation: Lewiner isosurface extraction at 0.5 in the original label grid, transformed by the CT affine. No smoothing, decimation, filling or component removal. Helper-vertex approximations and component findings are recorded in manifest.json. This is a source reference available in the reader; anatomical approval remains pending.

Browser packaging: original world positions and faces preserved exactly; area-weighted unit normals generated for lighting. No source components removed.

The four VerSe reader/CT screenshot adaptations retain CC BY-SA 4.0 for the source-derived content. The screenshots retain the native CT window/overlay and existing source mesh presentation.

## Liu captures

# MRI contour-envelope reference

Jionghui Liu, Wenqi Zhang, Yuxing Zhou, Linhao Xu, Yinghua Chu and Fumin Jia (2024). Dataset: https://doi.org/10.6084/m9.figshare.c.7372564. Original MRI: https://doi.org/10.6084/m9.figshare.26403595.v1. Original annotations: https://doi.org/10.6084/m9.figshare.26403442.v1. CC BY 4.0: https://creativecommons.org/licenses/by/4.0/.

Adapted from source sub-03 contours under documented fresh Slicer 5.4 defaults. Adjacent-plane triangulated envelopes retain the interpreted source points, open endpoints and shared LPS coordinates. Display normals generated for lighting. Anatomical boundary accuracy and full reporting coverage remain unverified. The study article licence is distinct; no article figure or generated nerve tube was adapted.

The two Liu reader screenshot adaptations retain CC BY 4.0 for source-derived content. They depict the existing reconstructed open contour envelopes, not source article figures or measured fine tissue boundaries.
