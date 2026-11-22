"""Gross salivary anatomy for the neck examinations that report these structures."""
from copy import deepcopy

ATLAS = 'zanatomy-salivary'
EXAMS = ('us.soft-tissue-neck', 'ra.mri-neck-spaces', 'ra.cervical-lymph-nodes')
SOURCE = 'https://github.com/Z-Anatomy/Models-of-human-anatomy/tree/ded1a55381328f3f242426f0e8e711c5fca62c14'


def references():
    card = {
        'id': ATLAS, 'title': 'Salivary glands and ducts in 3D and section',
        'src': '/app/anatomy/' + ATLAS + '/index.html',
        'modality': 'Gross anatomical atlas', 'model_context': True,
        'caption': ('Examine the left and right parotid, submandibular and sublingual gland bodies, the '
                    'modelled parotid and submandibular ducts, and eight muscular or bony landmarks. '
                    'The section view cuts the same atlas surfaces. The paired atlas objects share underlying geometry. '
                    'Imaging findings, nodal boundaries and glandular subdivisions require separate evidence.'),
        'source_label': 'Z-Anatomy original Blender scene', 'source_url': SOURCE,
        'publication_url': 'https://doi.org/10.5281/zenodo.4953712', 'license': 'CC BY-SA 4.0',
        'license_url': 'https://creativecommons.org/licenses/by-sa/4.0/',
        'attribution': ('Z-Anatomy · The libre 3D atlas of anatomy. Based on BodyParts3D, '
                        'Copyright © 2008 Database Center for Life Science, CC BY-SA 2.1 Japan. '
                        'Primer adaptations include mesh encoding, colours and cross-sections.'),
        'inline_label': 'Inspect the atlas surfaces and sections inline',
        'structure_ids': [], 'requirement_coverage': [], 'clinical_approval': False,
        'fine_anatomical_approval': False, 'current_patient_registration': False,
    }
    return {exam: [deepcopy(card)] for exam in EXAMS}
