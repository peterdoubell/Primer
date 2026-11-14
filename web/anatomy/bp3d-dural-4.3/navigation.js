'use strict';

const contexts = new Map([
  ['ra.venous-sinus-thrombosis', ['radiology', 'Return to the venous sinus thrombosis reference']],
  ['ra.intracranial-haemorrhage', ['radiology', 'Return to the haemorrhage reporting reference']],
  ['rad.5.intracranial-haemorrhage', ['node', 'Return to Intracranial Haemorrhage']],
]);
const query = new URLSearchParams(location.search);
const from = query.get('from');
if (contexts.has(from)) {
  const [route, label] = contexts.get(from);
  const link = document.querySelector('#return-context');
  link.href = '/app/#/' + route + '/' + from;
  link.textContent = label;
}

const layers = {
  sinuses: ['FJ5005', 'FJ5222', 'FJ4704', 'FJ4705', 'FJ5232', 'FJ4716', 'FJ5140', 'FJ5064', 'FJ5098', 'FJ5207'],
  deep: ['FJ4705', 'FJ4654', 'FJ4690'],
};
const focus = query.get('focus');
if (Object.hasOwn(layers, focus)) {
  for (const layer of document.querySelectorAll('.layer')) {
    layer.checked = layers[focus].includes(layer.value);
  }
}
