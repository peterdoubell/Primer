from pathlib import Path
import itertools,json,subprocess,math,hashlib,argparse
from scipy.integrate import quad
R=Path(__file__).resolve().parents[1];D=R/'docs/physics-rotation-review-20261102/prototype'
parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=D.parent/'runtime-core-proof.json');args=parser.parse_args()
params=[dict(diskMass=m,diskA=a,diskB=b,haloScaleMass=h,haloRadius=s)for m,a,b,h,s in itertools.product([0,1e10,1e11],[0,1,6],[.1,1],[0,1e11,1e12],[5,20,50])]
radii=[0,1e-9,1e-6,.001,.1,1,8,20,40,100]
requests=[{'r':r,'p':p}for p in params for r in radii]
script="const fs=require('fs'),unused=(global.window={},require('__CORE__')),c=window.RotationCore;console.log(JSON.stringify(JSON.parse(fs.readFileSync(0,'utf8')).map(q=>c.model(q.r,q.p))));"
script=script.replace('__CORE__',str(R/'web/physics-rotation-core.js'))
values=json.loads(subprocess.check_output(['node','-e',script],input=json.dumps(requests),text=True))
G=6.67430e-11*1.988409870698051e30/3.0856775814913673e19/1e6;maxmass=maxspeed=maxgradient=0.;gradientchecks=0
for request,v in zip(requests,values):
 r=request['r'];p=request['p'];x=r/p['haloRadius'];fraction=quad(lambda u:x*x*u/(1+x*u)**2,0,1,epsabs=1e-30,epsrel=1e-12)[0];mass=p['haloScaleMass']*fraction
 error=abs(v['haloEnclosedMassSolar']-mass)/max(abs(mass),1e-100);maxmass=max(maxmass,error);assert error<2e-10
 if r==0:assert v['totalSpeedKms']==0;continue
 a=p['diskA']+p['diskB'];disk2=G*p['diskMass']*r*r/(r*r+a*a)**1.5;halo2=G*mass/r;expected=math.sqrt(disk2+halo2);err=abs(v['totalSpeedKms']-expected)/max(expected,1e-100);maxspeed=max(maxspeed,err);assert err<2e-10
 if r>=.1:
  def potential(z):return -G*p['diskMass']/math.sqrt(z*z+a*a)-G*p['haloScaleMass']*math.log1p(z/p['haloRadius'])/z
  step=r*1e-4;derivative=(potential(r-2*step)-8*potential(r-step)+8*potential(r+step)-potential(r+2*step))/(12*step);force2=r*derivative;err=abs(force2-expected**2)/max(expected**2,1e-100);maxgradient=max(maxgradient,err);assert err<2e-7;gradientchecks+=1
proof={'allPassed':True,'parameterSets':len(params),'radiusCases':len(requests),'potentialGradientChecks':gradientchecks,'maxRelativeHaloMassError':maxmass,'maxRelativeSpeedError':maxspeed,'maxRelativePotentialGradientError':maxgradient,'haloScaleMassIsNotTotalOrVirialMass':True,'NFWTotalMassDivergesWithoutTruncation':True,'modelIsNotObservedGalaxyData':True,'coreSHA256':hashlib.sha256((R/'web/physics-rotation-core.js').read_bytes()).hexdigest(),'wholeGoalComplete':False};args.output.write_text(json.dumps(proof,indent=2)+'\n');print(proof)
