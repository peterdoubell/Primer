#!/usr/bin/env python3
"""Stage a distinct MRI-derived knee provider from native CC0 STL surfaces.

No geometry decimation, smoothing, anatomical fitting, or publication. Source
triangle corners and their original STL facet normals are preserved exactly.
"""
import collections,hashlib,io,json,pathlib,re,struct,zipfile
import numpy as np
import trimesh

CACHE=pathlib.Path('/tmp/primer-msk-sources/high-fidelity')
OUT=CACHE/'malaya-knee';OUT.mkdir(exist_ok=True)
SELECT={
 'Bone_Femur':('Femur','bone'), 'Bone_Tibia':('Tibia','bone'),
 'Bone_Fibula':('Fibula','bone'), 'Bone_Patella':('Patella','bone'),
 'Cartilage_Femur Distal':('Distal femoral cartilage','cartilage'),
 'Cartilage_Patella':('Patellar cartilage','cartilage'),
 'Cartilage_Tibia':('Tibial cartilage','cartilage'),
 'Ligament_ACL':('Anterior cruciate ligament','ligament'),
 'Ligament_PCL':('Posterior cruciate ligament','ligament'),
 'Ligament_MCL':('Medial collateral ligament','ligament'),
 'Ligament_LCL':('Lateral collateral ligament','ligament'),
 'Ligament_Patella':('Patellar ligament','ligament'),
 'Meniscus_Knee':('Knee meniscus (source combined object)','meniscus'),
 'Tendon_Quadriceps':('Quadriceps tendon','tendon'),
 'Muscle_Popliteus':('Popliteus','muscle'),
 'Muscle_Gastrocnemius Medial':('Medial gastrocnemius','muscle'),
 'Muscle_Gastrocnemius Lateral':('Lateral gastrocnemius','muscle'),
 'Muscle_Semimembranosus':('Semimembranosus','muscle'),
 'Muscle_Semitendinosus':('Semitendinosus','muscle'),
 'Muscle_Bicep Femoris Longhead':('Biceps femoris long head','muscle'),
 'Muscle_Bicep Femoris Shorthead':('Biceps femoris short head','muscle'),
 'Muscle_Sartorius':('Sartorius','muscle'),
 'Muscle_Gracilis':('Gracilis','muscle'),
 'Muscle_Rectus Femoris':('Rectus femoris','muscle'),
 'Muscle_Vastus Medialis':('Vastus medialis','muscle'),
 'Muscle_Vastus Intermedius':('Vastus intermedius','muscle'),
 'Muscle_Vastus Lateralis':('Vastus lateralis','muscle'),
 'Muscle_Soleus':('Soleus','muscle'),
}

def stl(data):
 assert data[:80].startswith(b'3D Slicer output. SPACE=LPS')
 count=struct.unpack_from('<I',data,80)[0]
 assert len(data)==84+count*50
 dtype=np.dtype([('normal','<f4',(3,)),('vertices','<f4',(3,3)),('attribute','<u2')])
 records=np.frombuffer(data,dtype=dtype,count=count,offset=84)
 return records['vertices'],records['normal'],count

def sha(data):return hashlib.sha256(data).hexdigest()

def main(region='knee', selection=None, output=None, focus_names=None, title=None):
 if region not in {'knee','ankle'}:raise ValueError('Unreviewed region selection')
 selection=SELECT if selection is None else selection
 output_directory=OUT if output is None else pathlib.Path(output)
 output_directory.mkdir(parents=True,exist_ok=True)
 archive=CACHE/'um-final-model-stl.zip';assert hashlib.md5(archive.read_bytes()).hexdigest()=='d7f066d2fd3fc21c21f64ad3d5a985fd'
 metadata=json.loads((CACHE/'um-dataset.json').read_text());v=metadata['data']['latestVersion'];assert v['license']['name']=='CC0 1.0'
 parts={};all_inventory=[];omission_evidence=[]
 with zipfile.ZipFile(archive) as z:
  for member in z.infolist():
   if not member.filename.endswith('.stl'):continue
   data=z.read(member);tri,normals,nt=stl(data);positions=tri.reshape(-1,3)
   key=pathlib.Path(member.filename).stem.removeprefix('Segmentation_').strip()
   info={'source_name':key,'source_member':member.filename,'source_sha256':sha(data),'source_bytes':len(data),'triangles':nt,'bounds':[positions.min(0).tolist(),positions.max(0).tolist()],'source_header':data[:80].rstrip(b'\0').decode('ascii')}
   assert np.isfinite(positions).all() and np.isfinite(normals).all()
   all_inventory.append(info)
   if key not in selection:continue
   label,layer=selection[key];identifier='um-'+region+'-'+re.sub('[^a-z0-9]+','-',key.lower()).strip('-')
   stlfile=output_directory/(identifier+'.stl');stlfile.write_bytes(data)
   # Omit only provably empty facets; never filter components by size/volume.
   source_triangles=nt;original_tri=tri;original_normals=normals
   cross64=np.cross(tri[:,1].astype('f8')-tri[:,0],tri[:,2].astype('f8')-tri[:,0])
   repeated=np.all(tri[:,0]==tri[:,1],1)|np.all(tri[:,1]==tri[:,2],1)|np.all(tri[:,0]==tri[:,2],1)
   eligible=np.all(cross64==0,axis=1)&repeated
   omit=eligible  # Explicit authorization: exactly empty repeated-vertex facets only.
   omitted=np.flatnonzero(omit).tolist();tri=tri[~omit];normals=normals[~omit];nt=len(tri);positions=tri.reshape(-1,3)
   if omitted:omission_evidence.append({'id':identifier,'source_member':member.filename,'source_sha256':info['source_sha256'],'source_triangle_count':source_triangles,'omitted_source_facet_indices':omitted,'reason':'Exactly zero area in float64 evaluation of source float32 positions, with repeated vertices. No anatomical surface removed.'})
   # Equal position/normal pairs can be indexed without changing retained facets.
   source_normals=np.repeat(normals,3,axis=0)
   rows=np.concatenate([positions,source_normals],axis=1)
   unique,inverse=np.unique(rows,axis=0,return_inverse=True)
   p=unique[:,:3].astype('<f4');n=unique[:,3:].astype('<f4');ix=inverse.astype('<u4')
   output=struct.pack('<4sII',b'BP3D',len(p),len(ix))+p.tobytes()+n.tobytes()+ix.tobytes()
   file=output_directory/(identifier+'.bin');file.write_bytes(output)
   # Exact-coordinate welding is analysis only; it is not applied to the export.
   welded,vertex_map=np.unique(positions,axis=0,return_inverse=True)
   mesh=trimesh.Trimesh(vertices=welded,faces=vertex_map.reshape(-1,3),process=False)
   parents=list(range(len(welded)))
   def find(i):
    while parents[i]!=i:parents[i]=parents[parents[i]];i=parents[i]
    return i
   for a,b in mesh.edges_unique:
    ra,rb=find(int(a)),find(int(b))
    if ra!=rb:parents[rb]=ra
   component_counts=collections.Counter(find(int(f[0])) for f in mesh.faces)

   cross=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);areas=np.linalg.norm(cross,axis=1)
   norms=np.linalg.norm(normals,axis=1)
   info.update({'detected_exact_empty_facets_not_omitted':np.flatnonzero(eligible&~omit).tolist(),'source_triangles':source_triangles,'triangles':nt,'omitted_source_facet_indices':omitted,'source_bounds_including_empty_facets':info['bounds'],'bounds':[positions.min(0).tolist(),positions.max(0).tolist()],'id':identifier,'name':label,'layer':layer,'regions':['knee'],'file':str(file),'stl_file':str(stlfile),'bytes':len(output),'sha256':sha(output),'export_vertices':len(p),'source_unique_positions':len(welded),'normals_preserved_exactly':True,'geometry_transform':'identity; native LPS positions retained','world_transform_columns':[[1,0,0],[0,1,0],[0,0,1],[0,0,0]],'component_count':len(component_counts),'component_triangles':sorted(component_counts.values(),reverse=True),'watertight':bool(mesh.is_watertight),'winding_consistent':bool(mesh.is_winding_consistent),'volume_native_units_cubed':float(mesh.volume),'degenerate_triangles':int((areas<1e-10).sum()),'normal_length_min':float(norms.min()),'normal_length_max':float(norms.max()),'license':'CC0 1.0'})
   parts[identifier]=info
 assert len(parts)==len(selection),(len(parts),len(selection))
 for part in parts.values():part['regions']=[region]
 focus=[p for p in parts.values() if p['source_name'] in focus_names] if focus_names else [p for p in parts.values() if p['layer'] in {'cartilage','meniscus','ligament'}]
 if not focus:raise ValueError('No source objects define the regional focus')
 bounds=[[min(p['bounds'][0][a] for p in focus) for a in range(3)],[max(p['bounds'][1][a] for p in focus) for a in range(3)]]
 result={'schema_version':1,'status':'research candidate; not clinically approved','dataset':'Universiti Malaya MRI-derived lower extremity, 2026','provider':'malaya-mri','source_doi':'10.22452/RD/5T6TZ7','source_url':'https://researchdata.um.edu.my/dataset.xhtml?persistentId=doi:10.22452/RD/5T6TZ7','source_datafile_url':'https://researchdata.um.edu.my/api/access/datafile/596','source_archive_sha256':sha(archive.read_bytes()),'license':'CC0 1.0','license_url':'https://creativecommons.org/publicdomain/zero/1.0/','attribution':'Jeevaraaj N Vivekanandan; Juliana Binti Usman (2026), A Three-Dimensional Lower Extremity Musculoskeletal Geometry Model of An Asian Male, Universiti Malaya Research Data Repository, doi:10.22452/RD/5T6TZ7.','sampling_limits':{'segmentation_grid_mm':[1.1538461446761996,1.1538461446761996,1.199999956403474],'paired_T2_FS_exported_grid_mm':[1.0714285373687997,1.0714285373687997,1.1000000346790628],'effective_spatial_resolution':'Not established by the STL facet count or exported voxel grid.','author_processing':'MRI semi-automatic segmentation, opening/closing/median and joint smoothing, then surface export.'},'author_review_claim':{'statement':'The dataset README reports inspection by a radiologist and radiographer at Universiti Malaya Medical Centre and acknowledges residual inaccuracies and omitted small structures.','evidence_file':str(CACHE/'um-readme.txt'),'evidence_sha256':sha((CACHE/'um-readme.txt').read_bytes()),'independent_clinical_approval':False},'coordinate_system':{'basis':'LPS','x_positive':'patient left','y_positive':'posterior','z_positive':'superior','basis_evidence':'Every native STL header explicitly contains SPACE=LPS','units':'pending registration metadata verification','registration':'Identity: all geometries from the same final segmented MRI model; no registration to another atlas','display_basis':'[x,z,-y] is a proper rigid basis conversion to patient-left/superior/anterior'},'adaptations':'Converted retained native STL triangle corners and facet normals to indexed binary. Only exactly zero-area repeated-vertex facets omitted, with source facet indices retained in evidence; now-unused render vertices dropped. Equal position/normal pairs deduplicated exactly. All nonzero-area components preserved. No smoothing, decimation, spatial fitting or synthetic anatomy.','parts':parts,'regions':{'knee':{'title':'MRI-derived right knee','side':'right','parts':list(parts),'focus_bounds':bounds,'focus_bounds_source_objects':[p['source_name'] for p in focus]}},'limitations':['Single adult male right lower-extremity segmentation, not a generic population atlas.','The source meniscus STL is one named object; medial and lateral surfaces are not source-labelled separately.','Minor ligaments, tendons and some intrinsic foot muscles were explicitly omitted by the authors.','Author-reported radiologist/radiographer inspection is not independent clinical certification of these exported surfaces.'],'clinical_image_pair':{'available':True,'source_datafile':595,'member':'Final model segmentation/19 RT T2 FS spc_SAG_iso (KNEE).nrrd','registration_status':'Source file available; header correspondence verification pending'}}
 region_record=result['regions'].pop('knee');region_record['title']=title or ('MRI-derived right '+region)
 result['regions']={region:region_record}
 if region=='ankle':
  result['sampling_limits'].pop('paired_T2_FS_exported_grid_mm',None)
  result['clinical_image_pair']={'available':False,'source_datafile':595,'registration_status':'Source segmentation is available; an ankle-specific imaging export has not been validated or published.'}
  result['limitations']=['Single adult male right lower-extremity segmentation, not a generic population atlas.','This selection contains bones, a separately segmented Achilles tendon and source muscle units. It has no separate ankle cartilage, ankle ligament, nerve, vascular or bursal segmentation.','Source muscle units cannot prove a separately delineated distal tendon or tendon sheath.','Author-reported radiologist/radiographer inspection is not independent clinical certification of these exported surfaces.']
 evidence_bytes=(json.dumps(omission_evidence,indent=2)+'\n').encode();(output_directory/'omitted-empty-facets.json').write_bytes(evidence_bytes)
 result['omission_evidence']={'file':str(output_directory/'omitted-empty-facets.json'),'sha256':sha(evidence_bytes),'total_facets':sum(len(p['omitted_source_facet_indices']) for p in parts.values())}
 for part in parts.values():part['omission_evidence_sha256']=sha(evidence_bytes)
 (output_directory/'manifest.json').write_text(json.dumps(result,indent=2)+'\n')
 (CACHE/'um-all-stl-inventory.json').write_text(json.dumps(all_inventory,indent=2)+'\n')
 print('NativeSTL count',len(all_inventory),region+' objects',len(parts),'native triangles',sum(p['triangles'] for p in parts.values()),'binary bytes',sum(p['bytes'] for p in parts.values()))
 for p in parts.values():print(p['name'],p['triangles'],'components',p['component_count'],'watertight',p['watertight'],'degenerate',p['degenerate_triangles'])

if __name__=='__main__':main()
