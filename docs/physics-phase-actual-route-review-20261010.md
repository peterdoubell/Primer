# Actual phase-change lesson route review — 2026-10-10

The integrated phase activity passed checks on the actual Primer routes
`/#/node/phys.2.matter` and `/#/node/phys.0.hot-cold` at 1440 and 390 CSS pixels.
This review used an isolated QA-only server at `127.0.0.1:8901`, disposable
database `/tmp/primer-phase-route-qa-20261010.db`, QA sign-in and learner profile,
and a dedicated Chromium session identified as `phase-route-20261010`.
The running application source was `.research/release-pulmonary-20261007`.

| Actual route | Width | Phase states checked | Phase 3D states checked |
| --- | ---: | ---: | ---: |
| `phys.2.matter` | 1440 | 90 | 30 |
| `phys.0.hot-cold` | 1440 | 90 | — |
| `phys.2.matter` | 390 | 90 | 30 |
| `phys.0.hot-cold` | 390 | 90 | — |

The actual curriculum API returned the strict phase bindings for each lesson.
Matter also returned its `module.phys.2.matter` companion with family
`phase-enthalpy-path`. Both lessons retained their existing concept activities;
the hot/cold lesson retained its separate thermal-contact activity. The added
models mounted through normal lesson navigation, rather than a synthetic test
page. The four backend/shell/independent phase pytest tests also passed after
integration.

## Phase activity evidence

For all six starting samples, native keyboard Home/End exercised the mass and
signed-heat controls at their allowed endpoints. Actual numeric heat entry
selected h=0, 167, 334, 752.6, 1880.6 and 3008.6 kJ/kg from each starting state.
This includes heating and cooling across complete melting and vaporization
intervals, pure transition endpoints, and half ice/liquid and half liquid/vapour
states. Out-of-range numeric heat clamped to the stated upper endpoint; blank
entry restored zero supplied heat. Every phase-target button, the condensing
vapour preset, enlargement/fit and reset was exercised. Reset restored each
lesson's exact starting mass, phase and zero heat input.

The check independently reconstructed the calorimetric state and signed
stage-energy overlaps from separate decimal constants. It compared those
physical values with the actual SVG heating/cooling segments, current-state
marker, phase-mass bar widths/origins and signed ledger bar lengths/origins.
The numeric temperature readout agreed with the current energy-controlled
state. SVG text stayed within its declared view boxes, and the document width
stayed within the viewport in fit and enlarged modes. Enlarged SVGs were at
least 660 CSS pixels wide inside local scrolling viewports.

The actual Read aloud button queued the current numeric heat, temperature,
phase masses/fractions, enthalpy change and equation. Speech chunks recombined
exactly to the visible readout plus equation; each phase case used one chunk,
526 characters in the reviewed condensing state. This verifies the submitted
speech text and queue behavior; voice pronunciation and acoustic quality were
not assessed.

## Phase 3D companion evidence

The actual matter companion was checked in each of its five equilibrium
intervals at progress 0, 1, 50, 99 and 100 percent. Its full five-segment path
and selected-state world coordinates agreed with h/1000, T/100 and liquid mass
fraction. The selected marker's actual SVG projection and radius were
independently reconstructed from those calibrated coordinates, the visible
camera angles, initial framing and current fit scale. All reviewed text labels
stayed in frame and did not overlap.

Reset model restored the exact default interval, progress, readout, view and
rendered geometry. Rotate right and keyboard ArrowUp changed the view; Home
restored the exact initial camera without changing the selected sample. The
companion's actual speech button queued its title, instructions, numeric state
and scope note; its two chunks recombined exactly, with a longest chunk of
1,139 characters. Hot/cold has no phase 3D companion; that column is outside
its actual binding rather than an omitted test.

Four phase-card screenshots and two 3D-canvas screenshots were visually
inspected. The mobile element screenshots include the existing sticky Primer
header over the card's top edge during screenshot scrolling; that capture
layering is not evidence of clipped SVG content. The mobile numerical controls,
stacked graphs and scrolling enlargement were exercised separately.

## Traceable proof and scope

The ignored proof is
`../phase-route-proof-20261010-ua0FGT/proof.json`; its directory also contains
the six screenshots. The reproduction script is
`../phase-route-qa-20261010.cjs`, outside this checkout in the ignored research
directory. Proof records actual API bindings, route/viewport counts, exact
speech recombination, and matching served/local SHA-256 hashes for
`physics-phase-lab.js`, `physics-phase-lab.css`, `lesson-models.js`,
`spatial-models.js`, `spatial-module-objects.js`, `app.js` and `styles.css`.
There were no browser runtime errors or failed HTTP responses in the successful
run.

The owned Chromium process closed after the checks. The owned Uvicorn process
65384 completed its shutdown, and a subsequent connection to port 8901 failed,
confirming the QA listener was closed. No shared application code was changed,
and no commit, push or deployment was performed by this route review.

No release blocker was found in these integrated phase examples. The scientific
assumptions and remaining lesson requirements in
[the phase-change fidelity review](physics-phase-change-fidelity-review.md)
still apply. This local authenticated QA does not establish authenticated
production delivery, full states-of-matter coverage, molecular/volume fidelity,
whole-physics approval, clinical/radiology accuracy or completion of the broader
user goal.
