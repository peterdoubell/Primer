"""Published multimodal MRI and reviewed segmentation from OpenNeuro ds007045."""
PREFIX = "/app/anatomy/glioblastoma-ba2/"


def case_inspector():
    return {
        "id": "openneuro-glioblastoma-ba2",
        "title": "Glioblastoma MRI and tumour compartments",
        "modality": "Multimodal MRI and segmented surfaces",
        "src": PREFIX + "index.html",
        "manifest_url": PREFIX + "manifest.json",
        "sha256": '0c42390754b72e82fc4d3bf3ce37513e7464b3e484a7e2c5b90dfb5fd45a4872',
        "manifest_sha256": '821d80674af57355928019557365b31cc104c96744872c89e81c848ec6c1a791',
        "caption": "Compare pre-contrast T1, post-contrast T1, T2 and FLAIR at a shared slice. Isolate each segmented compartment in 3D. The publisher registered these images to MNI152 space. Surface dimensions describe the processed grid.",
        "attribution": "Filimonova and colleagues, OpenNeuro ds007045 v2.0.1, case sub-BA2. Display windows and voxel-boundary surfaces prepared by Primer.",
        "source_url": "https://doi.org/10.18112/openneuro.ds007045.v2.0.1",
        "publication_url": "https://doi.org/10.1038/s41597-026-07953-2",
        "license": "CC0",
        "license_url": "https://creativecommons.org/publicdomain/zero/1.0/",
        "clinical_approval": False,
        "fine_anatomical_approval": False,
        "current_patient_registration": False,
        "normal_anatomical_atlas_approval": False,
        "complete_reporting_anatomy_approved": False,
    }
