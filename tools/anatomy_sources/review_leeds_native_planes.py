#!/usr/bin/env python3
"""Review the preserved CT array in source coordinates; no segmentation claims."""
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
manifest=json.loads((args.volume/'native-volume.json').read_text());path=args.volume/manifest['array_file']
h=hashlib.sha256()
with path.open('rb') as stream:
 for block in iter(lambda:stream.read(8*1024*1024),b''):h.update(block)
if h.hexdigest()!=manifest['array_sha256']:raise ValueError('Preserved volume changed')
a=np.load(path,mmap_mode='r',allow_pickle=False)
if list(a.shape)!=manifest['geometry']['shape'] or a.dtype!=np.dtype('<i2'):raise ValueError('Native shape/type mismatch')
calibrations={(f['rescale_slope'],f['rescale_intercept'],f['rescale_units']['units']) for f in manifest['frame_records']}
if len(calibrations)!=1:raise ValueError('This review requires explicit handling of varying calibration')
slope,intercept,unit=next(iter(calibrations))
if unit!='HU':raise ValueError('HU windowing requires established source-unit semantics')
affine=np.array(manifest['geometry']['index_to_dicom_lps_mm']);spacing=np.linalg.norm(affine[:3,:3],axis=0)
records=[];fig,axes=plt.subplots(3,3,figsize=(13,12),constrained_layout=True)
for axis in range(3):
 other=[i for i in range(3) if i!=axis]
 for col,fraction in enumerate((.25,.5,.75)):
  index=round((a.shape[axis]-1)*fraction);selector=[slice(None)]*3;selector[axis]=index;raw=np.asarray(a[tuple(selector)])
  values=raw.astype(np.float32)*slope+intercept
  view=axes[axis,col];view.imshow(values,cmap='gray',vmin=-400,vmax=2500,origin='upper',aspect=spacing[other[0]]/spacing[other[1]],interpolation='nearest')
  view.set_title(f'Source axis {axis}, index {index}');view.set_xlabel(f'Native axis {other[1]} index');view.set_ylabel(f'Native axis {other[0]} index')
  records.append(dict(axis=axis,index=index,plane_shape=list(raw.shape),source_axes=other,raw_plane_sha256=hashlib.sha256(raw.tobytes()).hexdigest(),display_window_hu=[-400,2500],display_interpolation='nearest',native_voxels_modified=False))
fig.suptitle('Leeds donor 1: native source planes\nDICOM coordinates retained; anatomical orientation and structure identity not yet independently verified',fontsize=13)
figure=args.output/'native-plane-grid.png';fig.savefig(figure,dpi=160);plt.close(fig)
boundaries=[]
for axis in range(3):
 for index in (0,a.shape[axis]-1):
  selector=[slice(None)]*3;selector[axis]=index;raw=np.asarray(a[tuple(selector)]);values=raw.astype(np.float32)*slope+intercept
  boundaries.append(dict(axis=axis,index=index,shape=list(raw.shape),raw_sha256=hashlib.sha256(raw.tobytes()).hexdigest(),rescaled_min=float(values.min()),rescaled_max=float(values.max()),threshold_counts={str(t):int(np.count_nonzero(values>t)) for t in (300,600,1000)}))
report=dict(source_array_sha256=manifest['array_sha256'],shape=list(a.shape),source_spacing_mm=spacing.tolist(),index_to_dicom_lps_mm=affine.tolist(),planes=records,boundaries=boundaries,figure=str(figure),figure_sha256=hashlib.sha256(figure.read_bytes()).hexdigest(),qualification='Boundary thresholds are numerical screening probes, not validated bone masks or proof of anatomical completeness. No surfaces, caps, named structures or clinical approvals are inferred.',clinical_approval=False,runtime_promoted=False)
(args.output/'native-plane-review.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(boundaries,indent=2),flush=True)
