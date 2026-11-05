'use strict';
const ids=['before','after','exposureBefore','exposureAfter'];
const get=id=>document.getElementById(id);
const format=value=>String(Number(value.toPrecision(6)));
function update(){
  const [before,after,exposureBefore,exposureAfter]=ids.map(id=>get(id).valueAsNumber);
  for(const id of ids)document.querySelector('output[for="'+id+'"]').value=get(id).value;
  const rates=[before/exposureBefore*100000,after/exposureAfter*100000];
  const table=document.querySelector('tbody');
  table.replaceChildren();
  for(const row of [['Earlier',before,exposureBefore,format(rates[0])],['Later',after,exposureAfter,format(rates[1])]]){
    const tr=document.createElement('tr');
    row.forEach((value,i)=>{const cell=document.createElement(i?'td':'th');if(!i)cell.scope='row';cell.textContent=value;tr.append(cell);});
    table.append(tr);
  }
  const svg=document.querySelector('svg'),ceiling=Math.max(...rates,1);
  svg.replaceChildren();
  function shape(tag,attributes,text){
    const node=document.createElementNS(svg.namespaceURI,tag);
    for(const [name,value] of Object.entries(attributes))node.setAttribute(name,value);
    if(text!==undefined)node.textContent=text;
    svg.append(node);
  }
  for(const tick of [0,ceiling/2,ceiling]){
    const y=180-140*tick/ceiling;
    shape('line',{x1:60,x2:345,y1:y,y2:y,stroke:'#bcc8c5'});
    shape('text',{x:50,y:y+5,'text-anchor':'end'},format(tick));
  }
  rates.forEach((rate,i)=>{
    const height=140*rate/ceiling,x=100+130*i;
    shape('rect',{x,y:180-height,width:50,height,fill:i?'#a65a29':'#227e79','data-period':i});
    shape('text',{x:x+25,y:170-height,'text-anchor':'middle'},format(rate));
    shape('text',{x:x+25,y:210,'text-anchor':'middle'},i?'Later':'Earlier');
  });
  const countChange=before===0?null:100*(after-before)/before;
  const rateChange=rates[0]===0?null:100*(rates[1]-rates[0])/rates[0];
  get('comparison').textContent='Count change: '+(countChange===null?'undefined from a zero baseline':format(countChange)+'%')+
    '. Observed-rate change: '+(rateChange===null?'undefined from a zero baseline':format(rateChange)+'%')+'.';
  const direction=rates[1]>rates[0]?'increased':rates[1]<rates[0]?'decreased':'stayed the same';
  const correct='Observed incident rate '+direction+': '+format(rates[0])+' to '+format(rates[1])+' per 100,000 exposures.';
  const unsupported='Underlying risk definitely '+(after>=before?'increased':'decreased')+'.';
  const options=[
    [correct,true,'This headline states the observed rates and their denominator.'],
    ['There were '+after+' incidents later; everyone should expect the same number next period.',false,'A count in these records does not establish the count in a future period. Check exposure and uncertainty.'],
    [unsupported,false,'These records describe observed rates. A definite claim about underlying risk needs additional evidence.']
  ];
  get('choices').replaceChildren();
  get('feedback').textContent='';
  const offset=(before+after)%options.length;
  const ordered=options.slice(offset).concat(options.slice(0,offset));
  for(const [text,valid,explanation] of ordered){
    const button=document.createElement('button');button.type='button';button.textContent=text;
    button.onclick=()=>{get('feedback').textContent=(valid?'Supported. ':'Revise. ')+explanation;};
    get('choices').append(button);
  }
}
for(const id of ids)get(id).addEventListener('input',update);
update();
