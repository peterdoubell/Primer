'use strict';

(() => {
  const witnesses = Object.freeze(['A', 'B', 'C', 'D']);
  const splits = Object.freeze([[0, 1, 2, 3], [0, 2, 1, 3], [0, 3, 1, 2]].map(Object.freeze));
  const splitLabel = ([a, b, c, d]) => witnesses[a] + witnesses[b] + ' | ' + witnesses[c] + witnesses[d];

  function countChanges(readings, split) {
    const leaves = split.map(index => readings[index]);
    const states = [...new Set(leaves.filter(value => value !== null))];
    // An entirely unreadable passage contributes zero to every split.
    if (!states.length) return {cost: 0, assignments: [[null, null]]};
    let cost = Infinity;
    let assignments = [];
    for (const left of states) {
      for (const right of states) {
        const internal = [left, left, right, right];
        const changes = Number(left !== right) + leaves.filter((value, i) =>
          value !== null && value !== internal[i]).length;
        if (changes < cost) {
          cost = changes;
          assignments = [];
        }
        if (changes === cost) assignments.push([left, right]);
      }
    }
    return {cost, assignments};
  }

  function score(passages) {
    return splits.map(split => {
      const results = passages.map(readings => countChanges(readings, split));
      return {split, results, total: results.reduce((sum, row) => sum + row.cost, 0)};
    });
  }

  globalThis.PrimerStemma = Object.freeze({witnesses, splits, splitLabel, countChanges, score});
})();
