# Nested PDF images and CMYK rendition

The four previously ambiguous image objects were found inside PDF Form XObjects:
Mezian Figure 8 and Hung Figures 9, 11 and 18. Unique source dimensions and
decoded-image comparison confirm the same panels. Their exact original JPEG
streams replace convenience exports that had introduced channel differences
of up to 4–5 levels. Native dimensions, annotations and anatomical claims remain
unchanged. The audit tool now traverses nested forms with a bounded depth.

Valgaeren Figure 2 is different: its PDF uses a DeviceCMYK/YCCK image. Displaying
the raw JPEG outside the PDF inverts its intended colour interpretation. The
old convenience export had re-encoded the image and cannot be called an original
JPEG stream. The runtime now uses Poppler 26.07.0's native-size RGB PNG extraction
(`pdfimages -f 4 -l 4 -png`). It was visually compared with the complete rendered
PDF page: grayscale anatomy, yellow arrows and a/b labels agree. Dimensions stay
1511 × 838; there is no resampling, crop, reconstructed detail or extra JPEG loss.
This is explicitly a colour rendition, not an unchanged encoded source image.

The original CMYK stream, old/new hashes, source PDF page/object and decoding
method remain documented. The original stream is held in the review folder for
provenance and requires its PDF colour semantics; it is not a clinical web asset.
The superseded runtime JPEG is retained offline. Current catalogue and evidence
records point to the new PNG and retain all source and population limits.

No requirements, anatomical bindings or clinical approval changed. Exact source
bytes and faithful PDF rendering are distinct checks; neither establishes
clinical completeness or diagnostic accuracy.

## Source-image appearance and verification

Actual browser inspection revealed that the night-reading theme applied
`brightness(0.86) contrast(1.04)` to enlarged medical images. Source radiology
figures now carry an appearance marker into enlargement and bypass decorative
glare/inversion filters. The reader's theme stays unchanged. The observed
computed filter is `none` in both the gallery and enlarged view while the
night-theme filter variable remains active. Non-source reading images retain
their existing behaviour.

All five updated figures opened and decoded at their native dimensions on the
actual elbow and ankle reporting pages. HTTP bytes match their new hashes;
browser errors were absent. The triceps PNG was inspected against the rendered
PDF and in the desktop and 390-pixel mobile dialogs. The mobile page has no
horizontal overflow. Regression checks passed 197 tests; the browser checker
now also asserts that source figures are not filtered during enlargement.

The repeat extraction audit finds 23 original whole-figure JPEGs; the separately
documented CMYK-to-PNG case completes this bounded set of 24. Other cropped or
non-JPEG source objects remain outside this pass. Requirement and figure counts,
source populations and clinical approval states are unchanged.
