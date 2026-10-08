#!/usr/bin/env python3
"""Transport all reviewed s0358 source surfaces without repairing source anatomy."""
import gzip,hashlib,json,struct,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import numpy as np
from tools.anatomy_sources.package_aortic_rupture_figures import append_evidence
from tools.anatomy_sources.package_laryngeal_phonation_reference import canonical_gzip
ROOT=Path(__file__).resolve().parents[2]
PROOF=ROOT/'docs/esophagus-native-context-review/s0358'
ATLAS='totalseg-v3-esophagus-s0358';FAMILY='esophagus-source';INV='ra.esophagus'
SOURCE=Path('/Users/peter/Documents/ChatGPT/Primer/.research/esophagus-native-v3')
URL='https://zenodo.org/records/22688904';GRANT='https://creativecommons.org/licenses/by/4.0/'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def package(source):
    native=json.loads((PROOF/'native-source-review.json').read_text());qc=json.loads((PROOF/'surface-quality-review.json').read_text());visual=json.loads((PROOF/'surface-visual-review.json').read_text());acquisition=json.loads((PROOF/'original-acquisition.json').read_text())
    metadata_path=source/'zenodo-22688904.json';metadata=json.loads(metadata_path.read_text())
    if sha(metadata_path.read_bytes())!=acquisition['metadata_sha256'] or metadata['metadata']['license']['id']!='cc-by-4.0':raise ValueError('Original dataset rights changed')
    if not visual['all_27_complete_surfaces_visually_inspected'] or qc['native_source_review_sha256']!=sha((PROOF/'native-source-review.json').read_bytes()):raise ValueError('Source surface review changed')
    metadata_proof=PROOF/'zenodo-22688904.json';metadata_proof.write_bytes(metadata_path.read_bytes())
    attribution=', '.join(c['name'] for c in metadata['metadata']['creators'])+'. TotalSegmentator dataset v3.0.0, case s0358. DOI 10.5281/zenodo.22688904. CC BY 4.0. Adaptation: original 0.5 label-interface extraction, float32 transport and display normals.'
    notes=[
      'Original CT case s0358: source metadata age 90,female,study type ct pelvis,trauma/abdomen. These are source-labelled inspection candidates, not a normal esophageal atlas or current patient.',
      'All 27 complete original selected source label interfaces and 686,252 triangles are retained. Original source-grid CT and masks can be inspected separately in every plane. No smoothing,padding,capping,decimation,component deletion,relabeling or fitted transformation is applied. Display colours and normals are illustrative.',
      'One declared 255×255×523 grid with 1.5 mm pitch and original RAS sform. Raw DICOM/HU calibration, native patient orientation,contrast phase and fine-tissue accuracy remain unverified. Left/right are original source label names; patient laterality is not independently verified.',
      'The esophageal label is an organ envelope, without separate lumen,wall layers,mucosa,glands,plexuses or hiatal attachments. Whole heart does not separately identify left atrium; atrial appendage is not the entire atrium. Published clinical figures are different cases with no registration to this CT.',
      'Left upper lung mask contains 261 six-connected components and 137 surface interfaces. Heart has 2 foreground components and 47 surface interfaces,including 45 opposite-winding to the largest; surface count alone does not identify organ fragments. Pulmonary veins retain 4 disconnected components. These source assignments require further anatomical review.',
      'Spinal cord retains 40 open source boundary edges at the scan extent. T6,T8,T11 and lower lung additional components remain. Closed source label endpoints do not establish physical organ ends. Source stair steps and Lewiner ambiguity-field residuals are not independently measured anatomical accuracy.',
      'Inspection reference only: no every-structure reporting coverage,clinical approval,current lesion diagnosis,physiological timing,pressure or flow evidence is granted. Original members pass CRC/SHA with stable publisher archive identity before/after; full 37.4 GB archive MD5 and object immutability remain unverified. '+attribution]
    out=ROOT/'web/anatomy'/ATLAS;out.mkdir(parents=True,exist_ok=True);parts={};checks=[]
    colours=['#e6a370','#8caec5','#b491ad','#ce8585','#d89494','#bf7070','#839dcc','#a0b2d2']
    quality={r['file']:r for r in qc['surface_checks']}
    for index,row in enumerate(native['targets']):
        colour=colours[index%len(colours)]
        stem=row['file'].removesuffix('.nii.gz');praw=gzip.decompress((PROOF/(stem+'-positions.f64.gz')).read_bytes());fraw=gzip.decompress((PROOF/(stem+'-triangles.u32.gz')).read_bytes())
        if sha(praw)!=row['positions_sha256'] or sha(fraw)!=row['triangles_sha256']:raise ValueError('Reviewed original source geometry changed')
        vertices=np.frombuffer(praw,'<f8').reshape(-1,3);faces=np.frombuffer(fraw,'<u4').reshape(-1,3);stored=vertices.astype('<f4');error=float(np.abs(stored.astype(float)-vertices).max())
        if error>4e-5:raise ValueError('Unexpected transport error')
        normals=np.zeros_like(vertices);triangles=vertices[faces];cross=np.cross(triangles[:,1]-triangles[:,0],triangles[:,2]-triangles[:,0])
        for corner in range(3):np.add.at(normals,faces[:,corner],cross)
        lengths=np.linalg.norm(normals,axis=1);normals[lengths>0]/=lengths[lengths>0,None]
        decoded=struct.pack('<4sII',b'BP3D',len(vertices),faces.size)+stored.tobytes()+normals.astype('<f4').tobytes()+fraw;encoded=canonical_gzip(decoded);identifier=ATLAS+'-'+stem;filename=identifier+'.bin.gz';(out/filename).write_bytes(encoded)
        readback=gzip.decompress((out/filename).read_bytes());assert readback[12+len(vertices)*24:]==fraw
        assert np.array_equal(np.frombuffer(readback,'<f4',len(vertices)*3,12).reshape(-1,3),stored)
        q=quality[row['file']];parts[identifier]={'id':identifier,'name':stem.replace('_',' ')+' · source label interface','file':'/app/anatomy/'+ATLAS+'/'+filename,'sha256':sha(encoded),'decoded_sha256':sha(decoded),'vertices':len(vertices),'triangles':len(faces),'bounds':[stored.min(0).tolist(),stored.max(0).tolist()],'source_positions_sha256':sha(praw),'source_triangles_sha256':sha(fraw),'source_components':q['surface_connected_components'],'source_boundary_edges':q['boundary_edges'],'clinical_fidelity':'unverified','color':colour,'layer':'source_labels','regions':[FAMILY]}
        checks.append({'id':identifier,'faces_unchanged':True,'maximum_float32_position_transport_error_source_units':error,'zero_display_normals':int((lengths==0).sum()),'source_components':q['surface_connected_components'],'source_boundary_edges':q['boundary_edges'],'sha256':sha(encoded)})
    low=np.min([p['bounds'][0] for p in parts.values()],axis=0);high=np.max([p['bounds'][1] for p in parts.values()],axis=0)
    manifest={'dataset':'TotalSegmentator v3 s0358 · esophageal CT context candidates','source_url':URL,'license':'CC BY 4.0','license_url':GRANT,'coordinate_system':{'basis':'RAS','units':'original source-declared millimetres','unit_meters':.001,'display_basis':'native-ras-to-x-left-y-superior-z-anterior','registration':'Original source sform only; raw DICOM/patient orientation unverified'},'parts':parts,'regions':{FAMILY:{'title':'Esophageal CT source context · inspection candidates','side':'source case s0358','parts':[{'id':i,'layer':'source_labels'} for i in parts],'layers':[['source_labels','Original label interfaces']],'source_up_range':[float(low[2]-1),float(high[2]+1)],'focus_bounds':[low.tolist(),high.tolist()],'source_coordinate_cameras':True,'uncropped_label':'Original selected source extent · spinal-cord boundary open'}},'viewer_notes':notes,'clinical_approval':False,'anatomical_approval':False,'complete_esophageal_geometry_verified':False,'runtime_promoted':True,'status':'Source inspection candidates; anatomical assignment/validation pending','total_triangles':sum(p['triangles'] for p in parts.values())}
    assert manifest['total_triangles']==686252
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');(out/'ATTRIBUTION.md').write_text('# Partial source reference\n\n'+'\n\n'.join(notes)+'\n')
    references_path=ROOT/'data/radiology/source-anatomy-references.json';references=json.loads(references_path.read_text());references[INV]=[r for r in references.get(INV,[]) if r['atlas']!=ATLAS]+[{'id':ATLAS+'-original-labels','label':'Esophageal CT context · original source candidates','atlas':ATLAS,'family':FAMILY,'manifest_url':'/app/anatomy/'+ATLAS+'/manifest.json','manifest_sha256':sha((out/'manifest.json').read_bytes()),'initial_layer':'source_labels','initial_cropped':False,'population_note':' '.join(notes)}];references_path.write_text(json.dumps(references,indent=2,ensure_ascii=False)+'\n')
    rights={'name':'CC BY 4.0','url':GRANT,'commercial_use':True,'redistribution':True,'review_status':'verified','evidence_path':str(metadata_proof.relative_to(ROOT)),'evidence_sha256':sha(metadata_proof.read_bytes()),'attribution':attribution,'reviewed_at':'2026-10-08'}
    assets=[{'id':p['id'],'kind':'model','name':p['name'],'local_path':'web/'+p['file'].removeprefix('/app/'),'sha256':p['sha256'],'investigation_ids':[INV],'structure_ids':[],'requirement_coverage':{},'source':{'url':URL,'license':rights},'anatomical_review':{'status':'pending','reason':'Coarse source label interfaces do not independently resolve every esophageal reporting structure.'}} for p in parts.values()];append_evidence(ROOT/'data/radiology/radiology-asset-evidence.json',assets,prefix=ATLAS+'-')
    (PROOF/'reader-transport-review.json').write_text(json.dumps({'source_native_review_sha256':sha((PROOF/'native-source-review.json').read_bytes()),'source_quality_review_sha256':sha((PROOF/'surface-quality-review.json').read_bytes()),'manifest_sha256':sha((out/'manifest.json').read_bytes()),'checks':checks,'all_original_faces_retained':True,'total_triangles':686252,'source_geometry_repaired':False,'independent_anatomical_approval':False},indent=2)+'\n');print('27 source interfaces, 686,252 unchanged triangles packaged')
if __name__=='__main__':package(SOURCE)
