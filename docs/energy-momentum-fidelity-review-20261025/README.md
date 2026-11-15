# Work, energy and momentum: fidelity review

The actual `phys.3.energy-work` reader now replaces its fixed equal-mass percentage ledger with four interactive, dimensioned mechanics stations. Existing assessment questions and original illustration are preserved. Six learning outcomes and a worked example connect the artifact to the lesson.

## Physical representations

- **Collisions:** independently adjustable masses, signed velocities, restitution, observer velocity and elapsed time. Finite 0.60 m cart bodies start with a 2.00 m gap. Contact is an instantaneous event only when the left cart catches the right cart. Actual positions and a centre-of-mass trace are calibrated in metres. Signed momentum and kinetic/internal energy are accounted for before and after contact. A centre-of-mass-frame control preserves the same physical collision.
- **Impulse:** a prescribed triangular net-force pulse has the required impulse `m(v_final−v_initial)`. Its time integral determines the changing velocity. Duration controls change average and peak force at fixed impulse. This does not claim to solve contact deformation or predict injury/damage.
- **Work and gravity:** a mass follows exact constant-acceleration trajectory pieces on a straight slope. The model solves zero-velocity events, static holding and reversal explicitly. Frictional internal energy depends on total distance, while gravitational and applied work depend on signed displacement. Horizontal and vertical geometry uses the same metres-per-pixel scale. Static and kinetic friction deliberately share one coefficient. Vertical slopes have exactly zero normal force.
- **Power:** constant power times elapsed time determines input energy, partitioned into declared useful and other transfers. No energy is silently discarded; the adjustable efficiency is hypothetical.

The controls include the lesson’s 250 kg crane lifted 8 m at steady speed (20,000 J applied work) and 1500 kg car at 20 m/s (300,000 J kinetic energy), as well as the 100 J descent, stationary 50 N push, sticking collision, stopping-duration comparison and 60 W / 5 minute energy account.

## Verification

Final mechanics source SHA-256: `2436b6bd01fdad03f1e7616736656882e4d2057d692971fa5b46f55e4efcae03`.

`independent-oracle.json` records 1,466 checked states: 729 collision cases, 405 impulse cases, 305 work/friction cases and 27 power cases. The independent Python checker solves collision constraints with rational arithmetic, integrates the separately defined force pulse by quadrature, and uses a small-step Newton-law integrator with zero-velocity splitting for the work trajectories. It checks 11,478 trajectory/geometry values. Energy-cancellation residuals are checked against 64 ulps of the largest contributing energy term; this avoids judging cancellation of large energies against an artificially tiny zero-based scale. The model retains the raw rounding residual in its ledger.

`reader/proof.json` records 154 actual authenticated reader states and 49,316 rendered-coordinate checks at 390 and 1440 CSS pixels. It verifies protected unauthenticated assets/API, exact served source files, lesson API data, every plot coordinate, physical cart widths, equal slope scales, mode/preset changes, numeric extremes, invalid-draft recovery, centre-of-mass selection, reset, keyboard scrolling in enlarged diagrams, full model speech, and absence of page/CSP errors or external requests. A synthetic database and profile isolate these checks from learner data. The `*-panel-*.png` files provide centred, unobscured plot captures; tall whole-element captures can include the application’s sticky header.

All three `tests/test_energy_momentum_lab.py` tests passed after the final source changes. Independent review by the mathematics agent found no actionable issue in the collision, impulse, friction, frame transformation or diagram mapping; its original review is recorded in the task conversation. The subsequent crane/car parameter-range expansion passed the same numerical and browser checks.

## Limits and remaining scope

The reader does not simulate a deformable collision, rotational impacts, actual egg failure, a launch/recoil energy-release event, or a full pendulum trajectory. It represents the conservation principles behind those contexts and states the distinction. The existing advanced-classical pendulum activity is separate; this release does not claim complete illustration of every mechanics application. The plots represent declared idealized physical models, not measured experiments or photorealistic scenes. No production verification is implied by the local reader proof, and neither all physics nor the full Primer goal is complete.

## Sources

Original diagrams and implementation use the physical laws explained in OpenStax University Physics Volume 1: [Impulse and Collisions](https://openstax.org/books/university-physics-volume-1/pages/9-2-impulse-and-collisions), [Types of Collisions](https://openstax.org/books/university-physics-volume-1/pages/9-4-types-of-collisions), and [Work–Energy Theorem](https://openstax.org/books/university-physics-volume-1/pages/7-3-work-energy-theorem). These primary textbook pages were accessed on 2026-10-25. No source figures or photos were copied.
