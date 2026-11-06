const assert=require('assert/strict'),{evaluate}=require('../web/language/quantifier-scope/core.js');
let each=0,one=0,only=0,neither=0;
for(let mask=0;mask<512;mask++){
 const pairs=[];
 for(let bit=0;bit<9;bit++)if(Math.floor(mask/2**bit)%2)pairs.push([Math.floor(bit/3),bit%3]);
 const covered=new Set(pairs.map(([child])=>child));
 const shared=[0,1,2].filter(tree=>new Set(pairs.filter(([,t])=>tree===t).map(([c])=>c)).size===3);
 const result=evaluate(mask);
 assert.equal(result.each,covered.size===3);assert.deepEqual(result.shared,shared);assert.equal(result.one,shared.length>0);
 for(let c=0;c<3;c++)assert.deepEqual(result.witnesses[c],pairs.filter(([child])=>child===c).map(([,tree])=>tree));
 assert.ok(!result.one||result.each);
 each+=result.each;one+=result.one;only+=result.each&&!result.one;neither+=!result.each&&!result.one;
}
assert.deepEqual({each,one,only,neither},{each:343,one:169,only:174,neither:169});
for(const bad of [-1,512,1.5,NaN,'3'])assert.throws(()=>evaluate(bad),RangeError);
console.log('All 512 relations match independent set-based quantifier evaluation; witnesses and implication verified.');
