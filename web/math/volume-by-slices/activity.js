const get = id => document.getElementById(id);
const styles = {
  cylinder: { exponent: 0, area: 'πR²', volume: 'πR²z', total: 'πR²H' },
  shear: { exponent: 0, area: 'πR²', volume: 'πR²z', total: 'πR²H' },
  cone: { exponent: 2, area: 'πR²(z/H)²', volume: 'πR²z³/(3H²)', total: 'πR²H/3' },
  paraboloid: { exponent: 1, area: 'πR²z/H', volume: 'πR²z²/(2H)', total: 'πR²H/2' },
};
const ink = '#193846';
const blue = '#087692';
const muted = '#607984';

function stroke(context, points, color, width = 1) {
  context.beginPath();
  for (const [index, [x, y]] of points.entries()) {
    if (index === 0) context.moveTo(x, y);
    else context.lineTo(x, y);
  }
  context.strokeStyle = color;
  context.lineWidth = width;
  context.stroke();
}

function fill(context, points, color) {
  context.beginPath();
  for (const [index, [x, y]] of points.entries()) {
    if (index === 0) context.moveTo(x, y);
    else context.lineTo(x, y);
  }
  context.closePath();
  context.fillStyle = color;
  context.fill();
}

function plotCanvas(id) {
  const canvas = get(id);
  const width = Math.round(canvas.getBoundingClientRect().width);
  if (width && canvas.width !== width) canvas.width = width;
  const context = canvas.getContext('2d');
  context.clearRect(0, 0, canvas.width, canvas.height);
  context.font = '14px system-ui';
  context.fillStyle = ink;
  return { canvas, context, width: canvas.width };
}

function circle(radius, offset, height, count = 64) {
  return Array.from({ length: count + 1 }, (_, i) => {
    const angle = 2 * Math.PI * i / count;
    return [offset + radius * Math.cos(angle), radius * Math.sin(angle), height];
  });
}

function drawSolid(state) {
  const { canvas, context, width } = plotCanvas('solid-view');
  const scale = Math.min(width / (2 * state.radius + state.shear + 1.2), 285 / (state.height + state.radius));
  const c = Math.cos(state.rotation), s = Math.sin(state.rotation);
  const pitch = Math.PI / 8;
  const project = ([x, y, z]) => {
    const along = x - state.shear / 2;
    return [width / 2 + scale * (c * along - s * y),
      180 - scale * (Math.cos(pitch) * (z - state.height / 2) + Math.sin(pitch) * (s * along + c * y))];
  };
  const levels = Array.from({ length: 9 }, (_, index) => state.height * index / 8);
  const pointAt = (angle, z) => project([state.center(z) + state.sectionRadius(z) * Math.cos(angle),
    state.sectionRadius(z) * Math.sin(angle), z]);
  for (let index = 0; index < 14; index++) {
    const angle = index * 2 * Math.PI / 14;
    stroke(context, levels.map(z => pointAt(angle, z)), '#b3c6cb');
    const below = [...levels.filter(z => z < state.cut), state.cut];
    stroke(context, below.map(z => pointAt(angle, z)), '#64a5b4');
  }
  for (const z of levels) {
    stroke(context, circle(state.sectionRadius(z), state.center(z), z).map(project),
      z <= state.cut ? '#3a879e' : muted);
  }
  const section = circle(state.sectionRadius(state.cut), state.center(state.cut), state.cut).map(project);
  fill(context, section, 'rgba(32,163,192,0.24)');
  stroke(context, section, blue, 2);
  if (state.sectionRadius(state.cut) === 0) {
    const [x, y] = section[0];
    context.fillStyle = blue;
    context.fillRect(x - 2, y - 2, 4, 4);
  }
  context.fillStyle = ink;
  context.fillText('z = ' + state.cut.toFixed(2), 12, 344);
  canvas.setAttribute('aria-label', state.name + ' wireframe with a horizontal section at z ' + state.cut.toFixed(2));
}

function drawSection(state) {
  const { canvas, context, width } = plotCanvas('section-view');
  const scale = Math.min(width / (2 * state.radius + state.shear + 1), 290 / (2 * state.radius));
  const project = ([x, y]) => [width / 2 + scale * (x - state.shear / 2), 174 - scale * y];
  const cross = project([0, 0]);
  stroke(context, [[cross[0] - 6, cross[1]], [cross[0] + 6, cross[1]]], muted);
  stroke(context, [[cross[0], cross[1] - 6], [cross[0], cross[1] + 6]], muted);
  const points = circle(state.sectionRadius(state.cut), state.center(state.cut), 0).map(project);
  fill(context, points, 'rgba(32,163,192,0.24)');
  stroke(context, points, blue, 2);
  const [x, y] = project([state.center(state.cut), 0]);
  context.fillStyle = blue;
  context.fillRect(x - 2, y - 2, 4, 4);
  context.fillText('r(z) = ' + state.sectionRadius(state.cut).toFixed(3), 12, 344);
  canvas.setAttribute('aria-label', 'Circular section with radius ' + state.sectionRadius(state.cut).toFixed(3) +
    ' and horizontal centre offset ' + state.center(state.cut).toFixed(3));
}

function drawArea(state) {
  const { canvas, context, width } = plotCanvas('area-view');
  const left = 44, baseline = 310, right = width - 16, top = 38;
  const x = z => left + (right - left) * z / state.height;
  const y = z => baseline - (baseline - top) * state.area(z) / state.baseArea;
  const sample = limit => Array.from({ length: 81 }, (_, i) => {
    const z = limit * i / 80;
    return [x(z), y(z)];
  });
  fill(context, [[left, baseline], ...sample(state.cut), [x(state.cut), baseline]], 'rgba(32,163,192,0.25)');
  stroke(context, [[left, 25], [left, baseline], [right, baseline]], ink);
  stroke(context, sample(state.height), blue, 2);
  stroke(context, [[x(state.cut), baseline], [x(state.cut), y(state.cut)]], blue, 2);
  context.fillStyle = ink;
  context.fillText('A(z)', 8, 27);
  context.fillText('πR²', 8, top + 4);
  context.fillText('0', left - 15, baseline + 16);
  context.fillText('H', right - 9, baseline + 16);
  context.fillText('Height z', (left + right) / 2 - 25, 345);
  canvas.setAttribute('aria-label', 'Area versus height. Area at cut equals ' + state.area(state.cut).toFixed(3) +
    ' square units. The shaded region extends from zero to height ' + state.cut.toFixed(2));
}

function render() {
  const kind = get('solid').value;
  const model = styles[kind];
  const radius = get('radius').valueAsNumber;
  const height = get('height').valueAsNumber;
  const cut = height * get('cut').valueAsNumber / 100;
  const shear = kind === 'shear' ? radius : 0;
  const baseArea = Math.PI * radius * radius;
  const sectionRadius = z => radius * Math.pow(z / height, model.exponent / 2);
  const center = z => shear * z / height;
  const area = z => baseArea * Math.pow(z / height, model.exponent);
  const volume = z => baseArea * z * Math.pow(z / height, model.exponent) / (model.exponent + 1);
  const name = get('solid').selectedOptions[0].textContent;
  get('radius-value').textContent = radius + ' units';
  get('height-value').textContent = height + ' units';
  get('cut-value').textContent = cut.toFixed(2) + ' units';
  get('cut').setAttribute('aria-valuetext', cut.toFixed(2) + ' units of ' + height);
  const state = { name, radius, height, cut, shear, baseArea, sectionRadius, center, area,
    rotation: get('rotation').valueAsNumber * Math.PI / 180 };
  drawSolid(state);
  drawSection(state);
  drawArea(state);
  const rows = [
    ['Area at the cut', model.area, area(cut).toFixed(3) + ' square units'],
    ['Volume below the cut', model.volume, volume(cut).toFixed(3) + ' cubic units'],
    ['Total volume', model.total, volume(height).toFixed(3) + ' cubic units'],
  ];
  get('measures').replaceChildren(...rows.map(([name, formula, value]) => {
    const row = document.createElement('tr');
    for (const [tag, text] of [['th', name], ['td', formula], ['td', value]]) {
      const cell = document.createElement(tag);
      cell.textContent = text;
      if (tag === 'th') cell.scope = 'row';
      row.append(cell);
    }
    return row;
  }));
  get('equation').textContent = 'R is the top radius and H is the total height. The accumulated volume is the integral of A(t) from 0 to z.';
  get('comparison').textContent = kind === 'shear'
    ? 'Shearing shifts the centre of each slice by Rz/H. Its radius stays R, so the sheared and straight cylinders have equal volume at every cut.'
    : 'Try the sheared cylinder at the same dimensions. Compare the areas and the total volumes.';
}

for (const id of ['solid', 'radius', 'height', 'cut', 'rotation']) get(id).addEventListener('input', render);
const resize = new ResizeObserver(render);
for (const id of ['solid-view', 'section-view', 'area-view']) resize.observe(get(id));
render();
