import hashlib
import json
import shutil
import subprocess
from pathlib import Path
import pytest

from primer.curriculum import Curriculum
from primer import radiology_catalog
from tools.check_radiology_fidelity import digest

ROOT=Path(__file__).resolve().parents[1]
NODE='rad.5.prostate-mri'

def test_underlying_lesson_and_reporting_desk_agree_on_region_scope_and_preserve_source_limits():
    curriculum=Curriculum();node=curriculum.node(NODE)
    lesson_map=node['reference']['approach'][5]['detail']
    assert '41-region' in lesson_map and '38 prostate' in lesson_map
    assert 'two seminal-vesicle' in lesson_map and 'one external urethral-sphincter' in lesson_map
    assert 'not a patient segmentation' in lesson_map
    assert '39-sector' not in json.dumps(node)
    ref=radiology_catalog.detail(curriculum,radiology_catalog.resolve('ra.mri-prostate'))['radiology_reference']
    assert len(ref['source_anatomy_references'])==1
    assert 'not a normal whole-prostate atlas or the current patient' in ref['source_anatomy_references'][0]['population_note']
    model=next(m for m in node['lesson_media'] if m.get('renderer')=='radiology-anatomy')
    assert 'Partial schematic orientation only' in model['instructions']
    assert 'boundaries remain unverified' in model['instructions']

def test_calculations_question_types_and_ordering_survive_clinical_corrections():
    node=Curriculum().node(NODE);q=node['quiz']
    assert len(q)==15
    assert [item['kind'] for item in q]==['choice','choice','choice','choice','choice','numeric','short','choice','short','choice','numeric','numeric','order','short','short']
    assert [q[i]['answer'] for i in [5,10,11,12]]==['0.77','4','0.22','organ-confined extraprostatic-extension seminal-vesicle-invasion rectal-wall-invasion']
    for item in q:
        if item['kind']=='choice':assert item['answer'] in item['choices'] and len(set(item['choices']))==4
        if item['kind']=='short':
            assert all(keyword.lower() in item['answer'].lower() for keyword in item['keywords'])
    assert 'management still requires clinical risk' in q[1]['answer']
    assert q[3]['answer'].startswith('A suspicious') and 'not histological confirmation' in q[3]['explain']
    assert 'not confirmed histology' in q[8]['answer']
    assert 'manufacturer instructions explicitly permit' in q[9]['prompt']
    assert 'not a PI-RADS scoring input or a universal biopsy threshold' in q[11]['explain']
    assert 'clinical T staging is based on DRE' in q[12]['explain']
    assert 'not an absolute cap' in q[13]['answer'] and 'then by size' in q[13]['answer']

def test_review_is_bound_to_actual_curriculum_and_does_not_approve_full_anatomy():
    proof=json.loads((ROOT/'docs/prostate-curriculum-consistency-review/review.json').read_text())
    node=Curriculum().node(NODE)
    fields=['goal','learning_outcomes','lesson','reference','radiology_reference','visual_spec','lesson_media','model_family','model_context','practice','quiz','kid_text']
    assert proof['module_contract_after_sha256']==digest({k:node.get(k) for k in fields})
    assert proof['all15_quiz_items_reviewed'] and proof['question_kinds_and_order_preserved']
    assert not proof['clinical_or_full_anatomical_approval'] and not proof['full_curriculum_media_scope_reconciled']

@pytest.mark.skipif(shutil.which('node') is None,reason='Node.js required for shipped lesson renderer')
def test_authored_native_model_instructions_survive_async_mesh_mount():
    script=r'''
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
class Element {
  constructor(tag,text=''){this.tag=tag;this.nodeType=tag==='#text'?3:1;this.children=[];this.text=text;this.className='';}
  appendChild(child){this.children.push(child);return child;}
  append(...children){this.children.push(...children);}
  setAttribute(name,value){this[name]=value;}
  addEventListener(){}
  replaceChildren(...children){this.children=children;}
  get textContent(){return this.text+this.children.map(c=>c.textContent).join('');}
}
const native=new Element('section'),context={window:{PrimerDetailedAnatomy:{supported:()=>true,render:()=>native}},document:{createElement:tag=>new Element(tag),createTextNode:text=>new Element('#text',text)}};
vm.runInNewContext(fs.readFileSync(process.argv[1],'utf8'),context);
const instruction='Partial source anatomy; <b>is text, not markup</b>';
const result=context.window.PrimerLessonModels.render({renderer:'radiology-anatomy',instructions:instruction,props:{family:'prostate'}},{});
assert.equal(result.children[0].tag,'p');assert.equal(result.children[0].textContent,instruction);assert.equal(result.children[1],native);
native.replaceChildren(new Element('canvas'));
assert.equal(result.children[0].textContent,instruction);
assert.equal(result.children[1].children[0].tag,'canvas');
console.log('Authored instructions persist outside asynchronous native mesh mount');
'''
    result=subprocess.run(['node','-e',script,str(ROOT/'web/lesson-models.js')],capture_output=True,text=True,check=False)
    assert result.returncode==0,result.stdout+result.stderr
