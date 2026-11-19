# Stored MSK 3D models bound to the structures and parts their labels name (2026-11-18)

## The decision

The MSK evidence ledger holds 636 stored 3D models. 12 of them had a binding. On 2026-11-18 the project
owner asked for the 3D models to be bound. The radiology ledger's models were bound first
(`docs/model-bindings-20261118`). This pass reviews the 624 unbound MSK models.

An MSK requirement is usually split into parts. A ligament has attachments and a course. A muscle has a
belly and junctions. A bone has regions, cortex and marrow. The fidelity checker counts the parts, not the
parent structure (`requirements_for`). So binding an MSK model means choosing the part it actually shows.

## What was bound

147 partial bindings on 115 models, covering 129 requirement parts and structures. Bound structures and
parts (both ledgers) go from 1,062 to 1,179 of 57,985. In the MSK fidelity checker, model rows move from
missing to unverified: unverified rows go from 173 to 326, and missing rows from 5,119 to 4,966. Nothing is
anatomically approved, and no radiologist has reviewed these bindings.

| Investigation | Models | Bindings | Bound requirements |
| --- | --- | --- | --- |
| `ra.mri-ankle` | 36 | 37 | 18 → 45 |
| `ra.mri-knee` | 28 | 28 | 31 → 47 |
| `ra.mri-diabetic-foot` | 24 | 25 | 10 → 31 |
| `ra.ultrasound-joint-injection` | 14 | 14 | 4 → 13 |
| `ra.mri-shoulder` | 14 | 14 | 16 → 30 |
| `ra.mri-elbow` | 11 | 11 | 14 → 25 |
| `ra.ultrasound-shoulder` | 9 | 9 | 6 → 13 |
| `ra.hip-fai` | 8 | 8 | 7 → 13 |
| `ra.ankle-fractures` | 7 | 7 | 7 → 10 |
| `ra.foot-ankle-cases` | 7 | 7 | 7 → 10 |
| `ra.wrist-fractures` | 6 | 6 | 24 → 24 |
| `ra.wrist-instability` | 6 | 6 | 24 → 24 |

A binding to a part that two investigations share is counted in both. The six wrist bindings are to
parts of the triangular fibrocartilage complex that figures already cover, so they add model coverage but
no new bound requirement.

By source: Z-Anatomy 104 models (136 bindings), Malaya MRI knee 7 (7), Open Knee(s) 3 (3), Malaya MRI
ankle 1 (1).

## How a pair was accepted

1. The model's own label names the structure. The label is stored verbatim and quoted in the coverage
   basis.
2. The requirement is one of:
   - the structure itself, when it has no parts (22 bindings: muscles at the knee, elbow and hip, the
     tibial nerve, the iliopsoas bursa, ultrasound shoulder ligaments);
   - the part that is the structure's own body, which a model of the whole structure shows (60). These
     are a ligament's or nerve's course, a ligament's or tendon's midsubstance or midportion, a muscle
     belly, a tendon substance, an articular surface and bursal boundaries (`body_parts`). This follows the
     earlier MSK bindings: a hamstring muscle object binds the muscle belly, and a ligament object binds
     its course;
   - a part that the label itself names (55). Examples are the superficial part of the tibial collateral
     ligament for the MCL's superficial component, the ulnolunate ligament of the TFCC, a tendon sheath, a
     nerve branch, a deltoid fibre bundle, or a bone's cartilage surface for its articular surfaces;
   - a small named group or union, of which the label names one member (10). Examples are the
     trochanteric bursae and the "fibular tendons" of the posterior subtalar injection target.
3. The fidelity checker finds no conflict.
4. The requirement belongs to an investigation that lists the model, or whose 3D view shows it.

A whole is never bound to a requirement that names its regions, bundles or components. The ACL is not
bound to its bundles, a bone to its malleoli or facets, a meniscus to its horns, or the plantar
aponeurosis to its bands. A part is never bound to its whole: one head of the pronator teres is not bound
to the whole muscle.

### Which investigation a model belongs to

Most Z-Anatomy models listed no investigation, but the app shows them anyway. Each MSK investigation's 3D
view loads an atlas region (shoulder, elbow, wrist, hip, knee or ankle) from the spatial model in the
catalog (`web/app.js`). A model in that region is shown to every learner of the investigation. The review
records each investigation's regions (`displays`), and the tool checks the model against the atlas
manifest's region list. Where the view shows the model but the record did not list the investigation, the
investigation is added to the record (135 additions on 100 models). A test recomputes `displays` from the
catalog.

### Words in other words

35 bindings name the structure in other words, and 4 name one member of a group. Each pair is listed in
`review.json` with its reason. Removing a pair makes the tool refuse its bindings. Examples:

| Label says | Requirement names | Why |
| --- | --- | --- |
| calcaneal tendon | Achilles tendon | the anatomical name |
| patellar ligament | patellar tendon | the anatomical name |
| superficial part of tibial collateral ligament | medial collateral ligament superficial component | the same ligament and part |
| anterior / posterior tibiofibular ligament | anterior / posterior inferior tibiofibular ligament | the syndesmotic ligaments |
| tibionavicular, tibiocalcaneal, posterior tibiotalar ligament | the deltoid ligament's fibre bundles | parts of the deltoid ligament |
| medial / lateral plantar nerve | the tibial nerve's medial / lateral plantar branch | its branches |
| cartilage surface (of a tarsal bone) | articular surfaces | a bone's cartilage-covered surfaces |
| clavicular, acromial, spinal part of deltoid | anterior, middle, posterior deltoid | the three parts |
| intertubercular tendon sheath | long head of biceps tendon sheath | the sheath in the bicipital groove |
| iliopectineal bursa | iliopsoas bursa | another name |
| tibialis anterior, EHL, EDL, fibularis tertius | anterior tendons (tibiotalar injection target) | the anterior ankle tendons |

### Sides

Every bound requirement is for the examined side. Z-Anatomy and the Malaya MRI models are right-side
references, and the Open Knee(s) specimen is a left knee. Each coverage basis says which, and that the
model is a mirror image for the other side.

## Earlier decisions kept

- An earlier Open Knee(s) review (`docs/msk-openknee-schematic-review`) left both tibial cartilages
  unbound: their selected mask revision lineage is unresolved. They stay unbound.
- The hamstring muscle objects keep only their muscle-belly bindings, and their tendon surfaces stay
  unbound.

## What was not bound

All 509 other models are listed in `review.json` under `not_bound`, each with its reason:

- 285: no requirement of an investigation that lists or shows the model names the structure.
- 61: the model is a cartilage surface of several joints, for example both ends of the tibia. Each
  requirement names one surface, or a region of one.
- 57: no MSK investigation lists or shows the model. These are the 57 BodyParts3D muscle and bone models.
- 37: a whole bone. The bone requirements name its regions, cortex and marrow.
- 28: the requirement names only regions, bundles, components or segments of the same structure. Examples
  are the cruciate ligaments, the menisci, the labra, the elbow ulnar collateral ligament, the nerves, the
  retinacula and the scapholunate and lunotriquetral ligaments.
- 25: the requirement names the tendon and the model is the whole muscle-tendon unit, or the other way
  round.
- 13: the model is one head or part of a muscle that the requirement names as a whole.
- 3: specific cases: the two Open Knee(s) tibial cartilages, and the extensor digitorum, which the elbow
  3D view does not show.

## Updated with the ledger

- `docs/native-source-presentation-review-20261011/current-msk-audit.json`: the queue audit gets the new
  review-scope fingerprints of the 115 models, the 154 requirement rows that gained a model candidate, and
  the new counts. Nothing else in it changed.
- `docs/msk-review-queue/`: regenerated with `tools/build_msk_review_queue.py`. The hamstring page was
  already behind the ledger and is now current.

## Limits of this pass

- This is a check of source labels, requirement parts and the 3D views, not a radiologist review. The
  meshes were not compared with patient images.
- Bindings are to the requirement leaf, not to every part of the structure. Coverage is always partial.

## Files

- `review.json`: accepted rows (label, evidence, leaf basis, investigations, side), `body_parts`,
  `displays` and `atlases`, the pairs in other words with reasons, and every unbound model with its
  reason.
- `inverse.json`: exact byte edits and hashes for the MSK evidence file.
- Tool: `tools/anatomy_sources/bind_msk_models.py`. It refuses a row whose requirement is not in an
  investigation that lists or shows the model, whose label is not in the record or does not name the
  requirement as recorded, whose part is not the recorded kind, or that the checker refuses.
- Tests: `tests/test_msk_model_bindings.py`.
