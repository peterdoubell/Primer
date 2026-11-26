"""Same-acquisition anatomy for the two cross-sectional surveys."""
from functools import lru_cache
import hashlib
import json
from pathlib import Path

ATLAS = 'ct-torso-s0028'
EXAMS = {'rad.4.oncology-response': 'ct.chest-abdomen-pelvis', 'rad.5.abdominal-trauma': 'ct.trauma-panscan'}


def references():
    rows = report_areas()
    return {exam: [{
        'id': ATLAS,
        'title': 'Explore the chest, abdomen and pelvis on the same CT',
        'src': '/app/anatomy/' + ATLAS + '/index.html?exam=' + exam,
        'modality': 'CT', 'model_context': True,
        'caption': ('TotalSegmentator case s0028 has 109 nonempty source masks on one CT grid. '
                    'Inspect the original section, a map that preserves shared labels, and the matching 3D surface. '
                    'The report-area menu identifies the structures available for this examination. '
                    'Injury, lesion measurements and response require separate evidence.'),
        'source_label': 'TotalSegmentator v3.0.0 case archive', 'source_url': 'https://zenodo.org/records/22688904',
        'publication_url': 'https://doi.org/10.1148/ryai.230024',
        'license': 'CC BY 4.0', 'license_url': 'https://creativecommons.org/licenses/by/4.0/',
        'attribution': 'Wasserthal and colleagues, University Hospital Basel. CT and segmentations from TotalSegmentator v3.0.0. Display, sections and label surfaces by Primer.',
        'inline_label': 'Inspect original CT, mask map and 3D surfaces',
        'report_area_links': rows[exam],
        'clinical_approval': False, 'current_patient_registration': False,
        'structure_ids': [], 'requirement_coverage': [],
    }] for exam in EXAMS.values()}


@lru_cache(maxsize=1)
def report_areas():
    directory = Path(__file__).resolve().parents[1] / 'web/anatomy' / ATLAS
    raw = (directory / 'report-areas.json').read_bytes()
    manifest = (directory / 'manifest.json').read_bytes()
    if (hashlib.sha256(raw).hexdigest() != '85dd872264ebf95e9aaae41aa1018ada97c635077661e33845a7c4a087848773' or
            hashlib.sha256(manifest).hexdigest() != '046d813e59dd34ff06e83398ef3f323b76b2f6d404e20e649a7267fb380046cd'):
        raise ValueError('Torso CT source metadata changed')
    labels = {row['sourceLabel']: row['voxelCount'] for row in json.loads(manifest)['labels']}
    links = {}
    for exam, sections in json.loads(raw).items():
        rows = []
        for section in sections:
            named = section['sourceLabels']
            nonempty = sum(labels[name] > 0 for name in named)
            rows.append({
                'row': section['id'], 'name': section['name'], 'present': nonempty,
                'empty': len(named) - nonempty, 'note': section['note'],
                'src': '/app/anatomy/' + ATLAS + '/index.html?exam=' + exam + '&row=' + section['id'],
            })
        links[exam] = rows
    return links
