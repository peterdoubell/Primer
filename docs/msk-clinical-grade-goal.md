# MSK clinical/commercial fidelity work

Objective: get all MSK radiology modules to clinical/commercial grade. Images,
schematics and 3D models must contain high-fidelity representations of every
structure to be reported on. **This objective is not achieved.** Passing software
tests, acquiring a licensed mesh, or displaying an anatomical name does not
prove anatomical completeness or clinical fidelity.

## Current authoritative scope

`data/radiology/msk-structure-requirements.json` inventories the 22 MSK
investigations and explicitly records supplementary/cross-specialty curriculum
surfaces. Its reporting references match the effective investigation guides.
It currently contains 5,229 structure/representation requirements. It is a draft
clinical specification, including unresolved modality boundaries
and site-dependent conditions. It must not be narrowed to the structures
already available. Parent structures cannot automatically satisfy their
separately reportable substructures.

`tools/check_msk_fidelity.py` checks three independent representation types per
required structure and commercial-use, artifact-fingerprint and review
evidence. `--require-complete` intentionally fails while the actual goal is
unproven. `data/radiology/msk-asset-evidence.json` inventories acquired assets;
source review and viewer QA are kept distinct from clinical approval. A future
review must inspect the actual geometry/images and update exact bindings,
rather than mark an entire region complete from its asset count.

## Progress on 26 September 2026

- Corrected paediatric elbow radiography's inherited DDH/Graf reporting guide
  and hip-model binding. It now has an elbow-specific guide/template and an
  explicitly adult elbow reference; a faithful paediatric model is still missing.
- Fixed camera labels that remained anterior after rotation, supplied exact
  superior/inferior views, and added a full-structure view so regional clipping
  does not permanently hide source anatomy.
- Preserved 76 published source figures and added three source-derived knee
  schematics, spanning shoulder, elbow, wrist, knee, hip,
  ankle/forefoot and spine, with source pixels/captions, source links, explicit modalities,
  actual visible-structure lists and coverage limits. They are available in the
  clinical-image and schematic panes, with full-resolution keyboard enlargement.
  Generated equipment photographs and the generated shoulder-bone scene are
  no longer used as anatomy in the MSK reporting workspace.
  Exact licences are retained: 71 CC BY 4.0, three CC BY 2.0, and two complete
  unchanged CC BY-ND 4.0 figures. The two ND originals have additional source
  SHA/MD5 and whole-figure preservation checks; no adapted versions are used.
  The three new mesh-derived figures retain their source's CC BY-SA 3.0
  Unported terms and are explicitly labelled as new teaching projections.
- The expanded wrist collection includes separate SL/LT MR arthrogram panels,
  TFCC MRI/MRA examples and source schematics. Wrist requirements now separately
  retain the dorsal/volar/membranous SL/LT parts and 13 TFCC components. The exact
  wrist atlas is also available in the wrist-fracture reference without changing
  its radiograph-first reporting scope.
- Added eight ankle/foot figures covering spring components, lateral and
  syndesmotic ligaments, tendon compartments/peroneal course, and explicit
  ultrasound examples. Mixed MRI/schematic panels have separate coverage lists;
  a normal/pathological tendon composite is identified as mixed. Ultrasound
  examples are not credited as MRI evidence. Complete per-digit plantar-plate
  coverage remains unresolved; the later third-MTP MRI and generic lesser-MTP
  schematic do not establish all required sites, and hallux-specific additions
  are not substitutes for digits 2–5.
- Added six hallux source entries, including three cadaveric MRI composites,
  an anatomical schematic and two native ultrasound panels. MRI, schematic,
  dissection and histology observations are visibly separated. Their source
  population, side, digit and acquisition limits remain explicit; histology or
  ultrasound cannot silently prove an MRI requirement.
- Preserved all 48 existing diabetic-foot structure groups and 203 leaves while
  adding nine conditional draft groups/44 leaves and naming 14 MTP/IP joint-site
  pairs. The infection report and site-expansion blocks are unchanged. Hallux
  capsular continuity and FDB middle-phalangeal attachments are explicitly
  distinguished; the added definitions still need clinical review.
- Corrected the diabetic-foot investigation's inherited long-bone model. Its
  adult foot view now frames all 27 existing pedal bone objects, including the
  paired hallux sesamoids, while retaining all 147 source-region parts unchanged.
  No missing plantar-plate, sheath or infection anatomy was invented.
- Added six shoulder source entries covering cuff/interval MRI, cuff footprint
  schematics and an original ultrasound pulley panel. The ultrasound-shoulder
  gallery selectively reuses that ultrasound panel and two relevant schematics;
  its selected gallery does not inherit the shoulder MRI scans. All source
  markings and contributor credits remain intact.
- Added six elbow figures covering anterior/posterior UCL MRI, local triceps
  insertion MRI, native common-flexor/distal-biceps ultrasound, and an attachment
  overlay with separately identified dissection panels. Eleven specific
  component candidates now have byte-bound evidence; ultrasound remains
  unbound to MRI-only targets. All eight elbow entries passed native image,
  label, attribution, zoom and mobile browser checks. No clinical approval was
  inferred from these checks.
- Corrected the elbow guide's common flexor/extensor origin terminology, named
  its already-required brachialis assessment in the worksheet, and added an
  explicit distal-biceps radial-tuberosity coverage check. All 38 parent
  structures and 83 components were preserved.
- Added 13 knee/hip figures covering MCL layers, meniscofemoral ligaments,
  posterolateral structures, both posterior meniscal roots, hip labrum/MRA
  relationships, a local gluteus-minimus insertion and proximal-hamstring
  schematic attachments. Pathological exams, normal variants, adolescent
  subjects, unknown facts and mixed panels remain explicit; one normal target
  does not make its whole exam normal. Fourteen unique local representation
  candidates were added without clinical approval.
- Corrected the hip FAI guide's diagnostic wording to use symptoms, clinical
  signs and imaging rather than require labral/cartilage injury. Alternative
  soft-tissue assessment is explicitly conditional on acquired MRI. All 20
  hip parent structures and 50 components remain unchanged.
- Added a separately selectable Open Knee(s) left-knee reference: 16 source
  objects and 307,024 unchanged facets under CC BY-SA 3.0. Original coordinates,
  facet normals and order survive the 7.7 MB compressed transport. Fourteen
  source-label correspondences were inspected across 84 native MRI sections;
  their agreement is source consistency, not independent tissue accuracy.
  Two tibial-cartilage label variants remain unresolved, fine roots/bundles/
  attachments are not automatically credited, and no raw diagnostic pair is
  published. The separate right-sided sources remain available.
- Imported 359 native Z-Anatomy objects and 131 source-defined cartilage/tendon
  surface regions in six registered regions. Preserved source coordinates and
  licenses; did not fit unrelated datasets together or invent tissue thickness.
  Small ligament and disc meshes remain visibly coarse and unapproved.
- Acquired the CC0 Universiti Malaya MRI-derived right lower-extremity dataset
  and packaged 28 knee-related objects. Cartilage is represented by segmented
  tissue volumes, rather than painted bone regions. The default knee viewer
  uses this source, with the broader reference atlas separately selectable.
  Their geometries are never overlaid or treated as co-registered.
- Exposed the four complete disconnected meniscus/tibial-cartilage components
  as separate medial/lateral selections. The original 28 source objects remain
  intact; 30 display parts retain the same 1,307,872 triangles. An independent
  original-STL audit verifies all 11,544 component facets and normals byte for
  byte. Side labels are explicit positional interpretations, not new author
  segmentation labels or independently validated fine anatomy.
- Added an optional MRI-derived ankle source with 20 native objects, including
  a separate Achilles segmentation, bones and source muscle units. Its 663,266
  retained facets preserve all nonzero source geometry, including small source
  artifacts. This source has no ankle ligaments, cartilage or separately
  segmented distal tendon sheaths; the broader atlas remains separately usable.
- Retained all nonzero-area MRI-derived facets and original coordinates/normals.
  Omitted only 48 proven exactly empty repeated-vertex facets; recorded source
  indices and hashes. The original STLs remain intact in acquisition staging.
- Losslessly compressed the MRI transport from about 110 MB to 41 MB. Only
  approximately 7 MB of bone data loads initially; tissue layers load on demand.
- Corrected the inherited thoracolumbar trauma report and radiographic ankle
  soft-tissue overclaims. Five retained modality/coverage notes now have an
  explicit documented-boundary classification; all unresolved source defects,
  site expansion and clinical-review obligations still block completeness.
- Reviews are bound to the asset bytes and exact anatomical/reporting scope.
  Clinical-image bindings additionally require a compatible explicitly recorded
  modality. These checks prevent a changed source, inferred component or
  ultrasound example from silently satisfying a different MRI requirement.
- Reconciled typed context for the existing 28 clinical-image records and added
  explicit context to the new shoulder entries. Known contradictory side,
  specimen setting, population, depiction, extent and panel claims cannot pass
  merely because a fresh review fingerprint matches. Source-reported ages and
  multi-subject panels remain separate; unknown facts are not invented and
  normal cadaveric anatomy is not automatically rejected as a reference.

## Limits that still prevent completion

The MRI-derived knee is one adult reference with approximately 1.154 × 1.154 ×
1.2 mm segmentation sampling and author-applied morphological processing and
smoothing. A large facet count does not establish fine anatomical accuracy.
Its source combines the two menisci under one label. The viewer now separates
their native disconnected components, but this adds no missing surface detail.
The source omits structures and does not separately delineate all reportable
roots, horns, attachments or bundles.
Source MRI exports and reconstructed DICOM metadata need their own imaging
validation before being offered as diagnostic examples; paired volumes remain
research QA inputs rather than clinical images in the app.
The actual MRML segmentation reference is node 25, the exported image labelled
`108: T1 SAG VIBE DIXON_W L-LIMB`; the separate image labelled `19: T2 FS...`
is node 12 and is not an independently validated pair. The source DICOM also
misidentifies itself as CT with HU units despite the author-labelled MRI data.
Ten structures were reviewed across 60 native-plane comparisons. Gross
correspondence is useful, but fine roots, bundles and interfaces remain
unresolved. Mesh/mask agreement and volume differences measure representation
consistency, not biological tissue error or independent anatomical accuracy.
The clinical-pair flag is now false, public technical provenance is correctly
linked, and original mesh records/hashes/coordinates/approvals are unchanged.

Wrist/ankle ligaments and the DRUJ disc in the broader atlas are particularly
coarse. Dedicated high-fidelity TFCC components, intrinsic/extrinsic ligaments,
cartilage volumes, cuff/pulley/footprint detail, bursae, nerves and other
reporting structures remain incomplete. Paediatric age-dependent anatomy,
thoracolumbar trauma and site-dependent tumour/muscle/arthritis pathways are
not fulfilled by a single adult joint model.

Existing Radiology Assistant figures remain source references; commercial
permission is not established by an attribution or a hotlink. The image audit
distinguishes the app's explicit commercial restriction from the website's
unresolved reuse permission. Replace or obtain documented rights for assets
that are to form part of a commercial product.
The current 22 MSK references still expose 90 distinct publisher key-image URLs.
Their presence must be reconciled with commercial rights or replacements; the
62 locally preserved open figures do not remove that requirement.
Their exact source URLs and investigation usage are recorded in
`msk-runtime-publisher-images-2026-09-26.json`.
The later runtime inventory includes the declared supplementary routes: 204
distinct static reference figures across 30 reporting and 20 lesson surfaces.
Sixty-three now have reviewed local rights records; 141 publisher URLs remain
unresolved for the intended commercial release. The website does grant
educational reproduction with author/publisher credit; commercial distribution,
adaptations, third-party scope and reliable full-resolution delivery are being
reconciled rather than presumed prohibited. A complete source-use appendix and
unsent publisher inquiry have been prepared. The user has been asked for explicit
sending instructions and sender details; nothing has been sent.

The runtime-rights check is independent of anatomy coverage and cannot be
omitted from the readiness result. It includes references still displayed even
when they have no anatomical evidence binding. The public-domain SPECT/CT
teaching composite is now preserved at its original local pixels and credited;
it receives no high-fidelity MSK structure credit.

The newly acquired Leeds ankle FE archive provides real tibial/talar cartilage
volumes but uses haemophilic anatomy, roughly 3 mm MRI slices and no ligament
geometry. It remains staged as a pathological research candidate. Denver's
normal-reference cartilage download remains inaccessible through the observed
official route; its documented inventory also lacks ankle ligament meshes.
These findings are recorded in `msk-ankle-fine-structure-sources.md`; no author
messages have been sent and no candidate was silently promoted as complete.
The separate FDA CC0 shoulder FE candidate is recorded in
`msk-shoulder-source-progress.md`. Its seven volume parts and native transforms
were inspected. Literature-offset cartilage, an unexplained labral-thickness
name, missing cuff/pulley volumes and unprovided CT sampling prevent automatic
promotion to the clinical atlas.
The independent Dryad knee dataset is now acquired through its public browser
download controls; both complete archives match the published SHA-256 values.
Its 12 raw MRI-derived STL objects contain 631,032 unchanged nonzero facets.
The actual export is not a uniformly finer source: its grid is approximately
0.513 × 0.513 × 2 mm, fine anatomical parts are not independently labelled,
and the file called MRI Scan contains only 15,475 nonzero voxels within a
243,609,600-voxel grid. Its mesh-to-image coordinate convention is unresolved.
No clinical image pair or runtime replacement was promoted. Original-source
hashes, native mesh/voxel measurements, rendered reviews and reproducible tools
are recorded in `msk-dryad-knee-source-progress.md` and
`docs/msk-dryad-knee-source-review/`.
The exact author data inquiry is prepared in `msk-dryad-knee-data-inquiry.md`.
Permission to send it through connected Gmail has been requested and remains
pending; no author message has been sent.

The original diagrams and broad source galleries do not automatically count
as high-fidelity coverage. Every actual requirement still needs appropriate
image, schematic and model evidence at useful viewing resolution, with
modality/age/site boundaries and source limitations reconciled.

## Evidence and next work

The source/licensing findings and reproducible extraction commands are in
`msk-mesh-source-audit.md` and `msk-image-source-audit.md`. Native mesh geometry,
source-registration metadata, transport decoding and exact empty-facet
omissions have dedicated checks. Browser checks inspect the real reporting
routes as well as individual layers and structures. These are engineering and
source-reconciliation checks, not a clinical approval certificate.

The later component and ankle-figure phase is documented in
`msk-knee-component-reconciliation.md`, `msk-knee-component-independent-audit.md`
and `msk-ankle-foot-image-progress.md`. A clean private rebuild reproduced all
28 original knee transports and all four component records. Browser checks
verified the 30 component-aware display parts, exact decoded transport hashes,
isolations, source switching, original facet total and mobile behavior.
The current completion audit and evidence fingerprints are recorded in
`msk-verification-components-and-ankle-2026-09-26.json`: 0 verified, 67 candidate
but unverified, and 5,003 missing representation requirements. The 136 focused
tests and browser checks passed; they do not replace the outstanding clinical
and commercial evidence.
The subsequent forefoot/runtime-rights phase is recorded separately in
`msk-verification-forefoot-and-rights-2026-09-26.json`. Its current audit has
0 verified, 83 candidate but unverified and 5,119 missing representation
requirements. The 256 focused tests, hallux/SPECT browser checks and separate
whole-foot browser checks passed; full fidelity remains unproven.
The subsequent source-correspondence phase is in
`msk-verification-source-correspondence-2026-09-26.json`: 0 verified, 105
candidate but unverified and 5,097 missing requirements. Its 294 focused tests
and bounded shoulder/ultrasound/knee browser checks passed. A private rebuild
reproduced the unchanged knee parts and corrected provenance. Ten offline
review sheets and their quantitative report are retained under
`docs/msk-knee-source-review/`, outside the app's clinical image assets.

The latest elbow/source-acquisition phase is in
`msk-verification-elbow-and-dryad-2026-09-26.json`: 0 verified, 116 candidate
but unverified and 5,086 missing requirements, with all 5,202 targets retained.
The final combined run passed 182 focused tests. The eight elbow source entries
passed browser checks, including the original CMYK JPEG and mixed schematic/
dissection caption separation. Geometry and image audits of the newly acquired
Dryad source found unresolved fidelity and coordinate issues rather than
establishing a replacement for the current knee.

The subsequent knee/hip/Open Knee(s) phase is recorded in
`msk-verification-knee-hip-openknee-2026-09-26.json`: 0 verified, 130 candidate
but unverified and 5,072 missing requirements. The full 5,202-target scope
remains intact. The ledger inventories 685 source assets; 16 newly available
mesh objects do not automatically count as their fine reporting components.
The combined MSK/API regression passed 368 tests, plus five coordinate/camera
checks. Source pixels, original licence versions and complete ND figures are
preserved; the author-reported normal specimen is not independently certified.
The [Open Knee(s) review](msk-openknee-public-source-progress.md) links the
durable 14-structure MRI/label/mesh review sheets and actual source evidence.
The [bounded browser audit](msk-hip-knee-browser-audit-2026-09-26.md) passed all
17 current knee/hip records (including 13 additions), every new model part,
source switching/disposal, left-side orientation controls, image enlargement
and mobile layout. These checks preserve the distinction between working
references and the full clinical/commercial fidelity objective.

The tibial-cartilage follow-up is documented in
`msk-openknee-tibial-review/README.md`. It acquired the two candidate masks and
earlier source surfaces, quantified processing differences, and fixed a genuine
on-plane mesh-intersection audit defect. Seven analytic tests pass and the
existing 84-section evidence reproduces exactly. Neither candidate-mask agreement
nor mesh density establishes clinical accuracy; no approval or scope was reduced.

Next priorities remain: resolve the remaining reporting/scope mismatches;
obtain better wrist/ankle and other fine-structure sources; reconcile exact
knee and other regional substructures against the requirements; acquire the
missing normal clinical/schematic examples; then perform and record a full
requirement-by-requirement anatomical, rights and runtime review. Preserve the
full objective while doing this work. No deployment or claim of clinical/
commercial readiness has been made by this phase.

The lesser-MTP follow-up adds one exact original 1420 × 2006 MRI composite,
with normal reference scope restricted to the third-MTP plate in panels a/b.
Its body is one new partial candidate; attachments and other digit sites remain
open. The catalogue now contains 62 original figures and the ledger 686 assets.
The audit remains unproven: 0 verified, 131 unverified and 5,071 missing targets.
The 159 focused tests and actual desktop/mobile image checks pass; see
`msk-lesser-plantar-plate-source.md`.

An original-stream audit subsequently restored 14 previously recompressed
whole-figure JPEGs. All now match their exact PDF DCT streams, with the same
native dimensions and anatomical scope. The repeat audit verifies 19 originals;
five colour/representation cases remain held for separate review. The 201-test
regression and actual-page checks for all 14 restored images passed. See
`msk-original-jpeg-restoration.md` and the current snapshot
`msk-verification-original-jpegs-2026-09-26.json`. This improves source fidelity
without adding invented anatomy or approving existing clinical candidates.

The nested-PDF follow-up recovered four further original JPEG streams and
replaced the CMYK triceps export with a documented native-size lossless PNG
rendition. It also removed decorative night-theme filtering from medical source
figures and their enlarged views. All five figures passed native-dimension,
HTTP-hash and browser checks; 197 regression tests passed. These corrections
are documented in `msk-nested-pdf-and-cmyk-review.md`; anatomical scope and the
clinical/commercial completion assessment remain unchanged.

The forefoot/spine follow-up adds six source figures: a generic lesser-MTP
schematic, a second-toe FDL ultrasound panel, PLC schematic/MRI references,
a functional spinal unit diagram and a mixed ligamentum-flavum comparison.
All retain their actual modality and source context. The forefoot additions
remain unbound to digit-specific MRI requirements. Six local spinal component
candidates are unverified; neither side-specific LF coverage nor whole-exam
normality is inferred. The Cureus PDF's explicit CC BY 4.0 and differing JATS
CC BY 3.0 link are both recorded. Complete annotated publisher PNGs are used
where raw PDF images would omit vector labels.

The current catalogue contains 68 figures and the ledger 693 assets. The
5,202-target audit has 0 verified, 137 unverified and 5,065 missing requirements;
210 runtime reference images comprise 69 rights-cleared and 141 unverified
resources. All six new source files pass HTTP-byte and actual-browser native
image/enlargement checks; source colours, Escape focus restoration and mobile
layout are preserved. The focused checks passed 221 tests. See
`msk-forefoot-additional-references.md`, `msk-spine-image-progress.md` and
`msk-verification-forefoot-spine-2026-09-26.json`. The separate whole-Primer
recheck confirms photographs and 3D bindings for all 558 lessons in 19 subjects,
with all 60 responsive photo files decoded and 15 media tests passing.

The source-view phase adds three native-geometry knee schematics with physical
source scale, explicit left/RAS orientation, direct whole-object labels and
omitted-context notes. An independent ray/mesh check confirms all ten label
anchors are on frontmost source faces. Three local exposed faces now have
unverified schematic and model candidates: patellar-cartilage articular surface
and both meniscal superior surfaces. This is six representation candidates
sharing three source objects, not independent anatomical validation. No source
mesh changed; the unresolved tibial-cartilage objects remain unbound. Each new
diagram opens the matching left-knee source in the 3D pane.

Two spinal figures now use complete annotated PDF renders at 1309 × 844 and
1534 × 583 instead of small publisher previews. Rendering preserves the PDF's
near-native raster sampling plus its vector labels/arrows, without inventing
detail. Exact prior/current hashes and full-page/crop evidence are retained.

The latest [verification record](msk-verification-source-views-2026-09-26.json)
records 71 figures, 696 ledger assets and all 5,202 requirements unchanged:
0 verified, 143 unverified and 5,059 missing. Runtime references comprise
72 rights-cleared and 141 unverified images. The 365-test MSK/API/reader
regression and four analytical renderer tests pass. Actual browser checks
cover all five changed images, source identities, native enlargement, focus
restoration, source-to-3D navigation, a posterior patellar-cartilage view and
390-pixel mobile layouts. See [knee source views](msk-openknee-schematics.md)
and [spine PDF rendering](msk-spine-pdf-rendering.md). Clinical/commercial
readiness remains unproven.

## Source follow-up on 27 September 2026

Completed the interrupted acquisition review for the independent Leeds Knee 2
dataset. The native Enhanced MR object contains 144 frames with consistent
oblique-sagittal geometry and exact pixel decoding. Its stored Vida/18-channel
metadata resolves the acquisition-specific scanner discrepancy. Potentially
identifying metadata values are excluded from the audit; raw-DICOM release
clearance remains unestablished.

The selected `seg_intact_fix` deck contains 291,045 nodes, 180,570 quadratic
tetrahedra and seven source-labelled solid groups. Quadratic coordinates,
six-node boundary faces, tissue interfaces and the author's initial transform
are preserved. Independent parsing agrees on counts, bounds and midside
offsets. Sixty spring connectors implement root mechanics; they do not supply
root tissue geometry. The source's meniscal adjustments for solver convergence,
unknown MRI–FE transform and limited anatomical scope prevent a clinical
replacement claim. Three source projections and six native MRI frames were
inspected and preserved in the [Leeds review package](msk-leeds-knee-source-review/README.md).
No Leeds asset or component binding was promoted to the runtime.

The [Open Knee(s) history review](msk-openknee-tibial-history-review.md) found
additional author notes explaining assembly selection, but no exact `_02`
mask-to-mesh lineage. The denied history-protocol route was stopped. The
[wrist source review](msk-wrist-fine-source-review.md) preserves concrete
rights/coverage exclusions and a formal caption correction, including the
qualification that a saved challenge response cannot prove a source caption.
It adds no duplicate or unsupported figure.

[Verification](msk-verification-source-audit-2026-09-27.json) records fifteen
scientific tests, twenty-six existing fidelity/rights tests, exact independent
report reproduction and eleven preserved evidence files. Optional scientific
modules skip in the production environment without adding heavy dependencies.
Current runtime and requirement fingerprints are unchanged: all 5,202 targets
remain, with 0 verified, 143 unverified and 5,059 missing. The full clinical/
commercial objective remains active and incomplete.

The [boundary follow-up](msk-boundary-followup-2026-09-27.md) classifies two
already-implemented reporting limits: the elbow's retained source terminology
caveat and the hip's acquired-MRI condition. The live reports and every anatomy
definition remain unchanged. All seven documented boundary decisions now bind
their exact report/anatomical scope and their specific interpretation, so a
changed checklist, template, component condition or boundary claim reopens the
issue even when its old evidence document still exists. Other source issues,
missing anatomy, asset reviews and commercial-rights obligations remain blocking.
The [verification record](msk-verification-boundary-followup-2026-09-27.json)
records 170 passing tests and unchanged 5,202-target coverage: 0 verified,
143 unverified and 5,059 missing. This improves the accuracy and integrity of
the completion audit; it does not approve any additional representation.

The [rectus femoris follow-up](msk-hip-rectus-femoris-source.md) adds one complete
source MRI figure identifying local proximal direct/indirect tendon courses.
The original PDF JPEG was decoded to a lossless PNG with its external Adobe RGB
profile attached, preserving all RGB samples, panel letters and arrows. This
is an explicit format adaptation, not a new anatomical rendering. Individual
normality and demographic facts remain unspecified; attachment footprints and
complete course coverage remain unproven.

[Verification](msk-verification-hip-tendon-2026-09-27.json) records 161 passing
tests, exact source pixel/profile checks, and actual desktop/mobile browser
enlargement and focus checks. The current catalogue has 72 figures and the
ledger 697 assets. All 5,202 requirements are unchanged: 0 verified, 144
unverified and 5,058 missing. Runtime references comprise 73 rights-cleared and
141 unverified resources. Clinical/commercial readiness remains unproven.

The [panel-state consistency follow-up](msk-panel-state-consistency.md) fixes
a concrete gate gap: a source-recorded pathological panel could retain a
normal-reference claim if its review fingerprint was renewed. Credited panel
states are now compared with explicit uniform claims, independently of review
freshness. The lesser-MTP composite records its already-reviewed a/b reference
and c–h pathology states; its local binding, source pixels and pending review
remain unchanged. Within-panel region selection and untyped source facts are
not inferred by this check.

[Verification](msk-verification-panel-states-2026-09-27.json) records 235 passing
tests, including a synthetic fresh-review counterexample and real-source
pathological-panel substitutions. Requirements, catalogue, runtime code and
coverage counts are unchanged: 0 verified, 144 unverified and 5,058 missing
across 5,202 targets. This closes an inconsistent-claim path without granting
any anatomical, visual or clinical approval.


## Hip tendon references integrated, 27 September 2026

Boutin and Robinson Figures 6.5 and 6.7 add two partial MRI candidates: the
normal local proximal hamstring cross-sections in 6.5a and the intact psoas
component alongside iliacus injury in 6.7. Full figure panels are retained;
pathological context is explicit. Figure 6.13 was rejected for distal gluteus
medius tendon coverage because that tendon is not pictured. See the
[source review](msk-boutin-hip-source-review.md) and rendering evidence.

The catalog now contains 74 figures and the ledger 699 assets. The unchanged
5,202 requirements comprise 0 verified, 146 unverified and 5,056 missing.
The current [fidelity snapshot](msk-verification-boutin-hip-2026-09-27.json)
continues to report clinical/commercial readiness false. 191 relevant tests
and desktop/mobile checks passed; they do not establish clinical fidelity.

## Explicit completeness evidence, 27 September 2026

The fidelity gate now requires per-requirement coverage evidence independently
of approval and source-context extent. Partial, unknown and missing claims
remain unverified even with fresh reviews; changing a claim invalidates the
review fingerprint. The three recent tendon references are explicitly partial.
No real asset was marked complete or clinically approved. See
[coverage policy and tests](msk-requirement-coverage.md). 183 focused tests
passed. The current [snapshot](msk-verification-coverage-extent-2026-09-27.json)
retains 0 verified, 146 unverified and 5,056 missing of 5,202 requirements.

## Ultrasound knee-injection source gap, 27 September 2026

Rechecked the linked source: its knee example explicitly lacks ultrasound
guidance. The existing issue remains unresolved. A new
[source review](msk-knee-injection-source-review.md) and fingerprinted
[scope proposal](msk-knee-injection-scope-proposal.json) identify a relevant
ultrasound suprapatellar anatomy paper and six targets for full-source review.
Only abstract/caption evidence was accessible; figure pixels and reuse rights
remain unverified after browser challenges and publisher HTTP 429. No source
asset, clinical approval, report change or requirement reduction was made.

## Independent injection atlas acquired, 27 September 2026

The Lungu/Moser 2015 CC BY 4.0 atlas was acquired and its actual ultrasound
Figure 10 inspected. It depicts first-MTP effusion/aspiration, not knee anatomy.
A caption inconsistency (metacarpal versus metatarsophalangeal) is recorded in
the [source review](msk-lungu-injection-source-review.md). No runtime promotion
or false knee/hand binding was made; site-scope and figure preservation remain.


Figure 10 of the independent injection atlas is now preserved offline at native
1302 × 499 grayscale resolution. Independent Poppler decoding matches every
pixel, with original annotations intact. The [preservation record](msk-lungu-injection-source-review/figure10-preservation.json)
documents the lossless PNG adaptation. Site-specific coverage remains unresolved;
no runtime binding or clinical approval was added.

## Matched upper-extremity injection source, 27 September 2026

The first-MTP figure was excluded from the source-defined wrist/finger target.
A new CC BY 4.0 Patel et al. atlas supplies inspected radiocapitellar and
radiocarpal ultrasound candidates for four existing local bone requirements.
Planned trajectory arrows are explicitly distinguished from actual needles.
The [source review and 75-leaf matrix](msk-upper-injection-source-review.md)
preserve all 225 injection representation statuses. Figures remain offline
pending source-preserving extraction and narrow integration; no approval added.


## Upper-extremity injection references integrated

Two unchanged native JPEG figures add four partial ultrasound candidates for
radiocapitellar and radiocarpal bone contours. Only selected ultrasound panels
are bound; positioning photographs and planned trajectory arrows cannot prove
actual needle-tip placement. The catalog has 76 figures and ledger 701 assets.
196 relevant tests and desktop/mobile checks passed. The
[current audit](msk-verification-injection-2026-09-27.json) retains 5,202
requirements: 0 verified, 150 unverified, 5,052 missing; readiness remains false.
See [source and preservation evidence](msk-upper-injection-source-review.md).

## Joint-injection 3D mismatch corrected

The injection investigation inherited a generic vascular-access schematic.
It now offers six attributed regional Z-Anatomy references with explicit
procedure and coverage limits, preserving the original general IR lesson.
[Implementation and verification](msk-injection-model-review.md) include all
six actually rendered regions, one viewer at a time, mobile switching and
145 passing API/investigation tests across the final verified suites. No new
clinical coverage is inferred; the [audit](msk-verification-injection-model-2026-09-27.json)
remains incomplete at the original full scope.

## Hamstring model mismatch identified

An effective-model audit of all 22 MSK investigations found that hamstring MRI
still inherits a generic long-bone schematic. Four relevant native muscle
objects exist in the registered knee atlas, but the default knee crop excludes
substantial proximal geometry. The [binary bounds audit](msk-hamstring-model-review.md)
verifies their preserved full extents and defines the required whole-course
framing work. No anatomy coverage or clinical approval was inferred.


## Hamstring source model implemented

The generic long-bone schematic is replaced by a dedicated full-extent view
of four native posterior-thigh muscles, retaining all 21,492 source triangles
and original coordinates. Reset preserves posterior framing and the muscle
layer; isolation and mobile controls were verified. 28 relevant tests passed.
[Implementation evidence](msk-hamstring-model-review.md) records the remaining
tendon, footprint, aponeurosis and sciatic-anatomy limitations. The
[fidelity audit](msk-verification-hamstring-model-2026-09-27.json) remains false
at the full 5,202-requirement scope, with no new clinical approvals.

## Hamstring model evidence linked

Four native muscle objects are linked to their corresponding muscle-belly
requirements as partial external-surface candidates. Tendon surface patches,
attachments, junctions and internal architecture remain unbound. Source IDs,
mesh fingerprints and view selection are explicit; no clinical review was
invented. 149 focused tests passed. The [current audit](msk-verification-hamstring-bindings-2026-09-27.json)
retains all 5,202 requirements: 0 verified, 154 unverified and 5,048 missing.

## Registered hamstring context added

The hamstring view now offers the native right hip bone, sacrotuberous ligament
and sciatic nerve alongside its four muscle objects. All seven preserve their
shared source coordinates; framing encloses their complete source bounds.
29 tests and browser layer/isolation/reset/mobile checks passed. See
[context evidence](msk-hamstring-model-review.md). Footprints, sacral attachment
context and nerve divisions remain unverified; no new clinical binding was added.

## Hamstring image/schematic integration

Two explicitly selected preserved figures are shared from Hip/FAI into the
hamstring module, retaining exact source identities. Four labelled muscle-belly
schematic candidates are partial; the MRI adds context without new tendon
substructure claims. Cross-topic sharing now requires a hash-bound scope review
for the exact selection. 175 tests and browser decoding/enlargement checks
passed. The [audit](msk-verification-hamstring-figures-2026-09-27.json) preserves
5,202 requirements: 0 verified, 158 unverified, 5,044 missing. No clinical approval
was added. See [integration evidence](msk-hamstring-model-review.md).

## Intramuscular hamstring tendon MRI acquired

A new CC BY 4.0 Weber et al. 2026 Figure 3 was acquired, visually inspected and
preserved byte-for-byte with independent Poppler agreement. It shows a local
intact long-head biceps femoris intramuscular tendon alongside muscle injury.
[Source evidence](msk-hamstring-mri-source-review.md) limits the candidate to
partial anatomy and retains pathological context. It remains offline pending
integration; no clinical approval or requirement change was made. A separate
2026 NC-licensed chapter was excluded from commercial image reuse.

## Authored/shared gallery support

Explicit append-mode support now allows the pending directly authored hamstring
MRI reference to coexist with its reviewed shared figures. Implicit overwrite,
unknown mode, self-append and duplicate identities are rejected; cross-topic
scope fingerprints bind merge mode. 28 focused tests passed. This catalogue
support does not promote the pending figure or assert anatomical coverage.
See [behavior and verification](msk-authored-and-shared-galleries.md).


## Intramuscular tendon MRI integrated

Weber Figure 3 now accompanies the hamstring module's shared MRI and schematic.
It supplies one partial intramuscular-tendon candidate with explicit adjacent
injury, not a normal whole examination. 174 distinct tests and desktop/mobile
checks passed. The [source evidence](msk-hamstring-mri-source-review.md) and
[audit](msk-verification-intramuscular-tendon-2026-09-27.json) retain the full
5,202-requirement scope: 0 verified, 159 unverified and 5,043 missing. The base
catalog has 77 figures and the ledger 702 assets; no clinical approval added.

## Complete review queue exported

The [review queue](msk-review-queue/README.md) exposes all 5,202 representation
requirements across 22 investigations, including conditions, modalities,
reporting obligations, candidate files/source links, exact artifact and scope
fingerprints, partial-coverage claims and blockers. It is an evidence handoff,
not approval. Five tests verify full scope/candidate inclusion and rejection of
missing rows, duplicate rows, stale claims and inconsistent counts. The export
does not change evidence, requirements or readiness. Regenerate using
`tools/build_msk_review_queue.py --audit AUDIT.json --output docs/msk-review-queue`
after producing a current full fidelity audit.


## Review handoff verifies actual candidate files

The review-queue exporter now hashes the actual bytes of all 68 distinct
bound candidate artifacts before writing output. Changed, missing or
out-of-project artifacts stop export even when ledger metadata and scope
fingerprints are unchanged. The queue index preserves those observed hashes.
Seven tests passed, including changed-byte, missing-file and path-boundary
counterexamples. All 5,202 requirement rows remain present; no approval or
clinical readiness status changed.

## Native nerve divisions exposed

The hamstring viewer now includes separate sciatic, tibial and common fibular
nerve objects in their original coordinates. The thigh crop is explicitly
labelled and Full structures exposes the longer tibial object. No connecting
geometry was invented. 32 tests plus desktop/mobile isolation/reset checks
passed. [Evidence](msk-hamstring-model-review.md) retains unverified branching
and fascicular limits; no clinical approvals or coverage waivers were added.

## Semimembranosus MRI sequence preserved

Weber Figure 7 was visually inspected and preserved at native resolution with
an independent encoded-byte match. Its six panels retain separate initial
injury, re-injury and scarred-healing states; none is relabelled normal.
[Evidence](msk-hamstring-mri-source-review.md) records a partial intramuscular
semimembranosus tendon candidate pending integration, without new approvals.


## Semimembranosus MRI sequence integrated

Weber Figure 7 supplies one partial intramuscular-tendon candidate with explicit
initial injury, re-injury and scarred-healing panel states. Native JPEG bytes
and source credit are retained. 183 focused tests and desktop/mobile checks
passed. The [current audit](msk-verification-semimembranosus-2026-09-27.json)
retains 5,202 requirements: 0 verified, 160 unverified and 5,042 missing. The base
catalog has 78 figures and the ledger 703 assets. No clinical approval added.

## Arthritis regional references expanded

The inherited hand-only view now offers wrist/hand, whole foot, knee and hip
source references. The UI retains explicit right-sided, distribution and missing
site limits; no scope blocker was waived. 179 focused tests plus desktop/mobile
checks passed. [Evidence](msk-arthritis-model-review.md) and the
[current audit](msk-verification-arthritis-regions-2026-09-27.json) retain the full
objective and readiness false.

## Rights evidence included in review handoff

Each candidate in the review queue now carries the exact licence name/version
and URL, recorded commercial-use/redistribution flags, review status, attribution,
rights-evidence path, any declared licence-use plan and presentation dependencies.
These are reported evidence fields, not new legal or clinical approvals. Eight
queue tests passed, including preservation of CC BY 2.0, CC BY 4.0 and CC BY-ND
4.0 distinctions and attribution for every bound candidate. All 5,202 requirement
rows remain included; readiness and requirements are unchanged.

## Atlantoaxial source objects located

The acquired skeletal FBX contains native C1, C2 and occipital meshes. A direct
binary-node check corroborated identities, vertex counts and valid selected
indices after the whole-file inventory rejected another mesh. Cached transforms
remain unverified by this pass; named stabilising ligament matches were not
found. [Source evidence](msk-atlantoaxial-source-review.md) defines the next
export/inspection work without runtime promotion or clinical approval.

## Craniovertebral source geometry exported offline

C1, C2 and occipital source meshes were freshly exported with all 12,059
triangles. Independent source-vertex decoding corroborates export positions
within float32 rounding, using the freshly evaluated transforms. The
[three-view audit](msk-atlantoaxial-source-review.md) documents coarse tessellation
and missing cartilage/ligament coverage. No clinical registration or fidelity
approval, runtime promotion or structure binding was inferred.

## Craniovertebral topology audit

C1/C2 exports pass basic connected/closed/winding checks, while the occipital
source has 40 boundary and 39 non-manifold edges. Its volume claim is withheld
and no geometry repair or clinical approval was performed. Four known-geometry
tests passed. [Evidence](msk-atlantoaxial-source-review.md) records this concrete
limitation before any runtime promotion.

## Occipital defects traced to source

Direct original-polygon edge counting matches every exported abnormal edge,
including world endpoints and incidence: 40 boundaries and 39 non-manifold
edges. These are inherited source topology, not export-introduced defects.
[Evidence and location plot](msk-atlantoaxial-source-review.md) guide further
source review without automatic repair or a closed-volume/clinical claim.

## Atlantoaxial placeholder groups excluded

Direct source hierarchy traversal established that both named atlantoaxial
joint groups are empty Null nodes with no descendant geometry. They cannot
satisfy anatomy requirements. Generic spinal ligaments remain separately named
and uncredited for the missing upper-cervical stabilisers. The
[hierarchy audit](msk-atlantoaxial-source-review.md) moves further acquisition
away from these placeholders without changing scope or clinical approvals.

## Craniocervical MRI source acquired

A CC BY 4.0 normal coronal MRI figure labels the transverse and alar ligaments.
It was inspected and preserved as unchanged native JPEG with independent byte
agreement. [Evidence](msk-craniocervical-mri-review.md) excludes the separately
copyrighted neighbouring illustration and limits the single image's coverage.
It remains offline pending site-specific scope; no 3D or clinical approval was
inferred from the source's 3D MRI acquisition label.


## Draft cervical ligament scope expanded

Nine explicit alar/transverse-ligament course and attachment leaves add 27
representation requirements, preserving every pre-existing site and blocker.
The entries remain draft and MRI-conditional; the cervical inventory is not
declared complete. 155 focused tests passed. The
[current audit](msk-verification-cervical-scope-2026-09-27.json) and full review
queue now contain 5,229 requirements: 0 verified, 160 unverified and 5,069
missing. [Source and scope evidence](msk-craniocervical-mri-review.md).


## Cervical ligament MRI integrated

The unchanged Offiah Figure 4 is visible in the arthritis module with one
partial transverse-ligament course binding. Alar labels remain context only;
side-specific alar/attachment and complete-course claims are not inferred.
182 distinct tests and browser checks passed. The
[current audit](msk-verification-cervical-mri-2026-09-27.json) retains 5,229
requirements: 0 verified, 161 unverified and 5,068 missing. The base catalog now
has 79 figures and the ledger 704 assets. Clinical readiness remains false.

## C1/C2 package prepared for review

Two checked native bone exports are packaged offline with all 4,528 triangles,
source identity/transform checks and preserved attribution. The defective
occipital source is excluded without removing any anatomical requirement.
Six tests passed. [Package evidence](msk-atlantoaxial-source-review.md) retains
missing stabilisers and clinical accuracy as unresolved; no runtime promotion
or approval was made.

## Limited C1/C2 viewer available

The arthritis region selector now offers the checked two-bone C1/C2 source
package with its own manifest, unchanged geometry and explicit missing-tissue
limits. It adds no structure-completeness or clinical approval. The ledger now
contains 706 assets. 190 tests plus desktop/mobile controls checks passed.
[Evidence](msk-atlantoaxial-source-review.md) and the
[current audit](msk-verification-cervical-bones-2026-09-27.json) retain all 5,229
requirements and readiness false. The complete objective remains outstanding.

## External decisions made concrete

A [decision brief](msk-external-decisions.md) separates anatomical acquisition,
commercial rights and independent clinical review. It retains all 5,229
requirements and the 221-reference rights accounting. Authorization and sender
details for the concrete CCJ model inquiry were requested; no email has been
sent. Rights clearance will not be treated as clinical validation.

## Alternative cervical FE sources screened

An independent source pass found a mixed spring/solid biomechanical model, not
a downloadable high-fidelity ligament dataset. Primary methods distinguish
spring ligaments from the parameter-derived transverse-ligament solid; no mesh
package was identified in the inspected article. The
[screening record](msk-cervical-model-source-screen.md) also documents blocked
Physiome access and excludes wrong-region repositories. No models, approvals or
clinical recommendations were imported. The separate rights question remains
unanswered; external contact has not occurred.

## Muscle-module 3D mismatch corrected

Muscle-injury and muscle-disease investigations now expose six available source
muscle groups instead of the inherited generic long-bone scene. Initial and
reset states show muscle objects without regional clipping. 185 tests and
six-region/disease-route/mobile checks passed. [Evidence](msk-muscle-region-review.md)
retains all unscoped muscles, bilateral and internal-tissue requirements; no
clinical approval or completeness binding was added. The
[current audit](msk-verification-muscle-regions-2026-09-27.json) remains false.

## Thoracolumbar source levels audited

All seventeen native T1–L5 objects were exported and checked individually.
Sixteen pass basic topology checks; T8 has two boundary and 117 non-manifold
edges. The complete assembly remains offline rather than omitting or replacing
the defective level. [Evidence](msk-thoracolumbar-source-review.md) preserves
source identities and all original geometry without new clinical approvals.

## T8 source topology confirmed

T8's two boundary and 117 non-manifold edges exist in original polygon
connectivity at native precision. Exact export-endpoint/incidence agreement
excludes export triangulation or float32 rounding as their origin. Six checker
tests passed. [Evidence](msk-thoracolumbar-source-review.md) keeps the assembly
held without automatic repair, substituted anatomy or clinical approval.

## Independent T8 source candidate acquired

An official BodyParts3D 4.0 T8 OBJ was acquired with matched ZIP member/CRC and
preserved original bytes. Its 2,424 triangles pass basic topology checks, unlike
the current Z-Anatomy T8 source. The publisher labels the archive 99%-reduced;
clinical fidelity and registration are not inferred. [Evidence](msk-bodyparts-t8-review.md)
keeps the candidate offline and separate rather than mixing source anatomy.

## Alternative T8 fidelity limits recorded

The official archive and historical construction description do not establish
version-specific fine-anatomy accuracy for the reduced BodyParts3D T8 candidate.
Its clean topology is not promoted to a clinical-fidelity conclusion. The
[fidelity screen](msk-bodyparts-t8-review.md) retains the need for reconstruction
provenance, registered source anatomy and independent review before substitution
or wider clinical adoption. No runtime change or approval was made.

## Paired CT source candidate identified

VerSe's author-linked, CC BY-SA 4.0 complete-data archive was indexed using
bounded ranges; three metadata pairs were inspected without downloading the
11.5-GB cohort. A C7–L5 labelled case is selected for NIfTI/CT/mask verification,
not declared normal or clinically approved. The [source record](msk-verse-source-review.md)
pins repository guidance and distinguishes the data licence from the MIT code
licence. No runtime data or structure binding has been added.

## Paired vertebral CT/mask acquired

The selected VerSe case was downloaded with verified archive/member checksums.
CT/mask grids and selected affines match; centroids align with corresponding
labels. C7 touches the volume boundary, whereas T1–L5 do not. Stored spacing
and acquisition thickness are recorded separately. [Evidence](msk-verse-source-review.md)
retains segmentation/clinical uncertainty; no model, runtime data or approval
was generated from geometry agreement alone.

## T8 paired-image review generated

The acquired CT was fully decoded and inspected with its original T8 mask on
nine native planes. A plotting-origin offset was corrected and affine-derived
orientation labels added. [Evidence](msk-verse-source-review.md) records exact
planes, source hashes and limits. Gross correspondence does not approve fine
anatomy; no mesh, clinical approval or runtime promotion was inferred.

## Image-backed T8 surface derived offline

The original VerSe T8 label now has an unsmoothed, unfiltered 38,516-triangle
surface in CT world coordinates. Isovalue correspondence, coordinate round trips
and basic topology checks pass; visible voxel stepping and annotation uncertainty
remain explicit. [Evidence](msk-verse-source-review.md) anchors world units to the
CT because the mask's unit flag is unknown. No clinical approval or runtime
substitution was inferred from this derivation.

## Complete source-label surface set derived

The paired VerSe case now supplies an offline T1–L5 surface set of 798,442
triangles with all source-labelled components retained. A helper-vertex
approximation was investigated against the pinned implementation and is reported
rather than concealed; T12's additional small surface component remains for
review. [Evidence](msk-verse-source-review.md) preserves source provenance and
clinical uncertainty. No other atlas was mixed in and no approval was added.
