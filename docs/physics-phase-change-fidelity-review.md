# Quantitative phase change in the actual matter and hot/cold lessons

The added `physics-phase-lab` activity addresses the missing latent-heat and
melting-ice examples in `phys.2.matter` and `phys.0.hot-cold`. The existing matter
activity selects particle motifs by temperature; temperature at a coexistence
boundary cannot determine how much material has changed phase. The new activity
uses mass and signed heat supplied since an explicitly selected starting state.
It shows complete melting and vaporization plateaux, mass fractions and the
reverse cooling path. It does not establish complete lesson or curriculum fidelity.

## Physical model and numerical domain

The ideal sample consists of captured pure water at approximately 1 atmosphere
(101.325 kPa). Its volume can change; no mass escapes. States are internally
uniform and in phase equilibrium. The model uses approximate transition
temperatures of 0 and 100 °C, constant ice/liquid/vapour specific heat capacities
of 2.09/4.186/2.020 kJ/(kg·K), and constant fusion/vaporization enthalpies of
334/2256 kJ/kg. These rounded properties and phase-change relations follow
[OpenStax's heat-capacity table](https://openstax.org/books/university-physics-volume-2/pages/1-4-heat-transfer-specific-heat-and-calorimetry)
and [latent-heat table and captured-sample example](https://openstax.org/books/university-physics-volume-2/pages/1-5-phase-changes).
The liquid value is treated as an effective constant-pressure heat capacity;
the small liquid/solid difference between constant-pressure and constant-volume
values is neglected. Steam uses the table's constant-pressure value.

At fixed pressure, with only expansion work, supplied heat is ΔH, including
pressure–volume work. It must not be presented as entirely ΔU. The diagram is a
mass-fraction bar, not a sealed fixed-volume container or a volume/piston
simulation. Its widths encode masses only. No particle counts, molecular sizes
or density changes are invented.

Specific enthalpy h has the reference zero of pure ice at 0 °C. The model's
transition endpoints are h=0 (pure ice), 334 (pure liquid at 0 °C), 752.6 (pure
liquid at 100 °C), and 3008.6 kJ/kg (pure vapour at 100 °C). Between each pair of
phase endpoints, the minority/majority fractions follow the latent-energy
balance. Within a pure phase, h changes with the selected constant heat capacity.
Thus equal temperatures at 0 or 100 °C can accompany different fractions.
Exact endpoints are labelled pure; they do not falsely assert an ongoing
transition or a second phase of zero mass.

The adjustable mass is 0.05–2 kg. Temperature is restricted to −30–140 °C,
corresponding to h=−62.7…3089.4 kJ/kg. The signed heat bounds for each sample are
m(h_min−h_start) and m(h_max−h_start). Inputs outside the range clamp to the
nearest endpoint, invalid mass defaults to 0.25 kg, and blank/invalid heat
defaults to zero. The rendered controls explain the dynamic heat limits.
Selecting a new starting state resets supplied heat to zero. Changing mass
retains the same supplied heat within the new range. Reset restores the
lesson-specific initial sample, while Return to starting state retains the
current mass and selected start. No extrapolation toward absolute zero occurs.

Cooling uses the same equilibrium state path in reverse. The five signed ledger
rows partition Q into ice temperature change, melting/freezing, liquid
temperature change, boiling/condensing, and vapour temperature change. Each row
is the signed overlap of the traversed heat interval with its physical stage.
Their sum is ΔH and agrees with Q to floating-point precision. This calculation
preserves positive tiny heat and coexistence fractions; there is no epsilon band
that converts a nearby state to a pure endpoint, and nonzero scientific-notation
values are not formatted as zero.

Absolute `currentH` remains a JavaScript Number. For heat smaller than an ulp
of a nonzero starting enthalpy, `h_start + Q/m` can round back to the starting
value. `build` therefore selects the phase, residual fractions and stage ledger
on a heat axis relative to exact transition heats. Consumers must use the
returned `fractions`, `temperature` and `deltaH`, rather than reconstructing
them by calling `resolve(build.currentH)`. `resolve(h)` is the pure scalar API
for representable absolute enthalpies. Decimal domain endpoints are explicit
and accessible without a floating-point tolerance.

These are educational constant-property calculations, not an implementation of
the [IAPWS fluid-water formulation](https://iapws.org/technical-guidance/release/IAPWS-95)
or [IAPWS ice equation of state](https://iapws.org/technical-guidance/release/Ice-2009).
Real properties and transition temperatures depend on temperature and pressure.
Supercooling, superheating, nucleation, heat-transfer rate, heat leaks and
irreversibility are omitted. The model does not predict the melting time of an
ice cube in a hand. Open-air evaporation below boiling, humidity, wind-driven
drying, actual ice/liquid/gas volumes, density, compressibility and pressure
variation remain separate lesson requirements. Vapour is a gas; visible kettle
mist consists of liquid droplets and is not represented by the mass bar.

## Renderer and integration contract

The renderer name is `physics-phase-lab`. The only accepted props are:

| Actual lesson | Exact props | Initial sample |
| --- | --- | --- |
| `phys.2.matter` | `{"scenario":"phys.2.matter.phase-change"}` | 0.25 kg ice at −18 °C, Q=0 |
| `phys.0.hot-cold` | `{"scenario":"phys.0.hot-cold.melting-ice"}` | 0.05 kg ice at 0 °C, Q=0 |

Load `/app/physics-phase-lab.css` and `/app/physics-phase-lab.js` before the
lesson-model registry, register `window.PrimerPhysicsPhaseLab.render(item,hooks)`,
and add the renderer to the dedicated-renderer return list. Backend validation
must reject extra props, unknown scenarios and cross-lesson bindings. The
activity supports the existing `hooks.speakButton` callback with numeric
temperature, heat, phase masses/fractions and enthalpy change. Native select,
range and numeric controls, target/reset buttons and focusable scrolling plot
regions support keyboard use. Enlarge creates a wider local plot viewport;
fit restores the responsive two-panel/stacked layout.

The module exports a normal CommonJS API and the window API. The pure
`equilibriumAtSpecificEnthalpy(hKJkg)` alias of `resolve(hKJkg)` returns
`{enthalpy, temperature, fractions:{ice,water,steam}, phase}` and throws
`RangeError` outside the documented h interval. `build({mass,start,energy})`
returns normalized state, `initialH`, `currentH`, `temperature`, `fractions`,
phase `masses`, signed `ledger`, `deltaH`, `balanceResidual`, heat `limits`, and
six physical graph `points` (`energy`, `temperature`, `enthalpy`). Graph heat
coordinates scale with mass; temperature axes retain −30–140 °C. Mass bars span
exactly the full sample width. Ledger half-axes each represent m×2256 kJ and
are labelled, so signed component lengths have a declared calibration.

## Verification and remaining gates

`node tools/check_physics_phase_lab.js` verifies 1,512 independent physical
states and 284 mounted DOM/graph/fraction/ledger states. The reference checker
uses independent decimal constants, a sequential calorimetric budget, weighted
phase enthalpies and signed interval-overlap energy accounting. It tests every
start, selected mass extrema/interior values, all transitions and near-boundary
states, reverse paths, heat clamping, derivatives within pure phases and flat
plateaux. Tiny signed heat and minority fractions receive explicit regression
checks. The DOM checks inspect actual SVG paths, bar widths/origins, markers,
control limits, reset and numeric speech. They do not execute file text with
`vm` or `eval`.

The optional `--browser` mode normally serves the original scripts and styles
on an ephemeral loopback server. Playwright verification passed 288 states at
1440 and 390 CSS pixels: six starting states, keyboard Home/End mass and energy
extrema, all phase targets, cooling, reset, speech and fit/enlarged layout.
Independent physical-coordinate comparisons, SVG text bounds and body-overflow
checks passed with no page errors. Desktop matter and mobile melting screenshots
were visually inspected. Evidence is in the new private temporary directory
printed by the checker. These are direct-renderer browser checks; actual lesson
route, backend, companion-3D and production verification are separate integration
gates. The pytest file additionally requires strict curriculum bindings and
script/style ordering after integration.

The phase-change activity closes a specific missing quantitative example. It
does not establish full matter/physics coverage, molecular fidelity, clinical
accuracy, radiology approval, authenticated production delivery or completion
of the broader mathematics/physics/clinical goal.
