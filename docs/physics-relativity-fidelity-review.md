# Relativity events, clocks and curvature lab

This authored activity covers the ten assessment rows in `phys.4.relativity` with eight interactive stations. The calculations are analytic within explicitly stated physical models; independent verification also integrates a trajectory numerically and solves reception intersections. This is a 1+1 dimensional special-relativity laboratory and a bounded introduction to general-relativity ideas. It does not claim an engineering GPS receiver, propulsion simulation or strong-field numerical spacetime solver.

## Assessment coverage

| Assessment | Interactive evidence and convention |
|---|---|
| Q1 muon lifetime | R2 preset: proper **mean** lifetime 2 µs, exact γ=5; lab mean 10 µs, associated flight distance and rest-frame decay event. An individual lifetime remains random. |
| Q2 tower clocks | R6 tower preset: 100 m, one Julian year, spherical Schwarzschild stationary-clock ratio plus leading differential Earth rotation. At latitude 45° the net top-minus-foot gain is about 0.343442 µs. Height, latitude and duration are interactive. |
| Q3 equivalence | R7 compares freely falling radial/transverse separations with flat-spacetime free particles. Tidal relative acceleration vanishes with extent; finite extent can reveal curvature. A Born-rigid Rindler cabin has a proper-acceleration gradient despite zero curvature. |
| Q4 rod length | R2 preset: 10 m rest rod, exact γ=2.5, 4 m lab simultaneous length. The endpoint events transform to different rod-frame times; a separate rod-simultaneous pair is displayed. |
| Q5 pole/barn | R3 preset: 20 m rest pole, γ=2, 10 m rest barn. Worldlines and **same physical closure events** appear in both frames. Exit closes before entrance in the pole frame; the barn’s simultaneous rest-in-pole length is 5 m and uses different events. Ideal instantaneous reopening is explicit. |
| Q6 GPS | R6 orbit preset: signed gravitational and velocity contributions, rounded +45−7=+38 µs/day assessment, distinct spherical-orbit estimate, model precompensation and NIST nominal prescription. Receiver propagation/rotation and eccentricity corrections are explained. |
| Q7 energy | R4 preset: 500 MeV invariant rest energy, 2500 MeV total energy, γ=5, plus pc, kinetic energy and energy–momentum invariant. |
| Q8 ships | R4 preset: station velocities +0.5c and −0.5c, other-ship speed 0.8c. The station’s closing rate is separately labelled. |
| Q9 steady acceleration | R5: exact constant proper acceleration worldline, rapidity, inertial/crew time, strictly subluminal speed, separately retained 1−v/c and finite energy. Rest mass does not grow. |
| Q10 Sagnac | R8: both null reception intersections with a moving detector; exact inertial and detector proper arrival differences. Unwrapped inertial and rotating angle charts expose equal rotating coordinate circumference and unequal travel times. Local vacuum speed remains c. |

R1 additionally makes Lorentz boosts, invariant causal intervals, null cones, frame-defined simultaneity and spacelike event-order reversal directly adjustable. Spacetime axes both use metres (`ct` and `x`) and the SVG’s chart area is square with the same gain on both axes. Neither the 2D charts nor a subsequent 3D embedding treats time as a physical spatial direction.

## Model and numerical limits

The exported browser/CommonJS API is `PrimerPhysicsRelativityLab`. It exposes `normalize`, `build`, `render`, the mode-specific snapshots, `lorentzEvent`, `interval`, `relativeVelocity` and `properAccelerationAt`. Every build returns the complete normalized state, current values, unit-labelled panels, worldlines, ledger, readout, equation and assumptions. It publishes the full lesson state through `phys.4.relativity` and accepts peer state without echoing it back.

Controls have finite explicit bounds, a range control and an exact `step=any` numerical entry. Invalid/nonfinite values fall back; legitimate numeric values clamp to their documented physical bounds. Typed drafts survive unrelated updates, blur/Enter commits them, Escape restores the current value, and reset restores the full state. Inactive controls are hidden and disabled. Assessed presets retain their exact β values rather than snapping the stored state to a slider step. Speech reads the current parameters, all ledger values, equations and assumptions.

Lorentz velocities are bounded below c. Events use `(ct)²−x²` with signature (+,−), and classification within 16 machine epsilons of the squared-coordinate scale is the numerical null limit. Proper time belongs to timelike pairs; proper separation belongs to spacelike pairs. Graphs join finite samples, while all selected values and event coordinates come from analytic expressions.

Constant acceleration uses η=aτ/c, integrates the exact hyperbolic worldline and retains `cosh(η)−1` through `2sinh²(η/2)` for small η. The displayed proper acceleration spans 0.1–2 g₀ and crew time 0–5 Julian years; at the largest setting speed is still numerically resolved below c. The near-light readout keeps enough digits to avoid displaying equality with c. The public helper rejects rapidity beyond 16.

The tower model preserves a small Schwarzschild clock-ratio difference without subtracting two nearly equal square roots. Leading rotation is added separately. Earth is spherical with GM=3.986004418×10¹⁴ m³/s² and reference radius 6378137 m. The orbit calculation is first order in Φ/c² and v²/c² with circular orbital velocity and a rotating ground clock. It omits oblateness/geoid harmonics and eccentricity, so its result is labelled separately from operational GPS’s geoid-based prescription. `c × clock offset` is explicitly a one-way range equivalent, not a claimed actual position error. The correction switch cancels this model’s secular rate only.

The tidal model uses the initial weak-field tidal tensor and a second-order short-time separation change. Extents are 0–1000 m and times 0–10 s; this is a local approximation, not an exact finite fall. Radial/transverse changes are stored directly to preserve tiny changes that subtraction from a large separation would lose. GR’s metric, geodesics, curvature, equivalence principle and stress–energy field equation are introduced without claiming a complete GR solver.

Sagnac uses ideal continuously redirected **vacuum** light on an inertial fixed-radius circle. It does not substitute a dielectric fiber or finite rotating-mirror polygon for that model. Signed β=ΩR/c is bounded to ±0.6. Exact reception times satisfy θlight=θdetector±2π; the proper difference uses the same detector’s clock. The area formula is labelled as the low-speed approximation. The signed difference is calculated directly, preserving realistic small rotations. Rotating coordinate velocities are labelled as rates of Rθ′ per inertial time; they are never presented as local light measurements. The two rotating coordinate path lengths are equal, while global Einstein synchronization around the loop has a gap.

## Primary-source basis

- [MIT 8.20 special relativity](https://ocw.mit.edu/courses/8-20-introduction-to-special-relativity-january-iap-2021/) supplies the inertial-frame, Lorentz transformation and interval conventions.
- [MIT 8.033 Lecture 13](https://ocw.mit.edu/courses/8-033-introduction-to-relativity-and-spacetime-physics-fall-2024/mit8_033_f24_lec13.pdf) derives constant proper acceleration using four-velocity and hyperbolic functions.
- [MIT 8.962 Lecture 7](https://ocw.mit.edu/courses/8-962-general-relativity-spring-2020/resources/lecture-7-the-principle-of-equivalence-continued-parallel-transport/) explains local equivalence and the finite-extent limitation caused by tides.
- [NIST optical-clock experiment](https://www.nist.gov/news-events/news/2010/09/nist-pair-aluminum-atomic-clocks-reveal-einsteins-relativity-personal-scale) reports gravitational comparison over 33 cm and velocity-induced clock shifts.
- [Ashby & Weiss, NIST TN 1385](https://tf.nist.gov/general/pdf/1274.pdf), particularly §§2.3–2.5, specifies geoid-based rates, a nominal −4.4645×10⁻¹⁰ oscillator offset, eccentricity correction and inertial signal propagation with receiver rotation. This older nominal value is identified by source, rather than claimed as an exact contemporary hardware specification.
- [Frauendiener, Notes on the Sagnac effect in General Relativity](https://arxiv.org/abs/1808.07914) develops the geometric time difference and its local/rotating-observer interpretation.

The lesson diagrams and code are original analytic assets; no source image or third-party full-text PDF is republished by the lab.

## Verification

`tools/check_physics_relativity_lab.js` checks 147 analytic fixtures, all eight stations, 102 mounted control/preset states, 520 calibrated SVG curves, 25 exact draft/blur/Enter/Escape controls, strict renderer props, scoped controls, reset/enlargement and current full speech.

`tests/test_physics_relativity_lab.py` checks independent rapidity-matrix Lorentz transforms/inverses/invariants, clock proper-time integration, simultaneous length pairs, door-event worldlines, velocity addition through rapidity, energy–momentum invariants, a DOP853 time/worldline ODE, 60-digit Schwarzschild clock ratios, signed orbit-rate prescriptions, finite-difference tidal Hessians, independent Sagnac reception roots and detector proper-time integration. It also rejects cross-lesson/unknown-prop curriculum binding and checks tiny proper times plus near-light readout precision.

Actual isolated headless Chromium QA at 1440×1000 and 390×844 checks eight stations per viewport, 50 exact number states, 50 range states, 25 draft preservation/blur states, 25 keyboard states, 14 presets, 207 full-speech checks, no document horizontal overflow and no SVG text clipping per viewport. Sixteen screenshots were retained; representative desktop pole/barn and Sagnac and mobile events/GPS views were visually inspected. The standalone QA’s server, browser and contexts are closed after each run. It does not claim authenticated production-reader verification. Local ignored evidence is `.research/relativity-lab-qa-20261011/proof.json`; a separate root-owned reader/3D integration review remains necessary before release.
