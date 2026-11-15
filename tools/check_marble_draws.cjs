'use strict';
const assert = require('node:assert/strict');
const {model} = require('../web/math/marble-draws/core.js');
let cases = 0;
for (let n=1;n<=10;n++) for (let r=0;r<=n;r++) {
  const b=n-r;
  for (const replacement of [false,true]) for (const condition of ['none','red','blue']) {
    const remaining=replacement?n:n-1;
    const first=condition==='none'?n:condition==='red'?r:b;
    const counts={
      'both-red':condition==='blue'?0:r*(replacement?r:Math.max(0,r-1)),
      'second-red':condition==='none'?r*remaining:condition==='red'?r*(replacement?r:Math.max(0,r-1)):b*r,
      'different':(condition==='none'?2:1)*r*b,
      'at-least-red':condition==='red'?r*remaining:condition==='blue'?b*r:n*remaining-b*(replacement?b:Math.max(0,b-1)),
    };
    for (const [event,numerator] of Object.entries(counts)) {
      const state=model(n,r,replacement,condition,event);
      assert.equal(state.denominator,first*remaining);
      assert.equal(state.numerator,numerator);
      assert.equal(state.outcomes.length,n*n);
      assert.equal(state.allowed,n*remaining);
      if (!state.denominator) assert.equal(state.probability,null);
      else assert.equal(state.probability[0]*state.denominator,state.probability[1]*numerator);
      cases++;
    }
  }
}
assert.deepEqual(model(5,3,false,'none','both-red').probability,[3,10]);
assert.deepEqual(model(5,3,true,'none','both-red').probability,[9,25]);
assert.deepEqual(model(10,1,true,'none','at-least-red').probability,[19,100]);
for (const bad of [[0,0,false,'none','both-red'],[5,6,true,'none','both-red'],[2,1,false,'invalid','both-red']]) {
  assert.throws(()=>model(...bad),RangeError);
}
console.log(cases+' exact event and conditioning cases passed.');
