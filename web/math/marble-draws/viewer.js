'use strict';
const get = id => document.getElementById(id);
const {model, fraction} = globalThis.PrimerMarbleDraws;
const display = value => value === null ? 'Undefined' : value.join('/');
function cell(row, tag, text, scope) {
  const node = document.createElement(tag);
  node.textContent = text;
  if (scope) node.scope = scope;
  row.append(node);
  return node;
}
function draw() {
  const total = get('total').valueAsNumber;
  get('red').max = total;
  const red = get('red').valueAsNumber, replacement = get('replacement').checked;
  const condition = get('condition').value, event = get('event').value;
  const state = model(total,red,replacement,condition,event);
  get('total-value').textContent = total;
  get('red-value').textContent = red + ' red · ' + (total-red) + ' blue';
  get('result').textContent = state.probability
    ? state.numerator + ' favourable outcomes out of ' + state.denominator + ' consistent outcomes. Probability ' + display(state.probability) + '.'
    : state.allowed ? 'The stated first-draw information is impossible for this bag. Conditional probability is undefined.'
    : 'Two draws without replacement cannot be completed with this bag.';
  get('assumptions').textContent = state.allowed + ' equally likely ordered outcomes before conditioning. ' +
    (replacement ? 'The second draw uses the original bag.' : 'The second draw uses the remaining marbles.');
  get('selected').textContent = 'Select an outcome to inspect it.';
  const table = get('outcomes');
  table.tHead?.remove();
  table.tBodies[0]?.remove();
  const heading = table.createTHead().insertRow();
  cell(heading,'th','First / second','col');
  for (const marble of state.marbles) cell(heading,'th',marble.id,'col');
  const body = table.createTBody();
  for (const [i,first] of state.marbles.entries()) {
    const row = body.insertRow();
    cell(row,'th',first.id,'row');
    for (let j=0;j<total;j++) {
      const outcome = state.outcomes[i*total+j];
      const td = row.insertCell();
      const button = document.createElement('button');
      button.type = 'button';
      const description = !outcome.possible ? 'unavailable' : !outcome.given ? 'outside the given information' :
        outcome.favorable ? 'favourable outcome' : 'event not met';
      button.textContent = !outcome.possible ? '—' : !outcome.given ? '×' : outcome.favorable ? '✓' : '·';
      button.setAttribute('aria-label',outcome.first + ' then ' + outcome.second + ', ' + description);
      td.className = !outcome.possible ? 'unavailable' : !outcome.given ? 'outside' : outcome.favorable ? 'favorable' : '';
      button.addEventListener('click',()=>{get('selected').textContent = outcome.first+' → '+outcome.second+' · '+description+'.';});
      td.append(button);
    }
  }
  const paths = get('paths').tBodies[0];
  paths.replaceChildren();
  for (const first of ['R','B']) for (const second of ['R','B']) {
    const count = state.outcomes.filter(row=>row.given&&row.first.startsWith(first)&&row.second.startsWith(second)).length;
    const row = paths.insertRow();
    cell(row,'th',(first==='R'?'Red':'Blue')+' → '+(second==='R'?'Red':'Blue'),'row');
    cell(row,'td',count);
    cell(row,'td',display(fraction(count,state.denominator)));
  }
}
for (const id of ['total','red','replacement','condition','event']) get(id).addEventListener('input',draw);
get('quiz').addEventListener('click',()=>{
  get('total').value=5;get('red').max=5;get('red').value=3;
  get('replacement').checked=false;get('condition').value='none';get('event').value='both-red';draw();
});
draw();
