# Shoulder soft-tissue source acquisition — 26 September 2026

**Acquired and inspected:** FDA/OSEL-DAM's CC0 shoulder finite-element model,
including native labrum, AC ligament, humeral cartilage and glenoid cartilage
volumes with the matching bones. This is a useful new source candidate; it is
not a completed rotator-cuff/pulley atlas or an approved clinical reference.
No production geometry, manifest or clinical evidence record was changed.

## Primary source and rights

The [FDA tool catalogue](https://cdrh-rst.fda.gov/human-shoulder-finite-element-model)
links directly to the [official author repository](https://github.com/OSEL-DAM/ShoulderFiniteElementModel).
The downloaded `LICENSE` and author DOCX README explicitly apply **CC0 1.0**,
including commercial purposes in the legal text. The [publication abstract](https://link.springer.com/article/10.1007/s10439-022-03018-8)
independently identifies this release. The subscription-only article body was
not retrieved or bypassed; the public author README provides the methods below.

Pinned revision: `fc9f3e56b104c06759750495be1f8dd5d53c1741`.
`Male-Shoulder.inp` is 59,793,091 bytes; SHA-256:
`547de9cff23a4ae98d5a297ba32d8b01fe042739160c4b7144dfe7066d08c70a`.
All acquired files were checked against their upstream Git blob SHA-1 as well
as recorded SHA-256. The license, two READMEs, repository metadata, original
input deck and acquisition record are preserved locally.

Credit retained for any eventual adaptation:
U.S. Food and Drug Administration (2023), *Human Shoulder Finite Element Model*,
RST24OP04.01; Sadeqi et al., DOI `10.1007/s10439-022-03018-8`.
The FDA catalogue does not establish approval for this project's use.

## What the authors actually released

The public author README describes manual CT segmentation of the Visible Human
male shoulder's bones, labrum and AC ligament. Cartilage was constructed by
offsetting mesh layers to literature-based thicknesses, not directly segmented.
Muscle-tendon loading uses connectors. These distinctions remain attached to
the candidate rather than treating all parts as equivalent image segmentations.

The native deck contains seven `C3D10M` volume parts and 19 `CONN3D2`
connectors. The README uses the broader `C3D10` name. The extracted surfaces
below follow the actual deck connectivity:

| Source part | Volume elements | Quadratic boundary faces | Preview triangles |
| --- | ---: | ---: | ---: |
| `Labrum` | 124,307 | 13,238 | 52,952 |
| `AC_Lig` | 2,111 | 398 | 1,592 |
| `Gcart` | 36,551 | 7,978 | 31,912 |
| `Hcart` | 73,736 | 22,342 | 89,368 |
| `CLAVICLE` | 16,511 | 8,246 | 32,984 |
| `Humerus` | 39,827 | 15,298 | 61,192 |
| `SCAPULA` | 55,349 | 29,162 | 116,648 |

The bone and soft-tissue volumes share a native assembly. Humerus and humeral
cartilage have matching explicit translation/rotation definitions; the other
five part instances have identity placement. The extractor preserves original
local coordinates and node IDs, and records/applies these exact source instance
transforms. Translation precedes rotation according to the
[Abaqus INSTANCE specification](https://docs.software.vt.edu/abaqusv2025/English/SIMACAEKEYRefMap/simakey-r-instance.htm).
No registration to Z-Anatomy, BodyParts3D or clinical images was estimated.
The inspected state is the initial undeformed assembly, before prescribed
simulation displacements.

Each external six-node quadratic face is retained, with a four-triangle preview
using its native corner/midside points. This approximates curved FE faces for
inspection; it does not invent tissue or claim exact continuous interpolation.
All positions are finite and transforms invert to their source coordinates.
No exactly zero-area preview faces or boundary edges were detected. Glenoid
cartilage has two nonmanifold edges; those are retained without repair. The
other six boundary surfaces have none under the same check.

The four-view native-assembly preview was inspected. It shows a volumetric
labral rim around the glenoid cartilage and a separate AC ligament between its
bone context. The two cartilage surfaces are distinct solids. The display crops
do not modify the staged geometry. Appearance and facet density are not proof
of tissue-boundary accuracy.

## Fidelity limits and disposition

The [FDA's stated validation](https://cdrh-rst.fda.gov/human-shoulder-finite-element-model)
covers one abduction scenario and literature comparators; it does not validate
this dataset as a clinical anatomical atlas. Single-subject geometry, prescribed
motion and connector musculature are explicit limits. No source CT voxel grid
or segmentation masks were supplied in the acquired deck/README. Units are not
encoded in Abaqus; millimetre/MPa consistency is inferred from the README and
native boundary/material values. Anatomical axis directions are not certified.

An additional provenance question remains: the actual labrum cell set is named
`LABRUM-THICKER_GEOM_VOLUME1`. The public README does not explain whether or how
labral thickness was changed. This is recorded as unresolved rather than
assuming unmodified segmentation or inferring a correction from the name.
The cartilage offset method is documented and is not rejected merely because
it is algorithmic, but source-specific cartilage shape accuracy is unproven.

**Recommendation:** retain all seven parts as a coordinated research candidate
for labrum/AC-ligament and explicitly modelled cartilage review. Do not promote
it automatically because it is denser than the current atlas or because FDA
hosts it. It contains no volumetric cuff tendons or insertion footprints, biceps
pulley, biceps tendon, capsule, capsular subdivisions or separately labelled
labral quadrants/attachments. It therefore cannot close those reportable gaps.

The prior [rotator-cuff reconstruction study](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0274075)
remains a described reconstruction without an acquired openly licensed tendon
dataset; it was not retried. No restricted download was retried and no authors
were contacted in this pass.

## Staging and reproduction

Everything remains under:
`/tmp/primer-msk-sources/shoulder-next/fda-shoulder/`.

New source-only tools:

- `tools/anatomy_sources/acquire_fda_shoulder.py`
- `tools/anatomy_sources/inspect_fda_shoulder.py`
- `tools/anatomy_sources/render_fda_shoulder.py`

The inspector uses the existing native quadratic-boundary helper from
`inspect_leeds_ankle.py`. Run inspection/rendering with Python 3.12 and the
staged NumPy/Matplotlib dependencies (`PYTHONPATH=/tmp/primer-msk-sources/python`).
Review artifacts are `acquisition.json`, `mesh-inspection.json`, seven boundary
NPZs and `native-shoulder-review.png`. No simulation code or Abaqus journal was
executed. No runtime promotion or anatomical approval has occurred.
