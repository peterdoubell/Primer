from pathlib import Path
import hashlib,itertools,json,re,struct
import numpy as np
from scipy.ndimage import map_coordinates
p=Path(__file__).resolve().parent
nrrd=next((p/'stiff-phase01').glob('*.nrrd'));raw=nrrd.read_bytes();h,payload=raw.split(b'\n\n',1)
fields={}
for l in h.decode().splitlines():
 if ':' in l and not l.startswith('#'):
  k,v=l.split(':',1);fields[k]=v.lstrip('=').strip()
shape=tuple(map(int,fields['sizes'].split()));a=np.frombuffer(payload,dtype='<f8').reshape(shape,order='F')
linear=np.array([list(map(float,v.split(','))) for v in re.findall(r'\(([^)]+)\)',fields['space directions'])]).T
origin=np.fromstring(fields['space origin'].strip('()'),sep=',');A=np.eye(4);A[:3,:3]=linear;A[:3,3]=origin
F=np.diag([-1,-1,1,1]);RAS=F@A
S=np.eye(4);S[:3,:]=np.array([np.fromstring(fields[k],sep=' ') for k in ['srow_x','srow_y','srow_z']])
corners=np.array(list(itertools.product(*[(0,n-1) for n in shape])));hc=np.column_stack([corners,np.ones(8)])
delta=hc@S.T-hc@RAS.T
stl=p/'stiff-phase01/frame_01.stl';b=stl.read_bytes();n=struct.unpack_from('<I',b,80)[0]
T=np.frombuffer(b,offset=84,count=n,dtype=[('n','<f4',(3,)),('v','<f4',(3,3)),('attr','<u2')])['v'].astype(float)
cent=T.mean(axis=1);cross=np.cross(T[:,1]-T[:,0],T[:,2]-T[:,0]);area=np.linalg.norm(cross,axis=1)/2;normal=cross/(2*area[:,None]);v=np.unique(T.reshape(-1,3),axis=0)
level=.0058;results=[]
def wquant(x,w,q):
 order=np.argsort(x);cum=np.cumsum(w[order]);return np.interp(np.array(q)*cum[-1],cum,x[order]).tolist()
# Exactly eight fixed origin-centred axis-sign hypotheses. No translation, scale, rigid fit, threshold optimisation or reorientation of source files.
for signs in itertools.product([-1,1],repeat=3):
 signs=np.array(signs);coords=v*signs;ix=(coords-origin)@np.linalg.inv(linear).T
 cc=cent*signs;nn=normal*signs;cx=(cc-origin)@np.linalg.inv(linear).T
 cv=map_coordinates(a,cx.T,order=1,mode='constant',cval=np.nan,prefilter=False)
 side_stats={}
 for d in [.3839285671710968,.8]:
  side=[]
  for sign in [-1,1]:
   index=(cc+nn*sign*d-origin)@np.linalg.inv(linear).T
   side.append(map_coordinates(a,index.T,order=1,mode='constant',cval=np.nan,prefilter=False))
  side=np.array(side);straddle=(np.min(side,axis=0)<=level)&(np.max(side,axis=0)>=level)
  side_stats[str(d)]={'area_weighted_fraction_sides_straddle_filename_threshold':float(np.sum(area[straddle])/np.sum(area)),
   'area_weighted_median_absolute_side_signal_difference':wquant(np.abs(side[0]-side[1]),area,[.5])[0],
   'both_side_interpolations_finite':bool(np.isfinite(side).all())}
 results.append({'STL_to_NRRD_LPS_fixed_axis_signs':signs.tolist(),'unique_vertices_inside_source_grid':int(np.all((ix>=0)&(ix<=np.array(shape)-1),axis=1).sum()),
  'index_bounds_min':ix.min(axis=0).tolist(),'index_bounds_max':ix.max(axis=0).tolist(),
  'area_weighted_mean_abs_centroid_signal_minus_filename_threshold':float(np.sum(area*np.abs(cv-level))/np.sum(area)),
  'area_weighted_centroid_signal_quantiles_05_50_95':wquant(cv,area,[.05,.5,.95]),'normal_offset_stats':side_stats,'transform_approved':False})
proof={'source_inputs':{'NRRD_SHA256':hashlib.sha256(raw).hexdigest(),'STL_SHA256':hashlib.sha256(b).hexdigest(),'sample_count':a.size,'triangle_count':n,'unique_vertices':len(v),'source_arrays_and_surface_modified':False},
 'affines':{'NRRD_LPS':A.tolist(),'NRRD_convention_only_RAS':RAS.tolist(),'inherited_NIfTI_srow':S.tolist(),'same_index_corner_displacement_max_source_numeric_units':float(np.max(np.linalg.norm(delta[:,:3],axis=1))), 'same_index_corner_displacement_axis_max':np.max(np.abs(delta[:,:3]),axis=0).tolist(),'convention_only_equivalent':bool(np.allclose(RAS,S,rtol=1e-5,atol=1e-4)),
 'mismatch':'x and z direction signs differ after LPS to RAS conversion. Origins agree to rounding. A flip of array x/z would require a distinct origin translation; inherited srow does not provide that translation. The original NIfTI payload was not supplied, so its conversion provenance cannot be reconstructed.',
 'standard_fields_govern_NRRD':True,'inherited_metadata_is_standard_NRRD_affine':False,'NRRD_explicit_space_units':fields.get('space units'), 'inherited_NIfTI_xyzt_units':fields.get('xyzt_units'),
 'source_corner_bounds_LPS_min':(hc@A.T)[:,:3].min(axis=0).tolist(),'source_corner_bounds_LPS_max':(hc@A.T)[:,:3].max(axis=0).tolist(),'STL_source_bounds_min':v.min(axis=0).tolist(),'STL_source_bounds_max':v.max(axis=0).tolist()},
 'fixed_hypothesis_tests':results,
 'method_limits':{'normal_offsets_are_source_numeric_units':'paper describes nominal millimetre scale; header does not explicitly declare units','filename_threshold_is_ground_truth':False,'linear_interpolation_is_original_sample_measurement':False,'air_tissue_straddling_is_anatomic_accuracy_proof':False,'coordinate_fit_performed':False,'registration_or_anatomical_coverage_approved':False,'separate_cartilage_mucosal_ligament_muscle_vessel_nerve_labels_supported':False},
 'primary_references':{'NRRD_format':'https://teem.sourceforge.net/nrrd/format.html','NIfTI_coordinate_definition':'https://nifti.nimh.nih.gov/pub/dist/src/niftilib/nifti1.h','Slicer_file_defaults':'https://slicer.readthedocs.io/en/5.10/user_guide/data_loading_and_saving.html','Slicer_coordinate_systems':'https://slicer.readthedocs.io/en/5.10/user_guide/coordinate_systems.html','source_dataset':'https://zenodo.org/records/19629778','source_article':'https://doi.org/10.1121/10.0043582'}}
(p/'coordinate-interface-independent-audit.json').write_text(json.dumps(proof,indent=2)+'\n')
print(json.dumps({'affine_displacement_max':proof['affines']['same_index_corner_displacement_max_source_numeric_units'],'hypotheses':[{'signs':r['STL_to_NRRD_LPS_fixed_axis_signs'],'residual':r['area_weighted_mean_abs_centroid_signal_minus_filename_threshold'],'straddles_0_8':r['normal_offset_stats']['0.8']['area_weighted_fraction_sides_straddle_filename_threshold']} for r in results]},indent=2))
