# Authenticated lesson-reader verification

Date: 2026-10-14. `proof.json` records four actual reader cases on a fresh
isolated loopback server, using synthetic Basic authentication and an isolated
synthetic profile/database. Both updated lessons were opened through their
actual `/app/#/node/…` routes at widths 1440 and 390.

Fourteen changed activity states passed: alternating convergent sequences,
constant terms with divergent series, a tiny positive remaining sum, the zero
series, exponential decay with a fractional exponent, base-1 inverse failure,
and a selected point outside the graph window. Actual rendered values,
label containment, absence of invalid SVG attributes and page overflow,
four resets and four keyboard/focus checks passed. There were no page errors.
The mounted titles/instructions equal the final curriculum descriptions.

The application loads consolidated startup assets. Both browser-loaded bundle
bodies were compared byte-for-byte with exact concatenations of the current
shipped sources and the original separators/prefix. Their full hashes and
sizes are recorded, along with four relevant individual source hashes and the
curriculum hash. These checks establish that the tested reader used the current
source code, rather than an earlier cached bundle.

Eight bounded graph screenshots are retained here (241,664 bytes total).
Larger viewport/activity captures remain in ignored private research at
`.research/math-growth-series-reader-20261014/`. The reproducible checker is
`.research/check-math-growth-series-reader-20261014.cjs`, which reloads the
fixture metadata and never accesses production. Final standalone-renderer
browser evidence was regenerated separately after the curriculum edits; all
recorded source hashes match the final files.

This verifies authenticated local integration of the two activities. It does
not establish production delivery or complete mathematics/radiology coverage.
