# Whole-curriculum visual release audit

Scope: all 432 current lessons, every subject and learning stage. Every lesson
needs an explanatory illustration; interactive models are selected for their
teaching purpose, not required merely to fill a counter. Neither an illustration
nor a simulated exercise certifies practical or clinical competence.

## Illustration evidence

`check_illustration_reviews.py` reports 432 current reviews and zero stale
fingerprints. The records document actual visual inspection, corrections and
sources. `check_curriculum_illustrations.py` verifies all 864 responsive WebPs,
their bindings, dimensions and metadata. Subject review documents retain the
specific scientific and layout findings. The gallery exposes all subjects,
stages, captions, lesson links and full-resolution pictures.

## Model selection assessment

Reviewed the current lesson goals for the 175 lessons without model bindings,
alongside the illustration review and the existing model inventory. Selection
is intentionally not equivalent to complete simulation of each lesson goal.

| Field | Current model selection and teaching rationale |
| --- | --- |
| Mathematics | All 59 lessons have models, including introductory counting and graduate concepts. Parameter changes expose an invariant, counterexample, transformation or approximation. |
| Physics | All 39 lessons; 41 entries. Models make rates, fields, conservation and limits inspectable. Explicit idealisations and units remain necessary. |
| Biology | All 37 lessons. Mechanism models distinguish genotype/phenotype, individual/population outcomes and schematic anatomy. |
| Chemistry | All 29 lessons. Matter, molecular structure and reaction/measurement relationships are modelled without pretending to be a laboratory. |
| Computer science | All 34 lessons. Executable traces, state transitions and constrained examples expose the mechanism behind the concept. |
| Earth and space | All 27 lessons; 28 entries. Space, time, cycles and quantitative assumptions benefit from controllable geometry or rates. |
| Language and literature | 21 of 40 lessons. Retained structural/linguistic demonstrations; the other goals centre on close reading, interpretation, original writing, revision and real language use. Plates and the lesson's reading/practice are retained instead of manufacturing a numerical verdict on an interpretation. |
| History and civics | 3 of 29 lessons. Timelines and a bounded economic model are interactive. Comparative chronology, primary-source evaluation, institutions, legal reasoning and contested explanations retain their explanatory plates and cases; an adjustable toy society would not verify those goals. |
| Arts and music | 4 of 25 lessons. Colour, visual elements and beat/subdivision benefit from direct manipulation. Added the beat model during this assessment. Drawing, craft, singing, dance, performance, criticism and sustained creative practice retain real-world practice and explanatory plates. The silent rhythm diagram explicitly does not assess musical performance. |
| Mind, society and philosophy | 3 of 29 lessons. Formal logic has testable truth/countermodel operations. Ethical, philosophical, social and personal-practice goals retain reasoned comparisons and cases, not a simulator presented as settling value judgements or measuring a learner's mind. |
| Radiology | CT windowing has a quantitative synthetic-phantom model. The other 83 lessons retain reviewed diagrams and clinical-question exercises: pattern/distribution, anatomy, measurement conventions, reporting and context-sensitive decisions require real studies and supervised practice. Schematic plates are not invented diagnostic scans, and no synthetic patient-management simulator is implied. |

This is an instructional selection judgement, not a claim that further useful
models could never be added. Optional future activities are not a universal
model-presence release requirement. The shipped models must still work and
teach the relationships they claim; their presence alone is insufficient.

## Runtime and release gates

- Concept suite: 176 bindings, state changes, keyboard/reset, desktop/mobile,
  semantic/geometry checks and current-source hashes.
- Spatial suite: 14 bindings, drag, keyboard, parameters, reset and mobile.
- Legacy suite: 70 bindings, real controls and viewport checks. Visual inspection
  found scientific SVG clipping; fixed whole-diagram default plus explicit
  enlarge/fit and keyboard-scrollable detail. The strengthened suite checks SVG
  bounds, not only the outer card, and exercises enlarge/fit.
- Genetics reader: successfully fetched and displayed in a fresh session.
  Upstream 429/503 now respects Retry-After and is distinguished from missing
  articles; cache/local content remains available. External images can still
  become unavailable, so honest fallbacks are retained.
- Navigation: subject/stage/lesson context, mobile collapse, Escape/focus,
  resizing, reading settings and route transitions have dedicated browser checks.
- Deployment input dry run: 864 WebPs; no learner databases, environment files,
  archives or local duplicate copies included. Existing FastAPI Primer project
  and Vercel account verified. Production alias must not move before verification.

## Release result — 7 September 2026

All final-source local checks passed:

- 31,936 pytest tests passed; 2 skipped. The two warnings concern the local
  Python 3.9 environment; production uses Python 3.12.
- 176 concept, 14 spatial and 70 legacy browser bindings passed: all 260 models.
  These runs include desktop/mobile and current-source hash verification.
- Mobile/desktop navigation, context labels, keyboard/Escape, focus and settings
  checks passed. All 432 illustration reviews remain current; zero stale.
- `git diff --check` passed.

Production deployment `dpl_pZJmJZd3JsnoXVEH55osqgFUKHES` is READY and was promoted
to `https://primer-antonpeterdoubell-7333s-projects.vercel.app`.
Its immutable deployment URL is
`https://primer-31fiuccfu-antonpeterdoubell-7333s-projects.vercel.app`.
The FastAPI build used Python 3.12 and completed in six seconds; the resulting
function bundle is 87,395,477 bytes. This is a deployment of the verified local
working tree, not a claim that the branch has been merged or pushed.

Both staged and promoted-alias health responses reported 432 nodes and zero
local archives. The promoted sign-in page returned 200, and the gallery API
returned the expected unauthenticated 401. The deployment's post-release error
log scan returned zero entries. Vercel's outer SSO was accessed through its
authenticated CLI, not disabled. No persistent monitoring or drains were added.
An authenticated remote
gallery/asset/browser check was **not** possible: the production application
password is a non-retrievable Sensitive variable. Vercel protection and Primer's
own sign-in remain enabled; no gate was bypassed or disabled. All-model and
image-quality verification above is local, not an authenticated production test.

### Packaging incident and correction

The first normal upload failed before deployment creation. The archive retry
created `dpl_6Dejns8KaVjzazCiajpsZ595nskv`, but its build failed at 938 MB.
Vercel CLI 58.9.0's archive packer recursively includes directory entries:
patterns such as `content/` hid their children in the dry listing but left the
directory itself, so the archive included ignored local content/databases and
backups. That failed deployment was deleted; it never served the application.
Deletion was confirmed by the CLI. This does not establish a provider-side
retention guarantee for uploaded build inputs.

Changed the exclusions to remove directory entries themselves (`content`,
`tools`, `tests`, etc.). Added `tools/prepare_release.cjs`: it rejects forbidden
paths, directories and symlinks, checks file sizes/content hashes, then copies
only the approved regular files into a fresh temporary release directory. Only
the project identity file is copied from `.vercel`, never environment secrets.
The successful archive was created from that clean directory. Its build log
confirms exactly 917 extracted files, matching the 49,471,263-byte manifest;
864 are responsive WebP images. Local data and recovery duplicates are intact.
