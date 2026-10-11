The post-main curvature and classical-constraints route QA passed at 1440 and 390 CSS pixels against commit `b23ce55f4b11e56532b6908062ef0a6278a3a240` (parent `421390435be1b6c9c7a65be44cc4ca2b88b505f4`). This handoff audited the saved completed evidence; the final driven-hoop 3D check had already finished successfully before the interruption, so no browser checks or server were restarted.

| Review | Coverage per viewport | Result |
| --- | --- | --- |
| Standalone curvature / transport | 19 selected states, 28 numeric endpoints, 6 speech captures | Pass |
| Curvature surface 3D | 66 selected states, 40 native endpoints, 11 speech captures | Pass |
| Classical constraints lab | 8 modes, 98 range endpoints, 98 numeric endpoints, 8 presets, 9 speech captures | Pass |
| Driven-hoop 3D | 6 parameters, 12 native endpoints, 6 camera buttons, 3 speech captures | Pass |

The saved proofs record empty browser exceptions, exact model resets and exact current-state speech at both widths. The 3D hoop records successful keyboard, model-button and view-button resets. Standalone and 3D curvature maximum speech chunks are 1194 and 1185 characters; constraints lab and hoop maxima are 1180 and 1164, all within the shared 1200-character limit. The final desktop/mobile hoop screenshots were also inspected during handoff: the upright hoop, labels and wrapped controls remain contained.

All served hashes in the three authoritative proofs match their saved local hashes and the current workspace files. This includes the shared application and stylesheet from the instrument-grammar integration, as well as the final curvature and constraints helpers:

| Current source | SHA-256 |
| --- | --- |
| `web/app.js` | `f8e06f35620eccdf50c7c34f712502c15195f439dd8f05f7cd658e6464c2d16d` |
| `web/lesson-models.js` | `f527ece3c8f03dfbdefddfd2e0216554f5b7ad9ee3976d698ba0ac64cca83ee8` |
| `web/math-curvature-lab.css` | `5b6890e6fe51b7c8ad9a4edc46aab690fc592354137d47349cf4821e6b43e91f` |
| `web/math-curvature-lab.js` | `715efc56d12676454a2c873470ad5f2181a56bc22bb8cb15cfc0bb2738a929b0` |
| `web/physics-constraints-lab.css` | `a0f1aff4aad7faf0c63038e5ec479d4b3b7a08e7dfa2fa2c12953282b27b2c0d` |
| `web/physics-constraints-lab.js` | `ff1d79ba13f619a7e96acd035a916d053a583af24e5890e2e16852ef9a120d77` |
| `web/spatial-models.js` | `b3d2e6dbb578e527da86fe221386456449cfcebd704cbdc06ab4c256cf0c63b6` |
| `web/spatial-module-objects.js` | `3b45c9a0b0ee2a6d8f51632c5b6ba584be5cacc204eacc18313770e75618c74c` |
| `web/speech-chunks.js` | `e742231ae27413d51e969f1391af355403453d1365da2ec9eeb94c4a5794dc50` |
| `web/styles.css` | `afbfab4349113e050c1ad2ddc4c5667d93bcc0b115afdda2a5c9056a3398183b` |

The preserved evidence root is `/Users/peter/Documents/ChatGPT/Primer/.research/curvature-reader-qa-62msxhbx/post-main-20261011-ay1c5ace`. Authoritative files are `curvature/proof.json`, `curvature/spatial-proof.json` and `physics/proof.json`; the final file contains `spatialPassed: true` and complete desktop/mobile hoop rows. The route drivers, server log and 50 PNGs remain in place. [The JSON handoff](post-main-review-20261011.json) inventories all 58 retained evidence files with byte lengths and SHA-256 hashes, records current source hashes, and supplies viewport counts and cleanup details.

The isolated 8916 server was already stopped and no listener remained. Only the owned disposable `qa.db` and `backups/primer-20261011-090550.db` were removed, followed by the empty owned backup directory. Runtime source, shared databases, data manifests and tests were not edited by this handoff.

These are authenticated local-reader checks using Chromium 151.0.7922.34, not authenticated production or deployment checks. Speech uses global reader stage 2 on the advanced lesson routes because the host suppresses model speakers above that stage; it verifies text and chunk delivery, not pronunciation. Coverage is bounded to the authored analytic surfaces and classical systems. It does not establish arbitrary-surface transport, general relativity, arbitrary central potentials, or completion of the wider fidelity objective. The parent task owns full-suite and release verification.
