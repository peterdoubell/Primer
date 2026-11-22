"""Paired native SegThy ultrasound sweeps used in the thyroid and neck references."""

THYROID = "ra.ultrasound-thyroid"
NECK = "us.soft-tissue-neck"
DATASET = "https://www.cs.cit.tum.de/en/camp/publications/segthy-dataset/"


def study():
    return {
        "id": "segthy-001", "modality": "Ultrasound",
        "title": "Inspect the thyroid and neck vessels on tracked ultrasound",
        "src": "/app/anatomy/segthy-001/index.html",
        "caption": ("Explore one volunteer’s left and right acquisitions. Each sweep has its own original "
                    "B-mode samples, manual thyroid and vessel labels, and matching 3D surfaces. "
                    "The two sweeps have separate coordinate systems. Nodule features, lymph nodes and blood flow "
                    "require other source evidence."),
        "source_url": DATASET, "publication_url": "https://doi.org/10.1371/journal.pone.0268550",
        "source_label": "SegThy ultrasound dataset", "inline_label": "Inspect ultrasound and label surfaces inline",
        "attribution": "Krönke, Eilers, Dimova and colleagues. SegThy, PLOS ONE (2022). CC BY. Display and surface extraction by Primer.",
        "license": "CC BY", "license_url": DATASET, "clinical_approval": False,
        "structure_ids": [], "requirement_coverage": [],
    }
