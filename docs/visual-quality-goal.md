# Primer: curriculum-wide visual quality goal

## Objective

Review, debug, upgrade and optimise the images, illustrations and interactive
models throughout **every subject, module and lesson, from introductory through
postgraduate levels**. This is not restricted to biology, mathematics or science.
Use the mathematics visuals as the quality benchmark while choosing a visual
language appropriate to each subject. Every visual should explain something
specific, not merely decorate a lesson.

## Scope and completion criteria

- Audit every lesson's visuals, including authored illustrations, imported
  article images and existing interactive models. Track coverage and remaining
  issues; asset counts alone do not establish visual quality.
- Fix broken, placeholder, partially rendered, blurry or distorted images and
  models across the reader and gallery. Preserve useful small source images at
  appropriate sizes rather than enlarging them into blurry illustrations.
- Upgrade weak or overly simplistic visuals to a consistent standard of
  composition, typography, colour, detail and explanatory clarity. Keep visuals
  that already meet that standard and preserve subject-specific meaning.
- Add or improve illustrations to augment every lesson. Use meaningful labels,
  comparisons, worked examples, mechanisms or relationships appropriate to the
  learner's level; avoid generic decorative abstractions.
- Add or improve interactive models where manipulation helps understanding.
  Use 3D where depth, orientation or spatial structure matters; use 2D diagrams,
  timelines, maps, networks or other interactions where those communicate better.
  Do not impose 3D on every subject or lesson.
- Verify factual relationships, model behaviour, meaningful controls and reset
  behaviour. State schematic simplifications and provide accessible explanatory
  text alongside visual information.
- Verify readability, image loading, responsive layout, keyboard/touch operation
  and performance on desktop and mobile. Avoid unnecessary dependencies,
  continuous animation and redundant regeneration of good assets.
- Keep the gallery useful across all subjects and levels, with clear subject
  and lesson context. Retain the requested toggleable navigation panel and
  visible current-lesson context while reading or scrolling.

## Execution

### Illustration review evidence

Run `python tools/check_illustration_reviews.py --json` to enumerate every
lesson's current illustration review state. Records in
`docs/illustration-reviews.json` fingerprint both responsive image files,
illustration metadata and the lesson's title, stage and goal. A changed input
makes a record stale. Add records only after inspecting the actual images and
recording the explanatory-quality finding and evidence; never populate approvals
from file existence or successful rendering alone.

The ledger initially contains six recent, directly verified reviews. A pending
record means review evidence has not been reconciled into this ledger, not that
the image necessarily lacks prior review or needs regeneration. Reconcile the
existing audit notes and current bytes before repeating work. The optional
`--require-complete` check fails unless every illustration has a current record;
this establishes traceable review coverage, not correctness by itself. Model
verification, runtime behavior and the rest of the release criteria remain
independent requirements.

The active goal requires explanatory illustrations and **appropriate interactive
models across all 432 lessons**, then deployment after verification. Earlier
execution notes incorrectly expanded this into a compulsory interaction in
every lesson. All lessons remain in scope: assess whether manipulating a
parameter, sequence, viewpoint or evidence set adds understanding. Add a model
where it does; record a lesson-specific rationale where a static explanation
already serves the concept. Neither a generic rotating scene nor a text-only
selector earns completion merely by increasing the model count.

Run `python tools/check_model_coverage.py --json` to locate lessons without
models for this assessment. Its `--require-complete` mode remains available to
measure universal model presence, but presence in every lesson is not the
user's stated acceptance criterion. Release still requires reviewed illustrations
for every lesson, completed model-appropriateness assessments, verification of
every included model, and numerical, browser, accessibility and runtime checks.
Do not deploy an unreviewed partial cohort as the final deliverable.

Mathematics and science are the starting sequence, not the scope boundary.
Continue across the entire curriculum, prioritising rendering defects and the
largest explanatory-quality gaps. Preserve existing work and report actual
verified coverage rather than declaring all subjects complete after one cohort.

This document records the user's broadened working objective. It does not claim
that the active Codex `/goal` metadata has been rewritten: the available goal
tools can read that objective and change completion/blocking status, but cannot
edit the text of an unfinished goal. Keep that goal active while work remains.
