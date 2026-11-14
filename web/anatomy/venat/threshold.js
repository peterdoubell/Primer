'use strict';
const threshold = document.querySelector('#threshold');
const layers = [...document.querySelectorAll('.layer')];
threshold.addEventListener('change', () => {
  layers.forEach((layer, index) => { layer.checked = index === Number(threshold.value); });
  layers[0].dispatchEvent(new Event('input'));
});

if (new URLSearchParams(location.search).get('from') === 'ra.intracranial-haemorrhage') {
  const back = document.querySelector('#return-context');
  back.href = '/app/#/radiology/ra.intracranial-haemorrhage';
  back.textContent = 'Return to the haemorrhage reporting reference';
}
