# Radiology reference visuals — September 2026

Built on the current reporting-reference release, not on the older curriculum
checkout. The earlier unmerged whole-curriculum work is left untouched.

## Changes

- Ported the reviewed, lesson-specific radiology drawing implementations and
  regenerated 83 pairs of responsive WebPs. The existing CT phantom is retained.
  All 84 final small plates match the earlier reviewed outputs byte-for-byte;
  the generator validates all 168 responsive assets.
- Preserved the newer reporting frameworks and report templates. Adjusted the
  generated captions/descriptions where the reviewed diagram metadata differed.
- Added a Doppler angle model to Ultrasound Physics: independently vary actual
  insonation angle, assumed correction angle and true speed. The model exposes
  the signal/estimate distinction and the zero-shift-at-90-degrees limitation.
  It is an ideal single-speed demonstration, not a diagnostic calculator.
  The existing CT-window model remains available.
- Added a keyboard-focusable jump from each radiology module heading to its
  visual reference. On mobile it clears the sticky navigation strip.
- Fixed the grid's intrinsic minimum sizing so wide reporting tables cannot
  widen the entire page and crop its visual reference.
- Corrected the ultrasound reference's contradictory instruction to reduce the
  beam angle to reduce aliasing. A smaller angle increases shift at fixed speed;
  baseline movement reallocates display range without changing PRF.

## Sources for the new physics model and correction

- [Uppal et al., RBC motion and the basis of ultrasound Doppler instrumentation](https://onlinelibrary.wiley.com/doi/abs/10.1002/j.2205-0140.2010.tb00216.x)
- [American Society of Echocardiography: identification and mitigation of cardiac ultrasound artifacts, 2026](https://www.asecho.org/wp-content/uploads/2026/05/PIIS0894731726000386.pdf)

## Verification

The browser checker covers all 84 real radiology module routes and their image
loads, preservation of reporting-reference cards, the Doppler numerical states,
keyboard controls, reset, desktop/mobile bounds, both themes, the image viewer,
and the jump's clearance below mobile navigation. Wikipedia is deliberately
offline in the isolated QA server; this is not a test of external article fetches.

Focused Python tests cover radiology drawing regressions, reference data and
curriculum validation: 433 passed, two skipped. All 84 browser routes and the
model interaction checks passed in the final run, with no page errors.
JavaScript syntax and Git whitespace checks passed.
A broader run was interrupted after 315 passes and one
skip because unrelated live Wikipedia requests made it slow; it is not a full
suite pass.

No production deployment or merge is included in this change.
