# Numerical analysis: exact references and rounded calculations

The `math.5.numerical` lesson's original cubic bisection/Newton-cycle activity
and root-method plate remain. Six new examples address the actual quiz's
rounding, cancellation, conditioning, square-root steps, trapezoid rule and
fixed-point behavior. Its generic coordinate-surface companion is replaced by
a 3D matrix-scaling example. No other module binding changes.

The quadratic quiz previously overstated the loss for B=200 in binary64 and
misidentified the discriminant square root as approximately 100. The corrected
wording identifies the subtraction of √(B²−4) from B and distinguishes partial
accuracy loss at200 from complete cancellation at larger coefficients. The
0.1 explanation now acknowledges that a computation can return exactly 1
without making its stored input exactly 1/10.

## Exact error accounts

The arithmetic examples use actual JavaScript binary64 operations or round
each stated operation with `Math.fround` for binary32. DataView decoding
converts each finite result to its exact dyadic rational. The sum of stored
inputs, the decimal target and arithmetic roundoff are distinct references.
Naive and compensated accumulation are both shown. For ten terms in binary64,
compensation reaches exactly 1 while input bias and arithmetic rounding cancel;
the activity does not attribute zero error to the input representation.

For x²−Bx+1=0, B=2·10ᵏ with integer k=1…16. Integer polynomial signs enclose
the original small root between adjacent 192-bit dyadic endpoints. This
reference is independent of the computed quadratic formula. Both naive and
reciprocal-of-large-root estimates are compared with that original problem,
including coefficient rounding in binary32. Exact residuals remain visible.
The selected displayed decimal error bounds round outward through integer
floor/ceiling operations; they cannot collapse into a falsely certified point
interval. The precise rational certificates remain available. Roots are
irrational in this family, so a binary estimate is never claimed equal to the
true root. The dangerous subtraction can return0 although the true root is
positive and well conditioned with respect to B.

The conditioning example is an exact nearby-data problem:
A=diag(1,η), b=(1,η), x=(1,1), and b̃=(1,η+δ). Therefore x̃₂=1+δ/η.
η=10⁻ᑫ stays strictly positive. The 2-norm condition number is1/η; relative
input, forward and bound values use their explicit formulas. This demonstrates
how a small RHS/backward perturbation can cause a large forward change; it is
not a measured backward-stability claim about a floating-point solver. The
precision selector is disabled for this analytical example. Exact solution
fractions prevent tiny changes from being mistaken for equality merely
because their rounded display coordinates coincide.

For √2, the selected format rounds Newton's `(x+2/x)/2` steps. Exact integer
sign tests keep bisection's dyadic bracket. The last tested midpoint differs
from the midpoint of the new bracket: at step2 those are1.25 and1.375. The new
midpoint radius is2⁻⁽ⁿ⁺¹⁾. A separate integer enclosure for √2 provides actual
nonzero Newton error even after floating-point stagnation. Displayed Newton
error bounds round outward. Near-root quadratic convergence is illustrated
up to the arithmetic limit; no general starting-value convergence guarantee
is inferred.

The trapezoid example integrates x² on[0,2]. Independent real-arithmetic
geometry has exact T_N=8/3+4/(3N²). The actual computation separately rounds h,
coordinates, squares, weights, accumulation and final multiplication. Its
exact rational total error equals mathematical discretization plus arithmetic
rounding. The drawing represents the mathematical trapezoids, not the
separately rounded sample grid. Positive discretization falls fourfold when
N doubles; arbitrary roundoff is not assigned that law.

For g(x)=1+a(x−1), rational multiplication gives exact e_n=aⁿe_0. Controls
include contraction, alternating growth, a=−1 cycles, a=1 fixed values, a=0
one-step convergence and an initially exact fixed point. The precision selector
is disabled because this example is exact. It illustrates the quiz's local
slope issue without treating an affine model as a global nonlinear theorem.

Log-error displays use a separate explicit exact-zero lane; no logarithm of0
or arbitrary positive floor is invented. Integer-index connections are visual
guides. Axis units, scale changes, selected arithmetic and source limitations
are explicit; rounded graphics never replace the rational/integer proof.

## 3D transformation

Two dimensionless cubes compare the input with the image under diag(1,η,1).
Translations−1.5/+1.5 separate their display positions; the map applies after
subtracting the center. Every source corner and face is retained in its scaled
counterpart. The extra identity z direction embeds the 2D lesson problem
without changing κ₂. Tiny positive thickness is retained, with no visual
minimum or fabricated singularity. At screen resolution it can look flat;
world-coordinate positivity and the exact matrix formula remain distinct.
The readout uses the same nearby-data calculation. Rotation changes projection.

The definitions draw on [Goldberg's floating-point paper](https://docs.oracle.com/cd/E19957-01/816-2464/ncg_goldberg.html),
[MIT conditioning/stability notes](https://ocw.mit.edu/courses/18-335j-introduction-to-numerical-methods-spring-2019/pages/week-2/)
and [OpenStax numerical integration](https://openstax.org/books/calculus-volume-2/pages/3-6-numerical-integration).
The calculations and artwork are original, with no copied source figure.

## Verification and remaining scope

The Node checker covers 4,295 states, 32 actual mounted coordinate/error states
and 68 3D maps. Python uses 210-digit Decimal roots independently of the
implementation certificate, Fraction error accounts and separate IEEE
operation emulation. It verifies every original quadratic coefficient/format,
all 64 trapezoid counts in both formats and selected accumulation boundaries.
Bit decoding also covers finite IEEE extrema. Backend bindings reject
cross-lesson scenarios and extra properties; the original activity remains.

Actual local lesson checks at 1440 and 390 pixels exercise 41 numerical states
and 6 additional 3D extrema per viewport, including exact zero, cancellation,
fixed-point boundaries, resetting, enlargement, text bounds and no body
overflow. API bindings, served hashes and numeric read-aloud receive separate
checks. These local checks are not authenticated production UI verification.

The named examples materially improve the lesson's requested error analysis.
General matrix solvers, every nonlinear problem, general quadrature/error
estimators and the entire 59-lesson mathematics curriculum remain outside this
finite activity. The full mathematics, physics and radiology goal stays active.
