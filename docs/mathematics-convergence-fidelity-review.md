# Analysis: convergence, tails and endpoints

The actual `math.4.analysis` goal names convergence. Its existing model gives an
epsilon–delta neighbourhood for x²; that remains unchanged. The new activity
adds nine mathematically specified examples, and the former generic coordinate
surface companion becomes a rotatable display of actual function errors.
Every other spatial binding is preserved.

## Exact tails rather than finite-sample inference

The convention includes the first tail term: all n≥N must satisfy the strict
inequality. The GUI uses ε=e/100 with integer e=1…200 and N=1…120. Its drawings
show only n=1…160; they do not prove an infinite statement. Proofs apply the
stated inequalities to all future indices, including arbitrary positive ε
outside the finite GUI grid where the formula is given.

| Example | Full-tail argument |
| --- | --- |
| 1/n, 1−1/n, 1+1/n and (−1)ⁿ/n | Absolute error is1/n≤1/N, attained atN. Strict containment requires Nε>1. N=floor(1/ε)+1 suffices. |
| 2⁻ⁿ | Error≤2⁻ᴺ, attained atN. The strict condition2ᴺε>1 is certified by integer cross-products for the displayed rational tolerance. |
| (−1)ⁿ | Every tail contains constant even/odd subsequences with limits+1/−1. Their distinct limits rule out convergence to anyL. One wide band around0 can contain every term without establishing convergence. |
| Decimal rationals approaching√2 | For d=10ⁿ, k=floor(√2d) is certified by k²<2d²<(k+1)². Every term k/d is rational; the only real limit is irrational√2. For all m,n≥N, the pairwise difference is strictly below√2−a_N<10⁻ᴺ. Thus the sequence is Cauchy and has no rational limit. |

The set{1−1/n} has supremum1 without attaining a maximum. These bounds are
distinct from the convergence of an infinite series: no conclusion about
Σ1/n is inferred from its terms tending to zero.

For the rational example, integer arithmetic certifies the decimal bracket
and the exact ε decision. Its numerical error is evaluated by rationalization:

    √2 − k/d = (2d² − k²) / [d²(√2 + k/d)].

The residual integer stays positive. Sequential scaling avoids overflow, and
the denominator uses rounded floating arithmetic only for the displayed error.
This avoids a false zero from subtracting two rounded coincident values.
Exact decimal strings remain available. Plotting a point at the same rounded
coordinate as√2 never makes that rational number equal to√2.

## Pointwise versus uniform convergence

On[0,1], x/n converges uniformly to0. The error supremum1/n is attained atx=1,
so its complete tail obeys the strict band exactly when Nε>1.

For xⁿ, the pointwise limit is0 at every fixedx<1 and1 atx=1. For every finite
n, the absolute error has supremum1, **not attained**. Actual error atx=1 is0.
When0<ε<1, x_n=((ε+1)/2)^(1/n)<1 gives error(ε+1)/2>ε for any chosen n≥N.
Taking ε=0.5 disproves uniform convergence for everyN. Atε=1 every actual
point still has error<ε; passing this single band does not imply uniform
convergence. A supremum equal toε is therefore treated differently according
to whether it is attained.

Adaptive samples resolve the thin x≈1 boundary layer. The pre-endpoint error
curve is not connected to the isolated actual endpoint value0. Open markers
denote excluded limiting values/suprema; filled markers denote actual data.
The scalar sequence is drawn with discrete dots, integer index ticks and a
highlighted first tail term. Its error panel uses an explicitly labelled
logarithmic axis and preserves positive tiny errors in scientific notation.

The 3D companion shows eight separate error curves for integer indicesN…N+7.
X is inputx, Y is absolute error, and the offset index axis is labelled with
actualn. No surface or noninteger data is invented between curves. The gold
plane is the strict ε boundary. Powers retain open supremum markers and
separate filled actual endpoint values. Camera rotation changes projection,
not the mathematical coordinates. This finite geometry is an illustration;
the analytic all-tail statement remains the proof.

Definitions and the distinction between pointwise/uniform and Cauchy
convergence are referenced to [MIT 18.100B lecture notes](https://ocw.mit.edu/courses/18-100b-real-analysis-spring-2025/pages/lecture-notes/).
Code, numerical cases and artwork are original; no course figure is copied.

## Verification and remaining scope

The direct-module checker verifies168,000 tail decisions,8,400 independently
evaluated function values,49 mounted states and18 3D family states. It checks
strict equalities, the x=1 exception, positive errors, counterexample witnesses,
rational brackets, exact decimals, actual SVG coordinates, control disabling,
presets/reset/enlargement and every sampled 3D error coordinate. Independent
Python Decimal arithmetic at210-digit precision checks all160 decimal
approximants and their numerical positive errors.

Actual local lesson review at1440 and390 CSS pixels checks56 scalar states and
8 3D control extrema per viewport, including strict-boundary examples,
logarithmic labels, rationalN=120, marker attainment, SVG text bounds,
no body overflow, scrolling enlargement and keyboard camera reset. The
original continuity model remains. API bindings and served source hashes
are checked independently; read-aloud is checked for exact visible numeric
and proof content without relying on audible voice availability.

This covers the named reciprocal/geometric/shifted/oscillating sequence
examples, bounded subsequences, the supremum example, rational Cauchy
incompleteness and a pointwise/nonuniform continuous-function counterexample.
It does not represent every sequence/function, construct the reals, prove
all convergence theorems, or complete the lesson's series, intermediate-value
or differentiability/squeeze examples. All59 mathematics lessons,39 physics
lessons and the full radiology requirement remain subject to the complete
thread objective. No whole-goal completion is claimed.
