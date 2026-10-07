# Original OpenEar source acquisition and preparation limits

The [OpenEar dataset](https://zenodo.org/records/1473724) explicitly grants CC BY 4.0. The complete ZETA.zip acquisition is in progress; its expected size is 3,868,308,936 bytes and publisher MD5 is `66fc062426086d2757e837593fd548e5`. Partial bytes are not a verified complete archive. Geometry, registration and colour remain unreviewed and no runtime promotion or structure coverage is granted.

The [original source paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC6326113/) describes adult cadaveric specimens, fixation, staining, dehydration and epoxy embedding, with a preparation opening drilled into the superior semicircular canal. Specimen colour and altered morphology must not be represented as untreated living-ear appearance. The source acquisition used 0.25 mm unembedded CBCT and 0.125 mm embedded CBCT; registered sampling is not proof of original resolution. Micro-slicing reconstruction includes alignment/interpolation. Source overmould registration measurements do not independently validate every internal structure. Case-specific data and limits still need inspection.

`tools/anatomy_sources/acquire_openear_case.py` retains incomplete transfers as `.zip.part`, checks exact HTTP resume ranges, verifies the complete publisher MD5 before promoting an archive, and then checks each member's ZIP CRC and SHA256. Three tests pass for exact resumed bytes, rejected non-range responses and checksum failure. No licence, header, mesh or colour claim is approved merely by those integrity checks.

## Original archive catalogue inspection

A bounded original archive-suffix HTTP range returned the central directory without restarting or replacing the full acquisition. The catalogue lists 2,917 entries, including folders: 13 PLY models, six NRRD files, five H5 files, two CSV files, 2,646 DICOM entries and 222 TIFF photographs. Its suffix hash is retained. Catalogue metadata is not complete-archive or member-byte verification; publisher MD5 and member CRC checks still await the ongoing full transfer.

Named model candidates include scala tympani/vestibuli, malleus/incus/stapes, facial/chorda/cochleovestibular nerves, tympanic membrane, external auditory canal, Sinus Dura, Carotis Interna and Bone. Names do not establish anatomical identity or complete tissue extent. The Sinus Dura label must not automatically supply separately resolved venous lumen, vessel wall and dural anatomy. Colour may only be used where original registered photographs actually provide support; preparation changes and unsupported regions must remain explicit. Detailed review gates are saved in `ZETA-catalogue-review.json`; every structure coverage claim remains unapproved.

## Complete ZETA acquisition and original geometry/header inspection

The original transfer completed successfully. The full 3,868,308,936-byte archive passed publisher MD5, and all 2,901 file members passed ZIP CRC and SHA checks. The earlier live transfer handle is terminal; it must not be restarted. Complete acquisition evidence is in `ZETA-original-acquisition.json`.

All 13 actual binary little-endian PLY meshes were read against their acquired member hashes. Every position is finite, face count is triangular, and index lies within its source vertex array. Chunked area checks cover all 7,349,910 triangles without decimation. Bone retains two original zero-area triangles; other meshes have none. Geometry, coordinates, triangles, source generator comments and degenerate faces are preserved. Some generator comments describe repair/hole-filling settings; those declarations do not independently prove which upstream operations occurred, and no further repair is applied.

PLY files contain x/y/z and face indices, with no photographic RGB attributes. Slicer segment colours include automatically generated values; they are display labels, not tissue photographs. Photographic colour must come from the separate source microscopy data, inside its supported registered extent, with fixation/staining/embedding limits explicit.

Original NRRD declarations are retained. Microscopy is an LPS three-channel vector volume (3×792×792×346, declared 0.05×0.05×0.15 mm). Registered CBCT volumes use LPS axes with negative x/y directions at 0.125 mm sampling. Segmentation is a RAS list-axis volume (13×641×579×475) with per-segment names/layers/values; it is not a single flattened label volume. Bone PLY explicitly declares RAS. Other mesh frame conventions and all source volume payload/mesh/colour registration still require independent reconciliation. Header identity or matching names do not establish full anatomical extent or true tissue thickness. All clinical/anatomical coverage remains unapproved.

Eight acquisition/binary-geometry/layered-header tests pass in the scientific runtime. The default runtime passes three acquisition tests and skips the optional NumPy geometry module. No source mesh, scalar, photographic texture or clinical approval is promoted to runtime by this inspection.

## Original registered volume payload and colour-domain audit

All five original registered NRRD payloads were decoded with bounded memory into the ignored cache. Every one of 4,413,318,357 decoded bytes matched separate gzip/zlib streaming and actual written-file readback. Scalar endian/index sentinels and declared payload counts were checked. Source samples were not reordered, resampled, repaired or flattened. The RGB/vector and list axes remain distinct.

All 13 source segmentation channels were inspected against their numbered metadata extents, which matched their complete foreground bounds. The old file lacks explicit per-segment Layer/LabelValue fields; this absence is recorded rather than filled with guessed values. There are 773 source positions with foreground in more than one channel. All overlaps remain intact. Equivalent RAS matrices are derived from explicit original LPS or RAS declarations without changing sample coordinates; matching a declaration is not independent anatomical registration approval.

Declared microscopy-domain bounds were checked against all original mesh vertices under the recorded RAS hypothesis (explicitly declared by Bone; other mesh conventions still need registration review). Bone has 1,134,563 vertices outside those bounds, Cochleovestibular Nerve 341, Sinus Dura 16,242 and Carotis Interna 198. Other meshes' vertices are inside the declared domain. Vertex fractions are not surface-area colour coverage. Bounds alone do not prove valid raw-photo tissue support; interpolation, padding, original slice transforms and specimen preparation still require review. No clamping, invented colour or texture application is performed.

Payload and support evidence are in `ZETA-original-volume-readback.json` and `ZETA-declared-colour-support-review.json`. Eleven scientific acquisition/geometry/volume/support tests pass. The default runtime passes three acquisition tests and skips two optional scientific modules. Clinical/anatomical approval, full structure coverage and runtime promotion remain false.

## Original mesh/layer comparison and source-plane review

All original mesh vertices were sampled against their original named segmentation channels under the explicitly recorded source RAS interpretation; no fitted transform or new geometry was used. The source surface is not assumed to equal a binary 0.5 interface. Dimensionless interpolated-field residuals are recorded per model and are not anatomical distances, error estimates or clinical accuracy. Bone has 433 vertices outside the cropped segmentation sample-centre domain, but zero outside the standalone Bone volume. Other models' vertices are inside their named channels' declared domains. Cropping and upstream surface construction remain explicit rather than being repaired or padded.

The segmentation's original reference-image offset [20,3,13] reconciles its equivalent RAS matrix with the registered CBCT matrix to a maximum matrix difference of approximately 3.91×10⁻¹⁴. This is a header/crop consistency check, not independent registration or tissue approval.

Original reconstructed microscopy, embedded registered CBCT and unembedded registered CBCT were rendered in three native planes each. Actual nearest-plane indices and world locations, physical pixel aspect and CBCT display windows are saved; nearest planes differ physically across modalities. No source resampling, fitted alignment or colour enhancement is applied. The figure was visually inspected. Prepared specimen colour, embedding, reconstructed slice effects, black padding and the smaller photographic extent remain visible; the figure does not certify untreated living-ear colour or every tissue interface.

Each decoded raw cache is rehashed before geometry or visual use, so a changed cache cannot silently retain the earlier source proof. Twelve scientific tests pass, including rejection of tampered decoded bytes. Original figures remain in the ignored source cache. No new colour is applied to meshes and no runtime or anatomical leaf coverage is granted.

## Original photograph and reconstruction-position review

All 222 original microscopy TIFF files were re-read against their original member SHA and ZIP CRC. Their full-resolution frames and embedded thumbnail frames remain separately identified. Photograph 135 uses a 3606×3640 RGB frame; its embedded 160×120 thumbnail is not treated as the anatomical master. Frame 0 was exported losslessly, with every decoded pixel preserved and checked against the TIFF.

The original position table has 222 entries and its transform table 222 row-major 3×3 matrices. Nearest assignment to the declared 0.15 mm, 346-layer reconstructed grid gives 219 distinct slots and three collisions (indices 56,129,207). There are 127 slots without a nearest original photograph under that calculation. This is an explicit source-position analysis, not proof of the author's exact reconstruction or collision-selection algorithm. Both photographs at a colliding slot remain recorded; no winner is silently selected.

Original photograph 135 at position 31.96 mm was visually compared with the preserved reconstructed layer 213 at position 31.95 mm. The original full frame and reconstructed image show corresponding specimen features, but they are not asserted pixel-identical or newly registered. Transform units, canvas/downsampling conventions, exact original-photo validity support, interpolation and padding remain unresolved. TIFF print-resolution tags are not microscopic physical calibration. No clamping, invented colours or texture application is performed.

Photograph/frame/position/transform evidence is saved in `ZETA-original-photo-reconstruction-review.json`. Sixteen scientific acquisition, geometry, volume, cache and photograph-position checks pass. Full source colour registration and clinical/anatomical approval remain pending.

## Recorded photograph transform and original template canvas

The original XCF template was read against its acquired member hash. Its actual canvas is 3701×3701, not an assumed square size derived from TIFF dimensions or NRRD spacing. Original photograph 135 and reconstructed layer 213 were checked under two explicit matrix-direction hypotheses using that canvas. Only the recorded 3×3 matrix or its inverse was used; no translation, rotation, shear or scale was fitted.

With the recorded matrix interpreted as raw-to-template, diagnostic RGB RMS is about 50.34 and mean absolute difference 26.55 on the 0–255 scale. Interpreting it as template-to-raw gives closer correspondence: RMS about 21.74 and mean absolute difference 5.59. Both results and their raw-domain masks are retained. This supports the latter direction as a candidate for this frame, but does not establish exact author reconstruction, resampling, edge padding, microscopic calibration or anatomical accuracy. Diagnostic bilinear sampling is not a replacement source image or newly registered volume.

Matrix-direction, pixel-centre and singular-matrix rejection tests bring the scientific checks to nineteen passing. Evidence is saved in `ZETA-recorded-photo-transform-comparison.json`. No source pixel file, mesh texture, clinical approval or structure coverage is changed.

## Offline source-reconstructed colour samples and visual findings

Source-reconstructed RGB samples were prepared for all 13 original meshes, retaining all 7,349,910 triangles. Sampling uses the original equivalent RAS grid and trilinear interpolation, rounded to uint8. No coordinate clamping, extrapolation, fitting, mesh smoothing or geometry changes occur. RGB and separate support-byte files pass exact serialized readback. Unsupported vertices are marked neutral, and a face must have all vertices inside the declared domain to qualify for sampled-colour display; crossing faces remain wholly neutral. This avoids a display that interpolates purported photograph colour across a missing source boundary.

Bone requires 2,280,053 neutral faces; Cochleovestibular Nerve 737, Sinus Dura 33,154 and Carotis Interna 461. Counts are not surface-area colour coverage or anatomical approval. Source preparation, reconstruction interpolation, unresolved frame/canvas conventions and tissue validity remain explicit. These are author-reconstructed volume samples, not independently validated raw or living-tissue colours.

The twelve smaller anatomical surfaces were rendered with all their original faces in an offline review sheet. Full Bone geometry and colour/support samples remain retained, but this sheet does not claim to render or approve its full surface. Visual inspection revealed black/background or embedding-like sampled regions within the declared bounds, especially on Sinus Dura. Thus inside-volume support is insufficient to call a sample anatomical tissue colour. No sampled texture is promoted to the reader. Further original specimen/photograph support and registration review remains required rather than removing inconvenient source features or inventing replacement colours.

Twenty-two scientific checks pass, including interpolation/channel identity, missing-domain retention and whole-face neutral handling. Review evidence is in `ZETA-source-colour-sample-review.json` and `ZETA-offline-colour-display-review.json`; arrays and the PNG remain in the ignored cache. Clinical approval and structure coverage remain false.

## Partial original-geometry reader reference

All thirteen original surfaces are now available in the temporal-bone reader with exact source float32 positions and original face bytes. Display normals are generated without changing geometry. The complete 7,349,910 triangles, including Bone's two zero-area faces, remain. The full 7,120,812-triangle Bone layer loads on demand; it is not replaced by a decimated subset. Source registered coordinate views use specimen labels rather than asserting patient anterior/lateral/superior directions or independently verified laterality.

The verified original microscopy photograph 135 is attached as a prepared-cadaver source reference. It remains a lossless decode of the full TIFF frame, not a new clinical CT/MRI figure or a mesh texture. A separate reference-only specimen-photo rights entry proves licence/bytes while being excluded from all clinical structure-coverage candidates; attempts to attach coverage to that rights record fail. Model assets remain pending anatomical review with empty coverage.

Unvalidated reconstructed texture stays withheld. Grey is a display label. Full tiny wall/joint/branch, tissue thickness, every device/lesion interface, pathology and function are not inferred from this specimen. Both acquisition-stage and preparation limitations remain visible. The source-reference CDN inventory now verifies 47 exact mesh contracts. Fifty-six reader, rights separation, source, hosted-layout, review-queue and scope tests pass. On a 390-pixel viewport, source camera controls and the full Bone layer were inspected with no horizontal overflow or browser errors; all thirteen served mesh hashes and the microscopy hash match. Local integration only, not deployed or clinically approved.
