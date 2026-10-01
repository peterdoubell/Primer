# MASSP 2.0 native source candidates

Pinned dataset: [MASSP 2.0 Lifespan Probabilistic Atlas, version 2](https://doi.org/10.21942/uva.27291579.v2), by P.L.E.A. Bazin, B.U. Forstmann, Anneke Alkemade and Steven Miletic. The publisher's versioned [metadata](https://api.figshare.com/v2/articles/27291579/versions/2) states CC BY 4.0. Its description specifies 97 subjects aged 18–80 and MNI2009b space. These adult population maps do not establish individual anatomy or developmental coverage.

Sixteen source files were acquired: bilateral caudate, putamen, internal/external globus pallidus, internal capsule and thalamus probability maps, plus the publisher label table, best-label map, maximum-label map and maximum-probability map. All match the publisher's byte count and MD5; independent SHA-256 values are retained in `brain-massp-source-review/acquisition.json`. Original NIfTI data are offline under `.research/massp-brain`, with no coordinate or probability changes.

The twelve selected probability maps share a 394 × 466 × 378 grid at 0.5 mm sampling. The declared sform provides the source affine; qform is absent. Storage axes are RPS, matching the publisher's warning. No identity registration to the BodyParts3D coordinate frame is assumed. Native probability inspection records bounds, centroids, threshold counts, affine codes and original file hashes. No probability threshold has been promoted to an anatomical surface. Subsequent offline source-label surface work is described below.

The left/right thalamus probability maps have small nonzero tails beyond the midline. These are preserved and recorded, not clipped or mirrored. Zero such tails were found in the other ten inspected maps. Probability colour plots use independently selected native axial planes, nearest-neighbour display and an explicit 0–1 scale. They are not clinical MRI images and do not prove full three-dimensional extent or clinical accuracy.

This source offers dedicated GPe/GPi candidates for the separately required pallidal segments, plus putamen candidates. Gross caudate, thalamus and internal-capsule maps still do not identify the required caudate segments, thalamic subdivisions or capsule limbs. A probabilistic atlas is not a patient boundary; source MRI, multi-planar anatomy and segmentation uncertainty need further review before runtime use.

The [associated methods paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC12319765/) describes automatic atlas construction from delineations and a broader AHEAD cohort. It discusses 105 subjects, whereas this pinned dataset describes and names 97. This cohort/version discrepancy remains explicit; no missing-subject explanation is inferred. Registration details, source contrast visibility and original validation metrics still need to be reconciled with the actual version 2 assets.

The two source label volumes were also enumerated in their original grids; integer-label consistency and header records are in `brain-massp-source-review/label-grid-review.json`. Label-to-probability and source-MRI correspondence remains unverified.

No runtime binding, clinical approval or complete representation credit was added. Acquisition is reproducible with `tools/anatomy_sources/acquire_massp_lifespan.py`; the native grid inspection uses `tools/anatomy_sources/review_massp_native_probability.py` with optional scientific libraries outside application dependencies.


## Native source-label surface review

All six GPe, GPi and putamen selections were evaluated using the publisher maximum-label volume and label table, in the same native source grid. Alternative 0.25, 0.5 and 0.75 probability selections were compared but not substituted for the source labels. Comparison Dice values describe selection differences, not anatomical accuracy.

The four pallidal label selections produced offline surface candidates with 48,762 triangles total. All original components remain; no smoothing, decimation, voxel resampling or anatomical editing was used. Their surfaces have no index-edge openings or nonmanifold edges. These checks do not exclude self-intersections or establish clinical anatomy. Source label masks have four to nine 6-connected components each, including low-probability tails down to 1/97. Their mean selected probabilities range from 0.716 to 0.872. Fragment identity and anatomical extent remain unresolved; closed surfaces alone cannot justify promotion.

The left putamen surface has nine nonmanifold edges and the right three. Exact coincident-position recounting does not remove them: these are not duplicate vertex seams. Both selections remain in the review record with their full voxel/probability statistics. No putamen model was exported from those maximum-label selections, no defect was repaired and no component was removed.

`brain-massp-source-review/surface-review.json` preserves all six outcomes. `pallidal-native-surface-candidates.png` shows the four candidates in original RAS millimetres from three views. Derived meshes stay offline in `.research/massp-brain/derived-surfaces`; no BodyParts3D registration or runtime coverage binding is implied. Reproduction uses `tools/anatomy_sources/massp_probability_mesh.py` and `render_massp_surface_review.py`; the renderer verifies candidate mesh hashes before plotting. Synthetic reflected-affine, retained-component and source-boundary tests passed with the separate scientific dependencies.

## Putamen contact localisation

The twelve nonmanifold edges were localised without source edits: six and three edges form two connected contact clusters on the left, and three form one cluster on the right. All incident edges have four faces. `putamen-contact-localisation.json` records source index/RAS coordinates, incident faces, exact native label/probability patches and the corresponding publisher best-label selections.

At the native voxel centres supporting these contact clusters, maximum-label-selected putamen values are 1/97 on the left and 1/97–2/97 on the right. The surrounding patches also include higher-probability anatomy; the low values must not be generalised to the entire putamen. A seventeenth, supplemental background probability file was acquired from the same pinned version 2 metadata and passed publisher size/MD5 and independent SHA-256 checks. Its acquisition record is `background-acquisition.json`.

At those selected contact-support centres the background probabilities are 96/97 on the left and 95/97–96/97 on the right. Every voxel in the recorded support blocks is labelled zero/background in the publisher best-label volume. These observed differences guide review of the two publisher selections; they do not independently establish the intended clinical use or full anatomical accuracy of either map. No model was substituted, no contact was repaired, and no original label, voxel or component was removed.

Reproduction: `tools/anatomy_sources/review_massp_putamen_contacts.py`, with `--source .research/massp-brain --output docs/brain-massp-source-review --background-record docs/brain-massp-source-review/background-acquisition.json`. This validates source file hashes and matching declared grids before localising the original maximum-label isosurface. Those two maximum-label putamen outputs remain held; original MRI visibility and complete anatomy still require assessment.


## Complete probability competition and source best-label surfaces

All 64 average probability maps (63 labelled regions plus background) from pinned version 2 were acquired and checked against publisher size/MD5, with independent SHA-256 records. The compressed collection is 82,686,729 bytes. Existing acquisition records and original source files remain preserved. `all-probability-acquisition.json` records the complete collection; raw volumes remain offline.

Whole-grid arithmetic reconstruction over 69,402,312 voxel centres gives an exact match for both publisher selections:

- `maxlabel` equals the highest positive foreground probability, excluding background, with lower label ID winning ties. It labels 1,266,135 voxels.
- `bestlabel` equals the highest probability including background, again with lower label ID winning ties. It labels 963,627 voxels.

Neither reconstruction has a disagreeing voxel. Including background changes 302,508 selected voxels relative to the foreground-only rule. Higher-ID tie alternatives fail the exact comparison. These are empirical identities with this dataset, not an author statement of clinical intent. They explain why a foreground-only selection can label areas where background is much more probable. `complete-label-selection-audit.json` preserves all comparisons.

The original publisher best-label volume was then evaluated for all six bilateral GPe, GPi and putamen requirements. All six complete selections yield closed index-edge surfaces with no nonmanifold edges, and each source selection has one 6-connected component. All components remain; no source probability threshold, mask repair, smoothing, decimation or anatomical editing was introduced. The derived candidates contain 105,222 triangles in original RAS millimetres. `bestlabel-surface-review.json` preserves hashes, native voxel counts, bounds, topology and uncertainty; `native-bestlabel-surface-candidates.png` shows three native views.

Selected mean probabilities range from about 0.882 to 0.939; minima still range from about 0.258 to 0.309. The arithmetic winner is not necessarily a high-confidence or anatomically validated boundary. Closed edge topology does not prove absence of self-intersections, fine anatomical completeness, clinical accuracy or registration to the existing reader atlas. All six candidates remain offline and unapproved, with no runtime coverage credit. Earlier foreground-only outputs and their failures remain separate evidence.

Reproduction uses `python -m tools.anatomy_sources.acquire_massp_probabilities`, `python -m tools.anatomy_sources.audit_massp_label_selection`, and the surface builder with `--selection bestlabel` and a separate output directory. The full source comparison and all six surface builds completed; 13 focused inventory/acquisition tests and three scientific geometry tests passed.

## Complete native voxel-centre coverage of exported surfaces

All six original best-label surface exports were compared independently with the publisher label volume. The audit intersects the exported triangles with every native Z voxel-centre plane spanning the full model, then fills the section at every native X/Y voxel centre in its complete bounds. Coplanar faces and shared on-plane edges are retained and deduplicated; no jitter, fitted transform, surface edit or source resampling is used. The comparison region is also checked to include every voxel carrying the target label anywhere in the original source volume.

Across 863,399 voxel-centre comparisons, all 160,498 source target voxels are included. Every one of the six exports has zero false-positive interior voxels and zero false-negative source voxels. This verifies complete exported coverage of these six source selections at their native voxel centres, rather than only a few sampled MRI sections. It does not prove independent anatomical accuracy, continuous subvoxel fidelity, absence of self-intersections or complete clinical reporting scope.

`complete-mesh-voxel-audit.json` preserves per-model hashes, full-source counts, comparison bounds and every audited plane. The section/raster method is adapted from the repository's existing native knee source audit, with explicit errors replacing optimisation-sensitive assertions. Analytical tests cover the known interior of a cube, an exactly coplanar face with shared edges and two disconnected complete components; all three passed with the separate scientific dependencies.

Reproduction uses `python -m tools.anatomy_sources.audit_massp_mesh_voxels --source .research/massp-brain --meshes .research/massp-brain/derived-bestlabel-surfaces --output docs/brain-massp-source-review/complete-mesh-voxel-audit.json`. No runtime asset or anatomical approval was added by this audit.

## Surface intersection and assembly hold

A full triangle-contact audit of all six source best-label models found no unexpected self-contact across 842,046 conservative AABB candidate pairs. The numerical comparison tolerance is 1e-9 mm. Noncoplanar pairs sharing an edge are resolved geometrically because their plane intersection is that shared edge; coplanar pairs and every single-vertex pair are explicitly tested for contact beyond the permitted shared topology. Eight analytical tests passed, including a crossing beyond a shared vertex, coplanar overlap beyond a shared edge, expected tangencies, reflection and broad-phase completeness on known cases.

The combined assembly does **not** pass the between-structure review. All fifteen structure pairs were assessed in the same original atlas frame. Four pairings initially had 653 contacts that were not covered by exact shared-vertex/edge or oppositely oriented coincident-triangle rules. Further assessment distinguishes 336 oppositely oriented coplanar contacts, 43 noncoplanar point contacts and 274 noncoplanar line contacts. At least eleven lines have a midpoint strictly inside both triangles: eight between left GPi/GPe and three between right GPi/GPe. Their endpoints, face IDs, line lengths and barycentric coordinates are preserved in `between-contact-assessment.json`.

These interior triangle crossings show that individually closed, voxel-consistent binary surfaces cannot yet be assumed to form a coherent non-crossing multi-structure assembly. Independently extracting each label introduces subvoxel interface approximations that need joint-interface investigation. The stored source label selections remain mutually exclusive at their voxel centres; no source label has been changed, merged or removed. A numerical crossing is an export/interface finding, not proof that the publisher anatomy is wrong.

The assembly is explicitly `held_cross_structure_surface_crossings`. Original meshes and earlier audits remain preserved. No runtime asset, anatomical approval or complete representation credit has been added. Other contacts also remain review evidence; the eleven confirmed interior crossings are not an upper bound on all possible interface defects or a volumetric overlap estimate. Fine medullary lamina anatomy remains unverified.

Evidence: `surface-intersection-audit.json`, `between-surface-contact-audit.json`, `between-contact-plane-assessment.json`, `between-contact-dimension-assessment.json` and the reproducible combined `between-contact-assessment.json`. Reproduction uses `audit_massp_surface_intersections.py`, `audit_massp_between_surfaces.py` and `assess_massp_between_contacts.py`, all under `tools/anatomy_sources/`.

## Joint-interface candidate resolving the detected crossings

A separate candidate now constructs all six targets jointly from the unchanged publisher best-label volume. Every native cell uses the same six-tetrahedron Freudenthal subdivision. Within each tetrahedron, each original label's weight is the sum of barycentric weights at source vertices carrying that label; the shared argmax interfaces are emitted with identical triangulation and opposite orientations for neighbours. Other source labels remain distinct competitors rather than being merged into background. Exact integer 1/12 index-coordinate keys preserve shared interface positions before the original native affine is applied.

This is a different, explicitly derived subvoxel interpolation. It does not add measured spatial resolution, infer a medullary lamina, establish clinical boundary accuracy or eliminate the directional assumption of the chosen subdivision. Source labels and probabilities were not edited. Earlier independent meshes and their crossing evidence remain unchanged. New candidate meshes are offline in `.research/massp-brain/joint-interface-surfaces`.

The joint candidate has 329,192 triangles across all six structures and passes the completed geometric checks:

- Every edge has incidence two; every vertex link is one connected cycle; every triangle has positive area and each surface has positive signed volume.
- All 863,399 native voxel-centre comparisons match, including all 160,498 original target voxels, with no extra interiors or omissions.
- The complete self-contact audit finds no unexpected contacts across 2,779,584 candidate pairs.
- All fifteen between-structure pairings find no unexpected contacts across 943,051 candidate pairs. This resolves the previously detected GPi/GPe crossings for this joint candidate.

Five analytical tests passed. They include all fifteen possible canonical vertex-label patterns: each emitted interface triangle appears exactly twice with opposite orientation across its adjacent regions. Additional checks cover the known two-class halfway plane, four-class face/tetrahedral junctions, maximum-weight interfaces and preservation of original labelled arrays.

Evidence: `joint-surface-review.json`, `joint-combined-topology-audit.json`, `joint-complete-mesh-voxel-audit.json`, `joint-surface-intersection-audit.json`, `joint-between-surface-contact-audit.json` and `native-joint-interface-candidates.png`. The earlier separate `joint-topology-audit.json` and `joint-vertex-link-audit.json` records also remain preserved. Reproduction uses `build_massp_joint_interfaces.py` and `audit_massp_joint_topology.py`, followed by the existing voxel/contact audits, all under `tools/anatomy_sources/`.

The specific geometric assembly hold is resolved for this candidate; anatomical approval is not. Direct MRI comparison of the newly interpolated boundaries, clinical source/context review and reader-atlas registration remain required. No runtime representation binding or clinical fidelity credit has been added.

The joint candidate now also has direct triangle/plane MRI overlays in the three quantitative contrasts, with both left and right sagittal sections. This checks the actual exported geometry's placement rather than substituting source-label contours. Twelve annotated median panels, their unmarked counterparts and variability panels are preserved in `docs/brain-ahead-qmri-source-review/`; source and mesh hashes passed. These selected views remain anatomical-review evidence, not complete boundary approval or clinical-grade credit.

## Reader integration of the scoped source reference

The local brain anatomy reader now offers the six joint-interface models as a partial adult population reference, alongside the existing whole-brain BodyParts3D context and reporting orientation guide. The coordinate frames remain separate; no geometric registration or coordinate merge is implied. The original walkthrough still uses its established context and does not falsely highlight new part IDs in the older atlas.

All original joint faces are retained in the BP3D transport. Float32 coordinate conversion is bounded below 2e-6 mm; each packaged file is byte-bound by compressed and decoded hashes. Normals are generated for lighting only. `reader-package.json` records conversion errors and unchanged face topology. The full source-labelled models remain intact, with no crop or source voxel edits. Clinical fidelity remains unverified in the manifest and all six candidate evidence records.

The three-contrast source MRI comparison is available below the model and in the image collection. Attribution and the 97-subject model versus 105-subject MRI context are supplied in the reader. Figure reuse rights are bound to pinned publisher licence evidence; rights review grants no anatomical approval. Six model requirements now have explicitly partial, unverified candidates, while the remaining brain requirements retain their previous missing/unverified state.

Desktop/mobile browser checks confirm load, structure selection/isolation, switching to the original whole-brain context and back, and full-resolution MRI image opening. A 390-pixel mobile viewport has no page overflow. The image loads at 1938 × 2553 pixels and supports the native-size control; browser runtime errors were empty. Screenshots and `reader-browser-checks.json` preserve evidence. Owned QA server/browser processes were stopped after verification.

The shared renderer change adds only this atlas URL and family range. Existing transforms, camera/framing, cropping, selection and geometry code are unchanged. Twenty-four already-pending MSK model dependency hashes were refreshed after reviewing that exact two-line registration diff; no clinical approvals were granted. The MSK queue was regenerated from `msk-verification-reader-massp-2026-10-01.json` without changing its anatomical denominator or coverage approvals.

No claim of clinical/commercial readiness or complete brain coverage is made. Runtime integration makes the source reference available for review; clinical anatomical accuracy, source variability, disease/developmental scope and every other required radiology structure remain unfinished.
