export const screenDistance = 100;
export const blockerRadius = 6;
export const screenHalfWidth = 56;

const area = radius => Math.PI * radius ** 2;
const clamp = value => Math.max(-1, Math.min(1, value));

export function circleOverlap(first, second, distance) {
  const tolerance = 32 * Number.EPSILON * Math.max(1, first, second, distance);
  if (distance >= first + second - tolerance) return 0;
  if (distance <= Math.abs(first - second) + tolerance) return area(Math.min(first, second));

  const angleFirst = Math.acos(clamp((distance ** 2 + first ** 2 - second ** 2) / (2 * distance * first)));
  const angleSecond = Math.acos(clamp((distance ** 2 + second ** 2 - first ** 2) / (2 * distance * second)));
  const triangle = Math.sqrt(Math.max(0,
    (-distance + first + second) * (distance + first - second) *
    (distance - first + second) * (distance + first + second))) / 2;
  const overlap = first ** 2 * angleFirst + second ** 2 * angleSecond - triangle;
  return Math.max(0, Math.min(area(Math.min(first, second)), overlap));
}

export function shadowEdges(lampRadius, blockerDistance) {
  const progress = blockerDistance / screenDistance;
  return {
    outer: (blockerRadius + (1 - progress) * lampRadius) / progress,
    inner: Math.max(0, (blockerRadius - (1 - progress) * lampRadius) / progress),
  };
}

export function lampView(lampRadius, blockerDistance, screenPoint) {
  const progress = blockerDistance / screenDistance;
  const apparentX = -progress * screenPoint / (1 - progress);
  const apparentRadius = blockerRadius / (1 - progress);
  let visible;
  if (lampRadius === 0) {
    visible = Math.abs(screenPoint * progress) <= blockerRadius ? 0 : 1;
  } else {
    visible = 1 - circleOverlap(lampRadius, apparentRadius, Math.abs(apparentX)) / area(lampRadius);
  }
  return {
    visible,
    kind: visible === 0 ? 'dark' : visible === 1 ? 'lit' : 'partial',
    apparentX,
    apparentRadius,
  };
}
