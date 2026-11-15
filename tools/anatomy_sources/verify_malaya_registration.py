#!/usr/bin/env python3
"""Check STL-to-author-label geometry; distinguish offline source image metadata."""
import gzip,hashlib,json,pathlib,re
import numpy as np

ROOT=pathlib.Path('/tmp/primer-msk-sources/high-fidelity')
REG=ROOT/'um-registration'

def knee_image_correspondence():
 """Separate source-reference metadata from independently validated pairing."""
 audit=ROOT/'um-knee-image-audit'
 acquisition=json.loads((audit/'reference-volume-acquisition.json').read_text())
 reference=pathlib.Path(acquisition['reference_image_file'])
 assert hashlib.sha256(reference.read_bytes()).hexdigest()==acquisition['sha256']
 def geometry(path):
  with path.open('rb') as source:
   lines=[]
   while True:
    line=source.readline()
    if not line.strip():break
    lines.append(line.decode())
  header={line.split(':',1)[0]:line.split(':',1)[1].strip() for line in lines if ':' in line and not line.startswith('#')}
  vectors=[list(map(float,p.strip('()').split(','))) for p in re.findall(r'\([^)]*\)',header['space directions'])]
  return {'exported_grid_mm':[float(np.linalg.norm(v)) for v in vectors],
          'origin_lps_mm':list(map(float,header['space origin'].strip('()').split(','))),
          'direction_columns':vectors,'sizes':list(map(int,header['sizes'].split()))}
 comparison=REG/'19 RT T2 FS spc_SAG_iso (KNEE).nrrd'
 return {'status':'offline_research_only; no independently validated clinical image/mesh pairing',
  'segmentation_reference':{'mrml_volume_id':acquisition['reference_volume_id'],
   'source_label':acquisition['reference_volume_name'],'source_datafile':595,
   'member':acquisition['source_member'],'sha256':acquisition['sha256'],
   'relation':'Explicit MRML referenceImageGeometryRef; source geometry correspondence is not independent tissue-boundary validation.',
   **geometry(reference)},
  'separate_comparison_sequence':{'mrml_volume_id':'vtkMRMLScalarVolumeNode12',
   'source_label':'19: RT T2 FS spc_SAG_iso (KNEE)','source_datafile':595,
   'member':'Final model segmentation/'+comparison.name,'sha256':hashlib.sha256(comparison.read_bytes()).hexdigest(),
   'is_segmentation_reference':False,'cross_sequence_alignment_validated':False,**geometry(comparison)},
  'no_fitted_transform':True,
  'contrast_limit':'Sequence labels come from source filenames/MRML and the authors; acquisition TR/TE and original MR DICOM were not supplied in these NRRDs.',
  'disposition':'Source scans retained offline for research correspondence review; no diagnostic examples or clinical pair offered.'}

def load_nrrd(path):
 raw=pathlib.Path(path).read_bytes();head,payload=raw.split(b'\n\n',1);lines=head.decode().splitlines();header={}
 for line in lines:
  if line.startswith('#') or ':' not in line:continue
  key,value=line.split(':=',1) if ':=' in line else line.split(':',1);header[key]=value.strip()
 types={'unsigned char':'u1','short':'<i2','unsigned short':'<u2'}
 data=gzip.decompress(payload) if header['encoding']=='gzip' else payload
 sizes=tuple(map(int,header['sizes'].split()));a=np.frombuffer(data,dtype=types[header['type']]).reshape(sizes,order='F')
 vectors=[]
 for p in re.findall(r'none|\([^)]*\)',header['space directions']):
  if p=='none':vectors.append(None)
  else:vectors.append(np.array(list(map(float,p.strip('()').split(',')))))
 origin=np.array(list(map(float,header['space origin'].strip('()').split(','))))
 return header,a,vectors,origin

def main(manifest_path=None, image_path=None):
 manifest_path=pathlib.Path(manifest_path) if manifest_path is not None else ROOT/'malaya-knee/manifest.json'
 manifest=json.loads(manifest_path.read_text());header,segments,vectors,origin=load_nrrd(REG/'Segmentation.seg.nrrd')
 assert header['space']=='left-posterior-superior'
 direction=np.column_stack([v for v in vectors if v is not None]);names={}
 for key,value in header.items():
  match=re.fullmatch(r'Segment(\d+)_Name',key)
  if match:
   prefix='Segment'+match[1]+'_';names[value.strip()]={'name':value,'id':header[prefix+'ID'],'layer':int(header[prefix+'Layer']),'label_value':int(header[prefix+'LabelValue'])}
 checks=[]
 for part in manifest['parts'].values():
  segment_name={'Ligament_Patella':'Tendon_Patella'}.get(part['source_name'],part['source_name']);segment=names[segment_name];voxels=np.argwhere(segments[segment['layer']]==segment['label_value'])
  lo,hi=voxels.min(0),voxels.max(0)
  corners=np.array([[x,y,z] for x in [lo[0]-.5,hi[0]+.5] for y in [lo[1]-.5,hi[1]+.5] for z in [lo[2]-.5,hi[2]+.5]])@direction.T+origin
  bbox=np.array([corners.min(0),corners.max(0)]);mesh=np.array(part['bounds']);delta=float(np.max(abs(mesh-bbox)))
  part['source_segmentation']=segment
  checks.append({'part':part['name'],'source_segment':segment,'mesh_to_voxel_extent_max_difference_mm':delta,'voxel_count':len(voxels),'same_frame_extent_check':delta<2.5})
 image_path=pathlib.Path(image_path) if image_path is not None else (REG/'19 RT T2 FS spc_SAG_iso (KNEE).nrrd' if 'knee' in manifest['regions'] else None)
 if image_path:
  ih,image,iv,io=load_nrrd(image_path);assert ih['space']==header['space']
 else:iv=[];io=np.array([])
 dicom=json.loads((REG/'dicom-geometry-evidence.json').read_text())
 result={'scope':'STL-to-author-segmentation names, LPS metadata and bounding extents only; not independently validated MRI tissue boundaries','same_anatomical_basis':True,'source_segmentation_names_found':len(checks),'coordinate_units':'millimeters','unit_evidence':'Public DICOM ImagePositionPatient/PixelSpacing fields (millimeters by DICOM definition) match the segmentation source grid; no rescaling applied.','dicom_geometry':dicom,'dicom_modality_caveat':'The derivative DICOM identifies CT Image Storage, Modality CT, ImageType ORIGINAL/PRIMARY/AXIAL, RescaleType HU and Manufacturer 3D Slicer despite a T1 VIBE DIXON description and author MRI methods; MR acquisition timing/field-strength metadata are absent. Do not treat its pixels as calibrated HU or validated original acquisition DICOM.','segmentation_origin':origin.tolist(),'segmentation_direction_columns':[v.tolist() if v is not None else None for v in vectors],'checks':checks}
 is_knee='knee' in manifest['regions']
 if is_knee:
  import pydicom
  derivative=REG/'representative-source-frame.dcm';dataset=pydicom.dcmread(derivative,stop_before_pixels=True)
  safe_fields=('SOPClassUID','Modality','ImageType','SeriesDescription','Manufacturer','RescaleType',
               'RepetitionTime','EchoTime','InversionTime','FlipAngle','MagneticFieldStrength')
  result['derivative_dicom_technical_fields']={key:str(getattr(dataset,key,'ABSENT')) for key in safe_fields}
  result['derivative_dicom_sha256']=hashlib.sha256(derivative.read_bytes()).hexdigest()
 evidence_path=ROOT/'um-knee-image-audit/registration-evidence.json' if is_knee else manifest_path.parent/'registration-evidence.json'
 if is_knee:
  correspondence=knee_image_correspondence();manifest['source_image_correspondence']=correspondence
  result['source_image_correspondence']=correspondence
  manifest['sampling_limits'].pop('paired_T2_FS_exported_grid_mm',None)
  manifest['sampling_limits']['segmentation_reference_exported_grid_mm']=correspondence['segmentation_reference']['exported_grid_mm']
  manifest['sampling_limits']['separate_T2_FS_comparison_exported_grid_mm']=correspondence['separate_comparison_sequence']['exported_grid_mm']
  source_audit=ROOT/'um-knee-image-audit/paired-source-audit.json'
  if source_audit.exists():
   review=json.loads(source_audit.read_text())
   result['offline_representation_comparison']={
    'scope':'Mesh-versus-author-label consistency only; no independent anatomical or clinical approval',
    'reference_image_origin_in_segmentation_ijk':review['reference_image_origin_in_segmentation_ijk'],
    'audit_sha256':hashlib.sha256(source_audit.read_bytes()).hexdigest(),
    'structures':[{key:item[key] for key in ('id','name','source_label_voxels','label_volume_mm3','mesh_volume_mm3','mesh_volume_difference_percent','mesh_vertex_to_boundary_voxel_centre_mm','planes')} for item in review['structures']]}
  manifest['clinical_image_pair']={'available':False,'independent_clinical_validation':False,
   'registration_status':'No independently validated clinical MRI/mesh pair. Actual MRML reference volume25 and separate comparison volume19 are documented in source_image_correspondence.',
   'metadata_caveat':result['dicom_modality_caveat']}
 evidence_path.write_text(json.dumps(result,indent=2)+'\n')
 manifest['registration_validation']={'scope':result['scope'],'source_segment_matches':len(checks),'extent_checks_within_2_5_mm':sum(c['same_frame_extent_check'] for c in checks),'maximum_mesh_to_voxel_extent_difference_mm':max(c['mesh_to_voxel_extent_max_difference_mm'] for c in checks),'evidence_file':str(evidence_path),'evidence_sha256':hashlib.sha256(evidence_path.read_bytes()).hexdigest(),'clinical_alignment_approval':False};
 for part,check in zip(manifest['parts'].values(),checks):part['mesh_to_voxel_extent_difference_mm']=check['mesh_to_voxel_extent_max_difference_mm']
 manifest['coordinate_system']['units']='millimeters';manifest['coordinate_system']['unit_meters']=.001;manifest['coordinate_system']['units_evidence']=result['unit_evidence']
 if not is_knee:
  manifest['clinical_image_pair']['registration_status']='STL source names and extents matched to author segmentation in LPS; this does not validate MRI tissue boundaries.'
  manifest['clinical_image_pair']['local_segmentation']=str(REG/'Segmentation.seg.nrrd');manifest['clinical_image_pair']['metadata_caveat']=result['dicom_modality_caveat']
 if image_path and not is_knee:
  manifest['clinical_image_pair']['local_image']=str(image_path)
  manifest['clinical_image_pair']['registration_status']+=' MRI and segmentation have different voxel grids and require coordinate-based resampling for overlay.'
 manifest_path.write_text(json.dumps(manifest,indent=2)+'\n')
 print('Source segment matches',len(checks),'extentpass',sum(c['same_frame_extent_check'] for c in checks),'maxextentdifference',max(c['mesh_to_voxel_extent_max_difference_mm'] for c in checks))
 for c in checks:print(c['part'],round(c['mesh_to_voxel_extent_max_difference_mm'],4),c['source_segment']['layer'],c['source_segment']['label_value'])

if __name__=='__main__':main()
