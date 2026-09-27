# Dryad S192803 Raw MRI STL geometry review

Reviewed 2026-09-26. **Retain as an offline source candidate; no runtime import or clinical approval.** The candidate supplies useful independently labelled menisci, tibial cartilage and ligament volumes, but the present evidence does not establish a uniform anatomical-fidelity improvement over Malaya.

## Originals and method

All 12 ASCII STL files are byte-identical to their members in `STLs.zip` (SHA-256 `873f56215c90634e249ce122cf6f558ce85615d80a708c0c1b45b7b6d7379362`). Individual byte hashes, native bounds, facet counts, edge incidence, components, normal agreement and header fingerprints are in `geometry-audit.json`. The reusable checker is `tools/anatomy_sources/audit_dryad_knee_geometry.py`.

Every source coordinate and facet was retained. The audit uses float64 parsing of the exact ASCII numbers and exact-position edge matching, with no welding tolerance, smoothing, repair, decimation, registration or island removal. Native XY/XZ/YZ orthographic projections preserve relative geometry. Some faint bone context is clipped only for display. Comparison panels show separate subjects and are independently framed, not registered or accuracy measurements. No tissue-shape changes were made to obtain these images.

## Source scope and fidelity claims

The [Dryad README](https://datadryad.org/dataset/doi%3A10.5061/dryad.zkh1893gw) identifies 12 left-knee MRI-segmented surfaces in the original MRI coordinate system. All names/counts match that inventory, including one object described as tibia/fibula. Every filename ends `_smooth` and every STL header names MeshLab. The exact smoothing settings and their effect on boundaries are not documented in the supplied files.

The [2025 primary paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC12391196/) assesses CT/white-light-scan kinematic models. Those models use ligament connectors and omit menisci/patella. Their validation does not certify these separate Raw MRI STL boundaries. The paper acknowledges assistance checking segmentation, but does not certify each of these files for our reporting use. Its disclosed smoothing/repair workflow should not be mistaken for untouched imaging boundaries.

## Geometry findings

There are **631,032 facets**, all finite and nonzero. Each file has one connected component by shared exact edges, no boundary edges, nonmanifold edges, duplicated geometric facets or inconsistent paired-edge winding. Every source normal agrees with winding; the largest angular discrepancy is 0.1062 degrees. Normal rounding is retained. These are geometry-integrity findings, not an anatomical-accuracy result. Self-intersection was not assessed globally.

| Object | Dryad facets | Current Malaya counterpart facets |
|---|---:|---:|
| ACL | 8,144 | 2,672 |
| PCL | 17,686 | 2,732 |
| MCL | 38,832 | 1,768 |
| LCL | 11,726 | 1,916 |
| Femoral cartilage | 62,862 | 22,788 |
| Medial tibial cartilage | 5,972 | 3,576 |
| Lateral tibial cartilage | 1,700 | 2,772 |
| Medial meniscus | 20,060 | 3,196 |
| Lateral meniscus | 6,030 | 2,000 |
| Femur | 57,840 | — |
| Tibia/fibula source object | 367,950 | — |
| Patella | 32,230 | — |

The table describes tessellation only. Malaya medial/lateral values are its existing exact disconnected-component exports. It is not evidence that the denser surfaces are more accurate.

Visual inspection of all three planes shows:

- **Menisci:** separately named crescent surfaces with variable wedge thickness and asymmetric endpoints. These are useful whole-object shape references. No independent horns, roots, attachment fibres, meniscocapsular or meniscotibial structures are labelled; rounded endpoints do not establish their completeness.
- **Cartilage:** femoral surface follows two condyles and their intervening region, with visible regional transitions despite dense tessellation. Medial and lateral tibial surfaces are separately identified. The lateral tibial mesh remains conspicuously faceted; its lower tessellation contradicts any blanket “higher resolution” description. There is no separately identified patellar-cartilage object.
- **Ligaments:** ACL/PCL and collaterals have nonuniform volumetric surfaces, not simple line connectors. The cruciates and MCL are not divided into the clinically required bundles, layers or attachments. A shaped end is not a validated footprint.
- **Bones:** the README's combined tibia/fibula object visibly includes both shaft forms, but is **one connected surface**, with Euler characteristic −2 (all other files: 2). It does not supply independent tibial/fibular boundaries or prove physiological joint continuity. Do not split or name new anatomical pieces without examining its segmentation.

## Paired-image and frame limitations

Available source headers report a `1024 × 1830 × 130` grid and spacing `0.5126953125 × 0.5126953125 × 2.0000000055` mm. Thus the exported grid has finer in-plane sampling but coarser slice spacing than Malaya's approximately `1.154 × 1.154 × 1.2` mm export. Sampling is not uniform-resolution improvement, and smoothing does not recover missing image detail.

The header `TransformMatrix`/`Offset` cannot currently be treated as a proven direct STL-to-MRI mapping. The usual `Offset + M × (Spacing × index)` convention does not explain the observed ACL STL bounds. Another ordering, `Mᵀ × (Offset + Spacing × index)`, approaches them numerically, but no undocumented transformation has been adopted. The root task is verifying source-export conventions and mask/mesh correspondence; this review leaves registration unresolved.

The verified full `Imaging_Data.zip` hash reported by the root acquisition task is `aa3fa1453cf20491494ef69dd02ed6bc92eb01e272159a5f3e4cdf6b2a5f9831`. Its preliminary CRC-verified MRI payload contains only a small region of nonzero grayscale data, so a complete diagnostic MRI pairing must not be inferred from filenames or common header grids. Consult the separate full-archive image audit for the final quantitative finding.

## Review images

- `individual-soft-tissue-surfaces.png`: isolated native objects, independently framed.
- `cartilage-three-planes.png`: the three cartilage objects with faint bone context.
- `menisci-three-planes.png`: both source-labelled menisci and their thickness/profile.
- `ligaments-three-planes.png`: all four intact source ligament volumes.
- `bone-source-objects-three-planes.png`: full bone objects, showing combined tibia/fibula extent.
- `dryad-malaya-separate-source-comparison.png`: separate-source silhouettes, not fitted correspondence or clinical validation.

The appropriate next decision depends on original mask completeness, the source coordinate convention, and expert tissue-boundary review. No current MSK fidelity requirement, approval or runtime asset is changed by this audit.
