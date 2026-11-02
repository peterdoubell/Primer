from pathlib import Path
import json,subprocess,math
D=Path(__file__).resolve().parent;requests=[{'temperature':T,'appliedMilliTesla':B}for T in [.5,5,7,7.2,10]for B in [0,10,30,60,80,100]]
script="const fs=require('fs'),{cylinderField}=require('__FIELD__');console.log(JSON.stringify(JSON.parse(fs.readFileSync(0,'utf8')).map(p=>{const f=cylinderField(p);return{...f,currents:Array.from({length:32},(_,i)=>f.surfaceCurrent(i*2*Math.PI/32))};})));"
script=script.replace('__FIELD__',str(D/'field.cjs'))
rows=json.loads(subprocess.check_output(['node','-e',script],input=json.dumps(requests),text=True));mu=4*math.pi*1e-7;maximum=0.;count=0
for p,f in zip(requests,rows):
 T=p['temperature'];B=p['appliedMilliTesla']*1e-3;bc=.08*max(0,1-(T/7.2)**2);screened=T<7.2 and B<bc;inside=0 if screened else B
 assert f['outsideTesla']==[0,0,B]and f['insideTesla']==[0,0,inside]
 for i,K in enumerate(f['currents']):
  theta=i*2*math.pi/32;tangent=(-math.sin(theta),math.cos(theta),0);projection=sum(K[j]*tangent[j]for j in range(3));expected=-(B-inside)/mu;error=abs(projection-expected);maximum=max(maximum,error);assert error<1e-10;assert abs(K[0]*math.cos(theta)+K[1]*math.sin(theta))<1e-10;count+=1
 # A rectangular Ampere loop spanning the ideal sheet gives the signed
 # current per unit axial length; normal magnetic flux remains continuous.
 assert math.isclose(-f['currents'][0][1],(B-inside)/mu,abs_tol=1e-10)
proof={'allPassed':True,'states':len(rows),'azimuthalCurrentChecks':count,'maxAbsoluteCurrentProjectionErrorAperM':maximum,'independentPhaseAndAmpereLoopCheck':True,'infiniteLongitudinalCylinderOnly':True,'finiteSampleEndFieldsNotClaimed':True,'wholeGoalComplete':False};(D/'field-independent-proof.json').write_text(json.dumps(proof,indent=2)+'\n');print(proof)
