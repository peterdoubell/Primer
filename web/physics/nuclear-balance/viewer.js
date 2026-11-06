'use strict';
const get=id=>document.getElementById(id);
const api=globalThis.PrimerNuclearBalance;
let revealed=false;
for(const item of api.cases)get('reaction').add(new Option(item.title,item.id));
function svg(tag,attrs,text){
 const node=document.createElementNS('http://www.w3.org/2000/svg',tag);
 for(const [key,value]of Object.entries(attrs))node.setAttribute(key,value);
 if(text!==undefined)node.textContent=text;
 get('diagram').append(node);
}
function values(){
 const a=get('nucleons').valueAsNumber,q=get('charge').valueAsNumber;
 return Number.isInteger(a)&&Number.isInteger(q)&&q>=0&&a>=q?{nucleons:a,charge:q}:null;
}
function draw(){
 const {example,before}=api.ledger(get('reaction').value),guess=values();
 const products=example.output.map((row,i)=>i===0?{label:revealed?row.label:'Missing nucleus',nucleons:guess?.nucleons??'?',charge:guess?.charge??'?'}:row);
 get('diagram').replaceChildren();
 svg('title',{id:'diagram-title'},example.title+' with a missing product nucleus');
 svg('text',{x:140,y:30},'Incoming');svg('text',{x:500,y:30},'Outgoing');
 for(const [column,rows]of [[0,example.input],[1,products]]){
  const x=column?390:30,spacing=Math.min(90,310/rows.length),start=215-spacing*(rows.length-1)/2;
  rows.forEach((row,i)=>{
   const y=start+i*spacing;
   svg('rect',{x,y:y-25,width:220,height:50,rx:6,fill:column===1&&i===0?'#225b65':'#263943',stroke:'#83b8c4'});
   svg('text',{x:x+110,y:y-4},row.label);
   svg('text',{x:x+110,y:y+16},'A = '+row.nucleons+' · charge = '+row.charge+' e');
  });
 }
 svg('line',{x1:268,x2:367,y1:215,y2:215,stroke:'#eac66d','stroke-width':3});
 svg('path',{d:'M 353 206 L 367 215 L 353 224',fill:'none',stroke:'#eac66d','stroke-width':3});
 const after=guess?api.totals([guess,...example.output.slice(1)]):null;
 const body=get('ledger');body.replaceChildren();
 for(const [name,key]of [['Nucleon count','nucleons'],['Total charge (e)','charge']]){
  const row=body.insertRow();
  for(const [i,value]of [name,before[key],after?.[key]??'Incomplete'].entries()){
   const cell=document.createElement(i===0?'th':'td');if(!i)cell.scope='row';cell.textContent=value;row.append(cell);
  }
 }
 get('note').textContent=example.note;
 get('source').href=example.source;
}
function reset(){
 revealed=false;get('answer').reset();get('feedback').textContent='';draw();
}
get('reaction').addEventListener('change',reset);
for(const id of ['nucleons','charge'])get(id).addEventListener('input',()=>{revealed=false;get('feedback').textContent='';draw();});
get('answer').addEventListener('submit',event=>{
 event.preventDefault();
 const v=values();
 if(!v){get('feedback').textContent='Use whole numbers with 0 ≤ charge ≤ nucleon count.';return;}
 const correct=api.checkMissingNucleus(get('reaction').value,v.nucleons,v.charge);
 revealed=correct;
 get('feedback').textContent=correct?'Both totals balance. The product nucleus is shown.':'The proposed totals do not both balance. Compare the before and after columns.';
 draw();
});
get('reveal').addEventListener('click',()=>{
 const row=api.ledger(get('reaction').value).example.output[0];
 get('nucleons').value=row.nucleons;get('charge').value=row.charge;revealed=true;
 get('feedback').textContent='Product shown. Check how the other particles complete both totals.';draw();
});
draw();
