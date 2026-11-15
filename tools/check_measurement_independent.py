"""Independent scientific checks using complex-step and exact rational algebra."""
from pathlib import Path
from fractions import Fraction as F
import argparse,hashlib,json,math,subprocess
import numpy as np
if not __debug__:
 raise RuntimeError('Run the scientific checker without Python optimization so every assertion executes.')
ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/'docs/measurement-fidelity-review-20261016/independent-review/regression-output'
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--write-proof',action='store_true',help='Write receipts only to the fixed independent-review/regression-output directory')
args=parser.parse_args()
requests=[];checks=[];metrics={}
def ask(id,method,*args):requests.append({'id':id,'method':method,'args':list(args)});return id
prop=[]
for op in ['sum','difference','ratio','gravity']:
 for a,b,ua,ub in [(10,2,.1,.04),(0,2,.125,.25),(1,1,.125,.125)]:
  for rho in [-1,-.625,0,.625,1]:
   s=dict(operation=op,a=a,b=b,ua=ua,ub=ub,rho=rho);id=ask(f'prop-{len(prop)}','propagate',s);prop.append((id,s))
intervals=[]
for op in ['sum','difference']:
 for a,b,da,db in [(-3,2,4,1),(2,-3,1,4),(-2,-7,1,3),(0,0,2,3),(1e3,-1e3,.25,.5)]:
  s=dict(operation=op,a=a,b=b,da=da,db=db);intervals.append((ask(f'interval-{len(intervals)}','interval',s),s))
for op in ['ratio','gravity']:
 for a,b,da,db in [(10,2,1,1.5),(1,1,1,.5),(.1,.01,.01,.005),(100,.1,20,.09)]:
  s=dict(operation=op,a=a,b=b,da=da,db=db);intervals.append((ask(f'interval-{len(intervals)}','interval',s),s))
invalid=[]
for op in ['ratio','gravity']:
 for a,b,da,db in [(1,1,.1,1),(1,1,.1,2),(1,-1,.1,.1),(0,1,.1,.1),(1,1e-6,.1,1e-12)]:
  invalid.append(ask(f'invalid-bound-{len(invalid)}','interval',dict(operation=op,a=a,b=b,da=da,db=db)))
repeats=[]
for n in [1,2,17,400]:
 for mode in ['included-in-scatter','shared-uniform','independent-uniform']:
  for offset,correction in [(.2,0),(.2,.2),(-.2,-.1)]:
   s=dict(n=n,readingStd=.2,calibrationStd=.05,resolution=.1,resolutionMode=mode,target=5,offset=offset,correction=correction)
   repeats.append((ask(f'repeat-{len(repeats)}','repeatBudget',s),s))
fitting=[]
def add_fit(name,rows,options=None):
 fitting.append((ask(name,'weightedLineFit',rows,*([options] if options else [])),rows,options or {'mode':'fit'}))
add_fit('heteroscedastic',[{'x':x,'y':y,'sigma':s} for x,y,s in [(-2,3,1),(-1,0,.5),(1,2,2),(3,7,1),(5,8,.5)]])
add_fit('uniform',[{'x':x,'y':y,'sigma':1}for x,y in [(-2,-3),(-1,2),(0,1),(1,4),(2,9)]])
for origin in [0,999999,-999999]:
 add_fit('subulp-mean-origin-'+str(origin),[{'x':origin+i*2**-33,'y':y,'sigma':s}for i,y,s in [(0,1,1),(1,2,1),(2,4,2)]])
add_fit('large-y-small-deviations',[{'x':i,'y':999999+i*2**-33,'sigma':s} for i,s in [(0,1),(1,1),(2,2)]])
for scale in [.125,8]:
 add_fit('residual-scale-'+str(scale),[{'x':i,'y':1+2*i+scale*r,'sigma':1}for i,r in zip([-2,-1,0,1,2],[1,-2,2,-2,1])])
add_fit('known-sigma-times-four',[{'x':x,'y':y,'sigma':4*s} for x,y,s in [(-2,3,1),(-1,0,.5),(1,2,2),(3,7,1),(5,8,.5)]])
add_fit('fixed-reference',[{'x':x,'y':y,'sigma':s}for x,y,s in [(0,2,1),(1,4,.5),(3,8,2)]],{'mode':'reference','intercept':1,'slope':2})
add_fit('rank-deficient-fixed-reference',[{'x':2,'y':i,'sigma':1}for i in [1,2,3]],{'mode':'reference','intercept':1,'slope':2})
invalid.append(ask('rank-deficient-fit','weightedLineFit',[{'x':2,'y':i,'sigma':1}for i in [1,2,3]]))
for scale in [1e-155,1e-160]:
 invalid.append(ask('unrepresentable-covariance-'+str(scale),'weightedLineFit',[{'x':i*scale,'y':i+1,'sigma':1}for i in range(3)]))
invalid.append(ask('zero-sigma','weightedLineFit',[{'x':i,'y':i,'sigma':0}for i in [1,2,3]]))
examples=[]
for state in [{},{'offset':2},{'sigma':.6},{'scatter':.1,'acceleration':.12},{'outlier':5,'heterogeneous':True},{'mode':'reference','offset':2}]:
 id=ask('example-'+str(len(examples)),'fitExample',state);examples.append((id,state))
reply=json.loads(subprocess.check_output(['node',str(ROOT/'tools/check_measurement_independent.cjs')],input=json.dumps(requests).encode(),cwd=ROOT,timeout=30))
assert reply['sourceSHA256']=='8a1d68588bb9689146a5673c1d2f7f7b4fad10213f53c10f47c4d1c35bd537af'
assert hashlib.sha256((ROOT/'web/measurement-lab.js').read_bytes()).hexdigest()==reply['sourceSHA256']
data={r['id']:r for r in reply['results']}
def near(a,b,label,rel=2e-11,abs_tol=1e-12):
 expected=float(b);assert math.isfinite(a),label
 assert abs(a-expected)<=abs_tol+rel*abs(expected),(label,a,expected)
 return abs(a-expected)
def result(id):assert 'error'not in data[id],data[id];return data[id]['result']
def function(op,a,b):
 if op=='sum':return a+b
 if op=='difference':return a-b
 if op=='ratio':return a/b
 return 4*math.pi**2*a/b**2
for id,s in prop:
 m=result(id);h=1e-30;a=s['a'];b=s['b'];g=np.array([function(s['operation'],a+1j*h,b).imag/h,function(s['operation'],a,b+1j*h).imag/h])
 C=np.array([[s['ua']**2,s['rho']*s['ua']*s['ub']],[s['rho']*s['ua']*s['ub'],s['ub']**2]])
 expected=float(np.einsum('i,ij,j',g,C,g))
 near(m['variance'],max(0,expected),id+' covariance quadratic form');near(m['standard']**2,m['variance'],id+' std squared')
 for actual,want in zip(m['gradient'],g):near(actual,want,id+' complex-step sensitivity')
 assert m['firstOrderApproximation']==(s['operation']in['ratio','gravity'])
 if m['value']==0:assert m['relativeStandard']is None
 if s['rho']==1 and s['ua']==s['ub'] and s['a']==s['b'] and s['operation']in['difference','ratio']:near(m['variance'],0,id+' identical common effect cancels',abs_tol=1e-30)
checks.append({'area':'propagation','result':'pass','method':'Independent complex-step sensitivity and covariance quadratic form, including exact common/anticorrelated cancellation and signed covariance terms','cases':len(prop)})
for id,s in intervals:
 m=result(id);loA=F(s['a'])-F(s['da']);hiA=F(s['a'])+F(s['da']);loB=F(s['b'])-F(s['db']);hiB=F(s['b'])+F(s['db']);op=s['operation']
 if op=='sum':expected=[loA+loB,hiA+hiB]
 elif op=='difference':expected=[loA-hiB,hiA-loB]
 elif op=='ratio':expected=[loA/hiB,hiA/loB]
 else:expected=[4*math.pi**2*float(loA/hiB**2),4*math.pi**2*float(hiA/loB**2)]
 near(m['low'],expected[0],id+' monotonic minimum');near(m['high'],expected[1],id+' monotonic maximum')
 assert 'No probability distribution' in m['interpretation']
 if op in ['sum','difference']:
  near(m['linearizedInterval'][0],m['low'],id+' exact linear lower');near(m['linearizedInterval'][1],m['high'],id+' exact linear upper')
checks.append({'area':'intervals','result':'pass','method':'Rational endpoint extrema derived from monotonicity, negative/zero-crossing voltage intervals, positive length/time ratio and inverse-square domains','cases':len(intervals),'interpretation':'Negative length/time are rejected by the declared physical model; the API does not claim general signed division.'})
for id in invalid:assert 'error'in data[id],data[id]
checks.append({'area':'invalid inputs','result':'pass','cases':len(invalid),'method':'Zero-crossing/time-floor bounds, negative physical domains, rank deficiency and zero sigma are rejected'})
# Quadrature integrates the rectangular rounding model independently of the implementation's Δ²/12 expression.
nodes,weights=np.polynomial.legendre.leggauss(3)
quant_var=float(np.dot(weights,(.1*nodes/2)**2)/2)
for id,s in repeats:
 m=result(id);average=np.full(s['n'],1/s['n']);independent_gain=float(np.dot(average,average));shared_gain=float(average.sum()**2)
 v=s['readingStd']**2*independent_gain+s['calibrationStd']**2*shared_gain
 if s['resolutionMode']!='included-in-scatter':v+=quant_var*(shared_gain if s['resolutionMode']=='shared-uniform' else independent_gain)
 near(m['variance'],v,id+' quadrature/basis response');near(m['residualOffset'],s['offset']-s['correction'],id+' corrected bias')
 near(m['expectedCorrected'],s['target']+s['offset']-s['correction'],id+' corrected expectation')
 if s['resolutionMode']=='included-in-scatter':assert m['resolutionVariance']==0
 assert m['standard']>=m['floor']
checks.append({'area':'repeat budget','result':'pass','cases':len(repeats),'method':'Gauss-Legendre integration of uniform rounding error and independent/shared averaging response vectors; correction changes signed expectation but not uncertainty'})

def exact_fit(rows,options):
 x=[F(r['x']) for r in rows];y=[F(r['y']) for r in rows];w=[1/F(r['sigma'])**2 for r in rows];n=len(rows)
 if options.get('mode')=='reference':
  beta=[F(options.get('intercept',1)),F(options.get('slope',.5))];cov=[[F(0),F(0)],[F(0),F(0)]];dof=n
 else:
  # Exact rational normal equations; no float centering, variance formula or QR copied from the implementation.
  M=[[sum(w),sum(wi*xi for wi,xi in zip(w,x))],[sum(wi*xi for wi,xi in zip(w,x)),sum(wi*xi*xi for wi,xi in zip(w,x))]]
  rhs=[sum(wi*yi for wi,yi in zip(w,y)),sum(wi*xi*yi for wi,xi,yi in zip(w,x,y))]
  det=M[0][0]*M[1][1]-M[0][1]*M[1][0];cov=[[M[1][1]/det,-M[0][1]/det],[-M[1][0]/det,M[0][0]/det]]
  beta=[sum(cov[i][j]*rhs[j] for j in range(2)) for i in range(2)];dof=n-2
 fitted=[beta[0]+beta[1]*xi for xi in x];res=[yi-pi for yi,pi in zip(y,fitted)];chi=sum(wi*ri*ri for wi,ri in zip(w,res))
 leverage=[wi*(cov[0][0]+2*xi*cov[0][1]+xi*xi*cov[1][1]) for wi,xi in zip(w,x)]
 return beta,cov,fitted,res,chi,dof,leverage
fit_receipts=[]
for id,rows,options in fitting+[(id,result(id)['rows'],{'mode':result(id)['mode']})for id,state in examples]:
 m=result(id);beta,cov,pred,res,chi,dof,leverage=exact_fit(rows,options)
 near(m['intercept'],beta[0],id+' intercept',rel=3e-13);near(m['slope'],beta[1],id+' slope',rel=3e-13,abs_tol=1e-23)
 near(m['chiSquare'],chi,id+' chi square',abs_tol=1e-24);assert m['degreesOfFreedom']==dof
 for i in range(2):
  for j in range(2):near(m['parameterCovariance'][i][j],cov[i][j],id+' parameter covariance',abs_tol=1e-25)
 for i,point in enumerate(m['rows']):
  near(point['fitted'],pred[i],id+' prediction');near(point['residual'],res[i],id+' residual',abs_tol=1e-24);near(point['leverage'],leverage[i],id+' leverage');assert -1e-12<=point['leverage']<=1+1e-12
 if options.get('mode','fit')=='fit':near(sum(p['leverage']for p in m['rows']),2,id+' hat matrix rank')
 fit_receipts.append({'id':id,'intercept_rational':str(beta[0]),'slope_rational':str(beta[1]),'chi_square_rational':str(chi),'degrees_of_freedom':dof,'parameter_covariance_rational':[[str(v)for v in r]for r in cov]})
checks.append({'area':'weighted known-sigma fitting','result':'pass','cases':len(fit_receipts),'method':'Exact rational design normal equations and covariance inversion; predictions, residuals, chi square, rank/hat leverage and fixed-reference degrees of freedom'})
a=result('residual-scale-0.125');b=result('residual-scale-8');assert a['parameterCovariance']==b['parameterCovariance'];near(b['chiSquare']/a['chiSquare'],4096,'residual-scale chi square factor')
a=result('heteroscedastic');b=result('known-sigma-times-four');near(b['chiSquare'],a['chiSquare']/16,'sigma scale chi square');
for i in range(2):
 for j in range(2):near(b['parameterCovariance'][i][j],16*a['parameterCovariance'][i][j],'sigma scale covariance')
checks.append({'area':'no silent residual rescaling','result':'pass','method':'Residual amplitude changed64-fold leaves known-sigma covariance identical while chi square changes4096-fold; sigma4-fold scales covariance16-fold and chi square by1/16'})
a=result('example-0');b=result('example-1');near(b['intercept']-a['intercept'],2,'synthetic common offset absorbed in free intercept');near(a['chiSquare'],b['chiSquare'],'offset leaves residual chi square');assert len(b['rows'])==12
for id,state in examples:assert 'not a random sample' in result(id)['syntheticNote'] and len(result(id)['rows'])==12
checks.append({'area':'synthetic fit meaning','result':'pass','method':'All12 fixed observations remain; common offset is absorbed by free intercept; synthetic notes distinguish fixed residual design from empirical randomness'})

report={'sourceSHA256':reply['sourceSHA256'],'pureAPIPrefixSHA256':reply['pureAPIPrefixSHA256'],'checks':checks,'initial_defect':{'description':'Rounded large x mean was reused to center tiny valid x separations, violating translation invariance and producing leverage>1.','fixture':'tools/check_measurement_independent.py: subulp-mean-origin fixtures','corrected_in_reviewed_source':True,'expected_fitted':[8/9,20/9,32/9],'expected_chi_square':1/9},'remaining_actionable_scientific_defects':[],'renderer_verified_by_this_review':False,'allPassed':True}
tiny=[r for r in reply['results'] if r['id'].startswith('unrepresentable-covariance-')]
for row in tiny:assert row['error']['name']=='RangeError' and 'rescale' in row['error']['message'].lower()
report['finalDisposition']='accepted_for_checked_scientific_APIs_and_declared_domains'
report['tiny_spacing_defect']={'corrected_in_reviewed_source':True,'fixtures':tiny,'resolution':'Explicit RangeError requests rescaling x before subnormal moments or non-finite parameter covariance are returned.','nonfinite_results_returned':False}
report['frozen_source_before_and_after_sha256']=reply['sourceSHA256']
report['primary_references']=[{'url':'https://www.nist.gov/pml/nist-technical-note-1297/nist-tn-1297-appendix-law-propagation-uncertainty','scope':'Sensitivity/covariance, independent-repeat mean and rectangular distribution variance'},{'url':'https://www.nist.gov/pml/nist-technical-note-1297/nist-tn-1297-5-combined-standard-uncertainty','scope':'Recognized systematic correction and its uncertainty are distinct from error'},{'url':'https://www.itl.nist.gov/div898/handbook/pmd/section4/pmd432.htm','scope':'Weighted quadratic residual criterion and correlated parameter estimates'}]
for check in report['checks']:
 if check['area']=='invalid inputs':check['method']+='; unrepresentable tiny-spacing fits explicitly request x rescaling'
report['requestCount']=len(requests)
if args.write_proof:
 OUTPUT.mkdir(parents=True,exist_ok=True)
 for name,value in [('api-results.json',reply),('exact-fit-receipts.json',fit_receipts),('review.json',report)]:
  (OUTPUT/name).write_text(json.dumps(value,indent=2)+'\n')
print(json.dumps(report,indent=2))
