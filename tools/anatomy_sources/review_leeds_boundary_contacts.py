#!/usr/bin/env python3
"""Locate threshold contacts without treating attenuation as a tissue label."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--volume',type=Path,required=True)
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
m=json.loads((args.volume/'native-volume.json').read_text());path=args.volume/m['array_file'];a=np.load(path,mmap_mode='r',allow_pickle=False)
if a.dtype!=np.dtype('<i2') or not a.flags.c_contiguous or list(a.shape)!=m['geometry']['shape']:raise ValueError('Unexpected native layout')
cal={(r['rescale_slope'],r['rescale_intercept'],r['rescale_units']['units']) for r in m['frame_records']}
if len(cal)!=1 or next(iter(cal))[2]!='HU':raise ValueError('Explicit per-frame unit handling required')
slope,intercept,_=next(iter(cal));affine=np.array(m['geometry']['index_to_dicom_lps_mm']);digest=hashlib.sha256()
with path.open('rb') as source:digest.update(source.read(a.offset))
contacts=[];planes={}
for k in range(a.shape[0]):
 raw=np.array(a[k],copy=True);digest.update(raw.tobytes());values=raw[:,-1].astype(np.float64)*slope+intercept
 rows=np.flatnonzero(values>1000)
 if len(rows):
  planes[k]=raw
  for row in rows:
   index=[k,int(row),a.shape[2]-1];world=affine@[*index,1]
   contacts.append({'index_slice_row_column':index,'dicom_lps_mm':world[:3].tolist(),'stored_value':int(raw[row,-1]),'rescaled_hu':float(values[row]),'source_member':m['frame_records'][k]['member']})
 if (k+1)%256==0:print(f'Inspected {k+1}/{a.shape[0]} complete source planes',flush=True)
if digest.hexdigest()!=m['array_sha256']:raise ValueError('Native source hash mismatch')
if not contacts:raise ValueError('Expected boundary contacts not reproduced')
fig,axes=plt.subplots(len(contacts),2,figsize=(10,3*len(contacts)),squeeze=False,constrained_layout=True)
for row,c in enumerate(contacts):
 k,j,i=c['index_slice_row_column'];raw=planes[k];values=raw.astype(np.float32)*slope+intercept
 axes[row,0].imshow(values,cmap='gray',vmin=-400,vmax=2500,interpolation='nearest');axes[row,0].plot(i,j,'rx',markersize=9);axes[row,0].set_title(f'Source slice {k}; contact at row {j}, column {i}')
 low=max(0,j-40);high=min(raw.shape[0],j+41);left=max(0,i-100)
 axes[row,1].imshow(values[low:high,left:],cmap='gray',vmin=-400,vmax=2500,interpolation='nearest',extent=[left-.5,i+.5,high-.5,low-.5]);axes[row,1].plot(i,j,'rx',markersize=9);axes[row,1].set_title(f'Native edge neighbourhood: {c["rescaled_hu"]:.1f} HU')
figure=args.output/'side-boundary-contacts.png';fig.savefig(figure,dpi=150);plt.close(fig)
result={'source_array_sha256':digest.hexdigest(),'threshold_hu':1000,'face':'final native column','contacts':contacts,'source_planes_sha256':{str(k):hashlib.sha256(p.tobytes()).hexdigest() for k,p in planes.items()},'figure':str(figure),'figure_sha256':hashlib.sha256(figure.read_bytes()).hexdigest(),'qualification':'Red marks are numerical QA overlays. Material identity and anatomical completeness require visual/source review; these are not bone masks.','clinical_approval':False,'runtime_promoted':False}
(args.output/'side-boundary-contacts.json').write_text(json.dumps(result,indent=2)+'\n');print('Contacts:',len(contacts),flush=True)
