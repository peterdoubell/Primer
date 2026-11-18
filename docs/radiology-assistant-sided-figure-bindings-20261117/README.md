# Radiology Assistant figures for left and right structures (2026-11-17)

The earlier Radiology Assistant passes skipped every left or right requirement. With the side rule
relaxed, the article sections that name an unbound sided structure were reviewed.

- 118 section figures were looked at, each with the sentence that names the structure.
- 39 figures were accepted and stored; they carry 62 partial bindings on 54 structures.
- Bound structures and parts go from 449 to 503 of 57,985; investigations with none from 73 to 67.

A figure is bound to the side its sentence states (20 bindings). Where the sentence states no side
it is bound to each side on the mirror-image assumption (42 bindings), and only for structures that
are mirror images. Unsided lung lobes, heart chambers, renal veins and venae cavae were not bound.

Rejected: tables, flow charts and photographs; composites that mix CT with PET or histology;
sections that name the structure in general while the figure does not mark it; findings; figures
whose modality the requirement does not allow.

The licence is educational only (`docs/radiology-assistant-figure-bindings-20261116/publisher-reuse-terms.txt`),
so every asset keeps the commercial-rights issue. No asset is anatomically approved and no
radiologist has reviewed these.

Files: `review.json` (accepted rows with quote and side, article credits), `inverse.json`, tool
`tools/anatomy_sources/package_radiology_assistant_sided_figures.py`, tests
`tests/test_radiology_assistant_sided_figures.py`.
