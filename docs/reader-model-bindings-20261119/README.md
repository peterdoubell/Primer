# Brain reader meshes recorded and bound to the structures their labels name (2026-11-19)

## The decision

Both evidence ledgers' stored 3D models were reviewed on 2026-11-18 (`docs/model-bindings-20261118`,
`docs/msk-model-bindings-20261118`). The app shows more 3D models than the ledgers held. The brain readers show the exact
label-boundary meshes of the SPL/NAC brain atlas, holiAtlas and HippUnfold, and the Schirmer vascular-territory template.
None of these meshes had an evidence record, so none could count as coverage. On 2026-11-19 the project owner asked again
for the 3D models to be bound.

This pass adds a record to the radiology evidence ledger for each label mesh that binds a requirement. Every other mesh of
these readers is listed with its reason.

## What was recorded and bound

186 new model records carry 192 partial bindings and cover 103 requirement leaves. Bound structures and parts go from 1,179
to 1,274 of 57,985. Investigations with none stay at 45. Nothing is anatomically approved, and no radiologist has reviewed
these bindings.

| Investigation | Meshes | Bindings | Bound requirements |
| --- | --- | --- | --- |
| `ra.brain-anatomy` | 127 | 129 | 8 → 72 |
| `ra.mri-neck-spaces` | 41 | 41 | 10 → 23 |
| `ra.mri-epilepsy` | 12 | 12 | 11 → 23 |
| `ra.mri-sella` | 6 | 6 | 30 → 36 |
| `ra.mri-dementia` | 4 | 4 | 2 → 2 |

Brain anatomy gains 64 bound requirements, not 70: its six putamen and pallidal parts were already bound to the MASSP 2.0
models. Both dementia hippocampi were already bound.

| Source | Meshes recorded | Bindings |
| --- | --- | --- |
| SPL/NAC brain atlas: reporting, limbic and additional readers | 111 | 115 |
| holiAtlas v1.0 | 73 | 75 |
| HippUnfold HCP-YA subject 101006 | 2 | 2 |
| Schirmer vascular territories | 0 | 0 |

## Which reader shows which mesh

A mesh counts for an investigation only when that investigation shows the reader (`readers` in `review.json`). A test
checks each one against the catalog's source inspectors.

| Reader | Investigations |
| --- | --- |
| SPL reporting relationships | brain anatomy |
| SPL temporal and ventricular context (18 of the reporting classes) | epilepsy MRI |
| SPL limbic reference | brain anatomy, dementia MRI, epilepsy MRI |
| SPL optic, pituitary and head/neck source | brain anatomy, sella MRI, neck spaces MRI |
| holiAtlas template | brain anatomy |
| HippUnfold registered hippocampus | epilepsy MRI, dementia MRI |
| Schirmer vascular territories | brain anatomy, acute stroke |

The epilepsy context reader holds no mesh files of its own: the server sends its mesh requests to the reporting reader. One
physical mesh file gets one record, which lists every investigation whose reader shows it.

## How a pair was accepted

1. The mesh's own source label names the requirement:
   - in its own words (101 bindings);
   - in another name (53), for example the pellucid septum for the septum pellucidum, the infundibulum for the pituitary
     stalk, or the inferior lateral ventricle for the temporal horn;
   - or as one member of a group the requirement names (38), for example a thalamic nucleus of the lateral region, or a
     suboccipital muscle of the paraspinal muscles.

   All 49 pairs in other words are listed in `review.json` with their reasons. Removing a pair makes the tool refuse its
   bindings.
2. The requirement leaf is one of:
   - the part the label names (113), for example a gyrus of the cortex and surface landmarks;
   - one member of a named group or union (63), for example the masseter in "masseter, temporalis and pterygoids";
   - the structure's own body (12), for example the whole visible course of the fornix;
   - the structure itself, when it has no parts (4): the dementia hippocampi.
3. A side the label states agrees with the requirement and with where the decoded mesh lies (below).
4. The fidelity checker finds no conflict.

A whole is never bound to a requirement that names its parts. The caudate is not bound to its head, body or tail, the
lateral ventricle to its horns, the corpus callosum to its segments, the pons to its basis or tegmentum, or the optic nerve
to its prechiasmatic segment. A part is never bound to its whole. A gyral part, an amygdala nucleus, a hippocampal subfield
and a cerebellar lobule are not bound to the gyrus, amygdala, hippocampus or lobe. Where holiAtlas unites the parts of a
gyrus in one composition (the inferior frontal gyrus, the cingulate gyrus, the insula), that union is bound.

The Schirmer territory masks are not bound. Each one covers a whole arterial territory, deep perforator territory included,
while the brain-anatomy requirements name the cortical, perforator and border-zone territories separately. The stroke
requirements ask for the actual tissue extent "without generic territory mask claim".

## Sides

Each record states the side its label states. The tool decodes every mesh and checks where it lies against a midsagittal
plane fitted to the source's own thin midline structures:

- SPL: the third ventricle, aqueduct, fourth ventricle and septum pellucidum;
- holiAtlas: the third and fourth ventricles and the medulla;
- HippUnfold: each hemisphere is a separate source file, and its affine places it on its own side of the registered
  midline.

A labelled side is supported when most of the mesh lies on that side of the plane and its centroid lies on that side of its
mirror mesh's centroid. A first draft asked for 95% of the vertices on one side, and medial structures failed it. The left
cuneus has 42% of its vertices right of the midline. Its centroid is still 2.3 mm left of the midline and 15 mm left of the
right cuneus. The mammillary bodies, the fornices and the dorsomedial thalamic nuclei also touch or cross the midline. A
swapped pair of labels still fails, and a test swaps one to show it. All 172 sided bindings pass.

Two classes hold both sides: holiAtlas's single superior cerebellar peduncle class and its cortical grey matter. Each has
at least 15% of its vertices on each side. They bind the right and the left requirement, and their records state no side.
The two medulla meshes bind a bilateral requirement and lie on both sides, so their records state both sides.

## What was not recorded

All 567 other label meshes of these readers are listed under `not_recorded`, each with its reason:

| Meshes | Reason |
| --- | --- |
| 213 | No requirement of the investigations whose reader shows the mesh names the structure (most sulci, the fusiform gyrus, the eye and palatal muscles) |
| 94 | One part of a structure that the requirements name only as a whole (gyral parts, Sylvian fissure parts, amygdala nuclei, midbrain nuclei and colliculi) |
| 88 | A cerebellar lobule or lobular zone; the requirements name the lobes, the flocculus and the vermis as wholes |
| 28 | A thalamic nucleus or tract whose place in the four localisation regions is not unambiguous (ventral anterior, centromedian, lateral posterior and dorsal, geniculate, habenular) |
| 28 | A holiAtlas structure mask that repeats a single fine label, which carries any binding |
| 27 | A whole whose parts the requirements name (the caudate, the lateral ventricle, the white matter, the pons, the midbrain, the corpus callosum) |
| 22 | Parts of the hypothalamus, or the whole hypothalamus where no requirement names it |
| 18 | Source groupings and residual classes (all CSF, all deep grey matter, the intracranial mask) |
| 14 | HippUnfold boundary and context classes, including the combined entorhinal/parahippocampal boundary context |
| 14 | Hippocampal subfields and border regions; the requirements divide the hippocampus into head, body and tail |
| 11 | Schirmer vascular-territory masks |
| 10 | Specific cases: the cingulate sulcus segments, holiAtlas's "Lobe Occipital" (a sulcal CSF territory despite its name), both whole optic nerves, and the banks of the superior temporal sulcus |

## The records

Each new record holds:

- the mesh path and hash, and the hash of its face file;
- the mesh's vertex and triangle counts, and its measured side: the share of its vertices right of the midline, its centroid
  offset and its mirror mesh;
- the source context: in vivo, complete label extent, and the stated side. Life stage is recorded only where the source states
  it: adult for holiAtlas and HippUnfold. The SPL atlas describes one healthy volunteer and gives no age;
- the licence:
  - holiAtlas and HippUnfold are CC BY 4.0.
  - The SPL atlas is under Part B of the 3D Slicer licence. It allows use, derivative works and distribution, including in
    proprietary programs. Its terms must go with every copy, and modified versions must be marked. Commercial use is at the
    user's own risk, and the source says clinical applications are neither recommended nor advised.
- a visual review that cites the reader review that checked the mesh against its source label grid;
- a pending anatomical review.

## Not in this pass

- The body readers: liver regions, renal, biliary, dural venous, colon vessels and others. The app links them from module
  pages rather than the catalog's source inspectors, so which investigations show them needs its own review.
- NextBrain: its reader draws boundaries from packed planes and stores no mesh files.
- Patient lesion and annotation meshes (LIDC-IDRI, SOOP, the Bonn FCD case). Earlier reviews grant them no structure
  coverage.
- The MASSP 2.0 models were already recorded and bound.

## Limits

- This checks source labels, requirement leaves and mesh positions. It is not a radiologist review, and the meshes were not
  compared with patient images.
- A source label boundary is not a validated anatomical boundary. Coverage is always partial.

## Files

- `review.json`:
  - the accepted rows (label, evidence, leaf basis, investigations, side);
  - the readers, frames and sources;
  - the pairs in other words, with their reasons;
  - every mesh that was not recorded, with its reason.
- `inverse.json`: the exact byte edit and hashes for the evidence file.
- Tool: `tools/anatomy_sources/bind_reader_models.py`. It refuses a row if any of these holds:
  - its reader is not shown in the requirement's investigation;
  - its label is not the mesh's source label, or does not name the requirement as recorded;
  - its leaf is not the recorded kind;
  - its side disagrees with the label or the decoded mesh;
  - the checker refuses it.
- Tests: `tests/test_reader_model_bindings.py`.
