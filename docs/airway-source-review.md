# Native thoracic source acquisition

## AeroPath case 1

Source: [AeroPath data](https://doi.org/10.5281/zenodo.10069289), with the [author repository](https://github.com/raidionics/AeroPath) linking the `andreped/AeroPath` mirror. One original CT and its matching airway/lung annotations were acquired from mirror revision `6d0f831ca22bf57918aba3980ae475c94d45b997`. All three byte lengths and author-mirror SHA-256 values passed. Source voxels remain unchanged and offline under `.research/thorax-sources/aeropath-case-1`.

The Zenodo data record and explicit mirror data licence are CC BY 4.0. Mirror card/code metadata says MIT; it is not used to relabel the data. Exact data-licence evidence and acquisition fingerprints are in `airway-source-review/aeropath-rights-evidence.json` and `aeropath-case-1-acquisition.json`. No clinical approval follows from rights verification.

The [source publication](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0311416) describes patients undergoing diagnostic tests for lung cancer, with varied pathology. Airway annotations were refined with pulmonologist supervision and verified case by case. This supports their provenance but does not independently validate our interpretation, each reported substructure or any future surface conversion. Case 1's diagnosis, age and acquisition phase have not been independently assigned. It is not labelled a healthy/normal reference.

All three supplied arrays are 512 × 512 × 767 with 0.6840000153 × 0.6840000153 × 0.5 sampling, LPS storage axes and identical selected affines. CT declared qform/sform are numerically equal despite differing codes; the lung file has a declared qform only, which supplies the same affine. No fitted alignment or resampling was required. Scaling is 1/0 and original CT values span −1024 to 3071. The paper discusses source CT values in HU; independent scanner calibration/acquisition resolution is not established by this review.

Both annotations are binary: 451,530 airway-labelled voxels and 23,426,015 combined lung-labelled voxels. No positive annotation touches a source boundary face. This does not prove complete anatomical endpoints or acquisition coverage. The lung mask is not a five-lobe map; the airway mask contains no individual branch or segment names. Wall layers, cartilage, arterial partners, fissures, segmental territories, pathology and dynamic findings are not inferred from either binary label.

Native axial, coronal and sagittal sections were inspected with unmarked counterparts. `case-1-native-labels.png` and `case-1-native-unmarked.png` preserve the original image samples, a disclosed display window and axis presentation. The contour version shows source annotations only. `case-1-section-review.json` records exact plane indices, positions, pixel counts and display changes. Selected sections do not establish complete anatomical fidelity or measured clinical airway dimensions.

Reproduction: `tools/anatomy_sources/acquire_aeropath_case.py` and `render_aeropath_native_review.py`, using separate scientific dependencies. No model was generated or promoted, no runtime resource was added and no airway requirement was approved.

## TotalSegmentator subset

Pinned [TotalSegmentator small subset v2.0.1](https://doi.org/10.5281/zenodo.10047263) lists CC BY 4.0 and includes CT images/labels from clinical routine. It may provide lobe/tracheal context, not automatic bronchopulmonary segment definitions. The publisher download endpoint lacks an ETag, so the strict range-source identity check was not bypassed. A complete archive acquisition subsequently passed the publisher's full byte count and MD5; the completed case review is recorded below.

The acquisition tool is `tools/anatomy_sources/acquire_totalseg_subset.py`; archive size is 3,244,617,817 bytes and expected MD5 is `6b5524af4b15e6ba06ef2d700c0c73e0`. Raw data remain in `.research/thorax-sources/totalseg-v201`. While acquisition is live, do not restart it based only on an observation timeout or partial-file presence. A final checksum record is required before treating the archive as verified.

This source is independent of AeroPath. Its cases, anatomy, pathology, image quality, field-of-view and mask completeness must be inspected before any reference use. No coordinates or source cases will be combined merely because structures have similar names. The full radiology objective, all 687 airway representation obligations and every unresolved structure remain intact.

## AeroPath source surface and topology review

An offline, unsmoothed 311,740-triangle surface was reconstructed from every original airway-labelled voxel using the original affine. All 451,530 source voxels are included; 25,935,000 complete-bound voxel-centre comparisons show zero extra interiors or omissions. No annotation component was removed, no source value changed and no clinical endpoint was inferred from the generated closure. The surface remains in `.research/thorax-sources/aeropath-case-1/surface`.

The numerical surface is one connected component, with zero boundary/nonmanifold edges and zero nonmanifold vertex links. Its Euler characteristic is −196, corresponding to genus 99 under the checked closed vertex-manifold interpretation. These topological handles have not been identified as actual airway anatomy. Digital Euler values of the original binary region are −79 under 6-connectivity and −17 under 26-connectivity. Different adjacency/interpolation conventions matter; voxel-centre consistency does not prove continuous clinical topology or a simple anatomical tree.

No hole filling, smoothing, pruning, guessed connections or source-mask correction was performed. The candidate is held for topology/source-CT review and named-anatomy/extent assessment. Selected CT figures remain useful source context but cannot independently classify every small handle or establish wall/segmental anatomy.

Evidence: `case-1-surface-review.json`, `case-1-surface-voxel-audit.json`, `case-1-surface-topology-audit.json` and `case-1-digital-topology-audit.json`. Reproduction uses `build_aeropath_airway_surface.py` and `audit_aeropath_surface_voxels.py` under `tools/anatomy_sources/`. Three analytical section/coplanar/component tests passed. No runtime model or clinical coverage approval was added.

## Completed TotalSegmentator acquisition

The previously live archive acquisition completed successfully. All 3,244,617,817 bytes match publisher MD5 `6b5524af4b15e6ba06ef2d700c0c73e0`; independent SHA-256 and licence evidence are in `totalseg-v201-acquisition.json`. Session 11720 is terminal; no archive download remains live and no restart is required.

The first source case, `s0011`, was preserved for review with its CT and six original masks, each CRC-checked by the ZIP reader and independently SHA-256 recorded. File presence was not treated as positive anatomy. Native inspection confirms nonempty five-lobe and tracheal labels with no positive boundary-face contacts. The supplied arrays are 311 × 311 × 431 at **1.5 mm isotropic sampling**. This provides coarse source context rather than high-resolution airway/segmental evidence; original acquisition resolution, anatomical completeness, case normality and clinical label accuracy are not independently established.

Its five lobe masks must not be treated as bronchopulmonary segments, wall layers or detailed bronchi. Case `s0011` is independent of AeroPath case 1; their coordinates and masks are not combined. `totalseg-s0011-acquisition.json` and `totalseg-s0011-native-review.json` retain the exact source record. All raw data stay offline, and every airway requirement remains pending.

## Localised adjacency-sensitive source sites

Every 2 × 2 × 2 cube in the complete native airway review bounds was classified without editing the source annotation. Across 25,093,530 cubes, 487 have multiple 6-connected foreground or background components and therefore depend on diagonal/adjacency interpretation. All native origins and exact configuration codes are preserved in `case-1-adjacency-locations.npz`, byte-bound by `case-1-adjacency-localisation.json`.

These are candidate topology-sensitive sites, not a count of anatomical handles, pathological communications or artefacts. They do not establish a one-to-one mapping to the reconstructed genus 99. Uniform, face-neighbour and corner-only configurations were checked analytically; foreground/background complement symmetry was verified for every one of the 256 possible cube configurations. All three tests passed.

Six representative sites were reviewed from the first/last indexed cubes in the three most populated native-Z candidate planes. Original CT patches are preserved with unmarked counterparts, original annotation contours, projected cube-centre markers and exact 2 × 2 × 2 CT/label arrays. Display is nearest-neighbour with disclosed windows; no source voxel is resampled or changed. `case-1-adjacency-source-patches.png` and `case-1-adjacency-site-review.json` contain the views and selection basis.

Small labelled regions and near-boundary contacts are visible in these source patches, but their complete local 3D anatomy/cause remains unclassified. Neither a selected axial patch nor a connectivity rule proves a clinically justified correction. No holes were filled, branches pruned, cells reclassified or models promoted. The airway surface stays held pending three-dimensional source/anatomical review.

Reproduction uses `localize_aeropath_adjacency.py` and `review_aeropath_adjacency_sites.py` under `tools/anatomy_sources/`. This supplies concrete review locations while preserving every candidate and the complete required radiology scope.

## Native source CT figure in the local reader

The unmarked orthogonal CT review figure is now available in the local airway reader alongside its existing teaching examples. It is explicitly a native-volume section view, not a numbered publisher figure, named-segment atlas, healthy reference, calibrated measurement result or approval of the held surface. Case diagnosis/age/phase is not inferred. Full native source inputs and the held surface remain offline.

Packaged figure and source provenance are byte-bound in `web/reference-media/radiology-open/aeropath-case1-native-ct.png` and `aeropath-case1-sections.provenance.json`. Runtime validation checks the pinned provider identity, CT source SHA-256, licence, shape/plane bounds, no-resampling/no-overlay declarations, provenance hash and actual PNG dimensions. It rejects an invented publisher figure number, wrong modality, altered provenance, invalid dimensions and escaped evidence paths. These checks establish software/provenance integrity, not anatomical accuracy.

Four image obligations have explicitly partial unverified candidates for selected thoracic tracheal/carinal and main-bronchial context. No wall, cartilage, lobe, segment, disease-specific, dynamic or 3D-model coverage is credited. Source image rights are verified separately; anatomical review remains pending. All requirements and the held genus-99 surface remain intact.

Eighty-four relevant tests passed. Desktop/mobile browser checks confirm the title and source-volume link, preserved older examples, full image opening at 2418 × 981 and the native-size control. A 390-pixel viewport has no page overflow; browser runtime errors were empty. Screenshots and `reader-native-ct-browser-checks.json` preserve evidence. Owned QA processes were stopped.

The gallery renderer change only handles native-volume titles and source links. Twenty already-pending image presentation hashes were refreshed after reviewing that limited diff; no approval or model behaviour changed. The MSK queue was regenerated from `msk-verification-reader-native-ct-2026-10-01.json` without altering its denominator or anatomical approvals.

These reader changes are local and undeployed. They make a real licensed source image available for review while preserving every anatomical/clinical gap.

## Same-case lobe relationship review

The five original `s0011` lobe masks were assessed against their own supplied CT, with each source member's SHA-256 checked. All masks share the exact CT shape/affine. Their combined 1,569,906 labelled voxels are mutually exclusive, with zero overlapping lobe voxels. No positive label touches a source boundary face. These findings establish source-grid consistency and sampled boundaries, not complete acquisition coverage, normality, fissural accuracy or fine anatomical precision.

Four detached single-voxel components are retained: one in the right upper lobe and three in the right lower lobe. Their exact native indices, all component sizes, voxel counts and bounds are in `s0011-lobe-review.json`. They have not been diagnosed as noise, deleted, reassigned or merged. The other three lobe masks have one 6-connected component each.

Representative native axial/coronal/sagittal CT views are preserved as `s0011-lobe-unmarked.png` and `s0011-lobe-labels.png`, with disclosed windows and original label contours. The 1.5 mm supplied grid is prominent in their titles. It is not described as high-resolution, and these coarse labels are not substituted for fine airway walls, segmental bronchi or bronchopulmonary territories. The midpoint sagittal plane may show little lung; it remains source context rather than a claim of complete lobe depiction.

`tools/anatomy_sources/review_totalseg_lobes.py` reproduces the source-grid/component/overlap checks and review views without resampling, fitted alignment or source edits. All original source fragments remain available. No model was generated, no image was added to the reader and no representation requirement was approved. The dataset remains independent of AeroPath case 1 and every finer required structure remains outstanding.
