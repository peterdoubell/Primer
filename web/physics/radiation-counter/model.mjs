// Homogeneous Poisson interactions and an initially live, non-extendable counter.
// All times are seconds. Input rate describes interactions at the counting chain.
export function settings(raw = {}) {
  const value = { rate: 5000, deadTime: .0002, duration: .1, seed: 104729, ...raw };
  for (const [key, low, high] of [['rate', 0, 20000], ['deadTime', 0, .001], ['duration', .0001, 2]]) {
    if (!Number.isFinite(value[key]) || value[key] < low || value[key] > high) throw RangeError('Invalid ' + key);
  }
  if (!Number.isInteger(value.seed) || value.seed < 0 || value.seed > 0xffffffff) throw RangeError('Invalid seed');
  return value;
}

export function randomStream(seed) {
  let state = seed >>> 0;
  return () => {
    state = (state + 0x6d2b79f5) >>> 0;
    let value = state;
    value = Math.imul(value ^ value >>> 15, value | 1);
    value ^= value + Math.imul(value ^ value >>> 7, value | 61);
    return (((value ^ value >>> 14) >>> 0) + .5) / 4294967296;
  };
}

export function countArrivals(times, deadTime, duration) {
  if (!(Number.isFinite(deadTime) && deadTime >= 0 && Number.isFinite(duration) && duration > 0)) throw RangeError('Invalid counter timing');
  const accepted = new Uint8Array(times.length);
  let ready = 0, count = 0, deadSeconds = 0, previous = -Infinity;
  times.forEach((time, index) => {
    if (!Number.isFinite(time) || time < 0 || time >= duration || time <= previous) throw RangeError('Interaction times must increase inside the gate');
    previous = time;
    if (time >= ready) {
      accepted[index] = 1;
      count += 1;
      ready = time + deadTime;
      deadSeconds += Math.min(deadTime, duration - time);
    }
    // A lost interaction does not move the recovery boundary.
  });
  const liveSeconds = Math.max(0, duration - deadSeconds);
  return { accepted, count, lost: times.length - count, deadSeconds, liveSeconds,
    recordedRate: count / duration, liveRate: liveSeconds ? count / liveSeconds : null };
}

export function simulate(raw = {}) {
  const state = settings(raw), random = randomStream(state.seed), times = [];
  if (state.rate) {
    let time = 0;
    for (;;) {
      time += -Math.log(random()) / state.rate;
      if (time >= state.duration) break;
      times.push(time);
    }
  }
  return { state, times: new Float64Array(times), ...countArrivals(times, state.deadTime, state.duration) };
}

export function steadyRate(rate, deadTime) {
  return rate / (1 + rate * deadTime);
}

export function repeatGates(raw = {}, repetitions = 256) {
  const state = settings(raw);
  if (!Number.isInteger(repetitions) || repetitions < 2 || repetitions > 4096) throw RangeError('Invalid gate count');
  const counts = [];
  for (let run = 0; run < repetitions; run += 1) {
    const random = randomStream((state.seed + Math.imul(run + 1, 0x9e3779b9)) >>> 0);
    let time = 0, ready = 0, count = 0;
    if (state.rate) for (;;) {
      time += -Math.log(random()) / state.rate;
      if (time >= state.duration) break;
      if (time >= ready) { count += 1; ready = time + state.deadTime; }
    }
    counts.push(count);
  }
  const mean = counts.reduce((sum, value) => sum + value, 0) / repetitions;
  const variance = counts.reduce((sum, value) => sum + (value - mean) ** 2, 0) / (repetitions - 1);
  return { counts, repetitions, mean, variance, standardDeviation: Math.sqrt(variance) };
}

function logGamma(value) {
  // Lanczos log-gamma; arguments below are positive integers.
  const coefficients = [676.5203681218851, -1259.1392167224028, 771.32342877765313,
    -176.61502916214059, 12.507343278686905, -.13857109526572012,
    9.9843695780195716e-6, 1.5056327351493116e-7];
  const z = value - 1;
  let x = .99999999999980993;
  coefficients.forEach((coefficient, index) => { x += coefficient / (z + index + 1); });
  const t = z + 7.5;
  return .9189385332046727 + (z + .5) * Math.log(t) - t + Math.log(x);
}

export function gammaCDF(shape, x) {
  if (!Number.isInteger(shape) || shape < 1 || !Number.isFinite(x) || x < 0) throw RangeError('Invalid gamma coordinates');
  if (x === 0) return 0;
  const factor = Math.exp(shape * Math.log(x) - x - logGamma(shape));
  const epsilon = 2e-14;
  if (x < shape + 1) {
    let term = 1 / shape, sum = term;
    for (let step = 1; step < 10000; step += 1) {
      term *= x / (shape + step);
      sum += term;
      if (Math.abs(term) < Math.abs(sum) * epsilon) return Math.max(0, Math.min(1, sum * factor));
    }
  } else {
    const small = 1e-300;
    let b = x + 1 - shape, c = 1 / small, d = 1 / b, fraction = d;
    for (let step = 1; step < 10000; step += 1) {
      const an = -step * (step - shape);
      b += 2;
      d = an * d + b; if (Math.abs(d) < small) d = small;
      c = b + an / c; if (Math.abs(c) < small) c = small;
      d = 1 / d;
      const change = d * c;
      fraction *= change;
      if (Math.abs(change - 1) < epsilon) return Math.max(0, Math.min(1, 1 - factor * fraction));
    }
  }
  throw Error('The renewal distribution did not converge');
}

export function countTail(raw, count) {
  const state = settings(raw);
  if (!Number.isInteger(count) || count < 0) throw RangeError('Invalid count');
  if (count === 0) return 1;
  const liveWait = state.duration - (count - 1) * state.deadTime;
  if (liveWait <= 0 || state.rate === 0) return 0;
  // Time of the nth accepted interaction = Gamma(n, rate) + (n−1) deadTime.
  return gammaCDF(count, state.rate * liveWait);
}

export function prediction(raw = {}) {
  const state = settings(raw);
  if (!state.rate) return { distribution: [{ count: 0, probability: 1 }], mean: 0, variance: 0,
    standardDeviation: 0, mass: 1, fano: null };
  const incidentMean = state.rate * state.duration;
  let upper = Math.ceil(incidentMean + 16 * Math.sqrt(incidentMean + 1) + 100);
  if (state.deadTime) upper = Math.min(upper, Math.ceil(state.duration / state.deadTime) + 1);
  const tail = count => countTail(state, count);
  function firstBelow(threshold) {
    let low = 1, high = upper;
    while (low < high) {
      const middle = Math.floor((low + high) / 2);
      if (tail(middle) > threshold) low = middle + 1;
      else high = middle;
    }
    return low;
  }
  const first = Math.max(0, firstBelow(1 - 1e-13) - 1), last = firstBelow(1e-13);
  const distribution = [];
  let previous = tail(first);
  for (let count = first; count < last; count += 1) {
    const next = tail(count + 1);
    distribution.push({ count, probability: Math.max(0, previous - next) });
    previous = next;
  }
  const mass = distribution.reduce((sum, row) => sum + row.probability, 0);
  if (mass < 1 - 1e-10) throw Error('The renewal distribution is incomplete');
  distribution.forEach(row => { row.probability /= mass; });
  const mean = distribution.reduce((sum, row) => sum + row.count * row.probability, 0);
  const variance = distribution.reduce((sum, row) => sum + (row.count - mean) ** 2 * row.probability, 0);
  return { distribution, mean, variance, standardDeviation: Math.sqrt(variance), mass,
    fano: mean ? variance / mean : null };
}
