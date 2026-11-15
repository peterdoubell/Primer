'use strict';
// Fixed repository source; requests arrive on stdin and results go to stdout.
// No request, argument or environment value is used as a filesystem path.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),assert=require('node:assert/strict');
const sourcePath=path.resolve(__dirname,'../web/measurement-lab.js');
const source=fs.readFileSync(sourcePath,'utf8');
const hash=value=>crypto.createHash('sha256').update(value).digest('hex');
const sourceSHA256=hash(source);
assert.equal(sourceSHA256,'8a1d68588bb9689146a5673c1d2f7f7b4fad10213f53c10f47c4d1c35bd537af');
const lab=require(sourcePath);
const methods=new Map(['propagate','interval','repeatBudget','weightedLineFit','fitExample'].map(name=>[name,lab[name]]));
const requests=JSON.parse(fs.readFileSync(0,'utf8'));
assert(Array.isArray(requests));
const results=requests.map(request=>{
  assert(typeof request.id==='string' && Array.isArray(request.args) && methods.has(request.method));
  try{return {id:request.id,result:methods.get(request.method)(...request.args)};}
  catch(error){return {id:request.id,error:{name:error.name,message:error.message}};}
});
assert.equal(hash(fs.readFileSync(sourcePath,'utf8')),sourceSHA256);
console.log(JSON.stringify({sourceSHA256,pureAPIPrefixSHA256:hash(source.split('  const defaults=')[0]),results}));
