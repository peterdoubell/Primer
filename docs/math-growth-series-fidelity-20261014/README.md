# Growth, decay, sequence and series fidelity

Date: 2026-10-14. These changes repair two specific curriculum gaps. They do
not establish complete mathematics or whole-Primer coverage.

The existing `math.3.sequences` lesson explicitly teaches sums to infinity,
including negative and fractional ratios, but the concept activity permitted
only positive first terms and ratios at least one. It could never demonstrate
the convergent geometric series described by its own lesson. The existing
`math.3.expo-logs` lesson teaches growth and decay; its activity permitted only
bases 2–5 and integer exponents, so exponential decay was unavailable.

## Shipped changes

Only two scenario specifications and their two branches in `drawGrowthTrig`
change in `web/concept-models.js`. A small `mathValueText` helper retains small
nonzero tails and large values in scientific notation.

The sequence activity now permits first terms −4 to 4, differences/ratios −4
to 4 in quarter steps, and 1–24 terms. It plots the actual term sequence and
partial-sum sequence as distinct series against integer indices, on one
labelled signed vertical scale. Segments guide the eye and do not represent
continuous sequences. The index ruler remains 1–24 across settings; the value
ruler adjusts and is explicitly labelled. Existing positive settings and their
term and finite-sum values are preserved.

Convergent geometric cases show the infinite sum and the signed remaining sum.
The remainder is evaluated directly from the next geometric term rather than
subtracting two nearly equal floating-point totals. A constant nonzero term
sequence is distinguished from its divergent series. Alternating ratios,
ratio zero, ratio ±1, the all-zero series and decreasing arithmetic sequences
have defined behaviour. The all-zero geometric series converges for every
ratio; the usual absolute-ratio condition assumes a nonzero first term.

The exponential activity permits positive bases 0.25–5 in quarter steps and
exponents −3–3 in quarter steps. Base 1 deliberately illustrates failure of a
unique inverse; no logarithm or inverse graph is manufactured for it. Integer
exponents display reduced rational expressions. Other displayed values are
rounded and explicitly introduced as approximate. The exponential graph and
its logarithmic inverse have equal axis scales over [−3,5]². Inverse samples
exchange coordinates exactly. Segments are clipped to the window, and selected
point pairs outside it are omitted with an explicit readout. Curves are sampled
at exponent spacing 1/64. Directly calculated selected points are not rounded
before positioning.

The mathematical families and assumptions are supported by original artwork
and code alongside primary references: [OpenStax geometric sequences](https://openstax.org/books/precalculus-2e/pages/11-3-geometric-sequences),
[OpenStax series and their notations](https://openstax.org/books/precalculus-2e/pages/11-4-series-and-their-notations),
and [OpenStax logarithmic graphs](https://openstax.org/books/precalculus-2e/pages/4-4-graphs-of-logarithmic-functions).
No textbook artwork was copied.

## Evidence

`tools/check_math_growth_series_fidelity.js` independently builds exact BigInt
rational recurrences and sums rather than using the renderer's term power
formulas. All 14,256 allowed sequence settings (two families, nine first terms,
33 differences/ratios, 24 lengths) agree. Exact rational remaining sums verify
convergent cases, with dedicated tests for zero and nonzero constants and
alternating boundary ratios. A tiny positive tail is preserved in the readout.

The 500 allowed base/exponent settings are checked by an independent positive
fourth-root bisection of a rational integer power. Exact displayed rational
strings are checked separately. Base 1 consistently has no logarithmic inverse.

Actual mounted SVG controls, resets and coordinates are checked in 264 cases.
All 20 allowed bases are included in curve checks. The 41,418 retained
exponential segments have a maximum midpoint chord error of
0.010928777251134392 SVG pixels in the checked segments. Logarithmic segments
are exact coordinate reflections of the exponential segments, and selected
point coordinates match the unrounded calculations. This finite sampling
error bound is evidence for these displayed families, not a general plotting
accuracy claim. The test wrapper is `tests/test_math_growth_series_fidelity.py`.

The retained `tools/check_cross_subject_models.js` checks passed: 178 models,
491 controls, 44,003 finite deterministic builds and 489 dispatched changes
and resets. The new test plus retained cross-subject pytest checks passed
31,001 tests locally.

`tools/check_math_growth_series_browser.cjs` mounts the actual renderer using
the two existing curriculum media items and shipped styles in fresh Chromium
contexts, without a database or credentials. Forty desktop/mobile states pass
at widths 1440 and 390, including signed divergence, alternating convergence,
zero, tiny tail, growth, decay, inverse failure, keyboard changes, reset,
label containment, label separation and page overflow. Screenshots and exact
loaded file hashes are recorded in `browser/proof.json`. Representative phone
images were visually inspected. This is standalone renderer evidence; it does
not prove authenticated reader integration or production delivery.

The fresh authenticated lesson-reader evidence in `reader/proof.json` covers both
activities at 1440 and 390 pixels: four cases, 14 changed states, four resets,
four keyboard checks and no page errors. The loaded startup bundles match the
exact concatenations of current source files; curriculum and relevant source
hashes are recorded. Only bounded plot captures are included here. The fixture
used an isolated synthetic learner/database; no production learner flow is claimed.

`curriculum-runtime-inverse.json` and `tools/math_growth_runtime_compatibility.py`
record an exact reversal of only the four changed activity-description lines for
older frozen evidence. Before/after file hashes, literal spans and proof bytes are
pinned; unknown bytes remain rejected by the historical guards. Earlier evidence
and approval scope are unchanged.

## Limits

Quarter-step controls do not offer every real ratio or base, or the lesson's
one-third example exactly. Arbitrary affine recursive sequences, non-geometric
convergence tests, applied half-life/population parameters and logarithm laws
remain outside these two activities. At very different magnitudes, terms may
visually merge on the shared value scale; numeric readouts retain their values.
The finite plot and rounded labels cannot prove convergence of arbitrary
sequences. The two existing curriculum model titles/instructions now describe the broader
controls; other curriculum text is unchanged. Other models, curriculum rasters, advanced labs, the reader and
server are unchanged by this change.
