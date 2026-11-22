"""Exact named source-template context, without granting stroke coverage."""
from copy import deepcopy
from functools import lru_cache
import json

CASE = 'ra.acute-stroke'
NODE = 'rad.4.stroke'
# These whole-territory names match the inventory's side/class literally.
MATCHES = (
    ('stroke.arterial_territory.ACA.left', 'left ACA', 12, 'Left ACA'),
    ('stroke.arterial_territory.ACA.right', 'right ACA', 2, 'Right ACA'),
    ('stroke.arterial_territory.PCA.left', 'left PCA', 16, 'Left PCA'),
    ('stroke.arterial_territory.PCA.right', 'right PCA', 6, 'Right PCA'),
)


@lru_cache(maxsize=1)
def examples():
    from .schirmer_vascular_reference import PREFIX, metadata_bytes

    labels = {row['code']: row for row in json.loads(metadata_bytes('labels.json'))['sourceClasses']}
    rows = []
    for parent, name, code, legend in MATCHES:
        source = labels[code]
        if source['publishedFigureLegendName'] != legend:
            raise ValueError('Stroke source context name differs')
        rows.append(dict(requirement_parent_id=parent, requirement_name=name,
                         source_code=code, source_name=source['name'],
                         src=PREFIX + 'index.html?code=' + str(code),
                         evidence_role='source-study territory context',
                         structure_coverage_granted=False))
    return rows


def decorate(identifier, inspector):
    result = deepcopy(inspector)
    if identifier == CASE:
        result['source_territory_contexts'] = deepcopy(examples())
    return result
