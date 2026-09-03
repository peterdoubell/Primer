# Humanities illustration generator

This package contains deterministic, lesson-specific explanatory plates for:

- `07-history.json` (`history.py`)
- `09-arts.json` (`arts.py`)
- `10-mind-society.json` (`mind_society.py`)

The 77 generated plates complement six pre-existing authored plates. Each is
rendered at 1600×1000 and 800×500 as WebP. The visuals encode chronology,
causation, comparison, evidence, argument, feedback, musical structure or a
worked example; they are not decorative topic cards.

From the repository root:

```sh
python3 tools/generate_humanities_illustrations.py --render --overwrite
python3 tools/generate_humanities_illustrations.py --sync-curriculum --check
python3 tools/generate_humanities_illustrations.py --check-determinism
python3 tools/generate_humanities_illustrations.py --contact-sheet-dir /tmp/primer-humanities
```

The inventory check requires specs for every previously unillustrated lesson.
The integrity check requires exactly one illustration and two unique responsive
WebPs for all 83 lessons. Canonical fingerprints protect each earlier authored
illustration/model pair from accidental edits. The determinism check renders all
77 owned plates into a temporary directory and byte-compares both sizes against
the committed assets.
