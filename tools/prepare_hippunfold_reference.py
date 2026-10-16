"""Pin the local, reviewed hippocampal viewer and its complete source payload set."""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ATLAS = 'hippunfold-hcp101006-registered'
IDENTIFIER = 'hippunfold-hcp101006-registered-reference'
PREFIX = '/app/anatomy/' + ATLAS + '/'


def main():
    base = ROOT / 'web/anatomy' / ATLAS
    files = {p.name: {'sha256': hashlib.sha256(p.read_bytes()).hexdigest(), 'bytes': p.stat().st_size}
             for p in sorted(base.iterdir()) if p.is_file()}
    assert len(files) == 25
    item = {
        'id': IDENTIFIER,
        'modality': 'Registered T2 MRI and categorical surfaces',
        'coordinate_context': 'published-registered-training-grid',
        'title': 'Published hippocampal T2 MRI and source-label surfaces',
        'src': PREFIX + 'index.html', 'manifest_url': PREFIX + 'manifest.json',
        'sha256': files['index.html']['sha256'], 'manifest_sha256': files['manifest.json']['sha256'],
        'caption': 'Explore matched T2 crops and eight research label classes from the published HippUnfold HCP-YA case 101006. Both supplied hemisphere files retain every source sample and all 472,392 categorical boundary triangles. These registered, resampled training grids support hippocampal context; they do not establish native volume or asymmetry, normality, pathology, patient laterality, CA subfields or complete reporting anatomy.',
        'attribution': 'Jordan DeKraker and Ali R. Khan. HippUnfold HCP-YA Training Data v1.0.0, case 101006. DOI 10.5281/zenodo.7007362. CC BY 4.0. Adaptations: lossless value transport, display windowing and exact categorical voxel-cell boundaries; no additional mirroring, smoothing, component deletion or anatomical fitting.',
        'source_url': 'https://zenodo.org/records/7007362',
        'publication_url': 'https://pmc.ncbi.nlm.nih.gov/articles/PMC9831605/',
        'license': 'CC BY 4.0', 'license_url': 'https://creativecommons.org/licenses/by/4.0/',
        'bound_source_ids': [IDENTIFIER],
        **{key: False for key in ['clinical_approval', 'fine_anatomical_approval', 'current_patient_registration',
                                  'normal_anatomical_atlas_approval', 'complete_reporting_anatomy_approved']},
    }
    data = {'schema_version': 1, 'source_case': '101006', 'source_version': 'v1.0.0',
            'source_doi': '10.5281/zenodo.7007362',
            'bindings': {key: [IDENTIFIER] for key in ['ra.mri-epilepsy', 'ra.mri-dementia']},
            'inspectors': {IDENTIFIER: item}, 'files': files}
    path = ROOT / 'data/radiology/hippunfold-reference.json'
    path.write_text(json.dumps(data, indent=2) + '\n')
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    helper = ROOT / 'primer/hippunfold_reference.py'
    code, count = re.subn(r"REGISTRY_SHA256 = '[^']+'", "REGISTRY_SHA256 = '" + digest + "'", helper.read_text())
    assert count == 1
    helper.write_text(code)
    print(json.dumps({'registry_sha256': digest, 'files': len(files), 'bytes': sum(r['bytes'] for r in files.values())}))


if __name__ == '__main__':
    main()
