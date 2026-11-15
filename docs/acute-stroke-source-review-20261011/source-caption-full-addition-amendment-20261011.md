# Complete source caption addition — 11 October 2026

Authenticated reader QA found that all thirteen CTP records had `original_caption`,
but the actual gallery renderer displays complete context only from
`source_caption_full`. This repair adds that missing field with exactly the existing
complete original caption on each approved CTP figure. It retains `original_caption`.
Every caption is compared with the immutable final source proposal and the entire
primary XML caption text under the same established whitespace normalization.

No source pixels, original caption text, figure case/context, modality roles,
clinical/fine flags or other row metadata changes. The other four stroke data files,
all unrelated registry value tokens and the frozen twelve-question file remain
unchanged. The reproducible normalizer now emits the same complete rows. A separate
repair command is idempotent and rejects partial, shortened or foreign bindings.

The original source GO/proposals, `af4b98…` data receipt, `c8e9d7…` historical guard
amendment and `3fe6bf…` validation are preserved byte-for-byte. The new data receipt
is `runtime-data-integration-caption-complete-20261011.json`. The strict historical
bridge first validates its original immutable amendment, then layers this bounded
caption addition onto only the thirteen-image collection's semantic/raw-token hashes.
All other guard records and all original expected historical hashes/semantics remain.
No general caption alias or broad source rebaseline is introduced.

Current source captions remain published source-patient context, not current-patient
findings or independent clinical approval. ISLES publication remains NO-GO. This
metadata repair grants no source geometry, anatomical coverage or clinical grade.

Targeted verification: 68 passed in 29.98 seconds, including caption contracts,
adversarial caption/source-role changes, current stroke reporting/scope and original
trauma/myelopathy guards. A further nine caption checks passed in 0.40 seconds after
explicitly requiring the field in the current-reader contract. The native QA owner
is rerunning the previously failed authenticated-reader caption proof separately.
