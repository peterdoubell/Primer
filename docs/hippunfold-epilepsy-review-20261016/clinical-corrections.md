# Epilepsy teaching corrections

Five JSON fields now distinguish the MRI transmantle pattern from a histological diagnosis and align the legacy epilepsy lesson with the HARNESS protocol. This review adds no image or structural coverage and does not establish whole-module clinical approval.

The transmantle tip, quiz answer and explanation describe a pattern supporting FCD type II, most often IIb. They no longer equate MRI with the demonstration of balloon cells, assign a specific migration mechanism from the sign, or infer resectability and seizure outcome from that sign alone. The interpretation follows the imaging and integrated-diagnosis sections of the [2022 ILAE FCD consensus](https://pmc.ncbi.nlm.nih.gov/articles/PMC9545778/) (DOI: 10.1111/epi.17301). The acquired full text was rechecked at implementation; its SHA-256 is recorded in the accompanying JSON.

The legacy technique template and approach now specify isotropic millimetric 3D T1 and 3D FLAIR, plus high-resolution coronal T2 perpendicular to the hippocampal long axes. The template retains the no-gap acquisition requirement and records the reason for any contrast use. These changes follow section 2.2.2 of the [ILAE structural MRI recommendations](https://www.ilae.org/guidelines/guidelines-and-reports/recommendations-for-the-use-of-structural-magnetic-resonance-imaging-in-the-care-of-patients-with-epilepsy) (DOI: 10.1111/epi.15612), printed pages 1058–1059. The official PDF was rechecked at implementation. The effective reporting protocol and module guide already used the three core acquisitions and were left unchanged.

`clinical-corrections.json` records every exact before/after string, JSON pointer, source rationale, JSON-token hash, and before/after file hash. It supports a bounded historical inverse: encode each recorded string as its UTF-8 JSON string token with `ensure_ascii=False`; require exactly one occurrence of the after token; replace it with the before token; then require the recorded original file SHA-256. The implementation proved that this inverse recovers each original file byte for byte. It must not be used to normalize unrelated future edits.

Verification proved:

- Exactly five JSON leaf values changed across the two product files; all other fields are identical.
- The quiz prompt, kind and grading keywords are unchanged. All four grading keywords still occur in the answer.
- The report template's findings and impression remain byte-identical.
- Image 3 retains its binding, source URL and accurate FCD caption. The optional sixth context-note proposal was not applied.
- The original file bytes are recovered exactly by the five bounded reverse replacements.

These checks validate the content delta. Browser rendering, authenticated reader integration and source-viewer verification belong to the enclosing release checks and are not claimed here.
