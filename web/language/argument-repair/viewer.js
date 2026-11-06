'use strict';

const { facts, scenarios, appeals, evaluateRepair } = globalThis.PrimerRhetoric;
const get = id => document.getElementById(id);
const factIds = Object.keys(facts);
let repaired = false;

function element(tag, text, className) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  if (className) node.className = className;
  return node;
}

for (const [id, scenario] of Object.entries(scenarios)) get('scenario').add(new Option(scenario.title, id));
for (const [id, appeal] of Object.entries(appeals)) get('appeal').add(new Option(appeal.name, id));
for (const [index, id] of factIds.entries()) {
  const fact = facts[id], row = element('li');
  row.id = 'fact-' + id;
  row.value = index + 1;
  row.tabIndex = -1;
  row.append(element('h3', fact.title), element('p', fact.text));
  get('facts').append(row);
}

function inspectFact(id) {
  for (const row of get('facts').children) row.removeAttribute('data-selected');
  const row = get('fact-' + id);
  row.dataset.selected = 'true';
  row.focus();
  row.scrollIntoView({ block: 'nearest', behavior: 'instant' });
}

function arrow(parent, from, to) {
  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  svg.setAttribute('viewBox', '0 0 32 28');
  svg.setAttribute('aria-hidden', 'true');
  svg.classList.add('map-arrow');
  svg.dataset.from = from;
  svg.dataset.to = to;
  const path = document.createElementNS(svg.namespaceURI, 'path');
  path.setAttribute('d', 'M16 1 V24 M8 17 L16 25 L24 17');
  svg.append(path);
  parent.append(svg);
}

function mapCard(id, title, text, className) {
  const card = element('div', undefined, 'map-card ' + className);
  card.dataset.node = id;
  card.append(element('h3', title), element('p', text));
  return card;
}

function drawMap(map) {
  const host = get('map');
  host.replaceChildren();
  const premises = element('div');
  premises.dataset.node = 'premises';
  premises.setAttribute('role', 'group');
  premises.setAttribute('aria-label', 'Premises considered together');
  const used = new Set();
  for (const [index, premise] of map.premises.entries()) {
    const card = mapCard('premise-' + index, 'Premise ' + (index + 1), premise.text, 'premise');
    card.append(element('p', premise.kind, 'kind'));
    const links = element('div', undefined, 'evidence-links');
    for (const id of premise.evidence) {
      used.add(id);
      const button = element('button', 'Inspect record ' + (factIds.indexOf(id) + 1));
      button.type = 'button';
      button.dataset.evidence = id;
      button.addEventListener('click', () => inspectFact(id));
      links.append(button);
    }
    card.append(links);
    premises.append(card);
  }
  host.append(premises);
  arrow(host, 'premises', 'warrant');
  host.append(mapCard('warrant', 'Connecting claim · warrant', map.warrant, 'warrant'));
  arrow(host, 'warrant', 'conclusion');
  host.append(mapCard('conclusion', 'Conclusion', map.conclusion, 'conclusion'));
  for (const id of factIds) get('fact-' + id).toggleAttribute('data-relevant', used.has(id));
  get('map-state').textContent = repaired ? 'Repaired argument' : 'Original argument';
}

function loadScenario() {
  const scenario = scenarios[get('scenario').value];
  repaired = false;
  get('feedback').textContent = '';
  get('diagnosis').open = false;
  get('diagnosis-text').textContent = scenario.diagnosis;
  for (const id of factIds) {
    const row = get('fact-' + id);
    row.hidden = !scenario.records.includes(id);
    row.removeAttribute('data-selected');
  }
  get('choices').replaceChildren();
  for (const choice of scenario.choices) {
    const label = element('label'), input = element('input');
    input.type = 'radio';
    input.name = 'repair';
    input.value = choice.id;
    input.required = true;
    label.append(input, ' ' + choice.text);
    get('choices').append(label);
  }
  drawMap(scenario.original);
}

function showAppeal() {
  const appeal = appeals[get('appeal').value];
  get('appeal-quote').textContent = appeal.quote;
  get('appeal-explanation').textContent = appeal.explanation;
}

get('scenario').addEventListener('change', loadScenario);
get('restore').addEventListener('click', () => {
  repaired = false;
  get('feedback').textContent = '';
  get('repair-form').reset();
  drawMap(scenarios[get('scenario').value].original);
});
get('choices').addEventListener('change', () => {
  repaired = false;
  get('feedback').textContent = '';
  drawMap(scenarios[get('scenario').value].original);
});
get('repair-form').addEventListener('submit', event => {
  event.preventDefault();
  const choice = new FormData(event.currentTarget).get('repair');
  const result = evaluateRepair(get('scenario').value, choice);
  repaired = result.correct;
  drawMap(result.map);
  get('feedback').textContent = (result.correct ? 'Repair supported. ' : 'This repair needs more work. ') + result.feedback;
});
get('appeal').addEventListener('change', showAppeal);
loadScenario();
showAppeal();
