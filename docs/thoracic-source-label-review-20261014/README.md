# Original thoracic source label correspondence

This companion maps 27 original publisher labels, arrow locations and signal/observation panels in six published figures to their native JPEG coordinates. It adds inspectable correspondence for RA, RV, LA, LV, IVC, pericardial fluid, source cardiac/respiratory signals and marked rib observations. Rectangles identify source annotations or panels, not tissue extent. No tissue segmentation, current-patient finding or anatomical 3D registration is supplied.

Serve this directory through local HTTP and open `index.html`. Figure selection preserves the entire original panel group. Selecting an annotation shows its original-pixel rectangle and a native decoded-pixel inset. The overlay can be disabled. Original JPEG bytes, dimensions, publication authors, article links and CC BY 4.0 attribution are retained; no source image is repainted or re-encoded. Failed source loads hide the previous figure and its details.

The source-authored chamber observations, inflow traces, respiratory behaviour and injury examples belong to their publications. A static locator cannot independently establish cardiac-cycle timing, quantify a patient's respiratory variation, identify valve leaflet morphology or supply a normal result. Label identification does not establish complete wall/cavity segmentation. The source resolutions limit visible detail.

Original sources and JATS/license evidence remain in `docs/thoracic-ultrasound-source-review-20261013/`. `manifest.json` records exact source image hashes and original pixel rectangles. The full scholarly figures and source captions remain the interpretive context. Every clinical or structure-completion flag remains false.

Actual browser evidence covers all 27 locators at 1440 and 390 pixels (54 cases). Native decoded crop RGBA values exactly match their source-image regions in the same browser. Measured overlay client coordinates match the original-pixel transforms, and body overflow checks pass. A failed-source test verifies that stale images are hidden. These are display-correspondence checks, not independent clinical review.

This companion is not yet integrated into the production reporting module. Remaining anatomy, schematics, 3D, acquisition adequacy and full clinical validation obligations remain open.
