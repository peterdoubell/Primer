# Keep the working report and its authored spacing

The live 335-investigation cohort was checked against the practice’s approved
[report format](../report-template-upgrade-20261115.md). `audit.json` records
the measured scope: 1,005 quick-report variants, both compiler paths for all
335 investigations, and the 36 investigations with named staging systems.

Three real workflow defects were corrected:

1. Multiline plain-text paste used `insertText`. Chromium built paragraph
   blocks that expanded an authored blank line into two blank lines, breaking
   the compact report layout. Multiline input now inserts escaped plain text
   separated by explicit line breaks. Single-line input retains `insertText`.
   The browser’s native one-operation undo/redo remains available. HTML from
   the clipboard is ignored; CRLF/CR becomes LF, while words, punctuation,
   measurements, significant trailing zeroes and internal paragraph spacing stay.
2. **Add staging prompts to report** always selected the first dictation
   editor. A clinician editing Fast template or Normal report received the
   named standard in another draft. The workspace now remembers the last-used
   draft and appends to that editor, opening its own panel. Its existing DOM
   and the other drafts remain intact. With no prior interaction, the first
   dictation draft remains the destination.
3. Inline labels before a blank followed immediately by punctuation, such as
   `Extent: [].`, missed the shared label formatter. The label is now italic;
   the blank, punctuation and following value remain normal. The shared rich
   preview and clipboard formatter use the same rule.

All 335 initial structured reports remain empty until the reader supplies
observations or report fields. Supplied clinical history, comparison,
impression and recommendations retain their text in the JavaScript preview
and Python compiler. Existing acquisition wording and confirmation profiles
retain their approved behaviour. The 21 multimodality/reference worksheets
without a builder acquisition profile are not assigned CT/MRI facts from the
separate quick-template title. No stage or diagnosis is selected by these fixes.

The format and workflow follow the practice’s existing instructions. General
professional guidance also calls for relevant clinical details, an account of
the examination actually performed, relevant comparisons, findings and a useful
conclusion: [RCR reporting standards, third edition](https://www.rcr.ac.uk/our-services/all-our-publications/clinical-radiology-publications/standards-for-interpretation-and-reporting-of-imaging-investigations-third-edition/)
and [ESR good-practice guidance](https://pmc.ncbi.nlm.nih.gov/articles/PMC3259387/).
These references support accurate communication; no clinical recommendation
or staging criterion is changed in this pass.

The CAP study’s sources, anatomical models and bindings are outside this
change. CAP reports use the common editor fixes like other reports. All
clinical data and historical inventories remain unchanged. The two exact
runtime projections are in `runtime-inverse.json`; foreign edits are not
projected. The new layer precedes the older report-layout and salivary layers.
When combining this change with another app/formatter change, regenerate its
two before/after rows against the resulting parent tree before older inverses.

Checks:

```sh
python -m pytest tests/test_report_working_draft.py tests/test_fast_report_templates.py tests/test_report_style.py tests/test_descriptor_reporting.py tests/test_confirmed_acquisition_conflicts.py -q
node tests/report-working-draft.test.cjs
```

The real Chromium check requires the existing Playwright setup. Set
`CHROMIUM_PATH` if its installed browser executable is outside Playwright’s
default cache. It exercises paste, native undo/redo, escaped clipboard text,
working-draft routing, unaffected other drafts and both clipboard formats at
1440 and 390 pixels. Separate real application checks exercised all 36
staging-enabled reporting routes at both widths, including plain paste and
preserved measurement precision in the edited report.
