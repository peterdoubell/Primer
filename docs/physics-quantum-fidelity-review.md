# Quantum states and measurement fidelity review

Implementation is restricted to `phys.4.quantum` and the exact renderer contract
`physics-quantum-lab` with `{ "scenario": "phys.4.quantum.states-measurement" }`.
The analytic laboratory covers all ten authored quiz requirements through five
bounded stations. Its CommonJS and browser API is `PrimerPhysicsQuantumLab`.
No arbitrary expression evaluation or general Schrödinger PDE solver is used.

| Quiz requirement | Actual station behavior | Independent evidence |
| --- | --- | --- |
| Q1 Born density / approximate local frequency ratio | Hard-wall complex amplitude, unit-integral density, exact regional probability, complete seeded detection positions and histogram counts. Equal small neighborhoods have the assessed approximate ratio. | Direct sine-state integral and quadrature; ratio-two small-neighborhood fixture; aggregated independent seeds. |
| Q2 width doubling reduces ground eigenenergy by four | Width control and electron SI energies; the note distinguishes separately prepared wells, adiabatic ground-state widening and abrupt excitation. | SI energy ratios and all six eigenlevels across the width range. |
| Q3 z-up measured along x gives half / half | Six axial preparation choices, single-axis projective measurement, resulting axis eigenstates. | NumPy Pauli density matrices and projector traces for each axis/preparation. |
| Q4 E₁ = 2 eV implies E₃ = 18 eV | Exact electron length preset 0.4336070583517251 nm, n = 3; ideal energy measurement and immediate repeat. | Independent constants and n² energy ratio; mounted preset and repeated projection. |
| Q5 selected z-up → x-up → z gives conditional half / half | Branch selection, blocked rows, final conditional probabilities, original-input probabilities and complete finite counts; bypass is available. | Sequential Pauli projectors; unpolarized original input gives 1/8 in each final branch, 1/2 conditional on middle survivors. |
| Q6 state uncertainty from Fourier-linked distributions | Complex Gaussian, analytic Fourier partner, width and mean controls, chirp, σx and σp, crop mass and two omitted tails. | Direct complex Fourier quadrature, Parseval norms, independent first/second moments and Gaussian tail integrals. |
| Q7 E₁ = 1.5 eV implies E₄ = 24 eV | Exact electron length preset 0.5006863037237804 nm, n = 4. | Independent SI length and energy evaluation. |
| Q8 500 nm photon gives 2.48 eV using rounded 1240 | Vacuum wavelength control, exact SI result and separately labelled 1240 convention. | Independent constants: 2.479683968664005 eV exact-SI numerical result, 2.48 eV rounded convention; inverse wavelength scaling. |
| Q9 identical superpositions yield statistical scatter | Prepared complex two-state superposition, relative/global phases, phase evolution, fresh-preparation batches and ideal energy projection/repeats. | Independent eigenfunction orthogonality, interval quadrature, phase fixtures, Hψ/time-derivative finite differences and aggregate sampling. |
| Q10 sub-barrier transmission with unchanged outgoing energy | Exact stationary finite barrier; both interior exponentials; ψ/ψ′ matching at both faces; signed currents, R/T and detector counts; zero-width limit. | Independent complex 4×4 boundary solve, current reconstruction, R+T conservation and E=V₀/2, κa=1 fixture T=0.4199743416140261. |

The well wavefunction ordinate is `nm⁻¹/²`, its Born density is `nm⁻¹`,
and the abscissa is nm. Gaussian momentum uses `k = p/ℏ` in `nm⁻¹` with a
unit-integral density per k, not a density per SI momentum. The station also
reports σp in kg·m/s and σxσp in J·s. Barrier amplitude uses a unit incident
amplitude and incident-flux normalization; its spatial density is not unit
integral. Signed reflected current remains negative; the finite counts have an
explicit original-input denominator. Photon wavelengths are in vacuum.

For the superposition, the exact n=1/n=2 interval cross term is integrated
analytically. Relative phase π reverses the two quarter-position densities
`(3 ± 2√2)/(2L)`. The Schrödinger state evolves using the individual eigenenergy
phases. Common phase changes both amplitude coordinates and leaves density
unchanged. An energy measurement prepares the observed eigenstate and repeated
ideal measurements of the same unchanged Hamiltonian are certain. No exact
point-position collapse is claimed within the finite basis.

For spin, Bloch coordinates represent a density matrix. They do not represent a
rotating ball or a calibrated Stern–Gerlach apparatus. When a selected branch
has zero probability, the ledger labels final conditional frequencies as
undefined and reports zero survivors, while showing the hypothetical projector
state separately. Original and survivor denominators never interchange.

For the Gaussian, the Fourier convention is `(2π)⁻¹/²`, and the optional chirp
b gives `σxσp = (ℏ/2)√(1+b²)`. Mean shifts do not change spreads. Neither plot
renormalizes a crop; its finite mass and both tails remain in the ledger. The
text distinguishes state uncertainty from instrument noise and disturbance.

For the barrier, a finite width retains growing and decaying internal terms.
The exact matched solution preserves energy and net current; transmission
requires no energy borrowing. `a = 0` gives zero reflection and unit
transmission. Input normalization enforces the displayed sub-barrier domain
`E < V₀` and recalculates the scattering problem when a parameter changes.

Controls have named range and numeric alternatives. Numeric input remains a
draft until blur, change or Enter; Escape restores the committed value. Drafts
survive changes to unrelated sliders. Station controls are scoped with hidden
wrappers and disabled inputs, so they leave keyboard navigation. Each SVG has a
title and description, explicit axes/units and a keyboard-focusable scroll
region. The ledger is the accessible quantitative alternative. Speech reads
the current model, equation and assumptions. Reset restores preparation,
seed/batch and enlargement. Narrow layouts use one plot/control column;
enlargement exposes horizontal scrolling. All plotted count markers contribute
to the density scale.

## Focused verification

Run in the release checkout:

```sh
node tools/check_physics_quantum_lab.js
/Users/peter/Documents/ChatGPT/Primer/.research/runtime-grade-py312-20261008/bin/python -m pytest tests/test_physics_quantum_lab.py -q
```

The focused JS check verifies 315 analytic states, 82 mounted states and 168
unit-labelled SVG curves, including every available station, exact fixtures,
invalid values, control endpoints, count ledgers, energy repeats, keyboard
drafts, reset, speech and scoped controls. The eight Python tests pass and
inspect production CommonJS output directly; they do not reuse the JS checker
as their reference. Trigonometric amplitude comparisons allow `1e-11` absolute
roundoff at the most rapidly rotating n=6 phase endpoints. Scientific
comparisons use independent constants, SciPy quadrature, NumPy projectors and a
complex linear solve rather than the production closed forms.

Root integration owns curriculum repairs/outcome crosswalk, exact binding,
script/style registration, the dedicated 3D family and reconstruction of its
emitted geometry. The existing original infinite-well model and
its tests remain present for regression coverage. This review describes the
five-station lab and its focused evidence, not a whole-curriculum or clinical
completion claim.

## Shared state and isolated actual-reader QA

Rendered roots expose `setModelState(values, announce=false, fromShared=false)`
and join the ephemeral `PrimerLessonStateBus` under exact key `phys.4.quantum`.
Every user commit publishes the full normalized state, including unannounced
range input, presets, projection/batch actions and reset. Peer reception updates
the calculation and controls without publishing again. The shared bus caches
no prior state and persists nothing. A focused real-bus check mounts two views
of each of the quantum and complex labs, verifies source exclusion and peer
echo suppression, checks cross-lesson isolation, and prunes disconnected views.
The combined focused Python suite passed ten tests in 12.32 seconds after these
hooks and the display fixes; quantum calculations were unchanged.

Release review found and repaired a correlated energy-projection eligibility
gap. A prepared eigenstate can project only onto its own n. In the two-state
preparation, n=1 requires mix<1 and n=2 requires mix>0; all other or
zero-probability requested outcomes restore the unprojected preparation. The
`preparedEnergyProbability` API exposes this support, and the 3D inspection menu
disables unsupported outcomes. Actual ideal measurement and immediate repeats
at the assessed n=3/n=4 fixtures remain valid. The focused suite now passes
eleven tests (11.54 seconds); an independent Born-overlap oracle and sixty
specified outcome-probability cases verify support, negative requests and
mounted supported repeats. Earlier complete browser state counts below are
historical; the affected release reader cases and final sources are pinned
separately.

The [actual quantum reader proof](/Users/peter/Documents/ChatGPT/Primer/.research/complex-quantum-owner-qa-20261011-_2wfb64z/quantum-proof.json)
uses a fresh private database, separate backups, the scientific Python 3.12
runtime and independent headless Chromium contexts against loopback. The real
`phys.4.quantum` route was opened with global reader stage 2, so the actual
application model speaker was present. Each viewport, 1440×980 and 390×980,
passed all five stations, 48 range endpoints, 48 numeric endpoints, eighteen
choice values, nine assessed presets, draft preservation and blur/Enter/Escape,
native keyboard selection, numeric arrows, Space reset, resampling, ideal energy
projection/repeats/repreparation, enlargement and exact reset. Fourteen complete
current-state speech captures per width preserve the current readout, equation
and assumptions through the real application's bounded speech chunks.

Actual hidden/disabled widgets and action buttons, SVG text bounds and overlap,
body overflow and finite SVG attributes were checked. One small tunnel-preset
axis tick extended left of the SVG; scientific notation fixed that renderer
label, and the complete final check passed with zero browser runtime errors or
remaining clipped/overlapping labels. Browser-loaded response hashes equal
refetched and local hashes for the quantum lab/CSS, state bus, registry,
application, shared stylesheet, speech chunker and spatial engine/module files. This is isolated-reader
evidence, with no production-host or acoustic-quality claim.

Ten station viewport captures were retained. The reviewer visually inspected
[desktop spin branches](/Users/peter/Documents/ChatGPT/Primer/.research/complex-quantum-owner-qa-20261011-_2wfb64z/quantum-1440-spin-viewport.png),
[desktop matched barrier](/Users/peter/Documents/ChatGPT/Primer/.research/complex-quantum-owner-qa-20261011-_2wfb64z/quantum-1440-barrier-viewport.png),
[mobile Born amplitudes/density](/Users/peter/Documents/ChatGPT/Primer/.research/complex-quantum-owner-qa-20261011-_2wfb64z/quantum-390-well-viewport.png),
[mobile Gaussian partners](/Users/peter/Documents/ChatGPT/Primer/.research/complex-quantum-owner-qa-20261011-_2wfb64z/quantum-390-gaussian-viewport.png),
[mobile barrier](/Users/peter/Documents/ChatGPT/Primer/.research/complex-quantum-owner-qa-20261011-_2wfb64z/quantum-390-barrier-viewport.png)
and [mobile photon dispersion](/Users/peter/Documents/ChatGPT/Primer/.research/complex-quantum-owner-qa-20261011-_2wfb64z/quantum-390-photon-viewport.png).
The plots and units remain in frame, finite-bin markers are visible, and mobile
panels stack above an internally scrollable ledger.

The [historical shared quantum reader proof](/Users/peter/Documents/ChatGPT/Primer/.research/complex-quantum-owner-qa-20261011-_2wfb64z/quantum-shared-proof.json)
verified both widths, 72 spatial control states, eleven lab/measurement/batch
cases, seventeen camera cases, current speech, full-state synchronization,
source/peer echo suppression, and exact reset. Nondefault scientific state and
camera tests distinguish preservation from accidental reset. That complete
batch preceded the projection eligibility repair. The
[bounded release projection proof](/Users/peter/Documents/ChatGPT/Primer/.research/complex-quantum-owner-qa-20261011-_2wfb64z/quantum-projection-release-proof.json)
replays only fifteen affected cases at each width: impossible eigen/endpoint
outcomes normalize to none and have disabled native options; valid mixed
outcomes, n=3/n=4 measurements/repeats and core↔3D synchronization remain valid.
Thirty-six current speaker captures, derived SVG bounds and all eleven
loaded/served/local hashes passed with zero runtime errors. The complete
historical batches were preserved and were not repeated for this repair.

The [final post-main reader smoke](/Users/peter/Documents/ChatGPT/Primer/.research/complex-quantum-owner-qa-20261011-_2wfb64z/post-main-reader-proof.json),
after main integration at `a96e36b`, opens both lessons in four fresh
desktop/mobile contexts. Desktop panel folding/unfolding, supported fixtures,
core↔3D controls, current speech and derived SVG bounds pass. All eleven
browser-loaded/local source hashes match the frozen runtime, with zero errors.
The private server was stopped after the proofs and documents were frozen.

## Primary references

- [NIST 2022 CODATA complete constants table](https://physics.nist.gov/cuu/Constants/Table/allascii.txt): electron mass and SI constants.
- [OpenStax, particle in a box](https://openstax.org/books/university-physics-volume-3/pages/7-4-the-quantum-particle-in-a-box): stationary hard-wall states and energy scaling.
- [MIT 8.05, Chapter 2: Spin](https://ocw.mit.edu/courses/8-05-quantum-physics-ii-fall-2013/a56c316e4ec548d8bd0a554fac9a74e8_MIT8_05F13_Chap_02.pdf): axial preparation and projective spin measurements.
- [MIT 8.04, Lecture 7: Wavepackets and uncertainty](https://ocw.mit.edu/courses/8-04-quantum-physics-i-spring-2016/6ca5bd79a2121967796f7c0b8f6f48c9_MIT8_04S16_LecNotes7.pdf): Fourier-linked Gaussian states and spreads.
- [OpenStax, finite potential barriers](https://openstax.org/books/university-physics-volume-3/pages/7-6-the-quantum-tunneling-of-particles-through-potential-barriers): matched scattering solutions, reflection and transmission.

All diagrams are original mathematical constructions. No source figures were copied.
