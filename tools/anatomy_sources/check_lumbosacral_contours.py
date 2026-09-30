"""Inspect native contour control polygons; do not infer unrecorded spline settings."""
from pathlib import Path
import json,hashlib,zipfile
import numpy as np,nibabel as nib
from matplotlib.path import Path as Polygon
ROOT=Path(__file__).resolve().parents[2];STAGE=Path('/tmp/primer-msk-sources/lumbosacral2024');OUT=ROOT/'docs/msk-lumbosacral-nerve-source-review'


def intersections(p):
    result=[]
    def cross(a,b):return a[0]*b[1]-a[1]*b[0]
    for i in range(len(p)):
        a,b=p[i],p[(i+1)%len(p)]
        for j in range(i+1,len(p)):
            if j in {i,(i+1)%len(p)} or (j+1)%len(p)==i:continue
            c,d=p[j],p[(j+1)%len(p)];den=cross(b-a,d-c)
            if abs(den)<1e-10:continue
            t=cross(c-a,d-c)/den;u=cross(c-a,b-a)/den
            if 0<t<1 and 0<u<1:result.append([i,j])
    return result


def main():
    base=json.loads((OUT/'annotation-and-image-audit.json').read_text());acq=json.loads((STAGE/'case-acquisition.json').read_text());record=next(x for x in acq['files'] if x['file'].endswith('CISS.nii.gz'));image_path=Path(record['file']);assert hashlib.sha256(image_path.read_bytes()).hexdigest()==record['sha256'];image=nib.load(image_path);inv=np.linalg.inv(image.affine)
    raw=(STAGE/'markers.zip').read_bytes();assert hashlib.sha256(raw).hexdigest()==base['marker_archive_sha256'];rows=[];vertices={}
    with zipfile.ZipFile(STAGE/'markers.zip') as archive:
        for r in base['selected_case_annotations']:
            if r['category'] not in ['cord','dura']:continue
            raw=archive.read(r['member']);assert hashlib.sha256(raw).hexdigest()==r['sha256'];m=json.loads(raw)['markups'][0];assert m['type']=='ClosedCurve' and m['coordinateSystem']=='LPS' and m['coordinateUnits']=='mm'
            lps=np.asarray([p['position'] for p in m['controlPoints']]);assert np.array_equal(lps,np.asarray(r['points_lps_mm']));vox=nib.affines.apply_affine(inv,lps*[-1,-1,1]);xy=vox[:,:2];native_k=vox[:,2];plane=float(np.mean(native_k));index=int(np.rint(plane));area=.5*float(np.sum(xy[:,0]*np.roll(xy[:,1],-1)-xy[:,1]*np.roll(xy[:,0],-1)))*float(np.linalg.norm(np.cross(image.affine[:3,0],image.affine[:3,1])))
            edges=np.linalg.norm(np.roll(lps,-1,axis=0)-lps,axis=1);hits=intersections(xy);key=r['member'];vertices[key]=xy
            rows.append({'member':key,'category':r['category'],'points':len(xy),'mean_native_slice':plane,'nearest_slice':index,'native_slice_spread':float(np.ptp(native_k)),'distance_to_nearest_slice_voxels':abs(plane-index),'signed_control_polygon_area_mm2':area,'minimum_edge_mm':float(edges.min()),'maximum_edge_mm':float(edges.max()),'duplicate_control_points':len(xy)-len(np.unique(xy,axis=0)),'strict_nonadjacent_edge_crossings':hits,'explicit_curve_type':m.get('curveType'),'source_sha256':r['sha256']})
    coverage={}
    for category in ['cord','dura']:
        selected=[r for r in rows if r['category']==category];indices=[r['nearest_slice'] for r in selected];coverage[category]={'count':len(selected),'minimum_slice':min(indices),'maximum_slice':max(indices),'missing_integer_slices_inside_range':sorted(set(range(min(indices),max(indices)+1))-set(indices)),'duplicate_slice_indices':sorted({i for i in indices if indices.count(i)>1}),'maximum_plane_spread_voxels':max(r['native_slice_spread'] for r in selected),'maximum_offset_from_native_slice_voxels':max(r['distance_to_nearest_slice_voxels'] for r in selected),'crossing_control_polygons':sum(bool(r['strict_nonadjacent_edge_crossings']) for r in selected)}
    pairs=[]
    for cord in [r for r in rows if r['category']=='cord']:
        matches=[r for r in rows if r['category']=='dura' and r['nearest_slice']==cord['nearest_slice']]
        if len(matches)!=1:continue
        dura=matches[0];boundary=vertices[dura['member']];polygon=Polygon(np.vstack([boundary,boundary[0]]),closed=True);inside=polygon.contains_points(vertices[cord['member']],radius=1e-8)
        pairs.append({'slice':cord['nearest_slice'],'cord':cord['member'],'dura':dura['member'],'cord_control_points_outside_dura_control_polygon':int((~inside).sum()),'mean_plane_separation_voxels':abs(cord['mean_native_slice']-dura['mean_native_slice'])})
    report={'case':'sub-03','source_ciss_sha256':record['sha256'],'marker_archive_sha256':base['marker_archive_sha256'],'contours':rows,'slice_coverage':coverage,'paired_control_polygon_checks':pairs,'limits':['These are original control polygons, not reconstruction of the unrecorded source interpolation settings.','Strict segment crossings omit collinear-overlap and tangency classification.','Containment of control points is not full-curve or inter-slice containment.','No surface lofting, capping, registration, smoothing or clinical validation performed.'],'geometry_modified':False,'clinical_approval':False,'runtime_promoted':False}
    (OUT/'cord-dura-contour-audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(coverage,indent=2));print('Paired slices:',len(pairs),'with outside control points:',sum(r['cord_control_points_outside_dura_control_polygon']>0 for r in pairs))


if __name__=='__main__':main()
