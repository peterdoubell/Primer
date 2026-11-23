import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { countArrivals, countTail, prediction, repeatGates, simulate, steadyRate, randomStream } from '../web/physics/radiation-counter/model.mjs';
const reference = JSON.parse(await readFile(new URL('./fixtures/radiation-counter-reference.json', import.meta.url)));
const close = (actual, expected) => assert.ok(Math.abs(actual - expected) <= Math.max(2e-8, Math.abs(expected) * 3e-9), `${actual} differs from ${expected}`);

test('non-extendable recovery loses close pulses without moving its boundary', () => {
  const result = countArrivals([0, .07, .13, .19, .24], .1, .5);
  assert.deepEqual([...result.accepted], [1, 0, 1, 0, 1]);
  assert.equal(result.count, 3); assert.equal(result.lost, 2);
  close(result.liveSeconds, .2);
});
test('exact recovery boundaries are accepted and the final dead interval is clipped to the gate', () => {
  assert.deepEqual([...countArrivals([0, .25, .5, .75], .25, 1).accepted], [1, 1, 1, 1]);
  const clipped = countArrivals([.8, .9], .2, 1);
  close(clipped.deadSeconds, .2); close(clipped.liveSeconds, .8); close(clipped.liveRate, 1.25);
  assert.throws(() => countArrivals([1], .2, 1), /inside the gate/);
  assert.throws(() => countArrivals([.5, .4], .2, 1), /increase/);
});
test('removing recovery preserves the entire seeded interaction stream', () => {
  const first = simulate(), ideal = simulate({ deadTime: 0 }), again = simulate();
  assert.deepEqual(first.times, ideal.times); assert.deepEqual(first, again);
  assert.equal(ideal.lost, 0); assert.equal(ideal.count, ideal.times.length);
  assert.notDeepEqual(first.times, simulate({ seed: 104730 }).times);
  const random = randomStream(0);
  for (let n = 0; n < 10000; n += 1) { const u = random(); assert.ok(u > 0 && u < 1); }
});
test('finite-gate predictions match independent SciPy gamma-distribution reference values', () => {
  for (const row of reference.cases) {
    const model = prediction(row.state);
    close(model.mean, row.mean); close(model.variance, row.variance);
    for (const probe of row.tails) close(countTail(row.state, probe.count), probe.value);
    assert.ok(model.mass > 1 - 1e-10);
  }
});
test('Poisson and single-event finite-gate limits retain their exact moments', () => {
  const ideal = prediction({ rate: 300, duration: .01, deadTime: 0 });
  close(ideal.mean, 3); close(ideal.variance, 3); close(ideal.fano, 1);
  const single = prediction({ rate: 5000, duration: .0001, deadTime: .001 });
  const p = 1 - Math.exp(-.5);
  close(single.mean, p); close(single.variance, p * (1 - p));
  assert.ok(single.distribution.every(row => row.count <= 1));
  close(steadyRate(5000, .0002), 2500);
  assert.ok(steadyRate(20000, .0005) < 1 / .0005);
});
test('fresh seeded gates reproduce the predicted count mean and underdispersion', () => {
  for (const deadTime of [0, .0002, .0005]) {
    const state = { rate: 5000, deadTime, duration: .1 }, expected = prediction(state), sample = repeatGates(state, 4096);
    assert.ok(Math.abs(sample.mean - expected.mean) < 6 * expected.standardDeviation / Math.sqrt(sample.repetitions));
    assert.ok(Math.abs(sample.variance / expected.variance - 1) < .15);
    assert.equal(sample.counts.length, 4096);
    assert.deepEqual(sample, repeatGates(state, 4096));
  }
});
test('zero input and invalid instrument settings have explicit outcomes', () => {
  assert.equal(simulate({ rate: 0 }).count, 0);
  assert.deepEqual(repeatGates({ rate: 0 }, 4).counts, [0, 0, 0, 0]);
  assert.equal(prediction({ rate: 0 }).fano, null);
  for (const state of [{ rate: -1 }, { rate: Infinity }, { duration: 0 }, { deadTime: -.1 }, { seed: 1.2 }]) assert.throws(() => simulate(state), /Invalid/);
});
