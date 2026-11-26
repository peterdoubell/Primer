export const sectionAxes = [
  [1, 2],
  [2, 0],
  [0, 1]
];

// Every pair points along the positively wound boundary of the cross-section.
// Shared edges in the archive have opposite winding, including at cube-face seams.
export function crossSection(vertices, plates, axis, height) {
  const [u, v] = sectionAxes[axis];
  const segments = [];
  let twiceArea = 0;
  for (let i = 0; i < plates.length; i += 3) {
    const p = 3 * plates[i],
      q = 3 * plates[i + 1],
      r = 3 * plates[i + 2];
    const a = vertices[p + axis] < height,
      b = vertices[q + axis] < height,
      c = vertices[r + axis] < height;
    if (a === b && b === c) continue;
    let start, end;
    for (let j = 0; j < 3; j++) {
      const from = 3 * plates[i + j],
        to = 3 * plates[i + ((j + 1) % 3)];
      const z0 = vertices[from + axis],
        z1 = vertices[to + axis];
      if (z0 < height === z1 < height) continue;
      const f = (height - z0) / (z1 - z0);
      const point = [0, 1, 2].map(
        (k) => vertices[from + k] + f * (vertices[to + k] - vertices[from + k])
      );
      if (z0 < height) end = point;
      else start = point;
    }
    if (start[u] === end[u] && start[v] === end[v]) continue;
    twiceArea += start[u] * end[v] - end[u] * start[v];
    segments.push(...start, ...end);
  }
  return { area: twiceArea / 2, segments };
}

export function estimate(model, axis, count, method) {
  const values = model.profiles[axis],
    steps = values.length - 1;
  const stride = steps / count;
  if (
    !Number.isInteger(stride) ||
    stride < 2 ||
    stride % 2 ||
    !['left', 'midpoint', 'trapezoid'].includes(method)
  )
    throw Error('Unsupported sampling rule.');
  const thickness = (model.bounds[1][axis] - model.bounds[0][axis]) / count;
  const slabs = [];
  let volume = 0;
  for (let i = 0; i < steps; i += stride) {
    const left = values[i],
      right = values[i + stride],
      middle = values[i + stride / 2];
    const sample = method === 'midpoint' ? middle : method === 'left' ? left : (left + right) / 2;
    volume += thickness * sample;
    slabs.push({ left, right, sample });
  }
  return { volume, thickness, slabs, error: volume - model.volumeM3 };
}

export async function openMesh(record, url, signal) {
  const response = await fetch(url, { signal });
  if (!response.ok) throw Error('The selected model is unavailable.');
  const packed = await response.arrayBuffer();
  const digest = async (bytes) =>
    Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', bytes)), (n) =>
      n.toString(16).padStart(2, '0')
    ).join('');
  if (packed.byteLength !== record.bytes || (await digest(packed)) !== record.sha256)
    throw Error('Packed source differs.');
  const decoded = await new Response(
    new Blob([packed]).stream().pipeThrough(new DecompressionStream('gzip'))
  ).arrayBuffer();
  signal.throwIfAborted();
  if (
    decoded.byteLength !== 24 * record.vertices + 12 * record.triangles ||
    (await digest(decoded)) !== record.decodedSHA256
  )
    throw Error('Decoded source differs.');
  const positions = new Float64Array(decoded, 0, 3 * record.vertices);
  const indices = new Uint32Array(decoded, positions.byteLength);
  if (positions.some((x) => !Number.isFinite(x)) || indices.some((i) => i >= record.vertices))
    throw Error('Invalid plate geometry.');
  return { positions, indices };
}
