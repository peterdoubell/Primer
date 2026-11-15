# Independent fluids review

This review checks the authored `phys.4.fluids` quiz and the declared idealized
workbench models. It does not certify all external readings, a complete fluid
mechanics course, real engineering predictions, resolved turbulence, or whole
Primer media coverage. Source facts and equations informed original calculations;
no source artwork or substantial source prose was copied.

Run from the repository root with Python containing NumPy and SciPy, and Node:

```sh
python tools/check_fluids_independent.py
node tools/check_fluids_independent.cjs --browser
```

The browser command also needs Playwright resolvable by Node. This environment
uses `NODE_PATH=/Users/peter/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules`.
Use the repository scientific environment or install the pinned scientific
dependencies already listed in `tools/requirements-anatomy-source-checks.txt`.
Neither command overwrites proofs by default. To regenerate the fixed receipts
and screenshots in this directory, add `--write-proof`, running Python first.
The CJS numerical transport accepts bounded numerical requests on stdin and
reads only the fixed repository module. It accepts no arbitrary file paths.

`numerical-review.json` records the exact module and checker hashes. Its checks
use independently constructed numerical methods:

- Pressure and force integrals reconstruct hydrostatic traces, hull capacity and
  opposing side loads; piston work integrates force over displaced distance.
  Retained fluid uses the surrounding-fluid density and cannot exceed the whole
  box volume; that necessary upper bound does not prove real interior capacity.
- Annular section flux and energy conservation check the maintained-flow
  continuity companion, including the exact quiz state of 2 and 8 m/s with a
  30 kPa drop. The original Venturi renderer remains byte-identical.
- A singular collocation boundary-value problem solves the radial momentum
  equation. Annular integration checks flux, shear, kinetic-energy correction
  and positive viscous dissipation for either flow direction.
- Two refined collocation boundary-value problems on eta domains 14 and 18
  check the Blasius solution independently of the product's RK4 shooting.
  `renderer-oracles.json` contains the finer solution for SVG verification.
- Adaptive force-ODE integration checks rising, falling and neutral particles.
  A 60-digit oracle checks very early displacement without cancellation.
- A complex-potential derivative and adaptive contour integration check the
  Joukowski geometry, velocity, pressure force, circulation sign and Kutta cusp.
  The deliberately coarse 128-sample thin-foil case has a small documented
  quadrature residual. Refinement to 256 and the default 720 resolves it.
- Independent plume power-law invariants test the normalized scaling without
  pretending to solve entrainment, eddies or transition onset.

`renderer-review.json` checks a real standalone browser mount at 390 and 1440 px.
It decodes the actual SVG coordinates back to physical units; it does not merely
count elements or compare the renderer's own readout with its own API. Checks
include circle-derived cylinder diameters, piston travel, submerged hull draft,
equal geometry scales, every profile point, pressure-traction directions and
control values. The separately recorded authenticated reader proof establishes
main-app mounting and delivery. This standalone audit does not claim that scope.

`teaching-review.json` records the four wording corrections and the resolved
stale-keyword scoring defect. Their original prose and changes remain in the
parent `teaching-corrections.json`. `original-venturi-preservation.json` pins the
retained original renderer body so the exact-quiz companion can be added without
rewriting that reviewed scene.

`requirements-disposition.json` maps all ten authored quiz items to the nine
concept groups and records the physics still excluded from these activities.
`final-review.json` pins the final reviewed source and receipts and identifies
the corrected findings. Counts describe executed checks, not module coverage.

Primary references for the mathematical conventions are the
[DOE fluid-flow handbook](https://www.energy.gov/sites/default/files/2026-04/DOE-HDBK-1012-92_VOL3.pdf),
[MIT Blasius lecture](https://web.mit.edu/13.021/demos/lectures/lecture16.pdf),
[Kerwin's MIT foil notes](https://ocw.mit.edu/courses/2-23-hydrofoils-and-propellers-spring-2007/6f698ed019180565602e04d6a7a71856_kerwin_notes.pdf),
[the primary unsteady-settling paper](https://arxiv.org/html/2408.12530v2), and
[the primary plume study](https://doi.org/10.1038/s41467-021-22159-3).
The settling review distinguishes memoryless particle inertia from added-mass
and history-force dynamics; low particle Reynolds number alone does not justify
the exponential transient. The plume study is used only for far-field scaling.

OpenStax's current license was observed to be CC BY-NC-SA in the source audit;
this package does not reuse its prose or images. Physical facts are checked by
the original calculations above. Sources do not themselves constitute approval
of this implementation.
