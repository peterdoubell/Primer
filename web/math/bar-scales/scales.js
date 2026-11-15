'use strict';
const get = id => document.getElementById(id);
const inputs = [get('a'), get('b'), get('base')];
const ceiling = 100;
function chart(svg, baseline, scores) {
  const top = 32, bottom = 187;
  const y = value => bottom - (bottom - top) * (value - baseline) / (ceiling - baseline);
  svg.replaceChildren();
  svg.setAttribute('aria-label', 'Points from ' + baseline + ' to 100. Team A ' + scores[0] + ', Team B ' + scores[1] + '.');
  function add(tag, attrs, label) {
    const node = document.createElementNS(svg.namespaceURI, tag);
    for (const [key,value] of Object.entries(attrs)) node.setAttribute(key,value);
    if (label !== undefined) node.textContent = label;
    svg.append(node);
  }
  for (const tick of [baseline,(baseline+ceiling)/2,ceiling]) {
    add('line',{x1:49,x2:287,y1:y(tick),y2:y(tick),stroke:'#b6c5c5'});
    add('text',{x:44,y:y(tick)+5,'text-anchor':'end'},tick);
  }
  scores.forEach((score,i) => {
    const x = 80 + 110*i;
    add('rect',{x,y:y(score),width:61,height:bottom-y(score),fill:i?'#95601b':'#217c78'});
    add('text',{x:x+30,y:y(score)-5,'text-anchor':'middle'},score);
    add('text',{x:x+30,y:213,'text-anchor':'middle'},i?'Team B':'Team A');
  });
}
function update() {
  const scores = inputs.slice(0,2).map(input => input.valueAsNumber);
  // Keep both bars on scale and retain a nonzero span even for two perfect scores.
  inputs[2].max = Math.min(...scores, ceiling-1);
  const baseline = inputs[2].valueAsNumber;
  for (const input of inputs) document.querySelector('output[for="'+input.id+'"]').value = input.value;
  chart(get('full'),0,scores);
  chart(get('cropped'),baseline,scores);
  const gap = Math.abs(scores[1]-scores[0]);
  const gain = Number((ceiling/(ceiling-baseline)).toFixed(2));
  get('comparison').textContent = 'The scores differ by ' + gap + (gap===1?' point. ':' points. ') +
    (gap===0?'The bars are level on both charts.':baseline===0?'Both charts show the same gap.':
    'At this baseline the gap between bar tops takes up ' + gain + ' times as much of the chart height.') +
    ' Measured from '+baseline+', the second chart’s bars span '+(scores[0]-baseline)+' and '+(scores[1]-baseline)+' points.';
}
for (const input of inputs) input.addEventListener('input',update);
update();
