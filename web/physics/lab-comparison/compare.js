'use strict';
const fields = Array.from(document.querySelectorAll('input'));
const plot = document.querySelector('svg');
const result = document.querySelector('#result');
const format = value => String(Number(value.toPrecision(6)));

function shape(tag, attributes, text) {
  const element = document.createElementNS(plot.namespaceURI, tag);
  for (const [name, value] of Object.entries(attributes)) element.setAttribute(name, value);
  if (text !== undefined) element.textContent = text;
  plot.append(element);
}

function draw() {
  plot.replaceChildren();
  if (fields.some(input => !input.validity.valid)) {
    result.textContent = 'Enter both estimates, nonnegative uncertainties and a correlation from −1 to 1.';
    return;
  }
  const [a, ua, b, ub, rho] = fields.map(input => input.valueAsNumber);
  const difference = a - b;
  // Factor the covariance so perfect cancellation at rho = 1 stays exact.
  const u = Math.hypot(ua - rho * ub, Math.sqrt((1 - rho) * (1 + rho)) * ub);
  const low = Math.min(a - ua, b - ub);
  const high = Math.max(a + ua, b + ub);
  if (![high - low, difference, u].every(Number.isFinite)) {
    result.textContent = 'Rescale the estimates and uncertainties to a smaller numerical range.';
    return;
  }
  const x = value => low === high ? 300 : 65 + 470 * ((value - low) / (high - low));
  for (const [lab, mean, uncertainty, y, color] of [['A',a,ua,43,'#086965'], ['B',b,ub,99,'#9b451a']]) {
    shape('text', {x:8,y:y+5}, 'Lab ' + lab);
    const start = x(mean - uncertainty), end = x(mean + uncertainty);
    shape('line', {x1:start,x2:end,y1:y,y2:y,stroke:color,'stroke-width':4});
    for (const edge of [start,end]) shape('line', {x1:edge,x2:edge,y1:y-7,y2:y+7,stroke:color});
    shape('circle', {cx:x(mean),cy:y,r:6,fill:color});
  }
  for (const value of new Set([low,high])) shape('text', {x:x(value),y:147,'text-anchor':'middle'}, format(value));
  const score = Math.abs(difference) / u;
  const comparison = u === 0 ? (difference === 0 ? 'The estimates coincide with zero modelled difference uncertainty.' : 'The nonzero difference is incompatible with zero modelled difference uncertainty.')
    : 'The estimates differ by ' + format(score) + ' combined standard uncertainties.';
  result.textContent = 'A − B = ' + format(difference) + '. Standard uncertainty of the difference = ' + format(u) + '. ' + comparison;
}
for (const input of fields) input.addEventListener('input', draw);
draw();
