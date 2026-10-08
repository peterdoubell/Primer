# Esophageal reporting and complete source anatomy draft

Reviewed 2026-10-08. Investigation `ra.esophagus` shares lesson
`rad.5.esophagus-swallowing` with the separately scoped swallowing reader. This
draft changes the esophageal reader only when the builder is explicitly run.
Importing the script or calling `build_draft()` does not change shared data.

The draft has **139 independently instantiated groups, 834 required parts and
2,502 image/schematic/model obligations**, including 12 groups that require actual
temporal evidence. This is a known floor, not evidence that these representations
exist or a closed list of every possible patient's anatomy. Five original normal
presets are removed on application. Existing media receive no new anatomical,
clinical or commercial-grade approval.

## Source evidence and resulting distinctions

The two [original Radiology Assistant esophagus sources](https://radiologyassistant.nl/chest/esophagus/esophagus-i-anatomy-rings-inflammation)
and [second source](https://radiologyassistant.nl/chest/esophagus/esophagus-ii-strictures-acute-syndromes-neoplasms-and-vascular-impressions)
define the effective reader's topics: anatomy, lumen/surface disease, narrowings,
pouches, masses, acute wall injury, external vessels and hiatal relationships.
They date from 2007. Their old diagnostic vocabulary and illustrative patterns
are not a current universal diagnosis, physiological classification or clinical
action. No source graphics, tables, captions or cine are repackaged.

The [ACG physiological testing guideline](https://pmc.ncbi.nlm.nih.gov/articles/PMC9468980/)
distinguishes bolus transit from measured pressure/distensibility and clinical
diagnosis. The draft records actual bolus, position, ingestion/time zero,
calibration and acquired times. It does not impose published retention thresholds
on another protocol. HRM/HRIM, FLIP and reflux-monitoring results remain separate,
identified evidence. These distinctions do not prescribe all tests to all patients.

The [ACG adult achalasia guideline](https://pmc.ncbi.nlm.nih.gov/articles/PMC9896940/)
describes complementary roles of esophagram, endoscopy and manometry, including
assessment for obstructing processes. Accordingly, distal tapering or retained
contents alone do not provide subtype, exclude pseudoachalasia, determine cause
or justify an intervention.

The [original Chicago v4.0 consensus](https://pmc.ncbi.nlm.nih.gov/articles/PMC8034247/)
applies within stated anatomical and manometry-protocol limits. It assumes normal
foregut anatomy without prior invasive foregut intervention or large/paraesophageal
hernias; mechanical obstruction and clinical/supportive evidence matter. The
reader therefore does not classify a static tube, postoperative course or one
fluoroscopic image as a pressure-defined disorder. Historical terms in reading
material remain source vocabulary rather than automatic current classifications.

The [ACG GERD guideline](https://pmc.ncbi.nlm.nih.gov/articles/PMC8754510/)
does not support barium swallow alone as a GERD diagnostic test. Observed reflux,
its acquired extent and hiatal geometry are reported without assigning GERD or
symptom causation from those findings alone.

The [updated ACG Barrett guideline](https://pmc.ncbi.nlm.nih.gov/articles/PMC10259184/)
uses endoscopic landmarks and tissue evidence within its applicable diagnostic
framework. Other professional definitions differ. A radiographic reticular
surface, web, ulcer or CT thickening is not supplied as intestinal metaplasia,
dysplasia, histology or a mandatory surveillance/treatment pathway.

The [original WSES emergency guideline](https://pmc.ncbi.nlm.nih.gov/articles/PMC6544956/)
supports assessment of wall injury and acquired spread by appropriate imaging,
with clinical stability and context determining management. A limited negative
contrast examination cannot exclude every perforation. The draft inventories
actual wall defects, intramural tracts and every leak/fistula/collection connection;
it does not prescribe one contrast type, force a typical injury side, infer a
unique cause from gas/fluid, or promise successful conservative treatment.

The [ESSD–ESGAR adult VFSS consensus](https://pmc.ncbi.nlm.nih.gov/articles/PMC12081525/)
states that esophageal screening is limited and does not replace a complete
dedicated esophagram. Preserved recorded frames, bolus/trial context and actual
temporal coverage are needed for passage observations. One still or static model
does not certify clearance, sphincter function, aspiration exclusion or future
safety. Adult guidance is not automatically a pediatric protocol.

The [paraesophageal surgical anatomy source](https://pmc.ncbi.nlm.nih.gov/articles/PMC7263794/),
[esophageal surgical anatomy review](https://pmc.ncbi.nlm.nih.gov/articles/PMC5538986/)
and [microscopic anatomy review](https://pubmed.ncbi.nlm.nih.gov/29761508/)
support maintaining actual segmental walls, layer/gland/duct, branching routes,
external tissues and hiatal attachments as requirements. Neither a source review
nor acquisition permission proves that current CT/MRI resolves tiny or
microscopic structures. These remain required and unproven pending matched
source anatomy and independent review. The surgical review's third-party figure
credit is not treated as a new graphics grant.

Review limits: the microscopic anatomy citation was reviewed through its primary
PubMed abstract only; its full text was not obtained. The PMC5538986 surgical
review was available as a primary-source search excerpt containing its general
anatomy section, but full-text retrieval failed. Neither is recorded as a complete
full-text review. Full original text for the other PMC sources was obtained
through NCBI BioC; review concentrated on the relevant technical, diagnostic and
anatomy sections. Source transport success is not independent clinical validation.

## Scope preserved

Each cervical, upper/middle/lower thoracic and abdominal segment requires separate
actual lumen/content, mucosal surface, lamina propria/muscularis mucosae,
submucosa/glands/ducts, circular/longitudinal muscle, adventitial interfaces,
neural/vascular/lymphatic plexuses, and every actual lesion/variant/repair component.
The abdominal peritoneal/serosal interfaces remain separate; no continuous serosa
is invented along the entire organ.

Source-resolved adjacent tissues, bilateral branches and nodes remain explicit.
Every actual nerve/vessel/lymphatic branch, variant arch/pulmonary route, venous
connection, node and source component requires its own instantiation. Named nodal
groups do not assign clinical stage, and a nodal outline is not a cortex, hilum,
capsule or every internal component.

Each lesion, ring/web/bar, narrowing, pouch/neck/reentry route, duplicated route,
gland/duct pseudodiverticular interface, stalk, wall injury, fistula and collection
requires its actual source site and connections. Diaphragm/crura, EGJ, cardia,
gastric folds, herniated contents, sac/neck, attachments and rotation are retained.
All acquired anastomosis/conduit, myotomy/fundoplication and device interfaces are
included. A generic parent shape cannot fulfill internal tissue or lesion parts.

Events require actual recorded times and bolus/source identity. Separately
supplied endoscopy/EUS, pathology, HRM/HRIM, FLIP, pH/impedance and clinical data
must not be invented from a surface. Independently reviewed source geometry,
high-resolution anatomical reference, matching clinical examples, and clinical
validation remain outstanding across this entire scope.

## Application and verification

From the release clone, explicitly apply:

```sh
/Users/peter/Documents/ChatGPT/Primer/.venv/bin/python tools/anatomy_sources/expand_esophagus_requirements.py
```

The command updates only this investigation in the overrides, chest walkthrough
and non-MSK requirements stores and then binds its actual effective source contract.
It does not alter the swallowing reader, approve assets or remove source images.
The parent release must separately review any inherited image bindings and the
shared lesson's model/media.

```sh
/Users/peter/Documents/ChatGPT/Primer/.venv/bin/python -m pytest tests/test_esophagus_requirement_scope.py -q
```

Before application, four pure-draft tests pass and the effective-reader binding
test is intentionally skipped. After application, the binding test must execute
and pass. Full release tests and the global incomplete-fidelity gate remain the
parent task's responsibility. No global builder was executed during delegated
source review.
