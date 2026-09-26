# Lesson media and 3D across the Primer

Every one of the 558 lessons across all 19 fields has its own explanatory
illustration and an interactive 3D companion. Existing interactive exercises
remain available. The lesson's leading illustration loads eagerly; later lesson
images and gallery images load lazily. The keyboard-accessible image viewer
provides enlargement and restores focus on Escape.

## Removed: generated contextual scenes

Until 26 September 2026 every lesson also showed one of 30 AI-generated
photorealistic "contextual scenes" (for example an ultrasound room for
radiology or a desk of geometric solids for mathematics), shared across a
field. They did not match the authored plates or the source figures and taught
nothing about the lesson, so they were removed with their catalog
(`data/module-photographs.json`), 60 WebP files and generation prompts. The
generated shoulder-bone plate in the radiology reference was removed for the
same reason. The lesson-media validator now rejects the `photograph` kind.

## Spatial companions

The general curriculum and imaging foundations contain 448 added spatial companions across 41 shared object
families. Fourteen existing
specialized general-subject 3D activities remain in place. All 96 Radiology
modules expose their existing anatomical or schematic 3D reference, in
addition to their existing exercises. There are 561 spatial entries and 816
interactive model entries in the complete gallery, including additional
activities within a lesson.

`data/module-models.json` binds general lessons to curated object families.
`web/spatial-module-objects.js` builds real 3D geometry using the existing local
projection engine. Controls change the objects, and mouse, touch and keyboard
controls rotate and zoom the view. Models distinguish explanatory geometry
from physical study contexts: a book or an experiment setup provides a
concrete object for an abstract lesson without claiming to simulate its
meaning, historical evidence, or human behavior. Readouts describe the
chosen relationship and the limits of each representation.

The implementation needs no remote model CDN or new graphics dependency.
Detailed Radiology meshes retain their existing source attribution and load
on demand. The reporting desk reuses its existing model pane without mounting
duplicate anatomical viewers.

## Integration and checks

`primer/module_media.py` appends the new media as the curriculum loads.
`primer/curriculum.py` validates local image dimensions and exact
lesson/model bindings. Runtime additions stay out of the compact curriculum
graph and navigation responses. The answer-free visual catalog lists lesson
plates and models, with separate illustration, model and 3D filters.

Useful verification commands:

```sh
.venv/bin/python -m pytest -q tests/test_module_media.py tests/test_api.py tests/test_primer.py
.venv/bin/python tools/check_model_coverage.py --require-complete
node tools/check_module_models.js
NODE_PATH=/path/to/playwright/node_modules node tools/check_module_media_browser.cjs http://127.0.0.1:8781
```

The browser checker requires an isolated development database because it
creates a QA reader. It checks complete API coverage, local image decoding,
gallery filters, representative lesson routes, model parameters, rotation,
reset, keyboard image enlargement and mobile overflow. Image presence and
working controls alone do not establish subject-matter accuracy.

Historical baseline before the pathway expansion, verified locally on 2026-09-23: 32,041 Python tests passed, with two existing
fixture skips. The final Radiology photo-selection adjustment also passed all
15 media tests. That baseline catalog contained 444 photograph placements, 444 original
diagrams, and 693 interactive entries, including 447 spatial entries.

The browser sweep passed 63 actual lesson routes covering all 41 new families
and all 17 original spatial scenes. Keyboard, mouse and touch controls,
camera/model reset, image enlargement, focus restoration, gallery filters and
390-pixel mobile layouts passed without uncaught JavaScript errors. All 22
photographs decoded at both resolutions, and the Radiology Foundations image
was verified in its lesson. Served JavaScript/style hashes matched the
workspace. QA used an isolated reader database with encyclopedia summaries
stubbed; verification concerned the local lesson media rather than external
article availability.

Browser QA now prints a generated `EVIDENCE_DIRECTORY` for each run; see [browser-qa.md](browser-qa.md).
