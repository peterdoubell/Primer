from pathlib import Path
from fractions import Fraction
from decimal import Decimal,localcontext
import json,hashlib,math
r=Path('.research/qft-representability-audit-20261011')
x=json.loads((r/'independent-representability-result.json').read_text())
points=axes=0;worst=worst_log=0.;cases=[]
F=Fraction.from_float
with localcontext() as ctx:
 ctx.prec=100
 def log10_fraction(v):
  return (Decimal(v.numerator)/Decimal(v.denominator)).log10()
 for record in x['ratioCharts']:
  c=record['chart'];sx=F(c['xmax'])-F(c['xmin']);sy=F(c['ymax'])-F(c['ymin']);sx=sx if sx else Fraction(1);sy=sy if sy else Fraction(1)
  equal=c['xMap']==c['yMap'] and c['xGainLog10']==c['yGainLog10']
  shared=min(Fraction(5)/sx,Fraction(3)/sy)
  k={'x':shared if equal else Fraction(5)/sx,'y':shared if equal else Fraction(3)/sy}
  local_worst=0.
  for axis,index in [('x',0),('y',1)]:
   if c[axis+'Map']['mode']!='ratio':continue
   # Exact binary input fractions and Decimal logarithm never divide tiny floats.
   expected_log=float(log10_fraction(k[axis]));error=abs(expected_log-c[axis+'GainLog10']);assert error<2e-12,(expected_log,c[axis+'GainLog10']);worst_log=max(worst_log,error);axes+=1
   for g in c['graphs']:
    for source,actual in zip(g['source'],g['points']):
     desired=F(c['origin'][index])+(F(source[axis])-F(c[axis+'min']))*k[axis]
     error=abs(float(desired)-actual[index]);assert error<2e-14,(error,source,actual)
     local_worst=max(local_worst,error);worst=max(worst,error);points+=1
  cases.append({'state':record['case']['state'],'chart':c['index'],'equalScale':equal,'maxAbsoluteCoordinateError':local_worst})
 # Independent mediator constants from exact SI h,c,e and a 100-digit pi.
 pi=Decimal('3.1415926535897932384626433832795028841971693993751058209749445923078164062862089986280348253421170679')
 hc=Decimal('6.62607015e-34')*Decimal(299792458)/(2*pi*Decimal('1.602176634e-19'))*Decimal('1e9')
 mediator=[];max_med_log=0.
 for record in x['mediator']:
  mass=record['mass'];d=record['current']
  if mass==0:continue
  exact_mass=Decimal.from_float(mass);exact_r=Decimal.from_float(record['radiusFm']);range_fm=hc/exact_mass;inverse=exact_mass/hc
  expected_range_log=float(range_fm.log10());expected_inverse_log=float(inverse.log10())
  delta=max(abs(expected_range_log-d['log10RangeFm']),abs(expected_inverse_log-d['log10InverseRange']));assert delta<2e-12;max_med_log=max(max_med_log,delta)
  if d['rangeOverflow']:assert range_fm>Decimal.from_float(float.fromhex('0x1.fffffffffffffp+1023')),'overflow label corresponds to physically beyond Float64 range'
  if mass==math.ulp(0.0):assert inverse>0 and inverse<Decimal.from_float(math.ulp(0.0)) and d['inverseRangeUnderflow']
  if d['suppressionUnresolved']:assert exact_r*inverse>0,'positive mass retains positive suppression exponent'
  mediator.append({'mass':mass,'radiusFm':record['radiusFm'],'independentLog10RangeFm':expected_range_log,'logErrorDex':delta,'positiveFiniteMathematicalRange':True})
 out={'status':'pass','method':'Fraction exact binary accepted coordinates plus 100-digit Decimal logarithms; exact SI h,c,e and pi for independent mediator range oracle. No runtime coordinate or mediator helper used.','ratioAxes':axes,'rationalCoordinateChecks':points,'maxAbsoluteCoordinateError':worst,'maxPhysicalGainLogErrorDex':worst_log,'ratioCases':cases,'mediatorPositiveCases':len(mediator),'maxMediatorRangeLogErrorDex':max_med_log,'mediatorCases':mediator,'scope':'Exact affine-ratio calibration of actually emitted coordinates, physical logarithmic gains, and positive finite mediator ranges. Actual browser pixels/performance remain separate.'}
(r/'rational-calibration-result.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items() if k not in ['ratioCases','mediatorCases','method','scope']},indent=2))
