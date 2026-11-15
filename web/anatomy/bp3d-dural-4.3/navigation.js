'use strict';

const contexts = new Map([
  ['ra.venous-sinus-thrombosis', ['radiology', 'Return to the venous sinus thrombosis reference']],
  ['ra.intracranial-haemorrhage', ['radiology', 'Return to the haemorrhage reporting reference']],
  ['rad.5.intracranial-haemorrhage', ['node', 'Return to Intracranial Haemorrhage']],
]);
const query = new URLSearchParams(location.search);
const from = query.get('from');
const returnLink = document.querySelector('#return-context');
if (contexts.has(from)) {
  const [route, label] = contexts.get(from);
  returnLink.href = '/app/#/' + route + '/' + from;
  returnLink.textContent = label;
}

returnLink.hidden = false;

const layers = {
  sinuses: ['FJ5005', 'FJ5222', 'FJ4704', 'FJ4705', 'FJ5232', 'FJ4716', 'FJ5140', 'FJ5064', 'FJ5098', 'FJ5207', 'FJ5008'],
  jugular: ['FJ5008'],
  deep: ['FJ4705', 'FJ4654', 'FJ4690', 'FJ5046'],
  cortical: ['FJ4695', 'FJ5007', 'FJ5090', 'FJ5091', 'FJ5194', 'FJ5195', 'FJ5196'],
};
const focus = query.get('focus');
if (Object.hasOwn(layers, focus)) {
  for (const layer of document.querySelectorAll('.layer')) {
    layer.checked = layers[focus].includes(layer.value);
  }
}

for (const id of ['atlas-link', 'mrv-link', 'swi-link']) {
  const link = document.getElementById(id);
  if (link) {
    link.search = location.search;
    link.hidden = false;
  }
}
