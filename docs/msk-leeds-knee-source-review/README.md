# Leeds Knee 2: preserved source review

This is an offline technical review of the acquired Leeds `LTKN8941` research
source. It does **not** establish clinical approval, normal anatomy, a direct
MRI-to-model transform or a replacement for the current runtime anatomy.
The full MSK reporting requirements remain unchanged.

## Evidence and images

- [Acquisition and native MR findings](../msk-leeds-knee-source-progress.md)
- [Quadratic geometry audit](geometry/geometry-audit.json) and
  [array integrity checks](geometry/array-verification.json)
- [Independent direct-input geometry check](geometry/independent-geometry-check.json)
- [Safe acquisition/frame/pixel audit](imaging/imaging-audit.json) and
  [native PNG readback verification](imaging/render-verification.json)
- [Six native MRI review frames](imaging/native-source-frames-contact-sheet.png)
- [Whole author assembly](visual/leeds-author-assembly.png),
  [tibial cartilage and menisci](visual/leeds-tibial-cartilage-menisci.png), and
  [femoral cartilage with bone](visual/leeds-femoral-cartilage-bone.png)
- [Rendering method and limits](visual/README.md) and
  [render fingerprints](visual/rendering-evidence.json)

[Preservation manifest](preserved-evidence.json) records the exact copied bytes.
The original DICOM, INP and complete quadratic mesh arrays remain in source
staging; they are not embedded in this documentation or the application.
The MRI audit reports the presence of potentially identifying fields without
their values. Only six inspected pixel frames are shown on the contact sheet;
that inspection does not clear all DICOM metadata or all frames for release.

## Source credit and adaptations

Copyright 2023 University of Leeds. Cooper RJ, Day GA, Wijayathunga VN, Yao J,
Mengoni M, Wilcox RK, Jones AC. *Three subject-specific human tibiofemoral joint
finite element models: complete three-dimensional imaging (CT & MR),
experimental validation and modelling dataset.* University of Leeds.
[DOI 10.5518/981](https://doi.org/10.5518/981),
[source record](https://archive.researchdata.leeds.ac.uk/1082/).
The dataset README grants [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
No endorsement is implied.

The MRI contact sheet applies a disclosed fixed display window and places
native pixel frames without resampling. Figure labels are outside those source
pixels. The model figures add projection, lighting and colours to the author's
baseline assembly. Their four-triangle display of each six-node face is
explicitly approximate; exact quadratic arrays remain the audit representation.
Neither adaptation adds anatomical detail or a clinical validation claim.
