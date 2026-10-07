#!/usr/bin/env python3
"""Offline, native-grid paired CT review; do not publish before example rights clearance."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from tools.anatomy_sources.review_hvsmr2_pat7_source import read_nifti

def plot(source_root,proof_dir):
    review=json.loads((proof_dir/'LNCTVSeg-original-example-volume-review.json').read_text())
    arrays={}
    for row in review['original_files']:
        path=source_root/'LNCTVSeg-original-example'/row['file']
        if hashlib.sha256(path.read_bytes()).hexdigest()!=row['source_file_sha256']:raise ValueError('Original source changed')
        arrays[row['file']]=read_nifti(path)[0]
    mask=arrays['lnctvseg0001.nii.gz'];slices=[94,115,123]
    fig,axes=plt.subplots(2,3,figsize=(12,9),facecolor='white')
    for row,suffix in enumerate(['0000','0001']):
        image=arrays[f'lnctvseg0001_{suffix}.nii.gz']
        for col,k in enumerate(slices):
            ax=axes[row,col];ax.imshow(image[:,:,k].T,origin='lower',cmap='gray',vmin=-160,vmax=240,interpolation='nearest')
            for value,color in enumerate(['#ff6b6b','#00d7ff','#f9cf44','#ae85ff','#ff80dc','#7cff78'],1):
                layer=(mask[:,:,k]==value).T
                if layer.any():ax.contour(layer,levels=[.5],colors=[color],linewidths=.6)
            ax.set_title(f'Author {"noncontrast" if row==0 else "contrast-enhanced"} CT; source k={k}',fontsize=10)
            ax.set_xlabel('Original voxel i');ax.set_ylabel('Original voxel j')
    fig.suptitle('Original LNCTVSeg example: six target-region contours, not individual nodes',fontsize=14)
    fig.text(.5,.015,'Native slices, no resampling. Display window -160 to 240 source values; no independent HU/DICOM calibration.\n1.338 × 1.338 × 3 mm sampling; phase, laterality and anatomical interpretation await review.',ha='center',fontsize=9)
    fig.tight_layout(rect=[0,.05,1,.95]);out=source_root/'public-example-derived-review'/'paired-native-CT-review.png';fig.savefig(out,dpi=130);plt.close(fig)
    evidence={'file':out.name,'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'source_k_indices':slices,'original_indices_not_interpolated':True,'window_source_values':[-160,240],'mask_contours':'Original six source labels; no relabelling','rights_cleared_for_publication':False,'anatomical_review_complete':False,'runtime_promoted':False}
    (proof_dir/'paired-native-CT-review.json').write_text(json.dumps(evidence,indent=2)+'\n');print(out)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);p.add_argument('--proof-dir',type=Path,required=True);a=p.parse_args();plot(a.source_root,a.proof_dir)
