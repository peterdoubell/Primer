#!/usr/bin/env python3
"""Display original matched cine planes without inventing motion, resampling or model registration."""
import argparse,hashlib,io,json,warnings,zipfile
from pathlib import Path
from tools.anatomy_sources.verify_sunnybrook_native_cine import OUT

def render(root):
    import numpy as np,pydicom
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    warnings.filterwarnings('ignore',message='Invalid value for VR UI:.*',category=UserWarning,module='pydicom.valuerep')
    report=json.loads((OUT/'native-cine-linkage-review.json').read_text());rows=report['linked_images'];planes=sorted([r for r in rows if r['label']=='SA6'],key=lambda r:r['frame'])
    if len(planes)!=20:raise ValueError('Matched native cine group missing')
    with zipfile.ZipFile(root/report['source_archive']['file']) as z:
        images=[pydicom.dcmread(io.BytesIO(z.read(r['native']['member']))).pixel_array for r in planes];low,high=np.percentile(np.stack(images),[1,99.5]);fig,axs=plt.subplots(4,5,figsize=(14,12),layout='constrained')
        for ax,row,image in zip(axs.ravel(),planes,images):
            ax.imshow(image,cmap='gray',vmin=low,vmax=high,interpolation='nearest');ax.set_title(f'Model frame {row["frame"]}\nTrigger {row["native"]["trigger_time_ms"]:g} ms',fontsize=9);ax.axis('off')
        fig.suptitle('Sunnybrook SCD0000101: exact model-referenced native SA6 cine frames\nOriginal pixel orientation/window display only; no native samples changed or frames interpolated',fontsize=13)
        fig.savefig(OUT/'native-sa6-20-frame-context.png',dpi=130);plt.close(fig)
        refs=[next(r for r in rows if r['label']==label and r['frame']==frame) for label in ['LA1','LA2','SA3','SA6','SA9','SA12'] for frame in [0,10]];fig,axs=plt.subplots(6,2,figsize=(9,18),layout='constrained')
        for ax,row in zip(axs.ravel(),refs):
            pixels=pydicom.dcmread(io.BytesIO(z.read(row['native']['member']))).pixel_array;ax.imshow(pixels,cmap='gray',vmin=low,vmax=high,interpolation='nearest');ax.set_title(f'{row["label"]}, model frame {row["frame"]}, trigger {row["native"]["trigger_time_ms"]:g} ms',fontsize=9);ax.axis('off')
        fig.suptitle('Native long-/short-axis source correspondence\nPlanes can have different source cycle timings; not one simultaneous volumetric heartbeat',fontsize=12)
        fig.savefig(OUT/'native-plane-phase-context.png',dpi=120);plt.close(fig)
    artifacts=[]
    for filename,selected in [('native-sa6-20-frame-context.png',planes),('native-plane-phase-context.png',refs)]:
        artifacts.append({'file':filename,'sha256':hashlib.sha256((OUT/filename).read_bytes()).hexdigest(),'native_frames':[{'label':r['label'],'frame':r['frame'],'sop_uid':r['sop_uid'],'source_pixel_bytes_sha256':r['native']['original_pixel_bytes_sha256']} for r in selected]})
    (OUT/'native-display-review.json').write_text(json.dumps({'artifacts':artifacts,'display_window_percentiles':[1,99.5],'display_window_values':[float(low),float(high)],'source_pixels_changed':False,'interpolated_frames_or_voxels':False,'model_transform_or_geometry_validated_by_display':False,'clinical_approval':False},indent=2)+'\n');print('Native full 20-frame and plane/phase worksheets rendered without source edits.')
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);render(p.parse_args().source_root)
