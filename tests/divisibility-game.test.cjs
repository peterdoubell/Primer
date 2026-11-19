'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
require('../web/learning-games/divisibility/game.js');
const { evaluate } = globalThis.PrimerDivisibility;
const root = path.join(__dirname, '..');
const model = JSON.parse(fs.readFileSync(path.join(root, 'web/learning-games/divisibility/model.json')));
// Exact arithmetic against an independent oracle, for every divisor the bench offers.
for (const d of model.game_model.allowed_divisors) for (let n = 0; n < 2000; n++) {
  assert.equal(evaluate({kind:'exact',number:String(n),divisor:d}).answer, n%d===0?'yes':'no');
}
for (const number of ['9007199254740993','10000000000000000000000000000000000000000000000000000000000000000000000000000000','00020']) {
  for (const divisor of model.game_model.allowed_divisors) {
    assert.equal(evaluate({kind:'exact',number,divisor}).answer, BigInt(number)%BigInt(divisor)===0n?'yes':'no');
  }
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
// The guided challenges moved to the shared, server-marked learning sequences:
// the bench model now points at them instead of carrying its own answer key.
assert.equal(model.schema_version, 2);
assert.equal(model.challenges, undefined, 'The bench ships no answer key');
const sequences = fs.readFileSync(path.join(root, model.sequences.source), 'utf8');
for (const title of ['Last-Digit Detective', 'Longer Endings']) {
  assert.ok(sequences.includes('~ ' + title + '\n'), title + ' is authored in ' + model.sequences.source);
}
assert.deepEqual(model.sequences.guided, ['last-digit-detective', 'longer-endings']);
console.log('Exact arithmetic for every bench divisor, hidden-clue oracle, invalid input and the sequence pointer passed.');
