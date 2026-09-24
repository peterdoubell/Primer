# Registered anatomical reference meshes

The radiology viewer now supports eleven real-mesh anatomy sets: shoulder, elbow, hip, knee, ankle / proximal foot, wrist, heart / coronary arteries, prostate and neighbouring organs, renal tract, liver segments, and brain / ventricles. The source is the official BodyParts3D 4.0 archive, under its current CC BY 4.0 license (updated February 2025), rather than procedural primitive anatomy.

There are 96 selectable structures assembled from 147 source components, containing 660,024 triangles and 16,941,672 bytes of packed geometry. Shared structures are reused between regions. Meshes load only when opening the relevant viewer; shoulder geometry is about 0.96 MB, coronary 1.98 MB, liver 3.49 MB and brain 7.62 MB. Browser requests cache loaded meshes. The renderer uses native WebGL without a third-party rendering dependency.

All registered source coordinates are retained. Bone and selected muscle / tendon layers can be shown separately or together. Clicking a named structure highlights it; Isolate reframes the selected structure. Anterior, posterior, lateral and superior views, pointer rotation, wheel / pinch zoom and keyboard controls are available. Regional long-bone cropping is a display operation and does not alter the source mesh files. GPU resources are released when the SPA removes a viewer. A readable dataset link is shown if WebGL is unavailable.

Source limitations remain explicit in the UI. The prostate surface has no internal PI-RADS zones. The MSK selections have no labral, meniscal, cartilage or complete ligament geometry. The brain contains source cerebral surface and internal components; ventricular surfaces are separately selectable. No disease, flow or MR signal is simulated. Parts are individually labelled and bilateral organs retain right / left labels.

## Implementation

- `web/radiology-detailed-anatomy.js`: `window.PrimerDetailedAnatomy.render({family})`, `supported(family)` and `families`. Returns a DOM element with a `dispose()` method.
- `web/anatomy/bodyparts3d/manifest.json`: mesh-to-anatomical-concept mapping, source identifiers, file hashes, license, regional layers and geometry bounds.
- `web/anatomy/bodyparts3d/ATTRIBUTION.md`: attribution, source provenance, license and adaptation description.
- `tools/build_detailed_anatomy.py`: reproducible archive selection / conversion; no mesh geometry invented or deformed.
- `tools/check_detailed_anatomy.cjs`: browser checks of nonempty rendered geometry, rotation, per-layer structure visibility, isolation, combined view, mobile overflow and JavaScript errors.

The browser suite was run against the local preview. Screenshots for each family, combined layers and the mobile shoulder viewer are generated in the requested output directory. Manual visual inspection confirms recognizable joint surfaces / anatomical relationships, individual wrist bones, liver segment surfaces, and cortical / ventricular geometry. It does not substitute for expert clinical validation of the source dataset.
