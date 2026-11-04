# Particle conservation and beta-decay momentum

The `phys.4.particles` activity replaces three Boolean outcomes with computed
additive quantum numbers and rest-energy budgets. A compatible channel opens
an interactive three-dimensional, orthographic momentum triangle for a neutron
initially at rest. The existing illustration, ten assessment questions, goals,
article references, pacing and separate detector-context companion are retained.
This is one improvement to the particle lesson, not a complete Standard Model
simulation or evidence that the whole Primer fidelity objective is achieved.

## Inputs and physical scope

Electron, proton and neutron rest energies use the central 2022 CODATA values
in [NIST SP 961, May 2024](https://physics.nist.gov/cuu/pdf/wall_2022.pdf), page 1.
The source values, units and published uncertainties are recorded in
`prototype/mass-source.json`. Rest energies are measured inputs, not exact
constants; uncertainty correlations are not propagated. The antineutrino is
approximated as massless. No nuclear binding, weak matrix element, rate, spin
correlation, detector response or measured event is supplied.

Charge and baryon number are stored in integer thirds. Proton `uud` and neutron
`udd` totals are computed from valence quark quantum numbers; they are not
spatial quark positions or complete nucleon wavefunctions. Nucleon masses are
measured inputs, not sums of quark rest energies. Electron-lepton numbers
refer to this elementary decay bookkeeping; neutrino mixing is not modeled.
A channel passing these number and energy checks is not thereby proven allowed
by every interaction or spin selection rule. The proton-to-positron-and-neutrino proposal fails baryon number even though
charge, electron-lepton number and the rest-energy budget pass. The bare proton
beta-plus example
balances these quantum numbers but fails its rest-energy budget. Nuclear
beta-plus decay requires nuclear mass differences and is outside that example.

## Kinematics and display

The following equations use natural units, c = 1. Rest energies `N`, `P`, `m`
are in MeV; momentum components are displayed in MeV/c:

- `Tmax = ((N-m)^2-P^2)/(2N)`; the implementation factors the numerator.
- `Ee = m+T`, `pe = sqrt(T(T+2m))`.
- `Eν = N(Tmax-T)/(N-Ee+pe cosθ)`.
- The proton momentum is minus the sum of the electron and antineutrino
  momenta, and its energy is `sqrt(P^2+|pp|^2)`.

The input fraction selects an energy between zero and `Tmax`; it is not a
sample from a predicted spectrum. Azimuth and opening angle select a possible
configuration, not a predicted angular distribution. The electron direction
sets the positive x-axis. Every displayed spatial component is a momentum
component. The triangle is arranged head to tail, not as particle tracks.
All momentum axes have the same gain, 180 SVG units per MeV/c, with a labeled
1 MeV/c scale. Yaw and pitch are orthographic camera angles. Arrowhead size is
a display aid; shaft endpoints encode the calculated momenta.

At zero electron momentum or zero antineutrino energy no corresponding direction
is assigned, and angle controls are disabled. The zero-antineutrino endpoint is
explicitly a limiting configuration rather than a finite-energy three-body event.
Collinear vectors have no unique momentum plane, so azimuth and “Face momentum
plane” are disabled there. The analytic stationary-proton configuration occurs
at `T=(N-P-m)^2/(2(N-P))` and `cosθ=-1`. A proton direction below the conservative
floating-point resolution `64 Number.EPSILON (N+P)` MeV/c is not drawn. This is a
numerical threshold, not a measurement uncertainty; the computed residual is
retained in the momentum sum.

## Verification

The tools directly import the shipped core and ledger through their CommonJS
exports, rather than evaluating source text or using a second implementation.
The same modules expose their APIs to the browser. Independent checks use Fraction arithmetic and Decimal
arithmetic at 50 or 60 digits:

- `tools/check_particle_ledger.py`: 516 channels, exact additive numbers and
  independent rest-energy budgets.
- `tools/check_particle_core.py`: 120 configurations, energy and momentum
  conservation, mass shells and endpoint limits.
- `tools/check_particle_edges.py`: 252 angular and endpoint configurations,
  including the analytic stationary-proton state.
- `tools/check_particle_app.py`: actual authenticated reader with temporary
  synthetic data, phone and desktop controls, rejected channels, numerical
  limits, four independent mounts, speech, disposal and two route reopens. Four controlled stale-response checks
  cover late successes and failures after navigating to another lesson.
- `tools/check_particle_rendered.py`: independent kinematics and projections
  compared with the actual reader's SVG shaft endpoints and scale.

The browser proof does not write production learner data or claim a verified
production authenticated-reader session. Historical source evidence is checked
through a pinned, exact inverse in `runtime-inverse.json`. This restores bytes
for older proofs only, grants no approval and rejects unrelated edits by default.
Current behavior is checked independently as described above.

The `prototype` directory preserves the separate development experiment.
Canonical current-reader evidence is in `reader`, and current numeric evidence
is at this directory's root. Prototype counts and integration flags are not
substitutes for current-reader proof.

## Navigation correction

A pre-fix browser capture in `diagnostics` shows a condensed-matter page
replacing the particle page after the URL had returned to particles. The generic
loader cleared the shared page on an outdated response. `renderNode` now uses
the existing route-aware guard, which checks route generation, hash and page
attachment before handling either a response or an error. Controlled delayed
responses now verify that the current particle page remains intact.

## Remaining scope

A complete particle illustration set still needs a verified Standard Model
inventory, spin/interaction representations, mediator-range treatment, pion
photon-decay geometry and calibrated detector-response examples. Other math,
physics and radiology modules require their own fidelity evidence. No clinical
approval, complete reporting coverage or whole-goal completion is claimed here.
