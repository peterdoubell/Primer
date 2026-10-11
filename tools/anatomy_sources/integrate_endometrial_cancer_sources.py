#!/usr/bin/env python3
"""Bind complete reviewed source figures to their actual endometrial MRI roles."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INV = 'ra.mri-endometrial-cancer'
PREFIX = 'open-endometrial-cancer-'
REVIEW = ROOT / 'docs/endometrial-cancer-source-review'
INDEPENDENT = ROOT / 'docs/endometrial-cancer-independent-source-review-20261011.json'


def save(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def integrate():
    contract = json.loads((REVIEW/'source-figure-contract.json').read_text())
    proof = json.loads((REVIEW/'published-source-preservation.json').read_text())
    independent = json.loads(INDEPENDENT.read_text())
    rows = contract['structure_atlas']
    assert len(rows) == proof['figure_count'] == independent['figure_count'] == 36
    assert not contract['clinical_approval'] and not independent['clinical_approval']
    assert independent['independent_primary_objects_checked']
    assert not independent['source_preservation_blockers_remaining']
    assert {f['id']: f['runtime_sha256'] for f in independent['figures']} == {row['id']: row['sha256'] for row in rows}
    for row in rows:
        assert sha(ROOT/'web'/row['src'].removeprefix('/app/')) == row['sha256']
    path = ROOT/'data/radiology/radiology-open-images.json'
    atlas = json.loads(path.read_text())
    atlas[INV] = rows
    save(path, atlas)
    def f(source, number):
        return PREFIX+source+'-fig'+str(number)
    groups = [
        [f('pmc11119523', n) for n in [4, 7, 9, 18]] + [f('pmc12830431', n) for n in [1, 5, 7]] + [f('pmc13025262', 2)],
        [f('pmc11119523', n) for n in [4, 5, 6, 7]] + [f('pmc12830431', n) for n in [1, 2, 4, 5, 7]] + [f('pmc13025262', 2), f('esr2026', 5)],
        [f('pmc11119523', n) for n in [8, 9, 12]] + [f('pmc12830431', n) for n in [6, 8]],
        [f('pmc11119523', 10)] + [f('pmc12830431', n) for n in [3, 8, 9, 10]] + [f('pmc13025262', 1)],
        [f('pmc11119523', n) for n in [11, 12, 13, 15, 19]] + [f('pmc12830431', 13)],
        [f('pmc11119523', 12), f('pmc12830431', 12), f('pmc13025262', 1), f('pmc8648287', 4)],
        [f('pmc11119523', n) for n in [14, 15, 16]] + [f('pmc12830431', n) for n in [11, 14]] + [f('pmc8648287', 4)],
        [f('pmc11119523', n) for n in [7, 18]] + [f('pmc12830431', 5), f('pmc13025262', 2), f('esr2026', 5)],
        [f('pmc7643338', n) for n in [2, 3]] + [f('pmc8648287', 5)],
    ]
    ids = {row['id'] for row in rows}
    assert set(image for group in groups for image in group) == ids
    path = ROOT/'data/radiology/reporting-steps/abdomen.json'
    walks = json.loads(path.read_text())
    walk = walks['investigations'][INV]
    assert len(walk['steps']) == len(groups) == 9
    for step, images in zip(walk['steps'], groups):
        step['images'] = images
    walk['start']['images'] = [f('pmc11119523', 18), f('pmc12830431', 1), f('esr2026', 5)]
    save(path, walks)
    articles = {a.get('pmcid') or a['source_id']: a for a in proof['articles']}
    records = {record['id']: record for record in proof['figures']}
    assets = []
    for row in rows:
        record = records[row['id']]
        source_id = record.get('pmcid') or record.get('source_id') or 'ESR2026'
        article = articles[source_id]
        evidence_path = REVIEW/(source_id+'-original.xml') if record.get('pmcid') else REVIEW/'ESR2026-figure5-license-and-caption-evidence.json'
        assert evidence_path.is_file()
        assert row['license'] in {'CC BY 4.0', 'CC BY 3.0'}
        assets.append({'id': row['id'], 'kind': row['kind'].replace('-', '_'), 'modality': row['modality'],
            'name': row['caption'], 'local_path': 'web/'+row['src'].removeprefix('/app/'), 'sha256': row['sha256'],
            'investigation_ids': [INV], 'structure_ids': [], 'requirement_coverage': {}, 'reference_only': True,
            'representation': 'complete_original_published_source_artwork_with_original_colour_profile',
            'source_context': row['source_context'],
            'source': {'dataset': article['title'], 'url': row['source_url'],
                'license': {'name': row['license'], 'url': row['license_url'], 'commercial_use': True,
                    'redistribution': True, 'review_status': 'verified', 'reviewed_at': '2026-10-11',
                    'evidence_path': str(evidence_path.relative_to(ROOT)), 'evidence_sha256': sha(evidence_path),
                    'attribution': row['attribution']}},
            'presentation_dependencies': {'web/app.js': sha(ROOT/'web/app.js'),
                'data/radiology/radiology-open-images.json': sha(ROOT/'data/radiology/radiology-open-images.json')},
            'visual_review': {'status': 'source_checked', 'sha256': row['sha256'], 'reviewed_at': '2026-10-11',
                'evidence_path': str(INDEPENDENT.relative_to(ROOT)),
                'basis': 'Independent original encoded/decoded source samples, source ICC, complete annotations and author/caption/rights checks; source-only approval.'},
            'anatomical_review': {'status': 'pending', 'reason': 'Licensed publication appearance does not approve each fine layer, clinical interpretation, current-patient calibration or registration.'},
            'limitations': row['limits']})
    path = ROOT/'data/radiology/radiology-asset-evidence.json'
    evidence = json.loads(path.read_text())
    evidence['assets'] = [asset for asset in evidence['assets'] if not asset['id'].startswith(PREFIX)] + assets
    changed = ['web/lesson-models.js', 'web/spatial-models.js', 'web/spatial-module-objects.js',
               'data/radiology/radiology-open-images.json', 'data/radiology/source-anatomy-references.json']
    for asset in evidence['assets']:
        for name in changed:
            if name in asset.get('presentation_dependencies', {}):
                assert asset['anatomical_review']['status'] == 'pending'
                assert sha(ROOT/asset['local_path']) == asset['sha256']
                asset['presentation_dependencies'][name] = sha(ROOT/name)
    evidence['updated_at'] = '2026-10-11'
    save(path, evidence)
    path = ROOT/'data/radiology/msk-asset-evidence.json'
    evidence = json.loads(path.read_text())
    for asset in evidence['assets']:
        for name in changed[:3]:
            if name in asset.get('presentation_dependencies', {}):
                assert asset['anatomical_review']['status'] == 'pending'
                assert sha(ROOT/asset['local_path']) == asset['sha256']
                asset['presentation_dependencies'][name] = sha(ROOT/name)
    save(path, evidence)
    print('36 complete reviewed source figures bound to nine endometrial MRI assessment areas; no anatomical/current-patient approval.')


if __name__ == '__main__':
    integrate()
