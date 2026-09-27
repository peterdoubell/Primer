#!/usr/bin/env python3
"""Stage the public shoulder deck's seven surfaces in their native assembly.

Never runs Abaqus/journal code or changes source positions. Source instance
placement is applied analytically and recorded, not estimated from anatomy.
"""
import hashlib
import json
from pathlib import Path

import numpy as np
from inspect_leeds_ankle import boundary

STAGE = Path('/tmp/primer-msk-sources/shoulder-next/fda-shoulder')
SOURCE_HASH = '547de9cff23a4ae98d5a297ba32d8b01fe042739160c4b7144dfe7066d08c70a'
NAMES = {'AC_Lig': 'Acromioclavicular ligament', 'CLAVICLE': 'Clavicle',
         'Gcart': 'Glenoid cartilage', 'Hcart': 'Humeral cartilage',
         'Humerus': 'Humerus', 'Labrum': 'Glenoid labrum', 'SCAPULA': 'Scapula'}


def parse(source):
    parts, instances, connectors = {}, [], []
    current, active, props = None, None, {}
    for line in source.decode().splitlines():
        line = line.strip()
        if not line or line.startswith('**'):
            continue
        if line.startswith('*'):
            fields = [field.strip() for field in line.split(',')]
            active = fields[0].upper()
            props = dict(field.split('=', 1) for field in fields[1:] if '=' in field)
            if active == '*INCLUDE':
                raise ValueError('External includes require separate inspection')
            if active == '*PART':
                current = props['name']
                assert current not in parts
                parts[current] = {'nodes': {}, 'elements': {}, 'sections': []}
            elif active == '*END PART':
                current = None
            elif active == '*INSTANCE':
                instances.append({'name': props['name'], 'part': props['part'], 'transform_lines': []})
            elif active == '*SOLID SECTION' and current:
                parts[current]['sections'].append(props)
            elif active == '*ELEMENT':
                assert props['type'] == ('C3D10M' if current else 'CONN3D2')
            continue
        if current and active == '*NODE':
            values = line.split(',')
            parts[current]['nodes'][int(values[0])] = [float(v) for v in values[1:]]
        elif current and active == '*ELEMENT':
            values = [int(v.strip()) for v in line.split(',') if v.strip()]
            assert len(values) == 11
            parts[current]['elements'][values[0]] = values[1:]
        elif active == '*INSTANCE':
            instances[-1]['transform_lines'].append([float(v) for v in line.split(',')])
        elif not current and active == '*ELEMENT':
            connectors.append({'declaration': props.copy(), 'connectivity': line})
    assert set(parts) == set(NAMES) and len(instances) == len(parts)
    assert {instance['part'] for instance in instances} == set(parts)
    return parts, instances, connectors


def transform(lines):
    result = np.eye(4)
    if not lines:
        return result
    assert len(lines) in (1, 2) and len(lines[0]) == 3
    result[:3, 3] = lines[0]
    if len(lines) == 1:
        return result
    assert len(lines[1]) == 7
    a, b = np.array(lines[1][:3]), np.array(lines[1][3:6])
    axis = (b - a) / np.linalg.norm(b - a)
    x, y, z = axis
    cross = np.array([[0, -z, y], [z, 0, -x], [-y, x, 0]])
    angle = np.deg2rad(lines[1][6])
    rotation = np.eye(3) + np.sin(angle) * cross + (1 - np.cos(angle)) * (cross @ cross)
    # Abaqus applies translation first, then right-hand rotation about a->b.
    result[:3, :3] = rotation
    result[:3, 3] = rotation @ (result[:3, 3] - a) + a
    assert np.allclose(rotation.T @ rotation, np.eye(3), atol=1e-13)
    assert np.isclose(np.linalg.det(rotation), 1, atol=1e-13)
    return result


def main():
    raw = (STAGE / 'Male-Shoulder.inp').read_bytes()
    assert hashlib.sha256(raw).hexdigest() == SOURCE_HASH
    parts, instances, connectors = parse(raw)
    report = {'status': 'Research source inspection only; anatomical fidelity unapproved',
              'dataset': 'FDA Human Shoulder Finite Element Model (RST24OP04.01)',
              'license': 'CC0-1.0', 'license_file': 'LICENSE',
              'source_sha256': SOURCE_HASH,
              'attribution': 'U.S. Food and Drug Administration (2023), Human Shoulder Finite Element Model (RST24OP04.01); Sadeqi et al., doi:10.1007/s10439-022-03018-8.',
              'source_url': 'https://cdrh-rst.fda.gov/human-shoulder-finite-element-model',
              'units': 'Consistent millimetre/MPa inference from README and native material/boundary magnitudes; no unit annotation in deck.',
              'frame': 'Native undeformed Abaqus assembly before simulation boundary conditions; no certified anatomical axis basis or registration to clinical images.',
              'placement_evidence': 'Native *INSTANCE translation then right-hand rotation, https://docs.software.vt.edu/abaqusv2025/English/SIMACAEKEYRefMap/simakey-r-instance.htm',
              'adaptation': 'Extracted external quadratic faces of each original ten-node tetrahedral part; four-triangle preview uses native corner/midside coordinates. Native local positions retained; explicit source assembly transform applied separately. No fitting, smoothing, segmentation or synthetic tissue.',
              'sampling': 'Specific source CT voxel grid not supplied in the acquired README/deck; effective anatomical resolution unestablished.',
              'parts': [], 'muscle_connector_count': len(connectors), 'muscle_connectors': connectors,
              'limitations': ['Single male right shoulder model; no subject-specific clinical certification.',
                  'No cuff tendon, tendon footprint, capsule or biceps-pulley volumetric part.',
                  'Cartilage is offset geometry constrained by cited literature thickness, not directly segmented cartilage.',
                  'Labrum element-set name includes THICKER; the acquired README does not explain whether or how the labrum was thickened.',
                  'Source validation addresses an abduction contact-force scenario and does not prove fine-structure anatomical accuracy.']}
    for instance in instances:
        name = instance['part']; part = parts[name]
        local, faces, ids, quadratic, stats = boundary(part['nodes'], part['elements'], list(part['elements']))
        matrix = transform(instance['transform_lines'])
        world = local @ matrix[:3, :3].T + matrix[:3, 3]
        assert np.isfinite(local).all() and np.isfinite(world).all()
        assert np.allclose((world - matrix[:3, 3]) @ matrix[:3, :3], local, atol=1e-10)
        destination = STAGE / (name + '-boundary.npz')
        np.savez_compressed(destination, positions_local=local, positions_world=world,
                            indices=faces, quadratic_faces=quadratic, source_node_ids=ids,
                            geometry_to_world=matrix)
        record = {'source_part': name, 'name': NAMES[name], 'instance': instance,
                  'source_sections': part['sections'], 'source_nodes': len(part['nodes']),
                  'geometry': destination.name, 'sha256': hashlib.sha256(destination.read_bytes()).hexdigest(),
                  'geometry_to_world_rows': matrix.tolist(),
                  'bounds_world': [world.min(axis=0).tolist(), world.max(axis=0).tolist()], **stats}
        report['parts'].append(record)
        print(name, json.dumps(stats), flush=True)
    (STAGE / 'mesh-inspection.json').write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    main()
