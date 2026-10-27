"""Independent Fraction oracle for every ratio operation and unit conversion."""
from fractions import Fraction as F
from pathlib import Path
import hashlib,itertools,json,random,subprocess
ROOT=Path(__file__).resolve().parents[1]
def main():
 values=['0','0.000001','0.1','0.25','1','2','3','7','91','999999.999999','1000000'];rng=random.Random(271026);states=[]
 modes=['scale','compare','share','missing','rate','recipe','map','model','mapCompare']
 for mode in modes:
  for _ in range(160):states.append(dict(mode=mode,**{k:rng.choice(values)for k in ['a','b','c','d','target']}))
 for mode in ['scale','share']:
  for a,b,t in itertools.product(values,values,['0','0.1','3','1000000']):states.append({'mode':mode,'a':a,'b':b,'c':t,'target':t})
 script="const fs=require('fs'),c=require('./web/ratio-core.js');console.log(JSON.stringify(JSON.parse(fs.readFileSync(0,'utf8')).map(s=>c.build(s))));"
 models=json.loads(subprocess.check_output(['node','-e',script],input=json.dumps(states),cwd=ROOT,text=True));checks=0;undefined=0
 for s,m in zip(states,models):
  a,b,c,d,t=(F(s.get(k,'2'if k=='a'else'3'if k in ['b','c']else'9'if k=='d'else'6'))for k in ['a','b','c','d','target']);mode=s['mode']
  bad=(mode in ['scale','compare','share','missing']and a+b==0)or(mode=='compare'and c+d==0)or(mode in ['missing','rate','recipe','map','model']and a==0)or(mode=='mapCompare'and(a==0 or b==0))
  if bad:assert m['status']=='undefined'and m['reason']and m['charts']==[];undefined+=1;continue
  assert m['status']=='defined'
  def check(key,expected):
   nonlocal checks
   p=m[key];assert F(int(p['n']),int(p['d']))==expected,(mode,key,s,p,expected);assert F(p['fraction'])==expected;assert p['decimal']is None or F(p['decimal'])==expected;assert F(p['exact'])==expected;checks+=1
  if mode=='scale':check('resultA',a*c);check('resultB',b*c);check('total',(a+b)*c);assert m['equivalent']==(c>0)
  elif mode=='compare':check('crossLeft',a*d);check('crossRight',b*c);check('firstFractionA',a/(a+b));check('secondFractionA',c/(c+d));assert m['equivalent']==(a*d==b*c)
  elif mode in ['share','missing']:
   factor=t/(a+b)if mode=='share'else t/a
   for k,v in [('factor',factor),('resultA',a*factor),('resultB',b*factor),('total',(a+b)*factor),('fractionA',a/(a+b)),('fractionB',b/(a+b))]:check(k,v)
  elif mode in ['rate','recipe']:check('unitRate',b/a);check('factor',t/a);check('result',b*t/a)
  elif mode=='map':check('groundKm',a*t);check('scaleDenominator',a*100000)
  elif mode=='model':check('actualCm',b*100);check('modelCm',b*100/a);check('lengthFactor',1/a)
  else:check('firstMapCm',t/a);check('secondMapCm',t/b);check('secondToFirst',a/b)
  for chart in m['charts']:
   assert chart['unit']and chart['title']
   for row in chart['rows']:assert F(row['amount']['fraction'])>=0
 invalid=[None,[],{'mode':'unknown'},{'mode':'scale','a':'-1'},{'mode':'scale','a':'1e2'},{'mode':'scale','a':True},{'mode':'scale','a':''},{'mode':'scale','a':'1000001'},{'mode':'share','target':'0.0000001'},{'extra':'1'}]
 script="const fs=require('fs'),c=require('./web/ratio-core.js');for(const s of JSON.parse(fs.readFileSync(0,'utf8'))){let rejected=false;try{c.build(s)}catch(e){rejected=true}if(!rejected)throw Error('Accepted invalid state '+JSON.stringify(s));}"
 subprocess.run(['node','-e',script],input=json.dumps(invalid),cwd=ROOT,text=True,check=True,capture_output=True)
 result={'allPassed':True,'cases':len(states),'exactQuantityChecks':checks,'undefinedCases':undefined,'invalidStatesRejected':len(invalid),'oracle':'Python fractions.Fraction; independent operation and unit-conversion formulas','sourceSHA256':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in ['web/ratio-core.js','web/decimal-core.js','tools/check_ratio_core.py']},'wholeGoalComplete':False};print(json.dumps(result))
if __name__=='__main__':main()
