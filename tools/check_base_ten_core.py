"""Independent integer/Fraction oracle for the proposed five-lesson foundation."""
from fractions import Fraction
from pathlib import Path
import hashlib,itertools,json,random,subprocess
R=Path.cwd();D=R/'docs/base-ten-fidelity-review-20261027';states=[];rng=random.Random(271027)
def add(lesson,state):states.append({'lesson':lesson,'state':state})
for n in range(10000):add('math.1.place-value',{'mode':'place','value':str(n)})
for h,t,o in itertools.product(range(3),range(21),range(201)):
 if 100*h+10*t+o>200:continue
 for f,d in itertools.product(['hundreds','tens'],['bundle','unbundle']):add('math.1.place-value',{'mode':'exchange','hundreds':str(h),'tens':str(t),'ones':str(o),'from':f,'direction':d})
for a,b in itertools.product(range(101),range(101)):
 add('math.1.addition',{'mode':'add','a':str(a),'b':str(b)})
 for mode in ['takeAway','difference']:add('math.1.subtraction',{'mode':mode,'a':str(a),'b':str(b)})
for mode,lesson in [('add','math.1.addition'),('takeAway','math.1.subtraction'),('difference','math.1.subtraction')]:
 for _ in range(500):add(lesson,{'mode':mode,'a':str(rng.randrange(1000)),'b':str(rng.randrange(1000))})
for a,b in itertools.product(range(13),repeat=2):add('math.1.multiplication',{'mode':'multiply','a':str(a),'b':str(b)})
for total,divisor,mode in itertools.product(range(145),range(13),['share','group']):add('math.1.division',{'mode':mode,'total':str(total),'divisor':str(divisor)})
script="const fs=require('fs'),c=require('./web/base-ten-core.js');console.log(JSON.stringify(JSON.parse(fs.readFileSync(0,'utf8')).map(r=>c.build(r.lesson,r.state))));"
checks=0;types={};undefined=0
for start in range(0,len(states),3000):
 models=json.loads(subprocess.check_output(['node','-e',script],cwd=R,input=json.dumps(states[start:start+3000]),text=True))
 for row,m in zip(states[start:start+3000],models):
  s=row['state'];mode=s['mode'];types[mode]=types.get(mode,0)+1
  def check(x,y):
   global checks
   assert x==y,(row,x,y);checks+=1
  if mode=='place':
   n=int(s['value']);check(m['value'],n);check(sum(p['contribution']for p in m['places']),n)
   for p in m['places']:check(p['unit'],10**p['power']);check(p['digit'],n//10**p['power']%10);check(p['contribution'],p['digit']*p['unit'])
  elif mode=='exchange':
   before={k:int(s[k])for k in ['hundreds','tens','ones']};after=dict(before);f=s['from'];lower='tens'if f=='hundreds'else'ones';d=s['direction'];possible=before[f]>=1 if d=='unbundle'else before[lower]>=10
   if possible:
    after[f]+= -1 if d=='unbundle'else 1;after[lower]+=10 if d=='unbundle'else-10
   check(m['before'],before);check(m['after'],after);check(m['possible'],possible)
   total=lambda v:v['hundreds']*100+v['tens']*10+v['ones'];check(total(before),total(after));check(m['value'],total(before));check(sum(after.values())-sum(before.values()),(9 if d=='unbundle'else-9)if possible else 0)
  elif mode=='add':
   a,b=int(s['a']),int(s['b']);check(m['result'],a+b);check(sum(p['contribution']for p in m['places']),a+b);carry=0;reconstructed=0
   for c in m['columns']:
    check(c['carryIn'],carry);check(c['aDigit']+c['bDigit']+carry,c['resultDigit']+10*c['carryOut']);assert 0<=c['resultDigit']<=9;reconstructed+=c['resultDigit']*c['unit'];carry=c['carryOut']
   check(carry,0);check(reconstructed,a+b)
  elif mode in ['takeAway','difference']:
   a,b=int(s['a']),int(s['b']);check(m['result'],a-b);check(m['magnitude'],abs(a-b));check(m['canTakeAway'],b<=a);check(m['retained']+m['removed'],a);check(m['shortfall'],max(b-a,0));borrow=0;reconstructed=0
   for c in m['columns']:
    check(c['borrowIn'],borrow);check(c['highDigit']-borrow+10*c['borrowOut']-c['lowDigit'],c['resultDigit']);assert 0<=c['resultDigit']<=9;reconstructed+=c['resultDigit']*c['unit'];borrow=c['borrowOut']
   check(borrow,0);check(reconstructed,abs(a-b))
  elif mode=='multiply':
   a,b=int(s['a']),int(s['b']);check(m['result'],a*b);check(m['repeatedAddends'],[b]*a);check(sum(m['repeatedAddends']),a*b);check(m['swappedRows']*m['swappedColumns'],a*b)
  else:
   n,d=int(s['total']),int(s['divisor'])
   if d==0:check(m['status'],'undefined');assert m['reason'];undefined+=1;continue
   check(m['quotient'],n//d);check(m['remainder'],n%d);check(m['check'],n);check(Fraction(m['exactQuotient']['text']),Fraction(n,d));check(m['groupCount']*m['groupSize']+m['remainder'],n);check(m['groupCount'],d if mode=='share'else n//d);check(m['groupSize'],n//d if mode=='share'else d)
invalid=[('math.1.addition',{'mode':'share'}),('unknown',{}),('math.1.place-value',{'value':'10000'}),('math.1.place-value',{'mode':'exchange','hundreds':'2','ones':'1'}),('math.1.addition',{'a':'-1'}),('math.1.addition',{'a':'1e2'}),('math.1.addition',{'a':True}),('math.1.multiplication',{'a':'13'}),('math.1.division',{'divisor':'13'}),('math.1.division',{'total':'145'}),('math.1.addition',None),('math.1.addition',{'extra':'1'})]
script="const fs=require('fs'),c=require('./web/base-ten-core.js');for(const[l,s]of JSON.parse(fs.readFileSync(0,'utf8'))){let bad=false;try{c.build(l,s)}catch(e){bad=true}if(!bad)throw Error('Accepted invalid '+JSON.stringify([l,s]));}"
subprocess.run(['node','-e',script],cwd=R,input=json.dumps(invalid),text=True,capture_output=True,check=True)
result={'allPassed':True,'cases':len(states),'checks':checks,'modes':types,'undefinedCases':undefined,'invalidStatesRejected':len(invalid),'scope':'Current arithmetic implementation; visual, reader and delivery checks are separate','sourceSHA256':hashlib.sha256((R/'web/base-ten-core.js').read_bytes()).hexdigest(),'oracleSHA256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'wholeGoalComplete':False};print(json.dumps(result))
