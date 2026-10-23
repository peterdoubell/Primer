"""Inspect supplied atlas intensities, categorical overlays and full mesh geometry."""
from pathlib import Path
import zipfile,gzip,io,json,struct,hashlib
import numpy as np,nibabel as nib
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'visual-review';OUT.mkdir(exist_ok=True)
source=json.loads((ROOT/'holiatlas-label-review.json').read_text());boundary=json.loads((ROOT/'boundaries/boundary-proof.json').read_text());codes=[60,61,80,81,102,103];metadata={'scope':'Selected native source planes and complete cell meshes; no clinical approval or full 332-class anatomical review','sourceContrastMeaning':{'T1w_average.nii.gz':'Processed population T1w template','T2w_average.nii.gz':'Processed population T2w template','WMn_average.nii.gz':'Population template of source-author synthesized WMn-like contrast; not acquired WMn'},'cases':[],'volumes':{}}
with zipfile.ZipFile(ROOT/'atlas_v1.0.zip') as z:
 raw=gzip.decompress(z.read('substructure_atlas.nii.gz'));header=nib.Nifti1Header.from_fileobj(io.BytesIO(raw[:352]));labels=np.frombuffer(raw,offset=int(header['vox_offset']),dtype=header.get_data_dtype()).reshape(header.get_data_shape(),order='F');affine=header.get_sform();volumes={};windows={}
 for name in metadata['sourceContrastMeaning']:
  rawMRI=gzip.decompress(z.read(name));h=nib.Nifti1Header.from_fileobj(io.BytesIO(rawMRI[:352]));data=np.frombuffer(rawMRI,offset=int(h['vox_offset']),dtype=h.get_data_dtype()).reshape(h.get_data_shape(),order='F');assert np.isfinite(data).all() and np.array_equal(h.get_sform(),affine) and data.shape==labels.shape;volumes[name]=data;positive=data[data>0];windows[name]=np.percentile(positive,[.5,99.5]).tolist();metadata['volumes'][name]={'sha256':hashlib.sha256(rawMRI).hexdigest(),'allVoxelsFinite':True,'gridAndSformExactlyEqualToLabels':True,'displayWindow':windows[name],'meaning':metadata['sourceContrastMeaning'][name]}
 for code in codes:
  row=next(r for r in boundary['rows'] if r['code']==code);cells=np.argwhere(labels==code);centroid=cells.mean(0);chosen=cells[np.argmin(np.sum((cells-centroid)**2,axis=1))];fig=plt.figure(figsize=(12,14),layout='constrained');world=affine@np.r_[chosen,1];fig.suptitle(row['sourceName']+f' — code {code}, {row["sourceVoxels"]} source cells\nCSF territory from a processed population atlas; not a sulcal centre-line',fontsize=12)
  for r,(name,data) in enumerate(volumes.items()):
   for c,axis in enumerate([2,1,0]):
    ax=fig.add_subplot(4,3,r*3+c+1);remaining=[k for k in range(3) if k!=axis];slices=[slice(max(0,int(chosen[k])-60),min(labels.shape[k],int(chosen[k])+61)) for k in range(3)];slices[axis]=int(chosen[axis]);image=data[tuple(slices)].T;mask=(labels[tuple(slices)]==code).T;extent=[affine[remaining[0],3]+.5*(slices[remaining[0]].start-.5),affine[remaining[0],3]+.5*(slices[remaining[0]].stop-.5),affine[remaining[1],3]+.5*(slices[remaining[1]].start-.5),affine[remaining[1],3]+.5*(slices[remaining[1]].stop-.5)];ax.imshow(image,origin='lower',extent=extent,cmap='gray',vmin=windows[name][0],vmax=windows[name][1],interpolation='nearest');rgba=np.zeros((*mask.shape,4));rgba[mask]=[0,1,1,.55];ax.imshow(rgba,origin='lower',extent=extent,interpolation='nearest');ax.set_title(('T1 template' if r==0 else 'T2 template' if r==1 else 'Synthesized WMn-like template')+' · '+['axial','coronal','sagittal'][c],fontsize=9);ax.set_xlabel(['R','A','S'][remaining[0]]+' coordinate (mm)');ax.set_ylabel(['R','A','S'][remaining[1]]+' coordinate (mm)')
  rawMesh=gzip.decompress((ROOT/'boundaries'/row['mesh']['file']).read_bytes());_,V,T,_=struct.unpack_from('<4sIII',rawMesh);p=np.frombuffer(rawMesh,dtype='<f4',count=3*V,offset=16).reshape(-1,3);tri=np.frombuffer(rawMesh,dtype='<u4',count=3*T,offset=16+12*V).reshape(-1,3)
  for c,azim in enumerate([-90,0,90]):
   ax=fig.add_subplot(4,3,10+c,projection='3d');ax.add_collection3d(Poly3DCollection(p[tri],facecolor='#2296a1',edgecolor='none',linewidth=0,rasterized=True));minimum=p.min(0);maximum=p.max(0);center=(minimum+maximum)/2;span=max(maximum-minimum)*.55
   for k,setter in enumerate([ax.set_xlim,ax.set_ylim,ax.set_zlim]):setter(center[k]-span,center[k]+span)
   ax.set_box_aspect([1,1,1]);ax.view_init(elev=15,azim=azim);ax.set_xlabel('R (mm)');ax.set_ylabel('A (mm)');ax.set_zlabel('S (mm)');ax.set_title('All source components · azimuth '+str(azim)+'°',fontsize=9)
  name=f'class-{code}.png';fig.savefig(OUT/name,dpi=130);plt.close(fig);metadata['cases'].append({'code':code,'sourceName':row['sourceName'],'voxel':chosen.tolist(),'worldCoordinate':world[:3].tolist(),'planeWindowRadiusMM':30,'sourceVoxels':row['sourceVoxels'],'triangles':T,'allMeshTrianglesRendered':True,'file':name});print('Rendered',code,flush=True)
(OUT/'review.json').write_text(json.dumps(metadata,indent=2)+'\n')
