'use strict';
const assert=require('node:assert/strict');
const {traverseCells}=require('./anatomy_sources/viewers/renal-volume/traversal.js');
const axis=traverseCells([-3,.2,.2],[1,0,0],[4,3,2],[4,3,2]);
assert.deepEqual(axis.map(r=>r.index),[[0,1,1],[1,1,1],[2,1,1],[3,1,1]]);
assert.equal(axis.reduce((s,r)=>s+r.exit-r.entry,0),4);
assert.deepEqual(traverseCells([3,.2,.2],[-1,0,0],[4,3,2],[4,3,2]).map(r=>r.index),axis.map(r=>r.index).reverse());
assert.deepEqual(traverseCells([-3,-3,-3],[1,1,1],[3,3,3],[3,3,3]).map(r=>r.index),[[0,0,0],[1,1,1],[2,2,2]]);
assert.deepEqual(traverseCells([-3,3,0],[1,0,0],[3,3,3],[3,3,3]),[]);
// A ray can graze a high-valued cell for much less than one native cell width.
const graze=traverseCells([-2,-1.0001,0],[1,1,0],[3,3,1],[3,3,1]);
assert(graze.some(r=>r.exit-r.entry>0&&r.exit-r.entry<.001));
const high=graze.find(r=>r.index[0]===1&&r.index[1]===1);assert(high&&high.exit-high.entry<.001);
// The previous fixed .625 step misses this nonzero-length high-valued cell.
const sampled=[];for(let t=graze[0].entry;t<=graze.at(-1).exit;t+=.625){const x=-2+t,y=-1.0001+t;sampled.push([Math.floor(x+1.5),Math.floor(y+1.5)]);}
assert(!sampled.some(i=>i[0]===1&&i[1]===1));
for(const row of graze)assert(row.exit>row.entry);
const anisotropic=traverseCells([0,0,-2],[0,0,1],[2,2,4],[2,2,.5]);
assert.equal(anisotropic.length,4);assert.equal(anisotropic.reduce((s,r)=>s+r.exit-r.entry,0),.5);
console.log('Verified full-cell traversal, reversed/parallel rays, exact corner ties, grazing cells and anisotropy');
