# Thoracic ultrasound: side-specific diaphragm panels

Date: 2026-11-16. Status: source-reviewed, **not clinically approved**. No radiologist has reviewed these bindings.

## What was bound

The thoracic ultrasound reporting inventory has a right and a left diaphragm requirement. The stored
figure `open-thoracic-us-pmc9956010-fig29` shows both sides in one image, so it has no single side and
could not be bound to either.

The peer-reviewed caption of that figure states the side of each lettered panel:

> Visualization of the right-sided (A) and left-sided diaphragm (B) with the lateral intercostal view and
> of the right-sided diaphragm with the subcostal view (C).

Source: Safai Zadeh E, Görg C, Prosch H, Horn R, Jenssen C, Dietrich CF. The Role of Thoracic Ultrasound
for Diagnosis of Diseases of the Chest Wall, the Mediastinum, and the Diaphragm—Narrative Review and
Pictorial Essay. Diagnostics 2023;13(4):767. DOI 10.3390/diagnostics13040767. CC BY 4.0. The stored article
XML is `docs/thoracic-ultrasound-source-review-20261013/evidence/PMC9956010.xml.gz`.

| Asset | Panel | Bound requirement | Extent |
| --- | --- | --- | --- |
| `open-thoracic-us-pmc9956010-fig29-panel-a` | A | `thoracic_ultrasound.right_diaphragm` | partial |
| `open-thoracic-us-pmc9956010-fig29-panel-b` | B | `thoracic_ultrasound.left_diaphragm` | partial |
| `open-thoracic-us-pmc9956010-fig29-panel-c` | C | `thoracic_ultrasound.right_diaphragm` | partial |

## How the panels were made

`tools/anatomy_sources/package_thoracic_us_side_panels.py` crops the stored 739 × 215 figure along its white
gutters and saves each panel as a lossless PNG. No pixel is resampled. The script refuses to run if the
stored figure or the stored caption has changed.

## What was checked

- The stored caption matches the text above.
- Panels A and C show the liver beneath the diaphragm; panel B shows the spleen. This agrees with the sides
  the caption gives. This is a consistency check by the packaging author, not an anatomical review.

## Limits

- Each panel is one modest-resolution still through one acoustic window. Coverage is recorded as partial.
- The other six thoracic ultrasound requirements (pleura, pleural fluid and lung base on each side) remain
  unbound. No stored open figure states a side for them.
- `inverse.json` records the exact bytes added to `data/radiology/radiology-asset-evidence.json`.
