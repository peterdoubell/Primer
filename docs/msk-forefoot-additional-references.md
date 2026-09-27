# Additional forefoot tendon and lesser-MTP references

Two rights-cleared original figures are integrated into the diabetic-foot
reporting desk as normal anatomical adjuncts. Their catalog entries live in
`data/radiology/msk-open-images.json`; the evidence ledger retains empty
`structure_ids` and pending anatomical review for both. No requirement,
reporting indication, site-expansion rule or clinical approval changed.

| Source | Runtime asset | Actual scope |
| --- | --- | --- |
| [Maas et al. 2016, Figure 2](https://link.springer.com/article/10.1186/s13047-016-0165-2/figures/2) | `web/reference-media/msk-open/forefoot-lesser-mtp-schematic-maas-fig2.jpg` | Generic lesser-MTP schematic; digit and side unspecified. Original artwork acknowledged to BJ Kompanje. |
| [Chen et al. 2022, Figure 7c](https://pmc.ncbi.nlm.nih.gov/articles/PMC9322853/figure/diagnostics-12-01541-f007/) | `web/reference-media/msk-open/forefoot-second-fdl-ultrasound-chen-fig7c.png` | Normal second-toe FDL distal-insertion ultrasound. Subject age, sex and laterality are not reported. |

Both source PDFs grant **CC BY 4.0** without a contrary credit on the selected
figures. The [official deed](https://creativecommons.org/licenses/by/4.0/)
permits commercial reuse with attribution and change disclosure. Source
captions, author/title credits, the Maas artwork credit, exact license links
and extraction details remain in the runtime catalog. These are original
figures in authored reviews, not new primary empirical MRI studies.

## Native source preservation

The complete Maas figure is a 1420 × 963 grayscale JPEG copied byte for byte
from page 5 `/Im4`, an original `/DCTDecode` stream. An independent Poppler
`pdfimages -j` extraction matched exactly. There was no cropping, resizing,
recompression, recolouring or annotation change. The source PDF's page-10
acknowledgements name BJ Kompanje; the drawing's signature remains visible.

The selected Chen ultrasound is the native 1398 × 704 RGB image at page 7
`/Im11 /Im26`, a `/FlateDecode` panel. It was decoded and saved as lossless PNG.
Saved RGB pixels match both the original decoded stream and an independent
Poppler extraction. No convenience JPEG re-encoding was used. The panel letter
`c` is separate PDF page text; the catalog declares `source_panel: "c"` rather
than painting it into the ultrasound. The dissection and probe-position panels
are not part of the runtime image.

| Artifact | SHA-256 |
| --- | --- |
| Maas native JPEG | `2c683969e02f03a17d94db4f4333ffcda48f00d11ad0ebe11b8b7b852f977d01` |
| Maas source PDF | `2b16d950bef3ddd024169e96f6914386ec5eb054672b7fece276e8a17d2994ab` |
| Chen lossless PNG | `89dce1a38224f0db8933c829353b88a74de96c6c4b59ba0b8c09580a9cd053d5` |
| Chen source PDF | `f205b6f7bdb729fda74cfd6c28211e6b6952965f2775f9d152d35d0315fe9565` |
| Chen decoded RGB pixels | `e66877c209db2981481e51ee409c715bc8b75f69c293ce6a6af1ffb70095da26` |

The Maas PDF came from the [primary publisher](https://link.springer.com/content/pdf/10.1186/s13047-016-0165-2.pdf).
The Chen PDF is the previously verified [NLM source snapshot](https://pmc-oa-opendata.s3.amazonaws.com/PMC9322853.1/PMC9322853.1.pdf?md5=d627e49fa3a9e01abaebdbc5b7c42d21),
whose MD5 is `d627e49fa3a9e01abaebdbc5b7c42d21`. The snapshot is not an assertion
about the latest NLM data or an NLM endorsement.

## Anatomical scope and withheld coverage

Maas labels the reflected plantar plate, its phalangeal insertion, proper and
accessory collateral ligaments, deep transverse metatarsal ligament, flexor
sheath, FDL and FDB. The drawing supports a general relationship explanation.
It does not identify a particular lesser digit or medial versus lateral
collaterals, show the distal FDB split and both middle-phalangeal slips, or
resolve synovial wall/lumen and complete sheath extent. The dimension inset is
a synthesis of source literature, not an individual patient calibration.

The contextual requirement candidates are
`diabetic_foot.lesser_mtp_plantar_plates.phalangeal_attachment`,
`diabetic_foot.lesser_mtp_plantar_plates.flexor_interface`,
`diabetic_foot.lesser_digital_flexor_sheaths.fdl_relationship` and
`diabetic_foot.lesser_digital_flexor_sheaths.fdb_relationship`.
They remain **unbound**: a generic joint does not instantiate MTP2, MTP3,
MTP4 and MTP5 or the individual digital sheaths.

Chen panel c labels FDL, P1, P2 and P3, with a white arrow at the second-toe
distal-phalangeal attachment. The two stars lie at the PIP/DIP plantar plates;
they must not be described as a normal second-MTP plate. FDB and distinct
sheath tissue are not separately identified. This is an **ultrasound**
reference for a local second-FDL attachment, with no MRI visibility credit.
Its contextual candidate,
`diabetic_foot.flexor_digitorum_longus_tendons.distal_attachment`, remains
unbound because the reporting requirement has MRI-only modality scope.

Neither figure depicts diabetic infection or Charcot disease, proves whole
tendon/sheath extent, covers every lesser digit, or creates a new blanket
plantar-plate instability-screening indication. These sources complement the
existing hallux figures and Siddle third-MTP MRI without exchanging their
anatomical sites or modalities. No additional normal MRI was acquired in this
batch.

## Excluded or unresolved sources

- [Mohana-Borges et al. 2003](https://doi.org/10.1148/radiol.2271020283): relevant
  lesser-MTP MRI and schematics, but no commercial reuse grant established in
  this pass. No image imported.
- [Dakkak et al. 2020](https://doi.org/10.1148/radiol.2020191725): valuable primary
  tendon-sheath study. A third-party index reports a CC BY repository copy,
  while the publisher result states © RSNA 2020 and the institutional landing
  page could not be verified. The aggregator claim was not used as permission.
- [Malhotra et al. 2016](https://pmc.ncbi.nlm.nih.gov/articles/PMC5367573/): useful
  diagrams, but CC BY-NC 4.0 does not permit the requested commercial reuse.
- [Zaottini et al. 2023](https://doi.org/10.15557/JoU.2023.0024) and
  [Reijnierse et al. 2023](https://doi.org/10.15557/JoU.2023.0033): NC-ND terms;
  no figures imported.
- [Palka et al. 2025](https://doi.org/10.1186/s13244-025-01945-3): pathological
  examples did not supply the requested normal distal flexor/sheath reference;
  no pathology image was relabelled normal.

## Verification

Native figures and their complete relevant PDF pages were visually inspected.
`tests/test_msk_forefoot_additional_figures.py` pins the image hashes and
dimensions, whole-figure/panel provenance, generic-versus-second-digit scope,
empty structure bindings and pending anatomical review. It also verifies that
the fidelity gate rejects the second-FDL ultrasound as MRI-only evidence.

The acquisition package remains at
`/tmp/primer-msk-sources/forefoot-next-batch/`: original PDFs, source text,
native extracts, independently rendered review pages, proposed context IDs
and byte/pixel validation. Runtime assets are the two repository files above;
the package's earlier staging status does not describe their integrated state.
