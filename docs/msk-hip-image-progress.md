# Hip source-image acquisition and integration

Reviewed 26 September 2026. Five source figures are integrated under `ra.hip-fai`, preserving all prior 54 records. At integration this batch raised the base catalogue from 54 to 59 entries; subsequent knee additions are tracked in the global attribution index. Three narrow source-local candidates are recorded; neither the images nor their successful extraction constitute clinical approval.

## Selected originals

| Figure | Modality / native size | Defensible scope |
|---|---|---|
| open-hip-normal-joint-schematic-aubry-fig2 | Schematic / 565×619 | Normal capsule/labrum/cartilage relationships; no sector or separate anterior/posterior recess leaf credited. |
| open-hip-superior-labrum-mra-aubry-fig3 | MR arthrography / 565×564 | Normal superior labrum and perilabral recess. Coronal superior does not establish anterosuperior/posterosuperior sectors; remains unbound. |
| open-hip-posterior-labral-recess-mra-aubry-fig5 | MR arthrography / 565×590 | Posterior labral normal variant in a 17-year-old girl. Local posterior-labrum candidate only; side/maturity unspecified. |
| open-hip-gluteus-minimus-comparison-mri-amin-fig3 | MRI / 898×946 | Full mixed figure retained. Only LEFT intact insertion at the panel-a arrowhead is a normal candidate; RIGHT tear/bursitis and panel b excluded from that claim. |
| open-hip-proximal-hamstring-schematic-balius-fig2 | Schematic / 986×1258 | Authored expanded tendon/muscle diagram. Local proximal attachment-relationship candidate, not MRI or measured footprint geometry. |

## Source rights and original credits

- [Aubry, Bélanger, Giguère and Lavigne (2010)](https://link.springer.com/article/10.1007/s13244-010-0023-x), *Magnetic resonance arthrography of the hip: technique and spectrum of findings in younger patients*. The official publisher Rights and permissions section explicitly grants **CC BY 2.0**, not CC BY 4.0. The PDF credits © European Society of Radiology 2010. Figures 2, 3 and 5 and their captions were inspected; none carries a different owner, permission-only notice or exclusion. The current publisher licence, title, authors and original copyright credit are preserved. The original PDF does not reproduce that online licence paragraph; there is no contrary selected-figure restriction.
- [Amin and Abdelkerim (2022)](https://link.springer.com/article/10.1186/s43055-022-00754-8), *Greater trochanteric pain syndrome: a simplified MRI approach*. Publisher and PDF grant **CC BY 4.0**, including images unless a credit states otherwise. Figure 3 has no excluded third-party credit. Its 57-year-old female patient has right-sided GTPS; only the expressly captioned intact contralateral left insertion is proposed as a normal anatomical reference.
- [Balius, Pedret, Iriarte, Sáiz and Cerezal (2019)](https://link.springer.com/article/10.1007/s00256-019-03208-x), *Sonographic landmarks in hamstring muscles*. Publisher and PDF grant **CC BY 4.0**. Figure 2 is the authors’ diagram; the visible `@inigoiri` signature is preserved and Iñigo Iriarte is credited among the authors. No restrictive or separate-owner credit is present in the figure/caption.

Both exact licence versions permit commercial reuse with their attribution conditions. The licenses are not evidence of clinical fidelity. Full source captions and original credits are stored with each catalogue entry and in [ATTRIBUTION.md](../web/reference-media/msk-open/ATTRIBUTION.md).

## Native extraction and visual inspection

Four selected JPEGs are the exact `/DCTDecode` image streams from the official PDFs. They were not obtained by rendering, cropping, resizing or re-encoding the pages. Independent Poppler `pdfimages -j` extraction produced identical SHA-256 values. This avoids the recompression performed by a generic `pypdf` image-data export.

Aubry Figures 2/3 are on PDF page 3 (`X1.jpg`, `X2.jpg`); Figure 5 is page 4 (`X1.jpg`). Their native widths are 565 pixels; the publisher web previews were only 307 pixels. Amin Figure 3 is PDF page 2 (`Im2.jpg`) at 898×946. The web preview was not substituted for the source stream.

Balius Figure 2 is PDF page 2 (`Im2`, `/FlateDecode`), 986×1258 RGB pixels. It was placed in a lossless PNG, and every decoded saved RGB byte matches the original decoded PDF image stream. No resampling or annotation modification occurred.

All five native figures and their corresponding rendered PDF pages were visually inspected. Aubry numbers 1–10, the labral arrows/arrowhead, Amin panel a/b labels and comparison arrows, and Balius tendon labels/artist signature remain present. The selected PDF images contain the annotations themselves; no vector labels were lost during extraction.

## Candidate bindings and limits

- `hip.acetabular_labrum.posterior`: local posterior labrum in Aubry Figure 5, MR arthrography; no whole posterior-sector or side-specific claim.
- `hip.gluteus_minimus_tendon.attachment`: only Amin Figure 3 panel a, LEFT white-arrowhead insertion. The stored image is bilateral/mixed; binding context deliberately describes just the selected left structure, not the whole figure or patient.
- `hip.proximal_hamstring_tendons.attachment`: schematic origin relationships in Balius Figure 2, not an MRI or measured enthesis claim.

All three remain partial, unapproved candidates. The superior labrum figure is not forced onto a clock-face leaf. Neither MR arthrogram is used to satisfy MRI-only capsule requirements. Broad schematic cartilage and capsule labels are not promoted to sector-specific coverage. The final report’s acquired-MRI conditions and all 20 parents/50 components are preserved. No full cartilage MRI map, normal gluteus-medius MRI attachment, iliopsoas MRI attachment, complete tendon course or circumferential labral coverage is supplied by this batch.

## Exact integrated files

| File | SHA-256 |
|---|---|
| hip-normal-anatomy-aubry-fig2.jpg | `c6debd7d0844c7f3dde0597ec6560bf7921d7acee4cd20e18cc3827f6f803ece` |
| hip-superior-labrum-mra-aubry-fig3.jpg | `607242223f474d65478054a90ca9bfcdc14827c3f2782e94641c9dd1ad2f4267` |
| hip-posterior-labrum-variant-mra-aubry-fig5.jpg | `7a09ca9407206ca9d3518fa0eaf5e9b23e74a5c711a7555a47a5c51b95332062` |
| hip-gluteus-minimus-comparison-mri-amin-fig3.jpg | `c58ddd8f8e6235c812f6903c7c8fc3d64ac990f806404bccdd76f43af059cb49` |
| hip-proximal-hamstring-anatomy-balius-fig2.png | `e4333402c44d4c5770894c0667d1b662b467850450c3b671aeda85b3bdd75e66` |

Acquisition logs, original publisher HTML/PDFs, rendered review pages, original image streams, staged records, partial-binding proposal and validation are retained in `/tmp/primer-msk-sources/hip-image-batch/`. `native-extraction.json` records PDF page/image identities and original-stream hashes. The staged proposal was checked against the current hip checklist fingerprint before integration.

Held/excluded leads: the Polish Journal of Radiology hip review is NC-ND; no figures were taken from it. RSNA capsule sources did not provide a confirmed commercial reuse grant. The lateral-hip scoping review’s reused Domb figure has a permission-specific third-party credit and was not selected. The 2024 hip-flexion hamstring MRI study contains symptomatic/tear cases despite some near-normal conventional appearances; those were not relabelled as normal anatomy. No external contacts were made.

Browser QA is pending the coordinator’s final application/source freeze. Source extraction checks do not substitute for that rendering pass or a clinical review.
