# Diabetic-foot forefoot scope audit — 26 September 2026

The initial [proposed JSON](msk-diabetic-foot-forefoot-requirements-proposal.json) records source anchors, the exact checklist/template snapshot, nine candidate anatomy groups, 44 component requirements, 14 MTP/IP joint-site pairs and five expansion rules. After an independent source review, these additions were integrated as **conditional, unapproved draft requirements** with the two wording refinements below. The reporting guide and clinical approval status remain unchanged. Components still need side/site instantiation; 44 is not a coverage claim.

The inspected `ra.mri-diabetic-foot` guide asks for ulcer-to-bone/joint routes, named marrow involvement, affected joints, collections/viability, and tendon/sheath/muscle/fascial spread. Its template follows those fields. I found no reason to replace this infection-focused guide with a plantar-plate injury template. The linked [Radiology Assistant chapter](https://radiologyassistant.nl/musculoskeletal/diabetic-foot/mri-examination) supports site-directed foot coverage and tracing contiguous spread. [IWGDF/IDSA recommendation 8](https://www.idsociety.org/practice-guideline/diabetic-foot-infections/) supports MRI when suspected osteomyelitis remains uncertain and notes diagnostic limitations; it does not mandate a universal ligament-tear assessment.

## What is already present

The current inventory contains **48 structures and 203 component leaves**. It already names all five metatarsals, the appropriate toe phalanges, both hallux sesamoids, five MTP joints, nine IP joints, and hindfoot/midfoot joints. These structures are not missing and must remain. Cartilage/subchondral surfaces, capsules/synovium, intrinsic muscles and neurovascular members are retained as broad groups requiring further site detail. The existing expansion rule correctly demands instantiation, but its `named_sites_or_targets` list is empty.

## Proposed additive clarification

| Existing report field | Candidate anatomy or site detail |
|---|---|
| Ulcer/tract and affected joints | Lesser MTP plates at digits 2–5; each plate's substance, margins and attachments; separate hallux plantar capsulosesamoid anatomy |
| Bone/joint involvement | Medial and lateral metatarsosesamoid articulations; explicit opposing surfaces for the existing 14 MTP/IP sites |
| Joint/collection extent | Hallux and lesser-MTP collateral structures; named intermetatarsal bursa/site when present and involved |
| Tendon/sheath and deep spread | Digit-specific flexor sheaths, FDB tendon slips and hallux intrinsic tendon insertions; actual tendon, sheath and segment must be distinguished |

The [48-joint cadaveric MRI study](https://pubmed.ncbi.nlm.nih.gov/12668744/) supports separating the lesser plate, capsule, collateral complex and attachments; its arthrographic visibility cannot simply be claimed for routine MRI. The proposed lesser-plate leaves and interspace rules use that distinction, not the mere presence of a generic forefoot picture.

The hallux needs source-specific terminology. [Hallinan et al.](https://pubs.rsna.org/doi/10.1148/rg.2020190145) describe a complex involving the sesamoids and surrounding tissues, with paired metatarsosesamoid articulations. [Wang et al.](https://link.springer.com/article/10.1186/s13018-021-02795-7) distinguish a central plantar portion and explain its continuity with adjacent ligaments using MRI and histology. The proposal preserves that difference. It does not declare a histological boundary independently visible on every MRI sequence. [The earlier hallux cadaveric study](https://pubmed.ncbi.nlm.nih.gov/12439324/) also supports separately identifying cartilage and named tendon attachments.

The eight existing tendon records all use the component suffix `sheath_or_achilles_paratenon`. That generic wording needs segment-specific reconciliation, not deletion of the underlying requirement. Digital flexor anatomy must be named by toe; a generic ankle tendon sheath cannot stand for every distal segment. The [diabetic-foot surgical/MRI study](https://pmc.ncbi.nlm.nih.gov/articles/PMC5583782/) supports attention to tendon involvement, while [EANM guidance](https://doi.org/10.1007/s00259-024-06693-y) cautions that forefoot infection can cross compartments. Neither makes a normal anatomical illustration evidence of infection status.

FDB is an additional named tendon target, with its own digit-specific slips. [Cadaveric anatomy](https://www.ijmhr.org/IntJAnatRes/IJAR.2017.298/) supports the attachment distinction; [documented variation](https://pubmed.ncbi.nlm.nih.gov/16333914/) means an absent fifth slip must not be fabricated. “Not present in the mesh” does not establish anatomical absence.

## Scope and acceptance boundaries

Every proposed addition is conditional on acquired coverage and the existing route/joint/collection/tendon question. No blanket instability or tear-screening field is proposed. Side, digit/ray, source-visible portion, attachments, actual field of view and postoperative anatomy must remain explicit. The same reference cannot automatically satisfy all digits or both sides.

The proposal does not finish the named-muscle, neurovascular, compartment, IP-stabilizer or digital-pulley inventories. Those remain unresolved rather than being removed. Normal cadaveric MRI, in-vivo MRI, ultrasound, histology and diagrams remain different kinds of evidence. An ultrasound or histology panel cannot satisfy an MRI-specific leaf, and a model or figure label does not establish clinical fidelity, commercial rights or full anatomical coverage.

The integrated IDs were reconciled with the asset acquisition team. All existing IDs and scope remain, and specialist review of the source definitions is still required before approval. The additions change the requirement fingerprint; they cannot inherit an approval tied to the old scope.

## Integration record

All 48 existing structures and 203 leaves were preserved byte-equivalently as
JSON values. The nine added groups bring the diabetic-foot draft to 57 groups
and 247 leaves. The original generic expansion requirement remains unresolved;
its 14 MTP/IP sites are now named, with five additional route/site rules. The
eight pre-existing generic tendon-sheath labels remain flagged for refinement,
rather than being silently removed or interpreted as complete digital sheaths.

Independent source review supported two clarifications: the hallux plantar
capsular portion is continuous with the capsulosesamoid complex, not a newly
separable tissue layer beside the central plantar portion; and the FDB medial
and lateral slips attach to the corresponding sides of the middle-phalangeal
shaft, not the FDL distal-phalangeal insertion. Stable IDs were retained.

No reporting indication, patient finding, normality claim, image-modality scope,
site-expansion approval or asset-fidelity approval was added by this integration.
