"""Independent exact-rational and geometric oracles for the linear algebra workbench."""
from pathlib import Path
from fractions import Fraction as F
from itertools import permutations, combinations, product
import argparse, cmath, hashlib, json, math, subprocess, sys

if not __debug__: raise RuntimeError('Assertions must remain enabled.')
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/linear-algebra-fidelity-review-20261016/independent-review'
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--write-proof',action='store_true')
parser.add_argument('--snapshot-oracles',action='store_true',help='Derive geometry only from ordinary-control states supplied on stdin; no product API is called.')
args=parser.parse_args()
requests=[];cases={};checks=[];metrics={}

def q(x):
    if isinstance(x,str) and '/' in x:
        numerator,denominator=x.split('/')
        return F(int(numerator),int(denominator))
    return F(str(x)) if isinstance(x,float) else F(x)
def mat(A): return [[q(x) for x in row] for row in A]
def tr(A): return [list(c) for c in zip(*A)]
def dot(x,y): return sum((a*b for a,b in zip(x,y)),F(0))
def mv(A,x): return [dot(r,x) for r in A]
def mm(A,B): return [[dot(r,c) for c in tr(B)] for r in A]
def identity(n): return [[F(i==j) for j in range(n)] for i in range(n)]
def power(A,n):
    R=identity(len(A))
    for _ in range(n): R=mm(R,A)
    return R
def det(A):
    n=len(A);result=F(0)
    for order in permutations(range(n)):
        term=F((-1)**sum(order[i]>order[j] for i in range(n) for j in range(i+1,n)))
        for i in range(n): term*=A[i][order[i]]
        result+=term
    return result
def minor_rank(A):
    for size in range(min(len(A),len(A[0])),0,-1):
        for rows in combinations(range(len(A)),size):
            for cols in combinations(range(len(A[0])),size):
                if det([[A[i][j] for j in cols] for i in rows]): return size
    return 0
def rref(A):
    R=[r[:] for r in A];pivot=[];row=0
    for col in range(len(R[0])):
        candidates=[i for i in range(row,len(R)) if R[i][col]]
        if not candidates: continue
        # Largest exact pivot: a different row-selection strategy from product.
        chosen=max(candidates,key=lambda i:abs(R[i][col]))
        R[row],R[chosen]=R[chosen],R[row]
        denominator=R[row][col];R[row]=[x/denominator for x in R[row]]
        for i in range(len(R)):
            if i!=row:
                factor=R[i][col];R[i]=[a-factor*b for a,b in zip(R[i],R[row])]
        pivot.append(col);row+=1
        if row==len(R): break
    return R,pivot
def kernel(A):
    R,pivots=rref(A);basis=[]
    for free in sorted(set(range(len(A[0])))-set(pivots)):
        v=[F(0)]*len(A[0]);v[free]=F(1)
        for i,p in enumerate(pivots): v[p]=-R[i][free]
        basis.append(v)
    return basis
def analysis(A,b=None):
    A=mat(A);R,pivots=rref(A);rank=minor_rank(A)
    assert rank==len(pivots)
    K=kernel(A);L=kernel(tr(A));n=len(A[0]);m=len(A)
    out=dict(matrix=A,rows=m,columns=n,rref=R,pivots=pivots,rank=rank,nullity=n-rank,kernelBasis=K,leftKernelBasis=L,columnBasis=[tr(A)[j] for j in pivots],determinant=det(A) if m==n else None,trace=sum(A[i][i] for i in range(n)) if m==n else None)
    assert all(mv(A,v)==[0]*m for v in K)
    assert all(mv(tr(A),v)==[0]*n for v in L)
    if b is not None:
        b=list(map(q,b));aug=[row+[rhs] for row,rhs in zip(A,b)];AR,AP=rref(aug);arank=minor_rank(aug)
        kind='none' if arank>rank else 'unique' if rank==n else 'infinite';part=None
        if kind!='none':
            part=[F(0)]*n
            for i,col in enumerate(pivots): part[col]=AR[i][-1]
            assert mv(A,part)==b
        out.update(rhs=b,augmentedRref=AR,augmentedRank=arank,classification=kind,particular=part,solutionBasis=[] if kind=='none' else K)
    return out
def strings(x):
    if isinstance(x,F): return str(x)
    if isinstance(x,list): return [strings(v) for v in x]
    if isinstance(x,dict): return {k:strings(v) for k,v in x.items()}
    return x
def ask(name,method,*arguments):
    requests.append(dict(id=name,method=method,args=list(arguments)));cases[name]=(method,arguments);return name
def equal(actual,expected,label): assert actual==strings(expected),(label,actual,strings(expected))
def near(a,b,label,rel=2e-12,absolute=1e-12): assert math.isfinite(a) and abs(a-b)<=absolute+rel*abs(b),(label,a,b)


def snapshot_oracle(snapshot):
    """Independent geometry specification, using control values, not model summaries."""
    station=snapshot['station'];s=snapshot['state'][station];plots={};facts={}
    def inp(value,limit=1000000):
        if isinstance(value,bool) or not isinstance(value,(str,int,float)): raise ValueError('Invalid rational type')
        text=str(value).strip()
        if not text or len(text)>80:raise ValueError('Invalid input length')
        # A single bounded scan preserves the product's ASCII grammar without
        # backtracking. The length bound above also bounds integer conversion.
        size=len(text);index=1 if text[0] in '+-' else 0
        start=index
        while index<size and '0'<=text[index]<='9':index+=1
        if index==start:raise ValueError('Outside declared input grammar')
        if index<size and text[index]=='/':
            index+=1
            if index<size and text[index] in '+-':index+=1
            start=index
            while index<size and '0'<=text[index]<='9':index+=1
            if index==start or index!=size:raise ValueError('Outside declared input grammar')
        else:
            if index<size and text[index]=='.':
                index+=1
                while index<size and '0'<=text[index]<='9':index+=1
            if index<size and text[index] in 'eE':
                index+=1;start=index
                if index<size and text[index] in '+-':index+=1
                digits=index
                while index<size and '0'<=text[index]<='9':index+=1
                if index==digits or abs(int(text[start:index]))>12:raise ValueError('Outside declared input grammar')
            if index!=size:raise ValueError('Outside declared input grammar')
        value=q(value)
        if value.denominator>10**12 or abs(value)>limit: raise ValueError('Outside declared rational domain')
        return value
    def put(plot,name,world,unordered=False):
        plots.setdefault(plot,{})[name]={'world':strings(world),'unordered':unordered}
    def axes(plot,L):
        for j in range(3):
            v=[F(0)]*3;v[j]=L;put(plot,'axis-'+str(j),[[F(0)]*3,v])
    spectra={
        'diag35':([[3,0],[0,5]],[3,5]),'tri235':([[2,1,0],[0,3,1],[0,0,5]],[2,3,5]),'tri124':([[1,1,0],[0,2,1],[0,0,4]],[1,2,4]),
        'identity':([[1,0],[0,1]],[1,1]),'shear':([[1,1],[0,1]],[1,1]),'eigenpower':([[4,1],[0,2]],[4,2]),
        'decay-diagonal':([['1/2',0],[0,'9/10']],['1/2','9/10']),'decay-nonnormal':([['1/2',10],[0,'9/10']],['1/2','9/10']),
        'reflection':([[1,0],[0,-1]],[1,-1]),'rotation':([[0,-1],[1,0]],None)}
    if station=='maps':
        A=[[inp(s['a'+str(i)+str(j)]) for j in range(2)] for i in range(2)];B=[[inp(s['b'+str(i)+str(j)]) for j in range(2)] for i in range(2)];v=[inp(s['x']),inp(s['y'])];image=mv(A,v);facts=analysis(A);facts.update(B=B,input=v,output=image,AB=mm(A,B),BA=mm(B,A),ABv=mv(mm(A,B),v),BAv=mv(mm(B,A),v))
        square=mat([[0,0],[1,0],[1,1],[0,1]]);put('maps-action','unit-square',square);put('maps-action','mapped-square',[mv(A,p) for p in square])
        for j,col in enumerate(tr(A)):put('maps-action','column-'+str(j),[[F(0),F(0)],col])
        term=[row[0]*v[0] for row in A];put('maps-action','column-sum',[[F(0),F(0)],term,image]);put('maps-action','output',[image])
        for name,points in [('AB',[v,mv(B,v),mv(mm(A,B),v)]),('BA',[v,image,mv(mm(B,A),v)])]:
            put('composition',name+'-path',points)
            for j,p in enumerate(points):put('composition',name+'-step-'+str(j),[p])
    elif station=='systems':
        k=inp(s['k'],16);rhs=inp(s['rhs2'],16);free=inp(s['free'],8);A=mat([[k,2],[8,k]]);b=[F(1),rhs];facts=analysis(A,b);chosen=facts['particular']
        if chosen is not None and facts['kernelBasis']:chosen=[x+free*y for x,y in zip(chosen,facts['kernelBasis'][0])]
        facts['chosen']=chosen;R=max([F(3)]+[abs(x)*F(23,20) for x in chosen or []])
        for j,(row,rhs) in enumerate(zip(A,b)):
            a,beta=row;points=set()
            if beta:
                for x in [-R,R]:
                    y=(rhs-a*x)/beta
                    if abs(y)<=R:points.add((x,y))
            if a:
                for y in [-R,R]:
                    x=(rhs-beta*y)/a
                    if abs(x)<=R:points.add((x,y))
            if len(points)>=2:put('system-lines','equation-'+str(j),[list(p) for p in sorted(points)],True)
        if chosen is not None:put('system-lines','solution',[chosen])
    elif station=='space':
        kind=s['kind'];t=inp(s['t'],4);v=[inp(s['c'+str(j)],4) for j in range(1,4)]
        raw={'family':[[1,0,1-t],[0,1,1-t],[1,1,2+t]],'repeated':[[1,1,2],[2,2,1],[3,3,1]],'rank1':[[1,2,3],[2,4,6],[3,6,9]],'zero':[[0,0,0],[0,0,0],[0,0,0]]}[kind]
        A=mat(raw);facts=analysis(A);output=mv(A,v);facts.update(input=v,output=output,columnVectors=tr(A))
        cube=[[F(i&1),F((i>>1)&1),F((i>>2)&1)] for i in range(8)];mapped=[mv(A,p) for p in cube]
        L=max([F(2)]+[abs(x) for p in mapped+[output] for x in p]);axes('span-volume',L)
        for i in range(8):
            for bit in [1,2,4]:
                j=i^bit
                if j>i:put('span-volume',f'unit-cube-edge-{i}-{j}',[cube[i],cube[j]]);put('span-volume',f'mapped-cube-edge-{i}-{j}',[mapped[i],mapped[j]])
            put('span-volume','mapped-corner-'+str(i),[mapped[i]])
        for j,vcol in enumerate(tr(A)):put('span-volume','column-'+str(j),[[F(0)]*3,vcol])
        put('span-volume','output',[output])
        if facts['rank']==2:
            a,b=facts['columnBasis'];patch=[[u*x+v*y for x,y in zip(a,b)] for u,v in [(-1,-1),(1,-1),(1,1),(-1,1)]];put('span-volume','image-plane-patch',patch)
        if facts['rank']==1:
            a=facts['columnBasis'][0];put('span-volume','image-line',[[-x for x in a],a])
    elif station=='kernel':
        A=mat({'4x4':[[1,0,0,1],[0,1,0,2],[0,0,1,3],[0,0,0,0]],'3x4':[[1,0,0,1],[0,1,0,2],[0,0,1,3]],'2x4':[[1,0,1,0],[0,1,0,1]]}[s['kind']]);facts=analysis(A);coeffs=[inp(s['s'],8),inp(s['t'],8)];v=list(map(F,[2,3,4,5]));base=v[:]
        for coefficient,basis in zip(coeffs,facts['kernelBasis']):v=[x+coefficient*y for x,y in zip(v,basis)]
        output=mv(A,v);assert output==mv(A,base);facts.update(input=v,output=output,baseInput=base,baseOutput=output,inputNormSquared=dot(v,v),outputNormSquared=dot(output,output))
        for name,values,offset in [('input',v,F(-3,25)),('output',output,F(3,25))]:
            for i,value in enumerate(values):
                x=F(i+1)+offset;put('coordinate-ledger',name+'-coordinate-'+str(i),[[x,F(0)],[x,value]]);put('coordinate-ledger',name+'-tip-'+str(i),[[x,value]])
    elif station=='spectrum':
        raw,values=spectra[s['kind']];A=mat(raw);facts=analysis(A);dim=len(A);origin=[F(0)]*dim;probe=[F(1)]*dim;image=mv(A,probe);vectors=[]
        if values is not None:
            values=list(map(q,values));facts.update(eigenvalues=values,eigenvalueSum=sum(values),eigenvalueProduct=math.prod(values))
            for value in dict.fromkeys(values):
                vectors.extend(kernel([[a-value*(i==j) for j,a in enumerate(row)] for i,row in enumerate(A)]))
        else:facts.update(eigenvalueSum=F(0),eigenvalueProduct=F(1),hasEigenbasisOverR=False,hasEigenbasisOverC=True)
        images=[mv(A,v) for v in vectors]
        if dim==3:axes('eigenvectors',max([F(2)]+[abs(x) for p in [probe,image]+vectors+images for x in p]))
        for i,(v,w) in enumerate(zip(vectors,images)):
            put('eigenvectors','eigenvector-'+str(i),[origin,v]);put('eigenvectors','eigenimage-'+str(i),[origin,w]);put('eigenvectors','eigenimage-point-'+str(i),[w])
        put('eigenvectors','probe',[origin,probe]);put('eigenvectors','probe-image',[origin,image])
    elif station=='orbits':
        A=mat(spectra[s['kind']][0]);v=[inp(s['x']),inp(s['y'])];n=s['n']
        if isinstance(n,bool) or not isinstance(n,(int,float)) or int(n)!=n or not 0<=n<=100:raise ValueError('Invalid iteration count')
        if len(A)!=2:raise ValueError('Displayed orbit requires two coordinates')
        points=[];norms=[];squares=[]
        for i in range(int(n)+1):
            points.append(v);sq=dot(v,v);squares.append(sq);norms.append([i,math.sqrt(sq)]);put('orbit','orbit-'+str(i),[v]);put('orbit-norm','norm-'+str(i),[norms[-1]]);v=mv(A,v)
        put('orbit','orbit-path',points);put('orbit-norm','norm-history',norms);facts.update(matrix=A,initial=points[0],n=n,last=points[-1],power=power(A,int(n)),normalizationApplied=False,directionDefined=any(points[-1]),finiteTracePeakIndex=max(range(len(points)),key=lambda i:squares[i]))
        facts['points']=[dict(n=i,value=v,normSquared=squares[i]) for i,v in enumerate(points)]
    elif station=='planes':
        raw,b={'unique':([[1,1,0],[0,1,1],[1,0,1]],[1,2,3]),'dependent':([[1,1,0],[0,1,1],[1,2,1]],[1,2,3]),'inconsistent':([[1,1,0],[0,1,1],[1,2,1]],[1,2,4]),'parallel':([[0,0,1],[0,0,1],[1,0,0]],[0,1,0]),'coincident':([[1,1,1],[2,2,2],[3,3,3]],[1,2,3])}[s['kind']];A=mat(raw);b=list(map(F,b));facts=analysis(A,b);params=[inp(s['s'],4),inp(s['t'],4)];chosen=facts['particular']
        if chosen is not None:
            for t,basis in zip(params,facts['kernelBasis']):chosen=[x+t*y for x,y in zip(chosen,basis)]
        L=F(max(4,math.ceil(max(map(abs,chosen)))+1 if chosen is not None else 4));facts.update(chosen=chosen,boxHalfWidth=L,intersectionDimension=None if chosen is None else facts['nullity']);axes('constraint-planes',L)
        for j,(normal,rhs) in enumerate(zip(A,b)):
            points=set()
            for free in range(3):
                if not normal[free]:continue
                fixed=[axis for axis in range(3) if axis!=free]
                for values in product([-L,L],repeat=2):
                    p=[F(0)]*3
                    for axis,value in zip(fixed,values):p[axis]=value
                    p[free]=(rhs-dot(normal,p))/normal[free]
                    if abs(p[free])<=L:points.add(tuple(p))
            put('constraint-planes','plane-'+str(j),[list(p) for p in sorted(points)],True)
        if chosen is not None:put('constraint-planes','chosen-solution',[chosen])
        if chosen is not None and facts['nullity']==1:
            p=facts['particular'];v=facts['kernelBasis'][0];bounds=[]
            for x,direction in zip(p,v):
                if direction:bounds.append(sorted([(-L-x)/direction,(L-x)/direction]))
            lo=max(pair[0] for pair in bounds);hi=min(pair[1] for pair in bounds)
            put('constraint-planes','common-line',[[x+t*y for x,y in zip(p,v)] for t in [lo,hi]],True)
    else:raise ValueError('Unknown station')
    if station in ['planes','space','spectrum']:
        yaw=float(s['yaw']);pitch=float(s['pitch'])
        if not math.isfinite(yaw) or not math.isfinite(pitch) or not -180<=yaw<=180 or not -90<=pitch<=90:raise ValueError('Camera outside domain')
    return {'id':snapshot.get('id'),'station':station,'facts':strings(facts),'plots':plots}


if args.snapshot_oracles:
    snapshots=json.load(sys.stdin)
    if not isinstance(snapshots,list) or len(snapshots)>500:raise ValueError('Expected bounded state list')
    result=[]
    for snapshot in snapshots:
        try:result.append(snapshot_oracle(snapshot))
        except (ValueError,KeyError,TypeError,ZeroDivisionError) as error:result.append({'id':snapshot.get('id'),'station':snapshot.get('station'),'error':str(error)})
    print(json.dumps({'oracles':result,'method':'Independent Fraction algebra and prescribed fixture construction from ordinary control states only; no product API calls.'}))
    sys.exit(0)

valid_rationals=['0','-0','+3','2/4','1/-2','-5/-10','0.125','-2.5e2','1e-12','1000000','1000000000000000000/1000000000000000000']
for i,value in enumerate(valid_rationals): ask('rational-'+str(i),'rational',value)
matrices=[[[0]],[[3]],[[0,0,0,0]],[[1,-2,3,4]],[[1],[0],[-2],[3]],[[2,1],[3,4]],[[0,-1],[1,0]],[[1,1],[0,1]],[[0,1],[0,0]],[[1,1],[1,'1000000000001/1000000000000']],[[0,2,0],[0,0,3]],[[1,2],[2,4],[3,6]],[[1,0],[0,1],[1,1]],[[1,0,1],[0,1,1],[1,1,2]],[[1,1,2],[2,2,1],[3,3,1]],[[1,0,0,1],[0,1,0,2],[0,0,1,3],[0,0,0,0]],[[1,0,0,1],[0,1,0,2],[0,0,1,3]],[[1,0,1,0],[0,1,0,1]],[[0,0,1,2],[0,1,0,3],[1,0,0,4],[0,0,0,0]],[[2,3,1,4],[1,-1,2,0],[3,1,-2,1],[0,2,1,-1]],[[0,0],[0,0]],[[1,'1/3','2/7'],['2/5',1,'-3/11'],['1/2','-1/9',1]]]
analysis_cases=[]
for i,A in enumerate(matrices):
    name=ask(f'analysis-{i}','analyze',A);analysis_cases.append((name,A,None))
    b=mv(mat(A),[F(j-1) for j in range(len(A[0]))]);name=ask(f'consistent-{i}','analyze',A,strings(b));analysis_cases.append((name,A,b))
    if minor_rank(mat(A))<len(A):
        for axis in range(len(A)):
            bad=[F(j==axis) for j in range(len(A))]
            if minor_rank([r+[v] for r,v in zip(mat(A),bad)])>minor_rank(mat(A)):
                name=ask(f'inconsistent-{i}','analyze',A,strings(bad));analysis_cases.append((name,A,bad));break
products=[];applies=[];powers=[]
for i,A in enumerate(matrices):
    B=[[j+1-i for j in range(2)] for i in range(len(A[0]))]
    products.append((ask(f'product-{i}','multiply',A,B),A,B))
    v=[j-2 for j in range(len(A[0]))];applies.append((ask(f'apply-{i}','apply',A,v),A,v))
for i,A in enumerate([[[0,-1],[1,0]],[[1,1],[0,1]],[[0,1],[0,0]],[['1/2',1],[0,'1/2']],[[1,0],[0,-1]],[[4,1],[0,2]],[[2,1,0],[0,3,1],[0,0,5]],matrices[15]]):
    for n in [0,1,2,3,10]: powers.append((ask(f'power-{i}-{n}','power',A,n),A,n))
map_cases=[{},dict(A=[[1,1],[0,1]],B=[[2,0],[0,1]],x=[0,1]),dict(A=[[1,0],[0,-1]],x=[-2,3]),dict(A=[[1,2],[2,4]],x=[-2,1]),dict(A=[[0,0],[0,0]],x=[1,-1]),dict(A=[[0,-1],[1,0]],x=[1,0])]
for i,state in enumerate(map_cases): ask(f'maps-{i}','maps',state)
system_cases=[dict(k=k,rhs2=4,free=0) for k in ['-16','-5','-4','-4000000000001/1000000000000','-3999999999999/1000000000000','0','3999999999999/1000000000000','4','4000000000001/1000000000000','5','16']]+[dict(k=4,rhs2=2,free=t) for t in [-8,0,8]]+[dict(k=-4,rhs2=-2,free='1/3')]
for i,state in enumerate(system_cases): ask(f'system-{i}','system',state)
space_cases=[dict(kind='family',t=t,coefficients=[1,-2,'1/3']) for t in [-4,'-1/8','0','1/1000000000000','1/8',4]]+[dict(kind=k,t=0,coefficients=v) for k in ['repeated','rank1','zero'] for v in [[1,1,1],[0,0,0]]]
for i,state in enumerate(space_cases): ask(f'space-{i}','space',state)
kernel_cases=[dict(kind=k,coefficients=c) for k in ['4x4','3x4','2x4'] for c in [[0,0],[3,-2],[-8,8]]]
for i,state in enumerate(kernel_cases): ask(f'kernel-{i}','kernel',state)
spectra={'diag35':([[3,0],[0,5]],[3,5]),'tri235':([[2,1,0],[0,3,1],[0,0,5]],[2,3,5]),'tri124':([[1,1,0],[0,2,1],[0,0,4]],[1,2,4]),'identity':([[1,0],[0,1]],[1,1]),'shear':([[1,1],[0,1]],[1,1]),'eigenpower':([[4,1],[0,2]],[4,2]),'decay-diagonal':([['1/2',0],[0,'9/10']],['1/2','9/10']),'decay-nonnormal':([['1/2',10],[0,'9/10']],['1/2','9/10']),'reflection':([[1,0],[0,-1]],[1,-1]),'rotation':([[0,-1],[1,0]],None)}
for kind in spectra: ask('spectrum-'+kind,'spectrum',dict(kind=kind))
orbit_cases=[dict(kind=k,initial=[1]*len(A),n=6) for k,(A,e) in spectra.items()]+[dict(kind='decay-nonnormal',initial=v,n=n) for v,n in [([0,1],100),([1,0],100),([25,1],30),([0,0],100),([-2,3],20)]]+[dict(kind='eigenpower',initial=[1,0],n=3),dict(kind='rotation',initial=[3,4],n=100),dict(kind='shear',initial=[0,1],n=100)]
for i,state in enumerate(orbit_cases): ask(f'orbit-{i}','orbit',state)
plane_matrices={'unique':([[1,1,0],[0,1,1],[1,0,1]],[1,2,3]),'dependent':([[1,1,0],[0,1,1],[1,2,1]],[1,2,3]),'inconsistent':([[1,1,0],[0,1,1],[1,2,1]],[1,2,4]),'parallel':([[0,0,1],[0,0,1],[1,0,0]],[0,1,0]),'coincident':([[1,1,1],[2,2,2],[3,3,3]],[1,2,3])}
plane_cases=[dict(kind=k,free=f) for k in plane_matrices for f in [[0,0],[2,-3],[-4,4]]]
for i,state in enumerate(plane_cases): ask(f'planes-{i}','planes',state)
cameras=[dict(yaw=y,pitch=p) for y,p in [(35,25),(0,0),(90,0),(180,90),(-180,-90),(0,90),(0,-90)]]
for i,state in enumerate(cameras): ask(f'camera-{i}','projection3D',state)
invalid=[]
for value in [None,True,{},[],'','1/0','not a number','1e13','1/1000000000001','1000001']:
    invalid.append(ask(f'invalid-{len(invalid)}','rational',value))
for value in ['NaN','Infinity','-Infinity']:
    name=f'invalid-{len(invalid)}';invalid.append(name);requests.append(dict(id=name,method='rational',nonfinite=value))
for method,arguments in [('analyze',([],)),('analyze',([[1],[1,2]],)),('analyze',([[1,2,3,4,5]],)),('analyze',([[1,2],[3,4]],[1])),('multiply',([[1,2]],[[1,2]])),('apply',([[1,2]],[1])),('power',([[1,2]],0)),('power',([[1]],-1)),('power',([[1]],101)),('power',([[1]],1.5)),('maps',({'A':[[1]],},)),('space',({'t':5},)),('kernel',({'kind':'5x5'},)),('spectrum',({'kind':'arbitrary'},)),('orbit',({'n':101},)),('planes',({'free':[5,0]},)),('projection3D',({'pitch':91},))]:
    invalid.append(ask(f'invalid-{len(invalid)}',method,*arguments))
reply=json.loads(subprocess.check_output(['node',str(ROOT/'tools/check_linear_algebra_independent.cjs')],input=json.dumps(requests).encode(),cwd=ROOT,timeout=60))
data={row['id']:row for row in reply['results']}
def result(name):
    assert 'error' not in data[name],data[name]
    return data[name]['result']
def check_analysis(actual,A,b=None):
    expected=analysis(A,b)
    for key,value in expected.items(): equal(actual[key],value,key)
    return expected
for i,value in enumerate(valid_rationals): equal(result('rational-'+str(i)),q(value),'canonical rational')
for name,A,b in analysis_cases: check_analysis(result(name),A,b)
checks.append(dict(area='exact algebra and consistency',cases=len(analysis_cases),result='pass',method='Rank from all exact permutation minors; independent largest-pivot Fraction Gauss-Jordan; original column bases, canonical free-variable kernel/left-kernel bases and augmented consistency, including rectangular and near-singular matrices.'))
for name,A,B in products: equal(result(name),mm(mat(A),mat(B)),name)
for name,A,v in applies: equal(result(name),mv(mat(A),list(map(q,v))),name)
for name,A,n in powers: equal(result(name),power(mat(A),n),name)
checks.append(dict(area='matrix operations',cases=len(products)+len(applies)+len(powers),result='pass',method='Independent exact dot products and sequential multiplication, including rectangular composition, reflection, nilpotent/defective matrices, rational decay and zero exponent.'))

for i,state in enumerate(map_cases):
    m=result(f'maps-{i}');A=mat(state.get('A',[[2,1],[3,4]]));B=mat(state.get('B',[[2,0],[0,1]]));v=list(map(q,state.get('x',[1,1])));check_analysis(m,A)
    equal(m['output'],mv(A,v),'map output');equal(m['AB'],mm(A,B),'AB');equal(m['BA'],mm(B,A),'BA');equal(m['ABv'],mv(mm(A,B),v),'ABv');equal(m['BAv'],mv(mm(B,A),v),'BAv')
    square=mat([[0,0],[1,0],[1,1],[0,1]]);mapped=[mv(A,p) for p in square];equal(m['mappedSquare'],mapped,'mapped actual square vertices')
    shoelace=sum(mapped[j][0]*mapped[(j+1)%4][1]-mapped[j][1]*mapped[(j+1)%4][0] for j in range(4))/2
    assert shoelace==det(A)
    equal(m['linearityResidual'],[F(0),F(0)],'linearity identity')
for i,state in enumerate(system_cases):
    m=result(f'system-{i}');A=mat([[state['k'],2],[8,state['k']]]);b=list(map(q,[1,state['rhs2']]));expected=check_analysis(m,A,b)
    if expected['particular'] is not None:
        chosen=expected['particular'][:]
        if expected['kernelBasis']: chosen=[a+q(state['free'])*v for a,v in zip(chosen,expected['kernelBasis'][0])]
        equal(m['chosen'],chosen,'chosen exact system member');equal(m['chosenResidual'],[F(0),F(0)],'exact system residual')
    else: assert m['chosen'] is None
checks.append(dict(area='maps and parameterized systems',cases=len(map_cases)+len(system_cases),result='pass',method='Independent shoelace area and composition order; exact inconsistent k=±4, consistent singular comparisons and accepted near-singular distant intersections.'))

for i,state in enumerate(space_cases):
    m=result(f'space-{i}');t=q(state['t']);kind=state['kind']
    A=mat([[1,0,1-t],[0,1,1-t],[1,1,2+t]]) if kind=='family' else mat({'repeated':[[1,1,2],[2,2,1],[3,3,1]],'rank1':[[1,2,3],[2,4,6],[3,6,9]],'zero':[[0,0,0],[0,0,0],[0,0,0]]}[kind]);expected=check_analysis(m,A)
    equal(m['output'],mv(A,list(map(q,state['coefficients']))),'3D output');equal(m['columnVectors'],tr(A),'actual 3D columns')
    for original,mapped in zip(m['unitCube'],m['mappedCube']): equal(mapped,mv(A,list(map(q,original))),'3D cube corner')
    p=mat(m['mappedCube']);a=[p[1][j]-p[0][j] for j in range(3)];b=[p[2][j]-p[0][j] for j in range(3)];c=[p[4][j]-p[0][j] for j in range(3)]
    oriented=a[0]*(b[1]*c[2]-b[2]*c[1])-a[1]*(b[0]*c[2]-b[2]*c[0])+a[2]*(b[0]*c[1]-b[1]*c[0]);assert oriented==det(A)
    if kind=='family': assert oriented==3*t
    if expected['rank']==2:
        normal=list(map(q,m['imagePlaneNormal']));assert normal!=[0,0,0]
        assert all(dot(normal,p)==0 for p in tr(A)+mat(m['spanPatch']))
for i,state in enumerate(kernel_cases):
    m=result(f'kernel-{i}');A=mat({'4x4':[[1,0,0,1],[0,1,0,2],[0,0,1,3],[0,0,0,0]],'3x4':[[1,0,0,1],[0,1,0,2],[0,0,1,3]],'2x4':[[1,0,1,0],[0,1,0,1]]}[state['kind']]);expected=check_analysis(m,A);base=list(map(F,[2,3,4,5]));x=base[:]
    for coefficient,v in zip(state['coefficients'],expected['kernelBasis']): x=[a+q(coefficient)*b for a,b in zip(x,v)]
    equal(m['input'],x,'full four-coordinate input');equal(m['output'],mv(A,base),'kernel family invariant');equal(m['inputNormSquared'],dot(x,x),'true 4D norm squared');near(m['inputNormApprox'],math.sqrt(dot(x,x)),'4D norm');assert len(m['input'])==4 and len(m['output'])==len(A)
    assert 'not a spatial projection' in m['displayMeaning']
checks.append(dict(area='3D geometry and four-coordinate kernels',cases=len(space_cases)+len(kernel_cases),result='pass',method='All cube corners and oriented triple-product volume, rank-drop plane membership, complete 4D coordinates and rectangular kernel-family invariance.'))

for kind,(raw,values) in spectra.items():
    m=result('spectrum-'+kind);A=mat(raw);check_analysis(m,A)
    if kind=='rotation':
        assert m['eigenspaces']==[] and not m['hasEigenbasisOverR'] and m['hasEigenbasisOverC']
        for pair in m['complexEigenpairs']:
            value=complex(float(q(pair['value']['real'])),float(q(pair['value']['imaginary'])));v=[complex(float(q(z['real'])),float(q(z['imaginary']))) for z in pair['vector']]
            assert all(abs(sum(float(a)*b for a,b in zip(row,v))-value*w)<1e-14 for row,w in zip(A,v))
        equal(m['eigenvalueSum'],F(0),'complex trace');equal(m['eigenvalueProduct'],F(1),'complex determinant')
        assert 'no nonzero real eigenvector' in m['limit']
    else:
        values=list(map(q,values));equal(m['eigenvalues'],values,'exact fixture eigenvalues');equal(m['eigenvalueSum'],sum(values),'spectrum trace');equal(m['eigenvalueProduct'],math.prod(values),'spectrum product')
        # Verify the entire characteristic polynomial by exact determinant evaluations.
        for x in [-2,0,1,2,4,6]: assert det([[F(x)*(i==j)-A[i][j] for j in range(len(A))] for i in range(len(A))])==math.prod(F(x)-v for v in values)
        all_vectors=[]
        for space in m['eigenspaces']:
            lam=q(space['value']);shift=[[A[i][j]-lam*(i==j) for j in range(len(A))] for i in range(len(A))];basis=kernel(shift);equal(space['basis'],basis,'canonical eigenspace');assert space['geometricMultiplicity']==len(basis) and space['algebraicMultiplicity']==values.count(lam);all_vectors.extend(basis)
        eigen_rank=minor_rank(tr(all_vectors)) if all_vectors else 0
        assert m['eigenvectorBasisRank']==eigen_rank and m['hasEigenbasis']==(eigen_rank==len(A))
for i,state in enumerate(orbit_cases):
    m=result(f'orbit-{i}');A=mat(spectra[state['kind']][0]);v=list(map(q,state['initial']));history=[]
    assert len(m['points'])==state['n']+1 and m['normalizationApplied'] is False
    for n,point in enumerate(m['points']):
        assert point['n']==n;equal(point['value'],v,'every orbit value');equal(point['normSquared'],dot(v,v),'exact orbit norm');near(point['normApprox'],math.sqrt(dot(v,v)),'orbit norm approximation');history.append(v);v=mv(A,v)
    equal(m['power'],power(A,state['n']),'orbit power matrix');equal(m['last'],history[-1],'last orbit point');assert m['directionDefined']==any(history[-1])
    expected_peak=max(range(len(history)),key=lambda n:dot(history[n],history[n]));assert m['finiteTracePeakIndex']==expected_peak
    if state['kind']=='decay-nonnormal':
        for n,actual in enumerate(history):
            x,y=list(map(q,state['initial']));expected=[F(1,2)**n*x+25*(F(9,10)**n-F(1,2)**n)*y,F(9,10)**n*y];assert actual==expected
        if state['initial']==[0,1]:
            assert history[2]==[14,F(81,100)] and history[3]==[F(151,10),F(729,1000)] and expected_peak==3
            metrics['nonnormal_transient']={'n2':strings(history[2]),'norm2':math.sqrt(dot(history[2],history[2])),'n3':strings(history[3]),'norm3':math.sqrt(dot(history[3],history[3])),'peakIndex':3,'n100':strings(history[100])}
    if state['kind']=='rotation': assert all(dot(v,v)==dot(history[0],history[0]) for v in history) and history[4]==history[0]
checks.append(dict(area='spectra and repeated powers',cases=len(spectra)+len(orbit_cases),result='pass',method='Characteristic polynomial evaluations and exact nullspaces, identity/defective shear distinction, explicit complex quarter-turn eigenpairs, exact entire orbits and independent nonnormal closed form with n=2 versus n=3.'))

def plane_vertices(normal,rhs,L):
    # Independent face-pair intersections: fix two cube coordinates, solve the third.
    points=set()
    for free in range(3):
        if not normal[free]: continue
        fixed=[j for j in range(3) if j!=free]
        for values in product([-L,L],repeat=2):
            p=[F(0)]*3
            for j,value in zip(fixed,values): p[j]=value
            p[free]=(rhs-dot(normal,p))/normal[free]
            if abs(p[free])<=L: points.add(tuple(p))
    return points

for i,state in enumerate(plane_cases):
    m=result(f'planes-{i}');raw,b=plane_matrices[state['kind']];A=mat(raw);b=list(map(q,b));expected=check_analysis(m,A,b);L=q(m['boxHalfWidth']);assert L>=4
    for normal,rhs,polygon in zip(A,b,m['planePolygons']):
        vertices=mat(polygon);assert set(map(tuple,vertices))==plane_vertices(normal,rhs,L)
        assert all(dot(normal,v)==rhs and max(map(abs,v))<=L for v in vertices)
        # Convex boundary order, not a self-crossing shuffle of valid corners.
        signs=[]
        for j in range(len(vertices)):
            p0,p1,p2=vertices[j-1],vertices[j],vertices[(j+1)%len(vertices)];u=[a-b for a,b in zip(p1,p0)];v=[a-b for a,b in zip(p2,p1)];cross=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]];turn=dot(cross,normal)
            if turn: signs.append(turn>0)
        assert len(set(signs))==1
    if expected['classification']=='none': assert m['chosen'] is None and m['commonLine'] is None and m['intersectionDimension'] is None
    else:
        x=expected['particular'][:]
        for coefficient,v in zip(state['free'],expected['kernelBasis']): x=[a+q(coefficient)*b for a,b in zip(x,v)]
        equal(m['chosen'],x,'affine solution member');assert m['intersectionDimension']==expected['nullity'];assert max(map(abs,x))<L
        if m['commonLine'] is not None:
            for p in mat(m['commonLine']): assert mv(A,p)==b and max(map(abs,p))==L
    assert 'affine' in m['geometryMeaning'] and 'clipped' in m['geometryMeaning']
for i,state in enumerate(cameras):
    m=result(f'camera-{i}');P=m['matrix'];assert len(P)==3 and all(len(row)==3 for row in P)
    for r in range(3):
        for c in range(3): near(sum(P[r][j]*P[c][j] for j in range(3)),float(r==c),'orthonormal camera basis')
    assert m['kind']=='orthographic' and m['numericApproximation']
checks.append(dict(area='affine constraint planes and camera',cases=len(plane_cases)+len(cameras),result='pass',method='Independent exact cube-face-pair intersections recover all polygon vertices; plane residuals, convex ordering and common point/line/plane or empty classifications; orthonormal declared projection coordinates.'))
for name in invalid: assert 'error' in data[name] and data[name]['error']['name'] in ['RangeError','TypeError'],data[name]
checks.append(dict(area='invalid domains',cases=len(invalid),result='pass',method='Invalid rational grammar, nonfinite values, declared magnitude/denominator bounds, ragged/oversized shapes, incompatible dimensions and unsupported spectrum/camera/iteration states rejected.'))
assert hashlib.sha256((ROOT/'web/linear-algebra-lab.js').read_bytes()).hexdigest()==reply['sourceSHA256']
report={'sourceSHA256':reply['sourceSHA256'],'purePrefixSHA256':reply['purePrefixSHA256'],'checks':checks,'metrics':metrics,'requests':len(requests),'allPassed':True,'remainingActionableDefects':[],'rendererVerifiedByThisReceipt':False,'scope':'Exact small rational matrices and declared fixture APIs. A bounded quarter-turn complex contrast is checked; no general numerical or complex eigensolver is claimed.'}
if args.write_proof:
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'numerical-review.json').write_text(json.dumps(report,indent=2)+'\n')
    (OUT/'numerical-requests.json').write_text(json.dumps(requests,indent=2)+'\n')
    (OUT/'numerical-results.json').write_text(json.dumps(reply,indent=2)+'\n')
print(json.dumps(report,indent=2))
