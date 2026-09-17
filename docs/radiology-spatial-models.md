# Radiology spatial companions

Added 2026-09-17; ported onto the current reporting-reference release. The existing 84 illustrated lessons (168 responsive WebPs)
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
media audit passes; 24 focused Python tests pass. The release geometry checker
covers the three radiology spatial scenes, including exact section-contour, oblique-diameter
and translated fracture-face invariants for the new companions.

The original checkout passed 17 spatial scenes. Release verification covers the
three radiology scenes on desktop and mobile, including
parameter extrema, drag/touch, keyboard, reset, label bounds and source hashes.
Screenshots and report: `/tmp/primer-radiology-release-browser/`. The three new
scenes were visually inspected; the vessel starts orthogonal to avoid an
edge-on initial plane. No deployment was performed in this update.
