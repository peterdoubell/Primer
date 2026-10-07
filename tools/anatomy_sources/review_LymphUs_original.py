#!/usr/bin/env python3
"""Review complete author ultrasound archives without assuming a volumetric or commercial data grant."""
import argparse,hashlib,io,json,re,zipfile
from pathlib import Path
import numpy as np
from PIL import Image
from openpyxl import load_workbook

def sha(raw):return hashlib.sha256(raw).hexdigest()
def review(source,proof):
    proof.mkdir(parents=True,exist_ok=True)
    acquisition=json.loads((source/'acquisition.json').read_text());centres=[]
    for record in acquisition['archives']:
        raw=(source/record['archive']).read_bytes()
        if sha(raw)!=record['sha256']:raise ValueError('Original archive changed')
        centre=int(re.search(r'Center-(\d)',record['archive'])[1]);cases=[]
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            if z.testzip() is not None:raise ValueError('Original ZIP member CRC differs')
            for member in record['members']:
                data=z.read(member['file'])
                if sha(data)!=member['sha256'] or len(data)!=member['bytes']:raise ValueError('Original archive member differs')
            book_name=next(n for n in z.namelist() if n.endswith('.xlsx'))
            book=load_workbook(io.BytesIO(z.read(book_name)),read_only=True,data_only=True);sheet=book.active;rows=list(sheet.values)
            clinical={};blank_rows=[]
            for row_index,row in enumerate(rows[1:],2):
                if not any(v is not None for v in row):blank_rows.append(row_index);continue
                if row[0] is None or row[1] not in ('Benign','Malignant'):raise ValueError('Unresolved spreadsheet case identity')
                key=(row[1],int(row[0]))
                if key in clinical:raise ValueError('Duplicate clinical case identity')
                clinical[key]=row_index
            keys=set()
            for name in sorted(n for n in z.namelist() if n.endswith(' Image.bmp')):
                match=re.fullmatch(r'Center (\d)/(Benign|Malignant)/(\d+) (Benign|Malignant) Image.bmp',name)
                if not match or int(match[1])!=centre or match[2]!=match[4]:raise ValueError('Source case path identity differs')
                group,index=match[2],int(match[3]);key=(group,index);keys.add(key)
                if key not in clinical:raise ValueError('Image missing matching clinical record')
                prefix=name[:-len('Image.bmp')];files={k:prefix+suffix for k,suffix in [('image','Image.bmp'),('mask','Mask.tif'),('lesion','Lesion.bmp')]}
                images={k:Image.open(io.BytesIO(z.read(n))) for k,n in files.items()}
                if len({im.size for im in images.values()})!=1:raise ValueError('Original image/mask dimensions differ')
                arrays={k:np.asarray(im) for k,im in images.items()}
                if images['image'].mode!='L' or arrays['image'].dtype!=np.uint8 or images['mask'].mode!='1':raise ValueError('Source scalar image/binary mask representation differs')
                mask=arrays['mask'].astype(bool);locations=np.where(mask)
                if not mask.any():raise ValueError('Source mask is empty')
                cases.append({'source_case':f'centre{centre}-{group.lower()}-{index}','group':group,'index_within_group':index,'spreadsheet_row':clinical[key],
                    'original_members':files,'size_xy':list(images['image'].size),'mask_foreground_pixels':int(mask.sum()),'mask_bounds_yx_inclusive':[[int(v.min()),int(v.max())] for v in locations],
                    'mask_touches_image_border':bool(mask[0].any() or mask[-1].any() or mask[:,0].any() or mask[:,-1].any()),
                    'source_lesion_is_exact_original_image_times_mask':bool(np.array_equal(arrays['lesion'],np.where(mask,arrays['image'],0))),
                    'original_decoded_sha256':{k:sha(a.tobytes()) for k,a in arrays.items()}})
            if keys!=set(clinical):raise ValueError('Clinical/image case identities differ')
        centres.append({'centre':centre,'original_archive_sha256':sha(raw),'all_members_hashes_and_CRC_verified':True,'case_count':len(cases),'group_counts':{g:sum(c['group']==g for c in cases) for g in ['Benign','Malignant']},'spreadsheet_headers':[str(v).strip() for v in rows[0]],'blank_spreadsheet_rows_retained':blank_rows,'cases':cases})
    result={'primary_dataset':'https://qamebi.com/cervical-lymph-node/','primary_article':'https://pmc.ncbi.nlm.nih.gov/articles/PMC13049566/',
        'acquisition_sha256':sha((source/'acquisition.json').read_bytes()),'centres':centres,'source_case_identity_includes_centre_group_and_number':True,
        'publisher_archive_checksum_supplied':False,'commercial_native_dataset_clearance_verified':False,'original_native_US_DICOM_or_cine_available':False,
        'source_images_are_anonymization_cropped_8_bit_exports':True,'mask_is_node_envelope_not_independent_cortex_hilum_capsule_annotation':True,
        'physical_pixel_spacing_independently_verified':False,'source_3D_geometry_acquired':False,'individual_source_case_age_sex_plane_level_laterality_or_ENE_assumed':False,
        'source_samples_repaired_resampled_or_relabelled':False,'clinical_approval':False,'structure_coverage_granted':False,'runtime_promoted':False}
    (proof/'original-image-review.json').write_text(json.dumps(result,indent=2)+'\n')
    (proof/'original-acquisition.json').write_bytes((source/'acquisition.json').read_bytes())
    print([(c['centre'],c['case_count'],c['group_counts']) for c in centres]);print('Lesion/mask multiplication differences:',sum(not c['source_lesion_is_exact_original_image_times_mask'] for centre in centres for c in centre['cases']))
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);p.add_argument('--proof-dir',type=Path,required=True);a=p.parse_args();review(a.source_root,a.proof_dir)
