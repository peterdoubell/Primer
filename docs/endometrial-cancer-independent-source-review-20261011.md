# Independent endometrial source-delivery review — 2026-10-11

The frozen package passes this independent source-preservation review: **36 complete figures, all 15 original ICC objects, and no remaining source-preservation blockers**. The reviewed source contract SHA-256 is `4863d5cdbc3c69e94f2c2768cec6193468f0e90dc2b745c15b8aae376326794f`. Clinical approval, every-structure approval, fine 3D tissue approval, native acquisition-array delivery, independent patient calibration and patient/model registration remain **false**.

The accompanying [machine-readable review](endometrial-cancer-independent-source-review-20261011.json) identifies every figure and its independently verified runtime SHA-256, native source PDF page/object, encoded-stream hash, decoded-sample hash, ICC object, placement, panel/case scope and licence. Root binds these verified image files after this proof; this review does not claim that final reader-route binding or production delivery was already tested.

## Direct original-object and appearance checks

Six ignored original PDF masters were opened directly with `pypdf` and PyMuPDF, rather than treating the package's archived streams as their own authority. Their SHA-256 and byte lengths match the original-source inventory; all five NLM PDF URLs' supplied MD5 values also match. Each selected native image object occurs at its recorded source page and placement. Archived encoded streams equal the native objects' actual encoded bytes.

All runtime decoded samples equal the native objects' decoded samples. JPEG scan encoding is unchanged: where an external original ICC was restored, only ICC APP2 metadata was added. The two Flate-decoded RGB figures are retained losslessly in PNG. Original RGB and grayscale modes remain intact (20 RGB, 16 grayscale), with complete native dimensions and no cropping, resizing, enhancement or new marks. The runtime image files total 6,430,845 bytes. Complete PDFs are not redistributed in the package.

Every one of the 15 source ICC objects was fetched from the original PDF object graph and compared byte-for-byte with the archived profile and runtime embedded profile. Independently profile-managed RGB samples agree between original and runtime images. Profiles were not assumed to be sRGB. The separate source-agent browser appearance proof was checked against these independently established native stream hashes, runtime hashes, original profile bytes and natural extents; it reports zero runtime-versus-original-profile differences for all 36 figures. That browser session is additional evidence, not represented as this reviewer's own session.

The native page display lists, image placements, text and drawing layers were independently inspected for every selected object. No intersecting text overlays or visible annotation layers were lost. The only intersecting vectors are white rectangular underlays preceding the opaque images in Cancers 2026 Figures 1/2 and Cureus Figures 4/5; they do not supply visible arrows or labels. The source images themselves retain arrows, arrowheads, stars, circles, outlines, measurement lines, scale bars, panel letters, acquisition text, ADC/SUV annotations and coloured PET observations.

All 36 original-page/runtime appearance pairs were rendered independently and visually inspected on six comparison sheets. One complete page from each original PDF was also rendered with Poppler and inspected to check caption/object placement and surrounding source context. A few original PDFs slightly stretch their placed images relative to native pixel aspect, by at most approximately 0.234% here. Runtime preserves the native sample aspect; it is not a clone of the complete PDF page layout. Neither this placement nor a publication's printed scale provides independently calibrated patient measurements.

## Sources, rights and identities

| Original source | Complete selected figures | Licence |
| --- | --- | --- |
| [Cancers 2024, DOI 10.3390/cancers16101869](https://doi.org/10.3390/cancers16101869) | 4–16, 18–19 (15 figures) | CC BY 4.0 |
| [Abdominal Radiology, DOI 10.1007/s00261-025-05058-9](https://doi.org/10.1007/s00261-025-05058-9) | 1–14 (14 figures) | CC BY 4.0 |
| [Cancers 2026, DOI 10.3390/cancers18061005](https://doi.org/10.3390/cancers18061005) | 1–2 | CC BY 4.0 |
| [Vaginal-recurrence cohort, DOI 10.1007/s00261-020-02453-2](https://doi.org/10.1007/s00261-020-02453-2) | 2–3 | CC BY 4.0 |
| [Cureus 2021, DOI 10.7759/cureus.19286](https://doi.org/10.7759/cureus.19286) | 4–5 | CC BY 3.0 |
| [ESR 2026, DOI 10.1007/s00330-026-12705-2](https://doi.org/10.1007/s00330-026-12705-2) | 5 | CC BY 4.0 |

Fresh NLM metadata and XML bytes matched all five archived NLM sources; every metadata record reports `is_retracted=false`. Current PubMed records were also checked for correction/retraction relationships and publication types, with none found for these five sources. The ESR publisher's current Figure 5 and permissions were reviewed. These are current-record checks, not a guarantee against future notices.

Original article permissions grant CC BY 3.0/4.0, both of which permit commercial reuse with attribution under their respective [3.0](https://creativecommons.org/licenses/by/3.0/) and [4.0](https://creativecommons.org/licenses/by/4.0/) terms. Selected figure captions, credits, original XML permission nodes and ESR Figure 5 were checked for restrictive third-party exceptions; none were found for the selected figures. Author-only attributions match original author lists, with source title, DOI/figure, licence and preparation notice. The adapted Node-RADS figure and NC/ND/unverified-grant candidates remain held.

All 35 XML-backed figure captions equal the originals after whitespace normalization; the ESR caption equals its original publisher caption. There are 138 visible panel observations, of which 132 are the selected clinical observations and six are explicitly ancillary CT/PET observations. Source-defined multi-patient cases, mixed MRI/CT/PET figures, recurrence cases and treatment phases are not combined into one examination. The 2021 FIGO 2009 context is not silently restaged. The 2020 recurrence figures depict separate baseline recurrent tumours and corresponding sequence pairs, not an invented serial treatment response.

## Reporting and source-stage limits

The nine assessment areas and blank report template were independently compared with supplied source identities and the [primary FIGO 2023 committee publication](https://doi.org/10.1002/ijgo.14923). Imaging findings do not supply histology, microscopic LVSI, molecular class, pathological nodal burden or a complete stage. Current criteria distinguish pelvic peritoneum, extrapelvic peritoneum and other distant disease; above-renal-vessel nodes remain IVC. The [corrigendum](https://doi.org/10.1002/ijgo.15193) corrects the pathological 0.2 mm deposit boundary, not an MRI size threshold. Advanced molecular notation may be recorded without changing III/IV anatomical categories.

Three draft scope issues were corrected and the final contract rechecked: Figure 11 now distinguishes early category modification from advanced molecular notation while retaining its unendorsed original glyph; Figure 15 no longer independently asserts pelvic-only peritoneal distribution and retains author IVB context with uncertainty; Figure 19 removes unsupported vaginal-cuff identity and supports local bladder/urethral observations in adjacent-organ area 4, with MRI and fused PET distinguished. Recommended source bindings were aligned with the root integration script.

Known source-prose discrepancies remain explicitly recorded rather than imported into current criteria: the ESR above-renal-vessel IVB statement; the Cancers historical-stage and molecular-glyph conflicts; and the Abdominal Radiology IIB myometrial-invasion wording and overly strict IA3 no-LVSI wording. Original captions/artwork remain unchanged. No unresolved source-role blocker remains in the frozen contract.

Native-object proof, 36 full figure-pair renders, six comparison sheets and six whole original page renders are preserved in the owner's ignored `.research/endometrial-independent-review-20261011-7czfs724/` directory. This reviewer changed only these independent `.md`/`.json` review files and private inspection artifacts. No source/package/reporting file, clinical approval, commit or deployment was changed.
