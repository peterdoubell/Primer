'use strict';

const {witnesses, splits, splitLabel, countChanges, score} = globalThis.PrimerStemma;
const get = id => document.getElementById(id);
const casePicker = get('case'), splitPicker = get('split'), passagePicker = get('passage');
const passages = [
  {label: '1 · Dock location', readings: ['west', 'west', 'east', 'east']},
  {label: '2 · Cargo', readings: ['salt', 'salt', 'grain', 'grain']},
  {label: '3 · Signal', readings: ['bell', 'horn', 'bell', 'horn']},
  {label: '4 · Arrival time', readings: ['dawn', 'dawn', 'dawn', 'dusk']},
  {label: '5 · Descriptor', readings: ['', '', 'tall', 'high']},
  {label: '6 · Weather', readings: ['clear', null, 'mist', 'mist']},
];
const cases = [
  {name: 'Matching disagreements', rows: [0, 1, 3, 4], note: 'Compare agreements that divide the copies two against two with a reading found in one copy alone.'},
  {name: 'Conflicting passages', rows: [0, 2, 3], note: 'Different passages may support different families. Try excluding one passage and see what changes.'},
  {name: 'Damaged copy', rows: [3, 5], note: 'Witness B is unreadable at the weather passage. Compare what the surviving evidence can distinguish.'},
];
const option = (value, label) => new Option(label, value);
const readingLabel = value => value === null ? 'Unreadable' : value === '' ? 'Omitted' : value;
const collationBody = get('collation').tBodies[0];

for (const [index, item] of cases.entries()) casePicker.add(option(index, item.name));
for (const [index, split] of splits.entries()) splitPicker.add(option(index, splitLabel(split)));
for (const [index, label] of [...splits.map(splitLabel), 'Tie'].entries()) {
  const wrapper = document.createElement('label'), input = document.createElement('input');
  input.type = 'radio';
  input.name = 'prediction';
  input.value = index;
  input.required = true;
  wrapper.append(input, ' ' + label);
  get('choices').append(wrapper);
}

function cell(row, tag, text, scope) {
  const item = document.createElement(tag);
  if (scope) item.scope = scope;
  item.textContent = text;
  row.append(item);
  return item;
}

function hideComparison() {
  get('comparison').hidden = true;
  get('feedback').textContent = '';
}

function renderCase() {
  const {rows, note} = cases[casePicker.selectedIndex];
  get('case-note').textContent = note;
  collationBody.replaceChildren();
  for (const index of rows) {
    const passage = passages[index], row = collationBody.insertRow();
    const heading = cell(row, 'th', '', 'row');
    const label = document.createElement('label'), input = document.createElement('input');
    input.type = 'checkbox';
    input.value = index;
    input.checked = true;
    input.addEventListener('change', hideComparison);
    label.append(input, ' ' + passage.label);
    heading.append(label);
    for (const value of passage.readings) cell(row, 'td', readingLabel(value));
  }
  get('prediction').reset();
  hideComparison();
}

function svgNode(tag, attributes, text) {
  const node = document.createElementNS('http://www.w3.org/2000/svg', tag);
  for (const [key, value] of Object.entries(attributes)) node.setAttribute(key, value);
  if (text !== undefined) node.textContent = text;
  get('map').append(node);
}

function drawMap() {
  const split = splits[splitPicker.selectedIndex], passage = passages[Number(passagePicker.value)];
  const {cost, assignments} = countChanges(passage.readings, split);
  const [left, right] = assignments[0];
  const values = [...split.map(index => passage.readings[index]), left, right];
  const coordinates = [[66,55],[66,171],[334,55],[334,171],[158,113],[242,113]];
  get('map').replaceChildren();
  svgNode('title', {id:'map-title'}, splitLabel(split) + ' for ' + passage.label + ', ' + cost + ' changes');
  for (const [a, b] of [[0,4],[1,4],[2,5],[3,5],[4,5]]) {
    const [x1,y1] = coordinates[a], [x2,y2] = coordinates[b];
    const changed = values[a] !== null && values[b] !== null && values[a] !== values[b];
    svgNode('line', {x1,y1,x2,y2,class:changed ? 'edge changed' : 'edge'});
  }
  for (const [i,[x,y]] of coordinates.entries()) {
    svgNode('circle', {cx:x,cy:y,r:7,class:values[i] === null ? 'unknown' : ''});
    const label = i < 4 ? witnesses[split[i]] : i === 4 ? 'X' : 'Y';
    svgNode('text',{x,y:y+29},label + ' · ' + readingLabel(values[i]));
  }
  const plural = cost === 1 ? ' change' : ' changes';
  get('map-note').textContent = cost + plural + ' in this minimum assignment. Dashed red edges mark changes. ' +
    (assignments.length === 1 ? 'One minimum assignment for X and Y.' : assignments.length + ' assignments for X and Y reach the same minimum.');
}

function compare(prediction) {
  const selected = [...collationBody.querySelectorAll('input:checked')].map(input => Number(input.value));
  if (!selected.length) {
    get('feedback').textContent = 'Select at least one passage to compare.';
    return;
  }
  const result = score(selected.map(index => passages[index].readings));
  const lowest = Math.min(...result.map(row => row.total));
  const leaders = result.filter(row => row.total === lowest);
  const winner = leaders.length > 1 ? 3 : result.indexOf(leaders[0]);
  const table = get('scores');
  table.tHead?.remove();
  table.tBodies[0]?.remove();
  table.tFoot?.remove();
  const header = table.createTHead().insertRow();
  cell(header,'th','Passage','col');
  for (const split of splits) cell(header,'th',splitLabel(split),'col');
  const body = table.createTBody();
  for (const [i,index] of selected.entries()) {
    const row = body.insertRow();
    cell(row,'th',passages[index].label,'row');
    for (const split of result) cell(row,'td',split.results[i].cost);
  }
  const totals = table.createTFoot().insertRow();
  cell(totals,'th','Total','row');
  for (const split of result) cell(totals,'td',split.total);
  const labels = leaders.map(row => splitLabel(row.split)).join(', ');
  get('best').textContent = 'Lowest total: ' + lowest + ' · ' + labels + '.';
  get('feedback').textContent = prediction === null ? 'Comparison shown.' :
    prediction === winner ? 'Correct. Your prediction matches the selected evidence.' :
    'Try changing a passage, then use the table to see how each split gained its score.';
  splitPicker.selectedIndex = result.indexOf(leaders[0]);
  passagePicker.replaceChildren(...selected.map(index => option(index,passages[index].label)));
  get('comparison').hidden = false;
  drawMap();
}

get('prediction').addEventListener('submit', event => {
  event.preventDefault();
  compare(Number(new FormData(event.currentTarget).get('prediction')));
});
get('reveal').addEventListener('click', () => compare(null));
casePicker.addEventListener('change',renderCase);
splitPicker.addEventListener('change',drawMap);
passagePicker.addEventListener('change',drawMap);
renderCase();
