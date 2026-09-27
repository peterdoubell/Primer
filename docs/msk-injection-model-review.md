# Joint-injection regional 3D reference correction

27 September 2026. The injection investigation previously inherited the
`rad.5.ir-basics` vascular-access schematic (family `access`, vessel focus).
That schematic did not represent its named joint targets.

The investigation now offers six regional references: shoulder, elbow, wrist
and hand, hip and pelvis, knee, and ankle and foot. They use the existing
registered Z-Anatomy source meshes with their original attribution and
limitations. The selector replaces and disposes the previous viewer. The
underlying general IR lesson retains its vascular-access teaching schematic.

These are regional orientation references, not thirteen validated procedural
target models. The UI explicitly excludes needle simulation, injectate,
patient-specific paths and clinical access-safety claims. Region-specific notes
retain missing capsule, recess, bursal, tendon and neurovascular requirements.
No mesh was invented, mirrored, refitted or relabelled as a procedural target.
No structure-level fidelity binding or clinical approval was added.

API checks passed (121 tests); all 24 investigation tests passed after correcting
a test assumption about the deliberately investigation-specific default title.
JavaScript syntax validation passed. Browser checks waited for actual rendered
canvases for all six regions, verified one viewer at a time, posterior-view
control, mobile switching at 390 pixels without horizontal overflow and no
console errors. [Loaded-region evidence](msk-injection-model-review/loaded-regions.json)
records the displayed triangle counts; these counts do not establish accuracy.
The temporary server/tab were closed and viewport reset.

The [fidelity snapshot](msk-verification-injection-model-2026-09-27.json)
retains all 5,202 requirements and readiness false. Regional availability is
not complete representation of the 225 injection requirements.
