# Thoracolumbar source-image acquisition — 26 September 2026

The initial acquisition below is retained as source history. The two small
ABCs publisher PNGs have since been superseded in the runtime catalogue by
complete, higher-resolution PDF-rendered figure regions with their original
vector labels and arrows. See [current files and rendering proof](msk-spine-pdf-rendering.md).
The Cureus originals and all anatomical scope/review limits remain as recorded.

**Four source figures are integrated in the `ra.thoracolumbar-fractures` runtime atlas.** They have five evidence-ledger representations because the ABCs ligamentum-flavum composite has separate clinical-image and schematic claims. Six local generic candidates are recorded from the other three figures; both ligamentum-flavum representations remain unbound. All anatomical/clinical reviews remain pending. The original staging/provenance package is `/tmp/primer-msk-sources/spine-image-batch/`; only its four selected assets were copied into `web/reference-media/msk-open/`.

## Selected sources and image checks

| Entry | Original size | Physically visible source evidence | Candidate limits |
|---|---:|---|---|
| `open-spine-plc-schematic-bizdikian-fig1` | 986×986 | PLC schematic labels FJC, ISL, LF, SSL, with original leader lines. | Local SSL/ISL intersegmental-course schematic candidates. No complete courses, entheses, sides or numbered levels. |
| `open-spine-plc-lumbar-mri-bizdikian-fig4` | 986×1856 | Lumbar MRI a labels SSL/LF; b labels ISL; c has FJC arrows and broad circles. All a/b/c labels preserved. | Local SSL/ISL MRI candidates. **Patient normal/pathological state is not reported**; no healthy-volunteer or intact-whole-PLC claim. FJC circles do not delineate full capsules. No left/right LF/capsule assignment. |
| `open-spine-functional-unit-kushchayev-fig1` | 520×333 | Complete publisher schematic labels superior/inferior endplates, disc, vertebrae, facet joint and FSU; original load arrows retained. | Two disc-endplate interface schematic candidates. Generic teaching unit, not a measured or numbered patient motion segment. |
| `open-spine-ligamentum-flavum-kushchayev-fig26` | 610×229 | Complete figure: a normal LF drawing; b source-described normal LF MRI with red arrows; c hypertrophy comparison. Panel letters, labels and arrows retained. | Normal MRI observation is b only. No left/right/level-specific course or attachment bindings yet. c is **pathological**, not normal evidence. Source caption calls c sagittal although the supplied raster appears transverse; mismatch is disclosed, without inventing acquisition metadata. |

All four were viewed at their native available detail. The publisher ABCs PNGs have limited native resolution but their labels/arrows are legible; no extra detail is claimed. No AI anatomy, upscaling, sharpening, painting or annotation reconstruction was used.

## Rights and exact source versions

1. **Bizdikian and El Rachkidi (2021)**, [primary deposited article](https://pmc.ncbi.nlm.nih.gov/articles/PMC8590454/), DOI [10.7759/cureus.18774](https://doi.org/10.7759/cureus.18774). The **actual PDF page 1 explicitly says CC-BY 4.0**. The publisher-deposited JATS instead hyperlinks **CC BY 3.0**. Both permit commercial redistribution, but the selected assets are raw streams from the PDF, so their record uses its explicit **CC BY 4.0** grant. The discrepancy and both PDF/JATS SHA-256 values are retained in each record's `source_license_evidence`. Selected figures have no different license/restrictive credit. The discrepancy was reported to root before freezing; the PDF-version route was explicitly selected.
2. **Kushchayev et al. (2018), ABCs of the degenerative spine**, [publisher article](https://link.springer.com/article/10.1007/s13244-017-0584-z), [Figure 1](https://link.springer.com/article/10.1007/s13244-017-0584-z/figures/1), [Figure 26](https://link.springer.com/article/10.1007/s13244-017-0584-z/figures/26). Primary CC BY 4.0 grant. Exact selected caption/image has no excluded third-party notice. Artist **Irina Nefedova** is acknowledged and credited in the records; artist attribution alone is not a license exclusion.

Complete author credits, source captions, display captions, limitations, original URLs, license notices and hashes are preserved in `data/radiology/msk-open-images.json` and `web/reference-media/msk-open/ATTRIBUTION.md`. The source PDF/JATS and byte-verification records remain in the provenance package.

## Raw PDF and annotation integrity

For the Cureus PDF, recursive resource inspection checked direct image objects and nested Form resources. Selected figure images are direct XObjects with `/DCTDecode`, `/DeviceRGB`, no `/Decode` array, and no mask or soft mask:

- Figure 1: page 2, `/Im30`, PDF object 30 0; raw DCT/file SHA-256 `008964ed0da0e6dac11fd2432c26f6a0c06dd9476ca16c44f3578fe082deb331`.
- Figure 4: page 5, `/Im69`, PDF object 69 0; raw DCT/file SHA-256 `2f50c74c47f5a52aae0cc2829703cb3dd4bfc9cdb36ff00f401e9ce8298e832c`.

The raw compressed DCT bytes were copied directly. **`pypdf` image `.data` was not used**, and no JPEG was recompressed. These larger originals contain all their own text/arrows/circles; native visual inspection confirms the annotations are integral pixels. No PDF color interpretation or raster conversion was necessary.

The ABCs PDF has larger RGB/ICCBased raw JPEGs, but **those omit text and arrow annotations drawn as PDF page vectors**. They were rejected as display assets. Instead, the complete publisher PNGs were copied unchanged; they preserve the figure's labels/arrows and avoid inventing a merged/reconstructed figure. Raw ABCs inspection files remain research evidence outside `assets/` and are not runtime assets.

Publisher PNG hashes:

- Functional-unit Figure 1: `38cd425a310046fc98d7ae2ce52a43428c2261affed8cdb25220d525da6dd6cf`.
- LF Figure 26: `be6227f07ce4013253e5db8032ac86940e31334aa850310c15fe09cdc8cb8b36`.

## Exact local candidate leaf bindings

- Cureus schematic 1 → `thoracolumbar.supraspinous_ligament.intersegmental_course` and `thoracolumbar.interspinous_ligament.intersegmental_course`.
- Cureus MRI 4a/4b respectively → the same two leaves, MRI representation only, with normality unknown and local extent explicit.
- ABCs schematic 1 → `thoracolumbar.intervertebral_disc.superior_endplate_interface` and `thoracolumbar.intervertebral_disc.inferior_endplate_interface`.
- ABCs 26 b normal MRI and a schematic → unbound pending level/side/extent verification. Do not infer both left/right ligamentum-flavum leaves from an unmarked generic image.

That is six structure/representation candidates, subject to independent clinical review and motion-segment instantiation, not six complete structures. No anterior/posterior longitudinal-ligament coverage is asserted.

## Rejected alternatives and remaining gaps

- Kumar/Hayashi 2016 normal Figure 2 is **cervical in both supplied panels**; it was not passed off as thoracolumbar evidence.
- Gamanagatti et al. 2015 *World Journal of Radiology* is CC BY-NC 4.0; the attractive functional/MRI anatomy figures were excluded from commercial use.
- The 2022 PLC algorithm source is CC BY-NC-ND and likewise excluded. ND alone was not used as an exclusion.
- Exact side-specific ligamentum-flavum and facet-capsule courses/entheses, numbered levels, normal ALL/PLL MRI and quantitative disc/ligament geometry remain gaps.

## Integration limits

The raw PDF-byte checks and complete-publisher-image checks establish preservation of the reviewed source representations. They do not establish a healthy examination, full ligament courses, enthesis geometry, numbered vertebral-level or side-specific coverage, clinical validation, or registration to a 3D model. MRI normality remains unknown for the Cureus teaching example; only ABCs panel b is explicitly source-described normal LF, while panel c is a pathological comparison. The source-checked visual review is not an anatomical/clinical approval. Browser presentation is verified separately by the integrating task.
