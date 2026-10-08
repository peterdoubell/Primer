#!/usr/bin/env python3
"""Package intact original laryngeal phonation geometry; registration stays unverified."""
import argparse
from collections import Counter
import gzip
import io
import hashlib
import json
import math
from pathlib import Path
import struct
import sys
import zlib

ROOT = Path(__file__).resolve().parents[2]
# CLI compatibility selector only: every source read uses this reviewed cache.
# Relocation requires an explicit code change and a fresh source proof review.
TRUSTED_SOURCE_ROOT = Path('/Users/peter/Documents/ChatGPT/Primer/.research/swallow-fine-larynx-19629778')
ATLAS = 'larynx-jasa19629778-phase01'
FAMILY = 'larynx-phonation-source'
PART = ATLAS + '-original-air-tissue-interface'
NAME = 'Original segmented air–tissue interface · source phonation phase01'
PROOF = ROOT / 'docs/laryngeal-phonation-source-review'
URL = 'https://zenodo.org/records/19629778'
GRANT = 'https://creativecommons.org/licenses/by/4.0/'
ORIGINAL_SHA = 'dddf49ed16942555eefcda5f97db3f39942676532bd816f348277895715480d2'
ALLOWED_INVESTIGATIONS = ('ra.swallowing', 'ra.mri-neck-spaces')
DATE = '2026-10-08'


def canonical_gzip(raw):
    # GzipFile fixes the platform OS marker across Python/zlib versions.
    buffer = io.BytesIO()
    with gzip.GzipFile(filename='', mode='wb', fileobj=buffer, mtime=0, compresslevel=9) as target:
        target.write(raw)
    return buffer.getvalue()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read_original_STL(data):
    """Deduplicate only bit-identical corners; retain every source face in order."""
    data = bytes(data)
    if len(data) < 84:
        raise ValueError('Incomplete original binary STL')
    count = struct.unpack_from('<I', data, 80)[0]
    if count != 29326 or len(data) != 84 + count * 50:
        raise ValueError('Original STL face count/size changed')
    coordinates = []
    position_bytes = bytearray()
    lookup = {}
    faces = []
    normals = []
    for first in range(84, len(data), 50):
        face = []
        for corner in range(3):
            encoded = data[first + 12 + corner * 12:first + 24 + corner * 12]
            if encoded not in lookup:
                vertex = struct.unpack('<fff', encoded)
                if not all(math.isfinite(v) for v in vertex):
                    raise ValueError('Nonfinite original source coordinate')
                lookup[encoded] = len(coordinates)
                coordinates.append(vertex)
                position_bytes.extend(encoded)
                normals.append([0.0, 0.0, 0.0])
            face.append(lookup[encoded])
        faces.append(face)
        a, b, c = [coordinates[i] for i in face]
        u = [b[i] - a[i] for i in range(3)]
        v = [c[i] - a[i] for i in range(3)]
        cross = [u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0]]
        for index in face:
            for dim in range(3):
                normals[index][dim] += cross[dim]
    zero = 0
    for normal in normals:
        length = math.sqrt(sum(value*value for value in normal))
        if not length:
            zero += 1
        else:
            for dim in range(3):
                normal[dim] /= length
    normal_bytes = b''.join(struct.pack('<fff', *v) for v in normals)
    triangle_bytes = b''.join(struct.pack('<III', *f) for f in faces)
    return bytes(position_bytes), normal_bytes, triangle_bytes, coordinates, faces, zero


def original_topology(coordinates, faces):
    edges = Counter()
    parent = list(range(len(coordinates)))
    def find(v):
        while parent[v] != v:
            parent[v] = parent[parent[v]]
            v = parent[v]
        return v
    for a, b, c in faces:
        for x, y in ((a, b), (b, c), (c, a)):
            edges[tuple(sorted((x, y)))] += 1
            rx, ry = find(x), find(y)
            if rx != ry:
                parent[rx] = ry
    components = Counter(find(face[0]) for face in faces)
    return {'components': len(components), 'component_triangle_counts': sorted(components.values(), reverse=True),
            'boundary_edges': sum(value == 1 for value in edges.values()), 'nonmanifold_edges': sum(value > 2 for value in edges.values())}


def notes(attribution):
    return [
        'Partial original source surface from one professionally trained female singer during sustained Stiff phonation. This is not swallowing, VFSS, aspiration assessment, a normal atlas or the anatomy of the patient being reported.',
        'All 29,326 original triangles, four source components and 328 open boundary edges are retained in their exact original STL coordinates and face order. No fit, centering, smoothing, capping, repair, decimation or fragment deletion. Neutral display colour and averaged display normals are not photographic tissue appearance.',
        'Original Blender 3.4.1 STL has no patient direction, coordinate-system or unit declaration. Cameras refer only to source coordinates. The paper provides nominal millimetre-scale context; source STL calibration and anatomical directions remain unverified.',
        'The matching published MR array has nominal 0.8 mm native acquisition resolution and a zero-filled export pitch 0.3839285671710968 (nominal 0.4 mm in the paper). This export grid does not increase acquired anatomical resolution.',
        'The MRI primary NRRD geometry declares LPS. Inherited NIfTI srow strings conflict in x/z directions even after LPS to RAS convention conversion. Fixed-sign image correspondence favours an LPS hypothesis for this STL, but producer transform and segmentation mask are absent. No MRI overlay or source-volume registration is presented or approved.',
        'Phase 01 is the authors’ maximum glottal-opening bin. Ten acoustic phase bins aggregate an oscillatory cycle over a 5 min 20 s sustained-phonation acquisition; they are not consecutive independent live frames or a swallowing timeline. Audio-to-volume sample timing and MRI-to-upright high-speed video correspondence remain unverified.',
        'Threshold-segmented air–tissue interface only. Individual cartilage, vocal-fold tissue layers, ligaments, muscles, mucosa, vessels and nerves are not independently labelled. Source surface ends truncate the visible airway extent. No physiological function, patient diagnosis, complete reporting anatomy or clinical/commercial fidelity is established.',
        'Selected complete ZIP member CRC32 and local SHA256 were verified; publisher archive size/checksum remained stable before/after range acquisition. The whole 5.23 GB ZIP MD5 was not independently verified and no HTTP entity tag was available. ' + attribution,
    ]


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n')


def package(source_root, apply_registry=False, investigations=('ra.swallowing',)):
    if str(source_root) != str(TRUSTED_SOURCE_ROOT):
        raise ValueError('Source root must select the fixed reviewed laryngeal source cache')
    # Do not propagate the CLI value to filesystem reads, even after checking it.
    source_root = TRUSTED_SOURCE_ROOT
    if not investigations or any(i not in ALLOWED_INVESTIGATIONS for i in investigations):
        raise ValueError('Only explicitly scoped source-reference investigations are permitted')
    metadata_raw = (source_root/'zenodo-record.json').read_bytes()
    metadata = json.loads(metadata_raw)
    acquisition = json.loads((source_root/'candidate-acquisition.json').read_text())
    geometry = json.loads((source_root/'original-STL-audit.json').read_text())
    coordinate = json.loads((source_root/'coordinate-interface-independent-audit.json').read_text())
    original = (source_root/'stiff-phase01/frame_01.stl').read_bytes()
    member = next(r for r in acquisition['members'] if r['local_file'].endswith('.stl'))
    if (metadata['id'] != 19629778 or metadata['metadata']['license']['id'] != 'cc-by-4.0'
            or sha(original) != ORIGINAL_SHA or sha(original) != member['sha256']
            or format(zlib.crc32(original)&0xffffffff, '08x') != member['source_CRC32']
            or not member['CRC32_verified'] or geometry['sha256'] != ORIGINAL_SHA
            or coordinate['source_inputs']['STL_SHA256'] != ORIGINAL_SHA):
        raise ValueError('Original source identity/rights/acquisition changed')
    pos, norm, face_bytes, positions, faces, zero = read_original_STL(original)
    topology = original_topology(positions, faces)
    if topology != {'components':4, 'component_triangle_counts':[29294,16,8,8], 'boundary_edges':328, 'nonmanifold_edges':0}:
        raise ValueError('Original source topology changed')
    if len(positions) != 14831:
        raise ValueError('Original source coordinate count changed')
    decoded = struct.pack('<4sII', b'BP3D', len(positions), len(faces)*3) + pos + norm + face_bytes
    encoded = canonical_gzip(decoded)
    out = ROOT/'web/anatomy'/ATLAS
    out.mkdir(parents=True, exist_ok=True)
    PROOF.mkdir(parents=True, exist_ok=True)
    filename = PART + '.bin.gz'
    (out/filename).write_bytes(encoded)
    readback = gzip.decompress((out/filename).read_bytes())
    if readback != decoded:
        raise ValueError('BP3D transport readback differs')
    read_positions = readback[12:12+len(positions)*12]
    read_faces = readback[12+len(positions)*24:]
    corner_bytes = bytearray()
    for (index,) in struct.iter_unpack('<I', read_faces):
        corner_bytes.extend(read_positions[index*12:index*12+12])
    original_corner_bytes = b''.join(original[i+12:i+48] for i in range(84, len(original), 50))
    if bytes(corner_bytes) != original_corner_bytes:
        raise ValueError('Original ordered source face corners changed')
    attribution = ', '.join(c['name'] for c in metadata['metadata']['creators']) + '. Supplementary dataset for Dynamic 3D MRI of vocal fold oscillations, Stiff phase 01. DOI 10.5281/zenodo.19629778. CC BY 4.0. Adaptation: bit-exact original STL geometry in BP3D transport; neutral display colour and averaged display normals.'
    warnings = notes(attribution)
    low = [min(v[d] for v in positions) for d in range(3)]
    high = [max(v[d] for v in positions) for d in range(3)]
    part = {'id':PART, 'name':NAME, 'file':'/app/anatomy/'+ATLAS+'/'+filename,
            'sha256':sha(encoded), 'decoded_sha256':sha(decoded), 'vertices':len(positions), 'triangles':len(faces),
            'bounds':[low, high], 'source_member':member['original_member'], 'source_member_sha256':ORIGINAL_SHA,
            'source_positions_sha256':sha(pos), 'source_triangles_sha256':sha(face_bytes),
            'source_components':4, 'source_boundary_edges':328, 'clinical_fidelity':'unverified',
            'color':'#a7b7ba', 'layer':'source_interface', 'regions':[FAMILY]}
    manifest = {'dataset':'Original laryngeal air–tissue interface · Stiff phase 01 · partial', 'source_url':URL,
        'license':'CC BY 4.0', 'license_url':GRANT,
        'coordinate_system':{'basis':'unknown original STL XYZ', 'units':'source STL numeric units; no embedded calibration',
            'unit_meters':None, 'display_basis':'source-xyz-to-display-x-z-minus-y',
            'registration':'Unregistered original source coordinates; producer patient transform, units and directions unverified'},
        'parts':{PART:part}, 'regions':{FAMILY:{'title':'Original phonation air–tissue interface · partial', 'side':'source phonation phase 01',
            'parts':[{'id':PART, 'layer':'source_interface'}], 'layers':[['source_interface', 'Original air–tissue interface']],
            'source_coordinate_cameras':True, 'uncropped_label':'Complete original source surface · airway extent partial',
            'source_up_range':[low[2]-1, high[2]+1], 'focus_bounds':[low,high]}},
        'viewer_notes':warnings, 'total_triangles':29326, 'clinical_approval':False, 'anatomical_approval':False,
        'source_MRI_registration_approved':False, 'complete_reporting_anatomy_verified':False,
        'photographic_texture_promoted':False, 'status':'Partial source reference; anatomy and registration unverified'}
    write_json(out/'manifest.json', manifest)
    (out/'ATTRIBUTION.md').write_text('# Partial original source reference\n\n'+'\n\n'.join(warnings)+'\n')
    copies = {'zenodo-record.json':'zenodo-19629778.json', 'candidate-acquisition.json':'original-acquisition.json',
        'stl-independent-acquisition.json':'independent-STL-acquisition.json', 'original-STL-audit.json':'original-STL-quality-review.json',
        'article-methods-review.json':'article-methods-review.json', 'candidate-native-review.json':'original-MRI-native-review.json',
        'independent-reader-review.json':'independent-MRI-reader-review.json', 'NRRD-header-partial.txt':'original-NRRD-header.txt',
        'coordinate-interface-independent-audit.json':'coordinate-interface-review.json',
        'coordinate-interface-independent-review.md':'coordinate-interface-review.md',
        'coordinate_interface_audit.py':'coordinate_interface_audit.py', 'original-STL-review.png':'original-STL-review.png'}
    copied = []
    for source_name, target in copies.items():
        raw = (source_root/source_name).read_bytes()
        (PROOF/target).write_bytes(raw)
        copied.append({'file':target, 'sha256':sha(raw), 'bytes':len(raw)})
    (PROOF/'original-frame_01.stl').write_bytes(original)
    copied.append({'file':'original-frame_01.stl','sha256':ORIGINAL_SHA,'bytes':len(original)})
    rights = {'name':'CC BY 4.0', 'url':GRANT, 'commercial_use':True, 'redistribution':True, 'review_status':'verified',
        'evidence_path':'docs/laryngeal-phonation-source-review/zenodo-19629778.json', 'evidence_sha256':sha(metadata_raw),
        'attribution':attribution, 'reviewed_at':DATE}
    asset = {'id':PART,'kind':'model','name':NAME, 'local_path':str((out/filename).relative_to(ROOT)),
        'sha256':sha(encoded), 'investigation_ids':list(investigations), 'structure_ids':[], 'requirement_coverage':{},
        'source':{'url':URL, 'license':rights}, 'anatomical_review':{'status':'pending',
            'reason':'Original source air–tissue interface only; producer registration, fine tissue labels and complete clinical anatomy remain unverified.'}}
    entry = {'id':ATLAS+'-original-surface', 'label':'Original phonation air–tissue interface · partial', 'atlas':ATLAS,
        'family':FAMILY, 'manifest_url':'/app/anatomy/'+ATLAS+'/manifest.json', 'manifest_sha256':sha((out/'manifest.json').read_bytes()),
        'initial_layer':'source_interface', 'initial_cropped':False, 'population_note':' '.join(warnings)}
    write_json(PROOF/'registry-candidate.json', {'investigation_ids':list(investigations), 'entry':entry, 'asset':asset,
        'registry_applied_by_this_run':apply_registry})
    write_json(PROOF/'reader-transport-review.json', {'original_STL_sha256':ORIGINAL_SHA, 'source_input_proofs':copied,
        'transport_SHA256':sha(encoded), 'decoded_transport_SHA256':sha(decoded), 'manifest_SHA256':entry['manifest_sha256'],
        'positions_SHA256':sha(pos), 'triangles_SHA256':sha(face_bytes), 'ordered_source_face_corner_SHA256':sha(original_corner_bytes),
        'all_87978_source_face_corners_byte_exact':True, 'maximum_position_transport_error_source_units':0,
        'all_29326_original_faces_retained_in_order':True, 'topology':topology, 'zero_display_normals':zero,
        'source_geometry_modified':False, 'source_MRI_overlay_presented':False, 'producer_registration_verified':False,
        'clinical_or_anatomical_coverage_approved':False, 'registry_applied_by_this_run':apply_registry})
    if apply_registry:
        sys.path.insert(0, str(ROOT))
        from tools.anatomy_sources.package_aortic_rupture_figures import append_evidence
        path = ROOT/'data/radiology/source-anatomy-references.json'
        registry = json.loads(path.read_text())
        for investigation in investigations:
            registry[investigation] = [r for r in registry.get(investigation, []) if r['atlas'] != ATLAS] + [entry]
        write_json(path, registry)
        append_evidence(ROOT/'data/radiology/radiology-asset-evidence.json', [asset], prefix=ATLAS+'-')
    print('Packaged 29,326 unchanged source triangles; registration/anatomy unapproved; registry '+('applied' if apply_registry else 'not changed'))
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', type=Path, required=True, help='Compatibility selector: must resolve to the fixed reviewed source-cache directory')
    parser.add_argument('--apply-registry', action='store_true', help='Explicitly add the reviewed partial reference to global registry/evidence')
    parser.add_argument('--investigation', action='append', choices=ALLOWED_INVESTIGATIONS, dest='investigations')
    args = parser.parse_args()
    package(args.source_root, args.apply_registry, tuple(args.investigations or ['ra.swallowing']))
