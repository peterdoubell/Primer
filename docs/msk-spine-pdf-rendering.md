# Complete annotated spine figures from the source PDF

Reviewed 26 September 2026. Two **PDF-rendered figure regions** replace the small publisher previews for Kushchayev et al., *ABCs of the degenerative spine*. The PDF carries CC BY 4.0; author and illustrator credits remain required. These PNGs are derived renders, **not unchanged original-image files**. They preserve the PDF's existing raster detail and vector annotations without adding diagnostic detail or clinical approval.

## Reproduction and source

```sh
python3 tools/anatomy_sources/render_spine_pdf_figures.py \
  --source-pdf /tmp/primer-msk-sources/spine-image-batch/PMC5893484.pdf \
  --output-dir /tmp/primer-msk-sources/spine-image-batch/high-resolution-review \
  --publisher-originals-dir /tmp/primer-msk-sources/spine-image-batch
```

Dependencies: Poppler `pdftoppm`/`pdftotext`, `pypdf` and Pillow. The deterministic script pins the reviewed source PDF SHA-256, checks image geometry and color interpretation, renders full pages, then crops at fixed integer pixel boundaries. It writes metadata and complete page renders for audit, without editing the catalog or ledger.

- [Primary article](https://link.springer.com/article/10.1007/s13244-017-0584-z); [publisher-deposited PDF](https://pmc-oa-opendata.s3.amazonaws.com/PMC5893484.1/PMC5893484.1.pdf?md5=ba4dd5a19b9cd29f16301f30bb1b68ef).
- PDF SHA-256: `affa1a6dc547a274a3d220b5c2aa956aaabba086e78e966273ad7e7ee7b0fe07`.
- Renderer: Poppler `pdftoppm` **26.07.0**, **300 DPI**, using the PDF's embedded **sRGB IEC 61966-2.1** color profile. Its SHA-256 is `2b3aa1645779a9e634744faf9b01e9102b0c9b88fd6deced7934df86b949af7e`.

## Current versus prior files

| Figure | Prior publisher PNG | PDF-rendered file | New dimensions / bytes |
|---|---|---|---|
| 1, functional spinal unit | `spine-functional-unit-kushchayev-fig1.png`, 520×333 | `spine-functional-unit-kushchayev-fig1-pdf-render.png` | 1309×844 / 577622 |
| 26, ligamentum flavum | `spine-ligamentum-flavum-kushchayev-fig26.png`, 610×229 | `spine-ligamentum-flavum-kushchayev-fig26-pdf-render.png` | 1534×583 / 629790 |

Exact identities:

- Figure 1 prior SHA-256: `38cd425a310046fc98d7ae2ce52a43428c2261affed8cdb25220d525da6dd6cf`; render SHA-256: `cad6b73674ae97d41021c61483595bd61b068f19e2bbf69eadcd101581328f17`.
- Figure 26 prior SHA-256: `be6227f07ce4013253e5db8032ac86940e31334aa850310c15fe09cdc8cb8b36`; render SHA-256: `373044961659f45b5df7d02a99f91b634b1245351083cad1f889e62fef37ef5d`.

The original small PNGs remain offline in `high-resolution-review/publisher-original-abcs-fig1.png` and `publisher-original-abcs-fig26.png`. `replacement-summary.json` and `proposed-replacement-records.json` retain exact old/new identities and change disclosures.

Durable copies of the original PNGs, both full-page renders, vector-position
inventories, [render metadata](msk-spine-pdf-review/render-metadata.json) and
the replacement summary are kept in `docs/msk-spine-pdf-review/`. The runtime
catalogue points to the new `-pdf-render.png` assets; historical original
resources are preserved. Automated tests compare the new decoded pixels with
the exact crops of the retained full-page renders.

## Page geometry and native sampling

Both source pages are 595.276×790.866 PDF points and render to 2481×3296 pixels. Crop coordinates use a top-left origin; right/bottom are exclusive pixel boundaries. Crops include the complete annotated figure and a 5-pixel white margin, excluding captions, body text, page headers and footers.

| Figure | PDF page / printed page | Crop pixels at 300 DPI | Crop PDF points |
|---|---|---|---|
| 1 | 2 / 254 | `[964,224,2273,1068]` | `[231.36,53.76,545.52,256.32]` |
| 26 | 16 / 268 | `[739,2384,2273,2967]` | `[177.36,572.16,545.52,712.08]` |

Figure 1 contains a 1202×753 embedded raster placed at approximately **299.94–299.96 PPI**. Figure 26 contains 525×553, 417×417 and 418×417 rasters placed at approximately **299.89–299.92 PPI**. At 300 DPI the output/source pixel ratios are **1.000125–1.000360**, less than **0.036%** departure from 1:1 due to fractional PDF placement. This preserves source sampling; it is not super-resolution or a claim of new MRI resolution. There is no post-render resampling, sharpening, painting or anatomical reconstruction.

The source raster streams alone omit annotations. Rendering the entire page preserves them: Figure 1 has 101 intersecting painted vector paths; Figure 26 has 26 plus separate a/b/c PDF text. The script inventories nested forms (none on these selected pages), image placement, vector paths and text positions, and asserts that all relevant bounds fit inside the crop. Full-page PNGs, original raster hashes, pixel/point coordinates, ICC information and commands are in `render-metadata.json` and the audit files under `/tmp/primer-msk-sources/spine-image-batch/high-resolution-review/`.

## Visual verification and limits

The rendered figures were compared with the complete source pages and prior publisher PNGs. Figure 1 retains every vertebra/disc/endplate/facet label, FSU bracket, leader line and 70%/30% arrow. Figure 26 retains the full schematic and both MRI panels, a/b/c letters, LF label/leader, T2 WI boxes and red arrows. Captions/body text are absent from both crops. A deterministic rerun produced identical output hashes; lossless PNG decoding matches the exact rendered crop pixels.

Figure 26's original caption error calling c sagittal remains preserved and disclosed; the supplied image appears transverse. Panel c is still the pathological hypertrophy comparison and is excluded from normal-anatomy evidence. Normal MRI observations remain limited to b; side/level-specific LF claims remain unbound. Larger, legible annotations do not establish complete ligament courses, numbered motion segments, enthesis geometry, clinical validation or registration to 3D anatomy. Existing pending review states must not become approval solely because of this rendering change.
