# Thoracolumbar source-bone inventory and export

27 September 2026. All seventeen named T1–T12 and L1–L5 objects are present in
the acquired Z-Anatomy skeletal source. Fresh exports preserve their source
model/geometry IDs, evaluated world transforms and all original triangles.
No other level was substituted, mirrored, aligned or reshaped.

[Per-level export audit](msk-thoracolumbar-source-review/export-audit.json)
records binary hashes, native bounds, source-bound rounding differences and
independently calculated edge-incidence/topology findings. Binary lengths,
finite coordinates and index ranges were checked. Fresh evaluated transforms
match the earlier source inventory; this is not an independent derivation of
the FBX hierarchy or clinical registration validation.

Sixteen levels have zero boundary, non-manifold and degenerate counts under
these checks. T8 has two boundary edges and 117 non-manifold edges. A complete
source assembly is held pending source diagnosis; T8 is not silently removed
or replaced with a neighbouring vertebra. Closed topology alone does not prove
endplate, facet, pedicle, cortical or marrow fidelity. No pathological feature
is inferred from a mesh defect.

The source also does not automatically supply the discs, posterior ligamentous
complex, neural anatomy or fracture findings required by the reporting scope.
The full original requirements remain active. All exports remain offline at
`/tmp/primer-msk-sources/thoracolumbar-staged/`; no runtime assets or clinical
approvals were added. The reproducible checker is
`tools/anatomy_sources/audit_thoracolumbar_exports.py`.

Source attribution and acquisition licence remain the existing Z-Anatomy /
BodyParts3D lineage review under CC BY-SA 4.0. The audit is evidence about these
specific files, not blanket approval of the source dataset.

## T8 defects traced to original polygons

The original T8 geometry contains 1,681 triangles, 23 quadrilaterals and two
pentagons. Its native-coordinate edge incidence contains 112 edges with four
incident polygons, five with three, and two boundary edges. The same incidence
histogram persists after source-world transformation and float32 encoding, and
every abnormal edge matches the exported endpoints and incidence exactly.
Thus neither export triangulation nor float32 rounding introduced these findings.

[Source comparison](msk-thoracolumbar-source-review/t8-source-topology.json)
records all affected coordinates and file/geometry fingerprints. The reusable
`compare_bone_source_topology.py` checker compares source polygons directly;
it does not triangulate or repair them to obtain the source edge count.
Six topology/incidence tests passed, including quad-versus-triangle boundary
agreement and preservation of duplicate incident-face counts.

This diagnoses the source mesh, not a fracture or other biological abnormality.
No duplicated face was removed, no gap filled and no adjacent vertebra scaled
into its place. Source replacement or an anatomically reviewed correction remains
necessary before claiming a complete checked thoracolumbar model. Runtime scope
and clinical approval status remain unchanged.
