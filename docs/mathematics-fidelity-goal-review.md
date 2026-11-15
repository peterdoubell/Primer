# Mathematics representation fidelity review

Date: 2026-10-09. This is an implementation audit against the expanded visual
goal, with a verified improvement to second-order differential equations. It is
not a declaration that all mathematical topics are adequately represented.

## What the existing inventory proves

`data/curriculum/01-mathematics.json` has 59 lessons. Before the second-order
addition, each has an illustration and a lesson interaction. The earlier
`mathematics-illustration-review.md` records an 800px content pass for all 59,
and expressly excludes renewed model and 1600px verification. Those findings
should be preserved; another presence count cannot extend their scope.

`data/module-models.json` also has 59 mathematics bindings. Eighteen explicitly
use `mode: context`; the others often reuse unit blocks, a lattice, a surface
or an urn. These are inspectable objects, but their presence does not demonstrate
the lesson's theorem or cover every mathematical object named by its goal.
In particular, an arbitrary real surface does not represent every higher
mathematical subject to which that family is attached. The authored concept
models are the stronger evidence for the individual examples they actually
calculate. Neither kind of binding supplies a curriculum-wide completeness
claim.

## Concrete coverage gaps inspected

| Lesson | Present representation | Remaining named topic needing representation |
| --- | --- | --- |
| Differential equations (`math.4.diffeq`) | Logistic direction-field plate; exact first-order decay compared with Euler steps | The goal and quiz also teach second-order equations, oscillation and repeated roots. The added activity below supplies a coherent unforced second-order example. Forcing and broader second-order equations remain outside it. |
| Multivariable calculus (`math.4.multivar`) | Saddle and gradient plate; an exact tangent-plane example on a bowl in `spatial-math.js` | Multiple integrals and vector calculus are named in the goal but are not represented by these two examples. An integration region, integral accumulation and a field/flux example remain necessary. |
| Linear algebra (`math.4.linalg`) | Determinant/area-collapse plate; selectable plane transformations | Eigenvalues and vector spaces are named in the goal. The current illustrated transformations do not expose eigenvectors, invariant directions or a basis/subspace construction. |
| Probability theory (`math.4.prob-theory`) | Law-of-large-numbers plate; binomial probability distribution interaction | The interaction is a distribution calculation, not a law-of-large-numbers exploration. A statistically valid sample-mean/concentration comparison would support the named limiting behaviour. |
| Real analysis (`math.4.analysis`) | Epsilon–delta plate and an exact whole-neighbourhood bound for x² | Convergence is named in the goal; no sequence-tail/N versus epsilon exploration is provided by this local continuity model. |
| Numerical analysis (`math.5.numerical`) | Root-method plate; certified bisection bracket versus Newton convergence/cycling | Root finding is represented. Floating-point error, conditioning and propagation of error bars are not exposed by that example, and need separate demonstrations for the wider goal. |
| Partial differential equations (`math.5.pde`) | Heat/diffusion plate and a stable insulated discrete-heat interaction | Waves are named in the goal but are not represented by a heat stencil. A wave field must distinguish propagation and its initial/boundary conditions from diffusive smoothing. |

These are observed gaps, not an exhaustive list of all missing examples across
59 lessons. A complete pass must also inspect all early/middle lesson goals,
every retained raster resolution, plot labels, mathematical boundary states,
controls, mobile displays and keyboard behaviour. A correct worked example is
not proof that the entire lesson's visual scope has been met.

## Added second-order activity

`web/math-ode-lab.js` implements the homogeneous equation

    x″ + 2ζω₀x′ + ω₀²x = 0

with independent initial displacement and initial velocity. It covers undamped,
underdamped, critical and overdamped regimes; displays characteristic roots and
the matching solution form; and links displacement/time, position/velocity and
energy plots to the inspected time. The repeated-root case uses both independent
solutions, exp(−ω₀t) and t exp(−ω₀t). Small parameters near critical damping
are retained rather than rounded into the repeated-root case. The solution
evaluation uses analytic formulas with the removable sine/sinh quotients
handled continuously at zero.

All axes carry units. Energy is per unit mass; the plotted energy fraction is
only normalized when initial energy is nonzero. The equilibrium state has a
dedicated zero-energy path. Tiny positive energy is kept in scientific notation
instead of displayed as exact zero. A phase arrow encodes direction, not speed.
The plots are sampled at 0.02 s, while the inspected values are computed from
the analytic solution. The user-facing note states finite sampling, the absence
of forcing/nonlinear behaviour, and the fact that non-oscillatory motion may
cross equilibrium with a suitable initial velocity.

The source for the mathematical families is [OpenStax Calculus Volume 3,
section 7.3](https://openstax.org/books/calculus-volume-3/pages/7-3-applications).
The activity's code and SVG artwork are original; no textbook figure is copied.

## Verification and limits

`tools/check_math_ode_lab.js` compares 432 analytic states against an independent
fourth-order Runge–Kutta solver for the first-order system. It separately checks
initial conditions, derivatives, the differential equation, energy dissipation,
undamped energy conservation and energy monotonicity over the finite window.
The cases include zero state, changing signs, extreme controls and values within
1e−10 of critical damping. Known sine and repeated-root solutions are checked
directly. Fifteen mounted control states, four regime presets, time preservation,
equilibrium, enlarge behaviour and resets are exercised through the actual
renderer. `tests/test_math_ode_lab.py` runs that checker in the test suite.

Browser review at desktop width and 390px inspected actual graph renderings,
labelled controls, keyboard time-scrubbing and internal scrolling when enlarged.
An initial narrow-screen label issue was corrected by using a 440px SVG viewBox
and a separate 660px enlarged view. Energy tick labels were simplified to quarter
fractions. The rendered phone page stays within its 390px viewport; enlarged
plots scroll inside their own containers. Screenshots are local review artefacts,
not an anatomical or whole-curriculum certification.

This improves one concrete coverage gap. The full mathematics goal remains open.
