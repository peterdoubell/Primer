"""Mechanics lab evidence checks actual equations and independent trajectories."""
import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
pytestmark = pytest.mark.skipif(shutil.which('node') is None, reason='Node.js required for mechanics models')

def test_independent_rational_and_differential_equation_oracles():
    result = subprocess.run([sys.executable, 'tools/check_energy_momentum_independent.py'], cwd=ROOT,
                            text=True, capture_output=True, check=True, timeout=60)
    proof = json.loads(result.stdout)
    assert proof['allPassed'] is True
    assert proof['cases'] == {'collision':729, 'impulse':405, 'work':305, 'power':27}
    assert proof['trajectoryChecks'] >= 11000


def test_mechanics_parameter_domains_and_physical_boundary_events():
    script = r"""
const assert=require('node:assert/strict'),l=require('./web/energy-momentum-lab.js');
for(const bad of [{massA:0},{massB:Infinity},{massA:'2'},{frame:NaN},{restitution:1.01},{duration:0},{friction:-1},{watts:-1},{workTime:11},{mode:'unknown'},{hiddenSwitch:true}])assert.throws(()=>l.build(bad));
for(const c of l.controls){assert.throws(()=>l.build({[c.key]:c.min-1}));assert.throws(()=>l.build({[c.key]:c.max+1}));}
assert.equal(l.render({renderer:'physics-concept-lab',props:{scenario:'phys.3.mechanics'}}),null);
assert.equal(l.render({renderer:'physics-concept-lab',props:{scenario:l.scenario,extra:true}}),null);
assert.equal(l.render({renderer:'spatial-3d',props:{scenario:l.scenario}}),null);
const held=l.work({mass:20,gravity:10,angle:0,force:100,friction:.5,initialVelocity:0,workTime:10});
assert.equal(held.current.q,0);assert.equal(held.current.appliedWork,0);assert.equal(held.current.frictionForce,-100);
const moving=l.work({...held.state,force:100-1e-10,initialVelocity:1,workTime:10});assert(moving.current.v>0);
const stopped=l.work({mass:2,gravity:10,angle:0,force:0,friction:.2,initialVelocity:4,workTime:3});
assert.equal(stopped.current.q,4);assert.equal(stopped.current.v,0);assert.equal(stopped.current.Q,16);
const reverse=l.work({mass:2,gravity:10,angle:30,force:0,friction:.1,initialVelocity:4,workTime:2});assert(reverse.current.v<0);assert(reverse.current.length>Math.abs(reverse.current.q));
const noEvent=l.collision({velocityA:-6,velocityB:6});assert.equal(noEvent.eventTime,null);assert.equal(noEvent.impulse,0);
const equal=l.collision({velocityA:6,velocityB:6});assert.equal(equal.eventTime,null);assert.equal(equal.lost,0);
const elastic=l.collision({massA:2,massB:2,velocityA:4,velocityB:0,restitution:1});assert.equal(elastic.vA,0);assert.equal(elastic.vB,4);assert.equal(elastic.lost,0);
const short=l.impulse({duration:.01}),long=l.impulse({duration:.2});assert.equal(short.J,long.J);assert.equal(short.peak/long.peak,20);
const zero=l.impulse({incoming:0,outgoing:0});assert(zero.points.every(p=>p.force===0&&p.impulse===0&&p.kinetic===0));
const off=l.power({watts:0});assert(off.points.every(p=>p.input===0&&p.useful===0&&p.other===0));
const crane=l.work({mass:250,initialVelocity:1,force:2500,angle:90,gravity:10,friction:0,workTime:8});assert.equal(crane.N,0);assert.equal(crane.current.height,8);assert.equal(crane.current.appliedWork,20000);assert.equal(crane.current.K,125);
const car=l.work({mass:1500,initialVelocity:20,force:0,angle:0,friction:0,workTime:0});assert.equal(car.current.K,300000);
console.log('mechanics boundary and domain checks passed');
"""
    result = subprocess.run(['node','-e',script], cwd=ROOT,text=True,capture_output=True,timeout=30)
    assert result.returncode == 0, result.stderr


def test_energy_lesson_has_worked_example_and_preserves_assessment():
    from primer.curriculum import Curriculum
    node = Curriculum().node('phys.3.energy-work')
    assert len(node['quiz']) == 10
    assert len(node['learning_outcomes']) == 6
    assert 'centre-of-mass' in node['lesson']['worked_example']
    model = next(item for item in node['lesson_media'] if item['kind']=='model')
    assert model['renderer'] == 'physics-concept-lab'
    assert model['props'] == {'scenario':'phys.3.energy-work'}
