# Manifest loading failure correction

Before this correction, an injected HTTP 503 left plane/class controls active, hid the retry button and produced two unhandled exceptions on plane/class changes. `reproduced.json` records those observed failures. `viewer-before.js` and `viewer.patch` preserve the exact before/after boundary.

The viewer now disables its controls before requesting metadata. HTTP/network failures, invalid JSON and an invalid metadata schema retain disabled controls and hidden canvases, show the request error, and enable “Retry reference load”. A valid retry populates the eight class options/legend entries once, enables controls and loads source data. Synthetic events are also guarded while no manifest is available. The existing source retry remains available for subsequent image loading failures.

`failure-proof.json` contains four injected metadata failure/recovery cases plus the existing corrupt image/mesh failure/recovery checks, all with zero page errors. Each metadata case checks the pending state, failed state, safe synthetic events and a successful interactive recovery.

No binary payload, coordinate, mesh index or display algorithm changed. `unchanged-rendering.json` verifies exact pre/post code identity for eight source indexing, world coordinate, image, shader and mesh rendering functions. Full raw and HTTP-gzip browser checks were rerun against this final viewer and saved in the `raw/` and `encoded/` directories.
