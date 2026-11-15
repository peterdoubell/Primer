# Accessory-muscle published PDF figures — 30 September 2026

The ankle reader now uses five complete figure renders from original published PDFs: two accessory-soleus composites, the peroneus-quartus MRI and signed schematic, and one FDAL MRI section. Four replace smaller repository previews; FDAL is a new partial belly candidate. Original panel layout, arrows, scale markings and the Eylem 2025 signature are retained. No new anatomy, sharpening or learned upscaling was introduced. Complete anatomical fidelity and all 3D requirements remain unverified.

## Original-source acquisition

PMC retired its legacy OA download service in August 2026. Its [current Cloud Service documentation](https://pmc.ncbi.nlm.nih.gov/tools/pmcaws/) expressly provides unauthenticated HTTPS access to published article PDFs and media. The documented article-version listings returned one published version for each of PMC4427770, PMC7516695 and PMC12468075. Each metadata object identifies an open-access CC BY article, not an author manuscript, and is not marked retracted at acquisition.

Every downloaded PDF and XML matched the MD5 value published in the corresponding metadata URL. SHA-256, byte length and exact URLs are recorded in [acquisition.json](msk-accessory-pdf-source-review/acquisition.json). The metadata snapshots are retained beside it. The older incomplete Europe PMC FDAL ZIP contains only two complete preview GIFs and a truncated surgical JPEG; it supplied no runtime pixels. The complete FDAL PDF and JPEG were subsequently obtained through the documented cloud service.

NLM/PMC is credited in the runtime captions. These are 30 September 2026 snapshots and may not reflect the latest NLM data; no NLM endorsement is implied. This follows the source's [dataset documentation](https://pmc-oa-opendata.s3.amazonaws.com/README.txt). Article and figure rights remain separate: FDAL uses CC BY 3.0, confirmed by the publisher-deposited Crossref record for DOI 10.1155/2015/823107; soleus and PQ use their reviewed CC BY 4.0 grants. The PQ artist credit remains intact.

## Rendering and limits

| Figure | Published PDF page | Rendered pixels | Source placement |
|---|---:|---:|---:|
| Accessory soleus Figure 1 | 3 | 1356 × 1940 | 300 dpi |
| Accessory soleus Figure 3 | 5 | 1360 × 1944 | 300 dpi |
| Peroneus quartus Figure 1 | 2 | 1047 × 782 | 300 dpi |
| Peroneus quartus Figure 2 | 4 | 1333 × 574 | 300 dpi |
| FDAL Figure 2 | 2 | 1438 × 1393 | 600 dpi |

Poppler 26.07.0 renders the complete figure regions to lossless PNG, preserving PDF colour handling and vector annotations. The soleus publication uses two columns of panels, whereas its small repository preview uses three; the PDF layout is retained. The PQ schematic's PDF presentation differs from its repository preview in aspect and label placement; the published PDF presentation and signature are retained without rearrangement. These PNGs are explicitly recorded as PDF renders, not byte-identical JPEG streams. Previous repository files and their hashes remain available for comparison.

All five renders were repeated from fingerprint-checked PDFs and were byte-identical. The [render records](msk-accessory-pdf-source-review/rendered-figure-records.json) retain crop coordinates, page numbers, DPI, PDF hashes and output hashes. The reproducible renderer is `tools/anatomy_sources/render_accessory_pdf_figures.py`. Original PDF panels contain more pixels than the repository previews, but this does not establish original scanner resolution, a highest-resolution prepublication master or biological accuracy.

The soleus Figure 3f plane discrepancy also exists in the PDF caption and remains unresolved. The PDF acquisition therefore does not justify correcting that source label without additional evidence.

## FDAL source scope

Batista et al.'s case describes a 34-year-old man with left posterior ankle pain and a prominent posterior talar process. Figure 2 is one transverse MRI section with a white arrow identifying an accessory muscle near the posterior tibial neurovascular bundle. Subsequent endoscopic identification supports the article's FDAL designation. The source does not report MRI sequence or voxel spacing, a complete course, origin or insertion footprint. It does not establish isolated FDAL symptom causation or MRI proof of tarsal-tunnel compression. Only the local muscle-belly requirement receives a partial, unapproved image candidate. No schematic or 3D candidate is inferred.

## Reader and audit verification

All five figures passed desktop (1280×900) and mobile (390×844) checks, including native-pixel zoom, caption/licence notices and no horizontal page overflow. Ten view records and screenshots are in `msk-accessory-pdf-source-review/reader-browser-checks.json`. All PDF image rectangles and the six soleus panel-letter annotations are contained in their recorded crops; raster-baked annotations were also inspected visually. The relevant 216 tests passed.

The current audit retains 5,292 representation obligations: 0 verified, 173 unverified and 5,119 missing. Runtime reference rights account for 231 figures/resources, of which 90 are cleared and 141 remain unverified. These changes remain local; the full clinical/commercial goal is incomplete.
