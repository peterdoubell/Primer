# Exact measurement comparison boundary

The offline inverse in `runtime-inverse.json` covers exactly three changes from commit `6881f3238f26c4c3fba36d4970faa8e01045ad36`:

- One script inclusion in `web/index.html`.
- The three-line `phys.4.experiment` renderer mount in `web/lesson-models.js`.
- The prompt, answer and explanation of `nodes[33].quiz[7]` in the physics curriculum. The revised question explicitly asks for independent combined standard uncertainty; its answer is 2.2%.

Every literal span and complete before/after file hash is recorded. Reversing the three deltas recovers each entire base file byte for byte. All other physics values and all other shared UI bytes are unchanged. The helper rejects unrecorded changes and leaves unknown paths untouched for their existing guards.

The existing optics and HippUnfold comparison entry points apply this bounded inverse before their original checks. The frozen HippUnfold reader proof also compares its index file through the exact prior view. QFT's historical physics-file check still reaches its original semantic guard after the single reviewed quiz correction has been reversed. Historical proof files are unchanged.

This inverse is used only for historical comparisons; it does not change current learner content. It supplies no validation of the new measurement script's numerical methods, browser behavior or current combined startup bundle. Those require their own current source and authenticated reader evidence. The six-figure epilepsy inverse is separate and remains byte-identical, with SHA-256 `796b0ddf3c1dedf0a5f053b09478f2046a3c6748168d58c22282f9fef1928340`.
