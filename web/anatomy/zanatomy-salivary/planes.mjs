// Coordinate order on the schematic: positive horizontal, positive vertical, fixed source axis.
export const axes = { xy: [0, 1, 2], xz: [0, 2, 1], yz: [1, 2, 0] };

export function sectionSegments(points, faces, plane, position) {
  const [h, v, n] = axes[plane];
  const segments = [];
  for (let t = 0; t < faces.length; t += 3) {
    const hits = [];
    for (let corner = 0; corner < 3; corner++) {
      const a = 3 * faces[t + corner],
        b = 3 * faces[t + ((corner + 1) % 3)];
      const p = Math.min(a, b),
        q = Math.max(a, b);
      const x = points[p + n],
        y = points[q + n];
      // The half-open rule gives a repeatable section at vertices and coplanar edges.
      if (x < position === y < position) continue;
      const f = (position - x) / (y - x);
      hits.push([
        points[p + h] + f * (points[q + h] - points[p + h]),
        points[p + v] + f * (points[q + v] - points[p + v])
      ]);
    }
    if (hits.length === 2 && (hits[0][0] !== hits[1][0] || hits[0][1] !== hits[1][1]))
      segments.push(hits);
  }
  return segments;
}
