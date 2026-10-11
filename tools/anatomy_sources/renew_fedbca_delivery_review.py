#!/usr/bin/env python3
"""Renew delivery hashes for the reviewed helper and separate additive source gallery."""
import argparse
import copy
import gzip
import hashlib
import json
from pathlib import Path

from primer.curriculum import Curriculum
from primer.module_media import source_model_bindings
from tools.check_radiology_fidelity import digest

ROOT = Path(__file__).resolve().parents[2]
PROOF = Path('docs/fedbca-bladder-source-review')
HISTORICAL_SHA256 = '73e855edd4f753c46f7daf7c08540803a89dbfec8d3a1dc65bcec3eac7e3c89a'
OLD_HELPER_SHA256 = 'e287d4f77eaefa99a849848611ea45fb69f7617cb588d3f3bd59190177003958'
CURRENT_HELPER_SHA256 = '30f82f5a0ef534ce44bfbe40961220abc6487fd426f9af914622ef79c0177890'
NATIVE_CONTRACT_SHA256 = '87c50f17631398d9d558b1b7c2065a7e53e9ecb9d47c39473ddc586b279f0a63'
PRESENTATION_FOLDER = Path('docs/native-source-presentation-review-20261011')
INDEPENDENT_REVIEW = Path('docs/native-source-presentation-independent-review-20261011.json')
GALLERY_REVIEW = Path('docs/myelopathy-independent-source-review-20261011.json')
GALLERY_REVIEW_SHA256 = 'ac775f60d6011bca10099a6607da02e4d99ea9489e9868ff0cf3948c60cba1b1'
CONTRACT_FIELDS = ('goal', 'learning_outcomes', 'lesson', 'reference', 'radiology_reference',
                   'visual_spec', 'lesson_media', 'model_family', 'model_context', 'practice',
                   'quiz', 'kid_text')


def historical_descriptor(value):
    """Restore one explicit metadata field; every other field stays hash-bound."""
    result = copy.deepcopy(value)

    def restore(item):
        if isinstance(item, dict):
            if item.get('id') == 'verse521-bones':
                volume = item.get('source_volume', {})
                if volume.get('script_sha256') != CURRENT_HELPER_SHA256:
                    raise ValueError('VerSe helper differs from the reviewed renewal')
                volume['script_sha256'] = OLD_HELPER_SHA256
            for child in item.values():
                restore(child)
        elif isinstance(item, list):
            for child in item:
                restore(child)

    restore(result)
    return result


def historical_module_contract(contract, module_id):
    """Restore only the separately reviewed shared spine gallery addition."""
    from .brain_native_delivery_amendment import restored_historical_contract
    result = historical_descriptor(restored_historical_contract(contract, module_id))
    if module_id == 'rad.4.spine-imaging':
        galleries = [item for item in result['lesson_media'] if item.get('kind') == 'source-gallery']
        if (len(galleries) != 1
                or galleries[0]['investigation_ids'] != ['ra.thoracolumbar-fractures', 'ra.mri-myelopathy']):
            raise ValueError('Unreviewed shared spine source-gallery scope')
        galleries[0]['investigation_ids'] = ['ra.thoracolumbar-fractures']
    return result


def verified_gallery_review(root):
    """Pin the independent source review without extending source model approval."""
    if hashlib.sha256((root / GALLERY_REVIEW).read_bytes()).hexdigest() != GALLERY_REVIEW_SHA256:
        raise ValueError('Separate myelopathy source review changed')
    return {'module_id': 'rad.4.spine-imaging', 'investigation_id': 'ra.mri-myelopathy',
            'review': GALLERY_REVIEW.as_posix(), 'review_sha256': GALLERY_REVIEW_SHA256,
            'source_models_or_historical_approval_extended': False}


def verified_source_files(root, sources):
    """Check local bytes against the retained descriptor/manifest identities."""
    files = {}

    def record(url, expected, decoded_sha256=None, payload=None):
        if not url.startswith('/app/'):
            raise ValueError('Source file requires a local application path')
        path = root / 'web' / url.removeprefix('/app/')
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != expected:
            raise ValueError('Reviewed source bytes changed: ' + url)
        row = {'path': path.relative_to(root).as_posix(), 'sha256': expected, 'bytes': len(raw)}
        if decoded_sha256 or payload:
            decoded = gzip.decompress(raw)
            actual = hashlib.sha256(decoded).hexdigest()
            if actual != (decoded_sha256 or payload['raw_source_voxel_sha256']):
                raise ValueError('Reviewed decoded source bytes changed: ' + url)
            row.update(decoded_sha256=actual, decoded_bytes=len(decoded))
            if payload and (len(raw) != payload['compressed_bytes'] or len(decoded) != payload['bytes']):
                raise ValueError('Reviewed complete source array extent changed: ' + url)
        if url in files and files[url] != row:
            raise ValueError('Inconsistent source file identity: ' + url)
        files[url] = row
        return raw

    for source in sources:
        manifest = json.loads(record(source['manifest_url'], source['manifest_sha256']))
        for part in manifest['parts'].values():
            record(part['file'], part['sha256'], part.get('decoded_sha256'))
        image = source.get('source_image')
        if image:
            record(image['src'], image['sha256'])
        volume = source.get('source_volume')
        if volume:
            record(volume['src'], volume['sha256'])
            script_url = str(Path(volume['src']).with_suffix('.js'))
            record(script_url, volume['script_sha256'])
            for payload in volume.get('data_files', []):
                record(str(Path(volume['src']).parent / payload['file']),
                       payload['compressed_sha256'], payload=payload)
    return sorted(files.values(), key=lambda row: row['path'])


def verified_helper_review(root):
    """Bind the helper amendment to the applied independent presentation review."""
    paths = {'contract': PRESENTATION_FOLDER / 'proposed-presentation-amendments.json',
             'applied_review': PRESENTATION_FOLDER / 'applied-presentation-review.json',
             'independent_review': INDEPENDENT_REVIEW}
    raw = {name: (root / path).read_bytes() for name, path in paths.items()}
    hashes = {name: hashlib.sha256(value).hexdigest() for name, value in raw.items()}
    contract, applied, independent = (json.loads(raw[name]) for name in paths)
    if (hashes['contract'] != NATIVE_CONTRACT_SHA256
            or applied['contract_sha256'] != NATIVE_CONTRACT_SHA256
            or independent['contract_sha256'] != NATIVE_CONTRACT_SHA256
            or applied['independent_review_sha256'] != hashes['independent_review']
            or contract['source_presentation_verified'] is not True
            or independent['source_presentation_only_verified'] is not True
            or independent['blockers'] != []
            or applied['source_bytes_changed'] is not False
            or applied['anatomical_or_fidelity_or_coverage_or_licence_fields_changed'] is not False
            or any(review['clinical_approval'] is not False or review['fine_anatomical_approval'] is not False
                   for review in (contract, applied, independent))):
        raise ValueError('VerSe helper amendment lacks matching independent presentation review')
    changes = [row for row in applied['dependency_changes']
               if row['path'] == 'web/anatomy/verse521/ct-reference.js']
    if changes != [{'id': 'verse521-native-ct-planes', 'path': 'web/anatomy/verse521/ct-reference.js',
                    'before': OLD_HELPER_SHA256, 'after': CURRENT_HELPER_SHA256}]:
        raise ValueError('VerSe helper amendment differs from the reviewed dependency change')
    return {**{name: {'path': path.as_posix(), 'sha256': hashes[name]} for name, path in paths.items()},
            'source_presentation_only_verified': True, 'blockers': [],
            'clinical_approval': False, 'fine_anatomical_approval': False}


def build_current_delivery_review(curriculum=None, bindings=None, root=ROOT):
    raw = (root / PROOF / 'historical-source-delivery-review.json').read_bytes()
    if hashlib.sha256(raw).hexdigest() != HISTORICAL_SHA256:
        raise ValueError('Retained historical delivery proof changed')
    retained = json.loads(raw)
    if retained['matching_lessons'] != 11 or retained['source_references'] != 20:
        raise ValueError('Retained delivery scope changed')
    curriculum = curriculum or Curriculum()
    bindings = bindings if bindings is not None else source_model_bindings()
    gallery_review = verified_gallery_review(root)
    from .brain_native_delivery_amendment import separate_review
    native_review = separate_review(root)
    result = copy.deepcopy(retained)
    sources = []
    for previous, row in zip(retained['modules'], result['modules']):
        node = curriculum.node(row['module_id'])
        contract = {field: node.get(field) for field in CONTRACT_FIELDS}
        model = next(item for item in node['lesson_media'] if item.get('renderer') == 'radiology-anatomy')
        refs = bindings[row['module_id']]
        if model['props'].get('source_references') != refs:
            raise ValueError('Current model props differ from delivered source bindings')
        for value, field in ((contract, 'current_module_contract_sha256'),
                             (model['props'], 'model_props_sha256'), (refs, 'source_references_sha256')):
            historical_value = (historical_module_contract(value, row['module_id'])
                                if field == 'current_module_contract_sha256'
                                else historical_descriptor(value))
            if digest(historical_value) != previous[field]:
                raise ValueError('Unreviewed module/props/source descriptor change: ' + row['module_id'])
            row[field] = digest(value)
        if [ref['id'] for ref in refs] != previous['source_reference_ids']:
            raise ValueError('Retained source scope changed: ' + row['module_id'])
        if previous['clinical_or_anatomical_approval'] is not False:
            raise ValueError('Delivery renewal cannot assign clinical approval')
        sources.extend(refs)
    if len(sources) != retained['source_references'] or retained['full_clinical_goal_complete'] is not False:
        raise ValueError('Delivery renewal cannot expand scope or complete the clinical goal')
    result['renewal'] = {
        'historical_proof': (PROOF / 'historical-source-delivery-review.json').as_posix(),
        'historical_proof_sha256': HISTORICAL_SHA256,
        'historical_source_commit': 'd0088d593ad8d56b0d3c1d03bc0da08451ffa63d',
        'reviewed_helper_commit': '5f18cb107987f65c6a12c6f893a4146e3a79ae94',
        'native_presentation_review': verified_helper_review(root),
        'separate_additive_gallery_scope': gallery_review,
        'separate_additive_native_inspector': native_review,
        'permitted_descriptor_change': {
            'source_id': 'verse521-bones', 'field': 'source_volume.script_sha256',
            'previous_sha256': OLD_HELPER_SHA256, 'current_sha256': CURRENT_HELPER_SHA256,
            'path': 'web/anatomy/verse521/ct-reference.js',
        },
        'basis': 'Every retained full module contract, model props and source binding reproduces its historical digest after restoring only the reviewed VerSe helper fingerprint and the independently reviewed additive myelopathy gallery reference in the shared spine lesson. The gallery does not extend historical source model approval. Local source manifests, model payloads, images, volume viewers, scripts and complete scalar arrays match their descriptor identities.',
        'new_browser_or_clinical_review_claimed': False,
        'clinical_approval': False,
        'fine_anatomical_approval': False,
        'verified_current_source_files': verified_source_files(root, sources),
    }
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    current = build_current_delivery_review()
    path = ROOT / PROOF / 'current-source-delivery-review.json'
    if args.write:
        path.write_text(json.dumps(current, indent=2) + '\n')
    elif json.loads(path.read_text()) != current:
        raise ValueError('Current delivery proof requires guarded renewal')
    print(f"Verified {current['matching_lessons']} lessons, {current['source_references']} source references and {len(current['renewal']['verified_current_source_files'])} local source files.")


if __name__ == '__main__':
    main()
