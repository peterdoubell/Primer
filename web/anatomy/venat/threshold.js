'use strict';
const threshold = document.querySelector('#threshold');
const layers = [...document.querySelectorAll('.layer')];
threshold.addEventListener('change', () => {
  layers.forEach((layer, index) => { layer.checked = index === Number(threshold.value); });
  layers[0].dispatchEvent(new Event('input'));
});

const back = document.querySelector('#return-context');
if (new URLSearchParams(location.search).get('from') === 'ra.intracranial-haemorrhage') {
  back.href = '/app/#/radiology/ra.intracranial-haemorrhage';
  back.textContent = 'Return to the haemorrhage reporting reference';
}
back.hidden = false;
