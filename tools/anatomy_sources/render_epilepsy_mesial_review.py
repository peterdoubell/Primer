"""Scientific review panels from verified native arrays; never generated anatomy."""
from pathlib import Path
import json,hashlib
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from audit_epilepsy_mesial_sources import SOURCE,OUT,decoded,transform,sha,MANIFEST_SHA256

def main():
    raw=(SOURCE/'manifest.json').read_bytes();assert sha(raw)==MANIFEST_SHA256
    m=json.loads(raw);anchors=json.loads((OUT/'mesial-source-anchors.json').read_bytes());assert anchors['manifestSHA256']==MANIFEST_SHA256
    lv=m['labelVolume'];labels=np.frombuffer(decoded(lv),dtype=lv['dtype']).reshape(lv['shape'],order=lv['storageOrder']);label_inverse=np.linalg.inv(np.asarray(lv['voxelToRAS']))
    scans={key:np.frombuffer(decoded(v),dtype=v['dtype']).reshape(v['shape'],order=v['storageOrder'])for key,v in m['volumes'].items()}
    destination=OUT/'native-review';destination.mkdir(exist_ok=True);evidence=[]
    views=[('Sagittal',2,0,1),('Coronal',0,2,1),('Axial',1,2,0)]
    for structure in anchors['structures']:
        code=structure['code'];positions=np.argwhere(labels==code);world=transform(np.asarray(lv['voxelToRAS']),positions)
        fig,axes=plt.subplots(2,6,figsize=(18,9),dpi=150);panels=[]
        for row,(modality,scan)in enumerate(scans.items()):
            descriptor=m['volumes'][modality];affine=np.asarray(descriptor['voxelToRAS']);ijk=structure['MRIAnchors'][modality]['sourceIJK'];native=transform(np.linalg.inv(affine),world)
            # Bounds include every source-label centre plus eight millimetres.
            spacing=np.linalg.norm(affine[:3,:3],axis=0);lower=np.maximum(0,np.floor(native.min(0)-8/spacing).astype(int));upper=np.minimum(scan.shape,np.ceil(native.max(0)+8/spacing).astype(int)+1)
            low,high=descriptor['defaultWindow']
            for column,(view,normal,u,v)in enumerate(views):
                horizontal=np.arange(lower[u],upper[u]);vertical=np.arange(lower[v],upper[v]);U,V=np.meshgrid(horizontal,vertical);points=np.empty((*U.shape,3),int);points[...,normal]=ijk[normal];points[...,u]=U;points[...,v]=V
                values=scan[points[...,0],points[...,1],points[...,2]];source_world=transform(affine,points);indices=np.floor(transform(label_inverse,source_world)+.5).astype(int);valid=np.all((indices>=0)&(indices<np.asarray(labels.shape)),axis=-1);mask=np.zeros(U.shape,bool);mask[valid]=labels[tuple(indices[valid].T)]==code
                grey=np.floor(255*np.clip((values-low)/(high-low),0,1)+.5).astype(np.uint8);rgb=np.repeat(grey[...,None],3,axis=2);marked=rgb.copy();marked[mask]=np.floor(.65*rgb[mask]+.35*np.array([255,128,0])+.5).astype(np.uint8)
                names=[['L','R'],['P','A'],['I','S']]
                def direction(axis,sign):
                    a=affine[:3,axis];dominant=int(np.argmax(abs(a)));return names[dominant][int(a[dominant]*sign>0)]
                for offset,image in enumerate([rgb,marked]):
                    ax=axes[row,column*2+offset];ax.imshow(image,interpolation='nearest',origin='upper',aspect=spacing[v]/spacing[u]);ax.set_title(modality+' '+view+'\n'+('MRI + source label' if offset else 'Unmarked MRI'));ax.set_xticks([]);ax.set_yticks([]);[spine.set_visible(False) for spine in ax.spines.values()];ax.set_xlabel(f'{direction(u,-1)} ← → {direction(u,1)} | top {direction(v,-1)}, bottom {direction(v,1)}\n{values.shape[1]*spacing[u]:.1f} × {values.shape[0]*spacing[v]:.1f} mm')
                panels.append({'modality':modality,'view':view,'normalSourceAxis':normal,'sourceSlice':ijk[normal],'horizontalSourceAxis':u,'verticalSourceAxis':v,'sourceCropLower':lower.tolist(),'sourceCropUpperExclusive':upper.tolist(),'window':[low,high],'shape':list(values.shape),'originalPlaneSampleSHA256':sha(values.tobytes()),'unmarkedRGB_SHA256':sha(rgb.tobytes()),'annotatedRGB_SHA256':sha(marked.tobytes()),'labelPixels':int(mask.sum())})
        fig.suptitle(structure['sourceName']+' — native MRI inspection samples',fontsize=18)
        fig.text(.5,.025,'SPL source grids; crop includes label bounds + 8 mm. Nearest source-label display only. No MRI interpolation.\nSelected planes do not prove whole-structure visibility, normality, registration to a patient, or clinical adequacy.',ha='center',fontsize=11)
        fig.subplots_adjust(left=.025,right=.98,bottom=.16,top=.84,wspace=.3,hspace=.9)
        fig.canvas.draw()
        for index,panel in enumerate(panels):
            row,column=divmod(index,3)
            panel['sourcePixelToFigureMatrices']=[axes[row,column*2+offset].transData.get_affine().get_matrix().tolist() for offset in [0,1]]
        name=f'source-label-{code}.png';fig.savefig(destination/name,dpi=150);plt.close(fig)
        evidence.append({'code':code,'name':structure['sourceName'],'image':name,'sha256':sha((destination/name).read_bytes()),'panels':panels,'clinicalVisibilityReviewed':False})
    proof={'sourceManifestSHA256':MANIFEST_SHA256,'generatorSHA256':sha(Path(__file__).read_bytes()),'reviewSheets':evidence,'MRIResampled':False,'sourceLabelsDisplayedBy':'Nearest native label-cell assignment in declared source world coordinates','clinicalApproval':False,'completeReportingCoverage':False}
    (destination/'proof.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps({'reviewSheets':len(evidence),'pairedPlanes':sum(len(x['panels'])for x in evidence),'clinicalAdequacyClaimed':False}))
if __name__=='__main__':main()
