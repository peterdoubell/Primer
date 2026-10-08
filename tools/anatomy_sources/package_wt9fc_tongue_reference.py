#!/usr/bin/env python3
"""Package four unchanged distributed WT9FC label surfaces as a partial reference.

Default execution only writes dedicated package/proof paths. The explicit
--apply-registry flag additionally registers the package for the swallowing reader.
Neither mode grants anatomical coverage or clinical approval.
"""
import argparse
import gzip
import hashlib
import json
import struct
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
ATLAS = 'wt9fc-sub007'
FAMILY = 'tongue-source'
INV = 'ra.swallowing'
SOURCE = 'https://osf.io/wt9fc/'
GRANT = 'https://creativecommons.org/publicdomain/zero/1.0/'
PROOF_REL = Path('docs/wt9fc-tongue-source-review')
IMAGE_NAME = 'sub-007_segID-001_T2w.nii.gz'
LABEL_NAME = 'sub-007_segID-001_T2w_labels.nii.gz'
LABELS = {
    1: ('transverse-vertical', 'transverse / vertical (combined)', '#2eb48b'),
    2: ('superior-longitudinal', 'superior longitudinal', '#e37d42'),
    3: ('inferior-longitudinal', 'inferior longitudinal', '#8d95d4'),
    4: ('genioglossus', 'genioglossus', '#c669a9'),
}
ATTRIBUTION = (
    'Ribeiro, F. L. and Shaw, T. B. An annotated MRI dataset for the study of '
    'the human tongue musculature. OSF WT9FC, DOI 10.17605/OSF.IO/WT9FC. '
    'Dataset CC0 1.0 Universal; the separately restricted article supplies no '
    'reused graphics or captions. Adaptation: unchanged distributed label '
    'interfaces, float32 transport, display normals and declared MRI window.'
)
NOTES = [
    'One source BeLong case, sub-007_segID-001; source demographic age 33.12 '
    'years and sex female. The publication describes the released cohort as '
    'non-neurodegenerative healthy controls; the individual spreadsheet has '
    'no diagnosis field. This does not independently establish normal '
    'anatomy, swallowing function or the current patient.',
    'These are distributed processed source data: study-template registration, '
    'mouth ROI masking/cropping, and publisher 1 mm Gaussian smoothing of '
    'labels. They are not an unmodified native acquisition. The original '
    'distributed MRI and label samples, own sforms and registration affine '
    'are preserved separately.',
    'Source grid 64×320×320 with declared 0.8 mm isotropic sample pitch. '
    'MRI stored int16 samples have original slope 0.05391012504696846 and '
    'intercept 1766.5269775390625; these are source-scaled signal values, '
    'not calibrated physical tissue measurements. The mask has its own '
    'slightly different sform; no replacement affine or fitted registration '
    'is applied. Camera labels use source coordinates.',
    'All four distributed labels and all 67,508 triangles are retained. '
    'Inferior longitudinal remains two separate source components; '
    'transverse and vertical are a single combined publisher label, not '
    'individually resolved muscles. No extra smoothing, capping, padding, '
    'decimation, repair, mirroring, component removal or relabelling.',
    'Hyoglossus, styloglossus, palatoglossus, muscle fibres, neural and '
    'vascular supply, fine mucosal interfaces, palate, hyoid, laryngeal '
    'folds/cartilage, pharyngeal wall and cricopharyngeal interfaces are not '
    'independently represented. Closed masks do not prove an anatomical '
    'capsule or a separately resolved tissue boundary.',
    'Matching MRI planes belong to this processed case and use its source '
    'index grid. There is no registration to published swallowing movies, '
    'other source patients or current reports. Static anatomy supplies no '
    'bolus transit, airway protection, aspiration exclusion, muscle activity '
    'or physiological swallowing simulation. Display colours are labels, '
    'not photographic tissue colours.',
    'Dataset rights are verified from the OSF node-linked CC0 grant, '
    'separately from the article CC-BY-NC-ND 4.0 licence. Independent '
    'anatomical and clinical review remain pending. ' + ATTRIBUTION,
]


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def nifti_samples(path, expected, dtype):
    """Read the unchanged NIfTI-1 storage and its declared source sform."""
    encoded = path.read_bytes()
    if sha(encoded) != expected['sha256']:
        raise ValueError('Original distributed NIfTI digest changed')
    raw = gzip.decompress(encoded)
    if struct.unpack_from('<i', raw)[0] != 348:
        raise ValueError('Expected source little-endian NIfTI-1')
    dim = struct.unpack_from('<8h', raw, 40)
    shape = tuple(dim[1:4])
    offset = int(struct.unpack_from('<f', raw, 108)[0])
    slope, intercept = struct.unpack_from('<2f', raw, 112)
    if shape != (64, 320, 320) or offset != 352:
        raise ValueError('Reviewed distributed grid changed')
    storage = np.frombuffer(raw, dtype=dtype, offset=offset).reshape(shape, order='F')
    affine = np.vstack((np.array(struct.unpack_from('<12f', raw, 280)).reshape(3, 4), [0, 0, 0, 1]))
    if not np.array_equal(affine, np.array(expected['affine'])):
        raise ValueError('Original source sform changed')
    if list((slope, intercept)) != expected['scale_slope_intercept']:
        raise ValueError('Original source signal scaling changed')
    return storage, storage.astype(np.float64) * slope + intercept, affine


def source_preview(image, labels, out):
    """Keep full planes and make a disclosed zero-margin-cropped pixel-repeat view."""
    indices = np.median(np.argwhere(labels > 0), axis=0).astype(int)
    lo, hi = np.percentile(image[image != 0], [1, 99])
    colours = np.array([[0, 0, 0], [46, 180, 139], [227, 125, 66], [141, 149, 212], [198, 105, 169]], dtype=np.uint8)
    plate = Image.new('RGB', (1020, 800), 'white')
    focused = Image.new('RGB', (1020, 800), 'white')
    draw = ImageDraw.Draw(plate)
    focus_draw = ImageDraw.Draw(focused)
    for d in (draw, focus_draw):
        d.text((10, 5), 'WT9FC sub-007: same-case processed MRI / original publisher labels', fill='black')
    draw.text((10, 22), 'Full source index planes, source window; publisher ROI zeros remain. Not raw/native acquisition.', fill='black')
    focus_draw.text((10, 22), 'Zero margins removed for display; each original pixel repeated 3x. No new resolution. Not raw/native.', fill='black')
    crops = []
    for axis, index in enumerate(indices):
        plane = np.take(image, index, axis=axis).T
        mask = np.take(labels, index, axis=axis).T
        gray = np.clip((plane - lo) / (hi - lo) * 255, 0, 255).astype(np.uint8)
        rgb = np.stack([gray] * 3, axis=-1)
        overlay = rgb.copy()
        selected = mask > 0
        overlay[selected] = (0.5 * rgb[selected] + 0.5 * colours[mask[selected]]).astype(np.uint8)
        nonzero = np.argwhere((plane != 0) | (mask > 0))
        low, high = nonzero.min(0), nonzero.max(0) + 1
        crops.append({'source_index_axis': axis, 'source_index': int(index),
                      'transposed_plane_low_inclusive': low.tolist(), 'transposed_plane_high_exclusive': high.tolist(),
                      'all_nonzero_plane_samples_retained': True, 'all_nonzero_label_samples_retained': True})
        for row, (title, pixels) in enumerate([('Source-scaled MRI', rgb), ('Publisher labels', overlay)]):
            x, y = axis * 340, 50 + row * 365
            draw.text((x + 10, y), f'{title}; index axis {axis} = {int(index)}', fill='black')
            plate.paste(Image.fromarray(pixels), (x + 10, y + 20))
            crop = pixels[low[0]:high[0], low[1]:high[1]]
            repeated = np.repeat(np.repeat(crop, 3, axis=0), 3, axis=1)
            focus_draw.text((x + 10, y), f'{title}; index axis {axis} = {int(index)}', fill='black')
            focused.paste(Image.fromarray(repeated), (x + 10, y + 20))
    draw.text((10, 784), 'Labels: 1 combined transverse/vertical; 2 superior longitudinal; 3 inferior longitudinal; 4 genioglossus.', fill='black')
    focus_draw.text((10, 784), 'Labels: 1 combined transverse/vertical; 2 superior longitudinal; 3 inferior longitudinal; 4 genioglossus.', fill='black')
    full_path = out.with_name('full-source-index-planes.png')
    plate.save(full_path)
    focused.save(out)
    return {'selected_source_index_planes': [int(i) for i in indices], 'source_window': [float(lo), float(hi)],
            'window_rule': '1st/99th percentile of nonzero source-scaled distributed MRI',
            'slice_transpose_for_display': True, 'display_overlay_alpha': 0.5, 'source_samples_changed': False,
            'display_zero_margin_crops': crops, 'display_pixel_repeat_factor': 3, 'interpolation_applied': False,
            'extra_anatomical_data_removed': False, 'extra_display_resolution_claimed': False,
            'original_publisher_ROI_masking_preserved': True,
            'full_source_plane_sha256': sha(full_path.read_bytes()),
            'source_patient_anatomical_planes_independently_verified': False, 'sha256': sha(out.read_bytes())}


def package(source_root, root=ROOT, apply_registry=False):
    proof = root / PROOF_REL
    proof.mkdir(parents=True, exist_ok=True)
    report = json.loads((source_root / 'independent-grid-and-surface-review.json').read_text())
    acquisition = json.loads((source_root / 'acquisition.json').read_text())
    node = json.loads((source_root / 'osf-node.json').read_text())
    licence = json.loads((source_root / 'osf-license.json').read_text())
    linked_id = node['data']['relationships']['license']['data']['id']
    if linked_id != licence['data']['id'] or licence['data']['attributes']['name'] != 'CC0 1.0 Universal':
        raise ValueError('Source dataset CC0 grant relationship changed')
    if report['case'] != 'BeLong/sub-007_segID-001' or report['unique_mask_values'] != [0, 1, 2, 3, 4]:
        raise ValueError('Reviewed source case/labels changed')
    copy_names = ['osf-node.json', 'osf-license.json', 'acquisition.json', 'demographics-source-metadata.json',
                  'demographics.xlsx', 'independent-grid-and-surface-review.json', 'licence-processing-and-visual-review.json']
    for record in acquisition['files']:
        raw = (source_root / record['filename']).read_bytes()
        if sha(raw) != record['sha256'] or hashlib.md5(raw).hexdigest() != record['md5'] or len(raw) != record['bytes']:
            raise ValueError('Original source file digest changed')
        copy_names.append(record['filename'])
    for name in copy_names:
        raw = (source_root / name).read_bytes()
        (proof / name).write_bytes(raw)
    demographic_metadata = json.loads((proof / 'demographics-source-metadata.json').read_text())
    hashes = demographic_metadata['attributes']['extra']['hashes']
    demo = (proof / 'demographics.xlsx').read_bytes()
    if sha(demo) != hashes['sha256'] or hashlib.md5(demo).hexdigest() != hashes['md5']:
        raise ValueError('Original source demographics changed')
    licence_evidence = {'source_url': SOURCE, 'node_id': node['data']['id'], 'linked_licence_id': linked_id,
                        'node_sha256': sha((proof / 'osf-node.json').read_bytes()),
                        'licence_sha256': sha((proof / 'osf-license.json').read_bytes()), 'licence': 'CC0 1.0 Universal',
                        'commercial_reuse_under_dataset_grant': True, 'article_licence': 'CC-BY-NC-ND 4.0',
                        'article_graphics_or_captions_reused': False, 'anatomical_or_clinical_approval': False}
    write_json(proof / 'dataset-licence-evidence.json', licence_evidence)
    _, image, image_affine = nifti_samples(proof / IMAGE_NAME, report['sample_checks'][IMAGE_NAME], '<i2')
    labels, _, label_affine = nifti_samples(proof / LABEL_NAME, report['sample_checks'][LABEL_NAME], '<u2')
    if list(np.unique(labels)) != [0, 1, 2, 3, 4]:
        raise ValueError('Source label storage changed')
    out = root / 'web/anatomy' / ATLAS
    out.mkdir(parents=True, exist_ok=True)
    parts, checks = {}, []
    for row in report['labels']:
        value = row['label_value']
        stem, name, colour = LABELS[value]
        if name != row['source_name'] or int((labels == value).sum()) != row['source_voxels']:
            raise ValueError('Source muscle mapping or original mask count changed')
        arrays = []
        for suffix in ['positions.f64le.bin', 'triangles.u32le.bin']:
            filename = f'label-{value}-{suffix}'
            candidate = source_root / filename
            raw = candidate.read_bytes() if candidate.exists() else gzip.decompress((source_root / (filename + '.gz')).read_bytes())
            original = next(f for f in row['output_files'] if f['filename'] == filename)
            if sha(raw) != original['sha256'] or len(raw) != original['bytes']:
                raise ValueError('Reviewed full source geometry changed')
            (proof / (filename + '.gz')).write_bytes(gzip.compress(raw, mtime=0))
            arrays.append(raw)
        praw, fraw = arrays
        vertices = np.frombuffer(praw, '<f8').reshape(-1, 3)
        faces = np.frombuffer(fraw, '<u4').reshape(-1, 3)
        if len(faces) != row['surface_triangles'] or len(vertices) != row['surface_vertices'] or not np.isfinite(vertices).all():
            raise ValueError('Reviewed source mesh contract changed')
        stored = vertices.astype('<f4')
        error = float(np.abs(stored.astype(np.float64) - vertices).max())
        if error > 4e-5:
            raise ValueError('Unexpected float32 position transport loss')
        normals = np.zeros_like(vertices)
        tri = vertices[faces]
        cross = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
        for corner in range(3):
            np.add.at(normals, faces[:, corner], cross)
        lengths = np.linalg.norm(normals, axis=1)
        normals[lengths > 0] /= lengths[lengths > 0, None]
        decoded = struct.pack('<4sII', b'BP3D', len(vertices), faces.size) + stored.tobytes() + normals.astype('<f4').tobytes() + fraw
        encoded = gzip.compress(decoded, mtime=0)
        ident = ATLAS + '-' + stem
        filename = ident + '.bin.gz'
        (out / filename).write_bytes(encoded)
        readback = gzip.decompress((out / filename).read_bytes())
        if readback[12 + len(vertices) * 24:] != fraw or not np.array_equal(np.frombuffer(readback, '<f4', len(vertices) * 3, 12).reshape(-1, 3), stored):
            raise ValueError('Full source transport readback differs')
        parts[ident] = {'id': ident, 'name': name + ' · distributed source label',
                        'file': '/app/anatomy/' + ATLAS + '/' + filename, 'sha256': sha(encoded), 'decoded_sha256': sha(decoded),
                        'vertices': len(vertices), 'triangles': len(faces), 'bounds': [stored.min(0).tolist(), stored.max(0).tolist()],
                        'source_label': value, 'source_positions_sha256': sha(praw), 'source_triangles_sha256': sha(fraw),
                        'source_components': row['source_connected_components'], 'source_boundary_edges': row['open_edges'],
                        'clinical_fidelity': 'unverified', 'color': colour, 'layer': 'source_labels', 'regions': [FAMILY]}
        checks.append({'id': ident, 'all_source_faces_unchanged': True, 'maximum_float32_transport_error_source_mm': error,
                       'zero_display_normals': int((lengths == 0).sum()), 'sha256': sha(encoded)})
    low = np.min([p['bounds'][0] for p in parts.values()], axis=0)
    high = np.max([p['bounds'][1] for p in parts.values()], axis=0)
    manifest = {'dataset': 'WT9FC BeLong sub-007 · four processed tongue source labels', 'source_url': SOURCE,
                'license': 'CC0 1.0 Universal', 'license_url': GRANT,
                'coordinate_system': {'basis': 'RAS', 'units': 'distributed NIfTI sform-declared millimetres', 'unit_meters': 0.001,
                                      'display_basis': 'native-ras-to-x-left-y-superior-z-anterior',
                                      'registration': 'Distributed processed mask sform only; original MRI sform retained separately'},
                'source_label_affine': label_affine.tolist(), 'source_image_affine': image_affine.tolist(),
                'source_grid_shape': [64, 320, 320], 'source_sample_pitch_mm': [0.8, 0.8, 0.8],
                'distributed_source_processed': True, 'unmodified_native_acquisition': False, 'source_movie_registration': False,
                'parts': parts, 'regions': {FAMILY: {'title': 'Tongue MRI source labels · partial', 'side': 'source case sub-007',
                    'parts': [{'id': i, 'layer': 'source_labels'} for i in parts], 'layers': [['source_labels', 'Distributed tongue muscle labels']],
                    'source_up_range': [float(low[2] - 1), float(high[2] + 1)], 'focus_bounds': [low.tolist(), high.tolist()],
                    'source_coordinate_cameras': True, 'uncropped_label': 'Full distributed labels · partial mouth reference'}},
                'viewer_notes': NOTES, 'clinical_approval': False, 'anatomical_approval': False,
                'complete_swallowing_geometry_verified': False, 'runtime_promoted': apply_registry,
                'status': 'Partial processed source reference; anatomical validation pending',
                'total_triangles': sum(p['triangles'] for p in parts.values())}
    if manifest['total_triangles'] != 67508:
        raise ValueError('Full source triangle total changed')
    write_json(out / 'manifest.json', manifest)
    (out / 'ATTRIBUTION.md').write_text('# Partial processed tongue source reference\n\n' + '\n\n'.join(NOTES) + '\n')
    image_path = root / 'web/reference-media' / ATLAS / 'source-MRI-label-context.png'
    image_path.parent.mkdir(parents=True, exist_ok=True)
    preview = source_preview(image, labels, image_path)
    write_json(proof / 'source-display-review.json', preview)
    source_image = {'src': '/app/reference-media/' + ATLAS + '/' + image_path.name, 'sha256': sha(image_path.read_bytes()),
                    'width': 1020, 'height': 800, 'title': 'Matching processed MRI planes and publisher tongue labels',
                    'alt': 'Same-case distributed MRI index planes and four publisher tongue muscle label overlays.',
                    'caption': 'Three index planes from the same registered, mouth-cropped source case. Display removes only zero ROI margins and repeats each original pixel three times, with no interpolation or new resolution. Original source-scaled MRI signal is clipped to a declared percentile window; coloured overlays show publisher labels already smoothed before release. Full source planes are preserved separately. Fine fibres or normal swallowing are not established.',
                    'attribution': ATTRIBUTION, 'source_url': SOURCE, 'license_url': GRANT, 'license': 'CC0 1.0 Universal'}
    entry = {'id': ATLAS + '-processed-labels', 'label': 'Tongue MRI source labels · partial', 'atlas': ATLAS, 'family': FAMILY,
             'manifest_url': '/app/anatomy/' + ATLAS + '/manifest.json', 'manifest_sha256': sha((out / 'manifest.json').read_bytes()),
             'initial_layer': 'source_labels', 'initial_cropped': False, 'population_note': ' '.join(NOTES), 'source_image': source_image}
    rights_path = proof / 'dataset-licence-evidence.json'
    rights = {'name': 'CC0 1.0 Universal', 'url': GRANT, 'commercial_use': True, 'redistribution': True, 'review_status': 'verified',
              'evidence_path': str(rights_path.relative_to(root)), 'evidence_sha256': sha(rights_path.read_bytes()),
              'attribution': ATTRIBUTION, 'reviewed_at': '2026-10-08'}
    assets = [{'id': p['id'], 'kind': 'model', 'name': p['name'], 'local_path': 'web/' + p['file'].removeprefix('/app/'),
               'sha256': p['sha256'], 'investigation_ids': [INV], 'structure_ids': [], 'requirement_coverage': {},
               'source': {'url': SOURCE, 'license': rights}, 'anatomical_review': {'status': 'pending', 'reason': 'Four processed muscle labels do not resolve all swallowing reporting anatomy.'}} for p in parts.values()]
    assets.append({'id': ATLAS + '-MRI-source-display', 'kind': 'clinical_image', 'name': source_image['title'],
                   'local_path': str(image_path.relative_to(root)), 'sha256': source_image['sha256'], 'modality': 'MRI',
                   'investigation_ids': [INV], 'structure_ids': [], 'requirement_coverage': {}, 'source': {'url': SOURCE, 'license': rights},
                   'pixel_provenance': {'source_samples_changed': False, 'source_distribution_processed': True,
                                        'adaptation': 'Source-index planes, zero-margin display crop, 3x pixel repeat, source-scaled percentile window and publisher label overlays'},
                   'anatomical_review': {'status': 'pending', 'reason': 'Selected processed source planes are not full fine anatomy or functional validation.'}})
    write_json(proof / 'reader-reference-entry.json', entry)
    write_json(proof / 'reader-asset-entries.json', assets)
    write_json(proof / 'reader-transport-review.json', {'manifest_sha256': entry['manifest_sha256'], 'parts': checks,
        'all_original_faces_retained': True, 'total_triangles': 67508, 'source_geometry_repaired': False,
        'image_sform_replaced_by_label_sform': False, 'independent_anatomical_approval': False, 'global_registry_applied': apply_registry})
    if apply_registry:
        from tools.anatomy_sources.package_aortic_rupture_figures import append_evidence
        refs_path = root / 'data/radiology/source-anatomy-references.json'
        refs = json.loads(refs_path.read_text())
        refs[INV] = [r for r in refs.get(INV, []) if r['atlas'] != ATLAS] + [entry]
        write_json(refs_path, refs)
        append_evidence(root / 'data/radiology/radiology-asset-evidence.json', assets, prefix=ATLAS + '-')
    return {'atlas': ATLAS, 'total_triangles': 67508, 'parts': len(parts), 'global_registry_applied': apply_registry}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', type=Path, default=ROOT / PROOF_REL)
    parser.add_argument('--apply-registry', action='store_true')
    args = parser.parse_args()
    print(json.dumps(package(args.source_root, apply_registry=args.apply_registry)))
