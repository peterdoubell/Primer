"""Independent physical checks for the new electricity/EM stations.
No tracked files or frozen proofs are changed by this script.
"""
from pathlib import Path
import json,subprocess,math,hashlib,itertools,time
import numpy as np
from scipy.integrate import quad, solve_ivp
from scipy.special import ellipk,ellipe
from numpy.polynomial.legendre import leggauss
ROOT=Path(__file__).resolve().parents[1];OUT=Path(__file__).resolve().parent
EPS=8.8541878188e-12;MU=1.25663706127e-6
checks={};maximum={}
def near(actual,expected,name,rtol=3e-9,atol=1e-14):
 error=abs(actual-expected);scale=max(abs(expected),atol/rtol);maximum[name]=max(maximum.get(name,0),error/scale)
 assert math.isfinite(actual) and error<=atol+rtol*abs(expected),(name,actual,expected,error)
 checks[name]=checks.get(name,0)+1

def bridge(queries):
 code="""const fs=require('fs'),c=require('./web/circuits-induction-core.js');const qs=JSON.parse(fs.readFileSync(0));console.log(JSON.stringify(qs.map(q=>{const m=q.args?c[q.method](...q.args):c[q.method](q.state);if(typeof m==='number'||m===null)return m;if(q.times)m.probes=q.times.map(t=>m.at(t));if(m.points)m.points=m.points.filter((p,i)=>i%Math.max(1,Math.floor(m.points.length/24))===0||i===m.points.length-1);return m;})));"""
 return json.loads(subprocess.run(['node','-e',code],input=json.dumps(queries),cwd=ROOT,text=True,capture_output=True,check=True).stdout)

def mutual_ref(a,r,z):
 # Independent Neumann line integral, using direct geometric distance and
 # periodic quadrature rather than the browser's AGM elliptic combination.
 angle=(np.arange(2048)+.5)*2*np.pi/2048;cs=np.cos(angle);D=a*a+r*r+z*z;distance=np.sqrt(D-2*a*r*cs)
 integrand=cs*(2*a*r*cs)/(np.sqrt(D)*distance*(np.sqrt(D)+distance))
 return MU*a*r/2*np.mean(integrand)*2*np.pi

def flux_ref(a,length,M,r,z):
 xs,ws=leggauss(96);return M*length/2*sum(w*mutual_ref(a,r,z-x*length/2)for x,w in zip(xs,ws))

def gradient_ref(a,length,M,r,z):
 return M*(mutual_ref(a,r,z+length/2)-mutual_ref(a,r,z-length/2))

def main():
 started=time.monotonic()
 states=[{'chargeNC':q,'radiusCM':R,'gapCM':gap,'permittivity':k,'wall':wall}for q,R,gap,k,wall in itertools.product([-50,0,50],[1,10],[0,5],[1,4,12],['dielectric','conductor'])]
 for m in bridge([{'method':'charge','state':s}for s in states]):
  q=m['q'];R=m['r'];d=m['d'];image=m['image'];k=1/(4*math.pi*EPS)
  expected=q/2*quad(lambda u:k*image*(2*d+R*u)/(4*d*d+R*R+4*d*R*u)**1.5,-1,1,epsabs=1e-17,epsrel=1e-11)[0]
  near(m['force'],expected,'finite_shell_force',atol=1e-15)
  integrated=quad(lambda rho:2*math.pi*rho*image*d/(2*math.pi*(rho*rho+d*d)**1.5),0,m['crop'],epsabs=1e-18)[0]
  near(m['capturedBoundCharge'],integrated,'wall_charge_integral',atol=1e-18)
  near(m['energy'],-k*q*q*m['contrast']/(4*d),'wall_energy',atol=1e-16)
  near(q+m['partnerCharge']+m['interfaceCharge']+m['remoteCompensation'],0,'complete_charge_ledger',atol=1e-20)
 states=[{'material':kind,'voltageMV':V,'lengthM':L,'areaMM2':A,'logConductivity':log}for kind,V,L,A,log in itertools.product(['copper','insulator','custom'],[0,1,10],[.1,2],[.1,2],[-14,8])]
 for m in bridge([{'method':'material','state':s}for s in states]):
  s=m['state'];sigma=58e6 if s['material']=='copper'else 0 if s['material']=='insulator'else 10**s['logConductivity'];V=s['voltageMV']*.001;A=s['areaMM2']*1e-6;L=s['lengthM']
  near(m['current'],sigma*A*V/L,'material_current',atol=1e-30);near(m['power'],quad(lambda x:sigma*(V/L)**2*A,0,L)[0],'material_joule_integral',atol=1e-30)
  if sigma==0:assert m['resistance'] is None and m['current']==0
 states=[{'chargeNC':q,'gapMM':gap,'pressureKPa':p,'secondary':gamma}for q,gap,p,gamma in itertools.product([-5000,0,500,2500],[.1,1,5],[20,101.325,120],[.005,.01,.05])]
 for m in bridge([{'method':'spark','state':s}for s in states]):
  s=m['state'];d=m['d'];p=m['p'];A=15/(101325/760*.01);B=365/(101325/760*.01);target=math.log1p(1/s['secondary'])
  # Numerically invert the Townsend multiplication condition rather than use
  # the browser's explicitly rearranged Paschen voltage.
  lo,hi=1e-6,1e7
  for _ in range(90):
   mid=(lo+hi)/2;gain=A*p*d*math.exp(-B*p*d/mid)
   if gain<target:lo=mid
   else:hi=mid
  threshold=(lo+hi)/2;near(m['threshold'],threshold,'Townsend_onset',atol=1e-8)
  near(m['energy'],m['q']**2*d/(2*EPS*m['area']),'capacitor_energy',atol=1e-16)
  assert m['breakdown']==(abs(m['voltage'])>=threshold)
 states=[{'current1':a,'current2':b,'separationCM':d,'lengthM':L}for a,b,d,L in itertools.product([-20,0,20],[-20,0,20],[1,20],[.5,5])]
 for m in bridge([{'method':'wires','state':s}for s in states]):
  s=m['state'];d=m['d'];integral=quad(lambda u:1/(1+u*u)**1.5,-np.inf,np.inf,epsabs=1e-12)[0];B=MU*s['current1']/(4*np.pi*d)*integral
  near(m['fieldAt2Due1'],B,'Biot_Savart_wire_field');near(m['force2'],-s['current2']*s['lengthM']*B,'Lorentz_wire_force');near(m['force1']+m['force2'],0,'wire_interaction_pair')
 states=[{'primaryTurns':n1,'secondaryTurns':n2,'coupling':k,'connection':connection,'drive':drive,'phase':phase}for n1,n2,k,connection,drive,phase in itertools.product([10,100,500],[10,200,500],[0,.98,.9999],['load','open','short'],['ac','dc'],[0,75])]
 for m in bridge([{'method':'transformer','state':s}for s in states]):
  s=m['state'];w=2*np.pi*s['frequency']if s['drive']=='ac'else 0;L1=m['L1'];L2=m['L2'];M=m['M'];R=s['load']if s['connection']!='short'else 0
  if s['connection']=='open':ip=s['voltage']/(s['primaryResistance']+1j*w*L1);isec=0j;vs=1j*w*M*ip
  else:
   ip,isec=np.linalg.solve(np.array([[s['primaryResistance']+1j*w*L1,1j*w*M],[1j*w*M,s['secondaryResistance']+R+1j*w*L2]]),np.array([s['voltage'],0]));vs=-R*isec
  for key,value in [('I1',ip),('I2',isec),('Vs',vs)]:near(m[key][0],value.real,'transformer_complex_solve',atol=1e-10);near(m[key][1],value.imag,'transformer_complex_solve',atol=1e-10)
  near(m['inputPower'],R*abs(isec)**2+s['primaryResistance']*abs(ip)**2+s['secondaryResistance']*abs(isec)**2,'transformer_mean_power',atol=1e-9)
  assert np.linalg.eigvalsh([[L1,M],[M,L2]])[0]>0
  for p in m['points']:near(p['inputP'],p['loadP']+p['heat']+p['storedPower'],'transformer_instant_power',atol=1e-8);assert p['stored']>=-1e-14
 # The new finite magnet must retain actual radius and length, including near
 # field where a point dipole or B_axis*area shortcut is inaccurate.
 queries=[];params=[]
 for a,L,r,z in itertools.product([.002,.006,.01],[.005,.02,.04],[.015,.03,.05],[-.1,-.01,0,.01,.1]):
  if r<1.25*a:continue
  M=8e5;queries.append({'method':'cylinderFlux','args':[a,L,M,r,z]});params.append((a,L,M,r,z))
 for value,args in zip(bridge(queries),params):near(value,flux_ref(*args),'finite_cylinder_Neumann_flux',rtol=2e-8,atol=2e-13)
 queries=[];params=[]
 for a,r,z in itertools.product([.002,.01],[.015,.05],[0,.001,.1,1]):queries.append({'method':'loopMutual','args':[a,r,z]});params.append((a,r,z))
 for value,args in zip(bridge(queries),params):near(value,mutual_ref(*args),'AGM_vs_Neumann_mutual',rtol=2e-10,atol=1e-20)
 states=[{'speed':v,'inductance':L,'time':t}for v,L,t in itertools.product([-.2,0,.2],[0,.001,.1],[0,.25,.5,.75,1])]
 for m in bridge([{'method':'finiteMagnet','state':s}for s in states]):
  s=m['state'];p=m['current'];a=m['a'];L=m['length'];M=m['M'];r=m['r'];v=m['v'];z0=m['z0'];t=s['time'];R=s['resistance'];N=s['turns'];ind=s['inductance'];grad=gradient_ref(a,L,M,r,z0+v*t);emf=-N*v*grad
  near(p['emf'],emf,'finite_source_Faraday',rtol=2e-9,atol=1e-11)
  if ind==0:current=emf/R
  else:
   tau=ind/R;end=min(45,t/tau);current=quad(lambda u:-N*v*gradient_ref(a,L,M,r,z0+v*(t-tau*u))*math.exp(-u)/R,0,end,epsabs=1e-11,epsrel=1e-9,limit=120)[0]
  near(p['current'],current,'finite_source_RL_convolution',rtol=2e-7,atol=1e-10)
  near(p['force'],N*current*grad,'finite_source_reciprocal_force',rtol=2e-7,atol=1e-10)
  near(p['drivePower'],p['heat']+p['storedPower'],'finite_source_power',atol=1e-10)
 # Primary-source numerical benchmark: Partovi & Morris, discussion of the
 # MacLatchy experiment. Their finite-geometry prediction is0.119±0.005m/s.
 moment=.67;radius=.0063;length=.0064;M=moment/(np.pi*radius**2*length)
 benchmark={'magnetRadiusMM':6.3,'magnetLengthMM':6.4,'magnetizationKA':M/1000,'innerRadiusMM':7.29,'wallMM':.67,'lengthCM':170,'conductivityMS':50.8}
 coefficient=bridge([{'method':'pipeCoefficient','args':[benchmark,0,12,16]}])[0];terminal=.060/coefficient;assert abs(terminal-.119)<.005
 report={'allPassed':True,'sourceSHA256':hashlib.sha256((ROOT/'web/circuits-induction-core.js').read_bytes()).hexdigest(),'checks':checks,'maximumScaledErrors':maximum,'primaryPipeBenchmark':{'predictedTerminalMS':terminal,'publishedFiniteGeometryPredictionMS':.119,'publishedUncertaintyMS':.005,'momentAm2':moment,'weightN':.060,'source':'https://arxiv.org/abs/physics/0406085'},'elapsedSeconds':time.monotonic()-started,'limits':'Declared bounded models, numerical geometry and circuit laws; no claim of real-component validation or whole-physics completion.'}
 print(json.dumps(report,indent=2))
if __name__=='__main__':main()
