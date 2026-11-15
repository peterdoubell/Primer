'use strict';
const assert=require('node:assert/strict');
const {meanDistribution}=require('../web/math/sampling-mean/core.js');
let cases=0,bins=0;
for(let n=1;n<=60;n++)for(let a=0;a<=10;a++){
  const result=meanDistribution(n,a),N=BigInt(n),A=BigInt(a);
  const total=result.outcomes.reduce((sum,x)=>sum+x.numerator,0n);
  const first=result.outcomes.reduce((sum,x)=>sum+BigInt(x.successes)*x.numerator,0n);
  const second=result.outcomes.reduce((sum,x)=>sum+BigInt(x.successes)**2n*x.numerator,0n);
  assert.equal(total,result.denominator);
  assert.equal(10n*first,N*A*result.denominator);
  assert.equal(100n*second,(N*A*(10n-A)+N*N*A*A)*result.denominator);
  assert.ok(result.withinPointTwo.numerator>=0n&&result.withinPointTwo.numerator<=result.denominator);
  if(n<=10){
    const weights=Array(n+1).fill(0n);
    for(let mask=0;mask<2**n;mask++){
      let successes=0,weight=1n;
      for(let i=0;i<n;i++){
        const success=Boolean(mask&(1<<i));
        if(success)successes++;
        weight*=BigInt(success?a:10-a);
      }
      weights[successes]+=weight;
    }
    assert.deepEqual(result.outcomes.map(x=>x.numerator),weights);
    bins+=weights.length;
  }
  cases++;
}
for(const n of [0,61,1.5,NaN,Infinity])assert.throws(()=>meanDistribution(n,5),RangeError);
for(const p of [-1,11,.5,NaN])assert.throws(()=>meanDistribution(10,p),RangeError);
console.log(cases+' exact distribution identities and '+bins+' independently enumerated outcome weights passed.');
