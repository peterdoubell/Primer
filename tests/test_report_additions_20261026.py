"""Clinical scenario, modality-scope and shipped-draft preservation checks."""
import copy
import gzip
import json
from pathlib import Path
import pytest
from primer.descriptor_reporting import render_descriptors
from primer.descriptor_calculations import descriptor_calculation_jobs
ROOT=Path(__file__).resolve().parents[1]
CURRENT=json.loads((ROOT/'data/radiology/descriptor-reporting.json').read_text())
ADDITIONS=json.loads((ROOT/'data/radiology/anatomic-additions-20261026.json').read_text())
EXAMS={i['id']:(f,i) for f in CURRENT['forms'].values() for i in f['investigations']}

def selected(iid,row,fields):return {'findings':{iid+':'+row+':'+k:v for k,v in fields.items()}}
def state(iid,selections):return {'investigation_id':iid,'selections':selections}

def test_new_examination_scope_is_exact_and_complete():
 ids=set(ADDITIONS['investigations'])
 assert len(ids)==69 and len([k for k in ids if k.startswith('xr.')])==29
 assert len(EXAMS)==225 and CURRENT['summary']['context_slots']==0
 for key in ['msk.mri-knee-postoperative','msk.mri-shoulder-postoperative','msk.mri-sacroiliac','msk.mri-soft-tissue-mass','msk.ultrasound-soft-tissue-mass','msk.mri-brachial-plexus','msk.mri-lumbosacral-plexus','msk.ct-spine-postoperative','us.venous-duplex-lower-limb','us.venous-duplex-upper-limb','us.venous-insufficiency','ct.kub','ct.urography','us.abdomen','us.renal-bladder','us.scrotum-adult','chest.ct-lung-screening','ct.colonography','neck.ct-post-treatment','neck.mri-post-treatment']:
  assert key in ids

@pytest.mark.parametrize('iid',['xr.shoulder','xr.elbow','xr.wrist','xr.hand','xr.pelvis','xr.hip','xr.knee','xr.ankle','xr.foot','xr.finger','xr.toe','xr.spine-cervical','xr.spine-thoracic','xr.spine-lumbar'])
def test_radiographs_do_not_inherit_mri_or_ct_negative_claims(iid):
 f,inv=EXAMS[iid];assert inv['modality']=='Radiography'
 negatives=' '.join(r['normal']['text'] for r in inv['sections'] if r['normal']).lower()
 assert not any(x in negatives for x in ['marrow oedema','diffusion','enhancement','ligament is intact','tendon is intact','meniscus is intact','hounsfield'])
 assert render_descriptors(f,state(iid,{}))['text']==''


def test_hand_and_foot_radiographs_keep_each_digit_and_joint_separate():
 for iid,digits in [('xr.hand',['Index','Middle finger','Ring finger','Little finger']),('xr.foot',['Second toe','Third toe','Fourth toe','Fifth toe'])]:
  labels={r['label'] for r in EXAMS[iid][1]['sections']}
  assert {d+' '+p+' phalanx' for d in digits for p in ['proximal','middle','distal']}<=labels
  assert {d+' '+j+' joint' for d in digits for j in ['PIP','DIP']}<=labels


def test_postoperative_disruption_cannot_coexist_with_native_normal():
 iid='msk.mri-knee-postoperative';f,_=EXAMS[iid]
 s=state(iid,{'anatomy-acl':{'normal':True},'anatomy-graft-acl':selected(iid,'graft-acl',{'continuity':{'slot-1':'complete disruption'}})})
 result=render_descriptors(f,s)
 assert not result['valid'] and 'conflicting_anatomic_normal' in {x['code'] for x in result['issues']}
 iid='msk.mri-shoulder-postoperative';f,_=EXAMS[iid]
 s=state(iid,{'anatomy-supraspinatus-tendon':{'normal':True},'anatomy-repair-supraspinatus':selected(iid,'repair-supraspinatus',{'status':{'slot-1':'full-thickness recurrent defect'}})})
 assert not render_descriptors(f,s)['valid']


def test_published_frozen_catalogue_preserves_every_original_investigation():
 old=json.loads(gzip.decompress((ROOT/'data/radiology/descriptor-history/cb2532f44e891cbf87c8396ab32168b11de670a3a6bddfaf33d711751206189c.json.gz').read_bytes()))
 assert sum(len(f['investigations']) for f in old['forms'].values())==156
 for form in old['forms'].values():
  for inv in form['investigations']:
   assert EXAMS[inv['id']][1]==inv,'Existing examination observations must not be rewritten'


def test_orads_jobs_use_each_lesions_own_features_and_do_not_score_absence():
 iid='us.adnexal-orads';f,_=EXAMS[iid]
 one=selected(iid,'adnexal-lesion',{'lesion':{'slot-1':'right ovary'},'simple':{},'size':{'slot-1':50}})
 two=selected(iid,'adnexal-lesion',{'lesion':{'slot-1':'left ovary'},'solid':{},'size':{'slot-1':50},'contour':{'slot-1':'irregular'}})
 s=state(iid,{'anatomy-adnexal-lesion':{'instances':[one,two]}})
 assert render_descriptors(f,s)['valid']
 jobs=descriptor_calculation_jobs(f,s)
 assert [j['inputs']['morphology'] for j in jobs]==['simple_cyst','solid']
 assert jobs[0]['inputs']['contour']=='smooth' and jobs[1]['inputs']['contour']=='irregular'
 assert 'applicable_adnexal_lesion' not in jobs[0]['inputs']
 assert descriptor_calculation_jobs(f,state(iid,{'anatomy-adnexal-lesion':{'normal':True}}))==[]


def test_venous_thrombosis_is_segment_specific_and_not_a_global_normal_default():
 iid='us.venous-duplex-lower-limb';f,inv=EXAMS[iid]
 labels={r['label'] for r in inv['sections']}
 assert {s+' '+v for s in ['Right','Left'] for v in ['Common femoral vein','Femoral vein proximal segment','Femoral vein middle segment','Femoral vein distal segment','Popliteal vein','Posterior tibial veins','Peroneal veins']}<=labels
 assert render_descriptors(f,state(iid,{}))['text']==''
