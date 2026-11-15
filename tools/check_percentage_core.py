"""Independent exact rational oracle for the percentage workbench."""
from pathlib import Path
from fractions import Fraction as F
import hashlib,itertools,json,random,subprocess
R=Path(__file__).resolve().parents[1];states=[]
for mode in ['of','convert']:
 for fmt,value in [('fraction','3/8'),('fraction','1/3'),('fraction','10/1'),('percent','37.5'),('percent','0'),('percent','1000'),('decimal','0.07'),('decimal','0.000001'),('decimal','1.25')]:
  for whole in ['0','0.000001','80','1000000']:states.append(dict(mode=mode,format=fmt,value=value,whole=whole))
for mode in ['ratio','change']:
 for x,y in itertools.product(['0','0.000001','30','40','1000000'],repeat=2):states.append(dict(mode=mode,**({'part':x,'whole':y}if mode=='ratio'else {'before':x,'after':y})))
for whole in ['0','0.000001','80','200','1000000']:
 for r1,r2 in itertools.product(['-100','-25','-10','0','20','37.5','1000'],repeat=2):states.append(dict(mode='chain',whole=whole,rate1=r1,rate2=r2))
for whole in ['0','80','200']:states.append(dict(mode='compare',whole=whole));states.append(dict(mode='compare',whole=whole,typeA='fraction',compareA='1/3',typeB='decimal',compareB='0.333333',typeC='percent',compareC='33.333333'))
rng=random.Random(20261026)
for _ in range(500):states.append(dict(mode='chain',whole=str(rng.randrange(1000000)/100),rate1=str(rng.randrange(-10000,100001)/100),rate2=str(rng.randrange(-10000,100001)/100)))
script="const c=require('./web/percentage-core.js');console.log(JSON.stringify(JSON.parse(require('fs').readFileSync(0,'utf8')).map(s=>c.build(s))));"
models=json.loads(subprocess.check_output(['node','-e',script],cwd=R,input=json.dumps(states),text=True))
def value(p):
 f=F(int(p['n']),int(p['d']));assert p['d']==str(f.denominator) and p['n']==str(f.numerator)
 if p['decimal'] is not None:assert F(p['decimal'])==f
 return f
def ratio(s,k='value',kind='format'):
 f=F(s[k]);return f/100 if s[kind]=='percent'else f
for m in models:
 s=m['state'];mode=s['mode']
 if mode in ['of','convert']:
  r=ratio(s);assert value(m['ratio'])==r and value(m['percent'])==100*r
  if mode=='of':assert value(m['part'])==r*F(s['whole'])
  grid=m['hundredGrid'];assert grid['wholeUnits']+F(grid['remainingWholeCells'],100)+value(grid['fractionOfNextCell'])/100==r
 elif mode=='ratio':
  a,b=F(s['part']),F(s['whole']);assert (m['status']=='undefined')==(b==0)
  if b:assert value(m['percent'])==100*a/b
 elif mode=='change':
  a,b=F(s['before']),F(s['after']);assert value(m['difference'])==b-a;assert(m['status']=='undefined')==(a==0)
  if a:assert value(m['percent'])==100*(b-a)/a
 elif mode=='chain':
  a,r1,r2=F(s['whole']),F(s['rate1']),F(s['rate2']);middle=a*(1+r1/100);last=middle*(1+r2/100)
  assert value(m['middle'])==middle and value(m['last'])==last
  assert value(m['composedPercent'])==r1+r2+r1*r2/100
  assert value(m['changes'][0])==middle-a and value(m['changes'][1])==last-middle
  if a:assert value(m['endpointPercentChange'])==100*(last-a)/a
  else:assert m['endpointPercentChange'] is None
 else:
  expected={k:ratio(s,'compare'+k,'type'+k)for k in ['A','B','C']}
  for row in m['discounts']:assert value(row['ratio'])==expected[row['name']] and value(row['saving'])==F(s['whole'])*expected[row['name']]
  assert m['descending']==sorted(expected,key=lambda k:-expected[k]);assert set(m['largest'])=={k for k,v in expected.items()if v==max(expected.values())}
negative="const c=require('./web/percentage-core.js'),a=require('assert/strict');for(const s of [{unknown:1},{value:'3/0',format:'fraction'},{value:'1e2'},{mode:'chain',rate1:'-100.01'},{whole:'-1'},{mode:'compare',compareC:'101'},{value:true},{mode:'bad'}])a.throws(()=>c.build(s));"
subprocess.run(['node','-e',negative],cwd=R,check=True)
proof={'allPassed':True,'cases':len(models),'oracle':'Python Fraction with independent operation, composed-rate and partial-grid identities','sourceSHA256':hashlib.sha256((R/'web/percentage-core.js').read_bytes()).hexdigest(),'oracleSHA256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()};print(json.dumps(proof))
