# Fast report templates and normal reports (2026-11-12)

Every radiology examination served at `/api/radiology/modules` now has a fast report template and a normal report. That is 225 examinations: 136 base guides, 75 reporting-only variants and 14 worksheets. Both texts use the paste-ready layout of the reader's Prism chest radiograph template:

```
Clinical history:
[ ].

<study title, alternatives separated by " / ">
<Heading>:
<normal finding>
<selectable finding with [a / b] picks and [ ] blanks>

Impression:
1. []
2. []
3. []

Recommendation:
[ ].
```

- **Fast template.** Under each sentence-case heading, the first line is the normal finding. The lines after it are the common abnormal findings. `[a / b]` is a pick and `[ ]` is a blank, used only where an explanation is needed.
- **Normal report.** Each heading carries only its normal line, followed by a numbered normal impression. The recommendation is `None.` unless a screening pathway applies. Only the clinical history is left to fill in.
- **Radiographs.** Radiographs (plain films, mammography and skeletal survey) have no Technique or Comparison heading. Every other examination opens with `Technique:` (a default protocol, its alternatives and `Limited by [ ].`) and then `Comparison:` (`None.` or `Compared with [ ].`).

## Where it lives

- `data/radiology/report-templates/*.json` is the authored library (`primer.fast-report-templates/1`), grouped by specialty.
- `primer/report_templates.py` validates the library and renders both texts. It refuses nested or single-choice brackets, normal lines that contain picks, all-caps or reserved headings, and a technique on a radiograph.
- `/api/radiology/modules/{id}` adds `radiology_reference.quick_report` (`template`, `normal`, `headings`, `title` and `radiograph`).
- The Report template tab shows "Fast template" and "Normal report" as editable panels, each with Copy text, Download .txt and Reset edits. They replace the older long text templates and sit above the click builder. Reporting-only pages show them above the builder too.

## Compatibility

`web/app.js` and `primer/server.py` are pinned by earlier proofs. `tools/fast_report_templates_compatibility.py` removes only these literal additions, from the exact new bytes. It runs at the head of `before_source_studies_bytes`, so every historical check still recovers its reviewed fingerprint.

## Known limit

The Step by step walkthrough still assembles its draft from the older long template. "Edit freely in Report template" places that draft in the Fast template editor, and Reset edits restores the fast template.

These templates are educational drafting aids. Check every report against the images before use.
