#!/usr/bin/env python3
"""Preserve every float32 sample in the three matching source MRI phases."""
import base64,gzip,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
import numpy as np
from tools.anatomy_sources.package_laryngeal_phonation_reference import canonical_gzip
from tools.anatomy_sources.package_ispy_expert_reference import ATLAS,OUT,PROOF,SOURCE,GRANT,ATTRIBUTION
CACHE=Path('/Users/peter/Documents/ChatGPT/Primer/.research/breast-native-MRI-source/expert-original-ISPY1_1002')
def sha(raw):return hashlib.sha256(raw).hexdigest()
def payload(row):
    encoded=(CACHE/row['file']).read_bytes()
    if sha(encoded)!=row['source_file_sha256']:raise ValueError('Original source file changed')
    raw=gzip.decompress(encoded);count=row['sample_count'];start=row['voxel_offset'];data=raw[start:start+count*row['bits']//8]
    if sha(data)!=row['payload_sha256'] or row['source_dtype']!='<f4':raise ValueError('Original processed source payload changed')
    if row['slope_intercept'][0] not in [0,1] or row['slope_intercept'][1]!=0:raise ValueError('Original source scaling requires review')
    return data

def package():
    native=json.loads((PROOF/'original-source-review.json').read_text());records=native['source_records'];maskrow=next(r for r in records if r['file'].startswith('masks_stv_manual/'));original=payload(maskrow);values=np.frombuffer(original,'<f4');mask=values.astype('u1');recovered=mask.astype('<f4').tobytes()
    if recovered!=original or set(np.unique(values))!={0,1}:raise ValueError('Original expert label encoding is not reversible')
    phases=[];proofs=[]
    for phase,label in enumerate(['Source0000 · producer precontrast','Source0001 · producer early','Source0002 · producer late']):
        row=next(r for r in records if r['file'].startswith('images_bias-corrected_resampled_zscored_nifti/') and ('DCE_'+str(phase).zfill(4)+'_') in r['file']);data=payload(row)
        if row['shape']!=maskrow['shape'] or row['affine']!=maskrow['affine']:raise ValueError('Expert mask/MRI source grid differs')
        phases.append({'label':label,'source_file':row['file'],'sha256':sha(data),'samples':base64.b64encode(canonical_gzip(data)).decode()});proofs.append({'source_file':row['file'],'source_file_sha256':row['source_file_sha256'],'original_payload_sha256':sha(data),'all_original_samples_preserved':True})
    shape=maskrow['shape'];A=np.array(maskrow['affine']);levels=[{'level':'expert structural tumour','part_id':ATLAS+'-expert-structural-tumour','bit':0,'center_indices':[98,89,77],'foreground_voxels':5091,'source_foreground_components':2}];data={'case':'ISPY1_1002','shape':shape,'spacing':[1,1,1],'affine':A.tolist(),'axes':['P','S','R'],'sample_type':'little-endian float32; original processed source z-scores','phases':phases,'levels':levels,'mask_sha256':sha(mask.tobytes()),'mask':base64.b64encode(canonical_gzip(mask.tobytes())).decode()};html=OUT/'mri-reference.html';html.write_text((ROOT/'tools/anatomy_sources/ispy_MRI_template.html').read_text().replace('__DATASET_JSON__',json.dumps(data,separators=(',',':'))))
    stored=json.loads(html.read_text().split('<script id="dataset" type="application/json">',1)[1].split('</script>',1)[0]);assert gzip.decompress(base64.b64decode(stored['mask']))==mask.tobytes()
    for r,p in zip(proofs,stored['phases']):assert sha(gzip.decompress(base64.b64decode(p['samples'])))==r['original_payload_sha256']
    proof={'shape':shape,'source_phase_count':3,'complete_MRI_float32_sample_count':3*maskrow['sample_count'],'original_expert_mask_sample_count':maskrow['sample_count'],'expert_mask_source_payload_sha256':sha(original),'expert_mask_recovered_float32_sha256':sha(recovered),'mask_encoded_sha256':sha(mask.tobytes()),'all_original_phase_and_mask_values_preserved':True,'phase_payloads':proofs,'viewer_sha256':sha(html.read_bytes()),'script_sha256':sha((OUT/'mri-reference.js').read_bytes()),'source_processed_pitch_is_native_acquisition_resolution':False,'source_sample_geometry_fitted_resampled_cropped_repaired_or_deleted':False,'clinical_approval':False};(PROOF/'MRI-reader-array-review.json').write_text(json.dumps(proof,indent=2)+'\n')
    p=ROOT/'data/radiology/source-anatomy-references.json';refs=json.loads(p.read_text());volume={'id':ATLAS+'-complete-source-MRI','modality':'MRI','src':'/app/anatomy/'+ATLAS+'/mri-reference.html','sha256':proof['viewer_sha256'],'script_sha256':proof['script_sha256'],'level_by_part':{ATLAS+'-expert-structural-tumour':'expert structural tumour'},'title':'Inspect matching complete three-phase processed MRI and expert mask','caption':'Every original distributed processed MRI phase and expert mask sample remains. Source1mm resampled/z-scored grid is not independently verified native resolution,raw registration,calibrated kinetics,current diagnosis or complete breast anatomy. Both manual source components remain.','attribution':ATTRIBUTION,'source_url':SOURCE,'license_url':GRANT}
    for inv in ['ra.mri-breast','ra.breast-cancer-staging']:next(r for r in refs[inv] if r['atlas']==ATLAS)['source_volume']=volume.copy()
    p.write_text(json.dumps(refs,indent=2,ensure_ascii=False)+'\n');print('Three original source MRI phases and complete expert mask preserved:',proof['complete_MRI_float32_sample_count'],'MRI samples')
if __name__=='__main__':package()
