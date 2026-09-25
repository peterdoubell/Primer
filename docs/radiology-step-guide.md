# Step-by-step reporting guide

Updated 25 September 2026. Every one of the **137 Radiology Assistant
investigations** in the reporting desk (`#/radiology/<investigation-id>`) now
opens on a **Step by step** tab. It takes the reader through the examination's
own report template in reading order, one section at a time, with the figures,
measurements and 3D landmark for that part of the search pattern alongside.

Coverage: **690 steps** (five to seven per investigation), **1,894 finding
phrases**, **565 normal statements**, **375 reporting tips**, **402 figure
placements**, **243 measurement links** and **199 steps with highlighted
source-mesh structures** across the 40 investigations whose anatomy has a
BodyParts3D region.

## Using it

1. **Before you start.** The introductory fields (indication, comparison,
   technique, key images) and any figures not tied to a later step. *Start from
   normal statements* fills every untouched finding field at once; fields the
   reader has already edited are left alone. *Restore all prompts* returns to
   the blank template.
2. **One step per finding section.** Each step shows what to assess, where to
   look, the normal statement, finding phrases, measurement methods and a tip.
   Choosing a phrase inserts it into the field last used (or the first field of
   the step). An untouched prompt or normal statement is replaced; a written
   finding is kept and the phrase is added on its own line. The first `__` or
   `[prompt]` blank is selected so typing fills it. *Step reviewed* marks the
   step in the stepper.
3. **Impression.** Impression prompts, the scoped classification or criteria
   table where one applies, direct-communication findings with an *Add a
   communication line* helper, and a *Before you sign* list of pitfalls.
4. **Review report.** The assembled report in template order, a list of
   sections that still contain blanks, *Copy report*, *Download .txt* and
   *Edit freely in Report template*, which hands the draft to the free-text
   editor on the Report template tab.

The visual panel beside each step switches between **Figures** (the step's
Radiology Assistant figures), **3D landmarks** (the schematic model focused on
the step's landmark) and, where available, **3D anatomy** (the BodyParts3D
viewer isolating the step's structures, for example the rotator cuff muscles
and humerus for the MRI shoulder cuff step). All controls are keyboard operable;
step changes move focus to the step heading and are announced through a polite
live region. Drafts stay in memory only, like the Report template editor:
nothing is stored, uploaded or generated, and nothing is scored.

## Content and validation

Steps live in `data/radiology/reporting-steps/`, one file per Radiology
Assistant specialty:

```json
{
  "reviewed_at": "2026-09-25",
  "section": "Musculoskeletal",
  "investigations": {
    "ra.mri-shoulder": {
      "steps": [{
        "sections": ["ROTATOR CUFF"],
        "label": "Rotator cuff", "detail": "What to assess.", "look": "Where to look.",
        "normal": "Normal statement for the field.",
        "findings": ["Full-thickness __ tear, __ mm AP × __ mm retraction."],
        "images": ["ra-mri-shoulder-detail-4"], "measurements": ["Cuff tear"],
        "landmark": "cuff", "parts": ["FJ1506"], "tip": "Optional pitfall."
      }]
    }
  }
}
```

`primer/radiology_catalog.py` merges the files and rejects, at load time:

- an unknown investigation, a duplicate entry, or a file under the wrong specialty;
- a step editing a section that is not in that investigation's template, a
  section owned by two steps, or a gap between the first and last step;
- a walkthrough without introductory or impression sections;
- a figure, measurement or mesh part that the investigation does not have, or a
  repeated one;
- a missing "where to look", landmark or finding phrase, more than six
  phrases, a blank tip, or a normal statement for another section (a missing
  label or assessment falls back to the guide's checklist);
- a measurement in the guide that no step uses.

Steps follow the scoped reporting guide's finding sections one to one; the two
flagship templates (CT coronary angiography and prostate MRI) group related
fields, for example dominance with origins and course. An investigation added
later without authored steps still walks through its own template fields, marked
incomplete, and `tools/audit_radiology_investigations.py` fails until it is
authored. `docs/radiology-investigation-audit.json` records steps, model family
and completeness per investigation.

### Corrected 3D companions

An investigation can carry a `model` (`family` and `reporting_aim`) when its
backing learning module shows the wrong anatomy. Ten investigations use this,
for example paediatric elbow fractures (previously the hip model), paediatric
renal tumours (renal tract), diabetic foot (ankle), carotid obstruction and
paediatric neck masses (neck), and vascular anomalies (aorta). Their scenes are
registered on demand by `PrimerRadiologyReferenceModels.ensure`, which returns
`null` for an unknown family or landmark rather than failing the page.

Five mixed guides were also scoped to their examination so the steps match the
source: paediatric elbow fractures, cartilage tumours, thoracolumbar fractures,
thoracic ultrasound and vascular anomalies of the aorta and pulmonary and
systemic vessels.

### Source basis and live recheck

Steps follow each investigation's Radiology Assistant article headings, the
reviewed scoped guide and the figures already selected from those articles.
They were first written from the stored source catalogue
(`data/radiology/source-catalog.json`) and then rechecked against the live site
on 25 September 2026:

- All 189 article pages, all gallery figures and every figure source page
  load, including in the walkthrough through a browser. Four non-Radiology Assistant guide references (doi.org, PubMed, ILAE
  and ESUR) refuse automated requests and were not changed.
- Live article headings match the catalogue for 165 articles; 20 differ only in
  order and 3 gained a site "Charity" banner. No article content was removed.
- Every number with a unit in the steps (101) was compared with its own
  articles. Four steps were corrected to the source: bowel wall thickening
  length bands (under 5, 5–10 and 10–30 cm, or diffuse), miliary nodules of
  2–3 mm, the normal ileal wall example, and the persistent loop in
  necrotising enterocolitis. The remaining values are standard published
  thresholds (for example ACR TI-RADS sizes, Graf angles and CAD-RADS bands).
- The bowel wall thickening steps now use the source's own figures: its length
  and differential table, wall-thickness chart and small-bowel faeces sign.
  Four other figures were moved to the step they illustrate (an iliac stenosis,
  an orbital compartment lesion, neonatal respiratory distress and a radial
  scar).
- One new article, "Thoracic Aorta - How to Measure", was added as the CT
  thoracic aorta measurement reference with its own guide, eight figures and
  six steps. Its normal-value and follow-up tables are shown as figures and not
  transcribed into rules.

This is a source review, not external clinical sign-off. Recheck the content
against the live articles and local protocols when maintaining the reference.

## Validation commands

```sh
PRIMER_DB=/tmp/primer-steps-test.db .venv/bin/python -m pytest tests/test_radiology_walkthrough.py -q
.venv/bin/python tools/audit_radiology_investigations.py > docs/radiology-investigation-audit.json
node tools/check_radiology_reference_models.js
```

`tests/test_radiology_walkthrough.py` checks complete coverage, template order,
guide alignment, landmarks against the shipped model families, mesh parts
against the manifest, corrected models, index step counts, canonical JSON
formatting and each rejection above. It also runs
`tools/check_radiology_walkthrough.js`, which exercises the phrase, blank and
report-assembly helpers and builds every step's 3D focus from the served
specifications.
