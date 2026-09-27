# MSK mesh source audit — 2026-09-26

## Decision and limits

**Z-Anatomy is the best immediately actionable source found for a coordinated
six-joint atlas.** Its actual FBX files contain named labra, menisci, ligaments,
retinacula, capsules, bursae, muscles, tendon material regions and peripheral
nerves that the current BodyParts3D selection omits. Bones and soft tissues can
be exported from the same source frame without invented registration.

This is a **coverage upgrade candidate, not clinical approval or proof of
commercial-grade fidelity**. Several critical structures are very coarse. The
source scapholunate and lunotriquetral ligaments have only 12 triangles each;
the native ATFL, CFL, PTFL and plantar calcaneonavicular ligament have 32 each.
Rendering or subdividing these meshes cannot supply missing anatomy. Every
reportable structure still requires an explicit adequacy decision.

All extraction work here was staged under `/tmp/primer-msk-sources`; this source
audit did not modify the existing viewer, BodyParts3D builder or published assets.
A separate integration task may promote candidates after review.

## Acquired, pinned sources

Primary repository: [LluisV/Z-Anatomy](https://github.com/LluisV/Z-Anatomy), commit
`6c7f9016bd5899ac8edafd31b9900c151df42ed6`. Files come from `Resources/Models/FBX/`.
The same joint FBX also appears in the Unity Assets tree with identical SHA-256.

| Source file | Download bytes | Mesh instances inspected | Use |
| --- | ---: | ---: | --- |
| Joints100.fbx | 9,804,796 | 416 | Joint soft tissues and capsules |
| SkeletalSystem100.fbx | 41,339,660 | 1,952 | Bones, articular surface material regions; also many helpers that must be excluded |
| MuscularSystem100.fbx | 37,343,180 | 686 | Muscles, tendon regions, tendon sheaths, retinacula and bursae |
| NervousSystem100.fbx | 53,887,724 | 712 | Whitelisted limb nerves only |

The joint source has 407 unique geometries and 327,886 native triangles.
Different node instances can share one geometry; the right and left ACL are an
example. **Enumerating geometry alone loses instances and their transforms.**
The preliminary pure-Python reader is for raw inspection; the authoritative
export uses native ufbx node instances.

`tools/anatomy_sources/acquire_z_anatomy.py` checks fixed byte counts and SHA-256
for the atlas files, records acquisition evidence, downloads pinned official
[ufbx](https://github.com/ufbx/ufbx) C sources and compiles the local exporter.
No file exceeded 54 MB. The source exporter does not execute embedded code or
load external FBX resources. Blender was not installed. The Python `ufbx`
0.0.5 binding loaded the files but segfaulted during cleanup in this runtime;
the official C implementation completed normally and is the chosen path.

## Licensing evidence and commercial redistribution

The [Z-Anatomy model license at the pinned commit](https://github.com/LluisV/Z-Anatomy/blob/6c7f9016bd5899ac8edafd31b9900c151df42ed6/Resources/Models/License.txt)
identifies the models as a derivative of BodyParts3D and requests both the
BodyParts3D lineage credit and Z-Anatomy credit. Its terms require attribution
and ShareAlike for redistributed derivatives. The [upstream project README](https://github.com/Z-Anatomy/Models-of-human-anatomy/blob/master/Readme.md)
also identifies the authors and mixed-source exceptions.

[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) permits commercial
reuse and adaptation. Distributed adapted atlas assets need that license,
creator/lineage credits, a license link, modification disclosure and no added
restrictions on the licensed material. A product must not describe these
adapted meshes as exclusively proprietary assets. This audit records the
published asset terms; it does not determine the licensing of unrelated app
code or offer a legal opinion about a larger combined product.

Do **not** import the entire atlas under a blanket CC BY-SA claim. The source
notice separately lists inner-ear models under CC BY-NC-SA and a kidney model
under CC BY-NC, plus other third-party brain/cranial-nerve components. The
whitelist here contains peripheral MSK anatomy, excludes these components and
records the exact source object IDs. A later expansion needs its own check.

Current original [BodyParts3D archive licensing](https://dbarchive.biosciencedbc.jp/data/bodyparts3d/LATEST/README_e.html#license)
is CC BY 4.0, updated in February 2025. That makes direct current BodyParts3D
reuse less restrictive, but does not remove Z-Anatomy's ShareAlike terms on its
adaptations. Preserve the older lineage credit supplied by the Z-Anatomy file
and explain the distinction rather than silently relabelling the adaptation.

## Exact extraction and coordinate contract

`tools/anatomy_sources/export_ufbx.c`:

- Evaluates each source node's `geometry_to_world`, including parent transforms
  and instanced negative scale, using ufbx.
- Preserves native world units: **centimeters**, `+X = patient left`,
  `+Y = superior`, `+Z = anterior`.
- Uses the source polygon faces, triangulated by ufbx; no decimation, smoothing
  of positions, procedural anatomy, pose fitting or BodyParts3D registration.
- Preserves source normal seams by indexing unique position/normal pairs;
  normals use the inverse-transpose transform. Mirrored instances have their
  triangle winding corrected.
- Exports source-assigned material face groups separately when present.

Axis evidence comes from actual anatomical meshes, not label helpers: right
scapula X is −17.358 to −6.061 cm and left scapula X is +6.061 to +17.358 cm.
Body of sternum Z is +6.914 to +13.079 cm, while vertebra T6 Z is −10.013 to
−3.337 cm. Knee structures have lower Y than shoulder structures. The right
ACL world bounds are approximately X −8.810..−6.692, Y 42.685..45.656,
Z −4.628..−2.168 cm, within the knee's skeletal setting.

The existing BodyParts3D viewer's `[x,z,-y]` transform must **not** be applied
to these already Y-up coordinates. A millimeter representation needs only a
uniform ×10 unit conversion, with the conversion recorded explicitly.

Main staged manifest: `/tmp/primer-msk-sources/staged/manifest.json`.
It contains 359 named objects in 6 regions, 47,174,244 bytes of main geometry,
and 279 material submeshes. All 638 binary files together occupy 106,309,248 bytes.
Each binary uses the existing `BP3D` header layout: vertex count, index count,
float32 world positions, float32 normals and uint32 triangle indices.

Each part records its exact source object and geometry IDs, world matrix,
source FBX hash, output hash, names, region membership and tissue layer.
`bounds` describes rendered vertices; `source_bounds_all_vertices` also retains
source loose-vertex bounds. One transverse knee ligament includes unused source
vertices outside its rendered faces. Submesh bounds use only referenced faces.
Region `focus_bounds` comes from named source capsule/labrum/ligament objects;
the names used to derive it are recorded. Runtime cropping is a viewing choice,
not a new anatomical boundary.

Final tissue classes include `bone`, `ligament`, `capsule`, `labrum`, `meniscus`,
`muscle`, `tendon`, `nerve`, `bursa`, `fibrocartilage`, `fat`, `tendon-sheath` and
`fascia`. Tendon sheaths and fat pads must not be labelled as tendons or ligaments.

## What each joint actually gains

| Region | Staged source objects | Concrete additions | Major fidelity/completeness limits |
| --- | ---: | --- | --- |
| Shoulder | 34 | Glenoid labrum (848 triangles); superior/middle/inferior GH ligaments; GH and AC capsules; CC/CA ligaments; cuff and biceps tendon material regions; bursae; axillary/suprascapular nerves | No reviewed labral subregion or tear representation; biceps tendon material may cover multiple anatomical portions; no cartilage thickness; separately named subcoracoid bursa not found |
| Elbow | 33 | UCL (152 triangles), RCL (96), annular ligament (376), quadrate ligament, capsule, biceps/triceps material regions, major nerves and bursae | UCL/RCL are coarse and not clinically reviewed bundle reconstructions; common tendon origin detail needs separate adequacy review |
| Wrist / hand | 108 | DRUJ disc, palmar/dorsal radioulnar ligaments, carpal ligaments, retinacula, tendon sheaths, nerve branches and hand bones | DRUJ disc is 28 triangles, not a complete TFCC; SL/LT ligaments are 12-triangle blocks; no claim of resolved dorsal/volar/membranous components |
| Hip | 45 | Acetabular labrum (1,408 triangles), ligament of femoral head, ilio/pubofemoral and ischiofemoral ligaments, capsule, periarticular tendon material regions, bursae and nerves | Labrum has no validated tear/clock-face segmentation; no true cartilage layer volume; requested inferior gluteal nerve exact object not found |
| Knee | 49 | ACL (1,576), PCL (788), medial meniscus (284), lateral meniscus (468), collateral/popliteal ligaments, capsule, retinacula, bursae and fat pad | Menisci remain coarse; roots/horns, meniscofemoral ligaments and MPFL completeness require structure-specific review; cartilage material is a surface, not thickness or defect geometry |
| Ankle / foot | 109 | Lateral/deltoid/syndesmotic ligaments, Achilles, other tendon material regions, retinacula, sheaths, plantar structures, nerves and foot bones | ATFL/CFL/PTFL/spring-ligament native meshes have only 32 triangles each; no reviewed fascicular/bundle anatomy or osteochondral lesion model |

Counts include some objects shared across adjacent regions and never establish
clinical completeness. Names are source labels; large grouped objects must not
be counted as individually resolved reportable structures without review.

The skeletal file's `Cartilage.001` material annotates articular **surface
faces**: humerus 803, scapula 731, femur 821, tibia 285 and patella 105 triangles.
This allows honest surface highlighting. It supplies no cartilage thickness,
deep/superficial layer or lesion volume. Similarly, a source `Tendon` material
is evidence for an authored tendon surface region, not automatic evidence that
all named tendon insertions and separate anatomical portions are resolved.

Helper warning: many skeletal `.i`/`.j` objects are 12-triangle label leaders or
landmark boxes under `.s` groups. The selection script excludes them and all
insertion markers. In contrast, the low-detail `Scapholunate interosseous
ligament.r` is the actual named object under the proper intercarpal hierarchy;
its poor detail is a source limitation, not a mislabeled helper count.

## Verification evidence

`check_staged_meshes.py` checks all 638 files for finite positions/normals,
valid indices, native triangle counts, unit normals, hashes and rendered bounds.
Those checks pass. It records source irregularities without silently repairing
them: a few degenerate scapular faces and small numbers of face/normal
orientation disagreements remain. The full per-object record is
`/tmp/primer-msk-sources/staged/geometry-validation.json`.

`render_audit.py` renders source-only six-joint and isolated-fidelity figures in
the staging directory. These are visual QA aids, not certified anatomy plates.
The figures were visually inspected: joint tissues occupy the expected general
skeletal regions in the common source frame, while isolated SL and ATFL meshes
visibly retain block/wedge forms and the medial meniscus has coarse faceting.
This is evidence of the source limitations, not anatomical certification. High
polygon counts, successful parsing and a good-looking render do not replace
expert verification of the clinically named structures.

## Other source routes assessed

**BodyParts3D:** the current builder deliberately selects the official 99%
polygon-reduced 4.0 archive. That archive is registered, attributable and useful
for context, but its downloaded official English indexes have no named
meniscus, labrum, cruciate, talofibular or scapholunate entries. The 4.0 download
page does not offer a full-resolution replacement. A claimed 4.3 mirror is not
substituted without primary provenance and exact licensing verification.

**Open Knee(s):** the official [download catalogue](https://simtk.org/frs/?group_id=485)
currently lists the Generation-1 original package `openknee_v1-0-1.zip` at
158 MB, with MRI, geometry and mesh data. The currently displayed package terms
are CC BY 4.0; old papers/documentation may still say CC BY-SA 3.0, so the exact
release notice should be preserved when acquired. The [project paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC4876308/)
identifies tibiofemoral cartilage, menisci and ligaments as model components.
The observed download-confirmation route redirects to SimTK login. No account
was created and no login was bypassed. This is a strong next candidate for
knee-specific, image-derived surfaces; it would be an independent specimen
frame, not silently merged into Z-Anatomy.

**Open3DModel:** [site terms](https://open3dmodel.com/3d-models/terms/) distinguish
commercial use from redistribution and prohibit redistribution without explicit
permission. An anatomical model being free or tagged for commercial use is not
sufficient evidence for distributing its mesh in Primer. No appropriately
provenanced, complete clinical MSK asset was selected from that catalogue.

## Reproduce the bounded staging work

1. `python3 tools/anatomy_sources/acquire_z_anatomy.py`
2. `python3 tools/anatomy_sources/stage_z_anatomy.py`
3. Run `tools/anatomy_sources/check_staged_meshes.py` with Python and NumPy.
4. Optionally run `tools/anatomy_sources/render_audit.py` with Matplotlib.

The scripts stage data only. The official ufbx C source is pinned at
`26a482ae66871d7de36eb722aa060bce95bce274`; its license is retained alongside the
build inputs. Python inspection dependencies used here were isolated in
`/tmp/primer-msk-sources/python`, leaving the application dependencies unchanged.

## Follow-up: acquired MRI-derived knee candidate

A higher-detail, independently licensed candidate was actually downloaded from
[Universiti Malaya, DOI 10.22452/RD/5T6TZ7](https://researchdata.um.edu.my/dataset.xhtml?persistentId=doi:10.22452/RD/5T6TZ7).
The public Dataverse API explicitly marks the files unrestricted and the dataset
**CC0 1.0**. The 61,109,803-byte STL archive's published MD5 was verified;
its SHA-256 is `0c6c7fa81329dba949e00c7d99de37afef0352368eb5b386eb8034ec0b66ec86`.
It contains 67 actual STL objects. The authors describe MRI segmentation and
smoothing, report UMMC radiologist/radiographer inspection, and acknowledge
omissions of hard-to-distinguish small structures. These are author claims,
not an independent certification by Primer. Source files, readme and API license
metadata are retained in `/tmp/primer-msk-sources/high-fidelity`.

The separate staged provider is
`/tmp/primer-msk-sources/high-fidelity/malaya-knee/manifest.json`.
It contains **28 knee-related objects**, 1,307,920 original facets and 109,861,296
bytes of render geometry after the precisely limited cleanup below. Nothing is
registered, fitted or mixed into the Z-Anatomy frame. The high object count and
facet count do not establish clinical accuracy.

The 14 core objects are femur, tibia, fibula, patella, distal femoral cartilage,
patellar cartilage, tibial cartilage, ACL, PCL, MCL, LCL, patellar ligament,
quadriceps tendon and the source's combined knee-meniscus object. Another 14
already supplied objects preserve knee-adjacent coverage: popliteus, medial and
lateral gastrocnemius, semimembranosus, semitendinosus, biceps femoris long and
short heads, sartorius, gracilis, rectus femoris, vastus medialis/intermedius/
lateralis and soleus. No separate iliotibial-band or plantaris STL was found.

| Core tissue | Original native facets | Render facets | Source detail still unresolved |
| --- | ---: | ---: | --- |
| Distal femoral cartilage | 22,796 | 22,788 | No validated clinical subregion/defect labels |
| Patellar cartilage | 4,364 | 4,364 | No defect grading or histological layer distinction |
| Tibial cartilage | 6,356 | 6,348 | Two main native surfaces in one source object |
| Combined knee menisci | 5,204 | 5,196 | Two main surfaces; no source-labelled roots/horns or separate medial/lateral names |
| ACL | 2,672 | 2,672 | No separately validated bundles or pathology |
| PCL | 2,732 | 2,732 | No separately validated bundles or pathology |
| MCL | 1,784 | 1,768 | No superficial/deep clinical component guarantee |
| LCL | 1,916 | 1,916 | Single source structure |
| Patellar ligament | 10,004 | 10,004 | Source NRRD names this `Tendon_Patella` |
| Quadriceps tendon | 10,472 | 10,472 | No independently labelled tendon layers |

The source meniscus contains two nonzero-area components of 3,196 and 2,000
facets plus an eight-facet empty artifact. The combined semantic identity is
retained. No roots, horns or other anatomical subobjects were fabricated.

### Precisely bounded empty-facet cleanup

Exactly **48 facets** were removed from six source objects:
eight each from distal femoral cartilage, tibial cartilage and menisci, and
sixteen from MCL, plus four each from biceps femoris long head and gracilis. Every removed facet has repeated vertices and an **exactly
zero** cross product evaluated in float64 from the native float32 coordinates.
No nonzero-area component was removed, however small. The original STL files
and their hashes remain untouched. Render vertices that became unused were
dropped. Within the original core set, only the MCL bounding box changes, by at most 1.252594 mm; bounds are recomputed from the retained facets for every object.

`omitted-empty-facets.json` records the source facet indices and reason;
its SHA-256 is included in every part record and the manifest. The 14 core
render objects are watertight after this cleanup. The additional eight empty facets in the knee-adjacent muscles were included
only after the same exact-empty-facet criterion was explicitly authorized.
Near-zero but nonzero-area triangles and all nonzero-area components remain;
some source muscle surfaces therefore still have recorded topology defects.
No clinical completeness claim is inferred from watertightness.

`check_malaya_exports.py` verifies, for all 28 objects, that every retained
triangle corner and normal is byte-equivalent as float32 values to the source,
all indices/bounds/hashes are valid, and the only omitted facets are those 48.
The frozen render total is **1,307,872 facets**. Full muscles are large; an app
should load optional layers on demand or use explicitly disclosed viewing crops,
not invent a simplified clinical substitute.

### Native frame, sampling and image correspondence

All STL headers explicitly declare `SPACE=LPS`; the source segmentation and
image NRRDs also declare left–posterior–superior coordinates. Native coordinates
are **millimeters**, verified against the publicly supplied DICOM geometric
fields and matching segmentation sampling. The display conversion is the proper
rigid basis change `[x, z, −y]`, yielding patient-left / superior / anterior.
No scaling or guessed alignment is applied. Source `RT` designations and the
negative-LPS-X knee support the right-sided identity.

The 382 MB segmentation archive was not bulk-downloaded. Its public HTTP-range
support allowed retrieval of the MRML scene, final segmentation, label map,
color table and one T2 fat-suppressed knee NRRD by exact ZIP member offsets.
Each retrieved member was checked against ZIP CRC and assigned a SHA-256. This
does **not** claim that the full archive's MD5 was verified. A single public
DICOM frame was retrieved only to establish geometry metadata.

The final segmentation sampling is approximately
**1.153846 × 1.153846 × 1.2 mm**; the paired T2-FS knee export is
**1.071429 × 1.071429 × 1.1 mm**. These are exported grid spacings, not a claim
about effective acquisition resolution. Opening, closing, median filtering and
joint smoothing appear in the authors' processing description. Fine STL facets
cannot recover structures below the information available in those images.

The MRML file contains no parent transform nodes. All 28 STL source names match
NRRD segment IDs, layers and label values, with the documented patellar
ligament/tendon nomenclature alias. Twenty-six whole-object mesh/voxel extent
comparisons differ by less than 2.5 mm; tibia and fibula differ by up to 4.7554
and 3.6794 mm respectively. These residuals are retained for review rather than
corrected by spatial fitting. The full numerical evidence is in
`um-registration/registration-evidence.json`.

A possible apparent-origin mismatch is explained by the image grid:
DICOM's Z ≈ +189 mm is the first row's origin for a full-leg image with 925 rows,
negative-Z row direction and 1.153846 mm row spacing. Its field extends to
roughly Z = −877 mm. The knee at Z ≈ −330 mm therefore lies around row 450;
the differing coordinates do not alone imply misregistration.

The derivative DICOM has `Modality=CT` despite a T1 VIBE DIXON series description
and the authors' MRI methods. This inconsistency is recorded. It must not be
presented as a validated original acquisition DICOM. The local MRI/segmentation
overlay is **technical QA only**: independently sampled sagittal planes differ
by about 0.85 mm, and cross-sequence motion/segmentation accuracy has not been
clinically evaluated. Clinical examples should remain separately reviewed.

### Inspection evidence and remaining gap

The comparison figures in `malaya-knee/` were visually inspected. The source
menisci have substantially less faceting than the Z-Anatomy examples and the
cartilage is a separate segmented volume. The soft-tissue arrangement is
coherent in the native knee frame. Source MRI/label contours occupy the expected
general anatomical regions, but this does not establish substructure accuracy
or fitness for clinical reporting. The figures compare different source
subjects; their viewpoints are centered for inspection, never registered to
one another.

This candidate advances knee-specific geometry. It does not resolve the
high-fidelity wrist TFCC/SL/LT gap or the ankle small-ligament gap, nor does it
supply every knee reportable structure or disease state.

Other bounded checks in this pass: Kneeview Zenodo record `17805176` exposes
**CC BY-NC 4.0** and no attached downloadable files, so it was rejected for this
commercial use; Figshare record `3464237` is CC BY 4.0 but contains breast-surgery
FE models, not knee/wrist anatomy; NIH/HRA search results and the University of
Denver Visible Human repository remain unacquired leads, not verified assets.
No SimTK login restriction was bypassed and no noncommercial model was imported.

Reproducible staging tools are `acquire_malaya_knee.py`, `stage_malaya_knee.py`,
`verify_malaya_registration.py`, `check_malaya_exports.py`, and
`render_malaya_comparison.py` under `tools/anatomy_sources/`. They use isolated
Python dependencies (NumPy, trimesh, pydicom and optional Matplotlib) and write
only to the research staging directory.
