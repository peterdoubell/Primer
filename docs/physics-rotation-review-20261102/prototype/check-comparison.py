from pathlib import Path
import json,math
from scipy.integrate import quad
D=Path(__file__).resolve().parent;O=D/'app'if '--app'in __import__('sys').argv else D;cases=json.loads((O/'browser-cases.json').read_bytes());G=6.67430e-11*1.988409870698051e30/3.0856775814913673e19/1e6;seed=0x57a83d19

def uniform():
 global seed
 seed=(seed^(seed<<13))&0xffffffff;seed^=seed>>17;seed=(seed^(seed<<5))&0xffffffff
 return(seed+.5)/4294967296

def speed(r,p):
 x=r/p['haloRadius'];mass=p['haloScaleMass']*quad(lambda t:x*x*t/(1+x*t)**2,0,1)[0]
 return math.sqrt(G*(p['diskMass']*r*r/(r*r+(p['diskA']+p['diskB'])**2)**1.5+mass/r))
truth={'diskMass':6e10,'diskA':3,'diskB':.3,'haloScaleMass':8e11,'haloRadius':20};expected=[]
for r in [2,4,6,8,10,12,15,18,22,26,32,40]:
 z=math.sqrt(-2*math.log(uniform()))*math.cos(2*math.pi*uniform());expected.append((r,speed(r,truth)+8*z))
maxerr=0
for c in cases:
 assert len(c['observations'])==len(c['errorBars'])==len(expected)
 score=0
 for (r,y),obs,bar,data in zip(expected,c['observations'],c['errorBars'],c['comparison']):
  assert r==obs['r']==bar['r']==data['radiusKpc']
  assert abs(data['speedKms']-y)<1e-10 and data['sigmaKms']==8
  actual=(370-obs['y'])/320*c['maximum'];err=abs(actual-y);maxerr=max(err,maxerr);assert err<1e-10
  assert abs((obs['x']-70)/660*40-r)<1e-12 and abs((bar['x']-70)/660*40-r)<1e-12
  assert abs((370-bar['y1'])/320*c['maximum']-(y-8))<1e-10
  assert abs((370-bar['y2'])/320*c['maximum']-(y+8))<1e-10
  score+=((y-speed(r,c['state']))/8)**2
 assert abs(c['weightedMismatch']-score)<1e-8
proof={'allPassed':True,'browserCases':len(cases),'syntheticObservationsVerified':96,'renderedUncertaintyEndpointsVerified':192,'independentWeightedMismatchChecks':8,'maxRenderedObservationErrorKms':maxerr,'sampleUnchangedAcrossControlsAndViewports':True,'observedGalaxyDataClaimed':False,'massConfidenceIntervalsClaimed':False,'wholeGoalComplete':False};(O/'comparison-proof.json').write_text(json.dumps(proof,indent=2)+'\n');print(proof)
