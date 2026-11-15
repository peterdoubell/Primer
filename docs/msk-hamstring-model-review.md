# Hamstring model mismatch and source extent audit

27 September 2026. The current `ra.mri-hamstring` investigation inherits a
`longbone` spatial schematic. It does not supply named posterior-thigh anatomy.
The [22-investigation inventory](msk-hamstring-model-review/investigation-model-inventory.json)
records the effective runtime families, including the corrected injection module.
Broad arthritis, tumour, muscle-disease and stress-fracture modules still need
site-specific review; a single inherited family does not establish their scope.

The registered Z-Anatomy knee dataset contains four native right-sided muscle
objects: long and short heads of biceps femoris, semimembranosus and
semitendinosus. Their full meshes preserve proximal geometry beyond the knee
view. The current knee crop excludes 58.5%, 23.8%, 44.9% and 54.3% of their
exported vertices respectively. These are renderer vertices with duplicate
triangle corners, not percentages of anatomical tissue or volume.

The [binary audit](msk-hamstring-model-review/mesh-bounds.json) independently
reads all positions from the four BP3D files, verifies file hashes, finite
coordinates, binary lengths and exact agreement with manifest bounds. The
source has native shared centimetre coordinates and CC BY-SA 4.0 attribution.
No mesh was modified or independently declared anatomically accurate.

A replacement should frame the full union of the four native objects, select
the muscle layer initially, and preserve orientation, full-structure inspection,
source attribution and reset behavior. Simply changing the module to the default
knee model would still hide proximal muscle anatomy. A new view must be checked
against actual rendered geometry and tested to keep reset from restoring the
old knee crop. The short head is shown as a separate source muscle; it must not
be assigned a pelvic origin by grouping it with the other objects.

Material-defined tendon surface patches remain surface patches, not full tendon
volumes. Fine fascicles, aponeuroses, attachment footprints, sciatic relationships
and source-specific clinical fidelity remain unverified. No structure-level
coverage or clinical approval is inferred from this bounds audit. Existing requirements remain unchanged. The implementation below replaces
the runtime schematic without granting new clinical coverage.

## Implemented full-extent view

The hamstring investigation now selects a dedicated Z-Anatomy source view.
Only the four audited muscle objects load (21,492 source triangles); the
geometry and source coordinates are unchanged. Framing uses their union plus
a 5-mm margin: source superior-axis interval 34.646389–82.517700 cm. The view
starts with the muscle layer and a posterior camera. Reset restores both and
the full source envelope, rather than returning to the old knee crop. Individual
objects can be selected and isolated. No tendon material overlay is promoted
to a separate tendon volume.

28 Python tests passed, including the Node geometry/orientation suite. The
new checks require all four native objects, ensure the frame includes their
complete bounds, reject the wrong atlas and verify the investigation binding.
Browser checks confirmed 4 rendered meshes/21,492 triangles, initial and reset
muscle/posterior state, keyboard rotation, uncropped isolation, 390-pixel mobile
layout with no overflow, and no browser errors. Temporary test server/tab were
closed and viewport reset.

[Desktop proof](msk-hamstring-model-review/browser-desktop.png) ·
[Mobile proof](msk-hamstring-model-review/browser-mobile.png).
The [fidelity snapshot](msk-verification-hamstring-model-2026-09-27.json) retains
all 5,202 requirements and clinical/commercial readiness false. This fixes a
representation mismatch and clipping problem; it is not clinical certification.

## Structure evidence bindings

The four native objects are now recorded as partial model candidates for their
respective `muscle_belly` leaves in `ra.mri-hamstring`. The source IDs, geometry
IDs, mesh fingerprints, original manifest fingerprint and view selection are
retained in each binding. Full source extent does not imply full anatomical
coverage: these objects provide external muscle surface context without an
independently segmented muscle-belly/tendon boundary or internal architecture.

No tendon, junction, footprint, fascia or nerve leaf is bound. The separate
material-defined tendon patches remain unbound. Anatomical review remains
pending and fidelity remains unassessed; visual source checking is not a
clinical approval. Source acquisition setting and health state remain unknown.

149 focused tests passed, including checks that each mesh binds only its own
muscle-belly leaf, matches the audited binary, remains partial and cannot pass
as complete anatomy. The [current audit](msk-verification-hamstring-bindings-2026-09-27.json)
retains 5,202 requirements: 0 verified, 154 unverified and 5,048 missing. Only
candidate evidence changed; no viewer, geometry or requirement was altered.

## Registered pelvic and sciatic context added

The full-extent view now includes three optional context objects from the same
Z-Anatomy manifest: right hip bone, sacrotuberous ligament and sciatic nerve.
Their hashes and binary bounds were independently checked in
[context-meshes.json](msk-hamstring-model-review/context-meshes.json). No source
coordinate or transform changed. Together displays seven native objects and
30,832 triangles. Muscle-only remains the default layer; bone, ligament and
nerve layers can be selected independently.

The frame now encloses all seven objects with the same 5-mm margin, extending
the superior-axis interval to 34.646389–101.694023 cm. This supersedes the earlier
four-object framing interval. The hip bone supplies gross pelvic context,
not validated tendon footprints. The nerve object does not establish complete
distal divisions. The sacrum and fine attachment anatomy remain absent; adding
a ligament surface does not prove its attachment connections.

29 relevant tests passed. Browser checks confirmed all seven meshes rendered,
layer switching, sciatic isolation without cropping, reset, a 390-pixel layout
without overflow and no browser errors. [Combined desktop view](msk-hamstring-model-review/context-desktop.png)
and [mobile view](msk-hamstring-model-review/context-mobile.png) record the result.
No new evidence bindings or clinical approvals were added. The four muscle
bindings remain partial. Temporary test resources were closed.

## Matching MRI and schematic references shared

The hamstring module now reuses the preserved Balius Figure 2 schematic and
Boutin Figure 6.5 MRI comparison. Source IDs and all original asset bytes,
caption/provenance fields and licences are unchanged. The schematic adds four
partial muscle-belly candidates; the MRI is contextual and adds no inferred
hamstring tendon-substructure binding. Other Hip/FAI figures are not shared.

The [fixed scope review](msk-hamstring-shared-figures.md) is hash-bound to the
source, target and exact selected IDs. Changing the selection or review file
invalidates that sharing record. This allows reviewed anatomical overlap
across catalogue topic groups without permitting arbitrary regional reuse.

175 relevant tests passed. Browser checks confirmed the correct Diagram and
Images placement, native decoding (986 × 1258 schematic; 1863 × 860 MRI),
keyboard enlargement and no decorative image filter or console errors. The
[schematic preview](msk-hamstring-model-review/shared-schematic.png) records the
result. Temporary server/tab were closed. The
[current audit](msk-verification-hamstring-figures-2026-09-27.json) remains
incomplete across all 5,202 requirements: 0 verified, 158 unverified, 5,044 missing.

## Source identity guards

The hamstring preset now rejects mismatched regional laterality, renamed
anatomical objects, incorrect tissue layers and malformed or inverted bounds.
Both source regions must remain right-sided and all seven expected object
names/layers must match. This prevents an atlas metadata change from silently
retaining the right-sided hamstring presentation. Valid source geometry,
framing and appearance are unchanged. Thirty-two Python tests passed, including
the Node orientation suite with seven mutated-source rejection cases.

## Distal nerve source audit

The same registered atlas includes separate right tibial and common fibular
nerve objects. [Binary and proximity evidence](msk-hamstring-model-review/nerve-division-audit.json)
verifies all three nerve files against their manifest hashes and bounds. Their
superior-axis extents overlap the sciatic object's inferior extent, with nearest
exported-vertex distances of approximately 0.39 mm (tibial) and 1.51 mm (common
fibular). These are vertex distances, not surface gaps or proof of continuous
fascicles, exact branching anatomy or clinical accuracy. No joining or synthetic
bridging was performed.

The tibial object reaches the distal leg; including it in the current full-object
frame would expand the hamstring view substantially. A future nerve-context view
needs an explicit framing choice and inspection of the separate source objects,
not an automatically generated continuous trunk. Runtime geometry, bindings and
clinical approval remain unchanged by this source audit.

## Separate nerve divisions integrated

The hamstring view now loads nine source objects, adding the native tibial and
common fibular nerves as independently selectable nerve-layer entries. Their
coordinates, mesh bytes and separate endpoints remain unchanged. No synthetic
junction, smoothing or surface joining was introduced. The default camera
retains the seven-object thigh frame; its label is now “Thigh reference extent”
rather than claiming every nerve is shown in full. Full structures and isolation
expose uncropped native objects, including the longer tibial nerve.

32 relevant tests passed. Browser checks confirmed all nine objects available,
three correctly named nerve entries, full-source rendering, common-fibular
isolation, reset to muscle/posterior/thigh framing, mobile width without overflow
and no console errors. [Full nerve source view](msk-hamstring-model-review/nerve-divisions-desktop.png)
records the result. Temporary preview resources were closed.

No new clinical binding is inferred from displaying the separate objects.
Fascicular continuity, branching fidelity and site-specific diagnostic accuracy
remain unverified. All original reporting requirements remain in force.

## Presentation-dependent review fingerprints

The four muscle candidates now declare hashes for the anatomy viewer and
investigation model-binding configuration. The fidelity gate checks these files
in addition to mesh bytes; a changed viewer or missing configuration blocks
verification even if an old review still matches the unchanged mesh. The review
queue independently rechecks these dependencies before exporting. They also
participate in each asset's review-scope fingerprint. No clinical approvals were
added or retroactively preserved.

150 fidelity/hamstring tests and seven review-queue tests passed. A synthetic
fresh-review counterexample verifies that changing framing code while retaining
the same mesh cannot stay verified. The refreshed
[audit](msk-verification-presentation-2026-09-27.json) and review queue retain all
5,202 requirements with readiness false.
