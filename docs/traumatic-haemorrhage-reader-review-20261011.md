# Traumatic haemorrhage reader and cloud delivery — 2026-10-11

The authenticated reader passes the trauma reporting and shared lesson flows at 1440px and 390px. The review is bound to `web/app.js` SHA-256 `a8dc2985ad28ed9a9b07bd17f87857b3bc389feb7d316049f66ff8f3cf22d29d` and the exact source/data hashes in the [machine-readable receipt](traumatic-haemorrhage-reader-review-20261011.json).

Story: reporting or the shared haemorrhage lesson requests the scoped trauma reference, displays complete original publication objects and reporting-document links, and receives byte-identical files through authenticated local routes or the exact public Blob URLs. The cloud browser check simulates those redirects under the actual app CSP; it does **not** claim authenticated production UI verification.

| Boundary | Verified evidence |
|---|---|
| Authenticated UI → case API | Fresh disposable database/backups, stage-2 test reader, isolated headless Chromium contexts. All four reporting/shared-lesson × desktop/mobile configurations pass. |
| Case API → figures and definitions | Fifteen complete CENTER-TBI PNG objects, five clinical objects containing 67 source-position panels (63 CT, four MRI including ancillary panels), ten separate cohort plots, complete captions and source limits. |
| Figures → browser pixels | Seventy-five full-native-dimension RGB comparisons across four local configurations plus a mobile reporting cloud configuration; every pixel digest equals the frozen source PNG sample digest. No image filter, repaint, crop or resampling is substituted for the original source object. |
| Assessment → report | All five inserted assessment presets retain exact `[__]` blanks and the step’s own source IDs; no automatic normal findings or unmatched 3D part selection. The assembled report contains every required section. |
| Documents → original files | Three NINDS document links retain exact IDs/paths, formats, attribution and original-publication/license links. Two source PDFs parse as 9/50 pages; the unchanged DOCX has 46 ZIP members, 28 native media members and valid CRCs. |
| Local/Blob delivery → bytes | All 34 files, 38,875,353 bytes: local authenticated GET/HEAD and fresh public Blob response bodies match every expected size/SHA-256. Response bodies are checked after HTTP decoding; no assumption about an outer content encoding replaces the byte comparison. |
| Browser → public Blob image | Ordinary image redirects plus anonymous CORS-enabled image/canvas decoding pass all fifteen PNGs under the real app CSP. Actual responses provide CORS `*`; the exact trauma image prefix is allowed, while `connect-src 'self'` and `object-src 'none'` remain. |
| Case boundaries | Switching to non-traumatic haemorrhage removes every new trauma figure/document link. The shared lesson gallery files the trauma references under their own investigation. Other tested reader APIs do not acquire the new context field. |

Native-size controls are checked for all fifteen objects in every configuration. Native-size views deliberately scroll; the viewport can show only part of the large object while the complete original bitmap remains available. “Fit the whole image” remains available. Figure 2 identities normalize to 2.1/2.2 for sorting, while their original source labels remain “Figure 2 Panel 1/2.” All full publication captions are retained.

These PNGs preserve native **PDF image-object** dimensions and disclosed MuPDF DeviceCMYK/DeviceGray interpretation to RGB. They are not native DICOM, calibrated Hounsfield arrays, complete patient acquisitions or independently registered source cases. The untouched CMYK JPEG streams remain archival originals; standalone JPEG decoding is not substituted for the reviewed PNG color interpretation. The MRI adjuncts, reconsidered J3/J4/J5 source diagnosis, distinct Figure 9 patients and statistical plots retain their separate source meanings. Source panel counts are evidence of retained source objects, not proof that every reporting structure is adequately represented.

## Current backend policy bridge

The UI was checked on the live server started before the parent’s bounded provenance/canonical-path fixes. It was kept running through the completed UI checks, without restart from an observation timeout. A fresh cold ASGI process then loaded the current Python files, including `primer/server.py` SHA-256 `4653f7b871e598b06f8a2601f12bb1a17589c70d243cc3a89e64307a5f22c07f`.

That cold process proves:

- The complete valid trauma `radiology_reference` equals the API output used by the GUI checks.
- All 34 authenticated local GET/HEAD pairs return 200 with exact bytes; all 68 unauthenticated requests return 401.
- Both hosted GET/HEAD branches return 307 to each exact pinned URL with `private, no-store`.
- Empty, unknown, nested and trailing/extra-path source names return 404 in local and hosted modes.
- The current metadata, document bindings and CSP remain valid. Fresh-process source hashes match the current files.

This is a current policy/provenance check with simulated hosted environment selection, not a deployed Vercel request or production UI approval. The source provider’s separate negative rebinding/approval-flag tests remain the parent’s evidence.

## Existing-reader compatibility

The bounded native-spine receipt verifies both widths, all seventeen VerSe selections linking to their own CT levels, two Liu objects, disappearance of CT links after switching source, unchanged guarded native files, current app/style bytes, and zero errors/failed requests/document overflow. The previous complete 306-frame/pointer/GPU science review is preserved and is not claimed to have been repeated here.

The bounded brain receipt verifies the shared native-inspector card and reporting Images/3D entry points, all six MASSP objects, correct inspector absence after selecting BodyParts3D or the guide, and a working original native-MRI popup with three source planes. No new trauma document links appear there. Original fine-source voxel, probability and geometry proofs are preserved; this check does not repeat or extend their approval.

The new [cervical amendment](cervical-cancer-source-review/browser-compatibility-amendment-algebra-trauma-20261011.md) and [endometrial amendment](endometrial-cancer-source-review/browser-compatibility-amendment-algebra-trauma-20261011.md) pass all eight route/width pairs: 32/36 original figures, eight/nine blank assessment areas, all 54 decoded source meshes and genuine 54-object GPU frames. Their affected tests pass **11 tests**. Original and previous amendments remain byte-identical. The cervical amendment explicitly records sixteen unavailable original named captures; it neither reconstructs them nor silently transfers their historical visual proof.

## Capture and observation history

Forty-three trauma/native captures were inspected through contact sheets, plus four individual document-section captures. Native zoom intentionally requires scrolling. Some tall element screenshots composite the fixed reader header across the captured section; this capture limitation is recorded separately from the successful full text/link and overflow checks. New uterine captures focus the actual canvas, with the earlier capture observations preserved.

A mobile initial-navigation observation timed out after the desktop configuration had passed. A bounded fresh diagnostic on the **same live server** showed both mobile routes with no JavaScript/HTTP errors. The harness then waited for initial application readiness and continued the remaining configurations from the saved desktop checkpoint. After all GUI/cloud-image checks passed, the new packet-only request context initially returned 401 because it had not signed in; authenticating that new context completed the packet checks without repeating successful GUI checks. Both observations and their hashes remain in the ignored evidence directory.

All owned browser contexts and processes are closed. The owned server command/PID was checked before termination; session 74178 ended with the expected SIGTERM exit. The cold process also ended successfully. The receipt names the ignored evidence directory and SHA-256 of each raw proof.

Clinical/commercial readiness, every-structure coverage, fine anatomical layers, patient registration, source-case 3D fidelity, production UI and whole-goal completion remain **unproven**. This review establishes source-reader compatibility, pixel/byte preservation, scoped references and current delivery policies only.
