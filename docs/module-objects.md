# Whole-curriculum 3D study objects

`data/module-models.json` binds all 348 non-radiology lessons to an explicitly
selected physical object or mathematical example. Existing lesson-specific
spatial scenes take precedence; 334 lessons receive a new companion. The 41
families are shared constructions, not 334 different physical simulations.
The explicit source mapping is `tools/generate_module_models.py`.

`web/spatial-module-objects.js` reuses the existing local `PrimerSpatial`
renderer. Meshes, prisms, spheres and lines occupy real three-dimensional
coordinates. The renderer already supplies rotation, zoom, keyboard controls,
touch/pointer dragging, reset and accessible readouts. No network asset,
continuous animation, WebGL or new graphics dependency is required.

Companion props are exactly `{scenario: 'module.' + node_id, family, context,
mode, lesson}`. `PrimerModuleObjects.ensure(item)` registers the scene once;
subsequent attempts to reuse that identifier with changed binding data fail.
The backend validates the complete props against the manifest. Original
spatial models and other interactive activities are preserved.

`mode: model` marks a direct example, such as equal blocks, a stated function
surface, a pendulum, a molecular geometry or a coordinate globe. Even a direct
example has finite scope: the surface is the displayed formula, the pendulum
is a static position, and the lattice is simple cubic.

`mode: context` identifies a physical study setting for concepts without a
faithful small 3D simulation. Examples include a book for interpreting text,
a discussion table for social questions, a printing press for textual
transmission, a detector for QFT's connection to measurement, and a classical
two-slit optical bench for discussing quantum experiments. These objects do
not encode truth, fairness, consciousness, cultural identities or theoretical
predictions in their geometry. Every readout is prefixed with its exact lesson
context, and every model explains its simplifications.

The reference configurations are grounded in established descriptions:

- [NCBI: alternative DNA conformations](https://www.ncbi.nlm.nih.gov/books/NBK6545/)
  supports the right-handed B-DNA example at roughly 10.5 pairs per turn.
- [OpenStax: molecular structure](https://openstax.org/books/chemistry-2e/pages/7-6-molecular-structure-and-polarity)
  supports the water, carbon-dioxide and tetrahedral methane examples.
- [OpenStax: mathematics of interference](https://openstax.org/books/university-physics-volume-3/pages/3-2-mathematics-of-interference)
  supports path-difference interference and the small-angle fringe-spacing
  comparison. The visual calculates equal-amplitude intensity from the actual
  path difference; it omits the single-slit envelope and intensity falloff.
- [CERN: how CMS detects particles](https://cmsexperiment.web.cern.ch/news/how-cms-detects-particles)
  supports the sequence of sensing layers. The study object is a generic
  arrangement, not a reconstruction of CMS or real collision data.

Run `node tools/check_module_models.js` or `pytest -q tests/test_module_models.py`.
The checker verifies all 348 bindings, preservation of existing scenes,
registration isolation, all 84 controls, deterministic finite geometry and
invalid-value fallback. Numeric checks inspect geometry independently for
counts, function surfaces, pendulum lengths/heights, lattice sites, molecular
angles, right-handed DNA, orbit radii and globe coordinates. Browser evidence
is produced separately by the whole-module-media browser checker.
