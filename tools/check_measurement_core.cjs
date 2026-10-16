'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'..'),lab=require(path.join(root,'web/measurement-lab.js'));
const near=(actual,expected,rel=2e-11,abs=1e-12)=>assert.ok(Math.abs(actual-expected)<=abs+rel*Math.abs(expected),`${actual} != ${expected}`);
const f=(op,a,b)=>op==='sum'?a+b:op==='difference'?a-b:op==='ratio'?a/b:4*Math.PI*Math.PI*a/b**2;
let propagation=0,intervals=0,repeatCases=0,fitCases=0,rejections=0;
for(const op of Object.keys(lab.operations))for(const a of [0,1,10])for(const b of [.5,2,20])for(const ua of [0,.01,.3])for(const ub of [0,.02,.4])for(const rho of [-1,-.4,0,.7,1]){
 const m=lab.propagate({operation:op,a,b,ua,ub,rho});assert.equal(m.a,a);assert.equal(m.b,b);near(m.value,f(op,a,b));
 const gradient=op==='sum'?[1,1]:op==='difference'?[1,-1]:op==='ratio'?[1/b,-a/b**2]:[4*Math.PI*Math.PI/b**2,-8*Math.PI*Math.PI*a/b**3];
 gradient.forEach((g,i)=>near(m.gradient[i],g));
 const h=1e-5;near((f(op,a+h,b)-f(op,a-h,b))/(2*h),gradient[0],1e-8,1e-8);near((f(op,a,b+h)-f(op,a,b-h))/(2*h),gradient[1],1e-8,1e-8);
 // Four equally weighted independent Rademacher combinations have exactly the
 // prescribed covariance. Propagate each linearized perturbation independently.
 const perturbations=[];for(const x of [-1,1])for(const z of [-1,1]){const A=ua*x,B=ub*(rho*x+Math.sqrt(1-rho*rho)*z);perturbations.push(gradient[0]*A+gradient[1]*B);}
 near(m.variance,perturbations.reduce((s,d)=>s+d*d,0)/4);near(m.standard**2,m.variance);assert.ok(m.variance>=0&&Number.isFinite(m.variance));
 if(m.value===0)assert.equal(m.relativeStandard,null);else near(m.relativeStandard,m.standard/Math.abs(m.value));propagation++;
}
near(100*lab.propagate(lab.defaults.propagation).relativeStandard,Math.sqrt(5));
assert.equal(lab.propagate({operation:'difference',a:1.52,b:1.28,ua:.2,ub:.2,rho:1}).standard,0);
for(const op of Object.keys(lab.operations))for(const a of [1,3,10])for(const b of [.2,2,5])for(const ra of [0,.01,.4])for(const rb of [0,.02,.7]){
 const da=a*ra,db=b*rb,m=lab.interval({operation:op,a,b,da,db});
 const values=[];for(let i=0;i<=10;i++)for(let j=0;j<=10;j++)values.push(f(op,a-da+2*da*i/10,b-db+2*db*j/10));
 near(m.low,Math.min(...values));near(m.high,Math.max(...values));assert.ok(values.every(v=>v>=m.low-1e-10&&v<=m.high+1e-10));
 assert.equal(m.corners.length,4);intervals++;
}
const bounds=lab.interval(lab.defaults.bounds);near(bounds.low,10*.99/(2*1.02));near(bounds.high,10*1.01/(2*.98));assert.ok(bounds.high>bounds.linearizedInterval[1]);
for(const n of [1,2,25,400,1000000])for(const readingStd of [0,.02,.2])for(const calibrationStd of [0,.05,.5])for(const resolution of [0,.1,1])for(const resolutionMode of ['included-in-scatter','shared-uniform','independent-uniform']){
 const s={n,readingStd,calibrationStd,resolution,resolutionMode,target:5,offset:.2,correction:.15},m=lab.repeatBudget(s);
 let oracle=0;const count=Math.min(n,400); // Explicit covariance summation for ordinary fixture counts.
 if(n<=400){for(let i=0;i<count;i++)for(let j=0;j<count;j++){oracle+=calibrationStd**2+(i===j?readingStd**2:0)+(resolutionMode==='shared-uniform'||resolutionMode==='independent-uniform'&&i===j?resolution**2/12:0);}oracle/=n*n;near(m.variance,oracle,3e-10);}
 near(m.residualOffset,.05);near(m.expectedCorrected,5.05);assert.ok(m.standard>=m.floor);repeatCases++;
}
const qs=lab.repeatBudget({...lab.defaults.repeats,n:400,readingStd:0,calibrationStd:0,resolution:.1,resolutionMode:'shared-uniform'}),qi=lab.repeatBudget({...lab.defaults.repeats,n:400,readingStd:0,calibrationStd:0,resolution:.1,resolutionMode:'independent-uniform'});near(qs.standard/qi.standard,20);
function qrFit(rows){
 const dot=(a,b)=>a.reduce((s,v,i)=>s+v*b[i],0),ones=rows.map(p=>1/p.sigma),x=rows.map(p=>p.x/p.sigma),y=rows.map(p=>p.y/p.sigma);
 const r00=Math.sqrt(dot(ones,ones)),q0=ones.map(v=>v/r00),r01=dot(q0,x),v1=x.map((v,i)=>v-r01*q0[i]),r11=Math.sqrt(dot(v1,v1)),q1=v1.map(v=>v/r11);
 const slope=dot(q1,y)/r11,intercept=(dot(q0,y)-r01*slope)/r00,inv=[[1/r00,-r01/(r00*r11)],[0,1/r11]];
 const covariance=inv.map(a=>inv.map(b=>dot(a,b)));
 const chi=rows.reduce((s,p)=>s+((p.y-intercept-slope*p.x)/p.sigma)**2,0);
 return {slope,intercept,covariance,chi};
}
for(const scatter of [0,.3,2])for(const offset of [-3,0,3])for(const acceleration of [-.2,0,.2])for(const outlier of [-5,0,5])for(const sigma of [.01,.3,3])for(const heterogeneous of [false,true]){
 const s={scatter,offset,acceleration,outlier,sigma,heterogeneous},m=lab.fitExample(s),q=qrFit(m.rows);
 near(m.intercept,q.intercept,1e-9,1e-10);near(m.slope,q.slope,1e-9,1e-10);m.parameterCovariance.forEach((r,i)=>r.forEach((v,j)=>near(v,q.covariance[i][j],1e-9)));near(m.chiSquare,q.chi,1e-9);assert.equal(m.degreesOfFreedom,10);
 near(m.rows.reduce((s,p)=>s+p.residual/p.sigma**2,0),0,1e-9,1e-8);near(m.rows.reduce((s,p)=>s+p.x*p.residual/p.sigma**2,0),0,1e-9,1e-7);
 const ref=lab.fitExample({...s,mode:'reference'});assert.equal(ref.degreesOfFreedom,12);assert.equal(ref.parametersEstimated,0);near(ref.chiSquare,ref.rows.reduce((s,p)=>s+((p.y-(1+.5*p.x))/p.sigma)**2,0));assert.deepEqual(ref.parameterCovariance,[[0,0],[0,0]]);fitCases++;
}
// Exactly representable small spacings at a large x origin expose cancellation
// that ordinary fixed classroom fixtures cannot. The rational result is known.
const translatedRows=[{x:999999,y:1,sigma:1},{x:999999+2**-33,y:2,sigma:1},{x:999999+2**-32,y:4,sigma:2}];
const untranslatedRows=translatedRows.map(r=>({...r,x:r.x-999999}));
const atOrigin=lab.weightedLineFit(untranslatedRows),translated=lab.weightedLineFit(translatedRows);
near(translated.chiSquare,1/9);near(translated.slope,atOrigin.slope);
for(let i=0;i<3;i++){near(translated.rows[i].fitted,[8/9,20/9,32/9][i]);near(translated.rows[i].residual,atOrigin.rows[i].residual);near(translated.rows[i].leverage,atOrigin.rows[i].leverage);assert.ok(translated.rows[i].leverage<=1);}
for(const spacing of [1e-155,1e-160]){assert.throws(()=>lab.weightedLineFit([{x:0,y:1,sigma:1},{x:spacing,y:2,sigma:1},{x:2*spacing,y:3,sigma:1}]),/rescale the x coordinates/);rejections++;}
const shiftedY=lab.weightedLineFit([{x:0,y:999999,sigma:1},{x:1,y:999999+2**-33,sigma:1},{x:2,y:999999+2**-32,sigma:2}]);
near(shiftedY.slope,2**-33);assert.ok(shiftedY.rows.every(r=>Math.abs(r.residual)<1e-25));
const base=lab.fitExample(),shift=lab.fitExample({offset:2}),wide=lab.fitExample({sigma:.6});near(shift.intercept-base.intercept,2);near(shift.chiSquare,base.chiSquare);near(wide.chiSquare,base.chiSquare/4);near(wide.slopeStandard,base.slopeStandard*2);near(wide.slope,base.slope);
assert.ok(lab.fitExample({scatter:.3,sigma:2}).reducedChiSquare<.02);
for(const bad of [NaN,Infinity,-Infinity,null,'1',undefined]){
 for(const method of [()=>lab.propagate({...lab.defaults.propagation,a:bad}),()=>lab.interval({...lab.defaults.bounds,da:bad}),()=>lab.repeatBudget({...lab.defaults.repeats,n:bad}),()=>lab.weightedLineFit([{x:0,y:1,sigma:.1},{x:1,y:2,sigma:.1},{x:2,y:3,sigma:bad}])]){assert.throws(method);rejections++;}
}
for(const method of [()=>lab.propagate({...lab.defaults.propagation,rho:1.01}),()=>lab.propagate({...lab.defaults.propagation,ua:-.1}),()=>lab.propagate({...lab.defaults.propagation,ua:1e-100}),()=>lab.propagate({...lab.defaults.propagation,b:0}),()=>lab.interval({...lab.defaults.bounds,db:2}),()=>lab.interval({...lab.defaults.bounds,da:11}),()=>lab.repeatBudget({...lab.defaults.repeats,n:1.5}),()=>lab.repeatBudget({...lab.defaults.repeats,resolutionMode:'guaranteed'}),()=>lab.weightedLineFit([{x:1,y:1,sigma:1},{x:1,y:2,sigma:1},{x:1,y:3,sigma:1}])]){assert.throws(method);rejections++;}
const readings=lab.summarizeReadings([4.8,5,5.1,4.9,5.2]);near(readings.mean,5);near(readings.sampleVariance,.025);near(readings.standardError,Math.sqrt(.005));
const one=lab.summarizeReadings([5]);assert.equal(one.sampleVariance,null);assert.equal(one.standardError,null);
const tiny=lab.summarizeReadings([999999,999999+2**-33,999999+2**-32]);near(tiny.sampleVariance,2**-66,1e-10,1e-30);
const proof={sourceSHA256:crypto.createHash('sha256').update(fs.readFileSync(path.join(root,'web/measurement-lab.js'))).digest('hex'),propagationCases:propagation,intervalCases:intervals,repeatCases,fitCases,invalidCasesRejected:rejections,methods:['analytic derivatives and central finite differences','independent four-point covariance oracle','dense rectangle sampling with all endpoints','explicit repeat covariance sums','weighted modified Gram-Schmidt QR fit and covariance'],allPassed:true};
if(process.env.MEASUREMENT_WRITE_PROOF==='1')fs.writeFileSync(path.join(root,'docs/measurement-fidelity-review-20261016/core-proof.json'),JSON.stringify(proof,null,2)+'\n');console.log(JSON.stringify(proof));
