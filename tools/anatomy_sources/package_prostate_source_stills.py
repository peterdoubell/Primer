#!/usr/bin/env python3
"""Add original complete T2 planes using source DICOM windows; preserve existing references."""
import hashlib
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image
from tools.anatomy_sources.package_aortic_rupture_figures import append_evidence
from tools.anatomy_sources.package_prostate_biopsy_reference import PROOF,SOURCE,URL,GRANT,ATTRIBUTION
from primer import radiology_catalog as catalog
from primer.curriculum import Curriculum
from tools.check_radiology_fidelity import digest

PREFIX='open-prostate-biopsy0001-T2-'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def package():
    source=json.loads((PROOF/'original-source-review.json').read_text());t2=next(v for v in source['MRI_series'] if v['role']=='T2');raw=(SOURCE/'T2-original-u16.bin').read_bytes()
    if sha(raw)!=t2['stored_samples_sha256']:raise ValueError('Source T2 changed')
    array=np.frombuffer(raw,'<u2').reshape(t2['geometry']['shape']);objects={r['SOPInstanceUID']:r for r in source['objects']};rows=[];assets=[];proof=[]
    for index in [15,25,35]:
        record=objects[t2['SOPInstanceUIDs_in_source_plane_order'][index]];center=float(record['source_WindowCenter']);width=float(record['source_WindowWidth'])
        if width<=1 or record['source_VOILUTFunction'] not in ['','LINEAR']:raise ValueError('Unsupported source VOI')
        pixels=np.clip(np.rint((array[index].astype(float)-(center-.5-(width-1)/2))*255/(width-1)),0,255).astype('u1')
        ident=PREFIX+str(index);local='web/reference-media/radiology-open/prostate-biopsy0001-T2-'+str(index)+'.png';path=ROOT/local;Image.fromarray(pixels).save(path)
        context={'setting':'in_vivo','laterality':'unknown','population':{'life_stage':'adult','age_years':64,'sex':'male'},'extent':'local','depicted_state':'source_prostate_case_with_suspicious_ROI','selected_panels':['full'],'panel_types':{'full':'MRI'},'panel_states':{'full':'source_case_context_only'},'source_case_groups':{'Prostate-MRI-US-Biopsy-0001':['full']},'source_native_frame_association_verified':True,'full_reporting_or_histological_boundary_approval':False}
        limit='Complete original256×256 T2 source plane, source native slice index'+str(index)+'. Original DICOM VOI window maps stored values to an8-bit display PNG; every original uint16 value remains in the complete MRI viewer. No crop, new labels or tissue segmentation. Source sampling0.6640625×0.6640625×1.5mm does not establish effective microanatomical resolution. Suspicious ROI, source case appearance and current pathology/scoring remain separate; every reported tissue/interface is not approved.'
        row={'id':ident,'kind':'clinical-image','modality':'MRI','src':'/app/'+local.removeprefix('web/'),'sha256':sha(path.read_bytes()),'width':256,'height':256,'source_url':URL,'asset_source_url':record['url'],'figure_url':record['url'],'alt':'Complete original prostate source T2 plane '+str(index)+'.','caption':'Original case0001 T2 plane '+str(index)+' of59 · source DICOM display window; no current diagnosis assigned.','source_caption_full':'Actor display of complete original source T2 MRI plane, using the original DICOM window. Source SOPInstanceUID '+record['SOPInstanceUID']+'.','clinical_panels':['full'],'source_context':context,'image_state':context['depicted_state'],'structures_visible':['Source-local prostate and acquired adjacent tissue; independent whole fine-anatomical coverage pending'],'limits':limit,'license':'CC BY 4.0','license_url':GRANT,'attribution':ATTRIBUTION,'rights_reviewed_on':'2026-10-08','rights_review':'Original collection CC BY4 grant and whole original DICOM object hashes verified. Actor8-bit VOI display adaptation is explicit; raw stored values retained separately.'}
        catalog._validate_source_panel_roles(row);rows.append(row)
        item={'id':ident,'source_slice_index':index,'source_SOPInstanceUID':record['SOPInstanceUID'],'source_object_sha256':record['sha256'],'original_plane_stored_samples_sha256':sha(array[index].tobytes()),'source_window_center':center,'source_window_width':width,'source_VOILUT':'LINEAR','display_pixel_sha256':sha(pixels.tobytes()),'display_file_sha256':sha(path.read_bytes()),'source_plane_matrix_cropped_resampled_or_relabelled':False,'actor_display_adaptation':'Original source DICOM window to8-bit grayscale; raw source stored values preserved in full viewer'};proof.append(item)
        evidence={'source':{'dataset_doi':'10.7937/TCIA.2020.A61IOC1A','data_license':'CC BY 4.0','case_id':'Prostate-MRI-US-Biopsy-0001','source_role':'T2','source_series_UID':t2['SeriesInstanceUID'],'whole_object_md5_and_scalar_readback_verified':True,'source_MRI_stored_sample_count':t2['stored_samples'],'source_T2_payload_sha256':t2['stored_samples_sha256'],'source_object_sha256':record['sha256'],'source_plane_stored_samples_sha256':item['original_plane_stored_samples_sha256'],'source_SOPInstanceUID':record['SOPInstanceUID']},'source_shape':t2['geometry']['shape'],'source_dtype':'<u2','source_sampling_zyx_mm':[1.5,.6640625,.6640625],'source_display_adaptation':'original_DICOM_LINEAR_VOI_to_8bit','figure_sha256':row['sha256'],'clinical_approval':False,'source_voxels_changed':False,'model_geometry_overlaid':False,'planes':[{'axis':0,'index':index,'source_resampling':False}],'original_window_center':center,'original_window_width':width,'display_pixel_sha256':item['display_pixel_sha256']}
        ep=path.with_suffix('.json');ep.write_text(json.dumps(evidence,indent=2)+'\n')
        row.update(origin='native-volume-sections',figure_title='Original prostate source T2 plane '+str(index),derivation={'evidence_url':'/app/'+str(ep.relative_to(ROOT/'web')),'evidence_sha256':sha(ep.read_bytes())})
        assets.append({'id':ident,'kind':'clinical_image','name':row['alt'],'local_path':local,'sha256':row['sha256'],'modality':'MRI','investigation_ids':['ra.mri-prostate'],'structure_ids':[],'requirement_coverage':{},'source_context':context,'source':{'url':URL,'asset_url':record['url'],'license':{'name':'CC BY 4.0','url':GRANT,'commercial_use':True,'redistribution':True,'review_status':'verified','evidence_path':str((PROOF/'publisher-roles-and-rights-review.json').relative_to(ROOT)),'evidence_sha256':sha((PROOF/'publisher-roles-and-rights-review.json').read_bytes()),'attribution':ATTRIBUTION,'reviewed_at':'2026-10-08'}},'pixel_provenance':item,'anatomical_review':{'status':'pending','reason':'Selected native planes do not supply every reported prostate/pelvic structure or current histology.'}})
    p=ROOT/'data/radiology/radiology-open-images.json';d=json.loads(p.read_text());d['ra.mri-prostate']=[r for r in d.get('ra.mri-prostate',[]) if not r['id'].startswith(PREFIX)]+rows;p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n');append_evidence(ROOT/'data/radiology/radiology-asset-evidence.json',assets,prefix=PREFIX)
    p=ROOT/'data/radiology/reporting-steps/abdomen.json';text=p.read_text();start=text.index('{',text.index('"ra.mri-prostate"'));node,end=json.JSONDecoder().raw_decode(text,start)
    for step in node['steps']:step['images']=[i for i in step.get('images',[]) if not i.startswith(PREFIX)]
    for index in [0,1,3]:node['steps'][index]['images'] += [r['id'] for r in rows]
    p.write_text(text[:start]+json.dumps(node,indent=2,ensure_ascii=False).replace('\n','\n    ')+text[end:])
    (PROOF/'source-T2-display-stills-review.json').write_text(json.dumps({'source_T2_stored_samples_sha256':t2['stored_samples_sha256'],'complete_original_source_plane_matrix_retained':True,'figures':proof,'clinical_anatomical_or_full_reporting_approval_granted':False},indent=2)+'\n')
    for value in vars(catalog).values():
        if callable(getattr(value,'cache_clear',None)):value.cache_clear()
    ref=catalog.detail(Curriculum(),catalog.resolve('ra.mri-prostate'))['radiology_reference'];p=ROOT/'data/radiology/non-msk-structure-requirements.json';d=json.loads(p.read_text());next(r for r in d['investigations'] if r['investigation_id']=='ra.mri-prostate')['source_contract_sha256']=digest({k:ref.get(k) for k in ['reporting','report_templates','walkthrough','reading']});p.write_text(json.dumps(d,indent=2)+'\n')
    print('Three original complete T2 source planes added; earlier clinical references preserved')

if __name__=='__main__':package()
