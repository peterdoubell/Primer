"""Independent exact quadrature and high-precision endpoint-limit oracles.

The browser module uses polynomial antiderivatives. This oracle integrates the
same degree-at-most-two functions with exact Simpson quadrature, including
absolute area after independently finding real polynomial roots. It also tests
all rectangle coordinates, oriented widths, and derivative/anchor identities.
"""
from decimal import Decimal, localcontext
from fractions import Fraction as Q
import itertools
import json
from pathlib import Path
import random
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[1]
COEFFICIENTS = {
    'square': (0, 0, 3), 'linear': (0, 2, 0), 'signed': (-1, 0, 1),
    'velocity': (0, 6, 0), 'inflow': (1, 4, 0), 'increasing': (1, 0, 1),
    'between': (0, 1, -1),
}


def bridge(states, method='proper', compact=False):
    script = "const a=require('./web/math-integral-lab.js');const fs=require('fs');const out=JSON.parse(fs.readFileSync(0,'utf8')).map(s=>a.%s(s));" % method
    if compact:
        script += "for(const m of out){for(const k of ['integrand','accumulation','antiderivative','upperCurve','lowerCurve'])delete m[k];for(const r of m.regions||[])delete r.points;}"
    script += "console.log(JSON.stringify(out));"
    run = subprocess.run(['node', '-e', script], cwd=ROOT, input=json.dumps(states), text=True, capture_output=True, check=True, timeout=60)
    return json.loads(run.stdout)


def polynomial(example, x):
    return sum(Q(c) * x ** n for n, c in enumerate(COEFFICIENTS[example]))


def simpson(example, a, b):
    return (b-a) * (polynomial(example, a)+4*polynomial(example, (a+b)/2)+polynomial(example, b))/6


def roots(example):
    # These polynomial discriminants are perfect squares, so no root rounding
    # participates in the exact area oracle.
    c, b, a = COEFFICIENTS[example]
    if a:
        d = b*b-4*a*c
        if d < 0:
            return []
        root = int(d**.5)
        assert root*root == d
        return sorted(set([Q(-b-root, 2*a), Q(-b+root, 2*a)]))
    return [Q(-c, b)] if b else []


def close(actual, expected, tol=2e-11):
    assert actual == pytest.approx(float(expected), abs=tol, rel=tol)


def verify(state, model):
    example = state['example']
    a, b, probe = (Q(str(model['state'][k])) for k in ['a', 'b', 'cursor'])
    expected = simpson(example, a, b)
    close(model['exact'], expected)
    lo, hi = sorted([a, b])
    knots = [lo]+[x for x in roots(example) if lo < x < hi]+[hi]
    expected_area = sum(abs(simpson(example, x, y)) for x, y in zip(knots, knots[1:]))
    close(model['geometricArea'], expected_area)
    if a == b:
        assert model['average'] is None and model['regions'] == []
    else:
        close(model['average'], expected/(b-a))
        assert len(model['regions']) == len(knots)-1
        for region, left, right in zip(model['regions'], knots, knots[1:]):
            close(region['left'], left); close(region['right'], right)
            close(region['integral'], simpson(example, left, right))
            assert region['sign'] == (1 if polynomial(example, (left+right)/2)>0 else -1)
    n = state.get('count', 8)
    width = (b-a)/n
    total = Q(0)
    assert len(model['rectangles']) == n
    for i, rectangle in enumerate(model['rectangles']):
        start, end = a+i*width, a+(i+1)*width
        x = min(start, end) if state.get('method', 'midpoint') == 'left' else max(start, end) if state.get('method', 'midpoint') == 'right' else (start+end)/2
        height = polynomial(example, x)
        for k, expected_value in [('start', start), ('end', end), ('x', x), ('width', width), ('height', height), ('contribution', width*height)]:
            close(rectangle[k], expected_value)
        total += width*height
    close(model['sum'], total)
    close(model['error'], total-expected)
    close(model['splitAtProbe']['before'], simpson(example, a, probe))
    close(model['splitAtProbe']['after'], simpson(example, probe, b))
    close(model['splitAtProbe']['before']+model['splitAtProbe']['after'], expected)
    close(model['cursor']['slope'], polynomial(example, probe))
    close(model['cursor']['accumulation'], simpson(example, a, probe))
    for x, y in model['cursor']['tangent']:
        assert model['domain'][0] <= x <= model['domain'][1]
        close(y, simpson(example, a, probe)+(Q(str(x))-probe)*polynomial(example, probe))


def test_every_example_orientations_methods_and_partition_boundaries():
    states=[]
    for example, method, count, interval in itertools.product(COEFFICIENTS, ['left','midpoint','right'], [1,2,8,31,128], [(0,0),(0,1),(0,4),(4,0),(-3,4),(2,-2)]):
        if example in ['velocity','inflow'] and min(interval)<0:
            continue
        states.append(dict(example=example,method=method,count=count,a=interval[0],b=interval[1],cursor=interval[0]))
    for state, model in zip(states, bridge(states, compact=True)):
        verify(state, model)


def test_random_tenths_and_curves_are_the_same_mathematical_objects():
    rng=random.Random(20261025)
    states=[]
    for example in COEFFICIENTS:
        minimum=0 if example in ['velocity','inflow'] else -30
        for _ in range(12):
            states.append(dict(example=example,a=rng.randint(minimum,40)/10,b=rng.randint(minimum,40)/10,cursor=rng.randint(minimum,40)/10,constant=rng.randint(-20,20)/2,count=rng.randint(1,128),method=rng.choice(['left','midpoint','right'])))
    for state, model in zip(states, bridge(states)):
        verify(state,model)
        example=state['example'];a=Q(str(state['a']));constant=Q(str(state['constant']))
        for (x,y),(_,acc),(_,anti) in zip(model['integrand'],model['accumulation'],model['antiderivative']):
            x=Q(str(x));close(y,polynomial(example,x));close(acc,simpson(example,a,x));close(anti,simpson(example,Q(0),x)+constant)
        if example=='between':
            for (x,y),(_,z) in zip(model['upperCurve'],model['lowerCurve']):
                close(y,x);close(z,x*x)


def test_refinement_error_and_fundamental_theorem_cases():
    models=bridge([dict(example=k,a=0,b=b,cursor=1,count=128) for k,b in [('square',2),('linear',2),('between',1),('velocity',4),('inflow',3),('signed',2),('increasing',3)]])
    for model,exact in zip(models,[8,4,Q(1,6),48,21,Q(2,3),12]):
        close(model['exact'],exact)
        example=model['state']['example'];a=Q(str(model['state']['a']));b=Q(str(model['state']['b']))
        for row in model['convergence']:
            n=row['n'];h=(b-a)/n
            for method in ['left','midpoint','right']:
                offset={'left':Q(0),'midpoint':Q(1,2),'right':Q(1)}[method]
                expected=sum(h*polynomial(example,a+(i+offset)*h) for i in range(n))
                close(row[method],expected)
        # Quadratic midpoint errors decrease by exactly four on each doubling;
        # linear midpoint errors are identically zero.
        errors=[row['midpoint']-model['exact'] for row in model['convergence']]
        for previous,current in zip(errors,errors[1:]):
            close(previous,4*current)
    signed=bridge([dict(example='signed',a=-2,b=2)])[0]
    close(signed['exact'],Q(4,3));close(signed['geometricArea'],4)
    between=bridge([dict(example='between',a=-1,b=2)])[0]
    close(between['exact'],Q(-3,2));close(between['geometricArea'],Q(11,6))


def test_improper_separate_cutoffs_against_decimal_oracle():
    states=[dict(singular='reciprocal',leftExponent=k,rightExponent=j,path=path) for k,j,path in itertools.product([.5,1,2.4,6],[.5,3.2,6],['equal','half','square','independent'])]
    with localcontext() as context:
        context.prec=60
        for state,model in zip(states,bridge(states,'improper')):
            e=Decimal(10)**-Decimal(str(state['leftExponent']))
            r=e if state['path']=='equal' else e/2 if state['path']=='half' else e*e if state['path']=='square' else Decimal(10)**-Decimal(str(state['rightExponent']))
            close(model['left'],e.ln());close(model['right'],-r.ln());close(model['combined'],(e/r).ln())
            assert model['reciprocalConverges'] is False
            if state['path']=='equal':close(model['combined'],0)
            if state['path']=='half':close(model['combined'],Decimal(2).ln())
            if state['path']=='square':close(model['combined'],-e.ln())
            for row in model['rows']:
                eps=Decimal(10)**-row['exponent']
                right=eps if state['path']=='equal' else eps/2 if state['path']=='half' else eps*eps if state['path']=='square' else r
                close(row['left'],eps.ln());close(row['right'],-right.ln());close(row['combined'],(eps/right).ln())


def test_endpoint_power_threshold_and_explicit_missing_area():
    states=[dict(singular='power',power=p,leftExponent=k) for p,k in itertools.product([.25,.5,.95,1-1e-9,1,1+1e-9,1.5,2],[.5,1,3,6])]
    with localcontext() as context:
        context.prec=60
        for state,model in zip(states,bridge(states,'improper')):
            p=Decimal(str(state['power']));e=Decimal(10)**-Decimal(str(state['leftExponent']))
            expected=-e.ln() if p==1 else (1-e**(1-p))/(1-p)
            close(model['powerIntegral'],expected)
            assert model['powerConverges']==(p<1)
            if p<1:
                close(model['powerLimit'],1/(1-p),tol=1e-7 if p>Decimal('.999') else 2e-11)
                close(model['powerRemainder'],e**(1-p)/(1-p),tol=1e-7 if p>Decimal('.999') else 2e-11)
                close(model['powerIntegral']+model['powerRemainder'],model['powerLimit'],tol=1e-7)
            else:
                assert model['powerLimit'] is None and model['powerRemainder'] is None
    zero=bridge([dict(singular='power',power=.5,leftExponent=6)],'improper')[0]
    close(zero['powerIntegral'],Q(1998,1000));close(zero['powerRemainder'],Q(2,1000))


def test_invalid_inputs_cannot_create_nonfinite_geometry():
    values=[None,[],{'example':'toString','a':'2'},{'a':-1e50,'b':1e50,'constant':99,'count':0},{'count':1.5,'method':'unknown'}, {'example':'velocity','a':-1,'b':-2,'cursor':-3}]
    for model in bridge(values):
        assert model['state']['example'] in COEFFICIENTS
        assert 1 <= model['state']['count'] <= 128
        assert 'NaN' not in json.dumps(model) and 'Infinity' not in json.dumps(model)
        if model['state']['example']=='velocity':
            assert min(model['state'][k] for k in ['a','b','cursor'])>=0
