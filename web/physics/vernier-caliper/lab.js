import { readScale, inspectDivision, makeSpecimen } from './model.mjs';
import { instrument, scales } from './drawing.mjs';

const el = id => document.getElementById(id);
let divisions = 10;
let specimen = { widthSteps: 147, zeroSteps: -2 };
let loaded = false;
let sawClosed = true;
let sawContact = false;
const places = () => divisions === 10 ? 1 : 2;
const mm = value => value.toFixed(places());
const status = message => { el('result').textContent = message; };

function draw() {
  const gap = el('gap').valueAsNumber;
  const angle = el('angle').valueAsNumber;
  const index = el('division').valueAsNumber;
  const reading = readScale(gap, specimen.zeroSteps, divisions);
  const selected = inspectDivision(reading, index);
  const contact = gap === (loaded ? specimen.widthSteps : 0);
  if (contact && loaded) sawContact = true;
  if (contact && !loaded) sawClosed = true;
  const scene = loaded ? (contact ? 'Both jaws touch the block.' : 'There is clearance between the block and the moving jaw.')
    : (contact ? 'The measuring faces touch. Read the signed zero error.' : 'The empty jaws are open.');
  el('contact-state').textContent = scene;
  el('instrument').setAttribute('aria-label', '3D caliper. ' + scene);
  el('gap').setAttribute('aria-valuetext', contact ? 'At contact' : 'Open, ' + (gap - el('gap').min) + ' graduation steps from contact');
  el('angle').setAttribute('aria-valuetext', angle + ' degrees');
  el('division-out').textContent = String(index);
  el('previous').disabled = index <= 0;
  el('next').disabled = index >= divisions;
  el('contact').disabled = contact;
  el('construction').textContent = divisions + ' moving divisions span ' + (divisions - 1) + ' fixed millimetres. Each moving division is ' + mm(1 / divisions) + ' mm shorter than one fixed division.';
  let alignment;
  if (selected.nearest < 0) alignment = 'This division is left of the first fixed mark.';
  else if (Math.abs(selected.offset) < 1e-8) alignment = 'Division ' + index + ' lines up with the ' + selected.nearest + ' mm mark.';
  else alignment = 'Division ' + index + ' is ' + mm(Math.abs(selected.offset)) + ' mm ' + (selected.offset < 0 ? 'left' : 'right') + ' of the ' + selected.nearest + ' mm mark.';
  el('alignment').textContent = alignment;
  const wholePosition = reading.origin < 0 ? 'The vernier zero is left of the fixed zero.' :
    (reading.matchingDivision === 0 ? 'The vernier zero meets the ' + reading.whole + ' mm mark.'
      : 'The vernier zero lies between ' + reading.whole + ' and ' + (reading.whole + 1) + ' mm.');
  el('description').textContent = wholePosition + ' Vernier division ' + reading.matchingDivision + ' aligns with the fixed ' + (reading.whole + reading.matchingDivision) + ' mm graduation.';
  instrument(el('instrument'), gap / divisions, loaded ? specimen.widthSteps / divisions : null, reading, angle);
  scales(el('scale'), reading, index, false);
  scales(el('detail'), reading, index, true);
}

function setJaws(insert) {
  loaded = insert;
  el('gap').min = insert ? specimen.widthSteps : 0;
  el('gap').max = 30 * divisions;
  el('gap').step = 1;
  el('gap').value = insert ? specimen.widthSteps + 2 * divisions : 0;
  el('division').value = 0;
  draw();
}

function fresh() {
  divisions = Number(el('graduations').value);
  specimen = makeSpecimen(divisions);
  el('division').max = divisions;
  el('measurement').reset();
  sawClosed = false;
  sawContact = false;
  setJaws(false);
  status('A new block and zero setting are ready. Read the closed jaws first.');
}

function worked() {
  const zero = specimen.zeroSteps / divisions;
  const atContact = readScale(specimen.widthSteps, specimen.zeroSteps, divisions);
  const closed = readScale(0, specimen.zeroSteps, divisions);
  const calibration = zero < 0
    ? 'The zero lies left of the origin. Division ' + closed.matchingDivision + ' aligns, so the closed reading is −(' + divisions + ' − ' + closed.matchingDivision + ')/' + divisions + ' = ' + mm(zero) + ' mm.'
    : 'With the jaws closed, division ' + closed.matchingDivision + ' aligns. The closed reading is ' + mm(zero) + ' mm.';
  status(calibration + ' At contact the reading is ' + atContact.whole + ' + ' + atContact.matchingDivision + '/' + divisions + ' = ' + mm(atContact.origin) + ' mm. Block width = ' + mm(atContact.origin) + ' − (' + mm(zero) + ') = ' + mm(specimen.widthSteps / divisions) + ' mm.');
}

el('zero').addEventListener('click', () => setJaws(false));
el('sample').addEventListener('click', () => setJaws(true));
el('contact').addEventListener('click', () => { el('gap').value = el('gap').min; draw(); });
for (const id of ['gap', 'division', 'angle']) el(id).addEventListener('input', draw);
el('previous').addEventListener('click', () => { el('division').stepDown(); draw(); });
el('next').addEventListener('click', () => { el('division').stepUp(); draw(); });
el('new-sample').addEventListener('click', fresh);
el('graduations').addEventListener('change', fresh);
el('solution').addEventListener('click', worked);
el('measurement').addEventListener('submit', event => {
  event.preventDefault();
  const matches = (id, steps) => Math.abs(el(id).valueAsNumber * divisions - steps) < 1e-7;
  if (!sawClosed || !sawContact) status('Check the empty closed jaws, then insert the block and close to contact before scoring.');
  else if (!matches('blank', specimen.zeroSteps)) status('Recheck the closed reading. A vernier zero left of the fixed zero gives a negative offset.');
  else if (!matches('loaded', specimen.widthSteps + specimen.zeroSteps)) status('Recheck the reading at contact. Add the aligned division divided by ' + divisions + ' to the preceding whole millimetre.');
  else if (!matches('corrected', specimen.widthSteps)) status('Both scale readings agree. Subtract the signed closed reading from the reading at contact.');
  else status('Correct. The measured block width is ' + mm(specimen.widthSteps / divisions) + ' mm, with the zero error removed.');
});
setJaws(false);
new ResizeObserver(draw).observe(el('scale'));
