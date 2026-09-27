# Independent knee component audit — 26 September 2026

**No actionable source-preservation or side-assignment defect found.** This
conclusion concerns the four source subsets and their provenance, not clinical
fidelity. No production file or approval status was changed during this audit.

Reviewed implementation:
`tools/anatomy_sources/split_malaya_knee_components.py`, the published nested
component records in `web/anatomy/msk-mri-knee/manifest.json`, and
`docs/msk-knee-component-reconciliation.md`.

## Independent source correspondence

The independent checker does not import or call the splitter. It reads the
original `um-final-model-stl.zip`, verifies the published source archive SHA-256,
then compares each child directly to the original binary STL using the recorded
original facet indices. Every triangle corner's float32 bytes and every facet
normal's float32 bytes match exactly, including bit-level signed-zero identity.
The two children of each parent are disjoint and exhaust every retained parent
facet in its original order. No nonzero source surface was discarded.

The two original files contain 11,560 facets; the four children contain 11,544.
The 16 omitted facets in these two source files were independently confirmed to
have exactly zero area and repeated vertices. This audit did not re-audit the
remaining 32 omissions elsewhere in the 28-object atlas.

| Child | Exact original facets | Recomputed connectivity |
| --- | ---: | --- |
| Lateral meniscus | 2,000 | One closed component |
| Medial meniscus | 3,196 | One closed component |
| Lateral tibial plateau cartilage | 2,772 | One closed component |
| Medial tibial plateau cartilage | 3,576 | One closed component |

Topology was independently recomputed after welding numerically identical
positions only, without a tolerance. All four are watertight, consistently wound
and contain no zero-area triangles. Child bounds and normal-length extrema also
recompute to the published values.

## Positional identity

Within the verified native right-sided LPS frame, higher X is medial. The
component X bounds do not overlap. Independent source landmarks agree:

- Proximal fibula (inspection window Z > −380 mm): X −98.586 to −74.807 mm.
- Source-labelled LCL: X −100.686 to −84.456 mm.
- Source-labelled MCL: X −24.248 to −8.681 mm.

The area-weighted X centroids are −79.213/−30.015 mm for lateral/medial
meniscus and −76.487/−35.124 mm for lateral/medial plateau cartilage.
Both lateral components lie toward the fibula/LCL; both medial components lie
toward the MCL. The existing superior source-frame projection was also inspected
and agrees with this assignment. No reflection, fitting or inter-atlas alignment
was used to obtain that interpretation.

These medial/lateral names remain **Primer positional interpretations**. The
original segmentation labels are combined `Meniscus_Knee` and `Cartilage_Tibia`;
the child records correctly retain those parent labels as source provenance.

## Inherited metadata and limits

The splitter removes the parent volume, unique-position count and
mesh-to-voxel-extent measurement. Those combined-object measurements are absent
from all child records. Remaining topology, bounds and normal measurements
were independently recomputed and agree with the current values. Source STL
bytes/hash and segmentation identifiers refer explicitly to the unchanged
combined source file, while child compressed/decoded bytes and hashes identify
the actual derivative.

Splitting adds selection, not anatomical detail or evidence of complete tissue
boundaries. Source MRI sampling and smoothing limitations remain. Individual
horns, roots, attachments, free-edge regions and cartilage layers are not source
labelled here. A complete connected source subset is not equivalent to complete,
clinically validated meniscal or cartilage anatomy. The reviewed documentation
preserves this distinction and all four fidelity-review statuses remain pending.

## Evidence and reproduction

New independent checker:
`tools/anatomy_sources/audit_malaya_knee_components.py`.

Run with Python 3.12 and the staged NumPy/trimesh dependencies via
`PYTHONPATH=/tmp/primer-msk-sources/python`.
It writes only:
`/tmp/primer-msk-sources/high-fidelity/malaya-knee/component-audit/independent-component-audit.json`.
The evidence includes the exact reviewed manifest hash, four child hashes,
recomputed measurements and landmark coordinates. The audit pass grants no
clinical approval and does not modify the evidence ledger.
