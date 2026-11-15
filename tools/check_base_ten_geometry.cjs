'use strict';
const assert=require('assert/strict');
module.exports=async function(root){
 const v=await root.evaluate(e=>({model:e.baseTen.getModel(),plots:[...e.querySelectorAll('[data-base-ten-plot]')].map(svg=>({type:svg.dataset.baseTenPlot,extent:+svg.dataset.extent,width:svg.viewBox.baseVal.width,height:svg.viewBox.baseVal.height,segments:[...svg.querySelectorAll('[data-base-ten-segment]')].map(n=>({id:n.dataset.baseTenSegment,units:+n.dataset.units,x:+n.getAttribute('x'),y:+n.getAttribute('y'),width:+n.getAttribute('width')})),zeros:[...svg.querySelectorAll('[data-base-ten-zero]')].map(n=>+n.dataset.baseTenZero),counters:[...svg.querySelectorAll('[data-base-ten-counter]')].map(n=>({id:n.dataset.baseTenCounter,x:+n.getAttribute('x'),y:+n.getAttribute('y'),width:+n.getAttribute('width'),height:+n.getAttribute('height')})),groups:[...svg.querySelectorAll('[data-base-ten-group]')].map(n=>+n.dataset.baseTenGroup),members:[...svg.querySelectorAll('[data-base-ten-member]')].map(n=>n.dataset.baseTenMember),remainders:[...svg.querySelectorAll('[data-base-ten-remainder]')].map(n=>+n.dataset.baseTenRemainder),labels:[...svg.querySelectorAll('text')].map(n=>{const b=n.getBBox();return{text:n.textContent,x:b.x,y:b.y,w:b.width,h:b.height};})})),bad:[...e.querySelectorAll('svg *')].flatMap(n=>[...n.attributes].filter(a=>/NaN|Infinity/.test(a.value)).map(a=>a.value))}));
 assert.deepEqual(v.bad,[]);const m=v.model,s=m.state;let checks=0;const near=(a,b)=>{assert(Number.isFinite(a)&&Number.isFinite(b));assert(Math.abs(a-b)<1e-8*Math.max(1,Math.abs(b)),a+' != '+b);checks++;};
 const a=+s.a,b=+s.b,total=+s.total,d=+s.divisor,digits=n=>[0,1,2,3].map(p=>Math.floor(n/10**p)%10*10**p);
 if(['share','group'].includes(s.mode)&&d===0){assert.equal(m.status,'undefined');assert.equal(v.plots.length,0);return{checks,undefinedHasNoStaleDiagrams:true};}
 assert.equal(v.plots.length,1);const plot=v.plots[0];
 if(['place','exchange','add','takeAway','difference'].includes(s.mode)){
  let rows;
  if(s.mode==='place')rows=[digits(+s.value)];
  else if(s.mode==='add')rows=[digits(a).map((x,i)=>x+digits(b)[i]),digits(a+b)];
  else if(['takeAway','difference'].includes(s.mode))rows=[[a],[b],[Math.abs(a-b)]];
  else{const before={hundreds:+s.hundreds,tens:+s.tens,ones:+s.ones},after={...before},from=s.from,lower=from==='hundreds'?'tens':'ones',possible=s.direction==='unbundle'?before[from]>=1:before[lower]>=10;if(possible){after[from]+=s.direction==='unbundle'?-1:1;after[lower]+=s.direction==='unbundle'?10:-10;}rows=[before,after].map(r=>[r.ones,10*r.tens,100*r.hundreds]);}
  const extent=Math.max(1,...rows.map(r=>r.reduce((a,b)=>a+b,0)));assert.equal(plot.extent,extent);let count=0;
  rows.forEach((row,r)=>{let sum=0;row.forEach((n,i)=>{if(n){const seg=plot.segments.find(x=>x.id===r+':'+i);assert(seg);near(seg.units,n);near(seg.x,170+560*sum/extent);near(seg.y,51+56*r);near(seg.width,560*n/extent);count++;}sum+=n;});assert.equal(plot.zeros.includes(r),sum===0);});assert.equal(plot.segments.length,count);
 }else if(s.mode==='multiply'){
  assert.equal(plot.counters.length,a*b);assert.equal(new Set(plot.counters.map(x=>x.id)).size,a*b);for(const x of plot.counters){const[r,c]=x.id.split(':').map(Number);assert(r<a&&c<b);near(x.x,64+25*c);near(x.y,54+25*r);near(x.width,17);near(x.height,17);}
 }else{
  const q=Math.floor(total/d),rem=total%d,count=s.mode==='share'?d:q,size=s.mode==='share'?q:d;assert.deepEqual(plot.groups,Array.from({length:count},(_,i)=>i));assert.equal(plot.members.length,count*size);assert.equal(new Set(plot.members).size,count*size);for(const text of plot.members){const[g,i]=text.split(':').map(Number);assert(g>=0&&g<count&&i>=0&&i<size);}assert.deepEqual(plot.remainders,Array.from({length:rem},(_,i)=>i));assert.equal(plot.members.length+plot.remainders.length,total);
 }
 for(const t of plot.labels)assert(t.x>=-.01&&t.y>=-.01&&t.x+t.w<=plot.width+.01&&t.y+t.h<=plot.height+.01,JSON.stringify(t));
 return{checks,plot:plot.type,allDiagramQuantitiesMatchIndependentInputFormulas:true,labelsWithinViewBox:true};
};
