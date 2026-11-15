'use strict';
const assert=require('assert/strict');
module.exports=async function(root){
 const data=await root.evaluate(e=>{const id=e.dataset.scenario,api=window.PrimerSpatial,controls=Object.fromEntries([...e.querySelectorAll('[data-parameter]')].map(n=>[n.dataset.parameter,n.value]));return{initial:api.build(id,{}),current:api.build(id,controls),readout:e.querySelector('.spatial-readout').textContent,camera:e.dataset.view.split(',').map(Number),polygons:[...e.querySelectorAll('.spatial-svg polygon')].map(n=>n.getAttribute('points').trim().split(/\s+/).map(p=>p.split(',').map(Number))),lines:[...e.querySelectorAll('.spatial-svg polyline')].map(n=>n.getAttribute('points').trim().split(/\s+/).map(p=>p.split(',').map(Number))),labels:[...e.querySelectorAll('.spatial-svg text')].map(n=>{const b=n.getBBox();return{text:n.textContent,x:b.x,y:b.y,w:b.width,h:b.height};})};});
 assert(data.current.baseTen);assert.equal(data.readout,data.current.readout);let checks=0;
 const initial=data.initial.primitives.filter(p=>p.kind!=='label').flatMap(p=>p.points),center=[0,1,2].map(i=>(Math.min(...initial.map(p=>p[i]))+Math.max(...initial.map(p=>p[i])))/2),radius=Math.max(...initial.map(p=>Math.hypot(...p.map((v,i)=>v-center[i]))));
 const[yaw,pitch,zoom]=data.camera,[cy,sy,cp,sp]=[Math.cos(yaw*Math.PI/180),Math.sin(yaw*Math.PI/180),Math.cos(pitch*Math.PI/180),Math.sin(pitch*Math.PI/180)];
 const rotate=p=>{const[x,y,z]=p.map((v,i)=>v-center[i]),u=cy*x+sy*z,v=-sy*x+cy*z;return[u,cp*y-sp*v,sp*y+cp*v];};
 const current=data.current.primitives.filter(p=>p.kind!=='label'),rotated=current.flatMap(p=>p.points.map(rotate)),requested=175/radius*zoom,fit=Math.min(282/Math.max(.1,...rotated.map(p=>Math.abs(p[0]))),192/Math.max(.1,...rotated.map(p=>Math.abs(p[1])))),scale=zoom<=1?Math.min(requested,fit):requested,project=p=>{const r=rotate(p);return[300+scale*r[0],210-scale*r[1]];};
 const canonical=points=>JSON.stringify(points.map(p=>p.map(v=>{assert(Number.isFinite(v));checks++;return Math.round(v*1e6)/1e6;})).sort((a,b)=>a[0]-b[0]||a[1]-b[1]));
 function same(actual,kind){const expected=current.filter(p=>p.kind===kind).map(p=>p.points.map(project));assert.equal(actual.length,expected.length);assert.deepEqual(actual.map(canonical).sort(),expected.map(canonical).sort());if(zoom<=1)for(const face of actual)for(const[x,y]of face)assert(x>=17.99999&&x<=582.00001&&y>=17.99999&&y<=402.00001);}
 same(data.polygons,'polygon');same(data.lines,'line');assert.equal(data.lines.length,12);
 for(const label of data.labels)assert(label.x>=0&&label.y>=0&&label.x+label.w<=600.00001&&label.y+label.h<=420.00001,label.text+' leaves the 3D canvas');
 for(let i=0;i<data.labels.length;i++)for(let j=i+1;j<data.labels.length;j++){const a=data.labels[i],b=data.labels[j];assert(!(a.x<b.x+b.w&&a.x+a.w>b.x&&a.y<b.y+b.h&&a.y+a.h>b.y),'3D callout labels overlap');}
 return{checks,polygons:data.polygons.length,referenceEdges:12,milliunits:data.current.baseTen.milliunits,camera:data.camera,allProjectedVerticesMatch:true,labelsWithinCanvasAndSeparate:true};
};
