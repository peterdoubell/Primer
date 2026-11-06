'use strict';
const get=id=>document.getElementById(id);
const format=value=>String(Number(value.toPrecision(6)));
function cell(tag,text){
  const element=document.createElement(tag);
  element.textContent=text;
  if(tag==='th')element.scope='row';
  return element;
}
function exactFraction(numerator, denominator){
  let a=numerator,b=denominator;
  while(b!==0n){
    const remainder=a%b;
    a=b;b=remainder;
  }
  return (numerator/a).toString()+'/'+(denominator/a).toString();
}
function draw(){
  const distribution=meanDistribution(get('n').valueAsNumber,get('p').valueAsNumber);
  const {n,p,outcomes,standardError,observationVariance,withinPointTwo}=distribution;
  document.querySelector('output[for="n"]').value=n;
  document.querySelector('output[for="p"]').value=format(p*100)+'%';
  get('summary').replaceChildren();
  for(const [label,value] of [['One observation: population SD',Math.sqrt(observationVariance)],['Mean of '+n+': standard error',standardError]]){
    const row=document.createElement('tr');row.append(cell('th',label),cell('td',format(value)));get('summary').append(row);
  }
  const svg=document.querySelector('svg');svg.replaceChildren();
  const x=value=>50+290*value,y=value=>185-145*value;
  function shape(tag,attrs,text){
    const node=document.createElementNS(svg.namespaceURI,tag);
    for(const [name,value] of Object.entries(attrs))node.setAttribute(name,value);
    if(text!==undefined)node.textContent=text;
    svg.append(node);
  }
  const lower=Math.max(0,p-.2),upper=Math.min(1,p+.2);
  shape('rect',{x:x(lower),y:40,width:x(upper)-x(lower),height:145,fill:'#e9f0e9'});
  for(const tick of [0,.5,1]){
    shape('line',{x1:50,x2:340,y1:y(tick),y2:y(tick),stroke:'#b8c7c2'});
    shape('text',{x:40,y:y(tick)+5,'text-anchor':'end'},tick);
    shape('text',{x:x(tick),y:208,'text-anchor':'middle'},tick);
  }
  shape('text',{x:8,y:23},'Probability');
  shape('text',{x:195,y:233,'text-anchor':'middle'},'Possible mean');
  const width=Math.min(16,230/(n+1));
  for(const outcome of outcomes){
    shape('rect',{x:x(outcome.mean)-width/2,y:y(outcome.probability),width,height:145*outcome.probability,fill:outcome.inBand?'#207d78':'#9d5b2d','data-k':outcome.successes});
  }
  shape('line',{x1:x(p),x2:x(p),y1:40,y2:185,stroke:'#273e45','stroke-dasharray':'4 4'});
  get('outcomes').replaceChildren();
  for(const outcome of outcomes){
    const row=document.createElement('tr');
    const exact=cell('td',exactFraction(outcome.numerator,outcome.denominator));exact.className='exact';
    row.append(cell('th',outcome.successes),cell('td',outcome.successes+'/'+n),exact);
    get('outcomes').append(row);
  }
  get('reading').textContent='Mean of the distribution: '+format(p)+'. Standard error: '+format(standardError)+'. Probability the sample mean is within 0.2 of p, including endpoints: '+format(100*withinPointTwo.probability)+'%.';
}
get('n').addEventListener('input',draw);
get('p').addEventListener('input',draw);
draw();
