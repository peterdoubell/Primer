"""Supplement immutable lesson-delivery evidence after one reviewed helper change."""
import copy
import hashlib
import json
from pathlib import Path

from primer.curriculum import Curriculum, _validate_lesson_media
from primer.module_media import source_model_bindings
from tools.check_radiology_fidelity import digest
from tools.anatomy_sources import apply_native_source_presentation_review as presentation

ROOT = Path(__file__).resolve().parents[2]
FOLDER = ROOT / 'docs/bladder-anatomy-fidelity-review'
HISTORICAL = FOLDER / 'source-model-lesson-delivery-review.json'
CURRENT = FOLDER / 'current-source-model-lesson-delivery-review.json'
HISTORICAL_SHA = 'a9b1be5d620e2071c399d5f88d1476e18f523273ad9e9d23b352f28810adb8fb'
NATIVE_CONTRACT_SHA = '87c50f17631398d9d558b1b7c2065a7e53e9ecb9d47c39473ddc586b279f0a63'
OLD_HELPER_SHA = 'e287d4f77eaefa99a849848611ea45fb69f7617cb588d3f3bd59190177003958'
CURRENT_HELPER_SHA = '30f82f5a0ef534ce44bfbe40961220abc6487fd426f9af914622ef79c0177890'
HELPER = 'web/anatomy/verse521/ct-reference.js'
FIELDS = ['goal', 'learning_outcomes', 'lesson', 'reference', 'radiology_reference',
          'visual_spec', 'lesson_media', 'model_family', 'model_context', 'practice', 'quiz', 'kid_text']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def scoped_contract(node):
    contract = copy.deepcopy({key: node.get(key) for key in FIELDS})
    props = next(m for m in contract['lesson_media'] if m.get('renderer') == 'radiology-anatomy')['props']
    # Later FEDBCA cases have their own proof; retain the original sixteen references.
    props['source_references'] = [s for s in props['source_references'] if not s['atlas'].startswith('fedbca-')]
    return contract, props


def checked_historical_contract(node, row):
    """Permit only the independently reviewed VerSe script transport amendment."""
    contract, props = scoped_contract(node)
    # The source models keep their historical review. The separately reviewed
    # myelopathy gallery is an additive lesson reference, not model approval.
    if node['id'] == 'rad.4.spine-imaging':
        gallery = next(m for m in contract['lesson_media'] if m.get('kind') == 'source-gallery')
        if gallery['investigation_ids'] != ['ra.thoracolumbar-fractures', 'ra.mri-myelopathy']:
            raise ValueError('Unreviewed shared spine source-gallery scope')
        gallery['investigation_ids'] = ['ra.thoracolumbar-fractures']
    for source in props['source_references']:
        if source['id'] == 'verse521-bones':
            if source['source_volume']['script_sha256'] != CURRENT_HELPER_SHA:
                raise ValueError('Unreviewed VerSe helper fingerprint')
            source['source_volume']['script_sha256'] = OLD_HELPER_SHA
    expected = {'model_props_sha256': digest(props),
                'complete_current_module_contract_sha256': digest(contract),
                'source_references_sha256': digest(props['source_references'])}
    if any(row[key] != value for key, value in expected.items()):
        raise ValueError('Unexpected historical lesson/source descriptor drift: ' + row['module_id'])
    if row['source_ids'] != [source['id'] for source in props['source_references']] or row['clinical_or_complete_anatomical_approval']:
        raise ValueError('Historical source scope or approval changed')
    return contract, props


def build_review():
    if sha(HISTORICAL) != HISTORICAL_SHA:
        raise ValueError('Immutable historical delivery evidence changed')
    historical = json.loads(HISTORICAL.read_text())
    if sha(ROOT / 'docs/myelopathy-independent-source-review-20261011.json') != 'ac775f60d6011bca10099a6607da02e4d99ea9489e9868ff0cf3948c60cba1b1':
        raise ValueError('Separate myelopathy source review changed')
    applied_path = presentation.FOLDER / 'applied-presentation-review.json'
    applied = json.loads(applied_path.read_text())
    independent = json.loads(presentation.INDEPENDENT.read_text())
    if (sha(presentation.CONTRACT) != NATIVE_CONTRACT_SHA
            or applied['contract_sha256'] != NATIVE_CONTRACT_SHA
            or independent['contract_sha256'] != NATIVE_CONTRACT_SHA
            or applied['independent_review_sha256'] != sha(presentation.INDEPENDENT)
            or not independent['source_presentation_only_verified'] or independent['blockers']
            or any(e['clinical_approval'] or e['fine_anatomical_approval'] for e in [applied, independent])):
        raise ValueError('VerSe presentation amendment lacks matching independent review')
    changes = [c for c in applied['dependency_changes'] if c['path'] == HELPER]
    if changes != [{'id': 'verse521-native-ct-planes', 'path': HELPER,
                    'before': OLD_HELPER_SHA, 'after': CURRENT_HELPER_SHA}] or sha(ROOT / HELPER) != CURRENT_HELPER_SHA:
        raise ValueError('VerSe helper bytes differ from the reviewed amendment')
    curr = Curriculum()
    bindings = source_model_bindings()
    modules = []
    files = {HELPER: CURRENT_HELPER_SHA}
    for row in historical['modules']:
        node = curr.node(row['module_id'])
        _validate_lesson_media(node)
        model = next(m for m in node['lesson_media'] if m.get('renderer') == 'radiology-anatomy')
        if model['props']['source_references'] != bindings[node['id']]:
            raise ValueError('Model source references differ from its matching lesson')
        checked_historical_contract(node, row)
        contract, props = scoped_contract(node)
        for source in props['source_references']:
            path = 'web/' + source['manifest_url'].removeprefix('/app/')
            if sha(ROOT / path) != source['manifest_sha256']:
                raise ValueError('Source manifest bytes changed')
            files[path] = source['manifest_sha256']
            if source['id'] == 'verse521-bones':
                volume = source['source_volume']
                path = 'web/' + volume['src'].removeprefix('/app/')
                if sha(ROOT / path) != volume['sha256']:
                    raise ValueError('Native VerSe CT payload changed')
                files[path] = volume['sha256']
            if source['atlas'].startswith('hra-bladder-'):
                manifest = json.loads((ROOT / path).read_text())
                if manifest['clinical_approval'] or manifest['complete_reporting_anatomy_approved']:
                    raise ValueError('Bladder source approval changed')
                for part in manifest['parts'].values():
                    part_path = 'web/' + part['file'].removeprefix('/app/')
                    if sha(ROOT / part_path) != part['sha256']:
                        raise ValueError('Original bladder primitive transport changed')
                    files[part_path] = part['sha256']
        modules.append({'module_id': row['module_id'],
                        'current_scoped_module_contract_sha256': digest(contract),
                        'model_props_sha256': digest(props),
                        'source_references_sha256': digest(props['source_references']),
                        'source_ids': [source['id'] for source in props['source_references']],
                        'clinical_or_complete_anatomical_approval': False})
    if len(modules) != historical['matching_lessons'] or sum(len(r['source_ids']) for r in modules) != historical['source_references']:
        raise ValueError('Historical delivery scope changed')
    return {'schema_version': 1, 'scope': 'Original 11 matching lessons and 16 source references; later source cases retain separate proofs',
            'historical_proof_sha256': HISTORICAL_SHA, 'native_presentation_contract_sha256': NATIVE_CONTRACT_SHA,
            'native_presentation_independent_review_sha256': sha(presentation.INDEPENDENT),
            'allowed_descriptor_amendment': {'module_id': 'rad.4.spine-imaging', 'source_id': 'verse521-bones',
                                           'field': 'source_volume.script_sha256', **changes[0]},
            'separate_additive_gallery_scope': {
                'module_id': 'rad.4.spine-imaging', 'investigation_id': 'ra.mri-myelopathy',
                'review': 'docs/myelopathy-independent-source-review-20261011.json',
                'review_sha256': 'ac775f60d6011bca10099a6607da02e4d99ea9489e9868ff0cf3948c60cba1b1',
                'source_models_or_historical_approval_extended': False},
            'matching_lessons': len(modules), 'source_references': historical['source_references'],
            'verified_current_files': dict(sorted(files.items())), 'modules': modules,
            'clinical_approval': False, 'fine_anatomical_approval': False,
            'whole_radiology_goal_complete': False, 'new_browser_visual_review': False}


if __name__ == '__main__':
    CURRENT.write_text(json.dumps(build_review(), indent=2) + '\n')
