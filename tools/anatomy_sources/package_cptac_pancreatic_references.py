#!/usr/bin/env python3
"""Package reviewed native CT figures with separate acquisition provenance for the reader."""
import hashlib
import json
import re
from pathlib import Path
import shutil

ROOT=Path(__file__).resolve().parents[2]

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def package():
    source=ROOT/'docs/cptac-pancreatic-native-sections'
    provenance_path=source/'C3L-02112-native-sections.provenance.json'
    native=json.loads(provenance_path.read_text())
    geometry=json.loads((ROOT/'docs/cptac-pancreatic-source-review/C3L-02112-original-geometry-review.json').read_text())
    selection_path=ROOT/'docs/cptac-pancreatic-source-review/C3L-02112-selection.json'
    if sha(selection_path)!=native['source_selection_sha256'] or sha(ROOT/'docs/cptac-pancreatic-source-review/C3L-02112-original-geometry-review.json')!=native['geometry_review_sha256']:
        raise ValueError('Original source selection or geometry review changed')
    target=ROOT/'web/reference-media/radiology-open'
    images_path=ROOT/'data/radiology/radiology-open-images.json'
    assets_path=ROOT/'data/radiology/radiology-asset-evidence.json'
    images=json.loads(images_path.read_text());assets=json.loads(assets_path.read_text())
    ids={'native-cptac-c3l02112-'+r['source_role']+'-ct' for r in native['records']}
    module='ra.ct-pancreatic-cancer'
    images[module]=[r for r in images.get(module,[]) if r['id'] not in ids]
    assets['assets']=[r for r in assets['assets'] if r['id'] not in ids]
    for row in native['records']:
        role=row['source_role'];record=next(r for r in geometry['records'] if r['source_role']==role)
        if sha(source/row['figure'])!=row['figure_sha256'] or row['ct_archive_sha256']!=record['ct_archive_sha256']:
            raise ValueError('Native source review changed')
        for kind, expected in [('ct', row['ct_archive_sha256']), ('annotation', row['annotation_archive_sha256'])]:
            audit=json.loads((ROOT/'docs/cptac-pancreatic-source-review'/('C3L-02112-'+role+'-'+kind+'-archive-audit.json')).read_text())
            if audit['archive_sha256']!=expected or audit['publisher_per_file_md5_verified'] is not True or audit['zip_member_crc_verified'] is not True:
                raise ValueError('Source archive integrity receipt differs')
        filename='cptac-c3l02112-'+role+'-native-ct.png'
        proofname='cptac-c3l02112-'+role+'-sections.provenance.json'
        shutil.copyfile(source/row['figure'],target/filename)
        proof={'source':{'dataset_doi':native['image_doi'],'annotation_doi':native['annotation_doi'],'data_license':native['image_license'],
                         'case_id':native['case_id'],'source_role':role,'ct_dicom_files':record['ct_objects'],
                         'selected_acquisition_number':int(row['source_acquisition_number']),'source_acquisition_time':row['source_acquisition_time'],
                         'ct_archive_sha256':row['ct_archive_sha256'],'annotation_archive_sha256':row['annotation_archive_sha256'],
                         'publisher_per_file_md5_verified':True,'source_selection_sha256':native['source_selection_sha256'],
                         'original_geometry_review_sha256':native['geometry_review_sha256'],'native_section_review_sha256':sha(provenance_path)},
               'figure_sha256':row['figure_sha256'],'source_shape':row['source_shape_zyx'],'source_sampling_zyx_mm':row['source_sampling_zyx_mm'],
               'source_slice_thickness_mm':.625,'declared_spacing_between_slices_mm':-.625,'observed_interplane_step_mm':.625,
               'original_instance_order_signed_steps_mm':[-.625,-.625],
               'planes':[dict(axis=p['axis_zyx'],index=p['index'],source_resampling=p['resampling'],
                              selected_hu_shape=p['selected_hu_shape'],selected_hu_float64_le_sha256=p['selected_hu_float64_le_sha256'],
                              display_extent_ras_mm=p['display_extent_ras_mm'],display_origin=p['display_origin']) for p in row['planes']],
               'axial_source_sop_instance_uid':row['axial_source_sop_instance_uid'],'crop_start_zyx':row['crop_start_zyx'],
               'crop_stop_exclusive_zyx':row['crop_stop_exclusive_zyx'],'display_hu_windows':row['display_hu_windows'],
               'source_rescale_applied_per_object':True,'annotation_is_location_aid_only':True,'source_voxels_changed':False,
               'source_acquisitions_interleaved_or_deduplicated':False,'cross_acquisition_registration':False,
               'annotation_geometry_overlaid':False,'model_geometry_overlaid':False,'named_phase_verified':False,
               'histological_diagnosis_verified':False,'complete_pancreatic_anatomy_verified':False,'source_annotation_is_whole_pancreas':False,
               'tracking_identity_reconciled':False,'source_volume_and_end_extent_reconciled':False,'clinical_approval':False,
               'runtime_reference_only':True,'selection_basis':native['selection_basis']}
        (target/proofname).write_text(json.dumps(proof,indent=2)+'\n')
        caption=('Selected unmarked axial, coronal and sagittal native CT sections from CPTAC case C3L-02112, '+role+' acquisition, in two display windows. '
                 'Source sampling 0.703125 × 0.703125 × 0.625 mm. Each acquisition uses its own source annotation only to select the review region; the views are not registered or matched between acquisitions. '
                 'The original spacing tag and instance order descend by −0.625 mm; analysis indices increase by actual physical position. '
                 'Series labels do not verify contrast-phase adequacy. Histology and anatomical boundaries remain unapproved.')
        limits=('The annotation is a selected target, not whole pancreas. CSV/RTSTRUCT tracking UIDs differ. The venous-labelled annotation leaves two acquired CT planes unannotated; their ROI state is unresolved. '
                'Original ROI-volume construction and positive contour endpoints remain unresolved. These selected unmarked sections do not establish ducts, vessel contact/invasion, neural spread, complete staging or resectability; no annotation or 3D model is overlaid.')
        attribution=('National Cancer Institute CPTAC. Original CPTAC-PDA imaging v15, DOI 10.7937/K9/TCIA.2018.SC20FO18, CC BY 4.0. '
                     'Annotation location context: Rozenfeld and Jordan, CPTAC-PDA-Tumor-Annotations v2, DOI 10.7937/BW9V-BX61, CC BY 4.0. '
                     'Adaptation: selected native CT sections with physical axes, crops and display windows. No source contour/model overlay or source voxel resampling.')
        image={'id':'native-cptac-c3l02112-'+role+'-ct','kind':'clinical-image','origin':'native-volume-sections',
               'figure_title':'CPTAC C3L-02112 · '+role+' original CT sections','src':'/app/reference-media/radiology-open/'+filename,
               'sha256':sha(target/filename),'width':1800,'height':1200,'source_url':'https://doi.org/'+native['image_doi'],
               'figure_url':'https://doi.org/'+native['image_doi'],'modality':'CT','image_state':'source_case_pancreatic_annotation_context',
               'structures_visible':['Selected original pancreatic target context; individual structure boundaries and diagnosis not approved'],
               'caption':caption,'alt':caption,'limits':limits,'license':'CC BY 4.0','license_url':'https://creativecommons.org/licenses/by/4.0/',
               'attribution':attribution,'rights_review':'Original image and annotation source grants checked separately with selected-series metadata and per-file MD5/CRC; rights do not approve anatomy.',
               'rights_reviewed_on':'2026-10-03','derivation':{'evidence_url':'/app/reference-media/radiology-open/'+proofname,'evidence_sha256':sha(target/proofname)}}
        images[module].append(image)
        assets['assets'].append({'id':image['id'],'kind':'clinical_image','name':image['figure_title'],'local_path':'web/reference-media/radiology-open/'+filename,
              'sha256':image['sha256'],'regions':['abdomen'],'investigation_ids':[module],'structure_ids':[],'modality':'CT',
              'source_context':{'setting':'in_vivo','laterality':'not_reported','population':{'life_stage':'not_reported'},'depicted_state':image['image_state'],'extent':'local'},
              'source':{'url':image['source_url'],'license':{'name':image['license'],'url':image['license_url'],'commercial_use':True,'redistribution':True,
                         'review_status':'verified','evidence_path':str(selection_path.relative_to(ROOT)),'evidence_sha256':sha(selection_path),'attribution':attribution,'reviewed_at':'2026-10-03'}},
              'anatomical_review':{'status':'pending','reason':'No specific pancreatic structure, complete lesion, histology, phase, vascular invasion or resectability binding is granted.'},
              'visual_review':{'status':'source_checked','sha256':image['sha256'],'reviewed_at':'2026-10-04','evidence_path':'docs/cptac-pancreatic-native-sections.md'},
              'requirement_coverage':{},'presentation_dependencies':{'web/reference-media/radiology-open/'+proofname:sha(target/proofname),'web/app.js':sha(ROOT/'web/app.js')}})
    images_path.write_text(json.dumps(images,indent=2,ensure_ascii=False)+'\n')
    # Preserve exact formatting/escaping of unrelated asset records.
    raw=assets_path.read_text(); start=raw.index('[',raw.index('\"assets\"'))+1
    cursor=start; decoder=json.JSONDecoder(); retained=[]
    while True:
        cursor += len(re.match(r'\s*',raw[cursor:]).group())
        if raw[cursor]==']':break
        item,end=decoder.raw_decode(raw,cursor)
        if item['id'] not in ids:retained.append(raw[cursor:end])
        cursor=end; cursor += len(re.match(r'\s*',raw[cursor:]).group())
        if raw[cursor]==',':cursor+=1
    for item in assets['assets']:
        if item['id'] in ids:
            retained.append(json.dumps(item,indent=2,ensure_ascii=False).replace('\n','\n    '))
    assets_path.write_text(raw[:start]+'\n    '+',\n    '.join(retained)+'\n  '+raw[cursor:])


if __name__=='__main__':package()
