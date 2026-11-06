'use strict';
const assert=require('node:assert/strict');
const {cases,ledger,checkMissingNucleus}=require('../web/physics/nuclear-balance/core.js');
const products={alpha:[234,90],beta:[14,7],fusion:[4,2],fission:[141,56],gamma:[40,20]};
assert.deepEqual(cases.map(row=>row.id).sort(),Object.keys(products).sort());
for(const [id,[a,q]]of Object.entries(products)){
  const state=ledger(id);
  assert.deepEqual(state.before,state.after);
  assert.ok(checkMissingNucleus(id,a,q));
  assert.equal(checkMissingNucleus(id,a+1,q),false);
  assert.equal(checkMissingNucleus(id,a,q+1),false);
  assert.equal(checkMissingNucleus(id,a+.5,q),false);
}
const beta=ledger('beta').example.output;
assert.ok(beta.some(row=>row.label==='Electron'&&row.nucleons===0&&row.charge===-1));
assert.ok(beta.some(row=>row.label==='Electron antineutrino'&&row.nucleons===0&&row.charge===0));
assert.deepEqual(ledger('fission').before,{nucleons:236,charge:92});
assert.deepEqual(ledger('fusion').before,{nucleons:5,charge:2});
assert.throws(()=>ledger('unknown'),RangeError);
console.log('Five source reaction ledgers and invalid proposed products passed.');
