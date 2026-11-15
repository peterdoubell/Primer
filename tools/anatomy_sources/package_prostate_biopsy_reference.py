#!/usr/bin/env python3
"""Package complete original operator surfaces and original MRI grids as partial references."""
import base64
import hashlib
import json
import struct
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
import numpy as np
from tools.anatomy_sources.review_prostate_biopsy0001 import binary_stl,SOURCE,OUT as PROOF
from tools.anatomy_sources.package_laryngeal_phonation_reference import canonical_gzip
from tools.anatomy_sources.package_aortic_rupture_figures import append_evidence

ATLAS='prostate-biopsy0001';FAMILY='prostate-source';OUT=ROOT/'web/anatomy'/ATLAS
URL='https://www.cancerimagingarchive.net/collection/prostate-mri-us-biopsy/'
GRANT='https://creativecommons.org/licenses/by/4.0/'
ATTRIBUTION='Natarajan,S.,Priester,A.,Margolis,D.,Huang,J.,and Marks,L.(2020). Prostate MRI and Ultrasound With Pathology and Coordinates of Tracked Biopsy,version2. TCIA DOI10.7937/TCIA.2020.A61IOC1A. CC BY4.0. Adaptation: complete source arrays/face transport,illustrative lighting and overlays; no endorsement implied.'
NAMES={'prostate':'source prostate outline','suspicious_target1':'suspicious source target ROI'}
NOTES=[
 'Source case Prostate-MRI-US-Biopsy-0001,source64-year-old male. These are operator source references,not a normal whole-prostate atlas or the current patient.',
 'All1,198 original prostate faces and4,280 suspicious-target faces remain. The prostate was outlined semi-automatically in Profuse with user-adjustable contours/vertices; accuracy is user-dependent. A suspicious MRI biopsy-target ROI is not proven complete tumour or histological extent.',
 'The delivered model/MRI/SEG frame identifiers and independent all-voxel comparison support the source DICOM LPS association. No fitting,axis flip,resampling,smoothing,capping or component deletion was applied. Original mesh and producer-derived mask differ at480 gland and5 ROI voxel centres; every original value remains. This numeric correspondence is not independent anatomical accuracy.',
 'The source encapsulated models omit the required measurement-units code. Display millimetre scale is inferred from the matching producer MRI/SEG grids and numeric correspondence; full DICOM model conformance and independent clinical registration are not claimed.',
 'The source supplies complete T2,producer ADC and calculated-DWI grids. ADC and calculated DWI use their own coarser source grid. They have no supplied rescale/physical ADC calibration,original native high-b series or DCE. Source study description and private diffusion metadata do not supply missing acquisitions or current assessment.',
 'Only the original T2 grid has the two producer-derived masks. They were rasterized from source STL and are not independent native manual voxel annotations. No mask is fitted or resampled onto ADC/DWI.',
 'The41 idealized PI-RADS regions,zones,outer fibromuscular boundary,pseudocapsule,ducts,nerves,vessels,seminal vesicles,sphincter,nodes,bone and actual extension/treatment interfaces still require faithful source coverage and independent review. The whole-gland outline and one suspicious ROI do not meet full reporting coverage.',
 'Source ultrasound has different private voxel-size tags and lacks standard patient orientation/position. Publisher nonrigid MRI-to-US target mapping is not this viewer\'s native registration. Source Likert-like scores do not assign current PI-RADS2.1. Source clinical/pathology/biopsy results are not inferred.',
 ATTRIBUTION]

def sha(raw):return hashlib.sha256(raw).hexdigest()
def compressed(raw):return base64.b64encode(canonical_gzip(raw)).decode()

def package():
    source=json.loads((PROOF/'original-source-review.json').read_text());coordinate=json.loads((PROOF/'coordinate-correspondence-review.json').read_text())
    if not coordinate['source_MRI_model_frame_association_numerically_verified'] or coordinate['mismatch_source_masks_changed_or_replaced']:raise ValueError('Original source coordinate review changed')
    OUT.mkdir(parents=True,exist_ok=True);parts={};transport=[]
    for role,name in NAMES.items():
        row=next(r for r in source['original_surfaces'] if r['role']==role);original=(PROOF/(role+'-original.stl')).read_bytes()
        if sha(original)!=row['source_STL_sha256']:raise ValueError('Original STL changed')
        records=binary_stl(original);corners=records['vertices'];positions=corners.reshape(-1,3).astype('<f4');faces=np.arange(len(positions),dtype='<u4').reshape(-1,3)
        normals=np.cross(corners[:,1]-corners[:,0],corners[:,2]-corners[:,0]);length=np.linalg.norm(normals,axis=1)
        if np.any(length==0):raise ValueError('Degenerate source face')
        normals=np.repeat(normals/length[:,None],3,axis=0).astype('<f4')
        raw=struct.pack('<4sII',b'BP3D',len(positions),faces.size)+positions.tobytes()+normals.tobytes()+faces.tobytes();encoded=canonical_gzip(raw)
        ident=ATLAS+'-'+role.replace('_','-');path=OUT/(ident+'.bin.gz');path.write_bytes(encoded)
        if positions.tobytes()!=corners.astype('<f4').tobytes():raise ValueError('Original ordered corners changed')
        parts[ident]={'id':ident,'name':name+' · complete original surface','file':'/app/anatomy/'+ATLAS+'/'+path.name,'sha256':sha(encoded),'decoded_sha256':sha(raw),'vertices':len(positions),'triangles':len(corners),'bounds':[positions.min(0).tolist(),positions.max(0).tolist()],'source_STL_sha256':sha(original),'source_face_corners_sha256':sha(positions.tobytes()),'source_components':1,'source_boundary_edges':0,'source_normals_and_attributes_retained_in_original_STL':True,'transport_normals':'Illustrative geometric face normals; source positions unchanged','color':'#809cad' if role=='prostate' else '#c19a77','layer':'gland' if role=='prostate' else 'target','regions':[FAMILY],'clinical_fidelity':'unverified'}
        transport.append({'role':role,'part_id':ident,'source_triangles':len(corners),'source_position_float32_error':0,'all_original_ordered_face_corners_retained':True,'mesh_sha256':sha(encoded),'decoded_sha256':sha(raw),'clinical_approval':False})
    low=np.min([p['bounds'][0] for p in parts.values()],axis=0);high=np.max([p['bounds'][1] for p in parts.values()],axis=0)
    manifest={'dataset':'Original prostate and suspicious biopsy ROI source surfaces','source_url':URL,'license':'CC BY 4.0','license_url':GRANT,'coordinate_system':{'basis':'LPS','units':'MRI-grid-corresponding inferred source millimetres; original model unit code absent','unit_meters':.001,'display_basis':'native-lps-to-x-left-y-superior-z-anterior','registration':'Delivered source frame association and numeric raster correspondence; clinical/fine anatomical registration not independently approved'},'parts':parts,'regions':{FAMILY:{'title':'Source prostate outline and suspicious ROI · partial reporting anatomy','side':'midline','parts':[{'id':ident,'layer':p['layer']} for ident,p in parts.items()],'layers':[['all','Both original source surfaces'],['gland','Source prostate outline'],['target','Suspicious source target ROI']],'source_coordinate_cameras':True,'source_up_range':[float(low[2]-1),float(high[2]+1)],'focus_bounds':[low.tolist(),high.tolist()],'uncropped_label':'Complete original source surfaces'}},'viewer_notes':NOTES,'total_triangles':5478,'complete_prostate_reporting_geometry_verified':False,'clinical_approval':False,'anatomical_approval':False,'status':'Original partial source reference; independent fine anatomical review pending','runtime_promoted':True}
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');(OUT/'ATTRIBUTION.md').write_text('# Original prostate source reference\n\n'+'\n\n'.join(NOTES)+'\n')
    volumes=[];proofs=[];objects={r['SOPInstanceUID']:r for r in source['objects']}
    for row in source['MRI_series']:
        raw=(SOURCE/(row['role']+'-original-u16.bin')).read_bytes()
        if sha(raw)!=row['stored_samples_sha256']:raise ValueError('Original MRI samples changed')
        windows=[[float(objects[sop]['source_WindowCenter']),float(objects[sop]['source_WindowWidth'])] for sop in row['SOPInstanceUIDs_in_source_plane_order']]
        volumes.append({'role':row['role'],'label':{'T2':'Original transmitted T2','producer_ADC':'Producer-derived ADC · stored units','producer_calculated_DWI':'Producer-calculated DWI'}[row['role']],'shape':row['geometry']['shape'],'affine':row['geometry']['index_to_dicom_lps_mm'],'spacing':[row['geometry']['slice_step_mm'],row['geometry']['index_to_dicom_lps_mm'][1][1],row['geometry']['index_to_dicom_lps_mm'][0][2]],'sha256':sha(raw),'samples':compressed(raw),'native_windows':windows,'source_series_UID':row['SeriesInstanceUID'],'sample_type':'little-endian uint16 original stored values','ImageType':row['ImageType']})
        proofs.append({'role':row['role'],'shape':row['geometry']['shape'],'sample_count':row['stored_samples'],'original_stored_samples_sha256':sha(raw),'original_frame_windows_preserved':True,'source_grid_changed':False})
    shape=next(v['shape'] for v in volumes if v['role']=='T2');mask=np.zeros(shape,'u1');levels=[]
    for bit,(role,name) in enumerate(NAMES.items()):
        row=next(r for r in source['derived_segmentations'] if r['role']==role);raw=(SOURCE/(role+'-derived-SEG-u8.bin')).read_bytes()
        if sha(raw)!=row['stored_samples_sha256']:raise ValueError('Original producer mask changed')
        values=np.frombuffer(raw,'u1').reshape(shape);mask|=values<<bit;centre=np.rint(np.mean(np.argwhere(values),axis=0)).astype(int).tolist()
        levels.append({'level':name,'part_id':transport[bit]['part_id'],'bit':bit,'T2_center_indices':centre,'foreground_voxels':row['foreground_samples'],'source_components':1})
        if not np.array_equal((mask>>bit)&1,values):raise ValueError('Original source label encoding changed')
    data={'case':'Prostate-MRI-US-Biopsy-0001','volumes':volumes,'levels':levels,'mask_shape':shape,'mask_sha256':sha(mask.tobytes()),'mask':compressed(mask.tobytes()),'clinical_approval':False}
    html=OUT/'mri-reference.html';html.write_text((ROOT/'tools/anatomy_sources/prostate_MRI_template.html').read_text().replace('__DATASET_JSON__',json.dumps(data,separators=(',',':'))))
    stored=json.loads(html.read_text().split('<script id="dataset" type="application/json">',1)[1].split('</script>',1)[0])
    import gzip
    for row,v in zip(proofs,stored['volumes']):
        if sha(gzip.decompress(base64.b64decode(v['samples'])))!=row['original_stored_samples_sha256']:raise ValueError('MRI transport readback differs')
    recovered=gzip.decompress(base64.b64decode(stored['mask']))
    if recovered!=mask.tobytes():raise ValueError('Original overlapping labels changed')
    proof={'mesh_transport':transport,'MRI_volumes':proofs,'complete_MRI_stored_sample_count':sum(r['sample_count'] for r in proofs),'complete_two_source_mask_sample_count':2*int(np.prod(shape)),'mask_encoded_sha256':sha(recovered),'every_original_value_and_face_retained':True,'no_mask_overlay_or_resampling_on_ADC_or_DWI':True,'source_unit_code_defect_retained_and_scale_inference_disclosed':True,'viewer_sha256':sha(html.read_bytes()),'script_sha256':sha((OUT/'mri-reference.js').read_bytes()),'clinical_anatomical_or_full_reporting_approval_granted':False}
    (PROOF/'reader-transport-review.json').write_text(json.dumps(proof,indent=2)+'\n')
    volume={'id':ATLAS+'-complete-source-MRI','modality':'MRI','src':'/app/anatomy/'+ATLAS+'/mri-reference.html','sha256':proof['viewer_sha256'],'script_sha256':proof['script_sha256'],'level_by_part':{r['part_id']:r['level'] for r in levels},'title':'Inspect complete original T2, source ADC and calculated-DWI grids','caption':'Every stored MRI and source-derived mask sample is retained. The masks belong only to T2. Source processing, absent ADC units/DCE/native high-b series and missing model unit code remain explicit; full anatomical/clinical approval is pending.','attribution':ATTRIBUTION,'source_url':URL,'license_url':GRANT}
    p=ROOT/'data/radiology/source-anatomy-references.json';refs=json.loads(p.read_text());refs['ra.mri-prostate']=[r for r in refs.get('ra.mri-prostate',[]) if r['atlas']!=ATLAS]+[{'id':ATLAS+'-operator-surfaces','label':'Original source gland/ROI and matching MRI · partial','atlas':ATLAS,'family':FAMILY,'manifest_url':'/app/anatomy/'+ATLAS+'/manifest.json','manifest_sha256':sha((OUT/'manifest.json').read_bytes()),'initial_layer':'target','initial_cropped':False,'population_note':' '.join(NOTES),'source_volume':volume}];p.write_text(json.dumps(refs,indent=2,ensure_ascii=False)+'\n')
    rights={'name':'CC BY 4.0','url':GRANT,'commercial_use':True,'redistribution':True,'review_status':'verified','evidence_path':str((PROOF/'publisher-roles-and-rights-review.json').relative_to(ROOT)),'evidence_sha256':sha((PROOF/'publisher-roles-and-rights-review.json').read_bytes()),'attribution':ATTRIBUTION,'reviewed_at':'2026-10-08'}
    append_evidence(ROOT/'data/radiology/radiology-asset-evidence.json',[{'id':ident,'kind':'model','name':p['name'],'local_path':p['file'].replace('/app/','web/',1),'sha256':p['sha256'],'investigation_ids':['ra.mri-prostate'],'structure_ids':[],'requirement_coverage':{},'source':{'url':URL,'license':rights},'anatomical_review':{'status':'pending','reason':'Original operator gland and suspicious ROI do not supply every reported prostate/pelvic tissue or current histology.'}} for ident,p in parts.items()],prefix=ATLAS+'-')
    print('All5478 original faces and4776960 MRI samples packaged on their three unchanged source grids')

if __name__=='__main__':package()
