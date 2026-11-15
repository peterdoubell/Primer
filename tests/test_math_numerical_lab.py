"""Independent high-precision references, IEEE operations and exact error accounts."""
import copy,json,math,shutil,struct,subprocess
from decimal import Decimal,localcontext
from fractions import Fraction
from pathlib import Path
import pytest
from primer.curriculum import Curriculum,_validate_lesson_media
ROOT=Path(__file__).resolve().parents[1]
def node(script):
 p=subprocess.run(['node','-e',script],cwd=ROOT,text=True,capture_output=True,timeout=40);assert p.returncode==0,p.stdout+p.stderr;return json.loads(p.stdout)
def rational(r):return Fraction(int(r['n']),int(r['d']))
def decimal(r):return Decimal(int(r['n']))/Decimal(int(r['d']))
def f32(x):return struct.unpack('f',struct.pack('f',x))[0]

@pytest.mark.skipif(shutil.which('node') is None,reason='Node required')
def test_exact_float_decoding_and_independent_rounded_sums():
 data=node("const a=require('./web/math-numerical-lab.js');const rows=[];for(const p of [32,64])for(const n of [1,2,3,7,10,11,31,100,999,1000]){const m=a.build({mode:'sum',precision:p,count:n});rows.push({p,n,input:m.input,naive:m.naive,comp:m.compensated,target:m.target,bias:m.dataError,round:m.naiveRound,compRound:m.compRound});}console.log(JSON.stringify(rows,(_k,v)=>typeof v==='bigint'?v.toString():v));")
 for row in data:
  q=f32 if row['p']==32 else float;input=q(.1);naive=comp=c=0.
  for _ in range(row['n']):
   naive=q(naive+input);y=q(input-c);t=q(comp+y);c=q(q(t-comp)-y);comp=t
  assert row['naive']==naive and row['comp']==comp
  target=Fraction(row['n'],10);stored=Fraction.from_float(input)*row['n'];assert rational(row['target'])==target
  assert rational(row['bias'])==stored-target
  assert rational(row['round'])==Fraction.from_float(naive)-stored
  assert rational(row['compRound'])==Fraction.from_float(comp)-stored
 floats=node("const a=require('./web/math-numerical-lab.js');console.log(JSON.stringify([.1,-.1,1,1000,Number.MIN_VALUE,Number.MAX_VALUE].map(x=>({x,r:a.fromFloat(x)})),(_k,v)=>typeof v==='bigint'?v.toString():v));")
 for row in floats:assert rational(row['r'])==Fraction.from_float(row['x'])

@pytest.mark.skipif(shutil.which('node') is None,reason='Node required')
def test_decimal_roots_and_outward_display_bounds_are_independent_of_algorithm():
 data=node("const a=require('./web/math-numerical-lab.js');const rows=[];for(const p of [32,64])for(let k=1;k<=16;k++){const m=a.quadratic(k,p);rows.push({p,k,...m,storedBRational:a.fromFloat(m.storedB),printedNaive:[a.decimalBound(m.naiveError.relativeLowRat),a.decimalBound(m.naiveError.relativeHighRat,true)],printedStable:[a.decimalBound(m.stableError.relativeLowRat),a.decimalBound(m.stableError.relativeHighRat,true)]});}console.log(JSON.stringify(rows,(_k,v)=>typeof v==='bigint'?v.toString():v));")
 with localcontext() as ctx:
  ctx.prec=210
  for row in data:
   B=Decimal(2)*Decimal(10)**row['k'];truth=(B-(B*B-4).sqrt())/2
   assert decimal(row['certificate']['low'])<truth<decimal(row['certificate']['high'])
   for kind,printed in [('naive','printedNaive'),('stable','printedStable')]:
    actual=Decimal.from_float(row[kind])-truth;bounds=row[kind+'Error']
    assert decimal(bounds['low'])<=actual<=decimal(bounds['high'])
    relative=abs(actual)/truth;assert Decimal(row[printed][0])<=relative<=Decimal(row[printed][1])
    assert relative>0
   q=f32 if row['p']==32 else float;b=q(float(B));D=q(q(b*b)-4);sq=q(math.sqrt(D));naive=q(q(b-sq)/2);large=q(q(b+sq)/2);stable=q(1/large)
   assert row['naive']==naive and row['stable']==stable and float(row['storedB'])==b and rational(row['storedBRational'])==Fraction.from_float(b)
   if row['k']==2 and row['p']==64:assert Decimal('1e-14')<abs(Decimal.from_float(naive)-truth)/truth<Decimal('1e-11')

@pytest.mark.skipif(shutil.which('node') is None,reason='Node required')
def test_quadrature_integrates_exact_trapezoids_and_uses_stated_rounded_operations():
 data=node("const a=require('./web/math-numerical-lab.js');const rows=[];for(const p of [32,64])for(let n=1;n<=64;n++){const m=a.build({mode:'trapezoid',precision:p,intervals:n});rows.push({p,n,value:m.value,theoretical:m.theoretical,truncation:m.truncation,rounding:m.rounding,total:m.total});}console.log(JSON.stringify(rows,(_k,v)=>typeof v==='bigint'?v.toString():v));")
 for r in data:
  n=r['n'];h=Fraction(2,n);xs=[i*h for i in range(n+1)];area=sum(h*(xs[i]**2+xs[i+1]**2)/2 for i in range(n))
  assert rational(r['theoretical'])==area and rational(r['truncation'])==area-Fraction(8,3)
  q=f32 if r['p']==32 else float;step=q(2/n);acc=0.
  for i in range(n+1):
   x=q(i*step);y=q(x*x);weight=.5 if i in [0,n] else 1;acc=q(acc+q(weight*y))
  actual=q(step*acc);assert r['value']==actual
  assert rational(r['rounding'])==Fraction.from_float(actual)-area
  assert rational(r['total'])==Fraction.from_float(actual)-Fraction(8,3)

def test_binding_keeps_original_model_and_rejects_cross_lesson_or_extra_props():
 c=Curriculum();n=copy.deepcopy(c.node('math.5.numerical'));media=n['lesson_media'];assert any(m.get('renderer')=='concept-lab' for m in media)
 m=next(m for m in media if m.get('renderer')=='math-numerical-lab');assert m['props']=={'scenario':'math.5.numerical.error-accounting'};_validate_lesson_media(n)
 for bad in [{'scenario':'math.4.analysis'},{'scenario':'math.5.numerical.error-accounting','extra':True}]:
  m['props']=bad
  with pytest.raises(ValueError,match='numerical error model'):_validate_lesson_media(n)
 assert 'only a few correct digits' not in json.dumps(c.node('math.5.numerical'))
 s=next(m for m in media if m.get('renderer')=='spatial-3d');assert s['props']['family']=='numerical-conditioning'
 shell=(ROOT/'web/index.html').read_text();assert shell.index('/app/math-numerical-lab.js')<shell.index('/app/lesson-models.js')

@pytest.mark.skipif(shutil.which('node') is None,reason='Node required')
def test_actual_mounted_values_error_geometry_and_3d_transformation():
 p=subprocess.run(['node','tools/check_math_numerical_lab.js'],cwd=ROOT,text=True,capture_output=True,timeout=40);assert p.returncode==0,p.stdout+p.stderr
 assert 'numerical states' in p.stdout and 'unthickened 3D matrix maps' in p.stdout
