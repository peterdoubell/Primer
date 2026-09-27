# Elbow/wrist soft-tissue acquisition pass — 26 September 2026

**Outcome: no new commercially cleared fine soft-tissue volume was acquired.**
This bounded pass found concrete new data/reuse limitations, rather than a
verified replacement for the elbow UCL/RCL/LUCL/annular complex, common tendon
origins, distal biceps/triceps, or wrist TFCC/SL/LT. No runtime asset, evidence
approval or existing source geometry was changed. Existing Z-Anatomy, Hamze,
TFCUTE, FDA shoulder and Leeds ankle acquisitions were not downloaded again.

## New primary releases checked

| Source | Actual access/rights evidence | Result for requested tissue geometry |
| --- | --- | --- |
| [Mayo wrist Data, Zenodo 18353473](https://zenodo.org/records/18353473) | Public API and 8,230-byte README acquired. Both specify CC BY 4.0. Listed data archive 37,753,485 bytes. | README describes raw/smoothed **bone** STLs and kinematic transforms. No TFCC/SL/LT tissue volume is established by this data release. Bone-only archive not downloaded unnecessarily. |
| [Linked Mayo wrist Model, current record 18354296](https://zenodo.org/records/18354296) | Model concept DOI 18166610 resolves to this record. Official API explicitly says **CC BY-NC 4.0**, despite the Data record's CC BY 4.0. | The Data license must not be transferred to the separate Model. No model geometry imported under assumed commercial rights. |
| [Brno proximal-ulna FE dataset, Zenodo15155804](https://zenodo.org/records/15155804) | Official API: CC BY 4.0; one 8,346,225,911-byte archive. | [Primary methods](https://link.springer.com/article/10.1186/s13018-025-06031-4) explicitly use tension-only LINK180 spring elements for tendons/ligaments. Cartilage is a uniform 1 mm extension. The 8.35 GB archive was not downloaded: it does not supply the requested soft-tissue volumes. |
| [Physiome elbow exposure a3d](https://models.physiomeproject.org/e/a3d) | Official exposure request returned HTTP 403. | No retry, alternate access workaround or geometry claim. Actual fine-tissue content and commercial terms remain unverified. |
| [KU Leuven digital human forearm/hand](https://gbiomed.kuleuven.be/english/research/50000737/research/HMB/isihealth/our-members/members/00071933/view?pubsonpage=20&pubtype=&sortby=popularity) / MorphoSource P419 | Institutional record identifies the exact legacy repository project. A normal request to that link returned an **Anubis anti-bot challenge**, not project data. No challenge was solved. | A potentially useful imaging/dissection route; actual per-file licenses and tissue meshes remain unverified. No assumption that “open access” grants commercial reuse. |
| [Shang et al. 2026 forearm FE model](https://link.springer.com/article/10.1186/s12891-026-09672-6) | Primary paper makes data available by corresponding-author request only; article is CC BY-NC-ND 4.0. No public model supplement found. | Describes 11 ligament/triangular-fibrocartilage surfaces and tendon reconstructions, but no reusable geometry acquired. Article rights do not license unpublished model files. No author contacted. |

## Why the distinction matters

The new Mayo releases illustrate a material licensing boundary: the exact
Data record and the exact Model record have different licenses. Their titles
and shared project description cannot bridge that difference. The downloaded
data README describes its own bone geometry and transform formats, not
segmented intrinsic wrist ligaments. A calibrated biomechanical model or a
ligament-injury research aim does not itself establish a tissue surface.

The Brno source is anatomically constrained and may be useful for its stated
fracture-fixation research. It was not rejected simply because cartilage was
constructed algorithmically. Its **ligaments and tendons are springs**, so
treating them as high-fidelity volumes would change the source representation.
No commercial asset purchase was made as an alternative.

Kerkhof et al.'s [primary 2018 study](https://pmc.ncbi.nlm.nih.gov/articles/PMC6183001/)
describes a 60-year-old left cadaveric forearm imaged with 7 T MRI and CT, followed
by dissection, with bone/cartilage/muscle STL surfaces and muscle pathways in
MorphoSource P419. Those linked measurements and medical images could support
future source-specific reconstruction; they are not evidence that UCL/LUCL,
common-origin, distal tendon, TFCC or SL/LT volumes are already available.
The browser route later presented a challenge, so no further retrieval was
attempted through that route.

Shang et al. describe CT/MRI-derived bones/muscles with CAD-built ligament and
tendon structures constrained by anatomical references. Reported validation
emphasises muscle dimensions and axial wrist contact mechanics, not each fine
ligament boundary. The paper itself lists small-structure refinement as future
work. Thus even an eventual licensed release would need exact label, coordinate,
attachment and local-shape review; the paper's “high-fidelity” title is not an
approval of the structures needed here.

## Preserved evidence and next legitimate route

Staging is limited to metadata and the public data README under
`/tmp/primer-msk-sources/elbow-wrist-next/`:

- `18353473-metadata.json`: Mayo Data, actual record 18353473, CC BY 4.0.
- `18166610-metadata.json`: concept lookup response identifying actual Model
  record 18354296 and CC BY-NC 4.0.
- `15155804-metadata.json`: Brno rights, archive size and published checksum.
- `wrist-18353473-readme.txt`: exact downloaded description of supplied bones
  and kinematic formats.
- `morphosource-p419-response.html`: challenge response, **not** a dataset or
  a license grant.

The new institutional route worth pursuing through its ordinary authorised
workflow is [MorphoSource P419](https://www.morphosource.org/Detail/ProjectDetail/Show/project_id/419):
first verify the actual media list, access requirements and per-file commercial
redistribution terms. Then determine whether native tendon/ligament volumes
exist or whether only images, muscle volumes and pathway points are supplied.
For the 2026 derived forearm model, a future request must separately obtain
native meshes/masks, source transforms, exact component names, local anatomical
review evidence and commercial redistribution permission, including any
underlying-source restrictions. This pass did not send such a request.

The remaining source gap is specific and unchanged: fine elbow ligament bundles
and tendon footprints, and separately resolved TFCC/SL/LT components, require
actual appropriate geometry plus adequate provenance and rights. No missing
coverage was replaced by a cable, label, name match or unverified surface.
