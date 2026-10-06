# UIC1 history sensitivity review

The pelvic candidate decoder's initial UIC1 history now has a finite sensitivity audit against all 47 source resources. Forty contain UIC1 blocks; seven do not test this question. Four explicit histories were considered: reverse-rank, all-zero, forward-rank and reverse-rank shifted by one. The original U3D, geometry candidates and encoded-normal candidates are unchanged.

Only reverse-rank passes numeric range/span constraints in all 40 applicable resources, and it reproduces the retained candidates. All-zero passes 29 and is rejected in 11; forward-rank passes 34 and is rejected in six; shifted reverse-rank passes 36 and is rejected in four. Among their range-valid comparisons, they affect 38,139, 58,964 and 62,164 faces respectively. These totals exclude rejected comparisons and are not comparable clinical quality scores.

The first 128 faces are examined explicitly because global averages can hide early history errors. Reverse-rank prefix median corner-to-facet direction agreement spans approximately 0.954–0.997. Some range-valid alternatives have negative prefix medians. Each record also retains the changed position/index counts, affected-face directional summary, encoded-block identities and rejection reason. Rejections are constraints on an interpretation, not diagnoses of original source geometry defects.

The published toy integer example passes with both reverse-rank and all-zero initialization. It therefore cannot certify the full decoder. Source ranges, complete stream consumption, a plausible picture or one test stream likewise cannot establish encoded-history semantics on their own.

This audit supports retaining the current reverse-rank interpretation while rejecting the tested alternatives as universal replacements. It does not prove the history independently: the finite alternatives are not exhaustive, encoded directions share candidate index interpretations, and an original encoder/independent decoder confirmation is still missing. No fixture or source array is rewritten to make an alternative pass; no coordinate fitting, topology repair or clinical threshold is introduced.

All artifacts retain `bootstrap_independently_verified=false`, no clinical approval and no runtime/model coverage credit. Whole-decoder, materials, registration, anatomical partitions and structure completeness remain unfinished. Full radiology counts and image-rights counts are unchanged.

Reproduce with `python -m tools.anatomy_sources.review_cvh5_uic_history --source docs/cvh5-pelvic-source-review --candidates docs/cvh5-candidate-geometry-review --normal-source docs/cvh5-normal-interpretation-review --output docs/cvh5-uic-history-review`. Tests preserve all source links, applicability/rejection accounting, the non-discriminating toy example and the retained verification limits.
