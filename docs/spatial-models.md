# Interactive spatial explanations

The mathematics/science rollout and cross-subject extension add 14 lesson-specific
3D activities and three 2D concept activities to the existing 70 models: 87 models
in total. All 432 lesson illustrations remain available. The Visual Gallery lists
519 items and has an **Interactive 3D** filter.

This is the first spatial rollout, not completion of the curriculum-wide
[visual-quality goal](visual-quality-goal.md). Remaining cross-subject findings
and suitable next models are recorded in [the audit](cross-subject-visual-audit.md).

## What the scenes explain

| Lesson | Explanatory interaction |
| --- | --- |
| Area, Perimeter and Volume | Count unit cubes, vary dimensions and separate layers; distinguish base area, perimeter and volume. |
| Vectors | Compare the sum, dot product and perpendicular cross product as the second vector changes. |
| Multivariable Calculus | Inspect an exact bowl surface, its tangent plane and the error in a local linear approximation. |
| Topology | Stretch a sphere or torus without changing the number of handles; switching surfaces is explicitly not a continuous deformation. |
| Electrodynamics | Rotate mutually perpendicular electric/magnetic fields and propagation; change phase and polarisation. |
| Solid State Physics | Compare simple, body-centred and face-centred cubic cells; distinguish visible boundary atoms from their fractional contributions. |
| Cell Biology | Open or close a schematic cell, separate organelles and inspect structures and functions. |
| Molecules and Compounds | Compare water, ammonia and methane, with bond-angle readouts and optional lone-pair markers. |
| Organic Chemistry | Compare reflected tetrahedral molecules with distinct or repeated substituents; distinguish object rotation from camera rotation. |
| Quantum Chemistry | Inspect schematic s/p orbital regions and nodal planes; phase is not electrical charge or an electron trajectory. |
| Why Seasons Happen | Move Earth around a circular orbit with a fixed tilted axis; compare hemispheres and daylight. |
| Earth Science | Open a wedge through physical layers; distinguish the solid mantle, liquid outer core and solid inner core. |
| Color and Composition | Keep a cube's physical size constant while changing depth and focal distance; compare exact perspective projections and rays. |
| Quantum Computing | Vary a pure qubit's polar angle and relative phase; compare Z- and X-basis probabilities on a Bloch sphere. |

The companion `concept-lab` renderer adds quantitative supply/demand, two syntactic
attachments of one sentence, and necessity/possibility on an editable accessibility
graph. These are 2D because depth would not improve their explanations.

## Implementation and limits

`web/spatial-models.js` projects real 3D coordinates into SVG, using orthographic
projection and depth-sorted mesh faces, spheres and line segments. It has no
external graphics library, WebGL requirement, network dependency or continuous
animation loop. Scene definitions are split between `spatial-math.js`,
`spatial-molecular.js`, `spatial-physical.js` and `spatial-cross-subject.js`.
The companion 2D scenarios live in `concept-models.js`.

This is an explanatory renderer, not a physical simulation or photorealistic
surface engine. Transparent surfaces use painter-style depth sorting. Molecular
sizes, electron-pair markers, orbital boundaries and cell structures are
explicitly schematic; model notes identify the limits. Numerical readouts use
the lesson formulas, not measurements of rasterised geometry.

Labels use bounded screen-space placement and leader lines where necessary.
Framing centres the initial geometry; an oversized parameter state is fitted
when needed and the orientation readout says “Auto-fit”. Explicit zoom may crop
the scene. Whole curves are split into segments before depth sorting so a
marked loop can pass behind a surface correctly.

Every model supports parameter controls, pointer/touch dragging, arrow-key
rotation, plus/minus zoom, Home/reset-view and a full model reset. Camera buttons
provide alternatives to dragging. Controls have text labels, the scene has a
text readout, and user changes are announced through a polite live region.
Touch gestures within the canvas rotate it; scrolling remains available outside
the canvas. There is no autoplay.

## Verification

Run the mathematical/scientific geometry checks without a browser:

```sh
node tools/check_spatial_models.js
python -m pytest -q tests/test_spatial_models.py
python tools/check_curriculum_illustrations.py
```

The geometry checker exercises 14 exact curriculum bindings, 32 meaningful
controls and 279 finite, deterministic builds, including scientific invariants
and invalid inputs. It also ensures the existing 70 models remain present.

For end-to-end verification, run an isolated dev server/database and provide
Playwright through the normal Node module resolution path (or `NODE_PATH`):

```sh
node tools/check_spatial_browser.cjs http://127.0.0.1:8768
```

The browser checker opens a model through the actual gallery, visits all 14
lesson routes, changes 71 parameter states, checks combined extrema and camera
changes, and measures geometry/label bounds. It checks desktop and
390-pixel mobile layouts, real mouse and touch dragging, keyboard controls,
exact reset behaviour, overflow and browser exceptions. It saves per-scene
screenshots and a `results.json` report. Screenshots still need human/visual
review: passing bounds or interaction tests alone does not establish a good
explanation.

Verified on 2026-09-05: all 14 scenes passed the browser checker, including
measured geometry/label states, desktop/mobile mouse and touch interactions,
and zero JavaScript exceptions. The report includes SHA-256 hashes confirming
that the browser tested the current renderer/application/style files.
Default desktop/mobile screenshots were visually reviewed, with additional
checks of alternate molecular shapes. The earlier full Python run had 858 passes, two
skips and one stale Seasons media-count expectation; after correcting that
expectation, the affected API test plus spatial and reader-picture tests passed
(28 tests). The fresh full-suite run including the cross-subject extension passed
on 2026-09-05: 894 passed, two skipped, in 811.55 seconds. Two warnings concern
Python 3.9 reaching end of life. This is evidence for this rollout, not a completed
all-subject audit. Subsequent static illustration edits receive separate focused checks.

Cross-subject verification also runs independently:

```sh
node tools/check_cross_subject_models.js
python -m pytest -q tests/test_cross_subject_models.py
node tools/check_concept_browser.cjs http://127.0.0.1:8768
```

On 2026-09-05, the five new models passed 32 focused Python tests and 1,117
deterministic builds. All three concept models passed browser checks (82 tested
parameter/configuration states in total), with keyboard operation, exact reset,
current-source hashes and no JavaScript exceptions. Desktop/mobile screenshots
were visually reviewed, including both syntactic attachments. The capture helper
centres drawings so sticky navigation does not obscure screenshot evidence.

Reader-image commands:

```sh
node tools/check_reader_pictures.js
python -m pytest -q tests/test_reader_pictures.py
```

These protect accessible picture names, keyboard activation and removal of
failed images without hiding healthy siblings or useful surrounding text.

Browser QA now prints a generated `EVIDENCE_DIRECTORY` for each run; see [browser-qa.md](browser-qa.md).
