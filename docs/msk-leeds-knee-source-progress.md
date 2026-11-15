# Leeds knee source acquisition and imaging audit

Reviewed 27 September 2026. **Acquired research candidate; no clinical replacement
or release clearance established.** The completed source downloads were reused.
No runtime asset, catalog binding, evidence approval or requirement was changed.

The subsequent [preserved review package](msk-leeds-knee-source-review/README.md)
includes the geometry audit, independently checked counts, safe MRI metadata,
native frame contact sheet and three inspected model projections.

## Exact source and reuse basis

The [University of Leeds dataset, DOI 10.5518/981](https://archive.researchdata.leeds.ac.uk/1082/)
is *Three subject-specific human tibiofemoral joint finite element models:
complete three-dimensional imaging (CT & MR), experimental validation and
modelling dataset*, Cooper, Day, Wijayathunga, Yao, Mengoni, Wilcox and Jones
(2023). The rights holder is the University of Leeds. The
[dataset README](https://archive.researchdata.leeds.ac.uk/1082/1/README_Cooper-etal_2023.pdf),
p2, explicitly grants [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)
for this dataset. The README enumerates the acquired archives. Attribution,
source and licence links, and disclosure of derivative display changes remain
necessary; the licence is not evidence of anatomical accuracy, de-identification
or clinical suitability.

All three completed ZIPs were independently rehashed, compared with the saved
download records, and decompressed for **all-member ZIP CRC validation**:

| Acquired file | Exact bytes | SHA-256 |
|---|---:|---|
| [Knee 2 FE models](https://archive.researchdata.leeds.ac.uk/1082/5/1-LTKN8941_FE_model_INP_files.zip) | 71,895,079 | `5ebb964179fd12b337b36bd29438c102db05c1300a1f8b70e7368608bd62a03d` |
| [MR preview slices](https://archive.researchdata.leeds.ac.uk/1082/36/6-Knee_MR_preview_slices.zip) | 12,924,914 | `9d0db0742ab39ef22f1ee8237d6c2b4b2deaca76e78298078eba242fc02d8a8f` |
| [Knee 2 DESS MR](https://archive.researchdata.leeds.ac.uk/1082/38/6-LTKN8941_MR_DESS.zip) | 19,682,907 | `932f42f6312c57c8574bf03a343344c1a408b6f54df07dae433cb315adc31ad3` |

The SHA-256 values are computed local provenance pins, not claimed publisher
checksums. The repository response ETags match computed MD5 values, and response
Content-Length values match the exact bytes. The ZIPs contain 9, 24 and 2 entries,
respectively, including directories. Existing acquisition timestamps are
26 September 2026 UTC. No second download or multi-GB CT acquisition occurred.

Original files remain under `/tmp/primer-msk-sources/leeds-knee-981/`. The
documentation PDF hashes were also verified against the acquisition records:

| Source document | SHA-256 |
|---|---|
| `README_Cooper-etal_2023.pdf` | `006b93d280710d8e45d22853dae11bdbec60267af89c0ac024311ff9c416ac0f` |
| `method_documentation.pdf` | `e50687b1ebeb908dc6c1b27a9b3ac90488b8ead8073eb53b033928ec16587966` |
| `specimen_codes.txt` | `2f96c391c7d6df9d1ded1fd15bc9a0cb7f0b13eb4746d180b90d6253f3bd7ada` |

## Actual MR acquisition and scanner discrepancy

The DESS archive contains one **Enhanced MR Image Storage** DICOM object,
`LTKN8941_MR_Series_7_DESS_PC_Knee2/87390321`, rather than 144 independent files.
Its 42,757,060 bytes match the complete archive member byte for byte; ZIP CRC32
is `57aceff0` and SHA-256 is
`a7597d0a43ca39b787bba910b090f85f650478f4dc4f4a32cc08f0d8c761e61f`.

The selected object's safe acquisition metadata records:

| Attribute | Stored evidence |
|---|---|
| Modality and acquisition | MR; ORIGINAL/PRIMARY magnitude; 3D; gradient echo |
| Scanner | Siemens MAGNETOM Vida; 3 tesla |
| Receive coil | `TxRx_Knee_18` |
| Timing and excitation | TR 16.3 ms; effective TE 4.7 ms on all frames; flip angle 25°; WATER excitation |
| Source sequence identity | README and archive label DESS; SeriesDescription and ProtocolName contain the DESS token |
| Standard sequence limitations | AcquisitionContrast `UNKNOWN`; SteadyStatePulseSequence `NONE` |
| Frame anatomy | FrameLaterality `L`; coded anatomic region Knee (`T-D9200`, SRT) |
| Dimensions | 144 frames × 384 rows × 384 columns |
| Sampling | 0.364583 × 0.364583 mm in-plane; nominal thickness 0.7 mm |

The DESS attribution is supported by the repository and sequence-name tokens;
the standard pulse/contrast fields alone do not fully characterize DESS. The
original raw free-text sequence values were not copied into the report.

The README p7 distinguishes Knee 1 Prisma/15-channel from Knees 2 and 3
Vida/18-channel. The [methods document](https://archive.researchdata.leeds.ac.uk/1082/3/method_documentation.pdf),
p2, generalizes Prisma/15-channel to the three knees. **The selected Knee 2 DICOM
supports the README's Vida and 18-channel description.** This resolves which
description fits this acquisition; it does not independently verify every other
series or specimen.

## Native geometry and frame progression

All 144 frames have the same ImageOrientationPatient and PixelSpacing; stack
positions run consecutively from 1 to 144 and dimension indices represent one
spatial stack. The source planes are **oblique sagittal**, with the following
directions in DICOM patient coordinates (+X left, +Y posterior, +Z superior):

| Native-array direction | Patient-coordinate vector |
|---|---|
| Increasing column / image right | `[-0.142875, 0.989741, -0.0000000110549]` |
| Increasing row / image down | `[0.0534636, 0.00771775, -0.99854]` |
| Cross product of these directions | `[-0.988295978, -0.142666403, -0.054017790]` |
| Mean next-frame displacement, mm | `[0.691806993, 0.099865734, 0.037812587]` |

The first ImagePositionPatient is `[-46.8294, -88.1614, 34.3575]` mm; the last is
`[52.099, -73.8806, 39.7647]` mm. Frame progression is opposite the IOP cross-product
normal: projected steps are −0.700096 to −0.699968 mm. Center-to-center step
lengths are 0.699968–0.700096 mm; the first-to-last center distance is 100.099987 mm.
Maximum off-normal step is 0.000110 mm and maximum residual from the mean-step
linear grid is 0.000124 mm, consistent with the stored coordinate precision.

Pixel-center coordinates are calculated as
`IPP[k] + c × PixelSpacing[1] × IOP[0:3] + r × PixelSpacing[0] × IOP[3:6]`.
Thus the review labels say image right is **predominantly posterior**, image
down **predominantly inferior**, and increasing frame index **predominantly
leftward**. No cardinal reformat or spatial transform was applied. This follows
the [DICOM Image Plane definition](https://dicom.nema.org/medical/dicom/current/output/chtml/part03/sect_C.7.6.2.html).
These coordinates establish the internal MR frame, not a transform to the FE
model or post-test CT.

## Stored pixels and inspected review images

Explicit VR Little Endian decoding produces an unsigned 16-bit array with 12
stored bits, MONOCHROME2, one sample per pixel. Pydicom's decoded values exactly
match an independent direct little-endian `uint16` interpretation of the
uncompressed PixelData. The pixel payload is 42,467,328 bytes, SHA-256
`b9c9ac920e37bf9e3de673f603f481718fca1f60b6d636b477331e018bf8818f`.

There are 21,233,664 voxels; 20,975,170 are nonzero, and all 144 frames contain
nonzero pixels. The stored range is 0–614. All frames use rescale slope 1 and
intercept 0; rescale type `US` means unspecified units, not Hounsfield units.
The DICOM reports no lossy compression. That flag does not establish absence
of scanner reconstruction or other processing before storage.

Six native frames (1-based 17, 41, 65, 89, 113 and 129) were rendered as 384 × 384
PNG files. The fixed review window is center **307.5**, width **615**, using the
[DICOM default LINEAR formula](https://dicom.nema.org/medical/dicom/current/output/chtml/part03/sect_C.11.2.html),
then rounded to 8-bit grayscale. This maps the entire observed 0–614 range to
0–255 without clipping; it is an audit display choice. The original per-frame
window centers (148–329) and widths (372–710) are retained in the audit, but not
used for these fixed-window images. There is no interpolation, resizing,
flipping, rotation, filtering, AI edit, anatomical overlay or inferred label.
The contact sheet pastes each source-plane rendering at 1:1 pixel size.
An [independent output readback](/tmp/primer-msk-sources/leeds-knee-981/imaging-audit/render-verification.json)
confirmed all six PNGs equal the direct full-range pixel mapping, contain no
PNG metadata, and match their contact-sheet crops exactly. The original DICOM
hash remained unchanged.

The [staged contact sheet](/tmp/primer-msk-sources/leeds-knee-981/imaging-audit/native-source-frames-contact-sheet.png)
was visually inspected. It shows whole-knee MR content through different native
planes, including bone contours and surrounding soft tissues, rather than a
sparse local export. No burned-in text or identifying overlay was visible in
these six inspected frames. This is not a full-volume privacy review or a
structure-by-structure clinical segmentation assessment.

## De-identification and specimen constraints

`PatientIdentityRemoved=NO` is stored. Patient-name, patient-ID, birth-date,
date/time, operator, institution and device/instance fields include populated
values, and the object contains **4,670 private elements** recursively. Only
presence states were recorded; no raw values were printed, serialized or copied
to PNG metadata. A populated field does not prove that its value identifies a
real person. Together, these indicators mean **de-identification and release
clearance are not established**. `BurnedInAnnotation=NO` is an indicator, not
clearance. The original DICOM remains unchanged and offline.

The [specimen mapping](https://archive.researchdata.leeds.ac.uk/1082/2/specimen_codes.txt)
maps Knee 2 to LTKN8941. Methods p2 describes it as a left knee from a 61-year-old
male, with “No meniscal extrusion.” That statement does not establish overall
normal anatomy or exclude other disease. Knee 1 has signs of cartilage and
lateral meniscus degeneration; Knee 3 has meniscus calcification. They must not
be silently pooled into an unqualified normal-anatomy source.

## Image-to-model limitations and next gate

Methods pp1, 4–5 state that bone/cartilage geometry was segmented from
post-meniscectomy microCT after testing; the femur/tibia were separated to aid
segmentation. MR was acquired in the intact state and registered to CT in
ScanIP. Menisci were segmented from MR and adjusted using dilation, binary
operations and curvature changes to obtain conforming contact surfaces and
convergent model solutions. Cartilage processing included morphological
operations and Gaussian smoothing. These steps matter for boundary fidelity.

No documented direct native-MR-to-FE transform was established by this audit,
and none was inferred, fitted or applied. Contact-mechanics validation does not
approve every image-visible structure, natural meniscal root attachment,
ligament, capsule or cartilage boundary for clinical reporting. The completed
FE audit below establishes its technical contents and keeps those limits explicit.

Retain this as an offline same-specimen research source. Raw DICOM distribution
needs de-identification/release review. A claimed MRI–FE pair needs a documented
and checked pairing transform. Use of any model or image as high-fidelity
reporting-component evidence needs anatomical assessment of that component
and its source processing and specimen state. These are separate questions;
the raw-DICOM metadata limitation does not automatically apply to mesh geometry.
The audit does not require acquiring all CT stacks simply to establish that
these gates remain open.

## Completed quadratic geometry review

The unchanged `ltkn8941_seg_intact_fix.inp` contains 291,045 part nodes and
180,570 C3D10 tetrahedra, partitioned exactly into seven source-labelled solid
groups. Every element belongs to one group; no part nodes are unused.

| Source group | Quadratic tetrahedra | Six-node boundary faces |
|---|---:|---:|
| Femoral cartilage | 76,059 | 41,928 |
| Femur | 41,401 | 24,752 |
| Tibia | 23,656 | 12,842 |
| Medial tibial cartilage | 15,528 | 6,974 |
| Lateral tibial cartilage | 15,859 | 6,086 |
| Medial meniscus | 4,597 | 2,212 |
| Lateral meniscus | 3,470 | 1,722 |

The volume has 46,328 external faces and 337,976 internal face pairs. Shared
bone/cartilage material interfaces remain on both corresponding tissue
boundaries. Six-node corner/midside associations agree across shared faces.
Each tissue boundary has one connected component, no open/nonmanifold edges
and Euler characteristic 2. These are representation/topology results, not
independent anatomical-boundary accuracy.

All ten volume nodes and six face nodes are retained in staged arrays. The
maximum midside displacement from a straight-edge midpoint is approximately
`1.036 × 10⁻⁵` native units. Thus the quadratic element order does not itself
establish extra anatomical detail in this undeformed geometry. An independent
direct parser agrees on every tissue's cell count, unique-node count, bounds
and maximum midside offset; no negative corner determinants were found.
Corner determinants do not establish positivity of every quadratic Jacobian.
The [independent checker](../tools/anatomy_sources/check_leeds_knee_geometry_independent.py)
reproduces its saved report byte for byte (SHA-256
`b4d24b1f2f42808a6e816a968842fe436322cfdd167f15ed05f1c29584cff462`).

The author instance first translates by `[114,166,0]`, then rotates 180° about
the specified parallel-to-Z axis through that point. The resulting placement
is `x′=114−x`, `y′=166−y`, `z′=z` up to floating-point rotation precision.
This is the author's initial assembly before loading displacements. It is not
a fitted registration to MRI or another atlas. Source methods use mm/MPa, but
the deck has no independent units declaration; no conversion or patient-axis
relabelling was applied.

Two assembly reference nodes and 60 SpringA elements are retained as mechanical
metadata, excluded from the seven anatomical solids. Four groups of fifteen
springs represent meniscal-root constraints. They provide no root tissue volume.
Fine horns, attachments, ligament bundles and other absent anatomy are not
reconstructed from their node locations.

[Three offline projections](msk-leeds-knee-source-review/visual/README.md)
show the complete seven-solid assembly, tibial cartilage/menisci with occluding
tissues omitted, and femoral cartilage with bone. Relative author positions
are preserved, and the display uses all six face nodes in four declared planar
triangles per face. Whole-tissue shapes and the source-limited bone ends are
visible; the whole-assembly view obscures much of the menisci. No viewport
clipping or stray display fragments were observed. Surface fidelity, exact
patient-axis identity and MRI correspondence remain unverified.

The [geometry audit tool](../tools/anatomy_sources/audit_leeds_knee_geometry.py)
and twelve analytical tests cover quadratic interpolation, edge-associated
midside topology, surface components, author-transform order and strict input
handling. Three MRI-audit tests verify native stack direction, missing-position
rejection and non-disclosure of identifying values. All fifteen passed in the
scientific runtime. In the production Python environment the two optional
scientific test modules skip without installing new dependencies.

**Suitability decision:** keep the Leeds source and these review artifacts
offline. They establish a reproducible research source with an explicit
commercial-use copyright grant,
but do not yet demonstrate a clinical improvement for an exact missing
reporting component. No model, image or component binding was promoted into
the application. A direct MRI–FE comparison would require the source
registration; fine root anatomy requires a different anatomical source.

## Reproduction

The [audit tool](/Users/peter/Documents/ChatGPT/Primer/tools/anatomy_sources/audit_leeds_knee_imaging.py)
verifies all three archives and the documentation, compares the extracted DICOM
with its full archive member, checks every frame's geometry and pixel decode,
and regenerates the safe JSON and native review PNGs. It performs no downloads
and writes only the selected audit output directory.

```sh
PYTHONPATH=/tmp/primer-msk-sources/audit-python:/tmp/primer-msk-sources/python:/tmp/primer-msk-sources/leeds-knee-981/python-deps \
  /Users/peter/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12 \
  tools/anatomy_sources/audit_leeds_knee_imaging.py \
  --source-root /tmp/primer-msk-sources/leeds-knee-981 \
  --output /tmp/primer-msk-sources/leeds-knee-981/imaging-audit
```

The [safe imaging audit JSON](/tmp/primer-msk-sources/leeds-knee-981/imaging-audit/imaging-audit.json)
preserves all per-frame IPP/IOP/spacing/window records, acquisition allowlist,
archive/member CRCs and hashes, pixel counts and output hashes. Original DICOM
metadata is deliberately not dumped. No external contacts were made.
