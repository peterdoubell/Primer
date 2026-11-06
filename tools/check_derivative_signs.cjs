'use strict';

const assert = require('node:assert/strict');
const { cubic, pen } = require('../web/math/derivative-signs/core.js');

function near(actual, expected, tolerance = 2e-12) {
  assert.ok(Math.abs(actual - expected) <= tolerance, actual + ' differs from ' + expected);
}

let cubicChecks = 0;
for (let numeratorA = -4; numeratorA <= 16; numeratorA++) {
  const a = numeratorA / 4;
  for (let numeratorX = -60; numeratorX <= 60; numeratorX++) {
    const x = numeratorX / 20;
    const result = cubic(a, x);
    // Integer arithmetic evaluates the exact rational polynomial and its derivatives.
    near(result.value, (numeratorX ** 3 - 300 * numeratorA * numeratorX) / 8000);
    near(result.derivative, 3 * (numeratorX ** 2 - 100 * numeratorA) / 400);
    near(result.secondDerivative, 3 * numeratorX / 10);
    cubicChecks++;
  }
  const result = cubic(a, 0);
  assert.equal(result.stationary.length, a < 0 ? 0 : a === 0 ? 1 : 2);
  for (const point of result.stationary) {
    near(cubic(a, point.x).derivative, 0);
    near(cubic(a, point.x).value, point.y);
    const before = cubic(a, point.x - .001).value;
    const after = cubic(a, point.x + .001).value;
    if (point.kind === 'local maximum') assert.ok(before < point.y && after < point.y);
    if (point.kind === 'local minimum') assert.ok(before > point.y && after > point.y);
    if (point.kind === 'stationary inflection') assert.ok(before < point.y && point.y < after);
  }
  for (const interval of result.intervals) {
    const from = interval.from ?? -3;
    const to = interval.to ?? 3;
    const midpoint = (from + to) / 2;
    // Secant signs are an independent observable of the claimed monotonic intervals.
    const delta = (to - from) / 8;
    const change = cubic(a, midpoint + delta).value - cubic(a, midpoint - delta).value;
    assert.equal(Math.sign(change), interval.sign);
  }
}
for (let numerator = 0; numerator <= 200; numerator++) {
  const width = numerator / 10;
  const result = pen(width);
  near(result.area, numerator * (200 - numerator) / 100);
  near(result.perimeter, 40);
  near(result.derivative, (200 - 2 * numerator) / 10);
  near(result.area + result.areaShortfall, 100);
  assert.ok(result.area <= 100);
  assert.equal(result.area === 100, numerator === 100);
}
assert.equal(pen(0).area, 0);
assert.equal(pen(20).area, 0);
assert.equal(cubic(0, 0).classification, 'flat');
for (const bad of [NaN, Infinity, -Infinity, '1', null, undefined]) {
  assert.throws(() => cubic(bad, 0), RangeError);
  assert.throws(() => cubic(1, bad), RangeError);
  assert.throws(() => pen(bad), RangeError);
}
for (const [a, x] of [[-1.01, 0], [4.01, 0], [1, -3.01], [1, 3.01]]) {
  assert.throws(() => cubic(a, x), RangeError);
}
assert.throws(() => pen(-.01), RangeError);
assert.throws(() => pen(20.01), RangeError);
console.log(cubicChecks + ' exact rational cubic samples, 201 pen states, stationary classifications, interval signs and invalid domains passed.');
