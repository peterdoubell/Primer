"""Independent Fraction/Decimal oracle for every decimal-workbench operation."""
from decimal import Decimal, localcontext, ROUND_HALF_UP
from fractions import Fraction as F
from pathlib import Path
import hashlib,itertools,json,random,subprocess
ROOT=Path(__file__).resolve().parents[1]
def main():
 states=[]
 values=['-1000000','-12.345678','-3','-0.85','-0.000001','-0','0','0.000001','0.07','0.089','0.300000','0.4','0.75','1.20','1.6','3','3.478','1000000']
 for mode in ['compare','add','subtract','multiply','divide']:
  for a,b in itertools.product(values,repeat=2):states.append(dict(mode=mode,a=a,b=b))
 for a in values:states.append(dict(mode='place',a=a))
 for a,p in itertools.product(values+['-1.25','1.25','-0.005','0.005','9.995','-9.995','1.200000'],range(7)):states.append(dict(mode='round',a=a,places=str(p)))
 for a,b,q1,q2,tender in itertools.product(['0','0.01','1.200','3.40'],['0','2.75'],['0','1','4','1000'],['0','1'],['0','10','1000000']):states.append(dict(mode='money',a=a,b=b,quantityA=q1,quantityB=q2,tender=tender))
 for a,b,start in itertools.product(['0','1','1.8','1000000'],['0.000001','0.3','0.6'],['0','1','2','12','1000000000000']):states.append(dict(mode='divide',a=a,b=b,groupStart=start))
 rng=random.Random(20261026)
 for _ in range(1200):
  mode=rng.choice(['add','subtract','multiply','divide','compare','round'])
  states.append(dict(mode=mode,a=f'{rng.randrange(-1000000000,1000000001)/1000000:.6f}',b=f'{rng.randrange(-1000000000,1000000001)/1000000:.6f}',places=str(rng.randrange(7))))
 script="const c=require('./web/decimal-core.js'); console.log(JSON.stringify(JSON.parse(require('fs').readFileSync(0,'utf8')).map(s=>c.build(s))));"
 models=json.loads(subprocess.check_output(['node','-e',script],cwd=ROOT,input=json.dumps(states),text=True))
 count={m:0 for m in ['place','compare','add','subtract','multiply','divide','round','money']};column_checks=0;window_checks=0
 def val(p):
  v=F(int(p['n']),int(p['d']));assert p['n']==str(v.numerator)and p['d']==str(v.denominator)
  if p['decimal']is not None:assert F(p['decimal'])==v
  assert F(p['fraction'])==v
  return v
 def unit(power):return F(10)**power
 for m in models:
  s=m['state'];mode=s['mode'];a=F(s['a']);count[mode]+=1;assert val(m['a'])==a
  if mode=='place':
   assert sum(val(c)for c in m['expanded'])==a
   for c in m['columns']:assert val(c['contribution'])==(1 if a>=0 else -1)*c['aDigit']*unit(c['power'])
   continue
  if mode=='round':
   p=int(s['places'])
   with localcontext()as ctx:
    ctx.prec=60;expected=Decimal(s['a']).quantize(Decimal(1).scaleb(-p),rounding=ROUND_HALF_UP)
   # This is exact arithmetic, with one mathematical zero rather than IEEE signed zero.
   if expected.is_zero():expected=expected.copy_abs()
   assert val(m['rounded'])==F(expected)and m['formatted']==format(expected,'f'),(s,m['formatted'],str(expected))
   u=unit(-p);lower=val(m['lower']);upper=val(m['upper']);assert lower<=a<upper and upper-lower==u and val(m['unit'])==u
   assert val(m['midpoint'])==(lower+upper)/2 and m['halfway']==(a==(lower+upper)/2)
   assert m['alreadyExact']==((a/u).denominator==1)
   continue
  b=F(s['b']);assert val(m['b'])==b
  if mode=='compare':
   assert m['relation']==((a>b)-(a<b));assert sum(c['aDigit']*unit(c['power'])for c in m['columns'])==abs(a)
   assert sum(c['bDigit']*unit(c['power'])for c in m['columns'])==abs(b)
  elif mode in ['add','subtract']:
   result=a+b if mode=='add'else a-b;assert val(m['result'])==result
   assert F(m['alignedA'])==a and F(m['alignedB'])==b
   columns=m['columns'];assert all(columns[i]['transferOut']==columns[i+1]['transferIn']for i in range(len(columns)-1))
   assert columns[0]['transferIn']==0 and columns[-1]['transferOut']==0
   reconstructed=sum(c['result']*unit(c['power'])for c in columns);assert reconstructed==abs(result)
   assert m['sign']==((result>0)-(result<0))
   for c in columns:
    if m['magnitudeOperation']=='add':assert c['aDigit']+c['bDigit']+c['transferIn']==c['result']+10*c['transferOut']
    else:assert c['aDigit']-c['transferIn']-c['bDigit']==c['result']-10*c['transferOut']
    column_checks+=1
  elif mode=='multiply':
   assert val(m['result'])==a*b and val(m['magnitudeA'])==abs(a)and val(m['magnitudeB'])==abs(b)
   largest=max(abs(a),abs(b));extent=largest if 0<largest<F(1,10)else max(F(1),largest)
   assert val(m['axisExtent'])==extent
   assert int(m['integerProduct'])==int(m['integerA'])*int(m['integerB'])
   assert F(int(m['integerProduct']),10**m['decimalPlaces'])==a*b
  elif mode=='divide':
   assert (m['status']=='undefined')==(b==0)
   if not b:continue
   quotient=a/b;assert val(m['quotient'])==quotient
   assert F(int(m['scaledA']),int(m['scaledB']))==quotient
   assert F(m['scaledA'])==a*int(m['scaleFactor'])and F(m['scaledB'])==b*int(m['scaleFactor'])
   full=abs(a)//abs(b);part=abs(quotient)-full;assert int(m['fullGroups'])==full and val(m['fractionOfLastGroup'])==part
   assert val(m['remainderAmount'])==abs(a)-full*abs(b)
   w=m['groupWindow'];start=int(s['groupStart']);last=int(full)+(part>0);expected=list(range(start,min(last,start+12)))
   assert [int(g['index'])for g in w['groups']]==expected and len(expected)<=12
   for g in w['groups']:assert val(g['fraction'])==(1 if int(g['index'])<full else part)
   assert int(w['hiddenBefore'])==min(start,last)
   assert int(w['hiddenAfter'])==max(0,last-max(start,min(last,start+12)))
   assert w['empty']==(not expected);window_checks+=len(expected)
  else:
   tender=F(s['tender']);costA=a*int(s['quantityA']);costB=b*int(s['quantityB']);total=costA+costB;balance=tender-total
   assert val(m['costA'])==costA and val(m['costB'])==costB and val(m['total'])==total and val(m['balance'])==balance
   assert F(m['totalMoney'])==total and F(m['changeMoney'])==abs(balance)and m['sufficient']==(balance>=0)
 negative="const c=require('./web/decimal-core.js'),a=require('assert/strict'); for(const s of [null,[],{mode:'bad'},{extra:1},{a:true},{a:'1e2'},{a:'1000001'},{a:'0.0000001'},{mode:'round',places:'1.5'},{mode:'round',places:'7'},{mode:'divide',b:'0',groupStart:'-1'},{mode:'money',a:'0.001'},{mode:'money',a:'-1'},{mode:'money',tender:'0.001'},{mode:'money',quantityA:'1.5'},{mode:'money',quantityB:'1001'}])a.throws(()=>c.build(s));"
 subprocess.run(['node','-e',negative],cwd=ROOT,check=True)
 proof={'allPassed':True,'cases':len(models),'operations':count,'columnIdentities':column_checks,'groupWindowChecks':window_checks,'oracle':'Python Fraction and Decimal ROUND_HALF_UP; independent column reconstruction and magnitude-group identities','sourceSHA256':hashlib.sha256((ROOT/'web/decimal-core.js').read_bytes()).hexdigest(),'oracleSHA256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()};print(json.dumps(proof))
if __name__=='__main__':main()
