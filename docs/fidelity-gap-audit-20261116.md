# Fidelity gap audit and first activity batch (2026-11-16)

This records where the modules stand against the goal of clinical-grade radiology and fully illustrated, interactive math, physics and language modules, and what the first batch of work adds.

## Radiology

Source: `docs/radiology-fidelity-scope.json`, `data/radiology/*structure-requirements.json`, `data/radiology/*asset-evidence.json`.

| Measure | Count |
|---|---|
| Investigations tracked | 136 |
| Marked clinically approved | 0 |
| With a draft structure inventory | 136 (99 earlier, 37 added 2026-11-16) |
| Still without a structure inventory | 0 |
| Non-MSK assets with no fidelity assessment recorded | 968 of 974 |
| MSK models recorded as not assessed | 504 of 736 |

Structure-level coverage, from `tools/audit_structure_coverage.py`:

| Measure | Count |
|---|---|
| Investigations with a structure inventory | 136 |
| Required structures and parts in those inventories | 57,985 |
| With an explicitly bound source image or model | 158 |
| Investigations with no bound structure at all | 118 |

The inventories are deliberately granular (for example, each named part of the distal tibia is a separate requirement), so the totals are large. The proportion still shows the position: under 1% of what must be shown has a bound, reviewed source.

What this means:

- The repository's own rule is that presence is not fidelity: each reportable structure needs an explicit, reviewed binding to a source image or model.
- Reaching a standard where certification could reasonably be expected needs two things that cannot be produced by authoring alone: licensed source imaging or meshes that show each structure, and review by a radiologist. Synthetic or inferred anatomy must not be presented as high fidelity.

### Inventories added on 2026-11-16

The 37 investigations that had no inventory now have a draft one (`tools/anatomy_sources/expand_remaining_requirements.py`).

- Each inventory lists the rows of that investigation's own click-builder reporting checklist: 733 requirements in total. Technique and report-review rows are left out.
- No sub-parts are invented. The earlier inventories expand each structure into named parts; these do not, so they are coarser and are marked `reporting_checklist_rows_without_sub_part_expansion`.
- 26 rows record context or a conclusion (for example "Time point" in RECIST) and are tagged as reporting items, not anatomy.
- Every inventory is `draft_requires_specialist_review`. No investigation is marked clinically approved.

### Binding assets to the new inventories

Three source-reviewed bindings were added. None is clinically approved.

- The stored thoracic ultrasound figure of the diaphragm shows both sides in one image, so it could not be bound to a sided requirement. Its peer-reviewed caption states the side of each lettered panel. The figure was split into its three panels, and each panel is bound to the right or left diaphragm requirement with partial coverage. Details are in `docs/thoracic-ultrasound-side-panels-20261116/README.md`.
- Bound requirements rise from 158 to 160 of 57,985. Investigations with no bound asset fall from 118 to 117.
- The other six thoracic ultrasound requirements stay unbound. No stored open figure states a side for them.
- The other 36 new investigations have no local source image or model.

Run `python tools/audit_structure_coverage.py` for the current count per investigation.

### Source locators (xrayhead.com and Radiology Assistant)

The project owner named two sources on 2026-11-16: the Stanford MSK MRI Atlas at xrayhead.com for musculoskeletal work, and Radiology Assistant as the primary source for everything else.

Neither source can supply bound assets:

- xrayhead.com states no reuse licence, so its images cannot be copied or embedded.
- Radiology Assistant permits reproduction for educational purposes with credit. That is not a commercial redistribution licence, which the fidelity checker requires for a bound asset.

Both are therefore used as link-out locators. A locator says where a named structure is shown in the source. It does not count towards coverage.

| Measure | Count |
| --- | --- |
| Reportable structures (top level) | 7,893 |
| Located in the Stanford MSK MRI Atlas | 199 |
| Located in a Radiology Assistant section | 593 |
| Located in either | 691 |
| Investigations with no locator | 57 of 136 |

- Atlas locators give the region, the label and the axial, coronal and sagittal slice numbers on which the label appears. A label matches a requirement by the same name or by a hand-reviewed synonym. Where the atlas labels only named parts of a structure, the locator says so.
- Radiology Assistant locators give the article section in which the structure is named, with the publisher's own figure shown from the publisher's address and credited.
- Matching is on the structure name. No radiologist has reviewed the locators.
- Most requirements are finer than either source names, which is why most have no locator.

The page is `web/radiology/structure-atlas/index.html`, linked from the Structured reporting module. Rebuild the data with `python tools/anatomy_sources/build_structure_source_locators.py CACHE_DIR`.

## Math, physics and language

Every module has an illustration and a 3D model. The gap is modules that use a generic shared model rather than a module-specific interactive.

| Domain | Modules | With a dedicated lab or activity before this batch | Added here |
|---|---|---|---|
| Mathematics | 59 | 29 | 12 |
| Physics | 39 | 20 | 8 |
| Language | 40 | 11 | 8 |

The counts come from matching module ids in the lab scripts and activity links; they are an estimate, not a reviewed inventory.

## Activities added

Twenty-eight stand-alone activities, each with a calculation model tested against hand-worked values (`tests/activity-models.test.cjs`, run in CI by `tests/test_lesson_activities.py`).

| Module | Activity |
|---|---|
| Trigonometry | Sine and cosine on the unit circle |
| Exponentials and Logarithms | Exponential growth and decay |
| Sequences and Series | Arithmetic and geometric series |
| Systems of Equations | Where two lines meet |
| Negative Numbers | Negative numbers on the number line |
| Primes and Factors | Primes, factors and common divisors |
| Forces and Friction | A block on a slope |
| Simple Machines | Balancing a lever |
| Special Relativity: a First Look | Time dilation and length contraction |
| The Quantum Idea | The photoelectric effect |
| Time and Calendars | Reading a clock |
| Order of Operations | Order of operations, one step at a time |
| Powers | Powers and the laws of exponents |
| Letters for Numbers | Solving an equation like a balance |
| Complex Numbers and Beyond | Multiplying complex numbers |
| Differential Equations | Slope fields and Euler's method |
| Newton's Laws | Projectile motion |
| Floating and Sinking | Why things float or sink |
| Light and Color | Mixing coloured light |
| Heat and Temperature | Mixing warm and cool water |
| Grammar | Parts of speech in a sentence (table and self-test) |
| Sentences | Build a complete sentence |
| Poetry | Hearing the metre of a line (table of feet) |
| Where Words Come From | Word roots from Greek and Latin (root map) |
| History of English | A timeline of the English language |
| The Alphabet | The twenty-six letters |
| Paragraphs and Essays | The four jobs in a paragraph (algorithm and game) |
| Rhymes and Songs | Words that rhyme (families and odd-one-out game) |

Each activity has labelled controls, a drawing with a text description, a table of values and a plain-language result line.

## Adding further activities

Activities are now listed in `web/activities/registry.json`. The reader loads that file and shows the links for the open module, so a new activity needs only its own folder and one registry entry. `web/app.js` does not change, which avoids the proof-chain conflicts that each hard-coded link caused.

Shared drawing helpers and styles are in `web/activities/kit.js` and `web/activities/kit.css`.
