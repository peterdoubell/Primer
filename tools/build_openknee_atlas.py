#!/usr/bin/env python3
"""Stage the reviewed Open Knee(s) oks003 source assembly for viewer evaluation.

This command never publishes into web/. It retains every original STL float32
corner and facet normal bit, source triangle order, and native RAS/mm frame.
No fitting, smoothing, removal, clinical approval, or raw MRI publication.
"""
from __future__ import annotations

import argparse
from array import array
import gzip
import hashlib
import json
import math
from pathlib import Path
import struct
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = Path('/tmp/primer-msk-sources/openknee-public-pass/oks003-native')
DEFAULT_DEST = DEFAULT_SOURCE.parent / 'viewer-staged'
PREFIX = '/app/anatomy/openknee-oks003/'
ASSEMBLY_SHA = 'ec128b6395652ec79e5d32ac175dd58fa5c4372680d25354ae6a666d310708a6'
# Exact acquired repository notice, not the independent MRI archive's CC BY 4.0.
LICENSE_SHA = 'f3dae5322470eb534be7e6e22ba7e067617ffce697df9390c68a293389dcd998'
METADATA_SHA = 'a4591361ab61597e59d79faa66c74a0c3fe799e5d382362410a0c7f410e2d20f'
LICENSE = 'CC BY-SA 3.0 Unported'
SOURCE_URL = 'https://simtk.org/svn/openknee/oks/oks003/'
PARTS = {
    'FMB': ('Femur', 'bone'), 'TBB': ('Tibia', 'bone'),
    'FBB': ('Fibula', 'bone'), 'PTB': ('Patella', 'bone'),
    'FMC': ('Femoral cartilage', 'cartilage'),
    'TBC-L': ('Lateral tibial cartilage', 'cartilage'),
    'TBC-M': ('Medial tibial cartilage', 'cartilage'),
    'PTC': ('Patellar cartilage', 'cartilage'),
    'MNS-M': ('Medial meniscus', 'meniscus'), 'MNS-L': ('Lateral meniscus', 'meniscus'),
    'ACL': ('Anterior cruciate ligament', 'ligament'),
    'PCL': ('Posterior cruciate ligament', 'ligament'),
    'MCL': ('Medial collateral ligament', 'ligament'),
    'LCL': ('Lateral collateral ligament', 'ligament'),
    'PTL': ('Patellar tendon (source: patellar ligament)', 'tendon'),
    'QAT': ('Quadriceps tendon', 'tendon'),
}
COLORS = {'bone': '#e7d5ad', 'cartilage': '#80c4cf', 'meniscus': '#a6bacf',
          'ligament': '#d7c28b', 'tendon': '#eadac1'}
LABELS = {'bone': 'Bones', 'cartilage': 'Cartilage volumes', 'meniscus': 'Menisci',
          'ligament': 'Ligaments', 'tendon': 'Tendons'}
SOURCE_IMAGES = {
    'oks003-general-mri.nii': (97075552, 'e0566dd0a81db02e3d6fcfc29ce0d78afe4337c2fb5b0375ea9e0a04595cf5cb'),
    'oks003-cartilage-mri.nii': (102760800, '9266f03edaff042932cdae09f7c308a80e4106e3790f32c4004c52d6edc67812'),
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def checked(path, expected):
    raw = path.read_bytes()
    if sha(raw) != expected:
        raise ValueError('Source fingerprint changed: ' + str(path))
    return raw


def encode_stl(raw):
    """Losslessly rearrange binary STL records into the planar BP3D protocol."""
    count = struct.unpack_from('<I', raw, 80)[0]
    if len(raw) != 84 + 50 * count or not count:
        raise ValueError('Expected complete binary source STL')
    positions, normals = bytearray(), bytearray()
    bounds = [[math.inf] * 3, [-math.inf] * 3]
    for i in range(count):
        start = 84 + i * 50
        normal = raw[start:start + 12]
        corners = raw[start + 12:start + 48]
        # Copy bytes directly; do not regenerate normals, quantize or weld.
        positions.extend(corners)
        normals.extend(normal * 3)
        values = struct.unpack('<9f', corners)
        if not all(map(math.isfinite, values + struct.unpack('<3f', normal))):
            raise ValueError('Nonfinite source facet')
        for corner in range(3):
            for axis in range(3):
                value = values[corner * 3 + axis]
                bounds[0][axis] = min(bounds[0][axis], value)
                bounds[1][axis] = max(bounds[1][axis], value)
    indices = array('I', range(count * 3))
    if sys.byteorder != 'little':
        indices.byteswap()
    if indices.itemsize != 4:
        raise ValueError('Unexpected uint32 width')
    payload = struct.pack('<4sII', b'BP3D', count * 3, count * 3)
    payload += positions + normals + indices.tobytes()
    verify_payload(raw, payload)
    return payload, count, bounds


def verify_payload(source, payload):
    count = struct.unpack_from('<I', source, 80)[0]
    magic, nv, ni = struct.unpack_from('<4sII', payload)
    if magic != b'BP3D' or nv != count * 3 or ni != count * 3 or len(payload) != 12 + nv * 24 + ni * 4:
        raise ValueError('Invalid binary protocol')
    norm_start, index_start = 12 + nv * 12, 12 + nv * 24
    for i in range(count):
        src = 84 + i * 50
        if payload[12 + i * 36:12 + (i + 1) * 36] != source[src + 12:src + 48]:
            raise ValueError('Source corner bits/order changed')
        if payload[norm_start + i * 36:norm_start + (i + 1) * 36] != source[src:src + 12] * 3:
            raise ValueError('Source facet normal bits/order changed')
        if struct.unpack_from('<3I', payload, index_start + i * 12) != (i * 3, i * 3 + 1, i * 3 + 2):
            raise ValueError('Source winding/order changed')


def validate_paired_audit(evidence, parts, masks):
    """Bind technical correspondence evidence to these exact sources, not accuracy."""
    if (evidence.get('specimen') != 'oks003'
            or evidence.get('no_fitted_transform') is not True
            or evidence.get('no_source_geometry_edits') is not True):
        raise ValueError('Paired evidence must retain the original oks003 source frame/geometry')
    images = evidence.get('images', [])
    if len(images) != 2 or {r.get('filename') for r in images} != set(SOURCE_IMAGES):
        raise ValueError('Paired evidence must identify both acquired MRI sources')
    for image in images:
        if (image.get('bytes'), image.get('sha256')) != SOURCE_IMAGES[image['filename']]:
            raise ValueError('Paired evidence MRI fingerprint differs from acquisition')
    rows = evidence.get('structures', [])
    required = set(PARTS) - {'TBC-L', 'TBC-M'}
    if len(rows) != 14 or {r.get('id') for r in rows} != required or set(masks) != required:
        raise ValueError('Expected exactly 14 unambiguous source-mask records')
    by_source = {p['source_id']: p for p in parts.values()}
    expected_planes = {(image, plane) for image in SOURCE_IMAGES
                       for plane in ('Sagittal', 'Coronal', 'Axial')}
    dice = []
    for row in rows:
        part, mask = by_source[row['id']], masks[row['id']]
        if row.get('mesh_file') != part['source_name'] or row.get('mesh_sha256') != part['source_sha256']:
            raise ValueError('Paired evidence mesh binding changed: ' + row['id'])
        source_mask = row.get('mask', {})
        if any(source_mask.get(field) != mask[expected] for field, expected in
               [('filename', 'mask_name'), ('sha256', 'sha256'), ('bytes', 'bytes')]):
            raise ValueError('Paired evidence mask binding changed: ' + row['id'])
        planes = row.get('planes', [])
        if len(planes) != 6 or {(r.get('image'), r.get('plane')) for r in planes} != expected_planes:
            raise ValueError('Each source structure needs all six declared-plane comparisons')
        for plane in planes:
            score = plane.get('mask_mesh_dice')
            if type(score) not in (int, float) or not math.isfinite(score) or not 0 <= score <= 1:
                raise ValueError('Invalid source mask/mesh comparison metric')
            dice.append(score)
    return {
        'scope': 'Source mask-to-mesh correspondence in declared NIfTI RAS coordinates across '
                 'two source MRI volumes; not independent tissue-boundary or clinical-accuracy validation.',
        'source_mask_matches': 14, 'source_images': 2, 'section_comparisons': 84,
        'sampled_section_dice_range': [min(dice), max(dice)],
        'unresolved_mask_source_ids': ['TBC-L', 'TBC-M'],
        'no_fitted_transform': True, 'no_source_geometry_edits': True,
        'clinical_alignment_approval': False,
    }


def build(source=DEFAULT_SOURCE, destination=DEFAULT_DEST, paired_audit=None):
    source, destination = source.resolve(), destination.resolve()
    if destination.is_relative_to((ROOT / 'web').resolve()):
        raise ValueError('This builder stages only; publication is a separate reviewed step')
    assembly_raw = checked(source / 'author-assembly.xml', ASSEMBLY_SHA)
    license_raw = checked(source / 'license.txt', LICENSE_SHA)
    metadata_raw = checked(source / 'source-metadata.xml', METADATA_SHA)
    assembly = ET.fromstring(assembly_raw)
    if [n.tag for n in assembly] != list(PARTS):
        raise ValueError('The source assembly is not the reviewed 16-part selection')
    acquisition = json.loads((source / 'acquisition.json').read_text())
    original = {p['id']: p for p in acquisition['parts']}
    audit = {p['id']: p for p in json.loads((source / 'geometry-audit.json').read_text())['parts']}
    mask_bindings = json.loads((source / 'assembly-mask-bindings.json').read_text())
    masks = {p['part_id']: p for p in mask_bindings['downloaded_masks']}
    held = {p['part_id']: p for p in mask_bindings['held_mappings']}
    if set(original) != set(PARTS) or set(masks) | set(held) != set(PARTS) or set(masks) & set(held):
        raise ValueError('Incomplete or ambiguous source inventory')
    if set(held) != {'TBC-L', 'TBC-M'}:
        raise ValueError('Unexpected mask-mapping change requires source review')
    destination.mkdir(parents=True, exist_ok=True)
    parts, proof = {}, []
    for node in assembly:
        key = node.tag
        item = original[key]
        if item['filename'] != node.findtext('file') or Path(item['filename']).name != item['filename']:
            raise ValueError('Unreviewed source filename: ' + key)
        raw = checked(source / item['filename'], item['sha256'])
        stats = audit[key]
        if stats['sha256'] != item['sha256'] or stats['exact_zero_area_facet_indices']:
            raise ValueError('Geometry audit does not match source')
        payload, count, bounds = encode_stl(raw)
        if count != stats['source_triangles'] or bounds != stats['bounds_native']:
            raise ValueError('Source geometry and audit differ')
        identifier = 'oks003-' + key.lower()
        filename = identifier + '.bin.gz'
        encoded = gzip.compress(payload, compresslevel=9, mtime=0)
        (destination / filename).write_bytes(encoded)
        verify_payload(raw, gzip.decompress((destination / filename).read_bytes()))
        name, layer = PARTS[key]
        part = {
            'id': identifier, 'name': name, 'layer': layer, 'regions': ['knee'],
            'source_id': key, 'source_name': item['filename'], 'source_url': item['url'],
            'source_sha256': item['sha256'], 'source_bytes': len(raw),
            'source_triangles': count, 'triangles': count, 'vertices': count * 3,
            'export_vertices': count * 3, 'bounds': bounds,
            'file': PREFIX + filename, 'content_encoding': 'gzip',
            'bytes': len(encoded), 'sha256': sha(encoded),
            'decoded_bytes': len(payload), 'decoded_sha256': sha(payload),
            'normals_preserved_exactly': True, 'triangle_order_preserved_exactly': True,
            'source_float32_position_bits_preserved': True,
            'geometry_transform': 'identity; native RAS millimeter positions retained',
            'world_transform_columns': [[1, 0, 0], [0, 1, 0], [0, 0, 1], [0, 0, 0]],
            'component_count': stats['face_components_shared_exact_edges'],
            'boundary_edges': stats['boundary_edges'], 'nonmanifold_edges': stats['nonmanifold_edges'],
            'omitted_source_facet_indices': [], 'license': LICENSE,
            'color': COLORS[layer], 'fidelity_review': 'pending',
        }
        if key in masks:
            mask = masks[key]
            part['source_segmentation'] = {
                'filename': mask['mask_name'], 'source_url': mask['url'],
                'sha256': mask['sha256'], 'bytes': mask['bytes'],
                'choice_basis': mask['choice_basis'],
                'exported_grid_mm': mask['nifti_header']['pixdim'][1:4],
                'correspondence_status': 'source filename correspondence; independent tissue-boundary validation incomplete',
            }
        else:
            part['source_segmentation'] = {
                'correspondence_status': held[key]['status'], 'reason': held[key]['reason'],
            }
        parts[identifier] = part
        proof.append({'id': identifier, 'source_sha256': part['source_sha256'],
                      'decoded_sha256': part['decoded_sha256'], 'transport_sha256': part['sha256'],
                      'triangles': count, 'positions_normals_and_facet_order_byte_exact': True})
    if sum(p['triangles'] for p in parts.values()) != 307024:
        raise ValueError('Unexpected source facet total')
    focus_parts = [p for p in parts.values() if p['layer'] != 'bone']
    bounds = [[min(p['bounds'][0][axis] for p in focus_parts) for axis in range(3)],
              [max(p['bounds'][1][axis] for p in focus_parts) for axis in range(3)]]
    attribution = ('Open Knee(s) Development Team; Chokhandre S, Schwartz A, Klonowski E, '
                   'Landis B, Erdemir A. Open Knee(s): A Free and Open Source Library of '
                   'Specimen-Specific Models and Related Digital Assets for Finite Element '
                   'Analysis of the Knee Joint (2022/2023), doi:10.1007/s10439-022-03074-0. '
                   'Source repository revision 3413; oks003 AGS assembly.')
    notes = [
        'MRI-derived left-knee reference from one 25-year-old female cadaveric donor (oks003). '
        'Native RAS millimeter coordinates are retained. This source is not co-registered with the other atlases.',
        'Separate source objects represent bones, cartilage, menisci, cruciate/collateral ligaments, '
        'patellar tendon and the covered quadriceps tendon segment. Roots, bundles, attachment fibres, '
        'MCL layers, and other fine stabilizers are not separately delineated.',
        'The source uses multiple MRI grids: general imaging at 0.5 mm isotropic and cartilage imaging '
        'at approximately 0.35 × 0.35 × 0.7 mm. Surfaces underwent source smoothing/reconstruction '
        'and remeshing. Mesh density does not establish clinical measurement accuracy.',
        'The source radiologist reported no identified tissue damage for this specimen. That author '
        'assessment and source correspondence checks are not independent clinical certification. '
        'These teaching surfaces are not a diagnostic MRI example or a complete reporting atlas.',
        attribution + ' Geometry: CC BY-SA 3.0 Unported. Viewer conversion preserves every source '
        'facet, coordinate and facet normal; no fitting, smoothing or anatomy removal was applied.',
    ]
    manifest = {
        'schema_version': 1, 'provider': 'openknee-oks003',
        'status': 'MRI-derived teaching source; clinical fidelity validation incomplete',
        'dataset': 'Open Knee(s) oks003 — native left-knee source assembly',
        'source_doi': '10.18735/b0zv-n395', 'source_url': SOURCE_URL,
        'source_repository_revision': 3413,
        'source_assembly': {'url': SOURCE_URL + 'Model/Connectivity.xml',
                            'sha256': ASSEMBLY_SHA, 'file': PREFIX + 'SOURCE-ASSEMBLY.xml'},
        'license': LICENSE, 'license_url': 'https://creativecommons.org/licenses/by-sa/3.0/',
        'converted_geometry_license': {
            'name': LICENSE, 'url': 'https://creativecommons.org/licenses/by-sa/3.0/',
            'scope': 'All converted mesh files and derived geometry in this provider are '
                     'distributed under the same CC BY-SA 3.0 Unported terms as the source geometry.',
        },
        'source_license': {'url': 'https://simtk.org/svn/openknee/license.txt',
                           'sha256': LICENSE_SHA, 'file': PREFIX + 'SOURCE-LICENSE.txt'},
        'attribution': attribution,
        'specimen': {'id': 'oks003', 'side': 'left', 'sex': 'female', 'age_years': 25,
                     'height_m': 1.73, 'mass_kg': 68.0, 'cadaveric': True,
                     'metadata_url': SOURCE_URL + 'metadata.xml',
                     'metadata_sha256': METADATA_SHA},
        'coordinate_system': {
            'basis': 'RAS', 'x_positive': 'patient right', 'y_positive': 'anterior',
            'z_positive': 'superior', 'units': 'millimeters', 'unit_meters': .001,
            'display_basis': 'native-ras-to-x-left-y-superior-z-anterior',
            'registration': 'Identity source image frame; no fitted transform or registration to another atlas.',
            'basis_evidence': 'Source NIfTI qform/sform coordinates and matching source mesh axes; '
                              'source SOP requires geometry in the imaging coordinate system.',
            'units_evidence': 'NIfTI millimeter units and author SOP page 15, millimeter STL export.',
        },
        'sampling_limits': {
            'general_mri_grid_mm': [.5, .5, .5],
            'cartilage_mri_grid_mm': [.3515625, .3515625, .6999969482421875],
            'effective_spatial_resolution': 'Not established by surface facet count or exported grid alone.',
            'author_processing': 'Manual segmentation followed by tissue-dependent smoothing, '
                                 'VCG reconstruction, Iso Parameterization/remeshing and optional repairs. '
                                 'The author SOP gives starting parameters, not exact per-file operation logs.',
            'source_sop_url': 'https://simtk.org/docman/view.php/1061/11481/CC-OKS-MD-specifications.pdf',
            'source_sop_sha256': '0ec1bfa5838ae5a8e80b6024377cea009e98b3d0111aeb1519b5a21c120b0de3',
            'source_sop_pages': [13, 14, 15, 16],
        },
        'author_review_claim': {
            'statement': 'The published data descriptor Table 3 reports grade-zero abnormalities and '
                         'normal menisci/no ligament damage for oks003, assessed by the source radiologist.',
            'source_url': 'https://pmc.ncbi.nlm.nih.gov/articles/PMC7890148/',
            'independent_clinical_approval': False,
        },
        'adaptations': 'Byte-exact rearrangement of binary STL float32 corners/facet normals to planar '
                       'BP3D buffers, sequential triangle indices, and lossless gzip transport. '
                       'No coordinate conversion, fitting, smoothing, decimation or facet omission.',
        'parts': parts,
        'regions': {'knee': {
            'title': 'Open Knee(s) left knee', 'side': 'left',
            'parts': [{'id': p['id'], 'layer': p['layer']} for p in parts.values()],
            'focus_bounds': bounds, 'focus_bounds_source_objects': [p['source_id'] for p in focus_parts],
            'source_up_range': [bounds[0][2] - 10, bounds[1][2] + 10],
            'layers': [[layer, label] for layer, label in LABELS.items()], 'lazy_layers': True,
        }},
        'clinical_image_pair': {'available': False, 'independent_clinical_validation': False,
                                 'registration_status': 'Source images and masks retained offline for '
                                                        'correspondence audit; no diagnostic image pair published.'},
        'registration_validation': {'scope': 'Source coordinates preserved; independent '
                                             'image-to-tissue boundary validation incomplete',
                                    'clinical_alignment_approval': False},
        'limitations': notes[:4] + [
            'Tibial-cartilage mask variant relationships remain explicitly unresolved.',
            'Global self-intersections were not checked; clean edge topology is not anatomical accuracy.',
        ],
        'viewer_notes': notes,
    }
    preservation = {'status': 'exact source geometry transport verification; not clinical approval',
                    'parts': proof, 'triangles': 307024, 'omitted_facets': 0,
                    'native_coordinates_unchanged': True}
    preservation_raw = (json.dumps(preservation, indent=2) + '\n').encode()
    (destination / 'geometry-preservation.json').write_bytes(preservation_raw)
    manifest['geometry_preservation'] = {'file': PREFIX + 'geometry-preservation.json',
                                         'sha256': sha(preservation_raw)}
    if paired_audit is not None:
        evidence_raw = Path(paired_audit).read_bytes()
        registration = validate_paired_audit(json.loads(evidence_raw), parts, masks)
        registration.update(evidence_file=PREFIX + 'registration-evidence.json',
                            evidence_sha256=sha(evidence_raw))
        manifest['registration_validation'] = registration
        (destination / 'registration-evidence.json').write_bytes(evidence_raw)
    for filename, raw in [('SOURCE-LICENSE.txt', license_raw), ('SOURCE-ASSEMBLY.xml', assembly_raw),
                          ('SOURCE-METADATA.xml', metadata_raw)]:
        (destination / filename).write_bytes(raw)
    (destination / 'manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n')
    credit = '# Open Knee(s) oks003 source anatomy\n\n' + '\n\n'.join(notes)
    credit += '\n\nSource: ' + SOURCE_URL + '\n\nLicense: ' + manifest['license_url']
    credit += ('\n\nAll converted mesh files and derived geometry in this provider are distributed '
               'under the same Creative Commons Attribution-ShareAlike 3.0 Unported license '
               '(CC BY-SA 3.0) as the original source geometry. Attribution and ShareAlike '
               'requirements apply. The separate source MRI archive carries CC BY 4.0; '
               'that notice does not replace the geometry license. No MRI or mask payload '
               'is included in this viewer package.')
    credit += '\n\n' + manifest['adaptations'] + '\n'
    (destination / 'ATTRIBUTION.md').write_text(credit)
    print(json.dumps({'destination': str(destination), 'parts': len(parts),
                      'triangles': 307024, 'transport_bytes': sum(p['bytes'] for p in parts.values()),
                      'all_source_positions_normals_and_facet_order_exact': True}))
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=DEFAULT_SOURCE)
    parser.add_argument('--output', type=Path, default=DEFAULT_DEST)
    parser.add_argument('--paired-audit', type=Path,
                        help='Optional exact-source technical correspondence JSON; never clinical approval')
    args = parser.parse_args()
    build(args.source, args.output, args.paired_audit)
