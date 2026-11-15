from pathlib import Path
import json,math
from scipy.integrate import quad
D=Path(__file__).resolve().parent;O=D/'app'if '--app'in __import__('sys').argv else D;cases=json.loads((O/'browser-cases.json').read_bytes());G=6.67430e-11*1.988409870698051e30/3.0856775814913673e19/1e6;count=0;worst=0
for c in cases:
 s=c['state'];M=s['diskMass'];a=s['diskA']+s['diskB'];Ms=s['haloScaleMass'];rs=s['haloRadius'];top=c['maximum']
 def speeds(r):
  if r==0:return [0,0,0]
  x=r/rs;mh=Ms*quad(lambda u:x*x*u/(1+x*u)**2,0,1,epsabs=1e-25)[0];vd=math.sqrt(G*M*r*r/(r*r+a*a)**1.5);vh=math.sqrt(G*mh/r);return [vd,vh,math.hypot(vd,vh)]
 for curve in c['curves']:
  component=['diskSpeedKms','haloSpeedKms','totalSpeedKms'].index(curve['component']);pts=[tuple(map(float,p.split(',')))for p in curve['points'].split()];assert len(pts)==161
  for i,(x,y)in enumerate(pts):
   r=(x-70)/660*40;v=(370-y)/320*top;assert abs(r-i/4)<1e-12 and 70-1e-9<=x<=730+1e-9 and 50-1e-9<=y<=370+1e-9;expected=speeds(i/4)[component];error=abs(v-expected);assert error<1e-8;worst=max(worst,error);count+=1
 marker=c['marker'];assert abs((marker['x']-70)/660*40-s['radius'])<1e-12;assert abs((370-marker['y'])/320*top-speeds(s['radius'])[2])<1e-8
proof={'allPassed':True,'browserCases':len(cases),'renderedCurveVertices':count,'selectedMarkers':len(cases),'maximumAbsoluteSpeedErrorKms':worst,'independentHaloDensityQuadrature':True,'calibratedRenderedAxesVerified':True,'wholeGoalComplete':False};(O/'geometry-proof.json').write_text(json.dumps(proof,indent=2)+'\n');print(proof)
