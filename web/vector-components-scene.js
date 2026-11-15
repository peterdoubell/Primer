/* Source-coordinate vector constructions with uniform, explicit display scaling. */
(function(host){
'use strict';
const core=host?host.PrimerVectorComponentsCore:require('./vector-components-core.js');
const norm=v=>Math.hypot(...v),rotate=v=>[v[0],v[2],-v[1]];
function scene(raw){const model=core.model(raw),{a,b}=model.state,zero=[0,0,0],projection=model.projectionOnB?.map(r=>r.n/r.d)||null;
const scaledA=a.map(n=>n*model.state.alpha),scaledB=b.map(n=>n*model.state.beta);
const endpoints=[zero,a,b,scaledA,scaledB,model.sum,model.combination,...(projection?[projection]:[])];const radius=Math.max(1,...endpoints.map(norm)),gain=1.8/radius;
const display=v=>rotate(v).map(x=>x*gain);
const segment=(id,from,to)=>({id,from:[...from],to:[...to],displayFrom:display(from),displayTo:display(to),zero:from.every((x,i)=>x===to[i])});
const arrows=[segment('a',zero,a),segment('b',zero,b),segment('sum',zero,model.sum),segment('combination',zero,model.combination),segment('b-after-a',a,model.sum),segment('a-after-b',b,model.sum),segment('scaled-a',zero,scaledA),segment('scaled-b',zero,scaledB),segment('scaled-b-after-a',scaledA,model.combination)];
if(projection)arrows.push(segment('projection-on-b',zero,projection),segment('orthogonal-remainder',projection,a));
const crossRadius=Math.max(1,norm(model.cross)),crossGain=1.8/crossRadius;
return {model,basis:'(x,y,z) → (x,z,−y): rigid right-handed display rotation',gain,displayUnitsPerCoordinateUnit:gain,arrows,parallelogram:[zero,a,model.sum,b].map(p=>({source:[...p],display:display(p)})),crossPanel:{source:model.cross,display:rotate(model.cross).map(x=>x*crossGain),gain:crossGain,zero:model.cross.every(x=>x===0),areaSquared:model.cross2,scaleNote:'Separate panel: cross-product components represent oriented area, not the same length scale as the input vectors.'},projectionExact:model.projectionOnB,projectionRendering:'Exact rational components retained; display positions use their floating-point quotients.'};}
const api=Object.freeze({scene});if(host)host.PrimerVectorComponentsScene=api;if(typeof module!=='undefined'&&module.exports)module.exports=api;
})(typeof window==='undefined'?null:window);
