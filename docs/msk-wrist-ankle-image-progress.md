# Normal wrist and TFCC image acquisition

Reviewed and acquired: 26 September 2026.

This bounded batch adds **10 visual entries from eight original source figures**: six complete figures and four separately preserved MR arthrogram panels. It extends the existing 12-entry MSK image collection to 22 entries. The original 12 records, identifiers and image files were preserved. No application code or anatomical geometry was changed.

The new material addresses normal TFCC components, ulnomeniscal homologue anatomy, scapholunate and lunotriquetral ligament subdivisions, normal dorsal SL and volar LT appearances on MR arthrography, and labeled dorsal/volar wrist ligament schematics. These are specific additions to partial coverage, not a complete or independently clinically validated wrist atlas.

## Sources and commercial reuse basis

1. Cerezal, A.; del Piñal, F.; Rolón, A.; Canga, A.; Perez, A.; Cerezal, L. **Beyond Palmer: a topographic classification of non-Palmer triangular fibrocartilage complex injuries.** *Insights into Imaging* 17:199 (6 August 2026). [Primary article and rights statement](https://link.springer.com/article/10.1186/s13244-026-02356-8).

   The article explicitly places images and third-party material under CC BY 4.0 unless a figure credit indicates otherwise. The two selected figures have no exclusion or additional restriction in their captions. Drawings carry the visible signature **M. Crespi © for Cerezal**, retained in the pixels and explicitly added to attribution. A copyright signature does not by itself contradict an open license. The acquisition relies on the publisher's express image-license statement; it does not claim an independently obtained artist contract. No author or artist was contacted.

2. Okoro, C.K.; Skalski, M.R.; Patel, D.B.; White, E.A.; Matcuk, G.R., Jr. **Imaging Diagnosis and Management of Carpal Trauma and Instability—An Illustrated Guide.** *Life* 13:1426 (2023). [DOI](https://doi.org/10.3390/life13071426), [publisher PDF](https://mdpi-res.com/d_attachment/life/life-13-01426/article_deploy/life-13-01426.pdf).

   The publisher PDF specifies CC BY 4.0 on page 1. Author Contributions identifies Matthew R. Skalski as the illustrator, and the article describes its medical illustrations as original. Selected figures 20, 22–26 have no separate rights restriction or courtesy credit. A different figure on PDF page 6 carries a Radiopaedia courtesy credit and was **not** acquired. Figure 21 includes a tear in one panel despite showing normal morphology in others and was not used for this normal-anatomy batch.

   Exact captions were cross-checked against the [NLM PMC Open Access dataset record](https://pmc-oa-opendata.s3.amazonaws.com/PMC10381215.1/PMC10381215.1.json), version `PMC10381215.1`. Its metadata records `CC BY`, published version, and not retracted. NLM is acknowledged as the source of this metadata/caption cross-check; this is a snapshot retrieved on 26 September 2026, not a claim to reproduce the most current NLM data. The shipped high-resolution image pixels come from the publisher PDF. No NLM endorsement is implied.

All entries record CC BY 4.0 and its [license link](https://creativecommons.org/licenses/by/4.0/), source/figure URLs, exact full source caption, attribution, dimensions, SHA-256, modality, image state, narrow visible structures and limits. No NC or ND material was added.

## Exact visual review

Every saved source raster was opened and inspected. The dimensions below are actual pixels; none was enlarged.

| Entry | Native size | Actual visible depiction | Coverage boundary |
| --- | --- | --- | --- |
| `open-wrist-tfcc-normal-cerezal-fig1` | 1974 × 1223 | Complete composite: labeled TFCC diagrams in a–d; coronal, sagittal and axial PD fat-suppressed MRI in e–g with arrows/markers at attachments, peripheral structures and capsule/subsheath relationships. | Main `structures_visible` records only clinical-panel evidence. Schematic-only ulnolunate/ulnocapitate and vascular labels are separated in `schematic_structures_visible`. |
| `open-wrist-tfcc-normal-cerezal-fig2` | 1975 × 531 | Diagrams a–c show numbered ulnomeniscal homologue portions and insertion variants; MR arthrogram d retains numbers 2, 3 and 4 along the ulnar periphery. | Clinical list includes styloid, collateral and distal portions; the distal radioulnar portion and variant configurations are schematic evidence only. |
| `open-wrist-scapholunate-components-okoro-fig20` | 1800 × 1372 | A source illustration shows red dorsal, white proximal and yellow volar SLL components. The original caption supplies the color key. | Schematic components, not MR signal, quantitative attachment maps or reusable 3D geometry. |
| `open-wrist-lunotriquetral-components-okoro-fig23` | 900 × 907 | Source illustration shows red dorsal, white proximal and yellow volar LTL components, keyed by the caption. | Schematic component separation; does not establish clinical depiction of the dorsal or membranous LTL. |
| `open-wrist-dorsal-capsular-ligaments-okoro-fig25` | 1800 × 1723 | Embedded text leaders explicitly name DIC, DRCL and dorsal distal radioulnar ligament. | Only these labeled ligaments are counted; surrounding bones are not separately credited as complete anatomy. |
| `open-wrist-volar-extrinsic-ligaments-okoro-fig26` | 2100 × 1386 | Embedded leaders identify scaphocapitate, triquetrohamocapitate, radioscaphocapitate, radial collateral, long/short radiolunate, ulnocapitate, ulnolunate, ulnotriquetral and volar radioulnar ligaments. | A detailed schematic. No normal MR appearances, complete entheses or high-fidelity source meshes are supplied. |
| `open-wrist-scapholunate-normal-mra-okoro-fig22a` | 987 × 881 | Axial T1 fat-suppressed MR arthrogram; original outlined arrow is visibly embedded at the dorsal SLL. | Panel a only; one normal ligament component, not the complete SL complex. |
| `open-wrist-scapholunate-normal-mra-okoro-fig22b` | 900 × 881 | Coronal T1 fat-suppressed MR arthrogram in a different source patient; original outlined arrow is present. | Panel b only; preserves the source's identification of the normal dorsal SLL without claiming other components. |
| `open-wrist-lunotriquetral-normal-mra-okoro-fig24a` | 916 × 900 | Axial T1 fat-suppressed MR arthrogram; original outlined arrow points to the volar LTL. | Panel a only; not evidence for dorsal/proximal LTL integrity. |
| `open-wrist-lunotriquetral-normal-mra-okoro-fig24b` | 921 × 900 | Axial T1 fat-suppressed MR arthrogram from a different source patient; original solid arrowhead marks volar LTL fibers. | Panel b only; selected normal fibers, not a scrollable full examination. |

The Cerezal composites keep all panel letters, numbers, arrows, anatomical labels and artist signatures. They are marked as mixed clinical/schematic content, with explicit panel lists. The application's existing modality field identifies their clinical modality (`MRI` or `MR arthrography`); their captions and limits state that other panels are drawings. This avoids treating a drawn vessel or ligament as clinically imaged evidence.

## Extraction and annotation checks

The complete publisher TFCC PNGs were copied byte-for-byte. Okoro PDF embedded rasters were extracted at their native dimensions. JPEG objects were preserved; JPEG 2000 and PNG objects were encoded losslessly as PNG where necessary. For all eight PDF-derived entries, saved dimensions, pixel mode and decoded pixel bytes were compared directly with the original embedded image and matched. The manifest records matching decoded source/saved pixel SHA-256 hashes.

The original clinical arrows and arrowheads are **inside the extracted pixel data** and were visually verified in each of 22a, 22b, 24a and 24b. Page-level `(a)`/`(b)` letters are separate PDF content and are not inside those images. They were not invented or painted in. Instead, each record has `source_panel`, a caption scoped to the displayed panel, and the complete original caption in `source_caption_full`. Both panels from each source figure are retained as separate entries. The original diagrams' source text leaders and colors were also checked directly after extraction.

No image was cropped, recomposed, sharpened, upscaled or processed with generative AI. Retaining more source pixels improves readability but does not increase the underlying MR acquisition resolution or create detail absent from the scan.

## Integration and remaining coverage

All ten entries are appended to the existing `ra.wrist-instability` atlas array, consistent with the earlier wrist MRI adjunct. That investigation's reporting template is radiographic: these MRI/arthrography images must remain explicitly identified as cross-sectional anatomical references, not be presented as structures directly assessed on a plain wrist radiograph.

This batch fills enough wrist gaps to use the bounded ten-entry allocation without substituting ankle pathology or generic bone images. **No additional ankle image is claimed.** Normal clinical deltoid, spring and syndesmotic ligament coverage remains outstanding. Wrist gaps also remain: normal clinical depictions of each extrinsic ligament, full dorsal/proximal LTL appearance, complete courses and attachments, normal variants across a reference population, matched three-plane examinations, and high-fidelity 3D representation of these fine structures. Source acquisition and depiction review do not replace specialist clinical validation.

Validation performed:

- All 22 collection records pass the application's `_structure_atlases()` loader.
- All ten new saved files match their recorded dimensions and file SHA-256.
- Eight PDF-derived entries have exact decoded-pixel equality with their native embedded sources.
- All old twelve records were compared for deep equality before the append; their existing IDs, fields and assets remain unchanged.
- Ten added assets total 6,710,599 bytes. Original source captions and full rights/attribution details are also preserved in `web/reference-media/msk-open/ATTRIBUTION.md`.

This document records an asset and source review. No independent MSK-radiologist sign-off, diagnostic-performance claim, complete anatomical-coverage claim or product release is asserted.
