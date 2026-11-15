# Report template upgrade (2026-11-15)

All 333 report templates were reviewed against four aims: information density, a structured search pattern, rapid reporting, and readability. `tools/authoring/report_upgrade_20261115.py` applies the changes, and `tests/test_report_style.py` enforces the rules.

## Layout

Every study has Clinical history, Comparison, the study name, findings under anatomical headings, Impression and Recommendation.

- **MRI** opens with `Protocol:` and then `Findings:`.
- **CT** opens with `Technique:` and then `Findings:`.
- **Radiographs, ultrasound, fluoroscopy and all other studies** have neither.

## Protocols and techniques

All 176 MRI and CT studies now state their own acquisition. Before this pass, 39 had none, and many others were generic ("through the prescribed abdominal or pelvic coverage") or omitted contrast on contrast studies.

- **MRI:** planes and weightings, with gadolinium named wherever the title says "with contrast".
- **CT:** contrast phases with timing, coverage and reformats.

Sources, in order of preference:

1. **Radiology Assistant.** The CT phase names and timings come from "CT contrast injection and protocols": late arterial 35 s, portal venous 70 s, nephrographic 100 s. Protocol notes in these topic articles were also used: rectal cancer, PI-RADS, VI-RADS, LI-RADS, solid renal masses, acute aortic syndrome, CT in trauma, dementia, epilepsy, multiple sclerosis, sella, elbow MRI, pulmonary emboli.
2. **Radiopaedia.** It could not be read from the build environment: it refuses automated access (HTTP 402/406). Sequences that the Radiology Assistant does not list follow standard practice and still need checking against Radiopaedia by a radiologist.

The knee MRI protocol is unchanged.

The click builder's selectable acquisition choices are unchanged. Its default text can differ in wording from the protocol line in the template.

## Content rules

| Rule | Before | After |
|---|---|---|
| The normal line does not repeat its heading | `Spleen: Normal spleen.` (163 lines) | `Spleen: Normal.` |
| No generic "Other findings" | 84 templates | The last heading names the review areas, e.g. `Other organs, lung bases and bones` |
| A finding line starts with the finding | `[ ] mm calculus in the …` (206 lines) | `Calculus [ ] mm in the …` |
| Lines stay scannable | Up to 250 characters, five picks | At most 145 characters, three picks, six choices per pick (coded scales excepted) |
| Limb trauma radiographs open with Bones | `Fracture:` | `Bones:` |

The RadProof export (`tools/authoring/radproof_export.py`) prints findings without headings. A normal line that relies on its heading is therefore exported with it, for example `Spleen: normal.`. The export prints Protocol or Technique only for MRI and CT.

## Layout and rich text

The layout follows the practice's dictation note.

| Element | Format |
|---|---|
| Font | Arial 12 pt in the formatted copy |
| Main headings: Clinical history, Comparison, study name, Protocol or Technique, Findings, Impression, Recommendation | Underlined, not bold |
| Anatomical subheadings | Italic |
| Findings | One sentence per line, each with a bullet |
| Dictation fields | `[]`, with no spaces inside, so the dictation system skips from field to field |
| Impression and Recommendation | Numbered `1.` to `3.` |

The study name runs straight into Protocol or Technique, and Findings runs straight into the first subheading. One blank line separates the other blocks.

Copy text puts both rich text and plain text on the clipboard. The plain text has the same lines without the underline and italics.

The report draft in the click checklist shows the same formatting as the copied text: Arial 12 pt, underlined main headings that are not bold, and italic subheadings. The Report template tab is a rich-text editor. It shows the template as it is copied and has Bold, Italic and Underline controls; the usual keyboard shortcuts also work. Copy text puts the formatting shown on the clipboard, with a plain-text alternative. Pasted and dropped content arrives as plain text. Download .txt saves the text without formatting.

## Checklist normals

In the click checklist, a structure marked Normal now reads as its label, not as a sentence.

| Case | Before | After |
|---|---|---|
| A structure | `The supraspinatus tendon is intact without tendinosis.` | `Supraspinatus tendon: normal.` |
| A heading that names a finding | `No fracture.` | `Fracture: none.` |
| A label used twice in one study | `The medial meniscus anterior horn has no tear.` | `Medial meniscus, anterior horn: normal.` |
| A label shared by a tendon and its muscle | `The supraspinatus muscle has normal bulk.` | `Supraspinatus muscle: normal.` |

This applies to all 5,676 normal statements in the 333 checklists. Of the distinct headings, 122 name a finding and read "none".

The pertinent negatives in the old sentences (for example "without tendinosis") no longer appear in the report. The grouped knee summaries ("No tear of the medial meniscal anterior horn, body or posterior horn.") are replaced by one line per structure.

The browser and the server apply the same rule (`normalLine` in `web/radiology-structured.js`, `normal_line` in `primer/descriptor_reporting.py`). Both files are pinned; the exact inverse is in `tools/report_layout_compatibility.py`.

These are educational drafting templates. Check each report against the images before use.
