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
| With an explicitly bound source image or model | 188 |
| Investigations with no bound structure at all | 112 |

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

### Radiology Assistant figures stored and bound

On the project owner's direction, reviewed Radiology Assistant figures are now stored locally and bound.

- 82 candidate figures came from article sections headed with a structure's name. Each was looked at; 35 plainly show the structure and were accepted. Tables, photographs, mixed-modality composites and unclear figures were rejected.
- 33 figures are stored and give 34 bindings across 13 investigations. Bound requirements rise from 160 to 188 of 57,985. Investigations with no bound asset fall from 117 to 112.
- Every binding is partial, source-reviewed and not clinically approved. The review was not done by a radiologist.
- The publisher permits educational reproduction with credit, not commercial use. Each asset records this and keeps the `commercial_rights_unverified` issue.
- Sided requirements stay unbound, because the figures do not state a side.

Details are in `docs/radiology-assistant-figure-bindings-20261116/README.md`.

Run `python tools/audit_structure_coverage.py` for the current count per investigation.

### Source locators (xrayhead.com and Radiology Assistant)

The project owner named two sources on 2026-11-16: the Stanford MSK MRI Atlas at xrayhead.com for musculoskeletal work, and Radiology Assistant as the primary source for everything else.

How each is used:

- xrayhead.com states no reuse licence and lists no contact address, so its images are not copied or embedded. It is used by link-out locator only.
- Radiology Assistant permits reproduction for educational purposes with credit. Reviewed figures are stored and bound under those terms (see above). Every other structure is reached by link-out locator.

A locator says where a named structure is shown in the source. It does not count towards coverage.

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

The page is `web/radiology/structure-atlas/index.html`, linked from the Structured reporting module. Rebuild the data with `python tools/anatomy_sources/build_structure_source_locators.py`.

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

## Language activities added on 2026-11-16 (second batch)

Every language module now has a dedicated activity. This batch adds 22, one for each module that had none.

| Module | Activity | Contains |
|---|---|---|
| Letter Sounds | Letters and their sounds | table, game |
| Talking and Listening | Question words | table, game |
| Story Time | Beginning, middle and end | table, game |
| Great Children's Books | Classic children's books | table, time line, game |
| Handwriting | Tall, small and tail letters | table, drawing of the writing lines, game |
| Learning to Read | Read a sentence and understand it | table, game |
| Word Collecting | Words, partners and opposites | table, game |
| Writing Your Own Stories | The story mountain | table, drawing, game |
| Myths and Legends | Gods, tricksters and where their stories come from | table, map, game |
| Reading Novels | Character, setting, plot, theme and point of view | table, plot drawing, game |
| Finding Things Out | Primary, secondary and tertiary sources | table, checking algorithm, game |
| Public Speaking | Plan and pace a talk | interactive plan, bar drawing, draft timer |
| The Essay | The parts of an argument | table, game |
| Literature | Literary devices in famous lines | table, game |
| Shakespeare | Comedies, histories and tragedies | table, time line, game |
| World Literature | Great works and where they come from | table, map, game |
| The Ancient Canon | The Greek and Roman canon in time | table, time line, game |
| Comparative Literature | Poetic forms across traditions | table, game |
| Literary Theory | Schools of literary theory | table, game |
| Computational Linguistics | Counting word pairs: a tiny language model | interactive model, algorithm, table |
| Psycholinguistics | Garden-path sentences | table, game |
| Sociolinguistics | Register: the same message in five styles | table, game |

Notes:

- The maps place points by longitude and latitude on a plain grid. No coastlines are drawn.
- Dates of ancient works and of Shakespeare's plays are approximate and are labelled so.
- Twenty of the activities share one layout (reference table, optional drawing, sorting game). They are generated by `tools/build_language_sorting_activities.py`; each generated `lab.js` is self-contained and tested.

## Mathematics activities added on 2026-11-17 (first batch of two)

Eighteen activities for the early and middle mathematics modules that had none. Each has sliders or a choice, a drawing, a table of values and a result line. They are generated by `tools/build_math_number_activities.py`.

| Module | Activity |
|---|---|
| Bigger and Smaller | Which is bigger? |
| Counting | Count up and count back |
| Numbers to Twenty | Tens and ones up to twenty |
| Patterns | What comes next? |
| Shapes All Around | Shapes and their sides |
| Addition | Adding with tens and ones |
| Subtraction | Taking away and finding the difference |
| Multiplication | Rows and columns: the times tables |
| Division | Sharing into equal groups |
| Halves and Quarters | Equal parts of a whole |
| Measuring Things | Measuring with small and large units |
| Place Value | What each digit is worth |
| The Coordinate Plane | Plotting a point |
| Decimals | Calculating with decimals |
| Fractions | Adding, multiplying and comparing fractions |
| Area, Perimeter and Volume | Measuring shapes and solids |
| Percentages | Percent, fraction and decimal |
| Ratio and Proportion | Sharing in a ratio and scaling up |

The remaining twenty-two mathematics modules are covered by the second batch below.

## Mathematics activities added on 2026-11-17 (second batch)

Twenty-two activities for the secondary and university modules, generated by `tools/build_math_higher_activities.py`. With these, every mathematics module has a dedicated activity.

| Module | Activity |
|---|---|
| Functions | Evaluating and composing functions |
| Linear Equations | Solving a linear equation |
| Polynomials | From roots to a polynomial |
| Quadratic Equations | Solving a quadratic three ways |
| Slope and Lines | The line through two points |
| Vectors | Adding vectors and the dot product |
| Real Analysis | Convergence: for every ε there is an N |
| Discrete Mathematics | Sets: union, intersection and counting |
| Linear Algebra | A matrix as a transformation of the plane |
| Multivariable Calculus | Partial derivatives and the gradient |
| Number Theory | Euclid's algorithm and arithmetic on a clock |
| Probability Theory | The binomial distribution |
| Abstract Algebra | Subgroups of the integers modulo n |
| Complex Analysis | A complex function as a map of the plane |
| Differential Geometry | Curvature and the circle of best fit |
| The Frontier | An open problem you can try: the Collatz conjecture |
| Functional Analysis | Approximating a function by sine waves |
| Logic and Set Theory | Truth tables and logical equivalence |
| Measure Theory | The Cantor set: uncountable, yet of length zero |
| Numerical Analysis | Newton's method and how fast it converges |
| Partial Differential Equations | Heat flow along a rod |
| Topology | Counting corners, edges and faces |

Each university activity illustrates one idea from its module. It does not cover the module.

## Physics activities added on 2026-11-17

Twenty-two activities, one for each physics module that had none, generated by `tools/build_physics_activities.py`. With these, every mathematics, physics and language module has a dedicated activity.

| Module | Activity |
|---|---|
| Hot and Cold | Heat moves from warm to cool |
| Light and Shadow | Where shadows come from |
| Pushes and Pulls | Pushes, pulls and what happens next |
| Energy Everywhere | Energy changes form as a ball falls |
| Magnets | A compass around a bar magnet |
| How Things Move | Speed, time and distance |
| Electricity | Two bulbs: in series or in parallel |
| States of Matter | Heating ice until it is steam |
| Measuring the World | A measurement and its uncertainty |
| Electricity and Magnetism | Faraday's law: a changing field makes a voltage |
| Work, Energy and Momentum | Collisions: momentum is always conserved |
| Thermodynamics | The best any heat engine can do |
| Electrodynamics | One wave, every wavelength |
| Fluid Mechanics | Flow through a narrowing pipe |
| Particle Physics | Building particles from quarks |
| Quantum Mechanics | An electron in a box |
| Relativity | One event seen from a moving frame |
| Solid State Physics | Band gaps and why semiconductors conduct |
| Statistical Mechanics | Entropy is counting |
| General Relativity and Cosmology | Time near a black hole |
| Quantum Field Theory | Why some forces reach further than others |
| Quantum Information | One qubit: states, gates and measurement |

Each activity states its simplifying assumptions in its result line (for example no air resistance, a level frictionless pipe, a non-rotating black hole and a hovering observer). Physical constants are the 2019 SI values. Each university activity illustrates one idea from its module; it does not cover the module.

## Radiology Assistant bindings: second pass (2026-11-17)

A wider search of the Radiology Assistant articles brings the totals to 77 stored figures and 90 bindings. Bound requirements rise from 188 to 240 of 57,985, and investigations with no bound asset fall from 112 to 92. A figure is bound only if it suits every investigation that shares the structure. Details and limits are in `docs/radiology-assistant-figure-bindings-20261116/README.md`.

What still blocks most of the inventory:

- 411 candidate pairs were skipped because the requirement names a side and the figure does not.
- Most requirements are finer than anything the articles name or label.
- No binding has been reviewed by a radiologist.

## Stored figures bound from their own captions (2026-11-17)

Stored, openly licensed figures were bound where their own published caption names a required
structure and no modality or side conflict exists: 29 bindings on 21 figures; bound structures
240 → 258 of 57,985; investigations with none 92 → 88. The stored catalogue yields little more
under the current rules: about 190 further caption matches fail only because the figure record
states no side. Details: `docs/stored-asset-caption-bindings-20261117/README.md`.

## Side rule relaxed and second stored-figure pass (2026-11-17)

On the project owner's direction, a figure whose record states no side may now be bound to a left
or right requirement. Such coverage can be partial at most and cannot verify the requirement; a
stated side must still match. With that rule and wider name matching, 280 further bindings were
made on 154 stored figures: bound structures 258 → 449 of 57,985; investigations with none 88 → 73.
Findings and diagnoses were left unbound. Details:
`docs/stored-asset-caption-bindings-pass2-20261117/README.md`.

Earlier sections of this document that say sided requirements stay unbound describe the state
before this change.

## Radiology Assistant figures for sided structures (2026-11-17)

118 section figures naming unbound left or right structures were reviewed; 39 were stored with 62
partial bindings on 54 structures. Bound structures 449 → 503 of 57,985; investigations with none
73 → 67. Details: `docs/radiology-assistant-sided-figure-bindings-20261117/README.md`.

## Figures of findings bound to finding requirements (2026-11-18)

On 2026-11-18 the project owner decided that figures of findings are bound to finding requirements.
The stored figures were reviewed for that (`docs/finding-figure-bindings-20261118`): 462 partial
bindings on 245 figures, covering 237 finding requirements. Bound structures 503 → 739 of 57,985;
investigations with none 67 → 51. Each binding quotes the sentence that names the finding; 34 rest
on a listed kind-of pair (a contusion is an injury). Unsided lung findings, catch-all requirements,
measurements and findings named only in a note that the source's suggestion is unconfirmed were not
bound. Nothing is anatomically approved.

## Figure-record context codes repaired (2026-11-18)

256 stored figures and models carried a context code the checker could not read, so it refused every
binding of them. 250 were repaired in the evidence ledger (`docs/source-context-code-repairs-20261118`):
318 changes into the checker's vocabulary, each with its rule, and a reviewed state where the old code
did not say what the figure shows. Six deliberate empty panel selections were left as they are, and
nine context-only figures keep that restriction. On the repaired figures, 375 caption matches (318
structure, 57 finding) can now be reviewed for binding. Bound structures stay at 739 of 57,985. The
app's figure catalog keeps the original codes.

## Unlocked figures bound (2026-11-18)

The figures that the context-code repair unlocked were reviewed for binding, structures and findings
alike (`docs/unlocked-figure-bindings-20261118`): 515 partial bindings on 138 figures, covering 283
requirements. Bound structures 739 → 993 of 57,985; investigations with none 51 → 47 (oesophagus,
epilepsy MRI, swallowing and cervical lymph nodes gain their first bindings). Each binding quotes the
sentence that names the structure or finding; 51 rest on a listed kind-of pair (a carcinoma is a
tumour) and 10 on a legend letter that a selected panel carries. After the figures were looked at,
three bindings were withdrawn: an orbit cyst whose stated side conflicts with the image, and both sides
of an unsided pouch above the diaphragm. The 69 repaired 3D models are reference-only and stay unbound. Nothing is
anatomically approved.

## 3D models bound (2026-11-18)

The 142 stored 3D models without a binding were reviewed against the requirements of their
investigations (`docs/model-bindings-20261118`): 108 partial bindings on 69 models, covering 94
structure requirements. Bound structures 993 → 1,062 of 57,985; investigations with none 47 → 45
(thyroid ultrasound and prostate MRI gain their first bindings). Each binding quotes the model's own
source label. A label that names a whole is not bound to a requirement that names its parts. Where a
label states a side, the stored mesh was checked to lie on that side of its source's midline. That
check found that the HRA female pelvis source swaps its round ligament labels; neither is bound. The
other 73 models are listed with their reasons. The MSK ledger's 636 models (12 bound) are a separate
pass. Nothing is anatomically approved.

## MSK 3D models bound (2026-11-18)

The 624 unbound models of the MSK evidence ledger were reviewed (`docs/msk-model-bindings-20261118`):
147 partial bindings on 115 models, covering 129 requirement parts and structures. Bound structures
993 → 1,062 → 1,179 of 57,985 across the two model passes. In the MSK checker, unverified rows 173 → 326
and missing rows 5,119 → 4,966. A model binds the structure itself (when it has no parts), the part that
is the structure's own body (course, midsubstance, muscle belly, articular surface), a part its label
names, or one member of a named group. A whole is never bound to its regions, bundles or components.
Where an investigation's 3D view shows a Z-Anatomy model that the record did not list, the investigation
was added to the record (135 additions). An earlier Open Knee(s) review that left the tibial cartilages
unbound was kept. Nothing is anatomically approved.
