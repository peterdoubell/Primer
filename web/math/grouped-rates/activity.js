const get = id => document.getElementById(id);
const canvas = get('workers');
const points = get('rates');
const groups = [['A', 9, 4], ['B', 8, 3]];
const colours = ['#20568b', '#96501f'];
let difference = 0;

function result(name, easyRate, hardRate) {
  const easy = get('easy-' + name.toLowerCase()).valueAsNumber;
  const hard = 100 - easy;
  const successes = [easyRate * (easy / 10), hardRate * (hard / 10)];
  return { name, counts: [easy, hard], successes, total: successes[0] + successes[1] };
}

function markGrid(teams) {
  const context = canvas.getContext('2d');
  const measuredWidth = Math.round(canvas.getBoundingClientRect().width);
  if (measuredWidth && canvas.width !== measuredWidth) canvas.width = measuredWidth;
  const block = Math.min(240, Math.floor((canvas.width - 36) / 2));
  const cell = Math.floor(block / 10);
  const left = (canvas.width - (20 * cell + 22)) / 2;
  const top = 42;
  const height = top + 10 * cell + 34;
  if (canvas.height !== height) canvas.height = height;
  context.clearRect(0, 0, canvas.width, canvas.height);
  context.font = '15px system-ui';
  teams.forEach((team, groupIndex) => {
    const start = left + groupIndex * (10 * cell + 22);
    context.fillStyle = '#1e354d';
    context.fillText('Team ' + team.name, start, 25);
    for (let i = 0; i < 100; i++) {
      const easy = i < team.counts[0];
      const within = easy ? i : i - team.counts[0];
      const stratum = easy ? 0 : 1;
      const x = start + (i % 10) * cell;
      const y = top + Math.floor(i / 10) * cell;
      if (within < team.successes[stratum]) {
        context.fillStyle = colours[stratum];
        context.fillRect(x + 1, y + 1, cell - 3, cell - 3);
      } else {
        context.strokeStyle = colours[stratum];
        context.strokeRect(x + 1.5, y + 1.5, cell - 4, cell - 4);
      }
    }
    context.fillStyle = '#1e354d';
    context.fillText(team.total + ' successes', start, top + 10 * cell + 23);
  });
  canvas.setAttribute('aria-label', teams.map(team =>
    'Team ' + team.name + ' completed ' + team.successes[0] + ' of ' + team.counts[0] +
    ' easy tasks and ' + team.successes[1] + ' of ' + team.counts[1] + ' hard tasks').join('. '));
}

function cell(tag, text) {
  const element = document.createElement(tag);
  element.textContent = text;
  return element;
}

function rate(successes, total) {
  return successes + '/' + total + ' (' + Math.round(successes / total * 100) + '%)';
}

function render() {
  const teams = groups.map(group => result(...group));
  for (const team of teams) {
    const label = team.counts[0] + ' easy, ' + team.counts[1] + ' hard';
    get('count-' + team.name.toLowerCase()).textContent = label;
    get('easy-' + team.name.toLowerCase()).setAttribute('aria-valuetext', label);
  }
  markGrid(teams);
  points.replaceChildren(...['Easy', 'Hard', 'Overall'].map((name, rowIndex) => {
    const row = document.createElement('tr');
    const heading = cell('th', name);
    heading.scope = 'row';
    row.append(heading, ...teams.map(team => cell('td', rowIndex === 2 ? rate(team.total, 100) :
      rate(team.successes[rowIndex], team.counts[rowIndex]))));
    return row;
  }));
  difference = teams[0].total - teams[1].total;
  const outcome = difference === 0 ? 'The overall rates tie.' :
    'Team ' + (difference > 0 ? 'A' : 'B') + ' leads overall by ' + Math.abs(difference) + ' percentage points.';
  get('comparison').textContent = 'Team A has the higher rate at each difficulty. ' + outcome;
  get('calculation').textContent = teams.map(team => 'Team ' + team.name + ' combines ' +
    team.successes[0] + ' easy and ' + team.successes[1] + ' hard successes for ' + team.total + ' out of 100 overall.').join(' ');
  get('feedback').textContent = '';
}

for (const control of [get('easy-a'), get('easy-b')]) control.addEventListener('input', render);
get('equalise').addEventListener('click', () => {
  get('easy-b').value = get('easy-a').value;
  render();
});
get('goal').addEventListener('change', () => { get('feedback').textContent = ''; });
get('check').addEventListener('click', () => {
  const actual = difference === 0 ? 'tie' : difference > 0 ? 'forward' : 'reverse';
  get('feedback').textContent = actual === get('goal').value ?
    'That mix meets the challenge.' : 'Try another mix. Check the overall row as you change the task counts.';
});
new ResizeObserver(render).observe(canvas);
render();
