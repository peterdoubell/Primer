from pathlib import Path
from decimal import Decimal,localcontext
import itertools,json,math,subprocess
D=Path(__file__).resolve().parent
with localcontext() as ctx:
 ctx.prec=60
 mn,mp,me=map(Decimal,['939.56542194','938.27208943','.51099895069'])
 delta=mn-mp
 stationary=(delta-me)**2/(2*delta)
 endpoint=((mn-me)**2-mp**2)/(2*mn)
 fraction=float(stationary/endpoint)
 expected_p=float((delta*delta-me*me)/(2*delta))
requests=[dict(fraction=f,cosine=c,azimuth=a)for f,c,a in itertools.product([0,1e-12,.1,fraction-1e-10,fraction,fraction+1e-10,.75,1-1e-12,1],[-1,-1+1e-12,-.7,0,.7,1-1e-12,1],[0,.3,math.pi,2*math.pi])]
script="const fs=require('fs'),c=require('./.research/physics-particle-20261102/core.cjs');console.log(JSON.stringify(JSON.parse(fs.readFileSync(0,'utf8')).map(p=>c.beta(p))));"
rows=json.loads(subprocess.check_output(['node','-e',script],input=json.dumps(requests),text=True))
max_energy=max_momentum=0
for request,row in zip(requests,rows):
 vectors=row['momentaMeVPerC']; energies=[row['electronEnergyMeV'],row['neutrinoEnergyMeV'],row['protonEnergyMeV']]
 assert all(math.isfinite(x)for x in energies+sum(vectors.values(),[]))
 energy=abs(math.fsum(energies)-float(mn)); momentum=max(abs(math.fsum(vectors[k][i]for k in vectors))for i in range(3))
 max_energy=max(max_energy,energy); max_momentum=max(max_momentum,momentum)
 assert energy<1e-10 and momentum<1e-12
 if request['cosine']==-1 and request['fraction']==fraction:
  assert abs(vectors['electron'][0]-expected_p)<1e-12
  assert abs(vectors['neutrino'][0]+expected_p)<1e-12
  assert math.hypot(*vectors['proton'])<1e-12
  assert not row['protonDirectionResolved']
  assert row['protonDirectionResolutionMeVPerC']==64*2**-52*float(mn+mp)
residual=max(math.hypot(*r['momentaMeVPerC']['proton'])for q,r in zip(requests,rows)if q['cosine']==-1 and q['fraction']==fraction)
proof={'allKinematicsChecksPassed':True,'cases':len(rows),'precisionDigits':60,'stationaryProtonFraction':fraction,'stationaryElectronKineticMeV':float(stationary),'stationaryProtonNumericalResidualMeVPerC':residual,'maxEnergyResidualMeV':max_energy,'maxMomentumResidualMeVPerC':max_momentum,'stationaryProtonDirectionSuppressed':True,'applicationIntegrated':False,'wholeGoalComplete':False}
(D/'angular-edge-proof.json').write_text(json.dumps(proof,indent=2)+'\n')
print(json.dumps(proof))
