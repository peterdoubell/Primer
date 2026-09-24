# Radiology spatial companions

Added 2026-09-17. The existing 84 illustrated lessons (168 responsive WebPs)
are preserved. Three local SVG-projected 3D scenes complement those plates:

- **Reading the CT Image:** move axial, coronal and sagittal planes through a
  sphere; the intersection contour follows the exact sphere/plane geometry.
- **TAVI Planning CT:** tilt a plane through an ideal access-vessel lumen and
  compare true diameter with the oblique long axis. This concerns access-vessel
  measurement, not annular sizing.
- **Describing a Fracture:** independently vary distal translation, angulation
  and displacement direction, then rotate to examine projection dependence.

All use the existing Primer spatial renderer, colours, typography, legends,
keyboard/pointer rotation, zoom, reset, text readouts and reduced-motion-friendly
rendering. They are explicitly schematic, with no downloaded assets or patient
images. The existing CT windowing activity remains available.

Clinical framing was checked against the [2022 ACC/AHA aortic guideline](https://www.ahajournals.org/doi/10.1161/CIR.0000000000001106)
and [AO Surgery Reference](https://surgeryreference.aofoundation.org/orthopedic-trauma/adult-trauma/proximal-femur/further-reading/assessment-of-reduction-quality-femoral-neck-fractures).
No management thresholds or device recommendations are introduced.

Validation: radiology asset audit passes 84 lessons / 168 WebPs; curriculum-wide
media audit passes; 36 focused Python tests pass. The shared geometry checker
now covers 17 spatial scenes, including exact section-contour, oblique-diameter
and translated fracture-face invariants for the new companions.

Final browser verification passed all 17 scenes on desktop and mobile, including
parameter extrema, drag/touch, keyboard, reset, label bounds and source hashes.
Screenshots and report: `/tmp/primer-radiology-browser-final/`. The three new
scenes were visually inspected; the vessel starts orthogonal to avoid an
edge-on initial plane. No deployment was performed in this update.

## Reporting reference expansion — 23 September 2026

The three original companions above are preserved. The dedicated reporting
desk adds 96 module-specific companions across 35 anatomy/acquisition geometry
families. Their source, controls, limitations and checks are documented in
[radiology-reporting-models.md](radiology-reporting-models.md) and
[radiology-reporting-desk.md](radiology-reporting-desk.md).
