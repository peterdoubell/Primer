"""Current algebra geometry preserves mathematical coordinates and domain limits."""
from pathlib import Path
import json
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]


def test_algebra_graph_geometry_source_correspondence():
    run=subprocess.run([sys.executable,str(ROOT/'tools/check_algebra_functions_spatial.py')],cwd=ROOT,text=True,capture_output=True,timeout=180)
    assert run.returncode==0,run.stdout+run.stderr
    proof=json.loads(run.stdout)
    assert proof['allPassed']
    assert proof['states']>=330
    assert proof['chords']==proof['completeErrorEnvelopes'] and proof['chords']>15000
    assert proof['omittedIntervals']>1700 and proof['markers']>800 and proof['lineEndpoints']>350
    assert proof['maxPrimitives']<3000


def test_invalid_geometry_windows_and_degenerate_lines_are_explicit():
    script=r"""
const assert=require('assert/strict'),core=require('./web/algebra-functions-core.js'),spatial=require('./web/algebra-functions-spatial.js');
const m=core.model('math.3.quadratics');
for(const bounds of [{xmin:0,xmax:0,ymin:-1,ymax:1},{xmin:0,xmax:1,ymin:2,ymax:1},{xmin:-Infinity,xmax:1,ymin:0,ymax:1}])assert.throws(()=>spatial.scene(m,{bounds}));
for(const tolerance of [0,-1,Infinity,1e99])assert.throws(()=>spatial.scene(m,{tolerance}));
for(const C of [0,1]){const s=spatial.scene(core.model('math.3.slope',{mode:'general',A:0,B:0,C}));assert.equal(s.lines[0].status,C?'empty':'all-plane');assert.equal(s.lines[0].segment,null);assert.equal(s.points.length,0);}
const off=spatial.scene(core.model('math.3.slope',{mode:'general',A:1,B:0,C:20}),{bounds:{xmin:-5,xmax:5,ymin:-5,ymax:5}});assert.equal(off.lines[0].segment,null);assert(off.points.every(p=>!p.visible));
const bad={...m,graph:{...m.graph,curves:[{id:'bad',label:'bad',coefficients:[{n:1,d:0}]}]}};assert.throws(()=>spatial.scene(bad));
const focused=core.model('math.3.quadratics',{a:'1/1000',b:1000,c:'1/1000'});
for(const view of [{chartFocus:'root0',chartRadius:.001},{chartFocus:'root1',chartRadius:1e-12},{chartFocus:'vertex',chartRadius:.001}]){const s=spatial.sceneForState(focused,view);assert(s.points.find(p=>p.id===view.chartFocus).visible);assert.deepEqual(s.transform.center,[s.focus.x,s.focus.y]);}
assert.throws(()=>spatial.viewState(focused,{chartFocus:'root0',chartRadius:1e-12}),/coordinate resolution/);
for(const chartRadius of [0,-1,1e-13,1e13,NaN,Infinity,true,''])assert.throws(()=>spatial.viewState(focused,{chartFocus:'root1',chartRadius}));
assert.throws(()=>spatial.viewState(focused,{chartFocus:'absent',chartRadius:1}));
assert.deepEqual(spatial.viewState(focused,{}),{chartFocus:'overview',chartRadius:6});
assert.deepEqual(spatial.algebraState({a:1,chartFocus:'root0',chartRadius:1}),{a:1});
const actual=spatial.families['math.3.quadratics'].normalize({...focused.state,chartFocus:'root1',chartRadius:1e-12});assert.equal(actual.chartFocus,'root1');assert.equal(actual.chartRadius,1e-12);
assert.equal(spatial.families['math.3.quadratics'].normalize(focused.state).chartFocus,'overview');
assert.deepEqual(Object.keys(spatial.families).sort(),core.lessonIds.slice().sort());
for(const id of core.lessonIds){const f=spatial.families[id];assert.equal(f.linkedStateKey,id);assert.deepEqual(f.controlsFactory(),[]);assert(!Object.isFrozen(f.normalize(f.initialFactory())));}
"""
    subprocess.run(['node','-e',script],cwd=ROOT,check=True)
