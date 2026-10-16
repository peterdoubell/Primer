# Triangle-solving fidelity review

The existing trigonometry concept lab retains its unit circle and now includes a triangle solver. Supported measurements are SSS (a,b,c), SAS (b,c,A), ASA (A,B,c), and SSA (a,b,A). Labels follow opposite-side conventions. Each accepted solution includes all sides, angles, area and a Cartesian triangle, rendered with equal horizontal/vertical scale. Two SSA solutions share the same scale. Reflections are congruent and counted once.

The solver rejects nonfinite, blank, out-of-range, impossible and degenerate inputs. Length inputs are 0.1–1000 common units and angle inputs are 0.1–179.9 degrees. These are input limits; calculated sides may extend beyond them. Results use binary floating-point arithmetic; displayed values use six significant digits. Tangency uses an eight-machine-epsilon comparison of the dimensionless sine ratio. Extremely near-degenerate distinctions below floating-point resolution are not represented exactly.

Equations and ambiguity convention were checked against the primary textbook sources:
- https://openstax.org/books/precalculus/pages/8-1-non-right-triangles-law-of-sines
- https://openstax.org/books/precalculus/pages/8-2-non-right-triangles-law-of-cosines

`node tools/verify_triangle_fidelity.cjs` verifies 52,982 solutions against Cartesian side distances, all three cosine identities, angle sums, positive areas and preservation of input measurements. It includes explicit impossible, tangent and two-solution SSA fixtures and invalid-input checks. The triangle coordinates are derived from area/angle; the distance checks independently recover all three side lengths from those coordinates.

`NODE_PATH=<Playwright installation> node tools/check_triangle_browser.cjs` mounts the actual concept-lab renderer and exercises six presets at 390px and 1440px. It checks solution counts, invalid-input clearing, no horizontal document overflow and no page errors. Screenshots record the two-solution SSA example. This is standalone browser evidence: authenticated lesson delivery and production deployment have not yet been verified for this change.

This review establishes the scoped triangle feature only. It does not establish complete math/physics coverage or clinical completeness of radiology modules.
