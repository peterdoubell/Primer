# Multivariable integral and flux review

Date: 2026-10-09. This adds a concrete multiple-integral and vector-calculus
activity to `math.4.multivar`. The existing tangent-plane model is preserved.
This is verification of two worked polynomial examples, not completion of the
entire mathematics or multivariable-calculus visual goal.

## Explicit mathematical model

`web/math-field-lab.js` uses dimensionless mathematical coordinates and field
values. No measured physical velocity, density or material quantity is implied.

| Integrand | Linked vector field | Divergence |
| --- | --- | --- |
| f(x,y) = x² + 2y | F(x,y) = (x³/3, y²) | ∂P/∂x + ∂Q/∂y = x² + 2y |
| f(x,y) = x + y | F(x,y) = (x²/2, y²/2) | ∂P/∂x + ∂Q/∂y = x + y |

The selected rectangle is Dₚ = [a,b] × [c,dₚ], where b = a + width,
d = c + height and dₚ = c + p(d−c). The accumulation slider p moves the upper
y boundary from c to the final d. Bounds, resolution, sample rule, integration
order, normal orientation and prism-view rotation are controlled independently.
Widths and heights are nonnegative; bounds are not silently reordered.

The double integral is evaluated analytically. The Riemann sum is computed
separately from n² actual cell samples and their areas. Positive and negative
contributions remain separate before being summed. Midpoint and lower-left
samples have distinct error behaviour; changing resolution does not change the
exact integral. The linear example's midpoint rule is exact for every grid in
this family. That special property is not asserted for arbitrary functions.

The flux total is independently calculated from the normal field component on
each of four sides. Counterclockwise traversal is paired with outward normals
to its right; clockwise traversal is paired with inward normals to its right.
The latter changes the sign of the oriented flux and leaves the interior
integral unchanged. The user-facing explanation distinguishes this sign change
from reversing only the parametrization while retaining a fixed physical
outward normal.

For a nondegenerate rectangle, the smooth fields satisfy the two-dimensional
flux form of Green's theorem. Zero width or zero accumulated height collapses
the domain: the zero integral follows from coincident bounds, and the activity
expressly declines to apply the theorem to that collapsed boundary. With zero
final height, the accumulation panel does not manufacture a nonzero y interval.

## What the visualizations encode

The prism view shows each sampled value above or below the zero plane, with
teal positive and coral negative contributions. Prism footprint dimensions and
heights come from the same cells used in the sum. A separate wire surface
samples the actual polynomial, rather than smoothing the Riemann boxes. The
height scale is displayed and separated from the x/y scale. Perspective is not
a reliable way to measure slopes or angles. Rotation uses the existing tested
`PrimerSpatial.rotate` helper without registering an additional generic scene.

The field view uses a common x/y display scale, blue field vectors, gold unit
normals and coral traversal directions. A zero vector is a dot without a
direction. Field vectors share a display multiplier; they are not particle
trajectories. A labelled table records all four exact boundary contributions.

The accumulation curve G(u) is sampled at 81 upper y bounds. The marked value
and the displayed derivative G′(dₚ) use exact formulas. The curve can fall when
newly included values are negative; adding area does not necessarily increase a
signed integral. Both iterated integration orders describe the same rectangle.

## Verification

`tools/check_math_field_lab.js` checks 1,944 rectangle states against independent
two-point Gauss quadrature in each coordinate. That rule exactly integrates
these polynomials in exact arithmetic; floating-point comparisons use stated
tolerances. It separately quadratures 7,776 boundary-side contributions and
checks their normal/traversal directions. The checker verifies cell footprints,
signed contributions, error identities, grid refinement, the accumulation
derivative, order invariance, orientation reversal and degenerate domains.

Twenty-nine mounted control states exercise the actual renderer, its unit-square
preset, reset and enlargement. Actual projected prism vertices are checked
against an independently derived orthographic projection, rather than relying
only on geometry metadata. Rendered field-vector components and boundary
normals are also checked. `tests/test_math_field_lab.py` runs this checker.

Browser review inspected desktop and 390px layouts, keyboard resolution and
accumulation controls, both sample rules, both integration orders, inward
normals, the unit-square preset, zero-area states and internal enlargement.
At 390px, the page remains 390px wide; each enlarged diagram is 660px wide inside
its own 322px scrolling container. The review corrected crowded bound labels,
made the projected x/y labels legible against prisms, and added clear zero-centred
accumulation ticks. Local review screenshots and browser outputs are retained
in the ignored `.research/math-field-preview` directory.

The default quadratic example has exact integral 4/3, midpoint n=4 sum 1.25,
and outward flux 4/3. Its lower-left n=4 sum is −0.5, while n=12 gives about
0.685185; this illustrates finite approximation error rather than changing the
exact answer. At 25% accumulation the exact signed integral and outward flux
are −7/6. The linear unit-square example has exact integral, midpoint sum and
outward flux all equal to 1.

## Scope still open

This artifact does not model arbitrary nonrectangular domains, triangular-limit
rewriting, triple integrals, circulation/curl, arbitrary vector fields or the
three-dimensional divergence theorem. Those topics need their own faithful
representations. A correct two-dimensional worked example does not establish
complete coverage of the lesson or the broader goal.

Primary mathematical references: [OpenStax Calculus Volume 3, double integrals
over rectangles](https://openstax.org/books/calculus-volume-3/pages/5-1-double-integrals-over-rectangular-regions)
and [Green's theorem](https://openstax.org/books/calculus-volume-3/pages/6-4-greens-theorem).
The code and SVG artwork are original; no source illustration is copied.
