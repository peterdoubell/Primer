"""Numerical/source correspondence checks for the four algebra graph scenes.

This is a geometry implementation check, not an independent clinical or curriculum
review. It verifies emitted geometry against rational mathematical values and tests
clipping, actual point placement, mutable accepted state, and camera independence.
"""
from fractions import Fraction as F
from pathlib import Path
from math import comb, isclose, isfinite
import hashlib
import itertools
import json
import subprocess

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = r"""
global.window={}; const fs=require('fs'); require('./web/spatial-models.js');
const core=require('./web/algebra-functions-core.js');window.PrimerAlgebraFunctionsCore=core;
const spatial=require('./web/algebra-functions-spatial.js');
for(const[id,f]of Object.entries(spatial.families))window.PrimerSpatial.register({[id]:{initial:f.initialFactory(),controls:[],normalize:f.normalize,build:f.build}});
const requests=JSON.parse(fs.readFileSync(0,'utf8'));
const out=requests.map(row=>{const model=row.model||core.model(row.lesson,row.state),before=JSON.stringify(model),scene=row.view?spatial.sceneForState(model,row.view):spatial.scene(model,row.options||{});
let geometry;if(!row.options&&!row.model&&!row.view){geometry=window.PrimerSpatial.build(row.lesson,row.state);if(Object.isFrozen(geometry.state))throw Error('Accepted renderer state is frozen');}
else{const primitives=[],g={colors:{blue:'#3e7085',teal:'#317e78',gold:'#b98a2f',coral:'#b96652',plum:'#876888',green:'#5c7754',ink:'#263b46'},line:(points,color,meta={})=>primitives.push({kind:'line',points,color,...meta}),polygon:(points,color,meta={})=>primitives.push({kind:'polygon',points,color,...meta}),sphere:(p,r,color,meta={})=>primitives.push({kind:'sphere',points:[p],radius:r,color,...meta}),label:(p,text,color)=>primitives.push({kind:'label',points:[p],text,color})};geometry={primitives,...spatial.buildFromModel(model,g,row.view?{view:row.view}:row.options||{})};}
if(before!==JSON.stringify(model))throw Error('Scene mutated the exact algebra model');return{model,scene,geometry};});console.log(JSON.stringify(out));
"""


def frac(value):
    if isinstance(value, dict):
        return F(value['n'], value['d'])
    if isinstance(value, int):
        return F(value)
    return F.from_float(value)


def value(coefficients, x):
    out = F(0)
    for c in reversed(coefficients):
        out = out*x+c
    return out


def exact_bernstein(coefficients, a, b):
    """Rational conversion used only to check the entire reported error envelope."""
    n=len(coefficients)-1; h=b-a
    powers=[sum((coefficients[k]*comb(k,j)*a**(k-j)*h**j for k in range(j,n+1)),F(0))for j in range(n+1)]
    return [sum((powers[j]*F(comb(i,j),comb(n,j))for j in range(i+1)),F(0))for i in range(n+1)]


def near(a,b):
    assert isclose(a,b,rel_tol=3e-12,abs_tol=3e-12),(a,b)


def inside(p,b):
    return b['xmin']<=p[0]<=b['xmax'] and b['ymin']<=p[1]<=b['ymax']


def run(requests):
    return json.loads(subprocess.check_output(['node','-e',SCRIPT],cwd=ROOT,input=json.dumps(requests),text=True))


def main():
    presets=json.loads(subprocess.check_output(['node','-e',"const c=require('./web/algebra-functions-core.js');console.log(JSON.stringify(c.lessonIds.flatMap(lesson=>c.presets(lesson).map(p=>({lesson,state:p.state})))));"],cwd=ROOT,text=True))
    requests=list(presets)
    for a,b,c in itertools.product([-5,-1,0,1,5],repeat=3):
        requests.append({'lesson':'math.3.quadratics','state':{'a':a,'b':b,'c':c}})
    for A,B,C in itertools.product([-3,0,3],repeat=3):
        requests.append({'lesson':'math.3.slope','state':{'mode':'general','A':A,'B':B,'C':C,'relation':'perpendicular','throughX':2,'throughY':-1}})
    for a,b,c,d in itertools.product([-2,0,3],repeat=4):
        requests.append({'lesson':'math.3.linear','state':{'a':a,'b':b,'c':c,'d':d}})
    for roots in [[-2,-1,1,2],[-2,-2,2,2],[0,0,0,0],[1000,1000,1000,1000],[-1000,-999,999,1000]]:
        for leading in [-2,1,3]:
            requests.append({'lesson':'math.3.polynomials','state':{'mode':'factors','roots':roots,'leading':leading}})
    for degree in range(9):
        for sign in [-1,1]:
            coefficients=[{'n':0,'d':1}]*degree+[{'n':sign,'d':1}]
            requests.append({'model':{'lessonId':'math.3.polynomials','state':{},'summary':'Power graph','graph':{'curves':[{'id':'power','label':'Power','coefficients':coefficients}], 'points':[], 'lines':[], 'segments':[]}},'options':{'bounds':{'xmin':-2,'xmax':2,'ymin':-.5,'ymax':.5}}})
    requests.extend([
        {'lesson':'math.3.polynomials','state':{'mode':'factors','roots':[1000,1000,1000,1000]},'options':{'bounds':{'xmin':999,'xmax':1001,'ymin':-.1,'ymax':1}}},
        {'lesson':'math.3.slope','state':{'mode':'general','A':1,'B':0,'C':20},'options':{'bounds':{'xmin':-5,'xmax':5,'ymin':-5,'ymax':5}}},
        {'lesson':'math.3.quadratics','state':{'a':1,'b':0,'c':-2},'options':{'bounds':{'xmin':1,'xmax':2,'ymin':-1,'ymax':2}}},
    ])
    requests.append({'lesson':'math.3.polynomials','state':{'mode':'divide','left':['6.462','-1.36','1'],'right':['1000']}})
    for focus,radius in [('root0',.001),('root1',1e-12),('vertex',.001)]:
        requests.append({'lesson':'math.3.quadratics','state':{'a':'1/1000','b':1000,'c':'1/1000'},'view':{'chartFocus':focus,'chartRadius':radius}})
    for remainder in [-9,0,9]:
        requests.append({'lesson':'math.3.polynomials','state':{'mode':'divide','left':[remainder-4,0,1],'right':[-2,1]}})
    for numerator in [5999999999999999,6000000000000000,6000000000000001]:
        requests.append({'model':{'lessonId':'math.3.polynomials','state':{},'summary':'Near-boundary constant','graph':{'curves':[{'id':'constant','label':'Constant','coefficients':[{'n':numerator,'d':1000000000000000}]}],'points':[],'lines':[],'segments':[]}},'options':{'bounds':{'xmin':-1,'xmax':1,'ymin':-6,'ymax':6}}})
    counts={'states':0,'chords':0,'completeErrorEnvelopes':0,'omittedIntervals':0,'markers':0,'lineEndpoints':0,'projectedPrimitivePoints':0,'maxPrimitives':0,'maxCurveLeaves':0}
    for start in range(0,len(requests),15):
        for request,out in zip(requests[start:start+15],run(requests[start:start+15])):
            m,s,g=out['model'],out['scene'],out['geometry'];b=s['bounds'];gain=s['transform']['gain'];center=s['transform']['center'];assert s['transform']['planeZ']==0
            near(gain*(max(b['xmax']-b['xmin'],b['ymax']-b['ymin'])),6)
            assert len(g['primitives'])<3000;counts['maxPrimitives']=max(counts['maxPrimitives'],len(g['primitives']))
            expected_curves={c['id']:c for c in m['graph'].get('curves',[])}
            for curve in s['curves']:
                coefficients=list(map(frac,expected_curves[curve['id']]['coefficients']));intervals=[];counts['maxCurveLeaves']=max(counts['maxCurveLeaves'],curve['leaves'])
                expected_segments=[]
                for segment in curve['segments']:
                    a,bb=map(frac,segment['sourceInterval']);intervals.append((float(a),float(bb)));assert a<bb
                    error=frac(segment['chordErrorBound']);assert error<=frac(s['tolerance'])
                    for point in [segment['sourceFrom'],segment['sourceTo']]:
                        discrepancy=abs(value(coefficients,frac(point[0]))-frac(point[1]));assert discrepancy<=frac(segment['endpointRoundoffBound']),discrepancy
                    assert inside(segment['from'],b) and inside(segment['to'],b)
                    for p,t in zip([segment['from'],segment['to']],segment['t']):
                        for axis in range(2):near(p[axis],segment['sourceFrom'][axis]+t*(segment['sourceTo'][axis]-segment['sourceFrom'][axis]))
                    # Bernstein coefficients of the exact polynomial minus the
                    # ACTUAL rounded endpoint chord bound its full interval.
                    net=exact_bernstein(coefficients,a,bb);degree=len(net)-1
                    y0,y1=map(frac,[segment['sourceFrom'][1],segment['sourceTo'][1]])
                    errors=[abs(v-(y0+(y1-y0)*F(i,degree)))if degree else abs(v-y0)for i,v in enumerate(net)]
                    assert max(errors)<=error, (request,max(errors),error)
                    clipped_a,clipped_b=map(frac,[segment['from'][0],segment['to'][0]])
                    draw_net=exact_bernstein(coefficients,clipped_a,clipped_b)
                    draw_y0,draw_y1=map(frac,[segment['from'][1],segment['to'][1]])
                    draw_errors=[abs(v-(draw_y0+(draw_y1-draw_y0)*F(i,degree)))if degree else abs(v-draw_y0)for i,v in enumerate(draw_net)]
                    assert max(draw_errors)<=error,('drawn chord',request,max(draw_errors),error)
                    counts['completeErrorEnvelopes']+=1;counts['chords']+=1;expected_segments.append((segment['from'],segment['to']))
                for omitted in curve['omittedIntervals']:
                    a,bb=map(frac,[omitted['fromX'],omitted['toX']]);intervals.append((float(a),float(bb)))
                    net=exact_bernstein(coefficients,a,bb);lo,hi=map(frac,omitted['yRange']);assert min(net)>=lo and max(net)<=hi
                    if omitted['reason'].startswith('Bernstein'):
                        exact_lo,exact_hi=(F(v['n'])/F(v['d'])for v in omitted['exactYRange']);assert exact_lo==min(net)and exact_hi==max(net)
                        assert exact_hi<frac(b['ymin'])or exact_lo>frac(b['ymax'])
                    else:
                        assert omitted['resolutionLimited'] and curve['boundaryUncertain']
                        assert omitted['chordErrorBound']<=s['tolerance']
                    counts['omittedIntervals']+=1
                intervals.sort();assert intervals[0][0]==b['xmin']and intervals[-1][1]==b['xmax']
                assert all(left[1]==right[0]for left,right in zip(intervals,intervals[1:])), 'Domain interval omitted or duplicated'
                actual_segments=[(path[i-1],path[i])for path in curve['paths']for i in range(1,len(path))];assert actual_segments==expected_segments
                if curve['status']=='outside-window':assert not curve['segments']and not curve['boundaryUncertain']and all(v['reason'].startswith('Bernstein')for v in curve['omittedIntervals'])
            line_sources={l['id']:l for l in m['graph'].get('lines',[])}
            for line in s['lines']:
                orig=line_sources[line['id']];A,B,C=map(frac,[orig['A'],orig['B'],orig['C']])
                if not A and not B:assert line['status']==('all-plane'if not C else'empty')and line['segment']is None
                elif line['segment']:
                    for i,(x,y) in enumerate(line['segment']):
                        exact_x,exact_y=(F(v['n'])/F(v['d'])for v in line['exactSegment'][i]);assert A*exact_x+B*exact_y==C
                        assert frac(b['xmin'])<=exact_x<=frac(b['xmax'])and frac(b['ymin'])<=exact_y<=frac(b['ymax'])
                        assert abs(exact_x-frac(x))<=frac(line['endpointRoundoffBounds'][i][0])and abs(exact_y-frac(y))<=frac(line['endpointRoundoffBounds'][i][1])
                        assert inside([x,y],b);residual=abs(float(A)*x+float(B)*y-float(C));assert residual<=1e-9*max(1,abs(float(C)),abs(float(A)*x),abs(float(B)*y));counts['lineEndpoints']+=1
            for point,source in zip(s['points'],m['graph'].get('points',[])):
                near(point['x'],float(frac(source['x'])));near(point['y'],float(frac(source['y'])));assert point['visible']==inside([point['x'],point['y']],b);assert point['exact']==(source.get('exact')is not False);counts['markers']+=1
            assert sorted(pid for group in s['markerGroups']for pid in group['pointIds'])==sorted(p['id']for p in s['points']if p['visible'])
            assert len({(group['x'],group['y'])for group in s['markerGroups']})==len(s['markerGroups'])
            for group in s['markerGroups']:
                assert all(p['x']==group['x']and p['y']==group['y']for p in s['points']if p['id']in group['pointIds'])
            segment_sources={segment['id']:segment for segment in m['graph'].get('segments',[])}
            for segment in s['segments']:
                source=segment_sources[segment['id']]
                for key in ['from','to']:
                    assert segment['source'+key.title()]==[float(frac(v))for v in source[key]]
                if segment['visible']:
                    assert inside(segment['from'],b)and inside(segment['to'],b)
                    delta=[v-u for u,v in zip(segment['sourceFrom'],segment['sourceTo'])]
                    axis=max(range(2),key=lambda i:abs(delta[i]))
                    for point in [segment['from'],segment['to']]:
                        if delta[axis]:
                            t=(point[axis]-segment['sourceFrom'][axis])/delta[axis];assert -1e-12<=t<=1+1e-12
                            for i in range(2):near(point[i],segment['sourceFrom'][i]+t*delta[i])
                        else:assert point==segment['sourceFrom']
            def world(point):return[(point[0]-center[0])*gain,(point[1]-center[1])*gain,0]
            for primitive in g['primitives']:
                assert all(len(p)==3 and all(map(isfinite,p))for p in primitive['points'])
                counts['projectedPrimitivePoints']+=len(primitive['points'])
                if primitive.get('algebra_kind')=='curve':
                    curve=next(c for c in s['curves']if c['id']==primitive['curveId']);assert primitive['points'] in [[world(p)for p in path]for path in curve['paths']]
                if primitive.get('algebra_kind')=='line':
                    line=next(l for l in s['lines']if l['id']==primitive['lineId']);assert primitive['points']==[world(p)for p in line['segment']]
                if primitive.get('algebra_kind')=='construction':
                    segment=next(v for v in s['segments']if v['id']==primitive['segmentId']);assert segment['visible']
                    assert primitive['points']==[world(segment['from']),world(segment['to'])]
                if primitive.get('algebra_kind')=='marker':
                    point=next(p for p in s['points']if p['id']==primitive['pointId']);assert point['visible'];assert primitive['points']==[world([point['x'],point['y']])]
            if request.get('view'):
                target=next(p for p in s['points']if p['id']==request['view']['chartFocus']);assert target['visible']
                assert center==[target['x'],target['y']]and s['view']==request['view']
                assert all(p['id']==target['id']or not p['visible']for p in s['points'])
            if request.get('state',{}).get('mode')=='divide'and request.get('state',{}).get('right')==[-2,1]and request['state']['left']in [[-13,0,1],[-4,0,1],[5,0,1]]:
                remainder=request['state']['left'][0]+4;segment=next(v for v in s['segments']if v['id']=='remainder-value')
                assert segment['sourceFrom']==[2,0]and segment['sourceTo']==[2,remainder]and segment['visible']
            if request.get('model',{}).get('summary')=='Near-boundary constant':
                numerator=request['model']['graph']['curves'][0]['coefficients'][0]['n'];assert s['curves'][0]['status']==('outside-window'if numerator>6000000000000000 else'visible')
                assert s['curves'][0]['leaves']<=2
            if request.get('state',{}).get('left')==['6.462','-1.36','1']:
                dividend=next(c for c in s['curves']if c['id']=='dividend');assert dividend['status']=='visible'and dividend['segments']
            counts['states']+=1
    proof={'allPassed':True,**counts,'scope':'Emitted geometry and source-coordinate numerical checks; independent authoring and browser review remain separate','sourceSHA256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()for p in [ROOT/'web/algebra-functions-core.js',ROOT/'web/algebra-functions-spatial.js',ROOT/'web/spatial-models.js',Path(__file__)]}}
    print(json.dumps(proof))

if __name__=='__main__':main()
