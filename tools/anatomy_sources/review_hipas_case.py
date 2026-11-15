#!/usr/bin/env python3
"""Inspect released original array samples and source limits without inventing native patient geometry."""
import argparse
import hashlib
import json
import xml.etree.ElementTree as E
import zipfile
from pathlib import Path
import numpy as np
from scipy import ndimage
def sha(raw):return hashlib.sha256(raw).hexdigest()
def describe(path, segmentation=False):
    with np.load(path,allow_pickle=False) as original:
        if original.files!=['data']:raise ValueError('Unexpected source NPZ keys')
        a=original['data']
    if a.ndim!=3 or not np.isfinite(a).all():raise ValueError('Invalid original scalar volume')
    row={'source_file_sha256':sha(path.read_bytes()),'array_key':'data','shape':list(a.shape),'dtype':str(a.dtype),'array_sha256':sha(a.tobytes(order='C')),'finite':True,'minimum':float(a.min()),'maximum':float(a.max())}
    if segmentation:
        if not np.isin(a,[0,1]).all():raise ValueError('Not the reviewed original binary mask')
        mask=a!=0;locations=np.where(mask);labels,count=ndimage.label(mask,ndimage.generate_binary_structure(3,1));sizes=np.bincount(labels.ravel())[1:];descending=np.sort(sizes)[::-1]
        row.update({'foreground_voxels':int(mask.sum()),'source_index_bounds_inclusive':[[int(x.min()),int(x.max())] for x in locations],'six_neighbour_components':int(count),'six_neighbour_component_sizes_descending':[int(n) for n in descending],'unfiltered_components_retained':True})
    return a,row
def review(root,out):
    acquisition=json.loads((root/'case-001-acquisition.json').read_text());record=json.loads((root/'zenodo-14879605.json').read_text());f=next(f for f in record['files'] if f['key']=='annotation.zip');archive=root/'annotation.zip'
    if archive.stat().st_size!=f['size'] or hashlib.md5(archive.read_bytes()).hexdigest()!=f['checksum'].split(':')[1]:raise ValueError('Original full annotation archive differs')
    ct,cp=describe(root/'case-001/ct/001.npz');artery,ap=describe(root/'case-001/annotation/artery/001.npz',True);vein,vp=describe(root/'case-001/annotation/vein/001.npz',True)
    if cp['source_file_sha256']!=acquisition['member_sha256']:raise ValueError('Acquired original CT file changed')
    if not ct.shape==artery.shape==vein.shape:raise ValueError('Original arrays do not share shape')
    # Original spreadsheet only supplies a spacing vector; no affine/IPP/IOP is inferred.
    ns={'x':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
    with zipfile.ZipFile(root/'metadata.xlsx') as z:
        strings=[''.join(si.itertext()) for si in E.fromstring(z.read('xl/sharedStrings.xml')).findall('x:si',ns)];sheet=E.fromstring(z.read('xl/worksheets/sheet1.xml'))
        values=[]
        for row in sheet.findall('.//x:row',ns):
            cells=[]
            for c in row.findall('x:c',ns):
                text=c.findtext('x:v','',ns);cells.append(strings[int(text)] if c.get('t')=='s' else text)
            if '001.npz' in cells:values.append(cells)
    if len(values)!=1:raise ValueError('Source spreadsheet case absent/ambiguous')
    p={'record_id':14879605,'record_url':'https://zenodo.org/records/14879605','source_record_sha256':sha((root/'zenodo-14879605.json').read_bytes()),'source_metadata_xlsx_sha256':sha((root/'metadata.xlsx').read_bytes()),'original_case_spreadsheet_row':values[0],'case':'001','original_CT_acquisition':acquisition,'annotation_archive':{'file':f['key'],'bytes':f['size'],'publisher_checksum':f['checksum'],'whole_archive_md5_verified':True,'sha256':sha(archive.read_bytes())},'CT':cp,'artery':ap,'vein':vp,'same_array_shape_verified':True,'foreground_overlap_voxels':int(np.count_nonzero((artery!=0)&(vein!=0))),'original_npz_source_keys':['data'],'native_DICOM_geometry_present':False,'patient_coordinate_affine_verified':False,'source_axis_order_and_laterality_verified':False,'source_voxel_to_HU_calibration_verified':False,'matching_raw_DICOM_acquisition_verified':False,'whole_24GB_CT_archive_checksum_verified':False,'published_segmentation_is_independently_clinically_validated':False,'full_lumen_wall_and_all_tissue_coverage_verified':False,'rights':{'zenodo_record_license':record['metadata']['license'],'article_figure_license':'CC BY-NC-ND 4.0','old_Google_Drive_sample_README_restriction_is_not_assumed_to_be_same_Zenodo_release':True,'commercial_dataset_reuse_review':'pending_scope_and_grant_reconciliation'},'runtime_promoted':False,'structure_coverage_granted':False}
    out.mkdir(parents=True,exist_ok=True);(out/'original-case-array-review.json').write_text(json.dumps(p,indent=2)+'\n')
    print(json.dumps({'shape':cp['shape'],'CT_dtype':cp['dtype'],'CT_range':[cp['minimum'],cp['maximum']],'artery_voxels':ap['foreground_voxels'],'vein_voxels':vp['foreground_voxels'],'artery_components':ap['six_neighbour_components'],'vein_components':vp['six_neighbour_components'],'overlap':p['foreground_overlap_voxels'],'spreadsheet_row':values[0]}))
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--source-root',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();review(args.source_root,args.output)
