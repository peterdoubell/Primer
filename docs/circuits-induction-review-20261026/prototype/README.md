# Circuits and induction prototype

This isolated prototype advances `phys.2.electricity` and `phys.3.em` without changing the frozen Primer release. `scope.json` maps all 20 current assessment questions to the supplied models or explicit remaining work. The full 39-module physics goal remains unchanged and incomplete.

## Implemented workbench

DC networks include one load, series, parallel, a series/parallel combination and a five-resistor bridge. Three independently oriented ideal cells drive editable resistors, open branches or ideal shorts. The solver reports every branch voltage/current/power, node potential, equivalent resistance, source power and individual cell power. Open circuits and floating potentials retain their distinction. Ideal wire-loop currents are not assigned an arbitrary split. A nonzero ideal source across a short has no finite solution; a zero-volt source loop has an undetermined circulating current while known zero voltage drops and resistor powers remain available.

Cell emfs are summed with scaled integer decimal coefficients before conversion to the solver's number representation. Consequently `0.1+0.2−0.3` is exactly zero, while `1+10⁻¹⁷−1` remains nonzero. No epsilon threshold changes one classification into another. These are canonical decimal values represented by the accepted numeric inputs; original strings beyond numeric precision are not retained.

The induction model uses a dimensioned circular coil in a prescribed uniform field `B=B₀+B₁ sin(2πft+φ)` and normal angle `θ=θ₀+Ωt`. External linked flux is `λ=Nπr²B cosθ`; emf is its negative time derivative. The R–L response is analytic harmonic forcing plus the exact homogeneous term enforcing `i(0)=0`. The `L=0` branch is the resistive quasistatic response, including its actual nonzero current derivative. Self-inductance appears once in `L di/dt+Ri=emf`. Torque `N i A n×B`, imposed motor power, changing-field power, resistive dissipation and self-field energy close their instantaneous power balance.

The coil is an actual 3D circle projected with an orthonormal camera basis. Its physical scale is labelled, as are the positive loop orientation and normal. Circuit diagrams show connectivity and numerical meters; they do not animate invented charge speeds. The plots have physical axes. High-frequency forcing is sampled at 128 segments per fastest cycle; startup receives additional points every 0.025 time constants through 24 time constants. A separate first 12-time-constant view exposes rapid current rise instead of hiding it on a 5-second axis. The selected readout is retained and explicitly described if it lies outside the selected plot window.

## Evidence

Core SHA-256: `5901c05cb0dab089457fc8b8bd642c2736de4ef6ce88b1ae07f9aebe05ebc8d3`.

- `numerical-proof.json`: **1,392 DC states** checked against an independent exact-rational modified-nodal/RREF oracle, including inconsistent equations, free currents and floating potentials; **203 induction states** checked against independent exponential-convolution quadrature of the directly differentiated external flux.
- The fast-transient regression has τ=10 μs and 801 samples through 20τ. Its largest checked midpoint interpolation error is **3.04598e-07 A** (about 0.008% of the characteristic current). The earlier coarse curve had a roughly 50% interpolation error and was corrected before handoff.
- `browser-proof/proof.json`: **240 standalone states** at 390 and 1440 CSS pixels, with **752,898 calibrated coordinate checks**, native controls/presets, exact-decimal short classifications, invalid-input recovery, transient-window selection, out-of-window marker handling, zoom/keyboard scrolling and reset. No page errors or document overflow were observed.
- The desktop/mobile network and startup screenshots were inspected. Diagram labels were moved clear of diagonal wires, and the coil view was enlarged with its physical scale retained.

Cross-review found the decimal-source classification, `L=0` derivative and fast-transient sampling issues; regression cases now cover all three. Final-source re-review passed with no remaining actionable finding in its reviewed scope; `independent-review.json` records the reviewer-reported rational circuit, Gauss–Kronrod current-response, derivative, transient and actual-browser checks. This is a scoped scientific review, not full-module or deployment approval.

## Running and integration

Run `python3 check_independent.py` from this folder (or give its absolute path). Run `check_browser.cjs` with Node and the bundled Playwright dependency path. The browser checker starts and closes its own loopback static server; it writes no learner records. To view manually, serve this directory with an ordinary local static server and open `index.html`.

`integration-contract.json` specifies the required scoped renderer adapter, protected asset loading, exact lesson bindings, current speech/state handling and actual authenticated reader verification. The standalone CSS/bootstrap must not be copied directly into the shared app. No integration, commit or deployment was performed here.

Static charge/polarization/sparks, actual conductor material response, parallel-wire forces, a loaded transformer, and moving-magnet/copper-pipe field dynamics remain absent. The present rotating-coil and changing-uniform-field models are explicitly bounded analogues. This prototype is not a declaration that both modules or physics as a whole are finished.

Physical references: [Kirchhoff’s rules](https://openstax.org/books/university-physics-volume-2/pages/10-3-kirchhoffs-rules), [Faraday’s law](https://openstax.org/books/university-physics-volume-2/pages/13-1-faradays-law), and [RL circuits](https://openstax.org/books/university-physics-volume-2/pages/14-4-rl-circuits), OpenStax University Physics. Original code and diagrams; no source figures were copied.
