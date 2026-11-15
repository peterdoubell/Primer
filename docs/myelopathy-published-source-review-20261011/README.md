# MRI myelopathy source and expanded requirement draft

Prepared 2026-10-11 for `ra.mri-myelopathy` in the current release checkout.
Twenty-five complete source figures and two unchanged publication PDFs are
preserved in **8,738,864 bytes (8.334 MiB)**. This fits the stated 26 MB runtime
margin and the requested sub-15 MB source selection without reducing pixels,
resolution, annotations or colour channels. Shared runtime, registry, evidence,
curriculum and structure inventory were not changed.

The source review establishes source identity, a commercial redistribution
licence grant and pixel preservation. **Clinical approval, fine anatomical
approval and complete requirement coverage remain false.**

## Files and reproducibility

- [Original source proof](original-source-review.json) binds article XML/PDF,
  complete captions, figure objects/pages, encoded streams, decoded samples,
  colour profiles, dimensions and packaged SHA-256 values.
- [Complete requirement draft](complete-requirement-draft.json) retains all
  named report fields, walkthrough steps and all 12 shared spine quiz rows:
  **231 structure groups, 2,422 parts, 7,266 image/schematic/model obligations**.
- [Proposed image rows](proposed-image-rows.json),
  [proposed evidence rows](proposed-asset-evidence-rows.json) and
  [integration plan](proposed-integration-plan.json) are reviewable input for a
  later integration; they do not grant anatomical coverage.
- [Actual contract parity](actual-contract-parity.json) verifies the captured
  audit against the actual effective current reporting contract, digest
  `62511becafc9f2507202998b1b50524c607b8772bca43d8092b3da0f8ecc2127`.
- [Visual source review](visual-source-review.json) and the
  [complete figure overview](complete-figure-overview.png) record source-page
  and complete-figure checks. The overview is a review aid, not an image master.

```sh
/Users/peter/Documents/ChatGPT/Primer/.research/runtime-grade-py312-20261008/bin/python tools/anatomy_sources/review_myelopathy_moghaddam2018.py
```

Add `--acquire` only to reacquire the original NLM/PMC Article Dataset files.
The script is restricted to this new review folder and the two unique
`myelopathy-moghaddam2018-*` / `myelopathy-mogad2025-*` media prefixes. It never
edits shared registries, content, runtime code or clinical approval.

## Primary source and rights review

[Sarah Mohajeri Moghaddam and Alok A. Bhatt, *Location, length, and enhancement:
systematic approach to differentiating intramedullary spinal cord lesions*,
Insights into Imaging 9, 511–526 (2018)](https://pmc.ncbi.nlm.nih.gov/articles/PMC6108975/)
provides 24 figures: three anatomical/pattern illustrations and 21 clinical
composites. The acquired original XML and PDF state **CC BY 4.0**. The complete
captions contain no separate attribution, permission block or excluded credit
line. The original acknowledgements credit **Nadezhda Kiriyak** for illustrations
and **Margaret Kowaluk** for figure formatting at the University of Rochester;
the artwork on Figs 1–2 prints **Nadezhda D. Kiriyak**. Both exact published spellings, the formatting credit and visible source signatures remain in the proposed attribution.
No explicit patient consent or ethics declaration was found in this acquired
article XML. The reported ages, sexes, histories and diagnoses remain author
reports; this review does not independently establish patient consent or
clinical truth.

[Santiago Aristizabal Ortiz, Laura Andrea Campaña Perilla and Angela Patricia
Guarnizo Capera, *The “H sign” in MOGAD myelitis*, Neurological Sciences 46,
4771–4772 (2025)](https://pmc.ncbi.nlm.nih.gov/articles/PMC12394311/) provides one
complete four-panel MRI figure. Its acquired XML and PDF state **CC BY 4.0**
with the explicit exception that third-party material is included unless a
credit line says otherwise. The full selected caption and PDF figure have no
such exclusion. The original declarations state retrospective routine-care
ethics approval was waived and written informed consent was given for clinical
testing. They do not separately establish independently verified consent for
our reuse. This case is a source-reported 40-year-old man with prior leukaemia,
C6–T10 cord abnormalities and positive MOG-IgG. The C6–T10 extent comes from the abstract/case presentation; the figure caption reports the central gray-matter H-pattern and longitudinally extensive myelitis without exact levels. These source bases are explicit and separate. Its baseline/follow-up panels
remain separate timepoints with no independently verified registration or
interval.

[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) permits commercial
sharing and adaptation subject to attribution, licence linking, change
indication and no implied endorsement. Proposed rows retain the authors,
article title, DOI, copyright notice, original figure number, licence link,
change description and NLM/PMC dataset-snapshot notice. A source licence grant
does not itself establish patient privacy/consent or clinical approval.

The existing [Radiology Assistant myelopathy page](https://radiologyassistant.nl/neuroradiology/spine/myelopathy)
is retained as the reporting-scope reference. Its images, including credited
third-party examples, were not copied or treated as commercially licensed.
The ANCA myelopathy candidate PMC10349218 was excluded from image acquisition
because its source grant is CC BY-NC-ND, which does not satisfy commercial
redistribution. That does not remove vasculitis from the requirement draft.

## Preservation and image roles

The two publication PDFs are byte-for-byte copies, including their original
vectors, text, annotations and profiles. Every selected PDF figure object is
larger than its corresponding acquired HTML figure. Numbered HTML and PDF
figure binding is checked by low-resolution comparison (RGB RMS under 1.72),
then by source-page review. All 25 image rectangles have **zero meaningful overlaid page
text glyphs and zero intersecting vector paths**, so extracting the complete image
objects does not omit page-level annotation strokes or panel letters. The MOGAD rectangle intersects a whitespace-only text span; it contributes no visible glyph.

Original grayscale JPEG streams are unchanged. Source Flate samples are
packaged losslessly without changing channels. Three coloured 2018 schematics
and the coloured MOGAD figure use the exact **3,144-byte source RGB ICC
profile**. PNG profiles are retained directly; for JPEG, ICC is inserted as
metadata only. Removing that inserted segment reproduces the original JPEG
stream byte-for-byte, and decoded samples and ICC bytes are independently
read back. Original JPEG streams and sample files remain under the review
folder; the unchanged complete PDFs preserve their original encoding context.
Highest resolution is established among the acquired HTML/PDF versions, not
for an unavailable scanner-native or author working master. Display colour
calibration and standalone browser/display equivalence are not independently approved.

The source image-object rendering intents are explicitly recorded: 2018 RGB
Figs 1–3 use `/Perceptual`, while 2025 Fig 1 uses `/RelativeColorimetric`.
All four retain the same source ICC profile whose header intent is 0
(perceptual). The unchanged PDFs preserve their complete OutputIntent and
image-object override context. Standalone PNG/JPEG samples and ICC bytes are
preserved, but equivalent rendering of the PDF override in a browser is
**unverified**; no blanket colour-context approval is granted.

| Source figures | Reported role | Boundaries of the evidence |
| --- | --- | --- |
| 2018 Fig 1–3 | Original tract anatomy, axial pattern and short/long illustrations | Schematic teaching context; no patient-specific tract geometry or native 3D. |
| Fig 4–5 | Short/partial right lateral MS examples; T2/MERGE/STIR and enhancement | Source-reported MS; not an independent dissemination-in-time/space or molecular diagnosis. |
| Fig 6 | NMOSD cord example and right optic nerve enhancement | Orbital and cord panels have distinct sequences; no inferred full optic pathway or brain coverage. |
| Fig 7 | Paediatric ADEM cervical/thoracic cord and thalamic example; follow-up | Different regions and timepoints; no registered volume or complete remission claim. |
| Fig 8 | Source Guillain–Barré conus/root example | Peripheral root process is kept distinct from intramedullary cord tissue. |
| Fig 9–12 | Partial transverse myelitis, HIV dorsal pattern, copper/B12 dorsal-column examples | Overlapping patterns; causal diagnoses and biochemical results remain source descriptions. |
| Fig 13–17 | Ependymoma, haemangioblastoma/syrinx, astrocytoma, metastasis and historical spinal GBM cases | Separate patients, levels and components; imaging does not establish current molecular type/WHO grade. |
| Fig 18–20 | DAVF/AVM flow-void and vessel examples | DSA panels are separate from MRI; Fig 19 MRA is a distinct acquired sequence. Fig 18c retains the burned-in **LEFT T-7** acquisition-panel marker. Its cord lesion side remains unreported; the marker does not independently establish feeder anatomy, full endpoints or MRI findings. |
| Fig 21 | Source cavernoma with T2/GRE/postcontrast appearances | Susceptibility pattern is an example, not full lesion anatomy or a specific diagnosis independent of clinical evidence. |
| Fig 22 | Cord infarction with paired DWI/ADC; ancillary CT angiography | CT arterial/aortic context cannot supply missing MRI signal; no newly calibrated diffusion values. |
| Fig 23 | C3–C4 degenerative compression and focal cord signal/enhancement | Local selected views; no complete multilevel examination or substitute for epidural tumour/haematoma/trauma. |
| Fig 24 | Hirayama anterior-horn signal and left-conspicuous atrophy, flexion dural displacement | Posture evidence is explicit; no dynamic animation, independent registration or 3D motion claim. |
| 2025 Fig 1 | Source MOGAD C6–T10 gray-matter H-pattern, baseline and follow-up T2 | H-pattern is not specific; source antibodies and case diagnosis remain separate evidence. |

All MRI, MRA, DSA, CT, schematic, paediatric/adult, side, sequence and timepoint
roles are explicit in the machine-readable rows. Entire composites remain
intact. A lesion side is not invented from conventional display orientation;
clinical symptom side is not substituted for lesion side. Unreported sequences,
planes and intervals are labelled unreported.

## Full requirement draft and unresolved scope

The draft covers every actual cord region/level, left/right white column and
gray horn, central gray matter/canal where resolved, cord/CSF/pial boundary,
calibre and longitudinal/axial extent; the compressive vertebral, disc,
ligament, epidural, thecal and intradural compartments; conus and each actual
root; every actual perimedullary/feeding/draining vessel, shunt/nidus and
connection; and each acquired brain/orbital/systemic association. Neural and
vertebral levels remain distinct. Adult cord geometry cannot be extended
through the whole lumbar vertebral canal.

The revised draft expands the literal named contexts identified in the independent
source review. Its source crosswalk contains **26 primary TM-table entries**,
**18 differential-graphic entries**, the literal Figure 2 Herpes, Polio,
Post-vaccination, Anterior Horn Ischemia and Cross Sectional Ischemia labels,
explicit Spinothalamic and Lateral corticospinal tract groups with fine parts,
Dorsal columns/Central canal links, and five supplied clinical/exposure
contexts. In total there are **58 literal source crosswalk entries**. Each
actual site, side, source state and condition still requires instantiation;
this is an expanded pending scaffold, not complete source or anatomy approval.

The TM table names HSV, herpes zoster, cytomegalovirus, Epstein-Barr virus,
enteroviruses (poliomyelitis, Coxsackie virus, echovirus), the literal ambiguous
**“human T-cell, leukemia virus”**, HIV, influenza, rabies, Mycoplasma pneumoniae,
Lyme borreliosis, syphilis, tuberculosis, rabies/cowpox postvaccinal contexts,
SLE, Sjogren's syndrome, sarcoidosis, MS, paraneoplastic syndrome, spinal
arterial thrombosis, heroin-associated vasculitis and AV-malformation. These
historical source-reported associations have separate conditional obligations;
clinical or causal validity is not inferred from a table. The comma in the
human T-cell/leukemia label is preserved without silently replacing it with a
modern organism name.

The differential graphic additionally retains literal lymphoma, **Herpes -
VZV**, **HIV - VM - TB**, **Toxo - Fungus**, and cysticercosis contexts. The VM
abbreviation remains unexpanded, and toxoplasma/fungal interpretations require
actual clinical/laboratory evidence. The source metabolic text/Table 2 says
**“nitric oxide use” / “Nitric oxide inhalation”**; it is not silently substituted
with nitrous oxide, which is a different chemical. Source terminology and
clinical/editorial reconciliation remain pending. Neurofibromatosis, NF2,
neurofibromatosis type I and VHL are explicit supplied-clinical-context
dependencies, rather than diagnoses inferred from tumour morphology.

The table and graphic were read by the independent reviewer at their primary
URLs; they were not acquired or copied into the redistributable media package.
The current field/template/walkthrough and quiz crosswalk is complete, while
**full named-source scope remains pending independent re-audit**. Conditions
without acquired clinical figures remain explicit gaps.

All 12 `rad.4.spine-imaging` quiz rows remain as distinct shared dependencies,
with named levels, sides, modalities and structures: disc extrusion geometry;
right migrated L4/L5 fragment; left postoperative L5/S1 scar/disc contrast;
L1 TLICS; disc definitions; metastatic T12/conus and whole spine; T9/T10 cord
versus L4/L5 roots; L2 collapse; L4/L5 Modic versus infection; L2 distraction
plus bowel/mesentery; thoracic radiographic height loss; and L1 PLC integrity.
These myelopathy sources do not certify those separate disc, trauma,
metastatic epidural, postoperative or radiographic requirements.

Fine tract/horn/meningeal boundaries, full native DICOM sequence stacks,
calibrated measurements, complete extent/vascular endpoints, matching
whole-site normal references and source-native patient-specific 3D remain
missing or pending. Source diagnoses, molecular identity, neurological
function, flow physiology, antibody results and treatment causality cannot be
approved from pixels. Zero complete fine anatomical requirements are verified.

The draft also retains qualification issues for specialist review: enhancement
cannot be called absent if not acquired; exact two-segment lesions cannot be
forced into the inherited <2/≥3 binary; H-patterns and enhancement overlap;
and shared TLICS/ordered-disc wording needs clinical/editorial reconciliation.
[NICE NG234](https://www.nice.org.uk/guidance/ng234/chapter/Recommendations)
provides current whole-spine MRI/urgent communication context for the inherited
metastatic-compression dependency. No clinical content repair was executed.

## Next integration work

The proposed rows are concrete and byte-bound. Independent source/licence and
pixel review can now run against these files. Neuroradiology/spinal specialist
review must determine source-specific structures and gaps before any fine
coverage is granted. Later integration should preserve the existing source
rows and historical issues, attach complete examples with credit and original
PDF links, and verify the actual reader in narrow/wide layouts. Native 3D needs
a separately acquired, licensed, source-resolved geometry; the published
schematics are not such a model.
