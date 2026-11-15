#!/usr/bin/env python3
"""Package four separate complete source image/annotation pairs and label-cell models."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import struct


def sha(b): return hashlib.sha256(b).hexdigest()


def package(root, project):
    import numpy as np
    from tools.anatomy_sources.review_fedbca_sources import read_nifti
    proof = project/'docs/fedbca-bladder-source-review'
    rows=json.loads((proof/'source-surface-review.json').read_text());metadata=json.loads((root/'fedbca-latest-metadata.json').read_text())
    creators=metadata['metadata']['creators'];authors='; '.join(c['name'] for c in creators)
    credit=authors+'. A multi-center MRI dataset for bladder cancer and baseline evaluations of federated learning in its clinical application, version2, DOI10.5281/zenodo.13622759; Scientific Data DOI10.1038/s41597-024-03971-0. CC BY4.0. Adaptation: lossless distributed-array transport, recorded window/native-index display and exact label-cell boundary geometry; no endorsement implied.'
    script=(project/'tools/anatomy_sources/fedbca_mri_viewer.js').read_bytes();template=(project/'tools/anatomy_sources/fedbca_mri_template.html').read_text()
    entries=[];packages=[]
    for row in rows:
        key=row['case_id'];atlas='fedbca-'+key;folder=project/'web/anatomy'/atlas;folder.mkdir(parents=True,exist_ok=True)
        image_path=root/'all-nifti'/row['source_image_member'];mask_path=root/'all-nifti'/row['source_mask_member']
        image,A,ih=read_nifti(image_path);mask,B,mh=read_nifti(mask_path)
        for array,header,path in [(image,ih,image_path),(mask,mh,mask_path)]:
            if sha(path.read_bytes())!=header['compressed_sha256']:raise ValueError('Original source member changed')
        payloads={}
        for name,array,header in [('image',image,ih),('mask',mask,mh)]:
            raw=array.tobytes(order='F');assert sha(raw)==header['raw_source_voxel_sha256'];packed=gzip.compress(raw,mtime=0)
            if gzip.decompress(packed)!=raw:raise ValueError('Complete original source payload differs')
            filename='source-'+('image' if name=='image' else 'label')+'.bin.gz';(folder/filename).write_bytes(packed)
            payloads[name]={**header,'file':filename,'compressed_sha256':sha(packed),'compressed_bytes':len(packed),'bytes':len(raw),
                            'provenance':header}
        coords=np.argwhere(mask==1);initial=((coords.min(0)+coords.max(0))//2).tolist();low,high=np.percentile(image,[1,99]);width=max(float(high-low),1);center=float((low+high)/2)
        source_fields=row['source_fields'];fields=['Age (years)','Gender','Pathological T stage','Pathological grade',"Type of patient's tumor number"]
        context='FedBCa source '+key+'. Producer table fields: '+ '; '.join(k+' '+str(source_fields.get(k,'not supplied')) for k in fields)+'. These source records are not a new diagnosis. Cohort eligibility allows untreated or diagnostic-TURBT cases; case-specific timing and full examination/pathology correspondence are not independently established.'
        data={**payloads,'case_context':context,'source_voxels':int(image.size+mask.size),'initial_indices':initial,'initial_window':[center,width],
              'source_grid_corner_difference_mm':row['source_grid_corner_difference_mm'],'selected_source_affines_bit_identical':row['selected_source_affines_bit_identical'],'attribution':credit}
        text=template.replace('__DATASET_JSON__',json.dumps(data,separators=(',',':')).replace('<','\\u003c'))
        (folder/'mri-reference.html').write_text(text);(folder/'mri-reference.js').write_bytes(script)
        positions=np.frombuffer(gzip.decompress((proof/(key+'-positions.f64.gz')).read_bytes()),'<f8').reshape(-1,3)
        faces=np.frombuffer(gzip.decompress((proof/(key+'-triangles.u32.gz')).read_bytes()),'<u4').reshape(-1,3)
        if sha(positions.tobytes())!=row['positions_sha256'] or sha(faces.tobytes())!=row['triangles_sha256']:raise ValueError('Reviewed source-cell geometry changed')
        stored=positions.astype('<f4');conversion=float(np.abs(stored.astype(float)-positions).max());normals=np.zeros_like(positions)
        tri=positions[faces];cross=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0])
        for c in range(3):np.add.at(normals,faces[:,c],cross)
        lengths=np.linalg.norm(normals,axis=1);nonzero=lengths>0;normals[nonzero]/=lengths[nonzero,None];normals=normals.astype('<f4')
        raw=struct.pack('<4sII',b'BP3D',len(stored),faces.size)+stored.tobytes()+normals.tobytes()+faces.tobytes();packed=gzip.compress(raw,mtime=0)
        assert gzip.decompress(packed)==raw and np.array_equal(np.frombuffer(raw,'<f4',count=stored.size,offset=12).reshape(-1,3),stored)
        pid=atlas+'-label1-cells';name=pid+'.bin.gz';(folder/name).write_bytes(packed)
        label='Original source tumour annotation cells '+key
        notes=[context,
            'Complete distributed T2 and producer label1 arrays are retained. The model is the exact boundary of labelled voxel cells, not a verified biological tumour envelope or histological invasion interface. No mask values, source components, positions or contours are fitted, resampled, smoothed or deleted.',
            f"Source label1 has {row['source_label_voxels']} voxels in {row['components_6_connected']} six-connected components. All source components remain. Cell-boundary topology retains {row['nonmanifold_edges']} nonmanifold edges; no repair or component pruning hides the discretization.",
            'MRI and mask use their own original NIfTI spatial forms. Their maximum declared grid-corner difference is '+str(row['source_grid_corner_difference_mm'])+' mm. Source-table index correspondence is not independent clinical registration; no fitted transform replaces either header.',
            'Original DICOM acquisitions/calibration, complete pretreatment eligibility, DWI, DCE, muscle/inner-layer segmentations, microscopic tissue extent and current stage are not independently supplied. Distributed sampling is not fine anatomical resolution.',
            'Display colours, averaged normals and window controls illustrate the source labels. They do not simulate photographic tumour tissue, diffusion, enhancement or treatment response.',credit]
        part={'id':pid,'name':label,'file':'/app/anatomy/'+atlas+'/'+name,'sha256':sha(packed),'decoded_sha256':sha(raw),'vertices':len(stored),'triangles':len(faces),'bounds':[stored.min(0).tolist(),stored.max(0).tolist()],'source_positions_sha256':row['positions_sha256'],'source_triangles_sha256':row['triangles_sha256'],'source_label':1,'source_components':row['components_6_connected'],'layer':'source_label_cells','clinical_fidelity':'unverified'}
        manifest={'dataset':label+' · partial','source_url':'https://zenodo.org/records/13622759','license':'CC BY4.0','license_url':'https://creativecommons.org/licenses/by/4.0/','coordinate_system':{'basis':'original selected NIfTI RAS affine','units':'NIfTI-declared millimetres; original DICOM calibration unverified','unit_meters':.001,'display_basis':'native-ras-to-x-left-y-superior-z-anterior','registration':'Separate source case; mask/image declarations retained without fit'},'parts':{pid:part},'regions':{'bladder-tumour-source':{'title':label+' · partial','side':'separate source '+key,'parts':[{'id':pid,'layer':'source_label_cells'}],'layers':[['source_label_cells','Original label1 voxel-cell boundary']],'source_coordinate_cameras':True,'source_up_range':[float(stored[:,2].min()-1),float(stored[:,2].max()+1)],'focus_bounds':part['bounds'],'uncropped_label':'Complete original label cells · full reporting anatomy incomplete'}},'viewer_notes':notes,'source_context':context,'source_case_id':key,'complete_reporting_anatomy_approved':False,'clinical_approval':False,'runtime_promoted':True,'source_values_changed':False,'total_triangles':len(faces)}
        manifest_path=folder/'manifest.json';manifest_path.write_text(json.dumps(manifest,indent=2)+'\n')
        volume={'id':atlas+'-original-t2-and-labels','modality':'MRI','src':'/app/anatomy/'+atlas+'/mri-reference.html','sha256':sha(text.encode()),'script_sha256':sha(script),'data_files':[{k:payloads[n][k] for k in ['file','compressed_sha256','compressed_bytes','bytes','raw_source_voxel_sha256']} for n in ['image','mask']],'level_by_part':{pid:label},'title':'Inspect complete original source T2 and producer annotation '+key,'caption':'Complete distributed native-index arrays; optional producer label boundary. Source spatial forms, processing, absent acquisitions and independent-registration limits are retained.','attribution':credit,'source_url':'https://zenodo.org/records/13622759','license_url':'https://creativecommons.org/licenses/by/4.0/'}
        entries.append({'id':atlas+'-source-cells','label':'Original MRI annotation '+key+' · partial','atlas':atlas,'family':'bladder-tumour-source','manifest_url':'/app/anatomy/'+atlas+'/manifest.json','manifest_sha256':sha(manifest_path.read_bytes()),'initial_layer':'source_label_cells','initial_cropped':False,'population_note':' '.join(notes),'source_volume':volume})
        packages.append({'case_id':key,'atlas':atlas,'part':part,'image_source_sha256':sha(image_path.read_bytes()),'mask_source_sha256':sha(mask_path.read_bytes()),'complete_voxel_arrays_retained':True,'maximum_source_position_float32_error_mm':conversion,'zero_display_normals':int((~nonzero).sum()),'source_samples':int(image.size+mask.size),'viewer_sha256':sha(text.encode()),'script_sha256':sha(script),'clinical_approval':False})
        print('Complete source case arrays and label-cell model packaged.',flush=True)
    p=project/'data/radiology/source-anatomy-references.json';registry=json.loads(p.read_text());registry['ra.mri-bladder']=[r for r in registry['ra.mri-bladder'] if not r['atlas'].startswith('fedbca-')]+entries;p.write_text(json.dumps(registry,indent=2)+'\n')
    (proof/'reader-package-review.json').write_text(json.dumps(packages,indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True);p.add_argument('--project',type=Path,required=True)
    a=p.parse_args();package(a.root,a.project)
