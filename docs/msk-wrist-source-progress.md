# Wrist source acquisition and fidelity review

Review date: 2026-09-26. This bounded pass searched for TFCC and intrinsic-wrist
ligament geometry beyond the existing coarse Z-Anatomy meshes. No runtime,
publisher, existing source staging or viewer files were changed.

## Outcome

A real, commercially reusable forearm geometry dataset was acquired and
inspected. It is useful for **research comparison and source review**, but the
available evidence does **not** yet support replacing the clinical wrist model
with it. The limitation is the specific validation and component evidence, not
the mere fact that geometry was algorithmically constructed.

The acquired data has coherent attachment constraints and a more structured
TFCC-region representation. Its source report nevertheless identifies geometric
uncertainty in the carpal/TFCC model, and the required SL/LT surfaces remain
missing. No other reviewed lead supplied a publicly downloadable, suitably
licensed, validated TFCC-plus-intrinsic-ligament mesh set in this pass.

## Actual acquired asset

Primary record: [Hamze et al., A 3D geometric model for the human forearm](https://zenodo.org/records/3728255),
DOI `10.5281/zenodo.3728255`, University of Innsbruck and Balgrist University
Hospital / University of Zurich, 2020.

- License: **CC BY 4.0**, verified in the public Zenodo API metadata saved as
  `/tmp/primer-msk-sources/wrist-next/zenodo-3728255.json`.
- Published archive: `forearm_model.zip`, 1,711,229 bytes.
- Published MD5 verified: `2ed767686667e5faeb8c04726776c786`.
- Computed SHA-256: `9e88aaf7a87722019f8f947ccfc3fdf84d259715936d00ddd2ba2f713c436ee3`.
- Intact source and extracted files:
  `/tmp/primer-msk-sources/wrist-next/hamze-2020/forearm_model/`.
- License permits commercial reuse and redistribution with attribution, a license
  link and change disclosure. No runtime redistribution has occurred in this pass.

The files contain **35 anatomical meshes**: 11 bone objects, 21 ligament objects,
and 3 disc/cartilage objects. A separate marker mesh and 44 attachment landmarks
are distinguished from anatomy and excluded from that count. No tissue was
synthesized, fitted to another atlas, subdivided or renamed to fill a gap.

Representative source meshes:

| Source object | Vertices | Triangles | Evidence and remaining limitation |
| --- | ---: | ---: | --- |
| `disc_pt609.ply` | 1,204 stored; 602 referenced | 1,146 | TFC-region surface; no named foveal/central/peripheral subobjects |
| `radius_cartilage_pt609.ply` | 1,646 | 2,974 | Distal radial cartilage surface; no clinical regional validation supplied |
| `ulna_cartilage_pt609.ply` | 370 | 638 | Ulnar cartilage surface; same source coordinate region |
| `DRUL1.obj` / `DRUL2.obj` | 768 / 761 | 1,352 / 1,356 | Separate dorsal radioulnar ligament objects with bone landmarks |
| `PRUL1.obj` / `PRUL2.obj` | 628 / 1,139 | 1,034 / 2,053 | Separate palmar radioulnar ligament objects with bone landmarks |
| `Radius.obj` / `Ulna.obj` | 12,232 / 4,203 | 24,460 / 8,402 | Bone context; not a substitute for soft-tissue evidence |

The complete exact filenames, bounds and hashes are in `hamze-inventory.json`.
The above face counts are inventory facts, not a fidelity score.

## Attachment, shape and frame evidence

All **44 provided attachment points** were checked against the actual source
bone vertices. Nearest-vertex distances range from approximately 0.0000054 to
0.0007015 native coordinate units. Thus the provided locations are coherent with
the source bone geometry, rather than being loosely placed decorative elements.
This test does not establish that the chosen points cover a correct clinical
attachment footprint or that the shape between them matches anatomy.

The original OBJ ligament headers identify the authors' ligament-modeler as the
producer. That alone is not grounds for rejection: anatomically constrained
modeling can produce useful reference geometry. The decisive issue here is that
no TFCC-specific ground-truth shape validation accompanies this model, while the
primary report explicitly discusses its geometric uncertainty.

The disc PLY has 54 boundary edges after exact-coordinate welding and
inconsistent winding; radius and ulna cartilage have 322 and 98 boundary edges.
These may be intentional surface representations for the simulation pipeline,
but they cannot be silently presented as validated, closed tissue volumes. No
holes were filled. These topology observations are separate from anatomical
accuracy and do not prove the surface is wrong.

A native-coordinate QA render was generated and visually inspected:
`/tmp/primer-msk-sources/wrist-next/hamze-wrist-source-qa.png`. The disc,
radioulnar branches and bone context occupy a coherent wrist region, but the
ligament surfaces show strongly regular constructed geometry. There was no
cross-atlas registration or anatomy-aware resculpting. Units, laterality and
canonical anatomical axis directions are not explicitly documented in the
archive. The supplied SOFA scene contains rigid-body transforms; its mapping
semantics require verification before treating it as an authoritative static
anatomical frame. No unit or side was guessed for runtime use.

Missing components are concrete: there is no scapholunate ligament surface,
and `IOM_landmarks_LTL.csv` supplies two LTL landmarks without a corresponding
`LTL.obj` surface. A landmark is not counted as a ligament. The disc is not
source-labelled into its clinical subregions, and the archive does not establish
complete ECU-subsheath or meniscal-homologue coverage.

## What the authors actually validated

The [primary technical reports](https://zenodo.org/records/3749272) were downloaded
and read. `TechReport_1.pdf`, sections 4–5, describes a proof-of-concept
pro-supination simulation and says the ex-vivo validation approach was only
partly implemented. Its discussion specifically includes uncertainty in the
carpal and TFCC geometric and behavior models.

`TechReport_2.pdf` discusses measurements and tensile experiments for 15
**interosseous-membrane ligaments** from five cadaveric forearms. Its shape/error
and mechanical results must not be transferred to the wrist's TFCC or SL/LT
ligaments. The related [ligament-modeling paper](https://arxiv.org/abs/2003.11025)
also distinguishes accuracy with known insertion locations from less reliable
predicted insertions. These results support a constrained research framework;
they do not establish the requested clinically resolved wrist substructures.

## Other specific routes checked

| Primary source | Access/license evidence | Outcome for this task |
| --- | --- | --- |
| [Dynamic MRI of the Wrist, Medical College of Wisconsin](https://data.mendeley.com/datasets/9kx5xp7h6d/2) | Published CC BY 4.0; static and dynamic MRI described | Public page is readable via web indexing; direct page and public-file API requests returned HTTP 403. No bypass attempted. No verified ligament segmentation or mesh was acquired. It remains an imaging/segmentation route, not ready geometry. |
| [SLIL_processing_public](https://github.com/a-quinn/SLIL_processing_public/tree/0.1) and [Zenodo release](https://zenodo.org/records/15717632) | Apache 2.0; public repository tree inspected, 576 entries | Standalone STLs are marker-plate apparatus; 3-matic projects contain bone contexts. The authors’ README states that scaffold designs were removed, and identifies the original-data ZIP as motion-capture data. No native SLIL tissue surface was found. The 284 MB release archive was not unnecessarily downloaded. |
| [VU hand/wrist anatomical parameters](https://research.vu.nl/en/datasets/anatomical-parameters-for-musculoskeletal-modeling-of-the-hand-an/) / Figshare `4434791` | CC BY 4.0 confirmed by primary API; file list inspected | Tables/figures and supplemental documentation for muscle/joint parameters. No usable TFCC/intrinsic-ligament surface files in the published list. |
| [TFC UTE MRI study, Geneva/Balgrist/EPFL](https://doi.org/10.3390/life15071117) | Article CC BY 4.0; source paper says additional data are available by request | TFC disc segmentation reviewed by a senior radiologist; potentially valuable original evidence. No public raw segmentation download or license for unpublished data is supplied. Also does not claim all TFCC/SL/LT components. |
| [Rotator-cuff MRI reconstruction study](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0274075) | Article CC BY; availability statement places relevant data within the paper | Expert-reviewed cuff masks are described, but no downloadable 3D tendon/pulley dataset was found in the article's release. Article licensing alone does not grant access to unpublished clinical data. |

Targeted NIH 3D searches did not reveal a directly downloadable TFCC/intrinsic
ligament asset with suitable validation. This is a search result limitation,
not a claim that no such asset exists anywhere in that repository.

## Best legitimate next acquisition routes

1. **Clarify this acquired dataset with the source authors before promotion.**
   Request the anatomical name mapping for all RUL/carpal branches, verified
   units/laterality/axis directions, interpretation of the open PLY surfaces,
   and any independent wrist/TFCC shape-validation results. The source is
   already reusable; the missing requirement is anatomical adequacy evidence.
2. **For genuinely image-grounded TFC detail, obtain the reviewed source masks
   from the Geneva/Balgrist/EPFL study.** Its corresponding author explicitly
   offers additional data on request. Obtain de-identified source images,
   masks, label dictionaries and native coordinate transforms, with written
   permission for commercial redistribution of derived meshes. Ask whether
   TFCC peripheral components and SL/LT were acquired or annotated; the paper's
   central-disc work must not be inflated into whole-wrist coverage.
3. **For the full reporting requirement, commission or license a coherent,
   anatomist/MSK-radiologist-reviewed wrist set** if those research data cannot
   cover the required components. The acceptance inventory must separately
   name SL dorsal/volar/proximal components, LT components, TFCC disc and
   attachments, radioulnar bundles, ECU subsheath and other requested structures.
   A commercial-use label without permission to redistribute the actual mesh
   is insufficient.

No external message, registration, purchase or access request was sent. These
are concrete next acquisition paths; the clinical/commercial fidelity goal
remains incomplete for the wrist.

## Reproducible evidence

New tools: `tools/anatomy_sources/wrist_inventory.py` and
`tools/anatomy_sources/wrist_render_audit.py`. They write only to the staging
folder. The first verifies the published ZIP checksum before extraction; the
second records exact-coordinate topology and attachment checks and creates the
QA figure. Source files remain intact. Research dependencies are the isolated
NumPy/trimesh/Matplotlib environment already used for the earlier mesh audit.
