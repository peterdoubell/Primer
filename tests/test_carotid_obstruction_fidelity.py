"""Carotid source geometry, cases and grading limits cannot imply full reporting anatomy."""
import copy
import gzip
import hashlib
import json
from pathlib import Path
import struct

import numpy as np
from PIL import Image
from primer.curriculum import Curriculum, _validate_lesson_media
from primer.radiology_catalog import detail, resolve
from primer.module_media import source_model_bindings
from tools.anatomy_sources.review_bodyparts_pancreatic_geometry import read_obj
from tools.check_msk_fidelity import requirements_for, validate_reporting_snapshots, audit
from tools.check_radiology_fidelity import digest

ROOT=Path(__file__).resolve().parents[1]
REVIEW=ROOT/'docs/carotid-obstruction-source-review'
ATLAS=ROOT/'web/anatomy/bp3d-carotid-4.3'

def sha(raw):return hashlib.sha256(raw).hexdigest()

def test_entire_report_scope_retains_both_sides_fine_tissues_and_actual_case_interfaces():
 data=json.loads((ROOT/'data/radiology/non-msk-structure-requirements.json').read_text())
 item=next(i for i in data['investigations'] if i['investigation_id']=='ra.carotid-obstruction')
 ref=detail(Curriculum(),resolve('ra.carotid-obstruction'))['radiology_reference']
 validate_reporting_snapshots({**data,'investigations':[item]},{'ra.carotid-obstruction':ref['reporting']})
 assert item['source_contract_sha256']==digest({k:ref.get(k) for k in ['reporting','report_templates','walkthrough','reading']})
 leaves={r['id']:r for r in requirements_for(item)}
 assert len(item['structures'])==142 and len(leaves)==816
 for side in ['left','right']:
  for suffix in ['vessel.distal_cervical_ICA.source_lumen_or_unresolved_lumen','wall.media.thickness_or_unresolved_thickness',
                 'lesion.every_actual_dissection.host_wall_interface','assessment.valid_distal_ICA_reference_site.actual_plane_reference_and_quality',
                 'branch.ophthalmic.source_unresolved_or_unacquired_extent']:
   assert 'carotid_obstruction.'+side+'.'+suffix in leaves
 result=audit({**data,'investigations':[item],'scope':{'catalog_investigation_ids':['ra.carotid-obstruction']}},{'assets':[{'id':'trunk-only','kind':'model','investigation_ids':['ra.carotid-obstruction'],
     'structure_ids':['carotid_obstruction.right.vessel.distal_cervical_ICA']}]},expected_catalog_ids={'ra.carotid-obstruction'})
 assert result['representation_requirements']==2448 and result['counts']['missing']==2448

def test_complete_source_figures_keep_case_panel_roles_and_caption_hold():
 ref=detail(Curriculum(),resolve('ra.carotid-obstruction'))['radiology_reference'];rows=ref['structure_atlas']
 assert len(rows)==8 and not ref['key_images']
 assert sum(r['kind']=='schematic' for r in rows)==2
 proof=json.loads((REVIEW/'published-source-preservation.json').read_text())
 assert proof['held'][0]['pmcid']=='PMC7160198' and proof['held'][0]['figure']==1
 assert not proof['clinical_approval'] and not proof['source_pixels_modified']
 for row in rows:
  raw=(ROOT/'web'/row['src'].removeprefix('/app/')).read_bytes();assert sha(raw)==row['sha256']
  with Image.open(ROOT/'web'/row['src'].removeprefix('/app/')) as im:assert im.size==(row['width'],row['height'])
 newer=next(r for r in rows if 'pmc12866240' in r['id'])
 assert newer['source_context']['source_case_groups']=={'full_collapse_case':['a'],'without_full_collapse_case':['b']}
 assert not newer['source_context']['different_panels_assumed_same_patient']
 old=next(r for r in rows if 'pmc7160198' in r['id'])
 assert old['source_context']['source_reported_diameters_mm']=={'left_distal_ICA':2.8,'right_distal_ICA':3.9,'left_ECA':2.7}
 assert not old['source_context']['independent_calibrated_measurements_verified']
 dissection=next(r for r in rows if r['id'].endswith('neck-spaces-fig12'))
 assert dissection['source_context']['panel_types']=={'a':'CT','b':'Ultrasound'}
 mra=next(r for r in rows if r['id'].endswith('neck-spaces-fig16'))
 assert 'Published MRA display' in mra['source_context']['panel_processing']['full_figure']

def test_all_original_right_carotid_coordinates_normals_and_faces_are_preserved():
 manifest=json.loads((ATLAS/'manifest.json').read_text());assert len(manifest['parts'])==3 and manifest['total_triangles']==5580
 assert manifest['license']=='CC BY-SA 2.1 Japan' and not manifest['clinical_approval']
 assert not manifest['complete_reporting_anatomy_approved'] and not manifest['source_geometry_smoothed_repaired_fitted_cropped_or_merged']
 assert {p['source_element_id'] for p in manifest['parts'].values()}=={'FJ4986','FJ4989','FJ4993'}
 for p in manifest['parts'].values():
  raw=gzip.decompress((REVIEW/'original-carotid-objects'/(p['source_element_id']+'.obj.gz')).read_bytes())
  assert sha(raw)==p['original_OBJ_sha256'];v,n,f,nf=read_obj(raw.decode())
  encoded=(ROOT/'web'/p['file'].removeprefix('/app/')).read_bytes();assert sha(encoded)==p['sha256']
  payload=gzip.decompress(encoded);assert sha(payload)==p['decoded_sha256']
  assert struct.unpack('<4sII',payload[:12])==(b'BP3D',len(v),f.size)
  assert np.array_equal(np.frombuffer(payload,'<f4',count=v.size,offset=12).reshape(v.shape),v.astype('<f4'))
  assert np.array_equal(np.frombuffer(payload,'<f4',count=n.size,offset=12+v.size*4).reshape(n.shape),n.astype('<f4'))
  assert np.array_equal(np.frombuffer(payload,'<u4',count=f.size,offset=12+(v.size+n.size)*4).reshape(f.shape),f)
  assert np.array_equal(f,nf)
  assert sha(v.astype('<f8').tobytes())==p['source_positions_float64_sha256']
  assert sha(n.astype('<f8').tobytes())==p['source_normals_float64_sha256']
  assert sha(f.astype('<i8').tobytes())==p['source_faces_int64_sha256']
  assert p['maximum_Float32_position_error_mm']<.0001
 assert manifest['regions']['carotid-right-source']['source_assembly_anatomically_approved'] is False
 assert 'CC BY-SA2.1 Japan' in (ATLAS/'ATTRIBUTION.md').read_text()

def test_source_contexts_remain_separate_and_reach_only_their_authored_lesson():
 curr=Curriculum();ref=detail(curr,resolve('ra.carotid-obstruction'))['radiology_reference'];refs=ref['source_anatomy_references']
 assert len(refs)==2 and {r['atlas'] for r in refs}=={'bp3d-carotid-4.3','totalseg-v3-s0358'}
 for r in refs:
  assert not r['initial_cropped'];assert sha((ROOT/'web/anatomy'/r['atlas']/'manifest.json').read_bytes())==r['manifest_sha256']
 native=next(r for r in refs if r['atlas']=='totalseg-v3-s0358')
 assert 'not a dedicated carotid CTA' in native['population_note']
 assert native['source_volume']['id']=='totalseg-v3-s0358-complete-CT'
 node=copy.deepcopy(curr.node('rad.5.peripheral-vascular'));model=next(m for m in node['lesson_media'] if m.get('renderer')=='radiology-anatomy')
 assert model['props']['source_references']==refs==source_model_bindings()[node['id']]
 _validate_lesson_media(node)
 model['props']['source_references'][0]['population_note']='Registered to current patient'
 import pytest
 with pytest.raises(ValueError,match='cross-lesson|binding'):_validate_lesson_media(node)

def test_report_prompts_never_turn_unassessed_sources_into_normality_or_percentage_grading():
 ref=detail(Curriculum(),resolve('ra.carotid-obstruction'))['radiology_reference'];steps=ref['walkthrough']['steps']
 assert ref['walkthrough']['preset_mode']=='assessment-prompts'
 assert ref['walkthrough']['reviewed_at']=='2026-10-10'
 assert len(steps)==5
 for step in steps:
  text=' '.join(step['normal'].values());assert '[__]' in text and any(t in text.lower() for t in ['unassessed','unresolved','unacquired'])
  assert not any(x in text for x in ['No occlusion.','No dissection','No haemodynamically significant','Normal intracranial run-off'])
 used={i for step in steps for i in step['images']}
 assert used=={r['id'] for r in ref['structure_atlas']}
 assert 'without a threadlike full collapse' in steps[1]['tip']
 assert 'Small ICA calibre alone is insufficient' in steps[1]['tip']
 assert 'Do not calculate a routine NASCET percentage' in steps[1]['tip']
 assert 'cannot independently establish complete occlusion' in steps[2]['look']
 assert 'does not independently establish functional paralysis' in steps[3]['tip']
 assert 'does not prove functional collateral flow' in steps[4]['look']

def test_assessment_preset_contract_rejects_unknown_modes_or_filled_claims(monkeypatch):
 import pytest
 import primer.radiology_catalog as catalog
 curr=Curriculum();original=copy.deepcopy(catalog._steps())
 for mode,normal,pattern in [('unknown',None,'Unknown report preset mode'),
                             ('assessment-prompts','Arteries normal.','explicit unfilled observations')]:
  changed=copy.deepcopy(original);entry=changed['investigations']['ra.carotid-obstruction'];entry['preset_mode']=mode
  if normal is not None:entry['steps'][0]['normal']={'SITE AND MORPHOLOGY':normal}
  monkeypatch.setattr(catalog,'_steps',lambda:changed)
  with pytest.raises(ValueError,match=pattern):detail(curr,resolve('ra.carotid-obstruction'))
 monkeypatch.setattr(catalog,'_steps',lambda:original)
 assert 'preset_mode' not in detail(curr,resolve('ra.mri-sella'))['radiology_reference']['walkthrough']
