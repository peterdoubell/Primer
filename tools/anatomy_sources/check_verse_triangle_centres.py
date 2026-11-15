"""Measure sampled face-to-mask correspondence, not biological accuracy."""
from pathlib import Path
import hashlib,json
import numpy as np,nibabel as nib
from scipy.ndimage import map_coordinates
ROOT=Path(__file__).resolve().parents[2]
CASE=Path('/tmp/primer-msk-sources/verse/verse521')


def main():
    audit=json.loads((ROOT/'docs/msk-verse-source-review/chain-surface-audit.json').read_text())
    for name,digest in audit['source_files'].items():assert hashlib.sha256((CASE/name).read_bytes()).hexdigest()==digest
    ct=nib.load(CASE/'sub-verse521_dir-ax_ct.nii.gz');seg=nib.load(CASE/'sub-verse521_dir-ax_seg-vert_msk.nii.gz');assert np.array_equal(ct.affine,seg.affine)
    labels=np.asanyarray(seg.dataobj);inverse=np.linalg.inv(ct.affine[:3,:3]);rows=[]
    for row in audit['levels']:
        path=ROOT/row['file'];assert hashlib.sha256(path.read_bytes()).hexdigest()==row['sha256'];mesh=np.load(path);v=mesh['vertices_world_mm'];f=mesh['faces'];tri=v[f];centres=tri.mean(axis=1);cross=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);length=np.linalg.norm(cross,axis=1);assert np.all(length>0);normal=cross/length[:,None]
        lo=np.asarray(row['crop_start']);hi=np.asarray(row['crop_stop']);field=(labels[tuple(slice(a,b) for a,b in zip(lo,hi))]==row['label']).astype(float)
        xyz=(centres-ct.affine[:3,3])@inverse.T-lo;direction=normal@inverse.T
        values=map_coordinates(field,xyz.T,order=1,mode='constant',cval=0);residual=values-.5;active=np.abs(residual)>1e-12;sign=np.where(residual>=0,1.,-1.);direction*=sign[:,None]
        lower=np.zeros(len(f));upper=np.zeros(len(f));bracketed=~active
        for distance in np.arange(.05,2.001,.05):
            ids=np.flatnonzero(~bracketed)
            if not len(ids):break
            sample=map_coordinates(field,(xyz[ids]+distance*direction[ids]).T,order=1,mode='constant',cval=0)-.5
            found=sample*residual[ids]<=0;upper[ids[found]]=distance;lower[ids[found]]=distance-.05;bracketed[ids[found]]=True
        ids=np.flatnonzero(bracketed & active)
        for _ in range(20):
            middle=(lower[ids]+upper[ids])/2;sample=map_coordinates(field,(xyz[ids]+middle[:,None]*direction[ids]).T,order=1,mode='constant',cval=0)-.5
            found=sample*residual[ids]<=0;upper[ids[found]]=middle[found];lower[ids[~found]]=middle[~found]
        distances=(lower+upper)/2;distances[~bracketed]=np.nan;valid=distances[bracketed]
        worst=np.argsort(np.nan_to_num(distances,nan=np.inf))[-10:][::-1]
        record={'level':row['level'],'triangles_sampled':len(f),'centroid_mask_value_range':[float(values.min()),float(values.max())],'centroids_exactly_on_isovalue':int((~active).sum()),'normal_line_intersections_bracketed':int(bracketed.sum()),'unbracketed_within_2mm':int((~bracketed).sum()),'bracketed_absolute_normal_distance_mm':dict(zip(['median','p95','p99','maximum'],map(float,np.quantile(valid,[.5,.95,.99,1])))),'unbracketed_surface_area_fraction':float(length[~bracketed].sum()/length.sum()),'largest_or_unbracketed_samples':[{'face':int(i),'world_ras_mm':centres[i].tolist(),'mask_value':float(values[i]),'normal_distance_mm':float(distances[i]) if bracketed[i] else None} for i in worst]}
        rows.append(record);print(row['level'],'max',record['bracketed_absolute_normal_distance_mm']['maximum'],'unbracketed',record['unbracketed_within_2mm'],flush=True)
    report={'source_files':audit['source_files'],'surface_manifest_sha256':hashlib.sha256((ROOT/'docs/msk-verse-source-review/chain-surface-audit.json').read_bytes()).hexdigest(),'levels':rows,'method':'Every triangle centroid sampled in the original trilinearly interpolated binary source label. Search in the face-normal direction toward the 0.5 boundary with 0.05-mm steps up to 2 mm, then 20 bisections in the first detected interval. Face winding determines normal; direction reverses when centroid is outside the label.','limits':['Centroids are samples, not exhaustive triangle-interior or Hausdorff bounds.','Normal-line intersections are not necessarily nearest Euclidean boundary points.','The sampled stepping procedure does not prove no closer pair of crossings lies within an interval.','Agreement with a segmentation does not establish correct anatomical boundaries or clinical fitness.'],'geometry_changed':False,'clinical_approval':False,'runtime_promoted':False}
    (ROOT/'docs/msk-verse-source-review/triangle-centre-correspondence.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
