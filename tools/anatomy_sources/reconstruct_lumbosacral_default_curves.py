"""Explicit fresh-default interpretation of saved Slicer 5.4 contour controls.

Not a claim that unrecorded author settings were default.
"""
from pathlib import Path
import json,hashlib,zipfile
import numpy as np
from vtkmodules.vtkCommonCore import vtkPoints,vtkVersion
from vtkmodules.vtkCommonComputationalGeometry import vtkCardinalSpline,vtkParametricSpline
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'docs/msk-lumbosacral-nerve-source-review';STAGE=Path('/tmp/primer-msk-sources/lumbosacral2024');DEST=ROOT/'output/msk-lumbosacral-sub03/default-curves'


def strict_crossings(points):
    start=points[:-1,:2];edge=np.diff(points[:,:2],axis=0);delta=start[None,:,:]-start[:,None,:]
    def cross(a,b):return a[...,0]*b[...,1]-a[...,1]*b[...,0]
    den=cross(edge[:,None,:],edge[None,:,:]);valid=np.abs(den)>1e-10;t=np.zeros_like(den);u=np.zeros_like(den)
    np.divide(cross(delta,edge[None,:,:]),den,out=t,where=valid);np.divide(cross(delta,edge[:,None,:]),den,out=u,where=valid)
    n=len(start);nonadj=np.triu(np.ones((n,n),bool),2);nonadj[0,n-1]=False
    return np.argwhere(nonadj&valid&(t>0)&(t<1)&(u>0)&(u<1)).tolist()


def main():
    assert vtkVersion.GetVTKVersion()=='9.2.6'
    source_dir=STAGE/'slicer-5.4.0'
    def normalized(path):return '\n'.join(x for x in path.read_text().splitlines() if x not in ['VTK_ABI_NAMESPACE_BEGIN','VTK_ABI_NAMESPACE_END'])
    for name in ['vtkCardinalSpline.cxx','vtkParametricSpline.cxx']:
        assert normalized(source_dir/('wheel-'+name))==normalized(source_dir/('slicer-'+name))
    records=json.loads((OUT/'annotation-and-image-audit.json').read_text());audit=json.loads((OUT/'cord-dura-contour-audit.json').read_text());inverse=np.linalg.inv(np.asarray(records['images']['CISS']['selected_affine']));rows=[];curve_arrays={};DEST.mkdir(parents=True,exist_ok=True)
    assert hashlib.sha256((STAGE/'markers.zip').read_bytes()).hexdigest()==records['marker_archive_sha256']
    archive=zipfile.ZipFile(STAGE/'markers.zip')
    for record in records['selected_case_annotations']:
        if record['category'] not in ['cord','dura']:continue
        raw=archive.read(record['member']);assert hashlib.sha256(raw).hexdigest()==record['sha256'];markup=json.loads(raw)['markups'][0];assert markup['type']=='ClosedCurve' and 'curveType' not in markup and markup['coordinateSystem']=='LPS' and markup['coordinateUnits']=='mm'
        original=np.asarray([p['position'] for p in markup['controlPoints']]);assert np.array_equal(original,np.asarray(record['points_lps_mm']));ras=original*[-1,-1,1];points=vtkPoints()
        for point in ras:points.InsertNextPoint(*point)
        assert points.GetData().GetDataTypeAsString()=='float'
        spline=vtkParametricSpline();spline.SetXSpline(vtkCardinalSpline());spline.SetYSpline(vtkCardinalSpline());spline.SetZSpline(vtkCardinalSpline());spline.SetPoints(points);spline.SetClosed(True);spline.SetParameterizeByLength(False)
        n=len(original);sampled=vtkPoints()
        for i in range(n*10+1):
            result=[0.,0.,0.];spline.Evaluate([i/(n*10),0,0],result,[0.]*9);sampled.InsertNextPoint(result)
        curve_ras=np.asarray([sampled.GetPoint(i) for i in range(sampled.GetNumberOfPoints())]);curve=curve_ras*[-1,-1,1]
        assert np.array_equal(curve[0],curve[-1]);assert np.array_equal(curve[::10],np.vstack([original.astype('f4').astype(float),original[0].astype('f4').astype(float)]))
        segment=np.minimum(np.arange(len(curve)-1)//10,n-1);a=original[segment];b=original[(segment+1)%n];edge=b-a;parameter=np.clip(np.sum((curve[:-1]-a)*edge,axis=1)/np.sum(edge*edge,axis=1),0,1);deviation=np.linalg.norm(curve[:-1]-(a+parameter[:,None]*edge),axis=1)
        area=.5*np.sum(curve[:-1,0]*curve[1:,1]-curve[:-1,1]*curve[1:,0]);base=next(r for r in audit['contours'] if r['member']==record['member']);voxel=curve_ras@inverse[:3,:3].T+inverse[:3,3]
        curve_arrays[record['member']]=curve
        path=DEST/(Path(record['member']).stem+'.npz');np.savez_compressed(path,original_lps_mm=original,default_curve_lps_mm=curve,native_voxel=voxel)
        rows.append({'member':record['member'],'source_sha256':record['sha256'],'category':record['category'],'native_slice':base['nearest_slice'],'sample_points':len(curve),'file':str(path.relative_to(ROOT)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'input_float32_max_error_mm':float(np.max(np.linalg.norm(original-original.astype('f4').astype(float),axis=1))),'maximum_deviation_from_corresponding_control_segment_mm':float(deviation.max()),'signed_sampled_area_lps_xy_mm2':float(area),'native_slice_spread_after_float32_sampling':float(np.ptp(voxel[:,2])),'strict_crossings':strict_crossings(curve)})
    pairs=[]
    for cord in [r for r in rows if r['category']=='cord']:
        dura=next(r for r in rows if r['category']=='dura' and r['native_slice']==cord['native_slice'])
        p=curve_arrays[cord['member']][:-1,:2];q=curve_arrays[dura['member']][:,:2];a=q[:-1];b=q[1:]
        crosses=(a[None,:,1]>p[:,None,1])!=(b[None,:,1]>p[:,None,1]);cross_x=np.zeros(crosses.shape)
        np.divide((p[:,None,1]-a[None,:,1])*(b-a)[None,:,0],(b-a)[None,:,1],out=cross_x,where=crosses)
        cross_x+=a[None,:,0];inside=((crosses&(p[:,None,0]<cross_x)).sum(axis=1)%2)==1
        pairs.append({'slice':cord['native_slice'],'cord_sample_points':len(p),'outside_sampled_dura_polygon':int((~inside).sum())})
    archive.close()
    report={'annotation_audit_sha256':hashlib.sha256((OUT/'annotation-and-image-audit.json').read_bytes()).hexdigest(),'marker_archive_sha256':records['marker_archive_sha256'],'interpretation':'Fresh Slicer 5.4 constructor defaults: closed cardinal spline; control-point-index parameterization; ten subdivisions per segment; float input/output vtkPoints. Author-specific scene defaults and unrecorded original settings are not asserted.','engine':'VTK '+vtkVersion.GetVTKVersion(),'slicer_vtk_ref':'4341e4825259e17d2acd0e30d2b6f138da10360f','vtk_core_comparison':'CardinalSpline and ParametricSpline C++ implementations differ only by ABI namespace wrappers.','curves':rows,'sampled_containment':pairs,'clinical_approval':False,'runtime_promoted':False,'limits':['No tissue volume, endpoint cap or between-slice surface is constructed.','Discrete curve crossings are not an exhaustive continuous-spline self-intersection proof.','Curve deviation from a control polygon is reconstruction sensitivity, not biological error.']}
    (OUT/'default-curve-reconstruction.json').write_text(json.dumps(report,indent=2)+'\n');print('Curves:',len(rows),'strict crossing cases:',sum(bool(r['strict_crossings']) for r in rows));print('Maximum corresponding-segment deviation mm:',max(r['maximum_deviation_from_corresponding_control_segment_mm'] for r in rows));print('Sampled containment violations:',sum(r['outside_sampled_dura_polygon'] for r in pairs));print('Maximum input roundoff mm:',max(r['input_float32_max_error_mm'] for r in rows))


if __name__=='__main__':main()
