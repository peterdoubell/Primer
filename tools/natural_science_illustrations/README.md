# Natural-science illustration source

This package is the auditable source for the deterministic Life Sciences,
Chemistry, and Earth & Space plates. Each lesson spec names a scientific
relationship and selects a diagram grammar: causal cards, cycles, flows,
branches, measured graphs, layers, networks, scales, or evidence matrices.

From the repository root:

```sh
.venv/bin/python tools/generate_natural_science_illustrations.py \
  --render --overwrite --sync-curriculum --check \
  --contact-sheet /tmp/primer-natural-science-contact-sheet.png
```

`--check` rerenders every generated plate twice, compares encoded bytes with
the committed WebPs, validates 1600×1000 and 800×500 formats and sizes, checks
unique URLs and content, and freezes the pre-existing authored media arrays.
