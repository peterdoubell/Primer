# Natural-science illustration source

This package is the auditable source for the deterministic Life Sciences,
Chemistry, and Earth & Space plates. Each lesson spec names a scientific
relationship and selects a diagram grammar: causal paths, cycles, flows,
branches, measured graphs, layers, networks, scales, or evidence matrices.
Every generated lesson in all three domains is then bound to a bespoke
field-guide composition so named structures, mechanisms, evidence, and scale
are never reduced to generic icons.

From the repository root:

```sh
.venv/bin/python tools/generate_natural_science_illustrations.py \
  --render --overwrite --sync-curriculum --check \
  --contact-sheet /tmp/primer-natural-science-contact-sheet.png
```

For a complete domain review sheet, including its authored plates:

```sh
.venv/bin/python tools/generate_natural_science_illustrations.py \
  --contact-sheet /tmp/primer-biology-contact-sheet.png \
  --contact-sheet-domain biology
```

The natural-science release rubric matches mathematics: every plate must make a
mechanism, structure, comparison, causal path, scale, constraint, or
misconception visible at the 800px delivery size. A generic subject icon beside
explanatory prose is not enough. Biology, Chemistry, and Earth & Space therefore
use lesson-specific, deterministic compositions while retaining the shared
cream paper, stage markers, palette, and responsive raster contract.

`--check` rerenders every generated plate twice, compares encoded bytes with
the committed WebPs, validates 1600×1000 and 800×500 formats and sizes, checks
unique URLs and content, and freezes the pre-existing authored media arrays.
Contact sheets read the curriculum media rather than the generator inventory,
so authored and generated plates are reviewed together.
