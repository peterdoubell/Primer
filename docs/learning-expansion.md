# Learning pathways: age three to master's level

The Primer now has 558 lessons across 19 broad fields, including the eight Grade 1–8 music lessons preserved from the live release. This expansion adds 96
lessons in eight fields and ten nonclinical imaging foundations. All 19 fields
have content at each of the six stages. These are expandable learning pathways,
not complete degree programs or an exhaustive catalogue of every specialism.

| Stage | Level | Teaching emphasis |
| --- | --- | --- |
| Seedling | Ages 3–5 | Adult-supported play, observation, speaking and pointing |
| Sprout | Ages 6–9 | Concrete examples, simple comparisons and explanations |
| Sapling | Ages 10–13 | Quantitative foundations, evidence and structured inquiry |
| Tree | Ages 14–17 | Models, arguments, experiments and applied problems |
| Grove | Undergraduate | Disciplinary methods, analysis and evaluation |
| Forest | Master's | Research design, uncertainty, synthesis and critique |

The original fields remain: mathematics; language; physics; life sciences;
chemistry; computer science; history; Earth and space; arts and music; mind,
society and philosophy; and radiology. New pathways cover engineering; health;
environment and agriculture; architecture and design; business and economics;
law and civics; education; and communication and media.

Each new field has two lessons per stage. Every new lesson includes an authored
explanation, worked example, activity, reflection, at least three outcomes and
an assessment bank. Early lessons also include concise read-aloud text.
Older banks contain ten choice questions and a produced-response question.
The new lessons add 986 assessment items, bringing the initial expansion total to 5,403; the merged music path brings it to 5,483.
Prerequisites connect new fields to existing mathematical, scientific and
humanistic foundations. Reading, assessment and spaced mastery continue using
the existing progression rules.

Radiology begins with shadows, viewpoints, layers, pixels and signal
interpretation, then progresses to reconstruction and validation. The original
96 advanced clinical references retain their content and reporting tools.
Their professional entry route remains available without crediting or skipping
the new imaging foundations. `reference_stage` records this separate route.
Introductory imaging lessons do not become clinical reports or child-facing
diagnosis tasks. Clinical and conceptual imaging illustrations have separate
generators so regenerating one cohort preserves the other.

## Visual material

Every lesson has an explanatory illustration and an interactive spatial
model. (The shared AI-generated contextual scenes that once accompanied them
were removed on 26 September 2026; see [module-media.md](module-media.md).)
Diagrams are authored lesson by lesson using the existing deterministic drawing system, with complete text
equivalents. The 3D companions use the established interactive object library;
their explanations explicitly distinguish a physical study context from a
simulation of a social, clinical or abstract process.

Atlas and the visual gallery have field and stage filters, age/academic labels,
coverage counts and links back to each lesson. Teaching bodies and large media
stay out of compact navigation responses. The new teaching content is rendered
as plain text and supports read-aloud for early learners.

## Maintenance

Curriculum JSON under `data/curriculum/` is the runtime source of truth. The
new `lesson`, `learning_outcomes`, `visual_spec`, `model_family` and
`model_context` fields make lessons and diagrams maintainable without relying
on a remote content generator. To regenerate the expansion media:

```sh
.venv/bin/python tools/generate_expansion_media.py
.venv/bin/python tools/generate_module_models.py
```

The rendering script accepts `--domain` for a single field. It refuses to
replace another illustration's ID and fails when text cannot fit its diagram.

Relevant checks include `tests/test_learning_expansion.py`, the existing
curriculum/media/API tests, `tools/check_curriculum_illustrations.py`,
`tools/check_model_coverage.py --require-complete`,
`tools/check_module_models.js`, and `tools/check_learning_pathways.cjs` against
an isolated development reader. Browser and asset review evidence is stored in
`artifacts/learning-expansion/` when those checks run.

## Verification before merging the live release, 2026-09-24

- Full Python suite: 32,079 passed, two existing skips.
- Illustration audit: 550 unique diagrams, 1,100 responsive WebPs, no missing
  or orphaned assets. All 106 new diagrams were inspected in contact sheets.
- Runtime model audit: all 550 lessons covered; 799 interactive entries,
  including 553 spatial entries. The 454 shared-object bindings pass 998
  deterministic geometry builds and quantitative invariants.
- All eight new subject banks pass the existing assessment authoring audit.
- Browser checks: 71 real lesson routes, all 19 fields, 41 shared object
  families, all 60 photograph resolutions decoded, keyboard/mouse/touch
  controls, camera/model reset, image enlargement and focus restoration,
  field/stage filtering, early read-aloud controls, and mobile-width checks.
  No uncaught JavaScript exceptions occurred.
- The clinical shortcut was verified separately: 96 reference modules open
  while the ten imaging-foundation mastery records remain untouched.

Browser QA used a disposable local reader. Local lesson/media behavior was
tested; this does not establish external encyclopedia availability or certify
the pathways as complete academic programs. Human subject-expert review remains
separate from structural checks and automated visual inspection.
