
## Simple report sheet (23 October 2026)

Primer and this API are the maintained reporting surfaces. The separate Template Review Suite has been retired. Both use the same single-page renderer: visible anatomical section headings, compact label/control rows, conditional fields, measurements, and a live report preview. Manual TI-RADS point-entry and CAD-RADS category rows are replaced by their calculators in this view; the original fields remain available in the data contract. Review acknowledgements and repeated source prompts are kept in the data contract instead of occupying the main report sheet. Calculator inputs remain on the same page; calculated assessments still need explicit inclusion.

Layout reference: [ICRI MSK MRI reporting formats](https://icri.iria.org.in/wp-content/uploads/2022/03/MSK_MRI_REPORTING_FORMATS.pdf), especially the shoulder and knee checklists. This informed grouping and scanability, not new clinical thresholds.

The supplied enhanced-package JSON uses path-keyed tree nodes, `ui.displayName`, `selectionChange.canOnlyHaveOneActiveChild`, and `textProduction.formattedText.fragments`. These correspond to field labels, single-choice/multiple-choice controls and report wording. Required-child/default-selection flags are not treated as observed normal findings. The external package is a format example, not executable instructions or an automatic clinical-content replacement. Existing stable field IDs, options, source text and API/MCP operations are retained. The structured-form response advertises `presentation.layout = "single_page"`.
