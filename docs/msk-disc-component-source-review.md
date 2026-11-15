# Disc-component source review

27 September 2026. The current thoracolumbar requirement retains four separate
parts: annulus fibrosus, nucleus pulposus, superior endplate interface and
inferior endplate interface. A whole-disc outline cannot satisfy these by itself.

## Native atlas inspection

The already-acquired Z-Anatomy Joints100 FBX was rechecked against its recorded
SHA-256. It contains 23 separately named whole-disc meshes and 23 separately
named nucleus meshes, covering C2–C3 through L5–S1. No geometry explicitly named
annulus fibrosus, or annulus/nucleus material name, was found in this inspection.
This is a naming/inventory finding, not a claim that an unlabelled region could
never depict part of the annulus.

Every nucleus has 482 vertices and identical native polygon connectivity.
Fitting each native vertex array to the first nucleus with an affine transform
leaves maximum residual below 1.3e-14 of that mesh's local bounding-box diagonal.
Thus the 23 arrays are affine copies of one base shape to numerical precision.
Separate object names and transformations do not establish independent measured
internal boundaries at each level. The audit does not claim to prove the
original authoring operation merely from this similarity.

Native polygon incidence also raises specific whole-disc review issues:

- L1–L2 has five boundary edges and seven non-manifold edges in the original
  indexed polygon data. These are not repaired or hidden by triangulation.
- C6–C7 has one connected component, no boundary/non-manifold edges in that
  check, and Euler characteristic −2. The topology requires interpretation;
  it is not automatically labelled a biological defect.
- The other disc counts do not establish anatomical accuracy, an internal
  annulus boundary, absence of self-intersections or valid tissue volumes.

The [native audit](msk-disc-component-source-review/native-atlas-disc-audit.json)
records every object, source identifier, local bounds, incidence counts and
nucleus comparison. `tools/anatomy_sources/audit_disc_component_sources.py`
reproduces it without exporting, modifying or promoting geometry.

## External candidates checked

| Source | What is supported by the inspected source | Decision for component geometry |
|---|---|---|
| [SPIDER, version 4](https://zenodo.org/records/10159290) | Public MRI with vertebra, whole-IVD and spinal-canal reference segmentations. | Useful whole-disc/MRI candidate; the inspected record does not document separate AF/NP/endplate-interface labels. Do not infer those labels. |
| [Matos et al., 2023](https://doi.org/10.1016/j.cmpb.2023.107337) | A segmentation method addressing AF/NP distinction; reported results include lateral under-segmentation. | A method lead, not a verified reusable component asset. No component masks or geometry from it were acquired or accepted. |
| [Patient-specific modelling study, 2025](https://www.nature.com/articles/s41598-025-19664-6) | Its methods define the nucleus by scaling a projected disc outline and extruding it, then generate annulus geometry around it. | Explicit geometric modelling assumption; not accepted as measured nucleus/annulus boundaries. A visually smooth mesh does not remove that limitation. |
| [Human L3L4 shape model, 2014](https://pmc.ncbi.nlm.nih.gov/articles/PMC4115453/) | A whole-disc statistical shape-model lead with supplemental data. | Component scope and reusable-asset rights remain unverified. The PMC page presented a browser challenge; no challenge was solved or bypassed. |
| [Stepwise micro-CT study, 2026](https://doi.org/10.1016/j.ocarto.2026.100857) | Reports high-resolution ex-vivo imaging and preparation-dependent morphological changes. | Potential microstructure lead; raw-data availability, reuse rights and component labels were not established. No unstated correction for processing distortion is permitted. |

No generated nucleus, atlas whole-disc shell or generic annular primitive was
substituted for the missing required structures. No requirement was removed or
marked complete. The next acquisition needs explicit component boundaries and
source images, with acquisition/processing limitations and reuse rights attached.
