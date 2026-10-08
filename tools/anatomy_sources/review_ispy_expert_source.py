#!/usr/bin/env python3
"""Preserve original expert ISPY source arrays/geometry and separate processed grids."""
import gzip,hashlib,json,math,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
import numpy as np,nibabel as nib
from scipy import ndimage,sparse
from scipy.sparse.csgraph import connected_components
from skimage.measure import marching_cubes
SOURCE=Path('/Users/peter/Documents/ChatGPT/Primer/.research/breast-native-MRI-source/expert-original-ISPY1_1002')
OUT=SOURCE/'native-review'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def read(path):
    raw=gzip.decompress(path.read_bytes());endian='<' if struct.unpack_from('<i',raw)[0]==348 else '>'
    if struct.unpack_from(endian+'i',raw)[0]!=348 or raw[344:348]!=b'n+1\0':raise ValueError('Original single-file NIfTI1 required')
    dims=struct.unpack_from(endian+'8h',raw,40);code,bits=struct.unpack_from(endian+'2h',raw,70);pix=struct.unpack_from(endian+'8f',raw,76);off=struct.unpack_from(endian+'f',raw,108)[0];offset=int(off)
    dtype={2:'u1',4:'i2',8:'i4',16:'f4',64:'f8',512:'u2'}.get(code)
    if dims[0]!=3 or min(dims[1:4])<1 or dtype is None or offset!=off or offset<352 or bits!=np.dtype(dtype).itemsize*8:raise ValueError('Unexpected original scalar source layout')
    count=math.prod(dims[1:4]);payload=raw[offset:offset+count*bits//8]
    if len(payload)!=count*bits//8 or len(raw)!=offset+len(payload):raise ValueError('Original payload count differs')
    values=np.frombuffer(payload,dtype=endian+dtype).reshape(dims[1:4],order='F');qcode,scode=struct.unpack_from(endian+'2h',raw,252);q=None;s=None
    if qcode>0:
        b,c,d=struct.unpack_from(endian+'3f',raw,256);norm=b*b+c*c+d*d
        if norm>1+1e-6:raise ValueError('Invalid original quaternion')
        if norm>1:b,c,d=np.array([b,c,d])/math.sqrt(norm)
        a=math.sqrt(max(0,1-b*b-c*c-d*d));R=np.array([[a*a+b*b-c*c-d*d,2*b*c-2*a*d,2*b*d+2*a*c],[2*b*c+2*a*d,a*a+c*c-b*b-d*d,2*c*d-2*a*b],[2*b*d-2*a*c,2*c*d+2*a*b,a*a+d*d-c*c-b*b]])
        q=np.eye(4);q[:3,:3]=R@np.diag([pix[1],pix[2],pix[3]*(-1 if pix[0]<0 else 1)]);q[:3,3]=struct.unpack_from(endian+'3f',raw,268)
    if scode>0:s=np.vstack([np.array(struct.unpack_from(endian+'12f',raw,280)).reshape(3,4),[0,0,0,1]])
    A=s if s is not None else q
    if A is None or not np.isfinite(A).all() or abs(np.linalg.det(A[:3,:3]))<1e-12:raise ValueError('Original declared geometry missing/invalid')
    if s is not None and q is not None and not np.allclose(s,q,rtol=0,atol=1e-6):raise ValueError('Original sform/qform disagree')
    h={'shape':list(values.shape),'datatype_code':code,'bits':bits,'source_dtype':endian+dtype,'sample_count':count,'payload_sha256':sha(payload),'voxel_offset':offset,'source_declared_units':raw[123],'pixdim':list(pix),'slope_intercept':list(struct.unpack_from(endian+'2f',raw,112)),'qform_code':qcode,'sform_code':scode,'qform':q.tolist() if q is not None else None,'sform':s.tolist() if s is not None else None,'affine':A.tolist(),'all_source_values_finite':bool(np.isfinite(values).all()),'stored_range':[float(values.min()),float(values.max())]}
    return values,A,h

def review():
    OUT.mkdir(exist_ok=True);acquisition=json.loads((SOURCE/'original-acquisition.json').read_text());records=[];arrays={};headers={};surfaces=[]
    if len(acquisition['records'])!=9:raise ValueError('Complete selected nine-file acquisition required')
    for row in acquisition['records']:
        path=SOURCE/row['file'];raw=path.read_bytes()
        if sha(raw)!=row['sha256'] or hashlib.md5(raw).hexdigest()!=row['source_MD5']:raise ValueError('Original acquired source changed')
        a,A,h=read(path);library=nib.load(path)
        if not np.array_equal(a,library.dataobj.get_unscaled(),equal_nan=True) or not np.allclose(A,library.affine,rtol=0,atol=1e-6):raise ValueError('Independent original sample/affine reading differs')
        records.append({'file':row['file'],'source_file_sha256':sha(raw),'all_samples_and_affines_match_independent_reader':True,**h});arrays[row['file']]=(a,A);headers[row['file']]=h
        print('Original samples/affine checked',row['file'],a.size,flush=True)
    manual_key=next(k for k in arrays if k.startswith('masks_stv_manual/'));manual,M=arrays[manual_key]
    normalized=[k for k in arrays if k.startswith('images_bias-corrected_resampled_zscored_nifti/')]
    if any(arrays[k][0].shape!=manual.shape or not np.array_equal(arrays[k][1],M) for k in normalized):raise ValueError('Expert mask and processed source MRI grids differ')
    for key,(values,A) in arrays.items():
        if not key.startswith('masks_'):continue
        labels=set(np.unique(values));expected={0,255} if key.startswith('masks_ftv/') else {0,1}
        if labels!=expected:raise ValueError('Original source class values changed')
        mask=values!=0;cc,n=ndimage.label(mask,ndimage.generate_binary_structure(3,1));locations=np.where(mask);bounds=[[int(v.min()),int(v.max())] for v in locations];verts,faces,_,_=marching_cubes(mask.astype('u1'),level=.5,allow_degenerate=True);world=verts.astype(float)@A[:3,:3].T+A[:3,3];tri=world[faces];area=np.linalg.norm(np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]),axis=1)/2
        e=np.sort(np.concatenate([faces[:,[0,1]],faces[:,[1,2]],faces[:,[2,0]]]),axis=1);unique,counts=np.unique(e,axis=0,return_counts=True);graph=sparse.coo_matrix((np.ones(len(unique)*2),(np.concatenate([unique[:,0],unique[:,1]]),np.concatenate([unique[:,1],unique[:,0]]))),shape=(len(verts),len(verts))).tocsr();nc,c=connected_components(graph,directed=False);inverse=np.linalg.inv(A);indices=world@inverse[:3,:3].T+inverse[:3,3];residual=np.abs(ndimage.map_coordinates(mask.astype(float),indices.T,order=1,mode='constant',cval=np.nan)-.5)
        stem=key.split('/')[0];position=world.astype('<f8').tobytes();face=faces.astype('<u4').tobytes();(OUT/(stem+'-positions.f64.gz')).write_bytes(gzip.compress(position,mtime=0));(OUT/(stem+'-triangles.u32.gz')).write_bytes(gzip.compress(face,mtime=0));surfaces.append({'file':key,'producer_role':'expert structural tumour' if stem=='masks_stv_manual' else 'functional enhancement-derived tumour mask' if stem=='masks_ftv' else 'computed structural tumour prediction','foreground_voxels':int(mask.sum()),'source_label_values':sorted(float(x) for x in labels),'source_mask_components_6':int(n),'source_surface_components':int(nc),'component_triangle_counts':np.bincount(c[faces[:,0]]).tolist(),'native_source_bounds_inclusive':bounds,'source_volume_boundary_axes':[i for i,b in enumerate(bounds) if b[0]==0 or b[1]==mask.shape[i]-1],'vertices':len(verts),'triangles':len(faces),'positions_sha256':sha(position),'triangles_sha256':sha(face),'world_bounds':np.stack([world.min(0),world.max(0)]).tolist(),'source_boundary_edges':int((counts==1).sum()),'source_nonmanifold_edges':int((counts>2).sum()),'degenerate_triangles':int((area==0).sum()),'source_binary_field_residual_max':float(np.nanmax(residual)),'residual_is_anatomical_distance_or_error':False,'source_geometry_repaired_smoothed_capped_or_decimated':False})
    computed_key=next(k for k in arrays if k.startswith('masks_stv_resunet/'));computed,C=arrays[computed_key]
    if computed.shape!=manual.shape or not np.array_equal(C,M):raise ValueError('Computed/manual comparison lacks original same-grid source')
    dice=2*float(((computed!=0)&(manual!=0)).sum())/float((computed!=0).sum()+(manual!=0).sum())
    proof={'case':'ISPY1_1002','source_acquisition_sha256':sha((SOURCE/'original-acquisition.json').read_bytes()),'all_nine_original_samples_and_affines_independently_checked':True,'total_original_scalar_samples_checked':sum(r['sample_count'] for r in records),'source_records':records,'expert_manual_mask_exactly_matches_all_three_processed_1mm_MRI_grids':True,'source_MRI_bias_corrected_resampled_and_zscored_by_producer':True,'source_processed_sample_pitch_establishes_native_acquisition_resolution':False,'source_acquired_DICOM_or_original_patient_registration_verified':False,'source_surfaces':surfaces,'manual_and_computed_original_voxel_Dice':dice,'computed_mask_substituted_for_expert_mask':False,'geometry_or_image_voxels_fitted_resampled_repaired_or_deleted_by_this_review':False,'source_expert_review_is_whole_breast_fine_anatomical_approval':False,'clinical_approval':False,'runtime_promoted':False};(OUT/'original-source-review.json').write_text(json.dumps(proof,indent=2)+'\n');print('Nine complete originals;',proof['total_original_scalar_samples_checked'],'samples; manual/computed Dice',dice);print([(s['producer_role'],s['triangles'],s['source_surface_components']) for s in surfaces])
def render_review():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    proof=json.loads((OUT/'original-source-review.json').read_text());fig=plt.figure(figsize=(15,6));plots=[]
    for i,row in enumerate(proof['source_surfaces']):
        stem=row['file'].split('/')[0];v=np.frombuffer(gzip.decompress((OUT/(stem+'-positions.f64.gz')).read_bytes()),'<f8').reshape(-1,3);faces=np.frombuffer(gzip.decompress((OUT/(stem+'-triangles.u32.gz')).read_bytes()),'<u4').reshape(-1,3);tri=v[faces];normals=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);length=np.linalg.norm(normals,axis=1);normals=np.divide(normals,length[:,None],out=np.zeros_like(normals),where=length[:,None]>0);shade=.3+.7*np.abs(normals@np.array([.3,-.4,.8660254]));ax=fig.add_subplot(1,3,i+1,projection='3d');ax.add_collection3d(Poly3DCollection(tri,facecolors=shade[:,None]*np.array([.65,.74,.8]),edgecolor='none'));low=v.min(0);high=v.max(0);ax.set_xlim(low[0],high[0]);ax.set_ylim(low[1],high[1]);ax.set_zlim(low[2],high[2]);ax.set_box_aspect(high-low);ax.set_proj_type('ortho');ax.view_init(elev=20,azim=-65);ax.set_title(row['producer_role']+'\n'+str(row['triangles'])+' full source triangles',fontsize=10);ax.set_xlabel('Source RAS x');ax.set_ylabel('Source RAS y');ax.set_zlabel('Source RAS z')
    fig.subplots_adjust(left=.03,right=.96,bottom=.1,top=.86,wspace=.15);path=OUT/'complete-source-surface-review.png';fig.savefig(path,dpi=120);plt.close(fig);plots.append({'filename':path.name,'sha256':sha(path.read_bytes())})
    mask=np.asarray(nib.load(SOURCE/'masks_stv_manual/ISPY1_1002.nii.gz').dataobj);image=np.asarray(nib.load(SOURCE/'images_bias-corrected_resampled_zscored_nifti/ISPY1_1002_DCE_0001_N3_zscored.nii.gz').dataobj);indices=np.array(np.where(mask)).mean(axis=1).round().astype(int);fig,axes=plt.subplots(1,3,figsize=(18,7));rows=[]
    for axis,ax in enumerate(axes):
        plane=np.take(image,indices[axis],axis=axis);target=np.take(mask,indices[axis],axis=axis);ax.imshow(plane.T,origin='lower',cmap='gray',vmin=-1.5,vmax=5,interpolation='nearest');ax.contour(target.T,levels=[.5],colors=['#f59e0b'],linewidths=.9);ax.set_title('Complete processed source plane | axis '+str(axis)+' index '+str(indices[axis]),fontsize=11);rows.append({'axis':axis,'index':int(indices[axis]),'shape':list(plane.shape),'source_full_plane_float32_sha256':sha(plane.astype('<f4').tobytes(order='F')),'source_full_mask_plane_float32_sha256':sha(target.astype('<f4').tobytes(order='F'))})
    fig.suptitle('Expert source mask and matching processed MRI | original arrays, illustrative display window only',fontsize=13);fig.subplots_adjust(left=.04,right=.98,bottom=.1,top=.85,wspace=.16);path=OUT/'expert-mask-matching-processed-MRI-planes.png';fig.savefig(path,dpi=100);plt.close(fig);plots.append({'filename':path.name,'sha256':sha(path.read_bytes())});(OUT/'visual-render-proof.json').write_text(json.dumps({'complete_source_triangles_rendered_without_decimation':True,'source_MRI_and_mask_grids_unchanged':True,'plane_records':rows,'display_window_source_zscores':[-1.5,5],'original_native_DICOM_physical_calibration_or_clinical_approval':False,'plots':plots},indent=2)+'\n')
if __name__=='__main__':
    review()
    render_review()

