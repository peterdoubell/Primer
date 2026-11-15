# Proximal rectus femoris MRI reference

Reviewed 27 September 2026. One complete source figure is added to the hip FAI
reference. It supplies a **local, unverified tendon-course candidate**; no
attachment, complete-course, normal-examination, schematic or 3D approval is
inferred. Existing reporting requirements and acquisition conditions remain.

## Primary source and anatomical selection

[Mechó et al. 2023](https://www.frontiersin.org/journals/physiology/articles/10.3389/fphys.2023.986872/full),
*Measuring direct and indirect tendon parameters to characterize the proximal
tendinous complex of the rectus femoris in football and futsal players*,
Frontiers in Physiology 14:986872, doi:10.3389/fphys.2023.986872.

[Figure 2](https://www.frontiersin.org/journals/physiology/articles/10.3389/fphys.2023.986872/full#F2)
contains axial, coronal and oblique-sagittal MRI views used for reformat planning.
The original white arrowhead in A identifies the indirect tendon margin; the
white arrow in B identifies the direct tendon margin. Those marked local
courses support `hip.rectus_femoris_tendon.visible_course` as a partial candidate.
Panel C retains reformat context. All three panels, their letters and arrows
remain intact. Attachment footprints and the entire distal course are not
established by this selection.

The cohort includes examinations with clinical indications and volunteers,
including junior/young/professional teams. A case whose acute tendon injury
prevented adequate definition was excluded, but that does not make every
included examination normal. The individual age, sex, side and pathological
state of Figure 2 are not given. They remain unknown in the evidence record.
Two MSK radiologists performed study measurements; that methodological review
is not represented as their approval of Primer's component binding.

The authors label the acquisition 3 T 3D proton-density MRI and report
2.5–3.5-mm sections with 1.4 × 0.88-mm in-plane sampling. These published values
are retained without describing the data as isotropic or claiming fine-fibre
accuracy. No new diagnostic angle or injury-risk threshold is added to the guide.

## Rights and source pixels

The primary publisher article and PDF grant CC BY; the article's licence link
is explicitly [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
The exact figure and caption contain no contrary third-party credit or reuse
restriction. The source describes the authors' own study acquisitions. Full
author/title/source/licence credit and the format adaptation are supplied with
the runtime figure. Editor and peer-reviewer names are not used as author credits
or fabricated clinical reviewers.

The PDF contains a complete 1805 × 502 JPEG at page 3, `/Im2`, object 581.
All figure annotations are embedded in its pixels, as confirmed against the
full rendered source page. The raw DCT stream matches an independent Poppler
`pdfimages -j` extraction byte for byte. The publisher's WebP is 1772 × 492;
the PDF source preserves the larger available raster.

The JPEG depends on an external **Adobe RGB (1998)** profile in the PDF and
does not embed that profile itself. Publishing the raw JPEG alone would lose
that colour interpretation. The runtime therefore uses a lossless PNG with
the exact decoded RGB samples and the original ICC profile attached. No
resizing, pixel editing, annotation reconstruction or JPEG re-encoding occurs.
The PNG is a disclosed format adaptation, not the unchanged encoded JPEG.

- Runtime: `web/reference-media/msk-open/hip-rectus-femoris-course-mecho-fig2.png`.
- [Pixel/profile evidence](msk-hip-tendon-source-review/figure2-preservation.json).
- [Source page for annotation review](msk-hip-tendon-source-review/source-page3-review.png).
- The retained `source-jpeg-requires-pdf-icc.jpg` is encoded-stream evidence;
  its colour interpretation requires the recorded PDF profile.

Source PDF SHA-256: `463b31950b0112e0341bcf4f310fc9aa66d4bfc65858863225f2d1cafcd99d25`.
Original JPEG SHA-256: `b56ea4409170775290ae27d3a74e1b73e121371f97c78610225c2623f0a5b9d8`.
Decoded RGB SHA-256: `c29914e081bdc6e3570a60ffdcc04091ca791d5faec16defc83dfbd0ad9c8af3`.
ICC SHA-256: `e5f6ffb83b6d3491301dd750975684cc5cc2a1951c994a14b08cfdaa0d75a041`.
Runtime PNG SHA-256: `eed1b91fbad07776381ff56a87d803df49b7a85180c42d04c2fd19e22aec7f8c`.

Acquired publisher HTML/PDF/WebPs and extraction records remain in
`/tmp/primer-msk-sources/hip-tendons-next/`. PMC browser challenges were not
solved or retried. The independently available primary publisher was used.
No external contact or clinical approval was made.
