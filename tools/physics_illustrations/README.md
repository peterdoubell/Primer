# Physics illustration pipeline

Primer's physics plates are deterministic diagrams: the geometry, arrows,
quantities, equations, and captions are authored in Python so their scientific
claims can be reviewed and reproduced.

From the repository root:

```bash
.venv/bin/python tools/generate_physics_media.py --render --overwrite
.venv/bin/python tools/generate_physics_media.py --sync-curriculum --check
```

Use `--contact-sheet /tmp/primer-physics-contact-sheet.png` for visual review.
The generator refuses to overwrite existing assets unless `--overwrite` is
explicitly supplied, and never replaces one of the three pre-existing authored
physics media pairs.
