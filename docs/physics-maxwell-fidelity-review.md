# Maxwell full-lesson fidelity review — 11 October 2026

The dedicated `phys.4.em-maxwell` activity now covers the four Maxwell equations, vacuum-wave directions and SI quantities, capacitor displacement current, coax cancellation, and antenna power conservation. Its seven quantitative stations share their complete state with the new spatial family. Existing authored examples remain available through the parent integration.

This is an author-owned science and presentation review of one lesson. Independent Python equation oracles do not make it an independent human review. The parent owns separate curriculum, whole-reader, spatial-peer, release and deployment verification. This document does not establish whole-Primer completion.

## Scope and assessed requirements

| Station | Quantitative representation | Quiz coverage |
|---|---|---|
| M1: magnetic closed flux | Prescribed uniformly magnetized sphere: exact interior and exterior B vectors, curved cap, cut disk, signed flux and outward normals. Reversing magnetization reverses both cancelling fluxes. The cut is a mathematical surface through the magnet, not physical removal of a piece. | 1 |
| M2: electric Gauss law | Uniform volume-charged ball, Gaussian surface, enclosed charge, signed radial E, local divergence and closed flux. Interior finite field and exterior inverse-square field remain distinct. | Full lesson's charge/divergence requirement |
| M3: Faraday law | Changing long-solenoid magnetic flux, oriented stationary loop, actual induced E vectors, circulation and local curl, including the field outside the solenoid. | Full lesson's induction/curl requirement |
| M4: Ampere–Maxwell law | Thin circular vacuum capacitor with conduction current, displacement density, B vectors, capacitance and instantaneous E. Two surfaces share one boundary, including partial plate loops. | 5, 7 |
| M5: waves | Actual SI E/B/Poynting vectors, frequency, wavelength, period, impedance and mean intensity. Equal-scale spacetime crest, polarization, reversed propagation, and a clearly hypothetical epsilon/mu comparison. | 2, 3, 4, 8 |
| M6: coax | Finite-thickness sheath and core, signed current-density integral, actual azimuthal B, exact external balance and deliberate imbalance. | 9 |
| M7: radiation | Hertzian effective-length dipole, anisotropic angular intensity, radiative E/B amplitudes, complete-sphere power, radius dependence, exact axis zero, and steady DC zero radiative term. | 6, 10 |

For a capacitor gap loop of radius `a/2`, the gap displacement contribution is `I/4`. The wire-spanning surface consists of an oppositely oriented gap annulus, a cylinder outside the plate, and a lower disk crossing the feed wire. Its displacement contribution is `−3I/4`, so its full wire current plus displacement also gives `I/4`. The lower positive plate and current point along +z. This prevents an incorrect comparison of a full feed current with a partial plate flux.

The wave defaults give `c0 = 299792458 m/s`, `Bpeak = 2.001384571… µT` for `Epeak = 600 V/m`, and `λ = 599.584916 nm` at `500 THz`. The quiz's rounded `3.0e8 m/s` gives `2 µT` and `600 nm`. E and B have different physical units; their drawn gains remain separate and stated.

The parent's current question 2 is scientifically consistent: it compares hypothetical nondispersive parameters and explicitly preserves exact SI c. Current question 10 is also consistent: a time-independent source after transients has no radiative term, although static fields may remain. The radiation activity does not claim that every changing current necessarily radiates; source geometry and cancellation matter.

## Runtime interface and geometry

`window.PrimerPhysicsMaxwellLab` and its CommonJS export expose `SCENARIO`, `constants`, `initial`, `stations`/`modes`, `controls`, `choices`, `presets`, `normalize`, `build`, `snapshot` and `render`. The scenario is `phys.4.em-maxwell.fields-flux-radiation`; the renderer is `physics-maxwell-lab`. Seven named snapshot methods and the analytic field functions are callable for valid SI geometry.

`build` returns `{state, current, panels, ledger, equation, readout, note}`. Standard field samples retain `positionM` and `vector`. Wave samples retain `positionM`, `phaseRad`, `EVM`, `BT` and `SWM2`. The full normalized state preserves inactive station parameters. Renderer publish/join uses `PrimerLessonStateBus` key `phys.4.em-maxwell`; received state does not republish.

`window.PrimerMaxwellSpatialFamily` exports a normalized controls factory, initial factory and the same state key. It uses actual field coordinates, cap and disk surfaces, capacitor spanning surfaces, source cylinders, wave endpoints and a physical radiation observation sphere. Its returned `maxwell` object retains the entire current source data, all plotted source coordinates, field endpoints, surfaces and calibrations. The wave's display translation is recorded alongside every plotted sample. The separate angular chart has radius proportional to `dP/dΩ`, not a physical distance or material surface.

All E arrows are coral; all B arrows are blue. Unit normals, signed total-current glyphs and mean Poynting vectors have explicit meanings. Field samples occupy stated meridian or transverse planes; they do not purport to be an exhaustive discretization of all space. Every geometric or field gain is recoverable from the record and readout. Float64 conversion/underflow, gain caps, exact zeros and unresolved small glyphs are disclosed.

## Verification

The pinned [science review](physics-maxwell-fidelity-review-20261011.json) records the exact source hashes and full requirement mapping. The [real-browser receipt](physics-maxwell-browser-proof-20261011.json) pins the actual served sources, Chromium version and capture hashes. Its server and browser handles were closed.

`node tools/check_physics_maxwell_lab.js` passes 272 analytic fixtures, 116 mounted control/preset states, 382 calibrated SVG curves, 4,079 exact SVG field arrows and 31 exact draft/blur/Enter/Escape controls. It also checks 76 spatial states, 4,374 SI field endpoints and 24,545 surface vertices, including source-to-display transforms, field colors, zero/subnormal inputs and the renderer geometry limit.

`python -m pytest -q tests/test_physics_maxwell_lab.py` passes all eight tests. Independent oracles use surface/volume/angular quadrature, Cartesian finite-difference divergence and curl, wave differential equations, and charge/current continuity. They cover 27 magnetic caps, 45 electric Gaussian surfaces, 45 induction loops, 135 capacitor surfaces, 108 wave states, 252 coax current states and 72 radiation states.

At each of 1440 px and 390 px, real Chromium exercises all seven stations, 62 numeric and 62 range states, 31 exact draft and keyboard controls, 11 presets and four choices. It checks 363 complete speech/state synchronizations and 84 camera actions per width. There are 42 captures and zero page errors. All 14 lesson captures and all 14 dedicated spatial canvas captures were visually inspected; the other 14 full spatial captures are retained. Phone ledgers and enlarged plots use explicit horizontal scrolling instead of page overflow.

The isolated HTTP harness uses the real source assets, state bus and spatial engine. It does **not** prove authenticated Primer-reader or production delivery behavior; those remain separate parent gates. Prior receipts and numerical tolerance observations are preserved. The review also records the repairs to exact-integer formatting, mobile camera framing and E/B legend colors.

## Physical limits and primary references

The sphere is an exact prescribed-magnetization model, not a constitutive ferromagnetic bar calculation. The capacitor and solenoid are stated quasistatic idealizations. Coax excludes ends, connectors, bends and skin effect. The plane wave is infinite and monochromatic. Dipole radiation shows only the Hertzian radiative terms at `r ≥ 5λ`, with effective length `ℓ ≤ 0.05λ`; it is not a near-field or half-wave antenna solution. These limits remain in the activity and complete speech.

Primary references, checked on 11 October 2026: [NIST 2022 constants](https://physics.nist.gov/cuu/pdf/all.pdf), [UT Austin's magnetized sphere derivation](https://farside.ph.utexas.edu/teaching/jk1/lectures/node61.html), [Caltech's Maxwell equations and continuity](https://www.feynmanlectures.caltech.edu/II_18.html), [Caltech's Gauss-law examples](https://www.feynmanlectures.caltech.edu/II_05.html), [MIT's electromagnetic-wave chapter](https://ocw.mit.edu/courses/8-02-physics-ii-electricity-and-magnetism-spring-2007/resources/chapte13em_waves/), and [MIT's Hertzian dipole notes](https://www.ocw.mit.edu/courses/6-013-electromagnetics-and-applications-spring-2009/015b9db53add91f7384c71335ae0b436_MIT6_013S09_lec19.pdf). Diagrams and code are original analytic representations; no source image was copied or repainted.
