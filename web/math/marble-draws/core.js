'use strict';
(function () {
  function fraction(numerator, denominator) {
    if (!denominator) return null;
    let a = numerator, b = denominator;
    while (b) [a, b] = [b, a % b];
    return [numerator / a, denominator / a];
  }

  function model(total, red, replacement, condition, event) {
    if (!Number.isInteger(total) || total < 1 || total > 10 ||
        !Number.isInteger(red) || red < 0 || red > total || typeof replacement !== 'boolean' ||
        !['none','red','blue'].includes(condition) ||
        !['both-red','second-red','different','at-least-red'].includes(event)) throw RangeError('Unsupported draw settings');
    const marbles = Array.from({length: total}, (_,i) => ({
      id: (i < red ? 'R' : 'B') + (i < red ? i + 1 : i - red + 1),
      color: i < red ? 'red' : 'blue',
    }));
    const outcomes = [];
    for (const [i, first] of marbles.entries()) {
      for (const [j, second] of marbles.entries()) {
        const possible = replacement || i !== j;
        const given = possible && (condition === 'none' || first.color === condition);
        const matches = {
          'both-red': first.color === 'red' && second.color === 'red',
          'second-red': second.color === 'red',
          'different': first.color !== second.color,
          'at-least-red': first.color === 'red' || second.color === 'red',
        };
        const hit = matches[event];
        outcomes.push({first: first.id, second: second.id, possible, given, favorable: given && hit});
      }
    }
    const allowed = outcomes.filter(row => row.possible).length;
    const denominator = outcomes.filter(row => row.given).length;
    const numerator = outcomes.filter(row => row.favorable).length;
    return {marbles, outcomes, allowed, numerator, denominator, probability: fraction(numerator,denominator)};
  }

  const api = {model, fraction};
  if (typeof module !== 'undefined') module.exports = api;
  globalThis.PrimerMarbleDraws = api;
})();
