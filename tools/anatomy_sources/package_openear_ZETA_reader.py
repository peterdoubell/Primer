#!/usr/bin/env python3
"""Expose intact original source geometry and microscopy as a limited, untextured reference."""
import argparse,gzip,hashlib,json,struct,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import numpy as np
from PIL import Image
from tools.anatomy_sources.review_openear_ZETA_geometry import ply
from tools.anatomy_sources.package_aortic_rupture_figures import append_evidence
ROOT=Path(__file__).resolve().parents[2];PROOF=ROOT/'docs/openear-native-source-review';OUT=ROOT/'web/anatomy/openear-zeta';FAMILY='temporal-source';URL='https://zenodo.org/records/1473724';GRANT='https://creativecommons.org/licenses/by/4.0/'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def package(root):
    metadata_path=root/'zenodo-1473724.json';metadata=json.loads(metadata_path.read_text());acquisition=json.loads((PROOF/'ZETA-original-acquisition.json').read_text());models=json.loads((PROOF/'ZETA-original-geometry-header-review.json').read_text())['meshes']
    if sha(metadata_path.read_bytes())!=acquisition['metadata_sha256'] or metadata['metadata']['license']['id']!='cc-by-4.0':raise ValueError('Original source identity/grant changed')
    attribution=', '.join(c['name'] for c in metadata['metadata']['creators'])+'. OpenEar library, ZETA specimen, DOI 10.5281/zenodo.1473724. CC BY 4.0.'
    OUT.mkdir(parents=True,exist_ok=True);parts={};checks=[]
    for i,m in enumerate(models):
        raw=(root/'ZETA-selected'/Path(m['member']).name).read_bytes()
        if sha(raw)!=m['original_member_sha256']:raise ValueError('Original acquired surface changed')
        positions,faces,_=ply(raw);normal=np.zeros(positions.shape,dtype=np.float64)
        for first in range(0,len(faces),100000):
            f=faces[first:first+100000];tri=positions[f].astype(float);cross=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0])
            for corner in range(3):np.add.at(normal,f[:,corner],cross)
        lengths=np.linalg.norm(normal,axis=1);zero=lengths==0;normal[~zero]/=lengths[~zero,None]
        source_positions=positions.astype('<f4').tobytes();source_faces=faces.astype('<u4').tobytes();decoded=struct.pack('<4sII',b'BP3D',len(positions),faces.size)+source_positions+normal.astype('<f4').tobytes()+source_faces
        encoded=gzip.compress(decoded,mtime=0);identifier='openear-zeta-part'+str(i);name=Path(m['member']).stem.split('_',1)[-1];filename=identifier+'.bin.gz';(OUT/filename).write_bytes(encoded);restored=gzip.decompress(encoded)
        if restored[12:12+len(positions)*12]!=source_positions or restored[12+len(positions)*24:]!=source_faces:raise ValueError('Reader transport changed original geometry')
        layer='bone' if name=='Bone' else 'source_structures';parts[identifier]={'id':identifier,'name':name+' · original source surface','file':'/app/anatomy/openear-zeta/'+filename,
            'sha256':sha(encoded),'decoded_sha256':sha(decoded),'vertices':len(positions),'triangles':len(faces),'bounds':m['source_bounds'],'source_member':m['member'],'source_member_sha256':m['original_member_sha256'],
            'source_positions_sha256':sha(source_positions),'source_triangles_sha256':sha(source_faces),'clinical_fidelity':'unverified','color':'#a7b7ba','layer':layer,'regions':[FAMILY]}
        checks.append({'id':identifier,'original_positions_and_faces_preserved_exactly':True,'source_zero_area_triangles_retained':m['zero_area_triangles'],'zero_display_normals':int(zero.sum()),'sha256':sha(encoded)})
        print(name,len(faces),'original triangles preserved',flush=True)
    low=np.min([p['bounds'][0] for p in parts.values()],axis=0);high=np.max([p['bounds'][1] for p in parts.values()],axis=0)
    notes=['One prepared adult cadaveric temporal-bone specimen, ZETA. Thirteen source surfaces only; this is not a full normal atlas or the anatomy of the patient being reported.',
        'Original 7,349,910 triangles retained, including two zero-area Bone faces. Source surface optimization/segmentation conventions do not independently delineate every tiny wall, joint, neural branch, implant or pathological interface.',
        'Source coordinate convention is RAS, reconciled with recorded volume declarations and crop offset. Patient anatomical directions and laterality are not independently verified; camera controls use specimen-coordinate labels.',
        'Microscopy shows fixed, stained, dehydrated, epoxy-embedded tissue. A preparation opening was drilled in the superior semicircular canal. The original photograph is not untreated living-ear colour or functional evidence.',
        'Registered CBCT sampling 0.125 mm is distinct from original unembedded 0.25 mm acquisition. Microscopy reconstruction includes alignment/interpolation; source registration measurements concern overmould and do not validate all internal anatomy.',
        'Reconstructed colour samples remain withheld: source bounds contain non-tissue/padding-like regions and many Bone/vascular/nerve portions lack colour support. Grey is a neutral display label, not a photographic tissue texture.',
        'Scalar/mask/colour comparisons, original TIFFs and transform evidence do not certify full reportable anatomy, physiology, hearing, nerve function, device performance or current-patient findings. '+attribution]
    manifest={'dataset':'OpenEar ZETA · original prepared-specimen surfaces','source_url':URL,'license':'CC BY 4.0','license_url':GRANT,
        'coordinate_system':{'basis':'RAS','units':'source-declared millimetres','unit_meters':.001,'display_basis':'native-ras-to-x-left-y-superior-z-anterior','registration':'Original source coordinates; recorded grid reconciliation only, no independently verified patient anatomical registration'},
        'parts':parts,'regions':{FAMILY:{'title':'Prepared temporal-bone source surfaces · partial','side':'specimen','parts':[{'id':k,'layer':v['layer']} for k,v in parts.items()],
        'layers':[['source_structures','Original anatomical surfaces'],['bone','Full original Bone surface']],'lazy_layers':True,'source_coordinate_cameras':True,'uncropped_label':'Acquired specimen extent · partial anatomy','source_up_range':[float(low[2]-1),float(high[2]+1)],'focus_bounds':[low.tolist(),high.tolist()]}},
        'viewer_notes':notes,'total_triangles':sum(p['triangles'] for p in parts.values()),'clinical_approval':False,'anatomical_approval':False,'complete_temporal_bone_anatomy_verified':False,'photographic_texture_promoted':False,'runtime_promoted':True}
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');manifest_sha=sha((OUT/'manifest.json').read_bytes());(OUT/'ATTRIBUTION.md').write_text('# Source reference\n\n'+'\n\n'.join(notes)+'\n')
    (PROOF/'zenodo-1473724.json').write_bytes(metadata_path.read_bytes());photo=json.loads((PROOF/'ZETA-original-photo-reconstruction-review.json').read_text())['selected_raw_and_reconstructed_planes'];source_photo=root/'ZETA-photo-reference'/photo['lossless_original_frame_file']
    if sha(source_photo.read_bytes())!=photo['lossless_original_frame_sha256']:raise ValueError('Original decoded photograph changed')
    image_path=ROOT/'web/reference-media/openear-zeta/original-microscopy-135.png';image_path.parent.mkdir(parents=True,exist_ok=True);image_path.write_bytes(source_photo.read_bytes())
    with Image.open(image_path) as im:width,height=im.size
    image={'src':'/app/reference-media/openear-zeta/'+image_path.name,'sha256':sha(image_path.read_bytes()),'width':width,'height':height,'title':'Original microscopy photograph 135 · prepared cadaver specimen',
        'alt':'Full original decoded microscopy frame of the ZETA epoxy-embedded specimen; no anatomical relabelling.',
        'caption':'Original TIFF frame 0 preserved losslessly, source position 31.96 mm. Fixation/staining/epoxy and preparation effects remain. This selected physical slice does not validate every surface or whole native anatomy; no reconstructed texture is applied to the models.',
        'attribution':attribution+' Adaptation: original TIFF frame0 decoded to lossless PNG, original pixels retained.','source_url':URL,'license_url':GRANT}
    entry={'id':'openear-zeta-original-surfaces','label':'Prepared temporal-bone specimen surfaces · partial','atlas':'openear-zeta','family':FAMILY,'manifest_url':'/app/anatomy/openear-zeta/manifest.json','manifest_sha256':manifest_sha,
        'initial_layer':'source_structures','initial_cropped':False,'population_note':' '.join(notes[:4]),'source_image':image}
    path=ROOT/'data/radiology/source-anatomy-references.json';data=json.loads(path.read_text());data['ra.ct-temporal-bone']=[e for e in data.get('ra.ct-temporal-bone',[]) if e['id']!=entry['id']]+[entry];path.write_text(json.dumps(data,indent=2)+'\n')
    (PROOF/'reader-geometry-package-review.json').write_text(json.dumps({'parts':checks,'manifest_sha256':manifest_sha,'source_geometry_changed':False,'clinical_approval':False,'photographic_texture_promoted':False,'structure_coverage_granted':False},indent=2)+'\n')
    rights={'name':'CC BY 4.0','url':GRANT,'commercial_use':True,'redistribution':True,'review_status':'verified','evidence_path':'docs/openear-native-source-review/zenodo-1473724.json','evidence_sha256':sha(metadata_path.read_bytes()),'attribution':attribution,'reviewed_at':'2026-10-07'}
    assets=[{'id':p['id'],'kind':'model','name':p['name'],'local_path':'web/'+p['file'].removeprefix('/app/'),'sha256':p['sha256'],'investigation_ids':['ra.ct-temporal-bone'],'structure_ids':[], 'requirement_coverage':{},'source':{'url':URL,'license':rights},'anatomical_review':{'status':'pending','reason':'Original thirteen source surfaces do not establish every reportable interface, branch, tiny tissue or complete clinical fidelity.'}} for p in parts.values()]
    # Source specimen photography has a rights-only record, never CT/MRI leaf evidence.
    ledger_path=ROOT/'data/radiology/radiology-asset-evidence.json';ledger=json.loads(ledger_path.read_text());ledger['reference_rights_assets']=[a for a in ledger.get('reference_rights_assets',[]) if a['id']!='openear-zeta-original-microscopy135']+[{'id':'openear-zeta-original-microscopy135','kind':'anatomical_specimen_photo','reference_only':True,'name':image['title'],'local_path':str(image_path.relative_to(ROOT)),'sha256':image['sha256'],'structure_ids':[],'requirement_coverage':{},'source':{'url':URL,'license':rights}}];ledger_path.write_text(json.dumps(ledger,indent=2)+'\n')
    append_evidence(ROOT/'data/radiology/radiology-asset-evidence.json',assets,prefix='openear-zeta-')
    print('13 complete source surfaces packaged; no tissue texture or clinical/leaf approval')
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);a=p.parse_args();package(a.source_root)
