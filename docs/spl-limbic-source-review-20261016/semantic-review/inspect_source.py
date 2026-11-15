"""Independent label naming/component/plane review; not anatomical approval."""
from pathlib import Path
import gzip,hashlib,json,xml.etree.ElementTree as ET
import numpy as np
from scipy import ndimage
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
ASSETS=ROOT/'web/anatomy/spl-nac-limbic'
manifest=json.loads((ASSETS/'manifest.json').read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
labrow=manifest['labelVolume'];labels=np.frombuffer(gzip.decompress((ASSETS/labrow['file']).read_bytes()),dtype=labrow['dtype']).reshape(labrow['shape'],order='F');L=np.asarray(labrow['voxelToRAS']);Li=np.linalg.inv(L)
vols={k:np.frombuffer(gzip.decompress((ASSETS/row['file']).read_bytes()),dtype=row['dtype']).reshape(row['shape'],order='F') for k,row in manifest['volumes'].items()}
assert all(np.isfinite(array).all() for array in vols.values())
source=ROOT/'docs/spl-limbic-source-review-20261016/source-evidence'
lut=gzip.decompress((source/'slicer--colortables--hncma-atlas-lut.ctbl.gz').read_bytes()).decode()
lutrows={int(line.split()[0]):line.split()[1:] for line in lut.splitlines() if line.strip() and not line.startswith('#')}
meta=gzip.decompress((source/'labelinfo--brain-atlas-labels-with-metadata.tsv.gz').read_bytes()).decode()
metarows={line.split('\t')[0]:line for line in meta.splitlines() if line.strip()}
scene=ET.fromstring(gzip.decompress((source/'slicer--brain-atlas.mrml.gz').read_bytes()))
models=[n.attrib for n in scene if n.tag=='Model'];storages={n.attrib['id']:n.attrib for n in scene if n.tag=='ModelStorage'}
def apply(A,points):
 return np.stack([sum(points[...,j]*A[k,j] for j in range(3))+A[k,3] for k in range(3)],axis=-1)
def world(points):return apply(L,points)
def getplane(contrast,axis,index):
 row=manifest['volumes'][contrast];A=np.asarray(row['voxelToRAS']);shape=row['shape'];img=vols[contrast]
 if axis=='axial':
  i,k=np.meshgrid(np.arange(shape[0]),np.arange(shape[2]),indexing='ij');native=np.stack((i,np.full_like(i,index),k),axis=-1);plane=img[:,index,:];extent=[78,-78,-108,108];xy=[0,1]
 elif axis=='coronal':
  j,k=np.meshgrid(np.arange(shape[1]),np.arange(shape[2]),indexing='ij');native=np.stack((np.full_like(j,index),j,k),axis=-1);plane=img[index,:,:];extent=[78,-78,-120,120];xy=[0,2]
 else:
  j,i=np.meshgrid(np.arange(shape[1]),np.arange(shape[0]),indexing='ij');native=np.stack((i,j,np.full_like(i,index)),axis=-1);plane=img[:,:,index].T;extent=[108,-108,-120,120];xy=[1,2]
 ras=apply(A,native);labelijk=np.floor(apply(Li,ras)+.5).astype(int);valid=np.all((labelijk>=0)&(labelijk<np.asarray(labels.shape)),axis=-1);sampled=np.zeros(plane.shape,dtype=np.int16);sampled[valid]=labels[tuple(labelijk[valid].T)]
 return plane,sampled,extent,xy
records=[]
for row in manifest['labels']:
 code=row['code'];ijk=np.argwhere(labels==code);ras=world(ijk);lo=ijk.min(0);hi=ijk.max(0)+1;crop=labels[tuple(slice(a,b) for a,b in zip(lo,hi))]==code;cc,n=ndimage.label(crop,np.ones((3,3,3),dtype=np.uint8));components=[]
 for c in range(1,n+1):
  pts=np.argwhere(cc==c)+lo;w=world(pts);components.append({'voxels':len(pts),'centroid_RAS':w.mean(0).tolist(),'bounds_RAS':[w.min(0).tolist(),w.max(0).tolist()]})
 components.sort(key=lambda x:x['voxels'],reverse=True)
 centroid=ijk.mean(0);focus=ijk[np.argmin(np.sum((ijk-centroid)**2,axis=1))];focusras=world(focus)
 matching=[m for m in models if m.get('name')=='Model_'+str(code)+'_'+row['sourceName']]
 assert len(matching)==1 and lutrows[code][0]==row['sourceName']
 model=matching[0];storage=storages[model['storageNodeRef']]
 rec={'code':code,'name':row['name'],'lut_name':lutrows[code][0],'source_metadata_row':metarows.get(str(code)),'source_model_name':model['name'],'source_storage_file':storage.get('fileName'),'source_parent_transform':model.get('transformNodeRef'),'voxel_count':len(ijk),'centroid_RAS':ras.mean(0).tolist(),'center_bounds_RAS':[ras.min(0).tolist(),ras.max(0).tolist()],'components_26':components,'focus_label_ijk':focus.tolist(),'focus_RAS':focusras.tolist(),'panels':[]}
 fig,axes=plt.subplots(2,3,figsize=(11,7.5),dpi=140)
 for rr,contrast in enumerate(['T1','T2']):
  A=np.asarray(manifest['volumes'][contrast]['voxelToRAS']);native=np.rint(np.linalg.inv(A)@np.r_[focusras,1])[:3].astype(int)
  for col,axis in enumerate(['coronal','axial','sagittal']):
   index=int(native[{'coronal':0,'axial':1,'sagittal':2}[axis]]);image,overlay,extent,xy=getplane(contrast,axis,index)
   ax=axes[rr,col];ax.imshow(image,cmap='gray',vmin=0,vmax=1100,origin='upper',extent=extent,interpolation='nearest');rgba=np.zeros((*image.shape,4));mask=overlay==code;rgba[mask,:3]=np.asarray(row['color'])/255;rgba[mask,3]=.55;ax.imshow(rgba,origin='upper',extent=extent,interpolation='nearest')
   cx,cy=focusras[xy];span=45 if code in [3005,3007] else 30;ax.set_xlim(cx+span,cx-span);ax.set_ylim(cy-span,cy+span);ax.set_aspect('equal');ax.set_title(f'{contrast} {axis} · native index {index}',fontsize=10);ax.set_xlabel(('RAS x: R ← → L' if axis!='sagittal' else 'RAS y: A ← → P')+' (mm)',fontsize=8);ax.set_ylabel(('RAS y (mm)' if axis=='axial' else 'RAS z (mm)'),fontsize=8);ax.tick_params(labelsize=7)
   rec['panels'].append({'contrast':contrast,'plane':axis,'native_index':index,'display_window':[0,1100],'selected_label_pixels':int(mask.sum()),'source_grid_unchanged':True})
 fig.suptitle(f'{code}: {row["name"]} — original MRI sample planes with source-label overlay\nSource-coordinate overlays; tissue boundary accuracy remains unverified.',fontsize=11);fig.tight_layout(rect=[0,0,1,.93]);fig.savefig(OUT/f'label-{code}-planes.png');plt.close(fig);records.append(rec)
# Explicitly show the isolated left-fornix component responsible for the long distance.
row=next(r for r in records if r['code']==3007)
for ix,component in enumerate(row['components_26'][1:],1):
 focusras=np.asarray(component['centroid_RAS']);fig,axes=plt.subplots(1,3,figsize=(11,3.7),dpi=140);A=np.asarray(manifest['volumes']['T1']['voxelToRAS']);native=np.rint(np.linalg.inv(A)@np.r_[focusras,1])[:3].astype(int)
 for ax,axis in zip(axes,['coronal','axial','sagittal']):
  index=int(native[{'coronal':0,'axial':1,'sagittal':2}[axis]]);image,overlay,extent,xy=getplane('T1',axis,index);ax.imshow(image,cmap='gray',vmin=0,vmax=1100,origin='upper',extent=extent,interpolation='nearest');rgba=np.zeros((*image.shape,4));rgba[overlay==3007]=[0,1,1,.7];ax.imshow(rgba,origin='upper',extent=extent,interpolation='nearest');cx,cy=focusras[xy];ax.set_xlim(cx+20,cx-20);ax.set_ylim(cy-20,cy+20);ax.plot(cx,cy,'+',color='red',markersize=12);ax.set_title(f'T1 {axis} · slice {index}',fontsize=10);ax.tick_params(labelsize=8)
 fig.suptitle(f'Preserved left-fornix component {ix+1}: {component["voxels"]} voxel at RAS {focusras.tolist()} mm\nRed cross locates the component; no biological-island or disease interpretation is established.',fontsize=10);fig.tight_layout(rect=[0,0,1,.86]);fig.savefig(OUT/f'fornix-island-{ix}-planes.png');plt.close(fig)
output={'scope':'Independent source naming, components and gross-location review; not clinical or boundary validation','source_commit':manifest['sourceCommit'],'manifest_sha256':sha(ASSETS/'manifest.json'),'records':records,'MRI_windows':'Both source contrasts displayed 0–1100 stored arbitrary intensity units; no intensity comparison across contrasts or quantitative tissue inference.','laterality_scope':'Source RAS coordinates and original label names; no patient registration.','source_parent_transform_count':sum(bool(r['source_parent_transform']) for r in records),'clinical_approval':False}
(OUT/'structure-audit.json').write_text(json.dumps(output,indent=2)+'\n')
print(json.dumps({'structures':len(records),'figure_count':len(list(OUT.glob('*.png'))),'naming_matches':True,'parent_transforms':output['source_parent_transform_count']}))
