"""Inventory actual MSK reference figures independently of coverage claims.

The static clinical/anatomical galleries are the scope here. Project-authored
lesson plates, generated contextual photos and linked external reading have
separate provenance/quality workflows and are not reclassified as clinical
reference figures by this inventory.
"""
from __future__ import annotations
import hashlib
from pathlib import Path


def reference_images(curriculum, catalogue, requirements, detail, catalog_section='Musculoskeletal'):
    """Read current rendered-reference inputs, including declared extra surfaces."""
    by_id = {item['id']: item for item in catalogue['investigations']}
    investigations = {item['id'] for item in by_id.values()
                      if catalog_section is None or item['section'] == catalog_section}
    modules = {by_id[key]['module_id'] for key in investigations}
    for additional in requirements.get('additional_scope', []):
        modules.add(additional['module_id'])
        if additional.get('investigation_id'):
            investigations.add(additional['investigation_id'])
    resources = {}
    surfaces = []

    def collect(reference, surface):
        surfaces.append(surface)
        collections = {field: reference.get(field, []) for field in ('key_images', 'structure_atlas', 'anatomical_illustrations')}
        collections['source_anatomy_images'] = [source['source_image'] for source in reference.get('source_anatomy_references', []) if source.get('source_image')]
        collections['source_anatomy_ct_volumes'] = [source['source_volume'] for source in reference.get('source_anatomy_references', []) if source.get('source_volume')]
        for field, images in collections.items():
            for image in images:
                src = image.get('src')
                if not isinstance(src, str) or not src:
                    raise ValueError(surface + ': reference image is missing its source')
                if not (src.startswith('/app/') or src.startswith('https://')):
                    raise ValueError(surface + ': unsupported reference image source')
                resource = resources.setdefault(src, {'src': src, 'uses': []})
                resource['uses'].append({'surface': surface, 'collection': field,
                    'id': image.get('id'), 'source_url': image.get('source_url'),
                    'attribution': image.get('attribution'), 'caption': image.get('caption')})

    for identifier in sorted(investigations):
        if identifier not in by_id:
            raise ValueError('Additional investigation missing from catalogue: ' + identifier)
        collect(detail(curriculum, by_id[identifier])['radiology_reference'], 'reporting:' + identifier)
    for identifier in sorted(modules):
        node = curriculum.node(identifier)
        if not node:
            raise ValueError('MSK curriculum surface is missing: ' + identifier)
        reference = node.get('radiology_reference')
        if reference:
            collect(reference, 'lesson:' + identifier)
    return {'surfaces': surfaces, 'images': [resources[key] for key in sorted(resources)]}


def license_issues(asset, root):
    source = asset.get('source', {})
    license_info = source.get('license', {})
    if not (source.get('url') and license_info.get('url')
            and license_info.get('commercial_use') is True
            and license_info.get('redistribution') is True
            and license_info.get('review_status') == 'verified'
            and license_info.get('attribution')):
        return ['commercial_rights_unverified']
    evidence = license_info.get('evidence_path')
    if not isinstance(evidence, str) or not evidence:
        return ['rights_evidence_missing']
    path = (root / evidence).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file():
        return ['rights_evidence_missing']
    expected = license_info.get('evidence_sha256')
    if expected and hashlib.sha256(path.read_bytes()).hexdigest() != expected:
        return ['rights_evidence_changed']
    return []


def audit_reference_image_rights(inventory, evidence, root):
    """Rights approval does not grant anatomical or clinical approval."""
    if inventory is None:
        return {'inspected': False, 'rights_ready': False, 'surfaces': [],
                'counts': {}, 'images': [], 'reason': 'runtime_reference_images_not_inspected'}
    root = Path(root)
    images = inventory['images']
    if len({item['src'] for item in images}) != len(images):
        raise ValueError('Runtime image inventory contains repeated resources')
    assets_by_path = {}
    for asset in evidence.get('assets', []):
        if asset.get('local_path'):
            assets_by_path.setdefault(asset['local_path'], []).append(asset)
    rows = []
    for image in images:
        src = image['src']
        # Existing remote galleries have no pinning/verification at delivery.
        # Even a future permission letter cannot attest that mutable remote
        # bytes still equal the clinically reviewed source. Preserve licensed
        # source files locally before clearing this product-readiness check.
        if src.startswith('https://'):
            rows.append({**image, 'status': 'unverified', 'cleared_assets': [],
                         'issues': ['remote_reference_image_not_locally_reviewable',
                                    'no_byte_bound_runtime_rights_record']})
            continue
        if not src.startswith('/app/'):
            raise ValueError('Unsupported runtime reference source: ' + src)
        local_path = 'web/' + src.removeprefix('/app/')
        path = (root / local_path).resolve()
        if not path.is_relative_to((root / 'web').resolve()):
            raise ValueError('Runtime reference source leaves web directory')
        if not path.is_file():
            rows.append({**image, 'status': 'unverified', 'cleared_assets': [],
                         'issues': ['runtime_image_missing']})
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        matches = assets_by_path.get(local_path, [])
        candidates = {}
        for asset in matches:
            problems = license_issues(asset, root)
            if asset.get('sha256') != digest:
                problems.append('runtime_image_fingerprint_mismatch')
            candidates[asset['id']] = problems
        cleared = [identifier for identifier, issues in candidates.items() if not issues]
        rows.append({**image, 'sha256': digest, 'status': 'cleared' if cleared else 'unverified',
                     'cleared_assets': cleared, 'candidates': candidates,
                     'issues': [] if cleared else ['runtime_image_rights_unverified'] if matches else ['runtime_image_absent_from_evidence']})
    return {'inspected': True, 'rights_ready': all(row['status'] == 'cleared' for row in rows),
            'surfaces': inventory['surfaces'],
            'counts': {'images': len(rows), 'cleared': sum(row['status'] == 'cleared' for row in rows),
                       'unverified': sum(row['status'] == 'unverified' for row in rows)},
            'images': rows,
            'qualification': 'Static reference-figure rights accounting only; it does not approve clinical accuracy, every project asset, external reading or the complete product.'}
