'use strict';
function meanDistribution(n, successTenths) {
  if (!Number.isSafeInteger(n) || n < 1 || n > 60)
    throw new RangeError('Use 1–60 independent observations.');
  if (!Number.isSafeInteger(successTenths) || successTenths < 0 || successTenths > 10)
    throw new RangeError('Use a success probability from 0/10 to 10/10.');
  const a = BigInt(successTenths), b = 10n - a;
  const denominator = 10n ** BigInt(n);
  const outcomes = [];
  let choose = 1n, within = 0n;
  for (let k = 0; k <= n; k++) {
    const weight = choose * a ** BigInt(k) * b ** BigInt(n - k);
    const inBand = Math.abs(k * 10 - n * successTenths) <= 2 * n;
    if (inBand) within += weight;
    outcomes.push({successes:k, mean:k/n, numerator:weight, denominator, probability:Number(weight)/Number(denominator), inBand});
    if (k < n) choose = choose * BigInt(n - k) / BigInt(k + 1);
  }
  const p = successTenths / 10;
  return {
    n, p, outcomes, denominator,
    observationVariance:p * (1 - p),
    meanVariance:p * (1 - p) / n,
    standardError:Math.sqrt(p * (1 - p) / n),
    withinPointTwo:{numerator:within, denominator, probability:Number(within)/Number(denominator)}
  };
}
if (typeof module !== 'undefined') module.exports = {meanDistribution};
