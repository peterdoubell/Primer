# Source anatomy release — 27 September 2026

This release integrates the source-backed MSK galleries, regional anatomy and prenatal sequence with production reporting walkthroughs. The production removal of generic AI scenes is retained.

Source anatomy and walkthrough schematics have separate model bindings: reporting landmarks keep their authored schematic family while the 3D anatomy tab uses the investigation's selected native source. Ankle fracture, paediatric elbow and thoracolumbar walkthroughs use the expanded report fields. The cartilage-specific production guide is retained; its requirement links are reconciled without removing existing anatomical requirements, and remaining specialist scope reconciliation is explicitly blocking.

The release evidence snapshot and review queue retain pending reviews. The target is clinical/commercial quality reasonably capable of certification; actual certification is not required. This release does not establish complete high-fidelity representation of all reporting structures.

Validation: the full Python run passed 33,749 cases and identified eight integration failures; after repairs all 246 tests in the affected hosted-safety, investigation, walkthrough, fidelity and review-queue suites passed. Fifteen JavaScript orientation and prenatal interaction tests passed. Curriculum bank audit reported zero problems across 19 subjects. Browser verification checks source model rendering and reporting navigation. CI verifies the final committed revision separately.

Offline downloads and generated scratch outputs remain local and are excluded from deployment. The small cervical source package is retained for reproducible tests.

Deployment packaging: the first preview exceeded Vercel's function limit. The build now copies large public-source mesh binaries and the prenatal GIF byte-for-byte to static hosting, excluding those duplicate files from the Python function. Authenticated `/app` routes redirect to those public source artifacts; reader HTML and APIs remain gated. Runtime manifests, source-derived OpenKnee validation bytes and the cross-topic review document remain in the function. Hosted/local delivery tests pass.

CodeQL review: its PR summary reports 56 findings in offline source tools and test harnesses (none in deployed runtime code). The three VM executions load fixed checked-in renderer files for Node tests. Command findings concern explicit local QA interpreter/ffmpeg selections and argument-array calls to Poppler; they do not invoke a shell with web input. Path findings concern caller-selected offline source/output files and checked-in acquisition reports. These tools run with the local operator's filesystem authority, are not exposed as web APIs, and are excluded from deployment. The findings remain visible; no scanning checks or protections were disabled. Do not expose these CLI utilities as untrusted-input services without further hardening.
