# Independent water phase-change review — 10 October 2026

The actual `phys.2.matter` lesson asks about phase identity and particle motion,
evaporation below boiling, density, warming ice from −18 to 0 °C, boiling-point
differences, gas expansion and compressibility, condensation and wind-assisted
drying. The prerequisite `phys.0.hot-cold` asks about warm-to-cool energy flow,
melting ice in a hand, cooling food and blowing on soup. A fixed-pressure
enthalpy activity can directly support melting, freezing, bulk boiling,
condensation and energy accounting. It does not calculate the other mechanisms.

This review was developed separately from `physics-phase-lab.js`. The numerical
oracle uses straight interpolation between independently calculated enthalpy
knots mapped onto the signed-heat axis; its energy ledger uses signed
intersections with those intervals. It
does not use the implementation's phase resolver to calculate expected values.

## Physical reference and scope

[OpenStax §1.4](https://openstax.org/books/university-physics-volume-2/pages/1-4-heat-transfer-specific-heat-and-calorimetry)
supplies `Q = mcΔT` and representative specific heats: ice 2090, liquid water
4186 and steam at constant atmospheric pressure 2020 J/(kg·K). The steam
constant-volume value is 1520 and would be inappropriate for this activity.
The liquid and solid values are treated as constant-pressure approximations;
real properties vary with temperature.

[OpenStax §1.5](https://openstax.org/books/university-physics-volume-2/pages/1-5-phase-changes)
supplies `Q = mL`, water's tabulated latent heats 334 and 2256 kJ/kg, and the
normal 0 and 100 °C phase boundaries. It distinguishes boiling from evaporation
below boiling. The ideal retained-water heating curve and its reverse preserve
the sample mass and have flat transition temperatures.

[OpenStax §3.3](https://openstax.org/books/university-physics-volume-2/pages/3-3-first-law-of-thermodynamics)
uses `ΔU = Q − W` and `W = pΔV` for atmospheric-pressure vaporization. Combining
these with `H = U + pV` gives `Q = ΔH` at constant pressure when only boundary
work occurs. Calling the whole prescribed heat input a change in internal
energy would omit expansion work. The activity therefore needs a retained
parcel whose volume may change, rather than a rigid sealed vessel. It must
describe its diagram as energy and mass accounting rather than density or
particle spacing to scale.

The constants are rounded teaching values at a fixed 101.325 kPa. They do not
provide a pressure-dependent water equation of state, a nucleation model,
supercooling, humidity, mass loss to air, elapsed time or a heat-transfer rate.
In particular, zero gas fraction in this retained bulk-equilibrium model does
not mean that a real puddle cannot evaporate below 100 °C.

## Independent enthalpy and phase oracles

Use kJ for heat `Q`, kg for mass `m`, kJ/kg for specific enthalpy `h`, and
kJ/(kg·K) for specific heat. Take pure ice at 0 °C as `h = 0`. The state is
`h_final = h_initial + Q/m`; its temperature alone cannot specify phase
fractions at a transition.

The independently calculated interpolation knots are:

| Specific enthalpy h (kJ/kg) | Temperature (°C) | Ice mass fraction | Liquid mass fraction | Vapor mass fraction |
| ---: | ---: | ---: | ---: | ---: |
| −62.7 | −30 | 1 | 0 | 0 |
| 0 | 0 | 1 | 0 | 0 |
| 334 | 0 | 0 | 1 | 0 |
| 752.6 | 100 | 0 | 1 | 0 |
| 3008.6 | 100 | 0 | 0 | 1 |
| 3089.4 | 140 | 0 | 0 | 1 |

Linear interpolation within each adjacent pair gives both temperature and
fractions. On the first coexistence interval, the liquid fraction is `h/334`.
On the second, the vapor fraction is `(h − 752.6)/2256`. Each phase mass is
`m × fraction`; fractions must stay nonnegative and sum to one. Endpoints are
pure states: 0 is ice at the melting point, 334 is liquid at the melting point,
752.6 is liquid at the boiling point and 3008.6 is vapor at the boiling point.
Pure endpoint labels must agree with zero mass in the other phase.

For a ledger independent of the phase branch code, split the interval from
`h_initial` to `h_final` at the four boundaries. The signed overlap with each
of the five intervals, multiplied by mass, is that stage's transferred heat.
The total overlap is `m(h_final − h_initial) = Q`. Cooling reverses the signs
and crosses the same knots in reverse, including the full latent plateaux.
No phase fraction may jump or temperature drift across a plateau.

For 0.1 kg initially at −18 °C, `h_initial = −37.62 kJ/kg`. These reproducible
values distinguish warming ice from melting it:

| Q into the parcel (kJ) | Expected state |
| ---: | --- |
| 0 | Pure ice at −18 °C |
| 3.762 | Pure ice at 0 °C |
| 20.462 | 0.05 kg ice and 0.05 kg liquid at 0 °C |
| 37.162 | Pure liquid at 0 °C |
| 45.534 | Pure liquid at 20 °C |
| 79.022 | Pure liquid at 100 °C |
| 191.822 | 0.05 kg liquid and 0.05 kg vapor at 100 °C |
| 304.622 | Pure vapor at 100 °C |
| 308.662 | Pure vapor at 120 °C |

Starting with pure vapor at 120 °C and removing 308.662 kJ from 0.1 kg must
recover pure ice at −18 °C. Scaling both `m` and `Q` by the same factor must
preserve temperature and fractions while scaling phase masses and ledger
energies by that factor.

## Implementation verification

The implementation was reviewed after it became available, using the separate
local oracle and runner at `.research/phase-independent-oracle-20261010.cjs`
and `.research/phase-independent-check-20261010.cjs` in the parent workspace.
The runner passed 12,306 computed states and 552 mounted SVG/control states.
Its largest stage-sum-minus-heat residual was `9.095 × 10⁻¹³ kJ`. These are
targeted evidence for this model, rather than a curriculum completeness measure.

The computed checks compare all six supported starts and masses 0.05, 0.1,
0.25, 0.37, 1.03 and 2 kg with independent heat-axis interpolation. They cover
all exact transition and domain endpoints, mixed states, interior samples,
both signs of heat, cooling from warm vapor through both transitions, bounded
energy inputs, phase-mass conservation and each signed sensible/latent stage.
An additional 432 checks compare exact target heat values with the immediately
adjacent representable heat values on both sides; zero-target comparisons use
`±10⁻¹⁶ kJ` to remain above phase-fraction underflow. Exact targets stay pure,
while the adjacent states preserve their nonzero residual phase.
The mounted checks exercise both lesson bindings, every starting state, mass
control extrema, numeric heat entry, every target button, the cooling preset,
return, reset and enlarge/fit. Starting-state changes reset heat to zero;
mass changes preserve entered heat until the new valid range requires clamping.
Extra binding properties and unknown scenarios are rejected.

The graph is a heat axis, with five independently checked segment endpoints.
Its plateau widths encode 334 and 2256 kJ/kg on the same scale, rather than
giving all stages equal width. Start/current marker coordinates, signed ledger
bar positions and widths, and each phase-fraction rectangle match independently
calculated states. Fraction widths show mass rather than volume. The source
note correctly distinguishes a prescribed energy path from a time/heat-rate
solution and `ΔH` from `ΔU` at fixed pressure.

Two concrete defects found during review were corrected before this passing
run. The initial implementation replaced genuine near-boundary states with
pure endpoints using an epsilon band, and formatted every magnitude below
`10⁻¹¹` as zero. For example:

```js
lab.build({mass: 0.1, start: 'ice0', energy: 1e-16});
lab.build({mass: 0.1, start: 'ice0', energy: -1e-16});
lab.build({mass: 0.1, start: 'ice0', energy: 0.1 * (334 - 1e-12)});
lab.build({mass: 0.1, start: 'water100', energy: 1e-12});
```

The first two originally became zero heat and were described as no transfer.
The third originally became pure liquid although some ice remained. The
fourth retained a vapor fraction but printed supplied heat and vapor mass as
zero. The corrected model keeps the caller's signed heat, compares it with
exact heat-coordinate boundaries, computes a small phase residual from its
nearby endpoint and formats nonzero small quantities in scientific notation.
Tiny `±10⁻¹⁶` and `±10⁻¹² kJ` inputs at ice0, water100 and steam100 now retain
their signed ledger contributions and appropriate phase state. The printed
minimum enthalpy `−62.7 kJ/kg` is also accepted directly.

A scalar IEEE-754 `currentH` can round back to its starting boundary when a
heat increment is smaller than that scalar's spacing. The corrected phase
fractions and ledger preserve that increment on the heat axis, rather than
reconstructing them by subtracting two nearly equal absolute enthalpies.
This distinction matters when inspecting the exported numerical API.

Mounted DOM verification does not establish real-browser text bounds,
responsive layout or authenticated production delivery. Those require their
own actual-route checks.

The existing matter questions cover the −18→0 °C temperature rise and name
condensation, but do not assess latent heat or phase fractions. Adding an
enthalpy activity does not by itself demonstrate alignment with the existing
density, evaporation, balloon and syringe questions or with all the hot/cold
examples. Whole-curriculum mathematics, physics and clinical radiology review
remains incomplete.
