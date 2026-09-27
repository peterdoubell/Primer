# Independent injection atlas source review

27 September 2026. Acquired the complete publisher PDF of Lungu and Moser
(2015), *A practical guide for performing arthrography under fluoroscopic or
ultrasound guidance*, DOI 10.1007/s13244-015-0442-9.
[Primary article](https://link.springer.com/article/10.1007/s13244-015-0442-9).
The article and PDF grant CC BY 4.0. Figure 10 has no contrary caption credit.

The article predominantly illustrates fluoroscopic approaches and diagrams.
Those cannot be relabelled as ultrasound evidence. Its actual ultrasound
example, Figure 10 on PDF page 6, depicts an effusion-distended first MTP dorsal
recess and aspiration. The figure does not solve the knee ultrasound gap.

Inspection found a source-caption discrepancy: the figure is titled as first
metatarsophalangeal anatomy, but one sentence names a metacarpal. The pixels
include an MTP1G label. Do not assign this foot example to the hand or wrist,
interpret the suffix as independently confirmed laterality, or quietly rewrite
a caption presented as verbatim. Any future presentation needs explicit
acknowledgment of the inconsistency and a narrow target selection.

Panel a supplies a possible local recess example; panel b shows the needle
within the depicted aspiration sequence. This is pathological/procedural
context, not normal anatomy or proof of successful delivery in another patient.
Individual age, sex and acquisition spacing have not been established. The
source does not establish complete cartilage, capsule, tendon or neurovascular
coverage, and contains no clinical 3D dataset.

The current injection inventory groups carpal/digital targets generically;
first-MTP scope must be reconciled explicitly before a binding is accepted.
No requirements were removed, no images promoted, and no clinical review
approved. The native figure has now been preserved; site-scope reconciliation remains.

[Source fingerprint and image-object inventory](msk-lungu-injection-source-review/source-review.json).
[Inspected source page](msk-lungu-injection-source-review/page6.png).
Original PDF: `/tmp/primer-msk-sources/lungu2015/article.pdf`.

## Native figure preservation

The complete two-panel Figure 10 is PDF page 6 `/Im1`, object 49: 1302 × 499,
8-bit DeviceGray with Flate compression. There is no Decode inversion, colour
profile, image mask or soft mask. The decoded grayscale samples were packaged
as PNG without resampling, contrast changes, new labels or anatomical editing.
An independent Poppler `pdfimages -png` extraction matches every decoded pixel.
Both panels and the original labels/acquisition marks match the inspected page.
This is a disclosed lossless format adaptation, not unchanged PDF stream bytes.

[Preserved figure](msk-lungu-injection-source-review/first-mtp-ultrasound-lungu-fig10.png) ·
[Pixel preservation proof](msk-lungu-injection-source-review/figure10-preservation.json).

Credit for this retained figure: Eugen Lungu and Thomas P Moser (2015),
*A practical guide for performing arthrography under fluoroscopic or ultrasound
guidance*, Insights into Imaging 6:601–610, Figure 10,
DOI 10.1007/s13244-015-0442-9. [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
Extracted from PDF to lossless grayscale PNG; original pixels and panel layout
retained. The source caption inconsistency described above remains disclosed.

The current generic digital-joint requirement has separate recess, extensor
tendon and collateral-ligament leaves. This figure does not substantiate all
of them, does not resolve every named joint, and must not satisfy that group
through a parent label. No runtime evidence binding or clinical approval was
created by preserving the file.
