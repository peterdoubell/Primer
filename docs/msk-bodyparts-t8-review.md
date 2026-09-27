# Independent BodyParts3D T8 candidate

27 September 2026. The official BodyParts3D name table maps eighth thoracic
vertebra to FMA9991/BP9221, and the element table maps FMA9991 to FJ3174. The
[official download page](https://dbarchive.biosciencedbc.jp/en/bodyparts3d/download.html)
and its public LATEST directory expose the 4.0 archive labelled **99% polygon
reduction**. This is not assumed to be an unreduced or clinically high-fidelity
source. The [current publisher licence](https://dbarchive.biosciencedbc.jp/en/bodyparts3d/lic.html)
specifies CC BY 4.0, updated 27 February 2025.

Only the required archive member was acquired using bounded public HTTP ranges.
Responses were HTTP 206 with a consistent ETag. The central directory and local
member name agreed; uncompressed size and ZIP CRC32 matched. The original OBJ
is preserved with SHA-256 in the [acquisition record](msk-bodyparts-t8-review/acquisition.json).
No authentication, hidden endpoint or protected resource was used.

[OBJ topology audit](msk-bodyparts-t8-review/topology.json) finds 2,424 triangles
in one connected component, with zero boundary, non-manifold, inconsistent-
winding and degenerate counts under the basic checker. The source has 1,392
vertices and 1,212 unique exact positions; seam welding was for measurement
only. No mesh repair or resampling was performed. These checks do not establish
absence of self-intersections or anatomical accuracy.

The candidate remains separate from Z-Anatomy. Source coordinates, version and
geometry have not been reconciled to that assembly. A single-level substitution
would risk mixing incompatible anatomy; no fit, scale or swap has been applied.
The [original OBJ](msk-bodyparts-t8-review/FJ3174.obj) is an offline source-
comparison artifact, not clinical approval. Broader acquisition of a consistent
source chain or independently reviewed registration is needed before integration.

Attribution: BodyParts3D, © The Database Center for Life Science licensed under
CC Attribution 4.0 International. The OBJ is the unchanged archive member;
metadata and topology analysis are newly generated review evidence.

## Fidelity screen before wider acquisition

The official README confirms an anatomical dictionary based on an adult male
whole-body model and labels the downloadable 4.0 meshes as 99%-polygon-reduced.
The indexed primary construction paper (doi:10.1093/nar/gkn613) describes the
TARO MRI framework and later illustrator refinement of missing/blurred detail.
Direct opening of the publisher paper was inaccessible and was not retried.
That historical description must not be treated as version-specific accuracy
validation of this T8 object.

[Fidelity decision](msk-bodyparts-t8-review/fidelity-screen.json): retain this
candidate offline. Clean topology is insufficient evidence for fine endplate,
facet, pedicle or cortical anatomy, and does not establish compatibility with
the Z-Anatomy chain. A larger download of this same reduced archive would not
resolve those evidence gaps by itself. No enlargement, smoothing or presumed
increase in triangle count is proposed as an accuracy remedy. Requirements and
clinical approval status remain unchanged.
