#!/usr/bin/env python3
"""Preserve original4.3 sellar source objects with separate alternatives and a held ICA identity."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import struct
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
ATLAS='bp3d-sella-4.3'
LICENSE='CC BY-SA 2.1 Japan'
LICENSE_URL='https://creativecommons.org/licenses/by-sa/2.1/jp/'
SOURCE_URL='https://lifesciencedb.jp/bp3d/'
CREDIT='BodyParts3D, Copyright 2008 Database Center for Life Science (DBCLS), licensed under CC BY-SA 2.1 Japan.'
HELD={'FJ3483'}
GROUPS={
    'sella-gross-default':['FJ1796','FJ7501','FJ7501M','FJ7502','FJ7502M','FJ7503','FJ7503M'],
    'gland-source-2011':['FJ1796'],
    'gland-source-2014':['FJ3848'],
    'optic-reduced-source':['FJ7501','FJ7501M','FJ7502','FJ7502M','FJ7503','FJ7503M'],
    'optic-elongated-source':['FJ7501','FJ7501M','FJ7502','FJ7502M','FJ7505','FJ7505M'],
    'right-ICA-source-2011':['FJ1682'],
    'right-ICA-source-2014':['FJ4993'],
}
NOTES=[
    'Original curated BodyParts3D4.3 source geometry, not a native acquisition, complete sellar examination, normal atlas approval or the patient being reported. No MRI registration or fitted transform is supplied.',
    'Two original pituitary objects occupy essentially the same region. Reduced and elongated chiasm pairs are separate source forms. They are alternatives for inspection, not extra gland layers or additional physical chiasms.',
    'The default inspection preset uses the first original manifest pituitary object and the reduced chiasm form. This deterministic selection does not imply anatomical superiority. Alternative forms remain independently accessible; right ICA source objects remain separate from the default assembly.',
    'The reduced chiasm pair retains a source X gap of0.72179mm; the elongated pair has source bounding-box X overlap of1.404735mm. No tissue bridge, fusion, removal or repair hides these source assembly limits.',
    'Both right ICA objects are retained separately. They have overlapping source course/extent and are not assembled as two independent arteries or complementary branches. Fine lumen, wall layers and acquired patency are unapproved.',
    'The object mapped as left ICA (FJ3483) is held: its filename names left common carotid artery and its source Z extent1307.39–1373.68mm is far below the gland1522.57–1535.54mm. No published left sellar ICA part is substituted or mirrored.',
    'M-suffix optic objects and right-source filenames remain declared producer source forms. They are not independently acquired bilateral patient anatomy. The catalogue synonym first cranial nerve is not propagated; optic nerve means CNII.',
    'Each original position/normal/face and source header remains in the original OBJ evidence. BP3D Float32 transport has measured conversion error; source decimal arrays and original face order are retained independently. No smoothing, capping, welding, fitting, crop, decimation or source component deletion is performed.',
    'Source coordinates and millimetres follow original OBJ declarations. Independent native acquisition calibration, patient axes, source resolution, continuous gland/optic/vascular junctions, self/inter-part contacts and tiny tissue boundaries remain unapproved. Camera labels must use source coordinates.',
    'No independently separated gland lobes/capsule, optic sheath/fascicles, cavernous walls/channels, neural branches, complete arterial branches, microscopic invasion or physiological function is supplied. All840 reporting component requirements remain unapproved.',
    CREDIT+' Adaptation: unchanged source surfaces in BP3D transport, measured Float32 conversion, illustrative display colour only. The geometric adaptation is distributed under the same CC BY-SA2.1 Japan licence; no archive4.0 CC BY4.0 grant is applied.',
]


def sha(raw):return hashlib.sha256(raw).hexdigest()


def packed(raw):
    encoded=bytearray(gzip.compress(raw,compresslevel=9,mtime=0));encoded[9]=255
    if gzip.decompress(encoded)!=raw:raise ValueError('Lossless source transport changed')
    return bytes(encoded)


def package(source):
    import numpy as np
    from tools.anatomy_sources.review_bodyparts_pancreatic_geometry import read_obj
    receipt=json.loads((source/'upstream-acquisition.json').read_text())
    if (receipt['version_manifest']!='4.3' or receipt['upstream_default_license']!=LICENSE
            or receipt['source_geometry_altered'] or len(receipt['objects'])!=13):
        raise ValueError('Complete original4.3 source and actual upstream grant required')
    output=ROOT/'web/anatomy'/ATLAS;output.mkdir(parents=True,exist_ok=True)
    evidence=ROOT/'docs/bp3d-sellar-native-source-review';evidence.mkdir(parents=True,exist_ok=True)
    (evidence/'upstream-acquisition.json').write_bytes((source/'upstream-acquisition.json').read_bytes())
    (evidence/'upstream-license.html').write_bytes((source/'upstream-license.html').read_bytes())
    (evidence/'FMA2Obj-4.3.txt.gz').write_bytes(packed((source/'FMA2Obj-4.3.txt').read_bytes()))
    review=json.loads((source/'geometry-review/original-obj-geometry-review.json').read_text())
    if not review['all_expected_original_objects_inspected'] or review['expected_original_object_count']!=13:
        raise ValueError('All original objects must be reviewed before transport')
    (evidence/'original-obj-geometry-review.json').write_bytes((source/'geometry-review/original-obj-geometry-review.json').read_bytes())
    originals=evidence/'original-objects';originals.mkdir(exist_ok=True)
    parts={};transport=[];holds=[]
    for row in receipt['objects']:
        fid=row['id'];raw=(source/'objects'/(fid+'.obj')).read_bytes()
        if sha(raw)!=row['sha256']:raise ValueError('Original source changed')
        (originals/(fid+'.obj.gz')).write_bytes(packed(raw))
        v,n,f,nf=read_obj(raw.decode())
        if len(v)!=len(n) or not np.array_equal(f,nf):
            raise ValueError('Original per-vertex authored normal/face association differs')
        if fid in HELD:
            holds.append({**row,'actual_bounds_mm':[v.min(0).tolist(),v.max(0).tolist()],
                'reason':'Left-ICA FMA label conflicts with common-carotid filename and source coordinate extent; no left sellar ICA representation granted.',
                'in_published_anatomical_part_list':False,'source_original_retained':True})
            continue
        pid=ATLAS+'-'+fid.lower();positions=v.astype('<f4');normals=n.astype('<f4');indices=f.astype('<u4')
        payload=struct.pack('<4sII',b'BP3D',len(v),f.size)+positions.tobytes()+normals.tobytes()+indices.tobytes()
        decoded_v=np.frombuffer(payload,'<f4',count=v.size,offset=12).reshape(v.shape)
        decoded_n=np.frombuffer(payload,'<f4',count=n.size,offset=12+positions.nbytes).reshape(n.shape)
        decoded_f=np.frombuffer(payload,'<u4',count=f.size,offset=12+positions.nbytes+normals.nbytes).reshape(f.shape)
        if not (np.array_equal(decoded_v,positions) and np.array_equal(decoded_n,normals) and np.array_equal(decoded_f,f)):
            raise ValueError('Every original source face/normal association must survive transport')
        filename=pid+'.bin.gz';encoded=packed(payload);(output/filename).write_bytes(encoded)
        record={'id':pid,'name':row['source_label']+' · original source '+fid,'file':'/app/anatomy/'+ATLAS+'/'+filename,
            'sha256':sha(encoded),'decoded_sha256':sha(payload),'vertices':len(v),'triangles':len(f),
            'bounds':[positions.min(0).tolist(),positions.max(0).tolist()],
            'source_element_id':fid,'source_fma':row['source_fma'],'source_representation_id':row['representation_id'],
            'source_obj_name':row['source_obj_name'],'source_obj_group':row['source_obj_group'],
            'original_source_header':row['original_obj_header'],'original_OBJ_sha256':sha(raw),
            'source_positions_float64_sha256':sha(v.astype('<f8').tobytes()),'source_normals_float64_sha256':sha(n.astype('<f8').tobytes()),
            'source_faces_int64_sha256':sha(f.astype('<i8').tobytes()),'source_normal_faces_int64_sha256':sha(nf.astype('<i8').tobytes()),
            'maximum_Float32_position_error_mm':float(np.abs(positions.astype(float)-v).max()),
            'maximum_Float32_normal_error':float(np.abs(normals.astype(float)-n).max()),
            'source_mirrored_ID':fid.endswith('M'),'layer':'source-surfaces','clinical_fidelity':'unverified'}
        parts[pid]=record;transport.append(record)
    if len(parts)!=12 or len(holds)!=1:raise ValueError('Exact original source hold/part accounting differs')
    regions={}
    for key,ids in GROUPS.items():
        values=[parts[ATLAS+'-'+fid.lower()] for fid in ids]
        lo=np.min([p['bounds'][0] for p in values],axis=0);hi=np.max([p['bounds'][1] for p in values],axis=0)
        regions[key]={'title':key.replace('-',' ')+' · partial source inspection','side':'original source coordinates',
            'parts':[{'id':p['id'],'layer':'source-surfaces'} for p in values],
            'layers':[['source-surfaces','Complete original source surfaces']],
            'source_coordinate_cameras':True,'source_up_range':[float(lo[2]),float(hi[2])],
            'focus_bounds':[lo.tolist(),hi.tolist()],'uncropped_label':'Complete retained source extent · full reporting anatomy incomplete',
            'alternatives_not_new_tissues':True,'source_assembly_anatomically_approved':False}
    manifest={'dataset':'Original BodyParts3D4.3 sellar source surfaces · partial',
        'source_url':SOURCE_URL,'license':LICENSE,'license_url':LICENSE_URL,
        'coordinate_system':{'basis':'original BodyParts3D4.3 OBJ XYZ coordinates','units':'millimetres as declared in original OBJ headers; acquisition calibration unverified',
            'unit_meters':.001,'display_basis':'native-bp3d-z-up','registration':'No fit or registration to clinical MRI or a current patient',
            'direction_labels':'Source X/Y/Z; independent patient axes unverified'},
        'parts':parts,'regions':regions,'default_region':'sella-gross-default','viewer_notes':NOTES,
        'source_case_id':'BodyParts3D4.3-curated-source','source_context':'Curated adult source atlas objects; original acquisition, fine anatomical interfaces and current-patient correspondence unverified.',
        'complete_reporting_anatomy_approved':False,'clinical_approval':False,'runtime_promoted':True,
        'runtime_promotion_scope':'Software registration and original-source transport only; no anatomical or clinical approval.',
        'source_geometry_smoothed_repaired_fitted_cropped_or_merged':False,
        'original_objects_retained_in_evidence':13,'held_source_element_ids':sorted(HELD),
        'published_source_parts':12,'total_triangles':sum(p['triangles'] for p in parts.values()),
        'original_source_faces_preserved_in_order':True,'original_source_normals_used':True,
        'default_selection_basis':'First original manifest gland object and reduced chiasm pair, for display determinism only; no anatomical superiority implied.'}
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n')
    notice=('# BodyParts3D4.3 original source geometric adaptation\n\n'+CREDIT+'\n\nLicence: '+LICENSE_URL+'\n\n'
        'Source: https://lifesciencedb.jp/bp3d/ ; original licence evidence: https://lifesciencedb.jp/bp3d/info_en/license/index.html .\n\n'
        'The source surfaces and this geometric transport adaptation are distributed under CC BY-SA2.1 Japan. '
        'The separate archived4.0 CC BY4.0 grant is not applied to upstream4.3. Changes are format conversion to BP3D Float32 positions/normals and Uint32 face indices, with measured conversion errors. '
        'Source face order and authored normal associations remain. No source fitting, smoothing, repair, crop, decimation, welding or artificial bridge is performed. '
        'Original OBJ files, source headers, ambiguity/identity holds and exact source arrays are retained in the review evidence. '
        'Display colours identify source objects and are not photographic tissue or pathology. No anatomical/clinical endorsement or complete reporting coverage is claimed.\n')
    (output/'ATTRIBUTION.md').write_text(notice)
    (evidence/'held-source-identities.json').write_text(json.dumps(holds,indent=2)+'\n')
    (evidence/'transport-review.json').write_text(json.dumps({'atlas':ATLAS,'parts':transport,
        'original_objects':13,'held_objects':1,'published_parts':12,'source_normals_recomputed':False,
        'source_original_faces_or_components_deleted':False,'published_scope_excludes_held_FJ3483':True,'original_OBJ_bytes_preserved':True,
        'geometric_adaptation_license':LICENSE,'clinical_approval':False,'all840component_requirements_approved':False},indent=2)+'\n')
    print('12 original source parts packaged;13original objects preserved; left ICA held; no anatomy approval.')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--source-root',type=Path,required=True)
    package(parser.parse_args().source_root)
