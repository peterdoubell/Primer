# Wrist acquisition and source-review request

**Draft for user review — not sent.** Prepared 2026-09-26. No author, institution
or vendor has been contacted; no permission, price or data release is assumed.

## Recommended first contact

**Sana Boudabbous — `sana.boudabbous@hug.ch`** is the corresponding-author contact
published on page 1 of *Triangular Fibrocartilage Characterization with
Ultrashort Echo Time-T2* MRI: Insights from a Healthy Cohort*, Life 2025;15:1117,
[DOI 10.3390/life15071117](https://doi.org/10.3390/life15071117).
The [primary article archived by EPFL](https://infoscience.epfl.ch/server/api/core/bitstreams/c30fc6ee-f378-478a-a5c0-811ee0666902/content)
identifies her Geneva University Hospital / University of Geneva affiliations.
Its page 9 data-availability statement directs requests for unpublished data to
the corresponding author. This is a published contact route, not confirmation
that the address remains active or that data will be released.

## What the source establishes, and what must be requested separately

| Item | Evidence in the study | Request status |
| --- | --- | --- |
| Source images | Anatomical MRI and 3D PD/UTE sequences in an asymptomatic cohort; 3D sequences report 0.4–0.5 mm slice thickness | Request a reviewed normal-reference wrist with its actual acquired and reconstructed sampling metadata |
| TFC disc mask | Manual disc segmentation guided by the PD sequence, reviewed by a senior radiologist; other TFCC tissues were excluded | Request the original contours/mask, associated images and any existing surface geometry |
| Radial, central and ulnar disc zones | The limitations state that these zones were not separately segmented | Ask whether later reviewed annotations exist; do not imply the published masks contain them |
| Peripheral TFCC, SL/LT and other ligaments | Not established as separately annotated by this paper | Additional-coverage enquiry only, or referral to a suitable dataset/collaborator |

The article's CC BY license applies to its published content. It does not, by
itself, establish the terms for unpublished image volumes, masks or meshes.
The study's asymptomatic cohort is not a blanket certification that every image
is free of degeneration or anatomical variants.

## Data requested

Start with one coherent, de-identified wrist case and its existing reviewed TFC
mask. Additional cases or annotations are useful only where their provenance and
permissions are equally clear. The following component inventory is a request,
not a claim about the study's available coverage.

| Priority | Requested component | Required distinction |
| --- | --- | --- |
| First release | TFC articular disc, distal radius/ulna and carpal bone context | Preserve the whole reviewed disc mask and its native relation to bones |
| TFCC detail, if available | Disc radial attachment and peripheral ulnar attachment; foveal and styloid attachments; dorsal and palmar radioulnar ligament portions | Source-defined names and boundaries; distinguish deep/proximal and superficial/distal components where the evidence resolves them |
| TFCC supporting tissues, if available | Ulnolunate, ulnotriquetral and other identified ulnocarpal components; meniscal homologue; ECU subsheath; capsule/ulnar collateral contribution as defined by the authors | Keep structures distinguishable; explain any shared, disputed or inseparable boundary |
| Intrinsic ligaments, additional enquiry | Scapholunate and lunotriquetral dorsal, palmar/volar and proximal/membranous components | Separately reviewed labels, or an explicit statement that a component is not resolved |
| Extrinsic ligaments, additional enquiry | Dorsal radiocarpal, dorsal intercarpal, radioscaphocapitate, long and short radiolunate ligaments, plus other reviewed available ligaments | Exact source nomenclature, origins/insertions and attachment footprints |

Preferred deliverables are original de-identified DICOM or NRRD/NIfTI volumes;
labelled masks or native ROI contours with a label dictionary; and, if already
available, native-resolution STL/PLY/OBJ/GLB surfaces. A rendered screenshot
alone cannot establish 3D correspondence. Do not request that authors invent
subdivisions which their scans cannot resolve.

## Metadata and source review to obtain

Request these with the files, or a clear indication of what is unavailable:

- **Sampling:** sequence names and acquisition parameters; acquired voxel spacing,
  reconstructed spacing, slice thickness/gap, field of view and any interpolation.
  Confirm these from source metadata rather than assuming the table's displayed
  resolution is the effective anatomical resolution.
- **Frame and identity:** laterality, wrist/forearm position, coordinate convention
  (LPS/RAS or other), units, origin, orientation matrices and all parent or
  cross-sequence transforms. Include a non-identifying case/series linkage.
- **Label provenance:** stable label IDs and anatomical names; exact image used
  for each mask; how ambiguous boundaries, variants, degeneration and partial
  volume were handled; any components deliberately omitted.
- **Mesh history:** conversion method, original polygon count, smoothing,
  decimation, hole filling, cropping, topology repair and any manual sculpting.
  Preserve the originals alongside derivatives and record file checksums.
- **Anatomical review:** reviewer roles, review date, components actually reviewed,
  available inter-reader or reference-comparison evidence, and known limitations.
  Ask whether a named substructure can be represented faithfully, rather than
  asking only whether a whole model “looks accurate.”
- **Release basis:** confirmation that the supplied de-identified material can be
  released for the requested use, who has authority to license it, and whether
  third-party or consent restrictions affect particular files. No direct patient
  identifiers or unnecessary clinical records are requested.

Receiving files would begin technical and anatomical review. It would not
complete the wrist fidelity goal automatically. A whole-disc approval would
not be copied to unreviewed TFCC subdivisions or SL/LT components.

## Rights required for the planned use

The request should describe Primer as an educational/reference website that may
be distributed commercially. Ask for the applicable written license or agreement
and its exact file/version scope, covering:

1. Internal storage, processing and anatomical review of the de-identified source
   images, masks and meshes.
2. Creation and review of derived segmentations, native-coordinate mesh exports,
   labelled illustrations and other format conversions, with changes disclosed.
3. Public display of selected images and interactive 3D derivatives on a
   commercial website, and delivery of mesh data to users' browsers. Web meshes
   may be technically downloadable; a render-only permission may not cover this.
4. Hosting, caching and distribution of the approved derived assets through the
   website's normal infrastructure, with any required attribution and notices.
5. Retention of approved versions and corrections. Identify whether further
   downstream redistribution is permitted, required by an open license, or
   restricted under a bespoke agreement.

A clear asset-specific CC BY 4.0 grant would cover broad commercial sharing and
adaptation subject to its conditions; another explicit agreement may also work.
No grant is presumed. Record any attribution wording, exclusions, review
conditions, term, fees or territorial limits the rights holder actually supplies.
Do not apply contractual restrictions inconsistent with an open license.
[CC BY 4.0 terms](https://creativecommons.org/licenses/by/4.0/).

## Ready-to-send draft

**To:** Sana Boudabbous, `sana.boudabbous@hug.ch`  
**Subject:** Request for reviewed TFC MRI masks and reuse terms — Life 2025, 15, 1117

Dear Sana Boudabbous,

I am developing Primer, an educational radiology reference website, and am
seeking anatomically reviewed wrist data for labelled images and interactive 3D
reference models. The website may be distributed commercially.

Your 2025 Life paper (doi:10.3390/life15071117) identifies a reviewed TFC-disc
segmentation and offers additional data on request. Would it be possible to
obtain one or more de-identified normal-reference wrist image volumes, their
original reviewed disc masks/contours, and any existing native mesh exports?
We would also need the label dictionary, voxel spacing, laterality, coordinate
convention/units and any transforms linking the masks to their source images.

I understand that your study segmented the disc rather than the entire TFCC,
and did not separately segment radial, central and ulnar disc zones. Separately,
please let me know whether your group has reviewed masks or geometry for TFCC
attachments and radioulnar components, ECU subsheath, or the dorsal, palmar and
proximal components of the scapholunate/lunotriquetral ligaments and relevant
extrinsic ligaments. A referral would also be helpful if these are outside the
available data.

Could you specify the license or institutional process for creating derived
meshes and illustrations and displaying/distributing them on a commercial
website? The interactive geometry would be delivered to users' browsers, so
permission needs to cover the mesh files as well as rendered images. We would
retain source attribution, disclose modifications and document the anatomical
scope and limitations. We do not assume the article's license covers unpublished
volumes or masks.

Please also indicate the available component-level review evidence, known
omissions and any applicable access conditions or fees. We can provide a precise
component inventory and return derived outputs for review if that is useful.

Kind regards,  
[Your name]  
[Affiliation, if applicable, and preferred contact details]

## Specific alternative route: review the acquired forearm model

[Hamze et al., Zenodo 3728255](https://zenodo.org/records/3728255) already supplies
CC BY 4.0 geometry: bones, a TFC disc, separate dorsal/palmar RUL objects and
attachment landmarks. Its archive and license metadata have been downloaded
and verified; see [the wrist source audit](msk-wrist-source-progress.md).
The unresolved requirement is anatomical adequacy, not a missing permission to
use that released CC BY material.

The [authors' primary modeling paper, page 1](https://arxiv.org/pdf/2003.11025)
publishes **Noura Hamze — `nourahamze@gmail.com`** and
**Matthias Harders — `matthias.harders@uibk.ac.at`** as contacts. These are the
published 2020 routes; current deliverability is unverified. No contact was made.

A focused request to them should ask for:

- The anatomical meaning of `DRUL1/2`, `PRUL1/2` and the other branch identifiers,
  including which source-defined components correspond to deep/superficial
  attachments.
- Units, side, axis conventions and the intended use of rigid transforms in the
  supplied SOFA scene.
- Whether the disc's open PLY surface is intentional, whether a reviewed closed
  representation exists, and any source images or ground-truth shape evidence.
- Validation specifically for the wrist/TFCC; results for the 15 tested IOM
  ligaments must not be transferred to these structures.
- Any available SL surface and the missing LTL mesh corresponding to the
  published LTL landmark file, plus the exact license for any newer files.

This route could validate a useful constrained reference model. It does not
currently resolve the missing intrinsic ligament surfaces or demonstrate full
clinical wrist coverage. Additional unreleased data would need their own stated
terms, even though the existing archive is already CC BY 4.0.

## Review before sending

Fill in the sender details and confirm the intended commercial distribution
scope. The draft requests information and data; it does not claim clinical
certification, offer payment, accept terms or imply an agreement. Attach the
component inventory if desired. **No email or other external message has been
sent from this task.**
