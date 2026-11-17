# Stored figures bound from their own captions (2026-11-17)

Openly licensed figures already stored in the repository were bound to nothing. This step binds a
figure to a structure only when all of the following hold:

1. the figure's stored published caption or structure note names the structure;
2. the figure was looked at and is consistent with that;
3. the fidelity checker finds no modality or side conflict for any investigation sharing the structure.

Result: 29 bindings on 21 figures, 18 further required structures covered (240 → 258 of 57,985).
Coverage is always `partial`. No asset is anatomically approved and no radiologist has reviewed these.

Why so few: 348 name matches were found among 823 unbound stored figures, but 302 fail the checker,
about 190 of them because the figure's record does not state a side while the requirement is sided.
Thirteen more were rejected on review (see `review.json`): diagnoses rather than anatomy, a structure
named only elsewhere in the record, a section heading rather than a panel description, a perfusion-map
composite, and a mixed-modality figure an existing rule keeps unbound.

Files: `review.json` (accepted and rejected pairs), `inverse.json` (exact byte edits and hashes),
tool `tools/anatomy_sources/bind_stored_caption_assets.py`, tests `tests/test_stored_caption_bindings.py`.
