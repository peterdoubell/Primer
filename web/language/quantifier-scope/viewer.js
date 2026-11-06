(function(){
'use strict';
const {children,trees,evaluate}=ScopeStudy,$=id=>document.getElementById(id),NS='http://www.w3.org/2000/svg';
let mask=273;
function svg(tag,attrs,text){const e=document.createElementNS(NS,tag);for(const [k,v]of Object.entries(attrs))e.setAttribute(k,v);if(text)e.textContent=text;return e;}
function list(id,items){$(id).replaceChildren(...items.map(text=>{const li=document.createElement('li');li.textContent=text;return li;}));}
for(let c=0;c<3;c++){
 const tr=document.createElement('tr'),th=document.createElement('th');th.scope='row';th.textContent=children[c];tr.append(th);
 for(let t=0;t<3;t++){
  const td=document.createElement('td'),label=document.createElement('label'),input=document.createElement('input');input.type='checkbox';input.id='link-'+c+'-'+t;input.setAttribute('aria-label',children[c]+' climbed '+trees[t]);
  input.addEventListener('change',()=>{mask^=1<<(3*c+t);$('example').value='custom';render();});label.append(input);td.append(label);tr.append(td);
 }$('relation').append(tr);
}
for(let i=0;i<3;i++)for(const [x,names]of [[100,children],[540,trees]]){$('nodes').append(svg('circle',{cx:x,cy:70+100*i,r:30}),svg('text',{x,y:75+100*i,'text-anchor':'middle'},names[i]));}
function render(){
 const state=evaluate(mask);$('feedback').textContent='';$('edges').replaceChildren();
 for(let c=0;c<3;c++)for(let t=0;t<3;t++){
  $('link-'+c+'-'+t).checked=state.rows[c][t];
  if(state.rows[c][t])$('edges').append(svg('line',{x1:130,y1:70+100*c,x2:510,y2:70+100*t,'data-child':c,'data-tree':t}));
 }
 $('map-description').textContent=children.map((name,c)=>name+' climbed '+(state.witnesses[c].map(t=>trees[t]).join(', ')||'no trees')).join('. ')+'.';
 $('each-result').textContent=state.each?'True: every child has at least one tree.':'False: at least one child has no tree.';
 $('one-result').textContent=state.one?'True: a shared tree exists.':'False: no tree was climbed by every child.';
 list('each-evidence',children.map((name,c)=>name+': '+(state.witnesses[c].map(t=>trees[t]).join(', ')||'no witness — this child makes the first reading false')));
 list('one-evidence',trees.map((name,t)=>{const missing=children.filter((_,c)=>!state.rows[c][t]);return name+': '+(missing.length?'not climbed by '+missing.join(', '):'climbed by all three children — a shared witness');}));
}
$('example').addEventListener('change',()=>{mask=Number($('example').value);render();});
$('challenge').addEventListener('change',()=>{$('feedback').textContent='';});
$('check').addEventListener('click',()=>{
 const s=evaluate(mask),target=$('challenge').value;
 const success={'only-each':s.each&&!s.one,both:s.each&&s.one,neither:!s.each&&!s.one,'only-one':s.one&&!s.each}[target];
 $('feedback').textContent=success?'Scene matches the challenge. Inspect the witnesses above to explain why.':target==='only-one'?'No scene can meet this challenge: any shared tree also supplies a tree for each child.':'This scene does not match yet. Use the missing-child and shared-tree evidence above, then edit the table.';
});
render();
})();
