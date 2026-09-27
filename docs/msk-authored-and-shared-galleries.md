# Authored and shared MSK figure galleries

27 September 2026. The hamstring gallery currently consists of two explicitly
shared Hip/FAI figures. Adding a directly authored MRI reference must retain
those references rather than replace the entire gallery.

The catalogue now supports an explicit `mode: append` in a structured sharing
record. It requires an existing, distinct authored target gallery and preserves
its figures first, followed by the explicitly selected shared figures. Unknown
modes, implicit overwrites, self-appends and duplicate figure identities are
rejected. Cross-topic scope fingerprints include append mode, so changing the
merge behavior invalidates an existing scope review. Source IDs, hashes and
figure provenance remain unchanged.

28 focused tests passed across model bindings and investigation integration.
Tests use a synthetic authored gallery to verify preservation and reject an
implicit overwrite or a replace mode. Existing gallery configuration is not
changed by this infrastructure update. The acquired Weber MRI figure remains
offline until its authored record and explicit partial evidence are integrated.
No anatomical requirements, reviews or fidelity counts changed.
