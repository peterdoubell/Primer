# Measure integration and convergence fidelity review

## Scope and integration contract

The original `math.5.measure` lesson assesses Lebesgue integration, null sets, dominated convergence, fat Cantor sets, atoms, measurability and the Vitali obstruction. Its existing cover illustration and Cantor-set concept activity are correctly bounded examples, but they do not interactively represent integration or dominated convergence. This additive activity addresses that substantive gap. It is initially bound only to Measure Theory; it does not claim to fulfil Functional Analysis or the complete mathematics curriculum.

Renderer: `math-measure-lab`. Props must be exactly `{ "scenario": "math.5.measure.integration-norms" }`. Load `web/math-measure-lab.js` and `web/math-measure-lab.css` before renderer registration. The script exports the same frozen API as `window.PrimerMathMeasureLab` and through CommonJS. `build(state)` is DOM-independent; `render(item, hooks)` returns a section or null for an unsupported scenario/renderer. `hooks.speakButton` receives a callback that obtains the current readout and assumptions when invoked. No external plotting or 3D library is needed.

State controls: integer `n` from 1 to 65,536; `amplitude` from 0 to 8 in quarters; `alpha` selected from the strings `0`, `0.5`, `1`; integer rational-probe `numerator`/`denominator`, with `0 ≤ numerator ≤ denominator ≤ 65,536` and denominator at least one; boolean `zoom`. Initial state is `n=4`, `A=2`, `α=1`, probe `1/4`, zoom enabled. This has height eight on a set of measure one quarter and integral two, matching the lesson's simple-function example. Number inputs preserve drafts while typing, then normalize on change; clearing an input cannot insert a fallback digit into the next typed value.

## Mathematical contract

The domain is `[0,1]` with Lebesgue measure `dx`. Coordinates, function values, integrals and norms in this example are dimensionless. The sequence holds A and α fixed:

`h_n(x) = A n^α 1_(0,1/n)(x)`.

Both endpoints are excluded, including x=0. The displayed interval has measure `1/n`. When A=0 its nonzero set is empty; the interval's measure must not be presented as the measure of a nonzero support.

The exact identities are:

- integral and L¹ norm: `A n^(α−1)`;
- squared L² norm: `A² n^(2α−1)`;
- L² norm: `A n^(α−1/2)`;
- supremum and essential supremum: `A n^α`;
- accumulated integral for `0 ≤ t ≤ 1`: `H_n(t) = A n^α min(t,1/n)`.

For a fixed rational probe `a/b`, membership is checked by integer arithmetic: `a>0` and `n*a<b`. Equality is outside. If a>0, every `n≥ceil(b/a)` yields zero at that same point. At a=0 every term is already zero. All three families converge pointwise everywhere to zero and hence almost everywhere. At finite n and A>0 they remain nonzero on a set of positive measure: pointwise convergence is not equality to zero almost everywhere at each finite stage.

For A>0, α=0 has a common dominator A and converges in L¹ and L², but not uniformly. For α=1/2 the common dominator is `A/√x` on x>0, defined as zero at x=0, with integral 2A. Its L¹ norm tends to zero while its L² norm stays A. Growing peaks alone do not imply failure of dominated convergence.

For α=1 and A>0, the common envelope is `A(ceil(1/x)−1)` on `0<x≤1`, not `A/x`. It is at least `A/(2x)` on `0<x≤1/2`, so its integral diverges. The integral of h_n stays A and cannot be interchanged with the pointwise limit. This also rules out a dominator stated almost everywhere: the countably many exceptional null sets can be combined. A=0 is a separate branch: every norm vanishes, uniform convergence holds, and zero is an integrable dominator for every α.

These uses of dominated convergence and almost-everywhere equivalence follow [MIT 18.125 Lecture 5](https://ocw.mit.edu/courses/18-125-measure-and-integration-fall-2003/1473498db368e7a3194855b6935cc616_18125_lec5.pdf). The norm conventions follow [MIT 18.125 Lecture 15](https://ocw.mit.edu/courses/18-125-measure-and-integration-fall-2003/0c85400465928cf42a19e5b87bdc349c_18125_lec15.pdf). Graphics and code are original; no source figures or media were copied.

## Representation and numerical verification

Four native SVG plots show the full unit interval, a labeled support detail, accumulated mass, and the three exact norm power laws. The full support's width is genuinely `350/n` SVG coordinate units. It is not widened to a minimum pixel. At n=65,536 it is about 0.00534 units wide, while the exact integral remains available in the readout. The detail view changes the labeled x-axis; it does not change dx, the function or its mass. Open top endpoint circles and filled zero endpoint circles distinguish the values at discontinuities when there is room to draw them. Dashed jump-location guides are explicitly not part of the function.

Height and accumulated-mass axes rescale and say so. Tiny positive accumulated mass retains a positive plotted scale. Zoom ticks use shorter scientific notation where needed. The norm panel plots `log₂(norm/A)` against n on a base-two logarithmic scale, using exact power laws; A=0 has no logarithmic points or division by zero. The activity states that a finite plot does not prove a sequence limit. Exact formulas and analytic arguments are distinguished from rounded decimal evaluations.

`tools/check_math_measure_lab.js` passes 150 independently boundary-split integration states, 309 exact rational probe states and 28 mounted control states. It checks actual rectangle coordinates and geometric area after undoing axis scales, accumulation vertices, norm-line coordinates, endpoint markers, current speech callback text, reset/enlargement state, malformed state normalization and number-input clearing/typing. It also demonstrates a 512-point midpoint grid missing the entire n=1,024 spike despite its exact integral of one.

`tests/test_math_measure_lab.py` passes four tests under the known Python 3.12 scientific environment. Independent Fraction arithmetic verifies probe membership, thresholds and squared L² norms; SciPy quadrature integrates separately on `[0,1/n]` and `[1/n,1]`. Splitting is essential: a whole-domain quadrature can miss a thin spike. A separate read-only reviewer compared 2,178 actual build states with 4,356 split SciPy integrations and rational invariants, with no remaining mathematical mismatches and maximum scaled numeric discrepancy about `2.30×10^-16`.

## Standalone browser evidence

An explicitly selected installed Google Chrome, owned session `math-measure-20261010`, exercised 22 numeric states at 1440×1100 and 390×844, plus dark mode, enlargement, reset, current speech callback text and native number editing. Cases include all three exponents, A=0, the exact rational endpoint, positive tiny mass and n=65,536. Actual SVG rectangles retain analytic dimensions and area after scale conversion. All SVG text stayed within its own image and had no pairwise label overlap in tested states; the page had no horizontal overflow or page exceptions. Enlarged SVGs scroll inside their focusable viewports, including keyboard panning. Screenshots were inspected. The browser checks found and corrected tiny-axis label collisions and the numeric-entry fallback defect before the final pass.

Ignored reproducible evidence is in `.research/math-measure-browser-review/browser-proof.json`, with the browser script, harness and screenshots beside it. This standalone check verifies the new component with current global styles and a speech-callback capture; it does not claim audible pronunciation or integrated application speech behavior.

## Integrated application browser evidence

The first integrated lesson check at `http://127.0.0.1:8900/#/node/math.5.measure` passed the same 22 numeric states at 1440×1100 and 390×844 in the separate explicitly selected Chrome session `measure-route-20261010`, using the root-owned disposable QA profile/database. At that check the new lab appeared alongside the original cover illustration, Cantor activity and contextual surface; the later quantitative 3D replacement is reviewed separately below. Exact rational boundaries, tiny positive mass, A=0, norm plots, dark mode, enlargement/reset, native number editing and keyboard panning passed. Actual rectangle coordinates and scaled area agreed with the mathematics; tested SVG labels had no clipping/overlap, and the page had no horizontal overflow or runtime exceptions. Final screenshots were inspected. Capturing the app's real speech queue confirmed that recombined chunks equal the complete current callback text, including the positive `0.0000038147` integral; the longest tested chunk was 1,191 characters. This checks text transport, not audible pronunciation. Ignored evidence is `.research/math-measure-browser-review/actual-route/browser-proof.json`, with screenshots and the replay script beside it. The proof records final JS SHA256 `564b56ba407c7a9a0f00741268c837de4c16124ead442c44fcdc577e8f9b3620` and CSS SHA256 `17ed2075e7cd715e510962dcccab4a0ab60ac54c37f3e273c77ec71988f3c4d0`.

## Remaining coverage

The original measure illustration and Cantor interaction remain useful. This addition meaningfully addresses simple-function integration and dominated convergence, especially quiz items 2, 5 and 9. It does not implement integration against atoms, countable exceptional-set editing, the rational/irrational indicator, inner/outer measure, sigma-algebras, the full probability foundations or Vitali construction. The 2D activity remains separate from the later `shrinking-support-subgraph` 3D companion, whose quantitative volume, closure semantics and actual-browser evidence are reviewed in [Integration and Carnot 3D fidelity review](integration-cycle-spatial-review.md). That companion represents this particular sequence, rather than all measure theory. Functional Analysis still lacks interactive infinite operators/spectrum, noncompactness, completeness and duality. Neither module nor the all-subjects fidelity goal is complete.
