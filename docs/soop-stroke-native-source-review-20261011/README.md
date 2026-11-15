# SOOP native stroke source packet, 11 October 2026

This packet preserves the complete original **sub-342** MRI and all three source
lesion masks from [SOOP ds004889 v1.1.2](https://doi.org/10.18112/openneuro.ds004889.v1.1.2).
The pinned published Git root tree is `a62344db73f18f384a95b452f4a1a423087e059b`.
All 11 original files, **52,676,049 bytes**, match the published Git blobs or
Git-annex SHA256 content identifiers and sizes. Original NIfTI and JSON bytes are
unchanged. The complete payload includes 21 files, **105,836,672 bytes**: originals,
seven lossless stored-value transports and three literal mask-cell meshes.

The source dataset description grants **CC0**. The separate
[primary publication](https://doi.org/10.1038/s41597-024-03667-5) carries different
article reuse terms; no publication artwork or full article text is packaged.
The source publication supports the dataset provenance and illustrates this
participant. It describes three trained neuroscientist raters; its T2, ADC and
TRACE annotation wording is inconsistent. Source filenames and Data Records
specify TRACE-space masks. Source “acute”, “chronic” and “combined” labels are
preserved without independently determining biological lesion age or clinical
validity. The source data were defaced; scalp and remaining source anatomy are
preserved.

The source selection examined sub-1 and 32 pinned protocol JSON files for eight
additional candidates, including the two publication-illustrated participants.
Sub-342 provides finer complete released anatomy and all three original mask
files. This is an evidence-driven case choice, not a claim to have screened every
SOOP examination or found its best achievable anatomical resolution.

| Source | Complete stored shape | Sample spacing, approximately | Source sidecar thickness / centre spacing |
| --- | --- | --- | --- |
| TRACE | 288 × 288 × 26 × 1 | 0.933 × 0.933 × 6 mm | 5 / 6 mm |
| ADC | 288 × 288 × 26 × 1 | 0.933 × 0.933 × 6 mm | 5 / 6 mm |
| T1 | 370 × 512 × 512 | 0.500 × 0.484 × 0.484 mm | 1 / 0.5 mm |
| FLAIR | 200 × 512 × 512 | 0.900 × 0.489 × 0.489 mm | 1.8 / 0.9 mm |
| Each of three masks | 288 × 288 × 26 | 0.933 × 0.933 × 6 mm | Source labels on the TRACE sampling grid |

These spacings do not establish effective acquisition resolution, histological
resolution, or full named-structure fidelity. Diffusion contains unacquired
interslice gaps. Literal sampling cells span centre-to-centre intervals, so mask
geometry and its sampling-grid volume do not imply continuously measured tissue
through those gaps.

All **160,204,800** stored source samples (**313,939,968 decoded bytes**) are
retained. MRI transports preserve original int16 values and apply the exact
NIfTI slope/intercept in JavaScript Number at display/probe time. Masks preserve
original uint8 label IDs. ADC's scaling is `raw × 0.5792486667633057 + 18980.8203125`;
its clinical physical unit scale is unverified. TRACE/ADC's singleton fourth
dimension remains in the manifest and is disclosed as original frame 0 of 1;
zero temporal spacing supplies no time interval. Both qform and sform, selected
affine, dimensions, all spacing and units remain inspectable. TRACE, ADC and masks
have identical stored spatial affines in this case. T1 and FLAIR remain separate
native grids with independent cursors and no mask overlay or cross-grid linking.

The viewer loads complete TRACE, ADC and mask buffers first. Selecting T1 or FLAIR
loads its complete source buffer, after releasing any previous large anatomical
buffer. The loading readout exposes sequence availability. No cropped or
lower-resolution stand-in is substituted. Native i/j/k controls accept only
finite whole source indices. Rendering uses nearest-neighbour original samples,
declared linear windows and optional reversible voxel tint. The complete pinned
manifest, compressed bytes and decoded values are verified before use.

| Original mask file | Labelled voxels | Complete 6-connected components | Triangles |
| --- | ---: | ---: | ---: |
| Acute | 2,760 | 13 | 9,688 |
| Chronic | 11,780 | 1 | 16,644 |
| Combined | 14,540 | 14 | 26,332 |

Every occupied cell and every exposed cell face is retained, including all
single-voxel components. Each mesh follows its own original file. No boolean
union, smoothing, interpolation, decimation, component removal or hole healing
is used. The source combined file happens to equal the boolean union with zero
overlap; this is an audit comparison and no replacement union was used. Float64
source coordinates and uint32 indices remain stored and verified; only GPU
display coordinates/normals round to float32. Edge/point contacts can make literal
cell boundaries nonmanifold, and the viewer makes no artificial repair.

Owned verification: eight pytest tests compare all original bytes, all stored
array bytes/scaling/dimensions/affines, every exposed original cell face,
source-volume determinants, component counts, 7,007 typed native probes, invalid
indices and bad geometry. Fresh actual-browser contexts at **1440 and 390**
verify all seven complete source buffers across sequence selections, 42 probe
states, 126 canvas frames (**38,341,632 actual RGBA bytes**) against independent
original-array pixel calculations, 30 complete mesh/camera draws, finite input
rejection, keyboard navigation, invalid and extreme finite window checks, and eight corrupted-source failure/recovery paths. Loading failures
clear all planes and prior GPU geometry, mark data unavailable and disable every
control except Retry. Both widths have zero page errors and no horizontal
page overflow. All browser handles were closed. Captures are source-viewer QA;
this evidence makes no authenticated-reader or production UI claim.

`integration-proposal.json` pins the presentation and payloads for parent-owned
registry/Blob/backend integration. Independent source/data/geometry review is a
separate prerequisite. Source fidelity and reuse permission do **not** grant
clinical, fine-anatomical or named-structure coverage. Timing, pretreatment status,
irreversibility, source ADC clinical units, source DICOMs, registration transforms,
vascular data and complete reportable anatomy are not proved. The stroke module
and the whole Primer goal remain incomplete.

The finite-window amendment retains the exact prior viewer hash and records its
overflow-induced NaN canvas value for ±1e308 endpoints. The repaired viewer
normalizes before multiplying and safely halves the ratio when the span overflows;
the correct centre value is 128. Prior exact viewer/proofs remain in ignored QA
intake; the final browser and pixel proofs are repeated against the repaired hash.
