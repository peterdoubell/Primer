"""Independent finite-wall quadrature and ODE comparison for pipe dynamics."""
import hashlib,json,subprocess
from pathlib import Path
import numpy as np
from scipy.special import ellipk,ellipe
from scipy.integrate import solve_ivp
from scipy.interpolate import CubicSpline
from numpy.polynomial.legendre import leggauss
R=Path(__file__).resolve().parents[1];O=R/'.research/circuits-integration';mu=1.25663706127e-6
code="const c=require('./web/circuits-induction-core.js');console.log(JSON.stringify([{}, {conductivityMS:0},{magnetizationKA:0},{magnetizationKA:-1300},{gravity:0},{gravity:10},{massG:5},{massG:100},{magnetRadiusMM:2},{magnetLengthMM:5},{magnetLengthMM:40},{innerRadiusMM:40},{wallMM:.2},{wallMM:4},{lengthCM:15,releaseCM:7.5},{lengthCM:60,releaseCM:25},{releaseCM:-10},{conductivityMS:.001},{magnetRadiusMM:2,magnetLengthMM:5,massG:100,innerRadiusMM:40,wallMM:.2}].map(state=>{const m=c.pipe(state);return {state:m.state,exitTime:m.exitTime,solvedUntil:m.solvedUntil,points:m.points,probes:Array.from({length:21},(_,i)=>m.at(m.solvedUntil*i/20))}})));"
models=json.loads(subprocess.check_output(['node','-e',code],text=True))
x,w=leggauss(24)
def coefficient(s,z):
 a=s['magnetRadiusMM']/1000;length=s['magnetLengthMM']/1000;M=s['magnetizationKA']*1000;r1=s['innerRadiusMM']/1000;r2=r1+s['wallMM']/1000;half=s['lengthCM']/200
 if s['conductivityMS']==0:return 0.
 rs=(r1+r2)/2+x*(r2-r1)/2
 # Independent complete elliptic integrals, rather than runtime AGM.
 def mutual(r,d):
  k2=4*a*r/((a+r)**2+d*d)
  return mu*np.sqrt(a*r)/np.sqrt(k2)*((2-k2)*ellipk(k2)-2*ellipe(k2))
 total=[]
 for r in rs:
  bounds=sorted(set([z-half,z+half]+[t for end in [-length/2,length/2] for scale in [-16,-8,-4,-2,-1,-.5,0,.5,1,2,4,8,16] if z-half<(t:=end+scale*r)<z+half]))
  lo=np.array(bounds[:-1]);hi=np.array(bounds[1:]);u=(lo[:,None]+hi[:,None])/2+(hi-lo)[:,None]*x/2
  grad=M*(mutual(r,u+length/2)-mutual(r,u-length/2))
  total.append(np.sum((hi-lo)/2*np.sum(grad*grad*w,axis=1))/r)
 return s['conductivityMS']*1e6/(2*np.pi)*(r2-r1)/2*np.dot(w,total)
rows=[]
for model in models:
 s=model['state'];mass=s['massG']/1000;g=s['gravity'];z0=s['releaseCM']/100;exit_z=-s['lengthCM']/200-s['magnetLengthMM']/2000
 zs=np.linspace(exit_z,z0,401);cs=np.array([coefficient(s,z)for z in zs]);interp=CubicSpline(zs,cs)
 def rhs(t,y):
  c=float(interp(np.clip(y[0],exit_z,z0)));return [y[1],-g-c*y[1]/mass,c*y[1]**2]
 sol=solve_ivp(rhs,[0,model['solvedUntil']],[z0,0,0],rtol=2e-10,atol=2e-12,dense_output=True,max_step=.005)
 errors={'position_m':0.,'velocity_m_s':0.,'heat_J':0.,'coefficient_relative':0.,'energy_J':0.}
 for p in model['probes']:
  truth=sol.sol(p['t']);expected=coefficient(s,p['z'])
  for key,actual,want in zip(['position_m','velocity_m_s','heat_J'],[p['z'],p['v'],p['Q']],truth):errors[key]=max(errors[key],abs(actual-want))
  errors['coefficient_relative']=max(errors['coefficient_relative'],abs(p['c']-expected)/max(expected,1e-20))
  errors['energy_J']=max(errors['energy_J'],abs(.5*mass*p['v']**2+mass*g*(p['z']-z0)+p['Q']))
 assert errors['position_m']<2e-5 and errors['velocity_m_s']<2e-4 and errors['heat_J']<2e-5,errors
 assert errors['coefficient_relative']<1e-7 and errors['energy_J']<1e-8,errors
 if s['conductivityMS']==0:assert all(p['c']==p['force']==p['heatPower']==p['Q']==0 for p in model['points'])
 rows.append({'state':s,'conductivityMS':s['conductivityMS'],'probes':len(model['probes']),'exitTime':model['exitTime'],'maximumErrors':errors})
report={'allPassed':True,'sourceSHA256':hashlib.sha256((R/'web/circuits-induction-core.js').read_bytes()).hexdigest(),'oracleSHA256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'method':'SciPy complete elliptic integrals; independent finite-wall quadrature on401positions; CubicSpline coefficient and solve_ivp trajectory/heat integration','rows':rows,'scope':'Nineteen default, boundary and combined-extreme trajectories; not an exhaustive control-domain proof or whole-goal approval.'}
print(json.dumps(report,indent=2))
