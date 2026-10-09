"""Teaching must retain source uncertainty and deliver the same original evidence as the reporting desk."""
import copy
import json
import shutil
import subprocess
from pathlib import Path

import pytest

from primer.curriculum import Curriculum, _validate_lesson_media
from primer import radiology_catalog
from tools.msk_runtime_rights import reference_images

ROOT = Path(__file__).resolve().parents[1]
NODE = 'rad.5.rectal-mr'
IDS = ['ra.mri-rectal-cancer', 'ra.mri-perianal-fistula']


def test_assessment_order_calculations_and_short_answer_scoring_are_preserved():
    node = Curriculum().node(NODE)
    quiz = node['quiz']
    assert len(quiz) == 13
    assert [q['kind'] for q in quiz] == ['choice'] * 6 + ['numeric'] * 3 + ['short'] * 3 + ['order']
    assert [quiz[i]['answer'] for i in (6, 7, 8)] == ['0.8', '11', '4']
    assert quiz[12]['answer'] == 'fibrosis-only dense-fibrosis-with-minimal-residual-signal over-half-fibrosis-with-visible-tumour-signal little-fibrosis-mostly-tumour-signal tumour-signal-unchanged-or-larger'
    for q in quiz:
        if q['kind'] == 'choice':
            assert q['answer'] in q['choices'] and len(set(q['choices'])) == 4
        elif q['kind'] == 'short':
            assert all(k.lower() in q['answer'].lower() for k in q['keywords'])


def test_baseline_and_response_teaching_do_not_infer_pathology_or_treatment():
    node = Curriculum().node(NODE)
    q = node['quiz']
    assert q[1]['answer'].startswith('MRF involved') and 'multidisciplinary' in q[1]['answer']
    assert 'smooth-margin node' in q[6]['explain'] and 'not the measured pathological CRM' in q[6]['explain']
    assert 'suspicious' in q[3]['answer'] and 'proven malignant histology' in q[3]['explain']
    assert 'strongly suspected' in q[5]['answer'] and 'prescribe resection' in q[5]['explain']
    assert 'negative superficial biopsy' in q[9]['answer']
    assert 'remain unassessed' in q[10]['answer'] and 'does not prove' in q[10]['answer']
    assert 'cannot accurately identify complete responders' in q[12]['explain']
    ref = node['reference']
    assert ref['source']['url'].endswith('/PMC13212678/')
    lateral = next(m for m in ref['measure'] if m['what'] == 'Baseline lateral nodes')
    assert '7 mm or more for both' in lateral['cutoff'] and 'No recommended lateral-node' in lateral['cutoff']
    assert 'No automatic histological diagnosis' in ref['template']
    model = next(m for m in node['lesson_media'] if m.get('renderer') == 'radiology-anatomy')
    assert 'Partial schematic orientation only' in model['instructions']


@pytest.mark.parametrize('change', ['unknown', 'cross_lesson', 'duplicate', 'empty', 'too_many', 'url_override'])
def test_source_gallery_rejects_unreviewed_or_cross_lesson_media(change):
    node = copy.deepcopy(Curriculum().node(NODE))
    media = next(m for m in node['lesson_media'] if m['kind'] == 'source-gallery')
    if change == 'unknown':
        media['investigation_ids'] = ['ra.not-real']
    elif change == 'cross_lesson':
        media['investigation_ids'] = ['ra.mri-prostate']
    elif change == 'duplicate':
        media['investigation_ids'] = [IDS[0], IDS[0]]
    elif change == 'empty':
        media['investigation_ids'] = []
    elif change == 'too_many':
        media['investigation_ids'] = IDS * 3
    else:
        media['url'] = 'https://example.com/unreviewed.png'
    with pytest.raises(ValueError):
        _validate_lesson_media(node)


def test_all_original_gallery_roles_are_audited_on_the_actual_lesson_surface():
    curriculum = Curriculum()
    inventory = reference_images(curriculum, radiology_catalog.catalogue(),
                                 {'additional_scope': [{'module_id': NODE}]},
                                 radiology_catalog.detail, catalog_section=None)
    rows = [r for r in inventory['images'] if any(
        u['surface'] == 'lesson:' + NODE and u['id'].startswith('open-anorectal-')
        for u in r['uses'] if u.get('id'))]
    assert len(rows) == 26
    assert sum(u['surface'] == 'lesson:' + NODE and u['collection'] == 'structure_atlas'
               for r in rows for u in r['uses']) == 30
    assert any('pmc13512459-fig1.webp' in r['src'] for r in rows)


@pytest.mark.skipif(shutil.which('node') is None, reason='Node.js required for shipped gallery loader')
def test_gallery_is_lazy_keeps_all_evidence_roles_and_retries_only_missing_readers():
    script = r'''
const assert=require('node:assert/strict');
global.window={addEventListener(){}};global.document={addEventListener(){}};
const {lessonSourceGallery}=require('./web/app.js');
class Element {
  constructor(tag,props={},...children){this.tag=tag;Object.assign(this,props);this.children=[];this.append(...children);}
  append(...children){for(const c of children){const i=this.children.indexOf(c);if(i>=0)this.children.splice(i,1);this.children.push(c);}}
}
const calls=[], rendered=[], wired=[];let retry=false;
const create=(tag,props,...children)=>new Element(tag,props,...children);
const references={a:{id:'a',title:'Reader A',radiology_reference:{structure_atlas:[{id:'MRI',kind:'clinical-image'},{id:'drawing',kind:'schematic'}]}},
                  b:{id:'b',title:'Reader B',radiology_reference:{structure_atlas:[{id:'specimen',kind:'clinical-image',ancillary_panels:[{kind:'Anatomical specimen photograph'}]}]}}};
const gallery=lessonSourceGallery({title:'Original sources',instructions:'Separate source cases',investigation_ids:['a','b']},
  {createElement:create,createButton:(props,text)=>create('button',props,text),
   loadReference:async id=>{calls.push(id);if(id==='b'&&!retry)throw Error('temporary failure');return references[id];},
   renderFigure:asset=>{rendered.push(asset);return create('figure',{},asset.id);},wirePictures:section=>wired.push(section)});
assert.equal(calls.length,0);const button=gallery.children.find(c=>c.tag==='button');
(async()=>{
 await button.onclick();assert.deepEqual(calls,['a','b']);assert.equal(button.disabled,false);
 assert.equal(gallery.children.filter(c=>c.tag==='details').length,1);assert.equal(rendered[1].kind,'schematic');
 retry=true;await button.onclick();assert.deepEqual(calls,['a','b','b']);assert.equal(button.disabled,true);
 assert.equal(gallery.children.filter(c=>c.tag==='details').length,2);assert.equal(wired.length,2);
 assert.equal(rendered[2].ancillary_panels[0].kind,'Anatomical specimen photograph');
 assert.deepEqual(gallery.children.filter(c=>c.tag==='details').map(c=>c.children[0].children[0]),['Reader A · 2 source references','Reader B · 1 source references']);
 const wrong=lessonSourceGallery({title:'Sources',instructions:'Separate cases',investigation_ids:['a']},
   {createElement:create,createButton:(props,text)=>create('button',props,text),loadReference:async()=>references.b,
    renderFigure:()=>{throw Error('must not render an unrelated reader');},wirePictures:()=>{}});
 await wrong.children.find(c=>c.tag==='button').onclick();assert.equal(wrong.children.filter(c=>c.tag==='details').length,0);
 console.log('Lazy gallery, full source roles, bounded retry and wrong-reader rejection passed');
})().catch(error=>{console.error(error);process.exitCode=1;});
'''
    result = subprocess.run(['node', '-e', script], cwd=ROOT, text=True, capture_output=True)
    assert result.returncode == 0, result.stdout + result.stderr
