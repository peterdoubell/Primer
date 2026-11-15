# Vertebral substructure source review — 30 September 2026

The thoracolumbar specification retains body walls, endplates, left/right pedicles and laminae, spinous/transverse processes and articular processes. The reader's whole-vertebra VerSe labels do not independently verify these components.

## Original LumASe candidate

[The original Zenodo record](https://zenodo.org/records/7181338) describes 663 lumbar vertebral CT crops with seven anatomical subregions, annotated by three physicians. Its saved API metadata declares CC BY 4.0. The stated exclusions include fractures, implants, bone tumours and foreign materials; this source cannot be presented as a trauma series.

The archive directory was acquired through validated byte ranges: 663 CT files and 663 annotation files, with no label dictionary or other non-NIfTI documentation in the archive. One original L3 CT/annotation pair was acquired. Local member names, expanded sizes and ZIP CRC32 values match the central directory; individual SHA256 hashes are recorded. The publisher's whole-archive MD5 is recorded, **not** independently verified, because the remaining archive was not downloaded.

The native pair shares a 190 × 195 × 102 grid and identical affine, with 0.41015625 × 0.41015625 × 0.5 mm voxels. The source mask contains foreground values 1–7. The NIfTI headers have no descriptive text or extensions that establish their anatomical meanings. Numeric label names remain unresolved. Four foreground classes (values 4, 5, 6 and 7) touch the source array boundary. This raises a crop-completeness question; it does not by itself prove anatomical truncation. Six- and 26-neighbour component counts and individual volumes/bounds are retained in the native audit. No caps, resampling, predicted segmentation, hole filling, component removal or smoothing has been applied.

Reproducible acquisition and audit tools are `inspect_lumase_archive.py`, `acquire_lumase_case.py` and `audit_lumase_case.py` under `tools/anatomy_sources`. Original NIfTI files and scientific dependencies remain in ignored `.research` staging. The saved record, inventory, acquisition hashes and native audit are in `msk-vertebral-substructure-source-review/`.

## Distinct newer resources

[The LumbarSeg-6K publication](https://doi.org/10.1038/s41597-026-07986-7) describes a harmonized derivative with **CC BY-NC-SA 4.0 data**; its article has separate CC BY-NC-ND terms. It is not the original CC BY LumASe archive. No images or annotations from that derivative were added to the commercial runtime.

The publication's author repository, SpineSubNet, was inspected at pinned commit `1bca53a9355fef46a586b1a65d7f0e140a52c333`. The inspected README, configuration, processing and consistency-evaluation definitions use numeric classes without proving the original LumASe numeric-to-anatomical mapping. Its component-cleaning rules were not run or copied into our source processing. Source file hashes and conclusions are recorded in `source-scope-and-schema-review.json`.

## Remaining gates

Obtain an authoritative original label dictionary, then inspect each actual region against the native CT. Bilateral grouping, endplate surfaces, cortical walls, source crop completeness and annotation errors must be evaluated separately. Seven class names alone cannot satisfy all reportable components, every spinal level, pathology or the complete MSK goal. No clinical approval or runtime promotion is claimed for this candidate.

## Crop-boundary review and ten-case screen

`lumase-native-boundary-review.png` displays all six native crop faces, with adjacent planes one and four voxels inward: 18 CT/label views. Physical voxel aspect ratios and source directions are retained. Labels remain numeric; the overlays are new review annotations under the original data's CC BY 4.0 terms. No underlying image values or segmentation voxels were edited. The associated JSON records exact planes, source coordinates, file hashes and visible label values.

The predetermined first ten lexicographically ordered paired L3 masks were acquired and screened, with all results retained in `lumase-crop-screen.json`. All ten contain the seven source classes; all ten have foreground voxels at the crop boundary (141–1,047 unique contacting voxels). None meets the criterion of having every label surrounded by source-array margin. This is a sampled source-scope finding, not a conclusion that all 663 cases are truncated or that any particular anatomical endpoint is definitely absent.

Do not zero-pad these masks and call the resulting closed surfaces complete anatomical objects. Boundary contact and finite native planes require explicit endpoint review, and numeric labels still require an authoritative mapping. No runtime model or completed reporting-component binding was created from this screen. `boundary-screen-decision.json` records these gates.

## Numeric source surfaces — offline

Seven original numeric label surfaces were extracted without zero padding or closure caps. They contain 238,484 triangles. Generated voxel positions, original-affine world coordinates and triangle topology are preserved in `output/msk-lumase-l3/`; all seven saved arrays passed exact reload comparison. No mask editing, smoothing, decimation or cross-case registration was performed. Original data attribution and CC BY 4.0 terms accompany the package.

| Original value | Triangles | Open crop edges |
| --- | ---: | ---: |
| 1 | 13,408 | 0 |
| 2 | 59,078 | 0 |
| 3 | 19,192 | 0 |
| 4 | 26,082 | 30 |
| 5 | 18,376 | 44 |
| 6 | 12,842 | 48 |
| 7 | 89,506 | 60 |

Every open-boundary vertex lies on an original array boundary. Basic edge/area checks found no nonmanifold edges or zero-area triangles, but did not prove absence of self-intersections or biological correctness. Independent trilinear sampling found 13 label-2 helper vertices at mask value 0.625 instead of the requested 0.5; these extraction approximations were retained and recorded, not projected or silently corrected. This mask-value discrepancy is not a measured physical anatomical error.

`lumase-numeric-surfaces.png` shows anterior, posterior and right lateral review projections of all seven surfaces, with open crop edges marked red. Its source/audit fingerprints are recorded in `lumase-surface-rendering.json`. The regions retain numeric names. A closed mesh is not evidence of a complete or correctly labelled anatomical structure. No global requirement bindings, runtime promotion or clinical approval were assigned.

Crossref publisher metadata identifies the related 2023 ISBI publication, DOI `10.1109/ISBI53787.2023.10230438`, by matching title and authors. The publisher page presented a JavaScript automated-access challenge; no full text or label dictionary was acquired. Its relationship to the exact original annotation schema remains unverified. `msk-lumase-schema-inquiry-draft.md` prepares precise source-definition questions and has not been sent.
