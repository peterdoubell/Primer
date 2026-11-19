# Body reader meshes recorded and bound to the structures their labels name (2026-11-19)

## The decision

The brain readers' label meshes were recorded and bound earlier the same day (`docs/reader-model-bindings-20261119`). The
body readers show further 3D models that no evidence record covered: BodyParts3D organ and vessel meshes, the segment and
region labels of source MRI cases, ColonVessels vessel segments, HRA bladder regions and the LyNoS mediastinal anatomy. A
mesh without a record cannot count as coverage. On 2026-11-19 the project owner asked for the body readers' 3D models to be
bound.

This pass adds a record to the radiology evidence ledger for each body-reader mesh that binds a requirement. Every other mesh
of these readers is listed with its reason.

## What was recorded and bound

119 new model records carry 204 partial bindings and cover 134 requirement leaves. Bound structures and parts go from 1,274
to 1,400 of 57,985, and investigations with none fall from 45 to 36. Nothing is anatomically approved, and no radiologist
has reviewed these bindings.

| Investigation | Meshes | Bindings | Bound requirements |
| --- | --- | --- | --- |
| `ra.ct-bowel-ischaemia` | 22 | 22 | 6 → 25 |
| `ra.liver-lirads` | 21 | 22 | 0 → 15 |
| `ra.liver-masses` | 21 | 22 | 0 → 15 |
| `ra.ultrasound-gallbladder` | 19 | 21 | 3 → 9 |
| `ra.cardiac-masses` | 18 | 18 | 28 → 36 |
| `ra.mri-cardiomyopathy` | 18 | 18 | 12 → 20 |
| `ra.venous-sinus-thrombosis` | 16 | 16 | 3 → 11 |
| `ra.biliary-duct-pathology` | 12 | 12 | 2 → 9 |
| `ra.mri-bladder` | 8 | 10 | 0 → 5 |
| `ra.ct-cardiovascular-pearls` | 7 | 7 | 29 → 36 |
| `ra.ct-coronary` | 5 | 5 | 2 → 5 |
| `ra.ct-pancreatic-cancer` | 5 | 5 | 0 → 5 |
| `ra.solid-renal-masses` | 5 | 5 | 0 → 5 |
| `ra.mri-epilepsy` | 4 | 4 | 23 → 25 |
| `ra.ct-lung-cancer` | 3 | 3 | 0 → 3 |
| `ra.acute-stroke` | 2 | 2 | 0 → 2 |
| `ra.ct-traumatic-haemorrhage` | 2 | 2 | 40 → 42 |
| `ra.intracranial-haemorrhage` | 2 | 2 | 0 → 2 |
| `ra.renal-cysts-bosniak` | 2 | 2 | 0 → 2 |
| `ra.brain-anatomy` | 2 | 2 | already bound |
| `ra.thoracic-ultrasound` | 1 | 2 | already bound |
| `ra.ct-abdominal-trauma` | 1 | 1 | 5 → 6 |
| `ra.mri-dementia` | 1 | 1 | 4 → 5 |

| Reader | Meshes recorded | Bindings |
| --- | --- | --- |
| BodyParts3D 4.0 atlas: liver, renal, coronary and brain regions | 23 | 59 |
| ColonVessels case pat_012 | 28 | 37 |
| BodyParts3D 4.3 biliary objects | 19 | 33 |
| BodyParts3D 4.3 cardiac objects | 12 | 26 |
| BodyParts3D 4.3 dural venous objects | 16 | 16 |
| TotalSegmentator liver_segments_mr case (liver regions MRI) | 7 | 14 |
| HRA bladder, female and male | 8 | 10 |
| PHLF Center 2 case 24 | 2 | 4 |
| LyNoS Pat9 | 3 | 3 |
| BodyParts3D 4.3 thoracic objects | 1 | 2 |

## Source findings

Decoding the meshes showed that four source objects do not match their labels. None of them is bound. The first three also
affect what the app shows, and fixing the display is a separate task.

- **The app's "hepatovenous segment vii" mesh is a second copy of segment VI.** The official BodyParts3D 4.0 table assigns
  object FJ2409 to segment VII. Its bounds equal those of segment VI (FJ2822) to within 0.4 mm, and BodyParts3D 4.3 lists
  FJ2409 as segment VI (original file "Hepatovenous segment VI.obj").
- **The app's "hepatovenous segment viii" mesh holds segments VII and VIII.** The 4.0 table assigns two objects to segment
  VIII. They are separate pieces. FJ2823 is posterior superior, where segment VII lies, and BodyParts3D 4.3 lists it as
  segment VII. FJ2824 is anterior superior.
- **The app's "trunk of portal vein" mesh is the left and right portal branches.** The 4.0 table assigns objects FJ3102 and
  FJ3122, which BodyParts3D 4.3 names the trunks of the left and right portal vein.
- **The "common hepatic duct" object also holds the common bile duct.** BodyParts3D 4.3 object FJ3079 spans 84 mm in height
  and ends 60 mm below the cystic duct. The source labels no common bile duct. An earlier source review
  (`docs/bodyparts-biliary-source-review.md`) had flagged its extent.

Segments VII and VIII stay covered by the liver-region MRI and the PHLF case, whose meshes lie where their numbers say. A
test checks that against the source axes: right lobe against left lateral section, superior above inferior, anterior before
posterior. Another test checks that each of the 12 bound bile duct tributaries lies inside the segment it is bound to; for
segments VII and VIII it uses the two pieces of the mesh labelled VIII.

Further findings, recorded in `review.json` under `source_findings`:

- Six biliary labels have two objects each, and three pairs occupy nearly the same place: the two cystic duct objects, the
  two medial inferior tributaries and the two caudate tributaries. Each object has its own record, as the earlier source
  review kept them. A pair is not two independent observations.
- The gallbladder and both atrial walls have identical geometry in the 4.0 atlas and in the 4.3 readers. Each file has its
  own record, because a different reader delivers it.

## Which reader shows which mesh

A mesh counts for an investigation only when that investigation shows the reader (`readers` in `review.json`). A test
checks each mapping against the app and the catalog:

- The 3D tab shows the BodyParts3D region named by the investigation's spatial-model family when the investigation has no
  source anatomy reference of its own (`web/radiology-detailed-anatomy.js` maps heart to coronary and kidney to renal). Brain
  anatomy names the BodyParts3D brain as its whole-brain context. No investigation shows the prostate region.
- `web/app.js` links the biliary atlas, the dural atlas, the HyperPIC models, the liver-region MRI, the PHLF and hepatic-vein
  cases and the ColonVessels segments from the investigation pages. A ColonVessels segment counts only where an investigation
  links it: four in each liver investigation, four in solid renal masses, five in pancreatic cancer, and every segment in
  abdominal trauma and bowel ischaemia.
- The catalog's source inspectors open the BodyParts3D 4.3 cardiac and thoracic objects, the TotalSegmentator readers and
  LyNoS; its source anatomy references open the HRA bladders.

Readers linked only from curriculum module pages (`kidney-adrenal-s0028`, `cptac-renal-contours`, `msd-pancreas`,
`liver-s0028`), patient lesion and case readers, and the unlabelled VENAT threshold surfaces are listed under
`readers_not_in_scope` with their reasons.

## How a pair was accepted

1. The mesh's own source label names the requirement:
   - in its own words (84 bindings);
   - in another name (60). Examples: BodyParts3D's hepatovenous segment II is Couinaud II; the source dataset's
     liver_segment_2 is Couinaud II; the right branch of the proper hepatic artery is the right hepatic artery; the sinus
     confluence is the torcular; the HRA region named for the bladder neck's smooth muscle is the wall of the bladder neck;
   - or as one member of a group the requirement names (60). Examples: a papillary muscle of the papillary groups, a valve
     cusp of the leaflets, Trolard's and Labbé's veins of the right cortical veins, a colic vein of the colic tributaries.

   All 59 pairs in other words are listed with their reasons, and each is used by a binding. A listed label word must match
   whole words, so hepatovenous segment II cannot name segment III. Removing a pair makes the tool refuse its bindings.
2. The requirement leaf is one of:
   - the structure's own body (88), for example a Couinaud segment's actual parenchymal territory, a kidney's complete
     renal extent, a gallbladder's complete surface or a vessel's lumen;
   - one member of a named group or union (57);
   - the part the label names (48);
   - the structure itself, when it has no parts (11): the dural sinuses, the jugular bulb and the deep veins, and the diaphragm.
3. The requirement is anatomy. A leaf whose context asks for an example of pathology is never bound to these sources.
4. A leaf that names a lumen is bound only to ColonVessels. Its surgeons segmented each vessel on contrast-enhanced CT, so
   the segmentation outlines the opacified lumen. A BodyParts3D vessel surface shows neither the lumen nor the wall alone.
5. The source's population fits the investigation. These adult sources are not bound in the paediatric renal tumour or
   neonatal brain investigations. The KCL cervix atlases describe pregnancy anatomy, so they are not bound in cervical cancer
   staging.
6. The object lies where its label says, and is no wider than its label (see "Source findings").
7. A side the label states agrees with the requirement and with where the decoded mesh lies (below).
8. The fidelity checker finds no conflict.

A whole is never bound to a requirement that names its parts:

- segment IV is not bound, because IVa and IVb are required;
- neither venous system of the hepatic CT case, nor ColonVessels' union of every artery or vein;
- neither source's wall of both ventricles;
- the LyNoS azygos vein is not bound where the requirement splits its course from its arch;
- nor the HyperPIC venous wall.

Where a requirement splits a vessel or duct into lumen and wall, a surface of the whole vessel binds neither. That holds for
the BodyParts3D renal arteries, the coronary segments and the oesophagus. A part is never bound to its whole: one head of a
papillary muscle is not bound to the papillary groups.

The earlier source reviews' limits stand. The TotalSegmentator cardiac labels stay CT context: their review says the
chamber regions establish no walls, appendages or valve-defined blood pools. The HyperPIC labels 2 to 5 are the
simulation's cut planes where its domain ends in each sinus, not the sinuses.

## Sides

Each frame's axes come from the source's own anatomy where it has asymmetrical anatomy:

| Frame | Right of the body | Midline |
| --- | --- | --- |
| BodyParts3D 4.0 and 4.3 | −X: the liver's right lobe and the gallbladder lie at −X, the ventricles and the circumflex artery at +X | plane fitted to the third and fourth ventricles and the prostate |
| ColonVessels | −X: LPS millimetres; the splenic vessels lie at +X and the portal vein at −X | x = mean of the coeliac trunk and superior mesenteric artery |
| HRA female bladder | −X: each region has exactly the coordinates of the HRA united female body, where the left ovary, tubes, ureter and ilium lie at +X | x = mean of the trigone and bladder neck |
| HRA male bladder | −X by the release's convention | x = mean of the trigone and bladder neck |

The BodyParts3D 4.3 readers share the 4.0 coordinates: their gallbladder and atrial-wall meshes are identical to the 4.0
meshes with the same identifiers. The ColonVessels and HRA midline structures lie close together, so they fix the plane's
position but not its tilt. ColonVessels does not register its two phases to each other; both are in the scanner's
coordinates, and the centroid of every sided venous mesh lies at least 35 mm from the plane.

The male HRA bladder is symmetrical, and no united male body is stored, so its own anatomy cannot check its axes. Its two
ureteral orifice bindings rest on the source's labels and on the convention that the female organ of the same release
shows. Their records say so.

A side can mean two things:

- **A side of the body** (29 bindings: the kidneys, lateral ventricles, renal and colic vessels, ureteral orifices and the
  right-sided dural objects). Most of the mesh must lie on that side of the midline, and its centroid on that side of its
  mirror mesh's centroid where the source has one. The dural objects are right-sided only, so they have no mirror.
- **A half of one organ** (78 bindings). The side word names a half of an organ, not a side of the body: the hepatic veins
  and ducts, the hepatic artery branches, the atria, the coronary arteries, the ventricles' papillary muscles and the valve
  cusps. The mesh's centroid must lie on that side of its named partner. The organ itself may lie across the midline:
  - the left hepatic duct has 72% of its vertices right of the body's midline;
  - the right coronary trunk has 43%;
  - the right ventricle's papillary muscles lie left of it.

  The record states the side only where a requirement of that side needs it.

A test swaps the right kidney's label to show that a body side is caught, and swaps the right hepatic vein's label to show
that an organ half is caught. The BodyParts3D 4.3 diaphragm holds both domes. It has at least 15% of its vertices on each
side, so it binds the right and the left diaphragm, and its record states no side. The posterior interventricular branch is
not recorded. Its label's side names its parent artery, its groove lies left of the midline, and no left-named partner
exists to check against.

## What was not recorded

All 142 other label meshes of these readers are listed under `not_recorded`, each with its reason:

| Meshes | Reason |
| --- | --- |
| 44 | LyNoS annotated lymph nodes. The requirements name stations and nodal findings, and one node mask with conflicting or undefined station terms shows no station's extent |
| 19 | No requirement of the thoracic ultrasound investigation names it (intercostal muscles, atrioventricular valve leaflets, upper and middle lobes, liver, spleen) |
| 15 | ColonVessels branches that no requirement names; the trauma requirements name whole arterial and venous trees |
| 10 | HyperPIC simulation cut planes and the wall of its whole venous domain |
| 8 | KCL pregnancy cervix atlases |
| 5 | TotalSegmentator cardiac labels, which their source review limits to CT context |
| 4 | Dural sinuses that no requirement names (cavernous, petrosal, occipital) |
| 4 | HRA regions both labelled "fundus of urinary bladder", which the source's node names call dome and base |
| 4 | Whole lower lobes, where the requirement names the lung base |
| 29 | The four objects under "Source findings"; wholes whose parts are required (segment IV twice, both venous systems, the two vessel unions, both ventricular walls); lumen and wall splits (the BodyParts3D renal arteries, the oesophagus); the paediatric-only ureters and bladder; the unshown prostate region; the cerebral hemispheres; the PHLF tumour mask; the great cerebral vein labelled with a side; the posterior interventricular branch; one papillary head; the plural right renal arteries; and the source's right supracolic vein |

## The records

Each new record holds:

- the mesh path and hash;
- the mesh's format, its vertex and triangle counts, and, in a frame, its measured side: the frame and what its axes rest
  on, the share of its vertices right of the midline, its centroid offset, and its partner mesh and partner kind;
- the source context, which states only what the source states:
  - BodyParts3D is one adult male reference body, setting not stated;
  - ColonVessels is an in vivo patient case from an adult cohort (its README, quoted in `evidence/`);
  - LyNoS, the liver regions and PHLF are in vivo patient cases with no stated age, and the PHLF case's state records its
    liver tumour;
  - the HRA bladders are adult female and male reference organs.

  Every record states complete label extent, and a side where one is stated;
- the licence, with a stored copy of its evidence:
  - BodyParts3D 4.0 is CC BY 4.0 (the official README of 25 February 2025, stored in `evidence/`);
  - the BodyParts3D 4.3 objects are CC BY-SA 2.1 Japan, so adaptations are shared alike;
  - ColonVessels, LyNoS, the liver regions dataset and PHLF are CC BY 4.0 (their Zenodo records, stored in `evidence/`);
  - HRA is CC BY 4.0 (its metadata);
- a visual review. It is `source_checked` where an earlier review compared the delivered mesh with the original object or
  label grid, and it cites that review. It is `pending` for BodyParts3D 4.0 and ColonVessels: their manifests record the
  source identifiers, hashes and counts, but no review compared the meshes with their sources. Nine dural objects came from
  a pinned mirror of the checksum-verified archive, without a fresh comparison with the primary endpoint; their records say
  so;
- a pending anatomical review.

## Limits

- This checks source labels, requirement leaves and mesh positions. It is not a radiologist review, and the meshes were not
  compared with patient images.
- A source label boundary is not a validated anatomical boundary. Coverage is always partial.
- The label check against BodyParts3D 4.3 covered every BodyParts3D mesh of these readers. The other sources have no second
  table to check against; their labels were checked against mesh positions only where a name states a side or, for the liver
  segments, a position.
- ColonVessels tags its segments as in progress, and the liver-region and PHLF cases come from different people than the
  vessel cases; nothing here registers them to one another.

## Files

- `review.json`:
  - the accepted rows (label, evidence, leaf basis, investigations, side);
  - the readers, frames, sources and partners;
  - the pairs in other words, with their reasons;
  - the source findings, the population limits and the sources excluded as a whole;
  - every mesh that was not recorded, and every reader out of scope, with its reason.
- `inverse.json`: the exact byte edit and hashes for the evidence file.
- `evidence/`: the BodyParts3D 4.0 licence statement, the quoted rows of its object table, the four Zenodo records and the
  quoted lines of the ColonVessels README. Each excerpt gives the hash of the complete file.
- Tool: `tools/anatomy_sources/bind_body_reader_models.py`. It refuses a row if any of these holds:
  - its reader is not shown in the requirement's investigation;
  - its label is not the mesh's source label, or does not name the requirement as recorded;
  - its leaf is not the recorded kind, or asks for an example of pathology;
  - its lumen leaf comes from a source that is not a lumen segmentation;
  - its source's population does not fit the investigation, or the review excludes the source as a whole;
  - its side disagrees with the label, the requirement or the decoded mesh;
  - the checker refuses it.
- Tests: `tests/test_body_reader_model_bindings.py`.
