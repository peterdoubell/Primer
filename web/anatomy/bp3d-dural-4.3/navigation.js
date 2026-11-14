'use strict';

const contexts = new Map([
  ['ra.venous-sinus-thrombosis', ['radiology', 'Return to the venous sinus thrombosis reference']],
  ['ra.intracranial-haemorrhage', ['radiology', 'Return to the haemorrhage reporting reference']],
  ['rad.5.intracranial-haemorrhage', ['node', 'Return to Intracranial Haemorrhage']],
]);
const from = new URLSearchParams(location.search).get('from');
if (contexts.has(from)) {
  const [route, label] = contexts.get(from);
  const link = document.querySelector('#return-context');
  link.href = '/app/#/' + route + '/' + from;
  link.textContent = label;
}
