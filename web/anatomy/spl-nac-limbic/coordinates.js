/* Native sample coordinates. No registration fitting or image resampling. */
(function (root) {
  'use strict';
  const finite = value => typeof value === 'number' && Number.isFinite(value);
  function validateAffine(a) {
    if (!Array.isArray(a) || a.length !== 4 || !a.every(row => Array.isArray(row) && row.length === 4 && row.every(finite)) ||
        a[3].some((value, i) => value !== (i === 3 ? 1 : 0))) throw new RangeError('Invalid source affine');
  }
  function transform(a, p) {
    return a.slice(0, 3).map(row => row[0] * p[0] + row[1] * p[1] + row[2] * p[2] + row[3]);
  }
  function inverse(a) {
    validateAffine(a);
    const [x, y, z] = a;
    const c = [
      [y[1]*z[2]-y[2]*z[1], x[2]*z[1]-x[1]*z[2], x[1]*y[2]-x[2]*y[1]],
      [y[2]*z[0]-y[0]*z[2], x[0]*z[2]-x[2]*z[0], x[2]*y[0]-x[0]*y[2]],
      [y[0]*z[1]-y[1]*z[0], x[1]*z[0]-x[0]*z[1], x[0]*y[1]-x[1]*y[0]],
    ];
    const determinant = x[0]*c[0][0] + x[1]*c[1][0] + x[2]*c[2][0];
    if (!finite(determinant) || determinant === 0) throw new RangeError('Singular source affine');
    const result = c.map(row => {
      const values = row.map(value => value / determinant);
      return [...values, -values.reduce((sum, value, i) => sum + value * a[i][3], 0)];
    });
    result.push([0, 0, 0, 1]);
    validateAffine(result);
    return result;
  }
  function shapeOf(row) {
    if (!Array.isArray(row.shape) || row.shape.length !== 3 || !row.shape.every(value => Number.isSafeInteger(value) && value > 0)) {
      throw new RangeError('Invalid source shape');
    }
    return row.shape;
  }
  function offset(shape, p) {
    return p[0] + shape[0] * (p[1] + shape[1] * p[2]);
  }
  function nearestVoxel(worldToVoxel, world, shape) {
    const continuous = transform(worldToVoxel, world);
    if (continuous.some((value, axis) => !finite(value) || value < -.5 || value >= shape[axis] - .5)) return null;
    return continuous.map(value => Math.floor(value + .5));
  }
  function planeSpec(row, plane, slice) {
    shapeOf(row); validateAffine(row.voxelToRAS);
    const axes = {axial: [2, 0, 1], coronal: [1, 0, 2], sagittal: [0, 1, 2]}[plane];
    if (!axes) throw new RangeError('Unknown anatomical plane');
    // This native viewer deliberately rejects oblique grids rather than silently reslicing them.
    const nativeAxis = worldAxis => {
      const candidates = row.voxelToRAS[worldAxis].slice(0, 3).map((value, i) => value !== 0 ? i : -1).filter(i => i >= 0);
      if (candidates.length !== 1) throw new RangeError('This native plane viewer requires an axis-aligned source grid');
      return candidates[0];
    };
    const [fixed, horizontal, vertical] = axes.map(nativeAxis);
    if (new Set([fixed, horizontal, vertical]).size !== 3) throw new RangeError('Invalid source axis mapping');
    if (!Number.isInteger(slice) || slice < 0 || slice >= row.shape[fixed]) throw new RangeError('Slice leaves source grid');
    const dx = row.voxelToRAS[axes[1]][horizontal], dy = row.voxelToRAS[axes[2]][vertical];
    return {
      plane, fixed, horizontal, vertical, slice, width: row.shape[horizontal], height: row.shape[vertical],
      flipHorizontal: dx > 0, flipVertical: dy > 0,
      spacing: [Math.abs(dx), Math.abs(dy)],
      edgeLabels: plane === 'axial' ? ['R', 'L', 'A', 'P'] : plane === 'coronal' ? ['R', 'L', 'S', 'I'] : ['A', 'P', 'S', 'I'],
    };
  }
  function pixelVoxel(spec, x, y) {
    if (![x, y].every(Number.isInteger) || x < 0 || y < 0 || x >= spec.width || y >= spec.height) throw new RangeError('Pixel leaves source plane');
    const p = [0, 0, 0]; p[spec.fixed] = spec.slice;
    p[spec.horizontal] = spec.flipHorizontal ? spec.width - 1 - x : x;
    p[spec.vertical] = spec.flipVertical ? spec.height - 1 - y : y;
    return p;
  }
  function probe(imageRow, image, labelRow, labels, voxel) {
    const imageShape = shapeOf(imageRow), labelShape = shapeOf(labelRow);
    if (image.length !== imageShape.reduce((a, b) => a*b) || labels.length !== labelShape.reduce((a, b) => a*b)) throw new RangeError('Payload sample count differs');
    if (voxel.some((value, axis) => !Number.isInteger(value) || value < 0 || value >= imageShape[axis])) throw new RangeError('Probe leaves native MRI');
    const ras = transform(imageRow.voxelToRAS, voxel);
    const labelVoxel = nearestVoxel(inverse(labelRow.voxelToRAS), ras, labelShape);
    return {voxel: [...voxel], ras, value: image[offset(imageShape, voxel)], labelVoxel,
      label: labelVoxel ? labels[offset(labelShape, labelVoxel)] : null};
  }
  const api = Object.freeze({validateAffine, transform, inverse, shapeOf, offset, nearestVoxel, planeSpec, pixelVoxel, probe});
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.SPLNativeCoordinates = api;
})(globalThis);
