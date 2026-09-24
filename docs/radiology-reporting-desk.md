# Radiology reporting desk

Updated 23 September 2026. Open `#/radiology` for the searchable professional
reference index, or `#/radiology/<module-id>` for a specific examination. The
sidebar and radiology lesson pages link directly to this workspace. Reference
access does not award mastery or require a quiz pass.

All **96 modules** now have:

- A protocol/quality guide and an examination-specific reporting checklist.
- Measurement methods and pitfalls where relevant, plus scoped classification
  notes, impression prompts and appropriate direct-communication findings.
- A complete reporting template with named finding fields and editable prompts.
- An attributed image gallery, an original rendered diagram and an interactive
  3D anatomy or acquisition companion.

The coverage audit records **480 checklist items, 211 measurement references,
492 authored finding sections, 96 templates, 298 image slots and 96 local
reporting diagrams**. The 96 3D companions use **35 distinct geometry families**,
with module-specific landmarks and reporting aims. The earlier measurement
activities remain available as additional exercises in the relevant modules.

Five concise classification tables cover CAD-RADS 2.0, PI-RADS v2.1, adult ACR
TI-RADS size prompts, Bosniak 2019 structural features and RECIST 1.1 response
anchors. Each identifies its scope and links to the professional source. They
are reference tables, not automated clinical scoring or management engines.
The prostate source links were repaired to ACR's current document host.

## Using the workspace

Search by examination, finding or classification and filter by specialty. Each
module has six tabs: Reporting guide, Report template, Images, Diagram,
3D anatomy and Sources. Keyboard users can move between tabs with arrow keys,
Home and End. Reference requests use a dedicated endpoint without live
Wikipedia summary fetching.

Checklist marks, report edits, selected tabs and 3D camera settings remain in
memory while moving between tabs or changing the reading theme. They are not
sent to the server or written into browser storage. Copy or download a report
before leaving the module or reloading. A generation check prevents delayed
responses from replacing a more recently selected route.

Images are independent published teaching examples, with the actual view
identified in each caption. They are not one patient study, and report image
references remain blank for the user's examination. Source-hosted images need
an internet connection; the guides, original diagrams and 3D geometry are
local. The models are deliberately schematic and do not generate diagnostic
slices, patient measurements or classifications.

## Review and maintenance

`reporting-body.json` and `reporting-neuro-msk.json` hold the authored reporting
content. `classification-tables.json` holds the five scoped reference tables.
`reporting-models.json` and `web/radiology-reference-models.js` bind all modules
to their 3D companions. Runtime validation rejects missing modules, incomplete
content and mismatched models. Rebuilding ordinary guide data does not erase
these reporting overlays or the image catalogs.

Content was reviewed against Radiology Assistant and the professional sources
recorded per module. Mixed examination pathways remain explicit: for example,
rectal staging/restaging/fistula work, paediatric masses/neurosonography and
nuclear study types are not assigned one catch-all classification. A dated
source review is not external clinical peer review; update named versions and
local protocols when maintaining the reference.

Validation commands:

```sh
.venv/bin/python tools/audit_radiology_reporting.py
node tools/check_radiology_reference_models.js
node tools/check_radiology_reporting_navigation.js
PRIMER_DB=/tmp/primer-reporting-test.db .venv/bin/python -m pytest tests/test_radiology_reporting_desk.py tests/test_radiology_reference.py tests/test_radiology_key_images.py -q
```

The machine-readable per-module inventory is
[`radiology-reporting-audit.json`](radiology-reporting-audit.json). The model
checker exercises 480 controls and 2,701 deterministic finite scene builds.
All 35 model families were visually reviewed. Live CCTA/prostate verification
covered desktop/mobile rendering, keyboard controls, reset, tab navigation,
report/checklist preservation, theme changes and narrow-screen containment.

Final focused regression run: **633 passed, 1 skipped**. JavaScript syntax,
route-race checks and the per-module coverage audit pass. The existing Python
3.9/Google-auth deprecation warnings are unrelated to these changes.
