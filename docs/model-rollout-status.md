# Curriculum-wide visual and model rollout

Completed and deployed 2026-09-07: explanatory illustrations across all 432
lessons and 260 appropriate interactive models. Final checks: 31,936 tests;
176 concept + 14 spatial + 70 legacy browser bindings; navigation passed.
Production deployment: `dpl_pZJmJZd3JsnoXVEH55osqgFUKHES`.
See `release-visual-audit.md` for the deployment evidence, authenticated remote
verification limitation and corrected archive-packaging incident. The entries
below are historical progress checkpoints, not the current release status.

2026-09-07 release checkpoint: all 432 illustration review records are current.
Added `arts.1.beat`: independent tempo/equal-subdivision controls on a fixed
eight-second timeline, with note-onset/beat/end-boundary distinctions and a
silent-practice limitation. Thirty tempo/subdivision combinations pass exact
timing invariants; 31,000 concept tests pass. Desktop/mobile control, reset and
keyboard checks passed the new model; the mobile rendering was inspected.
Then reduced dense-note radii so onsets remain distinct at maximum tempo and
four subdivisions. Latest counts: 257/432 lessons with 260 model entries.
No universal-model requirement is inferred; remaining appropriateness review
must distinguish genuine interactive benefit from physical/interpretive practice.

All 14 spatial scenes and mobile navigation passed. The earlier full concept
sweep exercised its scenarios but failed the final source-hash gate because
app.js changed during the run: do not cite it as current-source verification.
Restarted isolated QA server: session 47765, port 8768, database
`/tmp/primer-release-qa.EBDCUR/primer.db`. Current-source full concept sweep:
session 93555, log `/tmp/primer-release-qa.EBDCUR/concepts-current.log`.
Full current pytest: session 72113, log `/tmp/primer-release-current-tests.log`.
The prior full suite passed 31,579 tests before the last rate-limit/model changes;
146 network/API/hosted tests pass for the rate-limit change. Fresh browser
confirmed Genetics article loaded, rather than remaining in its skeleton/error.
Vercel CLI authentication and linked FastAPI Primer project confirmed; upload
exclusions hardened for databases, environment files and local duplicate copies.
No deployment yet. Keep the active objective open.
Scope correction: older checkpoints below treated universal model presence as
mandatory. That overstated the user's goal. Missing-model counts are an
assessment inventory, not proof that every listed lesson needs an interaction.
No lesson is exempt from visual-quality review and model-appropriateness
assessment. Existing model verification requirements remain in force.

2026-09-05 checkpoint: `tools/check_model_coverage.py` reports 256/432 lessons
covered, 259 model entries, 176 lessons missing models. Three extra entries are
companions on already-covered lessons. Use `--json` for the full current backlog;
these snapshot counts are not a release certificate.

Computer-science stages 0–3 add 20 current 800px reviews, bringing the ledger to
217/432. Nine plates received concrete corrections, including array bounds,
commit/reference semantics and control-flow readability. Ten focused tests and
all 74 language/CS asset pairs pass. See
`docs/computer-science-illustration-review.md`. Later CS stages, remaining subject
reviews, final model/runtime verification and deployment remain unfinished.

All 39 physics illustrations are now reconciled at 800px, bringing the ledger to
197/432. The advanced pass corrected thirteen further plates and added four
geometry/accounting regressions. Twenty focused tests and the full 39-pair
physics checker pass. See `docs/physics-illustration-review.md`. Other-subject
review, model-appropriateness assessment, final runtime checks and deployment
remain unfinished.

Physics stages 0–2 add 17 current 800px reviews, bringing the ledger to 175/432.
Nine native plates were corrected, including a shorted parallel-circuit drawing,
disconnected magnetic loops and misleading particle spacing. Sixteen focused
tests pass; all 39 physics pairs pass the asset checker. See
`docs/physics-illustration-review.md`. Later physics stages, other remaining
subjects, final model/runtime checks and deployment are still unfinished.

Earth and space's 27/27 illustrations are reconciled at 800px, bringing the
current ledger to 158/432. Eighteen native plates received specific corrections,
including transfer-orbit focus/tangency, liquid-boundary S-wave endpoints and
logarithmic radial spacing. Twenty-five focused Earth/chemistry/biology/review
tests pass; all 93 natural-science pairs pass their deterministic/integrity check.
See `docs/earth-illustration-review.md`. Remaining subject review,
model assessment, final runtime verification and deployment are unfinished.

Chemistry's 29/29 illustrations are now reconciled at 800px, bringing the current
ledger to 131/432 with no stale records. Twelve native plates received targeted
corrections, and eight lesson descriptions were aligned with actual imagery.
Twenty-one focused chemistry/biology/review tests pass, including sand containment,
gas-legend bounds, mole units, equal-volume nanoparticle geometry and science
glyph coverage. All 93 natural-science pairs pass their deterministic/integrity
check. See `docs/chemistry-illustration-review.md`. Remaining subjects, final
browser/model checks and deployment are still unfinished.

Biology's 37/37 lesson illustrations are now reconciled at 800px, bringing the
ledger to 102/432 with no stale records. Twenty native biology plates received
concrete layout/glyph/provenance corrections; six curriculum descriptions were
aligned or qualified. Sixteen focused tests pass, including a missing-glyph check
across all 85 generated natural-science plates. All 93 natural-science responsive
pairs pass their deterministic/integrity check. Mathematics and biology reviews
are complete at this resolution; other-subject review, final browser/model checks
and deployment remain unfinished. See `docs/biology-illustration-review.md`.

Biology stages 0–3 now have 25 current reviews, bringing the ledger to 90/432
with no stale records. Twelve native plates were corrected, including the
genetics caption overflow; photosynthesis and evolution descriptions were also
aligned with their actual schematics. Fifteen focused biology/review tests pass.
The remaining twelve biology plates and other-subject backlog still require
reconciliation, followed by final runtime/model checks and deployment.

Introductory biology reconciliation adds eleven records, bringing the current
ledger to 76/432. Five plates were corrected for overlapping roots, captions or
labels, an inaccurate broad-leaf grass glyph, and health icons covering prose.
Seven focused biology tests and the deterministic 93-lesson natural-science
asset check pass. See `docs/biology-illustration-review.md` for scope; deployment
and the remaining all-subject review are unfinished.

Mathematics illustration reconciliation is now 59/59, with 65/432 current
records overall. All remaining stages 4–5 plates were inspected at 800px.
Two native-source improvements were rendered: a logistic label moved off a
neighboring curve, and numerical-analysis plots gained explicit function labels.
This completes the mathematics 800px content pass only; final runtime/model
verification and the remaining subject reviews are still required.

Stage-3 mathematics review adds fifteen current records, for 46/432 overall.
Population-SD labels and their caption were clarified, and probability-tree
node labels were moved off the branches. Both corrected plates were rerendered
and inspected at 800px. Five focused cohort tests pass, including independent
population-SD calculation. The other thirteen diagrams were preserved.

Mathematics stage-2 reconciliation adds twelve inspected plates, bringing the
current illustration ledger to 31/432 with no stale records. Their 800px
renderings were checked against curriculum descriptions and exact worked
quantities. Geometry alt text was corrected in curriculum and generator to
describe two layer plans rather than an unseen cuboid rendering. All 59 math
illustration pairs pass their checker. No raster was regenerated or model added.
Full review, model-appropriateness assessments and deployment remain unfinished.

Review reconciliation now includes mathematics stages 0 and 1. The ledger has
19 current records: stage 0 was inspected at both resolutions; stage 1 was
inspected at 800px against curriculum descriptions, with that limitation explicit.
Worked counts, arithmetic, clock hands, ruler/liquid marks and fractional areas
agree with their labels. No assets were regenerated in this review pass.

Release-audit follow-up: `tools/check_illustration_reviews.py` now inventories
all 432 lessons and invalidates review records when either responsive image,
illustration description or lesson context changes. Six recent inspections
have been reconciled into `docs/illustration-reviews.json`; 426 remain pending
reconciliation, not automatically defective. Thirteen focused review/coverage
tests pass. This audit is not an automated quality judge and cannot replace
inspection, model verification or runtime checks. No deployment was made.

Maps and Places visual follow-up: replaced its text-only map description with
an actual invented map, matched legend, north arrow and proportional graphical
scale. The six-kilometre route is checked across four resize factors. Both
responsive images were visually inspected; four focused cohort tests and the
83-lesson humanities checker pass. Coverage counts are unchanged. This improves
visual teaching quality but does not complete or deploy the rollout.

Introductory history visual follow-up replaces the text-only community-helper
and long-ago plates with concrete tools, a bounded 1840 British postal example,
a present-day phone, and surviving evidence. Curriculum descriptions match the
new drawings. Both resolutions were visually inspected; focused cohort tests
pass (three tests), including deterministic rendering of the two replacements.
All 83 humanities pairs, the 432-lesson illustration audit and whitespace checks
pass. See `docs/cross-subject-visual-audit.md` for the source and limitations.
Coverage counts are unchanged; this is visual-quality progress, not a claim of
completed rollout. No browser process or test process was left running by this
pass, and no deployment was made.

Latest verification and visual-quality pass: the full current application suite
passed **31,525 tests**, two external-fixture skips and two Python 3.9 warnings
(`/tmp/primer-full-language-checkpoint.log`, 144 seconds). This run includes
etymology and all earlier language additions. Three subsequent static upgrades
replace the fairness stick markers with clothed figures while preserving eye
and support heights, put the feelings comparison in a shared school setting,
and replace the unscaled musical contours with an original four-beat,
pitch-labelled interval example. Their focused tests pass (three tests),
including exact pitch differences and deterministic responsive rerendering.
All 83 humanities illustration pairs and the 432-lesson asset audit pass.
Both image resolutions were visually inspected; the feelings lesson also
loaded correctly at 390px, with no page overflow, working full-resolution
picture opening and Escape restoring focus. No new model entry was added in
this pass. Mythology research was started but no model was implemented.
The full release remains unfinished and has not been deployed.

Etymology now compares three sourced transmission routes, including the French
intermediate for portable and the distinct Latin formations of import/export.
The model does not substitute root meanings for modern usage or claim that
English formed the words from its own word port. Exact route checks and
**30,674 focused tests** pass, 115 deselected, two existing warnings
(`/tmp/primer-etymology-tests.log`). All three word states pass keyboard/reset
and desktop/mobile browser checks (`/tmp/primer-etymology-qa/`); the portable
route was visually reviewed on mobile. Illustration and whitespace checks pass.
Language is now 21/40 covered; mythology is the remaining stage-2 gap. Current
isolated QA server: PID 41059, session 50159, port 8768, same temporary database.
No deployment: 176 lessons and final curriculum-wide quality review remain.

Poetry and novel tracking now have models. Sixteen metrical settings are checked
against independent binary stress patterns and exact foot partitions; category
heights and spacing are explicitly not loudness or timing measurements. Eight
chapter/perspective states preserve the story while exposing a reader/character
knowledge gap in chapter 2; the character learns the mapmaker’s identity only
in chapter 3. Displayed event history stops at the selected chapter. Focused
tests pass **30,325**, 115 deselected, two existing warnings
(`/tmp/primer-poetry-novels-tests.log`). Browser checks pass eight poetry and six
novel states with keyboard/reset and desktop/mobile coverage
(`/tmp/primer-poetry-novels-qa/`). Four anapestic feet and Mina’s chapter-2
knowledge were visually reviewed on mobile. Illustration and whitespace checks
pass. Language is now 20/40 covered. Current isolated QA server: PID 40378,
session 30043, port 8768, same temporary database. No deployment: 177 lessons
and final curriculum-wide quality review remain.

Research and public speaking now have models. Twelve provenance/question/source
states are independently checked by traversing copy edges to their roots;
three agreeing documents do not imply three original records, and agreement on
an opening year cannot answer a cost question. Eight speaking states preserve
example content while changing audience-specific explanation and optional
spoken signposts; neither signposts nor source counts become confidence scores.
Focused tests pass **29,633**, 115 deselected, two existing warnings
(`/tmp/primer-sources-speaking-tests.log`). Browser checks pass nine research
and eight speaking states with keyboard/reset and desktop/mobile coverage
(`/tmp/primer-sources-speaking-qa/`). The copied-source chain and the signposted
talk were visually reviewed on mobile. Illustration and whitespace checks pass.
Language is now 18/40 covered. Current isolated QA server: PID 39403,
session 27658, port 8768, same temporary database. No deployment: 179 lessons
and final curriculum-wide quality review remain.

Intermediate grammar and paragraph organization now have models. Twelve
grammar states preserve nested NP/VP/PP constituents while exposing independent
subject/verb agreement errors; the plural noun inside the PP does not control
agreement. Eight paragraph states preserve content when reordered and separate
relevant invented availability evidence from unrelated badge color; adding an
explanation or changing order cannot repair irrelevant evidence. Focused tests
pass **28,949**, 115 deselected, two existing warnings
(`/tmp/primer-grammar-paragraph-tests.log`). Browser checks pass nine grammar
and eight paragraph states with keyboard/reset and desktop/mobile coverage
(`/tmp/primer-grammar-paragraph-qa/`). The highlighted PP with mismatched agreement
and reordered irrelevant evidence were visually reviewed on mobile. Illustration
and whitespace checks pass. Language is now 16/40 covered. Current isolated QA
server: PID 38778, session 6640, port 8768, same temporary database. No deployment:
181 lessons and final curriculum-wide quality review remain.

Phonics and handwriting complete language stages 0–1. The adult-supported
blending guide checks all 12 word/progress states, explicitly separating sounds
from letter names and acknowledging that ordinary TTS is not a reliable source
of isolated phonemes. The handwriting guide checks all 12 letter/progress/guide
states, with ordered pen lifts, separate dot/cross strokes and invariant
baseline geometry. Movement arrows were placed outside the letter so they are
not mistaken for additional ink. Focused tests pass **28,273**, 115 deselected,
two existing warnings (`/tmp/primer-phonics-handwriting-tests.log`); the semantic
checker was rerun after the arrow refinement and passes. Browser checks pass
seven phonics and eight handwriting states with keyboard/reset and
desktop/mobile coverage (`/tmp/primer-phonics-handwriting-qa/`). Completed blending
and the guided lowercase t were visually reviewed. Illustration and whitespace
checks pass. Language coverage is 14/40. Current isolated QA server: PID 38171,
session 24466, port 8768, same temporary database. No deployment: 183 lessons
and final curriculum-wide quality review remain.

Talking/listening, reading response and story planning now have models. Six
conversation states distinguish relevant answers, mismatches and useful
clarification without social scoring. Nine passage/claim states separate textual
evidence from uncertain motives and unsupported always-claims. Twelve story
planning states connect the selected action to an invented resolved/open ending,
with no premature kite recovery. An initial test caught a missing model-object
closing brace; after correction **27,605 focused tests pass**, 115 deselected,
two existing warnings (`/tmp/primer-conversation-stories-reviewed-tests.log`).
Browser checks pass 7 conversation, 8 reading and 8 planning states with
keyboard/reset and desktop/mobile coverage (`/tmp/primer-conversation-stories-qa/`).
Clarification, the unsupported generalization and an unresolved ending were
visually reviewed on mobile. Illustration and whitespace checks pass. Language
is now 12/40 covered. Current isolated QA server: PID 37537, session 7303,
port 8768, same temporary database. No deployment: 185 lessons and final
curriculum-wide quality review remain.

Word collecting and dictionary use now have explanatory interactions. The
dictionary comparator checks all 288 word-pair/reveal states against an explicit
ordered list, including prefix endings and equality; later letters cannot
reverse an established order. Nine vocabulary/scene combinations keep lexical
meaning independent of scene evidence rather than assigning arbitrary scores
or physical speeds to words. Focused tests pass **26,618**, 115 deselected and
two existing warnings (`/tmp/primer-word-choices-tests.log`). Browser checks
pass 16 dictionary and eight vocabulary states with keyboard/reset and
desktop/mobile coverage (`/tmp/primer-word-choices-qa/`). Mobile prefix ordering
and the trudged/muddy-path comparison were visually reviewed. Illustration and
whitespace checks pass. Language is now 9/40 covered. Current isolated QA server:
PID 36797, session 67278, port 8768, same temporary database. No deployment:
188 lessons and final curriculum-wide quality review remain.

Early writing adds six checked sound–spelling maps and a sentence builder.
All 18 word/sound states preserve grapheme order and letter coverage, including
two letters for one sound and distinct TH sounds in thin/this. All 32 sentence
states distinguish clause completeness from capitalization and punctuation;
adding a full stop cannot turn the subject-only fragment into a full clause.
Focused tests pass **25,970**, 115 deselected and two existing warnings
(`/tmp/primer-writing-basics-tests.log`). Mobile review prompted friendlier
yes/no toggle wording for language models; the revised semantic checker and
all 22 desktop/mobile browser states pass (`/tmp/primer-writing-basics-reviewed-qa/`).
The final SH letter mapping and the punctuated fragment were visually reviewed.
Illustration and whitespace checks pass. Language coverage is 7/40. Current
isolated QA server: PID 36061, session 19751, port 8768, same temporary database.
No deployment: 190 lessons and final curriculum-wide quality review remain.

Introductory language now includes rhyme comparisons and story-clue tracking.
All 20 word pairs are checked against an explicit rhyme-pair oracle, including
blue/shoe (matching sounds despite different letters) and nonmatches. All 18
story/event/clue combinations preserve character, setting and object state;
searching does not prematurely recover the missing object. These are original
short stories, not a universal three-event narrative rule. The focused suite
passes **25,330 tests**, 115 deselected and two existing dependency warnings
(`/tmp/primer-rhyme-story-tests.log`). Browser checks pass 11 rhyme and nine
story states, including keyboard/reset and desktop/mobile checks
(`/tmp/primer-early-language-qa/`). Mobile alternate spelling and the recovered
hat sequence were visually reviewed. All illustration bindings and whitespace
checks pass. Language is now 5/40 covered. Current isolated QA server: PID 35394,
session 64285, port 8768, same temporary database. No deployment: 192 lessons
and final curriculum-wide quality review remain.

All 27 Earth & Space lessons now have models (28 entries). The postgraduate
cohort adds flat matter–Λ expansion (80 settings), hypothetical biosignature
Bayesian inference (1,800), ice–albedo feedback (810), and transverse
gravitational-wave polarization (910). Independent checks cover Friedmann and
acceleration identities, probability/count conservation, ring deformation and
orientation response, and energy-balance trajectories against a separate
fine-step Euler integrator plus analytic cold/warm equilibria. The models
explicitly distinguish assumptions from measured parameters, forecast claims
and astrophysical strain amplitudes. Browser checks pass 6 cosmology, 8
astrobiology, 10 feedback and 10 polarization states with keyboard/reset and
desktop/mobile coverage (`/tmp/primer-postgrad-earth-qa/`). Mobile low-base-rate
inference, accelerating expansion, cold/warm climate branches and cross-mode
detector response were visually reviewed. All 432 illustration bindings and
864 WebPs pass validation. Current isolated QA server: PID 34648, session 45488,
port 8768, same temporary database. Full regression passes **25,549 tests**,
two existing external-fixture skips and two Python 3.9 dependency warnings
(`/tmp/primer-full-earth-complete.log`). No deployment: 194 lessons and final
curriculum-wide quality review remain.

The remaining university Earth lessons now have models: planetary atmospheric
retention compares escape/RMS speeds and Jeans binding without a binary loss
threshold; climatology integrates a declining emissions trajectory and applies
an explicitly assumed CO₂-only TCRE; ocean/atmosphere science balances pressure
and Coriolis accelerations with hemisphere-dependent geostrophic velocity and
unavailable inversion at the equator. Independent tests cover all 720 retention,
975 emissions and 81 flow settings. A first renderer check caught insufficient
structure in the speed chart; a labeled shared speed axis was added. The revised
suite passes **23,458 focused tests**, 115 deselected, two existing warnings
(`/tmp/primer-university-earth-reviewed-tests.log`). Browser checks pass 13
retention, 11 emissions and seven flow states with keyboard/reset and
desktop/mobile coverage (`/tmp/primer-university-earth-qa/`). Weak gravitational
binding, the post-zero cumulative plateau and Southern Hemisphere force/flow
directions were visually reviewed. Sources link atmospheric escape research,
IPCC and NOAA. Illustration and whitespace checks pass. Earth coverage is 23/27
lessons (24 entries), with all stage 0–4 lessons covered. Current isolated QA
server: PID 33126, session 72948, port 8768, same temporary database.
No deployment: 198 lessons and final curriculum-wide quality review remain.

Geophysics now compares P/S arrival times and S–P path-length inference in a
uniform medium, with unavailable shear propagation/inference on a liquid path.
All 330 distance/speed/ratio/medium settings match travel-time identities;
the model explicitly does not infer source direction or liquid from absence
of an observed S arrival alone. Astrophysics compares normalized per-wavelength
Planck spectra with a redshift transformation. All 171 temperature/redshift
settings match an independent direct-Planck expression, peak scaling and bounded
normalization; a 6000 K source at z=1 matches the normalized shape of an
unredshifted 3000 K source. Absolute flux and velocity inference are excluded.
USGS and NASA sources are linked. **22,549 focused tests pass**, 115 deselected,
two existing warnings (`/tmp/primer-waves-spectra-tests.log`). Eleven seismic
and six spectral browser states pass keyboard/reset and desktop/mobile checks
(`/tmp/primer-waves-spectra-qa/`); liquid-path unavailability and the long-wavelength
redshift boundary were visually reviewed. Illustration and whitespace checks
pass. Earth coverage is 20/27 lessons (21 model entries). Current isolated QA
server: PID 32280, session 69062, port 8768, same temporary database.
No deployment: 201 lessons and final curriculum-wide quality review remain.

Astronomy now compares effective temperature, radius and bolometric luminosity
on logarithmic H–R axes with constant-radius guides, explicitly not evolutionary
tracks or age estimates. All 140 parameter pairs satisfy Stefan–Boltzmann scaling,
including a sixteenfold luminosity increase when temperature doubles. Biomes
and Ecology keeps annual rain at 1200 mm but changes timing and storage; all
720 seasonal/capacity/demand/inspection settings conserve water through ET,
drainage and final storage. The coarse within-month ordering and empty initial
store are explicit. Ohio State, IAU and NOAA sources are linked. **21,953 focused
tests pass**, 115 deselected, two existing warnings
(`/tmp/primer-stars-biomes-tests.log`). Nine astronomy and ten biome browser
states pass keyboard/reset and desktop/mobile checks
(`/tmp/primer-stars-biomes-qa/`); a cool large star and the seasonal water-deficit
view were visually reviewed. Illustration and whitespace checks pass. Earth is
18/27 lessons (19 model entries), with every stage 0–3 lesson now covered.
Current isolated QA server: PID 31735, session 43805, port 8768, same temporary
database. No deployment: 203 lessons and final curriculum-wide quality review
remain. The last full regression predates the two latest stage-3 batches.

Climate Science now balances a single grey infrared layer against absorbed
sunlight: all 693 albedo/emissivity/solar settings satisfy the surface, layer
and top-of-atmosphere flux balances. Zero emissivity leaves layer temperature
unconstrained (null), not zero kelvin. Space Exploration tracks initial, remaining
and expelled mass with ideal rocket Δv: all 13,950 dry/propellant/exhaust/burn
settings satisfy mass conservation and inverse exponential mass-ratio checks,
including zero propellant and full burns. UBC and NASA reference derivations
are linked; forecasts, CO₂ calibration and launch feasibility are explicitly
outside these teaching models. **21,365 focused tests pass**, 115 deselected,
two existing warnings (`/tmp/primer-energy-rockets-tests.log`). Eight climate
and ten rocket browser states pass keyboard/reset and desktop/mobile checks
(`/tmp/primer-energy-rockets-qa/`); full-opacity energy balance and complete
propellant exhaustion were visually reviewed. All illustration and whitespace
checks pass. Earth is 16/27 lessons with models (17 entries). The latest full
regression below predates this two-model batch. Current isolated QA server:
PID 31148, session 43170, port 8768, same temporary database. No deployment:
205 lessons and final curriculum-wide quality review remain.

The Changing Earth now compares across-boundary separation and along-boundary
sliding using markers attached to plates, without pretending to simulate
subduction or hazard. All 21 boundary/step pairs satisfy the expected relative
motions. Oceans and Rivers adds a lunar/solar angular tide profile: all 312
alignment/direction settings match an independent sine/cosine decomposition,
bounded amplitude, zero-mean periodic profile and spring/neap range checks.
USGS and NOAA sources are linked. **20,785 focused tests pass**, 115 deselected,
two existing warnings (`/tmp/primer-plates-tides-tests.log`). Eight plate and
seven tide browser states pass keyboard/reset and desktop/mobile checks
(`/tmp/primer-plates-tides-qa/`). Transform motion and nonzero neap range were
visually reviewed. Illustration and whitespace checks pass. Earth is now
14/27 lessons with models (15 entries), including every stage 0–2 lesson.
Current isolated QA server: PID 30312, session 19625, port 8768, same temporary
database. No deployment: 207 lessons and final curriculum-wide quality review
remain. Full regression at this milestone: **21,636 passed, 2 skipped, 2 warnings
in 102.76s** (`/tmp/primer-full-early-earth.log`). No frontend changed during the
run. The skipped integration checks require throwaway Turso credentials and a
substantial real offline article corpus; neither gap is a release certificate.

Weather and Climate now separates an invented same-calendar-date 30-year
reference from a day outside that period. All 2,550 shift/departure/year settings
preserve the reference independently of today's departure. Caring for Earth
tracks source reduction, collection capacity, environmental stock and managed
storage; all 405 settings match an independent closed-form stock calculation
and conserve actual incoming material without counting avoided generation as
a physical store. NOAA and EPA sources are linked, with clear teaching-model
limitations. **20,213 focused tests pass**, 115 deselected, two existing warnings
(`/tmp/primer-climate-waste-tests.log`). Visual review prompted a usability fix:
the reference-year control now uses 1–30, matching the chart. Subsequent full
semantic verification passes 144 cross-subject models, 397 controls and 43,009
deterministic builds (`/tmp/primer-climate-waste-semantic.log`). Both browser
models pass again: climate eight states, waste nine, with keyboard/reset and
desktop/mobile checks (`/tmp/primer-climate-waste-reviewed-qa/`). The corrected
cold-day comparison and complete-collection boundary were visually reviewed.
All illustration bindings, WebPs and whitespace checks pass. Earth coverage
is 12/27 lessons (13 entries). Current isolated QA server: PID 29451,
session 68934, port 8768, same temporary database. No deployment; 209 lessons
and the final curriculum-wide quality review remain.

Four more Earth/space activities compare weather measurements, planet order
versus linear Sun distance, physical planet diameters versus spherical volume,
and stellar emission versus received flux. NASA JPL reference distances and
diameters are linked; the star model links NASA's inverse-square explanation.
Weather records are explicitly invented, with rain and new snowfall distinguished.
Independent checks cover all 16 weather comparisons, 16 planet/scale settings,
64 planet-size pairs and 64 luminosity/distance settings, including equal flux
from different luminosity/distance pairs and the inverse-square doubling rule.
**19,649 focused tests pass**, 115 deselected, two existing warnings
(`/tmp/primer-earth-observations-tests.log`). All four browser models pass:
weather 11 states, solar distances 12, planet sizes 18, stellar flux 6, with
keyboard/reset and desktop/mobile checks (`/tmp/primer-earth-observations-qa/`).
Below-zero temperature, Mercury's crowded linear position, Jupiter/Mercury size
contrast and faint/distant stellar flux were visually reviewed. All 432
illustration bindings, 864 WebPs and whitespace checks pass. Earth now has
10/27 lessons with models (11 entries); all seedling and sprout Earth lessons
have model presence. No full regression rerun for this four-model batch; the
focused suite includes semantic renderer verification. Current isolated QA
server: PID 28903, session 80735, port 8768, same temporary database.
No deployment: 211 lessons and final curriculum-wide quality review remain.

Land and Water now includes a downhill-route activity comparing a ridge with a
closed basin. All 98 terrain/start/step settings match independent expected
routes and strictly descending heights; caveats explicitly exclude infiltration,
evaporation, filling and overflow. USGS watershed guidance is linked in the model.
**18,545 focused tests pass**, 115 deselected, two existing warnings
(`/tmp/primer-land-water-tests.log`). Visual inspection caught labels crossing
the terrain boundary; spacing was corrected. The subsequent semantic check passes
138 cross-subject models, 383 controls and 42,839 deterministic builds
(`/tmp/primer-land-water-semantic.log`). All nine browser states pass keyboard,
reset, desktop and mobile checks (`/tmp/primer-land-water-reviewed-qa/`); the
corrected basin view was visually reviewed. All 432 illustration bindings and
864 WebPs validate. Earth coverage is now 6/27 lessons (seven model entries).
Current isolated QA server: PID 27851, session 91111, port 8768, same temporary
database. No deployment; 215 lessons and the final quality audit remain.

The early Earth rollout adds water-store conservation and rock-process routes.
All 315 amount/infiltration/stage settings conserve 20 arbitrary water units;
all 25 rock-material/process pairs match the independent route table, including
explicitly unmodeled pairs. Water wording distinguishes invisible vapour from
liquid droplets; ice and snow are excluded from this chosen route. USGS sources
are linked. **18,274 focused tests pass**, 115 deselected, two existing warnings
(`/tmp/primer-earth-cycles-tests.log`). After wording and magma-shape improvements,
the full semantic renderer checker passes again (137 cross-subject models, 380
controls and 42,807 deterministic builds; `/tmp/primer-earth-cycles-final-semantic.log`).
Nine water and fourteen rock browser states pass with keyboard/reset and
desktop/mobile checks in `/tmp/primer-earth-cycles-reviewed-qa/`. Fractional
infiltration, sediment consolidation, solid-state metamorphism, unmodeled routes
and cooling molten material were visually reviewed. Magma uses a flowing form
distinct from the solid-rock outline. Illustration and whitespace checks pass.
Earth is 5/27 lessons with models (six entries). Current isolated QA server:
PID 26768, session 77799, port 8768, same temporary database. No deployment.

Latest full regression after the computing rollout: **18,589 passed, 2 skipped,
2 warnings in 104.14s** (`/tmp/primer-full-computing-rollout.log`). No frontend
changed during the run. The complete-goal release gate still lacks models in
218 lessons, plus the final curriculum-wide quality audit; no deployment occurred.

Computer science now has model presence in **34/34 lessons**, including the final
six security/systems/postgraduate lessons. Independent semantic checks cover
4,096 reused-pad cases, 2,400 memory access settings, 286 attention settings,
1,024 replica-set pairs, 90 typed reductions and 84 bounded-verification settings.
Cryptography framing was checked against Stanford CS144 notes; C11 lifetime and
one-past behavior against N1570 sections 6.2.4 and 6.5.6; attention against the
original paper section 3.2. These references are linked in the activities.
The examples explicitly exclude production cryptographic security, unsafe C
execution, complete transformer training, complete consensus and unbounded proof.
**17,738 focused tests pass**, 115 deselected, two existing warnings
(`/tmp/primer-computing-completion-tests.log`). Browser states pass for security
(8), systems (11), attention (8), quorum overlap (7), typed reduction (11) and
bounded verification (9), with keyboard/reset and desktop/mobile checks in
`/tmp/primer-computing-completion-qa/`. Each model’s mobile boundary/failure view
was visually reviewed. All illustration and whitespace checks pass. Current
isolated QA server: PID 25830, session 90090, port 8768, same temporary database.
No deployment: all other subjects and the final cross-curriculum quality audit
remain in scope. Full computing coverage is not the full-goal completion claim.

Theory of Computation now exposes all six transitions of the suffix-01 DFA and
checks 36 input/step settings against independent prefix/suffix predicates,
including empty input and a temporarily accepting prefix of a rejected word.
Advanced Algorithms runs Dijkstra on a directed positive-cost graph: all 3,645
cost/step settings check finalization, path cost and independent shortest-path
formulas. Machine Learning checks 540 learning-rate/update/shift settings against
the exact gradient-descent solution and proves held-out shifts cannot change the
learned weight. Tiny positive MSEs retain scientific notation rather than being
displayed as zero. **16,178 focused tests pass**, 115 deselected, two existing
warnings (`/tmp/primer-advanced-computing-tests.log`). Twelve DFA, eleven graph
and nine learning browser states pass with keyboard/reset and desktop/mobile
checks in `/tmp/primer-advanced-computing-qa/`; temporary prefix acceptance,
tentative nonoptimal routes, divergent training and shifted held-out loss were
visually reviewed on mobile. Computer science is 28/34. Current isolated QA
server: PID 24973, session 20177, port 8768, same temporary database. No deployment.

Earlier full regression, after the live web preview and preceding computing
cohort: **16,276 passed, 2 skipped, 2 warnings in 100.39s**
(`/tmp/primer-rollout-live-web-full.log`). No frontend changed during the run.
This supersedes the earlier full-suite counts below; model coverage remains
205/432, so the deployment gate is not satisfied.

Building for the Web now has a real HTML button, scoped background styles and a
switchable local modulo-ten counter handler. Sixty builder settings plus actual
click, handler-off and wraparound renderer tests pass. The persistent button
retains keyboard focus during refresh; mouse, Space and mobile tap are verified.
How the Internet Works now separates fictional DNS lookup/cache, TLS and HTTPS
request/response stages in 20 checked settings; cached DNS never skips the page
request. **15,425 focused tests pass**, 115 deselected, two existing warnings
(`/tmp/primer-web-layers-tests.log`). Nine web-layer and eight network browser
states pass in `/tmp/primer-web-layers-final-qa/`, including keyboard/reset and
desktop/mobile checks; the live counter and completed cached-address mobile
views were visually reviewed. The harness now enables touch support to test real
taps rather than treating viewport resizing as touch evidence. All illustration
and whitespace checks pass. Computer science is 25/34; all stages 0–3 have models.
Current isolated QA server: PID 23571, session 6665, port 8768, same temporary DB.
No deployment: the remaining nine computing lessons and other subjects stay in scope.

Version control now includes a line-aligned three-way merge with 96 checked
settings for independent edits, equal edits, conflicts and explicit resolutions.
Its 12 browser states pass in `/tmp/primer-merge-model-qa/`; unresolved and
right-resolved mobile views were visually reviewed. Operating Systems adds eight
scheduling cases checked against independently specified timelines, response,
completion and waiting times. Database Systems adds 36 atomicity cases including
interrupted writes, rollback and zero-quantity transfers. Both database models
also pass independent SQLite execution (`tests/test_database_model_sqlite.py`,
two tests, 0.14s), including actual BEGIN/COMMIT/ROLLBACK behavior for all 36
transaction settings. **14,933 focused tests pass**, 115 deselected, two existing
warnings (`/tmp/primer-scheduling-atomicity-tests.log`). Six scheduling and nine
atomicity browser states, keyboard/reset and desktop/mobile pass in
`/tmp/primer-scheduling-atomicity-qa/`; round-robin quantum one and interrupted
maximum transfers with/without rollback were visually reviewed. Illustration
and whitespace checks pass. Computer science is 23/34. Current isolated QA
server: PID 22817, session 17787, port 8768, same temporary database. No deployment.

Full regression after the seven new computing models: **15,060 passed, 2 skipped,
2 warnings in 93.54s** (`/tmp/primer-rollout-seven-models-full.log`). This is the
latest full-suite evidence, including the explicit code-indentation regression,
independent SQLite checks and coverage-gate tests. No frontend changed during
the run. All 432 illustration bindings, 864 WebPs and whitespace checks pass.
The model presence gate is still incomplete at 200/432, so deployment is pending.

Object-Oriented Programming now uses actual local class instances to distinguish
stored fields, inherited construction, overridden methods and independent object
state; all 72 settings pass, including changes to A leaving B unaffected. How
Computers Work extends the half-adder illustration with a full-adder gate trace;
all eight input combinations match independent decimal sum and carry rules.
**14,210 focused tests pass**, 115 deselected, two existing warnings
(`/tmp/primer-object-adder-tests.log`). Eight object and nine adder browser states,
keyboard/reset and desktop/mobile checks pass in `/tmp/primer-object-adder-qa/`;
zero stored points with a bonus return and all-one adder input mobile views were
visually reviewed. Computer science is 20/34. Current isolated QA server:
PID 21526, session 66932, port 8768, same temporary database. No deployment.

Fast and Slow Programs compares actual linear and binary search traces for all
272 size/target settings, including both absent boundaries and the first-item
case where linear search wins. Algorithms reveals stable merge-sort groups for
20 input/stage settings, with independent expected ordering and comparison counts.
**13,738 focused tests pass**, 115 deselected, two existing warnings
(`/tmp/primer-search-sort-tests.log`). Seven search and nine merge-sort browser
states plus keyboard/reset and desktop/mobile checks pass in
`/tmp/primer-search-sort-qa/`; the six-probe absent-target trace and stable duplicate
ordering mobile views were visually reviewed. Computer science is 18/34.
Current isolated QA server: PID 20856, session 27577, port 8768, same temporary DB.
No deployment; these additions do not satisfy the full-curriculum release gate.

Block Coding and Programming Basics now have linked loop/branch models: 75
repeat/star/jump settings and 40 threshold/iteration settings pass independent
expected-result checks, including zero repeats, passing over an earlier star,
strict comparison equality, pending iterations and zero totals. **13,274 focused
tests pass**, 115 deselected, two existing warnings
(`/tmp/primer-control-flow-reviewed-tests.log`). Browser review caught collapsed
Python indentation; explicit x-coordinates now preserve nesting, with a renderer
regression assertion. Fresh browser evidence passes nine block and seven program
states plus keyboard/reset and desktop/mobile checks in
`/tmp/primer-control-flow-reviewed-qa/`; maximum-jump and equality-boundary mobile
views were visually reviewed. Computer science is 16/34. Current isolated server
is PID 20213, session 20753, port 8768, using the same temporary database.
No production deployment; the all-lesson release gate remains incomplete.

Parts of a Computer now follows input, working memory, processing/writeback and
output through four explicitly simplified snapshots. All 80 settings check
computed values and null-versus-zero availability. **12,818 focused tests pass**,
115 deselected, two existing warnings (`/tmp/primer-parts-tests.log`). Nine
browser states plus keyboard/reset and desktop/mobile checks pass in
`/tmp/primer-parts-qa/`; the initial and final zero-input mobile views were
visually reviewed. Illustration and whitespace checks pass. Computer science
is 14/34. No deployment: the all-lesson release gate remains incomplete.

Independent database verification now executes real SQLite SELECT queries for
all 66 control settings and compares ordered results with the shipped JavaScript
model. It also checks the source against a separately specified fixture and
confirms the database remains unchanged. This test and the seven coverage-gate
tests pass (8 tests total). No frontend changes were made, so the existing visual
evidence remains applicable. Coverage remains 193/432; deployment is incomplete.

Databases now contrasts an unchanged six-row source with filtered, ordered query
results. All 66 filter/order settings preserve the source, select exactly matching
rows and sort ties by an explicit secondary ID; the inclusive score-70 boundary
has an independently specified expected order. **12,593 focused tests pass**,
115 deselected, two existing warnings (`/tmp/primer-query-tests.log`). Nine
browser states, keyboard/reset and desktop/mobile pass in `/tmp/primer-query-qa/`;
full ascending results and an empty result were visually reviewed. Illustration
and whitespace checks pass. Computer science is 13/34. Current isolated QA server:
PID 18488, session 32246, port 8768, same temporary database. No deployment.

Data and Types now contrasts integer addition, string concatenation and mixed-
type errors under an explicitly Python-style subset. All 400 digit/type cases
pass, including leading-zero text and null result on error. The model explains
literal quotes, language-dependent coercion and its deliberately limited types.
**12,370 focused tests pass**, 115 deselected, two existing warnings
(`/tmp/primer-data-types-tests.log`). Ten browser states, keyboard/reset and
desktop/mobile pass in `/tmp/primer-data-types-qa/`; leading-zero concatenation
and mixed-type error mobile views were visually reviewed. Illustration and
whitespace checks pass. Computer science is 12/34. Current isolated QA server:
PID 17863, session 67428, port 8768, same temporary database. No deployment.

Finding Bugs now contrasts expected and actual inclusive sums, with an executable
off-by-one loop, repair toggle and running-total trace. All 14 input/repair
settings pass trace and independent arithmetic checks; the buggy program passes
only n=0, while the repair passes all seven bounded tests. Instructions explicitly
distinguish inclusive sums from the existing zero-based indexing illustration.
**12,149 focused tests pass**, 115 deselected, two existing warnings
(`/tmp/primer-boundary-debug-tests.log`). Six browser states, keyboard/reset and
desktop/mobile pass in `/tmp/primer-boundary-debug-qa/`; the misleading zero-input
pass and repaired six-iteration mobile trace were visually reviewed. Illustration
and whitespace checks pass. Computer science is 11/34. Current isolated QA server:
PID 17317, session 92105, port 8768, same temporary database. No deployment.

Functions now shows one reusable definition and two independent argument/local-
binding/return lanes. All 300 operation/input combinations pass arithmetic and
swapped-call checks. It distinguishes parameter from argument, return from print,
and pure examples from functions with side effects. **11,930 focused tests pass**,
115 deselected, two existing warnings (`/tmp/primer-function-calls-tests.log`).
Nine browser states, keyboard/reset and desktop/mobile pass in
`/tmp/primer-function-calls-qa/`; negative-input squaring and identical-input
zero-return mobile views were visually reviewed. Illustration and whitespace
checks pass. Computer science is 10/34. Current isolated QA server: PID 16825,
session 67371, port 8768, same temporary database. No deployment was made.

The coverage gate now rejects empty input, empty domains, duplicate domain IDs
and duplicate lesson IDs instead of allowing vacuous completion or inflated
counts. Seven new tests pass, including multiple models on one lesson counting
as only one covered lesson. The actual `--require-complete` command was rerun
and correctly exits 1 at 189/432 covered, with 243 missing lessons. This is an
expected release-gate failure, not a blocked rollout. No frontend changes or
deployment were made during this validation hardening.

Introductory computing now includes explicit-key sorting and repeated-unit
patterns. All 21 sorting settings preserve the six identified objects, sort the
included prefix and leave the waiting suffix untouched; all 16 pattern settings
match the chosen unit and expected length. Shape and letter cues accompany
colour, and the pattern model distinguishes a chosen rule from a uniquely
inferable continuation. **11,713 focused tests pass**, 115 deselected, two
existing warnings (`/tmp/primer-early-computing-tests.log`). Seven sorting and
eight pattern browser states, keyboard/reset and desktop/mobile pass in
`/tmp/primer-early-computing-qa/`; the full colour sort and twelve-symbol ABB/ABC
mobile patterns were visually reviewed. Illustration and whitespace checks pass.
Computer science is 9/34. Current isolated QA server: PID 15946, session 13146,
port 8768, same temporary database. No production deployment was made.

Chemical Bonding now compares mobile charge carriers in solid/liquid salt,
copper and molecular iodine under a field. All 12 material/state/field settings
pass the carrier and drift rules. The model separates ionic motion from metallic
electron drift, explains molecular-covalent counterexamples and omitted effects,
and avoids measured-conductivity or experimental claims. **11,285 focused tests
pass**, 115 deselected, two existing warnings (`/tmp/primer-bonding-tests.log`).
Ten browser states, keyboard/reset and desktop/mobile pass in
`/tmp/primer-bonding-qa/`; molten salt, solid copper and liquid iodine mobile
views were visually reviewed. Illustration and whitespace checks pass.
Chemistry now has models in **29/29 lessons**. This is a subject coverage
milestone, not full rollout completion: 245 lessons elsewhere still lack models.
Current isolated QA server: PID 15389, session 23446, port 8768, same temporary
database. No production deployment was made.

Fresh full-suite regression after the coordination model and chemistry wording
changes: **11,916 passed, 2 skipped, 2 warnings in 77.57 seconds**, recorded in
`/tmp/primer-rollout-full-regression-current.log`. The process exited successfully;
this includes the reader picture-handler tests, not just model/gallery tests.
The warnings remain the existing Google-auth Python 3.9 end-of-life notices.
Coverage was rechecked at 186/432 with 246 gaps, so these passing tests do not
establish rollout completion or authorize treating the deployment as finished.
No application or model assets changed during this regression run.

Inorganic Chemistry now separates ligand count, donor count and complex charge
in a six-coordinate ledger with neutral bidentate en and monodentate NH₃/Cl⁻.
All 24 combinations preserve six donor sites and the correct formal charge.
The activity explicitly labels the drawing as connectivity, not geometry, and
does not claim all hypothetical complexes are stable or synthesizable.
Focused tests: **11,074 passed**, 115 deselected, two existing dependency warnings
(`/tmp/primer-coordination-tests.log`). Eight browser states, keyboard/reset and
desktop/mobile pass in `/tmp/primer-coordination-qa/`; the three-chelate and
all-chloride mobile diagrams were visually reviewed. Illustration and whitespace
checks pass. Chemistry is 28/29, with bonding remaining. Current isolated QA
server: PID 14612, session 53480, port 8768, same temporary database.
No production deployment was made.

Shared chemistry toggle labels now use learner-facing yes/no rather than
programming-style true/false while preserving boolean state and aria-pressed.
Single-candidate and hydrogen/outer-electron wording were corrected; a regression
asserts hydrogen's singular spoken description. **10,865 focused tests pass**
with 115 deselected and two existing warnings (`/tmp/primer-chemistry-labels-tests.log`).
Material selection, alkane branching and the periodic table pass desktop/mobile,
keyboard and reset checks (8/6/4 states) in `/tmp/primer-chemistry-labels-qa/`;
the all-requirements mobile material view was visually reviewed. Whitespace
checks pass. Coverage remains 185/432; bonding and inorganic chemistry remain
the two chemistry gaps. The broader rollout and deployment are still incomplete.

Carbon Chemistry now compares unbranched and branched alkane skeletons for
4–8 carbons with explicit CH₃/CH₂/CH groups. All ten combinations pass carbon
connectivity, n−1 edge count, valence-four and CₙH₂ₙ₊₂ checks. It distinguishes
constitutional isomerism from rotating a drawing and states that two examples
are not the complete isomer set or a three-dimensional conformation.
Focused tests: **10,865 passed**, 115 deselected, two existing dependency warnings
(`/tmp/primer-alkane-tests.log`). Six browser states, keyboard/reset and
desktop/mobile pass in `/tmp/primer-alkane-qa/`; four- and eight-carbon branched
mobile structures were visually reviewed. Illustration and whitespace checks
pass. Chemistry is 27/29. Current isolated QA server: PID 13684, session 69917,
port 8768, same temporary database. No production deployment was made.

Two reaction activities now track open/closed-system mass and zinc–copper redox.
All 22 mass-ledger settings preserve retained plus escaped mass; all five redox
extents preserve zinc/copper atom inventories and ionic charge, with equal
electron loss and gain. Gas production is explicitly distinguished from proof
of reaction, and the model warns against physically sealing gas-producing
reactions. Redox electron counts are cumulative bookkeeping, not free electrons
in solution; omitted counterions maintain neutrality in the real solution.
Focused tests: **10,658 passed**, 115 deselected, two existing dependency warnings
(`/tmp/primer-reaction-accounting-tests.log`). Six mass-ledger and four redox
browser states, keyboard/reset and desktop/mobile pass in
`/tmp/primer-reaction-accounting-final-qa/`. Open/closed endpoints and completed
redox mobile views were visually reviewed; electron text was matched to its
legend colour before the final run. Illustration and whitespace checks pass.
Chemistry is 26/29. Current isolated QA server: PID 13050, session 15520,
port 8768, same temporary database. No production deployment was made.

Reading the Periodic Table now links the first 18 neutral atoms to period,
group and occupied-shell counts. Selected and same-group atoms are highlighted;
helium's full two-electron shell and hydrogen's unusual chemistry are explicitly
distinguished from simplified family rules. The model warns against treating
shell counts as orbits or extending 2,8,8 to all later elements. All 18 atom
inventories, independently specified groups and unique grid positions pass.
Focused tests: **10,250 passed**, 115 deselected, two existing dependency warnings
(`/tmp/primer-periodic-tests.log`). Four browser states, keyboard/reset and
desktop/mobile pass in `/tmp/primer-periodic-reviewed-qa/`; sodium and helium
mobile layouts were visually reviewed, with singular wording corrected before
the final run. Illustration and whitespace checks pass. Chemistry is 24/29.
Current isolated QA server: PID 12305, session 29885, port 8768, same temporary
database. No production deployment was made.

Acids and Bases now compares sample/reference pH with a logarithmic number line,
hydronium activity ratio and complementary hydroxide activity. All 225 pH pairs
pass direct ratio, reversal and water-ion-product checks. The model states its
25 °C ideal-activity assumptions, distinguishes pH from hazard/total acid content,
and does not present 0–14 as an absolute physical limit. A diffusion display bug
was also fixed: small positive lengths now use scientific notation instead of
rounding to zero; a dedicated regression checks this case.
Focused tests: **10,049 passed**, 115 deselected, two existing dependency warnings
(`/tmp/primer-acidity-tests.log`). Browser checks pass for six acidity states and
eight diffusion states, keyboard/reset and desktop/mobile, in
`/tmp/primer-acidity-precision-qa/`. Visual review covered opposite-end and equal
pH markers and the tiny nonzero diffusion length. Illustration and whitespace
checks pass. Chemistry is 23/29. Current isolated QA server: PID 11760, session
91686, port 8768, same temporary database. Deployment remains outstanding.

Three materials activities now distinguish objects from their constituent
materials (nine shape/material combinations), compare design requirements with
sample properties (all eight requirement combinations), and explore thermally
activated diffusion (2,835 temperature/barrier/time settings). The advanced
model uses illustrative parameters and NIMS's Arrhenius and 2√(Dt) conventions;
it explicitly explains the logarithmic graph and avoids claiming a sharp front
or measured semiconductor behaviour. The selection summary names current needs
even when changing a requirement does not change the candidate list.
Focused tests: **9,850 passed**, 115 deselected, two existing dependency warnings
(`/tmp/primer-materials-tests.log`). All three models pass eight browser states
each, keyboard/reset and desktop/mobile checks in
`/tmp/primer-materials-reviewed-qa/`. Visual review covered the property table,
high/low diffusion extremes, wooden button and steel cup; a protruding cup
highlight was corrected and the cohort rerun. Illustration and whitespace checks
pass. Chemistry is 22/29; no deployment was made. Current isolated QA server:
PID 11078, session 84797, port 8768, same temporary learner database.

Changing Matter now compares melting with water decomposition using explicit
atom-labelled molecules before and after. All six process/snapshot combinations
conserve eight hydrogen and four oxygen atoms; melting preserves molecular
identity, while completed decomposition events follow 2 H₂O → 2 H₂ + O₂.
The lesson distinguishes energy-dependent decomposition from ordinary melting,
and explains schematic positions and the lack of a time/kinetic model.
Focused regression: **9,265 passed**, 115 deselected, two existing dependency
warnings (`/tmp/primer-changes-tests.log`). Six browser states, keyboard/reset,
desktop/mobile checks pass in `/tmp/primer-physical-chemical-qa/`; reaction and
liquid-water mobile captures were visually reviewed. Chemistry is now 19/29.
The current isolated QA server is PID 10393, session 53525, on port 8768 with
the same temporary learner database. No production deployment was made.

Electrochemistry now includes an ideal zinc concentration cell: changing ion
activities changes signed voltage, swapping concentrations reverses polarity and
electron flow, and equal activities give zero voltage. The salt bridge is
distinguished from the external electron path. Assumptions explicitly separate
open-circuit equilibrium predictions from loaded voltage and current. All 208
concentration/temperature settings pass direct Nernst and symmetry checks;
focused regression passes **9,074 tests**, with 115 deselected and two existing
dependency warnings (`/tmp/primer-concentration-tests.log`). Eight browser states,
keyboard/reset and desktop/mobile checks pass in
`/tmp/primer-concentration-cell-qa/`; default, reversed and equal-concentration
mobile captures were visually reviewed. All 432 illustration bindings, 864 WebPs
and whitespace checks pass. Chemistry coverage is 18/29. The isolated QA server
is PID 9757, session 14844, using `/tmp/primer-spatial-qa.lNZaZE/primer.db` on
port 8768. No production deployment was made.

Fresh full regression checkpoint: **9,727 passed, 2 skipped, 2 dependency
warnings in 72 seconds**, recorded in `/tmp/primer-full-rollout-regression.log`.
The skips were verified separately: the live Turso check lacks throwaway test
credentials, and the all-curriculum cloze audit lacks a real offline archive or
sufficient article cache. The smaller real-corpus cloze check passes. The warnings
are the existing Google-auth Python 3.9 end-of-life notices. This is current
regression evidence through enzyme inhibition, before the concentration-cell
addition; it is not proof of live hosted integration or full visual quality.

The browser harness now chooses an option different from the current selection,
types its complete label and verifies the exact selected value. It no longer
assumes the second option differs from the default or relies on one initial
letter. Four desktop/mobile activities pass the stronger checks in
`/tmp/primer-keyboard-selection-qa/`: mixing (Sand/Salt), enzyme inhibition,
linguistics and experimental discrimination. No application defaults were changed
to satisfy the test. Whitespace checks pass. Coverage remains 175/432, with 257
model gaps and final visual/deployment verification outstanding.

Advanced biochemistry now compares competitive and pure noncompetitive inhibition
against one uninhibited reference. It distinguishes apparent Km from limiting rate,
and labels the assumptions of the pure noncompetitive special case rather than
equating it with every allosteric mechanism. All 714 settings pass direct rate,
monotonicity, half-maximal-point and zero-substrate/inhibitor checks. Focused tests
pass 8,885 cases (115 deselected; two existing dependency warnings). Eight browser
states pass desktop/mobile layout, keyboard/reset and source hashes in
`/tmp/primer-inhibition-qa/`; the strongly noncompetitive mobile plot was visually
inspected. Asset and whitespace checks pass. Chemistry is 17/29. Preview: port 8768,
PID 8534, exec session 78876. No deployment: 257 model gaps and wider visual review
remain before release.

Chemistry frontier now contrasts atom economy, isolated yield and waste/product
ratio using a conserved hypothetical batch ledger. Recovered solvent is an explicit
output, not silently discarded from the balance; gross input/product is distinguished
from E+1 when recovered material leaves the batch. Zero product yields undefined
ratios rather than infinities. All 7,986 settings pass mass and metric identities.
Focused tests pass 8,698 cases (115 deselected; two existing dependency warnings).
The ten-state desktop/mobile route passes controls, keyboard/reset and source hashes
in `/tmp/primer-green-metrics-qa/`; the zero-yield recovered-solvent view was visually
inspected. Asset and whitespace checks pass. Chemistry is 16/29. Preview: port 8768,
PID 7946, exec session 93539. No deployment: 258 model gaps and wider visual review
still gate release.

Chemical inference additions: analytical chemistry now contrasts raw absorbance,
matching-blank correction and inferred concentration under a declared Beer–Lambert
toy model. Computational chemistry varies the width and centre of a normalised
Gaussian trial state for a harmonic oscillator, distinguishing a variational bound
for the specified Hamiltonian from validation of a real molecule. Checks cover all
726 calibration settings, all 493 variational settings and nine independent
numerical integrations of normalisation, kinetic and potential energies.
Focused tests pass 8,513 cases (115 deselected; two existing dependency warnings).
Both routes pass desktop/mobile, keyboard/pointer/reset and source-hash checks in
`/tmp/primer-chemical-inference-qa/` (ten and six states). The blank-only false
concentration and exact variational minimum were visually inspected on mobile.
Asset and whitespace checks pass. Chemistry is 15/29. Preview: port 8768, PID 7280,
exec session 96058. No deployment: 259 model gaps and wider visual review remain.

Mixtures and solutions now includes an ideal-filtration ledger with a deliberately
hypothetical solubility limit. It conserves dissolved solute, excess solid and sand
separately, distinguishes solvent volume from solution volume, and leaves dissolved
material in the filtrate. All 2,310 settings pass conservation and separation
checks. Focused tests pass 8,149 cases (115 deselected; two existing dependency
warnings). The ten-state desktop/mobile route passes keyboard/pointer/reset and
current-source checks in `/tmp/primer-filtration-qa/`; the saturated filtered
mobile state was visually inspected. Asset and whitespace checks pass. Chemistry
is 13/29. Preview: port 8768, PID 6717, exec session 28220. No deployment: 261 model
gaps and the remaining visual audit still gate release.

Shared mobile navigation fix: the previously always-expanded sticky header now
defaults to a compact Menu disclosure, leaving subject/stage and lesson title
visible while a model scrolls. Reader routes retain their existing exact lesson
navigator instead of duplicating the context. Menu, settings and statistics remain
available on demand; desktop navigation is unchanged. Escape closes the menu and
returns focus; route changes collapse it; theme-driven rebuilds preserve its open
state and restore focus to the visible theme control. Stale route completions do
not overwrite the current route's context/title/focus.

`tools/check_mobile_navigation.cjs` verifies the real shell's disclosure references,
keyboard/pointer operation, focus, route changes, breakpoint resizing, desktop
visibility and Genetics reader navigation. Final evidence in
`/tmp/primer-mobile-navigation-final/` includes light/dark inspection across runs;
the compact model and Genetics reader were visually reviewed. The tested collapsed
model header is below 155px (previous screenshots were about 245px). Thirty focused
reader/navigation/route/focus tests pass. Chemistry atomic inventory, biology neural
and mathematics quadratic model routes also pass a fresh desktop/mobile sweep in
`/tmp/primer-collapsed-nav-final-models/`. Coverage remains 170/432: this fixes a
shared reading defect, not another model gap. The goal remains active, not deployed.

Atomic structure now has a proton/neutron/electron inventory that separates
element identity, mass number and charge without suggesting classical electron
orbits or stability for arbitrary combinations. All 1,690 settings pass identity,
nucleon-count and charge checks. Focused tests pass 7,970 cases (115 deselected;
two existing dependency warnings). The route passes eight browser states,
keyboard/reset and desktop/mobile bounds in `/tmp/primer-atomic-inventory-qa/`;
the fully populated mobile inventory was visually inspected. Asset and whitespace
checks pass. Chemistry is 12/29. Preview: port 8768, PID 5247, exec session 27130.
No deployment: 262 remaining model gaps and wider visual review gate release.

Chemistry conditions cohort: gas laws (`chem.3.gases`) separates isothermal
pressure–volume comparisons from heating or changing amount; reaction energy
(`chem.3.energy`) keeps endpoint energies invariant under a lower-barrier pathway;
physical chemistry (`chem.4.physical`) distinguishes equilibrium ratios from equal
amounts and composition adjustment from elapsed time. Pure-component quotient
limits are described without emitting numerical infinities.

Checks cover all 5,330 gas settings for PV/nT and inverse-volume scaling, all 182
energy settings for forward/reverse barriers and unchanged endpoint differences,
and all 605 equilibrium settings for conservation, equilibrium ratios and net
direction. Focused tests pass 7,793 cases, 115 deselected, with two existing
dependency warnings. All three routes pass eight browser states each, keyboard,
reset, desktop/mobile layout and current-source checks in
`/tmp/primer-chemistry-conditions-qa/`. High-pressure, endothermic catalysed and
pure-B boundary screenshots were visually inspected. Asset and whitespace checks
pass. Chemistry is 11/29; overall coverage is 169/432. Preview: port 8768,
PID 4661, exec session 37289. No deployment: 263 model gaps and wider visual review
remain before the release gate can pass.

The stoichiometry activity now provides separately counted hydrogen and oxygen
ledgers for variable coefficients of H₂, O₂ and H₂O. All 216 coefficient triples
are checked, including proportional balanced equations and signed atom deficits.
It never changes molecular formulas or claims that balance proves kinetics/yield.
Focused tests pass 7,274 cases (115 deselected; two existing dependency warnings).
The desktop/mobile route passes nine states, keyboard/reset and current-source
checks in `/tmp/primer-stoichiometry-qa/`; the dense balanced mobile ledger was
visually inspected. Asset and whitespace checks pass. Chemistry is 8/29.
Preview: port 8768, PID 3960, exec session 61675. Not deployed: 266 model gaps and
the remaining visual audit still gate release.

Introductory chemistry now includes mixing versus dissolution (`chem.0.mixing`),
water phase identity and coexistence (`chem.0.water-states`), and container shape
versus occupied volume (`chem.1.matter`). The comparison distinguishes dissolved
ions, suspended grains and transient oil droplets; fixed-depth cross-section area
is explicitly a stand-in for volume. Water symbols retain one oxygen and two
hydrogens across all five heating snapshots. A visual correction spread vapour
through its entire region instead of leaving it near the top.

All six mixture/rest combinations, five phase snapshots with symbol conservation,
and 51 state/container settings pass independent semantic/area checks. The shared
checker passes 86 cross-subject models, 240 meaningful controls and 41,272 finite
generic builds. Its geometry inventory now includes SVG ellipses, avoiding a
false failure on correctly rendered sand grains. Focused tests pass 7,105 cases,
115 deselected, with two existing dependency warnings. The final three-route
browser run passes current-source hashes, desktop/mobile bounds, keyboard/pointer
controls and exact reset in `/tmp/primer-intro-chemistry-final/`. Dissolved salt,
boiling phase coexistence and wide-container liquid views were visually reviewed;
the corrected molecular/vapour render was also reviewed after the final run.

Chemistry coverage is 7/29. Asset and whitespace checks pass (432 illustrations,
864 WebPs, 168 model entries). Preview: port 8768, PID 3127, exec session 25543.
No deployment has occurred: 267 lesson-model gaps and wider visual review remain.

Biology model coverage is now **37/37**. Seven recent additions cover leaky
integrate-and-fire dynamics, cooperative binding, marginal-value foraging,
handwashing/material transfer, selection of existing resistance, competitive
antibody-fragment occupancy and discriminating toy experiments. They explicitly
separate schematic material from germ counts, abundance from fraction, affinity
from protection, and hypothesis discrimination from proof of a unique mechanism.

Independent checks include 279 neural settings and three fine-step Euler event
comparisons, 1,271 Hill-curve settings, 180 foraging settings with independent
residence grids, all 12 washing/contact combinations, 1,414 selection settings
against repeated multiplication, 4,410 binding settings with partition/mass-action
checks, and 924 experimental-design settings. The shared checker passes 83
cross-subject models, 235 meaningful controls and 41,218 finite generic builds
(the specific scientific checks are additional). Focused tests pass 6,610 cases,
115 deselected, with two existing Python dependency warnings.

All seven recent routes pass desktop/mobile bounds, current-source hashes,
keyboard/pointer controls and exact resets in `/tmp/primer-final-biology-verified/`.
The first browser attempt assumed the second select option differed from the
default; the experiment-design selector now lists its default first, and the
fresh seven-route run passes. This was a verification/default-order mismatch,
not evidence that the native selector could not be operated. Mobile handwashing,
recontamination, antibody occupancy, declining total abundance under selection,
and experiment-design default/extreme plots were visually inspected. The dense
49-spike plot was also inspected in the preceding three-model run.

Asset and whitespace checks pass: 432 illustrations, 864 WebPs, 165 model entries.
The isolated preview runs at port 8768 (PID 2210, exec session 47313 at this
checkpoint). No deployment has occurred. The 270 remaining model gaps and wider
visual review still gate release; the historical counts below are not fresh
full-suite certificates.

Molecular/computational cohort: `bio.4.genomics` distinguishes quality-filtered
read support from a genotype call, including undefined fractions at zero usable
coverage. `bio.5.comp-bio` exposes a global-alignment cost matrix, ties and a
deterministic optimal traceback. `bio.5.systems-bio` compares negative
autoregulation with an analytic no-feedback reference under matched input/removal
parameters, without claiming matched-output response times or experimental fit.

Checks cover 144 read/filter settings, 90 alignment settings against independently
enumerated paths and recomputed alignment costs, 54 feedback settings, and three
fine-step Euler comparisons. The checker passes 76 cross-subject models and 214
meaningful controls. Focused tests passed 5,525 cases (115 deselected; two existing
dependency warnings). Browser verification caught an unhelpful pure-insertion
default whose optimum barely responds to mismatch cost; the opening alignment
now contains a substitution. The final model checker and all three desktop/mobile
routes pass in `/tmp/primer-molecular-computation-final/`, including current-source
hashes, controls, keyboard, pointer, reset and layout checks. Mobile alignment,
zero usable coverage and feedback renders were visually inspected.

Biology is now 30/37 and overall model coverage 155/432. Asset and whitespace
checks pass: 432 illustrations, 864 WebPs and 158 model entries. The isolated
preview runs on port 8768 (PID 537, exec session 10214 at this checkpoint). No
deployment has occurred; 277 model gaps and wider visual review remain.

Five-model biology cohort: selection (`bio.3.evolution`), fixed-allele-frequency
genotype redistribution (`bio.4.evo-bio`), logistic growth (`bio.3.ecology`), stomatal
gas/water exchange (`bio.3.botany`), and Michaelis–Menten saturation
(`bio.4.biochem`). Models distinguish frequencies from individuals, genotype
redistribution from allele change, continuous populations from discrete counts,
normalised fluxes from measured rates, and initial-rate kinetics from equilibrium.
All assumptions and reference sources are available beside each model.

Independent checks cover 3,939 selection settings against propagated reproductive
weights, 10,201 genotype settings with allele-copy conservation, 36 logistic
trajectories against RK4 integration, 10,201 pore/humidity settings, and 450
enzyme settings including the exact half-maximal point. The shared checker passes
73 cross-subject models, 204 meaningful controls and 40,874 finite generic builds;
the specific scientific checks above are additional to that generic-build count.
Focused schema/model/gallery/hosted tests pass 5,090 cases (115 deselected; two
existing dependency warnings). All five routes pass current-source hashes,
desktop/mobile bounds, keyboard/reset and relevant pointer checks in
`/tmp/primer-five-biology-models-qa/`. Mobile defaults and selected extreme renders
were visually inspected: genotype redistribution, selection, closed stomata,
enzyme saturation and above-capacity decline. A native-browser selection also
confirmed the unchanged 50:50 result under equal reproductive contributions.

Biology is now 27/37; overall coverage is 152/432. All 432 illustration bindings,
864 WebPs and 155 model entries pass asset checks; whitespace checks pass.
Preview at this checkpoint: port 8768, PID 99575, exec session 99673. Nothing has
been deployed; 280 lesson-model gaps and the broader visual-quality audit remain.
The earlier full browser/regression counts below are historical checkpoints,
not fresh full-suite certificates for these additions.

Body/reproduction cohort: `bio.1.human-body` follows a portion of blood through
right heart, lungs, left heart and tissues; `bio.2.digestion` distinguishes
glucose, carbon-dioxide, urea and unabsorbed-residue routes; `bio.2.reproduction`
separates gamete fusion from subsequent cell multiplication. Independent checks
cover 16 circulation settings, 16 material-route settings and 12 chromosome/set
division settings. Focused tests pass 4,410 cases (115 deselected; two existing
dependency warnings). The numerical/semantic checker passes 68 cross-subject
models, 191 meaningful controls and 40,723 finite builds. Biology is now 22/37.

The three new desktop/mobile routes pass pointer/keyboard/reset, layout and
current-source checks. Visual review moved reproduction arrows clear of the
gamete labels. An eight-cell screenshot then revealed inconsistent clipping in
the element-capture method despite passing DOM bounds. The harness now waits two
compositor frames after scrolling and saves the entire viewport without a second
implicit element scroll, with fresh bounds checks at capture. Full-viewport
evidence in `/tmp/primer-body-viewport-qa/` shows the dense growth scene intact;
the urea route and desktop circulation were also visually reviewed. Earlier
cropped screenshots are not accepted as evidence of intact full-frame rendering.
The head/brain illustration's stale table-based alt text was corrected in both
the curriculum and generator metadata; quick metadata/asset checks pass without
regenerating unchanged rasters. Preview at this checkpoint: port 8768, PID 97300,
exec session 60883. No deployment has occurred.

The expanded **66-concept** viewport-capture sweep passes in
`/tmp/primer-66-concepts-viewport-recheck/`, including current source hashes,
desktop/mobile bounds, keyboard/pointer controls and exact resets. The first
attempt timed out in a browser evaluation for `math.5.numerical` and was not
accepted; the exact isolated case passed, then the complete fresh sweep passed.
The timeout's cause is not established. The five biology-visual tests pass after
the alt-text correction. `--require-complete` correctly exits 1 with 285 uncovered
lessons; this is not release-ready. None of these checks replaces remaining
curriculum-wide visual review or the final deployment verification.

Animal/habitat cohort: `bio.0.animals` groups four drawn adult animals by legs
or wings, distinguishing functional similarities from close ancestry.
`bio.1.habitats` shows how a wood frog's seasonal journey requires both a pool
and woodland plus a connecting route, with explicit limits on the graph model.
All eight animal feature/count settings and all eight habitat configurations
pass independent checks. Focused tests pass 4,023 cases (115 deselected; two
existing dependency warnings). The checker verifies 65 cross-subject models and
185 meaningful controls. Both new routes pass desktop/mobile browser verification
in `/tmp/primer-animals-habitats-qa/`; their mobile drawings were visually reviewed.
A separate agent-browser click confirmed the count toggle after scrolling the
off-screen control into view; clicks without that scroll were not accepted as
evidence. All five stage-zero biology lessons now have models; biology overall
is 19/37. Asset and whitespace checks pass. The isolated preview is on port 8768
(PID 96597, exec session 9023 at this checkpoint). No deployment has occurred.

Newest additions: `bio.0.body` traces stimulus/receptor, nerve signal and brain
processing across five senses; `bio.0.seasons` compares a temperate deciduous
tree's cycle across all months and hemispheres. The latter uses meteorological
season groups and explicitly excludes universal claims about trees/climates.
Independent tests check 15 sensory states and all 24 month/hemisphere pairs.
Focused tests passed 3,775 cases; after replacing a stale hard-coded checker
summary with registry-derived counts, all 3,745 cross-subject tests passed again.
The two routes pass desktop/mobile browser checks, keyboard interaction, reset
and source hashes in `/tmp/primer-senses-seasons-qa/`. Both mobile defaults were
visually inspected. A separate native-browser selection confirmed that September
switches from southern spring to northern autumn. Biology now has 17/37 models.
Preview at this checkpoint: port 8768, PID 95775, exec session 25024. Asset and
whitespace checks pass; nothing has been deployed. The earlier 4,372-test full
regression predates these two additions and is not a fresh full-run certificate.

The latest cohort adds `bio.0.living`, `bio.2.classification`,
`bio.2.ecosystems`, and `bio.2.microbes`: multiple signs of life, shared ancestry
versus convergent flight, food-web route removal, and fermentation bookkeeping.
Independent checks cover 10 specimen/inspection states, 72 classification
settings, 12 food-web settings, and 98 fermentation settings, including atom
conservation. Focused tests pass 3,507 cases. All four routes pass desktop/mobile
browser checks, native pointer toggles, keyboard operation and exact resets in
`/tmp/primer-life-systems-qa/`; their mobile defaults were visually inspected.
This extends, rather than replaces, the earlier 55-concept browser evidence.

Four existing native biology plates were corrected and their eight responsive
WebPs regenerated: body senses, cooperating organ systems, digestion exit routes,
and seasons. Fixes separate captions from diagrams, keep route arrows outside
node interiors, and contain output labels. All four regenerated 800px plates
were visually inspected; a new actual-ink-bounds regression protects reserved
caption boxes. Asset checks pass 432 illustrations, 864 WebPs and 143 models;
`git diff --check` passes. These checks do not certify all remaining visuals.

Full regression now passes **4,372 tests, 2 skipped**, with two existing Python
3.9/google-auth end-of-life warnings (112.63 seconds). Evidence:
`/tmp/primer-full-regression-sept5-v3.log`. During the previous diagnostic run,
18 maintenance workers were found looping after shutdown because a shared,
already-set event skipped the wait without terminating the outer loop. Each
lifespan now owns its shutdown event, captures its learner store and backup
directory, and joins its worker on exit. Targeted lifecycle/hosted-safety tests
pass 26 cases, including repeated lifespans and exceptional exit. No deployment
has occurred: 292 lessons still lack model coverage and visual review remains.

The restarted isolated preview (port 8768, PID 95288, exec session 45943 at this
checkpoint) passes the expanded **59-concept** desktop/mobile browser sweep,
including pointer/keyboard interactions, exact resets and current-source hashes.
Evidence: `/tmp/primer-59-concepts-final-sept5/`. Additional mobile edge captures
were visually reviewed for same-animal classification, removed mouse-to-owl food
routes and inactive-yeast fermentation. The natural-science source-to-raster
determinism check also passes: 93 lessons, 85 generated plates, 186 responsive
rasters. These results supersede the earlier narrower browser/check snapshots.

The next completed cohort fills all three remaining mathematics bindings:
`math.5.diffgeo`, `math.5.complex-analysis`, and `math.5.logic`. The models explain
spherical angle excess, directed residue sums (including an undefined on-path
pole), and Cantor’s missing-subset construction. Independent spherical-area
integration, complex contour quadrature, and diagonal-membership checks pass.
All 59 mathematics lessons now have model presence; this is not a blanket visual
quality certificate. Their targeted desktop/mobile browser run passed in
`/tmp/primer-math-completion-qa/`; the sphere heading was then moved clear of its
outline and reverified with the biology cohort.

Four connected biology models add seed growth, plant-part functions,
photosynthesis bookkeeping, and food-chain energy transfer. Conditions are
explicitly simplified: bean germination can start without light; the net
photosynthesis equation is not a kinetic simulation; a selected transfer
efficiency is not a universal ecological constant. Tests check all 40 seed
states, eight plant-part/flow settings, 722 photosynthesis supply states, and
40 energy-transfer settings. Detailed native plant shapes share the mathematics
palette and keep roots, leaves, cotyledons, flowers, and water paths distinct.
Focused schema/model/gallery tests pass 3,051 cases. The four new biology routes
plus the adjusted sphere pass keyboard/reset, current-source hashes, and
desktop/mobile layout checks in `/tmp/primer-botany-qa/`. Mobile defaults and
the low-energy food-chain edge case were visually inspected. Asset checks pass
432 illustrations, 864 WebPs, and 139 model entries. Broader regression checks
are recorded below once finished. Nothing has been deployed.

The full 55-concept browser sweep passes in `/tmp/primer-all-concepts-sept5/`
against current JS/CSS hashes. It checks desktop/mobile bounds and overlap,
control responses, keyboard use, and exact resets. The harness now additionally
checks native pointer clicks on toggle buttons at both viewport sizes; the
three new biology activities with toggles and complex-analysis orientation pass
that strengthened check in `/tmp/primer-pointer-qa/`. A fresh standalone pointer
check also confirms that clicking water off changes the seedling to a dry seed.
The 14 spatial-model invariant checks still pass. The deployment coverage gate
correctly failed with 296 uncovered lessons at that earlier checkpoint. The
first full pytest run ended with exit 143 without a summary; the second was
stopped after diagnosing the maintenance-worker leak. The replacement full run
passed as recorded above. The first run found a legacy media-contract assertion that still expected
five now-modelled mathematics lessons to contain only an illustration. The test
now expects the concept model and exact lesson binding, includes this cohort,
and retains lightweight graph/Today checks. External Wikipedia summaries are
stubbed only in this authored-media contract; dedicated article tests remain.
The corrected test passed separately in 3.30 seconds and now passes in the full
suite. The old server/session identifiers are no longer authoritative; validate
the current port 8768 process before restarting the isolated QA preview.

Latest continuation adds `math.5.frontier`: an exact finite primality experiment
for n²+n+41, with a checked-range grid and independent selected-value inspector.
The first counterexample at n=40 distinguishes finite evidence from universal
proof; the model explicitly does not claim to resolve an open problem. An
independent sieve checks all 3,721 control combinations. Production binding and
renderer checks caught and fixed an incorrectly placed binding and a missing
source-list field before verification. Focused schema/model/gallery tests pass
2,330 cases. The final targeted browser check passes keyboard/reset, source
hashes, and desktop/mobile layout; evidence is in `/tmp/primer-frontier-final/`.
All 432 illustration bindings and 864 WebPs pass the asset checker. Mathematics
now has 56/59 lessons with models; differential geometry, complex analysis and
mathematical logic remain. Nothing has been deployed; 303 lessons still lack
models and the cross-curriculum quality review is incomplete.

Latest additions in `concept-lab`: `cs.1.binary`, `math.0.compare`,
`math.0.patterns`, and `math.0.numbers20`. The binary model checks all 16 bit
patterns; the maths models check all 121 pairs of quantities, 21 numbers and 18
rule/length combinations. All five stage-zero maths lessons now have models.
The seven concept scenes passed keyboard/reset and desktop/mobile browser checks
against current-source hashes. Default desktop/mobile screenshots were visually
reviewed, plus the six-step growing pattern on mobile. Focused checks now pass
73 cross-subject tests and two gallery/API tests.
The gallery/API tests passed with 91 model entries and 523 total visual entries.
Integration tests caught missing instructions in the new curriculum entries;
those were fixed, and an explicit production-schema check now covers every
registered concept lesson's actual data, not only synthetic fixtures.

Next-stage additions: `math.1.subtraction` and `math.1.place-value`. Their checkers
cover all 121 stay/remove pairs and all 1,000 digit combinations. Subtraction
retains crossed-out counters so the starting whole remains visible; place value
shows 100-unit squares, ten-unit rods and ones with explicit scale limitations.
The QA server was reloaded and all nine concept routes passed browser checks,
including real keyboard operation, exact reset, current-source hashes, and
desktop/mobile layout. The two new models' default desktop/mobile screenshots
and combined-maximum mobile screenshots were visually inspected (20 counters
and 999). Reports/screenshots are in
`/tmp/primer-spatial-qa.lNZaZE/concepts-place/`. This verifies this cohort, not
the remaining 342 uncovered lessons. Multiplication and division are next.

Multiplication and division are now implemented. Multiplication covers 0–12 in
both factors, with 169 exact product/commutativity checks. Division covers totals
0–36 and 1–6 groups, with 222 quotient/remainder conservation checks. Focused
schema, model and gallery tests pass (147 tests). The browser harness includes
both routes plus maximum arrays and the dense 36-counter single-group case.
All 11 concept scenes passed the browser run; the new default desktop/mobile
and extreme mobile screenshots were visually reviewed. Current-source hashes,
keyboard operation, exact reset and layout checks passed. Evidence is in
`/tmp/primer-spatial-qa.lNZaZE/concepts-groups/`. Measurement, time and introductory
fractions remain in stage-one mathematics. Nothing has been deployed.

Measurement, time and introductory fractions are now implemented. The ruler
preserves length when translated and converts cm to mm; the clock uses continuously
advancing hour angles and includes a correctly aligned September 2026 calendar;
the fraction bars preserve the same whole while comparing quarters and halves.
Numerical checks cover 40 ruler settings, 288 clock times, 30 calendar dates and
five fractions. These additions complete model presence for maths stages zero
and one. All 14 concept routes passed browser verification after the server was
reloaded: keyboard operation, exact reset, label bounds, overflow and current-source
hash checks. The three additions' desktop/mobile screenshots were visually reviewed;
the calendar's weekday alignment and the half/quarter comparison are legible.
Evidence: `/tmp/primer-spatial-qa.lNZaZE/concepts-measure/`. This is cohort verification,
not approval of the 337 remaining uncovered lessons. Next-stage gaps include
decimals, percentages, order of operations, primes, ratios, exponents, coordinates,
data and pre-algebra. Nothing has been deployed.

Stage-two additions: percentages and coordinates. Percentages connect a
hundred-grid, simplified fraction, decimal and computed part of a variable whole;
2,121 combinations are checked. Coordinates show horizontal-then-vertical steps
and classify every point of the 11×11 control grid, including axes and origin.
Both are registered in the curriculum and browser harness. After reloading the
QA server, all 16 concept scenes passed browser checks for controls, keyboard
operation, exact reset, label bounds, overflow and current-source hashes. The
percentage and coordinate desktop/mobile screenshots were visually inspected.
Evidence: `/tmp/primer-spatial-qa.lNZaZE/concepts-percent/`. The remaining seven
stage-two gaps are decimals, order of operations, primes, ratios, exponents,
data and pre-algebra. No deployment has occurred.

Decimal addition and order of operations are implemented and bound to their
lessons. Decimal addition uses integer hundredths internally, two colour-coded
hundred-grids, and explicit carries; all 10,000 input pairs are checked. The
expression tree distinguishes a + b × c from (a + b) × c, with 1,800 configurations
checked. Their desktop/mobile screenshots, the 0.99 + 0.99 case and both expression
trees were visually reviewed. An initial browser run detected an unrelated app.js
change during testing and was not accepted. A fresh full run passed all 18 concept
scenes against current-source hashes, with keyboard/reset and layout checks.
Evidence: `/tmp/primer-spatial-qa.lNZaZE/concepts-decimals-current/`.
The required-complete coverage gate still fails at 99/432, as expected; this is not
a release-ready state. Remaining stage-two gaps: primes, ratios, exponents, data
and pre-algebra.

The five remaining stage-two models are implemented: factor/divisor testing,
ratio scaling, exponent chains, mean/median exploration, and substitution into
ax+b. Numerical checks cover 3,600 divisor tests, 150 ratios, 36 exponent pairs,
130 statistical fixtures/parameter sweeps (not all 21^5 datasets), and 847 signed
substitutions. Focused schema, model and gallery tests pass (555 tests), and the
asset checker passes. Every maths lesson in stages 0–2 now has model coverage.
The reloaded QA server passed all 23 concept routes against current-source
hashes; evidence: `/tmp/primer-spatial-qa.lNZaZE/concepts-stage2-final/`.
Visual review of all five maximum-value mobile renders passed. The data chart
now puts value labels above the mean/median line band; a dedicated regression
assertion protects this, and a fresh focused run passed 553 tests. Its desktop
render was also reviewed. Fresh desktop captures of primes, ratios, exponents
and substitution were reviewed; `/tmp/primer-primes-recapture.png` shows the
complete factor scene. Some earlier captures were inconsistent despite correct
live geometry. The harness now disables entrance animations during capture and
checks actual rendered text bounds against the canvas as well as SVG-local
bounds. All 23 routes passed this strengthened containment check, including
mobile and control extremes; evidence: `/tmp/primer-stage2-containment/`.
No deployment has occurred; 328 lessons still lack models.

Stage-three linear equations and slope are now implemented and bound to their
lessons. Equation operations preserve exact quotient solutions; slope exposes
rise, run and intercept with an analytically clipped line. The invariant suite
checks 5,850 equation/step combinations and 252 slope configurations. All 651
focused model/schema and gallery tests pass. After a curriculum reload, all 25
concept routes passed browser checks against current source hashes, including
keyboard/reset, label containment and desktop/mobile layouts. Added explicit
negative-fraction solution steps and steep positive/negative/horizontal slope
cases. Desktop/mobile defaults and selected edge captures were visually reviewed.
Evidence: `/tmp/primer-algebra-edges/`. The asset checker passes 109 models.
The required-complete gate still correctly fails: 326 lessons remain uncovered.

Systems of equations and quadratics are implemented. Systems distinguish unique,
parallel and coincident solutions; quadratics show vertex, opening direction and
zero/one repeated/two real roots. Invariants cover all 1,225 line pairs and 270
quadratics in the control ranges. All 755 focused model/schema and gallery tests
pass, along with the 432-illustration/111-model asset check. All 27 concept routes
passed desktop/mobile, keyboard/reset and clipping checks against current source
hashes. Defaults and selected special-case screenshots were visually reviewed;
evidence: `/tmp/primer-intersections-final/`. The keyboard harness now moves left when a slider starts at maximum,
rather than incorrectly expecting ArrowRight to change an already-maximal value.

Trigonometry, exponential/logarithmic inverse maps, and arithmetic/geometric
sequences are implemented. Tests cover all 25 angle settings, 28 base/exponent
pairs and 192 sequence configurations, including finite-sum identities. All 926
focused model/schema and gallery tests pass; the asset checker reports 114 models.
Mobile default and selected edge renders were visually reviewed, including
third-quadrant coordinates, 5^-3 = 1/125 and the six-term geometric maximum.
All 30 concept routes passed current-source browser checks: desktop/mobile,
keyboard/reset, rendered-label containment and special cases. Evidence:
`/tmp/primer-growth-qa/`. Coverage remains incomplete (321 gaps).

Probability, statistics, limits and polynomials are implemented. Invariants cover
22 dice-event configurations, 1,430 population/sample spread configurations,
168 approach/point-value configurations and 250 cubic root/sign configurations
(13 evaluation points per cubic). Focused model/schema and gallery checks pass
1,182 tests after a visual-review improvement: vertical zoom now makes cubic
crossing/touching behaviour easier to inspect. All 34 concept routes pass browser
checks against current-source hashes, with desktop/mobile, keyboard/reset and
special cases. All four default mobile renders and selected edge cases were
reviewed. Evidence: `/tmp/primer-evidence-final/`. The asset checker passes 118 models.

Euclidean proof, complex multiplication, derivatives and integrals are implemented.
Invariants cover 50 triangle configurations, 490 complex rotations/scales, 144
secant configurations and 720 rectangle sums. Rendered triangle areas and side
lengths are also checked for congruence under control changes; all 1,470 focused
model/schema and gallery tests pass. All 38 concept
routes pass current-source browser checks, including corner one-sided slopes,
signed midpoint sums, zero complex numbers and unequal-leg rearrangements.
Mobile defaults and selected edge captures were visually reviewed. Evidence:
`/tmp/primer-calculus-qa/`. All mathematics lessons at stages 0–3 now have model
presence; 13 mathematics lessons at stages 4–5 remain without models. This does
not certify the entire mathematics visual audit or the all-subject rollout.

The remaining five stage-four mathematics models are implemented: Euler ODE
steps, graph Euler trails, extended Euclid, epsilon–delta neighbourhoods, and
binomial distributions. Independent checks cover 128 ODE configurations, all 64
four-vertex graphs (exhaustive trail search), 1,600 integer pairs, 640 epsilon/delta
configurations and 1,210 distribution/cutoff configurations. All 1,875 focused
tests pass. The asset checker reports 127 models. All 43 concept routes passed
browser checks against current-source hashes, including keyboard/reset,
desktop/mobile label containment and special cases. All five default mobile
renders and selected edge cases were visually reviewed. Evidence:
`/tmp/primer-stage4-qa/`.
Only eight stage-five mathematics lessons remain without models; all-subject
coverage is still incomplete (308 gaps), so deployment remains pending.

Abstract algebra, measure theory, functional analysis and numerical analysis now
have models. Sources linked in the activities include MIT cyclic-group/Fourier
notes, Harvard analysis notes and NIST DLMF numerical methods. Checks cover 1,716
cyclic-group configurations, 12 finite Cantor constructions, 108 Fourier
projection/perturbation configurations (independent 4,096-point quadrature) and
187 bisection/Newton configurations. All 2,235 focused tests pass; assets validate
at 131 models. All 47 concept routes passed browser verification; evidence:
`/tmp/primer-postgrad-final/`. Mobile defaults and selected edge cases were
visually reviewed. Subgroup traces now have directional arrowheads. A subsequent
numerical-display fix uses exact fractional bisection error bounds instead of
rounding them downward; the full focused suite and a current-source targeted
browser rerun passed (`/tmp/primer-postgrad-exact/`). The browser harness now
accepts an optional validated comma-separated scenario list for targeted checks;
omitting it still runs the complete registry. Four mathematics lessons and
304 lessons across all subjects remain without models; no deployment has occurred.

The earlier 894-test full-suite pass predates these models. The prior illustration
work remains in the working tree. Do not stage unrelated/user-owned duplicate
files. No deployment has occurred for this rollout.
