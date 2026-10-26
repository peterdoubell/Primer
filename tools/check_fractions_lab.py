"""Independent Python Fraction oracle for the runtime rational workbench."""
from fractions import Fraction as F
from pathlib import Path
import hashlib,itertools,json,math,random,subprocess
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT / "web/fractions-lab.js"

def rational(p):return F(int(p['n']),int(p['d']))
def verify(s,m):
    op=s['operation'];uses_b=op not in ['simplify','of']
    if s['ad']==0 or (uses_b and s['bd']==0):
        assert m['status']=='undefined' and m['undefinedKind']=='operand-denominator';assert not m['detail'];return
    a=F(s['an'],s['ad']);b=F(s['bn'],s['bd']) if uses_b else F(0)
    if op=='divide' and b==0:
        assert m['status']=='undefined' and m['undefinedKind']=='zero-divisor';assert not m['detail'];return
    assert m['status']=='defined';assert rational(m['A'])==a
    if uses_b:assert rational(m['B'])==b
    expected={'add':lambda:a+b,'subtract':lambda:a-b,'multiply':lambda:a*b,'divide':lambda:a/b,'simplify':lambda:a,'of':lambda:a*s['quantity']}
    if op=='compare':assert m['comparison']==((a>b)-(a<b)) and m['result'] is None
    else:
        r=expected[op]();assert rational(m['result'])==r
        assert math.gcd(int(m['result']['n']),int(m['result']['d']))==1 and int(m['result']['d'])>0
        assert F(int(m['unreduced']['n']),int(m['unreduced']['d']))==r
        trace=m['reduction'];last=None
        for row in trace['rows']:
            x,y,q,rem=[int(row[k]) for k in ['dividend','divisor','quotient','remainder']]
            assert x==q*y+rem and 0<=rem<y
            if last:assert(x,y)==last
            last=(y,rem)
        assert int(trace['gcd'])==math.gcd(int(m['unreduced']['n']),int(m['unreduced']['d']))
    d=math.lcm(a.denominator,b.denominator);assert int(m['common']['denominator'])==d
    assert F(int(m['common']['aNumerator']),d)==a;assert F(int(m['common']['bNumerator']),d)==b
    if 'detail' in m:
        partition=int(m['partition']);start=m['state']['cell'];focus=s['focus']
        for i,c in enumerate(m['detail']):
            assert rational(c['lo'])==focus+F(start+i,partition)
            assert rational(c['hi'])==focus+F(start+i+1,partition)
        for row in m['fragments']:
            v=rational(row['value']);lo,hi=sorted([F(0),v]);assert row['sign']==((v>0)-(v<0))
            for cell,fragment in zip(m['detail'],row['cells']):
                left,right=max(lo,rational(cell['lo'])),min(hi,rational(cell['hi']))
                if left<right:assert rational(fragment['lo'])==left and rational(fragment['hi'])==right
                else:assert fragment is None
    if m.get('productArea'):
        p=m['productArea'];assert rational(p['width'])==abs(a) and rational(p['height'])==abs(b) and rational(p['area'])==abs(a*b)
        assert p['sign']==((a*b>0)-(a*b<0))
    if m.get('quantityShares'):
        q=m['quantityShares'];share=F(s['quantity'],a.denominator)
        assert rational(q['share'])==share and q['parts']==a.denominator and q['selectedParts']==abs(a.numerator)
        assert len(q['wholeCells'])==a.denominator and len(q['selectedCells'])==abs(a.numerator)
        for i,c in enumerate(q['wholeCells']):
            assert rational(c['start'])==i*share and rational(c['end'])==(i+1)*share
        sign=(a>0)-(a<0)
        for i,c in enumerate(q['selectedCells']):
            assert rational(c['start'])==i*sign*share and rational(c['end'])==(i+1)*sign*share
    if m.get('grouping'):
        g=m['grouping'];count=abs(a/b);whole=count.numerator//count.denominator;remaining=abs(a)-whole*abs(b)
        assert int(g['whole'])==whole;assert rational(g['remainder'])==remaining;assert rational(g['fractionalGroup'])==remaining/abs(b)
        for piece in g['pieces']:
            assert rational(piece['start'])==piece['index']*abs(b)
            assert rational(piece['end'])==min((piece['index']+1)*abs(b),abs(a))
        assert g['omittedBefore']+sum(p['complete'] for p in g['pieces'])+g['omittedAfter']==whole

def main():
    modes=['add','subtract','multiply','divide','compare','simplify','of'];cases=[]
    base=dict(an=2,ad=3,bn=1,bd=4,quantity=20,focus=0,cell=0,group=0)
    for op,an,ad,bn,bd in itertools.product(modes,[-2,-1,0,1,2],[-3,-1,0,1,3],[-2,-1,0,1,2],[-3,-1,0,1,3]):cases.append({**base,'operation':op,'an':an,'ad':ad,'bn':bn,'bd':bd})
    rng=random.Random(20261026)
    for _ in range(650):cases.append(dict(operation=rng.choice(modes),an=rng.randint(-120,120),ad=rng.randint(-60,60),bn=rng.randint(-120,120),bd=rng.randint(-60,60),quantity=rng.randint(0,60),focus=rng.randint(-5,5),cell=rng.randint(0,7200),group=rng.randint(0,7200)))
    for op in modes:
        for an,ad,bn,bd in [(120,59,-119,60),(-120,1,1,60),(0,60,0,59),(-120,-60,-120,60),(120,1,-120,-1)]:cases.append({**base,'operation':op,'an':an,'ad':ad,'bn':bn,'bd':bd,'quantity':60,'focus':-10000,'cell':7200,'group':7200})
    script="const a=require('./web/fractions-lab.js'),fs=require('fs');const rows=JSON.parse(fs.readFileSync(0,'utf8')).map(s=>a.build(s));console.log(JSON.stringify(rows));"
    run=subprocess.run(['node','-e',script],cwd=ROOT,input=json.dumps(cases),capture_output=True,text=True,check=True,timeout=90)
    rows=json.loads(run.stdout)
    for s,m in zip(cases,rows):verify(s,m)
    invalid="const a=require('./web/fractions-lab.js'),assert=require('assert/strict');for(const s of [{an:1.5},{an:'1e2'},{ad:'x'},{quantity:-1},{focus:10001},{cell:7201},{group:-1},{operation:'unknown'}])assert.throws(()=>a.build(s));console.log('invalid-state domains passed');"
    subprocess.run(['node','-e',invalid],cwd=ROOT,check=True,capture_output=True)
    proof={'allPassed':True,'cases':len(cases),'defined':sum(m['status']=='defined' for m in rows),'undefined':sum(m['status']=='undefined' for m in rows),'oracle':'Python fractions.Fraction, math.gcd/lcm; independent interval intersections and group remainder decomposition; no runtime arithmetic helper imports','sourceSHA256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'oracleSHA256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'productionVerified':False}
    print(json.dumps(proof))
    return proof
if __name__=='__main__':main()
