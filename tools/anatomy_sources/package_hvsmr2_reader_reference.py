#!/usr/bin/env python3
"""Expose native source blood-pool geometry as a limited reference, without clinical approval."""
import gzip,hashlib,json,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];SOURCE=ROOT/'docs/hvsmr2-pat7-native-source-review';OUT=ROOT/'web/anatomy/hvsmr2-pat7';FAMILY='cardiac-venous-source'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def package():
    import numpy as np
    from PIL import Image
    from tools.anatomy_sources.package_aortic_rupture_figures import append_evidence
    report=json.loads((SOURCE/'native-source-review.json').read_text());OUT.mkdir(parents=True,exist_ok=True);parts={};checks=[]
    colors=['#eb78ae','#467ee4','#61c6c6','#54b970','#e69b36','#ba72d9','#243cd1','#afb94a']
    names=['LV blood pool','RV blood pool (original small component retained)','LA blood pool with limited source pulmonary-vein extents','RA blood pool','Aortic blood pool (source label extent)','Pulmonary arterial blood pool (source label extent)','Both source SVC blood-pool channels','IVC blood pool (source label extent)']
    for c in report['classes']:
        label=c['label'];praw=gzip.decompress((SOURCE/f'label{label}-positions.f64.gz').read_bytes());fraw=gzip.decompress((SOURCE/f'label{label}-triangles.u32.gz').read_bytes())
        if sha(praw)!=c['positions_sha256'] or sha(fraw)!=c['triangles_sha256']:raise ValueError('Reviewed native geometry changed')
        pos=np.frombuffer(praw,'<f8').reshape(-1,3);faces=np.frombuffer(fraw,'<u4').reshape(-1,3);stored=pos.astype('<f4');error=float(np.abs(stored.astype(float)-pos).max())
        if error>1e-5:raise ValueError('Unexpected source transport precision loss')
        normals=np.zeros_like(pos);tri=pos[faces];cross=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0])
        for corner in range(3):np.add.at(normals,faces[:,corner],cross)
        length=np.linalg.norm(normals,axis=1);zero=length==0;normals[~zero]/=length[~zero,None];normals=normals.astype('<f4')
        # Zero display normals remain zero; geometry is never changed to repair lighting.
        decoded=struct.pack('<4sII',b'BP3D',len(pos),faces.size)+stored.tobytes()+normals.tobytes()+fraw;encoded=gzip.compress(decoded,mtime=0);id='hvsmr2-pat7-label'+str(label);filename=id+'.bin.gz';(OUT/filename).write_bytes(encoded)
        restored=gzip.decompress(encoded);n=len(pos)
        if not np.array_equal(np.frombuffer(restored,'<f4',n*3,12).reshape(-1,3),stored) or restored[12+n*24:]!=fraw:raise ValueError('Native transport changed topology')
        parts[id]={'id':id,'name':names[label-1],'file':'/app/anatomy/hvsmr2-pat7/'+filename,'sha256':sha(encoded),'decoded_sha256':sha(decoded),
            'vertices':n,'triangles':len(faces),'bounds':[stored.min(0).tolist(),stored.max(0).tolist()],'source_label':label,
            'source_positions_sha256':c['positions_sha256'],'source_triangles_sha256':c['triangles_sha256'],'clinical_fidelity':'unverified',
            'color':colors[label-1],'layer':'blood_pool','regions':[FAMILY]}
        checks.append({'id':id,'faces_unchanged':True,'maximum_position_conversion_error_source_mm':error,'zero_display_normals':int(zero.sum()),'sha256':sha(encoded)})
    low=np.min([p['bounds'][0] for p in parts.values()],axis=0);high=np.max([p['bounds'][1] for p in parts.values()],axis=0)
    notes=['Partial blood-pool reference from one adult MRI case (pat7, age 27), source-described bilateral SVC. It is not a normal whole-heart atlas or the anatomy of the patient being reported.',
        'Eight source classes only. LA includes limited source pulmonary-vein extents; SVC combines both source channels. Vessel endpoints and class junctions follow segmentation conventions, including benchmark optional zones, not complete clinical anatomy.',
        'Thin valves, myocardium/vessel walls, complete venous branches and drainage interfaces, coronary sinus, ductal/ligamentous ring and airway anatomy are not independently represented. The original small RV component is retained.',
        'Static MRI, not cine or measured flow. No shunt ratio, flow direction, pressure gradient, device suitability or clinical severity is inferred. NIfTI-declared units are not independently linked DICOM calibration.',
        'Original MRI/mask grid checked voxel-by-voxel with an independent reader. Source annotations were already manually edited/mildly smoothed by their creators; no additional fitting, smoothing, decimation, class merge or component removal was applied.',
        'Original source RAS coordinates are preserved with float32 transport and generated display normals. This case is independent of the generic aorta guide and all published figure patients; no registration between them is inferred.',
        report['attribution']+' Clinical/anatomical validation remains pending.']
    manifest={'dataset':'HVSMR-2.0 pat7 · partial bilateral-SVC blood-pool reference','source_url':report['source'],'license':report['license'],'license_url':report['license_url'],
        'coordinate_system':{'basis':'RAS','units':'NIfTI-declared millimetres','unit_meters':.001,'display_basis':'native-ras-to-x-left-y-superior-z-anterior','registration':'Original pat7 sform; no independent patient/figure/atlas registration'},
        'parts':parts,'regions':{FAMILY:{'title':'Adult bilateral-SVC source blood pools · partial','side':'bilateral','parts':[{'id':id,'layer':'blood_pool'} for id in parts],
            'layers':[['blood_pool','Source blood pools']],'source_up_range':[float(low[2]-1),float(high[2]+1)],'focus_bounds':[low.tolist(),high.tolist()]}},
        'viewer_notes':notes,'clinical_approval':False,'anatomical_approval':False,'complete_venous_geometry_verified':False,'runtime_promoted':True,
        'status':'Partial source reference; clinical anatomical validation pending','source_manifest_sha256':sha((SOURCE/'native-source-review.json').read_bytes()),'total_triangles':sum(p['triangles'] for p in parts.values())}
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');manifest_sha=sha((OUT/'manifest.json').read_bytes())
    (OUT/'ATTRIBUTION.md').write_text('# Native source reference\n\n'+report['attribution']+'\n\nDisplay adaptation: float32 transport, generated normals, gzip and source-coordinate framing. Source models/masks are unchanged. Partial anatomy only; clinical approval pending.\n')
    image_path=ROOT/'web/reference-media/hvsmr2-pat7/native-mri-label-context.png';image_path.parent.mkdir(parents=True,exist_ok=True);image_path.write_bytes((SOURCE/'pat7-native-mri-label-context.png').read_bytes())
    with Image.open(image_path) as im:width,height=im.size
    image={'src':'/app/reference-media/hvsmr2-pat7/native-mri-label-context.png','sha256':sha(image_path.read_bytes()),'width':width,'height':height,
        'title':'Matching native MRI planes and original label contours','alt':'Three native pat7 MRI index planes with original blood-pool label contours and optional zones.',
        'caption':'Matching planes from the source MRI; coloured contours are original labels, white dashed contours optional zones. Recorded window display is not an edited source volume. These three planes do not establish whole-examination, thin-wall, valve or venous-branch completeness.',
        'attribution':report['attribution']+' Adaptation: source-plane window display and original-label contour overlays.','source_url':report['source'],'license_url':report['license_url']}
    entry={'id':'hvsmr2-pat7-blood-pools','label':'Bilateral-SVC MRI source blood pools · partial','atlas':'hvsmr2-pat7','family':FAMILY,
        'manifest_url':'/app/anatomy/hvsmr2-pat7/manifest.json','manifest_sha256':manifest_sha,'initial_layer':'blood_pool','initial_cropped':False,
        'population_note':notes[0]+' '+notes[1]+' '+notes[2],'source_image':image}
    path=ROOT/'data/radiology/source-anatomy-references.json';data=json.loads(path.read_text());data['ra.vascular-anomalies']=[e for e in data.get('ra.vascular-anomalies',[]) if e['id']!=entry['id']]+[entry];path.write_text(json.dumps(data,indent=2)+'\n')
    proof=SOURCE/'reader-package-review.json';proof.write_text(json.dumps({'parts':checks,'manifest_sha256':manifest_sha,'source_labels_changed':False,'clinical_approval':False,'structure_coverage_granted':False},indent=2)+'\n')
    assets=[]
    for part in parts.values():
        assets.append({'id':part['id'],'kind':'model','name':part['name'],'local_path':'web/'+part['file'].removeprefix('/app/'),'sha256':part['sha256'],
            'investigation_ids':['ra.vascular-anomalies'],'structure_ids':[],'requirement_coverage':{},'source':{'url':report['source'],'license':{'name':report['license'],'url':report['license_url'],'commercial_use':True,'redistribution':True,'review_status':'verified','evidence_path':'docs/hvsmr2-pat7-native-source-review/figshare-25226360-v2.json','evidence_sha256':report['dataset_metadata_sha256'],'attribution':report['attribution'],'reviewed_at':'2026-10-06'}},
            'anatomical_review':{'status':'pending','reason':'Partial source blood-pool classes and segmentation interfaces do not establish complete reportable anatomy.'}})
    assets.append({'id':'hvsmr2-pat7-mri-source-review','kind':'clinical_image','name':image['title'],
        'local_path':str(image_path.relative_to(ROOT)),'sha256':image['sha256'],'modality':'MRI','investigation_ids':['ra.vascular-anomalies'],
        'structure_ids':[],'requirement_coverage':{},'source':{'url':report['source'],'license':{**assets[0]['source']['license'],'attribution':image['attribution']}},
        'pixel_provenance':{'source_voxels_changed':False,'adaptation':'Recorded percentile window, native index-plane display and unchanged original label/optional-zone contours.'},
        'anatomical_review':{'status':'pending','reason':'Three native source planes do not independently validate complete wall/valve/venous topology or function.'}})
    append_evidence(ROOT/'data/radiology/radiology-asset-evidence.json',assets,prefix='hvsmr2-pat7-')
    print('Eight source meshes packaged for a partial reader reference; no clinical or leaf-coverage approval.')
if __name__=='__main__':package()
