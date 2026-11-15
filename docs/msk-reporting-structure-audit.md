# MSK reporting structure audit

Review date: 26 September 2026. Status: **source-traceable draft requiring MSK radiologist review**.

The inventory defines 488 investigation-specific structure records and 1,615 required subparts across all 22 investigations in the source catalogue’s Musculoskeletal section. These are requirements, not counts of complete assets. Twenty-two additional entries explicitly identify curriculum umbrellas, supplementary MSK modules and related examinations filed under other specialties. Some records are conditional or require a named anatomical site, digit or vertebral level before completeness can be assessed.

The machine-readable contract is [msk-structure-requirements.json](../data/radiology/msk-structure-requirements.json). It contains stable structure and subpart IDs, laterality, modality conditions, the current reporting checklist and template text, zero-based checklist references, source URLs, source-review status and unresolved scope issues. No existing asset inventory was used to reduce the required anatomy.

## What counts as a requirement

Every listed part is a separate target. A label saying “rotator cuff”, a whole-bone surface, a bounding box or a link to an article does not demonstrate those parts. A meniscus needs distinguishable horns, body, roots and peripheral attachment; “cartilage” needs the specified opposing surfaces. Tendons and their muscles are separate structures. Implant interfaces, developmental cartilage and pathology-specific relationships require their own applicable representation.

`requires_site_instantiation: true` identifies an unresolved template. It cannot pass an asset audit until its named structures have been expanded for the selected region. The same applies to side, digit, vertebral level, implant configuration and postoperative anatomy. Conditional targets need a recorded applicable pathway or an explicit not-applicable reason.

Image, schematic and 3D evidence must be assessed separately. Source reading here does not establish permission to redistribute source figures, commercial-use rights, anatomical mesh accuracy or clinical validation. A schematic or 3D representation cannot prove findings that require an actual acquired image or clinical examination.

## Source-menu investigations

| Investigation | Structure records | Required subparts | Distinction retained |
|---|---:|---:|---|
| [Ankle fracture radiography](https://radiologyassistant.nl/musculoskeletal/ankle/weber-and-lauge-hansen-classification) (`ra.ankle-fractures`) | 27 | 110 | Malleoli, plafond, talus and syndesmosis; direct soft-tissue assessment needs another modality. |
| [MRI ankle](https://radiologyassistant.nl/musculoskeletal/ankle/mri-examination) (`ra.mri-ankle`) | 48 | 158 | Separate lateral/syndesmotic/deltoid/spring ligaments and each tendon compartment. |
| [Arthritis imaging](https://radiologyassistant.nl/musculoskeletal/arthritis/fractures-video-lesson) (`ra.arthritis`) | 6 | 18 | Instantiate every examined joint and compartment; distribution is not one joint. |
| [Bone tumour imaging](https://radiologyassistant.nl/musculoskeletal/bone-tumors/differential-diagnosis) (`ra.bone-tumours`) | 11 | 32 | Resolve host bone, compartments and named neurovascular neighbours for the actual site. |
| [Cartilage tumour imaging](https://radiologyassistant.nl/musculoskeletal/bone-tumors/chondrotumors-1) (`ra.cartilage-tumours`) | 13 | 39 | Keep tumour cap/endosteal interface separate from articular cartilage. |
| [Foot and ankle cases](https://radiologyassistant.nl/musculoskeletal/wrist-1/foot) (`ra.foot-ankle-cases`) | 31 | 120 | Lisfranc components, Chopart joints and coalition interfaces are different targets. |
| [MRI diabetic foot](https://radiologyassistant.nl/musculoskeletal/diabetic-foot/mri-examination) (`ra.mri-diabetic-foot`) | 48 | 203 | Trace ulcer-to-bone routes, individual bones, joints and fascial spaces. |
| [MRI elbow](https://radiologyassistant.nl/musculoskeletal/elbow/mri-examination) (`ra.mri-elbow`) | 38 | 83 | Keep collateral components, tendon attachments, nerve branches and entrapment sites distinct. |
| [Paediatric elbow radiography](https://radiologyassistant.nl/musculoskeletal/elbow/fractures-in-children) (`ra.paediatric-elbow-fractures`) | 14 | 47 | Age-specific physes, ossification centres, cartilage and alignment; scoped report corrected. |
| [Hip arthroplasty radiography](https://radiologyassistant.nl/musculoskeletal/hip/arthroplasty) (`ra.hip-arthroplasty`) | 9 | 38 | Requires actual implant components, liner, cement and zonal host-bone interfaces. |
| [Hip imaging — femoroacetabular impingement](https://radiologyassistant.nl/musculoskeletal/hip/femoroacetabular-impingement-syndrome) (`ra.hip-fai`) | 20 | 50 | Bony morphology, labrum and cartilage have different modality conditions. |
| [MRI knee](https://radiologyassistant.nl/musculoskeletal/knee/meniscal-pathology) (`ra.mri-knee`) | 49 | 144 | Meniscal segments/roots, six cartilage surfaces, cruciates/collaterals and corners. |
| [MRI muscle injury](https://radiologyassistant.nl/musculoskeletal/muscle/mri-traumatic-changes) (`ra.mri-muscle-injury`) | 8 | 23 | Instantiate named muscle–tendon–aponeurosis units for the acquired region. |
| [MRI non-traumatic muscle disease](https://radiologyassistant.nl/musculoskeletal/muscle/non-traumatic-changes) (`ra.mri-muscle-disease`) | 7 | 20 | Instantiate all examined muscles and affected nerve/compartment distributions. |
| [MRI hamstring injury](https://radiologyassistant.nl/musculoskeletal/muscle/hamstring-injury) (`ra.mri-hamstring`) | 14 | 53 | Separate conjoint and semimembranosus footprints, individual muscles and sciatic nerve. |
| [MRI shoulder](https://radiologyassistant.nl/musculoskeletal/shoulder/mri-anatomy) (`ra.mri-shoulder`) | 29 | 114 | Separate cuff muscles/tendons, labral sectors, pulley and capsuloligamentous attachments. |
| [Ultrasound shoulder](https://radiologyassistant.nl/musculoskeletal/shoulder/shoulder-ultrasound) (`ra.ultrasound-shoulder`) | 19 | 42 | Accessible tendon/posterior-joint views cannot claim complete MRI labral coverage. |
| [CT and MRI thoracolumbar fractures](https://radiologyassistant.nl/musculoskeletal/spine/tlics-classification-1) (`ra.thoracolumbar-fractures`) | 17 | 58 | Expand vertebral levels, neural structures and each posterior tension-band component. |
| [Stress fracture imaging](https://radiologyassistant.nl/musculoskeletal/unsorted/stress-fractures) (`ra.stress-fractures`) | 11 | 39 | Exact bone and tension/compression surface matter; expand the selected site. |
| [Ultrasound-guided joint injections](https://radiologyassistant.nl/musculoskeletal/ultrasound/us-guided-injection-of-joints) (`ra.ultrasound-joint-injection`) | 21 | 75 | Target-specific access anatomy; the source knee example is not ultrasound-guided. |
| [Wrist radiography — carpal instability](https://radiologyassistant.nl/musculoskeletal/wrist/carpal-instability) (`ra.wrist-instability`) | 25 | 78 | All carpals, articular relationships, Gilula arcs and individual bone axes. |
| [Wrist fracture imaging](https://radiologyassistant.nl/musculoskeletal/wrist/fractures) (`ra.wrist-fractures`) | 23 | 71 | Distal radial facets/rims/sigmoid notch, ulna and every included carpal. |

## Reporting defects and modality limits

**Paediatric elbow was inheriting a hip report.** Its effective checklist began with hip-plane, hip-development and painful-hip fields, and its classification was Graf. A dedicated `ra.paediatric-elbow-fractures` override now replaces that report with elbow alignment, development, fracture morphology, effusion and associated-injury fields. The requirements have been remapped to the corrected checklist and preserve the old checklist in `resolved_reporting_defects` for audit. The correction changes no other investigation override.

The corrected report qualifies anterior-humeral and radiocapitellar alignment by age, ossification and projection. It does not apply a universal middle-third rule to every child, or infer normal neurovascular status from a radiograph. These caveats are supported by primary studies of [anterior humeral-line age variability](https://pubmed.ncbi.nlm.nih.gov/19723996/) and [radiocapitellar-line limitations](https://pubmed.ncbi.nlm.nih.gov/21841436/); their abstracts were reviewed. The scoped fracture-imaging approach also uses the [RCH supracondylar guideline](https://www.rch.org.au/clinicalguide/guideline_index/fractures/supracondylar_fracture_of_the_humerus_emergency_department/) and [RCH lateral-condyle guideline](https://www.rch.org.au/clinicalguide/guideline_index/fractures/Lateral_condyle_fracture_of_the_humerus_-_Emergency_Department/). No new treatment algorithm or fixed age cutoff was introduced.

**Ankle fracture radiography is not direct tendon/ligament imaging.** The current generic ankle checklist requests partial versus complete soft-tissue discontinuity. The inventory preserves the anatomy but marks MRI/ultrasound as necessary for direct soft-tissue evidence. The foot-column item also depends on actual foot coverage. [Source: ankle fracture classification](https://radiologyassistant.nl/musculoskeletal/ankle/weber-and-lauge-hansen-classification).

**The joint-injection source contains a modality exception.** Its knee example is described as a blind lateral midpatellar approach. That example cannot validate an ultrasound needle-tip illustration. The module requires separate target-specific evidence and a validated ultrasound knee example before claiming that coverage. [Source: injection article, knee section](https://radiologyassistant.nl/musculoskeletal/ultrasound/us-guided-injection-of-joints).

**Thoracolumbar trauma retains an overbroad inherited report.** The current report includes generic degeneration fields. The requirements explicitly separate vertebral morphology, neural structures and the posterior tension-band components while retaining the need for a source-matched trauma-report rewrite. [Source: TLICS](https://radiologyassistant.nl/musculoskeletal/spine/tlics-classification-1), [source: AO thoracolumbar classification](https://radiologyassistant.nl/musculoskeletal/spine/ao-classification).

**Other limits remain explicit.** Radiographic joint-space loss is not direct cartilage visualization. Shoulder ultrasound cannot provide complete MRI labral coverage. A native hip mesh cannot represent an arthroplasty. Adult bones cannot stand in for the child’s unossified cartilage and physes. The knee corner decomposition goes beyond the older article’s abbreviated emphasis and requires contemporary specialist verification of the smaller components.

## Scope outside the 22 source-menu entries

The following entries are deliberately unresolved rather than excluded by menu location. “Linked” identifies potentially reusable requirements; it does not certify that the umbrella module’s own reporting guide is covered.

| Surface | Classification | Linked core investigations / remaining work |
|---|---|---|
| `rad.5.ankle-foot` — Ankle Fractures and the Painful Foot | msk curriculum umbrella | `ra.ankle-fractures`, `ra.mri-ankle`, `ra.foot-ankle-cases` |
| `rad.5.marrow-muscle` — Bone Marrow, Stress Injury, Muscle and the Diabetic Foot | msk curriculum umbrella | `ra.mri-diabetic-foot`, `ra.mri-muscle-injury`, `ra.mri-muscle-disease`, `ra.mri-hamstring`, `ra.stress-fractures` |
| `rad.5.bone-tumours` — Bone Tumours: Lytic, Sclerotic and Cartilage | msk curriculum umbrella | `ra.bone-tumours`, `ra.cartilage-tumours` |
| `rad.3.fracture-description` — Describing a Fracture | supplementary msk curriculum | Enumerate each reportable named structure for the selected anatomical region; link the module checklist independently. |
| `rad.5.hip` — Hip: Impingement, Arthroplasty and the Painful Hip | msk curriculum umbrella | `ra.hip-arthroplasty`, `ra.hip-fai` |
| `rad.5.knee` — Knee: Meniscus, Ligament and Cartilage | msk curriculum umbrella | `ra.mri-knee` |
| `rad.5.msk-mri` — Musculoskeletal MRI | supplementary msk curriculum | Enumerate each reportable named structure for the selected anatomical region; link the module checklist independently. |
| `rad.5.shoulder` — Shoulder: Cuff, Labrum and Instability | msk curriculum umbrella | `ra.mri-shoulder`, `ra.ultrasound-shoulder` |
| `rad.4.arthritis` — The Radiographic Pattern of Arthritis | msk curriculum umbrella | `ra.arthritis` |
| `rad.5.wrist-hand` — Wrist and Hand: Carpal Instability and Fractures | msk curriculum umbrella | `ra.wrist-instability`, `ra.wrist-fractures` |
| `rad.5.elbow-mri` — Elbow MRI: Tendons, Ligaments and Nerves | msk curriculum umbrella | `ra.mri-elbow` |
| `ra.cervical-spine-injury` — CT and MRI cervical spine injury | cross specialty spinal msk | Occiput-C1-C2 articulations; Dens; C1 arches and lateral masses; Alar ligaments; Transverse/cruciform ligament; Tectorial membrane; Subaxial vertebrae; Discs and longitudinal ligaments; Cord and nerve roots; Vertebral arteries when vascular injury assessment is acquired |
| `ra.mri-lumbar-disc` — MRI lumbar disc disease | cross specialty spinal msk | Each lumbar disc annulus/nucleus; Endplates; Central canal; Each lateral recess and neural foramen; Named traversing and exiting roots; Facet joints; Ligamentum flavum; Conus and cauda equina; Postoperative anatomy if present |
| `ra.mri-myelopathy` — MRI myelopathy | primarily neuroradiology with msk compression component | Cord tracts and signal localization; Vertebral/disc/ligament compressive structures; Epidural and intradural compartments; Source-specific noncompressive cord causes remain outside a purely skeletal atlas |
| `ra.thoracolumbar-injury` — Thoracolumbar injury imaging | cross specialty duplicate trauma pathway | `ra.thoracolumbar-fractures` |
| `ra.child-abuse-imaging` — Child abuse — diagnostic imaging | paediatric skeletal survey msk component | Each age-appropriate skeletal-survey bone and projection; Metaphyseal corners and growth plates; Anterior and posterior ribs; Skull sutures and fracture mimics; Spine; Pelvis; Hands and feet; Non-skeletal brain/visceral findings require separate specialty inventories |
| `ra.craniosynostosis` — Craniosynostosis imaging | craniofacial skeletal adjacent not appendicular msk | Sagittal suture; Coronal sutures separately; Lambdoid sutures separately; Metopic suture; Fontanelles; Age-specific cranial vault bones; Skull base and syndromic findings when acquired |
| `ra.paediatric-hip` — Paediatric hip imaging | core adjacent paediatric msk | Cartilaginous acetabular roof; Bony acetabular roof; Labrum; Femoral head ossification centre; Unossified femoral head; Proximal femoral physis; Triradiate cartilage; Iliac straight-line landmark; Capsule and effusion; Side-specific dynamic stability |
| `ra.ultrasound-neonatal-spine` — Ultrasound neonatal spine | paediatric neuro with developmental msk landmarks | Unossified posterior vertebral elements; Vertebral level landmarks; Conus; Filum terminale; Cauda equina roots; Thecal sac; Skin tract and subcutaneous lesion if present |
| `rad.4.paediatric` — Imaging the Child | paediatric umbrella | Resolve skeletal-development and trauma pathways; do not treat an adult atlas as paediatric coverage. |
| `rad.5.nuclear-general` — Bone Scan, V/Q, Thyroid and Sentinel Node | nuclear msk component | Whole-skeleton bone-scan localization and acquisition-specific functional evidence; separate non-MSK thyroid/VQ/sentinel-node targets. |
| `rad.5.pet-ct` — FDG PET/CT in Oncology | oncologic msk component | Individual osseous and marrow lesion localization within actual PET/CT coverage; functional uptake is not represented by a normal bone mesh. |

Paediatric DDH and the child’s elbow share a backing curriculum module but require different anatomy and different reporting paths. Child-abuse imaging includes a skeletal-survey component; craniosynostosis is adjacent craniofacial skeletal scope; neonatal spine is primarily developmental neuroimaging with essential skeletal landmarks. Cervical/lumbar spinal pathways are related MSK scope filed under Neuroradiology. General paediatric, nuclear-medicine and PET modules need explicitly bounded skeletal components, not a claim that this joint inventory covers their whole subject.

## Verification and remaining review

The 22 investigation IDs were compared with the effective `radiology_catalog.detail()` output. Every structure links to valid current checklist indices with matching label/detail text, and each required subpart has its own stable ID. The paediatric correction was checked through the effective catalogue and generated report template, not only the authored JSON. The catalogue sources not individually reviewed are labelled accordingly in the JSON.

This specification is ready to drive a conservative asset gap audit. Before clinical/commercial acceptance, an MSK radiologist must review the anatomical decompositions, resolve region-dependent scope, inspect each representation at the required granularity and modality, and record approval against the exact version. Rights and commercial reuse must be verified independently. This audit makes no claim that any current image, schematic or model has passed those requirements.
