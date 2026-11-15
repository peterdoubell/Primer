'use strict';
const get = id => document.getElementById(id);
function draw() {
  const rate=get('rate').valueAsNumber, sensitivity=get('sensitivity').valueAsNumber, specificity=get('specificity').valueAsNumber;
  const valid=Number.isInteger(rate)&&rate>=0&&rate<=10000&&
    [sensitivity,specificity].every(value=>Number.isInteger(value)&&value>=0&&value<=100);
  get('results').hidden=!valid;
  if(!valid){get('status').textContent='Use whole numbers within the displayed ranges.';return;}
  get('status').textContent='';
  const truePositive=rate*sensitivity, falseNegative=rate*(100-sensitivity);
  const falsePositive=(10000-rate)*(100-specificity), trueNegative=(10000-rate)*specificity;
  const rows=[
    ['Defective',truePositive,falseNegative,100*rate],
    ['Without defects',falsePositive,trueNegative,100*(10000-rate)],
    ['Total',truePositive+falsePositive,falseNegative+trueNegative,1000000],
  ];
  const body=get('counts');body.replaceChildren();
  for(const values of rows){
    const tr=body.insertRow();
    for(const [i,value]of values.entries()){
      const cell=document.createElement(i===0?'th':'td');
      if(i===0)cell.scope='row';
      cell.textContent=typeof value==='number'?value.toLocaleString('en-US'):value;
      tr.append(cell);
    }
  }
  const positives=truePositive+falsePositive;
  get('bar').hidden=positives===0;
  const proportion=positives?truePositive/positives:0;
  get('true-bar').style.width=100*proportion+'%';
  get('false-bar').style.width=100*(1-proportion)+'%';
  get('bar').setAttribute('aria-label',truePositive+' true positives and '+falsePositive+' false positives');
  get('posterior').textContent=positives
    ? 'P(defective | positive) = '+truePositive+' / '+positives+' ≈ '+(100*proportion).toFixed(4)+'%.'
    : 'This model produces no positive tests. P(defective | positive) is undefined.';
}
for(const id of ['rate','sensitivity','specificity'])get(id).addEventListener('input',draw);
get('reset').addEventListener('click',()=>{get('rate').value=1;get('sensitivity').value=99;get('specificity').value=99;draw();});
draw();
