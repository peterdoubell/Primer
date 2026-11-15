# Topology lesson: exact finite witnesses and disclosed infinite arguments

Scope: `math.5.topology`, all ten existing assessment rows and its stated goal, “Continuity without distance; the shape of space.” The interactive renderer is `math-topology-lab`, with exactly `{"scenario":"math.5.topology.opens-covers-surfaces"}`. Its seven stations share one bounded normalized state with the companion 3D view through the lesson-specific bus. No expression evaluator, persistent state, metric assumptions in the finite continuity test, or certificate/commercial-readiness claim is introduced.

## Assessment-to-artifact contract

| Row | Requirement | Active witness / argument |
|---|---|---|
| 1 | Two handles survive a homeomorphism | T6 actual genus 0–3 closed orientable meshes; genus chooses another object, while positive stretch and affine shear deform the chosen mesh. The curriculum must refer to the closed boundary of a handlebody, rather than ambiguously identify the clay solid itself with a surface. |
| 2 | A figure-eight crossing survives homeomorphic stretching | T6 one exact shared valence-four vertex, with original/image curves; continuous inverse and positive Jacobian supplied. Lengths and angles can change. |
| 3 | A missing union invalidates a proposed topology | T1 all eight subsets of `{a,b,c}` and all 256 families; assessed family 135 has `{a}∪{b}={a,b}` absent. Valid family 139 demonstrates that complements need not be open. |
| 4 | Compactness of `[0,1]` versus `(0,1)` | T3 infinite cover `(1/n,1)`, explicit finite-selection maximum N and missed point `1/(2N)`; Archimedean choice proves the infinite family covers every interior point. Heine–Borel proves closed-interval compactness. A separate finite cover is marked only an example. |
| 5 | Infinite cofinite real line is T1 but not Hausdorff | T4 finite exclusions with a concrete intersection witness, plus the argument that finite combined exclusions cannot exhaust infinite ℝ. Singleton complements prove T1. The display never substitutes a finite universe. |
| 6 | Continuous compact-to-Hausdorff bijection is a homeomorphism | T7 four dependent proof steps: closed subset compact, continuous image compact, Hausdorff compact subset closed, closed bijection has continuous inverse. T2 supplies exact preimages without distances. |
| 7 | A continuous surjection need not be a homeomorphism | T7 `[0,2π]→S¹` is compact, connected and onto, with endpoints identified and no inverse. Puncturing an interval versus a circle distinguishes their homeomorphism types. |
| 8 | Sine closure is connected but not path-connected | T5 graph and vertical closure segment drawn separately; exact sequence `x_n=1/(arcsin(y)+2πn)` proves each vertical point is in the closure. The IVT alternating-extrema argument obstructs a path. Closed boundedness proves compactness. |
| 9 | Genus-three Euler characteristic equals −4 | T6 V−E+F is computed from actual indexed triangles and unique edges; every edge has two opposite orientations and every vertex link is one circle. Counts agree with `2−2g`, including g=3. |
| 10 | Continuous bijection with a discontinuous inverse; repair hypothesis | T7 `[0,2π)→S¹` and explicit near-seam sequence: circle chord distance→0 while inverse parameter→2π rather than 0. Compact endpoint quotient produces a true homeomorphism; the angle coordinate still jumps at the seam. |

## Computation and geometric fidelity

T1 encodes a subset by three point-membership bits; subset k contributes `2^k` to the open-family code. It exhausts every distinct subfamily union, including the empty union, and every pairwise intersection. Since the universe is finite, arbitrary indexed unions reduce to these distinct members. Pairwise closure plus the whole set proves finite intersections by induction, including the zero-member intersection. Invalid families retain explicit failed witnesses; complement closure is never required.

T2 checks every open preimage for all 27 functions between each pair of four valid finite topologies. A bijection’s inverse is checked independently by images of domain opens. Discrete-to-indiscrete identity demonstrates why compactness alone is insufficient; finite Hausdorff targets are discrete.

T5 samples uniformly in `u=1/x`, with 48 steps per oscillation, rather than aliasing the graph on a uniform x grid. The omitted window is `0<x<1/(1+2π·cycles)`; no polyline joins it to x=0. The exact sequence, extrema and proof concern the complete set. The finite drawing is itself separated and is explicitly described that way. There are two path components: the graph and the vertical segment.

T6 doubles a connected rectangular planar domain with g disjoint rectangular holes, identifying its g+1 boundary circles. Each retained grid cell becomes a four-triangle fan. Interior upper and lower vertices are separate; boundary vertices are shared. Positive-height fan centers avoid duplicate flat faces, zero-area triangles, and accidental contact between the sheets. The mesh is a piecewise-linear closed embedded surface; every vertex link and edge incidence is checked. The separate CW counts (one vertex, 2g edges and one face for g≥1) are explicitly a different decomposition. The sphere uses one 0-cell and one 2-cell with a constant attaching map.

`F(x,y,z)=(sx+by,y,z)`, `s∈[0.5,2]`, has inverse `((x′−by′)/s,y′,z′)` and determinant s>0. It is affine, so every displayed straight triangle is exactly its image: this avoids substituting chords for a nonlinear deformation. Interpolating from the identity keeps s positive. Changing genus is not presented as deformation, cutting or gluing.

T7 keeps the plotted near-seam coordinates actual; it does not magnify them away from `(1,0)` to manufacture a visible jump. The parameter graph and numeric ledger carry the limit witness. The compact quotient is distinguished from the closed interval surjection and from the half-open bijection.

## Primary mathematical sources

- [UCLA, Romyar Sharifi: continuous functions, Chapter 2](https://www.math.ucla.edu/~sharifi/notes/topology-ch02.html): open-preimage continuity and homeomorphisms.
- [UCLA: connected and compact spaces, Chapter 3](https://www.math.ucla.edu/~sharifi/notes/topology-ch03.html): sine closure, compact images and compact–Hausdorff inverse theorem.
- [UCLA: separation axioms, Chapter 4](https://www.math.ucla.edu/~sharifi/notes/topology-ch04.html): T1 and Hausdorff hypotheses.
- [Cornell Math Explorers: Euler characteristic](https://pi.math.cornell.edu/~mec/Winter2009/Victor/part5.htm) and [orientable surfaces](https://pi.math.cornell.edu/~mec/Winter2009/Victor/part3.htm): triangulation invariant and connected sums.
- [Mathlib’s formal topologist-sine-curve development](https://leanprover-community.github.io/mathlib4_docs/Counterexamples/TopologistsSineCurve.html): independently formalized connected/not-path-connected distinction.

Sources were inspected on 2026-10-11. Runtime prose and proofs are authored for this lesson; no source raster, third-party model or copied lecture text is embedded.

## Verification

`node tools/check_math_topology_lab.js` passes independent set-array oracles for 256 open families (29 topologies), 432 function/topology preimage cases, 237 open/closed-cover cases, 144 infinite cofinite examples, 45 sine-closure parameter cases, 8 complete closed oriented manifold meshes (all vertices and links), 72 affine deformation/inverse cases, 27 circle cases, and 50 mounted control values across all seven stations. The mesh oracle rebuilds incidence from faces, checks distinct/nondegenerate triangles, opposite edge orientations, connectedness and one cyclic link at every vertex. It does not accept runtime counts as the expected topology.

The mounted tests verify scoped hiding/disabled controls, finite in-view SVG coordinates, current full speech, every fixture, numeric draft/blur/Enter/Escape behavior, exact resets/enlarge state, unique title IDs, state propagation, and suppressed peer echoes.

`tests/test_math_topology_lab.py` passes 3 tests: exact lesson/renderer/props scope, shared dependency ordering and scoped CSS, and the independent science/mounted checker. The final standalone Chromium proof and screenshot locations are recorded below. Parent integration must additionally verify the real reader and linked 3D view, as standalone rendering cannot prove their runtime behavior.


Final standalone Chromium QA: `.research/topology-lab-qa-20261011/proof.json` (ignored local reproduction artifact). Both 1440×1000 and 390×844 passed, each with 7 stations, 50 control values, 11 fixtures, 16 numeric draft/blur checks, 16 Enter/Escape pairs, 18 full current speech checks and exact reset/enlarge behavior. Fourteen station screenshots were inspected visually; SVG labels did not clip or overlap, visible inputs met 44px touch targets, no page/card overflow occurred and page errors were empty. The QA-only speech stub uses the native-size icon button. The harness closed its own temporary HTTP server and headless browser. This verifies standalone lab rendering, not production authentication or reader/3D integration.

Loaded and local source SHA-256 agreed:

| File | SHA-256 |
|---|---|
| `styles.css` | `b2bd335332cb0c2fbad671d9542000c544603817acbd29f55683b120f9cd3660` |
| `math-topology-lab.css` | `32496e4d39f42456e65fc696de5af12a394f545ba1a7e0ff8075635464f9c30b` |
| `lesson-state.js` | `662b5874d0677c9dbf7e4d283a7c23ee0971aa5b3e74b5e183bf93096a094727` |
| `math-topology-lab.js` | `5788e7c53dcbb8d36b8157fc8d8a034fef6ab7415e1c5059be52244492b5e2ed` |

Final standalone proof SHA-256: `319b4b6ada2c6c0538255bc5f96cb4aa3c95b5dcf96945cdf25469dcb61207a9`.
