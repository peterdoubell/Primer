// Daimon and Masumura (Applied Optics 46, 3811–3820, 2007), distilled
// water at 20 °C. Sellmeier wavelength is in micrometres.
const sellmeier = [
  [0.5684027565, 0.005101829712],
  [0.1726177391, 0.01821153936],
  [0.02086189578, 0.02620722293],
  [0.1130748688, 10.69792721],
];

export const radians = Math.PI / 180;

export function waterIndex(wavelengthNm) {
  const wavelengthSquared = (wavelengthNm / 1000) ** 2;
  const indexSquared = sellmeier.reduce((sum, [b, pole]) => {
    return sum + b * wavelengthSquared / (wavelengthSquared - pole);
  }, 1);
  return Math.sqrt(indexSquared);
}

export function causticHeight(index, reflections) {
  const triangleFactor = (reflections + 1) ** 2;
  return Math.sqrt((triangleFactor - index ** 2) / (triangleFactor - 1));
}

// The angular radius is measured from the direction opposite the Sun.
export function angularRadius(height, index, reflections) {
  const incidence = Math.asin(height);
  const refraction = Math.asin(height / index);
  const deviation = reflections * Math.PI + 2 * (incidence - (reflections + 1) * refraction);
  return Math.abs(Math.PI - deviation);
}

const dot = ([x, y], [a, b]) => x * a + y * b;
const scale = ([x, y], factor) => [x * factor, y * factor];
const add = ([x, y], [a, b]) => [x + a, y + b];

function refract(direction, forwardNormal, indexRatio) {
  const normalComponent = dot(direction, forwardNormal);
  const tangent = add(direction, scale(forwardNormal, -normalComponent));
  const newTangent = scale(tangent, indexRatio);
  const newNormal = Math.sqrt(Math.max(0, 1 - dot(newTangent, newTangent)));
  return add(newTangent, scale(forwardNormal, newNormal));
}

function fresnelPower(height, index, reflections) {
  const airCosine = Math.sqrt(1 - height ** 2);
  const waterCosine = Math.sqrt(1 - (height / index) ** 2);
  const s = ((airCosine - index * waterCosine) / (airCosine + index * waterCosine)) ** 2;
  const p = ((index * airCosine - waterCosine) / (index * airCosine + waterCosine)) ** 2;
  // Each component transmits at entry and exit. Keeping the two
  // polarisations separate preserves the filtering from each reflection.
  return ((1 - s) ** 2 * s ** reflections + (1 - p) ** 2 * p ** reflections) / 2;
}

export function traceRay(height, index, reflections) {
  const entry = [-Math.sqrt(1 - height ** 2), height];
  const points = [entry];
  let direction = refract([1, 0], scale(entry, -1), 1 / index);

  for (let segment = 0; segment <= reflections; segment++) {
    const start = points.at(-1);
    // The other intersection of a line from a unit circle's surface.
    const hit = add(start, scale(direction, -2 * dot(start, direction)));
    points.push(hit);
    if (segment < reflections) {
      direction = add(direction, scale(hit, -2 * dot(direction, hit)));
    }
  }

  const exit = points.at(-1);
  const outgoing = refract(direction, exit, index);
  return { points, outgoing, power: fresnelPower(height, index, reflections) };
}

// Azimuth is measured around the antisolar point from its upward meridian.
// For a ground observer, the horizon satisfies
// sin(elevation) = -sin(Sun) cos(radius) + cos(Sun) sin(radius) cos(azimuth).
export function skyElevation(radius, sun, azimuth) {
  const sine = Math.cos(sun) * Math.sin(radius) * Math.cos(azimuth) - Math.sin(sun) * Math.cos(radius);
  return Math.asin(Math.max(-1, Math.min(1, sine)));
}

export function visibleHalfArc(radius, sun) {
  if (radius <= sun) return 0;
  return Math.acos(Math.min(1, Math.tan(sun) / Math.tan(radius)));
}
