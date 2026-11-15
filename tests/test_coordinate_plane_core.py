"""Independent Fraction oracle for the authored coordinate constructions."""
from fractions import Fraction
from itertools import product
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def evaluate(states):
    script = """
const fs=require('fs'), c=require('./web/coordinate-plane-core.js');
const states=JSON.parse(fs.readFileSync(0,'utf8'));
console.log(JSON.stringify(states.map(s=>c.model(s))));
"""
    return json.loads(subprocess.check_output(
        ['node', '-e', script], input=json.dumps(states), text=True, cwd=ROOT))


def fraction(value):
    return Fraction(value['n'], value['d'])


def place(x, y):
    if x == y == 0:
        return 'origin'
    if x == 0:
        return 'y-axis'
    if y == 0:
        return 'x-axis'
    return {(True, True): 'Quadrant I', (False, True): 'Quadrant II',
            (False, False): 'Quadrant III', (True, False): 'Quadrant IV'}[x > 0, y > 0]


def test_coordinate_constructions_against_fraction_oracle():
    values = ['-3', '-1/2', '0', '1/3', '2', '5']
    states = []
    for x, y in product(values, repeat=2):
        states.append(dict(mode='plot', x=x, y=y))
        for reflection in ['x-axis', 'y-axis', 'origin', 'diagonal']:
            states.append(dict(mode='reflect', x=x, y=y, reflection=reflection))
        for a, b in product(values, repeat=2):
            states.append(dict(mode='translate', x=x, y=y, dx=a, dy=b))
            for mode in ['distance', 'rectangle']:
                states.append(dict(mode=mode, x=x, y=y, qx=a, qy=b))
    models = evaluate(states)
    assert len(models) == 4068
    for state, model in zip(states, models):
        x, y = Fraction(state['x']), Fraction(state['y'])
        result = model['result']
        assert result['location'] == place(x, y)
        assert [fraction(model['graph']['points'][0][k]) for k in ['x', 'y']] == [x, y]
        if state['mode'] == 'plot':
            assert list(map(fraction, result['swapped'])) == [y, x]
        elif state['mode'] in ['translate', 'reflect']:
            if state['mode'] == 'translate':
                expected = [x + Fraction(state['dx']), y + Fraction(state['dy'])]
            else:
                expected = {'x-axis': [x, -y], 'y-axis': [-x, y],
                            'origin': [-x, -y], 'diagonal': [y, x]}[state['reflection']]
            assert list(map(fraction, result['destination'])) == expected
            assert result['destinationLocation'] == place(*expected)
        else:
            qx, qy = Fraction(state['qx']), Fraction(state['qy'])
            dx, dy = qx - x, qy - y
            assert fraction(result['dx']) == dx
            assert fraction(result['dy']) == dy
            assert fraction(result['width']) == abs(dx)
            assert fraction(result['height']) == abs(dy)
            if state['mode'] == 'distance':
                assert fraction(result['squaredDistance']) == dx * dx + dy * dy
                assert fraction(result['axisPathLength']) == abs(dx) + abs(dy)
                assert abs(result['straightDistanceApproximation'] ** 2 - float(dx * dx + dy * dy)) < 1e-12
                if not result['straightDistance'].startswith('√'):
                    assert Fraction(result['straightDistance']) ** 2 == dx * dx + dy * dy
            else:
                assert [list(map(fraction, p)) for p in result['corners']] == [[x, y], [qx, y], [qx, qy], [x, qy]]
                assert fraction(result['area']) == abs(dx * dy)
                assert result['degenerate'] == (dx == 0 or dy == 0)
                if result['degenerate']:
                    assert result['perimeter'] is None
                else:
                    assert fraction(result['perimeter']) == 2 * (abs(dx) + abs(dy))


def test_presets_boundaries_and_invalid_inputs():
    script = """
const assert=require('assert/strict'), c=require('./web/coordinate-plane-core.js');
const presets=c.presets();
assert.deepEqual(presets.flatMap(p=>p.quizIndices).sort((a,b)=>a-b),[0,1,2,3,4,5,6,7,8,9]);
for(const p of presets) assert(Object.isFrozen(c.model(p.state).graph.points));
for(const s of [null,[],{unknown:1},{x:''},{x:'NaN'},{x:'Infinity'},{x:'1/0'},
 {x:'1001'},{x:'1/1001'},{mode:'bogus'},{reflection:'line-z'}]) assert.throws(()=>c.model(s));
const boundary=c.model({mode:'translate',x:1000,y:-1000,dx:1000,dy:-1000});
assert.deepEqual(boundary.result.destination,[{n:2000,d:1},{n:-2000,d:1}]);
assert.equal(c.model({mode:'distance',x:0,y:0,qx:1,qy:1}).result.straightDistance,'√(2)');
assert.equal(c.model({mode:'distance',x:0,y:0,qx:3,qy:4}).result.straightDistance,'5');
console.log('presets, limits, exact radicals and immutable results verified');
"""
    subprocess.run(['node', '-e', script], cwd=ROOT, check=True, capture_output=True, text=True)


def test_spatial_vertices_preserve_coordinates_and_equal_scales():
    script = """
const assert=require('assert/strict'), c=require('./web/coordinate-plane-core.js'), s=require('./web/coordinate-plane-spatial.js');
const states=c.presets().map(p=>p.state).concat([
 {mode:'rectangle',x:'1000',y:'-1000',qx:'-1000',qy:'1000'},
 {mode:'rectangle',x:'0',y:'0',qx:'0',qy:'0'},
 {mode:'plot',x:'1/1000',y:'-1/1000'},
 {mode:'translate',x:1000,y:1000,dx:1000,dy:1000}
]);
for(const state of states){
 const lines=[],markers=[],g={colors:{ink:'#000',teal:'#123',coral:'#234',plum:'#345',gold:'#456'},line:(points,color,meta)=>lines.push({points,meta}),label:()=>{},sphere:(point,r,color,meta)=>markers.push({point,meta})};
 const scene=s.build(state,g).coordinatePlaneGeometry;
 for(const line of lines)for(const vertex of line.points){assert(vertex.every(Number.isFinite));assert.equal(vertex[2],0);assert(Math.abs(vertex[0])<=3+1e-12&&Math.abs(vertex[1])<=3+1e-12);}
 for(const marker of markers)for(const id of marker.meta.pointIds){const p=scene.points.find(p=>p.id===id);assert(Math.abs(marker.point[0]/scene.gain-p.x)<1e-10);assert(Math.abs(marker.point[1]/scene.gain-p.y)<1e-10);}
 for(const line of lines.filter(l=>l.meta.coordinate_kind==='construction')){const source=scene.segments.find(s=>s.id===line.meta.segmentId);for(let i=0;i<2;i++)for(let axis=0;axis<2;axis++)assert(Math.abs(line.points[i][axis]/scene.gain-[source.from,source.to][i][axis])<1e-10);}
 assert.equal(new Set(scene.ticks.map(String)).size,scene.ticks.length);
 assert(scene.points.every(p=>Math.abs(p.x)<scene.extent&&Math.abs(p.y)<scene.extent));
}
"""
    subprocess.run(['node', '-e', script], cwd=ROOT, check=True, capture_output=True, text=True)
