# Acute stroke source and anatomy work — 11 October 2026

The prior released investigation `ra.acute-stroke` was absent from the expanded
non-MSK structure requirements. Its five reporting steps used generic brain parts
and three remote source stills. The actual `rad.4.stroke` lesson has twelve quiz
items, including posterior circulation, venous infarction, internal borderzones,
DWI/ADC/FLAIR, serial fogging and collateral-phase dependencies. This work covers
those requirements conditionally and adds acquired native patient source data.
It does not establish clinical/commercial readiness or approve anatomy.

`structure-requirements-proposal.json` contains 369 named groups, 3,692 required-part
floor and 11,076 image/schematic/model obligations. None is marked fulfilled.
Every actual branch, lesion, fine component, variant and acquisition still needs
source-resolved instantiation and independent clinical/anatomical review. The
patient-dependent denominator remains unknown. Source selection does not bound it.
`curriculum-reporting-correction-proposal.json` identifies unsafe teaching absolutes
and convenience normality inserts for the parent to repair in common files.

## Complete native MRI and actual mask geometry

The CC BY4 ISLES'22 [dataset v2.3](https://doi.org/10.5281/zenodo.7153326) and
[publisher article](https://doi.org/10.1038/s41597-022-01875-5) establish the source
rights and processing context. All eight published case0140 members are retained:
DWI/ADC/FLAIR NIfTI, original expert mask, three scanner JSON files and the original
case snapshot. This is one 82-year-old male source patient, not the current reader.
The published NIfTI grids were skull stripped and returned to their native spaces.
Original scanner dimensions in JSON can differ from the released NIfTI arrays.

All 5,716,736 stored samples are preserved: 915,712 each for float64 DWI, float64
ADC and uint16 mask, and 2,969,600 float32 FLAIR values. DWI/ADC/mask affines agree;
FLAIR has a separate grid with no overlay or cursor registration asserted. ADC
units, individual acquisition/onset timing, treatment state and artery diagnosis
are unknown. Identical stored affines do not prove motion-free biological alignment.

The 3D model is the literal union boundary of every source mask=1 voxel cell at
index ±0.5 transformed by the exact source affine: 18,113 float64 vertices, 36,788
triangles and 18,394 exposed faces. No original component is omitted: five under
6-connectivity and three under 26-connectivity. The label volume of about 141.368mL
is a source annotation volume, not a measured pretreatment core or irreversible
injury. Source 2mm sampling, edge/corner contacts and possible voxel-cell
nonmanifold contacts stay explicit. No smoothing or higher resolution is implied.
The native inspector shows source RAS orientation, complete arrays and geometry.

The ZIP is 1,692,717,470 bytes and the record advertises MD5
`302ee280373cdd5c190ab763d72a7a50`. A whole-archive download was deliberately stopped
after byte-range support was confirmed. The original archive tail and its complete
3,190-entry central directory were acquired by an exact HTTP206 range. Eight selected
members were extracted from the preserved partial original prefix or exact range
responses, checking local headers, original central-directory size and CRC32.
Per-member SHA256 and receipts are retained. **The whole archive MD5 was not checked.**

## Complete native publication artwork

The CC BY4 [CTP pictorial review](https://doi.org/10.3390/diagnostics13030447) supplies
all thirteen numbered figures, the full unchanged 20-page PDF and thirteen original
publisher JPEGs. All 22 selected native PDF raster objects are retained as encoded
streams and original-dimension RGB images. Whole figures use exact top/bottom strip
assembly where the publisher split a figure into strips. No source raster is
cropped, scaled, repainted, filtered or annotated. The complete native displays
contain 17,052,901 RGB pixels; PDF vectors/text and all original stream bytes remain
in the unchanged PDF. Figures are separate patients unless the caption says otherwise.
Figure6 includes next-day DWI, not a registered CT/MRI overlay. Figure13 includes
motion timepoints and source reprocessed map sets, not recoverable numerical maps.

Independent pypdf raw Flate/palette decoding matches all corresponding RGB samples.
Independent Pillow decoding of the original JPEG streams differs from MuPDF in a
small number of channels by at most one level; decoder rounding is disclosed, and
all original encoded bytes remain. This is a decoding distinction, not an anatomical
edit. Calibrated HU, original numerical perfusion maps, full CT/CTA volumes and native
publication patient meshes are absent. The source diagnostic captions are not a
current-patient assessment or an anatomical coverage grant. Static printed 3D views
are never converted into asserted patient meshes.

## Verification and open scope

Six tests independently compare original CRC/SHA, every stored array byte and affine,
every exposed mask-cell face, signed volume, browser exact typed reads, all 22 source
strips/all13 complete figures and every literal current quiz dependency. Desktop1440
and mobile390 standalone browser checks exercise all three sequences, separate grids,
source values, numeric/range/keyboard controls, invalid drafts, camera rotations,
retry, WebGL triangle counts and absence of errors/overflow. Fifty-four captured
native plane buffers (1,072,512 RGB pixels) match an independent original-NIfTI
display oracle. Eight captures are retained. This is standalone source-viewer evidence;
authenticated integrated Primer reader and production verification remain separate.

Missing: complete CT/CTA/CTP/MR-perfusion source studies with commercial reuse rights,
vascular lumen/wall/dissection and dynamic collateral native structures, complete
ASPECTS and tissue boundary labels, venous thrombosis native anatomy, susceptibility
and haemorrhagic transformation cases, independent named-anatomy approval, adequate
fine structure resolution, full pathology/variant/development coverage, and every
required image/schematic/model representation. ISLES24 was screened out because its
public release is noncommercial. ISLES18's source workshop restrictions and uncertain
commercial redistribution were not silently substituted with a mirror's licence.

All common runtime registries, curriculum and backend files are parent-owned.
No commit or Git mutation was performed by this source worker.
