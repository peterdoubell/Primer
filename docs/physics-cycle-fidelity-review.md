# Working-gas cycles and entropy in the actual thermodynamics lesson

The new `physics-cycle-lab` addresses quantitative gaps in `phys.3.thermo`.
Its existing activity calculates a Carnot ceiling with a fixed 100 J input but
has no working-gas path, signed leg balances, refrigerator operation or entropy
accounting. The added activity supplies a reversible ideal-gas Carnot cycle,
its exact reverse, a separate irreversible reservoir heat leak, and a distinct
first-law process ledger. It supports the lesson's 500−200 J, −150+400 J,
800/600 J engine, 600/300 K Carnot bound, insulated-compression energy argument
and open-fridge room-boundary questions. It does not solve water/ink mixing.

## Physical construction

The hypothetical classical monatomic ideal gas has fixed amount n, universal
gas constant R=8.31446261815324 J/(mol·K), C_v=3R/2 and γ=5/3. Each equilibrium
state satisfies pV=nRT and U=nC_vT. Gas entropy is referenced to state A. R is
consistent with [NIST CODATA](https://physics.nist.gov/cuu/pdf/all.pdf) and the
exact SI product N_A k_B. This is not a fitted gas, piston or molecular model.
Real-gas effects and temperature-dependent heat capacities are omitted.

For hot and cold reservoirs at T_h>T_c>0, state A has the selected V_A and T_h.
For hot-isotherm gas heat magnitude H, r=exp[H/(nRT_h)] and
a=(T_h/T_c)^(1/(γ−1)). State B is (rV_A,T_h), C is (arV_A,T_c), and D is
(aV_A,T_c). The engine follows A→B→C→D→A. Its isothermal legs use
W_by=nRT ln(V_end/V_start), Q=W_by and ΔU=0. Its reversible adiabats use
TV^(γ−1)=constant, Q=0 and W_by=−ΔU. These laws and the reverse cycle follow
[the Carnot-cycle construction](https://openstax.org/books/university-physics-volume-2/pages/4-5-the-carnot-cycle)
and [the quasistatic ideal-gas adiabat](https://openstax.org/books/university-physics-volume-2/pages/3-6-adiabatic-processes-for-an-ideal-gas).

The refrigerator follows A→D→C→B→A. It visits the same states in reverse;
each full leg reverses its Q, W_by, ΔU and ΔS. The selected point is calculated
analytically using log-volume progress, including exact leg endpoints. Progress
is a path coordinate, not time, power, engine speed or a solved transient.
Each displayed curved leg uses 121 analytic states joined by straight display
segments. The polygonal drawing approximates the continuous physical path;
it must not be described as an exact polygonal gas process.

The signed convention is Q>0 into the working gas and W_by>0 out as work.
Every leg satisfies ΔU=Q−W_by; cycle sums satisfy ΣΔU=ΣΔS_gas=0 and
W_net=∮p dV=Q_h−Q_c. Reversible Q_c/H=T_c/T_h gives efficiency
1−T_c/T_h and refrigeration COP T_c/(T_h−T_c). Isothermal gas entropy change
is Q/T, while reversible adiabats have zero entropy change.
[The entropy relation](https://openstax.org/books/university-physics-volume-2/pages/4-6-entropy)
also determines the two reservoir ledgers. Quasistatic reversible adiabats do
not calculate the actual pressure history of rapid irreversible compression.

## Bypass heat leak and whole-device boundaries

A prescribed L≥0 joules per completed cycle goes directly from the hot to the
cold reservoir. It bypasses the working gas. The gas p–V path, leg ledger and
work therefore remain unchanged; L is neither gas heat nor frictional work.
For engine operation, the hot reservoir supplies H+L and the cold reservoir
receives H(T_c/T_h)+L. Efficiency is W_net/(H+L), no larger than the Carnot
ceiling. Total entropy production is L(1/T_c−1/T_h)≥0; L=0 gives exactly zero
in the reversible model. Reservoir heat changes divided by their absolute
temperatures agree with their signed entropy changes.

At 600/300 K, H=400 J gives 200 J rejected by the gas and 200 J work. With
L=400 J, whole-device transfers become the actual quiz's 800 J input and
600 J rejection, with 200 J work and 25% efficiency. Entropy production is
2/3 J/K. This is a physically valid parallel heat pathway, rather than an
invented Carnot topology made to fit arbitrary heat budgets.

In reverse operation, the gas extracts H(T_c/T_h) from the cold reservoir,
rejects H to the hot reservoir and needs work input H(1−T_c/T_h). The leak
reduces net cold extraction to H(T_c/T_h)−L and net hot delivery to H−L.
Positive useful cooling has a COP no larger than the reversible value.
At exactly zero net extraction COP is zero. With negative net extraction the
cold side is heated overall; useful refrigeration COP is unavailable, not
reported as a negative cooling performance. A sufficiently large leak can also
make useful heat-pump COP unavailable. The work and energy ledger remain valid.

If both heat exchangers are inside one kitchen boundary, hot delivery minus
cold extraction equals compressor work. The room gains that energy even with
an open refrigerator. This is a whole-room energy account; it does not solve
evolving room temperature, door airflow or the changing conditions of a real
open refrigerator. The reservoirs here remain at prescribed temperatures.

The first-law mode accepts signed Q and W_by as independent process budgets.
It reproduces 500−200=300 J, −150−(−400)=250 J, and an insulated work input
Q=0,W_by=−400 J giving ΔU=400 J. The latter explains ideal-gas warming without
heat transfer. No pressure, volume, entropy, absolute internal energy or cycle
path is inferred from these arbitrary budgets.

## Domains, controls and API

The engine/refrigerator controls have T_h=250…1200 K,
T_c=100…min(1100,T_h−10) K, n=0.05…1 mol, V_A=0.0005…0.01 m³,
H=10…min(2000,nRT_h ln8) J, L=0…2000 J/cycle, and leg progress 0…100%.
These joint limits enforce positive temperature, a finite nonzero reservoir
gap and hot-isotherm volume ratio at most eight. Numeric entries outside the
range clamp to its nearest endpoint; blank/invalid entries restore that
control's default within its current joint bounds. Numeric entry normalizes on
change, so clearing a field while typing does not prematurely rewrite it.
First-law heat and work each span −1000…1000 J. Visible notes state the bounds
and sign conventions. Native controls, focusable local scrolling regions,
target/reset buttons and numeric speech support keyboard use. Enlarge preserves
local plot scrolling; fit restores the responsive layout. The leg table scrolls
locally on mobile, keeping all signed values reachable.

The strict renderer contract is `physics-cycle-lab` with exactly
`{"scenario":"phys.3.thermo.cycle-entropy"}` on the actual `phys.3.thermo`
lesson. Load the new CSS and JS before the lesson registry, register
`window.PrimerPhysicsCycleLab.render(item,hooks)`, and include it in the
dedicated-renderer return list. Backend validation rejects extra props, unknown
scenarios and cross-lesson bindings. Both the window API and normal CommonJS
exports are provided; no file text is executed using `eval` or `vm`.

`build(raw)` exposes normalized `state`, four `corners` with `{name,V,p,T,U,S}`,
four `legs` with `{index,label,kind,reservoir,from,to,Q,Wby,deltaU,deltaS,
logVolumeRatio,points}`, analytic `current`, physical plot bounds, reservoir
heat/entropy and device metrics. V is m³, p Pa, T K, Q/W/ΔU J and S/ΔS J/K.
`stateAtLeg(raw,index,fraction)` returns the physical analytic state and signed
transfers since that leg's start. It rejects first-law mode, invalid leg indices
and fractions outside 0…1. Cycle state fields are `{mode,hot,cold,moles,volume,
hotHeat,leak,leg,progress,heat,work}`; mode is engine, refrigerator or first-law.
Inactive budget values do not affect cycle states. Engine-only total hot input
and cold rejection are null in refrigerator mode; refrigerator-only net cold
extraction and hot delivery are null in engine mode. This keeps exported
metrics tied to their declared device boundary. First-law builds expose only
their process energy account, not asserted gas states or legs.

## Verification and scope

The independent checker reconstructs R from SI-defining constants, derives
state coordinates from ideal-gas and polytropic relations, and numerically
integrates pressure dV with composite Simpson quadrature. It passes 1,645
cycle/first-law state combinations and 6,480 independent leg-work integrals.
All 121 states on each reviewed leg satisfy the gas law, energy law, adiabatic
invariant or isothermal condition. It covers joint-bound extrema, reversed
paths, endpoints, all signed reservoir accounts, zero/positive/tiny heat leaks,
Carnot bounds, zero/negative net refrigeration and the kitchen boundary.
The actual drawn polygonal loop's work agrees within a 6×10⁻⁵ relative display
approximation over the tested domain. Numerical integration of the physical
curves is checked much more tightly; these tolerances are not physical bands.

Sixty-eight mounted DOM states independently check actual SVG path coordinates,
loop area, corner/current markers, signed bars, active control visibility,
numeric speech, presets and exact reset. The optional `--browser` mode passed
142 states at 1440/390 CSS pixels, including native keyboard/numeric controls,
all presets, bounded distinct corner labels, speech, enlargement/fit and body
overflow. Desktop/mobile cycle and first-law screenshots were visually
inspected. It uses a fixed installed Chrome path or Playwright's bundled browser,
with an ephemeral loopback server and awaited resource cleanup. All three
focused pytest tests pass after root integration. Direct-renderer proof is in
the fresh private directory printed by the checker as
`primer-browser-qa-cDyf6u/cycle-browser-proof.json`.

The actual `/#/node/phys.3.thermo` route passed 172 cycle-activity states and
102 root-owned companion-3D states across 1440/390 CSS pixels. Its curriculum
API exposed the strict cycle binding and `carnot-state-path` companion family.
The actual 2D controls exercised all operating modes, native keyboard extrema,
numeric entry, requested gas legs/endpoints/interior states, all presets,
reset and fit/enlarge. The 3D checks exercised both directions, all four native
leg selections at progress 0/1/50/99/100, every temperature/heat extremum,
Reset model and camera rotation/ArrowUp/Home. Every 121-point process curve and
analytic selected state matched independent ideal-gas/polytropic coordinates
in the declared native scales: 0.005 m³, 200000 Pa and 1000 K per coordinate unit.
Visible graph labels stayed in frame without overlap, and neither route layout
overflowed its viewport.

Native 3D choice values are strings, matching the DOM select value. The final
route check independently records each requested control state, asserts the
native select and the scene's actual numeric leg equal the requested leg, then
derives expected process points from that requested state. This guards against
a silent default fallback being used as its own expected answer. The proof
includes requested and actual leg records for 0, 1, 2 and 3 in both directions.

Actual Read aloud queues recombined exactly to current visible numeric content
in all three 2D modes and the 3D companion. The reviewed 2D engine/refrigerator/
budget states used 824/1011/218-character chunks. The 3D text used two chunks,
with longest 1117 characters. This verifies queue text, not acoustic rendering.
The final ignored route proof is
`../cycle-route-proof-20261010-vJzbTF/proof.json` relative to the checkout root;
its directory contains desktop/mobile 2D and 3D screenshots. The reproduction
script is `../cycle-route-qa-20261010.cjs`. Seven served JS/CSS asset hashes match
the source bytes reviewed in that successful run, with no runtime errors or
failed HTTP responses. The dedicated browser closed; the shared root-owned
QA server was deliberately left under root's control. These checks used the
disposable local reader, not a production account.

No quantities here
constitute a realistic engine calibration or a solved finite-rate irreversible
process. Thermal/material mixing, microscopic entropy, other cycles and broader
thermodynamic lesson coverage remain incomplete. This targeted activity does
not finish the larger mathematics/physics/clinical goal or grant clinical,
anatomical or authenticated-production approval.
