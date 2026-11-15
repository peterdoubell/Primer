"""Audit original marker coordinates and a paired MRI case without fitting them."""
from pathlib import Path
import json,hashlib,re,zipfile
from collections import Counter
import nibabel as nib,numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[2];STAGE=Path('/tmp/primer-msk-sources/lumbosacral2024');OUT=ROOT/'docs/msk-lumbosacral-nerve-source-review'


def main():
    acquisition=json.loads((STAGE/'case-acquisition.json').read_text())
    for file in acquisition['files']:assert hashlib.sha256(Path(file['file']).read_bytes()).hexdigest()==file['sha256']
    marker_record=json.loads((OUT/'figshare-26403442.json').read_text());record=next(f for f in marker_record['files'] if f['name']=='markers.zip');raw=(STAGE/'markers.zip').read_bytes();assert len(raw)==record['size'] and hashlib.md5(raw).hexdigest()==record['computed_md5']
    images={};image_info={}
    for name in ['CISS','DESS','T2TSE']:
        image=nib.load(STAGE/'sub-03'/('sub-03_'+name+'.nii.gz'));assert image.header.get_xyzt_units()[0]=='mm';images[name]=image
        sidecar=json.loads((STAGE/'sub-03'/('sub-03_'+name+'.json')).read_text());q,qcode=image.get_qform(coded=True);s,scode=image.get_sform(coded=True)
        image_info[name]={'shape':list(image.shape),'voxel_spacing_mm':list(map(float,image.header.get_zooms())),'axis_codes':list(nib.aff2axcodes(image.affine)),'selected_affine':image.affine.tolist(),'qform_code':int(qcode),'sform_code':int(scode),'qform_sform_max_difference':float(np.max(np.abs(q-s))) if qcode and scode else None,'sidecar':{k:sidecar[k] for k in ['SliceThickness','SpacingBetweenSlices','RepetitionTime','EchoTime','ImageType'] if k in sidecar}}
    subjects={};selected=[];all_points=0;filename_variants=[]
    with zipfile.ZipFile(STAGE/'markers.zip') as archive:
        assert archive.testzip() is None
        for name in archive.namelist():
            if not name.endswith('.json'):continue
            match=re.fullmatch(r'markers/(sub-\d{2})/(sub[-_]\d{2})_(cord|dura|ganglions|nerveroots)_(.+)\.json',name);assert match,name
            subject,prefix,category,structure=match.groups();assert prefix.replace('_','-')==subject
            if prefix!=subject:filename_variants.append(name)
            document=json.loads(archive.read(name));assert len(document['markups'])==1;m=document['markups'][0];assert m['coordinateSystem']=='LPS' and m['coordinateUnits']=='mm'
            points=np.asarray([p['position'] for p in m['controlPoints']],float);assert points.ndim==2 and points.shape[1]==3 and np.isfinite(points).all();assert all(p['positionStatus']=='defined' for p in m['controlPoints']);all_points+=len(points)
            counts=subjects.setdefault(subject,Counter());counts[category]+=1
            if subject!='sub-03':continue
            ras=points*np.array([-1,-1,1]);series={}
            for sequence,image in images.items():
                vox=nib.affines.apply_affine(np.linalg.inv(image.affine),ras);inside=np.all((vox>=-.5)&(vox<=np.asarray(image.shape)-.5),axis=1)
                series[sequence]={'inside_voxel_support':int(inside.sum()),'outside_voxel_support':int((~inside).sum()),'voxel_bounds':[vox.min(0).tolist(),vox.max(0).tolist()]}
            selected.append({'member':name,'category':category,'structure':structure,'type':m['type'],'points':len(points),'sha256':hashlib.sha256(archive.read(name)).hexdigest(),'points_lps_mm':points.tolist(),'coverage_by_series':series})
    point_groups=[x for x in selected if x['category']=='nerveroots'];assert len(point_groups)==14
    ciss=images['CISS'];inv=np.linalg.inv(ciss.affine);by_slice={}
    for group in point_groups:
        vox=nib.affines.apply_affine(inv,np.asarray(group['points_lps_mm'])*[-1,-1,1])
        for point in vox:
            index=int(np.rint(point[2]))
            if 0<=index<ciss.shape[2] and abs(point[2]-index)<=.5:
                by_slice.setdefault(index,[]).append((group['structure'],point))
    index=max(by_slice,key=lambda k:(len({x[0] for x in by_slice[k]}),-abs(k-(ciss.shape[2]-1)/2)))
    markers=by_slice[index];points=np.asarray([p for _,p in markers]);lo=np.maximum(0,np.floor(points[:,:2].min(0)-40).astype(int));hi=np.minimum(np.array(ciss.shape[:2]),np.ceil(points[:,:2].max(0)+41).astype(int));plane=np.asanyarray(ciss.dataobj[:,:,index]);crop=plane[lo[0]:hi[0],lo[1]:hi[1]];assert np.isfinite(crop).all();window=list(map(float,np.percentile(crop,[1,99.5])))
    fig,axes=plt.subplots(1,2,figsize=(12,6));colors=plt.get_cmap('tab20');keys=sorted({name for name,_ in markers});legend={name:colors(i) for i,name in enumerate(keys)}
    for n,ax in enumerate(axes):
        ax.imshow(crop.T,cmap='gray',origin='lower',interpolation='nearest',vmin=window[0],vmax=window[1]);ax.set_axis_off();ax.set_title('Source MRI window' if n==0 else 'Original annotation positions')
        for x,y,text in [(.02,.5,'L'),(.98,.5,'R'),(.5,.98,'A'),(.5,.02,'P')]:ax.text(x,y,text,transform=ax.transAxes,color='#ffd978',ha='center',va='center')
        if n:
            for key in keys:
                v=np.asarray([p for name,p in markers if name==key]);ax.scatter(v[:,0]-lo[0],v[:,1]-lo[1],facecolors='none',edgecolors=[legend[key]],s=55,label=key,linewidths=1)
            ax.legend(loc='upper left',bbox_to_anchor=(1,1),fontsize=8,title='Source root label')
    fig.suptitle(f'Lumbosacral MRI sub-03 · native CISS slice {index} · near-axial grid',fontsize=13)
    fig.text(.5,.025,'Markers are source annotation points within half a slice, not segmented nerve boundaries or measured diameters.\nDisplay window is documented; pixels enlarged without interpolation. Native grid directions shown. Anatomical correspondence requires review.\nLiu et al. (2024), Figshare collection 10.6084/m9.figshare.c.7372564 · CC BY 4.0. Crop, display window and overlays added.',ha='center',fontsize=8)
    fig.tight_layout(rect=(0,.11,1,.94));fig.savefig(OUT/'sub03-ciss-marker-review.png',dpi=160);plt.close(fig)
    report={'marker_archive_md5':record['computed_md5'],'marker_archive_sha256':hashlib.sha256(raw).hexdigest(),'subject_counts':{k:dict(v) for k,v in subjects.items()},'total_defined_points':all_points,'coordinate_system':'LPS millimetres; x/y signs reversed only to express RAS for NIfTI affine inversion','filename_prefix_variants':filename_variants,'case':'sub-03','images':image_info,'selected_case_annotations':selected,'review_figure':{'sequence':'CISS','slice_index':index,'crop_start':lo.tolist(),'crop_stop':hi.tolist(),'display_window':window,'source_labels':keys,'markers':[{'label':name,'voxel':point.tolist()} for name,point in markers]},'limits':['Bounding-box inclusion does not prove anatomical identity or accurate registration.','No cross-sequence registration or point fitting was applied.','Source markers represent annotated trajectories and contours, not all nerve rootlets or patient-specific nerve diameters.','No model was assigned to the VerSe CT case, which is a different source subject.'],'clinical_approval':False,'runtime_promoted':False}
    (OUT/'annotation-and-image-audit.json').write_text(json.dumps(report,indent=2)+'\n');print('Audited',len(subjects),'subjects,',all_points,'defined points;',len(selected),'sub-03 marker files.');print('Review slice',index,'labels',keys)


if __name__=='__main__':main()
