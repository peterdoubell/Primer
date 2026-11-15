# Atlantoaxial source inventory

27 September 2026. The published limb atlas contains no C1/C2 objects. The
already acquired Z-Anatomy skeletal FBX does contain named Atlas (C1), Axis
(C2), and Occipital bone objects, with 2,194, 2,334 and 7,531 triangles
respectively. These are source meshes, not labels or origin markers.

[Inventory evidence](msk-atlantoaxial-source-review/inventory.json) fingerprints
the source files and records source model/geometry IDs and cached transforms.
Direct binary-node inspection independently confirmed the three model names,
geometry vertex counts, index ranges and triangulated polygon counts. The
whole-file inspector rejected another empty/invalid mesh, so no successful
whole-file audit is claimed. Cached world transforms still need independent
export verification before combining geometry.

No exact named matches for alar ligaments, transverse ligament of atlas,
tectorial membrane or cruciform ligament were found in the acquired joint
inventory. This does not prove absence under alternate or grouped names.
Those structures require further source inspection. Whole-bone names cannot
establish separate dens, facet, cartilage or ligament coverage.

This is an offline acquisition decision, not a clinical review. No geometry
was exported to the app, no structures were declared complete, and no arthritis
scope requirement was removed. Next: independently export and inspect the
three native bone objects and audit stabilising structures before offering an
explicitly limited cervical reference.

## Fresh source export and position checks

The three selected objects have now been exported offline with the existing
ufbx exporter. Fresh transform matrices and bounds match the prior cache.
Independently decoded FBX vertices, transformed with those fresh matrices,
match the binary exports in both directions within 0.000008 cm (float32
rounding). All 12,059 source triangles are retained. These comparisons verify
preservation, not anatomical accuracy or independently derived registration.

[Export audit](msk-atlantoaxial-source-review/export-audit.json) records source,
exporter and binary hashes, geometry IDs, unused-source-vertex counts and maximum
position differences. `tools/anatomy_sources/audit_atlantoaxial_exports.py`
reproduces the audit. `tools/anatomy_sources/render_atlantoaxial_review.py`
produces the [three-view inspection image](msk-atlantoaxial-source-review/native-geometry-review.png).
The picture uses original triangles, orthographic views and display colours;
it is an offline derived review artifact, not a clinical anatomical figure.

Visible tessellation remains coarse for fine articular assessment. No cartilage,
ligament, pannus, erosion or instability representation is inferred. Independent
transform-hierarchy evaluation, topology/relationship inspection and clinical
assessment remain outstanding. No runtime promotion or requirement binding was
made. Binary exports remain under `/tmp/primer-msk-sources/atlantoaxial-staged`.

Attribution: BodyParts3D, The Database Center for Life Science (source lineage),
and Z-Anatomy contributors. The adapted source meshes and this derived review
render are CC BY-SA 4.0. See the existing project source-rights review in
`msk-mesh-source-audit.md`; the reviewed Z-Anatomy source revision is
`6c7f9016bd5899ac8edafd31b9900c151df42ed6`. No geometry alignment or repair was
performed; normals use the established exporter behavior.

## Topology findings

A non-repairing topology audit now records exact-position seam welding for
measurement only. C1 and C2 each form one connected component with zero boundary,
non-manifold, inconsistent-winding or degenerate edges/faces under these checks.
This is not proof of anatomical accuracy or absence of self-intersections.

The occipital mesh has 40 boundary edges and 39 non-manifold edges. Its volume
is intentionally not reported. It remains unsuitable for a closed-bone/volume
claim without further source diagnosis; no automatic closing or smoothing was
performed. A source modelling artifact must not be interpreted as a clinical
bone defect. The existing offline drawing is source inspection, not approval.

[Topology evidence](msk-atlantoaxial-source-review/topology.json) binds findings
to each exported file hash. The checker reproduces known closed, open,
non-manifold and reversed-face cases in four passing tests. Runtime assets,
anatomy requirements and clinical approvals remain unchanged.

## Source versus export defect comparison

The original occipital FBX has 7,455 triangular and 38 quadrilateral polygons.
Direct source-polygon edge counting reproduces all 40 boundary and 39
non-manifold edges. Every abnormal edge matches the export's world-space
endpoints and incident-face count exactly after float32 encoding. Thus these
incidences are inherited source topology, not defects introduced by the exporter.

[Comparison evidence](msk-atlantoaxial-source-review/occipital-source-topology.json)
includes the source/export hashes and coordinates of all 79 affected edges.
`compare_occipital_source_topology.py` reproduces the comparison without repairing
or triangulating the source for its edge count. The
[location plot](msk-atlantoaxial-source-review/occipital-defect-locations.png)
projects these edges over the original meshes. Depth occlusion is deliberately
ignored for the coloured overlays and disclosed in the title; the plot does not
claim the marked edges are all on the visible outer surface. Geometry is unchanged.

The affected region needs source/reference investigation. No automatic hole
filling, joining, deletion of faces or closed-volume claim is justified by this
comparison. Anatomical accuracy, self-intersections and stabilising soft tissues
remain unresolved. No runtime promotion or clinical approval was made.

## Atlantoaxial group hierarchy checked

The original joint FBX includes `Median atlanto-axial joint.g` and
`Lateral atlanto-axial joint.g` as Null nodes. A direct traversal of object-to-
object connections found no descendant models and no attached geometry for
either group. These are empty organisational labels, not joint-surface meshes.
[Hierarchy evidence](msk-atlantoaxial-source-review/hierarchy.json) records the
source hash, model IDs and empty descendant/geometry lists.

The source does contain broad anterior/posterior longitudinal, nuchal,
interspinous and ligamenta-flava objects. Their bounds are recorded separately;
they are not relabelled as alar ligaments, transverse ligament of the atlas or
tectorial membrane. The broad posterior-longitudinal object ends below the
atlas source's inferior bound, reinforcing that its name must not be used as
proof of the superior continuation. This geometric observation does not resolve
fine anatomy in other grouped objects or establish absence in other datasets.

The acquired joint hierarchy therefore does not supply a hidden mesh behind
the named atlantoaxial groups. A different appropriately licensed anatomical
source is needed for those stabilising structures. No runtime object, ligament
binding or clinical approval was created from these labels.

## Offline C1/C2 reference package

A reproducible package now preserves only the checked C1 and C2 exports under
`output/msk-cervical-bones/`. Its manifest retains source IDs, transforms,
original source hash, binary hashes, actual binary bounds, units and CC BY-SA
4.0 attribution. Source identity, transform consistency, topology evidence and
binary checks must pass before packaging. The occipital mesh is explicitly
excluded; no ligament, cartilage or instability representation is substituted.

[Package manifest](../output/msk-cervical-bones/manifest.json) ·
[Attribution](../output/msk-cervical-bones/ATTRIBUTION.md).
`tools/anatomy_sources/package_cervical_bones.py` rebuilds the package from
acquisition staging. Six package/topology tests passed, including exact
repackaging agreement. All 4,528 C1/C2 triangles remain unchanged. This is an
offline review artifact, not a published viewer or clinically approved model.

## Limited bone reference exposed in arthritis

The checked package is now available as the optional “C1/C2 bones · limited”
regional reference in the arthritis module. A separate runtime manifest keeps
these two objects distinct from the limb atlas. It preserves all 4,528 triangles,
source bytes, coordinates and attribution. The occipital source remains excluded;
no stabilising tissues or clinical stability simulation are supplied.

The source records are inventoried in the evidence ledger without structure-
completeness bindings or clinical approval. Existing pending presentation hashes
were refreshed for the changed viewer/configuration; no approved review was
carried forward. Generic BodyParts3D organ text no longer overrides the cervical
manifest's source notes, and the regional summary distinguishes midline bones
from right-sided limb references.

190 relevant tests passed. Browser checks confirmed the cervical atlas selection,
two actual rendered meshes, 4,528 triangles, rotation/reset, isolation, mobile
layout without overflow, one viewer at a time and no console errors. The source
notes explicitly retain missing occipital, ligament, cartilage and fine-joint
anatomy. [Browser proof](msk-atlantoaxial-source-review/browser-c1c2.png).
Temporary server/tab were closed and viewport reset.

The [current audit](msk-verification-cervical-bones-2026-09-27.json) and review
queue retain all 5,229 requirements and clinical/commercial readiness false.
The limited reference is not a substitute for the complete requested anatomy.

## Independent CCJ model lead: separate rights required

Vigo et al.'s *Immersive Surgical Anatomy of the Craniocervical Junction*
(DOI 10.7759/cureus.10364) links to an external UCSF model collection. The
search-indexed primary listing for Model 4: Ligaments states a noncommercial
licence and credits Anatomography reference meshes under CC BY-SA 2.1 Japan.
The article's CC BY grant is not treated as a model-specific commercial grant.
Direct collection/model-page access returned 403; no hidden assets or downloads
were attempted. Geometry and component coverage have not been inspected.

[Decision record](msk-ccj-external-source-review/source-decision.json) and
[unsent rights inquiry](msk-ccj-commercial-rights-draft.md) preserve the concrete
next external step. The draft asks about commercial distribution, modifications,
textures, component inventories and upstream obligations. It has not been sent
and does not authorise external contact. No model or licence was added to runtime.
