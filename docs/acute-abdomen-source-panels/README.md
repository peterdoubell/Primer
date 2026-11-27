# Acute-abdomen source panels and report targets

The general acute-abdomen reference already preserved twelve licensed ultrasound, CT and MRI figures. Their local observations were not reachable by a particular report row or required anatomy leaf. This change keeps those source files and clinical statements intact and adds a reader that selects the original panel for a reviewed target.

The inventory remains **102 parent structures and 724 required leaves** (826 recorded structures/parts). The source map records **39 partial image-to-leaf bindings across the twelve figures**, plus **two partial native-vessel model candidates**, for **23 distinct leaves**. No requirement becomes clinically complete. Anatomical review remains pending; no source is promoted to high fidelity or clinical approval.

## What the reader depicts

| Preserved source | Panels and limited correspondence |
| --- | --- |
| Mostbeck 2016, Figures 1–3 | Normal local appendiceal extent/lumen; source-labelled appendiceal wall change and original caliper sites; adjacent fluid and CT fat/wall changes. Figure 3 ultrasound a stays contextual; only its separately registered CT b receives bindings. Muscle-star correspondence in Figure 1 stays unresolved. |
| Fernandes, PMC3999365 Figures 6 and 9 | Captioned sigmoid wall/pericolonic fat change, fluid-filled retrocaecal appendix and reactive ascending-colon wall change. The original CC BY 2.0 grant is preserved. |
| Ramos-Andrade, PMC4729712 Figures 2 and 7 | Selected beak-shaped transition locations, author-described reduced enhancement, incisional-hernia contents/neck and a local mesenteric interface. The isolated whirl panel remains contextual. Neither complete loop connectivity nor viability is granted. |
| Sureka 2015, Figure 1 | The specifically captioned pancreatic-tail tissue and local peripancreatic change. Other pancreatic regions, duct anatomy and necrosis classification remain unrepresented. |
| PMC12181115 Figure 1 | Captioned gallbladder lumen/sludge and abnormal wall region. No separate histological wall layer, shadowing stone, tenderness or dynamic finding is inferred. |
| PMC12017295 Figure 1 | The initial source ultrasound's reported CBD calculus and local duct/lumen region; the original marker/calipers do not establish independent calibration or the complete clinical episode. |
| PMC12463306 Figures 1 and 3 | Separate T2 MRI and MRCP views from the same published case. Filling defects and abnormal duct/lumen regions are matched; the original “suggestive” calculus wording is retained without a definitive MRI calculus binding or a complete duct volume. |

All seventeen published panel rectangles retain access to the complete original figure and full source caption. The rectangles identify the publication's panel layout, not anatomical tissue boundaries. Magnification displays the same supplied pixels. The reader verifies each image's recorded bytes and dimensions before display. The twelve figures are separate cases unless the original caption explicitly establishes correspondence.

The two native entries open the existing **ColonVessels pat_012** readers at arterial `3:1` (SMA) and venous `1:11` (SMV). Their source-labelled, surgeon-delineated opacified lumen meshes are reused without geometry changes. They are partial examples of the mesenteric-vessel lumen leaves, not a complete branch/tributary tree, vessel wall, occlusion or bowel viability. This is a separate CT case, with no registration to the published figure patients. Original model records and other investigations' bindings remain unchanged; the two new candidate records retain their original source, licence, context and geometry provenance.

The native readers open in their own tabs under their existing framing policy. This change does not relax that policy or modify their CT decoding, mesh rendering or anatomy controls.

## Entry points

- Nine exact professional report rows have source links: pancreas, gallbladder lumen/wall, common bile duct, ascending colon, sigmoid colon, appendix, periappendiceal fat and periappendiceal fluid/gas. Each row is fingerprinted against its original label, normal statement and finding definitions. The source scope is narrower than the report row where necessary: pancreatic tail only, free fluid without a collection/perforation claim, and sludge without a shadowing-stone claim.
- Row links restrict the initial reader selection to that row's reviewed panels. Unspecified small-bowel loops do not become jejunum or ileum examples.
- The existing bowel/appendix, solid-organ and peritoneal/vascular walkthrough steps link their particular targets. The twelve preserved gallery figures also open their own source panels; mixed Figure 3 defaults to CT panel b.
- The structure locator keeps every original structure, identifier and external-source entry. Ten parent rows gain links to the particular matched leaves. Searching a part name such as lumen can reach its local source examples.

Links open separately from the report. Source selection does not insert findings or measurements into the patient's report. Report wording, presets, acquisition rules, stored edits and original source metadata are unchanged.

## Evidence and reproduction

[review.json](review.json) records the caption evidence, original panel bounds, exact targets, qualifications, declined claims and original report-row fingerprints. The generator validates the bounded acute-abdomen investigation definition, source modality/context and immutable image/mesh bytes. The original whole-inventory hash is retained as provenance without coupling this module to unrelated future inventory edits.

```sh
python tools/anatomy_sources/build_acute_abdomen_source_panels.py
python -m pytest -q tests/test_acute_abdomen_source_panels.py
```

Generation is byte-idempotent. It changes only the twelve acute-abdomen assets' binding fields, appends two explicitly separate source-model candidates, and generates the map and locator links. It creates no image or geometry file and changes no source pixels, source caption, licence version or existing model record.

[inverse.json](inverse.json) records exact reversible changes to the evidence ledger, report UI and locator files against main `0f620a581e5aa4306df58965a77eb8a8c52b5e3b`. Historical receipts are evaluated only after this newer recorded delta is removed. Unknown edits remain untouched and continue to fail their own guards. The biliary partition and common-hepatic-duct binding from #319/#320 are retained.
