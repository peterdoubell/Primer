"""Compare every released SR characterization and contour metric to original XML."""
from pathlib import Path
import hashlib
import io
import json
import sys
import zipfile
import numpy as np
from scipy.spatial.distance import pdist
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'.research/pulmonary-intake-20261011/python-deps'))
import pydicom
OUT=ROOT/'web/anatomy/lidc-idri-0525'


def contents(d):
    rows=[]
    for c in getattr(d,'ContentSequence',[]):
        rows.append(c);rows+=contents(c)
    return rows


def main():
    m=json.loads((OUT/'manifest.json').read_text());records=[]
    field_names={'subtlety':'Subtlety score','internalStructure':'Internal structure','calcification':'Calcification',
                 'sphericity':'Sphericity','margin':'Margin','lobulation':'Lobular Pattern','spiculation':'Spiculation','texture':'Texture','malignancy':'Malignancy'}
    for a in m['annotations']:
        archive=OUT/a['source_SR']['original_archive']
        with zipfile.ZipFile(archive) as z:
            raw=z.read(next(n for n in z.namelist() if n.endswith('.dcm')))
        assert hashlib.sha256(raw).hexdigest()==a['source_SR']['original_dicom_sha256']
        d=pydicom.dcmread(io.BytesIO(raw));all_content=contents(d)
        items={str(c.ConceptNameCodeSequence[0].CodeMeaning):c for c in all_content if hasattr(c,'ConceptNameCodeSequence')}
        checks=[]
        for field,name in field_names.items():
            expected=int(a['characteristics'][field]);c=items[name];coded=c.ConceptCodeSequence[0];meaning=str(coded.CodeMeaning)
            if str(coded.CodingSchemeDesignator)=='99LIDCQIICR':assert int(str(coded.CodeValue))%100==expected
            elif field=='internalStructure':assert meaning.lower()=={1:'soft tissue',2:'fluid',3:'fat',4:'air'}[expected]
            elif field=='calcification':assert meaning.lower()=={1:'popcorn',2:'laminated',3:'solid appearance',4:'non-central',5:'central',6:'absent'}[expected]
            elif field=='texture':assert meaning.lower()=={1:'non-solid pulmonary nodule',3:'part-solid pulmonary nodule',5:'solid pulmonary nodule'}[expected]
            elif field=='sphericity':assert meaning.lower()=={3:'ovoid',5:'round'}[expected]
            elif field=='margin':assert meaning.lower()=={1:'indistinct margin',5:'circumscribed margin'}[expected]
            else:raise ValueError((field,meaning,'unrecognized original mapping'))
            checks.append(dict(field=field,original_XML_value=expected,original_SR_meaning=meaning,original_SR_code=str(coded.CodeValue),source_match=True))
        mark=next(x for x in m['xml_marks'] if x['source_id']==a['id'].removeprefix('annotation-') and x['complete_contour'])
        zs=np.unique([float(r['imageZposition']) for r in mark['rois']]);extended=np.r_[2*zs[0]-zs[1],zs,2*zs[-1]-zs[-2]]
        volume=0.;diameter=0.
        for roi in mark['rois']:
            pts=np.array(roi['points'],dtype=float)*m['ct']['pixel_spacing_mm'][0]
            x,y=pts.T;area=.5*abs(np.dot(x,np.roll(y,1))-np.dot(y,np.roll(x,1)))
            iz=int(np.argmin(abs(extended-float(roi['imageZposition']))));step=.5*(extended[iz+1]-extended[iz-1])
            volume+=(1 if roi['inclusion']=='TRUE' else -1)*area*step
            if len(pts)>1:diameter=max(diameter,float(pdist(pts).max()))
        source_volume=float(items['Volume'].MeasuredValueSequence[0].NumericValue)
        source_diameter=float(items['Diameter'].MeasuredValueSequence[0].NumericValue)
        assert np.isclose(source_volume,volume,rtol=1e-6,atol=1e-5),(a['id'],source_volume,volume)
        assert np.isclose(source_diameter,diameter,rtol=1e-6,atol=1e-6),(a['id'],source_diameter,diameter)
        assert items['Volume'].MeasuredValueSequence[0].MeasurementUnitsCodeSequence[0].CodeValue=='mm3'
        assert items['Diameter'].MeasuredValueSequence[0].MeasurementUnitsCodeSequence[0].CodeValue=='mm'
        # Report the original method distinction, rather than forcing a cell sum
        # to match continuous contour area integration.
        cell_volume=a['occupied_voxels']*a['pixel_spacing_mm'][0]*a['pixel_spacing_mm'][1]*a['source_spacing_mm']
        records.append(dict(id=a['id'],original_SR_content_nodes=len(all_content),characterizations=checks,
                            original_SR_contour_volume_mm3=source_volume,independent_XML_contour_volume_mm3=volume,
                            original_SR_maximal_axial_contour_diameter_mm=source_diameter,independent_XML_maximal_axial_contour_diameter_mm=diameter,
                            released_SEG_native_sampling_cell_volume_mm3=cell_volume,
                            original_metric_rounding_tolerance='source6significant-digit metric strings; relative1e-6; source unchanged',
                            metrics_are_not_Fleischner_mean_diameter_or_histology=True))
    result=dict(manifest_sha256=hashlib.sha256((OUT/'manifest.json').read_bytes()).hexdigest(),original_SR_objects=8,
                compared_XML_SR_characterizations=72,compared_original_contour_metrics=16,records=records,
                source_SR_original_bytes_unchanged=True,clinical_approval=False,fine_anatomical_approval=False,structure_coverage_granted=False)
    (ROOT/'docs/pulmonary-nodule-source-review-20261011/original-XML-SR-check.json').write_text(json.dumps(result,indent=2)+'\n')
    print('source_SR_objects',len(records),'characterizations',72,'contour_metrics',16)


if __name__=='__main__':main()
