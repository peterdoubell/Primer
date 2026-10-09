'use strict';
const fs = require('node:fs');
const { createHash } = require('node:crypto');
const hash = buffer => createHash('sha256').update(buffer).digest('hex');
const models = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const result = {};
for (const [label, [vertices, cells]] of Object.entries(models)) {
  const points = Buffer.alloc(vertices.length * 24);
  for (let i = 0; i < vertices.length; i++) {
    if (!Array.isArray(vertices[i]) || vertices[i].length !== 3) throw Error('Invalid source point');
    for (let axis = 0; axis < 3; axis++) {
      const value = vertices[i][axis];
      if (typeof value !== 'number' || !Number.isFinite(value)) throw Error('Nonfinite source point');
      points.writeDoubleLE(value, i * 24 + axis * 8);
    }
  }
  const original = Buffer.alloc(cells.length * 4);
  const faces = [];
  let cursor = 0;
  while (cursor < cells.length) {
    const n = cells[cursor++];
    if (n !== 3 || cursor + n > cells.length) throw Error('Invalid source triangle cell');
    for (let corner = 0; corner < n; corner++) {
      const index = cells[cursor++];
      if (!Number.isInteger(index) || index < 0 || index >= vertices.length) throw Error('Invalid source index');
      faces.push(index);
    }
  }
  for (let i = 0; i < cells.length; i++) original.writeUInt32LE(cells[i], i * 4);
  const triangles = Buffer.alloc(faces.length * 4);
  faces.forEach((index, i) => triangles.writeUInt32LE(index, i * 4));
  result[label] = {positions: vertices.length, triangles: faces.length / 3,
    positions_float64_le_sha256: hash(points), original_VTK_cells_uint32_le_sha256: hash(original),
    ordered_triangle_indices_uint32_le_sha256: hash(triangles)};
}
process.stdout.write(JSON.stringify(result));
