# Independent SPL viewer verification

The Python checker reconstructs each exact original NRRD from its archived
header and unchanged compressed payload. It verifies the original SHA-256 and
Git blob identity before independently deriving pixel planes, display-window
values and categorical overlays. The MRI's original 0.75 mm grid and the label
volume's original 1 mm grid remain separate. The label array is signed Int16;
codes above 255, including the fornices and mammillary bodies, are preserved.

```sh
python tools/check_spl_limbic_viewer.py
node tools/check_spl_limbic_viewer.cjs
```

Python needs NumPy. Node needs Playwright; in this workspace it is available via
`NODE_PATH=/Users/peter/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules`.
The Python command compares the recomputed source oracle with the saved receipt.
Use `--write-proof` explicitly to regenerate the fixed output in this directory.
The Node command starts its own static server on an ephemeral loopback port,
checks the actual browser, and closes the browser and server when finished. It
does not write proofs without `--write-proof`.

The standalone proof checks complete canvas RGBA hashes across native T1/T2,
all three planes and all twelve selected labels. It includes original-grid
focus, native first/middle/last slices, MRI-only and all-label overlays, exact
window endpoints, zero-centred and fully clipped windows. Pointer probes use
the centre of the actual displayed pixel. Invalid windows hide the image.

For both source representations, the checker reads all 24 meshes back from the
GPU. Position and index hashes must match the manifest, and vertex-shader
transform feedback must recover the original RAS positions bit for bit. It
checks camera projection of every source vertex and nonblank actual GPU
framebuffers for each selected structure. It also exercises keyboard rotation,
zoom, fit views and enlargement at 390 and 1440 px. Failed metadata, MRI,
labels, surfaces and corrupt MRI responses must clear the affected display and
recover through the visible retry controls.

To check the main app, first start `tools/start_optics_reader.py` with a private
fixture path outside the repository. That launcher creates a fresh synthetic
learner database, disables Turso, and binds only to loopback. Then supply that
private fixture on stdin:

```sh
node tools/check_spl_limbic_viewer.cjs --reader --write-proof < /tmp/private-spl-fixture.json
```

The reader checker accepts only a loopback HTTP URL. It verifies authentication,
private caching, current startup-bundle bytes, viewer-file hashes and actual
payload-response hashes. Images, model, walkthrough and lesson entry points are
checked in brain anatomy, epilepsy MRI and dementia MRI. Existing reporting
guides and the separate HippUnfold reference remain present. This test uses
synthetic local learner data and makes no production writes. Stop the fixture
server after the reader test.

The final reader receipt contains all 24 entry-point cases. Fifteen completed
cases were retained when a test-harness scrolling adjustment was needed for a
fixed enlargement control in a partly visible outer iframe; the remaining nine
were then checked. The explicit `--resume` option accepts only the fixed partial
receipt and requires identical viewer, registry, JavaScript and CSS pins. Normal
execution checks all 24 cases afresh. No force click or direct invocation of a
private viewer handler is used to bypass the visible controls.

`standalone-proof.json` and `reader-proof.json` are the current acceptance
receipts. `findings.json` records the corrected defects. The partial proofs,
overflow diagnostic and earlier full outlier-viewport screenshot are retained
as development/finding evidence, not as current acceptance results. The focused
outlier disclosure, MRI and probe screenshots show the final ordinary action.

These are source-fidelity and implementation checks. The original publisher
surfaces differ from the categorical labels, especially at the fornices; that
comparison is not a patient finding. The retained isolated left-fornix source
voxel is not independently established as biologically continuous tract anatomy.
No clinical approval, complete reporting anatomy, normal population range,
patient registration or separately labelled CA/subiculum anatomy is implied.
