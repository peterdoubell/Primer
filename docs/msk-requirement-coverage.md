# Anatomical completeness per requirement

27 September 2026. Source quality, review approval and a structure-name binding
cannot by themselves establish that the complete required anatomy is depicted.
The fidelity audit now requires a `requirement_coverage` entry for each matched
structure requirement, for images, schematics and 3D.

Each entry records `extent` (`complete`, `partial` or `unknown`) and a nonempty
`basis` explaining the claim. Missing, malformed, unknown and partial entries
cannot satisfy a requirement, even with otherwise fresh approvals. Existing
assets without this evidence remain candidates. No complete-coverage claims
or clinical approvals were added to real assets.

This differs from `source_context.extent`: a local source might fully depict a
local requirement, while a large field of view might depict only part of a
tendon. Evaluate completeness against the actual requirement, report references
and conditions; do not infer it from captions, names or pixel dimensions.

Coverage records participate in the existing review fingerprint. Changing a
claim or its basis invalidates prior reviews. A complete claim still needs all
source, modality, rights, anatomical and visual checks. The automated gate does
not establish whether that claim is clinically true.

The Mechó rectus femoris and Boutin hamstring/psoas references have explicit
partial records, retaining their source selections and limits. Other legacy
claims have not been guessed or bulk-approved. Multiple partial assets do not
automatically combine into complete coverage; a future reviewed collection
needs explicit, fingerprinted evidence covering the full requirement.

183 focused tests passed, including synthetic fresh-approval counterexamples,
independent coverage for each requirement, stale-review rejection after a
coverage change, malformed claims, and two partial candidates that must not
silently become complete.

The [snapshot](msk-verification-coverage-extent-2026-09-27.json) preserves all
5,202 requirements: 0 verified, 146 unverified and 5,056 missing. Readiness
remains false. No viewer or source image was changed.
