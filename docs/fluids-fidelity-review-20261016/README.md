# Fluid mechanics: models and evidence

This work addresses the ten authored questions in `phys.4.fluids` and their necessary physical assumptions. The original Venturi illustration and quantitative Venturi activity remain in place. The companion workbench provides nine independently checked stations; its presence alone does not establish complete lesson coverage.

`requirements.json` maps every question to governing equations, units, applicability and concrete visual/numerical evidence. `coverage.json` records what remains unproven. The external articles listed by the lesson have not been exhaustively reviewed.

## Teaching corrections

`teaching-corrections.json` retains every original and revised field. The corrections distinguish available hull capacity from current displaced volume; specify the equal-density, quasi-steady model used for a settling-time comparison; remove the assumption that a plume must accelerate as it rises; and state the assumptions behind the ideal suction-height bound. The two short-answer keyword sets were also corrected after independent review showed that the revised model answers could lose marks against the old keywords. The existing grading function now gives both complete model answers full credit in the focused integration check.

The other six authored questions, the ten-question count and the existing media are retained. `runtime-inverse.json` and `tools/fluids_runtime_compatibility.py` reconstruct exact earlier runtime bytes for historical evidence. That reconstruction does not validate any new physics, rendering or clinical claim.

## Source and model boundaries

The visualizations, code, explanations and revised questions are original work informed by physical laws and the references in `primary-sources.json`. No OpenStax text, assessment or image is copied. Its currently displayed noncommercial license must not be confused with older licensing assumptions.

The declared ideal models do not by themselves establish ship stability, flooding dynamics, general unsteady particle settling, separated or stalled wing flow, or turbulent transition. A plume scaling plot describes its specified far-field regime; it is not a simulation of eddies or an onset predictor. Native anatomical source work is tracked separately and is not evidence for this physics lesson.

## Verification status

The focused integration checks verify media preservation, scenario validation, coordinated question/keyword changes and exact historical reconstruction. Independent numerical review passes 91 requests using collocation, adaptive ODE and pressure-integral oracles. Independent browser review passes 68 cases, including impossible-volume rejection, on 390/1440 px viewports. The actual authenticated lesson reader passes 92 states and 18 speech checks, with preserved media, exact startup bytes, invalid-domain recovery and no quiz leakage, page errors, CSP violations or horizontal overflow. These runs use isolated synthetic data; no production learner data is used.

`implementation-index.json` pins the implementation, core and standalone browser evidence. `independent-review/final-review.json` records defects found and their resolution. `reader/proof.json` records the actual lesson flow. `coverage.json` keeps each accepted model separate from excluded or unverified physics. The complete regression and release checks remain separate gates.
