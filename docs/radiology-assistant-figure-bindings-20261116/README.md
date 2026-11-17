# Radiology Assistant figures: stored and bound

Date: 2026-11-16. Status: source-reviewed, **not clinically approved**. No radiologist has reviewed these bindings.

## Why

The project owner directed that Radiology Assistant figures be stored and bound to reportable structures. The
tool is for personal use at this stage, and commercial rights are not being sought yet.

## Licence

The publisher's disclaimer permits reproduction "for educational purposes with due credit being given to the
original author and the Radiology Assistant" (`publisher-reuse-terms.txt`). This is not a commercial licence.
Every asset records `commercial_use: false`, so each keeps the checker's `commercial_rights_unverified` issue and
cannot be rated clinical or commercial grade. A commercial release needs the publisher's written permission or
replacement images.

Each asset credits the article's authors, the article title, the Radiology Assistant and the article address.

## How figures were chosen

1. Candidates were article sections whose heading is the structure's name and which carry a figure: 82 figures.
2. Each figure was looked at, at reduced size. A figure was accepted only if it plainly shows the named structure
   in one modality, or is a drawing of it. Tables, key-point slides, photographs, composites that mix modalities and
   unclear figures were rejected. 35 figures were accepted; `review.json` lists what was seen in each and the
   47 rejected figures.
3. A binding was kept only if the fidelity checker found no conflict: the figure's modality must be one on which
   that report describes the structure, and sided requirements were left unbound because the figures do not
   state a side.

Result: 33 stored figures and 34 bindings across 13 investigations. Bound requirements rise from 160 to 188
of 57,985. Every binding is recorded as partial coverage.

## Limits

- The review was done by the packaging author from the figure and its section heading, not by a radiologist.
- Many accepted figures are teaching cases that show pathology of the structure, not normal anatomy. Their
  recorded state is `published_case_example`.
- One figure per structure does not show its full extent.
- `inverse.json` records the exact bytes added to `data/radiology/radiology-asset-evidence.json`.
  Rebuild with `python tools/anatomy_sources/package_radiology_assistant_figures.py` from the pre-binding file.

## Second pass (2026-11-17)

The first pass used only sections whose heading is the structure's name. The second pass widened the search to
sections whose heading or text names an unbound structure that has no stated side.

- 219 further figures were looked at. 50 were accepted, each only for the structures it labels or plainly marks.
- Three accepted rows came from an article page that names no author. They were dropped, because the publisher's
  terms require credit to the original author.
- Bindings whose figure is in a modality the report does not use for that structure were dropped by the checker,
  as before.
- Some structure ids are shared by several investigations. A figure is now bound only if it suits every investigation
  that lists the structure, so a CT figure is not bound to a structure that another report describes on ultrasound.

Totals after both passes: 77 stored figures and 90 bindings, touching 36 investigations. Bound requirements stand at
240 of 57,985, and 92 investigations still have none.

The same limits apply. The review was by the packaging author at reduced size, not by a radiologist; every binding
is partial; many figures are teaching cases that show pathology. Sided requirements remain unbound because the
figures do not state a side.

Update 2026-11-17: the side rule has since been relaxed (see
`docs/stored-asset-caption-bindings-pass2-20261117/README.md`). The Radiology Assistant sections
that name sided structures have not yet been reviewed under the new rule.
