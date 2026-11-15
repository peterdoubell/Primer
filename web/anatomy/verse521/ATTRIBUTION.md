# VerSe sub-verse521 derived T1–L5 surfaces

Derived from the VerSe data under CC BY-SA 4.0: https://creativecommons.org/licenses/by-sa/4.0/

Source dataset: https://doi.org/10.17605/OSF.IO/T98FZ
Author repository: https://github.com/anjany/verse

Cite Sekuboyina et al. (2021), VerSe: A Vertebrae Labelling and Segmentation Benchmark for Multi-detector CT Images; Liebl and Schinz et al. (2021), A Computed Tomography Vertebral Segmentation Dataset with Anatomical Variations and Multi-Vendor Scanner Data; and Löffler et al. (2020), A Vertebral Segmentation Dataset with Fracture Grading. Full source citation guidance is preserved in docs/msk-verse-source-review/README-source.md.

Adaptation: Lewiner isosurface extraction at 0.5 in the original label grid, transformed by the CT affine. No smoothing, decimation, filling or component removal. Helper-vertex approximations and component findings are recorded in manifest.json. This is a source reference available in the reader; anatomical approval remains pending.

Browser packaging: original world positions and faces preserved exactly; area-weighted unit normals generated for lighting. No source components removed.
