# Four linked algebra lessons

Linear Equations, Slope and Lines, Quadratic Equations and Polynomials now have exact calculation workbenches with linked coordinate graphs and 3D charts. The earlier controls could not reproduce the existing figures: variables on both sides, the vertex (5/2,−1/4), and the given cubic root 3 were outside their input models. Three spatial companions displayed unrelated two-variable surfaces. This change replaces those activities and companions. All 40 original quiz items, prerequisites, practice identifiers and four illustration descriptors remain unchanged.

## Mathematical scope

The core accepts finite integer, decimal and fraction inputs with magnitude at most 1000 and reduced denominator at most 1000. Rational operations use BigInt internally and reject unsafe intermediates rather than clamping. Inputs and exact outputs are kept separate from approximate irrational root locations. Invalid drafts preserve accepted calculations, speech and both views.

Linear equations allow outside factors, parentheses and x terms on both sides. Equivalent stages preserve the solution set, including no-solution and identity classifications. A proposed x is checked in the original equation. The parameter identity for the right constant supports symbolic rearrangement such as F=9C/5+32.

Lines can start from two distinct points, a slope and point, or Ax+By=C. Intercepts, evaluation at a chosen x and parallel/perpendicular constructions are exact. Vertical evaluation distinguishes no y from every y. Degenerate general equations describe no points or every point; coincident input points do not determine a unique line. Application contexts retain units and physical domains, including the finite draining interval.

Quadratics retain fractional vertices, completed-square form, discriminants, stable approximate coordinates for irrational roots, exact radical expressions, multiplicity, and Vieta identities. A=0 is classified as a lower-degree relation without invoking the quadratic formula. Real-axis crossings are not inferred from complex-root identities. Projectile and rectangle examples distinguish algebraic roots from physical choices.

Polynomial input degrees are at most four, so multiplication can produce degree eight. Expansion from given roots is distinct from coefficient-driven factoring, which is explicitly limited to quadratic or lower degree. Division preserves the exact identity P=DQ+R, with R zero or lower degree than D. For a linear divisor, the root is derived from its coefficients and P(r)=R is evaluated exactly, shown in the ledger and marked on the dividend/divisor graphs.

## Coordinate fidelity and interaction

Both views share the same accepted algebra and numerical chart window. The chart lies in z=0, with one gain for x and y. It does not add a third algebra variable. Camera motion preserves the state; the explicitly named Reset model resets both views. Oblique projection can change apparent angles, so perpendicularity should be judged in the equal-scale 2D graph or exact equations.

Curves use exact rational Bernstein hulls for interval exclusion and certified error bounds against the actual drawn chords. Uncertain boundary intervals are refined; unresolved coordinate-precision contacts are reported rather than falsely classified outside. Line clipping uses exact rational frame intersections, and round caps retain closed-window point contacts. All exact point values remain in the table, including rational line intersections.

An overview is complemented by point-centred windows with numerical coordinate half-widths from 1e−12 to 1e12. Unrepresentable windows are explicitly rejected. Narrow views use numerical centres and offset ticks; common powers of ten keep tick numbers readable and distinct. Changing algebra resets the overview. The default phone graph fits its container; enlargement and exact-value tables support keyboard scrolling. Accepted edits retain focus, and invalid algebra or radius drafts preserve the accepted state.

## Evidence and boundaries

- `initial-scope.json` preserves the four original nodes and bindings at main e2d2003.
- `core-self-check.json` records the implementation author's numerical/property checks; it is not labelled independent.
- `independent-core-proof.json` comes from the separate Python Fraction/70-digit Decimal oracle in `tools/check_algebra_functions_independent.py`, covering 17,706 models, including all 9,823 input tuples of the three unchanged procedural practice generators, unsafe/invalid input rejections, constructed polynomial division identities and root calculations. The executable prints results without rewriting evidence.
- `geometry-implementation-check.json`, `geometry-algorithm.md` and the geometry browser records cover exact chord bounds, interval partitions, source-coordinate mapping and actual projected geometry. These are implementation checks, separately reviewed.
- `independent-review/` records another agent's independent rational samples, analytic quadratic error maxima and real-browser edge cases. The review found and led to fixes for restricted display scales, false boundary clipping, rounded exact coordinates, stage labels, focus loss and corner contacts. It explicitly excludes review of that agent's own arithmetic core.
- `reader/proof.json` is the authenticated synthetic lesson reader, at age 15 and widths 390/1440. It binds exact source hashes, preserves the original figures/assessments, and checks 116 states, shared algebra/window state, actual SVG coordinates, exact point tables, distinct scaled ticks, annotation containment, failed-draft recovery, keyboard access and camera/reset behavior. Production learner data is not changed by this test.

These checks establish the bounded implementations described here. They do not claim every mathematics or physics lesson is complete, nor any radiology clinical approval. The whole-Primer goal remains active.
