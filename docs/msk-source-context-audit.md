# MSK source-context audit — 26 September 2026

**No current clinical false-pass was found.** All 28 clinical-image evidence records inspected remain anatomically unapproved. The existing modality guard rejects the two shoulder arthrographic candidates against MRI-only leaf scopes; the ultrasound-only hallux and ankle examples remain unbound to MRI requirements. This audit does not approve a source, change a requirement or make an asset high fidelity.

The remaining gate gap concerns *a new review*: matching file and scope hashes protect the reviewed claim from subsequent changes, but do not test whether source and target context contradict one another. The [machine-readable audit](msk-source-context-audit.json) records the exact gate hash, 28-source metadata inventory and six synthetic reproductions. The [minimal proposal](msk-source-context-proposal.json) separates source facts, a binding's intended purpose and target suitability.

## Reproduced prospective false-positive paths

Using only disposable versions of the existing synthetic fixture, I supplied fresh matching review hashes and explicit contradictory facts. Each case produced two `verified` clinical-image rows:

| Source fact | Explicit hypothetical target or credited selection |
|---|---|
| Left side | Right side |
| Cadaveric acquisition | In-vivo example |
| Normal anatomy | Infection demonstration |
| Local segment; attachments absent | Complete course and attachments |
| Adult, age 58 | Immature anatomy with open physes |
| Selected panel explicitly listed as excluded histology | MRI clinical-image selection |

These are not tests that existing approved evidence was altered successfully: the fingerprint checks still prevent that. They show that a *fresh*, self-consistent approval record can carry semantically incompatible claims without a compatibility check. The synthetic results do not make the whole audit ready because other representations are missing. No real evidence was approved, and no shared data changed.

## Concrete metadata findings

All 28 records have modality. Only 12 have `image_state`, five have laterality and 18 have a representation selection; panel selections use both lists and loose strings such as “imaging” or “Source figure as captioned.” No consistent typed acquisition/population/context contract exists. Missing fields do not mean the publisher omitted the facts: some are in captions or limitations.

- The three Wang hallux MRI records are already well constrained in prose and use panels c/d. Their left/right side is structured, while specimen preparation, age and plane/sequence remain largely caption text. [The primary study](https://link.springer.com/article/10.1186/s13018-021-02795-7) establishes the cadaveric methods and distinct specimens; those facts should not become an in-vivo or bilateral claim.
- Wang figure 7 explicitly excludes a histology-only marker from the MRI claim. That separation is useful, but the evidence gate does not itself compare selected panels with the excluded ancillary panels. The runtime catalogue validator does; the two protections serve different paths.
- The Chen hallux ultrasound records honestly say side is unspecified and carry no MRI bindings. Preserve that uncertainty. The proposal uses only the reviewed source-panel facts from [Chen et al.](https://doi.org/10.3390/diagnostics12071541), without inferring age, side or individual sesamoid ligaments.
- The older wrist mixed figure records its MRI subset as the loose string “imaging,” while its limitations identify e–g. That should become an explicit selection before approving eight component bindings across both wrist investigations. The same anatomy reference may be relevant to both investigations, but each exact binding still needs its own extent/context assessment.
- The knee anterior-root figure identifies a single selected slice in its limitations but lacks typed side, preparation and state. It is a source candidate for the depicted attachments, not proof of the whole root course or every target population.
- The SPECT/CT teaching composite is unbound and explicitly not high-fidelity anatomy. It should remain a separately scoped teaching illustration; extending clinical-image modality acceptance merely to make it count would be inappropriate.

## What should and should not block

Normal anatomy can be useful in a diabetic-foot module. The [Radiology Assistant guide](https://radiologyassistant.nl/musculoskeletal/diabetic-foot/mri-examination) concerns patient-specific routes, joints and tissue findings; a normal figure can explain their anatomy without depicting infection. The module title alone must not impose a disease-example requirement on every anatomical leaf. Conversely, a normal cadaver image cannot establish a patient's infection or in-vivo signal behaviour.

The practical next step is a small `source_context` record plus an exact investigation/leaf/source-selection claim. Reject known contradictions, preserve unknown facts, and ask the reviewer to assess transfer only where the target depends on it. Do not invent universal exact-age, sex, field-strength or in-vivo requirements. Keep observed local portions distinct from complete structures: improving context metadata must not shrink a whole-course requirement to match a convenient panel.

All context claims must remain inside the existing scope fingerprint. Commercial rights, byte hashes, independent image/schematic/model review, site expansion, reporting scope and inventory clinical review remain separate gates. The proposal deliberately grants no approvals.

## Viewer claim audit

I inspected current source notes, crop logic and the recent rendered whole-foot evidence. The exact app, viewer and Z-Anatomy manifest hashes still match that browser pass. I found **no new misleading high-fidelity claim** requiring a viewer edit:

- Z-Anatomy is labelled adult right-sided reference anatomy; coarse meshes and material-only cartilage/tendon surfaces are explicitly limited.
- The whole-foot view derives its framing from all source pedal bones, retains source geometry and identifies missing plantar structures. It does not offer the partial MRI-ankle dataset as a full foot.
- Full structures removes a view crop; the notes specify complete *selected source object*, not a promise that the source segmented every anatomical component.
- MRI knee/ankle notes state source sampling, processing, missing structures and incomplete clinical validation. Atlas switching preserves separate coordinates rather than claiming registration between sources.

Presence, selection and positive pixels remain engineering evidence only. The earlier clinically incomplete anatomy and site-expansion gaps are preserved.

## Implemented follow-up

After this read-only baseline, the coordinator authorized a minimal guard in `tools/check_msk_fidelity.py`. It now compares explicit `source_context` facts with optional parent/leaf `context_requirements`, rejects known selected-panel type conflicts, preserves inherited constraints and blocks unknown facts only when an explicit target needs them. A source-limited normal cadaveric reference remains eligible for review. No source facts are inferred from module titles or prose.

The six baseline reproductions above retain their old gate hash and are not overwritten: they document the original absence of a semantic check. New synthetic tests express the analogous constraints in the typed contract; they also cover malformed data, unknowns, inherited constraints, normal-reference eligibility, fingerprint invalidation and retained site-review gates. The combined fidelity/scope suite passes 133 tests. Clinical approval is still separate.

The [28-record reconciliation snapshot](msk-clinical-image-source-context-reconciliation.json) records exact asset hashes, known source facts, field provenance and explicit unknowns. Its historical scope excludes the subsequently acquired shoulder batch. The coordinator verified its asset hashes and merged those facts into the shared ledger without refreshing approvals. Subsequent source-caption reconciliation added the explicitly stated ages/states for five knee/hip/ankle examples and kept the three healthy wrist volunteers' ages tied to their respective panels. Missing age, preparation or laterality was not filled by image appearance or module name. The new shoulder records carry their own context, with unknown facts retained.

Two further checks enforce explicit sides in the established requirement
`laterality` field and reject disagreement between typed selected panels and
the record's explicit credited panel list. These are compatibility checks,
not anatomical approvals. Requirements and approval statuses remain unchanged.
