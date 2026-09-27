# Ankle fine-structure source acquisition, 2026-09-26

**Result:** a new openly licensed, MRI-derived tibiotalar cartilage candidate
was acquired and inspected. It is a pathological research model, not a normal
ankle replacement or proof of high-fidelity fine-structure coverage. No runtime
manifest, evidence approval or production mesh was changed. Ankle/foot ligament
volumes remain unresolved.

## Acquired: Leeds ankle finite-element source

The [University of Leeds repository](https://archive.researchdata.leeds.ac.uk/1016/)
provides 42 Abaqus input decks under **CC BY 4.0**: 18 cyst-containing models,
18 cyst-ignored comparators and six depth variants. Repository, downloaded
README and DataCite metadata agree on the license. The README explicitly
reports permission to share anonymised derived data. Commercial redistribution
and adaptation require attribution, a license link and change disclosure;
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) does not permit implied
author endorsement.

The official 353,479,143-byte ZIP downloaded normally with HTTP 200. Its MD5
matches the official `Content-MD5`/ETag:
`a4f366536171f223eb708bb7d5208a41`. SHA-256:
`f477e686b196b86467621cba0a42089ee7df6bc484d7059491a574c3f6f1f70d`.

Staging directory:
`/tmp/primer-msk-sources/ankle-next/leeds-1207/`.
It contains the unchanged archive, publication, repository/license metadata,
two native input decks, extracted quadratic boundaries, numerical inspection
report and a rendered comparison. Nothing has been published to `web/`.

### Actual geometry inspection

The inspected native pair is `Ankle1_1_intact.inp` and
`Ankle1_1_cysts.inp`. Both contain one `PART-1` instance with **no assembly
transform**. All tissue sets therefore share their deck's original coordinates.
The parser verifies finite positions, exhaustive disjoint tissue cell sets,
ten-node `C3D10H` elements and matching six-node internal faces. Boundary
surfaces are derived from actual cell connectivity, not inferred from names.

| Native tissue set | Cyst-ignored volume cells | Quadratic boundary faces | Preview triangles |
| --- | ---: | ---: | ---: |
| `PT_CARTILAGE_1` | 30,166 | 12,580 | 50,320 |
| `PT_CARTILAGE_2` | 37,941 | 16,320 | 65,280 |
| `PT_TALUS` | 61,178 | 15,324 | 61,296 |
| `PT_TIBIA` | 54,531 | 13,970 | 55,880 |

The source contact/interface sets associate cartilage 1 with tibia and cartilage
2 with talus. These are separate volumetric tissues with curved, irregular
boundaries in the joint space; they are not flat labels or inflated bone shells.
The rendered pair was visually inspected in two views. The cyst-containing
variant also contains a distinct `PT_CYSTS` volume. Its tibial preview retains
38 nonmanifold edges; none were repaired or removed. All inspected surfaces
have zero boundary edges and no exactly zero-area preview triangles. The
cyst-ignored pair has no nonmanifold edges.

For inspection, each native quadratic face is retained in NPZ and also split
into four planar preview triangles using its exact corner and midside node
coordinates. This is an approximation of the quadratic face, not a claim of
continuous FE-surface equivalence. Source node and volume-element IDs are
retained. No smoothing, decimation, small-component removal or cross-atlas
registration was performed.

No anatomical axis labels or laterality are certified. The decks do not declare
a unit system. Millimetres are consistent with the publication's dimensions and
MPa material data, but remain an explicit inference pending source confirmation.
No acquired MRI/segmentation pair is included in this release.

### Fidelity disposition

The [primary publication, methods and discussion](https://eprints.whiterose.ac.uk/id/eprint/190744/1/TalbotEtAl_2022_ClinicalBiomechanics.pdf)
describes manual MRI segmentation and approximately **3 mm sagittal slice
thickness**. Its haemophilic specimens and lack of experimental validation
limit interpretation. Ligaments and other soft-tissue constraints are omitted.
“Intact” means the cyst was ignored in segmentation; it does **not** mean a
healthy control. Mesh convergence checks simulation sensitivity, not anatomical
accuracy. The README says five ankles, while its specimen table and publication
describe four; this discrepancy is retained.

**Recommendation:** keep this as a reviewable pathological cartilage/cyst
candidate. It adds genuine tissue volumes absent from the Malaya ankle source,
but sampling and population limits prevent promotion as a high-fidelity normal
cartilage atlas. Triangle counts do not remove those limits. There is no ATFL,
CFL, PTFL, deltoid, syndesmotic, spring, Lisfranc or plantar-ligament geometry.

## Denver and other legitimate acquisition routes

| Primary route | Verified finding | Disposition |
| --- | --- | --- |
| [Denver Visible Human Female, DOI 10.56902/COB.vh.2022.1](https://digitalcommons.du.edu/visiblehuman/1/) | Explicit CC BY 4.0; tibiotalar cartilage, native masks and final/smoothed STL packages. Only knee ligaments are listed. | Best normal-reference cartilage lead; prior official supplemental download 403 remains unresolved. No restricted URL retried or bypassed. |
| [Author-linked FEMORS](https://github.com/thor-andreassen/femors) | Processing code and link back to Denver; repository tree contains no ankle mesh release. | No official geometry mirror found. Request restored dataset access or an author-provided public mirror. |
| [Bath Open Ankle project](https://www.bath.ac.uk/projects/open-ankle-models-project/) | Official page still says model data/guides are forthcoming and gives `e.c.pegg@bath.ac.uk` for access enquiries. | Concrete author-access route; no public file/license grant found. No contact made. |
| [Muralidharan anklejoint source](https://github.com/laxmimurali/anklejoint) | Actual OpenFOAM mesh files; README describes uniformly extruded cartilage. Repository has no explicit license file/grant. | Not commercially cleared; algorithmic generation alone is not rejection, but fine morphology and reuse terms are unproven. Geometry was not imported. |
| [Lateral ankle ligament mechanical data, DOI 10.17632/87tng69ch6.1](https://data.mendeley.com/datasets/87tng69ch6/1) | CC BY 4.0 force/displacement and anthropometry tables. | Useful biomechanical data, no volumetric ligament mesh. |

Denver's documented smoothing targets are 0.75 mm edges for cartilage and
ligaments, and final processing imposes a 0.05 mm inter-geometry gap. These are
processing parameters rather than measurement accuracy. A future authorised
download should compare final surfaces with native segmentation masks and
document the ankle cartilage before any replacement. It cannot solve the
unlisted ankle ligament gap.

The next useful acquisition request is therefore specific: Denver's ankle
cartilage/bone subsets plus native masks and coordinate metadata; and Bath's
current ankle geometry, explicit commercial redistribution terms, and whether
ligaments are attachment paths/springs or separately reviewed volumes. Neither
request has been sent. A generic “open-source model” claim is insufficient.

## Reproduction

The new scripts under `tools/anatomy_sources/` are:

- `acquire_leeds_ankle.py`: bounded official downloads and source checksums.
- `inspect_leeds_ankle.py`: native element/part inspection and boundary export.
- `render_leeds_ankle.py`: native-coordinate scientific preview.

Run the latter two with Python 3.12 and the previously staged NumPy/Matplotlib
dependencies (`PYTHONPATH=/tmp/primer-msk-sources/python`). They write only under
the staging directory. The source acquisition report is `acquisition.json`,
geometry report `mesh-inspection.json`, and reviewed preview
`native-cartilage-review.png`.
