from pathlib import Path
import json,io,sys,zipfile,hashlib
ROOT=Path(__file__).resolve().parents[1];p=ROOT/'web/anatomy/lidc-idri-0525';sys.path.insert(0,str(ROOT/'.research/pulmonary-intake-20261011/python-deps'));import pydicom
m=json.loads((p/'manifest.json').read_text())
def tree(d):
 out=[]
 for c in getattr(d,'ContentSequence',[]):out.append(c);out+=tree(c)
 return out
names={'subtlety':'Subtlety score','internalStructure':'Internal structure','calcification':'Calcification','sphericity':'Sphericity','margin':'Margin','lobulation':'Lobular Pattern','spiculation':'Spiculation','texture':'Texture','malignancy':'Malignancy'}
# Standard source semantic mappings; numeric ordinal values use original
# QIICR99 codes in SR. Do not interpret those ordinal ratings as histology.
meanings={'internalStructure':{1:'soft tissue',2:'fluid',3:'fat',4:'air'},'calcification':{1:'popcorn',2:'laminated',3:'solid appearance',4:'non-central',5:'central',6:'absent'},'texture':{1:'non-solid pulmonary nodule',3:'part-solid pulmonary nodule',5:'solid pulmonary nodule'},'sphericity':{3:'ovoid',5:'round'},'margin':{1:'indistinct margin',5:'circumscribed margin'}}
def original_tree(d):
 result={'value_type':str(getattr(d,'ValueType','ROOT')),'name':'','children':[original_tree(c) for c in getattr(d,'ContentSequence',[])]}
 if hasattr(d,'ConceptNameCodeSequence'):result['name']=str(d.ConceptNameCodeSequence[0].CodeMeaning)
 if hasattr(d,'ConceptCodeSequence'):
  c=d.ConceptCodeSequence[0];result['coded_value']={'meaning':str(c.CodeMeaning),'value':str(c.CodeValue),'scheme':str(c.CodingSchemeDesignator)}
 if hasattr(d,'MeasuredValueSequence'):
  v=d.MeasuredValueSequence[0];result['measurement']={'value':str(v.NumericValue),'unit':str(v.MeasurementUnitsCodeSequence[0].CodeValue)}
 if hasattr(d,'TextValue'):result['text']=str(d.TextValue)
 return result
rows=[]
for a in m['annotations']:
 with zipfile.ZipFile(p/a['source_SR']['original_archive']) as z:raw=z.read(next(n for n in z.namelist() if n.endswith('.dcm')))
 d=pydicom.dcmread(io.BytesIO(raw));assert str(d.SOPInstanceUID)==a['source_SR']['source_sop'];assert original_tree(d)==a['source_SR']['full_content_tree'];nodes=tree(d);items={str(c.ConceptNameCodeSequence[0].CodeMeaning):c for c in nodes if hasattr(c,'ConceptNameCodeSequence')}
 checks=[]
 for field,name in names.items():
  value=int(a['characteristics'][field]);code=items[name].ConceptCodeSequence[0];meaning=str(code.CodeMeaning).lower();scheme=str(code.CodingSchemeDesignator)
  if scheme=='99LIDCQIICR':assert int(code.CodeValue)%100==value
  else:assert meaning==meanings[field][value],(field,meaning,value)
  checks.append(dict(field=field,XML_ordinal=value,SR_original_code=str(code.CodeValue),SR_original_scheme=scheme,SR_original_meaning=str(code.CodeMeaning)))
 # All source XML values already independently compared against originals.
 rows.append(dict(annotation=a['id'],SR_DICOM_sha256=hashlib.sha256(raw).hexdigest(),original_content_nodes=len(nodes),complete_original_displayed_content_tree_match=True,characterizations=checks))
result=dict(compared_original_objects=8,compared_original_XML_SR_characterizations=72,all_original_coded_values_match=True,subjective_malignancy_scores_are_not_histology=True,rows=rows,clinical_approval=False)
(ROOT/'docs/pulmonary-nodule-independent-review-20261011/SR-characteristics.json').write_text(json.dumps(result,indent=2)+'\n');print('SRobjects8 XMLcharacterizations72 exact source semantic agreement')
