"""Preserve every rootlet annotation as a separate source-surface candidate."""
from pathlib import Path
import gzip,hashlib,json,struct,sys
import numpy as np,nibabel as nib,skimage
from skimage.measure import marching_cubes
ROOT=Path(__file__).resolve().parents[2];STAGE=ROOT/'.research/anatomy-sources/rootlets';DOC=ROOT/'docs/msk-rootlet-source-review';OUT=ROOT/'output/msk-rootlet-sub-amu02'
sys.path.insert(0,str(ROOT))
from tools.anatomy_sources.check_atlantoaxial_topology import topology


def main():
    acquisition=json.loads((STAGE/'acquisition.json').read_text());records={Path(x['file']).name:x for x in acquisition['files']};folder=STAGE/'sub-amu02';image=nib.load(folder/'sub-amu02_T2w.nii.gz');arrays={};names=['rater1','rater2','rater3','rater4','staple'];OUT.mkdir(parents=True,exist_ok=True);rows=[];manifests={};all_bounds=[]
    for name in names:
        filename=f'sub-amu02_T2w_desc-{name}_label-rootlets_dseg.nii.gz';path=folder/filename;assert hashlib.sha256(path.read_bytes()).hexdigest()==records[filename]['sha256'];n=nib.load(path);assert np.array_equal(n.affine,image.affine) and n.shape==image.shape;raw=np.asanyarray(n.dataobj);assert np.isfinite(raw).all() and np.all(raw==np.rint(raw));arrays[name]=raw.astype(np.uint8)
    support=[]
    for label in range(2,10):
        votes=sum((arrays[name]==label).astype(np.uint8) for name in names[:4]);consensus=arrays['staple']==label;support.append({'label':label,'level':f'C{label}' if label<9 else 'T1','any_rater_voxels':int((votes>0).sum()),'consensus_matches_at_least_two_votes':bool(np.array_equal(consensus,votes>=2)),'unanimous_voxels':int((votes==4).sum()),'three_or_four_rater_voxels':int((votes>=3).sum()),'consensus_voxels_by_vote_count':{str(i):int(np.count_nonzero(consensus&(votes==i))) for i in range(5)}})
    stacked=np.stack([arrays[name] for name in names[:4]]);minimum=np.where(stacked>0,stacked,255).min(0);maximum=stacked.max(0);conflict=(minimum!=255)&(minimum!=maximum)
    for name in names:
        parts={};empty=[]
        for label in range(2,10):
            binary=arrays[name]==label;points=np.argwhere(binary);level=f'C{label}' if label<9 else 'T1'
            if not len(points):empty.append(level);rows.append({'annotation':name,'label':label,'level':level,'status':'no_source_label_voxels','anatomical_absence_inferred':False});continue
            lo=points.min(0)-1;hi=points.max(0)+2;assert np.all(lo>=0) and np.all(hi<=image.shape),'Source-volume edge requires separate handling'
            field=binary[tuple(slice(a,b) for a,b in zip(lo,hi))].astype(np.uint8);assert int(field.sum())==len(points)
            vox,faces,_,_=marching_cubes(field,level=.5,method='lewiner',step_size=1,allow_degenerate=True);vox=vox.astype(float)+lo;world=nib.affines.apply_affine(image.affine,vox);tri=world[faces]-world.mean(0);signed=np.einsum('ij,ij->i',tri[:,0],np.cross(tri[:,1],tri[:,2])).sum()/6
            if signed<0:faces=faces[:,[0,2,1]]
            check=topology(world.tolist(),faces.tolist());tri=world[faces];cross=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);normals=np.zeros_like(world)
            for c in range(3):np.add.at(normals,faces[:,c],cross)
            lengths=np.linalg.norm(normals,axis=1);assert np.all(lengths>0);normals=(normals/lengths[:,None]).astype('<f4');positions=world.astype('<f4');roundoff=float(np.linalg.norm(positions.astype(float)-world,axis=1).max());assert roundoff<1e-4
            encoded=struct.pack('<4sII',b'BP3D',len(world),faces.size)+positions.tobytes()+normals.tobytes()+faces.astype('<u4').tobytes();filename=f'{name}-{level.lower()}.bin.gz';payload=gzip.compress(encoded,mtime=0);(OUT/filename).write_bytes(payload);assert gzip.decompress(payload)==encoded
            ident=name+'-'+level.lower();bounds=[world.min(0).tolist(),world.max(0).tolist()];display=world[:,[0,2,1]]*[-1,1,1];all_bounds.append([display.min(0),display.max(0)])
            colors=['#4d9de0','#ff9a3d','#62bb65','#f06060','#b48bdd','#b58061','#e891c0','#63c9d4'];parts[ident]={'id':ident,'name':level+' dorsal rootlet label','file':filename,'sha256':hashlib.sha256(payload).hexdigest(),'color':colors[label-2],'vertices':len(world),'triangles':len(faces),'bounds':bounds,'source_label':label}
            saved_tri=positions.astype(float)[faces]-positions.astype(float).mean(0);surface_volume=float(np.einsum('ij,ij->i',saved_tri[:,0],np.cross(saved_tri[:,1],saved_tri[:,2])).sum()/6);occupancy_volume=float(len(points)*abs(np.linalg.det(image.affine[:3,:3])))
            rows.append({'annotation':name,'label':label,'level':level,'status':'surface_of_source_label','source_label_voxels':len(points),'source_file_sha256':records[f'sub-amu02_T2w_desc-{name}_label-rootlets_dseg.nii.gz']['sha256'],'mesh_sha256':parts[ident]['sha256'],'vertices':len(world),'triangles':len(faces),'float32_maximum_position_roundoff_mm':roundoff,'label_voxel_occupancy_mm3':occupancy_volume,'rendered_isosurface_volume_mm3':surface_volume,'surface_to_voxel_volume_ratio':surface_volume/occupancy_volume,'topology':check})
        manifests[name]={'dataset':'Spine Generic sub-amu02 · '+name,'source_url':'https://doi.org/10.5281/zenodo.4299140','license':'CC BY 4.0 terms retained; metadata also states CC0','license_url':'https://creativecommons.org/licenses/by/4.0/','coordinate_system':{'basis':'RAS','units':'millimetres','display_basis':'native-ras-to-x-left-y-superior-z-anterior','unit_meters':.001},'parts':parts,'regions':{'cervical':{'title':name+' · annotated dorsal rootlet regions','side':'midline','parts':[{'id':k,'layer':'rootlets'} for k in parts],'layers':[['rootlets','Dorsal rootlet labels']]}},'viewer_notes':['Surfaces follow source voxel labels at isovalue 0.5; annotation limits are not complete anatomical nerve endpoints.','No smoothing, decimation, component removal or fixed-radius nerve fitting.','Levels group dorsal rootlets; individual rootlets and sides are not separately inferred.','Annotation disagreement is not a probability of anatomical correctness.','No annotation for '+', '.join(empty)+'. This is not evidence of anatomical absence.' if empty else 'All eight source level labels are present in this annotation.','Source: Spine Generic / Cohen-Adad and colleagues; rootlet annotations by Mathieu, Schlienger, Valošek and Kowalczyk, described by Valošek et al. (2024), DOI 10.1162/imag_a_00218. Attribution and CC BY 4.0 terms retained.'],'clinical_approval':False,'runtime_promoted':False}
    bounds=np.asarray(all_bounds);lo=bounds[:,0].min(0);hi=bounds[:,1].max(0);margin=.05*np.max(hi-lo);lo-=margin;hi+=margin
    for manifest in manifests.values():manifest['review_display_bounds']=[lo.tolist(),hi.tolist()];manifest['regions']['cervical']['source_up_range']=[float(lo[1]),float(hi[1])]
    (OUT/'manifests.json').write_text(json.dumps(manifests,indent=2)+'\n')
    report={'case':'sub-amu02','method':'Separate 0.5 Lewiner surfaces for each original annotation/level. All foreground voxels and disconnected components retained.','skimage_version':skimage.__version__,'sources':rows,'same_class_rater_support':support,'cross_level_disagreement_voxels':int(conflict.sum()),'review_display_bounds': [lo.tolist(),hi.tolist()],'limits':['A closed label isosurface does not establish anatomical completeness or actual nerve diameter.','The source MRI grid is about 0.8 mm; generated polygon density adds no acquired detail.','Manual and consensus variants remain separate; missing annotations are not fabricated.'],'clinical_approval':False,'runtime_promoted':False};(DOC/'annotation-surface-comparison.json').write_text(json.dumps(report,indent=2)+'\n');print('Source surfaces',sum(r['status']=='surface_of_source_label' for r in rows),'empty annotation entries',len([r for r in rows if r['status']!='surface_of_source_label']));print('Cross-level disagreement voxels',int(conflict.sum()));print('Consensus voxels with no same-class manual support',sum(r['consensus_voxels_by_vote_count']['0'] for r in support))


if __name__=='__main__':main()
