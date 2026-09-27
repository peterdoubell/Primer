# Leeds author-assembly visual review

Offline projections inspected on 27 September 2026. No runtime, catalog or ledger changes, new source acquisition, geometry fitting or clinical approval.

## Figures

- `leeds-author-assembly.png`: all seven solid tissue groups in the unmodified author-instance positions, screen right +X, up +Z and eye on -Y. Every group has visible pixels, but only small portions of each meniscus are exposed by this opaque whole-assembly projection. The source-limited bone ends are retained; the renderer does not reconstruct missing tissue.
- `leeds-tibial-cartilage-menisci.png`: bone and femoral cartilage omitted, screen right +X, up +Y and eye on +Z. Both whole menisci and both tibial-cartilage surfaces are clearly distinguishable and remain in their original relative positions. This reveals two separated cartilage objects and the curved meniscal bodies, without inventing root, horn or attachment delineations.
- `leeds-femoral-cartilage-bone.png`: femur and femoral cartilage at the declared oblique native camera basis. Cartilage across the two broad lobes and the intervening exposed bone can be distinguished. Visible facets reflect the source/planar display; no smoothing is used to hide them.

The three images have legible labels and caveats, no apparent viewport cropping, and no obvious isolated rendering fragments. These are bounded visibility observations, not checks for microscopic boundary error, surface intersections, exact MRI correspondence, clinical normality or independent anatomical validation.

## Representation and provenance

`rendering-evidence.json` records source NPZ and INP hashes, source metadata, camera bases, per-tissue submission/visibility counts, renderer/font fingerprints and output hashes. All selected source faces are submitted, including their midside nodes. Each six-node face ordered a,b,c,ab,bc,ca is displayed as four planar triangles: a-ab-ca; ab-b-bc; ca-bc-c; ab-bc-ca. This is explicitly approximate. Unchanged six-node arrays in `../geometry-audit/` remain the exact source audit representation; the pre-existing 16-triangle preview arrays were not needed for these views. The geometry audit records a maximum midside-to-edge-midpoint deviation of approximately 1.04e-5 native units, but no complete display-error bound is claimed.

Normals are calculated from the display triangle geometry; no FE source facet normals are invented. Opaque per-pixel global depth testing handles occlusion across all included tissues. Shared interfaces at the same depth use the inherited canonical primitive tie rule. Figure colours, projection and lighting are added. Native source values undergo no unit conversion; no patient RAS labels are assigned and no registration is inferred.

The source methods document CT-derived bone/cartilage and MRI-derived menisci adjusted for contact conformity and solver convergence. Root mechanics are represented by springs and are excluded; other knee tissues are absent from this seven-solid-group model. The selected `seg_intact_fix` case is not proof of an intact whole knee or normal tissue.

Source: Cooper RJ, Day GA, Wijayathunga VN, Yao J, Mengoni M, Wilcox RK, Jones AC (2023), University of Leeds, DOI10.5518/981. CC BY4.0, https://creativecommons.org/licenses/by/4.0/. Dataset licence evidence: source README page2. Rendering is a derivative source-review image, not an MRI or clinical measurement.
