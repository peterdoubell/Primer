'use strict';
const assert=require('assert/strict');
module.exports=async function(root){
 const v=await root.evaluate(e=>({model:e.ratioModel(),charts:[...e.querySelectorAll('[data-ratio-plot]')].map(s=>({bars:[...s.querySelectorAll('[data-ratio-bar]')].map(n=>({i:+n.dataset.ratioBar,x:+n.getAttribute('x'),width:+n.getAttribute('width'),exact:n.dataset.exactAmount})),zeros:[...s.querySelectorAll('[data-ratio-zero]')].map(n=>+n.dataset.ratioZero),labels:[...s.querySelectorAll('text')].map(n=>{const b=n.getBBox();return{text:n.textContent,x:b.x,y:b.y,w:b.width,h:b.height};}),height:s.viewBox.baseVal.height})),bad:[...e.querySelectorAll('svg *')].flatMap(n=>[...n.attributes].filter(a=>/NaN|Infinity/.test(a.value)).map(a=>a.value))}));
 assert.deepEqual(v.bad,[]);const m=v.model,s=m.state,[a,b,c,d,t]=['a','b','c','d','target'].map(k=>Number(s[k]));let rows=[];let checks=0;
 const near=(x,y)=>{assert(Number.isFinite(x)&&Number.isFinite(y));assert(Math.abs(x-y)<1e-8*Math.max(1,Math.abs(y)),x+' != '+y);checks++;};
 const bad=(['scale','compare','share','missing'].includes(s.mode)&&a+b===0)||(s.mode==='compare'&&c+d===0)||(['missing','rate','recipe','map','model'].includes(s.mode)&&a===0)||(s.mode==='mapCompare'&&(a===0||b===0));
 if(bad){assert.equal(m.status,'undefined');assert.equal(v.charts.length,0);return{undefinedHasNoStaleGeometry:true,checks};}
 switch(s.mode){
  case'scale':rows=[[a,b,a*c,b*c]];break;
  case'compare':rows=[[a/(a+b),c/(c+d)]];break;
  case'share':{const k=t/(a+b);rows=[[a*k,b*k,t]];break;}
  case'missing':rows=[[t,b*t/a,t+b*t/a]];break;
  case'rate':case'recipe':rows=[[a,t],[b,b*t/a]];break;
  case'map':rows=[[1,t],[a,a*t]];break;
  case'model':rows=[[100*b,100*b/a]];break;
  case'mapCompare':rows=[[t/a,t/b]];break;
  default:throw Error('Unknown state');
 }
 assert.equal(v.charts.length,rows.length);
 rows.forEach((values,i)=>{const chart=v.charts[i],extent=s.mode==='compare'?1:Math.max(...values)||1;assert.equal(chart.bars.length+chart.zeros.length,values.length);for(let j=0;j<values.length;j++){
  const bar=chart.bars.find(r=>r.i===j);if(!values[j])assert(chart.zeros.includes(j));else{assert(bar);near(bar.x,185);near(bar.width,555*values[j]/extent);const[n,d='1']=bar.exact.split('/');near(Number(n)/Number(d),values[j]);}
 }for(const label of chart.labels)assert(label.x>=-0.01&&label.y>=-0.01&&label.x+label.w<=800.01&&label.y+label.h<=chart.height+.01,JSON.stringify(label));});
 return{checks,charts:rows.length,allRenderedBarLengthsMatchIndependentFormulas:true,labelsInsideViewBox:true};
};
