# Radiology visual review

The fingerprint ledger is the authoritative list of approved assets. Unrecorded
images below remain pending; a corrected rendering is not a complete content review.

## Cardiovascular batch in progress

- Cardiac masses/devices: moved the explicitly labelled LV apical thrombus out of
  the RV compartment and qualified the perfusion label. Final 800px rendering
  inspected. Replaced invented tumour enhancement bars with phase-comparison
  tiles and corrected attachment arrow to stalk; approved in ledger.
- Coronary CTA: Dmin now measures only the patent lumen below plaque, rather than
  extending beyond the vessel. Reduced cross-section size; final 800px inspected.
  Reference-lumen caption moved inside the panel; approved in fingerprint ledger.
  Content reference: CAD-RADS 2.0 consensus,
  https://pmc.ncbi.nlm.nih.gov/articles/PMC9627235/.
- Peripheral vascular imaging: diameter excludes plaque; collateral now connects
  both upstream and downstream of the depicted lesion. Final 800px inspected.
  Collateral/lesion labels spaced apart; approved in fingerprint ledger.
- TAVI: coronary-height label now fits within the middle panel. Final 800px
  inspected. Replaced access-route calibre arrow with a connected, labelled
  orthogonal cross-section inset measuring open lumen. Approved in fingerprint
  ledger. Content reference: SCCT consensus,
  https://www.jacc.org/doi/10.1016/j.jcmg.2018.12.003.
- Congenital CT: inspected 800px image; first card extends left of the inner
  content frame. Review orientation and improve vessel map before approval.

Regression tests now check that coronary, peripheral and TAVI diameter arrows
exclude plaque. Focused radiology plus ledger suite: 10 passed. Three new ledger
approvals bring the overall review count to 373/432, with no stale entries.

## Brain batch

Corrected arterial territory orientation (medial ACA, lateral MCA, posterior PCA)
and labelled the broad axial schematic; removed overlapping stroke/pressure
checklist markers and brought the optic-nerve drawing inside its panel. Final
800px images inspected. Cardiac masses, brain anatomy, stroke, venous/CSF and CNS
infection now have ledger records: 378/432 current, no stale. Sources are linked
in each ledger finding. Congenital CT and the remaining brain/head-neck lessons
are still pending. Final runtime, model-appropriateness and deployment checks are
separate and remain outstanding.

Dementia, epilepsy and intracranial haemorrhage now reviewed (381/432).
Epilepsy plane now actually perpendicular to the depicted hippocampal axis;
dementia checklist markers no longer overlap. MS and spine images inspected but
initially not approved. Subsequently moved infratentorial lesion to labelled
hindbrain inset and replaced false residual-space measurement with cord
deformation contacted by the mass. Both final 800px assets inspected and ledger
approved: 383/432. Congenital CT still pending.

Head/neck batch: thyroid, deep neck, temporal bone, cervical nodes, sinuses and
orbit reviewed (389/432). Fixed thyroid label overlap and fascial-route overflow;
added cricoid boundary and corrected node placement; separated bilateral nasal
drainage instead of drawing a trans-septal connection. Final 800px images inspected.
Focused tests: 10 passed. Congenital CT and 42 other illustration reviews remain,
as do model-appropriateness, final runtime checks and actual deployment.

Congenital CT completed: first panel contained, organs and patient sides named,
sequence connection extended. Pancreatitis labels contained and collection
captions separated; appendicitis measurement corrected to outer diameter on a
closed transverse wall. Final 800px assets inspected and approved (392/432).
Biliary image inspected but not yet source/content approved. Forty reviews remain.

Bowel obstruction, Crohn disease and bowel ischaemia reviewed (395/432). Replaced
disconnected obstruction geometry with a continuous calibre transition; opened
Crohn lumen at both ends with narrowing through thickened wall. Final 800px assets
inspected. Abdominal trauma, pancreatic tumour and peritoneum inspected but not yet
approved; check laceration-depth endpoints and the abdominal-wall hernia geometry.

Those checks are now complete: laceration depth reaches the organ surface and its
vessel marker lies on the intersection; bowel now protrudes through a wall defect.
Abdominal trauma, peritoneum, biliary and pancreatic tumour approved after source
cross-check (399/432). Focused radiology/ledger tests: 10 passed. Remaining review,
model assessment, runtime and deployment requirements are unchanged.

Kidney, scrotum and adrenal reviewed (402/432). Corrected renal pseudo-enhancement
overclaim and added preserved-flow torsion caveat. Final 800px assets inspected.
Rectal MR, acute abdomen and liver inspected but not approved: rectal measurement
endpoints do not yet reach the actual tumour edge; verify phase-pattern example
and acute-abdomen diagram before records. Thirty illustration reviews remain.

Rectal diagram corrected: MRF arrow now minimises distance between actual tumour
arc and fascia; extramural arrow starts at muscular wall and ends at tumour edge.
Final 800px rendering inspected; focused suite 10 passed. Keep pending until
clinical/content cross-check and metadata consistency review are complete.

Rectal source/metadata cross-check now complete; rectal, acute abdomen and liver
illustrations approved (405/432). Remaining 27 illustration reviews plus model
assessment, final runtime verification and deployment remain outstanding.

Prostate, mammography, breast calcifications, ovarian O-RADS and breast MRI
reviewed (410/432). Fixed prostate header overlap and mammography text containment;
added actual branching calcifications and wedge-shaped segmental distribution.
Bladder and uterine images inspected but pending anatomy/measurement corrections.

Final bladder/uterine geometry and nine musculoskeletal plates reviewed (421/432).
Fixed measured heading widths across the 19-plate cohort; corrected hip and
magic-angle vertices, cartilage-gap geometry, degenerative joint-space taper,
bone-segment label containment, and a reversed ulcer leader. Regression suite:
11 passed. Wrist Gilula-arc anatomy and paediatric hip/elbow landmarks remain
pending corrections; other final paediatric/nuclear plates and authored CT also
remain pending. Model assessment, full runtime verification and deployment are
still outstanding; the goal is not complete.

All 432/432 illustration reviews are current (84/84 radiology), with no stale
fingerprints. Final wrist arcs now map I/II to S-L-T and III to C-H; paediatric
hip landmarks and text containment were corrected, and V/Q preserved activity
is visibly distinct from the perfusion defect. All 168 radiology WebPs pass
deterministic regeneration. The curriculum-wide asset check passes 864 WebPs
and 259 model entries. This completes the illustration review gate, not the
model-appropriateness, runtime or production-deployment gates.

Release QA uses isolated `/tmp/primer-release-qa.EBDCUR/primer.db`, port 8768,
server PID 49491 / exec session 51383. Mobile navigation passed (including
Genetics context, Escape/focus and route collapse); all 14 spatial scenes passed
desktop/mobile controls, drag, keyboard and reset. Evidence directory:
`/tmp/primer-release-qa.EBDCUR/`. The Genetics screenshot captured an article
loading state, so article completion still needs separate verification.
Full pytest initially returned 31,578 passed, 2 skipped and one stale copy-test
failure. Updated that assertion to protect the corrected quantum relative-scale
and inelastic-collision energy explanations; 12 focused tests pass. Full rerun
session 27590 logs to `/tmp/primer-final-rollout-tests-rerun.log`; concept browser
sweep session 74230 remains running. No deployment has occurred.

Reader follow-up found real HTTP 429 responses from Wikipedia, incorrectly
presented as missing articles. Added Retry-After backoff for 429/503 (seconds
and HTTP dates), 503 article responses during backoff, and explicit temporary
unavailability copy. Six focused backoff/API tests pass. Server PID 49491
predates this backend change: restart only after the live concept sweep has
finished, then verify the corrected reader state. The full rerun also predates
this last backend fix, so it is not final release evidence for that change.
