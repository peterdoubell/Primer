# Independent Malaya ankle-source review

Review date: 2026-09-26. This audit concerns the separately staged ankle selection
from the already acquired [Universiti Malaya dataset](https://researchdata.um.edu.my/dataset.xhtml?persistentId=doi:10.22452/RD/5T6TZ7),
CC0 1.0. It did not modify source meshes, the current viewer or runtime packaging.

## Assessment

**The candidate improves the available gross Achilles reference shape and its
relation to the ankle bones.** It is an independently segmented source tendon,
with a continuous main surface from the lower-leg region to the posterior
calcaneal region in the same native coordinate frame as the bones. The actual
source geometry was visually inspected, rather than assessed solely by its
triangle count. This supports a separately labelled reference option; it does
not certify a complete or clinically validated ankle atlas.

There are no separately segmented ankle ligaments or ankle cartilage in this
selection. Muscle-unit files cannot be counted as separately delineated distal
tendons, sheaths, retinacula, or insertional substructures. Missing anatomy must
remain explicit. Z-Anatomy geometry must not be merged into this subject frame
by an undocumented fit.

## Exact geometry checks

Author archive: `/tmp/primer-msk-sources/high-fidelity/um-final-model-stl.zip`.
Its SHA-256 remains
`0c6c7fa81329dba949e00c7d99de37afef0352368eb5b386eb8034ec0b66ec86`.
The audited staged manifest is
`/tmp/primer-msk-sources/high-fidelity/malaya-ankle/manifest.json`.

The independent checker reads the **original ZIP member**, verifies that the
staged STL is identical, and reconstructs the expected retained source facets.
For all 20 objects, it confirms:

- Exact float32 equality of every retained triangle corner and source normal.
- Valid indices, finite geometry, correct referenced-vertex bounds and file hashes.
- Identity geometry transforms; native LPS coordinates in millimeters are retained.
- Every omission has an exactly zero cross product evaluated in float64 from
  source coordinates **and** a repeated vertex. No nonzero-area component is
  filtered by size, volume or appearance.
- Omission indices and their evidence hash match the manifest.

**Passed:** 663,532 source facets → 663,266 render facets, with 266 proven empty
facets omitted. The 20 main binaries occupy 55,710,528 bytes. This audit changes
no geometry. Its reproducible output is `independent-source-audit.json` in the
staging directory; that file records the manifest hash at the time of review.

The empty-facet omissions are: extensor digitorum longus 6, extensor hallucis
longus 6, flexor digitorum longus 82, tibialis anterior 98, tibialis posterior 38,
and Achilles 36. Other selected objects lose no facets.

## Achilles: actual shape and irregularity

The retained Achilles has two vertex-connected components:

| Component | Facets | Observed geometry |
| --- | ---: | --- |
| Main tendon | 33,992 | Watertight, consistently paired edge directions; continuous gross surface, no zero-area triangles |
| Separate source fragment | 12 | Nonzero area, 5 non-manifold edges, no boundary edges; retained without repair |

The main bounds are approximately X −73.944..−18.766, Y 60.751..108.655,
Z −736.542..−479.890 mm. Its superoinferior extent is 256.651 mm. The main surface
has no non-manifold edges; the aggregate part's non-manifold flag comes from
the separate tiny component.

That small component spans approximately **0.006409 × 0 × 0.000061 mm** and has
surface area **6.6031 × 10⁻⁷ mm²**. It is planar and carries nonzero triangle area,
so it is not eligible for the authorized empty-facet cleanup. Its location is
near X −70.44, Y 98.733, Z −501.822 mm, inside the main part's overall bounds.
It does not expand the Achilles bounding box. This describes a source topology
irregularity, not an anatomical structure or a diagnosis.

The source's broad proximal surface, distal narrowing and posterior calcaneal
position are inspectable in the QA figure. They are useful gross reference
features. The dataset's approximately **1.154 × 1.154 × 1.2 mm** segmentation
sampling and author-applied smoothing limit fine morphology. Tendon fascicles,
subtendons, paratenon, enthesis layers and pathology are not established by this
mesh. No thickness or clinical grading validation was performed here.

## Other source components that must remain visible in the audit

| Source muscle unit | Retained component facet counts | Non-manifold edges |
| --- | --- | ---: |
| Extensor digitorum longus | 33,924 + 2 | 0 |
| Extensor hallucis longus | 21,320 + 2 | 0 |
| Flexor digitorum longus | 20,492 + 40 + 6 | 23 |
| Tibialis anterior | 48,972 + 8 + 8 + 8 + 4 + 4 + 2 + 2 + 2 | 13 |
| Tibialis posterior | 41,536 + 32 + 6 + 4 | 6 |

All these components have been preserved. Zero boundary-edge count alone is
insufficient to establish a sound closed volume: duplicated or non-manifold
surfaces can have no boundary edges. These objects retain the source's
**muscle-unit** identity. A tapered end, by itself, does not prove that a
clinically distinct distal tendon or sheath is separately available.

## Registration and framing implications

All 20 object labels were matched to their source NRRD segment identities by the
registration pass. Seventeen mesh/voxel extent checks were within 2.5 mm; the
whole tibia and fibula differed by up to 4.755 and 3.679 mm, and flexor digitorum
longus by up to 12.693 mm. Achilles differed by up to 1.242 mm. These are
extent-comparison findings, not an image-registration accuracy certificate.
The larger flexor-digitorum-longus discrepancy remains a source-review item.

The region's initial focus is derived from talus and calcaneus bounds. Most of
the Achilles lies superior to that box: its upper extent is **213.329 mm above**
the box's superior boundary. A close ankle view therefore cannot be presented
as the entire tendon. Selection/isolation should permit inspection of the full
native tendon extent, with any viewing crop disclosed.

An initial metadata read found a stale knee T2-FS sampling field in the ankle
manifest. The root task corrected it before packaging. The final independent
checker requires that no knee-grid field or local knee-image reference remains,
and that `clinical_image_pair.available` is false. No ankle-specific clinical
image/mesh pair is claimed by this audit.

## Visual evidence and reproduction

Visually inspected, staging-only figures:

- `independent-achilles-audit.png`: full tendon/bone context, distal ankle view,
  and independently magnified 12-facet fragment.
- `independent-muscle-units-audit.png`: tibialis anterior/posterior and flexor
  digitorum longus source units with their small nonzero components retained.

Reproduce with the isolated NumPy environment:

```sh
PYTHONPATH=/tmp/primer-msk-sources/python \
  /Users/peter/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 \
  tools/anatomy_sources/check_malaya_ankle.py --render
```

The optional render requires Matplotlib. Both the checker and figures write
only under `/tmp/primer-msk-sources/high-fidelity/malaya-ankle`. The technical pass
supports packaging a clearly bounded, separately selectable reference source.
It does not close the outstanding ankle ligament, cartilage or component-level
clinical review requirements.
