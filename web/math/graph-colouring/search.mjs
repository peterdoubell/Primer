export function adjacency(size, edges) {
  const neighbours = Array.from({ length: size }, () => []);
  for (const [left, right] of edges) {
    neighbours[left].push(right);
    neighbours[right].push(left);
  }
  return neighbours.map(list => list.sort((a, b) => a - b));
}

export function colouringSearch(neighbours, limit) {
  const order = neighbours.map((_, vertex) => vertex)
    .sort((a, b) => neighbours[b].length - neighbours[a].length || a - b);
  const colours = Array(order.length).fill(0);
  const steps = [];

  function record(kind, vertex = null, colour = null, conflict = null) {
    steps.push({ kind, vertex, colour, conflict, colours: [...colours] });
  }

  function visit(depth) {
    if (depth === order.length) return true;
    const vertex = order[depth];
    for (let colour = 1; colour <= limit; colour += 1) {
      const conflict = neighbours[vertex].find(other => colours[other] === colour);
      if (conflict !== undefined) {
        record('reject', vertex, colour, conflict);
        continue;
      }
      colours[vertex] = colour;
      record('assign', vertex, colour);
      if (visit(depth + 1)) return true;
      colours[vertex] = 0;
      record('backtrack', vertex, colour);
    }
    return false;
  }

  record('start');
  const found = visit(0);
  record(found ? 'solution' : 'impossible');
  return { steps, found };
}
