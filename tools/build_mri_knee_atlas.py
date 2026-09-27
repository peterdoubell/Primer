#!/usr/bin/env python3
"""Package the MRI-derived knee in its own native LPS frame, never a mixed atlas."""
from __future__ import annotations
import argparse
import copy
import hashlib
import gzip
import json
from pathlib import Path
import struct
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.anatomy_sources.split_malaya_knee_components import add_components
DEST = ROOT / 'web/anatomy/msk-mri-knee'
COLORS = {'bone': '#e7d5ad', 'cartilage': '#80c4cf', 'meniscus': '#a6bacf',
          'ligament': '#d7c28b', 'tendon': '#eadac1', 'muscle': '#b97074'}
LABELS = {'bone': 'Bones', 'cartilage': 'Cartilage volumes', 'meniscus': 'Menisci',
          'ligament': 'Ligaments', 'tendon': 'Tendons', 'muscle': 'Muscles'}


def build(staged, region_name='knee'):
    if region_name not in {'knee', 'ankle'}:
        raise ValueError('Unreviewed MRI region')
    destination = ROOT / ('web/anatomy/msk-mri-' + region_name)
    url_prefix = '/app/anatomy/msk-mri-' + region_name + '/'
    source = json.loads((staged / 'manifest.json').read_text())
    if set(source['regions']) != {region_name}:
        raise ValueError('Source region does not match the requested atlas')
    if source['coordinate_system'].get('basis') != 'LPS' or source['coordinate_system'].get('units') != 'millimeters':
        raise ValueError('Native LPS millimeter registration must be verified before import')
    if source['license'] != 'CC0 1.0':
        raise ValueError('Unreviewed source license')
    destination.mkdir(parents=True, exist_ok=True)
    shared = {}
    if region_name == 'ankle' and (DEST / 'manifest.json').is_file():
        knee = json.loads((DEST / 'manifest.json').read_text())
        if knee['source_archive_sha256'] == source['source_archive_sha256']:
            shared = {part['decoded_sha256']: part for part in knee['parts'].values()}
    parts = {}
    for identifier, original in source['parts'].items():
        path = Path(original['file']).resolve()
        if not path.is_relative_to(staged.resolve()):
            raise ValueError('Source file leaves staging directory')
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() != original['sha256']:
            raise ValueError('Changed source export: ' + identifier)
        magic, vertices, indices = struct.unpack('<4sII', data[:12])
        if magic != b'BP3D' or len(data) != 12 + 24 * vertices + 4 * indices or indices % 3:
            raise ValueError('Invalid source mesh: ' + identifier)
        # Lossless transport compression preserves every retained source bit.
        # Static serving advertises gzip so browser fetch returns native bytes.
        existing = shared.get(original['sha256'])
        if existing:
            encoded = (ROOT / 'web' / existing['file'].removeprefix('/app/')).read_bytes()
            if hashlib.sha256(encoded).hexdigest() != existing['sha256']:
                raise ValueError('Shared source geometry changed after review')
            public_file = existing['file']
        else:
            encoded = gzip.compress(data, compresslevel=9, mtime=0)
            target = destination / (identifier + '.bin.gz')
            target.write_bytes(encoded)
            public_file = url_prefix + target.name
        part = {key: copy.deepcopy(value) for key, value in original.items() if key not in ('file', 'stl_file')}
        part.update({'file': public_file, 'vertices': vertices,
                     'triangles': indices // 3, 'bytes': len(encoded), 'decoded_bytes': len(data),
                     'sha256': hashlib.sha256(encoded).hexdigest(), 'decoded_sha256': original['sha256'],
                     'content_encoding': 'gzip', 'color': COLORS[part['layer']],
                     'fidelity_review': 'pending'})
        if existing:
            part['shared_binary_from'] = existing['id']
        parts[identifier] = part
    original_region = source['regions'][region_name]
    region = copy.deepcopy(original_region)
    region['parts'] = [{'id': identifier, 'layer': parts[identifier]['layer']} for identifier in original_region['parts']]
    region['layers'] = [[layer, label] for layer, label in LABELS.items() if any(p['layer'] == layer for p in parts.values())]
    margin = 60 if region_name == 'knee' else 40
    region['source_up_range'] = [region['focus_bounds'][0][2] - margin, region['focus_bounds'][1][2] + margin]
    region['lazy_layers'] = True
    manifest = copy.deepcopy(source)
    manifest.update({'parts': parts, 'regions': {region_name: region},
                     'status': 'MRI-derived source anatomy; clinical fidelity validation incomplete',
                     'viewer_notes': [
                         'MRI-derived right-knee anatomy from one adult male. All displayed components retain the same native LPS millimeter coordinates; these meshes are not fitted to or combined with the other atlas.',
                         'Cartilage is represented by segmented three-dimensional surfaces enclosing tissue, rather than painted regions on a bone. The source meniscus label combines the medial and lateral menisci; roots and horns are not independently segmented.',
                         'The source segmentation grid is approximately 1.154 × 1.154 × 1.2 mm and underwent morphological processing and joint smoothing. Surface detail is not a claim of equivalent clinical measurement accuracy. Source structures and acquisition limits remain relevant.',
                         'The source omits some ligaments and tendons. A complete reporting atlas and independent clinical fidelity review are still required. The separate broader atlas can provide additional reference structures, but the two datasets are not co-registered.',
                         source['attribution'] + ' Source data: CC0 1.0. Conversion and any exact zero-area facet omissions are documented in the provenance manifest.'
                     ]})
    if region_name == 'ankle':
        manifest['viewer_notes'] = [
            'MRI-derived right ankle bones, Achilles tendon and source muscle units from one adult male. Native LPS millimeter coordinates are preserved; this source is not fitted to or combined with the broader atlas.',
            'The Achilles tendon is a separate source segmentation. Other muscle units are not separately labelled distal tendons or tendon sheaths. Ankle ligaments, cartilage, nerves, vessels and bursae are not supplied by this source subset.',
            'Source sampling is approximately 1.154 × 1.154 × 1.2 mm with morphological processing and smoothing. Small disconnected/non-manifold source components are retained; detailed accuracy and reporting completeness remain unverified.',
            'The initial view focuses on the ankle. Full structures removes the view crop, including the complete Achilles and available muscle-unit geometry. No ankle-specific MRI image stack is offered by this viewer.',
            source['attribution'] + ' Source data: CC0 1.0. Original coordinates and nonempty surfaces are preserved; exact empty-facet omissions are recorded in the manifest.'
        ]
    manifest['coordinate_system']['display_basis'] = 'native-lps-to-x-left-y-superior-z-anterior'
    if region_name == 'knee':
        add_components(manifest, destination)
    for key in ('local_image', 'local_segmentation'):
        manifest.get('clinical_image_pair', {}).pop(key, None)
    for section, key, filename in [('author_review_claim', 'evidence_file', 'SOURCE-README.txt'),
                                    ('omission_evidence', 'file', 'omitted-empty-facets.json')]:
        if manifest.get(section, {}).get(key):
            evidence = Path(manifest[section][key]).resolve()
            if not evidence.is_relative_to(staged.parent.resolve()) or not evidence.is_file():
                raise ValueError('Source evidence leaves the acquisition directory')
            shutil.copyfile(evidence, destination / filename)
            manifest[section][key] = url_prefix + filename
    if manifest.get('registration_validation', {}).get('evidence_file'):
        evidence = Path(manifest['registration_validation']['evidence_file']).resolve()
        if not evidence.is_relative_to(staged.parent.resolve()) or not evidence.is_file():
            raise ValueError('Registration evidence leaves acquisition directory')
        shutil.copyfile(evidence, destination / 'registration-evidence.json')
        manifest['registration_validation']['evidence_file'] = url_prefix + 'registration-evidence.json'
    (destination / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    text = '# MRI-derived ' + region_name + ' reference\n\n' + '\n\n'.join(manifest['viewer_notes']) + '\n\n'
    text += 'Source: ' + source['source_url'] + '\n\nLicense: ' + source['license_url'] + '\n\n'
    text += 'Acquisition archive SHA-256: `' + source['source_archive_sha256'] + '`.\n\n' + source['adaptations'] + '\n'
    (destination / 'ATTRIBUTION.md').write_text(text)
    print('Packaged', len(parts), 'registered MRI-derived', region_name, 'objects,', sum(p['triangles'] for p in parts.values()), 'triangles')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--staged', type=Path, required=True)
    parser.add_argument('--region', choices=('knee', 'ankle'), default='knee')
    args = parser.parse_args()
    build(args.staged.resolve(), args.region)
