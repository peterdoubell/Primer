"""Every heading report_structures_20261117.py writes, by region."""
import importlib

PARTS = ('report_structures_msk', 'report_structures_body', 'report_structures_chest_neuro', 'report_structures_uniform')
CONTENT = '\n'.join(importlib.import_module(part).CONTENT for part in PARTS)
