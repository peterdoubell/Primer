"""Named s0028 lobe bodies beside the independent LIDC nodule example."""
from copy import deepcopy

CASE = 'ra.ct-pulmonary-nodules'
NODE = 'rad.4.pulmonary-nodule'
LOBE_BODIES = (
    ('pulmonary.right.upper', 'lung_upper_lobe_right', 'right upper lobe'),
    ('pulmonary.right.middle', 'lung_middle_lobe_right', 'right middle lobe'),
    ('pulmonary.right.lower', 'lung_lower_lobe_right', 'right lower lobe'),
    ('pulmonary.left.upper', 'lung_upper_lobe_left', 'left upper lobe'),
    ('pulmonary.left.lower', 'lung_lower_lobe_left', 'left lower lobe'),
)


def references():
    from .thoracic_lung_native import references as source_references

    item, = deepcopy(source_references()['ra.thoracic-ultrasound'])
    item['title'] = 'Same-case CT and five named lung-lobe labels'
    item['caption'] = (
        'Inspect the source CT of TotalSegmentator s0028 with its five original lobe masks and '
        'matching surfaces. These labels describe the lobar bodies of s0028. LIDC-IDRI-0525 '
        'supplies the independent nodule example. Fissural planes, lingular segments and nodule '
        'attachment need their own source evidence.'
    )
    item['named_lobe_examples'] = [
        {'requirement_parent_id': requirement, 'source_label': label, 'name': name,
         'evidence_role': 'source-labelled lobe body', 'extent': 'partial'}
        for requirement, label, name in LOBE_BODIES
    ]
    item['structure_coverage_granted'] = False
    return {CASE: [item]}
