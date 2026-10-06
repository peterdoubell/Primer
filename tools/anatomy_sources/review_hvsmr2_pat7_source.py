#!/usr/bin/env python3
"""Review native pat7 MRI/labels independently and retain unmodified derived source surfaces."""
import argparse,csv,gzip,hashlib,json,math,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUTPUT=ROOT/'docs/hvsmr2-pat7-native-source-review'
LABELS={1:'LV',2:'RV',3:'LA_including_source_PV_extents',4:'RA',5:'AO',6:'PA',7:'SVC_both_source_channels',8:'IVC'}
def sha(raw):return hashlib.sha256(raw).hexdigest()
def read_nifti(path):
    import numpy as np
    raw=gzip.decompress(path.read_bytes());endian='<' if struct.unpack_from('<i',raw)[0]==348 else '>'
    if struct.unpack_from(endian+'i',raw)[0]!=348 or raw[344:348]!=b'n+1\x00':raise ValueError('Original single-file NIfTI-1 required')
    dims=struct.unpack_from(endian+'8h',raw,40);code,bits=struct.unpack_from(endian+'2h',raw,70);pix=struct.unpack_from(endian+'8f',raw,76)
    if dims[0]!=3 or min(dims[1:4])<1 or any(d not in [0,1] for d in dims[4:]):raise ValueError('Not a static 3D source volume')
    dt={2:'u1',4:'i2',8:'i4',16:'f4',64:'f8',512:'u2'}.get(code)
    if dt is None or bits!=np.dtype(dt).itemsize*8:raise ValueError('Unsupported scalar datatype')
    offset_float=struct.unpack_from(endian+'f',raw,108)[0];offset=int(offset_float)
    if offset!=offset_float or offset<352:raise ValueError('Invalid voxel offset')
    size=math.prod(dims[1:4]);dtype=np.dtype(endian+dt);expected=size*dtype.itemsize
    if len(raw)!=offset+expected:raise ValueError('Original payload length differs')
    slope,intercept=struct.unpack_from(endian+'2f',raw,112);qform,sform=struct.unpack_from(endian+'2h',raw,252)
    affine=np.eye(4,dtype=np.float64)
    if sform>0:affine[:3]=np.array(struct.unpack_from(endian+'12f',raw,280)).reshape(3,4)
    else:raise ValueError('Review requires explicit source sform; do not invent patient orientation')
    if not np.isfinite(affine).all() or abs(np.linalg.det(affine[:3,:3]))<1e-12:raise ValueError('Invalid source transform')
    data=np.frombuffer(raw,dtype=dtype,count=size,offset=offset).reshape(dims[1:4],order='F')
    if not np.isfinite(data).all():raise ValueError('Nonfinite source voxels')
    return data,affine,{'dimensions':list(dims[1:4]),'datatype_code':code,'bits':bits,'endian':endian,'voxel_offset':offset,
        'pixdim':list(pix),'slope':float(slope),'intercept':float(intercept),'qform_code':qform,'sform_code':sform,
        'xyzt_units':raw[123],'sform':affine.tolist(),'raw_voxel_sha256':sha(raw[offset:]),'uncompressed_bytes':len(raw)}
def review(root):
    import numpy as np,nibabel as nib
    from scipy import ndimage
    from skimage.measure import marching_cubes
    from tools.anatomy_sources.acquire_hvsmr2_pat7_source import META_SHA
    if sha((root/'figshare-25226360-v2.json').read_bytes())!=META_SHA:raise ValueError('Pinned dataset metadata differs')
    if sha((root/'PMC11219801.1.xml').read_bytes())!='7a01aae052a07f0af3ecb035252323a61485c299f616177d3f2f9b833c9a774c':raise ValueError('Reviewed source article differs')
    OUTPUT.mkdir(parents=True,exist_ok=True);acq=json.loads((root/'pat7-acquisition.json').read_text());records={r['file']:r for r in acq['records']};arrays={};headers={};checks={}
    for name in ['pat7_orig.nii.gz','pat7_orig_seg.nii.gz','pat7_orig_seg_endpoints.nii.gz']:
        path=root/name;raw=path.read_bytes();r=records[name]
        if sha(raw)!=r['sha256']:raise ValueError('Acquired original changed')
        data,affine,header=read_nifti(path);library=nib.load(path);independent=library.dataobj.get_unscaled()
        if not np.array_equal(data,independent) or not np.allclose(affine,library.affine,rtol=0,atol=1e-7):raise ValueError('Independent NIfTI reader differs')
        if header['qform_code']>0 and not np.allclose(library.get_qform(),affine,rtol=0,atol=1e-4):raise ValueError('Source qform/sform disagree')
        arrays[name]=(data,affine);headers[name]=header;checks[name]={'all_voxels_match_independent_nibabel':True,'affine_matches_independent_nibabel':True,'sha256':sha(raw)}
    image,A=arrays['pat7_orig.nii.gz'];mask,B=arrays['pat7_orig_seg.nii.gz'];endpoint,C=arrays['pat7_orig_seg_endpoints.nii.gz']
    if image.shape!=mask.shape or mask.shape!=endpoint.shape or not np.array_equal(A,B) or not np.array_equal(B,C):raise ValueError('Original source grids differ')
    if set(np.unique(mask))!={0,*LABELS} or not set(np.unique(endpoint)).issubset({0,3,5,6,7,8}):raise ValueError('Unexpected source labels')
    if any(headers[n]['slope'] not in [0,1] or headers[n]['intercept']!=0 for n in [ 'pat7_orig_seg.nii.gz','pat7_orig_seg_endpoints.nii.gz']):raise ValueError('Scaled labels unsupported')
    clinical=list(csv.DictReader((root/'hvsmr_clinical.csv').read_text().splitlines()));technical=[r for r in csv.DictReader((root/'hvsmr_technical.csv').read_text(encoding='utf-8-sig').splitlines()) if r.get('Pat')]
    cr=next(r for r in clinical if r['Pat']=='7');tr=next(r for r in technical if r['Pat']=='7')
    if cr['BilateralSVC']!='X' or cr['Category']!='moderate':raise ValueError('Reviewed case source differs')
    if [k for k,v in cr.items() if v=='X']!=['BilateralSVC']:raise ValueError('Unexpected associated diagnosis')
    classes=[]
    for label,name in LABELS.items():
        binary=mask==label;cc,n=ndimage.label(binary);sizes=np.bincount(cc.ravel())[1:];optional=endpoint==label;required=binary&~optional
        v,f,_,_=marching_cubes(binary.astype(np.uint8),level=.5,allow_degenerate=True);pos=v.astype(np.float64)@A[:3,:3].T+A[:3,3]
        # Independent scalar affine application at dispersed original vertices.
        for idx in np.linspace(0,len(v)-1,min(101,len(v)),dtype=int):
            scalar=[sum(float(A[j,k])*float(v[idx,k]) for k in range(3))+float(A[j,3]) for j in range(3)]
            if not np.allclose(pos[idx],scalar,rtol=0,atol=1e-10):raise ValueError('Scalar affine check differs')
        positions=pos.astype('<f8').tobytes();triangles=f.astype('<u4').tobytes();stem='label'+str(label)
        (OUTPUT/(stem+'-positions.f64.gz')).write_bytes(gzip.compress(positions,mtime=0));(OUTPUT/(stem+'-triangles.u32.gz')).write_bytes(gzip.compress(triangles,mtime=0))
        edges=np.sort(np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]),axis=1);_,counts=np.unique(edges,axis=0,return_counts=True)
        classes.append({'label':label,'source_name':name,'voxels':int(binary.sum()),'components_6_connected':int(n),'component_voxels_descending':sorted(sizes.tolist(),reverse=True),
            'optional_zone_voxels':int(optional.sum()),'optional_voxels_within_mask':int((optional&binary).sum()),'optional_zone_outside_original_class':int((optional&~binary).sum()),
            'required_voxels_after_source_optional_zone_subtraction':int(required.sum()),'required_mask_modified_in_source':False,
            'vertices':len(v),'triangles':len(f),'bounds_source_sform':np.stack([pos.min(0),pos.max(0)]).tolist(),
            'boundary_edges':int((counts==1).sum()),'nonmanifold_edges':int((counts>2).sum()),'positions_sha256':sha(positions),'triangles_sha256':sha(triangles)})
    for name in ['pat7_orig_seg.nii.gz','pat7_orig_seg_endpoints.nii.gz','figshare-25226360-v2.json','hvsmr_clinical.csv','hvsmr_technical.csv','pat7-acquisition.json','PMC11219801.1.json','PMC11219801.1.xml']:(OUTPUT/name).write_bytes((root/name).read_bytes())
    report={'source':'https://figshare.com/articles/dataset/HVSMR-2_0_orig_/25226360/2','source_doi':'10.6084/m9.figshare.25226360.v2',
        'article_url':'https://pmc.ncbi.nlm.nih.gov/articles/PMC11219801/','article_doi':'10.1038/s41597-024-03469-9','license':'CC BY 4.0','license_url':'https://creativecommons.org/licenses/by/4.0/','dataset_metadata_sha256':META_SHA,
        'attribution':'Pace, Danielle; Contreras, Hannah; Romanowicz, Jennifer; et al. HVSMR-2.0 (orig), figshare DOI 10.6084/m9.figshare.25226360.v2; Scientific Data DOI 10.1038/s41597-024-03469-9. CC BY 4.0. Original masks preserved; derived 0.5 isosurfaces generated as described, without source annotation changes.',
        'clinical_record':cr,'technical_record':tr,'clinical_csv_pat_count':len(clinical),'technical_csv_pat_count':len(technical),
        'archive_patient_image_ids':acq['patient_image_ids'],'clinical_csv_missing_case_ids':sorted({r['Pat'] for r in technical}-{r['Pat'] for r in clinical}),
        'clinical_csv_bilateral_svc_ids':[r['Pat'] for r in clinical if r['BilateralSVC']=='X'],'original_headers':headers,'independent_checks':checks,
        'all_original_grids_identical':True,'source_frame':nib.aff2axcodes(A),'source_intensity_range':[float(image.min()),float(image.max())],
        'source_intensity_is_HU':False,'source_units_are_nifti_declared_not_independently_linked_DICOM':True,'classes':classes,
        'derivation':'Exact original per-class binary masks; marching cubes level 0.5; original sform only; no artificial background padding, fitting, smoothing, decimation, class merge or component deletion.',
        'source_annotation_processing':'Paper reports ensemble initial labels plus manual interfaces/corrections, island removal/mild smoothing and final pediatric cardiologist review. Source masks retained unchanged; this does not independently certify each interface.',
        'limitations':['Original MRI was manually cropped at chin; no original DICOM linkage or independently measured physical calibration.',
            'Static SSFP whole-heart snapshot, not cine/flow. Case-specific contrast administration is not supplied in the technical CSV.',
            'Blood-pool classes are not independent myocardium/wall, thin valve, ductal/ligamentous, airway or every venous branch labels.',
            'LA class includes limited PV extents; optional vessel zones are benchmark tolerance and not clinical-completeness approval.',
            'Source LV/RV/LA/RA definitions can reflect benchmark choices rather than full morphological identity in complex/heterotaxy cases.',
            'Clinical CSV v2 omits pat59 although technical CSV/archive contain 60 cases; do not invent missing diagnosis.',
            'Derived closed caps/class boundaries reflect published segmentation interface conventions; no new physiological septa or vessel termination is inferred.'],
        'full_archive_md5_verified':False,'native_motion_acquired':False,'complete_venous_geometry_verified':False,'anatomical_approval':False,'clinical_approval':False,'runtime_promoted':False}
    (OUTPUT/'native-source-review.json').write_text(json.dumps(report,indent=2)+'\n');print(len(classes),'native classes reviewed; frame',report['source_frame'],'clinical missing',report['clinical_csv_missing_case_ids'])
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);review(p.parse_args().source_root)
