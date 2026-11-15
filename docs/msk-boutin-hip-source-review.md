# Hip tendon source acquisition and selection

Reviewed 27 September 2026 against the downloaded publisher chapter and rendered
pages, not search snippets. Figures 6.5 and 6.7 are now integrated as partial, unverified MRI candidates.
No requirement satisfaction or clinical approval is asserted.

Source: Robert D. Boutin and Philip Robinson (2021), [Pelvis and Groin:
Practical Anatomy, Injury Patterns, and Imaging Findings](https://link.springer.com/chapter/10.1007/978-3-030-71281-5_6),
DOI 10.1007/978-3-030-71281-5_6. The chapter's rights section grants CC BY 4.0,
including figures unless a credit states otherwise. Figures 6.5, 6.7 and 6.13
have no contrary credit on their source pages. Figure 6.12 has an explicit
reproduced-with-permission credit and is excluded pending independent rights.

## Decisions from the actual images

- **6.13 is not a distal gluteus medius tendon reference.** The displayed axial
  slice is at the pelvis/muscle level. Its caption's assertion that the distal
  tendon was intact is not visual evidence of that tendon. Do not bind it to
  tendon attachment or course requirements.
- **6.5a is a partial proximal hamstring course candidate.** The source marks
  the normal conjoint tendon and semimembranosus in a right proximal thigh
  cross-section. It does not show the complete course or establish the origin
  footprint. Panel b depicts tendon-involving myotendinous injury; a complete
  figure must retain and distinguish that pathological comparison. This is a
  symptomatic 24-year-old athlete, not a normal whole examination.
- **6.7 is a partial psoas-component course candidate.** The two planes mark
  intact psoas major tendon next to iliacus injury in a 21-year-old athlete.
  This does not establish all iliopsoas tendon components, an attachment, or a
  normal examination. Laterality is not supplied in the caption and must not
  be inferred from page position.

The target requirement IDs were checked in the current specification:
`hip.proximal_hamstring_tendons.visible_course` and
`hip.iliopsoas_tendon.visible_course`. Neither requirement is satisfied by this
source review. No 3D or schematic coverage follows from these MR figures.

## Preservation and integration

The PDF stores each panel separately. Figure 6.5 uses page 3 `/Im4` and `/Im5`
(479 × 423 and 442 × 422 pixels); figure 6.7 uses page 4 `/Im0` and `/Im1`
(724 × 413 and 299 × 413 pixels). These use a PDF **Separation/Black colour
space**, not a standalone RGB interpretation. Publishing extracted JPEG streams
as ordinary greyscale images without checking the tint transform could change
their intended appearance. A PDF-aware complete-figure render should preserve
the panel layout, letters, arrows, and PDF colour interpretation. Higher render
resolution would not create more anatomical information than the source pixels.

The existing nested-PDF placement inspector was run on both pages; its output
records image transforms, effective source resolution, painted vectors and
forms. Complete figure renders have now been inspected and integrated, with exact
render bounds, source and output fingerprints, and explicit sRGB output
profiles. The original panel layout and annotations remain. The selected local
structures carry the documented examination context; figure 6.7 remains mixed
rather than normal because only the psoas component is intact.

Evidence: [source fingerprint and decisions](msk-boutin-hip-source-review/source-review.json),
[PDF placement audit](msk-boutin-hip-source-review/pdf-placement-audit.json),
[page 3](msk-boutin-hip-source-review/page-03.png),
[page 4](msk-boutin-hip-source-review/page-04.png), and
[page 8](msk-boutin-hip-source-review/page8.png).
Rendered pages are internal review evidence, not cleared runtime whole-page
illustrations: some neighboring figures carry separate permission credits.
The original PDF is retained at
`/tmp/primer-msk-sources/boutin-hip/chapter.pdf`.

## Verification

[Rendering record](msk-boutin-hip-source-review/figure-rendering.json) distinguishes
PDF-rendered resampling from original image bytes. The reproducible renderer is
`tools/anatomy_sources/render_boutin_hip_figures.py --source-pdf PDF --output-dir DIR`.
The catalog now preserves dotted chapter figure identifiers, including 6.5 and
6.7. The evidence ledger binds only the two course requirements identified
above; attachment, complete-course, schematic and 3D claims remain absent.

191 relevant tests passed across hip tendon preservation, panel-state checks,
the fidelity gate, derived schematics and investigation integration. An isolated
local browser check confirmed both native render dimensions, no decorative
image filters, desktop and 390-pixel mobile enlargement, full-size labels,
Escape focus restoration and no browser errors. The temporary server and tab
were closed and the viewport reset.

The [full fidelity snapshot](msk-verification-boutin-hip-2026-09-27.json) retains
5,202 requirements: 0 verified, 146 unverified and 5,056 missing. These additions
are source references, not clinical certification.
