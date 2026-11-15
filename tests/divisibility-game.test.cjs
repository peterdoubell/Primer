'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
require('../web/learning-games/divisibility/game.js');
const { evaluate } = globalThis.PrimerDivisibility;
const model = JSON.parse(fs.readFileSync(path.join(__dirname, '../web/learning-games/divisibility/model.json')));
for (const d of [2,4,5,10]) for (let n=0;n<1000;n++) {
  assert.equal(evaluate({kind:'exact',number:String(n),divisor:d}).answer, n%d===0?'yes':'no');
}
for (const number of ['9007199254740993','10000000000000000000000000000000000000000000000000000000000000000000000000000000','00020']) {
  for (const divisor of [2,4,5,10]) assert.equal(evaluate({kind:'exact',number,divisor}).answer,BigInt(number)%BigInt(divisor)===0n?'yes':'no');
}
// Independent oracle enumerates every legal two-digit hidden prefix.
for (const divisor of [2,4,5,10]) for (let suffix=0;suffix<100;suffix++) for (const width of [1,2]) {
  if (width===1 && suffix>9) continue;
  const text=String(suffix).padStart(width,'0'), outcomes=new Set();
  for (let prefix=10;prefix<=99;prefix++) outcomes.add((BigInt(String(prefix)+text)%BigInt(divisor))===0n);
  const expected=outcomes.size===2?'unknown':outcomes.has(true)?'yes':'no';
  assert.equal(evaluate({kind:'hidden',suffix:text,prefix_digits:2,divisor}).answer,expected);
}
for (const number of ['','1e3','-5','1.2','12x','1'.repeat(81)]) assert.throws(()=>evaluate({kind:'exact',number,divisor:2}));
assert.throws(()=>evaluate({kind:'exact',number:'12',divisor:3}));
assert.deepEqual(model.challenges.map(c=>evaluate(c).answer), ['yes','yes','no','unknown','yes','no']);
console.log('Exact arithmetic, hidden-clue oracle, invalid input and all authored challenges passed.');
