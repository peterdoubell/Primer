# Primer-wide image review — 19 September 2026

The review covers all 432 lessons across all eleven subjects. The release branch
is based on the current main revision (a7aa0bd), preserving the recent reporting
reference and learning-flow changes.

## Changes

- Brought 223 improved illustration pairs from the prepared, fingerprint-reviewed
  visual work into the current curriculum. Another seven lessons receive revised
  captions or alternative text: 230 lessons updated across the ten non-radiology
  subjects.
- Retained the original paper palette, typography, diagram language and authored
  opening illustrations. Concrete examples replace text-only layouts where the
  picture makes a mechanism, structure, sequence or relationship visible.
- Added three original radiology comparison plates alongside the existing
  overview images: haemorrhage compartments, lung opacity/vessel visibility, and
  liver enhancement across phases. These are explicitly labelled schematics.
- Updated image auditing, regeneration, contact sheets and review fingerprints to
  support supplementary plates. Every responsive asset is still checked for
  local ownership, unique content, dimensions, accessible copy and size.

| Subject | Updated existing lessons | Final illustrations |
| --- | ---: | ---: |
| Mathematics | 5 | 59 |
| Language & Literature | 38 | 40 |
| Physics | 22 | 39 |
| Life Sciences | 32 | 37 |
| Chemistry | 28 | 29 |
| Computer Science | 32 | 34 |
| History & Civics | 20 | 29 |
| Earth & Space | 25 | 27 |
| Arts & Music | 17 | 25 |
| Mind, Society & Philosophy | 11 | 29 |
| Radiology | 0 | 87 |

Radiology gains three additional images. Total: **435 illustrations**, supplied
as **870 responsive WebPs** at 800×500 and 1600×1000. No new model or learner-data
changes are included.

## Review evidence and limits

All 432 original plates were inspected in subject contact sheets in this pass;
forty old/revised examples were compared side by side. The existing 432 detailed
review records were brought forward only because their lesson, caption and
image fingerprints still match. They retain their original findings and source
links; this does not misrepresent them as newly performed clinical reviews.
The three new companions were separately inspected at 800px, checked against
their drawing sources and referenced clinical descriptions, and given their own
review records. Companion approval cannot inherit the overview's approval.

The new haemorrhage lens was widened to distinguish it from the subdural
crescent. Liver explanatory text was moved inside the bottom frame. The new
plates use comparative drawings rather than fabricated diagnostic scans.

## Sources for the new companion plates

- [Fleischner Society thoracic imaging glossary, 2024](https://pubs.rsna.org/doi/full/10.1148/radiol.232558): ground-glass opacity, consolidation and air bronchograms.
- [ACG focal liver lesion guideline, 2024](https://icus-society.org/wp-content/uploads/2024/10/acg_clinical_guideline__focal_liver_lesions.13.pdf): peripheral nodular enhancement and progressive blood-pool-matched fill-in.
- [Radiology Assistant: traumatic intracranial haemorrhage](https://radiologyassistant.nl/neuroradiology/hemorrhage/traumatic-intracranial-haemorrhage): compartment and shape comparison.

## Verification

Full test suite: **1,744 passed, 3 skipped**. The skips are pre-existing optional
capability checks; the two warnings concern the local Python 3.9 environment.

- All 435 current image review fingerprints match; zero stale records.
- All 870 image files pass the curriculum-wide asset audit.
- Subject-specific generator checks pass for mathematics, physics, natural
  sciences, language/computer science, humanities and radiology. All 814
  generator-owned raster files also match fresh deterministic renders; the
  remaining 56 authored raster files are retained.
- Browser verification passes all **432 real lesson routes / 435 images** at
  desktop and mobile widths, checking loads, image proportions, captions, and
  image-viewer open/Escape on subject samples and all companion lessons.
  No JavaScript exceptions. Mobile screenshots were visually inspected.
- Non-image curriculum content, quizzes, reference data and model bindings
  were compared programmatically against main and are unchanged.

Run the main gates with the repository Python environment:

```sh
python tools/check_curriculum_illustrations.py
python tools/check_illustration_reviews.py --require-complete
python tools/generate_radiology_illustrations.py --check --check-determinism
```

For the browser sweep, use an isolated, onboarded local server and Playwright:

```sh
node tools/check_primer_images.cjs http://127.0.0.1:8793
```

The checker creates its own temporary evidence directory. External article
fetching was disabled on the isolated QA server, so this check concerns local
lesson visuals rather than Wikipedia availability. No deployment is included
in this review pass.
