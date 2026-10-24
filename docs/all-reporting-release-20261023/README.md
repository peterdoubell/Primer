# Selectable radiology reports

The library covers all 156 examination and worksheet variants across 98 guides. Each report uses named anatomy or an explicitly scoped procedural/reference checklist, selectable descriptions and optional measurements. The compiler rejects unenumerated context slots in these authored reports. No clinical observation is selected by default.

Edit the `data/radiology/anatomic-*.json` and `msk-anatomic-*.json` definitions. The scripts in `tools/authoring/` are optional authoring aids, not part of the routine build. Preserve stable investigation, section and finding IDs. Keep supporting source references and distinguish modality, contrast, prior comparison, scan coverage and performed-procedure claims. `exclude_from_bulk_normal` prevents convenience actions from asserting those conditional observations.

A repeatable section accepts `instances`, with each record carrying its own findings. Its global normal/not-assessed state cannot coexist with records. Adding a blank record does not assert a lesion; incomplete or contradictory records block copying. Each instance is labelled independently in the report. Unscoped external context cannot replace observations in every instance.

`descriptor-calculation-bindings.json` maps explicitly selected descriptors to existing versioned calculators. Thyroid and prostate lesions receive their own TI-RADS/PI-RADS results. Prostate dimensions and optional reviewed PSA feed volume/PSA density. No clinical arithmetic is duplicated in the browser. Inapplicable inputs produce no category; missing or conflicting active calculation inputs block copy. CAD-RADS remains available with explicitly reviewed aggregate inputs; categorical stenosis ranges are never misrepresented as exact measured percentages.

Before replacing a shipped catalogue, build with `--archive-current`:

```sh
python3 tools/build_descriptor_reporting.py --catalog /path/to/reporting-api/catalog.json --archive-current
python3 tools/build_descriptor_reporting.py --catalog /path/to/reporting-api/catalog.json --check
```

The reporting API's `sync_report_ui.py --primer /path/to/Primer` copies the compiled catalogue, history and shared renderer. Saved drafts retain their original form versions. Never rewrite or delete a shipped archive. New source worksheets are exposed as reporting-only native library entries; they do not inherit unrelated clinical images or teaching claims.

Validation covers every authored finding path, conditional dependency, declared contradiction, repeated-record isolation, numeric bounds, calculation parity, saved-version compatibility and hosted flows. The exact runtime inverse preserves historical source/anatomy approvals; it does not grant clinical approval to these templates. The native presentation ledger and canonical lesson content are unchanged.
