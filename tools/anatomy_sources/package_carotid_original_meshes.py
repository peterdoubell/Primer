#!/usr/bin/env python3
"""Transport complete original right carotid source objects without inventing wall layers or left counterparts."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
ATLAS = 'bp3d-carotid-4.3'
EXPECTED = {'FJ4986': 'FMA69325', 'FJ4989': 'FMA66531', 'FJ4993': 'FMA75866'}
LICENSE_URL = 'https://creativecommons.org/licenses/by-sa/2.1/jp/'
def sha(raw): return hashlib.sha256(raw).hexdigest()
def save(path, value): path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')

def package(source):
    import numpy as np
    from tools.anatomy_sources.review_bodyparts_pancreatic_geometry import read_obj
    output = ROOT / 'web/anatomy' / ATLAS; output.mkdir(exist_ok=True)
    evidence = ROOT / 'docs/carotid-obstruction-source-review'; evidence.mkdir(exist_ok=True)
    originals = evidence / 'original-carotid-objects'; originals.mkdir(exist_ok=True)
    receipt = json.loads((source / 'right-acquisition.json').read_text())
    if receipt['CRC_verified'] is not True or len(receipt['objects']) != 3:
        raise ValueError('Exactly three original source objects require verified ZIP CRCs')
    licence = (ROOT / 'docs/bp3d-sellar-native-source-review/upstream-license.html').read_bytes()
    if b'by-sa/2.1/jp' not in licence:
        raise ValueError('Original upstream4.3 grant not established')
    (evidence / 'upstream-bodyparts-license.html').write_bytes(licence)
    parts, checks = {}, []
    for row in receipt['objects']:
        raw = (source / row['filename']).read_bytes()
        if sha(raw) != row['sha256']: raise ValueError('Original OBJ changed')
        header = {}
        for line in raw.decode().splitlines():
            if line.startswith('#') and ':' in line:
                k,v = line[1:].split(':',1); header[k.strip()] = v.strip()
        fid = header.get('File ID')
        if fid not in EXPECTED or header.get('Compatibility version') != '4.3' or header.get('Concept ID') != EXPECTED[fid]:
            raise ValueError('Original source identity/version differs')
        v,n,f,nf = read_obj(raw.decode())
        if len(v) != len(n) or not np.array_equal(f,nf) or not np.isfinite(v).all() or not np.isfinite(n).all():
            raise ValueError('Original position/normal/face association differs')
        original_path = originals / (fid + '.obj.gz'); original_path.write_bytes(gzip.compress(raw,mtime=0))
        pos = v.astype('<f4'); normals = n.astype('<f4'); faces = f.astype('<u4')
        decoded = struct.pack('<4sII', b'BP3D', len(v), f.size) + pos.tobytes() + normals.tobytes() + faces.tobytes()
        encoded = gzip.compress(decoded,mtime=0); pid = ATLAS + '-' + fid.lower(); (output / (pid + '.bin.gz')).write_bytes(encoded)
        source_index = np.unique(v,axis=0,return_inverse=True)[1]; welded = source_index[f]
        edges = np.sort(np.concatenate([welded[:,[0,1]],welded[:,[1,2]],welded[:,[2,0]]]),axis=1)
        counts = np.unique(edges,axis=0,return_counts=True)[1]
        area2 = np.linalg.norm(np.cross(v[f[:,1]]-v[f[:,0]],v[f[:,2]]-v[f[:,0]]),axis=1)
        quality = {'exact_position_boundary_edges': int((counts==1).sum()),
                   'exact_position_nonmanifold_edges': int((counts>2).sum()), 'zero_area_faces': int((area2==0).sum()),
                   'exact_position_welding_for_diagnostics_only': True}
        name = header['English name'] + ' · original source ' + fid
        parts[pid] = {'id': pid, 'name': name, 'file': '/app/anatomy/' + ATLAS + '/' + pid + '.bin.gz',
                      'sha256': sha(encoded), 'decoded_sha256': sha(decoded), 'vertices': len(v), 'triangles': len(f),
                      'bounds': [pos.min(0).tolist(),pos.max(0).tolist()], 'source_element_id': fid,
                      'source_fma': EXPECTED[fid], 'source_representation_id': header['Representation ID'],
                      'original_source_header': header, 'original_OBJ_sha256': sha(raw),
                      'source_positions_float64_sha256': sha(v.astype('<f8').tobytes()),
                      'source_normals_float64_sha256': sha(n.astype('<f8').tobytes()),
                      'source_faces_int64_sha256': sha(f.astype('<i8').tobytes()),
                      'source_normal_faces_int64_sha256': sha(nf.astype('<i8').tobytes()),
                      'maximum_Float32_position_error_mm': float(np.abs(pos.astype(float)-v).max()),
                      'maximum_Float32_normal_error': float(np.abs(normals.astype(float)-n).max()),
                      'source_quality': quality, 'layer': 'source-surfaces', 'clinical_fidelity': 'unverified'}
        checks.append(parts[pid])
    if {p['source_element_id'] for p in parts.values()} != set(EXPECTED):
        raise ValueError('Complete original source set differs')
    lo = np.min([p['bounds'][0] for p in parts.values()],axis=0); hi = np.max([p['bounds'][1] for p in parts.values()],axis=0)
    notes = [
      'Three complete original BodyParts3D4.3 source objects: right common, external and internal carotid arterial trunks. These are curated adult-male TARO reference surfaces with manual editing, not native CTA/MRA segmentation, a normal atlas approval or the patient being reported.',
      'Original source coordinates, positions, authored normals and face order are retained with measured Float32 transport error. No smoothing, fitting, decimation, repair, capping, component deletion, artificial branch bridge or cross-case registration is supplied.',
      'Original source parts are inspected together in their own coordinates; biological junction continuity, contact/overlap, every arterial branch and complete anatomical extent remain unapproved. Closed source meshes or numerical contacts do not establish physiological vessel endpoints or patency.',
      'The left ICA mapping conflict and unmapped producer-labelled left/mirrored forms are not substituted into this atlas. No mirrored right vessel is fabricated as independent left anatomy. Missing left and other reporting structures remain explicit requirements.',
      'These gross source surfaces do not independently separate lumen, intima, media, adventitia, plaque, thrombus, dissection channels, stenosis, near-occlusion or collateral flow. Do not measure patient NASCET stenosis or diagnose disease from this reference.',
      'Source millimetres follow the original headers; native acquisition calibration, effective thin-wall resolution and independent patient axes are unverified. Camera labels use source coordinates. Display colours distinguish source objects and are not photographic tissue colours.',
      'BodyParts3D, Copyright 2008 Database Center for Life Science (DBCLS), licensed under CC BY-SA2.1 Japan. Adaptation: unchanged original source surfaces in BP3D transport with measured Float32 conversion and illustrative colours. The geometric adaptation remains CC BY-SA2.1 Japan; the separate archive4.0 CC BY4.0 grant is not applied.'
    ]
    region = {'title': 'Original right common / external / internal carotid source trunks', 'side': 'producer-labelled right; source coordinates',
              'parts': [{'id': pid,'layer':'source-surfaces'} for pid in parts], 'layers': [['source-surfaces','Complete original source surfaces']],
              'source_up_range': [float(lo[2]),float(hi[2])], 'focus_bounds': [lo.tolist(),hi.tolist()],
              'source_coordinate_cameras': True, 'uncropped_label': 'Complete retained right source objects · reporting anatomy incomplete',
              'source_assembly_anatomically_approved': False}
    manifest = {'dataset': 'Original BodyParts3D4.3 right carotid source surfaces · partial reporting scope',
                'source_url': 'https://lifesciencedb.jp/bp3d/', 'license':'CC BY-SA 2.1 Japan','license_url':LICENSE_URL,
                'coordinate_system': {'basis':'original BodyParts3D4.3 OBJ XYZ','units':'source-declared millimetres; acquisition calibration unverified',
                                      'unit_meters':.001,'display_basis':'native-bp3d-z-up','registration':'No current-patient or publication-image registration'},
                'parts':parts,'regions':{'carotid-right-source':region},'default_region':'carotid-right-source',
                'viewer_notes':notes,'source_case_id':'BodyParts3D4.3-curated-reference',
                'clinical_approval':False,'complete_reporting_anatomy_approved':False,
                'source_geometry_smoothed_repaired_fitted_cropped_or_merged':False,
                'original_source_faces_preserved_in_order':True,'original_source_normals_used':True,
                'runtime_promoted':True,'runtime_promotion_scope':'Software registration/transport only; no anatomical or clinical approval',
                'total_triangles':sum(p['triangles'] for p in parts.values())}
    save(output / 'manifest.json',manifest)
    (output / 'ATTRIBUTION.md').write_text('# Original right carotid source surfaces\n\n' + '\n\n'.join(notes) +
                                         '\n\nLicence: ' + LICENSE_URL + '\nOriginal source: https://lifesciencedb.jp/bp3d/\n')
    save(evidence / 'original-right-carotid-acquisition.json',receipt)
    save(evidence / 'original-right-carotid-transport.json',{'objects':checks,'original_faces_and_normals_retained':True,
         'source_geometry_repaired_or_merged':False,'anatomical_or_clinical_approval':False,'manifest_sha256':sha((output/'manifest.json').read_bytes())})
    print(len(parts),'original objects;',manifest['total_triangles'],'unchanged triangles; no anatomical approval.')

if __name__ == '__main__':
    p=argparse.ArgumentParser();p.add_argument('--source-root',type=Path,required=True);package(p.parse_args().source_root)
