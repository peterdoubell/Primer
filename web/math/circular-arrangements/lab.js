import { analyse } from './symmetry.mjs';

const get = id => document.getElementById(id);
const count = get('size');
const movement = get('map');
const position = get('position');
const canvas = get('rings');
const ctx = canvas.getContext('2d');
const pretty = n => n.toLocaleString();
let pattern;
let analysis;

function guestMode() {
  return get('kind').value === 'guests';
}

function objectName(value) {
  return guestMode() ? 'Guest ' + String.fromCharCode(65 + value) : value ? 'Dark' : 'Light';
}

function movementName(map) {
  if (map.reflected) return 'Reflect, taking position 1 to ' + (map.shift + 1);
  if (!map.shift) return 'Identity';
  return 'Turn ' + map.shift + (map.shift === 1 ? ' place' : ' places') + ' clockwise';
}

function drawRings(map) {
  const width = canvas.clientWidth, height = canvas.clientHeight;
  const pixelRatio = window.devicePixelRatio || 1;
  canvas.width = Math.round(width * pixelRatio);
  canvas.height = Math.round(height * pixelRatio);
  ctx.setTransform(pixelRatio, 0, 0, pixelRatio, 0, 0);
  const vertical = width < 375;
  const panelWidth = width / (vertical ? 1 : 2);
  const panelHeight = height / (vertical ? 2 : 1);
  const r = Math.min(panelWidth * .32, panelHeight * .32);
  const bead = Math.min(18, r * Math.sin(Math.PI / pattern.length) * .7);
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  function ring(values, index, title) {
    const x = panelWidth * (vertical ? .5 : index + .5);
    const y = panelHeight * (vertical ? index + .49 : .49);
    ctx.beginPath();ctx.arc(x, y, r, 0, 2 * Math.PI);
    ctx.strokeStyle = '#839487';ctx.lineWidth = 2;ctx.stroke();
    values.forEach((value, i) => {
      const angle = 2 * Math.PI * i / values.length - Math.PI / 2;
      const dx = Math.cos(angle), dy = Math.sin(angle);
      const cx = x + r * dx, cy = y + r * dy;
      const isDark = !guestMode() && value === 1;
      ctx.beginPath();ctx.arc(cx,cy,bead,0,2*Math.PI);
      ctx.fillStyle = isDark ? '#275e55' : guestMode() ? '#ffe0a3' : '#fdfdf6';ctx.fill();
      ctx.strokeStyle = '#35483b';ctx.lineWidth=1.5;ctx.stroke();
      ctx.fillStyle = isDark ? '#ffffff' : '#26372c';
      ctx.font = 'bold ' + Math.min(17,bead*1.15) + 'px system-ui';
      ctx.fillText(guestMode() ? String.fromCharCode(65 + value) : isDark ? 'D' : 'L', cx,cy);
      ctx.font = '12px system-ui';ctx.fillStyle='#475c50';
      ctx.fillText(i + 1, cx + (bead + 10)*dx, cy + (bead + 10)*dy);
    });
    ctx.fillStyle='#273d34';ctx.font='bold 13px system-ui';ctx.fillText(title,x,y);
  }
  ring(pattern,0,'Original');
  ring(map.transformed,1,'After movement');
}

function showMovement() {
  const index = Number(movement.value);
  const map = analysis.results[index];
  get('previous').disabled = index === 0;
  get('next').disabled = index === analysis.results.length - 1;
  drawRings(map);
  const same = map.transformed.every((value, i)=>value === pattern[i]);
  const changed = pattern.flatMap((value, i)=>value === map.transformed[i] ? [] : [i+1]);
  get('effect').textContent = same ? 'Every numbered position contains the same object or colour after this movement.'
    : 'The contents change at positions ' + changed.join(', ') + '.';
  get('cycles').textContent = 'The position cycles are ' + map.cycles.map(cycle =>
    '(' + cycle.map(i=>i+1).join(' → ') + ')').join(' ') + '. Each cycle returns to its first position.';
  const mapping = get('mapping');
  mapping.replaceChildren();
  for (const [i, value] of pattern.entries()) {
    const row = mapping.insertRow();
    for (const text of [i+1,objectName(value),objectName(map.transformed[i])]) row.insertCell().textContent=text;
  }
  get('fixed').textContent = movementName(map) + ' fixes ' + pretty(map.fixedCount)
    + ' of the ' + pretty(analysis.labelled) + ' assignments. ' +
    (guestMode() ? 'Distinct guests can keep every position only under the identity.'
      : 'A fixed assignment gives every position in a cycle the same colour. Choose cycles whose lengths add to ' + analysis.dark + ' dark beads.');
  for (const row of get('fixed-table').rows) row.toggleAttribute('data-selected', row.sectionRowIndex === index);
}

function update() {
  const selected = movement.value;
  analysis = analyse(pattern,guestMode(),get('group').value === 'flips');
  movement.replaceChildren(...analysis.results.map((map,i)=>new Option(movementName(map),i)));
  movement.value = Number(selected) < analysis.results.length && selected !== '' ? selected : 1;
  get('population').textContent = guestMode() ? pattern.length + ' different guests occupy all ' + pattern.length + ' numbered seats.'
    : analysis.dark + ' dark beads and ' + (pattern.length - analysis.dark) + ' light beads occupy the ' + pattern.length + ' numbered positions.';
  get('labelled').textContent = pretty(analysis.labelled);
  get('classes').textContent = pretty(analysis.classes);
  get('orbit').textContent = 'The displayed arrangement has ' + analysis.orbitSize + ' distinct numbered '
    + (analysis.orbitSize === 1 ? 'view' : 'views') + '. Of the ' + analysis.results.length + ' allowed movements, '
    + analysis.stabilizer + (analysis.stabilizer === 1 ? ' fixes' : ' fix') + ' it.';
  const table = get('fixed-table');
  table.replaceChildren();
  for (const map of analysis.results) {
    const row = table.insertRow();
    row.insertCell().textContent = movementName(map);
    row.insertCell().textContent = pretty(map.fixedCount);
  }
  get('average').textContent = 'Averaging the fixed counts with Burnside’s lemma gives ' + pretty(analysis.fixedSum) + ' ÷ '
    + analysis.results.length + ' = ' + pretty(analysis.classes) + (analysis.classes === 1 ? ' class.' : ' classes.')
    + ' In the displayed class, ' + analysis.orbitSize + ' numbered ' + (analysis.orbitSize === 1 ? 'view contributes ' : 'views contribute ')
    + analysis.stabilizer + (analysis.stabilizer === 1 ? ' fixed count each.' : ' fixed counts each.')
    + ' Every class contributes a total of ' + analysis.results.length + ', the number of allowed movements.';
  get('edit').textContent = guestMode() ? 'Swap with the next seat' : 'Change bead colour';
  showMovement();
}

function buildPattern() {
  const n = Number(count.value);
  pattern = Array.from({length:n},(_,i)=>guestMode() ? i : i%2);
  position.replaceChildren(...pattern.map((_,i)=>new Option(String(i+1),i)));
  update();
}

count.replaceChildren(...Array.from({length:10},(_,i)=>new Option(String(i+3),i+3)));
count.value = '6';
count.addEventListener('change',buildPattern);
get('kind').addEventListener('change',buildPattern);
get('group').addEventListener('change',update);
movement.addEventListener('change',showMovement);
for (const [id, step] of [['previous', -1], ['next', 1]]) {
  get(id).addEventListener('click', () => {
    movement.value = Number(movement.value) + step;
    showMovement();
  });
}
get('edit').addEventListener('click',()=>{
  const i = Number(position.value);
  if (guestMode()) {
    const next = (i + 1) % pattern.length;
    [pattern[i], pattern[next]] = [pattern[next], pattern[i]];
  } else {
    pattern[i] = 1 - pattern[i];
  }
  update();
});
buildPattern();
new ResizeObserver(showMovement).observe(canvas);
