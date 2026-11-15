#!/usr/bin/env python3
"""Inventory one verified LiverHccSeg case without mixing original and warped volumes."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import zipfile

ORIGINAL={'pre.nii.gz':'precontrast T1','art.nii.gz':'arterial T1','pv.nii.gz':'portal-venous T1','del.nii.gz':'delayed T1'}
DERIVED={'art_pre.nii.gz':'registered precontrast to arterial','art_pv.nii.gz':'registered portal-venous to arterial','art_del.nii.gz':'registered delayed to arterial'}


def role(name):
    if name in ORIGINAL:return {'kind':'original_phase','publisher_sequence_identity':ORIGINAL[name],'source_registered':False}
    if name in DERIVED:return {'kind':'registered_derivative','publisher_sequence_identity':DERIVED[name],'source_registered':True}
    match=re.fullmatch(r'rater([12])_(liver|tumor([1-9][0-9]*))\.nii\.gz',name)
    if match:return {'kind':'independent_rater_mask','rater':int(match.group(1)),'roi':match.group(2),'source_mask_combined':False}
    raise ValueError('Unknown source MRI filename; do not infer sequence identity')


def inventory(root,output):
    import numpy as np
    import nibabel as nib
    archive=root/'nifti_and_segms.zip';receipt=json.loads((root/'nifti_and_segms.zip.acquisition.json').read_text())
    publisher=json.loads((root/'record.json').read_text());expected=next(e for e in publisher['files'] if e['key']==archive.name)
    if publisher['id']!=8179129 or publisher['metadata']['version']!='1.1' or receipt['publisher_md5']!=expected['checksum'] or not receipt['publisher_md5_verified']:
        raise ValueError('Corrected source archive identity is not verified')
    md5=hashlib.md5();sha=hashlib.sha256()
    with archive.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):md5.update(chunk);sha.update(chunk)
    if 'md5:'+md5.hexdigest()!=expected['checksum'] or sha.hexdigest()!=receipt['sha256']:
        raise ValueError('Whole verified source archive changed')
    prefix='nifti_and_segms/TCGA-BC-A3KG/02-02-2002/'
    dest=root/'case-BC-A3KG-original-and-derived';dest.mkdir(exist_ok=True);records=[]
    with zipfile.ZipFile(archive) as z:
        names=[n for n in z.namelist() if n.startswith(prefix) and n.endswith('.nii.gz') and not Path(n).name.startswith('._')]
        if len(names)!=len(set(names)):raise ValueError('Repeated source case member')
        for name in names:
            filename=Path(name).name;classification=role(filename);b=z.read(name);p=dest/filename;p.write_bytes(b)
            im=nib.load(p);a=np.asanyarray(im.dataobj);q,qcode=im.get_qform(coded=True);s,scode=im.get_sform(coded=True)
            if not np.isfinite(a).all() or not np.isfinite(im.affine).all():raise ValueError('Nonfinite source volume')
            rec={'source_member':name,'filename':filename,'bytes':len(b),'member_crc_verified':True,'sha256':hashlib.sha256(b).hexdigest(),**classification,
                 'shape':list(im.shape),'sampling_mm':list(map(float,im.header.get_zooms()[:3])),'selected_affine_ras':im.affine.tolist(),
                 'qform_code':int(qcode),'sform_code':int(scode),'qform_ras':None if q is None else q.tolist(),'sform_ras':None if s is None else s.tolist(),
                 'qform_sform_max_difference_mm':None if q is None or s is None else float(np.abs(q-s).max()),
                 'index_axis_codes':list(nib.aff2axcodes(im.affine)),'dtype':str(a.dtype),'range':[float(a.min()),float(a.max())],
                 'clinical_approval':False}
            if classification['kind']=='independent_rater_mask':
                rec['mask_values']=np.unique(a).tolist();rec['positive_voxels']=int(np.count_nonzero(a))
                rec['touches_source_boundary']=any(np.any(np.take(a,index,axis=axis)>0) for axis in range(3) for index in (0,-1))
            records.append(rec)
    if {r['filename'] for r in records if r['kind']=='original_phase'}!=set(ORIGINAL):raise ValueError('Original phase set incomplete')
    art=next(r for r in records if r['filename']=='art.nii.gz')
    for rec in records:
        rec['matches_arterial_reference_shape']=rec['shape']==art['shape']
        rec['matches_arterial_reference_selected_affine']=rec['selected_affine_ras']==art['selected_affine_ras']
    output.write_text(json.dumps({'source_doi':'10.5281/zenodo.8179129','source_version':'1.1','case_id':'TCGA-BC-A3KG',
        'whole_archive_publisher_md5_verified':True,'archive_sha256':receipt['sha256'],'records':records,
        'source_values_changed':False,'source_registered_and_original_volumes_combined':False,'rater_masks_merged':False,
        'original_dicom_acquisition_complete':False,'clinical_approval':False,'runtime_promoted':False,
        'limits':['Publisher filename identities do not verify every DICOM sequence, patient eligibility or contrast timing.',
                  'Matching registered grids are not native acquisition or validated anatomical correspondence.',
                  'T1 contrast volumes do not grant T2, ADC, fat-sensitive or hepatobiliary sequence coverage.',
                  'All original sampling, affine conflicts, boundary contacts and rater differences require review.']},indent=2)+'\n')
    print('Verified case files:',len(records));print([(r['filename'],r['shape'],r['sampling_mm'],r.get('positive_voxels')) for r in records])


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();inventory(a.source_root,a.output)
