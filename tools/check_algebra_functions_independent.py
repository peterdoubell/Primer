"""Independent Fraction/Decimal oracle for the shipped algebra models.

Builds expectations from equations and polynomial identities in Python, then
compares the JavaScript core through a data-only stdin bridge. No proof files
are rewritten by this executable.
"""
from decimal import Decimal, localcontext
from fractions import Fraction as F
from itertools import product
from pathlib import Path
import hashlib
import ast
import json
import math
import random
import subprocess

ROOT=Path(__file__).resolve().parents[1]
NODE="""const fs=require('fs'),c=require('./web/algebra-functions-core.js');const input=JSON.parse(fs.readFileSync(0,'utf8'));console.log(JSON.stringify(input.map(q=>{try{const m=c.model(q.id,q.state);return {state:m.state,result:m.result,graph:m.graph};}catch(e){return {error:e.message};}})));"""

def rational(x):
    if isinstance(x,dict):
        assert set(x)=={'n','d'} and isinstance(x['n'],int) and isinstance(x['d'],int)
        assert x['d']>0 and math.gcd(x['n'],x['d'])==1
        return F(x['n'],x['d'])
    return F(str(x))

def trim(p):
    p=list(p)
    while len(p)>1 and not p[-1]:p.pop()
    return p

def multiply(a,b):
    return trim([sum((a[i]*b[k-i]for i in range(len(a))if 0<=k-i<len(b)),F(0))for k in range(len(a)+len(b)-1)])

def plus(a,b):
    return trim([(a[i]if i<len(a)else F(0))+(b[i]if i<len(b)else F(0))for i in range(max(len(a),len(b)))])

def decimal(f):return Decimal(f.numerator)/Decimal(f.denominator)

def main():
    rng=random.Random(20261027);cases=[];checks=0
    def add(kind,state,expected=None,error=False):cases.append({'id':'math.3.'+kind,'state':state,'expected':expected,'error':error})
    for a,b,c,d in product(range(-2,3),repeat=4):
        for stage in [0,1,2,3]:add('linear',{'a':a,'b':b,'c':c,'d':d,'step':stage,'testX':'2/3'})
    for _ in range(300):
        state={k:str(F(rng.randint(-10,10),rng.randint(1,7)))for k in ['a','b','c','d','leftScale','rightScale','testX']};state['step']=rng.randrange(4);add('linear',state)
    for x1,y1,x2,y2 in product(range(-2,3),repeat=4):
        add('slope',{'mode':'points','x1':x1,'y1':y1,'x2':x2,'y2':y2,'atX':'1/3'},error=(x1,y1)==(x2,y2))
    for a,b,c in product(range(-3,4),repeat=3):
        for relation in ['none','parallel','perpendicular']:
            add('slope',{'mode':'general','A':a,'B':b,'C':c,'atX':'2/3','relation':relation,'throughX':'-2/3','throughY':'5/7'})
    for m,x,y in product(range(-3,4),repeat=3):add('slope',{'mode':'point-slope','m':m,'x1':x,'y1':y,'atX':5})
    for a,b,c in product(range(-4,5),range(-6,7),range(-6,7)):add('quadratics',{'a':a,'b':b,'c':c})
    for a,b,c in [('1/1000','1000','1/1000'),('-1/1000','1000','-1/1000'),('1/3','2/7','-5/11'),('1/1000','0','-1000'),('1000','0','-1/1000')]:add('quadratics',{'a':a,'b':b,'c':c})
    for _ in range(350):
        p=[F(rng.randint(-7,7),rng.randint(1,5))for _ in range(rng.randrange(1,5))]
        q=[F(rng.randint(-5,5),rng.randint(1,5))for _ in range(rng.randrange(1,5))]
        for mode in ['add','multiply']:add('polynomials',{'mode':mode,'left':list(map(str,p)),'right':list(map(str,q))},plus(p,q)if mode=='add'else multiply(p,q))
    # Construct P=DQ+R independently; uniqueness fixes the expected quotient.
    for _ in range(350):
        divisor=trim([F(rng.randint(-4,4))for _ in range(rng.randrange(1,4))])
        if divisor==[0]:divisor=[F(1)]
        quotient=trim([F(rng.randint(-4,4))for _ in range(rng.randrange(1,6-len(divisor)))])
        remainder=trim([F(rng.randint(-3,3))for _ in range(max(1,len(divisor)-1))])if len(divisor)>1 else[F(0)]
        dividend=plus(multiply(divisor,quotient),remainder)
        add('polynomials',{'mode':'divide','left':list(map(str,dividend)),'right':list(map(str,divisor))},(quotient,remainder))
    for roots in list(product(range(-3,4),repeat=2))+list(product(range(-2,3),repeat=3)):
        expected=[F(-2)]
        for root in roots:expected=multiply(expected,[F(-root),F(1)])
        add('polynomials',{'mode':'factors','roots':list(roots),'leading':-2},expected)
    for a,b,c in product([-2,-1,1,2],range(-4,5),range(-4,5)):add('polynomials',{'mode':'factor-quadratic','left':[c,b,a]})
    # Exhaust every input tuple used by the three unchanged procedural generators.
    practice_start=len(cases)
    for x,a,b in product(range(-9,10),[2,3,4,5,-2,-3],range(-10,11)):
        add('linear',{'a':a,'b':b,'c':0,'d':a*x+b,'testX':x},F(x))
    for x1,y1,x2,m in product(range(-5,6),range(-5,6),range(-5,6),[-3,-2,-1,1,2,3]):
        if x1!=x2:add('slope',{'mode':'points','x1':x1,'y1':y1,'x2':x2,'y2':y1+m*(x2-x1),'atX':x2},F(m))
    for r1,r2 in product(range(-6,7),repeat=2):
        add('quadratics',{'a':1,'b':-(r1+r2),'c':r1*r2},sorted({F(r1),F(r2)}))
    practice_cases=len(cases)-practice_start
    invalid=[('linear',{'a':''}),('linear',{'a':'NaN'}),('linear',{'a':'1/0'}),('linear',{'a':True}),('linear',{'a':1001}),('linear',{'a':'1/1001'}),('linear',{'step':4}),('slope',{'mode':'other'}),('quadratics',{'extra':0}),('polynomials',{'mode':'divide','right':[0]}),('polynomials',{'mode':'factor-quadratic','left':[1,2,3,4]}),('polynomials',{'mode':'factors','roots':[]})]
    for kind,state in invalid:add(kind,state,error=True)
    bridge=[{k:q[k]for k in ['id','state']}for q in cases]
    run=subprocess.run(['node','-e',NODE],input=json.dumps(bridge),cwd=ROOT,text=True,capture_output=True,check=True,timeout=180)
    results=json.loads(run.stdout);assert len(results)==len(cases)
    error_count=0
    for case,out in zip(cases,results):
        if case['error']:
            assert 'error'in out,(case,out);error_count+=1;checks+=1;continue
        assert 'error'not in out,(case,out)
        s=out['state'];r=out['result'];kind=case['id'].split('.')[-1]
        if kind=='linear':
            a,b,c,d,ls,rs,x=[rational(s[k])for k in ['a','b','c','d','leftScale','rightScale','testX']]
            A=ls*a-rs*c;B=rs*d-ls*b;expected_kind='unique'if A else'none'if B else'infinite'
            assert r['kind']==expected_kind and rational(r['A'])==A and rational(r['B'])==B
            assert rational(r['trial']['left'])==ls*(a*x+b)and rational(r['trial']['right'])==rs*(c*x+d)
            assert r['trial']['equal']==(ls*(a*x+b)==rs*(c*x+d));checks+=6
            if A:
                assert rational(r['solution'])==B/A
                if case['expected']is not None:assert rational(r['solution'])==case['expected'];checks+=1
                assert rational(r['verification']['left'])==rational(r['verification']['right'])==ls*(a*B/A+b)
                assert rational(r['parameterRule']['coefficient'])==rs/A and rational(r['parameterRule']['constant'])==-ls*b/A;checks+=4
            else:assert r['solution']is None;checks+=1
            stage=r['selectedStage'];la,lb,ra,rb=[rational(stage[k])for k in ['leftA','leftB','rightA','rightB']]
            for z in [F(-7,3),F(0),F(8,5),B/A if A else F(17)]:
                assert (la*z+lb==ra*z+rb)==(ls*(a*z+b)==rs*(c*z+d));checks+=1
            assert [[rational(v)for v in p['coefficients']]for p in out['graph']['curves']]==[trim([lb,la]),trim([rb,ra])];checks+=1
        elif kind=='slope':
            if s['mode']=='general':A,B,C=[rational(s[k])for k in ['A','B','C']]
            elif s['mode']=='point-slope':
                m,x,y=[rational(s[k])for k in ['m','x1','y1']];A,B,C=m,F(-1),m*x-y
            else:
                x,y,u,v=[rational(s[k])for k in ['x1','y1','x2','y2']];A,B,C=v-y,x-u,(v-y)*x+(x-u)*y
            assert [rational(r[k])for k in ['A','B','C']]==[A,B,C];checks+=3
            if B:assert rational(r['slope'])==-A/B
            else:assert r['slope']is None
            if case['expected']is not None:assert rational(r['slope'])==case['expected'];checks+=1
            z=rational(s['atX']);e=r['evaluation']
            if B:assert e['kind']=='one'and rational(e['y'])==(C-A*z)/B
            else:assert e['kind']==('all'if A*z==C else'none')and e['y']is None
            checks+=3
            if r['related']:
                ra,rb,rc=[rational(r['related'][k])for k in ['A','B','C']];px,py=[rational(s[k])for k in ['throughX','throughY']]
                assert ra*px+rb*py==rc
                assert A*rb-B*ra==0 if s['relation']=='parallel'else A*ra+B*rb==0;checks+=2
        elif kind=='quadratics' or kind=='polynomials'and s['mode']=='factor-quadratic':
            if kind=='quadratics':a,b,c=[rational(s[k])for k in ['a','b','c']];q=r
            else:
                p=[rational(v)for v in s['left']]+[F(0)]*3;c,b,a=p[:3];q=r['factoring']
            if kind=='polynomials':
                assert [rational(v)for v in r['coefficients']]==trim([c,b,a]);checks+=1
                assert r['factorization']['realLinearFactors']==bool(a and b*b-4*a*c>=0 or not a and b);checks+=1
                if q['roots'] and all(z['exact']for z in q['roots']):
                    reconstructed=[a if a else b]
                    for z in q['roots']:
                        for _ in range(z['multiplicity']):reconstructed=multiply(reconstructed,[-rational(z['value']),F(1)])
                    assert reconstructed==trim([c,b,a]);checks+=1
            if not a:
                expected='linear'if b else'nonzero-constant'if c else'zero-polynomial';assert q['kind']==expected;assert q['rootSum']is None and q['rootProduct']is None;checks+=3
                if b:assert rational(q['roots'][0]['value'])==-c/b;checks+=1
                continue
            D=b*b-4*a*c;h=-b/(2*a);k=c-b*b/(4*a)
            assert rational(q['discriminant'])==D and rational(q['vertex']['x'])==h and rational(q['vertex']['y'])==k;checks+=3
            assert rational(q['rootSum'])==-b/a and rational(q['rootProduct'])==c/a;checks+=2
            assert q['realRootCount']==(2 if D>0 else 1 if D==0 else 0);checks+=1
            if D<0:assert q['roots']==[];checks+=1;continue
            if kind=='quadratics'and case['expected']is not None:assert [rational(z['value'])for z in q['roots']]==case['expected'];checks+=len(q['roots'])
            with localcontext()as ctx:
                ctx.prec=70;da,db,dc,dd=map(decimal,[a,b,c,D]);sqrt=dd.sqrt()
                expected=sorted([(-db-sqrt)/(2*da),(-db+sqrt)/(2*da)])
                if D==0:expected=expected[:1]
                for index,(row,value) in enumerate(zip(q['roots'],expected)):
                    if row['exact']:
                        exact_root=rational(row['value']);assert a*exact_root*exact_root+b*exact_root+c==0
                        actual=decimal(exact_root)
                    else:
                        actual=Decimal(str(row['value']));sign=(['−','+']if a>0 else['+','−'])[index]
                        assert row['expression']==f'({-b} {sign} √({D})) / ({2*a})';checks+=1
                    assert abs(actual-value)<=max(Decimal('1e-15'),abs(value)*Decimal('3e-15')),(case,actual,value)
                    assert row['multiplicity']==(2 if D==0 else 1);checks+=3
        else:
            coefficients=[rational(v)for v in r['coefficients']]
            if s['mode']=='divide':
                Q,rem=case['expected'];assert coefficients==Q and [rational(v)for v in r['remainder']]==rem;checks+=2
                assert plus(multiply([rational(v)for v in r['inputRight']],Q),rem)==[rational(v)for v in r['inputLeft']];checks+=1
                divisor=[rational(v)for v in r['inputRight']];theorem=r['remainderTheorem']
                if len(divisor)==2:
                    root=-divisor[0]/divisor[1];value=sum((v*root**i for i,v in enumerate([rational(v)for v in r['inputLeft']])),F(0))
                    assert rational(theorem['root'])==root and rational(theorem['polynomialValue'])==value and rational(theorem['remainder'])==rem[0] and rational(theorem['divisorValue'])==0 and theorem['equality']is True;checks+=5
                    points={p['id']:p for p in out['graph']['points']}
                    assert [rational(points['remainder-dividend'][k])for k in ['x','y']]==[root,value]and [rational(points['remainder-divisor'][k])for k in ['x','y']]==[root,F(0)];checks+=4
                else:assert theorem is None;checks+=1
            else:assert coefficients==case['expected'];checks+=1
            degree=None if coefficients==[0]else len(coefficients)-1;assert r['degree']==degree;checks+=1
            if degree and degree>0:
                sign=1 if coefficients[-1]>0 else-1
                assert r['endBehavior']['right']==('up'if sign>0 else'down')and r['endBehavior']['left']==('up'if sign*(-1)**degree>0 else'down');checks+=2
    practice_source=(ROOT/'primer/practice.py').read_text();tree=ast.parse(practice_source);practice_hashes={n.name:hashlib.sha256(ast.get_source_segment(practice_source,n).encode()).hexdigest()for n in tree.body if isinstance(n,ast.FunctionDef)and n.name in ['g_linear_eq','g_slope','g_quadratics']}
    report={'allPassed':True,'models':len(cases),'practiceCases':practice_cases,'practiceFunctionSHA256':practice_hashes,'checks':checks,'explicitRejections':error_count,'method':'Independent Python Fraction equations, constructed polynomial division identities and 70-digit Decimal roots','sourceSHA256':hashlib.sha256((ROOT/'web/algebra-functions-core.js').read_bytes()).hexdigest(),'oracleSHA256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'wholeGoalComplete':False}
    print(json.dumps(report))

if __name__=='__main__':main()
