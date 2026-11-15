# Language and computer-science illustration pipeline

These plates are deterministic explanatory diagrams. Every generator-owned
lesson is bound to its own composition: a trace, hierarchy, comparison, causal
sequence, state machine, linguistic analysis, or evidence relationship. Shared
layout code remains only a low-level drawing primitive; no generative-image
service is involved.

From the repository root:

```bash
.venv/bin/python tools/generate_language_cs_illustrations.py \
  --render --sync-curriculum --check --check-determinism \
  --contact-sheet /tmp/primer-language-cs-contact-sheet.png
```

The generator creates a 1600×1000 and 800×500 WebP for each of 68 owned
lessons: 67 that previously lacked an illustration plus a deliberate upgrade
of the older decorative Step by Step plate. It validates all 74 assigned
lessons, refuses unrequested asset replacement, preserves the six remaining
authored plates and their companion models, rejects repeated media paths or
payloads, and compares two fresh regenerations byte-for-byte with the
checked-in files.
