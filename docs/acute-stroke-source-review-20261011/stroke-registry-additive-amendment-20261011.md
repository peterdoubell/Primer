# Exact stroke additive historical-guard amendment

The new CTP source and stroke reporting/requirement values are independently source
reviewed and pinned to CTP-only GO. The current twelve-question snapshot incorporates
the parent’s AIS/CVT and grader corrections while retaining the original source
snapshot. This amendment permits only those exact scoped values in comparison views;
it grants no clinical/fine anatomical approval and does not permit ISLES publication.

The immutable pre-stroke values were obtained from base commit
`837c0b1825bb0dc29c32b963fb9da09ebb3ce558`. The bridge removes exactly thirteen new
CTP image/asset records, the exact 369-group requirement row and its single scope ID,
and the scoped override. It restores only the five stroke steps’ original value token.
Every removal/restoration checks current semantic and raw-token hashes; fixed IDs,
counts, source review and current-quiz receipts are also pinned. Ambiguous token
namespaces, extra/missing records, source/clinical promotion, altered scope and changed
raw formatting are rejected. All other actual values and raw fingerprints survive
unchanged for the original historical guards to inspect.

The old myelopathy guard composes this comparison before its existing trauma bridge
and then executes its original full semantic/raw-token assertions. The old trauma
unrelated-value guard likewise executes its original hashes after the exact stroke
comparison. Its original canonical formatting gate retains the same whole-file raw
hash, semantic hash and canonical serialization requirement. An optional raw argument
supplies the strict actual-file comparison view; it does not change any expected
historical fingerprint. The source owner, original trauma/myelopathy reviews and
prior format evidence are not rewritten or rebaselined.

Fresh negative fixtures cover source-caption changes, duplicated figures/assets,
foreign investigation IDs, invented anatomical/clinical credit, omitted requirement
groups, duplicated scope ID, normal-finding insertion, an unreviewed reading source,
raw-token drift, unreviewed paths, ambiguous namespaces and unrelated drift. The last
case remains in the comparison and fails the old exact format guard as intended.

Final targeted run: 59 passed in 30.21 seconds across the new bridge tests, current
stroke integration tests and original trauma/myelopathy integration guards. A prior
in-flight run correctly failed when parent grader changes made the current-quiz and
curriculum receipt stale; those observations were retained and the unpublished draft
bridge was refreshed against the final questions. This is a bounded current-quiz
refresh, not a change to historical evidence or test requirements.
