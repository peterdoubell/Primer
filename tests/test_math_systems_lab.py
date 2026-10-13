"""Independent rational rank/row-operation oracle for general two-equation systems."""
from fractions import Fraction
import hashlib
import copy
import itertools
import json
from pathlib import Path
import re
import subprocess
import pytest
ROOT=Path(__file__).resolve().parents[1]


def rank(rows):
    a=[[Fraction(v) for v in row] for row in rows];r=0
    for c in range(len(a[0])):
        pivot=next((i for i in range(r,len(a)) if a[i][c]),None)
        if pivot is None:continue
        a[r],a[pivot]=a[pivot],a[r];p=a[r][c];a[r]=[v/p for v in a[r]]
        for i in range(r+1,len(a)):
            p=a[i][c];a[i]=[v-p*w for v,w in zip(a[i],a[r])]
        r+=1
        if r==len(a):break
    return r


def run(states):
    bridge="const a=require('./web/math-systems-lab.js');const fs=require('fs');console.log(JSON.stringify(JSON.parse(fs.readFileSync(0,'utf8')).map(s=>a.build(s))));"
    p=subprocess.run(['node','-e',bridge],cwd=ROOT,input=json.dumps(states),capture_output=True,text=True,check=True,timeout=90)
    return json.loads(p.stdout)


def state(values):return dict(zip(['a1','b1','c1','a2','b2','c2'],values))


def verify(values,m):
    original=[list(map(Fraction,values[:3])),list(map(Fraction,values[3:]))]
    ra=rank([r[:2] for r in original]);rab=rank(original)
    expected='none' if rab>ra else 'one' if ra==2 else 'line' if ra else 'plane'
    assert m['kind']==expected and m['rank']==ra
    if m['solution']:
        x,y=map(Fraction,m['solution'])
        assert all(a*x+b*y==c for a,b,c in original)
        assert m['residuals']==['0','0']
    else:assert expected!='one'
    sub=m['substitution']
    if sub['pivot']:
        r,c=sub['pivot']['row'],sub['pivot']['column'];free=1-c;pivot=original[r];other=original[1-r]
        constant,slope=Fraction(sub['constant']),Fraction(sub['slope'])
        for t in [Fraction(-2),Fraction(0),Fraction(3,2)]:
            pair=[None,None];pair[c]=constant+slope*t;pair[free]=t
            assert pivot[0]*pair[0]+pivot[1]*pair[1]==pivot[2]
        factor=other[c]/pivot[c]
        reduced=[v-factor*w for v,w in zip(other,pivot)]
        assert reduced[c]==0 and reduced[free]==Fraction(sub['coefficient']) and reduced[2]==Fraction(sub['rhs'])
        if m['solution']:
            pair=list(map(Fraction,m['solution']));assert Fraction(sub['coefficient'])*pair[free]==Fraction(sub['rhs'])
    else:assert all(not r[0] and not r[1] for r in original)
    current=original
    for i,step in enumerate(m['reduction']['steps']):
        op=step['operation'];n=[r[:] for r in current]
        if i:
            if op.startswith('Swap'):
                r,s=map(int,re.findall(r'\d+',op));n[r-1],n[s-1]=n[s-1],n[r-1]
            elif op.startswith('Divide'):
                match=re.fullmatch(r'Divide row (\d) by (.+)',op);r=int(match[1])-1;div=Fraction(match[2]);assert div;n[r]=[v/div for v in n[r]]
            else:
                match=re.fullmatch(r'Row (\d) ← row (\d) − \((.+)\) × row (\d)',op);assert match
                r,r_again,factor,s=match.groups();assert r==r_again;r=int(r)-1;s=int(s)-1;factor=Fraction(factor)
                n[r]=[v-factor*w for v,w in zip(n[r],n[s])]
        assert n==[[Fraction(v) for v in row] for row in step['matrix']]
        current=n
    assert current==[[Fraction(v) for v in row] for row in m['reduction']['matrix']]
    for coefficients,line,surface in zip([values[:3],values[3:]],m['lines'],m['surfaces']):
        a,b,c=coefficients;R=m['radius']
        assert line['kind']==('line' if a or b else 'empty' if c else 'plane')
        if a or b:assert len(line['points'])==2
        for x,y in line['points']:
            assert abs(a*x+b*y-c)<1e-8*max(1,(abs(a)+abs(b))*R+abs(c))
            assert abs(x)<=R+1e-7 and abs(y)<=R+1e-7
        for x,y,z in surface:
            assert z==a*x+b*y-c and abs(z)<=m['zMax']


def test_all_small_integer_ranks_and_exact_row_traces():
    values=list(itertools.product(range(-2,3),repeat=6))
    for v,m in zip(values,run([state(v) for v in values])):verify(v,m)


def test_boundaries_and_nearly_parallel_solution_outside_small_windows():
    values=[(100,99,100,99,98,-100),(-100,100,-100,100,100,100),(0,0,100,0,0,-100)]
    base=[1,1,10,1,-1,4]
    for i in range(6):
        for v in [-100,0,100]:
            row=base[:];row[i]=v;values.append(row)
    for v,m in zip(values,run([state(v) for v in values])):
        verify(v,m)
        if m['point']:assert max(map(abs,m['point']))<m['radius']


def test_quiz_examples_and_additional_degenerate_constraints():
    p=subprocess.run(['node','-e',"const a=require('./web/math-systems-lab.js');console.log(JSON.stringify(a.presets.map(p=>({id:p[0],values:p[2],model:a.build(Object.fromEntries(a.keys.map((k,i)=>[k,p[2][i]])))}))));"],cwd=ROOT,capture_output=True,text=True,check=True)
    rows=json.loads(p.stdout);assert [r['id'] for r in rows[:10]]==[f'q{i}' for i in range(1,11)]
    for r in rows:verify(r['values'],r['model'])
    assert [r['model']['solution'] for r in rows[:10]]==[['7','3'],['4','3'],None,['4','2'],['9','5'],None,['3','2'],['8','12'],['7','3'],['3','3']]
    assert [r['model']['kind'] for r in rows[-4:]]==['one','none','line','plane']


def test_invalid_input_and_unsafe_fraction_numbers():
    values=[None,[],{'a1':1.5},{'a1':1e100},{'a1':'1e2'},{'a1':'101'}]
    for m in run(values):assert m['state']['a1']==1
    p=subprocess.run(['node','-e',"const a=require('./web/math-systems-lab.js');for(const n of [1.5,1e20,Infinity,NaN]){try{a.fraction(n);throw Error('accepted unsafe Number');}catch(e){if(!(e instanceof RangeError))throw e;}}"],cwd=ROOT,capture_output=True,text=True)
    assert p.returncode==0,p.stderr


def test_only_the_original_systems_node_gains_a_companion():
    raw=(ROOT/'docs/systems-equations-fidelity-review-20261013/original-mathematics.json.txt').read_bytes()
    assert hashlib.sha256(raw).hexdigest()=='22e72a36850f61ee9e392c9097d53012121de530c8ec2ab9413467798005e9e5'
    old=json.loads(raw)
    current=json.loads((ROOT/'data/curriculum/01-mathematics.json').read_bytes())
    assert len(old['nodes'])==len(current['nodes'])
    assert {k:v for k,v in old.items() if k!='nodes'}=={k:v for k,v in current.items() if k!='nodes'}
    for before,after in zip(old['nodes'],current['nodes']):
        if before['id']!='math.3.systems':assert before==after
        else:
            assert before['quiz']==after['quiz'] and len(after['quiz'])==10
            restored=dict(after);restored['lesson_media']=restored['lesson_media'][:-1];assert before==restored
    from primer.curriculum import Curriculum,_validate_lesson_media
    n=Curriculum().node('math.3.systems');media=next(m for m in n['lesson_media'] if m.get('renderer')=='math-systems-lab')
    for change in ['node','scenario','extra-prop']:
        bad=copy.deepcopy(n);bad['lesson_media']=[copy.deepcopy(media)]
        if change=='node':bad['id']='math.3.slope'
        elif change=='scenario':bad['lesson_media'][0]['props']['scenario']='math.3.systems.other'
        else:bad['lesson_media'][0]['props']['unreviewed']=True
        with pytest.raises(ValueError,match='Systems lab must bind'):_validate_lesson_media(bad)
