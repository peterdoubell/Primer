# Independent source-label correspondence review

All 27 existing locations were compared with the six unchanged originals and retained publisher captions. Original/source-review/runtime JPEG bytes match, dimensions match, and all rectangles are in bounds. No mislabeled chamber, IVC or swapped Doppler panel was found.

Four arrow rectangles should include more of the original arrow. Coordinates are original JPEG [x,y,width,height], top-left origin:

| Figure and location | Current | Recommended | Finding |
|---|---|---|---|
| fped g007 / 4 | [145,97,31,21] | [117,93,52,26] | Shaft and upper edge cropped |
| fped g008 / 5 | [76,134,25,27] | [44,134,55,26] | Left shaft cropped |
| fped g003 / 0 | [187,184,18,27] | [182,186,21,31] | Tail cropped |
| diagnostics g004 / 1 | [107,358,24,38] | [103,363,30,29] | Minor clipping of faint tail at x106 |

The first three are confirmed both visually and by high-confidence red-pixel bounds in review.json. The fourth is a native-resolution visual review and grayscale-pixel inspection; surrounding ultrasound texture prevents a clean color-based annotation segmentation. Recommendations include modest padding without drawing a tissue boundary.

Two right-panel atrial-collapse arrows in g008 remain unlocated. Optional new rectangles: RA [422,177,56,26], LA [571,190,49,41]. They are supported by the publisher caption and must remain publisher-identified observations.

Current semantic descriptions agree with the source. [Frontiers figures 3,7,8,11,13](https://www.frontiersin.org/journals/pediatrics/articles/10.3389/fped.2017.00079/full) were checked online and against retained JATS. The [Diagnostics figure4](https://www.mdpi.com/2075-4418/13/4/767) caption was checked in retained JATS and publisher/PubMed search evidence; direct publisher/PMC page access failed.

This review establishes source-annotation correspondence only. It supplies no tissue segmentation, independent clinical approval, 3D registration, acquisition adequacy or full reportable-structure coverage. Static crops cannot validate timing or transfer findings to a current patient.

Additional explicit names in figure13 are the schematic inflow headings Mitral [7,22,25,11] and Tricuspid [7,96,34,11]. These names locate trace headings, not valve leaflets. No other complete unlocated anatomical text was found. A duplicate IVC fragment at the bottom of figure11 is clipped by the original image boundary.

For more complete signal context, expand g007/location5 to [353,122,414,183], g011/location1 to [404,107,363,156], and g003/location1 to [403,118,261,155]. These preserve instrument scales and ECG where present. The full unchanged figure is already visible, so no present diagnostic-measurement claim is contradicted.
