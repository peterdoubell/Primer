// Lengths are measured in whole vernier steps. N vernier divisions span N−1 mm.
export function readScale(gapSteps, zeroSteps, divisions) {
  const indicatedSteps = gapSteps + zeroSteps;
  const whole = Math.floor(indicatedSteps / divisions);
  const matchingDivision = indicatedSteps - whole * divisions;
  const origin = indicatedSteps / divisions;
  const pitch = (divisions - 1) / divisions;
  return { origin, pitch, whole, matchingDivision, divisions };
}

export function inspectDivision(reading, index) {
  const position = reading.origin + index * reading.pitch;
  const nearest = Math.round(position);
  return { position, nearest, offset: position - nearest };
}

export function makeSpecimen(divisions, random = Math.random) {
  // Independent settings allow both signs of zero error as well as a true zero.
  const widthSteps = 3 * divisions + Math.floor(random() * 21 * divisions);
  const zeroSteps = Math.floor(random() * 7) - 3;
  return { widthSteps, zeroSteps };
}
