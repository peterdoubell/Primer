"""Reviewed partial source references, separate from complete or patient evidence."""
from collections import defaultdict
from copy import deepcopy
import argparse
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urlencode

from tools.anatomy_sources.build_soft_tissue_neck_inventory import ROOT, OUTPUT as REQUIREMENTS, validate as validate_inventory

OUTPUT = 'data/radiology/descriptor-requirements/soft-tissue-neck-source-links.json'
ZANATOMY = 'web/anatomy/zanatomy-salivary'
SEGTHY = 'web/anatomy/segthy-001'
Z_MATCHES = {
    'parotid': ('parotid-gland', 'Parotid gland', 'gland', 'gland_body'),
    'submandibular': ('submandibular-gland', 'Submandibular gland', 'gland', 'gland_body'),
    'parotid_duct': ('parotid-duct', 'Parotid duct', 'duct', 'salivary_duct'),
    'submandibular_duct': ('submandibular-duct', 'Submandibular duct', 'duct', 'salivary_duct'),
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def build(root=ROOT):
    inventory = validate_inventory(read(root / REQUIREMENTS), root)
    z_path, us_path = root / ZANATOMY / 'surfaces.json', root / SEGTHY / 'manifest.json'
    pin = re.search(r'data-surfaces-sha256="([0-9a-f]{64})"', (root / ZANATOMY / 'index.html').read_text())
    if not pin or sha(z_path) != pin[1]:
        raise ValueError('Atlas reader metadata pin differs')
    us_pin = re.search(r"fingerprint\(bytes\) !== '([0-9a-f]{64})'", (root / SEGTHY / 'viewer.js').read_text())
    if not us_pin or sha(us_path) != us_pin[1]:
        raise ValueError('Native reader metadata pin differs')
    objects = {row['label']: row for row in read(z_path)}
    us = read(us_path)
    links = []
    for target in inventory['anatomical_requirements']:
        _, structure, side = target['id'].split('.')
        if structure in Z_MATCHES:
            slug, source_name, group, role = Z_MATCHES[structure]
            key = side + '-' + slug
            row = objects[key]
            if (row['name'] != side.title() + ' ' + source_name.lower() or row['side'] != side
                    or row['group'] != group or target['tissue_class'] != role):
                raise ValueError('Atlas source object/side/anatomy role differs')
            if sha(root / ZANATOMY / row['file']) != row['packedSHA256']:
                raise ValueError('Atlas source surface changed')
            for kind, anchor in [('model', 'surface'), ('schematic', 'section')]:
                links.append(dict(id='z-salivary-' + key + '-' + kind,
                    requirement_id=target['id'], representation=kind, side=side,
                    anatomy_role=role, status='partial', source_id='zanatomy-salivary',
                    source_url='https://github.com/Z-Anatomy/Models-of-human-anatomy/tree/ded1a55381328f3f242426f0e8e711c5fca62c14',
                    license='CC BY-SA 4.0', license_url='https://creativecommons.org/licenses/by-sa/4.0/',
                    attribution_url='/app/anatomy/zanatomy-salivary/LICENSE.txt',
                    source_object=row['sourceObject'], source_structure_id=key, source_name=row['name'],
                    source_group=group, source_metadata_sha256=sha(z_path),
                    payload_sha256=row['packedSHA256'], triangles=row['triangles'],
                    href='/app/anatomy/zanatomy-salivary/index.html?structure=' + key + '#' + anchor,
                    displayed_representation='source_surface' if kind == 'model' else 'source_triangle_plane_intersection',
                    scope='Modelled duct exterior/course only.' if group == 'duct' else 'Named gross source gland body only.',
                    limitations='Shared atlas geometry across sides; no full target extent, lumen, lesion, flow or current-patient claim.',
                    complete_extent=False, clinical_approval=False, current_patient_registration=False))
        elif structure == 'thyroid_lobe':
            case, = [row for row in us['cases'] if row['side'].lower() == side]
            label, = [row for row in case['labels'] if row['code'] == 1]
            if label['name'] != side.title() + ' thyroid lobe' or target['tissue_class'] != 'gland_body':
                raise ValueError('Native source label/side/anatomy role differs')
            if sha(root / SEGTHY / label['mesh']['file']) != label['mesh']['sha256']:
                raise ValueError('Native source surface changed')
            for kind, anchor in [('clinical_image', 'ultrasound'), ('model', 'surface')]:
                query = urlencode({'volume': case['id'], 'label': 1, 'representation': kind})
                links.append(dict(id='segthy-' + side + '-thyroid-' + kind,
                    requirement_id=target['id'], representation=kind, side=side,
                    anatomy_role='gland_body', status='partial', source_id='segthy-001',
                    source_url=us['source'], publication_url=us['article'], license=us['license'],
                    license_url=us['source'], attribution_url='/app/anatomy/segthy-001/ATTRIBUTION.md',
                    source_structure_id=case['id'] + ':1', source_name=label['name'],
                    source_volume=case['id'], source_label=1, source_metadata_sha256=sha(us_path),
                    source_image_payload_sha256=case['sources']['image']['payloadSHA256'],
                    source_mask_payload_sha256=case['sources']['mask']['payloadSHA256'],
                    payload_sha256=case['sources']['image']['payloadSHA256'] if kind == 'clinical_image' else label['mesh']['sha256'],
                    payload_role='native_source_image' if kind == 'clinical_image' else 'source_mask_surface',
                    source_mesh_packed_sha256=label['mesh']['sha256'], triangles=label['mesh']['triangles'],
                    href='/app/anatomy/segthy-001/index.html?' + query + '#' + anchor,
                    displayed_representation='unmarked_native_grayscale' if kind == 'clinical_image' else 'source_mask_interface',
                    scope='One released manual thyroid-lobe label and its acquired source sweep.',
                    limitations='Separate acquisition per side; no full target extent, capsule, nodule, flow or current-patient claim.',
                    complete_extent=False, clinical_approval=False, current_patient_registration=False))
    return dict(schema_version=1, investigation_id=inventory['investigation_id'],
        requirements_sha256=sha(root / REQUIREMENTS), clinical_approval=False, complete_set_claim=False,
        policy='Only exact side, structure, requested representation and anatomy_role matches count as source-specific partial references. No union of partial references establishes complete evidence.',
        source_reader_sha256={name: sha(root / name) for name in [ZANATOMY + '/controls.js', ZANATOMY + '/planes.mjs',
            SEGTHY + '/viewer.js', SEGTHY + '/source-selection.mjs']},
        links=links,
        uncounted_contexts=[
            {'source_id': 'salivary-us-2025', 'reason': 'Healthy A/B images have no reported side or plane; no sided target assignment.'},
            {'source_id': 'segthy-001', 'reason': 'Generic carotid/jugular class names do not establish common-carotid/internal-jugular subtypes.'},
            {'source_id': 'segthy-001', 'reason': 'No separate isthmus label or separately selected label-only schematic is exposed.'},
            {'source_id': 'cervical-node-figures', 'reason': 'Independent evidence work; no figures are loaded or credited by this registry.'}])


def validate(data, root=ROOT):
    expected = build(root)
    if data != expected:
        raise ValueError('Partial source links differ from exact reviewed object, side, anatomy role or native selector')
    targets = {row['id']: row for row in read(root / REQUIREMENTS)['anatomical_requirements']}
    if len({row['id'] for row in data['links']}) != len(data['links']):
        raise ValueError('Repeated partial source identity')
    for row in data['links']:
        target = targets[row['requirement_id']]
        if (row['side'] != target['laterality'] or row['anatomy_role'] != target['tissue_class']
                or row['representation'] not in target['required_representations']
                or row['status'] != 'partial' or row['clinical_approval'] is not False
                or row['complete_extent'] is not False or row['current_patient_registration'] is not False):
            raise ValueError('Partial source claim leaves its exact scope')
    return data


def apply_partial_sources(requirements, links):
    by_target = defaultdict(list)
    for link in links:
        by_target[link['requirement_id'], link['representation']].append(link)
    result = deepcopy(requirements)
    for row in result:
        source_links = by_target.get((row['structure_id'], row['kind']), [])
        if source_links:
            row['complete_fidelity_status'] = row['status']
            row['source_links'] = deepcopy(source_links)
            if row['status'] != 'verified':
                row['status'] = 'partial'
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--write', action='store_true'); args = parser.parse_args()
    data = build()
    if args.write: (ROOT / OUTPUT).write_text(json.dumps(data, indent=2) + '\n')
    else: validate(read(ROOT / OUTPUT))
    print(json.dumps({'partial_links': len(data['links']), 'clinical_approval': False}))


if __name__ == '__main__':
    main()
