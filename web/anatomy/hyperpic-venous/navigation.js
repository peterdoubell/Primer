'use strict';

const contexts = new Map([
  ['rad.5.venous-csf', '/app/#/node/rad.5.venous-csf'],
  ['ra.venous-sinus-thrombosis', '/app/#/radiology/ra.venous-sinus-thrombosis'],
]);
const from = new URLSearchParams(location.search).get('from');
const returnLink = document.getElementById('return');
if (returnLink) {
  if (contexts.has(from)) {
    returnLink.href = contexts.get(from);
    if (from === 'ra.venous-sinus-thrombosis') returnLink.textContent = 'Return to the venous thrombosis reference';
  }
  returnLink.hidden = false;
}
for (const link of document.querySelectorAll('[data-study-link]')) {
  if (contexts.has(from)) link.search = new URLSearchParams({from}).toString();
  link.hidden = false;
}
