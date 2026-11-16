import { adjacency, colouringSearch } from './search.mjs';

const get = id => document.getElementById(id);
const label = vertex => String.fromCharCode(65 + vertex);
const pairs = size => Array.from({ length: size }, (_, right) =>
  Array.from({ length: right }, (_, left) => [left, right])).flat();
const ring = size => Array.from({ length: size }, (_, index) => {
  const angle = 2 * Math.PI * index / size - Math.PI / 2;
  return [310 + 147 * Math.cos(angle), 205 + 147 * Math.sin(angle)];
});
const pentagon = [[0, 1], [1, 2], [2, 3], [3, 4], [0, 4]];
const examples = {
  wheel: { positions: [...ring(5), [310, 205]], edges: [...pentagon, ...pentagon.map((_, vertex) => [vertex, 5])] },
  pentagon: { positions: ring(5), edges: pentagon },
  complete: { positions: ring(4), edges: pairs(4) },
  bipartite: {
    positions: [[148, 71], [148, 205], [148, 339], [472, 71], [472, 205], [472, 339]],
    edges: pairs(6).filter(([left, right]) => left < 3 && right >= 3),
  },
};
const fills = ['#fffef8', '#c7e6f8', '#fadd9c', '#bcedd6', '#e7c9ef', '#facac2', '#d7d9ab'];
const canvas = get('graph');
const context = canvas.getContext('2d');
const vertices = get('vertices');
const limit = () => Number(get('palette').value);
let positions;
let edges;
let neighbours;
let manual;
let trace = [];
let current = 0;
let minimum = null;
let rows = [];

function option(value, name) {
  return new Option(name, value);
}

function endpointPair() {
  return [Number(get('from').value), Number(get('to').value)].sort((a, b) => a - b);
}

function selectedEdge() {
  const [first, second] = endpointPair();
  return edges.findIndex(([left, right]) => left === first && right === second);
}

function updateEdgeButton() {
  const [first, second] = endpointPair();
  get('toggle-edge').disabled = first === second;
  const action = selectedEdge() < 0 ? 'Add' : 'Remove';
  get('toggle-edge').textContent = action + ' edge ' + label(first) + '–' + label(second);
}

function buildRows() {
  rows = neighbours.map((_, vertex) => {
    const row = document.createElement('tr');
    const name = document.createElement('th');
    name.scope = 'row';
    name.textContent = label(vertex);
    const adjacent = document.createElement('td');
    const colourCell = document.createElement('td');
    const colour = document.createElement('select');
    colour.setAttribute('aria-label', 'Colour of vertex ' + label(vertex));
    colour.addEventListener('change', () => {
      manual = [...displayedColours()];
      manual[vertex] = Number(colour.value);
      clearTrace();
      render();
    });
    colourCell.append(colour);
    row.append(name, adjacent, colourCell);
    return { row, adjacent, colour };
  });
  vertices.replaceChildren(...rows.map(({ row }) => row));
}

function rebuildPalette() {
  for (const { colour } of rows) {
    colour.replaceChildren(option(0, 'Uncoloured'),
      ...Array.from({ length: limit() }, (_, index) => option(index + 1, 'Colour ' + (index + 1))));
  }
}

function clearTrace() {
  trace = [];
  minimum = null;
  current = 0;
}

function chooseGraph() {
  ({ positions, edges } = examples[get('example').value]);
  neighbours = adjacency(positions.length, edges);
  manual = Array(positions.length).fill(0);
  clearTrace();
  for (const id of ['from', 'to']) {
    get(id).replaceChildren(...positions.map((_, vertex) => option(vertex, label(vertex))));
  }
  get('to').value = '1';
  updateEdgeButton();
  buildRows();
  rebuildPalette();
  render();
}

function displayedColours() {
  return trace[current]?.colours ?? manual;
}

function conflictEdges(colours) {
  return edges.filter(([left, right]) => colours[left] && colours[left] === colours[right]);
}

function draw(colours, step, conflicts) {
  context.fillStyle = '#edf5ef';
  context.fillRect(0, 0, canvas.width, canvas.height);
  for (const edge of edges) {
    const [left, right] = edge;
    const rejected = step?.kind === 'reject'
      && edge.includes(step.vertex) && edge.includes(step.conflict);
    const conflict = rejected || conflicts.includes(edge);
    context.beginPath();
    context.setLineDash(conflict ? [10, 7] : []);
    context.strokeStyle = conflict ? '#a63829' : '#577777';
    context.lineWidth = conflict ? 5 : 3;
    context.moveTo(...positions[left]);
    context.lineTo(...positions[right]);
    context.stroke();
  }
  context.setLineDash([]);
  positions.forEach(([x, y], vertex) => {
    context.beginPath();
    context.arc(x, y, 27, 0, Math.PI * 2);
    context.fillStyle = fills[colours[vertex]];
    context.fill();
    context.lineWidth = step?.vertex === vertex ? 5 : 2;
    context.strokeStyle = '#254d53';
    context.stroke();
    context.fillStyle = '#173237';
    context.font = 'bold 23px system-ui';
    context.textAlign = 'center';
    context.textBaseline = 'middle';
    context.fillText(label(vertex), x, y);
    if (colours[vertex]) {
      context.font = 'bold 18px system-ui';
      context.fillText(String(colours[vertex]), x, y + 42);
    }
  });
}

function explain(step) {
  if (!step) return 'The search tries each fitting colour before backtracking. It visits vertices with more neighbours first.';
  const { kind, vertex, colour, conflict } = step;
  switch (kind) {
    case 'start': return 'Start with all vertices uncoloured. Visit vertices with more neighbours first. Break ties alphabetically.';
    case 'assign': return 'Assign colour ' + colour + ' to ' + label(vertex) + '. No coloured neighbour currently uses it.';
    case 'reject': return 'Reject colour ' + colour + ' at ' + label(vertex)
      + ' because neighbour ' + label(conflict) + ' already uses it.';
    case 'backtrack': return 'Remove colour ' + colour + ' from ' + label(vertex)
      + ' because later vertices could not all be coloured with that assignment.';
    case 'solution': return 'Every edge joins two different colours. This assignment is a witness.';
    case 'impossible': return 'Every branch has been checked. The graph cannot be coloured with ' + limit()
      + (limit() === 1 ? ' colour.' : ' colours.');
  }
}

function render() {
  const step = trace[current];
  const colours = displayedColours();
  const conflicts = conflictEdges(colours);
  draw(colours, step, conflicts);
  rows.forEach(({ row, adjacent, colour }, vertex) => {
    row.toggleAttribute('data-current', step?.vertex === vertex);
    adjacent.textContent = neighbours[vertex].map(label).join(', ') || 'None';
    colour.value = colours[vertex];
  });

  const coloured = colours.filter(Boolean).length;
  const conflictList = conflicts.map(([left, right]) => label(left) + '–' + label(right)).join(', ');
  get('colouring-status').textContent = edges.length + ' edges. ' + coloured + ' of ' + positions.length
    + ' vertices coloured. ' + (conflicts.length ? 'Conflicting edges: ' + conflictList + '.'
      : coloured === positions.length ? 'This is a proper colouring.' : 'No conflicting edges so far.');
  get('trace').hidden = !step;
  get('previous').disabled = current === 0;
  get('next').disabled = current >= trace.length - 1;
  get('result').disabled = current >= trace.length - 1;
  get('step').max = Math.max(0, trace.length - 1);
  get('step').value = current;
  get('step-count').textContent = (current + 1) + ' / ' + trace.length;
  const proof = minimum === null ? '' : 'Minimum: ' + minimum + (minimum === 1 ? ' colour. '
    : ' colours. Complete searches exhausted all smaller palettes. ');
  get('explanation').textContent = proof + explain(step);
}

function goToStep(index) {
  current = index;
  render();
}

get('example').addEventListener('change', chooseGraph);
get('palette').addEventListener('change', () => {
  manual = displayedColours().map(colour => colour <= limit() ? colour : 0);
  clearTrace();
  rebuildPalette();
  render();
});
get('from').addEventListener('change', updateEdgeButton);
get('to').addEventListener('change', updateEdgeButton);
get('toggle-edge').addEventListener('click', () => {
  manual = [...displayedColours()];
  const index = selectedEdge();
  edges = index < 0 ? [...edges, endpointPair()] : edges.filter((_, candidate) => candidate !== index);
  neighbours = adjacency(positions.length, edges);
  clearTrace();
  updateEdgeButton();
  render();
});
get('search').addEventListener('click', () => {
  trace = colouringSearch(neighbours, limit()).steps;
  minimum = null;
  goToStep(0);
});
get('minimum').addEventListener('click', () => {
  for (let count = 1; count <= positions.length; count += 1) {
    const run = colouringSearch(neighbours, count);
    if (!run.found) continue;
    minimum = count;
    get('palette').value = count;
    rebuildPalette();
    trace = run.steps;
    goToStep(trace.length - 1);
    break;
  }
});
get('previous').addEventListener('click', () => goToStep(current - 1));
get('next').addEventListener('click', () => goToStep(current + 1));
get('result').addEventListener('click', () => goToStep(trace.length - 1));
get('step').addEventListener('input', event => goToStep(Number(event.target.value)));
chooseGraph();
