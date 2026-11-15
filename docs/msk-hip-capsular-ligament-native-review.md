# Hip capsular ligament native-source review — 30 September 2026

Four already available right hip ligament objects are genuinely named in the
original Z-Anatomy FBX. Their original positions and oriented polygon faces are
preserved by the current runtime buffers. They are coarse, closed artist
surfaces, with no paired segmentation or measured tissue thickness.

**No new current requirement binding is recommended.** The inspected
`msk-structure-requirements.json` has no iliofemoral, pubofemoral or ischiofemoral
requirement IDs. Its nearby `hip.hip_capsule_and_synovium` requirement calls for
anterior and posterior recesses. A separate named capsular band does not
establish either recess or synovial tissue. This review does not invent
requirements to claim progress, substitute named surfaces for different
tissues, or change the source geometry, ledger, reader or approval status.

## Native source and current preserved objects

The exact original file was reused from the previous bounded acquisition:
`Joints100.fbx`, 9,804,796 bytes, SHA-256
`f4ba7a910cdaef99e31530f368628780d9f06b5d77853f8b721f47f67137e823`,
at Z-Anatomy commit `6c7f9016bd5899ac8edafd31b9900c151df42ed6`.
The [acquisition record](msk-hip-capsular-ligament-native-review/acquisition.json)
retains its pinned URL and earlier reacquisition time. No new model download
was necessary. The review reads the original FBX position, polygon, model,
geometry connection and material arrays directly.

| Runtime asset | Original model name | Native positions / oriented quads | Published triangles |
| --- | --- | ---: | ---: |
| `za-joints-318012956` | Transverse part of iliofemoral ligament.r | 234 / 232 | 464 |
| `za-joints-347770529` | Descending part of iliofemoral ligament.r | 306 / 304 | 608 |
| `za-joints-142701643` | Pubofemoral ligament.r | 198 / 196 | 392 |
| `za-joints-731742504` | Ischiofemoral ligament.r | 338 / 336 | 672 |

These are four complete **source objects**, not proof of complete anatomical
structures. The transverse and descending iliofemoral names are original
separate models; this review did not split one mesh into inferred arms.
All actual polygon material assignments are `Ligament`, index 0. The
iliofemoral and ischiofemoral models also have unused `Cartilage` and `Bone-1`
material slots. The objects audited here are whole meshes, rather than
extracted material patches.

Every original local position, transformed by the existing ufbx-evaluated
`geometry_to_world` matrix retained in the current manifest, matches the
published unique float32 position set exactly. The bounded audit does not
independently reevaluate the full FBX transformation hierarchy. Every original
oriented quad is exhaustively represented by its two oriented runtime
triangles, with no additional triangles. Normal seams account for extra render
vertices. All four source and unique-position runtime topologies have one
connected component, Euler characteristic 2, and zero boundary, nonmanifold or
inconsistently wound edges. Runtime triangles have no zero-area faces.

All four position sets are nonplanar. Their signed enclosed artist volumes
are respectively 0.27236, 0.30098, 0.24432 and 0.26853 cm³. These numbers measure
closed artist envelopes, not biological tissue volume or measured thickness.
The edge and nonplanarity checks do not prove freedom from self-intersection
or anatomical accuracy.

Exact model/geometry IDs, original and current file hashes, bounds, singular
values, material assignments, topology and current requirement-scope hash are
retained in the
[native preservation audit](msk-hip-capsular-ligament-native-review/native-preservation-audit.json).

## Shared-frame and isolated visual evidence

The
[shared-frame projections](msk-hip-capsular-ligament-native-review/shared-native-frame.png)
retain these four surfaces and the source right hip bone and femur in the same
frame. Native units are centimeters, with +X patient left, +Y superior and +Z
anterior. Display uses the proper basis change to RAS millimeters; no fitting,
translation or deformation is introduced. The original `.r` model names and
negative native X bounds support the supplied right-side designation. No new
left-side validation is claimed.

The
[isolated projections](msk-hip-capsular-ligament-native-review/isolated-source-surfaces.png)
show visible faceting and thin curved artist bands. The two iliofemoral source
bands are distinct in their anterior frame, while the ischiofemoral source
band is posterior. Pubofemoral is a curved narrow surface. These observations
describe the supplied source objects; they do not validate anatomical
endpoints, full attachment coverage, histological boundaries, separate fibers
or ligament thickness. The image scale is fixed between views within each
isolated-object column and differs across columns.

Both figures were opened and inspected. Their hashes and observations are
retained in the
[projection inspection](msk-hip-capsular-ligament-native-review/projection-inspection.json).
Transparent context bones and omitted distant context triangles affect only
the review projection; source geometry remains unchanged. These derivative
projections retain the existing
[source attribution](../web/anatomy/msk-atlas/ATTRIBUTION.md) and
[pinned model notice](../web/anatomy/msk-atlas/SOURCE-LICENSE.txt), including
BodyParts3D lineage and Z-Anatomy credits, under CC BY-SA 4.0.

## Reproducible check and next decision

The bounded
[review tool](../tools/anatomy_sources/review_hip_capsular_ligament_native.py)
completed its file-hash, model/geometry/material connection, exact position-set,
oriented-quad preservation and topology assertions for all four objects:
1,076 original positions and 2,136 retained triangles. It also enumerated all
current explicit structure and required-part names/IDs and found zero exact
named ligament requirements. Offline NumPy/Matplotlib dependencies were used;
no application dependency changed.

If a specialist-approved report scope later explicitly adds gross ligament
course, these exact source IDs offer an unapproved **partial** artist-surface
candidate for review. Their current native shape alone does not justify a
complete binding or approval. Until then they remain existing orientation
references, without new representation coverage. They cannot be repurposed as
capsule recesses, synovium, cartilage or ligamentum teres.
