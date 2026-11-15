# Panel-state consistency in the MSK fidelity gate

Reviewed 27 September 2026. This change checks the consistency of recorded
source facts. It does not infer a diagnosis from image pixels, approve an asset
or reduce any anatomical requirement.

## Confirmed failure and correction

The existing gate compared selected panels with their recorded modality and
bound reviews to the exact asset/requirement scope. It did not compare a
panel's recorded depiction state with the asset's claimed state. Consequently,
selecting the explicitly pathological panel c of the ligamentum-flavum
comparison could retain a normal-reference claim if a review fingerprint was
refreshed. Old fingerprints became stale, but the contradiction itself was
not rejected.

`inspect_source_context` now checks every credited panel when explicit
`panel_states` are supplied. Malformed state maps fail; a missing selected
panel state remains unresolved. An explicit uniform claim also fails when the
selected panel's state is unknown or contradictory. Known normal-reference
codes are compatible with the existing normal/normal-variant composite, while
specific non-normal states must match their declared code.

An overall `unknown` or `mixed` state does not assert a uniform depiction.
Those labels still cannot satisfy a requirement explicitly calling for normal
anatomy: the independent requirement-context check remains in force. No state
is guessed from a caption, a filename or a missing field. Existing references
without typed panel states retain their prior behavior and review obligations.

## Actual source selections

- The existing spinal comparison keeps normal MRI panel b and schematic
  panel a as separate representations. Its recorded hypertrophy panel c cannot
  be selected while claiming normal anatomy. The [source rendering record](msk-spine-pdf-rendering.md)
  and all source image bytes remain unchanged.
- The [Siddle lesser-MTP composite](msk-lesser-plantar-plate-source.md) now records
  its already-reviewed states explicitly: a/b are the intact third-MTP
  reference; c/d depict a fifth-MTP tear; e–h depict plantar-plate pathology
  in rheumatoid arthritis at other joints. Only a/b remain credited. Its
  single local body candidate, mtp3 site, source pixels and pending review are
  unchanged.
- The elbow normal/normal-variant composite retains its valid selection.
  Neither its variant description nor another source's normal reference is
  silently converted into a normal whole-examination claim.

Per-panel checks do not resolve selection within a panel containing multiple
regions or sides. In particular, the hip minimus comparison includes an intact
left insertion and right-sided pathology in the same panel. Its region limits
remain explicit; no fabricated whole-panel normal state is added here.

## Verification and limits

Tests use explicitly synthetic approvals to reproduce the failure: a normal
panel initially passes, then selecting a recorded tear still fails after both
synthetic review fingerprints are renewed. Real-source negative cases reject
spinal panel c and all six non-reference plantar-plate panels without changing
their image hashes. Normal/variant, unknown, mixed, malformed and missing-state
cases are also checked.

All 5,202 representation requirements and their report definitions remain.
Correct source selections gain no anatomical or visual approval from these
checks. The published-state mapping is still evidence that requires source
review; this gate cannot certify that a curator's underlying facts are true.
