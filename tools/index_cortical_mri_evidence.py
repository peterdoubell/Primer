"""Bind qualified MRI verification layers to their exact runtime and tool bytes."""
from pathlib import Path
import hashlib
import json
ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / 'docs/cortical-native-mri-review-20261101'
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
load = lambda name: json.loads((DOCS / name).read_bytes())

def main():
    lesson = load('lesson/proof.json'); headed = load('headed-browser-proof.json')
    assert lesson['allPassed'] and lesson['meshDeliveryFixture'] and not lesson['realHostedBrowserDeliveryVerified']
    assert len(lesson['mounts']) == 4 and len(lesson['mriCases']) == 332
    assert headed['allPassed'] and not headed['meshFixture'] and headed['sourceReadback']['allPassed']
    for proof in [lesson, headed, load('anchor-proof.json')]:
        for name, digest in proof['sourceSHA256'].items():
            assert sha(ROOT / name) == digest, name
    pixels = [load(name) for name in ['mri-pixel-proof.json', 'mri-navigation-pixel-proof.json', 'lesson/mri-pixel-proof.json']]
    assert all(proof['allPassed'] and not proof['clinicalApproval'] for proof in pixels)
    assert [proof['states'] for proof in pixels] == [616, 192, 332]
    files = [*sorted((ROOT / 'web/anatomy/spl-source-contacts').iterdir()),
             *sorted((ROOT / 'tools').glob('check_cortical_mri_*')),
             *[ROOT / name for name in ['tools/cortical_mri_runtime_compatibility.py', 'tools/cortical_contact_runtime_compatibility.py',
                 'tools/index_cortical_mri_evidence.py', 'primer/cortical_contact_reference.py', 'primer/server.py',
                 'primer/source_native_inspectors.py', 'web/app.js', 'web/anatomy/spl-nac-limbic/coordinates.js',
                 'web/anatomy/spl-nac-limbic/manifest.json']]]
    index = {'clinicalApproval': False, 'anatomicalVisibilityVerified': False, 'wholeGoalComplete': False,
             'productionAuthenticatedReaderVerified': False,
             'headlessHostedBrowserMeshVerified': False,
             'headlessHostedBrowserMeshLimitation': 'Observed HTTP 403 Vercel Security Checkpoint; no access/security changes made.',
             'normalChromeHostedMeshVerified': True, 'normalChromeViewerInteractionVerified': True,
             'authenticatedLessonMeshDeliveryFixture': True,
             'browserStates': sum(proof['states'] for proof in pixels),
             'actualCanvasPixelsCompared': sum(proof['actualCanvasPixelsCompared'] for proof in pixels),
             'crosshairLocationsChecked': sum(proof['crosshairLocationsChecked'] for proof in pixels),
             'sourceSHA256': {str(path.relative_to(ROOT)): sha(path) for path in files if path.is_file()},
             'proofSHA256': {str(path.relative_to(DOCS)): sha(path) for path in sorted(DOCS.rglob('*.json')) if path.name != 'evidence-index.json'}}
    (DOCS / 'evidence-index.json').write_text(json.dumps(index, indent=2) + '\n')
    print(json.dumps({key: index[key] for key in ['browserStates', 'actualCanvasPixelsCompared', 'crosshairLocationsChecked', 'clinicalApproval']}))

if __name__ == '__main__':
    main()
