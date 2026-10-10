# Independent cervical-cancer source review - 10 October 2026

This review examines the 32 original-source figure rows in
`docs/cervical-cancer-source-review/source-figure-contract.json` independently
of the packager's preservation assertions. The evidence is the original
article XML, publisher PDF image objects, original publisher JPEGs, source
ICC profiles and primary publisher figure captions. Original PDFs were read
from the ignored parent-workspace directory
`.research/cervical-cancer-source-20261010`; none is redistributed in this
figure package.

The review found and verified corrections for three concrete provenance and
preservation defects: an incorrect vector-overlay explanation for one normal
figure, academic editors included as authors, and missing source ICC profiles
in 20 native-PDF JPEG outputs. All 32 final rasters pass independent original
sample, annotation, profile and browser-decoding checks. Image transport, caption
preservation and this source review do not grant clinical, every-structure,
histological-layer, measurement or patient-specific 3D approval.

## Primary rights evidence

The original permissions nodes explicitly grant CC BY 4.0 for the four
articles. Original source XML and PDF MD5 values match the publisher metadata,
and the retained XML is byte-identical to the staged primary XML. No selected
figure has a separate permissions/attribution exception, and the complete
captions were reviewed for third-party credit. The included selections are:

| Primary publication | Included original figures | Source grant |
| --- | --- | --- |
| [Shakur, Lee and Freeman, 2023](https://pmc.ncbi.nlm.nih.gov/articles/PMC10605640/) | 1-18 | CC BY 4.0 |
| [Fischerova and colleagues, 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC10886638/) | 1, 2, 3, 4, 6, 8, 10, 11 | CC BY 4.0 |
| [Chen, Kitzing and Lo, 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC11171278/) | 1-2 | CC BY 4.0 |
| [Maciel and colleagues, 2020](https://link.springer.com/article/10.1007/s00330-020-06750-8) | 3, 4, 6 | CC BY 4.0 |
| [Kinkel, Ascher and Reinhold, 2018](https://link.springer.com/chapter/10.1007/978-3-319-75019-4_3) | 3.1 only | Chapter CC BY 4.0, reviewed with its third-party exception |

The 2018 chapter's last page grants CC BY 4.0 but explicitly excludes material
with a separate third-party credit. Figure 3.1 has no such credit. Figure 3.2
is attributed to the ESHRE/ESGE consensus publication and is not admitted here.
The [original consensus XML](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC3718988/fullTextXML)
identifies CC BY-NC 2.0 in both its license URL and license reference even
though its prose uses generic Attribution wording. That discrepancy is not
resolved by assuming the chapter's broader grant supersedes the credited
material. The [CC BY 4.0 terms](https://creativecommons.org/licenses/by/4.0/)
allow commercial reuse with attribution; [CC BY-NC 2.0](https://creativecommons.org/licenses/by-nc/2.0/)
has a noncommercial restriction. Only the independently reviewed normal
Figure 3.1 image object is retained; the whole chapter PDF stays ignored.

The primary XML distinguishes article authors from academic editors. The
initial attribution incorrectly added Athina Tsili to the 2023 article, Vito
Andrea Capozzi to the imaging update, and Andrea Giannini, Emma Allanson and
Ming Yin Lin to the normal/staging review's authors. These are explicitly
editor contributions in the original XML. Correct author lists must filter
`contrib-type="author"`; retaining the original XML unchanged is appropriate.

## Original samples, annotations and color interpretation

An independent reader checked all 32 runtime file hashes, dimensions and
decoded sample hashes against original source objects or complete publisher
JPEGs. Every saved compressed image stream decompresses to the exact original
PDF object's encoded bytes. Native Flate RGB samples match the lossless PNG's
decoded pixels. Original ICC evidence also matches its PDF object. The first
pass found no crop, resize, pixel enhancement, new arrows or dropped panels.
The initial runtime total was 13,964,042 bytes.

The normal 2024 Figure 1 publisher master is 795 x 660 pixels. PDF image
object 88 is a separate 767 x 637 rendition that already contains the colored
circles and panel letters. Independent bare-object inspection and the PDF
drawing list show that the circles are burned into that image; they are not
separate vector overlays. The publisher master is a valid complete original
figure, but its provenance must not claim that object 88 loses those circles.

Figure 2 differs materially. PDF image objects 125 and 126 contain the complete
image portions but omit seven separate vector arrows. The PDF page shows those
arrows, and the original 725 x 580 publisher JPEG retains all of them with
panels A-E. Using the unannotated bare objects would have lost precisely the
stromal, vaginal and mucosal comparison annotations that the caption discusses.
The full publisher master therefore remains the correct source for Figure 2.

The first pass also found 20 JPEG files with no embedded ICC profile despite
their PDF image objects having an explicit color space. Seventeen 2023 MRI
figures and the imaging update's schematic Figures 2/8 use Adobe RGB (1998);
the 2018 normal image uses the grayscale Dot Gain 15% profile. The package's
seven Flate-derived PNGs already carry the exact source profiles. Profile files
in review evidence alone do not inform a browser decoding an untagged JPEG.

An independent LittleCMS comparison demonstrates the consequence. Interpreting
the 2023 Figure 1 samples with their original profile, then mapping them to
sRGB, differs from treating the same samples as untagged RGB by up to 10/255
per channel, affecting 74.56% of pixels. The normal 2018 figure differs by up
to 35/255, affecting 99.56%. These are diagnostic comparisons, not proposed
edits to the clinical images. The fix must retain the exact original image
samples and restore their original profile metadata, without color conversion
or JPEG recompression. The [W3C image specification](https://www.w3.org/TR/png-3/#11iCCP)
distinguishes sample values from their color interpretation.

## Modality, case and clinical boundaries

The imaging update's complete figures are composites. Their MRI panel sets
are Figure 1 b/e/h/i, Figure 3 d/e/f, Figure 4 b/d, Figure 6 b, Figure 10 c/d,
and Figure 11 a/b/d. Ultrasound, CT and PET panels remain separate ancillary
observations; Figures 2/8 are drawings. These assignments match the primary
captions and visible source labels. A complete composite is not an MRI-only
frame, a registered acquisition or a new 3D model.

Source case groups must retain these distinctions:

- The 2023 Figure 11 comparison explicitly separates panel a from the patient
  in panels b/c. Bullous edema in one case cannot be borrowed as mucosal
  invasion in the other. Figures 14-16 depict brachytherapy devices and
  positioning, rather than pretreatment findings. Figure 18 explicitly follows
  one patient across staging, treatment and later recurrence.
- The imaging update's Figure 4 separates its two age-specific patients. Its
  3 cm/T1b1 wording is retained as source terminology without automatic
  restaging. Figures 1/10 have an explicit same-case link. Figure 11's fused
  views are labeled PET-MRI in the image and much of the caption, with one
  PET-CT wording discrepancy that remains visible rather than silently
  generating a different acquisition label.
- The congenital-anomaly figures remain separate variant/planning examples.
  Figure 4 explicitly compares the same patient and scanner on separate
  examinations; it does not establish registration of those acquisitions.

The normal 2024 caption labels its orange-circled region cervical mucosa with
high T2 signal; the 2018 zonal description distinguishes bright canal mucus
from intermediate-signal mucosa. These source descriptions are retained
individually. They do not supply histologically verified 3D layer boundaries
or justify transferring an annotation to another donor or patient.

The contract expressly withholds native acquisition arrays, independent
calibrated measurements, source-panel registration, current-patient findings
and biological 3D reconstruction from the artwork. It preserves original
author measurements and stage labels as author annotations. Its package-wide
clinical, complete-reporting-anatomy, every-structure, fine-3D-layer and
patient-calibration/lesion-registration approvals remain false. In particular,
the 2018 caption's 3D T2 acquisition describes the source method: the admitted
asset is still only one published 2D reconstruction bitmap.

## Correction verification

All three defects have been corrected and independently rechecked. The source
master explanation distinguishes the burned-in circles of normal Figure 1
from the seven separate PDF arrows of Figure 2. Article attribution now lists
only the original XML's author contributions.

The 20 affected JPEGs carry their original PDF ICC profiles through APP2
metadata. Removing only the inserted ICC APP2 blocks recovers the original
JPEG bytes exactly, including the unchanged image header, quantization tables
and entropy-coded samples. Every decoded raster remains sample-identical to
its original master. All restored profiles are byte-identical to the original
PDF profile; the seven PNG profiles and two complete publisher JPEGs also
retain their original source state. The final runtime total is 13,975,954 bytes,
an increase of 11,912 metadata bytes with no image-sample changes.

Actual Chromium 151.0.7922.34 decoding was checked for all 32 runtime rasters.
Each browser canvas result is RGB-identical to a separate lossless fixture
made from the original master samples and original source profile. An
additional independent LittleCMS conversion to sRGB differs from Chromium by
at most 1/255 in the Adobe RGB figures and 2/255 in the Dot Gain figure; the
other figures match exactly. This isolates decoder/color-engine rounding from
the earlier missing-profile error. The comparison uses the complete figures
at native resolution and includes all original annotations. It is a source
appearance check, not a diagnostic interpretation or an authenticated lesson
delivery test.

The local independent runner and diagnostic JSON remain ignored workspace
artifacts at `.research/cervical-independent-source-check-20261010.py` and
`.json`. Browser inputs, fixtures and results are also ignored. Original PDF
rendering and object inspection supplement byte/sample checks. The committed
independent summary JSON records the reviewed raster hashes and browser
comparison results without redistributing full PDFs or copying new clinical
annotations. No remaining blocker was found for this bounded source-only
preservation package. Clinical interpretation, every reporting structure,
fine 3D layers, calibrated measurements and current-patient/donor fitting
remain unapproved.
